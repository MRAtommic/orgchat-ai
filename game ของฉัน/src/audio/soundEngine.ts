/* ========================================================
    8-bit / 16-bit Web Audio Sound Synthesizer (TypeScript)
   Zero external files, instant, responsive sound effects!
   Includes Cozy Chiptune BGM, Fishing SFX & Weather Ambience
   ======================================================== */

const FARM_DAY_MELODY = [
  { note: 261.63, dur: 0.35 }, // C4
  { note: 329.63, dur: 0.35 }, // E4
  { note: 392.00, dur: 0.35 }, // G4
  { note: 523.25, dur: 0.60 }, // C5
  { note: 440.00, dur: 0.35 }, // A4
  { note: 392.00, dur: 0.45 }, // G4
  { note: 329.63, dur: 0.35 }, // E4
  { note: 293.66, dur: 0.60 }, // D4
  { note: 261.63, dur: 0.35 }, // C4
  { note: 329.63, dur: 0.35 }, // E4
  { note: 392.00, dur: 0.35 }, // G4
  { note: 440.00, dur: 0.45 }, // A4
  { note: 523.25, dur: 0.35 }, // C5
  { note: 587.33, dur: 0.45 }, // D5
  { note: 523.25, dur: 0.90 }, // C5
  { note: 0, dur: 0.60 }       // Rest
];

const VILLAGE_MELODY = [
  { note: 293.66, dur: 0.30 }, // D4
  { note: 369.99, dur: 0.30 }, // F#4
  { note: 440.00, dur: 0.35 }, // A4
  { note: 493.88, dur: 0.30 }, // B4
  { note: 440.00, dur: 0.35 }, // A4
  { note: 369.99, dur: 0.30 }, // F#4
  { note: 392.00, dur: 0.40 }, // G4
  { note: 329.63, dur: 0.50 }, // E4
  { note: 293.66, dur: 0.30 }, // D4
  { note: 369.99, dur: 0.30 }, // F#4
  { note: 440.00, dur: 0.35 }, // A4
  { note: 587.33, dur: 0.55 }, // D5
  { note: 554.37, dur: 0.30 }, // C#5
  { note: 493.88, dur: 0.35 }, // B4
  { note: 440.00, dur: 0.70 }, // A4
  { note: 0, dur: 0.45 }
];

const FOREST_MELODY = [
  { note: 329.63, dur: 0.40 }, // E4
  { note: 392.00, dur: 0.40 }, // G4
  { note: 493.88, dur: 0.50 }, // B4
  { note: 440.00, dur: 0.35 }, // A4
  { note: 392.00, dur: 0.35 }, // G4
  { note: 369.99, dur: 0.40 }, // F#4
  { note: 329.63, dur: 0.65 }, // E4
  { note: 293.66, dur: 0.40 }, // D4
  { note: 329.63, dur: 0.40 }, // E4
  { note: 392.00, dur: 0.40 }, // G4
  { note: 440.00, dur: 0.40 }, // A4
  { note: 493.88, dur: 0.60 }, // B4
  { note: 587.33, dur: 0.40 }, // D5
  { note: 523.25, dur: 0.40 }, // C5
  { note: 493.88, dur: 0.85 }, // B4
  { note: 0, dur: 0.50 }
];

const CAVE_MELODY = [
  { note: 261.63, dur: 0.50 }, // C4
  { note: 311.13, dur: 0.50 }, // Eb4
  { note: 392.00, dur: 0.60 }, // G4
  { note: 466.16, dur: 0.50 }, // Bb4
  { note: 392.00, dur: 0.50 }, // G4
  { note: 311.13, dur: 0.60 }, // Eb4
  { note: 0, dur: 0.40 },
  { note: 293.66, dur: 0.50 }, // D4
  { note: 349.23, dur: 0.50 }, // F4
  { note: 415.30, dur: 0.60 }, // Ab4
  { note: 523.25, dur: 0.50 }, // C5
  { note: 415.30, dur: 0.50 }, // Ab4
  { note: 349.23, dur: 0.70 }, // F4
  { note: 0, dur: 0.50 }
];

const NIGHT_MELODY = [
  { note: 220.00, dur: 0.70 }, // A3
  { note: 261.63, dur: 0.70 }, // C4
  { note: 329.63, dur: 0.90 }, // E4
  { note: 0, dur: 0.50 },
  { note: 196.00, dur: 0.70 }, // G3
  { note: 246.94, dur: 0.70 }, // B3
  { note: 293.66, dur: 0.90 }, // D4
  { note: 0, dur: 0.50 }
];

