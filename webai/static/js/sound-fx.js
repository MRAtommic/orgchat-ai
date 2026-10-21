// =====================================================================
// OrgChat AI — Audio & Haptic Feedback Engine (Web Audio API)
// =====================================================================

class OrgAudioEngine {
  constructor() {
    this.ctx = null;
    this.soundEnabled = localStorage.getItem('orgchat_sound_fx') !== 'false';
    this.hapticEnabled = localStorage.getItem('orgchat_haptic_fx') !== 'false';
    this._lastTypeSound = 0;
  }

  _initCtx() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  triggerHaptic(type = 'light') {
    if (!this.hapticEnabled || !navigator.vibrate) return;
    try {
      if (type === 'light') navigator.vibrate(8);
      else if (type === 'medium') navigator.vibrate(15);
      else if (type === 'success') navigator.vibrate([10, 30, 15]);
      else if (type === 'error') navigator.vibrate([20, 50, 20]);
    } catch (e) {}
  }

  playTypingClick() {
    if (!this.soundEnabled) return;
    const now = Date.now();
    if (now - this._lastTypeSound < 60) return; // throttle
    this._lastTypeSound = now;

    try {
      this._initCtx();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      // Soft mechanical typewriter click pitch
      const freq = 350 + Math.random() * 120;
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(80, this.ctx.currentTime + 0.025);

      gain.gain.setValueAtTime(0.015, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.025);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + 0.03);
    } catch (e) {}
  }

  playStreamTick() {
    if (!this.soundEnabled) return;
    const now = Date.now();
    if (now - this._lastTypeSound < 90) return;
    this._lastTypeSound = now;

    try {
      this._initCtx();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(520 + Math.random() * 60, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(200, this.ctx.currentTime + 0.02);

      gain.gain.setValueAtTime(0.008, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.02);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + 0.025);
    } catch (e) {}
  }

  playSendChime() {
    this.triggerHaptic('medium');
    if (!this.soundEnabled) return;
    try {
      this._initCtx();
      if (!this.ctx) return;

      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(380, now);
      osc.frequency.exponentialRampToValueAtTime(620, now + 0.12);

      gain.gain.setValueAtTime(0.035, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.14);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.15);
    } catch (e) {}
  }

  playReceiveChime() {
    this.triggerHaptic('success');
    if (!this.soundEnabled) return;
    try {
      this._initCtx();
      if (!this.ctx) return;

      const now = this.ctx.currentTime;

      // Two-tone bright notification bell
      [580, 880].forEach((freq, i) => {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        const startTime = now + (i * 0.08);

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, startTime);

        gain.gain.setValueAtTime(0.03, startTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, startTime + 0.22);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(startTime);
        osc.stop(startTime + 0.25);
      });
    } catch (e) {}
  }
}

window.soundEngine = new OrgAudioEngine();
