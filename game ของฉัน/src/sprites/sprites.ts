/* ========================================================
    Pixel Art Sprite Engine for 2D Stardew-Style Farm
   Draws pure retro 16-bit / 32-bit pixel sprites directly
   onto offscreen canvases for crisp, fast rendering.
   ZERO emojis or AI slop!
   ======================================================== */

export const SPRITES: Record<string, any> = {};

(function() {
    function makeCanvas(w, h) {
        const c = document.createElement('canvas');
        c.width = w;
        c.height = h;
        const ctx = c.getContext('2d');
        ctx.imageSmoothingEnabled = false;
        return { canvas: c, ctx: ctx };
    }

    // ==========================================
    // 1. TILES (32x32)
    // ==========================================

    function createGrassTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Rich vibrant meadow green
        ctx.fillStyle = '#559934';
        ctx.fillRect(0, 0, 32, 32);

        // Subtle grass shading and texture
        ctx.fillStyle = '#48852a';
        ctx.fillRect(3, 4, 2, 4);
        ctx.fillRect(5, 2, 2, 3);
        ctx.fillRect(19, 14, 2, 4);
        ctx.fillRect(17, 16, 2, 2);
        ctx.fillRect(9, 22, 2, 4);
        ctx.fillRect(25, 6, 2, 4);
        ctx.fillRect(13, 26, 2, 3);
        ctx.fillRect(27, 24, 2, 3);

        // Golden sunlight highlights
        ctx.fillStyle = '#6ab840';
        ctx.fillRect(4, 3, 2, 2);
        ctx.fillRect(20, 13, 2, 2);
        ctx.fillRect(10, 21, 2, 2);
        ctx.fillRect(26, 5, 2, 2);
        ctx.fillRect(14, 8, 2, 1);
        ctx.fillRect(6, 16, 2, 1);

        // Cute 4-petal chamomile daisies
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(11, 11, 3, 3);
        ctx.fillRect(10, 12, 5, 1);
        ctx.fillStyle = '#fde047';
        ctx.fillRect(12, 12, 1, 1);

        // Small blue wildflower
        ctx.fillStyle = '#60a5fa';
        ctx.fillRect(23, 20, 2, 2);
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(23, 20, 1, 1);

        return canvas;
    }

    function createSoilDryTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Rich warm crumbly earth
        ctx.fillStyle = '#8b572a';
        ctx.fillRect(0, 0, 32, 32);

        // Deep soil furrows with shading
        ctx.fillStyle = '#5c3514';
        ctx.fillRect(0, 4, 32, 3);
        ctx.fillRect(0, 12, 32, 3);
        ctx.fillRect(0, 20, 32, 3);
        ctx.fillRect(0, 28, 32, 3);

        // Raised earthen ridges & highlights
        ctx.fillStyle = '#a66d3b';
        ctx.fillRect(0, 2, 32, 2);
        ctx.fillRect(0, 10, 32, 2);
        ctx.fillRect(0, 18, 32, 2);
        ctx.fillRect(0, 26, 32, 2);

        // Little earth clumps and pebbles
        ctx.fillStyle = '#45250c';
        ctx.fillRect(5, 7, 2, 2);
        ctx.fillRect(15, 15, 2, 2);
        ctx.fillRect(24, 23, 2, 2);
        ctx.fillRect(8, 29, 2, 2);

        ctx.fillStyle = '#c48952';
        ctx.fillRect(6, 6, 1, 1);
        ctx.fillRect(16, 14, 1, 1);
        ctx.fillRect(25, 22, 1, 1);

        return canvas;
    }

    function createSoilWetTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Glistening dark hydrated earth
        ctx.fillStyle = '#42240e';
        ctx.fillRect(0, 0, 32, 32);

        // Deep soaked furrows
        ctx.fillStyle = '#2b1406';
        ctx.fillRect(0, 4, 32, 3);
        ctx.fillRect(0, 12, 32, 3);
        ctx.fillRect(0, 20, 32, 3);
        ctx.fillRect(0, 28, 32, 3);

        // Moist ridge highlights
        ctx.fillStyle = '#5a3316';
        ctx.fillRect(0, 2, 32, 2);
        ctx.fillRect(0, 10, 32, 2);
        ctx.fillRect(0, 18, 32, 2);
        ctx.fillRect(0, 26, 32, 2);

        // Glistening water sheen
        ctx.fillStyle = '#60829f';
        ctx.fillRect(4, 5, 4, 1);
        ctx.fillRect(18, 13, 5, 1);
        ctx.fillRect(10, 21, 4, 1);
        ctx.fillRect(22, 29, 5, 1);

        ctx.fillStyle = '#93c5fd';
        ctx.fillRect(5, 5, 2, 1);
        ctx.fillRect(19, 13, 2, 1);
        ctx.fillRect(11, 21, 2, 1);

        return canvas;
    }

    function createPathTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Sandy earthy mortar base
        ctx.fillStyle = '#6b543e';
        ctx.fillRect(0, 0, 32, 32);

        // Irregular interlocking cobblestones (seamless natural road)
        function drawStone(x, y, w, h, baseCol, lightCol, darkCol) {
            ctx.fillStyle = darkCol;
            ctx.fillRect(x, y, w, h);
            ctx.fillStyle = baseCol;
            ctx.fillRect(x + 1, y + 1, w - 2, h - 2);
            ctx.fillStyle = lightCol;
            ctx.fillRect(x + 1, y + 1, w - 3, 2);
            ctx.fillRect(x + 1, y + 1, 2, h - 3);
        }

        // Row 1
        drawStone(1, 1, 14, 10, '#949ba3', '#b4bac2', '#585e66');
        drawStone(16, 1, 15, 9, '#838a92', '#a2a9b2', '#4e545c');

        // Row 2
        drawStone(1, 12, 9, 9, '#7b828a', '#9da5ad', '#464c53');
        drawStone(11, 11, 12, 10, '#9da4ac', '#c0c6ce', '#5d646d');
        drawStone(24, 11, 7, 9, '#888f98', '#a8afb8', '#50565e');

        // Row 3
        drawStone(1, 22, 13, 9, '#8c939b', '#acb3bc', '#525860');
        drawStone(15, 22, 16, 9, '#9ba2aa', '#bdc4cc', '#5c626a');

        // Moss tufts in the stone cracks
        ctx.fillStyle = '#4c862e';
        ctx.fillRect(14, 8, 2, 3);
        ctx.fillRect(23, 18, 3, 2);
        ctx.fillRect(8, 20, 2, 2);

        return canvas;
    }


    function createFenceTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Posts
        ctx.fillStyle = '#7a4a24';
        ctx.fillRect(6, 6, 6, 24);
        ctx.fillRect(20, 6, 6, 24);

        ctx.fillStyle = '#a66a38';
        ctx.fillRect(7, 8, 4, 22);
        ctx.fillRect(21, 8, 4, 22);

        ctx.fillStyle = '#7a4a24';
        ctx.fillRect(8, 4, 2, 2);
        ctx.fillRect(22, 4, 2, 2);

        // Rails
        ctx.fillStyle = '#5c3517';
        ctx.fillRect(0, 11, 32, 4);
        ctx.fillRect(0, 21, 32, 4);

        ctx.fillStyle = '#8f572b';
        ctx.fillRect(0, 12, 32, 2);
        ctx.fillRect(0, 22, 32, 2);
        return canvas;
    }

    function createWaterTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#2b78b8';
        ctx.fillRect(0, 0, 32, 32);

        ctx.fillStyle = '#4293d6';
        ctx.fillRect(4, 6, 12, 2);
        ctx.fillRect(16, 18, 14, 2);
        ctx.fillRect(6, 26, 10, 2);

        ctx.fillStyle = '#7ec5f8';
        ctx.fillRect(6, 7, 5, 1);
        ctx.fillRect(18, 19, 6, 1);

        ctx.fillStyle = '#1c5d94';
        ctx.fillRect(0, 0, 32, 2);
        ctx.fillRect(0, 0, 2, 32);
        return canvas;
    }

    function createShippingBin() {
        const { canvas, ctx } = makeCanvas(48, 48);
        ctx.fillStyle = '#5c3517';
        ctx.fillRect(4, 14, 40, 30);

        ctx.fillStyle = '#8a5225';
        ctx.fillRect(6, 16, 36, 26);

        ctx.fillStyle = '#424549';
        ctx.fillRect(4, 20, 40, 4);
        ctx.fillRect(4, 34, 40, 4);

        ctx.fillStyle = '#83888e';
        ctx.fillRect(6, 21, 36, 2);
        ctx.fillRect(6, 35, 36, 2);

        ctx.fillStyle = '#6f3e1a';
        ctx.fillRect(2, 8, 44, 8);
        ctx.fillStyle = '#9c5f2d';
        ctx.fillRect(4, 9, 40, 5);

        ctx.fillStyle = '#d4af37';
        ctx.fillRect(22, 17, 4, 6);

        ctx.fillStyle = '#73411b';
        ctx.fillRect(16, 16, 2, 26);
        ctx.fillRect(30, 16, 2, 26);
        return canvas;
    }

    function createWell() {
        const { canvas, ctx } = makeCanvas(48, 48);
        ctx.fillStyle = '#62686e';
        ctx.fillRect(6, 24, 36, 20);
        ctx.fillStyle = '#8b939c';
        ctx.fillRect(8, 26, 32, 16);

        ctx.fillStyle = '#4b5055';
        ctx.fillRect(8, 33, 32, 2);
        ctx.fillRect(18, 26, 2, 7);
        ctx.fillRect(30, 26, 2, 7);
        ctx.fillRect(24, 35, 2, 7);

        ctx.fillStyle = '#1c4d79';
        ctx.fillRect(10, 24, 28, 4);

        ctx.fillStyle = '#6a3b17';
        ctx.fillRect(8, 8, 4, 18);
        ctx.fillRect(36, 8, 4, 18);

        ctx.fillStyle = '#a83232';
        ctx.beginPath();
        ctx.moveTo(4, 10);
        ctx.lineTo(24, 0);
        ctx.lineTo(44, 10);
        ctx.fill();

        ctx.fillStyle = '#7e2020';
        ctx.fillRect(4, 10, 40, 3);

        ctx.fillStyle = '#b8944d';
        ctx.fillRect(23, 8, 2, 12);
        ctx.fillStyle = '#5c3517';
        ctx.fillRect(21, 18, 6, 6);

        return canvas;
    }

    function createTree() {
        const { canvas, ctx } = makeCanvas(48, 64);
        // Gnarled Oak Trunk & Roots
        ctx.fillStyle = '#42220b';
        ctx.fillRect(18, 36, 12, 24);
        ctx.fillRect(15, 54, 5, 6);
        ctx.fillRect(28, 54, 5, 6);

        ctx.fillStyle = '#633818';
        ctx.fillRect(20, 38, 8, 20);
        ctx.fillRect(21, 40, 3, 16);

        // Volumetric lush canopy clusters
        function drawLeafCluster(cx, cy, r, baseCol, midCol, lightCol) {
            ctx.fillStyle = baseCol;
            ctx.beginPath(); ctx.arc(cx, cy + 2, r, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = midCol;
            ctx.beginPath(); ctx.arc(cx, cy, r - 1, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = lightCol;
            ctx.beginPath(); ctx.arc(cx - 2, cy - 3, r * 0.65, 0, Math.PI * 2); ctx.fill();
        }

        // Deep shadow clusters
        drawLeafCluster(24, 30, 18, '#183c13', '#23571d', '#357d2b');
        drawLeafCluster(13, 26, 14, '#183c13', '#23571d', '#357d2b');
        drawLeafCluster(35, 26, 14, '#183c13', '#23571d', '#357d2b');
        drawLeafCluster(24, 16, 16, '#23571d', '#357d2b', '#4fa336');

        // Bright top foliage highlights
        ctx.fillStyle = '#6ec046';
        ctx.fillRect(20, 6, 8, 4);
        ctx.fillRect(10, 16, 6, 4);
        ctx.fillRect(30, 16, 6, 4);

        // Ripe Red Apples
        const apples = [
            { x: 16, y: 18 }, { x: 28, y: 22 }, { x: 20, y: 30 },
            { x: 34, y: 28 }, { x: 12, y: 28 }
        ];
        apples.forEach(a => {
            ctx.fillStyle = '#dc2626';
            ctx.beginPath(); ctx.arc(a.x + 2, a.y + 2, 2.5, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(a.x + 1, a.y + 1, 1, 1);
            ctx.fillStyle = '#15803d';
            ctx.fillRect(a.x + 2, a.y - 1, 1, 1);
        });

        return canvas;
    }

    function createTreeStump() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Outer bark
        ctx.fillStyle = '#42220b';
        ctx.fillRect(8, 16, 16, 12);
        ctx.fillRect(6, 24, 4, 4);
        ctx.fillRect(22, 24, 4, 4);
        // Tree ring top cut
        ctx.fillStyle = '#d4a373';
        ctx.beginPath(); ctx.ellipse(16, 16, 8, 4, 0, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = '#b45309'; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.ellipse(16, 16, 5, 2.5, 0, 0, Math.PI * 2); ctx.stroke();
        // Inner heartwood
        ctx.fillStyle = '#78350f';
        ctx.fillRect(15, 15, 2, 2);
        // Axe chop mark
        ctx.fillStyle = '#451a03';
        ctx.fillRect(18, 14, 2, 3);
        return canvas;
    }

    function createSapling() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Little stem
        ctx.fillStyle = '#78350f';
        ctx.fillRect(15, 20, 2, 8);
        // Little green leaves
        ctx.fillStyle = '#22c55e';
        ctx.beginPath(); ctx.ellipse(13, 17, 5, 3, -Math.PI / 4, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.ellipse(19, 17, 5, 3, Math.PI / 4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#86efac';
        ctx.fillRect(15, 14, 2, 4);
        return canvas;
    }

    function createHouse() {
        const { canvas, ctx } = makeCanvas(96, 80);
        // Stone Foundation Base
        ctx.fillStyle = '#64748b';
        ctx.fillRect(8, 72, 80, 5);
        ctx.fillStyle = '#475569';
        for (let x = 8; x < 88; x += 10) ctx.fillRect(x, 72, 1, 5);

        // Warm Timber Plank Walls
        ctx.fillStyle = '#b4723a';
        ctx.fillRect(8, 32, 80, 40);

        // Wood plank grooves & grain
        ctx.fillStyle = '#83471c';
        for (let y = 37; y < 72; y += 7) {
            ctx.fillRect(8, y, 80, 2);
        }
        ctx.fillStyle = '#d28c50';
        for (let y = 39; y < 72; y += 7) {
            ctx.fillRect(8, y, 80, 1);
        }

        // Stone Chimney on Right Roof
        ctx.fillStyle = '#64748b';
        ctx.fillRect(72, 6, 14, 26);
        ctx.fillStyle = '#475569';
        ctx.fillRect(70, 4, 18, 4);
        ctx.fillRect(74, 12, 4, 3);
        ctx.fillRect(80, 20, 4, 3);
        // Smoke puffs
        ctx.fillStyle = 'rgba(241, 245, 249, 0.7)';
        ctx.beginPath(); ctx.arc(79, 1, 3, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(83, -4, 4, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(87, -9, 5, 0, Math.PI * 2); ctx.fill();

        // Shingle Roof (Warm terracotta layered tiles)
        ctx.fillStyle = '#5c1d15'; // Deep roof shadow
        ctx.beginPath();
        ctx.moveTo(0, 36); ctx.lineTo(48, 2); ctx.lineTo(96, 36); ctx.fill();

        ctx.fillStyle = '#991b1b'; // Base terracotta roof
        ctx.beginPath();
        ctx.moveTo(4, 34); ctx.lineTo(48, 5); ctx.lineTo(92, 34); ctx.fill();

        // Layered shingle bevels
        ctx.fillStyle = '#b91c1c';
        ctx.beginPath();
        ctx.moveTo(8, 28); ctx.lineTo(48, 8); ctx.lineTo(88, 28); ctx.fill();
        ctx.fillStyle = '#dc2626';
        ctx.beginPath();
        ctx.moveTo(14, 21); ctx.lineTo(48, 11); ctx.lineTo(82, 21); ctx.fill();

        // Roof Trim Fascia Board
        ctx.fillStyle = '#78350f';
        ctx.fillRect(0, 33, 96, 4);
        ctx.fillStyle = '#f59e0b';
        ctx.fillRect(0, 34, 96, 1);

        // Arched Wooden Front Door
        ctx.fillStyle = '#451a03';
        ctx.fillRect(40, 46, 16, 26);
        ctx.fillStyle = '#6d3412';
        ctx.fillRect(42, 48, 12, 24);
        // Vertical door planks
        ctx.fillStyle = '#451a03';
        ctx.fillRect(46, 48, 1, 24);
        ctx.fillRect(50, 48, 1, 24);
        // Brass Door Knob
        ctx.fillStyle = '#facc15';
        ctx.fillRect(51, 60, 2, 3);
        // Welcome Stone Step
        ctx.fillStyle = '#94a3b8';
        ctx.fillRect(38, 72, 20, 4);

        // 2 Cozy Arched Cottage Windows with Flower Planter Boxes
        function drawWindow(wx, wy) {
            // Dark window frame
            ctx.fillStyle = '#3b1c08';
            ctx.fillRect(wx - 1, wy - 1, 16, 18);
            // Warm amber glowing glass
            ctx.fillStyle = '#fef08a';
            ctx.fillRect(wx, wy, 14, 16);
            // Interior cozy yellow
            ctx.fillStyle = '#fde047';
            ctx.fillRect(wx + 1, wy + 1, 12, 14);
            // Window Mullions (crossbars)
            ctx.fillStyle = '#78350f';
            ctx.fillRect(wx + 6, wy, 2, 16);
            ctx.fillRect(wx, wy + 7, 14, 2);

            // Planter Box Overflowing with Flowers
            ctx.fillStyle = '#5c2d10';
            ctx.fillRect(wx - 2, wy + 16, 18, 5);
            // Green leaves
            ctx.fillStyle = '#16a34a';
            ctx.fillRect(wx - 1, wy + 14, 16, 3);
            // Red and yellow flowers
            ctx.fillStyle = '#ef4444';
            ctx.fillRect(wx, wy + 14, 2, 2);
            ctx.fillRect(wx + 8, wy + 14, 2, 2);
            ctx.fillStyle = '#facc15';
            ctx.fillRect(wx + 4, wy + 14, 2, 2);
            ctx.fillRect(wx + 12, wy + 14, 2, 2);
        }

        drawWindow(16, 46);
        drawWindow(66, 46);

        // Porch Lantern beside door
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(36, 52, 3, 6);
        ctx.fillStyle = '#fef08a';
        ctx.fillRect(36, 54, 3, 3);

        return canvas;
    }

    function createBarn() {
        const { canvas, ctx } = makeCanvas(96, 80);
        // Red Barn Wooden Siding
        ctx.fillStyle = '#831818';
        ctx.fillRect(8, 28, 80, 48);

        // Vertical red plank grooves
        ctx.fillStyle = '#991b1b';
        ctx.fillRect(10, 28, 76, 48);
        ctx.fillStyle = '#6b1111';
        for (let x = 12; x < 84; x += 6) ctx.fillRect(x, 28, 1, 48);

        // Crisp White Corner Posts & Trims
        ctx.fillStyle = '#f8fafc';
        ctx.fillRect(8, 28, 5, 48);
        ctx.fillRect(83, 28, 5, 48);
        ctx.fillRect(8, 72, 80, 4);

        // Classic Dutch Gambrel Roof (Charcoal slate tiles)
        ctx.fillStyle = '#1e293b';
        ctx.beginPath();
        ctx.moveTo(4, 30);
        ctx.lineTo(24, 8);
        ctx.lineTo(72, 8);
        ctx.lineTo(92, 30);
        ctx.fill();

        ctx.fillStyle = '#334155';
        ctx.beginPath();
        ctx.moveTo(6, 28);
        ctx.lineTo(25, 10);
        ctx.lineTo(71, 10);
        ctx.lineTo(90, 28);
        ctx.fill();

        // White Roof Edge Fascia
        ctx.fillStyle = '#f8fafc';
        ctx.fillRect(2, 28, 92, 3);

        // Rooster Weather Vane on Peak
        ctx.fillStyle = '#d97706';
        ctx.fillRect(47, 2, 2, 6);
        ctx.fillRect(45, 1, 6, 2);
        ctx.beginPath(); ctx.arc(48, 1, 2, 0, Math.PI * 2); ctx.fill();

        // Upper Hayloft with Golden Straw spilling out
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(40, 15, 16, 12);
        ctx.fillStyle = '#451a03';
        ctx.fillRect(40, 15, 16, 2);
        // Spilling golden hay
        ctx.fillStyle = '#eab308';
        ctx.fillRect(41, 22, 14, 6);
        ctx.fillStyle = '#facc15';
        ctx.fillRect(42, 24, 4, 5);
        ctx.fillRect(48, 24, 5, 6);
        ctx.fillRect(52, 23, 3, 4);

        // Double Sliding Red Barn Doors with White X-Braces
        ctx.fillStyle = '#1e293b'; // Door frame shadow
        ctx.fillRect(32, 42, 32, 34);

        // Left Door with White X-brace
        ctx.fillStyle = '#991b1b';
        ctx.fillRect(34, 44, 13, 30);
        ctx.fillStyle = '#f8fafc';
        ctx.fillRect(34, 44, 13, 2);
        ctx.fillRect(34, 72, 13, 2);
        ctx.fillRect(34, 44, 2, 30);
        ctx.fillRect(45, 44, 2, 30);
        // Diagonal X
        ctx.strokeStyle = '#f8fafc'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(35, 45); ctx.lineTo(46, 73); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(46, 45); ctx.lineTo(35, 73); ctx.stroke();

        // Right Door with White X-brace
        ctx.fillStyle = '#991b1b';
        ctx.fillRect(49, 44, 13, 30);
        ctx.fillStyle = '#f8fafc';
        ctx.fillRect(49, 44, 13, 2);
        ctx.fillRect(49, 72, 13, 2);
        ctx.fillRect(49, 44, 2, 30);
        ctx.fillRect(60, 44, 2, 30);
        // Diagonal X
        ctx.beginPath(); ctx.moveTo(50, 45); ctx.lineTo(61, 73); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(61, 45); ctx.lineTo(50, 73); ctx.stroke();

        // Iron Sliding Door Rail on Top
        ctx.fillStyle = '#334155';
        ctx.fillRect(30, 41, 36, 2);

        // Warm Wall Lantern
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(24, 50, 4, 6);
        ctx.fillStyle = '#fef08a';
        ctx.fillRect(25, 52, 2, 3);

        return canvas;
    }

    function createShopBuilding() {
        const { canvas, ctx } = makeCanvas(96, 80);
        // Warm Cream Plaster & Timber Walls
        ctx.fillStyle = '#fef3c7';
        ctx.fillRect(8, 30, 80, 46);

        // Tudor Dark Wood Timber Framing
        ctx.fillStyle = '#6b3410';
        ctx.fillRect(8, 30, 80, 3);
        ctx.fillRect(8, 72, 80, 4);
        ctx.fillRect(8, 30, 4, 46);
        ctx.fillRect(84, 30, 4, 46);
        ctx.fillRect(52, 30, 4, 46); // Center division

        // Festive Scalloped Striped Fabric Awning (Yellow & Burnt Orange)
        const awningColors = ['#f59e0b', '#c2410c', '#f59e0b', '#c2410c', '#f59e0b', '#c2410c', '#f59e0b', '#c2410c', '#f59e0b', '#c2410c'];
        awningColors.forEach((col, idx) => {
            ctx.fillStyle = col;
            ctx.fillRect(8 + idx * 8, 22, 8, 12);
            // Scallop bottom curve
            ctx.beginPath();
            ctx.arc(12 + idx * 8, 34, 4, 0, Math.PI);
            ctx.fill();
        });
        // Awning shadow
        ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
        ctx.fillRect(8, 35, 80, 2);

        // Large Bay Showcase Window with Produce Baskets
        ctx.fillStyle = '#451a03';
        ctx.fillRect(14, 40, 34, 26);
        ctx.fillStyle = '#bae6fd';
        ctx.fillRect(16, 42, 30, 22);

        // Wooden Display Crates Inside Window
        ctx.fillStyle = '#92400e';
        ctx.fillRect(18, 52, 12, 10);
        ctx.fillRect(32, 52, 12, 10);

        // Produce: Red Apples & Orange Carrots & Bread
        ctx.fillStyle = '#ef4444';
        ctx.fillRect(20, 50, 3, 3); ctx.fillRect(24, 50, 3, 3); ctx.fillRect(22, 48, 3, 3);
        ctx.fillStyle = '#f97316';
        ctx.fillRect(34, 50, 3, 4); ctx.fillRect(38, 50, 3, 4);

        // Glass Glare reflection lines
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(18, 44); ctx.lineTo(24, 50);
        ctx.moveTo(28, 44); ctx.lineTo(36, 52);
        ctx.stroke();

        // Shop Entrance Door
        ctx.fillStyle = '#451a03';
        ctx.fillRect(60, 38, 20, 38);
        ctx.fillStyle = '#78350f';
        ctx.fillRect(62, 40, 16, 34);
        // Glass Upper Pane
        ctx.fillStyle = '#bae6fd';
        ctx.fillRect(64, 42, 12, 14);
        // Brass Knob & Welcome Bell
        ctx.fillStyle = '#facc15';
        ctx.fillRect(64, 58, 2, 3);
        ctx.fillRect(69, 36, 3, 3); // Brass Bell

        // Hanging Wrought Iron Signboard with Golden Wheat 
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(4, 20, 10, 2);
        ctx.fillRect(8, 22, 2, 4);
        ctx.fillStyle = '#b45309';
        ctx.fillRect(4, 25, 12, 9);
        ctx.fillStyle = '#fef08a';
        ctx.fillRect(5, 26, 10, 7);
        // Wheat Sheaf Icon
        ctx.fillStyle = '#d97706';
        ctx.fillRect(9, 27, 2, 5);
        ctx.fillRect(7, 28, 2, 2);
        ctx.fillRect(11, 28, 2, 2);

        // Flower barrels beside door
        ctx.fillStyle = '#78350f';
        ctx.fillRect(82, 60, 6, 12);
        ctx.fillStyle = '#f43f5e';
        ctx.fillRect(82, 57, 6, 4);

        return canvas;
    }

    function createMill() {
        const { canvas, ctx } = makeCanvas(64, 80);
        // Whitewashed Cobblestone Tower
        ctx.fillStyle = '#cbd5e1';
        ctx.fillRect(16, 28, 32, 48);

        // Stone texture & shading
        ctx.fillStyle = '#94a3b8';
        ctx.fillRect(16, 28, 4, 48);
        ctx.fillRect(44, 28, 4, 48);
        ctx.fillRect(20, 36, 6, 3);
        ctx.fillRect(34, 46, 6, 3);
        ctx.fillRect(22, 58, 7, 3);

        // Climbing Green Ivy
        ctx.fillStyle = '#15803d';
        ctx.fillRect(16, 60, 5, 14);
        ctx.fillRect(18, 50, 4, 12);
        ctx.fillRect(16, 42, 3, 8);

        // Conical Shingle Roof
        ctx.fillStyle = '#7c2d12';
        ctx.beginPath();
        ctx.moveTo(10, 28); ctx.lineTo(32, 4); ctx.lineTo(54, 28); ctx.fill();
        ctx.fillStyle = '#9a3412';
        ctx.beginPath();
        ctx.moveTo(14, 28); ctx.lineTo(32, 7); ctx.lineTo(50, 28); ctx.fill();

        // Wooden Door & Sacks of Flour
        ctx.fillStyle = '#451a03';
        ctx.fillRect(26, 54, 12, 22);
        ctx.fillStyle = '#78350f';
        ctx.fillRect(27, 56, 10, 20);
        // Flour Sacks
        ctx.fillStyle = '#f8fafc';
        ctx.beginPath(); ctx.arc(42, 70, 4, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(40, 72, 4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#d97706';
        ctx.fillRect(41, 67, 2, 2);

        // Windmill Central Hub
        ctx.fillStyle = '#451a03';
        ctx.beginPath(); ctx.arc(32, 28, 5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#d97706';
        ctx.beginPath(); ctx.arc(32, 28, 2, 0, Math.PI * 2); ctx.fill();

        // 4 Large Wooden Lattice Blades with Cream Sails
        ctx.strokeStyle = '#78350f'; ctx.lineWidth = 2;
        ctx.fillStyle = '#fef3c7';

        // Blade 1 (Top Left)
        ctx.fillRect(14, 10, 16, 6);
        ctx.beginPath(); ctx.moveTo(32, 28); ctx.lineTo(12, 8); ctx.stroke();
        // Blade 2 (Top Right)
        ctx.fillRect(34, 14, 6, 16);
        ctx.beginPath(); ctx.moveTo(32, 28); ctx.lineTo(52, 8); ctx.stroke();
        // Blade 3 (Bottom Right)
        ctx.fillRect(34, 34, 16, 6);
        ctx.beginPath(); ctx.moveTo(32, 28); ctx.lineTo(52, 48); ctx.stroke();
        // Blade 4 (Bottom Left)
        ctx.fillRect(24, 34, 6, 16);
        ctx.beginPath(); ctx.moveTo(32, 28); ctx.lineTo(12, 48); ctx.stroke();

        return canvas;
    }

    function createHunterPost() {
        const { canvas, ctx } = makeCanvas(64, 64);
        // Forest Ranger Log Cabin Lodge
        // Heavy Sturdy Corner Logs
        ctx.fillStyle = '#5c3517';
        ctx.fillRect(8, 24, 48, 36);

        // Horizontal Log Siding with Notches
        ctx.fillStyle = '#78350f';
        for (let y = 26; y < 60; y += 6) {
            ctx.fillRect(10, y, 44, 4);
        }
        ctx.fillStyle = '#451a03';
        for (let y = 25; y < 60; y += 6) {
            ctx.fillRect(10, y, 44, 1);
        }

        // Green Cedar Shake Roof with Moss
        ctx.fillStyle = '#14532d';
        ctx.beginPath();
        ctx.moveTo(6, 24); ctx.lineTo(32, 4); ctx.lineTo(58, 24); ctx.fill();
        ctx.fillStyle = '#166534';
        ctx.beginPath();
        ctx.moveTo(9, 23); ctx.lineTo(32, 7); ctx.lineTo(55, 23); ctx.fill();

        // Front Porch & Heavy Door
        ctx.fillStyle = '#3b1c08';
        ctx.fillRect(24, 38, 16, 22);
        ctx.fillStyle = '#5c2d10';
        ctx.fillRect(26, 40, 12, 20);

        // Antler Motif above Door
        ctx.fillStyle = '#e2e8f0';
        ctx.fillRect(30, 32, 4, 3);
        ctx.fillRect(27, 30, 3, 2);
        ctx.fillRect(34, 30, 3, 2);

        // Archery Target Board with Arrows
        ctx.fillStyle = '#f8fafc';
        ctx.beginPath(); ctx.arc(16, 44, 6, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#dc2626';
        ctx.beginPath(); ctx.arc(16, 44, 4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#facc15';
        ctx.beginPath(); ctx.arc(16, 44, 2, 0, Math.PI * 2); ctx.fill();
        // Arrow stuck in target
        ctx.strokeStyle = '#78350f'; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(16, 44); ctx.lineTo(10, 48); ctx.stroke();

        // Hanging Brass Lantern
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(44, 40, 3, 6);
        ctx.fillStyle = '#fef08a';
        ctx.fillRect(44, 42, 3, 3);

        return canvas;
    }

    // ==========================================
    //  GRAND VILLAGE PROCEDURAL ASSETS
    // ==========================================

    function createVillageFountain() {
        const { canvas, ctx } = makeCanvas(64, 64);
        // Outer stone basin ring
        ctx.fillStyle = '#475569';
        ctx.beginPath(); ctx.ellipse(32, 40, 30, 20, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#64748b';
        ctx.beginPath(); ctx.ellipse(32, 38, 28, 18, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#94a3b8';
        ctx.beginPath(); ctx.ellipse(32, 36, 26, 16, 0, 0, Math.PI * 2); ctx.fill();

        // Crystal blue water pool
        ctx.fillStyle = '#0284c7';
        ctx.beginPath(); ctx.ellipse(32, 38, 24, 14, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#38bdf8';
        ctx.beginPath(); ctx.ellipse(32, 38, 20, 11, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#bae6fd';
        ctx.beginPath(); ctx.ellipse(32, 38, 14, 7, 0, 0, Math.PI * 2); ctx.fill();

        // Water ripples
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.ellipse(32, 38, 8, 4, 0, 0, Math.PI * 2); ctx.stroke();
        ctx.beginPath(); ctx.ellipse(32, 38, 16, 8, 0, 0, Math.PI * 2); ctx.stroke();

        // Center Carved Stone Pedestal
        ctx.fillStyle = '#334155'; ctx.fillRect(28, 20, 8, 20);
        ctx.fillStyle = '#64748b'; ctx.fillRect(29, 20, 6, 18);
        ctx.fillStyle = '#94a3b8'; ctx.fillRect(30, 20, 2, 18);

        // Upper Tier Stone Basin
        ctx.fillStyle = '#475569';
        ctx.beginPath(); ctx.ellipse(32, 20, 14, 6, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#64748b';
        ctx.beginPath(); ctx.ellipse(32, 19, 12, 5, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#38bdf8';
        ctx.beginPath(); ctx.ellipse(32, 19, 9, 3, 0, 0, Math.PI * 2); ctx.fill();

        // Center Spout & Water Spray Jets
        ctx.fillStyle = '#f8fafc';
        ctx.fillRect(31, 10, 2, 8);
        // Spray arches
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(32, 10); ctx.quadraticCurveTo(24, 8, 22, 20); ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(32, 10); ctx.quadraticCurveTo(40, 8, 42, 20); ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(32, 10); ctx.quadraticCurveTo(18, 14, 16, 36); ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(32, 10); ctx.quadraticCurveTo(46, 14, 48, 36); ctx.stroke();

        // Droplets & splashes
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(31, 8, 2, 2);
        ctx.fillRect(20, 18, 2, 2); ctx.fillRect(42, 18, 2, 2);
        ctx.fillRect(15, 34, 2, 2); ctx.fillRect(47, 34, 2, 2);

        return canvas;
    }

    function createBarricade() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Sandbags at the bottom
        ctx.fillStyle = '#b45309'; ctx.fillRect(2, 24, 28, 8);
        ctx.fillStyle = '#d97706';
        ctx.fillRect(3, 25, 8, 6); ctx.fillRect(12, 25, 8, 6); ctx.fillRect(21, 25, 8, 6);
        ctx.fillStyle = '#92400e';
        ctx.fillRect(11, 25, 1, 6); ctx.fillRect(20, 25, 1, 6);

        // Fortified cross logs
        ctx.strokeStyle = '#78350f'; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.moveTo(4, 26); ctx.lineTo(16, 6); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(16, 6); ctx.lineTo(28, 26); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(4, 14); ctx.lineTo(28, 14); ctx.stroke();

        // Sharpened wooden spikes
        ctx.fillStyle = '#451a03';
        ctx.beginPath(); ctx.moveTo(6, 20); ctx.lineTo(8, 2); ctx.lineTo(10, 20); ctx.fill();
        ctx.beginPath(); ctx.moveTo(14, 20); ctx.lineTo(16, 0); ctx.lineTo(18, 20); ctx.fill();
        ctx.beginPath(); ctx.moveTo(22, 20); ctx.lineTo(24, 2); ctx.lineTo(26, 20); ctx.fill();

        ctx.fillStyle = '#78350f';
        ctx.beginPath(); ctx.moveTo(7, 19); ctx.lineTo(8, 4); ctx.lineTo(9, 19); ctx.fill();
        ctx.beginPath(); ctx.moveTo(15, 19); ctx.lineTo(16, 2); ctx.lineTo(17, 19); ctx.fill();
        ctx.beginPath(); ctx.moveTo(23, 19); ctx.lineTo(24, 4); ctx.lineTo(25, 19); ctx.fill();

        // Iron bands
        ctx.fillStyle = '#475569';
        ctx.fillRect(4, 13, 24, 3);
        ctx.fillStyle = '#94a3b8';
        ctx.fillRect(7, 14, 2, 1); ctx.fillRect(15, 14, 2, 1); ctx.fillRect(23, 14, 2, 1);
        return canvas;
    }

    function createStreetLamp() {
        const { canvas, ctx } = makeCanvas(16, 32);
        // Stone base
        ctx.fillStyle = '#475569'; ctx.fillRect(5, 29, 6, 3);
        // Black iron post
        ctx.fillStyle = '#0f172a'; ctx.fillRect(7, 8, 2, 22);
        // Lamp head cap & finial
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(4, 4, 8, 3);
        ctx.fillRect(6, 2, 4, 2); ctx.fillRect(7, 1, 2, 2);
        // Glass lantern with warm amber glow
        ctx.fillStyle = '#fef08a'; ctx.fillRect(5, 7, 6, 7);
        ctx.fillStyle = '#facc15'; ctx.fillRect(6, 8, 4, 5);
        ctx.fillStyle = '#ffffff'; ctx.fillRect(7, 9, 2, 3);
        // Outer iron cage
        ctx.strokeStyle = '#0f172a'; ctx.lineWidth = 1;
        ctx.strokeRect(4.5, 6.5, 7, 8);
        return canvas;
    }

    function createManor() {
        const { canvas, ctx } = makeCanvas(96, 80);
        // Grand Stone Base & Quoins
        ctx.fillStyle = '#64748b'; ctx.fillRect(6, 74, 84, 6);
        ctx.fillStyle = '#cbd5e1'; ctx.fillRect(8, 28, 80, 48); // Stone brick walls

        // Brick texture lines
        ctx.fillStyle = '#94a3b8';
        for (let y = 32; y < 74; y += 6) {
            ctx.fillRect(8, y, 80, 1);
        }
        ctx.fillStyle = '#475569';
        for (let y = 28; y < 74; y += 12) {
            ctx.fillRect(8, y, 4, 6); ctx.fillRect(84, y, 4, 6); // Corner quoins
        }

        // Royal Navy Blue Slate Mansard Roof
        ctx.fillStyle = '#0f172a';
        ctx.beginPath();
        ctx.moveTo(2, 30); ctx.lineTo(20, 6); ctx.lineTo(76, 6); ctx.lineTo(94, 30); ctx.fill();
        ctx.fillStyle = '#1e3a8a';
        ctx.beginPath();
        ctx.moveTo(5, 28); ctx.lineTo(22, 8); ctx.lineTo(74, 8); ctx.lineTo(91, 28); ctx.fill();
        ctx.fillStyle = '#2563eb';
        ctx.fillRect(22, 7, 52, 2);

        // Center Clock Pediment Tower
        ctx.fillStyle = '#1e293b'; ctx.fillRect(38, 0, 20, 16);
        ctx.fillStyle = '#1e3a8a'; ctx.fillRect(40, 1, 16, 14);
        // Golden Clock Face
        ctx.fillStyle = '#facc15';
        ctx.beginPath(); ctx.arc(48, 8, 5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#ffffff';
        ctx.beginPath(); ctx.arc(48, 8, 4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(47, 5, 2, 3); ctx.fillRect(48, 7, 2, 2); // Hands

        // Grand Double Mahogany Doors with Arch
        ctx.fillStyle = '#311005'; ctx.fillRect(40, 48, 16, 26);
        ctx.fillStyle = '#78350f';
        ctx.fillRect(41, 50, 6, 24); ctx.fillRect(49, 50, 6, 24);
        ctx.fillStyle = '#facc15';
        ctx.fillRect(45, 60, 2, 2); ctx.fillRect(49, 60, 2, 2); // Gold Knockers

        // Tall Arched Windows with Golden Sills
        function drawManorWindow(wx, wy) {
            ctx.fillStyle = '#1e293b'; ctx.fillRect(wx - 1, wy - 1, 12, 18);
            ctx.fillStyle = '#38bdf8'; ctx.fillRect(wx, wy, 10, 16);
            ctx.fillStyle = '#bae6fd'; ctx.fillRect(wx + 1, wy + 1, 4, 14);
            ctx.fillStyle = '#facc15'; ctx.fillRect(wx - 2, wy + 16, 14, 2); // Sill
        }
        drawManorWindow(16, 36); drawManorWindow(16, 56);
        drawManorWindow(68, 36); drawManorWindow(68, 56);

        // Village Banner on Balcony
        ctx.fillStyle = '#dc2626'; ctx.fillRect(42, 34, 12, 10);
        ctx.fillStyle = '#facc15';
        ctx.fillRect(42, 34, 12, 2); ctx.fillRect(47, 36, 2, 6); ctx.fillRect(45, 38, 6, 2); // Crest
        return canvas;
    }

    function createApothecary() {
        const { canvas, ctx } = makeCanvas(96, 80);
        // Natural Stone Foundation
        ctx.fillStyle = '#475569'; ctx.fillRect(8, 74, 80, 6);
        // Cream Stucco Walls
        ctx.fillStyle = '#fef3c7'; ctx.fillRect(8, 30, 80, 46);

        // Tudor Timber framing
        ctx.fillStyle = '#78350f';
        ctx.fillRect(8, 30, 4, 46); ctx.fillRect(84, 30, 4, 46);
        ctx.fillRect(8, 30, 80, 3); ctx.fillRect(8, 72, 80, 3);
        ctx.fillRect(48, 30, 3, 46);

        // Emerald Green Herbal Shingle Roof
        ctx.fillStyle = '#064e3b';
        ctx.beginPath();
        ctx.moveTo(2, 32); ctx.lineTo(48, 4); ctx.lineTo(94, 32); ctx.fill();
        ctx.fillStyle = '#15803d';
        ctx.beginPath();
        ctx.moveTo(6, 30); ctx.lineTo(48, 7); ctx.lineTo(90, 30); ctx.fill();
        ctx.fillStyle = '#22c55e';
        ctx.beginPath();
        ctx.moveTo(12, 24); ctx.lineTo(48, 11); ctx.lineTo(84, 24); ctx.fill();

        // Stone Chimney with Lavender Smoke Puffs
        ctx.fillStyle = '#475569'; ctx.fillRect(70, 8, 12, 24);
        ctx.fillStyle = 'rgba(192, 132, 252, 0.7)';
        ctx.beginPath(); ctx.arc(76, 4, 3, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(79, -1, 4, 0, Math.PI * 2); ctx.fill();

        // Front Door with Green Glass
        ctx.fillStyle = '#451a03'; ctx.fillRect(42, 46, 14, 28);
        ctx.fillStyle = '#15803d'; ctx.fillRect(44, 48, 10, 10);
        ctx.fillStyle = '#facc15'; ctx.fillRect(51, 62, 2, 2);

        // Hanging Apothecary Mortar & Pestle / Green Cross Sign
        ctx.fillStyle = '#1e293b'; ctx.fillRect(36, 42, 6, 2);
        ctx.fillStyle = '#ffffff'; ctx.fillRect(34, 44, 10, 10);
        ctx.fillStyle = '#22c55e';
        ctx.fillRect(38, 46, 2, 6); ctx.fillRect(36, 48, 6, 2); // Green cross

        // Herbal Display Window with Potion Bottles
        ctx.fillStyle = '#451a03'; ctx.fillRect(14, 44, 24, 20);
        ctx.fillStyle = '#bae6fd'; ctx.fillRect(16, 46, 20, 16);
        // Colorful bottles on shelf
        ctx.fillStyle = '#06b6d4'; ctx.fillRect(18, 52, 3, 5); // Blue
        ctx.fillStyle = '#ec4899'; ctx.fillRect(23, 52, 3, 5); // Pink
        ctx.fillStyle = '#22c55e'; ctx.fillRect(28, 52, 3, 5); // Green
        ctx.fillStyle = '#eab308'; ctx.fillRect(32, 53, 2, 4); // Yellow

        // Window Herb Planter
        ctx.fillStyle = '#78350f'; ctx.fillRect(66, 62, 16, 4);
        ctx.fillStyle = '#16a34a'; ctx.fillRect(67, 56, 14, 6);
        ctx.fillStyle = '#38bdf8'; ctx.fillRect(68, 54, 3, 3); ctx.fillRect(75, 54, 3, 3); // Starflowers

        return canvas;
    }

    function createTavern() {
        const { canvas, ctx } = makeCanvas(96, 80);
        // Cobblestone Tavern Base
        ctx.fillStyle = '#334155'; ctx.fillRect(6, 72, 84, 8);
        // Rich Amber Timber & Red Brick Wall
        ctx.fillStyle = '#9a3412'; ctx.fillRect(8, 30, 80, 44);

        // Heavy Oak Post Beams
        ctx.fillStyle = '#451a03';
        ctx.fillRect(8, 30, 5, 44); ctx.fillRect(83, 30, 5, 44);
        ctx.fillRect(8, 30, 80, 3); ctx.fillRect(8, 70, 80, 3);
        ctx.fillRect(54, 30, 4, 44);

        // Terracotta Tile Roof with Warm Highlights
        ctx.fillStyle = '#451a03';
        ctx.beginPath();
        ctx.moveTo(2, 32); ctx.lineTo(48, 6); ctx.lineTo(94, 32); ctx.fill();
        ctx.fillStyle = '#c2410c';
        ctx.beginPath();
        ctx.moveTo(6, 30); ctx.lineTo(48, 9); ctx.lineTo(90, 30); ctx.fill();
        ctx.fillStyle = '#ea580c';
        ctx.beginPath();
        ctx.moveTo(12, 24); ctx.lineTo(48, 13); ctx.lineTo(84, 24); ctx.fill();

        // Cozy Glowing Amber Tavern Windows
        function drawTavernWindow(wx, wy) {
            ctx.fillStyle = '#451a03'; ctx.fillRect(wx - 1, wy - 1, 18, 16);
            ctx.fillStyle = '#fef08a'; ctx.fillRect(wx, wy, 16, 14);
            ctx.fillStyle = '#f59e0b'; ctx.fillRect(wx + 1, wy + 1, 14, 12);
            ctx.fillStyle = '#451a03';
            ctx.fillRect(wx + 7, wy, 2, 14); ctx.fillRect(wx, wy + 6, 16, 2);
        }
        drawTavernWindow(16, 44);
        drawTavernWindow(64, 44);

        // Tavern Solid Oak Door
        ctx.fillStyle = '#311005'; ctx.fillRect(38, 44, 14, 28);
        ctx.fillStyle = '#78350f'; ctx.fillRect(40, 46, 10, 24);
        ctx.fillStyle = '#facc15'; ctx.fillRect(48, 58, 2, 3);

        // Swinging Tavern Signboard with Golden Ale Mug
        ctx.fillStyle = '#1e293b'; ctx.fillRect(32, 36, 6, 2);
        ctx.fillStyle = '#78350f'; ctx.fillRect(30, 38, 10, 10);
        ctx.fillStyle = '#facc15'; ctx.fillRect(32, 41, 4, 5); // Golden Beer
        ctx.fillStyle = '#ffffff'; ctx.fillRect(32, 40, 5, 2); // Foam
        ctx.fillStyle = '#facc15'; ctx.fillRect(36, 42, 2, 3); // Handle

        // Outside Ale Barrels
        ctx.fillStyle = '#78350f'; ctx.fillRect(80, 60, 10, 12);
        ctx.fillStyle = '#1e293b'; ctx.fillRect(80, 62, 10, 1); ctx.fillRect(80, 69, 10, 1);
        return canvas;
    }

    function createVillageForge() {
        const { canvas, ctx } = makeCanvas(96, 80);
        // Basalt Stone Walls
        ctx.fillStyle = '#1e293b'; ctx.fillRect(8, 28, 80, 48);
        ctx.fillStyle = '#334155'; ctx.fillRect(10, 30, 76, 44);

        // Stone Brick texture
        ctx.fillStyle = '#0f172a';
        for (let y = 34; y < 74; y += 6) ctx.fillRect(10, y, 76, 1);

        // Industrial Dark Metal Roof
        ctx.fillStyle = '#0f172a';
        ctx.beginPath();
        ctx.moveTo(4, 30); ctx.lineTo(48, 8); ctx.lineTo(92, 30); ctx.fill();
        ctx.fillStyle = '#475569';
        ctx.beginPath();
        ctx.moveTo(8, 28); ctx.lineTo(48, 11); ctx.lineTo(88, 28); ctx.fill();

        // Massive Stone Forge Chimney with Smoke & Sparks
        ctx.fillStyle = '#1e293b'; ctx.fillRect(68, 2, 16, 28);
        ctx.fillStyle = '#475569'; ctx.fillRect(66, 0, 20, 4);
        // Smoke & Sparks
        ctx.fillStyle = 'rgba(71, 85, 105, 0.8)';
        ctx.beginPath(); ctx.arc(76, -4, 4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#f97316'; ctx.fillRect(75, 4, 2, 2); ctx.fillRect(79, 1, 2, 2); // Sparks

        // Blazing Open Furnace Arch
        ctx.fillStyle = '#1e293b';
        ctx.beginPath(); ctx.ellipse(30, 56, 12, 14, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#ea580c';
        ctx.beginPath(); ctx.ellipse(30, 56, 10, 12, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#facc15';
        ctx.beginPath(); ctx.ellipse(30, 57, 6, 8, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#ffffff';
        ctx.beginPath(); ctx.arc(30, 58, 3, 0, Math.PI * 2); ctx.fill();

        // Heavy Blacksmith Anvil on Wood Log
        ctx.fillStyle = '#78350f'; ctx.fillRect(60, 58, 10, 12); // Log
        ctx.fillStyle = '#0f172a'; ctx.fillRect(56, 52, 18, 7); // Anvil body
        ctx.fillStyle = '#64748b'; ctx.fillRect(58, 52, 14, 2); // Anvil top plate
        // Red-hot steel on anvil
        ctx.fillStyle = '#ef4444'; ctx.fillRect(62, 51, 6, 2);

        // Forge Door
        ctx.fillStyle = '#1e293b'; ctx.fillRect(44, 46, 10, 26);
        ctx.fillStyle = '#475569'; ctx.fillRect(45, 48, 8, 22);

        // Hanging Crossed Hammer Sign
        ctx.fillStyle = '#0f172a'; ctx.fillRect(44, 38, 10, 2);
        ctx.fillStyle = '#f59e0b'; ctx.fillRect(47, 36, 4, 4);
        return canvas;
    }


    // ==========================================
    // INTERIOR TILES & FURNITURE
    // ==========================================

    function createFloorWood() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#b77942';
        ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#9b5b29';
        ctx.fillRect(0, 7, 32, 1);
        ctx.fillRect(0, 15, 32, 1);
        ctx.fillRect(0, 23, 32, 1);
        ctx.fillRect(0, 31, 32, 1);
        ctx.fillRect(16, 0, 1, 8);
        ctx.fillRect(8, 8, 1, 8);
        ctx.fillRect(24, 16, 1, 8);
        ctx.fillRect(12, 24, 1, 8);
        return canvas;
    }

    function createWallHouse() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#f5ebd7';
        ctx.fillRect(0, 0, 32, 24);
        ctx.fillStyle = '#eadeca';
        ctx.fillRect(8, 0, 2, 24);
        ctx.fillRect(20, 0, 2, 24);
        ctx.fillStyle = '#7a421d';
        ctx.fillRect(0, 0, 32, 3);
        ctx.fillRect(0, 24, 32, 8);
        ctx.fillStyle = '#925124';
        ctx.fillRect(0, 25, 32, 2);
        return canvas;
    }

    function createFloorShop() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#eeddc3';
        ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#b58252';
        ctx.fillRect(0, 0, 16, 16);
        ctx.fillRect(16, 16, 16, 16);
        ctx.fillStyle = '#7a4e27';
        ctx.fillRect(0, 15, 32, 1);
        ctx.fillRect(15, 0, 1, 32);
        return canvas;
    }

    function createWallShop() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#47698a';
        ctx.fillRect(0, 0, 32, 24);
        ctx.fillStyle = '#33506d';
        ctx.fillRect(0, 0, 32, 3);
        ctx.fillRect(0, 24, 32, 8);
        ctx.fillStyle = '#78350f';
        ctx.fillRect(4, 12, 24, 2);
        return canvas;
    }

    function createDoorMat() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#8f572b';
        ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#991b1b';
        ctx.fillRect(3, 6, 26, 20);
        ctx.fillStyle = '#dc2626';
        ctx.fillRect(5, 8, 22, 16);
        ctx.fillStyle = '#fef08a';
        ctx.fillRect(8, 14, 16, 4);
        return canvas;
    }

    function createBed(isDeluxe = false) {
        const { canvas, ctx } = makeCanvas(48, 48);
        if (!isDeluxe) {
            ctx.fillStyle = '#6d401a';
            ctx.fillRect(4, 4, 40, 40);
            ctx.fillStyle = '#f8fafc';
            ctx.fillRect(8, 8, 32, 12);
            ctx.fillStyle = '#cbd5e1';
            ctx.fillRect(8, 18, 32, 24);
            ctx.fillStyle = '#2563eb';
            ctx.fillRect(8, 20, 32, 22);
            ctx.fillStyle = '#60a5fa';
            ctx.fillRect(8, 20, 32, 4);
        } else {
            ctx.fillStyle = '#451a03';
            ctx.fillRect(2, 2, 44, 44);
            ctx.fillStyle = '#d97706';
            ctx.fillRect(2, 2, 4, 6);
            ctx.fillRect(42, 2, 4, 6);
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(6, 6, 16, 12);
            ctx.fillRect(26, 6, 16, 12);
            ctx.fillStyle = '#991b1b';
            ctx.fillRect(6, 16, 36, 28);
            ctx.fillStyle = '#dc2626';
            ctx.fillRect(8, 18, 32, 24);
            ctx.fillStyle = '#facc15';
            ctx.fillRect(6, 28, 36, 3);
        }
        return canvas;
    }

    function createWardrobe() {
        const { canvas, ctx } = makeCanvas(32, 48);
        ctx.fillStyle = '#5c3517';
        ctx.fillRect(2, 4, 28, 42);
        ctx.fillStyle = '#7a471f';
        ctx.fillRect(4, 6, 24, 38);
        ctx.fillStyle = '#451a03';
        ctx.fillRect(0, 2, 32, 4);
        ctx.fillStyle = '#38bdf8';
        ctx.fillRect(7, 10, 18, 28);
        ctx.fillStyle = '#e0f2fe';
        ctx.fillRect(9, 12, 14, 24);
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.moveTo(9, 14); ctx.lineTo(15, 12); ctx.lineTo(11, 26); ctx.lineTo(9, 26);
        ctx.fill();
        ctx.fillStyle = '#f59e0b';
        ctx.fillRect(22, 24, 2, 4);
        return canvas;
    }

    function createFireplace() {
        const { canvas, ctx } = makeCanvas(48, 48);
        ctx.fillStyle = '#475569';
        ctx.fillRect(4, 4, 40, 40);
        ctx.fillStyle = '#64748b';
        ctx.fillRect(6, 6, 36, 36);
        ctx.fillStyle = '#5c3517';
        ctx.fillRect(2, 4, 44, 5);
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(10, 18, 28, 24);
        ctx.fillStyle = '#451a03';
        ctx.fillRect(14, 36, 20, 5);
        ctx.fillStyle = '#ea580c';
        ctx.beginPath();
        ctx.arc(24, 34, 8, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#facc15';
        ctx.beginPath();
        ctx.arc(24, 33, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(23, 31, 2, 3);
        return canvas;
    }

    function createFridge() {
        const { canvas, ctx } = makeCanvas(32, 48);
        ctx.fillStyle = '#2dd4bf';
        ctx.fillRect(3, 4, 26, 42);
        ctx.fillStyle = '#5eead4';
        ctx.fillRect(5, 6, 22, 38);
        ctx.fillStyle = '#14b8a6';
        ctx.fillRect(3, 18, 26, 2);
        ctx.fillStyle = '#cbd5e1';
        ctx.fillRect(6, 10, 2, 5);
        ctx.fillRect(6, 22, 2, 8);
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(6, 11, 1, 3);
        ctx.fillRect(6, 23, 1, 6);
        return canvas;
    }

    function createTeaTable() {
        const { canvas, ctx } = makeCanvas(48, 48);
        ctx.fillStyle = '#5c3517';
        ctx.fillRect(4, 18, 6, 12);
        ctx.fillRect(38, 18, 6, 12);
        ctx.fillStyle = '#8f572b';
        ctx.beginPath();
        ctx.arc(24, 24, 16, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#a66a38';
        ctx.beginPath();
        ctx.arc(24, 24, 14, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#f8fafc';
        ctx.beginPath();
        ctx.arc(24, 24, 9, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#0284c7';
        ctx.fillRect(22, 20, 5, 5);
        ctx.fillStyle = '#38bdf8';
        ctx.fillRect(21, 24, 2, 2);
        return canvas;
    }

    function createPersianRug() {
        const { canvas, ctx } = makeCanvas(64, 48);
        ctx.fillStyle = '#7f1d1d';
        ctx.fillRect(4, 4, 56, 40);
        ctx.strokeStyle = '#facc15';
        ctx.lineWidth = 2;
        ctx.strokeRect(7, 7, 50, 34);
        ctx.fillStyle = '#991b1b';
        ctx.fillRect(10, 10, 44, 28);
        ctx.fillStyle = '#fbbf24';
        ctx.beginPath();
        ctx.ellipse(32, 24, 12, 8, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#0284c7';
        ctx.beginPath();
        ctx.arc(32, 24, 4, 0, Math.PI * 2);
        ctx.fill();
        return canvas;
    }

    function createShopCounter() {
        const { canvas, ctx } = makeCanvas(64, 32);
        ctx.fillStyle = '#5c3517';
        ctx.fillRect(2, 6, 60, 24);
        ctx.fillStyle = '#8a5225';
        ctx.fillRect(4, 8, 56, 20);
        ctx.fillStyle = '#451a03';
        ctx.fillRect(0, 4, 64, 4);
        ctx.fillStyle = '#a66a38';
        ctx.fillRect(2, 5, 60, 2);
        ctx.fillStyle = '#b45309';
        ctx.fillRect(10, 0, 14, 8);
        ctx.fillStyle = '#f59e0b';
        ctx.fillRect(12, 2, 10, 5);
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(13, 3, 8, 2);
        return canvas;
    }

    function createDisplayShelf() {
        const { canvas, ctx } = makeCanvas(48, 36);
        ctx.fillStyle = '#5c3517';
        ctx.fillRect(2, 10, 44, 24);
        ctx.fillStyle = '#7a421d';
        ctx.fillRect(4, 12, 40, 20);
        ctx.fillStyle = '#451a03';
        ctx.fillRect(2, 8, 44, 3);
        ctx.fillRect(2, 20, 44, 3);
        ctx.fillStyle = '#fef3c7';
        ctx.fillRect(18, 28, 12, 5);
        ctx.fillStyle = '#78350f';
        ctx.fillRect(20, 30, 8, 1);
        return canvas;
    }

    function createFloorCarpet() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#831843';
        ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#9d174d';
        ctx.fillRect(2, 2, 28, 28);
        ctx.strokeStyle = '#facc15';
        ctx.lineWidth = 1;
        ctx.strokeRect(4, 4, 24, 24);
        ctx.fillStyle = '#f59e0b';
        ctx.fillRect(15, 15, 2, 2);
        return canvas;
    }

    function createWallManor() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#475569';
        ctx.fillRect(0, 0, 32, 24);
        ctx.fillStyle = '#334155';
        ctx.fillRect(0, 0, 32, 3);
        ctx.fillRect(0, 24, 32, 8);
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(0, 11, 32, 1);
        ctx.fillRect(16, 0, 1, 11);
        ctx.fillRect(8, 12, 1, 12);
        ctx.fillRect(24, 12, 1, 12);
        // Royal banner
        ctx.fillStyle = '#1d4ed8';
        ctx.fillRect(8, 5, 16, 14);
        ctx.fillStyle = '#facc15';
        ctx.fillRect(14, 7, 4, 4);
        ctx.beginPath();
        ctx.moveTo(8, 19); ctx.lineTo(16, 15); ctx.lineTo(24, 19); ctx.fill();
        return canvas;
    }

    function createWallForge() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(0, 0, 32, 24);
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 0, 32, 3);
        ctx.fillRect(0, 24, 32, 8);
        ctx.fillStyle = '#090d16';
        ctx.fillRect(0, 11, 32, 1);
        ctx.fillRect(16, 0, 1, 11);
        ctx.fillRect(8, 12, 1, 12);
        ctx.fillStyle = '#64748b';
        ctx.fillRect(10, 6, 2, 10);
        ctx.fillRect(9, 14, 4, 2);
        ctx.fillStyle = '#ea580c';
        ctx.fillRect(20, 10, 3, 3);
        return canvas;
    }

    function createAlchemyCauldron() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#78350f';
        ctx.fillRect(6, 26, 20, 4);
        ctx.fillStyle = '#ea580c';
        ctx.fillRect(10, 24, 12, 3);
        ctx.fillStyle = '#facc15';
        ctx.fillRect(13, 23, 6, 2);

        ctx.fillStyle = '#1e293b';
        ctx.fillRect(5, 20, 3, 8);
        ctx.fillRect(24, 20, 3, 8);

        ctx.fillStyle = '#334155';
        ctx.beginPath();
        ctx.arc(16, 16, 12, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#1e293b';
        ctx.beginPath();
        ctx.arc(16, 16, 10, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = '#10b981';
        ctx.beginPath();
        ctx.ellipse(16, 13, 9, 5, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#6ee7b7';
        ctx.beginPath();
        ctx.arc(14, 12, 2.5, 0, Math.PI * 2);
        ctx.arc(19, 14, 2, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = 'rgba(110, 231, 183, 0.6)';
        ctx.beginPath();
        ctx.arc(16, 5, 3, 0, Math.PI * 2);
        ctx.arc(18, 1, 2, 0, Math.PI * 2);
        ctx.fill();
        return canvas;
    }

    function createAnvilSprite() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#451a03';
        ctx.fillRect(6, 18, 20, 14);
        ctx.fillStyle = '#78350f';
        ctx.fillRect(8, 20, 16, 12);
        ctx.fillStyle = '#292524';
        ctx.fillRect(5, 23, 22, 2);

        ctx.fillStyle = '#475569';
        ctx.fillRect(8, 12, 16, 6);
        ctx.fillStyle = '#64748b';
        ctx.fillRect(4, 8, 24, 4);
        ctx.beginPath();
        ctx.moveTo(4, 8); ctx.lineTo(0, 10); ctx.lineTo(4, 12); ctx.fill();
        ctx.fillStyle = '#334155';
        ctx.fillRect(24, 10, 5, 2);

        ctx.fillStyle = '#ea580c';
        ctx.fillRect(12, 7, 6, 2);
        ctx.fillStyle = '#facc15';
        ctx.fillRect(13, 7, 4, 1);
        return canvas;
    }

    function createTavernTable() {
        const { canvas, ctx } = makeCanvas(48, 36);
        ctx.fillStyle = '#451a03';
        ctx.fillRect(6, 18, 4, 16);
        ctx.fillRect(38, 18, 4, 16);
        ctx.fillRect(8, 28, 32, 3);

        ctx.fillStyle = '#78350f';
        ctx.fillRect(2, 6, 44, 14);
        ctx.fillStyle = '#9a3412';
        ctx.fillRect(4, 8, 40, 10);

        ctx.fillStyle = '#991b1b';
        ctx.fillRect(16, 6, 16, 14);
        ctx.fillStyle = '#facc15';
        ctx.fillRect(16, 6, 16, 1);
        ctx.fillRect(16, 19, 16, 1);

        ctx.fillStyle = '#d97706';
        ctx.fillRect(8, 2, 6, 6);
        ctx.fillRect(34, 2, 6, 6);
        ctx.fillStyle = '#fef08a';
        ctx.fillRect(7, 0, 8, 3);
        ctx.fillRect(33, 0, 8, 3);

        ctx.fillStyle = '#e2e8f0';
        ctx.beginPath();
        ctx.ellipse(24, 12, 6, 3, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#b45309';
        ctx.fillRect(21, 10, 6, 3);
        return canvas;
    }

    function createHerbShelf() {
        const { canvas, ctx } = makeCanvas(32, 40);
        ctx.fillStyle = '#451a03';
        ctx.fillRect(2, 4, 28, 36);
        ctx.fillStyle = '#5c2c16';
        ctx.fillRect(4, 6, 24, 32);

        ctx.fillStyle = '#78350f';
        ctx.fillRect(2, 6, 28, 3);
        ctx.fillRect(2, 18, 28, 3);
        ctx.fillRect(2, 30, 28, 3);

        ctx.fillStyle = '#15803d';
        ctx.fillRect(6, 9, 3, 7);
        ctx.fillStyle = '#84cc16';
        ctx.fillRect(14, 9, 4, 8);
        ctx.fillStyle = '#a855f7';
        ctx.fillRect(22, 9, 3, 7);

        ctx.fillStyle = '#ef4444';
        ctx.fillRect(6, 21, 5, 8);
        ctx.fillStyle = '#3b82f6';
        ctx.fillRect(14, 21, 5, 8);
        ctx.fillStyle = '#10b981';
        ctx.fillRect(22, 21, 5, 8);
        ctx.fillStyle = '#b45309';
        ctx.fillRect(7, 19, 3, 2);
        ctx.fillRect(15, 19, 3, 2);
        ctx.fillRect(23, 19, 3, 2);

        ctx.fillStyle = '#94a3b8';
        ctx.beginPath();
        ctx.arc(10, 34, 4, 0, Math.PI);
        ctx.fill();
        ctx.fillStyle = '#cbd5e1';
        ctx.fillRect(18, 32, 8, 7);
        return canvas;
    }

    function createFlowerBed() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#451a03';
        ctx.beginPath(); ctx.ellipse(16, 18, 14, 10, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#78350f';
        ctx.beginPath(); ctx.ellipse(16, 17, 12, 8, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#15803d';
        ctx.fillRect(8, 14, 4, 4); ctx.fillRect(18, 12, 5, 4); ctx.fillRect(12, 19, 6, 4);
        ctx.fillStyle = '#16a34a';
        ctx.fillRect(6, 12, 3, 3); ctx.fillRect(22, 15, 3, 3);
        ctx.fillStyle = '#ef4444'; ctx.fillRect(7, 10, 5, 5);
        ctx.fillStyle = '#fca5a5'; ctx.fillRect(8, 11, 2, 2);
        ctx.fillStyle = '#ffffff'; ctx.fillRect(19, 10, 6, 6);
        ctx.fillStyle = '#facc15'; ctx.fillRect(21, 12, 2, 2);
        ctx.fillStyle = '#38bdf8'; ctx.fillRect(13, 16, 5, 5);
        ctx.fillStyle = '#e0f2fe'; ctx.fillRect(14, 17, 2, 2);
        return canvas;
    }

    function createBerryBush() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#14532d';
        ctx.beginPath(); ctx.arc(16, 18, 13, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#16a34a';
        ctx.beginPath(); ctx.arc(12, 16, 9, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(20, 16, 9, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(16, 13, 9, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#22c55e';
        ctx.beginPath(); ctx.arc(15, 12, 6, 0, Math.PI * 2); ctx.fill();
        const berryCoords = [{x: 10, y: 15}, {x: 16, y: 11}, {x: 21, y: 14}, {x: 13, y: 20}, {x: 19, y: 19}];
        berryCoords.forEach(b => {
            ctx.fillStyle = '#dc2626'; ctx.beginPath(); ctx.arc(b.x, b.y, 2.5, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#fca5a5'; ctx.fillRect(b.x - 1, b.y - 1, 1, 1);
        });
        return canvas;
    }

    function createHayBale() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#b45309';
        ctx.fillRect(4, 10, 24, 18);
        ctx.fillStyle = '#d97706';
        ctx.fillRect(5, 11, 22, 16);
        ctx.fillStyle = '#f59e0b';
        ctx.fillRect(6, 12, 20, 14);
        ctx.fillStyle = '#fef08a';
        for (let y = 13; y <= 24; y += 3) {
            ctx.fillRect(8, y, 16, 1);
        }
        ctx.fillStyle = '#78350f';
        ctx.fillRect(10, 10, 2, 18);
        ctx.fillRect(20, 10, 2, 18);
        return canvas;
    }

    function createWoodPile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        function drawLog(lx: number, ly: number) {
            ctx.fillStyle = '#451a03'; ctx.fillRect(lx, ly, 10, 8);
            ctx.fillStyle = '#78350f'; ctx.fillRect(lx + 1, ly + 1, 8, 6);
            ctx.fillStyle = '#fed7aa'; ctx.beginPath(); ctx.arc(lx + 2, ly + 4, 3, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#9a3412'; ctx.beginPath(); ctx.arc(lx + 2, ly + 4, 1.5, 0, Math.PI * 2); ctx.fill();
        }
        drawLog(3, 19); drawLog(11, 19); drawLog(19, 19);
        drawLog(7, 13); drawLog(15, 13);
        return canvas;
    }

    function createFishingDock() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#451a03'; ctx.fillRect(2, 6, 28, 24);
        ctx.fillStyle = '#78350f'; ctx.fillRect(4, 6, 24, 22);
        ctx.fillStyle = '#9a3412';
        for (let y = 8; y < 28; y += 4) {
            ctx.fillRect(4, y, 24, 3);
            ctx.fillStyle = '#451a03'; ctx.fillRect(4, y + 3, 24, 1);
            ctx.fillStyle = '#9a3412';
        }
        ctx.fillStyle = '#311005';
        ctx.fillRect(4, 26, 4, 6);
        ctx.fillRect(24, 26, 4, 6);
        ctx.fillStyle = '#fef08a';
        ctx.beginPath(); ctx.arc(22, 12, 3, 0, Math.PI * 2); ctx.stroke();
        return canvas;
    }

    function createFruitTree(fruitType = 'apple') {
        const { canvas, ctx } = makeCanvas(48, 64);
        ctx.fillStyle = '#451a03'; ctx.fillRect(20, 36, 8, 22);
        ctx.fillStyle = '#78350f'; ctx.fillRect(22, 36, 4, 22);
        ctx.beginPath();
        ctx.moveTo(18, 58); ctx.lineTo(24, 54); ctx.lineTo(30, 58); ctx.stroke();
        ctx.fillStyle = '#14532d';
        ctx.beginPath(); ctx.arc(24, 24, 22, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#16a34a';
        ctx.beginPath(); ctx.arc(18, 20, 16, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(30, 20, 16, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(24, 15, 14, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#22c55e';
        ctx.beginPath(); ctx.arc(22, 15, 9, 0, Math.PI * 2); ctx.fill();
        const fruitColor = fruitType === 'apple' ? '#ef4444' : '#f97316';
        const fruitHighlight = fruitType === 'apple' ? '#fca5a5' : '#fed7aa';
        const fruitPositions = [
            { x: 14, y: 18 }, { x: 26, y: 12 }, { x: 33, y: 22 },
            { x: 20, y: 28 }, { x: 28, y: 30 }, { x: 13, y: 28 }
        ];
        fruitPositions.forEach(p => {
            ctx.fillStyle = fruitColor;
            ctx.beginPath(); ctx.arc(p.x, p.y, 3, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = fruitHighlight;
            ctx.fillRect(p.x - 1, p.y - 1, 1, 1);
        });
        return canvas;
    }

    function createNPCFrames(type = 'uncle') {
        const palMap: Record<string, { hair: string; shirt: string; pants: string; skin: string; hat?: string }> = {
            uncle: { hair: '#94a3b8', shirt: '#15803d', pants: '#78350f', skin: '#ffccaa' },
            auntie: { hair: '#475569', shirt: '#ec4899', pants: '#831843', skin: '#ffccaa' },
            girl: { hair: '#d97706', shirt: '#eab308', pants: '#3b82f6', skin: '#ffccaa' },
            chef: { hair: '#1e293b', shirt: '#f8fafc', pants: '#1e293b', skin: '#ffccaa', hat: 'chef' },
            boy: { hair: '#451a03', shirt: '#0284c7', pants: '#334155', skin: '#ffccaa' },
            grandpa: { hair: '#e2e8f0', shirt: '#713f12', pants: '#3f2e14', skin: '#fbd5b5' },
            merchant: { hair: '#7c2d12', shirt: '#7c3aed', pants: '#4c1d95', skin: '#ffccaa' },
            maid: { hair: '#b45309', shirt: '#059669', pants: '#064e3b', skin: '#ffccaa' }
        };
        const p = palMap[type] || palMap.uncle;

        const directions = ['down', 'up', 'left', 'right'];
        const npcFrames = {};

        directions.forEach(dir => {
            npcFrames[dir] = [];
            [0, 1].forEach(f => {
                const { canvas, ctx } = makeCanvas(24, 32);
                const leg = (f === 1) ? 2 : 0;

                ctx.fillStyle = p.hair;
                ctx.fillRect(6, 4, 12, 7);

                if (p.hat === 'chef') {
                    ctx.fillStyle = '#ffffff';
                    ctx.fillRect(5, -2, 14, 7);
                }

                ctx.fillStyle = p.skin;
                ctx.fillRect(7, 8, 10, 7);
                ctx.fillStyle = '#0f172a';
                if (dir === 'down') {
                    ctx.fillRect(9, 10, 2, 2);
                    ctx.fillRect(13, 10, 2, 2);
                } else if (dir === 'left') {
                    ctx.fillRect(7, 10, 2, 2);
                } else if (dir === 'right') {
                    ctx.fillRect(15, 10, 2, 2);
                }

                ctx.fillStyle = p.shirt;
                ctx.fillRect(6, 15, 12, 8);

                ctx.fillStyle = p.pants;
                ctx.fillRect(7, 23, 4, 5 + leg);
                ctx.fillRect(13, 23, 4, 5 - leg);

                npcFrames[dir].push(canvas);
            });
        });
        return npcFrames;
    }

    // ==========================================
    // DEMON BUGS & PEST SPRITES
    // ==========================================
    function createDemonBugFrames(type = 'shadow_beetle') {
        const frames = [];
        [0, 1].forEach(f => {
            if (type === 'shadow_beetle') {
                const { canvas, ctx } = makeCanvas(32, 24);
                const legSwing = (f === 1) ? 2 : 0;

                // Beetle Body / Shell
                ctx.fillStyle = '#2e1065';
                ctx.beginPath();
                ctx.ellipse(16, 12, 10, 8, 0, 0, Math.PI * 2);
                ctx.fill();

                // Shiny Chitin Ridge
                ctx.fillStyle = '#6b21a8';
                ctx.fillRect(8, 9, 14, 5);
                ctx.fillStyle = '#c084fc';
                ctx.fillRect(10, 10, 3, 2);

                // Spiky Mandibles
                ctx.fillStyle = '#7e22ce';
                ctx.fillRect(4, 8, 4, 3);
                ctx.fillRect(4, 13, 4, 3);

                // Evil Glowing Red Eyes
                ctx.fillStyle = '#ef4444';
                ctx.fillRect(6, 9, 2, 2);
                ctx.fillRect(6, 13, 2, 2);
                ctx.fillStyle = '#fca5a5';
                ctx.fillRect(6, 10, 1, 1);

                // 6 Spiny Legs
                ctx.fillStyle = '#1e1b4b';
                ctx.fillRect(11, 2 + legSwing, 2, 5);
                ctx.fillRect(16, 2, 2, 5);
                ctx.fillRect(21, 2 - legSwing, 2, 5);

                ctx.fillRect(11, 17 - legSwing, 2, 5);
                ctx.fillRect(16, 17, 2, 5);
                ctx.fillRect(21, 17 + legSwing, 2, 5);

                frames.push(canvas);
            } else if (type === 'demon_hornet') {
                const { canvas, ctx } = makeCanvas(28, 28);
                const wingBob = (f === 1) ? 3 : 0;

                // Translucent demon wings
                ctx.fillStyle = 'rgba(56, 189, 248, 0.7)';
                ctx.beginPath();
                ctx.ellipse(14, 8 - wingBob, 8, 4, -0.3, 0, Math.PI * 2);
                ctx.ellipse(14, 8 + wingBob, 8, 4, 0.3, 0, Math.PI * 2);
                ctx.fill();

                // Hornet Body
                ctx.fillStyle = '#450a0a';
                ctx.beginPath();
                ctx.ellipse(12, 15, 7, 5, 0, 0, Math.PI * 2);
                ctx.fill();

                // Thorax & Stripes
                ctx.fillStyle = '#dc2626';
                ctx.fillRect(8, 12, 8, 2);
                ctx.fillRect(8, 16, 8, 2);

                // Stinger
                ctx.fillStyle = '#f59e0b';
                ctx.beginPath();
                ctx.moveTo(22, 15);
                ctx.lineTo(26, 15);
                ctx.lineTo(22, 17);
                ctx.fill();

                // Head & Antennae
                ctx.fillStyle = '#18181b';
                ctx.fillRect(4, 12, 5, 6);
                ctx.fillStyle = '#ef4444';
                ctx.fillRect(3, 13, 2, 2);

                frames.push(canvas);
            } else if (type === 'poison_larva') {
                const { canvas, ctx } = makeCanvas(32, 20);
                const squish = (f === 1) ? 1 : 0;

                // Caterpillar segments
                ctx.fillStyle = '#14532d';
                ctx.beginPath();
                ctx.arc(8, 11, 5, 0, Math.PI * 2);
                ctx.arc(14, 11 - squish, 6, 0, Math.PI * 2);
                ctx.arc(20, 11 + squish, 5, 0, Math.PI * 2);
                ctx.arc(26, 11, 4, 0, Math.PI * 2);
                ctx.fill();

                // Toxic venom spots & spikes
                ctx.fillStyle = '#4ade80';
                ctx.fillRect(7, 8, 2, 2);
                ctx.fillRect(13, 7 - squish, 3, 2);
                ctx.fillRect(19, 8 + squish, 2, 2);

                ctx.fillStyle = '#a855f7';
                ctx.fillRect(14, 3, 2, 4);
                ctx.fillRect(20, 4, 2, 3);

                // Glowing yellow eye
                ctx.fillStyle = '#facc15';
                ctx.fillRect(5, 10, 2, 2);

                // Venom drop
                ctx.fillStyle = '#84cc16';
                ctx.fillRect(2, 14 + squish, 2, 3);

                frames.push(canvas);
            }
        });
        return frames;
    }

    // ==========================================
    // HUNTERS (FARM DEFENDERS)
    // ==========================================
    function createHunterFrames(type = 'scout_hunter') {
        const directions = ['down', 'up', 'left', 'right'];
        const frames = {};

        directions.forEach(dir => {
            frames[dir] = [];
            [0, 1].forEach(f => {
                const { canvas, ctx } = makeCanvas(24, 32);
                const leg = (f === 1) ? 2 : 0;

                if (type === 'scout_hunter') {
                    // Feather cap
                    ctx.fillStyle = '#15803d'; ctx.fillRect(6, 2, 12, 6);
                    ctx.fillStyle = '#166534'; ctx.fillRect(4, 6, 16, 2);
                    ctx.fillStyle = '#dc2626'; ctx.fillRect(14, 0, 2, 4);

                    // Face
                    ctx.fillStyle = '#fed7aa'; ctx.fillRect(7, 7, 10, 7);
                    ctx.fillStyle = '#1e293b';
                    if (dir === 'down') { ctx.fillRect(9, 9, 2, 2); ctx.fillRect(13, 9, 2, 2); }
                    else if (dir === 'left') { ctx.fillRect(7, 9, 2, 2); }
                    else if (dir === 'right') { ctx.fillRect(15, 9, 2, 2); }

                    // Green Hunter Tunic
                    ctx.fillStyle = '#16a34a'; ctx.fillRect(6, 14, 12, 8);
                    ctx.fillStyle = '#78350f'; ctx.fillRect(5, 18, 14, 2);

                    // Legs
                    ctx.fillStyle = '#3f6212';
                    ctx.fillRect(7, 22, 4, 6 + leg);
                    ctx.fillRect(13, 22, 4, 6 - leg);
                    ctx.fillStyle = '#78350f';
                    ctx.fillRect(6, 28 + leg, 5, 3);
                    ctx.fillRect(13, 28 - leg, 5, 3);

                    // Slingshot held in hand
                    ctx.strokeStyle = '#78350f'; ctx.lineWidth = 2;
                    if (dir === 'down' || dir === 'right') {
                        ctx.beginPath(); ctx.moveTo(18, 16); ctx.lineTo(18, 12); ctx.stroke();
                        ctx.beginPath(); ctx.moveTo(18, 12); ctx.lineTo(16, 9); ctx.stroke();
                        ctx.beginPath(); ctx.moveTo(18, 12); ctx.lineTo(21, 9); ctx.stroke();
                    } else if (dir === 'left') {
                        ctx.beginPath(); ctx.moveTo(5, 16); ctx.lineTo(5, 12); ctx.stroke();
                        ctx.beginPath(); ctx.moveTo(5, 12); ctx.lineTo(3, 9); ctx.stroke();
                        ctx.beginPath(); ctx.moveTo(5, 12); ctx.lineTo(7, 9); ctx.stroke();
                    }
                } else {
                    // Veteran Marksman
                    ctx.fillStyle = '#78350f'; ctx.fillRect(4, 2, 16, 5);
                    ctx.fillStyle = '#451a03'; ctx.fillRect(2, 6, 20, 2);

                    // Face & Beard
                    ctx.fillStyle = '#fed7aa'; ctx.fillRect(7, 7, 10, 7);
                    ctx.fillStyle = '#94a3b8'; ctx.fillRect(7, 11, 10, 4);
                    ctx.fillStyle = '#1e293b';
                    if (dir === 'down') { ctx.fillRect(9, 8, 2, 2); ctx.fillRect(13, 8, 2, 2); }
                    else if (dir === 'left') { ctx.fillRect(7, 8, 2, 2); }
                    else if (dir === 'right') { ctx.fillRect(15, 8, 2, 2); }

                    // Leather Duster Coat
                    ctx.fillStyle = '#92400e'; ctx.fillRect(5, 13, 14, 11);
                    ctx.fillStyle = '#f59e0b'; ctx.fillRect(8, 15, 2, 7);
                    ctx.fillRect(11, 17, 2, 5);

                    // Boots
                    ctx.fillStyle = '#451a03';
                    ctx.fillRect(6, 24 + leg, 5, 7);
                    ctx.fillRect(13, 24 - leg, 5, 7);

                    // Rifle
                    ctx.fillStyle = '#475569';
                    if (dir === 'right' || dir === 'down') {
                        ctx.fillRect(17, 10, 3, 16);
                        ctx.fillStyle = '#78350f'; ctx.fillRect(17, 20, 4, 6);
                    } else if (dir === 'left') {
                        ctx.fillRect(4, 10, 3, 16);
                        ctx.fillStyle = '#78350f'; ctx.fillRect(3, 20, 4, 6);
                    }
                }

                frames[dir].push(canvas);
            });
        });
        return frames;
    }

    // ==========================================
    // FARM HELPERS & GARDENERS (คนดูแลสวน & คนเก็บเกี่ยว)
    // ==========================================
    function createGardenerFrames(type = 'gardener_joy') {
        const directions = ['down', 'up', 'left', 'right'];
        const frames = {};

        directions.forEach(dir => {
            frames[dir] = [];
            [0, 1].forEach(f => {
                const { canvas, ctx } = makeCanvas(24, 32);
                const leg = (f === 1) ? 2 : 0;
                const bobY = (f === 1) ? 1 : 0;

                if (type === 'gardener_joy') {
                    // ป้าแจ่ม (Auntie Joy - Flower Hat & Apron)
                    ctx.fillStyle = '#fde047'; ctx.fillRect(5, 2 + bobY, 14, 5);
                    ctx.fillStyle = '#f59e0b'; ctx.fillRect(3, 5 + bobY, 18, 2);
                    ctx.fillStyle = '#ec4899'; ctx.fillRect(15, 2 + bobY, 3, 3); // Pink flower

                    // Hair & Face
                    ctx.fillStyle = '#78350f'; ctx.fillRect(6, 6 + bobY, 12, 4);
                    ctx.fillStyle = '#fed7aa'; ctx.fillRect(7, 7 + bobY, 10, 7);
                    ctx.fillStyle = '#f43f5e'; ctx.fillRect(7, 11 + bobY, 2, 2); ctx.fillRect(15, 11 + bobY, 2, 2);
                    ctx.fillStyle = '#1e293b';
                    if (dir === 'down') { ctx.fillRect(9, 9 + bobY, 2, 2); ctx.fillRect(13, 9 + bobY, 2, 2); }
                    else if (dir === 'left') { ctx.fillRect(7, 9 + bobY, 2, 2); }
                    else if (dir === 'right') { ctx.fillRect(15, 9 + bobY, 2, 2); }

                    // Floral Apron & Dress
                    ctx.fillStyle = '#f472b6'; ctx.fillRect(6, 14 + bobY, 12, 9);
                    ctx.fillStyle = '#ffffff'; ctx.fillRect(8, 15 + bobY, 8, 8);
                    ctx.fillStyle = '#38bdf8'; ctx.fillRect(10, 17 + bobY, 4, 3);

                    // Shoes
                    ctx.fillStyle = '#78350f';
                    ctx.fillRect(7, 26 + leg, 4, 4);
                    ctx.fillRect(13, 26 - leg, 4, 4);

                    // Watering Can
                    if (dir === 'down' || dir === 'right') {
                        ctx.fillStyle = '#0284c7'; ctx.fillRect(18, 16 + bobY, 5, 6);
                        ctx.fillStyle = '#38bdf8'; ctx.fillRect(19, 14 + bobY, 3, 2);
                        ctx.fillStyle = '#bae6fd'; ctx.fillRect(23, 15 + bobY, 2, 3);
                    } else if (dir === 'left') {
                        ctx.fillStyle = '#0284c7'; ctx.fillRect(1, 16 + bobY, 5, 6);
                        ctx.fillStyle = '#38bdf8'; ctx.fillRect(2, 14 + bobY, 3, 2);
                    }
                } else {
                    // น้องกล้า (Farmer Boy - Harvester)
                    ctx.fillStyle = '#eab308'; ctx.fillRect(5, 2 + bobY, 14, 5);
                    ctx.fillStyle = '#ca8a04'; ctx.fillRect(3, 5 + bobY, 18, 2);
                    ctx.fillStyle = '#dc2626'; ctx.fillRect(5, 5 + bobY, 14, 1);

                    // Face
                    ctx.fillStyle = '#fed7aa'; ctx.fillRect(7, 7 + bobY, 10, 7);
                    ctx.fillStyle = '#1e293b';
                    if (dir === 'down') { ctx.fillRect(9, 9 + bobY, 2, 2); ctx.fillRect(13, 9 + bobY, 2, 2); }
                    else if (dir === 'left') { ctx.fillRect(7, 9 + bobY, 2, 2); }
                    else if (dir === 'right') { ctx.fillRect(15, 9 + bobY, 2, 2); }

                    // Blue Overalls & Red Plaid
                    ctx.fillStyle = '#dc2626'; ctx.fillRect(6, 14 + bobY, 12, 5);
                    ctx.fillStyle = '#1d4ed8'; ctx.fillRect(7, 17 + bobY, 10, 8);
                    ctx.fillStyle = '#3b82f6'; ctx.fillRect(8, 16 + bobY, 2, 3); ctx.fillRect(14, 16 + bobY, 2, 3);

                    // Boots
                    ctx.fillStyle = '#451a03';
                    ctx.fillRect(7, 26 + leg, 4, 4);
                    ctx.fillRect(13, 26 - leg, 4, 4);

                    // Harvesting Crate with veggies
                    if (dir === 'down' || dir === 'right') {
                        ctx.fillStyle = '#854d0e'; ctx.fillRect(17, 15 + bobY, 6, 6);
                        ctx.fillStyle = '#ea580c'; ctx.fillRect(18, 14 + bobY, 2, 2);
                        ctx.fillStyle = '#22c55e'; ctx.fillRect(20, 14 + bobY, 2, 2);
                    } else if (dir === 'left') {
                        ctx.fillStyle = '#854d0e'; ctx.fillRect(1, 15 + bobY, 6, 6);
                        ctx.fillStyle = '#ea580c'; ctx.fillRect(2, 14 + bobY, 2, 2);
                        ctx.fillStyle = '#22c55e'; ctx.fillRect(4, 14 + bobY, 2, 2);
                    }
                }

                frames[dir].push(canvas);
            });
        });
        return frames;
    }

    // ==========================================
    // PROJECTILES
    // ==========================================
    function createProjectileCanvas(type = 'stone') {
        const { canvas, ctx } = makeCanvas(type === 'meteor_blight' ? 24 : 16, type === 'meteor_blight' ? 24 : 16);
        if (type === 'stone') {
            ctx.fillStyle = '#64748b';
            ctx.beginPath(); ctx.arc(8, 8, 4, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#f1f5f9';
            ctx.fillRect(6, 6, 2, 2);
        } else if (type === 'rifle') {
            ctx.fillStyle = '#f59e0b';
            ctx.fillRect(3, 6, 10, 4);
            ctx.fillStyle = '#ef4444';
            ctx.fillRect(11, 6, 2, 4);
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(5, 7, 6, 2);
        } else if (type === 'arrow') {
            ctx.fillStyle = '#78350f'; ctx.fillRect(2, 7, 10, 2);
            ctx.fillStyle = '#cbd5e1'; ctx.beginPath(); ctx.moveTo(12, 5); ctx.lineTo(16, 8); ctx.lineTo(12, 11); ctx.fill();
            ctx.fillStyle = '#ef4444'; ctx.fillRect(1, 6, 3, 4);
        } else if (type === 'acid') {
            ctx.fillStyle = '#22c55e';
            ctx.beginPath(); ctx.arc(8, 8, 4, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#86efac';
            ctx.fillRect(6, 6, 2, 2);
        } else if (type === 'boss_flame') {
            ctx.fillStyle = '#dc2626';
            ctx.beginPath(); ctx.arc(8, 8, 6, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#ea580c';
            ctx.beginPath(); ctx.arc(7, 8, 4, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#fde047';
            ctx.fillRect(6, 7, 3, 3);
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(7, 8, 1, 1);
        } else if (type === 'spore_spiral') {
            // Glowing Blight Petal
            ctx.fillStyle = '#7c3aed';
            ctx.beginPath(); ctx.arc(8, 8, 6, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#ec4899';
            ctx.beginPath();
            ctx.moveTo(8, 2); ctx.lineTo(11, 8); ctx.lineTo(8, 14); ctx.lineTo(5, 8); ctx.fill();
            ctx.beginPath();
            ctx.moveTo(2, 8); ctx.lineTo(8, 11); ctx.lineTo(14, 8); ctx.lineTo(8, 5); ctx.fill();
            ctx.fillStyle = '#fef08a';
            ctx.fillRect(7, 7, 2, 2);
        } else if (type === 'homing_spore') {
            // Shadow Wisp with Glowing Red Eyes
            ctx.fillStyle = '#3b0764';
            ctx.beginPath(); ctx.arc(8, 8, 6, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#9333ea';
            ctx.beginPath(); ctx.arc(8, 8, 4, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#ef4444';
            ctx.fillRect(5, 6, 2, 2); ctx.fillRect(9, 6, 2, 2);
            ctx.fillStyle = '#fef08a';
            ctx.fillRect(6, 7, 1, 1); ctx.fillRect(10, 7, 1, 1);
        } else if (type === 'meteor_blight') {
            // Blazing Molten Meteor Core (24x24)
            ctx.fillStyle = '#450a0a';
            ctx.beginPath(); ctx.arc(12, 12, 10, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#dc2626';
            ctx.beginPath(); ctx.arc(12, 12, 8, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#f97316';
            ctx.beginPath(); ctx.arc(11, 11, 5, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#fef08a';
            ctx.beginPath(); ctx.arc(10, 10, 3, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(9, 9, 2, 2);
        } else if (type === 'holy_beam') {
            ctx.fillStyle = '#fde047';
            ctx.beginPath(); ctx.ellipse(8, 8, 7, 3, 0, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#ffffff';
            ctx.beginPath(); ctx.ellipse(8, 8, 5, 1.5, 0, 0, Math.PI * 2); ctx.fill();
        } else if (type === 'dragon_fire' || type === 'fire_breath') {
            ctx.fillStyle = '#ea580c';
            ctx.beginPath(); ctx.arc(8, 8, 6, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#fef08a';
            ctx.beginPath(); ctx.arc(7, 8, 3.5, 0, Math.PI * 2); ctx.fill();
        } else if (type === 'crystal_shard') {
            ctx.fillStyle = '#06b6d4';
            ctx.beginPath(); ctx.moveTo(8, 2); ctx.lineTo(13, 8); ctx.lineTo(8, 14); ctx.lineTo(3, 8); ctx.fill();
            ctx.fillStyle = '#cffafe';
            ctx.beginPath(); ctx.moveTo(8, 4); ctx.lineTo(11, 8); ctx.lineTo(8, 12); ctx.lineTo(5, 8); ctx.fill();
        } else if (type === 'poison_glob') {
            ctx.fillStyle = '#16a34a';
            ctx.beginPath(); ctx.arc(8, 8, 6, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#86efac';
            ctx.beginPath(); ctx.arc(7, 6, 3, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#22c55e';
            ctx.fillRect(11, 10, 2, 2); ctx.fillRect(4, 10, 2, 2);
        } else if (type === 'ice_shard') {
            ctx.fillStyle = '#38bdf8';
            ctx.beginPath(); ctx.moveTo(8, 1); ctx.lineTo(12, 8); ctx.lineTo(8, 15); ctx.lineTo(4, 8); ctx.fill();
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(7, 5, 2, 6);
        } else if (type === 'shadow_skull') {
            ctx.fillStyle = '#3b0764';
            ctx.beginPath(); ctx.arc(8, 7, 5, 0, Math.PI * 2); ctx.fill();
            ctx.fillRect(5, 10, 6, 4);
            ctx.fillStyle = '#a855f7';
            ctx.fillRect(6, 6, 2, 2); ctx.fillRect(9, 6, 2, 2); // Glowing Purple Eyes
            ctx.fillStyle = '#c084fc'; ctx.fillRect(7, 12, 1, 2); ctx.fillRect(9, 12, 1, 2); // Teeth
        } else if (type === 'petal_blade') {
            // Radiant emerald & golden nature leaf blade
            ctx.fillStyle = '#15803d';
            ctx.beginPath();
            ctx.moveTo(8, 1); ctx.quadraticCurveTo(15, 8, 8, 15); ctx.quadraticCurveTo(1, 8, 8, 1); ctx.fill();
            ctx.fillStyle = '#4ade80';
            ctx.beginPath();
            ctx.moveTo(8, 3); ctx.quadraticCurveTo(13, 8, 8, 13); ctx.quadraticCurveTo(3, 8, 8, 3); ctx.fill();
            ctx.fillStyle = '#fef08a';
            ctx.fillRect(7, 6, 2, 4);
        } else if (type === 'lightning_arc') {
            // Jagged electric bolt
            ctx.fillStyle = '#0284c7';
            ctx.beginPath();
            ctx.moveTo(8, 0); ctx.lineTo(13, 5); ctx.lineTo(9, 8); ctx.lineTo(14, 15); ctx.lineTo(6, 9); ctx.lineTo(10, 6); ctx.closePath();
            ctx.fill();
            ctx.fillStyle = '#38bdf8';
            ctx.fillRect(7, 4, 3, 7);
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(8, 5, 1, 5);
        } else if (type === 'lightning_beam') {
            // Concentrated blue-white high-voltage laser
            ctx.fillStyle = '#0284c7';
            ctx.fillRect(1, 6, 14, 4);
            ctx.fillStyle = '#38bdf8';
            ctx.fillRect(2, 7, 12, 2);
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(4, 7, 8, 2);
        } else if (type === 'void_scythe') {
            // Cursed void crescent blade
            ctx.fillStyle = '#581c87';
            ctx.beginPath();
            ctx.arc(8, 8, 7, -0.6, Math.PI * 0.8);
            ctx.lineWidth = 3; ctx.strokeStyle = '#a855f7'; ctx.stroke();
            ctx.fillStyle = '#c084fc';
            ctx.fillRect(7, 7, 3, 3);
        } else if (type === 'solar_beam') {
            // Blinding sacred solar core
            ctx.fillStyle = '#f59e0b';
            ctx.beginPath(); ctx.arc(8, 8, 7, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#fef08a';
            ctx.beginPath(); ctx.arc(8, 8, 4.5, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#ffffff';
            ctx.beginPath(); ctx.arc(8, 8, 2.5, 0, Math.PI * 2); ctx.fill();
        } else if (type === 'ice_boulder') {
            // Heavy faceted frost boulder
            ctx.fillStyle = '#0284c7';
            ctx.beginPath();
            ctx.moveTo(8, 2); ctx.lineTo(14, 6); ctx.lineTo(13, 13); ctx.lineTo(7, 15); ctx.lineTo(2, 10); ctx.closePath();
            ctx.fill();
            ctx.fillStyle = '#38bdf8';
            ctx.fillRect(5, 5, 6, 6);
            ctx.fillStyle = '#e0f2fe';
            ctx.fillRect(6, 6, 3, 3);
        } else if (type === 'acid_deluge') {
            // Venom bubbling cluster
            ctx.fillStyle = '#14532d';
            ctx.beginPath(); ctx.arc(8, 8, 6.5, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#22c55e';
            ctx.beginPath(); ctx.arc(7, 7, 4, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#86efac';
            ctx.fillRect(6, 6, 2, 2); ctx.fillRect(10, 8, 2, 2);
        }
        return canvas;
    }

    // ==========================================
    // 2. PLAYER SPRITES (Customizable Outfits)
    // ==========================================

    function createPlayerFrames(customOptions: any = {}) {
        const directions = ['down', 'up', 'left', 'right'];
        const frames = [0, 1, 2];

        const pal = {
            skin: '#ffccaa',
            skinDark: '#e6a882',
            hair: customOptions.hairColor || '#78350f',
            hatStyle: customOptions.hatStyle !== undefined ? customOptions.hatStyle : 'straw',
            hat: customOptions.hatColor || '#f59e0b',
            hatDark: customOptions.hatDarkColor || '#b45309',
            shirt: customOptions.shirtColor || '#3b82f6',
            overalls: customOptions.overallsColor || '#1e3a8a',
            overallsLight: customOptions.overallsLightColor || '#2563eb',
            boots: customOptions.bootsColor || '#451a03',
            eyes: '#1e293b'
        };

        const playerSprites = {};

        directions.forEach(dir => {
            playerSprites[dir] = [];
            frames.forEach(frame => {
                const { canvas, ctx } = makeCanvas(24, 32);
                const legOffset = (frame === 1) ? -2 : (frame === 2) ? 2 : 0;
                const bobY = (frame !== 0) ? 1 : 0;

                if (dir === 'down') {
                    // Hair base
                    ctx.fillStyle = pal.hair;
                    ctx.fillRect(6, 4 + bobY, 12, 6);

                    // Hat options
                    if (pal.hatStyle === 'straw') {
                        ctx.fillStyle = '#b45309'; ctx.fillRect(4, 3 + bobY, 16, 4);
                        ctx.fillStyle = '#f59e0b'; ctx.fillRect(6, 0 + bobY, 12, 5);
                        ctx.fillStyle = '#dc2626'; ctx.fillRect(6, 4 + bobY, 12, 2);
                    } else if (pal.hatStyle === 'cowboy') {
                        ctx.fillStyle = '#78350f'; ctx.fillRect(3, 3 + bobY, 18, 4);
                        ctx.fillStyle = '#92400e'; ctx.fillRect(6, 0 + bobY, 12, 5);
                        ctx.fillStyle = '#f59e0b'; ctx.fillRect(6, 3 + bobY, 12, 1);
                    } else if (pal.hatStyle === 'chef') {
                        ctx.fillStyle = '#f8fafc'; ctx.fillRect(6, 1 + bobY, 12, 6);
                        ctx.fillStyle = '#ffffff'; ctx.fillRect(4, -2 + bobY, 16, 5);
                    } else if (pal.hatStyle === 'flower') {
                        ctx.fillStyle = '#22c55e'; ctx.fillRect(5, 3 + bobY, 14, 2);
                        ctx.fillStyle = '#f43f5e'; ctx.fillRect(6, 2 + bobY, 3, 3);
                        ctx.fillStyle = '#facc15'; ctx.fillRect(11, 2 + bobY, 3, 3);
                        ctx.fillStyle = '#38bdf8'; ctx.fillRect(15, 2 + bobY, 3, 3);
                    } else if (pal.hatStyle === 'cap') {
                        ctx.fillStyle = '#dc2626'; ctx.fillRect(6, 1 + bobY, 12, 5);
                        ctx.fillRect(4, 4 + bobY, 16, 2);
                    }

                    // Face
                    ctx.fillStyle = pal.skin;
                    ctx.fillRect(7, 7 + bobY, 10, 8);
                    ctx.fillStyle = pal.eyes;
                    ctx.fillRect(9, 10 + bobY, 2, 3);
                    ctx.fillRect(13, 10 + bobY, 2, 3);
                    ctx.fillStyle = '#fca5a5';
                    ctx.fillRect(8, 12 + bobY, 2, 2);
                    ctx.fillRect(14, 12 + bobY, 2, 2);

                    // Shirt & Overalls
                    ctx.fillStyle = pal.shirt;
                    ctx.fillRect(6, 15 + bobY, 12, 5);
                    ctx.fillStyle = pal.overalls;
                    ctx.fillRect(7, 18 + bobY, 10, 7);
                    ctx.fillStyle = pal.overallsLight;
                    ctx.fillRect(8, 16 + bobY, 2, 4);
                    ctx.fillRect(14, 16 + bobY, 2, 4);
                    ctx.fillStyle = '#f59e0b';
                    ctx.fillRect(8, 18 + bobY, 2, 1);
                    ctx.fillRect(14, 18 + bobY, 2, 1);

                    // Hands
                    ctx.fillStyle = pal.skin;
                    ctx.fillRect(4, 17 + bobY, 2, 4);
                    ctx.fillRect(18, 17 + bobY, 2, 4);

                    // Legs / Boots
                    ctx.fillStyle = pal.overalls;
                    ctx.fillRect(7, 24 + bobY, 4, 3);
                    ctx.fillRect(13, 24 + bobY, 4, 3);
                    ctx.fillStyle = pal.boots;
                    ctx.fillRect(6, 27 + legOffset, 4, 4);
                    ctx.fillRect(14, 27 - legOffset, 4, 4);

                } else if (dir === 'up') {
                    // Back of head
                    ctx.fillStyle = pal.hair;
                    ctx.fillRect(7, 5 + bobY, 10, 10);

                    // Hat back
                    if (pal.hatStyle === 'straw') {
                        ctx.fillStyle = '#b45309'; ctx.fillRect(4, 3 + bobY, 16, 4);
                        ctx.fillStyle = '#f59e0b'; ctx.fillRect(6, 0 + bobY, 12, 5);
                    } else if (pal.hatStyle === 'cowboy') {
                        ctx.fillStyle = '#78350f'; ctx.fillRect(3, 3 + bobY, 18, 4);
                        ctx.fillStyle = '#92400e'; ctx.fillRect(6, 0 + bobY, 12, 5);
                    } else if (pal.hatStyle === 'chef') {
                        ctx.fillStyle = '#f8fafc'; ctx.fillRect(6, 1 + bobY, 12, 6);
                        ctx.fillStyle = '#ffffff'; ctx.fillRect(4, -2 + bobY, 16, 5);
                    } else if (pal.hatStyle === 'cap') {
                        ctx.fillStyle = '#dc2626'; ctx.fillRect(6, 1 + bobY, 12, 6);
                    }

                    // Shirt & Overalls back
                    ctx.fillStyle = pal.shirt;
                    ctx.fillRect(6, 15 + bobY, 12, 5);
                    ctx.fillStyle = pal.overalls;
                    ctx.fillRect(7, 17 + bobY, 10, 8);
                    ctx.fillStyle = pal.overallsLight;
                    ctx.fillRect(8, 16 + bobY, 8, 2);

                    // Legs
                    ctx.fillStyle = pal.boots;
                    ctx.fillRect(6, 27 - legOffset, 4, 4);
                    ctx.fillRect(14, 27 + legOffset, 4, 4);

                } else if (dir === 'left') {
                    // Side hair
                    ctx.fillStyle = pal.hair;
                    ctx.fillRect(10, 5 + bobY, 7, 9);

                    // Side hat
                    if (pal.hatStyle === 'straw') {
                        ctx.fillStyle = '#b45309'; ctx.fillRect(3, 3 + bobY, 16, 4);
                        ctx.fillStyle = '#f59e0b'; ctx.fillRect(5, 0 + bobY, 12, 5);
                        ctx.fillStyle = '#dc2626'; ctx.fillRect(5, 4 + bobY, 12, 2);
                    } else if (pal.hatStyle === 'cowboy') {
                        ctx.fillStyle = '#78350f'; ctx.fillRect(2, 3 + bobY, 17, 4);
                        ctx.fillStyle = '#92400e'; ctx.fillRect(5, 0 + bobY, 12, 5);
                    } else if (pal.hatStyle === 'chef') {
                        ctx.fillStyle = '#ffffff'; ctx.fillRect(4, -2 + bobY, 14, 7);
                    } else if (pal.hatStyle === 'cap') {
                        ctx.fillStyle = '#dc2626'; ctx.fillRect(5, 1 + bobY, 11, 5);
                        ctx.fillRect(2, 4 + bobY, 6, 2); // visor
                    }

                    // Face profile
                    ctx.fillStyle = pal.skin;
                    ctx.fillRect(5, 7 + bobY, 7, 8);
                    ctx.fillStyle = pal.eyes;
                    ctx.fillRect(6, 10 + bobY, 2, 3);

                    // Body
                    ctx.fillStyle = pal.shirt;
                    ctx.fillRect(6, 15 + bobY, 10, 5);
                    ctx.fillStyle = pal.overalls;
                    ctx.fillRect(7, 18 + bobY, 8, 7);
                    ctx.fillStyle = pal.skin;
                    ctx.fillRect(8 + legOffset, 18 + bobY, 3, 5);

                    // Legs
                    ctx.fillStyle = pal.boots;
                    ctx.fillRect(6 + legOffset, 27, 5, 4);
                    ctx.fillRect(11 - legOffset, 27, 4, 4);

                } else if (dir === 'right') {
                    ctx.save();
                    ctx.translate(24, 0);
                    ctx.scale(-1, 1);

                    ctx.fillStyle = pal.hair;
                    ctx.fillRect(10, 5 + bobY, 7, 9);

                    if (pal.hatStyle === 'straw') {
                        ctx.fillStyle = '#b45309'; ctx.fillRect(3, 3 + bobY, 16, 4);
                        ctx.fillStyle = '#f59e0b'; ctx.fillRect(5, 0 + bobY, 12, 5);
                        ctx.fillStyle = '#dc2626'; ctx.fillRect(5, 4 + bobY, 12, 2);
                    } else if (pal.hatStyle === 'cowboy') {
                        ctx.fillStyle = '#78350f'; ctx.fillRect(2, 3 + bobY, 17, 4);
                        ctx.fillStyle = '#92400e'; ctx.fillRect(5, 0 + bobY, 12, 5);
                    } else if (pal.hatStyle === 'chef') {
                        ctx.fillStyle = '#ffffff'; ctx.fillRect(4, -2 + bobY, 14, 7);
                    } else if (pal.hatStyle === 'cap') {
                        ctx.fillStyle = '#dc2626'; ctx.fillRect(5, 1 + bobY, 11, 5);
                        ctx.fillRect(2, 4 + bobY, 6, 2);
                    }

                    ctx.fillStyle = pal.skin;
                    ctx.fillRect(5, 7 + bobY, 7, 8);
                    ctx.fillStyle = pal.eyes;
                    ctx.fillRect(6, 10 + bobY, 2, 3);

                    ctx.fillStyle = pal.shirt;
                    ctx.fillRect(6, 15 + bobY, 10, 5);
                    ctx.fillStyle = pal.overalls;
                    ctx.fillRect(7, 18 + bobY, 8, 7);
                    ctx.fillStyle = pal.skin;
                    ctx.fillRect(8 + legOffset, 18 + bobY, 3, 5);

                    ctx.fillStyle = pal.boots;
                    ctx.fillRect(6 + legOffset, 27, 5, 4);
                    ctx.fillRect(11 - legOffset, 27, 4, 4);
                    ctx.restore();
                }

                playerSprites[dir].push(canvas);
            });
        });

        return playerSprites;
    }

    // ==========================================
    // 3. ANIMALS
    // ==========================================

    function createCowFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(40, 32);
            const tailSwing = (f === 1) ? 2 : 0;
            const headBob = (f === 1) ? 1 : 0;

            ctx.fillStyle = '#f8fafc';
            ctx.fillRect(8, 10, 24, 14);

            ctx.fillStyle = '#1e293b';
            ctx.fillRect(12, 10, 6, 6);
            ctx.fillRect(22, 14, 8, 8);
            ctx.fillRect(10, 18, 4, 4);

            ctx.fillStyle = '#f8fafc';
            ctx.fillRect(10, 24, 3, 6);
            ctx.fillRect(16, 24, 3, 6);
            ctx.fillRect(24, 24, 3, 6);
            ctx.fillRect(28, 24, 3, 6);

            ctx.fillStyle = '#334155';
            ctx.fillRect(10, 28, 3, 3);
            ctx.fillRect(16, 28, 3, 3);
            ctx.fillRect(24, 28, 3, 3);
            ctx.fillRect(28, 28, 3, 3);

            ctx.fillStyle = '#f472b6';
            ctx.fillRect(20, 22, 5, 3);

            ctx.fillStyle = '#f8fafc';
            ctx.fillRect(2, 6 + headBob, 10, 11);
            ctx.fillStyle = '#1e293b';
            ctx.fillRect(6, 6 + headBob, 4, 5);

            ctx.fillStyle = '#fbcfe8';
            ctx.fillRect(0, 11 + headBob, 6, 6);
            ctx.fillStyle = '#db2777';
            ctx.fillRect(1, 14 + headBob, 1, 1);
            ctx.fillRect(3, 14 + headBob, 1, 1);

            ctx.fillStyle = '#d97706';
            ctx.fillRect(4, 3 + headBob, 2, 3);
            ctx.fillRect(9, 3 + headBob, 2, 3);

            ctx.fillStyle = '#fbcfe8';
            ctx.fillRect(0, 6 + headBob, 3, 2);
            ctx.fillRect(11, 6 + headBob, 3, 2);

            ctx.fillStyle = '#0f172a';
            ctx.fillRect(7, 9 + headBob, 2, 2);

            ctx.fillStyle = '#f8fafc';
            ctx.fillRect(32, 12, 3, 6 + tailSwing);
            ctx.fillStyle = '#1e293b';
            ctx.fillRect(31, 17 + tailSwing, 4, 3);

            frames.push(canvas);
        });
        return frames;
    }


    function createChickenFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(24, 24);
            const peck = (f === 1) ? 2 : 0;

            ctx.fillStyle = '#ffffff';
            ctx.fillRect(6, 8, 12, 10);
            ctx.fillStyle = '#e2e8f0';
            ctx.fillRect(6, 14, 10, 4);

            ctx.fillStyle = '#f1f5f9';
            ctx.fillRect(9, 10, 6, 5);

            ctx.fillStyle = '#ef4444';
            ctx.fillRect(4, 2 + peck, 4, 3);
            ctx.fillRect(3, 9 + peck, 3, 3);

            ctx.fillStyle = '#ffffff';
            ctx.fillRect(3, 4 + peck, 6, 6);

            ctx.fillStyle = '#f59e0b';
            ctx.fillRect(1, 7 + peck, 3, 2);

            ctx.fillStyle = '#0f172a';
            ctx.fillRect(5, 5 + peck, 1, 2);

            ctx.fillStyle = '#ffffff';
            ctx.fillRect(16, 5, 4, 5);

            ctx.fillStyle = '#f59e0b';
            ctx.fillRect(8, 18, 2, 4);
            ctx.fillRect(13, 18, 2, 4);
            ctx.fillRect(7, 21, 3, 1);
            ctx.fillRect(12, 21, 3, 1);

            frames.push(canvas);
        });
        return frames;
    }


    function createSheepFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(36, 30);
            const bounce = (f === 1) ? 1 : 0;

            ctx.fillStyle = '#f1f5f9';
            ctx.beginPath();
            ctx.arc(16, 14 + bounce, 9, 0, Math.PI * 2);
            ctx.arc(24, 14 + bounce, 8, 0, Math.PI * 2);
            ctx.arc(20, 10 + bounce, 8, 0, Math.PI * 2);
            ctx.arc(14, 18 + bounce, 7, 0, Math.PI * 2);
            ctx.arc(22, 18 + bounce, 7, 0, Math.PI * 2);
            ctx.fill();

            ctx.fillStyle = '#334155';
            ctx.fillRect(4, 8 + bounce, 8, 8);
            ctx.fillStyle = '#475569';
            ctx.fillRect(2, 10 + bounce, 4, 4);

            ctx.fillStyle = '#f8fafc';
            ctx.fillRect(6, 9 + bounce, 2, 2);
            ctx.fillStyle = '#0f172a';
            ctx.fillRect(7, 10 + bounce, 1, 1);

            ctx.fillStyle = '#334155';
            ctx.fillRect(2, 7 + bounce, 3, 2);

            ctx.fillStyle = '#1e293b';
            ctx.fillRect(10, 22, 3, 6);
            ctx.fillRect(15, 22, 3, 6);
            ctx.fillRect(21, 22, 3, 6);
            ctx.fillRect(26, 22, 3, 6);

            frames.push(canvas);
        });
        return frames;
    }


    function createPigFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(36, 28);
            const waddle = (f === 1) ? 1 : 0;

            ctx.fillStyle = '#f472b6';
            ctx.fillRect(8, 8, 20, 12);
            ctx.fillStyle = '#ec4899';
            ctx.fillRect(8, 16, 20, 4);

            ctx.fillStyle = '#f472b6';
            ctx.fillRect(2, 6, 10, 10);

            ctx.fillStyle = '#fbcfe8';
            ctx.fillRect(0, 10, 5, 5);
            ctx.fillStyle = '#be185d';
            ctx.fillRect(1, 12, 1, 1);
            ctx.fillRect(3, 12, 1, 1);

            ctx.fillStyle = '#db2777';
            ctx.fillRect(3, 4, 3, 3);
            ctx.fillRect(8, 4, 3, 3);

            ctx.fillStyle = '#0f172a';
            ctx.fillRect(6, 8, 2, 2);

            ctx.fillStyle = '#db2777';
            ctx.fillRect(28, 10, 3, 2);
            ctx.fillRect(29, 8, 2, 2);

            ctx.fillStyle = '#be185d';
            ctx.fillRect(10, 20 - waddle, 3, 5);
            ctx.fillRect(15, 20 + waddle, 3, 5);
            ctx.fillRect(20, 20 - waddle, 3, 5);
            ctx.fillRect(24, 20 + waddle, 3, 5);

            frames.push(canvas);
        });
        return frames;
    }


    // ==========================================
    // 4. CROPS (Stages 0..3)
    // ==========================================

    function createCropSpriteSet(fruitColor, foliageColor = '#48bb78', shapeType = 'round') {
        const stages = [];

        // 0: Seeds
        {
            const { canvas, ctx } = makeCanvas(32, 32);
            ctx.fillStyle = '#d97706';
            ctx.fillRect(14, 20, 2, 2);
            ctx.fillRect(17, 22, 2, 2);
            ctx.fillRect(12, 23, 2, 2);
            stages.push(canvas);
        }
        // 1: Small Sprout
        {
            const { canvas, ctx } = makeCanvas(32, 32);
            ctx.fillStyle = '#38a169';
            ctx.fillRect(15, 22, 2, 6);
            ctx.fillStyle = '#68d391';
            ctx.fillRect(12, 18, 4, 3);
            ctx.fillRect(16, 17, 4, 3);
            stages.push(canvas);
        }
        // 2: Growing
        {
            const { canvas, ctx } = makeCanvas(32, 32);
            ctx.fillStyle = foliageColor;
            ctx.fillRect(14, 16, 4, 12);
            ctx.fillRect(8, 18, 6, 6);
            ctx.fillRect(18, 17, 6, 6);
            ctx.fillStyle = '#9ae6b4';
            ctx.fillRect(10, 14, 12, 4);
            stages.push(canvas);
        }
        // 3: Mature
        {
            const { canvas, ctx } = makeCanvas(32, 32);
            ctx.fillStyle = foliageColor;
            ctx.fillRect(14, 12, 4, 16);
            ctx.fillRect(6, 14, 8, 8);
            ctx.fillRect(18, 14, 8, 8);
            ctx.fillRect(10, 8, 12, 6);

            ctx.fillStyle = fruitColor;
            if (shapeType === 'carrot') {
                ctx.fillRect(14, 16, 4, 10);
                ctx.fillRect(15, 26, 2, 3);
                ctx.fillStyle = '#fff';
                ctx.fillRect(15, 18, 1, 3);
            } else if (shapeType === 'corn') {
                ctx.fillRect(13, 8, 6, 16);
                ctx.fillStyle = '#fde047';
                ctx.fillRect(14, 10, 4, 12);
            } else if (shapeType === 'wheat') {
                ctx.fillStyle = '#eab308';
                ctx.fillRect(10, 6, 4, 18);
                ctx.fillRect(15, 4, 4, 20);
                ctx.fillRect(20, 8, 4, 16);
                ctx.fillStyle = '#fef08a';
                ctx.fillRect(11, 7, 2, 8);
                ctx.fillRect(16, 5, 2, 10);
            } else if (shapeType === 'strawberry') {
                ctx.beginPath();
                ctx.arc(10, 18, 4, 0, Math.PI * 2);
                ctx.arc(22, 18, 4, 0, Math.PI * 2);
                ctx.arc(16, 22, 4, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(10, 17, 1, 1);
                ctx.fillRect(22, 17, 1, 1);
            } else {
                ctx.beginPath();
                ctx.arc(11, 16, 5, 0, Math.PI * 2);
                ctx.arc(21, 16, 5, 0, Math.PI * 2);
                ctx.arc(16, 20, 5, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(10, 14, 2, 2);
                ctx.fillRect(20, 14, 2, 2);
            }

            stages.push(canvas);
        }

        return stages;
    }

    // ==========================================
    // 5. ITEM ICONS (24x24 pixel icons)
    // ==========================================

    const iconCache = {};

    function generateItemIcon(itemId) {
        if (iconCache[itemId]) return iconCache[itemId];

        const { canvas, ctx } = makeCanvas(24, 24);

        switch(itemId) {
            case 'hoe':
                ctx.strokeStyle = '#854d0e'; ctx.lineWidth = 3;
                ctx.beginPath(); ctx.moveTo(4, 20); ctx.lineTo(16, 8); ctx.stroke();
                ctx.fillStyle = '#94a3b8'; ctx.fillRect(14, 4, 8, 4); ctx.fillRect(18, 7, 4, 5);
                break;
            case 'water':
            case 'watering_can':
                ctx.fillStyle = '#2563eb'; ctx.fillRect(6, 10, 10, 10);
                ctx.fillStyle = '#60a5fa'; ctx.fillRect(7, 11, 8, 3);
                ctx.strokeStyle = '#1d4ed8'; ctx.lineWidth = 2; ctx.strokeRect(4, 8, 5, 8);
                ctx.fillStyle = '#93c5fd'; ctx.fillRect(16, 8, 5, 3); ctx.fillRect(20, 6, 2, 3);
                ctx.fillStyle = '#38bdf8'; ctx.fillRect(21, 12, 2, 2);
                break;
            case 'scythe':
                ctx.strokeStyle = '#78350f'; ctx.lineWidth = 2;
                ctx.beginPath(); ctx.moveTo(6, 20); ctx.lineTo(12, 12); ctx.stroke();
                ctx.strokeStyle = '#cbd5e1'; ctx.lineWidth = 3;
                ctx.beginPath(); ctx.arc(14, 10, 7, Math.PI * 1.1, Math.PI * 1.8); ctx.stroke();
                break;
            case 'seeds':
            case 'wheat_seed':
            case 'carrot_seed':
            case 'tomato_seed':
            case 'corn_seed':
            case 'strawberry_seed':
                ctx.fillStyle = '#d97706'; ctx.fillRect(6, 6, 12, 14);
                ctx.fillStyle = '#f59e0b'; ctx.fillRect(8, 8, 8, 10);
                ctx.fillStyle = '#78350f'; ctx.fillRect(7, 5, 10, 3);
                ctx.fillStyle = '#16a34a'; ctx.fillRect(11, 11, 2, 4); ctx.fillRect(9, 10, 3, 2); ctx.fillRect(12, 10, 3, 2);
                break;
            case 'wheat':
                ctx.fillStyle = '#eab308'; ctx.fillRect(8, 6, 3, 14); ctx.fillRect(12, 4, 3, 16); ctx.fillRect(16, 8, 3, 12);
                ctx.fillStyle = '#fef08a'; ctx.fillRect(9, 7, 1, 6); ctx.fillRect(13, 5, 1, 8);
                break;
            case 'corn':
                ctx.fillStyle = '#16a34a'; ctx.fillRect(7, 12, 10, 8);
                ctx.fillStyle = '#eab308'; ctx.fillRect(9, 4, 6, 14);
                ctx.fillStyle = '#fef08a'; ctx.fillRect(10, 5, 4, 11);
                break;
            case 'carrot':
                ctx.fillStyle = '#ea580c'; ctx.beginPath(); ctx.moveTo(7, 6); ctx.lineTo(17, 6); ctx.lineTo(12, 20); ctx.fill();
                ctx.fillStyle = '#16a34a'; ctx.fillRect(10, 2, 2, 4); ctx.fillRect(12, 3, 3, 3);
                break;
            case 'tomato':
                ctx.fillStyle = '#ef4444'; ctx.beginPath(); ctx.arc(12, 13, 7, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#15803d'; ctx.fillRect(11, 4, 2, 3); ctx.fillRect(9, 6, 6, 2);
                ctx.fillStyle = '#fff'; ctx.fillRect(10, 10, 2, 2);
                break;
            case 'strawberry':
                ctx.fillStyle = '#f43f5e'; ctx.beginPath(); ctx.moveTo(6, 8); ctx.lineTo(18, 8); ctx.lineTo(12, 19); ctx.fill();
                ctx.fillStyle = '#15803d'; ctx.fillRect(9, 5, 6, 3);
                ctx.fillStyle = '#fff'; ctx.fillRect(10, 10, 1, 1); ctx.fillRect(13, 12, 1, 1);
                break;
            case 'milk':
            case 'goat_milk':
                ctx.fillStyle = '#f8fafc'; ctx.fillRect(8, 6, 8, 14);
                ctx.fillStyle = '#3b82f6'; ctx.fillRect(9, 11, 6, 4);
                ctx.fillStyle = '#94a3b8'; ctx.fillRect(10, 3, 4, 3);
                break;
            case 'egg':
            case 'duck_egg':
                ctx.fillStyle = '#fde68a'; ctx.beginPath(); ctx.ellipse(12, 13, 6, 8, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(10, 9, 2, 3);
                break;
            case 'wool':
            case 'rabbit_fur':
                ctx.fillStyle = '#e2e8f0'; ctx.beginPath(); ctx.arc(12, 12, 7, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(10, 9, 4, 3);
                break;
            case 'truffle':
                // Rich black truffle with textured golden-brown flecks
                ctx.fillStyle = '#292524'; ctx.beginPath(); ctx.arc(12, 13, 7, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#44403c'; ctx.beginPath(); ctx.arc(10, 11, 4, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#78716c'; ctx.fillRect(9, 9, 2, 2); ctx.fillRect(13, 14, 2, 2);
                ctx.fillStyle = '#ca8a04'; ctx.fillRect(11, 10, 1, 1);
                break;
            case 'bacon':
                ctx.fillStyle = '#be123c'; ctx.fillRect(5, 7, 14, 10);
                ctx.fillStyle = '#fecdd3'; ctx.fillRect(5, 9, 14, 2); ctx.fillRect(5, 13, 14, 2);
                break;
            case 'honey':
                ctx.fillStyle = '#f59e0b'; ctx.fillRect(7, 7, 10, 12);
                ctx.fillStyle = '#d97706'; ctx.fillRect(8, 4, 8, 3);
                ctx.fillStyle = '#fef3c7'; ctx.fillRect(9, 10, 6, 4);
                break;
            case 'bread':
                ctx.fillStyle = '#b45309'; ctx.fillRect(4, 9, 16, 10);
                ctx.fillStyle = '#f59e0b'; ctx.fillRect(6, 7, 12, 4);
                ctx.fillStyle = '#78350f'; ctx.fillRect(8, 8, 2, 4); ctx.fillRect(14, 8, 2, 4);
                break;
            case 'cheese':
                ctx.fillStyle = '#f59e0b'; ctx.beginPath(); ctx.moveTo(4, 18); ctx.lineTo(20, 18); ctx.lineTo(16, 8); ctx.fill();
                ctx.fillStyle = '#d97706'; ctx.fillRect(10, 14, 2, 2); ctx.fillRect(14, 12, 2, 2);
                break;
            case 'flour':
                ctx.fillStyle = '#f8fafc'; ctx.fillRect(6, 8, 12, 12);
                ctx.fillStyle = '#cbd5e1'; ctx.fillRect(8, 6, 8, 2);
                ctx.fillStyle = '#b45309'; ctx.font = 'bold 7px sans-serif'; ctx.fillText('F', 10, 17);
                break;
            case 'cake':
                ctx.fillStyle = '#fbcfe8'; ctx.fillRect(5, 11, 14, 9);
                ctx.fillStyle = '#f43f5e'; ctx.fillRect(5, 9, 14, 2);
                ctx.fillStyle = '#ef4444'; ctx.beginPath(); ctx.arc(12, 6, 3, 0, Math.PI * 2); ctx.fill();
                break;
            case 'cookie':
                ctx.fillStyle = '#d97706'; ctx.beginPath(); ctx.arc(12, 12, 7, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#451a03'; ctx.fillRect(9, 9, 2, 2); ctx.fillRect(13, 14, 2, 2); ctx.fillRect(14, 8, 2, 2);
                break;
            case 'pie':
                ctx.fillStyle = '#b45309'; ctx.beginPath(); ctx.moveTo(4, 16); ctx.lineTo(20, 16); ctx.lineTo(12, 8); ctx.fill();
                ctx.fillStyle = '#ea580c'; ctx.fillRect(8, 11, 8, 2);
                break;
            case 'pizza':
                ctx.fillStyle = '#b45309'; ctx.beginPath(); ctx.moveTo(4, 20); ctx.lineTo(20, 20); ctx.lineTo(12, 6); ctx.fill();
                ctx.fillStyle = '#facc15'; ctx.beginPath(); ctx.moveTo(6, 18); ctx.lineTo(18, 18); ctx.lineTo(12, 8); ctx.fill();
                ctx.fillStyle = '#ef4444'; ctx.fillRect(10, 13, 3, 3); ctx.fillRect(13, 16, 2, 2);
                break;
            case 'butter':
                ctx.fillStyle = '#fde047'; ctx.fillRect(6, 10, 12, 8);
                ctx.fillStyle = '#eab308'; ctx.fillRect(6, 16, 12, 2);
                break;
            case 'hay':
                ctx.fillStyle = '#ca8a04'; ctx.fillRect(5, 7, 14, 10);
                ctx.fillStyle = '#854d0e'; ctx.fillRect(5, 11, 14, 2);
                break;
            case 'coin':
            case 'gold':
                ctx.fillStyle = '#eab308'; ctx.beginPath(); ctx.arc(12, 12, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#fef08a'; ctx.fillRect(10, 8, 3, 8);
                break;
            case 'slingshot':
                ctx.strokeStyle = '#78350f'; ctx.lineWidth = 3;
                ctx.beginPath(); ctx.moveTo(12, 22); ctx.lineTo(12, 12); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(12, 12); ctx.lineTo(6, 6); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(12, 12); ctx.lineTo(18, 6); ctx.stroke();
                ctx.strokeStyle = '#dc2626'; ctx.lineWidth = 1.5;
                ctx.beginPath(); ctx.moveTo(6, 6); ctx.lineTo(12, 14); ctx.lineTo(18, 6); ctx.stroke();
                ctx.fillStyle = '#64748b'; ctx.fillRect(11, 13, 3, 3);
                break;
            case 'rifle':
            case 'hunting_rifle':
                ctx.fillStyle = '#78350f'; ctx.fillRect(3, 14, 8, 5);
                ctx.fillStyle = '#475569'; ctx.fillRect(8, 11, 13, 3);
                ctx.fillRect(10, 14, 2, 3);
                ctx.fillStyle = '#1e293b'; ctx.fillRect(12, 9, 4, 2);
                break;
            case 'beetle_shell':
                ctx.fillStyle = '#3b0764'; ctx.beginPath(); ctx.arc(12, 13, 7, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#7e22ce'; ctx.fillRect(8, 10, 8, 6);
                ctx.fillStyle = '#d8b4fe'; ctx.fillRect(9, 11, 3, 2);
                ctx.fillStyle = '#c084fc'; ctx.fillRect(4, 9, 3, 2); ctx.fillRect(17, 9, 3, 2);
                break;
            case 'demon_wing':
                ctx.fillStyle = '#991b1b'; ctx.beginPath(); ctx.ellipse(12, 12, 4, 8, Math.PI / 4, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ef4444'; ctx.beginPath(); ctx.ellipse(12, 12, 2, 6, Math.PI / 4, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#fca5a5'; ctx.fillRect(11, 11, 2, 2);
                break;
            case 'monster_essence':
                ctx.fillStyle = '#1e293b'; ctx.fillRect(10, 4, 4, 3);
                ctx.fillStyle = '#0f172a'; ctx.fillRect(7, 7, 10, 13);
                ctx.fillStyle = '#22c55e'; ctx.fillRect(8, 10, 8, 9);
                ctx.fillStyle = '#86efac'; ctx.fillRect(9, 11, 2, 2); ctx.fillRect(13, 14, 2, 2);
                break;
            case 'demon_elixir':
                ctx.fillStyle = '#78350f'; ctx.fillRect(10, 4, 4, 3);
                ctx.fillStyle = '#831843'; ctx.fillRect(7, 7, 10, 13);
                ctx.fillStyle = '#f43f5e'; ctx.fillRect(8, 10, 8, 9);
                ctx.fillStyle = '#fecdd3'; ctx.fillRect(9, 11, 2, 2);
                break;
            case 'iron_sword':
                ctx.fillStyle = '#64748b'; ctx.fillRect(11, 4, 3, 14);
                ctx.fillStyle = '#e2e8f0'; ctx.fillRect(12, 4, 1, 13);
                ctx.fillStyle = '#f59e0b'; ctx.fillRect(8, 17, 9, 2);
                ctx.fillStyle = '#78350f'; ctx.fillRect(11, 19, 3, 4);
                ctx.fillStyle = '#f59e0b'; ctx.fillRect(11, 23, 3, 2);
                break;
            case 'excalibur_sword':
                ctx.fillStyle = '#fef08a'; ctx.fillRect(11, 2, 3, 16);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(12, 2, 1, 15);
                ctx.fillStyle = '#38bdf8'; ctx.fillRect(12, 8, 1, 6);
                ctx.fillStyle = '#f59e0b'; ctx.fillRect(7, 17, 11, 3);
                ctx.fillStyle = '#0284c7'; ctx.fillRect(11, 17, 3, 3);
                ctx.fillStyle = '#78350f'; ctx.fillRect(11, 20, 3, 4);
                ctx.fillStyle = '#f59e0b'; ctx.fillRect(10, 24, 5, 2);
                break;
            case 'dragon_rifle':
                ctx.fillStyle = '#7f1d1d'; ctx.fillRect(2, 13, 8, 6);
                ctx.fillStyle = '#b91c1c'; ctx.fillRect(8, 10, 14, 4);
                ctx.fillStyle = '#f59e0b'; ctx.fillRect(18, 9, 4, 6);
                ctx.fillStyle = '#fef08a'; ctx.fillRect(20, 11, 2, 2);
                break;
            case 'shadow_pelt':
                ctx.fillStyle = '#1e1b4b'; ctx.fillRect(5, 7, 14, 12);
                ctx.fillStyle = '#312e81'; ctx.fillRect(6, 8, 12, 10);
                ctx.fillStyle = '#6366f1'; ctx.fillRect(8, 10, 4, 3);
                break;
            case 'wolf_fang':
                ctx.fillStyle = '#f8fafc'; ctx.beginPath(); ctx.moveTo(8, 6); ctx.lineTo(16, 6); ctx.lineTo(12, 20); ctx.fill();
                ctx.fillStyle = '#cbd5e1'; ctx.fillRect(9, 6, 6, 3);
                break;
            case 'iron_ore':
                ctx.fillStyle = '#475569'; ctx.beginPath(); ctx.arc(12, 13, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#94a3b8'; ctx.fillRect(8, 9, 4, 4); ctx.fillRect(13, 13, 5, 4);
                ctx.fillStyle = '#f8fafc'; ctx.fillRect(9, 10, 2, 2);
                break;
            case 'ruby_gem':
                ctx.fillStyle = '#b91c1c'; ctx.beginPath(); ctx.moveTo(12, 4); ctx.lineTo(20, 10); ctx.lineTo(12, 22); ctx.lineTo(4, 10); ctx.fill();
                ctx.fillStyle = '#ef4444'; ctx.beginPath(); ctx.moveTo(12, 7); ctx.lineTo(17, 11); ctx.lineTo(12, 19); ctx.lineTo(7, 11); ctx.fill();
                ctx.fillStyle = '#fecaca'; ctx.fillRect(10, 8, 2, 4);
                break;
            case 'cursed_wood':
                ctx.fillStyle = '#2e1065'; ctx.fillRect(5, 7, 14, 10);
                ctx.fillStyle = '#581c87'; ctx.fillRect(6, 9, 12, 3);
                ctx.fillStyle = '#c084fc'; ctx.fillRect(8, 8, 2, 2); ctx.fillRect(14, 12, 2, 2);
                break;
            case 'mana_gem':
                ctx.fillStyle = '#0369a1'; ctx.beginPath(); ctx.arc(12, 12, 7, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#38bdf8'; ctx.fillRect(9, 8, 6, 6);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(10, 9, 2, 2);
                break;
            case 'starflower_herb':
                ctx.fillStyle = '#15803d'; ctx.fillRect(11, 12, 2, 10);
                ctx.fillStyle = '#facc15'; ctx.beginPath(); ctx.arc(12, 8, 5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#38bdf8'; ctx.fillRect(11, 4, 2, 8); ctx.fillRect(8, 7, 8, 2);
                break;
            case 'blight_spore':
                ctx.fillStyle = '#701a75'; ctx.beginPath(); ctx.arc(12, 12, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#c026d3'; ctx.beginPath(); ctx.arc(12, 12, 6, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#f43f5e'; ctx.beginPath(); ctx.arc(10, 10, 3, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(10, 9, 2, 2);
                ctx.fillStyle = '#e879f9'; ctx.fillRect(5, 6, 2, 2); ctx.fillRect(18, 7, 2, 2); ctx.fillRect(17, 18, 2, 2); ctx.fillRect(6, 17, 2, 2);
                break;
            case 'antidote_serum':
                ctx.fillStyle = '#b45309'; ctx.fillRect(10, 3, 4, 3);
                ctx.fillStyle = '#94a3b8'; ctx.fillRect(9, 6, 6, 2);
                ctx.fillStyle = '#06b6d4'; ctx.beginPath(); ctx.arc(12, 15, 7, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#22d3ee'; ctx.beginPath(); ctx.arc(12, 15, 5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#a5f3fc'; ctx.fillRect(9, 12, 2, 4);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(11, 13, 2, 6); ctx.fillRect(9, 15, 6, 2);
                break;
            case 'health_potion':
                ctx.fillStyle = '#78350f'; ctx.fillRect(10, 4, 4, 3);
                ctx.fillStyle = '#b91c1c'; ctx.fillRect(7, 7, 10, 13);
                ctx.fillStyle = '#ef4444'; ctx.fillRect(8, 9, 8, 9);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(9, 10, 2, 2); ctx.fillRect(13, 14, 2, 2);
                break;
            case 'demon_heart':
                ctx.fillStyle = '#450a0a'; ctx.beginPath(); ctx.arc(9, 9, 6, 0, Math.PI * 2); ctx.fill();
                ctx.beginPath(); ctx.arc(15, 9, 6, 0, Math.PI * 2); ctx.fill();
                ctx.beginPath(); ctx.moveTo(3, 11); ctx.lineTo(21, 11); ctx.lineTo(12, 22); ctx.fill();
                ctx.fillStyle = '#dc2626'; ctx.fillRect(8, 8, 8, 8);
                ctx.fillStyle = '#f87171'; ctx.fillRect(10, 9, 2, 3);
                break;
            case 'crown_of_despair':
                ctx.fillStyle = '#ca8a04'; ctx.fillRect(4, 16, 16, 4);
                ctx.beginPath(); ctx.moveTo(4, 16); ctx.lineTo(4, 8); ctx.lineTo(8, 13); ctx.lineTo(12, 6); ctx.lineTo(16, 13); ctx.lineTo(20, 8); ctx.lineTo(20, 16); ctx.fill();
                ctx.fillStyle = '#ef4444'; ctx.fillRect(11, 10, 2, 2); ctx.fillRect(6, 17, 2, 2); ctx.fillRect(16, 17, 2, 2);
                break;
            case 'fishing_rod':
                ctx.fillStyle = '#a16207';
                ctx.fillRect(4, 18, 3, 3);
                ctx.strokeStyle = '#a16207'; ctx.lineWidth = 2;
                ctx.beginPath(); ctx.moveTo(4, 20); ctx.lineTo(19, 4); ctx.stroke();
                ctx.strokeStyle = '#e2e8f0'; ctx.lineWidth = 1;
                ctx.beginPath(); ctx.moveTo(19, 4); ctx.lineTo(20, 15); ctx.lineTo(18, 17); ctx.stroke();
                ctx.fillStyle = '#ef4444'; ctx.fillRect(18, 11, 3, 2);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(18, 13, 3, 2);
                break;
            case 'carp':
                ctx.fillStyle = '#f59e0b'; ctx.beginPath(); ctx.ellipse(12, 12, 8, 4, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#d97706'; ctx.beginPath(); ctx.moveTo(4, 12); ctx.lineTo(1, 8); ctx.lineTo(1, 16); ctx.fill();
                ctx.fillStyle = '#fbbf24'; ctx.fillRect(13, 9, 3, 2);
                ctx.fillStyle = '#1e293b'; ctx.fillRect(17, 11, 2, 2);
                break;
            case 'tilapia':
                ctx.fillStyle = '#38bdf8'; ctx.beginPath(); ctx.ellipse(12, 12, 8, 5, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#0284c7'; ctx.beginPath(); ctx.moveTo(4, 12); ctx.lineTo(1, 7); ctx.lineTo(1, 17); ctx.fill();
                ctx.fillStyle = '#bae6fd'; ctx.fillRect(10, 10, 4, 3);
                ctx.fillStyle = '#0f172a'; ctx.fillRect(16, 11, 2, 2);
                break;
            case 'catfish':
                ctx.fillStyle = '#334155'; ctx.beginPath(); ctx.ellipse(12, 12, 8, 4, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#1e293b'; ctx.beginPath(); ctx.moveTo(4, 12); ctx.lineTo(1, 8); ctx.lineTo(1, 16); ctx.fill();
                ctx.fillStyle = '#f8fafc'; ctx.fillRect(17, 11, 2, 2);
                ctx.fillStyle = '#64748b'; ctx.fillRect(18, 14, 4, 1); ctx.fillRect(18, 10, 4, 1);
                break;
            case 'golden_salmon':
                ctx.fillStyle = '#fbbf24'; ctx.beginPath(); ctx.ellipse(12, 12, 8, 4, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#f43f5e'; ctx.fillRect(8, 11, 6, 2);
                ctx.fillStyle = '#f59e0b'; ctx.beginPath(); ctx.moveTo(4, 12); ctx.lineTo(1, 7); ctx.lineTo(1, 17); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(16, 10, 2, 2);
                break;
            case 'ancient_glowfish':
                ctx.fillStyle = '#06b6d4'; ctx.beginPath(); ctx.ellipse(12, 12, 8, 5, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#67e8f9'; ctx.fillRect(8, 10, 6, 4);
                ctx.fillStyle = '#a5f3fc'; ctx.fillRect(10, 11, 2, 2);
                ctx.fillStyle = '#0891b2'; ctx.beginPath(); ctx.moveTo(4, 12); ctx.lineTo(0, 6); ctx.lineTo(0, 18); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(17, 10, 2, 2);
                break;
            case 'grilled_fish':
                ctx.fillStyle = '#e2e8f0'; ctx.beginPath(); ctx.ellipse(12, 14, 10, 6, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#b45309'; ctx.beginPath(); ctx.ellipse(12, 13, 7, 3, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#451a03'; ctx.fillRect(10, 11, 4, 1); ctx.fillRect(8, 13, 3, 1); ctx.fillRect(13, 13, 3, 1);
                ctx.fillStyle = '#facc15'; ctx.beginPath(); ctx.arc(17, 12, 3, 0, Math.PI * 2); ctx.fill();
                break;
            case 'spicy_fish_soup':
                ctx.fillStyle = '#78350f'; ctx.beginPath(); ctx.arc(12, 14, 8, 0, Math.PI); ctx.fill();
                ctx.fillStyle = '#dc2626'; ctx.beginPath(); ctx.ellipse(12, 12, 8, 3, 0, 0, Math.PI * 2); ctx.fill();
                break;
            case 'gold_ore':
                ctx.fillStyle = '#b45309'; ctx.beginPath(); ctx.arc(12, 13, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#facc15'; ctx.fillRect(8, 9, 5, 4); ctx.fillRect(13, 12, 5, 4);
                ctx.fillStyle = '#fef08a'; ctx.fillRect(9, 10, 2, 2); ctx.fillRect(14, 13, 2, 2);
                break;
            case 'diamond_crystal':
                ctx.fillStyle = '#0284c7'; ctx.beginPath(); ctx.moveTo(12, 3); ctx.lineTo(20, 9); ctx.lineTo(12, 22); ctx.lineTo(4, 9); ctx.fill();
                ctx.fillStyle = '#38bdf8'; ctx.beginPath(); ctx.moveTo(12, 6); ctx.lineTo(17, 10); ctx.lineTo(12, 19); ctx.lineTo(7, 10); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(10, 7, 3, 4); ctx.fillRect(12, 11, 2, 2);
                break;
            case 'bat_wing':
                ctx.fillStyle = '#311042'; ctx.beginPath(); ctx.ellipse(12, 12, 5, 8, Math.PI / 4, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#6b21a8'; ctx.beginPath(); ctx.ellipse(12, 12, 2, 6, Math.PI / 4, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#d8b4fe'; ctx.fillRect(11, 10, 2, 2);
                break;
            case 'crystal_core':
                ctx.fillStyle = '#0891b2'; ctx.beginPath(); ctx.arc(12, 12, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#67e8f9'; ctx.beginPath(); ctx.arc(12, 12, 5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(10, 9, 2, 2);
                break;
            case 'axe':
                // Woodcutter Axe
                ctx.strokeStyle = '#92400e'; ctx.lineWidth = 2.5;
                ctx.beginPath(); ctx.moveTo(4, 20); ctx.lineTo(19, 5); ctx.stroke();
                ctx.fillStyle = '#94a3b8';
                ctx.beginPath(); ctx.moveTo(13, 5); ctx.lineTo(21, 2); ctx.lineTo(21, 10); ctx.lineTo(15, 11); ctx.fill();
                ctx.fillStyle = '#f8fafc';
                ctx.fillRect(20, 3, 2, 7);
                break;
            case 'wood':
                // Wood log
                ctx.fillStyle = '#78350f';
                ctx.beginPath(); ctx.roundRect(4, 8, 16, 9, 3); ctx.fill();
                ctx.fillStyle = '#d4a373';
                ctx.beginPath(); ctx.ellipse(6, 12, 3, 4, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#92400e';
                ctx.fillRect(5, 12, 2, 1);
                ctx.fillStyle = '#451a03';
                ctx.fillRect(10, 10, 8, 1);
                ctx.fillRect(12, 14, 6, 1);
                break;
            case 'chest':
                // Storage Chest
                ctx.fillStyle = '#78350f';
                ctx.fillRect(4, 7, 16, 12);
                ctx.fillStyle = '#b45309';
                ctx.fillRect(5, 8, 14, 10);
                ctx.fillStyle = '#475569';
                ctx.fillRect(4, 7, 16, 2);
                ctx.fillRect(4, 12, 16, 1);
                ctx.fillRect(7, 7, 2, 12);
                ctx.fillRect(15, 7, 2, 12);
                ctx.fillStyle = '#facc15';
                ctx.fillRect(11, 11, 3, 3);
                break;
            case 'sapling':
                ctx.fillStyle = '#78350f';
                ctx.fillRect(11, 14, 2, 7);
                ctx.fillStyle = '#16a34a';
                ctx.beginPath(); ctx.ellipse(9, 12, 4, 2.5, -Math.PI / 4, 0, Math.PI * 2); ctx.fill();
                ctx.beginPath(); ctx.ellipse(15, 12, 4, 2.5, Math.PI / 4, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#4ade80';
                ctx.fillRect(11, 9, 2, 4);
                break;
            case 'backpack_upgrade_1':
            case 'backpack_upgrade_2':
                // Leather Adventurer Backpack
                ctx.fillStyle = '#78350f';
                ctx.beginPath(); ctx.roundRect(5, 6, 14, 14, 3); ctx.fill();
                ctx.fillStyle = '#92400e';
                ctx.fillRect(6, 8, 12, 10);
                ctx.fillStyle = '#451a03';
                ctx.fillRect(5, 6, 14, 5);
                ctx.fillStyle = '#facc15';
                ctx.fillRect(8, 10, 2, 3);
                ctx.fillRect(14, 10, 2, 3);
                ctx.fillStyle = '#ca8a04';
                ctx.fillRect(10, 3, 4, 3);
                break;
            case 'copper_ore':
                ctx.fillStyle = '#b45309'; ctx.beginPath(); ctx.arc(12, 13, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ea580c'; ctx.fillRect(8, 9, 5, 4); ctx.fillRect(13, 12, 5, 4);
                ctx.fillStyle = '#fdba74'; ctx.fillRect(9, 10, 2, 2); ctx.fillRect(14, 13, 2, 2);
                break;
            case 'stone':
                ctx.fillStyle = '#475569'; ctx.beginPath(); ctx.ellipse(12, 14, 7, 5, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#64748b'; ctx.beginPath(); ctx.ellipse(11, 13, 5, 3.5, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#94a3b8'; ctx.fillRect(9, 11, 2, 2);
                break;
            case 'star_core':
                ctx.fillStyle = '#7c3aed'; ctx.beginPath(); ctx.arc(12, 12, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#38bdf8';
                ctx.beginPath(); ctx.moveTo(12, 3); ctx.lineTo(14, 10); ctx.lineTo(21, 12); ctx.lineTo(14, 14); ctx.lineTo(12, 21); ctx.lineTo(10, 14); ctx.lineTo(3, 12); ctx.lineTo(10, 10); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(11, 11, 2, 2);
                break;
            case 'mayonnaise':
                ctx.fillStyle = '#eab308'; ctx.fillRect(8, 5, 8, 3);
                ctx.fillStyle = '#fef08a'; ctx.beginPath(); ctx.roundRect(7, 8, 10, 12, 2); ctx.fill();
                ctx.fillStyle = '#fef9c3'; ctx.fillRect(8, 9, 8, 10);
                ctx.fillStyle = '#ca8a04'; ctx.fillRect(9, 13, 6, 2);
                break;
            case 'strawberry_jam':
                ctx.fillStyle = '#ef4444'; ctx.fillRect(8, 5, 8, 3);
                ctx.fillStyle = '#b91c1c'; ctx.beginPath(); ctx.roundRect(7, 8, 10, 12, 2); ctx.fill();
                ctx.fillStyle = '#dc2626'; ctx.fillRect(8, 9, 8, 10);
                ctx.fillStyle = '#f87171'; ctx.fillRect(9, 11, 2, 3);
                break;
            case 'pickled_carrot':
                ctx.fillStyle = '#059669'; ctx.fillRect(8, 5, 8, 3);
                ctx.fillStyle = '#d1fae5'; ctx.beginPath(); ctx.roundRect(7, 8, 10, 12, 2); ctx.fill();
                ctx.fillStyle = '#ea580c'; ctx.fillRect(9, 10, 3, 7); ctx.fillRect(13, 12, 2, 5);
                break;
            case 'fine_wine':
                ctx.fillStyle = '#991b1b'; ctx.fillRect(10, 3, 4, 3);
                ctx.fillStyle = '#14532d'; ctx.fillRect(10, 6, 4, 5);
                ctx.fillStyle = '#15803d'; ctx.beginPath(); ctx.roundRect(8, 10, 8, 12, 2); ctx.fill();
                ctx.fillStyle = '#facc15'; ctx.fillRect(9, 13, 6, 4);
                break;
            case 'craft_ale':
                ctx.fillStyle = '#cbd5e1'; ctx.fillRect(7, 9, 10, 12);
                ctx.fillStyle = '#f59e0b'; ctx.fillRect(8, 10, 8, 10);
                ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(9, 8, 3, 0, Math.PI * 2); ctx.arc(13, 7, 3.5, 0, Math.PI * 2); ctx.arc(16, 8, 2.5, 0, Math.PI * 2); ctx.fill();
                ctx.strokeStyle = '#94a3b8'; ctx.lineWidth = 1.5; ctx.strokeRect(17, 11, 3, 6);
                break;
            case 'aged_cheese':
                ctx.fillStyle = '#d97706'; ctx.beginPath(); ctx.arc(12, 13, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#fbbf24'; ctx.beginPath(); ctx.arc(12, 13, 6.5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#92400e'; ctx.beginPath(); ctx.moveTo(12, 13); ctx.lineTo(19, 10); ctx.lineTo(17, 18); ctx.fill();
                break;
            case 'sprinkler_basic':
                ctx.fillStyle = '#b45309'; ctx.fillRect(10, 8, 4, 12); ctx.fillRect(6, 12, 12, 4);
                ctx.fillStyle = '#fdba74'; ctx.fillRect(11, 10, 2, 8); ctx.fillRect(8, 13, 8, 2);
                ctx.fillStyle = '#38bdf8'; ctx.fillRect(11, 7, 2, 2);
                break;
            case 'sprinkler_quality':
                ctx.fillStyle = '#eab308'; ctx.fillRect(10, 7, 4, 13); ctx.fillRect(5, 12, 14, 4);
                ctx.fillStyle = '#fef08a'; ctx.fillRect(11, 9, 2, 9); ctx.fillRect(7, 13, 10, 2);
                ctx.fillStyle = '#38bdf8'; ctx.beginPath(); ctx.arc(12, 7, 2.5, 0, Math.PI * 2); ctx.fill();
                break;
            case 'mayo_machine':
                ctx.fillStyle = '#64748b'; ctx.beginPath(); ctx.roundRect(6, 7, 12, 14, 2); ctx.fill();
                ctx.fillStyle = '#94a3b8'; ctx.fillRect(8, 9, 8, 7);
                ctx.fillStyle = '#fef08a'; ctx.fillRect(9, 11, 6, 4);
                ctx.fillStyle = '#f59e0b'; ctx.fillRect(11, 4, 2, 3);
                break;
            case 'cheese_press':
                ctx.fillStyle = '#78350f'; ctx.fillRect(5, 6, 14, 15);
                ctx.fillStyle = '#b45309'; ctx.fillRect(7, 8, 10, 11);
                ctx.fillStyle = '#facc15'; ctx.beginPath(); ctx.arc(12, 14, 3, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#475569'; ctx.fillRect(11, 3, 2, 4); ctx.fillRect(8, 3, 8, 2);
                break;
            case 'preserves_jar':
                ctx.fillStyle = '#78350f'; ctx.beginPath(); ctx.roundRect(6, 6, 12, 15, 3); ctx.fill();
                ctx.fillStyle = '#b45309'; ctx.fillRect(7, 8, 10, 11);
                ctx.fillStyle = '#f43f5e'; ctx.fillRect(8, 10, 8, 7);
                ctx.fillStyle = '#fbcfe8'; ctx.fillRect(9, 11, 2, 3);
                break;
            case 'wine_keg':
                ctx.fillStyle = '#78350f'; ctx.beginPath(); ctx.roundRect(5, 6, 14, 14, 4); ctx.fill();
                ctx.fillStyle = '#451a03'; ctx.fillRect(5, 9, 14, 2); ctx.fillRect(5, 15, 14, 2);
                ctx.fillStyle = '#d97706'; ctx.fillRect(11, 11, 2, 3);
                break;
            case 'horse_whistle':
                ctx.fillStyle = '#ca8a04'; ctx.beginPath(); ctx.roundRect(7, 10, 10, 5, 2); ctx.fill();
                ctx.fillStyle = '#fde047'; ctx.fillRect(8, 11, 4, 3);
                ctx.fillStyle = '#78350f'; ctx.fillRect(13, 8, 2, 3);
                break;
            case 'pet_basket':
                ctx.fillStyle = '#b45309'; ctx.beginPath(); ctx.ellipse(12, 14, 9, 6, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ef4444'; ctx.beginPath(); ctx.ellipse(12, 14, 7, 4, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#f87171'; ctx.fillRect(10, 13, 4, 2);
                break;
            case 'bouquet':
                // Beautiful flower bouquet with pink ribbon
                ctx.fillStyle = '#f43f5e'; ctx.beginPath(); ctx.arc(10, 8, 3.5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#facc15'; ctx.beginPath(); ctx.arc(15, 8, 3.5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ec4899'; ctx.beginPath(); ctx.arc(12, 5, 3.5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#84cc16'; ctx.fillRect(11, 11, 3, 7);
                ctx.fillStyle = '#f472b6'; ctx.fillRect(8, 14, 9, 3); // Ribbon bow
                ctx.fillStyle = '#db2777'; ctx.fillRect(10, 16, 2, 5); ctx.fillRect(13, 16, 2, 5);
                break;
            case 'mermaids_amulet':
                // Glowing blue seashell amulet with gold chain
                ctx.strokeStyle = '#eab308'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(12, 9, 7, Math.PI * 0.8, Math.PI * 2.2); ctx.stroke();
                ctx.fillStyle = '#0284c7'; ctx.beginPath(); ctx.arc(12, 15, 6, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#38bdf8'; ctx.beginPath(); ctx.arc(12, 15, 4, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(11, 13, 2, 2);
                break;
            case 'pineapple':
                // Golden pineapple
                ctx.fillStyle = '#f59e0b'; ctx.beginPath(); ctx.roundRect(8, 9, 9, 13, 4); ctx.fill();
                ctx.fillStyle = '#d97706'; ctx.fillRect(10, 11, 2, 2); ctx.fillRect(13, 14, 2, 2); ctx.fillRect(9, 16, 2, 2);
                ctx.fillStyle = '#22c55e'; // Spiky leaves
                ctx.beginPath(); ctx.moveTo(12, 2); ctx.lineTo(9, 9); ctx.lineTo(15, 9); ctx.closePath(); ctx.fill();
                ctx.beginPath(); ctx.moveTo(8, 5); ctx.lineTo(7, 10); ctx.lineTo(11, 9); ctx.closePath(); ctx.fill();
                ctx.beginPath(); ctx.moveTo(16, 5); ctx.lineTo(13, 9); ctx.lineTo(17, 10); ctx.closePath(); ctx.fill();
                break;
            case 'pineapple_seed':
                ctx.fillStyle = '#78350f'; ctx.fillRect(9, 13, 6, 7);
                ctx.fillStyle = '#84cc16'; ctx.fillRect(11, 7, 2, 6); ctx.fillRect(8, 9, 8, 2);
                break;
            case 'coconut':
                // Brown coconut
                ctx.fillStyle = '#78350f'; ctx.beginPath(); ctx.arc(12, 13, 7, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#451a03'; ctx.beginPath(); ctx.arc(10, 10, 1.5, 0, Math.PI * 2); ctx.arc(14, 10, 1.5, 0, Math.PI * 2); ctx.arc(12, 14, 1.5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#f8fafc'; ctx.fillRect(7, 13, 2, 3); // White flesh hint
                break;
            case 'banana':
                ctx.fillStyle = '#facc15'; ctx.beginPath(); ctx.arc(10, 10, 7, 0, Math.PI * 0.7); ctx.lineWidth = 3; ctx.strokeStyle = '#facc15'; ctx.stroke();
                ctx.fillStyle = '#713f12'; ctx.fillRect(7, 5, 2, 2);
                break;
            case 'mushroom_purple':
                // Mystical purple cave mushroom
                ctx.fillStyle = '#7e22ce'; ctx.beginPath(); ctx.arc(12, 10, 7, Math.PI, 0); ctx.fill();
                ctx.fillStyle = '#c084fc'; ctx.fillRect(8, 8, 2, 2); ctx.fillRect(14, 7, 2, 2);
                ctx.fillStyle = '#f3e8ff'; ctx.fillRect(11, 10, 3, 9);
                break;
            case 'mushroom_red':
                // Red toadstool
                ctx.fillStyle = '#dc2626'; ctx.beginPath(); ctx.arc(12, 10, 7, Math.PI, 0); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(9, 7, 2, 2); ctx.fillRect(14, 6, 2, 2);
                ctx.fillStyle = '#f1f5f9'; ctx.fillRect(11, 10, 3, 9);
                break;
            case 'mushroom_chanterelle':
                ctx.fillStyle = '#f59e0b'; ctx.beginPath(); ctx.arc(12, 9, 6, Math.PI, 0); ctx.fill();
                ctx.fillStyle = '#fbbf24'; ctx.fillRect(10, 9, 4, 8);
                break;
            case 'cinder_shard':
                // Glowing volcanic crystal
                ctx.fillStyle = '#ea580c'; ctx.beginPath(); ctx.moveTo(12, 3); ctx.lineTo(18, 12); ctx.lineTo(14, 21); ctx.lineTo(6, 15); ctx.closePath(); ctx.fill();
                ctx.fillStyle = '#facc15'; ctx.fillRect(10, 8, 4, 6);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(11, 9, 2, 2);
                break;
            case 'dragon_tooth':
                // Curved sharp dragon tooth
                ctx.fillStyle = '#f8fafc'; ctx.beginPath(); ctx.moveTo(9, 4); ctx.quadraticCurveTo(17, 10, 11, 21); ctx.quadraticCurveTo(8, 14, 9, 4); ctx.fill();
                ctx.fillStyle = '#94a3b8'; ctx.fillRect(8, 4, 3, 3);
                break;
            case 'magma_cap':
                ctx.fillStyle = '#c2410c'; ctx.beginPath(); ctx.arc(12, 10, 8, Math.PI, 0); ctx.fill();
                ctx.fillStyle = '#fde047'; ctx.fillRect(9, 7, 6, 2);
                ctx.fillStyle = '#451a03'; ctx.fillRect(11, 10, 3, 9);
                break;
            case 'volcano_sword':
                ctx.fillStyle = '#ea580c'; ctx.fillRect(11, 2, 3, 16);
                ctx.fillStyle = '#facc15'; ctx.fillRect(12, 3, 1, 14);
                ctx.fillStyle = '#7f1d1d'; ctx.fillRect(7, 17, 11, 3);
                ctx.fillStyle = '#292524'; ctx.fillRect(11, 20, 3, 4);
                break;
            case 'easter_egg':
                // Decorated Easter Egg
                ctx.fillStyle = '#f472b6'; ctx.beginPath(); ctx.ellipse(12, 13, 6, 8, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#38bdf8'; ctx.fillRect(7, 11, 10, 2);
                ctx.fillStyle = '#facc15'; ctx.fillRect(8, 14, 8, 2);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(10, 8, 2, 2);
                break;
            case 'luminarch_crystal_blade':
                // Prismatic Cyan Laser Blade
                ctx.fillStyle = '#0891b2'; ctx.fillRect(11, 2, 3, 16);
                ctx.fillStyle = '#22d3ee'; ctx.fillRect(12, 2, 1, 15);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(12, 5, 1, 10);
                ctx.fillStyle = '#06b6d4'; ctx.fillRect(7, 17, 11, 3);
                ctx.fillStyle = '#facc15'; ctx.fillRect(11, 17, 3, 3);
                ctx.fillStyle = '#0e7490'; ctx.fillRect(11, 20, 3, 4);
                ctx.fillStyle = '#67e8f9'; ctx.fillRect(10, 24, 5, 2);
                break;
            case 'hydra_venom_bow':
                // Serpent Venom Bow
                ctx.strokeStyle = '#15803d'; ctx.lineWidth = 2.5;
                ctx.beginPath(); ctx.arc(12, 12, 9, -Math.PI * 0.45, Math.PI * 0.45); ctx.stroke();
                ctx.strokeStyle = '#86efac'; ctx.lineWidth = 1;
                ctx.beginPath(); ctx.moveTo(17, 4); ctx.lineTo(17, 20); ctx.stroke();
                ctx.fillStyle = '#a855f7'; ctx.fillRect(10, 11, 8, 2); // Poison Arrow
                ctx.fillStyle = '#22c55e'; ctx.fillRect(18, 10, 3, 4);
                break;
            case 'volcano_magma_axe':
                // Double-Headed Molten Battleaxe
                ctx.fillStyle = '#292524'; ctx.fillRect(11, 3, 3, 20);
                ctx.fillStyle = '#dc2626'; // Left & right heads
                ctx.beginPath(); ctx.moveTo(11, 6); ctx.lineTo(4, 3); ctx.lineTo(3, 14); ctx.lineTo(11, 11); ctx.fill();
                ctx.beginPath(); ctx.moveTo(14, 6); ctx.lineTo(21, 3); ctx.lineTo(22, 14); ctx.lineTo(14, 11); ctx.fill();
                ctx.fillStyle = '#f97316'; ctx.fillRect(5, 6, 4, 5); ctx.fillRect(16, 6, 4, 5);
                ctx.fillStyle = '#fde047'; ctx.fillRect(6, 7, 2, 3); ctx.fillRect(17, 7, 2, 3);
                ctx.fillStyle = '#ef4444'; ctx.fillRect(11, 22, 3, 2);
                break;
            case 'glacial_titan_hammer':
                // Frost Titan Warhammer
                ctx.fillStyle = '#475569'; ctx.fillRect(11, 7, 3, 16);
                ctx.fillStyle = '#0284c7'; ctx.fillRect(6, 4, 13, 8);
                ctx.fillStyle = '#38bdf8'; ctx.fillRect(7, 5, 11, 6);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(8, 6, 4, 2); ctx.fillRect(13, 6, 4, 2);
                ctx.fillStyle = '#e0f2fe'; ctx.fillRect(4, 7, 3, 2); ctx.fillRect(18, 7, 3, 2); // Side Spikes
                ctx.fillStyle = '#0369a1'; ctx.fillRect(10, 22, 5, 3);
                break;
            case 'malakor_soul_scythe':
                // Nether Reaper Scythe
                ctx.strokeStyle = '#3b0764'; ctx.lineWidth = 2.5;
                ctx.beginPath(); ctx.moveTo(6, 23); ctx.lineTo(17, 4); ctx.stroke();
                ctx.fillStyle = '#7e22ce'; // Curved blade
                ctx.beginPath(); ctx.moveTo(17, 4); ctx.quadraticCurveTo(24, 2, 23, 12); ctx.quadraticCurveTo(19, 8, 15, 6); ctx.fill();
                ctx.fillStyle = '#c084fc'; ctx.fillRect(18, 5, 3, 3);
                ctx.fillStyle = '#a855f7'; ctx.beginPath(); ctx.arc(17, 5, 2.5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(16, 4, 1, 1);
                break;
            case 'sylvan_bow':
                // Nature Sylvan Bow
                ctx.strokeStyle = '#15803d'; ctx.lineWidth = 2.5;
                ctx.beginPath(); ctx.arc(10, 12, 10, -Math.PI * 0.4, Math.PI * 0.4); ctx.stroke();
                ctx.strokeStyle = '#4ade80'; ctx.lineWidth = 1;
                ctx.beginPath(); ctx.moveTo(17, 3); ctx.lineTo(17, 21); ctx.stroke();
                ctx.fillStyle = '#fef08a'; ctx.fillRect(10, 11, 4, 3);
                ctx.fillStyle = '#86efac'; ctx.fillRect(16, 2, 3, 3); ctx.fillRect(16, 19, 3, 3);
                break;
            case 'tempest_blade':
                // Tempest Lightning Blade
                ctx.strokeStyle = '#0284c7'; ctx.lineWidth = 2;
                ctx.beginPath(); ctx.moveTo(5, 19); ctx.lineTo(19, 5); ctx.stroke();
                ctx.fillStyle = '#38bdf8';
                ctx.beginPath(); ctx.moveTo(19, 5); ctx.lineTo(14, 4); ctx.lineTo(10, 12); ctx.lineTo(14, 10); ctx.closePath(); ctx.fill();
                ctx.fillStyle = '#fde047'; ctx.fillRect(4, 18, 4, 4);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(14, 7, 2, 2);
                break;
            case 'ancient_tree_heart':
                // Radiant sacred tree heart
                ctx.fillStyle = '#15803d'; ctx.beginPath(); ctx.arc(12, 12, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#22c55e'; ctx.beginPath(); ctx.arc(12, 12, 5.5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#fef08a'; ctx.fillRect(10, 10, 4, 4);
                break;
            case 'storm_core':
                // Pulsing electric storm core
                ctx.fillStyle = '#0284c7'; ctx.beginPath(); ctx.arc(12, 12, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#38bdf8'; ctx.beginPath(); ctx.arc(12, 12, 5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(10, 10, 4, 4);
                ctx.strokeStyle = '#fde047'; ctx.lineWidth = 1.5; ctx.strokeRect(7, 7, 10, 10);
                break;
            case 'star_fruit':
                // Golden star fruit
                ctx.fillStyle = '#eab308';
                ctx.beginPath();
                ctx.moveTo(12, 3); ctx.lineTo(15, 9); ctx.lineTo(21, 10); ctx.lineTo(17, 15);
                ctx.lineTo(18, 21); ctx.lineTo(12, 18); ctx.lineTo(6, 21); ctx.lineTo(7, 15);
                ctx.lineTo(3, 10); ctx.lineTo(9, 9); ctx.closePath(); ctx.fill();
                ctx.fillStyle = '#fef08a'; ctx.fillRect(11, 10, 3, 3);
                break;
            case 'thunder_crystal':
                // Jagged electric crystal
                ctx.fillStyle = '#0284c7';
                ctx.beginPath(); ctx.moveTo(12, 3); ctx.lineTo(19, 10); ctx.lineTo(15, 21); ctx.lineTo(8, 20); ctx.lineTo(5, 11); ctx.closePath(); ctx.fill();
                ctx.fillStyle = '#38bdf8';
                ctx.beginPath(); ctx.moveTo(12, 5); ctx.lineTo(17, 10); ctx.lineTo(14, 18); ctx.lineTo(9, 17); ctx.closePath(); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(11, 9, 2, 4);
                break;
            case 'farmer_stew':
                // Hearty Farmer Stew
                ctx.fillStyle = '#78350f'; ctx.beginPath(); ctx.ellipse(12, 14, 9, 6, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#b45309'; ctx.beginPath(); ctx.ellipse(12, 13, 7, 4, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ea580c'; ctx.fillRect(8, 11, 3, 2); // Carrot
                ctx.fillStyle = '#facc15'; ctx.fillRect(13, 12, 3, 2); // Potato
                ctx.fillStyle = '#22c55e'; ctx.fillRect(11, 13, 2, 2); // Herb
                ctx.fillStyle = '#ffffff'; ctx.fillRect(10, 6, 1, 3); ctx.fillRect(13, 5, 1, 3); // Steam
                break;
            case 'vigor_juice':
                // Glowing Golden Vigor Juice
                ctx.fillStyle = '#78350f'; ctx.fillRect(10, 3, 4, 3);
                ctx.fillStyle = '#fef08a'; ctx.fillRect(9, 6, 6, 2);
                ctx.fillStyle = '#f59e0b'; ctx.beginPath(); ctx.arc(12, 15, 7, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#fde047'; ctx.beginPath(); ctx.arc(12, 15, 5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(10, 12, 2, 4); ctx.fillRect(13, 14, 2, 3);
                break;
            case 'herbal_defense_soup':
                // Jade Herbal Defense Soup
                ctx.fillStyle = '#0f766e'; ctx.beginPath(); ctx.ellipse(12, 14, 9, 6, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#059669'; ctx.beginPath(); ctx.ellipse(12, 13, 7, 4, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#34d399'; ctx.fillRect(9, 11, 3, 2); ctx.fillRect(13, 12, 3, 2);
                ctx.fillStyle = '#38bdf8'; ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 1;
                ctx.beginPath(); ctx.arc(12, 13, 5, 0, Math.PI * 2); ctx.stroke(); // Shimmer ring
                ctx.fillStyle = '#ffffff'; ctx.fillRect(11, 6, 1, 3);
                break;
            case 'luminarch_crystal_heart':
                // 7-color Prismatic Heart
                ctx.fillStyle = '#06b6d4'; ctx.beginPath(); ctx.arc(9, 9, 5, 0, Math.PI * 2); ctx.arc(15, 9, 5, 0, Math.PI * 2); ctx.fill();
                ctx.beginPath(); ctx.moveTo(4, 10); ctx.lineTo(20, 10); ctx.lineTo(12, 21); ctx.fill();
                ctx.fillStyle = '#a855f7'; ctx.fillRect(8, 8, 4, 4);
                ctx.fillStyle = '#38bdf8'; ctx.fillRect(12, 8, 4, 4);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(9, 7, 2, 2);
                break;
            case 'hydra_venom_gland':
                // Poison gland flask
                ctx.fillStyle = '#166534'; ctx.beginPath(); ctx.arc(12, 13, 7, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#22c55e'; ctx.beginPath(); ctx.arc(12, 13, 5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#86efac'; ctx.fillRect(10, 11, 2, 4); ctx.fillRect(12, 19, 2, 3); // Drip
                break;
            case 'hydra_scale':
                ctx.fillStyle = '#14532d'; ctx.beginPath(); ctx.arc(12, 12, 7, 0, Math.PI); ctx.fill();
                ctx.fillStyle = '#16a34a'; ctx.beginPath(); ctx.arc(12, 10, 5, 0, Math.PI); ctx.fill();
                ctx.fillStyle = '#4ade80'; ctx.fillRect(10, 13, 4, 2);
                break;
            case 'magma_dragon_horn':
                ctx.fillStyle = '#7f1d1d'; ctx.beginPath(); ctx.moveTo(6, 21); ctx.quadraticCurveTo(8, 8, 18, 3); ctx.quadraticCurveTo(15, 14, 10, 21); ctx.fill();
                ctx.fillStyle = '#ea580c'; ctx.fillRect(9, 11, 4, 4);
                ctx.fillStyle = '#fde047'; ctx.fillRect(13, 6, 2, 2);
                break;
            case 'flame_heart':
                ctx.fillStyle = '#991b1b'; ctx.beginPath(); ctx.arc(12, 12, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ea580c'; ctx.beginPath(); ctx.arc(12, 12, 5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#fde047'; ctx.fillRect(11, 10, 3, 3);
                break;
            case 'glacial_titan_core':
                ctx.fillStyle = '#0284c7'; ctx.beginPath(); ctx.moveTo(12, 3); ctx.lineTo(20, 12); ctx.lineTo(12, 21); ctx.lineTo(4, 12); ctx.fill();
                ctx.fillStyle = '#7dd3fc'; ctx.beginPath(); ctx.moveTo(12, 6); ctx.lineTo(17, 12); ctx.lineTo(12, 18); ctx.lineTo(7, 12); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(11, 10, 2, 4); ctx.fillRect(10, 11, 4, 2);
                break;
            case 'frost_crystal':
                ctx.fillStyle = '#38bdf8'; ctx.fillRect(11, 3, 2, 18); ctx.fillRect(3, 11, 18, 2);
                ctx.fillStyle = '#e0f2fe'; ctx.fillRect(7, 7, 10, 10);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(10, 10, 4, 4);
                break;
            case 'death_lord_soul':
                ctx.fillStyle = '#3b0764'; ctx.beginPath(); ctx.arc(12, 11, 7, 0, Math.PI * 2); ctx.fill();
                ctx.beginPath(); ctx.moveTo(5, 12); ctx.lineTo(12, 22); ctx.lineTo(19, 12); ctx.fill();
                ctx.fillStyle = '#a855f7'; ctx.fillRect(9, 9, 2, 3); ctx.fillRect(13, 9, 2, 3); // Soul eyes
                ctx.fillStyle = '#c084fc'; ctx.fillRect(10, 14, 4, 2);
                break;
            case 'cursed_relic':
                ctx.fillStyle = '#334155'; ctx.fillRect(5, 4, 14, 17);
                ctx.fillStyle = '#1e293b'; ctx.fillRect(7, 6, 10, 13);
                ctx.fillStyle = '#a855f7'; ctx.fillRect(8, 8, 4, 2); ctx.fillRect(11, 12, 4, 2); ctx.fillRect(9, 15, 5, 2);
                break;
            case 'swamp_herb':
                ctx.fillStyle = '#065f46'; ctx.fillRect(11, 12, 2, 9);
                ctx.fillStyle = '#10b981'; ctx.beginPath(); ctx.arc(12, 9, 6, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#a7f3d0'; ctx.beginPath(); ctx.arc(12, 9, 3, 0, Math.PI * 2); ctx.fill();
                break;
            case 'frost_berry':
                ctx.fillStyle = '#0369a1'; ctx.beginPath(); ctx.arc(9, 14, 4, 0, Math.PI * 2); ctx.arc(15, 14, 4, 0, Math.PI * 2); ctx.arc(12, 9, 4, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#7dd3fc'; ctx.fillRect(8, 12, 2, 2); ctx.fillRect(14, 12, 2, 2); ctx.fillRect(11, 7, 2, 2);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(9, 13, 1, 1); ctx.fillRect(15, 13, 1, 1); ctx.fillRect(12, 8, 1, 1);
                break;
            case 'ring_glow':
                // Gold band with radiant glowing yellow gem
                ctx.strokeStyle = '#f59e0b'; ctx.lineWidth = 2.5;
                ctx.beginPath(); ctx.arc(12, 14, 6, 0, Math.PI * 2); ctx.stroke();
                ctx.fillStyle = '#fef08a'; ctx.beginPath(); ctx.arc(12, 7, 4, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(11, 6, 2, 2);
                break;
            case 'ring_magnet':
                // Steel-cobalt ring with blue-red tips
                ctx.strokeStyle = '#64748b'; ctx.lineWidth = 2.5;
                ctx.beginPath(); ctx.arc(12, 14, 6, 0, Math.PI * 2); ctx.stroke();
                ctx.fillStyle = '#3b82f6'; ctx.fillRect(8, 5, 3, 4);
                ctx.fillStyle = '#ef4444'; ctx.fillRect(13, 5, 3, 4);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(10, 6, 4, 2);
                break;
            case 'ring_warrior':
                // Platinum spiked ring with blood ruby
                ctx.strokeStyle = '#94a3b8'; ctx.lineWidth = 2.5;
                ctx.beginPath(); ctx.arc(12, 14, 6, 0, Math.PI * 2); ctx.stroke();
                ctx.fillStyle = '#dc2626'; ctx.beginPath(); ctx.moveTo(12, 3); ctx.lineTo(16, 8); ctx.lineTo(12, 12); ctx.lineTo(8, 8); ctx.fill();
                ctx.fillStyle = '#fca5a5'; ctx.fillRect(11, 6, 2, 2);
                break;
            case 'ring_vampiric':
                // Dark obsidian ring with purple-crimson jewel
                ctx.strokeStyle = '#1e1b4b'; ctx.lineWidth = 2.5;
                ctx.beginPath(); ctx.arc(12, 14, 6, 0, Math.PI * 2); ctx.stroke();
                ctx.fillStyle = '#991b1b'; ctx.beginPath(); ctx.arc(12, 7, 4, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#c084fc'; ctx.fillRect(11, 6, 2, 2);
                break;
            case 'ring_lucky':
                // Gold band with brilliant emerald clover gem
                ctx.strokeStyle = '#d97706'; ctx.lineWidth = 2.5;
                ctx.beginPath(); ctx.arc(12, 14, 6, 0, Math.PI * 2); ctx.stroke();
                ctx.fillStyle = '#10b981'; ctx.beginPath(); ctx.arc(12, 7, 4, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#6ee7b7'; ctx.fillRect(11, 6, 2, 2);
                break;
            case 'rune_fire':
                ctx.fillStyle = '#dc2626'; ctx.beginPath(); ctx.arc(12, 12, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#f97316'; ctx.beginPath(); ctx.arc(12, 12, 5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#fef08a'; ctx.fillRect(11, 9, 2, 6); ctx.fillRect(9, 11, 6, 2);
                break;
            case 'rune_frost':
                ctx.fillStyle = '#0284c7'; ctx.beginPath(); ctx.arc(12, 12, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#38bdf8'; ctx.beginPath(); ctx.arc(12, 12, 5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#e0f2fe'; ctx.fillRect(11, 8, 2, 8); ctx.fillRect(8, 11, 8, 2);
                break;
            case 'rune_lightning':
                ctx.fillStyle = '#d97706'; ctx.beginPath(); ctx.arc(12, 12, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#facc15'; ctx.beginPath(); ctx.arc(12, 12, 5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(11, 7, 3, 5); ctx.fillRect(10, 11, 4, 6);
                break;
            case 'rune_vampiric':
                ctx.fillStyle = '#7e22ce'; ctx.beginPath(); ctx.arc(12, 12, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#c084fc'; ctx.beginPath(); ctx.arc(12, 12, 5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#f43f5e'; ctx.fillRect(11, 9, 2, 6); ctx.fillRect(9, 11, 6, 2);
                break;
            case 'sacred_shard_earth':
            case 'sacred_shard_sun':
            case 'sacred_shard_water':
            case 'sacred_shard_fire':
            case 'sacred_shard_frost':
            case 'sacred_shard_shadow':
            case 'sacred_shard_nature':
            case 'sacred_shard_thunder':
                const sColor = itemId.includes('earth') ? '#22c55e' : (itemId.includes('sun') ? '#facc15' : (itemId.includes('water') ? '#38bdf8' : (itemId.includes('fire') ? '#ef4444' : (itemId.includes('frost') ? '#67e8f9' : (itemId.includes('nature') ? '#10b981' : (itemId.includes('thunder') ? '#38bdf8' : '#a855f7'))))));
                ctx.fillStyle = '#1e293b'; ctx.beginPath(); ctx.arc(12, 12, 9, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = sColor; ctx.beginPath(); ctx.moveTo(12, 4); ctx.lineTo(19, 12); ctx.lineTo(12, 20); ctx.lineTo(5, 12); ctx.closePath(); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillRect(11, 9, 3, 3);
                break;
            case 'wood_fence':
                ctx.fillStyle = '#78350f'; ctx.fillRect(5, 6, 4, 14); ctx.fillRect(15, 6, 4, 14);
                ctx.fillStyle = '#b45309'; ctx.fillRect(4, 9, 16, 3); ctx.fillRect(4, 14, 16, 3);
                break;
            case 'stone_fence':
                ctx.fillStyle = '#475569'; ctx.fillRect(5, 7, 5, 13); ctx.fillRect(14, 7, 5, 13);
                ctx.fillStyle = '#94a3b8'; ctx.fillRect(4, 10, 16, 4);
                break;
            case 'stone_path':
                ctx.fillStyle = '#64748b'; ctx.fillRect(4, 4, 16, 16);
                ctx.fillStyle = '#94a3b8'; ctx.fillRect(6, 6, 6, 5); ctx.fillRect(13, 7, 5, 4); ctx.fillRect(7, 13, 8, 5);
                break;
            case 'wood_path':
                ctx.fillStyle = '#b45309'; ctx.fillRect(4, 4, 16, 16);
                ctx.fillStyle = '#d97706'; ctx.fillRect(5, 6, 14, 3); ctx.fillRect(5, 11, 14, 3); ctx.fillRect(5, 16, 14, 3);
                break;
            case 'farm_lantern':
                ctx.fillStyle = '#78350f'; ctx.fillRect(11, 12, 2, 10);
                ctx.fillStyle = '#f59e0b'; ctx.fillRect(8, 6, 8, 7);
                ctx.fillStyle = '#fef08a'; ctx.fillRect(9, 7, 6, 5);
                break;
            case 'windmill_kit':
                ctx.fillStyle = '#64748b'; ctx.fillRect(8, 10, 8, 12);
                ctx.fillStyle = '#fef08a'; ctx.fillRect(6, 4, 12, 2); ctx.fillRect(11, 2, 2, 12);
                break;
            case 'silo_kit':
                ctx.fillStyle = '#dc2626'; ctx.fillRect(7, 8, 10, 14);
                ctx.fillStyle = '#991b1b'; ctx.beginPath(); ctx.arc(12, 8, 5, Math.PI, 0); ctx.fill();
                break;
            case 'fish_tank':
                ctx.fillStyle = '#38bdf8'; ctx.fillRect(4, 6, 16, 14);
                ctx.fillStyle = '#0284c7'; ctx.strokeRect(4, 6, 16, 14);
                ctx.fillStyle = '#f97316'; ctx.fillRect(8, 12, 4, 2);
                break;
            case 'spire_shard':
                ctx.fillStyle = '#c084fc'; ctx.beginPath(); ctx.moveTo(12, 4); ctx.lineTo(17, 12); ctx.lineTo(12, 20); ctx.lineTo(7, 12); ctx.closePath(); ctx.fill();
                ctx.fillStyle = '#f3e8ff'; ctx.fillRect(11, 9, 2, 4);
                break;
            case 'spire_blade':
                ctx.fillStyle = '#facc15'; ctx.beginPath(); ctx.moveTo(18, 4); ctx.lineTo(21, 6); ctx.lineTo(8, 19); ctx.lineTo(5, 18); ctx.closePath(); ctx.fill();
                ctx.fillStyle = '#c084fc'; ctx.fillRect(6, 16, 4, 4);
                break;
            case 'spire_bow':
                ctx.strokeStyle = '#c084fc'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(14, 12, 9, Math.PI * 0.6, Math.PI * 1.4); ctx.stroke();
                ctx.strokeStyle = '#facc15'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(8, 5); ctx.lineTo(8, 19); ctx.stroke();
                break;
            case 'spire_staff':
                ctx.fillStyle = '#78350f'; ctx.fillRect(6, 14, 3, 8);
                ctx.fillStyle = '#c084fc'; ctx.beginPath(); ctx.arc(15, 8, 6, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#facc15'; ctx.fillRect(14, 7, 3, 3);
                break;
            case 'sugar':
                ctx.fillStyle = '#e2e8f0'; ctx.fillRect(6, 8, 12, 12);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(7, 9, 10, 5);
                break;
            case 'clay':
                ctx.fillStyle = '#b45309'; ctx.beginPath(); ctx.ellipse(12, 14, 7, 5, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#d97706'; ctx.fillRect(9, 12, 4, 3);
                break;
            default:
                // Generic item box
                ctx.fillStyle = '#38bdf8'; ctx.fillRect(5, 5, 14, 14);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(7, 7, 10, 10);
                ctx.fillStyle = '#0284c7'; ctx.fillRect(9, 9, 6, 6);
                break;
        }

        iconCache[itemId] = canvas;
        return canvas;
    }

    // Set sprite references

    // Placeable Decor & Structure Sprites
    function createWoodFenceTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#78350f'; ctx.fillRect(6, 4, 5, 26); ctx.fillRect(21, 4, 5, 26);
        ctx.fillStyle = '#b45309'; ctx.fillRect(4, 9, 24, 4); ctx.fillRect(4, 18, 24, 4);
        ctx.fillStyle = '#d97706'; ctx.fillRect(7, 5, 2, 24); ctx.fillRect(22, 5, 2, 24);
        return canvas;
    }

    function createStoneFenceTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#475569'; ctx.fillRect(5, 6, 6, 24); ctx.fillRect(21, 6, 6, 24);
        ctx.fillStyle = '#64748b'; ctx.fillRect(3, 10, 26, 6); ctx.fillRect(3, 20, 26, 5);
        ctx.fillStyle = '#94a3b8'; ctx.fillRect(6, 7, 3, 22); ctx.fillRect(22, 7, 3, 22);
        return canvas;
    }

    function createStonePathTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#475569'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#64748b';
        ctx.fillRect(2, 2, 12, 12); ctx.fillRect(16, 2, 14, 10);
        ctx.fillRect(2, 16, 14, 14); ctx.fillRect(18, 14, 12, 16);
        ctx.fillStyle = '#94a3b8';
        ctx.fillRect(4, 4, 4, 4); ctx.fillRect(18, 4, 4, 4); ctx.fillRect(4, 18, 4, 4); ctx.fillRect(20, 16, 4, 4);
        return canvas;
    }

    function createWoodPathTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#78350f'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#b45309';
        ctx.fillRect(2, 2, 28, 7); ctx.fillRect(2, 11, 28, 8); ctx.fillRect(2, 21, 28, 9);
        ctx.fillStyle = '#d97706';
        ctx.fillRect(4, 4, 20, 2); ctx.fillRect(4, 13, 20, 2); ctx.fillRect(4, 23, 20, 2);
        ctx.fillStyle = '#451a03';
        ctx.fillRect(3, 4, 2, 2); ctx.fillRect(26, 4, 2, 2);
        ctx.fillRect(3, 14, 2, 2); ctx.fillRect(26, 14, 2, 2);
        return canvas;
    }

    function createFarmLanternTile() {
        const { canvas, ctx } = makeCanvas(32, 48);
        ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.beginPath(); ctx.ellipse(16, 44, 8, 3, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#78350f'; ctx.fillRect(14, 16, 4, 28);
        ctx.fillStyle = '#b45309'; ctx.fillRect(12, 14, 8, 3);
        ctx.fillStyle = '#f59e0b'; ctx.fillRect(10, 6, 12, 9);
        ctx.fillStyle = '#fef08a'; ctx.fillRect(12, 8, 8, 5);
        ctx.fillStyle = '#451a03'; ctx.fillRect(9, 4, 14, 3); ctx.fillRect(14, 2, 4, 3);
        return canvas;
    }

    function createWindmillBuilding() {
        const { canvas, ctx } = makeCanvas(64, 80);
        ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.beginPath(); ctx.ellipse(32, 74, 24, 6, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#475569'; ctx.fillRect(16, 44, 32, 30);
        ctx.fillStyle = '#94a3b8'; ctx.fillRect(18, 46, 28, 4);
        ctx.fillStyle = '#b45309'; ctx.fillRect(20, 16, 24, 28);
        ctx.fillStyle = '#78350f'; ctx.beginPath(); ctx.moveTo(18, 16); ctx.lineTo(32, 2); ctx.lineTo(46, 16); ctx.closePath(); ctx.fill();
        ctx.fillStyle = '#334155'; ctx.fillRect(26, 56, 12, 18);
        ctx.fillStyle = '#1e293b'; ctx.beginPath(); ctx.arc(32, 24, 5, 0, Math.PI * 2); ctx.fill();
        return canvas;
    }

    function createSiloBuilding() {
        const { canvas, ctx } = makeCanvas(48, 72);
        ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.beginPath(); ctx.ellipse(24, 68, 18, 4, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#991b1b'; ctx.fillRect(10, 20, 28, 48);
        ctx.fillStyle = '#dc2626'; ctx.fillRect(13, 20, 22, 48);
        ctx.fillStyle = '#64748b'; ctx.beginPath(); ctx.arc(24, 20, 14, Math.PI, 0); ctx.fill();
        ctx.fillStyle = '#94a3b8'; ctx.fillRect(23, 4, 2, 4);
        ctx.fillStyle = '#475569';
        ctx.fillRect(9, 32, 30, 3); ctx.fillRect(9, 46, 30, 3); ctx.fillRect(9, 60, 30, 3);
        return canvas;
    }

    function createFishTankFurniture() {
        const { canvas, ctx } = makeCanvas(48, 40);
        ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.beginPath(); ctx.ellipse(24, 36, 18, 4, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#78350f'; ctx.fillRect(8, 26, 32, 10);
        ctx.fillStyle = '#b45309'; ctx.fillRect(10, 28, 28, 6);
        ctx.fillStyle = 'rgba(56, 189, 248, 0.45)'; ctx.fillRect(6, 6, 36, 20);
        ctx.strokeStyle = '#0284c7'; ctx.lineWidth = 2; ctx.strokeRect(6, 6, 36, 20);
        ctx.fillStyle = '#e2e8f0'; ctx.fillRect(8, 22, 32, 3);
        ctx.fillStyle = '#16a34a'; ctx.fillRect(10, 12, 3, 10); ctx.fillRect(34, 10, 3, 12);
        ctx.fillStyle = '#f97316'; ctx.fillRect(18, 14, 6, 3); ctx.fillRect(24, 13, 2, 5);
        ctx.fillStyle = '#fde047'; ctx.fillRect(22, 10, 5, 2); ctx.fillRect(20, 9, 2, 4);
        return canvas;
    }

    function createSpirePortal() {
        const { canvas, ctx } = makeCanvas(64, 64);
        ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.beginPath(); ctx.ellipse(32, 56, 22, 6, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#475569'; ctx.fillRect(14, 16, 6, 40); ctx.fillRect(44, 16, 6, 40);
        ctx.fillRect(10, 10, 44, 8);
        ctx.fillStyle = '#c084fc'; ctx.fillRect(20, 18, 24, 38);
        ctx.fillStyle = '#e9d5ff'; ctx.fillRect(24, 22, 16, 30);
        ctx.fillStyle = '#fdf4ff'; ctx.fillRect(28, 26, 8, 22);
        return canvas;
    }

    SPRITES.woodFence = createWoodFenceTile();
    SPRITES.stoneFence = createStoneFenceTile();
    SPRITES.stonePath = createStonePathTile();
    SPRITES.woodPath = createWoodPathTile();
    SPRITES.farmLantern = createFarmLanternTile();
    SPRITES.windmill = createWindmillBuilding();
    SPRITES.silo = createSiloBuilding();
    SPRITES.fishTank = createFishTankFurniture();
    SPRITES.spirePortal = createSpirePortal();

    SPRITES.grass = createGrassTile();
    SPRITES.soilDry = createSoilDryTile();
    SPRITES.soilWet = createSoilWetTile();
    SPRITES.path = createPathTile();
    SPRITES.fence = createFenceTile();
    SPRITES.water = createWaterTile();
    SPRITES.shippingBin = createShippingBin();
    SPRITES.well = createWell();
    SPRITES.tree = createTree();
    SPRITES.treeStump = createTreeStump();
    SPRITES.sapling = createSapling();
    SPRITES.house = createHouse();
    SPRITES.barn = createBarn();
    SPRITES.shop = createShopBuilding();
    SPRITES.mill = createMill();
    SPRITES.hunterPost = createHunterPost();
    SPRITES.villageFountain = createVillageFountain();
    SPRITES.barricade = createBarricade();
    SPRITES.streetLamp = createStreetLamp();
    SPRITES.manor = createManor();
    SPRITES.apothecary = createApothecary();
    SPRITES.tavern = createTavern();
    SPRITES.villageForge = createVillageForge();

    SPRITES.player = createPlayerFrames();
    SPRITES.cow = createCowFrames();
    SPRITES.chicken = createChickenFrames();
    SPRITES.sheep = createSheepFrames();
    SPRITES.pig = createPigFrames();

    // Map each crop to sprite set
    SPRITES.crops = {
        wheat: createCropSpriteSet('#eab308', '#84cc16', 'wheat'),
        corn: createCropSpriteSet('#eab308', '#22c55e', 'corn'),
        rice: createCropSpriteSet('#e2e8f0', '#65a30d', 'wheat'),
        carrot: createCropSpriteSet('#f97316', '#16a34a', 'carrot'),
        tomato: createCropSpriteSet('#ef4444', '#15803d', 'round'),
        cabbage: createCropSpriteSet('#4ade80', '#166534', 'round'),
        chili: createCropSpriteSet('#dc2626', '#15803d', 'carrot'),
        strawberry: createCropSpriteSet('#f43f5e', '#16a34a', 'strawberry'),
        apple: createCropSpriteSet('#dc2626', '#15803d', 'round'),
        grape: createCropSpriteSet('#9333ea', '#15803d', 'round'),
        sunflower: createCropSpriteSet('#facc15', '#65a30d', 'round'),
        tulip: createCropSpriteSet('#ec4899', '#15803d', 'round'),
        rose: createCropSpriteSet('#b91c1c', '#15803d', 'round'),
        pumpkin: createCropSpriteSet('#ea580c', '#15803d', 'round'),
        potato: createCropSpriteSet('#a16207', '#15803d', 'round'),
        onion: createCropSpriteSet('#fbbf24', '#15803d', 'round'),
        garlic: createCropSpriteSet('#f1f5f9', '#15803d', 'round'),
        watermelon: createCropSpriteSet('#16a34a', '#14532d', 'round'),
        peach: createCropSpriteSet('#fb7185', '#15803d', 'round'),
        coconut: createCropSpriteSet('#78350f', '#15803d', 'round'),
        sugarcane: createCropSpriteSet('#84cc16', '#4d7c0f', 'wheat')
    };

    // Interior Tiles & Furniture
    SPRITES.floorWood = createFloorWood();
    SPRITES.wallHouse = createWallHouse();
    SPRITES.floorShop = createFloorShop();
    SPRITES.wallShop = createWallShop();
    SPRITES.doorMat = createDoorMat();

    SPRITES.bedStandard = createBed(false);
    SPRITES.bedDeluxe = createBed(true);
    SPRITES.wardrobe = createWardrobe();
    SPRITES.fireplace = createFireplace();
    SPRITES.refrigerator = createFridge();
    SPRITES.teaTable = createTeaTable();
    SPRITES.persianRug = createPersianRug();
    SPRITES.shopCounter = createShopCounter();
    SPRITES.displayShelf = createDisplayShelf();
    SPRITES.floorCarpet = createFloorCarpet();
    SPRITES.wallManor = createWallManor();
    SPRITES.wallForge = createWallForge();
    SPRITES.alchemyCauldron = createAlchemyCauldron();
    SPRITES.masterAnvil = createAnvilSprite();
    SPRITES.tavernTable = createTavernTable();
    SPRITES.herbShelf = createHerbShelf();
    SPRITES.flowerBed = createFlowerBed();
    SPRITES.berryBush = createBerryBush();
    SPRITES.hayBale = createHayBale();
    SPRITES.woodPile = createWoodPile();
    SPRITES.fishingDock = createFishingDock();
    SPRITES.treeApple = createFruitTree('apple');
    SPRITES.treeOrange = createFruitTree('orange');

    SPRITES.npcs = {
        uncle: createNPCFrames('uncle'),
        auntie: createNPCFrames('auntie'),
        girl: createNPCFrames('girl'),
        chef: createNPCFrames('chef'),
        boy: createNPCFrames('boy'),
        grandpa: createNPCFrames('grandpa'),
        merchant: createNPCFrames('merchant'),
        maid: createNPCFrames('maid')
    };

    SPRITES.bugs = {
        shadow_beetle: createDemonBugFrames('shadow_beetle'),
        demon_hornet: createDemonBugFrames('demon_hornet'),
        poison_larva: createDemonBugFrames('poison_larva')
    };

    SPRITES.hunters = {
        scout_hunter: createHunterFrames('scout_hunter'),
        veteran_marksman: createHunterFrames('veteran_marksman')
    };

    SPRITES.gardeners = {
        gardener_joy: createGardenerFrames('gardener_joy'),
        farmer_boy: createGardenerFrames('farmer_boy')
    };

    SPRITES.projectiles = {
        stone: createProjectileCanvas('stone'),
        rifle: createProjectileCanvas('rifle'),
        arrow: createProjectileCanvas('arrow'),
        acid: createProjectileCanvas('acid'),
        holy_beam: createProjectileCanvas('holy_beam'),
        dragon_fire: createProjectileCanvas('dragon_fire'),
        boss_flame: createProjectileCanvas('boss_flame'),
        spore_spiral: createProjectileCanvas('spore_spiral'),
        homing_spore: createProjectileCanvas('homing_spore'),
        meteor_blight: createProjectileCanvas('meteor_blight'),
        crystal_shard: createProjectileCanvas('crystal_shard'),
        poison_glob: createProjectileCanvas('poison_glob'),
        ice_shard: createProjectileCanvas('ice_shard'),
        shadow_skull: createProjectileCanvas('shadow_skull'),
        petal_blade: createProjectileCanvas('petal_blade'),
        lightning_arc: createProjectileCanvas('lightning_arc'),
        lightning_beam: createProjectileCanvas('lightning_beam'),
        void_scythe: createProjectileCanvas('void_scythe'),
        solar_beam: createProjectileCanvas('solar_beam'),
        ice_boulder: createProjectileCanvas('ice_boulder'),
        acid_deluge: createProjectileCanvas('acid_deluge')
    };

    // ==========================================
    //  OPEN WORLD RETRO PIXEL ART ASSETS
    // ==========================================
    function createDarkGrassTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#1e3a1e'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#142a14';
        ctx.fillRect(4, 6, 2, 4); ctx.fillRect(18, 12, 2, 4); ctx.fillRect(26, 22, 2, 4); ctx.fillRect(10, 24, 2, 4);
        ctx.fillStyle = '#2d5a27';
        ctx.fillRect(6, 4, 3, 2); ctx.fillRect(20, 10, 3, 2); ctx.fillRect(12, 22, 3, 2);
        ctx.fillStyle = '#a855f7'; ctx.fillRect(8, 14, 2, 2); ctx.fillRect(24, 8, 2, 2); // Mystic flora
        return canvas;
    }

    function createDarkStoneTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#1e293b'; ctx.fillRect(0, 0, 32, 32);
        ctx.strokeStyle = '#0f172a'; ctx.lineWidth = 1;
        ctx.strokeRect(1, 1, 14, 14); ctx.strokeRect(17, 1, 14, 14);
        ctx.strokeRect(1, 17, 14, 14); ctx.strokeRect(17, 17, 14, 14);
        ctx.fillStyle = '#334155'; ctx.fillRect(3, 3, 10, 3); ctx.fillRect(19, 3, 10, 3);
        ctx.fillStyle = '#065f46'; ctx.fillRect(14, 12, 3, 4); ctx.fillRect(16, 17, 3, 3); // Moss
        return canvas;
    }

    function createRuneTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#0f0a1c'; ctx.fillRect(0, 0, 32, 32);
        ctx.strokeStyle = '#3b0764'; ctx.lineWidth = 2;
        ctx.strokeRect(2, 2, 28, 28);
        ctx.strokeStyle = '#a855f7'; ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(16, 6); ctx.lineTo(26, 16); ctx.lineTo(16, 26); ctx.lineTo(6, 16); ctx.closePath();
        ctx.stroke();
        ctx.fillStyle = '#ef4444'; ctx.fillRect(15, 15, 2, 2);
        return canvas;
    }

    function createPillar() {
        const { canvas, ctx } = makeCanvas(32, 48);
        // Ancient Column
        ctx.fillStyle = '#0f172a'; ctx.fillRect(4, 6, 24, 40);
        ctx.fillStyle = '#334155'; ctx.fillRect(6, 8, 20, 36);
        ctx.fillStyle = '#64748b'; ctx.fillRect(8, 8, 4, 36);
        // Column head & base
        ctx.fillStyle = '#1e293b'; ctx.fillRect(2, 6, 28, 5); ctx.fillRect(2, 42, 28, 5);
        // Torches with fire
        ctx.fillStyle = '#78350f'; ctx.fillRect(14, 16, 4, 8);
        ctx.fillStyle = '#f97316'; ctx.beginPath(); ctx.arc(16, 14, 4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#fef08a'; ctx.beginPath(); ctx.arc(16, 13, 2, 0, Math.PI * 2); ctx.fill();
        return canvas;
    }

    function createCampfire() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Stone ring
        ctx.fillStyle = '#475569';
        for (let i = 0; i < 8; i++) {
            const angle = (i / 8) * Math.PI * 2;
            ctx.fillRect(16 + Math.cos(angle) * 11 - 2, 18 + Math.sin(angle) * 8 - 2, 5, 5);
        }
        // Logs
        ctx.fillStyle = '#78350f';
        ctx.fillRect(10, 18, 12, 4); ctx.fillRect(14, 15, 4, 10);
        // Glowing fire
        ctx.fillStyle = '#ea580c'; ctx.beginPath(); ctx.arc(16, 15, 7, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#facc15'; ctx.beginPath(); ctx.arc(16, 14, 4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(16, 13, 2, 0, Math.PI * 2); ctx.fill();
        return canvas;
    }

    function createRubyNode() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Rock base
        ctx.fillStyle = '#334155'; ctx.beginPath(); ctx.arc(16, 18, 12, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#1e293b'; ctx.fillRect(8, 20, 16, 8);
        // Embedded Ruby Crystals
        ctx.fillStyle = '#b91c1c';
        ctx.beginPath(); ctx.moveTo(14, 8); ctx.lineTo(20, 14); ctx.lineTo(16, 22); ctx.lineTo(10, 16); ctx.fill();
        ctx.fillStyle = '#ef4444';
        ctx.beginPath(); ctx.moveTo(15, 10); ctx.lineTo(19, 14); ctx.lineTo(16, 19); ctx.lineTo(12, 15); ctx.fill();
        ctx.fillStyle = '#ffffff'; ctx.fillRect(15, 11, 2, 2);
        // Small secondary crystal
        ctx.fillStyle = '#ef4444'; ctx.fillRect(20, 17, 4, 5); ctx.fillStyle = '#fecaca'; ctx.fillRect(21, 18, 2, 2);
        return canvas;
    }

    function createStarflower() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Stem and leaves
        ctx.fillStyle = '#16a34a'; ctx.fillRect(15, 16, 2, 12);
        ctx.fillRect(11, 21, 4, 2); ctx.fillRect(17, 23, 4, 2);
        // Star flower petals
        ctx.fillStyle = '#38bdf8';
        ctx.fillRect(14, 6, 4, 12); ctx.fillRect(10, 10, 12, 4);
        ctx.fillStyle = '#facc15'; ctx.beginPath(); ctx.arc(16, 12, 3, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#ffffff'; ctx.fillRect(15, 11, 2, 2);
        return canvas;
    }

    function createTreasureChest(opened = false) {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Chest base
        ctx.fillStyle = '#78350f'; ctx.fillRect(5, 14, 22, 14);
        ctx.fillStyle = '#451a03'; ctx.fillRect(5, 26, 22, 2);
        ctx.fillStyle = '#f59e0b'; ctx.fillRect(5, 14, 2, 14); ctx.fillRect(25, 14, 2, 14); ctx.fillRect(14, 14, 4, 14);

        if (!opened) {
            // Closed Lid
            ctx.fillStyle = '#92400e'; ctx.fillRect(4, 8, 24, 7);
            ctx.fillStyle = '#f59e0b'; ctx.fillRect(4, 8, 2, 7); ctx.fillRect(26, 8, 2, 7); ctx.fillRect(14, 8, 4, 7);
            // Keyhole / Lock
            ctx.fillStyle = '#fbbf24'; ctx.fillRect(14, 16, 4, 4);
            ctx.fillStyle = '#1e293b'; ctx.fillRect(15, 17, 2, 2);
        } else {
            // Open Lid tilted back
            ctx.fillStyle = '#451a03'; ctx.fillRect(4, 3, 24, 6);
            ctx.fillStyle = '#f59e0b'; ctx.fillRect(4, 3, 2, 6); ctx.fillRect(26, 3, 2, 6);
            // Sparkles inside
            ctx.fillStyle = '#fde047'; ctx.fillRect(8, 11, 16, 4);
            ctx.fillStyle = '#ffffff'; ctx.fillRect(12, 12, 3, 2); ctx.fillRect(18, 12, 2, 2);
        }
        return canvas;
    }

    function createBridgeTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Planks
        ctx.fillStyle = '#92400e'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#78350f';
        ctx.fillRect(0, 7, 32, 2); ctx.fillRect(0, 15, 32, 2); ctx.fillRect(0, 23, 32, 2); ctx.fillRect(0, 31, 32, 2);
        ctx.fillStyle = '#451a03';
        ctx.fillRect(0, 0, 32, 2); ctx.fillRect(0, 30, 32, 2);
        // Nails
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(4, 4, 2, 2); ctx.fillRect(26, 4, 2, 2);
        ctx.fillRect(4, 12, 2, 2); ctx.fillRect(26, 12, 2, 2);
        ctx.fillRect(4, 20, 2, 2); ctx.fillRect(26, 20, 2, 2);
        return canvas;
    }

    // Story NPCs Walking Frames (Valeria, Eldrin, Kael)
    function createStoryNPCFrames(type) {
        const directions = ['down', 'up', 'left', 'right'];
        const frames = {};
        directions.forEach(dir => {
            frames[dir] = [];
            [0, 1].forEach(f => {
                const { canvas, ctx } = makeCanvas(24, 32);
                const leg = (f === 1) ? 2 : 0;
                const bobY = (f === 1) ? 1 : 0;

                if (type === 'valeria') {
                    // อัศวินสาว วาเลเรีย (Silver Knight Valeria)
                    // Blonde hair with silver circlet
                    ctx.fillStyle = '#facc15'; ctx.fillRect(6, 2 + bobY, 12, 6);
                    ctx.fillStyle = '#e2e8f0'; ctx.fillRect(7, 3 + bobY, 10, 2); // Silver circlet
                    ctx.fillStyle = '#fed7aa'; ctx.fillRect(7, 7 + bobY, 10, 7); // Face
                    ctx.fillStyle = '#1e293b';
                    if (dir === 'down') { ctx.fillRect(9, 9 + bobY, 2, 2); ctx.fillRect(13, 9 + bobY, 2, 2); }
                    else if (dir === 'left') { ctx.fillRect(7, 9 + bobY, 2, 2); }
                    else if (dir === 'right') { ctx.fillRect(15, 9 + bobY, 2, 2); }
                    // Red Cape
                    ctx.fillStyle = '#dc2626'; ctx.fillRect(4, 14 + bobY, 16, 12);
                    // Silver Breastplate & Pauldrons
                    ctx.fillStyle = '#94a3b8'; ctx.fillRect(7, 14 + bobY, 10, 9);
                    ctx.fillStyle = '#e2e8f0'; ctx.fillRect(5, 13 + bobY, 4, 4); ctx.fillRect(15, 13 + bobY, 4, 4);
                    // Silver Sword
                    ctx.fillStyle = '#cbd5e1'; ctx.fillRect(19, 12 + bobY, 2, 12);
                    ctx.fillStyle = '#f59e0b'; ctx.fillRect(18, 16 + bobY, 4, 2);
                    // Legs / Greaves
                    ctx.fillStyle = '#64748b';
                    ctx.fillRect(7, 25 + leg, 4, 6); ctx.fillRect(13, 25 - leg, 4, 6);
                } else if (type === 'eldrin') {
                    // ผู้เฒ่าปราชญ์ เอลดริน (Sage Eldrin)
                    // Purple wizard hood
                    ctx.fillStyle = '#581c87'; ctx.fillRect(6, 1 + bobY, 12, 7);
                    ctx.fillStyle = '#a855f7'; ctx.fillRect(5, 6 + bobY, 14, 2);
                    // Face & Long white beard
                    ctx.fillStyle = '#fde047'; ctx.fillRect(8, 7 + bobY, 8, 4);
                    ctx.fillStyle = '#f8fafc'; ctx.fillRect(7, 10 + bobY, 10, 9); ctx.fillRect(9, 19 + bobY, 6, 3);
                    // Purple Starry Robe
                    ctx.fillStyle = '#3b0764'; ctx.fillRect(6, 15 + bobY, 12, 13);
                    ctx.fillStyle = '#fde047'; ctx.fillRect(9, 26 + bobY, 6, 2);
                    // Wooden Staff with Sapphire
                    ctx.fillStyle = '#78350f'; ctx.fillRect(19, 6 + bobY, 2, 22);
                    ctx.fillStyle = '#38bdf8'; ctx.beginPath(); ctx.arc(20, 5 + bobY, 3, 0, Math.PI * 2); ctx.fill();
                    ctx.fillStyle = '#ffffff'; ctx.fillRect(19, 4 + bobY, 2, 2);
                } else if (type === 'kael') {
                    // ช่างตีเหล็ก คาเอล (Blacksmith Kael)
                    // Dark Hair & Bandana
                    ctx.fillStyle = '#1e293b'; ctx.fillRect(6, 3 + bobY, 12, 5);
                    ctx.fillStyle = '#dc2626'; ctx.fillRect(6, 5 + bobY, 12, 2); // Red bandana
                    // Face & Stubble
                    ctx.fillStyle = '#fed7aa'; ctx.fillRect(7, 7 + bobY, 10, 7);
                    ctx.fillStyle = '#78350f'; ctx.fillRect(8, 12 + bobY, 8, 2);
                    // Leather Apron & Shirt
                    ctx.fillStyle = '#e2e8f0'; ctx.fillRect(6, 14 + bobY, 12, 5); // T-shirt
                    ctx.fillStyle = '#78350f'; ctx.fillRect(7, 16 + bobY, 10, 9); // Apron
                    // Sledgehammer
                    ctx.fillStyle = '#92400e'; ctx.fillRect(18, 16 + bobY, 2, 12);
                    ctx.fillStyle = '#475569'; ctx.fillRect(16, 14 + bobY, 6, 4);
                    // Pants & Boots
                    ctx.fillStyle = '#1e293b'; ctx.fillRect(7, 25 + leg, 4, 6); ctx.fillRect(13, 25 - leg, 4, 6);
                } else if (type === 'gilbert') {
                    // นายกเทศมนตรี กิลเบิร์ต (Mayor Gilbert)
                    // Silver-white hair
                    ctx.fillStyle = '#e2e8f0'; ctx.fillRect(6, 2 + bobY, 12, 5);
                    ctx.fillStyle = '#cbd5e1'; ctx.fillRect(5, 4 + bobY, 3, 4); ctx.fillRect(16, 4 + bobY, 3, 4);
                    // Face & Golden Monocle
                    ctx.fillStyle = '#fed7aa'; ctx.fillRect(7, 6 + bobY, 10, 7);
                    ctx.fillStyle = '#facc15'; ctx.strokeRect(12, 7 + bobY, 3, 3);
                    ctx.fillStyle = '#1e293b';
                    if (dir === 'down') { ctx.fillRect(9, 8 + bobY, 2, 2); ctx.fillRect(13, 8 + bobY, 1, 1); }
                    else if (dir === 'left') { ctx.fillRect(7, 8 + bobY, 2, 2); }
                    else if (dir === 'right') { ctx.fillRect(15, 8 + bobY, 2, 2); }
                    // Navy Blue Longcoat with Gold Trim
                    ctx.fillStyle = '#1e3a8a'; ctx.fillRect(6, 13 + bobY, 12, 11);
                    ctx.fillStyle = '#f59e0b'; ctx.fillRect(11, 13 + bobY, 2, 10);
                    // Formal Red Tie / Medallion
                    ctx.fillStyle = '#ef4444'; ctx.fillRect(11, 14 + bobY, 2, 3);
                    // Navy Pants & Polished Black Shoes
                    ctx.fillStyle = '#1e293b';
                    ctx.fillRect(7, 24 + leg, 4, 6); ctx.fillRect(13, 24 - leg, 4, 6);
                } else if (type === 'lilian') {
                    // หมอยาสาว ลิเลียน (Apothecary Lilian)
                    // Emerald green hair & white ribbon
                    ctx.fillStyle = '#15803d'; ctx.fillRect(6, 2 + bobY, 12, 6);
                    ctx.fillStyle = '#16a34a'; ctx.fillRect(4, 5 + bobY, 3, 8); ctx.fillRect(17, 5 + bobY, 3, 8);
                    ctx.fillStyle = '#f8fafc'; ctx.fillRect(8, 2 + bobY, 8, 2);
                    // Face & Kind Eyes
                    ctx.fillStyle = '#fed7aa'; ctx.fillRect(7, 6 + bobY, 10, 7);
                    ctx.fillStyle = '#065f46';
                    if (dir === 'down') { ctx.fillRect(8, 8 + bobY, 2, 2); ctx.fillRect(13, 8 + bobY, 2, 2); }
                    else if (dir === 'left') { ctx.fillRect(7, 8 + bobY, 2, 2); }
                    else if (dir === 'right') { ctx.fillRect(15, 8 + bobY, 2, 2); }
                    // White Apothecary Lab Coat over Teal Vest
                    ctx.fillStyle = '#f8fafc'; ctx.fillRect(6, 13 + bobY, 12, 11);
                    ctx.fillStyle = '#0f766e'; ctx.fillRect(10, 13 + bobY, 4, 7);
                    // Potion Flask on hip
                    ctx.fillStyle = '#06b6d4'; ctx.fillRect(18, 16 + bobY, 3, 5);
                    ctx.fillStyle = '#b45309'; ctx.fillRect(18, 14 + bobY, 3, 2);
                    // Teal Skirt & Boots
                    ctx.fillStyle = '#115e59'; ctx.fillRect(7, 23 + bobY, 10, 3);
                    ctx.fillStyle = '#78350f';
                    ctx.fillRect(8, 26 + leg, 3, 5); ctx.fillRect(13, 26 - leg, 3, 5);
                } else if (type === 'bob') {
                    // บ็อบ เจ้าของโรงเตี๊ยม (Barkeeper Bob)
                    // Brown hair & Classic Mustache
                    ctx.fillStyle = '#78350f'; ctx.fillRect(6, 2 + bobY, 12, 5);
                    ctx.fillStyle = '#fed7aa'; ctx.fillRect(7, 6 + bobY, 10, 7);
                    ctx.fillStyle = '#451a03'; ctx.fillRect(8, 10 + bobY, 8, 2);
                    ctx.fillStyle = '#1e293b';
                    if (dir === 'down') { ctx.fillRect(8, 7 + bobY, 2, 2); ctx.fillRect(13, 7 + bobY, 2, 2); }
                    else if (dir === 'left') { ctx.fillRect(7, 7 + bobY, 2, 2); }
                    else if (dir === 'right') { ctx.fillRect(15, 7 + bobY, 2, 2); }
                    // White shirt with Tavern Brown Apron
                    ctx.fillStyle = '#f8fafc'; ctx.fillRect(5, 13 + bobY, 14, 5);
                    ctx.fillStyle = '#b45309'; ctx.fillRect(7, 15 + bobY, 10, 10);
                    // Beer mug in hand
                    ctx.fillStyle = '#facc15'; ctx.fillRect(18, 15 + bobY, 4, 5);
                    ctx.fillStyle = '#ffffff'; ctx.fillRect(18, 13 + bobY, 4, 2);
                    // Brown Pants & Sturdy shoes
                    ctx.fillStyle = '#334155';
                    ctx.fillRect(7, 25 + leg, 4, 6); ctx.fillRect(13, 25 - leg, 4, 6);
                } else if (type === 'luna') {
                    // ลูน่า สาวน้อยร้านดอกไม้ (Florist Luna)
                    // Soft chestnut wavy hair & Daisy flower
                    ctx.fillStyle = '#9a3412'; ctx.fillRect(6, 2 + bobY, 12, 6);
                    ctx.fillStyle = '#b45309'; ctx.fillRect(4, 5 + bobY, 3, 9); ctx.fillRect(17, 5 + bobY, 3, 9);
                    ctx.fillStyle = '#ffffff'; ctx.fillRect(15, 3 + bobY, 3, 3); // Daisy
                    ctx.fillStyle = '#facc15'; ctx.fillRect(16, 4 + bobY, 1, 1);
                    // Gentle Face & Emerald eyes
                    ctx.fillStyle = '#fed7aa'; ctx.fillRect(7, 6 + bobY, 10, 7);
                    ctx.fillStyle = '#059669';
                    if (dir === 'down') { ctx.fillRect(8, 8 + bobY, 2, 2); ctx.fillRect(13, 8 + bobY, 2, 2); }
                    else if (dir === 'left') { ctx.fillRect(7, 8 + bobY, 2, 2); }
                    else if (dir === 'right') { ctx.fillRect(15, 8 + bobY, 2, 2); }
                    // Pink spring floral dress
                    ctx.fillStyle = '#fbcfe8'; ctx.fillRect(6, 13 + bobY, 12, 11);
                    ctx.fillStyle = '#ec4899'; ctx.fillRect(7, 15 + bobY, 10, 4);
                    // Flower basket in hand
                    ctx.fillStyle = '#b45309'; ctx.fillRect(18, 16 + bobY, 5, 4);
                    ctx.fillStyle = '#f43f5e'; ctx.fillRect(19, 14 + bobY, 3, 3);
                    // Cute shoes
                    ctx.fillStyle = '#db2777';
                    ctx.fillRect(8, 25 + leg, 3, 5); ctx.fillRect(13, 25 - leg, 3, 5);
                }
                frames[dir].push(canvas);
            });
        });
        return frames;
    }

    // 48x48 Dialogue Box Portraits
    function createPortrait(type) {
        const { canvas, ctx } = makeCanvas(48, 48);
        ctx.fillStyle = '#1e1b4b'; ctx.fillRect(0, 0, 48, 48);
        ctx.strokeStyle = '#f59e0b'; ctx.lineWidth = 2; ctx.strokeRect(1, 1, 46, 46);

        if (type === 'valeria') {
            // Golden hair
            ctx.fillStyle = '#eab308'; ctx.fillRect(12, 6, 24, 20);
            ctx.fillStyle = '#e2e8f0'; ctx.fillRect(14, 8, 20, 4); // Silver Diadem
            ctx.fillStyle = '#ef4444'; ctx.fillRect(23, 9, 2, 2); // Ruby gem
            // Face
            ctx.fillStyle = '#fed7aa'; ctx.fillRect(14, 12, 20, 18);
            // Determined Blue Eyes
            ctx.fillStyle = '#0284c7'; ctx.fillRect(17, 18, 4, 4); ctx.fillRect(27, 18, 4, 4);
            ctx.fillStyle = '#ffffff'; ctx.fillRect(18, 18, 2, 2); ctx.fillRect(28, 18, 2, 2);
            // Smile
            ctx.fillStyle = '#f43f5e'; ctx.fillRect(22, 26, 4, 2);
            // Silver Armor & Red Cloak
            ctx.fillStyle = '#dc2626'; ctx.fillRect(6, 32, 36, 14);
            ctx.fillStyle = '#94a3b8'; ctx.fillRect(14, 30, 20, 16);
            ctx.fillStyle = '#f1f5f9'; ctx.fillRect(10, 32, 6, 10); ctx.fillRect(32, 32, 6, 10);
        } else if (type === 'eldrin') {
            // Purple Sage Hood
            ctx.fillStyle = '#4c1d95'; ctx.fillRect(10, 4, 28, 18);
            ctx.fillStyle = '#a855f7'; ctx.fillRect(8, 14, 32, 4);
            // Wise Face
            ctx.fillStyle = '#fed7aa'; ctx.fillRect(14, 14, 20, 12);
            // Glowing Sapphire Eyes
            ctx.fillStyle = '#38bdf8'; ctx.fillRect(17, 18, 4, 3); ctx.fillRect(27, 18, 4, 3);
            // Grand White Beard
            ctx.fillStyle = '#f8fafc'; ctx.fillRect(12, 24, 24, 18); ctx.fillRect(16, 40, 16, 6);
            ctx.fillStyle = '#cbd5e1'; ctx.fillRect(14, 28, 4, 12); ctx.fillRect(30, 28, 4, 12);
        } else if (type === 'kael') {
            // Dark messy hair & red headband
            ctx.fillStyle = '#0f172a'; ctx.fillRect(12, 6, 24, 12);
            ctx.fillStyle = '#dc2626'; ctx.fillRect(12, 12, 24, 4);
            // Rugged Face
            ctx.fillStyle = '#fed7aa'; ctx.fillRect(14, 14, 20, 20);
            ctx.fillStyle = '#1e293b'; ctx.fillRect(17, 19, 3, 3); ctx.fillRect(28, 19, 3, 3); // Eyes
            ctx.fillStyle = '#78350f'; ctx.fillRect(15, 26, 18, 6); // Stubble beard
            ctx.fillStyle = '#451a03'; ctx.fillRect(21, 28, 6, 2); // Mouth
            // Apron & Muscles
            ctx.fillStyle = '#9a3412'; ctx.fillRect(10, 34, 28, 12);
            ctx.fillStyle = '#78350f'; ctx.fillRect(16, 36, 16, 10);
        } else if (type === 'kathuros') {
            // Mega Boss Kathuros Portrait
            ctx.fillStyle = '#1a0505'; ctx.fillRect(0, 0, 48, 48);
            // Massive Horns
            ctx.fillStyle = '#450a0a';
            ctx.fillRect(6, 4, 8, 14); ctx.fillRect(34, 4, 8, 14);
            ctx.fillStyle = '#dc2626'; ctx.fillRect(4, 2, 4, 4); ctx.fillRect(40, 2, 4, 4); // Horn tips
            // Demonic Face
            ctx.fillStyle = '#262626'; ctx.fillRect(12, 14, 24, 24);
            // Glowing Hellfire Eyes
            ctx.fillStyle = '#ff0000'; ctx.fillRect(16, 20, 6, 5); ctx.fillRect(26, 20, 6, 5);
            ctx.fillStyle = '#ffff00'; ctx.fillRect(18, 22, 2, 2); ctx.fillRect(28, 22, 2, 2);
            // Demonic Jaws with Fangs
            ctx.fillStyle = '#000000'; ctx.fillRect(16, 30, 16, 6);
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(17, 30, 2, 3); ctx.fillRect(21, 30, 2, 3); ctx.fillRect(25, 30, 2, 3); ctx.fillRect(29, 30, 2, 3);
            ctx.fillRect(19, 33, 2, 3); ctx.fillRect(23, 33, 2, 3); ctx.fillRect(27, 33, 2, 3);
            // Burning Rune Chest
            ctx.fillStyle = '#ef4444'; ctx.fillRect(22, 40, 4, 6); ctx.fillRect(18, 42, 12, 2);
        } else if (type === 'gilbert') {
            // Mayor Gilbert Portrait
            // Silver-white hair
            ctx.fillStyle = '#e2e8f0'; ctx.fillRect(10, 6, 28, 16);
            ctx.fillStyle = '#f8fafc'; ctx.fillRect(12, 8, 24, 6);
            // Dignified Face
            ctx.fillStyle = '#fed7aa'; ctx.fillRect(14, 14, 20, 18);
            // Monocle on right eye
            ctx.fillStyle = '#facc15'; ctx.lineWidth = 2; ctx.strokeRect(26, 18, 7, 7);
            ctx.fillStyle = '#38bdf8'; ctx.fillRect(27, 19, 5, 5);
            ctx.fillStyle = '#1e293b'; ctx.fillRect(17, 20, 3, 3); ctx.fillRect(28, 20, 3, 3);
            // Silver Moustache & Kind Smile
            ctx.fillStyle = '#cbd5e1'; ctx.fillRect(17, 26, 14, 3);
            ctx.fillStyle = '#e11d48'; ctx.fillRect(22, 29, 4, 2);
            // Mayor Formal Suit & Gold Chain
            ctx.fillStyle = '#1e3a8a'; ctx.fillRect(8, 32, 32, 14);
            ctx.fillStyle = '#f59e0b'; ctx.fillRect(14, 34, 20, 3);
            ctx.fillStyle = '#ef4444'; ctx.fillRect(22, 36, 4, 6);
            ctx.fillStyle = '#ffffff'; ctx.fillRect(19, 32, 10, 4);
        } else if (type === 'lilian') {
            // Apothecary Lilian Portrait
            // Emerald hair
            ctx.fillStyle = '#15803d'; ctx.fillRect(10, 5, 28, 20);
            ctx.fillStyle = '#16a34a'; ctx.fillRect(8, 14, 6, 16); ctx.fillRect(34, 14, 6, 16);
            ctx.fillStyle = '#ffffff'; ctx.fillRect(14, 6, 20, 3);
            ctx.fillStyle = '#22c55e'; ctx.fillRect(22, 5, 4, 5);
            // Kind Face
            ctx.fillStyle = '#fed7aa'; ctx.fillRect(14, 12, 20, 18);
            // Emerald Eyes
            ctx.fillStyle = '#0d9488'; ctx.fillRect(17, 17, 4, 4); ctx.fillRect(27, 17, 4, 4);
            ctx.fillStyle = '#ffffff'; ctx.fillRect(18, 17, 2, 2); ctx.fillRect(28, 17, 2, 2);
            // Gentle Smile & Rosy Cheeks
            ctx.fillStyle = '#f43f5e'; ctx.fillRect(22, 26, 4, 2);
            ctx.fillStyle = '#fecdd3'; ctx.fillRect(14, 22, 4, 2); ctx.fillRect(30, 22, 4, 2);
            // White Doctor/Lab Coat
            ctx.fillStyle = '#f8fafc'; ctx.fillRect(8, 30, 32, 16);
            ctx.fillStyle = '#0f766e'; ctx.fillRect(18, 32, 12, 14);
            // Herbal Flask Pendant
            ctx.fillStyle = '#06b6d4'; ctx.beginPath(); ctx.arc(24, 38, 4, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#ffffff'; ctx.fillRect(23, 37, 2, 2);
        } else if (type === 'bob') {
            // Barkeeper Bob Portrait
            // Brown hair
            ctx.fillStyle = '#78350f'; ctx.fillRect(12, 6, 24, 14);
            // Friendly Face
            ctx.fillStyle = '#fed7aa'; ctx.fillRect(14, 14, 20, 18);
            // Friendly Eyes
            ctx.fillStyle = '#1e293b'; ctx.fillRect(17, 18, 3, 3); ctx.fillRect(28, 18, 3, 3);
            // Cheerful Red Cheeks
            ctx.fillStyle = '#fca5a5'; ctx.fillRect(14, 22, 4, 2); ctx.fillRect(30, 22, 4, 2);
            // Classic Handlebar Moustache
            ctx.fillStyle = '#451a03'; ctx.fillRect(16, 24, 16, 4);
            ctx.fillRect(14, 26, 4, 2); ctx.fillRect(30, 26, 4, 2);
            // Smile
            ctx.fillStyle = '#dc2626'; ctx.fillRect(22, 28, 4, 2);
            // Tavern Shirt & Brown Leather Apron
            ctx.fillStyle = '#f8fafc'; ctx.fillRect(10, 32, 28, 6);
            ctx.fillStyle = '#b45309'; ctx.fillRect(12, 34, 24, 12);
            ctx.fillStyle = '#f59e0b'; ctx.fillRect(14, 38, 4, 8);
            ctx.fillStyle = '#f59e0b'; ctx.fillRect(30, 38, 4, 8);
        } else if (type === 'luna') {
            // Luna - Flower Maiden Portrait
            // Soft chestnut wavy hair with flowers
            ctx.fillStyle = '#9a3412'; ctx.fillRect(10, 5, 28, 22);
            ctx.fillStyle = '#b45309'; ctx.fillRect(8, 14, 6, 16); ctx.fillRect(34, 14, 6, 16);
            // Daisy Hairpin
            ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(33, 9, 4, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#facc15'; ctx.beginPath(); ctx.arc(33, 9, 2, 0, Math.PI * 2); ctx.fill();
            // Gentle Sweet Face
            ctx.fillStyle = '#fed7aa'; ctx.fillRect(14, 12, 20, 18);
            // Sparkling Emerald Green Eyes
            ctx.fillStyle = '#059669'; ctx.fillRect(17, 17, 4, 4); ctx.fillRect(27, 17, 4, 4);
            ctx.fillStyle = '#ffffff'; ctx.fillRect(18, 17, 2, 2); ctx.fillRect(28, 17, 2, 2);
            // Rosy Pink Cheeks & Shy Sweet Smile
            ctx.fillStyle = '#f472b6'; ctx.fillRect(15, 22, 4, 2); ctx.fillRect(29, 22, 4, 2);
            ctx.fillStyle = '#f43f5e'; ctx.fillRect(22, 25, 4, 2);
            // Floral Spring Dress & Emerald Pendant
            ctx.fillStyle = '#fbcfe8'; ctx.fillRect(10, 31, 28, 15);
            ctx.fillStyle = '#ec4899'; ctx.fillRect(14, 33, 20, 4);
            ctx.fillStyle = '#10b981'; ctx.beginPath(); ctx.arc(24, 37, 3, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#ffffff'; ctx.fillRect(23, 36, 2, 2);
        }
        return canvas;
    }

    // World Monsters (Shadow Wolf, Goblin, Treant)
    function createWorldMonsterFrames(type) {
        const frames = [];
        [0, 1].forEach(f => {
            if (type === 'shadow_wolf') {
                const { canvas, ctx } = makeCanvas(32, 24);
                const leg = (f === 1) ? 2 : 0;
                // Dark Wolf Body
                ctx.fillStyle = '#1e1b4b'; ctx.fillRect(6, 7, 20, 10);
                // Head & Snout
                ctx.fillStyle = '#312e81'; ctx.fillRect(20, 4, 9, 8); ctx.fillRect(26, 8, 4, 4);
                // Ears
                ctx.fillStyle = '#1e1b4b'; ctx.fillRect(21, 1, 3, 4); ctx.fillRect(25, 2, 3, 3);
                // Glowing Red Eye & Fangs
                ctx.fillStyle = '#ef4444'; ctx.fillRect(24, 6, 2, 2);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(27, 10, 2, 2);
                // Bushy Tail
                ctx.fillStyle = '#4338ca'; ctx.fillRect(2, 6, 5, 6);
                // 4 Legs
                ctx.fillStyle = '#1e1b4b';
                ctx.fillRect(8, 16 + leg, 3, 6); ctx.fillRect(12, 16 - leg, 3, 6);
                ctx.fillRect(18, 16 - leg, 3, 6); ctx.fillRect(22, 16 + leg, 3, 6);
                frames.push(canvas);
            } else if (type === 'goblin_scout') {
                const { canvas, ctx } = makeCanvas(24, 28);
                const leg = (f === 1) ? 2 : 0;
                // Green Goblin Head with Pointy Ears
                ctx.fillStyle = '#16a34a'; ctx.fillRect(7, 4, 10, 8);
                ctx.fillRect(3, 5, 5, 3); ctx.fillRect(16, 5, 5, 3); // Ears
                // Red Piercing Eyes
                ctx.fillStyle = '#ef4444'; ctx.fillRect(9, 7, 2, 2); ctx.fillRect(13, 7, 2, 2);
                // Brown Leather Vest & Ragged Pants
                ctx.fillStyle = '#78350f'; ctx.fillRect(6, 12, 12, 8);
                ctx.fillStyle = '#451a03'; ctx.fillRect(7, 19, 10, 4);
                // Slingshot / Club
                ctx.fillStyle = '#a16207'; ctx.fillRect(17, 10, 3, 10);
                // Feet
                ctx.fillStyle = '#15803d'; ctx.fillRect(7, 23 + leg, 4, 4); ctx.fillRect(13, 23 - leg, 4, 4);
                frames.push(canvas);
            } else if (type === 'demon_treant') {
                const { canvas, ctx } = makeCanvas(36, 44);
                const bob = (f === 1) ? 2 : 0;
                // Dark Haunted Trunk
                ctx.fillStyle = '#1c1917'; ctx.fillRect(8, 10 + bob, 20, 26);
                ctx.fillStyle = '#292524'; ctx.fillRect(10, 12 + bob, 16, 22);
                // Twisted Branch Arms
                ctx.fillStyle = '#1c1917';
                ctx.fillRect(1, 14 + bob, 8, 4); ctx.fillRect(1, 10 + bob, 4, 8);
                ctx.fillRect(27, 14 + bob, 8, 4); ctx.fillRect(31, 10 + bob, 4, 8);
                // Glowing Hollow Eyes & Mouth
                ctx.fillStyle = '#dc2626';
                ctx.fillRect(12, 16 + bob, 3, 4); ctx.fillRect(21, 16 + bob, 3, 4);
                ctx.fillRect(14, 24 + bob, 8, 4);
                // Gnarled Roots / Legs
                ctx.fillStyle = '#0c0a09';
                ctx.fillRect(8, 35, 6, 8); ctx.fillRect(22, 35, 6, 8); ctx.fillRect(15, 36, 6, 7);
                frames.push(canvas);
            } else if (type === 'cave_bat') {
                const { canvas, ctx } = makeCanvas(28, 22);
                const wingY = (f === 1) ? 4 : -2;
                // Purple Bat Body
                ctx.fillStyle = '#311042'; ctx.fillRect(10, 8, 8, 8);
                // Large Flapping Wings
                ctx.fillStyle = '#1e082b';
                ctx.beginPath();
                ctx.moveTo(10, 10); ctx.lineTo(1, 2 + wingY); ctx.lineTo(4, 16 + wingY); ctx.lineTo(10, 14); ctx.fill();
                ctx.beginPath();
                ctx.moveTo(18, 10); ctx.lineTo(27, 2 + wingY); ctx.lineTo(24, 16 + wingY); ctx.lineTo(18, 14); ctx.fill();
                // Glowing Eyes & Fangs
                ctx.fillStyle = '#ef4444'; ctx.fillRect(12, 10, 2, 2); ctx.fillRect(15, 10, 2, 2);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(13, 14, 1, 2); ctx.fillRect(15, 14, 1, 2);
                frames.push(canvas);
            } else if (type === 'crystal_slime') {
                const { canvas, ctx } = makeCanvas(28, 26);
                const squish = (f === 1) ? 2 : 0;
                // Translucent Cyan Slime Body
                ctx.fillStyle = 'rgba(6, 182, 212, 0.85)';
                ctx.beginPath();
                ctx.ellipse(14, 15 + squish / 2, 12 + squish, 9 - squish, 0, 0, Math.PI * 2);
                ctx.fill();
                // Inner Glowing Core
                ctx.fillStyle = '#67e8f9';
                ctx.beginPath();
                ctx.ellipse(14, 15 + squish / 2, 7, 5, 0, 0, Math.PI * 2);
                ctx.fill();
                // Sharp Crystal Shards on Top
                ctx.fillStyle = '#38bdf8';
                ctx.beginPath();
                ctx.moveTo(14, 4); ctx.lineTo(11, 12); ctx.lineTo(17, 12); ctx.fill();
                ctx.moveTo(8, 8); ctx.lineTo(6, 14); ctx.lineTo(11, 14); ctx.fill();
                ctx.moveTo(20, 8); ctx.lineTo(17, 14); ctx.lineTo(22, 14); ctx.fill();
                // Cute Slime Eyes
                ctx.fillStyle = '#083344'; ctx.fillRect(11, 13, 2, 3); ctx.fillRect(16, 13, 2, 3);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(11, 13, 1, 1); ctx.fillRect(16, 13, 1, 1);
                frames.push(canvas);
            } else if (type === 'swamp_croc') {
                const { canvas, ctx } = makeCanvas(32, 22);
                const leg = (f === 1) ? 2 : 0;
                // Dark Swamp Green Scaly Croc Body
                ctx.fillStyle = '#14532d'; ctx.fillRect(6, 8, 20, 8);
                // Jagged Mossy Ridge on Back
                ctx.fillStyle = '#166534'; ctx.fillRect(8, 6, 4, 3); ctx.fillRect(14, 6, 4, 3); ctx.fillRect(20, 6, 4, 3);
                // Long Croc Snout
                ctx.fillStyle = '#14532d'; ctx.fillRect(22, 10, 8, 5);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(24, 15, 2, 2); ctx.fillRect(28, 15, 2, 2); // Sharp Teeth
                // Menacing Reptile Eye
                ctx.fillStyle = '#facc15'; ctx.fillRect(22, 8, 2, 2);
                ctx.fillStyle = '#000000'; ctx.fillRect(23, 8, 1, 2);
                // Webbed Feet
                ctx.fillStyle = '#052e16';
                ctx.fillRect(8, 16 + leg, 4, 4); ctx.fillRect(18, 16 - leg, 4, 4);
                // Spiky Tail
                ctx.fillStyle = '#166534'; ctx.fillRect(2, 9, 5, 5);
                frames.push(canvas);
            } else if (type === 'crystal_spider') {
                const { canvas, ctx } = makeCanvas(28, 24);
                const leg = (f === 1) ? 2 : 0;
                // Deep Purple Body
                ctx.fillStyle = '#3b0764'; ctx.fillRect(8, 8, 12, 10);
                // Glowing Cyan Prismatic Cluster on Back
                ctx.fillStyle = '#06b6d4';
                ctx.beginPath(); ctx.moveTo(14, 4); ctx.lineTo(10, 10); ctx.lineTo(18, 10); ctx.fill();
                ctx.fillStyle = '#67e8f9';
                ctx.fillRect(13, 6, 2, 4);
                // Glowing Red Eyes
                ctx.fillStyle = '#ef4444';
                ctx.fillRect(9, 13, 2, 2); ctx.fillRect(12, 13, 2, 2); ctx.fillRect(15, 13, 2, 2); ctx.fillRect(18, 13, 2, 2);
                // Spindly Crystal Legs
                ctx.strokeStyle = '#0891b2'; ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(8, 10); ctx.lineTo(2, 6 + leg); ctx.lineTo(1, 18);
                ctx.moveTo(20, 10); ctx.lineTo(26, 6 + leg); ctx.lineTo(27, 18);
                ctx.moveTo(8, 14); ctx.lineTo(3, 14 - leg); ctx.lineTo(2, 22);
                ctx.moveTo(20, 14); ctx.lineTo(25, 14 - leg); ctx.lineTo(26, 22);
                ctx.stroke();
                frames.push(canvas);
            } else if (type === 'magma_elemental') {
                const { canvas, ctx } = makeCanvas(28, 30);
                const bob = (f === 1) ? 2 : 0;
                // Obsidian Stone Torso
                ctx.fillStyle = '#18181b'; ctx.fillRect(7, 8 + bob, 14, 14);
                // Burning Molten Lava Core
                ctx.fillStyle = '#ea580c'; ctx.fillRect(9, 10 + bob, 10, 8);
                ctx.fillStyle = '#fde047'; ctx.fillRect(11, 12 + bob, 6, 4);
                // Stone Brow & Fiery Eyes
                ctx.fillStyle = '#09090b'; ctx.fillRect(6, 4 + bob, 16, 5);
                ctx.fillStyle = '#f97316'; ctx.fillRect(9, 6 + bob, 3, 2); ctx.fillRect(16, 6 + bob, 3, 2);
                // Floating Lava Stone Fists
                ctx.fillStyle = '#27272a';
                ctx.fillRect(2, 12 + bob, 4, 6); ctx.fillRect(22, 12 - bob, 4, 6);
                ctx.fillStyle = '#f97316';
                ctx.fillRect(3, 14 + bob, 2, 2); ctx.fillRect(23, 14 - bob, 2, 2);
                // Molten Base
                ctx.fillStyle = '#c2410c'; ctx.fillRect(8, 22 + bob, 12, 5);
                ctx.fillStyle = '#ef4444'; ctx.fillRect(10, 24 + bob, 8, 3);
                frames.push(canvas);
            } else if (type === 'frost_wolf') {
                const { canvas, ctx } = makeCanvas(32, 24);
                const leg = (f === 1) ? 2 : 0;
                // Pure Snow White Fur Body
                ctx.fillStyle = '#f8fafc'; ctx.fillRect(6, 7, 20, 10);
                ctx.fillStyle = '#bae6fd'; ctx.fillRect(8, 13, 16, 4); // Cyan icy shadow
                // Head & Snout
                ctx.fillStyle = '#f1f5f9'; ctx.fillRect(20, 4, 9, 8); ctx.fillRect(26, 8, 4, 4);
                // Ears
                ctx.fillStyle = '#e2e8f0'; ctx.fillRect(21, 1, 3, 4); ctx.fillRect(25, 2, 3, 3);
                // Glowing Glacier Eyes
                ctx.fillStyle = '#0284c7'; ctx.fillRect(24, 6, 2, 2);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(27, 10, 2, 2);
                // Bushy White Tail
                ctx.fillStyle = '#f8fafc'; ctx.fillRect(2, 6, 5, 6);
                // 4 Running Paws
                ctx.fillStyle = '#e2e8f0';
                ctx.fillRect(8, 16 + leg, 3, 6); ctx.fillRect(12, 16 - leg, 3, 6);
                ctx.fillRect(18, 16 - leg, 3, 6); ctx.fillRect(22, 16 + leg, 3, 6);
                frames.push(canvas);
            } else if (type === 'skeleton_warrior') {
                const { canvas, ctx } = makeCanvas(24, 30);
                const leg = (f === 1) ? 2 : 0;
                // Weathered Skull
                ctx.fillStyle = '#e2e8f0'; ctx.fillRect(8, 4, 8, 8);
                // Iron Helmet
                ctx.fillStyle = '#475569'; ctx.fillRect(7, 2, 10, 4); ctx.fillRect(11, 0, 2, 2);
                // Glowing Crimson Eye Sockets
                ctx.fillStyle = '#dc2626'; ctx.fillRect(9, 7, 2, 2); ctx.fillRect(13, 7, 2, 2);
                // Bony Ribcage
                ctx.fillStyle = '#cbd5e1'; ctx.fillRect(9, 12, 6, 8);
                ctx.fillStyle = '#1e293b'; ctx.fillRect(10, 14, 4, 2); ctx.fillRect(10, 17, 4, 2);
                // Wooden Shield on Left
                ctx.fillStyle = '#78350f'; ctx.fillRect(2, 11, 4, 9);
                ctx.fillStyle = '#94a3b8'; ctx.strokeRect(2, 11, 4, 9);
                // Rusted Iron Sword on Right
                ctx.fillStyle = '#94a3b8'; ctx.fillRect(18, 8, 3, 14);
                ctx.fillStyle = '#b45309'; ctx.fillRect(17, 17, 5, 2);
                // Bony Legs
                ctx.fillStyle = '#e2e8f0';
                ctx.fillRect(8, 20 + leg, 2, 8); ctx.fillRect(14, 20 - leg, 2, 8);
                frames.push(canvas);
            } else if (type === 'spire_demon') {
                const { canvas, ctx } = makeCanvas(28, 30);
                const bob = (f === 1) ? 2 : 0;
                // Ethereal Dimensional Spire Demon
                ctx.fillStyle = '#0f172a'; ctx.fillRect(8, 6 + bob, 12, 14);
                ctx.fillStyle = '#06b6d4'; ctx.fillRect(9, 7 + bob, 10, 12);
                // Glowing Prismatic Core
                ctx.fillStyle = '#a855f7'; ctx.fillRect(11, 10 + bob, 6, 6);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(13, 12 + bob, 2, 2);
                // Crystal Horns
                ctx.fillStyle = '#38bdf8';
                ctx.fillRect(7, 2 + bob, 3, 5); ctx.fillRect(18, 2 + bob, 3, 5);
                // Floating Crystal Shards
                ctx.fillStyle = '#fde047';
                ctx.fillRect(3, 12 - bob, 3, 6); ctx.fillRect(22, 14 + bob, 3, 6);
                // Shadowy trailing base
                ctx.fillStyle = 'rgba(6, 182, 212, 0.4)';
                ctx.fillRect(10, 21 + bob, 8, 4);
                frames.push(canvas);
            } else if (type === 'spire_colossus') {
                const { canvas, ctx } = makeCanvas(36, 38);
                const stomp = (f === 1) ? 2 : 0;
                // Towering Ancient Spire Colossus
                ctx.fillStyle = '#3b0764'; ctx.fillRect(6, 6, 24, 22);
                ctx.fillStyle = '#6b21a8'; ctx.fillRect(8, 8, 20, 18);
                // Gold Trim
                ctx.fillStyle = '#eab308';
                ctx.fillRect(6, 6, 24, 3); ctx.fillRect(6, 25, 24, 3);
                // Glowing Runes
                ctx.fillStyle = '#f43f5e';
                ctx.fillRect(12, 14, 12, 4); ctx.fillRect(16, 11, 4, 10);
                // Glowing Eyes
                ctx.fillStyle = '#38bdf8';
                ctx.fillRect(11, 10, 3, 3); ctx.fillRect(22, 10, 3, 3);
                // Heavy Stone Legs
                ctx.fillStyle = '#1e1b4b';
                ctx.fillRect(8, 28 + stomp, 7, 8); ctx.fillRect(21, 28 - stomp, 7, 8);
                frames.push(canvas);
            } else if (type === 'island_crab') {
                const { canvas, ctx } = makeCanvas(32, 24);
                const step = (f === 1) ? 2 : 0;
                // Heavy Stone Shell
                ctx.fillStyle = '#64748b'; ctx.beginPath(); ctx.ellipse(16, 12, 11, 8, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#475569'; ctx.beginPath(); ctx.ellipse(16, 12, 9, 6, 0, 0, Math.PI * 2); ctx.fill();
                // Shell Ridge Dots
                ctx.fillStyle = '#94a3b8'; ctx.fillRect(12, 9, 3, 3); ctx.fillRect(17, 9, 3, 3); ctx.fillRect(14, 14, 4, 3);
                // Beady Black Eyes on Stalks
                ctx.fillStyle = '#0f172a'; ctx.fillRect(12, 3, 2, 3); ctx.fillRect(18, 3, 2, 3);
                ctx.fillStyle = '#ffffff'; ctx.fillRect(12, 2, 2, 2); ctx.fillRect(18, 2, 2, 2);
                // Big Red/Orange Claws
                ctx.fillStyle = '#ea580c';
                ctx.fillRect(2, 6 - step, 6, 5); ctx.fillRect(24, 6 + step, 6, 5);
                ctx.fillStyle = '#f97316';
                ctx.fillRect(1, 4 - step, 3, 4); ctx.fillRect(28, 4 + step, 3, 4);
                // Little Crab Legs
                ctx.fillStyle = '#475569';
                ctx.fillRect(7, 18 + step, 3, 5); ctx.fillRect(12, 18 - step, 3, 5);
                ctx.fillRect(17, 18 + step, 3, 5); ctx.fillRect(22, 18 - step, 3, 5);
                frames.push(canvas);
            } else if (type === 'cursed_pirate_skeleton') {
                const { canvas, ctx } = makeCanvas(26, 32);
                const leg = (f === 1) ? 2 : 0;
                // Pirate Red Bandana
                ctx.fillStyle = '#dc2626'; ctx.fillRect(7, 2, 12, 5); ctx.fillRect(17, 4, 4, 6);
                // Bone Skull
                ctx.fillStyle = '#f1f5f9'; ctx.fillRect(8, 6, 10, 8);
                // Pirate Eye Patch on Right Eye
                ctx.fillStyle = '#0f172a'; ctx.fillRect(13, 8, 3, 3); ctx.fillRect(7, 6, 12, 1);
                // Glowing Cursed Green Left Eye
                ctx.fillStyle = '#22c55e'; ctx.fillRect(9, 8, 2, 2);
                // Jaw & Teeth
                ctx.fillStyle = '#e2e8f0'; ctx.fillRect(9, 12, 8, 3);
                ctx.fillStyle = '#0f172a'; ctx.fillRect(11, 13, 1, 2); ctx.fillRect(13, 13, 1, 2); ctx.fillRect(15, 13, 1, 2);
                // Ribcage & Blue Naval Vest
                ctx.fillStyle = '#1e3a8a'; ctx.fillRect(6, 15, 14, 8);
                ctx.fillStyle = '#f8fafc'; ctx.fillRect(10, 16, 6, 6);
                // Steel Pirate Cutlass Sword in Hand
                ctx.fillStyle = '#94a3b8';
                ctx.fillRect(19, 10 - leg, 2, 12); ctx.fillRect(18, 9 - leg, 4, 2);
                ctx.fillStyle = '#facc15'; ctx.fillRect(18, 18 - leg, 4, 3);
                // Skeletal Legs & Worn Pirate Boots
                ctx.fillStyle = '#e2e8f0'; ctx.fillRect(9, 23 + leg, 3, 5); ctx.fillRect(14, 23 - leg, 3, 5);
                ctx.fillStyle = '#78350f'; ctx.fillRect(8, 27 + leg, 4, 4); ctx.fillRect(14, 27 - leg, 4, 4);
                frames.push(canvas);
            } else if (type === 'magma_sprite') {
                const { canvas, ctx } = makeCanvas(26, 26);
                const floatY = (f === 1) ? 2 : 0;
                // Outer Magma Aura
                ctx.fillStyle = 'rgba(239, 68, 68, 0.4)';
                ctx.beginPath(); ctx.arc(13, 13 + floatY, 11, 0, Math.PI * 2); ctx.fill();
                // Fiery Core
                ctx.fillStyle = '#ea580c';
                ctx.beginPath(); ctx.arc(13, 13 + floatY, 8, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#facc15';
                ctx.beginPath(); ctx.arc(13, 12 + floatY, 5, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ffffff';
                ctx.beginPath(); ctx.arc(13, 11 + floatY, 2.5, 0, Math.PI * 2); ctx.fill();
                // Fiery Ember Horns / Wisps
                ctx.fillStyle = '#dc2626';
                ctx.fillRect(8, 4 + floatY, 3, 4); ctx.fillRect(15, 4 + floatY, 3, 4);
                ctx.fillStyle = '#f97316';
                ctx.fillRect(9, 2 + floatY, 2, 3); ctx.fillRect(15, 2 + floatY, 2, 3);
                // Glowing Eyes
                ctx.fillStyle = '#450a0a';
                ctx.fillRect(10, 12 + floatY, 2, 3); ctx.fillRect(15, 12 + floatY, 2, 3);
                frames.push(canvas);
            } else if (type === 'magma_duggy') {
                const { canvas, ctx } = makeCanvas(28, 28);
                const bob = (f === 1) ? 2 : 0;
                // Obsidian Burrow Hole with Magma Glow
                ctx.fillStyle = '#18181b';
                ctx.beginPath(); ctx.ellipse(14, 22, 12, 5, 0, 0, Math.PI * 2); ctx.fill();
                ctx.fillStyle = '#ea580c';
                ctx.beginPath(); ctx.ellipse(14, 21, 9, 3, 0, 0, Math.PI * 2); ctx.fill();
                // Spiky Magma Worm Head
                ctx.fillStyle = '#dc2626';
                ctx.fillRect(8, 8 + bob, 12, 12);
                ctx.fillStyle = '#f97316';
                ctx.fillRect(9, 9 + bob, 10, 10);
                // Sharp Obsidian & Fire Spines
                ctx.fillStyle = '#27272a';
                ctx.fillRect(6, 10 + bob, 3, 3); ctx.fillRect(19, 10 + bob, 3, 3);
                ctx.fillStyle = '#facc15';
                ctx.fillRect(11, 4 + bob, 6, 4); ctx.fillRect(13, 2 + bob, 2, 3);
                // Fiery Yellow Eyes
                ctx.fillStyle = '#fef08a';
                ctx.fillRect(10, 12 + bob, 3, 3); ctx.fillRect(15, 12 + bob, 3, 3);
                ctx.fillStyle = '#450a0a';
                ctx.fillRect(11, 13 + bob, 1, 2); ctx.fillRect(16, 13 + bob, 1, 2);
                frames.push(canvas);
            } else if (type === 'lava_lurker') {
                const { canvas, ctx } = makeCanvas(32, 32);
                const step = (f === 1) ? 2 : 0;
                // Heavy Obsidian Stone Torso
                ctx.fillStyle = '#18181b'; ctx.fillRect(7, 8, 18, 16);
                ctx.fillStyle = '#27272a'; ctx.fillRect(9, 10, 14, 12);
                // Glowing Magma Cracks
                ctx.fillStyle = '#ea580c';
                ctx.fillRect(11, 12, 2, 7); ctx.fillRect(17, 14, 4, 2); ctx.fillRect(19, 11, 2, 5);
                ctx.fillStyle = '#facc15';
                ctx.fillRect(12, 14, 2, 3); ctx.fillRect(18, 13, 2, 2);
                // Fiery Horns
                ctx.fillStyle = '#dc2626';
                ctx.fillRect(6, 4 - step, 4, 6); ctx.fillRect(22, 4 + step, 4, 6);
                ctx.fillStyle = '#f97316';
                ctx.fillRect(7, 2 - step, 2, 3); ctx.fillRect(23, 2 + step, 2, 3);
                // Glowing Molten Eyes
                ctx.fillStyle = '#fef08a';
                ctx.fillRect(11, 10, 3, 2); ctx.fillRect(18, 10, 3, 2);
                // Huge Stone Fists
                ctx.fillStyle = '#3f3f46';
                ctx.fillRect(2, 12 + step, 6, 8); ctx.fillRect(24, 12 - step, 6, 8);
                ctx.fillStyle = '#ea580c';
                ctx.fillRect(3, 15 + step, 4, 3); ctx.fillRect(25, 15 - step, 4, 3);
                // Stubby Legs
                ctx.fillStyle = '#18181b';
                ctx.fillRect(9, 24 + step, 5, 6); ctx.fillRect(18, 24 - step, 5, 6);
                frames.push(canvas);
            }
        });
        return frames;
    }

    // MEGA BOSS: Archdemon Kathuros (64x64 Pixel Art)
    function createBossKathurosFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(64, 64);
            const wingY = (f === 1) ? 3 : 0;
            const coreGlow = (f === 1) ? '#ff0000' : '#dc2626';

            // Giant Demonic Bat Wings
            ctx.fillStyle = '#1a0505';
            // Left Wing
            ctx.beginPath();
            ctx.moveTo(20, 24); ctx.lineTo(2, 6 + wingY); ctx.lineTo(8, 22 + wingY); ctx.lineTo(4, 34 + wingY); ctx.lineTo(20, 32); ctx.fill();
            // Right Wing
            ctx.beginPath();
            ctx.moveTo(44, 24); ctx.lineTo(62, 6 + wingY); ctx.lineTo(56, 22 + wingY); ctx.lineTo(60, 34 + wingY); ctx.lineTo(44, 32); ctx.fill();
            // Wing bones
            ctx.fillStyle = '#450a0a';
            ctx.fillRect(6, 8 + wingY, 15, 3); ctx.fillRect(43, 8 + wingY, 15, 3);

            // Shadow Demon Torso
            ctx.fillStyle = '#18181b'; ctx.fillRect(20, 18, 24, 30);
            ctx.fillStyle = '#27272a'; ctx.fillRect(22, 20, 20, 26);

            // Burning Lava Rune Core on Chest
            ctx.fillStyle = coreGlow;
            ctx.beginPath(); ctx.arc(32, 28, 6, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#fef08a'; ctx.beginPath(); ctx.arc(32, 28, 3, 0, Math.PI * 2); ctx.fill();

            // Head & Horns
            ctx.fillStyle = '#09090b'; ctx.fillRect(24, 8, 16, 14);
            // Huge Curved Horns
            ctx.fillStyle = '#450a0a';
            ctx.fillRect(16, 2, 8, 12); ctx.fillRect(40, 2, 8, 12);
            ctx.fillStyle = '#dc2626'; ctx.fillRect(14, 0, 4, 5); ctx.fillRect(46, 0, 4, 5); // Fiery Horn Tips

            // Fiery Glowing Demon Eyes
            ctx.fillStyle = '#ef4444'; ctx.fillRect(27, 12, 3, 3); ctx.fillRect(34, 12, 3, 3);
            ctx.fillStyle = '#fef08a'; ctx.fillRect(28, 13, 1, 1); ctx.fillRect(35, 13, 1, 1);

            // Razor Fang Jaws
            ctx.fillStyle = '#000000'; ctx.fillRect(26, 17, 12, 4);
            ctx.fillStyle = '#ffffff'; ctx.fillRect(27, 17, 2, 2); ctx.fillRect(31, 17, 2, 2); ctx.fillRect(35, 17, 2, 2);

            // Muscular Shadow Arms with Claws
            ctx.fillStyle = '#18181b';
            ctx.fillRect(14, 22, 8, 18); ctx.fillRect(42, 22, 8, 18);
            // Claws
            ctx.fillStyle = '#dc2626';
            ctx.fillRect(12, 38, 4, 5); ctx.fillRect(16, 40, 4, 5);
            ctx.fillRect(44, 40, 4, 5); ctx.fillRect(48, 38, 4, 5);

            // Demon Legs / Hooves
            ctx.fillStyle = '#09090b';
            ctx.fillRect(23, 47, 7, 13); ctx.fillRect(34, 47, 7, 13);
            ctx.fillStyle = '#7f1d1d'; ctx.fillRect(22, 57, 9, 4); ctx.fillRect(33, 57, 9, 4);

            frames.push(canvas);
        });
        return frames;
    }


    // MEGA BOSS 2: Ancient Crystal Golem Luminarch (64x64 Pixel Art)
    function createBossLuminarchFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(64, 64);
            const floatY = (f === 1) ? 2 : 0;
            const coreColor = (f === 1) ? '#67e8f9' : '#06b6d4';

            // Floating Geometric Crystal Shoulders
            ctx.fillStyle = '#3b0764';
            ctx.fillRect(8, 14 + floatY, 14, 16); ctx.fillRect(42, 14 - floatY, 14, 16);
            ctx.fillStyle = '#581c87';
            ctx.fillRect(10, 16 + floatY, 10, 12); ctx.fillRect(44, 16 - floatY, 10, 12);
            // Crystal Shoulder Spikes
            ctx.fillStyle = '#06b6d4';
            ctx.beginPath(); ctx.moveTo(15, 6 + floatY); ctx.lineTo(10, 14 + floatY); ctx.lineTo(20, 14 + floatY); ctx.fill();
            ctx.beginPath(); ctx.moveTo(49, 6 - floatY); ctx.lineTo(44, 14 - floatY); ctx.lineTo(54, 14 - floatY); ctx.fill();

            // Heavy Amethyst Stone Torso
            ctx.fillStyle = '#1e1b4b'; ctx.fillRect(18, 16, 28, 30);
            ctx.fillStyle = '#2e1065'; ctx.fillRect(20, 18, 24, 26);

            // Pulsing Rotating Prismatic Core in Chest
            ctx.fillStyle = coreColor;
            ctx.beginPath(); ctx.moveTo(32, 20); ctx.lineTo(40, 30); ctx.lineTo(32, 40); ctx.lineTo(24, 30); ctx.fill();
            ctx.fillStyle = '#ffffff';
            ctx.beginPath(); ctx.moveTo(32, 25); ctx.lineTo(36, 30); ctx.lineTo(32, 35); ctx.lineTo(28, 30); ctx.fill();

            // Head / Golem Crest
            ctx.fillStyle = '#1e1b4b'; ctx.fillRect(24, 6, 16, 12);
            ctx.fillStyle = '#581c87'; ctx.fillRect(26, 8, 12, 10);
            // Glowing Cyan Horizontal Visor Eye
            ctx.fillStyle = '#22d3ee'; ctx.fillRect(27, 12, 10, 2);
            ctx.fillStyle = '#ffffff'; ctx.fillRect(31, 12, 2, 2);

            // Floating Crystal Fists
            ctx.fillStyle = '#2e1065';
            ctx.fillRect(4, 34 + floatY, 12, 14); ctx.fillRect(48, 34 - floatY, 12, 14);
            ctx.fillStyle = '#06b6d4';
            ctx.fillRect(4, 48 + floatY, 3, 5); ctx.fillRect(8, 48 + floatY, 3, 5); ctx.fillRect(12, 48 + floatY, 3, 5);
            ctx.fillRect(48, 48 - floatY, 3, 5); ctx.fillRect(52, 48 - floatY, 3, 5); ctx.fillRect(56, 48 - floatY, 3, 5);

            // Stone Pedestal Legs
            ctx.fillStyle = '#1e1b4b';
            ctx.fillRect(22, 46, 8, 14); ctx.fillRect(34, 46, 8, 14);
            ctx.fillStyle = '#06b6d4';
            ctx.fillRect(20, 58, 12, 4); ctx.fillRect(32, 58, 12, 4);

            frames.push(canvas);
        });
        return frames;
    }

    // MEGA BOSS 3: Venom Marsh Hydra (64x64 Pixel Art)
    function createBossHydrakisFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(64, 64);
            const sway = (f === 1) ? 2 : -2;

            // Coiled Serpentine Tail & Body Base
            ctx.fillStyle = '#064e3b';
            ctx.beginPath(); ctx.ellipse(32, 48, 22, 12, 0, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#047857';
            ctx.beginPath(); ctx.ellipse(32, 46, 18, 9, 0, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#84cc16'; // Belly scales
            ctx.fillRect(24, 48, 16, 6);

            // Left Serpentine Neck & Head
            ctx.fillStyle = '#064e3b';
            ctx.beginPath();
            ctx.moveTo(22, 46); ctx.quadraticCurveTo(12, 30 + sway, 14 + sway, 16); ctx.lineTo(20 + sway, 16); ctx.quadraticCurveTo(18, 32 + sway, 26, 46);
            ctx.fill();
            // Left Head
            ctx.fillStyle = '#047857'; ctx.fillRect(10 + sway, 12, 14, 10);
            ctx.fillStyle = '#facc15'; ctx.fillRect(13 + sway, 14, 3, 2); // Eye
            ctx.fillStyle = '#4ade80'; ctx.fillRect(10 + sway, 20, 2, 4); ctx.fillRect(14 + sway, 20, 2, 4); // Dripping Venom

            // Right Serpentine Neck & Head
            ctx.fillStyle = '#064e3b';
            ctx.beginPath();
            ctx.moveTo(42, 46); ctx.quadraticCurveTo(52, 30 - sway, 50 - sway, 16); ctx.lineTo(44 - sway, 16); ctx.quadraticCurveTo(46, 32 - sway, 38, 46);
            ctx.fill();
            // Right Head
            ctx.fillStyle = '#047857'; ctx.fillRect(40 - sway, 12, 14, 10);
            ctx.fillStyle = '#facc15'; ctx.fillRect(48 - sway, 14, 3, 2); // Eye
            ctx.fillStyle = '#4ade80'; ctx.fillRect(48 - sway, 20, 2, 4); ctx.fillRect(52 - sway, 20, 2, 4); // Venom

            // Middle Alpha Head (Taller & Dominant)
            ctx.fillStyle = '#064e3b';
            ctx.fillRect(28, 18 - sway, 8, 28);
            ctx.fillStyle = '#047857'; ctx.fillRect(24, 6 - sway, 16, 14);
            // Horn Crest on Center Head
            ctx.fillStyle = '#84cc16';
            ctx.beginPath(); ctx.moveTo(32, 1 - sway); ctx.lineTo(28, 6 - sway); ctx.lineTo(36, 6 - sway); ctx.fill();
            // Menacing Glowing Eyes & Fangs
            ctx.fillStyle = '#facc15'; ctx.fillRect(26, 10 - sway, 3, 3); ctx.fillRect(35, 10 - sway, 3, 3);
            ctx.fillStyle = '#000000'; ctx.fillRect(27, 11 - sway, 1, 2); ctx.fillRect(36, 11 - sway, 1, 2);
            ctx.fillStyle = '#ffffff'; ctx.fillRect(27, 18 - sway, 2, 3); ctx.fillRect(35, 18 - sway, 2, 3);
            ctx.fillStyle = '#4ade80'; ctx.fillRect(28, 20 - sway, 8, 3); // Venom froth

            frames.push(canvas);
        });
        return frames;
    }

    // MEGA BOSS 4: Molten Flame Drake Ignistron (64x64 Pixel Art)
    function createBossIgnistronFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(64, 64);
            const wingY = (f === 1) ? 3 : -2;

            // Fiery Giant Dragon Wings
            ctx.fillStyle = '#7f1d1d';
            // Left Wing
            ctx.beginPath();
            ctx.moveTo(22, 26); ctx.lineTo(2, 4 + wingY); ctx.lineTo(6, 26 + wingY); ctx.lineTo(2, 40 + wingY); ctx.lineTo(22, 34); ctx.fill();
            // Right Wing
            ctx.beginPath();
            ctx.moveTo(42, 26); ctx.lineTo(62, 4 + wingY); ctx.lineTo(58, 26 + wingY); ctx.lineTo(62, 40 + wingY); ctx.lineTo(42, 34); ctx.fill();
            // Burning Membrane Webbing
            ctx.fillStyle = '#f97316';
            ctx.fillRect(8, 8 + wingY, 12, 4); ctx.fillRect(44, 8 + wingY, 12, 4);
            ctx.fillStyle = '#fde047';
            ctx.fillRect(10, 14 + wingY, 8, 3); ctx.fillRect(46, 14 + wingY, 8, 3);

            // Black Obsidian Dragon Body
            ctx.fillStyle = '#09090b'; ctx.fillRect(22, 18, 20, 28);
            ctx.fillStyle = '#18181b'; ctx.fillRect(24, 20, 16, 24);
            // Glowing Magma Veins
            ctx.fillStyle = '#ea580c'; ctx.fillRect(28, 22, 8, 20);
            ctx.fillStyle = '#fde047'; ctx.fillRect(30, 24, 4, 16);

            // Dragon Head & Fiery Crown Horns
            ctx.fillStyle = '#09090b'; ctx.fillRect(24, 8, 16, 14);
            ctx.fillStyle = '#ea580c'; ctx.fillRect(16, 2, 8, 10); ctx.fillRect(40, 2, 8, 10);
            ctx.fillStyle = '#fde047'; ctx.fillRect(14, 0, 4, 4); ctx.fillRect(46, 0, 4, 4);
            // Blazing Magma Eyes & Smoking Snout
            ctx.fillStyle = '#facc15'; ctx.fillRect(27, 12, 3, 3); ctx.fillRect(34, 12, 3, 3);
            ctx.fillStyle = '#ffffff'; ctx.fillRect(28, 13, 1, 1); ctx.fillRect(35, 13, 1, 1);
            ctx.fillStyle = '#ef4444'; ctx.fillRect(27, 18, 10, 4);

            // Claws & Muscular Legs
            ctx.fillStyle = '#09090b';
            ctx.fillRect(20, 44, 8, 14); ctx.fillRect(36, 44, 8, 14);
            ctx.fillStyle = '#ea580c';
            ctx.fillRect(18, 56, 10, 4); ctx.fillRect(36, 56, 10, 4);

            frames.push(canvas);
        });
        return frames;
    }

    // MEGA BOSS 5: Glacial Titan Frostfang (64x64 Pixel Art)
    function createBossFrostfangFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(64, 64);
            const breathSway = (f === 1) ? 2 : 0;

            // Massive Pure White Fur Torso
            ctx.fillStyle = '#f8fafc'; ctx.fillRect(16, 14, 32, 32);
            ctx.fillStyle = '#e2e8f0'; ctx.fillRect(18, 16, 28, 28);
            ctx.fillStyle = '#bae6fd'; ctx.fillRect(22, 22, 20, 18); // Ice shaded belly

            // Translucent Glacial Ice Pauldrons on Shoulders
            ctx.fillStyle = '#38bdf8';
            ctx.fillRect(8, 12 + breathSway, 12, 14); ctx.fillRect(44, 12 - breathSway, 12, 14);
            ctx.fillStyle = '#e0f2fe';
            ctx.fillRect(10, 10 + breathSway, 8, 4); ctx.fillRect(46, 10 - breathSway, 8, 4);

            // Colossal Frost Fists
            ctx.fillStyle = '#e2e8f0';
            ctx.fillRect(4, 30 + breathSway, 14, 18); ctx.fillRect(46, 30 - breathSway, 14, 18);
            ctx.fillStyle = '#38bdf8'; // Ice-coated Knuckles
            ctx.fillRect(4, 44 + breathSway, 14, 6); ctx.fillRect(46, 44 - breathSway, 14, 6);

            // Head with Frozen Antler Horns
            ctx.fillStyle = '#f8fafc'; ctx.fillRect(22, 4, 20, 14);
            ctx.fillStyle = '#0284c7';
            ctx.beginPath(); ctx.moveTo(18, 0); ctx.lineTo(24, 6); ctx.lineTo(20, 10); ctx.fill();
            ctx.beginPath(); ctx.moveTo(46, 0); ctx.lineTo(40, 6); ctx.lineTo(44, 10); ctx.fill();
            // Glowing Piercing Sapphire Eyes
            ctx.fillStyle = '#0284c7'; ctx.fillRect(26, 8, 3, 3); ctx.fillRect(35, 8, 3, 3);
            ctx.fillStyle = '#ffffff'; ctx.fillRect(27, 9, 1, 1); ctx.fillRect(36, 9, 1, 1);
            // Cold Vapor Breath
            ctx.fillStyle = 'rgba(186, 230, 253, 0.7)';
            ctx.fillRect(28, 16, 8, 3 + breathSway);

            // Thick Yeti Legs
            ctx.fillStyle = '#cbd5e1';
            ctx.fillRect(20, 44, 10, 16); ctx.fillRect(34, 44, 10, 16);
            ctx.fillStyle = '#0284c7';
            ctx.fillRect(18, 56, 12, 5); ctx.fillRect(34, 56, 12, 5);

            frames.push(canvas);
        });
        return frames;
    }

    // MEGA BOSS 6: Undead Overlord Lord Malakor (64x64 Pixel Art)
    function createBossMalakorFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(64, 64);
            const hoverY = (f === 1) ? 3 : 0;

            // Billowing Royal Purple Necromancer Cape
            ctx.fillStyle = '#1e1b4b';
            ctx.beginPath(); ctx.moveTo(18, 16 + hoverY); ctx.lineTo(4, 58 + hoverY); ctx.lineTo(60, 58 + hoverY); ctx.lineTo(46, 16 + hoverY); ctx.fill();
            ctx.fillStyle = '#3b0764';
            ctx.beginPath(); ctx.moveTo(22, 18 + hoverY); ctx.lineTo(12, 56 + hoverY); ctx.lineTo(52, 56 + hoverY); ctx.lineTo(42, 18 + hoverY); ctx.fill();

            // Weathered Ancient Skeleton Torso
            ctx.fillStyle = '#e2e8f0'; ctx.fillRect(24, 18 + hoverY, 16, 22);
            // Swirling Violet Soul Flame in Ribcage
            ctx.fillStyle = '#a855f7';
            ctx.beginPath(); ctx.arc(32, 28 + hoverY, 5, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#f3e8ff';
            ctx.beginPath(); ctx.arc(32, 28 + hoverY, 2, 0, Math.PI * 2); ctx.fill();

            // Grim Ivory Skull & Crown
            ctx.fillStyle = '#f1f5f9'; ctx.fillRect(24, 8 + hoverY, 16, 12);
            // Ancient Spiked Gold Crown
            ctx.fillStyle = '#eab308';
            ctx.beginPath();
            ctx.moveTo(22, 8 + hoverY); ctx.lineTo(24, 0 + hoverY); ctx.lineTo(28, 6 + hoverY);
            ctx.lineTo(32, -1 + hoverY); ctx.lineTo(36, 6 + hoverY); ctx.lineTo(40, 0 + hoverY);
            ctx.lineTo(42, 8 + hoverY); ctx.fill();
            ctx.fillStyle = '#ef4444'; ctx.fillRect(31, 4 + hoverY, 2, 2); // Blood Ruby
            // Dark Crimson Eye Sockets
            ctx.fillStyle = '#dc2626'; ctx.fillRect(27, 12 + hoverY, 3, 3); ctx.fillRect(34, 12 + hoverY, 3, 3);
            ctx.fillStyle = '#000000'; ctx.fillRect(28, 17 + hoverY, 8, 2); // Jaw

            // Cursed Necromancer Scythe in Right Hand
            ctx.fillStyle = '#451a03'; ctx.fillRect(52, 6 + hoverY, 3, 48); // Staff
            ctx.fillStyle = '#7c3aed'; // Glowing Scythe Blade
            ctx.beginPath();
            ctx.moveTo(54, 6 + hoverY); ctx.quadraticCurveTo(40, -4 + hoverY, 28, 4 + hoverY);
            ctx.quadraticCurveTo(42, 4 + hoverY, 54, 14 + hoverY); ctx.fill();
            ctx.fillStyle = '#c084fc'; ctx.stroke();

            // Skeletal Left Hand Casting Magic
            ctx.fillStyle = '#e2e8f0'; ctx.fillRect(12, 24 + hoverY, 6, 8);
            ctx.fillStyle = '#c084fc'; ctx.fillRect(10, 22 + hoverY, 3, 3);

            frames.push(canvas);
        });
        return frames;
    }

    // MEGA BOSS 7: Ancient Forest Sovereign Sylvanus (64x64 Pixel Art)
    function createBossSylvanusFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(64, 64);
            const swayY = (f === 1) ? 2 : 0;
            const coreGlow = (f === 1) ? '#4ade80' : '#22c55e';

            // Ancient Tree Spirit Canopy (Broad leafy wings / foliage pauldrons)
            ctx.fillStyle = '#14532d';
            ctx.beginPath();
            ctx.moveTo(32, 20); ctx.lineTo(4, 4 + swayY); ctx.lineTo(8, 28 + swayY); ctx.lineTo(16, 42); ctx.lineTo(32, 36); ctx.fill();
            ctx.beginPath();
            ctx.moveTo(32, 20); ctx.lineTo(60, 4 + swayY); ctx.lineTo(56, 28 + swayY); ctx.lineTo(48, 42); ctx.lineTo(32, 36); ctx.fill();

            // Lush emerald leaf clusters
            ctx.fillStyle = '#16a34a';
            ctx.beginPath(); ctx.arc(10, 14 + swayY, 8, 0, Math.PI * 2); ctx.fill();
            ctx.beginPath(); ctx.arc(54, 14 + swayY, 8, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#4ade80';
            ctx.beginPath(); ctx.arc(12, 12 + swayY, 4, 0, Math.PI * 2); ctx.fill();
            ctx.beginPath(); ctx.arc(52, 12 + swayY, 4, 0, Math.PI * 2); ctx.fill();

            // Blooming Sacred Lotus Buds
            ctx.fillStyle = '#f472b6';
            ctx.fillRect(8, 6 + swayY, 4, 4); ctx.fillRect(52, 6 + swayY, 4, 4);
            ctx.fillStyle = '#fef08a';
            ctx.fillRect(9, 7 + swayY, 2, 2); ctx.fillRect(53, 7 + swayY, 2, 2);

            // Ancient Mossy Bark Torso
            ctx.fillStyle = '#27272a'; ctx.fillRect(22, 18 + swayY, 20, 24);
            ctx.fillStyle = '#15803d'; // Moss wraps
            ctx.fillRect(24, 20 + swayY, 6, 8); ctx.fillRect(34, 28 + swayY, 7, 10);

            // Radiant Emerald Nature Core (Heart of Sylvanus)
            ctx.fillStyle = coreGlow;
            ctx.beginPath(); ctx.arc(32, 28 + swayY, 5, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#fef08a';
            ctx.beginPath(); ctx.arc(32, 28 + swayY, 2, 0, Math.PI * 2); ctx.fill();

            // Majestic Branching Antler Crown
            ctx.strokeStyle = '#78350f'; ctx.lineWidth = 3;
            // Left Antler
            ctx.beginPath();
            ctx.moveTo(26, 12 + swayY); ctx.lineTo(18, 4 + swayY); ctx.lineTo(12, 2 + swayY);
            ctx.moveTo(20, 6 + swayY); ctx.lineTo(16, -1 + swayY);
            ctx.stroke();
            // Right Antler
            ctx.beginPath();
            ctx.moveTo(38, 12 + swayY); ctx.lineTo(46, 4 + swayY); ctx.lineTo(52, 2 + swayY);
            ctx.moveTo(44, 6 + swayY); ctx.lineTo(48, -1 + swayY);
            ctx.stroke();

            // Golden Wood Diadem & Eyes
            ctx.fillStyle = '#facc15'; ctx.fillRect(26, 10 + swayY, 12, 4);
            ctx.fillStyle = '#22c55e'; // Glowing Emerald Eyes
            ctx.fillRect(27, 12 + swayY, 3, 3); ctx.fillRect(34, 12 + swayY, 3, 3);
            ctx.fillStyle = '#ffffff'; ctx.fillRect(28, 13 + swayY, 1, 1); ctx.fillRect(35, 13 + swayY, 1, 1);

            // Hanging Root Tendrils
            ctx.fillStyle = '#78350f';
            ctx.fillRect(22, 42, 4, 18); ctx.fillRect(38, 42, 4, 18);
            ctx.fillRect(28, 44, 8, 14);
            ctx.fillStyle = '#15803d';
            ctx.fillRect(20, 56, 7, 4); ctx.fillRect(37, 56, 7, 4);

            frames.push(canvas);
        });
        return frames;
    }

    // MEGA BOSS 8: Sovereign of the Tempest Astreon (64x64 Pixel Art)
    function createBossAstreonFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(64, 64);
            const flap = (f === 1) ? 4 : 0;
            const eyeColor = (f === 1) ? '#38bdf8' : '#e0f2fe';

            // Expansive Thunder Wings (Cyan & Dark Basalt Feathering)
            ctx.fillStyle = '#0f172a';
            // Left Wing
            ctx.beginPath();
            ctx.moveTo(22, 22); ctx.lineTo(2, 6 + flap); ctx.lineTo(8, 24 + flap); ctx.lineTo(4, 38 + flap); ctx.lineTo(22, 34); ctx.fill();
            // Right Wing
            ctx.beginPath();
            ctx.moveTo(42, 22); ctx.lineTo(62, 6 + flap); ctx.lineTo(56, 24 + flap); ctx.lineTo(60, 38 + flap); ctx.lineTo(42, 34); ctx.fill();

            // Wing Lightning Feather Tips
            ctx.fillStyle = '#0284c7';
            ctx.fillRect(4, 8 + flap, 12, 4); ctx.fillRect(48, 8 + flap, 12, 4);
            ctx.fillStyle = '#38bdf8';
            ctx.fillRect(2, 6 + flap, 6, 3); ctx.fillRect(56, 6 + flap, 6, 3);
            ctx.fillStyle = '#fde047'; // Crackling sparks
            ctx.fillRect(8, 20 + flap, 3, 3); ctx.fillRect(53, 20 + flap, 3, 3);

            // Basalt Storm Armor Torso
            ctx.fillStyle = '#1e293b'; ctx.fillRect(22, 16 + flap * 0.5, 20, 26);
            ctx.fillStyle = '#0f172a'; ctx.fillRect(24, 18 + flap * 0.5, 16, 22);

            // Conductive Lightning Core on Chest
            ctx.fillStyle = '#0284c7';
            ctx.beginPath(); ctx.arc(32, 26 + flap * 0.5, 6, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#38bdf8';
            ctx.beginPath(); ctx.arc(32, 26 + flap * 0.5, 4, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#fef08a';
            ctx.fillRect(31, 24 + flap * 0.5, 3, 4);

            // Storm Helmet & Lightning Horns
            ctx.fillStyle = '#334155'; ctx.fillRect(24, 6 + flap * 0.5, 16, 12);
            ctx.fillStyle = '#facc15'; // Golden Lightning Horns
            ctx.beginPath(); ctx.moveTo(22, 6 + flap * 0.5); ctx.lineTo(16, -2 + flap * 0.5); ctx.lineTo(24, 2 + flap * 0.5); ctx.fill();
            ctx.beginPath(); ctx.moveTo(42, 6 + flap * 0.5); ctx.lineTo(48, -2 + flap * 0.5); ctx.lineTo(40, 2 + flap * 0.5); ctx.fill();

            // Piercing High-Voltage Eyes
            ctx.fillStyle = eyeColor;
            ctx.fillRect(27, 10 + flap * 0.5, 3, 3); ctx.fillRect(34, 10 + flap * 0.5, 3, 3);
            ctx.fillStyle = '#ffffff'; ctx.fillRect(28, 11 + flap * 0.5, 1, 1); ctx.fillRect(35, 11 + flap * 0.5, 1, 1);

            // Dual Storm-Lances
            // Left Lance
            ctx.fillStyle = '#64748b'; ctx.fillRect(14, 12 + flap, 2, 42);
            ctx.fillStyle = '#38bdf8'; ctx.fillRect(13, 8 + flap, 4, 12);
            ctx.fillStyle = '#fde047'; ctx.fillRect(14, 6 + flap, 2, 4);
            // Right Lance
            ctx.fillStyle = '#64748b'; ctx.fillRect(48, 12 + flap, 2, 42);
            ctx.fillStyle = '#38bdf8'; ctx.fillRect(47, 8 + flap, 4, 12);
            ctx.fillStyle = '#fde047'; ctx.fillRect(48, 6 + flap, 2, 4);

            // Armored Greaves
            ctx.fillStyle = '#1e293b';
            ctx.fillRect(22, 42, 8, 18); ctx.fillRect(34, 42, 8, 18);
            ctx.fillStyle = '#0284c7';
            ctx.fillRect(20, 56, 10, 5); ctx.fillRect(34, 56, 10, 5);

            frames.push(canvas);
        });
        return frames;
    }

    function createBossKarzarakFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(68, 68);
            const surge = (f === 1) ? 2 : 0;
            const eyeGlow = (f === 1) ? '#fef08a' : '#f59e0b';

            // Volcanic Smoke Aura
            ctx.fillStyle = 'rgba(234, 88, 12, 0.25)';
            ctx.beginPath(); ctx.ellipse(34, 38, 30, 22, 0, 0, Math.PI * 2); ctx.fill();

            // Colossal Serpentine Magma Neck & Body Segments
            ctx.fillStyle = '#1c1917';
            ctx.beginPath();
            ctx.moveTo(14, 62); ctx.lineTo(24, 38); ctx.lineTo(44, 38); ctx.lineTo(54, 62);
            ctx.closePath(); ctx.fill();

            // Molten Lava Belly Plates
            ctx.fillStyle = '#ea580c';
            ctx.fillRect(26, 44, 16, 6);
            ctx.fillRect(24, 52, 20, 6);
            ctx.fillStyle = '#facc15';
            ctx.fillRect(28, 45, 12, 3);
            ctx.fillRect(27, 53, 14, 3);

            // Great Wyrm Skull
            ctx.fillStyle = '#292524';
            ctx.beginPath();
            ctx.moveTo(20, 36 + surge); ctx.lineTo(16, 22 + surge); ctx.lineTo(34, 8 + surge);
            ctx.lineTo(52, 22 + surge); ctx.lineTo(48, 36 + surge);
            ctx.closePath(); ctx.fill();

            // Obsidian Brow & Snout
            ctx.fillStyle = '#1c1917';
            ctx.fillRect(24, 16 + surge, 20, 18);
            ctx.fillStyle = '#44403c';
            ctx.fillRect(26, 14 + surge, 16, 16);

            // Swept-back Obsidian Dragon Horns
            ctx.fillStyle = '#0c0a09';
            ctx.beginPath();
            ctx.moveTo(20, 18 + surge); ctx.lineTo(6, 6 + surge); ctx.lineTo(18, 10 + surge); ctx.fill();
            ctx.beginPath();
            ctx.moveTo(48, 18 + surge); ctx.lineTo(62, 6 + surge); ctx.lineTo(50, 10 + surge); ctx.fill();
            // Horn Magma Glow Lines
            ctx.fillStyle = '#f97316';
            ctx.fillRect(8, 7 + surge, 6, 2); ctx.fillRect(54, 7 + surge, 6, 2);

            // Crown Spines
            ctx.fillStyle = '#ea580c';
            ctx.fillRect(32, 2 + surge, 4, 8);
            ctx.fillStyle = '#facc15';
            ctx.fillRect(33, 1 + surge, 2, 4);

            // Molten Lava Jaws & Sharp White Fangs
            ctx.fillStyle = '#dc2626'; ctx.fillRect(22, 30 + surge, 24, 7);
            ctx.fillStyle = '#f97316'; ctx.fillRect(24, 32 + surge, 20, 4);
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(24, 29 + surge, 3, 3); ctx.fillRect(41, 29 + surge, 3, 3);
            ctx.fillRect(30, 30 + surge, 2, 2); ctx.fillRect(36, 30 + surge, 2, 2);

            // Blazing Lava Eyes
            ctx.fillStyle = eyeGlow;
            ctx.fillRect(22, 19 + surge, 5, 4); ctx.fillRect(41, 19 + surge, 5, 4);
            ctx.fillStyle = '#450a0a';
            ctx.fillRect(24, 20 + surge, 2, 3); ctx.fillRect(42, 20 + surge, 2, 3);

            // Nostril Smoke/Flame
            ctx.fillStyle = '#ea580c';
            ctx.fillRect(30, 35 + surge, 2, 2); ctx.fillRect(36, 35 + surge, 2, 2);

            frames.push(canvas);
        });
        return frames;
    }

    // New Open World Zones Tiles & Props (Ancient Canopy & Tempest Plateau)
    function createCanopyGrassTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#143419'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#1a4321'; ctx.fillRect(2, 4, 12, 10); ctx.fillRect(18, 16, 12, 12);
        ctx.fillStyle = '#22542a'; ctx.fillRect(4, 20, 6, 6); ctx.fillRect(20, 6, 6, 6);
        // Bioluminescent forest flora
        ctx.fillStyle = '#4ade80'; ctx.fillRect(8, 10, 2, 2); ctx.fillRect(22, 24, 2, 2);
        ctx.fillStyle = '#fef08a'; ctx.fillRect(24, 10, 2, 2); ctx.fillRect(6, 26, 2, 2);
        return canvas;
    }

    function createAncientTree() {
        const { canvas, ctx } = makeCanvas(48, 56);
        // Shadow base
        ctx.fillStyle = 'rgba(0,0,0,0.35)';
        ctx.beginPath(); ctx.ellipse(24, 50, 20, 5, 0, 0, Math.PI * 2); ctx.fill();
        // Massive mossy trunk
        ctx.fillStyle = '#27272a'; ctx.fillRect(16, 22, 16, 30);
        ctx.fillStyle = '#15803d'; // Moss wraps
        ctx.fillRect(17, 26, 6, 14); ctx.fillRect(25, 34, 6, 12);
        // Hollow tree hollow
        ctx.fillStyle = '#09090b'; ctx.beginPath(); ctx.ellipse(24, 38, 5, 7, 0, 0, Math.PI * 2); ctx.fill();
        // Gigantic sacred canopy
        ctx.fillStyle = '#14532d';
        ctx.beginPath(); ctx.arc(24, 18, 20, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(12, 14, 12, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(36, 14, 12, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#16a34a';
        ctx.beginPath(); ctx.arc(24, 14, 14, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#4ade80';
        ctx.fillRect(18, 8, 4, 4); ctx.fillRect(28, 12, 4, 4); ctx.fillRect(12, 16, 3, 3);
        // Glowing star fruits in canopy
        ctx.fillStyle = '#facc15'; ctx.fillRect(16, 12, 3, 3); ctx.fillRect(32, 16, 3, 3);
        return canvas;
    }

    function createBasaltFloorTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#0f172a'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#1e293b'; ctx.fillRect(2, 2, 14, 12); ctx.fillRect(18, 16, 12, 14);
        ctx.fillStyle = '#334155'; ctx.fillRect(4, 4, 10, 8); ctx.fillRect(20, 18, 8, 10);
        // Electric glowing hairline cracks
        ctx.fillStyle = '#0284c7';
        ctx.fillRect(15, 0, 2, 14); ctx.fillRect(17, 12, 14, 2);
        ctx.fillStyle = '#38bdf8'; ctx.fillRect(16, 4, 1, 6); ctx.fillRect(22, 13, 6, 1);
        return canvas;
    }

    function createThunderPillar() {
        const { canvas, ctx } = makeCanvas(32, 48);
        // Shadow
        ctx.fillStyle = 'rgba(0,0,0,0.35)';
        ctx.beginPath(); ctx.ellipse(16, 44, 14, 4, 0, 0, Math.PI * 2); ctx.fill();
        // Basalt pylon column
        ctx.fillStyle = '#1e293b'; ctx.fillRect(8, 10, 16, 34);
        ctx.fillStyle = '#0f172a'; ctx.fillRect(10, 12, 12, 30);
        // Brass conductive bands
        ctx.fillStyle = '#d97706';
        ctx.fillRect(7, 14, 18, 3); ctx.fillRect(7, 28, 18, 3); ctx.fillRect(7, 40, 18, 3);
        ctx.fillStyle = '#facc15';
        ctx.fillRect(9, 15, 14, 1); ctx.fillRect(9, 29, 14, 1);
        // Floating Lightning Capacitor Orb
        ctx.fillStyle = '#0284c7'; ctx.beginPath(); ctx.arc(16, 7, 6, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#38bdf8'; ctx.beginPath(); ctx.arc(16, 7, 4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#ffffff'; ctx.fillRect(15, 6, 2, 2);
        return canvas;
    }

    function createStarFruitCrop() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = 'rgba(0,0,0,0.25)';
        ctx.beginPath(); ctx.ellipse(16, 28, 10, 4, 0, 0, Math.PI * 2); ctx.fill();
        // Stem and broad leaves
        ctx.fillStyle = '#15803d'; ctx.fillRect(15, 14, 2, 14);
        ctx.fillStyle = '#22c55e';
        ctx.beginPath(); ctx.arc(11, 22, 6, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(21, 22, 6, 0, Math.PI * 2); ctx.fill();
        // Glowing Starfruit Cluster
        ctx.fillStyle = '#eab308';
        ctx.beginPath();
        ctx.moveTo(16, 4); ctx.lineTo(19, 11); ctx.lineTo(26, 12); ctx.lineTo(21, 18);
        ctx.lineTo(22, 25); ctx.lineTo(16, 21); ctx.lineTo(10, 25); ctx.lineTo(11, 18);
        ctx.lineTo(6, 12); ctx.lineTo(13, 11); ctx.closePath(); ctx.fill();
        ctx.fillStyle = '#fef08a'; ctx.fillRect(15, 12, 3, 4);
        ctx.fillStyle = '#ffffff'; ctx.fillRect(16, 13, 1, 2);
        return canvas;
    }

    function createThunderCrystalNode() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = 'rgba(0,0,0,0.3)';
        ctx.beginPath(); ctx.ellipse(16, 27, 12, 4, 0, 0, Math.PI * 2); ctx.fill();
        // Basalt ground node
        ctx.fillStyle = '#1e293b'; ctx.fillRect(8, 22, 16, 6);
        // Jagged sapphire crystals
        ctx.fillStyle = '#0284c7';
        // Center tall spire
        ctx.beginPath(); ctx.moveTo(16, 2); ctx.lineTo(21, 14); ctx.lineTo(17, 24); ctx.lineTo(11, 24); ctx.closePath(); ctx.fill();
        // Left spire
        ctx.beginPath(); ctx.moveTo(8, 10); ctx.lineTo(13, 18); ctx.lineTo(7, 24); ctx.closePath(); ctx.fill();
        // Right spire
        ctx.beginPath(); ctx.moveTo(25, 8); ctx.lineTo(27, 20); ctx.lineTo(20, 24); ctx.closePath(); ctx.fill();
        // Electric facets
        ctx.fillStyle = '#38bdf8';
        ctx.beginPath(); ctx.moveTo(16, 4); ctx.lineTo(19, 14); ctx.lineTo(16, 22); ctx.lineTo(13, 14); ctx.closePath(); ctx.fill();
        ctx.fillStyle = '#ffffff'; ctx.fillRect(15, 8, 2, 5);
        ctx.fillStyle = '#fde047'; ctx.fillRect(6, 12, 2, 2); ctx.fillRect(24, 14, 2, 2); // Sparks
        return canvas;
    }

    // New Zone Tiles & Props
    function createSwampFloorTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#22381f'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#172714'; ctx.fillRect(2, 4, 10, 8); ctx.fillRect(16, 14, 12, 10);
        ctx.fillStyle = '#2d4727'; ctx.fillRect(4, 20, 6, 6); ctx.fillRect(22, 6, 5, 5);
        // Swamp moss speckles
        ctx.fillStyle = '#84cc16'; ctx.fillRect(8, 10, 2, 2); ctx.fillRect(20, 24, 2, 2);
        return canvas;
    }

    function createSwampWaterTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#143026'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#1e4d3a'; ctx.fillRect(4, 6, 12, 6); ctx.fillRect(14, 18, 14, 8);
        ctx.fillStyle = '#4ade80'; ctx.fillRect(8, 8, 2, 2); ctx.fillRect(22, 22, 2, 2); // Toxic bubbles
        return canvas;
    }

    function createMagmaFloorTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#18181b'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#27272a'; ctx.fillRect(4, 4, 10, 8); ctx.fillRect(16, 16, 12, 10);
        // Glowing Heat Fissures
        ctx.fillStyle = '#ea580c'; ctx.fillRect(12, 2, 2, 14); ctx.fillRect(6, 18, 14, 2);
        ctx.fillStyle = '#fde047'; ctx.fillRect(12, 6, 1, 6);
        return canvas;
    }

    function createMagmaLavaTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#c2410c'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#ea580c'; ctx.fillRect(2, 4, 12, 8); ctx.fillRect(14, 16, 14, 10);
        ctx.fillStyle = '#facc15'; ctx.fillRect(6, 8, 6, 4); ctx.fillRect(20, 20, 6, 4);
        return canvas;
    }

    function createSnowFloorTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#f8fafc'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#f1f5f9'; ctx.fillRect(4, 6, 12, 8); ctx.fillRect(18, 18, 10, 8);
        ctx.fillStyle = '#e2e8f0'; ctx.fillRect(8, 20, 6, 4);
        ctx.fillStyle = '#bae6fd'; ctx.fillRect(14, 10, 2, 2); ctx.fillRect(24, 24, 2, 2); // Cyan glitter
        return canvas;
    }

    function createIceFloorTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#7dd3fc'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#bae6fd'; ctx.fillRect(2, 2, 28, 28);
        ctx.fillStyle = '#e0f2fe'; ctx.fillRect(6, 6, 12, 6); ctx.fillRect(16, 18, 12, 6);
        ctx.fillStyle = '#38bdf8'; ctx.fillRect(4, 14, 24, 1);
        return canvas;
    }

    function createCryptFloorTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#1c1917'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#292524'; ctx.fillRect(2, 2, 13, 13); ctx.fillRect(17, 2, 13, 13);
        ctx.fillRect(2, 17, 13, 13); ctx.fillRect(17, 17, 13, 13);
        ctx.fillStyle = '#44403c'; ctx.fillRect(4, 4, 4, 4); ctx.fillRect(20, 20, 4, 4);
        return canvas;
    }

    function createCryptWallTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#0c0a09'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#1c1917'; ctx.fillRect(2, 2, 28, 12); ctx.fillRect(2, 16, 28, 14);
        ctx.fillStyle = '#292524'; ctx.fillRect(4, 4, 12, 8); ctx.fillRect(18, 18, 10, 10);
        ctx.fillStyle = '#78716c'; ctx.fillRect(14, 8, 4, 4); // Skull carving
        return canvas;
    }

    function createTombstone() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#475569';
        ctx.beginPath();
        ctx.moveTo(8, 28); ctx.lineTo(8, 12); ctx.arc(16, 12, 8, Math.PI, 0); ctx.lineTo(24, 28); ctx.fill();
        ctx.fillStyle = '#64748b'; ctx.fillRect(10, 12, 12, 14);
        ctx.fillStyle = '#334155'; ctx.fillRect(15, 14, 2, 8); ctx.fillRect(12, 16, 8, 2); // Cross
        return canvas;
    }

    function createIcePillar() {
        const { canvas, ctx } = makeCanvas(32, 44);
        ctx.fillStyle = '#0284c7'; ctx.fillRect(8, 10, 16, 32);
        ctx.fillStyle = '#38bdf8';
        ctx.beginPath(); ctx.moveTo(16, 0); ctx.lineTo(8, 12); ctx.lineTo(24, 12); ctx.fill();
        ctx.fillStyle = '#bae6fd'; ctx.fillRect(10, 12, 12, 28);
        ctx.fillStyle = '#ffffff'; ctx.fillRect(12, 14, 4, 22);
        return canvas;
    }

    function createObsidianPillar() {
        const { canvas, ctx } = makeCanvas(32, 44);
        ctx.fillStyle = '#09090b'; ctx.fillRect(8, 10, 16, 32);
        ctx.fillStyle = '#18181b';
        ctx.beginPath(); ctx.moveTo(16, 0); ctx.lineTo(6, 12); ctx.lineTo(26, 12); ctx.fill();
        ctx.fillStyle = '#ea580c'; ctx.fillRect(14, 12, 4, 26);
        ctx.fillStyle = '#fde047'; ctx.fillRect(15, 16, 2, 16);
        return canvas;
    }

    function createBogTree() {
        const { canvas, ctx } = makeCanvas(44, 48);
        ctx.fillStyle = '#1c1917'; ctx.fillRect(18, 18, 8, 28); // Twisted trunk
        ctx.fillStyle = '#1e3a1e';
        ctx.beginPath(); ctx.arc(22, 16, 18, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#84cc16'; // Hanging moss
        ctx.fillRect(10, 24, 3, 10); ctx.fillRect(16, 26, 3, 12); ctx.fillRect(28, 24, 3, 10);
        return canvas;
    }

    function createPineTree() {
        const { canvas, ctx } = makeCanvas(44, 48);
        ctx.fillStyle = '#451a03'; ctx.fillRect(19, 36, 6, 10); // Trunk
        // 3 tiers of snow pine needles
        ctx.fillStyle = '#064e3b';
        ctx.beginPath(); ctx.moveTo(22, 4); ctx.lineTo(10, 18); ctx.lineTo(34, 18); ctx.fill();
        ctx.beginPath(); ctx.moveTo(22, 14); ctx.lineTo(6, 28); ctx.lineTo(38, 28); ctx.fill();
        ctx.beginPath(); ctx.moveTo(22, 24); ctx.lineTo(4, 38); ctx.lineTo(40, 38); ctx.fill();
        // Snow blankets
        ctx.fillStyle = '#f8fafc';
        ctx.fillRect(18, 6, 8, 4); ctx.fillRect(12, 18, 20, 4); ctx.fillRect(8, 28, 28, 4);
        return canvas;
    }

    // Set sprite references for Open World & Caves
    SPRITES.darkGrass = createDarkGrassTile();
    SPRITES.darkStone = createDarkStoneTile();
    SPRITES.runeTile = createRuneTile();
    SPRITES.pillar = createPillar();
    SPRITES.campfire = createCampfire();
    SPRITES.rubyNode = createRubyNode();
    SPRITES.starflower = createStarflower();
    SPRITES.chestClosed = createTreasureChest(false);
    SPRITES.chestOpened = createTreasureChest(true);
    SPRITES.bridge = createBridgeTile();

    function createCaveFloorTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#1e1b2e'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#171424'; ctx.fillRect(2, 4, 8, 6); ctx.fillRect(18, 14, 10, 8); ctx.fillRect(8, 22, 6, 6);
        ctx.fillStyle = '#2d2744'; ctx.fillRect(5, 5, 2, 2); ctx.fillRect(21, 16, 3, 2);
        // Bioluminescent crystal dust speckles
        ctx.fillStyle = '#67e8f9'; ctx.fillRect(12, 10, 1, 1); ctx.fillRect(26, 7, 1, 1); ctx.fillRect(15, 25, 1, 1);
        ctx.fillStyle = '#c084fc'; ctx.fillRect(6, 18, 1, 1); ctx.fillRect(24, 22, 1, 1);
        return canvas;
    }

    function createCaveWallTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#0f0d18'; ctx.fillRect(0, 0, 32, 32);
        // Jagged cavern rock facets
        ctx.fillStyle = '#1b172a';
        ctx.beginPath();
        ctx.moveTo(0, 0); ctx.lineTo(16, 4); ctx.lineTo(32, 0); ctx.lineTo(24, 16); ctx.lineTo(32, 32); ctx.lineTo(8, 30); ctx.lineTo(0, 32); ctx.fill();
        ctx.fillStyle = '#2c2542';
        ctx.fillRect(4, 8, 8, 8); ctx.fillRect(18, 6, 8, 10); ctx.fillRect(10, 18, 10, 8);
        ctx.fillStyle = '#0a0910'; ctx.fillRect(0, 28, 32, 4);
        return canvas;
    }

    function createCaveWaterTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Dark subterranean luminous pool
        ctx.fillStyle = '#082f49'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#0e7490'; ctx.fillRect(4, 6, 12, 2); ctx.fillRect(16, 18, 12, 2);
        ctx.fillStyle = '#38bdf8'; ctx.fillRect(6, 7, 6, 1); ctx.fillRect(18, 19, 6, 1);
        // Bioluminescent glowing ripple
        ctx.fillStyle = '#a5f3fc'; ctx.fillRect(12, 12, 2, 2); ctx.fillRect(22, 8, 2, 2); ctx.fillRect(8, 24, 2, 2);
        return canvas;
    }

    function createCaveEntranceTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#1c1917'; ctx.fillRect(0, 0, 32, 32);
        // Dark rocky arched mouth
        ctx.fillStyle = '#292524';
        ctx.fillRect(2, 2, 28, 28);
        ctx.fillStyle = '#050508';
        ctx.beginPath();
        ctx.arc(16, 26, 12, Math.PI, 0);
        ctx.fill();
        ctx.fillRect(4, 26, 24, 6);
        // Glowing cyan crystals at entrance
        ctx.fillStyle = '#38bdf8';
        ctx.fillRect(2, 20, 3, 6); ctx.fillRect(27, 20, 3, 6);
        ctx.fillStyle = '#a5f3fc'; ctx.fillRect(3, 21, 1, 3); ctx.fillRect(28, 21, 1, 3);
        return canvas;
    }

    function createCaveLadderTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#1e1b2e'; ctx.fillRect(0, 0, 32, 32);
        // Wooden mine ladder
        ctx.fillStyle = '#78350f'; ctx.fillRect(8, 0, 3, 32); ctx.fillRect(21, 0, 3, 32);
        ctx.fillStyle = '#b45309';
        for (let y = 3; y < 32; y += 7) {
            ctx.fillRect(11, y, 10, 3);
        }
        return canvas;
    }

    function createCrystalPillar() {
        const { canvas, ctx } = makeCanvas(32, 48);
        // Dark stone base
        ctx.fillStyle = '#1e1b2e'; ctx.beginPath(); ctx.ellipse(16, 42, 14, 6, 0, 0, Math.PI * 2); ctx.fill();
        // Giant central glowing cyan crystal
        ctx.fillStyle = '#0891b2';
        ctx.beginPath(); ctx.moveTo(16, 2); ctx.lineTo(24, 18); ctx.lineTo(22, 40); ctx.lineTo(10, 40); ctx.lineTo(8, 18); ctx.fill();
        ctx.fillStyle = '#06b6d4';
        ctx.beginPath(); ctx.moveTo(16, 4); ctx.lineTo(22, 18); ctx.lineTo(20, 38); ctx.lineTo(12, 38); ctx.lineTo(10, 18); ctx.fill();
        ctx.fillStyle = '#67e8f9';
        ctx.beginPath(); ctx.moveTo(16, 6); ctx.lineTo(18, 18); ctx.lineTo(17, 36); ctx.lineTo(15, 36); ctx.lineTo(14, 18); ctx.fill();
        ctx.fillStyle = '#ffffff'; ctx.fillRect(15, 8, 2, 8);
        // Side amethyst crystal shard
        ctx.fillStyle = '#9333ea';
        ctx.beginPath(); ctx.moveTo(6, 16); ctx.lineTo(10, 24); ctx.lineTo(8, 38); ctx.lineTo(4, 36); ctx.fill();
        ctx.fillStyle = '#c084fc';
        ctx.beginPath(); ctx.moveTo(6, 18); ctx.lineTo(9, 24); ctx.lineTo(7, 36); ctx.fill();
        // Side topaz crystal shard
        ctx.fillStyle = '#d97706';
        ctx.beginPath(); ctx.moveTo(26, 20); ctx.lineTo(28, 36); ctx.lineTo(23, 38); ctx.lineTo(22, 26); ctx.fill();
        return canvas;
    }

    function createGoldNode() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#1e1b2e'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#292524'; ctx.beginPath(); ctx.arc(16, 17, 12, 0, Math.PI * 2); ctx.fill();
        // Gold ore chunks
        ctx.fillStyle = '#eab308';
        ctx.fillRect(10, 10, 5, 4); ctx.fillRect(18, 14, 6, 5); ctx.fillRect(12, 18, 5, 4); ctx.fillRect(19, 9, 3, 3);
        ctx.fillStyle = '#fef08a';
        ctx.fillRect(11, 11, 2, 2); ctx.fillRect(19, 15, 2, 2); ctx.fillRect(13, 19, 2, 2);
        return canvas;
    }

    function createManaNode() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#1e1b2e'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#292524'; ctx.beginPath(); ctx.arc(16, 17, 12, 0, Math.PI * 2); ctx.fill();
        // Glowing cyan crystals
        ctx.fillStyle = '#0284c7';
        ctx.beginPath(); ctx.moveTo(16, 5); ctx.lineTo(21, 14); ctx.lineTo(11, 14); ctx.fill();
        ctx.beginPath(); ctx.moveTo(11, 12); ctx.lineTo(15, 22); ctx.lineTo(7, 22); ctx.fill();
        ctx.beginPath(); ctx.moveTo(22, 12); ctx.lineTo(25, 22); ctx.lineTo(17, 22); ctx.fill();
        ctx.fillStyle = '#38bdf8'; ctx.fillRect(14, 9, 4, 8); ctx.fillRect(10, 15, 4, 5); ctx.fillRect(19, 15, 4, 5);
        ctx.fillStyle = '#ffffff'; ctx.fillRect(15, 10, 2, 3);
        return canvas;
    }

    function createDiamondNode() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#1e1b2e'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#292524'; ctx.beginPath(); ctx.arc(16, 17, 12, 0, Math.PI * 2); ctx.fill();
        // Sparkling diamonds
        ctx.fillStyle = '#38bdf8';
        ctx.beginPath(); ctx.moveTo(16, 6); ctx.lineTo(22, 13); ctx.lineTo(16, 21); ctx.lineTo(10, 13); ctx.fill();
        ctx.beginPath(); ctx.moveTo(9, 14); ctx.lineTo(13, 19); ctx.lineTo(9, 24); ctx.lineTo(5, 19); ctx.fill();
        ctx.beginPath(); ctx.moveTo(23, 14); ctx.lineTo(27, 19); ctx.lineTo(23, 24); ctx.lineTo(19, 19); ctx.fill();
        ctx.fillStyle = '#ffffff'; ctx.fillRect(14, 10, 4, 5); ctx.fillRect(8, 17, 2, 2); ctx.fillRect(22, 17, 2, 2);
        return canvas;
    }

    SPRITES.caveFloor = createCaveFloorTile();
    SPRITES.caveWall = createCaveWallTile();
    SPRITES.caveWater = createCaveWaterTile();
    SPRITES.caveEntrance = createCaveEntranceTile();
    SPRITES.caveLadder = createCaveLadderTile();
    SPRITES.crystalPillar = createCrystalPillar();
    SPRITES.goldNode = createGoldNode();
    SPRITES.manaNode = createManaNode();
    SPRITES.diamondNode = createDiamondNode();

    function createCaveElevatorTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#1e1b2e'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#334155'; ctx.fillRect(4, 2, 24, 28);
        ctx.fillStyle = '#64748b'; ctx.fillRect(6, 4, 20, 24);
        ctx.fillStyle = '#0f172a'; ctx.fillRect(8, 6, 16, 20);
        ctx.fillStyle = '#cbd5e1';
        for (let x = 9; x <= 22; x += 3) {
            ctx.fillRect(x, 6, 1, 20);
        }
        ctx.fillStyle = '#f59e0b'; ctx.beginPath(); ctx.arc(16, 4, 3, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#fef08a'; ctx.fillRect(15, 3, 2, 2);
        ctx.fillStyle = '#94a3b8'; ctx.fillRect(15, 0, 2, 3);
        ctx.fillStyle = '#22c55e'; ctx.beginPath(); ctx.arc(16, 10, 2, 0, Math.PI * 2); ctx.fill();
        return canvas;
    }

    function createCaveLadderDownTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#1e1b2e'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#090810'; ctx.beginPath(); ctx.roundRect(6, 6, 20, 20, 4); ctx.fill();
        ctx.strokeStyle = '#334155'; ctx.lineWidth = 2; ctx.stroke();
        ctx.fillStyle = '#78350f'; ctx.fillRect(10, 6, 2, 20); ctx.fillRect(20, 6, 2, 20);
        ctx.fillStyle = '#d97706';
        for (let y = 9; y < 26; y += 4) {
            ctx.fillRect(11, y, 10, 2);
        }
        return canvas;
    }

    function createBreakableRockTile() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#1e1b2e'; ctx.fillRect(0, 0, 32, 32);
        ctx.fillStyle = '#334155';
        ctx.beginPath();
        ctx.moveTo(8, 26); ctx.lineTo(4, 18); ctx.lineTo(8, 8); ctx.lineTo(18, 5); ctx.lineTo(26, 9); ctx.lineTo(28, 20); ctx.lineTo(24, 27); ctx.closePath();
        ctx.fill();
        ctx.fillStyle = '#475569';
        ctx.beginPath();
        ctx.moveTo(9, 24); ctx.lineTo(6, 18); ctx.lineTo(9, 10); ctx.lineTo(17, 7); ctx.lineTo(24, 11); ctx.lineTo(25, 20); ctx.lineTo(22, 25); ctx.closePath();
        ctx.fill();
        ctx.fillStyle = '#64748b'; ctx.fillRect(11, 10, 6, 6);
        ctx.fillStyle = '#94a3b8'; ctx.fillRect(13, 11, 2, 2);
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(14, 12, 1, 4); ctx.fillRect(15, 15, 3, 1); ctx.fillRect(17, 16, 1, 3);
        return canvas;
    }

    function createSprinklerSprite(isQuality = false) {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = '#78350f'; ctx.beginPath(); ctx.ellipse(16, 22, 7, 3, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = isQuality ? '#b45309' : '#475569'; ctx.fillRect(14, 12, 4, 10);
        ctx.fillStyle = isQuality ? '#facc15' : '#94a3b8';
        ctx.fillRect(10, 10, 12, 4);
        ctx.fillRect(14, 7, 4, 10);
        if (isQuality) {
            ctx.fillStyle = '#fef08a'; ctx.fillRect(15, 8, 2, 2);
            ctx.fillStyle = '#38bdf8'; ctx.fillRect(15, 5, 2, 2);
        } else {
            ctx.fillStyle = '#38bdf8'; ctx.fillRect(15, 6, 2, 2);
        }
        return canvas;
    }

    function createMachineSprite(type) {
        const { canvas, ctx } = makeCanvas(32, 32);
        if (type === 'mayo_machine') {
            ctx.fillStyle = '#475569'; ctx.beginPath(); ctx.roundRect(6, 6, 20, 22, 3); ctx.fill();
            ctx.fillStyle = '#64748b'; ctx.fillRect(8, 8, 16, 18);
            ctx.fillStyle = '#fef08a'; ctx.beginPath(); ctx.arc(16, 17, 5, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#f59e0b'; ctx.fillRect(15, 2, 2, 4); ctx.fillRect(12, 2, 8, 2);
        } else if (type === 'cheese_press') {
            ctx.fillStyle = '#78350f'; ctx.fillRect(5, 6, 22, 22);
            ctx.fillStyle = '#92400e'; ctx.fillRect(7, 8, 18, 18);
            ctx.fillStyle = '#475569'; ctx.fillRect(14, 2, 4, 7); ctx.fillRect(10, 2, 12, 2);
            ctx.fillStyle = '#facc15'; ctx.fillRect(11, 15, 10, 8);
        } else if (type === 'preserves_jar') {
            ctx.fillStyle = '#78350f'; ctx.beginPath(); ctx.roundRect(6, 6, 20, 22, 4); ctx.fill();
            ctx.fillStyle = '#92400e'; ctx.fillRect(8, 8, 16, 18);
            ctx.fillStyle = '#f43f5e'; ctx.beginPath(); ctx.roundRect(10, 11, 12, 12, 2); ctx.fill();
            ctx.fillStyle = '#fbcfe8'; ctx.fillRect(12, 13, 3, 4);
        } else {
            ctx.fillStyle = '#5c2b0c'; ctx.beginPath(); ctx.roundRect(5, 5, 22, 24, 6); ctx.fill();
            ctx.fillStyle = '#854d0e'; ctx.fillRect(7, 7, 18, 20);
            ctx.fillStyle = '#1e293b'; ctx.fillRect(5, 10, 22, 2); ctx.fillRect(5, 22, 22, 2);
            ctx.fillStyle = '#ca8a04'; ctx.fillRect(14, 15, 4, 4);
        }
        return canvas;
    }

    function createDogFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(28, 24);
            const wag = (f === 1) ? 2 : 0;
            const step = (f === 1) ? 1 : 0;
            ctx.fillStyle = '#d97706'; ctx.beginPath(); ctx.roundRect(6, 8, 14, 9, 3); ctx.fill();
            ctx.fillStyle = '#fef3c7'; ctx.fillRect(6, 11, 10, 5);
            ctx.fillStyle = '#d97706'; ctx.beginPath(); ctx.roundRect(16, 4, 8, 8, 2); ctx.fill();
            ctx.fillStyle = '#fef3c7'; ctx.fillRect(20, 7, 4, 5);
            ctx.fillStyle = '#1e293b'; ctx.fillRect(23, 7, 2, 2);
            ctx.fillStyle = '#0f172a'; ctx.fillRect(19, 5, 2, 2);
            ctx.fillStyle = '#92400e'; ctx.beginPath(); ctx.moveTo(17, 4); ctx.lineTo(19, 1); ctx.lineTo(21, 4); ctx.fill();
            ctx.fillStyle = '#d97706'; ctx.fillRect(3, 6 - wag, 4, 4);
            ctx.fillStyle = '#fef3c7'; ctx.fillRect(2, 5 - wag, 3, 3);
            ctx.fillStyle = '#b45309';
            ctx.fillRect(8, 17 - step, 2, 4); ctx.fillRect(12, 17 + step, 2, 4);
            ctx.fillRect(15, 17 - step, 2, 4); ctx.fillRect(18, 17 + step, 2, 4);
            frames.push(canvas);
        });
        return frames;
    }


    function createCatFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(24, 22);
            const tail = (f === 1) ? 2 : 0;
            const step = (f === 1) ? 1 : 0;
            ctx.fillStyle = '#f8fafc'; ctx.beginPath(); ctx.roundRect(4, 7, 13, 8, 3); ctx.fill();
            ctx.fillStyle = '#ea580c'; ctx.fillRect(6, 7, 4, 4);
            ctx.fillStyle = '#1e293b'; ctx.fillRect(11, 8, 3, 4);
            ctx.fillStyle = '#f8fafc'; ctx.beginPath(); ctx.roundRect(13, 4, 7, 7, 2); ctx.fill();
            ctx.fillStyle = '#ea580c'; ctx.fillRect(14, 4, 3, 3);
            ctx.fillStyle = '#0f172a'; ctx.fillRect(17, 5, 1.5, 1.5);
            ctx.fillStyle = '#f43f5e'; ctx.fillRect(19, 7, 1.5, 1.5);
            ctx.fillStyle = '#f43f5e'; ctx.fillRect(14, 2, 2, 2); ctx.fillRect(18, 2, 2, 2);
            ctx.fillStyle = '#ea580c'; ctx.fillRect(2, 4 + tail, 2, 6);
            ctx.fillStyle = '#e2e8f0';
            ctx.fillRect(6, 15 - step, 2, 4); ctx.fillRect(9, 15 + step, 2, 4);
            ctx.fillRect(12, 15 - step, 2, 4); ctx.fillRect(15, 15 + step, 2, 4);
            frames.push(canvas);
        });
        return frames;
    }


    function createHorseFrames() {
        const frames = [];
        [0, 1].forEach(f => {
            const { canvas, ctx } = makeCanvas(40, 36);
            const gallop = (f === 1) ? 2 : 0;
            ctx.fillStyle = '#78350f'; ctx.beginPath(); ctx.roundRect(8, 12, 22, 14, 4); ctx.fill();
            ctx.fillStyle = '#3f1a05'; ctx.fillRect(2, 14, 7, 10);
            ctx.fillRect(26, 4, 3, 10);
            ctx.fillStyle = '#78350f';
            ctx.beginPath(); ctx.moveTo(24, 16); ctx.lineTo(32, 6); ctx.lineTo(37, 8); ctx.lineTo(30, 20); ctx.fill();
            ctx.fillStyle = '#92400e'; ctx.beginPath(); ctx.roundRect(31, 5, 8, 7, 2); ctx.fill();
            ctx.fillStyle = '#0f172a'; ctx.fillRect(35, 6, 2, 2);
            ctx.fillStyle = '#291104'; ctx.fillRect(36, 10, 3, 2);
            ctx.fillStyle = '#dc2626'; ctx.fillRect(16, 11, 8, 4);
            ctx.fillStyle = '#1e293b'; ctx.fillRect(17, 10, 6, 6);
            ctx.fillStyle = '#ca8a04'; ctx.fillRect(19, 16, 2, 4);
            ctx.strokeStyle = '#ca8a04'; ctx.lineWidth = 1; ctx.strokeRect(32, 6, 5, 5);
            ctx.fillStyle = '#5c2607';
            ctx.fillRect(10 + gallop, 26, 3, 8); ctx.fillRect(15 - gallop, 26, 3, 8);
            ctx.fillRect(22 + gallop, 26, 3, 8); ctx.fillRect(26 - gallop, 26, 3, 8);
            ctx.fillStyle = '#090807';
            ctx.fillRect(10 + gallop, 33, 3, 2); ctx.fillRect(15 - gallop, 33, 3, 2);
            ctx.fillRect(22 + gallop, 33, 3, 2); ctx.fillRect(26 - gallop, 33, 3, 2);
            frames.push(canvas);
        });
        return frames;
    }


    SPRITES.caveElevator = createCaveElevatorTile();
    SPRITES.caveLadderDown = createCaveLadderDownTile();
    SPRITES.breakableRock = createBreakableRockTile();
    SPRITES.sprinklerBasic = createSprinklerSprite(false);
    SPRITES.sprinklerQuality = createSprinklerSprite(true);
    SPRITES.mayoMachine = createMachineSprite('mayo_machine');
    SPRITES.cheesePress = createMachineSprite('cheese_press');
    SPRITES.preservesJar = createMachineSprite('preserves_jar');
    SPRITES.wineKeg = createMachineSprite('wine_keg');
    SPRITES.petDog = createDogFrames();
    SPRITES.petCat = createCatFrames();
    SPRITES.horse = createHorseFrames();

    function createBobberSprite() {
        const { canvas, ctx } = makeCanvas(12, 12);
        ctx.fillStyle = '#ef4444'; ctx.fillRect(3, 2, 6, 4);
        ctx.fillStyle = '#ffffff'; ctx.fillRect(3, 6, 6, 4);
        ctx.fillStyle = '#1e293b'; ctx.fillRect(5, 0, 2, 2);
        return canvas;
    }

    function createExclamationBubble() {
        const { canvas, ctx } = makeCanvas(16, 16);
        ctx.fillStyle = '#ffffff'; ctx.fillRect(1, 1, 14, 14);
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(0, 0, 16, 1); ctx.fillRect(0, 15, 16, 1);
        ctx.fillRect(0, 0, 1, 16); ctx.fillRect(15, 0, 1, 16);
        ctx.fillStyle = '#ef4444'; ctx.fillRect(7, 3, 2, 6); ctx.fillRect(7, 11, 2, 2);
        return canvas;
    }

    SPRITES.bobber = createBobberSprite();
    SPRITES.fishBiteBubble = createExclamationBubble();

    SPRITES.storyNpcs = {
        valeria: createStoryNPCFrames('valeria'),
        eldrin: createStoryNPCFrames('eldrin'),
        kael: createStoryNPCFrames('kael'),
        gilbert: createStoryNPCFrames('gilbert'),
        lilian: createStoryNPCFrames('lilian'),
        bob: createStoryNPCFrames('bob'),
        luna: createStoryNPCFrames('luna')
    };

    SPRITES.portraits = {
        valeria: createPortrait('valeria'),
        eldrin: createPortrait('eldrin'),
        kael: createPortrait('kael'),
        kathuros: createPortrait('kathuros'),
        gilbert: createPortrait('gilbert'),
        lilian: createPortrait('lilian'),
        bob: createPortrait('bob'),
        luna: createPortrait('luna')
    };

    function createStarBadge(fillColor: string, coreColor: string) {
        const { canvas, ctx } = makeCanvas(9, 9);
        ctx.fillStyle = fillColor;
        ctx.beginPath();
        ctx.moveTo(4.5, 0.5);
        ctx.lineTo(5.8, 3.2);
        ctx.lineTo(8.5, 3.5);
        ctx.lineTo(6.5, 5.5);
        ctx.lineTo(7.1, 8.5);
        ctx.lineTo(4.5, 7.0);
        ctx.lineTo(1.9, 8.5);
        ctx.lineTo(2.5, 5.5);
        ctx.lineTo(0.5, 3.5);
        ctx.lineTo(3.2, 3.2);
        ctx.closePath();
        ctx.fill();
        ctx.fillStyle = coreColor;
        ctx.fillRect(4, 3, 2, 2);
        return canvas;
    }

    SPRITES.starSilver = createStarBadge('#94a3b8', '#f8fafc');
    SPRITES.starGold = createStarBadge('#f59e0b', '#fef08a');
    SPRITES.starIridium = createStarBadge('#9333ea', '#f0abfc');

    function createPalmTree() {
        const { canvas, ctx } = makeCanvas(48, 64);
        // Curved brown trunk
        ctx.fillStyle = '#78350f';
        ctx.beginPath();
        ctx.moveTo(20, 64); ctx.quadraticCurveTo(28, 40, 24, 20); ctx.lineTo(28, 20); ctx.quadraticCurveTo(32, 40, 26, 64); ctx.closePath();
        ctx.fill();
        ctx.fillStyle = '#b45309';
        for (let y = 24; y < 60; y += 8) {
            ctx.fillRect(22, y, 6, 2);
        }
        // Coconuts
        ctx.fillStyle = '#451a03';
        ctx.beginPath(); ctx.arc(22, 22, 4, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(28, 22, 4, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(25, 26, 3.5, 0, Math.PI * 2); ctx.fill();
        // Sprawling green palm fronds
        ctx.fillStyle = '#15803d';
        ctx.beginPath(); ctx.ellipse(12, 16, 16, 6, -0.4, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.ellipse(36, 16, 16, 6, 0.4, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.ellipse(24, 10, 16, 6, 0, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.ellipse(10, 24, 14, 5, -0.7, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.ellipse(38, 24, 14, 5, 0.7, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#22c55e';
        ctx.fillRect(20, 8, 8, 4); ctx.fillRect(14, 12, 6, 3); ctx.fillRect(28, 12, 6, 3);
        return canvas;
    }

    function createSailboat() {
        const { canvas, ctx } = makeCanvas(48, 48);
        // Wooden hull
        ctx.fillStyle = '#78350f';
        ctx.beginPath();
        ctx.moveTo(6, 34); ctx.lineTo(42, 34); ctx.lineTo(36, 44); ctx.lineTo(12, 44); ctx.closePath();
        ctx.fill();
        ctx.fillStyle = '#b45309'; ctx.fillRect(8, 34, 32, 2);
        // Mast
        ctx.fillStyle = '#451a03'; ctx.fillRect(23, 4, 3, 30);
        // White & blue sail
        ctx.fillStyle = '#f8fafc';
        ctx.beginPath(); ctx.moveTo(25, 6); ctx.lineTo(42, 28); ctx.lineTo(25, 28); ctx.closePath(); ctx.fill();
        ctx.fillStyle = '#0284c7'; ctx.fillRect(25, 20, 14, 4);
        // Small front sail
        ctx.fillStyle = '#e2e8f0';
        ctx.beginPath(); ctx.moveTo(23, 10); ctx.lineTo(8, 28); ctx.lineTo(23, 28); ctx.closePath(); ctx.fill();
        // Golden pennant flag
        ctx.fillStyle = '#f59e0b';
        ctx.beginPath(); ctx.moveTo(24, 4); ctx.lineTo(32, 6); ctx.lineTo(24, 8); ctx.closePath(); ctx.fill();
        return canvas;
    }

    function createMushroomBox() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Wooden crate
        ctx.fillStyle = '#78350f'; ctx.fillRect(2, 8, 28, 22);
        ctx.fillStyle = '#451a03'; ctx.strokeRect(3, 9, 26, 20);
        ctx.fillStyle = '#b45309'; ctx.fillRect(4, 10, 24, 4); ctx.fillRect(4, 18, 24, 4);
        // Rich compost soil inside
        ctx.fillStyle = '#292524'; ctx.fillRect(5, 10, 22, 6);
        // Sprouting purple & red mushrooms
        ctx.fillStyle = '#c084fc'; ctx.beginPath(); ctx.arc(10, 9, 4, Math.PI, 0); ctx.fill();
        ctx.fillStyle = '#f8fafc'; ctx.fillRect(9, 9, 2, 4);
        ctx.fillStyle = '#ef4444'; ctx.beginPath(); ctx.arc(18, 8, 5, Math.PI, 0); ctx.fill();
        ctx.fillStyle = '#ffffff'; ctx.fillRect(17, 7, 2, 1);
        ctx.fillStyle = '#f8fafc'; ctx.fillRect(17, 8, 2, 5);
        ctx.fillStyle = '#fbbf24'; ctx.beginPath(); ctx.arc(24, 10, 3.5, Math.PI, 0); ctx.fill();
        return canvas;
    }

    function createGreenhouseExterior() {
        const { canvas, ctx } = makeCanvas(64, 64);
        // Glass roof structure
        ctx.fillStyle = '#0284c7'; ctx.fillRect(4, 8, 56, 48);
        ctx.fillStyle = '#38bdf8';
        for (let x = 6; x < 58; x += 10) {
            ctx.fillRect(x, 10, 8, 18);
            ctx.fillRect(x, 32, 8, 20);
        }
        // Iron structural frames
        ctx.fillStyle = '#334155';
        ctx.fillRect(4, 8, 56, 3); ctx.fillRect(4, 28, 56, 4); ctx.fillRect(4, 52, 56, 4);
        for (let x = 4; x <= 60; x += 10) ctx.fillRect(x, 8, 2, 48);
        // Glass shine
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(8, 12, 2, 10); ctx.fillRect(28, 12, 2, 10); ctx.fillRect(48, 12, 2, 10);
        // Brick base
        ctx.fillStyle = '#78350f'; ctx.fillRect(2, 54, 60, 10);
        ctx.fillStyle = '#9a3412';
        for (let x = 4; x < 60; x += 8) ctx.fillRect(x, 56, 6, 3);
        // Entrance door
        ctx.fillStyle = '#1e293b'; ctx.fillRect(24, 34, 16, 26);
        ctx.fillStyle = '#bae6fd'; ctx.fillRect(26, 36, 12, 14);
        ctx.fillStyle = '#facc15'; ctx.fillRect(35, 48, 2, 3); // Brass handle
        return canvas;
    }

    function createPirateShipwreck() {
        const { canvas, ctx } = makeCanvas(64, 64);
        // Broken Wooden Hull on sand
        ctx.fillStyle = '#451a03';
        ctx.beginPath();
        ctx.moveTo(4, 48); ctx.lineTo(60, 48); ctx.lineTo(52, 60); ctx.lineTo(12, 60); ctx.closePath();
        ctx.fill();
        ctx.fillStyle = '#78350f'; ctx.fillRect(6, 38, 48, 10);
        ctx.fillStyle = '#292524'; ctx.fillRect(10, 42, 6, 5); ctx.fillRect(24, 41, 7, 5); ctx.fillRect(40, 43, 6, 5);
        // Broken Main Mast leaning sideways
        ctx.fillStyle = '#451a03';
        ctx.save(); ctx.translate(32, 40); ctx.rotate(-0.25);
        ctx.fillRect(-3, -32, 6, 34);
        // Torn Black Jolly Roger Flag
        ctx.fillStyle = '#0f172a'; ctx.fillRect(3, -30, 24, 16);
        ctx.fillStyle = '#f8fafc'; ctx.beginPath(); ctx.arc(14, -23, 4, 0, Math.PI * 2); ctx.fill();
        ctx.fillRect(11, -18, 6, 2);
        ctx.restore();
        // Barnacles & Green Seaweed
        ctx.fillStyle = '#15803d'; ctx.fillRect(8, 56, 8, 4); ctx.fillRect(36, 58, 12, 3);
        ctx.fillStyle = '#cbd5e1'; ctx.fillRect(16, 52, 3, 3); ctx.fillRect(44, 50, 3, 3);
        return canvas;
    }

    function createPirateChest() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Rich Mahogany Chest Base
        ctx.fillStyle = '#78350f'; ctx.fillRect(4, 12, 24, 16);
        ctx.fillStyle = '#451a03'; ctx.strokeRect(4, 12, 24, 16);
        // Curved Lid
        ctx.fillStyle = '#9a3412';
        ctx.beginPath(); ctx.moveTo(4, 12); ctx.quadraticCurveTo(16, 5, 28, 12); ctx.closePath(); ctx.fill();
        // Golden Bands
        ctx.fillStyle = '#facc15';
        ctx.fillRect(8, 6, 3, 22); ctx.fillRect(21, 6, 3, 22);
        // Skull Keyhole Plate
        ctx.fillStyle = '#fbbf24'; ctx.fillRect(13, 14, 6, 7);
        ctx.fillStyle = '#0f172a'; ctx.beginPath(); ctx.arc(16, 17, 1.5, 0, Math.PI * 2); ctx.fill();
        ctx.fillRect(15.5, 18, 1, 2);
        return canvas;
    }

    function createPirateCaptain() {
        const { canvas, ctx } = makeCanvas(32, 36);
        // Captain Tricorn Hat with Red Feather
        ctx.fillStyle = '#0f172a';
        ctx.beginPath(); ctx.moveTo(4, 10); ctx.lineTo(16, 2); ctx.lineTo(28, 10); ctx.lineTo(24, 12); ctx.lineTo(8, 12); ctx.closePath(); ctx.fill();
        ctx.fillStyle = '#facc15'; ctx.fillRect(14, 8, 4, 3);
        ctx.fillStyle = '#ef4444'; ctx.beginPath(); ctx.moveTo(22, 4); ctx.quadraticCurveTo(28, -2, 26, 8); ctx.stroke();
        // Head & Face
        ctx.fillStyle = '#fed7aa'; ctx.fillRect(10, 11, 12, 10);
        // Eye Patch
        ctx.fillStyle = '#0f172a'; ctx.fillRect(11, 13, 3, 3); ctx.fillRect(8, 12, 14, 1);
        ctx.fillStyle = '#38bdf8'; ctx.fillRect(17, 13, 2, 2);
        // Bushy Crimson Beard
        ctx.fillStyle = '#b91c1c'; ctx.fillRect(9, 17, 14, 8); ctx.fillRect(11, 24, 10, 4);
        // Navy Blue Captain's Coat with Gold Trim
        ctx.fillStyle = '#1e3a8a'; ctx.fillRect(7, 21, 18, 11);
        ctx.fillStyle = '#facc15'; ctx.fillRect(14, 21, 4, 11); ctx.fillRect(15, 23, 2, 2); ctx.fillRect(15, 27, 2, 2);
        // Brown Pants & Peg Leg
        ctx.fillStyle = '#451a03'; ctx.fillRect(9, 31, 5, 5);
        ctx.fillStyle = '#b45309'; ctx.fillRect(17, 31, 3, 5);
        return canvas;
    }

    function createSeashell() {
        const { canvas, ctx } = makeCanvas(16, 16);
        ctx.fillStyle = '#fef08a';
        ctx.beginPath(); ctx.arc(8, 10, 6, Math.PI, 0); ctx.lineTo(9, 13); ctx.lineTo(7, 13); ctx.closePath(); ctx.fill();
        ctx.fillStyle = '#f472b6';
        ctx.beginPath(); ctx.moveTo(8, 4); ctx.lineTo(6, 12); ctx.moveTo(8, 4); ctx.lineTo(10, 12); ctx.stroke();
        return canvas;
    }

    function createMessageBottle() {
        const { canvas, ctx } = makeCanvas(16, 16);
        ctx.fillStyle = '#38bdf8'; ctx.fillRect(5, 6, 6, 8);
        ctx.fillStyle = '#bae6fd'; ctx.fillRect(6, 3, 4, 4);
        ctx.fillStyle = '#b45309'; ctx.fillRect(6, 2, 4, 2);
        ctx.fillStyle = '#fde047'; ctx.fillRect(7, 8, 2, 4);
        return canvas;
    }

    function createVolcanoForge() {
        const { canvas, ctx } = makeCanvas(48, 48);
        // Basalt Pedestal with Lava Runes
        ctx.fillStyle = '#1c1917'; ctx.fillRect(4, 28, 40, 16);
        ctx.fillStyle = '#292524'; ctx.fillRect(6, 30, 36, 12);
        // Molten Channels in Base
        ctx.fillStyle = '#ea580c';
        ctx.fillRect(8, 34, 32, 2); ctx.fillRect(16, 30, 2, 10); ctx.fillRect(30, 30, 2, 10);
        ctx.fillStyle = '#facc15';
        ctx.fillRect(10, 34, 12, 1); ctx.fillRect(26, 34, 12, 1);

        // Heavy Obsidian Anvil Top
        ctx.fillStyle = '#0c0a09';
        ctx.beginPath();
        ctx.moveTo(8, 16); ctx.lineTo(38, 16); ctx.lineTo(44, 20); ctx.lineTo(38, 28);
        ctx.lineTo(8, 28); ctx.lineTo(4, 20);
        ctx.closePath(); ctx.fill();

        ctx.fillStyle = '#27272a';
        ctx.fillRect(10, 18, 26, 8);
        // Glowing Fire Rune in center of Anvil
        ctx.fillStyle = '#ef4444'; ctx.fillRect(20, 20, 6, 4);
        ctx.fillStyle = '#fef08a'; ctx.fillRect(22, 21, 2, 2);

        // Fiery Smithing Hammer Resting on Top
        ctx.fillStyle = '#78350f'; ctx.fillRect(14, 8, 3, 10);
        ctx.fillStyle = '#f59e0b'; ctx.fillRect(12, 6, 7, 4);
        ctx.fillStyle = '#fef08a'; ctx.fillRect(13, 7, 5, 2);

        // Heat Shimmer Sparks
        ctx.fillStyle = '#ea580c'; ctx.fillRect(36, 12, 2, 2); ctx.fillRect(10, 12, 2, 2);
        return canvas;
    }

    function createVolcanoSwitch(active) {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Stone Base Plate
        ctx.fillStyle = '#27272a'; ctx.fillRect(4, 16, 24, 12);
        ctx.fillStyle = '#18181b'; ctx.strokeRect(4, 16, 24, 12);
        // Glowing Rim
        ctx.fillStyle = active ? '#22c55e' : '#dc2626';
        ctx.fillRect(6, 18, 20, 2);

        // Lever Handle
        if (active) {
            // Pulled down / activated
            ctx.fillStyle = '#71717a'; ctx.fillRect(14, 18, 10, 4);
            ctx.fillStyle = '#4ade80'; ctx.beginPath(); ctx.arc(24, 20, 4, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(23, 19, 1.5, 0, Math.PI * 2); ctx.fill();
        } else {
            // Standing upright
            ctx.fillStyle = '#71717a'; ctx.fillRect(14, 8, 4, 12);
            ctx.fillStyle = '#ef4444'; ctx.beginPath(); ctx.arc(16, 7, 4, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(15, 6, 1.5, 0, Math.PI * 2); ctx.fill();
        }
        return canvas;
    }

    function createCinderShardNode() {
        const { canvas, ctx } = makeCanvas(32, 32);
        // Basalt Rock Base
        ctx.fillStyle = '#1c1917'; ctx.beginPath(); ctx.arc(16, 18, 11, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#292524'; ctx.beginPath(); ctx.arc(16, 17, 8, 0, Math.PI * 2); ctx.fill();
        // Sprouting Fiery Cinder Crystals
        // Center Crystal
        ctx.fillStyle = '#ea580c';
        ctx.beginPath(); ctx.moveTo(16, 4); ctx.lineTo(20, 16); ctx.lineTo(12, 16); ctx.closePath(); ctx.fill();
        ctx.fillStyle = '#facc15';
        ctx.beginPath(); ctx.moveTo(16, 5); ctx.lineTo(18, 15); ctx.lineTo(14, 15); ctx.closePath(); ctx.fill();
        // Left Crystal
        ctx.fillStyle = '#dc2626';
        ctx.beginPath(); ctx.moveTo(9, 9); ctx.lineTo(14, 18); ctx.lineTo(7, 18); ctx.closePath(); ctx.fill();
        ctx.fillStyle = '#f97316';
        ctx.beginPath(); ctx.moveTo(9, 10); ctx.lineTo(12, 17); ctx.lineTo(8, 17); ctx.closePath(); ctx.fill();
        // Right Crystal
        ctx.fillStyle = '#dc2626';
        ctx.beginPath(); ctx.moveTo(23, 8); ctx.lineTo(25, 17); ctx.lineTo(18, 17); ctx.closePath(); ctx.fill();
        ctx.fillStyle = '#f97316';
        ctx.beginPath(); ctx.moveTo(23, 9); ctx.lineTo(24, 16); ctx.lineTo(20, 16); ctx.closePath(); ctx.fill();
        // Shimmer
        ctx.fillStyle = '#ffffff'; ctx.fillRect(15, 7, 2, 2);
        return canvas;
    }

    SPRITES.palmTree = createPalmTree();
    SPRITES.sailboat = createSailboat();
    SPRITES.mushroomBox = createMushroomBox();
    SPRITES.greenhouseExterior = createGreenhouseExterior();
    SPRITES.pirateShipwreck = createPirateShipwreck();
    SPRITES.pirateChest = createPirateChest();
    SPRITES.pirateCaptain = createPirateCaptain();
    SPRITES.seashell = createSeashell();
    SPRITES.messageBottle = createMessageBottle();
    SPRITES.volcanoForge = createVolcanoForge();
    SPRITES.volcanoSwitch = createVolcanoSwitch(false);
    SPRITES.volcanoSwitchActive = createVolcanoSwitch(true);
    SPRITES.cinderShardNode = createCinderShardNode();

    SPRITES.worldMonsters = {
        shadow_wolf: createWorldMonsterFrames('shadow_wolf'),
        goblin_scout: createWorldMonsterFrames('goblin_scout'),
        demon_treant: createWorldMonsterFrames('demon_treant'),
        cave_bat: createWorldMonsterFrames('cave_bat'),
        crystal_slime: createWorldMonsterFrames('crystal_slime'),
        swamp_croc: createWorldMonsterFrames('swamp_croc'),
        crystal_spider: createWorldMonsterFrames('crystal_spider'),
        magma_elemental: createWorldMonsterFrames('magma_elemental'),
        frost_wolf: createWorldMonsterFrames('frost_wolf'),
        skeleton_warrior: createWorldMonsterFrames('skeleton_warrior'),
        spire_demon: createWorldMonsterFrames('spire_demon'),
        spire_colossus: createWorldMonsterFrames('spire_colossus'),
        island_crab: createWorldMonsterFrames('island_crab'),
        cursed_pirate_skeleton: createWorldMonsterFrames('cursed_pirate_skeleton'),
        magma_sprite: createWorldMonsterFrames('magma_sprite'),
        magma_duggy: createWorldMonsterFrames('magma_duggy'),
        lava_lurker: createWorldMonsterFrames('lava_lurker')
    };

    SPRITES.bossKathuros = createBossKathurosFrames();
    SPRITES.bossLuminarch = createBossLuminarchFrames();
    SPRITES.bossHydrakis = createBossHydrakisFrames();
    SPRITES.bossIgnistron = createBossIgnistronFrames();
    SPRITES.bossFrostfang = createBossFrostfangFrames();
    SPRITES.bossMalakor = createBossMalakorFrames();
    SPRITES.bossSylvanus = createBossSylvanusFrames();
    SPRITES.bossAstreon = createBossAstreonFrames();
    SPRITES.bossKarzarak = createBossKarzarakFrames();

    SPRITES.bosses = {
        boss_kathuros: SPRITES.bossKathuros,
        boss_luminarch: SPRITES.bossLuminarch,
        boss_hydrakis: SPRITES.bossHydrakis,
        boss_ignistron: SPRITES.bossIgnistron,
        boss_frostfang: SPRITES.bossFrostfang,
        boss_malakor: SPRITES.bossMalakor,
        boss_sylvanus: SPRITES.bossSylvanus,
        boss_astreon: SPRITES.bossAstreon,
        boss_karzarak: SPRITES.bossKarzarak
    };

    SPRITES.swampFloor = createSwampFloorTile();
    SPRITES.swampWater = createSwampWaterTile();
    SPRITES.magmaFloor = createMagmaFloorTile();
    SPRITES.magmaLava = createMagmaLavaTile();
    SPRITES.snowFloor = createSnowFloorTile();
    SPRITES.iceFloor = createIceFloorTile();
    SPRITES.cryptFloor = createCryptFloorTile();
    SPRITES.cryptWall = createCryptWallTile();
    SPRITES.tombstone = createTombstone();
    SPRITES.icePillar = createIcePillar();
    SPRITES.obsidianPillar = createObsidianPillar();
    SPRITES.bogTree = createBogTree();
    SPRITES.pineTree = createPineTree();
    SPRITES.canopyGrass = createCanopyGrassTile();
    SPRITES.ancientTree = createAncientTree();
    SPRITES.basaltFloor = createBasaltFloorTile();
    SPRITES.thunderPillar = createThunderPillar();
    SPRITES.starFruitCrop = createStarFruitCrop();
    SPRITES.thunderCrystalNode = createThunderCrystalNode();

    function createDungeonChest(opened = false) {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = 'rgba(0,0,0,0.3)';
        ctx.beginPath(); ctx.ellipse(16, 28, 12, 4, 0, 0, Math.PI * 2); ctx.fill();
        if (!opened) {
            ctx.fillStyle = '#475569'; ctx.fillRect(4, 12, 24, 15);
            ctx.fillStyle = '#334155'; ctx.fillRect(6, 14, 20, 11);
            ctx.fillStyle = '#f59e0b';
            ctx.fillRect(4, 12, 24, 3);
            ctx.fillRect(4, 24, 24, 3);
            ctx.fillRect(4, 12, 3, 15);
            ctx.fillRect(25, 12, 3, 15);
            ctx.fillStyle = '#fbbf24'; ctx.fillRect(14, 16, 4, 5);
            ctx.fillStyle = '#d97706'; ctx.fillRect(15, 18, 2, 2);
        } else {
            ctx.fillStyle = '#334155'; ctx.fillRect(4, 16, 24, 11);
            ctx.fillStyle = '#fef08a'; ctx.fillRect(6, 12, 20, 5);
            ctx.fillStyle = '#f59e0b'; ctx.fillRect(8, 13, 16, 3);
            ctx.fillStyle = '#475569'; ctx.fillRect(4, 4, 24, 8);
            ctx.fillStyle = '#f59e0b'; ctx.fillRect(4, 4, 24, 2);
        }
        return canvas;
    }

    function createBreakablePot() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = 'rgba(0,0,0,0.3)';
        ctx.beginPath(); ctx.ellipse(16, 27, 8, 3, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#b45309';
        ctx.beginPath(); ctx.ellipse(16, 18, 9, 10, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#78350f'; ctx.fillRect(11, 7, 10, 3);
        ctx.fillRect(10, 5, 12, 2);
        ctx.fillStyle = '#fcd34d'; ctx.fillRect(8, 16, 16, 2);
        ctx.fillStyle = '#92400e'; ctx.fillRect(11, 19, 10, 2);
        ctx.fillStyle = '#d97706'; ctx.fillRect(10, 11, 4, 4);
        return canvas;
    }

    function createBreakableCrate() {
        const { canvas, ctx } = makeCanvas(32, 32);
        ctx.fillStyle = 'rgba(0,0,0,0.3)';
        ctx.beginPath(); ctx.ellipse(16, 28, 11, 4, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#92400e'; ctx.fillRect(5, 7, 22, 21);
        ctx.fillStyle = '#b45309'; ctx.fillRect(7, 9, 18, 17);
        ctx.strokeStyle = '#78350f'; ctx.lineWidth = 2.5;
        ctx.strokeRect(5, 7, 22, 21);
        ctx.beginPath(); ctx.moveTo(7, 9); ctx.lineTo(23, 24); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(23, 9); ctx.lineTo(7, 24); ctx.stroke();
        ctx.fillStyle = '#64748b';
        ctx.fillRect(5, 7, 4, 4); ctx.fillRect(23, 7, 4, 4);
        ctx.fillRect(5, 24, 4, 4); ctx.fillRect(23, 24, 4, 4);
        return canvas;
    }

    SPRITES.dungeonChest = createDungeonChest(false);
    SPRITES.dungeonChestOpened = createDungeonChest(true);
    SPRITES.breakablePot = createBreakablePot();
    SPRITES.breakableCrate = createBreakableCrate();

    SPRITES.updatePlayerAppearance = function(customOptions) {
        SPRITES.player = createPlayerFrames(customOptions);
    };

    const dataUrlCache = {};
    SPRITES.getItemDataURL = function(itemId) {
        if (dataUrlCache[itemId]) return dataUrlCache[itemId];
        const iconCanvas = SPRITES.getItemIcon(itemId);
        const url = iconCanvas.toDataURL();
        dataUrlCache[itemId] = url;
        return url;
    };

    SPRITES.getItemIcon = generateItemIcon;
})();
