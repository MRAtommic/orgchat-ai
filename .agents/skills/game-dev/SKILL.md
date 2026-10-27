---
name: game-dev
description: Specialized 2D & Canvas Game Development skill. Covers 2.5D depth/Y-sorting, dynamic lighting, contact shadows, procedural pixel art, game feel/juice (screenshake, hitstop, particles), collision physics, and top-down RPG/action game architecture. Use whenever designing, debugging, polishing, or optimizing 2D canvas, web, or indie games.
---

# 🎮 2D Game Development & Polish Engine Skill (Canvas / Web / Indie)

A rigorous, battle-tested engineering and art-direction guide for 2D Canvas, TypeScript/JavaScript, and indie games (Top-down, RPG, Roguelike, Farm Sim, Survivor-like).

---

## 1. The Depth & Dimensionality Rule (แก้ปัญหาเกม "แบน / ขาดมิติ")

Top-down and 2.5D isometric games feel flat when developers render entities in fixed procedural steps (e.g. tiles -> buildings -> NPCs -> player). This breaks spatial illusion.

### A. Strict Y-Sorting (Depth / Z-Ordering)
Every physical entity standing on the ground must be collected into a dynamic render list and sorted by its **foot position (Y-anchor)** every frame:

```typescript
interface Renderable {
    depthY: number; // The actual ground contact point (e.g., entity.y + entity.height)
    render(ctx: CanvasRenderingContext2D): void;
}

// 1. Draw Ground / Bottom Tile Layers (grass, soil, paths, water)
drawGroundTiles(ctx, camera);

// 2. Collect All Ground-Standing Entities for Y-Sorting
const renderables: Renderable[] = [];

// Push Player, NPCs, Animals, Monsters, Buildings, Trees, Chests, Ground Items
renderables.push({ depthY: player.y + player.anchorY, render: (ctx) => drawPlayer(ctx) });
animals.forEach(a => renderables.push({ depthY: a.y + a.height, render: (ctx) => drawAnimal(ctx, a) }));
trees.forEach(t => renderables.push({ depthY: t.baseY, render: (ctx) => drawTree(ctx, t) }));
buildings.forEach(b => renderables.push({ depthY: b.baseY, render: (ctx) => drawBuilding(ctx, b) }));

// 3. Sort by Y ascending (entities higher up on screen are drawn behind lower ones)
renderables.sort((a, b) => a.depthY - b.depthY);
for (const obj of renderables) {
    obj.render(ctx);
}

// 4. Draw Overhead / Canopy / Sky Layers (clouds, flying birds, weather overlays)
drawWeatherAndLighting(ctx);
```

---

## 2. The Grounding & Shadow System (แก้ปัญหาเกม "ไม่มีเงา / วัตถุลอย")

In 2D top-down games, objects look like stickers pasted onto grass unless they are firmly grounded with **Contact Shadows** and **Directional Ambient Shadows**.

### A. Universal Contact Shadow (Ground Occlusion)
Every character, monster, tree, and building must cast an elliptical shadow at its feet **before** the sprite is drawn:

```typescript
function drawContactShadow(
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    radiusX: number,
    radiusY: number,
    alpha: number = 0.28
) {
    ctx.save();
    ctx.fillStyle = `rgba(15, 23, 42, ${alpha})`; // Soft cool dark tone, never pure pitch black
    ctx.beginPath();
    ctx.ellipse(x, y, radiusX, radiusY, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
}
```
* **Player / Humanoid**: `radiusX: 9`, `radiusY: 4.5`, offset under feet.
* **Large Animals (Cow, Pig)**: `radiusX: 16`, `radiusY: 7`.
* **Trees**: `radiusX: 18`, `radiusY: 8` at trunk base.
* **Buildings / Stalls**: Rounded rectangle or large sheared ellipse along the southern wall.

### B. Dynamic Day/Night & Lighting Cookie (Multiplication Blend)
Never use a flat translucent color `fillRect()` over the screen for night or dusk—it washes out contrast and makes everything look murky.

