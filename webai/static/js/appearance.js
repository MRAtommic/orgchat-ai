// =====================================================================
// OrgChat AI — Personal Appearance & Custom UI Settings
// =====================================================================

const FONT_MAP = {
  'Inter': "'Inter', sans-serif",
  'Anuphan': "'Anuphan', sans-serif",
  'IBM Plex Sans Thai': "'IBM Plex Sans Thai', sans-serif",
  'Prompt': "'Prompt', sans-serif",
  'Kanit': "'Kanit', sans-serif",
  'Noto Sans Thai': "'Noto Sans Thai', sans-serif",
  'Krub': "'Krub', sans-serif",
  'K2D': "'K2D', sans-serif",
  'Fahkwang': "'Fahkwang', sans-serif",
  'Mitr': "'Mitr', sans-serif",
  'Athiti': "'Athiti', sans-serif",
  'Bai Jamjuree': "'Bai Jamjuree', sans-serif",
  'Pridi': "'Pridi', serif",
  'Chakra Petch': "'Chakra Petch', sans-serif",
  'Sarabun': "'Sarabun', sans-serif",
  'Niramit': "'Niramit', sans-serif",
  'Mali': "'Mali', cursive, sans-serif"
};

const FONT_SIZE_MAP = {
  'small': { size: '13px', label: 'เล็ก (13px)' },
  'normal': { size: '14.5px', label: 'ปกติ (14.5px)' },
  'large': { size: '16px', label: 'ใหญ่ (16px)' },
  'xl': { size: '18px', label: 'ใหญ่มาก (18px)' }
};

function initCustomUISettings() {
  const savedFont = localStorage.getItem('custom_font_family') || 'Sarabun';
  const savedSize = localStorage.getItem('custom_font_size') || 'normal';
  const savedAccent = localStorage.getItem('custom_accent_color') || 'indigo';

  setCustomFont(savedFont, false);
  setCustomFontSize(savedSize, false);
  setCustomAccent(savedAccent, false);

  // Sound & Haptic switches sync
  const soundToggle = document.getElementById('soundFxToggle');
  if (soundToggle && window.soundEngine) {
    soundToggle.checked = window.soundEngine.soundEnabled;
    soundToggle.onchange = (e) => {
      window.soundEngine.soundEnabled = e.target.checked;
      localStorage.setItem('orgchat_sound_fx', e.target.checked);
      if (e.isTrusted && e.target.checked) window.soundEngine.playSendChime();
    };
  }

  const hapticToggle = document.getElementById('hapticFxToggle');
  if (hapticToggle && window.soundEngine) {
    hapticToggle.checked = window.soundEngine.hapticEnabled;
    hapticToggle.onchange = (e) => {
      window.soundEngine.hapticEnabled = e.target.checked;
      localStorage.setItem('orgchat_haptic_fx', e.target.checked);
      if (e.isTrusted && e.target.checked) window.soundEngine.triggerHaptic('success');
    };
  }
}

function setCustomFont(fontName, save = true) {
  const fontCss = FONT_MAP[fontName] || FONT_MAP['Sarabun'];
  document.documentElement.style.setProperty('--user-font-family', fontCss);
  document.body.style.fontFamily = fontCss;

  if (save) localStorage.setItem('custom_font_family', fontName);

  document.querySelectorAll('.custom-font-btn').forEach(btn => {
    btn.classList.remove('border-indigo-500', 'ring-2', 'ring-indigo-500/20', 'bg-indigo-50/50', 'dark:bg-indigo-950/20');
  });

  const activeBtn = document.getElementById(`fontBtn-${fontName}`);
  if (activeBtn) {
    activeBtn.classList.add('border-indigo-500', 'ring-2', 'ring-indigo-500/20', 'bg-indigo-50/50', 'dark:bg-indigo-950/20');
  }
}

function setCustomFontSize(sizeKey, save = true) {
  const sizeObj = FONT_SIZE_MAP[sizeKey] || FONT_SIZE_MAP['normal'];
  document.documentElement.style.fontSize = sizeObj.size;

  if (save) localStorage.setItem('custom_font_size', sizeKey);

  const displayEl = document.getElementById('fontSizeDisplay');
  if (displayEl) displayEl.textContent = sizeObj.label;

  document.querySelectorAll('.custom-size-btn').forEach(btn => {
    btn.classList.remove('bg-indigo-600', 'text-white', 'border-indigo-600');
    btn.classList.add('border-surface-200', 'dark:border-surface-700', 'text-surface-700', 'dark:text-surface-300');
  });

  const activeBtn = document.getElementById(`fontSizeBtn-${sizeKey}`);
  if (activeBtn) {
    activeBtn.classList.remove('border-surface-200', 'dark:border-surface-700', 'text-surface-700', 'dark:text-surface-300');
    activeBtn.classList.add('bg-indigo-600', 'text-white', 'border-indigo-600');
  }
}

function setCustomAccent(colorName, save = true) {
  if (save) localStorage.setItem('custom_accent_color', colorName);

  document.querySelectorAll('.custom-accent-btn').forEach(btn => {
    btn.classList.remove('ring-4', 'ring-offset-2', 'ring-slate-400');
    const check = btn.querySelector('.accent-check');
    if (check) check.classList.add('hidden');
  });

  const activeBtn = document.getElementById(`accentBtn-${colorName}`);
  if (activeBtn) {
    activeBtn.classList.add('ring-4', 'ring-offset-2', 'ring-slate-400');
    const check = activeBtn.querySelector('.accent-check');
    if (check) check.classList.remove('hidden');
  }
}

function resetCustomUISettings() {
  setCustomFont('Sarabun');
  setCustomFontSize('normal');
  setCustomAccent('indigo');
  if (typeof toast === 'function') toast('คืนค่าการแสดงผลเริ่มต้นเรียบร้อย', 'info');
}

document.addEventListener('DOMContentLoaded', initCustomUISettings);

// Window Exports
window.setCustomFont = setCustomFont;
window.setCustomFontSize = setCustomFontSize;
window.setCustomAccent = setCustomAccent;
window.resetCustomUISettings = resetCustomUISettings;
window.initCustomUISettings = initCustomUISettings;
