/* ========================================================
   🌾 ฟาร์มสุขใจ (Happy Farm 2D) - Stardew Valley Style
   Game Data & Configuration
   ======================================================== */

const CROPS = {
    wheat: { id: 'wheat', name: 'ข้าวสาลี', seedName: 'เมล็ดข้าวสาลี', buyPrice: 10, sellPrice: 20, growDays: 2, xp: 4, levelReq: 1, category: 'grain' },
    carrot: { id: 'carrot', name: 'แครอท', seedName: 'เมล็ดแครอท', buyPrice: 15, sellPrice: 32, growDays: 2, xp: 6, levelReq: 1, category: 'vegetable' },
    corn: { id: 'corn', name: 'ข้าวโพด', seedName: 'เมล็ดข้าวโพด', buyPrice: 20, sellPrice: 45, growDays: 3, xp: 8, levelReq: 2, category: 'grain' },
    tomato: { id: 'tomato', name: 'มะเขือเทศ', seedName: 'เมล็ดมะเขือเทศ', buyPrice: 25, sellPrice: 55, growDays: 3, xp: 10, levelReq: 2, category: 'vegetable' },
    strawberry: { id: 'strawberry', name: 'สตรอเบอร์รี่', seedName: 'เมล็ดสตรอเบอร์รี่', buyPrice: 35, sellPrice: 80, growDays: 4, xp: 14, levelReq: 3, category: 'fruit' },
    pumpkin: { id: 'pumpkin', name: 'ฟักทอง', seedName: 'เมล็ดฟักทอง', buyPrice: 40, sellPrice: 95, growDays: 4, xp: 16, levelReq: 4, category: 'vegetable' },
    sunflower: { id: 'sunflower', name: 'ทานตะวัน', seedName: 'เมล็ดทานตะวัน', buyPrice: 30, sellPrice: 70, growDays: 3, xp: 12, levelReq: 3, category: 'flower' },
    rice: { id: 'rice', name: 'ข้าวเปลือก', seedName: 'เมล็ดข้าว', buyPrice: 12, sellPrice: 25, growDays: 2, xp: 5, levelReq: 2, category: 'grain' },
    cabbage: { id: 'cabbage', name: 'กะหล่ำปลี', seedName: 'เมล็ดกะหล่ำ', buyPrice: 22, sellPrice: 48, growDays: 3, xp: 9, levelReq: 3, category: 'vegetable' },
    chili: { id: 'chili', name: 'พริก', seedName: 'เมล็ดพริก', buyPrice: 28, sellPrice: 62, growDays: 3, xp: 11, levelReq: 4, category: 'vegetable' },
    sugarcane: { id: 'sugarcane', name: 'อ้อย', seedName: 'ท่อนอ้อย', buyPrice: 18, sellPrice: 40, growDays: 3, xp: 8, levelReq: 3, category: 'grain' }
};

const ANIMALS = {
    chicken: { id: 'chicken', name: 'ไก่', buyPrice: 150, product: 'egg', productName: 'ไข่ไก่', productPrice: 25, xp: 6, levelReq: 1, feedType: 'corn' },
    cow: { id: 'cow', name: 'วัวนม', buyPrice: 350, product: 'milk', productName: 'นมวัวสด', productPrice: 50, xp: 12, levelReq: 2, feedType: 'wheat' },
    sheep: { id: 'sheep', name: 'แกะ', buyPrice: 450, product: 'wool', productName: 'ขนแกะ', productPrice: 75, xp: 16, levelReq: 3, feedType: 'wheat' },
    pig: { id: 'pig', name: 'หมู', buyPrice: 500, product: 'truffle', productName: 'เห็ดทรัฟเฟิลดำ', productPrice: 120, xp: 20, levelReq: 4, feedType: 'carrot' }
};

