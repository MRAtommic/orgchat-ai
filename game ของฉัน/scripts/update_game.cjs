const fs = require('fs');
const path = require('path');

const gameTsPath = path.resolve(__dirname, '..', 'src', 'engine', 'game.ts');
let code = fs.readFileSync(gameTsPath, 'utf8');

console.log('Original game.ts size:', code.length, 'bytes');

// ========================================================
// 1. Update addItemToInventory
// ========================================================
const oldAddSign = `Game.addItemToInventory = function(id, count = 1, name = '') {`;
const newAddSign = `Game.addItemToInventory = function(id, count = 1, name = '', quality: 0 | 1 | 2 | 3 = 0) {
    const itemQuality = quality || 0;`;

if (code.includes(oldAddSign)) {
    code = code.replace(oldAddSign, newAddSign);
    console.log('[1/12] Replaced addItemToInventory signature');
} else {
    console.error('FAILED to find oldAddSign');
}

// Update stacking match to check quality as well
const oldStack = `if (slot && slot.id === id && slot.count !== undefined) {`;
const newStack = `if (slot && slot.id === id && slot.count !== undefined && (slot.quality || 0) === itemQuality) {`;
if (code.includes(oldStack)) {
    code = code.replace(oldStack, newStack);
    console.log('[1.1/12] Replaced stack match with quality check');
} else {
    console.error('FAILED to find oldStack');
}

// Update new slot creation to store quality
const oldCreateSlot = `this.player.inventory[i] = {
                id: id,
                name: name || WEAPONS[id]?.name || CROPS[id]?.name || RECIPES[id]?.name || WORLD_ITEMS[id]?.name || MONSTER_DROPS[id]?.name || id,
                count: (isWep || itemType === 'tool') ? undefined : count,
                type: itemType,
                cropId: cropId
            };`;
const newCreateSlot = `this.player.inventory[i] = {
                id: id,
                name: name || WEAPONS[id]?.name || CROPS[id]?.name || RECIPES[id]?.name || WORLD_ITEMS[id]?.name || MONSTER_DROPS[id]?.name || id,
                count: (isWep || itemType === 'tool') ? undefined : count,
                type: itemType,
                cropId: cropId,
                quality: itemQuality
            };`;
if (code.includes(oldCreateSlot)) {
    code = code.replace(oldCreateSlot, newCreateSlot);
    console.log('[1.2/12] Added quality to new inventory slot');
} else {
    console.error('FAILED to find oldCreateSlot');
}

// ========================================================
// 2. Update spawnDroppedItem & updateDroppedItems
// ========================================================
const oldSpawn = `Game.spawnDroppedItem = function(id, count = 1, name, x, y) {`;
const newSpawn = `Game.spawnDroppedItem = function(id, count = 1, name, x, y, quality: 0 | 1 | 2 | 3 = 0) {`;
if (code.includes(oldSpawn)) {
    code = code.replace(oldSpawn, newSpawn);
    console.log('[2/12] Updated spawnDroppedItem signature');
}

const oldSpawnPush = `bounces: 0,
            timer: 0,
            magnet: false
        });`;
const newSpawnPush = `bounces: 0,
            timer: 0,
            magnet: false,
            quality: quality || 0
        });`;
if (code.includes(oldSpawnPush)) {
    code = code.replace(oldSpawnPush, newSpawnPush);
    console.log('[2.1/12] Added quality to droppedItems.push');
}

const oldPickup = `this.addItemToInventory(item.id, item.count, item.name);`;
const newPickup = `this.addItemToInventory(item.id, item.count, item.name, (item as any).quality || 0);`;
if (code.includes(oldPickup)) {
    code = code.replace(oldPickup, newPickup);
    console.log('[2.2/12] Updated updateDroppedItems pickup with quality');
}

// ========================================================
// 3. Update harvestCrop with quality roll and double_harvest perk
// ========================================================
const oldHarvest = `    const yieldAmount = Math.floor(Math.random() * 2) + 1;
    this.spawnDroppedItem(tile.crop.cropId, yieldAmount, cropData.name, tx * 32 + 16, ty * 32 + 16);`;
