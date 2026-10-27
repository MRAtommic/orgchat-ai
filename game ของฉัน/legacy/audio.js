/* ========================================================
   🎵 8-bit / 16-bit Web Audio Sound Synthesizer
   Zero external files, instant, responsive sound effects!
   ======================================================== */

const SoundEngine = (function() {
    let ctx = null;
    let enabled = true;

    function init() {
        if (!ctx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                ctx = new AudioContext();
            }
        }
        if (ctx && ctx.state === 'suspended') {
            ctx.resume();
        }
    }

    // Play tone with envelope
    function playTone(freq, type, duration, startVol = 0.2, endVol = 0.001) {
        if (!enabled || !ctx) return;
        try {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = type;
            osc.frequency.setValueAtTime(freq, ctx.currentTime);
            gain.gain.setValueAtTime(startVol, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(endVol, ctx.currentTime + duration);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + duration);
        } catch(e) {}
    }

    return {
        init: init,
        toggle: function() {
            enabled = !enabled;
            return enabled;
        },
        step: function() {
            init();
            playTone(120, 'triangle', 0.04, 0.05);
        },
        till: function() {
            init();
            // Deep thud
            playTone(85, 'square', 0.12, 0.15);
            setTimeout(() => playTone(140, 'triangle', 0.08, 0.1), 30);
        },
        water: function() {
            init();
            // Splashing tones
            playTone(400, 'sine', 0.15, 0.15);
            setTimeout(() => playTone(650, 'sine', 0.12, 0.12), 40);
            setTimeout(() => playTone(500, 'sine', 0.1, 0.08), 80);
        },
        plant: function() {
            init();
            playTone(320, 'sine', 0.08, 0.15);
            setTimeout(() => playTone(480, 'sine', 0.1, 0.15), 50);
        },
        harvest: function() {
            init();
            // Joyful harvest chime
            playTone(523.25, 'triangle', 0.12, 0.2); // C5
            setTimeout(() => playTone(659.25, 'triangle', 0.12, 0.2), 60); // E5
            setTimeout(() => playTone(783.99, 'triangle', 0.15, 0.2), 120); // G5
            setTimeout(() => playTone(1046.50, 'triangle', 0.25, 0.25), 180); // C6
        },
        pet: function() {
            init();
            // Heart sound
            playTone(392, 'sine', 0.1, 0.2);
            setTimeout(() => playTone(587.33, 'sine', 0.2, 0.25), 80);
        },
        coin: function() {
            init();
            playTone(987.77, 'sine', 0.08, 0.2);
            setTimeout(() => playTone(1318.51, 'sine', 0.2, 0.25), 80);
        },
        cashRegister: function() {
            init();
            // Stardew / Heyday Ka-ching register chime!
            playTone(880, 'sine', 0.07, 0.22); // A5
            setTimeout(() => playTone(1174.66, 'sine', 0.08, 0.25), 55); // D6
            setTimeout(() => playTone(1760.00, 'triangle', 0.22, 0.28), 110); // A6
            setTimeout(() => playTone(2093.00, 'sine', 0.28, 0.25), 160); // C7
        },
        birdChirp: function() {
            init();
            playTone(2093, 'sine', 0.05, 0.08);
            setTimeout(() => playTone(2637, 'sine', 0.07, 0.09), 35);
            setTimeout(() => playTone(3135, 'sine', 0.05, 0.06), 90);
        },
        cricket: function() {
            init();
            playTone(4200, 'sawtooth', 0.03, 0.03);
            setTimeout(() => playTone(4400, 'sawtooth', 0.03, 0.03), 40);
        },
        craft: function() {
            init();
            playTone(260, 'sawtooth', 0.1, 0.15);
            setTimeout(() => playTone(330, 'sawtooth', 0.1, 0.15), 70);
            setTimeout(() => playTone(440, 'triangle', 0.2, 0.2), 140);
        },
        levelUp: function() {
            init();
            const notes = [440, 554.37, 659.25, 880];
            notes.forEach((freq, i) => {
                setTimeout(() => playTone(freq, 'triangle', 0.2, 0.3), i * 110);
            });
        },
        click: function() {
            init();
            playTone(700, 'sine', 0.03, 0.08);
        },
        door: function() {
            init();
            playTone(180, 'square', 0.08, 0.1);
            setTimeout(() => playTone(240, 'triangle', 0.12, 0.12), 40);
        },
        bell: function() {
            init();
            playTone(1174.66, 'sine', 0.15, 0.2); // D6
            setTimeout(() => playTone(1567.98, 'sine', 0.25, 0.25), 80); // G6
        },
        shoot: function(isRifle = false) {
            init();
            if (!isRifle) {
                // Slingshot snap & twang
                playTone(520, 'triangle', 0.06, 0.25);
                setTimeout(() => playTone(260, 'sine', 0.09, 0.18), 25);
            } else {
                // Hunting rifle blast
                playTone(160, 'sawtooth', 0.12, 0.35);
                setTimeout(() => playTone(90, 'square', 0.15, 0.25), 30);
            }
        },
        hit: function() {
            init();
            playTone(110, 'square', 0.08, 0.2);
            setTimeout(() => playTone(75, 'triangle', 0.06, 0.15), 25);
        },
        monsterDie: function() {
            init();
            playTone(220, 'sawtooth', 0.08, 0.25);
            setTimeout(() => playTone(140, 'sawtooth', 0.12, 0.2), 40);
            setTimeout(() => playTone(70, 'square', 0.18, 0.2), 90);
        },
        alarm: function() {
            init();
            playTone(440, 'sawtooth', 0.18, 0.25);
            setTimeout(() => playTone(370, 'sawtooth', 0.18, 0.25), 120);
            setTimeout(() => playTone(440, 'sawtooth', 0.25, 0.3), 240);
        },
        swordSlash: function() {
            init();
            playTone(340, 'triangle', 0.05, 0.25);
            setTimeout(() => playTone(180, 'sine', 0.08, 0.2), 20);
        },
        miningHit: function() {
            init();
            playTone(880, 'square', 0.04, 0.25);
            setTimeout(() => playTone(440, 'triangle', 0.09, 0.2), 30);
            setTimeout(() => playTone(220, 'sine', 0.08, 0.15), 60);
        },
        bossRoar: function() {
            init();
            playTone(90, 'sawtooth', 0.45, 0.4);
            setTimeout(() => playTone(65, 'square', 0.5, 0.35), 80);
            setTimeout(() => playTone(45, 'sawtooth', 0.6, 0.3), 200);
        },
        bossAttack: function() {
            init();
            playTone(180, 'sawtooth', 0.15, 0.3);
            setTimeout(() => playTone(120, 'square', 0.2, 0.25), 60);
            setTimeout(() => playTone(60, 'sawtooth', 0.3, 0.2), 140);
        },
        chestOpen: function() {
            init();
            const notes = [440, 554.37, 659.25, 880, 1108.73];
            notes.forEach((freq, i) => {
                setTimeout(() => playTone(freq, 'triangle', 0.18, 0.25), i * 90);
            });
        }
    };
})();
