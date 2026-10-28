/* ==========================================================================
   HAPPY FARM 2D - MULTIPLAYER SERVICE (HIGH-SPEED CLOUD RELAY & P2P)
   Ultra-fast cross-device multiplayer working across Mobile (4G/5G) and PC
   Bypasses NAT, Firewalls, and STUN/TURN restrictions via WSS Message Broker
   ========================================================================== */

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

// ── Lightweight Pure-Browser MQTT 3.1.1 Helper Functions ─────────
function encodeString(str: string): Uint8Array {
    const enc = new TextEncoder().encode(str);
    const buf = new Uint8Array(2 + enc.length);
    buf[0] = (enc.length >> 8) & 0xff;
    buf[1] = enc.length & 0xff;
    buf.set(enc, 2);
    return buf;
}

function concatUint8(arrays: Uint8Array[]): Uint8Array {
    let total = 0;
    for (let i = 0; i < arrays.length; i++) total += arrays[i].length;
    const res = new Uint8Array(total);
    let off = 0;
    for (let i = 0; i < arrays.length; i++) {
        res.set(arrays[i], off);
        off += arrays[i].length;
    }
    return res;
}

function encodeVarLength(len: number): Uint8Array {
    const bytes: number[] = [];
    do {
        let digit = len % 128;
        len = Math.floor(len / 128);
        if (len > 0) digit |= 0x80;
        bytes.push(digit);
    } while (len > 0);
    return new Uint8Array(bytes);
}

function decodeVarLength(buf: Uint8Array, offset: number): { value: number; bytesRead: number } {
    let multiplier = 1;
    let value = 0;
    let bytesRead = 0;
    let encodedByte = 0;
    do {
        encodedByte = buf[offset + bytesRead];
        value += (encodedByte & 127) * multiplier;
        multiplier *= 128;
        bytesRead++;
    } while ((encodedByte & 128) !== 0);
    return { value, bytesRead };
}

function createConnectPacket(clientId: string): Uint8Array {
    const protoName = encodeString('MQTT');
    const protoLevel = new Uint8Array([0x04]);
    const flags = new Uint8Array([0x02]); // Clean session
    const keepAlive = new Uint8Array([0x00, 0x1e]); // 30s
    const cid = encodeString(clientId);
    const varHeader = concatUint8([protoName, protoLevel, flags, keepAlive, cid]);
    const len = encodeVarLength(varHeader.length);
    return concatUint8([new Uint8Array([0x10]), len, varHeader]);
}

function createSubscribePacket(topic: string, packetId = 1): Uint8Array {
    const pktIdBuf = new Uint8Array([(packetId >> 8) & 0xff, packetId & 0xff]);
    const topBuf = encodeString(topic);
    const qosBuf = new Uint8Array([0x00]);
    const payload = concatUint8([pktIdBuf, topBuf, qosBuf]);
    const len = encodeVarLength(payload.length);
    return concatUint8([new Uint8Array([0x82]), len, payload]);
}

function createPublishPacket(topic: string, message: string): Uint8Array {
    const topBuf = encodeString(topic);
    const msgBuf = new TextEncoder().encode(message);
    const payload = concatUint8([topBuf, msgBuf]);
    const len = encodeVarLength(payload.length);
    return concatUint8([new Uint8Array([0x30]), len, payload]);
}

function parsePublishPacket(bytes: Uint8Array): { topic: string; message: string } {
    const { value: remLen, bytesRead } = decodeVarLength(bytes, 1);
    let offset = 1 + bytesRead;
    const topLen = (bytes[offset] << 8) | bytes[offset + 1];
    offset += 2;
    const topic = new TextDecoder().decode(bytes.subarray(offset, offset + topLen));
    offset += topLen;
    const message = new TextDecoder().decode(bytes.subarray(offset, 1 + bytesRead + remLen));
    return { topic, message };
}