const RECIPES = {
    flour: { id: 'flour', name: 'แป้งทำขนม', category: 'mill', ingredients: { wheat: 2 }, sellPrice: 35, xp: 8, levelReq: 1 },
    bread: { id: 'bread', name: 'ขนมปังอบสด', category: 'bakery', ingredients: { flour: 2 }, sellPrice: 85, energyRestore: 40, xp: 15, levelReq: 2 },
    butter: { id: 'butter', name: 'เนยสด', category: 'dairy', ingredients: { milk: 2 }, sellPrice: 75, xp: 12, levelReq: 2 },
    cheese: { id: 'cheese', name: 'ชีสแท้', category: 'dairy', ingredients: { milk: 3 }, sellPrice: 120, energyRestore: 50, xp: 20, levelReq: 3 },
    cake: { id: 'cake', name: 'เค้กสตรอเบอร์รี่', category: 'bakery', ingredients: { flour: 2, egg: 2, milk: 1, strawberry: 2 }, sellPrice: 320, energyRestore: 90, xp: 45, levelReq: 4 },
    cookie: { id: 'cookie', name: 'คุกกี้เนย', category: 'bakery', ingredients: { flour: 1, butter: 1, egg: 1 }, sellPrice: 140, energyRestore: 35, xp: 18, levelReq: 3 },
    pizza: { id: 'pizza', name: 'พิซซ่าถาดใหญ่', category: 'kitchen', ingredients: { flour: 2, tomato: 2, cheese: 1 }, sellPrice: 360, energyRestore: 100, xp: 50, levelReq: 5 },
    demon_elixir: { id: 'demon_elixir', name: 'น้ำยาบำรุงพลังปีศาจ', category: 'kitchen', ingredients: { beetle_shell: 1, demon_wing: 1, strawberry: 1 }, sellPrice: 280, energyRestore: 85, xp: 35, levelReq: 2 }
};

const TOOLS = [
    { id: 'hoe', name: 'จอบดายหญ้า', desc: 'ใช้พรวนดินเพื่อเตรียมแปลงปลูก (กด Space / คลิก)', energyCost: 2 },
    { id: 'water', name: 'บัวรดน้ำ', desc: 'รดน้ำแปลงดินที่พรวนแล้ว (เติมน้ำได้ที่บ่อน้ำ)', energyCost: 1 },
    { id: 'scythe', name: 'เคียว / มือเปล่า', desc: 'เก็บเกี่ยวผลผลิตที่สุกแล้ว หรือโต้ตอบสัตว์', energyCost: 1 }
];

const UPGRADES = {
    watering_can_pro: { id: 'watering_can_pro', name: 'บัวรดน้ำทองแดง', price: 300, desc: 'บรรจุน้ำได้มากขึ้น 2 เท่า และรดได้กว้างขึ้น', levelReq: 2 },
    backpack_1: { id: 'backpack_1', name: 'กระเป๋าเป้หนัง (+12 ช่อง)', price: 400, desc: 'เพิ่มความจุช่องเก็บของ', levelReq: 2 },
    coop_expansion: { id: 'coop_expansion', name: 'ขยายโรงเลี้ยงสัตว์ (+4 ตัว)', price: 600, desc: 'เลี้ยงสัตว์ในฟาร์มได้เพิ่มขึ้น', levelReq: 3 },
    auto_sprinkler: { id: 'auto_sprinkler', name: 'สปริงเกอร์รดน้ำ', price: 800, desc: 'รดน้ำอัตโนมัติทุกเช้า 4 ช่องรอบตัว', levelReq: 4 }
};

const LEVEL_XP = [
    0,     // Lv 0
    0,     // Lv 1
    120,   // Lv 2
    300,   // Lv 3
    600,   // Lv 4
    1000,  // Lv 5
    1600,  // Lv 6
    2400,  // Lv 7
    3500,  // Lv 8
    5000   // Lv 9
];

const SEASONS = ['ฤดูใบไม้ผลิ', 'ฤดูร้อน', 'ฤดูใบไม้ร่วง', 'ฤดูหนาว'];
const DAYS_PER_SEASON = 28;