const newHarvest = `    let yieldAmount = Math.floor(Math.random() * 2) + 1;
    if (this.player.skillMastery?.double_harvest && Math.random() < 0.25) {
        yieldAmount *= 2;
        this.addFloatingText('🌾 พลังเก็บเกี่ยวคูณสอง! (Double Yield)', tx * 32, ty * 32 - 32, '#4ade80');
    }
    const quality = this.rollItemQuality('farming', this.player.skills?.farming || 1);
    this.spawnDroppedItem(tile.crop.cropId, yieldAmount, cropData.name, tx * 32 + 16, ty * 32 + 16, quality);`;
if (code.includes(oldHarvest)) {
    code = code.replace(oldHarvest, newHarvest);
    console.log('[3/12] Updated harvestCrop with quality roll & double_harvest perk');
} else {
    console.error('FAILED to find oldHarvest');
}

// ========================================================
// 4. Update completeFishingCatch with quality roll & treasure_hunter perk
// ========================================================
const oldFishCatch = `    if (fish) {
        SoundEngine.fishCatch();
        this.addItemToInventory(fish.id, 1, fish.name);
        this.addXp(fish.xp);
        this.spawnParticles(this.player.x + 12, this.player.y + 16, '#facc15', 20);
        this.spawnParticles(this.player.x + 12, this.player.y + 16, '#38bdf8', 16);
        this.addFloatingText(\`🎣 ตกได้ \${fish.name}! (+\${fish.xp} XP)\`, this.player.x - 20, this.player.y - 25, '#4ade80');
        this.updateHUD();
    }`;

const newFishCatch = `    if (fish) {
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
            this.addFloatingText(\`🏴‍☠️ ตกพบหีบสมบัติใต้สมุทร! (+\${bonusGold}G & \${WORLD_ITEMS[tItem]?.name || tItem})\`, this.player.x - 40, this.player.y - 45, '#fde047');
        }

        const qText = this.getQualityBadgeText(quality);
        const qLabel = qText ? \` (\${qText})\` : '';
        this.spawnParticles(this.player.x + 12, this.player.y + 16, '#facc15', 20);
        this.spawnParticles(this.player.x + 12, this.player.y + 16, '#38bdf8', 16);
        this.addFloatingText(\`🎣 ตกได้ \${fish.name}\${qLabel}! (+\${fish.xp} XP)\`, this.player.x - 20, this.player.y - 25, '#4ade80');
        this.updateHUD();
    }`;

if (code.includes(oldFishCatch)) {
    code = code.replace(oldFishCatch, newFishCatch);
    console.log('[4/12] Updated completeFishingCatch with quality & treasure_hunter');
} else {
    console.error('FAILED to find oldFishCatch');
}

// ========================================================
// 5. Update playerMeleeAttack with critical_edge and vampiric_vitality
// ========================================================
const oldCrit = `    const attackRange = weapon.range || 65;
    const isCrit = Math.random() < 0.22;
    const finalDamage = Math.round(weapon.damage * (isCrit ? 1.8 : 1.0));`;

const newCrit = `    const attackRange = weapon.range || 65;
    const critRate = this.player.skillMastery?.critical_edge ? 0.38 : 0.22;
    const critMult = this.player.skillMastery?.critical_edge ? 2.5 : 1.8;
    const isCrit = Math.random() < critRate;
    const finalDamage = Math.round(weapon.damage * (isCrit ? critMult : 1.0));`;

if (code.includes(oldCrit)) {
    code = code.replace(oldCrit, newCrit);
    console.log('[5/12] Updated playerMeleeAttack crit calculations');
} else {
    console.error('FAILED to find oldCrit');
}

// ========================================================
// 6. Update sellItem with quality multiplier and artisan/gemologist perks
// ========================================================
const oldSellCalc = `    const count = item.count || 1;
    const totalEarnings = price * count;`;

const newSellCalc = `    // Star Quality multiplier
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
    const totalEarnings = Math.round(price * qualityMult * count);`;