const CAVE_DEPTHS_MELODY = [
  { note: 523.25, dur: 0.40 }, // C5
  { note: 659.25, dur: 0.40 }, // E5
  { note: 783.99, dur: 0.50 }, // G5
  { note: 932.33, dur: 0.35 }, // Bb5
  { note: 880.00, dur: 0.45 }, // A5
  { note: 659.25, dur: 0.50 }, // E5
  { note: 587.33, dur: 0.40 }, // D5
  { note: 523.25, dur: 0.70 }, // C5
  { note: 0, dur: 0.45 }
];

const SWAMP_MELODY = [
  { note: 174.61, dur: 0.50 }, // F3
  { note: 207.65, dur: 0.45 }, // Ab3
  { note: 246.94, dur: 0.50 }, // B3
  { note: 261.63, dur: 0.60 }, // C4
  { note: 207.65, dur: 0.40 }, // Ab3
  { note: 196.00, dur: 0.55 }, // G3
  { note: 174.61, dur: 0.75 }, // F3
  { note: 0, dur: 0.50 }
];

const VOLCANO_MELODY = [
  { note: 146.83, dur: 0.30 }, // D3
  { note: 293.66, dur: 0.30 }, // D4
  { note: 174.61, dur: 0.35 }, // F3
  { note: 207.65, dur: 0.35 }, // G#3
  { note: 220.00, dur: 0.45 }, // A3
  { note: 293.66, dur: 0.40 }, // D4
  { note: 277.18, dur: 0.35 }, // C#4
  { note: 220.00, dur: 0.60 }, // A3
  { note: 0, dur: 0.30 }
];

const FROST_PEAK_MELODY = [
  { note: 659.25, dur: 0.45 }, // E5
  { note: 493.88, dur: 0.40 }, // B4
  { note: 783.99, dur: 0.50 }, // G5
  { note: 739.99, dur: 0.40 }, // F#5
  { note: 659.25, dur: 0.60 }, // E5
  { note: 587.33, dur: 0.45 }, // D5
  { note: 493.88, dur: 0.75 }, // B4
  { note: 0, dur: 0.45 }
];

const CRYPT_MELODY = [
  { note: 130.81, dur: 0.55 }, // C3
  { note: 155.56, dur: 0.55 }, // Eb3
  { note: 196.00, dur: 0.65 }, // G3
  { note: 246.94, dur: 0.50 }, // B3
  { note: 261.63, dur: 0.75 }, // C4
  { note: 196.00, dur: 0.50 }, // G3
  { note: 155.56, dur: 0.70 }, // Eb3
  { note: 0, dur: 0.50 }
];

const BOSS_BATTLE_MELODY = [
  { note: 220.00, dur: 0.16 }, // A3
  { note: 329.63, dur: 0.16 }, // E4
  { note: 440.00, dur: 0.18 }, // A4
  { note: 523.25, dur: 0.18 }, // C5
  { note: 659.25, dur: 0.22 }, // E5
  { note: 587.33, dur: 0.16 }, // D5
  { note: 523.25, dur: 0.16 }, // C5
  { note: 493.88, dur: 0.20 }, // B4
  { note: 440.00, dur: 0.16 }, // A4
  { note: 392.00, dur: 0.16 }, // G4
  { note: 466.16, dur: 0.18 }, // Bb4
  { note: 587.33, dur: 0.24 }, // D5
  { note: 554.37, dur: 0.28 }, // C#5
  { note: 0, dur: 0.12 }
];

const ISLAND_MELODY = [
  { note: 329.63, dur: 0.35 }, // E4
  { note: 392.00, dur: 0.35 }, // G4
  { note: 440.00, dur: 0.35 }, // A4
  { note: 493.88, dur: 0.40 }, // B4
  { note: 587.33, dur: 0.35 }, // D5
  { note: 493.88, dur: 0.35 }, // B4
  { note: 440.00, dur: 0.50 }, // A4
  { note: 392.00, dur: 0.30 }, // G4
  { note: 329.63, dur: 0.60 }, // E4
  { note: 0, dur: 0.25 }
];

const ISLAND_VOLCANO_MELODY = [
  { note: 110.00, dur: 0.35 }, // A2
  { note: 164.81, dur: 0.30 }, // E3
  { note: 220.00, dur: 0.30 }, // A3
  { note: 207.65, dur: 0.30 }, // G#3
  { note: 174.61, dur: 0.35 }, // F3
  { note: 164.81, dur: 0.45 }, // E3
  { note: 130.81, dur: 0.55 }, // C3
  { note: 0, dur: 0.25 }
];

