---
name: game-balance-economy
description: Game balance, combat math, and economy design for 2D RPG, Stardew-like farming sims, and action games. Covers Time-To-Kill (TTK), Effective HP, DPS tiers, Gold Sources vs Sinks, risk/reward equilibrium, and progression gating.
---

# ⚖️ Game Balance & Economy Systems Design Skill

A rigorous mathematical and systems-design framework for balancing RPG combat, farming sims, crafting economies, and progression curves.

---

## 1. The Cardinal Rule of Game Balance: No "Rocket Tag"

In poor action games, combat degenerates into "Rocket Tag":
- Weapons deal 300+ damage while normal enemies have 80 HP (enemies die in 1 tap).
- Bosses deal 80 damage while the player has 100 HP (player dies in 1-2 hits).
- Result: **Zero depth, pure cheese or pure frustration.**

### Target Combat Metrics (Real-Time Action RPG / Souls-Lite):
- **Normal Mob TTK (Time to Kill):** 2.5 - 4.5 seconds (3 to 6 hits of standard weapon).
- **Elite Mob TTK:** 8 - 15 seconds.
- **Boss Fight Duration:** 60 - 120 seconds of tight, focused execution (approx. 40 - 70 player hits + dodge dance).
- **Player Margin of Error:** Player should survive **3 to 5 standard boss hits** or **2 heavy telegraphed hits** before dying. One-shots should ONLY occur on massive, 2-second telegraph ultimate moves that are 100% avoidable via I-frames.

---

## 2. Coherent 4-Tier Progression Curve

Every weapon, monster, boss, and reward must belong to a strictly defined progression tier:

| Tier | Zone / Biome | Weapon DPS | Player Max HP | Boss HP | Boss DMG | Gold Reward / Kill |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **Tier 1 (Early)** | Home Farm, Elderwood Forest | **20 - 35** | 100 - 130 | 1,200 - 1,600 | 14 - 22 | 80 - 180 G |
| **Tier 2 (Mid)** | Crystal Mine, Gloom Swamp | **45 - 65** | 130 - 180 | 2,200 - 2,800 | 22 - 32 | 220 - 350 G |
| **Tier 3 (High)** | Ignis Volcano, Frost Peak | **75 - 100** | 180 - 240 | 3,500 - 4,200 | 30 - 42 | 400 - 600 G |
| **Tier 4 (End)** | Necropolis, Sylvan Canopy, Tempest | **110 - 140** | 240 - 320 | 5,000 - 6,500 | 38 - 55 | 650 - 950 G |

### Golden Rule of Multi-Shot Weapons:
When a weapon fires multiple projectiles (e.g. Sylvan Bow 4 arrows, Hydra Bow 3 arrows):
- **NEVER** give each projectile the full single-target damage of a high-tier weapon!
- If target Tier 4 DPS is 130, and attack cooldown is 300ms (~3.3 attacks/sec):
  - Total damage per attack must be `130 / 3.3 ≈ 40 damage`.
  - For a 4-arrow bow: **10 - 12 DMG per arrow** (total 40 - 48 DMG per volley), NOT 160 per arrow!

---

## 3. Economy Equilibrium: Sources vs. Sinks (Preventing Hyperinflation)

When a player earns money faster than they can spend it, currency loses all value and player engagement plummets.

### A. Gold per Minute (GPM) Anchors:
1. **Farming (Safe, Low Risk):**
   - Yield: 8 - 25 Gold profit per tile per harvest day.
   - 20 tiles farmed = ~250 - 400 Gold per game day.
2. **Mob Hunting (Active, Moderate Risk):**
   - Normal Mob: 6 - 18 Gold.
   - 1 minute of mob grinding = ~60 - 120 Gold + crafting drops.
3. **Boss Bounty (High Risk, Milestone):**
   - Tier 1 Boss: 180 - 250 Gold.
   - Tier 2 Boss: 300 - 450 Gold.
   - Tier 3 Boss: 500 - 700 Gold.
   - Tier 4 Boss: 800 - 1,200 Gold.
   - **Never grant 10,000 - 50,000 Gold** in a single drop! That renders all farming and shop loops irrelevant.

### B. Meaningful Gold Sinks:
- Seed purchases (recurring)
- Blacksmith Forge costs: Tier 1 (150 G) -> Tier 2 (400 G) -> Tier 3 (800 G) -> Tier 4 (1,500 G)
- Tool Upgrades: Copper (300 G) -> Iron (750 G) -> Gold (1,600 G) -> Iridium (3,500 G)
- Farm Expansions & House Upgrades: 500 - 4,000 G
- Consumables / Potions: 40 - 120 G

---

## 4. Player Survivability & Defense Progression

To support Dark Souls difficulty without feeling unfair:
1. **Max HP Progression:**
   - Level 1: 100 HP.
   - Level 5: 140 HP.
   - Level 10: 200 HP.
   - End-game gear / foods: Up to 280 - 320 HP.
2. **Armor / Mitigation Formula:**
   $$\text{Damage Taken} = \text{Raw Damage} \times \frac{100}{100 + \text{Defense}}$$
   - 50 Defense = 33% damage reduction.
   - 100 Defense = 50% damage reduction.
3. **Dodge Roll I-Frames:**
   - Active window: 240 - 280 ms.
   - Recovery window: 300 - 400 ms.
   - Cooldown: 550 - 700 ms.
   - Punishes panic-rolling while rewarding read-and-react timing.
