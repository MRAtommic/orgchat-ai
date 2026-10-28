import { Peer, DataConnection } from 'peerjs';

export interface RemotePlayer {
    id: string;
    name: string;
    scene: string;
    x: number;
    y: number;
    targetX: number;
    targetY: number;
    direction: 'up' | 'down' | 'left' | 'right';
    frame: number;
    isMoving: boolean;
    hp: number;
    maxHp: number;
    weaponId: string;
    weaponName?: string;
    title?: string;
    isAttacking?: boolean;
    isGuarding?: boolean;
    isDashing?: boolean;
    comboStep?: number;
    chatMsg?: string;
    chatTimer?: number;
    color?: string;
    lastSeen: number;
}

export type PlayerNetState = Omit<RemotePlayer, 'targetX' | 'targetY'>;

export interface NetMessage {
    type: 'state' | 'join' | 'leave' | 'chat' | 'pvp_hit' | 'pvp_defeat' | 'world_sync' | 'crop_sync';
    senderId: string;
    senderName: string;
    roomCode: string;
    payload: any;
    timestamp: number;
}

// High-reliability STUN configuration for NAT & cross-device traversal (Mobile 4G/5G <-> PC)
const PEER_CONFIG = {
    debug: 1,
    config: {
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
            { urls: 'stun:stun2.l.google.com:19302' },
            { urls: 'stun:stun3.l.google.com:19302' },
            { urls: 'stun:stun4.l.google.com:19302' },
            { urls: 'stun:stun.cloudflare.com:3478' }
        ],
        sdpSemantics: 'unified-plan'
    }
};

class MultiplayerService {
    public isHost: boolean = false;
    public isConnected: boolean = false;
    public isGlobalHub: boolean = false;
    public roomCode: string | null = null;
    public myPeerId: string = '';
    public myPlayerId: string = '';
    public myPlayerName: string = 'ผู้เล่น';
    public connectionMode: 'p2p' | 'local' | 'none' = 'none';

    private peer: Peer | null = null;
    private hostConn: DataConnection | null = null;
    private clientConns: Map<string, DataConnection> = new Map();
    private broadcastChannel: BroadcastChannel | null = null;

    private syncInterval: any = null;
    private cleanupInterval: any = null;

    constructor() {
        this.myPlayerId = 'p_' + Math.floor(100000 + Math.random() * 900000);
    }

    public init(): void {
        const currentUser = (window as any).Auth?.getCurrentUser?.();
        if (currentUser && currentUser.username) {
            this.myPlayerName = currentUser.username;
        } else {
            this.myPlayerName = 'นักผจญภัย ' + this.myPlayerId.slice(-3);
        }
    }

    // ── Generate 6-Digit Room Code ─────────────────────────────
    public generateRoomCode(): string {
        return String(Math.floor(100000 + Math.random() * 900000));
    }

    // ── Host A Room (เปิดโลกของตัวเอง) ────────────────────────
    public hostRoom(customCode?: string): Promise<{ success: boolean; code: string; error?: string }> {
        return new Promise((resolve) => {
            this.disconnect();
            this.init();
            this.isGlobalHub = false;
            const code = customCode || this.generateRoomCode();
            this.roomCode = code;
            this.isHost = true;

            const peerTargetId = `gamefarm-room-${code}`;
            let resolved = false;

            try {
                this.peer = new Peer(peerTargetId, PEER_CONFIG);

                this.peer.on('open', (id) => {
                    if (resolved) return;
                    resolved = true;
                    this.myPeerId = id;
                    this.isConnected = true;
                    this.connectionMode = 'p2p';
                    this.setupBroadcastChannel(code);
                    this.startHeartbeat();
                    this.updateUI();
                    resolve({ success: true, code });
                });

                this.peer.on('connection', (conn) => {
                    this.handleIncomingClientConnection(conn);
                });

                this.peer.on('disconnected', () => {
                    console.warn('[Multiplayer Host]: Reconnecting to signaling server...');
                    try { this.peer?.reconnect(); } catch (_) {}
                });

                this.peer.on('error', (err: any) => {
                    console.warn('[Multiplayer Host Error]:', err);
                    if (resolved) return;
                    if (err.type === 'unavailable-id') {
                        // ID taken, retry with new code
                        const newCode = this.generateRoomCode();
                        this.hostRoom(newCode).then(resolve);
                    } else {
                        resolved = true;
                        // Setup local channel fallback for same-browser testing
                        this.setupBroadcastChannel(code);
                        this.isConnected = true;
                        this.connectionMode = 'local';
                        this.startHeartbeat();
                        this.updateUI();
                        resolve({
                            success: true,
                            code,
                            error: 'เปิดห้องสำเร็จ (โหมดสำรองเครือข่าย)'
                        });
                    }
                });
            } catch (err: any) {
                if (!resolved) {
                    resolved = true;
                    this.setupBroadcastChannel(code);
                    this.isConnected = true;
                    this.connectionMode = 'local';
                    this.startHeartbeat();
                    this.updateUI();
                    resolve({ success: true, code });
                }
            }
        });
    }