class SoundEngineService {
  private ctx: AudioContext | null = null;
  private enabled: boolean = true;
  private bgmEnabled: boolean = true;
  private bgmPlaying: boolean = false;
  private bgmTimer: any = null;
  private bgmStep: number = 0;
  private isNightTime: boolean = false;
  private isBossBattle: boolean = false;
  private currentScene: string = 'farm';
  private bgmVolume: number = 0.06;

  constructor() {
    if (typeof window !== 'undefined') {
      this.setupAutoUnlock();
    }
  }

  public setupAutoUnlock(): void {
    const unlock = () => {
      this.init();
      window.removeEventListener('touchstart', unlock);
      window.removeEventListener('click', unlock);
      window.removeEventListener('keydown', unlock);
    };
    window.addEventListener('touchstart', unlock, { passive: true });
    window.addEventListener('click', unlock, { passive: true });
    window.addEventListener('keydown', unlock, { passive: true });
  }

  public init(): void {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  public toggle(): boolean {
    this.enabled = !this.enabled;
    if (!this.enabled) {
      this.stopBgm();
    }
    return this.enabled;
  }

  public isEnabled(): boolean {
    return this.enabled;
  }

  // ── BGM System ─────────────────────────────────────────────
  public isBgmOn(): boolean {
    return this.bgmEnabled;
  }

  public toggleBgm(): boolean {
    this.bgmEnabled = !this.bgmEnabled;
    if (this.bgmEnabled) {
      this.startBgm();
    } else {
      this.stopBgm();
    }
    return this.bgmEnabled;
  }

  public setNightTime(night: boolean): void {
    if (this.isNightTime !== night) {
      this.isNightTime = night;
      this.bgmStep = 0;
    }
  }

  public setSceneTheme(scene: string): void {
    if (this.currentScene !== scene) {
      this.currentScene = scene;
      this.bgmStep = 0;
    }
  }

  public setBossBattle(active: boolean): void {
    if (this.isBossBattle !== active) {
      this.isBossBattle = active;
      this.bgmStep = 0;
    }
  }

  private getActiveMelody() {
    if (this.isBossBattle) return BOSS_BATTLE_MELODY;
    if (this.isNightTime) return NIGHT_MELODY;
    switch (this.currentScene) {
      case 'village':
      case 'manor':
      case 'apothecary':
      case 'tavern':
      case 'forge':
        return VILLAGE_MELODY;
      case 'forest':
        return FOREST_MELODY;
      case 'cave':
        return CAVE_MELODY;
      case 'cave_depths':
        return CAVE_DEPTHS_MELODY;
      case 'swamp':
        return SWAMP_MELODY;
      case 'volcano':
        return VOLCANO_MELODY;
      case 'frost_peak':
        return FROST_PEAK_MELODY;
      case 'crypt':
        return CRYPT_MELODY;
      case 'island':
        return ISLAND_MELODY;
      case 'island_volcano':
        return ISLAND_VOLCANO_MELODY;
      case 'farm':
      default:
        return FARM_DAY_MELODY;
    }
  }

  public startBgm(): void {
    if (!this.bgmEnabled || !this.enabled || this.bgmPlaying) return;
    this.init();
    this.bgmPlaying = true;
    this.scheduleNextBgmNote();
  }

  public stopBgm(): void {
    this.bgmPlaying = false;
    if (this.bgmTimer) {
      clearTimeout(this.bgmTimer);
      this.bgmTimer = null;
    }
  }

  private scheduleNextBgmNote(): void {
    if (!this.bgmPlaying || !this.bgmEnabled || !this.enabled) return;

    const melody = this.getActiveMelody();
    const current = melody[this.bgmStep % melody.length];
    this.bgmStep++;

    if (current.note > 0 && this.ctx) {
      try {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = this.isNightTime ? 'sine' : 'triangle';
        osc.frequency.setValueAtTime(current.note, this.ctx.currentTime);

        const vol = this.bgmVolume * (this.isNightTime ? 0.8 : 1.0);
        gain.gain.setValueAtTime(0.001, this.ctx.currentTime);
        gain.gain.linearRampToValueAtTime(vol, this.ctx.currentTime + 0.05);
        gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + current.dur);

        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start();
        osc.stop(this.ctx.currentTime + current.dur);
      } catch {}
    }

    const intervalMs = Math.round(current.dur * 1000) + 40;
    this.bgmTimer = setTimeout(() => {
      this.scheduleNextBgmNote();
    }, intervalMs);
  }