if (code.includes(oldSellCalc)) {
    code = code.replace(oldSellCalc, newSellCalc);
    console.log('[6/12] Updated sellItem with quality and mastery multipliers');
} else {
    console.error('FAILED to find oldSellCalc');
}

// ========================================================
// 7. Update updateHUD and renderInventoryModal with star badges
// ========================================================
const oldHotbarStarTarget = `                if (item.count !== undefined) {
                    const countBadge = document.createElement('span');
                    countBadge.className = 'slot-count';
                    countBadge.textContent = String(item.count);
                    slotEl.appendChild(countBadge);
                }
                slotEl.title = this.getItemTooltipText(item);`;

const newHotbarStarTarget = `                if (item.count !== undefined) {
                    const countBadge = document.createElement('span');
                    countBadge.className = 'slot-count';
                    countBadge.textContent = String(item.count);
                    slotEl.appendChild(countBadge);
                }
                if (item.quality && item.quality > 0) {
                    const starBadge = document.createElement('span');
                    starBadge.className = 'slot-quality-star quality-' + item.quality;
                    starBadge.textContent = item.quality === 1 ? '⭐' : item.quality === 2 ? '⭐⭐' : '💜';
                    slotEl.appendChild(starBadge);
                }
                slotEl.title = this.getItemTooltipText(item);`;

if (code.includes(oldHotbarStarTarget)) {
    code = code.replace(oldHotbarStarTarget, newHotbarStarTarget);
    console.log('[7/12] Added quality star badge to updateHUD');
} else {
    console.error('FAILED to find oldHotbarStarTarget');
}

const oldBagStarTarget = `            if (item.count !== undefined) {
                const countBadge = document.createElement('span');
                countBadge.className = 'slot-count';
                countBadge.textContent = String(item.count);
                slot.appendChild(countBadge);
            }
            slot.title = this.getItemTooltipText(item);`;

const newBagStarTarget = `            if (item.count !== undefined) {
                const countBadge = document.createElement('span');
                countBadge.className = 'slot-count';
                countBadge.textContent = String(item.count);
                slot.appendChild(countBadge);
            }
            if (item.quality && item.quality > 0) {
                const starBadge = document.createElement('span');
                starBadge.className = 'slot-quality-star quality-' + item.quality;
                starBadge.textContent = item.quality === 1 ? '⭐' : item.quality === 2 ? '⭐⭐' : '💜';
                slot.appendChild(starBadge);
            }
            slot.title = this.getItemTooltipText(item);`;

if (code.includes(oldBagStarTarget)) {
    code = code.replace(oldBagStarTarget, newBagStarTarget);
    console.log('[7.1/12] Added quality star badge to renderInventoryModal');
} else {
    console.error('FAILED to find oldBagStarTarget');
}

// ========================================================
// 8. Update getItemTooltipText & getItemTooltipData with quality info
// ========================================================
const oldTooltipDataRet = `    return {
        id,
        name,
        category,
        hpRestore,
        energyRestore,
        hungerRestore,
        thirstRestore,
        attackDmg,
        range,
        desc,
        sellPrice,
        count: item.count
    };`;

const newTooltipDataRet = `    const quality = item.quality || 0;
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
    };`;

if (code.includes(oldTooltipDataRet)) {
    code = code.replace(oldTooltipDataRet, newTooltipDataRet);
    console.log('[8/12] Updated getItemTooltipData with quality price bonus');
}

const oldTooltipTextLines = `    const lines = [\`【\${data.name}】\`];
    lines.push(\`📂 ประเภท: \${data.category}\`);`;

const newTooltipTextLines = `    const qBadge = this.getQualityBadgeText ? this.getQualityBadgeText(item.quality) : '';
    const nameLine = qBadge ? \`【\${data.name} \${qBadge}】\` : \`【\${data.name}】\`;
    const lines = [nameLine];
    lines.push(\`📂 ประเภท: \${data.category}\`);
    if (item.quality && item.quality > 0) {
        lines.push(item.quality === 1 ? '⭐ คุณภาพระดับเงิน (+25% มูลค่า)' : item.quality === 2 ? '⭐⭐ คุณภาพระดับทอง (+50% มูลค่า)' : '💜 คุณภาพระดับอิริเดียม (+100% มูลค่า)');
    }`;