// ===== อัพเกรดตกแต่งบ้าน & เฟอร์นิเจอร์ให้บัฟพลังงาน =====
const HOUSE_DECOR_UPGRADES = {
    bed_deluxe: {
        id: 'bed_deluxe',
        name: 'เตียงขนนกหรูหรา (Deluxe Bed)',
        price: 500,
        desc: 'เตียงคิงไซส์ เพิ่ม Max Energy ถาวร +30 (สูงสุด 130) และฟื้นฟูเต็ม 100% ทุกเช้า',
        effectType: 'maxEnergy',
        value: 30
    },
    fireplace: {
        id: 'fireplace',
        name: 'เตาผิงหินโบราณ (Stone Fireplace)',
        price: 600,
        desc: 'เตาผิงก่อหินให้ความอบอุ่นทั่วบ้าน ลดการเสียพลังงานในการทำงานลง 20%',
        effectType: 'energySave',
        value: 0.2
    },
    refrigerator: {
        id: 'refrigerator',
        name: 'ตู้เย็นถนอมอาหาร (Modern Fridge)',
        price: 450,
        desc: 'ตู้เย็นสีพาสเทล อาหารที่รับประทานฟื้นพลังงานเพิ่มขึ้น +50%',
        effectType: 'foodBoost',
        value: 0.5
    },
    tea_table: {
        id: 'tea_table',
        name: 'ชุดโต๊ะน้ำชาไม้สัก (Oak Tea Table)',
        price: 350,
        desc: 'โต๊ะกลมพร้อมกาน้ำชา ฟื้นฟูพลังงานอัตโนมัติ 1 หน่วยทุก 10 วินาทีเมื่ออยู่ในบ้าน',
        effectType: 'homeRegen',
        value: 1
    },
    persian_rug: {
        id: 'persian_rug',
        name: 'พรมทอมือเปอร์เซีย (Royal Rug)',
        price: 300,
        desc: 'พรมหรูหรากลางห้อง เพิ่มความเร็วเดินในบ้าน +30% และเพิ่มค่า XP จากการทำฟาร์มทั้งหมด +15%',
        effectType: 'xpBoost',
        value: 0.15
    }
};

// ===== ตัวเลือกแต่งชุดตัวละคร =====
const OUTFIT_OPTIONS = {
    hats: [
        { id: 'straw', name: 'หมวกฟางชาวสวน' },
        { id: 'cowboy', name: 'หมวกคาวบอยหนัง' },
        { id: 'chef', name: 'หมวกเชฟกุ๊ก' },
        { id: 'flower', name: 'มงกุฎดอกไม้ป่า' },
        { id: 'cap', name: 'หมวกแก๊ปสีแดง' },
        { id: 'none', name: 'ไม่สวมหมวก' }
    ],
    shirts: [
        { id: '#3b82f6', name: 'ฟ้าคลาสสิก' },
        { id: '#dc2626', name: 'แดงสดใส' },
        { id: '#16a34a', name: 'เขียวธรรมชาติ' },
        { id: '#1e293b', name: 'ดำพรีเมียม' },
        { id: '#ec4899', name: 'ชมพูหวาน' },
        { id: '#f59e0b', name: 'เหลืองทอง' },
        { id: '#8b5cf6', name: 'ม่วงลาเวนเดอร์' }
    ],
    overalls: [
        { id: '#1e3a8a', name: 'ยีนส์น้ำเงิน' },
        { id: '#78350f', name: 'น้ำตาลคลาสสิก' },
        { id: '#1e293b', name: 'ดำสุภาพ' },
        { id: '#3f6212', name: 'เขียวมะกอก' }
    ],
    hairs: [
        { id: '#78350f', name: 'น้ำตาลธรรมชาติ' },
        { id: '#1e293b', name: 'ดำสนิท' },
        { id: '#eab308', name: 'บลอนด์ทอง' },
        { id: '#dc2626', name: 'แดงส้มสดใส' },
        { id: '#94a3b8', name: 'สีเงินประกาย' }
    ]
};

// ===== ลูกค้า NPC ประจำร้าน =====
const NPC_CUSTOMERS = [
    { id: 'uncle', name: 'คุณลุงทอง', desc: 'ชอบซื้อข้าวสาลีและผักสด', type: 'uncle' },
    { id: 'auntie', name: 'คุณป้าแก้ว', desc: 'ชอบซื้อผลไม้ ไข่ไก่ และนมสด', type: 'auntie' },
    { id: 'girl', name: 'น้องมะลิ', desc: 'ชอบซื้อสตรอเบอร์รี่ ขนมปัง และชีส', type: 'girl' },
    { id: 'chef', name: 'เชฟมิกซ์', desc: 'ชอบซื้อวัตถุดิบทำอาหารคุณภาพสูง', type: 'chef' }
];