    // ── Join A Room (เข้าร่วมโลกเพื่อนด้วยรหัส) ─────────────────
    public joinRoom(roomCode: string, keepHubFlag?: boolean): Promise<{ success: boolean; error?: string }> {
        return new Promise((resolve) => {
            this.disconnect();
            this.init();
            if (!keepHubFlag) {
                this.isGlobalHub = (roomCode === '999999');
            }
            const cleanCode = roomCode.trim().replace(/[^0-9]/g, '');
            if (cleanCode.length < 4) {
                resolve({ success: false, error: 'รหัสห้องต้องมีอย่างน้อย 4 หลัก' });
                return;
            }

            this.roomCode = cleanCode;
            this.isHost = false;
            const peerTargetId = `gamefarm-room-${cleanCode}`;

            try {
                this.peer = new Peer(PEER_CONFIG);
                let resolved = false;

                this.peer.on('open', (myId) => {
                    this.myPeerId = myId;
                    this.setupBroadcastChannel(cleanCode);

                    if (!this.peer) return;
                    const conn = this.peer.connect(peerTargetId, {
                        reliable: true
                    });

                    this.hostConn = conn;

                    const onConnected = () => {
                        this.isConnected = true;
                        this.connectionMode = 'p2p';
                        this.startHeartbeat();
                        this.sendJoinPacket();
                        this.updateUI();
                        if (!resolved) {
                            resolved = true;
                            resolve({ success: true });
                        }
                    };

                    if (conn.open) {
                        onConnected();
                    } else {
                        conn.on('open', onConnected);
                    }

                    conn.on('data', (data) => {
                        this.handleNetworkMessage(data as NetMessage);
                    });

                    conn.on('close', () => {
                        this.handlePeerDisconnect('host');
                    });

                    conn.on('error', (err: any) => {
                        console.warn('[Multiplayer Conn Error]:', err);
                        if (!resolved) {
                            resolved = true;
                            resolve({
                                success: false,
                                error: 'ไม่พบโฮสต์ของห้อง ' + cleanCode + ' (ตรวจสอบว่าเครื่องเพื่อนเปิดห้องอยู่)'
                            });
                        }
                    });

                    // 12s timeout for WebRTC cross-device ICE candidate discovery
                    setTimeout(() => {
                        if (!resolved) {
                            resolved = true;
                            if (this.hostConn && this.hostConn.open) {
                                this.connectionMode = 'p2p';
                                resolve({ success: true });
                            } else {
                                this.disconnect();
                                resolve({
                                    success: false,
                                    error: 'การเชื่อมต่อห้อง ' + cleanCode + ' หมดเวลา (ไม่พบโฮสต์ หรือสัญญาณเครือข่ายบล็อกการเชื่อมต่อ P2P)'
                                });
                            }
                        }
                    }, 12000);
                });

                this.peer.on('disconnected', () => {
                    try { this.peer?.reconnect(); } catch (_) {}
                });

                this.peer.on('error', (err: any) => {
                    console.warn('[Multiplayer Join Peer Error]:', err);
                    if (!resolved) {
                        resolved = true;
                        if (err.type === 'peer-unavailable') {
                            resolve({
                                success: false,
                                error: 'ไม่พบห้องหมายเลข ' + cleanCode + ' (โปรดตรวจสอบว่าเครื่องเพื่อนเปิดห้องอยู่หรือไม่)'
                            });
                        } else {
                            resolve({
                                success: false,
                                error: 'เกิดข้อผิดพลาดในการเชื่อมต่อ: ' + (err.type || err.message || 'เครือข่ายไม่ตอบสนอง')
                            });
                        }
                    }
                });
            } catch (err: any) {
                console.warn('[Multiplayer Join Exception]:', err);
                resolve({
                    success: false,
                    error: 'ไม่สามารถสร้างการเชื่อมต่อได้: ' + (err.message || 'ข้อผิดพลาดระบบ')
                });
            }
        });
    }