if (code.includes(oldTooltipTextLines)) {
    code = code.replace(oldTooltipTextLines, newTooltipTextLines);
    console.log('[8.1/12] Updated getItemTooltipText with star quality label');
}

// ========================================================
// 9. Update sleepAndPassDay with greenhouse crops, spouse help, cave resets, festival check
// ========================================================
const oldSleepEnd = `    SoundEngine.levelUp();
    this.addFloatingText('เช้าวันใหม่! พลังงานเต็ม 100% (' + this.player.maxEnergy + ')', this.player.x, this.player.y - 20, '#fde047');
    if (isWetWeather) {
        this.addFloatingText('🌧️ ฝนตกรดน้ำแปลงผักให้ทั้งฟาร์ม!', this.player.x, this.player.y - 35, '#38bdf8');
    }
    this.updateHUD();`;

const newSleepEnd = `    // 🌿 Greenhouse Year-Round Crop Growth
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

    // 💖 Spouse Morning Care & Daily Reset
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
            this.addFloatingText(\`💖 \${spouseName}: "อรุณสวัสดิ์จ้ะที่รัก! ข้าช่วยรดน้ำแปลงผักให้เจ้าทั้งฟาร์มแล้วนะ!"\`, 19 * 32, 5 * 32 - 32, '#ec4899');
        } else {
            // Spouse cooks fresh hearty breakfast!
            const breakfasts = ['spicy_fish_soup', 'pizza', 'bread', 'cake'];
            const bItem = breakfasts[Math.floor(Math.random() * breakfasts.length)];
            this.addItemToInventory(bItem, 1);
            this.addFloatingText(\`💖 \${spouseName}: "ตื่นแล้วหรือจ๊ะที่รัก? ข้าเตรียมอาหารเช้าแสนอร่อยไว้ให้แล้วนะ!"\`, 19 * 32, 5 * 32 - 32, '#f472b6');
        }
    }

    // 🦇 Farm Cave: Fruit Bats Nightly Drops
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

    // 🎪 Check Seasonal Village Festival
    this.checkFestivalBanner();

    SoundEngine.levelUp();
    this.addFloatingText('เช้าวันใหม่! พลังงานเต็ม 100% (' + this.player.maxEnergy + ')', this.player.x, this.player.y - 20, '#fde047');
    if (isWetWeather) {
        this.addFloatingText('🌧️ ฝนตกรดน้ำแปลงผักให้ทั้งฟาร์ม!', this.player.x, this.player.y - 35, '#38bdf8');
    }
    this.updateHUD();`;

if (code.includes(oldSleepEnd)) {
    code = code.replace(oldSleepEnd, newSleepEnd);
    console.log('[9/12] Updated sleepAndPassDay with greenhouse, spouse care & festival check');
} else {
    console.error('FAILED to find oldSleepEnd');
}

// ========================================================
// 10. Update queueHouseInterior to render spouse in farmhouse
// ========================================================
const oldHouseSpouseAnchor = `    // Bed at (19, 3)`;
const newHouseSpouseAnchor = `    // 💖 Living Spouse in Farmhouse
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
                this.ctx.fillText(this.player.spouseKissedToday ? '💖' : '💕', screenSx + 4, screenSy - 4);

                // Name tag
                this.ctx.fillStyle = '#fdf2f8';
                this.ctx.font = 'bold 9px "Prompt", sans-serif';
                this.ctx.textAlign = 'center';
                this.ctx.fillText(spouseName, screenSx + 12, screenSy + 38);
                this.ctx.textAlign = 'left';
            }
        });
    }

    // Bed at (19, 3)`;

if (code.includes(oldHouseSpouseAnchor)) {
    code = code.replace(oldHouseSpouseAnchor, newHouseSpouseAnchor);
    console.log('[10/12] Added spouse rendering in queueHouseInterior');
} else {
    console.error('FAILED to find oldHouseSpouseAnchor');
}