// ── Ultra-Reliable WebSocket Message Relay Client ────────────────
class CloudRelayClient {
    public isConnected: boolean = false;
    private ws: WebSocket | null = null;
    private clientId: string = '';
    private pingTimer: any = null;
    private currentTopic: string = '';
    private onMessageCallback: ((msg: NetMessage, topic: string) => void) | null = null;
    private pendingMessages: string[] = [];
    private brokerUrl: string = 'wss://broker.hivemq.com:8884/mqtt';

    constructor() {
        this.clientId = 'gf_' + Math.random().toString(36).substring(2, 10);
    }

    public connect(topic: string, onMessage: (msg: NetMessage, topic: string) => void): Promise<boolean> {
        return new Promise((resolve) => {
            this.disconnect();
            this.currentTopic = topic;
            this.onMessageCallback = onMessage;
            let resolved = false;

            try {
                this.ws = new WebSocket(this.brokerUrl, ['mqtt']);
                this.ws.binaryType = 'arraybuffer';

                this.ws.onopen = () => {
                    if (this.ws) {
                        this.ws.send(createConnectPacket(this.clientId));
                    }
                };

                this.ws.onmessage = (e: MessageEvent) => {
                    const bytes = new Uint8Array(e.data as ArrayBuffer);
                    const type = bytes[0] >> 4;

                    if (type === 2) { // CONNACK
                        this.isConnected = true;
                        this.startPing();
                        if (this.ws && this.currentTopic) {
                            this.ws.send(createSubscribePacket(this.currentTopic));
                        }
                    } else if (type === 9) { // SUBACK
                        if (!resolved) {
                            resolved = true;
                            resolve(true);
                        }
                        while (this.pendingMessages.length > 0) {
                            const pending = this.pendingMessages.shift();
                            if (pending) this.publish(this.currentTopic, pending);
                        }
                    } else if (type === 3) { // PUBLISH
                        try {
                            const { topic: inTopic, message } = parsePublishPacket(bytes);
                            const parsed = JSON.parse(message);
                            if (this.onMessageCallback) {
                                this.onMessageCallback(parsed, inTopic);
                            }
                        } catch (err) {
                            console.warn('[Cloud Relay Parse Warning]:', err);
                        }
                    }
                };

                this.ws.onerror = (err) => {
                    console.warn('[Cloud Relay Error]:', err);
                    if (!resolved) {
                        resolved = true;
                        resolve(false);
                    }
                };

                this.ws.onclose = () => {
                    this.isConnected = false;
                    this.stopPing();
                };

                // Fast 3.5s timeout: if HiveMQ is slow, resolve with current status
                setTimeout(() => {
                    if (!resolved) {
                        resolved = true;
                        resolve(this.isConnected);
                    }
                }, 3500);
            } catch (err) {
                console.warn('[Cloud Relay Exception]:', err);
                resolve(false);
            }
        });
    }

    public publish(topic: string, data: any): void {
        const payloadStr = typeof data === 'string' ? data : JSON.stringify(data);
        if (this.ws && this.isConnected && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(createPublishPacket(topic, payloadStr));
            } catch (e) {
                console.warn('[Cloud Relay Send Error]:', e);
            }
        } else {
            if (this.pendingMessages.length < 50) {
                this.pendingMessages.push(payloadStr);
            }
        }
    }

    private startPing(): void {
        this.stopPing();
        this.pingTimer = setInterval(() => {
            if (this.ws && this.isConnected && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(new Uint8Array([0xc0, 0x00])); // PINGREQ
            }
        }, 20000);
    }

    private stopPing(): void {
        if (this.pingTimer) {
            clearInterval(this.pingTimer);
            this.pingTimer = null;
        }
    }

    public disconnect(): void {
        this.isConnected = false;
        this.stopPing();
        if (this.ws) {
            try {
                this.ws.close();
            } catch (_) {}
            this.ws = null;
        }
        this.pendingMessages = [];
        this.onMessageCallback = null;
    }
}

// ── Multiplayer Engine Service ────────────────────────────────────
class MultiplayerService {
    public isHost: boolean = false;
    public isConnected: boolean = false;
    public isGlobalHub: boolean = false;
    public roomCode: string | null = null;
    public myPlayerId: string = '';
    public myPlayerName: string = 'ผู้เล่น';
    public connectionMode: 'cloud' | 'local' | 'none' = 'none';