// ===== 🐛 ฝูงแมลงปีศาจทำลายฟาร์ม (Demon Bugs & Pests) =====
const DEMON_BUGS = {
    shadow_beetle: {
        id: 'shadow_beetle',
        name: 'ด้วงปีศาจทมิฬ',
        desc: 'คลานเข้ามากัดกินแปลงผัก มีกระดองแข็งแกร่ง',
        hp: 60,
        speed: 1.1,
        damage: 10,
        attackCooldown: 1200,
        targetType: 'crop',
        loot: { gold: 20, item: 'beetle_shell', name: 'กระดองด้วงปีศาจ', xp: 18 }
    },
    demon_hornet: {
        id: 'demon_hornet',
        name: 'ต่อปีศาจเหล็กในพิษ',
        desc: 'บินฉวัดเฉวียนรวดเร็ว มุ่งเข้ามารังแกสัตว์เลี้ยงในคอก',
        hp: 40,
        speed: 1.8,
        damage: 8,
        attackCooldown: 900,
        targetType: 'animal',
        loot: { gold: 25, item: 'demon_wing', name: 'ปีกต่อปีศาจ', xp: 22 }
    },
    poison_larva: {
        id: 'poison_larva',
        name: 'หนอนพิษดูดกลืนพืช',
        desc: 'หนอนปีศาจตัวอ้วน พ่นกรดพิษกัดกร่อนแปลงผัก',
        hp: 85,
        speed: 0.8,
        damage: 15,
        attackCooldown: 1600,
        targetType: 'crop',
        loot: { gold: 35, item: 'monster_essence', name: 'น้ำมันปีศาจ', xp: 28 }
    }
};

// ===== 🏹 อาวุธสำหรับต่อสู้ (Weapons) =====
const WEAPONS = {
    slingshot: {
        id: 'slingshot',
        name: 'หนังสติ๊กล่าสัตว์ (Hunter Slingshot)',
        desc: 'ยิงลูกหิน เล็งด้วยเมาส์ ยิงด้วยคลิกซ้ายหรือ Space',
        type: 'ranged',
        damage: 30,
        speed: 8.5,
        range: 350,
        cooldown: 280,
        bulletType: 'stone'
    },
    rifle: {
        id: 'rifle',
        name: 'ปืนล่าสัตว์โบราณ (Hunting Rifle)',
        desc: 'ปืนไรเฟิลล่าสัตว์ พลังยิงทะลวงสูงและระยะยิงไกลมาก',
        type: 'ranged',
        damage: 75,
        speed: 14.0,
        range: 520,
        cooldown: 550,
        bulletType: 'rifle'
    },
    iron_sword: {
        id: 'iron_sword',
        name: 'ดาบเหล็กกล้านักผจญภัย (Iron Sword)',
        desc: 'ดาบฟันระยะประชิด ฟันศัตรูด้านหน้าเป็นวงกว้าง (คลิกซ้าย / Space)',
        type: 'melee',
        damage: 55,
        speed: 0,
        range: 65,
        cooldown: 250
    },
    excalibur_sword: {
        id: 'excalibur_sword',
        name: 'ดาบศักดิ์สิทธิ์เอ็กซ์คาลิเบอร์ (Holy Excalibur)',
        desc: 'ดาบในตำนาน ฟันคลื่นแสงศักดิ์สิทธิ์ทะลวง พลังทำลายล้างมหาศาล!',
        type: 'melee_beam',
        damage: 135,
        speed: 12.0,
        range: 480,
        cooldown: 340,
        bulletType: 'holy_beam'
    },
    dragon_rifle: {
        id: 'dragon_rifle',
        name: 'ปืนมังกรเพลิง (Dragonfire Cannon)',
        desc: 'ยิงระเบิดเพลิงมังกร ระเบิดล้างผลาญกลุ่มศัตรู',
        type: 'ranged',
        damage: 160,
        speed: 13.0,
        range: 550,
        cooldown: 580,
        bulletType: 'dragon_fire'
    }
};

