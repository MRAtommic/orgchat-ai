/* ========================================================
   ฟาร์มสุขใจ (Happy Farm 2D) - Stardew Valley Style Engine
   With Walkable House & Shop Interiors, Outfit Wardrobe,
   House Upgrades/Decorations, and NPC Shop Customers!
   ======================================================== */

import {
    CROPS, ANIMALS, RECIPES, TOOLS, UPGRADES, LEVEL_XP, SEASONS, DAYS_PER_SEASON,
    HOUSE_DECOR_UPGRADES, OUTFIT_OPTIONS, NPC_CUSTOMERS, DEMON_BUGS, WEAPONS,
    HUNTERS, FARM_HELPERS, MONSTER_DROPS, WORLD_ITEMS, WORLD_MONSTERS,
    BOSS_KATHUROS, BOSS_LUMINARCH, BOSS_HYDRAKIS, BOSS_IGNISTRON, BOSS_FROSTFANG, BOSS_MALAKOR, BOSS_SYLVANUS, BOSS_ASTREON, BOSS_REGISTRY,
    QUESTS, NPC_STORY, FORGE_RECIPES, FISH,
    NPC_GIFTS, COMPENDIUM_CATEGORIES, ACHIEVEMENTS_DATA, ARTISAN_CONVERSIONS,
    SKILL_MASTERIES, FESTIVALS, BOUNTY_BOARD, NPC_HEART_EVENTS,
    PIRATE_SHOP_ITEMS, BOSS_KARZARAK, VOLCANO_FORGE_RECIPES
} from '../data/gamedata';
import { SPRITES } from '../sprites/sprites';
import { SoundEngine } from '../audio/soundEngine';
import { Auth } from '../auth/authManager';

// Global Game State
export const Game: any = {
    canvas: null,
    ctx: null,
    width: 800,
    height: 576,

    // Scene & Map System
    currentScene: 'farm', // 'farm', 'house', 'shop'
    scenes: {},

    // Active Map pointers (updated on scene change)
    mapWidth: 34,
    mapHeight: 24,
    tileSize: 32,
    map: [],

    // Multi-Floor Mines & Automation
    currentCaveFloor: 1,
    placedSprinklers: [],
    placedMachines: {},
    compendiumActiveTab: 'crops',
    placedLanterns: [],
    placedDecor: [],
    placedStructures: [],
    playerDashGhosts: [],
    ambientParticles: { fireflies: [], leaves: [], footprints: [], smoke: [] },
    spireCurrentFloor: 1,
    spireMonsters: [],
    spireChest: null,
    activeHeartEvent: null,
    volcanoCurrentFloor: 1,
    volcanoSwitchActive: false,

    // Player State
    player: {
        x: 6 * 32,
        y: 6 * 32,
        width: 20,
        height: 28,
        speed: 2.8,
        direction: 'down',
        frame: 0,
        animTimer: 0,
        isMoving: false,
        isMounted: false,
        pet: {
            type: 'dog',
            name: 'บัดดี้ (Buddy)',
            happiness: 100,
            x: 6 * 32 - 20,
            y: 6 * 32,
            dir: 'down',
            animTimer: 0,
            frame: 0
        },
        mineProgress: {
            currentFloor: 1,
            deepestFloor: 1,
            unlockedElevators: [1]
        },
        npcFriendship: {
            gilbert: 10,
            lilian: 10,
            valeria: 10,
            kael: 10,
            bob: 10,
            eldrin: 10
        },
        museumCollections: {
            crops: ['wheat', 'carrot'],
            fish: [],
            minerals: ['stone'],
            artisan: ['bread']
        },
        achievements: {
            first_harvest: true
        },
        achievementsClaimed: {},
        hp: 150,
        maxHp: 150,
        invincibleTimer: 0,
        isGuarding: false,
        guardTimer: 0,
        guardBreakTimer: 0,
        energy: 100,
        maxEnergy: 100,
        hunger: 100,
        maxHunger: 100,
        thirst: 100,
        maxThirst: 100,
        gold: 600,
        level: 1,
        xp: 0,
        waterCan: 10,
        waterCanMax: 10,
        selectedSlot: 0,
        inventory: [],
        quests: { q1: 'active', q2: 'not_started', q3: 'not_started', q4: 'not_started', q5: 'not_started', q6: 'not_started', q7: 'not_started', q8: 'not_started', q9: 'not_started', q10: 'not_started' },
        questProgress: { bugsDefeated: 0, sporesCollected: 0, wolvesKilled: 0, rubiesMined: 0, manaGemsFound: 0, caveMonstersDefeated: 0, kathurosDefeated: false, bossDefeated: false, cropsHarvested: 0, artisanGoodsProduced: 0, luminarchDefeated: false, hydrakisDefeated: false, ignistronDefeated: false, frostfangDefeated: false, malakorDefeated: false },
        claimedBounties: {},
        defeatedBosses: {},
        equippedRings: [null, null],
        equippedArmor: null,
        equippedShield: null,
        openedDungeonChests: {},
        outfit: {
            hatStyle: 'straw',
            shirtColor: '#3b82f6',
            overallsColor: '#1e3a8a',
            hairColor: '#78350f'
        },
        houseUpgrades: {
            bed_deluxe: false,
            fireplace: false,
            refrigerator: false,
            tea_table: false,
            persian_rug: false
        }
    },

    // Wardrobe temporary preview state
    tempOutfit: null,

    // Farm Animals
    animals: [],

    // Shop Shelves & NPC Customers
    shopShelves: [
        { id: 0, x: 6, y: 7, item: 'wheat', count: 6, price: 25 },
        { id: 1, x: 10, y: 7, item: 'carrot', count: 4, price: 40 },
        { id: 2, x: 14, y: 7, item: 'tomato', count: 3, price: 65 },
        { id: 3, x: 18, y: 7, item: 'milk', count: 2, price: 60 }
    ],
    selectedShelfIndex: null,
    shopNPCs: [],
    npcSpawnTimer: 0,

    // Particles & Floating Text
    particles: [],
    floatingTexts: [],

    // Demon Bugs & Farm Defense System
    demonBugs: [],
    projectiles: [],
    hiredHunters: [],
    hiredGardeners: [],
    bugSpawnTimer: 0,
    waveCounter: 0,
    playerShootCooldown: 0,
    waveAlertTimer: 0,

    // Open World, Monsters & Mega Boss
    worldMonsters: [],
    boss: null,
    bossTelegraphs: [] as Array<any>,
    bossGroundHazards: [] as Array<any>,
    bossDashGhosts: [] as Array<any>,
    bossShockwaves: [] as Array<any>,
    chests: {},
    placedChests: {} as Record<string, { id: string; scene: string; x: number; y: number; slots: any[]; name?: string }>,
    currentOpenChestId: null as string | null,
    activeCraftingTab: 'all' as 'all' | 'carpentry' | 'food',
    activeDialogue: null,
    meleeSlashAnim: null,

    // Time & Calendar & Weather
    time: {
        day: 1,
        seasonIndex: 0,
        hour: 6,
        minute: 0,
        timer: 0,
        weather: 'sun' // 'sun', 'rain', 'thunder', 'snow'
    },
    lightningFlashTimer: 0,

    // Fishing System State
    fishing: {
        active: false,
        state: 'idle', // 'waiting', 'biting', 'minigame', 'caught'
        targetTile: null, // { x, y }
        bobberPos: { x: 0, y: 0 },
        timer: 0,
        biteDuration: 0,
        fish: null,
        // Minigame variables (Stardew-style tension bar)
        fishPos: 40,
        fishVelocity: 0,
        fishTarget: 40,
        fishChangeTimer: 0,
        barPos: 30,
        barVelocity: 0,
        barHeight: 30,
        progress: 35,
        isHoldingPull: false
    },

    // Camera
    camera: { x: 0, y: 0 },

    // Input Keys (Layout-Independent)
    keys: {
        up: false,
        down: false,
        left: false,
        right: false
    },
    mouseTile: { x: 0, y: 0 },
    mouseWorld: { x: 0, y: 0 },

    lastTime: 0,
    activeModal: null,

    stats: {
        harvests: 0,
        sales: 0,
        crafts: 0,
        animalsPetted: 0,
        bugsDefeated: 0
    },

    inventorySwapSource: null as number | null,
    draggedSlotIndex: null as number | null,
    justFinishedTouchDrag: 0
};


// ========================================================
// 1. INITIALIZATION & SCENE MAPS GENERATION
// ========================================================

Game.init = function() {
    if (this._initialized) return;
    this._initialized = true;

    this.canvas = document.getElementById('gameCanvas');
    this.ctx = this.canvas.getContext('2d');
    this.ctx.imageSmoothingEnabled = false;

    this.resizeCanvas();
    const handleViewportResize = () => {
        this.resizeCanvas();
        this.setupTouchControls();
        this.checkOrientationNotice();
        this.updateHUD();
    };
    window.addEventListener('resize', handleViewportResize);
    window.addEventListener('orientationchange', () => setTimeout(handleViewportResize, 120));
    document.addEventListener('fullscreenchange', () => setTimeout(handleViewportResize, 120));
    document.addEventListener('webkitfullscreenchange', () => setTimeout(handleViewportResize, 120));

    this.initInventory();
    this.generateAllScenes();
    this.spawnAnimals();
    this.initVillageVillagers();
    this.initDroppedItems();
    this.initAmbientCreatures();
    this.setupInputListeners();
    this.setupTouchControls();
    if (typeof (this as any).setupSkillJoystickControls === 'function') {
        (this as any).setupSkillJoystickControls();
    }

    // Multi-User Profile & Cloud/Local Save System
    if (typeof Auth !== 'undefined') {
        Auth.init();
    }

    // Retroactive recovery: If player defeated wolves or bugs before the drop fix, grant their earned materials!
    if (this.player && this.player.questProgress) {
        if ((this.player.questProgress.wolvesKilled || 0) > 0 && this.countItemInInventory('wolf_fang') === 0) {
            const fangs = Math.max(1, Math.min(4, this.player.questProgress.wolvesKilled));
            this.addItemToInventory('wolf_fang', fangs, 'เขี้ยวหมาป่าอาถรรพ์');
            this.addItemToInventory('shadow_pelt', fangs, 'หนังหมาป่าเงา');
        }
        if ((this.player.questProgress.bugsDefeated || 0) > 0 && this.countItemInInventory('blight_spore') === 0) {
            const spores = Math.max(2, Math.min(6, this.player.questProgress.bugsDefeated));
            this.addItemToInventory('blight_spore', spores, 'สปอร์กลายพันธุ์ (Blight Spore)');
        }
    }

    // Ensure starter iron sword is available for existing saves
    if (this.player && this.player.inventory) {
        const hasMelee = this.player.inventory.some((it: any) => it && (it.id === 'iron_sword' || it.id === 'volcano_sword' || it.id === 'excalibur_sword'));
        if (!hasMelee) {
            this.addItemToInventory('iron_sword', 1, 'ดาบเหล็กกล้านักผจญภัย');
        }
        if (this.player.maxHp < 150) {
            this.player.maxHp = 150;
            this.player.hp = Math.max(this.player.hp, 150);
        }
    }

    this.updateHUD();

    // Start Game Loop
    this.lastTime = performance.now();
    requestAnimationFrame((t) => this.gameLoop(t));
};


Game.resizeCanvas = function() {
    if (!this.canvas) return;
    const isMobile = window.innerWidth <= 900 || window.innerHeight <= 560;
    const isFullscreen = !!(document.fullscreenElement || (document as any).webkitFullscreenElement);

    if (isMobile || isFullscreen) {
        // Full bleed dynamic resolution without black bars or shrinking
        this.canvas.width = Math.round(window.innerWidth);
        this.canvas.height = Math.round(window.innerHeight);
    } else {
        // Desktop windowed
        this.canvas.width = 800;
        this.canvas.height = 576;
    }

    this.width = this.canvas.width;
    this.height = this.canvas.height;

    if (this.ctx) {
        this.ctx.imageSmoothingEnabled = false;
    }
};


Game.initInventory = function() {
    this.player.maxInventorySlots = Math.max(36, this.player.maxInventorySlots || 36);
    if (!this.player.bossDefeatDay) this.player.bossDefeatDay = {};
    if (!this.player.defeatedBosses) this.player.defeatedBosses = {};
    this.player.inventory = [
        { id: 'hoe', type: 'tool', name: 'จอบ' },
        { id: 'water', type: 'tool', name: 'บัวรดน้ำ' },
        { id: 'iron_sword', type: 'weapon', name: 'ดาบเหล็กกล้านักผจญภัย' },
        { id: 'slingshot', type: 'weapon', name: 'หนังสติ๊กล่าสัตว์' },
        { id: 'scythe', type: 'tool', name: 'เคียว' },
        { id: 'axe', type: 'tool', name: 'ขวานตัดไม้' },
        { id: 'bread', type: 'food', name: 'ขนมปังอบสด', count: 5, energyRestore: 40 },
        { id: 'milk', type: 'food', name: 'นมวัวสด', count: 3, energyRestore: 25 },
        { id: 'wheat_seed', type: 'seed', cropId: 'wheat', name: 'เมล็ดข้าวสาลี', count: 12 },
        { id: 'fishing_rod', type: 'tool', name: 'เบ็ดตกปลา' }
    ];
    while (this.player.inventory.length < this.player.maxInventorySlots) {
        this.player.inventory.push(null);
    }
};


Game.generateAllScenes = function() {
    this.scenes.farm = this.generateFarmMap();
    this.scenes.village = this.generateVillageMap();
    this.scenes.house = this.generateHouseMap();
    this.scenes.shop = this.generateShopMap();
    this.scenes.manor = this.generateManorMap();
    this.scenes.apothecary = this.generateApothecaryMap();
    this.scenes.tavern = this.generateTavernMap();
    this.scenes.forge = this.generateForgeMap();
    this.scenes.forest = this.generateForestMap();
    this.scenes.cave = this.generateCaveMap();
    this.scenes.cave_depths = this.generateCaveDepthsMap();
    this.scenes.swamp = this.generateSwampMap();
    this.scenes.volcano = this.generateVolcanoMap();
    this.scenes.frost_peak = this.generateFrostpeakMap();
    this.scenes.crypt = this.generateCryptMap();
    this.scenes.ancient_canopy = this.generateAncientCanopyMap();
    this.scenes.tempest_plateau = this.generateTempestPlateauMap();
    this.scenes.greenhouse = this.generateGreenhouseMap();
    this.scenes.farmCave = this.generateFarmCaveMap();
    this.scenes.island = this.generateIslandMap();
    this.scenes.pvp_arena = this.generatePvPArenaMap();

    // Set default scene
    this.loadScene('farm');
};


Game.loadScene = function(sceneName) {
    this.currentScene = sceneName;
    const scene = this.scenes[sceneName];
    this.map = scene.map;
    this.mapWidth = scene.mapWidth;
    this.mapHeight = scene.mapHeight;

    // Ensure any placed chests in this scene are marked on map
    if (this.placedChests) {
        Object.values(this.placedChests).forEach((c: any) => {
            if (c && c.scene === sceneName && this.map[c.y] && this.map[c.y][c.x]) {
                this.map[c.y][c.x].type = 'placed_chest';
                this.map[c.y][c.x].chestId = c.id;
                this.map[c.y][c.x].solid = true;
            }
        });
    }

    // Ensure any placed sprinklers in this scene are marked on map
    if (this.placedSprinklers) {
        this.placedSprinklers.forEach((sp: any) => {
            if (sp && sp.scene === sceneName && this.map[sp.y] && this.map[sp.y][sp.x]) {
                this.map[sp.y][sp.x].type = sp.type;
                this.map[sp.y][sp.x].interactable = sp.id;
                this.map[sp.y][sp.x].solid = true;
            }
        });
    }

    // Ensure any placed machines in this scene are marked on map
    if (this.placedMachines) {
        Object.values(this.placedMachines).forEach((m: any) => {
            if (m && m.scene === sceneName && this.map[m.y] && this.map[m.y][m.x]) {
                this.map[m.y][m.x].type = m.type;
                this.map[m.y][m.x].interactable = m.id;
                this.map[m.y][m.x].solid = true;
            }
        });
    }

    // Ensure any placed decor (fences, paths) in this scene are marked on map
    if (this.placedDecor) {
        this.placedDecor.forEach((d: any) => {
            if (d && d.scene === sceneName && this.map[d.y] && this.map[d.y][d.x]) {
                this.map[d.y][d.x].type = d.type;
                this.map[d.y][d.x].decorId = d.id;
                this.map[d.y][d.x].solid = (d.type === 'wood_fence' || d.type === 'stone_fence');
            }
        });
    }

    // Ensure any placed lanterns in this scene are marked on map
    if (this.placedLanterns) {
        this.placedLanterns.forEach((l: any) => {
            if (l && l.scene === sceneName && this.map[l.y] && this.map[l.y][l.x]) {
                this.map[l.y][l.x].type = 'farm_lantern';
                this.map[l.y][l.x].lanternId = l.id;
                this.map[l.y][l.x].interactable = 'farm_lantern_' + l.id;
                this.map[l.y][l.x].solid = true;
            }
        });
    }

    // Ensure any placed structures (windmill, silo, fish_tank) in this scene are marked on map
    if (this.placedStructures) {
        this.placedStructures.forEach((st: any) => {
            if (st && st.scene === sceneName) {
                for (let dy = 0; dy < (st.height || 1); dy++) {
                    for (let dx = 0; dx < (st.width || 1); dx++) {
                        const px = st.x + dx;
                        const py = st.y + dy;
                        if (this.map[py] && this.map[py][px]) {
                            this.map[py][px].type = 'placed_structure_' + st.type;
                            this.map[py][px].structureId = st.id;
                            this.map[py][px].solid = true;
                            if (dx === 0 && dy === 0) {
                                this.map[py][px].interactable = st.type + '_interact_' + st.id;
                            }
                        }
                    }
                }
            }
        });
    }
};


// 1.1 Farm Map (Exterior)
Game.generateFarmMap = function() {
    const width = 34;
    const height = 24;
    const map = [];

    for (let y = 0; y < height; y++) {
        const row = [];
        for (let x = 0; x < width; x++) {
            row.push({
                x: x, y: y,
                type: 'grass',
                tilled: false,
                watered: false,
                crop: null,
                solid: false,
                interactable: null
            });
        }
        map.push(row);
    }

    // Border Trees & Fences
    for (let x = 0; x < width; x++) {
        map[0][x].solid = true; map[0][x].type = 'tree';
        map[height - 1][x].solid = true; map[height - 1][x].type = 'fence';
    }
    for (let y = 0; y < height; y++) {
        map[y][0].solid = true; map[y][0].type = 'tree';
        map[y][width - 1].solid = true; map[y][width - 1].type = 'tree';
    }

    // North Gate (Exit from Farm to Sunvale Village)
    for (let x = 15; x <= 17; x++) {
        map[0][x].solid = false;
        map[0][x].type = 'path';
        map[0][x].interactable = 'exit_to_village';
    }

    // ── Enhanced Cobblestone & Dirt Paths ───────────────────
    // Central North-South Highway (x: 15..17, y: 1..7)
    for (let y = 1; y <= 7; y++) {
        for (let x = 15; x <= 17; x++) {
            map[y][x].type = 'path';
        }
    }
    // Main Spine Path from y: 7 down to y: 15 (x: 16)
    for (let y = 7; y <= 15; y++) map[y][16].type = 'path';

    // Farmhouse Connection (y: 6, x: 5..15)
    for (let x = 5; x <= 15; x++) map[6][x].type = 'path';
    map[5][5].type = 'path'; // House doorstep

    // Crop Field Perimeter Paths
    for (let x = 3; x <= 16; x++) map[8][x].type = 'path';
    for (let y = 8; y <= 15; y++) map[y][7].type = 'path';

    // East-West Grand Farm Avenue (connecting Pond, Crops, Mill & Shop)
    for (let x = 4; x <= 30; x++) map[15][x].type = 'path';

    // Barn Pasture Branch
    for (let y = 13; y <= 15; y++) map[y][26].type = 'path';

    // Mill & General Store Branches
    for (let y = 15; y <= 17; y++) map[y][18].type = 'path';
    for (let y = 15; y <= 19; y++) map[y][28].type = 'path';

    // Pond Fishing Dock Branch
    for (let y = 15; y <= 17; y++) map[y][5].type = 'path';

    // ── Buildings ──────────────────────────────────────────
    // Farmhouse (x: 4..6, y: 3..5)
    for (let y = 3; y <= 5; y++) {
        for (let x = 4; x <= 6; x++) {
            map[y][x].solid = true;
            map[y][x].type = 'building';
        }
    }
    map[5][5].solid = false;
    map[5][5].interactable = 'house_door';

    // Shipping Bin, Well & Hunter Post
    map[5][8].solid = true; map[5][8].type = 'shippingBin'; map[5][8].interactable = 'shippingBin';
    map[7][9].solid = true; map[7][9].type = 'well'; map[7][9].interactable = 'well';
    map[5][12].solid = true; map[5][12].type = 'hunterPost'; map[5][12].interactable = 'hunter_post';

    // Farm Cave Entrance (North Cliff x: 10..12, y: 1)
    map[1][11].solid = false;
    map[1][11].type = 'farmCaveEntrance';
    map[1][11].interactable = 'enter_farm_cave';
    for (let y = 2; y <= 5; y++) map[y][11].type = 'path';

    // Farm Greenhouse (Upper Right x: 28..31, y: 1..3)
    for (let y = 1; y <= 3; y++) {
        for (let x = 28; x <= 30; x++) {
            map[y][x].solid = true;
            map[y][x].type = 'greenhouseBuilding';
        }
    }
    map[3][29].solid = false;
    map[3][29].type = 'greenhouseDoor';
    map[3][29].interactable = 'enter_greenhouse';
    for (let y = 4; y <= 6; y++) map[y][29].type = 'path';

    // Barn (x: 23..25, y: 3..5)
    for (let y = 3; y <= 5; y++) {
        for (let x = 23; x <= 25; x++) {
            map[y][x].solid = true;
            map[y][x].type = 'building';
        }
    }
    map[5][24].interactable = 'barn';

    // Pasture Fences
    for (let x = 21; x <= 31; x++) {
        if (x !== 24 && x !== 25) { map[5][x].solid = true; map[5][x].type = 'fence'; }
        map[13][x].solid = true; map[13][x].type = 'fence';
    }
    for (let y = 5; y <= 13; y++) {
        map[y][21].solid = true; map[y][21].type = 'fence';
        map[y][31].solid = true; map[y][31].type = 'fence';
    }
    map[13][26].solid = false; map[13][26].type = 'path';

    // Mill & General Store
    for (let y = 17; y <= 18; y++) {
        for (let x = 18; x <= 19; x++) { map[y][x].solid = true; map[y][x].type = 'building'; }
    }
    map[18][18].interactable = 'mill';

    for (let y = 17; y <= 19; y++) {
        for (let x = 27; x <= 29; x++) { map[y][x].solid = true; map[y][x].type = 'building'; }
    }
    map[19][28].solid = false;
    map[19][28].interactable = 'shop_door';

    // Farm Crop Field
    for (let y = 9; y <= 14; y++) {
        for (let x = 3; x <= 14; x++) {
            if (map[y][x].type !== 'path') {
                map[y][x].type = 'soil';
                map[y][x].tilled = true;
            }
        }
    }
    // Ready crops
    map[9][3].crop = { cropId: 'wheat', stage: 3, daysGrown: 2, ready: true };

    map[9][4].crop = { cropId: 'wheat', stage: 3, daysGrown: 2, ready: true };

    map[10][3].crop = { cropId: 'carrot', stage: 3, daysGrown: 2, ready: true };

    map[10][4].crop = { cropId: 'carrot', stage: 2, daysGrown: 1, ready: false };

    map[10][4].watered = true;
    map[11][3].crop = { cropId: 'tomato', stage: 1, daysGrown: 0, ready: false };

    map[11][3].watered = true;

    // ── Peaceful Farm Pond & Fishing Dock ───────────────────
    for (let y = 18; y <= 22; y++) {
        for (let x = 2; x <= 6; x++) {
            map[y][x].solid = true;
            map[y][x].type = 'water';
            map[y][x].interactable = 'fishing_spot';
        }
    }
    // Wooden Fishing Dock on Pond Edge (x: 4..5, y: 17..18)
    map[17][4].type = 'dock'; map[17][4].solid = false; map[17][4].interactable = 'fishing_spot';
    map[17][5].type = 'dock'; map[17][5].solid = false; map[17][5].interactable = 'fishing_spot';
    map[18][5].type = 'dock'; map[18][5].solid = false; map[18][5].interactable = 'fishing_spot';

    // ── Cozy Decorative Elements ────────────────────────────
    // 1. Lush Flower Beds around House & Store
    map[6][3].type = 'flowerBed';
    map[6][7].type = 'flowerBed';
    map[20][26].type = 'flowerBed';
    map[20][30].type = 'flowerBed';
    map[16][16].type = 'flowerBed';

    // 2. Hay Bales & Chopped Wood Stacks by Barn & House
    map[3][22].solid = true; map[3][22].type = 'hayBale';
    map[4][22].solid = true; map[4][22].type = 'hayBale';
    map[3][3].solid = true; map[3][3].type = 'woodPile';
    map[19][8].solid = true; map[19][8].type = 'woodPile'; map[19][8].interactable = 'bench';

    // 3. Forageable Wild Berry Bushes along southern border
    [
        { x: 10, y: 22 }, { x: 14, y: 22 }, { x: 22, y: 22 }, { x: 25, y: 22 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'berryBush';
        map[p.y][p.x].interactable = 'berry_bush';
    });

    // 4. Orchard Fruit Trees (Apple & Orange)
    map[16][23].solid = true; map[16][23].type = 'treeApple';
    map[16][25].solid = true; map[16][25].type = 'treeOrange';

    // 5. Mature Shade Trees
    [{x: 10, y: 3}, {x: 14, y: 3}, {x: 18, y: 3}, {x: 17, y: 11}, {x: 24, y: 20}, {x: 12, y: 19}].forEach(p => {
        map[p.y][p.x].solid = true; map[p.y][p.x].type = 'tree';
    });

    return { mapWidth: width, mapHeight: height, map: map };

};



// 1.14 Grand Sunvale Village Map (หมู่บ้านศิลาสุขาวดี & ศูนย์กลางการสำรวจโรคระบาด)
Game.generateVillageMap = function() {
    const width = 60;
    const height = 44;
    const map = [];

    for (let y = 0; y < height; y++) {
        const row = [];
        for (let x = 0; x < width; x++) {
            row.push({
                x: x, y: y,
                type: 'grass',
                solid: false,
                interactable: null
            });
        }
        map.push(row);
    }

    // 1. Border Trees & Palisade Wall
    for (let x = 0; x < width; x++) {
        map[0][x].solid = true; map[0][x].type = 'tree';
        map[height - 1][x].solid = true; map[height - 1][x].type = 'tree';
    }
    for (let y = 0; y < height; y++) {
        map[y][0].solid = true; map[y][0].type = 'tree';
        map[y][width - 1].solid = true; map[y][width - 1].type = 'tree';
    }

    // 2. North Barricade Line (Defending against Mutated Swarms)
    for (let x = 2; x < width - 2; x++) {
        if (x < 28 || x > 32) {
            map[4][x].solid = true;
            map[4][x].type = 'barricade';
            map[4][x].interactable = 'barricade';
        }
    }

    // 3. Main Boulevard Road Network (Cobblestone Path)
    // North-South Central Highway (x: 29..31, y: 0..43)
    for (let y = 0; y < height; y++) {
        for (let x = 29; x <= 31; x++) {
            map[y][x].solid = false;
            map[y][x].type = 'path';
        }
    }

    // East-West Grand Avenue (x: 4..55, y: 19..21)
    for (let y = 19; y <= 21; y++) {
        for (let x = 4; x <= 55; x++) {
            map[y][x].solid = false;
            map[y][x].type = 'path';
        }
    }

    // West Gate leading to Swamp (x: 0..3, y: 19..21)
    for (let y = 19; y <= 21; y++) {
        for (let x = 0; x <= 3; x++) {
            map[y][x].solid = false;
            map[y][x].type = 'path';
            if (x === 0) map[y][x].interactable = 'exit_to_swamp';
        }
    }

    // East Gate leading to Crypt (x: 56..width-1, y: 19..21)
    for (let y = 19; y <= 21; y++) {
        for (let x = 56; x < width; x++) {
            map[y][x].solid = false;
            map[y][x].type = 'path';
            if (x === width - 1) map[y][x].interactable = 'exit_to_crypt';
        }
    }

    // Branch Avenues to Quarters (Guaranteed solid: false)
    // Northwest Manor Avenue
    for (let x = 8; x <= 29; x++) { map[10][x].solid = false; map[10][x].type = 'path'; }
    for (let y = 10; y <= 19; y++) { map[y][11].solid = false; map[y][11].type = 'path'; }

    // Northeast Clinic Avenue
    for (let x = 31; x <= 49; x++) { map[10][x].solid = false; map[10][x].type = 'path'; }
    for (let y = 10; y <= 19; y++) { map[y][47].solid = false; map[y][47].type = 'path'; }

    // Southwest Forge Avenue
    for (let x = 8; x <= 29; x++) { map[29][x].solid = false; map[29][x].type = 'path'; }
    for (let y = 21; y <= 29; y++) { map[y][11].solid = false; map[y][11].type = 'path'; }

    // Southeast Tavern Avenue
    for (let x = 31; x <= 49; x++) { map[29][x].solid = false; map[29][x].type = 'path'; }
    for (let y = 21; y <= 29; y++) { map[y][47].solid = false; map[y][47].type = 'path'; }

    // 4. Grand Central Plaza (Cobblestone Square: x: 23..37, y: 15..25)
    for (let py = 15; py <= 25; py++) {
        for (let px = 23; px <= 37; px++) {
            map[py][px].solid = false;
            map[py][px].type = 'darkStone';
        }
    }

    // 5. Grand Central Fountain (x: 29..30, y: 19..20 - Exactly 64x64 / 2x2 tiles)
    for (let fy = 19; fy <= 20; fy++) {
        for (let fx = 29; fx <= 30; fx++) {
            map[fy][fx].solid = true;
            map[fy][fx].type = 'fountain';
            map[fy][fx].interactable = 'village_fountain';
        }
    }

    // 6. Streetlamps around the Village (placed neatly on borders, never blocking roads)
    const lampPositions = [
        { x: 23, y: 14 }, { x: 37, y: 14 },
        { x: 23, y: 26 }, { x: 37, y: 26 },
        { x: 28, y: 5 }, { x: 32, y: 5 },
        { x: 28, y: 39 }, { x: 32, y: 39 },
        { x: 13, y: 11 }, { x: 45, y: 11 },
        { x: 13, y: 28 }, { x: 45, y: 28 }
    ];
    lampPositions.forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'streetLamp';
        map[p.y][p.x].interactable = 'street_lamp';
    });

    // 7. Mayor's Manor (Northwest: x: 8..10, y: 6..8 - Exactly 96x80 / 3x2.5 tiles)
    for (let my = 6; my <= 7; my++) {
        for (let mx = 8; mx <= 10; mx++) {
            map[my][mx].solid = true;
            map[my][mx].type = 'building';
        }
    }
    // Base row at y = 8: sides solid, center door clear & enterable!
    map[8][8].solid = true; map[8][8].type = 'building';
    map[8][10].solid = true; map[8][10].type = 'building';
    map[8][9].solid = false; map[8][9].type = 'doorMat'; map[8][9].interactable = 'enter_manor';
    // Front door mat at y = 9, x = 9
    map[9][9].solid = false; map[9][9].type = 'doorMat'; map[9][9].interactable = 'enter_manor';
    // Mayor Gilbert standing on the front steps at (12, 10)
    map[10][12].solid = true;
    map[10][12].type = 'npc_gilbert';
    map[10][12].interactable = 'npc_gilbert';

    // 8. Apothecary Clinic of Lilian (Northeast: x: 46..48, y: 6..8 - Exactly 96x80 / 3x2.5 tiles)
    for (let cy = 6; cy <= 7; cy++) {
        for (let cx = 46; cx <= 48; cx++) {
            map[cy][cx].solid = true;
            map[cy][cx].type = 'building';
        }
    }
    // Base row at y = 8: sides solid, center door clear & enterable!
    map[8][46].solid = true; map[8][46].type = 'building';
    map[8][48].solid = true; map[8][48].type = 'building';
    map[8][47].solid = false; map[8][47].type = 'doorMat'; map[8][47].interactable = 'enter_apothecary';
    // Front door mat at y = 9, x = 47
    map[9][47].solid = false; map[9][47].type = 'doorMat'; map[9][47].interactable = 'enter_apothecary';
    // Apothecary Lilian standing outside her medicinal garden at (45, 10)
    map[10][45].solid = true;
    map[10][45].type = 'npc_lilian';
    map[10][45].interactable = 'npc_lilian';
    // Medicinal Herb Garden
    [{ x: 43, y: 7 }, { x: 44, y: 7 }, { x: 43, y: 8 }, { x: 44, y: 8 }].forEach(p => {
        map[p.y][p.x].solid = false;
        map[p.y][p.x].type = 'starflower';
        map[p.y][p.x].interactable = 'starflower_node';
    });

    // 9. Blacksmith Forge of Kael (Southwest: x: 8..10, y: 25..27 - Exactly 96x80 / 3x2.5 tiles)
    for (let fy = 25; fy <= 26; fy++) {
        for (let fx = 8; fx <= 10; fx++) {
            map[fy][fx].solid = true;
            map[fy][fx].type = 'building';
        }
    }
    // Base row at y = 27: sides solid, center door clear & enterable!
    map[27][8].solid = true; map[27][8].type = 'building';
    map[27][10].solid = true; map[27][10].type = 'building';
    map[27][9].solid = false; map[27][9].type = 'doorMat'; map[27][9].interactable = 'enter_forge';
    // Front door mat at y = 28, x = 9
    map[28][9].solid = false; map[28][9].type = 'doorMat'; map[28][9].interactable = 'enter_forge';
    // Kael working near the forge at (12, 29)
    map[29][12].solid = true;
    map[29][12].type = 'npc_kael';
    map[29][12].interactable = 'npc_kael';

    // 10. The Golden Crop Tavern of Bob (Southeast: x: 46..48, y: 25..27 - Exactly 96x80 / 3x2.5 tiles)
    for (let ty = 25; ty <= 26; ty++) {
        for (let tx = 46; tx <= 48; tx++) {
            map[ty][tx].solid = true;
            map[ty][tx].type = 'building';
        }
    }
    // Base row at y = 27: sides solid, center door clear & enterable!
    map[27][46].solid = true; map[27][46].type = 'building';
    map[27][48].solid = true; map[27][48].type = 'building';
    map[27][47].solid = false; map[27][47].type = 'doorMat'; map[27][47].interactable = 'enter_tavern';
    // Front door mat at y = 28, x = 47
    map[28][47].solid = false; map[28][47].type = 'doorMat'; map[28][47].interactable = 'enter_tavern';
    // Barkeeper Bob standing outside greeting guests at (45, 29)
    map[29][45].solid = true;
    map[29][45].type = 'npc_bob';
    map[29][45].interactable = 'npc_bob';

    // 11. North Gate Barricade & Captain Valeria
    map[4][27].solid = true;
    map[4][27].type = 'npc_valeria';
    map[4][27].interactable = 'npc_valeria';

    // 12. Sage Eldrin at Ancient Sanctuary Gazebo (quiet northwest courtyard)
    map[12][23].solid = true;
    map[12][23].type = 'npc_eldrin';
    map[12][23].interactable = 'npc_eldrin';
    map[11][22].solid = true; map[11][22].type = 'pillar';
    map[11][24].solid = true; map[11][24].type = 'pillar';

    // 12.1 Luna - Florist at Village Center Floral Square (x: 23, y: 17)
    map[17][23].solid = true;
    map[17][23].type = 'npc_luna';
    map[17][23].interactable = 'npc_luna';
    [{ x: 21, y: 16 }, { x: 21, y: 17 }, { x: 25, y: 16 }, { x: 25, y: 17 }].forEach(p => {
        map[p.y][p.x].solid = false;
        map[p.y][p.x].type = 'starflower';
    });

    // 12.2 Village Harbor Pier & Sailboat Dock (South-East: x: 48..54, y: 38..42)
    for (let y = 39; y <= 43; y++) {
        for (let x = 48; x <= 55; x++) {
            map[y][x].solid = true;
            map[y][x].type = 'water';
        }
    }
    for (let y = 37; y <= 41; y++) {
        map[y][51].solid = false;
        map[y][51].type = 'bridge';
    }
    map[40][51].interactable = 'sailboat_pier';
    map[41][51].solid = true;
    map[41][51].type = 'sailboat';
    map[41][51].interactable = 'sailboat_pier';
    for (let x = 32; x <= 51; x++) map[37][x].type = 'path';

    // 13. Exits & Portals
    // North Gate exit to Blighted Forest (x: 29..31, y: 0)
    for (let x = 29; x <= 31; x++) {
        map[0][x].solid = false;
        map[0][x].type = 'path';
        map[0][x].interactable = 'exit_to_forest';
    }

    // South Gate exit to Happy Farm (x: 29..31, y: 43)
    for (let x = 29; x <= 31; x++) {
        map[height - 1][x].solid = false;
        map[height - 1][x].type = 'path';
        map[height - 1][x].interactable = 'exit_to_farm';
    }

    // 14. Decorative Flower Planters & Village Park Trees
    [
        { x: 22, y: 14 }, { x: 38, y: 14 }, { x: 22, y: 26 }, { x: 38, y: 26 },
        { x: 18, y: 8 }, { x: 20, y: 8 }, { x: 40, y: 8 }, { x: 42, y: 8 },
        { x: 18, y: 32 }, { x: 20, y: 32 }, { x: 40, y: 32 }, { x: 42, y: 32 },
        { x: 5, y: 14 }, { x: 55, y: 14 }, { x: 5, y: 26 }, { x: 55, y: 26 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'tree';
    });

    // 15. The Infinite Crystal Spire Portal (Northwest Sanctuary: x: 37, y: 11)
    map[11][37].solid = true;
    map[11][37].type = 'spire_portal';
    map[11][37].interactable = 'spire_portal';

    return { mapWidth: width, mapHeight: height, map: map };

};



// 1.15 Open World Map: ผืนป่าเอลเดอร์วู้ด & วิหารจอมอสูร (Forest & Boss Sanctum)
Game.generateForestMap = function() {
    const width = 50;
    const height = 40;
    const map = [];

    for (let y = 0; y < height; y++) {
        const row = [];
        for (let x = 0; x < width; x++) {
            row.push({
                x: x, y: y,
                type: 'darkGrass',
                solid: false,
                interactable: null
            });
        }
        map.push(row);
    }

    // Border Trees
    for (let x = 0; x < width; x++) {
        map[0][x].solid = true; map[0][x].type = 'tree';
        map[height - 1][x].solid = true; map[height - 1][x].type = 'tree';
    }
    for (let y = 0; y < height; y++) {
        map[y][0].solid = true; map[y][0].type = 'tree';
        map[y][width - 1].solid = true; map[y][width - 1].type = 'tree';
    }

    // River across y: 35..36
    for (let x = 0; x < width; x++) {
        map[35][x].solid = true; map[35][x].type = 'water';
        map[36][x].solid = true; map[36][x].type = 'water';
    }

    // Wooden Bridge at x: 23..25
    for (let x = 23; x <= 25; x++) {
        map[35][x].solid = false; map[35][x].type = 'bridge';
        map[36][x].solid = false; map[36][x].type = 'bridge';
    }

    // South Exit Gate back to Sunvale Village (at x: 23..25, y: 39)
    for (let x = 23; x <= 25; x++) {
        map[37][x].type = 'path';
        map[38][x].type = 'path';
        map[39][x].solid = false;
        map[39][x].type = 'path';
        map[39][x].interactable = 'exit_to_village';
    }

    // North-West mountain road to Frostpeak (x: 2..5, y: 0..4)
    for (let x = 2; x <= 5; x++) {
        map[0][x].solid = false;
        map[0][x].type = 'path';
        map[0][x].interactable = 'exit_to_frost_peak';
        map[1][x].type = 'path';
        map[2][x].type = 'path';
        map[3][x].type = 'path';
        map[4][x].type = 'path';
    }

    // East Forest Trail to Ancient Sacred Canopy (x: width-1, y: 18..21)
    for (let y = 18; y <= 21; y++) {
        map[y][width - 1].solid = false;
        map[y][width - 1].type = 'path';
        map[y][width - 1].interactable = 'exit_to_ancient_canopy';
        map[y][width - 2].type = 'path';
        map[y][width - 3].type = 'path';
    }

    // Main Central Cobblestone Road (x: 24..25, y: 10..34)
    for (let y = 10; y <= 34; y++) {
        map[y][24].type = 'darkStone';
        map[y][25].type = 'darkStone';
    }

    // Adventurer Camp Zone (y: 28..33, x: 17..33)
    for (let cy = 28; cy <= 33; cy++) {
        for (let cx = 17; cx <= 33; cx++) {
            if (map[cy][cx].type !== 'darkStone') map[cy][cx].type = 'path';
        }
    }

    // Campfire at (25, 30)
    map[30][25].solid = true; map[30][25].type = 'campfire'; map[30][25].interactable = 'campfire';

    // Story NPCs at Camp
    map[30][22].solid = true; map[30][22].type = 'npc_valeria'; map[30][22].interactable = 'npc_valeria';
    map[30][28].solid = true; map[30][28].type = 'npc_eldrin'; map[30][28].interactable = 'npc_eldrin';
    map[32][18].solid = true; map[32][18].type = 'npc_kael'; map[32][18].interactable = 'npc_kael';

    // Boss Sanctum Arena (x: 15..35, y: 2..9)
    for (let sy = 2; sy <= 9; sy++) {
        for (let sx = 15; sx <= 35; sx++) {
            map[sy][sx].type = 'runeTile';
        }
    }

    // Sacred Celestial Shrine Altar (North center of sanctum)
    map[2][25].solid = true;
    map[2][25].type = 'shrine_altar';
    map[2][25].interactable = 'sacred_shrine_altar';

    // Ancient Cracked Pillars with Torches
    [
        { x: 16, y: 3 }, { x: 34, y: 3 },
        { x: 16, y: 8 }, { x: 34, y: 8 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'pillar';
    });

    // Mining Nodes (Ruby Crystal Boulders)
    [
        { x: 6, y: 15 }, { x: 12, y: 20 }, { x: 18, y: 14 },
        { x: 34, y: 18 }, { x: 42, y: 15 }, { x: 30, y: 22 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'rubyNode';
        map[p.y][p.x].interactable = 'ruby_node';
    });

    // Starflower Herbs (Forageable)
    [
        { x: 8, y: 22 }, { x: 15, y: 18 }, { x: 20, y: 24 },
        { x: 31, y: 14 }, { x: 40, y: 22 }, { x: 10, y: 12 }
    ].forEach(p => {
        map[p.y][p.x].solid = false;
        map[p.y][p.x].type = 'starflower';
        map[p.y][p.x].interactable = 'starflower_node';
    });

    // Treasure Chests
    map[11][5].solid = true; map[11][5].type = 'chestClosed'; map[11][5].interactable = 'chest_1';
    map[11][44].solid = true; map[11][44].type = 'chestClosed'; map[11][44].interactable = 'chest_2';

    // Ancient Cave Entrance at northeast mountains (x: 44, y: 8)
    map[8][44].solid = true;
    map[8][44].type = 'caveEntrance';
    map[8][44].interactable = 'cave_entrance';
    map[9][44].type = 'path';

    // Wilderness Trees
    [
        { x: 4, y: 12 }, { x: 7, y: 18 }, { x: 14, y: 12 }, { x: 10, y: 26 },
        { x: 36, y: 12 }, { x: 43, y: 18 }, { x: 40, y: 25 }, { x: 45, y: 15 },
        { x: 13, y: 32 }, { x: 37, y: 32 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'tree';
    });

    return { mapWidth: width, mapHeight: height, map: map };

};



// 1.16 Subterranean Crystals Cave Map (ถ้ำผลึกใต้พิภพ & เหมืองลึกหลายชั้น)
Game.generateCaveMap = function(floor: number = 1) {
    const width = 44;
    const height = 36;
    const map: any[] = [];
    this.currentCaveFloor = floor;

    for (let y = 0; y < height; y++) {
        const row: any[] = [];
        for (let x = 0; x < width; x++) {
            row.push({
                x: x, y: y,
                type: 'caveFloor',
                solid: false,
                interactable: null
            });
        }
        map.push(row);
    }

    // Border Rocky Cavern Walls
    for (let x = 0; x < width; x++) {
        map[0][x].solid = true; map[0][x].type = 'caveWall';
        map[height - 1][x].solid = true; map[height - 1][x].type = 'caveWall';
    }
    for (let y = 0; y < height; y++) {
        map[y][0].solid = true; map[y][0].type = 'caveWall';
        map[y][width - 1].solid = true; map[y][width - 1].type = 'caveWall';
    }

    // Natural Cavern Rock Formations & Chambers
    for (let y = 3; y <= 6; y++) {
        for (let x = 5; x <= 16; x++) {
            if ((x + y + floor) % 3 !== 0) { map[y][x].solid = true; map[y][x].type = 'caveWall'; }
        }
    }
    for (let y = 10; y <= 22; y++) {
        if (y !== 15 && y !== 16) {
            map[y][19].solid = true; map[y][19].type = 'caveWall';
            map[y][20].solid = true; map[y][20].type = 'caveWall';
        }
    }
    for (let y = 6; y <= 12; y++) {
        map[y][28].solid = true; map[y][28].type = 'caveWall';
        map[y][29].solid = true; map[y][29].type = 'caveWall';
    }
    for (let y = 20; y <= 27; y++) {
        map[y][30].solid = true; map[y][30].type = 'caveWall';
        map[y][31].solid = true; map[y][31].type = 'caveWall';
    }

    // Subterranean Lake (alternate floors)
    if (floor % 2 === 1) {
        for (let y = 16; y <= 22; y++) {
            for (let x = 5; x <= 14; x++) {
                map[y][x].solid = true;
                map[y][x].type = 'caveWater';
            }
        }
    }

    // Ladder Up (Exit back to forest if floor 1, else go to floor - 1)
    map[31][21].solid = false;
    map[31][21].type = 'caveLadder';
    map[31][21].interactable = (floor === 1 ? 'exit_cave' : 'cave_ladder_up');

    // Mine Shaft Elevator (Checkpoints: Floors 1, 5, 10, 15, 20)
    if (floor === 1 || floor % 5 === 0) {
        map[31][24].solid = true;
        map[31][24].type = 'caveElevator';
        map[31][24].interactable = 'cave_elevator';
    }

    // Glowing Crystal Pillars
    [
        { x: 18, y: 28 }, { x: 24, y: 28 },
        { x: 10, y: 14 }, { x: 33, y: 14 },
        { x: 21, y: 8 },  { x: 37, y: 25 },
        { x: 8, y: 25 }
    ].forEach(p => {
        if (!map[p.y][p.x].solid) {
            map[p.y][p.x].solid = true;
            map[p.y][p.x].type = 'crystalPillar';
        }
    });

    // Breakable Rocks (Scattered throughout the floor)
    const rockSpots = [
        { x: 12, y: 8 }, { x: 13, y: 8 }, { x: 14, y: 9 }, { x: 15, y: 10 },
        { x: 22, y: 12 }, { x: 23, y: 13 }, { x: 24, y: 14 },
        { x: 33, y: 18 }, { x: 34, y: 19 }, { x: 35, y: 20 },
        { x: 8, y: 26 }, { x: 9, y: 27 }, { x: 10, y: 28 },
        { x: 26, y: 8 }, { x: 27, y: 9 }, { x: 36, y: 12 },
        { x: 18, y: 24 }, { x: 22, y: 26 }, { x: 37, y: 28 }
    ];

    const secretLadderIdx = Math.floor(Math.random() * rockSpots.length);
    rockSpots.forEach((pos, idx) => {
        if (!map[pos.y][pos.x].solid) {
            map[pos.y][pos.x].solid = true;
            map[pos.y][pos.x].type = 'breakableRock';
            map[pos.y][pos.x].interactable = 'breakable_rock';
            if (idx === secretLadderIdx) {
                map[pos.y][pos.x].hasLadderDown = true;
            }
        }
    });

    // Guaranteed Open Ladder Down at Far Corner (Floors 1-19)
    if (floor < 20) {
        map[4][38].solid = false;
        map[4][38].type = 'caveLadderDown';
        map[4][38].interactable = 'cave_ladder_down';
    }

    // North-West Abyss Rift leading down to Cave Depths (Luminarch Lair)
    map[4][6].solid = false;
    map[4][6].type = 'caveLadderDown';
    map[4][6].interactable = 'exit_to_cave_depths';

    // Depth-tiered Ore Nodes:
    const oreSpots = [
        { x: 6, y: 8 }, { x: 15, y: 7 }, { x: 25, y: 6 },
        { x: 37, y: 16 }, { x: 32, y: 28 }, { x: 16, y: 26 },
        { x: 17, y: 16 }, { x: 24, y: 17 }, { x: 7, y: 26 },
        { x: 38, y: 22 }, { x: 12, y: 11 }, { x: 28, y: 18 },
        { x: 36, y: 8 }, { x: 10, y: 9 }, { x: 22, y: 4 },
        { x: 15, y: 23 }, { x: 26, y: 24 }, { x: 34, y: 5 }
    ];

    oreSpots.forEach((p, idx) => {
        if (!map[p.y][p.x].solid) {
            map[p.y][p.x].solid = true;
            if (floor >= 15 && idx % 3 === 0) {
                map[p.y][p.x].type = 'diamondNode';
                map[p.y][p.x].interactable = 'diamond_node';
            } else if (floor >= 10 && idx % 3 === 1) {
                map[p.y][p.x].type = 'rubyNode';
                map[p.y][p.x].interactable = 'ruby_node';
            } else if (floor >= 5 && idx % 2 === 0) {
                map[p.y][p.x].type = 'goldNode';
                map[p.y][p.x].interactable = 'gold_node';
            } else {
                map[p.y][p.x].type = 'manaNode';
                map[p.y][p.x].interactable = 'mana_node';
            }
        }
    });

    // Milestone Chests on floors 5, 10, 15, 20
    if (floor % 5 === 0) {
        map[5][21].solid = true;
        map[5][21].type = 'chestClosed';
        map[5][21].interactable = `cave_milestone_chest_f${floor}`;
    }

    return { mapWidth: width, mapHeight: height, map: map };

};



// 1.17 Gloom Swamp & Hydra Lair (บึงอสรพิษเงามืด)

Game.generateSwampMap = function() {
    const width = 48;
    const height = 38;
    const map: any[] = [];

    for (let y = 0; y < height; y++) {
        const row: any[] = [];
        for (let x = 0; x < width; x++) {
            row.push({ x, y, type: 'swampFloor', solid: false, interactable: null });
        }
        map.push(row);
    }

    // Border Bog Trees
    for (let x = 0; x < width; x++) {
        map[0][x].solid = true; map[0][x].type = 'bogTree';
        map[height - 1][x].solid = true; map[height - 1][x].type = 'bogTree';
    }
    for (let y = 0; y < height; y++) {
        map[y][0].solid = true; map[y][0].type = 'bogTree';
        map[y][width - 1].solid = true; map[y][width - 1].type = 'bogTree';
    }

    // Murky Toxic Bayou Water Channels
    for (let x = 4; x < width - 4; x++) {
        map[22][x].solid = true; map[22][x].type = 'swampWater';
        map[23][x].solid = true; map[23][x].type = 'swampWater';
    }
    // Wooden Boardwalk Bridges
    for (let x = 20; x <= 23; x++) {
        map[22][x].solid = false; map[22][x].type = 'bridge';
        map[23][x].solid = false; map[23][x].type = 'bridge';
    }
    for (let x = 36; x <= 39; x++) {
        map[22][x].solid = false; map[22][x].type = 'bridge';
        map[23][x].solid = false; map[23][x].type = 'bridge';
    }

    // East Exit back to Sunvale Village
    for (let y = 17; y <= 20; y++) {
        map[y][width - 1].solid = false;
        map[y][width - 1].type = 'path';
        map[y][width - 1].interactable = 'exit_swamp_to_village';
    }

    // Hydra Boss Altar (North-West Arena)
    for (let y = 3; y <= 12; y++) {
        for (let x = 8; x <= 22; x++) {
            map[y][x].type = 'runeTile';
        }
    }

    // Starflower Herbs & Swamp Minerals
    [
        { x: 10, y: 18 }, { x: 14, y: 26 }, { x: 28, y: 14 },
        { x: 34, y: 28 }, { x: 40, y: 12 }, { x: 6, y: 28 }
    ].forEach(p => {
        map[p.y][p.x].solid = false;
        map[p.y][p.x].type = 'starflower';
        map[p.y][p.x].interactable = 'starflower_node';
    });

    // Treasure Chests & Breakable Urns/Crates
    map[5][10].solid = true; map[5][10].type = 'dungeonChest'; map[5][10].interactable = 'chest_swamp_1';
    map[28][10].solid = true; map[28][10].type = 'dungeonChest'; map[28][10].interactable = 'chest_swamp_2';

    // Breakables
    [
        { x: 7, y: 7, t: 'breakable_pot' },
        { x: 23, y: 5, t: 'breakable_crate' },
        { x: 12, y: 28, t: 'breakable_pot' },
        { x: 30, y: 16, t: 'breakable_crate' },
        { x: 38, y: 26, t: 'breakable_pot' },
        { x: 16, y: 16, t: 'breakable_crate' }
    ].forEach(b => {
        map[b.y][b.x].solid = true;
        map[b.y][b.x].type = b.t;
        map[b.y][b.x].interactable = b.t;
    });

    return { mapWidth: width, mapHeight: height, map };

};





// 1.18 Crystal Cavern Abyss & Luminarch Lair (หุบเหวผลึกคริสตัลโบราณ)
Game.generateCaveDepthsMap = function() {
    const width = 46;
    const height = 36;
    const map: any[] = [];

    for (let y = 0; y < height; y++) {
        const row: any[] = [];
        for (let x = 0; x < width; x++) {
            row.push({ x, y, type: 'caveFloor', solid: false, interactable: null });
        }
        map.push(row);
    }

    // Border Cavern Walls
    for (let x = 0; x < width; x++) {
        map[0][x].solid = true; map[0][x].type = 'caveWall';
        map[height - 1][x].solid = true; map[height - 1][x].type = 'caveWall';
    }
    for (let y = 0; y < height; y++) {
        map[y][0].solid = true; map[y][0].type = 'caveWall';
        map[y][width - 1].solid = true; map[y][width - 1].type = 'caveWall';
    }

    // Subterranean Crystal Lake
    for (let y = 18; y <= 25; y++) {
        for (let x = 6; x <= 16; x++) {
            map[y][x].solid = true;
            map[y][x].type = 'caveWater';
        }
    }

    // South Ladder back to Cave Floor 1
    map[32][22].solid = false;
    map[32][22].type = 'caveLadder';
    map[32][22].interactable = 'exit_cave_depths_to_cave';

    // North-East Volcanic Rift (Portal to Volcano)
    for (let y = 4; y <= 7; y++) {
        for (let x = 39; x <= 42; x++) {
            map[y][x].type = 'magmaFloor';
        }
    }
    map[5][41].solid = false;
    map[5][41].type = 'magmaFloor';
    map[5][41].interactable = 'exit_to_volcano';

    // Luminarch Boss Arena (North-Center)
    for (let y = 3; y <= 11; y++) {
        for (let x = 16; x <= 30; x++) {
            map[y][x].type = 'runeTile';
        }
    }

    // Glowing Crystal Pillars surrounding Arena
    [
        { x: 17, y: 4 }, { x: 29, y: 4 },
        { x: 17, y: 10 }, { x: 29, y: 10 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'crystalPillar';
    });

    // Diamond & Gold Nodes
    [
        { x: 8, y: 12 }, { x: 12, y: 8 }, { x: 34, y: 18 },
        { x: 26, y: 28 }, { x: 38, y: 24 }
    ].forEach((p, idx) => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = idx % 2 === 0 ? 'diamondNode' : 'goldNode';
        map[p.y][p.x].interactable = idx % 2 === 0 ? 'diamond_node' : 'gold_node';
    });

    // Treasure Chests & Breakable Urns/Crates
    map[4][18].solid = true; map[4][18].type = 'dungeonChest'; map[4][18].interactable = 'chest_cave_depths_1';
    map[28][36].solid = true; map[28][36].type = 'dungeonChest'; map[28][36].interactable = 'chest_cave_depths_2';

    // Breakables
    [
        { x: 14, y: 5, t: 'breakable_pot' },
        { x: 32, y: 5, t: 'breakable_crate' },
        { x: 7, y: 15, t: 'breakable_pot' },
        { x: 22, y: 26, t: 'breakable_crate' },
        { x: 35, y: 22, t: 'breakable_pot' },
        { x: 40, y: 10, t: 'breakable_crate' }
    ].forEach(b => {
        map[b.y][b.x].solid = true;
        map[b.y][b.x].type = b.t;
        map[b.y][b.x].interactable = b.t;
    });

    return { mapWidth: width, mapHeight: height, map };

};





// 1.19 Ignis Magma Caldera & Dragon Lair (ปล่องภูเขาไฟอัคนีโลกันตร์)
Game.generateVolcanoMap = function() {
    const width = 50;
    const height = 38;
    const map: any[] = [];

    for (let y = 0; y < height; y++) {
        const row: any[] = [];
        for (let x = 0; x < width; x++) {
            row.push({ x, y, type: 'magmaFloor', solid: false, interactable: null });
        }
        map.push(row);
    }

    // Border Obsidian Walls
    for (let x = 0; x < width; x++) {
        map[0][x].solid = true; map[0][x].type = 'caveWall';
        map[height - 1][x].solid = true; map[height - 1][x].type = 'caveWall';
    }
    for (let y = 0; y < height; y++) {
        map[y][0].solid = true; map[y][0].type = 'caveWall';
        map[y][width - 1].solid = true; map[y][width - 1].type = 'caveWall';
    }

    // River of Molten Lava
    for (let y = 18; y <= 21; y++) {
        for (let x = 4; x < width - 4; x++) {
            map[y][x].solid = true;
            map[y][x].type = 'magmaLava';
        }
    }
    // Basalt Stone Bridges
    for (let x = 16; x <= 19; x++) {
        map[18][x].solid = false; map[18][x].type = 'magmaFloor';
        map[19][x].solid = false; map[19][x].type = 'magmaFloor';
        map[20][x].solid = false; map[20][x].type = 'magmaFloor';
        map[21][x].solid = false; map[21][x].type = 'magmaFloor';
    }
    for (let x = 32; x <= 35; x++) {
        map[18][x].solid = false; map[18][x].type = 'magmaFloor';
        map[19][x].solid = false; map[19][x].type = 'magmaFloor';
        map[20][x].solid = false; map[20][x].type = 'magmaFloor';
        map[21][x].solid = false; map[21][x].type = 'magmaFloor';
    }

    // South-West Entrance back to Cave Depths
    map[33][8].solid = false;
    map[33][8].type = 'caveFloor';
    map[33][8].interactable = 'exit_volcano_to_cave_depths';

    // Ignistron Dragon Arena (North Caldera)
    for (let y = 3; y <= 12; y++) {
        for (let x = 18; x <= 34; x++) {
            map[y][x].type = 'runeTile';
        }
    }

    // Obsidian Spire Pillars
    [
        { x: 19, y: 4 }, { x: 33, y: 4 },
        { x: 19, y: 11 }, { x: 33, y: 11 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'obsidianPillar';
    });

    // Ruby Nodes
    [
        { x: 8, y: 10 }, { x: 12, y: 26 }, { x: 26, y: 28 },
        { x: 40, y: 12 }, { x: 42, y: 26 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'rubyNode';
        map[p.y][p.x].interactable = 'ruby_node';
    });

    // Treasure Chests & Breakable Urns/Crates
    map[4][20].solid = true; map[4][20].type = 'dungeonChest'; map[4][20].interactable = 'chest_volcano_1';
    map[30][42].solid = true; map[30][42].type = 'dungeonChest'; map[30][42].interactable = 'chest_volcano_2';

    // Breakables
    [
        { x: 16, y: 6, t: 'breakable_pot' },
        { x: 36, y: 6, t: 'breakable_crate' },
        { x: 10, y: 24, t: 'breakable_pot' },
        { x: 28, y: 24, t: 'breakable_crate' },
        { x: 44, y: 18, t: 'breakable_pot' },
        { x: 38, y: 32, t: 'breakable_crate' }
    ].forEach(b => {
        map[b.y][b.x].solid = true;
        map[b.y][b.x].type = b.t;
        map[b.y][b.x].interactable = b.t;
    });

    return { mapWidth: width, mapHeight: height, map };

};





// 1.20 Frostpeak Glacial Sanctuary & Titan Lair (ยอดเขาเหมันต์นิรันดร์)
Game.generateFrostpeakMap = function() {
    const width = 48;
    const height = 38;
    const map: any[] = [];

    for (let y = 0; y < height; y++) {
        const row: any[] = [];
        for (let x = 0; x < width; x++) {
            row.push({ x, y, type: 'snowFloor', solid: false, interactable: null });
        }
        map.push(row);
    }

    // Border Pine Trees
    for (let x = 0; x < width; x++) {
        map[0][x].solid = true; map[0][x].type = 'pineTree';
        map[height - 1][x].solid = true; map[height - 1][x].type = 'pineTree';
    }
    for (let y = 0; y < height; y++) {
        map[y][0].solid = true; map[y][0].type = 'pineTree';
        map[y][width - 1].solid = true; map[y][width - 1].type = 'pineTree';
    }

    // South-East Mountain Path back to Forest
    for (let x = 22; x <= 26; x++) {
        map[height - 1][x].solid = false;
        map[height - 1][x].type = 'path';
        map[height - 1][x].interactable = 'exit_frost_peak_to_forest';
    }

    // North-East Ridge Path climbing to Tempest Lightning Plateau
    for (let x = 40; x <= 44; x++) {
        map[0][x].solid = false;
        map[0][x].type = 'path';
        map[0][x].interactable = 'exit_to_tempest_plateau';
        map[1][x].type = 'path';
        map[2][x].type = 'path';
    }

    // Frostfang Glacial Arena (North Ice Plateau)
    for (let y = 3; y <= 12; y++) {
        for (let x = 16; x <= 32; x++) {
            map[y][x].type = 'iceFloor';
        }
    }

    // Ice Pillars
    [
        { x: 17, y: 4 }, { x: 31, y: 4 },
        { x: 17, y: 11 }, { x: 31, y: 11 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'icePillar';
    });

    // Starflower & Diamond Nodes
    [
        { x: 8, y: 16 }, { x: 12, y: 24 }, { x: 36, y: 16 },
        { x: 38, y: 26 }, { x: 10, y: 30 }
    ].forEach(p => {
        map[p.y][p.x].solid = false;
        map[p.y][p.x].type = 'starflower';
        map[p.y][p.x].interactable = 'starflower_node';
    });

    // Treasure Chests & Breakable Urns/Crates
    map[5][18].solid = true; map[5][18].type = 'dungeonChest'; map[5][18].interactable = 'chest_frostpeak_1';
    map[28][10].solid = true; map[28][10].type = 'dungeonChest'; map[28][10].interactable = 'chest_frostpeak_2';

    // Breakables
    [
        { x: 14, y: 7, t: 'breakable_pot' },
        { x: 34, y: 7, t: 'breakable_crate' },
        { x: 10, y: 20, t: 'breakable_pot' },
        { x: 26, y: 22, t: 'breakable_crate' },
        { x: 34, y: 22, t: 'breakable_pot' },
        { x: 42, y: 30, t: 'breakable_crate' }
    ].forEach(b => {
        map[b.y][b.x].solid = true;
        map[b.y][b.x].type = b.t;
        map[b.y][b.x].interactable = b.t;
    });

    return { mapWidth: width, mapHeight: height, map };

};





// 1.21 Ancient Crypt of the Undead King (สุสานโบราณกษัตริย์ไร้นาม)
Game.generateCryptMap = function() {
    const width = 46;
    const height = 36;
    const map: any[] = [];

    for (let y = 0; y < height; y++) {
        const row: any[] = [];
        for (let x = 0; x < width; x++) {
            row.push({ x, y, type: 'cryptFloor', solid: false, interactable: null });
        }
        map.push(row);
    }

    // Border Crypt Walls
    for (let x = 0; x < width; x++) {
        map[0][x].solid = true; map[0][x].type = 'cryptWall';
        map[height - 1][x].solid = true; map[height - 1][x].type = 'cryptWall';
    }
    for (let y = 0; y < height; y++) {
        map[y][0].solid = true; map[y][0].type = 'cryptWall';
        map[y][width - 1].solid = true; map[y][width - 1].type = 'cryptWall';
    }

    // West Gate back to Sunvale Village
    for (let y = 17; y <= 20; y++) {
        map[y][0].solid = false;
        map[y][0].type = 'path';
        map[y][0].interactable = 'exit_crypt_to_village';
    }

    // Lord Malakor Mausoleum Arena (North Sanctuary)
    for (let y = 3; y <= 11; y++) {
        for (let x = 16; x <= 30; x++) {
            map[y][x].type = 'runeTile';
        }
    }

    // Weathered Tombstones flanking the Hall
    [
        { x: 17, y: 4 }, { x: 29, y: 4 },
        { x: 17, y: 10 }, { x: 29, y: 10 },
        { x: 8, y: 12 }, { x: 12, y: 18 }, { x: 8, y: 24 },
        { x: 36, y: 12 }, { x: 32, y: 18 }, { x: 36, y: 24 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'tombstone';
    });

    // Treasure Chests & Breakable Urns/Crates
    map[4][18].solid = true; map[4][18].type = 'dungeonChest'; map[4][18].interactable = 'chest_crypt_1';
    map[28][38].solid = true; map[28][38].type = 'dungeonChest'; map[28][38].interactable = 'chest_crypt_2';

    // Breakables
    [
        { x: 14, y: 5, t: 'breakable_pot' },
        { x: 32, y: 5, t: 'breakable_pot' },
        { x: 10, y: 14, t: 'breakable_crate' },
        { x: 34, y: 14, t: 'breakable_crate' },
        { x: 18, y: 26, t: 'breakable_pot' },
        { x: 28, y: 26, t: 'breakable_crate' }
    ].forEach(b => {
        map[b.y][b.x].solid = true;
        map[b.y][b.x].type = b.t;
        map[b.y][b.x].interactable = b.t;
    });

    return { mapWidth: width, mapHeight: height, map };

};





// 1.25 Ancient Sacred Canopy (ป่าพฤกษาศักดิ์สิทธิ์โบราณ & รังเทพพฤกษา ซิลวาเนีย)
Game.generateAncientCanopyMap = function() {
    const width = 60;
    const height = 50;
    const map: any[] = [];

    for (let y = 0; y < height; y++) {
        const row: any[] = [];
        for (let x = 0; x < width; x++) {
            row.push({ x, y, type: 'canopyGrass', solid: false, interactable: null });
        }
        map.push(row);
    }

    // Border Ancient Trees
    for (let x = 0; x < width; x++) {
        map[0][x].solid = true; map[0][x].type = 'ancientTree';
        map[height - 1][x].solid = true; map[height - 1][x].type = 'ancientTree';
    }
    for (let y = 0; y < height; y++) {
        map[y][0].solid = true; map[y][0].type = 'ancientTree';
        map[y][width - 1].solid = true; map[y][width - 1].type = 'ancientTree';
    }

    // West Forest Path back to Elderwood Forest
    for (let y = 22; y <= 26; y++) {
        map[y][0].solid = false;
        map[y][0].type = 'path';
        map[y][0].interactable = 'exit_ancient_canopy_to_forest';
        map[y][1].type = 'path';
        map[y][2].type = 'path';
    }

    // Central Cobblestone Path to North Arena
    for (let y = 14; y <= 35; y++) {
        map[y][29].type = 'path';
        map[y][30].type = 'path';
    }
    for (let x = 3; x <= 29; x++) {
        map[24][x].type = 'path';
    }

    // Sacred Altar Arena (North: x: 18..42, y: 3..14)
    for (let y = 3; y <= 14; y++) {
        for (let x = 18; x <= 42; x++) {
            map[y][x].type = 'runeTile';
        }
    }

    // Altar Pillars
    [
        { x: 19, y: 4 }, { x: 41, y: 4 },
        { x: 19, y: 13 }, { x: 41, y: 13 },
        { x: 25, y: 8 }, { x: 35, y: 8 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'pillar';
    });

    // Giant Ancient Trees scattered across forest
    [
        { x: 10, y: 10 }, { x: 12, y: 32 }, { x: 8, y: 42 },
        { x: 48, y: 12 }, { x: 50, y: 34 }, { x: 44, y: 44 },
        { x: 22, y: 38 }, { x: 38, y: 38 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'ancientTree';
    });

    // Starfruit Groves
    [
        { x: 6, y: 16 }, { x: 14, y: 20 }, { x: 8, y: 28 },
        { x: 52, y: 18 }, { x: 46, y: 26 }, { x: 54, y: 40 },
        { x: 20, y: 44 }, { x: 34, y: 44 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'starFruitCrop';
        map[p.y][p.x].interactable = 'starfruit_node';
    });

    // Fairy Springs (Water pools)
    for (let y = 28; y <= 31; y++) {
        for (let x = 14; x <= 18; x++) {
            map[y][x].solid = true;
            map[y][x].type = 'water';
        }
    }
    for (let y = 18; y <= 21; y++) {
        for (let x = 44; x <= 48; x++) {
            map[y][x].solid = true;
            map[y][x].type = 'water';
        }
    }

    // Dungeon Chests
    map[5][21].solid = true; map[5][21].type = 'dungeonChest'; map[5][21].interactable = 'chest_canopy_1';
    map[42][16].solid = true; map[42][16].type = 'dungeonChest'; map[42][16].interactable = 'chest_canopy_2';

    // Breakables
    [
        { x: 16, y: 7, t: 'breakable_pot' },
        { x: 44, y: 7, t: 'breakable_crate' },
        { x: 12, y: 25, t: 'breakable_pot' },
        { x: 48, y: 30, t: 'breakable_crate' },
        { x: 26, y: 36, t: 'breakable_pot' },
        { x: 34, y: 36, t: 'breakable_crate' }
    ].forEach(b => {
        map[b.y][b.x].solid = true;
        map[b.y][b.x].type = b.t;
        map[b.y][b.x].interactable = b.t;
    });

    return { mapWidth: width, mapHeight: height, map };
};

// 1.26 Tempest Lightning Plateau (ที่ราบสูงอัสนีบาต & บัลลังก์จ้าวพายุ ออสทริออน)
Game.generateTempestPlateauMap = function() {
    const width = 60;
    const height = 45;
    const map: any[] = [];

    for (let y = 0; y < height; y++) {
        const row: any[] = [];
        for (let x = 0; x < width; x++) {
            row.push({ x, y, type: 'basaltFloor', solid: false, interactable: null });
        }
        map.push(row);
    }

    // Border Thunder Chasms / Basalt Rocks
    for (let x = 0; x < width; x++) {
        map[0][x].solid = true; map[0][x].type = 'thunderPillar';
        map[height - 1][x].solid = true; map[height - 1][x].type = 'thunderPillar';
    }
    for (let y = 0; y < height; y++) {
        map[y][0].solid = true; map[y][0].type = 'thunderPillar';
        map[y][width - 1].solid = true; map[y][width - 1].type = 'thunderPillar';
    }

    // South-West Mountain Path back to Frostpeak
    for (let x = 12; x <= 16; x++) {
        map[height - 1][x].solid = false;
        map[height - 1][x].type = 'path';
        map[height - 1][x].interactable = 'exit_tempest_plateau_to_frost_peak';
        map[height - 2][x].type = 'path';
        map[height - 3][x].type = 'path';
    }

    // Lightning Trail to North-East Sovereign Arena
    for (let y = 14; y <= height - 3; y++) {
        map[y][14].type = 'darkStone';
    }
    for (let x = 14; x <= 30; x++) {
        map[20][x].type = 'darkStone';
    }
    for (let y = 14; y <= 20; y++) {
        map[y][30].type = 'darkStone';
    }

    // Sovereign Storm Spire Arena (North: x: 20..44, y: 3..14)
    for (let y = 3; y <= 14; y++) {
        for (let x = 20; x <= 44; x++) {
            map[y][x].type = 'runeTile';
        }
    }

    // Conductive Thunder Pillars framing the Arena & Plateau
    [
        { x: 21, y: 4 }, { x: 43, y: 4 },
        { x: 21, y: 13 }, { x: 43, y: 13 },
        { x: 32, y: 4 }, { x: 32, y: 13 },
        { x: 8, y: 16 }, { x: 14, y: 28 }, { x: 6, y: 36 },
        { x: 50, y: 16 }, { x: 54, y: 28 }, { x: 46, y: 38 },
        { x: 26, y: 34 }, { x: 38, y: 34 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'thunderPillar';
    });

    // Thunder Crystal Mining Nodes
    [
        { x: 8, y: 10 }, { x: 12, y: 22 }, { x: 6, y: 30 },
        { x: 52, y: 10 }, { x: 48, y: 22 }, { x: 54, y: 34 },
        { x: 22, y: 28 }, { x: 36, y: 28 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'thunderCrystalNode';
        map[p.y][p.x].interactable = 'thunder_crystal_node';
    });

    // Dungeon Chests
    map[5][23].solid = true; map[5][23].type = 'dungeonChest'; map[5][23].interactable = 'chest_tempest_1';
    map[36][10].solid = true; map[36][10].type = 'dungeonChest'; map[36][10].interactable = 'chest_tempest_2';

    // Breakables
    [
        { x: 18, y: 8, t: 'breakable_pot' },
        { x: 46, y: 8, t: 'breakable_crate' },
        { x: 10, y: 26, t: 'breakable_pot' },
        { x: 50, y: 26, t: 'breakable_crate' },
        { x: 28, y: 22, t: 'breakable_pot' },
        { x: 34, y: 22, t: 'breakable_crate' }
    ].forEach(b => {
        map[b.y][b.x].solid = true;
        map[b.y][b.x].type = b.t;
        map[b.y][b.x].interactable = b.t;
    });

    return { mapWidth: width, mapHeight: height, map };
};


// 1.22 Farm Greenhouse Map (โรงเรือนปลูกพืชทุกฤดู)
Game.generateGreenhouseMap = function() {
    const width = 18;
    const height = 16;
    const map: any[] = [];

    for (let y = 0; y < height; y++) {
        const row: any[] = [];
        for (let x = 0; x < width; x++) {
            const isWall = (y === 0 || y === 1 || x === 0 || x === width - 1 || y === height - 1);
            const isDoor = (x === 8 || x === 9) && y === height - 1;
            row.push({
                x, y,
                type: isWall && !isDoor ? 'wallHouse' : isDoor ? 'doorMat' : 'floorWood',
                solid: isWall && !isDoor,
                interactable: isDoor ? 'exit_greenhouse' : null
            });
        }
        map.push(row);
    }

    // 12x8 fertile tillable plot in center (x: 3..14, y: 3..10)
    for (let y = 3; y <= 10; y++) {
        for (let x = 3; x <= 14; x++) {
            map[y][x].type = 'soil';
            map[y][x].tilled = true;
            map[y][x].watered = false;
            map[y][x].crop = null;
        }
    }

    // Interior Water Basin / Well (x: 15, y: 3)
    map[3][15].solid = true;
    map[3][15].type = 'well';
    map[3][15].interactable = 'well';

    return { mapWidth: width, mapHeight: height, map };

};





// 1.23 Farm Cave Map (ถ้ำในฟาร์ม: เห็ด vs ค้างคาว)
Game.generateFarmCaveMap = function() {
    const width = 16;
    const height = 14;
    const map: any[] = [];

    for (let y = 0; y < height; y++) {
        const row: any[] = [];
        for (let x = 0; x < width; x++) {
            const isBorder = (y === 0 || y === 1 || x === 0 || x === width - 1 || y === height - 1);
            const isDoor = (x === 7 || x === 8) && y === height - 1;
            row.push({
                x, y,
                type: isBorder && !isDoor ? 'darkStone' : isDoor ? 'doorMat' : 'darkStone',
                solid: isBorder && !isDoor,
                interactable: isDoor ? 'exit_farm_cave' : null
            });
        }
        map.push(row);
    }

    // 6 Mushroom Boxes or Fruit Bat Drops
    const choice = this.player?.farmCaveChoice;
    if (choice === 'mushrooms') {
        [{ x: 4, y: 4 }, { x: 7, y: 4 }, { x: 11, y: 4 }, { x: 4, y: 8 }, { x: 7, y: 8 }, { x: 11, y: 8 }].forEach(p => {
            map[p.y][p.x].solid = true;
            map[p.y][p.x].type = 'mushroomBox';
            map[p.y][p.x].interactable = 'farm_mushroom_box';
        });
    } else if (choice === 'bats') {
        [{ x: 4, y: 4 }, { x: 10, y: 4 }, { x: 5, y: 7 }, { x: 9, y: 8 }, { x: 7, y: 5 }].forEach(p => {
            map[p.y][p.x].solid = false;
            map[p.y][p.x].type = 'caveFruitDrop';
            map[p.y][p.x].interactable = 'cave_fruit_drop';
        });
    } else {
        // Pedestal prompt
        map[5][7].solid = true;
        map[5][7].type = 'pillar';
        map[5][7].interactable = 'farm_cave_pedestal';
    }

    return { mapWidth: width, mapHeight: height, map };

};





// 1.24 Tropical Volcano Island Map (เกาะมหาสมบัติเขตร้อน & ชายหาดทะเลแคริบเบียน)
Game.generateIslandMap = function() {
    const width = 46;
    const height = 34;
    const map: any[] = [];

    for (let y = 0; y < height; y++) {
        const row: any[] = [];
        for (let x = 0; x < width; x++) {
            let type = 'sand';
            let solid = false;
            let interactable = null;

            // North: Volcanic mountain ridge (y: 0..6)
            if (y <= 6) {
                type = 'magmaFloor';
                if (y <= 3 || x <= 2 || x >= width - 3) solid = true;
            }
            // South: Turquoise Ocean Water (y: 29..33)
            else if (y >= 29) {
                type = 'water';
                solid = true;
                interactable = 'fishing_spot';
            }
            // East and West water borders
            else if (x <= 1 || x >= width - 2) {
                type = 'water';
                solid = true;
                interactable = 'fishing_spot';
            }

            row.push({ x, y, type, solid, interactable });
        }
        map.push(row);
    }

    // Northern Volcano Cave Mouth (x: 23, y: 4)
    map[4][23].solid = false;
    map[4][23].type = 'magmaLava';
    map[4][23].interactable = 'enter_volcano';

    // Wooden Pier Dock at South (x: 22..24, y: 27..32)
    for (let y = 27; y <= 32; y++) {
        for (let x = 22; x <= 24; x++) {
            map[y][x].solid = false;
            map[y][x].type = 'bridge';
        }
    }
    map[31][23].interactable = 'exit_island_sailboat';
    // Moored Sailboat at South Dock
    map[32][23].solid = true;
    map[32][23].type = 'sailboat';
    map[32][23].interactable = 'exit_island_sailboat';

    // West Beach: Pirate Shipwreck Cove (อ่าวซากเรือโจรสลัดแบล็กฮาวด์)
    map[22][6].solid = true;
    map[22][6].type = 'pirateShipwreck';
    map[22][6].interactable = 'pirate_shipwreck';

    map[24][9].solid = true;
    map[24][9].type = 'pirateChest';
    map[24][9].interactable = 'pirate_chest';

    // East Beach: Captain Barnaby's Pirate Outpost
    map[22][39].solid = true;
    map[22][39].type = 'pirateCaptain';
    map[22][39].interactable = 'npc_pirate_captain';

    // Central Oasis: Freshwater Pond (x: 22..24, y: 12..14)
    for (let py = 12; py <= 14; py++) {
        for (let px = 22; px <= 24; px++) {
            map[py][px].type = 'water';
            map[py][px].solid = true;
            map[py][px].interactable = 'fishing_spot';
        }
    }

    // Central Tropical Farm Plots (แปลงดินเพาะปลูกเขตร้อน 24 ช่อง)
    [
        { x: 17, y: 15 }, { x: 18, y: 15 }, { x: 19, y: 15 }, { x: 20, y: 15 },
        { x: 17, y: 16 }, { x: 18, y: 16 }, { x: 19, y: 16 }, { x: 20, y: 16 },
        { x: 17, y: 17 }, { x: 18, y: 17 }, { x: 19, y: 17 }, { x: 20, y: 17 },
        { x: 26, y: 15 }, { x: 27, y: 15 }, { x: 28, y: 15 }, { x: 29, y: 15 },
        { x: 26, y: 16 }, { x: 27, y: 16 }, { x: 28, y: 16 }, { x: 29, y: 16 },
        { x: 26, y: 17 }, { x: 27, y: 17 }, { x: 28, y: 17 }, { x: 29, y: 17 }
    ].forEach(p => {
        map[p.y][p.x].type = 'soil';
        map[p.y][p.x].isTilled = true;
    });

    // Tropical Palm Trees with coconuts
    [
        { x: 5, y: 14 }, { x: 12, y: 18 }, { x: 34, y: 16 }, { x: 41, y: 16 },
        { x: 8, y: 26 }, { x: 38, y: 26 }, { x: 16, y: 24 }, { x: 30, y: 24 }
    ].forEach(p => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x].type = 'palmTree';
        map[p.y][p.x].interactable = 'palm_tree';
    });

    // Wild Tropical Forageables (Pineapples, Bananas, Coconuts)
    [{ x: 15, y: 12 }, { x: 31, y: 13 }].forEach(p => {
        map[p.y][p.x].type = 'forage_pineapple';
        map[p.y][p.x].interactable = 'forage_pineapple';
    });
    [{ x: 14, y: 19 }, { x: 32, y: 19 }].forEach(p => {
        map[p.y][p.x].type = 'forage_banana';
        map[p.y][p.x].interactable = 'forage_banana';
    });
    [{ x: 10, y: 23 }, { x: 36, y: 23 }].forEach(p => {
        map[p.y][p.x].type = 'forage_coconut';
        map[p.y][p.x].interactable = 'forage_coconut';
    });

    // Seashells & Message Bottles along the beaches
    [
        { x: 13, y: 27 }, { x: 18, y: 28 }, { x: 28, y: 28 }, { x: 34, y: 27 }, { x: 4, y: 25 }
    ].forEach(p => {
        map[p.y][p.x].type = 'seashell';
        map[p.y][p.x].interactable = 'forage_seashell';
    });
    map[28][15].type = 'messageBottle';
    map[28][15].interactable = 'forage_bottle';

    return { mapWidth: width, mapHeight: height, map };
};






// 1.2 House Interior Map (ภายในบ้าน)
Game.generateHouseMap = function() {
    const width = 25;
    const height = 18;
    const map = [];

    for (let y = 0; y < height; y++) {
        const row = [];
        for (let x = 0; x < width; x++) {
            let isWall = (y <= 2 || x <= 1 || x >= width - 2 || y >= height - 2);
            let isDoor = (x >= 11 && x <= 13 && y >= height - 2);
            row.push({
                x: x, y: y,
                type: (y <= 2 ? 'wallHouse' : isDoor ? 'doorMat' : 'floorWood'),
                solid: (isWall && !isDoor),
                interactable: isDoor ? 'exit_house' : null
            });
        }
        map.push(row);
    }

    // Interactive furniture zones in house:
    // Bed at (19..21, 3..4)
    for (let by = 3; by <= 4; by++) {
        for (let bx = 19; bx <= 21; bx++) {
            map[by][bx].solid = true;
            map[by][bx].interactable = 'bed';
        }
    }

    // Wardrobe (ตู้เสื้อผ้า) at (3..4, 3..4)
    for (let wy = 3; wy <= 4; wy++) {
        for (let wx = 3; wx <= 4; wx++) {
            map[wy][wx].solid = true;
            map[wy][wx].interactable = 'wardrobe';
        }
    }

    // House Decor Desk (โต๊ะตกแต่ง/อัพเกรดบ้าน) at (8..9, 3..4)
    for (let dy = 3; dy <= 4; dy++) {
        for (let dx = 8; dx <= 9; dx++) {
            map[dy][dx].solid = true;
            map[dy][dx].interactable = 'house_decor';
        }
    }

    // Modern Fridge at (6, 3)
    map[3][6].solid = true;

    // Stone Fireplace at (13..15, 2..3)
    map[2][13].solid = true; map[2][14].solid = true; map[2][15].solid = true;
    map[3][13].solid = true; map[3][14].solid = true; map[3][15].solid = true;

    return { mapWidth: width, mapHeight: height, map: map };

};



// 1.3 Shop Interior Map (ภายในร้านค้า)
Game.generateShopMap = function() {
    const width = 25;
    const height = 18;
    const map = [];

    for (let y = 0; y < height; y++) {
        const row = [];
        for (let x = 0; x < width; x++) {
            let isWall = (y <= 2 || x <= 1 || x >= width - 2 || y >= height - 2);
            let isDoor = (x >= 11 && x <= 13 && y >= height - 2);
            row.push({
                x: x, y: y,
                type: (y <= 2 ? 'wallShop' : isDoor ? 'doorMat' : 'floorShop'),
                solid: (isWall && !isDoor),
                interactable: isDoor ? 'exit_shop' : null
            });
        }
        map.push(row);
    }

    // Checkout Counter at (4..6, 4)
    for (let cx = 4; cx <= 6; cx++) {
        map[4][cx].solid = true;
        map[4][cx].interactable = 'cash_register';
    }

    // Display Shelves at (6, 7), (10, 7), (14, 7), (18, 7)
    const shelfPos = [{x: 6, y: 7}, {x: 10, y: 7}, {x: 14, y: 7}, {x: 18, y: 7}];
    shelfPos.forEach((p, idx) => {
        map[p.y][p.x].solid = true;
        map[p.y][p.x + 1].solid = true;
        map[p.y][p.x].interactable = 'shelf_' + idx;
        map[p.y][p.x + 1].interactable = 'shelf_' + idx;
    });

    return { mapWidth: width, mapHeight: height, map: map };

};



// 1.31 Mayor's Manor Interior Map (คฤหาสน์ว่าการหมู่บ้าน)
Game.generateManorMap = function() {
    const width = 25;
    const height = 18;
    const map: any[][] = [];

    for (let y = 0; y < height; y++) {
        const row = [];
        for (let x = 0; x < width; x++) {
            let isWall = (y <= 2 || x <= 1 || x >= width - 2 || y >= height - 2);
            let isDoor = (x >= 11 && x <= 13 && y >= height - 2);
            row.push({
                x: x, y: y,
                type: (y <= 2 ? 'wallManor' : isDoor ? 'doorMat' : 'floorCarpet'),
                solid: (isWall && !isDoor),
                interactable: isDoor ? 'exit_manor' : null
            });
        }
        map.push(row);
    }

    // Mayor's Council Desk at (11..13, 3..4)
    for (let dy = 3; dy <= 4; dy++) {
        for (let dx = 11; dx <= 13; dx++) {
            map[dy][dx].solid = true;
            map[dy][dx].interactable = 'mayor_desk';
        }
    }

    // Village Archives Bookcases at (4..6, 3)
    for (let bx = 4; bx <= 6; bx++) {
        map[3][bx].solid = true;
        map[3][bx].interactable = 'village_archives';
    }

    // Grand Manor Fireplace at (19..20, 2..3)
    map[2][19].solid = true; map[2][20].solid = true;
    map[3][19].solid = true; map[3][20].solid = true;

    // Meeting Table & Chairs in Center (10..14, 8..9)
    for (let my = 8; my <= 9; my++) {
        for (let mx = 10; mx <= 14; mx++) {
            map[my][mx].solid = true;
        }
    }

    return { mapWidth: width, mapHeight: height, map: map };

};



// 1.32 Apothecary & Herb Clinic Interior Map (ร้านโอสถและคลินิกสมุนไพร ลิเลียน)
Game.generateApothecaryMap = function() {
    const width = 25;
    const height = 18;
    const map: any[][] = [];

    for (let y = 0; y < height; y++) {
        const row = [];
        for (let x = 0; x < width; x++) {
            let isWall = (y <= 2 || x <= 1 || x >= width - 2 || y >= height - 2);
            let isDoor = (x >= 11 && x <= 13 && y >= height - 2);
            row.push({
                x: x, y: y,
                type: (y <= 2 ? 'wallShop' : isDoor ? 'doorMat' : 'floorWood'),
                solid: (isWall && !isDoor),
                interactable: isDoor ? 'exit_apothecary' : null
            });
        }
        map.push(row);
    }

    // Alchemy Cauldron Station at (6..7, 3..4)
    for (let cy = 3; cy <= 4; cy++) {
        for (let cx = 6; cx <= 7; cx++) {
            map[cy][cx].solid = true;
            map[cy][cx].interactable = 'apothecary_cauldron';
        }
    }

    // Herb Shelves & Potion Display at (17..19, 3..4)
    for (let hy = 3; hy <= 4; hy++) {
        for (let hx = 17; hx <= 19; hx++) {
            map[hy][hx].solid = true;
            map[hy][hx].interactable = 'herb_shelf';
        }
    }

    // Clinic Recuperation Bed at (4..5, 9..10)
    for (let by = 9; by <= 10; by++) {
        for (let bx = 4; bx <= 5; bx++) {
            map[by][bx].solid = true;
            map[by][bx].interactable = 'clinic_bed';
        }
    }

    return { mapWidth: width, mapHeight: height, map: map };

};



// 1.33 The Golden Sheaf Tavern Interior Map (โรงเตี๊ยมรวงทอง บ็อบ)
Game.generateTavernMap = function() {
    const width = 25;
    const height = 18;
    const map: any[][] = [];

    for (let y = 0; y < height; y++) {
        const row = [];
        for (let x = 0; x < width; x++) {
            let isWall = (y <= 2 || x <= 1 || x >= width - 2 || y >= height - 2);
            let isDoor = (x >= 11 && x <= 13 && y >= height - 2);
            row.push({
                x: x, y: y,
                type: (y <= 2 ? 'wallHouse' : isDoor ? 'doorMat' : 'floorWood'),
                solid: (isWall && !isDoor),
                interactable: isDoor ? 'exit_tavern' : null
            });
        }
        map.push(row);
    }

    // Long Tavern Bar Counter at (5..9, 4)
    for (let cx = 5; cx <= 9; cx++) {
        map[4][cx].solid = true;
        map[4][cx].interactable = 'tavern_counter';
    }

    // Beer Casks / Barrels at (3..4, 3)
    map[3][3].solid = true; map[3][4].solid = true;

    // Tavern Bounty Board on Wall at (10..11, 2)
    map[2][10].solid = true; map[2][10].interactable = 'tavern_bounty_board';
    map[2][11].solid = true; map[2][11].interactable = 'tavern_bounty_board';

    // Fireplace at (13..15, 2..3)
    map[2][13].solid = true; map[2][14].solid = true; map[2][15].solid = true;
    map[3][13].solid = true; map[3][14].solid = true; map[3][15].solid = true;

    // Dining Tables with Stools at (5..6, 8..9), (17..18, 8..9), (17..18, 12..13)
    const tablePositions = [{x: 5, y: 8}, {x: 17, y: 8}, {x: 17, y: 12}];
    tablePositions.forEach(p => {
        for (let ty = p.y; ty <= p.y + 1; ty++) {
            for (let tx = p.x; tx <= p.x + 1; tx++) {
                map[ty][tx].solid = true;
            }
        }
    });

    // Minstrel Stage with Lute at (19..21, 3..4)
    for (let sy = 3; sy <= 4; sy++) {
        for (let sx = 19; sx <= 21; sx++) {
            map[sy][sx].solid = true;
        }
    }

    return { mapWidth: width, mapHeight: height, map: map };

};



// 1.34 Sunvale Blacksmith Forge Interior Map (โรงตีเหล็กศิลา คาเอล)
Game.generateForgeMap = function() {
    const width = 25;
    const height = 18;
    const map: any[][] = [];

    for (let y = 0; y < height; y++) {
        const row = [];
        for (let x = 0; x < width; x++) {
            let isWall = (y <= 2 || x <= 1 || x >= width - 2 || y >= height - 2);
            let isDoor = (x >= 11 && x <= 13 && y >= height - 2);
            row.push({
                x: x, y: y,
                type: (y <= 2 ? 'wallForge' : isDoor ? 'doorMat' : 'darkStone'),
                solid: (isWall && !isDoor),
                interactable: isDoor ? 'exit_forge' : null
            });
        }
        map.push(row);
    }

    // Great Master Furnace at (11..13, 2..4)
    for (let fy = 2; fy <= 4; fy++) {
        for (let fx = 11; fx <= 13; fx++) {
            map[fy][fx].solid = true;
        }
    }

    // Master Anvil at (12, 7)
    map[7][12].solid = true;
    map[7][12].interactable = 'master_anvil';

    // Armor Mannequins & Weapon Racks at (4..6, 3) and (18..20, 3)
    for (let wx = 4; wx <= 6; wx++) map[3][wx].solid = true;
    for (let ax = 18; ax <= 20; ax++) map[3][ax].solid = true;

    // Ore and Coal Bins at (3..4, 9..10)
    for (let by = 9; by <= 10; by++) {
        for (let bx = 3; bx <= 4; bx++) {
            map[by][bx].solid = true;
        }
    }

    return { mapWidth: width, mapHeight: height, map: map };

};



Game.spawnAnimals = function() {
    this.animals = [
        { id: 'cow1', type: 'cow', name: 'แม่วัวโมโม่', x: 24 * 32, y: 8 * 32, width: 36, height: 28, vx: 0, vy: 0, frame: 0, timer: 0, pettedToday: false, hasProduct: true, product: 'milk' },
        { id: 'chicken1', type: 'chicken', name: 'เจ้ากุ๊กไก่', x: 26 * 32, y: 9 * 32, width: 22, height: 20, vx: 0, vy: 0, frame: 0, timer: 0, pettedToday: false, hasProduct: true, product: 'egg' },
        { id: 'chicken2', type: 'chicken', name: 'เจ้าไข่ดาว', x: 28 * 32, y: 7 * 32, width: 22, height: 20, vx: 0, vy: 0, frame: 0, timer: 0, pettedToday: false, hasProduct: true, product: 'egg' },
        { id: 'sheep1', type: 'sheep', name: 'น้องปุยฝ้าย', x: 29 * 32, y: 10 * 32, width: 32, height: 26, vx: 0, vy: 0, frame: 0, timer: 0, pettedToday: false, hasProduct: true, product: 'wool' },
        { id: 'pig1', type: 'pig', name: 'เจ้าหมูอ้วน', x: 23 * 32, y: 11 * 32, width: 32, height: 24, vx: 0, vy: 0, frame: 0, timer: 0, pettedToday: false, hasProduct: true, product: 'truffle' }
    ];
};


// ========================================================
// 2. SCENE TRANSITION & SCREEN JUICE SYSTEM
// ========================================================

Game.triggerScreenShake = function(intensity = 5, duration = 140) {
    this.shakeIntensity = intensity;
    this.shakeDuration = duration;
    this.shakeTimer = duration;
};


Game.triggerHitstop = function(ms = 45) {
    this.hitstopTimer = Math.min(80, Math.max(this.hitstopTimer || 0, ms));
};


Game.switchScene = function(targetScene, targetTileX, targetTileY) {
    if (this.isTransitioning) return;
    this.isTransitioning = true;

    const sceneTitles: Record<string, { title: string; subtitle: string; sound: () => void }> = {
        farm: { title: 'ไร่สุขใจ (Happy Farm)', subtitle: 'ผืนแผ่นดินกสิกรรมอันสงบสุข', sound: () => SoundEngine.door() },
        village: { title: 'หมู่บ้านศิลาสุขาวดี (Sunvale Village)', subtitle: 'ศูนย์กลางชุมชนและแนวร่วมต้านโรคระบาด', sound: () => SoundEngine.bell() },
        forest: { title: 'ผืนป่าเอลเดอร์วู้ด & วิหารจอมอสูร', subtitle: 'แดนพงไพรลี้ลับและรังอสูรสปอร์กลายพันธุ์', sound: () => SoundEngine.door() },
        cave: { title: 'ถ้ำผลึกใต้พิภพ (Crystal Caverns)', subtitle: 'แหล่งแร่ทองคำและรังไหมปีศาจ', sound: () => SoundEngine.miningHit() },
        house: { title: 'บ้านพักชาวสวน', subtitle: 'จุดพักผ่อนฟื้นฟูกำลัง', sound: () => SoundEngine.door() },
        shop: { title: 'ร้านค้าการเกษตรและเมล็ดพันธุ์', subtitle: 'แลกเปลี่ยนผลผลิตและเครื่องมือ', sound: () => SoundEngine.bell() },
        manor: { title: 'คฤหาสน์ว่าการหมู่บ้าน', subtitle: 'ศูนย์บัญชาการนายกเทศมนตรีกิลเบิร์ต', sound: () => SoundEngine.door() },
        apothecary: { title: 'คลินิกโอสถสมุนไพร ลิเลียน', subtitle: 'สกัดยารักษาและเซรุ่มต้านสปอร์', sound: () => SoundEngine.bell() },
        tavern: { title: 'โรงเตี๊ยมรวงทอง บ็อบ', subtitle: 'จุดพักผ่อน รับประทานอาหารและสืบข่าวลือ', sound: () => SoundEngine.door() },
        forge: { title: 'โรงตีเหล็กศิลา คาเอล', subtitle: 'ตีดาบ ชุดเกราะ และหลอมแร่มีค่า', sound: () => SoundEngine.miningHit() },
        cave_depths: { title: 'หุบเหวผลึกคริสตัลโบราณ (Crystal Cavern Abyss)', subtitle: 'แดนลี้ลับใต้พิภพ & รังโกเลมลูมินาร์ค', sound: () => SoundEngine.bossLaser() },
        swamp: { title: 'บึงอสรพิษเงามืด (Gloom Swamp)', subtitle: 'หนองน้ำพิษอันตราย & รังพญาไฮดราไตรเศียร', sound: () => SoundEngine.bossPoisonSpit() },
        volcano: { title: 'ปล่องภูเขาไฟอัคนีโลกันตร์ (Ignis Magma Caldera)', subtitle: 'ดินแดนธารลาวาเดือด & รังมังกรเพลิงอิกนิสทรอน', sound: () => SoundEngine.bossDragonBreath() },
        frost_peak: { title: 'ยอดเขาเหมันต์นิรันดร์ (Frostpeak Glacial Sanctuary)', subtitle: 'ดินแดนหิมะเยือกแข็ง & รังจอมอสูรไททันน้ำแข็ง', sound: () => SoundEngine.bossIceShatter() },
        crypt: { title: 'สุสานโบราณกษัตริย์ไร้นาม (Ancient Catacombs & Crypt)', subtitle: 'โถงสุสานต้องสาป & รังลอร์ดมรณะมาลาคอร์', sound: () => SoundEngine.bossSoulScream() },
        ancient_canopy: { title: 'ป่าพฤกษาศักดิ์สิทธิ์โบราณ (Ancient Sacred Canopy)', subtitle: 'พงไพรลี้ลับพันปี & แท่นบูชาเทพพฤกษา ซิลวาเนีย', sound: () => SoundEngine.bossNatureBloom() },
        tempest_plateau: { title: 'ที่ราบสูงอัสนีบาต (Tempest Lightning Plateau)', subtitle: 'ยอดผาวายุคลั่ง & บัลลังก์จ้าวพายุสายฟ้า ออสทริออน', sound: () => SoundEngine.bossLightningStrike() },
        island: { title: 'เกาะภูเขาไฟเขตร้อน (Tropical Island)', subtitle: 'หาดทรายขาว ป่ามะพร้าว และปากปล่องภูเขาไฟ', sound: () => SoundEngine.door() },
        farmCave: { title: 'ถ้ำใต้ฟาร์ม (Farm Cave)', subtitle: 'แหล่งเพาะเห็ดและผลไม้อบอุ่น', sound: () => SoundEngine.miningHit() },
        greenhouse: { title: 'เรือนกระจกเกษตร (Greenhouse)', subtitle: 'ปลูกพืชผลได้ทุกฤดูกาลตลอดทั้งปี', sound: () => SoundEngine.door() },
        spire: { title: 'หอคอยผลึกมิติไร้สิ้นสุด (Infinite Crystal Spire)', subtitle: 'ท้าทายศัตรูไร้ขอบเขต & สะสมเศษเสี้ยวหอคอย', sound: () => SoundEngine.spirePortal() },
        island_volcano: { title: 'ดันเจี้ยนภูเขาไฟเกาะสมบัติ (Volcano Dungeon)', subtitle: 'สำรวจ 10 ชั้น ลาวาเดือด & แท่นหลอมมังกรโบราณ', sound: () => SoundEngine.bossDragonBreath() },
        pvp_arena: { title: 'ลานประลองยุทธ์จอมราชันย์ (PvP Colosseum Arena)', subtitle: 'สนามประลองฝีมือ 1v1 & ตะลุมบอนออนไลน์ ปลอดภัยไร้การสูญเสีย', sound: () => SoundEngine.alarm() }
    };


    const info = sceneTitles[targetScene] || { title: targetScene, subtitle: '', sound: () => SoundEngine.door() };


    this.screenFade = {
        alpha: 0,
        phase: 'fade_out',
        title: info.title,
        subtitle: info.subtitle,
        targetScene,
        targetTileX,
        targetTileY,
        sound: info.sound
    };

    SoundEngine.warpSound();
};


Game.updateTransition = function(dt) {
    if (!this.screenFade || this.screenFade.phase === 'none') return;

    if (this.screenFade.phase === 'fade_out') {
        this.screenFade.alpha += dt / 180;
        if (this.screenFade.alpha >= 1) {
            this.screenFade.alpha = 1;
            const sf = this.screenFade;
            this.loadScene(sf.targetScene);
            this.player.x = sf.targetTileX * this.tileSize;
            this.player.y = sf.targetTileY * this.tileSize;

            // Safety clamp to scene bounds
            const mapPixelW = this.mapWidth * this.tileSize;
            const mapPixelH = this.mapHeight * this.tileSize;
            if (this.player.x < 32 || this.player.x >= mapPixelW - 32) {
                this.player.x = Math.max(48, Math.min(this.player.x, mapPixelW - 48));
            }
            if (this.player.y < 32 || this.player.y >= mapPixelH - 32) {
                this.player.y = Math.max(48, Math.min(this.player.y, mapPixelH - 48));
            }
            this.player.warpCooldown = 1500;

            // Anti-Stuck Fail-Safe: If target tile or player hitbox intersects a solid tile, shift to nearest walkable tile!
            if (this.checkTileCollision(this.player.x, this.player.y)) {
                const offsets = [
                    [0, 1], [-1, 0], [0, 2], [-1, 1], [1, 0], [0, -1], [1, 1], [-1, -1],
                    [0, 3], [-2, 0], [2, 0], [0, -2]
                ];
                for (const [ox, oy] of offsets) {
                    const testX = (sf.targetTileX + ox) * this.tileSize;
                    const testY = (sf.targetTileY + oy) * this.tileSize;
                    if (!this.checkTileCollision(testX, testY)) {
                        this.player.x = testX;
                        this.player.y = testY;
                        break;
                    }
                }
            }

            const maxX = Math.max(0, mapPixelW - this.width);
            const maxY = Math.max(0, mapPixelH - this.height);
            this.camera.x = mapPixelW < this.width 
                ? -Math.round((this.width - mapPixelW) / 2) 
                : Math.max(0, Math.min(this.player.x - this.width / 2 + 12, maxX));
            this.camera.y = mapPixelH < this.height 
                ? -Math.round((this.height - mapPixelH) / 2) 
                : Math.max(0, Math.min(this.player.y - this.height / 2 + 16, maxY));

            SoundEngine.setSceneTheme(sf.targetScene);
            if (typeof SoundEngine.setBossBattle === 'function') SoundEngine.setBossBattle(false);
            if (sf.sound) sf.sound();

            if (sf.targetScene === 'forest') this.initForestScene();
            else if (sf.targetScene === 'cave') this.initCaveScene();
            else if (sf.targetScene === 'cave_depths') this.initCaveDepthsScene();
            else if (sf.targetScene === 'swamp') this.initSwampScene();
            else if (sf.targetScene === 'volcano') this.initVolcanoScene();
            else if (sf.targetScene === 'frost_peak') this.initFrostpeakScene();
            else if (sf.targetScene === 'crypt') this.initCryptScene();
            else if (sf.targetScene === 'ancient_canopy') this.initAncientCanopyScene();
            else if (sf.targetScene === 'tempest_plateau') this.initTempestPlateauScene();
            else if (sf.targetScene === 'spire') { /* keep spire monsters in this.worldMonsters */ }
            else if (sf.targetScene === 'island_volcano') { /* keep volcano monsters & boss in this.worldMonsters */ }
            else if (sf.targetScene === 'island') this.initIslandScene();
            else if (sf.targetScene === 'pvp_arena') this.initPvPArenaScene();
            else {
                // Non-combat zones: clean up any leftover monsters or bosses
                this.worldMonsters = [];
                this.boss = null;
                this.bossTelegraphs = [];
                this.bossGroundHazards = [];
                this.bossDashGhosts = [];
                this.bossShockwaves = [];
                if (this.projectiles) this.projectiles = this.projectiles.filter(p => !p.fromBoss);
                const bossBar = document.getElementById('bossHealthBar');
                if (bossBar) bossBar.style.display = 'none';
            }

            this.updateHUD();
            this.screenFade.phase = 'fade_in';
        }
    } else if (this.screenFade.phase === 'fade_in') {
        this.screenFade.alpha -= dt / 240;
        if (this.screenFade.alpha <= 0) {
            this.screenFade.alpha = 0;
            this.screenFade.phase = 'none';
            this.isTransitioning = false;
        }
    }
};


Game.drawTransition = function() {
    if (!this.screenFade || this.screenFade.alpha <= 0) return;

    this.ctx.save();
    this.ctx.fillStyle = `rgba(15, 23, 42, ${Math.min(1, this.screenFade.alpha)})`;
    this.ctx.fillRect(0, 0, this.width, this.height);

    if (this.screenFade.alpha > 0.35) {
        this.ctx.textAlign = 'center';
        this.ctx.fillStyle = '#fde047';
        this.ctx.font = 'bold 22px "Prompt", sans-serif';
        this.ctx.fillText(this.screenFade.title, this.width / 2, this.height / 2 - 8);

        this.ctx.fillStyle = '#94a3b8';
        this.ctx.font = '13px "Prompt", sans-serif';
        this.ctx.fillText(this.screenFade.subtitle, this.width / 2, this.height / 2 + 20);
    }
    this.ctx.restore();
};

Game.isCombatScene = function() {
    return ['farm', 'forest', 'cave', 'cave_depths', 'swamp', 'volcano', 'frost_peak', 'crypt', 'spire', 'ancient_canopy', 'tempest_plateau', 'island', 'island_volcano'].includes(this.currentScene);
};



// ========================================================
// 3. INPUT HANDLING
// ========================================================

Game.setupInputListeners = function() {
    if (this._inputListenersInitialized) return;
    this._inputListenersInitialized = true;

    window.addEventListener('keydown', (e) => {
        // Trigger BGM on first player interaction
        SoundEngine.init();
        if (SoundEngine.isBgmOn()) {
            SoundEngine.startBgm();
        }

        // Quick Save (Ctrl+S or Cmd+S)
        if ((e.ctrlKey || e.metaKey) && (e.code === 'KeyS' || e.key.toLowerCase() === 's')) {
            e.preventDefault();
            if (typeof Auth !== 'undefined' && typeof Auth.saveGame === 'function') {
                Auth.saveGame(null, true);
            }
            return;
        }

        // Dodge Roll / Dash (Shift key or Space during combat/movement)
        if (e.code === 'ShiftLeft' || e.code === 'ShiftRight') {
            e.preventDefault();
            this.playerDash();
            return;
        }

        // Layout-Independent Movement (supports Thai/US keyboards)
        if (e.code === 'KeyW' || e.code === 'ArrowUp') this.keys.up = true;
        if (e.code === 'KeyS' || e.code === 'ArrowDown') this.keys.down = true;
        if (e.code === 'KeyA' || e.code === 'ArrowLeft') this.keys.left = true;
        if (e.code === 'KeyD' || e.code === 'ArrowRight') this.keys.right = true;

        // Active Skills: Dedicated Action Keys Row (Z, X, C, V) under WASD + Fallback (F1 - F4)
        // 1. Action Keys Row (Z, X, C, V) - ALWAYS for Skills!
        if (e.code === 'KeyZ') {
            e.preventDefault();
            this.triggerPlayerSkill(1);
            return;
        }
        if (e.code === 'KeyX') {
            e.preventDefault();
            this.triggerPlayerSkill(2);
            return;
        }
        if (e.code === 'KeyC') {
            e.preventDefault();
            if (e.shiftKey) {
                this.takeFarmSnapshot();
            } else {
                this.triggerPlayerSkill(3);
            }
            return;
        }
        if (e.code === 'KeyV') {
            e.preventDefault();
            this.triggerPlayerSkill(4);
            return;
        }

        // 2. Fallback Function Keys F1 - F4
        if (e.code === 'F1' || e.key === 'F1') {
            e.preventDefault();
            this.triggerPlayerSkill(1);
            return;
        }
        if (e.code === 'F2' || e.key === 'F2') {
            e.preventDefault();
            this.triggerPlayerSkill(2);
            return;
        }
        if (e.code === 'F3' || e.key === 'F3') {
            e.preventDefault();
            this.triggerPlayerSkill(3);
            return;
        }
        if (e.code === 'F4' || e.key === 'F4') {
            e.preventDefault();
            this.triggerPlayerSkill(4);
            return;
        }

        // 3. Number Keys (Hotbar Item Selection 1 - 0) - ALWAYS 100% FOR ITEMS!
        const dNum = e.code.startsWith('Digit') ? parseInt(e.code.replace('Digit', '')) : (e.key >= '1' && e.key <= '9' ? parseInt(e.key) : (e.key === '0' ? 0 : -1));
        if (dNum >= 1 && dNum <= 9) {
            this.selectHotbarSlot(dNum - 1);
        } else if (dNum === 0) {
            this.selectHotbarSlot(9);
        }

        // Action Keys (Layout-Independent)
        if (e.code === 'Space') {
            e.preventDefault();
            //  Fishing Action Handling
            if (this.fishing && this.fishing.active) {
                if (this.fishing.state === 'biting') {
                    this.startFishingMinigame();
                    return;
                } else if (this.fishing.state === 'minigame') {
                    this.fishing.isHoldingPull = true;
                    return;
                } else if (this.fishing.state === 'waiting') {
                    this.cancelFishing('ยกเลิกการตกปลา');
                    return;
                }
            }

            const selItem = this.player.inventory[this.player.selectedSlot];
            if (this.isItemEdible(selItem)) {
                this.consumeItem(selItem, this.player.selectedSlot);
                return;
            }

            if (selItem && selItem.id === 'fishing_rod') {
                const target = this.getTargetTile();
                this.handleFishingAction(target.x, target.y);
                return;
            }

            // Check if facing an interactive tile (sailboat, door, chest, well) BEFORE weapon attack
            const target = this.getTargetTile();
            const facingTile = (this.map && this.map[target.y]) ? this.map[target.y][target.x] : null;
            if (facingTile && facingTile.interactable) {
                this.handleTileInteract(facingTile.interactable, target.x, target.y);
                return;
            }

            if (selItem && (selItem.type === 'weapon' || WEAPONS[selItem.id])) {
                const originX = this.player.x + 12;
                const originY = this.player.y + 14;
                let tx = originX;
                let ty = originY;
                const nearestEnemy = this.findNearestCombatTarget(380);
                if (nearestEnemy) {
                    tx = nearestEnemy.x;
                    ty = nearestEnemy.y;
                    const dx = tx - originX;
                    const dy = ty - originY;
                    if (Math.abs(dx) > Math.abs(dy)) {
                        this.player.direction = dx > 0 ? 'right' : 'left';
                    } else {
                        this.player.direction = dy > 0 ? 'down' : 'up';
                    }
                } else {
                    if (this.player.direction === 'up') ty -= 200;
                    else if (this.player.direction === 'down') ty += 200;
                    else if (this.player.direction === 'left') tx -= 200;
                    else if (this.player.direction === 'right') tx += 200;
                }
                this.playerAttackAt(tx, ty);
            } else {
                this.useCurrentTool();
            }
        } else if (e.code === 'KeyE') {
            this.interact();
        } else if (e.code === 'KeyQ') {
            this.toggleModal('questModal');
        } else if (e.code === 'KeyB') {
            this.toggleModal('bountyBoardModal');
        } else if (e.code === 'KeyI') {
            this.toggleModal('inventory');
        } else if (e.code === 'KeyC') {
            this.takeFarmSnapshot();
        } else if (e.code === 'KeyM') {
            this.toggleWorldMap();
        } else if (e.code === 'KeyH') {
            this.toggleModal('hunterModal');
        } else if (e.code === 'KeyP') {
            this.toggleCompendiumModal();
        } else if (e.code === 'KeyK') {
            const m = document.getElementById('activeSkillModal');
            if (m && m.style.display !== 'none') this.closeSkillTreeModal();
            else this.openSkillTreeModal();
        } else if (e.code === 'KeyO') {
            this.toggleMultiplayerModal();
        } else if (e.code === 'KeyR') {
            this.toggleMount();
        } else if (e.code === 'KeyT') {
            this.openCampModal();
        } else if (e.code === 'KeyF' && !e.repeat) {
            e.preventDefault();
            this.startPlayerGuard();
        } else if (e.code === 'Slash' || e.key === '?') {
            this.toggleModal('controlsModal');
        } else if (e.code === 'Escape' || e.key === 'Escape') {
            if (this.activeModal) {
                this.closeAllModals();
            } else {
                this.toggleModal('gameMenuModal');
            }
        }

    });

    window.addEventListener('keyup', (e) => {
        if (e.code === 'KeyW' || e.code === 'ArrowUp') this.keys.up = false;
        if (e.code === 'KeyS' || e.code === 'ArrowDown') this.keys.down = false;
        if (e.code === 'KeyA' || e.code === 'ArrowLeft') this.keys.left = false;
        if (e.code === 'KeyD' || e.code === 'ArrowRight') this.keys.right = false;

        if (e.code === 'KeyF') {
            this.stopPlayerGuard();
        }

        if (e.code === 'Space') {
            if (this.fishing && this.fishing.active && this.fishing.state === 'minigame') {
                this.fishing.isHoldingPull = false;
            }
        }
    });

    // Right-Click Context Menu Prevention & Guard / Parry Mouse Binding
    this.canvas.addEventListener('contextmenu', (e) => {
        e.preventDefault();
    });

    this.canvas.addEventListener('mousedown', (e) => {
        if (e.button === 2) {
            e.preventDefault();
            this.startPlayerGuard();
        }
    });

    window.addEventListener('mouseup', (e) => {
        if (e.button === 2) {
            this.stopPlayerGuard();
        }
    });

    window.addEventListener('blur', () => {
        if (this.player && this.player.isGuarding) {
            this.stopPlayerGuard();
        }
    });

    this.canvas.addEventListener('click', (e) => {
        if (this.activeModal) return;

        SoundEngine.init();
        if (SoundEngine.isBgmOn()) {
            SoundEngine.startBgm();
        }

        //  If fishing is active, clicking pulls or reacts
        if (this.fishing && this.fishing.active) {
            if (this.fishing.state === 'biting') {
                this.startFishingMinigame();
                return;
            } else if (this.fishing.state === 'waiting') {
                this.cancelFishing('ยกเลิกการตกปลา');
                return;
            }
        }

        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        const worldX = (e.clientX - rect.left) * scaleX + this.camera.x;
        const worldY = (e.clientY - rect.top) * scaleY + this.camera.y;

        const tileX = Math.floor(worldX / this.tileSize);
        const tileY = Math.floor(worldY / this.tileSize);

        // Check if clicking directly on a dropped item on the ground to pick it up!
        const clickedDroppedItem = this.findNearbyDroppedItem(worldX, worldY, 22);
        if (clickedDroppedItem) {
            const distToPlayer = Math.hypot((this.player.x + 12) - clickedDroppedItem.x, (this.player.y + 16) - clickedDroppedItem.y);
            if (distToPlayer <= 90) {
                this.pickupDroppedItem(clickedDroppedItem);
                return;
            } else {
                this.addFloatingText('เดินเข้าไปใกล้อีกนิดเพื่อเก็บ', clickedDroppedItem.x, clickedDroppedItem.y - 12, '#cbd5e1');
                return;
            }
        }

        // 1. Check animal click to pet
        if (this.currentScene === 'farm' && this.animals) {
            const clickedAnimal = this.animals.find(a => {
                return worldX >= a.x && worldX <= a.x + a.width && worldY >= a.y && worldY <= a.y + a.height;
            });
            if (clickedAnimal) {
                this.petAnimal(clickedAnimal);
                return;
            }
        }

        // 2. Check if clicked directly on ripe ready crop (ALWAYS HARVEST instantly!)
        const targetTile = this.map[tileY]?.[tileX];
        const pTileX = Math.floor((this.player.x + 10) / this.tileSize);
        const pTileY = Math.floor((this.player.y + 20) / this.tileSize);
        const distToTile = Math.hypot(pTileX - tileX, pTileY - tileY);

        if (targetTile && targetTile.crop && targetTile.crop.ready && distToTile <= 3.8) {
            this.harvestCrop(tileX, tileY);
            return;
        }

        // 3. Check villager click in village
        if (this.currentScene === 'village' && this.villageVillagers) {
            const clickedVillager = this.villageVillagers.find(v => Math.hypot((v.x + 12) - worldX, (v.y + 16) - worldY) < 24);
            if (clickedVillager) {
                this.talkToVillager(clickedVillager);
                return;
            }
        }

        // 4. Check interactive tile click (sailboat, door, chest, well, bed) BEFORE shooting
        if (targetTile && targetTile.interactable && distToTile <= 3.8) {
            this.handleTileInteract(targetTile.interactable, tileX, tileY);
            return;
        }

        const selItem = this.player.inventory[this.player.selectedSlot];
        const isWeapon = (selItem && (selItem.type === 'weapon' || (typeof WEAPONS !== 'undefined' && WEAPONS[selItem.id])));
        const isToolOrFarmItem = (selItem && (selItem.type === 'tool' || selItem.type === 'seed' || ['hoe', 'water', 'axe', 'pickaxe', 'scythe', 'sickle', 'fishing_rod'].includes(selItem.id)));

        // 3. Check if clicking directly on a hostile enemy
        let targetedEnemy = false;
        let targetAimX = worldX;
        let targetAimY = worldY;

        if (this.boss && this.boss.alive && Math.hypot((this.boss.x + 32) - worldX, (this.boss.y + 32) - worldY) < 110) {
            targetAimX = this.boss.x + (this.boss.width || 64) / 2;
            targetAimY = this.boss.y + (this.boss.height || 64) / 2;
            targetedEnemy = true;
        } else if (this.worldMonsters && this.worldMonsters.length > 0) {
            for (const m of this.worldMonsters) {
                if (!m.alive || (m.hp !== undefined && m.hp <= 0)) continue;
                if (Math.hypot((m.x + 16) - worldX, (m.y + 16) - worldY) < 60) {
                    targetAimX = m.x + (m.width || 32) / 2;
                    targetAimY = m.y + (m.height || 32) / 2;
                    targetedEnemy = true;
                    break;
                }
            }
        } else if (this.currentScene === 'farm' && this.demonBugs) {
            for (const bug of this.demonBugs) {
                if (bug.hp !== undefined && bug.hp <= 0) continue;
                if (Math.hypot((bug.x + 14) - worldX, (bug.y + 14) - worldY) < 50) {
                    targetAimX = bug.x + 14;
                    targetAimY = bug.y + 14;
                    targetedEnemy = true;
                    break;
                }
            }
        }

        // If player clicked directly on an enemy, attack that enemy!
        if (targetedEnemy) {
            if (!isWeapon) {
                this.ensureWeaponEquippedInCombat();
            }
            this.playerAttackAt(targetAimX, targetAimY);
            return;
        }

        // If holding a tool or seeds, or on the farm/greenhouse, prioritize farming/harvesting!
        if (isToolOrFarmItem || this.currentScene === 'farm' || this.currentScene === 'greenhouse') {
            if (isWeapon) {
                // If user deliberately selected a weapon, allow shooting
                this.playerAttackAt(worldX, worldY);
                return;
            }
            // Always harvest/act on tile with tool or empty hand
            this.actOnTile(tileX, tileY);
            return;
        }

        // In combat zones with weapon equipped: attack
        if (isWeapon) {
            this.playerAttackAt(worldX, worldY);
            return;
        }

        // Default: act on tile
        this.actOnTile(tileX, tileY);
    });

    this.canvas.addEventListener('mousemove', (e) => {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        const worldX = (e.clientX - rect.left) * scaleX + this.camera.x;
        const worldY = (e.clientY - rect.top) * scaleY + this.camera.y;

        this.mouseTile.x = Math.floor(worldX / this.tileSize);
        this.mouseTile.y = Math.floor(worldY / this.tileSize);
        this.mouseWorld.x = worldX;
        this.mouseWorld.y = worldY;

        // Dynamic crosshair cursor when weapon is equipped
        const selItem = this.player.inventory[this.player.selectedSlot];
        if (this.isCombatScene() && selItem && (selItem.type === 'weapon' || WEAPONS[selItem.id])) {
            this.canvas.style.cursor = 'crosshair';
        } else {
            this.canvas.style.cursor = 'default';
        }
    });

    window.addEventListener('wheel', (e) => {
        if (this.activeModal) return;
        if (e.deltaY > 0) this.selectHotbarSlot((this.player.selectedSlot + 1) % 10);
        else if (e.deltaY < 0) this.selectHotbarSlot((this.player.selectedSlot + 9) % 10);
    });
};


Game.selectHotbarSlot = function(index) {
    this.player.selectedSlot = index;
    SoundEngine.click();

    // Update cursor
    const selItem = this.player.inventory[this.player.selectedSlot];
    if (this.canvas && this.isCombatScene() && selItem && (selItem.type === 'weapon' || WEAPONS[selItem.id])) {
        this.canvas.style.cursor = 'crosshair';
    } else if (this.canvas) {
        this.canvas.style.cursor = 'default';
    }

    this.updateHUD();
};


// ========================================================
// 4. PLAYER MOVEMENT & COLLISION
// ========================================================

Game.updatePlayer = function(dt) {
    if (this.player.warpCooldown > 0) {
        this.player.warpCooldown -= dt;
    }

    if (this.screenFade && this.screenFade.phase === 'fade_out') {
        this.player.isMoving = false;
        return;
    }

    if (this.activeModal || this.activeDialogue) {
        this.player.isMoving = false;
        return;
    }

    if (this.player.invincibleTimer > 0) {
        this.player.invincibleTimer -= dt;
    }

    if (this.player.buffs && this.player.buffs.timer !== undefined) {
        this.player.buffs.timer -= dt;

        // Health Regeneration Buff (from Sacred Purification Tea)
        if (this.player.buffs.regen) {
            this.player.buffRegenTimer = (this.player.buffRegenTimer || 0) + dt;
            if (this.player.buffRegenTimer >= 1000) {
                this.player.buffRegenTimer = 0;
                if (this.player.hp < (this.player.maxHp || 100)) {
                    this.player.hp = Math.min(this.player.maxHp || 100, this.player.hp + this.player.buffs.regen);
                    this.addFloatingText('+' + this.player.buffs.regen + ' HP', this.player.x, this.player.y - 15, '#4ade80');
                    this.updateHpHUD();
                }
            }
        }

        // Stamina Surge fast regen (from Stamina Surge Pie)
        if (this.player.buffs.staminaSurge) {
            this.player.energy = Math.min(this.player.maxEnergy || 100, (this.player.energy || 0) + (dt * 0.04));
            this.updateEnergyHUD();
        }

        if (this.player.buffs.timer <= 0) {
            this.addFloatingText('★ บัฟหมดเวลาแล้ว', this.player.x - 10, this.player.y - 20, '#cbd5e1');
            this.player.buffs = undefined;
        }
    }

    if (this.playerShootCooldown > 0) {
        this.playerShootCooldown -= dt;
    }

    let dx = 0;
    let dy = 0;

    // Multiplayer: Smoothly interpolate remote players positions
    if (this.remotePlayers) {
        for (const pid in this.remotePlayers) {
            const rp = this.remotePlayers[pid];
            if (!rp) continue;
            if (rp.targetX !== undefined) rp.x += (rp.targetX - rp.x) * 0.35;
            if (rp.targetY !== undefined) rp.y += (rp.targetY - rp.y) * 0.35;
            if (rp.chatTimer && rp.chatTimer > 0) rp.chatTimer -= dt;
        }
    }

    // Smooth 360-degree analog movement for mobile virtual joystick
    if (this.player.joystickMove) {
        dx = this.player.joystickMove.x;
        dy = this.player.joystickMove.y;
    } else {
        if (this.keys.up) { dy -= 1; this.player.direction = 'up'; }
        if (this.keys.down) { dy += 1; this.player.direction = 'down'; }
        if (this.keys.left) { dx -= 1; this.player.direction = 'left'; }
        if (this.keys.right) { dx += 1; this.player.direction = 'right'; }
        if (dx !== 0 && dy !== 0) { dx *= 0.7071; dy *= 0.7071; }
    }

    
    // Dark Souls: Bloodstain Recovery
    if (this.player.bloodstain && this.player.bloodstain.scene === this.currentScene) {
        const bsDist = Math.hypot((this.player.x + 12) - this.player.bloodstain.x, (this.player.y + 14) - this.player.bloodstain.y);
        if (bsDist < 30) {
            SoundEngine.bloodstainReclaim();
            const reclaimed = this.player.bloodstain.gold || 0;
            this.player.gold += reclaimed;
            this.triggerScreenShake(3.0, 150);
            this.spawnParticles(this.player.x + 12, this.player.y + 14, '#fde047', 25);
            this.addFloatingText(`★ กอบกู้เถ้าธุลีวิญญาณสำเร็จ! (+${reclaimed} G)`, this.player.x - 30, this.player.y - 25, '#facc15');
            this.player.bloodstain = null;
            this.updateHUD();
        }
    }
    // Handle Guard Break Stun (Immobilized while posture broken)
    if (this.player.guardBreakTimer && this.player.guardBreakTimer > 0) {
        this.player.guardBreakTimer -= dt;
        dx = 0;
        dy = 0;
        this.player.isGuarding = false;
    }

    this.player.isMoving = (dx !== 0 || dy !== 0);

    // Apply speed bonus if persian rug owned and inside house
    let curSpeed = this.player.speed;
    if (this.currentScene === 'house' && this.player.houseUpgrades.persian_rug) {
        curSpeed *= 1.3;
    }

    // Apply horse mount speed bonus (+65% speed)
    if (this.player.isMounted) {
        curSpeed *= 1.65;
    }

    // Apply Path speed bonus (+15% stone path, +10% wood path)
    const curTileX = Math.floor((this.player.x + 10) / this.tileSize);
    const curTileY = Math.floor((this.player.y + 20) / this.tileSize);
    const standingTile = this.map[curTileY]?.[curTileX];
    if (standingTile?.type === 'stone_path') {
        curSpeed *= 1.15;
    } else if (standingTile?.type === 'wood_path') {
        curSpeed *= 1.10;
    }

    // Apply Sacred Shrine Blessing (+25% permanent speed)
    if (this.player.shrineRestored) {
        curSpeed *= 1.25;
    }

    // Apply Astreon Storm Greaves speed bonus (+30% speed)
    if (this.player.equippedShield === 'astreon_storm_greaves') {
        curSpeed *= 1.30;
    }

    // Apply Hazard Slow Debuff
    if (this.player.slowTimer && this.player.slowTimer > 0) {
        this.player.slowTimer -= dt;
        curSpeed *= 0.55;
    }

    // Update Dash Cooldown
    if (this.player.dashCooldown && this.player.dashCooldown > 0) {
        this.player.dashCooldown -= dt;
    }

    // Handle Active Dodge Roll / Dash (Dark Souls I-Frames)
    if (this.player.isDashing) {
        this.player.dashTimer = (this.player.dashTimer !== undefined ? this.player.dashTimer : 220) - dt;
        curSpeed *= 2.8;
        this.player.invincibleTimer = Math.max(this.player.invincibleTimer || 0, 180);

        // Record ghost after-image
        if (!this.playerDashGhosts) this.playerDashGhosts = [];
        this.playerDashGhosts.push({
            x: this.player.x,
            y: this.player.y,
            alpha: 0.65,
            frame: this.player.frame || 0,
            direction: this.player.direction || 'down'
        });

        if (this.player.dashDir) {
            dx = this.player.dashDir.x;
            dy = this.player.dashDir.y;
            this.player.isMoving = true;
        }

        if (this.player.dashTimer <= 0) {
            this.player.isDashing = false;
        }
    }

    // Handle Active Guard Stance
    if (this.player.isGuarding) {
        this.player.guardTimer = (this.player.guardTimer || 0) + dt;
        curSpeed *= 0.48; // Slower defensive stance movement
    }
    if (this.player.guardBreakTimer && this.player.guardBreakTimer > 0) {
        curSpeed = 0; // Completely stunned during guard break
    }

    // Apply combat food speed buff (+50% speed)
    if (this.player.buffs?.speed) {
        curSpeed *= this.player.buffs.speed;
    }

    // Well-Fed & Hydrated positive buff vs Hunger/Thirst penalties
    const hungerVal = this.player.hunger !== undefined ? this.player.hunger : 100;
    const thirstVal = this.player.thirst !== undefined ? this.player.thirst : 100;

    if (hungerVal >= 75 && thirstVal >= 75) {
        curSpeed *= 1.10; // สมบูรณ์พร้อม: วิ่งเร็วขึ้น +10%
    } else if (hungerVal <= 0 || thirstVal <= 0) {
        curSpeed *= 0.78; // เดินช้าลง 22% เมื่อหิวโซหรือขาดน้ำ
    } else if (hungerVal < 25 || thirstVal < 25) {
        curSpeed *= 0.90; // เดินช้าลง 10% เมื่อความหิวหรือน้ำต่ำกว่า 25%
    }

    // Anti-stuck safety: If player is ever trapped inside a solid obstacle, auto-nudge out to walkable floor
    if (this.checkTileCollision(this.player.x, this.player.y)) {
        const nudgeDirs = [[0, 2], [-2, 0], [2, 0], [0, -2], [0, 4], [-4, 0], [4, 0], [0, -4]];
        for (const [nx, ny] of nudgeDirs) {
            if (!this.checkTileCollision(this.player.x + nx, this.player.y + ny)) {
                this.player.x += nx;
                this.player.y += ny;
                break;
            }
        }
    }

    if (this.player.isMoving) {
        const nextX = this.player.x + dx * curSpeed;
        const nextY = this.player.y + dy * curSpeed;

        if (!this.checkTileCollision(nextX, this.player.y)) {
            this.player.x = nextX;
        } else if (dy === 0) {
            // Horizontal movement blocked: assist corner sliding
            if (!this.checkTileCollision(nextX, this.player.y - 10)) this.player.y -= 2.0;
            else if (!this.checkTileCollision(nextX, this.player.y + 10)) this.player.y += 2.0;
        }

        if (!this.checkTileCollision(this.player.x, nextY)) {
            this.player.y = nextY;
        } else if (dx === 0) {
            // Vertical movement blocked: assist corner sliding
            if (!this.checkTileCollision(this.player.x - 10, nextY)) this.player.x -= 2.0;
            else if (!this.checkTileCollision(this.player.x + 10, nextY)) this.player.x += 2.0;
        }

        this.player.animTimer += dt;
        if (this.player.animTimer > 130) {
            this.player.animTimer = 0;
            this.player.frame = (this.player.frame + 1) % 3;
            if (this.player.frame === 1) SoundEngine.step();
        }

        // Check Door Mat / Scene Exit triggers on footstep
        const pTileX = Math.floor((this.player.x + 10) / this.tileSize);
        const pTileY = Math.floor((this.player.y + 20) / this.tileSize);
        const curTile = this.map[pTileY]?.[pTileX];

        // Check Sailboat Dock collision contact trigger
        if ((!this.player.warpCooldown || this.player.warpCooldown <= 0) && (!this.screenFade || this.screenFade.phase === 'none')) {
            if (this.currentScene === 'village' && pTileX === 51 && pTileY >= 40 && pTileY <= 42) {
                this.player.warpCooldown = 800;
                this.handleTileInteract('sailboat_pier', 51, 41);
                return;
            } else if (this.currentScene === 'island' && pTileX === 23 && pTileY >= 31 && pTileY <= 33) {
                this.player.warpCooldown = 800;
                this.handleTileInteract('exit_island_sailboat', 23, 32);
                return;
            }
        }

        if (curTile && curTile.interactable && (!this.player.warpCooldown || this.player.warpCooldown <= 0) && (!this.screenFade || this.screenFade.phase === 'none')) {
            if (curTile.interactable === 'exit_house') {
                this.switchScene('farm', 5, 6);
                return;
            } else if (curTile.interactable === 'exit_shop') {
                this.switchScene('farm', 28, 20);
                return;
            } else if (curTile.interactable === 'house_door') {
                this.switchScene('house', 12, 15);
                return;
            } else if (curTile.interactable === 'shop_door') {
                this.switchScene('shop', 12, 15);
                return;
            } else if (curTile.interactable === 'enter_manor') {
                this.switchScene('manor', 12, 15);
                return;
            } else if (curTile.interactable === 'exit_manor') {
                this.switchScene('village', 9, 10);
                return;
            } else if (curTile.interactable === 'enter_apothecary') {
                this.switchScene('apothecary', 12, 15);
                return;
            } else if (curTile.interactable === 'exit_apothecary') {
                this.switchScene('village', 47, 10);
                return;
            } else if (curTile.interactable === 'enter_tavern') {
                this.switchScene('tavern', 12, 15);
                return;
            } else if (curTile.interactable === 'exit_tavern') {
                this.switchScene('village', 47, 29);
                return;
            } else if (curTile.interactable === 'enter_forge') {
                this.switchScene('forge', 12, 15);
                return;
            } else if (curTile.interactable === 'exit_forge') {
                this.switchScene('village', 9, 29);
                return;
            } else if (curTile.interactable === 'exit_to_village') {
                if (this.currentScene === 'farm') {
                    this.switchScene('village', 30, 41);
                } else if (this.currentScene === 'forest') {
                    this.switchScene('village', 30, 2);
                } else {
                    this.switchScene('village', 30, 22);
                }
                return;
            } else if (curTile.interactable === 'exit_to_forest') {
                this.switchScene('forest', 24, 38);
                return;
            } else if (curTile.interactable === 'exit_to_farm') {
                this.switchScene('farm', 16, 2);
                return;
            } else if (curTile.interactable === 'exit_cave') {
                this.switchScene('forest', 44, 9);
                return;
            } else if (curTile.interactable === 'cave_entrance') {
                this.switchScene('cave', 21, 30);
                return;
            } else if (curTile.interactable === 'exit_to_swamp') {
                this.switchScene('swamp', 44, 18);
                return;
            } else if (curTile.interactable === 'exit_swamp_to_village') {
                this.switchScene('village', 3, 20);
                return;
            } else if (curTile.interactable === 'exit_to_crypt') {
                this.switchScene('crypt', 4, 18);
                return;
            } else if (curTile.interactable === 'exit_crypt_to_village') {
                this.switchScene('village', 56, 20);
                return;
            } else if (curTile.interactable === 'exit_to_frost_peak') {
                this.switchScene('frost_peak', 24, 34);
                return;
            } else if (curTile.interactable === 'exit_frost_peak_to_forest') {
                this.switchScene('forest', 4, 4);
                return;
            } else if (curTile.interactable === 'exit_to_cave_depths') {
                this.switchScene('cave_depths', 22, 30);
                return;
            } else if (curTile.interactable === 'exit_cave_depths_to_cave') {
                this.switchScene('cave', 21, 30);
                return;
            } else if (curTile.interactable === 'exit_to_volcano') {
                this.switchScene('volcano', 8, 32);
                return;
            } else if (curTile.interactable === 'exit_volcano_to_cave_depths') {
                this.switchScene('cave_depths', 40, 6);
                return;
            } else if (curTile.interactable === 'exit_to_ancient_canopy') {
                this.switchScene('ancient_canopy', 3, 24);
                return;
            } else if (curTile.interactable === 'exit_ancient_canopy_to_forest') {
                this.switchScene('forest', 46, 20);
                return;
            } else if (curTile.interactable === 'exit_to_tempest_plateau') {
                this.switchScene('tempest_plateau', 14, 40);
                return;
            } else if (curTile.interactable === 'exit_tempest_plateau_to_frost_peak') {
                this.switchScene('frost_peak', 42, 3);
                return;
            }
        }
    } else {
        this.player.frame = 0;
        this.player.animTimer = 0;
    }

    // Camera follow (smooth lerp follow, clamped to scene map bounds)
    const mapPixelW = this.mapWidth * this.tileSize;
    const mapPixelH = this.mapHeight * this.tileSize;
    const maxX = Math.max(0, mapPixelW - this.width);
    const maxY = Math.max(0, mapPixelH - this.height);
    const targetCamX = mapPixelW < this.width 
        ? -Math.round((this.width - mapPixelW) / 2) 
        : Math.max(0, Math.min(this.player.x - this.width / 2 + 12, maxX));
    const targetCamY = mapPixelH < this.height 
        ? -Math.round((this.height - mapPixelH) / 2) 
        : Math.max(0, Math.min(this.player.y - this.height / 2 + 16, maxY));
    if (this.camera.x === undefined || isNaN(this.camera.x)) this.camera.x = targetCamX;
    if (this.camera.y === undefined || isNaN(this.camera.y)) this.camera.y = targetCamY;

    // Screen Shake update
    if (this.shakeTimer && this.shakeTimer > 0) {
        this.shakeTimer -= dt;
        const factor = Math.max(0, this.shakeTimer / this.shakeDuration);
        this.shakeOffsetX = (Math.random() - 0.5) * 2 * this.shakeIntensity * factor;
        this.shakeOffsetY = (Math.random() - 0.5) * 2 * this.shakeIntensity * factor;
    } else {
        this.shakeOffsetX = 0;
        this.shakeOffsetY = 0;
    }

    this.camera.x += (targetCamX - this.camera.x) * 0.14 + this.shakeOffsetX;
    this.camera.y += (targetCamY - this.camera.y) * 0.14 + this.shakeOffsetY;
};


Game.checkTileCollision = function(x, y) {
    const hitbox = {
        left: x + 6, right: x + 18,
        top: y + 20, bottom: y + 29
    };


    const minTileX = Math.floor(hitbox.left / this.tileSize);
    const maxTileX = Math.floor(hitbox.right / this.tileSize);
    const minTileY = Math.floor(hitbox.top / this.tileSize);
    const maxTileY = Math.floor(hitbox.bottom / this.tileSize);

    for (let ty = minTileY; ty <= maxTileY; ty++) {
        for (let tx = minTileX; tx <= maxTileX; tx++) {
            if (ty < 0 || ty >= this.mapHeight || tx < 0 || tx >= this.mapWidth) return true;
            if (this.map[ty][tx].solid) return true;
        }
    }
    return false;
};


// ========================================================
// 5. ANIMALS & NPC SHOP CUSTOMERS AI
// ========================================================

Game.updateAnimals = function(dt) {
    if (this.currentScene !== 'farm') return;

    this.animals.forEach(a => {
        a.timer += dt;
        if (a.timer > 2000 + Math.random() * 3000) {
            a.timer = 0;
            if (Math.random() < 0.6) {
                a.vx = (Math.random() - 0.5) * 0.8;
                a.vy = (Math.random() - 0.5) * 0.8;
                a.frame = 1;
            } else {
                a.vx = 0; a.vy = 0; a.frame = 0;
            }
        }

        const nextX = a.x + a.vx;
        const nextY = a.y + a.vy;
        if (nextX >= 22 * 32 && nextX <= 30 * 32) a.x = nextX;
        if (nextY >= 6 * 32 && nextY <= 12 * 32) a.y = nextY;
    });
};


Game.petAnimal = function(animal) {
    const dist = Math.hypot(this.player.x - animal.x, this.player.y - animal.y);
    if (dist > 70) {
        this.addFloatingText('เดินเข้าไปใกล้ๆ ก่อนนะ', animal.x, animal.y, '#fef08a');
        return;
    }

    SoundEngine.pet();
    this.addFloatingText('♥ ' + animal.name + ' อารมณ์ดีมาก!', animal.x + 8, animal.y - 12, '#ec4899');
    animal.pettedToday = true;
    this.stats.animalsPetted++;
    this.spawnParticles(animal.x + animal.width / 2, animal.y + animal.height / 2, '#ec4899', 8);
    this.spawnParticles(animal.x + animal.width / 2, animal.y + animal.height / 2, '#f472b6', 6);

    if (animal.hasProduct) {
        animal.hasProduct = false;
        const animData = ANIMALS[animal.type];
        if (animData) {
            this.addItemToInventory(animData.product, 1, animData.productName);
            this.addXp(animData.xp);
            this.spawnParticles(animal.x + animal.width / 2, animal.y + animal.height / 2, '#facc15', 10);
            this.addFloatingText(' +1 ' + animData.productName + ' (+' + animData.xp + ' XP)', animal.x, animal.y - 28, '#4ade80');
        }
    }
    this.updateHUD();
};


// NPC Shop Customer Simulation
Game.updateShopNPCs = function(dt) {
    if (this.currentScene !== 'shop') return;

    this.npcSpawnTimer += dt;
    // Spawn an NPC customer every 6-9 seconds if fewer than 2 active customers
    if (this.npcSpawnTimer > 7000 && this.shopNPCs.length < 2) {
        this.npcSpawnTimer = 0;
        const randomProf = NPC_CUSTOMERS[Math.floor(Math.random() * NPC_CUSTOMERS.length)];
        const stockedShelves = this.shopShelves.filter(s => s.count > 0);

        if (stockedShelves.length > 0) {
            const targetShelf = stockedShelves[Math.floor(Math.random() * stockedShelves.length)];
            this.shopNPCs.push({
                id: 'npc_' + performance.now(),
                type: randomProf.type,
                name: randomProf.name,
                x: 12 * 32,
                y: 16 * 32,
                targetShelf: targetShelf,
                state: 'to_shelf',
                timer: 0,
                frame: 0,
                direction: 'up'
            });
            SoundEngine.bell();
        }
    }

    // Update active NPCs
    for (let i = this.shopNPCs.length - 1; i >= 0; i--) {
        const npc = this.shopNPCs[i];
        const speed = 1.6;

        if (npc.state === 'to_shelf') {
            const targetX = (npc.targetShelf.x + 0.5) * 32;
            const targetY = (npc.targetShelf.y + 1) * 32;
            const dist = Math.hypot(targetX - npc.x, targetY - npc.y);

            if (dist > 4) {
                if (Math.abs(targetX - npc.x) > 4) {
                    npc.x += Math.sign(targetX - npc.x) * speed;
                    npc.direction = targetX > npc.x ? 'right' : 'left';
                } else {
                    npc.y += Math.sign(targetY - npc.y) * speed;
                    npc.direction = targetY > npc.y ? 'down' : 'up';
                }
                npc.frame = (Math.floor(performance.now() / 200) % 2);
            } else {
                npc.state = 'browsing';
                npc.timer = 0;
                npc.direction = 'up';
                this.addFloatingText(' ' + npc.name + ' กำลังเลือกดูสินค้า...', npc.x, npc.y - 12, '#fef08a');
            }
        } else if (npc.state === 'browsing') {
            npc.timer += dt;
            if (npc.timer > 1600) {
                if (npc.targetShelf.count > 0) {
                    const buyCount = Math.min(npc.targetShelf.count, Math.floor(Math.random() * 2) + 1);
                    npc.targetShelf.count -= buyCount;
                    npc.boughtCount = buyCount;
                    npc.earnedGold = buyCount * npc.targetShelf.price;
                    npc.state = 'to_counter';
                } else {
                    npc.state = 'leaving';
                }
            }
        } else if (npc.state === 'to_counter') {
            const counterX = 6 * 32;
            const counterY = 5 * 32;
            const dist = Math.hypot(counterX - npc.x, counterY - npc.y);

            if (dist > 4) {
                if (Math.abs(counterX - npc.x) > 4) {
                    npc.x += Math.sign(counterX - npc.x) * speed;
                    npc.direction = counterX > npc.x ? 'right' : 'left';
                } else {
                    npc.y += Math.sign(counterY - npc.y) * speed;
                    npc.direction = counterY > npc.y ? 'down' : 'up';
                }
                npc.frame = (Math.floor(performance.now() / 200) % 2);
            } else {
                // Checkout payment! Ka-ching!
                SoundEngine.cashRegister();
                this.player.gold += npc.earnedGold;
                this.addXp(15);
                this.stats.sales += npc.boughtCount;
                this.spawnParticles(counterX, counterY, '#facc15', 16);
                this.addFloatingText(' +' + npc.earnedGold + ' G (Ka-ching!) ' + npc.name + ' อุดหนุนแล้ว!', npc.x, npc.y - 22, '#facc15');
                this.updateHUD();
                npc.state = 'leaving';
            }
        } else if (npc.state === 'leaving') {
            const exitX = 12 * 32;
            const exitY = 16 * 32;
            const dist = Math.hypot(exitX - npc.x, exitY - npc.y);

            if (dist > 4) {
                if (Math.abs(exitX - npc.x) > 4) {
                    npc.x += Math.sign(exitX - npc.x) * speed;
                    npc.direction = exitX > npc.x ? 'right' : 'left';
                } else {
                    npc.y += speed;
                    npc.direction = 'down';
                }
                npc.frame = (Math.floor(performance.now() / 200) % 2);
            } else {
                this.shopNPCs.splice(i, 1);
            }
        }
    }
};


// ========================================================
// 6. FARM ACTIONS & INTERACTIONS
// ========================================================

Game.getTargetTile = function() {
    let tx = Math.floor((this.player.x + 10) / this.tileSize);
    let ty = Math.floor((this.player.y + 20) / this.tileSize);

    if (this.player.direction === 'up') ty -= 1;
    if (this.player.direction === 'down') ty += 1;
    if (this.player.direction === 'left') tx -= 1;
    if (this.player.direction === 'right') tx += 1;

    return { x: tx, y: ty };

};


Game.useCurrentTool = function() {
    const target = this.getTargetTile();
    this.actOnTile(target.x, target.y);
};


// ========================================================
//  CONSUMABLES, FOOD, DRINK & METABOLISM SYSTEM
// ========================================================

Game.isItemEdible = function(item: any) {
    if (!item) return false;
    const id = item.id;
    if (item.type === 'food' || item.type === 'potion' || item.type === 'crop' || item.type === 'fish') return true;
    if (['bread', 'cheese', 'cake', 'cookie', 'pizza', 'grilled_fish', 'spicy_fish_soup', 
         'milk', 'demon_elixir', 'health_potion', 'antidote_serum', 'bacon',
         'farmer_stew', 'vigor_juice', 'herbal_defense_soup',
         'carrot', 'tomato', 'corn', 'strawberry', 'cabbage', 'pumpkin', 'sugarcane',
         'carp', 'tilapia', 'catfish', 'salmon', 'golden_salmon', 'golden_carp', 'ancient_glowfish'].includes(id)) {
        return true;
    }
    if (RECIPES[id] && (RECIPES[id].energyRestore || RECIPES[id].category === 'bakery' || RECIPES[id].category === 'kitchen' || RECIPES[id].category === 'dairy')) return true;
    return false;
};


Game.getItemConsumableStats = function(item: any) {
    if (!item) return null;
    const id = item.id;
    let hpRestore = 0;
    let energyRestore = item.energyRestore || RECIPES[id]?.energyRestore || 20;
    let hungerRestore = 25;
    let thirstRestore = 5;
    let isDrink = false;

    if (id === 'health_potion') {
        hpRestore = 60; energyRestore = 30; hungerRestore = 5; thirstRestore = 35; isDrink = true;
    } else if (id === 'demon_elixir') {
        hpRestore = 40; energyRestore = 85; hungerRestore = 10; thirstRestore = 30; isDrink = true;
    } else if (id === 'antidote_serum') {
        hpRestore = 30; energyRestore = 50; hungerRestore = 5; thirstRestore = 30; isDrink = true;
    } else if (id === 'milk') {
        hpRestore = 10; energyRestore = 25; hungerRestore = 15; thirstRestore = 50; isDrink = true;
    } else if (id === 'spicy_fish_soup') {
        hpRestore = 25; energyRestore = 95; hungerRestore = 45; thirstRestore = 40; isDrink = true;
    } else if (id === 'pizza') {
        hpRestore = 30; energyRestore = 100; hungerRestore = 65; thirstRestore = -5;
    } else if (id === 'cake') {
        hpRestore = 25; energyRestore = 90; hungerRestore = 50; thirstRestore = -5;
    } else if (id === 'grilled_fish') {
        hpRestore = 15; energyRestore = 65; hungerRestore = 45; thirstRestore = 5;
    } else if (id === 'cheese') {
        hpRestore = 10; energyRestore = 50; hungerRestore = 35; thirstRestore = 0;
    } else if (id === 'bread') {
        hpRestore = 5; energyRestore = 40; hungerRestore = 40; thirstRestore = -5;
    } else if (id === 'cookie') {
        hpRestore = 5; energyRestore = 35; hungerRestore = 25; thirstRestore = -5;
    } else if (id === 'bacon') {
        hpRestore = 10; energyRestore = 35; hungerRestore = 35; thirstRestore = -5;
    } else if (id === 'strawberry') {
        hpRestore = 10; energyRestore = 25; hungerRestore = 18; thirstRestore = 25;
    } else if (id === 'tomato') {
        hpRestore = 5; energyRestore = 15; hungerRestore = 15; thirstRestore = 30;
    } else if (id === 'sugarcane') {
        hpRestore = 5; energyRestore = 20; hungerRestore = 10; thirstRestore = 30;
    } else if (id === 'carrot') {
        hpRestore = 5; energyRestore = 15; hungerRestore = 20; thirstRestore = 10;
    } else if (id === 'corn') {
        hpRestore = 8; energyRestore = 20; hungerRestore = 25; thirstRestore = 5;
    } else if (id === 'cabbage') {
        hpRestore = 5; energyRestore = 15; hungerRestore = 22; thirstRestore = 15;
    } else if (id === 'pumpkin') {
        hpRestore = 10; energyRestore = 25; hungerRestore = 30; thirstRestore = 8;
    } else if (id === 'ancient_glowfish') {
        hpRestore = 60; energyRestore = 100; hungerRestore = 60; thirstRestore = 30;
    } else if (id === 'golden_salmon' || id === 'salmon') {
        hpRestore = 20; energyRestore = 40; hungerRestore = 45; thirstRestore = 10;
    } else if (id === 'catfish') {
        hpRestore = 12; energyRestore = 25; hungerRestore = 30; thirstRestore = 5;
    } else if (id === 'tilapia') {
        hpRestore = 8; energyRestore = 18; hungerRestore = 25; thirstRestore = 5;
    } else if (id === 'carp') {
        hpRestore = 5; energyRestore = 15; hungerRestore = 20; thirstRestore = 5;
    } else if (id === 'farmer_stew') {
        hpRestore = 80; energyRestore = 120; hungerRestore = 80; thirstRestore = 20;
    } else if (id === 'vigor_juice') {
        hpRestore = 40; energyRestore = 100; hungerRestore = 20; thirstRestore = 80; isDrink = true;
    } else if (id === 'herbal_defense_soup') {
        hpRestore = 100; energyRestore = 100; hungerRestore = 50; thirstRestore = 50; isDrink = true;
    } else if (id === 'parry_master_broth') {
        hpRestore = 60; energyRestore = 120; hungerRestore = 45; thirstRestore = 45; isDrink = true;
    } else if (id === 'ironhide_dragon_steak') {
        hpRestore = 80; energyRestore = 140; hungerRestore = 85; thirstRestore = 15;
    } else if (id === 'stamina_surge_pie') {
        hpRestore = 50; energyRestore = 110; hungerRestore = 60; thirstRestore = 20;
    } else if (id === 'sacred_purification_tea') {
        hpRestore = 90; energyRestore = 150; hungerRestore = 30; thirstRestore = 80; isDrink = true;
    }

    if (this.player.houseUpgrades && this.player.houseUpgrades.refrigerator) {
        energyRestore = Math.round(energyRestore * 1.5);
        hungerRestore = Math.round(hungerRestore * 1.2);
        if (hpRestore > 0) hpRestore = Math.round(hpRestore * 1.2);
    }

    return { hpRestore, energyRestore, hungerRestore, thirstRestore, isDrink };
};


Game.consumeItem = function(item: any, slotIndex: number) {
    if (!item || !this.isItemEdible(item)) return false;

    const stats = this.getItemConsumableStats(item);
    if (!stats) return false;

    const id = item.id;
    const hasBuff = (id === 'farmer_stew' || id === 'vigor_juice' || id === 'herbal_defense_soup' ||
                     id === 'parry_master_broth' || id === 'ironhide_dragon_steak' || id === 'stamina_surge_pie' || id === 'sacred_purification_tea' ||
                     id === 'titan_elixir' || id === 'swiftfoot_tonic' || id === 'ironbark_brew');

    const maxHp = this.player.maxHp || 100;
    const maxEnergy = this.player.maxEnergy || 100;
    const maxHunger = this.player.maxHunger || 100;
    const maxThirst = this.player.maxThirst || 100;

    const isHpFull = this.player.hp >= maxHp;
    const isEnergyFull = this.player.energy >= maxEnergy;
    const isHungerFull = (this.player.hunger !== undefined ? this.player.hunger : 100) >= maxHunger;
    const isThirstFull = (this.player.thirst !== undefined ? this.player.thirst : 100) >= maxThirst;

    // Check if player really can't eat
    if (!hasBuff && isHpFull && isEnergyFull && isHungerFull && isThirstFull) {
        this.addFloatingText(' ร่างกายสมบูรณ์ อิ่มและสดชื่น 100%!', this.player.x - 20, this.player.y - 15, '#a7f3d0');
        return false;
    }

    const prevHp = this.player.hp;
    const prevE = this.player.energy;
    const prevH = this.player.hunger !== undefined ? this.player.hunger : 100;
    const prevT = this.player.thirst !== undefined ? this.player.thirst : 100;

    this.player.hp = Math.min(maxHp, Math.max(0, this.player.hp + stats.hpRestore));
    this.player.energy = Math.min(maxEnergy, Math.max(0, this.player.energy + stats.energyRestore));
    this.player.hunger = Math.min(maxHunger, Math.max(0, prevH + stats.hungerRestore));
    this.player.thirst = Math.min(maxThirst, Math.max(0, prevT + stats.thirstRestore));

    const dHp = this.player.hp - prevHp;
    const dE = this.player.energy - prevE;
    const dH = Math.round(this.player.hunger - prevH);
    const dT = Math.round(this.player.thirst - prevT);

    // Apply special combat buffs
    if (id === 'farmer_stew') {
        this.player.buffs = { damage: 35, timer: 180000, name: 'พลังใจชาวสวน (Damage +35)' };
        this.addFloatingText(' บัฟ: พลังใจชาวสวน (+35 ดาเมจ 3 นาที)', this.player.x - 30, this.player.y - 35, '#f59e0b');
    } else if (id === 'vigor_juice') {
        this.player.buffs = { speed: 1.5, timer: 180000, name: 'สายลมว่องไว (Speed +50%)' };
        this.addFloatingText(' บัฟ: สายลมว่องไว (+50% วิ่งเร็ว 3 นาที)', this.player.x - 30, this.player.y - 35, '#38bdf8');
    } else if (id === 'herbal_defense_soup') {
        this.player.buffs = { defense: 0.4, timer: 180000, name: 'เกราะพฤกษา (Defense +40%)' };
        this.addFloatingText(' บัฟ: เกราะพฤกษา (ลดดาเมจลง 40% 3 นาที)', this.player.x - 30, this.player.y - 35, '#4ade80');
    } else if (id === 'parry_master_broth') {
        this.player.buffs = Object.assign(this.player.buffs || {}, { parryWindowBonus: 120, timer: 180000, name: 'สมาธิอัศวิน (Parry Window 0.36s)' });
        this.addFloatingText(' บัฟ: สมาธิอัศวิน (Parry Window +120ms 3 นาที)', this.player.x - 40, this.player.y - 35, '#fbbf24');
    } else if (id === 'ironhide_dragon_steak') {
        this.player.buffs = Object.assign(this.player.buffs || {}, { defense: 0.3, guardBreakImmune: true, timer: 180000, name: 'เกราะศิลา (Def +30% & ต้านการ์ดแตก)' });
        this.addFloatingText(' บัฟ: เกราะศิลา (ลดดาเมจ 30% & ต้านการ์ดแตก 1 ครั้ง)', this.player.x - 40, this.player.y - 35, '#d97706');
    } else if (id === 'stamina_surge_pie') {
        this.player.buffs = Object.assign(this.player.buffs || {}, { staminaSurge: true, timer: 180000, name: 'พายวายุคลั่ง (Stamina Regen x3 & Free Dash)' });
        this.addFloatingText(' บัฟ: พายวายุคลั่ง (ฟื้นฟู SP x3 & กลิ้ง Dash ฟรี 3 นาที)', this.player.x - 40, this.player.y - 35, '#38bdf8');
    } else if (id === 'sacred_purification_tea') {
        this.player.buffs = Object.assign(this.player.buffs || {}, { hazardImmune: true, regen: 6, timer: 180000, name: 'ชาเทวะชำระมลทิน (กันไฟ/พิษ & ฮีล +6/s)' });
        this.addFloatingText(' บัฟ: ชาเทวะ (ภูมิคุ้มกันพิษ/ไฟ/ช็อต & ฟื้นฟู +6 HP/s 3 นาที)', this.player.x - 40, this.player.y - 35, '#4ade80');
    } else if (id === 'titan_elixir') {
        this.player.buffs = Object.assign(this.player.buffs || {}, { damage: 45, critBonus: 0.20, timer: 180000, name: 'เทวะสยบศึก (Dmg +45 & Crit +20%)' });
        this.addFloatingText(' บัฟ: เทวะสยบศึก (+45 ดาเมจ & คริ +20% 3 นาที)', this.player.x - 40, this.player.y - 35, '#f59e0b');
    } else if (id === 'swiftfoot_tonic') {
        this.player.buffs = Object.assign(this.player.buffs || {}, { speed: 1.40, staminaSurge: true, timer: 180000, name: 'สายลมคลั่ง (Speed +40% & Free Dash)' });
        this.addFloatingText(' บัฟ: สายลมคลั่ง (+40% วิ่งเร็ว & Dash ฟรี 3 นาที)', this.player.x - 40, this.player.y - 35, '#38bdf8');
    } else if (id === 'ironbark_brew') {
        this.player.buffs = Object.assign(this.player.buffs || {}, { defense: 0.35, guardBreakImmune: true, timer: 180000, name: 'ปราการศิลา (Def +35% & ต้านการ์ดแตก)' });
        this.addFloatingText(' บัฟ: ปราการศิลา (ลดดาเมจ 35% & ต้านการ์ดแตก 3 นาที)', this.player.x - 40, this.player.y - 35, '#10b981');
    }

    // Decrement item stack
    item.count = (item.count || 1) - 1;
    if (item.count <= 0) {
        this.player.inventory[slotIndex] = null;
    }

    
    // Dark Souls: Heal-Punish (Estus Punish)
    if (this.boss && this.boss.alive && this.boss.active && stats.hpRestore > 0) {
        SoundEngine.bossHealPunishRoar();
        this.addFloatingText(`★ ${this.boss.name}: "คิดจะฟื้นพลังต่อหน้าข้า?!"`, this.boss.x - 30, this.boss.y - 30, '#ef4444');
        this.boss.attackCooldown = Math.min(this.boss.attackCooldown, 200);
        const pAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32));
        this.spawnBossTelegraph('dash', this.boss.x + 32, this.boss.y + 32, 280, 420, 35, this.player.x + 12, this.player.y + 14);
    }
SoundEngine.craft();
    this.spawnParticles(this.player.x + 12, this.player.y + 16, stats.isDrink ? '#38bdf8' : '#fb923c', 16);
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#4ade80', 10);

    const verb = stats.isDrink ? 'ดื่ม' : 'รับประทาน';
    const gains: string[] = [];
    if (dH > 0) gains.push(`+${dH} อาหาร`);
    if (dT > 0) gains.push(`+${dT} น้ำ`);
    if (dE > 0) gains.push(`+${dE} พลัง`);
    if (dHp > 0) gains.push(`+${dHp} HP`);

    this.addFloatingText(`${verb} ${item.name} (${gains.join(', ')})`, this.player.x - 25, this.player.y - 20, '#4ade80');
    this.updateHUD();
    return true;
};


Game.actOnTile = function(tx, ty) {
    if (tx < 0 || tx >= this.mapWidth || ty < 0 || ty >= this.mapHeight) return;

    const tile = this.map[ty]?.[tx];
    const playerTileX = Math.floor((this.player.x + 10) / this.tileSize);
    const playerTileY = Math.floor((this.player.y + 20) / this.tileSize);
    const dist = Math.hypot(playerTileX - tx, playerTileY - ty);

    // 1. Check interaction triggers if within reach (doors, bed, well, chests, shop counter, sailboat)
    if (this.currentScene === 'village' && (tx === 51 || Math.abs(tx - 51) <= 1) && (ty >= 40 && ty <= 42) && dist <= 4.2) {
        this.handleTileInteract('sailboat_pier', 51, 41);
        return;
    }
    if (this.currentScene === 'island' && (tx === 23 || Math.abs(tx - 23) <= 1) && (ty >= 31 && ty <= 33) && dist <= 4.2) {
        this.handleTileInteract('exit_island_sailboat', 23, 32);
        return;
    }
    if (tile && tile.interactable && dist <= 3.8) {
        this.handleTileInteract(tile.interactable, tx, ty);
        return;
    }

    // 2. Check ripe crop harvest if within reach (generous 3.8 tiles reach for mobile comfort)
    if (tile && tile.crop && tile.crop.ready && dist <= 3.8) {
        this.harvestCrop(tx, ty);
        return;
    }

    const selectedItem = this.player.inventory[this.player.selectedSlot];

    // 3. Food & Drink consumption (Can be consumed ANYWHERE, no distance error, no 0 energy lockout!)
    if (this.isItemEdible(selectedItem)) {
        this.consumeItem(selectedItem, this.player.selectedSlot);
        return;
    }

    if (dist > 2.5) {
        this.addFloatingText('ไกลเกินไป', tx * 32, ty * 32, '#cbd5e1');
        return;
    }

    if (!selectedItem) {
        if (tile && tile.type === 'tree') {
            this.addFloatingText(' ต้องถือขวาน (Axe) เพื่อตัดต้นไม้!', tx * 32, ty * 32 - 12, '#f87171');
            return;
        }
        this.addFloatingText('เลือกเครื่องมือจากแถบลัด', this.player.x, this.player.y - 10, '#fde047');
        return;
    }

    //  1. Tree Chopping with Axe
    if (tile.type === 'tree') {
        if (selectedItem.id === 'axe') {
            if (this.player.energy <= 0) {
                this.addFloatingText('หมดแรงแล้ว! กินอาหารหรือเข้านอน', this.player.x, this.player.y - 10, '#f87171');
                return;
            }
            if (tx === 0 || tx === this.mapWidth - 1 || ty === 0 || ty === this.mapHeight - 1) {
                this.addFloatingText(' แนวป่าธรรมชาติ ไม่สามารถตัดได้', tx * 32, ty * 32 - 12, '#cbd5e1');
                return;
            }
            let cost = this.player.houseUpgrades.fireplace ? 1 : 2;
            this.player.energy = Math.max(0, this.player.energy - cost);
            this.player.energyRegenDelay = 2000;
            SoundEngine.chopWood();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 20, '#78350f', 8);
            this.spawnParticles(tx * 32 + 16, ty * 32 + 20, '#d4a373', 8);
            tile.treeHp = (tile.treeHp === undefined ? 3 : tile.treeHp) - 1;

            if (tile.treeHp > 0) {
                this.triggerScreenShake(2.5, 90);
                this.addFloatingText(`จามขวาน! (เหลืออีก ${tile.treeHp} ครั้ง)`, tx * 32, ty * 32 - 12, '#fde047');
            } else {
                tile.type = 'tree_stump';
                tile.solid = false;
                tile.treeHp = undefined;
                this.triggerScreenShake(4.5, 160);
                const woodCount = Math.floor(Math.random() * 5) + 8;
                this.spawnDroppedItem('wood', woodCount, tx * 32 + 16, ty * 32 + 16);
                if (Math.random() < 0.35) {
                    this.spawnDroppedItem('sapling', 1, tx * 32 + 16, ty * 32 + 16);
                    this.addFloatingText(`ตัดต้นไม้ล้ม! ท่อนไม้ x${woodCount} + ต้นกล้า`, tx * 32, ty * 32 - 15, '#4ade80');
                } else {
                    this.addFloatingText(`ตัดต้นไม้ล้ม! ท่อนไม้ x${woodCount}`, tx * 32, ty * 32 - 15, '#4ade80');
                }
                this.addXp(15);
            }
            this.updateHUD();
            return;
        } else {
            this.addFloatingText('ต้องถือขวาน (Axe) เพื่อตัดต้นไม้', tx * 32, ty * 32 - 12, '#f87171');
            return;
        }
    }

    // 2. Tree Stump Clearing
    if (tile.type === 'tree_stump') {
        if (selectedItem.id === 'axe') {
            if (this.player.energy <= 0) {
                this.addFloatingText('หมดแรงแล้ว! กินอาหารหรือเข้านอน', this.player.x, this.player.y - 10, '#f87171');
                return;
            }
            let cost = this.player.houseUpgrades.fireplace ? 1 : 2;
            this.player.energy = Math.max(0, this.player.energy - cost);
            this.player.energyRegenDelay = 2000;
            SoundEngine.chopWood();
            this.triggerScreenShake(3.0, 100);
            this.spawnParticles(tx * 32 + 16, ty * 32 + 20, '#78350f', 6);
            tile.type = (this.currentScene === 'forest' ? 'darkGrass' : 'grass');
            this.spawnDroppedItem('wood', 3, tx * 32 + 16, ty * 32 + 16);
            this.addFloatingText('ขุดตอไม้สำเร็จ! ได้รับ ท่อนไม้ x3', tx * 32, ty * 32 - 12, '#4ade80');
            this.updateHUD();
            return;
        } else {
            this.addFloatingText('ใช้ขวานจามตอไม้เพื่อเคลียร์พื้นที่', tx * 32, ty * 32 - 12, '#cbd5e1');
            return;
        }
    }

    // 3. Placing Storage Chest
    if (selectedItem.id === 'chest') {
        const canPlaceChest = (!tile.solid || tile.tilled) && !tile.crop && !tile.interactable && (['grass', 'soil', 'darkGrass', 'floorWood', 'path', 'stone_path', 'wood_path', 'dirt'].includes(tile.type) || tile.tilled);
        if (canPlaceChest) {
            const chestId = 'placed_chest_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
            tile.solid = true;
            tile.tilled = false;
            tile.watered = false;
            tile.type = 'placed_chest';
            tile.interactable = chestId;

            this.placedChests = this.placedChests || {};

            this.placedChests[chestId] = {
                id: chestId,
                scene: this.currentScene,
                x: tx,
                y: ty,
                slots: Array(16).fill(null),
                name: 'กล่องเก็บของไม้'
            };

            this.removeItemFromInventory('chest', 1);
            SoundEngine.craft();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#ca8a04', 12);
            this.addFloatingText('วางกล่องเก็บของสำเร็จ (คลิกเพื่อเปิด)', tx * 32, ty * 32 - 12, '#4ade80');
            this.updateHUD();
            return;
        } else {
            this.addFloatingText('ไม่สามารถวางตรงนี้ได้', tx * 32, ty * 32 - 12, '#f87171');
            return;
        }
    }

    // 4. Planting Tree Sapling
    if (selectedItem.id === 'sapling') {
        const canPlaceSapling = (!tile.solid || tile.tilled) && !tile.crop && !tile.interactable && (['grass', 'soil', 'darkGrass', 'dirt'].includes(tile.type) || tile.tilled);
        if (canPlaceSapling) {
            tile.tilled = false;
            tile.watered = false;
            tile.type = 'sapling';
            this.removeItemFromInventory('sapling', 1);
            SoundEngine.plant();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#22c55e', 8);
            this.addFloatingText('ปลูกต้นกล้าสำเร็จ (จะเติบโตเป็นต้นไม้ใหญ่)', tx * 32, ty * 32 - 12, '#4ade80');
            this.updateHUD();
            return;
        } else {
            this.addFloatingText('ปลูกได้เฉพาะบนพื้นหญ้าหรือดินว่าง', tx * 32, ty * 32 - 12, '#f87171');
            return;
        }
    }

    // 5. Placing Sprinklers (Farm Automation)
    if (selectedItem.id === 'sprinkler_basic' || selectedItem.id === 'sprinkler_quality') {
        const canPlaceSprinkler = (!tile.solid || tile.tilled) && !tile.crop && !tile.interactable && (['grass', 'soil', 'path', 'stone_path', 'wood_path', 'darkGrass', 'floorWood', 'dirt'].includes(tile.type) || tile.tilled || tile.watered);
        if (canPlaceSprinkler) {
            const spId = 'sprinkler_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
            tile.solid = true;
            tile.tilled = false;
            tile.watered = false;
            tile.type = selectedItem.id;
            tile.interactable = spId;

            this.placedSprinklers = this.placedSprinklers || [];
            this.placedSprinklers.push({
                id: spId,
                type: selectedItem.id,
                scene: this.currentScene,
                x: tx,
                y: ty
            });

            this.removeItemFromInventory(selectedItem.id, 1);
            SoundEngine.craft();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#38bdf8', 14);
            const spName = selectedItem.id === 'sprinkler_quality' ? 'สปริงเกอร์คุณภาพสูง (3x3)' : 'สปริงเกอร์พื้นฐาน (4 ทิศ)';
            this.addFloatingText(`วาง ${spName} สำเร็จ! รดน้ำแปลงผักอัตโนมัติทุกเช้า`, tx * 32, ty * 32 - 12, '#38bdf8');
            this.updateHUD();
            return;
        } else {
            this.addFloatingText('ไม่สามารถวางตรงนี้ได้', tx * 32, ty * 32 - 12, '#f87171');
            return;
        }
    }

    // 6. Placing Artisan Machinery (Mayo, Cheese, Jam, Wine)
    if (['mayo_machine', 'cheese_press', 'preserves_jar', 'wine_keg'].includes(selectedItem.id)) {
        const canPlaceMachine = (!tile.solid || tile.tilled) && !tile.crop && !tile.interactable && (['grass', 'soil', 'floorWood', 'path', 'stone_path', 'wood_path', 'darkGrass', 'dirt'].includes(tile.type) || tile.tilled);
        if (canPlaceMachine) {
            const mId = 'machine_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
            tile.solid = true;
            tile.tilled = false;
            tile.watered = false;
            tile.type = selectedItem.id;
            tile.interactable = mId;

            this.placedMachines = this.placedMachines || {};

            this.placedMachines[mId] = {
                id: mId,
                type: selectedItem.id,
                scene: this.currentScene,
                x: tx,
                y: ty,
                state: 'idle',
                inputItem: null,
                readyItem: null,
                readyItemName: '',
                remainingMs: 0,
                totalMs: 0
            };

            this.removeItemFromInventory(selectedItem.id, 1);
            SoundEngine.craft();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#ca8a04', 14);
            this.addFloatingText(`วางเครื่องแปรรูปสำเร็จ (คลิกเพื่อใส่วัตถุดิบ)`, tx * 32, ty * 32 - 12, '#4ade80');
            this.updateHUD();
            return;
        } else {
            this.addFloatingText('ไม่สามารถวางตรงนี้ได้', tx * 32, ty * 32 - 12, '#f87171');
            return;
        }
    }

    // 7. Horse Whistle (Ride mount)
    if (selectedItem.id === 'horse_whistle') {
        this.toggleMount();
        return;
    }

    // 7.1 Island Warp Totem
    if (selectedItem.id === 'island_warp_totem') {
        this.removeItemFromInventory('island_warp_totem', 1);
        SoundEngine.spirePortal();
        this.spawnParticles(this.player.x, this.player.y, '#38bdf8', 25);
        this.addFloatingText('วาร์ปข้ามมิติสู่เกาะเขตร้อน!', this.player.x - 20, this.player.y - 20, '#38bdf8');
        this.travelToIsland();
        return;
    }

    // 7.2 Tropical Delight Drink (Speed boost)
    if (selectedItem.id === 'tropical_delight_drink') {
        this.removeItemFromInventory('tropical_delight_drink', 1);
        this.player.speedBoostTimer = Math.max(this.player.speedBoostTimer || 0, 300000); // 5 mins
        this.player.energy = Math.min(this.player.maxEnergy, this.player.energy + 160);
        this.player.hp = Math.min(this.player.maxHp, this.player.hp + 100);
        SoundEngine.gulp();
        this.spawnParticles(this.player.x, this.player.y, '#38bdf8', 20);
        this.addFloatingText('ดื่มค็อกเทลเขตร้อน! วิ่งเร็วขึ้น +60% นาน 5 นาที!', this.player.x - 40, this.player.y - 25, '#38bdf8');
        this.updateHUD();
        return;
    }

    // 8. Pet Basket (Companion)
    if (selectedItem.id === 'pet_basket') {
        if (!this.player.pet) {
            this.player.pet = { type: 'dog', name: 'บัดดี้ (Buddy)', happiness: 100, x: this.player.x, y: this.player.y, dir: 'down', animTimer: 0, frame: 0 };

            SoundEngine.levelUp();
            this.addFloatingText(' รับเลี้ยงน้องหมาคู่หู บัดดี้ (Buddy) สำเร็จ!', this.player.x, this.player.y - 20, '#f472b6');
        } else {
            const nextType = this.player.pet.type === 'dog' ? 'cat' : 'dog';
            const nextName = nextType === 'dog' ? 'บัดดี้ (Buddy)' : 'ลูน่า (Luna)';
            this.player.pet.type = nextType;
            this.player.pet.name = nextName;
            SoundEngine.levelUp();
            this.addFloatingText(` สลับคู่หูเป็นน้อง${nextType === 'dog' ? 'หมา' : 'แมว'} ${nextName}!`, this.player.x, this.player.y - 20, '#f472b6');
        }
        this.checkAchievements();
        this.updateHUD();
        return;
    }

    // 8.1 Tool Retrieval of Placed Items (Axe / Pickaxe)
    if (selectedItem.id === 'axe' || selectedItem.id === 'pickaxe') {
        // Placed sprinkler retrieval
        if (tile.type === 'sprinkler_basic' || tile.type === 'sprinkler_quality' || (tile.interactable && tile.interactable.startsWith('sprinkler_'))) {
            const spType = tile.type === 'sprinkler_quality' ? 'sprinkler_quality' : 'sprinkler_basic';
            this.placedSprinklers = (this.placedSprinklers || []).filter((sp: any) => !(sp.x === tx && sp.y === ty && sp.scene === this.currentScene));
            tile.type = (this.currentScene === 'farm' ? 'soil' : 'grass');
            tile.solid = false;
            tile.interactable = null;
            this.spawnDroppedItem(spType, 1, tx * 32 + 16, ty * 32 + 16);
            SoundEngine.chopWood();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#38bdf8', 12);
            this.addFloatingText('รื้อถอนสปริงเกอร์สำเร็จ!', tx * 32, ty * 32 - 12, '#38bdf8');
            this.updateHUD();
            return;
        }

        // Placed machine retrieval
        if (['mayo_machine', 'cheese_press', 'preserves_jar', 'wine_keg'].includes(tile.type) || (tile.interactable && tile.interactable.startsWith('machine_'))) {
            const mId = tile.interactable;
            const mType = (this.placedMachines && this.placedMachines[mId]?.type) || tile.type;
            if (this.placedMachines && this.placedMachines[mId]) {
                delete this.placedMachines[mId];
            }
            tile.type = (this.currentScene === 'house' ? 'floorWood' : 'grass');
            tile.solid = false;
            tile.interactable = null;
            this.spawnDroppedItem(mType, 1, tx * 32 + 16, ty * 32 + 16);
            SoundEngine.chopWood();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#ca8a04', 12);
            this.addFloatingText('รื้อถอนเครื่องแปรรูปสำเร็จ!', tx * 32, ty * 32 - 12, '#4ade80');
            this.updateHUD();
            return;
        }

        // Placed chest retrieval (if empty)
        if (tile.type === 'placed_chest' || (tile.interactable && tile.interactable.startsWith('placed_chest_'))) {
            const cId = tile.interactable;
            const chest = this.placedChests && this.placedChests[cId];
            const hasItems = chest && chest.slots && chest.slots.some((s: any) => s !== null);
            if (hasItems) {
                this.addFloatingText('ต้องนำไอเทมออกจากกล่องให้หมดก่อนรื้อถอน!', tx * 32, ty * 32 - 12, '#f87171');
                return;
            }
            if (this.placedChests && this.placedChests[cId]) {
                delete this.placedChests[cId];
            }
            tile.type = (this.currentScene === 'house' ? 'floorWood' : 'grass');
            tile.solid = false;
            tile.interactable = null;
            this.spawnDroppedItem('chest', 1, tx * 32 + 16, ty * 32 + 16);
            SoundEngine.chopWood();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#ca8a04', 12);
            this.addFloatingText('เก็บกล่องเก็บของสำเร็จ!', tx * 32, ty * 32 - 12, '#4ade80');
            this.updateHUD();
            return;
        }

        // Placed decor: fences and paths
        if (tile.type === 'wood_fence' || tile.type === 'stone_fence' || tile.type === 'stone_path' || tile.type === 'wood_path') {
            const decorType = tile.type;
            this.placedDecor = (this.placedDecor || []).filter((d: any) => !(d.x === tx && d.y === ty && d.scene === this.currentScene));
            tile.type = (this.currentScene === 'house' ? 'floorWood' : this.currentScene === 'forest' ? 'darkGrass' : 'grass');
            tile.solid = false;
            tile.decorId = undefined;
            this.spawnDroppedItem(decorType, 1, tx * 32 + 16, ty * 32 + 16);
            SoundEngine.chopWood();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#ca8a04', 8);
            this.addFloatingText('เก็บไอเทมตกแต่งสำเร็จ', tx * 32, ty * 32 - 12, '#4ade80');
            this.updateHUD();
            return;
        }

        // Placed lantern
        if (tile.type === 'farm_lantern') {
            this.placedLanterns = (this.placedLanterns || []).filter((l: any) => !(l.x === tx && l.y === ty && l.scene === this.currentScene));
            tile.type = (this.currentScene === 'house' ? 'floorWood' : this.currentScene === 'forest' ? 'darkGrass' : 'grass');
            tile.solid = false;
            tile.interactable = null;
            tile.lanternId = undefined;
            this.spawnDroppedItem('farm_lantern', 1, tx * 32 + 16, ty * 32 + 16);
            SoundEngine.chopWood();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#fef08a', 10);
            this.addFloatingText('เก็บโคมไฟฟาร์มสำเร็จ', tx * 32, ty * 32 - 12, '#4ade80');
            this.updateHUD();
            return;
        }

        // Placed structure (windmill, silo, fish_tank)
        if (tile.type && tile.type.startsWith('placed_structure_')) {
            const st = (this.placedStructures || []).find((s: any) => s.scene === this.currentScene && tx >= s.x && tx < s.x + (s.width || 1) && ty >= s.y && ty < s.y + (s.height || 1));
            if (st) {
                for (let dy = 0; dy < (st.height || 1); dy++) {
                    for (let dx = 0; dx < (st.width || 1); dx++) {
                        const px = st.x + dx;
                        const py = st.y + dy;
                        if (this.map[py] && this.map[py][px]) {
                            this.map[py][px].type = (this.currentScene === 'house' ? 'floorWood' : 'grass');
                            this.map[py][px].solid = false;
                            this.map[py][px].interactable = null;
                            this.map[py][px].structureId = undefined;
                        }
                    }
                }
                this.placedStructures = this.placedStructures.filter((s: any) => s.id !== st.id);
                const kitItem = st.type === 'windmill' ? 'windmill_kit' : st.type === 'silo' ? 'silo_kit' : 'fish_tank';
                this.spawnDroppedItem(kitItem, 1, tx * 32 + 16, ty * 32 + 16);
                SoundEngine.chopWood();
                this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#f59e0b', 16);
                this.addFloatingText('รื้อถอนสิ่งปลูกสร้างสำเร็จ (ได้รับชุดก่อสร้างคืน)', tx * 32, ty * 32 - 12, '#4ade80');
                this.updateHUD();
                return;
            }
        }
    }

    // 8.2 Placing Fences (Wood & Stone)
    if (selectedItem.id === 'wood_fence' || selectedItem.id === 'stone_fence') {
        if (!tile.solid && !tile.crop && !tile.interactable && (tile.type === 'grass' || tile.type === 'soil' || tile.type === 'darkGrass' || tile.type === 'floorWood' || tile.type === 'path')) {
            tile.solid = true;
            tile.type = selectedItem.id;
            this.placedDecor = this.placedDecor || [];
            this.placedDecor.push({
                id: 'decor_' + Date.now() + '_' + Math.floor(Math.random() * 1000),
                type: selectedItem.id,
                scene: this.currentScene,
                x: tx,
                y: ty
            });
            this.removeItemFromInventory(selectedItem.id, 1);
            SoundEngine.craft();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#78350f', 8);
            this.addFloatingText(selectedItem.id === 'wood_fence' ? 'วางรั้วไม้สำเร็จ' : 'วางรั้วหินสำเร็จ', tx * 32, ty * 32 - 12, '#4ade80');
            this.updateHUD();
            return;
        } else {
            this.addFloatingText('ไม่สามารถวางรั้วตรงนี้ได้', tx * 32, ty * 32 - 12, '#f87171');
            return;
        }
    }

    // 8.3 Placing Paths (Stone & Wood)
    if (selectedItem.id === 'stone_path' || selectedItem.id === 'wood_path') {
        if (!tile.solid && !tile.crop && !tile.interactable && (tile.type === 'grass' || tile.type === 'soil' || tile.type === 'darkGrass' || tile.type === 'path')) {
            tile.type = selectedItem.id;
            this.placedDecor = this.placedDecor || [];
            this.placedDecor.push({
                id: 'path_' + Date.now() + '_' + Math.floor(Math.random() * 1000),
                type: selectedItem.id,
                scene: this.currentScene,
                x: tx,
                y: ty
            });
            this.removeItemFromInventory(selectedItem.id, 1);
            SoundEngine.step();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#cbd5e1', 6);
            const speedBonus = selectedItem.id === 'stone_path' ? '+15%' : '+10%';
            this.addFloatingText(`ปูทางเดินสำเร็จ (ความเร็วเดิน ${speedBonus})`, tx * 32, ty * 32 - 12, '#4ade80');
            this.updateHUD();
            return;
        } else {
            this.addFloatingText('ไม่สามารถปูทางเดินตรงนี้ได้', tx * 32, ty * 32 - 12, '#f87171');
            return;
        }
    }

    // 8.4 Placing Farm Lantern
    if (selectedItem.id === 'farm_lantern') {
        if (!tile.solid && !tile.crop && !tile.interactable && (tile.type === 'grass' || tile.type === 'soil' || tile.type === 'darkGrass' || tile.type === 'floorWood' || tile.type === 'path' || tile.type === 'stone_path' || tile.type === 'wood_path')) {
            const lanId = 'lantern_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
            tile.solid = true;
            tile.type = 'farm_lantern';
            tile.interactable = 'farm_lantern_' + lanId;
            this.placedLanterns = this.placedLanterns || [];
            this.placedLanterns.push({
                id: lanId,
                scene: this.currentScene,
                x: tx,
                y: ty
            });
            this.removeItemFromInventory('farm_lantern', 1);
            SoundEngine.craft();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#fef08a', 12);
            this.addFloatingText('ติดตั้งโคมไฟฟาร์มสำเร็จ! ส่องสว่างยามค่ำคืน', tx * 32, ty * 32 - 12, '#fef08a');
            this.updateHUD();
            return;
        } else {
            this.addFloatingText('ไม่สามารถวางตรงนี้ได้', tx * 32, ty * 32 - 12, '#f87171');
            return;
        }
    }

    // 8.5 Placing Windmill (2x2 Structure on Farm)
    if (selectedItem.id === 'windmill_kit') {
        if (this.currentScene !== 'farm') {
            this.addFloatingText('กังหันลมสร้างได้เฉพาะในฟาร์มเท่านั้น!', this.player.x, this.player.y - 12, '#f87171');
            return;
        }
        let canPlace = true;
        for (let dy = 0; dy < 2; dy++) {
            for (let dx = 0; dx < 2; dx++) {
                const px = tx + dx;
                const py = ty + dy;
                const t = this.map[py]?.[px];
                if (!t || t.solid || t.crop || t.interactable || (t.type !== 'grass' && t.type !== 'soil' && t.type !== 'path')) {
                    canPlace = false;
                }
            }
        }
        if (canPlace) {
            const windId = 'windmill_' + Date.now();
            for (let dy = 0; dy < 2; dy++) {
                for (let dx = 0; dx < 2; dx++) {
                    const px = tx + dx;
                    const py = ty + dy;
                    this.map[py][px].type = 'placed_structure_windmill';
                    this.map[py][px].solid = true;
                    this.map[py][px].structureId = windId;
                    if (dx === 0 && dy === 0) {
                        this.map[py][px].interactable = 'windmill_interact_' + windId;
                    }
                }
            }
            this.placedStructures = this.placedStructures || [];
            this.placedStructures.push({
                id: windId,
                type: 'windmill',
                scene: 'farm',
                x: tx,
                y: ty,
                width: 2,
                height: 2
            });
            this.removeItemFromInventory('windmill_kit', 1);
            SoundEngine.craft();
            this.spawnParticles(tx * 32 + 32, ty * 32 + 32, '#ca8a04', 20);
            this.addFloatingText('ก่อสร้างกังหันลมสำเร็จ! โม่แป้งสาลีและน้ำตาลได้ทันที', tx * 32, ty * 32 - 15, '#4ade80');
            this.updateHUD();
            return;
        } else {
            this.addFloatingText('ต้องมีพื้นที่ว่าง 2x2 ช่องเพื่อสร้างกังหันลม', tx * 32, ty * 32 - 12, '#f87171');
            return;
        }
    }

    // 8.6 Placing Silo (2x2 Structure on Farm)
    if (selectedItem.id === 'silo_kit') {
        if (this.currentScene !== 'farm') {
            this.addFloatingText('ไซโลสร้างได้เฉพาะในฟาร์มเท่านั้น!', this.player.x, this.player.y - 12, '#f87171');
            return;
        }
        let canPlace = true;
        for (let dy = 0; dy < 2; dy++) {
            for (let dx = 0; dx < 2; dx++) {
                const px = tx + dx;
                const py = ty + dy;
                const t = this.map[py]?.[px];
                if (!t || t.solid || t.crop || t.interactable || (t.type !== 'grass' && t.type !== 'soil' && t.type !== 'path')) {
                    canPlace = false;
                }
            }
        }
        if (canPlace) {
            const siloId = 'silo_' + Date.now();
            for (let dy = 0; dy < 2; dy++) {
                for (let dx = 0; dx < 2; dx++) {
                    const px = tx + dx;
                    const py = ty + dy;
                    this.map[py][px].type = 'placed_structure_silo';
                    this.map[py][px].solid = true;
                    this.map[py][px].structureId = siloId;
                    if (dx === 0 && dy === 0) {
                        this.map[py][px].interactable = 'silo_interact_' + siloId;
                    }
                }
            }
            this.placedStructures = this.placedStructures || [];
            this.placedStructures.push({
                id: siloId,
                type: 'silo',
                scene: 'farm',
                x: tx,
                y: ty,
                width: 2,
                height: 2
            });
            this.removeItemFromInventory('silo_kit', 1);
            SoundEngine.craft();
            this.spawnParticles(tx * 32 + 32, ty * 32 + 32, '#ca8a04', 20);
            this.addFloatingText('ก่อสร้างไซโลสำเร็จ! จ่ายอาหารให้สัตว์ทุกเช้าอัตโนมัติ', tx * 32, ty * 32 - 15, '#4ade80');
            this.updateHUD();
            return;
        } else {
            this.addFloatingText('ต้องมีพื้นที่ว่าง 2x2 ช่องเพื่อสร้างไซโล', tx * 32, ty * 32 - 12, '#f87171');
            return;
        }
    }

    // 8.7 Placing Fish Tank (2x1 Structure inside House)
    if (selectedItem.id === 'fish_tank') {
        if (this.currentScene !== 'house') {
            this.addFloatingText('ตู้ปลาวางได้เฉพาะในบ้านเท่านั้น!', this.player.x, this.player.y - 12, '#f87171');
            return;
        }
        const t1 = this.map[ty]?.[tx];
        const t2 = this.map[ty]?.[tx + 1];
        if (t1 && t2 && !t1.solid && !t2.solid && !t1.interactable && !t2.interactable && t1.type === 'floorWood' && t2.type === 'floorWood') {
            const ftId = 'fishtank_' + Date.now();
            t1.type = 'placed_structure_fish_tank';
            t1.solid = true;
            t1.interactable = 'fish_tank_interact_' + ftId;
            t1.structureId = ftId;
            t2.type = 'placed_structure_fish_tank';
            t2.solid = true;
            t2.structureId = ftId;
            this.placedStructures = this.placedStructures || [];
            this.placedStructures.push({
                id: ftId,
                type: 'fish_tank',
                scene: 'house',
                x: tx,
                y: ty,
                width: 2,
                height: 1
            });
            this.removeItemFromInventory('fish_tank', 1);
            SoundEngine.craft();
            this.spawnParticles(tx * 32 + 32, ty * 32 + 16, '#06b6d4', 16);
            this.addFloatingText('ติดตั้งตู้ปลาในบ้านสำเร็จ!', tx * 32, ty * 32 - 12, '#38bdf8');
            this.updateHUD();
            return;
        } else {
            this.addFloatingText('ต้องมีพื้นไม้ว่าง 2 ช่องแนวนอนในบ้านเพื่อวางตู้ปลา', tx * 32, ty * 32 - 12, '#f87171');
            return;
        }
    }

    // Hoe
    if (selectedItem.id === 'hoe' && (this.currentScene === 'farm' || this.currentScene === 'greenhouse')) {
        if (this.player.energy <= 0) {
            this.addFloatingText('หมดแรงแล้ว! กินอาหารหรือเข้านอน', this.player.x, this.player.y - 10, '#f87171');
            return;
        }
        if ((tile.type === 'soil' || tile.type === 'grass') && !tile.tilled && !tile.solid) {
            tile.type = 'soil';
            tile.tilled = true;
            let cost = this.player.houseUpgrades.fireplace ? 1 : 2;
            this.player.energy = Math.max(0, this.player.energy - cost);
            this.player.energyRegenDelay = 2000;
            SoundEngine.till();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#9b643a', 8);
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#713f12', 6);
            this.addFloatingText('-' + cost + ' พลังงาน', tx * 32, ty * 32 - 12, '#93c5fd');
            this.updateHUD();
        }
    }
    // Water
    else if (selectedItem.id === 'water' && (this.currentScene === 'farm' || this.currentScene === 'greenhouse')) {
        if (tile.type === 'well' || tile.type === 'water') {
            this.player.waterCan = this.player.waterCanMax;
            const prevT = this.player.thirst !== undefined ? this.player.thirst : 100;
            this.player.thirst = Math.min(this.player.maxThirst || 100, prevT + 40);
            const gainedT = Math.round(this.player.thirst - prevT);
            SoundEngine.water();
            this.addFloatingText(` เติมน้ำเต็มบัว & ดื่มน้ำสดชื่น (+${gainedT} น้ำ)`, tx * 32, ty * 32 - 10, '#38bdf8');
            this.updateHUD();
            return;
        }

        if (this.player.energy <= 0) {
            this.addFloatingText('หมดแรงแล้ว! กินอาหารหรือเข้านอน', this.player.x, this.player.y - 10, '#f87171');
            return;
        }

        if (tile.tilled && !tile.watered) {
            if (this.player.waterCan <= 0) {
                this.addFloatingText('น้ำในบัวหมด! ไปเติมน้ำที่บ่อน้ำ', tx * 32, ty * 32 - 10, '#38bdf8');
                return;
            }
            tile.watered = true;
            this.player.waterCan -= 1;
            this.player.energy = Math.max(0, this.player.energy - (this.player.houseUpgrades.fireplace ? 0 : 1));
            this.player.energyRegenDelay = 2000;
            SoundEngine.water();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#38bdf8', 10);
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#60a5fa', 8);
            this.updateHUD();
        }
    }
    // Seeds
    else if (selectedItem.type === 'seed' && (this.currentScene === 'farm' || this.currentScene === 'greenhouse')) {
        if (tile.tilled && !tile.crop) {
            tile.crop = { cropId: selectedItem.cropId, stage: 0, daysGrown: 0, ready: false };

            selectedItem.count -= 1;
            if (selectedItem.count <= 0) this.player.inventory[this.player.selectedSlot] = null;
            SoundEngine.plant();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#84cc16', 8);
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#facc15', 5);
            this.addFloatingText(' ปลูก ' + selectedItem.name, tx * 32, ty * 32 - 12, '#a3e635');
            this.updateHUD();
        }
    }
    // Food & Consumables
    if (this.isItemEdible(selectedItem)) {
        this.consumeItem(selectedItem, this.player.selectedSlot);
        return;
    }
    // Scythe (Standard Scythe or Malakor Soul Scythe)
    else if (selectedItem.id === 'scythe' || selectedItem.id === 'malakor_soul_scythe') {
        if (tile.crop && tile.crop.ready) {
            this.harvestCrop(tx, ty);
        } else if (tile.tilled && !tile.crop) {
            tile.tilled = false;
            tile.type = 'grass';
            SoundEngine.harvest();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#22c55e', 8);
            this.addFloatingText('ถางหญ้า/คืนสภาพดิน', tx * 32, ty * 32 - 10, '#86efac');
            this.updateHUD();
        } else {
            SoundEngine.step();
            this.addFloatingText('ใช้เกี่ยวพืชผลที่สุกแล้ว', tx * 32, ty * 32 - 10, '#cbd5e1');
        }
        return;
    }
    // Fishing Rod
    else if (selectedItem.id === 'fishing_rod') {
        this.handleFishingAction(tx, ty);
        return;
    }

    // Drop / place non-tool item from hand onto ground
    if (selectedItem && selectedItem.type !== 'tool' && !['hoe', 'water', 'axe', 'pickaxe', 'scythe', 'fishing_rod', 'rifle', 'dragon_rifle', 'dragon_cannon', 'slingshot', 'iron_sword', 'excalibur_sword', 'volcano_sword'].includes(selectedItem.id)) {
        if (!tile.solid && !tile.crop) {
            const itName = selectedItem.name || (WORLD_ITEMS && WORLD_ITEMS[selectedItem.id]?.name) || selectedItem.id;
            this.spawnDroppedItem(selectedItem.id, 1, tx * 32 + 16, ty * 32 + 16, selectedItem.quality || 0, true);
            this.removeItemFromInventory(selectedItem.id, 1);
            SoundEngine.step();
            this.addFloatingText(`วาง ${itName} ลงพื้น (กด E หรือคลิกเพื่อเก็บ)`, tx * 32, ty * 32 - 12, '#fde047');
            this.updateHUD();
            return;
        }
    }
};


// ========================================================
//  FISHING SYSTEM (Stardew Valley Style)
// ========================================================

Game.handleFishingAction = function(tx, ty) {
    if (this.fishing && this.fishing.active) {
        if (this.fishing.state === 'biting') {
            this.startFishingMinigame();
        } else {
            this.cancelFishing('ยกเลิกการตกปลา');
        }
        return;
    }

    // Must be in farm, forest, cave or island scene
    if (this.currentScene !== 'farm' && this.currentScene !== 'forest' && this.currentScene !== 'cave' && this.currentScene !== 'island') {
        this.addFloatingText('ไม่สามารถตกปลาในอาคารได้!', this.player.x, this.player.y - 15, '#f87171');
        return;
    }

    const tile = this.map[ty]?.[tx];
    if (!tile || (tile.type !== 'water' && tile.type !== 'caveWater')) {
        this.addFloatingText('ต้องเหวี่ยงเบ็ดลงในผืนน้ำ!', tx * 32, ty * 32, '#38bdf8');
        return;
    }

    if (this.player.energy < 2) {
        this.addFloatingText('หมดแรงแล้ว! กินอาหารหรือเข้านอน', this.player.x, this.player.y - 10, '#f87171');
        return;
    }

    this.startFishing(tx, ty);
};


Game.startFishing = function(tx, ty) {
    this.player.energy -= 2;
    this.fishing.active = true;
    this.fishing.state = 'waiting';
    this.fishing.targetTile = { x: tx, y: ty };

    this.fishing.bobberPos = {
        x: tx * this.tileSize + 16,
        y: ty * this.tileSize + 16
    };

    // Wait time: 2.5 - 5.5s
    this.fishing.timer = 2500 + Math.random() * 3000;
    this.fishing.biteDuration = 0;
    this.fishing.isHoldingPull = false;

    // Pick fish based on habitat & scene
    const fishList = Object.values(FISH);
    const isRiver = (this.currentScene === 'forest');
    const isOcean = (this.currentScene === 'island');
    const available = fishList.filter((f: any) => {
        if (isOcean) return f.habitat === 'ocean' || f.habitat === 'any';
        if (isRiver) return f.habitat === 'river' || f.habitat === 'any';
        return f.habitat === 'pond' || f.habitat === 'any';
    });
    this.fishing.fish = available[Math.floor(Math.random() * available.length)] || fishList[0];

    SoundEngine.fishCast();
    this.spawnParticles(this.fishing.bobberPos.x, this.fishing.bobberPos.y, '#38bdf8', 12);
    this.addFloatingText(' เหวี่ยงเบ็ดลงน้ำแล้ว... รอปลากินเบ็ด', this.player.x - 20, this.player.y - 15, '#38bdf8');
    this.updateHUD();
};


Game.startFishingMinigame = function() {
    this.fishing.state = 'minigame';
    this.fishing.fishPos = 40;
    this.fishing.fishTarget = 40;
    this.fishing.fishVelocity = 0;
    this.fishing.fishChangeTimer = 400;
    this.fishing.barPos = 25;
    this.fishing.barVelocity = 0;
    const diff = this.fishing.fish?.difficulty || 1;
    this.fishing.barHeight = Math.max(18, 38 - diff * 3.5);
    this.fishing.progress = 35;
    this.fishing.isHoldingPull = false;

    const overlay = document.getElementById('fishingOverlay');
    if (overlay) overlay.style.display = 'flex';
    const hint = document.getElementById('fishNameHint');
    if (hint && this.fishing.fish) {
        hint.textContent = `ปลาติดเบ็ดแล้ว! (${this.fishing.fish.name})`;
    }
    SoundEngine.fishBite();
};


Game.updateFishing = function(dt) {
    if (!this.fishing || !this.fishing.active) return;

    if (this.fishing.state === 'waiting') {
        this.fishing.timer -= dt;
        if (this.fishing.timer <= 0) {
            this.fishing.state = 'biting';
            this.fishing.biteDuration = 2200; // 2.2 seconds reaction window
            SoundEngine.fishBite();
            this.spawnParticles(this.fishing.bobberPos.x, this.fishing.bobberPos.y, '#ffffff', 8);
        }
    } else if (this.fishing.state === 'biting') {
        this.fishing.biteDuration -= dt;
        // Bobber wiggle
        this.fishing.bobberPos.y += (Math.sin(performance.now() / 40) * 0.8);
        if (this.fishing.biteDuration <= 0) {
            SoundEngine.fishEscape();
            this.cancelFishing('ปลาหลุดไปแล้ว! แตะไม่ทัน');
        }
    } else if (this.fishing.state === 'minigame') {
        const fish = this.fishing.fish;
        const diff = fish?.difficulty || 1;

        // Fish AI motion
        this.fishing.fishChangeTimer -= dt;
        if (this.fishing.fishChangeTimer <= 0) {
            this.fishing.fishChangeTimer = 350 + Math.random() * (1200 / diff);
            this.fishing.fishTarget = 8 + Math.random() * 84;
        }
        const fishSpeed = 0.04 + diff * 0.035;
        this.fishing.fishPos += (this.fishing.fishTarget - this.fishing.fishPos) * fishSpeed;

        // Bar physics (smooth acceleration & gravity)
        if (this.fishing.isHoldingPull) {
            this.fishing.barVelocity = Math.min(1.9, this.fishing.barVelocity + 0.18);
        } else {
            this.fishing.barVelocity = Math.max(-1.6, this.fishing.barVelocity - 0.15);
        }
        this.fishing.barPos += this.fishing.barVelocity;
        if (this.fishing.barPos < 0) {
            this.fishing.barPos = 0;
            this.fishing.barVelocity = 0;
        }
        const maxBarPos = 100 - this.fishing.barHeight;
        if (this.fishing.barPos > maxBarPos) {
            this.fishing.barPos = maxBarPos;
            this.fishing.barVelocity = 0;
        }

        // Check if bar covers fish
        const inBar = (this.fishing.fishPos >= this.fishing.barPos &&
                       this.fishing.fishPos <= this.fishing.barPos + this.fishing.barHeight);

        if (inBar) {
            this.fishing.progress += 0.32 * (dt / 16);
            if (Math.random() < 0.15) SoundEngine.fishReel();
        } else {
            this.fishing.progress -= 0.22 * (dt / 16);
        }
        this.fishing.progress = Math.max(0, Math.min(100, this.fishing.progress));

        // Update DOM elements
        const barEl = document.getElementById('fishingBar');
        const fishEl = document.getElementById('fishingTarget');
        const progEl = document.getElementById('fishingProgressFill');
        if (barEl) {
            barEl.style.bottom = this.fishing.barPos + '%';
            barEl.style.height = this.fishing.barHeight + '%';
            barEl.style.borderColor = inBar ? '#4ade80' : '#f59e0b';
            barEl.style.backgroundColor = inBar ? 'rgba(74, 222, 128, 0.45)' : 'rgba(245, 158, 11, 0.35)';
        }
        if (fishEl) {
            fishEl.style.bottom = this.fishing.fishPos + '%';
        }
        if (progEl) {
            progEl.style.height = this.fishing.progress + '%';
        }

        if (this.fishing.progress >= 100) {
            this.completeFishingCatch();
        } else if (this.fishing.progress <= 0) {
            SoundEngine.fishEscape();
            this.cancelFishing('ปลาหลุดไปแล้ว! แถบความคืบหน้าหมด');
        }
    }
};


Game.completeFishingCatch = function() {
    const fish = this.fishing.fish;
    const overlay = document.getElementById('fishingOverlay');
    if (overlay) overlay.style.display = 'none';

    this.fishing.active = false;
    this.fishing.state = 'idle';

    if (fish) {
        SoundEngine.fishCatch();
        const quality = this.rollItemQuality('fishing', this.player.skills?.fishing || 1);
        this.addItemToInventory(fish.id, 1, fish.name, quality);
        this.addXp(fish.xp);

        // Treasure Hunter Perk (+40% chance of sunken treasure chest)
        if (this.player.skillMastery?.treasure_hunter && Math.random() < 0.40) {
            const treasures = ['diamond', 'cinder_shard', 'dragon_tooth', 'ruby', 'emerald'];
            const tItem = treasures[Math.floor(Math.random() * treasures.length)];
            const bonusGold = 150 + Math.floor(Math.random() * 200);
            this.player.gold += bonusGold;
            this.addItemToInventory(tItem, 1);
            SoundEngine.bell();
            this.addFloatingText(`‍ ตกพบหีบสมบัติใต้สมุทร! (+${bonusGold}G & ${WORLD_ITEMS[tItem]?.name || tItem})`, this.player.x - 40, this.player.y - 45, '#fde047');
        }

        const qText = this.getQualityBadgeText(quality);
        const qLabel = qText ? ` (${qText})` : '';
        this.spawnParticles(this.player.x + 12, this.player.y + 16, '#facc15', 20);
        this.spawnParticles(this.player.x + 12, this.player.y + 16, '#38bdf8', 16);
        this.addFloatingText(` ตกได้ ${fish.name}${qLabel}! (+${fish.xp} XP)`, this.player.x - 20, this.player.y - 25, '#4ade80');
        this.updateHUD();
    }
};


Game.cancelFishing = function(reason = 'ยกเลิกการตกปลา') {
    const overlay = document.getElementById('fishingOverlay');
    if (overlay) overlay.style.display = 'none';
    this.fishing.active = false;
    this.fishing.state = 'idle';
    this.addFloatingText(reason, this.player.x - 10, this.player.y - 15, '#cbd5e1');
};


Game.drawFishingBobber = function() {
    if (!this.fishing || !this.fishing.active) return;
    const px = Math.round(this.player.x + 12 - this.camera.x);
    const py = Math.round(this.player.y + 16 - this.camera.y);
    const bx = Math.round(this.fishing.bobberPos.x - this.camera.x);
    const by = Math.round(this.fishing.bobberPos.y - this.camera.y);

    // Fishing line (curved delicate thread)
    this.ctx.save();
    this.ctx.strokeStyle = 'rgba(241, 245, 249, 0.75)';
    this.ctx.lineWidth = 1;
    this.ctx.beginPath();
    this.ctx.moveTo(px, py - 4);
    const midX = (px + bx) / 2;
    const midY = Math.min(py, by) - 16;
    this.ctx.quadraticCurveTo(midX, midY, bx, by);
    this.ctx.stroke();

    // Bobber
    if (SPRITES.bobber) {
        this.ctx.drawImage(SPRITES.bobber, bx - 6, by - 6);
    } else {
        this.ctx.fillStyle = '#ef4444';
        this.ctx.fillRect(bx - 3, by - 3, 6, 6);
    }

    // Water ripple around bobber
    const ripple = (performance.now() / 150) % 8;
    this.ctx.strokeStyle = 'rgba(147, 197, 253, 0.45)';
    this.ctx.beginPath();
    this.ctx.ellipse(bx, by + 4, 4 + ripple, 2 + ripple * 0.5, 0, 0, Math.PI * 2);
    this.ctx.stroke();

    // Bite bubble alert (!)
    if (this.fishing.state === 'biting') {
        const bounce = Math.sin(performance.now() / 80) * 3;
        if (SPRITES.fishBiteBubble) {
            this.ctx.drawImage(SPRITES.fishBiteBubble, bx - 8, by - 24 + bounce);
        } else {
            this.ctx.fillStyle = '#ef4444';
            this.ctx.font = 'bold 16px "Prompt", sans-serif';
            this.ctx.fillText('!', bx - 3, by - 12 + bounce);
        }
    }
    this.ctx.restore();
};


// ========================================================
//  TOUCH / MOBILE CONTROLS & ORIENTATION DETECTOR
// ========================================================

Game.checkOrientationNotice = function() {
    const noticeEl = document.getElementById('orientationNotice');
    if (!noticeEl) return;
    const isPortrait = window.innerHeight > window.innerWidth;
    const isMobileSize = window.innerWidth <= 900 || window.innerHeight <= 900;
    const hasTouch = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);

    if (isPortrait && (isMobileSize || hasTouch) && !this.orientationDismissed) {
        noticeEl.style.display = 'flex';
    } else {
        noticeEl.style.display = 'none';
    }
};

Game.dismissOrientationNotice = function() {
    this.orientationDismissed = true;
    const noticeEl = document.getElementById('orientationNotice');
    if (noticeEl) noticeEl.style.display = 'none';
};

Game.setupTouchControls = function() {
    const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || window.innerWidth <= 840 || this.forceTouchControls;
    const touchOverlay = document.getElementById('touchControls');
    if (touchOverlay) {
        touchOverlay.classList.toggle('force-show', isTouchDevice);
        touchOverlay.style.display = isTouchDevice ? 'flex' : 'none';
    }
    this.checkOrientationNotice();
    if (this._touchControlsInitialized) return;
    this._touchControlsInitialized = true;

    // ========================================================
    // ROV-STYLE DYNAMIC FLOATING VIRTUAL JOYSTICK
    // ========================================================
    const joystickZone = document.getElementById('virtualJoystickZone');
    const joystickBase = document.getElementById('virtualJoystickBase');
    const joystickKnob = document.getElementById('virtualJoystickKnob');
    let dpadTouchId: number | null = null;
    let joystickOriginX = 0;
    let joystickOriginY = 0;

    if (joystickZone && joystickBase && joystickKnob) {
        const updateJoystickMovement = (clientX: number, clientY: number) => {
            const dx = clientX - joystickOriginX;
            const dy = clientY - joystickOriginY;
            const dist = Math.hypot(dx, dy);
            const maxRadius = 45;
            const angle = Math.atan2(dy, dx);
            const clampedDist = Math.min(dist, maxRadius);

            const knobX = Math.cos(angle) * clampedDist;
            const knobY = Math.sin(angle) * clampedDist;
            joystickKnob.style.transform = `translate(${knobX}px, ${knobY}px)`;

            const deadZone = 7;
            if (dist > deadZone) {
                const normDist = (clampedDist - deadZone) / (maxRadius - deadZone);
                const cosVal = Math.cos(angle);
                const sinVal = Math.sin(angle);

                // True 360-degree analog vector
                this.player.joystickMove = {
                    x: cosVal * normDist,
                    y: sinVal * normDist
                };

                const threshold = 0.38;
                this.keys.right = cosVal > threshold;
                this.keys.left = cosVal < -threshold;
                this.keys.down = sinVal > threshold;
                this.keys.up = sinVal < -threshold;

                if (Math.abs(dx) > Math.abs(dy)) {
                    this.player.direction = dx > 0 ? 'right' : 'left';
                } else {
                    this.player.direction = dy > 0 ? 'down' : 'up';
                }
            } else {
                this.player.joystickMove = null;
                this.keys.up = false;
                this.keys.down = false;
                this.keys.left = false;
                this.keys.right = false;
            }
        };

        const handleJoystickStart = (e: TouchEvent) => {
            if (dpadTouchId !== null) return;
            const touch = e.changedTouches[0];
            dpadTouchId = touch.identifier;

            // Dynamically position joystick base around thumb (with safe padding from screen edges)
            const padRadius = 62;
            joystickOriginX = Math.max(padRadius, Math.min(window.innerWidth * 0.45, touch.clientX));
            joystickOriginY = Math.max(padRadius + 45, Math.min(window.innerHeight - padRadius, touch.clientY));

            joystickBase.style.left = `${joystickOriginX}px`;
            joystickBase.style.top = `${joystickOriginY}px`;
            joystickBase.style.bottom = 'auto';
            joystickBase.classList.add('is-active');

            updateJoystickMovement(touch.clientX, touch.clientY);

            SoundEngine.init();
            if (SoundEngine.isBgmOn()) SoundEngine.startBgm();
        };

        const handleJoystickMove = (e: TouchEvent) => {
            if (dpadTouchId === null) return;
            for (let i = 0; i < e.touches.length; i++) {
                if (e.touches[i].identifier === dpadTouchId) {
                    e.preventDefault();
                    updateJoystickMovement(e.touches[i].clientX, e.touches[i].clientY);
                    break;
                }
            }
        };

        const handleJoystickEnd = (e: TouchEvent) => {
            if (dpadTouchId === null) return;
            for (let i = 0; i < e.changedTouches.length; i++) {
                if (e.changedTouches[i].identifier === dpadTouchId) {
                    dpadTouchId = null;
                    this.player.joystickMove = null;
                    joystickKnob.style.transform = 'translate(0px, 0px)';
                    joystickBase.classList.remove('is-active');
                    this.keys.up = false;
                    this.keys.down = false;
                    this.keys.left = false;
                    this.keys.right = false;
                    break;
                }
            }
        };

        joystickZone.addEventListener('touchstart', handleJoystickStart, { passive: false });
        window.addEventListener('touchmove', handleJoystickMove, { passive: false });
        window.addEventListener('touchend', handleJoystickEnd, { passive: false });
        window.addEventListener('touchcancel', handleJoystickEnd, { passive: false });
    }

    // Individual D-Pad buttons fallback for mouse clicks
    const dpadBtns = document.querySelectorAll('.touch-btn[data-dir]');
    dpadBtns.forEach(btn => {
        const dir = btn.getAttribute('data-dir');
        if (!dir) return;

        const press = (e: Event) => {
            e.preventDefault();
            this.keys[dir] = true;
            SoundEngine.init();
            if (SoundEngine.isBgmOn()) SoundEngine.startBgm();
        };

        const release = (e: Event) => {
            e.preventDefault();
            this.keys[dir] = false;
        };

        btn.addEventListener('mousedown', press);
        btn.addEventListener('mouseup', release);
        btn.addEventListener('mouseleave', release);
    });

    // Helper: auto-switch to any available weapon in inventory if active slot is a tool or empty
    const ensureWeaponEquipped = () => {
        if (!this.player || !Array.isArray(this.player.inventory)) return false;
        const cur = this.player.inventory[this.player.selectedSlot];
        if (cur && (cur.type === 'weapon' || (typeof WEAPONS !== 'undefined' && WEAPONS[cur.id]))) {
            return true;
        }
        const wIdx = this.player.inventory.findIndex((it: any) => it && (it.type === 'weapon' || (typeof WEAPONS !== 'undefined' && WEAPONS[it.id])));
        if (wIdx >= 0) {
            this.player.selectedSlot = wIdx;
            if (typeof this.renderHotbar === 'function') this.renderHotbar();
            return true;
        }
        return false;
    };

    // Direct Multi-Touch Screen/Canvas Combat (แตะหน้าจอเพื่อยิงได้ทันทีขณะที่มือซ้ายยังเดินอยู่!)
    let canvasShootTouchId: number | null = null;
    let canvasShootInterval: number | null = null;
    let curShootClientX = 0;
    let curShootClientY = 0;

    const fireAtCurrentTouch = (clientX: number, clientY: number) => {
        if (!this.player || !this.canvas) return;
        curShootClientX = clientX;
        curShootClientY = clientY;

        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        const wx = (clientX - rect.left) * scaleX + this.camera.x;
        const wy = (clientY - rect.top) * scaleY + this.camera.y;
        const tx = Math.floor(wx / this.tileSize);
        const ty = Math.floor(wy / this.tileSize);

        // 0. Check if tapped directly on a ripe ready crop (ALWAYS HARVEST INSTANTLY!)
        const tapTile = (this.map && this.map[ty]) ? this.map[ty][tx] : null;
        const pTileX = Math.floor((this.player.x + 10) / this.tileSize);
        const pTileY = Math.floor((this.player.y + 20) / this.tileSize);
        const pDist = Math.hypot(pTileX - tx, pTileY - ty);

        if (tapTile && tapTile.crop && tapTile.crop.ready && pDist <= 3.8) {
            this.harvestCrop(tx, ty);
            return;
        }

        // Check if tapped directly on an interactive tile (sailboat, door, chest, well) BEFORE weapon shooting
        if (tapTile && tapTile.interactable && pDist <= 3.8) {
            this.handleTileInteract(tapTile.interactable, tx, ty);
            return;
        }

        const selItem = this.player.inventory[this.player.selectedSlot];
        const isWeapon = (selItem && (selItem.type === 'weapon' || (typeof WEAPONS !== 'undefined' && WEAPONS[selItem.id])));
        const isToolOrFarmItem = (selItem && (selItem.type === 'tool' || selItem.type === 'seed' || ['hoe', 'water', 'axe', 'pickaxe', 'scythe', 'sickle', 'fishing_rod'].includes(selItem.id)));

        // 1. Check if directly tapping a hostile enemy
        let targetedEnemy: any = null;
        if (this.boss && this.boss.alive && Math.hypot((this.boss.x + 32) - wx, (this.boss.y + 32) - wy) < 100) {
            targetedEnemy = { x: this.boss.x + (this.boss.width || 64) / 2, y: this.boss.y + (this.boss.height || 64) / 2 };
        } else if (this.worldMonsters && this.worldMonsters.length > 0) {
            for (const m of this.worldMonsters) {
                if (!m.alive || (m.hp !== undefined && m.hp <= 0)) continue;
                if (Math.hypot((m.x + 16) - wx, (m.y + 16) - wy) < 60) {
                    targetedEnemy = { x: m.x + (m.width || 32) / 2, y: m.y + (m.height || 32) / 2 };
                    break;
                }
            }
        } else if (this.currentScene === 'farm' && this.demonBugs) {
            for (const b of this.demonBugs) {
                if (b.hp !== undefined && b.hp <= 0) continue;
                if (Math.hypot((b.x + 14) - wx, (b.y + 14) - wy) < 50) {
                    targetedEnemy = { x: b.x + 14, y: b.y + 14 };
                    break;
                }
            }
        }

        // If directly tapped on an enemy, attack that enemy!
        if (targetedEnemy) {
            if (!isWeapon) ensureWeaponEquipped();
            this.playerAttackAt(targetedEnemy.x, targetedEnemy.y);
            return;
        }

        // 2. If holding a tool or seeds, or on the farm/greenhouse: ALWAYS prioritize farming / harvesting / tile interaction!
        if (isToolOrFarmItem || this.currentScene === 'farm' || this.currentScene === 'greenhouse') {
            if (isWeapon) {
                // If user deliberately selected a weapon on the farm, let them shoot
                this.playerAttackAt(wx, wy);
                return;
            }
            // Always harvest, till, water, plant or cut weeds with tool/hands!
            this.actOnTile(tx, ty);
            return;
        }

        // 3. In combat zones with weapon equipped: attack
        if (isWeapon) {
            this.playerAttackAt(wx, wy);
            return;
        }

        // 4. Default: act on tile
        this.actOnTile(tx, ty);
    };

    window.addEventListener('touchstart', (e: TouchEvent) => {
        if (!this.canvas || this.activeModal || this.activeDialogue) return;

        for (let i = 0; i < e.changedTouches.length; i++) {
            const t = e.changedTouches[i];
            if (t.identifier === dpadTouchId) continue;

            // Only shoot if touching the game canvas directly (never intercept hotbar, menus, or modals!)
            if (t.target !== this.canvas) continue;

            // Also ignore touches on the left 48% of screen (virtual joystick thumb area)
            if (t.clientX < window.innerWidth * 0.48 && t.clientY > 55) continue;

            e.preventDefault();
            canvasShootTouchId = t.identifier;

            fireAtCurrentTouch(t.clientX, t.clientY);

            if (canvasShootInterval !== null) clearInterval(canvasShootInterval);
            canvasShootInterval = window.setInterval(() => {
                if (canvasShootTouchId === null || this.activeModal || this.activeDialogue) {
                    if (canvasShootInterval !== null) {
                        clearInterval(canvasShootInterval);
                        canvasShootInterval = null;
                    }
                    return;
                }
                fireAtCurrentTouch(curShootClientX, curShootClientY);
            }, 180);

            break;
        }
    }, { passive: false });

    window.addEventListener('touchmove', (e: TouchEvent) => {
        if (canvasShootTouchId === null || !this.canvas) return;
        for (let i = 0; i < e.touches.length; i++) {
            const t = e.touches[i];
            if (t.identifier === canvasShootTouchId) {
                e.preventDefault();
                curShootClientX = t.clientX;
                curShootClientY = t.clientY;
                break;
            }
        }
    }, { passive: false });

    const endCanvasShoot = (e: TouchEvent) => {
        if (canvasShootTouchId === null) return;
        for (let i = 0; i < e.changedTouches.length; i++) {
            if (e.changedTouches[i].identifier === canvasShootTouchId) {
                canvasShootTouchId = null;
                if (canvasShootInterval !== null) {
                    clearInterval(canvasShootInterval);
                    canvasShootInterval = null;
                }
                break;
            }
        }
    };

    window.addEventListener('touchend', endCanvasShoot, { passive: false });
    window.addEventListener('touchcancel', endCanvasShoot, { passive: false });

    // Action Button [A] (Smart Auto-Aim Combat / Farm / Harvest)
    const btnA = document.getElementById('touchBtnA');
    if (btnA) {
        let holdIntervalA: number | null = null;
        let isHoldingA = false;

        const executeActionA = () => {
            if (!this.player) return;

            if (this.fishing && this.fishing.active) {
                if (this.fishing.state === 'biting') {
                    this.startFishingMinigame();
                    return;
                } else if (this.fishing.state === 'minigame') {
                    this.fishing.isHoldingPull = true;
                    return;
                } else if (this.fishing.state === 'waiting') {
                    this.cancelFishing('ยกเลิกการตกปลา');
                    return;
                }
            }

            const selItem = this.player.inventory[this.player.selectedSlot];
            if (this.isItemEdible(selItem)) {
                this.consumeItem(selItem, this.player.selectedSlot);
                return;
            }

            if (selItem && selItem.id === 'fishing_rod') {
                const target = this.getTargetTile();
                this.handleFishingAction(target.x, target.y);
                return;
            }

            // Check if facing an interactive tile (sailboat, door, chest, well) BEFORE weapon attack
            const target = this.getTargetTile();
            const facingTile = (this.map && this.map[target.y]) ? this.map[target.y][target.x] : null;
            if (facingTile && facingTile.interactable) {
                this.handleTileInteract(facingTile.interactable, target.x, target.y);
                return;
            }

            const isWeapon = (selItem && (selItem.type === 'weapon' || (typeof WEAPONS !== 'undefined' && WEAPONS[selItem.id])));
            const isToolOrFarmItem = (selItem && (selItem.type === 'tool' || selItem.type === 'seed' || ['hoe', 'water', 'axe', 'pickaxe', 'scythe', 'sickle', 'fishing_rod'].includes(selItem.id)));
            const isFarmScene = (this.currentScene === 'farm' || this.currentScene === 'greenhouse');

            // If player is holding a tool/seed, or on the farm without an equipped weapon: ALWAYS USE TOOL / HARVEST!
            if (isToolOrFarmItem || (isFarmScene && !isWeapon)) {
                this.useCurrentTool();
                return;
            }

            const nearestEnemy = typeof this.findNearestCombatTarget === 'function' ? this.findNearestCombatTarget(720) : null;

            if (isWeapon || nearestEnemy) {
                if (!isWeapon) {
                    ensureWeaponEquipped();
                }

                let tx = this.player.x + 12;
                let ty = this.player.y + 14;

                if (nearestEnemy) {
                    // Auto-target closest living monster or boss!
                    tx = nearestEnemy.x;
                    ty = nearestEnemy.y;
                } else {
                    // Shoot towards movement direction or facing direction
                    let dirX = 0;
                    let dirY = 0;
                    if (this.keys.up) dirY -= 1;
                    if (this.keys.down) dirY += 1;
                    if (this.keys.left) dirX -= 1;
                    if (this.keys.right) dirX += 1;

                    if (dirX !== 0 || dirY !== 0) {
                        tx += dirX * 220;
                        ty += dirY * 220;
                    } else {
                        if (this.player.direction === 'up') ty -= 220;
                        else if (this.player.direction === 'down') ty += 220;
                        else if (this.player.direction === 'left') tx -= 220;
                        else if (this.player.direction === 'right') tx += 220;
                    }
                }

                this.playerAttackAt(tx, ty);
            } else {
                this.useCurrentTool();
            }
        };

        const pressA = (e: Event) => {
            e.preventDefault();
            SoundEngine.init();
            if (SoundEngine.isBgmOn()) SoundEngine.startBgm();

            isHoldingA = true;
            btnA.classList.add('active');
            executeActionA();

            // Continuous auto-fire while holding button A!
            if (holdIntervalA !== null) clearInterval(holdIntervalA);
            holdIntervalA = window.setInterval(() => {
                if (!isHoldingA) {
                    if (holdIntervalA !== null) {
                        clearInterval(holdIntervalA);
                        holdIntervalA = null;
                    }
                    return;
                }
                executeActionA();
            }, 110);
        };

        const releaseA = (e: Event) => {
            e.preventDefault();
            isHoldingA = false;
            btnA.classList.remove('active');
            if (holdIntervalA !== null) {
                clearInterval(holdIntervalA);
                holdIntervalA = null;
            }
            if (this.fishing && this.fishing.active && this.fishing.state === 'minigame') {
                this.fishing.isHoldingPull = false;
            }
        };

        btnA.addEventListener('touchstart', pressA, { passive: false });
        btnA.addEventListener('touchend', releaseA, { passive: false });
        btnA.addEventListener('touchcancel', releaseA, { passive: false });
        btnA.addEventListener('mousedown', pressA);
        btnA.addEventListener('mouseup', releaseA);
        btnA.addEventListener('mouseleave', releaseA);
    }

    // Action Button [E] (Interact / Harvest / Talk) - Supports hold to harvest continuously!
    const btnE = document.getElementById('touchBtnE');
    if (btnE) {
        let holdIntervalE: number | null = null;
        let isHoldingE = false;

        const pressE = (e: Event) => {
            e.preventDefault();
            SoundEngine.init();
            if (SoundEngine.isBgmOn()) SoundEngine.startBgm();
            isHoldingE = true;
            btnE.classList.add('active');
            this.interact();

            if (holdIntervalE !== null) clearInterval(holdIntervalE);
            holdIntervalE = window.setInterval(() => {
                if (!isHoldingE) {
                    if (holdIntervalE !== null) {
                        clearInterval(holdIntervalE);
                        holdIntervalE = null;
                    }
                    return;
                }
                this.interact();
            }, 140);
        };

        const releaseE = (e: Event) => {
            e.preventDefault();
            isHoldingE = false;
            btnE.classList.remove('active');
            if (holdIntervalE !== null) {
                clearInterval(holdIntervalE);
                holdIntervalE = null;
            }
        };

        btnE.addEventListener('touchstart', pressE, { passive: false });
        btnE.addEventListener('touchend', releaseE, { passive: false });
        btnE.addEventListener('touchcancel', releaseE, { passive: false });
        btnE.addEventListener('mousedown', pressE);
        btnE.addEventListener('mouseup', releaseE);
        btnE.addEventListener('mouseleave', releaseE);
    }

    // Action Button [Dash] (Mobile Dodge Roll)
    const btnDash = document.getElementById('touchBtnDash');
    if (btnDash) {
        btnDash.addEventListener('touchstart', (e: Event) => {
            e.preventDefault();
            this.playerDash();
        }, { passive: false });
        btnDash.addEventListener('click', (e: Event) => {
            e.preventDefault();
            this.playerDash();
        });
    }

    // Action Button [Guard / Parry] (Mobile Touch Shield)
    const btnGuard = document.getElementById('touchBtnGuard');
    if (btnGuard) {
        const pressGuard = (e: Event) => {
            e.preventDefault();
            this.startPlayerGuard();
            btnGuard.classList.add('active');
        };
        const releaseGuard = (e: Event) => {
            e.preventDefault();
            this.stopPlayerGuard();
            btnGuard.classList.remove('active');
        };

        btnGuard.addEventListener('touchstart', pressGuard, { passive: false });
        btnGuard.addEventListener('touchend', releaseGuard, { passive: false });
        btnGuard.addEventListener('touchcancel', releaseGuard, { passive: false });
        btnGuard.addEventListener('mousedown', pressGuard);
        btnGuard.addEventListener('mouseup', releaseGuard);
        btnGuard.addEventListener('mouseleave', releaseGuard);
    }

    // Also allow tapping/holding anywhere inside fishing overlay to pull green bar
    const fishingOverlay = document.getElementById('fishingOverlay');
    if (fishingOverlay) {
        const pullStart = (e: Event) => {
            e.preventDefault();
            if (this.fishing) this.fishing.isHoldingPull = true;
        };

        const pullEnd = (e: Event) => {
            e.preventDefault();
            if (this.fishing) this.fishing.isHoldingPull = false;
        };

        fishingOverlay.addEventListener('touchstart', pullStart, { passive: false });
        fishingOverlay.addEventListener('touchend', pullEnd, { passive: false });
        fishingOverlay.addEventListener('mousedown', pullStart);
        fishingOverlay.addEventListener('mouseup', pullEnd);
    }

    // Ensure HUD menu icons and user badge open reliably on mobile touch without lag
    document.querySelectorAll('.btn-hud-icon, .user-profile-badge').forEach((el) => {
        el.addEventListener('touchend', (e: Event) => {
            const te = e as TouchEvent;
            if (te.cancelable) te.preventDefault();
            (el as HTMLElement).click();
        }, { passive: false });
    });
};

Game.toggleFullscreen = function() {
    const doc: any = document;
    const docEl: any = document.documentElement;

    if (!doc.fullscreenElement && !doc.webkitFullscreenElement) {
        if (docEl.requestFullscreen) docEl.requestFullscreen().catch(() => {});
        else if (docEl.webkitRequestFullscreen) docEl.webkitRequestFullscreen();
        this.addFloatingText('เปิดโหมดเต็มจอ (Fullscreen)', this.player.x, this.player.y - 15, '#38bdf8');
    } else {
        if (doc.exitFullscreen) doc.exitFullscreen().catch(() => {});
        else if (doc.webkitExitFullscreen) doc.webkitExitFullscreen();
        this.addFloatingText('ออกจากโหมดเต็มจอ', this.player.x, this.player.y - 15, '#fde047');
    }
};

Game.toggleTouchControls = function() {
    this.forceTouchControls = !this.forceTouchControls;
    const touchOverlay = document.getElementById('touchControls');
    if (touchOverlay) {
        touchOverlay.classList.toggle('force-show', this.forceTouchControls);
        touchOverlay.style.display = this.forceTouchControls ? 'flex' : 'none';
    }
    this.addFloatingText(this.forceTouchControls ? 'เปิดปุ่มควบคุมบนหน้าจอ' : 'ซ่อนปุ่มควบคุมบนหน้าจอ', this.player.x, this.player.y - 15, '#38bdf8');
};


Game.toggleMusic = function() {
    SoundEngine.toggleBgm();
    const isPlaying = SoundEngine.isBgmOn();
    const icon = document.getElementById('hudBgmIcon');
    if (icon) icon.textContent = isPlaying ? 'ON' : 'OFF';
    const menuIcon = document.getElementById('menuBgmIcon');
    if (menuIcon) menuIcon.textContent = isPlaying ? 'ON' : 'OFF';
    const menuStatus = document.getElementById('menuBgmStatus');
    if (menuStatus) menuStatus.textContent = isPlaying ? 'สถานะ: เปิดเสียงเพลง' : 'สถานะ: ปิดเสียงเพลง';
    this.addFloatingText(isPlaying ? 'เปิดเสียงดนตรี (BGM)' : 'ปิดเสียงดนตรี', this.player.x, this.player.y - 15, '#38bdf8');
};


Game.updateQuestTrackerHUD = function() {
    const trackerEl = document.getElementById('hudQuestTracker');
    if (!trackerEl || !this.player) return;

    const curQuestId = this.player.currentQuestId || 'q1';
    const qData = (typeof QUESTS !== 'undefined' && QUESTS[curQuestId]) ? QUESTS[curQuestId] : null;
    if (!qData) {
        trackerEl.style.display = 'none';
        return;
    }
    trackerEl.style.display = 'block';

    const titleEl = document.getElementById('questTrackerTitle');
    const objEl = document.getElementById('questTrackerObjective');
    const subObjEl = document.getElementById('questTrackerSubObjective');
    const hintEl = document.getElementById('questTrackerHint');

    if (titleEl) {
        const parts = qData.title.split(':');
        titleEl.textContent = (parts[0] || 'ภารกิจ') + ': ' + (parts[1] || '').trim();
    }

    const qp = this.player.questProgress || {};
    let objText = '';
    let subText = '';
    let hintText = '';
    let isComplete = false;

    if (qData.id === 'q1') {
        const bugs = qp.bugsDefeated || 0;
        const spores = this.getItemCount('blight_spore');
        objText = 'กำจัดแมลงปีศาจ (' + bugs + ' / 3)';
        subText = 'เก็บสปอร์กลายพันธุ์ (' + spores + ' / 2)';
        isComplete = bugs >= 3 && spores >= 2;
        hintText = isComplete ? 'ไปพบนายกเทศมนตรีกิลเบิร์ตที่คฤหาสน์หมู่บ้าน' : 'ปราบแมลงปีศาจที่บุกเข้ามาในไร่';
    } else if (qData.id === 'q2') {
        const spores = this.getItemCount('blight_spore');
        const herbs = this.getItemCount('starflower_herb');
        objText = 'สปอร์กลายพันธุ์ (' + spores + ' / 3)';
        subText = 'สมุนไพรดวงดาว (' + herbs + ' / 2)';
        isComplete = spores >= 3 && herbs >= 2;
        hintText = isComplete ? 'นำวัตถุดิบส่งให้หมอยาลิเลียนที่คลินิก' : 'เก็บสมุนไพรดวงดาวในป่าเอลเดอร์วู้ด';
    } else if (qData.id === 'q3') {
        const wolves = qp.wolvesKilled || 0;
        const rubies = this.getItemCount('ruby_gem');
        objText = 'กำจัดหมาป่าเงา (' + wolves + ' / 3)';
        subText = 'ขุดแร่ทับทิม (' + rubies + ' / 2)';
        isComplete = wolves >= 3 && rubies >= 2;
        hintText = isComplete ? 'รายงานผู้กองวาเลเรียที่ประตูปราการเหนือ' : 'ล่าหมาป่าในป่า และขุดแร่ในถ้ำ';
    } else if (qData.id === 'q4') {
        const caveBugs = qp.caveMonstersDefeated || 0;
        const manas = this.getItemCount('mana_crystal');
        objText = 'ปราบมอนสเตอร์ถ้ำ (' + caveBugs + ' / 3)';
        subText = 'ขุดผลึกมานา (' + manas + ' / 2)';
        isComplete = caveBugs >= 3 && manas >= 2;
        hintText = isComplete ? 'กลับไปรายงานผู้เฒ่าเอลดริน' : 'ลงสำรวจถ้ำผลึกหินทางตะวันออกเฉียงเหนือ';
    } else if (qData.targetBoss) {
        const bossDead = !!(this.player.defeatedBosses && this.player.defeatedBosses[qData.targetBoss]);
        objText = 'ปราบมหาบอส ' + qData.targetBoss.replace('boss_', '').toUpperCase();
        isComplete = bossDead;
        hintText = isComplete ? 'สำเร็จภารกิจ! รับรางวัลอันทรงเกียรติ' : 'เตรียมอาหารบัฟและอาวุธให้พร้อมก่อนบุก';
    } else {
        objText = qData.desc.substring(0, 36) + '...';
        hintText = 'ดูรายละเอียดเพิ่มเติมในสมุดเควสต์ (ESC)';
    }

    if (objEl) {
        objEl.textContent = objText;
        objEl.style.color = isComplete ? '#4ade80' : '#f8fafc';
    }
    if (subObjEl) {
        if (subText) {
            subObjEl.style.display = 'block';
            subObjEl.textContent = subText;
            subObjEl.style.color = isComplete ? '#4ade80' : '#e2e8f0';
        } else {
            subObjEl.style.display = 'none';
        }
    }
    if (hintEl) {
        if (!this.player.sailboatRepaired && this.currentScene === 'village') {
            hintEl.textContent = '[เป้าหมาย]: ซ่อมเรือใบที่ท่าเรือ (ไม้ 20, เหล็ก 5, 500 G) เพื่อข้ามสู่เกาะ';
            hintEl.style.color = '#38bdf8';
        } else {
            hintEl.textContent = hintText;
            hintEl.style.color = isComplete ? '#fde047' : '#94a3b8';
        }
    }
};

Game.toggleQuestTracker = function() {
    const body = document.getElementById('questTrackerBody');
    const arrow = document.getElementById('questTrackerToggleBtn');
    if (!body) return;
    const isHidden = body.style.display === 'none';
    body.style.display = isHidden ? 'block' : 'none';
    if (arrow) arrow.textContent = isHidden ? '▼' : '▶';
};

// ========================================================
//  MULTIPLAYER & PVP COLISEUM ARENA SYSTEM
// ========================================================

Game.generatePvPArenaMap = function() {
    const width = 34;
    const height = 24;
    const map = [];

    for (let y = 0; y < height; y++) {
        const row = [];
        for (let x = 0; x < width; x++) {
            const isBorder = (x <= 1 || x >= width - 2 || y <= 1 || y >= height - 2);
            const isExit = (x >= 15 && x <= 18 && y >= height - 2);
            const isCenterColosseum = (Math.hypot(x - 17, y - 12) <= 8.5);

            let type = 'cobblestone';
            let solid = isBorder && !isExit;
            let interactable = isExit ? 'exit_pvp_arena' : null;

            if (isBorder && !isExit) {
                type = 'stoneWall';
            } else if (isCenterColosseum) {
                type = 'stone_path';
            } else if (isExit) {
                type = 'doorMat';
            }

            row.push({
                x, y,
                type,
                solid,
                interactable
            });
        }
        map.push(row);
    }

    // Dueling Bell / Gong at top center (x: 17, y: 3)
    if (map[3] && map[3][17]) {
        map[3][17].type = 'bell';
        map[3][17].solid = true;
        map[3][17].interactable = 'pvp_bell';
    }

    // Corner Torches
    const torches = [[4, 4], [29, 4], [4, 19], [29, 19], [11, 4], [23, 4]];
    torches.forEach(([tx, ty]) => {
        if (map[ty] && map[ty][tx]) {
            map[ty][tx].solid = true;
            map[ty][tx].type = 'lantern';
        }
    });

    return { mapWidth: width, mapHeight: height, map };
};

Game.initPvPArenaScene = function() {
    this.worldMonsters = [];
    this.boss = null;
    this.bossTelegraphs = [];
    this.bossGroundHazards = [];
    this.bossDashGhosts = [];
    this.bossShockwaves = [];
};

Game.travelToPvPArena = function() {
    this.closeAllModals();
    SoundEngine.alarm();
    this.switchScene('pvp_arena', 17, 18);
    this.addFloatingText('เข้าสู่ลานประลองยุทธ์จอมราชันย์!', this.player.x, this.player.y - 25, '#fde047');
};

Game.drawRemotePlayer = function(rp: any) {
    const rx = Math.round(rp.x - this.camera.x);
    const ry = Math.round(rp.y - this.camera.y);

    // 1. Contact shadow
    this.ctx.fillStyle = 'rgba(15, 23, 42, 0.32)';
    this.ctx.beginPath();
    this.ctx.ellipse(rx + 12, ry + 27, 9, 4, 0, 0, Math.PI * 2);
    this.ctx.fill();

    // 2. Character Sprite
    const dir = rp.direction || 'down';
    const frame = rp.frame || 0;
    const spr = SPRITES.player?.[dir]?.[frame] || SPRITES.player?.down?.[0];
    if (spr) {
        this.ctx.drawImage(spr, rx, ry);
    }

    // 3. Remote Slash Animation
    if (rp.isAttacking) {
        this.ctx.save();
        this.ctx.translate(rx + 12, ry + 14);
        let ang = 0;
        if (dir === 'right') ang = 0;
        else if (dir === 'down') ang = Math.PI / 2;
        else if (dir === 'left') ang = Math.PI;
        else ang = -Math.PI / 2;
        this.ctx.rotate(ang);
        this.ctx.strokeStyle = rp.comboStep === 3 ? '#facc15' : '#38bdf8';
        this.ctx.lineWidth = rp.comboStep === 3 ? 5 : 3;
        this.ctx.beginPath();
        this.ctx.arc(14, 0, 24, -Math.PI / 3, Math.PI / 3);
        this.ctx.stroke();
        this.ctx.restore();
    }

    // 4. Overhead Player Name & HP Bar
    const isPvP = (this.currentScene === 'pvp_arena' || this.isPvPEnabled);
    const nameColor = isPvP ? '#f87171' : '#38bdf8';
    this.ctx.font = 'bold 9px "Prompt", sans-serif';
    this.ctx.textAlign = 'center';
    this.ctx.fillStyle = 'rgba(15, 23, 42, 0.75)';
    const tw = this.ctx.measureText(rp.name).width;
    this.ctx.fillRect(rx + 12 - tw / 2 - 4, ry - 18, tw + 8, 12);
    this.ctx.fillStyle = nameColor;
    this.ctx.fillText(rp.name, rx + 12, ry - 9);

    // Mini HP Bar
    const hpRatio = Math.max(0, Math.min(1, (rp.hp || 100) / (rp.maxHp || 100)));
    this.ctx.fillStyle = '#0f172a';
    this.ctx.fillRect(rx + 12 - 14, ry - 5, 28, 3.5);
    this.ctx.fillStyle = hpRatio > 0.4 ? (isPvP ? '#ef4444' : '#22c55e') : '#e11d48';
    this.ctx.fillRect(rx + 12 - 14, ry - 5, Math.round(28 * hpRatio), 3.5);
    this.ctx.textAlign = 'left';

    // 5. Chat Bubble (if chatting)
    if (rp.chatMsg && rp.chatTimer && rp.chatTimer > 0) {
        this.ctx.font = 'bold 9px "Prompt", sans-serif';
        const msgW = this.ctx.measureText(rp.chatMsg).width;
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
        this.ctx.strokeStyle = '#0f172a';
        this.ctx.lineWidth = 1;
        this.ctx.fillRect(rx + 12 - msgW / 2 - 6, ry - 34, msgW + 12, 14);
        this.ctx.strokeRect(rx + 12 - msgW / 2 - 6, ry - 34, msgW + 12, 14);
        this.ctx.fillStyle = '#0f172a';
        this.ctx.fillText(rp.chatMsg, rx + 12 - msgW / 2, ry - 24);
    }
};

Game.receivePvPHit = function(hitData: any, attackerName: string) {
    if (!this.player || this.player.isDead) return;

    let dmg = hitData.damage || 20;

    // Check Guard Stance
    if (this.player.isGuarding) {
        dmg = Math.round(dmg * 0.4);
        if (typeof SoundEngine.shieldBlock === 'function') SoundEngine.shieldBlock();
        else SoundEngine.hit();
        this.addFloatingText('★ ปัดป้องการ์ด!', this.player.x, this.player.y - 15, '#fbbf24');
    } else {
        if (hitData.isCrit) SoundEngine.critHit(); else SoundEngine.hit();
    }

    this.player.hp = Math.max(0, this.player.hp - dmg);
    this.player.flashTimer = 180;
    this.triggerScreenShake(hitData.isCrit ? 6.5 : 4.0, 150);
    this.triggerHitstop(45);
    this.spawnParticles(this.player.x + 12, this.player.y + 14, '#ef4444', 12);
    this.addFloatingText((hitData.isCrit ? 'CRIT -' : '-') + dmg + ' (' + attackerName + ')', this.player.x, this.player.y - 18, '#ef4444');
    this.updateHpHUD();

    if (this.player.hp <= 0) {
        if (typeof (window as any).Multiplayer !== 'undefined') {
            (window as any).Multiplayer.sendPvPDefeat(hitData.attackerId, attackerName);
        }
        this.addFloatingText('★ คุณพ่ายแพ้การประลองยุทธ์! ★', this.player.x - 35, this.player.y - 25, '#f87171');
        SoundEngine.monsterDie();
        setTimeout(() => {
            if (this.player) {
                this.player.hp = this.player.maxHp || 100;
                if (this.currentScene === 'pvp_arena') {
                    this.player.x = 6 * this.tileSize;
                    this.player.y = 12 * this.tileSize;
                }
                this.updateHpHUD();
                this.addFloatingText('ฟื้นคืนชีพพร้อมสู้ต่อ!', this.player.x, this.player.y - 15, '#4ade80');
            }
        }, 1500);
    }
};

Game.openMultiplayerModal = function() {
    this.closeAllModals();
    this.activeModal = 'multiplayerModal';
    const m = document.getElementById('multiplayerModal');
    if (m) {
        m.style.display = 'flex';
        if (typeof (window as any).Multiplayer !== 'undefined') {
            (window as any).Multiplayer.updateUI();
        }
    }
};

Game.toggleMultiplayerModal = function() {
    const m = document.getElementById('multiplayerModal');
    if (m && m.style.display !== 'none') {
        this.closeAllModals();
    } else {
        this.openMultiplayerModal();
    }
};

Game.switchMpTab = function(tabName: 'host' | 'join' | 'arena') {
    const tabHost = document.getElementById('tabMpHst');
    const tabJoin = document.getElementById('tabMpJoin');
    const tabArena = document.getElementById('tabMpArena');

    const contentHost = document.getElementById('mpTabContentHost');
    const contentJoin = document.getElementById('mpTabContentJoin');
    const contentArena = document.getElementById('mpTabContentArena');

    if (tabHost) tabHost.className = 'mp-tab-btn' + (tabName === 'host' ? ' active' : '');
    if (tabJoin) tabJoin.className = 'mp-tab-btn' + (tabName === 'join' ? ' active' : '');
    if (tabArena) tabArena.className = 'mp-tab-btn' + (tabName === 'arena' ? ' active' : '');

    if (contentHost) contentHost.style.display = tabName === 'host' ? 'block' : 'none';
    if (contentJoin) contentJoin.style.display = tabName === 'join' ? 'block' : 'none';
    if (contentArena) contentArena.style.display = tabName === 'arena' ? 'block' : 'none';
};

Game.startHostingRoom = async function() {
    if (typeof (window as any).Multiplayer === 'undefined') return;
    const res = await (window as any).Multiplayer.hostRoom();
    if (res.success) {
        this.addFloatingText('★ เปิดโลกออนไลน์สำเร็จ! รหัสห้อง: ' + res.code, this.player.x - 20, this.player.y - 25, '#4ade80');
        SoundEngine.questComplete();
    }
};

Game.joinFriendRoom = async function() {
    const input = document.getElementById('mpJoinCodeInput') as HTMLInputElement;
    const status = document.getElementById('mpJoinStatus');
    if (!input) return;
    const code = input.value.trim();
    if (!code) {
        if (status) {
            status.textContent = 'กรุณากรอกรหัสห้อง 6 หลัก';
            status.style.color = '#ef4444';
        }
        return;
    }
    if (status) {
        status.textContent = 'กำลังเชื่อมต่อไปยังห้อง ' + code + '...';
        status.style.color = '#38bdf8';
    }
    if (typeof (window as any).Multiplayer === 'undefined') return;
    const res = await (window as any).Multiplayer.joinRoom(code);
    if (res.success) {
        if (status) {
            status.textContent = 'เชื่อมต่อสำเร็จ! เข้าสู่โลกของห้อง ' + code;
            status.style.color = '#4ade80';
        }
        this.addFloatingText('★ เชื่อมต่อสำเร็จ! เข้าสู่ห้อง ' + code, this.player.x - 20, this.player.y - 25, '#4ade80');
        SoundEngine.bell();
    } else {
        if (status) {
            status.textContent = res.error || 'เชื่อมต่อล้มเหลว';
            status.style.color = '#ef4444';
        }
    }
};

Game.copyRoomCode = function() {
    const code = (window as any).Multiplayer?.roomCode;
    if (!code) {
        this.addFloatingText('ยังไม่ได้เปิดห้องออนไลน์!', this.player.x, this.player.y - 15, '#f87171');
        return;
    }
    if (navigator.clipboard) {
        navigator.clipboard.writeText(code).then(() => {
            this.addFloatingText('คัดลอกรหัสห้อง ' + code + ' แล้ว!', this.player.x, this.player.y - 15, '#4ade80');
            SoundEngine.click();
        });
    } else {
        this.addFloatingText('รหัสห้องคือ: ' + code, this.player.x, this.player.y - 15, '#fde047');
    }
};

Game.sendMultiplayerChat = function() {
    const input = document.getElementById('mpChatInput') as HTMLInputElement;
    if (!input || !input.value.trim()) return;
    if (typeof (window as any).Multiplayer !== 'undefined') {
        (window as any).Multiplayer.sendChat(input.value.trim());
    }
    input.value = '';
};

Game.harvestCrop = function(tx, ty) {
    const tile = this.map[ty][tx];
    if (!tile.crop || !tile.crop.ready) return;

    const cropData = CROPS[tile.crop.cropId];
    if (!cropData) return;

    let yieldAmount = Math.floor(Math.random() * 2) + 1;
    if (this.player.skillMastery?.double_harvest && Math.random() < 0.25) {
        yieldAmount *= 2;
        this.addFloatingText(' พลังเก็บเกี่ยวคูณสอง! (Double Yield)', tx * 32, ty * 32 - 32, '#4ade80');
    }
    const quality = this.rollItemQuality('farming', this.player.skills?.farming || 1);
    this.spawnDroppedItem(tile.crop.cropId, yieldAmount, cropData.name, tx * 32 + 16, ty * 32 + 16, quality);

    let xpGained = cropData.xp * yieldAmount;
    if (this.player.houseUpgrades.persian_rug) xpGained = Math.round(xpGained * 1.15);

    this.addXp(xpGained);
    this.stats.harvests++;

    SoundEngine.harvest();
    this.triggerScreenShake(3, 100);
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#facc15', 16);
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#4ade80', 10);
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#ffffff', 6);
    this.addFloatingText(' +' + yieldAmount + ' ' + cropData.name + ' (+' + xpGained + ' XP)', tx * 32, ty * 32 - 18, '#fde047');

    tile.crop = null;
    tile.watered = false;
    this.updateHUD();
};


Game.initDroppedItems = function() {
    this.droppedItems = this.droppedItems || [];
};


Game.spawnDroppedItem = function(id: string, count = 1, arg3?: any, arg4?: any, arg5?: any, qualityArg: any = 0, isManualArg: boolean = false) {
    this.droppedItems = this.droppedItems || [];
    if (!id) return;

    let actualName = '';
    let actualX = 0;
    let actualY = 0;
    let actualQuality: 0 | 1 | 2 | 3 = 0;
    let isManualDrop = false;

    if (typeof arg3 === 'number') {
        // Called as: spawnDroppedItem(id, count, x, y, quality?, isManualDrop?)
        actualX = arg3;
        actualY = typeof arg4 === 'number' ? arg4 : (this.player ? this.player.y : 0);
        if (typeof arg5 === 'boolean') {
            isManualDrop = arg5;
            actualQuality = 0;
        } else {
            actualQuality = (typeof arg5 === 'number' ? arg5 : 0) as 0 | 1 | 2 | 3;
            if (typeof qualityArg === 'boolean') {
                isManualDrop = qualityArg;
            } else if (typeof isManualArg === 'boolean') {
                isManualDrop = isManualArg;
            }
        }
        actualName = (WORLD_ITEMS && WORLD_ITEMS[id]?.name) || (MONSTER_DROPS && MONSTER_DROPS[id]?.name) || (CROPS && CROPS[id]?.name) || (RECIPES && RECIPES[id]?.name) || (TOOLS && TOOLS[id]?.name) || (WEAPONS && WEAPONS[id]?.name) || id;
    } else {
        // Called as: spawnDroppedItem(id, count, name, x, y, quality?, isManualDrop?)
        actualName = (typeof arg3 === 'string' && arg3) ? arg3 : ((WORLD_ITEMS && WORLD_ITEMS[id]?.name) || (MONSTER_DROPS && MONSTER_DROPS[id]?.name) || (CROPS && CROPS[id]?.name) || (RECIPES && RECIPES[id]?.name) || (TOOLS && TOOLS[id]?.name) || (WEAPONS && WEAPONS[id]?.name) || id);
        actualX = typeof arg4 === 'number' ? arg4 : (this.player ? this.player.x : 0);
        actualY = typeof arg5 === 'number' ? arg5 : (this.player ? this.player.y : 0);
        if (typeof qualityArg === 'boolean') {
            isManualDrop = qualityArg;
            actualQuality = 0;
        } else {
            actualQuality = (typeof qualityArg === 'number' ? qualityArg : 0) as 0 | 1 | 2 | 3;
            isManualDrop = !!isManualArg;
        }
    }

    if (isNaN(actualX) || actualX === undefined) actualX = this.player ? this.player.x : 0;
    if (isNaN(actualY) || actualY === undefined) actualY = this.player ? this.player.y : 0;

    if (isManualDrop) {
        this.droppedItems.push({
            id: id,
            name: actualName || id,
            count: count,
            x: actualX,
            y: actualY,
            z: 6,
            vx: 0,
            vy: 0,
            vz: 2.2,
            bounces: 0,
            timer: 0,
            magnet: false,
            quality: actualQuality || 0,
            manualPickup: true
        });
        SoundEngine.itemPop();
        return;
    }

    const spawnNum = Math.min(count, 3);
    for (let i = 0; i < spawnNum; i++) {
        const eachCount = Math.max(1, Math.floor(count / spawnNum));
        const angle = Math.random() * Math.PI * 2;
        const speed = 1.2 + Math.random() * 1.8;
        this.droppedItems.push({
            id: id,
            name: actualName || id,
            count: eachCount,
            x: actualX + (Math.random() - 0.5) * 6,
            y: actualY + (Math.random() - 0.5) * 6,
            z: 8 + Math.random() * 6,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed,
            vz: 3.5 + Math.random() * 1.8,
            bounces: 0,
            timer: 0,
            magnet: false,
            quality: actualQuality || 0,
            manualPickup: false
        });
    }
    SoundEngine.itemPop();
};


Game.updateDroppedItems = function(dt) {
    if (!this.droppedItems || this.droppedItems.length === 0) return;

    for (let i = this.droppedItems.length - 1; i >= 0; i--) {
        const item = this.droppedItems[i];
        item.timer += dt;

        if (!item.magnet) {
            item.x += item.vx * (dt / 16);
            item.y += item.vy * (dt / 16);
            item.z += item.vz * (dt / 16);
            item.vz -= 0.35 * (dt / 16);

            if (item.z <= 0) {
                item.z = 0;
                item.bounces++;
                if (item.bounces <= 2) {
                    item.vz = 2.4 / item.bounces;
                    item.vx *= 0.6;
                    item.vy *= 0.6;
                } else {
                    item.vz = 0;
                    item.vx = 0;
                    item.vy = 0;
                }
            }

            // Normal drops auto-magnet to player only IF player has space in inventory. Manual drops NEVER auto-magnet (require click or pressing E!)
            if (item.timer > 250 && !item.manualPickup) {
                const distToPlayer = Math.hypot((this.player.x + 12) - item.x, (this.player.y + 16) - item.y);
                const magnetDist = (typeof this.hasRing === 'function' && this.hasRing('ring_magnet')) ? 240 : 110;
                if (distToPlayer < magnetDist) {
                    const canFit = this.canItemFitInInventory(item.id, item.count || 1, (item as any).quality || 0);
                    if (canFit) {
                        item.magnet = true;
                    }
                }
            }
        } else {
            // Check if player's inventory became full mid-flight
            const canFit = this.canItemFitInInventory(item.id, item.count || 1, (item as any).quality || 0);
            if (!canFit) {
                // Cancel magnet immediately and let it settle peacefully on the ground
                item.magnet = false;
                item.vx = 0;
                item.vy = 0;
                item.vz = 0;
                item.z = 0;
                continue;
            }

            const dx = (this.player.x + 12) - item.x;
            const dy = (this.player.y + 16) - item.y;
            const dist = Math.hypot(dx, dy);
            const pullSpeed = 9.5;

            if (dist > 15) {
                item.x += (dx / dist) * pullSpeed;
                item.y += (dy / dist) * pullSpeed;
            } else {
                const added = this.addItemToInventory(item.id, item.count, item.name, (item as any).quality || 0, true);
                if (added) {
                    SoundEngine.itemMagnetPickup();
                    this.spawnParticles(item.x, item.y, '#facc15', 6);
                    this.addFloatingText('+' + item.count + ' ' + (item.name || item.id), this.player.x, this.player.y - 18, '#38bdf8');
                    this.droppedItems.splice(i, 1);
                } else {
                    // Cannot fit in inventory: cancel magnet and let it rest on the ground
                    item.magnet = false;
                    item.vx = 0;
                    item.vy = 0;
                    item.vz = 0;
                    item.z = 0;
                }
            }
        }
    }
};


Game.findNearbyDroppedItem = function(x: number, y: number, maxDist: number = 24) {
    if (!this.droppedItems || this.droppedItems.length === 0) return null;
    let closest: any = null;
    let closestDist = maxDist;
    for (const item of this.droppedItems) {
        const d = Math.hypot(item.x - x, item.y - y);
        if (d < closestDist) {
            closestDist = d;
            closest = item;
        }
    }
    return closest;
};


Game.pickupDroppedItem = function(item: any) {
    if (!item) return false;
    const fits = this.canItemFitInInventory(item.id, item.count || 1, item.quality || 0);
    if (!fits) {
        const now = performance.now();
        if (!this._lastFullInventoryWarning || now - this._lastFullInventoryWarning > 1500) {
            this._lastFullInventoryWarning = now;
            SoundEngine.hit();
            this.addFloatingText('กระเป๋าเต็ม! จัดช่องเก็บของก่อน', this.player.x, this.player.y - 18, '#ef4444');
        }
        return false;
    }

    const added = this.addItemToInventory(item.id, item.count || 1, item.name || item.id, item.quality || 0, true);
    if (added) {
        const idx = this.droppedItems.indexOf(item);
        if (idx !== -1) {
            this.droppedItems.splice(idx, 1);
        }
        SoundEngine.itemMagnetPickup();
        this.spawnParticles(item.x, item.y, '#facc15', 10);
        this.spawnParticles(item.x, item.y, '#38bdf8', 6);
        const itName = item.name || (WORLD_ITEMS && WORLD_ITEMS[item.id]?.name) || item.id;
        this.addFloatingText(`+${item.count || 1} ${itName}`, this.player.x, this.player.y - 20, '#38bdf8');
        this.updateHUD();
        return true;
    }
    return false;
};


Game.drawDroppedItems = function() {
    if (!this.droppedItems || this.droppedItems.length === 0) return;

    const px = this.player ? this.player.x + 12 : 0;
    const py = this.player ? this.player.y + 16 : 0;

    this.droppedItems.forEach(item => {
        const sx = Math.round(item.x - this.camera.x);
        const sy = Math.round(item.y - this.camera.y);

        this.drawContactShadow(item.x, item.y, 8, 4, 0.32);

        const bob = Math.sin(performance.now() / 160 + (item.x % 10)) * 2.5;
        const drawY = sy - item.z + (item.magnet ? 0 : bob);

        // Pulsing halo for manual drops to show they are interactable on the floor
        if (item.manualPickup) {
            this.ctx.save();
            const pulse = Math.sin(performance.now() / 220) * 1.5;
            this.ctx.strokeStyle = 'rgba(250, 204, 21, 0.55)';
            this.ctx.lineWidth = 1.5;
            this.ctx.beginPath();
            this.ctx.arc(sx, drawY, 11 + pulse, 0, Math.PI * 2);
            this.ctx.stroke();
            this.ctx.restore();
        }

        const iconCanvas = SPRITES.getItemCanvas ? SPRITES.getItemCanvas(item.id) : null;
        if (iconCanvas) {
            this.ctx.drawImage(iconCanvas, sx - 9, drawY - 9, 18, 18);
        } else {
            this.ctx.fillStyle = '#facc15';
            this.ctx.beginPath();
            this.ctx.arc(sx, drawY, 5, 0, Math.PI * 2);
            this.ctx.fill();
        }

        // Draw item count badge if count > 1
        if (item.count > 1) {
            this.ctx.save();
            this.ctx.font = 'bold 9px sans-serif';
            this.ctx.fillStyle = '#0f172a';
            this.ctx.fillText(`x${item.count}`, sx + 4, drawY + 8);
            this.ctx.fillStyle = '#ffffff';
            this.ctx.fillText(`x${item.count}`, sx + 3, drawY + 7);
            this.ctx.restore();
        }

        // If player is close to item (within 48px), display sleek prompt [E] เก็บ or item name
        const distToPlayer = Math.hypot(px - item.x, py - item.y);
        if (distToPlayer <= 48 && !item.magnet) {
            this.ctx.save();
            this.ctx.font = 'bold 10px "Mitr", sans-serif';
            const itName = item.name || (WORLD_ITEMS && WORLD_ITEMS[item.id]?.name) || item.id;
            const labelText = `[E] ${itName}${item.count > 1 ? ' x' + item.count : ''}`;
            const textWidth = this.ctx.measureText(labelText).width;
            const badgeX = sx - (textWidth / 2) - 4;
            const badgeY = drawY - 17;

            this.ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
            this.ctx.beginPath();
            if (typeof this.ctx.roundRect === 'function') {
                this.ctx.roundRect(badgeX, badgeY - 11, textWidth + 8, 15, 4);
            } else {
                this.ctx.rect(badgeX, badgeY - 11, textWidth + 8, 15);
            }
            this.ctx.fill();
            this.ctx.strokeStyle = 'rgba(250, 204, 21, 0.85)';
            this.ctx.lineWidth = 1;
            this.ctx.stroke();

            this.ctx.fillStyle = '#fef08a';
            this.ctx.fillText(labelText, badgeX + 4, badgeY);
            this.ctx.restore();
        }
    });
};


Game.initAmbientCreatures = function() {
    this.ambientButterflies = [
        { x: 6 * 32, y: 7 * 32, baseAngle: 0, color: '#f43f5e' },
        { x: 16 * 32, y: 16 * 32, baseAngle: 2, color: '#38bdf8' },
        { x: 26 * 32, y: 20 * 32, baseAngle: 4, color: '#eab308' },
        { x: 9 * 32, y: 20 * 32, baseAngle: 1.5, color: '#a855f7' }
    ];
};


Game.updateAmbientCreatures = function(dt) {
    if (this.currentScene !== 'farm' || !this.ambientButterflies) return;
    this.ambientButterflies.forEach(b => {
        b.baseAngle += dt * 0.0015;
    });
};


Game.drawAmbientCreatures = function() {
    if (this.currentScene !== 'farm' || !this.ambientButterflies) return;

    this.ambientButterflies.forEach(b => {
        const bx = b.x + Math.cos(b.baseAngle) * 22;
        const by = b.y + Math.sin(b.baseAngle * 1.4) * 14;
        const sx = Math.round(bx - this.camera.x);
        const sy = Math.round(by - this.camera.y);

        if (sx < -10 || sx > this.width + 10 || sy < -10 || sy > this.height + 10) return;

        const flap = Math.sin(performance.now() / 80) * 4;
        this.ctx.save();
        this.ctx.fillStyle = b.color;
        this.ctx.beginPath();
        this.ctx.ellipse(sx - 2, sy, Math.max(1, 3 + flap), 3, 0, 0, Math.PI * 2);
        this.ctx.ellipse(sx + 2, sy, Math.max(1, 3 + flap), 3, 0, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.fillStyle = '#ffffff';
        this.ctx.fillRect(sx, sy - 1, 1, 2);
        this.ctx.restore();
    });
};


Game.drawActiveQuestTracker = function() {
    let activeQ = null;

    for (let qKey of ['q1', 'q2', 'q3', 'q4', 'q5']) {
        if (this.player.quests && this.player.quests[qKey] === 'active') {
            activeQ = QUESTS[qKey];
            break;
        }
    }
    if (!activeQ) {
        for (let qKey of ['q1', 'q2', 'q3', 'q4', 'q5']) {
            if (!this.player.quests || !this.player.quests[qKey] || this.player.quests[qKey] === 'available') {
                activeQ = QUESTS[qKey];
                break;
            }
        }
    }

    if (!activeQ) return;

    const boxW = 230;
    const boxH = 52;
    // Position to the left of the clock/actions widget (186px from right) with a clean 12px gap so they never collide!
    const boxX = this.width - 198 - boxW;
    const boxY = 10;

    this.ctx.save();
    this.ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
    this.ctx.strokeStyle = '#d97706';
    this.ctx.lineWidth = 1.5;
    this.ctx.beginPath();
    this.ctx.roundRect(boxX, boxY, boxW, boxH, 8);
    this.ctx.fill();
    this.ctx.stroke();

    this.ctx.font = 'bold 11px "Prompt", sans-serif';
    this.ctx.fillStyle = '#fde047';
    this.ctx.fillText(activeQ.title.split('(')[0].trim(), boxX + 10, boxY + 18);

    let objectiveText = '';
    let targetX = 0;
    let targetY = 0;
    let targetScene = 'village';

    if (activeQ.id === 'q1') {
        const bugs = this.player.questProgress?.bugsDefeated || 0;
        const spores = this.player.questProgress?.sporesCollected || 0;
        if (bugs < 3 || spores < 2) {
            objectiveText = `กำจัดแมลงในไร่: ${bugs}/3 ตัว (สปอร์: ${spores}/2)`;
            targetScene = 'farm';
            targetX = 16 * 32; targetY = 12 * 32;
        } else {
            objectiveText = `พบกิลเบิร์ตที่คฤหาสน์หมู่บ้าน (สำเร็จแล้ว!)`;
            targetScene = 'village';
            targetX = 12 * 32; targetY = 10 * 32;
        }
    } else if (activeQ.id === 'q2') {
        objectiveText = `ส่งสปอร์ & ดอกไม้ดวงดาว ให้หมอยาลิเลียน`;
        targetScene = 'village';
        targetX = 45 * 32; targetY = 10 * 32;
    } else if (activeQ.id === 'q3') {
        objectiveText = `ช่วยผู้กองวาเลเรีย ที่ปราการทิศเหนือ`;
        targetScene = 'village';
        targetX = 27 * 32; targetY = 4 * 32;
    } else if (activeQ.id === 'q4') {
        objectiveText = `สำรวจถ้ำผลึกคริสตัล & รายงานผู้เฒ่าเอลดริน`;
        targetScene = 'village';
        targetX = 23 * 32; targetY = 12 * 32;
    } else if (activeQ.id === 'q5') {
        objectiveText = `ปราบราชินีคาธูรอส ณ วิหารโบราณในป่า`;
        targetScene = 'forest';
        targetX = 25 * 32; targetY = 6 * 32;
    }

    this.ctx.font = '10px "Prompt", sans-serif';
    this.ctx.fillStyle = '#cbd5e1';
    this.ctx.fillText(objectiveText, boxX + 10, boxY + 36);

    let guideX = targetX;
    let guideY = targetY;

    if (this.currentScene !== targetScene) {
        if (this.currentScene === 'farm') {
            guideX = 16 * 32; guideY = 0;
        } else if (this.currentScene === 'village') {
            if (targetScene === 'farm') {
                guideX = 30 * 32; guideY = 43 * 32;
            } else if (targetScene === 'forest' || targetScene === 'cave') {
                guideX = 30 * 32; guideY = 0;
            }
        } else if (this.currentScene === 'forest') {
            if (targetScene === 'village' || targetScene === 'farm') {
                guideX = 24 * 32; guideY = 39 * 32;
            } else if (targetScene === 'cave') {
                guideX = 44 * 32; guideY = 8 * 32;
            }
        }
    }

    const angle = Math.atan2(guideY - this.player.y, guideX - this.player.x);
    const distTiles = Math.round(Math.hypot(guideX - this.player.x, guideY - this.player.y) / 32);

    const arrowCenterX = boxX + boxW - 20;
    const arrowCenterY = boxY + 34;

    this.ctx.save();
    this.ctx.translate(arrowCenterX, arrowCenterY);
    this.ctx.rotate(angle);
    this.ctx.fillStyle = '#f59e0b';
    this.ctx.beginPath();
    this.ctx.moveTo(8, 0);
    this.ctx.lineTo(-4, -5);
    this.ctx.lineTo(-2, 0);
    this.ctx.lineTo(-4, 5);
    this.ctx.closePath();
    this.ctx.fill();
    this.ctx.restore();

    this.ctx.font = 'bold 9px "Prompt", sans-serif';
    this.ctx.fillStyle = '#f59e0b';
    this.ctx.textAlign = 'right';
    this.ctx.fillText(`${distTiles}m`, boxX + boxW - 32, boxY + 37);

    this.ctx.restore();
};


Game.interact = function() {
    // 0. Check nearby dropped item to pick up with [E]!
    const nearbyDropped = this.findNearbyDroppedItem(this.player.x + 12, this.player.y + 16, 48);
    if (nearbyDropped) {
        this.pickupDroppedItem(nearbyDropped);
        return;
    }

    if (this.currentScene === 'farm') {
        const nearbyAnimal = this.animals.find(a => Math.hypot(this.player.x - a.x, this.player.y - a.y) < 50);
        if (nearbyAnimal) {
            this.petAnimal(nearbyAnimal);
            return;
        }
    } else if (this.currentScene === 'village') {
        const nearbyVillager = this.villageVillagers?.find(v => Math.hypot(this.player.x - v.x, this.player.y - v.y) < 50);
        if (nearbyVillager) {
            this.talkToVillager(nearbyVillager);
            return;
        }
    }

    const target = this.getTargetTile();
    const currTileX = Math.floor((this.player.x + 10) / this.tileSize);
    const currTileY = Math.floor((this.player.y + 20) / this.tileSize);

    // 1. Check target tile
    const targetTile = this.map[target.y]?.[target.x];
    if (targetTile && targetTile.interactable) {
        this.handleTileInteract(targetTile.interactable, target.x, target.y);
        return;
    }

    // 2. Check immediate cardinal neighbors
    const candidates = [
        this.map[currTileY - 1]?.[currTileX],
        this.map[currTileY + 1]?.[currTileX],
        this.map[currTileY]?.[currTileX - 1],
        this.map[currTileY]?.[currTileX + 1],
        this.map[currTileY]?.[currTileX]
    ];

    for (let tile of candidates) {
        if (!tile || !tile.interactable) continue;
        this.handleTileInteract(tile.interactable, tile.x, tile.y);
        return;
    }

    // 3. Check 2-tile radius for interactive furniture
    for (let dy = -2; dy <= 2; dy++) {
        for (let dx = -2; dx <= 2; dx++) {
            const t = this.map[currTileY + dy]?.[currTileX + dx];
            if (t && t.interactable && !t.interactable.startsWith('exit_') && !t.interactable.endsWith('_door')) {
                this.handleTileInteract(t.interactable, currTileX + dx, currTileY + dy);
                return;
            }
        }
    }
};


Game.handleTileInteract = function(type, tx, ty) {
    if (type === 'house_door') {
        this.switchScene('house', 12, 15);
    } else if (type === 'shop_door') {
        this.switchScene('shop', 12, 15);
    } else if (type === 'exit_house') {
        this.switchScene('farm', 5, 6);
    } else if (type === 'exit_shop') {
        this.switchScene('farm', 28, 20);
    } else if (type === 'enter_manor') {
        this.switchScene('manor', 12, 15);
    } else if (type === 'exit_manor') {
        this.switchScene('village', 9, 10);
    } else if (type === 'enter_apothecary') {
        this.switchScene('apothecary', 12, 15);
    } else if (type === 'exit_apothecary') {
        this.switchScene('village', 47, 10);
    } else if (type === 'enter_tavern') {
        this.switchScene('tavern', 12, 15);
    } else if (type === 'exit_tavern') {
        this.switchScene('village', 47, 29);
    } else if (type === 'enter_forge') {
        this.switchScene('forge', 12, 15);
    } else if (type === 'exit_forge') {
        this.switchScene('village', 9, 29);
    } else if (type === 'exit_to_village') {
        if (this.currentScene === 'farm') {
            this.switchScene('village', 30, 41);
        } else if (this.currentScene === 'forest') {
            this.switchScene('village', 30, 2);
        } else {
            this.switchScene('village', 30, 22);
        }
    } else if (type === 'exit_to_forest') {
        this.switchScene('forest', 24, 38);
    } else if (type === 'exit_to_farm') {
        this.switchScene('farm', 16, 2);
    } else if (type === 'enter_greenhouse') {
        this.switchScene('greenhouse', 8, 14);
    } else if (type === 'exit_greenhouse') {
        this.switchScene('farm', 29, 4);
    } else if (type === 'enter_farm_cave') {
        if (!this.player.farmCaveChoice) {
            this.openModal('farmCaveChoiceModal');
            return;
        }
        this.switchScene('farmCave', 7, 12);
    } else if (type === 'exit_farm_cave') {
        this.switchScene('farm', 11, 2);
    } else if (type === 'farm_cave_pedestal') {
        this.openModal('farmCaveChoiceModal');
    } else if (type === 'farm_mushroom_box') {
        this.harvestMushroomBox(tx, ty);
    } else if (type === 'cave_fruit_drop') {
        this.pickupCaveFruit(tx, ty);
    } else if (type === 'exit_pvp_arena') {
        this.switchScene('village', 30, 25);
        SoundEngine.door();
        this.addFloatingText('ออกจากลานประลองยุทธ์กลับสู่หมู่บ้าน', this.player.x, this.player.y - 15, '#94a3b8');
    } else if (type === 'pvp_bell') {
        this.player.hp = this.player.maxHp || 100;
        this.player.energy = this.player.maxEnergy || 100;
        this.updateHpHUD();
        this.updateEnergyHUD();
        SoundEngine.bell();
        this.triggerScreenShake(4.0, 150);
        this.spawnParticles(this.player.x + 12, this.player.y + 14, '#fde047', 25);
        this.addFloatingText('★ ระฆังศึกดังก้อง! ฟื้นฟู HP/Energy เต็มเปี่ยม! ★', this.player.x - 40, this.player.y - 25, '#fde047');
    } else if (type === 'sailboat_pier') {
        if (!this.player.sailboatRepaired) {
            this.openSailboatRepairModal();
        } else {
            this.travelToIsland();
        }
    } else if (type === 'exit_island_sailboat') {
        this.switchScene('village', 51, 39);
        SoundEngine.bell();
        this.addFloatingText(' ล่องเรือกลับมาถึงท่าเรือหมู่บ้านศิลาสุขาวดีอย่างปลอดภัย!', this.player.x, this.player.y - 15, '#38bdf8');
    } else if (type === 'enter_volcano') {
        this.enterIslandVolcanoDungeon();
    } else if (type === 'exit_volcano_to_island' || type === 'volcano_shortcut_exit') {
        this.exitIslandVolcanoDungeon();
    } else if (type === 'volcano_stairs_down') {
        this.proceedVolcanoNextFloor();
    } else if (type === 'volcano_switch') {
        this.activateVolcanoSwitch(tx, ty);
    } else if (type === 'mine_cinder_shard') {
        this.mineCinderShardNode(tx, ty);
    } else if (type === 'volcano_urn') {
        this.breakVolcanoUrn(tx, ty);
    } else if (type === 'drink_volcano_spring') {
        this.drinkVolcanoCoolingSpring();
    } else if (type === 'volcano_chest_5') {
        this.openVolcanoChest5();
    } else if (type === 'volcano_magma_forge') {
        this.openVolcanoForgeModal();
    } else if (type === 'forage_pineapple') {
        this.forageIslandPineapple(tx, ty);
    } else if (type === 'forage_coconut') {
        this.forageIslandCoconut(tx, ty);
    } else if (type === 'forage_banana') {
        this.forageIslandBanana(tx, ty);
    } else if (type === 'forage_seashell') {
        this.forageIslandSeashell(tx, ty);
    } else if (type === 'forage_bottle') {
        this.forageIslandMessageBottle(tx, ty);
    } else if (type === 'pirate_shipwreck') {
        this.inspectPirateShipwreck();
    } else if (type === 'pirate_chest') {
        this.openPirateChest();
    } else if (type === 'npc_pirate_captain') {
        this.openPirateShopModal();
    } else if (type === 'palm_tree') {
        this.shakePalmTree(tx, ty);
    } else if (type === 'npc_luna') {
        this.startDialogue('luna');
    } else if (type === 'collect_easter_egg') {
        this.collectEasterEgg(tx, ty);
    } else if (type === 'clinic_bed') {
        this.player.hp = this.player.maxHp;
        this.player.energy = this.player.maxEnergy;
        SoundEngine.levelUp();
        this.spawnParticles(this.player.x, this.player.y, '#ec4899', 15);
        this.addFloatingText('♥ พักผ่อนบนเตียงฟื้นฟู ฟื้นพลัง HP & พลังงานเต็ม 100%!', this.player.x, this.player.y - 20, '#ec4899');
        this.updateHUD();
    } else if (type === 'apothecary_cauldron') {
        this.openModal('craftingModal');
        this.setCraftingTab('food');
    } else if (type === 'master_anvil') {
        this.openModal('forgeModal');
    } else if (type === 'tavern_counter') {
        this.startDialogue('bob');
    } else if (type === 'tavern_bounty_board') {
        this.openBountyBoard();
    } else if (type === 'village_archives') {
        SoundEngine.bell();
        this.addFloatingText(' บันทึกโบราณ: สปอร์สีเลือดเคยระบาดเมื่อ 200 ปีก่อน และถูกสยบด้วยเซรุ่มสมุนไพร!', this.player.x, this.player.y - 20, '#38bdf8');
    } else if (type === 'mayor_desk') {
        this.startDialogue('gilbert');
    } else if (type === 'bed') {
        this.openModal('sleepModal');
    } else if (type === 'wardrobe') {
        this.openWardrobeModal();
    } else if (type === 'house_decor') {
        this.openModal('houseDecorModal');
        this.renderHouseDecorModal();
    } else if (type === 'cash_register') {
        this.openModal('shop');
    } else if (type.startsWith('shelf_')) {
        const shelfIndex = parseInt(type.split('_')[1]);
        this.openStockShelfModal(shelfIndex);
    } else if (type === 'shippingBin') {
        this.toggleModal('sell');
    } else if (type === 'mill') {
        this.toggleModal('crafting');
    } else if (type === 'well') {
        this.player.waterCan = this.player.waterCanMax;
        const prevThirst = this.player.thirst !== undefined ? this.player.thirst : 100;
        this.player.thirst = Math.min(this.player.maxThirst || 100, prevThirst + 45);
        const gainedT = Math.round(this.player.thirst - prevThirst);
        SoundEngine.water();
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#38bdf8', 12);
        this.addFloatingText(` เติมน้ำเต็มบัว & ดื่มน้ำสดชื่น (+${gainedT} น้ำ)`, this.player.x - 20, this.player.y - 15, '#38bdf8');
        this.updateHUD();
    } else if (type === 'hunter_post') {
        this.openModal('hunterModal');
    } else if (type === 'berry_bush') {
        SoundEngine.harvest();
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#ec4899', 12);
        this.spawnDroppedItem('wild_berries', 2, this.player.x, this.player.y - 10);
        this.player.energy = Math.min(this.player.maxEnergy, this.player.energy + 15);
        this.addXp(12);
        this.addFloatingText('★ เก็บเบอร์รี่ป่าสดใหม่ (+15 พลังงาน, +12 XP)', this.player.x - 20, this.player.y - 15, '#f472b6');
        this.updateHUD();
    } else if (type === 'bench') {
        SoundEngine.bell();
        this.player.energy = Math.min(this.player.maxEnergy, this.player.energy + 8);
        this.addFloatingText('★ นั่งพักผ่อนริมน้ำชิลล์ๆ (+8 พลังงาน)', this.player.x - 15, this.player.y - 15, '#60a5fa');
        this.updateHUD();
    } else if (type === 'npc_gilbert') {
        this.startDialogue('gilbert');
    } else if (type === 'npc_lilian') {
        this.startDialogue('lilian');
    } else if (type === 'npc_bob') {
        this.startDialogue('bob');
    } else if (type === 'npc_valeria') {
        this.startDialogue('valeria');
    } else if (type === 'npc_eldrin') {
        this.startDialogue('eldrin');
    } else if (type === 'npc_kael') {
        this.startDialogue('kael');
    } else if (type === 'village_fountain') {
        this.player.waterCan = this.player.waterCanMax;
        const prevThirst = this.player.thirst !== undefined ? this.player.thirst : 100;
        this.player.thirst = Math.min(this.player.maxThirst || 100, prevThirst + 45);
        const gainedT = Math.round(this.player.thirst - prevThirst);
        SoundEngine.water();
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#38bdf8', 12);
        this.addFloatingText(` ดื่มน้ำพุกลางหมู่บ้านชื่นใจ (+${gainedT} น้ำ)`, this.player.x - 20, this.player.y - 15, '#38bdf8');
        this.updateHUD();
    } else if (type === 'barricade') {
        this.addFloatingText(' แนวกระสอบทรายและรั้วขวาก ป้องกันแมลงยักษ์จากป่าทึบ', this.player.x, this.player.y - 15, '#f87171');
    } else if (type === 'street_lamp') {
        this.addFloatingText(' เสาโคมไฟโบราณ ส่องสว่างทั่วหมู่บ้านยามค่ำคืน', this.player.x, this.player.y - 15, '#fef08a');
    } else if (type === 'campfire') {
        this.openCampModal();
    } else if (type === 'ruby_node') {
        SoundEngine.miningHit();
        this.triggerScreenShake(3.5, 120);
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#ef4444', 12);
        this.spawnDroppedItem('ruby_gem', 1, this.player.x, this.player.y - 12);
        this.spawnDroppedItem('iron_ore', 1, this.player.x, this.player.y - 12);
        this.addXp(20);
        this.player.questProgress.rubiesMined = (this.player.questProgress.rubiesMined || 0) + 1;
        this.addFloatingText(' ขุดได้ อัญมณีทับทิมเวทมนตร์ + แร่เหล็ก (+20 XP)', this.player.x - 20, this.player.y - 15, '#f87171');
        // Check quest 2 objective
        const hasHerbs = this.countItemInInventory('starflower_herb');
        const hasRubies = this.countItemInInventory('ruby_gem');
        if (this.player.quests.q2 === 'active' && hasHerbs >= 3 && hasRubies >= 2) {
            this.addFloatingText('★ ภารกิจที่ 2 สำเร็จ! นำของไปส่งที่ อัศวินสาว วาเลเรีย', this.player.x - 30, this.player.y - 30, '#4ade80');
        }
        this.updateHUD();
    } else if (type === 'starflower_node') {
        SoundEngine.harvest();
        this.triggerScreenShake(2.0, 80);
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#38bdf8', 8);
        this.spawnDroppedItem('starflower_herb', 1, this.player.x, this.player.y - 10);
        this.addXp(10);
        this.addFloatingText('★ เก็บสมุนไพรดวงดาว (+10 XP)', this.player.x - 10, this.player.y - 15, '#38bdf8');
        // Check quest 2 objective
        const hasHerbs = this.countItemInInventory('starflower_herb');
        const hasRubies = this.countItemInInventory('ruby_gem');
        if (this.player.quests.q2 === 'active' && hasHerbs >= 3 && hasRubies >= 2) {
            this.addFloatingText('★ ภารกิจที่ 2 สำเร็จ! นำของไปส่งที่ อัศวินสาว วาเลเรีย', this.player.x - 30, this.player.y - 30, '#4ade80');
        }
        this.updateHUD();
    } else if (type === 'starfruit_node') {
        SoundEngine.harvest();
        this.triggerScreenShake(2.0, 80);
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#facc15', 12);
        this.spawnDroppedItem('star_fruit', 1, this.player.x, this.player.y - 10);
        this.addXp(18);
        this.addFloatingText('★ เก็บผลไม้ดวงดาราพฤกษา (+18 XP)', this.player.x - 10, this.player.y - 15, '#facc15');
        this.updateHUD();
    } else if (type === 'thunder_crystal_node') {
        SoundEngine.miningHit();
        this.triggerScreenShake(2.5, 90);
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#38bdf8', 14);
        this.spawnDroppedItem('thunder_crystal', 1, this.player.x, this.player.y - 10);
        this.addXp(22);
        this.addFloatingText('★ สกัดผลึกสายฟ้าอัสนีบาต (+22 XP)', this.player.x - 10, this.player.y - 15, '#38bdf8');
        this.updateHUD();
    } else if (type === 'cave_entrance') {
        this.warpCaveFloor(1);
    } else if (type === 'exit_cave') {
        this.switchScene('forest', 44, 9);
    } else if (type === 'cave_ladder_down') {
        this.descendCaveFloor();
    } else if (type === 'exit_to_cave_depths') {
        this.switchScene('cave_depths', 22, 30);
    } else if (type === 'exit_cave_depths_to_cave') {
        this.switchScene('cave', 21, 30);
    } else if (type === 'cave_ladder_up') {
        this.ascendCaveFloor();
    } else if (type === 'cave_elevator') {
        this.openMineElevatorModal();
    } else if (type === 'breakable_rock') {
        SoundEngine.miningHit();
        this.triggerScreenShake(3.0, 100);
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#94a3b8', 14);

        const targetX = tx !== undefined ? tx : Math.floor((this.player.x + 10) / this.tileSize);
        const targetY = ty !== undefined ? ty : Math.floor((this.player.y + 20) / this.tileSize);
        const t = this.map[targetY]?.[targetX];

        this.addItemToInventory('stone', 1 + Math.floor(Math.random() * 2), 'ก้อนหินธรรมชาติ');
        if (Math.random() < 0.35) this.addItemToInventory('copper_ore', 1, 'แร่ทองแดงดิบ');
        else if (Math.random() < 0.20) this.addItemToInventory('coal', 1, 'ก้อนถ่านหิน');

        if (t && t.hasLadderDown) {
            t.type = 'caveLadderDown';
            t.solid = false;
            t.interactable = 'cave_ladder_down';
            SoundEngine.levelUp();
            this.addFloatingText(' พบทางลงสู่ชั้นถัดไป! (กด E หรือคลิกเพื่อลง)', this.player.x - 20, this.player.y - 15, '#67e8f9');
        } else if (t) {
            t.type = 'caveFloor';
            t.solid = false;
            t.interactable = null;
            this.addFloatingText(' ทุบหินแตก! ได้ก้อนหิน', this.player.x - 10, this.player.y - 15, '#cbd5e1');
        }
        this.unlockCompendiumItem('stone');
        this.updateHUD();
    } else if (type.startsWith('machine_')) {
        this.interactWithMachine(type);
    } else if (type.startsWith('cave_milestone_chest_')) {
        if (this.chests[type]) {
            this.addFloatingText('หีบนี้ถูกเปิดไปแล้ว', this.player.x, this.player.y - 10, '#94a3b8');
            return;
        }
        this.chests[type] = true;
        SoundEngine.chestOpen();
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#facc15', 25);
        const fNum = parseInt(type.replace('cave_milestone_chest_f', '')) || 5;
        const rewardGold = fNum * 150;
        this.player.gold += rewardGold;
        this.addItemToInventory('star_core', 1, 'แก่นพลังดวงดาว');
        this.addItemToInventory('diamond_crystal', 2, 'เพชรผลึกดวงดาว');
        this.addFloatingText(` เปิดหีบสมบัติชั้น ${fNum}! +${rewardGold} G และแก่นพลังดวงดาว!`, this.player.x - 35, this.player.y - 20, '#fde047');
        this.unlockCompendiumItem('star_core');
        this.unlockCompendiumItem('diamond_crystal');
        this.updateHUD();
    } else if (type === 'gold_node') {
        SoundEngine.miningHit();
        this.triggerScreenShake(3.5, 120);
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#facc15', 12);
        this.spawnDroppedItem('gold_ore', 2, this.player.x, this.player.y - 12);
        this.spawnDroppedItem('iron_ore', 1, this.player.x, this.player.y - 12);
        this.addXp(25);
        this.addFloatingText(' ขุดได้ แร่ทองคำบริสุทธิ์ x2 (+25 XP)', this.player.x - 20, this.player.y - 15, '#fde047');
        this.updateHUD();
    } else if (type === 'mana_node') {
        SoundEngine.miningHit();
        this.triggerScreenShake(3.5, 120);
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#38bdf8', 14);
        this.spawnDroppedItem('mana_gem', 2, this.player.x, this.player.y - 12);
        this.addXp(25);
        this.addFloatingText(' ขุดได้ ผลึกมานาสีคราม x2 (+25 XP)', this.player.x - 20, this.player.y - 15, '#38bdf8');
        this.updateHUD();
    } else if (type === 'diamond_node') {
        SoundEngine.miningHit();
        this.triggerScreenShake(4.5, 150);
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#c084fc', 16);
        this.spawnDroppedItem('diamond_crystal', 1, this.player.x, this.player.y - 12);
        this.spawnDroppedItem('gold_ore', 1, this.player.x, this.player.y - 12);
        this.addXp(40);
        this.addFloatingText(' ขุดพบ เพชรผลึกดวงดาว ล้ำค่า! (+40 XP)', this.player.x - 25, this.player.y - 15, '#e879f9');
        this.updateHUD();
    } else if (type.startsWith('cave_chest_')) {
        if (this.chests[type]) {
            this.addFloatingText('หีบผลึกนี้ถูกเปิดไปแล้ว', this.player.x, this.player.y - 10, '#94a3b8');
            return;
        }
        this.chests[type] = true;
        SoundEngine.chestOpen();
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#38bdf8', 25);
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#facc15', 20);
        const goldBonus = 400;
        this.player.gold += goldBonus;
        this.addItemToInventory('diamond_crystal', 1, 'เพชรผลึกดวงดาว');
        this.addItemToInventory('gold_ore', 3, 'แร่ทองคำบริสุทธิ์');
        this.addItemToInventory('mana_gem', 2, 'ผลึกมานาสีคราม');
        this.addXp(80);
        this.addFloatingText(' เปิดหีบสมบัติถ้ำผลึก! +' + goldBonus + ' G และเพชรล้ำค่า (+80 XP)', this.player.x - 35, this.player.y - 20, '#67e8f9');
        this.updateHUD();
    } else if (type.startsWith('dungeon_chest_') || (type.startsWith('chest_') && this.isCombatScene())) {
        this.openDungeonChest(type, tx, ty);
    } else if (type === 'breakable_pot' || type === 'breakable_crate') {
        this.breakDungeonObject(tx, ty, type);
    } else if (type.startsWith('placed_chest_')) {
        this.openStorageChest(type);
    } else if (type.startsWith('sprinkler_')) {
        const held = this.player.inventory[this.player.selectedSlot];
        if (held && (held.id === 'axe' || held.id === 'pickaxe')) {
            const tile = this.map[ty]?.[tx];
            const spType = (tile && tile.type === 'sprinkler_quality') ? 'sprinkler_quality' : 'sprinkler_basic';
            this.placedSprinklers = (this.placedSprinklers || []).filter((sp: any) => !(sp.x === tx && sp.y === ty && sp.scene === this.currentScene));
            if (tile) {
                tile.type = (this.currentScene === 'farm' ? 'soil' : 'grass');
                tile.solid = false;
                tile.interactable = null;
            }
            this.spawnDroppedItem(spType, 1, tx * 32 + 16, ty * 32 + 16);
            SoundEngine.chopWood();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#38bdf8', 12);
            this.addFloatingText('รื้อถอนสปริงเกอร์สำเร็จ!', tx * 32, ty * 32 - 12, '#38bdf8');
            this.updateHUD();
        } else {
            SoundEngine.bell();
            this.addFloatingText('สปริงเกอร์รดน้ำอัตโนมัติ (ใช้ขวานหรืออีเต๋อเพื่อรื้อถอน)', tx * 32, ty * 32 - 12, '#38bdf8');
        }
    } else if (type.startsWith('farm_lantern')) {
        SoundEngine.bell();
        this.addFloatingText('โคมไฟฟาร์ม: ส่องสว่างยามราตรีรอบฟาร์ม', this.player.x, this.player.y - 15, '#fef08a');
    } else if (type.startsWith('windmill_interact')) {
        const wheatCount = this.countItemInInventory('wheat');
        const sugarCaneCount = this.countItemInInventory('sugarcane');
        if (wheatCount >= 1) {
            this.removeItemFromInventory('wheat', 1);
            this.addItemToInventory('wheat_flour', 2, 'แป้งสาลีเนื้อละเอียด');
            SoundEngine.craft();
            this.spawnParticles(this.player.x + 10, this.player.y + 10, '#fef08a', 14);
            this.addFloatingText('กังหันลมโม่ข้าวสาลี! ได้รับ แป้งสาลี x2', this.player.x - 20, this.player.y - 18, '#fde047');
            this.updateHUD();
        } else if (sugarCaneCount >= 1) {
            this.removeItemFromInventory('sugarcane', 1);
            this.addItemToInventory('sugar', 2, 'น้ำตาลทรายบริสุทธิ์');
            SoundEngine.craft();
            this.spawnParticles(this.player.x + 10, this.player.y + 10, '#ffffff', 14);
            this.addFloatingText('กังหันลมโม่ลำต้นอ้อย! ได้รับ น้ำตาล x2', this.player.x - 20, this.player.y - 18, '#ffffff');
            this.updateHUD();
        } else {
            SoundEngine.bell();
            this.addFloatingText('กังหันลมโม่แป้ง: ต้องมีข้าวสาลีหรืออ้อยในกระเป๋าเพื่อโม่', this.player.x - 30, this.player.y - 15, '#fde047');
        }
    } else if (type.startsWith('silo_interact')) {
        SoundEngine.bell();
        this.addFloatingText('ไซโลเสบียงฟาร์ม: จ่ายหญ้าแห้งให้อาหารสัตว์เลี้ยงทุกเช้าอัตโนมัติ', this.player.x - 30, this.player.y - 15, '#fde047');
    } else if (type.startsWith('fish_tank_interact')) {
        SoundEngine.water();
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#38bdf8', 10);
        this.addFloatingText('ตู้ปลาสวยงาม: ชมฝูงปลาแหวกว่ายอย่างสงบสุขและเพลิดเพลิน', this.player.x - 25, this.player.y - 15, '#38bdf8');
    } else if (type === 'sacred_shrine_altar') {
        this.interactWithShrineAltar();
    } else if (type === 'spire_portal') {
        SoundEngine.spirePortal();
        this.generateSpireMap(1);
    } else if (type === 'spire_next_floor') {
        SoundEngine.spirePortal();
        this.generateSpireMap((this.spireCurrentFloor || 1) + 1);
    } else if (type === 'exit_spire_to_village') {
        SoundEngine.spirePortal();
        this.switchScene('village', 37, 12);
        this.addFloatingText('ก้าวออกจากหอคอยมิติ กลับสู่หมู่บ้านศิลาสุขาวดี', this.player.x - 20, this.player.y - 15, '#38bdf8');
    } else if (type === 'spire_shop_relic') {
        this.openSpireShopModal();
    }
};


Game.openDungeonChest = function(chestId: string, tx: number, ty: number) {
    if (!this.player.openedDungeonChests) this.player.openedDungeonChests = {};
    if (this.player.openedDungeonChests[chestId]) {
        this.addFloatingText('หีบสมบัตินี้ถูกเปิดและรับรางวัลไปแล้ว!', this.player.x, this.player.y - 15, '#94a3b8');
        return;
    }

    this.player.openedDungeonChests[chestId] = true;
    if (SoundEngine.chestOpen) SoundEngine.chestOpen();
    this.triggerScreenShake(4.5, 180);
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#facc15', 30);
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#38bdf8', 20);

    const goldReward = 500 + Math.floor(Math.random() * 800);
    this.player.gold += goldReward;
    this.addXp(300);

    const ringPool = ['ring_glow', 'ring_magnet', 'ring_warrior', 'ring_vampiric', 'ring_lucky', 'diamond_crystal', 'ruby_gem'];
    const chosenItem = ringPool[Math.floor(Math.random() * ringPool.length)];
    const itemName = WORLD_ITEMS[chosenItem]?.name || chosenItem;
    this.addItemToInventory(chosenItem, 1, itemName);

    this.addFloatingText(` สมบัติโบราณ! +${goldReward} G & ${itemName}!`, this.player.x - 30, this.player.y - 30, '#fde047');
    this.updateHUD();
};


Game.breakDungeonObject = function(tx: number, ty: number, type: string) {
    if (!this.map[ty] || !this.map[ty][tx]) return;
    const tile = this.map[ty][tx];

    const baseFloor = this.currentScene === 'crypt' ? 'cryptFloor' :
                      this.currentScene === 'volcano' ? 'magmaFloor' :
                      this.currentScene === 'frost_peak' ? 'snowFloor' :
                      this.currentScene === 'swamp' ? 'swampFloor' : 'caveFloor';
    tile.type = baseFloor;
    tile.solid = false;
    tile.interactable = null;

    if (SoundEngine.potBreak) SoundEngine.potBreak();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, type === 'breakable_pot' ? '#b45309' : '#78350f', 16);

    const roll = Math.random();
    if (roll < 0.40) {
        const heal = 25;
        this.player.hp = Math.min(this.player.maxHp, this.player.hp + heal);
        this.addFloatingText('♥ +' + heal + ' HP', tx * 32, ty * 32 - 12, '#4ade80');
        this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#ef4444', 8);
    } else if (roll < 0.75) {
        const g = 35 + Math.floor(Math.random() * 65);
        this.player.gold += g;
        this.addFloatingText(' +' + g + ' G', tx * 32, ty * 32 - 12, '#facc15');
    } else {
        const drops = ['health_potion', 'ruby_gem', 'bat_wing', 'antidote_serum'];
        const dId = drops[Math.floor(Math.random() * drops.length)];
        this.spawnDroppedItem(dId, 1, WORLD_ITEMS[dId]?.name || dId, tx * 32 + 16, ty * 32 + 16);
    }
    this.updateHUD();
};


Game.checkBreakablesInArea = function(hitX: number, hitY: number, radius: number = 32): boolean {
    if (!this.map) return false;
    const centerTx = Math.floor(hitX / 32);
    const centerTy = Math.floor(hitY / 32);
    let brokeAny = false;

    for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) {
            const tx = centerTx + dx;
            const ty = centerTy + dy;
            if (this.map[ty] && this.map[ty][tx]) {
                const t = this.map[ty][tx];
                if (t.type === 'breakable_pot' || t.type === 'breakable_crate') {
                    const cx = tx * 32 + 16;
                    const cy = ty * 32 + 16;
                    if (Math.hypot(cx - hitX, cy - hitY) <= radius + 14) {
                        this.breakDungeonObject(tx, ty, t.type);
                        brokeAny = true;
                    }
                }
            }
        }
    }
    return brokeAny;
};


// ========================================================
// 7. TIME, CALENDAR & SLEEP
// ========================================================

Game.updateTime = function(dt) {
    if (this.activeModal) return;

    this.time.timer += dt;
    // 3200ms per 10 in-game minutes (~5.8 minutes per full day)
    if (this.time.timer >= 3200) {
        this.time.timer = 0;
        this.time.minute += 10;

        // Gradual Hunger & Thirst Depletion over time
        this.player.hunger = Math.max(0, (this.player.hunger !== undefined ? this.player.hunger : 100) - 0.25);
        this.player.thirst = Math.max(0, (this.player.thirst !== undefined ? this.player.thirst : 100) - 0.40);

        // Starvation and Dehydration HP Penalty
        if (this.player.hunger <= 0 || this.player.thirst <= 0) {
            this.starvationTimer = (this.starvationTimer || 0) + 1;
            if (this.starvationTimer >= 3) { // every 30 in-game mins
                this.starvationTimer = 0;
                this.player.hp = Math.max(1, this.player.hp - 1);
                if (this.player.hunger <= 0 && this.player.thirst <= 0) {
                    this.addFloatingText(' หิวและกระหายน้ำรุนแรง! (-1 HP)', this.player.x - 20, this.player.y - 15, '#ef4444');
                } else if (this.player.hunger <= 0) {
                    this.addFloatingText(' หิวจนแสบท้อง! (-1 HP)', this.player.x - 20, this.player.y - 15, '#f97316');
                } else {
                    this.addFloatingText(' คอแห้งกระหายน้ำ! (-1 HP)', this.player.x - 20, this.player.y - 15, '#06b6d4');
                }
            }
        } else {
            this.starvationTimer = 0;
        }

        // Passive tea table regen in house
        if (this.currentScene === 'house' && this.player.houseUpgrades.tea_table) {
            this.player.energy = Math.min(this.player.maxEnergy, this.player.energy + 1);
        }
        this.updateHUD();

        // Ambient natural soundscape (Stardew birds & night crickets)
        if (this.currentScene === 'farm' || this.currentScene === 'forest') {
            this.ambientSoundTimer = (this.ambientSoundTimer || 0) + 1;
            if (this.ambientSoundTimer >= 15) {
                this.ambientSoundTimer = 0;
                if (this.time.hour >= 6 && this.time.hour < 18) {
                    SoundEngine.birdChirp();
                } else {
                    SoundEngine.cricket();
                }
            }
        }

        if (this.time.minute >= 60) {
            this.time.minute = 0;
            this.time.hour += 1;
            // Roll past 24:00 seamlessly into midnight & late night (00:00 -> 05:00)
            if (this.time.hour >= 24) {
                this.time.hour = 0;
            }
            if (this.time.hour === 6) {
                // Natural morning transition if stayed awake through the night
                this.time.day += 1;
                if (this.time.day > DAYS_PER_SEASON) {
                    this.time.day = 1;
                    this.time.seasonIndex = (this.time.seasonIndex + 1) % SEASONS.length;
                }
                // Daily Boss Respawn System (มหาบอสฟื้นคืนชีพทุก 1 วันในเกม)
                if (this.player.defeatedBosses && Object.keys(this.player.defeatedBosses).length > 0) {
                    this.player.defeatedBosses = {};
                    this.player.bossDefeatDay = {};
                    this.addFloatingText('★ มหาบอสทุกตัวฟื้นคืนชีพในเช้าวันใหม่แล้ว!', this.player.x, this.player.y - 45, '#ef4444');
                }
                this.checkFestivalBanner();
                SoundEngine.birdChirp();
                this.addFloatingText(' ยามเช้าวันใหม่มาถึงแล้ว!', this.player.x, this.player.y - 15, '#fde047');
            }
            SoundEngine.setNightTime(this.time.hour < 6 || this.time.hour >= 19);
            this.updateClockHUD();
        }
    }
};


Game.sleepAndPassDay = function(forceWarpToBed = false) {
    this.closeAllModals();

    const wasInsideHouse = (this.currentScene === 'house');

    this.time.day += 1;
    this.time.hour = 6;
    this.time.minute = 0;
    SoundEngine.setNightTime(false);
    if (this.player.pet) (this.player.pet as any).dailyGiftGiven = false;

    if (this.time.day > DAYS_PER_SEASON) {
        this.time.day = 1;
        this.time.seasonIndex = (this.time.seasonIndex + 1) % SEASONS.length;
    }

    // Daily Boss Respawn System (มหาบอสฟื้นคืนชีพทุก 1 วันในเกม)
    if (this.player.defeatedBosses && Object.keys(this.player.defeatedBosses).length > 0) {
        this.player.defeatedBosses = {};
        this.player.bossDefeatDay = {};
        this.addFloatingText('★ มหาบอสทุกตัวฟื้นคืนชีพในเช้าวันใหม่แล้ว!', this.player.x, this.player.y - 45, '#ef4444');
    }

    //  Season-specific Weather System
    const seasonIdx = this.time.seasonIndex;
    const r = Math.random();
    if (seasonIdx === 3) {
        // Winter: 45% snow, 15% rain, 40% sun
        if (r < 0.45) this.time.weather = 'snow';
        else if (r < 0.60) this.time.weather = 'rain';
        else this.time.weather = 'sun';
    } else if (seasonIdx === 0) {
        // Spring: 30% rain, 10% thunder, 60% sun
        if (r < 0.30) this.time.weather = 'rain';
        else if (r < 0.40) this.time.weather = 'thunder';
        else this.time.weather = 'sun';
    } else if (seasonIdx === 1) {
        // Summer: 20% rain, 15% thunder, 65% sun
        if (r < 0.20) this.time.weather = 'rain';
        else if (r < 0.35) this.time.weather = 'thunder';
        else this.time.weather = 'sun';
    } else {
        // Fall: 35% rain, 15% thunder, 50% sun
        if (r < 0.35) this.time.weather = 'rain';
        else if (r < 0.50) this.time.weather = 'thunder';
        else this.time.weather = 'sun';
    }

    const isWetWeather = (this.time.weather === 'rain' || this.time.weather === 'thunder');

    // Energy recovery (Deluxe bed bonus!)
    const maxBonus = this.player.houseUpgrades.bed_deluxe ? 130 : 100;
    this.player.maxEnergy = maxBonus;
    this.player.energy = this.player.maxEnergy;
    this.player.waterCan = this.player.waterCanMax;

    // Morning hunger and thirst (wake up wanting fresh breakfast & water)
    this.player.hunger = Math.max(25, (this.player.hunger !== undefined ? this.player.hunger : 100) - 20);
    this.player.thirst = Math.max(20, (this.player.thirst !== undefined ? this.player.thirst : 100) - 25);

    // Wake up: Only warp to house bed if player intentionally clicked bed in the house!
    const shouldWarpToBed = forceWarpToBed && wasInsideHouse;
    if (shouldWarpToBed) {
        this.switchScene('house', 19, 5);
        this.addFloatingText(' ตื่นนอนบนเตียงในบ้านแสนอบอุ่น! (พลังงานเต็ม 100%)', this.player.x, this.player.y - 20, '#fde047');
    } else {
        SoundEngine.bell();
        this.addFloatingText(' เช้าวันใหม่! ตื่นจากการตั้งแคมป์พร้อมลุยสำรวจต่อ!', this.player.x - 30, this.player.y - 25, '#38bdf8');
    }

    //  Sprinkler Automation: Water surrounding tiles on farm every morning
    const farmMap = this.scenes.farm.map;
    if (this.placedSprinklers && this.placedSprinklers.length > 0) {
        let spCount = 0;
        this.placedSprinklers.forEach((sp: any) => {
            if (sp.scene !== 'farm') return;
            const offsets = sp.type === 'sprinkler_quality'
                ? [[-1,-1], [-1,0], [-1,1], [0,-1], [0,1], [1,-1], [1,0], [1,1]]
                : [[-1,0], [1,0], [0,-1], [0,1]];
            offsets.forEach(([dx, dy]) => {
                const nx = sp.x + dx;
                const ny = sp.y + dy;
                if (ny >= 0 && ny < this.scenes.farm.mapHeight && nx >= 0 && nx < this.scenes.farm.mapWidth) {
                    const t = farmMap[ny][nx];
                    if (t.tilled) {
                        t.watered = true;
                        spCount++;
                    }
                }
            });
        });
        if (spCount > 0) {
            this.addFloatingText(` สปริงเกอร์รดน้ำแปลงผักอัตโนมัติ ${spCount} ช่อง!`, 19 * 32, 5 * 32 - 15, '#38bdf8');
        }
    }

    //  Pet Morning Greeting & Gift
    if (this.player.pet && Math.random() < 0.6) {
        const petGifts = ['seed_strawberry', 'seed_pumpkin', 'stone', 'copper_ore', 'wheat_seed'];
        const pGift = petGifts[Math.floor(Math.random() * petGifts.length)];
        this.addItemToInventory(pGift, 1);
        const pName = WORLD_ITEMS[pGift]?.name || pGift;
        this.addFloatingText(` ${this.player.pet.name} นำของขวัญมาให้! (${pName})`, 19 * 32, 5 * 32 - 32, '#f472b6');
    }

    // Overnight crop growth on farm & Auto-Watering on wet days
    for (let y = 0; y < this.scenes.farm.mapHeight; y++) {
        for (let x = 0; x < this.scenes.farm.mapWidth; x++) {
            const tile = farmMap[y][x];
            if (isWetWeather && tile.tilled) tile.watered = true;

            if (tile.crop) {
                if (tile.watered) {
                    tile.crop.daysGrown += 1;
                    const cropInfo = CROPS[tile.crop.cropId];
                    if (cropInfo) {
                        const step = cropInfo.growDays / 3;
                        tile.crop.stage = Math.min(3, Math.floor(tile.crop.daysGrown / step));
                        if (tile.crop.stage >= 3) tile.crop.ready = true;
                    }
                }
                tile.watered = isWetWeather;
            } else if (tile.tilled && !isWetWeather) {
                tile.watered = false;
            }
        }
    }

    this.animals.forEach(a => { a.pettedToday = false; a.hasProduct = true; });
    const hasSilo = (this.placedStructures || []).some((s: any) => s.type === 'silo');
    if (hasSilo && this.animals.length > 0) {
        this.animals.forEach(a => {
            (a as any).fed = true;
            (a as any).happiness = Math.min(100, ((a as any).happiness || 80) + 10);
        });
        this.addFloatingText('ไซโลเสบียงฟาร์มจ่ายหญ้าแห้งอัตโนมัติ! สัตว์ทุกตัวอิ่มท้องและอารมณ์ดี', 19 * 32, 5 * 32 - 15, '#fde047');
    }

    //  Greenhouse Year-Round Crop Growth
    if (this.scenes?.greenhouse?.map) {
        const ghMap = this.scenes.greenhouse.map;
        for (let gy = 0; gy < this.scenes.greenhouse.mapHeight; gy++) {
            for (let gx = 0; gx < this.scenes.greenhouse.mapWidth; gx++) {
                const t = ghMap[gy][gx];
                if (t.crop) {
                    t.crop.daysGrown += 1;
                    const cropInfo = CROPS[t.crop.cropId];
                    if (cropInfo) {
                        const step = cropInfo.growDays / 3;
                        t.crop.stage = Math.min(3, Math.floor(t.crop.daysGrown / step));
                        if (t.crop.stage >= 3) t.crop.ready = true;
                    }
                }
            }
        }
    }

    // ♥ Spouse Morning Care & Daily Reset
    this.player.spouseKissedToday = false;
    if (this.player.spouse) {
        const spouseName = NPC_STORY[this.player.spouse]?.name || 'คู่ชีวิต';
        if (Math.random() < 0.40) {
            // Spouse waters all tilled farm crops!
            let wateredCount = 0;
            for (let fy = 0; fy < this.scenes.farm.mapHeight; fy++) {
                for (let fx = 0; fx < this.scenes.farm.mapWidth; fx++) {
                    const ft = farmMap[fy][fx];
                    if (ft.tilled) {
                        ft.watered = true;
                        wateredCount++;
                    }
                }
            }
            this.addFloatingText(`♥ ${spouseName}: "อรุณสวัสดิ์จ้ะที่รัก! ข้าช่วยรดน้ำแปลงผักให้เจ้าทั้งฟาร์มแล้วนะ!"`, 19 * 32, 5 * 32 - 32, '#ec4899');
        } else {
            // Spouse cooks fresh hearty breakfast!
            const breakfasts = ['spicy_fish_soup', 'pizza', 'bread', 'cake'];
            const bItem = breakfasts[Math.floor(Math.random() * breakfasts.length)];
            this.addItemToInventory(bItem, 1);
            this.addFloatingText(`♥ ${spouseName}: "ตื่นแล้วหรือจ๊ะที่รัก? ข้าเตรียมอาหารเช้าแสนอร่อยไว้ให้แล้วนะ!"`, 19 * 32, 5 * 32 - 32, '#f472b6');
        }
    }

    //  Farm Cave: Fruit Bats Nightly Drops
    if (this.player.farmCaveChoice === 'bats' && this.scenes?.farmCave?.map) {
        const caveMap = this.scenes.farmCave.map;
        const emptyPoints = [{ x: 4, y: 4 }, { x: 10, y: 4 }, { x: 5, y: 7 }, { x: 9, y: 8 }, { x: 7, y: 5 }];
        emptyPoints.forEach(p => {
            if (caveMap[p.y] && caveMap[p.y][p.x] && !caveMap[p.y][p.x].solid && Math.random() < 0.6) {
                caveMap[p.y][p.x].type = 'caveFruitDrop';
                caveMap[p.y][p.x].interactable = 'cave_fruit_drop';
            }
        });
    }

    //  Check Seasonal Village Festival
    this.checkFestivalBanner();

    SoundEngine.levelUp();
    this.addFloatingText('เช้าวันใหม่! พลังงานเต็ม 100% (' + this.player.maxEnergy + ')', this.player.x, this.player.y - 20, '#fde047');
    if (isWetWeather) {
        this.addFloatingText(' ฝนตกรดน้ำแปลงผักให้ทั้งฟาร์ม!', this.player.x, this.player.y - 35, '#38bdf8');
    }
    this.updateHUD();

    // Auto-save on day sleep!
    if (typeof Auth !== 'undefined' && typeof Auth.saveGame === 'function') {
        Auth.saveGame(null, true);
    }
};

Game.openCampModal = function() {
    const sceneNames: Record<string, string> = {
        farm: 'ฟาร์มสุขใจ (Farm)',
        village: 'หมู่บ้านศิลาสุขาวดี (Village)',
        forest: 'ป่าทมิฬลึกลับ (Forest)',
        cave: 'เหมืองถ้ำโบราณ (Cave)',
        volcano: 'ดันเจี้ยนภูเขาไฟลาวา (Volcano)',
        island: 'เกาะเขตร้อนแคริบเบียน (Tropical Island)',
        house: 'บ้านพักชาวสวน (Farmhouse)',
        greenhouse: 'โรงเรือนปลูกผัก (Greenhouse)',
        farmCave: 'ถ้ำฟาร์ม (Farm Cave)'
    };
    const locName = sceneNames[this.currentScene] || this.currentScene;
    const locEl = document.getElementById('campCurrentLocationName');
    if (locEl) locEl.textContent = locName;

    this.openModal('campModal');
};

Game.campOut = function() {
    this.closeModal('campModal');

    // Campfire smoke & spark particles
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#f97316', 25);
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#facc15', 20);
    SoundEngine.craft();

    // Pass day right on the spot (zero warping)
    this.sleepAndPassDay(false);
};

// ========================================================
// 8. ECONOMY, INVENTORY & XP
// ========================================================

Game.canItemFitInInventory = function(id: string, count: number = 1, qualityOrIngredients?: number | Record<string, number>, ingredientsToDeduct?: Record<string, number>): boolean {
    let itemQuality = 0;
    let deductMap: Record<string, number> | undefined = undefined;

    if (typeof qualityOrIngredients === 'number') {
        itemQuality = qualityOrIngredients;
        deductMap = ingredientsToDeduct;
    } else if (typeof qualityOrIngredients === 'object' && qualityOrIngredients !== null) {
        deductMap = qualityOrIngredients;
    }

    if (!this.player || !Array.isArray(this.player.inventory)) return false;

    const maxSlots = Math.max(this.player.maxInventorySlots || 36, this.player.inventory.length);
    const isWepOrTool = (id === 'slingshot' || id === 'rifle' || id === 'dragon_rifle' || id === 'dragon_cannon' || id === 'iron_sword' || id === 'excalibur_sword' || !!(WEAPONS && WEAPONS[id]) || id === 'hoe' || id === 'water' || id === 'scythe' || id === 'fishing_rod' || id === 'axe');

    // 1. Check if can stack into an existing slot (weapons/tools never stack, quality must match!)
    if (!isWepOrTool) {
        for (let i = 0; i < maxSlots; i++) {
            const slot = this.player.inventory[i];
            if (slot && slot.id === id && slot.count !== undefined && (slot.quality || 0) === itemQuality) {
                return true;
            }
        }
    }

    // 2. Count existing empty slots
    let emptySlots = 0;
    for (let i = 0; i < maxSlots; i++) {
        if (!this.player.inventory[i]) emptySlots++;
    }
    if (emptySlots > 0) return true;

    // 3. If deducting ingredients, simulate to see if any slot becomes empty
    if (deductMap) {
        const sim = this.player.inventory.map((s: any) => s ? { ...s } : null);
        for (let [ingId, reqCount] of Object.entries(deductMap)) {
            let needed = reqCount;
            for (let i = 0; i < sim.length; i++) {
                const s = sim[i];
                if (s && s.id === ingId) {
                    if (s.count !== undefined) {
                        const take = Math.min(s.count, needed);
                        s.count -= take;
                        needed -= take;
                        if (s.count <= 0) {
                            sim[i] = null;
                            emptySlots++;
                        }
                    } else {
                        sim[i] = null;
                        emptySlots++;
                        needed = 0;
                    }
                    if (needed <= 0) break;
                }
            }
        }
        if (emptySlots > 0) return true;
    }

    return false;
};

Game.addItemToInventory = function(id, count = 1, name = '', quality: 0 | 1 | 2 | 3 = 0, isFromWorldPickup: boolean = false) {
    const itemQuality = quality || 0;
    const maxSlots = Math.max(this.player.maxInventorySlots || 36, this.player.inventory.length);
    while (this.player.inventory.length < maxSlots) {
        this.player.inventory.push(null);
    }
    // 1. Stack into existing slot
    for (let i = 0; i < maxSlots; i++) {
        const slot = this.player.inventory[i];
        if (slot && slot.id === id && slot.count !== undefined && (slot.quality || 0) === itemQuality) {
            slot.count += count;
            this.updateHUD();
            return true;
        }
    }
    // 2. Insert into first empty slot
    const isWep = (id === 'slingshot' || id === 'rifle' || id === 'dragon_rifle' || id === 'dragon_cannon' || id === 'iron_sword' || id === 'excalibur_sword' || !!WEAPONS[id]);
    for (let i = 0; i < maxSlots; i++) {
        if (!this.player.inventory[i]) {
            let itemType = 'item';
            let cropId = undefined;
            if (isWep) itemType = 'weapon';
            else if (id === 'hoe' || id === 'water' || id === 'scythe' || id === 'fishing_rod' || id === 'axe') itemType = 'tool';
            else if (id.endsWith('_seed')) {
                itemType = 'seed';
                cropId = id.replace('_seed', '');
            } else if (RECIPES[id] || id === 'bread' || id === 'cheese' || id === 'cake' || id === 'cookie' || id === 'pizza' || id === 'grilled_fish' || id === 'spicy_fish_soup') {
                itemType = 'food';
            } else if (id === 'health_potion' || id === 'demon_elixir') {
                itemType = 'potion';
            } else if (CROPS[id]) {
                itemType = 'crop';
            } else if (FISH[id]) {
                itemType = 'fish';
            } else if (WORLD_ITEMS[id] || MONSTER_DROPS[id]) {
                itemType = 'material';
            }

            this.player.inventory[i] = {
                id: id,
                name: name || WEAPONS[id]?.name || CROPS[id]?.name || RECIPES[id]?.name || WORLD_ITEMS[id]?.name || MONSTER_DROPS[id]?.name || id,
                count: (isWep || itemType === 'tool') ? undefined : count,
                type: itemType,
                cropId: cropId,
                quality: itemQuality
            };

            this.updateHUD();
            return true;
        }
    }

    // Inventory is full!
    const now = performance.now();
    if (!this._lastFullInventoryWarning || now - this._lastFullInventoryWarning > 2000) {
        this._lastFullInventoryWarning = now;
        this.addFloatingText('กระเป๋าเต็มแล้ว! จัดช่องเก็บของก่อน (กด E หรือคลิกเพื่อเก็บ)', this.player.x, this.player.y - 15, '#f59e0b');
        if (SoundEngine && SoundEngine.hit) SoundEngine.hit();
    }

    // Only spawn dropped item if this was NOT an already existing item lying in the world
    if (!isFromWorldPickup) {
        this.spawnDroppedItem(id, count, this.player.x, this.player.y, itemQuality, true);
    }
    return false;
};


Game.removeItemFromInventory = function(id, count = 1) {
    if (!this.player || !Array.isArray(this.player.inventory)) return false;
    let remaining = count;
    for (let i = 0; i < this.player.inventory.length; i++) {
        const slot = this.player.inventory[i];
        if (slot && slot.id === id) {
            const hasCount = slot.count !== undefined ? slot.count : 1;
            if (hasCount <= remaining) {
                remaining -= hasCount;
                this.player.inventory[i] = null;
            } else {
                slot.count = hasCount - remaining;
                remaining = 0;
            }
            if (remaining <= 0) {
                this.updateHUD();
                return true;
            }
        }
    }
    this.updateHUD();
    return remaining <= 0;
};


Game.countItemInInventory = function(id) {
    if (!this.player || !Array.isArray(this.player.inventory)) return 0;
    let total = 0;
    for (let slot of this.player.inventory) {
        if (slot && slot.id === id) total += (slot.count !== undefined ? slot.count : 1);
    }
    return total;
};


Game.getItemCount = function(id) {
    return this.countItemInInventory(id);
};


Game.addXp = function(amount) {
    this.player.xp += amount;
    const nextLvlXp = LEVEL_XP[this.player.level + 1] || 99999;
    if (this.player.xp >= nextLvlXp) {
        this.player.level += 1;
        this.player.skillPoints = (this.player.skillPoints || 0) + 1;
        this.player.maxHp = 100 + (this.player.level - 1) * 15;
        this.player.hp = this.player.maxHp;
        this.player.maxEnergy = 100 + (this.player.level - 1) * 5;
        this.player.energy = this.player.maxEnergy;
        SoundEngine.levelUp();
        this.triggerScreenShake(4.0, 150);
        this.spawnParticles(this.player.x + 12, this.player.y + 14, '#facc15', 24);
        this.addFloatingText('★ LEVEL UP! เลเวล ' + this.player.level + ' (HP สูงสุด ' + this.player.maxHp + ') ★', this.player.x - 30, this.player.y - 32, '#facc15');
    }
    this.updateHUD();
};


Game.sellItem = function(index) {
    const item = this.player.inventory[index];
    if (!item) return;

    let price = 10;
    if (CROPS[item.id]) price = CROPS[item.id].sellPrice;
    else if (RECIPES[item.id]) price = RECIPES[item.id].sellPrice;
    else if (FISH[item.id]) price = FISH[item.id].sellPrice;
    else if (MONSTER_DROPS[item.id]) price = MONSTER_DROPS[item.id].sellPrice;
    else if (WORLD_ITEMS[item.id]) price = WORLD_ITEMS[item.id].sellPrice;
    else if (item.id === 'milk') price = 50;
    else if (item.id === 'egg') price = 25;
    else if (item.id === 'wool') price = 75;
    else if (item.id === 'truffle') price = 120;
    else if (item.id === 'bacon') price = 90;

    // Star Quality multiplier
    const quality = item.quality || 0;
    let qualityMult = 1.0;
    if (quality === 1) qualityMult = 1.25;
    else if (quality === 2) qualityMult = 1.50;
    else if (quality === 3) qualityMult = 2.00;

    // Artisan Expert Perk (+40% for artisan foods/drinks)
    if (this.player.skillMastery?.artisan_expert && (RECIPES[item.id] || item.id === 'wine' || item.id === 'cheese' || item.id.includes('wine') || item.id.includes('jam'))) {
        qualityMult *= 1.40;
    }

    // Gemologist Perk (+35% for gems and ores)
    if (this.player.skillMastery?.gemologist && (item.id === 'ruby' || item.id === 'emerald' || item.id === 'diamond' || item.id === 'cinder_shard' || item.id === 'dragon_tooth' || item.id === 'copper_ore' || item.id === 'iron_ore' || item.id === 'gold_ore')) {
        qualityMult *= 1.35;
    }

    const count = item.count || 1;
    const totalEarnings = Math.round(price * qualityMult * count);

    this.player.gold += totalEarnings;
    this.player.inventory[index] = null;
    this.stats.sales += count;

    SoundEngine.coin();
    this.addFloatingText('+' + totalEarnings + ' G', this.player.x, this.player.y - 15, '#fde047');
    this.updateHUD();
    this.renderSellModal();
};


// ========================================================
// 9. RENDERING ENGINE (2.5D Y-SORTING & DYNAMIC SHADOWS)
// ========================================================

Game.drawContactShadow = function(worldX, worldY, radiusX, radiusY, alpha = 0.28) {
    const sx = Math.round(worldX - this.camera.x);
    const sy = Math.round(worldY - this.camera.y);
    if (sx + radiusX < -20 || sx - radiusX > this.width + 20 || sy + radiusY < -20 || sy - radiusY > this.height + 20) return;

    this.ctx.fillStyle = `rgba(15, 23, 42, ${alpha})`;
    this.ctx.beginPath();
    this.ctx.ellipse(sx, sy, radiusX, radiusY, 0, 0, Math.PI * 2);
    this.ctx.fill();
};


Game.render = function() {
    this.ctx.fillStyle = '#1c1917';
    this.ctx.fillRect(0, 0, this.width, this.height);

    // Dynamic Renderables for 2.5D Depth & Y-Sorting
    const renderables = [];

    // 1. Draw Map Tiles (Ground Pass)
    const startCol = Math.max(0, Math.floor(this.camera.x / this.tileSize));
    const endCol = Math.min(this.mapWidth, Math.ceil((this.camera.x + this.width) / this.tileSize));
    const startRow = Math.max(0, Math.floor(this.camera.y / this.tileSize));
    const endRow = Math.min(this.mapHeight, Math.ceil((this.camera.y + this.height) / this.tileSize));

    for (let y = startRow; y < endRow; y++) {
        for (let x = startCol; x < endCol; x++) {
            const tile = this.map[y][x];
            const screenX = Math.round(x * this.tileSize - this.camera.x);
            const screenY = Math.round(y * this.tileSize - this.camera.y);

            // Ground rendering by tile type
            if (tile.type === 'path') this.ctx.drawImage(SPRITES.path, screenX, screenY);
            else if (tile.type === 'stone_path') this.ctx.drawImage(SPRITES.stonePath || SPRITES.path, screenX, screenY);
            else if (tile.type === 'wood_path') this.ctx.drawImage(SPRITES.woodPath || SPRITES.path, screenX, screenY);
            else if (tile.type === 'water') this.ctx.drawImage(SPRITES.water, screenX, screenY);
            else if (tile.type === 'soil' || tile.tilled) {
                this.ctx.drawImage(tile.watered ? SPRITES.soilWet : SPRITES.soilDry, screenX, screenY);
            } else if (tile.type === 'fence' || tile.type === 'wood_fence') {
                this.ctx.drawImage(this.currentScene === 'forest' ? SPRITES.darkGrass : SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 14, 5, 0.25);
                        this.ctx.drawImage(SPRITES.woodFence || SPRITES.fence, screenX, screenY);
                    }
                });
            } else if (tile.type === 'stone_fence') {
                this.ctx.drawImage(this.currentScene === 'forest' ? SPRITES.darkGrass : SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 14, 5, 0.25);
                        this.ctx.drawImage(SPRITES.stoneFence || SPRITES.fence, screenX, screenY);
                    }
                });
            } else if (tile.type === 'farm_lantern') {
                this.ctx.drawImage(this.currentScene === 'forest' ? SPRITES.darkGrass : this.currentScene === 'house' ? SPRITES.floorWood : SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 10, 4, 0.3);
                        this.ctx.drawImage(SPRITES.farmLantern, screenX, screenY);
                    }
                });
            } else if (tile.type === 'spire_portal') {
                this.ctx.drawImage(SPRITES.darkStone || SPRITES.path, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 16, 6, 0.35);
                        this.ctx.drawImage(SPRITES.spirePortal, screenX, screenY);
                    }
                });
            } else if (tile.type === 'shrine_altar') {
                this.ctx.drawImage(SPRITES.runeTile || SPRITES.darkStone, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 18, 6, 0.4);
                        this.ctx.fillStyle = '#475569';
                        this.ctx.fillRect(screenX + 4, screenY + 12, 24, 16);
                        this.ctx.fillStyle = '#64748b';
                        this.ctx.fillRect(screenX + 2, screenY + 8, 28, 6);
                        this.ctx.fillStyle = '#fde047';
                        this.ctx.fillRect(screenX + 13, screenY + 2, 6, 6);
                        this.ctx.fillStyle = '#f59e0b';
                        this.ctx.fillRect(screenX + 15, screenY, 2, 4);
                    }
                });
            } else if (tile.type === 'floorWood') this.ctx.drawImage(SPRITES.floorWood, screenX, screenY);
            else if (tile.type === 'wallHouse') this.ctx.drawImage(SPRITES.wallHouse, screenX, screenY);
            else if (tile.type === 'floorShop') this.ctx.drawImage(SPRITES.floorShop, screenX, screenY);
            else if (tile.type === 'wallShop') this.ctx.drawImage(SPRITES.wallShop, screenX, screenY);
            else if (tile.type === 'floorCarpet') this.ctx.drawImage(SPRITES.floorCarpet, screenX, screenY);
            else if (tile.type === 'wallManor') this.ctx.drawImage(SPRITES.wallManor, screenX, screenY);
            else if (tile.type === 'wallForge') this.ctx.drawImage(SPRITES.wallForge, screenX, screenY);
            else if (tile.type === 'doorMat') this.ctx.drawImage(SPRITES.doorMat, screenX, screenY);
            else if (tile.type === 'darkGrass') this.ctx.drawImage(SPRITES.darkGrass, screenX, screenY);
            else if (tile.type === 'darkStone') this.ctx.drawImage(SPRITES.darkStone, screenX, screenY);
            else if (tile.type === 'runeTile') this.ctx.drawImage(SPRITES.runeTile, screenX, screenY);
            else if (tile.type === 'bridge') this.ctx.drawImage(SPRITES.bridge, screenX, screenY);
            else if (tile.type === 'rubyNode') {
                this.ctx.drawImage(SPRITES.darkGrass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 12, 5, 0.28);
                        this.ctx.drawImage(SPRITES.rubyNode, screenX, screenY);
                    }
                });
            } else if (tile.type === 'starflower') {
                this.ctx.drawImage(SPRITES.darkGrass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 10, 4, 0.25);
                        this.ctx.drawImage(SPRITES.starflower, screenX, screenY);
                    }
                });
            } else if (tile.type === 'campfire') {
                this.ctx.drawImage(SPRITES.path, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 14, 6, 0.3);
                        this.ctx.drawImage(SPRITES.campfire, screenX, screenY);
                        if (this.currentScene === 'forest') {
                            this.drawCampfireFlame(screenX, screenY);
                        }
                    }
                });
            } else if (tile.type === 'pillar') {
                this.ctx.drawImage(SPRITES.runeTile, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 12, 5, 0.3);
                        this.ctx.drawImage(SPRITES.pillar, screenX, screenY - 16);
                    }
                });
            } else if (tile.type === 'barricade') {
                this.ctx.drawImage(SPRITES.path, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 14, 5, 0.3);
                        this.ctx.drawImage(SPRITES.barricade, screenX, screenY);
                    }
                });
            } else if (tile.type === 'streetLamp') {
                this.ctx.drawImage(SPRITES.path, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 8, 4, 0.25);
                        this.ctx.drawImage(SPRITES.streetLamp, screenX + 8, screenY - 10);
                    }
                });
            } else if (tile.type === 'fountain') {
                this.ctx.drawImage(SPRITES.darkStone, screenX, screenY);
            } else if (tile.type === 'chestClosed') {
                this.ctx.drawImage(SPRITES.darkStone, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 12, 5, 0.28);
                        this.ctx.drawImage(this.chests[tile.interactable] ? SPRITES.chestOpened : SPRITES.chestClosed, screenX, screenY);
                    }
                });
            } else if (tile.type === 'tree') {
                this.ctx.drawImage(this.currentScene === 'forest' ? SPRITES.darkGrass : SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 16, 7, 0.32);
                        this.ctx.drawImage(SPRITES.tree, screenX - 8, screenY - 30);
                    }
                });
            } else if (tile.type === 'tree_stump') {
                this.ctx.drawImage(this.currentScene === 'forest' ? SPRITES.darkGrass : SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 26,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 12, 5, 0.28);
                        this.ctx.drawImage(SPRITES.treeStump, screenX, screenY);
                    }
                });
            } else if (tile.type === 'sapling') {
                this.ctx.drawImage(this.currentScene === 'forest' ? SPRITES.darkGrass : (tile.tilled ? (tile.watered ? SPRITES.soilWet : SPRITES.soilDry) : SPRITES.grass), screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 26,
                    render: () => {
                        this.ctx.drawImage(SPRITES.sapling, screenX, screenY);
                    }
                });
            } else if (tile.type === 'dock') {
                this.ctx.drawImage(SPRITES.water, screenX, screenY);
                this.ctx.drawImage(SPRITES.fishingDock, screenX, screenY);
            } else if (tile.type === 'flowerBed') {
                this.ctx.drawImage(SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 26,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 24, 12, 5, 0.2);
                        this.ctx.drawImage(SPRITES.flowerBed, screenX, screenY);
                    }
                });
            } else if (tile.type === 'berryBush') {
                this.ctx.drawImage(SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 12, 5, 0.25);
                        this.ctx.drawImage(SPRITES.berryBush, screenX, screenY);
                    }
                });
            } else if (tile.type === 'hayBale') {
                this.ctx.drawImage(SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 14, 6, 0.3);
                        this.ctx.drawImage(SPRITES.hayBale, screenX, screenY);
                    }
                });
            } else if (tile.type === 'woodPile') {
                this.ctx.drawImage(SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 14, 6, 0.3);
                        this.ctx.drawImage(SPRITES.woodPile, screenX, screenY);
                    }
                });
            } else if (tile.type === 'treeApple') {
                this.ctx.drawImage(SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 16, 7, 0.32);
                        this.ctx.drawImage(SPRITES.treeApple, screenX - 8, screenY - 30);
                    }
                });
            } else if (tile.type === 'treeOrange') {
                this.ctx.drawImage(SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 16, 7, 0.32);
                        this.ctx.drawImage(SPRITES.treeOrange, screenX - 8, screenY - 30);
                    }
                });
            } else if (tile.type === 'placed_chest') {
                if (this.currentScene === 'forest') this.ctx.drawImage(SPRITES.darkGrass, screenX, screenY);
                else if (this.currentScene === 'house' || this.currentScene === 'shop') this.ctx.drawImage(SPRITES.floorWood, screenX, screenY);
                else this.ctx.drawImage(SPRITES.grass, screenX, screenY);

                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 14, 5, 0.3);
                        const isOpen = (this.currentOpenChestId === tile.interactable && this.activeModal === 'storageChestModal');
                        this.ctx.drawImage(isOpen ? SPRITES.chestOpened : SPRITES.chestClosed, screenX, screenY);
                    }
                });
            } else if (tile.type === 'sand') {
                this.ctx.fillStyle = '#fef08a';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                this.ctx.fillStyle = '#fde047';
                this.ctx.fillRect(screenX + 4, screenY + 12, 10, 2);
                this.ctx.fillRect(screenX + 18, screenY + 22, 8, 2);
            } else if (tile.type === 'palmTree') {
                this.ctx.fillStyle = '#fef08a';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 16, 7, 0.32);
                        if (SPRITES.palmTree) this.ctx.drawImage(SPRITES.palmTree, screenX - 8, screenY - 32);
                    }
                });
            } else if (tile.type === 'sailboat') {
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 18, 8, 0.35);
                        if (SPRITES.sailboat) this.ctx.drawImage(SPRITES.sailboat, screenX - 8, screenY - 16);

                        // Floating interactive prompt badge when player is near
                        const distToP = Math.hypot((this.player.x + 12) - (x * this.tileSize + 16), (this.player.y + 14) - (y * this.tileSize + 16));
                        if (distToP <= 80) {
                            const isIsland = this.currentScene === 'island';
                            const isRepaired = !!this.player.sailboatRepaired;
                            const promptText = isIsland ? 'ล่องเรือกลับหมู่บ้าน' : (isRepaired ? 'ล่องเรือสู่เกาะเขตร้อน' : 'บูรณะเรือใบ (ไม้ 20, เหล็ก 5, 500 G)');
                            const badgeY = screenY - 26 + Math.sin(performance.now() * 0.005) * 3;

                            this.ctx.save();
                            this.ctx.font = 'bold 9px "Prompt", sans-serif';
                            const tw = this.ctx.measureText(promptText).width;
                            const bx = screenX + 16 - (tw + 26) / 2;

                            this.ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
                            this.ctx.strokeStyle = isRepaired || isIsland ? '#38bdf8' : '#f59e0b';
                            this.ctx.lineWidth = 1.2;
                            this.ctx.beginPath();
                            if (typeof (this.ctx as any).roundRect === 'function') {
                                (this.ctx as any).roundRect(bx, badgeY, tw + 26, 17, 4);
                            } else {
                                this.ctx.rect(bx, badgeY, tw + 26, 17);
                            }
                            this.ctx.fill();
                            this.ctx.stroke();

                            // Key badge [E]
                            this.ctx.fillStyle = isRepaired || isIsland ? '#0284c7' : '#d97706';
                            this.ctx.fillRect(bx + 3, badgeY + 2.5, 12, 12);
                            this.ctx.fillStyle = '#ffffff';
                            this.ctx.font = 'bold 8px monospace';
                            this.ctx.textAlign = 'center';
                            this.ctx.fillText('E', bx + 9, badgeY + 11.5);

                            // Text
                            this.ctx.font = 'bold 9px "Prompt", sans-serif';
                            this.ctx.textAlign = 'left';
                            this.ctx.fillStyle = isRepaired || isIsland ? '#bae6fd' : '#fef08a';
                            this.ctx.fillText(promptText, bx + 18, badgeY + 12);

                            this.ctx.restore();
                        }
                    }
                });
            } else if (tile.type === 'pirateShipwreck') {
                this.ctx.fillStyle = '#fef08a';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                renderables.push({
                    depthY: y * this.tileSize + 32,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 32, y * this.tileSize + 30, 30, 12, 0.4);
                        if (SPRITES.pirateShipwreck) this.ctx.drawImage(SPRITES.pirateShipwreck, screenX - 16, screenY - 24);
                    }
                });
            } else if (tile.type === 'pirateChest') {
                this.ctx.fillStyle = '#fef08a';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                renderables.push({
                    depthY: y * this.tileSize + 24,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 22, 14, 6, 0.35);
                        if (SPRITES.pirateChest) this.ctx.drawImage(SPRITES.pirateChest, screenX, screenY - 8);
                    }
                });
            } else if (tile.type === 'pirateCaptain') {
                this.ctx.fillStyle = '#fef08a';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 12, 5, 0.35);
                        if (SPRITES.pirateCaptain) this.ctx.drawImage(SPRITES.pirateCaptain, screenX, screenY - 14);
                    }
                });
            } else if (tile.type === 'seashell') {
                this.ctx.fillStyle = '#fef08a';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                renderables.push({
                    depthY: y * this.tileSize + 16,
                    render: () => {
                        if (SPRITES.seashell) this.ctx.drawImage(SPRITES.seashell, screenX + 8, screenY + 8);
                    }
                });
            } else if (tile.type === 'messageBottle') {
                this.ctx.fillStyle = '#fef08a';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                renderables.push({
                    depthY: y * this.tileSize + 16,
                    render: () => {
                        if (SPRITES.messageBottle) this.ctx.drawImage(SPRITES.messageBottle, screenX + 8, screenY + 8);
                    }
                });
            } else if (tile.type === 'forage_banana') {
                this.ctx.fillStyle = '#fef08a';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                renderables.push({
                    depthY: y * this.tileSize + 16,
                    render: () => {
                        this.ctx.fillStyle = '#facc15';
                        this.ctx.beginPath();
                        this.ctx.arc(screenX + 16, screenY + 16, 7, 0, Math.PI * 2);
                        this.ctx.fill();
                        this.ctx.fillStyle = '#713f12';
                        this.ctx.fillRect(screenX + 15, screenY + 8, 2, 4);
                    }
                });
            } else if (tile.type === 'volcanoForge') {
                this.ctx.fillStyle = '#1c1917';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                renderables.push({
                    depthY: y * this.tileSize + 32,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 20, 8, 0.45);
                        if (SPRITES.volcanoForge) this.ctx.drawImage(SPRITES.volcanoForge, screenX - 8, screenY - 16);
                    }
                });
            } else if (tile.type === 'volcanoSwitch') {
                this.ctx.fillStyle = '#1c1917';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                renderables.push({
                    depthY: y * this.tileSize + 24,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 22, 12, 5, 0.35);
                        const spr = this.volcanoSwitchActive ? SPRITES.volcanoSwitchActive : SPRITES.volcanoSwitch;
                        if (spr) this.ctx.drawImage(spr, screenX, screenY);
                    }
                });
            } else if (tile.type === 'cinderShardNode') {
                this.ctx.fillStyle = '#1c1917';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                renderables.push({
                    depthY: y * this.tileSize + 24,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 22, 12, 5, 0.35);
                        if (SPRITES.cinderShardNode) this.ctx.drawImage(SPRITES.cinderShardNode, screenX, screenY);
                    }
                });
            } else if (tile.type === 'volcanoSpring') {
                this.ctx.fillStyle = '#38bdf8';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                this.ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
                this.ctx.fillRect(screenX + 4, screenY + 4, 8, 6);
                this.ctx.fillStyle = '#0284c7';
                this.ctx.strokeRect(screenX, screenY, this.tileSize, this.tileSize);
            } else if (tile.type === 'volcanoStairsDown') {
                this.ctx.fillStyle = '#1c1917';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                renderables.push({
                    depthY: y * this.tileSize + 16,
                    render: () => {
                        this.ctx.fillStyle = '#0f172a';
                        this.ctx.fillRect(screenX + 4, screenY + 4, 24, 24);
                        this.ctx.fillStyle = '#ea580c';
                        this.ctx.strokeRect(screenX + 4, screenY + 4, 24, 24);
                        this.ctx.fillStyle = '#cbd5e1';
                        this.ctx.fillRect(screenX + 6, screenY + 8, 20, 3);
                        this.ctx.fillRect(screenX + 8, screenY + 14, 16, 3);
                        this.ctx.fillRect(screenX + 10, screenY + 20, 12, 3);
                    }
                });
            } else if (tile.type === 'obsidianWall') {
                this.ctx.fillStyle = '#0c0a09';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                this.ctx.fillStyle = '#1c1917';
                this.ctx.fillRect(screenX + 2, screenY + 2, 28, 28);
                this.ctx.fillStyle = '#44403c';
                this.ctx.fillRect(screenX + 4, screenY + 4, 10, 8);
                this.ctx.fillRect(screenX + 16, screenY + 14, 12, 10);
                this.ctx.fillStyle = '#ea580c';
                this.ctx.fillRect(screenX + 8, screenY + 18, 4, 2);
            } else if (tile.type === 'mushroomBox') {
                this.ctx.drawImage(SPRITES.darkStone, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 14, 5, 0.3);
                        if (SPRITES.mushroomBox) this.ctx.drawImage(SPRITES.mushroomBox, screenX, screenY);
                    }
                });
            } else if (tile.type === 'farmCaveEntrance') {
                this.ctx.drawImage(SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 16, 6, 0.35);
                        if (SPRITES.caveEntrance) this.ctx.drawImage(SPRITES.caveEntrance, screenX, screenY);
                    }
                });
            } else if (tile.type === 'greenhouseBuilding' || tile.type === 'greenhouseDoor') {
                this.ctx.drawImage(SPRITES.grass, screenX, screenY);
                if (x === 29 && y === 2) {
                    renderables.push({
                        depthY: 3 * this.tileSize + 28,
                        render: () => {
                            this.drawContactShadow(29 * this.tileSize + 16, 3 * this.tileSize + 28, 32, 12, 0.35);
                            if (SPRITES.greenhouseExterior) this.ctx.drawImage(SPRITES.greenhouseExterior, screenX - 16, screenY - 32);
                        }
                    });
                }
            } else if (tile.type === 'forage_pineapple') {
                this.ctx.fillStyle = '#fef08a';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                renderables.push({
                    depthY: y * this.tileSize + 26,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 24, 10, 4, 0.25);
                        const icon = SPRITES.getItemIcon('pineapple');
                        if (icon) this.ctx.drawImage(icon, screenX + 4, screenY + 4, 24, 24);
                    }
                });
            } else if (tile.type === 'forage_coconut') {
                this.ctx.fillStyle = '#fef08a';
                this.ctx.fillRect(screenX, screenY, this.tileSize, this.tileSize);
                renderables.push({
                    depthY: y * this.tileSize + 26,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 24, 10, 4, 0.25);
                        const icon = SPRITES.getItemIcon('coconut');
                        if (icon) this.ctx.drawImage(icon, screenX + 4, screenY + 4, 24, 24);
                    }
                });
            } else if (tile.type === 'caveFruitDrop') {
                this.ctx.drawImage(SPRITES.darkStone, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 24,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 22, 8, 3, 0.2);
                        const icon = SPRITES.getItemIcon('apple') || SPRITES.getItemIcon('strawberry');
                        if (icon) this.ctx.drawImage(icon, screenX + 6, screenY + 6, 20, 20);
                    }
                });
            } else if (tile.type === 'easterEgg') {
                this.ctx.drawImage(SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 26,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 24, 8, 3, 0.25);
                        const icon = SPRITES.getItemIcon('easter_egg');
                        if (icon) this.ctx.drawImage(icon, screenX + 6, screenY + 6, 20, 20);
                    }
                });
            } else if (tile.type === 'caveFloor') {
                this.ctx.drawImage(SPRITES.caveFloor, screenX, screenY);
            } else if (tile.type === 'caveWall') {
                this.ctx.drawImage(SPRITES.caveWall, screenX, screenY);
            } else if (tile.type === 'caveWater') {
                this.ctx.drawImage(SPRITES.caveWater, screenX, screenY);
            } else if (tile.type === 'caveLadder') {
                this.ctx.drawImage(SPRITES.caveFloor, screenX, screenY);
                this.ctx.drawImage(SPRITES.caveLadder, screenX, screenY);
            } else if (tile.type === 'caveEntrance') {
                this.ctx.drawImage(SPRITES.darkGrass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 16, 6, 0.35);
                        this.ctx.drawImage(SPRITES.caveEntrance, screenX, screenY);
                    }
                });
            } else if (tile.type === 'crystalPillar') {
                this.ctx.drawImage(SPRITES.caveFloor, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 14, 5, 0.35);
                        this.ctx.drawImage(SPRITES.crystalPillar, screenX, screenY - 14);
                    }
                });
            } else if (tile.type === 'goldNode') {
                this.ctx.drawImage(SPRITES.caveFloor, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 12, 5, 0.28);
                        this.ctx.drawImage(SPRITES.goldNode, screenX, screenY);
                    }
                });
            } else if (tile.type === 'manaNode') {
                this.ctx.drawImage(SPRITES.caveFloor, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 12, 5, 0.28);
                        this.ctx.drawImage(SPRITES.manaNode, screenX, screenY);
                    }
                });
            } else if (tile.type === 'diamondNode') {
                this.ctx.drawImage(SPRITES.caveFloor, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 12, 5, 0.28);
                        this.ctx.drawImage(SPRITES.diamondNode, screenX, screenY);
                    }
                });
            } else if (tile.type === 'breakableRock') {
                this.ctx.drawImage(SPRITES.caveFloor, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 12, 5, 0.28);
                        this.ctx.drawImage(SPRITES.breakableRock, screenX, screenY);
                    }
                });
            } else if (tile.type === 'caveLadderDown') {
                this.ctx.drawImage(SPRITES.caveFloor, screenX, screenY);
                this.ctx.drawImage(SPRITES.caveLadderDown, screenX, screenY);
            } else if (tile.type === 'caveElevator') {
                this.ctx.drawImage(SPRITES.caveFloor, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 14, 5, 0.35);
                        this.ctx.drawImage(SPRITES.caveElevator, screenX, screenY - 6);
                    }
                });
            } else if (tile.type === 'swampFloor') {
                this.ctx.drawImage(SPRITES.swampFloor, screenX, screenY);
            } else if (tile.type === 'swampWater') {
                this.ctx.drawImage(SPRITES.swampWater, screenX, screenY);
            } else if (tile.type === 'magmaFloor') {
                this.ctx.drawImage(SPRITES.magmaFloor, screenX, screenY);
            } else if (tile.type === 'magmaLava') {
                this.ctx.drawImage(SPRITES.magmaLava, screenX, screenY);
            } else if (tile.type === 'snowFloor') {
                this.ctx.drawImage(SPRITES.snowFloor, screenX, screenY);
            } else if (tile.type === 'iceFloor') {
                this.ctx.drawImage(SPRITES.iceFloor, screenX, screenY);
            } else if (tile.type === 'cryptFloor') {
                this.ctx.drawImage(SPRITES.cryptFloor, screenX, screenY);
            } else if (tile.type === 'cryptWall') {
                this.ctx.drawImage(SPRITES.cryptWall, screenX, screenY);
            } else if (tile.type === 'tombstone') {
                this.ctx.drawImage(SPRITES.cryptFloor, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 12, 5, 0.3);
                        this.ctx.drawImage(SPRITES.tombstone, screenX, screenY);
                    }
                });
            } else if (tile.type === 'icePillar') {
                this.ctx.drawImage(SPRITES.snowFloor, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 14, 5, 0.35);
                        this.ctx.drawImage(SPRITES.icePillar, screenX, screenY - 12);
                    }
                });
            } else if (tile.type === 'obsidianPillar') {
                this.ctx.drawImage(SPRITES.magmaFloor, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 14, 5, 0.35);
                        this.ctx.drawImage(SPRITES.obsidianPillar, screenX, screenY - 12);
                    }
                });
            } else if (tile.type === 'bogTree') {
                this.ctx.drawImage(SPRITES.swampFloor, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 16, 6, 0.35);
                        this.ctx.drawImage(SPRITES.bogTree, screenX - 6, screenY - 16);
                    }
                });
            } else if (tile.type === 'pineTree') {
                this.ctx.drawImage(SPRITES.snowFloor, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 16, 6, 0.35);
                        this.ctx.drawImage(SPRITES.pineTree, screenX - 6, screenY - 16);
                    }
                });
            } else if (tile.type === 'ancientTree') {
                this.ctx.drawImage(SPRITES.canopyGrass || SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 18, 7, 0.4);
                        this.ctx.drawImage(SPRITES.ancientTree, screenX - 8, screenY - 24);
                    }
                });
            } else if (tile.type === 'thunderPillar') {
                this.ctx.drawImage(SPRITES.basaltFloor || SPRITES.cryptFloor, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 28, 14, 5, 0.35);
                        this.ctx.drawImage(SPRITES.thunderPillar, screenX, screenY - 16);
                    }
                });
            } else if (tile.type === 'starFruitCrop') {
                this.ctx.drawImage(SPRITES.canopyGrass || SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 26,
                    render: () => {
                        this.ctx.drawImage(SPRITES.starFruitCrop, screenX, screenY);
                    }
                });
            } else if (tile.type === 'thunderCrystalNode') {
                this.ctx.drawImage(SPRITES.basaltFloor || SPRITES.cryptFloor, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 26,
                    render: () => {
                        this.ctx.drawImage(SPRITES.thunderCrystalNode, screenX, screenY);
                    }
                });
            } else if (tile.type === 'canopyGrass') {
                this.ctx.drawImage(SPRITES.canopyGrass || SPRITES.grass, screenX, screenY);
            } else if (tile.type === 'basaltFloor') {
                this.ctx.drawImage(SPRITES.basaltFloor || SPRITES.cryptFloor, screenX, screenY);
            } else if (tile.type === 'sprinkler_basic') {
                this.ctx.drawImage(tile.tilled ? (tile.watered ? SPRITES.soilWet : SPRITES.soilDry) : SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 26,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 10, 4, 0.25);
                        this.ctx.drawImage(SPRITES.sprinklerBasic, screenX, screenY);
                    }
                });
            } else if (tile.type === 'sprinkler_quality') {
                this.ctx.drawImage(tile.tilled ? (tile.watered ? SPRITES.soilWet : SPRITES.soilDry) : SPRITES.grass, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 26,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 11, 4, 0.25);
                        this.ctx.drawImage(SPRITES.sprinklerQuality, screenX, screenY);
                    }
                });
            } else if (['mayo_machine', 'cheese_press', 'preserves_jar', 'wine_keg'].includes(tile.type)) {
                this.ctx.drawImage(this.currentScene === 'house' ? SPRITES.floorWood : SPRITES.grass, screenX, screenY);
                const machineObj = this.placedMachines?.[tile.interactable];
                const spr = tile.type === 'mayo_machine' ? SPRITES.mayoMachine :
                            tile.type === 'cheese_press' ? SPRITES.cheesePress :
                            tile.type === 'preserves_jar' ? SPRITES.preservesJar : SPRITES.wineKeg;
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 12, 5, 0.3);
                        this.ctx.drawImage(spr, screenX, screenY);

                        if (machineObj && machineObj.state === 'ready' && machineObj.readyItem) {
                            const bobY = Math.sin(performance.now() / 180) * 3;
                            this.ctx.fillStyle = '#ffffff';
                            this.ctx.strokeStyle = '#ca8a04';
                            this.ctx.lineWidth = 1.5;
                            this.ctx.beginPath();
                            this.ctx.roundRect(screenX + 5, screenY - 20 + bobY, 22, 18, 4);
                            this.ctx.fill();
                            this.ctx.stroke();

                            const icon = SPRITES.items[machineObj.readyItem];
                            if (icon) {
                                this.ctx.drawImage(icon, screenX + 8, screenY - 17 + bobY, 16, 16);
                            }
                        } else if (machineObj && machineObj.state === 'processing') {
                            const rot = Math.floor(performance.now() / 250) % 4;
                            this.ctx.fillStyle = '#38bdf8';
                            this.ctx.fillRect(screenX + 13 + (rot % 2) * 3, screenY - 8, 3, 3);
                        }
                    }
                });
            } else if (tile.type === 'dungeonChest') {
                const floorSpr = this.currentScene === 'volcano' ? SPRITES.magmaFloor :
                                 this.currentScene === 'frost_peak' ? SPRITES.snowFloor :
                                 this.currentScene === 'swamp' ? SPRITES.swampFloor :
                                 this.currentScene === 'crypt' ? SPRITES.cryptFloor : SPRITES.caveFloor;
                this.ctx.drawImage(floorSpr, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 14, 5, 0.35);
                        const isOpened = !!(this.player.openedDungeonChests && this.player.openedDungeonChests[tile.interactable]);
                        this.ctx.drawImage(isOpened ? SPRITES.dungeonChestOpened : SPRITES.dungeonChest, screenX, screenY);
                    }
                });
            } else if (tile.type === 'breakable_pot') {
                const floorSpr = this.currentScene === 'ancient_canopy' ? (SPRITES.canopyGrass || SPRITES.grass) :
                                 this.currentScene === 'tempest_plateau' ? (SPRITES.basaltFloor || SPRITES.cryptFloor) :
                                 this.currentScene === 'volcano' ? SPRITES.magmaFloor :
                                 this.currentScene === 'frost_peak' ? SPRITES.snowFloor :
                                 this.currentScene === 'swamp' ? SPRITES.swampFloor :
                                 this.currentScene === 'crypt' ? SPRITES.cryptFloor : SPRITES.caveFloor;
                this.ctx.drawImage(floorSpr, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 26,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 25, 10, 4, 0.28);
                        this.ctx.drawImage(SPRITES.breakablePot, screenX, screenY);
                    }
                });
            } else if (tile.type === 'breakable_crate') {
                const floorSpr = this.currentScene === 'ancient_canopy' ? (SPRITES.canopyGrass || SPRITES.grass) :
                                 this.currentScene === 'tempest_plateau' ? (SPRITES.basaltFloor || SPRITES.cryptFloor) :
                                 this.currentScene === 'volcano' ? SPRITES.magmaFloor :
                                 this.currentScene === 'frost_peak' ? SPRITES.snowFloor :
                                 this.currentScene === 'swamp' ? SPRITES.swampFloor :
                                 this.currentScene === 'crypt' ? SPRITES.cryptFloor : SPRITES.caveFloor;
                this.ctx.drawImage(floorSpr, screenX, screenY);
                renderables.push({
                    depthY: y * this.tileSize + 28,
                    render: () => {
                        this.drawContactShadow(x * this.tileSize + 16, y * this.tileSize + 26, 12, 5, 0.3);
                        this.ctx.drawImage(SPRITES.breakableCrate, screenX, screenY);
                    }
                });
            } else if (this.currentScene === 'forest') {
                this.ctx.drawImage(SPRITES.darkGrass, screenX, screenY);
            } else if (this.currentScene === 'ancient_canopy') {
                this.ctx.drawImage(SPRITES.canopyGrass || SPRITES.grass, screenX, screenY);
            } else if (this.currentScene === 'tempest_plateau') {
                this.ctx.drawImage(SPRITES.basaltFloor || SPRITES.cryptFloor, screenX, screenY);
            } else if (this.currentScene === 'cave' || this.currentScene === 'cave_depths') {
                this.ctx.drawImage(SPRITES.caveFloor, screenX, screenY);
            } else if (this.currentScene === 'swamp') {
                this.ctx.drawImage(SPRITES.swampFloor, screenX, screenY);
            } else if (this.currentScene === 'volcano') {
                this.ctx.drawImage(SPRITES.magmaFloor, screenX, screenY);
            } else if (this.currentScene === 'frost_peak') {
                this.ctx.drawImage(SPRITES.snowFloor, screenX, screenY);
            } else if (this.currentScene === 'crypt') {
                this.ctx.drawImage(SPRITES.cryptFloor, screenX, screenY);
            } else {
                this.ctx.drawImage(SPRITES.grass, screenX, screenY);
            }

            // Crops
            if (tile.crop) {
                const cropSet = SPRITES.crops[tile.crop.cropId] || SPRITES.crops.wheat;
                const cropSprite = cropSet[tile.crop.stage] || cropSet[0];
                this.ctx.drawImage(cropSprite, screenX, screenY);

                if (tile.crop.ready) {
                    this.ctx.fillStyle = '#ffffff';
                    const pulse = Math.sin(performance.now() / 200) * 2;
                    this.ctx.fillRect(screenX + 8 + pulse, screenY + 6, 2, 2);
                    this.ctx.fillRect(screenX + 22 - pulse, screenY + 8, 2, 2);
                }
            }
        }
    }

    // 2. Queue Scene-Specific Entities for Y-Sorting
    if (this.currentScene === 'farm') {
        this.queueFarmBuildings(renderables);
        this.animals.forEach(a => renderables.push({
            depthY: a.y + (a.height || 32),
            render: () => this.drawSingleAnimal(a)
        }));
        this.hiredGardeners.forEach(g => renderables.push({
            depthY: g.y + 30,
            render: () => this.drawSingleGardener(g)
        }));
        this.hiredHunters.forEach(h => renderables.push({
            depthY: h.y + 30,
            render: () => this.drawSingleHunter(h)
        }));
        this.demonBugs.forEach(b => renderables.push({
            depthY: b.y + 24,
            render: () => this.drawSingleBug(b)
        }));
    } else if (this.currentScene === 'house') {
        this.queueHouseInterior(renderables);
    } else if (this.currentScene === 'shop') {
        this.queueShopInterior(renderables);
    } else if (this.currentScene === 'manor') {
        this.queueManorInterior(renderables);
    } else if (this.currentScene === 'apothecary') {
        this.queueApothecaryInterior(renderables);
    } else if (this.currentScene === 'tavern') {
        this.queueTavernInterior(renderables);
    } else if (this.currentScene === 'forge') {
        this.queueForgeInterior(renderables);
    } else if (this.currentScene === 'village') {
        this.queueVillageEntities(renderables);
    } else if (this.currentScene === 'forest') {
        this.queueForestEntities(renderables);
    } else if (this.currentScene === 'cave') {
        this.queueCaveEntities(renderables);
    } else if (this.currentScene === 'cave_depths') {
        this.queueCaveDepthsEntities(renderables);
    } else if (this.currentScene === 'swamp') {
        this.queueSwampEntities(renderables);
    } else if (this.currentScene === 'volcano') {
        this.queueVolcanoEntities(renderables);
    } else if (this.currentScene === 'frost_peak') {
        this.queueFrostpeakEntities(renderables);
    } else if (this.currentScene === 'crypt') {
        this.queueCryptEntities(renderables);
    } else if (this.currentScene === 'spire') {
        this.queueSpireEntities(renderables);
    } else if (this.currentScene === 'ancient_canopy') {
        this.queueAncientCanopyEntities(renderables);
    } else if (this.currentScene === 'tempest_plateau') {
        this.queueTempestPlateauEntities(renderables);
    } else if (this.currentScene === 'island') {
        this.queueIslandEntities(renderables);
    } else if (this.currentScene === 'island_volcano') {
        this.queueSceneCombatEntities(renderables);
    }

    // Queue Pet Companion
    if (this.player.pet) {
        renderables.push({
            depthY: this.player.pet.y + 24,
            render: () => this.drawPetCompanion()
        });
    }

    // 3. Queue Player
    renderables.push({
        depthY: this.player.y + 30,
        render: () => this.drawPlayer()
    });

    // 3.5. Queue Remote Multiplayer Players
    if (this.remotePlayers) {
        for (const pid in this.remotePlayers) {
            const rp = this.remotePlayers[pid];
            if (!rp || rp.scene !== this.currentScene) continue;
            renderables.push({
                depthY: rp.y + 30,
                render: () => this.drawRemotePlayer(rp)
            });
        }
    }

    // 4. Sort and Draw all Entities by Y Depth (Back to Front)
    renderables.sort((a, b) => a.depthY - b.depthY);
    for (let i = 0; i < renderables.length; i++) {
        try {
            renderables[i].render();
        } catch (err) {
            console.warn('Entity render error:', err);
        }
    }

    // 5. Tile Cursor & Fishing Bobber
    this.drawTileCursor();
    this.drawFishingBobber();

    // 6. Projectiles, Combat Slash & Active Skill Visuals
    if (this.isCombatScene()) {
        this.drawProjectiles();
    }
    this.drawMeleeSlash();
    this.drawActiveSkillVisuals(this.ctx);
    this.drawBloodstain();

    // 7. Dynamic Weather & Lighting
    if (this.currentScene !== 'house' && this.currentScene !== 'shop') {
        if (this.time.weather !== 'sun' && !['cave', 'cave_depths', 'volcano', 'crypt', 'spire'].includes(this.currentScene)) this.drawWeatherEffects();
        this.drawDayNightLighting();
        if (this.currentScene === 'farm' && this.waveAlertTimer > 0) this.drawWaveAlertBanner();
    }

    // 8. Particles & Ambient Game Feel Effects
    this.drawParticles();
    this.drawAmbientEffects();
    this.drawFloatingTexts();

    // 9. Dropped Physical Items & Ambient Critters
    this.drawDroppedItems();
    this.drawAmbientCreatures();

    // 10. HUD Overlays & Cinematic Transitions
    if (this.currentScene === 'island_volcano') {
        this.drawVolcanoDungeonHUD();
    }
    this.drawActiveQuestTracker();
    this.drawTransition();
};


Game.queueFarmBuildings = function(renderables) {
    // House at (4, 2)
    renderables.push({
        depthY: 2 * this.tileSize + 6 + 76,
        render: () => {
            this.drawContactShadow(4 * this.tileSize + 48, 2 * this.tileSize + 6 + 76, 46, 10, 0.35);
            this.ctx.drawImage(SPRITES.house, Math.round(4 * this.tileSize - this.camera.x), Math.round(2 * this.tileSize + 6 - this.camera.y));
        }
    });

    // Barn at (23, 2)
    renderables.push({
        depthY: 2 * this.tileSize + 6 + 76,
        render: () => {
            this.drawContactShadow(23 * this.tileSize + 48, 2 * this.tileSize + 6 + 76, 46, 10, 0.35);
            this.ctx.drawImage(SPRITES.barn, Math.round(23 * this.tileSize - this.camera.x), Math.round(2 * this.tileSize + 6 - this.camera.y));
        }
    });

    // Shipping Bin at (8, 4)
    renderables.push({
        depthY: 4 * this.tileSize + 16 + 44,
        render: () => {
            this.drawContactShadow(8 * this.tileSize + 24, 4 * this.tileSize + 16 + 44, 22, 6, 0.3);
            this.ctx.drawImage(SPRITES.shippingBin, Math.round(8 * this.tileSize - this.camera.x), Math.round(4 * this.tileSize + 16 - this.camera.y));
        }
    });

    // Well at (9, 6)
    renderables.push({
        depthY: 6 * this.tileSize + 16 + 44,
        render: () => {
            this.drawContactShadow(9 * this.tileSize + 24, 6 * this.tileSize + 16 + 44, 22, 6, 0.3);
            this.ctx.drawImage(SPRITES.well, Math.round(9 * this.tileSize - this.camera.x), Math.round(6 * this.tileSize + 16 - this.camera.y));
        }
    });

    // Hunter Post at (11, 4)
    renderables.push({
        depthY: 4 * this.tileSize + 8 + 60,
        render: () => {
            this.drawContactShadow(11 * this.tileSize + 32, 4 * this.tileSize + 8 + 60, 28, 8, 0.3);
            this.ctx.drawImage(SPRITES.hunterPost, Math.round(11 * this.tileSize - this.camera.x), Math.round(4 * this.tileSize + 8 - this.camera.y));
        }
    });

    // Mill at (18, 16)
    renderables.push({
        depthY: 16 * this.tileSize + 6 + 76,
        render: () => {
            this.drawContactShadow(18 * this.tileSize + 32, 16 * this.tileSize + 6 + 76, 30, 8, 0.35);
            this.ctx.drawImage(SPRITES.mill, Math.round(18 * this.tileSize - this.camera.x), Math.round(16 * this.tileSize + 6 - this.camera.y));
        }
    });

    // Shop at (27, 16)
    renderables.push({
        depthY: 16 * this.tileSize + 6 + 76,
        render: () => {
            this.drawContactShadow(27 * this.tileSize + 48, 16 * this.tileSize + 6 + 76, 46, 10, 0.35);
            this.ctx.drawImage(SPRITES.shop, Math.round(27 * this.tileSize - this.camera.x), Math.round(16 * this.tileSize + 6 - this.camera.y));
        }
    });

    // Placed Farm Structures (Windmill, Silo)
    if (this.placedStructures) {
        this.placedStructures.forEach((st: any) => {
            if (st.scene === 'farm') {
                if (st.type === 'windmill') {
                    const drawX = st.x * this.tileSize;
                    const drawY = st.y * this.tileSize;
                    renderables.push({
                        depthY: (st.y + 2) * this.tileSize + 28,
                        render: () => {
                            this.drawContactShadow(drawX + 32, (st.y + 2) * this.tileSize + 28, 30, 8, 0.35);
                            this.ctx.drawImage(SPRITES.windmill, Math.round(drawX - this.camera.x), Math.round(drawY - this.camera.y));
                            const angle = (Date.now() / 400) % (Math.PI * 2);
                            const cx = Math.round(drawX + 32 - this.camera.x);
                            const cy = Math.round(drawY + 28 - this.camera.y);
                            this.ctx.save();
                            this.ctx.translate(cx, cy);
                            this.ctx.rotate(angle);
                            this.ctx.strokeStyle = '#fef08a';
                            this.ctx.lineWidth = 3;
                            for (let b = 0; b < 4; b++) {
                                this.ctx.rotate(Math.PI / 2);
                                this.ctx.beginPath();
                                this.ctx.moveTo(0, 0);
                                this.ctx.lineTo(0, -22);
                                this.ctx.stroke();
                                this.ctx.fillStyle = '#fef3c7';
                                this.ctx.fillRect(2, -20, 8, 14);
                            }
                            this.ctx.restore();
                        }
                    });
                } else if (st.type === 'silo') {
                    const drawX = st.x * this.tileSize;
                    const drawY = st.y * this.tileSize;
                    renderables.push({
                        depthY: (st.y + 2) * this.tileSize + 28,
                        render: () => {
                            this.drawContactShadow(drawX + 32, (st.y + 2) * this.tileSize + 28, 28, 8, 0.35);
                            this.ctx.drawImage(SPRITES.silo, Math.round(drawX - this.camera.x), Math.round(drawY - this.camera.y));
                        }
                    });
                }
            }
        });
    }
};


Game.drawFarmBuildings = function() {
    const list = [];
    this.queueFarmBuildings(list);
    list.forEach(item => item.render());
};


Game.queueHouseInterior = function(renderables) {
    // Persian Rug on ground level
    if (this.player.houseUpgrades.persian_rug) {
        this.ctx.drawImage(SPRITES.persianRug, Math.round(11 * 32 - this.camera.x), Math.round(8 * 32 - this.camera.y));
    }

    // ♥ Living Spouse in Farmhouse
    if (this.player.spouse) {
        const spouseId = this.player.spouse;
        const spouseName = NPC_STORY[spouseId]?.name || 'คู่สมรส';
        const sx = 9 * 32;
        const sy = 6 * 32;
        renderables.push({
            depthY: sy + 30,
            render: () => {
                const screenSx = Math.round(sx - this.camera.x);
                const screenSy = Math.round(sy - this.camera.y);
                this.drawContactShadow(sx + 12, sy + 28, 10, 4, 0.28);
                const spr = (SPRITES.npcs as any)[spouseId]?.down?.[0] || SPRITES.npcs.lilian?.down?.[0] || SPRITES.npcs.uncle?.down?.[0];
                if (spr) this.ctx.drawImage(spr, screenSx, screenSy);

                // Heart badge over spouse head
                this.ctx.fillStyle = '#f43f5e';
                this.ctx.font = 'bold 11px sans-serif';
                this.ctx.fillText('♥', screenSx + 4, screenSy - 4);

                // Name tag
                this.ctx.fillStyle = '#fdf2f8';
                this.ctx.font = 'bold 9px "Prompt", sans-serif';
                this.ctx.textAlign = 'center';
                this.ctx.fillText(spouseName, screenSx + 12, screenSy + 38);
                this.ctx.textAlign = 'left';
            }
        });
    }

    // Bed at (19, 3)
    const bedSprite = this.player.houseUpgrades.bed_deluxe ? SPRITES.bedDeluxe : SPRITES.bedStandard;
    renderables.push({
        depthY: 3 * 32 + 42,
        render: () => {
            this.drawContactShadow(19 * 32 + 24, 3 * 32 + 42, 22, 6, 0.28);
            this.ctx.drawImage(bedSprite, Math.round(19 * 32 - this.camera.x), Math.round(3 * 32 - this.camera.y));
        }
    });

    // Wardrobe at (3, 3)
    renderables.push({
        depthY: 3 * 32 + 30,
        render: () => {
            this.drawContactShadow(3 * 32 + 16, 3 * 32 + 30, 16, 5, 0.3);
            this.ctx.drawImage(SPRITES.wardrobe, Math.round(3 * 32 - this.camera.x), Math.round(3 * 32 - 16 - this.camera.y));
        }
    });

    // Blueprint Workbench at (8, 3)
    renderables.push({
        depthY: 3 * 32 + 28,
        render: () => {
            this.drawContactShadow(8 * 32 + 22, 3 * 32 + 28, 22, 6, 0.3);
            this.ctx.fillStyle = '#78350f';
            this.ctx.fillRect(Math.round(8 * 32 - this.camera.x), Math.round(3 * 32 - this.camera.y), 44, 28);
            this.ctx.fillStyle = '#fef08a';
            this.ctx.fillRect(Math.round(8 * 32 + 4 - this.camera.x), Math.round(3 * 32 + 5 - this.camera.y), 36, 18);
            this.ctx.fillStyle = '#2563eb';
            this.ctx.fillRect(Math.round(8 * 32 + 8 - this.camera.x), Math.round(3 * 32 + 8 - this.camera.y), 28, 2);
        }
    });

    // Fireplace at (13, 2)
    if (this.player.houseUpgrades.fireplace) {
        renderables.push({
            depthY: 2 * 32 + 42,
            render: () => {
                this.drawContactShadow(13 * 32 + 24, 2 * 32 + 42, 22, 6, 0.35);
                this.ctx.drawImage(SPRITES.fireplace, Math.round(13 * 32 - this.camera.x), Math.round(2 * 32 - this.camera.y));
            }
        });
    }

    // Refrigerator at (6, 3)
    if (this.player.houseUpgrades.refrigerator) {
        renderables.push({
            depthY: 3 * 32 + 30,
            render: () => {
                this.drawContactShadow(6 * 32 + 16, 3 * 32 + 30, 16, 5, 0.3);
                this.ctx.drawImage(SPRITES.refrigerator, Math.round(6 * 32 - this.camera.x), Math.round(3 * 32 - 16 - this.camera.y));
            }
        });
    }

    // Tea Table at (11, 8)
    if (this.player.houseUpgrades.tea_table) {
        renderables.push({
            depthY: 8 * 32 + 36,
            render: () => {
                this.drawContactShadow(11 * 32 + 24, 8 * 32 + 36, 18, 6, 0.3);
                this.ctx.drawImage(SPRITES.teaTable, Math.round(11 * 32 + 8 - this.camera.x), Math.round(8 * 32 - this.camera.y));
            }
        });
    }

    // Placed Fish Tank in House
    if (this.placedStructures) {
        this.placedStructures.forEach((st: any) => {
            if (st.scene === 'house' && st.type === 'fish_tank') {
                const drawX = st.x * this.tileSize;
                const drawY = st.y * this.tileSize;
                renderables.push({
                    depthY: (st.y + 1) * this.tileSize + 30,
                    render: () => {
                        this.drawContactShadow(drawX + 32, (st.y + 1) * this.tileSize + 30, 30, 6, 0.3);
                        this.ctx.drawImage(SPRITES.fishTank, Math.round(drawX - this.camera.x), Math.round(drawY - this.camera.y));
                        const t = Date.now() / 600;
                        const fish1X = drawX + 16 + Math.sin(t) * 12;
                        const fish1Y = drawY + 16 + Math.cos(t * 1.5) * 4;
                        const fish2X = drawX + 44 - Math.sin(t * 0.8) * 12;
                        const fish2Y = drawY + 22 + Math.sin(t * 1.2) * 4;
                        this.ctx.fillStyle = '#f97316';
                        this.ctx.fillRect(Math.round(fish1X - this.camera.x), Math.round(fish1Y - this.camera.y), 6, 3);
                        this.ctx.fillStyle = '#06b6d4';
                        this.ctx.fillRect(Math.round(fish2X - this.camera.x), Math.round(fish2Y - this.camera.y), 5, 3);
                    }
                });
            }
        });
    }
};


Game.drawHouseInterior = function() {
    const list = [];
    this.queueHouseInterior(list);
    list.forEach(item => item.render());
};


Game.queueShopInterior = function(renderables) {
    // Checkout Counter at (4, 4)
    renderables.push({
        depthY: 4 * 32 + 30,
        render: () => {
            this.drawContactShadow(4 * 32 + 24, 4 * 32 + 30, 24, 6, 0.3);
            this.ctx.drawImage(SPRITES.shopCounter, Math.round(4 * 32 - this.camera.x), Math.round(4 * 32 - this.camera.y));
        }
    });

    // 4 Display Shelves with goods on top!
    const shelfPos = [{x: 6, y: 7}, {x: 10, y: 7}, {x: 14, y: 7}, {x: 18, y: 7}];
    shelfPos.forEach((p, idx) => {
        renderables.push({
            depthY: p.y * 32 + 30,
            render: () => {
                const sx = Math.round(p.x * 32 - this.camera.x);
                const sy = Math.round(p.y * 32 - this.camera.y);
                this.drawContactShadow(p.x * 32 + 24, p.y * 32 + 30, 24, 6, 0.3);
                this.ctx.drawImage(SPRITES.displayShelf, sx, sy);

                const shelfData = this.shopShelves[idx];
                if (shelfData && shelfData.count > 0 && shelfData.item) {
                    const icon = SPRITES.getItemIcon(shelfData.item);
                    this.ctx.drawImage(icon, sx + 6, sy + 3, 18, 18);
                    this.ctx.drawImage(icon, sx + 24, sy + 3, 18, 18);

                    // Price & Quantity badge
                    this.ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
                    this.ctx.beginPath();
                    this.ctx.roundRect(sx + 4, sy + 25, 40, 14, 3);
                    this.ctx.fill();
                    this.ctx.strokeStyle = '#facc15';
                    this.ctx.lineWidth = 1;
                    this.ctx.stroke();

                    this.ctx.fillStyle = '#fde047';
                    this.ctx.font = 'bold 8px "Prompt", sans-serif';
                    this.ctx.textAlign = 'center';
                    this.ctx.fillText(shelfData.price + 'G (' + shelfData.count + ')', sx + 24, sy + 35);
                    this.ctx.textAlign = 'left';
                }
            }
        });
    });

    // Draw NPC Customers
    this.shopNPCs.forEach(npc => {
        renderables.push({
            depthY: npc.y + 30,
            render: () => {
                const nx = Math.round(npc.x - this.camera.x);
                const ny = Math.round(npc.y - this.camera.y);

                // Contact shadow
                this.drawContactShadow(npc.x + 12, npc.y + 30, 8, 4, 0.28);

                const frames = SPRITES.npcs[npc.type] || SPRITES.npcs.uncle;
                const dirFrames = frames[npc.direction] || frames.down;
                const spr = dirFrames[npc.frame] || dirFrames[0];
                this.ctx.drawImage(spr, nx, ny);

                // Expressive speech bubble based on state
                if (npc.state === 'browsing') {
                    this.ctx.fillStyle = '#ffffff';
                    this.ctx.beginPath();
                    this.ctx.roundRect(nx + 3, ny - 16, 20, 12, 3);
                    this.ctx.fill();
                    this.ctx.strokeStyle = '#94a3b8';
                    this.ctx.lineWidth = 1;
                    this.ctx.stroke();

                    this.ctx.fillStyle = '#334155';
                    this.ctx.fillRect(nx + 6, ny - 10, 2, 2);
                    this.ctx.fillRect(nx + 11, ny - 10, 2, 2);
                    this.ctx.fillRect(nx + 16, ny - 10, 2, 2);
                } else if (npc.state === 'to_counter') {
                    this.ctx.fillStyle = '#ffffff';
                    this.ctx.beginPath();
                    this.ctx.roundRect(nx + 4, ny - 16, 18, 12, 3);
                    this.ctx.fill();
                    this.ctx.strokeStyle = '#facc15';
                    this.ctx.lineWidth = 1;
                    this.ctx.stroke();

                    this.ctx.fillStyle = '#b45309';
                    this.ctx.font = '9px sans-serif';
                    this.ctx.fillText('$', nx + 6, ny - 6);
                } else if (npc.state === 'leaving') {
                    this.ctx.fillStyle = '#ffffff';
                    this.ctx.beginPath();
                    this.ctx.roundRect(nx + 4, ny - 16, 18, 12, 3);
                    this.ctx.fill();
                    this.ctx.strokeStyle = '#ec4899';
                    this.ctx.lineWidth = 1;
                    this.ctx.stroke();

                    this.ctx.font = '9px sans-serif';
                    this.ctx.fillText('♥', nx + 6, ny - 6);
                }
            }
        });
    });
};


Game.drawShopInterior = function() {
    const list = [];
    this.queueShopInterior(list);
    list.forEach(item => item.render());
};


Game.queueManorInterior = function(renderables) {
    // 1. Mayor's Council Desk at (11, 3)
    renderables.push({
        depthY: 3 * 32 + 30,
        render: () => {
            this.drawContactShadow(11 * 32 + 32, 3 * 32 + 30, 36, 8, 0.35);
            this.ctx.fillStyle = '#78350f';
            this.ctx.fillRect(Math.round(11 * 32 - this.camera.x), Math.round(3 * 32 - this.camera.y), 64, 28);
            this.ctx.fillStyle = '#fef08a';
            this.ctx.fillRect(Math.round(11 * 32 + 4 - this.camera.x), Math.round(3 * 32 + 4 - this.camera.y), 56, 18);
            this.ctx.fillStyle = '#1e3a8a';
            this.ctx.font = 'bold 9px sans-serif';
            this.ctx.fillText('โต๊ะที่ว่าการสภา', Math.round(11 * 32 + 6 - this.camera.x), Math.round(3 * 32 + 16 - this.camera.y));
        }
    });

    // 2. Village Archives Bookshelves at (4, 3)
    renderables.push({
        depthY: 3 * 32 + 30,
        render: () => {
            this.drawContactShadow(4 * 32 + 36, 3 * 32 + 30, 34, 8, 0.3);
            this.ctx.drawImage(SPRITES.displayShelf, Math.round(4 * 32 - this.camera.x), Math.round(3 * 32 - this.camera.y));
            this.ctx.drawImage(SPRITES.displayShelf, Math.round(5 * 32 + 10 - this.camera.x), Math.round(3 * 32 - this.camera.y));
        }
    });

    // 3. Fireplace at (19, 2)
    renderables.push({
        depthY: 2 * 32 + 42,
        render: () => {
            this.drawContactShadow(19 * 32 + 24, 2 * 32 + 42, 22, 6, 0.35);
            this.ctx.drawImage(SPRITES.fireplace, Math.round(19 * 32 - this.camera.x), Math.round(2 * 32 - this.camera.y));
        }
    });

    // 4. Meeting Table in Center (10, 8)
    renderables.push({
        depthY: 8 * 32 + 34,
        render: () => {
            this.drawContactShadow(10 * 32 + 48, 8 * 32 + 34, 46, 10, 0.32);
            this.ctx.fillStyle = '#5c2c16';
            this.ctx.fillRect(Math.round(10 * 32 - this.camera.x), Math.round(8 * 32 - this.camera.y), 96, 26);
            this.ctx.fillStyle = '#b45309';
            this.ctx.fillRect(Math.round(10 * 32 + 4 - this.camera.x), Math.round(8 * 32 + 3 - this.camera.y), 88, 20);
        }
    });

    // 5. Indoor Secretary Scribe Barnaby at (8, 4)
    renderables.push({
        depthY: 4 * 32 + 30,
        render: () => {
            const sx = Math.round(8 * 32 - this.camera.x);
            const sy = Math.round(4 * 32 - this.camera.y);
            this.drawContactShadow(8 * 32 + 12, 4 * 32 + 30, 8, 4, 0.28);
            const scribeFrame = SPRITES.npcs.uncle?.down[Math.floor(performance.now() / 400) % 2];
            if (scribeFrame) this.ctx.drawImage(scribeFrame, sx, sy);
            this.ctx.fillStyle = '#93c5fd';
            this.ctx.font = 'bold 8px "Prompt", sans-serif';
            this.ctx.fillText('เสมียนบาร์นาบี้', sx - 10, sy - 5);
        }
    });
};


Game.queueApothecaryInterior = function(renderables) {
    // 1. Alchemy Cauldron at (6, 3)
    renderables.push({
        depthY: 3 * 32 + 30,
        render: () => {
            this.drawContactShadow(6 * 32 + 16, 3 * 32 + 30, 18, 6, 0.35);
            this.ctx.drawImage(SPRITES.alchemyCauldron, Math.round(6 * 32 - this.camera.x), Math.round(3 * 32 - this.camera.y));
        }
    });

    // 2. Herb Shelves at (17, 3) and (18, 3)
    renderables.push({
        depthY: 3 * 32 + 34,
        render: () => {
            this.drawContactShadow(17 * 32 + 16, 3 * 32 + 34, 16, 6, 0.3);
            this.ctx.drawImage(SPRITES.herbShelf, Math.round(17 * 32 - this.camera.x), Math.round(3 * 32 - 8 - this.camera.y));
            this.ctx.drawImage(SPRITES.herbShelf, Math.round(18 * 32 + 8 - this.camera.x), Math.round(3 * 32 - 8 - this.camera.y));
        }
    });

    // 3. Clinic Bed at (4, 9)
    renderables.push({
        depthY: 9 * 32 + 32,
        render: () => {
            this.drawContactShadow(4 * 32 + 24, 9 * 32 + 32, 24, 8, 0.3);
            this.ctx.drawImage(SPRITES.bedDeluxe, Math.round(4 * 32 - this.camera.x), Math.round(9 * 32 - this.camera.y));
            this.ctx.fillStyle = '#ec4899';
            this.ctx.font = 'bold 8px "Prompt", sans-serif';
            this.ctx.fillText('เตียงฟื้นฟู', Math.round(4 * 32 + 4 - this.camera.x), Math.round(9 * 32 - 4 - this.camera.y));
        }
    });

    // 4. Apprentice Emily at (10, 4)
    renderables.push({
        depthY: 4 * 32 + 30,
        render: () => {
            const ex = Math.round(10 * 32 - this.camera.x);
            const ey = Math.round(4 * 32 - this.camera.y);
            this.drawContactShadow(10 * 32 + 12, 4 * 32 + 30, 8, 4, 0.28);
            const emFrame = SPRITES.npcs.maid?.down[Math.floor(performance.now() / 400) % 2] || SPRITES.npcs.girl?.down[0];
            if (emFrame) this.ctx.drawImage(emFrame, ex, ey);
            this.ctx.fillStyle = '#86efac';
            this.ctx.font = 'bold 8px "Prompt", sans-serif';
            this.ctx.fillText('เอมิลี่ (ผู้ช่วย)', ex - 10, ey - 5);
        }
    });
};


Game.queueTavernInterior = function(renderables) {
    // 1. Tavern Bar Counter at (5, 4)
    renderables.push({
        depthY: 4 * 32 + 30,
        render: () => {
            this.drawContactShadow(5 * 32 + 32, 4 * 32 + 30, 34, 8, 0.35);
            this.ctx.drawImage(SPRITES.shopCounter, Math.round(5 * 32 - this.camera.x), Math.round(4 * 32 - this.camera.y));
            this.ctx.drawImage(SPRITES.shopCounter, Math.round(7 * 32 - this.camera.x), Math.round(4 * 32 - this.camera.y));
        }
    });

    // 2. Fireplace at (13, 2)
    renderables.push({
        depthY: 2 * 32 + 42,
        render: () => {
            this.drawContactShadow(13 * 32 + 24, 2 * 32 + 42, 22, 6, 0.35);
            this.ctx.drawImage(SPRITES.fireplace, Math.round(13 * 32 - this.camera.x), Math.round(2 * 32 - this.camera.y));
        }
    });

    // 3. Dining Tables at (5, 8), (17, 8), (17, 12)
    [{x: 5, y: 8}, {x: 17, y: 8}, {x: 17, y: 12}].forEach(p => {
        renderables.push({
            depthY: p.y * 32 + 34,
            render: () => {
                this.drawContactShadow(p.x * 32 + 24, p.y * 32 + 34, 24, 7, 0.3);
                this.ctx.drawImage(SPRITES.tavernTable, Math.round(p.x * 32 - this.camera.x), Math.round(p.y * 32 - this.camera.y));
            }
        });
    });

    // 4. Tavern Patrons sitting drinking
    // Patron 1 at table (4, 9)
    renderables.push({
        depthY: 9 * 32 + 28,
        render: () => {
            const px = Math.round(4 * 32 - this.camera.x);
            const py = Math.round(9 * 32 - this.camera.y);
            this.drawContactShadow(4 * 32 + 12, 9 * 32 + 28, 8, 4, 0.28);
            const f = SPRITES.npcs.grandpa?.right[0] || SPRITES.npcs.uncle?.right[0];
            if (f) this.ctx.drawImage(f, px, py);
            this.ctx.fillStyle = '#fef08a';
            this.ctx.font = 'bold 8px "Prompt", sans-serif';
            this.ctx.fillText('ลุงทอง', px, py - 4);
        }
    });

    // Patron 2 at table (19, 9)
    renderables.push({
        depthY: 9 * 32 + 28,
        render: () => {
            const px = Math.round(19 * 32 - this.camera.x);
            const py = Math.round(9 * 32 - this.camera.y);
            this.drawContactShadow(19 * 32 + 12, 9 * 32 + 28, 8, 4, 0.28);
            const f = SPRITES.npcs.merchant?.left[0] || SPRITES.npcs.auntie?.left[0];
            if (f) this.ctx.drawImage(f, px, py);
            this.ctx.fillStyle = '#fef08a';
            this.ctx.font = 'bold 8px "Prompt", sans-serif';
            this.ctx.fillText('นักเดินทาง', px - 8, py - 4);
        }
    });
};


Game.queueForgeInterior = function(renderables) {
    // 1. Blazing Master Furnace at (11, 2)
    renderables.push({
        depthY: 2 * 32 + 46,
        render: () => {
            this.drawContactShadow(11 * 32 + 32, 2 * 32 + 46, 36, 10, 0.4);
            this.ctx.drawImage(SPRITES.fireplace, Math.round(11 * 32 - this.camera.x), Math.round(2 * 32 - this.camera.y));
            this.ctx.drawImage(SPRITES.fireplace, Math.round(12 * 32 + 10 - this.camera.x), Math.round(2 * 32 - this.camera.y));
        }
    });

    // 2. Master Anvil at (12, 7)
    renderables.push({
        depthY: 7 * 32 + 30,
        render: () => {
            this.drawContactShadow(12 * 32 + 16, 7 * 32 + 30, 18, 6, 0.35);
            this.ctx.drawImage(SPRITES.masterAnvil, Math.round(12 * 32 - this.camera.x), Math.round(7 * 32 - this.camera.y));
            this.ctx.fillStyle = '#fb923c';
            this.ctx.font = 'bold 8px "Prompt", sans-serif';
            this.ctx.fillText('ทั่งช่างตีเหล็ก', Math.round(12 * 32 - 6 - this.camera.x), Math.round(7 * 32 - 4 - this.camera.y));
        }
    });

    // 3. Apprentice Smith Arthur at (14, 5)
    renderables.push({
        depthY: 5 * 32 + 30,
        render: () => {
            const ax = Math.round(14 * 32 - this.camera.x);
            const ay = Math.round(5 * 32 - this.camera.y);
            this.drawContactShadow(14 * 32 + 12, 5 * 32 + 30, 8, 4, 0.28);
            const f = SPRITES.npcs.boy?.left[Math.floor(performance.now() / 400) % 2];
            if (f) this.ctx.drawImage(f, ax, ay);
            this.ctx.fillStyle = '#fed7aa';
            this.ctx.font = 'bold 8px "Prompt", sans-serif';
            this.ctx.fillText('อาร์เธอร์ (เด็กฝึกงาน)', ax - 16, ay - 5);
        }
    });
};


Game.drawTileCursor = function() {
    const selItem = this.player.inventory[this.player.selectedSlot];
    const isWeapon = (selItem && (selItem.type === 'weapon' || WEAPONS[selItem.id]));

    // 1. Smart Auto-Aim Reticle for combat targets (Boss, Monsters, Bugs)
    if (this.isCombatScene()) {
        const autoTarget = this.findNearestCombatTarget(720);
        if (autoTarget) {
            const sx = Math.round(autoTarget.x - this.camera.x);
            const sy = Math.round(autoTarget.y - this.camera.y);
            const now = Date.now();
            const pulse = 1 + Math.sin(now / 140) * 0.12;
            const size = Math.round((autoTarget.type === 'boss' ? 26 : 16) * pulse);

            this.ctx.save();
            this.ctx.strokeStyle = autoTarget.type === 'boss' ? '#f59e0b' : '#38bdf8';
            this.ctx.lineWidth = 2;
            this.ctx.shadowColor = autoTarget.type === 'boss' ? 'rgba(245, 158, 11, 0.7)' : 'rgba(56, 189, 248, 0.7)';
            this.ctx.shadowBlur = 6;

            const bLen = Math.round(size * 0.45);
            // Top-Left bracket
            this.ctx.beginPath();
            this.ctx.moveTo(sx - size, sy - size + bLen);
            this.ctx.lineTo(sx - size, sy - size);
            this.ctx.lineTo(sx - size + bLen, sy - size);
            this.ctx.stroke();

            // Top-Right bracket
            this.ctx.beginPath();
            this.ctx.moveTo(sx + size - bLen, sy - size);
            this.ctx.lineTo(sx + size, sy - size);
            this.ctx.lineTo(sx + size, sy - size + bLen);
            this.ctx.stroke();

            // Bottom-Left bracket
            this.ctx.beginPath();
            this.ctx.moveTo(sx - size, sy + size - bLen);
            this.ctx.lineTo(sx - size, sy + size);
            this.ctx.lineTo(sx - size + bLen, sy + size);
            this.ctx.stroke();

            // Bottom-Right bracket
            this.ctx.beginPath();
            this.ctx.moveTo(sx + size - bLen, sy + size);
            this.ctx.lineTo(sx + size, sy + size);
            this.ctx.lineTo(sx + size, sy + size - bLen);
            this.ctx.stroke();

            // Center target pip
            this.ctx.fillStyle = autoTarget.type === 'boss' ? '#fbbf24' : '#7dd3fc';
            this.ctx.beginPath();
            this.ctx.arc(sx, sy, 2, 0, Math.PI * 2);
            this.ctx.fill();

            this.ctx.restore();
        }
    }

    if (this.isCombatScene() && isWeapon && this.mouseWorld) {
        const mx = Math.round(this.mouseWorld.x - this.camera.x);
        const my = Math.round(this.mouseWorld.y - this.camera.y);

        this.ctx.strokeStyle = '#ef4444';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.arc(mx, my, 8, 0, Math.PI * 2);
        this.ctx.stroke();

        this.ctx.beginPath();
        this.ctx.moveTo(mx - 12, my); this.ctx.lineTo(mx + 12, my);
        this.ctx.moveTo(mx, my - 12); this.ctx.lineTo(mx, my + 12);
        this.ctx.stroke();
    } else {
        const target = this.getTargetTile();
        if (target.x < 0 || target.x >= this.mapWidth || target.y < 0 || target.y >= this.mapHeight) return;

        const sx = Math.round(target.x * this.tileSize - this.camera.x);
        const sy = Math.round(target.y * this.tileSize - this.camera.y);
        const targetTile = this.map[target.y]?.[target.x];

        // Determine context color & feedback
        let mainColor = 'rgba(253, 224, 71, 0.85)';
        let fillColor = 'rgba(254, 240, 138, 0.08)';

        if (targetTile?.crop?.ready) {
            mainColor = '#4ade80';
            fillColor = 'rgba(74, 222, 128, 0.16)';
        } else if (targetTile?.interactable) {
            mainColor = '#38bdf8';
            fillColor = 'rgba(56, 189, 248, 0.12)';
        } else if (targetTile?.tilled && !targetTile?.watered && selItem?.id === 'water') {
            mainColor = '#60a5fa';
            fillColor = 'rgba(96, 165, 250, 0.14)';
        }

        const pulse = Math.sin(performance.now() / 240) * 0.8;
        const pad = 1 - pulse * 0.3;
        const cornerLen = 7;

        // Subtle warm tile glow
        this.ctx.fillStyle = fillColor;
        this.ctx.fillRect(sx + pad, sy + pad, this.tileSize - pad * 2, this.tileSize - pad * 2);

        // Elegant 4-corner brackets
        this.ctx.strokeStyle = mainColor;
        this.ctx.lineWidth = 2;
        this.ctx.lineCap = 'round';
        this.ctx.beginPath();

        // Top-Left
        this.ctx.moveTo(sx + pad, sy + pad + cornerLen);
        this.ctx.lineTo(sx + pad, sy + pad);
        this.ctx.lineTo(sx + pad + cornerLen, sy + pad);

        // Top-Right
        this.ctx.moveTo(sx + this.tileSize - pad - cornerLen, sy + pad);
        this.ctx.lineTo(sx + this.tileSize - pad, sy + pad);
        this.ctx.lineTo(sx + this.tileSize - pad, sy + pad + cornerLen);

        // Bottom-Right
        this.ctx.moveTo(sx + this.tileSize - pad, sy + this.tileSize - pad - cornerLen);
        this.ctx.lineTo(sx + this.tileSize - pad, sy + this.tileSize - pad);
        this.ctx.lineTo(sx + this.tileSize - pad - cornerLen, sy + this.tileSize - pad);

        // Bottom-Left
        this.ctx.moveTo(sx + pad + cornerLen, sy + this.tileSize - pad);
        this.ctx.lineTo(sx + pad, sy + this.tileSize - pad);
        this.ctx.lineTo(sx + pad, sy + this.tileSize - pad - cornerLen);

        this.ctx.stroke();
    }
};


Game.drawSingleAnimal = function(a) {
    const sx = Math.round(a.x - this.camera.x);
    const sy = Math.round(a.y - this.camera.y);
    const aw = a.width || 32;
    const ah = a.height || 32;

    // Soft Grounding Contact Shadow
    this.ctx.fillStyle = 'rgba(15, 23, 42, 0.28)';
    this.ctx.beginPath();
    this.ctx.ellipse(sx + aw / 2, sy + ah - 4, aw * 0.42, 5.5, 0, 0, Math.PI * 2);
    this.ctx.fill();

    let spriteList = SPRITES[a.type] || SPRITES.cow;
    let sprite = spriteList[a.frame] || spriteList[0];
    this.ctx.drawImage(sprite, sx, sy);

    const distToPlayer = Math.hypot(this.player.x - a.x, this.player.y - a.y);

    // If player is close, show prompt badge
    if (distToPlayer < 55) {
        const promptY = sy - 18;
        this.ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
        this.ctx.beginPath();
        this.ctx.roundRect(sx + aw / 2 - 24, promptY, 48, 15, 4);
        this.ctx.fill();
        this.ctx.strokeStyle = a.hasProduct ? '#facc15' : '#ec4899';
        this.ctx.lineWidth = 1;
        this.ctx.stroke();

        this.ctx.fillStyle = '#ffffff';
        this.ctx.font = 'bold 9px "Prompt", sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(a.hasProduct ? '[E] เก็บ' : '[E] ลูบ', sx + aw / 2, promptY + 11);
        this.ctx.textAlign = 'left';
    } else if (a.hasProduct) {
        // Cute soft bubble with product icon
        const bounce = Math.sin(performance.now() / 280) * 2;
        const bubbleX = sx + aw / 2;
        const bubbleY = sy - 12 + bounce;

        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.92)';
        this.ctx.beginPath();
        this.ctx.arc(bubbleX, bubbleY, 8, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.strokeStyle = '#facc15';
        this.ctx.lineWidth = 1.2;
        this.ctx.stroke();

        const icon = SPRITES.getItemIcon(a.product);
        this.ctx.drawImage(icon, bubbleX - 6, bubbleY - 6, 12, 12);
    }

    // Floating heart above animal if petted today
    if (a.pettedToday && Math.sin(performance.now() / 450 + a.x) > 0.65) {
        this.ctx.fillStyle = '#f43f5e';
        this.ctx.font = '9px sans-serif';
        this.ctx.fillText('♥', sx + aw - 6, sy - 2);
    }
};


Game.drawAnimals = function() {
    this.animals.forEach(a => this.drawSingleAnimal(a));
};


Game.drawPlayer = function() {
    // Draw Dash After-Images (Ghost Shadows)
    if (this.playerDashGhosts && this.playerDashGhosts.length > 0) {
        for (let g = this.playerDashGhosts.length - 1; g >= 0; g--) {
            const ghost = this.playerDashGhosts[g];
            ghost.alpha -= 0.08;
            if (ghost.alpha <= 0) {
                this.playerDashGhosts.splice(g, 1);
                continue;
            }
            this.ctx.save();
            this.ctx.globalAlpha = ghost.alpha * 0.55;
            const gx = Math.round(ghost.x - this.camera.x);
            const gy = Math.round(ghost.y - this.camera.y);
            const spr = SPRITES.player?.[ghost.direction]?.[ghost.frame] || SPRITES.player?.down?.[0];
            if (spr) this.ctx.drawImage(spr, gx, gy);
            this.ctx.restore();
        }
    }
    if (this.player.invincibleTimer > 0 && Math.floor(performance.now() / 100) % 2 === 0) {
        return; // Invincibility flashing
    }
    const px = Math.round(this.player.x - this.camera.x);
    const py = Math.round(this.player.y - this.camera.y);

    if (this.player.isMounted) {
        // Draw horse mount underneath player
        this.ctx.fillStyle = 'rgba(15, 23, 42, 0.35)';
        this.ctx.beginPath();
        this.ctx.ellipse(px + 12, py + 32, 14, 6, 0, 0, Math.PI * 2);
        this.ctx.fill();

        const horseFrames = Array.isArray(SPRITES.horse) ? SPRITES.horse : (SPRITES.horse?.[this.player.direction] || SPRITES.horse?.down);
        if (horseFrames && horseFrames.length) {
            const hIdx = (this.player.frame || 0) % horseFrames.length;
            const horseSpr = horseFrames[hIdx] || horseFrames[0];
            if (this.player.direction === 'left') {
                this.ctx.save();
                this.ctx.translate(px + 34, py);
                this.ctx.scale(-1, 1);
                this.ctx.drawImage(horseSpr, 0, 2);
                this.ctx.restore();
            } else {
                this.ctx.drawImage(horseSpr, px - 6, py + 2);
            }
        }

        // Player riding on saddle
        const dirFrames = SPRITES.player ? (SPRITES.player[this.player.direction] || SPRITES.player.down) : null;
        if (dirFrames) {
            const sprite = Array.isArray(dirFrames) ? dirFrames[0] : dirFrames;
            if (sprite) this.ctx.drawImage(sprite, px, py - 6);
        }
    } else {
        // Soft Grounding Contact Shadow
        this.ctx.fillStyle = 'rgba(15, 23, 42, 0.3)';
        this.ctx.beginPath();
        this.ctx.ellipse(px + 12, py + 30, 9, 4.5, 0, 0, Math.PI * 2);
        this.ctx.fill();

        const dirFrames = SPRITES.player ? (SPRITES.player[this.player.direction] || SPRITES.player.down) : null;
        if (dirFrames) {
            const fIdx = (this.player.frame || 0) % (dirFrames.length || 1);
            const sprite = Array.isArray(dirFrames) ? (dirFrames[fIdx] || dirFrames[0]) : dirFrames;
            if (sprite) this.ctx.drawImage(sprite, px, py);
        }
    }

    // Draw Active Guard Shield / Perfect Parry Aura
    if (this.player.isGuarding) {
        this.ctx.save();
        const isParryWindow = (this.player.guardTimer || 0) <= 240;

        let shieldX = px + 12;
        let shieldY = py + 16;
        if (this.player.direction === 'up') {
            shieldY = py + 8;
        } else if (this.player.direction === 'down') {
            shieldY = py + 22;
        } else if (this.player.direction === 'left') {
            shieldX = px + 2;
            shieldY = py + 16;
        } else if (this.player.direction === 'right') {
            shieldX = px + 22;
            shieldY = py + 16;
        }

        if (isParryWindow) {
            // Golden Radiant Perfect Parry Shield Window (< 240ms)
            const pulse = Math.sin(performance.now() * 0.02) * 2;
            this.ctx.shadowColor = '#fbbf24';
            this.ctx.shadowBlur = 14;

            // Parry Radiant Outer Aura Ring
            this.ctx.strokeStyle = 'rgba(251, 191, 36, 0.85)';
            this.ctx.lineWidth = 2.5;
            this.ctx.beginPath();
            this.ctx.arc(shieldX, shieldY, 14 + pulse, 0, Math.PI * 2);
            this.ctx.stroke();

            // Golden Kite Shield Body
            this.ctx.fillStyle = '#f59e0b';
            this.ctx.beginPath();
            this.ctx.moveTo(shieldX - 8, shieldY - 10);
            this.ctx.lineTo(shieldX + 8, shieldY - 10);
            this.ctx.lineTo(shieldX + 8, shieldY + 2);
            this.ctx.lineTo(shieldX, shieldY + 12);
            this.ctx.lineTo(shieldX - 8, shieldY + 2);
            this.ctx.closePath();
            this.ctx.fill();

            // Gold Trim
            this.ctx.strokeStyle = '#fef08a';
            this.ctx.lineWidth = 1.8;
            this.ctx.stroke();

            // Star Emblem in Center
            this.ctx.fillStyle = '#ffffff';
            this.ctx.fillRect(shieldX - 1.5, shieldY - 5, 3, 10);
            this.ctx.fillRect(shieldX - 5, shieldY - 1.5, 10, 3);
        } else {
            // Solid Steel Blue Block Shield (> 240ms)
            this.ctx.shadowColor = '#38bdf8';
            this.ctx.shadowBlur = 8;

            this.ctx.fillStyle = '#1e293b';
            this.ctx.beginPath();
            this.ctx.moveTo(shieldX - 7, shieldY - 9);
            this.ctx.lineTo(shieldX + 7, shieldY - 9);
            this.ctx.lineTo(shieldX + 7, shieldY + 1);
            this.ctx.lineTo(shieldX, shieldY + 10);
            this.ctx.lineTo(shieldX - 7, shieldY + 1);
            this.ctx.closePath();
            this.ctx.fill();

            this.ctx.strokeStyle = '#38bdf8';
            this.ctx.lineWidth = 1.6;
            this.ctx.stroke();

            // Steel cross
            this.ctx.fillStyle = '#94a3b8';
            this.ctx.fillRect(shieldX - 1, shieldY - 4, 2, 8);
            this.ctx.fillRect(shieldX - 4, shieldY - 1, 8, 2);
        }

        this.ctx.restore();
    }

    // Draw Guard Break Stun Stars
    if (this.player.guardBreakTimer && this.player.guardBreakTimer > 0) {
        this.ctx.save();
        const starTime = performance.now() * 0.006;
        for (let s = 0; s < 3; s++) {
            const sAng = starTime + (s * Math.PI * 2 / 3);
            const sx = px + 12 + Math.cos(sAng) * 12;
            const sy = py - 4 + Math.sin(sAng) * 4;
            this.ctx.fillStyle = '#fde047';
            this.ctx.shadowColor = '#f59e0b';
            this.ctx.shadowBlur = 6;
            this.ctx.fillRect(sx - 2, sy - 2, 4, 4);
        }
        this.ctx.restore();
    }

    // Overhead Player HP Bar (Visible in combat scenes, or when damaged, or when boss active)
    const maxH = this.player.maxHp || 100;
    const curHp = Math.max(0, this.player.hp || 0);
    const combatScenes = ['forest', 'cave', 'cave_depths', 'swamp', 'volcano', 'frost_peak', 'crypt', 'ancient_canopy', 'tempest_plateau', 'island', 'island_volcano'];
    const isCombatZone = combatScenes.includes(this.currentScene) || (this.boss && this.boss.alive && this.boss.active);
    const isDamaged = curHp < maxH;

    if (isCombatZone || isDamaged) {
        this.ctx.save();
        const barW = 34;
        const barH = 5;
        const barX = px + 12 - (barW / 2);
        const barY = py - 8;
        const ratio = Math.max(0, Math.min(1, curHp / maxH));

        // Background shadow
        this.ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
        this.ctx.fillRect(barX - 1, barY - 1, barW + 2, barH + 2);

        // Border
        this.ctx.strokeStyle = '#000000';
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(barX - 1, barY - 1, barW + 2, barH + 2);

        // Fill color based on ratio
        let fillColor = '#22c55e';
        if (ratio < 0.25) fillColor = '#ef4444';
        else if (ratio < 0.5) fillColor = '#f59e0b';

        this.ctx.fillStyle = fillColor;
        this.ctx.fillRect(barX, barY, Math.round(barW * ratio), barH);

        // Precise numeric text above bar
        this.ctx.font = 'bold 8px monospace, sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'bottom';
        this.ctx.lineWidth = 2;
        this.ctx.strokeStyle = '#000000';
        const hpText = `${Math.ceil(curHp)}/${maxH}`;
        this.ctx.strokeText(hpText, px + 12, barY - 1);
        this.ctx.fillStyle = ratio < 0.25 ? '#fca5a5' : '#ffffff';
        this.ctx.fillText(hpText, px + 12, barY - 1);

        this.ctx.restore();
    }
};


Game.drawWeatherEffects = function() {
    const time = performance.now();

    if (this.time.weather === 'rain' || this.time.weather === 'thunder') {
        this.ctx.strokeStyle = this.time.weather === 'thunder' ? 'rgba(191, 219, 254, 0.75)' : 'rgba(174, 214, 241, 0.6)';
        this.ctx.lineWidth = 1.5;
        const count = this.time.weather === 'thunder' ? 100 : 70;
        for (let i = 0; i < count; i++) {
            const rx = (i * 37 + time * 0.45) % this.width;
            const ry = (i * 29 + time * 0.85) % this.height;
            this.ctx.beginPath();
            this.ctx.moveTo(rx, ry);
            this.ctx.lineTo(rx - 4, ry + 13);
            this.ctx.stroke();
        }

        // Thunder & Lightning Flash
        if (this.time.weather === 'thunder') {
            if (this.lightningFlashTimer > 0) {
                this.lightningFlashTimer -= 16;
                this.ctx.fillStyle = `rgba(255, 255, 255, ${Math.min(0.65, this.lightningFlashTimer / 90)})`;
                this.ctx.fillRect(0, 0, this.width, this.height);
            } else if (Math.random() < 0.0035) {
                this.lightningFlashTimer = 160;
                SoundEngine.thunder();
            }
        }
    } else if (this.time.weather === 'snow') {
        // Soft drifting snowflakes
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
        for (let i = 0; i < 65; i++) {
            const sx = (i * 43 + Math.sin(time / 450 + i) * 14) % this.width;
            const sy = (i * 31 + time * 0.12) % this.height;
            const size = (i % 3 === 0) ? 3 : 2;
            this.ctx.beginPath();
            this.ctx.arc(sx, sy, size, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }
};


Game.drawRain = function() {
    this.drawWeatherEffects();
};


Game.drawDayNightLighting = function() {
    const hour = this.time.hour;
    let alpha = 0;
    let color = '0, 0, 0';

    if (this.currentScene === 'cave') {
        alpha = 0.82;
        color = '6, 10, 22';
    } else if (hour >= 6 && hour < 9) {
        alpha = 0.12 * (9 - hour) / 3;
        color = '251, 191, 36';
    } else if (hour >= 17 && hour < 20) {
        alpha = 0.28 * (hour - 16) / 4;
        color = '234, 88, 12';
    } else if (hour >= 20 || hour < 6) {
        alpha = 0.60;
        color = '10, 15, 28'; // Rich midnight atmosphere
    }

    if (alpha > 0) {
        this.ctx.fillStyle = `rgba(${color}, ${alpha})`;
        this.ctx.fillRect(0, 0, this.width, this.height);

        // Cozy Stardew Valley ambient lighting (torch, campfire, windows & player lantern)
        if (alpha > 0.18) {
            this.ctx.save();
            this.ctx.globalCompositeOperation = 'lighter';

            const drawLight = (worldX, worldY, innerRadius, outerRadius, intensity = 1.0) => {
                const lx = Math.round(worldX - this.camera.x);
                const ly = Math.round(worldY - this.camera.y);
                if (lx < -120 || lx > this.width + 120 || ly < -120 || ly > this.height + 120) return;

                const grad = this.ctx.createRadialGradient(lx, ly, innerRadius, lx, ly, outerRadius);
                grad.addColorStop(0, `rgba(254, 240, 138, ${0.35 * intensity})`);
                grad.addColorStop(0.4, `rgba(251, 191, 36, ${0.16 * intensity})`);
                grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

                this.ctx.fillStyle = grad;
                this.ctx.beginPath();
                this.ctx.arc(lx, ly, outerRadius, 0, Math.PI * 2);
                this.ctx.fill();
            };


            // 1. Player Lantern (Enhanced by Sun Glow Ring)
            const hasGlow = (typeof this.hasRing === 'function' && this.hasRing('ring_glow'));
            const lanternRadius = hasGlow ? 165 : 85;
            const lanternIntensity = hasGlow ? 1.4 : 1.0;
            drawLight(this.player.x + 12, this.player.y + 16, 12, lanternRadius, lanternIntensity);

            // 2. Scene Specific Glows
            if (this.currentScene === 'farm') {
                // House Porch & Windows
                drawLight(4 * this.tileSize + 48, 2 * this.tileSize + 54, 16, 95, 0.9);
                // Shop Windows
                drawLight(27 * this.tileSize + 48, 16 * this.tileSize + 54, 16, 95, 0.9);
                // Mill Lantern
                drawLight(18 * this.tileSize + 32, 16 * this.tileSize + 50, 10, 70, 0.75);
            } else if (this.currentScene === 'forest') {
                // Campfire (warm flickering hearth)
                const flicker = Math.sin(performance.now() / 110) * 8;
                drawLight(25 * 32 + 16, 30 * 32 + 14, 14, 110 + flicker, 1.3);
            } else if (this.currentScene === 'cave') {
                // Crystal pillars glow with cyan/violet luminescence
                const crystalGlowPositions = [
                    { x: 18 * 32 + 16, y: 28 * 32 + 16, c: '56, 189, 248' },
                    { x: 24 * 32 + 16, y: 28 * 32 + 16, c: '168, 85, 247' },
                    { x: 10 * 32 + 16, y: 14 * 32 + 16, c: '56, 189, 248' },
                    { x: 33 * 32 + 16, y: 14 * 32 + 16, c: '168, 85, 247' },
                    { x: 21 * 32 + 16, y: 8 * 32 + 16,  c: '234, 179, 8' },
                    { x: 37 * 32 + 16, y: 25 * 32 + 16, c: '56, 189, 248' },
                    { x: 8 * 32 + 16,  y: 25 * 32 + 16, c: '168, 85, 247' }
                ];
                crystalGlowPositions.forEach(p => {
                    const lx = Math.round(p.x - this.camera.x);
                    const ly = Math.round(p.y - this.camera.y);
                    if (lx < -120 || lx > this.width + 120 || ly < -120 || ly > this.height + 120) return;
                    const cgrad = this.ctx.createRadialGradient(lx, ly, 10, lx, ly, 95);
                    cgrad.addColorStop(0, `rgba(${p.c}, 0.55)`);
                    cgrad.addColorStop(0.5, `rgba(${p.c}, 0.22)`);
                    cgrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
                    this.ctx.fillStyle = cgrad;
                    this.ctx.beginPath();
                    this.ctx.arc(lx, ly, 95, 0, Math.PI * 2);
                    this.ctx.fill();
                });
            }

            // 3. Placed Farm Lanterns Glow
            if (this.placedLanterns && this.placedLanterns.length > 0) {
                this.placedLanterns.forEach((l: any) => {
                    if (l.scene === this.currentScene) {
                        const flicker = Math.sin((performance.now() + (l.x + l.y) * 100) / 120) * 4;
                        drawLight(l.x * this.tileSize + 16, l.y * this.tileSize + 16, 12, 105 + flicker, 1.2);
                    }
                });
            }

            this.ctx.restore();
        }
    }
};


Game.spawnParticles = function(x, y, color, count = 8) {
    if (this.particles.length > 150) {
        this.particles.splice(0, count);
    }
    for (let i = 0; i < count; i++) {
        this.particles.push({
            x: x, y: y,
            vx: (Math.random() - 0.5) * 3,
            vy: (Math.random() - 1.5) * 2.5,
            color: color,
            life: 1.0,
            size: Math.random() * 3 + 2
        });
    }
};


Game.drawParticles = function() {
    for (let i = this.particles.length - 1; i >= 0; i--) {
        const p = this.particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.life -= 0.04;
        if (p.life <= 0) { this.particles.splice(i, 1); continue; }
        const sx = Math.round(p.x - this.camera.x);
        const sy = Math.round(p.y - this.camera.y);
        this.ctx.fillStyle = p.color;
        this.ctx.fillRect(sx, sy, p.size, p.size);
    }
};


Game.addFloatingText = function(text, worldX, worldY, color = '#ffffff') {
    if (this.floatingTexts.length > 35) {
        this.floatingTexts.shift();
    }
    if (typeof text === 'string') {
        text = text.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/ug, '').trim();
    }
    this.floatingTexts.push({
        text: text, x: worldX, y: worldY,
        color: color, life: 1.0, vy: -0.7
    });
};


Game.drawFloatingTexts = function() {
    this.ctx.font = 'bold 13px "Prompt", sans-serif';
    for (let i = this.floatingTexts.length - 1; i >= 0; i--) {
        const t = this.floatingTexts[i];
        t.y += t.vy;
        t.life -= 0.02;
        if (t.life <= 0) { this.floatingTexts.splice(i, 1); continue; }
        const sx = Math.round(t.x - this.camera.x);
        const sy = Math.round(t.y - this.camera.y);

        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        this.ctx.fillText(t.text, sx + 1, sy + 1);
        this.ctx.fillStyle = t.color;
        this.ctx.fillText(t.text, sx, sy);
    }
};


// ========================================================
// 10. HUD & MODAL INTERFACE
// ========================================================

Game.swapInventorySlots = function(srcIndex: number, targetIndex: number) {
    if (srcIndex === targetIndex || isNaN(srcIndex) || isNaN(targetIndex)) return;
    if (srcIndex < 0 || srcIndex >= this.player.inventory.length) return;
    if (targetIndex < 0 || targetIndex >= this.player.inventory.length) return;

    const temp = this.player.inventory[srcIndex];
    this.player.inventory[srcIndex] = this.player.inventory[targetIndex];
    this.player.inventory[targetIndex] = temp;

    this.inventorySwapSource = null;
    this.draggedSlotIndex = null;
    SoundEngine.craft();
    this.updateHUD();

    const invModal = document.getElementById('inventoryModal');
    if (invModal && invModal.style.display !== 'none') {
        this.renderInventoryModal();
    }

    const itemTarget = this.player.inventory[targetIndex];
    const itemName = itemTarget ? itemTarget.name : 'ไอเทม';
    this.addFloatingText(` ย้าย / สลับ ${itemName} สำเร็จ!`, this.player.x, this.player.y - 15, '#4ade80');
};


Game.setupSlotInteractions = function(slotEl: HTMLElement, index: number, item: any, onClickFallback?: () => void) {
    slotEl.dataset.slotIndex = String(index);

    if (item) {
        slotEl.draggable = true;
    } else {
        slotEl.draggable = false;
    }

    // 1. Desktop HTML5 Drag & Drop
    slotEl.ondragstart = (e: DragEvent) => {
        if (!item) {
            e.preventDefault();
            return;
        }
        Game.draggedSlotIndex = index;
        if (e.dataTransfer) {
            e.dataTransfer.setData('text/plain', String(index));
            e.dataTransfer.effectAllowed = 'move';
        }
        slotEl.classList.add('is-dragging');
    };


    slotEl.ondragend = () => {
        Game.draggedSlotIndex = null;
        slotEl.classList.remove('is-dragging');
        document.querySelectorAll('.bag-slot.drag-over, .hotbar-slot.drag-over').forEach(el => el.classList.remove('drag-over'));
    };


    slotEl.ondragover = (e: DragEvent) => {
        e.preventDefault();
        if (e.dataTransfer) {
            e.dataTransfer.dropEffect = 'move';
        }
        if (!slotEl.classList.contains('drag-over')) {
            slotEl.classList.add('drag-over');
        }
    };


    slotEl.ondragleave = (e: DragEvent) => {
        const rect = slotEl.getBoundingClientRect();
        if (
            e.clientX < rect.left ||
            e.clientX >= rect.right ||
            e.clientY < rect.top ||
            e.clientY >= rect.bottom
        ) {
            slotEl.classList.remove('drag-over');
        }
    };


    slotEl.ondrop = (e: DragEvent) => {
        e.preventDefault();
        slotEl.classList.remove('drag-over');
        let src = Game.draggedSlotIndex;
        if (src === null || src === undefined) {
            if (e.dataTransfer) {
                const data = e.dataTransfer.getData('text/plain');
                if (data !== '') src = parseInt(data, 10);
            }
        }
        if (src !== null && src !== undefined && !isNaN(src) && src !== index) {
            Game.swapInventorySlots(src, index);
        }
    };


    // 2. Mobile Touch Drag & Drop (Touch gestures with floating follower ghost)
    let touchStartX = 0;
    let touchStartY = 0;
    let isTouchDragging = false;
    let touchGhostEl: HTMLElement | null = null;

    slotEl.ontouchstart = (e: TouchEvent) => {
        if (!item) return;
        const touch = e.touches[0];
        touchStartX = touch.clientX;
        touchStartY = touch.clientY;
        isTouchDragging = false;
    };


    slotEl.ontouchmove = (e: TouchEvent) => {
        if (!item) return;
        const touch = e.touches[0];
        const dist = Math.hypot(touch.clientX - touchStartX, touch.clientY - touchStartY);

        if (dist > 8) {
            isTouchDragging = true;
            if (e.cancelable) e.preventDefault();

            if (!touchGhostEl) {
                touchGhostEl = document.createElement('div');
                touchGhostEl.className = 'inventory-touch-ghost';
                const img = document.createElement('img');
                img.src = SPRITES.getItemDataURL(item.id);
                img.className = 'item-pixel-icon';
                touchGhostEl.appendChild(img);
                if (item.count !== undefined) {
                    const countBadge = document.createElement('span');
                    countBadge.className = 'slot-count';
                    countBadge.textContent = String(item.count);
                    touchGhostEl.appendChild(countBadge);
                }
                document.body.appendChild(touchGhostEl);
                slotEl.classList.add('is-dragging');
            }

            touchGhostEl.style.left = `${touch.clientX}px`;
            touchGhostEl.style.top = `${touch.clientY}px`;

            const elemUnder = document.elementFromPoint(touch.clientX, touch.clientY);
            const hoveredSlot = elemUnder ? (elemUnder.closest('.bag-slot, .hotbar-slot') as HTMLElement) : null;
            document.querySelectorAll('.bag-slot.drag-over, .hotbar-slot.drag-over').forEach(el => {
                if (el !== hoveredSlot) el.classList.remove('drag-over');
            });
            if (hoveredSlot && !hoveredSlot.classList.contains('drag-over')) {
                hoveredSlot.classList.add('drag-over');
            }
        }
    };


    slotEl.ontouchend = (e: TouchEvent) => {
        if (touchGhostEl) {
            touchGhostEl.remove();
            touchGhostEl = null;
        }
        slotEl.classList.remove('is-dragging');
        document.querySelectorAll('.bag-slot.drag-over, .hotbar-slot.drag-over').forEach(el => el.classList.remove('drag-over'));

        if (isTouchDragging) {
            Game.justFinishedTouchDrag = Date.now();
            const touch = e.changedTouches[0];
            const elemUnder = document.elementFromPoint(touch.clientX, touch.clientY);
            const targetSlot = elemUnder ? (elemUnder.closest('.bag-slot, .hotbar-slot') as HTMLElement) : null;
            if (targetSlot && targetSlot.dataset.slotIndex !== undefined) {
                const targetIdx = parseInt(targetSlot.dataset.slotIndex, 10);
                if (!isNaN(targetIdx) && targetIdx !== index) {
                    Game.swapInventorySlots(index, targetIdx);
                }
            }
        } else {
            // Immediate tap on touch screen (bypasses browser click delays and suppression)
            Game.justFinishedTouchDrag = Date.now();
            if (onClickFallback) {
                onClickFallback();
            }
        }
    };


    // 3. Click / Tap fallback
    slotEl.onclick = () => {
        if (Game.justFinishedTouchDrag && Date.now() - Game.justFinishedTouchDrag < 250) {
            return;
        }
        if (onClickFallback) {
            onClickFallback();
        }
    };

};


Game.updateHpHUD = function() {
    if (!this.player) return;
    const maxH = this.player.maxHp || 100;
    const curHp = Math.max(0, this.player.hp || 0);
    const hpPercent = Math.max(0, Math.min(100, (curHp / maxH) * 100));

    // 1. Primary/Mobile Vitals widget bar
    const hpBar = document.getElementById('hpBarFill');
    if (hpBar) {
        const isMobile = window.innerWidth <= 840;
        if (isMobile) {
            hpBar.style.width = hpPercent + '%';
            hpBar.style.height = '100%';
        } else {
            hpBar.style.height = hpPercent + '%';
            hpBar.style.width = '100%';
        }
        if (hpPercent < 25) hpBar.style.backgroundColor = '#dc2626';
        else if (hpPercent < 50) hpBar.style.backgroundColor = '#f97316';
        else hpBar.style.backgroundColor = '#ef4444';
    }

    // 2. Top-Left Player Badge HP Gauge & Live Text
    const topHpFill = document.getElementById('topHpFill');
    if (topHpFill) {
        topHpFill.style.width = hpPercent + '%';
        if (hpPercent < 25) {
            topHpFill.style.background = 'linear-gradient(90deg, #991b1b, #dc2626)';
        } else if (hpPercent < 50) {
            topHpFill.style.background = 'linear-gradient(90deg, #ea580c, #f97316)';
        } else {
            topHpFill.style.background = 'linear-gradient(90deg, #e11d48, #f43f5e)';
        }
    }
    const hudHpText = document.getElementById('hudHpText');
    if (hudHpText) {
        hudHpText.textContent = `${Math.ceil(curHp)} / ${maxH}`;
        if (hpPercent < 25) {
            hudHpText.style.color = '#fca5a5';
        } else {
            hudHpText.style.color = '#ffffff';
        }
    }
};


Game.updateEnergyHUD = function() {
    if (!this.player) return;
    const maxE = this.player.maxEnergy || 100;
    const curEnergy = Math.max(0, this.player.energy || 0);
    const percent = Math.max(0, Math.min(100, (curEnergy / maxE) * 100));

    // 1. Primary/Mobile Vitals widget bar
    const energyBar = document.getElementById('energyBarFill');
    if (energyBar) {
        const isMobile = window.innerWidth <= 840;
        if (isMobile) {
            energyBar.style.width = percent + '%';
            energyBar.style.height = '100%';
        } else {
            energyBar.style.height = percent + '%';
            energyBar.style.width = '100%';
        }
        if (percent < 25) energyBar.style.backgroundColor = '#ef4444';
        else if (percent < 50) energyBar.style.backgroundColor = '#f59e0b';
        else energyBar.style.backgroundColor = '#22c55e';
    }

    // 2. Top-Left Player Badge Energy Gauge & Live Text
    const topEnergyFill = document.getElementById('topEnergyFill');
    if (topEnergyFill) {
        topEnergyFill.style.width = percent + '%';
    }
    const hudEnergyText = document.getElementById('hudEnergyText');
    if (hudEnergyText) {
        hudEnergyText.textContent = `${Math.ceil(curEnergy)} / ${maxE}`;
    }
};


Game.updateHUD = function() {
    const hotbarEl = document.getElementById('hotbarSlots');
    if (hotbarEl) {
        hotbarEl.innerHTML = '';
        for (let i = 0; i < 10; i++) {
            const item = this.player.inventory[i];
            const slotEl = document.createElement('div');
            slotEl.className = 'hotbar-slot' + (i === this.player.selectedSlot ? ' active' : '');

            const numBadge = document.createElement('span');
            numBadge.className = 'slot-key';
            numBadge.textContent = String((i + 1) % 10);
            slotEl.appendChild(numBadge);

            if (item) {
                const img = document.createElement('img');
                img.src = SPRITES.getItemDataURL(item.id);
                img.className = 'slot-pixel-icon';
                img.draggable = false;
                slotEl.appendChild(img);

                if (item.count !== undefined) {
                    const countBadge = document.createElement('span');
                    countBadge.className = 'slot-count';
                    countBadge.textContent = String(item.count);
                    slotEl.appendChild(countBadge);
                }
                if (item.quality && item.quality > 0) {
                    const starBadge = document.createElement('span');
                    starBadge.className = 'slot-quality-star quality-' + item.quality;
                    starBadge.textContent = item.quality === 1 ? '★' : item.quality === 2 ? '★★' : '★★★';
                    starBadge.style.color = item.quality === 1 ? '#cbd5e1' : item.quality === 2 ? '#facc15' : '#c084fc';
                    slotEl.appendChild(starBadge);
                }
                slotEl.title = this.getItemTooltipText(item);
            } else {
                slotEl.title = `ช่องลัด ${(i + 1) % 10} (ลากไอเทมมาวางที่นี่)`;
            }

            this.setupSlotInteractions(slotEl, i, item, () => {
                if (i === this.player.selectedSlot && this.isItemEdible(item)) {
                    this.consumeItem(item, i);
                } else {
                    this.selectHotbarSlot(i);
                }
            });

            hotbarEl.appendChild(slotEl);
        }
    }

    const goldEl = document.getElementById('hudGold');
    if (goldEl) goldEl.textContent = this.player.gold;

    this.updateHpHUD();
    this.updateEnergyHUD();

    const isMobile = window.innerWidth <= 840;

    const hungerBar = document.getElementById('hungerBarFill');
    if (hungerBar) {
        const hVal = this.player.hunger !== undefined ? this.player.hunger : 100;
        const hMax = this.player.maxHunger || 100;
        const hPercent = Math.max(0, Math.min(100, (hVal / hMax) * 100));
        if (isMobile) {
            hungerBar.style.width = hPercent + '%';
            hungerBar.style.height = '100%';
        } else {
            hungerBar.style.height = hPercent + '%';
            hungerBar.style.width = '100%';
        }
        if (hPercent < 25) hungerBar.style.backgroundColor = '#ef4444';
        else if (hPercent < 50) hungerBar.style.backgroundColor = '#f59e0b';
        else hungerBar.style.backgroundColor = '#f97316';
    }

    const thirstBar = document.getElementById('thirstBarFill');
    if (thirstBar) {
        const tVal = this.player.thirst !== undefined ? this.player.thirst : 100;
        const tMax = this.player.maxThirst || 100;
        const tPercent = Math.max(0, Math.min(100, (tVal / tMax) * 100));
        if (isMobile) {
            thirstBar.style.width = tPercent + '%';
            thirstBar.style.height = '100%';
        } else {
            thirstBar.style.height = tPercent + '%';
            thirstBar.style.width = '100%';
        }
        if (tPercent < 25) thirstBar.style.backgroundColor = '#ef4444';
        else if (tPercent < 50) thirstBar.style.backgroundColor = '#38bdf8';
        else thirstBar.style.backgroundColor = '#06b6d4';
    }

    const waterFill = document.getElementById('waterFill');
    if (waterFill) waterFill.style.width = ((this.player.waterCan / this.player.waterCanMax) * 100) + '%';

    this.updateQuestTrackerHUD();

    const lvlEl = document.getElementById('hudLevel');
    if (lvlEl) lvlEl.textContent = 'Lv.' + this.player.level;

    // Dynamic Mobile Combat Button [A] UI Update
    const btnA = document.getElementById('touchBtnA');
    if (btnA && this.player && Array.isArray(this.player.inventory)) {
        const selItem = this.player.inventory[this.player.selectedSlot];
        const hasWeapon = (selItem && (selItem.type === 'weapon' || (typeof WEAPONS !== 'undefined' && WEAPONS[selItem.id])));
        const hasEnemies = (typeof this.findNearestCombatTarget === 'function' && this.findNearestCombatTarget(450) !== null);

        if (hasWeapon || hasEnemies) {
            btnA.classList.add('combat-mode');
            const spanEl = btnA.querySelector('span');
            const smallEl = btnA.querySelector('small');
            if (spanEl && spanEl.textContent !== 'ATK') spanEl.textContent = 'ATK';
            if (smallEl && smallEl.textContent !== 'ยิง/โจมตี') smallEl.textContent = 'ยิง/โจมตี';
        } else {
            btnA.classList.remove('combat-mode');
            const spanEl = btnA.querySelector('span');
            const smallEl = btnA.querySelector('small');
            if (spanEl && spanEl.textContent !== 'ACT') spanEl.textContent = 'ACT';
            if (smallEl && smallEl.textContent !== 'ทำฟาร์ม') smallEl.textContent = 'ทำฟาร์ม';
        }
    }

    // Dynamic Mobile Explore Button [E] UI Update
    const btnE = document.getElementById('touchBtnE');
    if (btnE && this.player && this.map) {
        let canInteract = false;
        const target = typeof this.getTargetTile === 'function' ? this.getTargetTile() : null;
        if (target && this.map[target.y] && this.map[target.y][target.x]) {
            const t = this.map[target.y][target.x];
            if (t && (t.interactable || (t.crop && t.crop.ready))) canInteract = true;
        }
        if (!canInteract) {
            const px = Math.floor((this.player.x + 10) / this.tileSize);
            const py = Math.floor((this.player.y + 20) / this.tileSize);
            const nearTiles = [
                this.map[py]?.[px],
                this.map[py - 1]?.[px],
                this.map[py + 1]?.[px],
                this.map[py]?.[px - 1],
                this.map[py]?.[px + 1]
            ];
            for (const nt of nearTiles) {
                if (nt && (nt.interactable || (nt.crop && nt.crop.ready))) {
                    canInteract = true;
                    break;
                }
            }
        }
        if (!canInteract && typeof this.findNearbyDroppedItem === 'function') {
            if (this.findNearbyDroppedItem(this.player.x + 12, this.player.y + 16, 48)) {
                canInteract = true;
            }
        }
        if (canInteract) {
            btnE.classList.add('interact-ready');
        } else {
            btnE.classList.remove('interact-ready');
        }
    }

    this.updateClockHUD();
};


Game.updateClockHUD = function() {
    const timeEl = document.getElementById('hudTime');
    if (timeEl) {
        const hStr = String(this.time.hour).padStart(2, '0');
        const mStr = String(this.time.minute).padStart(2, '0');
        timeEl.textContent = `${hStr}:${mStr} น.`;
    }

    const dayEl = document.getElementById('hudDay');
    if (dayEl) {
        const seasonName = SEASONS[this.time.seasonIndex];
        dayEl.textContent = `วันที่ ${this.time.day} ${seasonName}`;
    }

    const weatherEl = document.getElementById('hudWeather');
    if (weatherEl) {
        let wText = 'แจ่มใส';
        if (this.time.weather === 'rain') {
            wText = 'ฝนตก';
        } else if (this.time.weather === 'thunder') {
            wText = 'พายุฝนฟ้าคะนอง';
        } else if (this.time.weather === 'snow') {
            wText = 'หิมะตก';
        }
        weatherEl.textContent = wText;
    }
};


Game.toggleModal = function(modalType) {
    if (this.activeModal === modalType) this.closeAllModals();
    else this.openModal(modalType);
};


Game.openModal = function(modalType) {
    this.closeAllModals();
    this.activeModal = modalType;

    if (modalType === 'shop') {
        this.renderShopModal();
        document.getElementById('shopModal').style.display = 'flex';
    } else if (modalType === 'sell') {
        this.renderSellModal();
        document.getElementById('sellModal').style.display = 'flex';
    } else if (modalType === 'crafting') {
        this.renderCraftingModal();
        document.getElementById('craftingModal').style.display = 'flex';
    } else if (modalType === 'inventory') {
        this.renderInventoryModal();
        document.getElementById('inventoryModal').style.display = 'flex';
    } else if (modalType === 'sleepModal') {
        document.getElementById('sleepModal').style.display = 'flex';
    } else if (modalType === 'houseDecorModal') {
        this.renderHouseDecorModal();
        document.getElementById('houseDecorModal').style.display = 'flex';
    } else if (modalType === 'hunterModal') {
        this.renderHuntersModal();
        document.getElementById('hunterModal').style.display = 'flex';
    } else if (modalType === 'questModal') {
        this.renderQuestModal();
        document.getElementById('questModal').style.display = 'flex';
    } else if (modalType === 'forgeModal') {
        this.renderForgeModal();
        document.getElementById('forgeModal').style.display = 'flex';
    } else if (modalType === 'bountyBoardModal' || modalType === 'bountyBoard') {
        this.renderBountyBoard();
        const bEl = document.getElementById('bountyBoardModal');
        if (bEl) bEl.style.display = 'flex';
    } else if (modalType === 'controlsModal') {
        document.getElementById('controlsModal').style.display = 'flex';
    } else if (modalType === 'wardrobe') {
        this.openWardrobeModal();
    } else if (modalType === 'stockShelf') {
        this.openStockShelfModal(this.selectedShelfIndex || 0);
    } else if (modalType === 'loginModal') {
        if (typeof Auth !== 'undefined') Auth.openLoginModal();
    } else if (modalType === 'accountModal') {
        if (typeof Auth !== 'undefined') Auth.openAccountModal();
    } else if (modalType === 'worldMap' || modalType === 'worldMapModal') {
        this.renderWorldMap();
        const mapModal = document.getElementById('worldMapModal');
        if (mapModal) mapModal.style.display = 'flex';
    } else if (modalType === 'storageChestModal') {
        this.renderStorageChestModal();
        const chestModal = document.getElementById('storageChestModal');
        if (chestModal) chestModal.style.display = 'flex';
    } else if (modalType === 'gameMenuModal') {
        const menuModal = document.getElementById('gameMenuModal');
        if (menuModal) menuModal.style.display = 'flex';
        const menuIcon = document.getElementById('menuBgmIcon');
        const menuStatus = document.getElementById('menuBgmStatus');
        const isPlaying = SoundEngine.isBgmOn();
        if (menuIcon) menuIcon.textContent = isPlaying ? 'ON' : 'OFF';
        if (menuStatus) menuStatus.textContent = isPlaying ? 'สถานะ: เปิดเสียงเพลง' : 'สถานะ: ปิดเสียงเพลง';
    } else if (modalType === 'skillMasteryModal' || modalType === 'skillMastery') {
        this.renderSkillMasteryModal();
        const m = document.getElementById('skillMasteryModal');
        if (m) m.style.display = 'flex';
    } else if (modalType === 'farmCaveChoiceModal') {
        const m = document.getElementById('farmCaveChoiceModal');
        if (m) m.style.display = 'flex';
    } else if (modalType === 'festivalModal') {
        const m = document.getElementById('festivalModal');
        if (m) m.style.display = 'flex';
    } else if (modalType === 'weddingCutsceneModal') {
        const m = document.getElementById('weddingCutsceneModal');
        if (m) m.style.display = 'flex';
    } else if (modalType === 'campModal') {
        const m = document.getElementById('campModal');
        if (m) m.style.display = 'flex';
    } else {
        const fallbackEl = document.getElementById(modalType);
        if (fallbackEl) fallbackEl.style.display = 'flex';
    }
};


Game.closeModal = function(modalType?: string) {
    if (modalType) {
        const el = document.getElementById(modalType);
        if (el) el.style.display = 'none';
        if (this.activeModal === modalType) this.activeModal = null;
    } else {
        this.closeAllModals();
    }
};



Game.closeAllModals = function() {
    this.activeModal = null;
    this.currentOpenChestId = null;
    document.querySelectorAll('.modal-overlay').forEach(el => (el as HTMLElement).style.display = 'none');
    this.closeDialogue();
    if (this.player && this.player.outfit) {
        SPRITES.updatePlayerAppearance(this.player.outfit);
    }
};


// ========================================================
// 11. WARDROBE (แต่งชุดตัวละคร)
// ========================================================

Game.openWardrobeModal = function() {
    this.closeAllModals();
    this.activeModal = 'wardrobe';
    this.tempOutfit = Object.assign({}, this.player.outfit);

    this.renderWardrobeControls();
    this.renderWardrobePreview();
    document.getElementById('wardrobeModal').style.display = 'flex';
};


Game.renderWardrobeControls = function() {
    // Hats
    const hatsContainer = document.getElementById('wardrobeHats');
    hatsContainer.innerHTML = '';
    OUTFIT_OPTIONS.hats.forEach(h => {
        const btn = document.createElement('button');
        btn.className = 'picker-btn' + (this.tempOutfit.hatStyle === h.id ? ' active' : '');
        btn.textContent = h.name;
        btn.onclick = () => {
            this.tempOutfit.hatStyle = h.id;
            this.renderWardrobeControls();
            this.renderWardrobePreview();
        };

        hatsContainer.appendChild(btn);
    });

    // Shirts
    const shirtsContainer = document.getElementById('wardrobeShirts');
    shirtsContainer.innerHTML = '';
    OUTFIT_OPTIONS.shirts.forEach(s => {
        const circle = document.createElement('div');
        circle.className = 'color-circle' + (this.tempOutfit.shirtColor === s.id ? ' active' : '');
        circle.style.backgroundColor = s.id;
        circle.title = s.name;
        circle.onclick = () => {
            this.tempOutfit.shirtColor = s.id;
            this.renderWardrobeControls();
            this.renderWardrobePreview();
        };

        shirtsContainer.appendChild(circle);
    });

    // Overalls
    const overallsContainer = document.getElementById('wardrobeOveralls');
    overallsContainer.innerHTML = '';
    OUTFIT_OPTIONS.overalls.forEach(o => {
        const circle = document.createElement('div');
        circle.className = 'color-circle' + (this.tempOutfit.overallsColor === o.id ? ' active' : '');
        circle.style.backgroundColor = o.id;
        circle.title = o.name;
        circle.onclick = () => {
            this.tempOutfit.overallsColor = o.id;
            this.renderWardrobeControls();
            this.renderWardrobePreview();
        };

        overallsContainer.appendChild(circle);
    });

    // Hair
    const hairsContainer = document.getElementById('wardrobeHairs');
    hairsContainer.innerHTML = '';
    OUTFIT_OPTIONS.hairs.forEach(hr => {
        const circle = document.createElement('div');
        circle.className = 'color-circle' + (this.tempOutfit.hairColor === hr.id ? ' active' : '');
        circle.style.backgroundColor = hr.id;
        circle.title = hr.name;
        circle.onclick = () => {
            this.tempOutfit.hairColor = hr.id;
            this.renderWardrobeControls();
            this.renderWardrobePreview();
        };

        hairsContainer.appendChild(circle);
    });
};


Game.renderWardrobePreview = function() {
    const previewCanvas = document.getElementById('wardrobePreviewCanvas') as HTMLCanvasElement | null;
    if (!previewCanvas) return;
    const ctx = previewCanvas.getContext('2d');
    if (!ctx) return;
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, previewCanvas.width, previewCanvas.height);

    // Generate preview frames using temporary choices
    const previewSprites = SPRITES.player;
    SPRITES.updatePlayerAppearance(this.tempOutfit);

    const downSprite = SPRITES.player.down[0];
    ctx.drawImage(downSprite, 0, 0, 24, 32, 0, 0, 72, 96);
};


Game.saveOutfitCustomization = function() {
    this.player.outfit = Object.assign({}, this.tempOutfit);
    SPRITES.updatePlayerAppearance(this.player.outfit);
    SoundEngine.craft();
    this.addFloatingText(' แต่งชุดสำเร็จแล้ว!', this.player.x, this.player.y - 15, '#facc15');
    this.closeAllModals();
};


// ========================================================
// 12. HOUSE DECOR & ENERGY BUFF UPGRADES
// ========================================================

Game.renderHouseDecorModal = function() {
    const container = document.getElementById('houseDecorList');
    if (!container) return;
    container.innerHTML = '';

    Object.values(HOUSE_DECOR_UPGRADES).forEach(upg => {
        const card = document.createElement('div');
        card.className = 'craft-card';

        const isOwned = this.player.houseUpgrades[upg.id];
        const canBuy = (this.player.gold >= upg.price && !isOwned);

        const info = document.createElement('div');
        info.className = 'craft-card-info';
        info.innerHTML = `
            <h4>${upg.name}</h4>
            <p>${upg.desc}</p>
            <span class="price-tag">${isOwned ? 'ติดตั้งแล้ว (Active)' : 'ราคา: ' + upg.price + ' G'}</span>
        `;

        const actionBtn = document.createElement('button');
        actionBtn.className = 'btn-buy' + (isOwned ? ' disabled' : '');
        actionBtn.textContent = isOwned ? 'ติดตั้งแล้ว' : 'ซื้อ / ติดตั้ง';
        actionBtn.disabled = isOwned;

        actionBtn.onclick = () => {
            if (canBuy) {
                this.player.gold -= upg.price;
                this.player.houseUpgrades[upg.id] = true;

                if (upg.id === 'bed_deluxe') {
                    this.player.maxEnergy = 130;
                    this.player.energy = 130;
                }

                SoundEngine.craft();
                this.addFloatingText('ติดตั้ง ' + upg.name + ' แล้ว!', this.player.x, this.player.y - 15, '#fde047');
                this.updateHUD();
                this.renderHouseDecorModal();
            } else if (!isOwned) {
                alert('เหรียญทองไม่เพียงพอ!');
            }
        };


        card.appendChild(info);
        card.appendChild(actionBtn);
        container.appendChild(card);
    });
};


// ========================================================
// 13. SHELF STOCKING (จัดวางสินค้าขายในร้าน)
// ========================================================

Game.openStockShelfModal = function(shelfIndex) {
    this.closeAllModals();
    this.selectedShelfIndex = shelfIndex;
    this.activeModal = 'stockShelf';

    const titleEl = document.getElementById('stockShelfTitle');
    titleEl.textContent = `จัดวางสินค้าบนชั้นวางที่ ${shelfIndex + 1}`;

    this.renderStockShelfModal();
    document.getElementById('stockShelfModal').style.display = 'flex';
};


Game.renderStockShelfModal = function() {
    const listContainer = document.getElementById('shelfInventoryList');
    listContainer.innerHTML = '';

    const actionArea = document.getElementById('shelfActionArea');
    actionArea.style.display = 'none';

    let hasItems = false;
    this.player.inventory.forEach(item => {
        if (!item || item.type === 'tool') return;

        hasItems = true;
        const card = document.createElement('div');
        card.className = 'shelf-item-card';

        const img = document.createElement('img');
        img.src = SPRITES.getItemDataURL(item.id);
        img.className = 'item-pixel-icon';

        let defaultPrice = 25;
        if (CROPS[item.id]) defaultPrice = Math.round(CROPS[item.id].sellPrice * 1.3);
        else if (RECIPES[item.id]) defaultPrice = Math.round(RECIPES[item.id].sellPrice * 1.3);

        card.innerHTML = `
            <div style="flex: 1;">
                <b>${item.name}</b> (มีอยู่ ${item.count} ชิ้น)
            </div>
            <span class="price-tag">แนะนำ: ${defaultPrice} G</span>
        `;
        card.prepend(img);

        card.onclick = () => {
            document.querySelectorAll('.shelf-item-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');

            this.selectedItemToStock = item;
            actionArea.style.display = 'block';

            const countInput = document.getElementById('shelfStockCount') as HTMLInputElement | null;
            if (countInput) {
                countInput.max = String(item.count);
                countInput.value = String(Math.min(5, item.count));
            }

            const priceInput = document.getElementById('shelfStockPrice') as HTMLInputElement | null;
            if (priceInput) {
                priceInput.value = String(defaultPrice);
            }
        };


        listContainer.appendChild(card);
    });

    if (!hasItems) {
        listContainer.innerHTML = '<p class="empty-hint">ไม่มีสินค้าในกระเป๋าที่สามารถวางขายได้</p>';
    }
};


Game.confirmStockShelf = function() {
    if (!this.selectedItemToStock || this.selectedShelfIndex === null) return;

    const count = parseInt((document.getElementById('shelfStockCount') as HTMLInputElement)?.value || '1') || 1;
    const price = parseInt((document.getElementById('shelfStockPrice') as HTMLInputElement)?.value || '20') || 20;

    if (this.selectedItemToStock.count < count) {
        alert('จำนวนในกระเป๋ามีไม่พอ!');
        return;
    }

    // Deduct from inventory
    this.removeItemFromInventory(this.selectedItemToStock.id, count);

    // Assign to shelf
    this.shopShelves[this.selectedShelfIndex] = {
        id: this.selectedShelfIndex,
        x: this.shopShelves[this.selectedShelfIndex].x,
        y: this.shopShelves[this.selectedShelfIndex].y,
        item: this.selectedItemToStock.id,
        count: count,
        price: price
    };


    SoundEngine.click();
    this.addFloatingText('วาง ' + this.selectedItemToStock.name + ' x' + count + ' บนชั้นวางแล้ว!', this.player.x, this.player.y - 15, '#fde047');
    this.updateHUD();
    this.closeAllModals();
};


Game.clearShelf = function() {
    if (this.selectedShelfIndex === null) return;
    const shelf = this.shopShelves[this.selectedShelfIndex];
    if (shelf && shelf.count > 0) {
        this.addItemToInventory(shelf.item, shelf.count);
        shelf.item = null;
        shelf.count = 0;
        shelf.price = 0;
        SoundEngine.click();
        this.addFloatingText('เก็บสินค้ากลับเข้ากระเป๋าแล้ว', this.player.x, this.player.y - 15, '#cbd5e1');
        this.updateHUD();
    }
    this.closeAllModals();
};


// ========================================================
// 14. SHOP, SELL, CRAFTING & INVENTORY MODALS
// ========================================================

Game.renderShopModal = function() {
    const container = document.getElementById('shopItemsList');
    if (!container) return;
    container.innerHTML = '';

    Object.values(CROPS).forEach(crop => {
        const card = document.createElement('div');
        card.className = 'shop-card';

        const img = document.createElement('img');
        img.src = SPRITES.getItemDataURL(crop.id);
        img.className = 'item-pixel-icon';

        const info = document.createElement('div');
        info.className = 'shop-card-info';
        info.innerHTML = `
            <h4>${crop.seedName}</h4>
            <p>โตเต็มที่: ${crop.growDays} วัน | ขายได้: ${crop.sellPrice} G</p>
            <span class="price-tag">ราคา: ${crop.buyPrice} G</span>
        `;

        const buyBtn = document.createElement('button');
        buyBtn.className = 'btn-buy';
        buyBtn.textContent = 'ซื้อ';
        buyBtn.onclick = () => {
            if (this.player.gold >= crop.buyPrice) {
                this.player.gold -= crop.buyPrice;
                this.addItemToInventory(crop.id, 1, crop.seedName);
                SoundEngine.coin();
                this.updateHUD();
                this.renderShopModal();
            } else {
                alert('เหรียญทองไม่เพียงพอ!');
            }
        };


        card.appendChild(img);
        card.appendChild(info);
        card.appendChild(buyBtn);
        container.appendChild(card);
    });

    // Weapon option: hunting rifle
    const rifleCard = document.createElement('div');
    rifleCard.className = 'shop-card';
    const rifleImg = document.createElement('img');
    rifleImg.src = SPRITES.getItemDataURL('rifle');
    rifleImg.className = 'item-pixel-icon';
    const rifleInfo = document.createElement('div');
    rifleInfo.className = 'shop-card-info';
    rifleInfo.innerHTML = `
        <h4>ปืนล่าสัตว์โบราณ (Hunting Rifle)</h4>
        <p>พลังยิงสูง 75 dmg | ระยะไกล 520px | ส่องยิงศัตรู</p>
        <span class="price-tag">ราคา: 500 G</span>
    `;
    const rifleBtn = document.createElement('button');
    rifleBtn.className = 'btn-buy';
    rifleBtn.textContent = 'ซื้อ';
    rifleBtn.onclick = () => {
        if (this.player.gold >= 500) {
            this.player.gold -= 500;
            this.addItemToInventory('rifle', 1, 'ปืนล่าสัตว์โบราณ');
            SoundEngine.coin();
            this.updateHUD();
            this.renderShopModal();
        } else {
            alert('เหรียญทองไม่เพียงพอ!');
        }
    };

    rifleCard.appendChild(rifleImg);
    rifleCard.appendChild(rifleInfo);
    rifleCard.appendChild(rifleBtn);
    container.appendChild(rifleCard);
};


Game.renderSellModal = function() {
    const container = document.getElementById('sellItemsList');
    if (!container) return;
    container.innerHTML = '';

    let hasSellable = false;
    this.player.inventory.forEach((item, index) => {
        if (!item || item.type === 'tool' || item.type === 'weapon') return;

        hasSellable = true;
        let price = 10;
        if (CROPS[item.id]) price = CROPS[item.id].sellPrice;
        else if (RECIPES[item.id]) price = RECIPES[item.id].sellPrice;
        else if (FISH[item.id]) price = FISH[item.id].sellPrice;
        else if (MONSTER_DROPS[item.id]) price = MONSTER_DROPS[item.id].sellPrice;
        else if (item.id === 'milk') price = 50;
        else if (item.id === 'egg') price = 25;
        else if (item.id === 'wool') price = 75;
        else if (item.id === 'truffle') price = 120;
        else if (item.id === 'bacon') price = 90;

        const count = item.count || 1;
        const total = price * count;

        const card = document.createElement('div');
        card.className = 'sell-card';

        const img = document.createElement('img');
        img.src = SPRITES.getItemDataURL(item.id);
        img.className = 'item-pixel-icon';

        const info = document.createElement('div');
        info.className = 'sell-card-info';
        info.innerHTML = `
            <h4>${item.name} x${count}</h4>
            <p>ราคาต่อชิ้น: ${price} G</p>
            <span class="price-tag">มูลค่ารวม: ${total} G</span>
        `;

        const sellBtn = document.createElement('button');
        sellBtn.className = 'btn-sell';
        sellBtn.textContent = `ขาย (${total} G)`;
        sellBtn.onclick = () => this.sellItem(index);

        card.appendChild(img);
        card.appendChild(info);
        card.appendChild(sellBtn);
        container.appendChild(card);
    });

    if (!hasSellable) {
        container.innerHTML = '<p class="empty-hint">ไม่มีผลผลิตหรือไอเทมที่สามารถขายได้ในกระเป๋า</p>';
    }
};


Game.setCraftingTab = function(tab: 'all' | 'carpentry' | 'food') {
    this.activeCraftingTab = tab;
    document.querySelectorAll('.craft-tab-btn').forEach(btn => {
        if ((btn as HTMLElement).dataset.tab === tab) btn.classList.add('active');
        else btn.classList.remove('active');
    });
    this.renderCraftingModal();
};


Game.renderCraftingModal = function() {
    const container = document.getElementById('craftingList');
    if (!container) return;
    container.innerHTML = '';

    const currentTab = this.activeCraftingTab || 'all';

    Object.values(RECIPES).forEach(recipe => {
        const isCarpentry = (recipe.category === 'carpentry');
        if (currentTab === 'carpentry' && !isCarpentry) return;
        if (currentTab === 'food' && isCarpentry) return;

        const card = document.createElement('div');
        card.className = 'craft-card';

        const img = document.createElement('img');
        img.src = SPRITES.getItemDataURL(recipe.id);
        img.className = 'item-pixel-icon';

        const info = document.createElement('div');
        info.className = 'craft-card-info';

        let alreadyUpgraded = false;
        if (recipe.id === 'backpack_upgrade_1' && (this.player.maxInventorySlots || 36) >= 48) {
            alreadyUpgraded = true;
        } else if (recipe.id === 'backpack_upgrade_2' && (this.player.maxInventorySlots || 36) >= 60) {
            alreadyUpgraded = true;
        }

        let ingredText = '';
        let canCraft = !alreadyUpgraded;
        for (let [ingId, reqCount] of Object.entries(recipe.ingredients)) {
            const has = this.countItemInInventory(ingId);
            const ingName = CROPS[ingId]?.name || RECIPES[ingId]?.name || WORLD_ITEMS[ingId]?.name || (ingId === 'wood' ? 'ท่อนไม้' : ingId === 'iron_ore' ? 'แร่เหล็กดิบ' : ingId === 'milk' ? 'นมวัว' : ingId === 'egg' ? 'ไข่ไก่' : ingId === 'wool' ? 'ขนแกะ' : ingId);
            ingredText += `<span class="${has >= reqCount ? 'ing-ok' : 'ing-missing'}">${ingName}: ${has}/${reqCount}</span> `;
            if (has < reqCount) canCraft = false;
        }

        const isUpgrade = (recipe.id === 'backpack_upgrade_1' || recipe.id === 'backpack_upgrade_2');
        const fitsInBag = isUpgrade ? true : this.canItemFitInInventory(recipe.id, 1, recipe.ingredients);
        if (!fitsInBag && canCraft) {
            canCraft = false;
        }

        let priceDesc = recipe.sellPrice > 0 ? `ราคาขาย: ${recipe.sellPrice} G | +${recipe.xp} XP` : `+${recipe.xp} XP | อัปเกรดถาวร`;
        if (recipe.id.startsWith('backpack_upgrade')) {
            priceDesc = `เพิ่มความจุช่องเก็บของในกระเป๋าถาวร (+12 ช่อง)`;
        } else if (recipe.id === 'chest') {
            priceDesc = `นำไปวางบนพื้นดินเพื่อเก็บของได้ 16 ช่อง`;
        }

        info.innerHTML = `
            <h4>${recipe.name}</h4>
            <p>วัตถุดิบ: ${ingredText}</p>
            <span class="price-tag">${priceDesc}</span>
        `;

        const craftBtn = document.createElement('button');
        craftBtn.className = 'btn-craft' + (!canCraft ? ' disabled' : '');
        if (alreadyUpgraded) {
            craftBtn.textContent = '✓ อัปเกรดแล้ว';
            craftBtn.disabled = true;
        } else if (!fitsInBag) {
            craftBtn.textContent = 'กระเป๋าเต็ม';
            craftBtn.disabled = true;
            craftBtn.title = 'กระเป๋าเต็ม! จัดช่องเก็บของหรือใส่กล่องก่อนคราฟต์';
        } else {
            craftBtn.textContent = isCarpentry ? 'คราฟ / สร้าง' : 'ปรุง / แปรรูป';
            craftBtn.disabled = !canCraft;
        }

        craftBtn.onclick = () => {
            if (alreadyUpgraded) return;
            if (!fitsInBag) {
                SoundEngine.hit();
                this.addFloatingText('กระเป๋าเต็มแล้ว! จัดช่องเก็บของหรือใส่กล่องก่อนคราฟต์', this.player.x, this.player.y - 15, '#ef4444');
                return;
            }
            if (canCraft) {
                for (let [ingId, reqCount] of Object.entries(recipe.ingredients)) {
                    this.removeItemFromInventory(ingId, reqCount);
                }
                if (recipe.id === 'backpack_upgrade_1') {
                    this.player.maxInventorySlots = 48;
                    while (this.player.inventory.length < 48) this.player.inventory.push(null);
                    SoundEngine.levelUp();
                    this.addFloatingText('อัปเกรดกระเป๋าเป้นักเดินทาง! (ขยายเป็น 48 ช่อง)', this.player.x, this.player.y - 20, '#4ade80');
                } else if (recipe.id === 'backpack_upgrade_2') {
                    this.player.maxInventorySlots = 60;
                    while (this.player.inventory.length < 60) this.player.inventory.push(null);
                    SoundEngine.levelUp();
                    this.addFloatingText('อัปเกรดกระเป๋าเป้จอมผจญภัย! (ขยายเป็น 60 ช่อง)', this.player.x, this.player.y - 20, '#4ade80');
                } else {
                    this.addItemToInventory(recipe.id, 1, recipe.name);
                    SoundEngine.craft();
                    this.addFloatingText('คราฟ ' + recipe.name + ' สำเร็จ!', this.player.x, this.player.y - 15, '#4ade80');
                }
                this.addXp(recipe.xp);
                this.stats.crafts++;
                this.updateHUD();
                this.renderCraftingModal();
            }
        };


        card.appendChild(img);
        card.appendChild(info);
        card.appendChild(craftBtn);
        container.appendChild(card);
    });
};


Game.openStorageChest = function(chestId: string) {
    this.currentOpenChestId = chestId;
    this.placedChests = this.placedChests || {};

    if (!this.placedChests[chestId]) {
        this.placedChests[chestId] = {
            id: chestId,
            scene: this.currentScene,
            x: 0,
            y: 0,
            slots: Array(16).fill(null),
            name: 'กล่องเก็บของไม้'
        };

    }
    const chest = this.placedChests[chestId];
    while (chest.slots.length < 16) chest.slots.push(null);

    SoundEngine.chestOpen();
    this.openModal('storageChestModal');
    this.renderStorageChestModal();
};


Game.renderStorageChestModal = function() {
    const chestSlotsEl = document.getElementById('storageChestSlots');
    const playerSlotsEl = document.getElementById('storagePlayerSlots');
    if (!chestSlotsEl || !playerSlotsEl || !this.currentOpenChestId) return;

    chestSlotsEl.innerHTML = '';
    playerSlotsEl.innerHTML = '';

    const chest = this.placedChests[this.currentOpenChestId];
    if (!chest) return;
    while (chest.slots.length < 16) chest.slots.push(null);

    // 1. Render Chest Slots (16 slots)
    chest.slots.forEach((item, slotIdx) => {
        const slotEl = document.createElement('div');
        slotEl.className = 'bag-slot';

        if (item) {
            slotEl.draggable = true;
            const img = document.createElement('img');
            img.src = SPRITES.getItemDataURL(item.id);
            img.className = 'item-pixel-icon';
            img.draggable = false;
            slotEl.appendChild(img);

            if (item.count !== undefined && item.count > 1) {
                const countBadge = document.createElement('span');
                countBadge.className = 'slot-count';
                countBadge.textContent = String(item.count);
                slotEl.appendChild(countBadge);
            }
            slotEl.title = `${item.name} (คลิกเพื่อหยิบเข้ากระเป๋า)`;
        } else {
            slotEl.title = `ช่องกล่องว่าง ${slotIdx + 1}`;
        }

        slotEl.onclick = () => {
            if (!item) return;
            const success = this.addItemToInventory(item.id, item.count || 1, item.name);
            if (success) {
                chest.slots[slotIdx] = null;
                SoundEngine.click();
                this.renderStorageChestModal();
                this.updateHUD();
            }
        };


        chestSlotsEl.appendChild(slotEl);
    });

    // 2. Render Player Inventory Slots
    this.player.inventory.forEach((item, invIdx) => {
        const slotEl = document.createElement('div');
        slotEl.className = 'bag-slot';

        if (item) {
            slotEl.draggable = true;
            const img = document.createElement('img');
            img.src = SPRITES.getItemDataURL(item.id);
            img.className = 'item-pixel-icon';
            img.draggable = false;
            slotEl.appendChild(img);

            if (item.count !== undefined && item.count > 1) {
                const countBadge = document.createElement('span');
                countBadge.className = 'slot-count';
                countBadge.textContent = String(item.count);
                slotEl.appendChild(countBadge);
            }
            slotEl.title = `${item.name} (คลิกเพื่อฝากเข้ากล่อง)`;
        } else {
            slotEl.title = `ช่องกระเป๋าว่าง ${invIdx + 1}`;
        }

        slotEl.onclick = () => {
            if (!item) return;
            let deposited = false;
            if (item.count !== undefined) {
                for (let c = 0; c < chest.slots.length; c++) {
                    const cSlot = chest.slots[c];
                    if (cSlot && cSlot.id === item.id && cSlot.count !== undefined) {
                        cSlot.count += item.count;
                        this.player.inventory[invIdx] = null;
                        deposited = true;
                        break;
                    }
                }
            }
            if (!deposited) {
                const emptySlot = chest.slots.findIndex(s => s === null);
                if (emptySlot !== -1) {
                    chest.slots[emptySlot] = { ...item };

                    this.player.inventory[invIdx] = null;
                    deposited = true;
                }
            }

            if (deposited) {
                SoundEngine.click();
                this.renderStorageChestModal();
                this.updateHUD();
            } else {
                this.addFloatingText('กล่องเก็บของเต็มแล้ว!', this.player.x, this.player.y - 15, '#f87171');
            }
        };


        playerSlotsEl.appendChild(slotEl);
    });
};


Game.chestDepositMatching = function() {
    if (!this.currentOpenChestId) return;
    const chest = this.placedChests[this.currentOpenChestId];
    if (!chest) return;

    let depositedAny = false;
    for (let i = 0; i < this.player.inventory.length; i++) {
        const pItem = this.player.inventory[i];
        if (!pItem) continue;

        for (let c = 0; c < chest.slots.length; c++) {
            const cSlot = chest.slots[c];
            if (cSlot && cSlot.id === pItem.id && cSlot.count !== undefined && pItem.count !== undefined) {
                cSlot.count += pItem.count;
                this.player.inventory[i] = null;
                depositedAny = true;
                break;
            }
        }
    }

    if (depositedAny) {
        SoundEngine.craft();
        this.addFloatingText('ฝากของซ้ำเข้ากล่องเรียบร้อย', this.player.x, this.player.y - 15, '#4ade80');
        this.renderStorageChestModal();
        this.updateHUD();
    } else {
        this.addFloatingText('ไม่มีไอเทมที่ตรงกับในกล่อง', this.player.x, this.player.y - 15, '#cbd5e1');
    }
};


Game.chestTakeAll = function() {
    if (!this.currentOpenChestId) return;
    const chest = this.placedChests[this.currentOpenChestId];
    if (!chest) return;

    let tookAny = false;
    for (let c = 0; c < chest.slots.length; c++) {
        const item = chest.slots[c];
        if (!item) continue;
        const success = this.addItemToInventory(item.id, item.count || 1, item.name);
        if (success) {
            chest.slots[c] = null;
            tookAny = true;
        } else {
            break;
        }
    }

    if (tookAny) {
        SoundEngine.harvest();
        this.addFloatingText('หยิบของเข้ากระเป๋าเรียบร้อย', this.player.x, this.player.y - 15, '#4ade80');
        this.renderStorageChestModal();
        this.updateHUD();
    }
};


Game.pickupCurrentChest = function() {
    if (!this.currentOpenChestId) return;
    const chestId = this.currentOpenChestId;
    const chest = this.placedChests[chestId];
    if (!chest) return;

    for (let c = 0; c < chest.slots.length; c++) {
        const it = chest.slots[c];
        if (it) {
            this.addItemToInventory(it.id, it.count || 1, it.name);
            chest.slots[c] = null;
        }
    }

    this.addItemToInventory('chest', 1, 'กล่องเก็บของไม้');

    const sceneObj = this.scenes[chest.scene] || this.scenes.farm;
    if (sceneObj && sceneObj.map && sceneObj.map[chest.y] && sceneObj.map[chest.y][chest.x]) {
        const tile = sceneObj.map[chest.y][chest.x];
        tile.type = (chest.scene === 'forest' ? 'darkGrass' : (chest.scene === 'house' || chest.scene === 'shop' ? 'floorWood' : 'grass'));
        tile.solid = false;
        tile.interactable = null;
    }

    delete this.placedChests[chestId];
    this.currentOpenChestId = null;

    SoundEngine.craft();
    this.closeAllModals();
    this.addFloatingText('รื้อเก็บกล่องเข้ากระเป๋าเรียบร้อย', this.player.x, this.player.y - 15, '#4ade80');
    this.updateHUD();
};


// ========================================================
// 13.5 ITEM ENCYCLOPEDIA & TOOLTIP DETAILS HELPER
// ========================================================

Game.getItemTooltipData = function(item) {
    if (!item) return null;
    const id = item.id;
    let name = item.name || id;
    let category = 'ไอเทมทั่วไป';
    let hpRestore = 0;
    let energyRestore = 0;
    let attackDmg = 0;
    let range = 0;
    let desc = '';
    let sellPrice = 10;

    if (id === 'health_potion') {
        category = 'ยาฟื้นพลังชีวิต';
        hpRestore = 60;
        energyRestore = 30;
        desc = 'ดื่มเพื่อฟื้นฟู HP +60 และพลังงาน +30 (ถือแล้วกด Space หรือคลิก เพื่อดื่ม)';
        sellPrice = 80;
    } else if (id === 'demon_elixir') {
        category = 'ยาบำรุงพลังปีศาจ';
        hpRestore = 40;
        energyRestore = 85;
        desc = 'ยาบำรุงพลัง ฟื้นฟู HP +40 และพลังงาน +85 (ถือแล้วกด Space หรือคลิก เพื่อดื่ม)';
        sellPrice = 280;
    } else if (id === 'pizza') {
        category = 'อาหารจานหลัก (ครัว)';
        hpRestore = 30;
        energyRestore = 100;
        desc = 'พิซซ่าถาดใหญ่ อิ่มท้อง ฟื้นฟูพลังงาน +100 และ HP +30 (กด Space เพื่อกิน)';
        sellPrice = 360;
    } else if (id === 'cake') {
        category = 'ของหวานเบเกอรี่';
        hpRestore = 25;
        energyRestore = 90;
        desc = 'เค้กสตรอว์เบอร์รี่สด ฟื้นฟูพลังงาน +90 และ HP +25 (กด Space เพื่อกิน)';
        sellPrice = 320;
    } else if (id === 'spicy_fish_soup') {
        category = 'อาหารปรุงสุก (ครัว)';
        hpRestore = 25;
        energyRestore = 95;
        desc = 'ต้มยำปลารสจัดจ้าน ฟื้นฟูพลังงาน +95 และ HP +25 (กด Space เพื่อซด)';
        sellPrice = 240;
    } else if (id === 'grilled_fish') {
        category = 'อาหารปรุงสุก (ครัว)';
        hpRestore = 15;
        energyRestore = 65;
        desc = 'ปลาย่างสดใหม่ ฟื้นฟูพลังงาน +65 และ HP +15 (กด Space เพื่อกิน)';
        sellPrice = 160;
    } else if (id === 'cheese') {
        category = 'ผลิตภัณฑ์นมแปรรูป';
        hpRestore = 10;
        energyRestore = 50;
        desc = 'ชีสก้อนเข้มข้น ทำจากนมวัวสด ฟื้นฟูพลังงาน +50 และ HP +10';
        sellPrice = 120;
    } else if (id === 'bread') {
        category = 'เบเกอรี่อบสด';
        hpRestore = 5;
        energyRestore = 40;
        desc = 'ขนมปังหอมนุ่ม ทำจากข้าวสาลี ฟื้นฟูพลังงาน +40 และ HP +5';
        sellPrice = 85;
    } else if (id === 'cookie') {
        category = 'ของหวานเบเกอรี่';
        hpRestore = 5;
        energyRestore = 35;
        desc = 'คุกกี้อบเนยกรอบ ฟื้นฟูพลังงาน +35 และ HP +5';
        sellPrice = 140;
    } else if (id === 'strawberry') {
        category = 'พืชผลสดทานเล่น';
        hpRestore = 10;
        energyRestore = 25;
        desc = 'สตรอว์เบอร์รี่หวานฉ่ำ กินสดฟื้นพลังงาน +25 และ HP +10 หรือใช้ทำเค้ก';
        sellPrice = 120;
    } else if (id === 'corn') {
        category = 'พืชผลสดทานเล่น';
        hpRestore = 8;
        energyRestore = 20;
        desc = 'ข้าวโพดหวาน กินสดฟื้นพลังงาน +20 และ HP +8';
        sellPrice = 75;
    } else if (id === 'carrot') {
        category = 'พืชผลสดทานเล่น';
        hpRestore = 5;
        energyRestore = 15;
        desc = 'แครอทสดกรอบ กินสดฟื้นพลังงาน +15 และ HP +5';
        sellPrice = 35;
    } else if (id === 'tomato') {
        category = 'พืชผลสดทานเล่น';
        hpRestore = 5;
        energyRestore = 12;
        desc = 'มะเขือเทศฉ่ำน้ำ กินสดฟื้นพลังงาน +12 และ HP +5 หรือใช้ทำพิซซ่า';
        sellPrice = 60;
    } else if (id === 'wheat') {
        category = 'พืชผลเกษตร';
        desc = 'ข้าวสาลีสีทอง สำหรับนำไปอบขนมปัง คุกกี้ หรือแปรรูปที่โรงสี';
        sellPrice = 25;
    } else if (id === 'golden_salmon' || id === 'salmon') {
        category = 'ปลาแม่น้ำสด';
        hpRestore = 15;
        energyRestore = 30;
        desc = 'ปลาแซลมอนสีทอง ตกได้ในแม่น้ำป่า กินสดฟื้น HP +15, พลังงาน +30';
        sellPrice = 150;
    } else if (id === 'ancient_glowfish' || id === 'golden_carp') {
        category = 'ปลาหายากในตำนาน';
        hpRestore = 60;
        energyRestore = 100;
        desc = 'ปลาเรืองแสงโบราณล้ำค่า ฟื้นฟู HP +60 และพลังงานเต็มเปี่ยม +100';
        sellPrice = 320;
    } else if (id === 'catfish') {
        category = 'ปลาบ่อน้ำสด';
        hpRestore = 10;
        energyRestore = 20;
        desc = 'ปลาดุกยักษ์หนวดงาม กินสดฟื้น HP +10 หรือนำไปทำต้มยำปลา';
        sellPrice = 80;
    } else if (id === 'tilapia') {
        category = 'ปลาสด';
        hpRestore = 5;
        energyRestore = 15;
        desc = 'ปลานิลเกล็ดเงิน กินสดฟื้น HP +5 หรือนำไปทำปลาย่างในครัว';
        sellPrice = 55;
    } else if (id === 'carp') {
        category = 'ปลาบ่อน้ำ';
        hpRestore = 5;
        energyRestore = 10;
        desc = 'ปลาคาร์ปหางยาว ตกได้จากบ่อน้ำในฟาร์ม ส่งขายหรือปล่อยเลี้ยง';
        sellPrice = 40;
    } else if (WEAPONS[id]) {
        const wep = WEAPONS[id];
        category = (wep.type === 'melee' || wep.type === 'melee_beam') ? 'อาวุธประชิด' : 'อาวุธยิงไกล';
        attackDmg = wep.damage;
        range = wep.range;
        desc = `${wep.desc} (กด Space หรือคลิก เพื่อโจมตี)`;
        sellPrice = id === 'excalibur_sword' ? 1500 : id === 'dragon_rifle' ? 950 : id === 'rifle' ? 350 : 150;
    } else if (id === 'hoe') {
        category = 'เครื่องมือเกษตร';
        desc = 'ใช้พรวนดินเพื่อลงแปลงปลูกผัก (ใช้ 2 พลังงาน)';
    } else if (id === 'water') {
        category = 'เครื่องมือเกษตร';
        desc = 'รดน้ำแปลงผักที่พรวนแล้ว / เติมน้ำที่บ่อน้ำ';
    } else if (id === 'scythe') {
        category = 'เครื่องมือเกษตร';
        desc = 'เก็บเกี่ยวพืชผลที่สุกเต็มที่ / คืนสภาพดินเป็นหญ้า';
    } else if (id === 'fishing_rod') {
        category = 'อุปกรณ์ตกปลา';
        desc = 'หันหน้าเข้าหาน้ำ กด Space หรือคลิก เพื่อเริ่มตกปลา';
    } else if (id.endsWith('_seed')) {
        category = 'เมล็ดพันธุ์พืช';
        const crop = CROPS[id.replace('_seed', '')];
        desc = crop ? `ปลูกลงบนดินที่พรวนแล้ว ใช้เวลาเติบโต ${crop.growDays} วัน (ได้รับ +${crop.xp} XP)` : 'เมล็ดพันธุ์สำหรับปลูกในแปลงดิน';
        sellPrice = Math.round((crop?.sellPrice || 20) * 0.4);
    } else if (WORLD_ITEMS[id] || MONSTER_DROPS[id]) {
        const mat = WORLD_ITEMS[id] || MONSTER_DROPS[id];
        category = 'แร่ & วัตถุดิบสร้างของ';
        desc = mat.desc || 'วัตถุดิบสำหรับหลอมอาวุธและปรุงยา';
        sellPrice = mat.sellPrice || 35;
    } else if (id === 'milk') {
        category = 'ผลผลิตสัตว์เลี้ยง';
        energyRestore = 20;
        desc = 'นมวัวสด ดื่มฟื้นพลังงาน +20 หรือนำไปทำชีสและเค้ก';
        sellPrice = 50;
    } else if (id === 'egg') {
        category = 'ผลผลิตสัตว์เลี้ยง';
        energyRestore = 15;
        desc = 'ไข่ไก่สด นำไปทำคุกกี้และเค้ก';
        sellPrice = 25;
    } else if (id === 'wool') {
        category = 'ผลผลิตสัตว์เลี้ยง';
        desc = 'ขนแกะนุ่มฟู สำหรับส่งขายหรือตัดเย็บ';
        sellPrice = 75;
    } else if (id === 'truffle') {
        category = 'ผลผลิตหายาก';
        desc = 'เห็ดทรัฟเฟิลดำ หมูขุดพบในฟาร์ม สินค้ามูลค่าสูง';
        sellPrice = 120;
    } else if (id === 'bacon') {
        category = 'อาหารแปรรูป';
        energyRestore = 35;
        desc = 'เบคอนรมควัน ทานฟื้นพลังงาน +35';
        sellPrice = 90;
    }

    const cons = this.getItemConsumableStats ? this.getItemConsumableStats(item) : null;
    const hungerRestore = cons ? cons.hungerRestore : 0;
    const thirstRestore = cons ? cons.thirstRestore : 0;
    if (cons) {
        if (cons.hpRestore) hpRestore = cons.hpRestore;
        if (cons.energyRestore) energyRestore = cons.energyRestore;
    }

    const quality = item.quality || 0;
    if (quality === 1) sellPrice = Math.round(sellPrice * 1.25);
    else if (quality === 2) sellPrice = Math.round(sellPrice * 1.50);
    else if (quality === 3) sellPrice = Math.round(sellPrice * 2.00);

    return {
        id,
        name,
        category,
        quality,
        hpRestore,
        energyRestore,
        hungerRestore,
        thirstRestore,
        attackDmg,
        range,
        desc,
        sellPrice,
        count: item.count
    };

};


Game.getItemTooltipText = function(item) {
    const data = this.getItemTooltipData(item);
    if (!data) return '';

    const qBadge = this.getQualityBadgeText ? this.getQualityBadgeText(item.quality) : '';
    const nameLine = qBadge ? `【${data.name} ${qBadge}】` : `【${data.name}】`;
    const lines = [nameLine];
    lines.push(`ประเภท: ${data.category}`);
    if (item.quality && item.quality > 0) {
        lines.push(item.quality === 1 ? 'คุณภาพระดับเงิน (+25% มูลค่า)' : item.quality === 2 ? 'คุณภาพระดับทอง (+50% มูลค่า)' : 'คุณภาพระดับอิริเดียม (+100% มูลค่า)');
    }
    if (data.hpRestore > 0) lines.push(`ฟื้นฟู HP: +${data.hpRestore}`);
    if (data.energyRestore > 0) lines.push(`ฟื้นฟูพลังงาน: +${data.energyRestore}`);
    if (data.hungerRestore > 0) lines.push(`ฟื้นฟูความอิ่ม: +${data.hungerRestore}`);
    if (data.thirstRestore > 0) lines.push(`ฟื้นฟูน้ำดื่ม: +${data.thirstRestore}`);
    if (data.attackDmg > 0) lines.push(`พลังโจมตี: ${data.attackDmg} dmg (ระยะ: ${data.range}px)`);
    if (data.desc) lines.push(data.desc);
    if (item.type !== 'tool' && !WEAPONS[data.id]) lines.push(`ราคาขาย: ${data.sellPrice} G / ชิ้น`);
    if (data.count !== undefined && data.count > 1) lines.push(`มีอยู่ในกระเป๋า: ${data.count} ชิ้น`);

    return lines.join('\n');
};


Game.showItemDetailCard = function(item) {
    const card = document.getElementById('inventoryItemDetailCard');
    if (!card) return;

    if (!item) {
        card.style.display = 'none';
        return;
    }

    const data = this.getItemTooltipData(item);
    if (!data) {
        card.style.display = 'none';
        return;
    }

    card.style.display = 'block';

    const iconEl = document.getElementById('detailItemIcon') as HTMLImageElement | null;
    if (iconEl) iconEl.src = SPRITES.getItemDataURL(data.id);

    const nameEl = document.getElementById('detailItemName');
    if (nameEl) nameEl.textContent = data.name;

    const typeEl = document.getElementById('detailItemTypeBadge');
    if (typeEl) typeEl.textContent = data.category;

    const statsRow = document.getElementById('detailItemStatsRow');
    if (statsRow) {
        let pillsHtml = '';
        if (data.hpRestore > 0) {
            pillsHtml += `<span class="stat-pill stat-pill-hp">HP +${data.hpRestore}</span>`;
        }
        if (data.energyRestore > 0) {
            pillsHtml += `<span class="stat-pill stat-pill-energy">พลังงาน +${data.energyRestore}</span>`;
        }
        if (data.hungerRestore > 0) {
            pillsHtml += `<span class="stat-pill stat-pill-hunger">อาหาร +${data.hungerRestore}</span>`;
        }
        if (data.thirstRestore > 0) {
            pillsHtml += `<span class="stat-pill stat-pill-thirst">น้ำดื่ม +${data.thirstRestore}</span>`;
        }
        if (data.attackDmg > 0) {
            pillsHtml += `<span class="stat-pill stat-pill-atk">โจมตี ${data.attackDmg} dmg</span>`;
        }
        if (item.type !== 'tool' && !WEAPONS[data.id]) {
            pillsHtml += `<span class="stat-pill stat-pill-gold">ขาย ${data.sellPrice} G</span>`;
        }
        if (data.count !== undefined) {
            pillsHtml += `<span class="stat-pill stat-pill-count">มี ${data.count} ชิ้น</span>`;
        }
        statsRow.innerHTML = pillsHtml;
    }

    const descEl = document.getElementById('detailItemDesc');
    if (descEl) descEl.textContent = data.desc || 'ไม่มีคำอธิบายเพิ่มเติม';

    const actionCont = document.getElementById('detailItemActionContainer');
    const consumeBtn = document.getElementById('detailItemConsumeBtn');
    const dropBtn = document.getElementById('detailItemDropBtn');

    this.selectedItemForDetailCard = { item, index: this.player.inventory.indexOf(item) };

    if (actionCont) {
        actionCont.style.display = 'flex';
        if (consumeBtn) {
            if (item.id && item.id.startsWith('ring_')) {
                consumeBtn.style.display = 'inline-block';
                consumeBtn.textContent = 'สวมใส่แหวนนี้ (Equip Ring)';
                consumeBtn.onclick = () => this.equipRing(item.id);
            } else if (item.id && ['kathuros_spore_armor', 'frostfang_frozen_plate', 'malakor_void_cloak'].includes(item.id)) {
                consumeBtn.style.display = 'inline-block';
                consumeBtn.textContent = 'สวมใส่เกราะบอสนี้ (Equip Armor)';
                consumeBtn.onclick = () => this.equipArmor(item.id);
            } else if (item.id && ['ignistron_flame_shield', 'astreon_storm_greaves', 'hydrakis_venom_pendant'].includes(item.id)) {
                consumeBtn.style.display = 'inline-block';
                consumeBtn.textContent = 'สวมใส่อุปกรณ์รองนี้ (Equip Shield/Gear)';
                consumeBtn.onclick = () => this.equipShield(item.id);
            } else if (this.isItemEdible(item)) {
                consumeBtn.style.display = 'inline-block';
                const stats = this.getItemConsumableStats(item);
                consumeBtn.textContent = stats?.isDrink ? 'ดื่มตอนนี้' : 'รับประทานตอนนี้';
                consumeBtn.onclick = () => this.consumeItemFromInventoryCard();
            } else {
                consumeBtn.style.display = 'none';
            }
        }
        if (dropBtn) {
            const isBaseTool = ['hoe', 'water'].includes(item.id);
            dropBtn.style.display = isBaseTool ? 'none' : 'inline-block';
            dropBtn.onclick = () => this.dropItemFromInventoryCard();
        }
    }
};


Game.consumeItemFromInventoryCard = function() {
    if (!this.selectedItemForDetailCard) return;
    const { item, index } = this.selectedItemForDetailCard;
    const slotIdx = index !== -1 ? index : this.player.inventory.indexOf(item);
    if (slotIdx === -1 || !this.player.inventory[slotIdx]) return;

    const eaten = this.consumeItem(this.player.inventory[slotIdx], slotIdx);
    if (eaten) {
        this.renderInventoryModal();
        const updatedItem = this.player.inventory[slotIdx];
        if (updatedItem) {
            this.showItemDetailCard(updatedItem);
        } else {
            const card = document.getElementById('inventoryItemDetailCard');
            if (card) card.style.display = 'none';
        }
    }
};


Game.dropItemFromInventoryCard = function() {
    if (!this.selectedItemForDetailCard) return;
    const { item, index } = this.selectedItemForDetailCard;
    const slotIdx = index !== -1 ? index : this.player.inventory.indexOf(item);
    if (slotIdx === -1 || !this.player.inventory[slotIdx]) return;

    const currentItem = this.player.inventory[slotIdx];
    const itemId = currentItem.id;
    const itemName = currentItem.name || (WORLD_ITEMS && WORLD_ITEMS[itemId]?.name) || itemId;
    const itemQuality = currentItem.quality || 0;

    // Calculate drop position in front of player
    let dropX = this.player.x + 12;
    let dropY = this.player.y + 16;
    if (this.player.direction === 'down') dropY += 24;
    else if (this.player.direction === 'up') dropY -= 20;
    else if (this.player.direction === 'left') dropX -= 22;
    else if (this.player.direction === 'right') dropX += 22;

    this.spawnDroppedItem(itemId, 1, dropX, dropY, itemQuality, true);
    this.removeItemFromInventory(itemId, 1);
    SoundEngine.step();
    this.addFloatingText(`ทิ้ง ${itemName} ลงพื้น (กด E หรือคลิกเพื่อเก็บ)`, dropX, dropY - 14, '#cbd5e1');

    this.renderInventoryModal();
    const updatedItem = this.player.inventory[slotIdx];
    if (updatedItem) {
        this.showItemDetailCard(updatedItem);
    } else {
        const card = document.getElementById('inventoryItemDetailCard');
        if (card) card.style.display = 'none';
        this.selectedItemForDetailCard = null;
    }
};


Game.renderInventoryModal = function() {
    const hotbarGrid = document.getElementById('inventoryHotbarGrid');
    const bagGrid = document.getElementById('inventoryBagGrid');
    if (!hotbarGrid || !bagGrid) return;
    hotbarGrid.innerHTML = '';
    bagGrid.innerHTML = '';

    const createSlotElement = (index: number, isHotbar: boolean) => {
        const item = this.player.inventory[index];
        const slot = document.createElement('div');
        slot.className = 'bag-slot' + (this.inventorySwapSource === index ? ' swap-source' : '');

        if (isHotbar) {
            const keyBadge = document.createElement('span');
            keyBadge.className = 'slot-hotbar-key';
            keyBadge.textContent = String((index + 1) % 10);
            slot.appendChild(keyBadge);
        }

        if (item) {
            const img = document.createElement('img');
            img.src = SPRITES.getItemDataURL(item.id);
            img.className = 'item-pixel-icon';
            img.draggable = false;
            slot.appendChild(img);

            if (item.count !== undefined) {
                const countBadge = document.createElement('span');
                countBadge.className = 'slot-count';
                countBadge.textContent = String(item.count);
                slot.appendChild(countBadge);
            }
            if (item.quality && item.quality > 0) {
                const starBadge = document.createElement('span');
                starBadge.className = 'slot-quality-star quality-' + item.quality;
                starBadge.textContent = item.quality === 1 ? '★' : item.quality === 2 ? '★★' : '★★★';
                starBadge.style.color = item.quality === 1 ? '#cbd5e1' : item.quality === 2 ? '#facc15' : '#c084fc';
                slot.appendChild(starBadge);
            }
            slot.title = this.getItemTooltipText(item);
        } else {
            slot.title = `ช่องว่าง ${index + 1} (ลากหรือคลิกไอเทมมาวางที่นี่)`;
        }

        slot.onmouseenter = () => {
            if (item) this.showItemDetailCard(item);
        };


        this.setupSlotInteractions(slot, index, item, () => {
            if (item) this.showItemDetailCard(item);
            if (this.inventorySwapSource === null) {
                if (!item) return; // empty slot, nothing to pick
                this.inventorySwapSource = index;
                SoundEngine.click();
                this.renderInventoryModal();
            } else if (this.inventorySwapSource === index) {
                // Deselect
                this.inventorySwapSource = null;
                SoundEngine.click();
                this.renderInventoryModal();
            } else {
                // Perform swap!
                const src = this.inventorySwapSource;
                this.swapInventorySlots(src, index);
            }
        });

        return slot;
    };


    // Render Hotbar slots (0..9)
    for (let i = 0; i < 10; i++) {
        hotbarGrid.appendChild(createSlotElement(i, true));
    }

    // Render Backpack slots dynamically according to expanded maxInventorySlots (24 -> 30 -> 36)
    const totalSlots = Math.max(this.player.maxInventorySlots || 24, this.player.inventory.length);
    while (this.player.inventory.length < totalSlots) {
        this.player.inventory.push(null);
    }

    const bagHeaderTag = document.querySelector('.section-tag-bag');
    if (bagHeaderTag) {
        bagHeaderTag.textContent = `ช่องเก็บของในกระเป๋าเป้ (ช่อง 11 - ${totalSlots})`;
    }

    for (let i = 10; i < totalSlots; i++) {
        bagGrid.appendChild(createSlotElement(i, false));
    }

    // Render Armor Slot
    const armorEl = document.getElementById('armorSlot');
    if (armorEl) {
        armorEl.innerHTML = '';
        const armorId = this.player.equippedArmor;
        if (armorId) {
            armorEl.className = 'ring-slot filled';
            const img = document.createElement('img');
            img.src = SPRITES.getItemDataURL(armorId);
            img.className = 'item-pixel-icon';
            armorEl.appendChild(img);
            const info = WORLD_ITEMS[armorId];
            armorEl.title = `${info?.name || armorId}\n${info?.desc || ''}\n(คลิกเพื่อถอดเกราะ)`;
        } else {
            armorEl.className = 'ring-slot';
            armorEl.innerHTML = '<span style="font-size: 10px; font-weight: bold; opacity: 0.6;">ARMOR</span>';
            armorEl.title = 'ช่องชุดเกราะบอส (คลิกชุดเกราะในกระเป๋าเพื่อสวมใส่)';
        }
    }

    // Render Shield / Offhand Slot
    const shieldEl = document.getElementById('shieldSlot');
    if (shieldEl) {
        shieldEl.innerHTML = '';
        const shieldId = this.player.equippedShield;
        if (shieldId) {
            shieldEl.className = 'ring-slot filled';
            const img = document.createElement('img');
            img.src = SPRITES.getItemDataURL(shieldId);
            img.className = 'item-pixel-icon';
            shieldEl.appendChild(img);
            const info = WORLD_ITEMS[shieldId];
            shieldEl.title = `${info?.name || shieldId}\n${info?.desc || ''}\n(คลิกเพื่อถอดอุปกรณ์)`;
        } else {
            shieldEl.className = 'ring-slot';
            shieldEl.innerHTML = '<span style="font-size: 10px; font-weight: bold; opacity: 0.6;">SHIELD</span>';
            shieldEl.title = 'ช่องโล่/อุปกรณ์บอส (คลิกในกระเป๋าเพื่อสวมใส่)';
        }
    }

    // Render Equipped Ring Slots (ringSlot0, ringSlot1)
    if (!this.player.equippedRings) this.player.equippedRings = [null, null];
    [0, 1].forEach((sIdx: number) => {
        const ringEl = document.getElementById('ringSlot' + sIdx);
        if (ringEl) {
            ringEl.innerHTML = '';
            const ringId = this.player.equippedRings[sIdx];
            if (ringId) {
                ringEl.className = 'ring-slot filled';
                const img = document.createElement('img');
                img.src = SPRITES.getItemDataURL(ringId);
                img.className = 'item-pixel-icon';
                ringEl.appendChild(img);
                const info = WORLD_ITEMS[ringId];
                ringEl.title = `${info?.name || ringId}\n${info?.desc || ''}\n(คลิกเพื่อถอดแหวน)`;
            } else {
                ringEl.className = 'ring-slot';
                ringEl.innerHTML = '<span style="font-size: 11px; font-weight: bold; opacity: 0.5;">RING</span>';
                ringEl.title = `ช่องแหวน ${sIdx + 1} (คลิกแหวนในกระเป๋าเพื่อสวมใส่)`;
            }
        }
    });

    // Show details of currently selected hotbar item or first available item
    const initialItem = this.player.inventory[this.player.selectedSlot] || this.player.inventory.find(it => it !== null);
    if (initialItem) {
        this.showItemDetailCard(initialItem);
    }
};


Game.hasRing = function(ringId: string): boolean {
    if (!this.player.equippedRings) return false;
    return this.player.equippedRings[0] === ringId || this.player.equippedRings[1] === ringId;
};

Game.equipRing = function(ringId: string, targetSlot: number = -1) {
    if (!this.player.equippedRings) this.player.equippedRings = [null, null];
    const invIdx = this.player.inventory.findIndex((it: any) => it && it.id === ringId);
    if (invIdx === -1) return;

    if (targetSlot === -1) {
        if (!this.player.equippedRings[0]) targetSlot = 0;
        else if (!this.player.equippedRings[1]) targetSlot = 1;
        else targetSlot = 0;
    }

    const oldRing = this.player.equippedRings[targetSlot];
    this.player.equippedRings[targetSlot] = ringId;
    this.player.inventory[invIdx] = oldRing ? { id: oldRing, name: WORLD_ITEMS[oldRing]?.name || oldRing, count: 1 } : null;

    if (SoundEngine.craft) SoundEngine.craft();
    const ringName = WORLD_ITEMS[ringId]?.name || ringId;
    this.addFloatingText(' สวมใส่ ' + ringName, this.player.x, this.player.y - 15, '#facc15');
    this.renderInventoryModal();
    this.updateHUD();
};

Game.unequipRing = function(slotIdx: 0 | 1) {
    if (!this.player.equippedRings || !this.player.equippedRings[slotIdx]) return;
    const ringId = this.player.equippedRings[slotIdx];

    const emptyIdx = this.player.inventory.findIndex((it: any) => it === null);
    if (emptyIdx === -1) {
        this.addFloatingText('กระเป๋าเต็ม ไม่สามารถถอดแหวนได้!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }

    this.player.inventory[emptyIdx] = { id: ringId, name: WORLD_ITEMS[ringId]?.name || ringId, count: 1 };
    this.player.equippedRings[slotIdx] = null;

    if (SoundEngine.itemPop) SoundEngine.itemPop();
    const ringName = WORLD_ITEMS[ringId]?.name || ringId;
    this.addFloatingText('ถอด ' + ringName, this.player.x, this.player.y - 15, '#cbd5e1');
    this.renderInventoryModal();
    this.updateHUD();
};

Game.equipArmor = function(armorId: string) {
    const invIdx = this.player.inventory.findIndex((it: any) => it && it.id === armorId);
    if (invIdx === -1) return;

    const oldArmor = this.player.equippedArmor;
    this.player.equippedArmor = armorId;
    this.player.inventory[invIdx] = oldArmor ? { id: oldArmor, name: WORLD_ITEMS[oldArmor]?.name || oldArmor, count: 1 } : null;

    if (SoundEngine.craft) SoundEngine.craft();
    const aName = WORLD_ITEMS[armorId]?.name || armorId;
    this.addFloatingText('★ สวมใส่ ' + aName, this.player.x, this.player.y - 15, '#38bdf8');
    this.renderInventoryModal();
    this.updateHUD();
};

Game.unequipArmor = function() {
    if (!this.player.equippedArmor) return;
    const armorId = this.player.equippedArmor;
    const emptyIdx = this.player.inventory.findIndex((it: any) => it === null);
    if (emptyIdx === -1) {
        this.addFloatingText('★ กระเป๋าเต็ม ไม่สามารถถอดชุดเกราะได้!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }
    this.player.inventory[emptyIdx] = { id: armorId, name: WORLD_ITEMS[armorId]?.name || armorId, count: 1 };
    this.player.equippedArmor = null;
    if (SoundEngine.itemPop) SoundEngine.itemPop();
    this.renderInventoryModal();
    this.updateHUD();
};

Game.equipShield = function(shieldId: string) {
    const invIdx = this.player.inventory.findIndex((it: any) => it && it.id === shieldId);
    if (invIdx === -1) return;

    const oldShield = this.player.equippedShield;
    this.player.equippedShield = shieldId;
    this.player.inventory[invIdx] = oldShield ? { id: oldShield, name: WORLD_ITEMS[oldShield]?.name || oldShield, count: 1 } : null;

    if (SoundEngine.craft) SoundEngine.craft();
    const sName = WORLD_ITEMS[shieldId]?.name || shieldId;
    this.addFloatingText('★ สวมใส่ ' + sName, this.player.x, this.player.y - 15, '#fbbf24');
    this.renderInventoryModal();
    this.updateHUD();
};

Game.unequipShield = function() {
    if (!this.player.equippedShield) return;
    const shieldId = this.player.equippedShield;
    const emptyIdx = this.player.inventory.findIndex((it: any) => it === null);
    if (emptyIdx === -1) {
        this.addFloatingText('★ กระเป๋าเต็ม ไม่สามารถถอดอุปกรณ์ได้!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }
    this.player.inventory[emptyIdx] = { id: shieldId, name: WORLD_ITEMS[shieldId]?.name || shieldId, count: 1 };
    this.player.equippedShield = null;
    if (SoundEngine.itemPop) SoundEngine.itemPop();
    this.renderInventoryModal();
    this.updateHUD();
};

Game.sortInventory = function() {
    if (!this.player || !this.player.inventory) return;

    const getCategory = (it: any): number => {
        if (!it) return 99;
        const id = it.id;
        if (['hoe', 'water', 'watering_can', 'axe', 'pickaxe', 'scythe', 'fishing_rod', 'horse_whistle'].includes(id)) return 0;
        if (WEAPONS[id] || id.startsWith('ring_') || id.includes('sword') || id.includes('bow') || id.includes('axe') || id.includes('scythe') || id.includes('blade') || id.includes('hammer') || id.includes('rifle')) return 1;
        if (id.endsWith('_seed') || id === 'sapling') return 2;
        if (CROPS[id] || ['blight_spore', 'starflower_herb', 'swamp_herb', 'frost_berry', 'coconut'].includes(id)) return 3;
        if (['mayonnaise', 'strawberry_jam', 'pickled_carrot', 'fine_wine', 'craft_ale', 'aged_cheese', 'farmer_stew', 'vigor_juice', 'herbal_defense_soup', 'health_potion', 'antidote_serum'].includes(id)) return 4;
        if (['iron_ore', 'gold_ore', 'ruby_gem', 'diamond_crystal', 'mana_gem', 'crystal_core', 'shadow_pelt', 'wolf_fang', 'bat_wing', 'demon_heart', 'crown_of_despair', 'luminarch_crystal_heart', 'hydra_venom_gland', 'hydra_scale', 'magma_dragon_horn', 'flame_heart', 'glacial_titan_core', 'frost_crystal', 'death_lord_soul', 'cursed_relic'].includes(id)) return 5;
        if (['wood', 'chest', 'pet_basket'].includes(id)) return 6;
        return 7;
    };

    const nonNullItems: any[] = [];
    for (const item of this.player.inventory) {
        if (!item) continue;
        if (item.count !== undefined) {
            const existing = nonNullItems.find(x => x.id === item.id && x.quality === item.quality);
            if (existing && existing.count !== undefined) {
                existing.count += item.count;
                continue;
            }
        }
        nonNullItems.push(Object.assign({}, item));
    }

    nonNullItems.sort((a, b) => {
        const catA = getCategory(a);
        const catB = getCategory(b);
        if (catA !== catB) return catA - catB;
        return a.id.localeCompare(b.id);
    });

    const totalSlots = Math.max(this.player.maxInventorySlots || 24, this.player.inventory.length);
    const newInv: any[] = [];
    for (let i = 0; i < totalSlots; i++) {
        newInv.push(nonNullItems[i] || null);
    }
    this.player.inventory = newInv;

    if (SoundEngine.sortSound) SoundEngine.sortSound();
    else if (SoundEngine.itemPop) SoundEngine.itemPop();
    this.addFloatingText(' จัดระเบียบกระเป๋าสำเร็จ!', this.player.x, this.player.y - 15, '#38bdf8');
    this.renderInventoryModal();
    this.updateHUD();
};

Game.sortChest = function() {
    if (!this.currentOpenChestId) return;
    const chest = this.placedChests[this.currentOpenChestId];
    if (!chest) return;

    const getCategory = (it: any): number => {
        if (!it) return 99;
        const id = it.id;
        if (['hoe', 'water', 'watering_can', 'axe', 'pickaxe', 'scythe', 'fishing_rod', 'horse_whistle'].includes(id)) return 0;
        if (WEAPONS[id] || id.startsWith('ring_') || id.includes('sword') || id.includes('bow')) return 1;
        if (id.endsWith('_seed') || id === 'sapling') return 2;
        if (CROPS[id] || ['blight_spore', 'starflower_herb', 'swamp_herb', 'frost_berry'].includes(id)) return 3;
        if (['mayonnaise', 'strawberry_jam', 'pickled_carrot', 'fine_wine', 'craft_ale', 'aged_cheese', 'farmer_stew', 'vigor_juice', 'herbal_defense_soup', 'health_potion', 'antidote_serum'].includes(id)) return 4;
        return 5;
    };

    const nonNullItems: any[] = [];
    for (const item of chest.slots) {
        if (!item) continue;
        if (item.count !== undefined) {
            const existing = nonNullItems.find(x => x.id === item.id && x.quality === item.quality);
            if (existing && existing.count !== undefined) {
                existing.count += item.count;
                continue;
            }
        }
        nonNullItems.push(Object.assign({}, item));
    }

    nonNullItems.sort((a, b) => {
        const catA = getCategory(a);
        const catB = getCategory(b);
        if (catA !== catB) return catA - catB;
        return a.id.localeCompare(b.id);
    });

    const newSlots: any[] = [];
    for (let i = 0; i < 16; i++) {
        newSlots.push(nonNullItems[i] || null);
    }
    chest.slots = newSlots;

    if (SoundEngine.sortSound) SoundEngine.sortSound();
    else if (SoundEngine.itemPop) SoundEngine.itemPop();
    this.addFloatingText(' จัดระเบียบหีบสำเร็จ!', this.player.x, this.player.y - 15, '#38bdf8');
    this.renderStorageChestModal();
    this.updateHUD();
};


// ========================================================
// 14. FARM DEFENSE & HUNTERS SYSTEM (นายพราน & ยิงแมลงปีศาจ)
// ========================================================

// Helper: auto-switch to any available weapon in inventory if active slot is a tool or empty
Game.ensureWeaponEquippedInCombat = function() {
    if (!this.player || !Array.isArray(this.player.inventory)) return false;
    const cur = this.player.inventory[this.player.selectedSlot];
    if (cur && (cur.type === 'weapon' || (typeof WEAPONS !== 'undefined' && WEAPONS[cur.id]))) {
        return true;
    }
    const wIdx = this.player.inventory.findIndex((it: any) => it && (it.type === 'weapon' || (typeof WEAPONS !== 'undefined' && WEAPONS[it.id])));
    if (wIdx >= 0) {
        this.selectHotbarSlot(wIdx % 10);
        this.updateHUD();
        return true;
    }
    return false;
};

// Smart Auto-Aim: Finds the closest hostile enemy/boss in range for seamless mobile & keyboard combat
Game.findNearestCombatTarget = function(maxDist = 720) {
    if (!this.player || !this.isCombatScene()) return null;
    const px = this.player.x + 12;
    const py = this.player.y + 14;

    let nearest: { x: number; y: number; dist: number; type: string; entity: any } | null = null;
    let minDist = maxDist;

    // 1. Boss: Highest priority if active and alive (covers full mobile widescreen up to 950px)
    if (this.boss && this.boss.alive && this.boss.active) {
        const bw = this.boss.width || 64;
        const bh = this.boss.height || 64;
        const bx = this.boss.x + bw / 2;
        const by = this.boss.y + bh / 2;
        const d = Math.hypot(bx - px, by - py);
        if (d <= maxDist + 220) {
            return { x: bx, y: by, dist: d, type: 'boss', entity: this.boss };
        }
    }

    // 2. World Monsters (Dungeon, Swamp, Cave, Island, Volcano, Spire)
    if (this.worldMonsters && this.worldMonsters.length > 0) {
        for (let i = 0; i < this.worldMonsters.length; i++) {
            const m = this.worldMonsters[i];
            if (!m || m.alive === false || (m.hp !== undefined && m.hp <= 0)) continue;
            const mw = m.width || 32;
            const mh = m.height || 32;
            const mx = m.x + mw / 2;
            const my = m.y + mh / 2;
            const d = Math.hypot(mx - px, my - py);
            if (d < minDist) {
                minDist = d;
                nearest = { x: mx, y: my, dist: d, type: 'monster', entity: m };
            }
        }
    }

    // 3. Farm Demon Bugs
    if (this.currentScene === 'farm' && this.demonBugs && this.demonBugs.length > 0) {
        for (let i = 0; i < this.demonBugs.length; i++) {
            const bug = this.demonBugs[i];
            if (!bug || (bug.hp !== undefined && bug.hp <= 0)) continue;
            const bx = bug.x + 14;
            const by = bug.y + 14;
            const d = Math.hypot(bx - px, by - py);
            if (d < minDist) {
                minDist = d;
                nearest = { x: bx, y: by, dist: d, type: 'bug', entity: bug };
            }
        }
    }

    return nearest;
};

Game.playerAttackAt = function(targetWorldX, targetWorldY) {
    if (!this.isCombatScene()) {
        this.addFloatingText('ไม่สามารถใช้อาวุธในอาคารได้', this.player.x, this.player.y - 15, '#fca5a5');
        return;
    }
    if (this.playerShootCooldown > 0) return;

    const selectedItem = this.player.inventory[this.player.selectedSlot];
    let weapon = (selectedItem && WEAPONS[selectedItem.id]) ? WEAPONS[selectedItem.id] : WEAPONS.slingshot;

    if (weapon.type === 'melee' || weapon.type === 'melee_beam') {
        this.playerMeleeAttack(targetWorldX, targetWorldY, weapon);
    } else {
        this.playerShootAt(targetWorldX, targetWorldY, weapon);
    }
};


Game.playerMeleeAttack = function(targetWorldX, targetWorldY, weapon) {
    const originX = this.player.x + 12;
    const originY = this.player.y + 14;
    const dx = targetWorldX - originX;
    const dy = targetWorldY - originY;
    const angle = Math.atan2(dy, dx);

    if (Math.abs(dx) > Math.abs(dy)) {
        this.player.direction = dx > 0 ? 'right' : 'left';
    } else {
        this.player.direction = dy > 0 ? 'down' : 'up';
    }

    // 3-Hit Combat Combo System
    const now = performance.now();
    if (!this.player.lastAttackTime || (now - this.player.lastAttackTime > 1100)) {
        this.player.comboStep = 1;
    } else {
        this.player.comboStep = ((this.player.comboStep || 1) % 3) + 1;
    }
    this.player.lastAttackTime = now;
    const combo = this.player.comboStep;

    let comboMult = 1.0;
    let comboCooldownMult = 1.0;
    let forceCrit = false;

    if (combo === 1) {
        comboMult = 1.0;
        comboCooldownMult = 0.88;
        SoundEngine.swordSlash(1);
    } else if (combo === 2) {
        comboMult = 1.25;
        comboCooldownMult = 0.92;
        SoundEngine.swordSlash(2);
        this.addFloatingText('[2x COMBO!]', originX, originY - 24, '#38bdf8');
    } else if (combo === 3) {
        comboMult = 1.75;
        comboCooldownMult = 1.15;
        forceCrit = true;
        this.triggerScreenShake(5.0, 150);
        this.spawnParticles(originX, originY, '#facc15', 20);
        this.spawnParticles(originX, originY, '#ffffff', 14);
        if (typeof SoundEngine.comboFinisher === 'function') SoundEngine.comboFinisher();
        else SoundEngine.swordSlash(3);
        this.addFloatingText('★ 3x FINISHER CRIT! ★', originX - 25, originY - 28, '#fde047');
    }

    this.playerShootCooldown = Math.round((weapon.cooldown || 250) * comboCooldownMult);
    this.meleeSlashAnim = {
        x: originX,
        y: originY,
        angle: angle,
        dir: this.player.direction,
        isHoly: (weapon.id === 'excalibur_sword' || weapon.id === 'luminarch_crystal_blade'),
        timer: combo === 3 ? 210 : 160,
        maxTimer: combo === 3 ? 210 : 160,
        comboStep: combo
    };

    const attackRange = (weapon.range || 65) + (combo === 3 ? 18 : 0);
    const hasWarrior = (typeof this.hasRing === 'function' && this.hasRing('ring_warrior'));
    const forgeEnchant = (this.player.volcanoForgeEnchant || 0) * 30;
    const forgeCrit = (this.player.volcanoForgeEnchant || 0) * 0.15;
    const baseCrit = (this.player.skillMastery?.critical_edge ? 0.38 : 0.22) + forgeCrit;
    const buffCrit = this.player.buffs?.critBonus || 0;
    const critRate = (hasWarrior ? baseCrit + 0.18 : baseCrit) + buffCrit;
    const baseMult = this.player.skillMastery?.critical_edge ? 2.5 : 1.8;
    const critMult = hasWarrior ? baseMult + 0.4 : baseMult;
    const isCrit = forceCrit || (Math.random() < critRate);
    const bonusDmg = (this.player.buffs?.damage || 0) + forgeEnchant;
    const isWellFed = (this.player.hunger !== undefined ? this.player.hunger : 100) >= 75 &&
                      (this.player.thirst !== undefined ? this.player.thirst : 100) >= 75;
    const wellFedBonus = isWellFed ? 1.15 : 1.0;
    const finalDamage = Math.round((weapon.damage + bonusDmg) * comboMult * (isCrit ? critMult : 1.0) * wellFedBonus);

    // Check hit on breakables (Urns / Crates)
    if (typeof this.checkBreakablesInArea === 'function') {
        this.checkBreakablesInArea(targetWorldX, targetWorldY, attackRange);
    }

    // Check hit on Farm Demon Bugs
    if (this.currentScene === 'farm') {
        for (let bIdx = this.demonBugs.length - 1; bIdx >= 0; bIdx--) {
            const bug = this.demonBugs[bIdx];
            const dist = Math.hypot((bug.x + 14) - originX, (bug.y + 14) - originY);
            if (dist < attackRange) {
                bug.hp -= finalDamage;
                bug.flashTimer = 160;
                bug.squashX = 1.35;
                bug.squashY = 0.72;
                bug.x += Math.cos(angle) * (isCrit ? 18 : 10);
                bug.y += Math.sin(angle) * (isCrit ? 18 : 10);

                this.triggerScreenShake(isCrit ? 5.5 : 3.5, 120);
                this.triggerHitstop(isCrit ? 60 : 40);
                if (isCrit) SoundEngine.critHit(); else SoundEngine.hit();

                this.spawnParticles(bug.x + 14, bug.y + 14, isCrit ? '#facc15' : '#ef4444', isCrit ? 14 : 8);
                this.addFloatingText((isCrit ? ' CRIT -' : ' -') + finalDamage, bug.x, bug.y - 10, isCrit ? '#fde047' : '#ef4444');
                if (bug.hp <= 0) {
                    SoundEngine.monsterDie();
                    this.spawnParticles(bug.x + 14, bug.y + 14, '#9333ea', 18);
                    this.player.gold += bug.loot.gold;
                    this.spawnDroppedItem(bug.loot.item, 1, bug.x, bug.y);
                    this.addXp(bug.loot.xp);
                    this.player.questProgress.bugsDefeated = (this.player.questProgress.bugsDefeated || 0) + 1;
                    this.spawnDroppedItem('blight_spore', 1, bug.x, bug.y);
                    this.player.questProgress.sporesCollected = (this.player.questProgress.sporesCollected || 0) + 1;
                    this.addFloatingText('ดรอป: สปอร์กลายพันธุ์', bug.x, bug.y - 12, '#c084fc');
                    this.demonBugs.splice(bIdx, 1);
                    this.updateHUD();
                }
            }
        }
    }

    // Check hit on World Monsters across ALL combat scenes
    if (this.currentScene !== 'farm') {
        for (let mIdx = this.worldMonsters.length - 1; mIdx >= 0; mIdx--) {
            const m = this.worldMonsters[mIdx];
            const dist = Math.hypot((m.x + 14) - originX, (m.y + 12) - originY);
            if (dist < attackRange) {
                m.hp -= finalDamage;
                this.applyRuneCombatProc(m, finalDamage);
                m.flashTimer = 160;
                m.squashX = 1.35;
                m.squashY = 0.72;
                m.x += Math.cos(angle) * (isCrit ? 18 : 10);
                m.y += Math.sin(angle) * (isCrit ? 18 : 10);

                this.triggerScreenShake(isCrit ? 5.5 : 3.5, 120);
                this.triggerHitstop(isCrit ? 60 : 40);
                if (isCrit) SoundEngine.critHit(); else SoundEngine.hit();

                // Lifesteal on hit for Malakor Soul Scythe & Vampiric Ring
                if (weapon.id === 'malakor_soul_scythe') {
                    const heal = Math.max(3, Math.round(finalDamage * 0.08));
                    this.player.hp = Math.min(this.player.maxHp, this.player.hp + heal);
                    this.addFloatingText(' +' + heal + ' HP (ดูดวิญญาณ)', this.player.x, this.player.y - 18, '#c084fc');
                    this.spawnParticles(this.player.x + 12, this.player.y + 14, '#c084fc', 8);
                } else if (typeof this.hasRing === 'function' && this.hasRing('ring_vampiric')) {
                    const heal = Math.max(1, Math.round(finalDamage * 0.04));
                    this.player.hp = Math.min(this.player.maxHp, this.player.hp + heal);
                    this.addFloatingText(' +' + heal + ' HP', this.player.x, this.player.y - 14, '#4ade80');
                    this.spawnParticles(this.player.x + 12, this.player.y + 14, '#ef4444', 6);
                }

                // Malakor Void Shroud: Soul leech on attack
                if (this.player.equippedArmor === 'malakor_void_cloak') {
                    const heal = Math.max(3, Math.round(finalDamage * 0.06));
                    this.player.hp = Math.min(this.player.maxHp || 100, this.player.hp + heal);
                    this.addFloatingText(' +' + heal + ' HP (มฤตยูดูดเลือด)', this.player.x, this.player.y - 18, '#c084fc');
                    this.spawnParticles(this.player.x + 12, this.player.y + 14, '#c084fc', 8);
                }

                // Hydrakis Venom Amulet: Poison strike on hit
                if (this.player.equippedShield === 'hydrakis_venom_pendant') {
                    this.boss.poisonTimer = 3500;
                    this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#22c55e', 8);
                    this.addFloatingText('★ พิษไฮดรา!', this.boss.x + 16, this.boss.y - 18, '#4ade80');
                }

                this.spawnParticles(m.x + 14, m.y + 12, isCrit ? '#facc15' : '#ef4444', isCrit ? 14 : 8);
                this.addFloatingText((isCrit ? ' CRIT -' : ' -') + finalDamage, m.x, m.y - 12, isCrit ? '#fde047' : '#ef4444');

                if (m.hp <= 0) {
                    SoundEngine.monsterDie();
                    this.spawnParticles(m.x + 14, m.y + 12, '#7e22ce', 20);
                    const cfg = WORLD_MONSTERS[m.type];
                    if (cfg) {
                        const goldMult = (typeof this.hasRing === 'function' && this.hasRing('ring_lucky')) ? 1.35 : 1.0;
                        const earnedGold = Math.round(cfg.gold * goldMult);
                        this.player.gold += earnedGold;
                        this.addXp(cfg.xp);
                        cfg.drops.forEach(d => {
                            const dropBonus = (typeof this.hasRing === 'function' && this.hasRing('ring_lucky')) ? 0.15 : 0.0;
                            if (Math.random() <= d.chance + dropBonus) {
                                this.spawnDroppedItem(d.item, 1, m.x, m.y);
                                const dName = (WORLD_ITEMS && WORLD_ITEMS[d.item]?.name) || d.item;
                                this.addFloatingText('ดรอป: ' + dName, m.x, m.y - 12, '#facc15');
                            }
                        });
                        if (m.type === 'shadow_wolf') {
                            this.player.questProgress.wolvesKilled = (this.player.questProgress.wolvesKilled || 0) + 1;
                        }
                        if (this.currentScene === 'cave') {
                            this.player.questProgress.caveMonstersDefeated = (this.player.questProgress.caveMonstersDefeated || 0) + 1;
                        }
                        this.addFloatingText('+' + earnedGold + ' G ' + cfg.name + ' ถูกปราบ! (+' + cfg.xp + ' XP)' + (goldMult > 1 ? ' (โชคลาภ)' : ''), m.x - 20, m.y - 20, '#4ade80');
                    }
                    this.worldMonsters.splice(mIdx, 1);
                    this.updateHUD();
                }
            }
        }

        // Check hit on Remote Players in PvP (Multiplayer Dueling)
        if (this.remotePlayers && (this.currentScene === 'pvp_arena' || this.isPvPEnabled)) {
            for (const pid in this.remotePlayers) {
                const rp = this.remotePlayers[pid];
                if (!rp || rp.scene !== this.currentScene || rp.hp <= 0) continue;
                const distP = Math.hypot((rp.x + 12) - originX, (rp.y + 14) - originY);
                if (distP < attackRange + 10) {
                    let pvpDmg = finalDamage;
                    if (rp.isGuarding) pvpDmg = Math.round(pvpDmg * 0.4);
                    if (typeof (window as any).Multiplayer !== 'undefined') {
                        (window as any).Multiplayer.sendPvPHit(pid, pvpDmg, isCrit, angle, weapon.name || weapon.id);
                    }
                    this.triggerScreenShake(isCrit ? 6.5 : 4.0, 140);
                    this.triggerHitstop(isCrit ? 60 : 40);
                    if (isCrit) SoundEngine.critHit(); else SoundEngine.hit();
                    this.spawnParticles(rp.x + 12, rp.y + 14, isCrit ? '#fde047' : '#ef4444', isCrit ? 16 : 10);
                    this.addFloatingText((isCrit ? 'CRIT -' : '-') + pvpDmg, rp.x, rp.y - 15, isCrit ? '#fde047' : '#ef4444');
                    break;
                }
            }
        }

        // Check hit on Bosses
        if (this.boss && this.boss.alive) {
            const distBoss = Math.hypot((this.boss.x + 32) - originX, (this.boss.y + 32) - originY);
            if (distBoss < attackRange + 30) {
                this.boss.hp -= finalDamage;
                this.applyRuneCombatProc(this.boss, finalDamage);
                this.boss.flashTimer = 180;
                this.boss.squashX = 1.25;
                this.boss.squashY = 0.8;
                this.triggerScreenShake(isCrit ? 7.0 : 4.5, 160);
                this.triggerHitstop(isCrit ? 70 : 45);
                if (isCrit) SoundEngine.critHit(); else SoundEngine.hit();

                // Lifesteal on boss hit for Malakor Soul Scythe & Vampiric Ring
                if (weapon.id === 'malakor_soul_scythe') {
                    const heal = Math.max(4, Math.round(finalDamage * 0.08));
                    this.player.hp = Math.min(this.player.maxHp, this.player.hp + heal);
                    this.addFloatingText(' +' + heal + ' HP (ดูดวิญญาณ)', this.player.x, this.player.y - 18, '#c084fc');
                    this.spawnParticles(this.player.x + 12, this.player.y + 14, '#c084fc', 8);
                } else if (typeof this.hasRing === 'function' && this.hasRing('ring_vampiric')) {
                    const heal = Math.max(1, Math.round(finalDamage * 0.04));
                    this.player.hp = Math.min(this.player.maxHp, this.player.hp + heal);
                    this.addFloatingText(' +' + heal + ' HP', this.player.x, this.player.y - 14, '#4ade80');
                    this.spawnParticles(this.player.x + 12, this.player.y + 14, '#ef4444', 6);
                }

                // Malakor Void Shroud: Soul leech on attack
                if (this.player.equippedArmor === 'malakor_void_cloak') {
                    const heal = Math.max(3, Math.round(finalDamage * 0.06));
                    this.player.hp = Math.min(this.player.maxHp || 100, this.player.hp + heal);
                    this.addFloatingText(' +' + heal + ' HP (มฤตยูดูดเลือด)', this.player.x, this.player.y - 18, '#c084fc');
                    this.spawnParticles(this.player.x + 12, this.player.y + 14, '#c084fc', 8);
                }

                // Hydrakis Venom Amulet: Poison strike on hit
                if (this.player.equippedShield === 'hydrakis_venom_pendant') {
                    this.boss.poisonTimer = 3500;
                    this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#22c55e', 8);
                    this.addFloatingText('★ พิษไฮดรา!', this.boss.x + 16, this.boss.y - 18, '#4ade80');
                }

                this.spawnParticles(originX + Math.cos(angle) * 35, originY + Math.sin(angle) * 35, isCrit ? '#facc15' : '#f59e0b', 14);
                this.addFloatingText((isCrit ? ' CRIT -' : ' -') + finalDamage, this.boss.x + 20, this.boss.y - 10, isCrit ? '#fde047' : '#ef4444');
                if (this.boss.hp <= 0) {
                    this.defeatBoss();
                }
            }
        }
    }

    // Boss Legendary Weapons & Excalibur Projectiles (Spawns ahead of melee arc to prevent double-dipping)
    const projDmg = weapon.damage + bonusDmg;
    const beamOriginX = originX + Math.cos(angle) * 36;
    const beamOriginY = originY + Math.sin(angle) * 36;

    if (weapon.id === 'excalibur_sword') {
        this.projectiles.push({
            x: beamOriginX,
            y: beamOriginY,
            vx: Math.cos(angle) * 12,
            vy: Math.sin(angle) * 12,
            angle: angle,
            damage: projDmg,
            rangeLeft: weapon.range,
            type: 'holy_beam',
            fromPlayer: true
        });
    } else if (weapon.id === 'luminarch_crystal_blade') {
        this.projectiles.push({
            x: beamOriginX,
            y: beamOriginY,
            vx: Math.cos(angle) * 14,
            vy: Math.sin(angle) * 14,
            angle: angle,
            damage: projDmg,
            rangeLeft: weapon.range,
            type: 'crystal_shard',
            fromPlayer: true
        });
        SoundEngine.shoot(true);
    } else if (weapon.id === 'volcano_sword' || weapon.id === 'volcano_magma_axe' || weapon.id === 'volcano_flame_sword') {
        this.projectiles.push({
            x: beamOriginX,
            y: beamOriginY,
            vx: Math.cos(angle) * 11,
            vy: Math.sin(angle) * 11,
            angle: angle,
            damage: projDmg,
            rangeLeft: weapon.range,
            type: 'dragon_fire',
            fromPlayer: true
        });
        this.triggerScreenShake(3.5, 90);
        this.spawnParticles(beamOriginX, beamOriginY, '#f97316', 10);
        SoundEngine.thunder();
    } else if (weapon.id === 'glacial_titan_hammer') {
        [-0.15, 0.15].forEach(offset => {
            const a = angle + offset;
            this.projectiles.push({
                x: beamOriginX,
                y: beamOriginY,
                vx: Math.cos(a) * 11,
                vy: Math.sin(a) * 11,
                angle: a,
                damage: Math.round(projDmg * 0.75),
                rangeLeft: weapon.range,
                type: 'ice_shard',
                fromPlayer: true
            });
        });
        this.triggerScreenShake(3.5, 90);
        this.spawnParticles(beamOriginX, beamOriginY, '#38bdf8', 12);
        SoundEngine.hit();
    } else if (weapon.id === 'malakor_soul_scythe') {
        this.projectiles.push({
            x: beamOriginX,
            y: beamOriginY,
            vx: Math.cos(angle) * 12,
            vy: Math.sin(angle) * 12,
            angle: angle,
            damage: projDmg,
            rangeLeft: weapon.range,
            type: 'shadow_skull',
            fromPlayer: true
        });
        SoundEngine.thunder();
    } else if (weapon.id === 'tempest_blade') {
        this.projectiles.push({
            x: beamOriginX,
            y: beamOriginY,
            vx: Math.cos(angle) * 15,
            vy: Math.sin(angle) * 15,
            angle: angle,
            damage: projDmg,
            rangeLeft: weapon.range,
            type: 'lightning_beam',
            fromPlayer: true
        });
        this.triggerScreenShake(4.0, 110);
        this.spawnParticles(beamOriginX, beamOriginY, '#38bdf8', 14);
        SoundEngine.thunder();
    } else if (weapon.id === 'spire_blade') {
        this.projectiles.push({
            x: beamOriginX,
            y: beamOriginY,
            vx: Math.cos(angle) * 13,
            vy: Math.sin(angle) * 13,
            angle: angle,
            damage: projDmg,
            rangeLeft: weapon.range,
            type: 'holy_beam',
            fromPlayer: true
        });
        SoundEngine.shoot(true);
    }
};


Game.playerShootAt = function(targetWorldX, targetWorldY, weapon = null) {
    if (!this.isCombatScene()) {
        this.addFloatingText('ไม่สามารถใช้อาวุธในอาคารได้', this.player.x, this.player.y - 15, '#fca5a5');
        return;
    }
    if (this.playerShootCooldown > 0) return;

    if (!weapon) {
        const selectedItem = this.player.inventory[this.player.selectedSlot];
        weapon = (selectedItem && WEAPONS[selectedItem.id]) ? WEAPONS[selectedItem.id] : WEAPONS.slingshot;
    }

    const originX = this.player.x + 12;
    const originY = this.player.y + 14;
    const dx = targetWorldX - originX;
    const dy = targetWorldY - originY;
    const angle = Math.atan2(dy, dx);

    if (Math.abs(dx) > Math.abs(dy)) {
        this.player.direction = dx > 0 ? 'right' : 'left';
    } else {
        this.player.direction = dy > 0 ? 'down' : 'up';
    }

    const bonusDmg = this.player.buffs?.damage || 0;
    const isRifle = (weapon.id === 'rifle' || weapon.id === 'dragon_rifle');
    SoundEngine.shoot(isRifle);

    // Ring of the Warrior & Critical Strike
    const hasWarriorRing = this.hasRing('ring_warrior');
    const critChance = hasWarriorRing ? 0.25 : 0.08;
    const isCrit = Math.random() < critChance;
    const critMult = isCrit ? (hasWarriorRing ? 2.2 : 1.5) : 1.0;
    const bulletDamage = Math.round((weapon.damage + bonusDmg) * critMult);

    if (isCrit) {
        this.addFloatingText(' CRIT!', originX, originY - 18, '#fbbf24');
    }

    if (weapon.id === 'hydra_venom_bow') {
        [-0.20, 0, 0.20].forEach(offset => {
            const a = angle + offset;
            this.projectiles.push({
                x: originX,
                y: originY,
                vx: Math.cos(a) * weapon.speed,
                vy: Math.sin(a) * weapon.speed,
                angle: a,
                damage: bulletDamage,
                rangeLeft: weapon.range,
                type: weapon.bulletType,
                fromPlayer: true
            });
        });
    } else if (weapon.id === 'sylvan_bow') {
        [-0.24, -0.08, 0.08, 0.24].forEach(offset => {
            const a = angle + offset;
            this.projectiles.push({
                x: originX,
                y: originY,
                vx: Math.cos(a) * weapon.speed,
                vy: Math.sin(a) * weapon.speed,
                angle: a,
                damage: bulletDamage,
                rangeLeft: weapon.range,
                type: weapon.bulletType,
                fromPlayer: true
            });
        });
    } else if (weapon.id === 'spire_bow') {
        [-0.18, 0, 0.18].forEach(offset => {
            const a = angle + offset;
            this.projectiles.push({
                x: originX,
                y: originY,
                vx: Math.cos(a) * weapon.speed,
                vy: Math.sin(a) * weapon.speed,
                angle: a,
                damage: bulletDamage,
                rangeLeft: weapon.range,
                type: weapon.bulletType,
                fromPlayer: true
            });
        });
    } else {
        this.projectiles.push({
            x: originX,
            y: originY,
            vx: Math.cos(angle) * weapon.speed,
            vy: Math.sin(angle) * weapon.speed,
            angle: angle,
            damage: bulletDamage,
            rangeLeft: weapon.range,
            type: weapon.bulletType,
            fromPlayer: true
        });
    }

    this.playerShootCooldown = weapon.cooldown;
    this.spawnParticles(originX + Math.cos(angle) * 12, originY + Math.sin(angle) * 12, isRifle ? '#f59e0b' : '#cbd5e1', 5);
};


Game.triggerBugWave = function(manual = false) {
    if (this.currentScene !== 'farm') return;

    SoundEngine.alarm();
    this.waveCounter++;
    this.waveAlertTimer = 4500;
    this.addFloatingText(' ฝูงแมลงปีศาจบุกเข้าฟาร์ม!', this.player.x, this.player.y - 30, '#ef4444');

    const waveSize = manual ? 3 : Math.min(5, 2 + Math.floor(this.waveCounter / 2));
    const bugKeys = Object.keys(DEMON_BUGS);

    for (let i = 0; i < waveSize; i++) {
        const typeKey = bugKeys[Math.floor(Math.random() * bugKeys.length)];
        const bugConfig = DEMON_BUGS[typeKey];

        let sx, sy;
        const side = Math.floor(Math.random() * 4);
        if (side === 0) { // Top
            sx = (4 + Math.random() * 26) * this.tileSize;
            sy = 2 * this.tileSize;
        } else if (side === 1) { // Bottom
            sx = (4 + Math.random() * 26) * this.tileSize;
            sy = 22 * this.tileSize;
        } else if (side === 2) { // Left
            sx = 2 * this.tileSize;
            sy = (6 + Math.random() * 14) * this.tileSize;
        } else { // Right
            sx = 31 * this.tileSize;
            sy = (6 + Math.random() * 14) * this.tileSize;
        }

        this.demonBugs.push({
            id: 'bug_' + performance.now() + '_' + i,
            type: typeKey,
            name: bugConfig.name,
            x: sx,
            y: sy,
            hp: bugConfig.hp,
            maxHp: bugConfig.hp,
            speed: bugConfig.speed,
            damage: bugConfig.damage,
            targetType: bugConfig.targetType,
            attackCooldown: 0,
            loot: bugConfig.loot,
            frame: 0,
            animTimer: 0
        });
    }
};


Game.updateDemonBugs = function(dt) {
    if (this.currentScene !== 'farm') return;

    if (this.waveAlertTimer > 0) {
        this.waveAlertTimer -= dt;
    }

    // Auto-spawn bug wave every 28 seconds
    this.bugSpawnTimer += dt;
    if (this.bugSpawnTimer >= 28000) {
        this.bugSpawnTimer = 0;
        this.triggerBugWave();
    }

    for (let i = this.demonBugs.length - 1; i >= 0; i--) {
        const bug = this.demonBugs[i];
        if (bug.flashTimer > 0) bug.flashTimer -= dt;

        if (bug.squashX && bug.squashX !== 1.0) {
            bug.squashX += (1.0 - bug.squashX) * 0.22;
            if (Math.abs(bug.squashX - 1.0) < 0.02) bug.squashX = 1.0;
        }
        if (bug.squashY && bug.squashY !== 1.0) {
            bug.squashY += (1.0 - bug.squashY) * 0.22;
            if (Math.abs(bug.squashY - 1.0) < 0.02) bug.squashY = 1.0;
        }

        bug.animTimer += dt;
        if (bug.animTimer > 160) {
            bug.animTimer = 0;
            bug.frame = (bug.frame + 1) % 2;
        }

        // Determine destination based on targetType
        let targetX = 8 * 32;
        let targetY = 11 * 32;

        if (bug.targetType === 'animal' && this.animals.length > 0) {
            let nearestDist = 99999;
            let targetAnimal = this.animals[0];
            this.animals.forEach(a => {
                const d = Math.hypot(a.x - bug.x, a.y - bug.y);
                if (d < nearestDist) {
                    nearestDist = d;
                    targetAnimal = a;
                }
            });
            targetX = targetAnimal.x + 8;
            targetY = targetAnimal.y + 8;
        } else {
            // Find nearest crop on the field
            let nearestDist = 99999;
            for (let y = 9; y <= 14; y++) {
                for (let x = 3; x <= 14; x++) {
                    const tile = this.map[y]?.[x];
                    if (tile && tile.crop) {
                        const d = Math.hypot((x * 32 + 16) - bug.x, (y * 32 + 16) - bug.y);
                        if (d < nearestDist) {
                            nearestDist = d;
                            targetX = x * 32 + 16;
                            targetY = y * 32 + 16;
                        }
                    }
                }
            }
        }

        const dist = Math.hypot(targetX - bug.x, targetY - bug.y);

        if (dist > 18) {
            const angle = Math.atan2(targetY - bug.y, targetX - bug.x);
            bug.x += Math.cos(angle) * bug.speed;
            bug.y += Math.sin(angle) * bug.speed;
        } else {
            // Reached target: attack periodically!
            bug.attackCooldown += dt;
            if (bug.attackCooldown >= 1400) {
                bug.attackCooldown = 0;
                SoundEngine.hit();
                if (bug.targetType === 'animal') {
                    this.addFloatingText(' สัตว์เลี้ยงถูกก่อกวน!', bug.x - 20, bug.y - 12, '#f87171');
                } else {
                    this.spawnParticles(bug.x + 12, bug.y + 12, '#84cc16', 8);
                    this.addFloatingText(' แมลงกัดกินพืช!', bug.x - 10, bug.y - 12, '#ef4444');
                }
            }
        }
    }
};


Game.updateHiredHunters = function(dt) {
    if (this.currentScene !== 'farm') return;

    this.hiredHunters.forEach(hunter => {
        hunter.attackTimer = (hunter.attackTimer || 0) + dt;

        // Check if there are demon bugs in range
        let targetBug = null;
        let nearestDist = hunter.range;

        this.demonBugs.forEach(bug => {
            const d = Math.hypot(bug.x - hunter.x, bug.y - hunter.y);
            if (d < nearestDist) {
                nearestDist = d;
                targetBug = bug;
            }
        });

        if (targetBug) {
            // Face target bug
            const dx = targetBug.x - hunter.x;
            const dy = targetBug.y - hunter.y;
            if (Math.abs(dx) > Math.abs(dy)) {
                hunter.direction = dx > 0 ? 'right' : 'left';
            } else {
                hunter.direction = dy > 0 ? 'down' : 'up';
            }

            // Shoot if cooldown ready
            if (hunter.attackTimer >= hunter.attackSpeed) {
                hunter.attackTimer = 0;
                const angle = Math.atan2(dy, dx);
                const isMarksman = (hunter.type === 'veteran_marksman');

                SoundEngine.shoot(isMarksman);

                this.projectiles.push({
                    x: hunter.x + 12,
                    y: hunter.y + 14,
                    vx: Math.cos(angle) * (isMarksman ? 14 : 9),
                    vy: Math.sin(angle) * (isMarksman ? 14 : 9),
                    angle: angle,
                    damage: hunter.damage,
                    rangeLeft: hunter.range,
                    type: isMarksman ? 'rifle' : 'stone',
                    fromHunter: true
                });

                this.spawnParticles(hunter.x + 12 + Math.cos(angle) * 12, hunter.y + 14 + Math.sin(angle) * 12, isMarksman ? '#f59e0b' : '#94a3b8', 4);
                this.addFloatingText(isMarksman ? ' เล็งยิง!' : ' สกัดแมลง!', hunter.x, hunter.y - 14, '#fde047');
            }
        } else {
            // Patrol waypoints
            if (!hunter.waypoints) {
                if (hunter.patrolArea === 'crops') {
                    hunter.waypoints = [
                        { x: 4 * 32, y: 8 * 32 },
                        { x: 15 * 32, y: 8 * 32 },
                        { x: 15 * 32, y: 15 * 32 },
                        { x: 4 * 32, y: 15 * 32 }
                    ];
                } else {
                    hunter.waypoints = [
                        { x: 21 * 32, y: 6 * 32 },
                        { x: 30 * 32, y: 6 * 32 },
                        { x: 30 * 32, y: 14 * 32 },
                        { x: 21 * 32, y: 14 * 32 }
                    ];
                }
                hunter.currentWp = 0;
            }

            const wp = hunter.waypoints[hunter.currentWp];
            const dist = Math.hypot(wp.x - hunter.x, wp.y - hunter.y);

            if (dist > 4) {
                const speed = 1.3;
                const angle = Math.atan2(wp.y - hunter.y, wp.x - hunter.x);
                hunter.x += Math.cos(angle) * speed;
                hunter.y += Math.sin(angle) * speed;

                if (Math.abs(Math.cos(angle)) > Math.abs(Math.sin(angle))) {
                    hunter.direction = Math.cos(angle) > 0 ? 'right' : 'left';
                } else {
                    hunter.direction = Math.sin(angle) > 0 ? 'down' : 'up';
                }

                hunter.frame = Math.floor(performance.now() / 200) % 2;
            } else {
                hunter.currentWp = (hunter.currentWp + 1) % hunter.waypoints.length;
            }
        }
    });
};


Game.updateProjectiles = function(dt) {
    if (!this.isCombatScene()) {
        this.projectiles = [];
        return;
    }

    for (let i = this.projectiles.length - 1; i >= 0; i--) {
        const p = this.projectiles[i];

        p.x += p.vx;
        p.y += p.vy;
        p.rangeLeft -= Math.hypot(p.vx, p.vy);

        if (p.rangeLeft <= 0) {
            if (p.fromPlayer && p.splashRadius && p.splashRadius > 0) {
                const splashDmg = Math.round(p.damage * 0.75);
                this.damageEnemiesInRadius(p.x, p.y, p.splashRadius, splashDmg, 'ระเบิดกระจาย! -' + splashDmg, p.color || '#f97316');
                this.spawnParticles(p.x, p.y, p.color || '#f97316', 16);
                this.spawnParticles(p.x, p.y, '#fde047', 10);
            }
            this.projectiles.splice(i, 1);
            continue;
        }

        let hit = false;

        // 1. If projectile is from Boss: hit Player
        if (p.fromBoss) {
            // Homing spore logic
            if (p.type === 'homing_spore') {
                const targetX = this.player.x + 12;
                const targetY = this.player.y + 14;
                const desiredAngle = Math.atan2(targetY - p.y, targetX - p.x);
                let diff = desiredAngle - (p.angle || 0);
                while (diff < -Math.PI) diff += Math.PI * 2;
                while (diff > Math.PI) diff -= Math.PI * 2;
                p.angle = (p.angle || 0) + Math.sign(diff) * Math.min(Math.abs(diff), 0.045);
                const curSpeed = Math.hypot(p.vx, p.vy) || 2.4;
                p.vx = Math.cos(p.angle) * curSpeed;
                p.vy = Math.sin(p.angle) * curSpeed;
                if (Math.random() < 0.35) {
                    this.spawnParticles(p.x, p.y, '#c084fc', 2);
                }
            } else if (p.type === 'meteor_blight') {
                if (Math.random() < 0.4) {
                    this.spawnParticles(p.x, p.y, '#f97316', 3);
                }
            }

            const hitRadius = (p.type === 'meteor_blight') ? 24 : 16;
            const dist = Math.hypot((this.player.x + 12) - p.x, (this.player.y + 16) - p.y);
            if (dist < hitRadius) {
                // Perfect Parry: Deflect projectile back with amplified damage!
                if (this.player.isGuarding && (this.player.guardTimer || 0) <= 240) {
                    this.triggerPlayerParry(p);
                    continue;
                }
                hit = true;
                this.damagePlayer(p.damage, p);
                this.triggerScreenShake(p.type === 'meteor_blight' ? 4.5 : 2.5, 100);
                this.spawnParticles(p.x, p.y, '#ef4444', p.type === 'meteor_blight' ? 14 : 8);
            }
        }
        // 2. If projectile is from Player or Hunters
        else {
            // Farm scene: Check collision against demon bugs
            if (this.currentScene === 'farm') {
                for (let bIdx = this.demonBugs.length - 1; bIdx >= 0; bIdx--) {
                    const bug = this.demonBugs[bIdx];
                    const dist = Math.hypot((bug.x + 14) - p.x, (bug.y + 14) - p.y);

                    if (dist < 28) {
                        hit = true;
                        bug.hp -= p.damage;
                        bug.flashTimer = 140;
                        bug.squashX = 1.35;
                        bug.squashY = 0.72;
                        if (p.fromPlayer) this.triggerScreenShake(2.5, 90);
                        SoundEngine.hit();
                        this.spawnParticles(p.x, p.y, '#f59e0b', 6);
                        this.addFloatingText('-' + p.damage, bug.x, bug.y - 10, '#ef4444');

                        if (bug.hp <= 0) {
                            SoundEngine.monsterDie();
                            this.spawnParticles(bug.x + 14, bug.y + 14, '#9333ea', 18);

                            this.player.gold += bug.loot.gold;
                            this.spawnDroppedItem(bug.loot.item, 1, bug.x, bug.y);
                            this.addXp(bug.loot.xp);
                            this.stats.bugsDefeated = (this.stats.bugsDefeated || 0) + 1;
                            this.player.questProgress.bugsDefeated = (this.player.questProgress.bugsDefeated || 0) + 1;
                            this.spawnDroppedItem('blight_spore', 1, bug.x, bug.y);
                            this.player.questProgress.sporesCollected = (this.player.questProgress.sporesCollected || 0) + 1;
                            this.addFloatingText('ดรอป: สปอร์กลายพันธุ์', bug.x, bug.y - 12, '#c084fc');

                            this.addFloatingText('+' + bug.loot.gold + ' G ' + bug.loot.name + ' (+' + bug.loot.xp + ' XP)', bug.x - 20, bug.y - 20, '#4ade80');
                            this.demonBugs.splice(bIdx, 1);
                            this.updateHUD();
                        }
                        break;
                    }
                }
            }

            // Check collision against World Monsters & Bosses across all open combat zones
            if (this.currentScene !== 'farm') {
                const mHitDist = p.hitboxRadius || (p.splashRadius ? 36 : 28);
                for (let mIdx = this.worldMonsters.length - 1; mIdx >= 0; mIdx--) {
                    const m = this.worldMonsters[mIdx];
                    const dist = Math.hypot((m.x + 16) - p.x, (m.y + 16) - p.y);

                    if (dist < mHitDist) {
                        hit = true;
                        m.hp -= p.damage;
                        if (p.fromPlayer) this.applyRuneCombatProc(m, p.damage);
                        m.flashTimer = 140;
                        m.squashX = 1.35;
                        m.squashY = 0.72;
                        if (p.fromPlayer) this.triggerScreenShake(2.5, 90);
                        SoundEngine.hit();
                        this.spawnParticles(p.x, p.y, '#f59e0b', 6);
                        this.addFloatingText('-' + p.damage, m.x, m.y - 10, '#ef4444');

                        if (m.hp <= 0) {
                            SoundEngine.monsterDie();
                            this.spawnParticles(m.x + 16, m.y + 16, '#9333ea', 18);
                            const cfg = WORLD_MONSTERS[m.type];
                            if (cfg) {
                                let gReward = cfg.gold;
                                if (p.fromPlayer && this.hasRing('ring_lucky')) {
                                    gReward = Math.round(gReward * 1.35);
                                }
                                this.player.gold += gReward;
                                this.addXp(cfg.xp);
                                cfg.drops.forEach(d => {
                                    const dropBonus = (p.fromPlayer && this.hasRing('ring_lucky')) ? 0.15 : 0;
                                    if (Math.random() <= (d.chance + dropBonus)) {
                                        this.spawnDroppedItem(d.item, 1, m.x, m.y);
                                        const dName = (WORLD_ITEMS && WORLD_ITEMS[d.item]?.name) || d.item;
                                        this.addFloatingText('ดรอป: ' + dName, m.x, m.y - 12, '#facc15');
                                    }
                                });
                                if (m.type === 'shadow_wolf') {
                                    this.player.questProgress.wolvesKilled = (this.player.questProgress.wolvesKilled || 0) + 1;
                                }
                                if (this.currentScene === 'cave') {
                                    this.player.questProgress.caveMonstersDefeated = (this.player.questProgress.caveMonstersDefeated || 0) + 1;
                                }
                                this.addFloatingText('+' + gReward + ' G ' + cfg.name + ' ถูกปราบ! (+' + cfg.xp + ' XP)', m.x - 20, m.y - 20, '#4ade80');
                            }
                            this.worldMonsters.splice(mIdx, 1);
                            this.updateHUD();
                        }
                        break;
                    }
                }

                // Check collision against Remote Players in PvP
                if (!hit && p.fromPlayer && this.remotePlayers && (this.currentScene === 'pvp_arena' || this.isPvPEnabled)) {
                    for (const pid in this.remotePlayers) {
                        const rp = this.remotePlayers[pid];
                        if (!rp || rp.scene !== this.currentScene || rp.hp <= 0) continue;
                        const distP = Math.hypot((rp.x + 12) - p.x, (rp.y + 14) - p.y);
                        if (distP < 24) {
                            hit = true;
                            const pvpDmg = p.damage || 25;
                            if (typeof (window as any).Multiplayer !== 'undefined') {
                                (window as any).Multiplayer.sendPvPHit(pid, pvpDmg, false, 0, 'ลูกธนู/เวทมนตร์');
                            }
                            this.triggerScreenShake(3.0, 90);
                            SoundEngine.hit();
                            this.spawnParticles(p.x, p.y, '#f59e0b', 8);
                            this.addFloatingText('-' + pvpDmg, rp.x, rp.y - 12, '#ef4444');
                            break;
                        }
                    }
                }

                // Check collision against Boss Kathuros & World Bosses
                if (!hit && this.boss && this.boss.alive) {
                    const bossHitDist = (p.hitboxRadius || 36) + 24;
                    const distBoss = Math.hypot((this.boss.x + 32) - p.x, (this.boss.y + 32) - p.y);
                    if (distBoss < bossHitDist) {
                        hit = true;
                        this.boss.hp -= p.damage;
                        if (p.fromPlayer) this.applyRuneCombatProc(this.boss, p.damage);
                        this.boss.flashTimer = 140;
                        this.boss.squashX = 1.25;
                        this.boss.squashY = 0.8;
                        if (p.fromPlayer) this.triggerScreenShake(3.5, 120);
                        SoundEngine.hit();
                        this.spawnParticles(p.x, p.y, '#f59e0b', 8);
                        this.addFloatingText(' -' + p.damage, this.boss.x + 20, this.boss.y - 10, '#ef4444');
                        if (this.boss.hp <= 0) {
                            this.defeatBoss();
                        }
                    }
                }
            }

            // AoE Splash Explosion on impact for skill projectiles
            if (hit && p.fromPlayer && p.splashRadius && p.splashRadius > 0) {
                const splashDmg = Math.round(p.damage * 0.75);
                this.damageEnemiesInRadius(p.x, p.y, p.splashRadius, splashDmg, 'ระเบิดกระจาย! -' + splashDmg, p.color || '#f97316');
                this.spawnParticles(p.x, p.y, p.color || '#f97316', 18);
                this.spawnParticles(p.x, p.y, '#fde047', 12);
                this.triggerScreenShake(3.0, 100);
            }

            // Lifesteal Passive from Ring of the Vampire
            if (hit && p.fromPlayer && this.hasRing('ring_vampiric')) {
                const vampHeal = Math.max(1, Math.round(p.damage * 0.04));
                this.player.hp = Math.min(this.player.maxHp, this.player.hp + vampHeal);
                this.addFloatingText('+' + vampHeal + ' HP', this.player.x, this.player.y - 25, '#4ade80');
                this.updateHUD();
            }

            // Check breakables (Pots & Crates) in combat zones
            if (!hit && p.fromPlayer && typeof this.checkBreakablesInArea === 'function') {
                if (this.checkBreakablesInArea(p.x, p.y, 16)) {
                    hit = true;
                }
            }

            // AoE explosion for dragon rifle
            if (hit && p.type === 'dragon_fire') {
                SoundEngine.shoot(true);
                this.spawnParticles(p.x, p.y, '#ea580c', 20);
            }
        }

        if (hit) {
            this.projectiles.splice(i, 1);
        }
    }
};


Game.openHunterModal = function() {
    this.closeAllModals();
    this.activeModal = 'hunterModal';
    this.renderHuntersModal();
    document.getElementById('hunterModal').style.display = 'flex';
};


Game.renderHuntersModal = function() {
    // 1. Render Farm Caretaker Gardeners (คนดูแลสวน & คนเก็บเกี่ยว)
    const gardenersContainer = document.getElementById('gardenersList');
    if (gardenersContainer && typeof FARM_HELPERS !== 'undefined') {
        gardenersContainer.innerHTML = '';
        Object.values(FARM_HELPERS).forEach(helperConfig => {
            const isHired = this.hiredGardeners.some(g => g.id === helperConfig.id);

            const card = document.createElement('div');
            card.className = 'hunter-card';

            const previewDiv = document.createElement('div');
            previewDiv.className = 'hunter-preview';
            const canvas = document.createElement('canvas');
            canvas.width = 24;
            canvas.height = 32;
            const ctx = canvas.getContext('2d');
            ctx.imageSmoothingEnabled = false;
            const spr = SPRITES.gardeners[helperConfig.spriteType]?.down[0];
            if (spr) ctx.drawImage(spr, 0, 0);
            previewDiv.appendChild(canvas);

            const info = document.createElement('div');
            info.className = 'hunter-info';
            info.innerHTML = `
                <h4>${helperConfig.name}</h4>
                <p>${helperConfig.desc}</p>
                <div class="hunter-stats">รดน้ำแปลงผัก | เก็บเกี่ยวผลผลิตสุกอัตโนมัติ | ความเร็ว: ${helperConfig.speed}</div>
            `;

            card.appendChild(previewDiv);
            card.appendChild(info);

            if (isHired) {
                const badge = document.createElement('div');
                badge.className = 'hunter-active-badge';
                badge.innerHTML = '✓ กำลังดูแลสวน';
                card.appendChild(badge);
            } else {
                const btn = document.createElement('button');
                btn.className = 'btn-hire';
                btn.textContent = `จ้าง (${helperConfig.price} G)`;
                btn.onclick = () => this.hireGardener(helperConfig.id);
                card.appendChild(btn);
            }

            gardenersContainer.appendChild(card);
        });
    }

    // 2. Render Farm Hunters (นายพรานยิงแมลง)
    const container = document.getElementById('huntersList');
    if (!container) return;
    container.innerHTML = '';

    Object.values(HUNTERS).forEach(hunterConfig => {
        const isHired = this.hiredHunters.some(h => h.id === hunterConfig.id);

        const card = document.createElement('div');
        card.className = 'hunter-card';

        // Preview canvas
        const previewDiv = document.createElement('div');
        previewDiv.className = 'hunter-preview';
        const canvas = document.createElement('canvas');
        canvas.width = 24;
        canvas.height = 32;
        const ctx = canvas.getContext('2d');
        ctx.imageSmoothingEnabled = false;
        const spr = SPRITES.hunters[hunterConfig.spriteType].down[0];
        ctx.drawImage(spr, 0, 0);
        previewDiv.appendChild(canvas);

        // Info
        const info = document.createElement('div');
        info.className = 'hunter-info';
        info.innerHTML = `
            <h4>${hunterConfig.name}</h4>
            <p>${hunterConfig.desc}</p>
            <div class="hunter-stats">พลังยิง: ${hunterConfig.damage} | ระยะยิง: ${hunterConfig.range}px | พื้นที่: ${hunterConfig.patrolArea === 'crops' ? 'รอบแปลงผัก' : 'รอบคอกสัตว์'}</div>
        `;

        card.appendChild(previewDiv);
        card.appendChild(info);

        if (isHired) {
            const badge = document.createElement('div');
            badge.className = 'hunter-active-badge';
            badge.innerHTML = '✓ กำลังปฏิบัติหน้าที่';
            card.appendChild(badge);
        } else {
            const btn = document.createElement('button');
            btn.className = 'btn-hire';
            btn.textContent = `จ้าง (${hunterConfig.price} G)`;
            btn.onclick = () => this.hireHunter(hunterConfig.id);
            card.appendChild(btn);
        }

        container.appendChild(card);
    });
};


Game.hireGardener = function(helperId) {
    const config = FARM_HELPERS[helperId];
    if (!config) return;

    if (this.player.gold < config.price) {
        this.addFloatingText('เหรียญทองไม่พอ!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }

    this.player.gold -= config.price;
    SoundEngine.coin();

    let spawnX = (config.role === 'gardener') ? 7 * 32 : 10 * 32;
    let spawnY = 8 * 32;

    this.hiredGardeners.push({
        id: config.id,
        spriteType: config.spriteType,
        name: config.name,
        role: config.role,
        speed: config.speed,
        x: spawnX,
        y: spawnY,
        direction: 'down',
        frame: 0,
        target: null,
        actionCooldown: 0,
        animTimer: 0
    });

    this.addFloatingText('‍ จ้าง ' + config.name + ' สำเร็จแล้ว!', this.player.x, this.player.y - 25, '#4ade80');
    this.updateHUD();
    this.renderHuntersModal();
};


Game.updateHiredGardeners = function(dt) {
    if (this.currentScene !== 'farm') return;

    this.hiredGardeners.forEach(gardener => {
        gardener.actionCooldown = Math.max(0, (gardener.actionCooldown || 0) - dt);
        gardener.animTimer = (gardener.animTimer || 0) + dt;
        if (gardener.animTimer > 160) {
            gardener.animTimer = 0;
            gardener.frame = (gardener.frame + 1) % 2;
        }

        // If performing an action pause
        if (gardener.actionCooldown > 0) return;

        // 1. Move to target
        if (gardener.target) {
            const tx = gardener.target.x;
            const ty = gardener.target.y;
            const dist = Math.hypot(tx - gardener.x, ty - gardener.y);

            if (dist > 6) {
                const speed = gardener.speed || 1.4;
                const angle = Math.atan2(ty - gardener.y, tx - gardener.x);
                gardener.x += Math.cos(angle) * speed;
                gardener.y += Math.sin(angle) * speed;

                if (Math.abs(Math.cos(angle)) > Math.abs(Math.sin(angle))) {
                    gardener.direction = Math.cos(angle) > 0 ? 'right' : 'left';
                } else {
                    gardener.direction = Math.sin(angle) > 0 ? 'down' : 'up';
                }
            } else {
                // Reached target tile! Perform harvesting or watering
                const targetTile = this.map[gardener.target.tileY]?.[gardener.target.tileX];

                if (gardener.target.type === 'harvest') {
                    if (targetTile && targetTile.crop && targetTile.crop.ready) {
                        this.harvestCrop(gardener.target.tileX, gardener.target.tileY);
                        this.addFloatingText(' ' + gardener.name.split(' ')[0] + ' เก็บเกี่ยวแล้ว!', gardener.x - 10, gardener.y - 15, '#fde047');
                        gardener.actionCooldown = 550;
                    }
                } else if (gardener.target.type === 'water') {
                    if (targetTile && targetTile.tilled && !targetTile.watered) {
                        targetTile.watered = true;
                        SoundEngine.water();
                        this.spawnParticles(gardener.target.tileX * 32 + 16, gardener.target.tileY * 32 + 16, '#60a5fa', 8);
                        this.addFloatingText(' ' + gardener.name.split(' ')[0] + ' รดน้ำแล้ว!', gardener.x - 10, gardener.y - 15, '#38bdf8');
                        gardener.actionCooldown = 550;
                    }
                }
                gardener.target = null;
            }
        } else {
            // 2. Search for tasks on crop field (x: 3..14, y: 9..14)
            let bestTask = null;
            let minDist = 99999;

            // Priority 1: Harvest Ripe Crops
            for (let y = 9; y <= 14; y++) {
                for (let x = 3; x <= 14; x++) {
                    const tile = this.map[y]?.[x];
                    if (tile && tile.crop && tile.crop.ready) {
                        // Check if another gardener already targeted this tile
                        const alreadyTargeted = this.hiredGardeners.some(other => other !== gardener && other.target && other.target.tileX === x && other.target.tileY === y);
                        if (alreadyTargeted) continue;

                        const d = Math.hypot((x * 32 + 4) - gardener.x, (y * 32 + 4) - gardener.y);
                        if (d < minDist) {
                            minDist = d;
                            bestTask = { tileX: x, tileY: y, x: x * 32 + 4, y: y * 32 + 4, type: 'harvest' };

                        }
                    }
                }
            }

            // Priority 2: Water Dry Tilled Soil or Crops
            if (!bestTask) {
                for (let y = 9; y <= 14; y++) {
                    for (let x = 3; x <= 14; x++) {
                        const tile = this.map[y]?.[x];
                        if (tile && tile.tilled && !tile.watered) {
                            const alreadyTargeted = this.hiredGardeners.some(other => other !== gardener && other.target && other.target.tileX === x && other.target.tileY === y);
                            if (alreadyTargeted) continue;

                            const d = Math.hypot((x * 32 + 4) - gardener.x, (y * 32 + 4) - gardener.y);
                            if (d < minDist) {
                                minDist = d;
                                bestTask = { tileX: x, tileY: y, x: x * 32 + 4, y: y * 32 + 4, type: 'water' };

                            }
                        }
                    }
                }
            }

            if (bestTask) {
                gardener.target = bestTask;
            } else {
                // Idle rest & patrol near the garden paths
                if (!gardener.idleWp) {
                    gardener.idleWp = [
                        { x: 7 * 32, y: 8 * 32 },
                        { x: 10 * 32, y: 8 * 32 },
                        { x: 9 * 32, y: 6 * 32 },
                        { x: 6 * 32, y: 8 * 32 }
                    ];
                    gardener.idleIdx = 0;
                }

                const wp = gardener.idleWp[gardener.idleIdx];
                const dist = Math.hypot(wp.x - gardener.x, wp.y - gardener.y);
                if (dist > 4) {
                    const angle = Math.atan2(wp.y - gardener.y, wp.x - gardener.x);
                    gardener.x += Math.cos(angle) * 0.8;
                    gardener.y += Math.sin(angle) * 0.8;
                    gardener.direction = Math.cos(angle) > 0 ? 'right' : 'left';
                } else {
                    gardener.idleIdx = (gardener.idleIdx + 1) % gardener.idleWp.length;
                    gardener.actionCooldown = 1800; // Peaceful rest
                }
            }
        }
    });
};


Game.drawSingleGardener = function(g) {
    const gx = Math.round(g.x - this.camera.x);
    const gy = Math.round(g.y - this.camera.y);

    // Grounding Contact Shadow
    this.ctx.fillStyle = 'rgba(15, 23, 42, 0.28)';
    this.ctx.beginPath();
    this.ctx.ellipse(gx + 12, gy + 30, 8, 4, 0, 0, Math.PI * 2);
    this.ctx.fill();

    const frames = SPRITES.gardeners[g.spriteType] || SPRITES.gardeners.gardener_joy;
    if (frames) {
        const dirFrames = frames[g.direction] || frames.down;
        const spr = dirFrames[g.frame] || dirFrames[0];
        this.ctx.drawImage(spr, gx, gy);
    }

    // Gardener Name Tag
    this.ctx.fillStyle = '#86efac';
    this.ctx.font = 'bold 9px "Prompt", sans-serif';
    this.ctx.fillText(g.name.split(' ')[0], gx - 4, gy - 4);
};


Game.drawHiredGardeners = function() {
    this.hiredGardeners.forEach(g => this.drawSingleGardener(g));
};


Game.hireHunter = function(hunterId) {
    const config = HUNTERS[hunterId];
    if (!config) return;

    if (this.player.gold < config.price) {
        this.addFloatingText('เหรียญทองไม่พอ!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }

    this.player.gold -= config.price;
    SoundEngine.coin();

    let spawnX = (config.patrolArea === 'crops') ? 6 * 32 : 24 * 32;
    let spawnY = (config.patrolArea === 'crops') ? 7 * 32 : 8 * 32;

    this.hiredHunters.push({
        id: config.id,
        type: config.spriteType,
        name: config.name,
        damage: config.damage,
        range: config.range,
        attackSpeed: config.attackSpeed,
        patrolArea: config.patrolArea,
        x: spawnX,
        y: spawnY,
        direction: 'down',
        frame: 0,
        attackTimer: 0
    });

    this.addFloatingText(' จ้าง ' + config.name + ' สำเร็จแล้ว!', this.player.x, this.player.y - 25, '#4ade80');
    this.updateHUD();
    this.renderHuntersModal();
};


Game.drawSingleBug = function(bug) {
    const sx = Math.round(bug.x - this.camera.x);
    const sy = Math.round(bug.y - this.camera.y);

    // Grounding Contact Shadow
    this.ctx.fillStyle = 'rgba(15, 23, 42, 0.28)';
    this.ctx.beginPath();
    this.ctx.ellipse(sx + 16, sy + 25, 11, 4.5, 0, 0, Math.PI * 2);
    this.ctx.fill();

    const frames = SPRITES.bugs[bug.type];
    if (frames) {
        const spr = frames[bug.frame] || frames[0];
        const bSquashX = bug.squashX || 1.0;
        const bSquashY = bug.squashY || 1.0;
        const hasSquash = (bSquashX !== 1.0 || bSquashY !== 1.0);

        if (hasSquash) {
            this.ctx.save();
            this.ctx.translate(sx + 14, sy + 14);
            this.ctx.scale(bSquashX, bSquashY);
            this.ctx.translate(-(sx + 14), -(sy + 14));
        }

        this.ctx.drawImage(spr, sx, sy);

        if (bug.flashTimer > 0) {
            this.ctx.save();
            this.ctx.globalCompositeOperation = 'lighter';
            this.ctx.globalAlpha = Math.min(0.85, bug.flashTimer / 100);
            this.ctx.drawImage(spr, sx, sy);
            this.ctx.restore();
        }

        if (hasSquash) {
            this.ctx.restore();
        }
    }

    // Health bar
    const barW = 28;
    const barH = 4;
    const hpPercent = Math.max(0, bug.hp / bug.maxHp);
    this.ctx.fillStyle = '#0f172a';
    this.ctx.fillRect(sx, sy - 8, barW, barH);
    this.ctx.fillStyle = hpPercent > 0.4 ? '#22c55e' : '#ef4444';
    this.ctx.fillRect(sx, sy - 8, Math.round(barW * hpPercent), barH);

    // Bug Name tag
    this.ctx.fillStyle = '#f8fafc';
    this.ctx.font = 'bold 8px "Prompt", sans-serif';
    this.ctx.fillText(bug.name, sx - 2, sy - 11);
};


Game.drawDemonBugs = function() {
    this.demonBugs.forEach(bug => this.drawSingleBug(bug));
};


Game.drawSingleHunter = function(hunter) {
    const hx = Math.round(hunter.x - this.camera.x);
    const hy = Math.round(hunter.y - this.camera.y);

    // Grounding Contact Shadow
    this.ctx.fillStyle = 'rgba(15, 23, 42, 0.28)';
    this.ctx.beginPath();
    this.ctx.ellipse(hx + 12, hy + 30, 8, 4, 0, 0, Math.PI * 2);
    this.ctx.fill();

    const frames = SPRITES.hunters[hunter.type];
    if (frames) {
        const dirFrames = frames[hunter.direction] || frames.down;
        const spr = dirFrames[hunter.frame] || dirFrames[0];
        this.ctx.drawImage(spr, hx, hy);
    }

    // Hunter label
    this.ctx.fillStyle = '#fef08a';
    this.ctx.font = 'bold 9px "Prompt", sans-serif';
    this.ctx.fillText(hunter.name, hx - 4, hy - 4);
};


Game.drawHiredHunters = function() {
    this.hiredHunters.forEach(hunter => this.drawSingleHunter(hunter));
};


Game.drawProjectiles = function() {
    this.projectiles.forEach(p => {
        const sx = Math.round(p.x - this.camera.x);
        const sy = Math.round(p.y - this.camera.y);

        const spr = SPRITES.projectiles[p.type] || SPRITES.projectiles.stone;
        const halfSize = (p.type === 'meteor_blight') ? 12 : 8;
        this.ctx.save();
        this.ctx.translate(sx, sy);
        this.ctx.rotate(p.angle || 0);
        this.ctx.drawImage(spr, -halfSize, -halfSize);
        this.ctx.restore();
    });
};


Game.drawWaveAlertBanner = function() {
    this.ctx.save();
    const bannerW = 320;
    const bannerH = 28;
    const bx = Math.round((this.width - bannerW) / 2);
    const by = 48;

    this.ctx.fillStyle = 'rgba(185, 28, 28, 0.92)';
    this.ctx.fillRect(bx, by, bannerW, bannerH);
    this.ctx.strokeStyle = '#fca5a5';
    this.ctx.lineWidth = 2;
    this.ctx.strokeRect(bx, by, bannerW, bannerH);

    this.ctx.fillStyle = '#ffffff';
    this.ctx.font = 'bold 12px "Prompt", sans-serif';
    this.ctx.textAlign = 'center';
    this.ctx.fillText('! แมลงปีศาจบุกเข้าฟาร์ม! ยิงสกัดด้วยคลิก/Space', this.width / 2, by + 19);
    this.ctx.restore();
};


// ========================================================
// 14. OPEN WORLD, BOSS & STORY QUEST ENGINE
// ========================================================

Game.initForestScene = function() {
    this.bossTelegraphs = [];
    this.bossGroundHazards = [];
    this.bossDashGhosts = [];
    this.bossShockwaves = [];

    this.worldMonsters = [
        // Shadow wolves in Shadow Woods
        { id: 'wolf1', type: 'shadow_wolf', x: 8 * 32, y: 16 * 32, hp: 60, maxHp: 60, speed: 1.4, damage: 12, aggroRange: 160, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'wolf2', type: 'shadow_wolf', x: 14 * 32, y: 22 * 32, hp: 60, maxHp: 60, speed: 1.4, damage: 12, aggroRange: 160, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'wolf3', type: 'shadow_wolf', x: 16 * 32, y: 15 * 32, hp: 60, maxHp: 60, speed: 1.4, damage: 12, aggroRange: 160, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        // Goblin scouts in eastern fields
        { id: 'gob1', type: 'goblin_scout', x: 33 * 32, y: 16 * 32, hp: 45, maxHp: 45, speed: 1.6, damage: 10, aggroRange: 180, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'gob2', type: 'goblin_scout', x: 38 * 32, y: 20 * 32, hp: 45, maxHp: 45, speed: 1.6, damage: 10, aggroRange: 180, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'gob3', type: 'goblin_scout', x: 42 * 32, y: 14 * 32, hp: 45, maxHp: 45, speed: 1.6, damage: 10, aggroRange: 180, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        // Demon treants in deep cursed grove
        { id: 'treant1', type: 'demon_treant', x: 9 * 32, y: 24 * 32, hp: 120, maxHp: 120, speed: 0.8, damage: 18, aggroRange: 140, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'treant2', type: 'demon_treant', x: 37 * 32, y: 26 * 32, hp: 120, maxHp: 120, speed: 0.8, damage: 18, aggroRange: 140, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 }
    ];

    if (!this.player.defeatedBosses) this.player.defeatedBosses = {};

    if (!this.player.defeatedBosses['boss_kathuros']) {
        this.boss = {
            id: 'boss_kathuros',
            name: BOSS_KATHUROS.name,
            title: BOSS_KATHUROS.title,
            x: 24 * 32,
            y: 4 * 32,
            width: 64,
            height: 64,
            hp: BOSS_KATHUROS.hp,
            maxHp: BOSS_KATHUROS.hp,
            speed: 1.0,
            alive: true,
            active: false,
            phase: 1,
            attackCooldown: 2200,
            specialCooldown: 4500,
            summonCooldown: 14000,
            frame: 0,
            animTimer: 0,
            flashTimer: 0,
            state: 'normal',
            spiralAngle: 0,
            dashTarget: null
        };

    } else {
        this.boss = null;
    }
};



Game.initCaveScene = function() {
    this.bossTelegraphs = [];
    this.bossGroundHazards = [];
    this.bossDashGhosts = [];
    this.bossShockwaves = [];

    this.worldMonsters = [
        // Cave bats: quick aerial creatures
        { id: 'bat1', type: 'cave_bat', x: 12 * 32, y: 14 * 32, hp: 40, maxHp: 40, speed: 1.8, damage: 8, aggroRange: 170, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'bat2', type: 'cave_bat', x: 28 * 32, y: 16 * 32, hp: 40, maxHp: 40, speed: 1.8, damage: 8, aggroRange: 170, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'bat3', type: 'cave_bat', x: 20 * 32, y: 8 * 32, hp: 40, maxHp: 40, speed: 1.8, damage: 8, aggroRange: 170, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'bat4', type: 'cave_bat', x: 35 * 32, y: 24 * 32, hp: 40, maxHp: 40, speed: 1.8, damage: 8, aggroRange: 170, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        // Crystal slimes: tough subterranean slimes
        { id: 'slime1', type: 'crystal_slime', x: 16 * 32, y: 20 * 32, hp: 70, maxHp: 70, speed: 1.1, damage: 14, aggroRange: 150, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'slime2', type: 'crystal_slime', x: 26 * 32, y: 22 * 32, hp: 70, maxHp: 70, speed: 1.1, damage: 14, aggroRange: 150, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'slime3', type: 'crystal_slime', x: 34 * 32, y: 10 * 32, hp: 70, maxHp: 70, speed: 1.1, damage: 14, aggroRange: 150, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 }
    ];
};


Game.initCaveDepthsScene = function() {
    this.bossTelegraphs = [];
    this.bossGroundHazards = [];
    this.bossDashGhosts = [];
    this.bossShockwaves = [];

    this.worldMonsters = [
        { id: 'cd_spider1', type: 'crystal_spider', x: 10 * 32, y: 16 * 32, hp: 95, maxHp: 95, speed: 1.7, damage: 14, aggroRange: 190, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'cd_spider2', type: 'crystal_spider', x: 34 * 32, y: 18 * 32, hp: 95, maxHp: 95, speed: 1.7, damage: 14, aggroRange: 190, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'cd_slime1', type: 'crystal_slime', x: 14 * 32, y: 24 * 32, hp: 110, maxHp: 110, speed: 1.1, damage: 15, aggroRange: 160, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'cd_slime2', type: 'crystal_slime', x: 28 * 32, y: 26 * 32, hp: 110, maxHp: 110, speed: 1.1, damage: 15, aggroRange: 160, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 }
    ];

    if (!this.player.defeatedBosses) this.player.defeatedBosses = {};

    if (!this.player.defeatedBosses['boss_luminarch']) {
        this.boss = {
            id: 'boss_luminarch',
            name: BOSS_LUMINARCH.name,
            title: BOSS_LUMINARCH.title,
            x: 23 * 32,
            y: 5 * 32,
            width: 64,
            height: 64,
            hp: BOSS_LUMINARCH.hp,
            maxHp: BOSS_LUMINARCH.hp,
            speed: 0.85,
            alive: true,
            active: false,
            phase: 1,
            attackCooldown: 2000,
            specialCooldown: 4000,
            summonCooldown: 12000,
            frame: 0,
            animTimer: 0,
            flashTimer: 0,
            state: 'normal',
            spiralAngle: 0,
            dashTarget: null
        };

    } else {
        this.boss = null;
    }
};



Game.initSwampScene = function() {
    this.bossTelegraphs = [];
    this.bossGroundHazards = [];
    this.bossDashGhosts = [];
    this.bossShockwaves = [];

    this.worldMonsters = [
        { id: 'sw_croc1', type: 'swamp_croc', x: 12 * 32, y: 18 * 32, hp: 130, maxHp: 130, speed: 1.1, damage: 16, aggroRange: 170, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'sw_croc2', type: 'swamp_croc', x: 28 * 32, y: 16 * 32, hp: 130, maxHp: 130, speed: 1.1, damage: 16, aggroRange: 170, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'sw_gob1', type: 'goblin_scout', x: 36 * 32, y: 26 * 32, hp: 75, maxHp: 75, speed: 1.3, damage: 10, aggroRange: 180, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'sw_gob2', type: 'goblin_scout', x: 18 * 32, y: 28 * 32, hp: 75, maxHp: 75, speed: 1.3, damage: 10, aggroRange: 180, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 }
    ];

    if (!this.player.defeatedBosses) this.player.defeatedBosses = {};

    if (!this.player.defeatedBosses['boss_hydrakis']) {
        this.boss = {
            id: 'boss_hydrakis',
            name: BOSS_HYDRAKIS.name,
            title: BOSS_HYDRAKIS.title,
            x: 14 * 32,
            y: 6 * 32,
            width: 64,
            height: 64,
            hp: BOSS_HYDRAKIS.hp,
            maxHp: BOSS_HYDRAKIS.hp,
            speed: 1.05,
            alive: true,
            active: false,
            phase: 1,
            attackCooldown: 1800,
            specialCooldown: 4200,
            summonCooldown: 13000,
            frame: 0,
            animTimer: 0,
            flashTimer: 0,
            state: 'normal',
            spiralAngle: 0,
            dashTarget: null
        };

    } else {
        this.boss = null;
    }
};



Game.initVolcanoScene = function() {
    this.bossTelegraphs = [];
    this.bossGroundHazards = [];
    this.bossDashGhosts = [];
    this.bossShockwaves = [];

    this.worldMonsters = [
        { id: 'vol_elem1', type: 'magma_elemental', x: 12 * 32, y: 14 * 32, hp: 160, maxHp: 160, speed: 0.9, damage: 22, aggroRange: 180, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'vol_elem2', type: 'magma_elemental', x: 38 * 32, y: 16 * 32, hp: 160, maxHp: 160, speed: 0.9, damage: 22, aggroRange: 180, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'vol_elem3', type: 'magma_elemental', x: 24 * 32, y: 26 * 32, hp: 160, maxHp: 160, speed: 0.9, damage: 22, aggroRange: 180, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 }
    ];

    if (!this.player.defeatedBosses) this.player.defeatedBosses = {};

    if (!this.player.defeatedBosses['boss_ignistron']) {
        this.boss = {
            id: 'boss_ignistron',
            name: BOSS_IGNISTRON.name,
            title: BOSS_IGNISTRON.title,
            x: 25 * 32,
            y: 5 * 32,
            width: 64,
            height: 64,
            hp: BOSS_IGNISTRON.hp,
            maxHp: BOSS_IGNISTRON.hp,
            speed: 1.15,
            alive: true,
            active: false,
            phase: 1,
            attackCooldown: 1700,
            specialCooldown: 3800,
            summonCooldown: 12000,
            frame: 0,
            animTimer: 0,
            flashTimer: 0,
            state: 'normal',
            spiralAngle: 0,
            dashTarget: null
        };

    } else {
        this.boss = null;
    }
};



Game.initFrostpeakScene = function() {
    this.bossTelegraphs = [];
    this.bossGroundHazards = [];
    this.bossDashGhosts = [];
    this.bossShockwaves = [];

    this.worldMonsters = [
        { id: 'fp_wolf1', type: 'frost_wolf', x: 10 * 32, y: 18 * 32, hp: 120, maxHp: 120, speed: 1.8, damage: 18, aggroRange: 210, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'fp_wolf2', type: 'frost_wolf', x: 36 * 32, y: 20 * 32, hp: 120, maxHp: 120, speed: 1.8, damage: 18, aggroRange: 210, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'fp_bat1', type: 'cave_bat', x: 16 * 32, y: 28 * 32, hp: 55, maxHp: 55, speed: 2.1, damage: 9, aggroRange: 190, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'fp_bat2', type: 'cave_bat', x: 30 * 32, y: 28 * 32, hp: 55, maxHp: 55, speed: 2.1, damage: 9, aggroRange: 190, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 }
    ];

    if (!this.player.defeatedBosses) this.player.defeatedBosses = {};

    if (!this.player.defeatedBosses['boss_frostfang']) {
        this.boss = {
            id: 'boss_frostfang',
            name: BOSS_FROSTFANG.name,
            title: BOSS_FROSTFANG.title,
            x: 23 * 32,
            y: 5 * 32,
            width: 64,
            height: 64,
            hp: BOSS_FROSTFANG.hp,
            maxHp: BOSS_FROSTFANG.hp,
            speed: 0.95,
            alive: true,
            active: false,
            phase: 1,
            attackCooldown: 1900,
            specialCooldown: 4100,
            summonCooldown: 13000,
            frame: 0,
            animTimer: 0,
            flashTimer: 0,
            state: 'normal',
            spiralAngle: 0,
            dashTarget: null
        };

    } else {
        this.boss = null;
    }
};



Game.initCryptScene = function() {
    this.bossTelegraphs = [];
    this.bossGroundHazards = [];
    this.bossDashGhosts = [];
    this.bossShockwaves = [];

    this.worldMonsters = [
        { id: 'cr_skel1', type: 'skeleton_warrior', x: 10 * 32, y: 16 * 32, hp: 140, maxHp: 140, speed: 1.2, damage: 20, aggroRange: 180, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'cr_skel2', type: 'skeleton_warrior', x: 34 * 32, y: 16 * 32, hp: 140, maxHp: 140, speed: 1.2, damage: 20, aggroRange: 180, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'cr_skel3', type: 'skeleton_warrior', x: 22 * 32, y: 24 * 32, hp: 140, maxHp: 140, speed: 1.2, damage: 20, aggroRange: 180, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'cr_wolf1', type: 'shadow_wolf', x: 16 * 32, y: 28 * 32, hp: 90, maxHp: 90, speed: 1.6, damage: 12, aggroRange: 180, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 }
    ];

    if (!this.player.defeatedBosses) this.player.defeatedBosses = {};

    if (!this.player.defeatedBosses['boss_malakor']) {
        this.boss = {
            id: 'boss_malakor',
            name: BOSS_MALAKOR.name,
            title: BOSS_MALAKOR.title,
            x: 23 * 32,
            y: 5 * 32,
            width: 64,
            height: 64,
            hp: BOSS_MALAKOR.hp,
            maxHp: BOSS_MALAKOR.hp,
            speed: 1.0,
            alive: true,
            active: false,
            phase: 1,
            attackCooldown: 1800,
            specialCooldown: 4000,
            summonCooldown: 12000,
            frame: 0,
            animTimer: 0,
            flashTimer: 0,
            state: 'normal',
            spiralAngle: 0,
            dashTarget: null
        };

    } else {
        this.boss = null;
    }
};



Game.initAncientCanopyScene = function() {
    this.bossTelegraphs = [];
    this.bossGroundHazards = [];
    this.bossDashGhosts = [];
    this.bossShockwaves = [];

    this.worldMonsters = [
        { id: 'canopy_treant1', type: 'demon_treant', x: 14 * 32, y: 16 * 32, hp: 160, maxHp: 160, speed: 0.9, damage: 20, aggroRange: 220, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'canopy_treant2', type: 'demon_treant', x: 44 * 32, y: 22 * 32, hp: 160, maxHp: 160, speed: 0.9, damage: 20, aggroRange: 220, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'canopy_spider1', type: 'crystal_spider', x: 26 * 32, y: 28 * 32, hp: 110, maxHp: 110, speed: 1.8, damage: 16, aggroRange: 220, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'canopy_spider2', type: 'crystal_spider', x: 38 * 32, y: 34 * 32, hp: 110, maxHp: 110, speed: 1.8, damage: 16, aggroRange: 220, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'canopy_wolf1', type: 'shadow_wolf', x: 18 * 32, y: 38 * 32, hp: 100, maxHp: 100, speed: 1.7, damage: 14, aggroRange: 210, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 }
    ];

    if (!this.player.defeatedBosses) this.player.defeatedBosses = {};

    if (!this.player.defeatedBosses['boss_sylvanus']) {
        this.boss = {
            id: 'boss_sylvanus',
            name: BOSS_SYLVANUS.name,
            title: BOSS_SYLVANUS.title,
            x: 29 * 32,
            y: 6 * 32,
            width: 64,
            height: 64,
            hp: BOSS_SYLVANUS.hp,
            maxHp: BOSS_SYLVANUS.hp,
            speed: 0.95,
            alive: true,
            active: false,
            phase: 1,
            attackCooldown: 1500,
            specialCooldown: 3500,
            summonCooldown: 12000,
            frame: 0,
            animTimer: 0,
            flashTimer: 0,
            state: 'normal',
            spiralAngle: 0,
            dashTarget: null
        };
    } else {
        this.boss = null;
    }
};

Game.initTempestPlateauScene = function() {
    this.bossTelegraphs = [];
    this.bossGroundHazards = [];
    this.bossDashGhosts = [];
    this.bossShockwaves = [];

    this.worldMonsters = [
        { id: 'tempest_demon1', type: 'spire_demon', x: 18 * 32, y: 22 * 32, hp: 180, maxHp: 180, speed: 1.6, damage: 24, aggroRange: 240, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'tempest_demon2', type: 'spire_demon', x: 42 * 32, y: 24 * 32, hp: 180, maxHp: 180, speed: 1.6, damage: 24, aggroRange: 240, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'tempest_magma1', type: 'magma_elemental', x: 28 * 32, y: 32 * 32, hp: 140, maxHp: 140, speed: 1.3, damage: 20, aggroRange: 210, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'tempest_bat1', type: 'cave_bat', x: 20 * 32, y: 36 * 32, hp: 70, maxHp: 70, speed: 2.2, damage: 12, aggroRange: 220, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'tempest_bat2', type: 'cave_bat', x: 38 * 32, y: 36 * 32, hp: 70, maxHp: 70, speed: 2.2, damage: 12, aggroRange: 220, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 }
    ];

    if (!this.player.defeatedBosses) this.player.defeatedBosses = {};

    if (!this.player.defeatedBosses['boss_astreon']) {
        this.boss = {
            id: 'boss_astreon',
            name: BOSS_ASTREON.name,
            title: BOSS_ASTREON.title,
            x: 31 * 32,
            y: 6 * 32,
            width: 64,
            height: 64,
            hp: BOSS_ASTREON.hp,
            maxHp: BOSS_ASTREON.hp,
            speed: 1.45,
            alive: true,
            active: false,
            phase: 1,
            attackCooldown: 1200,
            specialCooldown: 3000,
            summonCooldown: 10000,
            frame: 0,
            animTimer: 0,
            flashTimer: 0,
            state: 'normal',
            spiralAngle: 0,
            dashTarget: null
        };
    } else {
        this.boss = null;
    }
};


Game.damagePlayer = function(amount, source = null) {
    if (this.player.invincibleTimer > 0 || this.player.isDead) return;

    // GUARD & PERFECT PARRY SYSTEM
    if (this.player.isGuarding) {
        // Perfect Parry window: within 240ms (extended by Malakor Void Shroud and Parry Master Broth!)
        let parryWindow = 240;
        if (this.player.equippedArmor === 'malakor_void_cloak') parryWindow += 80;
        if (this.player.buffs?.parryWindowBonus) parryWindow += this.player.buffs.parryWindowBonus;

        if ((this.player.guardTimer || 0) <= parryWindow) {
            this.triggerPlayerParry(source);
            return;
        }

        // Regular Guard / Block (> parryWindow)
        const blockCost = 14;
        if ((this.player.energy || 0) >= blockCost) {
            this.player.energy = Math.max(0, this.player.energy - blockCost);
            // Block negates 65% of damage (takes 35%). Frostfang Glacial Plate negates 80% (takes 20%)!
            const blockRatio = (this.player.equippedArmor === 'frostfang_frozen_plate') ? 0.20 : 0.35;
            const blockedAmount = Math.max(1, Math.round(amount * blockRatio));
            SoundEngine.shieldBlock();
            this.triggerScreenShake(3.5, 130);
            this.triggerHitstop(45);
            this.player.invincibleTimer = 220;

            // Frostfang Glacial chill counter against attacker!
            if (this.player.equippedArmor === 'frostfang_frozen_plate' && source) {
                source.slowTimer = 2500;
                this.spawnParticles(this.player.x + 12, this.player.y + 14, '#38bdf8', 14);
                this.addFloatingText('★ ไอเย็นแช่แข็งสวนกลับ! (Slow 50%)', this.player.x - 10, this.player.y - 32, '#67e8f9');
            }

            this.activeSkillVisuals = this.activeSkillVisuals || [];
            this.activeSkillVisuals.push({
                type: 'block_spark',
                x: this.player.x + 12,
                y: this.player.y + 14,
                timer: 220,
                maxTimer: 220
            });
            this.spawnParticles(this.player.x + 12, this.player.y + 14, '#38bdf8', 12);
            this.spawnParticles(this.player.x + 12, this.player.y + 14, '#94a3b8', 8);
            this.player.hp -= blockedAmount;
            this.player.hpRegenDelay = 3000;
            this.updateHpHUD();

            if (this.player.hp <= 0 && !this.player.isDead) {
                this.player.isDead = true;
                this.player.hp = 0;
                SoundEngine.youDied();
                this.triggerScreenShake(12.0, 500);
                this.triggerHitstop(120);

                const lostGold = Math.floor((this.player.gold || 0) * 0.25);
                this.player.gold -= lostGold;
                this.player.bloodstain = {
                    scene: this.currentScene,
                    x: Math.round(this.player.x + 12),
                    y: Math.round(this.player.y + 14),
                    gold: lostGold
                };

                const overlay = document.getElementById('youDiedOverlay');
                if (overlay) overlay.style.display = 'flex';
                const goldEl = document.getElementById('youDiedLostGoldText');
                if (goldEl) {
                    goldEl.textContent = lostGold > 0 
                        ? `★ เถ้าธุลีวิญญาณตกหล่น ณ จุดที่คุณตาย (-${lostGold} G) สามารถกลับไปเก็บคืนได้!` 
                        : '★ พ่ายแพ้แก่ความมืดมิด...';
                }

                setTimeout(() => {
                    if (overlay) overlay.style.display = 'none';
                    this.player.hp = this.player.maxHp || 100;
                    this.player.energy = 50;
                    this.player.isDead = false;
                    this.player.isGuarding = false;
                    this.player.isDashing = false;
                    this.player.guardBreakTimer = 0;
                    this.keys = { up: false, down: false, left: false, right: false };
                    this.switchScene('house', 18, 5);
                    this.addFloatingText('★ ฟื้นคืนชีพ ณ บ้านพักชาวสวน... เถ้าธุลีวิญญาณรอการกอบกู้', this.player.x - 40, this.player.y - 30, '#facc15');
                    this.updateHpHUD();
                    this.updateEnergyHUD();
                    this.updateHUD();
                }, 2600);
            }
            return;
        } else {
            // Check if ironhide_dragon_steak buff prevents Guard Break!
            if (this.player.buffs?.guardBreakImmune) {
                this.player.buffs.guardBreakImmune = false;
                this.player.energy = 25;
                this.addFloatingText('★ [เกราะศิลาคุ้มภัย] ต้านทานการ์ดแตกสำเร็จ!', this.player.x - 30, this.player.y - 25, '#d97706');
                SoundEngine.shieldBlock();
                this.player.invincibleTimer = 350;
                return;
            }
            // Energy insufficient -> Guard Break!
            this.triggerGuardBreak();
            // Staggered vulnerability takes 1.25x damage
            amount = Math.round(amount * 1.25);
        }
    }

    // RPG Armor & Defense Mitigation formula: DMG = Raw * (100 / (100 + Defense))
    let baseArmor = Math.floor((this.player.level || 1) * 3);
    if (this.player.equippedArmor === 'kathuros_spore_armor') baseArmor += 25;
    let mitigation = 100 / (100 + baseArmor);
    if (this.player.buffs?.defense) {
        mitigation *= (1 - this.player.buffs.defense);
    }
    amount = Math.max(1, Math.round(amount * mitigation));

    // Kathuros Spore Mail retaliatory thorn burst!
    if (this.player.equippedArmor === 'kathuros_spore_armor') {
        const sporeDmg = 45;
        this.spawnParticles(this.player.x + 12, this.player.y + 14, '#a855f7', 18);
        this.damageEnemiesInRadius(this.player.x + 12, this.player.y + 14, 90, sporeDmg, '★ หนามสปอร์สะท้อน! -' + sporeDmg, '#c084fc');
        SoundEngine.bossSpikeErupt();
    }

    this.player.hp -= amount;
    this.player.hpRegenDelay = 3000;
    this.player.invincibleTimer = 850; // Generous 850ms i-frame window so player has time to react & escape swarms
    SoundEngine.hit();
    this.triggerScreenShake(5.5, 180);
    this.triggerHitstop(60);
    this.spawnParticles(this.player.x + 12, this.player.y + 14, '#ef4444', 14);
    this.addFloatingText('★ -' + amount + ' HP' + (this.player.buffs?.defense ? ' (เกราะลดดาเมจ)' : ''), this.player.x, this.player.y - 20, '#ef4444');
    this.updateHpHUD();
    this.updateHUD();

    if (this.player.hp <= 0 && !this.player.isDead) {
        this.player.isDead = true;
        this.player.hp = 0;
        SoundEngine.youDied();
        this.triggerScreenShake(12.0, 500);
        this.triggerHitstop(120);

        // Friendly penalty: Drop Bloodstain (5% gold lost instead of 25%)
        const lostGold = Math.floor((this.player.gold || 0) * 0.05);
        this.player.gold -= lostGold;
        this.player.bloodstain = {
            scene: this.currentScene,
            x: Math.round(this.player.x + 12),
            y: Math.round(this.player.y + 14),
            gold: lostGold
        };

        const overlay = document.getElementById('youDiedOverlay');
        if (overlay) overlay.style.display = 'flex';
        const goldEl = document.getElementById('youDiedLostGoldText');
        if (goldEl) {
            goldEl.textContent = lostGold > 0 
                ? `★ เถ้าธุลีวิญญาณตกหล่น ณ จุดที่คุณตาย (-${lostGold} G) สามารถกลับไปเก็บคืนได้!` 
                : '★ พ่ายแพ้แก่ความมืดมิด...';
        }

        setTimeout(() => {
            if (overlay) overlay.style.display = 'none';
            this.player.hp = this.player.maxHp || 100;
            this.player.energy = 50;
            this.player.isDead = false;
            this.player.isGuarding = false;
            this.player.isDashing = false;
            this.player.guardBreakTimer = 0;
            this.keys = { up: false, down: false, left: false, right: false };
            this.switchScene('house', 18, 5);
            this.addFloatingText('★ ฟื้นคืนชีพ ณ บ้านพักชาวสวน... เถ้าธุลีวิญญาณรอการกอบกู้', this.player.x - 40, this.player.y - 30, '#facc15');
            this.updateHpHUD();
            this.updateEnergyHUD();
            this.updateHUD();
        }, 2600);
    }
};


Game.checkMonsterCollision = function(x, y) {
    const hitbox = {
        left: x + 6, right: x + 24,
        top: y + 14, bottom: y + 27
    };
    const minTileX = Math.floor(hitbox.left / this.tileSize);
    const maxTileX = Math.floor(hitbox.right / this.tileSize);
    const minTileY = Math.floor(hitbox.top / this.tileSize);
    const maxTileY = Math.floor(hitbox.bottom / this.tileSize);

    for (let ty = minTileY; ty <= maxTileY; ty++) {
        for (let tx = minTileX; tx <= maxTileX; tx++) {
            if (ty < 0 || ty >= this.mapHeight || tx < 0 || tx >= this.mapWidth) return true;
            if (this.map[ty]?.[tx]?.solid) return true;
        }
    }
    return false;
};

Game.updateWorldMonsters = function(dt) {
    const combatScenes = ['forest', 'cave', 'cave_depths', 'swamp', 'volcano', 'frost_peak', 'crypt', 'ancient_canopy', 'tempest_plateau', 'island', 'island_volcano'];
    if (!combatScenes.includes(this.currentScene)) return;

    for (let i = this.worldMonsters.length - 1; i >= 0; i--) {
        const m = this.worldMonsters[i];
        if (m.flashTimer > 0) m.flashTimer -= dt;

        // Smooth Squash & Stretch recovery (Dynamic Impact Bounce)
        if (m.squashX && m.squashX !== 1.0) {
            m.squashX += (1.0 - m.squashX) * 0.22;
            if (Math.abs(m.squashX - 1.0) < 0.02) m.squashX = 1.0;
        }
        if (m.squashY && m.squashY !== 1.0) {
            m.squashY += (1.0 - m.squashY) * 0.22;
            if (Math.abs(m.squashY - 1.0) < 0.02) m.squashY = 1.0;
        }

        m.animTimer = (m.animTimer || 0) + dt;
        if (m.animTimer > 160) {
            m.animTimer = 0;
            m.frame = (m.frame + 1) % 2;
        }

        if (m.attackCooldown > 0) {
            m.attackCooldown -= dt;
        }

        const dist = Math.hypot((this.player.x + 12) - (m.x + 16), (this.player.y + 14) - (m.y + 16));

        // 1. Separation / Flocking Force (Prevent monsters from stacking into a single blob)
        let sepX = 0;
        let sepY = 0;
        for (let j = 0; j < this.worldMonsters.length; j++) {
            if (i === j) continue;
            const other = this.worldMonsters[j];
            const dmx = m.x - other.x;
            const dmy = m.y - other.y;
            const sepDist = Math.hypot(dmx, dmy);
            if (sepDist > 0 && sepDist < 30) {
                const repulse = (30 - sepDist) / 30;
                sepX += (dmx / sepDist) * repulse * 0.95;
                sepY += (dmy / sepDist) * repulse * 0.95;
            }
        }

        // 2. Aggro & Chase player with Obstacle Sliding (No walking through trees or rocks!)
        if (dist < (m.aggroRange || 170)) {
            const angle = Math.atan2((this.player.y + 14) - (m.y + 16), (this.player.x + 12) - (m.x + 16));
            const moveSpeed = (m.speed || 1.2);
            let vx = Math.cos(angle) * moveSpeed + sepX;
            let vy = Math.sin(angle) * moveSpeed + sepY;

            // X movement check
            if (!this.checkMonsterCollision(m.x + vx, m.y)) {
                m.x += vx;
            } else if (!this.checkMonsterCollision(m.x, m.y + (vy !== 0 ? vy : moveSpeed * 0.6))) {
                // Wall slide Y
                m.y += (vy !== 0 ? vy : moveSpeed * 0.6);
            }

            // Y movement check
            if (!this.checkMonsterCollision(m.x, m.y + vy)) {
                m.y += vy;
            } else if (!this.checkMonsterCollision(m.x + (vx !== 0 ? vx : moveSpeed * 0.6), m.y)) {
                // Wall slide X
                m.x += (vx !== 0 ? vx : moveSpeed * 0.6);
            }

            if (Math.abs(vx) > Math.abs(vy)) {
                m.direction = vx > 0 ? 'right' : 'left';
            } else {
                m.direction = vy > 0 ? 'down' : 'up';
            }

            // Attack player if within 26px
            if (dist < 26 && m.attackCooldown <= 0) {
                this.damagePlayer(m.damage || 10, m);
                m.attackCooldown = 1500;
            }
        } else {
            // 3. Idle Wander Behavior (ลาดตระเวนสำรวจรอบๆ ตัว ไม่ยืนแข็งทื่อ)
            m.wanderTimer = (m.wanderTimer || 0) - dt;
            if (m.wanderTimer <= 0) {
                m.wanderTimer = 2200 + Math.random() * 2800;
                if (Math.random() < 0.5) {
                    const wandAngle = Math.random() * Math.PI * 2;
                    m.wanderVx = Math.cos(wandAngle) * 0.42;
                    m.wanderVy = Math.sin(wandAngle) * 0.42;
                    m.direction = Math.abs(m.wanderVx) > Math.abs(m.wanderVy) ? (m.wanderVx > 0 ? 'right' : 'left') : (m.wanderVy > 0 ? 'down' : 'up');
                } else {
                    m.wanderVx = 0;
                    m.wanderVy = 0;
                }
            }

            if (m.wanderVx || m.wanderVy) {
                const nextWx = m.x + m.wanderVx;
                const nextWy = m.y + m.wanderVy;
                if (!this.checkMonsterCollision(nextWx, nextWy)) {
                    m.x = nextWx;
                    m.y = nextWy;
                } else {
                    m.wanderVx = 0;
                    m.wanderVy = 0;
                }
            }
        }
    }
};


// ========================================================
//  MEGA BOSS KATHUROS: ABILITIES, TELEGRAPHS & MULTI-PHASE
// ========================================================

Game.spawnBossTelegraph = function(type, x, y, radius, duration, damage, targetX = 0, targetY = 0) {
    this.bossTelegraphs = this.bossTelegraphs || [];
    this.bossTelegraphs.push({
        id: 'tele_' + performance.now() + '_' + Math.random(),
        type,
        x,
        y,
        targetX,
        targetY,
        radius,
        timer: duration,
        maxTimer: duration,
        damage
    });
};


Game.updateBossTelegraphs = function(dt) {
    if (!this.bossTelegraphs || this.bossTelegraphs.length === 0) return;

    for (let i = this.bossTelegraphs.length - 1; i >= 0; i--) {
        const t = this.bossTelegraphs[i];
        t.timer -= dt;

        // Gravitational singularity pull while charging
        if (t.type === 'void_singularity') {
            const pDist = Math.hypot((this.player.x + 12) - t.x, (this.player.y + 14) - t.y);
            if (pDist < 260 && pDist > 20) {
                const pullAng = Math.atan2(t.y - (this.player.y + 14), t.x - (this.player.x + 12));
                this.player.x += Math.cos(pullAng) * (dt * 0.05);
                this.player.y += Math.sin(pullAng) * (dt * 0.05);
            }
        }

        if (t.timer <= 0) {
            // Trigger telegraph detonation!
            if (t.type === 'spike') {
                SoundEngine.bossSpikeErupt();
                this.triggerScreenShake(4.0, 140);
                this.spawnParticles(t.x, t.y, '#9333ea', 18);
                this.spawnParticles(t.x, t.y, '#22c55e', 12);

                const dist = Math.hypot((this.player.x + 12) - t.x, (this.player.y + 14) - t.y);
                if (dist < t.radius + 6) {
                    this.damagePlayer(t.damage || 22, this.boss);
                    this.addFloatingText('★ โดนหนามสปอร์ปะทุ!', this.player.x, this.player.y - 15, '#c084fc');
                }
                this.spawnBossGroundHazard(t.x, t.y, 'poison_thorn', 2800, 8);
            } else if (t.type === 'meteor') {
                SoundEngine.bossMeteor();
                this.triggerScreenShake(7.0, 220);
                this.spawnParticles(t.x, t.y, '#ea580c', 25);
                this.spawnParticles(t.x, t.y, '#facc15', 20);

                const dist = Math.hypot((this.player.x + 12) - t.x, (this.player.y + 14) - t.y);
                if (dist < t.radius + 10) {
                    this.damagePlayer(t.damage || 26, this.boss);
                    this.addFloatingText('★ อุกกาบาตระเบิด!', this.player.x, this.player.y - 15, '#ef4444');
                }
                this.spawnBossGroundHazard(t.x, t.y, 'fire_patch', 3500, 10);
            } else if (t.type === 'dash') {
                if (this.boss && this.boss.alive) {
                    SoundEngine.bossDash();
                    this.boss.state = 'dashing';
                    const ang = Math.atan2(t.targetY - (this.boss.y + 32), t.targetX - (this.boss.x + 32));
                    const totalDist = Math.hypot(t.targetX - (this.boss.x + 32), t.targetY - (this.boss.y + 32));
                    const spd = this.boss.id === 'boss_astreon' ? 18 : 14;
                    this.boss.dashTarget = {
                        vx: Math.cos(ang) * spd,
                        vy: Math.sin(ang) * spd,
                        distLeft: totalDist + 80
                    };
                    this.triggerScreenShake(5.0, 160);
                }
            } else if (t.type === 'lightning') {
                if (typeof SoundEngine.bossLightningStrike === 'function') SoundEngine.bossLightningStrike();
                else SoundEngine.thunder();
                this.triggerScreenShake(7.5, 260);
                this.spawnParticles(t.x, t.y, '#38bdf8', 25);
                this.spawnParticles(t.x, t.y, '#fde047', 20);
                const dist = Math.hypot((this.player.x + 12) - t.x, (this.player.y + 14) - t.y);
                if (dist < t.radius + 8) {
                    this.damagePlayer(t.damage || 32, this.boss);
                    this.addFloatingText('★ อัสนีบาตฟาดผ่า!', this.player.x, this.player.y - 15, '#38bdf8');
                }
                this.spawnBossGroundHazard(t.x, t.y, 'electric_patch', 3200, 10);
            } else if (t.type === 'thorn_trap') {
                SoundEngine.bossSpikeErupt();
                this.triggerScreenShake(4.5, 150);
                this.spawnParticles(t.x, t.y, '#22c55e', 20);
                this.spawnParticles(t.x, t.y, '#84cc16', 15);
                const dist = Math.hypot((this.player.x + 12) - t.x, (this.player.y + 14) - t.y);
                if (dist < t.radius + 8) {
                    this.damagePlayer(t.damage || 24, this.boss);
                    this.addFloatingText('★ บ่วงหนามพันธนาการ!', this.player.x, this.player.y - 15, '#4ade80');
                    this.player.slowTimer = 1600;
                }
                this.spawnBossGroundHazard(t.x, t.y, 'poison_thorn', 3500, 8);
            } else if (t.type === 'ice_boulder') {
                if (typeof SoundEngine.bossIceShatter === 'function') SoundEngine.bossIceShatter();
                this.triggerScreenShake(6.5, 220);
                this.spawnParticles(t.x, t.y, '#38bdf8', 25);
                this.spawnParticles(t.x, t.y, '#e0f2fe', 20);
                const dist = Math.hypot((this.player.x + 12) - t.x, (this.player.y + 14) - t.y);
                if (dist < t.radius + 10) {
                    this.damagePlayer(t.damage || 28, this.boss);
                    this.addFloatingText('★ อุกกาบาตน้ำแข็งแตกกระจาย!', this.player.x, this.player.y - 15, '#67e8f9');
                }
                for (let s = 0; s < 6; s++) {
                    const ang = (s / 6) * Math.PI * 2;
                    this.projectiles.push({
                        x: t.x,
                        y: t.y,
                        vx: Math.cos(ang) * 3.8,
                        vy: Math.sin(ang) * 3.8,
                        angle: ang,
                        damage: 16,
                        rangeLeft: 300,
                        type: 'ice_shard',
                        fromBoss: true
                    });
                }
            } else if (t.type === 'void_singularity') {
                if (typeof SoundEngine.bossVoidSingularity === 'function') SoundEngine.bossVoidSingularity();
                this.triggerScreenShake(8.0, 300);
                this.spawnParticles(t.x, t.y, '#7c3aed', 30);
                this.spawnParticles(t.x, t.y, '#c084fc', 25);
                const dist = Math.hypot((this.player.x + 12) - t.x, (this.player.y + 14) - t.y);
                if (dist < t.radius + 12) {
                    this.damagePlayer(t.damage || 34, this.boss);
                    this.addFloatingText('★ หลุมดำมฤตยูปะทุระเบิด!', this.player.x, this.player.y - 15, '#c084fc');
                }
            }

            this.bossTelegraphs.splice(i, 1);
        }
    }
};


Game.drawBossTelegraphs = function() {
    if (!this.bossTelegraphs || this.bossTelegraphs.length === 0) return;

    this.bossTelegraphs.forEach(t => {
        const sx = Math.round(t.x - this.camera.x);
        const sy = Math.round(t.y - this.camera.y);
        const progress = Math.max(0, 1 - (t.timer / t.maxTimer));

        if (t.type === 'dash') {
            const targetSx = Math.round(t.targetX - this.camera.x);
            const targetSy = Math.round(t.targetY - this.camera.y);

            this.ctx.save();
            const pulse = (Math.sin(performance.now() / 60) + 1) * 0.5;
            this.ctx.strokeStyle = `rgba(239, 68, 68, ${0.4 + pulse * 0.5})`;
            this.ctx.lineWidth = 3 + pulse * 3;
            this.ctx.setLineDash([8, 4]);
            this.ctx.beginPath();
            this.ctx.moveTo(sx, sy);
            this.ctx.lineTo(targetSx, targetSy);
            this.ctx.stroke();
            this.ctx.setLineDash([]);

            this.ctx.fillStyle = 'rgba(239, 68, 68, 0.5)';
            this.ctx.beginPath();
            this.ctx.arc(targetSx, targetSy, 16 * progress, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.restore();
        } else {
            this.ctx.save();
            let strokeStyle = 'rgba(168, 85, 247, 0.85)';
            let fillStyle = 'rgba(147, 51, 234, 0.35)';
            let warnColor = '#e879f9';

            if (t.type === 'meteor') {
                strokeStyle = 'rgba(239, 68, 68, 0.85)';
                fillStyle = 'rgba(234, 88, 12, 0.35)';
                warnColor = '#fef08a';
            } else if (t.type === 'lightning') {
                strokeStyle = 'rgba(56, 189, 248, 0.95)';
                fillStyle = 'rgba(253, 224, 71, 0.35)';
                warnColor = '#fde047';
            } else if (t.type === 'thorn_trap') {
                strokeStyle = 'rgba(34, 197, 94, 0.9)';
                fillStyle = 'rgba(132, 204, 22, 0.35)';
                warnColor = '#bbf7d0';
            } else if (t.type === 'ice_boulder') {
                strokeStyle = 'rgba(56, 189, 248, 0.9)';
                fillStyle = 'rgba(224, 242, 254, 0.4)';
                warnColor = '#e0f2fe';
            } else if (t.type === 'void_singularity') {
                strokeStyle = 'rgba(147, 51, 234, 0.95)';
                fillStyle = 'rgba(88, 28, 135, 0.5)';
                warnColor = '#c084fc';
            }

            this.ctx.strokeStyle = strokeStyle;
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.arc(sx, sy, t.radius, 0, Math.PI * 2);
            this.ctx.stroke();

            // Inner shrinking/filling charge
            this.ctx.fillStyle = fillStyle;
            this.ctx.beginPath();
            this.ctx.arc(sx, sy, t.radius * progress, 0, Math.PI * 2);
            this.ctx.fill();

            // Warning icon
            this.ctx.font = 'bold 11px sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.fillStyle = warnColor;
            this.ctx.fillText('!', sx, sy + 4);
            this.ctx.restore();
        }
    });
};


Game.spawnBossGroundHazard = function(x, y, type, duration, damage) {
    this.bossGroundHazards = this.bossGroundHazards || [];
    this.bossGroundHazards.push({
        id: 'hazard_' + performance.now() + '_' + Math.random(),
        type,
        x,
        y,
        radius: 20,
        duration,
        tickTimer: 0,
        damage
    });
};


Game.updateBossGroundHazards = function(dt) {
    if (!this.bossGroundHazards || this.bossGroundHazards.length === 0) return;

    for (let i = this.bossGroundHazards.length - 1; i >= 0; i--) {
        const h = this.bossGroundHazards[i];
        h.duration -= dt;
        h.tickTimer -= dt;

        if (h.duration <= 0) {
            this.bossGroundHazards.splice(i, 1);
            continue;
        }

        const dist = Math.hypot((this.player.x + 12) - h.x, (this.player.y + 14) - h.y);
        if (dist < h.radius && h.tickTimer <= 0) {
            h.tickTimer = 650;
            // Ground Hazard Immunity (from Hydrakis Venom Amulet, Firewalker Band, or Sacred Purification Tea)
            if (this.player.equippedShield === 'hydrakis_venom_pendant' || (this.getItemCount && this.getItemCount('ring_of_fire_walker') > 0) || this.player.buffs?.hazardImmune) {
                this.spawnParticles(this.player.x + 12, this.player.y + 14, '#4ade80', 2);
                continue;
            }
            const dmg = h.damage || (h.type === 'electric_patch' ? 12 : 8);
            this.damagePlayer(dmg);
            if (h.type === 'electric_patch') {
                this.spawnParticles(this.player.x + 12, this.player.y + 14, '#38bdf8', 8);
                this.addFloatingText('★ ไฟฟ้าสถิตช็อต!', this.player.x, this.player.y - 12, '#38bdf8');
            } else if (h.type === 'fire_patch') {
                this.spawnParticles(this.player.x + 12, this.player.y + 14, '#f97316', 6);
                this.addFloatingText('★ เปลวเพลิงเผาไหม้!', this.player.x, this.player.y - 12, '#f87171');
            } else {
                this.spawnParticles(this.player.x + 12, this.player.y + 14, '#a855f7', 6);
                this.addFloatingText('★ ติดพิษสปอร์ใต้ดิน!', this.player.x, this.player.y - 12, '#c084fc');
            }
        }
    }
};


Game.drawBossGroundHazards = function() {
    if (!this.bossGroundHazards || this.bossGroundHazards.length === 0) return;

    this.bossGroundHazards.forEach(h => {
        const sx = Math.round(h.x - this.camera.x);
        const sy = Math.round(h.y - this.camera.y);
        const flicker = Math.sin((performance.now() + h.x) / 100) * 2;

        this.ctx.save();
        if (h.type === 'fire_patch') {
            this.ctx.fillStyle = 'rgba(234, 88, 12, 0.4)';
            this.ctx.beginPath();
            this.ctx.ellipse(sx, sy, h.radius + flicker, h.radius * 0.6 + flicker * 0.5, 0, 0, Math.PI * 2);
            this.ctx.fill();

            this.ctx.fillStyle = '#fde047';
            this.ctx.fillRect(sx - 4 + flicker, sy - 4, 3, 5);
            this.ctx.fillRect(sx + 3 - flicker, sy - 6, 2, 6);
            this.ctx.fillStyle = '#ea580c';
            this.ctx.fillRect(sx - 2, sy - 8, 4, 4);
        } else if (h.type === 'electric_patch') {
            this.ctx.fillStyle = 'rgba(56, 189, 248, 0.35)';
            this.ctx.beginPath();
            this.ctx.ellipse(sx, sy, h.radius + flicker * 0.8, h.radius * 0.6 + flicker * 0.4, 0, 0, Math.PI * 2);
            this.ctx.fill();

            this.ctx.strokeStyle = '#facc15';
            this.ctx.lineWidth = 1.5;
            this.ctx.beginPath();
            this.ctx.moveTo(sx - 5 + flicker, sy - 4);
            this.ctx.lineTo(sx - 1, sy);
            this.ctx.lineTo(sx - 4, sy + 3);
            this.ctx.stroke();

            this.ctx.strokeStyle = '#38bdf8';
            this.ctx.beginPath();
            this.ctx.moveTo(sx + 2, sy - 5);
            this.ctx.lineTo(sx + 6 + flicker, sy);
            this.ctx.lineTo(sx + 3, sy + 4);
            this.ctx.stroke();
        } else {
            this.ctx.fillStyle = 'rgba(147, 51, 234, 0.35)';
            this.ctx.beginPath();
            this.ctx.ellipse(sx, sy, h.radius, h.radius * 0.6, 0, 0, Math.PI * 2);
            this.ctx.fill();

            this.ctx.fillStyle = '#a855f7';
            this.ctx.fillRect(sx - 5, sy - 7, 2, 7);
            this.ctx.fillRect(sx + 4, sy - 8, 3, 8);
            this.ctx.fillRect(sx, sy - 5, 2, 5);
        }
        this.ctx.restore();
    });
};


Game.spawnBossShockwave = function(x, y) {
    this.bossShockwaves = this.bossShockwaves || [];
    this.bossShockwaves.push({
        x,
        y,
        radius: 15,
        maxRadius: 180,
        speed: 0.28,
        damage: 20,
        hitPlayer: false
    });
};


Game.updateBossShockwaves = function(dt) {
    if (!this.bossShockwaves || this.bossShockwaves.length === 0) return;

    for (let i = this.bossShockwaves.length - 1; i >= 0; i--) {
        const sw = this.bossShockwaves[i];
        sw.radius += sw.speed * dt;

        if (sw.radius >= sw.maxRadius) {
            this.bossShockwaves.splice(i, 1);
            continue;
        }

        if (!sw.hitPlayer) {
            const dist = Math.hypot((this.player.x + 12) - sw.x, (this.player.y + 14) - sw.y);
            if (Math.abs(dist - sw.radius) < 18) {
                sw.hitPlayer = true;
                this.damagePlayer(sw.damage, this.boss);
                this.triggerScreenShake(5.0, 160);
                const knockAngle = Math.atan2((this.player.y + 14) - sw.y, (this.player.x + 12) - sw.x);
                this.player.x += Math.cos(knockAngle) * 32;
                this.player.y += Math.sin(knockAngle) * 32;
                this.addFloatingText('★ คลื่นกระแทกมฤตยู!', this.player.x, this.player.y - 15, '#f87171');
                this.spawnParticles(this.player.x + 12, this.player.y + 14, '#ef4444', 12);
            }
        }
    }
};


Game.drawBossShockwaves = function() {
    if (!this.bossShockwaves || this.bossShockwaves.length === 0) return;

    this.bossShockwaves.forEach(sw => {
        const sx = Math.round(sw.x - this.camera.x);
        const sy = Math.round(sw.y - this.camera.y);
        const alpha = Math.max(0, 1 - (sw.radius / sw.maxRadius));

        this.ctx.save();
        this.ctx.strokeStyle = `rgba(239, 68, 68, ${alpha * 0.85})`;
        this.ctx.lineWidth = 4;
        this.ctx.beginPath();
        this.ctx.arc(sx, sy, sw.radius, 0, Math.PI * 2);
        this.ctx.stroke();

        this.ctx.strokeStyle = `rgba(168, 85, 247, ${alpha * 0.6})`;
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.arc(sx, sy, Math.max(0, sw.radius - 8), 0, Math.PI * 2);
        this.ctx.stroke();
        this.ctx.restore();
    });
};


Game.updateBossDashGhosts = function(dt) {
    if (!this.bossDashGhosts || this.bossDashGhosts.length === 0) return;

    for (let i = this.bossDashGhosts.length - 1; i >= 0; i--) {
        const g = this.bossDashGhosts[i];
        g.alpha -= dt * 0.0035;
        if (g.alpha <= 0) {
            this.bossDashGhosts.splice(i, 1);
        }
    }
};


Game.drawBossDashGhosts = function() {
    if (!this.bossDashGhosts || this.bossDashGhosts.length === 0) return;

    this.bossDashGhosts.forEach(g => {
        const bx = Math.round(g.x - this.camera.x);
        const by = Math.round(g.y - this.camera.y);
        const bId = this.boss ? this.boss.id : 'boss_kathuros';
        const bossSprites = (SPRITES.bosses && SPRITES.bosses[bId]) || SPRITES.bossKathuros;
        const spr = (bossSprites && bossSprites[g.frame]) || bossSprites[0] || SPRITES.bossKathuros[0];
        if (spr) {
            this.ctx.save();
            this.ctx.globalAlpha = Math.max(0, g.alpha * 0.72);
            this.ctx.drawImage(spr, bx, by);
            this.ctx.globalCompositeOperation = 'lighter';
            this.ctx.globalAlpha = Math.max(0, g.alpha * 0.5);
            this.ctx.drawImage(spr, bx, by);
            this.ctx.restore();
        }
    });
};


Game.updateBoss = function(dt) {
    const bossScenes = ['forest', 'cave_depths', 'swamp', 'volcano', 'frost_peak', 'crypt', 'ancient_canopy', 'tempest_plateau', 'island_volcano'];
    if (!bossScenes.includes(this.currentScene) || !this.boss || !this.boss.alive) {
        const bossBar = document.getElementById('bossHealthBar');
        if (bossBar && bossBar.style.display !== 'none') bossBar.style.display = 'none';
        if (typeof SoundEngine.setBossBattle === 'function') SoundEngine.setBossBattle(false);
        return;
    }

    if (this.boss.flashTimer > 0) this.boss.flashTimer -= dt;
    if (this.boss.squashX && this.boss.squashX !== 1.0) {
        this.boss.squashX += (1.0 - this.boss.squashX) * 0.22;
        if (Math.abs(this.boss.squashX - 1.0) < 0.02) this.boss.squashX = 1.0;
    }
    if (this.boss.squashY && this.boss.squashY !== 1.0) {
        this.boss.squashY += (1.0 - this.boss.squashY) * 0.22;
        if (Math.abs(this.boss.squashY - 1.0) < 0.02) this.boss.squashY = 1.0;
    }

    const dist = Math.hypot((this.player.x + 12) - (this.boss.x + 32), (this.player.y + 14) - (this.boss.y + 32));

    // Dark Souls Menacing Titles
    const bossTitles: Record<string, string> = {
        'boss_kathuros': 'คาธูรอส, มหาวิปลาสสปอร์ปีศาจแห่งป่าชั่วนิรันดร์',
        'boss_luminarch': 'ลูมินาร์ค, ราชันย์ผลึกสุริยะนิรันดร์กาล',
        'boss_hydrakis': 'ไฮดราคิส, อสรพิษมรณะสามเศียรกลูมสแวมป์',
        'boss_ignistron': 'อิกนิสตรอน, มังกรเพลิงโลกันตร์ผู้กลืนกินภูเขาไฟ',
        'boss_frostfang': 'ฟรอสต์แฟงก์, จอมไททันเยือกแข็งแห่งกลาเซียร์',
        'boss_malakor': 'มาลาคอร์, ลอร์ดมรณะผู้บงการวิญญาณแห่งความมืด',
        'boss_sylvanus': 'ซิลวาเนีย, เทพพฤกษาบรรพกาลผู้พิโรธ',
        'boss_astreon': 'ออสทริออน, จ้าวทัณฑ์อัสนีบาตไร้พ่าย'
    };

    // Boss Activation & Dark Souls Health Bar
    const bossBar = document.getElementById('bossHealthBar');
    if (dist < 550) {
        this.boss.active = true;
        if (bossBar) bossBar.style.display = 'flex';
        if (typeof SoundEngine.setBossBattle === 'function') SoundEngine.setBossBattle(true);

        const hpPct = Math.max(0, (this.boss.hp / this.boss.maxHp) * 100);
        const bossHpFill = document.getElementById('bossHpFill');
        if (bossHpFill) bossHpFill.style.width = hpPct + '%';

        // Dark Souls Lagging Damage Drain Bar
        const bossHpDrain = document.getElementById('bossHpDrain');
        if (bossHpDrain) {
            if (!this.boss.drainTimer || this.boss.drainTimer <= 0) {
                this.boss.drainTimer = 260;
            } else {
                this.boss.drainTimer -= dt;
                if (this.boss.drainTimer <= 0) {
                    bossHpDrain.style.width = hpPct + '%';
                }
            }
        }

        const bossNameEl = document.getElementById('bossNameText');
        if (bossNameEl) bossNameEl.textContent = bossTitles[this.boss.id] || this.boss.name;

        const bossHpText = document.getElementById('bossHpText');
        if (bossHpText) {
            const phaseTitle = this.boss.phase === 3 ? '[เฟส 3: BERSERK คลั่งขั้นสุด]' : (this.boss.phase === 2 ? '[เฟส 2: พิโรธ]' : '[เฟส 1]');
            bossHpText.textContent = `${phaseTitle} ${this.boss.hp} / ${this.boss.maxHp} HP`;
        }
    } else if (dist > 800) {
        this.boss.active = false;
        if (bossBar) bossBar.style.display = 'none';
        if (typeof SoundEngine.setBossBattle === 'function') SoundEngine.setBossBattle(false);
    }

    if (this.boss.active) {
        if (this.boss.flashTimer > 0) this.boss.flashTimer -= dt;

        const p2Hp = Math.round(this.boss.maxHp * 0.66);
        const p3Hp = Math.round(this.boss.maxHp * 0.33);

        // Phase Transitions
        if (this.boss.phase === 1 && this.boss.hp <= p2Hp) {
            this.boss.phase = 2;
            SoundEngine.bossPhaseChange();
            this.triggerScreenShake(8.0, 380);
            this.triggerHitstop(80);
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#a855f7', 40);
            this.addFloatingText(`★ ${this.boss.name} พิโรธ! ปลดปล่อยพลังขั้นที่ 2!`, this.boss.x - 40, this.boss.y - 25, '#c084fc');
            this.spawnBossShockwave(this.boss.x + 32, this.boss.y + 32);
        } else if (this.boss.phase === 2 && this.boss.hp <= p3Hp) {
            this.boss.phase = 3; // DARK SOULS BERSERK
            SoundEngine.bossPhaseChange();
            this.triggerScreenShake(10.0, 500);
            this.triggerHitstop(120);
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#ef4444', 50);
            this.addFloatingText(`★ ${this.boss.name} เข้าสู่สถานะ BERSERK คลั่งขั้นสุด!`, this.boss.x - 40, this.boss.y - 25, '#f87171');
            
            // Opening Calamity Salvo
            if (this.boss.id === 'boss_astreon') {
                for (let m = 0; m < 5; m++) {
                    setTimeout(() => {
                        if (this.boss && this.boss.alive) {
                            const rx = (this.boss.x - 160) + Math.random() * 320;
                            const ry = (this.boss.y - 120) + Math.random() * 240;
                            this.spawnBossTelegraph('lightning', rx, ry, 34, 600 + m * 140, 45);
                        }
                    }, m * 150);
                }
            } else if (this.boss.id === 'boss_sylvanus') {
                for (let m = 0; m < 5; m++) {
                    setTimeout(() => {
                        if (this.boss && this.boss.alive) {
                            const rx = (this.boss.x - 160) + Math.random() * 320;
                            const ry = (this.boss.y - 120) + Math.random() * 240;
                            this.spawnBossTelegraph('thorn_trap', rx, ry, 30, 500 + m * 160, 35);
                        }
                    }, m * 180);
                }
            } else if (this.boss.id === 'boss_frostfang') {
                this.spawnBossTelegraph('ice_boulder', this.player.x + 12, this.player.y + 14, 36, 750, 45);
                this.spawnBossTelegraph('ice_boulder', this.player.x - 45, this.player.y - 30, 36, 950, 45);
            } else if (this.boss.id === 'boss_malakor') {
                this.spawnBossTelegraph('void_singularity', this.boss.x + 32, this.boss.y + 32, 65, 1600, 50);
            } else {
                for (let m = 0; m < 5; m++) {
                    setTimeout(() => {
                        if (this.boss && this.boss.alive) {
                            const rx = (this.boss.x - 160) + Math.random() * 320;
                            const ry = (this.boss.y - 120) + Math.random() * 240;
                            this.spawnBossTelegraph('meteor', rx, ry, 34, 750 + m * 160, 40);
                        }
                    }, m * 200);
                }
            }
        }

        // Animation
        this.boss.animTimer = (this.boss.animTimer || 0) + dt;
        const animSpeed = this.boss.phase === 3 ? 100 : 160;
        if (this.boss.animTimer > animSpeed) {
            this.boss.animTimer = 0;
            this.boss.frame = (this.boss.frame + 1) % 2;
        }

        // Dashing State Handler
        if (this.boss.state === 'dashing' && this.boss.dashTarget) {
            this.boss.x += this.boss.dashTarget.vx;
            this.boss.y += this.boss.dashTarget.vy;
            const stepDist = Math.hypot(this.boss.dashTarget.vx, this.boss.dashTarget.vy);
            this.boss.dashTarget.distLeft -= stepDist;

            if (Math.random() < 0.7) {
                this.bossDashGhosts.push({
                    x: this.boss.x,
                    y: this.boss.y,
                    frame: this.boss.frame,
                    alpha: 0.85
                });
            }
            if (Math.random() < 0.4) {
                const hz = (this.boss.id === 'boss_astreon') ? 'electric_patch' : 
                           ((this.boss.id === 'boss_ignistron') ? 'fire_patch' : 'poison_thorn');
                this.spawnBossGroundHazard(this.boss.x + 32, this.boss.y + 32, hz, 3200, 12);
            }

            // Hit player during dash
            const dashHitDist = Math.hypot((this.player.x + 12) - (this.boss.x + 32), (this.player.y + 14) - (this.boss.y + 32));
            if (dashHitDist < 38) {
                this.damagePlayer(this.boss.phase === 3 ? 45 : 35, this.boss);
                this.triggerScreenShake(7.0, 200);
                this.spawnParticles(this.player.x + 12, this.player.y + 14, '#ef4444', 18);
            }

            if (this.boss.dashTarget.distLeft <= 0) {
                this.boss.state = 'normal';
                this.boss.dashTarget = null;
            }
        } else {
            // Dedicated Boss AI routine dispatcher
            const bId = this.boss.id;
            if (bId === 'boss_kathuros') {
                this.updateKathurosBoss(dt, dist);
            } else if (bId === 'boss_luminarch') {
                this.updateLuminarchBoss(dt, dist);
            } else if (bId === 'boss_hydrakis') {
                this.updateHydrakisBoss(dt, dist);
            } else if (bId === 'boss_ignistron') {
                this.updateIgnistronBoss(dt, dist);
            } else if (bId === 'boss_frostfang') {
                this.updateFrostfangBoss(dt, dist);
            } else if (bId === 'boss_malakor') {
                this.updateMalakorBoss(dt, dist);
            } else if (bId === 'boss_sylvanus') {
                this.updateSylvanusBoss(dt, dist);
            } else if (bId === 'boss_astreon') {
                this.updateAstreonBoss(dt, dist);
            } else if (bId === 'boss_karzarak') {
                this.updateKarzarakBoss(dt, dist);
            } else {
                this.updateKathurosBoss(dt, dist);
            }
        }
    }
};


// 1. KATHUROS: Spore Demon Sovereign (5 Distinct Attacks)
Game.updateKathurosBoss = function(dt, dist) {
    const p = this.boss.phase;
    const speed = p === 3 ? 2.0 : (p === 2 ? 1.5 : 1.15);

    if (dist > 70) {
        const ang = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32));
        this.boss.x += Math.cos(ang) * speed;
        this.boss.y += Math.sin(ang) * speed;
    }

    this.boss.attackCooldown -= dt;
    if (this.boss.attackCooldown <= 0) {
        this.boss.attackCooldown = p === 3 ? 580 : (p === 2 ? 1000 : 1400);
        const roll = Math.random();

        // Guaranteed 5-Attack Round-Robin Combo Sequence:
        const step = (this.boss.comboStep || 0) % 5;
        this.boss.comboStep = step + 1;

        if (step === 0) {
            // Move 1: Spore Needle Spiral
            SoundEngine.bossSporeSpiral();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#a855f7', 16);
            this.addFloatingText('★ [คาธูรอส] คลื่นเข็มสปอร์ควงสว่าน!', this.boss.x - 20, this.boss.y - 20, '#a855f7');
            this.boss.spiralAngle = (this.boss.spiralAngle || 0) + 0.45;
            const count = p === 3 ? 16 : 12;
            for (let i = 0; i < count; i++) {
                const ang = (i / count) * Math.PI * 2 + this.boss.spiralAngle;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 4.8, vy: Math.sin(ang) * 4.8,
                    angle: ang, damage: 26, rangeLeft: 460,
                    type: 'spore_spiral', fromBoss: true
                });
            }
        } else if (step === 1) {
            // Move 2: Homing Fungal Souls
            SoundEngine.bossSporeSpiral();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#ec4899', 16);
            this.addFloatingText('★ [คาธูรอส] วิญญาณสปอร์ติดตาม!', this.boss.x - 20, this.boss.y - 20, '#ec4899');
            [-0.35, 0, 0.35].forEach(off => {
                const bAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32)) + off;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(bAng) * 3.4, vy: Math.sin(bAng) * 3.4,
                    angle: bAng, damage: 28, rangeLeft: 540,
                    type: 'homing_spore', fromBoss: true
                });
            });
        } else if (step === 2) {
            // Move 3: Erupting Poison Brambles (Roll Catch)
            SoundEngine.bossTelegraph();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#22c55e', 14);
            this.addFloatingText('★ [คาธูรอส] หนามพิษปะทุใต้พิภพ!', this.boss.x - 20, this.boss.y - 20, '#22c55e');
            this.spawnBossTelegraph('spike', this.player.x + 12, this.player.y + 14, 28, 750, 32);
            this.spawnBossTelegraph('spike', this.player.x - 30, this.player.y + 15, 26, 750, 28);
            this.spawnBossTelegraph('spike', this.player.x + 30, this.player.y - 15, 26, 750, 28);
        } else if (step === 3) {
            // Move 4: Predatory Fungal Lunge (Gap Closer)
            SoundEngine.bossTelegraph();
            this.addFloatingText('★ [คาธูรอส] พุ่งขย้ำพริบตา!', this.boss.x - 20, this.boss.y - 20, '#ef4444');
            this.spawnBossTelegraph('dash', this.boss.x + 32, this.boss.y + 32, 280, 440, 38, this.player.x + 12, this.player.y + 14);
        } else {
            // Move 5: Toxic Cataclysm Supernova (Signature Calamity)
            SoundEngine.bossSporeSpiral();
            SoundEngine.bossShockwave();
            this.spawnBossShockwave(this.boss.x + 32, this.boss.y + 32);
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#a855f7', 26);
            this.addFloatingText('★ [ท่าไม้ตายบอส] มหาวินาศสปอร์ล้างโลก!', this.boss.x - 35, this.boss.y - 25, '#c084fc');
            for (let i = 0; i < 20; i++) {
                const ang = (i / 20) * Math.PI * 2;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 5.0, vy: Math.sin(ang) * 5.0,
                    angle: ang, damage: 32, rangeLeft: 480,
                    type: 'spore_spiral', fromBoss: true
                });
            }
            if (p >= 2) {
                for (let m = 0; m < 3; m++) {
                    const mx = (this.boss.x - 140) + Math.random() * 280;
                    const my = (this.boss.y - 90) + Math.random() * 180;
                    this.spawnBossTelegraph('meteor', mx, my, 30, 650 + m * 140, 38);
                }
            }
        }
    }

    // Minion summon
    this.boss.summonCooldown -= dt;
    if (this.boss.summonCooldown <= 0) {
        this.boss.summonCooldown = p === 3 ? 8000 : 11000;
        SoundEngine.bossRoar();
        this.addFloatingText('★ คาธูรอสคำราม! ปลุกฝูงอสูรเงาสปอร์!', this.boss.x + 10, this.boss.y - 15, '#ef4444');
        this.worldMonsters.push({
            id: 'minion_' + performance.now(),
            type: 'shadow_wolf',
            x: this.boss.x - 30, y: this.boss.y + 20,
            hp: 60, maxHp: 60, speed: 1.6, damage: 16,
            aggroRange: 320, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0
        });
    }
};


// 2. LUMINARCH: Solar Crystal Monarch (5 Distinct Attacks)
Game.updateLuminarchBoss = function(dt, dist) {
    const p = this.boss.phase;
    const speed = p === 3 ? 2.1 : (p === 2 ? 1.6 : 1.2);

    if (dist > 85) {
        const ang = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32));
        this.boss.x += Math.cos(ang) * speed;
        this.boss.y += Math.sin(ang) * speed;
    }

    this.boss.attackCooldown -= dt;
    if (this.boss.attackCooldown <= 0) {
        this.boss.attackCooldown = p === 3 ? 560 : (p === 2 ? 950 : 1350);

        const step = (this.boss.comboStep || 0) % 5;
        this.boss.comboStep = step + 1;

        if (step === 0) {
            // Move 1: Prismatic Cross Shards
            SoundEngine.bossLaser();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#c084fc', 14);
            this.addFloatingText('★ [ลูมินาร์ค] ม่านผลึกสุริยันตัดไขว้!', this.boss.x - 20, this.boss.y - 20, '#c084fc');
            this.boss.prismAngle = (this.boss.prismAngle || 0) + Math.PI / 4;
            const count = p === 3 ? 14 : 10;
            for (let i = 0; i < count; i++) {
                const ang = (i / count) * Math.PI * 2 + this.boss.prismAngle;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 4.8, vy: Math.sin(ang) * 4.8,
                    angle: ang, damage: 28, rangeLeft: 480,
                    type: 'crystal_shard', fromBoss: true
                });
            }
        } else if (step === 1) {
            // Move 2: Solar Lance Piercing Thrust
            SoundEngine.bossLaserSweep();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#fde047', 16);
            this.addFloatingText('★ [ลูมินาร์ค] หอกแสงสุริยันทะลวงมิติ!', this.boss.x - 20, this.boss.y - 20, '#fde047');
            const bAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32));
            this.projectiles.push({
                x: this.boss.x + 32, y: this.boss.y + 32,
                vx: Math.cos(bAng) * 7.8, vy: Math.sin(bAng) * 7.8,
                angle: bAng, damage: 44, rangeLeft: 600,
                type: 'solar_beam', fromBoss: true
            });
            if (p >= 2) {
                [-0.28, 0.28].forEach(off => {
                    this.projectiles.push({
                        x: this.boss.x + 32, y: this.boss.y + 32,
                        vx: Math.cos(bAng + off) * 7.0, vy: Math.sin(bAng + off) * 7.0,
                        angle: bAng + off, damage: 35, rangeLeft: 560,
                        type: 'solar_beam', fromBoss: true
                    });
                });
            }
        } else if (step === 2) {
            // Move 3: Prismatic Starburst Nova
            SoundEngine.bossShockwave();
            this.spawnBossShockwave(this.boss.x + 32, this.boss.y + 32);
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#facc15', 18);
            this.addFloatingText('★ [ลูมินาร์ค] ระเบิดแสงดาราจักร!', this.boss.x - 20, this.boss.y - 20, '#facc15');
            for (let i = 0; i < 14; i++) {
                const ang = (i / 14) * Math.PI * 2;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 5.0, vy: Math.sin(ang) * 5.0,
                    angle: ang, damage: 32, rangeLeft: 480,
                    type: 'crystal_shard', fromBoss: true
                });
            }
        } else if (step === 3) {
            // Move 4: Solar Flash Ambush (Gap Closer)
            SoundEngine.bossTelegraph();
            this.addFloatingText('★ [ลูมินาร์ค] ก้าวพริบตาสุริยัน!', this.boss.x - 20, this.boss.y - 20, '#38bdf8');
            this.spawnBossTelegraph('dash', this.boss.x + 32, this.boss.y + 32, 280, 440, 40, this.player.x + 12, this.player.y + 14);
        } else {
            // Move 5: Quad Solar Beam Supernova (Signature Calamity)
            SoundEngine.bossLaserSweep();
            this.spawnBossShockwave(this.boss.x + 32, this.boss.y + 32);
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#fde047', 25);
            this.addFloatingText('★ [ท่าไม้ตายบอส] ซูเปอร์โนวาสี่ทิศส่องหล้า!', this.boss.x - 35, this.boss.y - 25, '#fde047');
            this.boss.prismAngle = (this.boss.prismAngle || 0) + 0.35;
            [0, Math.PI / 2, Math.PI, Math.PI * 1.5].forEach(ang => {
                const curAng = ang + this.boss.prismAngle;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(curAng) * 7.2, vy: Math.sin(curAng) * 7.2,
                    angle: curAng, damage: 46, rangeLeft: 600,
                    type: 'solar_beam', fromBoss: true
                });
            });
            for (let i = 0; i < 16; i++) {
                const ang = (i / 16) * Math.PI * 2;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 4.6, vy: Math.sin(ang) * 4.6,
                    angle: ang, damage: 28, rangeLeft: 460,
                    type: 'crystal_shard', fromBoss: true
                });
            }
        }
    }

    this.boss.summonCooldown -= dt;
    if (this.boss.summonCooldown <= 0) {
        this.boss.summonCooldown = p === 3 ? 9000 : 12000;
        SoundEngine.bossRoar();
        this.addFloatingText('★ ลูมินาร์คเสกผลึกสุริยะ! แมงมุมผลึกกำเนิด!', this.boss.x + 10, this.boss.y - 15, '#38bdf8');
        this.worldMonsters.push({
            id: 'minion_' + performance.now(),
            type: 'crystal_spider',
            x: this.boss.x - 30, y: this.boss.y + 20,
            hp: 75, maxHp: 75, speed: 1.7, damage: 18,
            aggroRange: 340, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0
        });
    }
};


// 3. HYDRAKIS: Three-Headed Toxic Wyrm (5 Distinct Attacks)
Game.updateHydrakisBoss = function(dt, dist) {
    const p = this.boss.phase;
    const speed = p === 3 ? 2.15 : (p === 2 ? 1.65 : 1.25);

    this.boss.slitherTimer = (this.boss.slitherTimer || 0) + dt * 0.007;
    if (dist > 75) {
        const baseAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32));
        const weave = Math.sin(this.boss.slitherTimer) * 0.45;
        const ang = baseAng + weave;
        this.boss.x += Math.cos(ang) * speed;
        this.boss.y += Math.sin(ang) * speed;
    }

    this.boss.attackCooldown -= dt;
    if (this.boss.attackCooldown <= 0) {
        this.boss.attackCooldown = p === 3 ? 540 : (p === 2 ? 900 : 1300);

        const step = (this.boss.comboStep || 0) % 5;
        this.boss.comboStep = step + 1;

        if (step === 0) {
            // Move 1: Triple Head Synchronous Spit
            SoundEngine.bossPoisonSpit();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#84cc16', 14);
            this.addFloatingText('★ [ไฮดราคิส] พ่นกระสุนพิษสามหัว!', this.boss.x - 20, this.boss.y - 20, '#84cc16');
            [-0.3, 0, 0.3].forEach(headOffset => {
                for (let b = -1; b <= 1; b++) {
                    const bAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32)) + headOffset + b * 0.12;
                    this.projectiles.push({
                        x: this.boss.x + 32, y: this.boss.y + 32,
                        vx: Math.cos(bAng) * 4.4, vy: Math.sin(bAng) * 4.4,
                        angle: bAng, damage: 26, rangeLeft: 480,
                        type: 'poison_glob', fromBoss: true
                    });
                }
            });
        } else if (step === 1) {
            // Move 2: Corrosive Acid Deluge
            SoundEngine.bossPoisonSpit();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#22c55e', 16);
            this.addFloatingText('★ [ไฮดราคิส] คลื่นสาดกรดกัดกร่อน!', this.boss.x - 20, this.boss.y - 20, '#22c55e');
            for (let a = 0; a < 4; a++) {
                const spread = (a - 1.5) * 0.28;
                const bAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32)) + spread;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(bAng) * 4.0, vy: Math.sin(bAng) * 4.0,
                    angle: bAng, damage: 32, rangeLeft: 520,
                    type: 'acid_deluge', fromBoss: true
                });
            }
        } else if (step === 2) {
            // Move 3: Tail Thrash Shockwave
            SoundEngine.bossShockwave();
            this.triggerScreenShake(6.5, 220);
            this.spawnBossShockwave(this.boss.x + 32, this.boss.y + 32);
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#15803d', 18);
            this.addFloatingText('★ [ไฮดราคิส] คลื่นกระแทกหางอสรพิษ!', this.boss.x - 20, this.boss.y - 20, '#15803d');
            for (let i = 0; i < 14; i++) {
                const ang = (i / 14) * Math.PI * 2;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 4.6, vy: Math.sin(ang) * 4.6,
                    angle: ang, damage: 30, rangeLeft: 460,
                    type: 'poison_glob', fromBoss: true
                });
            }
        } else if (step === 3) {
            // Move 4: Abyssal Slither Thrash (Gap Closer)
            SoundEngine.bossTelegraph();
            this.addFloatingText('★ [ไฮดราคิส] เลื้อยพุ่งชนมรณะ!', this.boss.x - 20, this.boss.y - 20, '#84cc16');
            this.spawnBossTelegraph('dash', this.boss.x + 32, this.boss.y + 32, 280, 440, 38, this.player.x + 12, this.player.y + 14);
        } else {
            // Move 5: Toxic Geyser Meltdown (Signature Calamity)
            SoundEngine.bossTelegraph();
            SoundEngine.bossShockwave();
            this.spawnBossShockwave(this.boss.x + 32, this.boss.y + 32);
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#22c55e', 24);
            this.addFloatingText('★ [ท่าไม้ตายบอส] มหาธรณีพิษหลอมละลาย!', this.boss.x - 35, this.boss.y - 25, '#22c55e');
            for (let i = -2; i <= 2; i++) {
                const bAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32)) + i * 0.2;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(bAng) * 4.6, vy: Math.sin(bAng) * 4.6,
                    angle: bAng, damage: 34, rangeLeft: 500,
                    type: 'poison_glob', fromBoss: true
                });
            }
            this.spawnBossTelegraph('spike', this.player.x + 12, this.player.y + 14, 30, 700, 36);
            this.spawnBossTelegraph('spike', this.player.x + 35, this.player.y, 28, 700, 32);
            this.spawnBossTelegraph('spike', this.player.x - 35, this.player.y, 28, 700, 32);
        }
    }

    this.boss.summonCooldown -= dt;
    if (this.boss.summonCooldown <= 0) {
        this.boss.summonCooldown = p === 3 ? 8500 : 11000;
        SoundEngine.bossRoar();
        this.addFloatingText('★ ไฮดราคิสฟาดหาง! จระเข้บึงมรณะตื่นขึ้น!', this.boss.x + 10, this.boss.y - 15, '#84cc16');
        this.worldMonsters.push({
            id: 'minion_' + performance.now(),
            type: 'swamp_croc',
            x: this.boss.x - 30, y: this.boss.y + 20,
            hp: 85, maxHp: 85, speed: 1.5, damage: 20,
            aggroRange: 320, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0
        });
    }
};


// 4. IGNISTRON: Infernal Magma Dragon (5 Distinct Attacks)
Game.updateIgnistronBoss = function(dt, dist) {
    const p = this.boss.phase;
    const speed = p === 3 ? 2.2 : (p === 2 ? 1.7 : 1.3);

    if (dist > 80) {
        const ang = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32));
        this.boss.x += Math.cos(ang) * speed;
        this.boss.y += Math.sin(ang) * speed;
    }

    this.boss.attackCooldown -= dt;
    if (this.boss.attackCooldown <= 0) {
        this.boss.attackCooldown = p === 3 ? 500 : (p === 2 ? 850 : 1250);

        const step = (this.boss.comboStep || 0) % 5;
        this.boss.comboStep = step + 1;

        if (step === 0) {
            // Move 1: Dragon Flamethrower Fan
            SoundEngine.bossDragonBreath();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#ea580c', 16);
            this.addFloatingText('★ [อิกนิสตรอน] พ่นเพลิงโลกันตร์พัดคลื่น!', this.boss.x - 20, this.boss.y - 20, '#ea580c');
            for (let i = -3; i <= 3; i++) {
                const bAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32)) + i * 0.15;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(bAng) * 5.0, vy: Math.sin(bAng) * 5.0,
                    angle: bAng, damage: 30, rangeLeft: 480,
                    type: 'dragon_fire', fromBoss: true
                });
            }
        } else if (step === 1) {
            // Move 2: Magma Artillery Cannon
            SoundEngine.bossDragonBreath();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#f97316', 16);
            this.addFloatingText('★ [อิกนิสตรอน] กระสุนปืนใหญ่อัคนี!', this.boss.x - 20, this.boss.y - 20, '#f97316');
            [-0.2, 0.2].forEach(off => {
                const bAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32)) + off;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(bAng) * 6.0, vy: Math.sin(bAng) * 6.0,
                    angle: bAng, damage: 42, rangeLeft: 560,
                    type: 'dragon_fire', fromBoss: true
                });
            });
        } else if (step === 2) {
            // Move 3: Volcanic Meteor Bombardment
            SoundEngine.bossMeteor();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#facc15', 18);
            this.addFloatingText('★ [อิกนิสตรอน] ฝนอุกกาบาตภูเขาไฟ!', this.boss.x - 20, this.boss.y - 20, '#facc15');
            for (let m = 0; m < 4; m++) {
                const mx = (this.boss.x - 150) + Math.random() * 300;
                const my = (this.boss.y - 110) + Math.random() * 220;
                this.spawnBossTelegraph('meteor', mx, my, 32, 650 + m * 140, 48);
            }
        } else if (step === 3) {
            // Move 4: Blazing Hellfire Charge (Gap Closer)
            SoundEngine.bossTelegraph();
            this.addFloatingText('★ [อิกนิสตรอน] บินโฉบพุ่งชนเปลวเพลิง!', this.boss.x - 20, this.boss.y - 20, '#ef4444');
            this.spawnBossTelegraph('dash', this.boss.x + 32, this.boss.y + 32, 280, 440, 44, this.player.x + 12, this.player.y + 14);
        } else {
            // Move 5: Hellfire Supernova (Signature Calamity)
            SoundEngine.bossDragonBreath();
            SoundEngine.bossShockwave();
            this.spawnBossShockwave(this.boss.x + 32, this.boss.y + 32);
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#ef4444', 25);
            this.addFloatingText('★ [ท่าไม้ตายบอส] มหาเพลิงโลกันตร์ล้างพิภพ!', this.boss.x - 35, this.boss.y - 25, '#ef4444');
            this.boss.spiralAngle = (this.boss.spiralAngle || 0) + 0.55;
            for (let i = 0; i < 24; i++) {
                const ang = (i / 24) * Math.PI * 2 + this.boss.spiralAngle;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 5.4, vy: Math.sin(ang) * 5.4,
                    angle: ang, damage: 34, rangeLeft: 500,
                    type: 'dragon_fire', fromBoss: true
                });
            }
            if (p >= 2) {
                for (let m = 0; m < 3; m++) {
                    const mx = (this.boss.x - 140) + Math.random() * 280;
                    const my = (this.boss.y - 90) + Math.random() * 180;
                    this.spawnBossTelegraph('meteor', mx, my, 32, 600 + m * 120, 50);
                }
            }
        }
    }

    this.boss.summonCooldown -= dt;
    if (this.boss.summonCooldown <= 0) {
        this.boss.summonCooldown = p === 3 ? 8000 : 11000;
        SoundEngine.bossRoar();
        this.addFloatingText('★ อิกนิสตรอนพ่นไฟ! ภูตเพลิงลาวาอุบัติ!', this.boss.x + 10, this.boss.y - 15, '#f97316');
        this.worldMonsters.push({
            id: 'minion_' + performance.now(),
            type: 'flame_spirit',
            x: this.boss.x - 30, y: this.boss.y + 20,
            hp: 75, maxHp: 75, speed: 1.6, damage: 20,
            aggroRange: 340, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0
        });
    }
};


// 5. FROSTFANG: Glacial Titan of the North (5 Distinct Attacks)
Game.updateFrostfangBoss = function(dt, dist) {
    const p = this.boss.phase;
    const speed = p === 3 ? 2.0 : (p === 2 ? 1.5 : 1.15);

    if (dist > 75) {
        const ang = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32));
        this.boss.x += Math.cos(ang) * speed;
        this.boss.y += Math.sin(ang) * speed;
    }

    this.boss.attackCooldown -= dt;
    if (this.boss.attackCooldown <= 0) {
        this.boss.attackCooldown = p === 3 ? 580 : (p === 2 ? 950 : 1350);

        const step = (this.boss.comboStep || 0) % 5;
        this.boss.comboStep = step + 1;

        if (step === 0) {
            // Move 1: Piercing Glacial Shards
            SoundEngine.bossIceShatter();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#38bdf8', 16);
            this.addFloatingText('★ [ฟรอสต์แฟงก์] ห่าผลึกน้ำแข็งแทงทะลวง!', this.boss.x - 20, this.boss.y - 20, '#38bdf8');
            for (let i = -3; i <= 3; i++) {
                const bAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32)) + i * 0.14;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(bAng) * 4.8, vy: Math.sin(bAng) * 4.8,
                    angle: bAng, damage: 28, rangeLeft: 480,
                    type: 'ice_shard', fromBoss: true
                });
            }
        } else if (step === 1) {
            // Move 2: Avalanche Boulder Slam
            SoundEngine.bossTelegraph();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#e0f2fe', 16);
            this.addFloatingText('★ [ฟรอสต์แฟงก์] หิมะถล่มทับพิภพ!', this.boss.x - 20, this.boss.y - 20, '#e0f2fe');
            this.spawnBossTelegraph('ice_boulder', this.player.x + 12, this.player.y + 14, 36, 750, 58);
        } else if (step === 2) {
            // Move 3: Glacial Fissure Stomp
            SoundEngine.bossShockwave();
            this.spawnBossShockwave(this.boss.x + 32, this.boss.y + 32);
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#7dd3fc', 18);
            this.addFloatingText('★ [ฟรอสต์แฟงก์] กระทืบพื้นธารน้ำแข็งแตก!', this.boss.x - 20, this.boss.y - 20, '#7dd3fc');
            this.spawnBossTelegraph('spike', this.player.x - 30, this.player.y - 30, 26, 750, 32);
            this.spawnBossTelegraph('spike', this.player.x + 30, this.player.y - 30, 26, 750, 32);
            this.spawnBossTelegraph('spike', this.player.x, this.player.y + 35, 26, 750, 32);
        } else if (step === 3) {
            // Move 4: Blizzard Vortex Machine Gun
            SoundEngine.bossIceShatter();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#38bdf8', 16);
            this.addFloatingText('★ [ฟรอสต์แฟงก์] มหาพายุหิมะกลืนกิน!', this.boss.x - 20, this.boss.y - 20, '#38bdf8');
            for (let b = 0; b < 8; b++) {
                setTimeout(() => {
                    if (this.boss && this.boss.alive) {
                        const bAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32)) + (Math.random() - 0.5) * 0.2;
                        this.projectiles.push({
                            x: this.boss.x + 32, y: this.boss.y + 32,
                            vx: Math.cos(bAng) * 5.4, vy: Math.sin(bAng) * 5.4,
                            angle: bAng, damage: 26, rangeLeft: 520,
                            type: 'ice_shard', fromBoss: true
                        });
                    }
                }, b * 75);
            }
        } else {
            // Move 5: Absolute Zero Cataclysm (Signature Calamity)
            SoundEngine.bossTelegraph();
            SoundEngine.bossShockwave();
            this.spawnBossShockwave(this.boss.x + 32, this.boss.y + 32);
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#e0f2fe', 25);
            this.addFloatingText('★ [ท่าไม้ตายบอส] มหาเหมันต์ศูนย์สัมบูรณ์!', this.boss.x - 35, this.boss.y - 25, '#7dd3fc');
            this.spawnBossTelegraph('ice_boulder', this.player.x + 12, this.player.y + 14, 36, 700, 60);
            this.spawnBossTelegraph('ice_boulder', this.player.x - 40, this.player.y - 30, 36, 900, 60);
            for (let i = 0; i < 18; i++) {
                const ang = (i / 18) * Math.PI * 2;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 5.0, vy: Math.sin(ang) * 5.0,
                    angle: ang, damage: 32, rangeLeft: 500,
                    type: 'ice_shard', fromBoss: true
                });
            }
        }
    }

    this.boss.summonCooldown -= dt;
    if (this.boss.summonCooldown <= 0) {
        this.boss.summonCooldown = p === 3 ? 8000 : 11000;
        SoundEngine.bossRoar();
        this.addFloatingText('★ ฟรอสต์แฟงก์กระทืบเท้า! หมาป่าเหมันต์คำราม!', this.boss.x + 10, this.boss.y - 15, '#38bdf8');
        this.worldMonsters.push({
            id: 'minion_' + performance.now(),
            type: 'frost_wolf',
            x: this.boss.x - 30, y: this.boss.y + 20,
            hp: 80, maxHp: 80, speed: 1.7, damage: 20,
            aggroRange: 340, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0
        });
    }
};


// 6. MALAKOR: Sovereign of the Nether Void (5 Distinct Attacks)
Game.updateMalakorBoss = function(dt, dist) {
    const p = this.boss.phase;
    const speed = p === 3 ? 2.3 : (p === 2 ? 1.8 : 1.35);

    if (dist > 85) {
        const ang = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32));
        this.boss.x += Math.cos(ang) * speed;
        this.boss.y += Math.sin(ang) * speed;
    }

    this.boss.attackCooldown -= dt;
    if (this.boss.attackCooldown <= 0) {
        this.boss.attackCooldown = p === 3 ? 480 : (p === 2 ? 850 : 1200);

        const step = (this.boss.comboStep || 0) % 5;
        this.boss.comboStep = step + 1;

        if (step === 0) {
            // Move 1: Cursed Tracking Soul Skulls
            SoundEngine.bossSoulScream();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#a855f7', 16);
            this.addFloatingText('★ [มาลาคอร์] หัวกะโหลกวิญญาณต้องสาป!', this.boss.x - 20, this.boss.y - 20, '#a855f7');
            [-0.35, 0, 0.35].forEach(off => {
                const bAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32)) + off;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(bAng) * 3.6, vy: Math.sin(bAng) * 3.6,
                    angle: bAng, damage: 32, rangeLeft: 560,
                    type: 'shadow_skull', fromBoss: true
                });
            });
        } else if (step === 1) {
            // Move 2: Crescent Void Scythe Slash
            SoundEngine.bossSoulScream();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#c084fc', 18);
            this.addFloatingText('★ [มาลาคอร์] เคียวทมิฬผ่าสุญญากาศ!', this.boss.x - 20, this.boss.y - 20, '#c084fc');
            [-0.25, 0.25].forEach(off => {
                const bAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32)) + off;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(bAng) * 5.4, vy: Math.sin(bAng) * 5.4,
                    angle: bAng, damage: 45, rangeLeft: 580,
                    type: 'void_scythe', fromBoss: true
                });
            });
        } else if (step === 2) {
            // Move 3: Gravitational Singularity (Black Hole)
            SoundEngine.bossTelegraph();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#581c87', 20);
            this.addFloatingText('★ [มาลาคอร์] หลุมดำดูดกลืนมิติ!', this.boss.x - 20, this.boss.y - 20, '#581c87');
            this.spawnBossTelegraph('void_singularity', this.player.x + 12, this.player.y + 14, 60, 1600, 58);
        } else if (step === 3) {
            // Move 4: Shadow Step Cleave
            SoundEngine.bossSoulScream();
            this.addFloatingText('★ [มาลาคอร์] วาร์ปสังหารพริบตา!', this.boss.x - 20, this.boss.y - 20, '#ef4444');
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#7c3aed', 20);
            this.boss.x = this.player.x - 20;
            this.boss.y = this.player.y - 20;
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#ef4444', 25);
            this.damagePlayer(45, this.boss);
        } else {
            // Move 5: Void Apotheosis Danmaku (Signature Calamity)
            SoundEngine.bossSoulScream();
            SoundEngine.bossShockwave();
            this.spawnBossShockwave(this.boss.x + 32, this.boss.y + 32);
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#a855f7', 26);
            this.addFloatingText('★ [ท่าไม้ตายบอส] มหาพายุดับสูญแห่งความมืด!', this.boss.x - 35, this.boss.y - 25, '#c084fc');
            this.boss.spiralAngle = (this.boss.spiralAngle || 0) + 0.5;
            for (let i = 0; i < 24; i++) {
                const ang = (i / 24) * Math.PI * 2 + this.boss.spiralAngle;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 5.0, vy: Math.sin(ang) * 5.0,
                    angle: ang, damage: 32, rangeLeft: 500,
                    type: 'shadow_skull', fromBoss: true
                });
            }
            [0, Math.PI / 2, Math.PI, Math.PI * 1.5].forEach(ang => {
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 5.5, vy: Math.sin(ang) * 5.5,
                    angle: ang, damage: 46, rangeLeft: 580,
                    type: 'void_scythe', fromBoss: true
                });
            });
        }
    }

    this.boss.summonCooldown -= dt;
    if (this.boss.summonCooldown <= 0) {
        this.boss.summonCooldown = p === 3 ? 7500 : 10000;
        SoundEngine.bossRoar();
        this.addFloatingText('★ มาลาคอร์เปิดประตูนรก! อสูรโครงกระดูกตื่นขึ้น!', this.boss.x + 10, this.boss.y - 15, '#a855f7');
        this.worldMonsters.push({
            id: 'minion_' + performance.now(),
            type: 'skeleton_warrior',
            x: this.boss.x - 30, y: this.boss.y + 20,
            hp: 90, maxHp: 90, speed: 1.6, damage: 22,
            aggroRange: 340, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0
        });
    }
};


// 7. SYLVANUS: Ancient Forest Sovereign (5 Distinct Attacks)
Game.updateSylvanusBoss = function(dt, dist) {
    const p = this.boss.phase;
    const speed = p === 3 ? 2.15 : (p === 2 ? 1.65 : 1.25);

    if (dist > 80) {
        const ang = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32));
        this.boss.x += Math.cos(ang) * speed;
        this.boss.y += Math.sin(ang) * speed;
    }

    this.boss.attackCooldown -= dt;
    if (this.boss.attackCooldown <= 0) {
        this.boss.attackCooldown = p === 3 ? 540 : (p === 2 ? 900 : 1250);

        const step = (this.boss.comboStep || 0) % 5;
        this.boss.comboStep = step + 1;

        if (step === 0) {
            // Move 1: Floral Blossom Blade Ring
            SoundEngine.bossNatureBloom();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#ec4899', 16);
            this.addFloatingText('★ [ซิลวานัส] พายุดอกไม้คมกริบ!', this.boss.x - 20, this.boss.y - 20, '#ec4899');
            const count = p === 3 ? 16 : 12;
            for (let i = 0; i < count; i++) {
                const ang = (i / count) * Math.PI * 2;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 4.6, vy: Math.sin(ang) * 4.6,
                    angle: ang, damage: 30, rangeLeft: 480,
                    type: 'petal_blade', fromBoss: true
                });
            }
        } else if (step === 1) {
            // Move 2: Entangling Root Trap (Roll Catch)
            SoundEngine.bossTelegraph();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#22c55e', 14);
            this.addFloatingText('★ [ซิลวานัส] คุกรากไม้พันธนาการ!', this.boss.x - 20, this.boss.y - 20, '#22c55e');
            this.spawnBossTelegraph('thorn_trap', this.player.x + 12, this.player.y + 14, 30, 700, 36);
            this.spawnBossTelegraph('thorn_trap', this.player.x - 30, this.player.y - 20, 28, 700, 32);
        } else if (step === 2) {
            // Move 3: Canopy Petal Wall Sweep
            SoundEngine.bossNatureBloom();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#f472b6', 16);
            this.addFloatingText('★ [ซิลวานัส] กำแพงพฤกษาพัดคลื่น!', this.boss.x - 20, this.boss.y - 20, '#f472b6');
            for (let i = 0; i < 16; i++) {
                const ang = (i / 16) * Math.PI * 2;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 4.8, vy: Math.sin(ang) * 4.8,
                    angle: ang, damage: 32, rangeLeft: 500,
                    type: 'petal_blade', fromBoss: true
                });
            }
        } else if (step === 3) {
            // Move 4: Solar Cannon Cross
            SoundEngine.bossLaserSweep();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#facc15', 18);
            this.addFloatingText('★ [ซิลวานัส] ปืนใหญ่แสงอาทิตย์สี่ทิศ!', this.boss.x - 20, this.boss.y - 20, '#facc15');
            this.boss.solarAngle = (this.boss.solarAngle || 0) + 0.4;
            [0, Math.PI / 2, Math.PI, Math.PI * 1.5].forEach(ang => {
                const curAng = ang + this.boss.solarAngle;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(curAng) * 6.4, vy: Math.sin(curAng) * 6.4,
                    angle: curAng, damage: 42, rangeLeft: 580,
                    type: 'solar_beam', fromBoss: true
                });
            });
        } else {
            // Move 5: Wrath of the World Tree (Signature Calamity)
            SoundEngine.bossLaserSweep();
            SoundEngine.bossNatureBloom();
            SoundEngine.bossShockwave();
            this.spawnBossShockwave(this.boss.x + 32, this.boss.y + 32);
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#22c55e', 25);
            this.addFloatingText('★ [ท่าไม้ตายบอส] พิโรธพฤกษาบรรพกาลล้างโลก!', this.boss.x - 35, this.boss.y - 25, '#22c55e');
            for (let i = 0; i < 8; i++) {
                const ang = (i / 8) * Math.PI * 2;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 6.4, vy: Math.sin(ang) * 6.4,
                    angle: ang, damage: 46, rangeLeft: 600,
                    type: 'solar_beam', fromBoss: true
                });
            }
            for (let i = 0; i < 16; i++) {
                const ang = (i / 16) * Math.PI * 2 + (Math.PI / 16);
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 5.0, vy: Math.sin(ang) * 5.0,
                    angle: ang, damage: 32, rangeLeft: 520,
                    type: 'petal_blade', fromBoss: true
                });
            }
            this.spawnBossTelegraph('thorn_trap', this.player.x + 12, this.player.y + 14, 30, 650, 36);
        }
    }

    this.boss.summonCooldown -= dt;
    if (this.boss.summonCooldown <= 0) {
        this.boss.summonCooldown = p === 3 ? 8000 : 11000;
        SoundEngine.bossRoar();
        this.addFloatingText('★ ซิลวาเนียปลุกชีพพฤกษา! อสูรแมงมุมพฤกษาตื่นขึ้น!', this.boss.x + 10, this.boss.y - 15, '#22c55e');
        this.worldMonsters.push({
            id: 'minion_' + performance.now(),
            type: 'cave_spider',
            x: this.boss.x - 30, y: this.boss.y + 20,
            hp: 75, maxHp: 75, speed: 1.7, damage: 18,
            aggroRange: 340, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0
        });
    }
};


// 8. ASTREON: Sovereign of the Tempest (5 Distinct Attacks - 10/10 Nightmare)
Game.updateAstreonBoss = function(dt, dist) {
    const p = this.boss.phase;
    const speed = p === 3 ? 3.5 : (p === 2 ? 3.0 : 2.5);

    this.boss.blitzTimer = (this.boss.blitzTimer || 0) + dt * 0.01;
    if (dist > 75) {
        const baseAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32));
        const zigzag = Math.sin(this.boss.blitzTimer * 2.8) * 0.6;
        const ang = baseAng + zigzag;
        this.boss.x += Math.cos(ang) * speed;
        this.boss.y += Math.sin(ang) * speed;
    }

    this.boss.attackCooldown -= dt;
    if (this.boss.attackCooldown <= 0) {
        this.boss.attackCooldown = p === 3 ? 380 : (p === 2 ? 650 : 950);

        const step = (this.boss.comboStep || 0) % 5;
        this.boss.comboStep = step + 1;

        if (step === 0) {
            // Move 1: Lightning Arc Wave
            SoundEngine.thunder();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#38bdf8', 16);
            this.addFloatingText('★ [ออสทริออน] คลื่นอัสนีบาตแปดทิศ!', this.boss.x - 20, this.boss.y - 20, '#38bdf8');
            const count = p === 3 ? 16 : 10;
            for (let i = 0; i < count; i++) {
                const ang = (i / count) * Math.PI * 2;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 6.4, vy: Math.sin(ang) * 6.4,
                    angle: ang, damage: 32, rangeLeft: 520,
                    type: 'lightning_arc', fromBoss: true
                });
            }
        } else if (step === 1) {
            // Move 2: Thunder God's Snipe
            SoundEngine.bossLightningStrike();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#fde047', 16);
            this.addFloatingText('★ [ออสทริออน] หอกสายฟ้าเทวะสไนป์!', this.boss.x - 20, this.boss.y - 20, '#fde047');
            this.spawnBossTelegraph('lightning', this.player.x + 12, this.player.y + 14, 34, 450, 65);
            if (p >= 2) {
                setTimeout(() => {
                    if (this.boss && this.boss.alive) {
                        this.spawnBossTelegraph('lightning', this.player.x + 12 + (Math.random() - 0.5) * 30, this.player.y + 14 + (Math.random() - 0.5) * 30, 32, 450, 55);
                    }
                }, 140);
            }
        } else if (step === 2) {
            // Move 3: Conductive Web Grid
            SoundEngine.bossLaserSweep();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#38bdf8', 18);
            this.addFloatingText('★ [ออสทริออน] ตาข่ายเลเซอร์สายฟ้า!', this.boss.x - 20, this.boss.y - 20, '#38bdf8');
            this.boss.lightningAngle = (this.boss.lightningAngle || 0) + 0.45;
            [0, Math.PI / 2, Math.PI, Math.PI * 1.5].forEach(ang => {
                const curAng = ang + this.boss.lightningAngle;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(curAng) * 7.2, vy: Math.sin(curAng) * 7.2,
                    angle: curAng, damage: 48, rangeLeft: 600,
                    type: 'lightning_beam', fromBoss: true
                });
            });
        } else if (step === 3) {
            // Move 4: Supersonic Lightning Blitz (Gap Closer)
            SoundEngine.bossTelegraph();
            this.addFloatingText('★ [ออสทริออน] สายฟ้าฟาดความเร็วเสียง!', this.boss.x - 20, this.boss.y - 20, '#fde047');
            this.spawnBossTelegraph('dash', this.boss.x + 32, this.boss.y + 32, 280, 360, 52, this.player.x + 12, this.player.y + 14);
        } else {
            // Move 5: Cataclysmic Storm Supernova (Signature Calamity)
            SoundEngine.bossLightningStrike();
            SoundEngine.bossShockwave();
            this.spawnBossShockwave(this.boss.x + 32, this.boss.y + 32);
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#38bdf8', 30);
            this.addFloatingText('★ [ท่าไม้ตายบอส] มหาพายุทัณฑ์เทวาดับดารา!', this.boss.x - 35, this.boss.y - 25, '#fde047');
            for (let s = 0; s < 4; s++) {
                setTimeout(() => {
                    if (this.boss && this.boss.alive) {
                        this.spawnBossTelegraph('lightning', this.player.x + 12 + (Math.random() - 0.5) * 40, this.player.y + 14 + (Math.random() - 0.5) * 40, 34, 420, 58);
                    }
                }, s * 130);
            }
            this.boss.spiralAngle = (this.boss.spiralAngle || 0) + 0.6;
            for (let i = 0; i < 24; i++) {
                const ang = (i / 24) * Math.PI * 2 + this.boss.spiralAngle;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 6.5, vy: Math.sin(ang) * 6.5,
                    angle: ang, damage: 36, rangeLeft: 540,
                    type: 'lightning_arc', fromBoss: true
                });
            }
        }
    }

    this.boss.summonCooldown -= dt;
    if (this.boss.summonCooldown <= 0) {
        this.boss.summonCooldown = p === 3 ? 7000 : 9000;
        SoundEngine.bossRoar();
        this.addFloatingText('★ ออสทริออนคำรามกึกก้อง! ค้างคาวสายฟ้าผ่าลงมา!', this.boss.x + 10, this.boss.y - 15, '#38bdf8');
        this.worldMonsters.push({
            id: 'minion_' + performance.now(),
            type: 'cave_bat',
            x: this.boss.x - 30, y: this.boss.y + 20,
            hp: 65, maxHp: 65, speed: 2.1, damage: 18,
            aggroRange: 360, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0
        });
    }
};

// 9. KARZARAK: Ancient Magma Wyrm Boss (Island Volcano Caldera Summit)
Game.updateKarzarakBoss = function(dt: number, dist: number) {
    const p = this.boss.phase;
    const speed = p === 3 ? 2.6 : (p === 2 ? 1.9 : 1.3);

    // Serpentine pursuit towards player
    if (dist > 75) {
        const ang = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32));
        this.boss.x += Math.cos(ang) * speed;
        this.boss.y += Math.sin(ang) * speed;
    }

    this.boss.attackCooldown -= dt;
    if (this.boss.attackCooldown <= 0) {
        this.boss.attackCooldown = p === 3 ? 650 : (p === 2 ? 950 : 1350);

        const step = (this.boss.comboStep || 0) % 4;
        this.boss.comboStep = step + 1;

        if (step === 0) {
            // Move 1: Triple Magma Blast
            SoundEngine.bossDragonBreath();
            this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#ea580c', 16);
            this.addFloatingText('[คาร์ซาร็อค] พ่นคลื่นลูกไฟลาวาหลอมเหลว!', this.boss.x - 20, this.boss.y - 20, '#f97316');
            const bAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32));
            const spreads = p >= 2 ? [-0.35, -0.18, 0, 0.18, 0.35] : [-0.25, 0, 0.25];
            spreads.forEach((off: number) => {
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(bAng + off) * 6.2, vy: Math.sin(bAng + off) * 6.2,
                    angle: bAng + off, damage: 36, rangeLeft: 520,
                    type: 'dragon_fire', fromBoss: true
                });
            });
            // Spawn fire patch at boss feet
            this.spawnBossGroundHazard(this.boss.x + 32, this.boss.y + 40, 'fire_patch', 4000, 14);
        } else if (step === 1) {
            // Move 2: Magma Wyrm Eruption Shockwave
            SoundEngine.bossShockwave();
            this.spawnBossShockwave(this.boss.x + 32, this.boss.y + 32);
            this.triggerScreenShake(5.0, 180);
            this.addFloatingText('[คาร์ซาร็อค] กระแทกคลื่นหินหนืดสะเทือนปฐพี!', this.boss.x - 20, this.boss.y - 20, '#ef4444');
            const ringCount = p === 3 ? 12 : 8;
            for (let i = 0; i < ringCount; i++) {
                const ang = (i / ringCount) * Math.PI * 2;
                this.projectiles.push({
                    x: this.boss.x + 32, y: this.boss.y + 32,
                    vx: Math.cos(ang) * 4.8, vy: Math.sin(ang) * 4.8,
                    angle: ang, damage: 32, rangeLeft: 460,
                    type: 'crystal_shard', fromBoss: true
                });
            }
        } else if (step === 2) {
            // Move 3: Volcanic Meteor Shower (Caldera Bombardment)
            SoundEngine.bossMeteor();
            this.addFloatingText('[คาร์ซาร็อค] ฝนอุกกาบาตภูเขาไฟถล่ม!', this.boss.x - 20, this.boss.y - 20, '#facc15');
            const count = p === 3 ? 6 : 4;
            for (let m = 0; m < count; m++) {
                setTimeout(() => {
                    if (this.boss && this.boss.alive) {
                        const targetX = this.player.x + 12 + (Math.random() - 0.5) * 120;
                        const targetY = this.player.y + 14 + (Math.random() - 0.5) * 120;
                        this.spawnBossTelegraph('meteor', targetX, targetY, 36, 600 + m * 100, 48);
                    }
                }, m * 150);
            }
        } else if (step === 3) {
            // Move 4: Breaching Dash Strike
            SoundEngine.bossDash();
            this.addFloatingText('[คาร์ซาร็อค] พุ่งทะลวงผ่านธารลาวา!', this.boss.x - 20, this.boss.y - 20, '#ea580c');
            this.spawnBossTelegraph('dash', this.player.x + 12, this.player.y + 14, 44, 450, 52);
        }
    }

    // Minion Spawn (Magma Sprites)
    this.boss.summonCooldown = (this.boss.summonCooldown || 8000) - dt;
    if (this.boss.summonCooldown <= 0) {
        this.boss.summonCooldown = p === 3 ? 6500 : 9500;
        SoundEngine.bossRoar();
        this.addFloatingText('[คาร์ซาร็อค] ปลุกภูตลูกไฟลาวาขึ้นมาจากหินหนืด!', this.boss.x - 20, this.boss.y - 20, '#ea580c');
        this.worldMonsters.push({
            id: 'minion_magma_' + performance.now(),
            type: 'magma_sprite',
            name: 'ภูตลูกไฟลาวา (Magma Sprite)',
            x: this.boss.x + (Math.random() - 0.5) * 80,
            y: this.boss.y + 40,
            hp: 85, maxHp: 85, speed: 1.8, damage: 18,
            alive: true, flashTimer: 0, frame: 0, animTimer: 0,
            gold: 25, xp: 30,
            drops: [{ item: 'cinder_shard', chance: 0.8 }]
        });
    }
};

Game.damageBoss = function(amount: number) {
    if (!this.boss || !this.boss.alive) return;
    this.boss.hp -= amount;
    this.boss.flashTimer = Math.max(this.boss.flashTimer || 0, 200);
    const bossHpFill = document.getElementById('bossHpFill');
    if (bossHpFill && this.boss.maxHp) {
        const hpPct = Math.max(0, (this.boss.hp / this.boss.maxHp) * 100);
        bossHpFill.style.width = hpPct + '%';
    }
    if (this.boss.hp <= 0) {
        this.defeatBoss();
    }
};

Game.defeatBoss = function() {
    this.boss.alive = false;
    const bossBar = document.getElementById('bossHealthBar');
    if (bossBar) bossBar.style.display = 'none';
    if (typeof SoundEngine.setBossBattle === 'function') SoundEngine.setBossBattle(false);

    SoundEngine.bossVictoryFanfare();
    SoundEngine.bossRoar();
    this.triggerScreenShake(9.0, 450);

    // Staggered multi-stage explosions
    for (let s = 0; s < 5; s++) {
        setTimeout(() => {
            if (this.boss) {
                const rx = this.boss.x + 10 + Math.random() * 44;
                const ry = this.boss.y + 10 + Math.random() * 44;
                this.spawnParticles(rx, ry, '#ef4444', 20);
                this.spawnParticles(rx, ry, '#facc15', 20);
                this.spawnParticles(rx, ry, '#c084fc', 15);
                SoundEngine.thunder();
            }
        }, s * 220);
    }

    if (!this.player.defeatedBosses) this.player.defeatedBosses = {};
    if (!this.player.bossDefeatDay) this.player.bossDefeatDay = {};

    this.player.defeatedBosses[this.boss.id] = true;
    this.player.bossDefeatDay[this.boss.id] = this.time.day;

    const registry = (window as any).BOSS_REGISTRY || {};

    const bData = registry[this.boss.id] || BOSS_KATHUROS;
    const gReward = bData.gold || 1500;
    const xReward = bData.xp || 800;

    this.player.gold += gReward;
    this.addXp(xReward);

    if (this.boss.id === 'boss_luminarch') {
        this.spawnDroppedItem('luminarch_crystal_heart', 1, this.boss.x + 32, this.boss.y + 32);
        this.spawnDroppedItem('sacred_shard_sun', 1, this.boss.x + 32, this.boss.y + 16);
        this.spawnDroppedItem('diamond_crystal', 2, this.boss.x + 20, this.boss.y + 32);
        this.spawnDroppedItem('gold_ore', 5, this.boss.x + 44, this.boss.y + 32);
        this.player.questProgress.luminarchDefeated = true;
        if (!this.player.sacredShards) this.player.sacredShards = {};
        this.player.sacredShards['sacred_shard_sun'] = true;
    } else if (this.boss.id === 'boss_hydrakis') {
        this.spawnDroppedItem('hydra_venom_gland', 1, this.boss.x + 32, this.boss.y + 32);
        this.spawnDroppedItem('sacred_shard_water', 1, this.boss.x + 32, this.boss.y + 16);
        this.spawnDroppedItem('hydra_scale', 4, this.boss.x + 20, this.boss.y + 32);
        this.spawnDroppedItem('swamp_herb', 5, this.boss.x + 44, this.boss.y + 32);
        this.player.questProgress.hydrakisDefeated = true;
        if (!this.player.sacredShards) this.player.sacredShards = {};
        this.player.sacredShards['sacred_shard_water'] = true;
    } else if (this.boss.id === 'boss_ignistron') {
        this.spawnDroppedItem('magma_dragon_horn', 1, this.boss.x + 32, this.boss.y + 32);
        this.spawnDroppedItem('sacred_shard_fire', 1, this.boss.x + 32, this.boss.y + 16);
        this.spawnDroppedItem('flame_heart', 2, this.boss.x + 20, this.boss.y + 32);
        this.spawnDroppedItem('ruby_gem', 5, this.boss.x + 44, this.boss.y + 32);
        this.player.questProgress.ignistronDefeated = true;
        if (!this.player.sacredShards) this.player.sacredShards = {};
        this.player.sacredShards['sacred_shard_fire'] = true;
    } else if (this.boss.id === 'boss_frostfang') {
        this.spawnDroppedItem('glacial_titan_core', 1, this.boss.x + 32, this.boss.y + 32);
        this.spawnDroppedItem('sacred_shard_frost', 1, this.boss.x + 32, this.boss.y + 16);
        this.spawnDroppedItem('frost_crystal', 4, this.boss.x + 20, this.boss.y + 32);
        this.spawnDroppedItem('diamond_crystal', 2, this.boss.x + 44, this.boss.y + 32);
        this.player.questProgress.frostfangDefeated = true;
        if (!this.player.sacredShards) this.player.sacredShards = {};
        this.player.sacredShards['sacred_shard_frost'] = true;
    } else if (this.boss.id === 'boss_malakor') {
        this.spawnDroppedItem('death_lord_soul', 1, this.boss.x + 32, this.boss.y + 32);
        this.spawnDroppedItem('sacred_shard_shadow', 1, this.boss.x + 32, this.boss.y + 16);
        this.spawnDroppedItem('cursed_relic', 3, this.boss.x + 20, this.boss.y + 32);
        this.spawnDroppedItem('crown_of_despair', 1, this.boss.x + 44, this.boss.y + 32);
        this.player.questProgress.malakorDefeated = true;
        if (!this.player.sacredShards) this.player.sacredShards = {};
        this.player.sacredShards['sacred_shard_shadow'] = true;
        this.addFloatingText('★ พิชิตมหาบอสผู้บงการสำเร็จ! รายงานนายกฯ กิลเบิร์ตเพื่อรับตำแหน่งมหาผู้พิทักษ์!', this.player.x - 40, this.player.y - 50, '#fde047');
    } else if (this.boss.id === 'boss_sylvanus') {
        this.spawnDroppedItem('ancient_tree_heart', 1, this.boss.x + 32, this.boss.y + 32);
        this.spawnDroppedItem('sacred_shard_nature', 1, this.boss.x + 32, this.boss.y + 16);
        this.spawnDroppedItem('star_fruit', 4, this.boss.x + 20, this.boss.y + 32);
        this.spawnDroppedItem('wood', 12, this.boss.x + 44, this.boss.y + 32);
        this.player.questProgress.sylvanusDefeated = true;
        if (!this.player.sacredShards) this.player.sacredShards = {};
        this.player.sacredShards['sacred_shard_nature'] = true;
        this.addFloatingText('★ กำราบเทพพฤกษาบรรพกาล ซิลวาเนีย! ได้รับศิลาพฤกษาศักดิ์สิทธิ์!', this.player.x - 40, this.player.y - 50, '#4ade80');
    } else if (this.boss.id === 'boss_astreon') {
        this.spawnDroppedItem('storm_core', 1, this.boss.x + 32, this.boss.y + 32);
        this.spawnDroppedItem('sacred_shard_thunder', 1, this.boss.x + 32, this.boss.y + 16);
        this.spawnDroppedItem('thunder_crystal', 5, this.boss.x + 20, this.boss.y + 32);
        this.spawnDroppedItem('gold_ore', 6, this.boss.x + 44, this.boss.y + 32);
        this.player.questProgress.astreonDefeated = true;
        if (!this.player.sacredShards) this.player.sacredShards = {};
        this.player.sacredShards['sacred_shard_thunder'] = true;
        this.addFloatingText('★ สยบจ้าวแห่งพายุสายฟ้า ออสทริออน! ได้รับศิลาสายฟ้าบรรพกาล!', this.player.x - 40, this.player.y - 50, '#38bdf8');
    } else if (this.boss.id === 'boss_karzarak') {
        this.spawnDroppedItem('magma_wyrm_scale', 3, this.boss.x + 32, this.boss.y + 32);
        this.spawnDroppedItem('volcano_flame_sword', 1, this.boss.x + 32, this.boss.y + 16);
        this.spawnDroppedItem('ring_of_fire_walker', 1, this.boss.x + 16, this.boss.y + 32);
        this.spawnDroppedItem('cinder_shard', 20, this.boss.x + 48, this.boss.y + 32);
        this.spawnDroppedItem('pirate_doubloon', 15, this.boss.x + 32, this.boss.y + 48);
        if (!this.player.questProgress) this.player.questProgress = {};
        this.player.questProgress.karzarakDefeated = true;
        this.addFloatingText('[พิชิตมังกรลาวายักษ์ คาร์ซาร็อค สำเร็จ!] แท่นหลอมภูเขาไฟโบราณตื่นขึ้นแล้ว!', this.player.x - 50, this.player.y - 50, '#facc15');

        // Unlock Volcano Forge at (18, 6) & Exit portal at (18, 24) on Floor 10
        if (this.currentScene === 'island_volcano') {
            if (this.map[6] && this.map[6][18]) {
                this.map[6][18].type = 'volcanoForge';
                this.map[6][18].solid = true;
                this.map[6][18].interactable = 'volcano_magma_forge';
            }
            if (this.map[24] && this.map[24][18]) {
                this.map[24][18].type = 'spire_portal';
                this.map[24][18].solid = false;
                this.map[24][18].interactable = 'exit_volcano_to_island';
            }
        }
    } else {
        // boss_kathuros
        this.spawnDroppedItem('demon_heart', 1, this.boss.x + 32, this.boss.y + 32);
        this.spawnDroppedItem('sacred_shard_earth', 1, this.boss.x + 32, this.boss.y + 16);
        this.spawnDroppedItem('crown_of_despair', 1, this.boss.x + 20, this.boss.y + 32);
        this.spawnDroppedItem('ruby_gem', 3, this.boss.x + 44, this.boss.y + 32);
        this.player.questProgress.kathurosDefeated = true;
        this.player.questProgress.bossDefeated = true;
        if (!this.player.sacredShards) this.player.sacredShards = {};
        this.player.sacredShards['sacred_shard_earth'] = true;
    }

    this.addFloatingText(`★ กำราบ ${this.boss.name}! ชัยชนะอันยิ่งใหญ่! (+${gReward} G, +${xReward} XP)`, this.boss.x - 40, this.boss.y - 30, '#facc15');
    this.updateHUD();
};


Game.startDialogue = function(npcId) {
    const npcCfg = NPC_STORY[npcId];
    if (!npcCfg) return;

    this.activeDialogue = npcId;
    const box = document.getElementById('storyDialogueBox');
    if (!box) return;
    box.style.display = 'flex';

    document.getElementById('dialogueSpeakerName').textContent = npcCfg.name;
    document.getElementById('dialogueSpeakerRole').textContent = npcCfg.role;

    // Render Friendship Hearts (0-5 hearts, each 20 points)
    const heartsEl = document.getElementById('dialogueFriendshipHearts');
    if (heartsEl) {
        heartsEl.innerHTML = '';
        if (!this.player.npcFriendship) this.player.npcFriendship = {};

        const score = this.player.npcFriendship[npcId] || 0;
        const hearts = Math.min(5, Math.floor(score / 20));
        for (let i = 1; i <= 5; i++) {
            const hSpan = document.createElement('span');
            hSpan.className = i <= hearts ? 'heart-filled' : 'heart-empty';
            hSpan.textContent = '♥';
            heartsEl.appendChild(hSpan);
        }
    }

    // Draw Portrait
    const cvs = document.getElementById('dialoguePortraitCanvas') as HTMLCanvasElement | null;
    if (cvs) {
        const ctx = cvs.getContext('2d');
        if (ctx) {
            ctx.imageSmoothingEnabled = false;
            ctx.clearRect(0, 0, 48, 48);
            const pType = npcCfg.portraitType || npcCfg.portrait || npcId;
            const pSpr = SPRITES.portraits[pType];
            if (pSpr) ctx.drawImage(pSpr, 0, 0);
        }
    }

    const textEl = document.getElementById('dialogueText');
    const actionsEl = document.getElementById('dialogueActionButtons');
    actionsEl.innerHTML = '';

    const dlgs = npcCfg.dialogues || npcCfg.dialogue || {};


    if (npcId === 'gilbert') {
        const q1State = this.player.quests.q1;
        const q4State = this.player.quests.q4;
        const q5State = this.player.quests.q5;

        if (!q1State || q1State === 'not_started') {
            textEl.textContent = dlgs.intro || 'ยินดีต้อนรับท่านชาวสวนผู้กล้าหาญ! เกิดโรคระบาดสปอร์สีแดงทำให้แมลงกลายร่างเป็นอสูรยักษ์!';
            const acceptBtn = document.createElement('button');
            acceptBtn.className = 'btn-dialogue-action btn-quest-accept';
            acceptBtn.textContent = 'รับภารกิจบทที่ 1: วิบัติสปอร์กลายพันธุ์';
            acceptBtn.onclick = () => {
                this.player.quests.q1 = 'active';
                SoundEngine.levelUp();
                this.addFloatingText('รับภารกิจบทที่ 1: วิบัติสปอร์กลายพันธุ์', this.player.x, this.player.y - 20, '#fde047');
                this.closeDialogue();
                this.updateHUD();
            };

            actionsEl.appendChild(acceptBtn);
        } else if (q1State === 'active') {
            const bugsKilled = this.player.questProgress.bugsDefeated || 0;
            const spores = this.countItemInInventory('blight_spore');
            if (bugsKilled >= 3 && spores >= 2) {
                textEl.textContent = dlgs.q1_reward || 'เจ้าทำได้จริงๆ! สปอร์พวกนี้คือหลักฐานสำคัญ รีบนำไปให้ หมอยาลิเลียน ที่คลินิกวิจัยทันที!';
                const turnInBtn = document.createElement('button');
                turnInBtn.className = 'btn-dialogue-action btn-quest-accept';
                turnInBtn.textContent = 'ส่งภารกิจบทที่ 1 (รับ 200 G + ยาฟื้นพลัง x3 + 100 XP)';
                turnInBtn.onclick = () => {
                    this.removeItemFromInventory('blight_spore', 2);
                    this.player.quests.q1 = 'completed';
                    this.player.quests.q2 = 'active'; // Progress to Chapter 2
                    this.player.gold += 200;
                    this.addXp(100);
                    this.addItemToInventory('health_potion', 3, 'ยาฟื้นพลังชีวิตชั้นเลิศ');
                    SoundEngine.levelUp();
                    this.addFloatingText('สำเร็จบทที่ 1! ปลดล็อกบทที่ 2 ที่คลินิกหมอยาลิเลียน', this.player.x, this.player.y - 25, '#4ade80');
                    this.closeDialogue();
                    this.updateHUD();
                };

                actionsEl.appendChild(turnInBtn);
            } else {
                textEl.textContent = `สถานการณ์รอบฟาร์มยังอันตราย! เจ้ากำจัดแมลงยักษ์ไปแล้ว ${bugsKilled}/3 ตัว และเก็บสปอร์กลายพันธุ์ได้ ${spores}/2 ชิ้น จงรีบไปรวบรวมมานะ!`;
            }
        } else if (q4State === 'completed' && (!q5State || q5State === 'not_started')) {
            textEl.textContent = dlgs.q5_intro || 'ท่านผู้กล้า... บัดนี้ถึงเวลาเผชิญหน้ากับต้นตอที่แท้จริง "ราชินีสปอร์ปีศาจ คาธูรอส" ณ วิหารโบราณทางเหนือสุด!';
            const acceptQ5Btn = document.createElement('button');
            acceptQ5Btn.className = 'btn-dialogue-action btn-quest-accept';
            acceptQ5Btn.textContent = 'รับมหาภารกิจบทที่ 5: ชำระล้างราชินีสปอร์ปีศาจ';
            acceptQ5Btn.onclick = () => {
                this.player.quests.q5 = 'active';
                SoundEngine.bossRoar();
                this.addFloatingText('รับมหาภารกิจบทที่ 5: ชำระล้างราชินีสปอร์ปีศาจ!', this.player.x, this.player.y - 20, '#ef4444');
                this.closeDialogue();
                this.updateHUD();
            };

            actionsEl.appendChild(acceptQ5Btn);
        } else if (q5State === 'active') {
            if (this.player.questProgress.kathurosDefeated) {
                textEl.textContent = dlgs.victory || 'มหาศึกสิ้นสุดลงแล้ว! สปอร์สีเลือดสลายไป ท้องฟ้ากลับมาสดใสอีกครั้ง ขอยกย่องท่านเป็น "ยอดวีรบุรุษนักสวนผู้กอบกู้แผ่นดิน"!';
                const turnInQ5Btn = document.createElement('button');
                turnInQ5Btn.className = 'btn-dialogue-action btn-quest-accept';
                turnInQ5Btn.textContent = 'ส่งมอบมหาภารกิจบทที่ 5 (รับ 2,500 G + ดาบศักดิ์สิทธิ์เอ็กซ์คาลิเบอร์ + 1,200 XP)';
                turnInQ5Btn.onclick = () => {
                    this.player.quests.q5 = 'completed';
                    this.player.gold += 2500;
                    this.addXp(1200);
                    this.addItemToInventory('excalibur_sword', 1, 'ดาบศักดิ์สิทธิ์เอ็กซ์คาลิเบอร์ (Holy Excalibur)');
                    SoundEngine.levelUp();
                    this.addFloatingText('ชัยชนะอันยิ่งใหญ่! ปราบราชินีสปอร์ปีศาจสำเร็จ! (+2,500 G, +1,200 XP)', this.player.x, this.player.y - 30, '#facc15');
                    this.closeDialogue();
                    this.updateHUD();
                };

                actionsEl.appendChild(turnInQ5Btn);
            } else {
                textEl.textContent = 'จงมุ่งหน้าข้ามสะพานเหนือไปยังวิหารโบราณ ลานบูชาทางเหนือสุดคือที่สิงสถิตของ คาธูรอส จงใช้เซรุ่มและอาวุธทั้งหมดสยบมันให้ได้!';
            }
        } else if (this.player.quests.q9 === 'completed' && (!this.player.quests.q10 || this.player.quests.q10 === 'not_started')) {
            textEl.textContent = dlgs.q10_intro || 'ท่านผู้กล้า! เอลดรินได้ยืนยันแล้ว... จอมบงการผู้อยู่เบื้องหลังหายนะทั้งหมดคือ "ลอร์ดมรณะกระดูกอสูร มาลาคอร์" แห่งสุสานใต้พิภพต้องสาป!';
            const acceptQ10Btn = document.createElement('button');
            acceptQ10Btn.className = 'btn-dialogue-action btn-quest-accept';
            acceptQ10Btn.textContent = 'รับมหาศึกอวสานบทที่ 10: บัญชามรณะแห่งลอร์ดมาลาคอร์';
            acceptQ10Btn.onclick = () => {
                this.player.quests.q10 = 'active';
                SoundEngine.bossRoar();
                this.addFloatingText('รับมหาศึกอวสานบทที่ 10: บัญชามรณะแห่งลอร์ดมาลาคอร์!', this.player.x, this.player.y - 20, '#a855f7');
                this.closeDialogue();
                this.updateHUD();
            };
            actionsEl.appendChild(acceptQ10Btn);
        } else if (this.player.quests.q10 === 'active') {
            if (this.player.questProgress.malakorDefeated) {
                textEl.textContent = dlgs.grand_finale_victory || 'ปาฏิหาริย์เกิดขึ้นแล้ว! มาลาคอร์ถูกปราบ และมหาบอสทั้ง 6 ทั่วทุกแดนถูกสยบลงด้วยมือของท่าน! ขอสรรเสริญ "มหาผู้พิทักษ์แห่งจักรวาลและแผ่นดินสุขาวดี"!';
                const turnInQ10Btn = document.createElement('button');
                turnInQ10Btn.className = 'btn-dialogue-action btn-quest-accept';
                turnInQ10Btn.textContent = 'ส่งมอบมหาศึกอวสานบทที่ 10 (รับ 10,000 G + เคียวมรณะสูบวิญญาณ + 5,000 XP)';
                turnInQ10Btn.onclick = () => {
                    this.player.quests.q10 = 'completed';
                    this.player.gold += 10000;
                    this.addXp(5000);
                    this.addItemToInventory('malakor_soul_scythe', 1, 'เคียวมรณะสูบวิญญาณลอร์ดมาลาคอร์ (Malakor Soul Scythe)');
                    SoundEngine.bossVictoryFanfare();
                    this.triggerScreenShake(8.0, 400);
                    this.addFloatingText('ชัยชนะอันเป็นอมตะ! กอบกู้แผ่นดินครบ 10 บท! (+10,000 G, +5,000 XP)', this.player.x, this.player.y - 30, '#facc15');
                    this.closeDialogue();
                    this.updateHUD();
                };
                actionsEl.appendChild(turnInQ10Btn);
            } else {
                textEl.textContent = dlgs.q10_progress || 'จงบุกสุสานใต้พิภพต้องสาป (The Nether Crypt) ทางตะวันออกเฉียงใต้ สยบลอร์ดมาลาคอร์เพื่อยุติคำสาปสปอร์มรณะชั่วนิรันดร์!';
            }
        } else if (this.player.quests.q10 === 'completed') {
            textEl.textContent = 'มหาผู้พิทักษ์แห่งจักรวาล! แผ่นดินศิลาสุขาวดีรุ่งโรจน์และสงบสุขชั่วนิรันดร์ด้วยวีรกรรมอันยิ่งใหญ่ของท่าน!';
        } else {
            textEl.textContent = 'ขอขอบคุณท่านผู้กอบกู้แผ่นดิน! หากต้องการไขความลับเพิ่มเติม จงไปปรึกษาผู้เฒ่าปราชญ์เอลดรินที่วิหารศักดิ์สิทธิ์เถิด!';
        }
    } else if (npcId === 'lilian') {
        const q1State = this.player.quests.q1;
        const q2State = this.player.quests.q2;

        if (!q2State || q2State === 'not_started') {
            textEl.textContent = dlgs.intro || 'สวัสดีจ้ะ! ข้าคือลิเลียน ดูแลคลินิกปรุงยา... ละอองสปอร์สีแดงนี้มีความเข้มข้นของพิษสูงมาก ข้าต้องการสปอร์ 3 ชิ้น และสมุนไพรดวงดาว 2 ดอก เพื่อสกัดเซรุ่มต้านพิษ!';
            if (q1State === 'completed') {
                const acceptQ2Btn = document.createElement('button');
                acceptQ2Btn.className = 'btn-dialogue-action btn-quest-accept';
                acceptQ2Btn.textContent = 'รับภารกิจบทที่ 2: วิจัยเซรุ่มต้านพิษ';
                acceptQ2Btn.onclick = () => {
                    this.player.quests.q2 = 'active';
                    SoundEngine.levelUp();
                    this.addFloatingText('รับภารกิจบทที่ 2: วิจัยเซรุ่มต้านพิษ', this.player.x, this.player.y - 20, '#fde047');
                    this.closeDialogue();
                    this.updateHUD();
                };

                actionsEl.appendChild(acceptQ2Btn);
            } else {
                textEl.textContent += ' (กรุณาไปพบนายกเทศมนตรีกิลเบิร์ตเพื่อเริ่มการสำรวจบทที่ 1 ก่อนนะจ๊ะ)';
            }
        } else if (q2State === 'active') {
            const spores = this.countItemInInventory('blight_spore');
            const herbs = this.countItemInInventory('starflower_herb');
            if (spores >= 3 && herbs >= 2) {
                textEl.textContent = dlgs.q2_complete || 'ยอดเยี่ยมมาก! สปอร์กับสมุนไพรทำปฏิกิริยากลายเป็นเซรุ่มใสสีคราม นี่คือเซรุ่มต้านสปอร์พิษและดาบเหล็กกล้าสำหรับเจ้า!';
                const turnInQ2Btn = document.createElement('button');
                turnInQ2Btn.className = 'btn-dialogue-action btn-quest-accept';
                turnInQ2Btn.textContent = 'สกัดเซรุ่มต้านพิษสำเร็จ (รับ 350 G + เซรุ่ม x2 + ดาบเหล็กกล้า + 180 XP)';
                turnInQ2Btn.onclick = () => {
                    this.removeItemFromInventory('blight_spore', 3);
                    this.removeItemFromInventory('starflower_herb', 2);
                    this.player.quests.q2 = 'completed';
                    this.player.quests.q3 = 'active'; // Progress to Chapter 3
                    this.player.gold += 350;
                    this.addXp(180);
                    this.addItemToInventory('antidote_serum', 2, 'เซรุ่มต้านสปอร์พิษ (Antidote Serum)');
                    this.addItemToInventory('iron_sword', 1, 'ดาบเหล็กกล้านักผจญภัย (Iron Sword)');
                    SoundEngine.levelUp();
                    this.addFloatingText('สำเร็จบทที่ 2! ได้รับเซรุ่มต้านพิษ x2 + ดาบเหล็กกล้า', this.player.x, this.player.y - 25, '#4ade80');
                    this.closeDialogue();
                    this.updateHUD();
                };

                actionsEl.appendChild(turnInQ2Btn);
            } else {
                textEl.textContent = `สมุนไพรดวงดาว (${herbs}/2 ดอก) และ สปอร์กลายพันธุ์ (${spores}/3 ชิ้น) ยังไม่ครบจ้ะ สมุนไพรหาได้ในป่าและสวนคลินิกนะ!`;
            }
        } else if (this.player.quests.q6 === 'completed' && (!this.player.quests.q7 || this.player.quests.q7 === 'not_started')) {
            textEl.textContent = dlgs.q7_intro || 'ท่านผู้กล้าจ๊ะ! สายน้ำเริ่มมีสารพิษสีเขียวมรกตปนเปื้อน... มันไหลมาจาก "พญาไฮดราสามเศียร ไฮดราคิส" ในหนองน้ำมืดทางตะวันตกเฉียงใต้!';
            const acceptQ7Btn = document.createElement('button');
            acceptQ7Btn.className = 'btn-dialogue-action btn-quest-accept';
            acceptQ7Btn.textContent = 'รับภารกิจบทที่ 7: กวาดล้างมัจจุราชแห่งบึงมืด';
            acceptQ7Btn.onclick = () => {
                this.player.quests.q7 = 'active';
                SoundEngine.bossRoar();
                this.addFloatingText('รับภารกิจบทที่ 7: กวาดล้างมัจจุราชแห่งบึงมืด!', this.player.x, this.player.y - 20, '#22c55e');
                this.closeDialogue();
                this.updateHUD();
            };
            actionsEl.appendChild(acceptQ7Btn);
        } else if (this.player.quests.q7 === 'active') {
            if (this.player.questProgress.hydrakisDefeated) {
                textEl.textContent = dlgs.q7_complete || 'น่าอัศจรรย์ยิ่งนัก! ต่อมพิษบริสุทธิ์จากพญาไฮดรานี้มีฤทธิ์ต้านพิษทุกชนิดในโลก ขอบใจเจ้ามากนะจ๊ะ!';
                const turnInQ7Btn = document.createElement('button');
                turnInQ7Btn.className = 'btn-dialogue-action btn-quest-accept';
                turnInQ7Btn.textContent = 'ส่งภารกิจบทที่ 7 (รับ 3,500 G + ยาฟื้นพลัง x5 + 1,800 XP)';
                turnInQ7Btn.onclick = () => {
                    this.player.quests.q7 = 'completed';
                    this.player.gold += 3500;
                    this.addXp(1800);
                    this.addItemToInventory('health_potion', 5, 'ยาฟื้นพลังชีวิตชั้นเลิศ');
                    SoundEngine.levelUp();
                    this.addFloatingText('สำเร็จบทที่ 7! ปลดล็อกบทที่ 8 กับผู้กองวาเลเรีย', this.player.x, this.player.y - 25, '#4ade80');
                    this.closeDialogue();
                    this.updateHUD();
                };
                actionsEl.appendChild(turnInQ7Btn);
            } else {
                textEl.textContent = dlgs.q7_progress || 'หนองน้ำมืดเต็มไปด้วยไอพิษ อย่าลืมดื่มเซรุ่มต้านพิษและทานซุปเกราะสมุนไพรก่อนเข้าสู้นะจ๊ะ!';
            }
        } else {
            textEl.textContent = dlgs.ready_craft || 'ยินดีต้อนรับสู่คลินิกสมุนไพร! ต้องการให้ข้าช่วยปรุงยาหรือดูแลสุขภาพไหมจ๊ะ?';
        }

        // Potion Crafting Shortcut
        const craftSerumBtn = document.createElement('button');
        craftSerumBtn.className = 'btn-dialogue-action';
        craftSerumBtn.textContent = 'ปรุงเซรุ่มต้านพิษ (สปอร์ x2 + สมุนไพร x1 + 50 G)';
        craftSerumBtn.onclick = () => {
            const sp = this.countItemInInventory('blight_spore');
            const hb = this.countItemInInventory('starflower_herb');
            if (sp >= 2 && hb >= 1 && this.player.gold >= 50) {
                this.removeItemFromInventory('blight_spore', 2);
                this.removeItemFromInventory('starflower_herb', 1);
                this.player.gold -= 50;
                this.addItemToInventory('antidote_serum', 1, 'เซรุ่มต้านสปอร์พิษ');
                SoundEngine.craft();
                this.addFloatingText('ปรุงเซรุ่มต้านสปอร์พิษ สำเร็จ!', this.player.x, this.player.y - 20, '#22d3ee');
                this.updateHUD();
            } else {
                this.addFloatingText('วัตถุดิบหรือเงินไม่พอ (สปอร์ x2, สมุนไพร x1, 50 G)', this.player.x, this.player.y - 20, '#ef4444');
            }
        };

        actionsEl.appendChild(craftSerumBtn);

        // Medical Care Button
        const healBtn = document.createElement('button');
        healBtn.className = 'btn-dialogue-action';
        healBtn.textContent = 'รับการรักษาพยาบาล (ฟื้นฟู HP เต็ม 40 G)';
        healBtn.onclick = () => {
            if (this.player.gold >= 40) {
                this.player.gold -= 40;
                this.player.hp = this.player.maxHp;
                SoundEngine.levelUp();
                this.addFloatingText('ฟื้นฟู HP เต็ม 100%! (-40 G)', this.player.x, this.player.y - 20, '#4ade80');
                this.updateHUD();
                this.closeDialogue();
            } else {
                this.addFloatingText('เงินไม่พอ (ต้องการ 40 G)', this.player.x, this.player.y - 20, '#ef4444');
            }
        };

        actionsEl.appendChild(healBtn);
    } else if (npcId === 'valeria') {
        const q2State = this.player.quests.q2;
        const q3State = this.player.quests.q3;

        if (!q3State || q3State === 'not_started') {
            textEl.textContent = dlgs.intro || 'สวัสดีท่านชาวสวน! ข้าผู้กองวาเลเรีย กำลังระดมกำลังตรึงประตูปราการเหนือของหมู่บ้าน!';
            if (q2State === 'completed') {
                const acceptQ3Btn = document.createElement('button');
                acceptQ3Btn.className = 'btn-dialogue-action btn-quest-accept';
                acceptQ3Btn.textContent = 'รับภารกิจบทที่ 3: ตรึงแนวรบปราการเหนือ';
                acceptQ3Btn.onclick = () => {
                    this.player.quests.q3 = 'active';
                    SoundEngine.levelUp();
                    this.addFloatingText('รับภารกิจบทที่ 3: ตรึงแนวรบปราการเหนือ', this.player.x, this.player.y - 20, '#fde047');
                    this.closeDialogue();
                    this.updateHUD();
                };

                actionsEl.appendChild(acceptQ3Btn);
            } else {
                textEl.textContent += ' (เจ้าต้องช่วยลิเลียนคิดค้นเซรุ่มในบทที่ 2 เสียก่อน จึงจะพร้อมรบกับสัตว์ป่าติดเชื้อด้านนอก!)';
            }
        } else if (q3State === 'active') {
            const wolvesKilled = this.player.questProgress.wolvesKilled || 0;
            const rubies = this.countItemInInventory('ruby_gem');
            if (wolvesKilled >= 3 && rubies >= 2) {
                textEl.textContent = dlgs.q3_complete || 'ขอบคุณที่ช่วยกวาดล้างแนวหน้า! แร่ทับทิมเหล่านี้ ช่างตีเหล็กคาเอลได้นำไปตีเสริมคมอาวุธแล้ว รับปืนล่าสัตว์โบราณกระบอกนี้ไปใช้เถิด!';
                const turnInQ3Btn = document.createElement('button');
                turnInQ3Btn.className = 'btn-dialogue-action btn-quest-accept';
                turnInQ3Btn.textContent = 'ส่งภารกิจบทที่ 3 (รับ 500 G + ปืนล่าสัตว์โบราณ + 250 XP)';
                turnInQ3Btn.onclick = () => {
                    this.removeItemFromInventory('ruby_gem', 2);
                    this.player.quests.q3 = 'completed';
                    this.player.quests.q4 = 'active'; // Progress to Chapter 4
                    this.player.gold += 500;
                    this.addXp(250);
                    this.addItemToInventory('rifle', 1, 'ปืนล่าสัตว์โบราณ (Hunting Rifle)');
                    SoundEngine.levelUp();
                    this.addFloatingText('สำเร็จบทที่ 3! ได้รับปืนล่าสัตว์โบราณ (+500 G, +250 XP)', this.player.x, this.player.y - 25, '#4ade80');
                    this.closeDialogue();
                    this.updateHUD();
                };

                actionsEl.appendChild(turnInQ3Btn);
            } else {
                textEl.textContent = `ระวังตัวด้วยนะสหาย! เจ้ากำจัดหมาป่าเงาไปแล้ว ${wolvesKilled}/3 ตัว และขุดแร่ทับทิมได้ ${rubies}/2 ก้อน ในป่าทึบยังมีสัตว์ติดเชื้อซุ่มอยู่!`;
            }
        } else if (this.player.quests.q7 === 'completed' && (!this.player.quests.q8 || this.player.quests.q8 === 'not_started')) {
            textEl.textContent = dlgs.q8_intro || 'สัญญาณเตือนภัยสีแดงระดับสูงสุด! เตาลาวาโบราณ ณ ปากปล่องภูเขาไฟทางตะวันตกเฉียงเหนือกำลังเดือดพล่าน "ราชันย์มังกรลาวา อิกนิสทรอน" กำลังจะพ่นฝนเพลิงเผาผลาญเมือง!';
            const acceptQ8Btn = document.createElement('button');
            acceptQ8Btn.className = 'btn-dialogue-action btn-quest-accept';
            acceptQ8Btn.textContent = 'รับภารกิจบทที่ 8: โทสะแห่งภูเขาไฟลาวาเดือด';
            acceptQ8Btn.onclick = () => {
                this.player.quests.q8 = 'active';
                SoundEngine.bossRoar();
                this.addFloatingText('รับภารกิจบทที่ 8: โทสะแห่งภูเขาไฟลาวาเดือด!', this.player.x, this.player.y - 20, '#ef4444');
                this.closeDialogue();
                this.updateHUD();
            };
            actionsEl.appendChild(acceptQ8Btn);
        } else if (this.player.quests.q8 === 'active') {
            if (this.player.questProgress.ignistronDefeated) {
                textEl.textContent = dlgs.q8_complete || 'สุดยอดการรบ! ท่านดับเพลิงพิโรธของมังกรลาวาลงได้สำเร็จ แผ่นดินรอดพ้นจากทะเลเพลิง!';
                const turnInQ8Btn = document.createElement('button');
                turnInQ8Btn.className = 'btn-dialogue-action btn-quest-accept';
                turnInQ8Btn.textContent = 'ส่งภารกิจบทที่ 8 (รับ 4,000 G + ทับทิม x5 + 2,000 XP)';
                turnInQ8Btn.onclick = () => {
                    this.player.quests.q8 = 'completed';
                    this.player.quests.q9 = 'active';
                    this.player.gold += 4000;
                    this.addXp(2000);
                    this.addItemToInventory('ruby_gem', 5, 'อัญมณีทับทิมโลกันตร์');
                    SoundEngine.levelUp();
                    this.addFloatingText('สำเร็จบทที่ 8! ปลดล็อกบทที่ 9 กับช่างตีเหล็กคาเอล', this.player.x, this.player.y - 25, '#4ade80');
                    this.closeDialogue();
                    this.updateHUD();
                };
                actionsEl.appendChild(turnInQ8Btn);
            } else {
                textEl.textContent = dlgs.q8_progress || 'ระวังอุกกาบาตเพลิงและธารลาวาเดือดของอิกนิสทรอนด้วยนะสหาย! รีบหลบวงเตือนบนพื้นให้ทัน!';
            }
        } else {
            textEl.textContent = 'แนวรบปราการเหนือมั่นคงแล้ว! ขอบใจเจ้ามาก บัดนี้จงไปปรึกษา ผู้เฒ่าปราชญ์เอลดริน ที่วิหารศักดิ์สิทธิ์เพื่อสืบหารังไหมของแมลงยักษ์เถิด!';
        }
    } else if (npcId === 'eldrin') {
        const q3State = this.player.quests.q3;
        const q4State = this.player.quests.q4;

        if (!q4State || q4State === 'not_started') {
            textEl.textContent = dlgs.intro || 'โฮ่โฮ่... พืชผลในฟาร์มของเจ้าเติบโตงดงามยิ่งนัก แต่จงรู้ไว้เถิด ใต้ผืนดินมีรังไหมของแมลงปีศาจฟักตัวอยู่!';
            if (q3State === 'completed') {
                const acceptQ4Btn = document.createElement('button');
                acceptQ4Btn.className = 'btn-dialogue-action btn-quest-accept';
                acceptQ4Btn.textContent = 'รับภารกิจบทที่ 4: สำรวจถ้ำรังไหมผลึก';
                acceptQ4Btn.onclick = () => {
                    this.player.quests.q4 = 'active';
                    SoundEngine.levelUp();
                    this.addFloatingText('รับภารกิจบทที่ 4: สำรวจถ้ำรังไหมผลึก', this.player.x, this.player.y - 20, '#fde047');
                    this.closeDialogue();
                    this.updateHUD();
                };

                actionsEl.appendChild(acceptQ4Btn);
            } else {
                textEl.textContent += ' (เจ้าต้องช่วยผู้กองวาเลเรียตรึงแนวรบเหนือในบทที่ 3 ก่อน จึงจะมีกำลังพอสำรวจถ้ำลึก!)';
            }
        } else if (q4State === 'active') {
            const manaGems = this.countItemInInventory('mana_gem');
            const caveKills = this.player.questProgress.caveMonstersDefeated || 0;
            if (manaGems >= 2 && caveKills >= 3) {
                textEl.textContent = dlgs.q4_complete || 'ผลึกมานาบริสุทธิ์เหล่านี้จะช่วยสะกดรอยคลื่นพลังของราชินีสปอร์ได้ บัดนี้เส้นทางสู่วิหารเปิดออกแล้ว จงมุ่งหน้าไปเถิด!';
                const turnInQ4Btn = document.createElement('button');
                turnInQ4Btn.className = 'btn-dialogue-action btn-quest-accept';
                turnInQ4Btn.textContent = 'ส่งภารกิจบทที่ 4 (รับ 800 G + เซรุ่มต้านสปอร์พิษ x3 + 400 XP)';
                turnInQ4Btn.onclick = () => {
                    this.removeItemFromInventory('mana_gem', 2);
                    this.player.quests.q4 = 'completed';
                    this.player.gold += 800;
                    this.addXp(400);
                    this.addItemToInventory('antidote_serum', 3, 'เซรุ่มต้านสปอร์พิษ (Antidote Serum)');
                    SoundEngine.levelUp();
                    this.addFloatingText('สำเร็จบทที่ 4! รายงานนายกฯ กิลเบิร์ตเพื่อเปิดศึกชี้ชะตาบทที่ 5', this.player.x, this.player.y - 25, '#4ade80');
                    this.closeDialogue();
                    this.updateHUD();
                };

                actionsEl.appendChild(turnInQ4Btn);
            } else {
                textEl.textContent = `ในถ้ำผลึกใต้พิภพทางตะวันออกเฉียงเหนือ เจ้าขุดผลึกมานาสีครามได้แล้ว (${manaGems}/2 ชิ้น) และกำจัดอสูรในถ้ำ (${caveKills}/3 ตัว) จงสำรวจให้ทั่ว!`;
            }
        } else if (this.player.quests.q5 === 'completed' && (!this.player.quests.q6 || this.player.quests.q6 === 'not_started')) {
            textEl.textContent = dlgs.q6_intro || 'โฮ่โฮ่... แม้คาธูรอสจะสิ้นฤทธิ์ แต่ข้าสัมผัสได้ถึงคลื่นพลังเวทมนตร์อันมหาศาลจากรอยแยกลึกใต้ถ้ำผลึก (The Crystal Abyss Floor -2)! โกเลมผลึกโบราณ ลูมินาร์ค ได้ตื่นขึ้นแล้ว!';
            const acceptQ6Btn = document.createElement('button');
            acceptQ6Btn.className = 'btn-dialogue-action btn-quest-accept';
            acceptQ6Btn.textContent = 'รับภารกิจบทที่ 6: หัวใจผลึกปริซึมใต้พิภพ';
            acceptQ6Btn.onclick = () => {
                this.player.quests.q6 = 'active';
                SoundEngine.bossRoar();
                this.addFloatingText('รับภารกิจบทที่ 6: หัวใจผลึกปริซึมใต้พิภพ!', this.player.x, this.player.y - 20, '#06b6d4');
                this.closeDialogue();
                this.updateHUD();
            };
            actionsEl.appendChild(acceptQ6Btn);
        } else if (this.player.quests.q6 === 'active') {
            if (this.player.questProgress.luminarchDefeated) {
                textEl.textContent = dlgs.q6_complete || 'มหัศจรรย์ยิ่งนัก! หัวใจผลึกปริซึมส่องแสงรุ้งบริสุทธิ์ บัดนี้ช่างคาเอลสามารถหลอม "ดาบเลเซอร์ผลึกปริซึมลูมินาร์ค" ได้แล้ว!';
                const turnInQ6Btn = document.createElement('button');
                turnInQ6Btn.className = 'btn-dialogue-action btn-quest-accept';
                turnInQ6Btn.textContent = 'ส่งภารกิจบทที่ 6 (รับ 3,000 G + เพชร x3 + 1,500 XP)';
                turnInQ6Btn.onclick = () => {
                    this.player.quests.q6 = 'completed';
                    this.player.quests.q7 = 'active';
                    this.player.gold += 3000;
                    this.addXp(1500);
                    this.addItemToInventory('diamond_crystal', 3, 'เพชรผลึกประกายรุ้ง');
                    SoundEngine.levelUp();
                    this.addFloatingText('สำเร็จบทที่ 6! ปลดล็อกบทที่ 7 ที่คลินิกหมอยาลิเลียน', this.player.x, this.player.y - 25, '#4ade80');
                    this.closeDialogue();
                    this.updateHUD();
                };
                actionsEl.appendChild(turnInQ6Btn);
            } else {
                textEl.textContent = dlgs.q6_progress || 'จงลงบันไดรอยแยกผลึก (Abyss Rift) ในถ้ำ สยบโกเลมลูมินาร์คใน The Crystal Abyss Floor -2!';
            }
        } else {
            textEl.textContent = dlgs.victory || 'ความสงบสุขกลับคืนสู่ผืนป่าและฟาร์มของเราแล้ว ขอพรแห่งปัญญาและแสงสว่างจงสถิตอยู่กับเจ้าตลอดกาล ผู้กล้าแห่งฟาร์มสุขใจ!';
        }

        // Eldrin's Holy Blessing button (always available)
        const blessBtn = document.createElement('button');
        blessBtn.className = 'btn-dialogue-action';
        blessBtn.textContent = 'ขอรับพรศักดิ์สิทธิ์ (ฟื้นฟู HP และพลังงานเต็ม)';
        blessBtn.onclick = () => {
            this.player.hp = this.player.maxHp;
            this.player.energy = this.player.maxEnergy;
            SoundEngine.levelUp();
            this.spawnParticles(this.player.x + 12, this.player.y + 16, '#38bdf8', 16);
            this.addFloatingText('ได้รับพรศักดิ์สิทธิ์! ฟื้นฟู HP 100% & พลังงาน 100%', this.player.x - 20, this.player.y - 20, '#38bdf8');
            this.updateHUD();
            this.closeDialogue();
        };

        actionsEl.appendChild(blessBtn);
    } else if (npcId === 'bob') {
        textEl.textContent = dlgs.intro || 'ฮ่าฮ่าฮ่า! ยินดีต้อนรับสู่โรงเตี๊ยมรวงทอง สหายเอ๋ย! เข้ามาพักเหนื่อย จิบเบียร์ข้าวสาลีหรือกินปลาย่างสักจานไหม?';

        // Order Tavern Food & Drink
        const orderFoodBtn = document.createElement('button');
        orderFoodBtn.className = 'btn-dialogue-action';
        orderFoodBtn.textContent = 'ดื่มเบียร์ข้าวสาลี & อาหารย่าง (ฟื้นฟู HP +40, พลังงาน +40 จ่าย 30 G)';
        orderFoodBtn.onclick = () => {
            if (this.player.gold >= 30) {
                this.player.gold -= 30;
                this.player.hp = Math.min(this.player.maxHp, this.player.hp + 40);
                this.player.energy = Math.min(this.player.maxEnergy, this.player.energy + 40);
                SoundEngine.craft();
                this.addFloatingText('ดื่มเบียร์ข้าวสาลีสดชื่น! ฟื้นฟู HP +40 & พลังงาน +40 (-30 G)', this.player.x, this.player.y - 20, '#facc15');
                this.updateHUD();
            } else {
                this.addFloatingText('เงินไม่พอ (ต้องการ 30 G)', this.player.x, this.player.y - 20, '#ef4444');
            }
        };

        actionsEl.appendChild(orderFoodBtn);

        // Bounty Board button
        const bountyBtn = document.createElement('button');
        bountyBtn.className = 'btn-dialogue-action btn-quest-accept';
        bountyBtn.textContent = 'ตรวจสอบกระดานประกาศล่าค่าหัวมหาบอส (Bounty Board)';
        bountyBtn.onclick = () => {
            this.closeDialogue();
            this.openBountyBoard();
        };
        actionsEl.appendChild(bountyBtn);

        // Ask for Rumors
        const rumorBtn = document.createElement('button');
        rumorBtn.className = 'btn-dialogue-action';
        rumorBtn.textContent = 'สอบถามข่าวลือเกี่ยวกับโรคระบาดแมลงยักษ์';
        rumorBtn.onclick = () => {
            textEl.textContent = dlgs.rumors || 'พรานป่าเล่าว่า พวกแมลงยักษ์ชอบมาวางไข่ในถ้ำผลึกคริสตัลทางตะวันออกเฉียงเหนือ หมอกควันสีม่วงที่ลอยออกมามีกลิ่นพิษฉุนกึก หากเจ้าจะเข้าไปข้างใน อย่าลืมพกเซรุ่มต้านพิษของหมอยาลิเลียนติดตัวไปด้วยล่ะ!';
        };

        actionsEl.appendChild(rumorBtn);
    } else if (npcId === 'kael') {
        textEl.textContent = dlgs.intro || dlgs.forge_ready || 'ยินดีต้อนรับสู่เตาหลอมของข้า! นำแร่และผลึกมาสิ ข้าจะตีสุดยอดอาวุธให้!';

        if (this.player.quests.q8 === 'completed' && (!this.player.quests.q9 || this.player.quests.q9 === 'not_started')) {
            textEl.textContent = dlgs.q9_intro || 'เฮ้สหาย! ลมหนาวผิดธรรมชาติกำลังแช่แข็งสายแร่บนยอดเขาหิมะเยือกแข็ง (Frostpeak) ทางตะวันออกเฉียงเหนือ! "จอมอสูรไททันน้ำแข็ง ฟรอสต์แฟงก์" ตื่นขึ้นมาแล้ว!';
            const acceptQ9Btn = document.createElement('button');
            acceptQ9Btn.className = 'btn-dialogue-action btn-quest-accept';
            acceptQ9Btn.textContent = 'รับภารกิจบทที่ 9: ไททันเหมันต์แห่งยอดเขาเยือกแข็ง';
            acceptQ9Btn.onclick = () => {
                this.player.quests.q9 = 'active';
                SoundEngine.bossRoar();
                this.addFloatingText('รับภารกิจบทที่ 9: ไททันเหมันต์แห่งยอดเขาเยือกแข็ง!', this.player.x, this.player.y - 20, '#38bdf8');
                this.closeDialogue();
                this.updateHUD();
            };
            actionsEl.appendChild(acceptQ9Btn);
        } else if (this.player.quests.q9 === 'active') {
            if (this.player.questProgress.frostfangDefeated) {
                textEl.textContent = dlgs.q9_complete || 'โอ้โห! แก่นเหมันต์พันปีช่างงดงามและเย็นยะเยือกจับตา! ค้อนเหมันต์ไททันน้ำแข็งพร้อมตีขึ้นรูปในเตาหลอมแล้ว!';
                const turnInQ9Btn = document.createElement('button');
                turnInQ9Btn.className = 'btn-dialogue-action btn-quest-accept';
                turnInQ9Btn.textContent = 'ส่งภารกิจบทที่ 9 (รับ 4,500 G + ผลึกน้ำแข็ง x5 + 2,500 XP)';
                turnInQ9Btn.onclick = () => {
                    this.player.quests.q9 = 'completed';
                    this.player.gold += 4500;
                    this.addXp(2500);
                    this.addItemToInventory('frost_crystal', 5, 'ผลึกน้ำแข็งบริสุทธิ์');
                    SoundEngine.levelUp();
                    this.addFloatingText('สำเร็จบทที่ 9! รายงานนายกฯ กิลเบิร์ตเพื่อเปิดศึกอวสานบทที่ 10', this.player.x, this.player.y - 25, '#4ade80');
                    this.closeDialogue();
                    this.updateHUD();
                };
                actionsEl.appendChild(turnInQ9Btn);
            } else {
                textEl.textContent = dlgs.q9_progress || 'พายุหิมะบนยอดเขาหนาวเหน็บจับขั้วหัวใจ จงใช้อาวุธธาตุไฟอย่างดาบเพลิงลาวาฟันทะลวงเกราะน้ำแข็งของมันนะ!';
            }
        }

        const openForgeBtn = document.createElement('button');
        openForgeBtn.className = 'btn-dialogue-action btn-quest-accept';
        openForgeBtn.textContent = 'เปิดโรงตีเหล็ก (Forge)';
        openForgeBtn.onclick = () => {
            this.closeDialogue();
            this.openModal('forgeModal');
        };

        actionsEl.appendChild(openForgeBtn);
    }

    // Check NPC Heart Events (Heart 2 = 40 pts, Heart 4 = 80 pts)
    const friendshipPts = this.player.npcFriendship?.[npcId] || 0;
    const seenEvents = this.player.seenHeartEvents || {};

    const event2Id = `${npcId}_heart2`;
    const event4Id = `${npcId}_heart4`;

    if ((NPC_HEART_EVENTS as any)?.[event2Id] && friendshipPts >= 40 && !seenEvents[event2Id]) {
        const heart2Btn = document.createElement('button');
        heart2Btn.className = 'btn-dialogue-action btn-quest-accept';
        heart2Btn.textContent = '★ เหตุการณ์ผูกใจ 2 หัวใจ';
        heart2Btn.onclick = () => {
            this.closeDialogue();
            this.triggerHeartEvent(event2Id);
        };
        actionsEl.appendChild(heart2Btn);
    }

    if ((NPC_HEART_EVENTS as any)?.[event4Id] && friendshipPts >= 80 && !seenEvents[event4Id]) {
        const heart4Btn = document.createElement('button');
        heart4Btn.className = 'btn-dialogue-action btn-quest-accept';
        heart4Btn.textContent = '★ เหตุการณ์ผูกใจ 4 หัวใจ';
        heart4Btn.onclick = () => {
            this.closeDialogue();
            this.triggerHeartEvent(event4Id);
        };
        actionsEl.appendChild(heart4Btn);
    }

    // Gift Button
    const giftBtn = document.createElement('button');
    giftBtn.className = 'btn-dialogue-action btn-gift-give';
    giftBtn.textContent = 'มอบของขวัญ';
    giftBtn.onclick = () => this.openGiftSelectModal(npcId);
    actionsEl.appendChild(giftBtn);

    // Close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'btn-dialogue-action';
    closeBtn.textContent = '✕ ปิดการสนทนา';
    closeBtn.onclick = () => this.closeDialogue();
    actionsEl.appendChild(closeBtn);
};


Game.closeDialogue = function() {
    this.activeDialogue = null;
    const box = document.getElementById('storyDialogueBox');
    if (box) box.style.display = 'none';
};


Game.renderQuestModal = function() {
    const list = document.getElementById('questsList');
    if (!list) return;
    list.innerHTML = '';

    Object.values(QUESTS).forEach(q => {
        const state = this.player.quests[q.id] || 'available';
        const card = document.createElement('div');
        card.className = 'quest-card';

        let statusText = 'ยังไม่ได้รับ';
        let statusClass = 'quest-badge-locked';
        let progressDetail = '';

        if (state === 'completed') {
            statusText = '✓ เสร็จสิ้นแล้ว';
            statusClass = 'quest-badge-completed';
            progressDetail = '<div class="quest-prog-text" style="color:#4ade80;">✓ สำเร็จเควสต์แล้ว และรับรางวัลเรียบร้อย</div>';
        } else if (state === 'active') {
            statusText = 'กำลังดำเนินการ';
            statusClass = 'quest-badge-active';

            if (q.id === 'q1') {
                const count = Math.min(3, this.player.questProgress.bugsDefeated || 0);
                const sp = Math.min(2, this.countItemInInventory('blight_spore'));
                progressDetail = `<div class="quest-prog-text">กำจัดแมลงยักษ์: ${count}/3 ตัว | สปอร์กลายพันธุ์: ${sp}/2 ชิ้น</div>`;
            } else if (q.id === 'q2') {
                const sp = Math.min(3, this.countItemInInventory('blight_spore'));
                const h = Math.min(2, this.countItemInInventory('starflower_herb'));
                progressDetail = `<div class="quest-prog-text">สปอร์กลายพันธุ์: ${sp}/3 ชิ้น | สมุนไพรดวงดาว: ${h}/2 ดอก</div>`;
            } else if (q.id === 'q3') {
                const count = Math.min(3, this.player.questProgress.wolvesKilled || 0);
                const r = Math.min(2, this.countItemInInventory('ruby_gem'));
                progressDetail = `<div class="quest-prog-text">กำจัดหมาป่าเงา: ${count}/3 ตัว | แร่ทับทิม: ${r}/2 ก้อน</div>`;
            } else if (q.id === 'q4') {
                const mg = Math.min(2, this.countItemInInventory('mana_gem'));
                const caveKills = Math.min(3, this.player.questProgress.caveMonstersDefeated || 0);
                progressDetail = `<div class="quest-prog-text">ผลึกมานาสีคราม: ${mg}/2 ชิ้น | อสูรในถ้ำผลึก: ${caveKills}/3 ตัว</div>`;
            } else if (q.id === 'q5') {
                const def = this.player.questProgress.kathurosDefeated ? '✓ สยบสำเร็จ' : 'ยังไม่ถูกปราบ';
                progressDetail = `<div class="quest-prog-text">ราชินีสปอร์ปีศาจ คาธูรอส: ${def}</div>`;
            } else if (q.id === 'q6') {
                const def = this.player.questProgress.luminarchDefeated ? '✓ สยบสำเร็จ' : 'ยังไม่ถูกปราบ';
                progressDetail = `<div class="quest-prog-text">โกเลมผลึกโบราณ ลูมินาร์ค (ถ้ำผลึกลึก -2): ${def}</div>`;
            } else if (q.id === 'q7') {
                const def = this.player.questProgress.hydrakisDefeated ? '✓ สยบสำเร็จ' : 'ยังไม่ถูกปราบ';
                progressDetail = `<div class="quest-prog-text">พญาไฮดราสามเศียร ไฮดราคิส (หนองน้ำมืด): ${def}</div>`;
            } else if (q.id === 'q8') {
                const def = this.player.questProgress.ignistronDefeated ? '✓ สยบสำเร็จ' : 'ยังไม่ถูกปราบ';
                progressDetail = `<div class="quest-prog-text">ราชันย์มังกรลาวา อิกนิสทรอน (ภูเขาไฟ): ${def}</div>`;
            } else if (q.id === 'q9') {
                const def = this.player.questProgress.frostfangDefeated ? '✓ สยบสำเร็จ' : 'ยังไม่ถูกปราบ';
                progressDetail = `<div class="quest-prog-text">จอมอสูรไททันน้ำแข็ง ฟรอสต์แฟงก์ (ยอดเขาหิมะ): ${def}</div>`;
            } else if (q.id === 'q10') {
                const def = this.player.questProgress.malakorDefeated ? '✓ สยบสำเร็จ' : 'ยังไม่ถูกปราบ';
                progressDetail = `<div class="quest-prog-text">ลอร์ดมรณะกระดูกอสูร มาลาคอร์ (สุสานใต้พิภพ): ${def}</div>`;
            }
        } else {
            progressDetail = `<div class="quest-prog-text" style="color:#94a3b8;">คุยกับ ${NPC_STORY[q.giver]?.name || 'NPC'} เพื่อรับภารกิจ</div>`;
        }

        card.innerHTML = `
            <div class="quest-card-header">
                <h4>${q.title}</h4>
                <span class="quest-status-badge ${statusClass}">${statusText}</span>
            </div>
            <p class="quest-card-desc">${q.desc}</p>
            ${progressDetail}
            <div class="quest-card-reward">
                รางวัล: <span>${q.rewardText || q.rewardDesc || ''}</span>
            </div>
        `;
        list.appendChild(card);
    });
};


Game.buyBlacksmithSupply = function(matId: string, count: number, totalCost: number) {
    if (this.player.gold < totalCost) {
        this.addFloatingText('เหรียญทองไม่เพียงพอ!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }
    if (!this.canItemFitInInventory(matId, count)) {
        SoundEngine.hit();
        this.addFloatingText('กระเป๋าเต็มแล้ว! จัดช่องเก็บของหรือใส่กล่องก่อนซื้อ', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }
    this.player.gold -= totalCost;
    const matName = (WORLD_ITEMS && WORLD_ITEMS[matId]?.name) || matId;
    this.addItemToInventory(matId, count, matName);
    SoundEngine.coin();
    this.addFloatingText(`+${count} ${matName} (-${totalCost} G)`, this.player.x, this.player.y - 20, '#facc15');
    this.updateHUD();
    this.renderForgeModal();
};

Game.renderForgeModal = function() {
    const list = document.getElementById('forgeList');
    if (!list) return;
    list.innerHTML = '';

    // 1. Blacksmith Direct Supplies (แผงขายแร่ & วัตถุดิบตีเหล็กของคาเอล)
    const supplyContainer = document.createElement('div');
    supplyContainer.className = 'forge-supplies-banner';
    supplyContainer.style.cssText = 'background: rgba(180, 83, 9, 0.08); border: 1.5px dashed #b45309; border-radius: 8px; padding: 10px 12px; margin-bottom: 12px; width: 100%; box-sizing: border-box;';
    
    supplyContainer.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-weight: 700; color: #78350f; font-size: 13px;">[วัตถุดิบ] เสบียงแร่ช่างตีเหล็ก คาเอล (ซื้อวัตถุดิบตีเหล็กได้ทันที)</span>
            <span style="font-size: 11px; color: #92400e; font-weight: 600;">เหรียญทอง: ${this.player.gold} G</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 8px;">
            <div style="background: #fff8ee; border: 1px solid #d4a373; border-radius: 6px; padding: 6px 8px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <img src="${SPRITES.getItemDataURL('iron_ore')}" style="width: 22px; height: 22px; image-rendering: pixelated;">
                    <div style="font-size: 11px; font-weight: 700; color: #451a03;">แร่เหล็กดิบ<br><span style="color: #b45309; font-weight: 600;">60 G/ก้อน</span></div>
                </div>
                <div style="display: flex; gap: 4px;">
                    <button class="btn-buy" style="padding: 3px 6px; font-size: 10px; border-radius: 4px;" onclick="Game.buyBlacksmithSupply('iron_ore', 1, 60)">+1</button>
                    <button class="btn-buy" style="padding: 3px 6px; font-size: 10px; border-radius: 4px; font-weight: 700;" onclick="Game.buyBlacksmithSupply('iron_ore', 2, 120)">+2 (120G)</button>
                </div>
            </div>
            <div style="background: #fff8ee; border: 1px solid #d4a373; border-radius: 6px; padding: 6px 8px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <img src="${SPRITES.getItemDataURL('copper_ore')}" style="width: 22px; height: 22px; image-rendering: pixelated;">
                    <div style="font-size: 11px; font-weight: 700; color: #451a03;">แร่ทองแดง<br><span style="color: #b45309; font-weight: 600;">35 G/ก้อน</span></div>
                </div>
                <div style="display: flex; gap: 4px;">
                    <button class="btn-buy" style="padding: 3px 6px; font-size: 10px; border-radius: 4px;" onclick="Game.buyBlacksmithSupply('copper_ore', 2, 70)">+2 (70G)</button>
                </div>
            </div>
            <div style="background: #fff8ee; border: 1px solid #d4a373; border-radius: 6px; padding: 6px 8px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <img src="${SPRITES.getItemDataURL('cursed_wood')}" style="width: 22px; height: 22px; image-rendering: pixelated;">
                    <div style="font-size: 11px; font-weight: 700; color: #451a03;">ไม้ต้องสาป<br><span style="color: #b45309; font-weight: 600;">85 G/ท่อน</span></div>
                </div>
                <div style="display: flex; gap: 4px;">
                    <button class="btn-buy" style="padding: 3px 6px; font-size: 10px; border-radius: 4px;" onclick="Game.buyBlacksmithSupply('cursed_wood', 1, 85)">+1</button>
                    <button class="btn-buy" style="padding: 3px 6px; font-size: 10px; border-radius: 4px; font-weight: 700;" onclick="Game.buyBlacksmithSupply('cursed_wood', 2, 170)">+2 (170G)</button>
                </div>
            </div>
            <div style="background: #fff8ee; border: 1px solid #d4a373; border-radius: 6px; padding: 6px 8px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <img src="${SPRITES.getItemDataURL('wood')}" style="width: 22px; height: 22px; image-rendering: pixelated;">
                    <div style="font-size: 11px; font-weight: 700; color: #451a03;">ท่อนไม้โอ๊ค<br><span style="color: #b45309; font-weight: 600;">15 G/ท่อน</span></div>
                </div>
                <div style="display: flex; gap: 4px;">
                    <button class="btn-buy" style="padding: 3px 6px; font-size: 10px; border-radius: 4px;" onclick="Game.buyBlacksmithSupply('wood', 5, 75)">+5 (75G)</button>
                </div>
            </div>
        </div>
    `;
    list.appendChild(supplyContainer);

    // 2. Weapon & Armor Forge Recipes
    Object.values(FORGE_RECIPES).forEach(recipe => {
        const card = document.createElement('div');
        card.className = 'forge-card';

        const img = document.createElement('img');
        img.src = SPRITES.getItemDataURL(recipe.id);
        img.className = 'forge-item-icon';

        const info = document.createElement('div');
        info.className = 'forge-card-info';

        let matHtml = '';
        let canForge = true;

        for (let [matId, reqQty] of Object.entries(recipe.materials)) {
            const hasQty = this.countItemInInventory(matId);
            const matName = (WORLD_ITEMS && WORLD_ITEMS[matId]?.name) || matId;
            const ok = hasQty >= reqQty;
            if (!ok) canForge = false;
            matHtml += `<span class="${ok ? 'ing-ok' : 'ing-missing'}">${matName}: ${hasQty}/${reqQty}</span> `;
        }

        const cost = recipe.cost ?? recipe.goldCost ?? 0;
        if (this.player.gold < cost) canForge = false;
        const goldOk = this.player.gold >= cost;

        const fitsInBag = this.canItemFitInInventory(recipe.id, 1, recipe.materials);
        if (!fitsInBag && canForge) {
            canForge = false;
        }

        info.innerHTML = `
            <h4>${recipe.name}</h4>
            <p>${recipe.desc}</p>
            <div class="forge-mats">${matHtml}</div>
            <div class="price-tag ${goldOk ? 'ing-ok' : 'ing-missing'}">ค่าตีเหล็ก: ${cost} G (มี ${this.player.gold} G)</div>
        `;

        const btn = document.createElement('button');
        btn.className = 'btn-forge' + (!canForge ? ' disabled' : '');
        if (!fitsInBag) {
            btn.textContent = 'กระเป๋าเต็ม';
            btn.disabled = true;
            btn.title = 'กระเป๋าเต็ม! จัดช่องเก็บของหรือใส่กล่องก่อนตีอาวุธ';
        } else {
            btn.textContent = canForge ? 'ตีขึ้นรูป' : 'วัตถุดิบไม่พอ';
            btn.disabled = !canForge;
        }
        btn.onclick = () => this.forgeItem(recipe.id);

        card.appendChild(img);
        card.appendChild(info);
        card.appendChild(btn);
        list.appendChild(card);
    });
};


Game.forgeItem = function(recipeId) {
    const recipe = FORGE_RECIPES[recipeId];
    if (!recipe) return;

    const fitsInBag = this.canItemFitInInventory(recipe.id, 1, recipe.materials);
    if (!fitsInBag) {
        SoundEngine.hit();
        this.addFloatingText('กระเป๋าเต็มแล้ว! จัดช่องเก็บของหรือใส่กล่องก่อนตีอาวุธ', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }

    const cost = recipe.cost ?? recipe.goldCost ?? 0;
    if (this.player.gold < cost) {
        this.addFloatingText('เหรียญทองไม่เพียงพอ!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }

    for (let [matId, reqQty] of Object.entries(recipe.materials)) {
        if (this.countItemInInventory(matId) < reqQty) {
            this.addFloatingText('วัตถุดิบไม่ครบถ้วน!', this.player.x, this.player.y - 15, '#ef4444');
            return;
        }
    }

    // Deduct
    this.player.gold -= cost;
    for (let [matId, reqQty] of Object.entries(recipe.materials)) {
        this.removeItemFromInventory(matId, reqQty);
    }

    SoundEngine.craft();
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#f59e0b', 20);
    this.addItemToInventory(recipe.id, 1, recipe.name);
    this.addFloatingText(' ตี ' + recipe.name + ' สำเร็จแล้ว!', this.player.x - 20, this.player.y - 25, '#4ade80');
    this.updateHUD();
    this.renderForgeModal();
};


// ========================================================
// TAVERN BOUNTY BOARD (กระดานประกาศล่าค่าหัวมหาบอส)
// ========================================================

Game.openBountyBoard = function() {
    this.closeAllModals();
    this.activeModal = 'bountyBoardModal';
    this.renderBountyBoard();
    const modal = document.getElementById('bountyBoardModal');
    if (modal) modal.style.display = 'flex';
    if (SoundEngine.bell) SoundEngine.bell();
};

Game.renderBountyBoard = function() {
    const list = document.getElementById('bountyList');
    if (!list) return;
    list.innerHTML = '';

    if (!this.player.claimedBounties) this.player.claimedBounties = {};
    if (!this.player.defeatedBosses) this.player.defeatedBosses = {};

    Object.values(BOUNTY_BOARD).forEach((bounty: any) => {
        const isDefeated = !!(this.player.defeatedBosses && this.player.defeatedBosses[bounty.bossId]) ||
            (bounty.bossId === 'boss_kathuros' && !!this.player.questProgress?.kathurosDefeated) ||
            (bounty.bossId === 'boss_luminarch' && !!this.player.questProgress?.luminarchDefeated) ||
            (bounty.bossId === 'boss_hydrakis' && !!this.player.questProgress?.hydrakisDefeated) ||
            (bounty.bossId === 'boss_ignistron' && !!this.player.questProgress?.ignistronDefeated) ||
            (bounty.bossId === 'boss_frostfang' && !!this.player.questProgress?.frostfangDefeated) ||
            (bounty.bossId === 'boss_malakor' && !!this.player.questProgress?.malakorDefeated);

        const isClaimed = !!this.player.claimedBounties[bounty.id];

        const card = document.createElement('div');
        let cardClass = 'bounty-card';
        if (isClaimed) cardClass += ' bounty-claimed';
        else if (isDefeated) cardClass += ' bounty-ready';
        card.className = cardClass;

        let statusBadge = '';
        if (isClaimed) {
            statusBadge = '<span class="bounty-status-badge claimed">✓ รับรางวัลแล้ว</span>';
        } else if (isDefeated) {
            statusBadge = '<span class="bounty-status-badge ready">[สำเร็จ] ปราบสำเร็จ! พร้อมรับรางวัล</span>';
        } else {
            statusBadge = '<span class="bounty-status-badge wanted">[WANTED] กำลังออกอาละวาด</span>';
        }

        const itemName = bounty.rewardItemName || (WORLD_ITEMS[bounty.rewardItem]?.name) || bounty.rewardItem;
        const itemIcon = SPRITES.getItemDataURL ? SPRITES.getItemDataURL(bounty.rewardItem) : '';

        card.innerHTML = `
            <div class="bounty-header">
                <div>
                    <span style="font-size: 11px; font-weight: 700; color: #b45309;">${bounty.location}</span>
                    <h3 style="margin-top: 2px;">${bounty.title}</h3>
                </div>
                ${statusBadge}
            </div>
            <p class="bounty-desc">${bounty.desc}</p>
            <div class="bounty-weakness"><strong>กลยุทธ์ / จุดอ่อน:</strong> ${bounty.weakness}</div>
            <div class="bounty-rewards-row">
                <div class="bounty-rewards">
                    <span>${bounty.rewardGold} G</span>
                    <span>⭐ ${bounty.rewardXp} XP</span>
                    <span style="display: inline-flex; align-items: center; gap: 4px;">
                        ${itemIcon ? `<img src="${itemIcon}" style="width: 18px; height: 18px; image-rendering: pixelated; vertical-align: middle;">` : '[รางวัล]'}
                        ${itemName}
                    </span>
                </div>
                <div class="bounty-actions" id="actions_${bounty.id}"></div>
            </div>
        `;

        const actionsEl = card.querySelector(`#actions_${bounty.id}`);
        if (actionsEl) {
            if (isDefeated && !isClaimed) {
                const claimBtn = document.createElement('button');
                claimBtn.className = 'btn-claim-bounty';
                claimBtn.textContent = 'รับค่าหัว & วัตถุดิบ';
                claimBtn.onclick = () => this.claimBounty(bounty.id);
                actionsEl.appendChild(claimBtn);
            }

            const travelBtn = document.createElement('button');
            travelBtn.className = 'btn-travel-bounty';
            travelBtn.textContent = 'เดินทางล่า';
            travelBtn.onclick = () => this.travelToBounty(bounty.scene);
            actionsEl.appendChild(travelBtn);
        }

        list.appendChild(card);
    });
};

Game.claimBounty = function(bountyId: string) {
    const bounty = BOUNTY_BOARD[bountyId];
    if (!bounty) return;

    if (!this.player.claimedBounties) this.player.claimedBounties = {};
    if (this.player.claimedBounties[bountyId]) {
        this.addFloatingText('คุณรับรางวัลค่าหัวนี้ไปแล้ว!', this.player.x, this.player.y - 15, '#94a3b8');
        return;
    }

    const isDefeated = !!(this.player.defeatedBosses && this.player.defeatedBosses[bounty.bossId]) ||
        (bounty.bossId === 'boss_kathuros' && !!this.player.questProgress?.kathurosDefeated) ||
        (bounty.bossId === 'boss_luminarch' && !!this.player.questProgress?.luminarchDefeated) ||
        (bounty.bossId === 'boss_hydrakis' && !!this.player.questProgress?.hydrakisDefeated) ||
        (bounty.bossId === 'boss_ignistron' && !!this.player.questProgress?.ignistronDefeated) ||
        (bounty.bossId === 'boss_frostfang' && !!this.player.questProgress?.frostfangDefeated) ||
        (bounty.bossId === 'boss_malakor' && !!this.player.questProgress?.malakorDefeated);

    if (!isDefeated) {
        this.addFloatingText('ยังไม่ได้ปราบมหาบอสตนนี้!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }

    this.player.claimedBounties[bountyId] = true;
    this.player.gold += bounty.rewardGold;
    this.addXp(bounty.rewardXp);

    const itemName = bounty.rewardItemName || (WORLD_ITEMS[bounty.rewardItem]?.name) || bounty.rewardItem;
    this.addItemToInventory(bounty.rewardItem, 1, itemName);

    if (SoundEngine.bossVictoryFanfare) SoundEngine.bossVictoryFanfare();
    else if (SoundEngine.levelUp) SoundEngine.levelUp();
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#facc15', 30);
    this.addFloatingText(` รับค่าหัว ${bounty.rewardGold}G & ${itemName}!`, this.player.x - 30, this.player.y - 25, '#4ade80');
    this.updateHUD();
    this.renderBountyBoard();
};

Game.travelToBounty = function(scene: string) {
    const spawns: Record<string, {x: number, y: number, name: string}> = {
        forest: { x: 24, y: 34, name: 'ป่าเอลเดอร์วู้ด & ดงสปอร์' },
        cave_depths: { x: 22, y: 28, name: 'ถ้ำห้วงลึกใต้พิภพ' },
        swamp: { x: 24, y: 28, name: 'บึงมรณะกลูมสแวมป์' },
        volcano: { x: 24, y: 28, name: 'ภูเขาไฟอิกนิส' },
        frost_peak: { x: 24, y: 30, name: 'ยอดเขาเหมันต์นิรันดร์' },
        crypt: { x: 23, y: 28, name: 'สุสานโบราณใต้พิภพ' }
    };

    const target = spawns[scene] || { x: 17, y: 12, name: 'ดินแดนลึกลับ' };
    this.closeAllModals();
    if (SoundEngine.warpSound) SoundEngine.warpSound();
    else if (SoundEngine.bell) SoundEngine.bell();
    this.switchScene(scene, target.x, target.y);
    this.addFloatingText(' ออกเดินทางสู่ ' + target.name + '!', this.player.x, this.player.y - 25, '#fde047');
};


Game.drawCampfireFlame = function(screenX, screenY) {
    this.ctx.fillStyle = '#f97316';
    const flicker = Math.sin(performance.now() / 120) * 3;
    this.ctx.beginPath();
    this.ctx.arc(screenX + 16, screenY + 14, 6 + flicker, 0, Math.PI * 2);
    this.ctx.fill();
    this.ctx.fillStyle = '#fde047';
    this.ctx.beginPath();
    this.ctx.arc(screenX + 16, screenY + 14, 3 + flicker * 0.5, 0, Math.PI * 2);
    this.ctx.fill();
};


Game.drawSingleWorldMonster = function(m) {
    const mx = Math.round(m.x - this.camera.x);
    const my = Math.round(m.y - this.camera.y);

    // Grounding Contact Shadow
    this.ctx.fillStyle = 'rgba(15, 23, 42, 0.3)';
    this.ctx.beginPath();
    this.ctx.ellipse(mx + 16, my + 28, 11, 4.5, 0, 0, Math.PI * 2);
    this.ctx.fill();

    const frames = SPRITES.worldMonsters[m.type];
    if (frames) {
        const spr = frames[m.frame] || frames[0];
        // Fast hardware-accelerated hit flash (Zero ctx.filter GPU stall!)
        const sx = m.squashX || 1.0;
        const sy = m.squashY || 1.0;
        const hasSquash = (sx !== 1.0 || sy !== 1.0);

        if (hasSquash) {
            this.ctx.save();
            this.ctx.translate(mx + 16, my + 16);
            this.ctx.scale(sx, sy);
            this.ctx.translate(-(mx + 16), -(my + 16));
        }

        this.ctx.drawImage(spr, mx, my);

        if (m.flashTimer > 0) {
            this.ctx.save();
            this.ctx.globalCompositeOperation = 'lighter';
            this.ctx.globalAlpha = Math.min(0.85, m.flashTimer / 100);
            this.ctx.drawImage(spr, mx, my);
            this.ctx.restore();
        }

        if (hasSquash) {
            this.ctx.restore();
        }
    }

    // Health bar
    const barW = 30;
    const barH = 4;
    const hpPct = Math.max(0, m.hp / m.maxHp);
    this.ctx.fillStyle = '#0f172a';
    this.ctx.fillRect(mx + 1, my - 8, barW, barH);
    this.ctx.fillStyle = hpPct > 0.4 ? '#22c55e' : '#ef4444';
    this.ctx.fillRect(mx + 1, my - 8, Math.round(barW * hpPct), barH);

    // Name tag
    const cfg = WORLD_MONSTERS[m.type];
    const mName = cfg ? (cfg.shortName || cfg.name.split(' (')[0]) : m.type;
    this.ctx.fillStyle = '#f8fafc';
    this.ctx.font = 'bold 8px "Prompt", sans-serif';
    this.ctx.fillText(mName, mx - 2, my - 11);
};


Game.drawBoss = function() {
    if (!this.boss || !this.boss.alive) return;
    const bx = Math.round(this.boss.x - this.camera.x);
    const by = Math.round(this.boss.y - this.camera.y);

    // 1. Dynamic Demonic Aura (Phase & Boss-based coloring & pulsation)
    this.ctx.save();
    const pulse = (Math.sin(performance.now() / 180) + 1) * 0.5;
    const auraRad = 44 + pulse * 14;
    const grad = this.ctx.createRadialGradient(bx + 32, by + 32, 10, bx + 32, by + 32, auraRad);

    if (this.boss.id === 'boss_luminarch') {
        grad.addColorStop(0, this.boss.phase === 3 ? 'rgba(6, 182, 212, 0.6)' : 'rgba(6, 182, 212, 0.38)');
        grad.addColorStop(0.5, 'rgba(168, 85, 247, 0.22)');
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    } else if (this.boss.id === 'boss_hydrakis') {
        grad.addColorStop(0, this.boss.phase === 3 ? 'rgba(34, 197, 94, 0.6)' : 'rgba(34, 197, 94, 0.38)');
        grad.addColorStop(0.5, 'rgba(234, 179, 8, 0.22)');
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    } else if (this.boss.id === 'boss_ignistron') {
        grad.addColorStop(0, this.boss.phase === 3 ? 'rgba(234, 88, 12, 0.65)' : 'rgba(234, 88, 12, 0.42)');
        grad.addColorStop(0.5, 'rgba(250, 204, 21, 0.28)');
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    } else if (this.boss.id === 'boss_frostfang') {
        grad.addColorStop(0, this.boss.phase === 3 ? 'rgba(56, 189, 248, 0.6)' : 'rgba(56, 189, 248, 0.38)');
        grad.addColorStop(0.5, 'rgba(224, 242, 254, 0.25)');
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    } else if (this.boss.id === 'boss_malakor') {
        grad.addColorStop(0, this.boss.phase === 3 ? 'rgba(147, 51, 234, 0.65)' : 'rgba(147, 51, 234, 0.42)');
        grad.addColorStop(0.5, 'rgba(220, 38, 38, 0.25)');
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    } else if (this.boss.id === 'boss_sylvanus') {
        grad.addColorStop(0, this.boss.phase === 3 ? 'rgba(34, 197, 94, 0.65)' : 'rgba(34, 197, 94, 0.42)');
        grad.addColorStop(0.5, 'rgba(74, 222, 128, 0.28)');
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    } else if (this.boss.id === 'boss_astreon') {
        grad.addColorStop(0, this.boss.phase === 3 ? 'rgba(234, 179, 8, 0.65)' : 'rgba(234, 179, 8, 0.42)');
        grad.addColorStop(0.5, 'rgba(56, 189, 248, 0.3)');
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    } else if (this.boss.id === 'boss_karzarak') {
        grad.addColorStop(0, this.boss.phase === 3 ? 'rgba(239, 68, 68, 0.7)' : 'rgba(239, 68, 68, 0.45)');
        grad.addColorStop(0.5, 'rgba(249, 115, 22, 0.35)');
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    } else {
        if (this.boss.phase === 3) {
            grad.addColorStop(0, 'rgba(239, 68, 68, 0.45)');
            grad.addColorStop(0.5, 'rgba(234, 88, 12, 0.25)');
            grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        } else if (this.boss.phase === 2) {
            grad.addColorStop(0, 'rgba(168, 85, 247, 0.4)');
            grad.addColorStop(0.5, 'rgba(220, 38, 38, 0.2)');
            grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        } else {
            grad.addColorStop(0, 'rgba(185, 28, 28, 0.35)');
            grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        }
    }

    this.ctx.fillStyle = grad;
    this.ctx.beginPath();
    this.ctx.arc(bx + 32, by + 32, auraRad, 0, Math.PI * 2);
    this.ctx.fill();

    // Grounding Contact Shadow
    this.drawContactShadow(this.boss.x + 32, this.boss.y + 60, 28, 10, 0.4);

    // Electric / Energy sparks for Phase 2 & 3
    if (this.boss.phase >= 2 && Math.random() < 0.45) {
        this.ctx.strokeStyle = (this.boss.phase === 3) ? '#fde047' : '#c084fc';
        this.ctx.lineWidth = 1.5;
        this.ctx.beginPath();
        const startX = bx + 16 + Math.random() * 32;
        const startY = by + 16 + Math.random() * 32;
        this.ctx.moveTo(startX, startY);
        this.ctx.lineTo(startX + (Math.random() - 0.5) * 16, startY + (Math.random() - 0.5) * 16);
        this.ctx.stroke();
    }

    // Boss Sprite with Flash (Zero ctx.filter GPU stall & Dynamic Squash Bounce)
    const bossSprites = (SPRITES.bosses && SPRITES.bosses[this.boss.id]) || SPRITES.bossKathuros;
    const spr = (bossSprites && bossSprites[this.boss.frame]) || bossSprites[0] || SPRITES.bossKathuros[0];
    if (spr) {
        const bSquashX = this.boss.squashX || 1.0;
        const bSquashY = this.boss.squashY || 1.0;
        const hasSquash = (bSquashX !== 1.0 || bSquashY !== 1.0);

        if (hasSquash) {
            this.ctx.save();
            this.ctx.translate(bx + 32, by + 32);
            this.ctx.scale(bSquashX, bSquashY);
            this.ctx.translate(-(bx + 32), -(by + 32));
        }

        this.ctx.drawImage(spr, bx, by);

        if (this.boss.flashTimer > 0) {
            this.ctx.save();
            this.ctx.globalCompositeOperation = 'lighter';
            this.ctx.globalAlpha = Math.min(0.85, this.boss.flashTimer / 100);
            this.ctx.drawImage(spr, bx, by);
            this.ctx.restore();
        }

        if (hasSquash) {
            this.ctx.restore();
        }
    }

    // Phase 3 Enraged Flaming Crown
    if (this.boss.phase === 3) {
        const crownFlicker = Math.sin(performance.now() / 80) * 2;
        this.ctx.fillStyle = '#facc15';
        this.ctx.beginPath();
        this.ctx.moveTo(bx + 26, by + 4);
        this.ctx.lineTo(bx + 28, by - 4 + crownFlicker);
        this.ctx.lineTo(bx + 32, by + 2);
        this.ctx.lineTo(bx + 36, by - 4 + crownFlicker);
        this.ctx.lineTo(bx + 38, by + 4);
        this.ctx.fill();
        this.ctx.fillStyle = '#ef4444';
        this.ctx.fillRect(bx + 31, by + 2, 2, 2);
    }

    // Overhead Boss Health Bar (directly above boss sprite for immediate combat read)
    const barW = 64;
    const barH = 5;
    const barX = bx + 32 - barW / 2;
    const barY = by - 16;
    this.ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    this.ctx.fillRect(barX - 1, barY - 1, barW + 2, barH + 2);
    this.ctx.strokeStyle = '#475569';
    this.ctx.lineWidth = 1;
    this.ctx.strokeRect(barX - 1, barY - 1, barW + 2, barH + 2);

    const hpRatio = Math.max(0, Math.min(1, this.boss.hp / this.boss.maxHp));
    const barFillCol = this.boss.phase === 3 ? '#ef4444' : (this.boss.phase === 2 ? '#a855f7' : '#e11d48');
    this.ctx.fillStyle = barFillCol;
    this.ctx.fillRect(barX, barY, Math.round(barW * hpRatio), barH);

    // Boss overhead tag
    const bossLabels: Record<string, string> = {
        boss_kathuros: 'ราชินีสปอร์ คาธูรอส',
        boss_luminarch: 'โกเลมผลึก ลูมินาร์ค',
        boss_hydrakis: 'พญาไฮดรา ไฮดราคิส',
        boss_ignistron: 'มังกรลาวา อิกนิสทรอน',
        boss_frostfang: 'ไททันน้ำแข็ง ฟรอสต์แฟงก์',
        boss_malakor: 'ลอร์ดมรณะ มาลาคอร์',
        boss_sylvanus: 'เทพพฤกษา ซิลวาเนีย',
        boss_astreon: 'จ้าวพายุสายฟ้า ออสทริออน',
        boss_karzarak: 'จอมมารลาวา คาร์ซารัค'
    };

    const bName = bossLabels[this.boss.id] || this.boss.name || 'บอสแห่งดินแดน';
    const badge = this.boss.phase === 3 ? `${bName} (คลั่งขั้นสุด)` : (this.boss.phase === 2 ? `${bName} (เฟส 2)` : bName);
    this.ctx.fillStyle = this.boss.phase === 3 ? '#fde047' : (this.boss.phase === 2 ? '#c084fc' : '#fca5a5');
    this.ctx.font = 'bold 9px "Prompt", sans-serif';
    this.ctx.textAlign = 'center';
    this.ctx.fillText(badge, bx + 32, by - 20);
    this.ctx.textAlign = 'start';
    this.ctx.restore();
};


Game.queueVillageEntities = function(renderables) {
    // 1. Mayor's Manor at (8, 6)
    renderables.push({
        depthY: 6 * 32 + 76,
        render: () => {
            this.drawContactShadow(8 * 32 + 48, 6 * 32 + 76, 46, 10, 0.35);
            this.ctx.drawImage(SPRITES.manor, Math.round(8 * 32 - this.camera.x), Math.round(6 * 32 - this.camera.y));
        }
    });

    // 2. Apothecary Clinic at (46, 6)
    renderables.push({
        depthY: 6 * 32 + 76,
        render: () => {
            this.drawContactShadow(46 * 32 + 48, 6 * 32 + 76, 46, 10, 0.35);
            this.ctx.drawImage(SPRITES.apothecary, Math.round(46 * 32 - this.camera.x), Math.round(6 * 32 - this.camera.y));
        }
    });

    // 3. Blacksmith Forge at (8, 25)
    renderables.push({
        depthY: 25 * 32 + 76,
        render: () => {
            this.drawContactShadow(8 * 32 + 48, 25 * 32 + 76, 46, 10, 0.35);
            this.ctx.drawImage(SPRITES.villageForge, Math.round(8 * 32 - this.camera.x), Math.round(25 * 32 - this.camera.y));
        }
    });

    // 4. Tavern at (46, 25)
    renderables.push({
        depthY: 25 * 32 + 76,
        render: () => {
            this.drawContactShadow(46 * 32 + 48, 25 * 32 + 76, 46, 10, 0.35);
            this.ctx.drawImage(SPRITES.tavern, Math.round(46 * 32 - this.camera.x), Math.round(25 * 32 - this.camera.y));
        }
    });

    // 5. Grand Central Fountain at (29, 19)
    renderables.push({
        depthY: 19 * 32 + 58,
        render: () => {
            this.drawContactShadow(29 * 32 + 32, 19 * 32 + 56, 30, 10, 0.32);
            this.ctx.drawImage(SPRITES.villageFountain, Math.round(29 * 32 - this.camera.x), Math.round(19 * 32 - this.camera.y));
        }
    });

    // 6. Story NPCs in Village
    // Gilbert at (12, 10)
    renderables.push({
        depthY: 10 * 32 + 30,
        render: () => {
            const gx = Math.round(12 * 32 - this.camera.x);
            const gy = Math.round(10 * 32 - this.camera.y);
            this.drawContactShadow(12 * 32 + 12, 10 * 32 + 30, 8, 4, 0.28);
            const gFrame = SPRITES.storyNpcs.gilbert?.down[Math.floor(performance.now() / 400) % 2];
            if (gFrame) this.ctx.drawImage(gFrame, gx, gy);
            this.ctx.fillStyle = '#60a5fa';
            this.ctx.font = 'bold 9px "Prompt", sans-serif';
            this.ctx.fillText('นายกฯ กิลเบิร์ต', gx - 16, gy - 6);
        }
    });

    // Lilian at (45, 10)
    renderables.push({
        depthY: 10 * 32 + 30,
        render: () => {
            const lx = Math.round(45 * 32 - this.camera.x);
            const ly = Math.round(10 * 32 - this.camera.y);
            this.drawContactShadow(45 * 32 + 12, 10 * 32 + 30, 8, 4, 0.28);
            const lFrame = SPRITES.storyNpcs.lilian?.down[Math.floor(performance.now() / 400) % 2];
            if (lFrame) this.ctx.drawImage(lFrame, lx, ly);
            this.ctx.fillStyle = '#4ade80';
            this.ctx.font = 'bold 9px "Prompt", sans-serif';
            this.ctx.fillText('หมอยา ลิเลียน', lx - 14, ly - 6);
        }
    });

    // Bob at (45, 29)
    renderables.push({
        depthY: 29 * 32 + 30,
        render: () => {
            const bx = Math.round(45 * 32 - this.camera.x);
            const by = Math.round(29 * 32 - this.camera.y);
            this.drawContactShadow(45 * 32 + 12, 29 * 32 + 30, 8, 4, 0.28);
            const bFrame = SPRITES.storyNpcs.bob?.down[Math.floor(performance.now() / 400) % 2];
            if (bFrame) this.ctx.drawImage(bFrame, bx, by);
            this.ctx.fillStyle = '#fbbf24';
            this.ctx.font = 'bold 9px "Prompt", sans-serif';
            this.ctx.fillText('บ็อบ (โรงเตี๊ยม)', bx - 14, by - 6);
        }
    });

    // Valeria at North Barricade Gate (27, 4)
    renderables.push({
        depthY: 4 * 32 + 30,
        render: () => {
            const vx = Math.round(27 * 32 - this.camera.x);
            const vy = Math.round(4 * 32 - this.camera.y);
            this.drawContactShadow(27 * 32 + 12, 4 * 32 + 30, 8, 4, 0.28);
            const vFrame = SPRITES.storyNpcs.valeria?.down[Math.floor(performance.now() / 400) % 2];
            if (vFrame) this.ctx.drawImage(vFrame, vx, vy);
            this.ctx.fillStyle = '#f87171';
            this.ctx.font = 'bold 9px "Prompt", sans-serif';
            this.ctx.fillText('ผู้กองวาเลเรีย', vx - 14, vy - 6);
        }
    });

    // Kael at Forge (12, 29)
    renderables.push({
        depthY: 29 * 32 + 30,
        render: () => {
            const kx = Math.round(12 * 32 - this.camera.x);
            const ky = Math.round(29 * 32 - this.camera.y);
            this.drawContactShadow(12 * 32 + 12, 29 * 32 + 30, 8, 4, 0.28);
            const kFrame = SPRITES.storyNpcs.kael?.down[Math.floor(performance.now() / 400) % 2];
            if (kFrame) this.ctx.drawImage(kFrame, kx, ky);
            this.ctx.fillStyle = '#fb923c';
            this.ctx.font = 'bold 9px "Prompt", sans-serif';
            this.ctx.fillText('ช่างตีเหล็ก คาเอล', kx - 16, ky - 6);
        }
    });

    // Eldrin at Sanctuary (23, 12)
    renderables.push({
        depthY: 12 * 32 + 30,
        render: () => {
            const ex = Math.round(23 * 32 - this.camera.x);
            const ey = Math.round(12 * 32 - this.camera.y);
            this.drawContactShadow(23 * 32 + 12, 12 * 32 + 30, 8, 4, 0.28);
            const eFrame = SPRITES.storyNpcs.eldrin?.down[Math.floor(performance.now() / 400) % 2];
            if (eFrame) this.ctx.drawImage(eFrame, ex, ey);
            this.ctx.fillStyle = '#c084fc';
            this.ctx.font = 'bold 9px "Prompt", sans-serif';
            this.ctx.fillText('ผู้เฒ่าเอลดริน', ex - 12, ey - 6);
        }
    });

    // 7. Dynamic Wandering Townspeople (ชาวบ้านเดินขวักไขว่)
    if (this.villageVillagers && this.villageVillagers.length > 0) {
        this.villageVillagers.forEach(v => {
            renderables.push({
                depthY: v.y + 30,
                render: () => this.drawSingleVillager(v)
            });
        });
    }
};


Game.drawVillageEntities = function() {
    const list = [];
    this.queueVillageEntities(list);
    list.forEach(item => item.render());
};


Game.initVillageVillagers = function() {
    this.villageVillagers = [
        {
            id: 'v_somchai',
            name: 'ลุงสมชาย (คนสวนเฒ่า)',
            type: 'uncle',
            x: 24 * 32, y: 17 * 32,
            minX: 18 * 32, maxX: 30 * 32,
            minY: 15 * 32, maxY: 23 * 32,
            direction: 'down',
            state: 'idle',
            timer: 2000,
            speed: 0.9,
            frame: 0,
            bubbleText: null,
            bubbleTimer: 0,
            phrases: [
                'โอ้ สหายชาวสวนรุ่นเยาว์! พืชผลในไร่สุขใจโตงามดีไหม?',
                'ระวังพวกแมลงยักษ์แถวชายป่านะ ยุคนี้มันดุร้ายผิดปกติ!',
                'ลานน้ำพุตรงกลางเมืองนั่งพักแล้วเย็นชื่นใจจริงๆ'
            ]
        },
        {
            id: 'v_somsri',
            name: 'ป้าสมศรี (แม่ค้าดอกไม้)',
            type: 'auntie',
            x: 32 * 32, y: 18 * 32,
            minX: 27 * 32, maxX: 37 * 32,
            minY: 16 * 32, maxY: 24 * 32,
            direction: 'left',
            state: 'idle',
            timer: 1800,
            speed: 0.9,
            frame: 0,
            bubbleText: null,
            bubbleTimer: 0,
            phrases: [
                'ดอกไม้ดวงดาว (Starflower) ในสวนลิเลียนคืนนี้เรืองแสงสวยมากจ้ะ',
                'ขอให้แผ่นดินศิลาสุขาวดีกลับมาสงบสุขในเร็ววันนะ',
                'เจ้าดื่มน้ำจากน้ำพุหรือยัง? หายเหนื่อยเป็นปลิดทิ้งเลยล่ะ'
            ]
        },
        {
            id: 'v_paeng',
            name: 'น้องแป้ง (เด็กน้อยร่าเริง)',
            type: 'girl',
            x: 30 * 32, y: 22 * 32,
            minX: 24 * 32, maxX: 36 * 32,
            minY: 16 * 32, maxY: 25 * 32,
            direction: 'up',
            state: 'walking',
            timer: 2500,
            speed: 1.4,
            frame: 0,
            bubbleText: null,
            bubbleTimer: 0,
            phrases: [
                'เย้ๆ! พี่คนสวนพาไปจับผีเสื้อหน่อยสิ!',
                'ข้าชอบวิ่งรอบน้ำพุที่สุดเลย!',
                'พี่คนสวนมีผลไม้หวานๆ จากไร่มาแบ่งหนูไหมคะ?'
            ]
        },
        {
            id: 'v_tony',
            name: 'เชฟโทนี่ (พ่อครัวพเนจร)',
            type: 'chef',
            x: 38 * 32, y: 26 * 32,
            minX: 32 * 32, maxX: 46 * 32,
            minY: 22 * 32, maxY: 29 * 32,
            direction: 'right',
            state: 'idle',
            timer: 3000,
            speed: 1.0,
            frame: 0,
            bubbleText: null,
            bubbleTimer: 0,
            phrases: [
                'ห้ามเอาเห็ดม่วงจากป่ามาทำซุปเด็ดขาด! มีพิษสปอร์อันตรายมาก',
                'ปลาย่างสมุนไพรของบ็อบที่โรงเตี๊ยมจานละ 30 G คุ้มค่าสุดๆ',
                'ถ้าเจ้ามีข้าวโพดกับมันฝรั่ง นำมาทำสลัดเพื่อสุขภาพได้นะ'
            ]
        },
        {
            id: 'v_mana',
            name: 'มานะ (หนุ่มส่งของ)',
            type: 'boy',
            x: 20 * 32, y: 11 * 32,
            minX: 14 * 32, maxX: 46 * 32,
            minY: 10 * 32, maxY: 14 * 32,
            direction: 'right',
            state: 'walking',
            timer: 3200,
            speed: 1.5,
            frame: 0,
            bubbleText: null,
            bubbleTimer: 0,
            phrases: [
                'จดหมายเตือนภัยและเสบียงยาต้องส่งให้ถึงมือทุกหลังคาเรือน!',
                'ท่านกิลเบิร์ตกำลังเร่งประสานงานกับนายพรานทั่วมณฑล',
                'ขอตัวก่อนนะ ข้าต้องรีบวิ่งไปส่งของต่อแล้ว!'
            ]
        },
        {
            id: 'v_methee',
            name: 'คุณปู่เมธี (ปราชญ์ท้องถิ่น)',
            type: 'grandpa',
            x: 22 * 32, y: 19 * 32,
            minX: 18 * 32, maxX: 26 * 32,
            minY: 16 * 32, maxY: 22 * 32,
            direction: 'right',
            state: 'idle',
            timer: 4000,
            speed: 0.8,
            frame: 0,
            bubbleText: null,
            bubbleTimer: 0,
            phrases: [
                'ศิลาสุขาวดีตั้งตระหง่านมานับศตวรรษ... เราจะผ่านวิกฤตสปอร์นี้ไปด้วยกัน',
                'จงศึกษาธรรมชาติให้ถ่องแท้ พืชสมุนไพรคือเกราะป้องกันที่ดีที่สุด',
                'อย่าลืมแวะไปกราบไหว้รูปปั้นโบราณที่ศาลานักปราชญ์เอลดรินนะ'
            ]
        },
        {
            id: 'v_marina',
            name: 'แม่ค้ามารีน่า (พ่อค้าเร่)',
            type: 'merchant',
            x: 28 * 32, y: 28 * 32,
            minX: 25 * 32, maxX: 35 * 32,
            minY: 26 * 32, maxY: 38 * 32,
            direction: 'up',
            state: 'idle',
            timer: 2200,
            speed: 1.1,
            frame: 0,
            bubbleText: null,
            bubbleTimer: 0,
            phrases: [
                'สินค้าจากต่างแดนเริ่มขาดแคลนเพราะถนนทางเหนือถูกปิดกั้น',
                'แร่ทับทิมและอัญมณีจากถ้ำใต้พิภพมีค่ามาก ช่างตีเหล็กคาเอลรับซื้อไม่อั้น',
                'ถ้าต้องการอาวุธดีๆ อย่าลืมแวะโรงตีเหล็กทางทิศตะวันตกเฉียงใต้นะ'
            ]
        },
        {
            id: 'v_meena',
            name: 'หนูน้อยมีนา (สาวน้อยไล่จับผีเสื้อ)',
            type: 'girl',
            x: 44 * 32, y: 14 * 32,
            minX: 40 * 32, maxX: 48 * 32,
            minY: 10 * 32, maxY: 18 * 32,
            direction: 'down',
            state: 'walking',
            timer: 2200,
            speed: 1.3,
            frame: 0,
            bubbleText: null,
            bubbleTimer: 0,
            phrases: [
                'หมอยาลิเลียนใจดีมาก สอนหนูจำแนกดอกไม้มีพิษด้วย!',
                'เมื่อกี้หนูเห็นผีเสื้อปีกสีรุ้งบินผ่านไปทางบ่อน้ำพุด้วยล่ะ!',
                'อยากให้ฟาร์มสุขใจเปิดสวนให้น้องๆ เข้าไปวิ่งเล่นจัง'
            ]
        }
    ];
};


Game.updateVillageVillagers = function(dt) {
    if (this.currentScene !== 'village' || !this.villageVillagers) return;

    this.ambientVillagerChatTimer = (this.ambientVillagerChatTimer || 0) + dt;
    if (this.ambientVillagerChatTimer > 7500) {
        this.ambientVillagerChatTimer = 0;
        const randomV = this.villageVillagers[Math.floor(Math.random() * this.villageVillagers.length)];
        if (randomV && randomV.phrases) {
            randomV.bubbleText = randomV.phrases[Math.floor(Math.random() * randomV.phrases.length)];
            randomV.bubbleTimer = 3500;
        }
    }

    this.villageVillagers.forEach(v => {
        if (v.bubbleTimer && v.bubbleTimer > 0) {
            v.bubbleTimer -= dt;
            if (v.bubbleTimer <= 0) v.bubbleText = null;
        }

        v.timer -= dt;
        if (v.timer <= 0) {
            v.timer = 2000 + Math.random() * 3000;
            if (Math.random() < 0.65) {
                v.state = 'walking';
                const dirs = ['up', 'down', 'left', 'right'];
                v.direction = dirs[Math.floor(Math.random() * dirs.length)];
            } else {
                v.state = 'idle';
                v.frame = 0;
            }
        }

        if (v.state === 'walking') {
            let dx = 0;
            let dy = 0;
            if (v.direction === 'left') dx = -v.speed;
            else if (v.direction === 'right') dx = v.speed;
            else if (v.direction === 'up') dy = -v.speed;
            else if (v.direction === 'down') dy = v.speed;

            const nextX = v.x + dx;
            const nextY = v.y + dy;

            // Check bounding box
            const insideBounds = (nextX >= v.minX && nextX <= v.maxX && nextY >= v.minY && nextY <= v.maxY);

            // Check tile collision in village
            const tileX = Math.floor((nextX + 12) / 32);
            const tileY = Math.floor((nextY + 24) / 32);
            const isWalkable = this.map && this.map[tileY] && this.map[tileY][tileX] && !this.map[tileY][tileX].solid;

            if (insideBounds && isWalkable) {
                v.x = nextX;
                v.y = nextY;
                v.frame = (Math.floor(performance.now() / 200) % 2);
            } else {
                v.state = 'idle';
                v.timer = 1200 + Math.random() * 1500;
                v.frame = 0;
            }
        }
    });
};


Game.drawSingleVillager = function(v) {
    const vx = Math.round(v.x - this.camera.x);
    const vy = Math.round(v.y - this.camera.y);
    this.drawContactShadow(v.x + 12, v.y + 30, 8, 4, 0.28);
    const frameSet = SPRITES.npcs[v.type] || SPRITES.npcs.uncle;
    const dirFrames = frameSet[v.direction] || frameSet.down;
    const curFrame = dirFrames[v.frame || 0] || dirFrames[0];
    if (curFrame) this.ctx.drawImage(curFrame, vx, vy);

    // Villager name label
    this.ctx.fillStyle = '#fef08a';
    this.ctx.font = 'bold 8px "Prompt", sans-serif';
    this.ctx.textAlign = 'center';
    this.ctx.fillText(v.name, vx + 12, vy - 5);
    this.ctx.textAlign = 'start';

    // Ambient speech bubble if active
    if (v.bubbleText && v.bubbleTimer > 0) {
        this.ctx.font = 'bold 9px "Prompt", sans-serif';
        const txtWidth = this.ctx.measureText(v.bubbleText).width;
        const bw = Math.max(30, txtWidth + 14);
        const bh = 18;
        const bx = vx + 12 - bw / 2;
        const by = vy - 26;

        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
        this.ctx.beginPath();
        this.ctx.roundRect(bx, by, bw, bh, 5);
        this.ctx.fill();
        this.ctx.strokeStyle = '#d97706';
        this.ctx.lineWidth = 1;
        this.ctx.stroke();

        // Pointer triangle
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
        this.ctx.beginPath();
        this.ctx.moveTo(vx + 9, by + bh);
        this.ctx.lineTo(vx + 15, by + bh);
        this.ctx.lineTo(vx + 12, by + bh + 4);
        this.ctx.fill();

        this.ctx.fillStyle = '#451a03';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(v.bubbleText, vx + 12, by + 12);
        this.ctx.textAlign = 'start';
    }
};


Game.talkToVillager = function(v) {
    const dx = this.player.x - v.x;
    const dy = this.player.y - v.y;
    if (Math.abs(dx) > Math.abs(dy)) {
        v.direction = dx > 0 ? 'right' : 'left';
    } else {
        v.direction = dy > 0 ? 'down' : 'up';
    }
    v.state = 'idle';
    v.timer = 4000;

    const quote = v.phrases[Math.floor(Math.random() * v.phrases.length)];
    v.bubbleText = quote;
    v.bubbleTimer = 4500;

    SoundEngine.bell();
    this.spawnParticles(v.x + 12, v.y + 10, '#ec4899', 8);
    this.addFloatingText(' ' + v.name + ': ' + quote, v.x, v.y - 15, '#fef08a');
};


Game.queueForestEntities = function(renderables) {
    // 1. Story NPCs
    // Valeria at (22, 30)
    renderables.push({
        depthY: 30 * 32 + 30,
        render: () => {
            const vx = Math.round(22 * 32 - this.camera.x);
            const vy = Math.round(30 * 32 - this.camera.y);
            this.drawContactShadow(22 * 32 + 12, 30 * 32 + 30, 8, 4, 0.28);
            const valFrame = SPRITES.storyNpcs.valeria.down[Math.floor(performance.now() / 400) % 2];
            if (valFrame) this.ctx.drawImage(valFrame, vx, vy);
            this.ctx.fillStyle = '#60a5fa';
            this.ctx.font = 'bold 9px "Prompt", sans-serif';
            this.ctx.fillText('วาเลเรีย (อัศวิน)', vx - 8, vy - 6);
        }
    });

    // Eldrin at (28, 30)
    renderables.push({
        depthY: 30 * 32 + 30,
        render: () => {
            const ex = Math.round(28 * 32 - this.camera.x);
            const ey = Math.round(30 * 32 - this.camera.y);
            this.drawContactShadow(28 * 32 + 12, 30 * 32 + 30, 8, 4, 0.28);
            const eldFrame = SPRITES.storyNpcs.eldrin.down[Math.floor(performance.now() / 400) % 2];
            if (eldFrame) this.ctx.drawImage(eldFrame, ex, ey);
            this.ctx.fillStyle = '#c084fc';
            this.ctx.font = 'bold 9px "Prompt", sans-serif';
            this.ctx.fillText('ปราชญ์เอลดริน', ex - 6, ey - 6);
        }
    });

    // Kael at (18, 32)
    renderables.push({
        depthY: 32 * 32 + 30,
        render: () => {
            const kx = Math.round(18 * 32 - this.camera.x);
            const ky = Math.round(32 * 32 - this.camera.y);
            this.drawContactShadow(18 * 32 + 12, 32 * 32 + 30, 8, 4, 0.28);
            const kaelFrame = SPRITES.storyNpcs.kael.down[Math.floor(performance.now() / 400) % 2];
            if (kaelFrame) this.ctx.drawImage(kaelFrame, kx, ky);
            this.ctx.fillStyle = '#fb923c';
            this.ctx.font = 'bold 9px "Prompt", sans-serif';
            this.ctx.fillText('ช่างตีเหล็ก คาเอล', kx - 12, ky - 6);
        }
    });

    // 2. World Monsters
    this.worldMonsters.forEach(m => {
        renderables.push({
            depthY: m.y + 28,
            render: () => this.drawSingleWorldMonster(m)
        });
    });

    // 3. Boss Kathuros
    if (this.boss && this.boss.alive) {
        renderables.push({
            depthY: this.boss.y + 60,
            render: () => this.drawBoss()
        });
    }

    // 4. Boss VFX & Ground Indicators (Telegraphs, ground hazards, dash ghosts)
    renderables.push({
        depthY: -99999,
        render: () => {
            this.drawBossGroundHazards();
            this.drawBossTelegraphs();
            this.drawBossDashGhosts();
        }
    });

    // 5. Boss Shockwaves (Impact explosion level, above ground entities)
    renderables.push({
        depthY: 99999,
        render: () => {
            this.drawBossShockwaves();
        }
    });
};

Game.drawBloodstain = function() {
    if (!this.player.bloodstain || this.player.bloodstain.scene !== this.currentScene) return;

    const bs = this.player.bloodstain;
    const sx = Math.round(bs.x - this.camera.x);
    const sy = Math.round(bs.y - this.camera.y);
    const pulse = (Math.sin(performance.now() / 220) + 1) * 0.5;

    this.ctx.save();
    // Glowing radiant soul aura
    const grad = this.ctx.createRadialGradient(sx, sy, 2, sx, sy, 22 + pulse * 6);
    grad.addColorStop(0, `rgba(250, 204, 21, ${0.8 + pulse * 0.2})`);
    grad.addColorStop(0.5, `rgba(234, 88, 12, ${0.4 + pulse * 0.2})`);
    grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    this.ctx.fillStyle = grad;
    this.ctx.beginPath();
    this.ctx.arc(sx, sy, 24 + pulse * 6, 0, Math.PI * 2);
    this.ctx.fill();

    // Soul flame core
    this.ctx.fillStyle = '#fef08a';
    this.ctx.beginPath();
    this.ctx.arc(sx, sy - 2 + pulse * 2, 4 + pulse * 2, 0, Math.PI * 2);
    this.ctx.fill();

    // Rising soul sparks
    this.ctx.fillStyle = '#fde047';
    this.ctx.fillRect(sx - 3 + pulse * 2, sy - 8 - pulse * 4, 2, 3);
    this.ctx.fillRect(sx + 2 - pulse * 2, sy - 10 - pulse * 3, 2, 4);

    // Floating label
    this.ctx.font = 'bold 8.5px Prompt, sans-serif';
    this.ctx.textAlign = 'center';
    this.ctx.fillStyle = '#fde047';
    this.ctx.fillText(`★ เถ้าธุลีวิญญาณ (${bs.gold} G)`, sx, sy - 16);
    this.ctx.restore();
};


Game.drawForestEntities = function() {
    const list = [];
    this.queueForestEntities(list);
    list.forEach(item => item.render());
};


Game.queueSceneCombatEntities = function(renderables) {
    if (this.worldMonsters) {
        this.worldMonsters.forEach(m => {
            renderables.push({
                depthY: m.y + 28,
                render: () => this.drawSingleWorldMonster(m)
            });
        });
    }

    if (this.boss && this.boss.alive) {
        renderables.push({
            depthY: this.boss.y + 60,
            render: () => this.drawBoss()
        });
    }

    renderables.push({
        depthY: -99999,
        render: () => {
            this.drawBossGroundHazards();
            this.drawBossTelegraphs();
            this.drawBossDashGhosts();
        }
    });

    renderables.push({
        depthY: 99999,
        render: () => {
            this.drawBossShockwaves();
        }
    });
};


Game.queueCaveEntities = function(renderables) {
    this.queueSceneCombatEntities(renderables);
};


Game.queueCaveDepthsEntities = function(renderables) {
    this.queueSceneCombatEntities(renderables);
};


Game.queueSwampEntities = function(renderables) {
    this.queueSceneCombatEntities(renderables);
};


Game.queueVolcanoEntities = function(renderables) {
    this.queueSceneCombatEntities(renderables);
};


Game.queueFrostpeakEntities = function(renderables) {
    this.queueSceneCombatEntities(renderables);
};


Game.queueCryptEntities = function(renderables) {
    this.queueSceneCombatEntities(renderables);
};


Game.queueSpireEntities = function(renderables) {
    this.queueSceneCombatEntities(renderables);
};


Game.queueAncientCanopyEntities = function(renderables) {
    this.queueSceneCombatEntities(renderables);
};


Game.queueTempestPlateauEntities = function(renderables) {
    this.queueSceneCombatEntities(renderables);
};


Game.queueIslandEntities = function(renderables) {
    this.queueSceneCombatEntities(renderables);
};


Game.drawCaveEntities = function() {
    const list = [];
    this.queueCaveEntities(list);
    list.forEach(item => item.render());
};


// ========================================================
// 14.5 WORLD MAP & EXPLORATION (เปิด/ปิด แผนที่โลก)
// ========================================================

Game.toggleWorldMap = function() {
    const modal = document.getElementById('worldMapModal');
    if (!modal) return;
    if (modal.style.display === 'flex') {
        modal.style.display = 'none';
        this.activeModal = null;
    } else {
        this.closeAllModals();
        this.activeModal = 'worldMap';
        modal.style.display = 'flex';
        this.renderWorldMap();
    }
};


Game.renderWorldMap = function() {
    const canvas = document.getElementById("worldMapCanvas") as HTMLCanvasElement | null;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.imageSmoothingEnabled = false;

    const w = canvas.width;
    const h = canvas.height;

    // 1. Parchment map base texture
    ctx.fillStyle = "#eddcd2";
    ctx.fillRect(0, 0, w, h);

    // Vignette / Aged parchment border
    const grad = ctx.createRadialGradient(w / 2, h / 2, 160, w / 2, h / 2, 340);
    grad.addColorStop(0, "rgba(237, 220, 210, 0)");
    grad.addColorStop(1, "rgba(127, 85, 57, 0.45)");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    // Decorative ornate border
    ctx.strokeStyle = "#7f5539";
    ctx.lineWidth = 4;
    ctx.strokeRect(6, 6, w - 12, h - 12);
    ctx.strokeStyle = "#b08968";
    ctx.lineWidth = 1.5;
    ctx.strokeRect(10, 10, w - 20, h - 20);

    // 2. Header Title Banner
    ctx.fillStyle = "rgba(67, 40, 24, 0.9)";
    ctx.beginPath();
    ctx.roundRect(120, 10, 360, 26, 6);
    ctx.fill();
    ctx.strokeStyle = "#d4a373";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    ctx.font = "bold 11.5px Prompt, sans-serif";
    ctx.fillStyle = "#fef08a";
    ctx.textAlign = "center";
    ctx.fillText("แผนที่โลกผจญภัย & ภารกิจปราบ 8 มหาบอส (Fast Travel)", 300, 27);
    ctx.textAlign = "start";

    // 3. Roads / Trails connecting the regions (Dotted paths)
    ctx.strokeStyle = "#a68a64";
    ctx.lineWidth = 2.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    // Tempest Plateau <-> Frostpeak
    ctx.moveTo(152, 81); ctx.lineTo(158, 81);
    // Frostpeak <-> Forest
    ctx.moveTo(294, 81); ctx.lineTo(300, 81);
    // Forest <-> Ancient Canopy
    ctx.moveTo(440, 81); ctx.lineTo(446, 81);
    // Forest <-> Village
    ctx.moveTo(226, 118); ctx.lineTo(226, 126);
    // Crypt <-> Village
    ctx.moveTo(152, 168); ctx.lineTo(158, 168);
    // Village <-> Gloom Swamp
    ctx.moveTo(294, 168); ctx.lineTo(300, 168);
    // Gloom Swamp <-> Ignis Volcano
    ctx.moveTo(384, 168); ctx.lineTo(390, 168);
    // Ignis Volcano <-> Cave
    ctx.moveTo(474, 168); ctx.lineTo(480, 168);
    // Cave Upper <-> Cave Depths
    ctx.moveTo(532, 166); ctx.lineTo(532, 170);
    // Village <-> Farm
    ctx.moveTo(226, 210); ctx.lineTo(226, 218);
    ctx.stroke();
    ctx.setLineDash([]);

    // 4. Region Definitions
    interface WorldMapRegion {
        id: string;
        name: string;
        title: string;
        subtitle: string;
        bossBadge?: string;
        bossDefeated?: boolean;
        bgColor: string;
        borderColor: string;
        x: number;
        y: number;
        w: number;
        h: number;
        spawn: { scene: string; x: number; y: number };
    }

    const defBosses = this.player?.defeatedBosses || {};

    const regions: WorldMapRegion[] = [
        // NW Far: Tempest Plateau (NEW)
        {
            id: "tempest_plateau",
            name: "ที่ราบพายุอัสนี (Tempest Plateau)",
            title: "ที่ราบพายุอัสนี",
            subtitle: "จ้าวพายุสายฟ้า",
            bossBadge: "บอสออสทริออน",
            bossDefeated: !!defBosses["boss_astreon"],
            bgColor: "#e0e7ff",
            borderColor: "#6366f1",
            x: 16, y: 44, w: 136, h: 74,
            spawn: { scene: "tempest_plateau", x: 6, y: 22 }
        },
        // NW Mid: Frostpeak
        {
            id: "frost_peak",
            name: "ยอดเขาเหมันต์นิรันดร์",
            title: "ยอดเขาเหมันต์",
            subtitle: "ไททันน้ำแข็งกลาเซียร์",
            bossBadge: "บอสฟรอสต์แฟงก์",
            bossDefeated: !!defBosses["boss_frostfang"],
            bgColor: "#e0f2fe",
            borderColor: "#38bdf8",
            x: 158, y: 44, w: 136, h: 74,
            spawn: { scene: "frost_peak", x: 24, y: 30 }
        },
        // N Center: Forest
        {
            id: "forest",
            name: "ป่าเอลเดอร์วู้ด & ดงสปอร์",
            title: "ป่าเอลเดอร์วู้ด",
            subtitle: "ดงสปอร์ & ราชาสปอร์",
            bossBadge: "บอสคาธูรอส",
            bossDefeated: !!defBosses["boss_kathuros"],
            bgColor: "#dcfce7",
            borderColor: "#16a34a",
            x: 300, y: 44, w: 140, h: 74,
            spawn: { scene: "forest", x: 24, y: 34 }
        },
        // NE: Ancient Canopy (NEW)
        {
            id: "ancient_canopy",
            name: "พฤกษาบรรพกาล (Ancient Canopy)",
            title: "พฤกษาบรรพกาล",
            subtitle: "เทพพฤกษา & สวนดารา",
            bossBadge: "บอสซิลวาเนีย",
            bossDefeated: !!defBosses["boss_sylvanus"],
            bgColor: "#ecfdf5",
            borderColor: "#059669",
            x: 446, y: 44, w: 138, h: 74,
            spawn: { scene: "ancient_canopy", x: 5, y: 25 }
        },
        // W: Ancient Crypt
        {
            id: "crypt",
            name: "สุสานโบราณใต้พิภพ",
            title: "สุสานโบราณ (Crypt)",
            subtitle: "โครงกระดูก & วิญญาณแค้น",
            bossBadge: "บอสมาลาคอร์",
            bossDefeated: !!defBosses["boss_malakor"],
            bgColor: "#f3e8ff",
            borderColor: "#7c3aed",
            x: 16, y: 126, w: 136, h: 84,
            spawn: { scene: "crypt", x: 23, y: 28 }
        },
        // Center: Village
        {
            id: "village",
            name: "หมู่บ้านศิลาสุขาวดี",
            title: "หมู่บ้านศิลาสุขาวดี",
            subtitle: "คฤหาสน์ • โอสถ • ร้าน • ตีเหล็ก",
            bgColor: "#fef3c7",
            borderColor: "#d97706",
            x: 158, y: 126, w: 136, h: 84,
            spawn: { scene: "village", x: 30, y: 25 }
        },
        // E Left: Gloom Swamp
        {
            id: "swamp",
            name: "บึงมรณะกลูมสแวมป์",
            title: "บึงกลูมสแวมป์",
            subtitle: "จระเข้บึง & พิษ",
            bossBadge: "บอสไฮดราคิส",
            bossDefeated: !!defBosses["boss_hydrakis"],
            bgColor: "#ecfccb",
            borderColor: "#65a30d",
            x: 300, y: 126, w: 84, h: 84,
            spawn: { scene: "swamp", x: 24, y: 28 }
        },
        // E Mid: Ignis Volcano
        {
            id: "volcano",
            name: "ภูเขาไฟอิกนิส",
            title: "ภูเขาไฟอิกนิส",
            subtitle: "ธารลาวา & ภูตเพลิง",
            bossBadge: "บอสอิกนิสตรอน",
            bossDefeated: !!defBosses["boss_ignistron"],
            bgColor: "#ffedd5",
            borderColor: "#ea580c",
            x: 390, y: 126, w: 84, h: 84,
            spawn: { scene: "volcano", x: 24, y: 28 }
        },
        // E Far Top: Cave Upper
        {
            id: "cave",
            name: "ถ้ำผลึกเรืองแสง",
            title: "ถ้ำผลึกชั้นบน",
            subtitle: "สายแร่ทองคำ",
            bgColor: "#f1f5f9",
            borderColor: "#64748b",
            x: 480, y: 126, w: 104, h: 40,
            spawn: { scene: "cave", x: 21, y: 28 }
        },
        // E Far Bottom: Cave Depths
        {
            id: "cave_depths",
            name: "ถ้ำห้วงลึกใต้พิภพ",
            title: "ถ้ำห้วงลึก (Depths)",
            subtitle: "ลูมินาร์ค",
            bossBadge: "บอสลูมินาร์ค",
            bossDefeated: !!defBosses["boss_luminarch"],
            bgColor: "#cffafe",
            borderColor: "#0891b2",
            x: 480, y: 170, w: 104, h: 40,
            spawn: { scene: "cave_depths", x: 22, y: 28 }
        },
        // S: Happy Farm
        {
            id: "farm",
            name: "ไร่สุขใจ",
            title: "ไร่สุขใจ (Home Farm)",
            subtitle: "บ้านพัก • แปลงผัก • ร้าน • บ่อน้ำ",
            bgColor: "#dcfce7",
            borderColor: "#10b981",
            x: 158, y: 218, w: 136, h: 88,
            spawn: { scene: "farm", x: 17, y: 12 }
        }
    ];

    // 5. Draw Each Region Card
    for (const r of regions) {
        ctx.fillStyle = r.bgColor;
        ctx.beginPath();
        ctx.roundRect(r.x, r.y, r.w, r.h, 7);
        ctx.fill();

        ctx.strokeStyle = r.borderColor;
        ctx.lineWidth = 1.8;
        ctx.stroke();

        ctx.font = "bold 10px Prompt, sans-serif";
        ctx.fillStyle = "#1e293b";
        ctx.fillText(r.title, r.x + 6, r.y + 16);

        ctx.font = "8px Prompt, sans-serif";
        ctx.fillStyle = "#64748b";
        ctx.fillText(r.subtitle, r.x + 6, r.y + 28);

        if (r.bossBadge) {
            const badgeY = r.y + (r.h > 55 ? 42 : 18);
            ctx.fillStyle = r.bossDefeated ? "rgba(34, 197, 94, 0.15)" : "rgba(239, 68, 68, 0.15)";
            ctx.beginPath();
            ctx.roundRect(r.x + 5, badgeY, r.w - 10, 16, 4);
            ctx.fill();
            ctx.strokeStyle = r.bossDefeated ? "#22c55e" : "#ef4444";
            ctx.lineWidth = 1;
            ctx.stroke();

            ctx.font = "bold 8px Prompt, sans-serif";
            ctx.fillStyle = r.bossDefeated ? "#15803d" : "#b91c1c";
            const statusLabel = r.bossDefeated ? "✓ ปราบแล้ว" : "ยังไม่ปราบ";
            ctx.fillText(r.bossBadge, r.x + 8, badgeY + 11);
            ctx.textAlign = "right";
            ctx.fillText(statusLabel, r.x + r.w - 8, badgeY + 11);
            ctx.textAlign = "start";
        }

        ctx.font = "bold 7.5px Prompt, sans-serif";
        ctx.fillStyle = "#6366f1";
        ctx.textAlign = "right";
        ctx.fillText("▶ วาร์ป", r.x + r.w - 5, r.y + r.h - 5);
        ctx.textAlign = "start";
    }

    // 6. Bottom Panels
    // Bottom-Left Panel: Compass & Fast Travel Instructions
    ctx.fillStyle = "#f8fafc";
    ctx.beginPath();
    ctx.roundRect(16, 218, 136, 88, 7);
    ctx.fill();
    ctx.strokeStyle = "#94a3b8";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Compass Rose in Bottom-Left
    ctx.save();
    ctx.translate(45, 262);
    ctx.strokeStyle = "#7f5539";
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.arc(0, 0, 16, 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillStyle = "#b91c1c";
    ctx.beginPath(); ctx.moveTo(0, -14); ctx.lineTo(4, 0); ctx.lineTo(0, -4); ctx.fill();
    ctx.fillStyle = "#7f5539";
    ctx.beginPath(); ctx.moveTo(0, 14); ctx.lineTo(4, 0); ctx.lineTo(0, 4); ctx.fill();
    ctx.font = "bold 7.5px sans-serif";
    ctx.fillStyle = "#b91c1c"; ctx.fillText("N", -3, -16);
    ctx.fillStyle = "#7f5539"; ctx.fillText("S", -2, 23);
    ctx.fillText("W", -23, 3); ctx.fillText("E", 18, 3);
    ctx.restore();

    ctx.font = "bold 9.5px Prompt, sans-serif";
    ctx.fillStyle = "#1e293b";
    ctx.fillText("Fast Travel", 72, 240);
    ctx.font = "8px Prompt, sans-serif";
    ctx.fillStyle = "#475569";
    ctx.fillText("คลิกสถานที่ใดก็ได้", 72, 256);
    ctx.fillText("เพื่อวาร์ปทันที!", 72, 270);
    ctx.fillStyle = "#2563eb";
    ctx.fillText("ไม่มีคูลดาวน์", 72, 286);

    // Bottom-Right Panel: 8 Boss Hunter Bounty Tracker
    ctx.fillStyle = "#0f172a";
    ctx.beginPath();
    ctx.roundRect(300, 218, 284, 88, 7);
    ctx.fill();
    ctx.strokeStyle = "#6366f1";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    let defCount = 0;
    const bossList = ["boss_kathuros", "boss_luminarch", "boss_hydrakis", "boss_ignistron", "boss_frostfang", "boss_malakor", "boss_sylvanus", "boss_astreon"];
    for (const bId of bossList) {
        if (defBosses[bId]) defCount++;
    }

    ctx.font = "bold 10px Prompt, sans-serif";
    ctx.fillStyle = "#fde047";
    ctx.fillText("ล่า 8 มหาบอสทั่วพิภพ (Boss Tracker)", 312, 236);

    ctx.font = "8.5px Prompt, sans-serif";
    ctx.fillStyle = "#94a3b8";
    ctx.fillText("ปราบสำเร็จแล้ว: ", 312, 252);
    ctx.fillStyle = defCount === 8 ? "#4ade80" : "#facc15";
    ctx.font = "bold 9.5px Prompt, sans-serif";
    ctx.fillText(defCount + " / 8 ราชา", 380, 252);

    // 8 Mini Boss Badges in 4x2 Grid
    const miniBadges = [
        { id: "boss_kathuros", label: "คาธูรอส" },
        { id: "boss_luminarch", label: "ลูมินาร์ค" },
        { id: "boss_hydrakis", label: "ไฮดรา" },
        { id: "boss_ignistron", label: "อิกนิส" },
        { id: "boss_frostfang", label: "ฟรอสต์" },
        { id: "boss_malakor", label: "มาลาคอร์" },
        { id: "boss_sylvanus", label: "ซิลวาเนีย" },
        { id: "boss_astreon", label: "ออสทริออน" },
    ];

    miniBadges.forEach((mb, idx) => {
        const isDef = !!defBosses[mb.id];
        const col = idx % 4;
        const row = Math.floor(idx / 4);
        const bx = 312 + col * 66;
        const by = 260 + row * 18;
        ctx.fillStyle = isDef ? "rgba(34, 197, 94, 0.25)" : "rgba(239, 68, 68, 0.2)";
        ctx.fillRect(bx, by, 62, 15);
        ctx.strokeStyle = isDef ? "#22c55e" : "#64748b";
        ctx.lineWidth = 1;
        ctx.strokeRect(bx, by, 62, 15);
        ctx.font = "7.5px Prompt, sans-serif";
        ctx.fillStyle = isDef ? "#86efac" : "#cbd5e1";
        ctx.fillText((isDef ? "✓ " : "") + mb.label, bx + 3, by + 11);
    });

    // 7. Live Player Location Pin Calculation
    let pinX = 226;
    let pinY = 255;
    let locName = "ไร่สุขใจ (Happy Farm)";

    if (this.currentScene === "farm") {
        pinX = 160 + (this.player.x / (34 * 32)) * 130;
        pinY = 222 + (this.player.y / (24 * 32)) * 75;
        locName = "คุณอยู่ที่: ไร่สุขใจ (ฟาร์มเกษตรกร)";
    } else if (this.currentScene === "house") {
        pinX = 175; pinY = 245;
        locName = "คุณอยู่ที่: บ้านพักชาวสวน";
    } else if (this.currentScene === "shop") {
        pinX = 270; pinY = 245;
        locName = "คุณอยู่ที่: ร้านค้าเกษตรชุมชน";
    } else if (this.currentScene === "village") {
        pinX = 160 + (this.player.x / (60 * 32)) * 130;
        pinY = 130 + (this.player.y / (44 * 32)) * 75;
        locName = "คุณอยู่ที่: หมู่บ้านศิลาสุขาวดี (Sunvale Village)";
    } else if (this.currentScene === "manor") {
        pinX = 175; pinY = 145;
        locName = "คุณอยู่ที่: คฤหาสน์ว่าการหมู่บ้านศิลาสุขาวดี";
    } else if (this.currentScene === "apothecary") {
        pinX = 270; pinY = 145;
        locName = "คุณอยู่ที่: ร้านโอสถและสมุนไพร ลิเลียน";
    } else if (this.currentScene === "tavern") {
        pinX = 270; pinY = 185;
        locName = "คุณอยู่ที่: โรงเตี๊ยมรวงทอง บ็อบ";
    } else if (this.currentScene === "forge") {
        pinX = 175; pinY = 185;
        locName = "คุณอยู่ที่: โรงตีเหล็กศิลา คาเอล";
    } else if (this.currentScene === "forest") {
        pinX = 305 + (this.player.x / (50 * 32)) * 130;
        pinY = 48 + (this.player.y / (40 * 32)) * 66;
        locName = "คุณอยู่ที่: ผืนป่าเอลเดอร์วู้ด & ดงสปอร์พิษ";
    } else if (this.currentScene === "ancient_canopy") {
        pinX = 450 + (this.player.x / (60 * 32)) * 130;
        pinY = 48 + (this.player.y / (50 * 32)) * 66;
        locName = "คุณอยู่ที่: พฤกษาบรรพกาล (เทพพฤกษา ซิลวาเนีย)";
    } else if (this.currentScene === "tempest_plateau") {
        pinX = 20 + (this.player.x / (60 * 32)) * 128;
        pinY = 48 + (this.player.y / (45 * 32)) * 66;
        locName = "คุณอยู่ที่: ที่ราบพายุอัสนี (จ้าวพายุ ออสทริออน)";
    } else if (this.currentScene === "cave") {
        pinX = 485 + (this.player.x / (44 * 32)) * 95;
        pinY = 130 + (this.player.y / (36 * 32)) * 32;
        locName = "คุณอยู่ที่: ถ้ำผลึกเรืองแสง";
    } else if (this.currentScene === "cave_depths") {
        pinX = 485 + (this.player.x / (44 * 32)) * 95;
        pinY = 174 + (this.player.y / (36 * 32)) * 32;
        locName = "คุณอยู่ที่: ถ้ำห้วงลึกใต้พิภพ (ลูมินาร์ค)";
    } else if (this.currentScene === "swamp") {
        pinX = 305 + (this.player.x / (50 * 32)) * 74;
        pinY = 130 + (this.player.y / (36 * 32)) * 75;
        locName = "คุณอยู่ที่: บึงมรณะกลูมสแวมป์ (ไฮดราคิส)";
    } else if (this.currentScene === "volcano") {
        pinX = 395 + (this.player.x / (50 * 32)) * 74;
        pinY = 130 + (this.player.y / (36 * 32)) * 75;
        locName = "คุณอยู่ที่: ปากปล่องภูเขาไฟอิกนิส (อิกนิสตรอน)";
    } else if (this.currentScene === "frost_peak") {
        pinX = 162 + (this.player.x / (50 * 32)) * 128;
        pinY = 48 + (this.player.y / (36 * 32)) * 66;
        locName = "คุณอยู่ที่: ยอดเขาเหมันต์นิรันดร์ (ฟรอสต์แฟงก์)";
    } else if (this.currentScene === "crypt") {
        pinX = 20 + (this.player.x / (50 * 32)) * 128;
        pinY = 130 + (this.player.y / (36 * 32)) * 75;
        locName = "คุณอยู่ที่: สุสานโบราณใต้พิภพ (มาลาคอร์)";
    }

    // Draw Live Pin & Pulsing Rings
    const pulse = (performance.now() / 300) % 1;
    ctx.strokeStyle = "rgba(239, 68, 68, " + (1 - pulse) + ")";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(pinX, pinY, 6 + pulse * 14, 0, Math.PI * 2);
    ctx.stroke();

    ctx.fillStyle = "#ef4444";
    ctx.beginPath();
    ctx.arc(pinX, pinY - 10, 7, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(pinX, pinY - 10, 2.5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#ef4444";
    ctx.beginPath();
    ctx.moveTo(pinX - 5, pinY - 6);
    ctx.lineTo(pinX + 5, pinY - 6);
    ctx.lineTo(pinX, pinY);
    ctx.fill();

    // Pin Label Badge
    ctx.fillStyle = "rgba(15, 23, 42, 0.9)";
    ctx.beginPath();
    ctx.roundRect(pinX - 42, pinY + 6, 84, 18, 4);
    ctx.fill();
    ctx.strokeStyle = "#facc15";
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillStyle = "#fde047";
    ctx.font = "bold 9px Prompt, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("ตัวคุณอยู่ที่นี่", pinX, pinY + 18);
    ctx.textAlign = "start";

    // Update Text in modal header
    const locTextEl = document.getElementById("mapCurrentLocationText");
    if (locTextEl) locTextEl.textContent = locName;

    // 8. Interactive Fast Travel Click & Hover Listeners
    canvas.onclick = (e: MouseEvent) => {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const clickX = (e.clientX - rect.left) * scaleX;
        const clickY = (e.clientY - rect.top) * scaleY;

        for (const r of regions) {
            if (clickX >= r.x && clickX <= r.x + r.w && clickY >= r.y && clickY <= r.y + r.h) {
                SoundEngine.warpSound();
                this.toggleWorldMap();
                this.switchScene(r.spawn.scene, r.spawn.x, r.spawn.y);
                this.addFloatingText("เดินทางด่วนสู่ " + r.name + "!", this.player.x, this.player.y - 25, "#fde047");
                return;
            }
        }
    };

    canvas.onmousemove = (e: MouseEvent) => {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const mx = (e.clientX - rect.left) * scaleX;
        const my = (e.clientY - rect.top) * scaleY;
        const hover = regions.some(r => mx >= r.x && mx <= r.x + r.w && my >= r.y && my <= r.y + r.h);
        canvas.style.cursor = hover ? "pointer" : "default";
    };
};

Game.drawMeleeSlash = function() {
    if (!this.meleeSlashAnim) return;

    const slash = this.meleeSlashAnim;
    const sx = Math.round(slash.x - this.camera.x);
    const sy = Math.round(slash.y - this.camera.y);
    const progress = Math.max(0, Math.min(1, slash.timer / (slash.maxTimer || 180)));
    const combo = slash.comboStep || 1;

    this.ctx.save();
    this.ctx.translate(sx, sy);
    this.ctx.rotate(slash.angle);

    if (combo === 3) {
        // Step 3 Finisher: Giant Golden Explosive Solar Arc (180 degrees)
        this.ctx.shadowColor = '#facc15';
        this.ctx.shadowBlur = 16;

        this.ctx.strokeStyle = `rgba(250, 204, 21, ${0.95 * progress})`;
        this.ctx.lineWidth = 6;
        this.ctx.beginPath();
        this.ctx.arc(14, 0, 36, -Math.PI / 1.8, Math.PI / 1.8);
        this.ctx.stroke();

        this.ctx.strokeStyle = `rgba(255, 255, 255, ${1.0 * progress})`;
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        this.ctx.arc(16, 0, 32, -Math.PI / 2.2, Math.PI / 2.2);
        this.ctx.stroke();
    } else if (combo === 2) {
        // Step 2: Wide Azure Cleave (125 degrees)
        this.ctx.shadowColor = '#38bdf8';
        this.ctx.shadowBlur = 12;

        this.ctx.strokeStyle = `rgba(56, 189, 248, ${0.88 * progress})`;
        this.ctx.lineWidth = 4.5;
        this.ctx.beginPath();
        this.ctx.arc(16, 0, 28, -Math.PI / 2.6, Math.PI / 2.6);
        this.ctx.stroke();

        this.ctx.strokeStyle = `rgba(255, 255, 255, ${0.95 * progress})`;
        this.ctx.lineWidth = 2.2;
        this.ctx.beginPath();
        this.ctx.arc(18, 0, 25, -Math.PI / 3, Math.PI / 3);
        this.ctx.stroke();
    } else {
        // Step 1: Swift Silver Slash (75 degrees)
        this.ctx.shadowColor = '#cbd5e1';
        this.ctx.shadowBlur = 8;

        this.ctx.strokeStyle = `rgba(248, 250, 252, ${0.88 * progress})`;
        this.ctx.lineWidth = 3.5;
        this.ctx.beginPath();
        this.ctx.arc(18, 0, 24, -Math.PI / 3.4, Math.PI / 3.4);
        this.ctx.stroke();
    }

    if (slash.isHoly) {
        this.ctx.strokeStyle = `rgba(253, 224, 71, ${0.9 * progress})`;
        this.ctx.lineWidth = 2.5;
        this.ctx.beginPath();
        this.ctx.arc(22, 0, 38, -Math.PI / 3, Math.PI / 3);
        this.ctx.stroke();
    }

    this.ctx.restore();
};


// ========================================================
// 15. MAIN GAME LOOP
// ========================================================

Game.gameLoop = function(timestamp) {
    try {
        const rawDt = timestamp - (this.lastTime || timestamp);
        const dt = Math.min(100, Math.max(1, rawDt));
        this.lastTime = timestamp;

        // Fluid combat hitstop (no freeze, smooth 60fps controls)
        if (this.hitstopTimer > 0) {
            this.hitstopTimer = Math.max(0, this.hitstopTimer - dt);
        }

        // Screen transition updates (fade in/out & scene banner)
        this.updateTransition(dt);

        this.updatePlayer(dt);
        this.updatePetCompanion(dt);
        this.updateMachines(dt);
        this.updateAnimals(dt);
        this.updateShopNPCs(dt);
        this.updateVillageVillagers(dt);
        this.updateDemonBugs(dt);
        this.updateWorldMonsters(dt);
        this.updatePlayerSkills(dt);
        this.updateBoss(dt);
        this.updateBossTelegraphs(dt);
        this.updateBossGroundHazards(dt);
        this.updateBossShockwaves(dt);
        this.updateBossDashGhosts(dt);
        this.updateHiredGardeners(dt);
        this.updateHiredHunters(dt);
        this.updateProjectiles(dt);
        this.updateFishing(dt);
        this.updateDroppedItems(dt);
        this.updateAmbientCreatures(dt);
        this.updateAmbientEffects(dt);
        this.updateTime(dt);

        if (this.meleeSlashAnim) {
            this.meleeSlashAnim.timer -= dt;
            if (this.meleeSlashAnim.timer <= 0) {
                this.meleeSlashAnim = null;
            }
        }

        if (this.activeModal === 'worldMap' || this.activeModal === 'worldMapModal') {
            this.renderWorldMap();
        }

        this.render();
    } catch (err) {
        console.error('GameLoop auto-recovered error:', err);
    } finally {
        requestAnimationFrame((t) => this.gameLoop(t));
    }
};


// ========================================================
// 16. MUSEUM COMPENDIUM & ACHIEVEMENTS SYSTEM
// ========================================================

Game.toggleCompendiumModal = function() {
    const modal = document.getElementById('compendiumModal');
    if (!modal) return;
    if (modal.style.display === 'flex') {
        modal.style.display = 'none';
        this.activeModal = null;
    } else {
        this.closeAllModals();
        this.activeModal = 'compendium';
        modal.style.display = 'flex';
        this.checkAchievements();
        this.renderCompendium();
    }
};


Game.setCompendiumTab = function(tab: string) {
    this.compendiumActiveTab = tab;
    document.querySelectorAll('.compendium-tab-btn').forEach((btn: any) => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    this.renderCompendium();
};


Game.renderCompendium = function() {
    const container = document.getElementById('compendiumContent');
    if (!container) return;
    container.innerHTML = '';

    const currentTab = this.compendiumActiveTab || 'crops';
    const catData = COMPENDIUM_CATEGORIES[currentTab];

    if (!this.player.museumCollections) {
        this.player.museumCollections = { crops: [], fish: [], minerals: [], artisan: [] };

    }
    const collectedList = this.player.museumCollections[currentTab] || [];

    // Header banner
    const banner = document.createElement('div');
    banner.style.cssText = 'display:flex; justify-content:space-between; align-items:center; background:#eddcd2; border:2px solid #7f5539; border-radius:8px; padding:10px 14px; margin-bottom:12px;';

    if (currentTab === 'achievements') {
        const unlockedCount = Object.keys(this.player.achievements || {}).length;
        banner.innerHTML = `
            <div style="font-size:12px; color:#451a03; font-weight:600;">${catData?.desc || 'บันทึกเกียรติยศและภารกิจท้าทาย'}</div>
            <div style="font-size:12px; font-weight:700; color:#78350f;">ปลดล็อคแล้ว: <span style="color:#b45309;">${unlockedCount} / ${ACHIEVEMENTS_DATA.length} ตรา</span></div>
        `;
        container.appendChild(banner);

        const list = document.createElement('div');
        list.className = 'achievements-list';

        ACHIEVEMENTS_DATA.forEach(ach => {
            const isUnlocked = !!(this.player.achievements && this.player.achievements[ach.id]);
            const isClaimed = !!(this.player.achievementsClaimed && this.player.achievementsClaimed[ach.id]);
            const card = document.createElement('div');
            card.className = `achievement-card ${isUnlocked ? 'completed' : ''}`;

            let claimBtnHtml = '';
            if (isUnlocked && !isClaimed) {
                claimBtnHtml = `<button class="btn-claim-reward" onclick="Game.claimAchievementReward('${ach.id}', ${ach.rewardGold})">รับ +${ach.rewardGold} G</button>`;
            } else if (isClaimed) {
                claimBtnHtml = `<span style="color:#16a34a; font-weight:700; font-size:11px;">✓ รับรางวัลแล้ว</span>`;
            } else {
                claimBtnHtml = `<span style="color:#94a3b8; font-size:11px; font-weight:600;">[ยังไม่สำเร็จ]</span>`;
            }

            card.innerHTML = `
                <div class="achievement-icon">${ach.icon}</div>
                <div class="achievement-info">
                    <div class="achievement-title">${ach.name}</div>
                    <div class="achievement-desc">${ach.desc}</div>
                    <div style="font-size:10px; color:#b45309; font-weight:700; margin-top:3px;">รางวัล: +${ach.rewardGold} G</div>
                </div>
                <div>${claimBtnHtml}</div>
            `;
            list.appendChild(card);
        });
        container.appendChild(list);
        return;
    }

    // Normal Item Category
    const allItems = catData ? catData.items : [];
    banner.innerHTML = `
        <div style="font-size:12px; color:#451a03; font-weight:600;">${catData?.desc || ''}</div>
        <div style="font-size:12px; font-weight:700; color:#78350f;">ค้นพบแล้ว: <span style="color:#15803d;">${collectedList.length} / ${allItems.length} ชนิด</span></div>
    `;
    container.appendChild(banner);

    const grid = document.createElement('div');
    grid.className = 'compendium-grid';

    allItems.forEach((itemId: string) => {
        const isDiscovered = collectedList.includes(itemId);
        const itemInfo = WORLD_ITEMS[itemId] || { name: itemId, desc: '' };

        const card = document.createElement('div');
        card.className = `compendium-card ${isDiscovered ? 'discovered' : 'locked'}`;

        const iconContainer = document.createElement('div');
        iconContainer.className = 'compendium-card-icon';
        if (isDiscovered) {
            const icon = SPRITES.getItemIcon(itemId);
            icon.style.width = '32px';
            icon.style.height = '32px';
            iconContainer.appendChild(icon);
        } else {
            iconContainer.innerHTML = '<span style="font-size:22px; color:#94a3b8; font-weight:bold;">?</span>';
        }

        const nameEl = document.createElement('div');
        nameEl.className = 'compendium-card-name';
        nameEl.textContent = isDiscovered ? itemInfo.name : '???';

        const descEl = document.createElement('div');
        descEl.className = 'compendium-card-desc';
        descEl.textContent = isDiscovered ? (itemInfo.desc || 'ไอเทมที่ค้นพบแล้ว') : 'ยังไม่เคยค้นพบหรือผลิตได้';

        card.appendChild(iconContainer);
        card.appendChild(nameEl);
        card.appendChild(descEl);
        grid.appendChild(card);
    });
    container.appendChild(grid);
};


Game.claimAchievementReward = function(achId: string, gold: number) {
    if (!this.player.achievementsClaimed) this.player.achievementsClaimed = {};

    if (this.player.achievementsClaimed[achId]) return;
    this.player.achievementsClaimed[achId] = true;
    this.player.gold += gold;
    SoundEngine.levelUp();
    this.spawnParticles(this.player.x + 10, this.player.y + 10, '#facc15', 20);
    this.addFloatingText(` รับรางวัลความสำเร็จ! +${gold} G`, this.player.x - 20, this.player.y - 20, '#fde047');
    this.updateHUD();
    this.renderCompendium();
};


Game.checkAchievements = function() {
    if (!this.player.achievements) this.player.achievements = {};

    const ach = this.player.achievements;

    if ((this.stats?.harvests || 0) >= 1) ach.first_harvest = true;
    if ((this.player.gold || 0) >= 1000) ach.first_1k_gold = true;
    if ((this.player.mineProgress?.deepestFloor || 1) >= 5) ach.cave_floor_5 = true;
    if ((this.player.mineProgress?.deepestFloor || 1) >= 20) ach.cave_floor_20 = true;
    if ((this.stats?.animalsPetted || 0) >= 5) ach.master_breeder = true;
    if (Object.keys(this.placedMachines || {}).length >= 2) ach.artisan_builder = true;
    if (this.player.isMounted) ach.mount_rider = true;
    if (this.player.pet && this.player.pet.happiness >= 100) ach.pet_best_friend = true;

    // Check 5-heart friend (friendship >= 100)
    if (this.player.npcFriendship) {
        for (const k in this.player.npcFriendship) {
            if (this.player.npcFriendship[k] >= 100) {
                ach.village_heart = true;
                break;
            }
        }
    }
};


Game.unlockCompendiumItem = function(itemId: string) {
    if (!this.player.museumCollections) {
        this.player.museumCollections = { crops: [], fish: [], minerals: [], artisan: [] };

    }
    for (const catKey in COMPENDIUM_CATEGORIES) {
        if (catKey === 'achievements') continue;
        const cat = COMPENDIUM_CATEGORIES[catKey];
        if (cat.items.includes(itemId)) {
            const list = this.player.museumCollections[catKey] || [];
            if (!list.includes(itemId)) {
                list.push(itemId);
                this.player.museumCollections[catKey] = list;
                const info = WORLD_ITEMS[itemId] || { name: itemId };

                this.addFloatingText(` บันทึก '${info.name}' ลงสมุดสะสมแล้ว!`, this.player.x - 30, this.player.y - 30, '#a855f7');
                SoundEngine.bell();
                this.checkAchievements();
            }
            break;
        }
    }
};


// ========================================================
// 17. MULTI-FLOOR DEEP MINES & SHAFT ELEVATOR
// ========================================================

Game.openMineElevatorModal = function() {
    const modal = document.getElementById('mineElevatorModal');
    if (!modal) return;
    const deepest = this.player.mineProgress?.deepestFloor || 1;
    const unlocked = this.player.mineProgress?.unlockedElevators || [1];

    const grid = document.getElementById('mineElevatorFloorGrid');
    if (grid) {
        grid.innerHTML = '';
        [1, 5, 10, 15, 20].forEach(floor => {
            const isAvailable = unlocked.includes(floor) || deepest >= floor;
            const btn = document.createElement('button');
            btn.className = 'elevator-floor-btn';
            btn.innerHTML = `<span>ชั้นที่ ${floor}</span><span>${isAvailable ? (floor === 20 ? '[ชั้นลึกสุด]' : '▶ ไปที่ชั้นนี้') : '[ยังไม่ปลดล็อก]'}</span>`;
            if (isAvailable) {
                btn.onclick = () => {
                    this.warpCaveFloor(floor);
                    modal.style.display = 'none';
                    this.activeModal = null;
                };

            } else {
                btn.disabled = true;
            }
            grid.appendChild(btn);
        });
    }
    this.closeAllModals();
    this.activeModal = 'mineElevator';
    modal.style.display = 'flex';
};


Game.descendCaveFloor = function() {
    const nextFloor = (this.currentCaveFloor || 1) + 1;
    this.warpCaveFloor(nextFloor);
};


Game.ascendCaveFloor = function() {
    const prevFloor = Math.max(1, (this.currentCaveFloor || 1) - 1);
    this.warpCaveFloor(prevFloor);
};


Game.warpCaveFloor = function(targetFloor: number) {
    this.currentCaveFloor = targetFloor;
    if (!this.player.mineProgress) {
        this.player.mineProgress = { currentFloor: 1, deepestFloor: 1, unlockedElevators: [1] };

    }
    this.player.mineProgress.currentFloor = targetFloor;
    if (targetFloor > (this.player.mineProgress.deepestFloor || 1)) {
        this.player.mineProgress.deepestFloor = targetFloor;
    }
    if ((targetFloor === 1 || targetFloor % 5 === 0) && !this.player.mineProgress.unlockedElevators.includes(targetFloor)) {
        this.player.mineProgress.unlockedElevators.push(targetFloor);
        this.addFloatingText(` ปลดล็อคลิฟต์เหมืองชั้น ${targetFloor} แล้ว!`, this.player.x, this.player.y - 25, '#facc15');
        SoundEngine.levelUp();
    }

    // Generate and enter floor
    this.scenes.cave = this.generateCaveMap(targetFloor);
    this.switchScene('cave', 21, 30);
    this.addFloatingText(` เหมืองผลึกเวทมนตร์ ชั้นที่ ${targetFloor}`, this.player.x - 30, this.player.y - 20, '#67e8f9');
    this.checkAchievements();
};


Game.sailToIslandNow = function() {
    this.closeAllModals();
    this.player.sailboatRepaired = true;
    if (typeof this.saveGame === 'function') {
        this.saveGame();
    }
    SoundEngine.bell();
    this.travelToIsland();
};


// ========================================================
// 18. MOUNT SYSTEM & HORSE SPEED
// ========================================================

Game.toggleMount = function() {
    this.player.isMounted = !this.player.isMounted;
    if (this.player.isMounted) {
        SoundEngine.whistleSound();
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#facc15', 15);
        this.addFloatingText(' ขึ้นขี่ม้าพาหนะ! ความเร็วเคลื่อนที่ +65%', this.player.x - 20, this.player.y - 25, '#facc15');
        this.checkAchievements();
    } else {
        SoundEngine.step();
        this.addFloatingText(' ลงจากหลังม้า', this.player.x, this.player.y - 15, '#94a3b8');
    }
    this.updateHUD();
};


// ========================================================
// 19. NPC FRIENDSHIP & GIFT GIVING
// ========================================================

Game.openGiftSelectModal = function(npcId: string) {
    const modal = document.getElementById('giftSelectModal');
    if (!modal) return;
    const targetNameEl = document.getElementById('giftTargetNpcName');
    const npcCfg = NPC_STORY[npcId];
    if (targetNameEl && npcCfg) targetNameEl.textContent = npcCfg.name;

    const grid = document.getElementById('giftCandidateSlots');
    if (grid) {
        grid.innerHTML = '';
        const inventory = this.player.inventory || [];
        const seenItems = new Set<string>();

        inventory.forEach((slot: any) => {
            if (!slot || !slot.id || seenItems.has(slot.id)) return;
            seenItems.add(slot.id);

            const count = this.countItemInInventory(slot.id);
            const btn = document.createElement('button');
            btn.className = 'gift-item-btn';
            btn.title = slot.name || slot.id;
            const icon = SPRITES.getItemIcon(slot.id);
            icon.style.width = '24px';
            icon.style.height = '24px';

            const countSpan = document.createElement('span');
            countSpan.className = 'gift-item-count';
            countSpan.textContent = `x${count}`;

            btn.appendChild(icon);
            btn.appendChild(countSpan);
            btn.onclick = () => {
                this.giveGiftToNpc(npcId, slot.id);
                this.closeGiftSelectModal();
            };

            grid.appendChild(btn);
        });

        if (seenItems.size === 0) {
            grid.innerHTML = '<div style="color:#94a3b8; font-size:13px; text-align:center; padding:15px; grid-column:1/-1;">ไม่มีสิ่งของในกระเป๋าที่สามารถมอบให้ได้</div>';
        }
    }

    modal.style.display = 'flex';
};


Game.closeGiftSelectModal = function() {
    const modal = document.getElementById('giftSelectModal');
    if (modal) modal.style.display = 'none';
};


Game.giveGiftToNpc = function(npcId: string, itemId: string) {
    if (this.countItemInInventory(itemId) < 1) {
        this.addFloatingText('ไม่มีไอเทมนี้ในกระเป๋า', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }

    if (!this.player.npcFriendship) this.player.npcFriendship = {};

    const currentScore = this.player.npcFriendship[npcId] || 0;

    //  Bouquet Confession
    if (itemId === 'bouquet') {
        this.removeItemFromInventory(itemId, 1);
        if (currentScore >= 60) {
            this.player.dating = npcId;
            this.player.npcFriendship[npcId] = Math.min(200, currentScore + 30);
            SoundEngine.levelUp();
            this.spawnParticles(this.player.x, this.player.y, '#ec4899', 30);
            this.addFloatingText(`♥ ${NPC_STORY[npcId]?.name} รับช่อดอกไม้! ตกลงเป็น "แฟน (Dating)" กันแล้ว!`, this.player.x - 40, this.player.y - 25, '#ec4899');
            const textEl = document.getElementById('dialogueText');
            if (textEl) textEl.textContent = `"ช่อดอกไม้นี้งดงามมาก... หัวใจของข้าเต้นแรงไปหมดแล้ว ข้าสัญญาว่าจะดูแลความรักของเราอย่างดีที่สุดนะ! ♥"`;
            this.updateHUD();
            return;
        } else {
            const textEl = document.getElementById('dialogueText');
            if (textEl) textEl.textContent = `"ช่อดอกไม้นี้สวยจัง... แต่เรายังเพิ่งรู้จักกันได้ไม่นานนะ เป็นเพื่อนที่ดีต่อกันก่อนดีกว่าจ้ะ"`;
            this.updateHUD();
            return;
        }
    }

    //  Mermaid's Star Amulet: Marriage Proposal
    if (itemId === 'mermaids_amulet') {
        this.removeItemFromInventory(itemId, 1);
        if (currentScore >= 80) {
            this.startWeddingCutscene(npcId);
            return;
        } else {
            const textEl = document.getElementById('dialogueText');
            if (textEl) textEl.textContent = `"จี้ดวงดาวสื่อรักนี้เลอค่ายิ่งนัก... แต่ข้าคิดว่าเราควรสะสมความทรงจำร่วมกันมากกว่านี้ก่อนนะ"`;
            this.updateHUD();
            return;
        }
    }

    this.removeItemFromInventory(itemId, 1);
    const prefs = (NPC_GIFTS as Record<string, any>)[npcId];
    let points = 10;
    let quote = 'ขอบคุณมากนะ!';
    let heartColor = '#f472b6';

    if (prefs?.loved?.includes(itemId)) {
        points = 25;
        quote = prefs.lovedQuote || 'โอ้โห! ข้ารักสิ่งนี้มากที่สุดเลย! ขอบคุณเจ้าจริงๆ!';
        heartColor = '#ec4899';
        SoundEngine.levelUp();
    } else if (prefs?.liked?.includes(itemId)) {
        points = 15;
        quote = prefs.likedQuote || 'นี่มันดีจัง ขอบคุณมากนะสำหรับของขวัญ';
        SoundEngine.bell();
    } else if (prefs?.disliked?.includes(itemId)) {
        points = -5;
        quote = prefs.dislikedQuote || 'เอ่อ... ข้าไม่ค่อยชอบสิ่งนี้เท่าไหร่ แต่ก็ขอบคุณนะ';
        heartColor = '#94a3b8';
    } else {
        SoundEngine.bell();
    }

    this.player.npcFriendship[npcId] = Math.max(0, Math.min(200, currentScore + points));

    this.spawnParticles(this.player.x + 10, this.player.y + 10, heartColor, 18);
    this.addFloatingText(`♥ มิตรภาพกับ ${NPC_STORY[npcId]?.name} +${points}!`, this.player.x - 20, this.player.y - 25, heartColor);

    const textEl = document.getElementById('dialogueText');
    if (textEl) textEl.textContent = `"${quote}"`;

    // Refresh hearts in dialogue (up to 10 hearts)
    const heartsEl = document.getElementById('dialogueFriendshipHearts');
    if (heartsEl) {
        heartsEl.innerHTML = '';
        const hearts = Math.min(10, Math.floor(this.player.npcFriendship[npcId] / 20));
        for (let i = 1; i <= 10; i++) {
            const hSpan = document.createElement('span');
            hSpan.className = i <= hearts ? 'heart-filled' : 'heart-empty';
            hSpan.textContent = '♥';
            heartsEl.appendChild(hSpan);
        }
    }

    this.checkAchievements();
    this.updateHUD();
};


// ========================================================
// 20. ARTISAN MACHINERY & AUTOMATION
// ========================================================

Game.interactWithMachine = function(machineId: string) {
    if (!this.placedMachines) this.placedMachines = {};

    const machine = this.placedMachines[machineId];
    if (!machine) return;

    if (machine.state === 'ready' && machine.readyItem) {
        // Collect finished artisan item
        const readyId = machine.readyItem;
        this.addItemToInventory(readyId, 1);
        this.unlockCompendiumItem(readyId);
        SoundEngine.harvest();
        this.spawnParticles(machine.x * 32 + 16, machine.y * 32 + 16, '#facc15', 15);
        const itemInfo = WORLD_ITEMS[readyId] || { name: readyId };

        this.addFloatingText(` แปรรูปเสร็จสิ้น! ได้รับ ${itemInfo.name}`, this.player.x - 20, this.player.y - 20, '#fde047');
        machine.state = 'idle';
        machine.readyItem = null;
        machine.remainingMs = 0;
        this.checkAchievements();
        this.updateHUD();
        return;
    }

    if (machine.state === 'processing') {
        const sec = Math.ceil(machine.remainingMs / 1000);
        this.addFloatingText(` กำลังแปรรูป... (เหลือเวลาอีก ${sec} วินาที)`, this.player.x - 25, this.player.y - 15, '#38bdf8');
        return;
    }

    // Machine is idle: Check if player wants to pick it up with axe/pickaxe, or process an item
    const selIndex = this.player.selectedSlot;
    const selItem = this.player.inventory[selIndex];

    if (machine.state === 'idle' && selItem && (selItem.id === 'axe' || selItem.id === 'pickaxe')) {
        const mType = machine.type;
        const tx = machine.x;
        const ty = machine.y;
        delete this.placedMachines[machineId];
        if (this.map[ty]?.[tx]) {
            this.map[ty][tx].type = (this.currentScene === 'house' ? 'floorWood' : 'grass');
            this.map[ty][tx].solid = false;
            this.map[ty][tx].interactable = null;
        }
        this.spawnDroppedItem(mType, 1, tx * 32 + 16, ty * 32 + 16);
        SoundEngine.chopWood();
        this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#ca8a04', 12);
        this.addFloatingText('รื้อถอนเครื่องแปรรูปสำเร็จ!', this.player.x - 20, this.player.y - 20, '#4ade80');
        this.updateHUD();
        return;
    }

    if (!selItem) {
        this.addFloatingText(' ถือวัตถุดิบในมือแล้วคลิกที่เครื่องเพื่อเริ่มแปรรูป (ใช้ขวาน/อีเต๋อเพื่อรื้อถอน)', this.player.x - 30, this.player.y - 15, '#94a3b8');
        return;
    }

    const conv = Object.values(ARTISAN_CONVERSIONS).find(
        (c: any) => c.machineType === machine.type && c.inputItem === selItem.id
    );
    if (conv) {
        this.removeItemFromInventory(selItem.id, 1);
        machine.state = 'processing';
        machine.readyItem = conv.outputItem;
        machine.remainingMs = conv.durationMs;
        SoundEngine.craft();
        this.spawnParticles(machine.x * 32 + 16, machine.y * 32 + 16, '#38bdf8', 12);
        this.addFloatingText(` เริ่มแปรรูป ${conv.outputName}!`, this.player.x - 20, this.player.y - 20, '#38bdf8');
        this.updateHUD();
        return;
    }

    this.addFloatingText(' เครื่องจักรนี้ไม่สามารถแปรรูปวัตถุดิบชนิดนี้ได้', this.player.x - 25, this.player.y - 15, '#ef4444');
};


Game.updateMachines = function(dt: number) {
    if (!this.placedMachines) return;
    for (const id in this.placedMachines) {
        const m = this.placedMachines[id];
        if (m && m.state === 'processing') {
            m.remainingMs -= dt;
            if (m.remainingMs <= 0) {
                m.state = 'ready';
                m.remainingMs = 0;
                SoundEngine.bell();
            }
        }
    }
};


// ========================================================
// 21. PET COMPANION SYSTEM
// ========================================================

Game.updatePetCompanion = function(dt: number) {
    const pet = this.player.pet;
    if (!pet) return;

    if (!pet.barkCooldown) pet.barkCooldown = 0;
    if (pet.barkCooldown > 0) pet.barkCooldown -= dt;

    // 1. Dog Special Utility: Auto-Loot Fetching & Alert Barking
    if (pet.type === 'dog') {
        let closestItem: any = null;
        let closestDist = 220;
        if (this.droppedItems && this.droppedItems.length > 0) {
            for (let i = 0; i < this.droppedItems.length; i++) {
                const it = this.droppedItems[i];
                if (!it || it.timer < 300) continue;
                // Dog must never fetch manual drops (items dropped intentionally by player)
                if (it.manualPickup) continue;
                // Dog must only fetch if the player can actually carry it in their inventory!
                if (!this.canItemFitInInventory(it.id, it.count || 1, it.quality || 0)) continue;
                const d = Math.hypot(it.x - pet.x, it.y - pet.y);
                if (d < closestDist) {
                    closestDist = d;
                    closestItem = it;
                }
            }
        }

        if (closestItem) {
            const idx = closestItem.x - pet.x;
            const idy = closestItem.y - pet.y;
            const distItem = Math.hypot(idx, idy);

            if (distItem < 18) {
                if (!this.canItemFitInInventory(closestItem.id, closestItem.count || 1, closestItem.quality || 0)) {
                    return;
                }
                const itName = closestItem.name || closestItem.id;
                const added = this.addItemToInventory(closestItem.id, closestItem.count || 1, itName, closestItem.quality || 0, true);
                if (added) {
                    if (SoundEngine.dogBark) SoundEngine.dogBark();
                    this.spawnParticles(pet.x, pet.y, '#facc15', 12);
                    this.addFloatingText(' โฮ่ง! คาบ ' + itName + ' มาให้', pet.x, pet.y - 12, '#38bdf8');
                    const fIdx = this.droppedItems.indexOf(closestItem);
                    if (fIdx !== -1) this.droppedItems.splice(fIdx, 1);
                    this.updateHUD();
                }
            } else {
                const fetchSpeed = 4.8 * (dt / 16);
                pet.x += (idx / distItem) * Math.min(distItem, fetchSpeed);
                pet.y += (idy / distItem) * Math.min(distItem, fetchSpeed);
                pet.dir = Math.abs(idx) > Math.abs(idy) ? (idx > 0 ? 'right' : 'left') : (idy > 0 ? 'down' : 'up');
                pet.animTimer = (pet.animTimer || 0) + dt;
                if (pet.animTimer > 95) { pet.frame = ((pet.frame || 0) + 1) % 4; pet.animTimer = 0; }
                return;
            }
        }

        // Alert Barking at approaching monsters
        if (pet.barkCooldown <= 0) {
            const combatMonsters = this.currentScene === 'farm' ? this.demonBugs : this.worldMonsters;
            if (combatMonsters && combatMonsters.length > 0) {
                for (const m of combatMonsters) {
                    const md = Math.hypot((m.x + 16) - pet.x, (m.y + 16) - pet.y);
                    if (md < 95) {
                        pet.barkCooldown = 4500;
                        if (SoundEngine.dogBark) SoundEngine.dogBark();
                        this.addFloatingText(' โฮ่งๆ! ระวังมอนสเตอร์!', pet.x, pet.y - 16, '#f87171');
                        m.attackCooldown = 1800;
                        m.flashTimer = 220;
                        break;
                    }
                }
            }
        }

        // 2. Dog Active Combat Companion (Lunge, Bite, Stun & Boss Harass)
        if (!pet.combatCooldown) pet.combatCooldown = 0;
        if (pet.combatCooldown > 0) pet.combatCooldown -= dt;

        if (this.isCombatScene() && pet.combatCooldown <= 0) {
            let combatTarget: any = null;
            let targetDist = 240;

            if (this.boss && this.boss.alive && this.boss.active) {
                const bDist = Math.hypot((this.boss.x + 32) - pet.x, (this.boss.y + 32) - pet.y);
                if (bDist < 280) {
                    combatTarget = this.boss;
                    targetDist = bDist;
                }
            }

            if (!combatTarget) {
                const hostiles = this.currentScene === 'farm' ? this.demonBugs : this.worldMonsters;
                if (hostiles && hostiles.length > 0) {
                    for (const m of hostiles) {
                        const md = Math.hypot((m.x + 16) - pet.x, (m.y + 16) - pet.y);
                        if (md < targetDist) {
                            targetDist = md;
                            combatTarget = m;
                        }
                    }
                }
            }

            if (combatTarget) {
                const tx = (combatTarget === this.boss) ? (this.boss.x + 32) : (combatTarget.x + 16);
                const ty = (combatTarget === this.boss) ? (this.boss.y + 32) : (combatTarget.y + 16);
                const tdx = tx - pet.x;
                const tdy = ty - pet.y;
                const distToT = Math.hypot(tdx, tdy);

                if (distToT < 26) {
                    // Lunge Bite!
                    pet.combatCooldown = 3800;
                    if (SoundEngine.dogBark) SoundEngine.dogBark();
                    SoundEngine.hit();
                    const petDmg = Math.round(45 + (this.player.level || 1) * 8);

                    if (combatTarget === this.boss) {
                        this.damageBoss(petDmg);
                        this.boss.flashTimer = 350;
                        this.addFloatingText('★ บัดดี้กระโจนกัดบอส! -' + petDmg + ' HP', this.boss.x + 16, this.boss.y - 25, '#f59e0b');
                    } else {
                        combatTarget.hp -= petDmg;
                        combatTarget.flashTimer = 300;
                        combatTarget.stunTimer = 1400;
                        combatTarget.attackCooldown = 2000;
                        this.addFloatingText('★ บัดดี้กระโจนกัด! -' + petDmg + ' (สตัน 1.4s)', combatTarget.x, combatTarget.y - 20, '#f59e0b');
                    }
                    this.spawnParticles(pet.x, pet.y, '#facc15', 16);
                    this.triggerScreenShake(3.0, 100);
                } else {
                    // Rapid dash toward enemy
                    const chargeSpeed = 4.2 * (dt / 16);
                    pet.x += (tdx / distToT) * Math.min(distToT, chargeSpeed);
                    pet.y += (tdy / distToT) * Math.min(distToT, chargeSpeed);
                    pet.dir = Math.abs(tdx) > Math.abs(tdy) ? (tdx > 0 ? 'right' : 'left') : (tdy > 0 ? 'down' : 'up');
                    pet.animTimer = (pet.animTimer || 0) + dt;
                    if (pet.animTimer > 80) { pet.frame = ((pet.frame || 0) + 1) % 4; pet.animTimer = 0; }
                    return;
                }
            }
        }
    } else if (pet.type === 'cat') {
        // 2. Cat Special Utility: Daily Morning Gold Gift
        if (this.time && this.time.hour === 6 && !pet.dailyGiftGiven) {
            pet.dailyGiftGiven = true;
            if (SoundEngine.catMeow) SoundEngine.catMeow();
            const g = 150;
            this.player.gold += g;
            this.spawnParticles(pet.x, pet.y, '#facc15', 10);
            this.addFloatingText(' เหมียว! คุ้ยเจอเหรียญทองมาฝาก +' + g + ' G', pet.x, pet.y - 16, '#facc15');
            this.updateHUD();
        }
    }

    // Default: Follow player smoothly
    const targetX = this.player.x + (this.player.direction === 'left' ? 28 : -28);
    const targetY = this.player.y + 6;

    const dx = targetX - pet.x;
    const dy = targetY - pet.y;
    const dist = Math.hypot(dx, dy);

    if (dist > 320) {
        pet.x = targetX;
        pet.y = targetY;
    } else if (dist > 24) {
        const speed = (this.player.isMounted ? 4.5 : 2.6) * (dt / 16);
        pet.x += (dx / dist) * Math.min(dist, speed);
        pet.y += (dy / dist) * Math.min(dist, speed);

        pet.animTimer = (pet.animTimer || 0) + dt;
        if (pet.animTimer > 130) {
            pet.frame = ((pet.frame || 0) + 1) % 4;
            pet.animTimer = 0;
        }

        if (Math.abs(dx) > Math.abs(dy)) {
            pet.dir = dx > 0 ? 'right' : 'left';
        } else {
            pet.dir = dy > 0 ? 'down' : 'up';
        }
    } else {
        pet.frame = 0;
    }
};


Game.drawPetCompanion = function() {
    const pet = this.player.pet;
    if (!pet) return;
    const px = Math.round(pet.x - this.camera.x);
    const py = Math.round(pet.y - this.camera.y);

    // Soft Contact Shadow
    this.ctx.fillStyle = 'rgba(15, 23, 42, 0.28)';
    this.ctx.beginPath();
    this.ctx.ellipse(px + 12, py + 22, 10, 4.5, 0, 0, Math.PI * 2);
    this.ctx.fill();

    const frames = pet.type === 'cat' ? SPRITES.petCat : SPRITES.petDog;
    if (!frames || !frames.length) return;
    const fIdx = (pet.frame || 0) % frames.length;
    const spr = frames[fIdx] || frames[0];
    if (spr) {
        if (pet.dir === 'left') {
            this.ctx.save();
            this.ctx.translate(px + 24, py);
            this.ctx.scale(-1, 1);
            this.ctx.drawImage(spr, 0, 0);
            this.ctx.restore();
        } else {
            this.ctx.drawImage(spr, px, py);
        }
    }
};



// ========================================================
// 22. STAR QUALITY & SKILL MASTERY SYSTEM
// ========================================================

Game.rollItemQuality = function(source: 'farming' | 'fishing' | 'foraging' | 'mining' | 'combat', level: number = 1): 0 | 1 | 2 | 3 {
    let silverChance = 0.15 + level * 0.02;
    let goldChance = 0.08 + level * 0.015;
    let iridiumChance = 0.02 + level * 0.008;

    // Golden Touch Mastery Perk: All harvested crops & forages have boosted quality!
    if (this.player.skillMastery?.golden_touch) {
        silverChance += 0.25;
        goldChance += 0.20;
        iridiumChance += 0.15;
    }

    const roll = Math.random();
    if (roll < iridiumChance) return 3; // Iridium
    if (roll < iridiumChance + goldChance) return 2; // Gold
    if (roll < iridiumChance + goldChance + silverChance) return 1; // Silver
    return 0; // Regular
};


Game.getQualityBadgeText = function(quality?: number): string {
    if (quality === 3) return '★★★';
    if (quality === 2) return '★★';
    if (quality === 1) return '★';
    return '';
};


Game.toggleSkillMasteryModal = function() {
    const modal = document.getElementById('skillMasteryModal');
    if (!modal) return;
    const isVisible = modal.style.display !== 'none';
    if (isVisible) {
        this.closeModal('skillMasteryModal');
    } else {
        this.renderSkillMasteryModal();
        this.openModal('skillMasteryModal');
    }
};


Game.renderSkillMasteryModal = function() {
    if (this.player.masteryPoints === undefined) {
        // Calculate points: 1 point for every 5 skill levels reached across all skills
        let totalSkillLevels = 0;
        if (this.player.skills) {
            Object.values(this.player.skills).forEach((lvl: any) => totalSkillLevels += Number(lvl) || 0);
        }
        this.player.masteryPoints = Math.max(1, Math.floor(totalSkillLevels / 3));
    }
    if (!this.player.skillMastery) {
        this.player.skillMastery = {};

    }

    const ptsCountEl = document.getElementById('masteryPointsCount');
    if (ptsCountEl) ptsCountEl.textContent = String(this.player.masteryPoints);

    const grid = document.getElementById('skillMasteryGrid');
    if (!grid) return;
    grid.innerHTML = '';

    const branchNames: Record<string, string> = {
        farming: 'กสิกรรม (Farming)',
        mining: 'เหมืองแร่ (Mining)',
        fishing: 'ตกปลา (Fishing)',
        combat: 'ต่อสู้ (Combat)',
        artisan: 'การแปรรูป (Artisan)'
    };


    const perks = Object.values(SKILL_MASTERIES) as any[];
    perks.forEach(perk => {
        const isUnlocked = !!this.player.skillMastery[perk.id];
        const card = document.createElement('div');
        card.className = 'mastery-perk-card' + (isUnlocked ? ' unlocked' : '');

        const branchTitle = perk.branchName || branchNames[perk.branch] || perk.branch;
        const cost = perk.cost || 1;
        const canUnlock = (this.player.masteryPoints || 0) >= cost;

        card.innerHTML = `
            <div class="perk-header">
                <span class="perk-icon">${perk.icon}</span>
                <div>
                    <h3 class="perk-name">${perk.name}</h3>
                    <span class="perk-branch">${branchTitle}</span>
                </div>
            </div>
            <p class="perk-desc">${perk.desc}</p>
            <div class="perk-footer">
                ${isUnlocked ? '<span class="badge-unlocked">ปลดล็อกแล้ว</span>' :
                   (canUnlock ?
                    `<button class="btn-unlock-mastery" onclick="Game.unlockSkillMastery('${perk.id}')">เรียนรู้ทักษะ (${cost} แต้ม)</button>` :
                    '<span class="badge-locked">แต้มไม่เพียงพอ</span>')}
            </div>
        `;
        grid.appendChild(card);
    });
};


Game.unlockSkillMastery = function(perkId: string) {
    if (!this.player.masteryPoints || this.player.masteryPoints <= 0) {
        this.addFloatingText(' แต้มความชำนาญไม่เพียงพอ!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }
    const perk = (SKILL_MASTERIES as any)[perkId];
    if (!perk) return;

    this.player.masteryPoints -= 1;
    this.player.skillMastery[perkId] = true;

    SoundEngine.levelUp();
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#facc15', 30);
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#38bdf8', 20);
    this.addFloatingText(`★ ปลดล็อกสุดยอดทักษะ: ${perk.name}!`, this.player.x - 30, this.player.y - 25, '#fde047');

    this.renderSkillMasteryModal();
    this.updateHUD();
};


// ========================================================
// 23. GREENHOUSE, FARM CAVE & TROPICAL ISLAND
// ========================================================

Game.confirmFarmCaveChoice = function(choice: 'mushrooms' | 'bats') {
    this.player.farmCaveChoice = choice;
    this.closeModal('farmCaveChoiceModal');

    // Regenerate farm cave scene map
    this.scenes.farmCave = this.generateFarmCaveMap();

    SoundEngine.bell();
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#a855f7', 25);
    const choiceName = choice === 'mushrooms' ? 'ห้องเพาะเห็ดวิจัย (Mushroom Boxes)' : 'ถ้ำค้างคาวผลไม้สด (Fruit Bats)';
    this.addFloatingText(` พัฒนาถ้ำเป็น: ${choiceName} สำเร็จ!`, this.player.x - 30, this.player.y - 20, '#e9d5ff');

    this.switchScene('farmCave', 7, 11);
};


Game.harvestMushroomBox = function(tx: number, ty: number) {
    const mushrooms = ['mushroom_purple', 'mushroom_red', 'mushroom_chanterelle'];
    const chosen = mushrooms[Math.floor(Math.random() * mushrooms.length)];
    const quality = this.rollItemQuality('foraging', this.player.skills?.foraging || 1);
    const mInfo = WORLD_ITEMS[chosen] || { name: 'เห็ดสด' };


    this.addItemToInventory(chosen, 1, mInfo.name, quality);
    SoundEngine.harvest();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#c084fc', 14);

    const qBadge = this.getQualityBadgeText(quality);
    this.addFloatingText(` เก็บเกี่ยว ${mInfo.name} ${qBadge}! (+15 XP)`, tx * 32, ty * 32 - 15, '#e9d5ff');
    this.addXp(15);
    this.updateHUD();
};


Game.pickupCaveFruit = function(tx: number, ty: number) {
    const fruits = ['apple', 'strawberry', 'orange', 'plum'];
    const chosen = fruits[Math.floor(Math.random() * fruits.length)];
    const quality = this.rollItemQuality('foraging', this.player.skills?.foraging || 1);
    const fInfo = WORLD_ITEMS[chosen] || { name: 'ผลไม้ป่า' };


    this.addItemToInventory(chosen, 1, fInfo.name, quality);
    SoundEngine.itemPop();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#f472b6', 12);

    // Clear cave drop from tile
    this.map[ty][tx].type = 'darkStone';
    this.map[ty][tx].interactable = null;

    const qBadge = this.getQualityBadgeText(quality);
    this.addFloatingText(` เก็บผลไม้ถ้ำ: ${fInfo.name} ${qBadge}! (+10 XP)`, tx * 32, ty * 32 - 15, '#fbcfe8');
    this.addXp(10);
    this.updateHUD();
};


Game.initIslandScene = function() {
    this.boss = null;
    this.worldMonsters = [
        // Stoneback Crabs along the southern beaches
        { id: 'crab1', type: 'island_crab', x: 12 * 32, y: 26 * 32, hp: 140, maxHp: 140, speed: 0.9, damage: 16, aggroRange: 150, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'crab2', type: 'island_crab', x: 19 * 32, y: 28 * 32, hp: 140, maxHp: 140, speed: 0.9, damage: 16, aggroRange: 150, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'crab3', type: 'island_crab', x: 28 * 32, y: 27 * 32, hp: 140, maxHp: 140, speed: 0.9, damage: 16, aggroRange: 150, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'crab4', type: 'island_crab', x: 35 * 32, y: 25 * 32, hp: 140, maxHp: 140, speed: 0.9, damage: 16, aggroRange: 150, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        // Cursed Pirate Skeletons guarding the Shipwreck Cove at West beach
        { id: 'pirate1', type: 'cursed_pirate_skeleton', x: 6 * 32, y: 20 * 32, hp: 210, maxHp: 210, speed: 1.5, damage: 26, aggroRange: 200, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'pirate2', type: 'cursed_pirate_skeleton', x: 9 * 32, y: 22 * 32, hp: 210, maxHp: 210, speed: 1.5, damage: 26, aggroRange: 200, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 },
        { id: 'pirate3', type: 'cursed_pirate_skeleton', x: 7 * 32, y: 25 * 32, hp: 210, maxHp: 210, speed: 1.5, damage: 26, aggroRange: 200, attackCooldown: 0, direction: 'down', frame: 0, animTimer: 0 }
    ];
};

Game.openSailboatRepairModal = function() {
    this.closeAllModals();
    this.activeModal = 'sailboatRepairModal';
    const modal = document.getElementById('sailboatRepairModal');
    if (!modal) return;

    const woodCount = this.getItemCount('wood');
    const ironCount = this.getItemCount('iron_ore');
    const goldCount = this.player.gold || 0;

    const woodEl = document.getElementById('repairReqWood');
    const ironEl = document.getElementById('repairReqIron');
    const goldEl = document.getElementById('repairReqGold');
    const btnRepair = document.getElementById('btnConfirmSailboatRepair') as HTMLButtonElement;
    const btnSailNow = document.getElementById('btnSailNow') as HTMLButtonElement;

    if (woodEl) {
        woodEl.textContent = `${woodCount} / 20`;
        woodEl.style.color = woodCount >= 20 ? '#4ade80' : '#ef4444';
    }
    if (ironEl) {
        ironEl.textContent = `${ironCount} / 5`;
        ironEl.style.color = ironCount >= 5 ? '#4ade80' : '#ef4444';
    }
    if (goldEl) {
        goldEl.textContent = `${goldCount} / 500 G`;
        goldEl.style.color = goldCount >= 500 ? '#4ade80' : '#ef4444';
    }

    const canRepair = woodCount >= 20 && ironCount >= 5 && goldCount >= 500;
    if (btnRepair) {
        btnRepair.disabled = !canRepair;
        btnRepair.textContent = canRepair ? 'บูรณะเรือใบ (+100 XP)' : 'ต้องการวัสดุครบเพื่อบูรณะ (+100 XP)';
    }
    if (btnSailNow) {
        btnSailNow.disabled = false;
        btnSailNow.textContent = 'ออกเรือสู่เกาะเขตร้อนทันที';
    }

    modal.style.display = 'flex';
};

Game.repairSailboat = function() {
    const woodCount = this.getItemCount('wood');
    const ironCount = this.getItemCount('iron_ore');
    const goldCount = this.player.gold || 0;

    if (woodCount < 20 || ironCount < 5 || goldCount < 500) {
        SoundEngine.errorClick();
        this.addFloatingText('วัสดุไม่เพียงพอสำหรับบูรณะเรือ!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }

    this.removeItemFromInventory('wood', 20);
    this.removeItemFromInventory('iron_ore', 5);
    this.player.gold -= 500;
    this.player.sailboatRepaired = true;

    this.closeAllModals();
    SoundEngine.levelUp();
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#38bdf8', 35);
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#facc15', 25);
    this.triggerScreenShake(4.0, 150);
    this.addFloatingText('★ บูรณะเรือใบโบราณสำเร็จ! ปลดล็อกเส้นทางสู่เกาะเขตร้อน!', this.player.x - 40, this.player.y - 25, '#38bdf8');
    this.updateHUD();

    setTimeout(() => {
        this.travelToIsland();
    }, 1200);
};

Game.travelToIsland = function() {
    SoundEngine.bell();
    this.switchScene('island', 23, 29);
    this.spawnParticles(23 * 32, 29 * 32, '#38bdf8', 30);
    this.addFloatingText('ล่องเรือข้ามสมุทรมาถึงเกาะมหาสมบัติเขตร้อนแล้ว!', this.player.x - 30, this.player.y - 20, '#38bdf8');
};

Game.forageIslandPineapple = function(tx: number, ty: number) {
    const quality = this.rollItemQuality('foraging', this.player.skills?.foraging || 1);
    this.addItemToInventory('pineapple', 1, 'สับปะรดภูเขาไฟเขตร้อน', quality);
    this.addXp(25);
    SoundEngine.harvest();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#facc15', 16);
    const qBadge = this.getQualityBadgeText(quality);
    this.addFloatingText(`เก็บสับปะรดป่าเขตร้อน ${qBadge}! (+25 XP)`, tx * 32, ty * 32 - 15, '#fde047');
    this.map[ty][tx].type = 'sand';
    this.map[ty][tx].interactable = null;
    this.updateHUD();
};

Game.forageIslandCoconut = function(tx: number, ty: number) {
    const quality = this.rollItemQuality('foraging', this.player.skills?.foraging || 1);
    this.addItemToInventory('coconut', 1, 'มะพร้าวป่าสด', quality);
    this.addXp(20);
    SoundEngine.itemPop();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#78350f', 14);
    const qBadge = this.getQualityBadgeText(quality);
    this.addFloatingText(`เก็บมะพร้าวป่า ${qBadge}! (+20 XP)`, tx * 32, ty * 32 - 15, '#fef08a');
    this.map[ty][tx].type = 'sand';
    this.map[ty][tx].interactable = null;
    this.updateHUD();
};

Game.forageIslandBanana = function(tx: number, ty: number) {
    const quality = this.rollItemQuality('foraging', this.player.skills?.foraging || 1);
    this.addItemToInventory('banana', 1, 'กล้วยหอมทอง (Golden Banana)', quality);
    this.addXp(20);
    SoundEngine.harvest();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#facc15', 14);
    const qBadge = this.getQualityBadgeText(quality);
    this.addFloatingText(`เก็บกล้วยหอมทอง ${qBadge}! (+20 XP)`, tx * 32, ty * 32 - 15, '#fde047');
    this.map[ty][tx].type = 'sand';
    this.map[ty][tx].interactable = null;
    this.updateHUD();
};

Game.forageIslandSeashell = function(tx: number, ty: number) {
    this.addItemToInventory('seashell', 1, 'เปลือกหอยมุกสีรุ้ง', 0);
    this.addXp(15);
    SoundEngine.itemPop();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#f472b6', 12);
    this.addFloatingText(`เก็บเปลือกหอยมุกสีรุ้ง! (+15 XP)`, tx * 32, ty * 32 - 15, '#fbcfe8');
    this.map[ty][tx].type = 'sand';
    this.map[ty][tx].interactable = null;
    this.updateHUD();
};

Game.forageIslandMessageBottle = function(tx: number, ty: number) {
    this.addItemToInventory('message_bottle', 1, 'ขวดแก้วลายแทงสมบัติ', 0);
    this.addItemToInventory('pirate_doubloon', 2, 'เหรียญทองโบราณโจรสลัด', 0);
    this.addXp(30);
    SoundEngine.levelUp();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#38bdf8', 20);
    this.addFloatingText('เปิดขวดแก้ว: พบลายแทงสมบัติ & +2 เหรียญทองโบราณ!', tx * 32, ty * 32 - 20, '#38bdf8');
    this.map[ty][tx].type = 'sand';
    this.map[ty][tx].interactable = null;
    this.updateHUD();
};

Game.shakePalmTree = function(tx: number, ty: number) {
    SoundEngine.hit();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 10, '#22c55e', 12);
    const roll = Math.random();
    if (roll < 0.45) {
        this.spawnDroppedItem('coconut', 1, tx * 32 + 16, ty * 32 + 24);
        this.addFloatingText('มะพร้าวร่วงหล่นลงมา!', tx * 32, ty * 32 - 15, '#fef08a');
    } else if (roll < 0.70) {
        this.spawnDroppedItem('banana', 1, tx * 32 + 16, ty * 32 + 24);
        this.addFloatingText('กล้วยหอมทองร่วงหล่นลงมา!', tx * 32, ty * 32 - 15, '#fde047');
    } else {
        this.addFloatingText('ใบมะพร้าวพลิ้วไหวตามสายลม', tx * 32, ty * 32 - 15, '#86efac');
    }
};

Game.inspectPirateShipwreck = function() {
    SoundEngine.miningHit();
    this.spawnParticles(this.player.x, this.player.y, '#78350f', 15);
    this.addFloatingText('ซากเรือโจรสลัดแบล็กฮาวด์: มีหีบสมบัติต้องสาปตั้งอยู่ใกล้ๆ!', this.player.x - 30, this.player.y - 20, '#fde047');
};

Game.openPirateChest = function() {
    if (this.player.pirateChestOpened) {
        SoundEngine.errorClick();
        this.addFloatingText('หีบสมบัติโจรสลัดถูกเปิดไปแล้ว!', this.player.x, this.player.y - 15, '#94a3b8');
        return;
    }

    const keyCount = this.getItemCount('skeleton_key');
    if (keyCount < 1) {
        SoundEngine.errorClick();
        this.addFloatingText('หีบถูกล็อกด้วยอาถรรพ์! ต้องใช้กุญแจโครงกระดูกโจรสลัด (Skeleton Key)', this.player.x - 40, this.player.y - 15, '#ef4444');
        return;
    }

    this.removeItemFromInventory('skeleton_key', 1);
    this.player.pirateChestOpened = true;

    const rewardGold = 600;
    this.player.gold += rewardGold;
    this.addItemToInventory('pirate_doubloon', 5, 'เหรียญทองโบราณโจรสลัด', 0);
    this.addItemToInventory('golden_melon_seed', 3, 'เมล็ดเมลอนทองคำ', 0);
    this.addItemToInventory('diamond_crystal', 2, 'เพชรคริสตัลโบราณ', 0);

    SoundEngine.levelUp();
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#facc15', 30);
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#38bdf8', 25);
    this.triggerScreenShake(5.0, 180);
    this.addFloatingText(`★ ปลดล็อกสมบัติโจรสลัด! (+${rewardGold} G, +5 เหรียญโบราณ, เมล็ดเมลอนทองคำ & เพชร!)`, this.player.x - 50, this.player.y - 30, '#facc15');
    this.updateHUD();
};

Game.openPirateShopModal = function() {
    this.closeAllModals();
    this.activeModal = 'pirateShopModal';
    const modal = document.getElementById('pirateShopModal');
    if (!modal) return;

    this.renderPirateShopModal();
    modal.style.display = 'flex';
};

Game.renderPirateShopModal = function() {
    const countEl = document.getElementById('pirateDoubloonCount');
    const doubloonCount = this.getItemCount('pirate_doubloon');
    if (countEl) countEl.textContent = doubloonCount.toString();

    const container = document.getElementById('pirateShopItemsList');
    if (!container || typeof PIRATE_SHOP_ITEMS === 'undefined') return;

    let html = '';
    Object.values(PIRATE_SHOP_ITEMS).forEach((item: any) => {
        const canAfford = doubloonCount >= item.priceDoubloons;
        html += `
            <div class="pirate-shop-card">
                <div class="pirate-card-header">
                    <strong class="pirate-card-title">${item.name}</strong>
                    <span class="pirate-card-price">${item.priceDoubloons} เหรียญโบราณ</span>
                </div>
                <p class="pirate-card-desc">${item.desc}</p>
                <div class="pirate-card-footer">
                    <button class="btn-primary pirate-buy-btn" 
                            ${canAfford ? '' : 'disabled'}
                            onclick="Game.buyPirateShopItem('${item.id}')">
                        ${canAfford ? 'แลกเปลี่ยน' : 'เหรียญไม่พอ'}
                    </button>
                </div>
            </div>
        `;
    });
    container.innerHTML = html;
};

Game.buyPirateShopItem = function(itemId: string) {
    if (typeof PIRATE_SHOP_ITEMS === 'undefined') return;
    const item: any = (PIRATE_SHOP_ITEMS as any)[itemId];
    if (!item) return;

    const doubloonCount = this.getItemCount('pirate_doubloon');
    if (doubloonCount < item.priceDoubloons) {
        SoundEngine.errorClick();
        this.addFloatingText('เหรียญทองโบราณไม่เพียงพอ!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }

    if (this.isInventoryFull()) {
        SoundEngine.errorClick();
        this.addFloatingText('กระเป๋าเต็มแล้ว!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }

    this.removeItemFromInventory('pirate_doubloon', item.priceDoubloons);

    if (item.id === 'island_warp_totem') {
        this.addItemToInventory('island_warp_totem', 3, 'เสาวาร์ปเกาะเขตร้อน', 0);
    } else if (item.id === 'golden_melon_seed') {
        this.addItemToInventory('golden_melon_seed', 5, 'เมล็ดเมลอนทองคำเกาะโจรสลัด', 0);
    } else if (item.id === 'starfruit_seed') {
        this.addItemToInventory('starfruit_seed', 5, 'เมล็ดผลไม้ดาวแคริบเบียน', 0);
    } else if (item.id === 'tropical_delight_drink') {
        this.addItemToInventory('tropical_delight_drink', 3, 'ค็อกเทลเขตร้อนสูตรกัปตัน', 0);
    } else {
        this.addItemToInventory(item.id, 1, item.name, 0);
    }

    SoundEngine.cashRegister();
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#facc15', 20);
    this.addFloatingText(`แลกรับ ${item.name} สำเร็จ!`, this.player.x - 20, this.player.y - 20, '#facc15');
    this.renderPirateShopModal();
    this.updateHUD();
};


// ========================================================
// 24. SEASONAL VILLAGE FESTIVALS
// ========================================================

Game.getCurrentFestival = function() {
    const sIdx = this.time.seasonIndex;
    const day = this.time.day;
    const festivals = Object.values(FESTIVALS) as any[];
    return festivals.find(f => f.seasonIndex === sIdx && f.day === day) || null;
};


Game.checkFestivalBanner = function() {
    const fest = this.getCurrentFestival();
    const banner = document.getElementById('hudFestivalBanner');
    const nameEl = document.getElementById('hudFestivalName');
    if (!banner || !nameEl) return;

    if (fest) {
        nameEl.textContent = fest.name;
        banner.style.display = 'flex';
    } else {
        banner.style.display = 'none';
    }
};


Game.openFestivalModal = function() {
    const fest = this.getCurrentFestival() || (FESTIVALS as any)['spring_egg_hunt'];
    const modal = document.getElementById('festivalModal');
    const titleEl = document.getElementById('festivalModalTitle');
    const contentEl = document.getElementById('festivalModalBodyContent');
    if (!modal || !titleEl || !contentEl) return;

    const rewards: Record<string, string> = {
        spring_egg_hunt: 'ถ้วยรางวัลไข่ทองคำ & เงินรางวัล 1,000 G + ไข่อีสเตอร์หายาก',
        summer_fishing_derby: 'รางวัลชนะเลิศ & แต้มปลาสองเท่า + 1,500 G',
        fall_harvest_fair: 'ริบบิ้นรางวัลชนะเลิศ & เงินรางวัล 1,000 G',
        winter_star_feast: 'เพชรล้ำค่าแห่งดวงดาวฤดูหนาว (คุณภาพอิริเดียม ★★★)'
    };

    const rewardText = rewards[fest.id] || 'ของขวัญและเกียรติยศประจำฤดูกาล';

    titleEl.textContent = fest.name;
    contentEl.innerHTML = `
        <div style="font-size: 15px; color: #f8fafc; line-height: 1.6; margin-bottom: 12px;">
            ${fest.desc}
        </div>
        <div style="background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="color: #facc15; font-weight: bold; margin-bottom: 4px;">รางวัลกิจกรรมเทศกาล:</div>
            <div style="color: #cbd5e1;">${rewardText}</div>
        </div>
    `;

    this.openModal('festivalModal');
};


Game.closeFestivalModal = function() {
    this.closeModal('festivalModal');
};


Game.startFestivalMiniGame = function() {
    const fest = this.getCurrentFestival();
    this.closeFestivalModal();

    if (!fest || fest.id === 'spring_egg_hunt') {
        // Spring Egg Hunt: Spawn 10 Easter Eggs in current scene
        let spawned = 0;
        for (let i = 0; i < 25 && spawned < 10; i++) {
            const rx = Math.floor(Math.random() * (this.mapWidth - 4)) + 2;
            const ry = Math.floor(Math.random() * (this.mapHeight - 4)) + 2;
            const tile = this.map[ry]?.[rx];
            if (tile && !tile.solid && !tile.interactable && tile.type !== 'water') {
                tile.type = 'easterEgg';
                tile.interactable = 'collect_easter_egg';
                spawned++;
            }
        }
        SoundEngine.levelUp();
        this.addFloatingText(' กิจกรรมล่าไข่อีสเตอร์เริ่มขึ้นแล้ว! ตามเก็บไข่หลากสีรอบตัว!', this.player.x - 40, this.player.y - 20, '#fde047');
    } else if (fest.id === 'summer_fishing_derby') {
        SoundEngine.bell();
        this.addFloatingText(' งานแข่งขันตกปลาฤดูร้อน! ตกปลาได้แต้มและทองคูณสอง!', this.player.x - 30, this.player.y - 20, '#38bdf8');
    } else if (fest.id === 'fall_harvest_fair') {
        SoundEngine.levelUp();
        this.player.gold += 1000;
        this.addFloatingText(' ผลผลิตฟาร์มของคุณชนะการประกวดงานเทศกาลฤดูใบไม้ร่วง! (+1,000G)', this.player.x - 40, this.player.y - 20, '#f59e0b');
    } else if (fest.id === 'winter_star_feast') {
        SoundEngine.bell();
        this.addItemToInventory('diamond', 1, 'เพชรล้ำค่าแห่งดวงดาวฤดูหนาว', 3);
        this.addFloatingText('★ ชาวบ้านมอบของขวัญแห่งดวงดาวฤดูหนาวให้คุณ! (ได้รับ เพชรคุณภาพอิริเดียม )', this.player.x - 40, this.player.y - 20, '#c084fc');
    }
};


Game.collectEasterEgg = function(tx: number, ty: number) {
    SoundEngine.itemPop();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#f43f5e', 16);
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#facc15', 12);

    this.player.gold += 150;
    this.addItemToInventory('easter_egg', 1, 'ไข่อีสเตอร์หลากสี');
    this.map[ty][tx].type = 'grass';
    this.map[ty][tx].interactable = null;

    this.addFloatingText(' เก็บไข่อีสเตอร์สำเร็จ! (+150 G)', tx * 32, ty * 32 - 15, '#fde047');
    this.updateHUD();
};


// ========================================================
// 25. ROMANCE, PROPOSALS, WEDDINGS & SPOUSE INTERACTION
// ========================================================

Game.startWeddingCutscene = function(spouseId: string) {
    this.player.spouse = spouseId;
    const spouse = NPC_STORY[spouseId] || { name: 'คู่ชีวิต' };


    const modal = document.getElementById('weddingCutsceneModal');
    const nameEl = document.getElementById('weddingSpouseName');
    const vowEl = document.getElementById('weddingVowText');
    if (!modal || !nameEl || !vowEl) return;

    nameEl.textContent = `♥ ${spouse.name} & คุณ`;
    vowEl.textContent = `"ต่อหน้าสักขีพยานชาวหมู่บ้านศิลาสุขาวดี... ทั้งสองจะร่วมแบ่งปันรอยยิ้ม กลิ่นอายดิน และสร้างฟาร์มแห่งความรักด้วยกันตลอดไป"`;

    // Draw player and spouse faces on canvases
    const pCanvas = document.getElementById('weddingPlayerCanvas') as HTMLCanvasElement;
    if (pCanvas) {
        const pCtx = pCanvas.getContext('2d');
        if (pCtx) {
            pCtx.clearRect(0, 0, 48, 48);
            const pSpr = SPRITES.player?.down?.[0];
            if (pSpr) pCtx.drawImage(pSpr, 12, 8, 24, 32);
        }
    }

    const sCanvas = document.getElementById('weddingSpouseCanvas') as HTMLCanvasElement;
    if (sCanvas) {
        const sCtx = sCanvas.getContext('2d');
        if (sCtx) {
            sCtx.clearRect(0, 0, 48, 48);
            const sSpr = (SPRITES.npcs as any)[spouseId]?.down?.[0] || SPRITES.npcs.lilian?.down?.[0];
            if (sSpr) sCtx.drawImage(sSpr, 12, 8, 24, 32);
        }
    }

    SoundEngine.levelUp();
    this.openModal('weddingCutsceneModal');
};


Game.finishWeddingCutscene = function() {
    this.closeModal('weddingCutsceneModal');
    SoundEngine.bell();

    // Teleport both to farmhouse bed
    this.switchScene('house', 12, 10);
    this.spawnParticles(12 * 32, 10 * 32, '#ec4899', 35);
    this.spawnParticles(12 * 32, 10 * 32, '#fde047', 25);

    const spouseName = NPC_STORY[this.player.spouse]?.name || 'คู่รัก';
    this.addFloatingText(` พิธีแต่งงานเสร็จสมบูรณ์! ยินดีต้อนรับ ${spouseName} เข้าสู่บ้านฟาร์มสุขใจ!`, this.player.x - 40, this.player.y - 25, '#f472b6');
    this.updateHUD();
};


Game.interactWithSpouse = function() {
    if (!this.player.spouse) return;
    const spouseId = this.player.spouse;
    const spouseName = NPC_STORY[spouseId]?.name || 'คู่รัก';

    if (!this.player.spouseKissedToday) {
        this.player.spouseKissedToday = true;
        this.player.energy = Math.min(this.player.maxEnergy, this.player.energy + 25);
        this.player.hp = Math.min(this.player.maxHp, this.player.hp + 15);

        SoundEngine.bell();
        this.spawnParticles(this.player.x + 12, this.player.y + 16, '#f43f5e', 20);
        this.addFloatingText(` จุมพิตยามเช้ากับ ${spouseName}! ( พลังงาน +25 / ♥ HP +15)`, this.player.x - 30, this.player.y - 25, '#f472b6');
    } else {
        const quotes = [
            'บ้านของเราอบอุ่นที่สุดเลยนะ ข้าดีใจที่ได้แต่งงานกับเจ้า ♥',
            'สู้ๆ กับงานในฟาร์มวันนี้นะที่รัก ข้าจะเป็นกำลังใจให้เสมอ!',
            'วันนี้ลมพัดเย็นสบายจัง อยากออกไปเดินเล่นในสวนดอกไม้กับเจ้าจัง'
        ];
        const q = quotes[Math.floor(Math.random() * quotes.length)];
        this.addFloatingText(`♥ ${spouseName}: "${q}"`, this.player.x - 30, this.player.y - 20, '#fbcfe8');
    }
};


if (typeof window !== 'undefined') {
    (window as any).Game = Game;
    (window as any).SoundEngine = SoundEngine;
    (window as any).SPRITES = SPRITES;
    (window as any).Auth = Auth;
    (window as any).CROPS = CROPS;
    (window as any).ANIMALS = ANIMALS;
    (window as any).RECIPES = RECIPES;
    (window as any).FISH = FISH;
    (window as any).TOOLS = TOOLS;
    (window as any).UPGRADES = UPGRADES;
    (window as any).LEVEL_XP = LEVEL_XP;
    (window as any).SEASONS = SEASONS;
    (window as any).DAYS_PER_SEASON = DAYS_PER_SEASON;
    (window as any).HOUSE_DECOR_UPGRADES = HOUSE_DECOR_UPGRADES;
    (window as any).OUTFIT_OPTIONS = OUTFIT_OPTIONS;
    (window as any).NPC_CUSTOMERS = NPC_CUSTOMERS;
    (window as any).DEMON_BUGS = DEMON_BUGS;
    (window as any).WEAPONS = WEAPONS;
    (window as any).HUNTERS = HUNTERS;
    (window as any).FARM_HELPERS = FARM_HELPERS;
    (window as any).MONSTER_DROPS = MONSTER_DROPS;
    (window as any).WORLD_ITEMS = WORLD_ITEMS;
    (window as any).WORLD_MONSTERS = WORLD_MONSTERS;
    (window as any).BOSS_KATHUROS = BOSS_KATHUROS;
    (window as any).QUESTS = QUESTS;
    (window as any).NPC_STORY = NPC_STORY;
    (window as any).FORGE_RECIPES = FORGE_RECIPES;
    (window as any).NPC_GIFTS = NPC_GIFTS;
    (window as any).COMPENDIUM_CATEGORIES = COMPENDIUM_CATEGORIES;
    (window as any).ACHIEVEMENTS_DATA = ACHIEVEMENTS_DATA;
    (window as any).ARTISAN_CONVERSIONS = ARTISAN_CONVERSIONS;

    if (document.readyState === 'loading') {
        window.addEventListener('DOMContentLoaded', () => Game.init());
    } else {
        Game.init();
    }
}


// ========================================================
// 26. DODGE ROLL / DASH SYSTEM
// ========================================================

Game.playerDash = function() {
    if (this.player.isDashing || this.player.isDead) return;
    if (this.player.dashCooldown && this.player.dashCooldown > 0) return;
    const dashCost = (this.player.buffs?.staminaSurge) ? 0 : 4;
    if (this.player.energy < dashCost) {
        this.addFloatingText('★ พลังงานไม่พอสำหรับกลิ้งหลบ!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }

    this.player.energy = Math.max(0, this.player.energy - dashCost);
    this.player.dashCooldown = 600; // 600ms cooldown
    this.player.isDashing = true;
    this.player.dashTimer = 220; // 220ms active roll duration
    this.player.invincibleTimer = 260; // 260ms of Dark Souls I-frames!

    let dx = 0;
    let dy = 0;
    if (this.keys.up) dy -= 1;
    if (this.keys.down) dy += 1;
    if (this.keys.left) dx -= 1;
    if (this.keys.right) dx += 1;

    if (dx === 0 && dy === 0) {
        if (this.player.direction === 'up') dy = -1;
        else if (this.player.direction === 'down') dy = 1;
        else if (this.player.direction === 'left') dx = -1;
        else if (this.player.direction === 'right') dx = 1;
    }

    if (dx !== 0 && dy !== 0) { dx *= 0.7071; dy *= 0.7071; }
    this.player.dashDir = { x: dx, y: dy };

    SoundEngine.dash();
    this.spawnParticles(this.player.x + 10, this.player.y + 24, '#94a3b8', 8);
    this.spawnParticles(this.player.x + 10, this.player.y + 24, '#38bdf8', 4);

    // Astreon Storm Greaves: Lightning burst on roll!
    if (this.player.equippedShield === 'astreon_storm_greaves') {
        const stormDmg = 60;
        this.damageEnemiesInRadius(this.player.x + 12, this.player.y + 14, 110, stormDmg, '★ สายฟ้าออสทริออน! -' + stormDmg, '#38bdf8');
        SoundEngine.thunder();
        this.spawnParticles(this.player.x + 10, this.player.y + 24, '#38bdf8', 14);
    }

    this.updateHUD();
};


// ========================================================
// 26.1 GUARD / PERFECT PARRY SYSTEM
// ========================================================

Game.startPlayerGuard = function() {
    if (this.player.isDead || this.player.isDashing) return;
    if (this.player.guardBreakTimer && this.player.guardBreakTimer > 0) {
        this.addFloatingText('[การป้องกันแตกพ่าย] ยังไม่สามารถยกโล่ได้!', this.player.x - 20, this.player.y - 15, '#ef4444');
        return;
    }
    if (this.player.isGuarding) return;

    this.player.isGuarding = true;
    this.player.guardTimer = 0;
    SoundEngine.shieldUp();

    this.activeSkillVisuals = this.activeSkillVisuals || [];
    this.activeSkillVisuals.push({
        type: 'shield_activate',
        x: this.player.x + 12,
        y: this.player.y + 14,
        timer: 200,
        maxTimer: 200
    });
};

Game.stopPlayerGuard = function() {
    if (!this.player.isGuarding) return;
    this.player.isGuarding = false;
    this.player.guardTimer = 0;
};

Game.triggerPlayerParry = function(source: any = null) {
    SoundEngine.parrySuccess();
    this.triggerHitstop(120);
    this.triggerScreenShake(7.5, 260);

    // Dark Souls generous parry immunity
    this.player.invincibleTimer = 400;

    // Energy recovery reward for clutch perfect timing (+15 Stamina)
    this.player.energy = Math.min(this.player.maxEnergy || 100, (this.player.energy || 0) + 15);

    this.activeSkillVisuals = this.activeSkillVisuals || [];
    this.activeSkillVisuals.push({
        type: 'parry_flash',
        x: this.player.x + 12,
        y: this.player.y + 14,
        timer: 400,
        maxTimer: 400,
        radius: 65
    });

    this.spawnParticles(this.player.x + 12, this.player.y + 14, '#fbbf24', 24);
    this.spawnParticles(this.player.x + 12, this.player.y + 14, '#ffffff', 16);
    this.spawnParticles(this.player.x + 12, this.player.y + 14, '#38bdf8', 12);
    this.addFloatingText('[ PERFECT PARRY! ] ปัดป้องสมบูรณ์แบบ (+15 SP)', this.player.x - 45, this.player.y - 32, '#fbbf24');

    // Ignistron Magma Shield: Erupt flaming wave!
    if (this.player.equippedShield === 'ignistron_flame_shield') {
        const flameDmg = 110;
        this.damageEnemiesInRadius(this.player.x + 12, this.player.y + 14, 130, flameDmg, '★ เพลิงผลาญอิกนิสทรอน! -' + flameDmg, '#ea580c');
        SoundEngine.bossMeteor();
        this.spawnParticles(this.player.x + 12, this.player.y + 14, '#ea580c', 20);
        this.spawnParticles(this.player.x + 12, this.player.y + 14, '#facc15', 14);
        this.triggerScreenShake(5.0, 150);
    }

    // Malakor Void Shroud: Soul leech on parry!
    if (this.player.equippedArmor === 'malakor_void_cloak') {
        const vHeal = Math.max(5, Math.round((this.player.maxHp || 100) * 0.06));
        this.player.hp = Math.min(this.player.maxHp || 100, this.player.hp + vHeal);
        this.addFloatingText('+' + vHeal + ' HP (มฤตยูดูดเลือด)', this.player.x - 20, this.player.y - 20, '#c084fc');
        this.spawnParticles(this.player.x + 12, this.player.y + 14, '#c084fc', 10);
    }

    // Synergistic Buddy Combo Bite on Parry!
    if (this.player.pet && this.player.pet.type === 'dog') {
        this.player.pet.combatCooldown = 0;
        this.spawnParticles(this.player.pet.x, this.player.pet.y, '#fbbf24', 12);
        this.addFloatingText('★ บัดดี้ประสานคอมโบ! (PARRY COMBO)', this.player.pet.x - 20, this.player.pet.y - 20, '#fbbf24');
    }

    // Reaction against attacker
    if (source) {
        if (source.vx !== undefined && source.vy !== undefined) {
            // Deflect Projectile back at enemy with amplified damage!
            source.vx = -source.vx * 1.8;
            source.vy = -source.vy * 1.8;
            source.fromPlayer = true;
            source.fromBoss = false;
            source.damage = Math.round((source.damage || 20) * 2.2);
            source.color = '#fbbf24';
            this.addFloatingText('★ DEFLECTED! ★', source.x, source.y - 15, '#fbbf24');
        } else if (source === this.boss || (source && source.id && source.id.startsWith('boss_'))) {
            // Boss Stagger / Posture Break!
            source.state = 'parried';
            source.flashTimer = 500;
            const counterDmg = Math.round(60 + (this.player.level || 1) * 16);
            this.damageBoss(counterDmg);
            this.addFloatingText('POSTURE BROKEN! -' + counterDmg + ' HP', source.x + 16, source.y - 35, '#f59e0b');
        } else if (source.hp !== undefined) {
            // Regular monster stagger
            source.stunTimer = 1600;
            source.flashTimer = 400;
            const counterDmg = Math.round(45 + (this.player.level || 1) * 12);
            source.hp = Math.max(0, source.hp - counterDmg);
            this.addFloatingText('STUNNED! -' + counterDmg, source.x, source.y - 20, '#f59e0b');
            SoundEngine.hit();
        }
    } else if (this.boss && this.boss.alive) {
        // If source not explicitly passed but boss is nearby, stagger boss
        const bDist = Math.hypot((this.boss.x + 32) - (this.player.x + 12), (this.boss.y + 32) - (this.player.y + 14));
        if (bDist < 260) {
            this.boss.state = 'parried';
            this.boss.flashTimer = 500;
            const counterDmg = Math.round(50 + (this.player.level || 1) * 14);
            this.damageBoss(counterDmg);
            this.addFloatingText('POSTURE BROKEN! -' + counterDmg + ' HP', this.boss.x + 16, this.boss.y - 35, '#f59e0b');
        }
    }

    this.updateHUD();
};

Game.triggerGuardBreak = function() {
    this.player.isGuarding = false;
    this.player.guardBreakTimer = 1800; // 1.8 seconds stun
    this.player.energy = 0;
    SoundEngine.guardBreak();
    this.triggerScreenShake(8.0, 320);
    this.triggerHitstop(90);

    this.activeSkillVisuals = this.activeSkillVisuals || [];
    this.activeSkillVisuals.push({
        type: 'guard_break',
        x: this.player.x + 12,
        y: this.player.y + 14,
        timer: 450,
        maxTimer: 450
    });

    this.spawnParticles(this.player.x + 12, this.player.y + 14, '#ef4444', 24);
    this.spawnParticles(this.player.x + 12, this.player.y + 14, '#f87171', 16);
    this.addFloatingText('[ GUARD BREAK! ] การป้องกันแตกพ่าย!', this.player.x - 30, this.player.y - 30, '#ef4444');
    this.updateHUD();
};


// ========================================================
// 27. ELEMENTAL RUNES ENCHANTING & COMBAT PROCS
// ========================================================

Game.enchantWeapon = function(runeId: string) {
    const runeType = runeId.replace('rune_', '') as 'fire' | 'frost' | 'lightning' | 'vampiric';
    const runeNames: Record<string, string> = {
        fire: 'รูนอัคคีพิโรธ (Burn DoT)',
        frost: 'รูนเหมันต์นิรันดร์ (Slow 50%)',
        lightning: 'รูนอัสนีบาต (Chain Lightning)',
        vampiric: 'รูนกลืนวิญญาณ (Life Steal 8%)'
    };

    if (this.countItemInInventory(runeId) <= 0) {
        this.addFloatingText('ไม่มีรูนชนิดนี้ในกระเป๋า!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }

    this.player.equippedRune = runeType;
    SoundEngine.bell();
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#c084fc', 20);
    this.addFloatingText('[สลักรูนสำเร็จ] อาวุธได้รับพลังแห่ง ' + runeNames[runeType] + '!', this.player.x - 30, this.player.y - 25, '#facc15');
    this.updateHUD();
};

Game.applyRuneCombatProc = function(target: any, damageDealt: number) {
    if (!this.player.equippedRune || !target) return;
    const rune = this.player.equippedRune;

    if (rune === 'fire') {
        SoundEngine.runeFire();
        this.spawnParticles(target.x + 16, target.y + 16, '#ef4444', 10);
        this.spawnParticles(target.x + 16, target.y + 16, '#f97316', 8);
        const burnDmg = Math.max(8, Math.round(damageDealt * 0.28));
        target.hp = Math.max(0, target.hp - burnDmg);
        this.addFloatingText('เผาไหม้ -' + burnDmg, target.x + 10, target.y - 18, '#f97316');
    } else if (rune === 'frost') {
        SoundEngine.runeFrost();
        this.spawnParticles(target.x + 16, target.y + 16, '#38bdf8', 12);
        target.speed = (target.speed || 1.8) * 0.5;
        setTimeout(() => { if (target) target.speed = (target.speed || 0.9) * 2; }, 2800);
        this.addFloatingText('เยือกแข็ง (Slow 50%)', target.x, target.y - 18, '#38bdf8');
    } else if (rune === 'lightning') {
        SoundEngine.runeLightning();
        this.spawnParticles(target.x + 16, target.y + 16, '#facc15', 14);
        const chainDmg = Math.max(10, Math.round(damageDealt * 0.35));
        // Chain to nearby monsters
        if (this.worldMonsters && this.worldMonsters.length > 0) {
            let chained = 0;
            this.worldMonsters.forEach(m => {
                if (m !== target && m.alive && chained < 2) {
                    const d = Math.hypot(m.x - target.x, m.y - target.y);
                    if (d < 140) {
                        m.hp = Math.max(0, m.hp - chainDmg);
                        this.spawnParticles(m.x + 16, m.y + 16, '#fde047', 8);
                        this.addFloatingText('สายฟ้าชิ่ง -' + chainDmg, m.x, m.y - 16, '#facc15');
                        chained++;
                    }
                }
            });
        }
    } else if (rune === 'vampiric') {
        SoundEngine.runeVampiric();
        const heal = Math.max(2, Math.round(damageDealt * 0.08));
        this.player.hp = Math.min(this.player.maxHp, this.player.hp + heal);
        this.spawnParticles(this.player.x + 10, this.player.y + 14, '#c084fc', 8);
        this.addFloatingText('+' + heal + ' HP (กลืนวิญญาณ)', this.player.x - 10, this.player.y - 22, '#c084fc');
        this.updateHUD();
    }
};

// ========================================================
// 28. NPC HEART EVENTS SYSTEM
// ========================================================

Game.triggerHeartEvent = function(eventId: string) {
    const event = (NPC_HEART_EVENTS as any)?.[eventId];
    if (!event) return;

    this.activeHeartEvent = event;
    const modal = document.getElementById('heartEventModal');
    const titleEl = document.getElementById('heartEventTitle');
    const nameEl = document.getElementById('heartEventNpcName');
    const storyEl = document.getElementById('heartEventStoryText');
    const rewardEl = document.getElementById('heartEventRewardBadge');
    const choicesEl = document.getElementById('heartEventChoicesContainer');
    const reactionEl = document.getElementById('heartEventReactionBox');
    if (!modal || !titleEl || !nameEl || !storyEl || !choicesEl) return;

    titleEl.textContent = event.title;
    const npc = NPC_STORY[event.npcId] || { name: 'ชาวเมือง' };
    nameEl.textContent = npc.name;
    if (rewardEl) rewardEl.textContent = event.rewardDesc;
    storyEl.textContent = event.story;
    if (reactionEl) reactionEl.style.display = 'none';

    // Draw portrait
    const cvs = document.getElementById('heartEventPortraitCanvas') as HTMLCanvasElement | null;
    if (cvs) {
        const ctx = cvs.getContext('2d');
        if (ctx) {
            ctx.imageSmoothingEnabled = false;
            ctx.clearRect(0, 0, 56, 56);
            const pSpr = SPRITES.portraits?.[event.npcId] || SPRITES.portraits?.lilian;
            if (pSpr) ctx.drawImage(pSpr, 4, 4, 48, 48);
        }
    }

    // Render choice buttons
    choicesEl.innerHTML = '';
    event.choices.forEach((c: any, idx: number) => {
        const btn = document.createElement('button');
        btn.className = 'heart-choice-btn';
        btn.textContent = c.text;
        btn.onclick = () => this.chooseHeartEventOption(idx);
        choicesEl.appendChild(btn);
    });

    SoundEngine.bell();
    this.closeDialogue();
    this.openModal('heartEventModal');
};

Game.chooseHeartEventOption = function(choiceIdx: number) {
    if (!this.activeHeartEvent) return;
    const event = this.activeHeartEvent;
    const choice = event.choices[choiceIdx];
    if (!choice) return;

    const reactionEl = document.getElementById('heartEventReactionBox');
    const choicesEl = document.getElementById('heartEventChoicesContainer');
    if (choicesEl) choicesEl.innerHTML = '';

    if (reactionEl) {
        reactionEl.textContent = choice.response;
        reactionEl.style.display = 'block';
    }

    // Apply friendship bonus
    if (!this.player.npcFriendship) this.player.npcFriendship = {};
    this.player.npcFriendship[event.npcId] = (this.player.npcFriendship[event.npcId] || 0) + (choice.friendshipBonus || 30);

    // Apply stat reward
    if (event.rewardType === 'hp') {
        this.player.maxHp += event.rewardValue;
        this.player.hp = this.player.maxHp;
    } else if (event.rewardType === 'damage') {
        this.player.bonusBaseDamage = (this.player.bonusBaseDamage || 0) + event.rewardValue;
    } else if (event.rewardType === 'energy') {
        this.player.maxEnergy += event.rewardValue;
        this.player.energy = this.player.maxEnergy;
    }

    if (!this.player.seenHeartEvents) this.player.seenHeartEvents = {};
    this.player.seenHeartEvents[event.id] = true;

    SoundEngine.questComplete();
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#f472b6', 25);
    this.addFloatingText('[ความผูกพันลึกซึ้ง] ' + event.rewardDesc, this.player.x - 30, this.player.y - 25, '#fbcfe8');
    this.updateHUD();

    // Auto close after 3 seconds
    setTimeout(() => {
        this.closeHeartEventModal();
    }, 3200);
};

Game.closeHeartEventModal = function() {
    this.activeHeartEvent = null;
    this.closeModal('heartEventModal');
};

// ========================================================
// 29. ANCIENT SHRINE EPILOGUE & MASTER MODE
// ========================================================

Game.interactWithShrineAltar = function() {
    const requiredShards = [
        'sacred_shard_earth',
        'sacred_shard_sun',
        'sacred_shard_water',
        'sacred_shard_fire',
        'sacred_shard_frost',
        'sacred_shard_shadow',
        'sacred_shard_nature',
        'sacred_shard_thunder'
    ];

    if (!this.player.sacredShards) this.player.sacredShards = {};
    // Auto-credit shards if bosses were already defeated
    if (this.player.defeatedBosses?.boss_kathuros) this.player.sacredShards['sacred_shard_earth'] = true;
    if (this.player.defeatedBosses?.boss_luminarch) this.player.sacredShards['sacred_shard_sun'] = true;
    if (this.player.defeatedBosses?.boss_hydrakis) this.player.sacredShards['sacred_shard_water'] = true;
    if (this.player.defeatedBosses?.boss_ignistron) this.player.sacredShards['sacred_shard_fire'] = true;
    if (this.player.defeatedBosses?.boss_frostfang) this.player.sacredShards['sacred_shard_frost'] = true;
    if (this.player.defeatedBosses?.boss_malakor) this.player.sacredShards['sacred_shard_shadow'] = true;
    if (this.player.defeatedBosses?.boss_sylvanus) this.player.sacredShards['sacred_shard_nature'] = true;
    if (this.player.defeatedBosses?.boss_astreon) this.player.sacredShards['sacred_shard_thunder'] = true;

    let count = 0;
    requiredShards.forEach(sh => {
        if (this.player.sacredShards[sh] || this.countItemInInventory(sh) > 0) count++;
    });

    if (count >= 8) {
        if (!this.player.grandSovereignAwakened) {
            this.player.grandSovereignAwakened = true;
            this.player.gold += 50000;
            this.addXp(20000);
            this.triggerScreenShake(9.0, 500);
            SoundEngine.shrineEpilogue();
            this.addFloatingText('★ ปลดผนึก 8 ศิลาเทพบรรพกาลสำเร็จ! ได้รับฉายา "มหาจักรพรรดิผู้พิทักษ์แห่งจักรวาลและแผ่นดินสุขาวดี" (+50,000 G, +20,000 XP)', this.player.x - 50, this.player.y - 30, '#fde047');
        }
        this.startShrineEpilogueCutscene();
    } else if (count >= 6) {
        this.startShrineEpilogueCutscene();
    } else {
        SoundEngine.bell();
        this.addFloatingText(`★ แท่นบูชาศักดิ์สิทธิ์: ครอบครองแก่นศิลาศักดิ์สิทธิ์ ${count}/8 ชิ้น (ต้องปราบมหาบอสทั้ง 8 ตน)`, this.player.x - 40, this.player.y - 25, '#fde047');
    }
};

Game.startShrineEpilogueCutscene = function() {
    SoundEngine.shrineEpilogue();
    this.triggerScreenShake(8.0, 400);

    // Flash screen white
    const flash = document.createElement('div');
    flash.className = 'photo-flash-overlay';
    document.body.appendChild(flash);
    requestAnimationFrame(() => {
        flash.style.opacity = '0.9';
        setTimeout(() => {
            flash.style.opacity = '0';
            setTimeout(() => flash.remove(), 400);
        }, 300);
    });

    this.player.shrineRestored = true;
    this.player.gold += 25000;
    this.addXp(10000);
    this.updateHUD();

    this.openModal('shrineEpilogueModal');
};

Game.finishShrineEpilogue = function() {
    this.closeModal('shrineEpilogueModal');
    SoundEngine.questComplete();
    this.addFloatingText('ได้รับฉายา "มหาผู้กอบกู้แห่งศิลาสุขาวดี" และพรแห่งเทพถาวร!', this.player.x - 40, this.player.y - 25, '#facc15');
};

Game.toggleMasterMode = function() {
    this.player.masterMode = !this.player.masterMode;
    const btn = document.getElementById('btnToggleMasterMode');
    if (btn) {
        btn.textContent = this.player.masterMode ? 'Master Mode: เปิดใช้งานอยู่ (มอนสเตอร์ดรอปของเทพ x2)' : 'เปิดใช้งาน Master Mode';
    }
    SoundEngine.bell();
    this.addFloatingText(this.player.masterMode ? '[Master Mode] ความท้าทายระดับสูงเปิดใช้งานแล้ว!' : '[Normal Mode] กลับสู่ความยากปกติ', this.player.x - 30, this.player.y - 20, '#38bdf8');
};

// ========================================================
// 30. INFINITE CRYSTAL SPIRE (THE ENDLESS DUNGEON)
// ========================================================

Game.generateSpireMap = function(floor: number) {
    this.spireCurrentFloor = floor;
    const w = 26;
    const h = 26;
    const map = [];

    for (let y = 0; y < h; y++) {
        const row = [];
        for (let x = 0; x < w; x++) {
            const isBorder = (x === 0 || x === w - 1 || y === 0 || y === h - 1);
            if (isBorder) {
                row.push({ x, y, type: 'darkStone', solid: true });
            } else if ((x === 6 || x === 19) && (y === 6 || y === 19)) {
                // Crystal pillars
                row.push({ x, y, type: 'crystalPillar', solid: true });
            } else {
                row.push({ x, y, type: 'darkStone', solid: false });
            }
        }
        map.push(row);
    }

    // Spire Relic Shop Altar at (13, 8)
    map[8][13].type = 'spire_shop_relic';
    map[8][13].interactable = 'spire_shop_relic';
    map[8][13].solid = true;

    // Portal back to village at (13, 23)
    map[23][13].type = 'spire_portal';
    map[23][13].interactable = 'exit_spire_to_village';

    // Portal to next floor in center (13, 14)
    map[14][13].type = 'spire_portal';
    map[14][13].interactable = 'spire_next_floor';

    // Spawn Spire monsters directly into this.worldMonsters
    this.worldMonsters = [];
    const count = 3 + Math.min(8, Math.floor(floor * 0.7));
    for (let i = 0; i < count; i++) {
        const isBoss = (floor % 5 === 0 && i === 0);
        const mx = (Math.floor(Math.random() * 16) + 5) * 32;
        const my = (Math.floor(Math.random() * 10) + 4) * 32;
        this.worldMonsters.push({
            id: 'spire_' + floor + '_' + i,
            type: isBoss ? 'spire_colossus' : 'spire_demon',
            name: isBoss ? `ผู้พิทักษ์หอคอยชั้น ${floor}` : `อสูรผลึกมิติ ชั้น ${floor}`,
            x: mx,
            y: my,
            hp: isBoss ? (350 + floor * 45) : (130 + floor * 22),
            maxHp: isBoss ? (350 + floor * 45) : (130 + floor * 22),
            speed: isBoss ? 1.1 : 1.5 + Math.min(0.8, floor * 0.04),
            damage: isBoss ? (28 + floor * 4) : (16 + floor * 3),
            alive: true,
            flashTimer: 0,
            frame: 0,
            animTimer: 0,
            gold: isBoss ? (180 + floor * 20) : (40 + floor * 6),
            xp: isBoss ? (140 + floor * 20) : (25 + floor * 5),
            drops: [
                { item: 'spire_shard', chance: isBoss ? 1.0 : 0.95 }
            ]
        });
    }

    this.scenes.spire = { mapWidth: w, mapHeight: h, map: map };
    this.loadScene('spire');
    this.player.x = 13 * 32;
    this.player.y = 21 * 32;
    this.player.spireProgress = Math.max(this.player.spireProgress || 1, floor);
    SoundEngine.spirePortal();
    this.addFloatingText(`เข้าสู่หอคอยมิติ ชั้นที่ ${floor}!`, this.player.x - 20, this.player.y - 20, '#38bdf8');
    this.updateHUD();

    return map;
};

Game.openSpireShopModal = function() {
    const modal = document.getElementById('spireShopModal');
    const shardEl = document.getElementById('spireShardCount');
    const floorEl = document.getElementById('spireCurrentFloorLabel');
    const listEl = document.getElementById('spireShopItemsList');
    if (!modal || !listEl) return;

    const shards = this.countItemInInventory('spire_shard');
    if (shardEl) shardEl.textContent = String(shards);
    if (floorEl) floorEl.textContent = 'ชั้นปัจจุบัน: ' + (this.spireCurrentFloor || 1);

    const items = [
        { id: 'spire_blade', name: 'ดาบสุริยันผลึกหอคอย (พลังโจมตี 260)', desc: 'ดาบเทวตำนาน ฟันคลื่นสุริยันทะลวงศัตรูอย่างรุนแรง', cost: 15 },
        { id: 'spire_bow', name: 'ธนูประกายดาราผลึก (พลังโจมตี 130x3)', desc: 'คันธนูมิติ แผลงศรแสงดารา 3 ดอกพร้อมกัน', cost: 15 },
        { id: 'spire_staff', name: 'คทาแก่นหอคอยมิติ (พลังโจมตี 300)', desc: 'คทามหาเวท ปลดปล่อยลูกพลังเนบิวลาระเบิดกว้าง', cost: 20 },
        { id: 'diamond_crystal', name: 'เพชรผลึกประกายรุ้ง x3', desc: 'อัญมณีล้ำค่าใช้ตีอาวุธระดับสูงและขายได้ราคาสูง', cost: 5 },
        { id: 'antidote_serum', name: 'เซรุ่มต้านสปอร์พิษ x5', desc: 'ฟื้นฟูพลังชีวิตและรักษาพิษทุกชนิด', cost: 3 }
    ];

    listEl.innerHTML = '';
    items.forEach(it => {
        const canAfford = shards >= it.cost;
        const row = document.createElement('div');
        row.className = 'spire-shop-item';
        row.innerHTML = `
            <img src="${SPRITES.getItemDataURL(it.id)}" class="spire-item-icon">
            <div class="spire-item-details">
                <div class="spire-item-name">${it.name}</div>
                <div class="spire-item-desc">${it.desc}</div>
            </div>
            <button class="btn-spire-buy" ${canAfford ? '' : 'disabled'} onclick="Game.buySpireItem('${it.id}', ${it.cost})">
                แลก (${it.cost} ผลึก)
            </button>
        `;
        listEl.appendChild(row);
    });

    this.openModal('spireShopModal');
};

Game.buySpireItem = function(itemId: string, cost: number) {
    const shards = this.countItemInInventory('spire_shard');
    if (shards < cost) {
        this.addFloatingText('ผลึกหอคอยมิติไม่เพียงพอ!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }

    this.removeItemFromInventory('spire_shard', cost);
    this.addItemToInventory(itemId, itemId.includes('x') ? 3 : 1);
    SoundEngine.questComplete();
    this.addFloatingText('แลกรับ ' + itemId + ' สำเร็จแล้ว!', this.player.x - 20, this.player.y - 20, '#c084fc');
    this.openSpireShopModal();
    this.updateHUD();
};

// ========================================================
// 31. ATMOSPHERE & AMBIENT EFFECTS (FIREFLIES, LEAVES, SNOW, SMOKE)
// ========================================================

Game.updateAmbientEffects = function(dt: number) {
    if (!this.ambientParticles) {
        this.ambientParticles = { fireflies: [], leaves: [], footprints: [], smoke: [] };
    }

    const hour = this.time.hour;
    const season = this.time.seasonIndex;
    const isExterior = ['farm', 'village', 'forest', 'island'].includes(this.currentScene);

    // 1. Night Fireflies (18:00 - 05:00)
    if (isExterior && (hour >= 18 || hour < 5)) {
        if (this.ambientParticles.fireflies.length < 18) {
            this.ambientParticles.fireflies.push({
                x: Math.random() * this.width,
                y: Math.random() * this.height,
                baseY: Math.random() * this.height,
                vx: (Math.random() - 0.5) * 0.6,
                pulse: Math.random() * Math.PI * 2,
                size: Math.random() * 2 + 2
            });
        }
    } else {
        this.ambientParticles.fireflies = [];
    }

    this.ambientParticles.fireflies.forEach((f: any) => {
        f.x += f.vx;
        f.pulse += 0.05;
        f.y = f.baseY + Math.sin(f.pulse) * 12;
        if (f.x < 0) f.x = this.width;
        if (f.x > this.width) f.x = 0;
    });

    // 2. Autumn Leaves (Season 2 = Fall)
    if (isExterior && season === 2) {
        if (this.ambientParticles.leaves.length < 14) {
            this.ambientParticles.leaves.push({
                x: Math.random() * (this.width + 100),
                y: -10,
                vx: -1.2 - Math.random() * 0.8,
                vy: 0.8 + Math.random() * 0.7,
                rot: Math.random() * Math.PI,
                color: Math.random() < 0.5 ? '#f97316' : '#ea580c'
            });
        }
    } else {
        this.ambientParticles.leaves = [];
    }

    for (let i = this.ambientParticles.leaves.length - 1; i >= 0; i--) {
        const l = this.ambientParticles.leaves[i];
        l.x += l.vx;
        l.y += l.vy;
        l.rot += 0.04;
        if (l.y > this.height + 20 || l.x < -20) {
            this.ambientParticles.leaves.splice(i, 1);
        }
    }

    // 3. Snow Footprints Decay
    if (this.ambientParticles.footprints) {
        for (let i = this.ambientParticles.footprints.length - 1; i >= 0; i--) {
            const fp = this.ambientParticles.footprints[i];
            fp.alpha -= dt * 0.28;
            if (fp.alpha <= 0) {
                this.ambientParticles.footprints.splice(i, 1);
            }
        }
    }

    // 4. Chimney Smoke
    if (this.currentScene === 'farm' || this.currentScene === 'village') {
        if (Math.random() < 0.12) {
            const chimneyWorldX = this.currentScene === 'farm' ? 4 * 32 + 54 : 47 * 32 + 54;
            const chimneyWorldY = this.currentScene === 'farm' ? 2 * 32 + 10 : 29 * 32 + 10;
            this.ambientParticles.smoke.push({
                x: chimneyWorldX,
                y: chimneyWorldY,
                vx: -0.3 + Math.random() * 0.6,
                vy: -0.7 - Math.random() * 0.5,
                alpha: 0.6,
                size: 4
            });
        }
    }

    for (let i = this.ambientParticles.smoke.length - 1; i >= 0; i--) {
        const sm = this.ambientParticles.smoke[i];
        sm.x += sm.vx;
        sm.y += sm.vy;
        sm.size += 0.06;
        sm.alpha -= 0.012;
        if (sm.alpha <= 0) {
            this.ambientParticles.smoke.splice(i, 1);
        }
    }
};

Game.drawAmbientEffects = function() {
    if (!this.ambientParticles) return;

    // 1. Draw Chimney Smoke (in world coords)
    if (this.ambientParticles.smoke && this.ambientParticles.smoke.length > 0) {
        this.ctx.fillStyle = 'rgba(241, 245, 249, 0.45)';
        this.ambientParticles.smoke.forEach((sm: any) => {
            const sx = Math.round(sm.x - this.camera.x);
            const sy = Math.round(sm.y - this.camera.y);
            this.ctx.save();
            this.ctx.globalAlpha = sm.alpha;
            this.ctx.beginPath();
            this.ctx.arc(sx, sy, sm.size, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.restore();
        });
    }

    // 2. Draw Footprints on Snow
    if (this.ambientParticles.footprints && this.ambientParticles.footprints.length > 0) {
        this.ambientParticles.footprints.forEach((fp: any) => {
            const sx = Math.round(fp.x - this.camera.x);
            const sy = Math.round(fp.y - this.camera.y);
            this.ctx.save();
            this.ctx.globalAlpha = fp.alpha * 0.4;
            this.ctx.fillStyle = '#cbd5e1';
            this.ctx.fillRect(sx, sy, 3, 2);
            this.ctx.restore();
        });
    }

    // 3. Draw Autumn Leaves (screen coords)
    if (this.ambientParticles.leaves && this.ambientParticles.leaves.length > 0) {
        this.ambientParticles.leaves.forEach((l: any) => {
            this.ctx.save();
            this.ctx.translate(l.x, l.y);
            this.ctx.rotate(l.rot);
            this.ctx.fillStyle = l.color;
            this.ctx.fillRect(-3, -2, 6, 4);
            this.ctx.restore();
        });
    }

    // 4. Draw Night Fireflies (screen coords)
    if (this.ambientParticles.fireflies && this.ambientParticles.fireflies.length > 0) {
        this.ambientParticles.fireflies.forEach((f: any) => {
            const glow = (Math.sin(f.pulse) + 1) * 0.5;
            this.ctx.save();
            this.ctx.globalCompositeOperation = 'lighter';
            this.ctx.fillStyle = `rgba(254, 240, 138, ${0.25 + glow * 0.65})`;
            this.ctx.beginPath();
            this.ctx.arc(f.x, f.y, f.size + glow * 2, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.restore();
        });
    }
};

// ========================================================
// 32. FARM SNAPSHOT / PHOTO MODE
// ========================================================

Game.takeFarmSnapshot = function() {
    SoundEngine.cameraShutter();

    // Trigger visual camera flash
    const flash = document.createElement('div');
    flash.className = 'photo-flash-overlay';
    document.body.appendChild(flash);
    requestAnimationFrame(() => {
        flash.style.opacity = '0.9';
        setTimeout(() => {
            flash.style.opacity = '0';
            setTimeout(() => flash.remove(), 350);
        }, 150);
    });

    try {
        const offscreen = document.createElement('canvas');
        offscreen.width = this.width;
        offscreen.height = this.height;
        const oCtx = offscreen.getContext('2d');
        if (oCtx && this.canvas) {
            oCtx.drawImage(this.canvas, 0, 0);

            // Watermark stamp in corner
            oCtx.fillStyle = 'rgba(15, 23, 42, 0.75)';
            oCtx.fillRect(10, this.height - 36, 260, 26);
            oCtx.fillStyle = '#fde047';
            oCtx.font = 'bold 12px "Prompt", sans-serif';
            oCtx.fillText('ฟาร์มสุขใจ - Happy Farm 2D', 18, this.height - 19);

            const link = document.createElement('a');
            link.download = 'happy-farm-snapshot-' + Date.now() + '.png';
            link.href = offscreen.toDataURL('image/png');
            link.click();

            this.addFloatingText('[ถ่ายรูปสำเร็จ] บันทึกภาพถ่ายฟาร์มเรียบร้อยแล้ว!', this.player.x - 40, this.player.y - 25, '#fde047');
        }
    } catch (e) {
        this.addFloatingText('ถ่ายรูปสำเร็จ!', this.player.x, this.player.y - 15, '#4ade80');
    }
};

export default Game;



// ========================================================
// ACTIVE COMBAT SKILL SYSTEM (4 Classes x 4 Skills)
// Zero AI-slop emojis - 100% pure chiptune retro RPG
// ========================================================
export interface SkillConfig {
    id: string;
    slot: number;
    name: string;
    enName: string;
    tag: string;
    baseDmg: number;
    dmgPerLv: number;
    cd: number;
    energy: number;
    isUltimate?: boolean;
    desc: string;
}

export interface ClassConfig {
    id: string;
    name: string;
    tag: string;
    desc: string;
    skills: SkillConfig[];
}

export const CLASS_SKILLS: Record<string, ClassConfig> = {
    warrior: {
        id: 'warrior',
        name: 'สายจอมดาบ (Blade Master)',
        tag: '[ดาบ]',
        desc: 'เน้นการฟันระยะประชิด คลื่นสะบั้นคมดาบรอบทิศ และเกราะเหล็กสะท้อนดาเมจ',
        skills: [
            { id: 'cyclone_slash', slot: 1, name: 'คลื่นพายุคมดาบ', enName: 'Cyclone Slash', tag: '[ดาบ 1]', baseDmg: 140, dmgPerLv: 35, cd: 3500, energy: 12, desc: 'หมุนตัวฟัน 360 องศา ดูดศัตรูเข้ามาและสะบั้นรอบตัว รัศมี 140px (+สเกลพลังอาวุธ)' },
            { id: 'flash_thrust', slot: 2, name: 'พุ่งทะลวงพริบตา', enName: 'Flash Thrust', tag: '[ดาบ 2]', baseDmg: 180, dmgPerLv: 45, cd: 4800, energy: 14, desc: 'พุ่งทะลวงไปข้างหน้าตามทิศทางเมาส์ 180px ฟันทะลวงศัตรูเป็นแนวกว้าง (+สเกลพลังอาวุธ)' },
            { id: 'ironclad_bastion', slot: 3, name: 'ปราการเกราะเหล็ก', enName: 'Ironclad Bastion', tag: '[ดาบ 3]', baseDmg: 0, dmgPerLv: 0, cd: 10000, energy: 16, desc: 'กางบาเรียสีทอง ลดดาเมจที่ได้รับ 75% เป็นเวลา 6 วินาที พร้อมสะท้อนความเสียหาย 50%' },
            { id: 'judgement_blade', slot: 4, name: 'สุริยันพิฆาตสะบั้นหล้า', enName: 'Judgement Blade', tag: '[ดาบ 4]', baseDmg: 550, dmgPerLv: 120, cd: 15000, energy: 24, isUltimate: true, desc: '[อัลติเมท] ดาบยักษ์สุริยันฟาดถล่มพื้น รัศมี 220px ระเบิดมหาดาเมจพร้อมทำให้บอสเสียหลักสตัน' }
        ]
    },
    mage: {
        id: 'mage',
        name: 'สายจอมเวท (Elementalist)',
        tag: '[เวท]',
        desc: 'เน้นพลังเวทมนตร์ธาตุ ไฟเผาผลาญ น้ำแข็งแช่แข็ง และฝนดาวตกกลืนนภา',
        skills: [
            { id: 'pyroclast_orb', slot: 1, name: 'บอลเพลิงโลกันตร์', enName: 'Pyroclast Orb', tag: '[เวท 1]', baseDmg: 150, dmgPerLv: 40, cd: 3800, energy: 14, desc: 'ยิงบอลเพลิงขนาดใหญ่พุ่งตรงตามเมาส์ เมื่อกระทบจะระเบิดเป็นทะเลเพลิงรัศมี 110px' },
            { id: 'glacial_ring', slot: 2, name: 'วงแหวนเหมันต์เยือกแข็ง', enName: 'Glacial Ring', tag: '[เวท 2]', baseDmg: 130, dmgPerLv: 35, cd: 5500, energy: 15, desc: 'ระเบิดไอเย็นรอบตัว รัศมี 160px แช่แข็งและสโลว์ศัตรู 80% นาน 4 วินาที' },
            { id: 'prism_shield', slot: 3, name: 'ม่านพายุปริซึม', enName: 'Prism Shield', tag: '[เวท 3]', baseDmg: 65, dmgPerLv: 18, cd: 9500, energy: 16, desc: 'สร้างลูกแก้วปริซึม 3 ลูกโคจรรอบตัว คอยยิงเลเซอร์ใส่มอนสเตอร์รอบข้างอัตโนมัติ 10 วินาที' },
            { id: 'meteor_cataclysm', slot: 4, name: 'ฝนดาวตกกลืนนภา', enName: 'Meteor Cataclysm', tag: '[เวท 4]', baseDmg: 650, dmgPerLv: 140, cd: 16000, energy: 26, isUltimate: true, desc: '[อัลติเมท] อัญเชิญห่าอุกกาบาตยักษ์ 6 ลูกร่วงถล่มจุดเล็งเมาส์ ระเบิดล้างบางทั่วสนามรบ' }
        ]
    },
    ranger: {
        id: 'ranger',
        name: 'สายจอมพราน (Shadow Hunter)',
        tag: '[พราน]',
        desc: 'เน้นความว่องไว ยิงธนูกระจาย วางกับดักหนามพิษ และศรอัสนีบาตทะลวงเกราะ',
        skills: [
            { id: 'arrow_barrage', slot: 1, name: 'ฝนธนูเจาะเกราะ', enName: 'Arrow Barrage', tag: '[พราน 1]', baseDmg: 55, dmgPerLv: 15, cd: 3400, energy: 12, desc: 'ยิงห่าธนูเจาะเกราะ 7 ดอกพุ่งตรงตามทิศทางเมาส์ ทะลวงศัตรูทั้งหมดในเส้นทาง' },
            { id: 'venom_trap', slot: 2, name: 'กับดักลวดหนามพิษ', enName: 'Venom Trap', tag: '[พราน 2]', baseDmg: 160, dmgPerLv: 40, cd: 5200, energy: 14, desc: 'วางกับดักสปอร์พิษบนพื้น รัศมี 90px ตรึงขาศัตรูและทำพิษรุนแรงกัดกร่อนเกราะบอส' },
            { id: 'shadow_dash', slot: 3, name: 'ก้าวเงาล่องหน', enName: 'Shadow Dash', tag: '[พราน 3]', baseDmg: 0, dmgPerLv: 0, cd: 7000, energy: 10, desc: 'ก้าวเงาล่องหน ไร้เทียมทานสมบูรณ์ (I-Frames 1.8 วิ) พร้อมวิ่งไวขึ้น +60%' },
            { id: 'dragonpiercer', slot: 4, name: 'ธนูอัสนีพิฆาตมังกร', enName: 'Dragonpiercer', tag: '[พราน 4]', baseDmg: 580, dmgPerLv: 130, cd: 15000, energy: 24, isUltimate: true, desc: '[อัลติเมท] รวมพลังยิงศรสายฟ้ายักษ์เจาะทะลุสิ่งกีดขวาง 800px แนวกว้าง ช็อตสตันศัตรูทั้งหมด' }
        ]
    },
    paladin: {
        id: 'paladin',
        name: 'สายอัศวินศักดิ์สิทธิ์ (Paladin)',
        tag: '[เทวะ]',
        desc: 'เน้นพลังศักดิ์สิทธิ์แห่งแสง ฟื้นฟูพลังชีวิต ปักเสาคุ้มภัย และทัณฑ์สวรรค์พิพากษา',
        skills: [
            { id: 'radiant_spear', slot: 1, name: 'หอกแสงพิพากษา', enName: 'Radiant Spear', tag: '[เทวะ 1]', baseDmg: 150, dmgPerLv: 40, cd: 3600, energy: 12, desc: 'ปาหอกแสงศักดิ์สิทธิ์พุ่งตรงตามเมาส์ ระเบิดคลื่นแสงกระแทก 100px เมื่อกระทบ' },
            { id: 'divine_heal', slot: 2, name: 'อวยพรเทวะชำระล้าง', enName: 'Divine Benediction', tag: '[เทวะ 2]', baseDmg: 0, dmgPerLv: 0, cd: 8000, energy: 18, desc: 'สวดภาวนาฟื้นฟู HP +120 (+35/Lv) ฟื้นพลังงาน +30 SP และลบล้างพิษ/สโลว์ทั้งหมด' },
            { id: 'sanctuary_pylon', slot: 3, name: 'เสาเพลิงชำระล้าง', enName: 'Sanctuary Pylon', tag: '[เทวะ 3]', baseDmg: 75, dmgPerLv: 20, cd: 9500, energy: 16, desc: 'ปักเสาอาณาเขตศักดิ์สิทธิ์ รัศมี 120px ปล่อยคลื่นแสงเผาผลาญศัตรูทุก 0.5 วินาที' },
            { id: 'wrath_heavens', slot: 4, name: 'มหาทัณฑ์เทวาสะท้านภพ', enName: 'Wrath of the Heavens', tag: '[เทวะ 4]', baseDmg: 600, dmgPerLv: 135, cd: 16000, energy: 25, isUltimate: true, desc: '[อัลติเมท] เสาแสงสวรรค์ขนาดมหึมารัศมี 220px ฟาดผ่าลงมา ถล่มศัตรูและลดพลังโจมตีบอส 40%' }
        ]
    }
};

// Initialize Active Combat Skills State
Game.initPlayerSkills = function() {
    if (!this.player) return;
    if (!this.player.activeClass) this.player.activeClass = 'warrior';
    if (this.player.skillPoints === undefined) this.player.skillPoints = 5;
    if (!this.player.skillLevels) {
        this.player.skillLevels = {
            cyclone_slash: 1, flash_thrust: 1, ironclad_bastion: 1, judgement_blade: 1,
            pyroclast_orb: 1, glacial_ring: 1, prism_shield: 1, meteor_cataclysm: 1,
            arrow_barrage: 1, venom_trap: 1, shadow_dash: 1, dragonpiercer: 1,
            radiant_spear: 1, divine_heal: 1, sanctuary_pylon: 1, wrath_heavens: 1
        };
    }
    if (!this.player.skillCooldowns) this.player.skillCooldowns = {};
    if (!this.activeSkillVisuals) this.activeSkillVisuals = [];
};

// Trigger Player Skill via Hotkey 1, 2, 3, 4
Game.triggerPlayerSkill = function(slot) {
    if (!this.player || this.player.isDead) return false;
    this.initPlayerSkills();

    const cls = CLASS_SKILLS[this.player.activeClass || 'warrior'];
    if (!cls) return false;
    const skill = cls.skills.find(s => s.slot === slot);
    if (!skill) return false;

    // Check cooldown
    const cd = this.player.skillCooldowns[skill.id] || 0;
    if (cd > 0) {
        SoundEngine.errorClick();
        this.addFloatingText('★ สกิลติดคูลดาวน์ (' + (cd / 1000).toFixed(1) + 's)', this.player.x, this.player.y - 20, '#f87171');
        return true;
    }

    // Check energy
    if ((this.player.energy || 0) < skill.energy) {
        SoundEngine.errorClick();
        this.addFloatingText('★ พลังงานไม่พอ (ต้องการ ' + skill.energy + ' E)', this.player.x, this.player.y - 20, '#f87171');
        return true;
    }

    // Deduct energy & start energy cooldown delay (2 seconds before passive recovery starts)
    this.player.energy -= skill.energy;
    this.player.energyRegenDelay = 2000;
    const lv = this.player.skillLevels[skill.id] || 1;
    // Cooldown reduction per level (-8% per lv above 1)
    const effectiveCd = Math.round(skill.cd * (1 - (lv - 1) * 0.08));
    this.player.skillCooldowns[skill.id] = effectiveCd;

    // Cast sound
    if (skill.isUltimate) SoundEngine.ultimateCast();
    else SoundEngine.skillCast();

    // Execute class-specific skill logic
    const clsId = this.player.activeClass;
    if (clsId === 'warrior') this.castWarriorSkill(skill, lv);
    else if (clsId === 'mage') this.castMageSkill(skill, lv);
    else if (clsId === 'ranger') this.castRangerSkill(skill, lv);
    else if (clsId === 'paladin') this.castPaladinSkill(skill, lv);

    this.renderActiveSkillBar();
    this.updateHUD();
    return true;
};

// 1. Warrior Skills
Game.castWarriorSkill = function(skill, lv) {
    const px = this.player.x + 12;
    const py = this.player.y + 14;
    const dmg = this.calculateSkillDamage(skill, lv);

    if (skill.id === 'cyclone_slash') {
        this.triggerScreenShake(7.0, 220);
        this.triggerHitstop(70);
        this.spawnParticles(px, py, '#facc15', 25);
        this.spawnParticles(px, py, '#38bdf8', 18);
        this.pullEnemiesInRadius(px, py, 160, 40);
        this.activeSkillVisuals.push({ type: 'cyclone', x: px, y: py, radius: 140, timer: 600, maxTimer: 600 });
        this.damageEnemiesInRadius(px, py, 140, dmg, '★ คมดาบสะบั้น! -' + dmg, '#facc15');
        this.addFloatingText('★ [ดาบ 1] คลื่นพายุคมดาบสะบั้น! -' + dmg, px - 40, py - 30, '#facc15');
    } else if (skill.id === 'flash_thrust') {
        const rad = this.getPlayerAimAngle();
        const dist = 180;
        const tx = px + Math.cos(rad) * dist;
        const ty = py + Math.sin(rad) * dist;
        this.triggerScreenShake(8.0, 240);
        this.triggerHitstop(80);
        this.spawnParticles(px, py, '#38bdf8', 20);
        this.spawnParticles(tx, ty, '#ffffff', 20);
        this.activeSkillVisuals.push({ type: 'slash_line', x1: px, y1: py, x2: tx, y2: ty, timer: 500, maxTimer: 500 });
        this.damageEnemiesInLine(px, py, tx, ty, 55, dmg, '★ แทงทะลวง! -' + dmg, '#38bdf8');
        this.player.x += Math.cos(rad) * 95;
        this.player.y += Math.sin(rad) * 95;
        this.addFloatingText('★ [ดาบ 2] พุ่งทะลวงพริบตา! -' + dmg, tx - 30, ty - 25, '#38bdf8');
    } else if (skill.id === 'ironclad_bastion') {
        this.triggerScreenShake(6.0, 160);
        this.spawnParticles(px, py, '#facc15', 25);
        this.player.buffs = this.player.buffs || {};
        this.player.buffs.defense = 0.75;
        setTimeout(() => { if (this.player.buffs) this.player.buffs.defense = 0; }, 6000);
        this.activeSkillVisuals.push({ type: 'shield_barrier', x: px, y: py, radius: 55, timer: 6000, maxTimer: 6000, targetPlayer: true });
        this.addFloatingText('★ [ดาบ 3] ปราการเกราะเหล็ก! (ลดดาเมจ 75% นาน 6s)', px - 50, py - 30, '#facc15');
    } else if (skill.id === 'judgement_blade') {
        this.triggerScreenShake(12.0, 550);
        this.triggerHitstop(160);
        this.spawnParticles(px, py, '#fde047', 35);
        this.spawnParticles(px, py, '#f59e0b', 30);
        this.activeSkillVisuals.push({ type: 'judgement_sword', x: px, y: py, radius: 220, timer: 900, maxTimer: 900 });
        this.damageEnemiesInRadius(px, py, 220, dmg, '★ สุริยันพิฆาต! -' + dmg, '#fde047');
        this.addFloatingText('★ [อัลติเมท] สุริยันพิฆาตสะบั้นหล้า! -' + dmg + ' HP', px - 55, py - 35, '#fde047');
        if (this.boss && this.boss.alive) {
            this.boss.flashTimer = 500;
            this.boss.state = 'parried';
        }
    }
};

// 2. Mage Skills
Game.castMageSkill = function(skill, lv) {
    const px = this.player.x + 12;
    const py = this.player.y + 14;
    const dmg = this.calculateSkillDamage(skill, lv);
    const rad = this.getPlayerAimAngle();

    if (skill.id === 'pyroclast_orb') {
        this.triggerScreenShake(6.0, 180);
        this.spawnParticles(px, py, '#ea580c', 22);
        this.spawnParticles(px, py, '#facc15', 16);
        this.projectiles.push({
            x: px, y: py,
            vx: Math.cos(rad) * 11.0, vy: Math.sin(rad) * 11.0,
            angle: rad, damage: dmg, rangeLeft: 600,
            type: 'dragon_fire', fromPlayer: true,
            splashRadius: 110
        });
        this.activeSkillVisuals.push({ type: 'fire_blast', x: px, y: py, radius: 80, timer: 500, maxTimer: 500 });
        this.addFloatingText('★ [เวท 1] บอลเพลิงโลกันตร์! -' + dmg, px - 30, py - 25, '#ea580c');
    } else if (skill.id === 'glacial_ring') {
        this.triggerScreenShake(7.0, 220);
        this.spawnParticles(px, py, '#38bdf8', 28);
        this.spawnParticles(px, py, '#e0f2fe', 22);
        this.activeSkillVisuals.push({ type: 'frost_ring', x: px, y: py, radius: 160, timer: 700, maxTimer: 700 });
        this.damageEnemiesInRadius(px, py, 160, dmg, '★ แช่แข็งเยือกแข็ง! -' + dmg, '#38bdf8', (e) => {
            e.slowTimer = 4000;
        });
        this.addFloatingText('★ [เวท 2] วงแหวนเหมันต์เยือกแข็ง! -' + dmg, px - 45, py - 30, '#38bdf8');
    } else if (skill.id === 'prism_shield') {
        this.triggerScreenShake(5.0, 150);
        this.spawnParticles(px, py, '#c084fc', 25);
        const orbDmg = Math.round(dmg * 0.45);
        this.activeSkillVisuals.push({ type: 'prism_orbs', x: px, y: py, timer: 10000, maxTimer: 10000, targetPlayer: true, damage: orbDmg });
        this.addFloatingText('★ [เวท 3] ม่านพายุปริซึม! (เลเซอร์ออโต้ ' + orbDmg + ' DMG)', px - 30, py - 25, '#c084fc');
    } else if (skill.id === 'meteor_cataclysm') {
        this.triggerScreenShake(13.0, 600);
        this.spawnParticles(px, py, '#ea580c', 35);
        this.addFloatingText('★ [อัลติเมท] ฝนดาวตกกลืนนภา! มหาอุกกาบาตล้างบาง!', px - 50, py - 35, '#ea580c');
        const nearestEnemy = this.findNearestCombatTarget(520);
        const targetCenterX = nearestEnemy ? nearestEnemy.x : ((this.mouseWorld && this.mouseWorld.x !== 0) ? this.mouseWorld.x : (this.boss ? this.boss.x + 32 : px));
        const targetCenterY = nearestEnemy ? nearestEnemy.y : ((this.mouseWorld && this.mouseWorld.y !== 0) ? this.mouseWorld.y : (this.boss ? this.boss.y + 32 : py));
        const meteorDmg = Math.round(dmg * 0.55);

        for (let m = 0; m < 6; m++) {
            const mx = targetCenterX - 110 + Math.random() * 220;
            const my = targetCenterY - 90 + Math.random() * 180;
            setTimeout(() => {
                this.activeSkillVisuals.push({ type: 'meteor_strike', x: mx, y: my, radius: 100, timer: 550, maxTimer: 550 });
                this.damageEnemiesInRadius(mx, my, 100, meteorDmg, '★ อุกกาบาตระเบิด! -' + meteorDmg, '#ea580c');
                this.spawnParticles(mx, my, '#ea580c', 22);
                this.spawnParticles(mx, my, '#fde047', 18);
                this.triggerScreenShake(7.5, 200);
                SoundEngine.thunder();
            }, m * 130);
        }
    }
};

// 3. Ranger Skills
Game.castRangerSkill = function(skill, lv) {
    const px = this.player.x + 12;
    const py = this.player.y + 14;
    const dmg = this.calculateSkillDamage(skill, lv);
    const baseAng = this.getPlayerAimAngle();

    if (skill.id === 'arrow_barrage') {
        const arrowDmg = Math.round(dmg * 0.32);
        [-0.30, -0.20, -0.10, 0, 0.10, 0.20, 0.30].forEach(off => {
            const a = baseAng + off;
            this.projectiles.push({
                x: px, y: py,
                vx: Math.cos(a) * 14.0, vy: Math.sin(a) * 14.0,
                angle: a, damage: arrowDmg, rangeLeft: 600,
                type: 'crystal_shard', fromPlayer: true
            });
        });
        this.triggerScreenShake(5.0, 150);
        this.spawnParticles(px, py, '#4ade80', 25);
        this.activeSkillVisuals.push({ type: 'arrow_barrage_cone', x: px, y: py, angle: baseAng, timer: 450, maxTimer: 450 });
        this.addFloatingText('★ [พราน 1] ฝนธนู 7 ดอกแผลงศร! (ดอกละ ' + arrowDmg + ' DMG)', px - 40, py - 25, '#4ade80');
    } else if (skill.id === 'venom_trap') {
        this.triggerScreenShake(4.5, 120);
        this.spawnParticles(px, py, '#22c55e', 22);
        this.activeSkillVisuals.push({ type: 'poison_trap', x: px, y: py, radius: 90, timer: 9000, maxTimer: 9000, damage: dmg });
        this.addFloatingText('★ [พราน 2] วางกับดักหนามพิษ! -' + dmg, px - 35, py - 25, '#22c55e');
    } else if (skill.id === 'shadow_dash') {
        this.player.invincibleTimer = 1800; // 1.8s invincibility
        this.player.speed = 4.5;
        setTimeout(() => { if (this.player) this.player.speed = 2.8; }, 2500);
        this.spawnParticles(px, py, '#475569', 25);
        this.spawnParticles(px, py, '#a855f7', 20);
        this.activeSkillVisuals.push({ type: 'shadow_trail', x: px, y: py, timer: 500, maxTimer: 500 });
        this.addFloatingText('★ [พราน 3] ก้าวเงาล่องหน! (อมตะ 1.8s & วิ่งไว +60%)', px - 40, py - 25, '#94a3b8');
    } else if (skill.id === 'dragonpiercer') {
        this.triggerScreenShake(11.0, 450);
        this.spawnParticles(px, py, '#38bdf8', 30);
        this.spawnParticles(px, py, '#fde047', 20);
        this.activeSkillVisuals.push({ type: 'lightning_beam_line', x: px, y: py, angle: baseAng, length: 800, timer: 650, maxTimer: 650 });
        const ex = px + Math.cos(baseAng) * 800;
        const ey = py + Math.sin(baseAng) * 800;
        this.damageEnemiesInLine(px, py, ex, ey, 65, dmg, '★ ศรอัสนีพิฆาต! -' + dmg, '#38bdf8');
        this.addFloatingText('★ [อัลติเมท] ธนูอัสนีพิฆาตมังกร! -' + dmg + ' HP', px - 50, py - 35, '#38bdf8');
        if (this.boss && this.boss.alive) {
            this.boss.flashTimer = 450;
        }
    }
};

// 4. Paladin Skills
Game.castPaladinSkill = function(skill, lv) {
    const px = this.player.x + 12;
    const py = this.player.y + 14;
    const dmg = this.calculateSkillDamage(skill, lv);
    const baseAng = this.getPlayerAimAngle();

    if (skill.id === 'radiant_spear') {
        this.triggerScreenShake(6.0, 180);
        this.spawnParticles(px, py, '#facc15', 25);
        this.projectiles.push({
            x: px, y: py,
            vx: Math.cos(baseAng) * 14.0, vy: Math.sin(baseAng) * 14.0,
            angle: baseAng, damage: dmg, rangeLeft: 600,
            type: 'holy_beam', fromPlayer: true,
            splashRadius: 100
        });
        this.activeSkillVisuals.push({ type: 'radiant_burst', x: px, y: py, angle: baseAng, timer: 500, maxTimer: 500 });
        this.addFloatingText('★ [เทวะ 1] หอกแสงพิพากษา! -' + dmg, px - 35, py - 25, '#facc15');
    } else if (skill.id === 'divine_heal') {
        const healAmt = 120 + (lv - 1) * 35;
        this.player.hp = Math.min(this.player.maxHp || 100, this.player.hp + healAmt);
        this.player.energy = Math.min(this.player.maxEnergy || 100, (this.player.energy || 0) + 30);
        this.player.slowTimer = 0;
        this.triggerScreenShake(4.5, 140);
        this.spawnParticles(px, py, '#4ade80', 25);
        this.spawnParticles(px, py, '#fef08a', 20);
        this.activeSkillVisuals.push({ type: 'heal_aura', x: px, y: py, timer: 800, maxTimer: 800, targetPlayer: true });
        this.addFloatingText('★ [เทวะ 2] อวยพรเทวะ! +' + healAmt + ' HP (+30 SP)', px - 35, py - 25, '#4ade80');
    } else if (skill.id === 'sanctuary_pylon') {
        this.triggerScreenShake(5.5, 160);
        this.spawnParticles(px, py, '#facc15', 25);
        const pylonDmg = Math.round(dmg * 0.45);
        this.activeSkillVisuals.push({ type: 'holy_sanctuary', x: px, y: py, radius: 120, timer: 9000, maxTimer: 9000, damage: pylonDmg });
        this.addFloatingText('★ [เทวะ 3] เสาเพลิงชำระล้าง! (คลื่นแสง ' + pylonDmg + ' DMG)', px - 40, py - 25, '#facc15');
    } else if (skill.id === 'wrath_heavens') {
        this.triggerScreenShake(13.0, 600);
        this.triggerHitstop(140);
        this.spawnParticles(px, py, '#fde047', 40);
        this.spawnParticles(px, py, '#ffffff', 30);
        this.activeSkillVisuals.push({ type: 'heaven_pillar', x: px, y: py, radius: 220, timer: 950, maxTimer: 950 });
        this.damageEnemiesInRadius(px, py, 220, dmg, '★ ทัณฑ์เทวาสะท้านภพ! -' + dmg, '#fde047');
        this.addFloatingText('★ [อัลติเมท] มหาทัณฑ์เทวาสะท้านภพ! -' + dmg + ' HP', px - 55, py - 35, '#fde047');
        if (this.boss && this.boss.alive) {
            this.boss.flashTimer = 550;
            this.boss.state = 'parried';
        }
    }
};

// Damage Helper in Radius
Game.damageEnemiesInRadius = function(x, y, radius, dmg, text, color, proc = null) {
    if (this.demonBugs) {
        for (let i = this.demonBugs.length - 1; i >= 0; i--) {
            const b = this.demonBugs[i];
            if (Math.hypot((b.x + 14) - x, (b.y + 14) - y) <= radius) {
                b.hp -= dmg;
                b.flashTimer = 160;
                b.squashX = 1.35;
                b.squashY = 0.72;
                this.addFloatingText(text, b.x, b.y - 10, color);
                if (proc) proc(b);
            }
        }
    }
    if (this.worldMonsters) {
        for (let i = this.worldMonsters.length - 1; i >= 0; i--) {
            const m = this.worldMonsters[i];
            if (Math.hypot((m.x + 16) - x, (m.y + 16) - y) <= radius) {
                m.hp -= dmg;
                m.flashTimer = 160;
                m.squashX = 1.35;
                m.squashY = 0.72;
                this.addFloatingText(text, m.x, m.y - 10, color);
                if (proc) proc(m);
            }
        }
    }
    if (this.remotePlayers && (this.currentScene === 'pvp_arena' || this.isPvPEnabled)) {
        for (const pid in this.remotePlayers) {
            const rp = this.remotePlayers[pid];
            if (!rp || rp.scene !== this.currentScene || rp.hp <= 0) continue;
            if (Math.hypot((rp.x + 12) - x, (rp.y + 14) - y) <= radius) {
                if (typeof (window as any).Multiplayer !== 'undefined') {
                    (window as any).Multiplayer.sendPvPHit(pid, dmg, false, 0, 'สกิลพิเศษ');
                }
                this.addFloatingText(text, rp.x, rp.y - 12, color);
            }
        }
    }

    if (this.boss && this.boss.alive) {
        if (Math.hypot((this.boss.x + 32) - x, (this.boss.y + 32) - y) <= radius + 30) {
            this.boss.hp -= dmg;
            this.boss.flashTimer = 180;
            this.boss.squashX = 1.25;
            this.boss.squashY = 0.8;
            this.addFloatingText(text, this.boss.x + 20, this.boss.y - 10, color);
            if (proc) proc(this.boss);
            if (this.boss.hp <= 0) this.defeatBoss();
        }
    }
};

// Damage Helper in Line
Game.damageEnemiesInLine = function(x1, y1, x2, y2, width, dmg, text, color) {
    const checkLineHit = (ex, ey) => {
        const lineLen = Math.hypot(x2 - x1, y2 - y1);
        if (lineLen === 0) return Math.hypot(ex - x1, ey - y1) <= width;
        const u = ((ex - x1) * (x2 - x1) + (ey - y1) * (y2 - y1)) / (lineLen * lineLen);
        const clampedU = Math.max(0, Math.min(1, u));
        const nearX = x1 + clampedU * (x2 - x1);
        const nearY = y1 + clampedU * (y2 - y1);
        return Math.hypot(ex - nearX, ey - nearY) <= width;
    };

    if (this.worldMonsters) {
        for (let i = this.worldMonsters.length - 1; i >= 0; i--) {
            const m = this.worldMonsters[i];
            if (checkLineHit(m.x + 16, m.y + 16)) {
                m.hp -= dmg;
                m.flashTimer = 160;
                m.squashX = 1.35;
                m.squashY = 0.72;
                this.addFloatingText(text, m.x, m.y - 10, color);
            }
        }
    }
    if (this.boss && this.boss.alive) {
        if (checkLineHit(this.boss.x + 32, this.boss.y + 32)) {
            this.boss.hp -= dmg;
            this.boss.flashTimer = 180;
            this.boss.squashX = 1.25;
            this.boss.squashY = 0.8;
            this.addFloatingText(text, this.boss.x + 20, this.boss.y - 10, color);
            if (this.boss.hp <= 0) this.defeatBoss();
        }
    }
};

Game.getPlayerDirectionAngle = function() {
    const d = this.player.direction || 'down';
    if (d === 'right') return 0;
    if (d === 'down') return Math.PI / 2;
    if (d === 'left') return Math.PI;
    return -Math.PI / 2;
};

Game.getPlayerAimAngle = function() {
    // 0. Manual Skill Joystick Aim Angle (Active when dragging a skill button!)
    if (this.skillAimAngle !== undefined && this.skillAimAngle !== null) {
        return this.skillAimAngle;
    }

    const px = this.player.x + 12;
    const py = this.player.y + 14;

    // 1. Smart Auto-Aim Assist: Prioritize nearest enemy on touch devices or mobile viewport (Full Widescreen 720px)
    const nearest = this.findNearestCombatTarget(720);
    const hasTouch = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || (window.innerWidth <= 900);

    if (hasTouch && nearest) {
        const dx = nearest.x - px;
        const dy = nearest.y - py;
        if (Math.abs(dx) > Math.abs(dy)) {
            this.player.direction = dx > 0 ? 'right' : 'left';
        } else {
            this.player.direction = dy > 0 ? 'down' : 'up';
        }
        return Math.atan2(dy, dx);
    }

    // 2. Desktop: Aim accurately toward mouse cursor in world coordinates
    if (this.mouseWorld && (this.mouseWorld.x !== 0 || this.mouseWorld.y !== 0)) {
        const dx = this.mouseWorld.x - px;
        const dy = this.mouseWorld.y - py;
        if (Math.hypot(dx, dy) > 20) {
            if (Math.abs(dx) > Math.abs(dy)) {
                this.player.direction = dx > 0 ? 'right' : 'left';
            } else {
                this.player.direction = dy > 0 ? 'down' : 'up';
            }
            return Math.atan2(dy, dx);
        }
    }

    // 3. Fallback Auto-Aim for desktop if mouse is stationary
    if (nearest) {
        const dx = nearest.x - px;
        const dy = nearest.y - py;
        if (Math.abs(dx) > Math.abs(dy)) {
            this.player.direction = dx > 0 ? 'right' : 'left';
        } else {
            this.player.direction = dy > 0 ? 'down' : 'up';
        }
        return Math.atan2(dy, dx);
    }

    // 4. Fallback to 4-way facing direction
    return this.getPlayerDirectionAngle();
};

Game.calculateSkillDamage = function(skill: any, lv: number): number {
    const selItem = this.player.inventory[this.player.selectedSlot];
    const weaponDmg = (selItem && selItem.damage) ? selItem.damage : ((selItem && WEAPONS[selItem.id]?.damage) ? WEAPONS[selItem.id].damage : 45);
    const pLevel = this.player.level || 1;
    const buffDmg = this.player.buffs?.damage || 0;
    const isWellFed = (this.player.hunger !== undefined ? this.player.hunger : 100) >= 75 &&
                      (this.player.thirst !== undefined ? this.player.thirst : 100) >= 75;
    const wellFedMult = isWellFed ? 1.15 : 1.0;

    if (skill.isUltimate) {
        return Math.round(((skill.baseDmg * 3.2) + ((lv - 1) * skill.dmgPerLv * 2.8) + (weaponDmg * 2.6) + (pLevel * 22) + buffDmg) * wellFedMult);
    }
    return Math.round(((skill.baseDmg * 2.5) + ((lv - 1) * skill.dmgPerLv * 2.0) + (weaponDmg * 1.5) + (pLevel * 10) + buffDmg) * wellFedMult);
};

Game.pullEnemiesInRadius = function(x: number, y: number, radius: number, pullForce: number) {
    if (this.currentScene === 'farm') {
        this.demonBugs.forEach(bug => {
            const d = Math.hypot((bug.x + 14) - x, (bug.y + 14) - y);
            if (d < radius && d > 20) {
                const ang = Math.atan2(y - (bug.y + 14), x - (bug.x + 14));
                bug.x += Math.cos(ang) * pullForce;
                bug.y += Math.sin(ang) * pullForce;
            }
        });
    } else {
        this.worldMonsters.forEach(m => {
            const d = Math.hypot((m.x + 16) - x, (m.y + 16) - y);
            if (d < radius && d > 20) {
                const ang = Math.atan2(y - (m.y + 16), x - (m.x + 16));
                m.x += Math.cos(ang) * pullForce;
                m.y += Math.sin(ang) * pullForce;
            }
        });
    }
};

// Update active skill cooldowns, energy regeneration & visuals
Game.updatePlayerSkills = function(dt) {
    if (!this.player) return;
    this.initPlayerSkills();

    // 0. Passive HP & Energy Recovery System (ฟื้นฟูเลือดและพลังงานอัตโนมัติ)
    if (!this.player.isDead) {
        // --- A. Passive Health (HP) Regeneration (เลือดฟื้นฟูอัตโนมัติเมื่อพ้นจากการต่อสู้) ---
        const maxH = this.player.maxHp || 100;
        if (this.player.hpRegenDelay && this.player.hpRegenDelay > 0) {
            this.player.hpRegenDelay = Math.max(0, this.player.hpRegenDelay - dt);
        } else if (this.player.hp < maxH) {
            // Base recovery: 8 HP per second (ฟื้นฟู 8 HP/วินาทีเมื่อไม่ได้โดนโจมตีเกิน 3 วินาที)
            let hpRate = 8;
            if ((this.player.hunger !== undefined && this.player.hunger <= 0) || (this.player.thirst !== undefined && this.player.thirst <= 0)) {
                hpRate *= 0.5; // โดนลดอัตราฟื้นฟูหากหิวจัด
            }
            if (this.currentScene === 'house') {
                hpRate *= 1.5; // พักผ่อนในบ้านฟื้นฟูเร็วขึ้น 50%
            }
            const prevHp = this.player.hp;
            this.player.hp = Math.min(maxH, this.player.hp + (hpRate * (dt / 1000)));
            if (Math.floor(prevHp) !== Math.floor(this.player.hp) || this.player.hp >= maxH) {
                this.updateHpHUD();
            }
        }

        // --- B. Passive Energy Recovery (พลังงานฟื้นฟูอัตโนมัติเมื่อไม่ได้ใช้สกิล) ---
        const maxE = this.player.maxEnergy || 100;
        if (this.player.energyRegenDelay && this.player.energyRegenDelay > 0) {
            this.player.energyRegenDelay = Math.max(0, this.player.energyRegenDelay - dt);
        } else if (this.player.energy < maxE) {
            let regenRate = 14;
            if ((this.player.hunger !== undefined && this.player.hunger <= 0) || (this.player.thirst !== undefined && this.player.thirst <= 0)) {
                regenRate *= 0.5;
            }
            if (this.player.buffs?.energy) {
                regenRate *= 1.6;
            }
            const prevEnergy = this.player.energy;
            this.player.energy = Math.min(maxE, this.player.energy + (regenRate * (dt / 1000)));
            if (Math.floor(prevEnergy) !== Math.floor(this.player.energy) || this.player.energy >= maxE) {
                this.updateEnergyHUD();
            }
        }
    }

    // Decrement skill cooldowns
    if (this.player.skillCooldowns) {
        for (const k in this.player.skillCooldowns) {
            if (this.player.skillCooldowns[k] > 0) {
                this.player.skillCooldowns[k] = Math.max(0, this.player.skillCooldowns[k] - dt);
            }
        }
    }

    // Update visuals
    if (this.activeSkillVisuals) {
        for (let i = this.activeSkillVisuals.length - 1; i >= 0; i--) {
            const v = this.activeSkillVisuals[i];
            v.timer -= dt;

            // Follow player if attached
            if (v.targetPlayer && this.player) {
                v.x = this.player.x + 12;
                v.y = this.player.y + 14;
            }

            // Periodic ticks for traps & pylons
            if (v.type === 'holy_sanctuary' || v.type === 'poison_trap') {
                v.tickTimer = (v.tickTimer || 0) - dt;
                if (v.tickTimer <= 0) {
                    v.tickTimer = 650;
                    this.damageEnemiesInRadius(v.x, v.y, v.radius, v.damage || 20, '★ -' + (v.damage || 20), v.type === 'holy_sanctuary' ? '#facc15' : '#22c55e');
                    this.spawnParticles(v.x, v.y, v.type === 'holy_sanctuary' ? '#fde047' : '#22c55e', 8);
                }
            } else if (v.type === 'prism_orbs') {
                v.tickTimer = (v.tickTimer || 0) - dt;
                if (v.tickTimer <= 0) {
                    v.tickTimer = 750;
                    let nearest = null;
                    let minDist = 160;
                    const checkEnemies = (list) => {
                        if (!list) return;
                        list.forEach(e => {
                            const d = Math.hypot((e.x + 14) - v.x, (e.y + 14) - v.y);
                            if (d < minDist) { minDist = d; nearest = e; }
                        });
                    };
                    checkEnemies(this.demonBugs);
                    checkEnemies(this.worldMonsters);
                    if (this.boss && this.boss.alive) {
                        const bd = Math.hypot((this.boss.x + 32) - v.x, (this.boss.y + 32) - v.y);
                        if (bd < minDist) nearest = this.boss;
                    }
                    if (nearest) {
                        const targetX = nearest.x + (nearest.width ? nearest.width / 2 : 14);
                        const targetY = nearest.y + (nearest.height ? nearest.height / 2 : 14);
                        nearest.hp -= (v.damage || 24);
                        nearest.flashTimer = 160;
                        this.spawnParticles(targetX, targetY, '#c084fc', 8);
                        this.addFloatingText('★ ปริซึมช็อต! -' + (v.damage || 24), targetX, targetY - 10, '#c084fc');
                        SoundEngine.bossLaser();
                    }
                }
            }

            if (v.timer <= 0) {
                this.activeSkillVisuals.splice(i, 1);
            }
        }
    }

    this._skillBarTimer = (this._skillBarTimer || 0) + dt;
    if (this._skillBarTimer >= 100) {
        this._skillBarTimer = 0;
        this.renderActiveSkillBar();
    }
};

// Skill Visual Metadata & SVG Vector Icon Glyphs
const SKILL_SHORT_TAGS: Record<string, string> = {
    cyclone_slash: 'ดาบหมุน',
    flash_thrust: 'แทงพริบตา',
    ironclad_bastion: 'เกราะเหล็ก',
    judgement_blade: 'สุริยัน',
    pyroclast_orb: 'บอลเพลิง',
    glacial_ring: 'เหมันต์',
    prism_shield: 'ปริซึม',
    meteor_cataclysm: 'ฝนดาวตก',
    arrow_barrage: 'ห่าธนู',
    venom_trap: 'กับดักพิษ',
    shadow_dash: 'ก้าวเงา',
    dragonpiercer: 'ศรอัสนี',
    radiant_spear: 'หอกแสง',
    divine_heal: 'อวยพรเทวะ',
    sanctuary_pylon: 'เสาศักดิ์',
    wrath_heavens: 'ทัณฑ์เทวา'
};

const CLASS_HERALDRY: Record<string, { icon: string; name: string; color: string }> = {
    warrior: { icon: '⚔️', name: 'จอมดาบ', color: '#f59e0b' },
    mage: { icon: '🔮', name: 'จอมเวท', color: '#a855f7' },
    ranger: { icon: '🏹', name: 'จอมพราน', color: '#10b981' },
    paladin: { icon: '✨', name: 'เทวะ', color: '#eab308' }
};

const SKILL_ICONS: Record<string, string> = {
    // Warrior
    cyclone_slash: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2a10 10 0 0 1 10 10c0 4-2.5 7.5-6 9" stroke="#38bdf8"/>
        <path d="M12 22A10 10 0 0 1 2 12c0-4 2.5-7.5 6-9" stroke="#7dd3fc"/>
        <path d="M8 8l8 8M16 8l-8 8" stroke="#ffffff"/>
        <circle cx="12" cy="12" r="2.5" fill="#38bdf8"/>
    </svg>`,
    flash_thrust: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 21l8-8M11 13l8-8 2 2-8 8-2-2z" fill="rgba(103,232,249,0.25)" stroke="#67e8f9"/>
        <path d="M21 3l-4 4" stroke="#ffffff"/>
        <path d="M2 11h4M3 15h4M5 7h3" stroke="#a5f3fc"/>
    </svg>`,
    ironclad_bastion: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2l8 3.5v6.5c0 6-4 10.5-8 11.8C8 22.5 4 18 4 12V5.5L12 2z" fill="rgba(245,158,11,0.25)" stroke="#f59e0b"/>
        <path d="M12 6v12M7.5 11h9" stroke="#fef08a" stroke-width="2.2"/>
        <circle cx="12" cy="11" r="2" fill="#fbbf24"/>
    </svg>`,
    judgement_blade: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2v18M9 7l3-5 3 5M8 15h8M12 20v2" stroke="#fde047"/>
        <path d="M4 12l2-1M20 12l-2-1M6 6l2 2M18 6l-2 2M6 18l2-2M18 18l-2-2" stroke="#f59e0b"/>
        <circle cx="12" cy="11" r="2" fill="#ef4444"/>
    </svg>`,

    // Mage
    pyroclast_orb: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="13" r="6" fill="rgba(249,115,22,0.3)" stroke="#f97316"/>
        <path d="M12 2c1.5 3 0 5 2 8 1.5-2 2.5-3 2.5-5 3 2.5 4.5 6 2 9.5-1.5 2.5-4 3.5-6.5 3-3-.6-5-3.2-4.5-6.5.5-3 3-5 6.5-9z" fill="rgba(239,68,68,0.3)" stroke="#ef4444"/>
        <circle cx="12" cy="13" r="2" fill="#fef08a"/>
    </svg>`,
    glacial_ring: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2v20M2 12h20M5 5l14 14M5 19L19 5" stroke="#38bdf8"/>
        <circle cx="12" cy="12" r="3" fill="rgba(147,197,253,0.35)" stroke="#bfdbfe"/>
        <path d="M10 6l2-2 2 2M10 18l2 2 2-2M6 10l-2 2 2 2M18 10l2 2-2 2" stroke="#ffffff"/>
    </svg>`,
    prism_shield: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="12 2 20 7 20 17 12 22 4 17 4 7" fill="rgba(192,132,252,0.25)" stroke="#c084fc"/>
        <polygon points="12 6 16 9 16 15 12 18 8 15 8 9" stroke="#e879f9"/>
        <circle cx="12" cy="12" r="2" fill="#ffffff"/>
    </svg>`,
    meteor_cataclysm: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="7" cy="17" r="4.5" fill="rgba(239,68,68,0.4)" stroke="#ef4444"/>
        <path d="M10 14l11-11M14 17l7-7M7 11l10-10" stroke="#f97316"/>
        <path d="M3 21l3-1M2 17l2 1M7 22l-1-2" stroke="#fde047"/>
    </svg>`,

    // Ranger
    arrow_barrage: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 12h18M16 7l5 5-5 5" stroke="#34d399"/>
        <path d="M4 6l14 3.5-3 1.5M4 18l14-3.5-3-1.5" stroke="#10b981"/>
    </svg>`,
    venom_trap: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 16c2 4 14 4 18 0M5 16l2-6 3 4 2-8 2 8 3-4 2 6" stroke="#84cc16"/>
        <circle cx="12" cy="7" r="2" fill="#a3e635"/>
        <path d="M12 12v3" stroke="#4ade80"/>
    </svg>`,
    shadow_dash: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M13 2l-6 10h6l-4 10 10-12h-6l4-8z" fill="rgba(167,139,250,0.3)" stroke="#a78bfa"/>
        <path d="M3 8h4M2 13h5M4 17h3" stroke="#818cf8"/>
    </svg>`,
    dragonpiercer: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M2 12l6-5 4 2.5 5-6 3 4-3.5 4.5 3.5 4.5-3 4-5-6-4 2.5z" fill="rgba(56,189,248,0.25)" stroke="#38bdf8"/>
        <path d="M10 12h12M17 8l5 4-5 4" stroke="#facc15" stroke-width="2.2"/>
    </svg>`,

    // Paladin
    radiant_spear: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2l3 5-3 2-3-2zM12 9v13M8 14h8" stroke="#facc15"/>
        <path d="M5 9c2.5-1 4.5 1 7 3 2.5-2 4.5-4 7-3" stroke="#fef08a"/>
    </svg>`,
    divine_heal: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" fill="rgba(244,114,182,0.3)" stroke="#f472b6"/>
        <path d="M12 7v6M9 10h6" stroke="#ffffff" stroke-width="2.4"/>
    </svg>`,
    sanctuary_pylon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="12 2 16 6 15 20 9 20 8 6" fill="rgba(251,191,36,0.25)" stroke="#fbbf24"/>
        <path d="M12 7v8M10 11h4" stroke="#fef3c7"/>
        <circle cx="12" cy="2" r="1.5" fill="#2dd4bf"/>
        <path d="M5 21h14" stroke="#fbbf24"/>
    </svg>`,
    wrath_heavens: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 10a4 4 0 0 0-7.8-1.2A5 5 0 0 0 2 13h16a3 3 0 0 0 1-5.8z" fill="rgba(254,240,138,0.2)" stroke="#fde047"/>
        <path d="M13 11l-3 6h4l-3 6" stroke="#f59e0b" stroke-width="2.5"/>
    </svg>`
};

// Render HUD Active Skill Bar
Game.renderActiveSkillBar = function() {
    const container = document.getElementById('activeSkillSlots');
    const touchContainer = document.getElementById('touchSkillsRow');
    if (!this.player) return;

    this.initPlayerSkills();
    const cls = CLASS_SKILLS[this.player.activeClass || 'warrior'];
    if (!cls) return;

    // Update Class tag & SP badge
    const tagEl = document.getElementById('skillClassTag');
    if (tagEl && tagEl.textContent !== cls.tag) tagEl.textContent = cls.tag;
    const nameEl = document.getElementById('skillClassName');
    if (nameEl) {
        const shortName = cls.name.split(' ')[0].replace('สาย', '');
        if (nameEl.textContent !== shortName) nameEl.textContent = shortName;
    }
    const spEl = document.getElementById('skillPointsBadge');
    const spVal = this.player.skillPoints || 0;
    const spText = spVal + ' SP';
    if (spEl && spEl.textContent !== spText) spEl.textContent = spText;

    const ACTION_KEYS = ['Z', 'X', 'C', 'V'];
    const heraldry = CLASS_HERALDRY[this.player.activeClass || 'warrior'] || CLASS_HERALDRY.warrior;
    const hasSp = spVal > 0;

    // 1. Initial DOM Build on first load or class change (Zero innerHTML churn during combat!)
    if (this._renderedSkillClass !== this.player.activeClass) {
        this._renderedSkillClass = this.player.activeClass;

        if (container) {
            let html = '';
            cls.skills.forEach(skill => {
                const lv = this.player.skillLevels[skill.id] || 1;
                const tag = SKILL_SHORT_TAGS[skill.id] || skill.name.substring(0, 4);
                const actionKey = ACTION_KEYS[skill.slot - 1] || 'Z';
                const svgIcon = SKILL_ICONS[skill.id] || '';
                html += `
                    <div class="active-skill-slot slot-${skill.slot} ${skill.isUltimate ? 'ultimate' : ''}" 
                         data-slot="${skill.slot}"
                         title="${skill.name} (${skill.enName}) [${actionKey}]">
                        <div class="skill-slot-icon-wrap">${svgIcon}</div>
                        <span class="skill-slot-key">${actionKey}</span>
                        <span class="skill-slot-tag">${tag}</span>
                        <span class="skill-slot-level">Lv.${lv}</span>
                        <div class="skill-cooldown-overlay" style="display: none;"></div>
                    </div>
                `;
            });
            container.innerHTML = html;
        }

        if (touchContainer) {
            let touchHtml = `
                <button class="touch-skill-class-btn ${hasSp ? 'has-sp-glow' : ''}" 
                        type="button" 
                        onclick="Game.openSkillTreeModal()" 
                        title="เปิดผังสกิลและเปลี่ยนสายอาชีพ [K]">
                    <div class="touch-skill-class-orb">
                        <div class="touch-skill-class-header">
                            <span class="touch-skill-class-icon">${heraldry.icon}</span>
                            <span class="touch-skill-class-name">${heraldry.name}</span>
                        </div>
                        <div class="touch-skill-class-sp ${hasSp ? 'has-sp' : ''}">
                            <span class="sp-sparkle">✦</span> ${spVal} SP
                        </div>
                    </div>
                    <div class="touch-skill-pill touch-skill-class-pill">[K] ผัง</div>
                </button>
            `;
            cls.skills.forEach(skill => {
                const lv = this.player.skillLevels[skill.id] || 1;
                const tag = SKILL_SHORT_TAGS[skill.id] || skill.name.substring(0, 4);
                const actionKey = ACTION_KEYS[skill.slot - 1] || 'Z';
                const isUlt = !!skill.isUltimate;
                const svgIcon = SKILL_ICONS[skill.id] || '';

                touchHtml += `
                    <button class="touch-skill-btn slot-${skill.slot} ${isUlt ? 'touch-skill-ult' : ''}"
                            data-slot="${skill.slot}"
                            type="button"
                            title="${skill.name} [${actionKey}]">
                        <div class="touch-skill-orb">
                            <div class="touch-skill-icon-wrap">${svgIcon}</div>
                            <div class="touch-skill-cd" style="display: none;"></div>
                            <div class="touch-skill-sheen"></div>
                        </div>
                        <span class="touch-skill-key">${actionKey}</span>
                        <span class="touch-skill-lv">★${lv}</span>
                        <div class="touch-skill-pill">${tag}</div>
                    </button>
                `;
            });
            touchContainer.innerHTML = touchHtml;
        }
    }

    // 2. High-Performance Lightweight Cooldown & SP Tick (Zero DOM churn)
    if (touchContainer) {
        const touchSpEl = touchContainer.querySelector('.touch-skill-class-sp') as HTMLElement;
        if (touchSpEl) {
            const touchSpTxt = `✦ ${spVal} SP`;
            if (touchSpEl.textContent !== touchSpTxt) touchSpEl.textContent = touchSpTxt;
            touchSpEl.classList.toggle('has-sp', hasSp);
        }
        const classBtn = touchContainer.querySelector('.touch-skill-class-btn') as HTMLElement;
        if (classBtn) {
            classBtn.classList.toggle('has-sp-glow', hasSp);
        }
    }

    cls.skills.forEach(skill => {
        const cd = this.player.skillCooldowns[skill.id] || 0;
        const lv = this.player.skillLevels[skill.id] || 1;
        const isOnCd = cd > 0;
        const cdText = (cd / 1000).toFixed(1) + 's';

        // Desktop overlay
        if (container) {
            const slotEl = container.querySelector(`[data-slot="${skill.slot}"]`) as HTMLElement;
            if (slotEl) {
                slotEl.classList.toggle('on-cooldown', isOnCd);
                const cdEl = slotEl.querySelector('.skill-cooldown-overlay') as HTMLElement;
                if (cdEl) {
                    if (isOnCd) {
                        cdEl.textContent = cdText;
                        if (cdEl.style.display !== 'flex') cdEl.style.display = 'flex';
                    } else if (cdEl.style.display !== 'none') {
                        cdEl.style.display = 'none';
                    }
                }
            }
        }

        // Mobile touch button
        if (touchContainer) {
            const touchBtn = touchContainer.querySelector(`[data-slot="${skill.slot}"]`) as HTMLElement;
            if (touchBtn) {
                touchBtn.classList.toggle('on-cooldown', isOnCd);
                if (skill.isUltimate) {
                    touchBtn.classList.toggle('touch-ult-ready', !isOnCd);
                }
                const cdEl = touchBtn.querySelector('.touch-skill-cd') as HTMLElement;
                if (cdEl) {
                    if (isOnCd) {
                        cdEl.textContent = cdText;
                        if (cdEl.style.display !== 'flex') cdEl.style.display = 'flex';
                    } else if (cdEl.style.display !== 'none') {
                        cdEl.style.display = 'none';
                    }
                }
                const lvEl = touchBtn.querySelector('.touch-skill-lv') as HTMLElement;
                const expectedLv = '★' + lv;
                if (lvEl && lvEl.textContent !== expectedLv) {
                    lvEl.textContent = expectedLv;
                }
            }
        }
    });
};

// Skill Joystick Aiming Controls (Mobile Drag to Aim & Desktop Mouse Drag Aim with ROV Cancel)
Game.setupSkillJoystickControls = function() {
    if (this._skillJoystickInitialized) return;
    this._skillJoystickInitialized = true;

    let activeTouchId: number | null = null;
    let startX = 0;
    let startY = 0;
    let activeSlot = 0;
    let activeSlotEl: HTMLElement | null = null;
    let isDraggingAim = false;
    let cancelRect: { cx: number; cy: number; radius: number } | null = null;

    const cacheCancelZone = () => {
        const cancelZone = document.getElementById('skillCancelZone');
        if (cancelZone) {
            cancelZone.style.display = 'flex';
            const r = cancelZone.getBoundingClientRect();
            cancelRect = {
                cx: r.left + r.width / 2,
                cy: r.top + r.height / 2,
                radius: Math.max(r.width * 0.75, 55)
            };
        }
    };

    const hideCancelZone = () => {
        cancelRect = null;
        const cancelZone = document.getElementById('skillCancelZone');
        if (cancelZone) {
            cancelZone.style.display = 'none';
            cancelZone.classList.remove('is-hovered');
        }
    };

    // Global Delegated Touchstart for Skill Buttons
    document.addEventListener('touchstart', (e: TouchEvent) => {
        const slotEl = (e.target as HTMLElement)?.closest?.('.active-skill-slot, .touch-skill-btn') as HTMLElement;
        if (!slotEl) return;
        const slot = parseInt(slotEl.getAttribute('data-slot') || '0', 10);
        if (!slot) return;

        e.preventDefault();
        e.stopPropagation();
        const touch = e.changedTouches[0];
        activeTouchId = touch.identifier;
        startX = touch.clientX;
        startY = touch.clientY;
        activeSlot = slot;
        activeSlotEl = slotEl;
        isDraggingAim = false;
        this.activeSkillCancelled = false;
        cacheCancelZone();

        SoundEngine.init();
        if (SoundEngine.isBgmOn()) SoundEngine.startBgm();
    }, { passive: false });

    window.addEventListener('touchmove', (e: TouchEvent) => {
        if (activeTouchId === null || !activeSlotEl) return;
        let touch: Touch | null = null;
        for (let i = 0; i < e.touches.length; i++) {
            if (e.touches[i].identifier === activeTouchId) {
                touch = e.touches[i];
                break;
            }
        }
        if (!touch) return;

        const dx = touch.clientX - startX;
        const dy = touch.clientY - startY;
        const dist = Math.hypot(dx, dy);

        if (dist > 12) {
            isDraggingAim = true;
            this.activeSkillAiming = true;
            this.activeSkillAimSlot = activeSlot;
            
            // Butter-smooth angular interpolation (Zero jitter)
            const targetAngle = Math.atan2(dy, dx);
            if (this.skillAimAngle === null || this.skillAimAngle === undefined) {
                this.skillAimAngle = targetAngle;
            } else {
                let diff = targetAngle - this.skillAimAngle;
                while (diff < -Math.PI) diff += Math.PI * 2;
                while (diff > Math.PI) diff -= Math.PI * 2;
                this.skillAimAngle += diff * 0.55;
            }
            this.skillAimDistRatio = Math.min(1.0, (dist - 12) / 70);

            // Fast cancel zone check (Zero getBoundingClientRect in touchmove!)
            if (cancelRect) {
                const distToCancel = Math.hypot(touch.clientX - cancelRect.cx, touch.clientY - cancelRect.cy);
                const isHover = distToCancel < cancelRect.radius;
                this.activeSkillCancelled = isHover;
                const cz = document.getElementById('skillCancelZone');
                if (cz) cz.classList.toggle('is-hovered', isHover);
            }
        }
    }, { passive: false });

    const endSkillTouch = (e: TouchEvent) => {
        if (activeTouchId === null) return;
        let stillTouch = false;
        for (let i = 0; i < e.touches.length; i++) {
            if (e.touches[i].identifier === activeTouchId) {
                stillTouch = true;
                break;
            }
        }
        if (stillTouch) return;

        hideCancelZone();

        if (activeSlotEl) {
            activeSlotEl.style.transform = '';
            activeSlotEl.style.boxShadow = '';
        }

        const slotToTrigger = activeSlot;
        const wasAiming = isDraggingAim;
        const wasCancelled = !!this.activeSkillCancelled;
        const finalAngle = this.skillAimAngle;

        activeTouchId = null;
        activeSlotEl = null;
        this.activeSkillAiming = false;
        this.activeSkillCancelled = false;
        this.skillAimAngle = null;

        if (wasCancelled) {
            this.addFloatingText('✕ ยกเลิกสกิล', this.player.x, this.player.y - 15, '#ef4444');
            return;
        }

        if (wasAiming && finalAngle !== null) {
            this.skillAimAngle = finalAngle;
            this.triggerPlayerSkill(slotToTrigger);
            this.skillAimAngle = null;
        } else {
            this.triggerPlayerSkill(slotToTrigger);
        }
    };

    window.addEventListener('touchend', endSkillTouch, { passive: false });
    window.addEventListener('touchcancel', endSkillTouch, { passive: false });

    // Global Delegated Mousedown for Desktop Mouse Drag
    let isMouseDown = false;
    document.addEventListener('mousedown', (e: MouseEvent) => {
        const slotEl = (e.target as HTMLElement)?.closest?.('.active-skill-slot, .touch-skill-btn') as HTMLElement;
        if (!slotEl) return;
        const slot = parseInt(slotEl.getAttribute('data-slot') || '0', 10);
        if (!slot) return;

        isMouseDown = true;
        startX = e.clientX;
        startY = e.clientY;
        activeSlot = slot;
        activeSlotEl = slotEl;
        isDraggingAim = false;
        this.activeSkillCancelled = false;
        cacheCancelZone();
    });

    window.addEventListener('mousemove', (e: MouseEvent) => {
        if (!isMouseDown || !activeSlotEl) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        const dist = Math.hypot(dx, dy);

        if (dist > 10) {
            isDraggingAim = true;
            this.activeSkillAiming = true;
            this.activeSkillAimSlot = activeSlot;
            this.skillAimAngle = Math.atan2(dy, dx);
            if (cancelRect) {
                const distToCancel = Math.hypot(e.clientX - cancelRect.cx, e.clientY - cancelRect.cy);
                const isHover = distToCancel < cancelRect.radius;
                this.activeSkillCancelled = isHover;
                const cz = document.getElementById('skillCancelZone');
                if (cz) cz.classList.toggle('is-hovered', isHover);
            }

            const maxTilt = 18;
            const tiltX = Math.cos(this.skillAimAngle) * Math.min(dist, maxTilt);
            const tiltY = Math.sin(this.skillAimAngle) * Math.min(dist, maxTilt);
            activeSlotEl.style.transform = `translate(${tiltX}px, ${tiltY}px) scale(1.12)`;
            if (this.activeSkillCancelled) {
                activeSlotEl.style.boxShadow = `0 0 18px #ef4444, 0 0 10px #b91c1c`;
            } else {
                activeSlotEl.style.boxShadow = `0 0 16px #38bdf8, 0 0 8px #facc15`;
            }
        }
    });

    window.addEventListener('mouseup', () => {
        if (!isMouseDown) return;
        isMouseDown = false;
        hideCancelZone();

        if (activeSlotEl) {
            activeSlotEl.style.transform = '';
            activeSlotEl.style.boxShadow = '';
        }
        const slotToTrigger = activeSlot;
        const wasAiming = isDraggingAim;
        const wasCancelled = !!this.activeSkillCancelled;
        const finalAngle = this.skillAimAngle;

        activeSlotEl = null;
        this.activeSkillAiming = false;
        this.activeSkillCancelled = false;
        this.skillAimAngle = null;

        if (wasCancelled) {
            this.addFloatingText('✕ ยกเลิกสกิล', this.player.x, this.player.y - 15, '#ef4444');
            return;
        }

        if (wasAiming && finalAngle !== null) {
            this.skillAimAngle = finalAngle;
            this.triggerPlayerSkill(slotToTrigger);
            this.skillAimAngle = null;
        } else {
            this.triggerPlayerSkill(slotToTrigger);
        }
    });
};

if (typeof window !== 'undefined') {
    setTimeout(() => {
        if (typeof Game.setupSkillJoystickControls === 'function') {
            Game.setupSkillJoystickControls();
        }
    }, 100);
}

// Draw Canvas Active Skill Visuals
Game.drawActiveSkillVisuals = function(ctx) {
    // 0. Contextual Skill Aim Indicator (Mobile & Mouse Drag Aim)
    if (this.activeSkillAiming && this.skillAimAngle !== null && this.skillAimAngle !== undefined && this.player) {
        const px = Math.round(this.player.x + 12 - this.camera.x);
        const py = Math.round(this.player.y + 14 - this.camera.y);
        const ang = this.skillAimAngle;
        const isCancelled = !!this.activeSkillCancelled;

        // Detect Skill Category
        const cls = CLASS_SKILLS[this.player.activeClass || 'warrior'];
        const currentSkill = cls?.skills?.find(s => s.slot === this.activeSkillAimSlot);
        const skillId = currentSkill ? currentSkill.id : '';

        // Category A: 360-Degree Self AoE (Cyclone, Glacial Ring, Sanctuary Pylon, Judgement)
        const isAoeSelf = ['cyclone_slash', 'glacial_ring', 'sanctuary_pylon', 'judgement_blade'].includes(skillId);
        // Category B: Ground Target AoE (Meteor, Venom Trap)
        const isGroundAoe = ['meteor_cataclysm', 'venom_trap'].includes(skillId);
        // Category C: Self Buff / Healing (Ironclad, Prism Shield, Shadow Dash, Divine Heal)
        const isSelfBuff = ['ironclad_bastion', 'prism_shield', 'shadow_dash', 'divine_heal'].includes(skillId);

        ctx.save();
        ctx.shadowColor = isCancelled ? '#ef4444' : '#38bdf8';
        ctx.shadowBlur = 12;

        if (isAoeSelf) {
            // Draw Full 360-Degree Radial Blast Area around player
            const radius = (skillId === 'judgement_blade') ? 220 : ((skillId === 'glacial_ring') ? 160 : 140);
            ctx.strokeStyle = isCancelled ? '#ef4444' : '#facc15';
            ctx.lineWidth = 3;
            ctx.setLineDash([10, 8]);
            ctx.beginPath();
            ctx.arc(px, py, radius, 0, Math.PI * 2);
            ctx.stroke();

            ctx.fillStyle = isCancelled ? 'rgba(239, 68, 68, 0.12)' : 'rgba(250, 204, 21, 0.14)';
            ctx.beginPath();
            ctx.arc(px, py, radius, 0, Math.PI * 2);
            ctx.fill();

            ctx.setLineDash([]);
            ctx.fillStyle = isCancelled ? '#fee2e2' : '#fef08a';
            ctx.font = 'bold 12px "Prompt", sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(isCancelled ? '✕ ยกเลิก' : (currentSkill?.name || 'โจมตีรอบตัว 360°') + ' (รัศมี ' + radius + 'px)', px, py - radius - 10);
        } else if (isGroundAoe) {
            // Draw Ground Target Reticle
            const castDist = 70 + (this.skillAimDistRatio || 0.6) * 140;
            const gx = px + Math.cos(ang) * castDist;
            const gy = py + Math.sin(ang) * castDist;
            const groundRadius = 100;

            ctx.strokeStyle = isCancelled ? '#ef4444' : '#fb923c';
            ctx.lineWidth = 2.5;
            ctx.setLineDash([8, 6]);
            ctx.beginPath();
            ctx.moveTo(px, py);
            ctx.lineTo(gx, gy);
            ctx.stroke();

            ctx.setLineDash([]);
            ctx.strokeStyle = isCancelled ? '#ef4444' : '#ea580c';
            ctx.lineWidth = 3;
            ctx.fillStyle = isCancelled ? 'rgba(239, 68, 68, 0.15)' : 'rgba(234, 88, 12, 0.2)';
            ctx.beginPath();
            ctx.arc(gx, gy, groundRadius, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();

            ctx.fillStyle = isCancelled ? '#fee2e2' : '#fed7aa';
            ctx.font = 'bold 12px "Prompt", sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(isCancelled ? '✕ ยกเลิก' : (currentSkill?.name || 'จุดตกบนพื้น') + ' (รัศมี 100px)', gx, gy - groundRadius - 8);
        } else if (isSelfBuff) {
            // Self Buff / Heal protective aura
            ctx.strokeStyle = isCancelled ? '#ef4444' : '#4ade80';
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.arc(px, py, 50, 0, Math.PI * 2);
            ctx.stroke();
            ctx.fillStyle = isCancelled ? 'rgba(239, 68, 68, 0.12)' : 'rgba(74, 222, 128, 0.15)';
            ctx.beginPath();
            ctx.arc(px, py, 50, 0, Math.PI * 2);
            ctx.fill();

            ctx.fillStyle = isCancelled ? '#fee2e2' : '#bbf7d0';
            ctx.font = 'bold 12px "Prompt", sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(isCancelled ? '✕ ยกเลิก' : (currentSkill?.name || 'บัฟเสริมพลัง') + ' (ร่ายใส่ตัวเอง)', px, py - 60);
        } else {
            // Directional Skillshot Beam
            const range = (skillId === 'dragonpiercer') ? 450 : ((skillId === 'flash_thrust') ? 180 : 220);
            const tx = px + Math.cos(ang) * range;
            const ty = py + Math.sin(ang) * range;

            ctx.strokeStyle = isCancelled ? '#ef4444' : '#38bdf8';
            ctx.lineWidth = 3;
            ctx.setLineDash([8, 6]);
            ctx.beginPath();
            ctx.moveTo(px, py);
            ctx.lineTo(tx, ty);
            ctx.stroke();

            ctx.setLineDash([]);
            ctx.fillStyle = isCancelled ? '#ef4444' : '#fde047';
            ctx.beginPath();
            const arrowSize = 14;
            const a1 = ang + Math.PI - 0.45;
            const a2 = ang + Math.PI + 0.45;
            ctx.moveTo(tx, ty);
            ctx.lineTo(tx + Math.cos(a1) * arrowSize, ty + Math.sin(a1) * arrowSize);
            ctx.lineTo(tx + Math.cos(a2) * arrowSize, ty + Math.sin(a2) * arrowSize);
            ctx.closePath();
            ctx.fill();

            ctx.strokeStyle = isCancelled ? '#ef4444' : '#38bdf8';
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            ctx.arc(tx, ty, 18, 0, Math.PI * 2);
            ctx.stroke();

            ctx.fillStyle = isCancelled ? '#fee2e2' : '#e0f2fe';
            ctx.font = 'bold 12px "Prompt", sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(isCancelled ? '✕ ยกเลิก' : (currentSkill?.name || 'เล็งยิงเส้นตรง'), tx, ty - 24);
        }

        ctx.restore();
    }

    if (!this.activeSkillVisuals || this.activeSkillVisuals.length === 0) return;

    this.activeSkillVisuals.forEach(v => {
        const sx = Math.round(v.x - this.camera.x);
        const sy = Math.round(v.y - this.camera.y);
        const progress = Math.min(1, Math.max(0, 1 - (v.timer / v.maxTimer)));
        const alpha = Math.max(0, 1 - progress);

        ctx.save();

        if (v.type === 'cyclone') {
            // Cyclone Slash - Multi-layer golden & electric vortex
            const curR = v.radius * (0.35 + progress * 0.65);
            const rot = progress * Math.PI * 6;

            ctx.shadowColor = '#facc15';
            ctx.shadowBlur = 18;

            // Outer golden blade arc
            ctx.strokeStyle = `rgba(250, 204, 21, ${alpha * 0.95})`;
            ctx.lineWidth = 6;
            ctx.beginPath();
            ctx.arc(sx, sy, curR, rot, rot + Math.PI * 1.5);
            ctx.stroke();

            // Inner counter-rotating cyan wind blade
            ctx.strokeStyle = `rgba(56, 189, 248, ${alpha * 0.9})`;
            ctx.lineWidth = 4;
            ctx.beginPath();
            ctx.arc(sx, sy, curR * 0.72, -rot * 1.2, -rot * 1.2 + Math.PI * 1.3);
            ctx.stroke();

            // Core whirlwind flash
            ctx.fillStyle = `rgba(254, 240, 138, ${alpha * 0.4})`;
            ctx.beginPath();
            ctx.arc(sx, sy, curR * 0.4, 0, Math.PI * 2);
            ctx.fill();

        } else if (v.type === 'slash_line') {
            // Flash Thrust - Piercing hyper-speed laser trail
            const x1 = Math.round(v.x1 - this.camera.x);
            const y1 = Math.round(v.y1 - this.camera.y);
            const x2 = Math.round(v.x2 - this.camera.x);
            const y2 = Math.round(v.y2 - this.camera.y);

            ctx.shadowColor = '#38bdf8';
            ctx.shadowBlur = 20;

            // Outer cyan flare
            ctx.strokeStyle = `rgba(56, 189, 248, ${alpha * 0.5})`;
            ctx.lineWidth = 18;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();

            // Middle beam
            ctx.strokeStyle = `rgba(125, 211, 252, ${alpha * 0.85})`;
            ctx.lineWidth = 7;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();

            // Center blinding white core
            ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();

            // Destination sonic shockwave ring
            ctx.strokeStyle = `rgba(56, 189, 248, ${alpha * 0.8})`;
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.arc(x2, y2, 28 * progress, 0, Math.PI * 2);
            ctx.stroke();

        } else if (v.type === 'shield_barrier') {
            // Ironclad Bastion - Radiant golden hexagonal aegis forcefield
            const pulse = (Math.sin(performance.now() / 160) + 1) * 0.5;
            const shieldR = v.radius * (0.95 + pulse * 0.08);

            ctx.shadowColor = '#facc15';
            ctx.shadowBlur = 16;

            // Hexagonal barrier path
            ctx.beginPath();
            for (let i = 0; i < 6; i++) {
                const ang = (i / 6) * Math.PI * 2 + performance.now() * 0.0015;
                const hx = sx + Math.cos(ang) * shieldR;
                const hy = sy + Math.sin(ang) * shieldR;
                if (i === 0) ctx.moveTo(hx, hy);
                else ctx.lineTo(hx, hy);
            }
            ctx.closePath();
            ctx.fillStyle = `rgba(250, 204, 21, ${0.22 + pulse * 0.1})`;
            ctx.fill();
            ctx.strokeStyle = '#fef08a';
            ctx.lineWidth = 3;
            ctx.stroke();

            // Vertex diamond gems
            for (let i = 0; i < 6; i++) {
                const ang = (i / 6) * Math.PI * 2 + performance.now() * 0.0015;
                const hx = sx + Math.cos(ang) * shieldR;
                const hy = sy + Math.sin(ang) * shieldR;
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(hx - 2, hy - 2, 4, 4);
            }

        } else if (v.type === 'judgement_sword') {
            // Judgement Blade [ULTIMATE] - Colossal Celestial Golden Greatsword & Holy Crater
            ctx.shadowColor = '#fde047';
            ctx.shadowBlur = 24;

            const dropProg = Math.min(1, progress * 2.2);
            const swordY = (sy - 220) + 220 * dropProg;

            // 1. Holy golden sword plunging down
            ctx.fillStyle = '#fef08a';
            ctx.fillRect(sx - 5, swordY - 95, 10, 95); // Blade
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(sx - 2, swordY - 90, 4, 85); // Inner spine
            ctx.fillStyle = '#facc15';
            ctx.fillRect(sx - 16, swordY - 95, 32, 6); // Crossguard
            ctx.fillRect(sx - 3, swordY - 110, 6, 15); // Hilt
            ctx.fillStyle = '#38bdf8';
            ctx.fillRect(sx - 4, swordY - 114, 8, 4); // Pommel gem

            // 2. Blast & shockwave upon landing
            if (progress > 0.25) {
                const blastProg = (progress - 0.25) / 0.75;
                const blastAlpha = 1 - blastProg;
                const curR = v.radius * blastProg;

                // Ground holy explosion ring
                ctx.strokeStyle = `rgba(253, 224, 71, ${blastAlpha * 0.9})`;
                ctx.lineWidth = 5;
                ctx.beginPath();
                ctx.arc(sx, sy, curR, 0, Math.PI * 2);
                ctx.stroke();

                // Ground radial rays
                ctx.strokeStyle = `rgba(254, 240, 138, ${blastAlpha * 0.6})`;
                ctx.lineWidth = 2;
                for (let r = 0; r < 8; r++) {
                    const rayAng = (r / 8) * Math.PI * 2;
                    ctx.beginPath();
                    ctx.moveTo(sx, sy);
                    ctx.lineTo(sx + Math.cos(rayAng) * curR, sy + Math.sin(rayAng) * curR);
                    ctx.stroke();
                }

                // Inner holy flash
                ctx.fillStyle = `rgba(254, 240, 138, ${blastAlpha * 0.35})`;
                ctx.beginPath();
                ctx.arc(sx, sy, curR * 0.6, 0, Math.PI * 2);
                ctx.fill();
            }

        } else if (v.type === 'fire_blast') {
            // Pyroclast Orb explosion blast
            const curR = v.radius * (0.3 + progress * 0.7);
            ctx.shadowColor = '#ea580c';
            ctx.shadowBlur = 18;

            const grad = ctx.createRadialGradient(sx, sy, 2, sx, sy, curR);
            grad.addColorStop(0, `rgba(255, 255, 255, ${alpha})`);
            grad.addColorStop(0.35, `rgba(250, 204, 21, ${alpha * 0.85})`);
            grad.addColorStop(0.7, `rgba(234, 88, 12, ${alpha * 0.6})`);
            grad.addColorStop(1, 'rgba(239, 68, 68, 0)');
            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(sx, sy, curR, 0, Math.PI * 2);
            ctx.fill();

            ctx.strokeStyle = `rgba(249, 115, 22, ${alpha * 0.8})`;
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.arc(sx, sy, curR * 0.9, 0, Math.PI * 2);
            ctx.stroke();

        } else if (v.type === 'frost_ring') {
            // Glacial Ring - Expanding frozen crystal shockwave
            const curR = v.radius * (0.25 + progress * 0.75);
            ctx.shadowColor = '#38bdf8';
            ctx.shadowBlur = 20;

            // Ice mist fill
            ctx.fillStyle = `rgba(56, 189, 248, ${alpha * 0.22})`;
            ctx.beginPath();
            ctx.arc(sx, sy, curR, 0, Math.PI * 2);
            ctx.fill();

            // Main ice ring
            ctx.strokeStyle = `rgba(125, 211, 252, ${alpha * 0.95})`;
            ctx.lineWidth = 4;
            ctx.beginPath();
            ctx.arc(sx, sy, curR, 0, Math.PI * 2);
            ctx.stroke();

            // Radial ice crystal spikes
            for (let i = 0; i < 12; i++) {
                const ang = (i / 12) * Math.PI * 2 + progress * 0.3;
                const ix = sx + Math.cos(ang) * curR;
                const iy = sy + Math.sin(ang) * curR;
                const tipX = sx + Math.cos(ang) * (curR + 12 * (1 - progress));
                const tipY = sy + Math.sin(ang) * (curR + 12 * (1 - progress));
                ctx.beginPath();
                ctx.moveTo(ix, iy);
                ctx.lineTo(tipX, tipY);
                ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
                ctx.lineWidth = 2.5;
                ctx.stroke();
            }

        } else if (v.type === 'prism_orbs') {
            // Prism Shield - 3 Orbiting Prismatic Crystal Orbs & Laser Forcefield
            const orbitR = 46;
            const baseAng = performance.now() * 0.003;
            const colors = ['#c084fc', '#38bdf8', '#facc15'];

            ctx.shadowColor = '#c084fc';
            ctx.shadowBlur = 14;

            const orbPts = [];
            for (let i = 0; i < 3; i++) {
                const ang = baseAng + (i * Math.PI * 2) / 3;
                const ox = sx + Math.cos(ang) * orbitR;
                const oy = sy + Math.sin(ang) * orbitR;
                orbPts.push({ x: ox, y: oy, color: colors[i] });
            }

            // Triangular forcefield connection
            ctx.strokeStyle = 'rgba(192, 132, 252, 0.4)';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(orbPts[0].x, orbPts[0].y);
            ctx.lineTo(orbPts[1].x, orbPts[1].y);
            ctx.lineTo(orbPts[2].x, orbPts[2].y);
            ctx.closePath();
            ctx.stroke();

            // Draw glowing diamond crystal for each orb
            orbPts.forEach(o => {
                ctx.fillStyle = o.color;
                ctx.beginPath();
                ctx.arc(o.x, o.y, 5.5, 0, Math.PI * 2);
                ctx.fill();

                ctx.fillStyle = '#ffffff';
                ctx.beginPath();
                ctx.arc(o.x, o.y, 2.5, 0, Math.PI * 2);
                ctx.fill();
            });

        } else if (v.type === 'meteor_strike') {
            // Meteor Cataclysm [ULTIMATE] - Falling Magma Rock & Ground Crater Explosion
            ctx.shadowColor = '#ea580c';
            ctx.shadowBlur = 22;

            if (progress < 0.35) {
                // Incoming meteor streak
                const dropProg = progress / 0.35;
                const mx = (sx + 60) - 60 * dropProg;
                const my = (sy - 140) + 140 * dropProg;

                ctx.fillStyle = '#ea580c';
                ctx.beginPath();
                ctx.arc(mx, my, 8, 0, Math.PI * 2);
                ctx.fill();

                // Fire trail
                ctx.strokeStyle = 'rgba(250, 204, 21, 0.7)';
                ctx.lineWidth = 6;
                ctx.beginPath();
                ctx.moveTo(mx, my);
                ctx.lineTo(mx + 30, my - 60);
                ctx.stroke();
            } else {
                // Impact explosion
                const blastProg = (progress - 0.35) / 0.65;
                const blastAlpha = 1 - blastProg;
                const curR = v.radius * (0.3 + blastProg * 0.7);

                const grad = ctx.createRadialGradient(sx, sy, 2, sx, sy, curR);
                grad.addColorStop(0, `rgba(255, 255, 255, ${blastAlpha})`);
                grad.addColorStop(0.3, `rgba(254, 240, 138, ${blastAlpha * 0.9})`);
                grad.addColorStop(0.65, `rgba(234, 88, 12, ${blastAlpha * 0.7})`);
                grad.addColorStop(1, 'rgba(185, 28, 28, 0)');
                ctx.fillStyle = grad;
                ctx.beginPath();
                ctx.arc(sx, sy, curR, 0, Math.PI * 2);
                ctx.fill();

                ctx.strokeStyle = `rgba(251, 146, 60, ${blastAlpha * 0.9})`;
                ctx.lineWidth = 3.5;
                ctx.beginPath();
                ctx.arc(sx, sy, curR, 0, Math.PI * 2);
                ctx.stroke();
            }

        } else if (v.type === 'arrow_barrage_cone') {
            // Arrow Barrage - Emerald piercing wind spread cone
            const curLen = 95 * progress;
            ctx.shadowColor = '#4ade80';
            ctx.shadowBlur = 15;

            [-0.28, -0.14, 0, 0.14, 0.28].forEach(off => {
                const a = v.angle + off;
                const ex = sx + Math.cos(a) * curLen;
                const ey = sy + Math.sin(a) * curLen;

                ctx.strokeStyle = `rgba(74, 222, 128, ${alpha * 0.85})`;
                ctx.lineWidth = 3.5;
                ctx.beginPath();
                ctx.moveTo(sx, sy);
                ctx.lineTo(ex, ey);
                ctx.stroke();

                ctx.fillStyle = '#ffffff';
                ctx.fillRect(ex - 2, ey - 2, 4, 4);
            });

        } else if (v.type === 'poison_trap') {
            // Venom Trap - Toxic Bramble Rune Mire
            const pulse = (Math.sin(performance.now() / 200) + 1) * 0.5;

            ctx.shadowColor = '#22c55e';
            ctx.shadowBlur = 12;

            ctx.fillStyle = `rgba(34, 197, 94, ${0.28 + pulse * 0.1})`;
            ctx.beginPath();
            ctx.arc(sx, sy, v.radius, 0, Math.PI * 2);
            ctx.fill();

            ctx.strokeStyle = '#15803d';
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            ctx.arc(sx, sy, v.radius, 0, Math.PI * 2);
            ctx.stroke();

            // Thorny thorns along ring
            for (let i = 0; i < 8; i++) {
                const ang = (i / 8) * Math.PI * 2;
                const tx = sx + Math.cos(ang) * v.radius;
                const ty = sy + Math.sin(ang) * v.radius;
                ctx.fillStyle = '#4ade80';
                ctx.fillRect(tx - 3, ty - 3, 6, 6);
            }

            // Center marker
            ctx.fillStyle = '#86efac';
            ctx.font = 'bold 12px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('★', sx, sy + 4);

        } else if (v.type === 'shadow_trail') {
            // Shadow Dash - Shadowy phantom silhouettes & speed lines
            ctx.fillStyle = `rgba(71, 85, 105, ${alpha * 0.45})`;
            ctx.beginPath();
            ctx.arc(sx, sy, 18, 0, Math.PI * 2);
            ctx.fill();

            ctx.strokeStyle = `rgba(168, 85, 247, ${alpha * 0.6})`;
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.arc(sx, sy, 24 * (1 - progress), 0, Math.PI * 2);
            ctx.stroke();

        } else if (v.type === 'lightning_beam_line') {
            // Dragonpiercer [ULTIMATE] - Colossal Electrifying Piercing Lightning Beam
            const ex = sx + Math.cos(v.angle) * v.length;
            const ey = sy + Math.sin(v.angle) * v.length;

            ctx.shadowColor = '#38bdf8';
            ctx.shadowBlur = 28;

            // Outer cyan laser aura
            ctx.strokeStyle = `rgba(56, 189, 248, ${alpha * 0.45})`;
            ctx.lineWidth = 24;
            ctx.beginPath();
            ctx.moveTo(sx, sy);
            ctx.lineTo(ex, ey);
            ctx.stroke();

            // Middle electric blue beam
            ctx.strokeStyle = `rgba(125, 211, 252, ${alpha * 0.85})`;
            ctx.lineWidth = 10;
            ctx.beginPath();
            ctx.moveTo(sx, sy);
            ctx.lineTo(ex, ey);
            ctx.stroke();

            // Inner bright white lightning laser
            ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
            ctx.lineWidth = 4;
            ctx.beginPath();
            ctx.moveTo(sx, sy);
            ctx.lineTo(ex, ey);
            ctx.stroke();

            // Branching jagged lightning sparks along beam
            const segCount = 8;
            for (let s = 1; s < segCount; s++) {
                const t = s / segCount;
                const bx = sx + (ex - sx) * t;
                const by = sy + (ey - sy) * t;
                const perpX = -Math.sin(v.angle);
                const perpY = Math.cos(v.angle);
                const sparkDist = (Math.random() - 0.5) * 36;

                ctx.strokeStyle = `rgba(253, 224, 71, ${alpha * 0.9})`;
                ctx.lineWidth = 2.5;
                ctx.beginPath();
                ctx.moveTo(bx, by);
                ctx.lineTo(bx + perpX * sparkDist, by + perpY * sparkDist);
                ctx.stroke();
            }

            // Launch discharge flash at player
            ctx.fillStyle = `rgba(255, 255, 255, ${alpha * 0.8})`;
            ctx.beginPath();
            ctx.arc(sx, sy, 22, 0, Math.PI * 2);
            ctx.fill();

        } else if (v.type === 'radiant_burst') {
            // Radiant Spear launch flare
            ctx.shadowColor = '#facc15';
            ctx.shadowBlur = 18;

            const curR = 35 * progress;
            ctx.strokeStyle = `rgba(250, 204, 21, ${alpha})`;
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.arc(sx, sy, curR, 0, Math.PI * 2);
            ctx.stroke();

            for (let r = 0; r < 6; r++) {
                const a = (r / 6) * Math.PI * 2;
                ctx.beginPath();
                ctx.moveTo(sx, sy);
                ctx.lineTo(sx + Math.cos(a) * (curR + 10), sy + Math.sin(a) * (curR + 10));
                ctx.stroke();
            }

        } else if (v.type === 'heal_aura') {
            // Divine Benediction - Rising Heavenly Light & Ascending Cross Glyphs
            ctx.shadowColor = '#4ade80';
            ctx.shadowBlur = 18;

            // Translucent emerald cylinder
            const grad = ctx.createLinearGradient(sx, sy + 15, sx, sy - 50);
            grad.addColorStop(0, `rgba(74, 222, 128, ${alpha * 0.4})`);
            grad.addColorStop(1, 'rgba(254, 240, 138, 0)');
            ctx.fillStyle = grad;
            ctx.fillRect(sx - 20, sy - 50, 40, 65);

            // Ground holy ring
            ctx.strokeStyle = `rgba(74, 222, 128, ${alpha * 0.9})`;
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            ctx.ellipse(sx, sy + 10, 26, 12, 0, 0, Math.PI * 2);
            ctx.stroke();

            // Ascending cross glyph
            const crossY = sy - 10 - progress * 45;
            ctx.fillStyle = `rgba(254, 240, 138, ${alpha})`;
            ctx.fillRect(sx - 3, crossY - 10, 6, 20);
            ctx.fillRect(sx - 8, crossY - 5, 16, 6);

        } else if (v.type === 'holy_sanctuary') {
            // Sanctuary Pylon - Consecrated Golden Ground & Obelisk
            const pulse = (Math.sin(performance.now() / 220) + 1) * 0.5;
            ctx.shadowColor = '#facc15';
            ctx.shadowBlur = 16;

            // Consecrated holy ground circle
            ctx.fillStyle = `rgba(250, 204, 21, ${0.22 + pulse * 0.08})`;
            ctx.beginPath();
            ctx.arc(sx, sy, v.radius, 0, Math.PI * 2);
            ctx.fill();

            ctx.strokeStyle = '#eab308';
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.arc(sx, sy, v.radius, 0, Math.PI * 2);
            ctx.stroke();

            // Pylon monument at center
            ctx.fillStyle = '#fde047';
            ctx.fillRect(sx - 4, sy - 28, 8, 28);
            ctx.fillStyle = '#f59e0b';
            ctx.fillRect(sx - 7, sy - 4, 14, 5);
            // Sun gem on top of obelisk
            ctx.fillStyle = '#ffffff';
            ctx.beginPath();
            ctx.arc(sx, sy - 30, 4.5, 0, Math.PI * 2);
            ctx.fill();

            // 4 Cardinal markers
            [0, Math.PI / 2, Math.PI, Math.PI * 1.5].forEach(ang => {
                const mx = sx + Math.cos(ang) * v.radius;
                const my = sy + Math.sin(ang) * v.radius;
                ctx.fillStyle = '#fde047';
                ctx.fillRect(mx - 3, my - 3, 6, 6);
            });

        } else if (v.type === 'heaven_pillar') {
            // Wrath of the Heavens [ULTIMATE] - Colossal Celestial Column of Light
            ctx.shadowColor = '#fef08a';
            ctx.shadowBlur = 32;

            const beamTop = sy - 420;
            const beamBot = sy + 20;

            // Outer halo column
            ctx.fillStyle = `rgba(253, 224, 71, ${alpha * 0.4})`;
            ctx.fillRect(sx - 55, beamTop, 110, beamBot - beamTop);

            // Middle golden beam
            ctx.fillStyle = `rgba(254, 240, 138, ${alpha * 0.75})`;
            ctx.fillRect(sx - 28, beamTop, 56, beamBot - beamTop);

            // Center blinding white core
            ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
            ctx.fillRect(sx - 10, beamTop, 20, beamBot - beamTop);

            // Ground impact shockwave
            const curR = v.radius * (0.35 + progress * 0.65);
            ctx.strokeStyle = `rgba(253, 224, 71, ${alpha * 0.95})`;
            ctx.lineWidth = 5;
            ctx.beginPath();
            ctx.arc(sx, sy, curR, 0, Math.PI * 2);
            ctx.stroke();

            // Radial divine sparks
            ctx.strokeStyle = `rgba(255, 255, 255, ${alpha * 0.8})`;
            ctx.lineWidth = 2.5;
            for (let i = 0; i < 12; i++) {
                const a = (i / 12) * Math.PI * 2;
                ctx.beginPath();
                ctx.moveTo(sx, sy);
                ctx.lineTo(sx + Math.cos(a) * (curR + 15), sy + Math.sin(a) * (curR + 15));
                ctx.stroke();
            }
        } else if (v.type === 'parry_flash') {
            // Perfect Parry Golden Shockwave & Radiant Burst
            const curR = v.radius * (0.2 + progress * 0.8);
            ctx.shadowColor = '#fbbf24';
            ctx.shadowBlur = 24;

            // Outer radiant gold ring
            ctx.strokeStyle = `rgba(251, 191, 36, ${alpha * 0.95})`;
            ctx.lineWidth = 4;
            ctx.beginPath();
            ctx.arc(sx, sy, curR, 0, Math.PI * 2);
            ctx.stroke();

            // Inner white shockwave
            ctx.strokeStyle = `rgba(255, 255, 255, ${alpha * 0.9})`;
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            ctx.arc(sx, sy, curR * 0.65, 0, Math.PI * 2);
            ctx.stroke();

            // Cross Star Flare Rays
            ctx.strokeStyle = `rgba(254, 240, 138, ${alpha})`;
            ctx.lineWidth = 3;
            const rayLen = curR * 1.3;
            ctx.beginPath();
            ctx.moveTo(sx - rayLen, sy);
            ctx.lineTo(sx + rayLen, sy);
            ctx.moveTo(sx, sy - rayLen);
            ctx.lineTo(sx, sy + rayLen);
            ctx.stroke();

            // Center blinding flash
            ctx.fillStyle = `rgba(255, 255, 255, ${alpha * 0.8})`;
            ctx.beginPath();
            ctx.arc(sx, sy, curR * 0.28, 0, Math.PI * 2);
            ctx.fill();

        } else if (v.type === 'block_spark') {
            // Guard Block Cyan Impact Spark
            ctx.shadowColor = '#38bdf8';
            ctx.shadowBlur = 14;

            ctx.strokeStyle = `rgba(56, 189, 248, ${alpha * 0.9})`;
            ctx.lineWidth = 3;
            ctx.beginPath();
            ctx.arc(sx, sy, 22 * (0.4 + progress * 0.6), 0, Math.PI * 2);
            ctx.stroke();

            // Ricochet spark lines
            for (let i = 0; i < 6; i++) {
                const ang = (i / 6) * Math.PI * 2;
                ctx.strokeStyle = `rgba(224, 242, 254, ${alpha})`;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(sx, sy);
                ctx.lineTo(sx + Math.cos(ang) * (14 + progress * 16), sy + Math.sin(ang) * (14 + progress * 16));
                ctx.stroke();
            }

        } else if (v.type === 'shield_activate') {
            // Raising Shield Flash
            ctx.shadowColor = '#fbbf24';
            ctx.shadowBlur = 10;
            ctx.strokeStyle = `rgba(251, 191, 36, ${alpha * 0.75})`;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(sx, sy, 18 * (0.6 + progress * 0.4), 0, Math.PI * 2);
            ctx.stroke();

        } else if (v.type === 'guard_break') {
            // Guard Break Shatter Shockwave
            ctx.shadowColor = '#ef4444';
            ctx.shadowBlur = 18;
            ctx.strokeStyle = `rgba(239, 68, 68, ${alpha * 0.9})`;
            ctx.lineWidth = 4;
            ctx.beginPath();
            ctx.arc(sx, sy, 32 * (0.3 + progress * 0.7), 0, Math.PI * 2);
            ctx.stroke();
        }

        ctx.restore();
    });
};

// Skill Tree Modal Handlers
Game.openSkillTreeModal = function() {
    this.initPlayerSkills();
    const modal = document.getElementById('activeSkillModal');
    if (!modal) return;
    modal.style.display = 'flex';
    this.renderSkillTreeContent();
};

Game.closeSkillTreeModal = function() {
    const modal = document.getElementById('activeSkillModal');
    if (modal) modal.style.display = 'none';
};

Game.switchSkillClass = function(clsId) {
    if (!CLASS_SKILLS[clsId] || !this.player) return;
    this.player.activeClass = clsId;
    this._renderedSkillClass = null;
    SoundEngine.skillCast();
    this.renderSkillTreeContent();
    this.renderActiveSkillBar();
    this.addFloatingText('★ สลับสู่ ' + CLASS_SKILLS[clsId].name, this.player.x, this.player.y - 20, '#facc15');
};

Game.upgradeSkill = function(skillId) {
    if (!this.player || (this.player.skillPoints || 0) < 1) {
        SoundEngine.errorClick();
        return;
    }
    const currentLv = this.player.skillLevels[skillId] || 1;
    if (currentLv >= 5) {
        SoundEngine.errorClick();
        return;
    }

    this.player.skillPoints -= 1;
    this.player.skillLevels[skillId] = currentLv + 1;
    this._renderedSkillClass = null;
    SoundEngine.skillUpgrade();
    this.triggerScreenShake(3.0, 100);
    this.addFloatingText('★ อัปเกรดสกิลเป็น Lv.' + (currentLv + 1) + '!', this.player.x, this.player.y - 25, '#4ade80');
    this.renderSkillTreeContent();
    this.renderActiveSkillBar();
};

Game.resetSkillPoints = function() {
    if (!this.player) return;
    this.initPlayerSkills();
    let totalPoints = 5 + ((this.player.level || 1) - 1);
    this.player.skillPoints = totalPoints;
    for (const k in this.player.skillLevels) {
        this.player.skillLevels[k] = 1;
    }
    this._renderedSkillClass = null;
    SoundEngine.skillUpgrade();
    this.addFloatingText('★ รีเซ็ตแต้มสกิลทั้งหมด คืน ' + totalPoints + ' SP!', this.player.x - 30, this.player.y - 25, '#38bdf8');
    this.renderSkillTreeContent();
    this.renderActiveSkillBar();
};

Game.renderSkillTreeContent = function() {
    this.initPlayerSkills();
    const spEl = document.getElementById('activeSkillPointsCount');
    if (spEl) spEl.textContent = this.player.skillPoints || 0;

    // Update active tab buttons
    ['warrior', 'mage', 'ranger', 'paladin'].forEach(c => {
        const btn = document.getElementById('tab_' + c);
        if (btn) {
            if (this.player.activeClass === c) btn.classList.add('active');
            else btn.classList.remove('active');
        }
    });

    const listEl = document.getElementById('activeSkillsList');
    if (!listEl) return;

    const cls = CLASS_SKILLS[this.player.activeClass || 'warrior'];
    if (!cls) return;

    let html = '';
    cls.skills.forEach(s => {
        const lv = this.player.skillLevels[s.id] || 1;
        const isMax = lv >= 5;
        const currentDmg = s.baseDmg > 0 ? (s.baseDmg + (lv - 1) * s.dmgPerLv) : 0;
        const nextDmg = s.baseDmg > 0 ? (s.baseDmg + lv * s.dmgPerLv) : 0;
        const cdSec = (s.cd * (1 - (lv - 1) * 0.08) / 1000).toFixed(1);
        const nextCdSec = (s.cd * (1 - lv * 0.08) / 1000).toFixed(1);

        html += `
            <div class="skill-card ${s.isUltimate ? 'ultimate' : ''}">
                <div class="skill-card-header">
                    <span class="skill-card-title">${s.name} (${s.enName})</span>
                    <span class="skill-card-key">[ปุ่ม ${['Z', 'X', 'C', 'V'][s.slot - 1] || s.slot}]</span>
                </div>
                <p class="skill-card-desc">${s.desc}</p>
                <div class="skill-card-stats">
                    <span>${s.baseDmg > 0 ? 'ดาเมจ: ' + currentDmg + (isMax ? ' (MAX)' : ' -> ' + nextDmg) : 'สกิลสนับสนุน/บัฟ'}</span>
                    <span>คูลดาวน์: ${cdSec}s ${!isMax ? '-> ' + nextCdSec + 's' : ''} | ใช้ ${s.energy} E</span>
                </div>
                <div class="skill-card-footer">
                    <span class="skill-level-indicator">ระดับ: Lv.${lv} / 5 ${isMax ? '★ MAX' : ''}</span>
                    <button class="skill-upgrade-btn" ${isMax || (this.player.skillPoints || 0) < 1 ? 'disabled' : ''} onclick="Game.upgradeSkill('${s.id}')">
                        ${isMax ? 'เต็มแล้ว' : '+ อัปเกรด (1 SP)'}
                    </button>
                </div>
            </div>
        `;
    });

    listEl.innerHTML = html;
};

// ========================================================
// 27. ISLAND VOLCANO DUNGEON & MAGMA FORGE
// ========================================================

Game.enterIslandVolcanoDungeon = function() {
    this.volcanoCurrentFloor = 1;
    this.volcanoSwitchActive = false;
    this.generateVolcanoFloor(1);
    this.switchScene('island_volcano', 17, 23);
    SoundEngine.bossDragonBreath();
    this.addFloatingText('เข้าสู่ดันเจี้ยนภูเขาไฟเกาะสมบัติ ชั้น 1!', this.player.x, this.player.y - 20, '#ea580c');
};

Game.exitIslandVolcanoDungeon = function() {
    SoundEngine.door();
    this.switchScene('island', 23, 6);
    this.addFloatingText('ออกจากถ้ำภูเขาไฟ กลับสู่เกาะเขตร้อน', this.player.x, this.player.y - 20, '#38bdf8');
};

Game.proceedVolcanoNextFloor = function() {
    const nextFloor = (this.volcanoCurrentFloor || 1) + 1;
    if (nextFloor > 10) return;
    this.volcanoCurrentFloor = nextFloor;
    this.volcanoSwitchActive = false;
    this.generateVolcanoFloor(nextFloor);
    SoundEngine.bossDragonBreath();
    this.player.x = 17 * 32;
    this.player.y = 23 * 32;
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#f97316', 20);
    this.addFloatingText(`ลงสู่ดันเจี้ยนภูเขาไฟ ชั้น ${nextFloor}!`, this.player.x - 20, this.player.y - 20, '#ea580c');
};

Game.activateVolcanoSwitch = function(tx: number, ty: number) {
    if (this.volcanoSwitchActive) {
        SoundEngine.errorClick();
        this.addFloatingText('คันโยกหินโบราณถูกเปิดใช้งานแล้ว!', tx * 32, ty * 32 - 10, '#94a3b8');
        return;
    }
    this.volcanoSwitchActive = true;
    SoundEngine.miningHit();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#22c55e', 20);
    this.triggerScreenShake(4.0, 150);
    this.addFloatingText('เปิดกลไกสำเร็จ! สะพานหินเชื่อมข้ามธารลาวาแล้ว!', tx * 32 - 40, ty * 32 - 15, '#4ade80');

    // Update lava bridge tiles on this map
    for (let y = 0; y < this.mapHeight; y++) {
        for (let x = 0; x < this.mapWidth; x++) {
            if (this.map[y][x].isLavaBridge) {
                this.map[y][x].solid = false;
                this.map[y][x].type = 'bridge';
            }
        }
    }
};

Game.mineCinderShardNode = function(tx: number, ty: number) {
    if (!this.map[ty] || !this.map[ty][tx]) return;
    const tile = this.map[ty][tx];
    SoundEngine.miningHit();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#f97316', 16);
    this.addItemToInventory('cinder_shard', Math.floor(Math.random() * 2) + 2, 'เศษผลึกเพลิง (Cinder Shard)', 0);
    if (Math.random() < 0.4) {
        this.addItemToInventory('gold_ore', 1, 'แร่ทองคำดิบ', 0);
    }
    this.addFloatingText('+เศษผลึกเพลิง (Cinder Shard)', tx * 32 - 20, ty * 32 - 15, '#f97316');
    this.player.energy = Math.max(0, this.player.energy - 3);

    tile.type = 'magmaFloor';
    tile.solid = false;
    delete tile.interactable;
    this.updateHUD();
};

Game.breakVolcanoUrn = function(tx: number, ty: number) {
    if (!this.map[ty] || !this.map[ty][tx]) return;
    const tile = this.map[ty][tx];
    SoundEngine.potBreak();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#f59e0b', 16);
    
    const goldDrop = Math.floor(Math.random() * 35) + 15;
    this.player.gold = (this.player.gold || 0) + goldDrop;
    if (Math.random() < 0.5) {
        this.addItemToInventory('cinder_shard', 1, 'เศษผลึกเพลิง (Cinder Shard)', 0);
    }
    this.addFloatingText(`+${goldDrop} G`, tx * 32, ty * 32 - 10, '#facc15');

    tile.type = 'magmaFloor';
    tile.solid = false;
    delete tile.interactable;
    this.updateHUD();
};

Game.drinkVolcanoCoolingSpring = function() {
    SoundEngine.gulp();
    this.player.hp = this.player.maxHp;
    this.player.energy = this.player.maxEnergy;
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#38bdf8', 25);
    this.addFloatingText('ดื่มน้ำพุเย็นดับร้อน! ฟื้นฟู HP และพลังงาน 100%!', this.player.x - 40, this.player.y - 20, '#38bdf8');
    this.updateHUD();
};

Game.openVolcanoChest5 = function() {
    if (this.player.volcanoChest5Opened) {
        SoundEngine.errorClick();
        this.addFloatingText('หีบสมบัติจุดพักถูกเปิดไปแล้ว!', this.player.x, this.player.y - 15, '#94a3b8');
        return;
    }
    this.player.volcanoChest5Opened = true;
    SoundEngine.chestOpen();
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#facc15', 30);
    this.player.gold = (this.player.gold || 0) + 500;
    this.addItemToInventory('cinder_shard', 10, 'เศษผลึกเพลิง', 0);
    this.addItemToInventory('gold_ore', 5, 'แร่ทองคำดิบ', 0);
    this.addItemToInventory('tropical_delight_drink', 2, 'ค็อกเทลเขตร้อนสูตรกัปตัน', 0);
    this.addFloatingText('เปิดหีบสมบัติภูเขาไฟสำเร็จ! (+500 G, เศษผลึกเพลิง x10, แร่ทอง x5)', this.player.x - 50, this.player.y - 25, '#facc15');
    this.updateHUD();
};

Game.generateVolcanoFloor = function(floor: number) {
    this.volcanoCurrentFloor = floor;
    const w = 34;
    const h = 26;
    const map: any[] = [];

    for (let y = 0; y < h; y++) {
        const row: any[] = [];
        for (let x = 0; x < w; x++) {
            const isBorder = (x === 0 || x === w - 1 || y === 0 || y === h - 1);
            if (isBorder) {
                row.push({ x, y, type: 'obsidianWall', solid: true });
            } else {
                row.push({ x, y, type: 'magmaFloor', solid: false });
            }
        }
        map.push(row);
    }

    this.worldMonsters = [];
    this.boss = null;
    this.bossTelegraphs = [];
    this.bossGroundHazards = [];

    if (floor === 10) {
        // Floor 10: Caldera Summit (Boss Arena)
        const centerX = 17;
        const centerY = 13;
        for (let y = 1; y < h - 1; y++) {
            for (let x = 1; x < w - 1; x++) {
                const distFromCenter = Math.hypot(x - centerX, y - centerY);
                if (distFromCenter > 11) {
                    map[y][x].type = 'magmaLava';
                    map[y][x].solid = true;
                }
            }
        }

        // Spawn Boss Karzarak
        this.boss = {
            ...BOSS_REGISTRY.boss_karzarak,
            x: 17 * 32,
            y: 9 * 32,
            hp: BOSS_REGISTRY.boss_karzarak.hp,
            maxHp: BOSS_REGISTRY.boss_karzarak.maxHp,
            alive: true,
            active: true,
            phase: 1,
            attackCooldown: 1200
        };

        const bossBar = document.getElementById('bossHealthBar');
        const bossNameEl = document.getElementById('bossName');
        if (bossBar && bossNameEl) {
            bossNameEl.textContent = this.boss.name;
            bossBar.style.display = 'block';
        }
        if (typeof SoundEngine.setBossBattle === 'function') SoundEngine.setBossBattle(true);

        // Entrance Doorway at South
        map[24][17].type = 'door';
        map[24][17].solid = false;
        map[24][17].interactable = 'exit_volcano_to_island';

    } else if (floor === 5) {
        // Floor 5: Peaceful Oasis Checkpoint
        for (let y = 12; y <= 14; y++) {
            for (let x = 16; x <= 18; x++) {
                map[y][x].type = 'volcanoSpring';
                map[y][x].solid = false;
                map[y][x].interactable = 'drink_volcano_spring';
            }
        }

        map[8][17].type = 'dungeonChest';
        map[8][17].solid = true;
        map[8][17].interactable = 'volcano_chest_5';

        map[22][8].type = 'ladder_up';
        map[22][8].solid = false;
        map[22][8].interactable = 'volcano_shortcut_exit';

        map[8][26].type = 'volcanoStairsDown';
        map[8][26].solid = false;
        map[8][26].interactable = 'volcano_stairs_down';

    } else {
        // Normal Procedural Dungeon Floors 1-4, 6-9
        for (let y = 12; y <= 14; y++) {
            for (let x = 1; x < w - 1; x++) {
                map[y][x].type = 'magmaLava';
                map[y][x].solid = true;
            }
        }

        for (let y = 12; y <= 14; y++) {
            for (let x = 16; x <= 17; x++) {
                map[y][x].isLavaBridge = true;
                if (this.volcanoSwitchActive) {
                    map[y][x].type = 'bridge';
                    map[y][x].solid = false;
                } else {
                    map[y][x].type = 'magmaLava';
                    map[y][x].solid = true;
                }
            }
        }

        map[8][8].type = 'volcanoSwitch';
        map[8][8].solid = true;
        map[8][8].interactable = 'volcano_switch';

        map[6][26].type = 'volcanoStairsDown';
        map[6][26].solid = false;
        map[6][26].interactable = 'volcano_stairs_down';

        if (floor === 1) {
            map[24][17].type = 'door';
            map[24][17].solid = false;
            map[24][17].interactable = 'exit_volcano_to_island';
        }

        const nodePositions = [
            { x: 5, y: 6 }, { x: 11, y: 19 }, { x: 22, y: 6 }, { x: 26, y: 20 }, { x: 14, y: 7 }
        ];
        nodePositions.forEach(p => {
            if (map[p.y] && map[p.y][p.x] && !map[p.y][p.x].solid) {
                map[p.y][p.x].type = 'cinderShardNode';
                map[p.y][p.x].solid = true;
                map[p.y][p.x].interactable = 'mine_cinder_shard';
            }
        });

        const urnPositions = [
            { x: 9, y: 18 }, { x: 24, y: 18 }, { x: 20, y: 7 }, { x: 7, y: 10 }
        ];
        urnPositions.forEach(p => {
            if (map[p.y] && map[p.y][p.x] && !map[p.y][p.x].solid) {
                map[p.y][p.x].type = 'volcano_urn';
                map[p.y][p.x].solid = true;
                map[p.y][p.x].interactable = 'volcano_urn';
            }
        });

        const monsterCount = 3 + Math.min(5, Math.floor(floor * 0.6));
        for (let i = 0; i < monsterCount; i++) {
            const mType = (floor <= 3) ? (i % 2 === 0 ? 'magma_sprite' : 'magma_duggy') :
                          (i % 3 === 0 ? 'lava_lurker' : (i % 2 === 0 ? 'magma_duggy' : 'magma_sprite'));
            const cfg = WORLD_MONSTERS[mType] || WORLD_MONSTERS.magma_sprite;
            const spawnNorth = (i % 2 === 0);
            const mx = (Math.floor(Math.random() * 20) + 7) * 32;
            const my = (spawnNorth ? (Math.floor(Math.random() * 6) + 4) : (Math.floor(Math.random() * 6) + 16)) * 32;

            this.worldMonsters.push({
                id: `volc_${floor}_${i}`,
                type: mType,
                name: cfg.name,
                x: mx,
                y: my,
                hp: cfg.hp + floor * 15,
                maxHp: cfg.hp + floor * 15,
                speed: cfg.speed,
                damage: cfg.damage + Math.floor(floor * 1.5),
                attackCooldown: 0,
                aggroRange: cfg.aggroDist || 200,
                direction: 'down',
                frame: 0,
                animTimer: 0,
                alive: true,
                flashTimer: 0,
                gold: cfg.gold + floor * 5,
                xp: cfg.xp + floor * 6,
                drops: cfg.drops
            });
        }
    }

    this.scenes.island_volcano = { mapWidth: w, mapHeight: h, map: map };
    this.mapWidth = w;
    this.mapHeight = h;
    this.map = map;
    return map;
};

Game.drawVolcanoDungeonHUD = function() {
    this.ctx.save();
    const floor = this.volcanoCurrentFloor || 1;
    const text = floor === 10 ? 'ดันเจี้ยนภูเขาไฟเกาะสมบัติ: ชั้น 10 [มหายอดปล่องภูเขาไฟ - ห้องบอส]' :
                 floor === 5 ? 'ดันเจี้ยนภูเขาไฟเกาะสมบัติ: ชั้น 5 [จุดแวะพักโอเอซิส]' :
                 `ดันเจี้ยนภูเขาไฟเกาะสมบัติ: ชั้น ${floor} / 10`;
    this.ctx.font = 'bold 13px Sarabun, sans-serif';
    const textWidth = this.ctx.measureText(text).width;
    const boxW = textWidth + 30;
    const boxH = 28;
    const boxX = (this.width - boxW) / 2;
    const boxY = 12;

    this.ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    this.ctx.fillRect(boxX, boxY, boxW, boxH);
    this.ctx.strokeStyle = '#ea580c';
    this.ctx.lineWidth = 1.5;
    this.ctx.strokeRect(boxX, boxY, boxW, boxH);

    this.ctx.fillStyle = '#facc15';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(text, this.width / 2, boxY + boxH / 2);
    this.ctx.restore();
};

Game.openVolcanoForgeModal = function() {
    this.closeAllModals();
    this.activeModal = 'volcanoForgeModal';
    const modal = document.getElementById('volcanoForgeModal');
    if (!modal) return;
    this.renderVolcanoForgeModal();
    modal.style.display = 'flex';
};

Game.renderVolcanoForgeModal = function() {
    const modal = document.getElementById('volcanoForgeModal');
    const countEl = document.getElementById('volcanoForgeCinderCount');
    const container = document.getElementById('volcanoForgeRecipeList');
    if (!modal || !container || typeof VOLCANO_FORGE_RECIPES === 'undefined') return;

    const cinderCount = this.getItemCount('cinder_shard');
    if (countEl) countEl.textContent = String(cinderCount);

    let html = '';
    Object.values(VOLCANO_FORGE_RECIPES).forEach((recipe: any) => {
        let canCraft = cinderCount >= recipe.costCinderShards;
        let matReqStr = `${recipe.costCinderShards} เศษผลึกเพลิง`;

        if (recipe.materials) {
            for (const [matId, matCount] of Object.entries(recipe.materials)) {
                const has = this.getItemCount(matId);
                const matName = (WORLD_ITEMS as any)[matId]?.name || matId;
                matReqStr += ` + ${has}/${matCount} ${matName}`;
                if (has < (matCount as number)) canCraft = false;
            }
        }

        html += `
            <div class="volcano-forge-card">
                <div class="forge-card-header">
                    <strong class="forge-card-title">${recipe.name}</strong>
                    <span class="forge-card-price">${recipe.costCinderShards} Shards</span>
                </div>
                <p class="forge-card-desc">${recipe.desc}</p>
                <div class="forge-card-reqs" style="color: ${canCraft ? '#4ade80' : '#ef4444'}; font-size: 12px; margin-bottom: 6px;">
                    ต้องใช้: ${matReqStr}
                </div>
                <div class="forge-card-footer">
                    <button class="btn-primary forge-craft-btn" ${canCraft ? '' : 'disabled'} onclick="Game.craftVolcanoForgeRecipe('${recipe.id}')">
                        ${canCraft ? 'หลอมสร้าง' : 'วัตถุดิบไม่พอ'}
                    </button>
                </div>
            </div>
        `;
    });
    container.innerHTML = html;
};

Game.craftVolcanoForgeRecipe = function(recipeId: string) {
    if (typeof VOLCANO_FORGE_RECIPES === 'undefined') return;
    const recipe: any = (VOLCANO_FORGE_RECIPES as any)[recipeId];
    if (!recipe) return;

    const cinderCount = this.getItemCount('cinder_shard');
    if (cinderCount < recipe.costCinderShards) {
        SoundEngine.errorClick();
        this.addFloatingText('เศษผลึกเพลิงไม่เพียงพอ!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }

    if (recipe.materials) {
        for (const [matId, matCount] of Object.entries(recipe.materials)) {
            if (this.getItemCount(matId) < (matCount as number)) {
                SoundEngine.errorClick();
                this.addFloatingText('วัตถุดิบไม่เพียงพอ!', this.player.x, this.player.y - 15, '#ef4444');
                return;
            }
        }
    }

    if (recipe.type !== 'enchant' && this.isInventoryFull()) {
        SoundEngine.errorClick();
        this.addFloatingText('กระเป๋าเต็มแล้ว!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }

    this.removeItemFromInventory('cinder_shard', recipe.costCinderShards);
    if (recipe.materials) {
        for (const [matId, matCount] of Object.entries(recipe.materials)) {
            this.removeItemFromInventory(matId, matCount as number);
        }
    }

    if (recipe.type === 'enchant') {
        this.player.volcanoForgeEnchant = (this.player.volcanoForgeEnchant || 0) + 1;
        SoundEngine.levelUp();
        this.spawnParticles(this.player.x + 12, this.player.y + 16, '#ea580c', 25);
        this.addFloatingText('สลักรูนเถ้าภูเขาไฟสำเร็จ! เสริมพลังรบ +30 DMG, +15% Crit!', this.player.x - 40, this.player.y - 25, '#facc15');
    } else if (recipe.resultItem) {
        this.addItemToInventory(recipe.resultItem, recipe.resultCount || 1, recipe.name, 0);
        SoundEngine.craft();
        this.spawnParticles(this.player.x + 12, this.player.y + 16, '#facc15', 25);
        this.addFloatingText(`หลอมสร้าง ${recipe.name} สำเร็จ!`, this.player.x - 30, this.player.y - 25, '#4ade80');
    }

    this.renderVolcanoForgeModal();
    this.updateHUD();
};