  // ── SFX Helper ─────────────────────────────────────────────
  private playTone(
    freq: number,
    type: OscillatorType,
    duration: number,
    startVol: number = 0.2,
    endVol: number = 0.001
  ): void {
    if (!this.enabled) return;
    this.init();
    if (!this.ctx) return;

    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      gain.gain.setValueAtTime(startVol, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(endVol, this.ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch {}
  }

  public step(): void {
    this.playTone(120, 'triangle', 0.04, 0.05);
  }

  public till(): void {
    this.playTone(85, 'square', 0.12, 0.15);
    setTimeout(() => this.playTone(140, 'triangle', 0.08, 0.1), 30);
  }

  public water(): void {
    this.playTone(400, 'sine', 0.15, 0.15);
    setTimeout(() => this.playTone(650, 'sine', 0.12, 0.12), 40);
    setTimeout(() => this.playTone(500, 'sine', 0.1, 0.08), 80);
  }

  public plant(): void {
    this.playTone(320, 'sine', 0.08, 0.15);
    setTimeout(() => this.playTone(480, 'sine', 0.1, 0.15), 50);
  }

  public harvest(): void {
    this.playTone(523.25, 'triangle', 0.12, 0.2); // C5
    setTimeout(() => this.playTone(659.25, 'triangle', 0.12, 0.2), 60); // E5
    setTimeout(() => this.playTone(783.99, 'triangle', 0.15, 0.2), 120); // G5
    setTimeout(() => this.playTone(1046.50, 'triangle', 0.25, 0.25), 180); // C6
  }

  public pet(): void {
    this.playTone(392, 'sine', 0.1, 0.2);
    setTimeout(() => this.playTone(587.33, 'sine', 0.2, 0.25), 80);
  }

  public coin(): void {
    this.playTone(987.77, 'sine', 0.08, 0.2);
    setTimeout(() => this.playTone(1318.51, 'sine', 0.2, 0.25), 80);
  }

  public cashRegister(): void {
    this.playTone(880, 'sine', 0.07, 0.22); // A5
    setTimeout(() => this.playTone(1174.66, 'sine', 0.08, 0.25), 55); // D6
    setTimeout(() => this.playTone(1760.00, 'triangle', 0.22, 0.28), 110); // A6
    setTimeout(() => this.playTone(2093.00, 'sine', 0.28, 0.25), 160); // C7
  }

  public birdChirp(): void {
    this.playTone(2093, 'sine', 0.05, 0.08);
    setTimeout(() => this.playTone(2637, 'sine', 0.07, 0.09), 35);
    setTimeout(() => this.playTone(3135, 'sine', 0.05, 0.06), 90);
  }

  public cricket(): void {
    this.playTone(4200, 'sawtooth', 0.03, 0.03);
    setTimeout(() => this.playTone(4400, 'sawtooth', 0.03, 0.03), 40);
  }

  public craft(): void {
    this.playTone(260, 'sawtooth', 0.1, 0.15);
    setTimeout(() => this.playTone(330, 'sawtooth', 0.1, 0.15), 70);
    setTimeout(() => this.playTone(440, 'triangle', 0.2, 0.2), 140);
  }

  public levelUp(): void {
    const notes = [440, 554.37, 659.25, 880];
    notes.forEach((freq, i) => {
      setTimeout(() => this.playTone(freq, 'triangle', 0.2, 0.3), i * 110);
    });
  }

  public click(): void {
    this.playTone(700, 'sine', 0.03, 0.08);
  }

  public errorClick(): void {
    if (!this.enabled) return;
    this.init();
    this.playTone(150, 'sawtooth', 0.12, 0.25);
  }

  public door(): void {
    this.playTone(180, 'square', 0.08, 0.1);
    setTimeout(() => this.playTone(240, 'triangle', 0.12, 0.12), 40);
  }

  public bell(): void {
    this.playTone(1174.66, 'sine', 0.15, 0.2); // D6
    setTimeout(() => this.playTone(1567.98, 'sine', 0.25, 0.25), 80); // G6
  }

  public shoot(isRifle: boolean = false): void {
    if (!isRifle) {
      this.playTone(520, 'triangle', 0.06, 0.25);
      setTimeout(() => this.playTone(260, 'sine', 0.09, 0.18), 25);
    } else {
      this.playTone(160, 'sawtooth', 0.12, 0.35);
      setTimeout(() => this.playTone(90, 'square', 0.15, 0.25), 30);
    }
  }

  public hit(): void {
    this.playTone(110, 'square', 0.08, 0.2);
    setTimeout(() => this.playTone(75, 'triangle', 0.06, 0.15), 25);
  }

  public monsterDie(): void {
    this.playTone(220, 'sawtooth', 0.08, 0.25);
    setTimeout(() => this.playTone(140, 'sawtooth', 0.12, 0.2), 40);
    setTimeout(() => this.playTone(70, 'square', 0.18, 0.2), 90);
  }

  public alarm(): void {
    this.playTone(440, 'sawtooth', 0.18, 0.25);
    setTimeout(() => this.playTone(370, 'sawtooth', 0.18, 0.25), 120);
    setTimeout(() => this.playTone(440, 'sawtooth', 0.25, 0.3), 240);
  }

  public swordSlash(comboStep: number = 1): void {
    if (comboStep === 3) {
      // Step 3 Finisher Smite Sound (resonant blade boom + high harmonic shimmer)
      this.playTone(160, 'sawtooth', 0.12, 0.35);
      setTimeout(() => this.playTone(520, 'triangle', 0.16, 0.4), 25);
      setTimeout(() => this.playTone(880, 'sine', 0.22, 0.3), 60);
    } else if (comboStep === 2) {
      // Step 2 Cleave (medium pitch whoosh)
      this.playTone(420, 'triangle', 0.06, 0.28);
      setTimeout(() => this.playTone(220, 'sine', 0.09, 0.22), 20);
    } else {
      // Step 1 Swift Slash (crisp agile swoosh)
      this.playTone(340, 'triangle', 0.05, 0.25);
      setTimeout(() => this.playTone(180, 'sine', 0.08, 0.2), 20);
    }
  }

  public comboFinisher(): void {
    this.playTone(95, 'sawtooth', 0.18, 0.4);
    setTimeout(() => this.playTone(380, 'square', 0.12, 0.35), 30);
    setTimeout(() => this.playTone(760, 'triangle', 0.22, 0.35), 70);
    setTimeout(() => this.playTone(1200, 'sine', 0.3, 0.28), 120);
  }

  public miningHit(): void {
    this.playTone(880, 'square', 0.04, 0.25);
    setTimeout(() => this.playTone(440, 'triangle', 0.09, 0.2), 30);
    setTimeout(() => this.playTone(220, 'sine', 0.08, 0.15), 60);
  }

  public chopWood(): void {
    this.playTone(220, 'sawtooth', 0.06, 0.28);
    setTimeout(() => this.playTone(130, 'triangle', 0.1, 0.25), 35);
    setTimeout(() => this.playTone(85, 'sine', 0.14, 0.2), 70);
  }

  public bossRoar(): void {
    this.playTone(90, 'sawtooth', 0.45, 0.4);
    setTimeout(() => this.playTone(65, 'square', 0.5, 0.35), 80);
    setTimeout(() => this.playTone(45, 'sawtooth', 0.6, 0.3), 200);
  }

  public bossAttack(): void {
    this.playTone(180, 'sawtooth', 0.15, 0.3);
    setTimeout(() => this.playTone(120, 'square', 0.2, 0.25), 60);
    setTimeout(() => this.playTone(60, 'sawtooth', 0.3, 0.2), 140);
  }

  // ──  Epic Boss Kathuros SFX Suite ──────────────────────────
  public bossTelegraph(): void {
    if (!this.enabled || !this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(140, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(520, this.ctx.currentTime + 0.35);
      gain.gain.setValueAtTime(0.01, this.ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.22, this.ctx.currentTime + 0.15);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.35);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.35);
    } catch {}
  }

  public bossShockwave(): void {
    if (!this.enabled || !this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(80, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(28, this.ctx.currentTime + 0.5);
      gain.gain.setValueAtTime(0.38, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.5);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.5);
    } catch {}
    this.playTone(60, 'sawtooth', 0.25, 0.25);
  }

  public bossMeteor(): void {
    if (!this.enabled || !this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(900, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(120, this.ctx.currentTime + 0.45);
      gain.gain.setValueAtTime(0.18, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.45);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.45);
    } catch {}
    setTimeout(() => {
      this.playTone(55, 'sawtooth', 0.55, 0.35);
      this.playTone(35, 'square', 0.65, 0.3);
    }, 420);
  }

  public bossDash(): void {
    if (!this.enabled || !this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(450, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(110, this.ctx.currentTime + 0.25);
      gain.gain.setValueAtTime(0.28, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.25);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.25);
    } catch {}
  }

  public bossSpikeErupt(): void {
    this.playTone(160, 'square', 0.12, 0.28);
    setTimeout(() => this.playTone(720, 'triangle', 0.18, 0.3), 30);
    setTimeout(() => this.playTone(90, 'sawtooth', 0.25, 0.25), 60);
  }

  public bossPhaseChange(): void {
    if (!this.enabled || !this.ctx) return;
    this.playTone(75, 'sawtooth', 0.9, 0.4);
    setTimeout(() => this.playTone(50, 'square', 1.1, 0.4), 80);
    setTimeout(() => this.playTone(110, 'sawtooth', 0.8, 0.35), 160);
    setTimeout(() => this.playTone(220, 'triangle', 0.7, 0.3), 240);
  }

  // ──  Mega Bosses Arsenal SFX ──────────────────────────────
  public bossLaser(): void {
    if (!this.enabled || !this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(1400, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(320, this.ctx.currentTime + 0.35);
      gain.gain.setValueAtTime(0.25, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.35);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.35);
    } catch {}
    this.playTone(880, 'triangle', 0.2, 0.2);
  }

  public bossPoisonSpit(): void {
    this.playTone(280, 'square', 0.08, 0.22);
    setTimeout(() => this.playTone(180, 'triangle', 0.15, 0.25), 40);
    setTimeout(() => this.playTone(120, 'sine', 0.22, 0.28), 90);
  }

  public bossDragonBreath(): void {
    if (!this.enabled || !this.ctx) return;
    this.playTone(85, 'sawtooth', 0.65, 0.38);
    setTimeout(() => this.playTone(140, 'square', 0.5, 0.35), 60);
    setTimeout(() => this.playTone(65, 'sawtooth', 0.75, 0.4), 140);
  }

  public bossIceShatter(): void {
    this.playTone(950, 'triangle', 0.1, 0.3);
    setTimeout(() => this.playTone(1250, 'sine', 0.14, 0.35), 35);
    setTimeout(() => this.playTone(400, 'square', 0.2, 0.25), 80);
  }

  public bossSoulScream(): void {
    if (!this.enabled || !this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(350, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(820, this.ctx.currentTime + 0.25);
      osc.frequency.exponentialRampToValueAtTime(160, this.ctx.currentTime + 0.5);
      gain.gain.setValueAtTime(0.24, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.5);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.5);
    } catch {}
  }

  public bossHoming(): void {
    this.playTone(420, 'sine', 0.1, 0.2);
    setTimeout(() => this.playTone(360, 'sine', 0.12, 0.18), 70);
    setTimeout(() => this.playTone(480, 'sine', 0.15, 0.22), 140);
  }

  public bossSporeSpiral(): void {
    const notes = [330, 440, 554, 659, 880];
    notes.forEach((freq, idx) => {
      setTimeout(() => this.playTone(freq, 'triangle', 0.08, 0.15), idx * 35);
    });
  }

  public bossNatureBloom(): void {
    if (!this.enabled || !this.ctx) return;
    const freqs = [523.25, 659.25, 783.99, 1046.50, 1318.51];
    freqs.forEach((freq, idx) => {
      setTimeout(() => this.playTone(freq, 'sine', 0.14, 0.18), idx * 40);
    });
  }

  public bossLightningStrike(): void {
    if (!this.enabled || !this.ctx) return;
    try {
      this.playTone(880, 'sawtooth', 0.08, 0.35);
      setTimeout(() => this.playTone(440, 'square', 0.12, 0.35), 30);
      setTimeout(() => this.playTone(110, 'sawtooth', 0.35, 0.4), 70);
      setTimeout(() => this.playTone(55, 'square', 0.5, 0.45), 140);
    } catch {}
  }

  public bossLaserSweep(): void {
    if (!this.enabled || !this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(600, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1200, this.ctx.currentTime + 0.3);
      osc.frequency.exponentialRampToValueAtTime(400, this.ctx.currentTime + 0.6);
      gain.gain.setValueAtTime(0.2, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.6);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.6);
    } catch {}
  }

