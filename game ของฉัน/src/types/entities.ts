/* ========================================================
    Happy Farm 2D - TypeScript Type Definitions: Entities & Quests
   ======================================================== */

export interface DemonBugData {
  id: string;
  name: string;
  desc: string;
  hp: number;
  speed: number;
  damage: number;
  attackCooldown: number;
  targetType: 'crop' | 'animal';
  loot: {
    gold: number;
    item: string;
    name: string;
    xp: number;
  };
}

export interface HunterData {
  id: string;
  name: string;
  price: number;
  salary: number;
  desc: string;
  damage: number;
  range: number;
  attackSpeed: number;
  patrolArea: 'crops' | 'animals';
  spriteType: string;
}

export interface FarmHelperData {
  id: string;
  name: string;
  price: number;
  desc: string;
  role: 'gardener' | 'harvester';
  spriteType: string;
  speed: number;
  actionCooldown: number;
}

export interface MonsterDrop {
  item: string;
  chance: number;
  count?: number;
}

export interface WorldMonsterData {
  id: string;
  name: string;
  shortName?: string;
  hp: number;
  maxHp: number;
  speed: number;
  damage: number;
  attackCooldown: number;
  aggroDist: number;
  drops: MonsterDrop[];
  gold: number;
  xp: number;
}

export interface BossData extends WorldMonsterData {
  title: string;
}

export interface BountyData {
  id: string;
  bossId: string;
  title: string;
  name: string;
  location: string;
  scene: string;
  desc: string;
  weakness: string;
  rewardGold: number;
  rewardXp: number;
  rewardItem: string;
  rewardItemName: string;
}

export interface QuestRewardItem {
  id: string;
  count: number;
  name: string;
}

export interface QuestData {
  id: string;
  title: string;
  desc: string;
  giver?: string;
  rewardText?: string;
  targetType: 'talk' | 'hunt_mine' | 'boss' | 'collect' | 'purify' | string;
  targetNpc?: string;
  reqWolves?: number;
  reqRubies?: number;
  reqBugs?: number;
  reqSpores?: number;
  targetBoss?: string;
  rewardDesc: string;
  goldReward: number;
  xpReward: number;
  itemsReward: QuestRewardItem[];
}

export interface StoryNPCData {
  id: string;
  name: string;
  role: string;
  portraitType: string;
  portrait?: string;
  dialogue?: any;
  dialogues: Record<string, string>;
}

export interface NPCCustomerData {
  id: string;
  name: string;
  desc: string;
  type: string;
}

export interface VillageVillagerData {
  id: string;
  name: string;
  type: string;
  x: number;
  y: number;
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
  direction: 'up' | 'down' | 'left' | 'right';
  state: 'idle' | 'walking' | 'talking';
  timer: number;
  speed: number;
  frame: number;
  bubbleText?: string | null;
  bubbleTimer?: number;
  phrases: string[];
}

export interface DroppedItemEntity {
  id: string;
  name: string;
  count: number;
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  bounces: number;
  timer: number;
  magnet: boolean;
  quality?: number;
  manualPickup?: boolean;
}