    // ── Join Global Hub (ห้องรวมสาธารณะสำหรับพบปะผู้เล่นทุกคน) ───────
    public joinGlobalHub(): Promise<{ success: boolean; isHost: boolean; error?: string }> {
        return new Promise((resolve) => {
            this.disconnect();
            this.init();
            const hubCode = '999999';
            this.roomCode = hubCode;
            this.isGlobalHub = true;
            this.isHost = true;
            const peerTargetId = `gamefarm-room-${hubCode}`;

            let resolved = false;

            try {
                this.peer = new Peer(peerTargetId, PEER_CONFIG);

                this.peer.on('open', (id) => {
                    if (resolved) return;
                    resolved = true;
                    this.myPeerId = id;
                    this.isConnected = true;
                    this.isHost = true;
                    this.connectionMode = 'p2p';
                    this.setupBroadcastChannel(hubCode);
                    this.startHeartbeat();
                    this.updateUI();
                    resolve({ success: true, isHost: true });
                });

                this.peer.on('connection', (conn) => {
                    this.handleIncomingClientConnection(conn);
                });

                this.peer.on('disconnected', () => {
                    try { this.peer?.reconnect(); } catch (_) {}
                });

                this.peer.on('error', (err: any) => {
                    if (resolved) return;
                    resolved = true;
                    if (this.peer) {
                        try { this.peer.destroy(); } catch (_) {}
                        this.peer = null;
                    }
                    // ID already taken means another player is already hosting the Hub. Join as client!
                    this.joinRoom(hubCode, true).then((res) => {
                        this.isGlobalHub = true;
                        resolve({ success: res.success, isHost: false, error: res.error });
                    });
                });

                // 4.5s timeout: if hosting takes too long, fallback to join as client
                setTimeout(() => {
                    if (!resolved) {
                        resolved = true;
                        if (this.peer) {
                            try { this.peer.destroy(); } catch (_) {}
                            this.peer = null;
                        }
                        this.joinRoom(hubCode, true).then((res) => {
                            this.isGlobalHub = true;
                            resolve({ success: res.success, isHost: false, error: res.error });
                        });
                    }
                }, 4500);
            } catch (err) {
                if (!resolved) {
                    resolved = true;
                    this.joinRoom(hubCode, true).then((res) => {
                        this.isGlobalHub = true;
                        resolve({ success: res.success, isHost: false, error: res.error });
                    });
                }
            }
        });
    }

    // ── Setup Local BroadcastChannel (Zero-Config Same-Browser Sync) ──
    private setupBroadcastChannel(code: string): void {
        if (typeof BroadcastChannel !== 'undefined') {
            if (this.broadcastChannel) {
                this.broadcastChannel.close();
            }
            this.broadcastChannel = new BroadcastChannel(`gamefarm_mp_${code}`);
            this.broadcastChannel.onmessage = (e) => {
                const msg = e.data as NetMessage;
                if (msg && msg.senderId !== this.myPlayerId) {
                    this.handleNetworkMessage(msg);
                }
            };
        }
    }