  public bossVoidSingularity(): void {
    if (!this.enabled || !this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(180, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(60, this.ctx.currentTime + 0.8);
      gain.gain.setValueAtTime(0.25, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.8);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.8);
    } catch {}
  }

  public bossVictoryFanfare(): void {
    const chords = [
      { notes: [261.63, 329.63, 392.00], delay: 0 },
      { notes: [293.66, 369.99, 440.00], delay: 180 },
      { notes: [329.63, 415.30, 493.88], delay: 360 },
      { notes: [392.00, 493.88, 587.33, 783.99], delay: 600 }
    ];
    chords.forEach(c => {
      setTimeout(() => {
        c.notes.forEach(n => this.playTone(n, 'triangle', 0.45, 0.22));
      }, c.delay);
    });
  }

  public chestOpen(): void {
    const notes = [440, 554.37, 659.25, 880, 1108.73];
    notes.forEach((freq, i) => {
      setTimeout(() => this.playTone(freq, 'triangle', 0.18, 0.25), i * 90);
    });
  }

  // ──  Fishing SFX ──────────────────────────────────────────
  public fishCast(): void {
    this.playTone(380, 'sine', 0.12, 0.18);
    setTimeout(() => this.playTone(220, 'sine', 0.16, 0.12), 40);
    setTimeout(() => this.playTone(150, 'triangle', 0.1, 0.08), 90);
  }