// ===== 🤠 นายพรานดูแลฟาร์ม (Hired Farm Hunters) =====
const HUNTERS = {
    scout_hunter: {
        id: 'scout_hunter',
        name: 'นายพรานป่า (Woodland Scout)',
        price: 350,
        salary: 0,
        desc: 'เดินลาดตระเวนรอบแปลงผัก คอยเล็งยิงหนังสติ๊กใส่แมลงปีศาจในระยะ 7 ช่อง',
        damage: 28,
        range: 220,
        attackSpeed: 800,
        patrolArea: 'crops', // Patrols crop field
        spriteType: 'scout_hunter'
    },
    veteran_marksman: {
        id: 'veteran_marksman',
        name: 'นายพรานปืนยาว (Veteran Marksman)',
        price: 700,
        salary: 0,
        desc: 'พรานรุ่นใหญ่ถือปืนยาว ส่องยิงแมลงปีศาจรอบคอกสัตว์และรั้วฟาร์มอย่างแม่นยำ',
        damage: 65,
        range: 340,
        attackSpeed: 1100,
        patrolArea: 'animals', // Patrols animal pasture
        spriteType: 'veteran_marksman'
    }
};

// ===== 🧑‍🌾 ผู้ช่วยดูแลฟาร์ม & คนดูแลสวน (Hired Farmhands & Gardeners) =====
const FARM_HELPERS = {
    gardener_joy: {
        id: 'gardener_joy',
        name: 'ป้าแจ่ม คนดูแลสวน (Garden Caretaker)',
        price: 250,
        desc: 'เดินรดน้ำแปลงดินที่แห้ง และช่วยเก็บเกี่ยวผลผลิตที่สุกแล้วเข้ากระเป๋าให้คุณอัตโนมัติ',
        role: 'gardener',
        spriteType: 'gardener_joy',
        speed: 1.4,
        actionCooldown: 1200
    },
    farmer_boy: {
        id: 'farmer_boy',
        name: 'น้องกล้า ผู้ช่วยเก็บเกี่ยว (Master Harvester)',
        price: 450,
        desc: 'ผู้ช่วยเก็บเกี่ยวความเร็วสูง เดินเก็บผลผลิตทันทีที่สุก และช่วยเติมน้ำใส่บัวให้เต็มตลอดเวลา',
        role: 'harvester',
        spriteType: 'farmer_boy',
        speed: 1.8,
        actionCooldown: 800
    }
};

const MONSTER_DROPS = {
    beetle_shell: { id: 'beetle_shell', name: 'กระดองด้วงปีศาจ', sellPrice: 45, desc: 'กระดองแข็งสีม่วง ใช้ปรุงยาหรือส่งขาย' },
    demon_wing: { id: 'demon_wing', name: 'ปีกต่อปีศาจ', sellPrice: 55, desc: 'ปีกแมลงสะท้อนแสงสีเลือด นำไปปรุงยาบำรุงพลัง' },
    monster_essence: { id: 'monster_essence', name: 'น้ำมันปีศาจ', sellPrice: 70, desc: 'ของเหลวเรืองแสงสีเขียวเข้มข้น' }
};