    // ── Handle Incoming Client (Host Side) ────────────────────
    private handleIncomingClientConnection(conn: DataConnection): void {
        const onOpen = () => {
            this.clientConns.set(conn.peer, conn);
            this.connectionMode = 'p2p';
            this.sendWorldSyncPacket(conn);
            this.updateUI();
            const game = (window as any).Game;
            if (game && typeof game.addFloatingText === 'function') {
                game.addFloatingText('★ มีผู้เล่นเชื่อมต่อเข้าสู่โลกของคุณ! ★', game.player.x - 30, game.player.y - 30, '#38bdf8');
            }
        };

        if (conn.open) {
            onOpen();
        } else {
            conn.on('open', onOpen);
        }

        conn.on('data', (data) => {
            const msg = data as NetMessage;
            this.handleNetworkMessage(msg);
            // Host relays message to other clients
            this.broadcastExcept(msg, conn.peer);
        });

        conn.on('close', () => {
            this.clientConns.delete(conn.peer);
            this.updateUI();
        });

        conn.on('error', (err) => {
            console.warn('[Host Client Conn Error]:', err);
            this.clientConns.delete(conn.peer);
            this.updateUI();
        });
    }

    // ── Send Join Packet ──────────────────────────────────────
    private sendJoinPacket(): void {
        const game = (window as any).Game;
        if (!game || !game.player) return;

        this.broadcastMessage({
            type: 'join',
            senderId: this.myPlayerId,
            senderName: this.myPlayerName,
            roomCode: this.roomCode || '',
            payload: {
                x: game.player.x,
                y: game.player.y,
                scene: game.currentScene,
                direction: game.player.direction || 'down',
                hp: game.player.hp,
                maxHp: game.player.maxHp || 100,
                weaponId: game.player.inventory?.[game.player.selectedSlot]?.id || 'hoe'
            },
            timestamp: Date.now()
        });
    }

    // ── Send World Sync Packet (Host to Guest) ────────────────
    private sendWorldSyncPacket(conn?: DataConnection): void {
        const game = (window as any).Game;
        if (!game) return;

        const cropData: { x: number; y: number; crop: any }[] = [];
        if (game.map) {
            for (let y = 0; y < game.mapHeight; y++) {
                for (let x = 0; x < game.mapWidth; x++) {
                    const tile = game.map[y]?.[x];
                    if (tile && tile.crop) {
                        cropData.push({ x, y, crop: tile.crop });
                    }
                }
            }
        }

        const syncMsg: NetMessage = {
            type: 'world_sync',
            senderId: this.myPlayerId,
            senderName: this.myPlayerName,
            roomCode: this.roomCode || '',
            payload: {
                scene: game.currentScene,
                hostX: Math.round(game.player.x),
                hostY: Math.round(game.player.y),
                weather: game.currentWeather,
                dayTime: game.time,
                day: game.day,
                crops: cropData
            },
            timestamp: Date.now()
        };

        if (conn && conn.open) {
            conn.send(syncMsg);
        } else {
            this.broadcastMessage(syncMsg);
        }
    }

    // ── Start Heartbeat State Broadcast (20 FPS) ──────────────
    private startHeartbeat(): void {
        if (this.syncInterval) clearInterval(this.syncInterval);
        if (this.cleanupInterval) clearInterval(this.cleanupInterval);

        this.syncInterval = setInterval(() => {
            if (!this.isConnected) return;
            this.broadcastPlayerState();
        }, 50);

        this.cleanupInterval = setInterval(() => {
            this.cleanupStalePlayers();
        }, 2000);
    }

    // ── Broadcast Local Player State ──────────────────────────
    private broadcastPlayerState(): void {
        const game = (window as any).Game;
        if (!game || !game.player) return;

        const selItem = game.player.inventory?.[game.player.selectedSlot];
        const weaponId = (selItem && selItem.id) ? selItem.id : 'hoe';
        const weaponName = (selItem && selItem.name) ? selItem.name : 'เครื่องมือ';

        const statePayload: PlayerNetState = {
            id: this.myPlayerId,
            name: this.myPlayerName,
            scene: game.currentScene,
            x: Math.round(game.player.x),
            y: Math.round(game.player.y),
            direction: game.player.direction || 'down',
            frame: game.player.frame || 0,
            isMoving: !!game.player.isMoving,
            hp: game.player.hp,
            maxHp: game.player.maxHp || 100,
            weaponId: weaponId,
            weaponName: weaponName,
            title: game.player.title || 'นักผจญภัยฝึกหัด',
            isAttacking: !!game.meleeSlashAnim,
            comboStep: game.player.comboStep || 1,
            isGuarding: !!game.player.isGuarding,
            isDashing: !!game.player.isDashing,
            lastSeen: Date.now()
        };

        this.broadcastMessage({
            type: 'state',
            senderId: this.myPlayerId,
            senderName: this.myPlayerName,
            roomCode: this.roomCode || '',
            payload: statePayload,
            timestamp: Date.now()
        });
    }

