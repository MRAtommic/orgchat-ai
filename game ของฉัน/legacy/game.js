/* ========================================================
   🌾 ฟาร์มสุขใจ (Happy Farm 2D) - Stardew Valley Style Engine
   With Walkable House & Shop Interiors, Outfit Wardrobe,
   House Upgrades/Decorations, and NPC Shop Customers!
   ======================================================== */

// Global Game State
const Game = {
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
        hp: 100,
        maxHp: 100,
        invincibleTimer: 0,
        energy: 100,
        maxEnergy: 100,
        gold: 600,
        level: 1,
        xp: 0,
        waterCan: 10,
        waterCanMax: 10,
        selectedSlot: 0,
        inventory: [],
        quests: { q1: 'active', q2: 'not_started', q3: 'not_started' },
        questProgress: { wolvesKilled: 0, rubiesMined: 0, bossDefeated: false },
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
    chests: {},
    activeDialogue: null,
    meleeSlashAnim: null,

    // Time & Calendar
    time: {
        day: 1,
        seasonIndex: 0,
        hour: 6,
        minute: 0,
        timer: 0,
        weather: 'sun' // 'sun', 'rain'
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
    }
};

// ========================================================
// 1. INITIALIZATION & SCENE MAPS GENERATION
// ========================================================

Game.init = function() {
    this.canvas = document.getElementById('gameCanvas');
    this.ctx = this.canvas.getContext('2d');
    this.ctx.imageSmoothingEnabled = false;

    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());

    this.initInventory();
    this.generateAllScenes();
    this.spawnAnimals();
    this.setupInputListeners();

    // Multi-User Profile & Cloud/Local Save System
    if (typeof Auth !== 'undefined') {
        Auth.init();
    }

    this.updateHUD();

    // Start Game Loop
    this.lastTime = performance.now();
    requestAnimationFrame((t) => this.gameLoop(t));
};

Game.resizeCanvas = function() {
    this.canvas.width = 800;
    this.canvas.height = 576;
    this.width = this.canvas.width;
    this.height = this.canvas.height;
};

Game.initInventory = function() {
    this.player.inventory = [
        { id: 'hoe', type: 'tool', name: 'จอบ' },
        { id: 'water', type: 'tool', name: 'บัวรดน้ำ' },
        { id: 'scythe', type: 'tool', name: 'เคียว' },
        { id: 'slingshot', type: 'weapon', name: 'หนังสติ๊กล่าสัตว์' },
        { id: 'wheat_seed', type: 'seed', cropId: 'wheat', name: 'เมล็ดข้าวสาลี', count: 12 },
        { id: 'carrot_seed', type: 'seed', cropId: 'carrot', name: 'เมล็ดแครอท', count: 8 },
        { id: 'tomato_seed', type: 'seed', cropId: 'tomato', name: 'เมล็ดมะเขือเทศ', count: 6 },
        { id: 'corn_seed', type: 'seed', cropId: 'corn', name: 'เมล็ดข้าวโพด', count: 4 },
        { id: 'bread', type: 'food', name: 'ขนมปัง', count: 3, energyRestore: 40 },
        null
    ];
    // Expand inventory to 24 slots (10 hotbar + 14 backpack)
    while (this.player.inventory.length < 24) {
        this.player.inventory.push(null);
    }
};

Game.generateAllScenes = function() {
    this.scenes.farm = this.generateFarmMap();
    this.scenes.house = this.generateHouseMap();
    this.scenes.shop = this.generateShopMap();
    this.scenes.forest = this.generateForestMap();

    // Set default scene
    this.loadScene('farm');
};

