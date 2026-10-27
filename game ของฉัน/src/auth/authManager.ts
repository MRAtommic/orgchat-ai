/* ========================================================
   ฟาร์มสุขใจ (Happy Farm 2D) - User & Save System
   Google Sign-In (OAuth2 / GSI) & Multi-User Cloud/Local Storage
   แยกบันทึกข้อมูลและโปรไฟล์ผู้เล่น: "ข้อมูล user ใคร user มัน"
   ======================================================== */

import '../types';

declare const Game: any;
declare const google: any;

export const Auth: any = (function() {
    // ── Google OAuth2 Configuration ───────────────────────────
    const GOOGLE_CLIENT_ID = "38422568920-1ahu4gj5v17jehljgjdcted7ajerhsnr.apps.googleusercontent.com";
    
    // Storage Keys
    const KEY_ACTIVE_USER_ID = "happyfarm_active_user_id";
    const KEY_USERS_REGISTRY = "happyfarm_users_registry";
    const KEY_SAVE_PREFIX    = "happyfarm_save_";

    // In-memory state
    let currentUser = null;
    let autoSaveTimer = null;
    let lastSavedTime = null;

    // ── Safe LocalStorage Wrappers ────────────────────────────
    function storageGet(key) {
        try {
            return localStorage.getItem(key);
        } catch (e) {
            console.warn("Storage access warning:", e);
            return null;
        }
    }

    function storageSet(key, value) {
        try {
            localStorage.setItem(key, value);
            return true;
        } catch (e) {
            console.error("Storage write error:", e);
            return false;
        }
    }

    // ── JWT Parser for Google GSI Token ───────────────────────
    function parseJwt(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            return JSON.parse(jsonPayload);
        } catch (e) {
            console.error("JWT parse error:", e);
            return null;
        }
    }

    // ── Users Registry (บัญชีทั้งหมดในเครื่อง) ────────────────
    function getUsersRegistry(): Record<string, any> {
        try {
            const raw = storageGet(KEY_USERS_REGISTRY);
            return raw ? JSON.parse(raw) : {};
        } catch (e) {
            return {};
        }
    }

    function saveUserToRegistry(user: any) {
        const registry = getUsersRegistry();
        registry[user.id] = {
            id: user.id,
            name: user.name,
            email: user.email || '',
            picture: user.picture || '',
            provider: user.provider || 'guest',
            lastPlayed: new Date().toISOString()
        };
        storageSet(KEY_USERS_REGISTRY, JSON.stringify(registry));
    }

    // ── Default Guest User ────────────────────────────────────
    function createGuestUser(customName?: string): any {
        return {
            id: 'guest',
            name: customName || 'ชาวสวนนิรนาม (Guest)',
            email: 'guest@happyfarm.local',
            picture: '',
            provider: 'guest'
        };
    }

    // ── Google Sign-In Initialization ─────────────────────────
    function initGoogleGSI() {
        if (typeof google === 'undefined' || !google.accounts || !google.accounts.id) {
            // Retry if GSI library is still loading
            setTimeout(initGoogleGSI, 300);
            return;
        }

        try {
            google.accounts.id.initialize({
                client_id: GOOGLE_CLIENT_ID,
                callback: handleGoogleCredentialResponse,
                auto_select: false,
                cancel_on_tap_outside: true
            });

            // Render Google Button in Login Modal
            renderGoogleButton();
        } catch (e) {
            console.warn("Google GSI Init Exception (likely running on file:// or strict sandbox):", e);
        }
    }

    function renderGoogleButton() {
        const btnContainer = document.getElementById('googleSignInBtnContainer');
        if (!btnContainer || typeof google === 'undefined' || !google.accounts || !google.accounts.id) return;

        try {
            btnContainer.innerHTML = '';
            google.accounts.id.renderButton(btnContainer, {
                theme: 'filled_blue',
                size: 'large',
                shape: 'rectangular',
                text: 'signin_with',
                logo_alignment: 'left',
                width: 280
            });
        } catch (e) {
            console.warn("Could not render official Google button:", e);
        }
    }

    // Callback when user signs in with Google
    function handleGoogleCredentialResponse(response) {
        if (!response || !response.credential) {
            alert('ไม่พบข้อมูลการเข้าสู่ระบบของ Google กรุณาลองใหม่อีกครั้ง');
            return;
        }

        const payload = parseJwt(response.credential);
        if (!payload || !payload.sub) {
            alert('ไม่สามารถตรวจสอบโทเค็น Google ได้');
            return;
        }

        const googleUser = {
            id: 'google_' + payload.sub,
            googleSub: payload.sub,
            name: payload.name || payload.given_name || 'ผู้เล่น Google',
            email: payload.email || '',
            picture: payload.picture || '',
            provider: 'google'
        };

        // Switch to this user & load their game data
        loginAs(googleUser);

        // Close login modal if open
        if (window.Game && typeof Game.closeAllModals === 'function') {
            Game.closeAllModals();
        }

        if (window.Game && typeof Game.addFloatingText === 'function') {
            Game.addFloatingText('ยินดีต้อนรับ ' + googleUser.name + '!', Game.player.x, Game.player.y - 20, '#fde047');
        }
    }

    // ── User Switching & Session Management ───────────────────
    function loginAs(user, isInitialLoad = false) {
        // Save previous user data before switching (if changing users)
        if (currentUser && currentUser.id !== user.id && window.Game && Game.player) {
            saveGame(currentUser.id, false);
        }

        currentUser = user;
        saveUserToRegistry(user);
        storageSet(KEY_ACTIVE_USER_ID, user.id);

        // Update UI Badges & Profile Displays
        updateUserUI();

        // Load this user's specific saved game
        if (window.Game) {
            loadGame(user.id);
        }
    }

    function logout() {
        if (currentUser) {
            saveGame(currentUser.id, false);
        }

        // Switch to Guest as default
        const guest = createGuestUser();
        currentUser = guest;
        storageSet(KEY_ACTIVE_USER_ID, guest.id);
        updateUserUI();

        if (window.Game) {
            loadGame(guest.id);
        }

        alert('ออกจากระบบเรียบร้อยแล้ว สลับเข้าสู่โหมด Guest (ออฟไลน์)');
    }

    // ── Game Data Serialization (แปลงข้อมูลเกมเป็น JSON) ───────
    function serializeGameState() {
        if (!window.Game || !Game.player) return null;

        // 1. Pack modified farm tiles only (super compact & fast!)
        const farmTiles = [];
        if (Game.scenes && Game.scenes.farm && Game.scenes.farm.map) {
            const fMap = Game.scenes.farm.map;
            for (let y = 0; y < Game.scenes.farm.mapHeight; y++) {
                for (let x = 0; x < Game.scenes.farm.mapWidth; x++) {
                    const tile = fMap[y][x];
                    if (tile.tilled || tile.watered || tile.crop) {
                        farmTiles.push({
                            x: x,
                            y: y,
                            tilled: !!tile.tilled,
                            watered: !!tile.watered,
                            crop: tile.crop ? {
                                cropId: tile.crop.cropId,
                                stage: tile.crop.stage,
                                daysGrown: tile.crop.daysGrown,
                                ready: !!tile.crop.ready
                            } : null
                        });
                    }
                }
            }
        }

        // 1.1 Pack modified greenhouse tiles
        const greenhouseTiles = [];
        if (Game.scenes && Game.scenes.greenhouse && Game.scenes.greenhouse.map) {
            const gMap = Game.scenes.greenhouse.map;
            for (let y = 0; y < Game.scenes.greenhouse.mapHeight; y++) {
                for (let x = 0; x < Game.scenes.greenhouse.mapWidth; x++) {
                    const tile = gMap[y][x];
                    if (tile.tilled || tile.watered || tile.crop) {
                        greenhouseTiles.push({
                            x: x,
                            y: y,
                            tilled: !!tile.tilled,
                            watered: !!tile.watered,
                            crop: tile.crop ? {
                                cropId: tile.crop.cropId,
                                stage: tile.crop.stage,
                                daysGrown: tile.crop.daysGrown,
                                ready: !!tile.crop.ready
                            } : null
                        });
                    }
                }
            }
        }

        // 2. Pack animals state
        const animalsData = (Game.animals || []).map(a => ({
            id: a.id,
            type: a.type,
            name: a.name,
            x: a.x,
            y: a.y,
            pettedToday: !!a.pettedToday,
            hasProduct: !!a.hasProduct,
            product: a.product
        }));

        // 3. Pack shop shelves
        const shelvesData = (Game.shopShelves || []).map(s => ({
            id: s.id,
            x: s.x,
            y: s.y,
            item: s.item,
            count: s.count,
            price: s.price
        }));

        // 4. Pack hired helpers
        const hiredHuntersData = (Game.hiredHunters || []).map(h => ({
            id: h.id,
            hunterId: h.hunterId,
            name: h.name,
            x: h.x,
            y: h.y
        }));

        const hiredGardenersData = (Game.hiredGardeners || []).map(g => ({
            id: g.id,
            gardenerId: g.gardenerId,
            name: g.name,
            x: g.x,
            y: g.y
        }));

        return {
            version: '1.0',
            savedAt: new Date().toISOString(),
            userId: currentUser ? currentUser.id : 'guest',
            userName: currentUser ? currentUser.name : 'Guest',
            player: {
                x: Game.player.x,
                y: Game.player.y,
                direction: Game.player.direction || 'down',
                hp: Game.player.hp,
                maxHp: Game.player.maxHp,
                energy: Game.player.energy,
                maxEnergy: Game.player.maxEnergy,
                hunger: Game.player.hunger !== undefined ? Game.player.hunger : 100,
                maxHunger: Game.player.maxHunger || 100,
                thirst: Game.player.thirst !== undefined ? Game.player.thirst : 100,
                maxThirst: Game.player.maxThirst || 100,
                gold: Game.player.gold,
                level: Game.player.level,
                xp: Game.player.xp,
                waterCan: Game.player.waterCan,
                waterCanMax: Game.player.waterCanMax,
                maxInventorySlots: Math.max(36, Game.player.maxInventorySlots || 36),
                selectedSlot: Game.player.selectedSlot || 0,
                inventory: JSON.parse(JSON.stringify(Game.player.inventory || [])),
                quests: JSON.parse(JSON.stringify(Game.player.quests || {})),
                questProgress: JSON.parse(JSON.stringify(Game.player.questProgress || {})),
                claimedBounties: JSON.parse(JSON.stringify(Game.player.claimedBounties || {})),
                defeatedBosses: JSON.parse(JSON.stringify(Game.player.defeatedBosses || {})),
                bossDefeatDay: JSON.parse(JSON.stringify(Game.player.bossDefeatDay || {})),
                equippedRings: JSON.parse(JSON.stringify(Game.player.equippedRings || [null, null])),
                openedDungeonChests: JSON.parse(JSON.stringify(Game.player.openedDungeonChests || {})),
                outfit: JSON.parse(JSON.stringify(Game.player.outfit || {})),
                houseUpgrades: JSON.parse(JSON.stringify(Game.player.houseUpgrades || {})),
                pet: Game.player.pet ? JSON.parse(JSON.stringify(Game.player.pet)) : null,
                spouse: Game.player.spouse || null,
                skillMastery: JSON.parse(JSON.stringify(Game.player.skillMastery || {})),
                masteryPoints: Game.player.masteryPoints || 0,
                npcFriendship: JSON.parse(JSON.stringify(Game.player.npcFriendship || {})),
                mineProgress: JSON.parse(JSON.stringify(Game.player.mineProgress || { currentFloor: 1, maxUnlockedFloor: 1 })),
                museumCollections: JSON.parse(JSON.stringify(Game.player.museumCollections || {})),
                equippedRune: Game.player.equippedRune || null,
                spireProgress: Game.player.spireProgress || 1,
                seenHeartEvents: JSON.parse(JSON.stringify(Game.player.seenHeartEvents || {})),
                sacredShards: JSON.parse(JSON.stringify(Game.player.sacredShards || {})),
                shrineRestored: !!Game.player.shrineRestored,
                masterMode: !!Game.player.masterMode,
                bonusBaseDamage: Game.player.bonusBaseDamage || 0
            },
            currentScene: Game.currentScene || 'farm',
            time: {
                day: Game.time ? Game.time.day : 1,
                seasonIndex: Game.time ? Game.time.seasonIndex : 0,
                hour: Game.time ? Game.time.hour : 6,
                minute: Game.time ? Game.time.minute : 0,
                weather: Game.time ? Game.time.weather : 'sun'
            },
            stats: JSON.parse(JSON.stringify(Game.stats || {})),
            farmTiles: farmTiles,
            greenhouseTiles: greenhouseTiles,
            animals: animalsData,
            shopShelves: shelvesData,
            hiredHunters: hiredHuntersData,
            hiredGardeners: hiredGardenersData,
            chests: JSON.parse(JSON.stringify(Game.chests || {})),
            placedChests: JSON.parse(JSON.stringify(Game.placedChests || {})),
            placedSprinklers: JSON.parse(JSON.stringify(Game.placedSprinklers || [])),
            placedMachines: JSON.parse(JSON.stringify(Game.placedMachines || {})),
            placedDecor: JSON.parse(JSON.stringify(Game.placedDecor || [])),
            placedLanterns: JSON.parse(JSON.stringify(Game.placedLanterns || [])),
            placedStructures: JSON.parse(JSON.stringify(Game.placedStructures || [])),
            unlockedCompendium: JSON.parse(JSON.stringify(Game.unlockedCompendium || {})),
            achievements: JSON.parse(JSON.stringify(Game.achievements || {}))
        };
    }

    // ── Save Game (บันทึกข้อมูล) ──────────────────────────────
    function saveGame(targetUserId = null, showVisualFeedback = true) {
        const uid = targetUserId || (currentUser ? currentUser.id : 'guest');
        const data = serializeGameState();
        if (!data) return false;

        const key = KEY_SAVE_PREFIX + uid;
        const success = storageSet(key, JSON.stringify(data));

        if (success) {
            lastSavedTime = new Date();
            updateSaveBadge('saved', 'บันทึกแล้ว');

            // Update user registry with latest gold & day
            if (currentUser && currentUser.id === uid) {
                const reg = getUsersRegistry();
                if (reg[uid]) {
                    reg[uid].lastDay = data.time.day;
                    reg[uid].lastGold = data.player.gold;
                    reg[uid].lastSaved = lastSavedTime.toISOString();
                    storageSet(KEY_USERS_REGISTRY, JSON.stringify(reg));
                }
            }

            if (showVisualFeedback && window.Game && typeof Game.addFloatingText === 'function') {
                Game.addFloatingText('บันทึกเกมสำเร็จ!', Game.player.x, Game.player.y - 15, '#86efac');
            }
            return true;
        } else {
            updateSaveBadge('error', 'บันทึกล้มเหลว');
            return false;
        }
    }

    // ── Save Compression & Decompression (Sync Code) ─────────
    async function compressSaveData(dataObj: any): Promise<string> {
        const jsonStr = JSON.stringify(dataObj);
        try {
            if (typeof CompressionStream !== 'undefined') {
                const stream = new Blob([jsonStr]).stream();
                const cs = stream.pipeThrough(new CompressionStream('gzip'));
                const blob = await new Response(cs).blob();
                const ab = await blob.arrayBuffer();
                const bytes = new Uint8Array(ab);
                let binary = '';
                const chunk = 8192;
                for (let i = 0; i < bytes.length; i += chunk) {
                    binary += String.fromCharCode.apply(null, Array.from(bytes.subarray(i, i + chunk)));
                }
                return 'GZ:' + btoa(binary);
            }
        } catch (e) {
            console.warn("CompressionStream failed, using raw fallback:", e);
        }
        return 'RAW:' + btoa(encodeURIComponent(jsonStr));
    }

    async function decompressSaveData(codeStr: string): Promise<any> {
        const trimmed = (codeStr || '').trim();
        if (!trimmed) throw new Error("รหัสเซฟว่างเปล่า");

        if (trimmed.startsWith('GZ:')) {
            const rawBase64 = trimmed.slice(3);
            const binary = atob(rawBase64);
            const bytes = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) {
                bytes[i] = binary.charCodeAt(i);
            }
            if (typeof DecompressionStream !== 'undefined') {
                const stream = new Blob([bytes]).stream();
                const ds = stream.pipeThrough(new DecompressionStream('gzip'));
                const text = await new Response(ds).text();
                return JSON.parse(text);
            } else {
                throw new Error("เบราว์เซอร์นี้ไม่รองรับการคลายบีบอัด Gzip กรุณาใช้วิธีนำเข้าไฟล์ .json");
            }
        } else if (trimmed.startsWith('RAW:')) {
            const jsonStr = decodeURIComponent(atob(trimmed.slice(4)));
            return JSON.parse(jsonStr);
        } else if (trimmed.startsWith('{')) {
            return JSON.parse(trimmed);
        } else {
            try {
                const jsonStr = decodeURIComponent(atob(trimmed));
                return JSON.parse(jsonStr);
            } catch (e) {
                return JSON.parse(trimmed);
            }
        }
    }

    // ── Restore Game From Serialized Data ─────────────────────
    function restoreGameFromData(data: any, saveToStorage = false): boolean {
        if (!window.Game || !data || !data.player) return false;

        // 1. Restore Player Data
        Object.assign(Game.player, {
            x: data.player.x,
            y: data.player.y,
            direction: data.player.direction || 'down',
            hp: data.player.hp,
            maxHp: data.player.maxHp,
            energy: data.player.energy,
            maxEnergy: data.player.maxEnergy,
            hunger: data.player.hunger !== undefined ? data.player.hunger : 100,
            maxHunger: data.player.maxHunger || 100,
            thirst: data.player.thirst !== undefined ? data.player.thirst : 100,
            maxThirst: data.player.maxThirst || 100,
            gold: data.player.gold,
            level: data.player.level,
            xp: data.player.xp,
            waterCan: data.player.waterCan,
            waterCanMax: data.player.waterCanMax,
            maxInventorySlots: Math.max(36, data.player.maxInventorySlots || 36),
            selectedSlot: data.player.selectedSlot || 0,
            inventory: data.player.inventory || [],
            quests: Object.assign({ q1: 'active', q2: 'not_started', q3: 'not_started', q4: 'not_started', q5: 'not_started', q6: 'not_started', q7: 'not_started', q8: 'not_started', q9: 'not_started', q10: 'not_started' }, data.player.quests || {}),
            questProgress: Object.assign({ bugsDefeated: 0, sporesCollected: 0, wolvesKilled: 0, rubiesMined: 0, manaGemsFound: 0, caveMonstersDefeated: 0, kathurosDefeated: false, bossDefeated: false, luminarchDefeated: false, hydrakisDefeated: false, ignistronDefeated: false, frostfangDefeated: false, malakorDefeated: false }, data.player.questProgress || {}),
            claimedBounties: data.player.claimedBounties || {},
            defeatedBosses: data.player.defeatedBosses || {},
            bossDefeatDay: data.player.bossDefeatDay || {},
            equippedRings: data.player.equippedRings || [null, null],
            openedDungeonChests: data.player.openedDungeonChests || {},
            outfit: data.player.outfit || { hatStyle: 'straw', shirtColor: '#3b82f6', overallsColor: '#1e3a8a', hairColor: '#78350f' },
            houseUpgrades: data.player.houseUpgrades || { bed_deluxe: false, fireplace: false, refrigerator: false, tea_table: false, persian_rug: false },
            pet: data.player.pet || null,
            spouse: data.player.spouse || null,
            skillMastery: data.player.skillMastery || {},
            masteryPoints: data.player.masteryPoints || 0,
            npcFriendship: data.player.npcFriendship || {},
            mineProgress: data.player.mineProgress || { currentFloor: 1, maxUnlockedFloor: 1 },
            museumCollections: data.player.museumCollections || {},
            equippedRune: data.player.equippedRune || null,
            spireProgress: data.player.spireProgress || 1,
            seenHeartEvents: data.player.seenHeartEvents || {},
            sacredShards: data.player.sacredShards || {},
            shrineRestored: !!data.player.shrineRestored,
            masterMode: !!data.player.masterMode,
            bonusBaseDamage: data.player.bonusBaseDamage || 0
        });

        // Ensure inventory slots match maxInventorySlots (minimum 36)
        const targetSlots = Math.max(Game.player.maxInventorySlots || 36, (Game.player.inventory || []).length);
        while (Game.player.inventory.length < targetSlots) {
            Game.player.inventory.push(null);
        }

        // 2. Restore Time & Calendar
        if (data.time && Game.time) {
            Game.time.day = data.time.day || 1;
            Game.time.seasonIndex = data.time.seasonIndex || 0;
            Game.time.hour = data.time.hour || 6;
            Game.time.minute = data.time.minute || 0;
            Game.time.weather = data.time.weather || 'sun';
        }

        // 3. Restore Stats
        if (data.stats && Game.stats) {
            Object.assign(Game.stats, data.stats);
        }

        // 4. Regenerate base maps and overlay saved farm crops
        Game.generateAllScenes();
        if (data.farmTiles && Game.scenes && Game.scenes.farm && Game.scenes.farm.map) {
            const fMap = Game.scenes.farm.map;
            data.farmTiles.forEach((savedTile: any) => {
                if (fMap[savedTile.y] && fMap[savedTile.y][savedTile.x]) {
                    const target = fMap[savedTile.y][savedTile.x];
                    target.type = savedTile.tilled ? 'soil' : target.type;
                    target.tilled = savedTile.tilled;
                    target.watered = savedTile.watered;
                    target.crop = savedTile.crop;
                }
            });
        }

        // 4.1 Overlay saved greenhouse crops
        if (data.greenhouseTiles && Game.scenes && Game.scenes.greenhouse && Game.scenes.greenhouse.map) {
            const gMap = Game.scenes.greenhouse.map;
            data.greenhouseTiles.forEach((savedTile: any) => {
                if (gMap[savedTile.y] && gMap[savedTile.y][savedTile.x]) {
                    const target = gMap[savedTile.y][savedTile.x];
                    target.type = savedTile.tilled ? 'soil' : target.type;
                    target.tilled = savedTile.tilled;
                    target.watered = savedTile.watered;
                    target.crop = savedTile.crop;
                }
            });
        }

        // 5. Restore Animals
        if (data.animals && Array.isArray(data.animals) && data.animals.length > 0) {
            Game.animals = data.animals.map((a: any) => ({
                id: a.id,
                type: a.type,
                name: a.name,
                x: a.x,
                y: a.y,
                width: a.type === 'cow' ? 36 : a.type === 'chicken' ? 22 : 32,
                height: a.type === 'cow' ? 28 : a.type === 'chicken' ? 20 : 26,
                vx: 0,
                vy: 0,
                frame: 0,
                timer: 0,
                pettedToday: !!a.pettedToday,
                hasProduct: a.hasProduct !== undefined ? a.hasProduct : true,
                product: a.product
            }));
        }

        // 6. Restore Shop Shelves
        if (data.shopShelves && Array.isArray(data.shopShelves)) {
            Game.shopShelves = data.shopShelves;
        }

        // 7. Restore Hired Helpers
        if (data.hiredHunters && Array.isArray(data.hiredHunters)) {
            Game.hiredHunters = data.hiredHunters;
        }
        if (data.hiredGardeners && Array.isArray(data.hiredGardeners)) {
            Game.hiredGardeners = data.hiredGardeners;
        }

        // 8. Restore Chests & Placed Chests
        if (data.chests) {
            Game.chests = data.chests;
        }
        if (data.placedChests) {
            Game.placedChests = data.placedChests;
        }
        if (data.placedSprinklers && Array.isArray(data.placedSprinklers)) {
            Game.placedSprinklers = data.placedSprinklers;
        }
        if (data.placedMachines) {
            Game.placedMachines = data.placedMachines;
        }
        if (data.placedDecor && Array.isArray(data.placedDecor)) {
            Game.placedDecor = data.placedDecor;
        }
        if (data.placedLanterns && Array.isArray(data.placedLanterns)) {
            Game.placedLanterns = data.placedLanterns;
        }
        if (data.placedStructures && Array.isArray(data.placedStructures)) {
            Game.placedStructures = data.placedStructures;
        }
        if (data.unlockedCompendium) {
            Game.unlockedCompendium = data.unlockedCompendium;
        }
        if (data.achievements) {
            Game.achievements = data.achievements;
        }

        // 9. Load Scene & Center Camera
        const sceneToLoad = (data.currentScene && Game.scenes[data.currentScene]) ? data.currentScene : 'farm';
        Game.loadScene(sceneToLoad);

        const maxX = Math.max(0, Game.mapWidth * Game.tileSize - Game.width);
        const maxY = Math.max(0, Game.mapHeight * Game.tileSize - Game.height);
        Game.camera.x = Math.max(0, Math.min(Game.player.x - Game.width / 2 + 12, maxX));
        Game.camera.y = Math.max(0, Math.min(Game.player.y - Game.height / 2 + 16, maxY));

        if (typeof (window as any).SoundEngine !== 'undefined' && typeof (window as any).SoundEngine.setSceneTheme === 'function') {
            (window as any).SoundEngine.setSceneTheme(sceneToLoad);
        }

        // Retroactive recovery: If player defeated wolves or bugs before the drop fix, grant materials!
        if (Game.player && Game.player.questProgress) {
            if ((Game.player.questProgress.wolvesKilled || 0) > 0 && Game.countItemInInventory('wolf_fang') === 0) {
                const fangs = Math.max(1, Math.min(4, Game.player.questProgress.wolvesKilled));
                Game.addItemToInventory('wolf_fang', fangs, 'เขี้ยวหมาป่าอาถรรพ์');
                Game.addItemToInventory('shadow_pelt', fangs, 'หนังหมาป่าเงา');
            }
            if ((Game.player.questProgress.bugsDefeated || 0) > 0 && Game.countItemInInventory('blight_spore') === 0) {
                const spores = Math.max(2, Math.min(6, Game.player.questProgress.bugsDefeated));
                Game.addItemToInventory('blight_spore', spores, 'สปอร์กลายพันธุ์ (Blight Spore)');
            }
        }

        // Refresh UI
        Game.updateHUD();
        if (typeof Game.renderHotbar === 'function') Game.renderHotbar();
        lastSavedTime = data.savedAt ? new Date(data.savedAt) : new Date();
        updateSaveBadge('saved', 'โหลดเซฟแล้ว');

        // Optional save to local storage (for imports / sync)
        if (saveToStorage) {
            const uid = (currentUser ? currentUser.id : 'guest');
            storageSet(KEY_SAVE_PREFIX + uid, JSON.stringify(data));
            const reg = getUsersRegistry();
            if (reg[uid]) {
                reg[uid].lastDay = data.time ? data.time.day : 1;
                reg[uid].lastGold = data.player ? data.player.gold : 0;
                reg[uid].lastSaved = new Date().toISOString();
                storageSet(KEY_USERS_REGISTRY, JSON.stringify(reg));
            }
            updateSaveBadge('saved', 'บันทึกแล้ว');
        }

        return true;
    }

    // ── Load Game (โหลดข้อมูล) ────────────────────────────────
    function loadGame(targetUserId = null) {
        const uid = targetUserId || (currentUser ? currentUser.id : 'guest');
        const key = KEY_SAVE_PREFIX + uid;
        const raw = storageGet(key);

        if (!raw) {
            console.log("No existing save found for user:", uid, "- Starting fresh farm!");
            initFreshGameForUser();
            return false;
        }

        try {
            const data = JSON.parse(raw);
            if (!data || !data.player) {
                initFreshGameForUser();
                return false;
            }
            const success = restoreGameFromData(data, false);
            if (success && typeof Game.addFloatingText === 'function') {
                Game.addFloatingText('ยินดีต้อนรับกลับ ' + (currentUser ? currentUser.name : ''), Game.player.x, Game.player.y - 15, '#fde047');
            }
            return success;
        } catch (e) {
            console.error("Failed to parse save data:", e);
            initFreshGameForUser();
            return false;
        }
    }

    // ── Fresh Game Generator for New User ─────────────────────
    function initFreshGameForUser() {
        if (!window.Game) return;

        // Reset Player to default starting values
        Game.player.x = 6 * 32;
        Game.player.y = 6 * 32;
        Game.player.hp = 100;
        Game.player.maxHp = 100;
        Game.player.energy = 100;
        Game.player.maxEnergy = 100;
        Game.player.hunger = 100;
        Game.player.maxHunger = 100;
        Game.player.thirst = 100;
        Game.player.maxThirst = 100;
        Game.player.gold = 600;
        Game.player.level = 1;
        Game.player.xp = 0;
        Game.player.waterCan = 10;
        Game.player.waterCanMax = 10;
        Game.player.selectedSlot = 0;
        Game.player.quests = { q1: 'active', q2: 'not_started', q3: 'not_started', q4: 'not_started', q5: 'not_started', q6: 'not_started', q7: 'not_started', q8: 'not_started', q9: 'not_started', q10: 'not_started' };
        Game.player.questProgress = { bugsDefeated: 0, sporesCollected: 0, wolvesKilled: 0, rubiesMined: 0, manaGemsFound: 0, caveMonstersDefeated: 0, kathurosDefeated: false, bossDefeated: false, luminarchDefeated: false, hydrakisDefeated: false, ignistronDefeated: false, frostfangDefeated: false, malakorDefeated: false };
        Game.player.claimedBounties = {};
        Game.player.defeatedBosses = {};
        Game.player.equippedRings = [null, null];
        Game.player.openedDungeonChests = {};
        Game.player.houseUpgrades = { bed_deluxe: false, fireplace: false, refrigerator: false, tea_table: false, persian_rug: false };
        Game.player.outfit = { hatStyle: 'straw', shirtColor: '#3b82f6', overallsColor: '#1e3a8a', hairColor: '#78350f' };

        Game.player.maxInventorySlots = 36;
        Game.player.bossDefeatDay = {};
        Game.placedChests = {};

        if (typeof Game.initInventory === 'function') Game.initInventory();
        if (typeof Game.generateAllScenes === 'function') Game.generateAllScenes();
        if (typeof Game.spawnAnimals === 'function') Game.spawnAnimals();

        Game.shopShelves = [
            { id: 0, x: 6, y: 7, item: 'wheat', count: 6, price: 25 },
            { id: 1, x: 10, y: 7, item: 'carrot', count: 4, price: 40 },
            { id: 2, x: 14, y: 7, item: 'tomato', count: 3, price: 65 },
            { id: 3, x: 18, y: 7, item: 'milk', count: 2, price: 60 }
        ];
        Game.hiredHunters = [];
        Game.hiredGardeners = [];
        Game.chests = {};

        if (Game.time) {
            Game.time.day = 1;
            Game.time.seasonIndex = 0;
            Game.time.hour = 6;
            Game.time.minute = 0;
            Game.time.weather = 'sun';
        }

        Game.loadScene('farm');
        Game.updateHUD();

        // Save fresh game immediately so user slot is created
        saveGame(currentUser ? currentUser.id : 'guest', false);
    }

    // ── UI Updates ────────────────────────────────────────────
    function updateUserUI() {
        const user = currentUser || createGuestUser();
        const avatarEl = document.getElementById('hudUserAvatar');
        const nameEl = document.getElementById('hudUserName');
        const providerBadge = document.getElementById('hudUserProvider');

        if (nameEl) {
            nameEl.textContent = user.name;
        }

        if (avatarEl) {
            if (user.picture) {
                avatarEl.innerHTML = `<img src="${user.picture}" alt="${user.name}" class="avatar-img" />`;
            } else {
                const initial = user.name ? user.name.charAt(0).toUpperCase() : 'G';
                avatarEl.innerHTML = `<span class="avatar-initial">${initial}</span>`;
            }
        }

        if (providerBadge) {
            if (user.provider === 'google') {
                providerBadge.innerHTML = `<span class="badge-google" title="Google Account">G</span>`;
            } else {
                providerBadge.innerHTML = `<span class="badge-guest" title="Guest Account">Guest</span>`;
            }
        }
    }

    function updateSaveBadge(status, text) {
        const badge = document.getElementById('hudSaveBadge');
        if (!badge) return;

        badge.className = 'hud-save-badge save-' + status;
        badge.innerHTML = `<span class="save-text">${text}</span>`;
    }

    // ── Render Account Modal ──────────────────────────────────
    function renderAccountModal() {
        const user = currentUser || createGuestUser();
        const modalBody = document.getElementById('accountModalBody');
        if (!modalBody) return;

        const reg = getUsersRegistry();
        const userListHtml = Object.values(reg).map(u => {
            const isActive = u.id === user.id;
            const icon = u.provider === 'google' ? '[Google]' : '[Local]';
            const saveSummary = u.lastDay ? `วันที่ ${u.lastDay} • ${u.lastGold || 0} G` : 'ยังไม่มีข้อมูล';
            return `
                <div class="user-card-item ${isActive ? 'active-user' : ''}" onclick="Auth.switchUser('${u.id}')">
                    <div class="user-card-left">
                        <span class="user-card-icon" style="font-size: 11px; font-weight: bold; color: #d4a373;">${icon}</span>
                        <div>
                            <div class="user-card-name">${u.name} ${isActive ? '<span class="tag-current">กำลังเล่น</span>' : ''}</div>
                            <div class="user-card-meta">${saveSummary}</div>
                        </div>
                    </div>
                    <button class="btn-user-select">${isActive ? 'กำลังใช้' : 'สลับเล่น'}</button>
                </div>
            `;
        }).join('');

        const timeStr = lastSavedTime ? lastSavedTime.toLocaleTimeString('th-TH') : 'ยังไม่ได้บันทึก';

        modalBody.innerHTML = `
            <div class="account-profile-box">
                <div class="profile-avatar-large">
                    ${user.picture ? `<img src="${user.picture}" alt="${user.name}" />` : `<span class="large-initial">${user.name.charAt(0)}</span>`}
                </div>
                <div class="profile-info-details">
                    <h3 class="profile-display-name">${user.name}</h3>
                    <p class="profile-email">${user.email || 'ออฟไลน์ / บันทึกในเครื่อง'}</p>
                    <div class="profile-badges-row">
                        <span class="badge-pill ${user.provider === 'google' ? 'pill-google' : 'pill-guest'}">
                            ${user.provider === 'google' ? 'บัญชี Google (บันทึกในเครื่องนี้)' : 'โหมด Guest ในเครื่อง'}
                        </span>
                        <span class="badge-pill pill-save">บันทึกล่าสุด: ${timeStr}</span>
                    </div>
                </div>
            </div>

            <div class="account-actions-grid">
                <button class="btn-account-action btn-save-now" onclick="Auth.saveGame(null, true)">
                    บันทึกเกมทันที (Save Now)
                </button>
                <button class="btn-account-action btn-reload-save" onclick="Auth.reloadCurrentSave()">
                    โหลดเซฟล่าสุด (Reload Save)
                </button>
            </div>

            <!-- Cross-Device Sync Card (PC <-> Mobile) -->
            <div class="sync-banner-card">
                <div class="sync-banner-header">
                    <span class="sync-banner-tag">เล่นข้ามเครื่อง (PC / มือถือ)</span>
                    <span class="sync-banner-sub">ย้ายข้อมูลฟาร์มของคุณไปเล่นต่อได้ทุกที่</span>
                </div>
                <p class="sync-banner-desc">
                    เกมนี้เก็บข้อมูลไว้ในเบราว์เซอร์ของเครื่องนี้ (Local Storage) หากคุณต้องการนำเซฟนี้ไปเล่นบนมือถือ หรือนำเซฟจากคอมพิวเตอร์มาใส่ในมือถือ ให้ใช้เมนูด้านล่างนี้:
                </p>
                <div class="sync-banner-actions">
                    <button class="btn-sync-action btn-sync-export" onclick="Auth.openExportModal()">
                        <span class="sync-btn-title">ส่งออกรหัสเซฟ (Export)</span>
                        <span class="sync-btn-sub">คัดลอกรหัสจากเครื่องนี้ไปเปิดในมือถือ</span>
                    </button>
                    <button class="btn-sync-action btn-sync-import" onclick="Auth.openImportModal()">
                        <span class="sync-btn-title">นำเข้ารหัสเซฟ (Import)</span>
                        <span class="sync-btn-sub">วางรหัสจากคอมเพื่อโหลดฟาร์มเข้ามา</span>
                    </button>
                </div>
                <div class="sync-file-row">
                    <button class="btn-file-sub" onclick="Auth.downloadSaveFile()">ดาวน์โหลดไฟล์เซฟ (.json)</button>
                    <label class="btn-file-sub" style="cursor: pointer;">
                        นำเข้าไฟล์เซฟ (.json)
                        <input type="file" accept=".json" style="display: none;" onchange="Auth.handleFileInput(this)">
                    </label>
                </div>
            </div>

            <div class="switch-accounts-section">
                <h4 class="section-sub-title">สลับบัญชีผู้เล่นบนเครื่องนี้:</h4>
                <div class="users-list-scroll">
                    ${userListHtml || '<p class="text-muted">ยังไม่มีโปรไฟล์อื่น</p>'}
                </div>
            </div>

            <div class="account-footer-actions">
                <button class="btn-primary" onclick="Auth.openLoginModal()">เข้าสู่ระบบด้วย Google บัญชีอื่น</button>
                <button class="btn-danger-outline" onclick="Auth.resetCurrentFarm()">เริ่มต้นฟาร์มใหม่</button>
            </div>
        `;
    }

    // ── Cross-Device Sync Modal Handlers ──────────────────────
    async function openExportModal() {
        if (window.Game && typeof Game.closeAllModals === 'function') {
            Game.closeAllModals();
        }
        const modal = document.getElementById('syncModal');
        const titleEl = document.getElementById('syncModalTitle');
        const bodyEl = document.getElementById('syncModalBody');
        if (!modal || !bodyEl) return;

        if (titleEl) titleEl.textContent = 'ส่งออกรหัสเซฟ (ย้ายไปเล่นบนมือถือ)';
        bodyEl.innerHTML = `
            <div style="text-align: center; padding: 20px; color: #451a03;">
                กำลังบีบอัดข้อมูลเซฟฟาร์มของคุณ...
            </div>
        `;
        modal.style.display = 'flex';

        const data = serializeGameState();
        if (!data) {
            bodyEl.innerHTML = `<p style="color: #b91c1c;">ไม่สามารถอ่านข้อมูลเกมในขณะนี้ได้</p>`;
            return;
        }

        try {
            const code = await compressSaveData(data);
            
            // Auto copy if supported
            let autoCopied = false;
            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(code);
                    autoCopied = true;
                }
            } catch (e) {
                // Clipboard permissions might require direct gesture
            }

            bodyEl.innerHTML = `
                <div class="sync-step-box">
                    <strong>ขั้นตอนนำเซฟไปเปิดในมือถือ:</strong>
                    <ol>
                        <li>กดปุ่ม <strong>[คัดลอกรหัสซิงค์]</strong> ด้านล่าง</li>
                        <li>ส่งรหัสนี้เข้ามือถือคุณ (ผ่าน LINE, Messenger หรือบันทึกโน้ต)</li>
                        <li>เปิดเกมในมือถือ กดที่โปรไฟล์มุมซ้ายบน แล้วกด <strong>[นำเข้ารหัสเซฟ (Import)]</strong> วางรหัสลงไป ฟาร์มจะกลับมาครบ 100%!</li>
                    </ol>
                </div>

                <div id="syncExportStatus" class="sync-status-msg" style="${autoCopied ? 'display: block;' : 'display: none;'}">
                    คัดลอกรหัสเซฟลงคลิปบอร์ดแล้ว! ส่งเข้ามือถือได้เลย
                </div>

                <div style="margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 11px; font-weight: bold; color: #451a03;">รหัสเซฟฟาร์มของคุณ:</span>
                    <span style="font-size: 10px; color: #78350f;">ขนาดรหัส: ${code.length} ตัวอักษร</span>
                </div>

                <textarea id="syncExportArea" class="sync-code-textarea" readonly onclick="this.select()">${code}</textarea>

                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <button class="btn-primary" style="padding: 10px; font-weight: bold; font-size: 13px;" onclick="Auth.copyExportCode()">
                        คัดลอกรหัสซิงค์ (Copy Sync Code)
                    </button>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                        <button class="btn-secondary" style="padding: 8px; font-size: 11px;" onclick="Auth.downloadSaveFile()">
                            ดาวน์โหลดไฟล์ .json
                        </button>
                        <button class="btn-secondary" style="padding: 8px; font-size: 11px;" onclick="Auth.openAccountModal()">
                            กลับหน้าบัญชี
                        </button>
                    </div>
                </div>
            `;
        } catch (e: any) {
            bodyEl.innerHTML = `<p style="color: #b91c1c;">เกิดข้อผิดพลาดในการสร้างรหัสเซฟ: ${e.message || ''}</p>`;
        }
    }

    function copyExportCode() {
        const area = document.getElementById('syncExportArea') as HTMLTextAreaElement;
        if (area) {
            area.select();
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(area.value);
            } else {
                document.execCommand('copy');
            }
            const status = document.getElementById('syncExportStatus');
            if (status) {
                status.style.display = 'block';
                status.textContent = 'คัดลอกรหัสเซฟลงคลิปบอร์ดเรียบร้อยแล้ว!';
            }
        }
    }

    function openImportModal() {
        if (window.Game && typeof Game.closeAllModals === 'function') {
            Game.closeAllModals();
        }
        const modal = document.getElementById('syncModal');
        const titleEl = document.getElementById('syncModalTitle');
        const bodyEl = document.getElementById('syncModalBody');
        if (!modal || !bodyEl) return;

        if (titleEl) titleEl.textContent = 'นำเข้ารหัสเซฟ (โหลดฟาร์มจากคอม)';
        bodyEl.innerHTML = `
            <div class="sync-step-box">
                <strong>นำข้อมูลฟาร์มจากคอมพิวเตอร์เข้าสู่เครื่องนี้:</strong>
                <p style="margin: 4px 0 0 0;">
                    วางรหัสเซฟที่คุณคัดลอกมาจากคอมพิวเตอร์ลงในช่องด้านล่าง แล้วกด <strong>[โหลดและเซฟฟาร์มทันที]</strong> ข้อมูลทั้งหมดจะถูกโหลดและบันทึกลงในมือถือเครื่องนี้
                </p>
            </div>

            <div id="syncImportStatus" class="sync-status-msg" style="display: none; background: #fee2e2; border-color: #fca5a5; color: #991b1b;"></div>

            <textarea id="syncImportArea" class="sync-code-textarea" placeholder="วางรหัสซิงค์ (ที่ขึ้นต้นด้วย GZ: หรือ RAW:) ที่นี่..."></textarea>

            <div style="display: flex; flex-direction: column; gap: 8px;">
                <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 8px;">
                    <button class="btn-secondary" style="padding: 10px; font-weight: bold; font-size: 12px;" onclick="Auth.pasteFromClipboard()">
                        วางจากคลิปบอร์ด
                    </button>
                    <button class="btn-primary" style="padding: 10px; font-weight: bold; font-size: 12px; background: linear-gradient(135deg, #15803d, #166534);" onclick="Auth.confirmImportCode()">
                        โหลดและเซฟฟาร์มทันที
                    </button>
                </div>
                <div style="display: flex; gap: 8px; align-items: center; justify-content: space-between; margin-top: 4px;">
                    <label class="btn-file-sub" style="flex: 1; cursor: pointer; padding: 7px; text-align: center;">
                        เลือกไฟล์เซฟ .json จากเครื่อง
                        <input type="file" accept=".json" style="display: none;" onchange="Auth.handleFileInput(this)">
                    </label>
                    <button class="btn-secondary" style="padding: 7px 12px; font-size: 11px;" onclick="Auth.openAccountModal()">
                        กลับหน้าบัญชี
                    </button>
                </div>
            </div>
        `;
        modal.style.display = 'flex';
    }

    async function confirmImportCode(manualCode?: string) {
        const area = document.getElementById('syncImportArea') as HTMLTextAreaElement;
        const code = manualCode || (area ? area.value.trim() : '');
        const statusEl = document.getElementById('syncImportStatus');

        if (!code) {
            if (statusEl) {
                statusEl.style.display = 'block';
                statusEl.textContent = 'กรุณาวางรหัสเซฟก่อนกดยืนยัน';
            } else {
                alert('กรุณาวางรหัสเซฟก่อนกดยืนยัน');
            }
            return;
        }

        try {
            if (statusEl) {
                statusEl.style.display = 'block';
                statusEl.style.background = '#e0f2fe';
                statusEl.style.borderColor = '#7dd3fc';
                statusEl.style.color = '#0369a1';
                statusEl.textContent = 'กำลังถอดรหัสและซิงค์ข้อมูลฟาร์ม...';
            }

            const data = await decompressSaveData(code);
            if (!data || !data.player) {
                throw new Error('โครงสร้างข้อมูลเซฟไม่ถูกต้อง');
            }

            const success = restoreGameFromData(data, true);
            if (success) {
                if (window.Game && typeof Game.closeAllModals === 'function') {
                    Game.closeAllModals();
                }
                if (window.Game && typeof Game.addFloatingText === 'function') {
                    Game.addFloatingText('ซิงค์ข้อมูลสำเร็จ! ฟาร์มพร้อมเล่นต่อแล้ว', Game.player.x, Game.player.y - 20, '#86efac');
                }
                alert('ซิงค์ฟาร์มข้ามเครื่องสำเร็จ! บันทึกข้อมูลลงอุปกรณ์นี้เรียบร้อยแล้ว');
            } else {
                throw new Error('ไม่สามารถกู้คืนข้อมูลเกมได้');
            }
        } catch (err: any) {
            console.error("Import error:", err);
            if (statusEl) {
                statusEl.style.display = 'block';
                statusEl.style.background = '#fee2e2';
                statusEl.style.borderColor = '#fca5a5';
                statusEl.style.color = '#991b1b';
                statusEl.textContent = 'รหัสเซฟไม่ถูกต้อง: ' + (err.message || 'เกิดข้อผิดพลาด');
            } else {
                alert('รหัสเซฟไม่ถูกต้อง กรุณาตรวจสอบรหัสที่คัดลอกมา');
            }
        }
    }

    async function pasteFromClipboard() {
        try {
            if (navigator.clipboard && navigator.clipboard.readText) {
                const text = await navigator.clipboard.readText();
                const area = document.getElementById('syncImportArea') as HTMLTextAreaElement;
                if (area && text) {
                    area.value = text.trim();
                }
            } else {
                alert('กรุณากดค้างที่ช่องข้อความแล้วกด วาง (Paste)');
            }
        } catch (e) {
            alert('เบราว์เซอร์ไม่อนุญาตให้อ่านคลิปบอร์ดอัตโนมัติ กรุณากดค้างที่ช่องแล้วเลือก วาง (Paste)');
        }
    }

    function downloadSaveFile() {
        const data = serializeGameState();
        if (!data) return;
        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        const safeName = (currentUser ? currentUser.name : 'farmer').replace(/[^a-zA-Z0-9_\u0E00-\u0E7F]/g, '_');
        const day = Game.time ? Game.time.day : 1;
        a.href = url;
        a.download = `HappyFarm_Save_${safeName}_Day${day}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function handleFileInput(inputEl: HTMLInputElement) {
        if (!inputEl.files || !inputEl.files[0]) return;
        const file = inputEl.files[0];
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const text = e.target?.result as string;
                const data = JSON.parse(text);
                if (!data || !data.player) {
                    alert('ไฟล์เซฟไม่ถูกต้อง ไม่พบข้อมูลผู้เล่น');
                    return;
                }
                const success = restoreGameFromData(data, true);
                if (success) {
                    if (window.Game && typeof Game.closeAllModals === 'function') {
                        Game.closeAllModals();
                    }
                    alert('โหลดไฟล์เซฟ ' + file.name + ' สำเร็จเรียบร้อยแล้ว!');
                }
            } catch (err: any) {
                alert('ไม่สามารถอ่านไฟล์เซฟได้: ' + (err.message || ''));
            }
        };
        reader.readAsText(file);
    }

    function promptNewDeviceGoogleUser(user: any) {
        if (window.Game && typeof Game.closeAllModals === 'function') {
            Game.closeAllModals();
        }
        const modal = document.getElementById('syncModal');
        const titleEl = document.getElementById('syncModalTitle');
        const bodyEl = document.getElementById('syncModalBody');
        if (!modal || !bodyEl) return;

        if (titleEl) titleEl.textContent = 'เข้าสู่ระบบบัญชี Google บนอุปกรณ์ใหม่';
        bodyEl.innerHTML = `
            <div class="sync-step-box" style="border-left: 4px solid #2563eb; background: #eff6ff;">
                <h3 style="margin: 0 0 6px 0; font-size: 14px; color: #1e3a8a;">ยินดีต้อนรับคุณ ${user.name}!</h3>
                <p style="margin: 0 0 6px 0; font-size: 11px; color: #334155; line-height: 1.5;">
                    เข้าสู่ระบบด้วยบัญชี Google สำเร็จ (${user.email || ''})<br>
                    <strong>เนื่องจากเป็นการเปิดเล่นบนอุปกรณ์นี้ครั้งแรก</strong> ระบบจึงยังไม่มีข้อมูลฟาร์มของคุณในเบราว์เซอร์ของเครื่องนี้ (เซฟหลักยังถูกเก็บอยู่อย่างปลอดภัยบนคอมพิวเตอร์ของคุณ)
                </p>
                <p style="margin: 0; font-size: 11px; color: #1e40af; font-weight: 700;">
                    คุณต้องการดึงข้อมูลฟาร์มเดิมจากคอมพิวเตอร์มาเล่นต่อหรือไม่?
                </p>
            </div>

            <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 12px;">
                <button class="btn-primary" style="padding: 12px; font-weight: bold; font-size: 13px; background: linear-gradient(135deg, #15803d, #166534);" onclick="Auth.openImportModal()">
                    นำเข้ารหัสเซฟจากคอมพิวเตอร์ (เล่นฟาร์มเดิมต่อ)
                </button>
                <button class="btn-secondary" style="padding: 10px; font-size: 12px;" onclick="Game.closeAllModals()">
                    เริ่มสร้างฟาร์มใหม่บนเครื่องนี้
                </button>
            </div>
        `;
        modal.style.display = 'flex';
    }

    // ── Open Login Modal ──────────────────────────────────────
    function openLoginModal() {
        if (window.Game && typeof Game.closeAllModals === 'function') {
            Game.closeAllModals();
        }
        const modal = document.getElementById('loginModal');
        if (modal) {
            modal.style.display = 'flex';
            renderGoogleButton();
        }
    }

    // ── Fast Profile Switcher ─────────────────────────────────
    function switchUser(targetUserId) {
        const reg = getUsersRegistry();
        const target = reg[targetUserId];
        if (target) {
            loginAs(target);
            if (window.Game && typeof Game.closeAllModals === 'function') {
                Game.closeAllModals();
            }
        }
    }

    function createNewNamedProfile() {
        const name = prompt('กรุณากรอกชื่อชาวสวนของคุณ:', 'ชาวสวน ' + Math.floor(Math.random() * 1000));
        if (name && name.trim()) {
            const newGuest = {
                id: 'player_' + Date.now(),
                name: name.trim(),
                email: '',
                picture: '',
                provider: 'local'
            };
            loginAs(newGuest);
            if (window.Game && typeof Game.closeAllModals === 'function') {
                Game.closeAllModals();
            }
        }
    }

    function resetCurrentFarm() {
        if (!confirm('คำเตือน: คุณต้องการเริ่มฟาร์มใหม่สำหรับบัญชีนี้หรือไม่? ข้อมูลพืชผลและเงินทองจะถูกรีเซ็ตทั้งหมด!')) {
            return;
        }
        initFreshGameForUser();
        if (window.Game && typeof Game.closeAllModals === 'function') {
            Game.closeAllModals();
        }
        alert('เริ่มต้นฟาร์มใหม่เรียบร้อยแล้ว!');
    }

    function reloadCurrentSave() {
        if (currentUser) {
            loadGame(currentUser.id);
            if (window.Game && typeof Game.closeAllModals === 'function') {
                Game.closeAllModals();
            }
        }
    }

    // ── Initialize Auth & Auto-Save ───────────────────────────
    function init() {
        // 1. Determine active user from storage or fallback to guest
        const lastActiveUserId = storageGet(KEY_ACTIVE_USER_ID);
        const reg = getUsersRegistry();

        if (lastActiveUserId && reg[lastActiveUserId]) {
            currentUser = reg[lastActiveUserId];
        } else {
            currentUser = createGuestUser();
            saveUserToRegistry(currentUser);
            storageSet(KEY_ACTIVE_USER_ID, currentUser.id);
        }

        updateUserUI();

        // 2. Load the user's saved game immediately on launch!
        if (window.Game) {
            loadGame(currentUser.id);
        }

        // 3. Initialize Google GSI
        initGoogleGSI();

        // 4. Setup Auto-Save Timer (every 30 seconds)
        if (autoSaveTimer) clearInterval(autoSaveTimer);
        autoSaveTimer = setInterval(() => {
            if (currentUser && window.Game && Game.player) {
                saveGame(currentUser.id, false);
            }
        }, 30000);

        // 5. Save on window unload / page refresh
        window.addEventListener('beforeunload', () => {
            if (currentUser && window.Game && Game.player) {
                saveGame(currentUser.id, false);
            }
        });
    }

    // ── Public API ────────────────────────────────────────────
    return {
        init: init,
        getCurrentUser: () => currentUser,
        saveGame: saveGame,
        loadGame: loadGame,
        loginAs: loginAs,
        logout: logout,
        openLoginModal: openLoginModal,
        openAccountModal: function() {
            renderAccountModal();
            const modal = document.getElementById('accountModal');
            if (modal) modal.style.display = 'flex';
        },
        renderAccountModal: renderAccountModal,
        switchUser: switchUser,
        createNewNamedProfile: createNewNamedProfile,
        resetCurrentFarm: resetCurrentFarm,
        reloadCurrentSave: reloadCurrentSave,
        createGuestUser: createGuestUser,
        // Cross-device sync functions
        openExportModal: openExportModal,
        openImportModal: openImportModal,
        copyExportCode: copyExportCode,
        confirmImportCode: confirmImportCode,
        pasteFromClipboard: pasteFromClipboard,
        downloadSaveFile: downloadSaveFile,
        handleFileInput: handleFileInput,
        restoreGameFromData: restoreGameFromData,
        compressSaveData: compressSaveData,
        decompressSaveData: decompressSaveData,
        promptNewDeviceGoogleUser: promptNewDeviceGoogleUser
    };
})();

if (typeof window !== 'undefined') {
    (window as any).Auth = Auth;
}