// ===== 🌲 วัตถุดิบและไอเทมในโลกผจญภัย (World Items & Materials) =====
const WORLD_ITEMS = {
    shadow_pelt: { id: 'shadow_pelt', name: 'หนังหมาป่าเงา', sellPrice: 50, desc: 'ขนสัตว์สีดำเงา สำหรับตัดเย็บชุดเกราะ' },
    wolf_fang: { id: 'wolf_fang', name: 'เขี้ยวหมาป่าอาถรรพ์', sellPrice: 60, desc: 'เขี้ยวแหลมคม สำหรับตีดาบและอาวุธ' },
    iron_ore: { id: 'iron_ore', name: 'แร่เหล็กดิบ', sellPrice: 35, desc: 'แร่เหล็กบริสุทธิ์ สำหรับหลอมอาวุธที่เตาตีเหล็ก' },
    ruby_gem: { id: 'ruby_gem', name: 'อัญมณีทับทิมเวทมนตร์', sellPrice: 120, desc: 'ทับทิมเปล่งแสงสีเลือด บรรจุพลังเวทโบราณ' },
    cursed_wood: { id: 'cursed_wood', name: 'ไม้โบราณต้องสาป', sellPrice: 65, desc: 'กิ่งไม้จากต้นไม้ปีศาจ มีพลังวิญญาณสถิต' },
    mana_gem: { id: 'mana_gem', name: 'ผลึกมานาสีคราม', sellPrice: 95, desc: 'ผลึกแก้วสีฟ้าเรืองแสง ใช้สร้างอุปกรณ์ขั้นสูง' },
    starflower_herb: { id: 'starflower_herb', name: 'สมุนไพรดวงดาว', sellPrice: 40, desc: 'ดอกไม้สมุนไพรเรืองแสง นำไปต้มเป็นยาฟื้นพลังชีวิต' },
    health_potion: { id: 'health_potion', name: 'ยาฟื้นพลังชีวิตชั้นเลิศ', sellPrice: 80, energyRestore: 30, hpRestore: 60, desc: 'ดื่มเพื่อฟื้นฟู HP +60 และพลังงาน +30' },
    demon_heart: { id: 'demon_heart', name: 'หัวใจจอมอสูรคาธูรอส', sellPrice: 1000, desc: 'หัวใจที่ยังเต้นของราชาปีศาจ วัตถุดิบสร้างอาวุธระดับตำนาน' },
    crown_of_despair: { id: 'crown_of_despair', name: 'มงกุฎแห่งความสิ้นหวัง', sellPrice: 1200, desc: 'มงกุฎทองคำโบราณ หลักฐานแห่งการปราบราชาปีศาจ' }
};

// ===== 🐺 มอนสเตอร์ในป่าลึก (World Monsters) =====
const WORLD_MONSTERS = {
    shadow_wolf: {
        id: 'shadow_wolf',
        name: 'หมาป่าเงา (Shadow Wolf)',
        hp: 90,
        maxHp: 90,
        speed: 1.6,
        damage: 12,
        attackCooldown: 900,
        aggroDist: 180,
        drops: [{ item: 'shadow_pelt', chance: 0.8 }, { item: 'wolf_fang', chance: 0.6 }],
        gold: 35,
        xp: 25
    },
    goblin_scout: {
        id: 'goblin_scout',
        name: 'ก็อบลินโจรไพร (Goblin Scout)',
        hp: 75,
        maxHp: 75,
        speed: 1.3,
        damage: 10,
        attackCooldown: 1100,
        aggroDist: 210,
        drops: [{ item: 'iron_ore', chance: 0.75 }, { item: 'starflower_herb', chance: 0.4 }],
        gold: 40,
        xp: 30
    },
    demon_treant: {
        id: 'demon_treant',
        name: 'ต้นไม้ปีศาจกินคน (Demon Treant)',
        hp: 190,
        maxHp: 190,
        speed: 0.7,
        damage: 22,
        attackCooldown: 1400,
        aggroDist: 150,
        drops: [{ item: 'cursed_wood', chance: 0.9 }, { item: 'mana_gem', chance: 0.6 }],
        gold: 65,
        xp: 50
    }
};

// ===== 👑 จอมอสูรราชาปีศาจ คาธูรอส (Archdemon Kathuros) =====
const BOSS_KATHUROS = {
    id: 'boss_kathuros',
    name: 'จอมอสูรราชาปีศาจ คาธูรอส',
    title: 'เจ้านรกแห่งวิหารโบราณ (Archdemon Kathuros)',
    hp: 1200,
    maxHp: 1200,
    speed: 1.0,
    damage: 26,
    attackCooldown: 1200,
    aggroDist: 340,
    gold: 1500,
    xp: 800,
    drops: [
        { item: 'demon_heart', chance: 1.0, count: 1 },
        { item: 'crown_of_despair', chance: 1.0, count: 1 },
        { item: 'ruby_gem', chance: 1.0, count: 3 }
    ]
};