Game.loadScene = function(sceneName) {
    this.currentScene = sceneName;
    const scene = this.scenes[sceneName];
    this.map = scene.map;
    this.mapWidth = scene.mapWidth;
    this.mapHeight = scene.mapHeight;
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

    // North Forest Gate (Exit from Farm to Open World)
    for (let x = 15; x <= 17; x++) {
        map[0][x].solid = false;
        map[0][x].type = 'path';
        map[0][x].interactable = 'exit_to_forest';
    }
    for (let y = 1; y <= 7; y++) {
        map[y][16].type = 'path';
    }

    // Paths
    for (let x = 3; x <= 16; x++) map[8][x].type = 'path';
    for (let y = 5; y <= 18; y++) map[y][7].type = 'path';
    for (let x = 7; x <= 30; x++) map[15][x].type = 'path';
    for (let y = 5; y <= 21; y++) map[y][20].type = 'path';

    // Farmhouse (x: 4..6, y: 3..5)
    for (let y = 3; y <= 5; y++) {
        for (let x = 4; x <= 6; x++) {
            map[y][x].solid = true;
            map[y][x].type = 'building';
        }
    }
    // Walk into house at door
    map[5][5].solid = false;
    map[5][5].interactable = 'house_door';

    // Shipping Bin, Well & Hunter Post
    map[5][8].solid = true; map[5][8].type = 'shippingBin'; map[5][8].interactable = 'shippingBin';
    map[7][9].solid = true; map[7][9].type = 'well'; map[7][9].interactable = 'well';
    map[5][12].solid = true; map[5][12].type = 'hunterPost'; map[5][12].interactable = 'hunter_post';

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
    // Walk into Shop at door
    map[19][28].solid = false;
    map[19][28].interactable = 'shop_door';

    // Pond
    for (let y = 18; y <= 22; y++) {
        for (let x = 2; x <= 6; x++) { map[y][x].solid = true; map[y][x].type = 'water'; }
    }

    // Trees
    [{x: 10, y: 3}, {x: 14, y: 3}, {x: 18, y: 3}, {x: 17, y: 11}, {x: 24, y: 21}, {x: 12, y: 20}].forEach(p => {
        map[p.y][p.x].solid = true; map[p.y][p.x].type = 'tree';
    });

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

    // South Exit Gate back to Farm (at x: 23..25, y: 39)
    for (let x = 23; x <= 25; x++) {
        map[37][x].type = 'path';
        map[38][x].type = 'path';
        map[39][x].solid = false;
        map[39][x].type = 'path';
        map[39][x].interactable = 'exit_to_farm';
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

// 1.2 House Interior Map (ภายในบ้าน)
Game.generateHouseMap = function() {
    const width = 25;
    const height = 18;
    const map = [];

    for (let y = 0; y < height; y++) {
        const row = [];
        for (let x = 0; x < width; x++) {
            let isWall = (y <= 2 || x <= 1 || x >= width - 2 || y >= height - 2);
            let isDoor = (x === 12 && y >= height - 2);
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
            let isDoor = (x === 12 && y >= height - 2);
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
// 2. SCENE TRANSITION SYSTEM
// ========================================================

Game.switchScene = function(targetScene, targetTileX, targetTileY) {
    this.loadScene(targetScene);
    this.player.x = targetTileX * this.tileSize;
    this.player.y = targetTileY * this.tileSize;
    // Snap camera immediately on scene transition
    const maxX = Math.max(0, this.mapWidth * this.tileSize - this.width);
    const maxY = Math.max(0, this.mapHeight * this.tileSize - this.height);
    this.camera.x = Math.max(0, Math.min(this.player.x - this.width / 2 + 12, maxX));
    this.camera.y = Math.max(0, Math.min(this.player.y - this.height / 2 + 16, maxY));

    if (targetScene === 'house') {
        SoundEngine.door();
        this.addFloatingText('🏠 เข้าสู่บ้านพักชาวสวน', this.player.x, this.player.y - 15, '#fde047');
    } else if (targetScene === 'shop') {
        SoundEngine.bell();
        this.addFloatingText('🏪 เข้าสู่ร้านค้าเกษตรชุมชน', this.player.x, this.player.y - 15, '#38bdf8');
    } else if (targetScene === 'forest') {
        SoundEngine.door();
        this.addFloatingText('🌲 ผืนป่าเอลเดอร์วู้ด & วิหารจอมอสูร', this.player.x, this.player.y - 15, '#a855f7');
        this.initForestScene();
    } else {
        SoundEngine.door();
        this.addFloatingText('🌾 กลับสู่ฟาร์มสุขใจ', this.player.x, this.player.y - 15, '#86efac');
    }

    this.updateHUD();
};

// ========================================================
// 3. INPUT HANDLING
// ========================================================

Game.setupInputListeners = function() {
    window.addEventListener('keydown', (e) => {
        // Layout-Independent Movement (supports Thai/US keyboards)
        if (e.code === 'KeyW' || e.code === 'ArrowUp') this.keys.up = true;
        if (e.code === 'KeyS' || e.code === 'ArrowDown') this.keys.down = true;
        if (e.code === 'KeyA' || e.code === 'ArrowLeft') this.keys.left = true;
        if (e.code === 'KeyD' || e.code === 'ArrowRight') this.keys.right = true;

        // Number Keys (Hotbar)
        if (e.code.startsWith('Digit')) {
            const digit = parseInt(e.code.replace('Digit', ''));
            if (digit >= 1 && digit <= 9) this.selectHotbarSlot(digit - 1);
            else if (digit === 0) this.selectHotbarSlot(9);
        } else if (e.key >= '1' && e.key <= '9') {
            this.selectHotbarSlot(parseInt(e.key) - 1);
        } else if (e.key === '0') {
            this.selectHotbarSlot(9);
        }

        // Action Keys (Layout-Independent)
        if (e.code === 'Space') {
            e.preventDefault();
            const selItem = this.player.inventory[this.player.selectedSlot];
            if (selItem && (selItem.type === 'weapon' || WEAPONS[selItem.id])) {
                const originX = this.player.x + 12;
                const originY = this.player.y + 14;
                let tx = originX;
                let ty = originY;
                if (this.player.direction === 'up') ty -= 200;
                else if (this.player.direction === 'down') ty += 200;
                else if (this.player.direction === 'left') tx -= 200;
                else if (this.player.direction === 'right') tx += 200;
                this.playerAttackAt(tx, ty);
            } else {
                this.useCurrentTool();
            }
        } else if (e.code === 'KeyE') {
            this.interact();
        } else if (e.code === 'KeyQ') {
            this.toggleModal('questModal');
        } else if (e.code === 'KeyI') {
            this.toggleModal('inventory');
        } else if (e.code === 'KeyC') {
            this.toggleModal('crafting');
        } else if (e.code === 'KeyM') {
            this.toggleModal('shop');
        } else if (e.code === 'KeyH') {
            this.toggleModal('hunterModal');
        } else if (e.code === 'Slash' || e.key === '?' || e.code === 'F1') {
            this.toggleModal('controlsModal');
        } else if (e.code === 'Escape' || e.key === 'Escape') {
            this.closeAllModals();
        }

    });

    window.addEventListener('keyup', (e) => {
        if (e.code === 'KeyW' || e.code === 'ArrowUp') this.keys.up = false;
        if (e.code === 'KeyS' || e.code === 'ArrowDown') this.keys.down = false;
        if (e.code === 'KeyA' || e.code === 'ArrowLeft') this.keys.left = false;
        if (e.code === 'KeyD' || e.code === 'ArrowRight') this.keys.right = false;
    });

    this.canvas.addEventListener('click', (e) => {
        if (this.activeModal) return;

        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        const worldX = (e.clientX - rect.left) * scaleX + this.camera.x;
        const worldY = (e.clientY - rect.top) * scaleY + this.camera.y;

        const tileX = Math.floor(worldX / this.tileSize);
        const tileY = Math.floor(worldY / this.tileSize);

        if (this.currentScene === 'farm' || this.currentScene === 'forest') {
            const selItem = this.player.inventory[this.player.selectedSlot];
            const isWeapon = (selItem && (selItem.type === 'weapon' || WEAPONS[selItem.id]));

            if (isWeapon) {
                this.playerAttackAt(worldX, worldY);
                return;
            }

            if (this.currentScene === 'farm') {
                const clickedBug = this.demonBugs.find(b => Math.hypot((b.x + 14) - worldX, (b.y + 14) - worldY) < 28);
                if (clickedBug) {
                    this.playerAttackAt(worldX, worldY);
                    return;
                }

                const clickedAnimal = this.animals.find(a => {
                    return worldX >= a.x && worldX <= a.x + a.width && worldY >= a.y && worldY <= a.y + a.height;
                });
                if (clickedAnimal) {
                    this.petAnimal(clickedAnimal);
                    return;
                }
            } else if (this.currentScene === 'forest') {
                const clickedMonster = this.worldMonsters.find(m => Math.hypot((m.x + 14) - worldX, (m.y + 14) - worldY) < 28);
                const clickedBoss = (this.boss && this.boss.alive && Math.hypot((this.boss.x + 32) - worldX, (this.boss.y + 32) - worldY) < 48);
                if (clickedMonster || clickedBoss) {
                    this.playerAttackAt(worldX, worldY);
                    return;
                }
            }
        }

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
        if ((this.currentScene === 'farm' || this.currentScene === 'forest') && selItem && (selItem.type === 'weapon' || WEAPONS[selItem.id])) {
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
    if (this.canvas && (this.currentScene === 'farm' || this.currentScene === 'forest') && selItem && (selItem.type === 'weapon' || WEAPONS[selItem.id])) {
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
    if (this.activeModal || this.activeDialogue) {
        this.player.isMoving = false;
        return;
    }

    if (this.player.invincibleTimer > 0) {
        this.player.invincibleTimer -= dt;
    }

    if (this.playerShootCooldown > 0) {
        this.playerShootCooldown -= dt;
    }

    let dx = 0;
    let dy = 0;

    if (this.keys.up) { dy -= 1; this.player.direction = 'up'; }
    if (this.keys.down) { dy += 1; this.player.direction = 'down'; }
    if (this.keys.left) { dx -= 1; this.player.direction = 'left'; }
    if (this.keys.right) { dx += 1; this.player.direction = 'right'; }

    if (dx !== 0 && dy !== 0) { dx *= 0.7071; dy *= 0.7071; }

    this.player.isMoving = (dx !== 0 || dy !== 0);

    // Apply speed bonus if persian rug owned and inside house
    let curSpeed = this.player.speed;
    if (this.currentScene === 'house' && this.player.houseUpgrades.persian_rug) {
        curSpeed *= 1.3;
    }

    if (this.player.isMoving) {
        const nextX = this.player.x + dx * curSpeed;
        const nextY = this.player.y + dy * curSpeed;

        if (!this.checkTileCollision(nextX, this.player.y)) {
            this.player.x = nextX;
        } else if (dy === 0) {
            // Horizontal movement blocked: assist corner sliding
            if (!this.checkTileCollision(nextX, this.player.y - 6)) this.player.y -= 1.8;
            else if (!this.checkTileCollision(nextX, this.player.y + 6)) this.player.y += 1.8;
        }

        if (!this.checkTileCollision(this.player.x, nextY)) {
            this.player.y = nextY;
        } else if (dx === 0) {
            // Vertical movement blocked: assist corner sliding
            if (!this.checkTileCollision(this.player.x - 6, nextY)) this.player.x -= 1.8;
            else if (!this.checkTileCollision(this.player.x + 6, nextY)) this.player.x += 1.8;
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

        if (curTile && curTile.interactable) {
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
            } else if (curTile.interactable === 'exit_to_forest') {
                this.switchScene('forest', 24, 38);
                return;
            } else if (curTile.interactable === 'exit_to_farm') {
                this.switchScene('farm', 16, 2);
                return;
            }
        }
    } else {
        this.player.frame = 0;
        this.player.animTimer = 0;
    }

    // Camera follow (smooth lerp follow, clamped to scene map bounds)
    const maxX = Math.max(0, this.mapWidth * this.tileSize - this.width);
    const maxY = Math.max(0, this.mapHeight * this.tileSize - this.height);
    const targetCamX = Math.max(0, Math.min(this.player.x - this.width / 2 + 12, maxX));
    const targetCamY = Math.max(0, Math.min(this.player.y - this.height / 2 + 16, maxY));
    if (this.camera.x === undefined || isNaN(this.camera.x)) this.camera.x = targetCamX;
    if (this.camera.y === undefined || isNaN(this.camera.y)) this.camera.y = targetCamY;
    this.camera.x += (targetCamX - this.camera.x) * 0.14;
    this.camera.y += (targetCamY - this.camera.y) * 0.14;
};

Game.checkTileCollision = function(x, y) {
    const hitbox = {
        left: x + 4, right: x + 20,
        top: y + 16, bottom: y + 30
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
    this.addFloatingText('❤️ ' + animal.name + ' อารมณ์ดีมาก!', animal.x + 8, animal.y - 12, '#ec4899');
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
            this.addFloatingText('🧺 +1 ' + animData.productName + ' (+' + animData.xp + ' XP)', animal.x, animal.y - 28, '#4ade80');
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
                this.addFloatingText('🛒 ' + npc.name + ' กำลังเลือกดูสินค้า...', npc.x, npc.y - 12, '#fef08a');
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
                this.addFloatingText('💰 +' + npc.earnedGold + ' G (Ka-ching!) ' + npc.name + ' อุดหนุนแล้ว!', npc.x, npc.y - 22, '#facc15');
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

Game.actOnTile = function(tx, ty) {
    if (tx < 0 || tx >= this.mapWidth || ty < 0 || ty >= this.mapHeight) return;

    const playerTileX = Math.floor((this.player.x + 10) / this.tileSize);
    const playerTileY = Math.floor((this.player.y + 20) / this.tileSize);
    const dist = Math.hypot(playerTileX - tx, playerTileY - ty);

    if (dist > 2.5) {
        this.addFloatingText('ไกลเกินไป', tx * 32, ty * 32, '#cbd5e1');
        return;
    }

    const tile = this.map[ty][tx];

    // Check interaction triggers on click
    if (tile.interactable) {
        this.handleTileInteract(tile.interactable);
        return;
    }

    // Check ripe crop harvest
    if (tile.crop && tile.crop.ready) {
        this.harvestCrop(tx, ty);
        return;
    }

    const selectedItem = this.player.inventory[this.player.selectedSlot];

    // Check energy
    if (this.player.energy <= 0) {
        this.addFloatingText('หมดแรงแล้ว! กินอาหารหรือเข้านอน', this.player.x, this.player.y - 10, '#f87171');
        return;
    }

    if (!selectedItem) {
        this.addFloatingText('เลือกเครื่องมือจากแถบลัด', this.player.x, this.player.y - 10, '#fde047');
        return;
    }

    // Hoe
    if (selectedItem.id === 'hoe' && this.currentScene === 'farm') {
        if ((tile.type === 'soil' || tile.type === 'grass') && !tile.tilled && !tile.solid) {
            tile.type = 'soil';
            tile.tilled = true;
            let cost = this.player.houseUpgrades.fireplace ? 1 : 2;
            this.player.energy -= cost;
            SoundEngine.till();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#9b643a', 8);
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#713f12', 6);
            this.addFloatingText('-' + cost + ' พลังงาน', tx * 32, ty * 32 - 12, '#93c5fd');
            this.updateHUD();
        }
    }
    // Water
    else if (selectedItem.id === 'water' && this.currentScene === 'farm') {
        if (tile.type === 'well' || tile.type === 'water') {
            this.player.waterCan = this.player.waterCanMax;
            SoundEngine.water();
            this.addFloatingText('💧 เติมน้ำเต็มบัวแล้ว!', tx * 32, ty * 32 - 10, '#38bdf8');
            this.updateHUD();
            return;
        }

        if (tile.tilled && !tile.watered) {
            if (this.player.waterCan <= 0) {
                this.addFloatingText('น้ำในบัวหมด! ไปเติมน้ำที่บ่อน้ำ', tx * 32, ty * 32 - 10, '#38bdf8');
                return;
            }
            tile.watered = true;
            this.player.waterCan -= 1;
            this.player.energy -= (this.player.houseUpgrades.fireplace ? 0 : 1);
            SoundEngine.water();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#38bdf8', 10);
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#60a5fa', 8);
            this.updateHUD();
        }
    }
    // Seeds
    else if (selectedItem.type === 'seed' && this.currentScene === 'farm') {
        if (tile.tilled && !tile.crop) {
            tile.crop = { cropId: selectedItem.cropId, stage: 0, daysGrown: 0, ready: false };
            selectedItem.count -= 1;
            if (selectedItem.count <= 0) this.player.inventory[this.player.selectedSlot] = null;
            SoundEngine.plant();
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#84cc16', 8);
            this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#facc15', 5);
            this.addFloatingText('🌱 ปลูก ' + selectedItem.name, tx * 32, ty * 32 - 12, '#a3e635');
            this.updateHUD();
        }
    }
    // Food
    else if (selectedItem.type === 'food') {
        let restore = selectedItem.energyRestore || 30;
        if (this.player.houseUpgrades.refrigerator) restore = Math.round(restore * 1.5);

        this.player.energy = Math.min(this.player.maxEnergy, this.player.energy + restore);
        selectedItem.count -= 1;
        if (selectedItem.count <= 0) this.player.inventory[this.player.selectedSlot] = null;
        SoundEngine.craft();
        this.addFloatingText('+' + restore + ' พลังงาน อร่อยมาก!', this.player.x, this.player.y - 15, '#4ade80');
        this.updateHUD();
    }
};

Game.harvestCrop = function(tx, ty) {
    const tile = this.map[ty][tx];
    if (!tile.crop || !tile.crop.ready) return;

    const cropData = CROPS[tile.crop.cropId];
    if (!cropData) return;

    const yieldAmount = Math.floor(Math.random() * 2) + 1;
    this.addItemToInventory(tile.crop.cropId, yieldAmount, cropData.name);

    let xpGained = cropData.xp * yieldAmount;
    if (this.player.houseUpgrades.persian_rug) xpGained = Math.round(xpGained * 1.15);

    this.addXp(xpGained);
    this.stats.harvests++;

    SoundEngine.harvest();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#facc15', 16);
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#4ade80', 10);
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#ffffff', 6);
    this.addFloatingText('✨ +' + yieldAmount + ' ' + cropData.name + ' (+' + xpGained + ' XP)', tx * 32, ty * 32 - 18, '#fde047');

    tile.crop = null;
    tile.watered = false;
    this.updateHUD();
};

Game.interact = function() {
    if (this.currentScene === 'farm') {
        const nearbyAnimal = this.animals.find(a => Math.hypot(this.player.x - a.x, this.player.y - a.y) < 50);
        if (nearbyAnimal) {
            this.petAnimal(nearbyAnimal);
            return;
        }
    }

    const target = this.getTargetTile();
    const currTileX = Math.floor((this.player.x + 10) / this.tileSize);
    const currTileY = Math.floor((this.player.y + 20) / this.tileSize);

    // 1. Check target tile
    const targetTile = this.map[target.y]?.[target.x];
    if (targetTile && targetTile.interactable) {
        this.handleTileInteract(targetTile.interactable);
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
        this.handleTileInteract(tile.interactable);
        return;
    }

    // 3. Check 2-tile radius for interactive furniture
    for (let dy = -2; dy <= 2; dy++) {
        for (let dx = -2; dx <= 2; dx++) {
            const t = this.map[currTileY + dy]?.[currTileX + dx];
            if (t && t.interactable && !t.interactable.startsWith('exit_') && !t.interactable.endsWith('_door')) {
                this.handleTileInteract(t.interactable);
                return;
            }
        }
    }
};

Game.handleTileInteract = function(type) {
    if (type === 'house_door') {
        this.switchScene('house', 12, 15);
    } else if (type === 'shop_door') {
        this.switchScene('shop', 12, 15);
    } else if (type === 'exit_house') {
        this.switchScene('farm', 5, 6);
    } else if (type === 'exit_shop') {
        this.switchScene('farm', 28, 20);
    } else if (type === 'exit_to_forest') {
        this.switchScene('forest', 24, 38);
    } else if (type === 'exit_to_farm') {
        this.switchScene('farm', 16, 2);
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
        SoundEngine.water();
        this.addFloatingText('💧 เติมน้ำเต็มบัวแล้ว!', this.player.x, this.player.y - 15, '#38bdf8');
        this.updateHUD();
    } else if (type === 'hunter_post') {
        this.openModal('hunterModal');
    } else if (type === 'npc_valeria') {
        this.startDialogue('valeria');
    } else if (type === 'npc_eldrin') {
        this.startDialogue('eldrin');
    } else if (type === 'npc_kael') {
        this.startDialogue('kael');
    } else if (type === 'campfire') {
        this.player.hp = Math.min(this.player.maxHp, this.player.hp + 30);
        this.player.energy = Math.min(this.player.maxEnergy, this.player.energy + 30);
        SoundEngine.craft();
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#f97316', 8);
        this.addFloatingText('🔥 นั่งพักผ่อนข้างกองไฟ ฟื้นฟู HP +30 และพลังงาน +30!', this.player.x - 20, this.player.y - 15, '#fde047');
        this.updateHUD();
    } else if (type === 'ruby_node') {
        SoundEngine.miningHit();
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#ef4444', 12);
        this.addItemToInventory('ruby_gem', 1, 'อัญมณีทับทิมเวทมนตร์');
        this.addItemToInventory('iron_ore', 1, 'แร่เหล็กดิบ');
        this.addXp(20);
        this.player.questProgress.rubiesMined = (this.player.questProgress.rubiesMined || 0) + 1;
        this.addFloatingText('⛏️ ได้รับ อัญมณีทับทิมเวทมนตร์ + แร่เหล็ก (+20 XP)', this.player.x - 20, this.player.y - 15, '#f87171');
        // Check quest 2 objective
        if (this.player.quests.q2 === 'active' && this.player.questProgress.rubiesMined >= 2 && this.player.questProgress.wolvesKilled >= 3) {
            this.addFloatingText('⭐ ภารกิจที่ 2 สำเร็จ! นำของไปส่งที่ช่างตีเหล็ก คาเอล', this.player.x - 30, this.player.y - 30, '#4ade80');
        }
        this.updateHUD();
    } else if (type === 'starflower_node') {
        SoundEngine.harvest();
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#38bdf8', 8);
        this.addItemToInventory('starflower_herb', 1, 'สมุนไพรดวงดาว');
        this.addXp(10);
        this.addFloatingText('🌸 เก็บ สมุนไพรดวงดาว (+10 XP)', this.player.x - 10, this.player.y - 15, '#38bdf8');
        this.updateHUD();
    } else if (type.startsWith('chest_')) {
        if (this.chests[type]) {
            this.addFloatingText('หีบนี้ถูกเปิดไปแล้ว', this.player.x, this.player.y - 10, '#94a3b8');
            return;
        }
        this.chests[type] = true;
        SoundEngine.chestOpen();
        this.spawnParticles(this.player.x + 10, this.player.y + 10, '#facc15', 20);
        const goldBonus = 250;
        this.player.gold += goldBonus;
        this.addItemToInventory('health_potion', 2, 'ยาฟื้นพลังชีวิตชั้นเลิศ');
        this.addItemToInventory('iron_ore', 3, 'แร่เหล็กดิบ');
        this.addXp(50);
        this.addFloatingText('✨ เปิดหีบโบราณ! +' + goldBonus + ' G และยาฟื้นพลัง (+50 XP)', this.player.x - 30, this.player.y - 20, '#fde047');
        this.updateHUD();
    }
};

// ========================================================
// 7. TIME, CALENDAR & SLEEP
// ========================================================

Game.updateTime = function(dt) {
    if (this.activeModal) return;

    this.time.timer += dt;
    if (this.time.timer >= 1000) {
        this.time.timer = 0;
        this.time.minute += 10;

        // Passive tea table regen in house
        if (this.currentScene === 'house' && this.player.houseUpgrades.tea_table) {
            this.player.energy = Math.min(this.player.maxEnergy, this.player.energy + 1);
            this.updateHUD();
        }

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
            this.updateClockHUD();

            if (this.time.hour >= 24) {
                this.addFloatingText('คุณง่วงจนสลบไป...', this.player.x, this.player.y - 10, '#f87171');
                this.sleepAndPassDay();
            }
        }
    }
};

Game.sleepAndPassDay = function() {
    this.closeAllModals();

    this.time.day += 1;
    this.time.hour = 6;
    this.time.minute = 0;

    if (this.time.day > DAYS_PER_SEASON) {
        this.time.day = 1;
        this.time.seasonIndex = (this.time.seasonIndex + 1) % SEASONS.length;
    }

    this.time.weather = Math.random() < 0.3 ? 'rain' : 'sun';

    // Energy recovery (Deluxe bed bonus!)
    const maxBonus = this.player.houseUpgrades.bed_deluxe ? 130 : 100;
    this.player.maxEnergy = maxBonus;
    this.player.energy = this.player.maxEnergy;
    this.player.waterCan = this.player.waterCanMax;

    // Wake up in bed inside house
    this.switchScene('house', 19, 5);

    // Overnight crop growth on farm
    const farmMap = this.scenes.farm.map;
    for (let y = 0; y < this.scenes.farm.mapHeight; y++) {
        for (let x = 0; x < this.scenes.farm.mapWidth; x++) {
            const tile = farmMap[y][x];
            if (this.time.weather === 'rain' && tile.tilled) tile.watered = true;

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
                tile.watered = (this.time.weather === 'rain');
            } else if (tile.tilled && this.time.weather !== 'rain') {
                tile.watered = false;
            }
        }
    }

    this.animals.forEach(a => { a.pettedToday = false; a.hasProduct = true; });

    SoundEngine.levelUp();
    this.addFloatingText('เช้าวันใหม่! พลังงานเต็ม 100% (' + this.player.maxEnergy + ')', this.player.x, this.player.y - 20, '#fde047');
    this.updateHUD();
};

// ========================================================
// 8. ECONOMY, INVENTORY & XP
// ========================================================

Game.addItemToInventory = function(id, count = 1, name = '') {
    for (let slot of this.player.inventory) {
        if (slot && slot.id === id && slot.count !== undefined) {
            slot.count += count;
            this.updateHUD();
            return true;
        }
    }
    const isWep = (id === 'slingshot' || id === 'rifle' || WEAPONS[id]);
    for (let i = 0; i < this.player.inventory.length; i++) {
        if (!this.player.inventory[i]) {
            this.player.inventory[i] = {
                id: id,
                name: name || WEAPONS[id]?.name || CROPS[id]?.name || id,
                count: isWep ? undefined : count,
                type: isWep ? 'weapon' : 'item'
            };
            this.updateHUD();
            return true;
        }
    }
    this.addFloatingText('กระเป๋าเต็ม!', this.player.x, this.player.y - 15, '#f87171');
    return false;
};

Game.removeItemFromInventory = function(id, count = 1) {
    for (let i = 0; i < this.player.inventory.length; i++) {
        const slot = this.player.inventory[i];
        if (slot && slot.id === id) {
            if (slot.count !== undefined) {
                if (slot.count >= count) {
                    slot.count -= count;
                    if (slot.count <= 0) this.player.inventory[i] = null;
                    this.updateHUD();
                    return true;
                }
            } else {
                this.player.inventory[i] = null;
                this.updateHUD();
                return true;
            }
        }
    }
    return false;
};

Game.countItemInInventory = function(id) {
    let total = 0;
    for (let slot of this.player.inventory) {
        if (slot && slot.id === id) total += (slot.count !== undefined ? slot.count : 1);
    }
    return total;
};

Game.addXp = function(amount) {
    this.player.xp += amount;
    const nextLvlXp = LEVEL_XP[this.player.level + 1] || 99999;
    if (this.player.xp >= nextLvlXp) {
        this.player.level += 1;
        SoundEngine.levelUp();
        this.addFloatingText('★ LEVEL UP! เลเวล ' + this.player.level + ' ★', this.player.x, this.player.y - 30, '#facc15');
    }
    this.updateHUD();
};

Game.sellItem = function(index) {
    const item = this.player.inventory[index];
    if (!item) return;

    let price = 10;
    if (CROPS[item.id]) price = CROPS[item.id].sellPrice;
    else if (RECIPES[item.id]) price = RECIPES[item.id].sellPrice;
    else if (item.id === 'milk') price = 50;
    else if (item.id === 'egg') price = 25;
    else if (item.id === 'wool') price = 75;
    else if (item.id === 'truffle') price = 120;
    else if (item.id === 'bacon') price = 90;

    const count = item.count || 1;
    const totalEarnings = price * count;

    this.player.gold += totalEarnings;
    this.player.inventory[index] = null;
    this.stats.sales += count;

    SoundEngine.coin();
    this.addFloatingText('+' + totalEarnings + ' G', this.player.x, this.player.y - 15, '#fde047');
    this.updateHUD();
    this.renderSellModal();
};

// ========================================================
// 9. RENDERING ENGINE
// ========================================================

Game.render = function() {
    this.ctx.fillStyle = '#1c1917';
    this.ctx.fillRect(0, 0, this.width, this.height);

    // 1. Draw Map Tiles
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
            else if (tile.type === 'water') this.ctx.drawImage(SPRITES.water, screenX, screenY);
            else if (tile.type === 'soil' || tile.tilled) {
                this.ctx.drawImage(tile.watered ? SPRITES.soilWet : SPRITES.soilDry, screenX, screenY);
            } else if (tile.type === 'fence') this.ctx.drawImage(SPRITES.fence, screenX, screenY);
            else if (tile.type === 'floorWood') this.ctx.drawImage(SPRITES.floorWood, screenX, screenY);
            else if (tile.type === 'wallHouse') this.ctx.drawImage(SPRITES.wallHouse, screenX, screenY);
            else if (tile.type === 'floorShop') this.ctx.drawImage(SPRITES.floorShop, screenX, screenY);
            else if (tile.type === 'wallShop') this.ctx.drawImage(SPRITES.wallShop, screenX, screenY);
            else if (tile.type === 'doorMat') this.ctx.drawImage(SPRITES.doorMat, screenX, screenY);
            else if (tile.type === 'darkGrass') this.ctx.drawImage(SPRITES.darkGrass, screenX, screenY);
            else if (tile.type === 'darkStone') this.ctx.drawImage(SPRITES.darkStone, screenX, screenY);
            else if (tile.type === 'runeTile') this.ctx.drawImage(SPRITES.runeTile, screenX, screenY);
            else if (tile.type === 'bridge') this.ctx.drawImage(SPRITES.bridge, screenX, screenY);
            else if (tile.type === 'rubyNode') {
                this.ctx.drawImage(SPRITES.darkGrass, screenX, screenY);
                this.ctx.drawImage(SPRITES.rubyNode, screenX, screenY);
            } else if (tile.type === 'starflower') {
                this.ctx.drawImage(SPRITES.darkGrass, screenX, screenY);
                this.ctx.drawImage(SPRITES.starflower, screenX, screenY);
            } else if (tile.type === 'campfire') {
                this.ctx.drawImage(SPRITES.path, screenX, screenY);
                this.ctx.drawImage(SPRITES.campfire, screenX, screenY);
            } else if (tile.type === 'pillar') {
                this.ctx.drawImage(SPRITES.runeTile, screenX, screenY);
                this.ctx.drawImage(SPRITES.pillar, screenX, screenY - 16);
            } else if (tile.type === 'chestClosed') {
                this.ctx.drawImage(SPRITES.darkStone, screenX, screenY);
                this.ctx.drawImage(this.chests[tile.interactable] ? SPRITES.chestOpened : SPRITES.chestClosed, screenX, screenY);
            } else if (tile.type === 'tree') {
                this.ctx.drawImage(this.currentScene === 'forest' ? SPRITES.darkGrass : SPRITES.grass, screenX, screenY);
                this.ctx.drawImage(SPRITES.tree, screenX - 8, screenY - 30);
            } else if (this.currentScene === 'forest') {
                this.ctx.drawImage(SPRITES.darkGrass, screenX, screenY);
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

    // 2. Draw Scene-Specific Buildings / Furniture
    if (this.currentScene === 'farm') {
        this.drawFarmBuildings();
        this.drawAnimals();
        this.drawHiredGardeners();
        this.drawHiredHunters();
        this.drawDemonBugs();
    } else if (this.currentScene === 'house') {
        this.drawHouseInterior();
    } else if (this.currentScene === 'shop') {
        this.drawShopInterior();
    } else if (this.currentScene === 'forest') {
        this.drawForestEntities();
    }

    // 3. Tile Cursor
    this.drawTileCursor();

    // 4. Player
    this.drawPlayer();

    // 4.1 Projectiles
    if (this.currentScene === 'farm' || this.currentScene === 'forest') {
        this.drawProjectiles();
    }
    this.drawMeleeSlash();

    // 5. Weather & Lighting (outside only)
    if (this.currentScene === 'farm' || this.currentScene === 'forest') {
        if (this.time.weather === 'rain') this.drawRain();
        this.drawDayNightLighting();
        if (this.currentScene === 'farm' && this.waveAlertTimer > 0) this.drawWaveAlertBanner();
    }

    // 6. Particles & Floating Texts
    this.drawParticles();
    this.drawFloatingTexts();
};

Game.drawFarmBuildings = function() {
    this.ctx.drawImage(SPRITES.house, Math.round(4 * this.tileSize - this.camera.x), Math.round(2 * this.tileSize + 6 - this.camera.y));
    this.ctx.drawImage(SPRITES.barn, Math.round(23 * this.tileSize - this.camera.x), Math.round(2 * this.tileSize + 6 - this.camera.y));
    this.ctx.drawImage(SPRITES.shippingBin, Math.round(8 * this.tileSize - this.camera.x), Math.round(4 * this.tileSize + 16 - this.camera.y));
    this.ctx.drawImage(SPRITES.well, Math.round(9 * this.tileSize - this.camera.x), Math.round(6 * this.tileSize + 16 - this.camera.y));
    this.ctx.drawImage(SPRITES.hunterPost, Math.round(11 * this.tileSize - this.camera.x), Math.round(4 * this.tileSize + 8 - this.camera.y));
    this.ctx.drawImage(SPRITES.mill, Math.round(18 * this.tileSize - this.camera.x), Math.round(16 * this.tileSize + 6 - this.camera.y));
    this.ctx.drawImage(SPRITES.shop, Math.round(27 * this.tileSize - this.camera.x), Math.round(16 * this.tileSize + 6 - this.camera.y));

    for (let y = 0; y < this.mapHeight; y++) {
        for (let x = 0; x < this.mapWidth; x++) {
            if (this.map[y][x].type === 'tree') {
                this.ctx.drawImage(SPRITES.tree, Math.round(x * this.tileSize - 8 - this.camera.x), Math.round(y * this.tileSize - 30 - this.camera.y));
            }
        }
    }
};

Game.drawHouseInterior = function() {
    // Bed at (19, 3)
    const bedSprite = this.player.houseUpgrades.bed_deluxe ? SPRITES.bedDeluxe : SPRITES.bedStandard;
    this.ctx.drawImage(bedSprite, Math.round(19 * 32 - this.camera.x), Math.round(3 * 32 - this.camera.y));

    // Wardrobe at (3, 3)
    this.ctx.drawImage(SPRITES.wardrobe, Math.round(3 * 32 - this.camera.x), Math.round(3 * 32 - 16 - this.camera.y));

    // Blueprint Workbench at (8, 3)
    this.ctx.fillStyle = '#78350f';
    this.ctx.fillRect(Math.round(8 * 32 - this.camera.x), Math.round(3 * 32 - this.camera.y), 44, 28);
    this.ctx.fillStyle = '#fef08a';
    this.ctx.fillRect(Math.round(8 * 32 + 4 - this.camera.x), Math.round(3 * 32 + 5 - this.camera.y), 36, 18);
    this.ctx.fillStyle = '#2563eb';
    this.ctx.fillRect(Math.round(8 * 32 + 8 - this.camera.x), Math.round(3 * 32 + 8 - this.camera.y), 28, 2);

    // Upgrades that are bought:
    // Fireplace at (13, 2)
    if (this.player.houseUpgrades.fireplace) {
        this.ctx.drawImage(SPRITES.fireplace, Math.round(13 * 32 - this.camera.x), Math.round(2 * 32 - this.camera.y));
    }
    // Refrigerator at (6, 3)
    if (this.player.houseUpgrades.refrigerator) {
        this.ctx.drawImage(SPRITES.refrigerator, Math.round(6 * 32 - this.camera.x), Math.round(3 * 32 - 16 - this.camera.y));
    }
    // Persian Rug at (11, 8)
    if (this.player.houseUpgrades.persian_rug) {
        this.ctx.drawImage(SPRITES.persianRug, Math.round(11 * 32 - this.camera.x), Math.round(8 * 32 - this.camera.y));
    }
    // Tea Table at (11, 8)
    if (this.player.houseUpgrades.tea_table) {
        this.ctx.drawImage(SPRITES.teaTable, Math.round(11 * 32 + 8 - this.camera.x), Math.round(8 * 32 - this.camera.y));
    }
};

Game.drawShopInterior = function() {
    // Checkout Counter at (4, 4)
    this.ctx.drawImage(SPRITES.shopCounter, Math.round(4 * 32 - this.camera.x), Math.round(4 * 32 - this.camera.y));

    // 4 Display Shelves with goods on top!
    const shelfPos = [{x: 6, y: 7}, {x: 10, y: 7}, {x: 14, y: 7}, {x: 18, y: 7}];
    shelfPos.forEach((p, idx) => {
        const sx = Math.round(p.x * 32 - this.camera.x);
        const sy = Math.round(p.y * 32 - this.camera.y);
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
    });

    // Draw NPC Customers
    this.shopNPCs.forEach(npc => {
        const nx = Math.round(npc.x - this.camera.x);
        const ny = Math.round(npc.y - this.camera.y);

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
            this.ctx.fillText('🛍️', nx + 6, ny - 6);
        } else if (npc.state === 'leaving') {
            this.ctx.fillStyle = '#ffffff';
            this.ctx.beginPath();
            this.ctx.roundRect(nx + 4, ny - 16, 18, 12, 3);
            this.ctx.fill();
            this.ctx.strokeStyle = '#ec4899';
            this.ctx.lineWidth = 1;
            this.ctx.stroke();

            this.ctx.font = '9px sans-serif';
            this.ctx.fillText('😊', nx + 6, ny - 6);
        }
    });
};

Game.drawTileCursor = function() {
    const selItem = this.player.inventory[this.player.selectedSlot];
    const isWeapon = (selItem && (selItem.type === 'weapon' || WEAPONS[selItem.id]));

    if ((this.currentScene === 'farm' || this.currentScene === 'forest') && isWeapon && this.mouseWorld) {
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

Game.drawAnimals = function() {
    this.animals.forEach(a => {
        const sx = Math.round(a.x - this.camera.x);
        const sy = Math.round(a.y - this.camera.y);

        let spriteList = SPRITES[a.type] || SPRITES.cow;
        let sprite = spriteList[a.frame] || spriteList[0];
        this.ctx.drawImage(sprite, sx, sy);

        const distToPlayer = Math.hypot(this.player.x - a.x, this.player.y - a.y);

        // If player is close, show prompt badge
        if (distToPlayer < 55) {
            const promptY = sy - 18;
            this.ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
            this.ctx.beginPath();
            this.ctx.roundRect(sx + a.width / 2 - 24, promptY, 48, 15, 4);
            this.ctx.fill();
            this.ctx.strokeStyle = a.hasProduct ? '#facc15' : '#ec4899';
            this.ctx.lineWidth = 1;
            this.ctx.stroke();

            this.ctx.fillStyle = '#ffffff';
            this.ctx.font = 'bold 9px "Prompt", sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(a.hasProduct ? '🖐️ [E] เก็บ' : '❤️ [E] ลูบ', sx + a.width / 2, promptY + 11);
            this.ctx.textAlign = 'left';
        } else if (a.hasProduct) {
            // Cute soft bubble with product icon
            const bounce = Math.sin(performance.now() / 280) * 2;
            const bubbleX = sx + a.width / 2;
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
            this.ctx.fillText('❤️', sx + a.width - 6, sy - 2);
        }
    });
};

Game.drawPlayer = function() {
    if (this.player.invincibleTimer > 0 && Math.floor(performance.now() / 100) % 2 === 0) {
        return; // Invincibility flashing
    }
    const px = Math.round(this.player.x - this.camera.x);
    const py = Math.round(this.player.y - this.camera.y);

    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.25)';
    this.ctx.beginPath();
    this.ctx.ellipse(px + 12, py + 30, 8, 4, 0, 0, Math.PI * 2);
    this.ctx.fill();

    const dirFrames = SPRITES.player[this.player.direction] || SPRITES.player.down;
    const sprite = dirFrames[this.player.frame] || dirFrames[0];
    this.ctx.drawImage(sprite, px, py);
};

Game.drawRain = function() {
    this.ctx.strokeStyle = 'rgba(174, 214, 241, 0.6)';
    this.ctx.lineWidth = 1.5;
    const time = performance.now();
    for (let i = 0; i < 70; i++) {
        const rx = (i * 37 + time * 0.4) % this.width;
        const ry = (i * 29 + time * 0.8) % this.height;
        this.ctx.beginPath();
        this.ctx.moveTo(rx, ry);
        this.ctx.lineTo(rx - 4, ry + 12);
        this.ctx.stroke();
    }
};

Game.drawDayNightLighting = function() {
    const hour = this.time.hour;
    let alpha = 0;
    let color = '0, 0, 0';

    if (hour >= 6 && hour < 9) {
        alpha = 0.12 * (9 - hour) / 3;
        color = '251, 191, 36';
    } else if (hour >= 17 && hour < 20) {
        alpha = 0.28 * (hour - 16) / 4;
        color = '234, 88, 12';
    } else if (hour >= 20 || hour < 6) {
        alpha = 0.58;
        color = '15, 23, 42';
    }

    if (alpha > 0) {
        this.ctx.fillStyle = `rgba(${color}, ${alpha})`;
        this.ctx.fillRect(0, 0, this.width, this.height);

        // Cozy Stardew Valley lantern glow around player at night/dusk
        if (alpha > 0.2) {
            this.ctx.save();
            const px = Math.round(this.player.x + 12 - this.camera.x);
            const py = Math.round(this.player.y + 16 - this.camera.y);

            const lanternGrad = this.ctx.createRadialGradient(px, py, 12, px, py, 80);
            lanternGrad.addColorStop(0, 'rgba(254, 240, 138, 0.28)');
            lanternGrad.addColorStop(0.5, 'rgba(251, 191, 36, 0.12)');
            lanternGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

            this.ctx.globalCompositeOperation = 'lighter';
            this.ctx.fillStyle = lanternGrad;
            this.ctx.beginPath();
            this.ctx.arc(px, py, 80, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.restore();
        }
    }
};

Game.spawnParticles = function(x, y, color, count = 8) {
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

Game.updateHUD = function() {
    const hotbarEl = document.getElementById('hotbarSlots');
    if (hotbarEl) {
        hotbarEl.innerHTML = '';
        for (let i = 0; i < 10; i++) {
            const item = this.player.inventory[i];
            const slotEl = document.createElement('div');
            slotEl.className = 'hotbar-slot' + (i === this.player.selectedSlot ? ' active' : '');
            slotEl.onclick = () => this.selectHotbarSlot(i);

            const numBadge = document.createElement('span');
            numBadge.className = 'slot-key';
            numBadge.textContent = (i + 1) % 10;
            slotEl.appendChild(numBadge);

            if (item) {
                const img = document.createElement('img');
                img.src = SPRITES.getItemDataURL(item.id);
                img.className = 'slot-pixel-icon';
                slotEl.appendChild(img);

                if (item.count !== undefined) {
                    const countBadge = document.createElement('span');
                    countBadge.className = 'slot-count';
                    countBadge.textContent = item.count;
                    slotEl.appendChild(countBadge);
                }
            }
            hotbarEl.appendChild(slotEl);
        }
    }

    const goldEl = document.getElementById('hudGold');
    if (goldEl) goldEl.textContent = this.player.gold;

    const hpBar = document.getElementById('hpBarFill');
    if (hpBar) {
        const hpPercent = Math.max(0, (this.player.hp / this.player.maxHp) * 100);
        hpBar.style.height = hpPercent + '%';
        if (hpPercent < 30) hpBar.style.backgroundColor = '#991b1b';
        else hpBar.style.backgroundColor = '#ef4444';
    }

    const energyBar = document.getElementById('energyBarFill');
    if (energyBar) {
        const percent = Math.max(0, (this.player.energy / this.player.maxEnergy) * 100);
        energyBar.style.height = percent + '%';
        if (percent < 25) energyBar.style.backgroundColor = '#ef4444';
        else if (percent < 50) energyBar.style.backgroundColor = '#f59e0b';
        else energyBar.style.backgroundColor = '#22c55e';
    }

    const waterFill = document.getElementById('waterFill');
    if (waterFill) waterFill.style.width = ((this.player.waterCan / this.player.waterCanMax) * 100) + '%';

    const lvlEl = document.getElementById('hudLevel');
    if (lvlEl) lvlEl.textContent = 'Lv.' + this.player.level;

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
        const weatherIcon = this.time.weather === 'rain' ? '🌧️' : '☀️';
        dayEl.textContent = `${this.time.day} ${seasonName} ${weatherIcon}`;
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
    } else if (modalType === 'controlsModal') {
        document.getElementById('controlsModal').style.display = 'flex';
    } else if (modalType === 'loginModal') {
        if (typeof Auth !== 'undefined') Auth.openLoginModal();
    } else if (modalType === 'accountModal') {
        if (typeof Auth !== 'undefined') Auth.openAccountModal();
    }
};


Game.closeAllModals = function() {
    this.activeModal = null;
    document.querySelectorAll('.modal-overlay').forEach(el => el.style.display = 'none');
    this.closeDialogue();
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
    const previewCanvas = document.getElementById('wardrobePreviewCanvas');
    if (!previewCanvas) return;
    const ctx = previewCanvas.getContext('2d');
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
    this.addFloatingText('✨ แต่งชุดสำเร็จแล้ว!', this.player.x, this.player.y - 15, '#facc15');
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

            const countInput = document.getElementById('shelfStockCount');
            countInput.max = item.count;
            countInput.value = Math.min(5, item.count);

            const priceInput = document.getElementById('shelfStockPrice');
            priceInput.value = defaultPrice;
        };

        listContainer.appendChild(card);
    });

    if (!hasItems) {
        listContainer.innerHTML = '<p class="empty-hint">ไม่มีสินค้าในกระเป๋าที่สามารถวางขายได้</p>';
    }
};

Game.confirmStockShelf = function() {
    if (!this.selectedItemToStock || this.selectedShelfIndex === null) return;

    const count = parseInt(document.getElementById('shelfStockCount').value) || 1;
    const price = parseInt(document.getElementById('shelfStockPrice').value) || 20;

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

Game.renderCraftingModal = function() {
    const container = document.getElementById('craftingList');
    if (!container) return;
    container.innerHTML = '';

    Object.values(RECIPES).forEach(recipe => {
        const card = document.createElement('div');
        card.className = 'craft-card';

        const img = document.createElement('img');
        img.src = SPRITES.getItemDataURL(recipe.id);
        img.className = 'item-pixel-icon';

        const info = document.createElement('div');
        info.className = 'craft-card-info';

        let ingredText = '';
        let canCraft = true;
        for (let [ingId, reqCount] of Object.entries(recipe.ingredients)) {
            const has = this.countItemInInventory(ingId);
            const ingName = CROPS[ingId]?.name || RECIPES[ingId]?.name || (ingId === 'milk' ? 'นมวัว' : ingId === 'egg' ? 'ไข่ไก่' : ingId === 'wool' ? 'ขนแกะ' : ingId);
            ingredText += `<span class="${has >= reqCount ? 'ing-ok' : 'ing-missing'}">${ingName}: ${has}/${reqCount}</span> `;
            if (has < reqCount) canCraft = false;
        }

        info.innerHTML = `
            <h4>${recipe.name}</h4>
            <p>วัตถุดิบ: ${ingredText}</p>
            <span class="price-tag">ราคาขาย: ${recipe.sellPrice} G | +${recipe.xp} XP</span>
        `;

        const craftBtn = document.createElement('button');
        craftBtn.className = 'btn-craft' + (!canCraft ? ' disabled' : '');
        craftBtn.textContent = 'ปรุง / แปรรูป';
        craftBtn.disabled = !canCraft;
        craftBtn.onclick = () => {
            if (canCraft) {
                for (let [ingId, reqCount] of Object.entries(recipe.ingredients)) {
                    this.removeItemFromInventory(ingId, reqCount);
                }
                this.addItemToInventory(recipe.id, 1, recipe.name);
                this.addXp(recipe.xp);
                this.stats.crafts++;
                SoundEngine.craft();
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

Game.renderInventoryModal = function() {
    const grid = document.getElementById('inventoryGrid');
    if (!grid) return;
    grid.innerHTML = '';

    this.player.inventory.forEach((item, i) => {
        const slot = document.createElement('div');
        slot.className = 'bag-slot';

        if (item) {
            const img = document.createElement('img');
            img.src = SPRITES.getItemDataURL(item.id);
            img.className = 'item-pixel-icon';
            slot.appendChild(img);

            if (item.count !== undefined) {
                const countBadge = document.createElement('span');
                countBadge.className = 'slot-count';
                countBadge.textContent = item.count;
                slot.appendChild(countBadge);
            }
            slot.title = item.name;
        }
        grid.appendChild(slot);
    });
};

// ========================================================
// 14. FARM DEFENSE & HUNTERS SYSTEM (นายพราน & ยิงแมลงปีศาจ)
// ========================================================

Game.playerAttackAt = function(targetWorldX, targetWorldY) {
    if (this.currentScene !== 'farm' && this.currentScene !== 'forest') {
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

    SoundEngine.swordSlash();
    this.playerShootCooldown = weapon.cooldown || 250;
    this.meleeSlashAnim = {
        x: originX,
        y: originY,
        angle: angle,
        dir: this.player.direction,
        isHoly: (weapon.id === 'excalibur_sword'),
        timer: 160
    };

    const attackRange = weapon.range || 65;

    // Check hit on Farm Demon Bugs
    if (this.currentScene === 'farm') {
        for (let bIdx = this.demonBugs.length - 1; bIdx >= 0; bIdx--) {
            const bug = this.demonBugs[bIdx];
            const dist = Math.hypot((bug.x + 14) - originX, (bug.y + 14) - originY);
            if (dist < attackRange) {
                bug.hp -= weapon.damage;
                SoundEngine.hit();
                this.spawnParticles(bug.x + 14, bug.y + 14, '#ef4444', 8);
                this.addFloatingText('💥 -' + weapon.damage, bug.x, bug.y - 10, '#ef4444');
                if (bug.hp <= 0) {
                    SoundEngine.monsterDie();
                    this.spawnParticles(bug.x + 14, bug.y + 14, '#9333ea', 18);
                    this.player.gold += bug.loot.gold;
                    this.addItemToInventory(bug.loot.item, 1, bug.loot.name);
                    this.addXp(bug.loot.xp);
                    this.demonBugs.splice(bIdx, 1);
                    this.updateHUD();
                }
            }
        }
    }

    // Check hit on World Monsters
    if (this.currentScene === 'forest') {
        for (let mIdx = this.worldMonsters.length - 1; mIdx >= 0; mIdx--) {
            const m = this.worldMonsters[mIdx];
            const dist = Math.hypot((m.x + 14) - originX, (m.y + 12) - originY);
            if (dist < attackRange) {
                m.hp -= weapon.damage;
                SoundEngine.hit();
                this.spawnParticles(m.x + 14, m.y + 12, '#ef4444', 8);
                this.addFloatingText('💥 -' + weapon.damage, m.x, m.y - 12, '#ef4444');

                if (m.hp <= 0) {
                    SoundEngine.monsterDie();
                    this.spawnParticles(m.x + 14, m.y + 12, '#7e22ce', 20);
                    const cfg = WORLD_MONSTERS[m.type];
                    if (cfg) {
                        this.player.gold += cfg.gold;
                        this.addXp(cfg.xp);
                        cfg.drops.forEach(d => {
                            if (Math.random() <= d.chance) {
                                const itm = WORLD_ITEMS[d.item];
                                this.addItemToInventory(d.item, 1, itm ? itm.name : d.item);
                            }
                        });
                        if (m.type === 'shadow_wolf') {
                            this.player.questProgress.wolvesKilled = (this.player.questProgress.wolvesKilled || 0) + 1;
                        }
                        this.addFloatingText('+' + cfg.gold + ' G ' + cfg.name + ' ถูกปราบ! (+' + cfg.xp + ' XP)', m.x - 20, m.y - 20, '#4ade80');
                    }
                    this.worldMonsters.splice(mIdx, 1);
                    this.updateHUD();
                }
            }
        }

        // Check hit on Boss Kathuros
        if (this.boss && this.boss.alive) {
            const distBoss = Math.hypot((this.boss.x + 32) - originX, (this.boss.y + 32) - originY);
            if (distBoss < attackRange + 30) {
                this.boss.hp -= weapon.damage;
                SoundEngine.hit();
                this.spawnParticles(originX + Math.cos(angle) * 35, originY + Math.sin(angle) * 35, '#f59e0b', 10);
                this.addFloatingText('💥 -' + weapon.damage, this.boss.x + 20, this.boss.y - 10, '#ef4444');
                if (this.boss.hp <= 0) {
                    this.defeatBoss();
                }
            }
        }
    }

    // Excalibur Holy Beam projectile
    if (weapon.id === 'excalibur_sword') {
        this.projectiles.push({
            x: originX,
            y: originY,
            vx: Math.cos(angle) * 12,
            vy: Math.sin(angle) * 12,
            angle: angle,
            damage: weapon.damage,
            rangeLeft: weapon.range,
            type: 'holy_beam',
            fromPlayer: true
        });
    }
};

Game.playerShootAt = function(targetWorldX, targetWorldY, weapon = null) {
    if (this.currentScene !== 'farm' && this.currentScene !== 'forest') {
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

    const isRifle = (weapon.id === 'rifle' || weapon.id === 'dragon_rifle');
    SoundEngine.shoot(isRifle);

    this.projectiles.push({
        x: originX,
        y: originY,
        vx: Math.cos(angle) * weapon.speed,
        vy: Math.sin(angle) * weapon.speed,
        angle: angle,
        damage: weapon.damage,
        rangeLeft: weapon.range,
        type: weapon.bulletType,
        fromPlayer: true
    });

    this.playerShootCooldown = weapon.cooldown;
    this.spawnParticles(originX + Math.cos(angle) * 12, originY + Math.sin(angle) * 12, isRifle ? '#f59e0b' : '#cbd5e1', 5);
};

Game.triggerBugWave = function(manual = false) {
    if (this.currentScene !== 'farm') return;

    SoundEngine.alarm();
    this.waveCounter++;
    this.waveAlertTimer = 4500;
    this.addFloatingText('⚠️ ฝูงแมลงปีศาจบุกเข้าฟาร์ม!', this.player.x, this.player.y - 30, '#ef4444');

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
                    this.addFloatingText('💢 สัตว์เลี้ยงถูกก่อกวน!', bug.x - 20, bug.y - 12, '#f87171');
                } else {
                    this.spawnParticles(bug.x + 12, bug.y + 12, '#84cc16', 8);
                    this.addFloatingText('💥 แมลงกัดกินพืช!', bug.x - 10, bug.y - 12, '#ef4444');
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
                this.addFloatingText(isMarksman ? '💥 เล็งยิง!' : '🏹 สกัดแมลง!', hunter.x, hunter.y - 14, '#fde047');
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
    if (this.currentScene !== 'farm' && this.currentScene !== 'forest') {
        this.projectiles = [];
        return;
    }

    for (let i = this.projectiles.length - 1; i >= 0; i--) {
        const p = this.projectiles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.rangeLeft -= Math.hypot(p.vx, p.vy);

        if (p.rangeLeft <= 0) {
            this.projectiles.splice(i, 1);
            continue;
        }

        let hit = false;

        // 1. If projectile is from Boss: hit Player
        if (p.fromBoss) {
            const dist = Math.hypot((this.player.x + 12) - p.x, (this.player.y + 16) - p.y);
            if (dist < 18) {
                hit = true;
                this.damagePlayer(p.damage);
                this.spawnParticles(p.x, p.y, '#ef4444', 8);
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
                        SoundEngine.hit();
                        this.spawnParticles(p.x, p.y, '#f59e0b', 6);
                        this.addFloatingText('-' + p.damage, bug.x, bug.y - 10, '#ef4444');

                        if (bug.hp <= 0) {
                            SoundEngine.monsterDie();
                            this.spawnParticles(bug.x + 14, bug.y + 14, '#9333ea', 18);

                            this.player.gold += bug.loot.gold;
                            this.addItemToInventory(bug.loot.item, 1, bug.loot.name);
                            this.addXp(bug.loot.xp);
                            this.stats.bugsDefeated = (this.stats.bugsDefeated || 0) + 1;

                            this.addFloatingText('+' + bug.loot.gold + ' G ' + bug.loot.name + ' (+' + bug.loot.xp + ' XP)', bug.x - 20, bug.y - 20, '#4ade80');
                            this.demonBugs.splice(bIdx, 1);
                            this.updateHUD();
                        }
                        break;
                    }
                }
            }

            // Forest scene: Check collision against World Monsters
            if (this.currentScene === 'forest') {
                for (let mIdx = this.worldMonsters.length - 1; mIdx >= 0; mIdx--) {
                    const m = this.worldMonsters[mIdx];
                    const dist = Math.hypot((m.x + 16) - p.x, (m.y + 16) - p.y);

                    if (dist < 22) {
                        hit = true;
                        m.hp -= p.damage;
                        SoundEngine.hit();
                        this.spawnParticles(p.x, p.y, '#f59e0b', 6);
                        this.addFloatingText('-' + p.damage, m.x, m.y - 10, '#ef4444');

                        if (m.hp <= 0) {
                            SoundEngine.monsterDie();
                            this.spawnParticles(m.x + 16, m.y + 16, '#9333ea', 18);
                            const cfg = WORLD_MONSTERS[m.type];
                            if (cfg) {
                                this.player.gold += cfg.gold;
                                this.addXp(cfg.xp);
                                cfg.drops.forEach(d => {
                                    if (Math.random() <= d.chance) {
                                        const itm = WORLD_ITEMS[d.item];
                                        this.addItemToInventory(d.item, 1, itm ? itm.name : d.item);
                                    }
                                });
                                if (m.type === 'shadow_wolf') {
                                    this.player.questProgress.wolvesKilled = (this.player.questProgress.wolvesKilled || 0) + 1;
                                }
                                this.addFloatingText('+' + cfg.gold + ' G ' + cfg.name + ' ถูกปราบ! (+' + cfg.xp + ' XP)', m.x - 20, m.y - 20, '#4ade80');
                            }
                            this.worldMonsters.splice(mIdx, 1);
                            this.updateHUD();
                        }
                        break;
                    }
                }

                // Check collision against Boss Kathuros
                if (!hit && this.boss && this.boss.alive) {
                    const distBoss = Math.hypot((this.boss.x + 32) - p.x, (this.boss.y + 32) - p.y);
                    if (distBoss < 36) {
                        hit = true;
                        this.boss.hp -= p.damage;
                        SoundEngine.hit();
                        this.spawnParticles(p.x, p.y, '#f59e0b', 8);
                        this.addFloatingText('💥 -' + p.damage, this.boss.x + 20, this.boss.y - 10, '#ef4444');
                        if (this.boss.hp <= 0) {
                            this.defeatBoss();
                        }
                    }
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
                <div class="hunter-stats">💧 รดน้ำแปลงผัก | 🌾 เก็บเกี่ยวผลผลิตสุกอัตโนมัติ | ⚡ ความเร็ว: ${helperConfig.speed}</div>
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
            <div class="hunter-stats">⚡ พลังยิง: ${hunterConfig.damage} | 🎯 ระยะยิง: ${hunterConfig.range}px | 🛡️ พื้นที่: ${hunterConfig.patrolArea === 'crops' ? 'รอบแปลงผัก' : 'รอบคอกสัตว์'}</div>
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

    this.addFloatingText('🧑‍🌾 จ้าง ' + config.name + ' สำเร็จแล้ว!', this.player.x, this.player.y - 25, '#4ade80');
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
                        this.addFloatingText('🌾 ' + gardener.name.split(' ')[0] + ' เก็บเกี่ยวแล้ว!', gardener.x - 10, gardener.y - 15, '#fde047');
                        gardener.actionCooldown = 550;
                    }
                } else if (gardener.target.type === 'water') {
                    if (targetTile && targetTile.tilled && !targetTile.watered) {
                        targetTile.watered = true;
                        SoundEngine.water();
                        this.spawnParticles(gardener.target.tileX * 32 + 16, gardener.target.tileY * 32 + 16, '#60a5fa', 8);
                        this.addFloatingText('💧 ' + gardener.name.split(' ')[0] + ' รดน้ำแล้ว!', gardener.x - 10, gardener.y - 15, '#38bdf8');
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

Game.drawHiredGardeners = function() {
    this.hiredGardeners.forEach(g => {
        const gx = Math.round(g.x - this.camera.x);
        const gy = Math.round(g.y - this.camera.y);

        // Shadow
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.25)';
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
    });
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

    this.addFloatingText('🤠 จ้าง ' + config.name + ' สำเร็จแล้ว!', this.player.x, this.player.y - 25, '#4ade80');
    this.updateHUD();
    this.renderHuntersModal();
};

Game.drawDemonBugs = function() {
    this.demonBugs.forEach(bug => {
        const sx = Math.round(bug.x - this.camera.x);
        const sy = Math.round(bug.y - this.camera.y);

        const frames = SPRITES.bugs[bug.type];
        if (frames) {
            const spr = frames[bug.frame] || frames[0];
            this.ctx.drawImage(spr, sx, sy);
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
    });
};

Game.drawHiredHunters = function() {
    this.hiredHunters.forEach(hunter => {
        const hx = Math.round(hunter.x - this.camera.x);
        const hy = Math.round(hunter.y - this.camera.y);

        // Shadow
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.25)';
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
    });
};

Game.drawProjectiles = function() {
    this.projectiles.forEach(p => {
        const sx = Math.round(p.x - this.camera.x);
        const sy = Math.round(p.y - this.camera.y);

        const spr = SPRITES.projectiles[p.type] || SPRITES.projectiles.stone;
        this.ctx.save();
        this.ctx.translate(sx, sy);
        this.ctx.rotate(p.angle || 0);
        this.ctx.drawImage(spr, -8, -8);
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
    this.ctx.fillText('⚠️ แมลงปีศาจบุกเข้าฟาร์ม! ยิงสกัดด้วยคลิก/Space', this.width / 2, by + 19);
    this.ctx.restore();
};

// ========================================================
// 14. OPEN WORLD, BOSS & STORY QUEST ENGINE
// ========================================================

Game.initForestScene = function() {
    if (!this.worldMonsters || this.worldMonsters.length === 0) {
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
    }

    if (!this.boss || !this.boss.alive) {
        if (!this.player.questProgress.kathurosDefeated) {
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
                summonCooldown: 12000,
                frame: 0,
                animTimer: 0
            };
        }
    }
};

Game.damagePlayer = function(amount) {
    if (this.player.invincibleTimer > 0) return;

    this.player.hp -= amount;
    this.player.invincibleTimer = 1200; // 1.2s invulnerability
    SoundEngine.hit();
    this.addFloatingText('💔 -' + amount + ' HP', this.player.x, this.player.y - 20, '#ef4444');
    this.updateHUD();

    if (this.player.hp <= 0) {
        SoundEngine.monsterDie();
        this.player.hp = this.player.maxHp;
        this.player.energy = 50;
        const lostGold = Math.min(100, this.player.gold);
        this.player.gold -= lostGold;
        this.addFloatingText('💀 หมดสติไป! ตื่นขึ้นมาที่เตียงบ้านพัก (-' + lostGold + ' G)', this.player.x - 30, this.player.y - 30, '#ef4444');
        this.switchScene('house', 19, 4);
    }
};

Game.updateWorldMonsters = function(dt) {
    if (this.currentScene !== 'forest') return;

    for (let i = this.worldMonsters.length - 1; i >= 0; i--) {
        const m = this.worldMonsters[i];
        m.animTimer = (m.animTimer || 0) + dt;
        if (m.animTimer > 160) {
            m.animTimer = 0;
            m.frame = (m.frame + 1) % 2;
        }

        if (m.attackCooldown > 0) {
            m.attackCooldown -= dt;
        }

        const dist = Math.hypot((this.player.x + 12) - (m.x + 16), (this.player.y + 14) - (m.y + 16));

        // Aggro & chase player
        if (dist < (m.aggroRange || 160)) {
            const angle = Math.atan2((this.player.y + 14) - (m.y + 16), (this.player.x + 12) - (m.x + 16));
            m.x += Math.cos(angle) * (m.speed || 1.2);
            m.y += Math.sin(angle) * (m.speed || 1.2);

            if (Math.abs(Math.cos(angle)) > Math.abs(Math.sin(angle))) {
                m.direction = Math.cos(angle) > 0 ? 'right' : 'left';
            } else {
                m.direction = Math.sin(angle) > 0 ? 'down' : 'up';
            }

            // Attack player if within 26px
            if (dist < 26 && m.attackCooldown <= 0) {
                this.damagePlayer(m.damage || 10);
                m.attackCooldown = 1500;
            }
        }
    }
};

Game.updateBoss = function(dt) {
    if (this.currentScene !== 'forest' || !this.boss || !this.boss.alive) {
        const bossBar = document.getElementById('bossHealthBar');
        if (bossBar && bossBar.style.display !== 'none') bossBar.style.display = 'none';
        return;
    }

    const dist = Math.hypot((this.player.x + 12) - (this.boss.x + 32), (this.player.y + 14) - (this.boss.y + 32));

    // Boss Activation & Health Bar
    const bossBar = document.getElementById('bossHealthBar');
    if (dist < 420) {
        this.boss.active = true;
        if (bossBar) bossBar.style.display = 'flex';

        const hpPct = Math.max(0, (this.boss.hp / this.boss.maxHp) * 100);
        const bossHpFill = document.getElementById('bossHpFill');
        if (bossHpFill) bossHpFill.style.width = hpPct + '%';
        const bossHpText = document.getElementById('bossHpText');
        if (bossHpText) bossHpText.textContent = `${this.boss.hp} / ${this.boss.maxHp} HP`;

        // Phases
        if (this.boss.hp <= 400) this.boss.phase = 3;
        else if (this.boss.hp <= 800) this.boss.phase = 2;
        else this.boss.phase = 1;
    } else if (dist > 650) {
        this.boss.active = false;
        if (bossBar) bossBar.style.display = 'none';
    }

    if (this.boss.active) {
        // Wing flapping animation
        this.boss.animTimer = (this.boss.animTimer || 0) + dt;
        if (this.boss.animTimer > 180) {
            this.boss.animTimer = 0;
            this.boss.frame = (this.boss.frame + 1) % 2;
        }

        // Movement towards player
        if (dist > 75) {
            const moveSpeed = this.boss.phase === 3 ? 1.3 : 0.8;
            const ang = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32));
            this.boss.x += Math.cos(ang) * moveSpeed;
            this.boss.y += Math.sin(ang) * moveSpeed;
        }

        // Hellfire Attacks
        this.boss.attackCooldown -= dt;
        if (this.boss.attackCooldown <= 0) {
            if (this.boss.phase === 1) {
                SoundEngine.bossAttack();
                const ang = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32));
                this.projectiles.push({
                    x: this.boss.x + 32,
                    y: this.boss.y + 32,
                    vx: Math.cos(ang) * 4.5,
                    vy: Math.sin(ang) * 4.5,
                    angle: ang,
                    damage: 16,
                    rangeLeft: 450,
                    type: 'boss_flame',
                    fromBoss: true
                });
                this.boss.attackCooldown = 2200;
            } else if (this.boss.phase === 2) {
                SoundEngine.bossAttack();
                [0, Math.PI * 0.5, Math.PI, Math.PI * 1.5, Math.PI * 0.25, Math.PI * 0.75, Math.PI * 1.25, Math.PI * 1.75].forEach(ang => {
                    this.projectiles.push({
                        x: this.boss.x + 32,
                        y: this.boss.y + 32,
                        vx: Math.cos(ang) * 4.0,
                        vy: Math.sin(ang) * 4.0,
                        angle: ang,
                        damage: 20,
                        rangeLeft: 420,
                        type: 'boss_flame',
                        fromBoss: true
                    });
                });
                this.boss.attackCooldown = 2600;
            } else { // Phase 3 (Enraged Triple Burst)
                SoundEngine.bossAttack();
                const baseAng = Math.atan2((this.player.y + 14) - (this.boss.y + 32), (this.player.x + 12) - (this.boss.x + 32));
                [-0.25, 0, 0.25].forEach(offset => {
                    const ang = baseAng + offset;
                    this.projectiles.push({
                        x: this.boss.x + 32,
                        y: this.boss.y + 32,
                        vx: Math.cos(ang) * 5.2,
                        vy: Math.sin(ang) * 5.2,
                        angle: ang,
                        damage: 24,
                        rangeLeft: 500,
                        type: 'boss_flame',
                        fromBoss: true
                    });
                });
                this.boss.attackCooldown = 1500;
            }
        }

        // Summoning Minions
        this.boss.summonCooldown -= dt;
        if (this.boss.summonCooldown <= 0) {
            this.boss.summonCooldown = 13000;
            SoundEngine.bossRoar();
            this.addFloatingText('🔥 จอมอสูรคำราม! ปลุกหมาป่าเงา!', this.boss.x + 10, this.boss.y - 15, '#ef4444');
            this.worldMonsters.push({
                id: 'minion_' + performance.now(),
                type: 'shadow_wolf',
                x: this.boss.x - 30,
                y: this.boss.y + 20,
                hp: 50,
                maxHp: 50,
                speed: 1.5,
                damage: 12,
                aggroRange: 320,
                attackCooldown: 0,
                direction: 'down',
                frame: 0,
                animTimer: 0
            });
            this.worldMonsters.push({
                id: 'minion_' + (performance.now() + 1),
                type: 'shadow_wolf',
                x: this.boss.x + 70,
                y: this.boss.y + 20,
                hp: 50,
                maxHp: 50,
                speed: 1.5,
                damage: 12,
                aggroRange: 320,
                attackCooldown: 0,
                direction: 'down',
                frame: 0,
                animTimer: 0
            });
        }
    }
};

Game.defeatBoss = function() {
    this.boss.alive = false;
    const bossBar = document.getElementById('bossHealthBar');
    if (bossBar) bossBar.style.display = 'none';

    SoundEngine.monsterDie();
    SoundEngine.bossRoar();
    this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#ef4444', 35);
    this.spawnParticles(this.boss.x + 32, this.boss.y + 32, '#facc15', 25);

    this.player.gold += BOSS_KATHUROS.gold;
    this.addXp(BOSS_KATHUROS.xp);
    this.addItemToInventory('demon_heart', 1, 'หัวใจจอมอสูร (Demon Heart)');
    this.addItemToInventory('crown_of_despair', 1, 'มงกุฎแห่งความสิ้นหวัง (Crown of Despair)');
    this.player.questProgress.kathurosDefeated = true;

    this.addFloatingText('👑 มหาศึกสิ้นสุด! กำราบจอมอสูรคาธูรอส! (+1,500 G, +500 XP)', this.boss.x - 30, this.boss.y - 30, '#facc15');
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

    // Draw Portrait
    const cvs = document.getElementById('dialoguePortraitCanvas');
    if (cvs) {
        const ctx = cvs.getContext('2d');
        ctx.imageSmoothingEnabled = false;
        ctx.clearRect(0, 0, 48, 48);
        const pType = npcCfg.portraitType || npcCfg.portrait || npcId;
        const pSpr = SPRITES.portraits[pType];
        if (pSpr) ctx.drawImage(pSpr, 0, 0);
    }

    const textEl = document.getElementById('dialogueText');
    const actionsEl = document.getElementById('dialogueActionButtons');
    actionsEl.innerHTML = '';

    const dlgs = npcCfg.dialogues || npcCfg.dialogue || {};

    if (npcId === 'valeria') {
        const q1State = this.player.quests.q1;
        const q2State = this.player.quests.q2;

        if (!q1State) {
            textEl.textContent = dlgs.intro || 'ยินดีที่ได้พบท่านชาวสวน!';
            const acceptBtn = document.createElement('button');
            acceptBtn.className = 'btn-dialogue-action btn-quest-accept';
            acceptBtn.textContent = '📜 รับภารกิจ: เงาแห่งพงไพร';
            acceptBtn.onclick = () => {
                this.player.quests.q1 = 'active';
                SoundEngine.levelUp();
                this.addFloatingText('📜 รับภารกิจ: เงาแห่งพงไพร', this.player.x, this.player.y - 20, '#fde047');
                this.closeDialogue();
            };
            actionsEl.appendChild(acceptBtn);
        } else if (q1State === 'active') {
            const wolvesKilled = this.player.questProgress.wolvesKilled || 0;
            if (wolvesKilled >= 3) {
                textEl.textContent = dlgs.q1_reward || dlgs.q1_complete || 'ขอบคุณที่ท่านช่วยกำจัดหมาป่าเงา!';
                const turnInBtn = document.createElement('button');
                turnInBtn.className = 'btn-dialogue-action btn-quest-accept';
                turnInBtn.textContent = '✨ ส่งภารกิจที่ 1 รับรางวัล (ดาบเหล็กกล้า + 200 G)';
                turnInBtn.onclick = () => {
                    this.player.quests.q1 = 'completed';
                    this.player.gold += 200;
                    this.addXp(100);
                    this.addItemToInventory('iron_sword', 1, 'ดาบเหล็กกล้าอัศวิน (Iron Sword)');
                    SoundEngine.levelUp();
                    this.addFloatingText('🎉 สำเร็จภารกิจที่ 1! ได้รับดาบเหล็กกล้า (+200 G, +100 XP)', this.player.x, this.player.y - 25, '#4ade80');
                    this.closeDialogue();
                    this.updateHUD();
                };
                actionsEl.appendChild(turnInBtn);
            } else {
                textEl.textContent = `ระวังตัวด้วยนะสหาย! เจ้ากำจัดหมาป่าเงาไปแล้ว ${wolvesKilled}/3 ตัว ยังเหลืออยู่อีก จงระวังเขี้ยวเล็บของพวกมัน!`;
            }
        } else if (q1State === 'completed' && !q2State) {
            textEl.textContent = 'ยอดเยี่ยมมาก! ผืนป่าทางใต้ปลอดภัยขึ้นแล้ว แต่เราต้องการเสบียงและแร่เพื่อเตรียมรบกับจอมอสูร เจ้าช่วยไปหา สมุนไพรดวงดาว 3 ชิ้น และขุดแร่ทับทิม 2 ก้อน ได้หรือไม่?';
            const acceptQ2Btn = document.createElement('button');
            acceptQ2Btn.className = 'btn-dialogue-action btn-quest-accept';
            acceptQ2Btn.textContent = '📜 รับภารกิจ: ชำระล้างผืนป่า (เควสต์ที่ 2)';
            acceptQ2Btn.onclick = () => {
                this.player.quests.q2 = 'active';
                SoundEngine.levelUp();
                this.addFloatingText('📜 รับภารกิจ: ชำระล้างผืนป่า', this.player.x, this.player.y - 20, '#fde047');
                this.closeDialogue();
            };
            actionsEl.appendChild(acceptQ2Btn);
        } else if (q2State === 'active') {
            const hasHerbs = this.countItemInInventory('starflower_herb');
            const hasRubies = this.countItemInInventory('ruby_gem');
            if (hasHerbs >= 3 && hasRubies >= 2) {
                textEl.textContent = 'วิเศษไปเลย! สมุนไพรเหล่านี้จะนำมาปรุงยาฟื้นพลัง และทับทิมจะนำไปเสริมคมดาบ นี่คือรางวัลของเจ้า!';
                const turnInQ2Btn = document.createElement('button');
                turnInQ2Btn.className = 'btn-dialogue-action btn-quest-accept';
                turnInQ2Btn.textContent = '✨ ส่งภารกิจที่ 2 (รับ 350 G + ยาฟื้นพลัง x3)';
                turnInQ2Btn.onclick = () => {
                    this.removeItemFromInventory('starflower_herb', 3);
                    this.removeItemFromInventory('ruby_gem', 2);
                    this.player.quests.q2 = 'completed';
                    this.player.gold += 350;
                    this.addXp(150);
                    this.addItemToInventory('health_potion', 3, 'ยาฟื้นพลังชีวิตชั้นเลิศ');
                    SoundEngine.levelUp();
                    this.addFloatingText('🎉 สำเร็จภารกิจที่ 2! (+350 G, +150 XP, ยา x3)', this.player.x, this.player.y - 25, '#4ade80');
                    this.closeDialogue();
                    this.updateHUD();
                };
                actionsEl.appendChild(turnInQ2Btn);
            } else {
                textEl.textContent = `สมุนไพรดวงดาว (${hasHerbs}/3) และแร่ทับทิม (${hasRubies}/2) เจ้ายังเก็บไม่ครบ ลองเดินสำรวจลึกเข้าไปในป่าดูนะ!`;
            }
        } else {
            textEl.textContent = 'เจ้าแข็งแกร่งขึ้นมาก! บัดนี้ถึงเวลาบุกวิหารทางเหนือเพื่อกำราบจอมอสูรคาธูรอสแล้ว จงไปคุยกับผู้เฒ่าเอลดรินเพื่อรับพรอันศักดิ์สิทธิ์เถิด!';
        }
    } else if (npcId === 'eldrin') {
        const q3State = this.player.quests.q3;
        if (!q3State) {
            textEl.textContent = dlgs.intro || 'โฮ่โฮ่... ผืนป่าทางเหนือนั้นมีวิหารโบราณสถิตอยู่';
            const acceptQ3Btn = document.createElement('button');
            acceptQ3Btn.className = 'btn-dialogue-action btn-quest-accept';
            acceptQ3Btn.textContent = '⚔️ รับมหาภารกิจ: โค่นจอมอสูรคาธูรอส';
            acceptQ3Btn.onclick = () => {
                this.player.quests.q3 = 'active';
                SoundEngine.bossRoar();
                this.addFloatingText('⚔️ รับมหาภารกิจ: โค่นจอมอสูรคาธูรอส!', this.player.x, this.player.y - 20, '#ef4444');
                this.closeDialogue();
            };
            actionsEl.appendChild(acceptQ3Btn);
        } else if (q3State === 'active') {
            if (this.player.questProgress.kathurosDefeated) {
                textEl.textContent = dlgs.boss_defeated || dlgs.victory || 'ม่านหมอกสีเลือดสลายไปแล้ว... แผ่นดินได้รับความบริสุทธิ์คืนมา!';
                const turnInQ3Btn = document.createElement('button');
                turnInQ3Btn.className = 'btn-dialogue-action btn-quest-accept';
                turnInQ3Btn.textContent = '🏆 ส่งมอบชัยชนะ (รับ 1,000 G + ดาบศักดิ์สิทธิ์เอ็กซ์คาลิเบอร์)';
                turnInQ3Btn.onclick = () => {
                    this.player.quests.q3 = 'completed';
                    this.player.gold += 1000;
                    this.addXp(600);
                    this.addItemToInventory('excalibur_sword', 1, 'ดาบศักดิ์สิทธิ์เอ็กซ์คาลิเบอร์ (Excalibur Sword)');
                    SoundEngine.levelUp();
                    this.addFloatingText('🏆 มหาศึกสิ้นสุด! ได้รับดาบศักดิ์สิทธิ์เอ็กซ์คาลิเบอร์! (+1,000 G)', this.player.x, this.player.y - 30, '#facc15');
                    this.closeDialogue();
                    this.updateHUD();
                };
                actionsEl.appendChild(turnInQ3Btn);
            } else {
                textEl.textContent = dlgs.lore || 'จอมอสูรคาธูรอสสิงสถิตอยู่ในวิหารศิลาทางเหนือ ข้ามสะพานหินขึ้นไป เจ้าจะได้เผชิญหน้ากับมัน จงระวังเพลิงนรกผลาญวิญญาณ!';
            }
        } else {
            textEl.textContent = 'ความสงบสุขกลับคืนสู่ผืนป่าและฟาร์มของเราแล้ว ขอพรแห่งปัญญาและแสงสว่างจงสถิตอยู่กับเจ้าตลอดกาล ผู้กล้าแห่งฟาร์มสุขใจ!';
        }

        // Eldrin's Holy Blessing button (always available)
        const blessBtn = document.createElement('button');
        blessBtn.className = 'btn-dialogue-action';
        blessBtn.textContent = '✨ ขอรับพรศักดิ์สิทธิ์ (ฟื้นฟู HP และพลังงานเต็ม)';
        blessBtn.onclick = () => {
            this.player.hp = this.player.maxHp;
            this.player.energy = this.player.maxEnergy;
            SoundEngine.levelUp();
            this.spawnParticles(this.player.x + 12, this.player.y + 16, '#38bdf8', 16);
            this.addFloatingText('✨ ได้รับพรศักดิ์สิทธิ์! ฟื้นฟู HP 100% & พลังงาน 100%', this.player.x - 20, this.player.y - 20, '#38bdf8');
            this.updateHUD();
            this.closeDialogue();
        };
        actionsEl.appendChild(blessBtn);
    } else if (npcId === 'kael') {
        textEl.textContent = dlgs.intro || dlgs.forge_ready || 'ยินดีต้อนรับสู่เตาหลอมของข้า! นำแร่และผลึกมาสิ ข้าจะตีสุดยอดอาวุธให้!';
        const openForgeBtn = document.createElement('button');
        openForgeBtn.className = 'btn-dialogue-action btn-quest-accept';
        openForgeBtn.textContent = '🔨 เปิดโรงตีเหล็ก (Forge)';
        openForgeBtn.onclick = () => {
            this.closeDialogue();
            this.openModal('forgeModal');
        };
        actionsEl.appendChild(openForgeBtn);
    }

    // Close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'btn-dialogue-action';
    closeBtn.textContent = '✖ ปิดการสนทนา';
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
            statusText = '⚡ กำลังดำเนินการ';
            statusClass = 'quest-badge-active';

            if (q.id === 'q1') {
                const count = Math.min(3, this.player.questProgress.wolvesKilled || 0);
                progressDetail = `<div class="quest-prog-text">กำจัดหมาป่าเงา: ${count}/3 ตัว</div>`;
            } else if (q.id === 'q2') {
                const h = Math.min(3, this.countItemInInventory('starflower_herb'));
                const r = Math.min(2, this.countItemInInventory('ruby_gem'));
                progressDetail = `<div class="quest-prog-text">สมุนไพรดวงดาว: ${h}/3 ชิ้น | แร่ทับทิม: ${r}/2 ก้อน</div>`;
            } else if (q.id === 'q3') {
                const def = this.player.questProgress.kathurosDefeated ? 'สำเร็จ' : 'ยังไม่ถูกปราบ';
                progressDetail = `<div class="quest-prog-text">จอมอสูรคาธูรอส: ${def}</div>`;
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
                🎁 รางวัล: <span>${q.rewardText || q.rewardDesc || ''}</span>
            </div>
        `;
        list.appendChild(card);
    });
};

Game.renderForgeModal = function() {
    const list = document.getElementById('forgeList');
    if (!list) return;
    list.innerHTML = '';

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
            const matName = WORLD_ITEMS[matId]?.name || matId;
            const ok = hasQty >= reqQty;
            if (!ok) canForge = false;
            matHtml += `<span class="${ok ? 'ing-ok' : 'ing-missing'}">${matName}: ${hasQty}/${reqQty}</span> `;
        }

        const cost = recipe.cost ?? recipe.goldCost ?? 0;
        if (this.player.gold < cost) canForge = false;
        const goldOk = this.player.gold >= cost;

        info.innerHTML = `
            <h4>${recipe.name}</h4>
            <p>${recipe.desc}</p>
            <div class="forge-mats">${matHtml}</div>
            <div class="price-tag ${goldOk ? 'ing-ok' : 'ing-missing'}">ค่าตีเหล็ก: ${cost} G (มี ${this.player.gold} G)</div>
        `;

        const btn = document.createElement('button');
        btn.className = 'btn-forge';
        btn.textContent = canForge ? '🔨 ตีขึ้นรูป' : 'วัตถุดิบไม่พอ';
        btn.disabled = !canForge;
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
    this.addFloatingText('✨ ตี ' + recipe.name + ' สำเร็จแล้ว!', this.player.x - 20, this.player.y - 25, '#4ade80');
    this.updateHUD();
    this.renderForgeModal();
};

Game.drawForestEntities = function() {
    // 1. Campfire animated flame at (25, 30)
    const cx = Math.round(25 * 32 - this.camera.x);
    const cy = Math.round(30 * 32 - this.camera.y);
    this.ctx.fillStyle = '#f97316';
    const flicker = Math.sin(performance.now() / 120) * 3;
    this.ctx.beginPath();
    this.ctx.arc(cx + 16, cy + 14, 6 + flicker, 0, Math.PI * 2);
    this.ctx.fill();
    this.ctx.fillStyle = '#fde047';
    this.ctx.beginPath();
    this.ctx.arc(cx + 16, cy + 14, 3 + flicker * 0.5, 0, Math.PI * 2);
    this.ctx.fill();

    // 2. Story NPCs
    // Valeria at (22, 30)
    const vx = Math.round(22 * 32 - this.camera.x);
    const vy = Math.round(30 * 32 - this.camera.y);
    this.ctx.fillStyle = 'rgba(0,0,0,0.25)';
    this.ctx.beginPath(); this.ctx.ellipse(vx + 12, vy + 30, 8, 4, 0, 0, Math.PI * 2); this.ctx.fill();
    const valFrame = SPRITES.storyNpcs.valeria.down[Math.floor(performance.now() / 400) % 2];
    if (valFrame) this.ctx.drawImage(valFrame, vx, vy);
    this.ctx.fillStyle = '#60a5fa';
    this.ctx.font = 'bold 9px "Prompt", sans-serif';
    this.ctx.fillText('วาเลเรีย (อัศวิน)', vx - 8, vy - 6);

    // Eldrin at (28, 30)
    const ex = Math.round(28 * 32 - this.camera.x);
    const ey = Math.round(30 * 32 - this.camera.y);
    this.ctx.fillStyle = 'rgba(0,0,0,0.25)';
    this.ctx.beginPath(); this.ctx.ellipse(ex + 12, ey + 30, 8, 4, 0, 0, Math.PI * 2); this.ctx.fill();
    const eldFrame = SPRITES.storyNpcs.eldrin.down[Math.floor(performance.now() / 400) % 2];
    if (eldFrame) this.ctx.drawImage(eldFrame, ex, ey);
    this.ctx.fillStyle = '#c084fc';
    this.ctx.font = 'bold 9px "Prompt", sans-serif';
    this.ctx.fillText('ปราชญ์เอลดริน', ex - 6, ey - 6);

    // Kael at (18, 32)
    const kx = Math.round(18 * 32 - this.camera.x);
    const ky = Math.round(32 * 32 - this.camera.y);
    this.ctx.fillStyle = 'rgba(0,0,0,0.25)';
    this.ctx.beginPath(); this.ctx.ellipse(kx + 12, ky + 30, 8, 4, 0, 0, Math.PI * 2); this.ctx.fill();
    const kaelFrame = SPRITES.storyNpcs.kael.down[Math.floor(performance.now() / 400) % 2];
    if (kaelFrame) this.ctx.drawImage(kaelFrame, kx, ky);
    this.ctx.fillStyle = '#fb923c';
    this.ctx.font = 'bold 9px "Prompt", sans-serif';
    this.ctx.fillText('ช่างตีเหล็ก คาเอล', kx - 12, ky - 6);

    // 3. World Monsters
    this.worldMonsters.forEach(m => {
        const mx = Math.round(m.x - this.camera.x);
        const my = Math.round(m.y - this.camera.y);

        // Shadow
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        this.ctx.beginPath();
        this.ctx.ellipse(mx + 16, my + 28, 10, 4, 0, 0, Math.PI * 2);
        this.ctx.fill();

        const frames = SPRITES.worldMonsters[m.type];
        if (frames) {
            const spr = frames[m.frame] || frames[0];
            this.ctx.drawImage(spr, mx, my);
        }

        // Health bar
        const barW = 30;
        const barH = 4;
        const hpPct = Math.max(0, m.hp / m.maxHp);
        this.ctx.fillStyle = '#0f172a';
        this.ctx.fillRect(mx + 1, my - 8, barW, barH);
        this.ctx.fillStyle = hpPct > 0.4 ? '#22c55e' : '#ef4444';
        this.ctx.fillRect(mx + 1, my - 8, Math.round(barW * hpPct), barH);

        // Name tag (clean short name, avoiding long cluttered text)
        const cfg = WORLD_MONSTERS[m.type];
        const mName = cfg ? (cfg.shortName || cfg.name.split(' (')[0]) : m.type;
        this.ctx.fillStyle = '#f8fafc';
        this.ctx.font = 'bold 8px "Prompt", sans-serif';
        this.ctx.fillText(mName, mx - 2, my - 11);
    });

    // 4. Boss Kathuros
    if (this.boss && this.boss.alive) {
        const bx = Math.round(this.boss.x - this.camera.x);
        const by = Math.round(this.boss.y - this.camera.y);

        // Demonic aura shadow
        this.ctx.fillStyle = 'rgba(185, 28, 28, 0.35)';
        this.ctx.beginPath();
        this.ctx.ellipse(bx + 32, by + 60, 28, 10, 0, 0, Math.PI * 2);
        this.ctx.fill();

        const spr = SPRITES.bossKathuros[this.boss.frame] || SPRITES.bossKathuros[0];
        if (spr) this.ctx.drawImage(spr, bx, by);

        // Boss overhead tag (clean, minimal - full title is in top health bar)
        this.ctx.fillStyle = '#fca5a5';
        this.ctx.font = 'bold 9px "Prompt", sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('👑 คารูธอส (บอส)', bx + 32, by - 6);
        this.ctx.textAlign = 'start';
    }

};

Game.drawMeleeSlash = function() {
    if (!this.meleeSlashAnim) return;

    const slash = this.meleeSlashAnim;
    const sx = Math.round(slash.x - this.camera.x);
    const sy = Math.round(slash.y - this.camera.y);

    this.ctx.save();
    this.ctx.translate(sx, sy);
    this.ctx.rotate(slash.angle);

    this.ctx.strokeStyle = slash.isHoly ? 'rgba(253, 224, 71, 0.9)' : 'rgba(248, 250, 252, 0.85)';
    this.ctx.lineWidth = 3;
    this.ctx.beginPath();
    this.ctx.arc(20, 0, 24, -Math.PI / 3, Math.PI / 3);
    this.ctx.stroke();

    if (slash.isHoly) {
        this.ctx.strokeStyle = 'rgba(96, 165, 250, 0.8)';
        this.ctx.lineWidth = 1.5;
        this.ctx.beginPath();
        this.ctx.arc(26, 0, 30, -Math.PI / 4, Math.PI / 4);
        this.ctx.stroke();
    }

    this.ctx.restore();
};

// ========================================================
// 15. MAIN GAME LOOP
// ========================================================

Game.gameLoop = function(timestamp) {
    const rawDt = timestamp - (this.lastTime || timestamp);
    const dt = Math.min(100, Math.max(1, rawDt));
    this.lastTime = timestamp;

    this.updatePlayer(dt);
    this.updateAnimals(dt);
    this.updateShopNPCs(dt);
    this.updateDemonBugs(dt);
    this.updateWorldMonsters(dt);
    this.updateBoss(dt);
    this.updateHiredGardeners(dt);
    this.updateHiredHunters(dt);
    this.updateProjectiles(dt);
    this.updateTime(dt);

    if (this.meleeSlashAnim) {
        this.meleeSlashAnim.timer -= dt;
        if (this.meleeSlashAnim.timer <= 0) {
            this.meleeSlashAnim = null;
        }
    }

    this.render();

    requestAnimationFrame((t) => this.gameLoop(t));
};

window.addEventListener('DOMContentLoaded', () => {
    Game.init();
});