  public fishBite(): void {
    this.playTone(880, 'triangle', 0.08, 0.3);
    setTimeout(() => this.playTone(1320, 'sine', 0.18, 0.35), 60);
  }

  public fishReel(): void {
    this.playTone(550, 'square', 0.03, 0.12);
  }

  public fishCatch(): void {
    const notes = [523.25, 659.25, 783.99, 1046.50];
    notes.forEach((freq, i) => {
      setTimeout(() => this.playTone(freq, 'triangle', 0.2, 0.28), i * 80);
    });
  }

  public fishEscape(): void {
    this.playTone(330, 'sawtooth', 0.15, 0.2);
    setTimeout(() => this.playTone(220, 'sawtooth', 0.2, 0.15), 100);
  }

  // ──  Weather SFX ──────────────────────────────────────────
  public thunder(): void {
    this.playTone(65, 'sawtooth', 0.6, 0.4);
    setTimeout(() => this.playTone(45, 'square', 0.8, 0.35), 100);
    setTimeout(() => this.playTone(30, 'sawtooth', 1.0, 0.25), 250);
  }

  // ──  Juice & Polish SFX ────────────────────────────────────
  public itemPop(): void {
    this.playTone(440, 'triangle', 0.05, 0.18);
    setTimeout(() => this.playTone(880, 'sine', 0.08, 0.22), 30);
  }

