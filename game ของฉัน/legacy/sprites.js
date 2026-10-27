/* ========================================================
   🌾 Pixel Art Sprite Engine for 2D Stardew-Style Farm
   Draws pure retro 16-bit / 32-bit pixel sprites directly
   onto offscreen canvases for crisp, fast rendering.
   ZERO emojis or AI slop!
   ======================================================== */

const SPRITES = {};

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

        // Hanging Wrought Iron Signboard with Golden Wheat 🌾
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

    function createNPCFrames(type = 'uncle') {
        const palMap = {
            uncle: { hair: '#94a3b8', shirt: '#15803d', pants: '#78350f', skin: '#ffccaa' },
            auntie: { hair: '#475569', shirt: '#ec4899', pants: '#831843', skin: '#ffccaa' },
            girl: { hair: '#d97706', shirt: '#eab308', pants: '#3b82f6', skin: '#ffccaa' },
            chef: { hair: '#1e293b', shirt: '#f8fafc', pants: '#1e293b', skin: '#ffccaa', hat: 'chef' }
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
        const { canvas, ctx } = makeCanvas(16, 16);
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
        }
        return canvas;
    }

    // ==========================================
    // 2. PLAYER SPRITES (Customizable Outfits)
    // ==========================================

    function createPlayerFrames(customOptions = {}) {
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
    SPRITES.grass = createGrassTile();
    SPRITES.soilDry = createSoilDryTile();
    SPRITES.soilWet = createSoilWetTile();
    SPRITES.path = createPathTile();
    SPRITES.fence = createFenceTile();
    SPRITES.water = createWaterTile();
    SPRITES.shippingBin = createShippingBin();
    SPRITES.well = createWell();
    SPRITES.tree = createTree();
    SPRITES.house = createHouse();
    SPRITES.barn = createBarn();
    SPRITES.shop = createShopBuilding();
    SPRITES.mill = createMill();
    SPRITES.hunterPost = createHunterPost();

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

    SPRITES.npcs = {
        uncle: createNPCFrames('uncle'),
        auntie: createNPCFrames('auntie'),
        girl: createNPCFrames('girl'),
        chef: createNPCFrames('chef')
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
        boss_flame: createProjectileCanvas('boss_flame')
    };

    // ==========================================
    // 🌲 OPEN WORLD RETRO PIXEL ART ASSETS
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

    // Set sprite references for Open World
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

    SPRITES.storyNpcs = {
        valeria: createStoryNPCFrames('valeria'),
        eldrin: createStoryNPCFrames('eldrin'),
        kael: createStoryNPCFrames('kael')
    };

    SPRITES.portraits = {
        valeria: createPortrait('valeria'),
        eldrin: createPortrait('eldrin'),
        kael: createPortrait('kael'),
        kathuros: createPortrait('kathuros')
    };

    SPRITES.worldMonsters = {
        shadow_wolf: createWorldMonsterFrames('shadow_wolf'),
        goblin_scout: createWorldMonsterFrames('goblin_scout'),
        demon_treant: createWorldMonsterFrames('demon_treant')
    };

    SPRITES.bossKathuros = createBossKathurosFrames();

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
