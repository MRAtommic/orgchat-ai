/* ========================================================
    Happy Farm 2D - TypeScript Type Definitions: Core Game & Save
   ======================================================== */

export type Direction = 'up' | 'down' | 'left' | 'right';
export type SceneName = 'farm' | 'house' | 'shop' | 'forest';

export interface PlayerOutfit {
  hatStyle: string;
  shirtColor: string;
  overallsColor: string;
  hairColor: string;
}

export interface HouseUpgrades {
  bed_deluxe: boolean;
  fireplace: boolean;
  refrigerator: boolean;
  tea_table: boolean;
  persian_rug: boolean;
}

export interface InventoryItem {
  id: string;
  name: string;
  type: 'tool' | 'seed' | 'crop' | 'animal_product' | 'food' | 'weapon' | 'material';
  count?: number;
  cropId?: string;
  energyRestore?: number;
  hpRestore?: number;
  quality?: 0 | 1 | 2 | 3; // 0: Normal, 1: Silver ★, 2: Gold ★★, 3: Iridium 
  [key: string]: any;
}

export type InventorySlot = InventoryItem | null;

export interface PlayerState {
  x: number;
  y: number;
  width: number;
  height: number;
  speed: number;
  direction: Direction;
  frame: number;
  animTimer: number;
  isMoving: boolean;
  hp: number;
  maxHp: number;
  hpRegenDelay?: number;
  invincibleTimer: number;
  energy: number;
  maxEnergy: number;
  energyRegenDelay?: number;
  hunger?: number;
  maxHunger?: number;
  thirst?: number;
  maxThirst?: number;
  gold: number;
  level: number;
  xp: number;
  waterCan: number;
  waterCanMax: number;
  selectedSlot: number;
  inventory: InventorySlot[];
  quests: Record<string, 'not_started' | 'active' | 'completed'>;
  questProgress: {
    wolvesKilled: number;
    rubiesMined: number;
    bossDefeated: boolean;
    [key: string]: any;
  };
  buffs?: { speed?: number; damage?: number; defense?: number; maxHp?: number; timer?: number; name?: string };
  outfit: PlayerOutfit;
  houseUpgrades: HouseUpgrades;
  pet?: {
    type: 'dog' | 'cat';
    name: string;
    x: number;
    y: number;
    affection: number;
    level: number;
  };
  isMounted?: boolean;
  mineProgress?: {
    currentFloor: number;
    maxUnlockedFloor: number;
  };
  npcFriendship?: Record<string, number>;
  museumCollections?: Record<string, boolean>;
  defeatedBosses?: Record<string, boolean>;
  bossDefeatDay?: Record<string, number>;
  claimedBounties?: Record<string, boolean>;
  achievements?: Record<string, boolean>;
  skillMastery?: Record<string, boolean>;
  masteryPoints?: number;
  equippedRings?: [string | null, string | null];
  openedDungeonChests?: Record<string, boolean>;
  spouse?: string | null;
  dating?: string | null;
  spouseKissedToday?: boolean;
  greenhouseUnlocked?: boolean;
  farmCaveChoice?: 'mushrooms' | 'bats' | null;
  islandUnlocked?: boolean;
  festivalState?: {
    activeFestival: string | null;
    timer: number;
    score: number;
  };
  // Advanced Combat & Runes
  isDashing?: boolean;
  dashTimer?: number;
  dashCooldown?: number;
  dashDir?: { x: number; y: number };
  equippedRune?: 'fire' | 'frost' | 'lightning' | 'vampiric' | null;
  // Infinite Crystal Spire
  spireProgress?: {
    currentFloor: number;
    maxFloor: number;
    shards: number;
  };
  // Lore & Heart Events & Ancient Shrine
  seenHeartEvents?: Record<string, boolean>;
  sacredShards?: Record<string, boolean>;
  shrineRestored?: boolean;
  masterMode?: boolean;
  bonusBaseDamage?: number;
}

export interface PlacedMachine {
  id: string;
  type: 'preserves_jar' | 'wine_keg' | 'cheese_press' | 'mayo_machine';
  name: string;
  scene: string;
  x: number;
  y: number;
  inputItem?: any;
  outputItem?: any;
  progress: number;
  maxProgress: number;
  isReady: boolean;
}

export interface PlacedSprinkler {
  id: string;
  type: 'sprinkler_basic' | 'sprinkler_quality';
  scene: string;
  x: number;
  y: number;
}

export interface PlacedDecor {
  id: string;
  type: 'wood_fence' | 'stone_fence' | 'stone_path' | 'wood_path' | 'farm_lantern' | 'fish_tank';
  scene: string;
  x: number;
  y: number;
  fishId?: string;
}

export interface PlacedStructure {
  id: string;
  type: 'windmill' | 'silo';
  scene: string;
  x: number;
  y: number;
  grainStored?: number;
  processing?: boolean;
}

export interface TileCrop {
  cropId: string;
  stage: number;
  daysGrown: number;
  ready: boolean;
}

export interface MapTile {
  x: number;
  y: number;
  type: string;
  solid: boolean;
  tilled?: boolean;
  watered?: boolean;
  crop?: TileCrop | null;
  interactable?: string | null;
}

export interface GameScene {
  mapWidth: number;
  mapHeight: number;
  map: MapTile[][];
}

export type WeatherType = 'sun' | 'rain' | 'thunder' | 'snow';

export interface FishingState {
  active: boolean;
  phase: 'idle' | 'casting' | 'waiting' | 'hooked' | 'minigame' | 'caught';
  timer: number;
  fishId: string | null;
  bobberX: number;
  bobberY: number;
  barPos: number;
  barHeight: number;
  fishPos: number;
  fishTargetPos: number;
  progress: number;
}

export interface GameTime {
  day: number;
  seasonIndex: number;
  hour: number;
  minute: number;
  timer: number;
  weather: WeatherType;
}


export interface GameStats {
  harvests: number;
  sales: number;
  crafts: number;
  animalsPetted: number;
  bugsDefeated: number;
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  picture: string;
  provider: 'google' | 'guest';
  lastPlayed: string;
}

export interface GameSaveData {
  version: number;
  timestamp: string;
  player: PlayerState;
  time: GameTime;
  stats: GameStats;
  farmMapCrops?: { x: number; y: number; crop: TileCrop; watered: boolean; tilled: boolean }[];
  shopShelves?: any[];
  hiredHunters?: any[];
  hiredGardeners?: any[];
}