  public itemMagnetPickup(): void {
    this.playTone(784, 'sine', 0.04, 0.15);
    setTimeout(() => this.playTone(1174, 'triangle', 0.08, 0.2), 30);
  }

  public critHit(): void {
    this.playTone(180, 'square', 0.1, 0.35);
    setTimeout(() => this.playTone(520, 'sawtooth', 0.15, 0.4), 30);
    setTimeout(() => this.playTone(1046, 'triangle', 0.2, 0.3), 70);
  }

  public questComplete(): void {
    const notes = [523.25, 659.25, 783.99, 1046.50, 1318.51];
    notes.forEach((freq, i) => {
      setTimeout(() => this.playTone(freq, 'triangle', 0.22, 0.28), i * 95);
    });
  }

  public warpSound(): void {
    this.playTone(300, 'sine', 0.15, 0.2);
    setTimeout(() => this.playTone(600, 'triangle', 0.25, 0.25), 80);
    setTimeout(() => this.playTone(900, 'sine', 0.3, 0.2), 160);
  }

  public whistleSound(): void {
    this.playTone(880, 'sine', 0.12, 0.25);
    setTimeout(() => this.playTone(1320, 'sine', 0.25, 0.28), 100);
  }

  public potBreak(): void {
    this.playTone(180, 'sawtooth', 0.08, 0.3);
    setTimeout(() => this.playTone(90, 'square', 0.12, 0.25), 40);
  }

  public dogBark(): void {
    this.playTone(280, 'sawtooth', 0.08, 0.25);
    setTimeout(() => this.playTone(340, 'sawtooth', 0.1, 0.28), 70);
  }

  public catMeow(): void {
    this.playTone(580, 'sine', 0.12, 0.2);
    setTimeout(() => this.playTone(740, 'sine', 0.18, 0.22), 60);
    setTimeout(() => this.playTone(680, 'sine', 0.15, 0.18), 160);
  }

  public sortSound(): void {
    this.playTone(523.25, 'sine', 0.05, 0.15);
    setTimeout(() => this.playTone(659.25, 'triangle', 0.06, 0.18), 40);
    setTimeout(() => this.playTone(783.99, 'sine', 0.08, 0.2), 80);
  }

  public dash(): void {
    if (!this.enabled) return;
    this.playTone(180, 'triangle', 0.08, 0.25);
    setTimeout(() => this.playTone(320, 'sine', 0.12, 0.28), 20);
    setTimeout(() => this.playTone(120, 'triangle', 0.1, 0.15), 60);
  }

  public runeFire(): void {
    this.playTone(120, 'sawtooth', 0.15, 0.28);
    setTimeout(() => this.playTone(220, 'sawtooth', 0.2, 0.22), 40);
  }

  public runeFrost(): void {
    this.playTone(880, 'sine', 0.1, 0.25);
    setTimeout(() => this.playTone(1200, 'triangle', 0.18, 0.22), 30);
  }

  public runeLightning(): void {
    this.playTone(300, 'square', 0.06, 0.35);
    setTimeout(() => this.playTone(600, 'sawtooth', 0.08, 0.3), 30);
    setTimeout(() => this.playTone(950, 'square', 0.12, 0.25), 60);
  }