Use Canvas **`destination-out`** or **`globalCompositeOperation = 'multiply'`**:
1. Fill a dark ambient overlay canvas (e.g. Deep Midnight Navy `#090d16` with 80% opacity).
2. Cut out circular/radial gradient light holes where torches, windows, lanterns, or campfires are positioned.
3. Draw the ambient canvas over the game view.

```typescript
// Render warm glowing lights that cut through darkness
const lightGrad = ctx.createRadialGradient(lightX, lightY, 4, lightX, lightY, lightRadius);
lightGrad.addColorStop(0, 'rgba(255, 220, 140, 0.9)');
lightGrad.addColorStop(0.5, 'rgba(255, 180, 80, 0.35)');
lightGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
```

---

## 3. Collision Box Architecture (แก้ปัญหา "บั๊กเยอะ / ติดกำแพง / เดินทะลุ")

The #1 cause of bugs in 2D top-down games is using the entire visual sprite bounding box for physics collision.

### A. Separation of Hitbox vs Collision Box:
1. **Visual Bounds**: Where the character is rendered (e.g., 32x48 px).
2. **Hurtbox / Hitbox**: The body volume that receives or deals damage (e.g., 20x36 px centered).
3. **Feet Collision Box (Solid Obstacle Collider)**: **Only the feet contact area** (e.g., 18x8 px at the bottom).

```
Visual Sprite (32x48)
┌──────────────────────┐
│       (Head)         │
│     [Hurtbox]        │
│       (Torso)        │
│                      │
├──────────────────────┤
│ [Feet Collider 18x8] │  <-- ONLY this rectangle checks collisions against walls!
└──────────────────────┘
```
This allows the player's head and shoulders to overlap slightly behind fences, trees, and walls naturally, giving immediate 2.5D depth without getting stuck.

### B. Wall-Sliding (Preventing Sticky Corners):
When moving diagonally against a wall, decompose velocity:
* If `(player.x + vx, player.y)` hits a wall, test if `(player.x, player.y + vy)` is clear. If so, apply `vy` so the player slides smoothly instead of stopping dead.

---

## 4. Game Feel & "Juice" Checklist

1. **Screen Shake**: When hitting or taking damage, apply a damped trauma shake `angle = maxAngle * trauma^2 * random(-1, 1)`.
2. **Hit Stop / Freeze Frame**: When landing a critical hit or harvesting a big crop, freeze the game update loop for 40-70ms (`3-5 frames`).
3. **Squash & Stretch**:
   - On Jump/Action: Scale `(sx: 0.85, sy: 1.2)`.
   - On Landing/Impact: Scale `(sx: 1.25, sy: 0.8)`.
   - Smoothly interpolate back to `(1.0, 1.0)` using lerp.
4. **Impact Particles**: Don't just spawn numbers. Spawn 4-8 directional debris particles (dirt crumbs for hoes, wood splinters for axes, gold sparkles for coin pickups).
5. **Floating Feedback Curves**: Animate floating text with an elastic bounce up, brief float, then alpha fadeout.

---

## 5. Performance & Offscreen Canvas Caching

* **Never run raw procedural loops** (e.g., `fillRect` loops to generate pixel art) inside the main 60 FPS animation loop.
* Pre-bake procedural sprites onto hidden offscreen `<canvas>` elements once during loading, then use fast native `ctx.drawImage(cachedCanvas, x, y)`.
* **Viewport Culling**: Check `entity.x + entity.width > camera.x && entity.x < camera.x + viewWidth` before drawing.

---

## 6. Systematic Bug Investigation in 2D Games

When hunting bugs in 2D game loops:
1. **Check delta time (`dt`) spikes**: Clamp `Math.min(dt, 0.05)` to prevent physics tunneling when switching browser tabs.
2. **Check Coordinate Rounding**: Always `Math.round()` screen drawing coordinates to avoid subpixel shimmer or fuzzy pixel art lines (`imageSmoothingEnabled = false`).
3. **Check Event Listeners & Modals**: Ensure UI modal clicks don't bleed through to the canvas click listeners (`e.stopPropagation()`).
