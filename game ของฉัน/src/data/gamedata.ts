/* ========================================================
   ฟาร์มสุขใจ (Happy Farm 2D) - Stardew Valley Style
   Game Data & Configuration (Typed TypeScript Module)
   ======================================================== */

import {
  CropData,
  AnimalData,
  RecipeData,
  ToolData,
  UpgradeData,
  DemonBugData,
  WeaponData,
  HunterData,
  FarmHelperData,
  MaterialItem,
  WorldMonsterData,
  BossData,
  QuestData,
  StoryNPCData,
  ForgeRecipe,
  NPCCustomerData,
  FishData,
  BountyData
} from '../types';

export const CROPS: Record<string, CropData> = {
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
  sugarcane: { id: 'sugarcane', name: 'อ้อย', seedName: 'ท่อนอ้อย', buyPrice: 18, sellPrice: 40, growDays: 3, xp: 8, levelReq: 3, category: 'grain' },
  pineapple: { id: 'pineapple', name: 'สับปะรดทองคำ', seedName: 'หน่อสับปะรด', buyPrice: 50, sellPrice: 135, growDays: 4, xp: 22, levelReq: 3, category: 'fruit' },
  coconut: { id: 'coconut', name: 'มะพร้าวน้ำหอม', seedName: 'ลูกมะพร้าวเพาะชำ', buyPrice: 60, sellPrice: 150, growDays: 4, xp: 25, levelReq: 3, category: 'fruit' },
  banana: { id: 'banana', name: 'กล้วยหอมทอง (Golden Banana)', seedName: 'หน่อกล้วยทอง', buyPrice: 55, sellPrice: 140, growDays: 3, xp: 20, levelReq: 3, category: 'fruit' },
  golden_melon: { id: 'golden_melon', name: 'เมลอนทองคำเกาะโจรสลัด', seedName: 'เมล็ดเมลอนทองคำ', buyPrice: 120, sellPrice: 420, growDays: 5, xp: 45, levelReq: 4, category: 'fruit' },
  starfruit: { id: 'starfruit', name: 'ผลไม้ดวงดาวแคริบเบียน', seedName: 'เมล็ดผลไม้ดาว', buyPrice: 150, sellPrice: 550, growDays: 6, xp: 60, levelReq: 5, category: 'fruit' },
  cosmic_fruit: { id: 'cosmic_fruit', name: 'ผลไม้ดวงดาวจักรวาล', seedName: 'เมล็ดพันธุ์ดาราจักร', buyPrice: 400, sellPrice: 1500, growDays: 3, xp: 85, levelReq: 3, category: 'fruit' }
};

export const ANIMALS: Record<string, AnimalData> = {
  chicken: { id: 'chicken', name: 'ไก่', buyPrice: 150, product: 'egg', productName: 'ไข่ไก่', productPrice: 25, xp: 6, levelReq: 1, feedType: 'corn' },
  cow: { id: 'cow', name: 'วัวนม', buyPrice: 350, product: 'milk', productName: 'นมวัวสด', productPrice: 50, xp: 12, levelReq: 2, feedType: 'wheat' },
  sheep: { id: 'sheep', name: 'แกะ', buyPrice: 450, product: 'wool', productName: 'ขนแกะ', productPrice: 75, xp: 16, levelReq: 3, feedType: 'wheat' },
  pig: { id: 'pig', name: 'หมู', buyPrice: 500, product: 'truffle', productName: 'เห็ดทรัฟเฟิลดำ', productPrice: 120, xp: 20, levelReq: 4, feedType: 'carrot' }
};

export const RECIPES: Record<string, RecipeData> = {
  flour: { id: 'flour', name: 'แป้งทำขนม', category: 'mill', ingredients: { wheat: 2 }, sellPrice: 35, xp: 8, levelReq: 1 },
  bread: { id: 'bread', name: 'ขนมปังอบสด', category: 'bakery', ingredients: { flour: 2 }, sellPrice: 85, energyRestore: 40, xp: 15, levelReq: 2 },
  butter: { id: 'butter', name: 'เนยสด', category: 'dairy', ingredients: { milk: 2 }, sellPrice: 75, xp: 12, levelReq: 2 },
  cheese: { id: 'cheese', name: 'ชีสแท้', category: 'dairy', ingredients: { milk: 3 }, sellPrice: 120, energyRestore: 50, xp: 20, levelReq: 3 },
  cake: { id: 'cake', name: 'เค้กสตรอเบอร์รี่', category: 'bakery', ingredients: { flour: 2, egg: 2, milk: 1, strawberry: 2 }, sellPrice: 320, energyRestore: 90, xp: 45, levelReq: 4 },
  cookie: { id: 'cookie', name: 'คุกกี้เนย', category: 'bakery', ingredients: { flour: 1, butter: 1, egg: 1 }, sellPrice: 140, energyRestore: 35, xp: 18, levelReq: 3 },
  pizza: { id: 'pizza', name: 'พิซซ่าถาดใหญ่', category: 'kitchen', ingredients: { flour: 2, tomato: 2, cheese: 1 }, sellPrice: 360, energyRestore: 100, xp: 50, levelReq: 5 },
  demon_elixir: { id: 'demon_elixir', name: 'น้ำยาบำรุงพลังปีศาจ', category: 'kitchen', ingredients: { beetle_shell: 1, demon_wing: 1, strawberry: 1 }, sellPrice: 280, energyRestore: 85, xp: 35, levelReq: 2 },
  antidote_serum: { id: 'antidote_serum', name: 'เซรุ่มต้านสปอร์พิษ', category: 'kitchen', ingredients: { blight_spore: 2, starflower_herb: 1 }, sellPrice: 160, energyRestore: 50, xp: 30, levelReq: 1 },
  grilled_fish: { id: 'grilled_fish', name: 'ปลาย่างเนยสด', category: 'kitchen', ingredients: { tilapia: 1, butter: 1 }, sellPrice: 160, energyRestore: 65, xp: 22, levelReq: 2 },
  spicy_fish_soup: { id: 'spicy_fish_soup', name: 'ต้มยำปลารสเด็ด', category: 'kitchen', ingredients: { catfish: 1, chili: 2, tomato: 1 }, sellPrice: 240, energyRestore: 95, xp: 35, levelReq: 3 },
  farmer_stew: { id: 'farmer_stew', name: 'สตูว์เนื้อผักรวมพลังใจชาวสวน', category: 'kitchen', ingredients: { potato: 2, carrot: 2, aged_cheese: 1 }, sellPrice: 280, energyRestore: 120, xp: 45, levelReq: 3 },
  vigor_juice: { id: 'vigor_juice', name: 'น้ำผลไม้วิเศษสายลมว่องไว', category: 'kitchen', ingredients: { strawberry: 2, frost_berry: 1, craft_ale: 1 }, sellPrice: 250, energyRestore: 100, xp: 40, levelReq: 3 },
  herbal_defense_soup: { id: 'herbal_defense_soup', name: 'ซุปสมุนไพรเกราะพฤกษาคุ้มภัย', category: 'kitchen', ingredients: { starflower_herb: 2, swamp_herb: 2, milk: 1 }, sellPrice: 320, energyRestore: 100, xp: 50, levelReq: 4 },
  parry_master_broth: { id: 'parry_master_broth', name: 'ซุปสมาธิอัศวิน (Parry Master Broth)', category: 'kitchen', ingredients: { carrot: 3, tilapia: 1, milk: 1 }, sellPrice: 380, energyRestore: 120, xp: 55, levelReq: 3 },
  ironhide_dragon_steak: { id: 'ironhide_dragon_steak', name: 'สเต๊กเกราะศิลา (Ironhide Steak)', category: 'kitchen', ingredients: { potato: 3, aged_cheese: 1, butter: 1 }, sellPrice: 420, energyRestore: 140, xp: 60, levelReq: 4 },
  stamina_surge_pie: { id: 'stamina_surge_pie', name: 'พายวายุคลั่ง (Stamina Surge Pie)', category: 'kitchen', ingredients: { flour: 2, strawberry: 2, egg: 2 }, sellPrice: 390, energyRestore: 110, xp: 50, levelReq: 3 },
  sacred_purification_tea: { id: 'sacred_purification_tea', name: 'ชาเทวะชำระมลทิน (Purification Tea)', category: 'kitchen', ingredients: { starflower_herb: 2, star_fruit: 1, milk: 1 }, sellPrice: 460, energyRestore: 150, xp: 65, levelReq: 4 },
  crab_cakes: { id: 'crab_cakes', name: 'ทอดมันปูยักษ์เกาะสมบัติ (Crab Cakes)', category: 'kitchen', ingredients: { crab_meat: 2, flour: 1, egg: 1 }, sellPrice: 380, energyRestore: 130, xp: 50, levelReq: 3 },
  tropical_smoothie: { id: 'tropical_smoothie', name: 'สมูทตี้ผลไม้รวมเขตร้อน (Tropical Smoothie)', category: 'kitchen', ingredients: { pineapple: 1, banana: 1, coconut: 1 }, sellPrice: 340, energyRestore: 120, xp: 45, levelReq: 3 },
  titan_elixir: { id: 'titan_elixir', name: 'น้ำยาเทวะสยบศึก (Titan Elixir)', category: 'kitchen', ingredients: { strawberry: 2, blight_spore: 2, aged_cheese: 1 }, sellPrice: 480, energyRestore: 150, xp: 75, levelReq: 4 },
  swiftfoot_tonic: { id: 'swiftfoot_tonic', name: 'ยาบำรุงสายลมคลั่ง (Swiftfoot Tonic)', category: 'kitchen', ingredients: { pineapple: 2, banana: 2, craft_ale: 1 }, sellPrice: 420, energyRestore: 130, xp: 60, levelReq: 3 },
  ironbark_brew: { id: 'ironbark_brew', name: 'โอสถปราการศิลา (Ironbark Brew)', category: 'kitchen', ingredients: { potato: 3, swamp_herb: 2, beetle_shell: 1 }, sellPrice: 450, energyRestore: 140, xp: 70, levelReq: 4 },

  // สิ่งประดิษฐ์งานช่าง & กล่องเก็บของ & อัปเกรดกระเป๋า
  chest: { id: 'chest', name: 'กล่องเก็บของไม้ (Storage Chest)', category: 'carpentry', ingredients: { wood: 20 }, sellPrice: 50, xp: 15, levelReq: 1 },
  axe: { id: 'axe', name: 'ขวานตัดไม้ (Woodcutter Axe)', category: 'carpentry', ingredients: { wood: 10, iron_ore: 1 }, sellPrice: 80, xp: 20, levelReq: 1 },
  backpack_upgrade_1: { id: 'backpack_upgrade_1', name: 'กระเป๋าเป้นักเดินทาง (+12 ช่อง -> รวม 48 ช่อง)', category: 'carpentry', ingredients: { wood: 20 }, sellPrice: 0, xp: 35, levelReq: 1 },
  backpack_upgrade_2: { id: 'backpack_upgrade_2', name: 'กระเป๋าเป้จอมผจญภัย (+12 ช่อง -> รวม 60 ช่อง)', category: 'carpentry', ingredients: { wood: 40, iron_ore: 2 }, sellPrice: 0, xp: 60, levelReq: 2 },

  // ระบบฟาร์มอัตโนมัติ (Automated Sprinklers)
  sprinkler_basic: { id: 'sprinkler_basic', name: 'สปริงเกอร์รดน้ำพื้นฐาน (รด 4 ช่องติดกัน)', category: 'carpentry', ingredients: { copper_ore: 4, iron_ore: 1 }, sellPrice: 120, xp: 25, levelReq: 1 },
  sprinkler_quality: { id: 'sprinkler_quality', name: 'สปริงเกอร์รดน้ำคุณภาพสูง (รด 8 ช่อง 3x3)', category: 'carpentry', ingredients: { iron_ore: 4, gold_ore: 2 }, sellPrice: 280, xp: 50, levelReq: 2 },

  // เครื่องแปรรูปผลผลิต (Artisan Processing Machines)
  mayo_machine: { id: 'mayo_machine', name: 'เครื่องทำมายองเนส (Mayonnaise Machine)', category: 'carpentry', ingredients: { wood: 15, stone: 10, copper_ore: 2 }, sellPrice: 150, xp: 30, levelReq: 1 },
  cheese_press: { id: 'cheese_press', name: 'เครื่องอัดชีสแท้ (Cheese Press)', category: 'carpentry', ingredients: { wood: 20, stone: 15 }, sellPrice: 160, xp: 30, levelReq: 1 },
  preserves_jar: { id: 'preserves_jar', name: 'ถังหมักแยม & ผักดอง (Preserves Jar)', category: 'carpentry', ingredients: { wood: 25, stone: 15, iron_ore: 2 }, sellPrice: 220, xp: 35, levelReq: 2 },
  wine_keg: { id: 'wine_keg', name: 'ถังบ่มไวน์และเอลโบราณ (Wine & Ale Keg)', category: 'carpentry', ingredients: { wood: 35, iron_ore: 3, copper_ore: 2 }, sellPrice: 320, xp: 50, levelReq: 3 },

  // ม้าพาหนะ & สัตว์เลี้ยงคู่ใจ (Mount & Pets)
  horse_whistle: { id: 'horse_whistle', name: 'นกหวีดเรียกม้าคู่ใจ (ขี่ม้าวิ่งเร็ว +65%)', category: 'carpentry', ingredients: { wood: 10, iron_ore: 2, ruby_gem: 1 }, sellPrice: 0, xp: 60, levelReq: 1 },
  pet_basket: { id: 'pet_basket', name: 'เบาะสัตว์เลี้ยงคู่หู (รับเลี้ยงน้องหมา/แมว)', category: 'carpentry', ingredients: { wood: 15, wool: 2 }, sellPrice: 0, xp: 40, levelReq: 1 },

  // สิ่งปลูกสร้างและตกแต่งฟาร์ม (Farm Building & Decor)
  wood_fence: { id: 'wood_fence', name: 'รั้วไม้กั้นคอก (Wood Fence x4)', category: 'carpentry', ingredients: { wood: 5 }, sellPrice: 20, xp: 8, levelReq: 1 },
  stone_fence: { id: 'stone_fence', name: 'รั้วหินแกรนิต (Stone Fence x4)', category: 'carpentry', ingredients: { stone: 5 }, sellPrice: 32, xp: 10, levelReq: 1 },
  stone_path: { id: 'stone_path', name: 'ทางเดินหินปูพื้น (Cobblestone Path x4 - วิ่งเร็ว +15%)', category: 'carpentry', ingredients: { stone: 4 }, sellPrice: 16, xp: 6, levelReq: 1 },
  wood_path: { id: 'wood_path', name: 'ทางเดินไม้กระดาน (Plank Path x4 - วิ่งเร็ว +10%)', category: 'carpentry', ingredients: { wood: 4 }, sellPrice: 12, xp: 5, levelReq: 1 },
  farm_lantern: { id: 'farm_lantern', name: 'โคมไฟเสาไม้โบราณ (Farm Lantern)', category: 'carpentry', ingredients: { wood: 10, iron_ore: 1, copper_ore: 1 }, sellPrice: 40, xp: 15, levelReq: 1 },
  windmill_kit: { id: 'windmill_kit', name: 'ชุดสร้างกังหันลม (Windmill Kit - บดแป้ง/น้ำตาลเร็ว x2)', category: 'carpentry', ingredients: { wood: 40, stone: 30, iron_ore: 4 }, sellPrice: 500, xp: 80, levelReq: 2 },
  silo_kit: { id: 'silo_kit', name: 'ชุดสร้างไซโลเก็บเสบียง (Silo Kit - ให้อาหารสัตว์อัตโนมัติ)', category: 'carpentry', ingredients: { stone: 50, iron_ore: 4, copper_ore: 4 }, sellPrice: 600, xp: 90, levelReq: 2 },
  fish_tank: { id: 'fish_tank', name: 'ตู้จัดแสดงปลาในบ้าน (Fish Tank)', category: 'carpentry', ingredients: { stone: 25, iron_ore: 3, mana_gem: 1 }, sellPrice: 300, xp: 50, levelReq: 2 }
};

export const TOOLS: ToolData[] = [
  { id: 'hoe', name: 'จอบดายหญ้า', desc: 'ใช้พรวนดินเพื่อเตรียมแปลงปลูก (กด Space / คลิก)', energyCost: 2 },
  { id: 'water', name: 'บัวรดน้ำ', desc: 'รดน้ำแปลงดินที่พรวนแล้ว (เติมน้ำได้ที่บ่อน้ำ)', energyCost: 1 },
  { id: 'scythe', name: 'เคียว / มือเปล่า', desc: 'เก็บเกี่ยวผลผลิตที่สุกแล้ว หรือโต้ตอบสัตว์', energyCost: 1 },
  { id: 'axe', name: 'ขวานตัดไม้', desc: 'ใช้ตัดต้นไม้เพื่อเก็บท่อนไม้และผลโอ๊ค (กด Space / คลิก ที่ต้นไม้)', energyCost: 2 },
  { id: 'fishing_rod', name: 'คันเบ็ดไม้ไผ่', desc: 'เหวี่ยงเบ็ดริมน้ำเพื่อจับปลา (กด Space / คลิก เมื่อหันหน้าเข้าน้ำ)', energyCost: 2 }
];

export const FISH: Record<string, FishData> = {
  carp: { id: 'carp', name: 'ปลาคาร์ปหางยาว', sellPrice: 40, xp: 8, difficulty: 1, desc: 'ปลาเกล็ดทองประกาย พบได้ทั่วไปในบ่อน้ำฟาร์ม', habitat: 'pond' },
  tilapia: { id: 'tilapia', name: 'ปลานิลแม่น้ำ', sellPrice: 55, xp: 12, difficulty: 2, desc: 'ปลานิลตัวอ้วน เนื้อแน่นหวาน นิยมนำไปย่าง', habitat: 'any' },
  catfish: { id: 'catfish', name: 'ปลาดุกยักษ์', sellPrice: 80, xp: 18, difficulty: 3, desc: 'ปลาดุกหนวดยาว ว่ายน้ำเร็วและดิ้นแรงมาก', habitat: 'pond' },
  golden_salmon: { id: 'golden_salmon', name: 'ปลาแซลมอนสีทอง', sellPrice: 150, xp: 30, difficulty: 4, desc: 'ปลาหายาก ว่ายทวนน้ำในลำธารป่าลึก', habitat: 'river' },
  ancient_glowfish: { id: 'ancient_glowfish', name: 'ปลาเรืองแสงโบราณ', sellPrice: 320, xp: 60, difficulty: 5, desc: 'ปลาในตำนานที่เรืองแสงสีฟ้าคราม นำโชคลาภมาสู่ผู้ครอบครอง', habitat: 'river' },
  clownfish: { id: 'clownfish', name: 'ปลาการ์ตูนนีโม่', sellPrice: 85, xp: 16, difficulty: 2, desc: 'ปลาทะเลเขตร้อนลายส้มสลับขาว ว่ายตามแนวปะการังเกาะ', habitat: 'ocean' },
  lionfish: { id: 'lionfish', name: 'ปลาสิงโตครีบเพลิง', sellPrice: 135, xp: 26, difficulty: 3, desc: 'ปลาทะเลครีบหนามแหลมคม ลวดลายงดงามดั่งเปลวไฟ', habitat: 'ocean' },
  manta_ray: { id: 'manta_ray', name: 'ปลากระเบนราหูยักษ์', sellPrice: 260, xp: 50, difficulty: 4, desc: 'กระเบนทะเลลึกตัวมหึมา ร่อนใต้เกลียวคลื่นอย่างสง่างาม', habitat: 'ocean' },
  hammerhead_shark: { id: 'hammerhead_shark', name: 'ฉลามหัวค้อนเกาะสมบัติ', sellPrice: 700, xp: 130, difficulty: 5, desc: 'ราชันแห่งท้องทะเลเขตร้อน ฉลามในตำนานที่เฝ้าซากเรืออับปางโจรสลัด', habitat: 'ocean' }
};

export const UPGRADES: Record<string, UpgradeData> = {
  watering_can_pro: { id: 'watering_can_pro', name: 'บัวรดน้ำทองแดง', price: 300, desc: 'บรรจุน้ำได้มากขึ้น 2 เท่า และรดได้กว้างขึ้น', levelReq: 2 },
  backpack_1: { id: 'backpack_1', name: 'กระเป๋าเป้หนัง (+12 ช่อง)', price: 400, desc: 'เพิ่มความจุช่องเก็บของ', levelReq: 2 },
  coop_expansion: { id: 'coop_expansion', name: 'ขยายโรงเลี้ยงสัตว์ (+4 ตัว)', price: 600, desc: 'เลี้ยงสัตว์ในฟาร์มได้เพิ่มขึ้น', levelReq: 3 },
  auto_sprinkler: { id: 'auto_sprinkler', name: 'สปริงเกอร์รดน้ำ', price: 800, desc: 'รดน้ำอัตโนมัติทุกเช้า 4 ช่องรอบตัว', levelReq: 4 }
};

export const LEVEL_XP: number[] = [
  0, 0, 120, 300, 600, 1000, 1600, 2400, 3500, 5000
];

export const SEASONS = ['ฤดูใบไม้ผลิ', 'ฤดูร้อน', 'ฤดูใบไม้ร่วง', 'ฤดูหนาว'];
export const DAYS_PER_SEASON = 28;

