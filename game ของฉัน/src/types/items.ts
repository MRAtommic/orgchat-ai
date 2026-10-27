/* ========================================================
    Happy Farm 2D - TypeScript Type Definitions: Items & Economy
   ======================================================== */

export type CropCategory = 'grain' | 'vegetable' | 'fruit' | 'flower';

export interface CropData {
  id: string;
  name: string;
  seedName: string;
  buyPrice: number;
  sellPrice: number;
  growDays: number;
  xp: number;
  levelReq: number;
  category: CropCategory;
}

export interface AnimalData {
  id: string;
  name: string;
  buyPrice: number;
  product: string;
  productName: string;
  productPrice: number;
  xp: number;
  levelReq: number;
  feedType: string;
}

export interface RecipeData {
  id: string;
  name: string;
  category: 'mill' | 'bakery' | 'dairy' | 'kitchen' | 'carpentry';
  ingredients: Record<string, number>;
  sellPrice: number;
  xp: number;
  levelReq: number;
  energyRestore?: number;
}

export interface ToolData {
  id: string;
  name: string;
  desc: string;
  energyCost: number;
}

export interface UpgradeData {
  id: string;
  name: string;
  price: number;
  desc: string;
  levelReq?: number;
  effectType?: 'maxEnergy' | 'energySave' | 'foodBoost' | 'homeRegen' | 'xpBoost';
  value?: number;
}

export interface WeaponData {
  id: string;
  name: string;
  desc: string;
  type: 'ranged' | 'melee' | 'melee_beam' | string;
  damage: number;
  speed: number;
  range: number;
  cooldown: number;
  bulletType?: 'stone' | 'rifle' | 'holy_beam' | 'dragon_fire' | 'crystal_shard' | 'poison_glob' | 'ice_shard' | 'shadow_skull' | string;
}

export interface MaterialItem {
  id: string;
  name: string;
  sellPrice: number;
  desc: string;
  energyRestore?: number;
  hpRestore?: number;
}

export interface ForgeRecipe {
  id: string;
  name: string;
  desc: string;
  cost: number;
  goldCost?: number;
  materials: Record<string, number>;
}

export interface FishData {
  id: string;
  name: string;
  sellPrice: number;
  xp: number;
  difficulty: number;
  desc: string;
  habitat: 'pond' | 'river' | 'ocean' | 'any';
}