  public runeVampiric(): void {
    this.playTone(140, 'sine', 0.2, 0.25);
    setTimeout(() => this.playTone(280, 'sine', 0.25, 0.28), 50);
  }

  public cameraShutter(): void {
    this.playTone(800, 'square', 0.03, 0.35);
    setTimeout(() => this.playTone(300, 'triangle', 0.08, 0.3), 40);
  }

  public shrineEpilogue(): void {
    const notes = [261.63, 329.63, 392.00, 523.25, 659.25, 783.99, 1046.50];
    notes.forEach((freq, i) => {
      setTimeout(() => this.playTone(freq, 'triangle', 0.45, 0.32), i * 140);
    });
  }

  public spirePortal(): void {
    const notes = [349.23, 440.00, 523.25, 698.46, 880.00];
    notes.forEach((freq, i) => {
      setTimeout(() => this.playTone(freq, 'sine', 0.28, 0.22), i * 80);
    });
  }

  // Dark Souls Audio Effects
  public youDied(): void {
    if (!this.enabled) return;
    this.init();
    // Deep dark gong & minor toll
    this.playTone(55.0, 'sawtooth', 1.8, 0.55);
    this.playTone(73.42, 'triangle', 2.0, 0.45);
    setTimeout(() => this.playTone(87.31, 'sine', 1.6, 0.4), 200);
    setTimeout(() => this.playTone(65.41, 'triangle', 2.4, 0.5), 500);
  }

  public bloodstainReclaim(): void {
    if (!this.enabled) return;
    const chime = [523.25, 659.25, 783.99, 987.77, 1046.50];
    chime.forEach((freq, i) => {
      setTimeout(() => this.playTone(freq, 'triangle', 0.4, 0.35), i * 90);
    });
  }

  public bossHealPunishRoar(): void {
    if (!this.enabled) return;
    this.playTone(80, 'sawtooth', 0.4, 0.5);
    setTimeout(() => this.playTone(160, 'sawtooth', 0.35, 0.45), 60);
    setTimeout(() => this.playTone(60, 'sawtooth', 0.5, 0.4), 140);
  }

  // Active Player Skills Audio
  public skillCast(): void {
    if (!this.enabled) return;
    this.init();
    this.playTone(440, 'triangle', 0.12, 0.3);
    setTimeout(() => this.playTone(660, 'sine', 0.18, 0.35), 40);
  }

  public ultimateCast(): void {
    if (!this.enabled) return;
    this.init();
    this.playTone(220, 'sawtooth', 0.35, 0.5);
    setTimeout(() => this.playTone(330, 'triangle', 0.35, 0.45), 80);
    setTimeout(() => this.playTone(554.37, 'sine', 0.6, 0.55), 160);
    setTimeout(() => this.playTone(880, 'sine', 0.8, 0.6), 260);
  }

  public skillUpgrade(): void {
    if (!this.enabled) return;
    this.init();
    [523.25, 659.25, 783.99, 1046.50].forEach((freq, i) => {
      setTimeout(() => this.playTone(freq, 'triangle', 0.22, 0.35), i * 70);
    });
  }

  // Guard & Perfect Parry System Audio
  public shieldUp(): void {
    if (!this.enabled) return;
    this.init();
    this.playTone(320, 'triangle', 0.08, 0.25);
    setTimeout(() => this.playTone(480, 'sine', 0.1, 0.2), 30);
  }

  public shieldBlock(): void {
    if (!this.enabled) return;
    this.init();
    this.playTone(160, 'square', 0.1, 0.45);
    setTimeout(() => this.playTone(110, 'triangle', 0.18, 0.4), 25);
  }

  public parrySuccess(): void {
    if (!this.enabled) return;
    this.init();
    // High-pitched crystal metallic clash (Dark Souls parry ring)
    this.playTone(1320, 'sine', 0.4, 0.65);
    this.playTone(1760, 'triangle', 0.35, 0.6);
    setTimeout(() => this.playTone(2093, 'sine', 0.5, 0.7), 40);
    setTimeout(() => this.playTone(880, 'triangle', 0.6, 0.4), 80);
  }

  public guardBreak(): void {
    if (!this.enabled) return;
    this.init();
    this.playTone(120, 'sawtooth', 0.25, 0.55);
    setTimeout(() => this.playTone(85, 'square', 0.35, 0.5), 50);
  }

  public gulp(): void {
    if (!this.enabled) return;
    this.init();
    this.playTone(320, 'sine', 0.12, 0.25);
    setTimeout(() => this.playTone(480, 'sine', 0.14, 0.22), 60);
    setTimeout(() => this.playTone(600, 'sine', 0.16, 0.25), 130);
  }
}

export const SoundEngine = new SoundEngineService();