export const HOUSE_DECOR_UPGRADES: Record<string, UpgradeData> = {
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

export const OUTFIT_OPTIONS = {
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

export const NPC_CUSTOMERS: NPCCustomerData[] = [
  { id: 'uncle', name: 'คุณลุงทอง', desc: 'ชอบซื้อข้าวสาลีและผักสด', type: 'uncle' },
  { id: 'auntie', name: 'คุณป้าแก้ว', desc: 'ชอบซื้อผลไม้ ไข่ไก่ และนมสด', type: 'auntie' },
  { id: 'girl', name: 'น้องมะลิ', desc: 'ชอบซื้อสตรอเบอร์รี่ ขนมปัง และชีส', type: 'girl' },
  { id: 'chef', name: 'เชฟมิกซ์', desc: 'ชอบซื้อวัตถุดิบทำอาหารคุณภาพสูง', type: 'chef' }
];

export const DEMON_BUGS: Record<string, DemonBugData> = {
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

export const WEAPONS: Record<string, WeaponData> = {
  slingshot: {
    id: 'slingshot',
    name: 'หนังสติ๊กล่าสัตว์ (Hunter Slingshot)',
    desc: 'ยิงลูกหิน เล็งเป้าหมายอัตโนมัติ ยิงด้วยคลิกซ้าย ปุ่ม A หรือแตะหน้าจอ',
    type: 'ranged',
    damage: 24,
    speed: 12.0,
    range: 680,
    cooldown: 280,
    bulletType: 'stone'
  },
  rifle: {
    id: 'rifle',
    name: 'ปืนล่าสัตว์โบราณ (Hunting Rifle)',
    desc: 'ปืนไรเฟิลล่าสัตว์ พลังยิงทะลวงสูงและระยะยิงไกลมาก',
    type: 'ranged',
    damage: 52,
    speed: 14.0,
    range: 720,
    cooldown: 520,
    bulletType: 'rifle'
  },
  iron_sword: {
    id: 'iron_sword',
    name: 'ดาบเหล็กกล้านักผจญภัย (Iron Sword)',
    desc: 'ดาบฟันระยะประชิด ฟันศัตรูด้านหน้าเป็นวงกว้าง (คลิกซ้าย / Space / ปุ่ม A)',
    type: 'melee',
    damage: 32,
    speed: 0,
    range: 88,
    cooldown: 300
  },
  excalibur_sword: {
    id: 'excalibur_sword',
    name: 'ดาบศักดิ์สิทธิ์เอ็กซ์คาลิเบอร์ (Holy Excalibur)',
    desc: 'ดาบในตำนาน ฟันคลื่นแสงศักดิ์สิทธิ์ทะลวง พลังโจมตี 52',
    type: 'melee_beam',
    damage: 52,
    speed: 12.0,
    range: 480,
    cooldown: 350,
    bulletType: 'holy_beam'
  },
  dragon_rifle: {
    id: 'dragon_rifle',
    name: 'ปืนมังกรเพลิง (Dragonfire Cannon)',
    desc: 'ยิงระเบิดเพลิงมังกร ระเบิดล้างผลาญกลุ่มศัตรู พลังโจมตี 62',
    type: 'ranged',
    damage: 62,
    speed: 12.0,
    range: 520,
    cooldown: 520,
    bulletType: 'dragon_fire'
  },
  luminarch_crystal_blade: {
    id: 'luminarch_crystal_blade',
    name: 'ดาบเลเซอร์ผลึกปริซึมลูมินาร์ค (Prismatic Laser Blade)',
    desc: 'ดาบผลึกโบราณ ฟันปลดปล่อยลำแสงเลเซอร์ปริซึมทะลวง พลังโจมตี 60',
    type: 'melee_beam',
    damage: 60,
    speed: 13.0,
    range: 480,
    cooldown: 340,
    bulletType: 'crystal_shard'
  },
  hydra_venom_bow: {
    id: 'hydra_venom_bow',
    name: 'คันธนูสามศรพิษพญาไฮดรา (Hydra Venom Bow)',
    desc: 'คันธนูมังกรบึงพิษ แผลงศรกรดพิษกระจาย 3 ดอกพร้อมกัน (24x3 DMG)',
    type: 'ranged',
    damage: 24,
    speed: 12.0,
    range: 450,
    cooldown: 480,
    bulletType: 'poison_glob'
  },
  volcano_sword: {
    id: 'volcano_sword',
    name: 'ดาบเพลิงลาวาภูเขาไฟ (Volcano Magma Blade)',
    desc: 'ดาบเพลิงหลอมจากแก่นภูเขาไฟ ฟันคลื่นเพลิงลาวา พลังโจมตี 68',
    type: 'melee_beam',
    damage: 68,
    speed: 12.0,
    range: 480,
    cooldown: 340,
    bulletType: 'dragon_fire'
  },
  volcano_magma_axe: {
    id: 'volcano_magma_axe',
    name: 'ขวานเพลิงโลกันตร์ลาวาอิกนิสทรอน (Molten Magma Axe)',
    desc: 'ขวานหินลาวาคู่ ระเบิดคลื่นเพลิงล้างผลาญกลุ่มศัตรู พลังโจมตี 82',
    type: 'melee_beam',
    damage: 82,
    speed: 11.0,
    range: 460,
    cooldown: 400,
    bulletType: 'dragon_fire'
  },
  glacial_titan_hammer: {
    id: 'glacial_titan_hammer',
    name: 'ค้อนเหมันต์ไททันน้ำแข็งฟรอสต์แฟงก์ (Glacial Titan Hammer)',
    desc: 'ค้อนน้ำแข็งพันปี ทุบพื้นสร้างคลื่นหอกน้ำแข็งแช่แข็งศัตรู พลังโจมตี 88',
    type: 'melee_beam',
    damage: 88,
    speed: 11.5,
    range: 480,
    cooldown: 440,
    bulletType: 'ice_shard'
  },
  malakor_soul_scythe: {
    id: 'malakor_soul_scythe',
    name: 'เคียวมรณะสูบวิญญาณลอร์ดมาลาคอร์ (Malakor Soul Scythe)',
    desc: 'เคียวแห่งความตาย ปล่อยคลื่นกะโหลกวิญญาณมืด และดูดเลือด 6% คืนแก่ผู้ใช้ พลังโจมตี 92',
    type: 'melee_beam',
    damage: 92,
    speed: 12.5,
    range: 500,
    cooldown: 360,
    bulletType: 'shadow_skull'
  },
  sylvan_bow: {
    id: 'sylvan_bow',
    name: 'คันธนูใบไม้พฤกษาพันปี (Ancient Sylvan Bow)',
    desc: 'คันธนูแห่งเทพพฤกษา แผลงศรใบไม้คมกริบ 4 ดอกรูปพัด ทะลวงศัตรู (28x4 DMG)',
    type: 'ranged',
    damage: 28,
    speed: 13.0,
    range: 550,
    cooldown: 420,
    bulletType: 'petal_blade'
  },
  tempest_blade: {
    id: 'tempest_blade',
    name: 'ดาบอัสนีบาตคลื่นสายฟ้า (Tempest Lightning Blade)',
    desc: 'สุดยอดดาบสายฟ้าแห่งจ้าวพายุ ปลดปล่อยคลื่นลำแสงสายฟ้าผ่าทะลวงศัตรู พลังโจมตี 105',
    type: 'melee_beam',
    damage: 105,
    speed: 14.0,
    range: 560,
    cooldown: 350,
    bulletType: 'lightning_beam'
  },
  spire_blade: {
    id: 'spire_blade',
    name: 'ดาบสุริยันผลึกหอคอย (Spire Solar Blade)',
    desc: 'ดาบในตำนานแห่งหอคอยผลึก ฟันคลื่นสุริยันทะลวงศัตรู พลังโจมตี 95',
    type: 'melee_beam',
    damage: 95,
    speed: 13.0,
    range: 520,
    cooldown: 340,
    bulletType: 'holy_beam'
  },
  spire_bow: {
    id: 'spire_bow',
    name: 'ธนูประกายดาราผลึก (Spire Star Bow)',
    desc: 'คันธนูมิติ แผลงศรแสงดารา 3 ดอก (34x3 DMG)',
    type: 'ranged',
    damage: 34,
    speed: 13.5,
    range: 540,
    cooldown: 380,
    bulletType: 'crystal_shard'
  },
  spire_staff: {
    id: 'spire_staff',
    name: 'คทาแก่นหอคอยมิติ (Spire Nebula Staff)',
    desc: 'คทามหาเวท ปลดปล่อยลูกพลังเนบิวลาระเบิดกว้าง พลังโจมตี 110',
    type: 'ranged',
    damage: 110,
    speed: 11.0,
    range: 500,
    cooldown: 420,
    bulletType: 'dragon_fire'
  },
  cutlass_saber: {
    id: 'cutlass_saber',
    name: 'ดาบโจรสลัดคัตลาสอาถรรพ์ (Corsair Cutlass)',
    desc: 'ดาบโค้งเหล็กกล้าแห่งแคริบเบียน ฟันคลื่นจันทร์เสี้ยววารี พลังโจมตี 100 ติดคริติคอล 35%!',
    type: 'melee_beam',
    damage: 100,
    speed: 13.5,
    range: 500,
    cooldown: 320,
    bulletType: 'crystal_shard'
  },
  volcano_flame_sword: {
    id: 'volcano_flame_sword',
    name: 'ดาบเพลิงสุริยันอัคนี (Solar Magma Blade)',
    desc: 'ดาบเพลิงศักดิ์สิทธิ์ใจกลางปล่องภูเขาไฟ ฟันคลื่นลูกไฟลาวาระเบิด พลังโจมตี 135 คริติคอล 35%!',
    type: 'melee_beam',
    damage: 135,
    speed: 13.5,
    range: 520,
    cooldown: 280,
    bulletType: 'dragon_fire'
  }
};

export const HUNTERS: Record<string, HunterData> = {
  scout_hunter: {
    id: 'scout_hunter',
    name: 'นายพรานป่า (Woodland Scout)',
    price: 350,
    salary: 0,
    desc: 'เดินลาดตระเวนรอบแปลงผัก คอยเล็งยิงหนังสติ๊กใส่แมลงปีศาจในระยะ 7 ช่อง',
    damage: 28,
    range: 220,
    attackSpeed: 800,
    patrolArea: 'crops',
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
    patrolArea: 'animals',
    spriteType: 'veteran_marksman'
  }
};

export const FARM_HELPERS: Record<string, FarmHelperData> = {
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

export const MONSTER_DROPS: Record<string, MaterialItem> = {
  beetle_shell: { id: 'beetle_shell', name: 'กระดองด้วงปีศาจ', sellPrice: 45, desc: 'กระดองแข็งสีม่วง ใช้ปรุงยาหรือส่งขาย' },
  demon_wing: { id: 'demon_wing', name: 'ปีกต่อปีศาจ', sellPrice: 55, desc: 'ปีกแมลงสะท้อนแสงสีเลือด นำไปปรุงยาบำรุงพลัง' },
  monster_essence: { id: 'monster_essence', name: 'น้ำมันปีศาจ', sellPrice: 70, desc: 'ของเหลวเรืองแสงสีเขียวเข้มข้น' }
};

export const WORLD_ITEMS: Record<string, MaterialItem> = {
  shadow_pelt: { id: 'shadow_pelt', name: 'หนังหมาป่าเงา', sellPrice: 50, desc: 'ขนสัตว์สีดำเงา สำหรับตัดเย็บชุดเกราะ' },
  wolf_fang: { id: 'wolf_fang', name: 'เขี้ยวหมาป่าอาถรรพ์', sellPrice: 60, desc: 'เขี้ยวแหลมคม สำหรับตีดาบและอาวุธ' },
  iron_ore: { id: 'iron_ore', name: 'แร่เหล็กดิบ', sellPrice: 35, desc: 'แร่เหล็กบริสุทธิ์ สำหรับหลอมอาวุธที่เตาตีเหล็ก' },
  ruby_gem: { id: 'ruby_gem', name: 'อัญมณีทับทิมเวทมนตร์', sellPrice: 120, desc: 'ทับทิมเปล่งแสงสีเลือด บรรจุพลังเวทโบราณ' },
  cursed_wood: { id: 'cursed_wood', name: 'ไม้โบราณต้องสาป', sellPrice: 65, desc: 'กิ่งไม้จากต้นไม้ปีศาจ มีพลังวิญญาณสถิต' },
  mana_gem: { id: 'mana_gem', name: 'ผลึกมานาสีคราม', sellPrice: 95, desc: 'ผลึกแก้วสีฟ้าเรืองแสง ใช้สร้างอุปกรณ์ขั้นสูง' },
  starflower_herb: { id: 'starflower_herb', name: 'สมุนไพรดวงดาว', sellPrice: 40, desc: 'ดอกไม้สมุนไพรเรืองแสง นำไปต้มเป็นยาฟื้นพลังชีวิต' },
  blight_spore: { id: 'blight_spore', name: 'สปอร์กลายพันธุ์ (Blight Spore)', sellPrice: 65, desc: 'สปอร์สีม่วงแดงเรืองแสงที่ตกจากแมลงกลายพันธุ์ ใช้ศึกษาและปรุงเซรุ่มแก้พิษ' },
  antidote_serum: { id: 'antidote_serum', name: 'เซรุ่มต้านสปอร์พิษ (Antidote Serum)', sellPrice: 160, energyRestore: 50, hpRestore: 80, desc: 'เซรุ่มสูตรพิเศษของหมอยาลิเลียน ดื่มฟื้นฟู HP +80 และ พลังงาน +50 พร้อมชำระล้างพิษสปอร์' },
  health_potion: { id: 'health_potion', name: 'ยาฟื้นพลังชีวิตชั้นเลิศ', sellPrice: 80, energyRestore: 30, hpRestore: 60, desc: 'ดื่มเพื่อฟื้นฟู HP +60 และพลังงาน +30' },
  gold_ore: { id: 'gold_ore', name: 'แร่ทองคำดิบ', sellPrice: 70, desc: 'แร่ทองคำประกายระยิบระยับ ขุดได้จากถ้ำลึก' },
  diamond_crystal: { id: 'diamond_crystal', name: 'เพชรคริสตัลโบราณ', sellPrice: 260, desc: 'อัญมณีล้ำค่าและแข็งแกร่งที่สุดในถ้ำ' },
  bat_wing: { id: 'bat_wing', name: 'ปีกค้างคาวถ้ำ', sellPrice: 40, desc: 'ปีกค้างคาว ใช้ปรุงยาหรือขายเป็นเงิน' },
  crystal_core: { id: 'crystal_core', name: 'แก่นคริสตัลสไลม์', sellPrice: 65, desc: 'แก่นผลึกเวทมนตร์เรืองแสง' },
  demon_heart: { id: 'demon_heart', name: 'หัวใจจอมอสูรคาธูรอส', sellPrice: 1000, desc: 'หัวใจที่ยังเต้นของราชาปีศาจ วัตถุดิบสร้างอาวุธระดับตำนาน' },
  crown_of_despair: { id: 'crown_of_despair', name: 'มงกุฎแห่งความสิ้นหวัง', sellPrice: 1200, desc: 'มงกุฎทองคำโบราณ หลักฐานแห่งการปราบราชาปีศาจ' },
  cinder_shard: { id: 'cinder_shard', name: 'เศษผลึกเพลิง (Cinder Shard)', sellPrice: 200, desc: 'ผลึกหินลาวาคุกรุ่นจากถ้ำภูเขาไฟ ใช้สลักรูนไฟและหลอมอาวุธเพลิง' },
  dragon_tooth: { id: 'dragon_tooth', name: 'เขี้ยวมังกรโบราณ (Dragon Tooth)', sellPrice: 450, desc: 'เขี้ยวมังกรเพลิงโบราณที่แข็งแกร่งดั่งเหล็กกล้า วัตถุดิบสร้างดาบเพลิงลาวา' },
  volcano_sword: { id: 'volcano_sword', name: 'ดาบเพลิงลาวาภูเขาไฟ (Volcano Magma Blade)', sellPrice: 2400, desc: 'ดาบเพลิงหลอมจากแก่นภูเขาไฟ ฟันคลื่นเพลิงลาวาลุกท่วม พลังโจมตี 180!' },
  wood: { id: 'wood', name: 'ท่อนไม้', sellPrice: 8, desc: 'ท่อนไม้เนื้อแข็ง ได้จากการตัดต้นไม้ ใช้สร้างกล่องและสิ่งประดิษฐ์' },
  chest: { id: 'chest', name: 'กล่องเก็บของไม้', sellPrice: 50, desc: 'นำไปวางบนพื้นดินเพื่อเปิดเก็บของได้ 16 ช่อง' },
  axe: { id: 'axe', name: 'ขวานตัดไม้', sellPrice: 80, desc: 'ใช้ตัดต้นไม้เพื่อเก็บท่อนไม้' },
  sapling: { id: 'sapling', name: 'ต้นกล้าไม้โอ๊ค', sellPrice: 15, desc: 'นำไปปลูกลงบนพื้นเพื่อปลูกต้นไม้ใหม่' },
  backpack_upgrade_1: { id: 'backpack_upgrade_1', name: 'กระเป๋าเป้นักเดินทาง (+12 ช่อง)', sellPrice: 0, desc: 'ขยายกระเป๋าเป้เป็น 48 ช่องทันที จุของได้จุใจ' },
  backpack_upgrade_2: { id: 'backpack_upgrade_2', name: 'กระเป๋าเป้จอมผจญภัย (+12 ช่อง)', sellPrice: 0, desc: 'ขยายกระเป๋าเป้เป็น 60 ช่องทันที จุของได้จุใจ' },

  // Deep Mine Minerals
  stone: { id: 'stone', name: 'ก้อนหินเนื้อแน่น', sellPrice: 4, desc: 'หินธรรมชาติจากการขุดเหมือง ใช้ก่อสร้างและประดิษฐ์เครื่องจักร' },
  copper_ore: { id: 'copper_ore', name: 'แร่ทองแดงบริสุทธิ์', sellPrice: 20, desc: 'แร่โลหะสีส้ม พบในเหมืองชั้นต้น ใช้สร้างสปริงเกอร์และเครื่องแปรรูป' },
  star_core: { id: 'star_core', name: 'แก่นผลึกดวงดาว', sellPrice: 500, desc: 'อัญมณีเรืองแสงล้ำค่าจากเหมืองชั้นลึกที่สุด มีพลังงานเวทมหาศาล' },
  phoenix_feather: { id: 'phoenix_feather', name: 'ขนนกฟีนิกซ์ศักดิ์สิทธิ์ (Phoenix Feather)', sellPrice: 2000, desc: 'ขนนกเรืองแสงสีทองอร่าม หากพลังชีวิตหมดลงจะชุบชีวิตฟื้นคืนชีพเต็ม 100% ทันที!' },
  void_elixir: { id: 'void_elixir', name: 'โอสถแห่งความว่างเปล่า (Void Elixir)', sellPrice: 500, energyRestore: 100, hpRestore: 100, desc: 'โอสถสีม่วงเรืองแสง ดื่มเพื่อฟื้นฟู HP/Energy เต็มเปี่ยมและวิ่งเร็วขึ้น 60 วินาที' },
  mystery_geode: { id: 'mystery_geode', name: 'หินผลึกปิดผนึกปริศนา (Mystery Geode)', sellPrice: 150, desc: 'หินเปลือกแข็งเรืองแสง นำไปกะเทาะที่โรงตีเหล็กหรือกดสำรวจเพื่อลุ้นรับอัญมณีล้ำค่า!' },
  ancient_relic: { id: 'ancient_relic', name: 'โบราณวัตถุแห่งอารยธรรมสาบสูญ', sellPrice: 850, desc: 'โบราณวัตถุแกะสลักลวดลายลึกลับ นักสะสมและนักประวัติศาสตร์ให้ราคาสูงยิ่ง' },
  star_shard: { id: 'star_shard', name: 'เศษอุกกาบาตดวงดาว (Star Shard)', sellPrice: 350, desc: 'เศษหินอุกกาบาตเรืองแสงสีฟ้าอมม่วง ปล่อยไอความร้อนจากห้วงอวกาศ' },
  cosmic_fruit_seed: { id: 'cosmic_fruit_seed', name: 'เมล็ดพันธุ์ดาราจักร (Cosmic Star Seed)', sellPrice: 200, desc: 'เมล็ดพืชเรืองแสง ปลูกได้ทุกฤดู โตเร็ว ให้ผลไม้ดวงดาวมูลค่ามหาศาล' },
  cosmic_fruit: { id: 'cosmic_fruit', name: 'ผลไม้ดวงดาวจักรวาล (Cosmic Star Fruit)', sellPrice: 1500, energyRestore: 120, hpRestore: 120, desc: 'ผลไม้สีทองอร่ามดั่งแสงดารา กลิ่นหอมฟุ้ง รับประทานฟื้นฟูพลังทั้งหมด!' },

  // Machines & Sprinklers
  sprinkler_basic: { id: 'sprinkler_basic', name: 'สปริงเกอร์รดน้ำพื้นฐาน', sellPrice: 120, desc: 'วางในฟาร์มเพื่อรดน้ำแปลงดิน 4 ช่องรอบตัวอัตโนมัติทุกเช้า' },
  sprinkler_quality: { id: 'sprinkler_quality', name: 'สปริงเกอร์รดน้ำคุณภาพสูง', sellPrice: 280, desc: 'วางในฟาร์มเพื่อรดน้ำแปลงดิน 8 ช่อง (3x3) รอบตัวอัตโนมัติทุกเช้า' },
  mayo_machine: { id: 'mayo_machine', name: 'เครื่องทำมายองเนส', sellPrice: 150, desc: 'วางบนพื้น นำไข่ไก่มาใส่เพื่อแปรรูปเป็นมายองเนสรสกลมกล่อม' },
  cheese_press: { id: 'cheese_press', name: 'เครื่องอัดชีสแท้', sellPrice: 160, desc: 'วางบนพื้น นำนมสดมาใส่เพื่อบ่มเป็นเชดดาร์ชีสชั้นเลิศ' },
  preserves_jar: { id: 'preserves_jar', name: 'ถังหมักแยม & ผักดอง', sellPrice: 220, desc: 'วางบนพื้น ใส่ผลไม้หรือผักเพื่อทำแยมหวานฉ่ำหรือผักดอง' },
  wine_keg: { id: 'wine_keg', name: 'ถังบ่มไวน์และเอลโบราณ', sellPrice: 320, desc: 'วางบนพื้น ใส่ผลไม้เพื่อบ่มไวน์ หรือใส่ข้าวสาลีเพื่อบ่มเบียร์สด' },
  horse_whistle: { id: 'horse_whistle', name: 'นกหวีดเรียกม้าคู่ใจ', sellPrice: 0, desc: 'เป่านกหวีดเพื่อขึ้นขี่ม้าพาหนะคู่ใจ วิ่งเร็วขึ้น +65% (กด [R] ได้)' },
  pet_basket: { id: 'pet_basket', name: 'เบาะสัตว์เลี้ยงแสนรัก', sellPrice: 0, desc: 'วางในบ้านหรือฟาร์มเพื่อรับเลี้ยงน้องหมาหรือน้องแมวคอยเดินตาม' },

  // ผลิตภัณฑ์แปรรูปมูลค่าสูง (Artisan Products)
  mayonnaise: { id: 'mayonnaise', name: 'มายองเนสเข้มข้น', sellPrice: 100, energyRestore: 45, desc: 'มายองเนสสดจากไข่ไก่ รสชาติเปรี้ยวหวานกลมกล่อม' },
  strawberry_jam: { id: 'strawberry_jam', name: 'แยมสตรอเบอร์รี่หวานฉ่ำ', sellPrice: 190, energyRestore: 55, desc: 'แยมผลไม้โฮมเมดเข้มข้น หอมหวานกลิ่นผลไม้สด' },
  pickled_carrot: { id: 'pickled_carrot', name: 'ผักดองแครอทกรอบ', sellPrice: 85, energyRestore: 30, desc: 'แครอทดองน้ำส้มสายชูสูตรโบราณ กรุบกรอบอร่อย' },
  fine_wine: { id: 'fine_wine', name: 'ไวน์ผลไม้ชั้นเลิศ', sellPrice: 300, energyRestore: 80, desc: 'ไวน์หมักบ่มจนได้ที่ รสชาตินุ่มละมุนลิ้น เป็นของขวัญที่ผู้ใหญ่ชื่นชอบ' },
  craft_ale: { id: 'craft_ale', name: 'เบียร์สดข้าวสาลีคราฟต์', sellPrice: 180, energyRestore: 60, desc: 'เบียร์หมักสดจากข้าวสาลีชั้นดี ฟองนุ่มกลิ่นหอม' },
  aged_cheese: { id: 'aged_cheese', name: 'เชดดาร์ชีสบ่มพิเศษ', sellPrice: 220, energyRestore: 70, desc: 'ชีสแท้บ่มด้วยเครื่องอัด รสชาติเข้มข้น หอมมันกลมกล่อม' },

  // วัตถุดิบและไอเทมระดับตำนานจากมหาบอสทั้ง 6 (Mega Boss Legendary Artifacts)
  luminarch_crystal_heart: { id: 'luminarch_crystal_heart', name: 'หัวใจผลึกปริซึมลูมินาร์ค', sellPrice: 1200, desc: 'หัวใจคริสตัลบริสุทธิ์จากโกเลมโบราณ ส่องประกายแสงรุ้ง 7 สี มีพลังงานเวทมนตร์ไร้ขีดจำกัด' },
  hydra_venom_gland: { id: 'hydra_venom_gland', name: 'ต่อมพิษพญาไฮดราโบราณ', sellPrice: 1350, desc: 'ต่อมพิษเข้มข้นสูงสุดจากพญาไฮดราแห่งบึงมืด ใช้สกัดยาแก้สารพัดพิษและชุบคมดาบ' },
  hydra_scale: { id: 'hydra_scale', name: 'เกล็ดมังกรบึงพิษ', sellPrice: 120, desc: 'เกล็ดหนาสีเขียวมรกต ทนทานต่อกรดและความร้อน' },
  magma_dragon_horn: { id: 'magma_dragon_horn', name: 'เขามังกรอัคนีเพลิงอิกนิสทรอน', sellPrice: 1600, desc: 'เขามังกรลาวาที่ยังคุกรุ่นด้วยเปลวเพลิงโลกันตร์ วัตถุดิบสร้างสุดยอดดาบเพลิง' },
  flame_heart: { id: 'flame_heart', name: 'แก่นเพลิงลาวาเดือด', sellPrice: 350, desc: 'ผลึกหินลาวาที่มีเปลวเพลิงลุกไหม้ชั่วนิรันดร์' },
  glacial_titan_core: { id: 'glacial_titan_core', name: 'แก่นเหมันต์ไททันน้ำแข็ง', sellPrice: 1400, desc: 'ผลึกน้ำแข็งพันปีที่ไม่มีวันละลาย แผ่ไอความเย็นยะเยือกฟื้นฟูจิตใจ' },
  frost_crystal: { id: 'frost_crystal', name: 'ผลึกน้ำแข็งบริสุทธิ์', sellPrice: 150, desc: 'เกล็ดน้ำแข็งรูปดาวที่สกัดได้จากยอดเขาเหมันต์' },
  death_lord_soul: { id: 'death_lord_soul', name: 'ดวงวิญญาณมรณะลอร์ดมาลาคอร์', sellPrice: 1500, desc: 'ดวงวิญญาณเรืองแสงสีม่วงทมิฬ กักเก็บพลังอำนาจแห่งความตายและความเป็นอมตะ' },
  cursed_relic: { id: 'cursed_relic', name: 'โบราณวัตถุต้องสาป', sellPrice: 280, desc: 'แผ่นศิลาจารึกอักขระโบราณของกษัตริย์ไร้นาม' },
  swamp_herb: { id: 'swamp_herb', name: 'บัวสมุนไพรหนองน้ำ', sellPrice: 60, energyRestore: 40, desc: 'ดอกบัวสมุนไพรหายาก ขึ้นในบึงพิษ ช่วยสลายพิษและเพิ่มพลังชีวิต' },
  frost_berry: { id: 'frost_berry', name: 'เบอร์รี่หิมะเยือกแข็ง', sellPrice: 75, energyRestore: 45, desc: 'ผลไม้สีฟ้าฉ่ำน้ำ เติบโตบนยอดเขาหิมะ รสชาติหวานเย็นสดชื่น' },

  // อาวุธระดับตำนานจากมหาบอสทั้ง 5 (Boss Legendary Weapons)
  luminarch_crystal_blade: { id: 'luminarch_crystal_blade', name: 'ดาบเลเซอร์ผลึกปริซึมลูมินาร์ค', sellPrice: 2000, desc: 'สุดยอดดาบคริสตัลโบราณ ฟันปล่อยลำแสงเลเซอร์ปริซึมทะลวง พลังโจมตี 195!' },
  hydra_venom_bow: { id: 'hydra_venom_bow', name: 'คันธนูสามศรพิษพญาไฮดรา', sellPrice: 2200, desc: 'คันธนูมังกรบึงพิษ แผลงศรกรดพิษกระจาย 3 ดอกพร้อมกัน พลังโจมตี 110x3!' },
  volcano_magma_axe: { id: 'volcano_magma_axe', name: 'ขวานเพลิงโลกันตร์ลาวาอิกนิสทรอน', sellPrice: 2400, desc: 'ขวานหินลาวาคู่ ระเบิดคลื่นเพลิงล้างผลาญกลุ่มศัตรู พลังโจมตี 230!' },
  glacial_titan_hammer: { id: 'glacial_titan_hammer', name: 'ค้อนเหมันต์ไททันน้ำแข็งฟรอสต์แฟงก์', sellPrice: 2500, desc: 'ค้อนน้ำแข็งพันปี ทุบพื้นสร้างคลื่นหอกน้ำแข็งแช่แข็งศัตรู พลังโจมตี 240!' },
  malakor_soul_scythe: { id: 'malakor_soul_scythe', name: 'เคียวมรณะสูบวิญญาณลอร์ดมาลาคอร์', sellPrice: 3000, desc: 'เคียวแห่งความตาย ปล่อยคลื่นกะโหลกวิญญาณมืด และดูดเลือด 8% คืนแก่ผู้ใช้ พลังโจมตี 260!' },
  sylvan_bow: { id: 'sylvan_bow', name: 'คันธนูใบไม้พฤกษาพันปี (Ancient Sylvan Bow)', sellPrice: 3200, desc: 'คันธนูแห่งเทพพฤกษา แผลงศรใบไม้คมกริบ 4 ดอกรูปพัด ทะลวงศัตรู พลังโจมตี 160x4!' },
  tempest_blade: { id: 'tempest_blade', name: 'ดาบอัสนีบาตคลื่นสายฟ้า (Tempest Lightning Blade)', sellPrice: 3600, desc: 'สุดยอดดาบสายฟ้าแห่งจ้าวพายุ ปลดปล่อยคลื่นสายฟ้าผ่าทะลวงศัตรู พลังโจมตี 320!' },

  // อาหารเสบียงรบจากผลผลิตฟาร์ม (Combat Rations & Food Buffs)
  farmer_stew: { id: 'farmer_stew', name: 'สตูว์เนื้อผักรวมพลังใจชาวสวน', sellPrice: 280, energyRestore: 120, desc: 'สตูว์ร้อนๆ รสชาติเข้มข้น เพิ่มพลังโจมตีอาวุธทุกชนิด +35 นาน 3 นาที!' },
  vigor_juice: { id: 'vigor_juice', name: 'น้ำผลไม้วิเศษสายลมว่องไว', sellPrice: 250, energyRestore: 100, desc: 'น้ำสกัดผลไม้เข้มข้น เพิ่มความเร็วในการเคลื่อนที่ +50% นาน 3 นาที!' },
  herbal_defense_soup: { id: 'herbal_defense_soup', name: 'ซุปสมุนไพรเกราะพฤกษาคุ้มภัย', sellPrice: 320, energyRestore: 100, desc: 'ซุปเคี่ยวสมุนไพรหายาก สร้างโล่พฤกษาลดความเสียหายที่ได้รับลง 40% นาน 3 นาที!' },

  // แหวนและเครื่องประดับสถิตพลัง (Equippable Power Rings & Accessories)
  ring_glow: { id: 'ring_glow', name: 'แหวนเรืองแสงสุริยัน (Sun Glow Ring)', sellPrice: 450, desc: 'แหวนทองคำสลักอำพัน ส่องรัศมีแสงสว่างรอบตัวในถ้ำมืดและสุสานใต้ดิน (+80 รัศมีแสง)' },
  ring_magnet: { id: 'ring_magnet', name: 'แหวนแม่เหล็กดูดทรัพย์ (Magneto Ring)', sellPrice: 500, desc: 'แหวนแร่เหล็กโบราณ ปล่อยคลื่นแม่เหล็กดูดไอเทมบนพื้นเข้าตัวจากระยะไกลขึ้น 3 เท่า!' },
  ring_warrior: { id: 'ring_warrior', name: 'แหวนนักรบผู้กล้า (Warrior Bravery Ring)', sellPrice: 650, desc: 'แหวนเหล็กกล้าประดับทับทิม เพิ่มโอกาสโจมตีติดคริติคอล +18% และพลังทำลายคริติคอล 2.2 เท่า' },
  ring_vampiric: { id: 'ring_vampiric', name: 'แหวนแวมไพร์สูบโลหิต (Vampiric Leech Ring)', sellPrice: 850, desc: 'แหวนโลหิตต้องสาป ฟื้นฟูพลังชีวิตผู้ใช้ 4% จากความเสียหายทุกครั้งที่ฟันโดนศัตรู' },
  ring_lucky: { id: 'ring_lucky', name: 'แหวนนำโชคจอมพราน (Fortune Hunter Ring)', sellPrice: 750, desc: 'แหวนมรกตนำโชค มอนสเตอร์ดรอปเหรียญทองเพิ่มขึ้น +35% และเพิ่มอัตราการดรอปไอเทมหายาก' },

  // รูนเวทมนตร์สลักอาวุธ (Elemental Runes)
  rune_fire: { id: 'rune_fire', name: 'รูนอัคคีพิโรธ (Fire Rune)', sellPrice: 250, desc: 'ศิลาเวทมนตร์อัคคี สลักลงอาวุธทำให้การโจมตีติดสถานะเผาไหม้ (Burn DoT)' },
  rune_frost: { id: 'rune_frost', name: 'รูนเหมันต์นิรันดร์ (Frost Rune)', sellPrice: 250, desc: 'ศิลาเวทมนตร์เหมันต์ สลักลงอาวุธทำให้ศัตรูถูกแช่แข็งสโลว์ความเร็วลง 50%' },
  rune_lightning: { id: 'rune_lightning', name: 'รูนอัสนีบาต (Lightning Rune)', sellPrice: 250, desc: 'ศิลาเวทมนตร์สายฟ้า สลักลงอาวุธทำให้เกิดประกายสายฟ้าชิ่งโดนศัตรูรอบข้าง' },
  rune_vampiric: { id: 'rune_vampiric', name: 'รูนกลืนวิญญาณ (Vampiric Rune)', sellPrice: 300, desc: 'ศิลาเวทมนตร์สูบวิญญาณ สลักลงอาวุธดูดพลังชีวิต 8% ของความเสียหายที่ทำได้' },

  // แก่นศิลาศักดิ์สิทธิ์ทั้ง 6 ธาตุ (The 6 Sacred Shards)
  sacred_shard_earth: { id: 'sacred_shard_earth', name: 'แก่นศิลาปฐพีศักดิ์สิทธิ์ (Sacred Earth Shard)', sellPrice: 1000, desc: 'แก่นแท้แห่งธาตุดิน ได้รับจากการปราบราชินีสปอร์คาธูรอส' },
  sacred_shard_sun: { id: 'sacred_shard_sun', name: 'แก่นศิลาสุริยันศักดิ์สิทธิ์ (Sacred Sun Shard)', sellPrice: 1000, desc: 'แก่นแท้แห่งแสงสว่าง ได้รับจากการปราบโกเลมลูมินาร์ค' },
  sacred_shard_water: { id: 'sacred_shard_water', name: 'แก่นศิลาวารีศักดิ์สิทธิ์ (Sacred Water Shard)', sellPrice: 1000, desc: 'แก่นแท้แห่งสายน้ำ ได้รับจากการปราบพญาไฮดราคิส' },
  sacred_shard_fire: { id: 'sacred_shard_fire', name: 'แก่นศิลาเพลิงศักดิ์สิทธิ์ (Sacred Fire Shard)', sellPrice: 1000, desc: 'แก่นแท้แห่งเพลิงโลกันตร์ ได้รับจากการปราบมังกรอิกนิสทรอน' },
  sacred_shard_frost: { id: 'sacred_shard_frost', name: 'แก่นศิลาเหมันต์ศักดิ์สิทธิ์ (Sacred Frost Shard)', sellPrice: 1000, desc: 'แก่นแท้แห่งความเย็นเยือก ได้รับจากการปราบไททันฟรอสต์แฟงก์' },
  sacred_shard_shadow: { id: 'sacred_shard_shadow', name: 'แก่นศิลาทมิฬศักดิ์สิทธิ์ (Sacred Shadow Shard)', sellPrice: 1000, desc: 'แก่นแท้แห่งมิติเงา ได้รับจากการปราบนครมรณะลอร์ดมาลาคอร์' },
  sacred_shard_nature: { id: 'sacred_shard_nature', name: 'แก่นศิลาพฤกษาศักดิ์สิทธิ์ (Sacred Nature Shard)', sellPrice: 1200, desc: 'แก่นแท้แห่งพงไพร ได้รับจากการปราบเทพพฤกษาโบราณ ซิลวาเนีย' },
  sacred_shard_thunder: { id: 'sacred_shard_thunder', name: 'แก่นศิลาอัสนีศักดิ์สิทธิ์ (Sacred Thunder Shard)', sellPrice: 1500, desc: 'แก่นแท้แห่งสายฟ้า ได้รับจากการปราบจ้าวพายุ ออสทริออน' },
  ancient_tree_heart: { id: 'ancient_tree_heart', name: 'หัวใจพฤกษาบรรพกาล', sellPrice: 1800, desc: 'หัวใจไม้ศักดิ์สิทธิ์พันปี แผ่พลังชีวิตบริสุทธิ์ของผืนป่าโบราณ' },
  storm_core: { id: 'storm_core', name: 'แก่นอัสนีบาตคำราม', sellPrice: 2000, desc: 'แก่นสายฟ้าทรงอานุภาพที่กักเก็บกระแสไฟฟ้าแรงสูงนับล้านโวลต์' },
  star_fruit: { id: 'star_fruit', name: 'ผลไม้ดวงดาราพฤกษา', sellPrice: 120, energyRestore: 60, desc: 'ผลไม้เรืองแสงสีทองรูปดาว หวานหอมฟื้นฟูพลังกายและจิตใจได้อย่างยอดเยี่ยม' },
  thunder_crystal: { id: 'thunder_crystal', name: 'ผลึกสายฟ้าอัสนีบาต', sellPrice: 180, desc: 'แร่ผลึกสีฟ้าครามที่สะสมประจุไฟฟ้าสถิตจากยอดเขาพายุ' },

  // วัตถุสิ่งปลูกสร้างตกแต่งฟาร์ม (Farm Placeable Items)
  wood_fence: { id: 'wood_fence', name: 'รั้วไม้กั้นคอก (Wood Fence)', sellPrice: 5, desc: 'รั้วไม้แปรรูป วางกั้นอาณาเขตบนฟาร์ม สัตว์และมอนสเตอร์ไม่สามารถเดินผ่านได้' },
  stone_fence: { id: 'stone_fence', name: 'รั้วหินแกรนิต (Stone Fence)', sellPrice: 8, desc: 'รั้วหินโบราณแข็งแกร่ง ใช้จัดระเบียบแปลงฟาร์มอย่างงดงาม' },
  stone_path: { id: 'stone_path', name: 'ทางเดินหินปูพื้น (Cobblestone Path)', sellPrice: 4, desc: 'ทางเดินหินธรรมชาติ ปูบนพื้นฟาร์มช่วยให้วิ่งเร็วขึ้น 15%' },
  wood_path: { id: 'wood_path', name: 'ทางเดินไม้กระดาน (Wood Plank Path)', sellPrice: 3, desc: 'ทางเดินไม้ชนบท ปูบนพื้นฟาร์มช่วยให้วิ่งเร็วขึ้น 10%' },
  farm_lantern: { id: 'farm_lantern', name: 'โคมไฟเสาไม้โบราณ (Farm Lantern)', sellPrice: 40, desc: 'โคมไฟส่องสว่าง ส่องประกายแสงอบอุ่นทั่วบริเวณในยามค่ำคืน' },
  windmill_kit: { id: 'windmill_kit', name: 'ชุดสร้างกังหันลม (Windmill Kit)', sellPrice: 500, desc: 'กังหันลมแปรรูป บดข้าวสาลีเป็นแป้งและอ้อยเป็นน้ำตาลได้อย่างรวดเร็ว' },
  silo_kit: { id: 'silo_kit', name: 'ชุดสร้างไซโลเก็บเสบียง (Silo Kit)', sellPrice: 600, desc: 'หอคอยเก็บหญ้าเลี้ยงสัตว์ ส่งอาหารให้สัตว์ในฟาร์มอัตโนมัติทุกเช้า' },
  fish_tank: { id: 'fish_tank', name: 'ตู้จัดแสดงปลา (Fish Tank)', sellPrice: 300, desc: 'ตู้ปลาแก้วสวยงาม วางในบ้านและนำปลามาใส่เพื่อชมว่ายน้ำเพลิดเพลิน' },
  spire_shard: { id: 'spire_shard', name: 'ผลึกหอคอยมิติ (Spire Shard)', sellPrice: 50, desc: 'ผลึกเรืองแสงลึกลับที่เก็บได้จากการพิชิตชั้นในหอคอยไร้จุดสิ้นสุด' },
  sugar: { id: 'sugar', name: 'น้ำตาลทรายบริสุทธิ์', sellPrice: 30, desc: 'น้ำตาลทรายขาวบริสุทธิ์ ได้จากการนำอ้อยมาบดที่กังหันลม' },

  // 6 ชุดเกราะและอุปกรณ์บอสระดับตำนาน (Boss Legendary Equipment)
  kathuros_spore_armor: { id: 'kathuros_spore_armor', name: 'เกราะสปอร์ราชันคาธูรอส (Spore Mail)', sellPrice: 2000, desc: '[ชุดเกราะบอส] พลังป้องกัน +50% เมื่อโดนโจมตีจะระเบิดหนามสปอร์สวนกลับศัตรู 45 ดาเมจ' },
  ignistron_flame_shield: { id: 'ignistron_flame_shield', name: 'โล่อัคคีพิโรธอิกนิสทรอน (Magma Shield)', sellPrice: 2200, desc: '[โล่บอส] เมื่อทำการ Perfect Parry สำเร็จ จะระเบิดคลื่นเพลิงลาวาพุ่งเผาศัตรู 110 ดาเมจ' },
  frostfang_frozen_plate: { id: 'frostfang_frozen_plate', name: 'เกราะเกล็ดหิมะฟรอสต์แฟงก์ (Glacial Plate)', sellPrice: 2200, desc: '[ชุดเกราะบอส] การยกโล่บล็อกลดความเสียหาย 80% (จากปกติ 65%) และสะท้อนไอเย็นแช่แข็งศัตรู' },
  astreon_storm_greaves: { id: 'astreon_storm_greaves', name: 'เกราะขาอัสนีบาตออสทริออน (Storm Greaves)', sellPrice: 2100, desc: '[อุปกรณ์บอส] ความเร็วเคลื่อนที่ +30% และเมื่อกลิ้งหลบ Dash จะฟาดสายฟ้าผ่าใส่ศัตรู 60 ดาเมจ' },
  malakor_void_cloak: { id: 'malakor_void_cloak', name: 'ผ้าคลุมมฤตยูลอร์ดมาลาคอร์ (Void Shroud)', sellPrice: 2500, desc: '[ชุดเกราะบอส] ขยายหน้าต่าง Perfect Parry เพิ่ม +80ms และดูดเลือด 6% จากความเสียหายที่ทำได้' },
  hydrakis_venom_pendant: { id: 'hydrakis_venom_pendant', name: 'จี้เขี้ยวพิษพญาไฮดรา (Venom Amulet)', sellPrice: 1900, desc: '[อุปกรณ์บอส] ป้องกันความเสียหายจากพิษและบึงมลทิน 100% พร้อมเคลือบพิษให้การโจมตี' },

  // 4 อาหารกูร์เมต์ปรุงรบขั้นสูง (Gourmet Combat Dishes)
  parry_master_broth: { id: 'parry_master_broth', name: 'ซุปสมาธิอัศวิน (Parry Master Broth)', sellPrice: 380, energyRestore: 120, hpRestore: 60, desc: '[อาหารบัฟรบ] ขยายหน้าต่าง Perfect Parry จาก 0.24 วิ เป็น 0.36 วิ นาน 3 นาที!' },
  ironhide_dragon_steak: { id: 'ironhide_dragon_steak', name: 'สเต๊กเกราะศิลา (Ironhide Steak)', sellPrice: 420, energyRestore: 140, hpRestore: 80, desc: '[อาหารบัฟรบ] ลดความเสียหายลงอีก 30% และป้องกันการเกิด Guard Break ได้ 1 ครั้ง' },
  stamina_surge_pie: { id: 'stamina_surge_pie', name: 'พายวายุคลั่ง (Stamina Surge Pie)', sellPrice: 390, energyRestore: 110, hpRestore: 50, desc: '[อาหารบัฟรบ] ฟื้นฟู Stamina รวดเร็วขึ้น 200% และกลิ้งหลบ Dash ได้ฟรีไม่เสียพลังงาน' },
  sacred_purification_tea: { id: 'sacred_purification_tea', name: 'ชาเทวะชำระมลทิน (Purification Tea)', sellPrice: 460, energyRestore: 150, hpRestore: 90, desc: '[อาหารบัฟรบ] ป้องกันความเสียหายจากไฟ/พิษ/สายฟ้าบนพื้น 100% และฟื้นเลือด +6 HP/วินาที' },
  titan_elixir: { id: 'titan_elixir', name: 'น้ำยาเทวะสยบศึก (Titan Elixir)', sellPrice: 480, energyRestore: 150, hpRestore: 120, desc: '[อาหารบัฟรบ] พลังโจมตี +45 ดาเมจ และเพิ่มอัตราคริติคอล +20% นาน 3 นาที!' },
  swiftfoot_tonic: { id: 'swiftfoot_tonic', name: 'ยาบำรุงสายลมคลั่ง (Swiftfoot Tonic)', sellPrice: 420, energyRestore: 130, hpRestore: 80, desc: '[อาหารบัฟรบ] ความเร็วเคลื่อนที่ +40% และกลิ้ง Dash ไม่จำกัด Stamina นาน 3 นาที!' },
  ironbark_brew: { id: 'ironbark_brew', name: 'โอสถปราการศิลา (Ironbark Brew)', sellPrice: 450, energyRestore: 140, hpRestore: 100, desc: '[อาหารบัฟรบ] ลดความเสียหายลง 35% และป้องกันการ์ดแตกได้ 2 ครั้ง นาน 3 นาที!' },

  // วัตถุดิบและสมบัติจากเกาะมหาสมบัติเขตร้อน (Tropical Island Relics & Expedition Items)
  banana: { id: 'banana', name: 'กล้วยหอมทอง (Golden Banana)', sellPrice: 140, energyRestore: 60, desc: 'กล้วยหอมทองคำสุกหวาน อุดมด้วยแร่ธาตุ ฟื้นฟู Stamina +60' },
  golden_melon: { id: 'golden_melon', name: 'เมลอนทองคำเกาะโจรสลัด', sellPrice: 420, energyRestore: 120, desc: 'ผลไม้สีทองอร่ามหวานฉ่ำ โตบนเกาะเขตร้อน ขายได้ราคาสูงถึง 420 G!' },
  starfruit: { id: 'starfruit', name: 'ผลไม้ดวงดาวแคริบเบียน', sellPrice: 550, energyRestore: 150, hpRestore: 100, desc: 'ผลไม้รูปดาวเรืองแสง รสเปรี้ยวอมหวาน ฟื้นพลังชีวิต +100 และพลังงาน +150' },
  banana_seed: { id: 'banana_seed', name: 'หน่อกล้วยทองเพาะชำ', sellPrice: 25, desc: 'หน่อพันธุ์กล้วยหอม ปลูกในดินเกาะโต 3 วัน' },
  golden_melon_seed: { id: 'golden_melon_seed', name: 'เมล็ดเมลอนทองคำเกาะโจรสลัด', sellPrice: 50, desc: 'เมล็ดพันธุ์ผลไม้ทองคำ ปลูกในแปลงเกาะโต 5 วัน' },
  starfruit_seed: { id: 'starfruit_seed', name: 'เมล็ดผลไม้ดาวแคริบเบียน', sellPrice: 70, desc: 'เมล็ดผลไม้ดวงดาว ปลูกในแปลงเกาะโต 6 วัน' },
  pirate_doubloon: { id: 'pirate_doubloon', name: 'เหรียญทองโบราณโจรสลัด (Ancient Doubloon)', sellPrice: 100, desc: 'เหรียญทองคำสลักลายหัวกะโหลก ใช้แลกไอเทมระดับสูงกับกัปตันบาร์นาบี้' },
  skeleton_key: { id: 'skeleton_key', name: 'กุญแจโครงกระดูกโจรสลัด (Skeleton Key)', sellPrice: 150, desc: 'กุญแจกระดูกอาถรรพ์ ใช้ไขเปิดหีบสมบัติโบราณบนซากเรืออับปาง' },
  seashell: { id: 'seashell', name: 'เปลือกหอยมุกสีรุ้ง (Pearl Seashell)', sellPrice: 45, desc: 'เปลือกหอยแวววาว เก็บได้ตามชายหาดเกาะเขตร้อน' },
  message_bottle: { id: 'message_bottle', name: 'ขวดแก้วลายแทงสมบัติ', sellPrice: 75, desc: 'ขวดแก้วลอยน้ำที่มีลายแทงซากเรืออับปางซ่อนอยู่ด้านใน' },
  crab_meat: { id: 'crab_meat', name: 'เนื้อปูยักษ์สด (Stoneback Crab Meat)', sellPrice: 85, desc: 'เนื้อปูทะเลสดแน่นหวาน นำไปทอดเป็นทอดมันปูยักษ์' },
  cutlass_saber: { id: 'cutlass_saber', name: 'ดาบโจรสลัดคัตลาสอาถรรพ์ (Corsair Cutlass)', sellPrice: 2500, desc: 'ดาบโค้งเหล็กกล้าแห่งแคริบเบียน ฟันคลื่นจันทร์เสี้ยววารี พลังโจมตี 100 ติดคริติคอล 35%!' },
  pirate_tricorn_hat: { id: 'pirate_tricorn_hat', name: 'หมวกกัปตันโจรสลัดสามมุม (Captain Tricorn)', sellPrice: 1800, desc: '[หมวกแฟชั่น & บัฟ] สวมใส่เพิ่มโอกาสหลบหลีก +20% และเดินไวขึ้น +25%' },
  parrot_egg: { id: 'parrot_egg', name: 'ไข่นกแก้วมาคอว์โจรสลัด (Parrot Egg)', sellPrice: 3000, desc: 'ฟักเป็นนกแก้วคู่หูโจรสลัด บินตามเก็บของและจิกศัตรู' },
  island_warp_totem: { id: 'island_warp_totem', name: 'เสาวาร์ปเกาะเขตร้อน (Island Warp Totem)', sellPrice: 250, desc: 'กดใช้เพื่อเทเลพอร์ตข้ามมิติมายังเกาะเขตร้อนได้ทันทีจากทุกที่' },
  tropical_delight_drink: { id: 'tropical_delight_drink', name: 'ค็อกเทลเขตร้อนสูตรกัปตัน', sellPrice: 350, energyRestore: 160, hpRestore: 100, desc: 'เครื่องดื่มผลไม้เขตร้อนเย็นฉ่ำ ดื่มเพื่อวิ่งเร็วขึ้น +60% นาน 5 นาที!' },
  crab_cakes: { id: 'crab_cakes', name: 'ทอดมันปูยักษ์เกาะสมบัติ (Crab Cakes)', sellPrice: 380, energyRestore: 130, hpRestore: 70, desc: 'เนื้อปูคลุกเคล้าเครื่องเทศทอดกรอบ รสเลิศ' },
  tropical_smoothie: { id: 'tropical_smoothie', name: 'สมูทตี้ผลไม้รวมเขตร้อน (Tropical Smoothie)', sellPrice: 340, energyRestore: 120, hpRestore: 60, desc: 'สมูทตี้สับปะรด กล้วย มะพร้าว ฟื้นฟูพลังงานยอดเยี่ยม' },
  clownfish: { id: 'clownfish', name: 'ปลาการ์ตูนนีโม่', sellPrice: 85, desc: 'ปลาทะเลเขตร้อนลายส้มสลับขาว' },
  lionfish: { id: 'lionfish', name: 'ปลาสิงโตครีบเพลิง', sellPrice: 135, desc: 'ปลาทะเลครีบหนามแหลมคม ลวดลายงดงามดั่งเปลวไฟ' },
  manta_ray: { id: 'manta_ray', name: 'ปลากระเบนราหูยักษ์', sellPrice: 260, desc: 'กระเบนทะเลลึกตัวมหึมา ร่อนใต้เกลียวคลื่น' },
  hammerhead_shark: { id: 'hammerhead_shark', name: 'ฉลามหัวค้อนเกาะสมบัติ', sellPrice: 700, desc: 'ราชันแห่งท้องทะเลเขตร้อน ฉลามในตำนานที่เฝ้าซากเรืออับปาง' },
  magma_wyrm_scale: { id: 'magma_wyrm_scale', name: 'เกล็ดมังกรลาวายักษ์ (Magma Scale)', sellPrice: 1800, desc: 'เกล็ดหนาทนความร้อนนับพันองศา ดร็อปจากคาร์ซาร็อค ใช้หลอมอาวุธที่แท่นหลอมภูเขาไฟ' },
  volcano_flame_sword: { id: 'volcano_flame_sword', name: 'ดาบเพลิงสุริยันอัคนี (Solar Magma Blade)', sellPrice: 4500, desc: 'ดาบโบราณใจกลางภูเขาไฟ พลังโจมตี 135 คลื่นลูกไฟลาวา' },
  ring_of_fire_walker: { id: 'ring_of_fire_walker', name: 'แหวนผู้เดินบนลาวา (Firewalker Band)', sellPrice: 3200, desc: '[เครื่องประดับ] ป้องกันความเสียหายจากไฟและบ่อลาวา 100% พร้อมวิ่งไวขึ้น 15%' },
  volcano_cinder_forge_stone: { id: 'volcano_cinder_forge_stone', name: 'ศิลาหลอมอัคนีขั้นสูง', sellPrice: 1200, desc: 'ใช้ผสานพลังเสริมออปชันขั้นสูงสุดที่แท่นหลอมภูเขาไฟ' }
};

export const WORLD_MONSTERS: Record<string, WorldMonsterData> = {
  shadow_wolf: {
    id: 'shadow_wolf',
    name: 'หมาป่าเงา (Shadow Wolf)',
    hp: 80,
    maxHp: 80,
    speed: 1.6,
    damage: 12,
    attackCooldown: 900,
    aggroDist: 180,
    drops: [{ item: 'shadow_pelt', chance: 1.0 }, { item: 'wolf_fang', chance: 1.0 }],
    gold: 12,
    xp: 15
  },
  goblin_scout: {
    id: 'goblin_scout',
    name: 'ก็อบลินโจรไพร (Goblin Scout)',
    hp: 65,
    maxHp: 65,
    speed: 1.3,
    damage: 10,
    attackCooldown: 1100,
    aggroDist: 210,
    drops: [{ item: 'iron_ore', chance: 1.0 }, { item: 'starflower_herb', chance: 0.6 }],
    gold: 10,
    xp: 14
  },
  demon_treant: {
    id: 'demon_treant',
    name: 'ต้นไม้ปีศาจกินคน (Demon Treant)',
    hp: 170,
    maxHp: 170,
    speed: 0.7,
    damage: 20,
    attackCooldown: 1400,
    aggroDist: 150,
    drops: [{ item: 'cursed_wood', chance: 1.0 }, { item: 'mana_gem', chance: 0.75 }],
    gold: 24,
    xp: 28
  },
  cave_bat: {
    id: 'cave_bat',
    name: 'ค้างคาวถ้ำดูดเลือด (Cave Bat)',
    hp: 45,
    maxHp: 45,
    speed: 2.1,
    damage: 8,
    attackCooldown: 700,
    aggroDist: 190,
    drops: [{ item: 'bat_wing', chance: 1.0 }, { item: 'ruby_gem', chance: 0.5 }],
    gold: 8,
    xp: 12
  },
  crystal_slime: {
    id: 'crystal_slime',
    name: 'สไลม์ผลึกคริสตัล (Crystal Slime)',
    hp: 95,
    maxHp: 95,
    speed: 1.1,
    damage: 14,
    attackCooldown: 1200,
    aggroDist: 160,
    drops: [{ item: 'crystal_core', chance: 1.0 }, { item: 'mana_gem', chance: 0.65 }, { item: 'diamond_crystal', chance: 0.35 }],
    gold: 16,
    xp: 20
  },
  swamp_croc: {
    id: 'swamp_croc',
    name: 'จระเข้หนองน้ำพิษ (Gloom Marsh Croc)',
    hp: 120,
    maxHp: 120,
    speed: 1.1,
    damage: 16,
    attackCooldown: 1000,
    aggroDist: 170,
    drops: [{ item: 'hydra_scale', chance: 1.0 }, { item: 'swamp_herb', chance: 0.8 }],
    gold: 20,
    xp: 25
  },
  crystal_spider: {
    id: 'crystal_spider',
    name: 'แมงมุมผลึกปริซึม (Prismatic Crystal Spider)',
    hp: 85,
    maxHp: 85,
    speed: 1.7,
    damage: 14,
    attackCooldown: 800,
    aggroDist: 200,
    drops: [{ item: 'crystal_core', chance: 1.0 }, { item: 'diamond_crystal', chance: 0.45 }],
    gold: 18,
    xp: 22
  },
  magma_elemental: {
    id: 'magma_elemental',
    name: 'อสูรธาตุเพลิงลาวา (Magma Elemental)',
    hp: 150,
    maxHp: 150,
    speed: 0.9,
    damage: 20,
    attackCooldown: 1300,
    aggroDist: 180,
    drops: [{ item: 'flame_heart', chance: 1.0 }, { item: 'ruby_gem', chance: 0.8 }],
    gold: 25,
    xp: 32
  },
  frost_wolf: {
    id: 'frost_wolf',
    name: 'หมาป่าหิมะเยือกแข็ง (Frostpeak Snow Wolf)',
    hp: 110,
    maxHp: 110,
    speed: 1.8,
    damage: 17,
    attackCooldown: 900,
    aggroDist: 210,
    drops: [{ item: 'frost_crystal', chance: 1.0 }, { item: 'wolf_fang', chance: 1.0 }, { item: 'frost_berry', chance: 0.6 }],
    gold: 22,
    xp: 28
  },
  skeleton_warrior: {
    id: 'skeleton_warrior',
    name: 'นักรบโครงกระดูกโบราณ (Ancient Skeleton Warrior)',
    hp: 130,
    maxHp: 130,
    speed: 1.2,
    damage: 19,
    attackCooldown: 1100,
    aggroDist: 180,
    drops: [{ item: 'iron_ore', chance: 1.0 }, { item: 'cursed_relic', chance: 1.0 }],
    gold: 24,
    xp: 30
  },
  spire_demon: {
    id: 'spire_demon',
    name: 'อสูรผลึกมิติ (Spire Crystal Fiend)',
    hp: 150,
    maxHp: 150,
    speed: 1.6,
    damage: 22,
    attackCooldown: 900,
    aggroDist: 220,
    drops: [{ item: 'spire_shard', chance: 0.95 }, { item: 'crystal_core', chance: 0.4 }],
    gold: 30,
    xp: 38
  },
  spire_colossus: {
    id: 'spire_colossus',
    name: 'ผู้พิทักษ์หอคอยมิติ (Spire Colossus Guardian)',
    hp: 380,
    maxHp: 380,
    speed: 1.1,
    damage: 32,
    attackCooldown: 1200,
    aggroDist: 260,
    drops: [{ item: 'spire_shard', chance: 1.0 }, { item: 'diamond_crystal', chance: 0.6 }],
    gold: 65,
    xp: 70
  },
  island_crab: {
    id: 'island_crab',
    name: 'ปูยักษ์เกราะหิน (Stoneback Crab)',
    hp: 140,
    maxHp: 140,
    speed: 1.1,
    damage: 16,
    attackCooldown: 1000,
    aggroDist: 170,
    drops: [{ item: 'crab_meat', chance: 1.0 }, { item: 'seashell', chance: 0.75 }, { item: 'pirate_doubloon', chance: 0.3 }],
    gold: 25,
    xp: 28
  },
  cursed_pirate_skeleton: {
    id: 'cursed_pirate_skeleton',
    name: 'โจรสลัดโครงกระดูกต้องสาป (Cursed Pirate Skeleton)',
    hp: 210,
    maxHp: 210,
    speed: 1.5,
    damage: 26,
    attackCooldown: 850,
    aggroDist: 220,
    drops: [{ item: 'pirate_doubloon', chance: 1.0 }, { item: 'skeleton_key', chance: 0.4 }, { item: 'gold_ore', chance: 0.6 }],
    gold: 45,
    xp: 50
  },
  magma_sprite: {
    id: 'magma_sprite',
    name: 'ภูตลูกไฟลาวา (Magma Sprite)',
    hp: 120,
    maxHp: 120,
    speed: 1.8,
    damage: 20,
    attackCooldown: 700,
    aggroDist: 240,
    drops: [{ item: 'cinder_shard', chance: 0.8 }, { item: 'coal', chance: 0.6 }],
    gold: 30,
    xp: 35
  },
  magma_duggy: {
    id: 'magma_duggy',
    name: 'หนอนลาวาหนามหิน (Magma Duggy)',
    hp: 190,
    maxHp: 190,
    speed: 1.2,
    damage: 28,
    attackCooldown: 850,
    aggroDist: 200,
    drops: [{ item: 'cinder_shard', chance: 0.9 }, { item: 'iron_ore', chance: 0.6 }],
    gold: 42,
    xp: 48
  },
  lava_lurker: {
    id: 'lava_lurker',
    name: 'ปีศาจลาวาดำ (Lava Lurker)',
    hp: 280,
    maxHp: 280,
    speed: 1.0,
    damage: 36,
    attackCooldown: 1000,
    aggroDist: 220,
    drops: [{ item: 'cinder_shard', chance: 1.0 }, { item: 'magma_wyrm_scale', chance: 0.25 }, { item: 'gold_ore', chance: 0.6 }],
    gold: 65,
    xp: 75
  }
};

export const BOSS_KATHUROS: BossData = {
  id: 'boss_kathuros',
  name: 'ราชินีสปอร์ปีศาจ คาธูรอส',
  title: 'เจ้านรกแห่งวิหารโบราณ (Queen of Blight Kathuros)',
  hp: 2600,
  maxHp: 2600,
  speed: 1.0,
  damage: 18,
  attackCooldown: 1200,
  aggroDist: 380,
  gold: 180,
  xp: 450,
  drops: [
    { item: 'demon_heart', chance: 1.0, count: 1 },
    { item: 'crown_of_despair', chance: 1.0, count: 1 },
    { item: 'ruby_gem', chance: 1.0, count: 2 }
  ]
};

export const BOSS_LUMINARCH: BossData = {
  id: 'boss_luminarch',
  name: 'โกเลมผลึกคริสตัลโบราณ ลูมินาร์ค',
  title: 'ผู้พิทักษ์หุบเหวปริซึม (Ancient Crystal Golem Luminarch)',
  hp: 4500,
  maxHp: 4500,
  speed: 0.85,
  damage: 24,
  attackCooldown: 1400,
  aggroDist: 380,
  gold: 280,
  xp: 650,
  drops: [
    { item: 'luminarch_crystal_heart', chance: 1.0, count: 1 },
    { item: 'diamond_crystal', chance: 1.0, count: 2 },
    { item: 'gold_ore', chance: 1.0, count: 3 }
  ]
};

export const BOSS_HYDRAKIS: BossData = {
  id: 'boss_hydrakis',
  name: 'พญาไฮดราหนองน้ำพิษ ไฮดราคิส',
  title: 'มัจจุราชสามเศียรแห่งบึงมืด (Hydrakis the Venom Marsh Hydra)',
  hp: 5400,
  maxHp: 5400,
  speed: 1.05,
  damage: 26,
  attackCooldown: 1100,
  aggroDist: 380,
  gold: 340,
  xp: 750,
  drops: [
    { item: 'hydra_venom_gland', chance: 1.0, count: 1 },
    { item: 'hydra_scale', chance: 1.0, count: 3 },
    { item: 'swamp_herb', chance: 1.0, count: 4 }
  ]
};

export const BOSS_IGNISTRON: BossData = {
  id: 'boss_ignistron',
  name: 'ราชันย์มังกรลาวาเพลิงอัคนี อิกนิสทรอน',
  title: 'เจ้าอสูรเพลิงโลกันตร์ (Ignistron the Molten Flame Drake)',
  hp: 7200,
  maxHp: 7200,
  speed: 1.15,
  damage: 30,
  attackCooldown: 1000,
  aggroDist: 400,
  gold: 420,
  xp: 900,
  drops: [
    { item: 'magma_dragon_horn', chance: 1.0, count: 1 },
    { item: 'flame_heart', chance: 1.0, count: 2 },
    { item: 'ruby_gem', chance: 1.0, count: 4 }
  ]
};

export const BOSS_FROSTFANG: BossData = {
  id: 'boss_frostfang',
  name: 'จอมอสูรไททันน้ำแข็ง ฟรอสต์แฟงก์',
  title: 'เจ้าพายุเหมันต์นิรันดร์ (Frostfang the Glacial Titan)',
  hp: 7600,
  maxHp: 7600,
  speed: 0.95,
  damage: 32,
  attackCooldown: 1200,
  aggroDist: 380,
  gold: 480,
  xp: 950,
  drops: [
    { item: 'glacial_titan_core', chance: 1.0, count: 1 },
    { item: 'frost_crystal', chance: 1.0, count: 3 },
    { item: 'diamond_crystal', chance: 1.0, count: 2 }
  ]
};

export const BOSS_MALAKOR: BossData = {
  id: 'boss_malakor',
  name: 'ลอร์ดมรณะกระดูกอสูร มาลาคอร์',
  title: 'ราชาไร้นามแห่งสุสานต้องสาป (Lord Malakor the Undead Overlord)',
  hp: 9500,
  maxHp: 9500,
  speed: 1.0,
  damage: 36,
  attackCooldown: 1100,
  aggroDist: 380,
  gold: 600,
  xp: 1200,
  drops: [
    { item: 'death_lord_soul', chance: 1.0, count: 1 },
    { item: 'cursed_relic', chance: 1.0, count: 2 },
    { item: 'crown_of_despair', chance: 1.0, count: 1 }
  ]
};

export const BOSS_SYLVANUS: BossData = {
  id: 'boss_sylvanus',
  name: 'เทพพฤกษาบรรพกาล ซิลวาเนีย',
  title: 'เทวีผู้พิทักษ์ไพรสณฑ์โบราณ (Sylvanus Ancient Forest Sovereign)',
  hp: 11000,
  maxHp: 11000,
  speed: 0.95,
  damage: 38,
  attackCooldown: 1000,
  aggroDist: 420,
  gold: 750,
  xp: 1400,
  drops: [
    { item: 'ancient_tree_heart', chance: 1.0, count: 1 },
    { item: 'sacred_shard_nature', chance: 1.0, count: 1 },
    { item: 'star_fruit', chance: 1.0, count: 4 }
  ]
};

export const BOSS_ASTREON: BossData = {
  id: 'boss_astreon',
  name: 'จ้าวแห่งพายุสายฟ้า ออสทริออน',
  title: 'ราชันย์แห่งสายฟ้าและวายุคลั่ง (Astreon Sovereign of Tempest)',
  hp: 13500,
  maxHp: 13500,
  speed: 1.45,
  damage: 42,
  attackCooldown: 850,
  aggroDist: 450,
  gold: 950,
  xp: 1800,
  drops: [
    { item: 'storm_core', chance: 1.0, count: 1 },
    { item: 'sacred_shard_thunder', chance: 1.0, count: 1 },
    { item: 'thunder_crystal', chance: 1.0, count: 5 }
  ]
};

export const BOSS_KARZARAK: BossData = {
  id: 'boss_karzarak',
  name: 'คาร์ซาร็อค มังกรลาวายักษ์โบราณ',
  title: 'จ้าวแห่งปล่องภูเขาไฟเกาะสมบัติ (Karzarak the Ancient Magma Wyrm)',
  hp: 2800,
  maxHp: 2800,
  speed: 1.25,
  damage: 38,
  attackCooldown: 900,
  aggroDist: 480,
  gold: 800,
  xp: 1600,
  drops: [
    { item: 'magma_wyrm_scale', chance: 1.0, count: 3 },
    { item: 'volcano_flame_sword', chance: 1.0, count: 1 },
    { item: 'ring_of_fire_walker', chance: 1.0, count: 1 },
    { item: 'cinder_shard', chance: 1.0, count: 20 },
    { item: 'pirate_doubloon', chance: 1.0, count: 15 }
  ]
};

export const BOSS_REGISTRY: Record<string, BossData> = {
  boss_kathuros: BOSS_KATHUROS,
  boss_luminarch: BOSS_LUMINARCH,
  boss_hydrakis: BOSS_HYDRAKIS,
  boss_ignistron: BOSS_IGNISTRON,
  boss_frostfang: BOSS_FROSTFANG,
  boss_malakor: BOSS_MALAKOR,
  boss_sylvanus: BOSS_SYLVANUS,
  boss_astreon: BOSS_ASTREON,
  boss_karzarak: BOSS_KARZARAK
};

export interface VolcanoForgeRecipe {
  id: string;
  name: string;
  desc: string;
  costCinderShards: number;
  materials?: Record<string, number>;
  resultItem?: string;
  resultCount?: number;
  type: 'weapon' | 'accessory' | 'enchant' | 'currency';
}

export const VOLCANO_FORGE_RECIPES: Record<string, VolcanoForgeRecipe> = {
  forge_solar_blade: {
    id: 'forge_solar_blade',
    name: 'ดาบเพลิงสุริยันอัคนี (Solar Magma Blade)',
    desc: 'หลอมดาบเพลิงศักดิ์สิทธิ์ใจกลางภูเขาไฟ พลังโจมตี 135 คลื่นลูกไฟลาวา',
    costCinderShards: 15,
    materials: { magma_wyrm_scale: 2, gold_ore: 5 },
    resultItem: 'volcano_flame_sword',
    resultCount: 1,
    type: 'weapon'
  },
  forge_fire_ring: {
    id: 'forge_fire_ring',
    name: 'แหวนผู้เดินบนลาวา (Firewalker Band)',
    desc: 'เครื่องประดับโบราณ ป้องกันความเสียหายจากไฟและลาวา 100% พร้อมวิ่งไวขึ้น 15%',
    costCinderShards: 10,
    materials: { magma_wyrm_scale: 1, ruby_gem: 2 },
    resultItem: 'ring_of_fire_walker',
    resultCount: 1,
    type: 'accessory'
  },
  forge_enchant_weapon: {
    id: 'forge_enchant_weapon',
    name: 'สลักรูนเถ้าภูเขาไฟเสริมอาวุธ (+30 DMG, +15% Crit)',
    desc: 'อาบพลังเถ้าภูเขาไฟให้อาวุธที่สวมใส่ เพิ่มพลังโจมตี +30 และโอกาสคริติคอล +15%',
    costCinderShards: 12,
    materials: { gold_ore: 3 },
    type: 'enchant'
  },
  forge_cinder_to_doubloons: {
    id: 'forge_cinder_to_doubloons',
    name: 'หลอมเศษเถ้าเป็นเหรียญทองโจรสลัด (5 เหรียญ)',
    desc: 'นำเศษผลึกเพลิง 5 ชิ้น หลอมประทับตราเป็นเหรียญทองโจรสลัดโบราณ 5 เหรียญ',
    costCinderShards: 5,
    resultItem: 'pirate_doubloon',
    resultCount: 5,
    type: 'currency'
  }
};

export const QUESTS: Record<string, QuestData> = {
  q1: {
    id: 'q1',
    title: 'บทที่ 1: วิบัติสปอร์กลายพันธุ์ (Blight of Mutated Bugs)',
    desc: 'เกิดโรคระบาดปริศนาจากละอองสปอร์สีเลือด ทำให้แมลงในไร่และป่ากลายพันธุ์ตัวมหึมาเข้าโจมตีชาวบ้าน! จงกำจัดแมลงปีศาจ 3 ตัวในไร่ รวบรวมสปอร์กลายพันธุ์ 2 ชิ้น แล้วไปพบนายกเทศมนตรีกิลเบิร์ตที่คฤหาสน์หมู่บ้านศิลาสุขาวดี',
    giver: 'gilbert',
    targetType: 'collect',
    targetNpc: 'gilbert',
    reqBugs: 3,
    reqSpores: 2,
    rewardDesc: '200 G, ยาฟื้นพลังชีวิต x3, 100 XP',
    goldReward: 100,
    xpReward: 100,
    itemsReward: [
      { id: 'health_potion', count: 3, name: 'ยาฟื้นพลังชีวิตชั้นเลิศ' }
    ]
  },
  q2: {
    id: 'q2',
    title: 'บทที่ 2: วิจัยเซรุ่มต้านพิษ (The Apothecary\'s Antidote)',
    desc: 'หมอยาสาวลิเลียนกำลังเร่งศึกษาสูตรสกัดเพื่อคิดค้นเซรุ่มแก้พิษสปอร์! จงนำ สปอร์กลายพันธุ์ 3 ชิ้น และ สมุนไพรดวงดาว 2 ดอก จากป่ามาส่งให้ลิเลียนที่คลินิกสมุนไพรหมู่บ้าน',
    giver: 'lilian',
    targetType: 'collect',
    targetNpc: 'lilian',
    rewardDesc: '350 G, เซรุ่มต้านสปอร์พิษ x2, ดาบเหล็กกล้า, 180 XP',
    goldReward: 180,
    xpReward: 180,
    itemsReward: [
      { id: 'antidote_serum', count: 2, name: 'เซรุ่มต้านสปอร์พิษ' },
      { id: 'iron_sword', count: 1, name: 'ดาบเหล็กกล้านักผจญภัย' }
    ]
  },
  q3: {
    id: 'q3',
    title: 'บทที่ 3: ตรึงแนวรบปราการเหนือ (Fortify the Northern Barricade)',
    desc: 'ผู้กองวาเลเรียประจำการอยู่ที่ประตูปราการเหนือของหมู่บ้านเพื่อสกัดกั้นฝูงแมลงยักษ์และสัตว์ป่าติดเชื้อ จงช่วยกำจัดหมาป่าเงา 3 ตัวในป่าทึบ และขุดแร่ทับทิม 2 ก้อนส่งให้ช่างตีเหล็กคาเอลสร้างอาวุธเสริมแกร่ง',
    giver: 'valeria',
    targetType: 'hunt_mine',
    targetNpc: 'valeria',
    reqWolves: 3,
    reqRubies: 2,
    rewardDesc: '500 G, ปืนล่าสัตว์โบราณ, 250 XP',
    goldReward: 250,
    xpReward: 250,
    itemsReward: [
      { id: 'rifle', count: 1, name: 'ปืนล่าสัตว์โบราณ' }
    ]
  },
  q4: {
    id: 'q4',
    title: 'บทที่ 4: สำรวจถ้ำรังไหมผลึก (The Cocoon & Crystal Caverns)',
    desc: 'ผู้เฒ่าปราชญ์เอลดรินตรวจพบว่าสปอร์ระบาดกำลังบ่มเพาะรังไหมยักษ์ในถ้ำผลึกใต้พิภพทางทิศตะวันออกเฉียงเหนือ! จงบุกเข้าไปขุดผลึกมานาสีคราม 2 ชิ้น และกำจัดค้างคาวถ้ำหรือสไลม์ผลึก 3 ตัว เพื่อไขความลับต้นตอของฝูงแมลง',
    giver: 'eldrin',
    targetType: 'hunt_mine',
    targetNpc: 'eldrin',
    rewardDesc: '800 G, เซรุ่มต้านสปอร์พิษ x3, 400 XP',
    goldReward: 350,
    xpReward: 350,
    itemsReward: [
      { id: 'antidote_serum', count: 3, name: 'เซรุ่มต้านสปอร์พิษ' }
    ]
  },
  q5: {
    id: 'q5',
    title: 'บทที่ 5: ชำระล้างราชินีสปอร์ปีศาจ คาธูรอส (Purify Queen Broodmother Kathuros)',
    desc: 'ต้นตอของเชื้อร้ายคือ ราชินีสปอร์ปีศาจ คาธูรอส ณ ลานบูชาวิหารโบราณทางเหนือสุด! จงบุกข้ามสะพานเข้าสู่ใจกลางวิหาร สยบจอมอสูร และชำระล้างแหล่งแพร่พันธุ์เพื่อคืนความสงบสุขให้ฟาร์มและหมู่บ้าน!',
    giver: 'gilbert',
    targetType: 'boss',
    targetBoss: 'boss_kathuros',
    rewardDesc: '500 G, ดาบศักดิ์สิทธิ์เอ็กซ์คาลิเบอร์, ฉายายอดวีรบุรุษนักสวนผู้กอบกู้แผ่นดิน, 1,200 XP',
    goldReward: 500,
    xpReward: 800,
    itemsReward: [
      { id: 'excalibur_sword', count: 1, name: 'ดาบศักดิ์สิทธิ์เอ็กซ์คาลิเบอร์' }
    ]
  },
  q6: {
    id: 'q6',
    title: 'บทที่ 6: หัวใจผลึกปริซึมใต้พิภพ (The Crystal Abyss Core)',
    desc: 'เอลดรินสัมผัสได้ถึงคลื่นสั่นสะเทือนจากถ้ำผลึกลึกชั้นใต้พิภพ (The Crystal Abyss)! "โกเลมผลึกโบราณ ลูมินาร์ค" ผู้พิทักษ์แก่นแท้แห่งธาตุได้ตื่นขึ้น จงลงบันไดรอยแยกผลึกในถ้ำ สยบโกเลม และนำ หัวใจผลึกปริซึมลูมินาร์ค กลับมา!',
    giver: 'eldrin',
    targetType: 'boss',
    targetBoss: 'boss_luminarch',
    rewardDesc: '650 G, เพชรผลึกประกายรุ้ง x3, 1,500 XP',
    goldReward: 650,
    xpReward: 1000,
    itemsReward: [
      { id: 'diamond_crystal', count: 3, name: 'เพชรผลึกประกายรุ้ง' }
    ]
  },
  q7: {
    id: 'q7',
    title: 'บทที่ 7: กวาดล้างมัจจุราชแห่งบึงมืด (The Venom Marsh Scourge)',
    desc: 'ลิเลียนตรวจพบว่าสารพิษที่แทรกซึมสู่แหล่งน้ำธรรมชาติ ไหลมาจาก "พญาไฮดราสามเศียร ไฮดราคิส" ในหนองน้ำมืดทางตะวันตกเฉียงใต้! จงนำเซรุ่มและอาหารบัฟไปลุยดงบึงพิษ ปราบไฮดรา และชิง ต่อมพิษพญาไฮดราโบราณ มาสร้างธนูพิษ!',
    giver: 'lilian',
    targetType: 'boss',
    targetBoss: 'boss_hydrakis',
    rewardDesc: '800 G, ยาฟื้นพลังชีวิตชั้นเลิศ x5, 1,800 XP',
    goldReward: 800,
    xpReward: 1200,
    itemsReward: [
      { id: 'health_potion', count: 5, name: 'ยาฟื้นพลังชีวิตชั้นเลิศ' }
    ]
  },
  q8: {
    id: 'q8',
    title: 'บทที่ 8: โทสะแห่งภูเขาไฟลาวาเดือด (The Wrath of Mount Ignis)',
    desc: 'ผู้กองวาเลเรียแจ้งเตือนภัยแดงด่วน! เตาลาวาโบราณปะทุขึ้น และ "ราชันย์มังกรลาวา อิกนิสทรอน" กำลังโหมพ่นเปลวเพลิงโลกันตร์ลงมาเผาผลาญเมือง! จงบุกสู่ปากปล่องภูเขาไฟทางตะวันตกเฉียงเหนือ ดับไฟพิโรธ และนำ เขามังกรอัคนีเพลิง มาหลอมขวานเพลิง!',
    giver: 'valeria',
    targetType: 'boss',
    targetBoss: 'boss_ignistron',
    rewardDesc: '1,000 G, อัญมณีทับทิมโลกันตร์ x5, 2,000 XP',
    goldReward: 1000,
    xpReward: 1400,
    itemsReward: [
      { id: 'ruby_gem', count: 5, name: 'อัญมณีทับทิมโลกันตร์' }
    ]
  },
  q9: {
    id: 'q9',
    title: 'บทที่ 9: ไททันเหมันต์แห่งยอดเขาเยือกแข็ง (The Glacial Titan of Frostpeak)',
    desc: 'ช่างตีเหล็กคาเอลเตือนว่าความหนาวเหน็บผิดธรรมชาติกำลังแช่แข็งสายแร่บนยอดเขาหิมะเยือกแข็งทางตะวันออกเฉียงเหนือ "จอมอสูรไททันน้ำแข็ง ฟรอสต์แฟงก์" ได้คืนชีพ! จงปีนฝ่าพายุหิมะ พิชิตไททัน และนำ แก่นเหมันต์ไททันน้ำแข็ง มาตีค้อนทุบปฐพี!',
    giver: 'kael',
    targetType: 'boss',
    targetBoss: 'boss_frostfang',
    rewardDesc: '1,200 G, ผลึกน้ำแข็งบริสุทธิ์ x5, 2,500 XP',
    goldReward: 1200,
    xpReward: 1600,
    itemsReward: [
      { id: 'frost_crystal', count: 5, name: 'ผลึกน้ำแข็งบริสุทธิ์' }
    ]
  },
  q10: {
    id: 'q10',
    title: 'บทที่ 10 (มหาศึกอวสาน): บัญชามรณะแห่งลอร์ดมาลาคอร์ (The Nether Overlord Lord Malakor)',
    desc: 'ความจริงอันดำมืดถูกเปิดเผยโดยกิลเบิร์ตและเอลดริน! ผู้อยู่เบื้องหลังสปอร์ปีศาจและอสูรกลายพันธุ์ทั้งหมด คือ "ลอร์ดมรณะกระดูกอสูร มาลาคอร์" จอมราชันย์แห่งสุสานใต้พิภพต้องสาปทางตะวันออกเฉียงใต้! จงบุกสุสานโบราณ สังหารมาลาคอร์ และนำสันติภาพนิรันดร์มาสู่ผืนดินสุขาวดี!',
    giver: 'gilbert',
    targetType: 'boss',
    targetBoss: 'boss_malakor',
    rewardDesc: '1,800 G, เคียวมรณะสูบวิญญาณลอร์ดมาลาคอร์, ฉายามหาผู้พิทักษ์แห่งจักรวาลและแผ่นดินสุขาวดี, 5,000 XP',
    goldReward: 1800,
    xpReward: 2500,
    itemsReward: [
      { id: 'malakor_soul_scythe', count: 1, name: 'เคียวมรณะสูบวิญญาณลอร์ดมาลาคอร์' }
    ]
  },
  q_shrine: {
    id: 'q_shrine',
    title: 'บทสรุปตำนาน: ปลดผนึกวิหารเทวะโบราณ (The Sacred Celestial Seal)',
    desc: 'รวบรวม "แก่นศิลาศักดิ์สิทธิ์ทั้ง 8 ธาตุ" (ปฐพี, สุริยัน, วารี, อัคคี, เหมันต์, ทมิฬ, พฤกษา, อัสนี) จากการพิชิต 8 มหาบอสทั่วทั้งโลกผจญภัย นำไปวาง ณ แท่นบูชาวิหารศักดิ์สิทธิ์ (The Ancient Shrine Altar) เพื่อปลดปล่อยพลังงานเทวะฟื้นฟูหุบเขาแห่งศิลาสุขาวดีให้รุ่งเรืองชั่วนิรันดร์!',
    giver: 'eldrin',
    targetType: 'purify',
    targetNpc: 'eldrin',
    rewardDesc: 'ฉายามหาจักรพรรดิผู้พิทักษ์แห่งจักรวาลและแผ่นดินสุขาวดี, ปลดล็อก Master Mode (New Game+), บัฟพรแห่งเทพถาวร (พืชโตเร็วขึ้น 1 วัน & วิ่งเร็วขึ้น +35%), ทองคำ 3,500 G, 20,000 XP',
    goldReward: 3500,
    xpReward: 5000,
    itemsReward: []
  }
};

export const NPC_STORY: Record<string, StoryNPCData> = {
  gilbert: {
    id: 'gilbert',
    name: 'นายกเทศมนตรี กิลเบิร์ต',
    role: 'ผู้นำหมู่บ้านศิลาสุขาวดี (Sunvale Mayor)',
    portraitType: 'gilbert',
    dialogues: {
      intro: 'ยินดีต้อนรับท่านชาวสวนผู้กล้าหาญ! ข้าคือกิลเบิร์ต... สถานการณ์ตอนนี้วิกฤตเหลือเกิน ละอองสปอร์สีแดงจากทางเหนือทำให้แมลงในธรรมชาติกลายร่างเป็นอสูรยักษ์บุกทำลายพืชผลและขู่ขวัญชาวบ้าน! เราต้องการคนที่มีความรู้เรื่องธรรมชาติเช่นเจ้าช่วยสำรวจต้นตอ!',
      q1_progress: 'เจ้ากำจัดแมลงยักษ์และเก็บสปอร์มาได้หรือยัง? ระวังตัวด้วยนะ สปอร์พวกนั้นอันตรายมาก!',
      q1_reward: 'เจ้าทำได้จริงๆ! สปอร์พวกนี้คือหลักฐานชิ้นสำคัญ รีบนำไปให้ หมอยาลิเลียน ที่คลินิกทางทิศตะวันออกเฉียงเหนือของหมู่บ้านวิจัยทันทีเลย!',
      q5_intro: 'ท่านผู้กล้า... บัดนี้เราได้เซรุ่มและอาวุธศักดิ์สิทธิ์พร้อมแล้ว ถึงเวลาต้องบุกวิหารทางเหนือสุดเพื่อสยบ "ราชินีสปอร์ปีศาจ คาธูรอส" ต้นตอของหายนะครั้งนี้!',
      q5_victory: 'มหาศึกสิ้นสุดลงแล้ว! สปอร์สีเลือดสลายไป ท้องฟ้ากลับมาสดใสอีกครั้ง ในนามของชาวหมู่บ้านศิลาสุขาวดี ขอยกย่องท่านเป็น "ยอดวีรบุรุษนักสวนผู้กอบกู้แผ่นดิน"!',
      q10_intro: 'ท่านผู้กล้า! เอลดรินได้ยืนยันความจริงอันน่าสะพรึงกลัวแล้ว... แท้จริงแล้ว "ลอร์ดมรณะกระดูกอสูร มาลาคอร์" แห่งสุสานใต้พิภพทางตะวันออกเฉียงใต้ คือจอมบงการผู้อยู่เบื้องหลังคำสาปสปอร์มรณะและมหาบอสทั้งหมด! หากไม่ปราบมัน แผ่นดินจะไม่มีวันสงบสุขอย่างแท้จริง!',
      q10_progress: 'สุสานใต้พิภพเต็มไปด้วยไอวิญญาณคนตายและเวทมนตร์แห่งความมืด ขอให้ท่านเตรียมเสบียงรบและอาวุธระดับตำนานให้พร้อมที่สุด!',
      grand_finale_victory: 'ปาฏิหาริย์เกิดขึ้นแล้ว! มาลาคอร์ถูกปราบ และมหาบอสทั้ง 8 ทั่วทุกแดน ไม่ว่าจะเป็นเทพพฤกษาซิลวาเนียหรือจ้าวพายุออสทริออน ล้วนถูกสยบลงด้วยมือของท่าน! บัดนี้ แผ่นดินศิลาสุขาวดีและผืนฟาร์มได้รับการปลดปล่อยสู่ยุคทองแห่งสันติสุขนิรันดร์ ขอยกย่องท่านเป็น "มหาจักรพรรดิผู้พิทักษ์แห่งจักรวาลและแผ่นดินสุขาวดี"!'
    }
  },
  lilian: {
    id: 'lilian',
    name: 'หมอยาสาว ลิเลียน',
    role: 'แพทย์สมุนไพรและนักพฤกษศาสตร์ (Apothecary)',
    portraitType: 'lilian',
    dialogues: {
      intro: 'สวัสดีจ้ะ! ข้าคือลิเลียน ดูแลคลินิกปรุงยาของหมู่บ้าน... สปอร์สีแดงนี้มีความเข้มข้นของสารพิษชีวภาพสูงมาก ทำให้สิ่งมีชีวิตโตผิดธรรมชาติและดุร้าย หากข้าได้ สปอร์กลายพันธุ์ 3 ชิ้น และ สมุนไพรดวงดาว 2 ดอก ข้าจะสามารถสกัด "เซรุ่มต้านสปอร์พิษ" ได้สำเร็จ!',
      q2_progress: 'สมุนไพรดวงดาวมักจะบานอยู่ตามริมน้ำและซอกหินในป่าทึบ เจ้าเก็บมาครบหรือยังจ๊ะ?',
      q2_complete: 'ยอดเยี่ยมมาก! กลิ่นหอมบริสุทธิ์ของสมุนไพรดวงดาวกำลังสะเทินพิษสปอร์... นี่คือ "เซรุ่มต้านสปอร์พิษ" สำหรับเจ้า! ดื่มเมื่อไหร่จะฟื้นฟูทั้ง HP และพลังงานทันที แถมข้ายังสอนสูตรปรุงยานี้ให้เจ้าด้วยนะ!',
      q7_intro: 'ท่านผู้กล้าจ๊ะ! ข้าตรวจพบว่าสายน้ำที่หล่อเลี้ยงฟาร์มเริ่มมีสารพิษสีเขียวมรกตปนเปื้อน... มันไหลมาจาก "พญาไฮดราสามเศียร ไฮดราคิส" ในหนองน้ำมืดทางตะวันตกเฉียงใต้! หากเจ้าปราบมันและนำ "ต่อมพิษพญาไฮดราโบราณ" มาได้ ข้าจะช่วยสกัดยาแก้สารพัดพิษและให้ช่างคาเอลสร้างคันธนูพิษให้เจ้าจ้ะ!',
      q7_progress: 'หนองน้ำมืดเต็มไปด้วยไอพิษ อย่าลืมดื่มเซรุ่มต้านพิษและทานซุปเกราะสมุนไพรก่อนเข้าสู้นะจ๊ะ!',
      q7_complete: 'น่าอัศจรรย์ยิ่งนัก! ต่อมพิษบริสุทธิ์จากพญาไฮดรานี้มีฤทธิ์ต้านพิษทุกชนิดในโลก ขอบใจเจ้ามากนะจ๊ะ รับยาฟื้นพลังชีวิตชั้นเลิศเหล่านี้ไปใช้เถิด!',
      ready_craft: 'ต้องการให้ข้าช่วยปรุงเซรุ่ม ยาฟื้นพลัง หรือซุปสมุนไพรเพิ่มไหม? วัตถุดิบในสวนของเจ้าใช้ประโยชน์ได้มหาศาลเลยล่ะ!'
    }
  },
  bob: {
    id: 'bob',
    name: 'บ็อบ เจ้าของโรงเตี๊ยมรวงทอง',
    role: 'เถ้าแก่โรงเตี๊ยมและแหล่งข่าวกรอง (Barkeeper Bob)',
    portraitType: 'bob',
    dialogues: {
      intro: 'ฮ่าฮ่าฮ่า! ยินดีต้อนรับสู่โรงเตี๊ยมรวงทอง สหายเอ๋ย! เข้ามาหลบพักเหนื่อย จิบเบียร์ข้าวสาลีหรือกินปลาย่างอุ่นๆ สักจานไหม? ข้าได้ยินพรานป่าคุยกันว่าทางเหนือมีหมอกประหลาดลอยลงมา อย่าลืมพกอาวุธติดตัวไว้เสมอนะ!',
      rumors: 'มีคนเห็นแสงสีม่วงวาบออกมาจากถ้ำผลึกทางตะวันออกเฉียงเหนือ... ดูเหมือนพวกแมลงยักษ์จะใช้ถ้ำนั้นเป็นรังดักแด้ฟักตัวล่ะ ถ้าคิดจะไปสำรวจ ต้องเตรียมเซรุ่มและอาวุธไปให้พร้อมนะ!',
      bounty_hint: 'เฮ้เกลอ! ข้าเพิ่งติด "กระดานประกาศล่าค่าหัวมหาบอส (Bounty Board)" ไว้บนผนังโรงเตี๊ยมนะ! มหาบอสระดับพระกาฬทั้ง 6 แห่งแผ่นดิน มีค่าหัวและของรางวัลมหาศาล เจ้าลองไปตรวจดูสิ!'
    }
  },
  valeria: {
    id: 'valeria',
    name: 'ผู้กองวาเลเรีย',
    role: 'ผู้พิทักษ์ปราการด่านหน้าแห่งอาณาจักร',
    portraitType: 'valeria',
    dialogues: {
      intro: 'สวัสดีท่านชาวสวน! ข้าผู้กองวาเลเรีย กำลังระดมกำลังตรึงประตูปราการเหนือของหมู่บ้าน ฝูงสัตว์ป่าติดเชื้อและแมลงยักษ์กำลังพยายามพังแนวป้องกันเข้ามา! ข้าต้องการสหายร่วมรบฝีมือดีอย่างท่าน!',
      q3_progress: 'แนวรบด้านนอกยังมีหมาป่าเงาและอสูรติดเชื้อป้วนเปี้ยนอยู่ จงระวังเขี้ยวเล็บของพวกมันด้วย!',
      q3_complete: 'ขอบคุณที่ช่วยกวาดล้างแนวหน้า! และแร่ทับทิมเหล่านี้ ช่างตีเหล็กคาเอลได้นำไปตีเสริมคมอาวุธแล้ว รับปืนล่าสัตว์โบราณกระบอกนี้ไปใช้เถิด!',
      q8_intro: 'สัญญาณเตือนภัยสีแดงระดับสูงสุด! เตาลาวาโบราณ ณ ปากปล่องภูเขาไฟทางตะวันตกเฉียงเหนือกำลังเดือดพล่าน "ราชันย์มังกรลาวา อิกนิสทรอน" กำลังจะพ่นฝนเพลิงเผาผลาญเมือง! ข้าขอฝากท่านบุกไปตัดเขามังกรอัคนีเพลิงของมันมาดับไฟหายนะครั้งนี้!',
      q8_progress: 'ระวังอุกกาบาตเพลิงและธารลาวาเดือดของอิกนิสทรอนด้วยนะสหาย! รีบหลบวงเตือนบนพื้นให้ทัน!',
      q8_complete: 'สุดยอดการรบ! ท่านดับเพลิงพิโรธของมังกรลาวาลงได้สำเร็จ แผ่นดินรอดพ้นจากทะเลเพลิง รับอัญมณีทับทิมโลกันตร์เหล่านี้ไปหลอมอาวุธเถิด!',
      victory: 'ท่านทำสำเร็จแล้ว! วิหารทางเหนือสงบลงแล้ว และหมู่บ้านของเราปลอดภัยด้วยคมดาบและสติปัญญาของท่าน!'
    }
  },
  kael: {
    id: 'kael',
    name: 'ช่างตีเหล็ก คาเอล',
    role: 'ยอดช่างตีเหล็กและสรรพาวุธ',
    portraitType: 'kael',
    dialogues: {
      intro: 'ยินดีต้อนรับสู่เตาหลอมของข้า! นำแร่เหล็ก เขี้ยวสัตว์ และผลึกปีศาจที่เจ้าล่าได้มาให้ข้าสิ ข้าจะตีสุดยอดอาวุธให้เจ้าเอง!',
      q9_intro: 'เฮ้สหาย! ลมหนาวผิดธรรมชาติกำลังแช่แข็งสายแร่บนยอดเขาหิมะเยือกแข็ง (Frostpeak) ทางตะวันออกเฉียงเหนือ! แร่ของข้าถูกแช่แข็งหมดเพราะ "จอมอสูรไททันน้ำแข็ง ฟรอสต์แฟงก์" ตื่นขึ้นมา! ไปทุบมันให้แหลก แล้วนำ "แก่นเหมันต์ไททันน้ำแข็ง" มาให้ข้า ข้าจะตีค้อนยักษ์ระดับมหาตำนานให้เจ้า!',
      q9_progress: 'พายุหิมะบนยอดเขาหนาวเหน็บจับขั้วหัวใจ จงใช้อาวุธธาตุไฟอย่างดาบเพลิงลาวาฟันทะลวงเกราะน้ำแข็งของมันนะ!',
      q9_complete: 'โอ้โห! แก่นเหมันต์พันปีช่างงดงามและเย็นยะเยือกจับตา! ค้อนเหมันต์ไททันน้ำแข็งพร้อมตีขึ้นรูปในเตาหลอมแล้ว รับผลึกน้ำแข็งบริสุทธิ์เหล่านี้ไปเป็นรางวัลเถิด!',
      forge_ready: 'ต้องการให้ข้าตีอาวุธ ปืนล่าสัตว์ หรือดาบศักดิ์สิทธิ์ชิ้นไหนล่ะ? วัตถุดิบพร้อมหรือยัง?'
    }
  },
  eldrin: {
    id: 'eldrin',
    name: 'ผู้เฒ่าปราชญ์ เอลดริน',
    role: 'นักปราชญ์เวทมนตร์แห่งพงไพร',
    portraitType: 'eldrin',
    dialogues: {
      intro: 'โฮ่โฮ่... พืชผลในฟาร์มของเจ้าเติบโตงดงามยิ่งนัก แต่จงรู้ไว้เถิด ใต้ผืนดินวิหารทางเหนือนั้น มีราชินีสปอร์ปีศาจหลับใหลอยู่ เมื่อมันตื่นขึ้น ละอองสปอร์จะเปลี่ยนทุกชีวิตให้กลายเป็นอสูร!',
      lore: 'ราชินีสปอร์แพ้พลังศักดิ์สิทธิ์และแร่ทับทิมโบราณ จงนำแร่และผลึกมานาไปให้ช่างตีเหล็กคาเอลสร้างอาวุธระดับตำนานเสียก่อนจะเข้าไปเผชิญหน้ากับมัน!',
      q4_progress: 'ในถ้ำผลึกใต้พิภพมีรังไหมของตัวอ่อนแมลงยักษ์ จงไปนำผลึกมานาและกำจัดตัวอ่อนเหล่านั้นเสีย!',
      q4_complete: 'ผลึกมานาบริสุทธิ์เหล่านี้จะช่วยสะกดรอยคลื่นพลังของราชินีสปอร์ได้ บัดนี้เส้นทางสู่วิหารเปิดออกแล้ว จงมุ่งหน้าไปเถิด!',
      q6_intro: 'โฮ่โฮ่... แม้คาธูรอสจะสิ้นฤทธิ์ แต่ข้าสัมผัสได้ถึงคลื่นพลังเวทมนตร์อันมหาศาลจากรอยแยกลึกใต้ถ้ำผลึก (The Crystal Abyss Floor -2)! "โกเลมผลึกโบราณ ลูมินาร์ค" ได้ตื่นขึ้นแล้ว จงลงบันไดรอยแยกในถ้ำไปสยบมัน แล้วนำ "หัวใจผลึกปริซึม" กลับมา ข้าจะสอนเคล็ดวิชาดาบเลเซอร์ผลึกให้เจ้า!',
      q6_progress: 'โกเลมลูมินาร์คยิงลำแสงเลเซอร์ปริซึมทะลวงทุกสิ่ง จงจับจังหวะชาร์จพลังแล้วพุ่งหลบด้านข้างนะผู้กล้า!',
      q6_complete: 'มหัศจรรย์ยิ่งนัก! หัวใจผลึกปริซึมส่องแสงรุ้งบริสุทธิ์ บัดนี้ช่างคาเอลสามารถหลอม "ดาบเลเซอร์ผลึกปริซึมลูมินาร์ค" ได้แล้ว รับเพชรประกายรุ้งเหล่านี้ไปเถิด!',
      victory: 'ม่านหมอกสีเลือดสลายไปแล้ว... แผ่นดินได้รับความบริสุทธิ์คืนมาด้วยพลังใจอันกล้าแกร่งของเจ้า!'
    }
  },
  luna: {
    id: 'luna',
    name: 'ลูน่า สาวน้อยร้านดอกไม้',
    role: 'ผู้ดูแลสวนดอกไม้และพรรณไม้งาม (Florist)',
    portraitType: 'luna',
    dialogues: {
      intro: 'สวัสดีจ้ะ! ข้าคือลูน่า สวนดอกไม้ในหมู่บ้านเป็นสถานที่โปรดของข้าเลยล่ะ หากเจ้าปลูกทานตะวันหรือสตรอเบอร์รี่สดๆ ข้าจะดีใจมากๆ เลยนะ!',
      flower_talk: 'ดอกไม้แต่ละชนิดมีความหมายของมันนะ... ทานตะวันคือความสดใส ส่วนช่อดอกไม้บูเกต์คือสัญลักษณ์แห่งความรักอันบริสุทธิ์จ้ะ!',
      dating: 'ช่วงเวลาที่ได้เดินเคียงข้างเจ้าในทุ่งดอกไม้ คือช่วงเวลาที่มีความสุขที่สุดในชีวิตข้าเลยนะ...',
      married: 'อรุณสวัสดิ์นะที่รัก! วันนี้อากาศสดใสมาก ข้าทำแพนเค้กหอมกรุ่นและช่วยรดน้ำแปลงดอกไม้ให้เจ้าเรียบร้อยแล้วจ้ะ!'
    }
  }
};

export const FORGE_RECIPES: Record<string, ForgeRecipe> = {
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
  antidote_serum: {
    id: 'antidote_serum',
    name: 'เซรุ่มต้านสปอร์พิษ (Antidote Serum)',
    desc: 'ฟื้นฟู HP +80 และพลังงาน +50 ช่วยชำระล้างพิษสปอร์',
    cost: 50,
    materials: { blight_spore: 2, starflower_herb: 1 }
  },
  excalibur_sword: {
    id: 'excalibur_sword',
    name: 'ดาบศักดิ์สิทธิ์เอ็กซ์คาลิเบอร์',
    desc: 'ดาบศักดิ์สิทธิ์ ฟันคลื่นแสงทะลวงศัตรู พลังโจมตี 135!',
    cost: 350,
    materials: { demon_heart: 1, ruby_gem: 2, mana_gem: 2 }
  },
  dragon_rifle: {
    id: 'dragon_rifle',
    name: 'ปืนมังกรเพลิง (Dragonfire Cannon)',
    desc: 'ปืนมังกรยิงระเบิดเพลิง พลังโจมตี 160!',
    cost: 450,
    materials: { demon_heart: 1, cursed_wood: 3, ruby_gem: 2 }
  },
  volcano_sword: {
    id: 'volcano_sword',
    name: 'ดาบเพลิงลาวาภูเขาไฟ (Volcano Magma Blade)',
    desc: 'ดาบเพลิงหลอมจากแก่นภูเขาไฟ ฟันติดไฟลุกท่วม พลังโจมตี 180!',
    cost: 550,
    materials: { cinder_shard: 5, dragon_tooth: 1, ruby_gem: 2 }
  },
  luminarch_crystal_blade: {
    id: 'luminarch_crystal_blade',
    name: 'ดาบเลเซอร์ผลึกปริซึมลูมินาร์ค (Prismatic Laser Blade)',
    desc: 'สุดยอดดาบคริสตัลโบราณ ปลดปล่อยเลเซอร์ปริซึมทะลวง พลังโจมตี 195!',
    cost: 550,
    materials: { luminarch_crystal_heart: 1, diamond_crystal: 2, gold_ore: 4 }
  },
  hydra_venom_bow: {
    id: 'hydra_venom_bow',
    name: 'คันธนูสามศรพิษพญาไฮดรา (Hydra Venom Bow)',
    desc: 'คันธนูบึงพิษ แผลงศรกรดพิษกระจาย 3 ดอกพร้อมกัน พลังโจมตี 110x3!',
    cost: 600,
    materials: { hydra_venom_gland: 1, hydra_scale: 4, swamp_herb: 3 }
  },
  volcano_magma_axe: {
    id: 'volcano_magma_axe',
    name: 'ขวานเพลิงโลกันตร์ลาวาอิกนิสทรอน (Molten Magma Axe)',
    desc: 'ขวานหินลาวาคู่ ปลดปล่อยระเบิดเพลิงล้างผลาญ พลังโจมตี 230!',
    cost: 750,
    materials: { magma_dragon_horn: 1, flame_heart: 2, ruby_gem: 4 }
  },
  glacial_titan_hammer: {
    id: 'glacial_titan_hammer',
    name: 'ค้อนเหมันต์ไททันน้ำแข็งฟรอสต์แฟงก์ (Glacial Titan Hammer)',
    desc: 'ค้อนน้ำแข็งพันปี ทุบคลื่นหอกน้ำแข็งแช่แข็ง พลังโจมตี 240!',
    cost: 800,
    materials: { glacial_titan_core: 1, frost_crystal: 4, diamond_crystal: 2 }
  },
  malakor_soul_scythe: {
    id: 'malakor_soul_scythe',
    name: 'เคียวมรณะสูบวิญญาณลอร์ดมาลาคอร์ (Malakor Soul Scythe)',
    desc: 'เคียวแห่งความตาย ปล่อยคลื่นกะโหลกมืด และดูดเลือด 8% คืนแก่ผู้ใช้ พลังโจมตี 260!',
    cost: 1000,
    materials: { death_lord_soul: 1, cursed_relic: 3, crown_of_despair: 1 }
  },
  sylvan_bow: {
    id: 'sylvan_bow',
    name: 'คันธนูใบไม้พฤกษาพันปี (Ancient Sylvan Bow)',
    desc: 'คันธนูแห่งเทพพฤกษา แผลงศรใบไม้คมกริบ 4 ดอกรูปพัด ทะลวงศัตรู พลังโจมตี 160x4!',
    cost: 1150,
    materials: { ancient_tree_heart: 1, cursed_wood: 4, star_fruit: 3 }
  },
  tempest_blade: {
    id: 'tempest_blade',
    name: 'ดาบอัสนีบาตคลื่นสายฟ้า (Tempest Lightning Blade)',
    desc: 'สุดยอดดาบสายฟ้าแห่งจ้าวพายุ ปล่อยลำแสงสายฟ้าผ่าทะลุทะลวง พลังโจมตี 320!',
    cost: 1400,
    materials: { storm_core: 1, thunder_crystal: 5, gold_ore: 5 }
  },
  kathuros_spore_armor: {
    id: 'kathuros_spore_armor',
    name: 'เกราะสปอร์ราชันคาธูรอส (Spore Mail)',
    desc: '[ชุดเกราะบอส] พลังป้องกัน +50% เมื่อโดนโจมตีจะระเบิดหนามสปอร์สวนกลับศัตรู 45 ดาเมจ',
    cost: 800,
    materials: { demon_heart: 1, iron_ore: 5, ruby_gem: 2 }
  },
  ignistron_flame_shield: {
    id: 'ignistron_flame_shield',
    name: 'โล่อัคคีพิโรธอิกนิสทรอน (Magma Shield)',
    desc: '[โล่บอส] เมื่อทำการ Perfect Parry สำเร็จ จะระเบิดคลื่นเพลิงลาวาพุ่งเผาศัตรู 110 ดาเมจ',
    cost: 950,
    materials: { magma_dragon_horn: 1, flame_heart: 2, iron_ore: 6 }
  },
  frostfang_frozen_plate: {
    id: 'frostfang_frozen_plate',
    name: 'เกราะเกล็ดหิมะฟรอสต์แฟงก์ (Glacial Plate)',
    desc: '[ชุดเกราะบอส] การยกโล่บล็อกลดความเสียหาย 80% (จากปกติ 65%) และสะท้อนไอเย็นแช่แข็งศัตรู',
    cost: 950,
    materials: { glacial_titan_core: 1, frost_crystal: 4, diamond_crystal: 2 }
  },
  astreon_storm_greaves: {
    id: 'astreon_storm_greaves',
    name: 'เกราะขาอัสนีบาตออสทริออน (Storm Greaves)',
    desc: '[อุปกรณ์บอส] ความเร็วเคลื่อนที่ +30% และเมื่อกลิ้งหลบ Dash จะฟาดสายฟ้าผ่าใส่ศัตรู 60 ดาเมจ',
    cost: 850,
    materials: { storm_core: 1, thunder_crystal: 4, gold_ore: 5 }
  },
  malakor_void_cloak: {
    id: 'malakor_void_cloak',
    name: 'ผ้าคลุมมฤตยูลอร์ดมาลาคอร์ (Void Shroud)',
    desc: '[ชุดเกราะบอส] ขยายหน้าต่าง Perfect Parry เพิ่ม +80ms และดูดเลือด 6% จากความเสียหายที่ทำได้',
    cost: 1200,
    materials: { death_lord_soul: 1, cursed_relic: 3, crown_of_despair: 1 }
  },
  hydrakis_venom_pendant: {
    id: 'hydrakis_venom_pendant',
    name: 'จี้เขี้ยวพิษพญาไฮดรา (Venom Amulet)',
    desc: '[อุปกรณ์บอส] ป้องกันความเสียหายจากพิษและบึงมลทิน 100% พร้อมเคลือบพิษให้การโจมตี',
    cost: 750,
    materials: { hydra_venom_gland: 1, hydra_scale: 4, swamp_herb: 4 }
  },
  health_potion: {
    id: 'health_potion',
    name: 'ยาฟื้นพลังชีวิตชั้นเลิศ',
    desc: 'ฟื้นฟู HP +60 และพลังงาน +30',
    cost: 40,
    materials: { starflower_herb: 2 }
  },
  ring_glow: {
    id: 'ring_glow',
    name: 'แหวนเรืองแสงสุริยัน (Sun Glow Ring)',
    desc: 'ส่องรัศมีแสงสว่างรอบตัวในถ้ำมืดและสุสานใต้ดิน (+80 รัศมีแสง)',
    cost: 300,
    materials: { gold_ore: 3, ruby_gem: 1 }
  },
  ring_magnet: {
    id: 'ring_magnet',
    name: 'แหวนแม่เหล็กดูดทรัพย์ (Magneto Ring)',
    desc: 'ดูดไอเทมที่ตกบนพื้นเข้าหาตัวจากระยะไกลขึ้น 3 เท่า!',
    cost: 350,
    materials: { iron_ore: 4, crystal_core: 2 }
  },
  ring_warrior: {
    id: 'ring_warrior',
    name: 'แหวนนักรบผู้กล้า (Warrior Bravery Ring)',
    desc: 'เพิ่มโอกาสติดคริติคอล +18% และความแรงคริติคอล 2.2 เท่า',
    cost: 500,
    materials: { iron_ore: 5, ruby_gem: 2, wolf_fang: 2 }
  },
  ring_vampiric: {
    id: 'ring_vampiric',
    name: 'แหวนแวมไพร์สูบโลหิต (Vampiric Leech Ring)',
    desc: 'ดูดเลือด 4% จากความเสียหายที่ทำได้ คืนเป็นพลังชีวิต',
    cost: 650,
    materials: { cursed_wood: 3, bat_wing: 4, blight_spore: 2 }
  },
  ring_lucky: {
    id: 'ring_lucky',
    name: 'แหวนนำโชคจอมพราน (Fortune Hunter Ring)',
    desc: 'มอนสเตอร์ดรอปทองเพิ่มขึ้น +35% และเพิ่มโอกาสได้ไอเทมหายาก',
    cost: 550,
    materials: { gold_ore: 4, diamond_crystal: 1 }
  },

  // สลักรูนเวทมนตร์ (Elemental Runes)
  rune_fire: {
    id: 'rune_fire',
    name: 'รูนอัคคีพิโรธ (Fire Rune)',
    desc: 'สลักรูนเพลิงลงอาวุธ โจมตีติดสถานะเผาไหม้ (Burn DoT 3 ครั้ง)',
    cost: 300,
    materials: { ruby_gem: 2, cinder_shard: 2 }
  },
  rune_frost: {
    id: 'rune_frost',
    name: 'รูนเหมันต์นิรันดร์ (Frost Rune)',
    desc: 'สลักรูนน้ำแข็งลงอาวุธ แช่แข็งสโลว์ความเร็วศัตรูลง 50%',
    cost: 300,
    materials: { frost_crystal: 2, diamond_crystal: 1 }
  },
  rune_lightning: {
    id: 'rune_lightning',
    name: 'รูนอัสนีบาต (Lightning Rune)',
    desc: 'สลักรูนสายฟ้าลงอาวุธ สร้างประกายสายฟ้าชิ่งศัตรูรอบข้าง',
    cost: 300,
    materials: { mana_gem: 2, gold_ore: 3 }
  },
  rune_vampiric: {
    id: 'rune_vampiric',
    name: 'รูนกลืนวิญญาณ (Vampiric Rune)',
    desc: 'สลักรูนสูบวิญญาณลงอาวุธ ฟื้นฟู HP คืน 8% ของความเสียหาย',
    cost: 400,
    materials: { demon_heart: 1, wolf_fang: 3 }
  }
};

// ========================================================
// NPC GIFTS & FRIENDSHIP PREFERENCES
// ========================================================
export const NPC_GIFTS: Record<string, {
  loved: string[];
  liked: string[];
  disliked: string[];
  lovedQuote: string;
  likedQuote: string;
  dislikedQuote: string;
}> = {
  gilbert: {
    loved: ['fine_wine', 'cheese', 'aged_cheese', 'pizza'],
    liked: ['bread', 'wheat', 'corn', 'diamond_crystal'],
    disliked: ['blight_spore', 'beetle_shell', 'stone'],
    lovedQuote: 'โอ้โห! ของขวัญชั้นยอดแบบนี้หาได้ยากยิ่งนัก ขอบใจเจ้ามากสหายชาวสวน!',
    likedQuote: 'ขอบใจนะ! ข้าจะนำสิ่งนี้ไปแบ่งปันกับชาวเมือง',
    dislikedQuote: 'เอ่อ... ข้าคิดว่าของสิ่งนี้น่าจะเหมาะกับผู้อื่นมากกว่านะ'
  },
  lilian: {
    loved: ['starflower_herb', 'strawberry', 'strawberry_jam', 'antidote_serum', 'bouquet', 'mermaids_amulet'],
    liked: ['tomato', 'carrot', 'mana_gem', 'milk', 'pineapple'],
    disliked: ['blight_spore', 'demon_wing', 'bat_wing'],
    lovedQuote: 'ว้าว! สมุนไพรและของขวัญที่แสนอ่อนโยนนี้... ข้าชอบมากที่สุดเลยจ้ะ ขอบคุณนะ!',
    likedQuote: 'ขอบคุณมากจ้ะ สิ่งนี้มีประโยชน์ต่อการวิจัยยาของข้ามากเลย',
    dislikedQuote: 'อุ๊ย! กลิ่นฉุนของเศษชิ้นส่วนพวกนี้ทำให้ข้าเวียนหัวจ้ะ...'
  },
  valeria: {
    loved: ['iron_sword', 'ruby_gem', 'fine_wine', 'grilled_fish', 'volcano_sword', 'bouquet', 'mermaids_amulet'],
    liked: ['iron_ore', 'gold_ore', 'spicy_fish_soup', 'bacon', 'cinder_shard'],
    disliked: ['blight_spore', 'wool', 'egg'],
    lovedQuote: 'ยอดเยี่ยมมาก! ของขวัญที่ตราตรึงและคู่ควรกับใจข้า... ข้าสัญญาว่าจะอยู่เคียงข้างเจ้าเสมอ!',
    likedQuote: 'ขอบใจนะสหาย! เสบียงและแร่เหล่านี้จำเป็นสำหรับแนวรบมาก',
    dislikedQuote: 'ข้าเป็นทหารปกป้องเมือง ของหยุมหยิมพวกนี้ข้าคงไม่ได้ใช้หรอก'
  },
  kael: {
    loved: ['gold_ore', 'diamond_crystal', 'star_core', 'craft_ale', 'volcano_sword', 'bouquet', 'mermaids_amulet'],
    liked: ['iron_ore', 'copper_ore', 'coal', 'stone', 'cinder_shard'],
    disliked: ['strawberry', 'flower', 'cake'],
    lovedQuote: 'ฮ่าฮ่าฮ่า! ช่างงดงามและเลอค่ายิ่งนัก! เจ้าช่างรู้ใจข้าที่สุดในโลกเลย!',
    likedQuote: 'แร่เนื้อดี ข้าจะนำไปหลอมอาวุธคมกริบ ขอบใจเจ้ามาก!',
    dislikedQuote: 'อะไรเนี่ย? ของหวานเลอะเทอะ เดี๋ยวเตาหลอมข้าก็ดับพอดี!'
  },
  luna: {
    loved: ['sunflower', 'strawberry', 'bouquet', 'mermaids_amulet', 'strawberry_jam'],
    liked: ['starflower_herb', 'bread', 'pineapple', 'milk', 'coconut'],
    disliked: ['stone', 'blight_spore', 'bat_wing'],
    lovedQuote: 'โอ้พระเจ้า! ดอกไม้และความรักนี้ช่างงดงามเหลือเกิน... ใจฉันเต้นแรงจัง ขอบคุณมากนะจ๊ะ!',
    likedQuote: 'ขอบคุณมากนะจ๊ะ สิ่งนี้น่ารักและสดชื่นมากเลย!',
    dislikedQuote: 'อ๊ะ... ของแบบนี้น่ากลัวจัง ฉันไม่ค่อยชอบเลยจ้ะ'
  },
  bob: {
    loved: ['grilled_fish', 'spicy_fish_soup', 'craft_ale', 'fine_wine'],
    liked: ['tilapia', 'catfish', 'carp', 'cheese', 'bread'],
    disliked: ['stone', 'beetle_shell', 'bat_wing'],
    lovedQuote: 'สุดยอดไปเลยเกลอ! ทั้งกับแกล้มทั้งเครื่องดื่มรสเด็ด วันนี้ข้าขอเลี้ยงโต๊ะเจ้า!',
    likedQuote: 'ขอบใจมากเพื่อนรัก วัตถุดิบสดๆ แบบนี้โรงเตี๊ยมข้าต้องการอยู่พอดี!',
    dislikedQuote: 'เฮ้ๆ อย่าเอาของอันตรายหรือเศษหินมาวางบนโต๊ะอาหารสิเพื่อน!'
  },
  eldrin: {
    loved: ['mana_gem', 'diamond_crystal', 'star_core', 'ancient_glowfish'],
    liked: ['ruby_gem', 'starflower_herb', 'antidote_serum'],
    disliked: ['stone', 'wood', 'bacon'],
    lovedQuote: 'โฮ่โฮ่... พลังงานเวทมนตร์อันบริสุทธิ์เปล่งประกาย สัมผัสถึงความลับแห่งจักรวาล!',
    likedQuote: 'จิตวิญญาณแห่งผืนป่าตอบรับของขวัญชิ้นนี้ ขอบใจเจ้ามากผู้มีปัญญา',
    dislikedQuote: 'สิ่งของทางโลกียะเหล่านี้ ไม่อาจเทียบเคียงแก่นแท้แห่งเวทมนตร์ได้'
  }
};

// ========================================================
// MUSEUM COMPENDIUM & COLLECTION ITEMS
// ========================================================
export const COMPENDIUM_CATEGORIES = {
  crops: {
    name: 'พืชผลการเกษตร',
    items: ['wheat', 'carrot', 'corn', 'tomato', 'strawberry', 'pumpkin', 'sunflower', 'rice', 'cabbage', 'chili', 'sugarcane']
  },
  fish: {
    name: 'สิ่งมีชีวิตในน้ำ',
    items: ['carp', 'tilapia', 'catfish', 'golden_salmon', 'ancient_glowfish']
  },
  minerals: {
    name: 'แร่ธาตุและอัญมณี',
    items: ['stone', 'copper_ore', 'iron_ore', 'gold_ore', 'ruby_gem', 'mana_gem', 'diamond_crystal', 'star_core']
  },
  artisan: {
    name: 'สินค้าแปรรูป & ครัว',
    items: ['mayonnaise', 'aged_cheese', 'strawberry_jam', 'pickled_carrot', 'fine_wine', 'craft_ale', 'bread', 'pizza', 'grilled_fish', 'spicy_fish_soup']
  }
};

// ========================================================
// ACHIEVEMENTS & MILESTONES
// ========================================================
export const ACHIEVEMENTS_DATA = [
  { id: 'first_harvest', name: 'ก้าวแรกชาวสวน', desc: 'เก็บเกี่ยวผลผลิตจากแปลงผักแปลงแรก', icon: '★', rewardGold: 100 },
  { id: 'master_farmer', name: 'ราชาแห่งทุ่งรวงทอง', desc: 'เก็บเกี่ยวผลผลิตสะสมครบ 50 ครั้ง', icon: '★', rewardGold: 500 },
  { id: 'mine_explorer_5', name: 'ผู้กล้าถ้ำลึก (ชั้น 5)', desc: 'พิชิตและปลดล็อกลิฟต์เหมืองชั้นที่ 5', icon: '★', rewardGold: 300 },
  { id: 'mine_explorer_10', name: 'นักดำดิ่งผลึกคราม (ชั้น 10)', desc: 'พิชิตและปลดล็อกลิฟต์เหมืองชั้นที่ 10', icon: '★', rewardGold: 600 },
  { id: 'mine_explorer_20', name: 'ผู้พิชิตแก่นดวงดาว (ชั้น 20)', desc: 'เดินทางถึงเหมืองชั้นลึกสุดชั้นที่ 20', icon: '★', rewardGold: 1500 },
  { id: 'pet_lover', name: 'เพื่อนแท้สี่ขา', desc: 'มีสัตว์เลี้ยงคู่หู (น้องหมาหรือน้องแมว) คอยเดินตาม', icon: '★', rewardGold: 200 },
  { id: 'horse_rider', name: 'อาชาไนยแห่งหุบเขา', desc: 'ขึ้นขี่ม้าพาหนะคู่ใจ', icon: '★', rewardGold: 300 },
  { id: 'artisan_master', name: 'ช่างแปรรูปมือฉมัง', desc: 'แปรรูปสินค้าสำเร็จ (ไวน์, แยม, มายองเนส, ชีส) ครบ 10 ชิ้น', icon: '★', rewardGold: 400 },
  { id: 'town_favorite', name: 'ขวัญใจชาวเมือง', desc: 'ผูกมิตรกับชาวเมืองจนมีหัวใจ 3 ดวงขึ้นไป', icon: '★', rewardGold: 500 },
  { id: 'boss_slayer', name: 'วีรบุรุษผู้กอบกู้', desc: 'ปราบราชาปีศาจคาธูรอสในวิหารโบราณ', icon: '★', rewardGold: 2000 }
];

// ========================================================
// ARTISAN CONVERSION RECIPES
// ========================================================
export const ARTISAN_CONVERSIONS: Record<string, {
  machineType: 'mayo_machine' | 'cheese_press' | 'preserves_jar' | 'wine_keg';
  inputItem: string;
  outputItem: string;
  outputName: string;
  durationMs: number;
}> = {
  egg_to_mayo: {
    machineType: 'mayo_machine',
    inputItem: 'egg',
    outputItem: 'mayonnaise',
    outputName: 'มายองเนสเข้มข้น',
    durationMs: 8000
  },
  milk_to_cheese: {
    machineType: 'cheese_press',
    inputItem: 'milk',
    outputItem: 'aged_cheese',
    outputName: 'เชดดาร์ชีสบ่มพิเศษ',
    durationMs: 10000
  },
  strawberry_to_jam: {
    machineType: 'preserves_jar',
    inputItem: 'strawberry',
    outputItem: 'strawberry_jam',
    outputName: 'แยมสตรอเบอร์รี่หวานฉ่ำ',
    durationMs: 9000
  },
  carrot_to_pickle: {
    machineType: 'preserves_jar',
    inputItem: 'carrot',
    outputItem: 'pickled_carrot',
    outputName: 'ผักดองแครอทกรอบ',
    durationMs: 7000
  },
  fruit_to_wine: {
    machineType: 'wine_keg',
    inputItem: 'strawberry',
    outputItem: 'fine_wine',
    outputName: 'ไวน์ผลไม้ชั้นเลิศ',
    durationMs: 14000
  },
  wheat_to_ale: {
    machineType: 'wine_keg',
    inputItem: 'wheat',
    outputItem: 'craft_ale',
    outputName: 'เบียร์สดข้าวสาลีคราฟต์',
    durationMs: 11000
  },
  pineapple_to_wine: {
    machineType: 'wine_keg',
    inputItem: 'pineapple',
    outputItem: 'fine_wine',
    outputName: 'ไวน์สับปะรดทองคำพรีเมียม',
    durationMs: 15000
  },
  coconut_to_jam: {
    machineType: 'preserves_jar',
    inputItem: 'coconut',
    outputItem: 'strawberry_jam',
    outputName: 'แยมมะพร้าวเนื้อนุ่ม',
    durationMs: 9000
  }
};

// ========================================================
// SKILL MASTERY PERKS (TREE [K])
// ========================================================
export interface SkillMasteryPerk {
  id: string;
  branch: 'farming' | 'mining' | 'fishing' | 'combat' | 'artisan';
  branchName: string;
  name: string;
  desc: string;
  icon: string;
  cost: number;
}

export const SKILL_MASTERIES: Record<string, SkillMasteryPerk> = {
  double_harvest: {
    id: 'double_harvest',
    branch: 'farming',
    branchName: 'กสิกรรมขั้นเทพ (Farming Mastery)',
    name: 'ผลผลิตทวีคูณ (Double Harvest)',
    desc: 'มีโอกาส 25% ที่จะเก็บเกี่ยวพืชผลได้จำนวน 2 เท่าในทุกแปลง',
    icon: '',
    cost: 1
  },
  golden_touch: {
    id: 'golden_touch',
    branch: 'farming',
    branchName: 'กสิกรรมขั้นเทพ (Farming Mastery)',
    name: 'หัตถ์ทองคำ (Golden Touch)',
    desc: 'เพิ่มโอกาสได้พืชผลระดับดาวทองและอิริเดียมขึ้นเป็น 2 เท่า',
    icon: '',
    cost: 1
  },
  gemologist: {
    id: 'gemologist',
    branch: 'mining',
    branchName: 'ปรมาจารย์เหมือง (Mining Mastery)',
    name: 'ผู้เชี่ยวชาญอัญมณี (Gemologist)',
    desc: 'แร่และอัญมณีทุกชนิดขายได้ราคาสูงขึ้น 35%',
    icon: '',
    cost: 1
  },
  geode_cracker: {
    id: 'geode_cracker',
    branch: 'mining',
    branchName: 'ปรมาจารย์เหมือง (Mining Mastery)',
    name: 'สัญชาตญาณสายแร่ (Vein Seeker)',
    desc: 'โอกาสขุดพบแร่ทองคำ ทับทิม และผลึกมานาเพิ่มขึ้น 50%',
    icon: '',
    cost: 1
  },
  master_angler: {
    id: 'master_angler',
    branch: 'fishing',
    branchName: 'จ้าวแห่งสายน้ำ (Fishing Mastery)',
    name: 'สายเบ็ดเซียน (Master Angler)',
    desc: 'แถบตกปลากว้างขึ้น 35% และปลาดิ้นช้าลงอย่างมาก',
    icon: '',
    cost: 1
  },
  treasure_hunter: {
    id: 'treasure_hunter',
    branch: 'fishing',
    branchName: 'จ้าวแห่งสายน้ำ (Fishing Mastery)',
    name: 'นักล่าสมบัติบาดาล (Treasure Hunter)',
    desc: 'มีโอกาสพบหีบสมบัติใต้ทะเลขณะตกปลาเพิ่มขึ้น 2 เท่า',
    icon: '',
    cost: 1
  },
  vampiric_vitality: {
    id: 'vampiric_vitality',
    branch: 'combat',
    branchName: 'วีรชนผู้กล้า (Combat Mastery)',
    name: 'สูบพลังชีวิต (Vampirism)',
    desc: 'ฟื้นฟู HP 8 หน่วยทันทีทุกครั้งที่กำจัดมอนสเตอร์หรือศัตรูสำเร็จ',
    icon: '',
    cost: 1
  },
  critical_edge: {
    id: 'critical_edge',
    branch: 'combat',
    branchName: 'วีรชนผู้กล้า (Combat Mastery)',
    name: 'คมดาบสังหาร (Critical Edge)',
    desc: 'มีโอกาส 20% โจมตีติดคริติคอล สร้างความเสียหาย 2.5 เท่า!',
    icon: '',
    cost: 1
  },
  artisan_expert: {
    id: 'artisan_expert',
    branch: 'artisan',
    branchName: 'ช่างหัตถศิลป์ (Artisan Mastery)',
    name: 'ปรมาจารย์แปรรูป (Artisan Expert)',
    desc: 'สินค้าแปรรูปทั้งหมด (ไวน์, แยม, ชีส, มายองเนส) ขายได้ราคาเพิ่ม 40%',
    icon: '',
    cost: 1
  },
  gourmet_chef: {
    id: 'gourmet_chef',
    branch: 'artisan',
    branchName: 'ช่างหัตถศิลป์ (Artisan Mastery)',
    name: 'ยอดกุ๊กเทวดา (Gourmet Chef)',
    desc: 'อาหารปรุงเองทุกจานฟื้นฟูพลังงานและ HP เพิ่มขึ้น 50%',
    icon: '',
    cost: 1
  }
};

// ========================================================
// SEASONAL FESTIVALS CALENDAR
// ========================================================
export interface FestivalData {
  id: string;
  seasonIndex: number;
  day: number;
  name: string;
  timeText: string;
  desc: string;
  location: string;
}

export const FESTIVALS: Record<string, FestivalData> = {
  spring_egg_hunt: {
    id: 'spring_egg_hunt',
    seasonIndex: 0,
    day: 13,
    name: 'เทศกาลล่าไข่อีสเตอร์ (Egg Hunt Festival)',
    timeText: '09:00 - 14:00 น.',
    desc: 'วิ่งแข่งเก็บไข่อีสเตอร์สีสันสดใสที่ซ่อนอยู่ตามมุมต่างๆ ในหมู่บ้าน ชนะรับถ้วยรางวัลและ 1,000 G!',
    location: 'village'
  },
  summer_fishing_derby: {
    id: 'summer_fishing_derby',
    seasonIndex: 1,
    day: 11,
    name: 'เทศกาลแข่งตกปลาฤดูร้อน (Fishing Derby)',
    timeText: '09:00 - 15:00 น.',
    desc: 'แข่งขันตกปลาที่ชายหาดและท่าเรือ นับแต้มปลาที่ตกได้ ชนะรับเบ็ดตกปลาอิริเดียม!',
    location: 'village'
  },
  fall_harvest_fair: {
    id: 'fall_harvest_fair',
    seasonIndex: 2,
    day: 16,
    name: 'งานประกวดผลผลิตกรังด์ปรีซ์ (Fall Harvest Fair)',
    timeText: '10:00 - 16:00 น.',
    desc: 'นำสุดยอดผลผลิตและสินค้าแปรรูป 9 รายการมาจัดแสดงโชว์ ชนะรับเหรียญดวงดาวแลกของรางวัลหายาก!',
    location: 'village'
  },
  winter_star_night: {
    id: 'winter_star_night',
    seasonIndex: 3,
    day: 25,
    name: 'เทศกาลราตรีดวงดาวฉลองปีใหม่ (Feast of the Winter Star)',
    timeText: '18:00 - 22:00 น.',
    desc: 'รวมตัวรอบต้นคริสต์มาสยักษ์ แลกของขวัญลับกับชาวเมือง และรับคำอวยพรแห่งดวงดาวเพิ่มความสนิทเต็มหัวใจ!',
    location: 'village'
  }
};

// ========================================================
// TAVERN BOUNTY BOARD (กระดานประกาศจับมหาบอสแห่งโรงเตี๊ยมรวงทอง)
// ========================================================
export const BOUNTY_BOARD: Record<string, BountyData> = {
  bounty_kathuros: {
    id: 'bounty_kathuros',
    bossId: 'boss_kathuros',
    title: 'ประกาศจับระดับ S: ราชินีสปอร์ปีศาจ คาธูรอส',
    name: 'ราชินีสปอร์ปีศาจ คาธูรอส (Queen Kathuros)',
    location: 'วิหารโบราณเหนือสุด (Ancient Forest Sanctuary)',
    scene: 'forest',
    desc: 'อสูรโบราณผู้ปล่อยละอองสปอร์สีเลือดกลายพันธุ์แมลงและพืชผล สถิตอยู่ ณ ลานบูชาข้ามสะพานเหนือ',
    weakness: 'แพ้การโจมตีระยะไกล, ให้ระวังวงระเบิดสปอร์หมุนวนและฝูงมินเนี่ยนแมลง',
    rewardGold: 250,
    rewardXp: 300,
    rewardItem: 'demon_heart',
    rewardItemName: 'หัวใจปีศาจโบราณ'
  },
  bounty_luminarch: {
    id: 'bounty_luminarch',
    bossId: 'boss_luminarch',
    title: 'ประกาศจับระดับ SS: โกเลมผลึกโบราณ ลูมินาร์ค',
    name: 'โกเลมผลึกโบราณ ลูมินาร์ค (Prismatic Golem Luminarch)',
    location: 'ถ้ำผลึกลึกชั้นใต้พิภพ (The Crystal Abyss Floor -2)',
    scene: 'cave_depths',
    desc: 'ผู้พิทักษ์แก่นแท้แห่งธาตุผลึก ก่อตัวขึ้นจากพลังงานมานามหาศาล ยิงลำแสงเลเซอร์ปริซึม 7 สี',
    weakness: 'เคลื่อนที่ช้า หลบลำแสงเลเซอร์ชาร์จแล้วฟันสวนด้วยดาบศักดิ์สิทธิ์หรืออาวุธหนัก',
    rewardGold: 380,
    rewardXp: 450,
    rewardItem: 'luminarch_crystal_heart',
    rewardItemName: 'หัวใจผลึกปริซึมลูมินาร์ค'
  },
  bounty_hydrakis: {
    id: 'bounty_hydrakis',
    bossId: 'boss_hydrakis',
    title: 'ประกาศจับระดับ SS: มัจจุราชสามเศียร ไฮดราคิส',
    name: 'มัจจุราชสามเศียรแห่งบึงมืด ไฮดราคิส (Hydrakis the Venom Hydra)',
    location: 'หนองน้ำมืดแดนพิษ (The Gloom Venom Bog)',
    scene: 'swamp',
    desc: 'อสรพิษยักษ์สามเศียรพ่นลูกบอลกรดพิษและสร้างบ่อกรดกัดกร่อนทั่วบริเวณบึงมืด',
    weakness: 'ต้องพกเซรุ่มต้านพิษและซุปเกราะสมุนไพร หลีกเลี่ยงการเหยียบแอ่งกรดเขียว',
    rewardGold: 450,
    rewardXp: 550,
    rewardItem: 'hydra_venom_gland',
    rewardItemName: 'ต่อมพิษพญาไฮดราโบราณ'
  },
  bounty_ignistron: {
    id: 'bounty_ignistron',
    bossId: 'boss_ignistron',
    title: 'ประกาศจับระดับ SSS: ราชันย์มังกรลาวา อิกนิสทรอน',
    name: 'ราชันย์มังกรลาวาเพลิงอัคนี อิกนิสทรอน (Ignistron the Molten Drake)',
    location: 'ปากปล่องภูเขาไฟเพลิงโลกันตร์ (Mount Ignis Molten Caldera)',
    scene: 'volcano',
    desc: 'มังกรเพลิงยักษ์หลับใหลใต้ธารลาวา เมื่อพิโรธจะเรียกระเบิดอุกกาบาตเพลิงถล่มพื้นดิน',
    weakness: 'ดื่มน้ำผลไม้วิเศษสายลมเพื่อวิ่งหลบวงเตือนอุกกาบาต แล้วรัวยิงปืนล่าสัตว์จากระยะปลอดภัย',
    rewardGold: 550,
    rewardXp: 700,
    rewardItem: 'magma_dragon_horn',
    rewardItemName: 'เขามังกรอัคนีเพลิงอิกนิสทรอน'
  },
  bounty_frostfang: {
    id: 'bounty_frostfang',
    bossId: 'boss_frostfang',
    title: 'ประกาศจับระดับ SSS: จอมอสูรไททันน้ำแข็ง ฟรอสต์แฟงก์',
    name: 'จอมอสูรไททันน้ำแข็ง ฟรอสต์แฟงก์ (Frostfang the Glacial Titan)',
    location: 'ยอดเขาหิมะเยือกแข็งพันปี (Frostpeak Blizzard Summit)',
    scene: 'frost_peak',
    desc: 'ยักษ์น้ำแข็งศิลาผู้บัญชาการพายุหิมะ มีเกราะผลึกน้ำแข็งสะท้อนการโจมตีและทุบพื้นเป็นหนามน้ำแข็ง',
    weakness: 'ใช้อาวุธธาตุเพลิง (เช่น ดาบเพลิงลาวา หรือขวานอิกนิสทรอน) เพื่อทำดาเมจทะลวงเกราะน้ำแข็ง',
    rewardGold: 650,
    rewardXp: 800,
    rewardItem: 'glacial_titan_core',
    rewardItemName: 'แก่นเหมันต์ไททันน้ำแข็ง'
  },
  bounty_malakor: {
    id: 'bounty_malakor',
    bossId: 'boss_malakor',
    title: 'ประกาศจับระดับ MYTHIC: ลอร์ดมรณะกระดูกอสูร มาลาคอร์',
    name: 'ลอร์ดมรณะกระดูกอสูร มาลาคอร์ (Lord Malakor the Undead Overlord)',
    location: 'สุสานใต้พิภพต้องสาป (The Nether Crypt Tomb of Kings)',
    scene: 'crypt',
    desc: 'จอมบงการผู้อยู่เบื้องหลังคำสาปสปอร์มรณะ ควบคุมวิญญาณคนตายและปลดปล่อยคลื่นพลังแห่งความมืด',
    weakness: 'เตรียมสตูว์เนื้อผักและซุปเกราะสมุนไพรเต็มอัตรา สลับการฟันประชิดและการยิงระยะไกลอย่างต่อเนื่อง',
    rewardGold: 800,
    rewardXp: 1000,
    rewardItem: 'death_lord_soul',
    rewardItemName: 'ดวงวิญญาณมรณะลอร์ดมาลาคอร์'
  },
  bounty_sylvanus: {
    id: 'bounty_sylvanus',
    bossId: 'boss_sylvanus',
    title: 'ประกาศจับระดับ ANCIENT: เทพพฤกษาบรรพกาล ซิลวาเนีย',
    name: 'เทพพฤกษาบรรพกาล ซิลวาเนีย (Sylvanus Ancient Deity)',
    location: 'ป่าพฤกษาศักดิ์สิทธิ์โบราณลึกสุด (Ancient Sacred Canopy)',
    scene: 'ancient_canopy',
    desc: 'พฤกษาเทวีโบราณผู้พิทักษ์ป่าลึก ปลดปล่อยดงหนามพิโรธ ระเบิดกลีบดอกไม้สังหาร และยิงลำแสงสุริยันทำลายล้าง',
    weakness: 'กลิ้งแดชหลบลำแสงสุริยัน ทำลายดอกไม้ตูมฮีลที่งอกขึ้นมาเพื่อขัดขวางการฟื้นฟูเลือด',
    rewardGold: 950,
    rewardXp: 1200,
    rewardItem: 'ancient_tree_heart',
    rewardItemName: 'หัวใจพฤกษาบรรพกาล'
  },
  bounty_astreon: {
    id: 'bounty_astreon',
    bossId: 'boss_astreon',
    title: 'ประกาศจับระดับ GODLIKE: จ้าวแห่งพายุสายฟ้า ออสทริออน',
    name: 'จ้าวแห่งพายุสายฟ้า ออสทริออน (Astreon Tempest Sovereign)',
    location: 'ที่ราบสูงอัสนีบาตและยอดเขาพายุ (Tempest Lightning Plateau)',
    scene: 'tempest_plateau',
    desc: 'ราชันย์แห่งสายฟ้า เคลื่อนที่ด้วยความเร็วแสง ขึงตาข่ายเสาสายฟ้าช็อตตรึง และเรียกอสุนีบาตผ่าลงมาอย่างต่อเนื่อง',
    weakness: 'สังเกตวงเตือนสายฟ้าผ่าสีทองบนพื้น ห้ามเดินเฉียดเสาล่อฟ้าที่เชื่อมกระแสไฟฟ้า',
    rewardGold: 1200,
    rewardXp: 1500,
    rewardItem: 'storm_core',
    rewardItemName: 'แก่นอัสนีบาตคำราม'
  }
};


export interface HeartEventChoice {
  text: string;
  response: string;
  friendshipBonus: number;
}

export interface HeartEventData {
  id: string;
  npcId: string;
  requiredHearts: number;
  title: string;
  story: string;
  choices: HeartEventChoice[];
  rewardDesc: string;
  rewardType: 'hp' | 'damage' | 'energy' | 'recipe' | 'gold';
  rewardValue: number;
}

export const NPC_HEART_EVENTS: Record<string, HeartEventData> = {
  lilian_2: {
    id: 'lilian_2',
    npcId: 'lilian',
    requiredHearts: 2,
    title: 'ชาสมุนไพรสูตรลับของลิเลียน (Heart 2)',
    story: 'ลิเลียนกำลังต้มชากลิ่นหอมฟุ้งในคลินิก เธอหันมายิ้มอย่างอบอุ่น: "เจ้ามาพอดีเลย! ข้ากำลังทดลองสูตรชาสมุนไพรบำรุงชีพจรอยู่พอดี อยากให้เจ้าช่วยลองชิมหน่อย จะได้ไหม?"',
    choices: [
      { text: '"ยินดีอย่างยิ่ง กลิ่นหอมอบอุ่นมาก!"', response: 'ลิเลียนยิ้มแก้มแดง: "รสหวานชุ่มคอใช่ไหมล่ะ? ชานี้จะช่วยให้ร่างกายของเจ้าแข็งแกร่งขึ้นนะ!"', friendshipBonus: 50 },
      { text: '"จะปลอดภัยแน่ใช่ไหมเนี่ย...?"', response: 'ลิเลียนหัวเราะเบาๆ: "แหม ข้าเป็นหมอยานะ ไม่วางยาพิษเพื่อนหรอกน่า! ดื่มแล้วสดชื่นแน่นอน"', friendshipBonus: 25 }
    ],
    rewardDesc: 'Max HP ถาวร +10!',
    rewardType: 'hp',
    rewardValue: 10
  },
  lilian_4: {
    id: 'lilian_4',
    npcId: 'lilian',
    requiredHearts: 4,
    title: 'คำสัญญาใต้ต้นสมุนไพรโบราณ (Heart 4)',
    story: 'ลิเลียนพาคุณเดินไปที่ทุ่งดอกไม้นอกคลินิก ลมพัดเส้นผมของเธอพลิ้วไหว: "ตั้งแต่เจ้ามาที่หุบเขาแห่งนี้... ทั้งคลินิกและหัวใจของข้าก็ไม่เคยเงียบเหงาอีกเลย ขอบคุณที่คอยอยู่เคียงข้างข้านะ"',
    choices: [
      { text: '"ข้าสัญญาว่าจะคอยปกป้องเจ้าเสมอ"', response: 'ลิเลียนก้มหน้าเขินอายอย่างมีความสุข: "ข้าเชื่อมั่นในตัวเจ้าเสมอ... เจ้าคือคนพิเศษของข้า"', friendshipBonus: 80 },
      { text: '"เราเป็นคู่หูที่ยอดเยี่ยมที่สุดในหุบเขา!"', response: 'ลิเลียนยิ้มสดใส: "ใช่แล้ว! พลังแห่งความร่วมมือของเราไม่มีใครเทียบได้!"', friendshipBonus: 40 }
    ],
    rewardDesc: 'Max HP ถาวร +15!',
    rewardType: 'hp',
    rewardValue: 15
  },
  valeria_2: {
    id: 'valeria_2',
    npcId: 'valeria',
    requiredHearts: 2,
    title: 'บทเรียนเพลงดาบแห่งปราการเหนือ (Heart 2)',
    story: 'ผู้กองวาเลเรียกำลังฝึกซ้อมดาบอย่างดุดันที่ลานหิน เธอปักดาบลงดินแล้วหันมามองคุณด้วยสายตามุ่งมั่น: "เจ้ามีแววตานักรบที่ยอดเยี่ยมมาก มาประลองดาบกับข้าสักยกเถอะ! ข้าจะชี้แนะเคล็ดวิชาจับดาบให้"',
    choices: [
      { text: '"น้อมรับคำชี้แนะ พร้อมเสมอครับผู้กอง!"', response: 'วาเลเรียพยักหน้าอย่างชื่นชม: "ยอดเยี่ยม! สมาธิมั่นคง ดาบมีพลัง! จำความรู้สึกนี้ไว้"', friendshipBonus: 50 },
      { text: '"ออมมือให้ข้าด้วยนะ"', response: 'วาเลเรียหัวเราะหึๆ: "ในสนามรบไม่มีใครออมมือหรอก แต่สำหรับเจ้า... ข้าจะค่อยๆ สอน"', friendshipBonus: 30 }
    ],
    rewardDesc: 'พลังโจมตีพื้นฐานถาวร +5!',
    rewardType: 'damage',
    rewardValue: 5
  },
  valeria_4: {
    id: 'valeria_4',
    npcId: 'valeria',
    requiredHearts: 4,
    title: 'ตราเกียรติยศแห่งอัศวินคู่กาย (Heart 4)',
    story: 'วาเลเรียเรียกคุณไปที่หอสังเกตการณ์ยามเย็น เธอปลดเข็มกลัดตราสิงโตเหล็กออกจากเกราะแล้วยื่นให้คุณ: "มีเพียงคนที่ข้าไว้วางใจจะฝากแผ่นหลังให้ได้เท่านั้นที่จะได้สิ่งนี้... เจ้าคือสหายที่สำคัญที่สุดของข้า"',
    choices: [
      { text: '"ข้าจะติดตรานี้ไว้ใกล้หัวใจเสมอ"', response: 'วาเลเรียมองตาคุณลึกซึ้ง: "ข้ารู้ว่าเจ้าจะไม่ทำให้ข้าผิดหวัง... ร่วมสู้ไปด้วยกันนะ"', friendshipBonus: 80 },
      { text: '"เป็นเกียรติอย่างยิ่งครับผู้กอง"', response: 'วาเลเรียยิ้มมุมปาก: "ไม่ต้องเป็นทางการนักก็ได้ เมื่ออยู่กับข้าสองคน เจ้าคือคนพิเศษ"', friendshipBonus: 50 }
    ],
    rewardDesc: 'พลังโจมตีพื้นฐานถาวร +10!',
    rewardType: 'damage',
    rewardValue: 10
  },
  bob_2: {
    id: 'bob_2',
    npcId: 'bob',
    requiredHearts: 2,
    title: 'สูตรเครื่องดื่มแห่งความสุขของบ็อบ (Heart 2)',
    story: 'บ็อบกำลังเช็ดแก้วอยู่ที่เคาน์เตอร์โรงเตี๊ยม พลางฮัมเพลงอย่างสบายอารมณ์: "เฮ้สหาย! วันนี้ข้าหมักเบียร์สูตรข้าวสาลีพิเศษได้สำเร็จ รสชาตินุ่มละมุนมาก มานั่งตรงนี้แล้วยกแก้วฉลองกันสักหน่อยสิ!"',
    choices: [
      { text: '"หมดแก้วเพื่อมิตรภาพของเรา!"', response: 'บ็อบตบโต๊ะดังลั่นด้วยความสะใจ: "ฮ่าๆๆ! ดื่มแบบนี้สิถึงจะเรียกว่ายอดสหาย! เอาเบียร์สูตรพิเศษไปติดตัวเลย"', friendshipBonus: 50 },
      { text: '"ขอจิบช้าๆ ลิ้มรสชาติดีกว่า"', response: 'บ็อบยิ้มกว้าง: "คนมีรสนิยม! เจ้าเข้าใจศาสตร์แห่งการหมักอย่างแท้จริง"', friendshipBonus: 35 }
    ],
    rewardDesc: 'Max Energy ถาวร +15!',
    rewardType: 'energy',
    rewardValue: 15
  },
  bob_4: {
    id: 'bob_4',
    npcId: 'bob',
    requiredHearts: 4,
    title: 'เรื่องเล่าใต้แสงดาวของบ็อบ (Heart 4)',
    story: 'โรงเตี๊ยมปิดแล้ว บ็อบนั่งผิงไฟกับคุณ: "ข้าเคยเดินทางไปมาครึ่งโลก แต่ไม่มีที่ไหนทำให้ข้ารู้สึกอบอุ่นเหมือนที่นี่เลย... และข้าดีใจจริงๆ ที่ได้รู้จักเจ้า เจ้าทำให้โรงเตี๊ยมนี้มีชีวิตชีวา"',
    choices: [
      { text: '"ข้าก็ดีใจที่มีบ็อบคอยต้อนรับเสมอ"', response: 'บ็อบตบบ่าคุณเบาๆ อย่างจริงใจ: "ประตูโรงเตี๊ยมของข้าเปิดรับเจ้าเสมอ ไม่ว่าจะเกิดอะไรขึ้น"', friendshipBonus: 80 },
      { text: '"โรงเตี๊ยมของบ็อบคือที่พักใจที่ดีที่สุด"', response: 'บ็อบยิ้มอบอุ่น: "ได้ยินแบบนี้ข้าก็หายเหนื่อยแล้ว ขอบใจมากนะเพื่อนรัก"', friendshipBonus: 50 }
    ],
    rewardDesc: 'Max Energy ถาวร +25 และทองคำ 1,000 G!',
    rewardType: 'energy',
    rewardValue: 25
  },
  eldrin_2: {
    id: 'eldrin_2',
    npcId: 'eldrin',
    requiredHearts: 2,
    title: 'ปราชญ์ชี้ทางแห่งดวงดาว (Heart 2)',
    story: 'ผู้เฒ่าเอลดรินยืนมองลูกแก้วเวทมนตร์ในคฤหาสน์ เขาหันมาสบตาคุณด้วยแววตาเปี่ยมปัญญา: "ดวงชะตาของเจ้าส่องประกายสว่างไสวเหนือหุบเขา... ข้าสัมผัสได้ถึงพลังเวทโบราณที่หลับใหลอยู่ในกายเจ้า เจ้าพร้อมจะให้ข้าช่วยปลุกมันหรือไม่?"',
    choices: [
      { text: '"ข้าพร้อมรับฟังคำชี้แนะจากท่านปราชญ์ครับ"', response: 'เอลดรินวางมือบนศีรษะคุณ แสงสีทองส่องประกาย: "จงเปิดจิตรับพลังแห่งศิลาโบราณ... พลังเวทของเจ้าตื่นขึ้นแล้ว"', friendshipBonus: 50 },
      { text: '"พลังเวทนั้นจะนำความสงบสุขมาสู่ฟาร์มได้ใช่ไหม?"', response: 'เอลดรินยิ้มอย่างเมตตา: "แน่นอน พลังที่ขับเคลื่อนด้วยเจตนาอันบริสุทธิ์ย่อมสร้างสรรค์สิ่งงดงาม"', friendshipBonus: 40 }
    ],
    rewardDesc: 'Max Energy ถาวร +20!',
    rewardType: 'energy',
    rewardValue: 20
  },
  eldrin_4: {
    id: 'eldrin_4',
    npcId: 'eldrin',
    requiredHearts: 4,
    title: 'กุญแจสู่มิติผลึกนิรันดร์ (Heart 4)',
    story: 'เอลดรินมอบม้วนคัมภีร์หนังแกะโบราณให้คุณ: "นี่คือแผนที่นำทางสู่ หอคอยผลึกมิติไร้จุดสิ้นสุด (The Infinite Spire)... หอคอยนี้เชื่อมต่อกับแก่นพลังงานจักรวาล มีเพียงผู้กล้าที่ข้าไว้วางใจสูงสุดเท่านั้นที่จะก้าวเข้าไปได้"',
    choices: [
      { text: '"ข้าจะพิชิตหอคอยนี้และนำเกียรติยศมาสู่หุบเขา!"', response: 'เอลดรินพยักหน้าด้วยความภาคภูมิใจ: "ดวงดาวนำทางเจ้าเสมอ ขอให้พลังแห่งศิลาคุ้มครอง"', friendshipBonus: 80 },
      { text: '"ขอบพระคุณท่านผู้เฒ่าที่เชื่อมั่นในตัวข้า"', response: 'เอลดรินยิ้มอบอุ่น: "เจ้าคือความหวังที่แท้จริงของพวกเราทุกคน"', friendshipBonus: 60 }
    ],
    rewardDesc: 'ปลดล็อกทางเข้าหอคอยผลึก และ Max Energy ถาวร +30!',
    rewardType: 'energy',
    rewardValue: 30
  }
};

// ========================================================
// PIRATE EXPEDITION SHOP ITEMS (ร้านค้าเหรียญทองโบราณ กัปตันบาร์นาบี้)
// ========================================================
export interface PirateShopItem {
  id: string;
  name: string;
  priceDoubloons: number;
  type: string;
  desc: string;
  itemType: string;
}

export const PIRATE_SHOP_ITEMS: Record<string, PirateShopItem> = {
  cutlass_saber: {
    id: 'cutlass_saber',
    name: 'ดาบโจรสลัดคัตลาสอาถรรพ์ (Corsair Cutlass)',
    priceDoubloons: 20,
    type: 'weapon',
    itemType: 'weapon',
    desc: 'ดาบโค้งเหล็กกล้าแห่งแคริบเบียน ฟันคลื่นจันทร์เสี้ยววารี พลังโจมตี 100 ติดคริติคอล 35%!'
  },
  pirate_tricorn_hat: {
    id: 'pirate_tricorn_hat',
    name: 'หมวกกัปตันโจรสลัดสามมุม (Captain Tricorn)',
    priceDoubloons: 12,
    type: 'hat',
    itemType: 'armor',
    desc: 'หมวกโจรสลัดขนนกสีแดง สวมใส่เพิ่มโอกาสหลบหลีก +20% และเดินไวขึ้น +25%'
  },
  island_warp_totem: {
    id: 'island_warp_totem',
    name: 'เสาวาร์ปเกาะเขตร้อน x3 (Island Warp Totem)',
    priceDoubloons: 4,
    type: 'consumable',
    itemType: 'material',
    desc: 'เสาอาถรรพ์ ใช้เทเลพอร์ตข้ามมิติมายังเกาะเขตร้อนได้ทันทีจากทุกที่'
  },
  golden_melon_seed: {
    id: 'golden_melon_seed',
    name: 'เมล็ดเมลอนทองคำเกาะโจรสลัด x5',
    priceDoubloons: 3,
    type: 'seed',
    itemType: 'seed',
    desc: 'เมล็ดพืชหายาก ปลูกบนเกาะโต 5 วัน ได้ผลเมลอนทองคำขายได้ราคา 420 G!'
  },
  starfruit_seed: {
    id: 'starfruit_seed',
    name: 'เมล็ดผลไม้ดวงดาวแคริบเบียน x5',
    priceDoubloons: 5,
    type: 'seed',
    itemType: 'seed',
    desc: 'เมล็ดผลไม้รูปดาวเรืองแสง ปลูกบนเกาะโต 6 วัน ขายได้ราคาสูง 550 G!'
  },
  skeleton_key: {
    id: 'skeleton_key',
    name: 'กุญแจโครงกระดูกโจรสลัด (Skeleton Key)',
    priceDoubloons: 2,
    type: 'key',
    itemType: 'material',
    desc: 'กุญแจกระดูกอาถรรพ์ ใช้ไขเปิดหีบสมบัติโจรสลัดโบราณบนซากเรืออับปาง'
  },
  tropical_delight_drink: {
    id: 'tropical_delight_drink',
    name: 'ค็อกเทลเขตร้อนสูตรกัปตัน x3',
    priceDoubloons: 3,
    type: 'food',
    itemType: 'material',
    desc: 'เครื่องดื่มผลไม้เขตร้อนเย็นฉ่ำ ดื่มเพื่อวิ่งเร็วขึ้น +60% นาน 5 นาที!'
  }
};
