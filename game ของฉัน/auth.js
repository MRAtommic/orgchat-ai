/* ========================================================
   🌾 ฟาร์มสุขใจ (Happy Farm 2D) - User & Save System
   Google Sign-In (OAuth2 / GSI) & Multi-User Cloud/Local Storage
   แยกบันทึกข้อมูลและโปรไฟล์ผู้เล่น: "ข้อมูล user ใคร user มัน"
   ======================================================== */

const Auth = (function() {
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
    function getUsersRegistry() {
        try {
            const raw = storageGet(KEY_USERS_REGISTRY);
            return raw ? JSON.parse(raw) : {};
        } catch (e) {
            return {};
        }
    }

    function saveUserToRegistry(user) {
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
    function createGuestUser(customName) {
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
            Game.addFloatingText('🎉 ยินดีต้อนรับ ' + googleUser.name + '!', Game.player.x, Game.player.y - 20, '#fde047');
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
                gold: Game.player.gold,
                level: Game.player.level,
                xp: Game.player.xp,
                waterCan: Game.player.waterCan,
                waterCanMax: Game.player.waterCanMax,
                selectedSlot: Game.player.selectedSlot || 0,
                inventory: JSON.parse(JSON.stringify(Game.player.inventory || [])),
                quests: JSON.parse(JSON.stringify(Game.player.quests || {})),
                questProgress: JSON.parse(JSON.stringify(Game.player.questProgress || {})),
                outfit: JSON.parse(JSON.stringify(Game.player.outfit || {})),
                houseUpgrades: JSON.parse(JSON.stringify(Game.player.houseUpgrades || {}))
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
            animals: animalsData,
            shopShelves: shelvesData,
            hiredHunters: hiredHuntersData,
            hiredGardeners: hiredGardenersData,
            chests: JSON.parse(JSON.stringify(Game.chests || {}))
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
                Game.addFloatingText('💾 บันทึกเกมสำเร็จ!', Game.player.x, Game.player.y - 15, '#86efac');
            }
            return true;
        } else {
            updateSaveBadge('error', 'บันทึกล้มเหลว');
            return false;
        }
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

            // 1. Restore Player Data
            Object.assign(Game.player, {
                x: data.player.x,
                y: data.player.y,
                direction: data.player.direction || 'down',
                hp: data.player.hp,
                maxHp: data.player.maxHp,
                energy: data.player.energy,
                maxEnergy: data.player.maxEnergy,
                gold: data.player.gold,
                level: data.player.level,
                xp: data.player.xp,
                waterCan: data.player.waterCan,
                waterCanMax: data.player.waterCanMax,
                selectedSlot: data.player.selectedSlot || 0,
                inventory: data.player.inventory || [],
                quests: data.player.quests || { q1: 'active', q2: 'not_started', q3: 'not_started' },
                questProgress: data.player.questProgress || { wolvesKilled: 0, rubiesMined: 0, bossDefeated: false },
                outfit: data.player.outfit || { hatStyle: 'straw', shirtColor: '#3b82f6', overallsColor: '#1e3a8a', hairColor: '#78350f' },
                houseUpgrades: data.player.houseUpgrades || { bed_deluxe: false, fireplace: false, refrigerator: false, tea_table: false, persian_rug: false }
            });

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
                data.farmTiles.forEach(savedTile => {
                    if (fMap[savedTile.y] && fMap[savedTile.y][savedTile.x]) {
                        const target = fMap[savedTile.y][savedTile.x];
                        target.type = savedTile.tilled ? 'soil' : target.type;
                        target.tilled = savedTile.tilled;
                        target.watered = savedTile.watered;
                        target.crop = savedTile.crop;
                    }
                });
            }

            // 5. Restore Animals
            if (data.animals && Array.isArray(data.animals) && data.animals.length > 0) {
                Game.animals = data.animals.map(a => ({
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

            // 8. Restore Chests
            if (data.chests) {
                Game.chests = data.chests;
            }

            // 9. Load Scene
            const sceneToLoad = (data.currentScene && Game.scenes[data.currentScene]) ? data.currentScene : 'farm';
            Game.loadScene(sceneToLoad);

            // Refresh UI
            Game.updateHUD();
            if (typeof Game.renderHotbar === 'function') Game.renderHotbar();
            lastSavedTime = data.savedAt ? new Date(data.savedAt) : new Date();
            updateSaveBadge('saved', 'โหลดเซฟแล้ว');

            if (typeof Game.addFloatingText === 'function') {
                Game.addFloatingText('🌾 ยินดีต้อนรับกลับ ' + (currentUser ? currentUser.name : ''), Game.player.x, Game.player.y - 15, '#fde047');
            }
            return true;
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
        Game.player.gold = 600;
        Game.player.level = 1;
        Game.player.xp = 0;
        Game.player.waterCan = 10;
        Game.player.waterCanMax = 10;
        Game.player.selectedSlot = 0;
        Game.player.quests = { q1: 'active', q2: 'not_started', q3: 'not_started' };
        Game.player.questProgress = { wolvesKilled: 0, rubiesMined: 0, bossDefeated: false };
        Game.player.houseUpgrades = { bed_deluxe: false, fireplace: false, refrigerator: false, tea_table: false, persian_rug: false };
        Game.player.outfit = { hatStyle: 'straw', shirtColor: '#3b82f6', overallsColor: '#1e3a8a', hairColor: '#78350f' };

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
        const icon = status === 'saved' ? '💾' : status === 'saving' ? '⏳' : '⚠️';
        badge.innerHTML = `<span class="save-icon">${icon}</span> <span class="save-text">${text}</span>`;
    }

    // ── Render Account Modal ──────────────────────────────────
    function renderAccountModal() {
        const user = currentUser || createGuestUser();
        const modalBody = document.getElementById('accountModalBody');
        if (!modalBody) return;

        const reg = getUsersRegistry();
        const userListHtml = Object.values(reg).map(u => {
            const isActive = u.id === user.id;
            const icon = u.provider === 'google' ? '🌐' : '👤';
            const saveSummary = u.lastDay ? `วันที่ ${u.lastDay} • 🪙 ${u.lastGold || 0} G` : 'ยังไม่มีข้อมูล';
            return `
                <div class="user-card-item ${isActive ? 'active-user' : ''}" onclick="Auth.switchUser('${u.id}')">
                    <div class="user-card-left">
                        <span class="user-card-icon">${icon}</span>
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
                            ${user.provider === 'google' ? '🌐 บัญชี Google Cloud Save' : '🎮 โหมด Guest ในเครื่อง'}
                        </span>
                        <span class="badge-pill pill-save">บันทึกล่าสุด: ${timeStr}</span>
                    </div>
                </div>
            </div>

            <div class="account-actions-grid">
                <button class="btn-account-action btn-save-now" onclick="Auth.saveGame(null, true)">
                    <span>💾</span> บันทึกเกมทันที (Save Now)
                </button>
                <button class="btn-account-action btn-reload-save" onclick="Auth.reloadCurrentSave()">
                    <span>🔄</span> โหลดเซฟล่าสุด (Reload Save)
                </button>
            </div>

            <div class="switch-accounts-section">
                <h4 class="section-sub-title">👥 สลับบัญชีผู้เล่นบนเครื่องนี้:</h4>
                <div class="users-list-scroll">
                    ${userListHtml || '<p class="text-muted">ยังไม่มีโปรไฟล์อื่น</p>'}
                </div>
            </div>

            <div class="account-footer-actions">
                <button class="btn-primary" onclick="Auth.openLoginModal()">🌐 เข้าสู่ระบบด้วย Google บัญชีอื่น</button>
                <button class="btn-danger-outline" onclick="Auth.resetCurrentFarm()">🗑️ เริ่มต้นฟาร์มใหม่</button>
            </div>
        `;
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
        if (!confirm('⚠️ คำเตือน: คุณต้องการเริ่มฟาร์มใหม่สำหรับบัญชีนี้หรือไม่? ข้อมูลพืชผลและเงินทองจะถูกรีเซ็ตทั้งหมด!')) {
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

        // 2. Initialize Google GSI
        initGoogleGSI();

        // 3. Setup Auto-Save Timer (every 35 seconds)
        if (autoSaveTimer) clearInterval(autoSaveTimer);
        autoSaveTimer = setInterval(() => {
            if (currentUser && window.Game && Game.player) {
                saveGame(currentUser.id, false);
            }
        }, 35000);

        // 4. Save on window unload / page refresh
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
        createGuestUser: createGuestUser
    };
})();