    // ── Handle Incoming Network Message ───────────────────────
    public handleNetworkMessage(msg: NetMessage): void {
        if (!msg || msg.senderId === this.myPlayerId) return;

        const game = (window as any).Game;
        if (!game) return;

        game.remotePlayers = game.remotePlayers || {};

        if (msg.type === 'state') {
            const p = msg.payload as PlayerNetState;
            const existing = game.remotePlayers[msg.senderId];
            if (existing) {
                existing.targetX = p.x;
                existing.targetY = p.y;
                existing.direction = p.direction;
                existing.frame = p.frame;
                existing.scene = p.scene;
                existing.isMoving = p.isMoving;
                existing.hp = p.hp;
                existing.maxHp = p.maxHp;
                existing.weaponId = p.weaponId;
                existing.weaponName = p.weaponName;
                existing.isAttacking = p.isAttacking;
                existing.comboStep = p.comboStep;
                existing.isGuarding = p.isGuarding;
                existing.isDashing = p.isDashing;
                existing.title = p.title;
                existing.lastSeen = Date.now();
            } else {
                game.remotePlayers[msg.senderId] = {
                    ...p,
                    targetX: p.x,
                    targetY: p.y,
                    lastSeen: Date.now()
                };
                if (typeof game.addFloatingText === 'function') {
                    game.addFloatingText(`★ ${msg.senderName} เข้าร่วมห้อง!`, game.player.x, game.player.y - 25, '#38bdf8');
                }
                this.updateUI();
            }
        } else if (msg.type === 'join') {
            if (typeof game.addFloatingText === 'function') {
                game.addFloatingText(`★ ${msg.senderName} เข้ามาในโลกของคุณ!`, game.player.x, game.player.y - 25, '#38bdf8');
            }
            if (this.isHost) {
                this.sendWorldSyncPacket();
            }
            this.updateUI();
        } else if (msg.type === 'pvp_hit') {
            const hitData = msg.payload;
            if (hitData.targetId === this.myPlayerId) {
                // Local player took PvP damage!
                if (typeof game.receivePvPHit === 'function') {
                    game.receivePvPHit(hitData, msg.senderName);
                }
            }
        } else if (msg.type === 'pvp_defeat') {
            const defeatData = msg.payload;
            if (typeof game.addFloatingText === 'function') {
                game.addFloatingText(`★ ${defeatData.winnerName} พิชิต ${defeatData.loserName} ในการประลองยุทธ์! ★`, game.player.x - 40, game.player.y - 30, '#fde047');
            }
        } else if (msg.type === 'chat') {
            const chatData = msg.payload;
            const rp = game.remotePlayers[msg.senderId];
            if (rp) {
                rp.chatMsg = chatData.text;
                rp.chatTimer = 4000;
            }
            if (typeof game.addFloatingText === 'function') {
                game.addFloatingText(`${msg.senderName}: ${chatData.text}`, (rp ? rp.x : game.player.x), (rp ? rp.y : game.player.y) - 20, '#ffffff');
            }
        } else if (msg.type === 'world_sync' && !this.isHost) {
            // Apply host's world state
            const sync = msg.payload;
            if (sync.scene && game.currentScene !== sync.scene) {
                const targetTileX = Math.round((sync.hostX || 480) / 32);
                const targetTileY = Math.round((sync.hostY || 384) / 32);
                if (typeof game.switchScene === 'function') {
                    game.switchScene(sync.scene, targetTileX, targetTileY);
                    if (typeof game.addFloatingText === 'function') {
                        game.addFloatingText(`★ เดินทางมาถึงโลกของ ${msg.senderName}! ★`, game.player.x - 30, game.player.y - 30, '#38bdf8');
                    }
                }
            }
            if (sync.weather && game.currentWeather !== sync.weather) {
                game.currentWeather = sync.weather;
            }
            if (sync.crops && game.map) {
                sync.crops.forEach((c: any) => {
                    if (game.map[c.y] && game.map[c.y][c.x]) {
                        game.map[c.y][c.x].crop = c.crop;
                    }
                });
            }
        }
    }