// ===== 📜 เควสต์เนื้อเรื่อง (Story Quests) =====
const QUESTS = {
    q1: {
        id: 'q1',
        title: 'การตื่นขึ้นของเงามืด (Shadows Awaken)',
        desc: 'เดินทางออกจากรั้วฟาร์มทางทิศเหนือ ข้ามสะพานเข้าสู่ป่าโบราณเพื่อพบกับ อัศวินสาว วาเลเรีย ที่แคมป์นักผจญภัย',
        targetType: 'talk',
        targetNpc: 'valeria',
        rewardDesc: '150 G, ยาฟื้นพลัง x3, ดาบเหล็กกล้า',
        goldReward: 150,
        xpReward: 50,
        itemsReward: [
            { id: 'health_potion', count: 3, name: 'ยาฟื้นพลังชีวิต' },
            { id: 'iron_sword', count: 1, name: 'ดาบเหล็กกล้า' }
        ]
    },
    q2: {
        id: 'q2',
        title: 'กวาดล้างพงไพร & รวบรวมแร่ (Purge the Woods)',
        desc: 'ปราบหมาป่าเงา 3 ตัวในป่าทึบ และขุดแร่ทับทิมเวทมนตร์ 2 ชิ้นกลับมาให้ช่างตีเหล็ก คาเอล',
        targetType: 'hunt_mine',
        reqWolves: 3,
        reqRubies: 2,
        rewardDesc: '350 G, ปืนล่าสัตว์โบราณ, 120 XP',
        goldReward: 350,
        xpReward: 120,
        itemsReward: [
            { id: 'rifle', count: 1, name: 'ปืนล่าสัตว์โบราณ' }
        ]
    },
    q3: {
        id: 'q3',
        title: 'พิชิตจอมอสูรราชาปีศาจ คาธูรอส (Slay Archdemon Kathuros)',
        desc: 'บุกเข้าสู่ลานบูชาวิหารต้องสาปทางทิศเหนือสุด สังหาร จอมอสูรราชาปีศาจ คาธูรอส เพื่อคืนความสงบสุขให้ผืนแผ่นดิน!',
        targetType: 'boss',
        targetBoss: 'boss_kathuros',
        rewardDesc: '1,500 G, ดาบศักดิ์สิทธิ์เอ็กซ์คาลิเบอร์, ฉายาวีรบุรุษผู้กอบกู้แผ่นดิน',
        goldReward: 1500,
        xpReward: 800,
        itemsReward: [
            { id: 'excalibur_sword', count: 1, name: 'ดาบศักดิ์สิทธิ์เอ็กซ์คาลิเบอร์' }
        ]
    }
};