// ========================================================
// 11. Update Game.render to draw new scenery & ground tile types
// ========================================================
const oldRenderAnchor = `            } else if (tile.type === 'caveFloor') {`;
const newRenderTiles = `            } else if (tile.type === 'sand') {
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
                    }
                });
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
            } else if (tile.type === 'caveFloor') {`;

if (code.includes(oldRenderAnchor)) {
    code = code.replace(oldRenderAnchor, newRenderTiles);
    console.log('[11/12] Added scenery tile renders in Game.render');
} else {
    console.error('FAILED to find oldRenderAnchor');
}

// ========================================================
// 12. Append New Expansion Methods Before window exports
// ========================================================
const expansionMethods = `
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
    if (roll < iridiumChance) return 3; // 💜 Iridium
    if (roll < iridiumChance + goldChance) return 2; // ⭐⭐ Gold
    if (roll < iridiumChance + goldChance + silverChance) return 1; // ⭐ Silver
    return 0; // Regular
};

Game.getQualityBadgeText = function(quality?: number): string {
    if (quality === 3) return '💜';
    if (quality === 2) return '⭐⭐';
    if (quality === 1) return '⭐';
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
        farming: '🌾 กสิกรรม (Farming)',
        mining: '⛏️ เหมืองแร่ (Mining)',
        fishing: '🎣 ตกปลา (Fishing)',
        combat: '⚔️ ต่อสู้ (Combat)',
        artisan: '🍷 การแปรรูป (Artisan)'
    };

    const perks = Object.values(SKILL_MASTERIES) as any[];
    perks.forEach(perk => {
        const isUnlocked = !!this.player.skillMastery[perk.id];
        const card = document.createElement('div');
        card.className = 'mastery-perk-card' + (isUnlocked ? ' unlocked' : '');

        const branchTitle = branchNames[perk.branch] || perk.branch;
        const currentSkillLevel = this.player.skills?.[perk.branch] || 1;
        const meetsReq = currentSkillLevel >= perk.requiredLevel;

        card.innerHTML = \`
            <div class="perk-header">
                <span class="perk-icon">\${perk.icon}</span>
                <div>
                    <h3 class="perk-name">\${perk.name}</h3>
                    <span class="perk-branch">\${branchTitle} (ขั้นต่ำ Lv.\${perk.requiredLevel})</span>
                </div>
            </div>
            <p class="perk-desc">\${perk.desc}</p>
            <div class="perk-footer">
                \${isUnlocked ? '<span class="badge-unlocked">✅ ปลดล็อกแล้ว</span>' :
                  (!meetsReq ? \`<span class="badge-locked">🔒 ต้องการทักษะ Lv.\${perk.requiredLevel}</span>\` :
                   (this.player.masteryPoints > 0 ?
                    \`<button class="btn-unlock-mastery" onclick="Game.unlockSkillMastery('\${perk.id}')">🌟 เรียนรู้ทักษะ (1 แต้ม)</button>\` :
                    '<span class="badge-locked">แต้มไม่เพียงพอ</span>'))}
            </div>
        \`;
        grid.appendChild(card);
    });
};

Game.unlockSkillMastery = function(perkId: string) {
    if (!this.player.masteryPoints || this.player.masteryPoints <= 0) {
        this.addFloatingText('❌ แต้มความชำนาญไม่เพียงพอ!', this.player.x, this.player.y - 15, '#ef4444');
        return;
    }
    const perk = (SKILL_MASTERIES as any)[perkId];
    if (!perk) return;

    this.player.masteryPoints -= 1;
    this.player.skillMastery[perkId] = true;

    SoundEngine.levelUp();
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#facc15', 30);
    this.spawnParticles(this.player.x + 12, this.player.y + 16, '#38bdf8', 20);
    this.addFloatingText(\`🌟 ปลดล็อกสุดยอดทักษะ: \${perk.name}!\`, this.player.x - 30, this.player.y - 25, '#fde047');

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
    const choiceName = choice === 'mushrooms' ? '🍄 ห้องเพาะเห็ดวิจัย (Mushroom Boxes)' : '🦇 ถ้ำค้างคาวผลไม้สด (Fruit Bats)';
    this.addFloatingText(\`✨ พัฒนาถ้ำเป็น: \${choiceName} สำเร็จ!\`, this.player.x - 30, this.player.y - 20, '#e9d5ff');

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
    this.addFloatingText(\`🍄 เก็บเกี่ยว \${mInfo.name} \${qBadge}! (+15 XP)\`, tx * 32, ty * 32 - 15, '#e9d5ff');
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
    this.addFloatingText(\`🍎 เก็บผลไม้ถ้ำ: \${fInfo.name} \${qBadge}! (+10 XP)\`, tx * 32, ty * 32 - 15, '#fbcfe8');
    this.addXp(10);
    this.updateHUD();
};

Game.travelToIsland = function() {
    SoundEngine.bell();
    this.switchScene('island', 18, 23);
    this.spawnParticles(18 * 32, 23 * 32, '#38bdf8', 25);
    this.addFloatingText('⛵ ล่องเรือข้ามสมุทรมาถึงเกาะภูเขาไฟเขตร้อนแล้ว!', this.player.x - 30, this.player.y - 20, '#38bdf8');
};

Game.forageIslandPineapple = function(tx: number, ty: number) {
    const quality = this.rollItemQuality('foraging', this.player.skills?.foraging || 1);
    this.addItemToInventory('pineapple', 1, 'สับปะรดภูเขาไฟเขตร้อน', quality);
    this.addXp(25);
    SoundEngine.harvest();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 16, '#facc15', 16);

    const qBadge = this.getQualityBadgeText(quality);
    this.addFloatingText(\`🍍 เก็บสับปะรดป่าเขตร้อน \${qBadge}! (+25 XP)\`, tx * 32, ty * 32 - 15, '#fde047');

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
    this.addFloatingText(\`🥥 เก็บมะพร้าวป่า \${qBadge}! (+20 XP)\`, tx * 32, ty * 32 - 15, '#fef08a');

    this.map[ty][tx].type = 'sand';
    this.map[ty][tx].interactable = null;
    this.updateHUD();
};

Game.shakePalmTree = function(tx: number, ty: number) {
    SoundEngine.hit();
    this.spawnParticles(tx * 32 + 16, ty * 32 + 10, '#22c55e', 12);
    if (Math.random() < 0.6) {
        this.spawnDroppedItem('coconut', 1, 'มะพร้าวป่าสด', tx * 32 + 16, ty * 32 + 24);
        this.addFloatingText('🥥 มะพร้าวร่วงหล่นลงมา!', tx * 32, ty * 32 - 15, '#fef08a');
    } else {
        this.addFloatingText('🍃 ใบมะพร้าวพลิ้วไหวตามสายลม', tx * 32, ty * 32 - 15, '#86efac');
    }
};

// ========================================================
// 24. SEASONAL VILLAGE FESTIVALS
// ========================================================

Game.getCurrentFestival = function() {
    const sName = SEASONS[this.time.seasonIndex]?.id || 'spring';
    const day = this.time.day;
    const festivals = Object.values(FESTIVALS) as any[];
    return festivals.find(f => f.season === sName && f.day === day) || null;
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
    const fest = this.getCurrentFestival() || (FESTIVALS as any)['egg_festival'];
    const modal = document.getElementById('festivalModal');
    const titleEl = document.getElementById('festivalModalTitle');
    const contentEl = document.getElementById('festivalModalBodyContent');
    if (!modal || !titleEl || !contentEl) return;

    titleEl.textContent = fest.name;
    contentEl.innerHTML = \`
        <div style="font-size: 15px; color: #f8fafc; line-height: 1.6; margin-bottom: 12px;">
            \${fest.desc}
        </div>
        <div style="background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="color: #facc15; font-weight: bold; margin-bottom: 4px;">🏆 รางวัลกิจกรรมเทศกาล:</div>
            <div style="color: #cbd5e1;">\${fest.reward}</div>
        </div>
    \`;

    this.openModal('festivalModal');
};

Game.closeFestivalModal = function() {
    this.closeModal('festivalModal');
};

Game.startFestivalMiniGame = function() {
    const fest = this.getCurrentFestival();
    this.closeFestivalModal();

    if (!fest || fest.id === 'egg_festival') {
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
        this.addFloatingText('🥚 กิจกรรมล่าไข่อีสเตอร์เริ่มขึ้นแล้ว! ตามเก็บไข่หลากสีรอบตัว!', this.player.x - 40, this.player.y - 20, '#fde047');
    } else if (fest.id === 'fishing_derby') {
        SoundEngine.bell();
        this.addFloatingText('🎣 งานแข่งขันตกปลาฤดูร้อน! ตกปลาได้แต้มและทองคูณสอง!', this.player.x - 30, this.player.y - 20, '#38bdf8');
    } else if (fest.id === 'harvest_fair') {
        SoundEngine.levelUp();
        this.player.gold += 1000;
        this.addFloatingText('🎪 ผลผลิตฟาร์มของคุณชนะการประกวดงานเทศกาลฤดูใบไม้ร่วง! (+1,000G)', this.player.x - 40, this.player.y - 20, '#f59e0b');
    } else if (fest.id === 'winter_star') {
        SoundEngine.bell();
        this.addItemToInventory('diamond', 1, 'เพชรล้ำค่าแห่งดวงดาวฤดูหนาว', 3);
        this.addFloatingText('🌟 ชาวบ้านมอบของขวัญแห่งดวงดาวฤดูหนาวให้คุณ! (ได้รับ เพชรคุณภาพอิริเดียม 💜)', this.player.x - 40, this.player.y - 20, '#c084fc');
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

    this.addFloatingText('🥚 เก็บไข่อีสเตอร์สำเร็จ! (+150 G)', tx * 32, ty * 32 - 15, '#fde047');
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

    nameEl.textContent = \`💍 \${spouse.name} & คุณ\`;
    vowEl.textContent = \`"ต่อหน้าสักขีพยานชาวหมู่บ้านศิลาสุขาวดี... ทั้งสองจะร่วมแบ่งปันรอยยิ้ม กลิ่นอายดิน และสร้างฟาร์มแห่งความรักด้วยกันตลอดไป"\`;

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
    this.addFloatingText(\`💍 พิธีแต่งงานเสร็จสมบูรณ์! ยินดีต้อนรับ \${spouseName} เข้าสู่บ้านฟาร์มสุขใจ!\`, this.player.x - 40, this.player.y - 25, '#f472b6');
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
        this.addFloatingText(\`💋 จุมพิตยามเช้ากับ \${spouseName}! (⚡ พลังงาน +25 / ❤️ HP +15)\`, this.player.x - 30, this.player.y - 25, '#f472b6');
    } else {
        const quotes = [
            'บ้านของเราอบอุ่นที่สุดเลยนะ ข้าดีใจที่ได้แต่งงานกับเจ้า ♥',
            'สู้ๆ กับงานในฟาร์มวันนี้นะที่รัก ข้าจะเป็นกำลังใจให้เสมอ!',
            'วันนี้ลมพัดเย็นสบายจัง อยากออกไปเดินเล่นในสวนดอกไม้กับเจ้าจัง'
        ];
        const q = quotes[Math.floor(Math.random() * quotes.length)];
        this.addFloatingText(\`💖 \${spouseName}: "\${q}"\`, this.player.x - 30, this.player.y - 20, '#fbcfe8');
    }
};
`;

const oldExportAnchor = `if (typeof window !== 'undefined') {`;
if (code.includes(oldExportAnchor)) {
    code = code.replace(oldExportAnchor, expansionMethods + '\n' + oldExportAnchor);
    console.log('[12/12] Successfully inserted all 5 Expansion feature methods');
} else {
    console.error('FAILED to find oldExportAnchor');
}

fs.writeFileSync(gameTsPath, code, 'utf8');
console.log('Successfully updated game.ts! New size:', code.length, 'bytes');