    // ── Send PvP Hit ──────────────────────────────────────────
    public sendPvPHit(targetId: string, damage: number, isCrit: boolean, angle: number, weaponName: string): void {
        this.broadcastMessage({
            type: 'pvp_hit',
            senderId: this.myPlayerId,
            senderName: this.myPlayerName,
            roomCode: this.roomCode || '',
            payload: {
                targetId,
                damage,
                isCrit,
                angle,
                attackerId: this.myPlayerId,
                attackerName: this.myPlayerName,
                weaponName
            },
            timestamp: Date.now()
        });
    }

    // ── Send PvP Defeat ───────────────────────────────────────
    public sendPvPDefeat(winnerId: string, winnerName: string): void {
        this.broadcastMessage({
            type: 'pvp_defeat',
            senderId: this.myPlayerId,
            senderName: this.myPlayerName,
            roomCode: this.roomCode || '',
            payload: {
                winnerId,
                winnerName,
                loserId: this.myPlayerId,
                loserName: this.myPlayerName
            },
            timestamp: Date.now()
        });
    }

    // ── Send Chat Message ─────────────────────────────────────
    public sendChat(text: string): void {
        const clean = text.trim().substring(0, 50);
        if (!clean) return;

        const game = (window as any).Game;
        if (game && game.player) {
            game.player.chatMsg = clean;
            game.player.chatTimer = 4000;
        }

        this.broadcastMessage({
            type: 'chat',
            senderId: this.myPlayerId,
            senderName: this.myPlayerName,
            roomCode: this.roomCode || '',
            payload: { text: clean },
            timestamp: Date.now()
        });
    }

    // ── Broadcast Message to Peers & Local Channel ─────────────
    private broadcastMessage(msg: NetMessage): void {
        // Send over WebRTC to host (if client)
        if (this.hostConn && this.hostConn.open) {
            this.hostConn.send(msg);
        }

        // Send over WebRTC to all clients (if host)
        if (this.isHost) {
            this.clientConns.forEach((conn) => {
                if (conn.open) conn.send(msg);
            });
        }

        // Send over BroadcastChannel
        if (this.broadcastChannel) {
            try {
                this.broadcastChannel.postMessage(msg);
            } catch {}
        }
    }

    private broadcastExcept(msg: NetMessage, exceptPeerId: string): void {
        this.clientConns.forEach((conn, peerId) => {
            if (peerId !== exceptPeerId && conn.open) {
                conn.send(msg);
            }
        });
    }

    // ── Clean Stale Remote Players (after 6 seconds timeout) ───
    private cleanupStalePlayers(): void {
        const game = (window as any).Game;
        if (!game || !game.remotePlayers) return;

        const now = Date.now();
        for (const pid in game.remotePlayers) {
            if (now - game.remotePlayers[pid].lastSeen > 6000) {
                delete game.remotePlayers[pid];
                this.updateUI();
            }
        }
    }

    private handlePeerDisconnect(type: string): void {
        console.log('[Multiplayer Disconnect]:', type);
        if (this.isGlobalHub && !this.isHost && this.isConnected) {
            console.log('[Global Hub]: Reconnecting to hub host...');
            setTimeout(() => {
                if (this.isGlobalHub) {
                    this.joinGlobalHub();
                }
            }, 1200);
        }
        this.updateUI();
    }