// ===== 🗣️ บทสนทนา NPC เนื้อเรื่อง (Story NPCs) =====
const NPC_STORY = {
    valeria: {
        id: 'valeria',
        name: 'อัศวินสาว วาเลเรีย',
        role: 'ผู้พิทักษ์แนวหน้าแห่งอาณาจักร',
        portraitType: 'valeria',
        dialogues: {
            intro: 'ยินดีที่ได้พบท่านชาวสวน! ข้าสัมผัสได้ถึงพลังบริสุทธิ์จากฟาร์มของท่าน... แต่บัดนี้ ผืนป่าทางเหนือกำลังถูกเงามืดของ "จอมอสูรคาธูรอส" กลืนกิน! ข้าต้องการสหายร่วมรบเพื่อผนึกมันอีกครั้ง!',
            q1_complete: 'ขอบคุณที่ท่านกล้าก้าวออกจากรั้วฟาร์มมาช่วยพวกเรา! รับดาบเล่มนี้และยาฟื้นพลังไปเตรียมตัวเถิด!',
            in_progress: 'จงระวังตัวด้วย ในป่ามืดมีฝูงหมาป่าเงาและก็อบลินดักซุ่มอยู่ หากบาดเจ็บให้รีบดื่มยาฟื้นพลังนะ!',
            victory: 'ท่านทำสำเร็จแล้ว! ข้าแทบไม่เชื่อสายตา... จอมอสูรคาธูรอสพ่ายแพ้ต่อท่าน! นามของท่านจะถูกจารึกไว้ในฐานะ "วีรบุรุษผู้กอบกู้แผ่นดิน" ตลอดกาล!'
        }
    },
    eldrin: {
        id: 'eldrin',
        name: 'ผู้เฒ่าปราชญ์ เอลดริน',
        role: 'นักปราชญ์เวทมนตร์แห่งพงไพร',
        portraitType: 'eldrin',
        dialogues: {
            intro: 'โฮ่โฮ่... พืชผลในฟาร์มของเจ้าเติบโตงดงามยิ่งนัก แต่จงรู้ไว้เถิด ใต้ผืนดินวิหารทางเหนือนั้น มีหัวใจจอมอสูรหลับใหลอยู่ เมื่อมันตื่นขึ้น ท้องฟ้าจะกลายเป็นสีเลือด!',
            lore: 'จอมอสูรคาธูรอสแพ้พลังศักดิ์สิทธิ์และแร่ทับทิมโบราณ จงนำแร่และผลึกมานาไปให้ช่างตีเหล็กคาเอลสร้างอาวุธระดับตำนานเสียก่อนจะเข้าไปเผชิญหน้ากับมัน!',
            victory: 'ม่านหมอกสีเลือดสลายไปแล้ว... แผ่นดินได้รับความบริสุทธิ์คืนมาด้วยพลังใจอันกล้าแกร่งของเจ้า!'
        }
    },
    kael: {
        id: 'kael',
        name: 'ช่างตีเหล็ก คาเอล',
        role: 'ยอดช่างตีเหล็กและสรรพาวุธ',
        portraitType: 'kael',
        dialogues: {
            intro: 'ยินดีต้อนรับสู่เตาหลอมของข้า! นำแร่เหล็ก เขี้ยวสัตว์ และผลึกปีศาจที่เจ้าล่าได้มาให้ข้าสิ ข้าจะตีสุดยอดอาวุธให้เจ้าเอง!',
            forge_ready: 'ต้องการให้ข้าตีอาวุธหรือชุดเกราะชิ้นไหนล่ะ? วัตถุดิบพร้อมหรือยัง?'
        }
    }
};

// ===== 🔨 โรงตีเหล็กอัพเกรดอาวุธ (Blacksmith Forge Recipes) =====
const FORGE_RECIPES = {
    iron_sword: {
        id: 'iron_sword',
        name: 'ดาบเหล็กกล้านักผจญภัย',
        desc: 'ดาบเหล็กฟันระยะประชิด พลังโจมตี 55',
        cost: 150,
        materials: { iron_ore: 2, wolf_fang: 1 }
    },
    rifle: {
        id: 'rifle',
        name: 'ปืนล่าสัตว์โบราณ',
        desc: 'ปืนไรเฟิลยิงระยะไกล พลังโจมตี 75',
        cost: 350,
        materials: { iron_ore: 4, cursed_wood: 2 }
    },
    excalibur_sword: {
        id: 'excalibur_sword',
        name: 'ดาบศักดิ์สิทธิ์เอ็กซ์คาลิเบอร์',
        desc: 'ดาบศักดิ์สิทธิ์ ฟันคลื่นแสงทะลวงศัตรู พลังโจมตี 135!',
        cost: 800,
        materials: { demon_heart: 1, ruby_gem: 2, mana_gem: 2 }
    },
    dragon_rifle: {
        id: 'dragon_rifle',
        name: 'ปืนมังกรเพลิง (Dragonfire Cannon)',
        desc: 'ปืนมังกรยิงระเบิดเพลิง พลังโจมตี 160!',
        cost: 950,
        materials: { demon_heart: 1, cursed_wood: 3, ruby_gem: 2 }
    },
    health_potion: {
        id: 'health_potion',
        name: 'ยาฟื้นพลังชีวิตชั้นเลิศ',
        desc: 'ฟื้นฟู HP +60 และพลังงาน +30',
        cost: 40,
        materials: { starflower_herb: 2 }
    }
};