    private relay: CloudRelayClient = new CloudRelayClient();
    private broadcastChannel: BroadcastChannel | null = null;
    private currentTopic: string = '';

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
    public async hostRoom(customCode?: string): Promise<{ success: boolean; code: string; error?: string }> {
        this.disconnect();
        this.init();
        this.isGlobalHub = false;
        const code = customCode || this.generateRoomCode();
        this.roomCode = code;
        this.isHost = true;
        this.currentTopic = `happyfarm2d/room/${code}`;

        const connected = await this.relay.connect(this.currentTopic, (msg) => {
            this.handleNetworkMessage(msg);
        });

        this.isConnected = true;
        this.connectionMode = connected ? 'cloud' : 'local';
        this.setupBroadcastChannel(code);
        this.startHeartbeat();
        this.updateUI();

        return { success: true, code };
    }

    // ── Join A Room (เข้าร่วมโลกเพื่อนด้วยรหัส) ─────────────────
    public async joinRoom(roomCode: string, keepHubFlag?: boolean): Promise<{ success: boolean; error?: string }> {
        this.disconnect();
        this.init();
        if (!keepHubFlag) {
            this.isGlobalHub = (roomCode === '999999');
        }
        const cleanCode = roomCode.trim().replace(/[^0-9]/g, '');
        if (cleanCode.length < 4) {
            return { success: false, error: 'รหัสห้องต้องมีอย่างน้อย 4 หลัก' };
        }

        this.roomCode = cleanCode;
        this.isHost = false;
        this.currentTopic = `happyfarm2d/room/${cleanCode}`;

        const connected = await this.relay.connect(this.currentTopic, (msg) => {
            this.handleNetworkMessage(msg);
        });

        this.isConnected = true;
        this.connectionMode = connected ? 'cloud' : 'local';
        this.setupBroadcastChannel(cleanCode);
        this.startHeartbeat();
        this.sendJoinPacket();
        this.updateUI();

        return { success: true };
    }

    // ── Join Global Hub (ห้องรวมสาธารณะสำหรับพบปะผู้เล่นทุกคน) ───────
    public async joinGlobalHub(): Promise<{ success: boolean; isHost: boolean; error?: string }> {
        this.disconnect();
        this.init();
        const hubCode = '999999';
        this.roomCode = hubCode;
        this.isGlobalHub = true;
        this.isHost = true;
        this.currentTopic = 'happyfarm2d/global_hub';

        const connected = await this.relay.connect(this.currentTopic, (msg) => {
            this.handleNetworkMessage(msg);
        });

        this.isConnected = true;
        this.connectionMode = connected ? 'cloud' : 'local';
        this.setupBroadcastChannel(hubCode);
        this.startHeartbeat();
        this.sendJoinPacket();
        this.updateUI();

        return { success: true, isHost: true };
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
    private sendWorldSyncPacket(): void {
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

        this.broadcastMessage(syncMsg);
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
        // 1. Send via Cloud WebSocket Relay (works everywhere!)
        if (this.relay && this.relay.isConnected) {
            this.relay.publish(this.currentTopic, msg);
        }

        // 2. Send via local BroadcastChannel (for instant 0ms same-device dual-tabs)
        if (this.broadcastChannel) {
            try {
                this.broadcastChannel.postMessage(msg);
            } catch {}
        }
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

    // ── Disconnect / Leave ────────────────────────────────────
    public disconnect(): void {
        this.isConnected = false;
        this.isHost = false;
        this.isGlobalHub = false;
        this.roomCode = null;
        this.connectionMode = 'none';

        if (this.syncInterval) clearInterval(this.syncInterval);
        if (this.cleanupInterval) clearInterval(this.cleanupInterval);

        if (this.relay) {
            this.relay.disconnect();
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
                const modeText = this.connectionMode === 'cloud' ? 'ออนไลน์ข้ามเครื่อง (Cloud Relay)' : 'จำลองเครื่องเดียวกัน';
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