    // ── Disconnect / Leave ────────────────────────────────────
    public disconnect(): void {
        this.isConnected = false;
        this.isHost = false;
        this.isGlobalHub = false;
        this.roomCode = null;
        this.connectionMode = 'none';

        if (this.syncInterval) clearInterval(this.syncInterval);
        if (this.cleanupInterval) clearInterval(this.cleanupInterval);

        if (this.hostConn) {
            try { this.hostConn.close(); } catch {}
            this.hostConn = null;
        }

        this.clientConns.forEach(c => {
            try { c.close(); } catch {}
        });
        this.clientConns.clear();

        if (this.peer) {
            try { this.peer.destroy(); } catch {}
            this.peer = null;
        }

        if (this.broadcastChannel) {
            try { this.broadcastChannel.close(); } catch {}
            this.broadcastChannel = null;
        }

        const game = (window as any).Game;
        if (game) {
            game.remotePlayers = {};
        }

        this.updateUI();
    }

    // ── Update Multiplayer Modal UI & HUD Badge ───────────────
    public updateUI(): void {
        const game = (window as any).Game;
        const count = game && game.remotePlayers ? Object.keys(game.remotePlayers).length : 0;

        // Update HUD Badge
        const badge = document.getElementById('hudMultiplayerStatus');
        if (badge) {
            if (this.isConnected && this.roomCode) {
                badge.style.display = 'flex';
                badge.className = 'hud-badge mp-active';
                if (this.isGlobalHub) {
                    badge.innerHTML = `<span class="mp-dot" style="background:#38bdf8;"></span><span>ห้องรวม (${count + 1} คน)</span>`;
                } else {
                    badge.innerHTML = `<span class="mp-dot"></span><span>ห้อง: ${this.roomCode} (${count + 1} คน)</span>`;
                }
            } else {
                badge.style.display = 'none';
            }
        }

        // Update Modal elements
        const roomCodeDisplay = document.getElementById('mpHostRoomCode');
        if (roomCodeDisplay && this.roomCode) {
            roomCodeDisplay.textContent = this.roomCode;
        }

        const statusEl = document.getElementById('mpStatusText');
        if (statusEl) {
            if (this.isConnected) {
                const modeText = this.connectionMode === 'p2p' ? 'P2P ออนไลน์จริง' : 'จำลองเครื่องเดียวกัน';
                if (this.isGlobalHub) {
                    statusEl.textContent = `อยู่ในห้องโถงชุมนุมส่วนกลาง (Global Hub - ${modeText}) - นักผจญภัยออนไลน์ในห้อง ${count + 1} คน`;
                    statusEl.style.color = '#38bdf8';
                } else {
                    statusEl.textContent = this.isHost
                        ? `โฮสต์โลกออนไลน์ (ห้อง ${this.roomCode} - ${modeText}) - มีผู้เล่นอื่นร่วมโลก ${count} คน`
                        : `เชื่อมต่อในโลกห้อง ${this.roomCode} (${modeText}) สำเร็จ!`;
                    statusEl.style.color = '#4ade80';
                }
            } else {
                statusEl.textContent = 'ยังไม่ได้เชื่อมต่อ (เล่นคนเดียว)';
                statusEl.style.color = '#94a3b8';
            }
        }

        const playersListEl = document.getElementById('mpPlayersList');
        if (playersListEl) {
            let html = `<div class="mp-player-row self"><span class="mp-crown">★</span> <b>${this.myPlayerName} (คุณ)</b> <span class="badge-role">${this.isHost ? 'โฮสต์' : 'สมาชิก'}</span></div>`;
            if (game && game.remotePlayers) {
                for (const pid in game.remotePlayers) {
                    const rp = game.remotePlayers[pid];
                    html += `
                    <div class="mp-player-row" style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span class="mp-circle" style="color: #4ade80;">●</span>
                            <b>${rp.name}</b>
                            <span class="badge-scene">${rp.scene}</span>
                        </div>
                        <button class="btn-primary" onclick="Game.warpToPlayer('${pid}')" style="font-size: 10px; padding: 2px 8px; border-radius: 4px; cursor: pointer;">วาร์ปไปหา</button>
                    </div>`;
                }
            }
            playersListEl.innerHTML = html;
        }
    }
}

export const Multiplayer = new MultiplayerService();
if (typeof window !== 'undefined') {
    (window as any).Multiplayer = Multiplayer;
}
