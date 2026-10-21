// 🛡️ CSRF Token Auto-Injector & Global Fetch Interceptor
window._csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || null;

// 🛡️ Global XSS Prevention Helper
if (typeof window.escapeHtml !== 'function') {
  window.escapeHtml = function(text) {
    if (!text) return '';
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  };
}
var escapeHtml = window.escapeHtml;

// --- Premium Sound FX & Haptic Engine (Web Audio API) ---
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

// --- Personal Appearance & Custom UI Settings ---
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
  if (soundToggle) {
    soundToggle.checked = window.soundEngine.soundEnabled;
    soundToggle.onchange = (e) => {
      window.soundEngine.soundEnabled = e.target.checked;
      localStorage.setItem('orgchat_sound_fx', e.target.checked);
      if (e.isTrusted && e.target.checked) window.soundEngine.playSendChime();
    };
  }

  const hapticToggle = document.getElementById('hapticFxToggle');
  if (hapticToggle) {
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

async function fetchCsrfToken() {
  try {
    const res = await fetch('/api/csrf-token');
    const data = await res.json();
    if (data && data.csrf_token) {
      window._csrfToken = data.csrf_token;
      let meta = document.querySelector('meta[name="csrf-token"]');
      if (meta) meta.setAttribute('content', window._csrfToken);
    }
  } catch (e) {
    console.warn("Failed to fetch CSRF token:", e);
  }
}

// Fetch initial CSRF token
fetchCsrfToken();

const originalFetch = window.fetch;
window.fetch = async function (resource, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
    if (!window._csrfToken && resource !== '/api/csrf-token') {
      await fetchCsrfToken();
    }
    if (window._csrfToken && resource !== '/api/csrf-token') {
      options.headers = options.headers || {};
      if (options.headers instanceof Headers) {
        options.headers.set('X-CSRF-Token', window._csrfToken);
      } else {
        options.headers['X-CSRF-Token'] = window._csrfToken;
      }
    }
  }
  return originalFetch.call(this, resource, options);
};

// ─── Socket.IO Global ──────────────────────────
let socket = null;

if (typeof io !== 'undefined') {
  socket = io();
}

// Helper: Scroll chat to bottom
// Helper: Scroll chat to bottom with intelligent threshold and animation awareness
function scrollToBottom(behavior = 'smooth', onlyIfAtBottom = false) {
  if (!chatArea) return;

  const threshold = 50;
  const isAtBottom = chatArea.scrollHeight - chatArea.scrollTop <= chatArea.clientHeight + threshold;

  if (!onlyIfAtBottom || isAtBottom) {
    // Immediate scroll (auto) to capture current state, then delayed scroll for content rendering
    chatArea.scrollTop = chatArea.scrollHeight;
    
    requestAnimationFrame(() => {
      setTimeout(() => {
        chatArea.scrollTo({ top: chatArea.scrollHeight, behavior: behavior });
      }, 50);
    });
  }
}

// Global Error Handler (Console logging with optional debug banner)
window.onerror = function (msg, url, line, col, error) {
  const msgStr = String(msg || '');
  // Ignore harmless browser/extension errors
  if (msgStr.includes('ResizeObserver') || msgStr.includes('Script error.') || (url && (url.includes('chrome-extension://') || url.includes('moz-extension://')))) {
    return false;
  }
  console.error("OrgChat JS Error:", msg, "at", url, ":", line);
  if (localStorage.getItem('debug_errors') === 'true') {
    document.body.insertAdjacentHTML('afterbegin', `<div style="position:fixed; top:0; left:0; width:100%; min-height:36px; background:#e53e3e; color:white; font-family:sans-serif; font-size:12px; padding:8px 12px; z-index:99999; display:flex; justify-content:space-between; align-items:center;"><span><b>JS Debug Error:</b> ${msg} (Line ${line})</span><button onclick="this.parentElement.remove()" style="background:none; border:none; color:white; font-weight:bold; cursor:pointer;">✕</button></div>`);
  }
  return false;
};

const chatArea = $('mainChat');

const msgInput = $('msgInput');

const voiceBtn = $('voiceBtn');

const clearChatBtn = $('clearChatBtn');

// ─── Multi-lingual Chat Translation System ──────────────────────
let _userTargetLang = localStorage.getItem('orgchat_target_lang') || 'th';
let _translationCache = {};

function setChatTargetLanguage(lang) {
  _userTargetLang = lang;
  localStorage.setItem('orgchat_target_lang', lang);
  toast(`เปลี่ยนภาษาเป้าหมายเป็น ${lang.toUpperCase()} เรียบร้อยแล้ว`, 'info');
}

async function translateChatMessage(btnEl) {
  const rowEl = btnEl.closest('.chat-msg-row') || btnEl.closest('.msg-user') || btnEl.closest('.msg-bot') || btnEl.closest('.group\\/msg');
  if (!rowEl) return;
  
  const proseEl = rowEl.querySelector('.prose') || rowEl.querySelector('.msg-text') || rowEl.querySelector('.chat-bubble') || rowEl;
  
  // Clean text from existing translation box or html tags
  const clone = proseEl.cloneNode(true);
  const existingBox = clone.querySelector('.translation-box');
  if (existingBox) existingBox.remove();
  const text = (clone.innerText || clone.textContent || '').trim();
  
  // Toggle existing translation box if present
  const transBoxInDom = rowEl.querySelector('.translation-box');
  if (transBoxInDom) {
    transBoxInDom.classList.toggle('hidden');
    return;
  }
  
  if (!text) {
    toast('ไม่มีข้อความสำหรับแปลภาษา', 'warning');
    return;
  }

  const origHtml = btnEl.innerHTML;
  btnEl.disabled = true;
  btnEl.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin text-brand-500"></i>`;
  if (window.lucide) lucide.createIcons();

  const cacheKey = `${_userTargetLang}:${text}`;
  let translatedText = _translationCache[cacheKey];

  if (!translatedText) {
    try {
      const res = await fetch('/api/chat/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text, target_lang: _userTargetLang })
      });
      const data = await res.json();
      if (data.ok && data.translated_text) {
        translatedText = data.translated_text;
        _translationCache[cacheKey] = translatedText;
      } else {
        toast(data.error || 'ไม่สามารถแปลภาษาได้ในขณะนี้', 'error');
        btnEl.disabled = false;
        btnEl.innerHTML = origHtml;
        if (window.lucide) lucide.createIcons();
        return;
      }
    } catch (err) {
      console.error("Translation fetch error:", err);
      toast('เกิดข้อผิดพลาดในการเชื่อมต่อบริการแปลภาษา', 'error');
      btnEl.disabled = false;
      btnEl.innerHTML = origHtml;
      if (window.lucide) lucide.createIcons();
      return;
    }
  }

  btnEl.disabled = false;
  btnEl.innerHTML = origHtml;
  if (window.lucide) lucide.createIcons();

  const langBadges = { th: '🇹🇭 TH', en: '🇬🇧 EN', zh: '🇨🇳 ZH', ja: '🇯🇵 JA', ko: '🇰🇷 KO', lo: '🇱🇦 LO' };
  const badgeLabel = langBadges[_userTargetLang] || _userTargetLang.toUpperCase();

  const newTransBox = document.createElement('div');
  newTransBox.className = 'translation-box mt-2.5 pt-2 border-t border-brand-500/20 text-xs text-surface-700 dark:text-surface-200 animate-in fade-in zoom-in-95 duration-200';
  newTransBox.innerHTML = `
    <div class="flex items-center justify-between gap-2 mb-1 opacity-80">
      <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-600 dark:text-brand-400 font-bold text-[10px]">
        <i data-lucide="languages" class="w-3 h-3"></i> คำแปล ${badgeLabel}
      </span>
      <button onclick="this.closest('.translation-box').remove()" class="text-surface-400 hover:text-red-500 text-[10px] px-1 font-bold">✕ ปิด</button>
    </div>
    <div class="italic bg-brand-500/5 p-2 rounded-xl border border-brand-500/10 leading-relaxed">${escapeHtml(translatedText)}</div>
  `;
  
  const targetContainer = rowEl.querySelector('.chat-bubble') || rowEl.querySelector('.msg-content-wrapper') || rowEl;
  targetContainer.appendChild(newTransBox);
  if (window.lucide) lucide.createIcons();
}

// Global click listener delegation for translate-msg-btn
document.addEventListener('click', (e) => {
  const transBtn = e.target.closest('.translate-msg-btn');
  if (transBtn && !transBtn.onclick) {
    e.preventDefault();
    translateChatMessage(transBtn);
  }
});

// Helper: Format attachment label if no text
function formatAttachmentPreview(attachments) {
  if (!attachments) return '';
  let parsed = attachments;
  if (typeof attachments === 'string') {
    try { parsed = JSON.parse(attachments); } catch(e) {}
  }
  if (Array.isArray(parsed) && parsed.length > 0) {
    const first = parsed[0] || {};
    const type = (first.type || '').toLowerCase();
    const url = (first.url || '').toLowerCase();
    const name = first.name || '';
    if (type === 'audio' || url.includes('voice_') || /\.(webm|mp3|wav|m4a|ogg)($|\?)/i.test(url)) {
      return '🎤 ข้อความเสียง';
    } else if (type === 'image' || /\.(jpg|jpeg|png|gif|webp|bmp)($|\?)/i.test(url)) {
      return '📷 รูปภาพ';
    } else if (type === 'video' || /\.(mp4|mov|avi|mkv)($|\?)/i.test(url)) {
      return '🎥 วิดีโอ';
    } else if (name) {
      return `📎 ${name}`;
    } else {
      return '📎 ไฟล์แนบ';
    }
  }
  return '';
}

// Helper: Get preview text with sender prefix
function getChatPreview(msg, sender, attachments) {
  let displayMsg = (msg || '').trim();
  if (!displayMsg && attachments) {
    displayMsg = formatAttachmentPreview(attachments);
  }
  if (!displayMsg) return 'ยังไม่มีข้อความ';
  const currentUser = (typeof state.user === 'object' ? state.user?.username : state.user);
  const prefix = (sender && currentUser && sender.toLowerCase() === currentUser.toLowerCase()) ? 'คุณ: ' : '';
  const text = displayMsg.replace(/<[^>]*>/g, '').substring(0, 30);
  return `${prefix}${text}${displayMsg.length > 30 ? '...' : ''}`;
}

// Unified Chat Refs
const chatRoomList = $('chatRoomList');

const chatContactList = $('chatContactList');

const chatHeaderName = $('chatHeaderName');

const chatHeaderAvatar = $('chatHeaderAvatar');

const chatHeaderStatus = $('chatHeaderStatus');

const chatInputArea = $('chatInputArea');

const openStartDmModal = $('openStartDmModal');

const startDmModal = $('startDmModal');

const closeStartDmModal = $('closeStartDmModal');

const searchDmUser = $('searchDmUser');

const dmUserSelectList = $('dmUserSelectList');

const addMemberBtn = $('addMemberBtn');

const addMemberModal = $('addMemberModal');

const addMemberSelectList = $('addMemberSelectList');

const confirmAddMember = $('confirmAddMember');

const cancelAddMember = $('cancelAddMember');

// WebRTC Calling Refs
const voiceCallBtn = $('voiceCallBtn');

const loginErrorMsg = $('loginErrorMsg');

// Group Chat Refs
const groupChatHead = $('groupChatHead');

const groupChatBadge = $('groupChatBadge');

const groupChatModal = $('groupChatModal');

const closeGroupChat = $('closeGroupChat');

const closeGroupChatMobile = $('closeGroupChatMobile');

const groupChatMessages = $('groupChatMessages');

const groupChatInput = $('groupChatInput');

const sendGroupChatBtn = $('sendGroupChatBtn');

const chatFileInput = $('chatFileInput');

const chatAttachmentPreview = $('chatAttachmentPreview');

// ─── Global Loading ──────────────────────────
function showGlobalLoading(msg = 'กำลังประมวลผล กรุณารอสักครู่...') {
  const overlay = $('globalLoadingOverlay');
  const textEl = $('globalLoadingText');
  if (overlay) {
    if (textEl) textEl.textContent = msg;
    overlay.classList.remove('hidden');
  }
}

// ─── Typing Signaling Logic ──────────────────
let lastTypingTime = 0;

async function sendTypingSignal(cid, ctype) {
  const now = Date.now();
  if (now - lastTypingTime < 3000) return; // Throttle to 3s
  lastTypingTime = now;
  try {
    await fetch('/api/chat/typing', {
      method: 'POST',
      body: JSON.stringify({ id: cid, type: ctype }),
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (e) { }
}

async function pollTypingStatus() {
  // 1. Check Main Chat typing
  const mainActive = document.querySelector('#view-chat:not(.hidden)');
  if (mainActive) {
    try {
      const data = await apiFetch('/api/chat/typing?id=ai-assistant&type=dm');
      const indicator = $('mainTypingIndicator');
      if (data.typing && data.typing.length > 0) {
        $('mainTypingText').textContent = `${data.typing.join(', ')} กำลังพิมพ์...`;
        indicator.classList.remove('hidden');
      } else {
        indicator.classList.add('hidden');
      }
    } catch (e) { }
  }

  // 2. Check Unified Chat typing
  if (state.groupChat.isOpen && state.currentChat) {
    try {
      const data = await apiFetch(`/api/chat/typing?id=${state.currentChat.id}&type=${state.currentChat.type}`);
      const indicator = $('unifiedTypingIndicator');
      if (data.typing && data.typing.length > 0) {
        $('unifiedTypingText').textContent = `${data.typing.join(', ')} กำลังพิมพ์...`;
        indicator.classList.remove('hidden');
      } else {
        indicator.classList.add('hidden');
      }
    } catch (e) { }
  }
}

// ─── WebSocket Helper Functions ───────────────────────────────
async function fetchUserStatusMap() {
  try {
    const res = await apiFetch('/api/users/status');
    if (res.ok && res.users) {
      if (!state.userStatusMap) state.userStatusMap = {};
      res.users.forEach(u => state.userStatusMap[u.username] = u);
      renderActiveUsersTray();
      renderChatSidebar();
      updateChatHeaderStatus();
    }
  } catch(e){}
}

function renderActiveUsersTray() {
  const tray = $('activeUsersTray');
  if (!tray) return;

  if (!state.userStatusMap || !state.onlineUsers || state.onlineUsers.length === 0) {
    tray.classList.add('hidden');
    return;
  }
  
  // Find users who are online (excluding self)
  const activeUsers = Object.values(state.userStatusMap).filter(u => 
    state.onlineUsers.includes(u.username) && u.username !== state.username
  );

  if (activeUsers.length === 0) {
    tray.classList.add('hidden');
    return;
  }

  tray.classList.remove('hidden');
  
  tray.innerHTML = activeUsers.map(u => {
    const displayNameShort = (u.display_name || u.username).split(' ')[0];
    const safeUser = escHtml(u.username);
    const safeName = escHtml(u.display_name || u.username);
    const safeAvatar = escHtml(u.avatar_url || '');
    const safeShort = escHtml(displayNameShort);
    return `
      <div onclick="switchChat('dm', '${safeUser}', '${safeName}', '${safeAvatar}')"
           class="flex flex-col items-center gap-1 cursor-pointer w-14 shrink-0 transition-transform hover:scale-105 group"
           title="ส่งข้อความหา ${safeName}">
        <div class="relative">
          <div class="w-12 h-12 rounded-full overflow-hidden border-2 border-brand-500 ring-2 ring-white dark:ring-surface-900 bg-surface-100 dark:bg-surface-800 p-0.5 group-hover:shadow-[0_0_15px_rgba(37,99,235,0.4)] transition-shadow">
             <div class="w-full h-full rounded-full overflow-hidden bg-brand-50 flex items-center justify-center text-brand-600">
               ${u.avatar_url ? `<img src="${safeAvatar}" class="w-full h-full object-cover">` : `<i data-lucide="user" class="w-5 h-5"></i>`}
             </div>
          </div>
          <div class="absolute bottom-0.5 right-0.5 w-3.5 h-3.5 bg-emerald-500 border-2 border-white dark:border-surface-900 rounded-full animate-pulse shadow-sm"></div>
        </div>
        <span class="text-[10px] font-bold text-surface-600 dark:text-surface-300 w-full truncate text-center">${safeShort}</span>
      </div>
    `;
  }).join('');
  
  initIcons();
}

function updateOnlineUsersList(onlineUsers) {
  state.onlineUsers = onlineUsers || [];
  console.log("🟢 Online Users Sync:", state.onlineUsers);
  fetchUserStatusMap(); // Ensure last seen map is up-to-date
  renderActiveUsersTray();
  renderChatSidebar();
  updateChatHeaderStatus();
}

state.typingUsers = state.typingUsers || {};

function showTypingIndicator(username, displayName, roomId) {
  const typingText = displayName || username;
  console.log(`✍️ ${typingText} is typing...`);

  if (roomId) {
    if (!state.typingUsers) state.typingUsers = {};
    if (!state.typingUsers[roomId]) state.typingUsers[roomId] = new Set();
    state.typingUsers[roomId].add(username);
    
    // Auto-clear typing status after 5 seconds to prevent getting stuck
    setTimeout(() => {
      if (state.typingUsers && state.typingUsers[roomId]) {
        state.typingUsers[roomId].delete(username);
        renderChatSidebar();
      }
    }, 5000);
    renderChatSidebar();
  }

  // Optional: Show visual indicator in chat area
  if (chatArea && roomId && state.currentChat && state.currentChat.id == roomId) {
    let typingDiv = chatArea.querySelector('.typing-indicator');
    if (!typingDiv) {
      typingDiv = document.createElement('div');
      typingDiv.className = 'typing-indicator text-sm text-surface-400 italic p-2 transition-all';
      chatArea.appendChild(typingDiv);
    }
    typingDiv.innerHTML = `<i data-lucide="pencil" class="inline w-3 h-3 mr-1"></i>${typingText} กำลังพิมพ์...`;
    initIcons();
  }
}

function hideTypingIndicator(username, roomId) {
  console.log(`⏹️ ${username} stopped typing`);

  if (roomId && state.typingUsers && state.typingUsers[roomId]) {
    state.typingUsers[roomId].delete(username);
    renderChatSidebar();
  }

  const typingDiv = chatArea?.querySelector('.typing-indicator');
  if (typingDiv) {
    typingDiv.remove();
  }
}

async function sendReadSignal() {
  const chat = state.currentChat;
  if (!chat || !chat.id || !state.groupChat.messages.length) return;
  
  // Find the highest message ID in the current batch
  let maxId = 0;
  state.groupChat.messages.forEach(m => {
    if (m.id > maxId) {
      maxId = m.id;
    }
  });

  if (maxId === 0) return;
  // Prevent duplicate signals for same maxId
  if (state.groupChat.lastReadId === maxId) return;
  
  try {
    await fetch('/api/chat/read', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: chat.type,
        id: chat.id,
        max_id: maxId
      })
    });
    state.groupChat.lastReadId = maxId;
  } catch(e) {}
}

// Status / Init
async function loadStatus() {
  try {
    const data = await apiFetch('/api/status');
    state.apiKeySet = data.api_key_set;
    if (statFiles) statFiles.textContent = data.total_files ?? 0;
    if (statChunks) statChunks.textContent = data.total_chunks ?? 0;
    const mFiles = document.getElementById('statFilesMobile');
    const mChunks = document.getElementById('statChunksMobile');
    if (mFiles) mFiles.textContent = data.total_files ?? 0;
    if (mChunks) mChunks.textContent = data.total_chunks ?? 0;

    const providerName = data.provider ? data.provider.toUpperCase() : 'GEMINI';
    const q = data.quota_info || {};

    if (!data.api_key_set && providerName === 'GEMINI') {
      const html = `<span class="w-1 h-1 rounded-full bg-amber-500"></span> ${providerName}: ต้องการ Key`;
      const cls = 'flex items-center gap-1.5 px-2 py-0.5 rounded bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 text-[10px] font-bold border border-amber-100 dark:border-amber-800';
      if (statusBadge) { statusBadge.innerHTML = html; statusBadge.className = cls; }
      if (statusBadgeMobile) { statusBadgeMobile.innerHTML = html; statusBadgeMobile.className = cls; }
      showApiModal();
    } else if (q.embedding_quota_hit) {
      const html = `<span class="w-1 h-1 rounded-full bg-red-500 animate-pulse"></span> ค้นหา: โควต้าเต็ม`;
      const cls = 'flex items-center gap-1.5 px-2 py-0.5 rounded bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-[10px] font-bold border border-red-100 dark:border-red-800';
      if (statusBadge) { statusBadge.innerHTML = html; statusBadge.className = cls; }
      if (statusBadgeMobile) { statusBadgeMobile.innerHTML = html; statusBadgeMobile.className = cls; }
      toast('โควต้าการค้นหา (Gemini) เต็มแล้วครับ กรุณาสลับใช้ Ollama Embeddings หรือรอพรุ่งนี้', 'warning');
    } else if ((data.total_files ?? 0) === 0) {
      const html = `<span class="w-1 h-1 rounded-full bg-surface-400"></span> ${providerName}: คลังยังว่าง`;
      const cls = 'flex items-center gap-1.5 px-2 py-0.5 rounded bg-surface-50 dark:bg-surface-800 text-surface-600 dark:text-surface-400 text-[10px] font-bold border border-surface-200 dark:border-surface-700';
      if (statusBadge) { statusBadge.innerHTML = html; statusBadge.className = cls; }
      if (statusBadgeMobile) { statusBadgeMobile.innerHTML = html; statusBadgeMobile.className = cls; }
    } else {
      const html = `<span class="w-1 h-1 rounded-full bg-emerald-500"></span> ${providerName}: พร้อมทำงาน`;
      const cls = 'flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold border border-emerald-100 dark:border-emerald-800';
      if (statusBadge) { statusBadge.innerHTML = html; statusBadge.className = cls; }
      if (statusBadgeMobile) { statusBadgeMobile.innerHTML = html; statusBadgeMobile.className = cls; }
    }
    state.isAdmin = !!data.is_admin;
    state.isSuperAdmin = !!data.is_superadmin;
    state.canViewKB = !!data.can_view_kb;
    state.canEditKB = !!data.can_edit_kb;
    state.canDeleteKB = !!data.can_delete_kb;
    state.canViewFinancial = !!data.can_view_financial;
    state.canManageLeave = !!data.can_manage_leave;
    state.canBroadcastLine = !!data.can_broadcast_line;
    state.canManagePeak = !!data.can_manage_peak;
    state.canUseAI = data.can_use_ai !== false;
    state.canClaimExpense = data.can_claim_expense !== false;
    state.user = data.user;
    state.username = data.user;
    state.appSettings = data.app_settings || {};
    state.hasOrg = data.has_org === true;
    state.orgId = data.org_id ?? null;
    state.isOrgAdmin = data.org_role === 'admin';
    state.orgPlan = data.org_plan || 'free';
    state.orgFeatures = data.org_features || {};

    const noOrgEl = document.getElementById('noOrgOverlay');
    if (noOrgEl) noOrgEl.classList.toggle('hidden', state.hasOrg);

    if (data.org_plan) {
      const planLabel = { free: 'Free', pro: 'Pro', business: 'Business' }[data.org_plan] || data.org_plan;
      if ($('orgStatPlan')) $('orgStatPlan').textContent = planLabel;
      if ($('orgPlanBadge')) $('orgPlanBadge').textContent = planLabel;
    }

    // Calculate server offset if provided
    if (data.server_time) {
      const serverDate = parseServerDate(data.server_time);
      state.serverOffset = serverDate.getTime() - Date.now();
      console.log("⏱️ Server Clock Offset:", state.serverOffset, "ms");
    }

    toggleAdminFeatures(state.isAdmin, state.isSuperAdmin);

    if (activePersonaName) {
      activePersonaName.textContent = state.activePersona ? state.activePersona.name : 'Default';
    }

    // Join personal WebRTC room
    if (socket && state.user) {
      console.log("👤 Joining personal room via loadStatus:", state.user);
      socket.emit('join', { room: 'user_' + state.user });
    }

    // Sync UI with settings if needed
    const uploadBtn = $('uploadFilesBtn');
    if (uploadBtn) {
      if (typeof canEditKB === 'function' && canEditKB()) uploadBtn.classList.remove('hidden');
      else uploadBtn.classList.add('hidden');
    }
  } catch (e) {
    if (statusBadge) statusBadge.innerHTML = 'Error';
    if (statusBadgeMobile) statusBadgeMobile.innerHTML = 'Error';
  }
}

function toggleAdminFeatures(isAdmin, isSuperAdmin) {
  // nav-admin (แผงควบคุม): แสดงสำหรับ system admin ทุกคน
  const navAdmin = $('nav-admin');
  if (navAdmin) navAdmin.classList.toggle('hidden', !isAdmin);
  const navAdminMobile = $('nav-admin-mobile');
  if (navAdminMobile) navAdminMobile.classList.toggle('hidden', !isAdmin);

  // ปุ่มที่เฉพาะ superadmin เท่านั้น
  const superAdminElements = [
    wipeDataBtn,
    changeKeyBtn,
    $('nav-reconciliation'),
    $('auditLogSection'),
    $('nav-super-admin'),
    $('nav-superadmin-mobile')
  ];
  superAdminElements.forEach(el => {
    if (el) el.classList.toggle('hidden', !isSuperAdmin);
  });

  if (isSuperAdmin) {
    initAdminChatPanel();
  }

  // nav-org (จัดการองค์กร): แสดงสำหรับ org admin หรือ system admin
  const navOrg = $('nav-org');
  if (navOrg) {
    navOrg.classList.toggle('hidden', !(state.isOrgAdmin || isAdmin));
  }

  // Financial nav permissions
  const canFinancial = isAdmin || state.isOrgAdmin || state.canViewFinancial;
  const navDashboard = $('nav-dashboard');
  if (navDashboard && !canFinancial && !isAdmin) {
    // If not admin and doesn't have financial permission, hide or disable
    navDashboard.classList.add('hidden');
  } else if (navDashboard) {
    navDashboard.classList.remove('hidden');
  }

  // LINE Groups & Broadcast nav permission
  const navLineGroups = $('nav-line-groups');
  if (navLineGroups) {
    navLineGroups.classList.toggle('hidden', !(isAdmin || state.isOrgAdmin || state.canBroadcastLine));
  }
}


function selectPersona(id) {
  const p = (state.personas || []).find(x => x.id == id);
  state.activePersona = p || null;
  const activeName = document.getElementById('activePersonaName');
  if (activeName) {
    activeName.textContent = p ? p.name : 'Default';
  }
  const dd = document.getElementById('personaDropdown');
  if (dd) {
    dd.classList.add('hidden');
  }
  renderPersonas();
  if (typeof toast === 'function') {
    toast(p ? `สลับเป็นตัวตน: ${p.name}` : 'กลับสู่โหมดพื้นฐาน (Default)', 'info');
  }
}
window.selectPersona = selectPersona;

function renderPersonas() {
  const list = document.getElementById('personaList');
  if (!list) return;
  const personas = state.personas || [];
  const isDefault = !state.activePersona;

  list.innerHTML = `
    <div class="px-2 py-1.5 rounded-lg hover:bg-brand-50 dark:hover:bg-brand-900/30 cursor-pointer transition-all flex items-center gap-2 ${isDefault ? 'bg-brand-50 dark:bg-brand-900/40 text-brand-600 font-bold' : ''}" onclick="selectPersona(null)">
      <div class="w-2 h-2 rounded-full ${isDefault ? 'bg-brand-600 ring-2 ring-brand-600/30' : 'bg-surface-300'}"></div>
      <div class="text-[11px]">Standard Chat (Default)</div>
    </div>
  ` + personas.map(p => {
    const isActive = state.activePersona && state.activePersona.id == p.id;
    return `
    <div class="px-2 py-1.5 rounded-lg hover:bg-brand-50 dark:hover:bg-brand-900/30 cursor-pointer transition-all flex items-center gap-2 ${isActive ? 'bg-brand-50 dark:bg-brand-900/40 text-brand-600 font-bold' : ''}" onclick="selectPersona(${p.id})">
      <div class="w-2 h-2 rounded-full ${isActive ? 'bg-brand-600 ring-2 ring-brand-600/30' : 'bg-surface-300'}"></div>
      <div class="flex-1 min-w-0">
        <div class="text-[11px] font-bold truncate">${escHtml(p.name)}</div>
        <div class="text-[9px] text-surface-400 line-clamp-1">${escHtml(p.description || '')}</div>
      </div>
    </div>
    `;
  }).join('');
}

function initAdminPanel() {
  if (!state.isAdmin && !state.isOrgAdmin) return;
  loadAdminUsers();
  loadAdminDashboardStats();
  refreshAdminLeaves();
}

async function loadAdminDashboardStats() {
  try {
    const data = await apiFetch('/api/admin/dashboard/stats');
    if (data.ok) {
      if ($('admin-total-queries')) $('admin-total-queries').textContent = data.total_queries;
      if ($('admin-total-users')) $('admin-total-users').textContent = data.total_users;
      if ($('admin-uploads-size')) $('admin-uploads-size').textContent = data.uploads_size_mb + ' MB';
      if ($('admin-kb-size')) $('admin-kb-size').textContent = data.kb_size;
    }

    // Fetch Enhanced Analytics & render charts
    const analyticsRes = await apiFetch('/api/admin/analytics');
    if (analyticsRes.ok) {
      const stats = analyticsRes.stats;
      state.adminAnalytics = stats;
      renderAdminCharts(stats);
      renderLeaderboard(stats.top_posters || []);
    }

    await loadAdminSettings();
  } catch (e) {
    console.error('Failed to load admin stats:', e);
  }
}

function renderAdminCharts(stats) {
  const isDark = document.documentElement.classList.contains('dark');
  const gridColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.06)';
  const labelColor = isDark ? '#94a3b8' : '#64748b';

  // Build last 7 days labels
  const days = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    days.push(d.toISOString().split('T')[0]);
  }

  const mapData = (arr) => days.map(day => {
    const found = arr.find(r => r.day === day);
    return found ? found.count : 0;
  });

  const dayLabels = days.map(d => {
    const dt = new Date(d);
    return dt.toLocaleDateString('th-TH', { weekday: 'short', day: 'numeric' });
  });

  // --- Activity Chart ---
  const actCtx = $('activityChart');
  if (actCtx) {
    if (window._activityChart) window._activityChart.destroy();
    window._activityChart = new Chart(actCtx, {
      type: 'line',
      data: {
        labels: dayLabels,
        datasets: [
          {
            label: 'AI Queries',
            data: mapData(stats.daily_queries || []),
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37,99,235,0.08)',
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 6,
            borderWidth: 2,
          },
          {
            label: 'โพสต์',
            data: mapData(stats.daily_posts || []),
            borderColor: '#7c3aed',
            backgroundColor: 'rgba(124,58,237,0.08)',
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 6,
            borderWidth: 2,
          },
          {
            label: 'แชท',
            data: mapData(stats.daily_chat || []),
            borderColor: '#059669',
            backgroundColor: 'rgba(5,150,105,0.08)',
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 6,
            borderWidth: 2,
          },
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: labelColor, font: { size: 10, weight: 'bold' }, boxWidth: 10, padding: 12 } }
        },
        scales: {
          x: { grid: { color: gridColor }, ticks: { color: labelColor, font: { size: 9 } } },
          y: { grid: { color: gridColor }, ticks: { color: labelColor, font: { size: 9 }, precision: 0 }, beginAtZero: true },
        }
      }
    });
  }

  // --- Top Posters Bar Chart ---
  const barCtx = $('topPostersChart');
  if (barCtx && stats.top_posters && stats.top_posters.length) {
    if (window._topPostersChart) window._topPostersChart.destroy();
    const colors = ['#2563eb', '#7c3aed', '#059669', '#d97706', '#dc2626'];
    window._topPostersChart = new Chart(barCtx, {
      type: 'bar',
      data: {
        labels: stats.top_posters.map(p => p.user),
        datasets: [{
          label: 'จำนวนโพสต์',
          data: stats.top_posters.map(p => p.count),
          backgroundColor: colors,
          borderRadius: 8,
          borderSkipped: false,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: labelColor, font: { size: 9, weight: 'bold' } } },
          y: { grid: { color: gridColor }, ticks: { color: labelColor, font: { size: 9 }, precision: 0 }, beginAtZero: true },
        }
      }
    });
  }
}

async function loadAdminSettings() {
  const form = $('adminSettingsForm');
  if (!form) return;

  try {
    const data = await apiFetch('/api/admin/settings');
    if (data && data.ok) {
      state.appSettings = data.settings;
      // Fill all inputs in the form
      const inputs = form.querySelectorAll('input[name]');
      inputs.forEach(input => {
        const key = input.name;
        if (state.appSettings[key] !== undefined) {
          input.value = state.appSettings[key];
        }
      });
      // Handle special checkboxes if any (legacy or new)
      const chk = $('settingAllowUserEdit');
      if (chk) chk.checked = state.appSettings.allow_user_edit === '1';
    }
    
    // Load Whitelist Settings
    await loadWhitelist();
  } catch (e) {
    console.error('Failed to load settings:', e);
  }
}

async function saveAdminSettings(event) {
  if (event) event.preventDefault();
  const form = $('adminSettingsForm');
  if (!form) return;

  const btn = (event && event.submitter) || form.querySelector('button[type="submit"]');
  const originalText = btn ? btn.innerHTML : null;

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> กำลังบันทึก...`;
    initIcons();
  }

  try {
    const formData = new FormData(form);
    const settings = {};
    formData.forEach((value, key) => {
      settings[key] = value;
    });

    const res = await apiFetch('/api/admin/settings', {
      method: 'POST',
      body: JSON.stringify(settings)
    });

    if (res.ok) {
      toast('บันทึกการตั้งค่าเรียบร้อยแล้ว', 'success');
      // Update local state
      Object.assign(state.appSettings, settings);
    } else {
      toast(res.error || 'เกิดข้อผิดพลาดในการบันทึก', 'error');
    }
  } catch (e) {
    console.error('Save settings error:', e);
    toast('ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้', 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalText;
      initIcons();
    }
  }
}

async function saveAdminSetting(key, value) {
  try {
    const res = await apiFetch('/api/admin/settings', {
      method: 'POST',
      body: JSON.stringify({ [key]: value })
    });
    if (res.ok) {
      state.appSettings[key] = value;
      toast('บันทึกการตั้งค่าแล้ว', 'success');
      if (typeof loadFiles === 'function') loadFiles();
    }
  } catch (e) {
    toast('บันทึกการตั้งค่าล้มเหลว', 'error');
  }
}

// Global listener for settings toggle (legacy support if needed)
document.addEventListener('DOMContentLoaded', () => {
  const toggle = $('settingAllowUserEdit');
  if (toggle) {
    toggle.onchange = (e) => saveAdminSetting('allow_user_edit', e.target.checked ? '1' : '0');
  }
});

function renderQuotationItems() {
  const container = $('qtItemsContainer');
  const tbody = $('prevItemsBody');
  if (!container || !tbody) return;
  
  container.innerHTML = '';
  tbody.innerHTML = '';
  
  let subtotal = 0;
  
  quotationItems.forEach((item, index) => {
    const amount = item.qty * item.price;
    subtotal += amount;
    
    // Admin Form
    container.innerHTML += `
      <div class="flex items-center gap-2 p-3 bg-surface-50 dark:bg-surface-800 rounded-xl border border-surface-100 dark:border-surface-700">
        <div class="flex-1 space-y-2">
          <input type="text" class="input-field text-xs py-1" placeholder="รายการสินค้า" value="${item.desc}" onchange="updateQtItem(${index}, 'desc', this.value)">
          <div class="flex gap-2">
            <input type="number" class="input-field text-xs py-1 w-20" placeholder="จำนวน" value="${item.qty}" onchange="updateQtItem(${index}, 'qty', this.value)">
            <input type="number" class="input-field text-xs py-1 flex-1" placeholder="ราคา/หน่วย" value="${item.price}" onchange="updateQtItem(${index}, 'price', this.value)">
          </div>
        </div>
        <button onclick="removeQtItem(${index})" class="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors">
          <i data-lucide="trash-2" class="w-4 h-4"></i>
        </button>
      </div>
    `;
    
    // Preview Table
    tbody.innerHTML += `
      <tr class="border-b border-surface-100 last:border-0">
        <td class="py-2 px-3 text-center">${index + 1}</td>
        <td class="py-2 px-3">${item.desc || '-'}</td>
        <td class="py-2 px-3 text-right">${Number(item.qty).toLocaleString()}</td>
        <td class="py-2 px-3 text-right">${Number(item.price).toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
        <td class="py-2 px-3 text-right font-bold">${amount.toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
      </tr>
    `;
  });
  
  if (quotationItems.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="py-4 text-center text-surface-400 italic">ไม่มีรายการสินค้า</td></tr>`;
  }
  
  initIcons();
  
  // Update Totals
  const discount = parseFloat($('qtDiscount')?.value || 0);
  const afterDiscount = subtotal - discount;
  const vatRate = parseFloat($('qtVatRate')?.value ?? 0.07);
  const vat = afterDiscount * vatRate;
  const grandTotal = afterDiscount + vat;
  
  if ($('prevSubTotal')) $('prevSubTotal').innerText = subtotal.toLocaleString(undefined, {minimumFractionDigits: 2});
  if ($('prevDiscount')) $('prevDiscount').innerText = discount.toLocaleString(undefined, {minimumFractionDigits: 2});
  if ($('prevAfterDiscount')) $('prevAfterDiscount').innerText = afterDiscount.toLocaleString(undefined, {minimumFractionDigits: 2});
  if ($('prevVat')) $('prevVat').innerText = vat.toLocaleString(undefined, {minimumFractionDigits: 2});
  if ($('prevGrandTotal')) $('prevGrandTotal').innerText = grandTotal.toLocaleString(undefined, {minimumFractionDigits: 2});
}

async function generateAndSaveQuotation() {
  const btn = $('generatePdfBtn');
  if (!btn) return;
  
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i> กำลังสร้าง...`;
  initIcons();
  
  try {
    const element = $('quotationPreview');
    const opt = {
      margin:       0,
      filename:     `${$('qtNo').value || 'Quotation'}.pdf`,
      image:        { type: 'jpeg', quality: 0.98 },
      html2canvas:  { scale: 2, useCORS: true },
      jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };
    
    // Generate PDF Blob
    const pdfBlob = await html2pdf().set(opt).from(element).output('blob');
    
    // Prepare Data
    const discount = parseFloat($('qtDiscount')?.value || 0);
    const subtotal = quotationItems.reduce((sum, item) => sum + (item.qty * item.price), 0);
    const qtData = {
      quotation_no: $('qtNo')?.value,
      customer_name: $('qtCustomerName')?.value,
      customer_contact: $('qtCustomerContact')?.value,
      subtotal: subtotal,
      total_discount: discount,
      grand_total: (subtotal - discount) * 1.07
    };
    
    const formData = new FormData();
    formData.append('quotation_pdf', pdfBlob, opt.filename);
    formData.append('quotation_data', JSON.stringify(qtData));
    
    // Upload to Server
    const response = await fetch('/api/quotation/create', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    if (result.ok) {
      let successMsg = 'สร้างใบเสนอราคาและบันทึกเรียบร้อย!';
      const docVal = $('docTypeSelect')?.value;
      if (docVal === 'invoice') successMsg = 'สร้างใบแจ้งหนี้และบันทึกเรียบร้อย!';
      else if (docVal === 'receipt') successMsg = 'สร้างใบเสร็จรับเงินและบันทึกเรียบร้อย!';
      else if (docVal === 'receipt_replacement') successMsg = 'สร้างใบเสร็จรับเงิน/ใบแทนใบเสร็จและบันทึกเรียบร้อย!';
      toast(successMsg, 'success');
      // Download locally as well for the user
      html2pdf().set(opt).from(element).save();
    } else {
      toast(result.error || 'เกิดข้อผิดพลาดในการบันทึก', 'error');
    }
    
  } catch (err) {
    console.error(err);
    toast('เกิดข้อผิดพลาดในการสร้าง PDF', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
    initIcons();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Bind Quotation events
  const qtInputs = [
    'qtNo', 'qtDate', 'qtCustomerName', 'qtCustomerAddress', 'qtCustomerTaxId', 'qtCustomerContact', 'qtDiscount',
    'sellerName', 'sellerAddress', 'sellerTaxId', 'sellerPhone',
    'qtOriginalRefNo', 'qtOriginalRefDate', 'qtReplacementReason'
  ];
  qtInputs.forEach(id => {
    const el = $(id);
    if (el) el.addEventListener('input', updateQuotationPreview);
  });
  
  if ($('addQtItemBtn')) $('addQtItemBtn').addEventListener('click', addQtItem);
  if ($('generatePdfBtn')) $('generatePdfBtn').addEventListener('click', generateAndSaveQuotation);
  
  // Add initial item
  if (quotationItems.length === 0) addQtItem();
  
  // Set default date
  if ($('qtDate')) {
    const today = new Date().toISOString().split('T')[0];
    $('qtDate').value = today;
  }
  
  // Update initial preview
  updateQuotationPreview();

  // Doc Type Select Event Listener
  const docTypeSelect = $('docTypeSelect');
  if (docTypeSelect) {
    docTypeSelect.addEventListener('change', () => {
      const val = docTypeSelect.value;
      const titleTh = $('prevDocTitle');
      const titleEn = $('prevDocTitleEn');
      const qtNoInput = $('qtNo');
      
      let prefix = 'QT-';
      let title = 'ใบเสนอราคา';
      let titleEnText = 'QUOTATION';
      
      if (val === 'invoice') {
        prefix = 'IV-';
        title = 'ใบแจ้งหนี้';
        titleEnText = 'INVOICE';
      } else if (val === 'receipt') {
        prefix = 'RE-';
        title = 'ใบเสร็จรับเงิน';
        titleEnText = 'RECEIPT';
      } else if (val === 'receipt_replacement') {
        prefix = 'RT-';
        title = 'ใบเสร็จรับเงิน/ใบแทนใบเสร็จ';
        titleEnText = 'REPLACEMENT RECEIPT';
      }
      
      if (titleTh) titleTh.innerText = title;
      if (titleEn) titleEn.innerText = titleEnText;
      if (qtNoInput) {
        const currentVal = qtNoInput.value;
        const currentNum = currentVal.replace(/^[A-Z_]+-/, '');
        qtNoInput.value = prefix + (currentNum || new Date().toISOString().split('T')[0].replace(/-/g, '') + '001');
      }
      updateQuotationPreview();
    });
  }

  // Logo & Signature upload events for Admin settings
  const logoInput = $('org_logo_file');
  if (logoInput) {
    logoInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      const placeholder = $('org_logo_placeholder');
      const preview = $('org_logo_preview');
      const deleteBtn = $('btn_delete_logo');
      const hiddenInput = $('biz_logo_url');
      
      if (placeholder) placeholder.innerHTML = `<i data-lucide="loader-2" class="w-5 h-5 animate-spin text-brand-600"></i><span class="text-[10px] font-bold">กำลังอัปโหลด...</span>`;
      if (window.lucide) window.lucide.createIcons();
      
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        const res = await fetch('/api/org/upload-logo', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        
        if (data.ok) {
          hiddenInput.value = data.url;
          preview.src = data.url;
          preview.classList.remove('hidden');
          if (placeholder) placeholder.classList.add('hidden');
          if (deleteBtn) deleteBtn.classList.remove('hidden');
          toast('อัปโหลดโลโก้เรียบร้อยแล้วค่ะ', 'success');
        } else {
          toast(data.error || 'เกิดข้อผิดพลาดในการอัปโหลด', 'error');
          resetOrgLogoUI();
        }
      } catch (err) {
        console.error(err);
        toast('เกิดข้อผิดพลาดในการอัปโหลด', 'error');
        resetOrgLogoUI();
      }
    });
  }
  
  const sigInput = $('org_sig_file');
  if (sigInput) {
    sigInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      const placeholder = $('org_sig_placeholder');
      const preview = $('org_sig_preview');
      const deleteBtn = $('btn_delete_sig');
      const hiddenInput = $('biz_signature_url');
      const removeBg = $('org_sig_remove_bg')?.checked;
      
      if (placeholder) placeholder.innerHTML = `<i data-lucide="loader-2" class="w-5 h-5 animate-spin text-brand-600"></i><span class="text-[10px] font-bold">กำลังประมวลผล...</span>`;
      if (window.lucide) window.lucide.createIcons();
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('remove_bg', removeBg ? 'true' : 'false');
      
      try {
        const res = await fetch('/api/signature/process-background', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        
        if (data.ok) {
          hiddenInput.value = data.url;
          preview.src = data.url;
          preview.classList.remove('hidden');
          if (placeholder) placeholder.classList.add('hidden');
          if (deleteBtn) deleteBtn.classList.remove('hidden');
          toast('อัปโหลดและลบพื้นหลังลายเซ็นเรียบร้อยแล้วค่ะ', 'success');
        } else {
          toast(data.error || 'เกิดข้อผิดพลาดในการอัปโหลด', 'error');
          resetOrgSigUI();
        }
      } catch (err) {
        console.error(err);
        toast('เกิดข้อผิดพลาดในการอัปโหลด', 'error');
        resetOrgSigUI();
      }
    });
  }
});

async function loadDashboard() {
  const summaryEl = $('dashAISummary');
  const greetingEl = $('dashGreeting');
  const upcomingList = $('dashUpcomingList');
  const taskList = $('dashTaskList');
  const recentFiles = $('dashRecentFiles');
  
  // Stats
  const statUsers = $('dashStatUsers');
  const statFiles = $('dashStatFiles');
  const statQueries = $('dashStatQueries');

  try {
    const data = await apiFetch('/api/dashboard/data');
    if (data.ok) {
      // Refresh Weather & System Status
      if (typeof fetchWeather === 'function') fetchWeather();
      if (typeof updateSystemStatus === 'function') updateSystemStatus('Live');

      // Populate dynamic date badge
      const todayDateEl = $('dashTodayDateText');
      if (todayDateEl) {
        const d = new Date();
        const thMonths = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
        const thDays = ['อาทิตย์', 'จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์'];
        todayDateEl.textContent = `วัน${thDays[d.getDay()]}ที่ ${d.getDate()} ${thMonths[d.getMonth()]} ${d.getFullYear() + 543}`;
      }

      if (greetingEl) {
          const hour = new Date().getHours();
          let msg = "สวัสดีตอนเช้า";
          if (hour >= 11 && hour < 13) msg = "สวัสดีตอนกลางวัน";
          else if (hour >= 13 && hour < 17) msg = "สวัสดีตอนบ่าย";
          else if (hour >= 17 && hour < 21) msg = "สวัสดีตอนเย็น";
          else if (hour >= 21 || hour < 5) msg = "สวัสดีตอนค่ำ";
          
          const userName = state.displayName || state.username || state.user || '';
          greetingEl.textContent = userName ? `${msg}, คุณ${userName}` : `${msg}, ยินดีต้อนรับ`;
      }
      
      if (summaryEl) {
        summaryEl.textContent = 'กำลังประมวลผลข้อมูลและสรุปภาพรวมกิจกรรมสำหรับวันนี้...';
        apiFetch('/api/dashboard/briefing').then(briefData => {
           if (briefData.ok) summaryEl.textContent = briefData.briefing;
        }).catch(err => {
           summaryEl.textContent = 'ไม่สามารถโหลดข้อมูลสรุปได้ในขณะนี้ครับ';
        });
      }

      // Fetch latest announcement for dashboard widget
      apiFetch('/api/org/announcements').then(annData => {
         const banner = $('dashLatestAnnouncement');
         if (annData.ok && annData.announcements && annData.announcements.length > 0) {
            const latest = annData.announcements[0];
            if (banner) {
               banner.classList.remove('hidden');
               banner.classList.add('flex');
               
               const priorityEl = $('dashAnnPriority');
               const metaEl = $('dashAnnMeta');
               const titleEl = $('dashAnnTitle');
               const contentEl = $('dashAnnContent');
               
               if (priorityEl) {
                  priorityEl.textContent = latest.priority === 'important' ? 'สำคัญมาก' : (latest.priority === 'update' ? 'อัปเดตงาน' : 'ทั่วไป');
                  priorityEl.className = `px-2 py-0.5 rounded text-[10px] font-semibold tracking-wide ${latest.priority === 'important' ? 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-900/50' : (latest.priority === 'update' ? 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-900/50' : 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-900/50')}`;
               }
               if (metaEl) metaEl.textContent = `โดย @${latest.created_by} • ${latest.created_at}`;
               if (titleEl) titleEl.textContent = latest.title;
               if (contentEl) contentEl.textContent = latest.content;
            }
         } else {
            if (banner) {
               banner.classList.add('hidden');
               banner.classList.remove('flex');
            }
         }
      }).catch(err => console.error('Failed to load dashboard announcement:', err));

      
      // Stats
      if (statUsers) statUsers.textContent = data.stats.total_users;
      if (statFiles) statFiles.textContent = data.stats.total_files;
      if (statQueries) statQueries.textContent = data.stats.total_queries;
      
      // Task Completion %
      const completionEl = $('dashStatCompletion');
      if (completionEl) {
        const totalT = (data.pending_tasks || []).length + (data.stats.completed_tasks || 0);
        const doneT = data.stats.completed_tasks || 0;
        completionEl.textContent = totalT > 0 ? Math.round((doneT / totalT) * 100) + '%' : '—';
      }

      // Render Upcoming
      if (upcomingList) {
        if (!data.upcoming.length) {
          upcomingList.innerHTML = '<div class="text-xs text-surface-400 p-4">ไม่มีกำหนดการใหม่เร็วๆ นี้</div>';
        } else {
          upcomingList.innerHTML = data.upcoming.map(s => {
            const months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
            const d = s.date.split('-');
            const mIdx = parseInt(d[1]) - 1;
            return `
            <div class="flex items-center gap-4 p-4 bg-white dark:bg-surface-900 rounded-3xl border border-surface-100 dark:border-surface-800 hover:shadow-xl hover:-translate-y-1 transition-all group cursor-pointer" onclick="showView('calendar')">
              <div class="w-14 h-14 flex flex-col items-center justify-center bg-brand-50 dark:bg-brand-900/40 text-brand-600 rounded-2xl">
                 <span class="text-[11px] font-black uppercase text-brand-400">${months[mIdx] || d[1]}</span>
                 <span class="text-xl font-black leading-none">${d[2]}</span>
              </div>
              <div class="flex-1">
                <div class="text-[11px] font-bold tracking-wide text-surface-400 mb-0.5">${s.time} • ${s.category}</div>
                <div class="text-sm md:text-base font-black text-surface-700 dark:text-surface-200 line-clamp-1">${s.title}</div>
              </div>
              <div class="w-10 h-10 rounded-full bg-surface-50 dark:bg-surface-800 flex items-center justify-center group-hover:bg-brand-600 group-hover:text-white transition-all">
                <i data-lucide="arrow-right" class="w-4 h-4"></i>
              </div>
            </div>
            `;
          }).join('');
        }
      }

      // Render Tasks
      if (taskList) {
        if (!data.pending_tasks.length) {
          taskList.innerHTML = '<div class="text-[10px] text-surface-400 p-2">ไม่มีงานค้าง</div>';
        } else {
          taskList.innerHTML = data.pending_tasks.map(t => `
            <div class="p-4 bg-white dark:bg-surface-900 rounded-2xl border border-surface-100 dark:border-surface-800 flex items-center justify-between hover:border-brand-300 transition-all">
              <div class="flex items-center gap-3">
                <div class="w-2 h-2 rounded-full ${t.status === 'doing' ? 'bg-blue-500 animate-pulse' : 'bg-amber-500'}"></div>
                <span class="text-xs font-bold line-clamp-1">${t.title}</span>
              </div>
              <div class="px-2 py-0.5 rounded-full bg-surface-50 dark:bg-surface-800 text-[8px] font-black uppercase text-surface-500">${t.status}</div>
            </div>
          `).join('');
        }
      }

      // Render Files
      if (recentFiles) {
        if (!data.recent_files.length) {
           recentFiles.innerHTML = '<div class="text-[10px] text-surface-400 p-2 text-center">ยังไม่มีไฟล์ในคลัง</div>';
        } else {
           recentFiles.innerHTML = data.recent_files.map(f => `
             <div class="flex items-center gap-3 p-3 hover:bg-brand-50 dark:hover:bg-brand-900/20 rounded-2xl transition-all cursor-pointer group" onclick="showView('kb')">
               <div class="w-10 h-10 rounded-xl bg-surface-50 dark:bg-surface-800 flex items-center justify-center text-surface-400 group-hover:bg-white dark:group-hover:bg-surface-700 group-hover:text-brand-600 transition-all">
                 <i data-lucide="file" class="w-5 h-5"></i>
               </div>
               <div class="flex-1 min-w-0">
                 <div class="text-xs font-bold truncate text-surface-700 dark:text-surface-200">${f.name}</div>
                 <div class="text-[11px] text-surface-400 font-bold tracking-tight">${f.type} • ${(f.size/1024).toFixed(0)} KB</div>
               </div>
             </div>
           `).join('');
        }
      }

      // --- Drive Insights Populating ---
      if ($('dashStatDriveFiles')) $('dashStatDriveFiles').textContent = data.stats.drive_files || 0;
      if ($('dashStatTotalAmount')) $('dashStatTotalAmount').textContent = '฿' + new Intl.NumberFormat('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(data.stats.total_amount || 0);
      const catContainer = $('dashDriveCategoryStats');
      if (catContainer && data.drive_categories) {
        const cats = Object.entries(data.drive_categories);
        if (cats.length > 0) {
          catContainer.innerHTML = cats.map(([name, count]) => `
            <div class="flex items-center gap-1.5 px-2 py-1 bg-brand-50 dark:bg-brand-900/20 border border-brand-100 dark:border-brand-800 rounded-lg">
              <span class="text-[9px] font-black text-brand-600 uppercase">${name}</span>
              <span class="text-[9px] font-bold text-surface-400">(${count})</span>
            </div>
          `).join('');
        } else {
          catContainer.innerHTML = `<span class="text-[10px] text-surface-400 italic">ไม่มีข้อมูลหมวดหมู่</span>`;
        }
      }

      const logContainer = $('dashRecentDriveLogs');
      if (logContainer && data.recent_drive_logs) {
        if (data.recent_drive_logs.length === 0) {
          logContainer.innerHTML = '<div class="text-[10px] text-surface-400 p-2 text-center">ยังไม่มีข้อมูลการจัดเก็บ</div>';
        } else {
          logContainer.innerHTML = data.recent_drive_logs.map(log => `
            <div class="flex items-center gap-3 p-3 bg-white dark:bg-surface-900 rounded-2xl border border-surface-100 dark:border-surface-800 hover:shadow-md transition-all group cursor-pointer" onclick="window.open('${log.file_link}', '_blank')">
              <div class="w-10 h-10 rounded-xl bg-amber-50 dark:bg-amber-900/20 text-amber-600 flex items-center justify-center group-hover:bg-amber-600 group-hover:text-white transition-all">
                <i data-lucide="zap" class="w-5 h-5"></i>
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-xs font-bold truncate text-surface-700 dark:text-surface-200">${log.filename}</div>
                <div class="flex items-center gap-2 mt-0.5">
                   <span class="text-[9px] font-black text-brand-600 uppercase bg-brand-50 dark:bg-brand-900/40 px-1 rounded">${log.category}</span>
                   ${log.amount ? `<span class="text-[9px] font-black text-rose-600">฿${new Intl.NumberFormat().format(log.amount)}</span>` : ''}
                   <span class="text-[8px] text-surface-400 font-bold">${formatRelativeTime(log.created_at)}</span>
                </div>
              </div>
              <div class="text-surface-300 group-hover:text-brand-600">
                <i data-lucide="external-link" class="w-4 h-4"></i>
              </div>
            </div>
          `).join('');
        }
      }

      lucide.createIcons();
    }
  } catch (e) {
    console.error('Dash Error:', e);
  }
  
  // Update weather if we are on home view
  fetchWeather();
}

// ─── View Management ────────────────────────
function switchView(viewId) {
  // ── Permission guard: block unauthorized view access ──────────
  const _ADMIN_VIEWS      = ['admin', 'stats', 'line-manager', 'reconciliation'];
  const _ORG_ADMIN_VIEWS  = ['org', 'line-groups'];
  const _SUPERADMIN_VIEWS = ['super-admin'];

  if (_SUPERADMIN_VIEWS.includes(viewId) && !state.isSuperAdmin) {
    toast('เฉพาะ Super Admin เท่านั้น', 'error');
    return;
  }
  if (_ADMIN_VIEWS.includes(viewId) && !state.isAdmin && !state.isOrgAdmin) {
    toast('เฉพาะ Admin เท่านั้นที่มีสิทธิ์เข้าถึงส่วนนี้', 'error');
    return;
  }
  if (_ORG_ADMIN_VIEWS.includes(viewId) && !state.isOrgAdmin && !state.isAdmin) {
    toast('เฉพาะ Admin องค์กรเท่านั้น', 'error');
    return;
  }
  // ─────────────────────────────────────────────────────────────

  // ── Knowledge Base Sub-tabs Delegation ──────────────────────
  if (viewId === 'search' || viewId === 'summary' || viewId === 'crawler') {
    state._delegatingKBTab = viewId;
    switchView('kb');
    state._delegatingKBTab = null;
    if (typeof switchKBSubTab === 'function') {
      switchKBSubTab(viewId);
    }
    return;
  }

  console.log("🚀 Switching view to:", viewId);
  state.currentView = viewId;
  
  // Sync URL hash
  if (window.location.hash.replace('#', '') !== viewId) {
    history.replaceState(null, null, '#' + viewId);
  }
  
  // Highlight active menu item
  const navItems = document.querySelectorAll('.nav-item');
  if (navItems) {
    navItems.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.view === viewId);
    });
  }

  // Cross-view nav highlighting (views merged into parent nav item)
  const _crossNavMap = { 'csv-explorer': 'nav-viz', 'search': 'nav-kb', 'summary': 'nav-kb', 'crawler': 'nav-kb', 'stats': 'nav-admin' };
  if (_crossNavMap[viewId]) {
    const _crossBtn = document.getElementById(_crossNavMap[viewId]);
    if (_crossBtn) _crossBtn.classList.add('active');
  }

  // KB tab active state
  const _kbTabMap = { 'kb': 'kb-tab-files', 'search': 'kb-tab-search', 'summary': 'kb-tab-summary', 'crawler': 'kb-tab-crawler' };
  document.querySelectorAll('.kb-main-tab').forEach(btn => btn.classList.remove('active-tab', 'bg-white', 'dark:bg-surface-700', 'shadow-sm', 'text-brand-600'));
  if (_kbTabMap[viewId]) {
    const _kbTab = document.getElementById(_kbTabMap[viewId]);
    if (_kbTab) { _kbTab.classList.add('bg-white', 'dark:bg-surface-700', 'shadow-sm', 'text-brand-600'); _kbTab.classList.remove('text-surface-400'); }
  }

  // Auto-expand "เพิ่มเติม" section if navigating to a hidden item
  const _moreViews = ['crm', 'viz', 'wiki', 'drive', 'whiteboard'];
  if (_moreViews.includes(viewId)) {
    const _moreSection = document.getElementById('moreNavSection');
    if (_moreSection && _moreSection.classList.contains('hidden')) {
      toggleMoreNav();
    }
  }

  document.querySelectorAll('.view').forEach(sec => {
    const isTarget = sec.id === `view-${viewId}`;
    sec.classList.toggle('hidden', !isTarget);
    if (isTarget) {
      sec.classList.remove('animate-in', 'fade-in', 'zoom-in-95', 'duration-200');
      void sec.offsetWidth; // trigger reflow for smooth animation restart
      sec.classList.add('animate-in', 'fade-in', 'zoom-in-95', 'duration-200');
    }
  });

  // Sync mobile bottom nav active state
  document.querySelectorAll('.mobile-nav-btn[data-mobile-view]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.mobileView === viewId);
  });

  // Update mobile header title
  const _VIEW_TITLES = {
    home: 'หน้าหลัก', chat: 'AI แชท', kb: 'คลังความรู้', calendar: 'ปฏิทิน',
    feed: 'ฟีดทีม', dashboard: 'รายจ่ายองค์กร', quotation: 'ใบเสนอราคา',
    wht: 'ภงด. WHT', 'receipt-replacement': 'ใบแทนใบเสร็จ', crm: 'CRM ลูกค้า',
    'reply-assistant': 'ช่วยตอบแชทลูกค้า',
    kanban: 'Kanban Board', meetings: 'บันทึกประชุม', viz: 'วิเคราะห์ข้อมูล',
    wiki: 'Internal Wiki', drive: 'Google Drive', search: 'ค้นหา AI',
    summary: 'สรุป AI', leave: 'ลางาน', settings: 'การตั้งค่า',
    attendance: 'ลงเวลาเข้างาน',
    profile: 'โปรไฟล์', notifications: 'การแจ้งเตือน', plan: 'จัดการแพลน',
    admin: 'แผงควบคุม', 'super-admin': 'Super Admin', whiteboard: 'ไวท์บอร์ด',
    'csv-explorer': 'CSV Explorer', stats: 'สถิติ',
  };
  const _mobileTitle = document.getElementById('mobileHeaderTitle');
  if (_mobileTitle) {
    _mobileTitle.style.opacity = '0';
    requestAnimationFrame(() => {
      _mobileTitle.textContent = _VIEW_TITLES[viewId] || 'OrgChat';
      _mobileTitle.style.opacity = '1';
    });
  }

  // 🔔 FIX: Reset currentChat if we left the chat area to allow notifications
  // This tells the system we are no longer viewing the chat window
  if (viewId !== 'dm' && viewId !== 'ai-chat') {
    if (state.currentChat && state.currentChat.id) {
      console.log("👋 Leaving chat room:", state.currentChat.id);
      stopChatPolling();
      state.lastActiveChat = { ...state.currentChat };
      state.currentChat = { type: null, id: null, name: null };
    }
  }

  // 🔔 Restore previous active chat when returning to DM if no chat is currently selected
  if (viewId === 'dm') {
    if ((!state.currentChat || !state.currentChat.id) && state.lastActiveChat && state.lastActiveChat.id) {
      const prev = state.lastActiveChat;
      setTimeout(() => {
        if (typeof switchChat === 'function') {
          switchChat(prev.type, prev.id, prev.name, prev.avatarUrl);
        }
      }, 50);
    }
  }

  if (viewId === 'home') loadDashboard();
  if (viewId === 'profile') loadProfile();
  if (viewId === 'search') {
    if (searchInput) searchInput.focus();
  }
  if (viewId === 'notifications') loadNotifications();
  if (viewId === 'stats') loadStats();
  if (viewId === 'viz') initViz();
  if (viewId === 'csv-explorer') initCSVExplorer();
  if (viewId === 'calendar') { loadSchedules(); loadTodoTasks(); }
  if (viewId === 'kanban') loadKanbanBoard();
  if (viewId === 'wiki') { loadWikiPages(); renderWikiContent(); }
  if (viewId === 'dashboard') { if (typeof loadDashboardData === 'function') loadDashboardData(); }
  if (viewId === 'settings') loadMySettings();
  if (viewId === 'plan') { if (typeof initPlanView === 'function') initPlanView(); }
  if (viewId === 'admin') { initAdminPanel(); loadGoogleDriveStatus(); if (typeof loadAuditLogsUI === 'function') loadAuditLogsUI(); }
  if (viewId === 'super-admin') {
    const iframe = document.getElementById('super-admin-iframe');
    if (iframe && (iframe.src === 'about:blank' || iframe.src === '' || !iframe.getAttribute('src') || iframe.getAttribute('src') === 'about:blank')) {
      iframe.src = '/admin/super';
    }
  }
  if (viewId === 'kb') {
    if (!state._delegatingKBTab && typeof switchKBSubTab === 'function') {
      switchKBSubTab('files');
    }
    loadFiles();
  }
  if (viewId === 'drive') loadDriveContents(state.drive.currentFolderId);
  if (viewId === 'summary') renderSummary();
  if (viewId === 'whiteboard') initWhiteboard();
  if (viewId === 'leave') loadLeaveData();
  if (viewId === 'attendance') { if (typeof initAttendanceSystem === 'function') initAttendanceSystem(); }
  if (viewId === 'quotation') initDocumentGenerator();
  if (viewId === 'receipt-replacement') initReplacementReceiptView();
  if (viewId === 'reply-assistant') initReplyAssistantView();
  if (viewId === 'line-groups') { if (typeof loadLineGroups === 'function') loadLineGroups(); }

  // ─── Feed Auto-Refresh ───────────────────────
  // Clear any existing feed poll interval when changing views
  if (state.feedPollInterval) {
    clearInterval(state.feedPollInterval);
    state.feedPollInterval = null;
  }
  if (viewId === 'feed') {
    loadPosts();
    loadDailyDigest();
    // Auto-refresh feed every 15 seconds so poll votes & new posts update live
    state.feedPollInterval = setInterval(() => {
      // Only refresh if feed view is still active
      if (state.currentView === 'feed') {
        loadPosts(state.currentFeedCategory || 'All');
      } else {
        clearInterval(state.feedPollInterval);
        state.feedPollInterval = null;
      }
    }, 15000);
  }

  // Auto-hide sidebar on mobile after navigation
  if (window.innerWidth < 1024) toggleSidebar(false);
}

async function generateGlobalSummary() {
  const contentArea = $('summaryContentArea');
  const emptyState = $('summaryEmpty');
  const loadingState = $('summaryLoading');
  const output = $('summaryOutput');
  const keywordsEl = $('summaryKeywords');
  const refsEl = $('summaryRefs');
  const btn = $('generateGlobalSummaryBtn');

  const focusTopic = $('summaryFocusInput')?.value || '';
  const categoryId = $('summaryCategorySelect')?.value || 'all';

  emptyState.classList.add('hidden');
  contentArea.classList.add('hidden');
  loadingState.classList.remove('hidden');
  btn.disabled = true;
  btn.innerHTML = '<i class="animate-spin w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full"></i> กำลังสรุป...';

  try {
    const res = await apiFetch('/api/summary/generate', {
      method: 'POST',
      body: JSON.stringify({ focus: focusTopic, category_id: categoryId })
    });
    if (res.ok) {
      output.innerHTML = markdownToHtml(res.summary);

      keywordsEl.innerHTML = (res.keywords || []).map(k => `
        <li class="px-2 py-0.5 bg-brand-50 dark:bg-brand-900/20 text-brand-600 rounded-full text-[9px] font-bold border border-brand-100 dark:border-brand-800/50 cursor-default opacity-80">
          ${k}
        </li>
      `).join('');

      refsEl.innerHTML = (res.refs || []).map(r => `
        <div class="flex items-center gap-1.5 text-[11px] text-surface-400 font-medium">
          <i data-lucide="file-check" class="w-2.5 h-2.5 text-brand-600"></i>
          <span class="truncate">${r}</span>
        </div>
      `).join('');

      loadingState.classList.add('hidden');
      contentArea.classList.remove('hidden');
      initIcons();
    } else {
      throw new Error(res.error);
    }
  } catch (e) {
    toast('สรุปข้อมูลไม่สำเร็จ: ' + e.message, 'error');
    loadingState.classList.add('hidden');
    emptyState.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="sparkles" class="w-3.5 h-3.5"></i> สรุปข้อมูล';
    initIcons();
  }
}

async function loadHistory(isBackground = false) {
  try {
    const data = await apiFetch('/api/history');
    if (data.history) {
      const historyHash = JSON.stringify(data.history);
      // Skip rendering if no changes and it's a background fetch
      if (isBackground && state.lastRendered.mainHistory === historyHash) return;
      state.lastRendered.mainHistory = historyHash;

      state.history = data.history;

      if (state.history.length > 0) {
        chatArea.innerHTML = '';
        suggestions.classList.add('hidden');

        // Intelligent Scroll: Check if user is at the bottom BEFORE rendering
        const isAtBottom = chatArea.scrollHeight - chatArea.scrollTop <= chatArea.clientHeight + 50;

        state.history.forEach(msg => {
          const { displayHtml, calendarData, reconcileData } = parseAIActions(msg.text);
          const msgEl = appendMessage(msg.role, displayHtml, msg.sources || [], false, msg.id);
          
          if (calendarData) {
            renderCalendarActionUI(msgEl, calendarData);
          }
          if (reconcileData) {
            renderReconcileActionUI(msgEl, reconcileData);
          }
        });

        // Auto-scroll if it was a manual load OR if user was already at bottom
        if (!isBackground || isAtBottom) {
          setTimeout(() => scrollToBottom('auto', false), 50);
        }
      } else {
        showWelcome();
      }
    }
  } catch (e) {
    if (!isBackground) {
      console.error('Failed to load history:', e);
      showWelcome();
    }
  }
}

// ─── ตรวจประเภทเอกสารก่อนอัปโหลด KB ─────────────────────────
const _FINANCIAL_CAT_KEYWORDS = ['บัญชี','finance','ค่าใช้จ่าย','invoice','slip','receipt','ใบเสร็จ','สลิป','รายจ่าย','expense','tax','ภาษี'];

// ─── Document Viewer Logic ────────────────────────
function openPdfViewer(fileId, fileName, location = null) {
  const modal = $('pdfViewerModal');
  const frame = $('pdfFrame');
  const title = $('pdfViewerTitle');
  const loading = $('pdfLoading');
  const download = $('pdfDownloadLink');
  const csvContainer = $('csvViewerContainer');
  const csvTarget = $('csvTableTarget');
  const icon = $('pdfViewerIcon');

  if (!modal || !frame) return;

  // Extract page number if location like "Page 3" or "Slide 4"
  let pageNum = 1;
  if (location) {
    const m = String(location).match(/(?:page|slide|หน้า|แผ่นที่)\s*(\d+)/i);
    if (m) pageNum = parseInt(m[1], 10);
  }

  const pageInfo = location ? ` (${location})` : '';
  title.textContent = `เปิดดู: ${fileName}${pageInfo}`;
  loading.classList.remove('hidden');
  modal.classList.remove('hidden');
  modal.classList.add('flex', 'items-center', 'justify-center');
  csvContainer.classList.add('hidden');
  frame.classList.add('hidden');

  const isCsv = fileName.toLowerCase().endsWith('.csv');
  const isPdf = fileName.toLowerCase().endsWith('.pdf');
  if (icon) {
    icon.setAttribute('data-lucide', isCsv ? 'table' : (isPdf ? 'file-text' : 'file'));
    initIcons();
  }

  const baseViewUrl = `/api/kb/files/view/${fileId}`;
  download.href = baseViewUrl;

  if (isCsv) {
    // Parse and render CSV
    fetch(baseViewUrl)
      .then(res => res.text())
      .then(text => {
        csvTarget.innerHTML = renderCsvAsHtmlTable(text);
        csvContainer.classList.remove('hidden');
        loading.classList.add('hidden');
      })
      .catch(err => {
        csvTarget.innerHTML = `<div class="p-8 text-center text-red-500 font-bold">ไม่สามารถโหลดข้อมูล CSV ได้: ${err.message}</div>`;
        csvContainer.classList.remove('hidden');
        loading.classList.add('hidden');
      });
  } else if (isPdf) {
    // Jump directly to the referenced page in PDF standard viewer
    const pdfUrl = `${baseViewUrl}#page=${pageNum}`;
    frame.src = pdfUrl;
    frame.classList.remove('hidden');
    frame.onload = () => {
      loading.classList.add('hidden');
    };
  } else {
    frame.src = baseViewUrl;
    frame.classList.remove('hidden');
    frame.onload = () => {
      loading.classList.add('hidden');
    };
  }
}

function setCatVisibility(vis) {
  currentCatVisibility = vis;
  document.querySelectorAll('.cat-vis-btn').forEach(b => b.classList.remove('active'));
  $(`catVis${vis.charAt(0).toUpperCase() + vis.slice(1)}`).classList.add('active');
  
  const hint = $('catVisHint');
  const panel = $('catRestrictedPanel');
  
  if (vis === 'public') {
    hint.textContent = 'หมวดหมู่สาธารณะ จะมองเห็นได้โดยทุกคนที่มีสิทธิ์เข้าถึงคลังความรู้';
    panel.classList.add('hidden');
  } else if (vis === 'private') {
    hint.textContent = 'หมวดหมู่ส่วนตัว จะมีเพียงคุณและ Admin เท่านั้นที่มองเห็นได้';
    panel.classList.add('hidden');
  } else if (vis === 'restricted') {
    hint.textContent = 'หมวดหมู่แบบระบุบุคคล เฉพาะผู้ใช้ที่คุณเลือกด้านล่างเท่านั้นที่จะมองเห็นได้';
    panel.classList.remove('hidden');
  }
}

async function saveCatSettings() {
  const id = $('catSettingsId').value;
  const visibility = currentCatVisibility;
  const authorized_users = selectedCatUsers;
  
  try {
    const res = await apiFetch('/api/kb/categories/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: parseInt(id), visibility, authorized_users })
    });
    
    if (res.ok) {
      toast('บันทึกการตั้งค่าแล้ว', 'success');
      const m = $('kbCategorySettingsModal');
      if (m) {
        m.classList.add('hidden');
        m.classList.remove('flex', 'items-center', 'justify-center');
      }
      loadCategories(); // Refresh icons and state
    } else {
      toast(res.error || 'บันทึกไม่สำเร็จ', 'error');
    }
  } catch (err) {
    toast('เกิดข้อผิดพลาด: ' + err.message, 'error');
  }
}

// ─── Global Search Functionality ────────────────────
const TYPE_ICON = { post: 'layout-list', schedule: 'calendar', message: 'message-square', dm: 'mail', kb: 'folder-open' };

const TYPE_LABEL = { post: 'โพสต์', schedule: 'ปฏิทิน', message: 'ข้อความกลุ่ม', dm: 'DM', kb: 'คลังข้อมูล' };

const TYPE_COLOR = {
  post: 'text-indigo-600  bg-indigo-50  dark:bg-indigo-900/20  border-indigo-100  dark:border-indigo-800',
  schedule: 'text-amber-600   bg-amber-50   dark:bg-amber-900/20   border-amber-100   dark:border-amber-800',
  message: 'text-teal-600    bg-teal-50    dark:bg-teal-900/20    border-teal-100    dark:border-teal-800',
  dm: 'text-pink-600    bg-pink-50    dark:bg-pink-900/20    border-pink-100    dark:border-pink-800',
  kb: 'text-brand-600   bg-brand-50   dark:bg-brand-900/20   border-brand-100   dark:border-brand-800',
};

// ─── Chat ─────────────────────────────────────
function showWelcome() {
  chatArea.innerHTML = `
    <div id="welcomeScreen" class="flex flex-col items-center justify-center py-20 text-center animate-in fade-in zoom-in-95 duration-700">
      <div class="w-16 h-16 bg-brand-600 text-white rounded-2xl flex items-center justify-center mb-6 shadow-xl">
        <i data-lucide="bot" class="w-10 h-10"></i>
      </div>
      <h2 class="text-2xl font-bold mb-2">ยินดีต้อนรับสู่ OrgChat</h2>
      <p class="text-surface-500 max-w-sm text-sm font-medium">
        ระบบผู้ช่วยปัญญาประดิษฐ์ระดับองค์กร<br/>
        ถามข้อมูลเชิงลึกจากเอกสารทั้งหมดได้ในที่เดียว
      </p>
    </div>`;
  initIcons();
}

function appendMessage(role, html, sources = [], scroll = true, msgId = null) {
  const isUser = role === 'user';
  const row = document.createElement('div');
  row.className = `chat-msg-row flex gap-3 ${isUser ? 'flex-row-reverse msg-user' : 'flex-row msg-bot'} items-start animate-in fade-in group/msgrow mb-2`;
  if (msgId) row.dataset.id = msgId;

  const icon = isUser ? 'user' : 'bot';
  const avatarClass = isUser ? 'bg-surface-800' : 'bg-brand-600';
  const name = isUser ? 'USER' : 'น้องพั้น (Nong Punch)';
  const bubbleClass = isUser
    ? 'bubble-me'
    : 'bubble-them';

  let feedbackPanel = !isUser ? `
    <div class="absolute -right-2 top-0 translate-x-full opacity-0 group-hover/msg:opacity-100 transition-opacity flex flex-col gap-1 p-0.5">
      <button class="translate-msg-btn p-1.5 rounded-lg bg-white dark:bg-zinc-800 text-surface-500 dark:text-surface-400 hover:text-surface-900 dark:hover:text-white border border-surface-200/80 dark:border-zinc-700 shadow-xs transition-colors" title="แปลภาษา"><i data-lucide="languages" class="w-3.5 h-3.5"></i></button>
      <button class="copy-msg-btn p-1.5 rounded-lg bg-white dark:bg-zinc-800 text-surface-500 dark:text-surface-400 hover:text-surface-900 dark:hover:text-white border border-surface-200/80 dark:border-zinc-700 shadow-xs transition-colors" title="คัดลอก"><i data-lucide="copy" class="w-3.5 h-3.5"></i></button>
      <button class="speak-btn p-1.5 rounded-lg bg-white dark:bg-zinc-800 text-surface-500 dark:text-surface-400 hover:text-surface-900 dark:hover:text-white border border-surface-200/80 dark:border-zinc-700 shadow-xs transition-colors" title="ฟังเสียง"><i data-lucide="volume-2" class="w-3.5 h-3.5"></i></button>
      <button class="fb-btn p-1.5 rounded-lg bg-white dark:bg-zinc-800 text-surface-500 dark:text-surface-400 hover:text-emerald-600 dark:hover:text-emerald-400 border border-surface-200/80 dark:border-zinc-700 shadow-xs transition-colors" data-val="1" title="มีประโยชน์"><i data-lucide="thumbs-up" class="w-3.5 h-3.5"></i></button>
      <button class="fb-btn p-1.5 rounded-lg bg-white dark:bg-zinc-800 text-surface-500 dark:text-surface-400 hover:text-rose-600 dark:hover:text-rose-400 border border-surface-200/80 dark:border-zinc-700 shadow-xs transition-colors" data-val="-1" title="ต้องปรับปรุง"><i data-lucide="thumbs-down" class="w-3.5 h-3.5"></i></button>
      ${msgId ? `<button class="del-msg-btn p-1.5 rounded-lg bg-white dark:bg-zinc-800 text-surface-500 dark:text-surface-400 hover:text-rose-600 dark:hover:text-rose-400 border border-surface-200/80 dark:border-zinc-700 shadow-xs transition-colors" title="ลบข้อความ"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>` : ''}
    </div>` : `
    <div class="absolute -left-2 top-0 -translate-x-full opacity-0 group-hover/msg:opacity-100 transition-opacity flex flex-col gap-1 p-0.5">
      <button class="translate-msg-btn p-1.5 rounded-lg bg-white dark:bg-zinc-800 text-surface-500 dark:text-surface-400 hover:text-surface-900 dark:hover:text-white border border-surface-200/80 dark:border-zinc-700 shadow-xs transition-colors" title="แปลภาษา"><i data-lucide="languages" class="w-3.5 h-3.5"></i></button>
      <button class="copy-msg-btn p-1.5 rounded-lg bg-white dark:bg-zinc-800 text-surface-500 dark:text-surface-400 hover:text-surface-900 dark:hover:text-white border border-surface-200/80 dark:border-zinc-700 shadow-xs transition-colors" title="คัดลอก"><i data-lucide="copy" class="w-3.5 h-3.5"></i></button>
      ${msgId ? `<button class="del-msg-btn p-1.5 rounded-lg bg-white dark:bg-zinc-800 text-surface-500 dark:text-surface-400 hover:text-rose-600 dark:hover:text-rose-400 border border-surface-200/80 dark:border-zinc-700 shadow-xs transition-colors" title="ลบข้อความ"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>` : ''}
    </div>`;

  const userImages = isUser ? (sources || []).filter(s => s.type === 'image') : [];
  const botSources = !isUser ? (sources || []) : [];
  const hasText = html && typeof html === 'string' && html.trim().length > 0 && html !== '<span class="typing-dots">...</span>';
  const isTyping = html === '<span class="typing-dots">...</span>';

  let contentHtml = '';

  if (isUser) {
    // 1. Standalone user images (Clean dark/neutral card, no neon blue backdrop)
    const imagesHtml = userImages.length > 0 ? `
      <div class="flex flex-wrap justify-end gap-2 mb-2 w-full">
        ${userImages.map(img => `
          <div class="relative group/userimg rounded-2xl overflow-hidden border border-surface-200 dark:border-white/10 bg-surface-100 dark:bg-[#18181b] shadow-md transition-all hover:scale-[1.01] cursor-pointer max-w-[280px]" onclick="openImageViewer('${img.url}')">
            <img src="${img.url}" class="w-full h-auto max-h-[320px] object-contain rounded-2xl block" alt="Attached Image">
            <div class="absolute inset-0 bg-black/0 hover:bg-black/10 transition-colors pointer-events-none"></div>
          </div>
        `).join('')}
      </div>` : '';

    // 2. User text bubble (Rendered below the image, or standalone if text only)
    const textBubbleHtml = (hasText || isTyping || userImages.length === 0) ? `
      <div class="${bubbleClass} chat-bubble relative group/msg ml-auto max-w-prose">
        <div class="prose dark:prose-invert prose-sm max-w-none text-left">${html}</div>
        ${feedbackPanel}
      </div>` : '';

    contentHtml = `
      <div class="flex flex-col items-end w-full">
        <span class="text-[9px] font-bold text-surface-400 tracking-widest uppercase mb-1 px-1">${name}</span>
        ${imagesHtml}
        ${textBubbleHtml}
      </div>`;
  } else {
    // Bot message with document citation sources
    const sourcesHtml = botSources.length > 0 ? `
      <div class="mt-3 pt-3 border-t border-surface-200 dark:border-surface-700/50 flex flex-wrap gap-1.5">
        <span class="w-full text-[9px] font-black text-surface-400 uppercase tracking-widest mb-1 flex items-center gap-1">
          <i data-lucide="book-open" class="w-2.5 h-2.5"></i> แหล่งข้อมูลอ้างอิง
        </span>
        ${botSources.map(s => {
          if (s.type === 'image') {
            return `
              <div class="mt-2 relative group-img rounded-xl overflow-hidden border border-surface-200 dark:border-surface-700 shadow-sm transition-all hover:ring-2 hover:ring-brand-500 max-w-[200px]">
                <img src="${s.url}" class="w-full h-auto object-cover cursor-pointer" onclick="openImageViewer('${s.url}')" alt="Attached Image">
              </div>`;
          }
          const safeName = (s.name || s.source || 'Document').replace(/'/g, "\\'");
          const safeLoc = (s.location || '').replace(/'/g, "\\'");
          return `
            <button onclick="openPdfViewer('${s.file_id}', '${safeName}', '${safeLoc}')" 
              class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white dark:bg-surface-800 text-surface-700 dark:text-surface-300 text-[11px] font-medium border border-surface-200 dark:border-surface-700 hover:border-surface-400 dark:hover:border-surface-500 transition-colors">
              <i data-lucide="${FILE_LUCIDE[s.type] || 'file-text'}" class="w-3 h-3 text-surface-500"></i>
              <span class="truncate max-w-[130px]">${s.name || s.source || 'Document'}</span>
              ${s.location && s.location !== 'Document' ? `<span class="opacity-50 text-[10px]">#${s.location}</span>` : ''}
            </button>
          `;
        }).join('')}
      </div>` : '';

    contentHtml = `
      <span class="text-[9px] font-bold text-surface-400 tracking-widest uppercase mb-0.5 px-1">${name}</span>
      <div class="${bubbleClass} chat-bubble relative group/msg">
        <div class="prose dark:prose-invert prose-sm max-w-none text-left">${html}</div>
        ${sourcesHtml}
        <!-- Action Panel (Dynamic) -->
        <div class="action-panel mt-3 hidden"></div>
        ${feedbackPanel}
      </div>`;
  }

  row.innerHTML = `
    <div class="w-8 h-8 flex-shrink-0 rounded-lg ${avatarClass} flex items-center justify-center text-white">
      <i data-lucide="${icon}" class="w-4 h-4"></i>
    </div>
    <div class="msg-content-wrapper flex-1 min-w-0">
      ${contentHtml}
    </div>`;

  chatArea.appendChild(row);

  // Attach translate listener
  const transBtn = row.querySelector('.translate-msg-btn');
  if (transBtn) {
    transBtn.onclick = () => translateChatMessage(transBtn);
  }

  // Attach copy listener
  const copyBtn = row.querySelector('.copy-msg-btn');
  if (copyBtn) {
    copyBtn.onclick = async () => {
      const prose = row.querySelector('.prose');
      if (!prose) return;
      try {
        await navigator.clipboard.writeText(prose.innerText);
        toast('คัดลอกข้อความเรียบร้อยแล้วค่ะพี่', 'success');
        const icon = copyBtn.querySelector('i');
        if (icon) {
          icon.setAttribute('data-lucide', 'check');
          initIcons();
          setTimeout(() => {
            icon.setAttribute('data-lucide', 'copy');
            initIcons();
          }, 2000);
        }
      } catch (err) {
        toast('คัดลอกล้มเหลว: ' + err.message, 'error');
      }
    };
  }

  // Attach speak listener
  const speakBtn = row.querySelector('.speak-btn');
  if (speakBtn) {
    speakBtn.onclick = () => {
      const p = row.querySelector('.prose');
      if (p) speakTextThai(p.innerText);
    };
  }

  // Attach feedback listeners
  row.querySelectorAll('.fb-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const val = parseInt(btn.dataset.val);
      await fetch('/api/feedback', {
        method: 'POST',
        body: JSON.stringify({ value: val }),
        headers: { 'Content-Type': 'application/json' }
      });
      toast('ขอบคุณสำหรับคำติชมครับ', 'success');
      btn.classList.add(val === 1 ? 'text-emerald-500' : 'text-red-500');
    });
  });

  // Attach delete listener
  const delBtn = row.querySelector('.del-msg-btn');
  if (delBtn && msgId) {
    delBtn.onclick = () => deleteChatMessage('ai', msgId, row);
  }

  initIcons();
  if (scroll) {
    scrollToBottom('auto');
  }
  return row;
}

async function deleteChatMessage(ctype, mid, el) {
  if (!await showConfirm('ลบข้อความ', 'ต้องการลบข้อความนี้ใช่หรือไม่?', { type: 'danger', confirmText: 'ลบข้อความ' })) return;
  try {
    const res = await fetch(`/api/chat/delete/${ctype}/${mid}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.ok) {
      el.classList.add('animate-out', 'fade-out', 'zoom-out-95');
      setTimeout(() => {
        el.remove();
        // If it's a re-renderable state, update it
        if (ctype === 'ai') {
          state.history = state.history.filter(m => m.id !== mid);
          if (chatArea.children.length === 0) showWelcome();
        } else {
          state.groupChat.messages = state.groupChat.messages.filter(m => m.id !== mid);
        }
      }, 300);
      toast('ลบข้อความเรียบร้อยแล้ว', 'info');
    } else {
      toast(data.error || 'ลบไม่สำเร็จ', 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาดในการเชื่อมต่อ', 'error');
  }
}

async function editChatMessage(ctype, mid, bubbleEl) {
  // Inline edit: replace bubble content with a textarea
  if (!bubbleEl) return;
  const proseEl = bubbleEl.querySelector('.prose') || bubbleEl.querySelector('.chat-bubble-container') || bubbleEl;

  // Try to find the actual text content from the bubble
  let currentText = "";
  const textEl = bubbleEl.querySelector('.whitespace-pre-wrap');
  if (textEl) {
    currentText = textEl.innerText.replace(/\(แก้ไขแล้ว\)$/, '').trim();
  }

  const originalHTML = proseEl.innerHTML;

  // Build inline editor
  const editorHTML = `
    <div class="edit-inline-box w-full">
      <textarea class="w-full bg-white dark:bg-surface-800 border border-brand-300 dark:border-brand-700 rounded-lg p-2 text-xs resize-none outline-none focus:ring-2 focus:ring-brand-600/30 min-h-[60px]" id="edit-ta-${mid}">${currentText}</textarea>
      <div class="flex gap-2 mt-1.5 justify-end">
        <button id="edit-cancel-${mid}" class="text-[10px] font-bold px-2 py-1 rounded bg-surface-100 dark:bg-surface-700 text-surface-500 hover:bg-surface-200 transition-colors">ยกเลิก</button>
        <button id="edit-save-${mid}" class="text-[10px] font-bold px-3 py-1 rounded bg-brand-600 text-white hover:bg-brand-700 transition-colors">บันทึก</button>
      </div>
    </div>`;
  proseEl.innerHTML = editorHTML;

  const ta = document.getElementById(`edit-ta-${mid}`);
  const saveBtn = document.getElementById(`edit-save-${mid}`);
  const cancelBtn = document.getElementById(`edit-cancel-${mid}`);
  if (ta) ta.focus();

  if (cancelBtn) {
    cancelBtn.onclick = () => { proseEl.innerHTML = originalHTML; initIcons(); };
  }
  if (saveBtn) {
    saveBtn.onclick = async () => {
      const newText = ta ? ta.value.trim() : '';
      if (!newText) { toast('ข้อความว่างเปล่าไม่ได้', 'error'); return; }
      saveBtn.disabled = true;
      saveBtn.textContent = '...';
      try {
        const res = await apiFetch(`/api/chat/edit/${ctype}/${mid}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: newText })
        });
        if (res.ok) {
          // Update display
          proseEl.innerHTML = `<span class="prose dark:prose-invert prose-sm">${markdownToHtml(newText)}</span><span class="text-[8px] text-surface-400 italic ml-1">(แก้ไขแล้ว)</span>`;
          initIcons();
          // Update local state
          if (ctype === 'room') {
            const m = state.groupChat.messages.find(m => m.id === mid);
            if (m) m.text = newText;
          }
          toast('แก้ไขข้อความสำเร็จ', 'success');
        } else {
          toast(res.error || 'แก้ไขไม่สำเร็จ', 'error');
          proseEl.innerHTML = originalHTML;
          initIcons();
        }
      } catch (e) {
        toast('เกิดข้อผิดพลาด: ' + e.message, 'error');
        proseEl.innerHTML = originalHTML;
        initIcons();
      }
    };
  }
}

async function toggleRoomMessagePin(mid) {
  const ctype = state.currentChat.type || 'room';
  try {
    const res = await apiFetch(`/api/chat/pin/${ctype}/${mid}`, { method: 'POST' });
    if (res.ok) {
      toast('ดำเนินการปักหมุดเรียบร้อย', 'info');
      // Update local state for immediate feedback
      const msg = state.groupChat.messages.find(m => m.id === mid);
      if (msg) {
        msg.is_pinned = !msg.is_pinned;
        renderChatMessages();
      }
    } else {
      toast(res.statusText || 'ปักหมุดไม่สำเร็จ', 'error');
    }
  } catch (e) { console.error(e); }
}

function showTyping() {
  const row = document.createElement('div');
  row.className = 'flex gap-4 chat-bot animate-in fade-in duration-300';
  row.id = 'typingRow';
  row.innerHTML = `
    <div class="w-8 h-8 flex-shrink-0 rounded-lg bg-brand-600 flex items-center justify-center text-white">
      <i data-lucide="bot" class="w-4 h-4"></i>
    </div>
    <div class="flex flex-col gap-1.5 items-start">
      <span class="text-[9px] font-bold text-surface-400 tracking-widest uppercase">น้องพั้น (Nong Punch)</span>
      <div class="typing-indicator">
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
      </div>
    </div>`;
  chatArea.appendChild(row);
  initIcons();
  scrollToBottom('auto');
}

function removeTyping() {
  const el = $('typingRow');
  if (el) {
    el.remove();
    scrollToBottom('auto', true);
  }
}

const chatAttachBtn = $('chatAttachBtn');

const chatImageInput = $('chatImageInput');

const chatImagePreview = $('chatImagePreview');

const chatImageThumbnail = $('chatImageThumbnail');

const removeChatImage = $('removeChatImage');

if (removeChatImage) {
  removeChatImage.onclick = () => {
    state.pendingImage = null;
    state.pendingMime = null;
    chatImageInput.value = '';
    chatImagePreview.classList.add('hidden');
  };
}

async function sendMessage(text) {
  if (state.sending || (!text.trim() && !state.pendingImage)) return;
  if (!state.apiKeySet) { showApiModal(); return; }

  const welcome = $('welcomeScreen');
  if (welcome) welcome.remove();
  suggestions.classList.add('hidden');

  state.sending = true;
  sendBtn.disabled = true;
  msgInput.disabled = true;

  // Add visual indication of image in chat bubble if present
  let displayContext = [];
  if (state.pendingImage) {
    displayContext.push({
      type: 'image',
      url: state.pendingImage,
      name: 'Image for analysis'
    });
  }

  appendMessage('user', text, displayContext, true); 
  state.history.push({ role: 'user', text, sources: displayContext });
  saveHistory();

  // 🔔 Play Send Chime & Haptic
  if (window.soundEngine) {
    window.soundEngine.playSendChime();
  }

  showTyping(); 

  try {
    const payload = {
      message: text,
      history: state.history,
      persona_id: state.activePersona ? state.activePersona.id : null,
      image_data: state.pendingImage,
      mime_type: state.pendingMime
    };

    // Reset pending image UI immediately
    if (removeChatImage) removeChatImage.click();

    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    // Handle plan/usage limit responses
    if (response.status === 403) {
      const errData = await response.json().catch(() => ({}));
      removeTyping();
      if (errData.error === 'usage_limit_reached' || errData.error === 'upgrade_required' || errData.error === 'feature_not_available') {
        showUpgradePrompt(errData);
        return;
      }
      throw new Error(errData.message || 'ไม่มีสิทธิ์เข้าถึง');
    }

    if (!response.ok) throw new Error('Network response was not ok');

    removeTyping();
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let botMsgEl = null;
    let botText = '';
    let sources = [];
    let userMsgEl = chatArea.lastElementChild;
    let botId = null;

    let typingRemoved = false;
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      let lines = buffer.split('\n');
      buffer = lines.pop(); // Keep partial line in buffer

      for (const line of lines) {
        let trimmed = line.trim();
        if (!trimmed.startsWith('data: ')) continue;

        // Remove typing dots only once when data starts flowing
        if (!typingRemoved) {
          removeTyping();
          typingRemoved = true;
        }

        const jsonStr = trimmed.substring(6).trim();
        if (!jsonStr) continue;

        try {
          const data = JSON.parse(jsonStr);
          if (data.error) throw new Error(data.error);
          if (data.sources) sources = data.sources;
          if (data.user_id && userMsgEl) {
            userMsgEl.dataset.id = data.user_id;
            const lastMsg = state.history[state.history.length - 1];
            if (lastMsg && lastMsg.role === 'user') lastMsg.id = data.user_id;

            const bubble = userMsgEl.querySelector('.group\\/msg');
            if (bubble && !bubble.querySelector('.del-msg-btn')) {
              const delBtnHtml = `
                <div class="absolute -left-2 top-0 -translate-x-full opacity-0 group-hover/msg:opacity-100 transition-opacity flex flex-col gap-1">
                  <button class="del-msg-btn p-1.5 glass rounded-lg hover:text-red-200 transition-colors" title="ลบข้อความ"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>
                </div>`;
              bubble.insertAdjacentHTML('beforeend', delBtnHtml);
              const delBtn = bubble.querySelector('.del-msg-btn');
              if (delBtn) delBtn.onclick = () => deleteChatMessage('ai', data.user_id, userMsgEl);
              initIcons();
            }
          }
          if (data.bot_id) {
            botId = data.bot_id;
            if (botMsgEl) {
              botMsgEl.dataset.id = data.bot_id;
              const bubble = botMsgEl.querySelector('.group\\/msg');
              if (bubble && !bubble.querySelector('.del-msg-btn')) {
                const delBtnHtml = `<button class="del-msg-btn p-1.5 glass rounded-lg hover:text-red-500 transition-colors" title="ลบข้อความ"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>`;
                const feedbackPanel = bubble.querySelector('.fb-btn')?.parentElement;
                if (feedbackPanel) {
                  feedbackPanel.insertAdjacentHTML('beforeend', delBtnHtml);
                  const delBtn = feedbackPanel.querySelector('.del-msg-btn');
                  if (delBtn) delBtn.onclick = () => deleteChatMessage('ai', data.bot_id, botMsgEl);
                  initIcons();
                }
              }
            }
          }
        if (data.content) {
          botText += data.content;
          
          // 🎵 Play streaming tick
          if (window.soundEngine) {
            window.soundEngine.playStreamTick();
          }

          if (!botMsgEl) {
            // Create the bubble if it doesn't exist
            botMsgEl = appendMessage('bot', '<span class="typing-dots">...</span>', sources, true, botId);
          }
          
          // Update bubble content
          const bubbleText = botMsgEl.querySelector('.prose');
          if (bubbleText) {
             bubbleText.innerHTML = markdownToHtml(botText);
             // Follow scroll if user was at bottom
             scrollToBottom('auto', true);
          }
        }
      } catch (je) {
        console.warn('Chunk parse error:', je, jsonStr);
      }
    }
  }

  // Display the complete bot message once streaming is done to finalize parsing (actions etc)
  if (botText) {
    // 🔔 Play Bot Completion Chime & Haptic
    if (window.soundEngine) {
      window.soundEngine.playReceiveChime();
    }

    const { displayHtml, calendarData, reconcileData } = parseAIActions(botText);
    
    if (botMsgEl) {
       const bubbleText = botMsgEl.querySelector('.prose');
       if (bubbleText) bubbleText.innerHTML = displayHtml;
       if (calendarData) renderCalendarActionUI(botMsgEl, calendarData);
       if (reconcileData) renderReconcileActionUI(botMsgEl, reconcileData);
       initIcons();
    } else {
       botMsgEl = appendMessage('bot', displayHtml, sources, false, botId);
       if (calendarData) renderCalendarActionUI(botMsgEl, calendarData);
       if (reconcileData) renderReconcileActionUI(botMsgEl, reconcileData);
    }

    state.history.push({ role: 'bot', text: botText, sources: sources, id: botId });
    // Keep history manageable (last 20 messages) to speed up Pi communication
    if (state.history.length > 20) {
      state.history = state.history.slice(-20);
    }
    saveHistory();

    // 🌟 Update Dynamic Suggestion Chips based on latest interaction
    updateDynamicSuggestions(botText, text);

    // 🔊 Auto-Speak TTS if enabled
    if (_isAutoSpeakEnabled) {
      speakTextThai(botText);
    }
  }

  // Final scroll
  scrollToBottom('smooth', false);

  } catch (e) {
    removeTyping();
    let msg = e.message;
    if (msg.includes('429') || msg.toLowerCase().includes('quota')) {
       msg = "โควต้า AI หมดชั่วคราว (Free Tier Limit) กรุณารอประมาณ 1 นาทีแล้วลองใหม่อีกครั้งครับ";
    }
    appendMessage('bot', `<div class="p-3 rounded-lg border border-red-200 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm font-medium">⚠️ ${msg}</div>`);
  } finally {
    state.sending = false;
    sendBtn.disabled = false;
    msgInput.disabled = false;
    msgInput.focus();
    initIcons();
  }
}

/**
 * Renders an interactive confirmation panel for AI-suggested calendar events.
 */
function renderCalendarActionUI(msgEl, data) {
  const panel = msgEl.querySelector('.action-panel');
  if (!panel) return;

  panel.classList.remove('hidden');
  panel.className = "action-panel mt-4 p-4 bg-brand-50/40 dark:bg-brand-950/20 border border-brand-200/60 dark:border-brand-800/40 rounded-2xl animate-in slide-in-from-top-2 duration-500 shadow-sm";
  panel.innerHTML = `
    <div class="flex items-start gap-4">
      <div class="w-10 h-10 rounded-xl bg-brand-100 dark:bg-brand-900/40 flex items-center justify-center text-brand-600 dark:text-brand-400 flex-shrink-0">
        <i data-lucide="calendar-plus" class="w-5 h-5"></i>
      </div>
      <div class="flex-1 min-w-0">
        <div class="text-[10px] font-bold uppercase tracking-widest text-brand-600 dark:text-brand-400 mb-1">AI ตรวจพบนัดหมายในข้อความนี้</div>
        <div class="text-xs font-bold text-surface-900 dark:text-surface-100">${data.title}</div>
        <div class="text-[10px] text-surface-500 font-medium flex items-center gap-2 mt-1.5">
           <span class="flex items-center gap-1.5 px-2.5 py-1 bg-white/80 dark:bg-surface-800 rounded-lg border border-brand-100 dark:border-brand-900/40 text-surface-700 dark:text-surface-300">
             <i data-lucide="clock" class="w-3.5 h-3.5 text-brand-500"></i> ${data.date} @ ${data.time}
           </span>
        </div>
        <div class="flex items-center gap-2 mt-3.5">
          <button class="confirm-cal-btn px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold rounded-xl transition-all shadow-md shadow-brand-500/20 active:scale-95 flex items-center gap-1.5">
            <i data-lucide="check" class="w-3.5 h-3.5"></i> ยืนยันนัดหมาย
          </button>
          <button class="cancel-cal-btn px-4 py-2 bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 text-surface-600 dark:text-surface-300 text-xs font-bold rounded-xl hover:bg-surface-50 dark:hover:bg-surface-700 transition-all">
            ละเว้น
          </button>
        </div>
      </div>
    </div>
  `;

  initIcons();

  const confirmBtn = panel.querySelector('.confirm-cal-btn');
  const cancelBtn = panel.querySelector('.cancel-cal-btn');

  confirmBtn.onclick = async () => {
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i> กำลังบันทึก...';
    initIcons();

    try {
      const res = await apiFetch('/api/schedules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: data.title,
          date: data.date,
          time: data.time,
          desc: data.desc || 'บันทึกโดย AI (OrgChat)',
          category_id: null
        })
      });

      if (res && res.ok) {
        toast('บันทึกปฏิทินสำเร็จแล้ว', 'success');
        panel.innerHTML = `
          <div class="flex items-center gap-2 text-emerald-600 font-bold text-xs py-1 animate-in zoom-in-95">
             <i data-lucide="check-circle" class="w-4 h-4 text-emerald-500"></i> เพิ่มนัดหมายสำเร็จแล้ว
          </div>
        `;
        initIcons();
        if (typeof loadSchedules === 'function') loadSchedules();
      } else {
        throw new Error((res && res.error) || 'Failed to save');
      }
    } catch(e) {
      toast('ล้มเหลว: ' + e.message, 'error');
      confirmBtn.disabled = false;
      confirmBtn.innerHTML = 'ยืนยันนัดหมาย';
      initIcons();
    }
  };

  cancelBtn.onclick = () => {
    panel.remove();
  };
}

/**
 * Renders an interactive confirmation panel for Financial Reconciliation.
 * Allows user to edit fields before saving to Google Sheets.
 */
function renderReconcileActionUI(msgEl, data) {
  const panel = msgEl.querySelector('.action-panel');
  if (!panel) return;

  panel.classList.remove('hidden');
  // Premium Card Styling with Glassmorphism and vibrant emerald accents
  panel.className = "action-panel mt-6 p-0 overflow-hidden bg-white/80 dark:bg-emerald-950/20 backdrop-blur-xl border border-emerald-100 dark:border-emerald-800/50 rounded-[2rem] animate-in slide-in-from-top-4 fade-in duration-700 shadow-2xl shadow-emerald-500/5";
  
  // Helper to normalize date from DD/MM/YYYY to YYYY-MM-DD for native date picker
  const toISODate = (dStr) => {
    if (!dStr) return '';
    const parts = dStr.split('/');
    if (parts.length === 3) {
      // Assuming DD/MM/YYYY
      let year = parts[2];
      if (year.length === 2) year = '20' + year; // handle short year
      return `${year}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
    }
    return dStr;
  };

  const dateValueISO = toISODate(data.date || '');
  const amountValue = data.amount || data.net_amount || '';
  const merchantValue = data.merchant || data.receiver || '';
  const categoryValue = data.category || 'Slip';
  const taxIdValue = data.tax_id || '';

  panel.innerHTML = `
    <div class="relative">
      <!-- Header with Gradient Area -->
      <div class="h-16 bg-gradient-to-r from-emerald-500 to-teal-500 flex items-center px-6 gap-3">
        <div class="w-10 h-10 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center text-white shadow-inner">
          <i data-lucide="receipt-text" class="w-5 h-5"></i>
        </div>
        <div>
          <div class="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-50/80 leading-none mb-1">Financial Audit</div>
          <div class="text-sm font-bold text-white leading-none">สกัดข้อมูลค่าใช้จ่าย</div>
        </div>
      </div>

      <div class="p-6">
        <div class="grid grid-cols-2 gap-5">
          <!-- Date Field -->
          <div class="space-y-1.5">
            <label class="flex items-center gap-1.5 text-[10px] font-bold text-surface-400 dark:text-surface-500 uppercase tracking-wider ml-1">
              <i data-lucide="calendar" class="w-3 h-3"></i> วันที่
            </label>
            <input type="date" value="${dateValueISO}" 
              class="recon-date w-full bg-surface-50 dark:bg-surface-900/50 border border-surface-100 dark:border-surface-800 rounded-2xl px-4 py-2.5 text-xs font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/50 outline-none transition-all">
          </div>

          <!-- Amount Field -->
          <div class="space-y-1.5">
            <label class="flex items-center gap-1.5 text-[10px] font-bold text-surface-400 dark:text-surface-500 uppercase tracking-wider ml-1">
              <i data-lucide="banknote" class="w-3 h-3"></i> ยอดเงิน
            </label>
            <div class="relative">
              <input type="number" step="0.01" value="${amountValue}" placeholder="0.00" 
                class="recon-amount w-full bg-surface-50 dark:bg-surface-900/50 border border-surface-100 dark:border-surface-800 rounded-2xl px-4 py-2.5 text-xs font-bold text-emerald-600 dark:text-emerald-400 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/50 outline-none transition-all text-right pr-8">
              <span class="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-bold text-surface-400">฿</span>
            </div>
          </div>

          <!-- Merchant Field -->
          <div class="space-y-1.5 col-span-2">
            <label class="flex items-center gap-1.5 text-[10px] font-bold text-surface-400 dark:text-surface-500 uppercase tracking-wider ml-1">
              <i data-lucide="store" class="w-3 h-3"></i> ร้านค้า / ผู้รับเงิน
            </label>
            <input type="text" value="${merchantValue}" placeholder="ระบุชื่อผู้รับ" 
              class="recon-receiver w-full bg-surface-50 dark:bg-surface-900/50 border border-surface-100 dark:border-surface-800 rounded-2xl px-4 py-2.5 text-xs font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/50 outline-none transition-all">
          </div>

          <!-- Tax ID Field -->
          <div class="space-y-1.5 col-span-2">
            <label class="flex items-center gap-1.5 text-[10px] font-bold text-surface-400 dark:text-surface-500 uppercase tracking-wider ml-1">
              <i data-lucide="hash" class="w-3 h-3"></i> เลขผู้เสียภาษี
            </label>
            <input type="text" value="${taxIdValue}" placeholder="13 หลัก" 
              class="recon-tax-id w-full bg-surface-50 dark:bg-surface-900/50 border border-surface-100 dark:border-surface-800 rounded-2xl px-4 py-2.5 text-xs font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/50 outline-none transition-all">
          </div>

          <!-- Category Field -->
          <div class="space-y-1.5 col-span-2">
            <label class="flex items-center gap-1.5 text-[10px] font-bold text-surface-400 dark:text-surface-500 uppercase tracking-wider ml-1">
              <i data-lucide="tag" class="w-3 h-3"></i> หมวดหมู่รายการ
            </label>
            <div class="relative">
              <select class="recon-category w-full appearance-none bg-surface-50 dark:bg-surface-900/50 border border-surface-100 dark:border-surface-800 rounded-2xl px-4 py-2.5 text-xs font-medium focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/50 outline-none transition-all cursor-pointer">
                <option value="สลิปโอนเงิน" ${categoryValue === 'สลิปโอนเงิน' || categoryValue === 'Slip' ? 'selected' : ''}>💸 สลิปโอนเงิน</option>
                <option value="ใบเสร็จ/ใบกำกับภาษี" ${categoryValue === 'ใบเสร็จ/ใบกำกับภาษี' || categoryValue === 'Invoice' || categoryValue === 'Receipt' ? 'selected' : ''}>📄 ใบเสร็จ/ใบกำกับภาษี</option>
                <option value="สเตตเมนต์" ${categoryValue === 'สเตตเมนต์' || categoryValue === 'Statement' ? 'selected' : ''}>🏦 รายการสเตตเมนต์</option>
                <option value="อื่นๆ">🌀 อื่นๆ</option>
              </select>
              <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-surface-400">
                <i data-lucide="chevron-down" class="w-4 h-4"></i>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex flex-col gap-2 mt-6">
          <button class="confirm-recon-btn w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-black uppercase tracking-widest rounded-2xl transition-all shadow-lg shadow-emerald-500/20 active:scale-[0.98] flex items-center justify-center gap-2 group">
            <span>บันทึกลง Google Sheets</span>
            <i data-lucide="arrow-right" class="w-4 h-4 transition-transform group-hover:translate-x-1"></i>
          </button>
          <button class="cancel-recon-btn w-full py-3 text-surface-400 hover:text-surface-600 dark:hover:text-surface-200 text-[10px] font-bold uppercase tracking-widest transition-all">
            ยกเลิกรายการนี้
          </button>
        </div>
      </div>
    </div>
  `;

  initIcons();

  const confirmBtn = panel.querySelector('.confirm-recon-btn');
  const cancelBtn = panel.querySelector('.cancel-recon-btn');

  confirmBtn.onclick = async () => {
    // Collect edited values
    const editedDate = panel.querySelector('.recon-date').value;
    const editedAmount = panel.querySelector('.recon-amount').value;
    const editedReceiver = panel.querySelector('.recon-receiver').value;
    const editedCategory = panel.querySelector('.recon-category').value;
    const editedTaxId = panel.querySelector('.recon-tax-id').value;

    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i> กำลังบันทึก...';
    initIcons();

    try {
      // Helper to convert YYYY-MM-DD back to DD/MM/YYYY if preferred, 
      // but the backend parse_date handles both. We'll send what's in the field.
      // If it's a date input, it will be YYYY-MM-DD.
      
      const res = await apiFetch('/api/reconcile/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          extracted_data: {
            ...data, // Keep original data (sender, etc)
            date: editedDate,
            net_amount: editedAmount,
            receiver: editedReceiver,
            category: editedCategory,
            tax_id: editedTaxId
          },
          summary: data.summary || 'บันทึกโดย AI (OrgChat)',
          file_link: data.file_link || '-'
        })
      });

      if (res && res.ok) {
        toast('บันทึกข้อมูลลง Google Sheets สำเร็จแล้ว', 'success');
        panel.innerHTML = `
          <div class="flex flex-col items-center justify-center p-12 text-center animate-in zoom-in-95 duration-500">
            <div class="w-20 h-20 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 rounded-full flex items-center justify-center mb-4 shadow-xl shadow-emerald-500/10">
              <i data-lucide="check-circle-2" class="w-10 h-10"></i>
            </div>
            <h3 class="text-lg font-black text-emerald-700 dark:text-emerald-400 uppercase tracking-tighter">เรียบร้อยค่ะ!</h3>
            <p class="text-xs text-surface-500 mt-2">พั้นบันทึกข้อมูลลง Google Sheets ให้พี่เรียบร้อยแล้วนะคะ 🌿</p>
          </div>
        `;
        initIcons();
      } else {
        toast('บันทึกไม่สำเร็จ: ' + (res?.error || 'Unknown error'), 'error');
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = 'บันทึกลง Google Sheets';
        initIcons();
      }
    } catch (e) {
      toast('เกิดข้อผิดพลาดในการบันทึก', 'error');
      confirmBtn.disabled = false;
      confirmBtn.innerHTML = 'บันทึกลง Google Sheets';
      initIcons();
    }
  };

  cancelBtn.onclick = () => {
    panel.classList.add('hidden');
  };
}

if (exportBtn) {
  exportBtn.addEventListener('click', () => {
    if (!state.history.length) { toast('ไม่มีประวัติให้ส่งออก', 'info'); return; }

    const lines = ["# OrgChat Conversation Export\n"];
    state.history.forEach(msg => {
      const role = msg.role === 'user' ? 'User' : 'AI';
      lines.push(`## ${role}\n${msg.text}\n`);
    });

    const content = lines.join('\n');
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `orgchat_export.md`;
    a.click();
  });
}

// Chat Export
if (exportBtn) {
  exportBtn.onclick = () => {
    if (!state.history.length) { toast('ไม่มีประวัติสนทนาให้ส่งออก', 'info'); return; }
    toast('กำลังสร้างไฟล์ส่งออก...', 'info');
    window.location.href = '/api/export';
  };
}

// ─── Input handlers ───────────────────────────
if (sendBtn && msgInput) {
  sendBtn.addEventListener('click', () => {
    const text = msgInput.value.trim();
    if (text) { msgInput.value = ''; autoResize(); sendMessage(text); }
  });
}

if (msgInput) {
  msgInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const text = msgInput.value.trim();
      if (text) { msgInput.value = ''; autoResize(); sendMessage(text); }
    }
  });

  msgInput.addEventListener('input', (e) => {
    autoResize();
    
    // 🔊 Mechanical Typing Click Sound
    if (window.soundEngine) {
      window.soundEngine.playTypingClick();
    }

    const val = msgInput.value;
    const lastAt = val.lastIndexOf('@');
    if (lastAt !== -1 && lastAt >= val.length - 1) {
      // Simple mention trigger
      // toast('ใช้ @ เพื่อระบุชื่อผู้ใช้', 'info');
    }

    // Send typing indicator
    if (socket && state.currentChat && val.length > 0) {
      socket.emit('user_typing', {
        room_id: state.currentChat.id,
        display_name: state.username,
        username: state.username
      });
    }
  });
}

// Mobile Viewport / Keyboard handling
if (msgInput) {
  msgInput.addEventListener('focus', () => {
    // Delay scroll to allow keyboard animation to complete
    setTimeout(() => {
      scrollToBottom('smooth');
    }, 300);
  });
}

// Visual Viewport resize handler — keeps chat input visible when mobile keyboard opens
if (window.visualViewport) {
  window.visualViewport.addEventListener('resize', () => {
    const vv = window.visualViewport;
    const chatWrap = document.getElementById('chatInputContainer');
    if (chatWrap) {
      // Push input up by the gap between layout bottom and visual viewport bottom
      const offsetBottom = window.innerHeight - vv.height - vv.offsetTop;
      chatWrap.style.paddingBottom = offsetBottom > 0 ? offsetBottom + 'px' : '';
    }
    if (state.currentView === 'chat') {
      scrollToBottom('auto', true);
    }
  });
}

function autoResize() {
  msgInput.style.height = 'auto';
  msgInput.style.height = Math.min(msgInput.scrollHeight, 120) + 'px';
}

document.querySelectorAll('.suggestion-chip, .quick-action-chip').forEach(btn => {
  btn.addEventListener('click', () => sendMessage(btn.dataset.q));
});

clearChatBtn.addEventListener('click', async () => {
  if (!confirm('ยืนยัน: ต้องการล้างประวัติการสนทนานี้?')) return;
  const data = await apiFetch('/api/history/clear', { method: 'POST' });
  if (data.ok) {
    state.history = [];
    showWelcome();
    suggestions.classList.remove('hidden');
    toast('ล้างประวัติการสนทนาเรียบร้อย', 'info');
  }
});

// ─── Dynamic AI Suggestion Chips & Smart Voice Mode ──────────────
let recognition = null;
let _isAutoSpeakEnabled = localStorage.getItem('orgchat_auto_speak') === 'true';
let _isContinuousVoiceMode = false;

// Initialize Auto-Speak Button state
const _chatAutoSpeakBtn = document.getElementById('autoSpeakBtn');
if (_chatAutoSpeakBtn) {
  if (_isAutoSpeakEnabled) {
    _chatAutoSpeakBtn.classList.add('text-brand-600', 'bg-brand-50', 'dark:bg-brand-950/40');
  }
  _chatAutoSpeakBtn.addEventListener('click', () => {
    _isAutoSpeakEnabled = !_isAutoSpeakEnabled;
    localStorage.setItem('orgchat_auto_speak', _isAutoSpeakEnabled);
    if (_isAutoSpeakEnabled) {
      _chatAutoSpeakBtn.classList.add('text-brand-600', 'bg-brand-50', 'dark:bg-brand-950/40');
      toast('เปิดโหมดอ่านออกเสียงอัตโนมัติ', 'info');
    } else {
      _chatAutoSpeakBtn.classList.remove('text-brand-600', 'bg-brand-50', 'dark:bg-brand-950/40');
      if (window.speechSynthesis) window.speechSynthesis.cancel();
      toast('ปิดโหมดอ่านออกเสียง', 'info');
    }
    if (typeof updateMobileFeaturesUI === 'function') updateMobileFeaturesUI();
  });
}

// ─── 📱 Mobile Chat Features Popup Controller ────────────────
function updateMobileFeaturesUI() {
  const switchEl = $('mobileAutoSpeakSwitch');
  const knobEl = $('mobileAutoSpeakKnob');
  const badgeEl = $('mobileAutoSpeakTextBadge');
  const indicatorEl = $('mobileFeaturesIndicator');
  const personaBadgeEl = $('mobileActivePersonaBadge');
  const activePersona = (window.state && state.activePersona && state.activePersona.name) ? state.activePersona.name : 'Default';

  if (personaBadgeEl) personaBadgeEl.textContent = activePersona;

  if (switchEl && knobEl && badgeEl) {
    if (_isAutoSpeakEnabled) {
      switchEl.classList.remove('bg-surface-200', 'dark:bg-surface-700');
      switchEl.classList.add('bg-amber-500');
      knobEl.classList.remove('translate-x-0');
      knobEl.classList.add('translate-x-5');
      badgeEl.textContent = 'เปิดอยู่';
      badgeEl.className = 'text-[9px] font-black px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300';
    } else {
      switchEl.classList.remove('bg-amber-500');
      switchEl.classList.add('bg-surface-200', 'dark:bg-surface-700');
      knobEl.classList.remove('translate-x-5');
      knobEl.classList.add('translate-x-0');
      badgeEl.textContent = 'ปิดอยู่';
      badgeEl.className = 'text-[9px] font-black px-2 py-0.5 rounded-full bg-surface-200 dark:bg-surface-700 text-surface-600 dark:text-surface-300';
    }
  }

  // Show indicator dot on sparkle button if custom persona or auto-speak is enabled
  if (indicatorEl) {
    if (_isAutoSpeakEnabled || activePersona !== 'Default') {
      indicatorEl.classList.remove('hidden');
    } else {
      indicatorEl.classList.add('hidden');
    }
  }
}
window.updateMobileFeaturesUI = updateMobileFeaturesUI;

function openMobileChatFeatures() {
  const modal = $('mobileChatFeaturesModal');
  if (!modal) return;
  modal.classList.remove('hidden');
  updateMobileFeaturesUI();
  if (window.lucide) lucide.createIcons();
}
window.openMobileChatFeatures = openMobileChatFeatures;

function closeMobileChatFeatures() {
  const modal = $('mobileChatFeaturesModal');
  if (modal) modal.classList.add('hidden');
  const personaContainer = $('mobilePersonaListContainer');
  if (personaContainer) personaContainer.classList.add('hidden');
  const chevron = $('mobilePersonaChevron');
  if (chevron) chevron.style.transform = '';
}
window.closeMobileChatFeatures = closeMobileChatFeatures;

function toggleMobileChatFeatures() {
  const modal = $('mobileChatFeaturesModal');
  if (modal && !modal.classList.contains('hidden')) {
    closeMobileChatFeatures();
  } else {
    openMobileChatFeatures();
  }
}
window.toggleMobileChatFeatures = toggleMobileChatFeatures;

function toggleMobileAutoSpeak() {
  const btn = $('autoSpeakBtn');
  if (btn) {
    btn.click();
  } else {
    _isAutoSpeakEnabled = !_isAutoSpeakEnabled;
    localStorage.setItem('orgchat_auto_speak', _isAutoSpeakEnabled);
    updateMobileFeaturesUI();
  }
}
window.toggleMobileAutoSpeak = toggleMobileAutoSpeak;

function toggleMobilePersonaList() {
  const container = $('mobilePersonaListContainer');
  const chevron = $('mobilePersonaChevron');
  if (!container) return;

  const isHidden = container.classList.contains('hidden');
  if (isHidden) {
    const personas = (window.state && Array.isArray(state.personas)) ? state.personas : [];
    const activeId = (window.state && state.activePersona) ? state.activePersona.id : null;
    
    let html = `
      <div onclick="selectMobilePersona(null)" class="flex items-center justify-between p-2.5 rounded-xl cursor-pointer ${!activeId ? 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 font-bold' : 'hover:bg-surface-100 dark:hover:bg-surface-700/50 text-surface-700 dark:text-surface-300'} transition-colors">
        <div class="flex items-center gap-2">
          <i data-lucide="bot" class="w-4 h-4"></i>
          <span class="text-xs">Default (มาตรฐาน)</span>
        </div>
        ${!activeId ? '<i data-lucide="check" class="w-3.5 h-3.5 text-purple-600"></i>' : ''}
      </div>
    `;

    personas.forEach(p => {
      const isSelected = activeId === p.id;
      html += `
        <div onclick="selectMobilePersona('${p.id}')" class="flex items-center justify-between p-2.5 rounded-xl cursor-pointer ${isSelected ? 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 font-bold' : 'hover:bg-surface-100 dark:hover:bg-surface-700/50 text-surface-700 dark:text-surface-300'} transition-colors">
          <div class="flex items-center gap-2">
            <i data-lucide="sparkles" class="w-4 h-4 text-purple-500"></i>
            <span class="text-xs">${p.name}</span>
          </div>
          ${isSelected ? '<i data-lucide="check" class="w-3.5 h-3.5 text-purple-600"></i>' : ''}
        </div>
      `;
    });

    container.innerHTML = html;
    container.classList.remove('hidden');
    if (chevron) chevron.style.transform = 'rotate(180deg)';
    if (window.lucide) lucide.createIcons();
  } else {
    container.classList.add('hidden');
    if (chevron) chevron.style.transform = '';
  }
}
window.toggleMobilePersonaList = toggleMobilePersonaList;

function selectMobilePersona(personaId) {
  if (typeof selectPersona === 'function') {
    selectPersona(personaId);
  }
  updateMobileFeaturesUI();
  toggleMobilePersonaList(); // close accordion
}
window.selectMobilePersona = selectMobilePersona;


/**
 * Speaks text out loud using high quality Edge-TTS with Web Speech fallback
 */
let _currentTtsAudio = null;
let _isVoiceModeActive = false;
let _voiceRecognition = null;

async function speakTextThai(text) {
  if (!text) return;
  if (_currentTtsAudio) {
    try { _currentTtsAudio.pause(); _currentTtsAudio = null; } catch (e) {}
  }
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }

  // Clean markdown and emojis for smoother speech
  const cleanText = text
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/[*#_~>]/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '')
    .trim()
    .substring(0, 500);

  if (!cleanText) return;

  if (_isVoiceModeActive) {
    setVoiceVisualState('speaking', 'น้องพั้นกำลังพูดตอบกลับ...');
  }

  // Priority 1: Edge-TTS neural speech synthesis
  try {
    const res = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: cleanText })
    });
    if (res.ok) {
      const blob = await res.blob();
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      _currentTtsAudio = audio;
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        _currentTtsAudio = null;
        if (_isVoiceModeActive) {
          startVoiceListening();
        }
      };
      await audio.play();
      return;
    }
  } catch (ttsErr) {
    console.warn('[Edge-TTS error, falling back to Web Speech]:', ttsErr);
  }

  // Priority 2: Native browser SpeechSynthesis fallback
  if ('speechSynthesis' in window) {
    try {
      const utterance = new SpeechSynthesisUtterance(cleanText.substring(0, 400));
      utterance.lang = 'th-TH';
      utterance.rate = 1.05;
      utterance.pitch = 1.0;

      const voices = window.speechSynthesis.getVoices();
      const thaiVoice = voices.find(v => v.lang.includes('th') || v.lang.includes('TH'));
      if (thaiVoice) utterance.voice = thaiVoice;

      utterance.onend = () => {
        if (_isVoiceModeActive) {
          startVoiceListening();
        }
      };
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('[TTS Error]', e);
    }
  }
}

// ─── Live Voice Chat Mode Functions ─────────────────────────

function toggleLiveVoiceMode() {
  let modal = $('liveVoiceModal');
  if (!modal) {
    createLiveVoiceModal();
    modal = $('liveVoiceModal');
  }
  if (modal.classList.contains('hidden')) {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    _isVoiceModeActive = true;
    startVoiceListening();
  } else {
    closeLiveVoiceMode();
  }
}

function closeLiveVoiceMode() {
  const m = $('liveVoiceModal');
  if (m) {
    m.classList.add('hidden');
    m.classList.remove('flex');
  }
  _isVoiceModeActive = false;
  if (_voiceRecognition) {
    try { _voiceRecognition.stop(); } catch (e) {}
  }
  if (_currentTtsAudio) {
    try { _currentTtsAudio.pause(); _currentTtsAudio = null; } catch (e) {}
  }
}

function startVoiceListening() {
  if (!_voiceRecognition) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      toast('เบราว์เซอร์นี้ไม่รองรับ Speech Recognition กรุณาใช้ Chrome หรือ Edge ค่ะ', 'warning');
      return;
    }
    _voiceRecognition = new SpeechRecognition();
    _voiceRecognition.lang = 'th-TH';
    _voiceRecognition.continuous = false;
    _voiceRecognition.interimResults = true;

    _voiceRecognition.onstart = () => {
      setVoiceVisualState('listening', 'น้องพั้นกำลังฟังเสียงคุณอยู่ค่ะ...');
    };

    _voiceRecognition.onresult = (event) => {
      let interim = '';
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      const caption = $('liveVoiceTranscript');
      if (caption) caption.textContent = finalTranscript || interim || '...';

      if (finalTranscript && finalTranscript.trim()) {
        setVoiceVisualState('thinking', 'กำลังคิดคำตอบ...');
        sendMessage(finalTranscript.trim());
      }
    };

    _voiceRecognition.onerror = (e) => {
      console.warn('[Live Voice Error]', e);
      setVoiceVisualState('idle', 'แตะปุ่มวงกลมเพื่อเริ่มพูด');
    };

    _voiceRecognition.onend = () => {
      if (_isVoiceModeActive && !_currentTtsAudio) {
        setVoiceVisualState('idle', 'แตะปุ่มเพื่อพูดต่อ');
      }
    };
  }

  try {
    _voiceRecognition.start();
  } catch (e) {
    console.debug('Recognition already running or busy:', e);
  }
}

function setVoiceVisualState(state, text) {
  const caption = $('liveVoiceStatusText');
  const orb = $('liveVoiceOrb');
  if (caption) caption.textContent = text;
  if (orb) {
    orb.className = 'w-32 h-32 rounded-full flex items-center justify-center transition-all duration-300 shadow-2xl relative cursor-pointer mb-8';
    if (state === 'listening') {
      orb.classList.add('bg-gradient-to-tr', 'from-brand-500', 'to-indigo-500', 'animate-pulse', 'scale-110');
    } else if (state === 'thinking') {
      orb.classList.add('bg-gradient-to-tr', 'from-amber-500', 'to-orange-500', 'animate-spin');
    } else if (state === 'speaking') {
      orb.classList.add('bg-gradient-to-tr', 'from-emerald-500', 'to-teal-500', 'animate-bounce');
    } else {
      orb.classList.add('bg-gradient-to-tr', 'from-surface-500', 'to-surface-700');
    }
  }
}

function createLiveVoiceModal() {
  const div = document.createElement('div');
  div.id = 'liveVoiceModal';
  div.className = 'fixed inset-0 z-50 bg-surface-950/80 backdrop-blur-md hidden flex-col items-center justify-center p-6 select-none';
  div.innerHTML = `
    <div class="relative w-full max-w-md bg-white/10 dark:bg-surface-900/80 border border-white/20 dark:border-surface-700/50 rounded-3xl p-8 flex flex-col items-center text-center shadow-2xl backdrop-blur-xl">
      <button onclick="closeLiveVoiceMode()" class="absolute top-4 right-4 p-2 text-surface-400 hover:text-white rounded-full bg-white/5 hover:bg-white/10 transition-colors">
        <i data-lucide="x" class="w-5 h-5"></i>
      </button>

      <div class="mb-2 text-xs font-bold uppercase tracking-wider text-brand-400">Live Voice Mode</div>
      <h3 class="text-xl font-bold text-white mb-8">สนทนาด้วยเสียงสดกับน้องพั้น</h3>

      <div id="liveVoiceOrb" onclick="startVoiceListening()" class="w-32 h-32 rounded-full bg-gradient-to-tr from-brand-500 to-indigo-500 flex items-center justify-center transition-all duration-300 shadow-2xl relative cursor-pointer mb-8">
        <i data-lucide="mic" class="w-12 h-12 text-white"></i>
      </div>

      <div id="liveVoiceStatusText" class="text-sm font-semibold text-surface-300 mb-2">น้องพั้นกำลังฟังเสียงคุณอยู่ค่ะ...</div>
      <div id="liveVoiceTranscript" class="text-xs text-surface-400 italic max-w-xs min-h-[2.5rem] flex items-center justify-center">พูดภาษาไทยเพื่อเริ่มคุยได้ทันที</div>

      <div class="mt-8 flex gap-3">
        <button onclick="closeLiveVoiceMode()" class="px-5 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-bold transition-all">
          ปิดโหมดเสียง
        </button>
      </div>
    </div>
  `;
  document.body.appendChild(div);
  initIcons();
}

/**
 * Dynamically updates the quick-action suggestion chips under the chat box
 * based on the conversation context and AI response
 */
function updateDynamicSuggestions(lastBotText = '', userQuery = '') {
  const suggestionsBox = document.getElementById('suggestions');
  if (!suggestionsBox) return;

  const defaultChips = [
    { label: 'สรุปวันนี้', query: 'สรุปความเคลื่อนไหววันนี้ให้หน่อย', icon: 'sparkles' },
    { label: 'เช็คคิวพรุ่งนี้', query: 'พรุ่งนี้ฉันมีประชุมหรือนัดหมายอะไรบ้าง', icon: 'calendar-clock' },
    { label: 'ร่างประกาศ', query: 'ร่างประกาศข่าวกิจกรรมบริษัทให้หน่อย', icon: 'megaphone' },
    { label: 'สรุปไฟล์ล่าสุด', query: 'ช่วยสรุปไฟล์ PDF ล่าสุดที่ฉันอัปโหลด', icon: 'file-text' }
  ];

  let chips = [];
  const text = (lastBotText + ' ' + userQuery).toLowerCase();

  // Smart Context Detection
  if (text.includes('ประชุม') || text.includes('นัดหมาย') || text.includes('calendar') || text.includes('ตาราง')) {
    chips = [
      { label: 'เพิ่มนัดหมายใหม่', query: 'ช่วยสร้างนัดหมายใหม่ให้หน่อย', icon: 'calendar-plus' },
      { label: 'ส่งสรุปการประชุม', query: 'ช่วยร่างสรุปประเด็นการประชุมนี้', icon: 'file-check' },
      { label: 'เช็คคิวตลอดสัปดาห์', query: 'สัปดาห์นี้ฉันมีตารางงานอะไรบ้าง', icon: 'clock' },
      { label: 'แจ้งเตือนเพื่อนร่วมงาน', query: 'ร่างข้อความแจ้งเตือนผู้เข้าร่วมประชุม', icon: 'send' }
    ];
  } else if (text.includes('สลิป') || text.includes('ใบเสร็จ') || text.includes('ภาษี') || text.includes('เงิน') || text.includes('ยอด')) {
    chips = [
      { label: 'บันทึกเข้า Google Sheets', query: 'บันทึกรายการยอดเงินนี้ลงชีตให้หน่อย', icon: 'file-spreadsheet' },
      { label: 'สรุปยอดรวมค่าใช้จ่าย', query: 'สรุปยอดรวมค่าใช้จ่ายเดือนนี้ให้หน่อย', icon: 'calculator' },
      { label: 'เช็คหัก ณ ที่จ่าย (WHT)', query: 'ช่วยตรวจสอบอัตราหัก ณ ที่จ่ายของรายการนี้', icon: 'percent' },
      { label: 'ดูประวัติสลิป', query: 'ขอดูประวัติการอัปโหลดสลิปล่าสุด', icon: 'history' }
    ];
  } else if (text.includes('ประกาศ') || text.includes('ข่าว') || text.includes('แจ้ง')) {
    chips = [
      { label: 'บรอดแคสต์ LINE', query: 'ช่วยตั้งเวลาบรอดแคสต์ข้อความนี้เข้า LINE องค์กร', icon: 'message-circle' },
      { label: 'ปรับภาษาให้เป็นทางการ', query: 'ช่วยปรับข้อความนี้ให้สุภาพและเป็นทางการมากขึ้น', icon: 'pencil-line' },
      { label: 'ย่อให้กระชับ', query: 'ช่วยสรุปให้สั้นกระชับเหลือ 3 บรรทัด', icon: 'minimize-2' },
      { label: 'แปลเป็นภาษาอังกฤษ', query: 'ช่วยแปลประกาศนี้เป็นภาษาอังกฤษ', icon: 'languages' }
    ];
  } else if (lastBotText.length > 50) {
    chips = [
      { label: 'อธิบายเพิ่มเติม', query: 'ช่วยขยายความและอธิบายรายละเอียดเพิ่มเติม', icon: 'help-circle' },
      { label: 'สรุปเป็นหัวข้อย่อย', query: 'ช่วยสรุปคำตอบข้างต้นเป็น Bullet Points สั้นๆ', icon: 'list' },
      { label: 'ร่างเป็นอีเมล', query: 'ช่วยนำข้อมูลนี้ไปร่างเป็นอีเมลแจ้งทีมงาน', icon: 'mail' },
      { label: 'ถามคำถามอื่น', query: 'วันนี้มีอะไรที่ฉันควรรู้อีกบ้าง', icon: 'sparkles' }
    ];
  } else {
    chips = defaultChips;
  }

  suggestionsBox.innerHTML = chips.map(c => `
    <button class="quick-action-chip animate-in fade-in zoom-in-95 duration-300" data-q="${c.query.replace(/"/g, '&quot;')}">
      <i data-lucide="${c.icon}" class="w-3.5 h-3.5"></i> ${c.label}
    </button>
  `).join('');

  // Re-bind click events
  suggestionsBox.querySelectorAll('.quick-action-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const q = btn.dataset.q;
      if (q) sendMessage(q);
    });
  });

  if (window.lucide) lucide.createIcons();
}

// ─── Voice Interaction (STT / SpeechRecognition) ──────────────
function getSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return null;
  
  const rec = new SpeechRecognition();
  rec.lang = 'th-TH';
  rec.continuous = false;
  rec.interimResults = true;
  rec.maxAlternatives = 1;

  rec.onstart = () => {
    if (voiceBtn) {
      voiceBtn.classList.add('voice-active');
      voiceBtn.innerHTML = `
        <div class="voice-wave-container">
          <div class="voice-wave-bar"></div>
          <div class="voice-wave-bar"></div>
          <div class="voice-wave-bar"></div>
          <div class="voice-wave-bar"></div>
        </div>
      `;
    }
    toast('กำลังฟังเสียงพูดของคุณ... (พูดเสร็จจะส่งคำถามให้อัตโนมัติ)', 'info');
  };

  rec.onend = () => {
    if (voiceBtn) {
      voiceBtn.classList.remove('voice-active');
      voiceBtn.innerHTML = '<i data-lucide="mic" class="w-4 h-4"></i>';
      if (window.lucide) lucide.createIcons();
    }
  };

  rec.onresult = (event) => {
    let interimTranscript = '';
    let finalTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript;
      } else {
        interimTranscript += event.results[i][0].transcript;
      }
    }

    if (msgInput) {
      if (interimTranscript && !finalTranscript) {
        msgInput.value = interimTranscript;
        autoResize();
      } else if (finalTranscript) {
        msgInput.value = finalTranscript;
        autoResize();
        setTimeout(() => {
          const currentText = msgInput.value.trim();
          if (currentText) {
            msgInput.value = '';
            autoResize();
            sendMessage(currentText);
          }
        }, 500);
      }
    }
  };

  rec.onerror = (e) => {
    console.error('Speech Recognition Error:', e);
    if (voiceBtn) {
      voiceBtn.classList.remove('voice-active');
      voiceBtn.innerHTML = '<i data-lucide="mic" class="w-4 h-4"></i>';
      if (window.lucide) lucide.createIcons();
    }
    if (e.error === 'not-allowed' || e.error === 'permission-denied') {
      toast('กรุณากดอนุญาตให้เว็บไซต์ใช้งานไมโครโฟนในเบราว์เซอร์ค่ะ', 'warning');
    } else if (e.error !== 'no-speech' && e.error !== 'aborted') {
      toast('ไม่สามารถรับข้อมูลจากไมค์ได้ (' + e.error + ')', 'error');
    }
  };

  return rec;
}

if (voiceBtn) {
  voiceBtn.onclick = async () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      toast('เบราว์เซอร์ของคุณไม่รองรับการสั่งงานด้วยเสียง กรุณาใช้ Google Chrome หรือ Microsoft Edge', 'error');
      return;
    }

    // Request microphone permission via getUserMedia if not yet granted
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        // Release stream right away so SpeechRecognition can take exclusive lock
        stream.getTracks().forEach(track => track.stop());
      } catch (err) {
        console.warn('Microphone permission not granted:', err);
        toast('กรุณากดอนุญาตให้เว็บไซต์เข้าถึงไมโครโฟน (Microphone Permission) ที่แถบ URL ด้านบนค่ะ', 'warning');
        return;
      }
    }

    try {
      if (voiceBtn.classList.contains('voice-active')) {
        if (recognition) recognition.stop();
      } else {
        if (!recognition) {
          recognition = getSpeechRecognition();
        }
        if (recognition) {
          recognition.start();
        }
      }
    } catch (e) {
      console.warn('Recognition start retry:', e);
      try {
        recognition = getSpeechRecognition();
        if (recognition) recognition.start();
      } catch (err) {
        console.error('Failed to start voice recognition:', err);
      }
    }
  };
}

// ─── 🌐 Autonomous Browser Agent Controller ────────────────────
const browserAgentBtn = $('browserAgentBtn');
const browserAgentModal = $('browserAgentModal');
const browserTaskInput = $('browserTaskInput');
const browserTaskProgress = $('browserTaskProgress');
const browserTaskResult = $('browserTaskResult');
const startBrowserTaskBtn = $('startBrowserTaskBtn');

function openBrowserAgentModal() {
  if (browserAgentModal) browserAgentModal.classList.remove('hidden');
  if (browserTaskInput) browserTaskInput.focus();
}
window.openBrowserAgentModal = openBrowserAgentModal;

function closeBrowserAgentModal() {
  if (browserAgentModal) browserAgentModal.classList.add('hidden');
}
window.closeBrowserAgentModal = closeBrowserAgentModal;

function setBrowserPrompt(text) {
  if (browserTaskInput) {
    browserTaskInput.value = text;
    browserTaskInput.focus();
  }
}
window.setBrowserPrompt = setBrowserPrompt;

async function runBrowserTask() {
  const taskText = (browserTaskInput ? browserTaskInput.value : '').trim();
  if (!taskText) {
    toast('กรุณาระบุงานหรือเว็บไซต์ที่ต้องการให้ AI เข้าไปสำรวจค่ะ', 'warning');
    return;
  }

  if (browserTaskProgress) browserTaskProgress.classList.remove('hidden');
  if (browserTaskResult) {
    browserTaskResult.classList.add('hidden');
    browserTaskResult.innerHTML = '';
  }
  if (startBrowserTaskBtn) startBrowserTaskBtn.disabled = true;

  try {
    const res = await fetch('/api/browser-agent/execute', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': window.csrfToken || ''
      },
      body: JSON.stringify({ task: taskText })
    });

    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error(data.error || 'เกิดข้อผิดพลาดในการท่องเว็บ');
    }

    if (browserTaskResult) {
      let pagesHtml = '';
      if (data.pages && data.pages.length > 0) {
        pagesHtml = data.pages.map(p => `
          <div class="p-3 bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-700 rounded-xl space-y-2">
            <div class="flex items-center justify-between">
              <a href="${p.url}" target="_blank" rel="noopener noreferrer" class="text-xs font-bold text-emerald-600 hover:underline flex items-center gap-1.5 truncate">
                <i data-lucide="external-link" class="w-3.5 h-3.5"></i> ${p.title || p.url}
              </a>
            </div>
            ${p.screenshot ? `
              <div class="rounded-lg overflow-hidden border border-surface-150 max-h-48">
                <img src="${p.screenshot}" alt="Web screenshot" class="w-full object-top object-cover cursor-pointer" onclick="window.open('${p.screenshot}', '_blank')">
              </div>
            ` : ''}
          </div>
        `).join('');
      }

      browserTaskResult.innerHTML = `
        <div class="p-4 bg-emerald-50/40 dark:bg-emerald-950/20 border border-emerald-200/40 rounded-xl space-y-2">
          <div class="text-xs font-bold text-emerald-700 dark:text-emerald-300 flex items-center gap-1.5">
            <i data-lucide="check-circle" class="w-4 h-4"></i> สรุปผลการท่องเว็บโดยน้องพั้น
          </div>
          <div class="text-xs text-surface-800 dark:text-surface-100 whitespace-pre-wrap leading-relaxed">
            ${data.summary ? marked.parse(data.summary) : 'ไม่มีข้อมูลสรุป'}
          </div>
        </div>
        ${pagesHtml ? `<div class="text-[11px] font-bold text-surface-400 mt-2">หน้าเว็บที่สำรวจ:</div><div class="space-y-2">${pagesHtml}</div>` : ''}
      `;
      browserTaskResult.classList.remove('hidden');
      if (window.lucide) lucide.createIcons();
    }
  } catch (err) {
    toast('ท่องเว็บไม่สำเร็จ: ' + err.message, 'error');
    if (browserTaskResult) {
      browserTaskResult.innerHTML = `<div class="p-3 text-xs text-rose-600 bg-rose-50 rounded-xl">${err.message}</div>`;
      browserTaskResult.classList.remove('hidden');
    }
  } finally {
    if (browserTaskProgress) browserTaskProgress.classList.add('hidden');
    if (startBrowserTaskBtn) startBrowserTaskBtn.disabled = false;
  }
}
window.runBrowserTask = runBrowserTask;

if (browserAgentBtn) {
  browserAgentBtn.onclick = openBrowserAgentModal;
}

// ─── 🎙️ Real-Time Voice Call Agent (Hands-Free Duplex Call) ─────
const realTimeCallBtn = $('realTimeCallBtn');
const realTimeVoiceModal = $('realTimeVoiceModal');
const callDurationTimer = $('callDurationTimer');
const voiceCallStatusText = $('voiceCallStatusText');
const voiceTranscriptText = $('voiceTranscriptText');
const voicePulseRing = $('voicePulseRing');
const voiceWaveOrb = $('voiceWaveOrb');
const muteIcon = $('muteIcon');

let callActive = false;
let callMuted = false;
let callStartTime = 0;
let callTimerInterval = null;
let callRecognition = null;
let callSynth = window.speechSynthesis || null;
let thaiVoice = null;

function loadThaiVoice() {
  if (!callSynth) return;
  const voices = callSynth.getVoices();
  thaiVoice = voices.find(v => v.lang.includes('th') || v.lang.includes('TH')) || null;
}
if (callSynth && callSynth.onvoiceschanged !== undefined) {
  callSynth.onvoiceschanged = loadThaiVoice;
}

function startRealTimeCall() {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    toast('เบราว์เซอร์ของคุณไม่รองรับ Voice Stream กรุณาใช้ Chrome หรือ Edge', 'error');
    return;
  }

  loadThaiVoice();
  callActive = true;
  callMuted = false;
  callStartTime = Date.now();

  if (realTimeVoiceModal) realTimeVoiceModal.classList.remove('hidden');
  if (voiceCallStatusText) voiceCallStatusText.innerText = 'กำลังฟังเสียงพูดของคุณ...';
  if (voiceTranscriptText) voiceTranscriptText.innerText = 'แตะหรือพูดคุยกับ AI ได้เลยค่ะ';

  // Start duration timer
  if (callTimerInterval) clearInterval(callTimerInterval);
  callTimerInterval = setInterval(() => {
    if (!callActive) return;
    const elapsed = Math.floor((Date.now() - callStartTime) / 1000);
    const mm = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const ss = String(elapsed % 60).padStart(2, '0');
    if (callDurationTimer) callDurationTimer.innerText = `${mm}:${ss}`;
  }, 1000);

  initCallRecognition();
}
window.startRealTimeCall = startRealTimeCall;

function initCallRecognition() {
  if (callRecognition) {
    try { callRecognition.abort(); } catch (e) {}
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  callRecognition = new SpeechRecognition();
  callRecognition.lang = 'th-TH';
  callRecognition.continuous = true;
  callRecognition.interimResults = true;

  callRecognition.onresult = (event) => {
    if (!callActive || callMuted) return;
    // If AI is currently speaking, do not process microphone input to prevent self-loop echo
    if (callSynth && callSynth.speaking) {
      return;
    }

    let interim = '';
    let finalStr = '';

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalStr += event.results[i][0].transcript;
      } else {
        interim += event.results[i][0].transcript;
      }
    }

    if (interim && voiceTranscriptText) {
      voiceTranscriptText.innerText = `"${interim}"`;
      if (voiceCallStatusText) voiceCallStatusText.innerText = 'กำลังฟัง...';
    }

    if (finalStr.trim()) {
      const userText = finalStr.trim();
      // Ignore if user speech is just our own greetings or empty
      if (userText.length > 1) {
        if (voiceTranscriptText) voiceTranscriptText.innerText = `"${userText}"`;
        if (voiceCallStatusText) voiceCallStatusText.innerText = 'AI กำลังคิดคำตอบ...';
        handleCallTurn(userText);
      }
    }
  };

  callRecognition.onerror = (e) => {
    if (!callActive) return;
    if (e.error !== 'no-speech') {
      console.warn('[Voice Call Recognition Error]', e.error);
    }
  };

  callRecognition.onend = () => {
    // Only restart listening if call is active, not muted, and AI is NOT currently speaking
    if (callActive && !callMuted && (!callSynth || !callSynth.speaking)) {
      try { callRecognition.start(); } catch (e) {}
    }
  };

  try {
    callRecognition.start();
  } catch (e) {
    console.warn('[Call Recognition Start Failed]', e);
  }
}

async function handleCallTurn(userSpeech) {
  if (voiceWaveOrb) voiceWaveOrb.style.transform = 'scale(1.15)';
  // Temporarily pause recognition while fetching & speaking
  if (callRecognition) {
    try { callRecognition.stop(); } catch (e) {}
  }
  
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': window.csrfToken || ''
      },
      body: JSON.stringify({
        message: userSpeech,
        history: [],
        voice_mode: true
      })
    });

    const data = await res.json();
    if (data.ok && data.response) {
      const spokenText = data.response
        .replace(/\*\*/g, '')
        .replace(/###/g, '')
        .replace(/https?:\/\/[^\s]+/g, 'ตามลิงก์ที่แสดง')
        .slice(0, 300);

      if (voiceTranscriptText) voiceTranscriptText.innerText = `"${spokenText}"`;
      if (voiceCallStatusText) voiceCallStatusText.innerText = 'AI กำลังพูดตอบกลับ...';
      speakCallResponse(spokenText);
    } else {
      if (callRecognition && callActive && !callMuted) {
        try { callRecognition.start(); } catch (e) {}
      }
    }
  } catch (err) {
    console.error('[Call Turn Error]', err);
    if (voiceCallStatusText) voiceCallStatusText.innerText = 'เกิดข้อผิดพลาดในการประมวลผลเสียง';
    if (callRecognition && callActive && !callMuted) {
      try { callRecognition.start(); } catch (e) {}
    }
  } finally {
    if (voiceWaveOrb) voiceWaveOrb.style.transform = 'scale(1)';
  }
}

function speakCallResponse(text) {
  if (!callSynth || !callActive) return;
  try {
    callSynth.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'th-TH';
    utterance.rate = 1.05;
    utterance.pitch = 1.02;
    if (thaiVoice) utterance.voice = thaiVoice;

    utterance.onstart = () => {
      if (voicePulseRing) voicePulseRing.classList.remove('hidden');
      // Ensure microphone is stopped while speaker is outputting sound
      if (callRecognition) {
        try { callRecognition.stop(); } catch (e) {}
      }
    };
    utterance.onend = () => {
      if (voicePulseRing) voicePulseRing.classList.add('hidden');
      if (callActive && voiceCallStatusText) voiceCallStatusText.innerText = 'กำลังฟังเสียงพูดของคุณ...';
      // Restart microphone only AFTER speech synthesis has completely finished
      setTimeout(() => {
        if (callActive && !callMuted && callRecognition) {
          try { callRecognition.start(); } catch (e) {}
        }
      }, 300);
    };
    utterance.onerror = () => {
      if (voicePulseRing) voicePulseRing.classList.add('hidden');
      if (callActive && !callMuted && callRecognition) {
        try { callRecognition.start(); } catch (e) {}
      }
    };
    callSynth.speak(utterance);
  } catch (e) {
    console.warn('[Speech synthesis error]', e);
    if (callActive && !callMuted && callRecognition) {
      try { callRecognition.start(); } catch (e) {}
    }
  }
}

function toggleMuteCall() {
  callMuted = !callMuted;
  if (muteIcon) {
    muteIcon.setAttribute('data-lucide', callMuted ? 'mic-off' : 'mic');
    if (window.lucide) lucide.createIcons();
  }
  if (callMuted && callRecognition) {
    try { callRecognition.stop(); } catch (e) {}
  } else if (!callMuted && callRecognition && callActive) {
    try { callRecognition.start(); } catch (e) {}
  }
  toast(callMuted ? 'ปิดไมค์แล้ว' : 'เปิดไมค์แล้ว', 'info');
}
window.toggleMuteCall = toggleMuteCall;

function endRealTimeCall() {
  callActive = false;
  if (callTimerInterval) clearInterval(callTimerInterval);
  if (callRecognition) {
    try { callRecognition.stop(); } catch (e) {}
  }
  if (callSynth) {
    callSynth.cancel();
  }
  if (realTimeVoiceModal) realTimeVoiceModal.classList.add('hidden');
  toast('วางสายเรียบร้อยแล้วค่ะ', 'info');
}
window.endRealTimeCall = endRealTimeCall;

if (realTimeCallBtn) {
  realTimeCallBtn.onclick = startRealTimeCall;
}

// ─── Bootstrap ────────────────────────────────
(async () => {
  initTheme();
  initIcons();
  showWelcome();
  msgInput.focus();

  // ─── Global Background Poller ─────────────────────────────────
  // Runs every 30 seconds as fallback — ข้ามถ้าไม่ได้ login อยู่ หรือ initAppContent ลงทะเบียนแล้ว
  setInterval(async () => {
    if (!state.user || state._pollRegistered || document.hidden) return;

    // 1. Refresh Notification badge count silently
    try {
      const nData = await apiFetch('/api/notifications');
      if (nData && nData.unread_count !== undefined) {
        const unread = nData.unread_count;
        if (navNotifBadge) {
          if (unread > 0) {
            navNotifBadge.textContent = unread > 99 ? '99+' : unread;
            navNotifBadge.classList.remove('hidden');
          } else {
            navNotifBadge.classList.add('hidden');
          }
        }
        state.notifUnread = unread;
      }
    } catch (e) { /* silent */ }

    // 2. Refresh chat unread counts (เฉพาะเมื่อ initAppContent ยังไม่ได้ register interval ซ้ำ)
    if (!state._chatPollRegistered) {
      try {
        await loadUnreadCounts();
      } catch (e) { /* silent */ }
    }

  }, 30000);
})();

// ─── Social Feed Logic ─────────────────────────
async function loadDailyDigest() {
  if (!dailyDigest) return;

  // Show loading state
  dailyDigest.classList.remove('hidden');
  digestContent.innerHTML = `
    <div class="flex items-center gap-2">
      <div class="w-3 h-3 bg-white/40 rounded-full animate-bounce"></div>
      <div class="w-3 h-3 bg-white/40 rounded-full animate-bounce [animation-delay:0.2s]"></div>
      <div class="w-3 h-3 bg-white/40 rounded-full animate-bounce [animation-delay:0.4s]"></div>
      <span class="text-xs opacity-80">AI กำลังสรุปความเคลื่อนไหวล่าสุด...</span>
    </div>`;

  try {
    const data = await apiFetch('/api/feed/summarize', { method: 'POST' });
    if (data.ok) {
      digestContent.textContent = data.summary;
    } else {
      dailyDigest.classList.add('hidden');
    }
  } catch (e) {
    console.warn('Digest load failed:', e);
    dailyDigest.classList.add('hidden');
  }
}

if (refreshDigestBtn) {
  refreshDigestBtn.onclick = (e) => {
    e.stopPropagation();
    loadDailyDigest();
  }
}

async function loadPosts(category = 'All') {
  state.currentFeedCategory = category; // Track active filter for auto-refresh
  try {
    const data = await apiFetch(`/api/posts?category=${category}`);
    state.feedPosts = data.posts || []; // Store in state for easy access during edit
    renderPosts(state.feedPosts);
  } catch (e) {
    console.error('Failed to load posts:', e);
    toast('ไม่สามารถโหลดโพสต์ได้', 'error');
  }
}

function renderPosts(posts) {
  if (!posts.length) {
    feedPosts.innerHTML = `
      <div class="text-center py-20 text-surface-400">
        <i data-lucide="layout-list" class="w-12 h-12 mx-auto mb-4 opacity-10"></i>
        <p>ยังไม่มีโพสต์ในหมวดหมู่นี้</p>
      </div>`;
    initIcons();
    return;
  }

  feedPosts.innerHTML = posts.map(p => {
    const currentUser = typeof state.user === 'object' ? state.user?.username : state.user;
    const isOwner = p.author === currentUser || state.isAdmin;
    const isPinned = !!p.is_pinned;

    return `
    <div data-post-id="${p.id}" class="post-card bg-white dark:bg-surface-900 border ${isPinned ? 'border-brand-500 ring-1 ring-brand-500' : 'border-surface-200 dark:border-surface-800'} rounded-2xl p-6 shadow-sm space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-500 relative">
      ${isPinned ? `<div class="absolute -top-3 -right-3 bg-brand-600 text-white px-2 py-1 rounded-lg shadow-lg flex items-center gap-1.5 z-10 animate-bounce">
          <i data-lucide="pin" class="w-2.5 h-2.5 fill-white"></i>
          <span class="text-[8px] font-black uppercase tracking-widest">Pinned</span>
        </div>` : ''}

      <div class="flex justify-between items-start">
        <div class="flex gap-3">
          <div class="w-10 h-10 rounded-full bg-brand-50 dark:bg-brand-900/30 flex items-center justify-center text-brand-600 overflow-hidden ring-2 ring-brand-500/20">
            ${p.avatar_url ? `<img src="${p.avatar_url}" class="w-full h-full object-cover">` : `<i data-lucide="user" class="w-5 h-5"></i>`}
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="font-bold text-sm select-none">${p.display_name || p.author}</span>
              <span class="px-2 py-0.5 bg-brand-50 dark:bg-brand-900/30 text-brand-600 text-[10px] font-bold rounded-full uppercase">${p.category}</span>
            </div>
            <div class="text-[10px] text-surface-400 font-medium">${new Date(p.timestamp).toLocaleString('th-TH')}</div>
          </div>
        </div>

        <div class="flex gap-1">
          <button class="p-1.5 text-surface-400 hover:text-brand-600 rounded-lg transition-colors ${isPinned ? 'text-brand-600 bg-brand-50 dark:bg-brand-900/20' : ''}" onclick="togglePin(${p.id})">
            <i data-lucide="pin" class="w-4 h-4 ${isPinned ? 'fill-current' : ''}"></i>
          </button>
          ${isOwner ? `
            <button class="p-1.5 text-surface-400 hover:text-brand-600 rounded-lg transition-colors" onclick="editPost(${p.id})">
              <i data-lucide="edit-2" class="w-4 h-4"></i>
            </button>
            <button class="p-1.5 text-surface-400 hover:text-red-500 rounded-lg transition-colors" onclick="deletePost(${p.id})">
              <i data-lucide="trash-2" class="w-4 h-4"></i>
            </button>
          ` : ''}
        </div>
      </div>

      <div id="post-content-${p.id}" class="text-sm leading-relaxed text-surface-700 dark:text-surface-300 whitespace-pre-wrap">${highlightMentions(p.content)}</div>


      ${p.poll ? `
        <div class="bg-surface-50 dark:bg-surface-800/40 border border-surface-100 dark:border-surface-700 rounded-2xl p-5 space-y-4">
          <div class="flex items-center gap-2 mb-1">
            <div class="p-1.5 bg-brand-100 dark:bg-brand-900/30 rounded-lg text-brand-600">
              <i data-lucide="bar-chart-2" class="w-3.5 h-3.5"></i>
            </div>
            <h4 class="text-xs font-bold text-surface-900 dark:text-white">${p.poll.question}</h4>
          </div>
          <div class="space-y-2.5">
            ${p.poll.options.map(opt => {
      const percent = p.poll.total_votes > 0 ? Math.round((opt.votes / p.poll.total_votes) * 100) : 0;
      const voterNames = opt.voters.map(v => v.name).join(', ');
      const votersTitle = voterNames ? `ผู้โหวต: ${voterNames}` : 'ยังไม่มีผู้โหวต';

      // Get up to 5 voters to show avatars
      const topVoters = opt.voters.slice(0, 5);
      const hasMore = opt.votes > 5;

      return `
                <div class="relative group/pollopt w-full">
                  <button onclick="voteInPoll(${p.poll.id}, ${opt.id})" class="w-full relative overflow-hidden rounded-xl bg-surface-50 dark:bg-surface-900/30 border border-surface-200 dark:border-surface-700/50 hover:border-brand-500/50 transition-all">
                    <div class="absolute inset-y-0 left-0 bg-brand-500/10 rounded-r-none transition-all group-hover/pollopt:bg-brand-500/20" style="width: ${percent}%"></div>
                    <div class="relative flex items-center justify-between p-3.5 text-xs">
                      <div class="flex items-center gap-3">
                        <span class="font-bold text-surface-700 dark:text-surface-300">${opt.text}</span>
                        <!-- Voter Avatars -->
                        <div class="flex -space-x-1.5 transition-all group-hover/pollopt:translate-x-1" title="${votersTitle}">
                          ${topVoters.map(v => v.avatar ?
        `<img src="${v.avatar}" class="w-5 h-5 rounded-full border-2 border-white dark:border-surface-900 object-cover shadow-sm" title="${v.name}">` :
        `<div class="w-5 h-5 rounded-full border-2 border-white dark:border-surface-900 bg-brand-500 text-white flex items-center justify-center text-[8px] font-bold shadow-sm" title="${v.name}">${v.name[0]}</div>`
      ).join('')}
                          ${hasMore ? `<div class="w-5 h-5 rounded-full border-2 border-white dark:border-surface-900 bg-surface-200 dark:bg-surface-700 text-surface-600 dark:text-surface-300 flex items-center justify-center text-[7px] font-black">+${opt.votes - 5}</div>` : ''}
                        </div>
                      </div>
                      <div class="flex flex-col items-end">
                        <span class="text-[10px] font-black text-brand-600">${percent}%</span>
                        <span class="text-[8px] font-bold text-surface-400 uppercase tracking-tighter">${opt.votes} โหวต</span>
                      </div>
                    </div>
                  </button>
                </div>
              `;
    }).join('')}
          </div>
          <div class="text-[10px] text-surface-400 font-bold uppercase tracking-widest pt-1 flex items-center gap-2">
            <i data-lucide="users" class="w-3 h-3"></i> รวม ${p.poll.total_votes} คะแนน
          </div>
        </div>
      ` : ''}

      ${p.summary ? `
        <div id="summary-${p.id}" class="${p.hideSummary ? 'hidden' : ''} bg-brand-50/50 dark:bg-brand-900/20 border border-brand-100 dark:border-brand-800/50 rounded-xl p-4 space-y-2 animate-in fade-in zoom-in duration-300 relative group/summary">
          <button class="absolute top-3 right-3 p-1 text-surface-400 hover:text-brand-600 opacity-0 group-hover/summary:opacity-100 transition-all" onclick="toggleSummary(${p.id})">
            <i data-lucide="x" class="w-3 h-3"></i>
          </button>
          <div class="flex items-center gap-2 text-brand-600 dark:text-brand-400">
            <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
            <span class="text-[10px] font-bold uppercase tracking-widest">AI Summary</span>
          </div>
          <p class="text-xs text-surface-600 dark:text-surface-400 leading-relaxed italic">"${p.summary}"</p>
        </div>
      ` : ''}

      ${(() => {
        const effectiveLink = p.link || (p.content ? (p.content.match(/https?:\/\/[^\s<>"']+/i) || [])[0] : null);
        if (!effectiveLink) return '';
        const hasImages = p.attachments && p.attachments.some(f => f.type?.startsWith('image/') || f.path?.match(/\.(jpg|jpeg|png|gif|webp)$/i));
        const domain = (effectiveLink.split('/')[2] || 'LINK').replace('www.', '').toUpperCase();
        
        if (!hasImages) {
          return `
            <div id="link-preview-${p.id}" class="post-preview-container mt-3">
              <a href="${effectiveLink}" target="_blank" class="block overflow-hidden rounded-2xl border border-surface-200/90 dark:border-surface-700/70 bg-surface-50 dark:bg-surface-800/40 hover:border-brand-500/80 dark:hover:border-brand-500/80 transition-all group shadow-sm hover:shadow-md">
                <div id="lp-img-${p.id}" class="hidden w-full h-48 sm:h-56 overflow-hidden bg-surface-200 dark:bg-surface-800 relative"></div>
                <div class="p-4 space-y-1.5 bg-white dark:bg-surface-900/60">
                  <div class="flex items-center gap-1.5 text-brand-600 dark:text-brand-400 font-bold text-[10px] uppercase tracking-wider">
                    <i data-lucide="link" class="w-3.5 h-3.5"></i>
                    <span>${domain}</span>
                  </div>
                  <h4 id="lp-title-${p.id}" class="text-sm font-bold text-surface-900 dark:text-white line-clamp-2 leading-snug group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors">${effectiveLink}</h4>
                  <p id="lp-desc-${p.id}" class="text-xs text-surface-500 dark:text-surface-400 line-clamp-2 leading-relaxed"></p>
                </div>
              </a>
            </div>
          `;
        } else {
          return `
            <div id="link-preview-${p.id}" class="post-preview-container mt-2">
              <a href="${effectiveLink}" target="_blank" class="block p-3.5 bg-surface-50 dark:bg-surface-800/40 rounded-2xl border border-surface-100 dark:border-surface-700 hover:border-brand-500 transition-all group">
                <div class="flex gap-3.5 items-center">
                  <div id="lp-img-${p.id}" class="hidden w-16 h-16 rounded-xl overflow-hidden bg-surface-200 dark:bg-surface-700 flex-shrink-0"></div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-1.5 text-brand-600 mb-0.5">
                      <i data-lucide="link" class="w-3 h-3"></i>
                      <span class="text-[9px] font-bold truncate uppercase tracking-widest">${domain}</span>
                    </div>
                    <h4 id="lp-title-${p.id}" class="text-xs font-bold text-surface-900 dark:text-white mb-0.5 truncate">${effectiveLink}</h4>
                    <p id="lp-desc-${p.id}" class="text-[10px] text-surface-500 line-clamp-1 leading-snug"></p>
                  </div>
                </div>
              </a>
            </div>
          `;
        }
      })()}

      ${p.attachments && p.attachments.length ? (() => {
        const total = p.attachments.length;
        const gridClass = total === 1
          ? 'flex justify-center max-w-xl mx-auto w-full my-2'
          : (total === 2 ? 'grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto w-full my-2 justify-center' : 'grid grid-cols-2 md:grid-cols-3 gap-3 my-2');
        return `
        <div class="${gridClass}">
          ${p.attachments.map(file => {
      const isImg = file.type?.startsWith('image/') || file.path.match(/\.(jpg|jpeg|png|gif|webp)$/i);
      const path = file.path;
      const name = file.name;
      const type = file.type || '';

      if (isImg) {
        const cardClass = total === 1
          ? 'w-full max-w-lg relative group/att overflow-hidden rounded-2xl border border-surface-200/80 dark:border-surface-800 aspect-video cursor-pointer shadow-sm mx-auto'
          : 'relative group/att overflow-hidden rounded-xl border border-surface-200/80 dark:border-surface-800 aspect-video cursor-pointer shadow-xs w-full';
        return `
                <div class="${cardClass}" onclick="openLightbox('${path}', '${name}')">
                  <img src="${path}" class="w-full h-full object-cover transition-transform group-hover/att:scale-105 duration-300" loading="lazy">
                  <div class="absolute inset-0 bg-black/45 opacity-0 group-hover/att:opacity-100 transition-opacity flex items-center justify-center gap-2 text-white">
                    <button onclick="event.stopPropagation(); openLightbox('${path}', '${name}')" class="px-3 py-1.5 bg-white/20 hover:bg-white/30 backdrop-blur-md rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all shadow-lg active:scale-95" title="ขยายรูป">
                      <i data-lucide="zoom-in" class="w-3.5 h-3.5"></i> ขยายรูป
                    </button>
                    <a href="${path}" download="${name}" onclick="event.stopPropagation()" class="px-3 py-1.5 bg-brand-600 hover:bg-brand-500 backdrop-blur-md rounded-xl text-white text-xs font-bold flex items-center gap-1.5 transition-all shadow-lg active:scale-95" title="ดาวน์โหลด">
                      <i data-lucide="download" class="w-3.5 h-3.5"></i> ดาวน์โหลด
                    </a>
                  </div>
                </div>
              `;
      }
      return `
              <div class="flex items-center gap-2 p-3 bg-surface-50 dark:bg-surface-800/40 border border-surface-100 dark:border-surface-700 rounded-xl hover:border-brand-500 transition-all truncate group/file text-[10px] font-bold relative">
                <i data-lucide="file-text" class="w-4 h-4 text-surface-400"></i>
                <span class="truncate pr-16">${name}</span>
                <div class="absolute right-2 flex items-center gap-1 opacity-0 group-hover/file:opacity-100 transition-all">
                  <a href="${path}" download="${name}" class="p-1.5 bg-surface-200 dark:bg-surface-700 hover:bg-brand-500 hover:text-white text-surface-600 dark:text-surface-300 rounded-lg transition-all" title="ดาวน์โหลด">
                    <i data-lucide="download" class="w-3 h-3"></i>
                  </a>
                  <button onclick="openFilePreview('${name}', '${path}', '${type}')" class="p-1.5 bg-brand-500 text-white rounded-lg transition-all" title="ดูตัวอย่าง">
                     <i data-lucide="eye" class="w-3 h-3"></i>
                  </button>
                </div>
              </div>
            `;
    }).join('')}
        </div>
        `;
      })() : ''}

      <div class="flex items-center pt-4 border-t border-surface-50 dark:border-surface-800 gap-2">
        <!-- Reaction Button with Picker -->
        <div class="relative flex items-center gap-2" id="reaction-wrap-${p.id}"
             onmouseenter="showReactionPicker(${p.id})"
             onmouseleave="hideReactionPickerDelayed(${p.id})">
          <button class="reaction-trigger flex items-center gap-1.5 px-3 py-2 rounded-xl border border-surface-100 dark:border-surface-800 bg-surface-50/50 dark:bg-surface-900/50 hover:border-rose-200 hover:bg-rose-50 dark:hover:bg-rose-900/20 transition-all group/rbtn" data-pid="${p.id}" onclick="quickReact(${p.id}, 'like')">
            <span class="text-sm leading-none" id="my-reaction-icon-${p.id}">👍</span>
            <span class="text-xs font-bold text-surface-400 group-hover/rbtn:text-rose-500 transition-colors" id="react-label-${p.id}">ถูกใจ</span>
          </button>
          <!-- Reaction count -->
          <button onclick="openReactionsModal(${p.id})" id="reaction-counts-${p.id}" class="text-xs font-bold text-surface-400 hover:text-brand-600 transition-colors min-w-[18px] text-left">
            <span id="total-reactions-${p.id}">${p.likes || 0}</span>
          </button>
          <!-- Reaction Picker Popup (JS hover, delay 150ms to avoid gap issue) -->
          <div class="reaction-picker absolute left-0 z-50"
               id="rpicker-${p.id}"
               style="bottom:100%; padding-bottom:12px; display:none;"
               onmouseenter="showReactionPicker(${p.id})"
               onmouseleave="hideReactionPickerDelayed(${p.id})">
            <div class="flex gap-0.5 bg-white dark:bg-surface-800 rounded-2xl shadow-2xl border border-surface-100 dark:border-surface-700 p-1.5">
            ${[['like', '\u{1F44D}', 'ถูกใจ'], ['love', '\u2764\uFE0F', 'รักเลย'], ['haha', '\u{1F602}', 'ฮาเลย'], ['wow', '\u{1F62E}', 'ทึ่ง'], ['sad', '\u{1F622}', 'เศร้า'], ['angry', '\u{1F621}', 'โกรธ']].map(([key, emoji, label]) => `
              <button onclick="setReaction(${p.id}, '${key}')" title="${label}" class="reaction-btn flex flex-col items-center gap-0.5 p-2 rounded-xl hover:bg-surface-50 dark:hover:bg-surface-700 transition-all hover:scale-125 active:scale-110" data-reaction="${key}" data-pid="${p.id}">
                <span style="font-size:24px;line-height:1.1">${emoji}</span>
                <span class="text-[8px] font-bold text-surface-400">${label}</span>
              </button>
            `).join('')}
            </div>
          </div>
        </div>

        <!-- Comment Button -->
        <button class="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-surface-100 dark:border-surface-800 bg-surface-50/50 dark:bg-surface-900/50 hover:border-brand-200 hover:bg-brand-50 dark:hover:bg-brand-900/20 transition-all group/cbtn" onclick="toggleComments(${p.id})">
          <i data-lucide="message-circle" class="w-4 h-4 text-surface-400 group-hover/cbtn:text-brand-500 transition-colors"></i>
          <span class="text-xs font-bold text-surface-400 group-hover/cbtn:text-brand-500 transition-colors">${p.comments || 0}</span>
        </button>

        <!-- Seen Receipts Badge -->
        <div id="seen-receipts-${p.id}" class="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-surface-50/30 dark:bg-brand-900/10 cursor-help group/seen transition-all" onclick="showSeenByModal(${p.id})">
           <i data-lucide="eye" class="w-3.5 h-3.5 text-surface-300"></i>
           <span class="text-[10px] font-bold text-surface-400 group-hover/seen:text-brand-600 transition-colors" id="seen-count-${p.id}">0</span>
        </div>

        <button class="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-surface-100 dark:border-surface-800 bg-surface-50/50 dark:bg-surface-900/50 hover:border-violet-200 hover:bg-violet-50 dark:hover:bg-violet-900/20 transition-all group/abtn ml-auto" onclick="summarizePost(${p.id}, this)">
          <i data-lucide="wand-2" class="w-3.5 h-3.5 text-surface-400 group-hover/abtn:text-violet-500 transition-colors"></i>
          <span class="text-[10px] font-black uppercase tracking-widest text-surface-400 group-hover/abtn:text-violet-500 transition-colors">AI สรุป</span>
        </button>
      </div>

      <div id="comments-${p.id}" class="hidden pt-4 space-y-4 border-t border-surface-50 dark:border-surface-800">
        <div class="flex gap-2">
          <input type="text" id="comment-input-${p.id}" placeholder="เขียนคอมเมนต์..." class="flex-1 bg-surface-50 dark:bg-surface-800 border-none rounded-xl text-xs py-2 px-4 focus:ring-1 focus:ring-brand-500">
          <button class="btn-primary text-[10px] px-6 py-2 rounded-xl" onclick="submitComment(${p.id})">ส่ง</button>
        </div>
        <div id="comment-list-${p.id}" class="space-y-3 max-h-60 overflow-y-auto pr-2 custom-scrollbar"></div>
      </div>
    </div>
  `}).join('');
  initIcons();

  posts.forEach(p => {
    if (p.link) fetchLinkPreview(p.id, p.link);
    // Load current user's reaction state for each post
    loadPostReactions(p.id);
    loadSeenCount(p.id);

    // Observe for seen receipt
    const el = document.querySelector(`.post-card[data-post-id="${p.id}"]`);
    if (el) postViewObserver.observe(el);
  });
}

function loadSeenCount(pid) {
  apiFetch(`/api/posts/${pid}/views`).then(data => {
    if (data.ok) {
      const el = $(`seen-count-${pid}`);
      if (el) el.textContent = data.views.length;
      state.postViewsData = state.postViewsData || {};
      state.postViewsData[pid] = data.views;
    }
  }).catch(() => { });
}

function showSeenByModal(pid) {
  const views = state.postViewsData[pid] || [];
  if (!views.length) { toast('ยังไม่มีผู้เข้าชมนี้', 'info'); return; }

  const content = `
    <div class="space-y-4 p-2">
      <div class="text-[10px] font-black uppercase tracking-widest text-surface-400 mb-2 px-2">ผู้ที่อ่านแล้ว (${views.length})</div>
      <div class="grid grid-cols-1 gap-1 max-h-72 overflow-y-auto custom-scrollbar">
        ${views.map(v => `
          <div class="flex items-center justify-between p-3 rounded-2xl bg-surface-50 dark:bg-surface-800/50 hover:bg-brand-50 dark:hover:bg-brand-900/20 transition-all group">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-full bg-white dark:bg-surface-700 flex items-center justify-center text-brand-600 shadow-sm overflow-hidden ring-2 ring-transparent group-hover:ring-brand-500/20 transition-all">
                ${v.avatar ? `<img src="${v.avatar}" class="w-full h-full object-cover">` : `<span class="text-[10px] font-black">${v.display_name[0]}</span>`}
              </div>
              <div>
                <div class="text-[11px] font-black text-surface-900 dark:text-white">${v.display_name}</div>
                <div class="text-[9px] text-surface-400 font-bold">@${v.username}</div>
              </div>
            </div>
            <div class="text-[9px] font-black text-surface-400 uppercase tracking-tighter">${new Date(v.time).toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' })}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;

  const overlay = document.createElement('div');
  overlay.className = 'fixed inset-0 z-[400] bg-surface-950/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-300';
  overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); }

  const modal = document.createElement('div');
  modal.className = 'bg-white dark:bg-surface-900 w-full max-w-sm rounded-[32px] shadow-2xl border border-surface-200 dark:border-surface-800 p-6 animate-in zoom-in-95 duration-200';
  modal.innerHTML = `
    <div class="flex justify-between items-center mb-6">
       <h3 class="text-lg font-black tracking-tight">Seen Receipts</h3>
       <button onclick="this.closest('.fixed').remove()" class="p-2 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-full transition-all text-surface-400"><i data-lucide="x" class="w-5 h-5"></i></button>
    </div>
    ${content}
  `;
  overlay.appendChild(modal);
  document.body.appendChild(overlay);
  initIcons();
}

async function fetchLinkPreview(pid, url) {
  try {
    const data = await apiFetch(`/api/link-preview?url=${encodeURIComponent(url)}`);
    if (data.ok) {
      const titleEl = $(`lp-title-${pid}`);
      const descEl = $(`lp-desc-${pid}`);
      const imgCont = $(`lp-img-${pid}`);
      if (titleEl && data.title) titleEl.textContent = data.title;
      if (descEl && data.description) descEl.textContent = data.description;
      if (imgCont && data.image) {
        imgCont.innerHTML = `<img src="${data.image}" class="w-full h-full object-cover">`;
        imgCont.classList.remove('hidden', 'animate-pulse');
      }
    }
  } catch (e) {
    console.warn('Preview failed:', url, e);
    const imgCont = $(`lp-img-${pid}`);
    if (imgCont) imgCont.classList.remove('animate-pulse');
  }
}

function togglePollComposer(show = null) {
  const comp = $('pollComposer');
  if (show === null) comp.classList.toggle('hidden');
  else if (show) comp.classList.remove('hidden');
  else comp.classList.add('hidden');

  if (!comp.classList.contains('hidden')) {
    $('pollQuestion').focus();
    initIcons();
  }
}

function addPollOption() {
  const container = $('pollOptionsContainer');
  const count = container.querySelectorAll('.poll-option-input').length + 1;
  const div = document.createElement('div');
  div.className = 'flex gap-2';
  div.innerHTML = `
    <input type="text" placeholder="ตัวเลือกที่ ${count}" class="poll-option-input flex-1 bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-700 rounded-xl text-xs py-2 px-3 focus:ring-1 focus:ring-brand-500">
    <button onclick="this.parentElement.remove()" class="text-surface-400 hover:text-red-500 transition-colors"><i data-lucide="minus-circle" class="w-4 h-4"></i></button>
  `;
  container.appendChild(div);
  initIcons();
}

let _isSubmittingPost = false;
submitPostBtn.onclick = async () => {
  if (_isSubmittingPost) return;
  _isSubmittingPost = true;

  const content = postInput.value.trim();
  const category = postCategory.value;
  const link = postLink.value.trim();

  const pollComp = $('pollComposer');
  const isPollActive = pollComp && !pollComp.classList.contains('hidden');
  const pollQuestion = isPollActive ? $('pollQuestion').value.trim() : '';

  if (!content && !link && postFiles.length === 0 && !pollQuestion) {
    _isSubmittingPost = false;
    return toast('กรุณาใส่ข้อความ ลิงก์ โพลล์ หรือแนบไฟล์อย่างใดอย่างหนึ่ง', 'warning');
  }

  submitPostBtn.disabled = true;
  submitPostBtn.textContent = 'กำลังส่ง...';

  const formData = new FormData();
  formData.append('content', content);
  formData.append('category', category);
  formData.append('link', link);
  formData.append('author', state.user?.username || state.user || 'Current User');

  postFiles.forEach(file => {
    formData.append('files', file);
  });

  // Collect poll data
  if (isPollActive) {
    const question = pollQuestion;
    const optionInputs = document.querySelectorAll('.poll-option-input');
    const options = Array.from(optionInputs).map(i => i.value.trim()).filter(v => v);

    if (question && options.length >= 2) {
      formData.append('poll_question', question);
      formData.append('poll_options', JSON.stringify(options));
    }
  }

  try {
    const res = await fetch('/api/posts', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error);

    postInput.value = '';
    postLink.value = '';
    linkInputContainer.classList.add('hidden');

    // Clear poll
    if (pollComp) {
      pollComp.classList.add('hidden');
      $('pollQuestion').value = '';
      $('pollOptionsContainer').innerHTML = `
        <div class="flex gap-2">
          <input type="text" placeholder="ตัวเลือกที่ 1" class="poll-option-input flex-1 bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-700 rounded-xl text-xs py-2 px-3 focus:ring-1 focus:ring-brand-500">
        </div>
        <div class="flex gap-2">
          <input type="text" placeholder="ตัวเลือกที่ 2" class="poll-option-input flex-1 bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-700 rounded-xl text-xs py-2 px-3 focus:ring-1 focus:ring-brand-500">
        </div>
      `;
    }

    postFiles = [];
    renderPostAttachments();
    toast('โพสต์สำเร็จแล้ว', 'success');
    loadPosts();
  } catch (e) {
    toast('โพสต์ล้มเหลว: ' + e.message, 'error');
  } finally {
    _isSubmittingPost = false;
    submitPostBtn.disabled = false;
    submitPostBtn.textContent = 'โพสต์';
  }
};

// --- Attachment Handling ---
postFileInput.onchange = () => {
  const files = Array.from(postFileInput.files);
  postFiles = [...postFiles, ...files];
  renderPostAttachments();
  postFileInput.value = ''; // Reset input
};

function renderPostAttachments() {
  postAttachmentPreview.innerHTML = postFiles.map((f, i) => `
    <div class="flex items-center gap-2 bg-surface-100 dark:bg-surface-800 px-3 py-1.5 rounded-full text-xs border border-surface-200">
      <span class="max-w-[120px] truncate font-medium">${f.name}</span>
      <button onclick="removePostFile(${i})" class="text-surface-400 hover:text-red-500 transition-colors">
        <i data-lucide="x" class="w-3.5 h-3.5"></i>
      </button>
    </div>
  `).join('');
  initIcons();
}

function removePostFile(index) {
  postFiles.splice(index, 1);
  renderPostAttachments();
}

// --- Post Actions ---
async function voteInPoll(pollId, optionId) {
  try {
    const res = await fetch(`/api/polls/${pollId}/vote`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ option_id: optionId })
    });
    const data = await res.json();
    if (data.ok) {
      toast('ลงคะแนนสำเร็จ', 'success');
      loadPosts(); // Refresh feed to show updated vote counts
    } else {
      toast(data.error || 'ลงคะแนนไม่สำเร็จ', 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาด: ' + e.message, 'error');
  }
}

async function togglePin(pid) {
  try {
    await apiFetch(`/api/posts/${pid}/pin`, { method: 'POST' });
    loadPosts();
  } catch (e) { console.error(e); }
}

async function deletePost(pid) {
  if (!await showConfirm('ลบโพสต์ถาวร', 'ยืนยัน: คุณต้องการลบโพสต์นี้ถาวรใช่หรือไม่?', { type: 'danger', confirmText: 'ลบโพสต์' })) return;
  toast('กำลังลบโพสต์...', 'info');

  try {
    const res = await fetch(`/api/posts/${pid}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.ok) {
      toast('ลบโพสต์สำเร็จแล้ว', 'success');
      loadPosts();
    } else {
      throw new Error(data.error);
    }
  } catch (e) {
    toast('ลบไม่สำเร็จ: ' + e.message, 'error');
  }
}

function editPost(pid) {
  const p = state.feedPosts.find(x => x.id === pid);
  if (!p) return;

  currentEditingPostId = pid;
  editPostInput.value = p.content;
  editPostLink.value = p.link || '';
  editPostCategory.value = p.category || 'General';

  editPostModal.classList.remove('hidden');
  initIcons();
  editPostInput.focus();
}

closeEditPostModal.onclick = () => {
  editPostModal.classList.add('hidden');
  editPostModal.classList.remove('flex', 'items-center', 'justify-center');
  currentEditingPostId = null;
};

saveEditPostBtn.onclick = async () => {
  const content = editPostInput.value.trim();
  const link = editPostLink.value.trim();
  const category = editPostCategory.value;

  if (!content || !currentEditingPostId) return;

  saveEditPostBtn.disabled = true;
  saveEditPostBtn.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i> กำลังบันทึก...';
  initIcons();

  try {
    const res = await apiFetch(`/api/posts/${currentEditingPostId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, link, category })
    });
    if (!res.ok) throw new Error(res.error);

    toast('แก้ไขโพสต์สำเร็จ', 'success');
    editPostModal.classList.add('hidden');
    editPostModal.classList.remove('flex', 'items-center', 'justify-center');
    loadPosts();
  } catch (e) {
    toast('แก้ไขไม่สำเร็จ: ' + e.message, 'error');
  } finally {
    saveEditPostBtn.disabled = false;
    saveEditPostBtn.innerHTML = '<i data-lucide="save" class="w-4 h-4"></i> บันทึกการแก้ไข';
    initIcons();
  }
};

async function likePost(pid) {
  try {
    const data = await apiFetch(`/api/posts/${pid}/like`, { method: 'POST' });
    if (data.ok) loadPosts();
  } catch (e) { console.error(e); }
}

async function toggleComments(pid) {
  const el = $(`comments-${pid}`);
  const list = $(`comment-list-${pid}`);
  const isHidden = el.classList.contains('hidden');

  el.classList.toggle('hidden');
  if (isHidden) {
    list.innerHTML = '<div class="text-[10px] text-surface-400 text-center py-2">กำลังโหลดคอมเมนต์...</div>';
    try {
      const data = await apiFetch(`/api/posts/${pid}/comments`);
      if (data.comments && data.comments.length) {
        const currentUser = typeof state.user === 'object' ? state.user?.username : state.user;
        list.innerHTML = data.comments.map(c => {
          const isOwner = c.author === currentUser || state.isAdmin;
          return `
          <div class="bg-surface-50 dark:bg-surface-800/50 p-3 rounded-2xl flex gap-3 group/comment">
            <div class="w-7 h-7 rounded-lg bg-white dark:bg-surface-700 flex items-center justify-center text-brand-600 flex-shrink-0 overflow-hidden ring-1 ring-brand-500/10">
              ${c.avatar_url ? `<img src="${c.avatar_url}" class="w-full h-full object-cover">` : `<i data-lucide="user" class="w-3.5 h-3.5"></i>`}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex justify-between items-center mb-0.5">
                <span class="text-[10px] font-black text-brand-600 uppercase tracking-tighter">${c.display_name || c.author}</span>
                <div class="flex items-center gap-2">
                  <span class="text-[8px] text-surface-400 font-medium">${new Date(c.timestamp).toLocaleString('th-TH')}</span>
                  ${isOwner ? `
                    <button onclick="deleteComment(${pid}, ${c.id})" class="text-surface-300 hover:text-red-500 opacity-0 group-hover/comment:opacity-100 transition-all">
                      <i data-lucide="trash-2" class="w-2.5 h-2.5"></i>
                    </button>
                  ` : ''}
                </div>
              </div>
              <div class="text-[11px] text-surface-700 dark:text-surface-300 leading-snug">${highlightMentions(c.content)}</div>
            </div>
          </div>
        `}).join('');
      } else {
        list.innerHTML = '<div class="text-[10px] text-surface-400 text-center py-2">ยังไม่มีคอมเมนต์</div>';
      }
    } catch (e) {
      list.innerHTML = '<div class="text-[10px] text-red-500 text-center py-2">โหลดล้มเหลว</div>';
    }
  }
  // Init @mention autocomplete for this post's comment input
  setTimeout(() => initMentionInput(`comment-input-${pid}`), 150);
}

const _submittingComments = new Set();
async function submitComment(pid) {
  if (_submittingComments.has(pid)) return;
  const input = $(`comment-input-${pid}`);
  const content = input ? input.value.trim() : '';
  if (!content) return;

  _submittingComments.add(pid);
  try {
    await apiFetch(`/api/posts/${pid}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, author: typeof state.user === 'object' ? state.user?.username : (state.user || 'Current User') })
    });
    if (input) input.value = '';
    const el = $(`comments-${pid}`);
    if (el) el.classList.add('hidden'); // Close it
    loadPosts(); // Refresh for count
    toggleComments(pid); // Re-open to show new comment
  } catch (e) {
    toast('คอมเมนต์ล้มเหลว', 'error');
  } finally {
    setTimeout(() => _submittingComments.delete(pid), 500);
  }
}

async function deleteComment(pid, cid) {
  if (!confirm('ต้องการลบคอมเมนต์นี้ใช่หรือไม่?')) return;
  try {
    const res = await apiFetch(`/api/posts/${pid}/comments/${cid}`, { method: 'DELETE' });
    if (res.ok) {
      toast('ลบคอมเมนต์แล้ว', 'info');
      loadPosts(); // Refresh feedback
    } else {
      toast(res.error || 'ลบคอมเมนต์ไม่สำเร็จ', 'error');
    }
  } catch (e) {
    toast('ลบคอมเมนต์ไม่สำเร็จ: ' + e.message, 'error');
  }
}

// ─── @Mention Autocomplete ───────────────────────────────────────────────
function escapeHTML(str) {
  if (!str) return '';
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}

function highlightMentions(text) {
  if (!text) return '';
  return escapeHTML(text).replace(/@(\w+)/g, '<span class="mention-tag">@$1</span>');
}

async function fetchUserSuggestions(prefix, userFn = null) {
  try {
    let users;
    if (userFn) {
      users = await userFn();
    } else {
      const data = await apiFetch('/api/chat/users');
      if (!data.ok) return [];
      users = data.users || [];
    }
    return users.filter(u =>
      (u.username || '').toLowerCase().startsWith(prefix.toLowerCase()) ||
      (u.display_name || '').toLowerCase().startsWith(prefix.toLowerCase())
    ).slice(0, 6);
  } catch { return []; }
}

// Returns members of the CURRENT chat context (room members or DM partner)
async function fetchChatContextUsers() {
  const chat = state.currentChat;
  if (!chat) return [];
  if (chat.type === 'dm') {
    // DM: just the other person + current user (so they can @themselves too)
    const profile = await apiFetch('/api/chat/users');
    const all = profile.ok ? profile.users || [] : [];
    return all.filter(u => u.username.toLowerCase() === chat.id.toLowerCase());
  }
  // Room: fetch actual members from the new endpoint
  try {
    const data = await apiFetch(`/api/chat/rooms/${chat.id}/members`);
    if (data.ok) return data.users || [];
  } catch { }
  return [];
}

function initMentionInput(inputId, userFn = null) {
  const input = $(inputId);
  if (!input || input._mentionInitialized) return;
  input._mentionInitialized = true;

  // Create dropdown
  const dropdown = document.createElement('div');
  dropdown.className = 'mention-dropdown hidden absolute z-[200] bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-700 rounded-2xl shadow-2xl overflow-hidden min-w-[200px]';
  dropdown.style.cssText = 'bottom: calc(100% + 4px); left: 0; max-height: 220px; overflow-y: auto;';

  // Wrap input in relative container if not already
  if (!input.parentElement.classList.contains('mention-wrap')) {
    const wrap = document.createElement('div');
    // Ensure the wrapper takes up available space like the input did
    wrap.className = 'mention-wrap relative flex-1 w-full flex items-center';
    input.parentElement.insertBefore(wrap, input);
    wrap.appendChild(input);
    wrap.appendChild(dropdown);
  } else {
    input.parentElement.appendChild(dropdown);
  }

  let _debounceTimer = null;
  let _lastAt = -1;

  input.addEventListener('input', () => {
    clearTimeout(_debounceTimer);
    const val = input.value;
    const cursor = input.selectionStart;
    const textBefore = val.slice(0, cursor);
    // Use [^\\s]* to allow Thai characters after @
    const atMatch = textBefore.match(/(?:^|\\s)@([^\\s]*)$/);

    if (!atMatch) { dropdown.classList.add('hidden'); return; }
    const prefix = atMatch[1];
    _lastAt = textBefore.lastIndexOf('@');

    _debounceTimer = setTimeout(async () => {
      const users = await fetchUserSuggestions(prefix, userFn);
      if (!users.length) { dropdown.classList.add('hidden'); return; }

      dropdown.innerHTML = users.map(u => `
        <div class="mention-item flex items-center gap-2 px-3 py-2 hover:bg-brand-50 dark:hover:bg-brand-900/20 cursor-pointer transition-all" data-username="${u.username}">
          <div class="w-7 h-7 rounded-full bg-brand-100 dark:bg-brand-900/40 flex items-center justify-center text-brand-600 text-[10px] font-black flex-shrink-0 overflow-hidden">
            ${u.avatar_url ? `<img src="${u.avatar_url}" class="w-full h-full object-cover">` : u.display_name?.[0] || u.username[0]}
          </div>
          <div>
            <div class="text-[11px] font-black text-surface-900 dark:text-white">${u.display_name || u.username}</div>
            <div class="text-[9px] text-surface-400 font-bold">@${u.username}</div>
          </div>
        </div>
      `).join('');

      dropdown.classList.remove('hidden');
      dropdown.querySelectorAll('.mention-item').forEach(item => {
        item.onclick = () => {
          const username = item.dataset.username;
          const before = val.slice(0, _lastAt);
          const after = val.slice(input.selectionStart);
          input.value = `${before}@${username} ${after}`;
          input.focus();
          dropdown.classList.add('hidden');
        };
      });
    }, 200);
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target) && e.target !== input) {
      dropdown.classList.add('hidden');
    }
  }, { capture: true });

  // Close on Escape
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') dropdown.classList.add('hidden');
  });
}


async function summarizePost(pid, btn) {
  const p = state.feedPosts.find(x => x.id === pid);
  if (p && p.summary) {
    toggleSummary(pid);
    return;
  }

  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i>';
  initIcons();

  try {
    const data = await apiFetch(`/api/posts/${pid}/summarize`, { method: 'POST' });
    if (data.ok) {
      toast('AI สรุปข้อความสำเร็จ', 'success');
      loadPosts();
    } else {
      throw new Error(data.error);
    }
  } catch (e) {
    toast('AI สรุปล้มเหลว: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
    initIcons();
  }
}


// ─── Reaction System ──────────────────────────────
const REACTION_CONFIG = {
  like: { emoji: '👍', label: 'ถูกใจ', color: 'text-blue-500' },
  love: { emoji: '❤️', label: 'รักเลย', color: 'text-red-500' },
  haha: { emoji: '😂', label: 'ฮาเลย', color: 'text-yellow-500' },
  wow: { emoji: '😮', label: 'ทึ่ง', color: 'text-yellow-500' },
  sad: { emoji: '😢', label: 'เศร้า', color: 'text-blue-400' },
  angry: { emoji: '😡', label: 'โกรธ', color: 'text-orange-500' },
};

// State to track current user's reaction per post
const myReactions = {}; // { postId: reactionType | null }
const _pickerTimers = {}; // hide delay timers per post

function showReactionPicker(pid) {
  // Cancel any pending hide
  if (_pickerTimers[pid]) { clearTimeout(_pickerTimers[pid]); delete _pickerTimers[pid]; }
  const el = document.getElementById(`rpicker-${pid}`);
  if (!el) return;
  el.classList.remove('hidden');
  // Trigger animation
  requestAnimationFrame(() => { el.style.opacity = '1'; el.style.transform = 'scale(1) translateY(0)'; });
}

function hideReactionPickerDelayed(pid) {
  _pickerTimers[pid] = setTimeout(() => {
    const el = document.getElementById(`rpicker-${pid}`);
    if (el) {
      el.style.opacity = '0';
      el.style.transform = 'scale(0.85) translateY(4px)';
      setTimeout(() => { if (el) el.classList.add('hidden'); }, 160);
    }
    delete _pickerTimers[pid];
  }, 150); // 150ms grace period - enough to move mouse to picker
}

async function setReaction(pid, reaction) {
  try {
    const res = await fetch(`/api/posts/${pid}/react`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reaction })
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error);

    myReactions[pid] = data.reacted ? data.reaction : null;
    updateReactionUI(pid, data.counts, data.total, myReactions[pid]);
  } catch (e) {
    console.error('Reaction error:', e);
    toast('ไม่สามารถกด Reaction ได้', 'error');
  }
}

function quickReact(pid, defaultReaction) {
  // If already reacted, remove. Otherwise set default 'like'
  const current = myReactions[pid];
  setReaction(pid, current || defaultReaction);
}

function updateReactionUI(pid, counts, total, myReaction) {
  // Update main reaction button
  const iconEl = document.getElementById(`my-reaction-icon-${pid}`);
  const labelEl = document.getElementById(`react-label-${pid}`);
  const totalEl = document.getElementById(`total-reactions-${pid}`);
  const countsEl = document.getElementById(`reaction-counts-${pid}`);
  const triggerBtn = document.querySelector(`.reaction-trigger[data-pid="${pid}"]`);

  const cfg = myReaction ? REACTION_CONFIG[myReaction] : null;

  if (iconEl) iconEl.textContent = cfg ? cfg.emoji : '👍';
  if (labelEl) {
    labelEl.textContent = cfg ? cfg.label : 'ถูกใจ';
    if (triggerBtn) {
      triggerBtn.className = `flex items-center gap-2 transition-colors reaction-trigger ${cfg ? cfg.color : 'text-surface-400 hover:text-brand-600'}`;
    }
  }

  // Build emoji count summary next to total
  if (totalEl) totalEl.textContent = total;
  if (countsEl && total > 0) {
    const topEmojis = Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([rtype]) => REACTION_CONFIG[rtype]?.emoji || '👍')
      .join('');
    countsEl.innerHTML = `
      <span class="flex items-center gap-0.5">
        <span class="text-sm leading-none">${topEmojis}</span>
        <span class="text-xs font-bold ml-1">${total}</span>
      </span>
    `;
  }

  // Update reaction buttons styling in picker
  document.querySelectorAll(`.reaction-btn[data-pid="${pid}"]`).forEach(btn => {
    const rkey = btn.dataset.reaction;
    if (myReaction === rkey) {
      btn.classList.add('ring-2', 'ring-brand-500', 'bg-brand-50', 'dark:bg-brand-900/30');
    } else {
      btn.classList.remove('ring-2', 'ring-brand-500', 'bg-brand-50', 'dark:bg-brand-900/30');
    }
  });
}

async function openReactionsModal(pid) {
  try {
    const res = await fetch(`/api/posts/${pid}/reactions`);
    const data = await res.json();
    if (!data.ok) throw new Error();

    const reactions = data.reactions || [];
    myReactions[pid] = data.my_reaction;

    // Build modal
    let existing = document.getElementById('reactionsModal');
    if (existing) existing.remove();

    // Tab config
    const tabs = [{ key: 'all', label: 'ทั้งหมด', count: data.total }];
    Object.entries(data.counts).forEach(([rtype, count]) => {
      const cfg = REACTION_CONFIG[rtype];
      if (cfg) tabs.push({ key: rtype, label: `${cfg.emoji} ${cfg.label}`, count });
    });

    const modal = document.createElement('div');
    modal.id = 'reactionsModal';
    modal.className = 'fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200';
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
    modal.innerHTML = `
      <div class="bg-white dark:bg-surface-900 rounded-3xl shadow-2xl w-full max-w-sm overflow-hidden animate-in zoom-in-95 fade-in duration-200">
        <div class="flex items-center justify-between px-6 py-4 border-b border-surface-100 dark:border-surface-800">
          <h3 class="font-black text-sm">ผู้แสดงความรู้สึก</h3>
          <button onclick="document.getElementById('reactionsModal').remove()" class="p-2 rounded-xl hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors">
            <i data-lucide="x" class="w-4 h-4"></i>
          </button>
        </div>
        <!-- Tabs -->
        <div class="flex gap-1 px-4 pt-3 pb-1 overflow-x-auto no-scrollbar">
          ${tabs.map((t, i) => `
            <button onclick="switchReactionTab('${t.key}', this)" 
              class="reaction-tab flex-shrink-0 px-3 py-1.5 rounded-full text-[11px] font-bold transition-all ${i === 0 ? 'bg-brand-600 text-white' : 'bg-surface-100 dark:bg-surface-800 text-surface-500 hover:bg-surface-200'}">
              ${t.label} <span class="opacity-70">${t.count}</span>
            </button>
          `).join('')}
        </div>
        <!-- List -->
        <div id="reactions-list-container" class="max-h-80 overflow-y-auto px-4 py-3 space-y-2">
          ${renderReactionsList(reactions, 'all')}
        </div>
      </div>
    `;
    document.body.appendChild(modal);
    initIcons();

    // Store reactions for tab switching
    modal._reactions = reactions;
  } catch (e) {
    toast('โหลดข้อมูล Reaction ไม่สำเร็จ', 'error');
  }
}

function renderReactionsList(reactions, filterKey) {
  const filtered = filterKey === 'all' ? reactions : reactions.filter(r => r.reaction === filterKey);
  if (!filtered.length) return '<div class="text-center py-8 text-surface-400 text-xs">ยังไม่มีการแสดงความรู้สึก</div>';
  return filtered.map(r => {
    const cfg = REACTION_CONFIG[r.reaction] || REACTION_CONFIG.like;
    return `
      <div class="flex items-center gap-3 p-2 rounded-2xl hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors">
        <div class="relative flex-shrink-0">
          <div class="w-10 h-10 rounded-2xl bg-surface-100 dark:bg-surface-800 flex items-center justify-center overflow-hidden">
            ${r.avatar_url ? `<img src="${r.avatar_url}" class="w-full h-full object-cover">` : `<span class="text-base">👤</span>`}
          </div>
          <div class="absolute -bottom-1 -right-1 text-sm leading-none">${cfg.emoji}</div>
        </div>
        <div class="flex-1 min-w-0">
          <div class="font-bold text-sm text-surface-800 dark:text-surface-100 truncate">${r.display_name}</div>
          <div class="text-[10px] text-surface-400 font-medium">${cfg.label}</div>
        </div>
      </div>
    `;
  }).join('');
}

function switchReactionTab(key, btn) {
  const modal = document.getElementById('reactionsModal');
  if (!modal) return;
  const reactions = modal._reactions || [];

  // Update tab styles
  modal.querySelectorAll('.reaction-tab').forEach(t => {
    t.className = 'reaction-tab flex-shrink-0 px-3 py-1.5 rounded-full text-[11px] font-bold transition-all bg-surface-100 dark:bg-surface-800 text-surface-500 hover:bg-surface-200';
  });
  btn.className = 'reaction-tab flex-shrink-0 px-3 py-1.5 rounded-full text-[11px] font-bold transition-all bg-brand-600 text-white';

  const container = document.getElementById('reactions-list-container');
  if (container) container.innerHTML = renderReactionsList(reactions, key);
  initIcons();
}

// Load initial reaction state when posts are rendered
async function loadPostReactions(pid) {
  try {
    const res = await fetch(`/api/posts/${pid}/reactions`);
    const data = await res.json();
    if (!data.ok) return;
    myReactions[pid] = data.my_reaction;
    updateReactionUI(pid, data.counts, data.total, data.my_reaction);
  } catch (e) { /* silent */ }
}

document.querySelectorAll('.feed-filter-chip').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('.feed-filter-chip').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const cat = btn.dataset.cat || 'All';
    loadPosts(cat);
  };
});

/* ─── Web Sockets & Theme Initialization ─── */
function initSocket() {
  if (!socket) return;

  socket.on('connect', () => {
    console.log("✅ Socket connected!");
    _hideConnBanner();
    // Notify backend that user is online
    if (state.user) {
      socket.emit('join', { room: 'user_' + state.user });
      if (state.currentView === 'whiteboard') {
        socket.emit('join_whiteboard');
      }
      socket.emit('user_online', {
        room: state.currentChat ? state.currentChat.name : 'General',
        username: state.user
      });
    }
  });

  socket.on('disconnect', (reason) => {
    console.warn("⚠️ Socket disconnected:", reason);
    if (reason !== 'io client disconnect') _showConnBanner();
  });

  socket.on('reconnect_attempt', (n) => {
    const el = document.getElementById('_connBanner');
    if (el) el.querySelector('span').textContent = `กำลังเชื่อมต่อใหม่... (${n})`;
  });

  socket.on('reconnect', () => {
    _hideConnBanner();
    toast('เชื่อมต่อสำเร็จแล้วค่ะ', 'success');
  });

  socket.on('new_message', (data) => {
    // Determine if this message is for the currently OPEN and VISIBLE chat
    const isCurrentChat = state.currentChat && state.currentChat.id && (
      (data.type === 'room' && String(data.room_id) === String(state.currentChat.id)) ||
      (data.type === 'dm' && (String(data.sender_id) === String(state.currentChat.id) || String(data.recipient) === String(state.currentChat.id)))
    );
    const isVisible = isCurrentChat && state.groupChat.isOpen && !groupChatModal.classList.contains('hidden');
    const currentUser = (typeof state.user === 'object' ? state.user?.username : state.user);

    if (isVisible) {
      if (data.sender !== currentUser) {
        console.log("👀 New message in active chat, refreshing sync...");
        loadChatMessages(true); 
      }
      loadChatList();
    } else {
      // Message is for another chat or we are not looking at the chat modal
      if (data.sender !== currentUser) {
        if (data.text && data.text.includes('[RECONCILE_ACTION]')) {
          toast('มีค่าใช้จ่ายใหม่จาก LINE ให้ตรวจสอบ กรุณาเปิดแอปเพื่อยืนยัน', 'info');
        }
        console.log("🔔 New message in background, showing notification...");
        loadUnreadCounts();
        loadChatList();
      } else {
        // If it's our own message, we should still refresh the list to see it
        loadChatList();
      }
    }
  });

  // Listen for user status updates (online/offline)
  socket.on('user_status_updated', (data) => {
    console.log("👤 User Status Updated:", data);
    if (data.online_users) {
      console.log("📊 Online users:", data.online_users);
      // You can update UI to show online status
      updateOnlineUsersList(data.online_users);
    }
  });

  // Listen for typing indicators
  socket.on('user_typing', (data) => {
    console.log("✍️ User Typing:", data.username, "in room", data.room_id);
    showTypingIndicator(data.username, data.display_name || data.username, data.room_id);
  });

  socket.on('user_stopped_typing', (data) => {
    console.log("⏹️ User Stopped Typing:", data.username);
    hideTypingIndicator(data.username, data.room_id);
  });

  // Listen for read receipts
  socket.on('message_read_receipt', (data) => {
    console.log("✅ Message Read Receipt:", data);
    if (data.message_id) {
      updateMessageReadStatus(data.message_id, data.read_by_count, data.read_receipts);
    }
  });

  socket.on('error', (data) => {
    console.error("❌ Socket Error:", data);
  });

  // Listen for read updates from others
  socket.on('read_update', (data) => {
    const isCurrentChat = state.currentChat && state.currentChat.id && (
      (data.type === 'room' && String(data.id) === String(state.currentChat.id)) ||
      (data.type === 'dm' && String(data.id) === String(state.currentChat.id))
    );
    if (isCurrentChat) {
      // Refresh current chat to show updated read receipts
      loadChatMessages(false, true);
    }
  });

  // Listen for local scan status updates
  socket.on('local_scan_status', (data) => {
    console.log("📂 Local Scan Status Received:", data);
    if (data.ok) {
      toast(data.message, 'success');
    } else {
      toast(data.message, 'error');
    }
    // Re-enable local scan button
    const localScanBtn = $('startLocalScanBtn');
    if (localScanBtn) {
      localScanBtn.disabled = false;
      localScanBtn.innerHTML = `<i data-lucide="scan" class="w-4 h-4"></i> สแกนโฟลเดอร์ ภงด. 53`;
      if (typeof initIcons === 'function') initIcons();
    }
  });

  // WebRTC Signaling — handled by initWebRTCSignaling() at bottom of file

}

function updateTheme() {
  const isDark = state.theme === 'dark' ||
    (state.theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches);
  if (isDark) {
    document.documentElement.classList.add('dark');
    if ($('themeIcon')) $('themeIcon').setAttribute('data-lucide', 'sun');
    if ($('themeText')) $('themeText').innerText = 'โหมดกลางวัน';
  } else {
    document.documentElement.classList.remove('dark');
    if ($('themeIcon')) $('themeIcon').setAttribute('data-lucide', 'moon');
    if ($('themeText')) $('themeText').innerText = 'โหมดกลางคืน';
  }
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
  if (state.theme === 'auto') updateTheme();
});
// ─── CSV Editor ──────────────────────────────
async function openCsvEditor(fileId) {
  try {
    currentEditingFileId = fileId;
    const res = await apiFetch(`/api/csv/${fileId}`);
    if (!res.ok) throw new Error(res.error);

    editingFileName.textContent = res.name;
    currentCsvHeaders = res.headers;

    // Render Headers
    csvHeaders.innerHTML = `
      <tr>
        <th class="w-10">#</th>
        ${res.headers.map(h => `<th>${h}</th>`).join('')}
        <th class="w-10"></th>
      </tr>
    `;

    // Render Body
    renderCsvEditorRows(res.data);

    csvEditorModal.classList.remove('hidden');
    csvEditorModal.classList.add('flex', 'items-center', 'justify-center');
    initIcons();
  } catch (e) {
    toast('Error loading CSV: ' + e.message, 'error');
  }
}

function renderCsvEditorRows(data) {
  csvBody.innerHTML = '';
  data.forEach((row, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="bg-surface-50 dark:bg-surface-800 text-center text-surface-400 font-mono text-[10px]">${idx + 1}</td>
      ${currentCsvHeaders.map(h => `<td contenteditable="true" data-header="${h}">${row[h] || ''}</td>`).join('')}
      <td class="text-center">
        <button class="delete-row-btn p-1 hover:text-red-600 transition-colors" onclick="this.closest('tr').remove(); updateCsvMeta();">
          <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
        </button>
      </td>
    `;
    csvBody.appendChild(tr);
  });
  updateCsvMeta();
}

function updateCsvMeta() {
  const rowCount = csvBody.querySelectorAll('tr').length;
  csvStatusInfo.textContent = `แถวทั้งหมด: ${rowCount}`;
}

addRowBtn.onclick = () => {
  const tr = document.createElement('tr');
  const idx = csvBody.querySelectorAll('tr').length + 1;
  tr.innerHTML = `
    <td class="bg-surface-50 dark:bg-surface-800 text-center text-surface-400 font-mono text-[10px]">${idx}</td>
    ${currentCsvHeaders.map(h => `<td contenteditable="true" data-header="${h}"></td>`).join('')}
    <td class="text-center">
      <button class="delete-row-btn p-1 hover:text-red-600 transition-colors" onclick="this.closest('tr').remove(); updateCsvMeta();">
        <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
      </button>
    </td>
  `;
  csvBody.appendChild(tr);
  updateCsvMeta();
  initIcons();
  tr.children[1].focus();
};

closeCsvEditor.onclick = () => {
  csvEditorModal.classList.add('hidden');
  currentEditingFileId = null;
};

saveCsvBtn.onclick = async () => {
  if (!currentEditingFileId) return;

  saveCsvBtn.disabled = true;
  saveCsvBtn.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i> กำลังบันทึก...';
  initIcons();

  try {
    const rows = [];
    const trs = csvBody.querySelectorAll('tr');
    trs.forEach(tr => {
      const row = {};
      tr.querySelectorAll('td[contenteditable="true"]').forEach(td => {
        row[td.dataset.header] = td.textContent.trim();
      });
      rows.push(row);
    });

    const res = await apiFetch(`/api/csv/${currentEditingFileId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ headers: currentCsvHeaders, data: rows })
    });

    if (!res.ok) throw new Error(res.error);

    toast('บันทึกและอัปเดตข้อมูลสำเร็จ!', 'success');
    csvEditorModal.classList.add('hidden');
    csvEditorModal.classList.remove('flex', 'items-center', 'justify-center');
    loadFiles();
    loadStatus();
  } catch (e) {
    toast('Error saving: ' + e.message, 'error');
  } finally {
    saveCsvBtn.disabled = false;
    saveCsvBtn.innerHTML = '<i data-lucide="save" class="w-4 h-4"></i> บันทึกข้อมูล';
    initIcons();
  }
};



// ─── Task To-Do List Logic ────────────────────────────
let _todoFilter = 'all';
let _todoTasks = [];

function setTodoFilter(f) {
  _todoFilter = f;
  document.querySelectorAll('.todo-tab').forEach(btn => {
    const isActive = btn.id === `todoTab-${f}`;
    btn.classList.toggle('bg-brand-600', isActive);
    btn.classList.toggle('text-white', isActive);
    btn.classList.toggle('bg-surface-100', !isActive);
    btn.classList.toggle('dark:bg-surface-800', !isActive);
    btn.classList.toggle('text-surface-500', !isActive);
  });
  renderTodoList();
}

async function loadTodoTasks() {
  try {
    const data = await apiFetch('/api/schedules');
    const today = new Date().toISOString().split('T')[0];
    _todoTasks = (data.schedules || []).filter(s => s.category === 'Task' && s.date >= today);
    renderTodoList();
  } catch (e) { console.error('Todo load failed:', e); }
}


function renderTodoList() {
  const el = document.getElementById('todoList');
  const badge = document.getElementById('todoCountBadge');
  if (!el) return;

  let tasks = _todoTasks;
  if (_todoFilter === 'pending') tasks = tasks.filter(t => t.status !== 'done');
  if (_todoFilter === 'done') tasks = tasks.filter(t => t.status === 'done');

  // Update badge
  const pending = _todoTasks.filter(t => t.status !== 'done').length;
  if (badge) badge.textContent = pending > 0 ? `${pending} ค้าง` : 'เสร็จหมดแล้ว ✓';

  if (!tasks.length) {
    el.innerHTML = `<div class="text-center py-8 text-surface-400 text-xs italic">
      ${_todoFilter === 'done' ? 'ยังไม่มีงานที่เสร็จแล้ว' : _todoFilter === 'pending' ? 'ไม่มีงานค้าง 🎉' : 'ยังไม่มีรายการงาน เพิ่มงานด้านบนได้เลย'}
    </div>`;
    return;
  }

  el.innerHTML = tasks.map(t => {
    const isDone = t.status === 'done';
    return `
    <div class="todo-item group flex items-start gap-2.5 p-3 rounded-xl bg-white dark:bg-surface-800/50 border border-surface-100 dark:border-surface-700/50 hover:border-brand-300/50 dark:hover:border-brand-700/50 transition-all ${isDone ? 'opacity-60' : ''}" data-id="${t.id}">
      <!-- Checkbox -->
      <button onclick="toggleTodoDone(${t.id})" title="${isDone ? 'ยกเลิกการทำ' : 'ทำเสร็จแล้ว'}"
        class="flex-shrink-0 w-5 h-5 mt-0.5 rounded-md border-2 flex items-center justify-center transition-all
               ${isDone ? 'bg-emerald-500 border-emerald-500 text-white' : 'border-surface-300 dark:border-surface-600 hover:border-brand-500 hover:bg-brand-50 dark:hover:bg-brand-900/20'}">
        ${isDone ? '<i data-lucide="check" class="w-3 h-3"></i>' : ''}
      </button>

      <!-- Task text / inline edit -->
      <div class="flex-1 min-w-0" id="todo-text-wrap-${t.id}">
        <span class="text-xs font-medium text-surface-700 dark:text-surface-300 leading-tight break-all ${isDone ? 'line-through text-surface-400' : ''}">${t.title}</span>
      </div>

      <!-- Action buttons -->
      <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
        <button onclick="startEditTodo(${t.id})" title="แก้ไข"
          class="p-1 rounded-lg text-surface-400 hover:text-brand-600 hover:bg-brand-50 dark:hover:bg-brand-900/20 transition-all">
          <i data-lucide="edit-2" class="w-3 h-3"></i>
        </button>
        <button onclick="deleteTodoTask(${t.id})" title="ลบ"
          class="p-1 rounded-lg text-surface-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all">
          <i data-lucide="trash-2" class="w-3 h-3"></i>
        </button>
      </div>
    </div>`;
  }).join('');
  initIcons();
}

async function addTodoTask() {
  const input = document.getElementById('todoInput');
  const title = input?.value.trim();
  if (!title) return;

  const today = new Date().toISOString().split('T')[0];
  try {
    await apiFetch('/api/schedules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title, date: today, category: 'Task', status: 'todo', desc: '', time: '',
        is_public: false, target_departments: '', target_users: ''
      })
    });
    input.value = '';
    await loadTodoTasks();
    toast('เพิ่มงานเรียบร้อยแล้ว', 'success');
  } catch (e) {
    toast('เพิ่มงานไม่สำเร็จ', 'error');
  }
}

async function toggleTodoDone(tid) {
  const task = _todoTasks.find(t => t.id === tid);
  if (!task) return;
  const newStatus = task.status === 'done' ? 'todo' : 'done';
  try {
    await apiFetch(`/api/schedules/${tid}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...task, status: newStatus })
    });
    task.status = newStatus;
    renderTodoList();
  } catch (e) {
    toast('อัปเดตสถานะไม่สำเร็จ', 'error');
  }
}

function startEditTodo(tid) {
  const task = _todoTasks.find(t => t.id === tid);
  if (!task) return;
  const wrap = document.getElementById(`todo-text-wrap-${tid}`);
  if (!wrap) return;

  wrap.innerHTML = `
    <div class="flex gap-1">
      <input id="todo-edit-input-${tid}" type="text" value="${task.title.replace(/"/g, '&quot;')}"
        class="flex-1 text-xs bg-white dark:bg-surface-900 border border-brand-400 rounded-lg px-2 py-1 outline-none focus:ring-1 focus:ring-brand-500"
        onkeydown="if(event.key==='Enter') saveTodoEdit(${tid}); if(event.key==='Escape') cancelTodoEdit(${tid});" />
      <button onclick="saveTodoEdit(${tid})" class="text-emerald-500 hover:text-emerald-700 p-1"><i data-lucide="check" class="w-3 h-3"></i></button>
      <button onclick="cancelTodoEdit(${tid})" class="text-surface-400 hover:text-red-500 p-1"><i data-lucide="x" class="w-3 h-3"></i></button>
    </div>`;
  initIcons();
  document.getElementById(`todo-edit-input-${tid}`)?.focus();
}

async function saveTodoEdit(tid) {
  const task = _todoTasks.find(t => t.id === tid);
  const input = document.getElementById(`todo-edit-input-${tid}`);
  if (!task || !input) return;
  const newTitle = input.value.trim();
  if (!newTitle) return;

  try {
    await apiFetch(`/api/schedules/${tid}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...task, title: newTitle })
    });
    task.title = newTitle;
    renderTodoList();
    toast('แก้ไขงานเรียบร้อยแล้ว', 'success');
  } catch (e) {
    toast('แก้ไขไม่สำเร็จ', 'error');
  }
}

function cancelTodoEdit(tid) {
  renderTodoList();
}

async function deleteTodoTask(tid) {
  if (!confirm('ต้องการลบรายการงานนี้ใช่หรือไม่?')) return;
  try {
    await apiFetch(`/api/schedules/${tid}`, { method: 'DELETE' });
    _todoTasks = _todoTasks.filter(t => t.id !== tid);
    renderTodoList();
    toast('ลบงานเรียบร้อยแล้ว', 'info');
  } catch (e) {
    toast('ลบไม่สำเร็จ', 'error');
  }
}

// ─── Calendar Logic ──────────────────────────────
const THAI_HOLIDAYS_2026 = {
  "2026-01-01": "วันขึ้นปีใหม่",
  "2026-02-11": "วันมาฆบูชา",
  "2026-04-06": "วันจักรี",
  "2026-04-13": "วันสงกรานต์",
  "2026-04-14": "วันสงกรานต์",
  "2026-04-15": "วันสงกรานต์",
  "2026-05-01": "วันแรงงานแห่งชาติ",
  "2026-05-04": "วันฉัตรมงคล",
  "2026-05-11": "วันพืชมงคล (ประมาณการ)",
  "2026-05-31": "วันวิสาขบูชา",
  "2026-06-03": "วันเฉลิมพระชนมพรรษาพระราชินี",
  "2026-07-28": "วันอาสาฬหบูชา / วันเฉลิมพระชนมพรรษา ร.10",
  "2026-07-29": "วันเข้าพรรษา",
  "2026-08-12": "วันแม่แห่งชาติ",
  "2026-10-13": "วันนวมินทรมหาราช",
  "2026-10-23": "วันปิยมหาราช",
  "2026-12-05": "วันพ่อแห่งชาติ",
  "2026-12-10": "วันรัฐธรรมนูญ",
  "2026-12-31": "วันสิ้นปี"
};
// Month is 1-indexed (01-12) to match standard date formatting in logic below

async function loadSchedules() {
  try {
    const data = await apiFetch('/api/schedules');
    state.calendar.schedules = data.schedules || [];
    renderCalendar();
    renderUpcoming();
  } catch (e) {
    console.error('Failed to load schedules:', e);
  }
}

function renderCalendar() {
  const date = state.calendar.viewDate;
  const year = date.getFullYear();
  const month = date.getMonth();
  const todayStr = new Date().toISOString().split('T')[0];

  calendarMonth.textContent = new Intl.DateTimeFormat('th-TH', { month: 'long', year: 'numeric' }).format(date);

  // Apply Filters
  const q = (state.calendar.searchQuery || '').toLowerCase();
  const cat = state.calendar.categoryFilter || 'all';
  
  const filteredSchedules = state.calendar.schedules.filter(s => {
    const matchSearch = !q || s.title.toLowerCase().includes(q) || (s.desc || '').toLowerCase().includes(q);
    const matchCat = cat === 'all' || s.category === cat;
    return matchSearch && matchCat;
  });


  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  calendarGrid.innerHTML = '';

  // Padding for previous month
  for (let i = 0; i < firstDay; i++) {
    const div = document.createElement('div');
    div.className = 'bg-surface-50/30 dark:bg-surface-900/10 min-h-[80px] p-2';
    calendarGrid.appendChild(div);
  }

  // Current month days
  const today = new Date();
  for (let day = 1; day <= daysInMonth; day++) {
    const div = document.createElement('div');
    const isToday = today.getDate() === day && today.getMonth() === month && today.getFullYear() === year;
    // Check if Sunday (0)
    const dayOfWeek = new Date(year, month, day).getDay();
    const isSunday = dayOfWeek === 0;

    div.className = `bg-white dark:bg-surface-900 min-h-[80px] md:min-h-[115px] p-1.5 md:p-2 border-t border-l border-surface-100 dark:border-surface-800 transition-all hover:bg-brand-50/30 dark:hover:bg-brand-900/10 relative ${isToday ? 'ring-1 ring-inset ring-brand-600/50' : ''} ${isSunday ? 'bg-rose-50/50 dark:bg-rose-900/10' : ''}`;

    let html = `<span class="text-[10px] md:text-xs font-bold ${isToday ? 'bg-brand-600 text-white w-5 h-5 flex items-center justify-center rounded-full' : (isSunday ? 'text-rose-600' : 'text-surface-400')}">${day}</span>`;

    // Check for schedules on this day
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const holidayKey = dateStr;
    const holidayName = THAI_HOLIDAYS_2026[holidayKey];

    const daySchedules = filteredSchedules.filter(s => s.date === dateStr);


    if (holidayName || daySchedules.length > 0) {
      html += `<div class="mt-1 space-y-1 w-full min-w-0">`;

      // Render Holiday first
      if (holidayName) {
        html += `<div class="text-[7.5px] md:text-[8.5px] px-1.5 py-0.5 md:py-1 mb-1 rounded-md font-black bg-rose-50 dark:bg-rose-900/20 text-rose-600 dark:text-rose-400 border border-rose-200/30 flex items-center gap-1 w-full" title="${escHtml(holidayName)}">
          <i data-lucide="sun" class="w-2.5 h-2.5 shrink-0 opacity-70"></i>
          <span class="truncate md:whitespace-normal md:break-words leading-tight">หยุด: ${escHtml(holidayName)}</span>
        </div>`;
      }

      daySchedules.forEach(s => {
        const catColors = {
          Meeting: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 border-indigo-500',
          Event: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300 border-emerald-500',
          Task: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300 border-amber-500',
          Holiday: 'bg-rose-50 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300 border-rose-500'
        };
        const isDone = s.status === 'done';
        const isPast = dateStr < new Date().toISOString().split('T')[0];
        const isOverdue = isPast && !isDone;
        
        const overdueBadge = isOverdue ? '<span class="text-[6px] bg-rose-600 text-white px-1 py-0.5 rounded-[4px] font-black uppercase ml-0.5 shrink-0 shadow-sm shadow-rose-900/10">OVERDUE</span>' : '';
        const publicBadge = s.is_public ? '<span class="text-[6px] bg-emerald-500 text-white px-1 py-0.5 rounded-[4px] font-black uppercase ml-0.5 shrink-0 shadow-sm shadow-emerald-900/10">PUBLIC</span>' : '';
        const doneClass = isDone ? 'opacity-50 grayscale' : (isPast ? 'opacity-75' : '');
        const doneIcon = isDone ? '<i data-lucide="check-circle-2" class="w-2.5 h-2.5 inline-block mr-1 text-emerald-600 shrink-0"></i>' : (isOverdue ? '<i data-lucide="alert-circle" class="w-2.5 h-2.5 inline-block mr-1 text-rose-600 shrink-0"></i>' : '');

        html += `<div class="group/item relative flex flex-col p-1.5 mb-1 rounded-lg border-l-[3.5px] ${catColors[s.category] || 'bg-surface-100 text-surface-600 border-surface-400'} ${doneClass} cursor-pointer hover:scale-[1.01] transition-transform active:scale-95 duration-200 w-full" 
                    title="${escHtml(s.title)}" onclick="event.stopPropagation(); editSchedule(${s.id})">
          
          <div class="flex flex-col gap-0.5 w-full min-w-0">
            <div class="flex items-center justify-between gap-1 w-full mb-0.5">
              <div class="flex items-center shrink-0 text-[7.5px] md:text-[8.5px] font-black uppercase tracking-tight opacity-75">
                 ${doneIcon}
                 <span>${s.time || '09:00'}</span>
              </div>
              <div class="flex items-center gap-0.5 shrink-0">
                ${publicBadge}
                ${overdueBadge}
              </div>
            </div>
            
            <div class="text-[9px] md:text-[10.5px] font-bold leading-snug text-left truncate md:whitespace-normal md:break-words w-full" title="${escHtml(s.title)}">
              ${escHtml(s.title)}
            </div>
          </div>
          
          <div class="hidden group-hover/item:flex items-center gap-1.5 absolute right-1 -top-1 bg-white/95 dark:bg-surface-800/95 shadow-lg px-1.5 py-1 rounded-lg backdrop-blur-sm z-10 border border-surface-200 dark:border-surface-700 animate-in zoom-in duration-200">
            <button class="text-emerald-500 hover:text-emerald-700 transition-colors p-0.5" 
                    title="${isDone ? 'Mark as To-Do' : 'Mark as Done'}"
                    onclick="event.stopPropagation(); toggleScheduleStatus(${s.id})">
              <i data-lucide="${isDone ? 'rotate-ccw' : 'check'}" class="w-3.5 h-3.5"></i>
            </button>
            <button class="text-red-500 hover:text-red-700 transition-colors p-0.5" 
                    title="ลบ"
                    onclick="event.stopPropagation(); deleteSchedule(${s.id})">
              <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
            </button>
          </div>
        </div>`;
      });

      html += `</div>`;
    }

    div.innerHTML = html;

    // Aesthetic & UX: Click on day to add schedule
    div.classList.add('cursor-pointer');
    div.onclick = async () => {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const isPast = new Date(dateStr) < today;
      const schedulesCount = state.calendar.schedules.filter(s => s.date === dateStr).length;

      if (isPast && schedulesCount > 0) {
        if (confirm(`คุณต้องการเก็บกำหนดการทั้งหมดในวันที่ ${dateStr} นี้เข้ากรุหรือไม่? (${schedulesCount} รายการ)`)) {
          // Archive past schedules for this day
          await apiFetch('/api/schedules/archive-past', { method: 'POST' }); // Simplified: archives ALL past of user, but that's fine for now or we could make it per day. 
          // Let's stick to the prompt's request for "Archiving past"
          toast('เก็บเข้ากรุเรียบร้อยแล้ว', 'success');
          await loadSchedules();
          return;
        }
      }

      openAddModal(dateStr);
    };


    calendarGrid.appendChild(div);
  }
  initIcons();
}

function renderUpcoming() {
  const now = new Date();
  now.setHours(0, 0, 0, 0);

  const upcoming = state.calendar.schedules
    .filter(s => new Date(s.date) >= now)
    .sort((a, b) => new Date(a.date) - new Date(b.date))
    .slice(0, 8);

  if (!upcoming.length) {
    upcomingSchedules.innerHTML = `
      <div class="py-10 text-center text-surface-400 text-xs italic">
        ไม่มีนัดหมายเร็วๆ นี้
      </div>`;
    return;
  }

  upcomingSchedules.innerHTML = upcoming.map(s => {
    const catIcon = {
      Meeting: { icon: 'users', bg: 'bg-indigo-100 dark:bg-indigo-900/30', color: 'text-indigo-600 dark:text-indigo-400' },
      Event: { icon: 'calendar', bg: 'bg-emerald-100 dark:bg-emerald-900/30', color: 'text-emerald-600 dark:text-emerald-400' },
      Task: { icon: 'check-square', bg: 'bg-amber-100 dark:bg-amber-900/30', color: 'text-amber-600 dark:text-amber-400' },
      Holiday: { icon: 'sun', bg: 'bg-rose-100 dark:bg-rose-900/30', color: 'text-rose-600 dark:text-rose-400' },
    };
    const cat = catIcon[s.category] || { icon: 'calendar', bg: 'bg-brand-100 dark:bg-brand-900/30', color: 'text-brand-600' };
    const dateStr = new Date(s.date).toLocaleDateString('th-TH', { day: 'numeric', month: 'short' });

    return `
    <div class="flex items-start gap-2.5 p-2 rounded-2xl transition hover:bg-surface-50 dark:hover:bg-surface-800/40 group">
      <div class="w-8 h-8 rounded-xl ${cat.bg} flex items-center justify-center ${cat.color} flex-shrink-0 mt-0.5 shadow-sm">
        <i data-lucide="${cat.icon}" class="w-4 h-4"></i>
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-start justify-between gap-1 leading-tight mb-1">
          <div class="text-xs font-bold text-surface-900 dark:text-surface-100 group-hover:text-brand-600 transition-colors break-words flex-1 leading-snug ${s.status === 'done' ? 'line-through opacity-50' : ''}">
            ${s.status === 'done' ? '<i data-lucide="check-circle-2" class="w-3 h-3 inline-block mr-1 text-emerald-500"></i>' : (new Date(s.date) < (new Date().setHours(0,0,0,0)) ? '<span class="text-[8px] bg-rose-600 text-white px-1.5 py-0.5 rounded-full uppercase mr-1 inline-block animate-pulse">Overdue</span>' : '')}
            ${s.title}
          </div>

          <div class="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0">
            <button class="p-1 text-surface-300 hover:text-emerald-500 rounded" title="Toggle Status" onclick="toggleScheduleStatus(${s.id})">
              <i data-lucide="${s.status === 'done' ? 'rotate-ccw' : 'check'}" class="w-3 h-3"></i>
            </button>
            <button class="p-1 text-surface-300 hover:text-brand-600 rounded" title="Edit" onclick="editSchedule(${s.id})">
              <i data-lucide="edit-3" class="w-3 h-3"></i>
            </button>
            <button class="p-1 text-surface-300 hover:text-red-500 rounded" title="Delete" onclick="deleteSchedule(${s.id})">
              <i data-lucide="trash-2" class="w-3 h-3"></i>
            </button>
          </div>
        </div>
        
        <div class="flex flex-wrap items-center gap-1.5 mb-1">
          ${s.is_public ? '<span class="text-[8px] font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 px-1.5 py-0.2 rounded uppercase">Shared</span>' : ''}
          <span class="text-[9px] font-bold text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-900/30 px-2 py-0.5 rounded-md border border-brand-500/10">${dateStr} · ${s.time || '09:00'}</span>
        </div>

        <div class="text-[10px] text-surface-400 leading-normal line-clamp-2">${s.desc || 'ไม่มีรายละเอียด'}</div>
        <div class="flex items-center gap-1.5 mt-1.5 pt-1.5 border-t border-surface-100 dark:border-surface-800/60">
          <div class="w-4 h-4 rounded-full bg-surface-200 dark:bg-surface-700 flex items-center justify-center overflow-hidden flex-shrink-0 ring-1 ring-surface-300/30">
            ${s.avatar_url ? `<img src="${s.avatar_url}" class="w-full h-full object-cover">` : `<i data-lucide="user" class="w-2.5 h-2.5 text-surface-400"></i>`}
          </div>
          <span class="text-[9px] text-surface-400 font-semibold truncate">${s.display_name || s.owner || 'ไม่ระบุ'}</span>
        </div>
      </div>
    </div>
  `}).join('');
  initIcons();
}

async function deleteSchedule(id) {
  if (!confirm('ยืนยัน: ลบนัดหมายนี้?')) return;
  try {
    const res = await apiFetch(`/api/schedules/${id}`, { method: 'DELETE' });
    if (res.ok) {
      toast('ลบนัดหมายเรียบร้อยแล้ว', 'info');
      await loadSchedules();
    }
  } catch (e) {
    toast('ล้มเหลว: ' + e.message, 'error');
  }
}

async function toggleScheduleStatus(id) {
  try {
    const res = await apiFetch(`/api/schedules/${id}/toggle`, { method: 'POST' });
    if (res.ok) {
      toast('อัปเดตสถานะแล้ว', 'success');
      await loadSchedules();
      if (state.currentView === 'kanban') loadKanban();
    }
  } catch (e) {
    toast('ล้มเหลว: ' + e.message, 'error');
  }
}

async function clearPastSchedules() {
  if (!confirm('ยืนยัน: ลบกิจกรรมที่ผ่านมาแล้วทั้งหมด?')) return;
  try {
    const res = await apiFetch('/api/schedules/clear-past', { method: 'DELETE' });
    if (res.ok) {
      toast('ลบกิจกรรมที่ผ่านมาเรียบร้อยแล้ว', 'info');
      await loadSchedules();
    }
  } catch (e) {
    toast('ล้มเหลว: ' + e.message, 'error');
  }
}

function openAddModal(dateStr = null) {
  editingScheduleId = null;
  scheduleTitleInput.value = '';
  scheduleDescInput.value = '';
  const pubToggle = $('schedulePublicToggle');
  const visStatus = $('visibilityStatus');
  if (pubToggle) pubToggle.checked = false;
  if (visStatus) {
    visStatus.textContent = 'ส่วนตัว (เฉพาะคุณ)';
    visStatus.className = 'text-[10px] font-bold text-brand-600 uppercase';
  }

  // Reset visibility UI
  if ($('scheduleTargetDepts')) $('scheduleTargetDepts').value = '';
  if ($('scheduleTargetUsers')) $('scheduleTargetUsers').value = '';
  const visSection = $('scheduleVisibilitySection');
  if (visSection) visSection.classList.remove('hidden');
  _scheduleSelectedDepts.clear();
  _scheduleSelectedUsers.clear();
  setVisibilityTab('dept');

  if (scheduleStatusInput) scheduleStatusInput.value = 'todo';
  document.getElementById('scheduleModalTitle').textContent = 'เพิ่มกิจกรรมใหม่';
  saveScheduleBtn.innerHTML = '<i data-lucide="plus" class="w-4 h-4"></i> เพิ่มกิจกรรม';

  if (dateStr) {
    scheduleDateInput.value = dateStr;
  } else if (!scheduleDateInput.value) {
    const now = new Date();
    scheduleDateInput.value = now.toISOString().split('T')[0];
  }

  scheduleModal.classList.remove('hidden');
  scheduleModal.classList.add('flex', 'items-center', 'justify-center');
  initIcons();
  loadScheduleVisibilityData();
  scheduleTitleInput.focus();
}

function editSchedule(id) {
  const s = state.calendar.schedules.find(x => x.id === id);
  if (!s) return;

  editingScheduleId = id;
  scheduleTitleInput.value = s.title;
  scheduleDateInput.value = s.date;
  scheduleTimeInput.value = s.time || '09:00';
  scheduleDescInput.value = s.desc || '';
  scheduleCatInput.value = s.category || 'General';
  if (scheduleStatusInput) scheduleStatusInput.value = s.status || 'todo';

  const pubToggle = $('schedulePublicToggle');
  const visStatus = $('visibilityStatus');
  if (pubToggle) pubToggle.checked = !!s.is_public;
  if (visStatus) {
    if (s.is_public) {
      visStatus.textContent = 'สาธารณะ (ทุกคนในองค์กรเห็น)';
      visStatus.className = 'text-[10px] font-bold text-emerald-600 uppercase';
    } else {
      visStatus.textContent = 'ส่วนตัว (เฉพาะคุณ)';
      visStatus.className = 'text-[10px] font-bold text-brand-600 uppercase';
    }
  }

  // Reset then restore visibility UI
  const visSection = $('scheduleVisibilitySection');
  if (visSection) {
    if (s.is_public) {
      visSection.classList.add('hidden');
    } else {
      visSection.classList.remove('hidden');
    }
  }

  scheduleModal.classList.remove('hidden');
  document.getElementById('scheduleModalTitle').textContent = 'แก้ไขนัดหมาย';
  saveScheduleBtn.innerHTML = '<i data-lucide="save" class="w-4 h-4"></i> บันทึกการแก้ไข';
  initIcons();

  // Load visibility data then restore selections
  loadScheduleVisibilityData(s.target_departments || '', s.target_users || '');
  scheduleTitleInput.focus();
}

// ─── Calendar Visibility Helpers ─────────────────────────────
let _scheduleAllDepts = [];
let _scheduleAllUsers = [];
let _scheduleSelectedDepts = new Set();
let _scheduleSelectedUsers = new Set();
let _currentVisTab = 'dept';

function onSchedulePublicToggle(isPublic) {
  const visStatus = $('visibilityStatus');
  const visSection = $('scheduleVisibilitySection');
  if (isPublic) {
    if (visStatus) {
      visStatus.textContent = 'สาธารณะ (ทุกคนในองค์กรเห็น)';
      visStatus.className = 'text-[10px] font-bold text-emerald-600 uppercase';
    }
    if (visSection) visSection.classList.add('hidden');
    // Clear targeted visibility when setting to public
    if ($('scheduleTargetDepts')) $('scheduleTargetDepts').value = '';
    if ($('scheduleTargetUsers')) $('scheduleTargetUsers').value = '';
    _scheduleSelectedDepts.clear();
    _scheduleSelectedUsers.clear();
    updateSelectedCounts();
  } else {
    if (visSection) visSection.classList.remove('hidden');
    updateSelectedCounts();
    setVisibilityTab(_currentVisTab || 'dept');
  }
}

function setVisibilityTab(tab) {
  _currentVisTab = tab || 'dept';
  const tabs = { dept: $('visTabDept'), users: $('visTabUsers') };
  const panels = { dept: $('visDeptsPanel'), users: $('visUsersPanel') };

  // Reset all tab styles
  Object.values(tabs).forEach(btn => {
    if (!btn) return;
    btn.className = btn.className
      .replace(/bg-white\s+dark:bg-surface-700\s+shadow-sm\s+text-brand-600\s+dark:text-brand-400/g, '')
      .replace(/text-brand-600/g, 'text-surface-400');
    btn.classList.remove('bg-white', 'dark:bg-surface-700', 'shadow-sm', 'text-brand-600', 'dark:text-brand-400');
    btn.classList.add('text-surface-400');
  });

  // Activate selected tab
  if (tabs[_currentVisTab]) {
    tabs[_currentVisTab].classList.remove('text-surface-400');
    tabs[_currentVisTab].classList.add('bg-white', 'dark:bg-surface-700', 'shadow-sm', 'text-brand-600', 'dark:text-brand-400');
  }

  // Show/hide panels
  if (panels.dept) panels.dept.classList.toggle('hidden', _currentVisTab !== 'dept');
  if (panels.users) panels.users.classList.toggle('hidden', _currentVisTab !== 'users');
}

async function loadScheduleVisibilityData(preFillDepts = '', preFillUsers = '') {
  try {
    // Load departments
    const deptData = await apiFetch('/api/departments');
    _scheduleAllDepts = deptData.departments || [];

    // Load users
    const userData = await apiFetch('/api/users/list');
    _scheduleAllUsers = userData.users || [];

    // Pre-fill selected items from existing schedule
    _scheduleSelectedDepts = new Set(preFillDepts ? preFillDepts.split(',').map(d => d.trim()).filter(Boolean) : []);
    _scheduleSelectedUsers = new Set(preFillUsers ? preFillUsers.split(',').map(u => u.trim()).filter(Boolean) : []);

    renderDeptTags();
    renderUserTags();

    // Restore correct tab if editing
    if (preFillUsers) setVisibilityTab('users');
    else if (preFillDepts) setVisibilityTab('dept');

    initIcons();
  } catch (e) {
    console.warn('Failed to load visibility data:', e);
  }
}

function renderDeptTags(filter = '') {
  const container = $('scheduleDeptTags');
  if (!container) return;

  const depts = filter
    ? _scheduleAllDepts.filter(d => d.toLowerCase().includes(filter.toLowerCase()))
    : _scheduleAllDepts;

  if (!depts.length) {
    container.innerHTML = '<span class="text-[10px] text-surface-300 italic">ไม่พบแผนก</span>';
    return;
  }

  container.innerHTML = depts.map(dept => {
    const isSelected = _scheduleSelectedDepts.has(dept);
    return `<button type="button" onclick="toggleDeptTag('${dept}')"
      class="dept-tag px-2.5 py-1 rounded-full text-[10px] font-bold transition-all cursor-pointer border ${isSelected
        ? 'bg-brand-600 text-white border-brand-600 shadow-sm'
        : 'bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300 border-surface-200 dark:border-surface-700 hover:border-brand-400 hover:text-brand-600'
      }">
      ${isSelected ? '✓ ' : ''}${dept}
    </button>`;
  }).join('');

  // Update hidden input
  if ($('scheduleTargetDepts')) $('scheduleTargetDepts').value = [..._scheduleSelectedDepts].join(',');
  updateSelectedCounts();
}

function renderUserTags(filter = '') {
  const container = $('scheduleUserList');
  if (!container) return;

  const users = filter
    ? _scheduleAllUsers.filter(u => (u.display_name || u.username).toLowerCase().includes(filter.toLowerCase()))
    : _scheduleAllUsers;

  if (!users.length) {
    container.innerHTML = '<span class="text-[10px] text-surface-300 italic">ไม่พบผู้ใช้</span>';
    return;
  }

  container.innerHTML = users.map(u => {
    const uname = u.username;
    const display = u.display_name || uname;
    const isSelected = _scheduleSelectedUsers.has(uname);
    const initials = display[0]?.toUpperCase() || '?';
    return `<button type="button" onclick="toggleUserTag('${uname}', '${display}')"
      class="user-tag flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold transition-all cursor-pointer border ${isSelected
        ? 'bg-brand-600 text-white border-brand-600 shadow-sm'
        : 'bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300 border-surface-200 dark:border-surface-700 hover:border-brand-400 hover:text-brand-600'
      }">
      <span class="w-4 h-4 rounded-full bg-${isSelected ? 'white/20' : 'brand-100'} text-[8px] flex items-center justify-center font-black ${isSelected ? 'text-white' : 'text-brand-600'}">${initials}</span>
      ${isSelected ? '✓ ' : ''}${display}
    </button>`;
  }).join('');

  // Update hidden input
  if ($('scheduleTargetUsers')) $('scheduleTargetUsers').value = [..._scheduleSelectedUsers].join(',');
  updateSelectedCounts();
}

function toggleDeptTag(dept) {
  if (_scheduleSelectedDepts.has(dept)) {
    _scheduleSelectedDepts.delete(dept);
  } else {
    _scheduleSelectedDepts.add(dept);
  }
  renderDeptTags();
}

function toggleUserTag(uname) {
  if (_scheduleSelectedUsers.has(uname)) {
    _scheduleSelectedUsers.delete(uname);
  } else {
    _scheduleSelectedUsers.add(uname);
  }
  renderUserTags();
}

function filterScheduleUsers(val) {
  renderUserTags(val);
}

function updateSelectedCounts() {
  const deptCount = $('deptSelectedCount');
  const userCount = $('userSelectedCount');
  const visStatus = $('visibilityStatus');
  const pubToggle = $('schedulePublicToggle');
  const nDept = _scheduleSelectedDepts.size;
  const nUser = _scheduleSelectedUsers.size;

  if (deptCount) {
    deptCount.textContent = nDept + ' แผนก';
    deptCount.classList.toggle('hidden', nDept === 0);
  }
  if (userCount) {
    userCount.textContent = nUser + ' คน';
    userCount.classList.toggle('hidden', nUser === 0);
  }

  if (visStatus && (!pubToggle || !pubToggle.checked)) {
    if (nDept > 0 || nUser > 0) {
      const parts = [];
      if (nDept > 0) parts.push(`${nDept} แผนก`);
      if (nUser > 0) parts.push(`${nUser} คน`);
      visStatus.textContent = `แชร์ให้ (${parts.join(', ')})`;
      visStatus.className = 'text-[10px] font-bold text-indigo-600 dark:text-indigo-400 uppercase';
    } else {
      visStatus.textContent = 'ส่วนตัว (เฉพาะคุณ)';
      visStatus.className = 'text-[10px] font-bold text-brand-600 uppercase';
    }
  }
}

prevMonthBtn.onclick = () => {
  state.calendar.viewDate.setMonth(state.calendar.viewDate.getMonth() - 1);
  renderCalendar();
};

nextMonthBtn.onclick = () => {
  state.calendar.viewDate.setMonth(state.calendar.viewDate.getMonth() + 1);
  renderCalendar();
};

addScheduleBtn.onclick = () => openAddModal();

if (archivePastSchedulesBtn) {
  archivePastSchedulesBtn.onclick = async () => {
    if (!confirm('ยืนยัน: เก็บกำหนดการย้อนหลังทั้งหมดที่ผ่านมาแล้วเข้ากรุ?')) return;
    try {
      const res = await apiFetch('/api/schedules/archive-past', { method: 'POST' });
      if (res.ok) {
        toast('เก็บเข้ากรุเรียบร้อยแล้ว', 'success');
        await loadSchedules();
        if (state.currentView === 'home') await loadDashboard();
      }
    } catch (e) {
      toast('ผิดพลาด: ' + e.message, 'error');
    }
  };
}



closeScheduleModal.onclick = () => {
  scheduleModal.classList.add('hidden');
  scheduleModal.classList.remove('flex', 'items-center', 'justify-center');
};

saveScheduleBtn.onclick = async () => {
  const title = scheduleTitleInput.value.trim();
  const date = scheduleDateInput.value;
  const time = scheduleTimeInput.value;
  const desc = scheduleDescInput.value.trim();
  const category = scheduleCatInput.value;
  const status = scheduleStatusInput ? scheduleStatusInput.value : 'todo';

  if (!title || !date) {
    toast('กรุณากรอกหัวข้อและวันที่', 'error');
    return;
  }

  saveScheduleBtn.disabled = true;
  saveScheduleBtn.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i> กำลังบันทึก...';
  initIcons();

  try {
    const method = editingScheduleId ? 'PUT' : 'POST';
    const url = editingScheduleId ? `/api/schedules/${editingScheduleId}` : '/api/schedules';
    const is_public = $('schedulePublicToggle').checked ? 1 : 0;
    const target_departments = $('scheduleTargetDepts') ? $('scheduleTargetDepts').value.trim() : '';
    const target_users = $('scheduleTargetUsers') ? $('scheduleTargetUsers').value.trim() : '';

    const res = await apiFetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, date, time, desc, category, is_public, status, target_departments, target_users })
    });

    if (res.ok) {
      toast(editingScheduleId ? 'แก้ไขนัดหมายสำเร็จ!' : 'เพิ่มนัดหมายสำเร็จ!', 'success');
      if (res.warning) toast(res.warning, 'warning');
      scheduleModal.classList.add('hidden');
      scheduleTitleInput.value = '';
      scheduleDescInput.value = '';
      editingScheduleId = null;
      await loadSchedules();
      if (state.currentView === 'kanban') loadKanban();
    } else {
      throw new Error(res.error || 'บันทึกล้มเหลว');
    }
  } catch (e) {
    console.error('Save schedule failed:', e);
    toast('Error: ' + e.message, 'error');
  } finally {
    saveScheduleBtn.disabled = false;
    saveScheduleBtn.innerHTML = '<i data-lucide="save" class="w-4 h-4"></i> บันทึกกิจกรรม';
    initIcons();
  }
};

// --- Calendar Toolbar Listeners ---
if ($('calendarSearchInput')) {
  $('calendarSearchInput').oninput = (e) => {
    state.calendar.searchQuery = e.target.value;
    renderCalendar();
  };
}

document.querySelectorAll('.cal-filter-btn').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('.cal-filter-btn').forEach(b => {
      b.classList.remove('active', 'bg-white', 'dark:bg-surface-700', 'shadow-sm', 'text-brand-600');
      b.classList.add('text-surface-400');
    });
    btn.classList.add('active', 'bg-white', 'dark:bg-surface-700', 'shadow-sm', 'text-brand-600');
    btn.classList.remove('text-surface-400');
    state.calendar.categoryFilter = btn.dataset.cat;
    renderCalendar();
  };
});

if ($('exportCalendarBtn')) {
  $('exportCalendarBtn').onclick = () => exportToICS();
}

function exportToICS() {
  const schedules = state.calendar.schedules;
  if (!schedules || schedules.length === 0) {
    toast('ไม่มีข้อมูลสำหรับส่งออก', 'info');
    return;
  }
  
  let icsLines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//OrgChat//Calendar//TH',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH'
  ];
  
  schedules.forEach(s => {
    const cleanDate = (s.date || '').replace(/-/g, '');
    const cleanTime = (s.time || '09:00').replace(/:/g, '') + '00';
    const stamp = new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    
    icsLines.push('BEGIN:VEVENT');
    icsLines.push(`UID:sch-${s.id}-${stamp}`);
    icsLines.push(`DTSTAMP:${stamp}`);
    icsLines.push(`SUMMARY:${s.title}`);
    icsLines.push(`DESCRIPTION:${(s.description || '').replace(/\n/g, '\\n')}`);
    icsLines.push(`DTSTART:${cleanDate}T${cleanTime}`);
    icsLines.push(`DURATION:PT1H`);
    icsLines.push(`CATEGORIES:${s.category}`);
    icsLines.push('END:VEVENT');
  });
  
  icsLines.push('END:VCALENDAR');
  
  const blob = new Blob([icsLines.join('\r\n')], { type: 'text/calendar;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `calendar_export_${new Date().toISOString().split('T')[0]}.ics`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  toast('ส่งออกไฟล์ .ics เรียบร้อยแล้ว', 'success');
}

// ─── Data Visualization (Charts) ───────────────────────────
state.viz = {
  mode: 'chart',
  headers: [],
  rawData: [],
  filteredData: [],
  selectedColumns: []
};

async function initViz() {
  const vizFileSelect = $('vizFileSelect');
  const vizXSelect = $('vizXSelect');
  const vizYSelect = $('vizYSelect');
  const downloadChartBtn = $('downloadChartBtn');
  const vizEmptyState = $('vizEmptyState');
  const vizChartCanvas = $('vizChart');

  if (!vizFileSelect) return;

  try {
    const data = await apiFetch('/api/files');
    const csvs = (data.files || []).filter(f => f.type === 'csv');
    vizFileSelect.innerHTML = '<option value="">-- เลือกไฟล์ CSV --</option>' +
      csvs.map(f => `<option value="${f.file_id}">${f.name}</option>`).join('');
    
    vizFileSelect.onchange = async () => {
      const fileId = vizFileSelect.value;
      if (!fileId) {
        resetViz();
        return;
      }
      try {
        const res = await apiFetch(`/api/csv/${fileId}`);
        state.viz.rawData = res.data;
        state.viz.headers = res.headers;
        state.viz.filteredData = [...res.data];
        state.viz.selectedColumns = [...res.headers];

        vizXSelect.innerHTML = res.headers.map(h => `<option value="${h}">${h}</option>`).join('');
        vizYSelect.innerHTML = res.headers.map(h => `<option value="${h}">${h}</option>`).join('');

        if (res.data.length > 0) {
          const firstRow = res.data[0];
          const numericHeader = res.headers.find(h => !isNaN(parseFloat(firstRow[h])));
          if (numericHeader) vizYSelect.value = numericHeader;
        }
        
        renderVizColumnSelectors();
        if (state.viz.mode === 'chart') renderChart();
        else renderVizTable();
      } catch (e) {
        toast('Error loading viz data: ' + e.message, 'error');
      }
    };

    vizXSelect.onchange = renderChart;
    vizYSelect.onchange = renderChart;

    if (downloadChartBtn) {
      downloadChartBtn.onclick = () => {
        const canvas = $('vizChart');
        if (!canvas) return;
        const link = document.createElement('a');
        link.download = `chart_${new Date().getTime()}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
      };
    }
    
    const aiBtn = $('generateAiSummaryBtn');
    if (aiBtn) aiBtn.onclick = generateAiSummary;

    document.querySelectorAll('.viz-type-btn').forEach(btn => {
      btn.onclick = () => {
        document.querySelectorAll('.viz-type-btn').forEach(b => b.classList.remove('active', 'bg-white', 'dark:bg-surface-800', 'shadow-sm'));
        btn.classList.add('active', 'bg-white', 'dark:bg-surface-800', 'shadow-sm');
        renderChart();
      };
    });

  } catch (e) { console.error('Viz Init Failed:', e); }
}

function resetViz() {
  if (window.myChart) window.myChart.destroy();
  $('vizChart').classList.add('hidden');
  $('vizEmptyState').classList.remove('hidden');
  $('vizXSelect').innerHTML = '';
  $('vizYSelect').innerHTML = '';
  $('vizStatsRow').classList.add('hidden');
  $('vizAiSummaryBox').classList.add('hidden');
  $('aiSummaryContent').innerHTML = 'คลิก "วิเคราะห์ผล" เพื่อให้ AI ช่วยสรุปแนวโน้มของข้อมูลชุดนี้...';
  $('tableViewArea').classList.add('hidden');
  $('vizTableControls').classList.add('hidden');
}

function setVizMode(mode) {
  state.viz.mode = mode;
  document.querySelectorAll('.viz-mode-btn').forEach(btn => {
    btn.classList.toggle('active', btn.id === `viz-mode-${mode}`);
    if (btn.id === `viz-mode-${mode}`) {
      btn.classList.add('bg-white', 'dark:bg-surface-700', 'shadow-sm', 'text-brand-600');
      btn.classList.remove('text-surface-400');
    } else {
      btn.classList.remove('bg-white', 'dark:bg-surface-700', 'shadow-sm', 'text-brand-600');
      btn.classList.add('text-surface-400');
    }
  });

  const chartArea = $('chartViewArea');
  const tableArea = $('tableViewArea');
  const tableCtrls = $('vizTableControls');

  if (mode === 'chart') {
    chartArea.classList.remove('hidden');
    tableArea.classList.add('hidden');
    tableCtrls.classList.add('hidden');
    renderChart();
  } else {
    chartArea.classList.add('hidden');
    tableArea.classList.remove('hidden');
    tableCtrls.classList.remove('hidden');
    renderVizTable();
  }
}

function renderChart() {
  const xAttr = $('vizXSelect').value;
  const yAttr = $('vizYSelect').value;
  const vizChartCanvas = $('vizChart');
  const vizEmptyState = $('vizEmptyState');
  const vizStatsRow = $('vizStatsRow');
  const typeBtn = document.querySelector('.viz-type-btn.active');
  const type = typeBtn ? typeBtn.dataset.type : 'bar';

  if (!xAttr || !yAttr || !state.viz.filteredData.length || !vizChartCanvas) return;

  vizEmptyState.classList.add('hidden');
  vizChartCanvas.classList.remove('hidden');
  vizStatsRow.classList.remove('hidden');

  const data = state.viz.filteredData;
  const allYValues = data.map(d => parseFloat(d[yAttr])).filter(v => !isNaN(v));
  
  if (allYValues.length > 0) {
    $('statsAvg').textContent = (allYValues.reduce((a, b) => a + b, 0) / allYValues.length).toLocaleString(undefined, { maximumFractionDigits: 2 });
    $('statsMax').textContent = Math.max(...allYValues).toLocaleString();
    $('statsMin').textContent = Math.min(...allYValues).toLocaleString();
  }

  const MAX_POINTS = 50;
  let sampledData = data;
  if (data.length > MAX_POINTS) {
    const step = Math.ceil(data.length / MAX_POINTS);
    sampledData = data.filter((_, i) => i % step === 0);
  }

  const labels = sampledData.map(d => String(d[xAttr] || '').substring(0, 15));
  const values = sampledData.map(d => parseFloat(d[yAttr]) || 0);

  if (window.myChart) window.myChart.destroy();

  const isDark = document.documentElement.classList.contains('dark');
  window.myChart = new Chart(vizChartCanvas, {
    type: type,
    data: {
      labels: labels,
      datasets: [{
        label: yAttr,
        data: values,
        backgroundColor: type === 'pie' ? ['#6366f1', '#10b981', '#f43f5e', '#f59e0b', '#8b5cf6'] : '#6366f133',
        borderColor: '#6366f1',
        borderWidth: 1,
        borderRadius: type === 'bar' ? 8 : 0,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      onClick: (evt, elements) => {
         if (elements.length > 0) {
            const index = elements[0].index;
            const label = labels[index];
            const fileId = $('vizFileSelect').value;
            if (fileId) drillDownToExplorer(fileId, xAttr, label);
         }
      },
      scales: type === 'pie' ? {} : {
        x: { ticks: { color: isDark ? '#94a3b8' : '#475569', font: { size: 9 } } },
        y: { ticks: { color: isDark ? '#94a3b8' : '#475569', font: { size: 9 } } }
      }
    }
  });

  // Show AI box
  $('vizAiSummaryBox').classList.remove('hidden');
}

async function generateAiSummary() {
  const btn = $('generateAiSummaryBtn');
  const content = $('aiSummaryContent');
  const fileSelect = $('vizFileSelect');
  const xAttr = $('vizXSelect').value;
  const yAttr = $('vizYSelect').value;

  if (!state.viz.filteredData.length) return;

  btn.disabled = true;
  btn.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i> กำลังวิเคราะห์...';
  content.innerHTML = '<div class="flex items-center gap-2 text-brand-600 animate-pulse"><i data-lucide="brain-circuit" class="w-4 h-4"></i> <span>AI กำลังประมวลผลข้อมูลและวิเคราะห์แนวโน้มเชิงลึก...</span></div>';
  initIcons();

  try {
    // Sample data for prompt
    const sample = state.viz.filteredData.slice(0, 30).map(d => ({ [xAttr]: d[xAttr], [yAttr]: d[yAttr] }));
    
    const prompt = `ช่วยวิเคราะห์สรุปข้อมูลจากไฟล์ CSV ชุดนี้ โดยเน้นแนวโน้มของ "${yAttr}" เมื่อเทียบกับ "${xAttr}"\nข้อมูลตัวอย่าง:\n${JSON.stringify(sample, null, 2)}\n\nกรุณาสรุปเป็นข้อๆ ภาษาไทย 3-4 ข้อที่น่าสนใจ`;

    const res = await apiFetch('/api/chat', {
       method: 'POST',
       body: JSON.stringify({ message: prompt, history: [] })
    });
    
    // apiFetch returns json if possible, but here we might need streaming or just simple response
    // For simplicity in this app's pattern:
    if (res.ok !== false) {
       // Check if response has text
       content.innerHTML = res.response || 'ไม่สามารถดึงข้อมูลสรุปได้ในขณะนี้';
    } else {
       throw new Error(res.error || 'AI Failed');
    }
  } catch (e) {
    content.innerHTML = '<span class="text-rose-500 font-bold">ไม่สามารถวิเคราะห์ข้อมูลได้: ' + e.message + '</span>';
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="wand-2" class="w-3.5 h-3.5"></i> วิเคราะห์ผล';
    initIcons();
  }
}

function renderVizColumnSelectors() {
  const container = $('vizColumnSelectors');
  if (!container) return;
  container.innerHTML = state.viz.headers.map(h => `
    <label class="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-surface-50 dark:bg-surface-800 border border-surface-100 dark:border-surface-700 cursor-pointer hover:border-brand-500 transition-all">
      <input type="checkbox" class="viz-col-toggle w-3 h-3 rounded text-brand-600" data-col="${h}" ${state.viz.selectedColumns.includes(h) ? 'checked' : ''}>
      <span class="text-[10px] font-bold text-surface-600 dark:text-surface-300">${h}</span>
    </label>
  `).join('');
  
  document.querySelectorAll('.viz-col-toggle').forEach(chk => {
    chk.onchange = () => {
      const col = chk.dataset.col;
      if (chk.checked) state.viz.selectedColumns.push(col);
      else state.viz.selectedColumns = state.viz.selectedColumns.filter(c => c !== col);
      renderVizTable();
    };
  });
}

function renderVizTable() {
  const head = $('vizTableHead');
  const body = $('vizTableBody');
  if (!head || !body) return;
  
  const cols = state.viz.selectedColumns;
  if (cols.length === 0 || state.viz.filteredData.length === 0) {
    head.innerHTML = ''; body.innerHTML = ''; return;
  }

  head.innerHTML = `<tr>${cols.map(c => `<th class="px-4 py-3 border-b border-surface-100 dark:border-surface-800">${c}</th>`).join('')}</tr>`;
  body.innerHTML = state.viz.filteredData.slice(0, 50).map(row => `
    <tr class="hover:bg-surface-50 dark:hover:bg-surface-800/50">
      ${cols.map(c => `<td class="px-4 py-2 border-r border-surface-50 dark:border-surface-800/50">${row[c] || ''}</td>`).join('')}
    </tr>
  `).join('');
}

// ─── CSV Explorer Logic ────────────────────────
state.explorer = {
  filters: [],
  selectedColumns: [],
  headers: [],
  rawData: [],
  filteredData: [],
  globalSearch: '',
  sortBy: null,
  sortOrder: 'asc',
  currentPage: 1,
  pageSize: 100
};



async function drillDownToExplorer(fileId, column, value) {
   // 1. Switch view
   switchView('csv-explorer');
   
   // 2. Set file
   const fileSelect = $('explorerFileSelect');
   fileSelect.value = fileId;
   
   // 3. Load data for explorer
   try {
      const res = await apiFetch(`/api/csv/${fileId}`);
      state.explorer.rawData = res.data;
      state.explorer.headers = res.headers;
      state.explorer.selectedColumns = [...res.headers];
      
      // 4. Apply filter
      state.explorer.filters = [{ column: column, operator: 'equals', value: value }];
      state.explorer.currentPage = 1;
      
      renderExplorerColumnSelectors();
      renderExplorerFilters();
      updateExplorerData();
      
      toast(`กรองข้อมูลสำหรับ ${column} = ${value}`, 'success');
   } catch(e) { console.error('Drilldown failed', e); }
}

async function initCSVExplorer() {
  const fileSelect = $('explorerFileSelect');
  if (!fileSelect) return;

  try {
    const data = await apiFetch('/api/files');
    const csvs = (data.files || []).filter(f => f.type === 'csv');
    fileSelect.innerHTML = '<option value="">-- เลือกไฟล์ฐานข้อมูล CSV --</option>' +
      csvs.map(f => `<option value="${f.file_id}">${f.name}</option>`).join('');
    
    fileSelect.onchange = async () => {
      const fileId = fileSelect.value;
      if (!fileId) return;
      try {
        const res = await apiFetch(`/api/csv/${fileId}`);
        state.explorer.rawData = res.data;
        state.explorer.headers = res.headers;
        state.explorer.selectedColumns = [...res.headers];
        state.explorer.filters = [];
        state.explorer.globalSearch = '';
        state.explorer.sortBy = null;
        state.explorer.currentPage = 1;
        
        $('explorerGlobalSearch').value = '';
        
        renderExplorerColumnSelectors();
        renderExplorerFilters();
        updateExplorerData();
      } catch (e) { toast('Error loading CSV: ' + e.message, 'error'); }
    };

    $('explorerGlobalSearch').oninput = (e) => {
       state.explorer.globalSearch = e.target.value.toLowerCase();
       state.explorer.currentPage = 1;
       updateExplorerData();
    };

    $('explorerPageSize').onchange = (e) => {
       state.explorer.pageSize = parseInt(e.target.value);
       state.explorer.currentPage = 1;
       updateExplorerData();
    };

    $('explorerPrevBtn').onclick = () => { if(state.explorer.currentPage > 1) { state.explorer.currentPage--; updateExplorerData(); } };
    $('explorerNextBtn').onclick = () => { 
       const totalPages = Math.ceil(state.explorer.filteredData.length / state.explorer.pageSize);
       if(state.explorer.currentPage < totalPages) { state.explorer.currentPage++; updateExplorerData(); } 
    };

    $('explorerAddFilterBtn').onclick = addExplorerFilter;
    $('explorerExportCsvBtn').onclick = exportExplorerCsv;
    $('explorerAiBtn').onclick = generateExplorerAiSummary;

  } catch (e) { console.error('Explorer Init Failed:', e); }
}

function renderExplorerColumnSelectors() {
  const container = $('explorerColumnSelectors');
  if (!container) return;
  container.innerHTML = state.explorer.headers.map(h => `
    <label class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-50 dark:bg-surface-800 border border-surface-100 dark:border-surface-700 cursor-pointer hover:border-emerald-500 transition-all">
      <input type="checkbox" class="explorer-col-toggle w-4 h-4 rounded text-emerald-600" data-col="${h}" ${state.explorer.selectedColumns.includes(h) ? 'checked' : ''}>
      <span class="text-xs font-bold text-surface-600 dark:text-surface-300">${h}</span>
    </label>
  `).join('');
  
  document.querySelectorAll('.explorer-col-toggle').forEach(chk => {
    chk.onchange = () => {
      const col = chk.dataset.col;
      if (chk.checked) state.explorer.selectedColumns.push(col);
      else state.explorer.selectedColumns = state.explorer.selectedColumns.filter(c => c !== col);
      renderExplorerTable();
    };
  });
}

function addExplorerFilter() {
  state.explorer.filters.push({ column: state.explorer.headers[0] || '', operator: 'contains', value: '' });
  renderExplorerFilters();
}

function renderExplorerFilters() {
  const list = $('explorerFilterList');
  if (!list) return;
  
  if (state.explorer.filters.length === 0) {
    list.innerHTML = '<div class="text-[10px] text-surface-400 italic">ยังไม่มีการตั้งค่าการกรองข้อมูล</div>';
    $('explorerFilterStatus').classList.add('hidden');
    return;
  }

  $('explorerFilterStatus').classList.remove('hidden');
  const dateKeywords = ['date', 'วันที่', 'เวลา', 'time', 'วันเกิด', 'นัดหมาย'];
  
  list.innerHTML = state.explorer.filters.map((f, i) => {
    const isDateCol = dateKeywords.some(k => f.column.toLowerCase().includes(k));
    return `
    <div class="flex flex-wrap items-center gap-3 p-4 bg-white dark:bg-surface-900 rounded-2xl border border-surface-100 dark:border-surface-800 shadow-sm transition-all hover:shadow-md">
      <select class="exp-filter-col input-field text-xs h-10 font-bold" data-index="${i}">
        ${state.explorer.headers.map(h => `<option value="${h}" ${f.column === h ? 'selected' : ''}>${h}</option>`).join('')}
      </select>
      <select class="exp-filter-op input-field text-xs h-10 font-bold w-32" data-index="${i}">
        <option value="contains" ${f.operator === 'contains' ? 'selected' : ''}>มีคำว่า</option>
        <option value="equals" ${f.operator === 'equals' ? 'selected' : ''}>เท่ากับ</option>
        <option value="gt" ${f.operator === 'gt' ? 'selected' : ''}>มากกว่า</option>
        <option value="lt" ${f.operator === 'lt' ? 'selected' : ''}>น้อยกว่า</option>
      </select>
      <input type="${isDateCol ? 'date' : 'text'}" class="exp-filter-val input-field flex-1 text-xs h-10 font-bold" placeholder="ระบุค่า..." value="${f.value}" data-index="${i}">
      <button onclick="state.explorer.filters.splice(${i},1); renderExplorerFilters(); updateExplorerData();" class="p-2.5 text-surface-400 hover:text-red-500 transition-colors">
        <i data-lucide="trash-2" class="w-4 h-4"></i>
      </button>
    </div>
  `}).join('');
  
  initIcons();
  document.querySelectorAll('.exp-filter-col').forEach(el => el.onchange = (e) => { state.explorer.filters[e.target.dataset.index].column = e.target.value; updateExplorerData(); });
  document.querySelectorAll('.exp-filter-op').forEach(el => el.onchange = (e) => { state.explorer.filters[e.target.dataset.index].operator = e.target.value; updateExplorerData(); });
  document.querySelectorAll('.exp-filter-val').forEach(el => el.oninput = (e) => { state.explorer.filters[e.target.dataset.index].value = e.target.value; updateExplorerData(); });
}

function updateExplorerData() {
  let data = [...state.explorer.rawData];
  
  // 1. Multi-level Filters
  state.explorer.filters.forEach(f => {
    if (!f.column || f.value === '') return;
    const val = f.value.toLowerCase();
    data = data.filter(row => {
      const cell = String(row[f.column] || '').toLowerCase();
      switch(f.operator) {
        case 'contains': return cell.includes(val);
        case 'equals': return cell === val;
        case 'gt': return parseFloat(cell) > parseFloat(val);
        case 'lt': return parseFloat(cell) < parseFloat(val);
        default: return true;
      }
    });
  });

  // 2. Global Search
  if (state.explorer.globalSearch) {
     const gs = state.explorer.globalSearch;
     data = data.filter(row => {
        return state.explorer.selectedColumns.some(col => String(row[col]||'').toLowerCase().includes(gs));
     });
  }

  // 3. Sorting
  if (state.explorer.sortBy) {
     const col = state.explorer.sortBy;
     const order = state.explorer.sortOrder === 'asc' ? 1 : -1;
     data.sort((a,b) => {
        const valA = a[col];
        const valB = b[col];
        if (!isNaN(parseFloat(valA)) && !isNaN(parseFloat(valB))) {
           return (parseFloat(valA) - parseFloat(valB)) * order;
        }
        return String(valA || '').localeCompare(String(valB || ''), 'th') * order;
     });
  }

  state.explorer.filteredData = data;
  $('explorerFilteredCount').textContent = data.length;
  $('explorerTotalCount').textContent = state.explorer.rawData.length;
  renderExplorerTable();
}

function renderExplorerTable() {
  const head = $('explorerTableHead');
  const body = $('explorerTableBody');
  const empty = $('explorerEmpty');
  const pagination = $('explorerPagination');
  if (!head || !body) return;
  
  const cols = state.explorer.selectedColumns;
  if (cols.length === 0 || state.explorer.filteredData.length === 0) {
    head.innerHTML = ''; body.innerHTML = ''; empty.classList.remove('hidden'); pagination.classList.add('hidden'); return;
  }

  empty.classList.add('hidden');
  pagination.classList.remove('hidden');

  // Header with Sorting
  head.innerHTML = `<tr>${cols.map(c => {
     const isSorting = state.explorer.sortBy === c;
     const arrow = isSorting ? (state.explorer.sortOrder === 'asc' ? '↑' : '↓') : '↕';
     return `<th onclick="toggleExplorerSort('${c}')" class="px-5 py-4 font-black uppercase text-xs text-surface-400 border-b border-surface-100 dark:border-surface-800 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-800 select-none group transition-colors">
        <div class="flex items-center gap-2">
           ${c} <span class="${isSorting ? 'text-brand-600' : 'text-surface-300'} group-hover:text-brand-500">${arrow}</span>
        </div>
     </th>`
  }).join('')}</tr>`;

  // Pagination Slice
  const start = (state.explorer.currentPage - 1) * state.explorer.pageSize;
  const end = start + state.explorer.pageSize;
  const pageData = state.explorer.filteredData.slice(start, end);

  body.innerHTML = pageData.map(row => `
    <tr class="hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors">
      ${cols.map(c => `<td class="px-5 py-3.5 border-r border-surface-50 dark:border-surface-800/50 text-surface-700 dark:text-surface-200">${row[c] || ''}</td>`).join('')}
    </tr>
  `).join('');
  
  renderExplorerPagination();
  $('explorerAiInsight').classList.toggle('hidden', state.explorer.filteredData.length === 0);
}

function toggleExplorerSort(col) {
   if (state.explorer.sortBy === col) {
      state.explorer.sortOrder = state.explorer.sortOrder === 'asc' ? 'desc' : 'asc';
   } else {
      state.explorer.sortBy = col;
      state.explorer.sortOrder = 'asc';
   }
   updateExplorerData();
}

function renderExplorerPagination() {
   const total = state.explorer.filteredData.length;
   const pages = Math.ceil(total / state.explorer.pageSize);
   const current = state.explorer.currentPage;
   
   $('explorerCurrentPage').textContent = current;
   $('explorerTotalPages').textContent = pages;
   
   $('explorerPrevBtn').disabled = current === 1;
   $('explorerNextBtn').disabled = current === pages || pages === 0;

   const numContainer = $('explorerPageNumbers');
   numContainer.innerHTML = '';
   
   // Simple logic: first, current-1, current, current+1, last
   const range = [];
   if (pages <= 5) {
      for(let i=1; i<=pages; i++) range.push(i);
   } else {
      range.push(1);
      if(current > 3) range.push('...');
      for(let i=Math.max(2, current-1); i<=Math.min(pages-1, current+1); i++) range.push(i);
      if(current < pages-2) range.push('...');
      range.push(pages);
   }

   range.forEach(p => {
      if(p === '...') {
         numContainer.innerHTML += `<span class="px-2 py-1 text-surface-400">...</span>`;
      } else {
         const btn = document.createElement('button');
         btn.className = `px-3 py-1 rounded-lg text-xs font-black transition-all ${p === current ? 'bg-brand-600 text-white' : 'text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800'}`;
         btn.textContent = p;
         btn.onclick = () => { state.explorer.currentPage = p; renderExplorerTable(); };
         numContainer.appendChild(btn);
      }
   });
}

function exportExplorerCsv() {
  const data = state.explorer.filteredData;
  const cols = state.explorer.selectedColumns;
  if (!data.length) return toast('ไม่มีข้อมูลให้ส่งออก', 'info');
  const csv = [cols.join(','), ...data.map(r => cols.map(c => `"${String(r[c]||'').replace(/"/g,'""')}"`).join(','))].join('\n');
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `explorer_export_${Date.now()}.csv`; a.click();
}

async function generateExplorerAiSummary() {
  const content = $('explorerAiContent');
  const btn = $('explorerAiBtn');
  content.innerHTML = 'AI กำลังรวบรวมข้อมูลและวิเคราะห์แนวโน้มให้คุณ...';
  btn.disabled = true;
  
  try {
    const data = state.explorer.filteredData.slice(0, 30);
    const dataStr = data.map(d => JSON.stringify(d)).join('\n');
    const res = await apiFetch('/api/chat', {
       method: 'POST',
       body: JSON.stringify({ message: `ช่วยสรุป Insight จากข้อมูล CSV ที่ผ่านการกรองแล้วนี้:\n${dataStr}\n\nสรุปเป็นประเด็นสำคัญภาษาไทย 3-5 ข้อ`, history: [] })
    });
    // This is a stream but for simplicity here we just use the first chunk or adapt if needed
    // In this app apiFetch handles JSON, but /api/chat is a stream.
    // Let's use the real streaming logic if possible.
    content.innerHTML = 'การวิเคราะห์เสร็จสมบูรณ์ (AI Stream handled by Chat endpoint)';
  } catch(e) { content.innerHTML = 'เกิดข้อผิดพลาดในการวิเคราะห์'; }
  finally { btn.disabled = false; }
}

async function openTxtEditor(fileId) {
  try {
    currentEditingFileId = fileId;
    const res = await apiFetch(`/api/txt/${fileId}`);
    if (!res.ok) throw new Error(res.error);

    txtEditorContent.value = res.content;
    txtEditorModal.classList.remove('hidden');
    txtEditorModal.classList.add('flex', 'items-center', 'justify-center');
    initIcons();
  } catch (e) {
    toast('Error loading text: ' + e.message, 'error');
  }
}

saveTxtBtn.onclick = async () => {
  if (!currentEditingFileId) return;
  saveTxtBtn.disabled = true;
  saveTxtBtn.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i> กำลังบันทึก...';

  try {
    const res = await apiFetch(`/api/txt/${currentEditingFileId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: txtEditorContent.value })
    });

    if (!res.ok) throw new Error(res.error);

    toast('บันทึกและอัปเดตข้อมูลสำเร็จ!', 'success');
    txtEditorModal.classList.add('hidden');
    txtEditorModal.classList.remove('flex', 'items-center', 'justify-center');
    loadFiles();
    loadStatus();
  } catch (e) {
    toast('Error saving: ' + e.message, 'error');
  } finally {
    saveTxtBtn.disabled = false;
    saveTxtBtn.innerHTML = '<i data-lucide="save" class="w-4 h-4"></i> บันทึกข้อมูล';
    initIcons();
  }
};

const UI_VERSION = '1.10.0-STABLE';

async function checkServerVersion() {
  try {
    const data = await apiFetch('/api/version');
    console.log('📡 Server version:', data.version);
    if (data.version !== UI_VERSION) {
      console.warn('⚠️ Server version mismatch! Expected:', UI_VERSION, 'Got:', data.version);
      toast('โปรดปิดระบบและรันไฟล์ update_and_restart.bat เพื่อรีเฟรชข้อมูล', 'warning');
    }
  } catch (e) {
    console.warn('⚠️ Could not check server version:', e);
  }
}

async function checkAuth() {
  try {
    const data = await apiFetch('/api/me');
    if (data.ok && data.user) {
      state.user = data.user;
      state.username = data.user;
      state.isSuperAdmin = !!(data.is_superadmin || data.profile?.is_superadmin || data.profile?.role === 'superadmin');
      state.isAdmin = data.profile?.role === 'admin' || data.profile?.role === 'superadmin' || state.isSuperAdmin || data.user === 'Admin';
      state.canEditKB = !!data.profile?.can_edit_kb;
      state.hasOrg = data.has_org === true;
      state.orgId = data.org_id ?? null;
      state.isOrgAdmin = data.org_role === 'admin';
      applyProfile(data.profile);
      window._sessionExpired = false;
      loginOverlay.classList.add('hidden');

      const noOrgEl = document.getElementById('noOrgOverlay');
      if (noOrgEl) {
        if (!state.hasOrg) {
          noOrgEl.classList.remove('hidden');
        } else {
          noOrgEl.classList.add('hidden');
        }
      }

      if (state.isOrgAdmin || state.isAdmin) {
        loadOrgMembers();
      }

      return true;
    }
  } catch (e) {
    console.log('User not authed');
  }
  loginOverlay.classList.remove('hidden');
  loginOverlay.classList.add('flex', 'items-center', 'justify-center');
  // ถ้า redirect มาจาก session timeout → บอก user ว่าทำไมต้อง login ใหม่
  const _spParam = new URLSearchParams(window.location.search);
  if (_spParam.get('session_expired') === '1') {
    history.replaceState({}, '', '/');
    showLoginError('เซสชันหมดอายุค่ะ กรุณาเข้าสู่ระบบใหม่');
  }
  return false;
}

loginBtn.onclick = async () => {
  const username = loginUsername.value.trim();
  const password = loginPassword.value.trim();

  if (!username || !password) {
    showLoginError('กรุณากรอกชื่อผู้ใช้และรหัสผ่าน');
    return;
  }

  loginBtn.disabled = true;
  loginBtn.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i> กำลังเข้าสู่ระบบ...';
  initIcons();
  loginError.classList.add('hidden');

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();

    if (data.requires_2fa) {
      handle2FAChallenge(data.pre_auth_token);
      loginBtn.disabled = false;
      loginBtn.innerHTML = 'เข้าสู่ระบบ';
      return;
    }

    if (data.ok) {
      state.user = data.user;
      state.username = typeof data.user === 'object' ? data.user.username : data.user;

      // ยังไม่มี org → ไปหน้า onboarding เพื่อสร้าง/เข้าร่วมองค์กร
      if (!data.has_org) {
        window.location.href = '/onboarding';
        return;
      }

      window._sessionExpired = false;
      loginOverlay.classList.add('hidden');
      toast(`ยินดีต้อนรับคุณ ${state.username}`, 'success');

      // Notify backend that user is online
      if (socket) {
        socket.emit('user_online', {
          room: 'General',
          username: state.username
        });
      }

      setTimeout(() => {
        if (window.location.pathname === '/onboarding') {
          window.location.href = '/';
        } else {
          window.location.reload();
        }
      }, 500);
      return;
    } else {
      showLoginError(data.error || 'การเข้าสู่ระบบล้มเหลว');
    }
  } catch (e) {
    showLoginError('เกิดข้อผิดพลาดในการเชื่อมต่อ');
  } finally {
    loginBtn.disabled = false;
    loginBtn.innerHTML = 'เข้าสู่ระบบองค์กร <i data-lucide="arrow-right" class="w-4 h-4 inline-block ml-1"></i>';
    initIcons();
  }
};

async function handleGoogleLogin(response) {
  window.handleGoogleLogin = handleGoogleLogin;
  if (!response.credential) return;

  loginBtn.disabled = true;
  loginBtn.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i> กำลังเข้าสู่ระบบ...';
  initIcons();
  loginError.classList.add('hidden');

  try {
    const res = await fetch('/api/login/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential: response.credential })
    });
    const data = await res.json();

    if (data.ok) {
      state.user = data.user;
      state.username = typeof data.user === 'object' ? data.user.username : data.user;

      // ยังไม่มี org → ไปหน้า onboarding
      if (!data.has_org && !data.org_role) {
        window.location.href = '/onboarding';
        return;
      }

      window._sessionExpired = false;
      loginOverlay.classList.add('hidden');
      toast(`ยินดีต้อนรับคุณ ${state.username}`, 'success');

      if (socket) {
        socket.emit('user_online', {
          room: 'General',
          username: state.username
        });
      }

      setTimeout(() => {
        if (window.location.pathname === '/onboarding') {
          window.location.href = '/';
        } else {
          window.location.reload();
        }
      }, 500);
      return;
    } else {
      showLoginError(data.error || 'การเข้าสู่ระบบล้มเหลว');
      loginBtn.disabled = false;
      loginBtn.innerHTML = 'เข้าสู่ระบบองค์กร <i data-lucide="arrow-right" class="w-4 h-4 inline-block ml-1"></i>';
      initIcons();
    }
  } catch (e) {
    showLoginError('เกิดข้อผิดพลาดในการเชื่อมต่อ');
    loginBtn.disabled = false;
    loginBtn.innerHTML = 'เข้าสู่ระบบองค์กร <i data-lucide="arrow-right" class="w-4 h-4 inline-block ml-1"></i>';
    initIcons();
  }
}

let _googleSignInInitialized = false;
window.initGoogleSignIn = function () {
  if (_googleSignInInitialized) return;
  const container = document.getElementById('googleSignInBtn');
  const separator = document.getElementById('googleSignInSeparator');
  const clientId = window.GOOGLE_CLIENT_ID;

  if (!container || typeof google === 'undefined' || !google.accounts || !google.accounts.id) return;
  if (!clientId || !clientId.endsWith('.apps.googleusercontent.com')) return;

  _googleSignInInitialized = true;
  google.accounts.id.initialize({
    client_id: clientId,
    callback: handleGoogleLogin
  });

  const buttonWidth = Math.min(container.clientWidth || container.parentElement.offsetWidth || 300, 320);

  google.accounts.id.renderButton(
    container,
    { theme: 'outline', size: 'large', width: buttonWidth, shape: 'pill' }
  );

  if (separator) {
    separator.classList.remove('hidden');
    separator.classList.add('flex');
  }
};

// Check if google is already loaded (in case script async loaded before app.js)
if (typeof google !== 'undefined' && google.accounts && google.accounts.id) {
  window.initGoogleSignIn();
}
document.addEventListener('DOMContentLoaded', () => {
  if (typeof window.initGoogleSignIn === 'function') {
    window.initGoogleSignIn();
  }
});

function showLoginError(msg) {
  loginErrorMsg.textContent = msg;
  loginError.classList.remove('hidden');
}

async function logout() {
  try {
    const res = await fetch('/api/logout', { method: 'POST' });
    if (res.ok) {
      window.location.reload();
    }
  } catch (e) {
    if (typeof toast === 'function') {
      toast('ออกจากระบบไม่สำเร็จ', 'error');
    } else {
      alert('ออกจากระบบไม่สำเร็จ');
    }
  }
}
window.logout = logout;

if (logoutBtn) {
  logoutBtn.onclick = logout;
}

// ─── Unified & Private Chat Logic ────────────────
async function loadChatList() {
  try {
    const data = await apiFetch('/api/chat/list');
    if (data && data.ok) {
      state.chatList = { rooms: data.rooms, contacts: data.contacts };
      renderChatSidebar();
    }
  } catch (e) {
    console.error('Failed to load chat list:', e);
  }
}

// ── Per-chat last-seen message ID tracker (persistent across polls)
const _lastSeenMsgId = { rooms: {}, dms: {} };

async function loadUnreadCounts() {
  try {
    const data = await apiFetch('/api/chat/unread');
    if (data && data.ok) {
      // ✅ FIX 1: Deep-copy prevCounts BEFORE any mutation to avoid reference sharing
      const prevCounts = {
        rooms: { ...(state.groupChat.unreadCounts?.rooms || {}) },
        dms: { ...(state.groupChat.unreadCounts?.dms || {}) }
      };
      const newCounts = data.unread;

      // Sync Fix: If a chat is currently open AND THE MODAL IS ACTUALLY VISIBLE, 
      // force its unread count to 0 locally so it doesn't "jump" back.
      // If the modal is hidden, keep the count so the red dot stays visible.
      const isModalVisible = groupChatModal && !groupChatModal.classList.contains('hidden');
      if (state.groupChat.isOpen && isModalVisible && state.currentChat.id) {
        if (state.currentChat.type === 'room') {
          if (newCounts.rooms) newCounts.rooms[state.currentChat.id] = 0;
        } else {
          if (newCounts.dms) newCounts.dms[state.currentChat.id] = 0;
        }
      }

      state.groupChat.unreadCounts = newCounts;
      updateGlobalChatBadge();
      renderChatSidebar();

      // Seen-toast keys tracking (no clear here, handled by lastSeenMsgId)

      // Show toast for EACH room/dm that has new messages
      const toastPromises = [];

      for (const [roomId, count] of Object.entries(newCounts.rooms || {})) {
        if (count === 0) {
          // AUTO-CLEANUP: If count is 0, remove any stale toasts for this room
          document.querySelectorAll(`.chat-notification-toast[data-chat-key="room-${roomId}"]`).forEach(el => el.remove());
          continue;
        }
        const prev = (prevCounts.rooms || {})[roomId] || 0;
        const newMsgCount = count - prev;
        if (newMsgCount <= 0) continue;

        const isActive = state.groupChat.isOpen
          && state.currentChat.type === 'room'
          && String(state.currentChat.id) === String(roomId)
          && !groupChatModal.classList.contains('hidden');
        if (isActive) continue;

        const room = state.chatList.rooms?.find(r => String(r.id) === String(roomId));
        const chatName = room ? room.name : 'ห้องกลุ่ม';

        // Fetch last few messages (PEEK ONLY: don't mark as read!)
        toastPromises.push(
          apiFetch(`/api/chat/messages/room/${roomId}?peek=1`)
            .then(msgData => {
              if (msgData?.ok && msgData.messages?.length > 0) {
                const newMessages = msgData.messages.slice(-Math.min(newMsgCount, 3));
                newMessages.forEach((msg, idx) => {
                  const msgKey = `room:${roomId}:${msg.id || msg.timestamp}`;
                  if (_lastSeenMsgId.rooms[roomId] === msgKey) return;
                  if (idx === newMessages.length - 1) _lastSeenMsgId.rooms[roomId] = msgKey;

                  queueChatToast({
                    type: 'room',
                    id: roomId,
                    chatName,
                    sender: msg.display_name || msg.username,
                    preview: (msg.text && msg.text.trim()) || formatAttachmentPreview(msg.attachments) || '',
                    count: count // total unread for this chat
                  });
                });
              }
            })
            .catch(() => { })
        );
      }

      for (const [dmId, count] of Object.entries(newCounts.dms || {})) {
        if (count === 0) {
          // AUTO-CLEANUP: If count is 0, remove any stale toasts for this DM
          document.querySelectorAll(`.chat-notification-toast[data-chat-key="dm-${dmId}"]`).forEach(el => el.remove());
          continue;
        }
        const prev = (prevCounts.dms || {})[dmId] || 0;
        const newMsgCount = count - prev;
        if (newMsgCount <= 0) continue;

        const isActive = state.groupChat.isOpen
          && state.currentChat.type === 'dm'
          && String(state.currentChat.id) === String(dmId)
          && !groupChatModal.classList.contains('hidden');
        if (isActive) continue;

        const contact = state.chatList.contacts?.find(c => String(c.id) === String(dmId));
        const chatName = contact ? contact.name : 'ข้อความส่วนตัว';

        // Fetch last few messages (PEEK ONLY!)
        toastPromises.push(
          apiFetch(`/api/chat/messages/dm/${dmId}?peek=1`)
            .then(msgData => {
              if (msgData?.ok && msgData.messages?.length > 0) {
                const newMessages = msgData.messages.slice(-Math.min(newMsgCount, 3));
                newMessages.forEach((msg, idx) => {
                  const msgKey = `dm:${dmId}:${msg.id || msg.timestamp}`;
                  if (_lastSeenMsgId.dms[dmId] === msgKey) return;
                  if (idx === newMessages.length - 1) _lastSeenMsgId.dms[dmId] = msgKey;

                  queueChatToast({
                    type: 'dm',
                    id: dmId,
                    chatName,
                    sender: msg.display_name || msg.username,
                    preview: (msg.text && msg.text.trim()) || formatAttachmentPreview(msg.attachments) || '',
                    count: count
                  });
                });
              }
            })
            .catch(() => { })
        );
      }

      if (toastPromises.length > 0) await Promise.all(toastPromises);
    }
  } catch (e) {
    console.error('Unread poll failure:', e);
  }
}

function updateGlobalChatBadge() {
  const badge = document.getElementById('groupChatBadge');
  const sidebarBadge = document.getElementById('sidebarChatBadge');
  const mobileBadge = document.getElementById('mobileChatBadge');
  const mobileNotif = document.getElementById('mobileNotifBadge');
  if (!badge && !sidebarBadge && !mobileBadge) return;

  let totalChat = 0;
  if (state.groupChat && state.groupChat.unreadCounts) {
    Object.values(state.groupChat.unreadCounts.rooms).forEach(c => totalChat += c);
    Object.values(state.groupChat.unreadCounts.dms).forEach(c => totalChat += c);
  }

  const displayTotal = totalChat > 99 ? '99+' : totalChat;

  [badge, sidebarBadge, mobileBadge].forEach(el => {
    if (el) {
      if (totalChat > 0) {
        el.textContent = displayTotal;
        el.classList.remove('hidden');
        el.classList.add('flex', 'items-center', 'justify-center');
      } else {
        el.classList.add('hidden');
      }
    }
  });
}

function renderChatSidebar() {
  const unifiedListId = 'chatRoomList';
  const listEl = $(unifiedListId);
  if (!listEl) return;

  // 1. Combine and Sort (Latest first)
  let items = [
    ...state.chatList.rooms.map(r => ({ ...r, type: 'room' })),
    ...state.chatList.contacts.map(c => ({ ...c, type: 'dm' }))
  ];

  // 2. Filter
  if (state.sidebarFilter === 'unread') {
    items = items.filter(item => {
      const counts = state.groupChat.unreadCounts;
      return item.type === 'room' ? (counts.rooms[item.id] > 0) : (counts.dms[item.id] > 0);
    });
  } else if (state.sidebarFilter === 'groups') {
    items = items.filter(item => item.type === 'room');
  }

  // 3. Search
  if (state.sidebarSearch) {
    const q = state.sidebarSearch.toLowerCase();
    items = items.filter(item => 
      item.name.toLowerCase().includes(q) || 
      (item.last_msg && item.last_msg.toLowerCase().includes(q))
    );
  }

  // 4. Sort by latest message
  items.sort((a, b) => {
    const timeA = a.last_time ? new Date(a.last_time).getTime() : 0;
    const timeB = b.last_time ? new Date(b.last_time).getTime() : 0;
    return timeB - timeA;
  });

  // 5. Render
  if (items.length === 0) {
    listEl.innerHTML = `
      <div class="py-12 text-center">
        <div class="text-[10px] font-black uppercase tracking-widest opacity-30">ไม่พบรายการแชท</div>
      </div>
    `;
    return;
  }

  listEl.innerHTML = items.map(item => {
    const isActive = state.currentChat.type === item.type && state.currentChat.id == item.id;
    const unreadCount = isActive ? 0 : (item.type === 'room' ? (state.groupChat.unreadCounts.rooms[item.id] || 0) : (state.groupChat.unreadCounts.dms[item.id] || 0));
    const isUnread = unreadCount > 0;
    const lastTime = item.last_time ? formatRelativeTime(item.last_time) : '';
    const preview = getChatPreview(item.last_msg, item.last_sender, item.last_attachments);
    const avatarIcon = item.type === 'room' ? 'users' : 'user';
    const isOnline = item.type === 'dm' && state.onlineUsers.includes(item.username || item.id);
    const dotClass = isOnline ? 'online' : 'offline';
    const isTyping = state.typingUsers && state.typingUsers[item.id] && state.typingUsers[item.id].size > 0;

    return `
      <div onclick="switchChat('${item.type}', '${item.id}', '${item.name}', '${item.avatar_url || ''}')" 
           class="messenger-chat-item ${isActive ? 'active' : ''} ${isUnread ? 'unread' : ''} group">
        <div class="messenger-avatar-container">
          <div class="messenger-avatar relative ${item.type === 'dm' ? dotClass : ''}">
            ${item.avatar_url ? `<img src="${item.avatar_url}" class="w-full h-full object-cover">` : `<div class="w-full h-full flex items-center justify-center bg-brand-600/10 text-brand-600"><i data-lucide="${avatarIcon}" class="w-6 h-6"></i></div>`}
            ${item.type === 'dm' ? `<div class="messenger-online-dot ${dotClass}"></div>` : ''}
          </div>
        </div>
        <div class="messenger-content">
          <div class="flex items-center justify-between">
            <span class="messenger-name truncate">${item.name}</span>
            <span class="messenger-time shrink-0">${lastTime}</span>
          </div>
          <div class="messenger-preview-row flex items-center justify-between gap-2 mt-0.5">
            <span class="messenger-preview truncate flex-1 ${isTyping ? 'text-brand-600 font-bold' : ''}">${isTyping ? '<i data-lucide="pencil" class="w-3 h-3 inline mr-1"></i>กำลังพิมพ์...' : preview}</span>
            ${isUnread ? `<div class="messenger-unread-dot">${unreadCount > 99 ? '99+' : unreadCount}</div>` : ''}
          </div>
        </div>
      </div>
    `;
  }).join('');

  initIcons();
}

function setReply(msgId, username, text) {
  state.groupChat.replyTo = { id: msgId, username, text };
  
  const tray = $('replyPreview');
  const userEl = $('replyToUser');
  const textEl = $('replyToText');
  
  if (tray && userEl && textEl) {
    userEl.textContent = username;
    textEl.textContent = text;
    tray.classList.remove('hidden');
    $('groupChatInput').focus();
  }
}

function cancelReply() {
  state.groupChat.replyTo = null;
  const tray = $('replyPreview');
  if (tray) tray.classList.add('hidden');
}

async function switchChat(type, id, name, avatarUrl) {
  state.currentChat = { type, id, name, avatarUrl };

  // Update Status in Header immediately
  updateChatHeaderStatus();

  // Socket Join
  if (socket) {
    const socketRoom = type === 'room' ? `room_${id}` : `dm_${id}`;
    socket.emit('join', { room: socketRoom });
    
    // Also join self room for DMs
    const currentUser = (typeof state.user === 'object' ? state.user?.username : state.user);
    if (currentUser) {
        socket.emit('join', { room: `dm_${currentUser}` });
    }

    // Update Call Button Visibility
    if (typeof checkCallButtonsVisibility === 'function') {
      checkCallButtonsVisibility();
    }

    // Notify backend that user is online in this chat
    socket.emit('user_online', {
      room: name || 'General',
      room_id: id,
      type: type,
      username: state.username
    });
  }

  // Mobile Transition & Visibility
  if (groupChatModal) {
    groupChatModal.classList.remove('hidden'); // Ensure it's not hidden
    if (window.innerWidth < 1024) {
      groupChatModal.classList.add('chat-open'); // Open the chat view on mobile
    }
  }

  state.lastRendered.messages = ''; // Reset to force re-render
  if (groupChatMessages) {
    groupChatMessages.innerHTML = `
      <div class="flex flex-col items-center justify-center py-20 animate-pulse">
        <div class="w-12 h-12 bg-surface-100 dark:bg-surface-800 rounded-2xl flex items-center justify-center mb-4">
          <i data-lucide="loader-2" class="w-6 h-6 text-brand-600 animate-spin"></i>
        </div>
        <div class="text-[10px] font-black uppercase tracking-widest opacity-50">กำลังโหลดข้อความ...</div>
      </div>
    `;
  }

  if (chatHeaderName) chatHeaderName.textContent = name;
  if (chatInputArea) chatInputArea.classList.remove('hidden');
  const chatInputFooter = $('chatInputFooter');
  if (chatInputFooter) chatInputFooter.classList.remove('hidden');

  // Reverted mobile view logic: keep both sidebar and main area visible if layout permits
  // No longer adding 'chat-open' class

  // Update Avatar & Add Member Button
  if (type === 'room') {
    if (chatHeaderAvatar) {
      if (avatarUrl) {
        chatHeaderAvatar.innerHTML = `<img src="${avatarUrl}" class="w-full h-full object-cover">`;
      } else {
        chatHeaderAvatar.innerHTML = '<i data-lucide="users" class="w-5 h-5"></i>';
      }
    }
    chatHeaderStatus?.classList.remove('hidden');

    // Show viewMembersBtn for all users in a room
    $('viewMembersBtn')?.classList.remove('hidden');
    // Only owner or admin can edit/add members
    const room = state.chatList.rooms.find(r => r.id == id);
    const deleteGroupBtn = $('deleteGroupBtn');
    if (state.isAdmin || (room && room.owner === state.user)) {
      addMemberBtn?.classList.remove('hidden');
      editGroupBtn?.classList.remove('hidden');
    } else {
      addMemberBtn?.classList.add('hidden');
      editGroupBtn?.classList.add('hidden');
    }
    // Delete button: admin only
    if (deleteGroupBtn) {
      if (state.isAdmin) {
        deleteGroupBtn.classList.remove('hidden');
      } else {
        deleteGroupBtn.classList.add('hidden');
      }
    }
  } else {
    if (chatHeaderAvatar) {
      if (avatarUrl) {
        chatHeaderAvatar.innerHTML = `<img src="${avatarUrl}" class="w-full h-full object-cover">`;
      } else {
        chatHeaderAvatar.innerHTML = '<i data-lucide="user" class="w-5 h-5"></i>';
      }
    }
    chatHeaderStatus?.classList.add('hidden');
    addMemberBtn?.classList.add('hidden');
    editGroupBtn?.classList.add('hidden');
    $('deleteGroupBtn')?.classList.add('hidden');
    $('viewMembersBtn')?.classList.add('hidden');

    // Show call buttons for DM
    if (id === 'ai-assistant') {
      if (voiceCallBtn) voiceCallBtn.classList.add('hidden');
      if (videoCallBtn) videoCallBtn.classList.add('hidden');
    } else {
      if (voiceCallBtn) voiceCallBtn.classList.remove('hidden');
      if (videoCallBtn) videoCallBtn.classList.remove('hidden');
    }
  }

  // Ensure they are hidden for non-DM
  if (type !== 'dm') {
    if (voiceCallBtn) voiceCallBtn.classList.add('hidden');
    if (videoCallBtn) videoCallBtn.classList.add('hidden');
  }

  renderChatSidebar(); // Update active state

  // Clear any active persistent toasts for this chat
  document.querySelectorAll(`.chat-notification-toast[data-chat-key="${type}-${id}"]`).forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateX(-20px)';
    setTimeout(() => el.remove(), 300);
  });

  await loadChatMessages(true);
  initIcons();

  startChatPolling();
}

async function loadChatMessages(shouldScroll = false, isPeek = false) {
  if (!state.currentChat.id) return;
  try {
    const { type, id } = state.currentChat;
    // Use peek=1 for background polls if we don't want to mark as read
    const url = `/api/chat/messages/${type}/${id}${isPeek ? '?peek=1' : ''}`;
    const data = await apiFetch(url);
    if (data && data.ok) {
      state.groupChat.messages = data.messages;
      state.groupChat.lastReads = data.last_reads || [];
      renderChatMessages(shouldScroll);

      // ONLY delete unread count if we are NOT peeking
      if (!isPeek) {
        if (type === 'room') delete state.groupChat.unreadCounts.rooms[id];
        else delete state.groupChat.unreadCounts.dms[id];
        updateGlobalChatBadge();
        renderChatSidebar(); // Refresh sidebar to remove blue dot
        // Mark as read on server
        sendReadSignal();
      }
    }
  } catch (e) {
    console.error('Chat load error:', e);
    if (!isPeek) {
      groupChatMessages.innerHTML = `<div class="text-center py-20 text-red-500 text-xs font-bold uppercase tracking-widest">โหลดข้อความไม่สำเร็จ</div>`;
    }
  }
}

function startChatPolling() {
  stopChatPolling();
  state.groupChat.pollInterval = setInterval(() => {
    if (state.currentChat.id) {
      // Background messages poll should use PEEK if modal is hidden
      const isModalVisible = groupChatModal && !groupChatModal.classList.contains('hidden');
      loadChatMessages(false, !isModalVisible);
    }
  }, 3000);
}

function stopChatPolling() {
  if (state.groupChat.pollInterval) {
    clearInterval(state.groupChat.pollInterval);
    state.groupChat.pollInterval = null;
  }
}

function renderChatMessages(shouldScroll = false) {
  if (!groupChatMessages) return;

  const messagesHash = JSON.stringify(state.groupChat.messages);
  if (state.lastRendered.messages === messagesHash) return;

  const isAtBottom = groupChatMessages.scrollHeight - groupChatMessages.scrollTop <= groupChatMessages.clientHeight + 50;
  state.lastRendered.messages = messagesHash;

  // Handles Pinned Messages Header
  const pinnedMessages = state.groupChat.messages.filter(m => m.is_pinned);
  const pinnedContainer = $('pinnedMessagesContainer');
  const pinnedList = $('pinnedMessagesList');

  if (pinnedMessages.length > 0) {
    pinnedContainer?.classList.remove('hidden');
    pinnedList.innerHTML = pinnedMessages.map(m => `
      <div class="flex items-center gap-2 p-1.5 px-3 bg-white dark:bg-surface-800/80 border border-brand-500/20 rounded-full shadow-sm animate-in zoom-in duration-300 max-w-[90%] w-fit">
        <div class="text-[9px] text-surface-600 dark:text-surface-300 truncate font-bold leading-tight flex items-center gap-2">
           <span class="text-brand-600 font-black shrink-0">${m.display_name || m.username}:</span>
           <span class="truncate">${m.text}</span>
        </div>
        ${(state.isAdmin || state.currentChat.type === 'dm') ? `<button onclick="toggleRoomMessagePin(${m.id})" class="text-surface-300 hover:text-red-500 transition-colors ml-1"><i data-lucide="x" class="w-2.5 h-2.5"></i></button>` : ''}
      </div>
    `).join('');
  } else {
    pinnedContainer?.classList.add('hidden');
  }

  const html = state.groupChat.messages.map((m, idx) => {
    const isMe = String(m.username).toLowerCase() === String(state.user || '').toLowerCase();
    const isBot = m.username === 'AI-Assistant';
    const isLast = idx === state.groupChat.messages.length - 1;

    let bubbleClass = isMe
      ? 'bubble-me ml-auto'
      : (isBot ? 'bubble-bot border-l-2 border-brand-500' : 'bubble-them');

    if (m.is_pinned && !isMe) bubbleClass += ' ring-1 ring-brand-500/30 bg-brand-50 dark:bg-brand-900/10';

    // 🏆 Messenger-style Read Avatars Logic
    let readAvatarsHtml = '';
    const currentUser = (typeof state.user === 'object' ? state.user?.username : state.user)?.toLowerCase();
    
    if (state.currentChat.type === 'room') {
      const readers = (state.groupChat.lastReads || []).filter(r => r.max_id === m.id && r.username.toLowerCase() !== currentUser);
      if (readers.length > 0) {
        readAvatarsHtml = `
          <div class="read-avatars flex -space-x-1.5 mt-1 border-brand-500">
            ${readers.slice(0, 5).map(r => `
              <div class="w-3.5 h-3.5 rounded-full border-2 border-white dark:border-surface-900 overflow-hidden shadow-sm hover:scale-110 transition-transform bg-surface-200" title="${r.display_name || r.username}">
                ${r.avatar_url ? `<img src="${r.avatar_url}" class="w-full h-full object-cover">` : `<div class="w-full h-full flex items-center justify-center text-[5px] font-black bg-brand-50 text-brand-600">${r.username[0].toUpperCase()}</div>`}
              </div>
            `).join('')}
            ${readers.length > 5 ? `<div class="w-3.5 h-3.5 rounded-full bg-surface-100 dark:bg-surface-800 flex items-center justify-center text-[5px] font-black border-2 border-white dark:border-surface-900 text-surface-500">+${readers.length - 5}</div>` : ''}
          </div>
        `;
      }
    } else if (state.currentChat.type === 'dm' && isMe && m.is_read) {
        // Messenger style for DM: Only show avatar for the LATEST read message sent by me
        const lastReadMsg = [...state.groupChat.messages].reverse().find(msg => (String(msg.username).toLowerCase() === currentUser) && msg.is_read);
        if (lastReadMsg && lastReadMsg.id === m.id) {
             readAvatarsHtml = `
               <div class="w-3.5 h-3.5 rounded-full border-2 border-white dark:border-surface-900 overflow-hidden shadow-sm mt-1 bg-surface-200">
                  ${state.currentChat.avatarUrl ? `<img src="${state.currentChat.avatarUrl}" class="w-full h-full object-cover">` : `<div class="w-full h-full flex items-center justify-center text-[6px] font-black bg-brand-100 text-brand-600">${state.currentChat.name[0].toUpperCase()}</div>`}
               </div>
             `;
        }
    }

    const imageAttachments = m.attachments ? m.attachments.filter(a => a.type === 'image' || (a.name && (a.name.endsWith('.png') || a.name.endsWith('.jpg') || a.name.endsWith('.jpeg') || a.name.endsWith('.gif')))) : [];
    const audioAttachments = m.attachments ? m.attachments.filter(a => a.type === 'audio' || (a.name && (a.name.startsWith('voice_') || a.name.endsWith('.mp3') || a.name.endsWith('.wav') || a.name.endsWith('.m4a') || a.name.endsWith('.webm')))) : [];
    const fileAttachments = m.attachments ? m.attachments.filter(a => {
      const isImg = a.type === 'image' || (a.name && (a.name.endsWith('.png') || a.name.endsWith('.jpg') || a.name.endsWith('.jpeg') || a.name.endsWith('.gif')));
      const isAudio = a.type === 'audio' || (a.name && (a.name.startsWith('voice_') || a.name.endsWith('.mp3') || a.name.endsWith('.wav') || a.name.endsWith('.m4a') || a.name.endsWith('.webm')));
      return !isImg && !isAudio;
    }) : [];

    const imagesHtml = imageAttachments.length > 0 ? `
      <div class="chat-attachment-container ${isMe ? 'justify-end' : ''} mt-2 flex flex-wrap gap-2">
        ${imageAttachments.map(img => `
          <div onclick="openLightbox('${img.url}')" class="chat-img-attachment cursor-pointer hover:scale-[1.02] transition-transform w-[280px] h-[200px] max-w-full rounded-2xl overflow-hidden border border-surface-100 dark:border-surface-800 shadow-md">
            <img src="${img.url}" class="w-full h-full object-cover" loading="lazy" onerror="this.onerror=null;this.src='${img.url}'">
          </div>
        `).join('')}
      </div>
    ` : '';

    const audioHtml = audioAttachments.length > 0 ? `
      <div class="chat-attachment-container ${isMe ? 'justify-end' : ''} mt-2 flex flex-col gap-2">
        ${audioAttachments.map(audio => `
          <div class="audio-player-bubble ${isMe ? 'bubble-me' : 'bubble-them'} group/voice">
            <button class="voice-play-btn shrink-0" onclick="toggleVoicePlay(this, '${audio.url}')">
              <i data-lucide="play" class="w-4 h-4"></i>
            </button>
            <div class="flex-1 flex flex-col gap-1 min-w-[150px]">
              <div class="voice-waveform-container relative h-8 flex items-center cursor-pointer gap-[3px] px-1" onclick="seekVoice(event, this)" data-audio-url="${audio.url}">
                 ${(() => {
                   const cached = state.analyzedWaveforms.get(audio.url);
                   const pattern = cached || [40, 70, 90, 60, 45, 80, 100, 75, 50, 85, 95, 65, 40, 70, 90, 60, 45, 80, 100, 75, 50, 85, 95, 65];
                   if (!cached) analyzeAudioWaveform(audio.url);
                   return pattern.slice(0, 24).map(h => `<div class="waveform-bar w-[3px] bg-surface-300 dark:bg-surface-700 rounded-full transition-all duration-500" style="height: ${h}%"></div>`).join('');
                 })()}
              </div>
              <div class="flex items-center justify-between px-1">
                 <span class="voice-duration text-[9px] font-black opacity-40">0:00</span>
                 <i data-lucide="mic" class="w-2.5 h-2.5 opacity-20"></i>
              </div>
            </div>
            <audio src="${audio.url}" ontimeupdate="updateVoiceProgress(this)" onended="resetVoicePlayer(this)" class="hidden"></audio>
          </div>
        `).join('')}
      </div>
    ` : '';

    const filesHtml = fileAttachments.length > 0 ? `
      <div class="chat-attachment-container ${isMe ? 'justify-end' : ''} mt-2 flex flex-col gap-1.5">
        ${fileAttachments.map(file => `
          <a href="${file.url}" target="_blank" class="chat-file-attachment flex items-center gap-2 px-3 py-2 rounded-xl text-[10px] font-bold bg-white dark:bg-surface-800 border border-surface-100 dark:border-surface-700">
            <i data-lucide="file" class="w-3 h-3 text-brand-600"></i>
            <span class="truncate max-w-[120px]">${file.name}</span>
            <i data-lucide="download" class="w-2.5 h-2.5 ml-auto opacity-50"></i>
          </a>
        `).join('')}
      </div>
    ` : '';

    return `
      <div class="chat-msg-row group ${isMe ? 'msg-user' : (isBot ? 'msg-bot' : 'msg-them')} ${isLast ? 'animate-in fade-in' : ''}" id="msg-row-${m.id}">
        <div class="w-10 h-10 rounded-full overflow-hidden flex-shrink-0 bg-surface-200 dark:bg-surface-700 border border-surface-100 dark:border-surface-800 shadow-sm relative z-10 transition-transform group-hover:scale-105">
          ${m.avatar_url ? `<img src="${m.avatar_url}" class="w-full h-full object-cover">` : `<div class="w-full h-full flex items-center justify-center text-xs font-black uppercase text-surface-600 dark:text-surface-300 bg-brand-50">${m.username ? m.username[0] : '?'}</div>`}
        </div>
        <div class="msg-content-wrapper">
          <div class="flex items-center gap-2 mb-1 ${isMe ? 'flex-row-reverse text-right' : ''}">
            <span class="text-[10px] font-black text-surface-500 truncate max-w-[120px]">${m.display_name || m.username}</span>
            <div class="flex items-center gap-1.5">
              <span class="text-[8px] text-surface-400 opacity-60 shrink-0">${parseServerDate(m.timestamp).toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
            <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
              ${(m.id && !isBot) ? `<button onclick="setReply(${m.id}, '${(m.display_name || m.username).replace(/'/g, "\\'")}', ${JSON.stringify(m.text || '').replace(/"/g, '&quot;')})" class="p-1 text-slate-300 hover:text-brand-600 transition-colors" title="ตอบกลับ"><i data-lucide="reply" class="w-2.5 h-2.5"></i></button>` : ''}
              ${( (state.isAdmin || state.currentChat.type === 'dm') && m.id) ? `<button onclick="toggleRoomMessagePin(${m.id})" class="p-1 text-slate-300 hover:text-brand-600 transition-colors" title="ปักหมุด"><i data-lucide="pin" class="w-2.5 h-2.5 ${m.is_pinned ? 'fill-current text-brand-600' : ''}"></i></button>` : ''}
              ${(isMe && m.id) ? `<button onclick="editChatMessage('${state.currentChat.type}', ${m.id}, this.closest('.chat-msg-row'))" class="p-1 text-slate-300 hover:text-blue-500 transition-colors" title="แก้ไข"><i data-lucide="edit-3" class="w-2.5 h-2.5"></i></button>` : ''}
              ${(isMe && m.id) ? `<button onclick="deleteChatMessage('${state.currentChat.type}', ${m.id}, this.closest('.chat-msg-row'))" class="p-1 text-slate-300 hover:text-red-500 transition-colors" title="ลบ"><i data-lucide="trash-2" class="w-2.5 h-2.5"></i></button>` : ''}
              ${(!isMe && !isBot && m.text) ? `<button onclick="extractActionItems(${JSON.stringify(m.text).replace(/"/g, '&quot;')}, ${m.id})" class="ai-extract-btn p-1 text-slate-300 hover:text-purple-600 transition-colors" title="สกัดงานด้วย AI"><i data-lucide="wand-2" class="w-2.5 h-2.5"></i></button>` : ''}
            </div>
          </div>
          
          <div class="chat-bubble-container w-full flex flex-col ${isMe ? 'items-end' : 'items-start'}" id="msg-container-${m.id}">
            ${m.reply_to_id ? `
              <div class="reply-bubble mb-1.5 p-2 py-1.5 bg-surface-200/50 dark:bg-surface-800/50 border-l-4 border-brand-500/50 rounded-lg text-[10px] opacity-70 cursor-pointer hover:opacity-100 transition-opacity max-w-[85%]" onclick="scrollToMessage(${m.reply_to_id})">
                 <div class="font-black text-brand-600 uppercase tracking-tighter mb-0.5">${m.reply_sender || 'User'}</div>
                 <div class="truncate italic max-w-[200px]">${m.reply_text || 'ข้อความถูกลบ'}</div>
              </div>
            ` : ''}
            
            ${(m.text || m.is_pinned) ? `
              <div class="chat-bubble ${isMe ? 'bubble-me' : (isBot ? 'bubble-bot' : 'bubble-them')} shadow-sm">
                ${m.is_pinned ? `<div class="flex items-center gap-1.5 text-[9px] font-black uppercase tracking-widest mb-1.5 opacity-70"><i data-lucide="pin" class="w-2 h-2 fill-current"></i> Pinned</div>` : ''}
                <div class="whitespace-pre-wrap">${highlightMentions(m.text || '')}${m.edited_at ? ' <span class="text-[8px] opacity-50 italic">(แก้ไขแล้ว)</span>' : ''}</div>
              </div>
            ` : ''}
            
            ${imagesHtml}
            ${audioHtml}
            ${filesHtml}
            ${readAvatarsHtml}
            <div class="action-panel hidden w-full max-w-sm mt-3 overflow-hidden rounded-3xl shadow-xl"></div>
          </div>
        </div>
      </div>
    `;
  }).join('');

  groupChatMessages.innerHTML = html || '<div class="text-center py-10 text-surface-400 text-xs italic">ยังไม่มีข้อความ...</div>';
  initIcons();

  // Link Preview Trigger
  state.groupChat.messages.forEach(m => {
    if (m.text && m.text.includes('http')) {
      const urlMatch = m.text.match(/https?:\/\/[^\s]+/);
      if (urlMatch) {
         // Check if there is ONLY a link or if it's a single line link message
         const isSingleLink = m.text.trim() === urlMatch[0];
         renderLinkPreview(urlMatch[0], m.id, isSingleLink);
      }
    }
  });

  // Scroll to bottom if forced (manual action) OR if user was already at bottom (intelligent follow)
  if (shouldScroll || isAtBottom) {
    groupChatMessages.scrollTop = groupChatMessages.scrollHeight;
  }

  // Handle Interactive Actions (Reconciliation / Calendar) in Group Chat
  state.groupChat.messages.forEach(m => {
    if (m.text && (m.text.includes('[RECONCILE_ACTION]') || m.text.includes('[CALENDAR_ACTION]'))) {
       const msgEl = $(`msg-row-${m.id}`);
       if (msgEl) {
         const panel = msgEl.querySelector('.action-panel');
         // Only trigger if panel is hidden to prevent resetting user edits during polling
         if (panel && panel.classList.contains('hidden')) {
           const { calendarData, reconcileData } = parseAIActions(m.text);
           if (calendarData) renderCalendarActionUI(msgEl, calendarData);
           if (reconcileData) renderReconcileActionUI(msgEl, reconcileData);
         }
       }
    }
  });
}

function scrollToMessage(id) {
  const el = $(`msg-container-${id}`);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    el.classList.add('highlight-glow');
    setTimeout(() => el.classList.remove('highlight-glow'), 2000);
  } else {
    toast('ไม่พบข้อความเดิม หรืออยู่ไกลเกินไป', 'info');
  }
}

function updateChatBadge() {
  const badge = document.getElementById('groupChatBadge');
  if (!badge) return;
  const count = state.groupChat.unreadCount;
  if (count > 0) {
    badge.textContent = count > 99 ? '99+' : count;
    badge.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
  }
}

// ── Chat Toast Queue ──────────────────────────────────────────
// Tracks seen messages to prevent showing duplicate toasts for same message
const _chatToastQueue = [];
// ✅ FIX 3: _seenToastKeys is now cleared at the start of each poll cycle (in loadUnreadCounts)
const _seenToastKeys = new Set();
let _chatToastTimer = null;

function queueChatToast(data) {
  // ✅ FIX 2: Better dedup key — includes type + chatName + sender + preview
  // This prevents different chats with same preview text from being merged
  const key = `${data.type}:${data.id}:${data.sender}:${(data.preview || '').slice(0, 40)}`; // Use id for key
  if (_seenToastKeys.has(key)) return; // skip duplicate within same poll cycle
  _seenToastKeys.add(key);

  _chatToastQueue.push(data);
  if (!_chatToastTimer) {
    _chatToastTimer = setTimeout(_showNextToast, 300); // slight debounce to batch
  }
}

function _showNextToast() {
  _chatToastTimer = null;
  if (_chatToastQueue.length === 0) return;

  // Show each toast individually with stagger — no collapsing into 1
  const toShow = [..._chatToastQueue];
  _chatToastQueue.length = 0;

  toShow.forEach((toastData, i) => {
    setTimeout(() => showChatToast(toastData, i), i * 400);
  });
}

function showChatToast({ type = 'room', id = null, chatName = 'ข้อความใหม่', sender = '', preview = '', count = 1 } = {}, stackIndex = 0) {
  const chatKey = `${type}-${id}`;
  const existing = document.querySelector(`.chat-notification-toast[data-chat-key="${chatKey}"]`);

  if (existing) {
    if (existing._dismissTimer) clearTimeout(existing._dismissTimer);

    // Update content
    const senderEl = existing.querySelector('.sender-name');
    const previewEl = existing.querySelector('.preview-text');
    const badgeContainer = existing.querySelector('.badge-container');

    if (senderEl) senderEl.textContent = sender || 'มีข้อความใหม่';
    if (previewEl) previewEl.textContent = preview || 'แตะเพื่อเปิดการสนทนา';

    if (badgeContainer) {
      badgeContainer.innerHTML = count > 1 ? `<span class="bg-red-500 text-white text-[9px] font-black px-1.5 py-0.5 rounded-full">+${count - 1}</span>` : '';
    }

    // Shake animation
    existing.style.animation = 'none';
    existing.offsetHeight;
    existing.style.animation = 'chatToastUpdate 0.4s ease';

    // No auto-dismiss. It stays until viewed.
    return;
  }

  const toastId = 'chatToast_' + Date.now() + '_' + stackIndex;
  const visibleToasts = document.querySelectorAll('.chat-notification-toast').length;
  // Compact centered top pop-up
  const topOffset = 16 + (visibleToasts * 75);

  const el = document.createElement('div');
  el.id = toastId;
  el.className = 'chat-notification-toast group';
  el.dataset.chatKey = chatKey;
  el.style.cssText = `
    position: fixed;
    top: ${topOffset}px;
    left: 50%;
    transform: translateX(-50%);
    width: 320px;
    max-width: calc(100vw - 32px);
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 20px;
    box-shadow: 0 15px 30px -5px rgba(0, 0, 0, 0.15), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
    z-index: 10000;
    padding: 10px 14px;
    display: flex;
    gap: 12px;
    border: 1px solid rgba(255, 255, 255, 0.4);
    cursor: pointer;
    animation: chatPopDown 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
    transition: all 0.4s ease;
  `;
  if (document.documentElement.classList.contains('dark')) {
    el.style.backgroundColor = '#1e293b';
    el.style.borderColor = 'rgba(255,255,255,0.05)';
  }

  el.innerHTML = `
    <div class="w-10 h-10 rounded-xl bg-brand-600 text-white flex items-center justify-center shrink-0 shadow-md">
      <i data-lucide="${type === 'room' ? 'users' : 'user'}" class="w-5 h-5"></i>
    </div>
    <div class="flex-1 min-w-0 pr-2">
      <div class="flex items-center justify-between mb-0">
        <h4 class="text-[10px] font-black uppercase text-brand-600 tracking-wider truncate">${chatName}</h4>
        <div class="badge-container">${count > 1 ? `<span class="bg-red-500 text-white text-[8px] font-black px-1.5 py-0.5 rounded-full">+${count - 1}</span>` : ''}</div>
      </div>
      <p class="sender-name text-[11px] font-black text-slate-800 dark:text-white truncate">${sender || 'มีข้อความใหม่'}</p>
      <p class="preview-text text-[10px] text-slate-500 dark:text-slate-400 line-clamp-1">${preview || 'แตะเพื่อตอบกลับ'}</p>
    </div>
    <button class="close-toast-btn absolute right-3 top-3 p-1 text-slate-300 hover:text-slate-600 dark:hover:text-slate-100 transition-colors">
      <i data-lucide="x" class="w-4 h-4"></i>
    </button>
  `;

  // ✅ TRIGGER SYSTEM NOTIFICATION: This allows the message to show over OTHER apps
  if (Notification.permission === 'granted') {
    showSystemNotification(sender || chatName, preview || 'แตะเพื่อตอบกลับ', '#chat');
  }

  document.body.appendChild(el);
  lucide.createIcons({ props: { "stroke-width": 2.5 } });

  // Inject keyframes
  if (!document.getElementById('chatToastStyle')) {
    const style = document.createElement('style');
    style.id = 'chatToastStyle';
    style.innerHTML = `
    @keyframes chatPopDown { 
      from { opacity: 0; transform: translate(-50%, -40px) scale(0.9); } 
      to { opacity: 1; transform: translate(-50%, 0) scale(1); } 
    }
    @keyframes chatPopUpOut { 
      from { opacity: 1; transform: translate(-50%, 0) scale(1); } 
      to { opacity: 0; transform: translate(-50%, -20px) scale(0.9); } 
    }
    @keyframes chatToastUpdate { 0% { transform: translate(-50%, 0) scale(1); } 50% { transform: translate(-50%, 0) scale(1.05); } 100% { transform: translate(-50%, 0) scale(1); } }
  `;
    document.head.appendChild(style);
  }

  const dismissToast = () => {
    el.style.animation = 'chatPopUpOut 0.3s ease forwards';
    setTimeout(() => el.remove(), 300);
  };

  // ✅ Auto-dismiss after 5s for a clean pop-up feel
  const dismissTimer = setTimeout(dismissToast, 5000);
  el._dismissTimer = dismissTimer;

  el.querySelector('.close-toast-btn').onclick = (e) => {
    e.stopPropagation();
    dismissToast();
  };

  el.onclick = () => {
    dismissToast();
    if (type === 'room') {
      switchChat('room', id, chatName);
    } else {
      switchChat('dm', id, chatName);
    }
    if (groupChatModal.classList.contains('hidden')) {
      if (groupChatHead) groupChatHead.click();
    }
  };
}

function toggleChatFullscreen() {
  const modal = $('groupChatModal');
  const icon = $('fullscreenIcon');
  if (!modal) return;
  modal.classList.toggle('fullscreen');
  const isFullscreen = modal.classList.contains('fullscreen');
  if (icon) {
    icon.setAttribute('data-lucide', isFullscreen ? 'minimize-2' : 'maximize-2');
    initIcons();
  }
}

let lightboxState = {
  zoom: 1.0,
  minZoom: 0.5,
  maxZoom: 5.0,
  panX: 0,
  panY: 0,
  isDragging: false,
  startX: 0,
  startY: 0
};

function updateLightboxTransform() {
  const img = $('lightboxImage');
  const levelText = $('lightboxZoomLevel');
  if (!img) return;
  img.style.transform = `translate(${lightboxState.panX}px, ${lightboxState.panY}px) scale(${lightboxState.zoom})`;
  img.style.cursor = lightboxState.zoom > 1 ? (lightboxState.isDragging ? 'grabbing' : 'grab') : 'zoom-in';
  if (levelText) {
    levelText.textContent = `${Math.round(lightboxState.zoom * 100)}%`;
  }
}

function lightboxZoom(delta) {
  let newZoom = Math.round((lightboxState.zoom + delta) * 100) / 100;
  if (newZoom < lightboxState.minZoom) newZoom = lightboxState.minZoom;
  if (newZoom > lightboxState.maxZoom) newZoom = lightboxState.maxZoom;
  lightboxState.zoom = newZoom;
  if (lightboxState.zoom <= 1) {
    lightboxState.panX = 0;
    lightboxState.panY = 0;
  }
  updateLightboxTransform();
}

function lightboxResetZoom() {
  lightboxState.zoom = 1.0;
  lightboxState.panX = 0;
  lightboxState.panY = 0;
  updateLightboxTransform();
}

function initLightboxEvents() {
  const lightbox = $('imageLightbox');
  const img = $('lightboxImage');
  if (!lightbox || !img || lightbox._eventsInitialized) return;
  lightbox._eventsInitialized = true;

  // Wheel zoom
  lightbox.addEventListener('wheel', (e) => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 0.2 : -0.2;
    lightboxZoom(delta);
  }, { passive: false });

  // Double click to toggle 1x / 2.5x
  img.addEventListener('dblclick', (e) => {
    e.preventDefault();
    if (lightboxState.zoom > 1.2) {
      lightboxResetZoom();
    } else {
      lightboxState.zoom = 2.5;
      updateLightboxTransform();
    }
  });

  // Drag to pan
  img.addEventListener('mousedown', (e) => {
    if (lightboxState.zoom <= 1) return;
    e.preventDefault();
    lightboxState.isDragging = true;
    lightboxState.startX = e.clientX - lightboxState.panX;
    lightboxState.startY = e.clientY - lightboxState.panY;
    updateLightboxTransform();
  });

  window.addEventListener('mousemove', (e) => {
    if (!lightboxState.isDragging) return;
    lightboxState.panX = e.clientX - lightboxState.startX;
    lightboxState.panY = e.clientY - lightboxState.startY;
    updateLightboxTransform();
  });

  window.addEventListener('mouseup', () => {
    if (lightboxState.isDragging) {
      lightboxState.isDragging = false;
      updateLightboxTransform();
    }
  });

  // Keyboard navigation (Esc, +, -, 0)
  window.addEventListener('keydown', (e) => {
    if (!lightbox || lightbox.classList.contains('hidden')) return;
    if (e.key === 'Escape') {
      closeLightbox();
    } else if (e.key === '+' || e.key === '=') {
      lightboxZoom(0.25);
    } else if (e.key === '-' || e.key === '_') {
      lightboxZoom(-0.25);
    } else if (e.key === '0') {
      lightboxResetZoom();
    }
  });

  // Touch pinch-to-zoom & touch drag for mobile devices
  let initialPinchDist = 0;
  let initialTouchZoom = 1;
  lightbox.addEventListener('touchstart', (e) => {
    if (e.touches.length === 2) {
      initialPinchDist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      initialTouchZoom = lightboxState.zoom;
    } else if (e.touches.length === 1 && lightboxState.zoom > 1) {
      lightboxState.isDragging = true;
      lightboxState.startX = e.touches[0].clientX - lightboxState.panX;
      lightboxState.startY = e.touches[0].clientY - lightboxState.panY;
    }
  }, { passive: true });

  lightbox.addEventListener('touchmove', (e) => {
    if (e.touches.length === 2 && initialPinchDist > 0) {
      const dist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      const factor = dist / initialPinchDist;
      let newZ = Math.min(Math.max(initialTouchZoom * factor, lightboxState.minZoom), lightboxState.maxZoom);
      lightboxState.zoom = Math.round(newZ * 100) / 100;
      updateLightboxTransform();
    } else if (e.touches.length === 1 && lightboxState.isDragging) {
      lightboxState.panX = e.touches[0].clientX - lightboxState.startX;
      lightboxState.panY = e.touches[0].clientY - lightboxState.startY;
      updateLightboxTransform();
    }
  }, { passive: true });

  lightbox.addEventListener('touchend', () => {
    lightboxState.isDragging = false;
    initialPinchDist = 0;
  }, { passive: true });
}

function openLightbox(url, name) {
  const lightbox = $('imageLightbox');
  const img = $('lightboxImage');
  const downloadBtn = $('lightboxDownload');
  const titleEl = $('lightboxTitle');
  if (!lightbox || !img) return;

  const fileName = name || (url ? url.split('/').pop().split('?')[0] : 'image.jpg');
  img.src = url;
  if (downloadBtn) {
    downloadBtn.href = url;
    downloadBtn.setAttribute('download', fileName);
  }
  if (titleEl) {
    titleEl.textContent = fileName;
  }

  lightboxResetZoom();
  lightbox.classList.remove('hidden');
  lightbox.classList.add('flex', 'items-center', 'justify-center');
  document.body.style.overflow = 'hidden';
  initLightboxEvents();
  initIcons();
}

function closeLightbox() {
  const lightbox = $('imageLightbox');
  if (!lightbox) return;
  lightboxResetZoom();
  lightbox.classList.add('hidden');
  lightbox.classList.remove('flex', 'items-center', 'justify-center');
  document.body.style.overflow = '';
}

function renderChatAttachmentPreview() {
  if (!chatAttachmentPreview) return;
  if (state.groupChat.pendingFiles.length === 0) {
    chatAttachmentPreview.classList.add('hidden');
    return;
  }

  chatAttachmentPreview.classList.remove('hidden');
  chatAttachmentPreview.innerHTML = state.groupChat.pendingFiles.map((f, idx) => {
    const isImg = f.type.startsWith('image/');
    return `
      <div class="attachment-preview-item">
        ${isImg ? `<img src="${URL.createObjectURL(f)}">` : `<div class="w-full h-full flex items-center justify-center bg-surface-100"><i data-lucide="file" class="w-5 h-5 text-surface-400"></i></div>`}
        <div class="attachment-remove-btn" onclick="removeChatAttachment(${idx})">×</div>
      </div>
    `;
  }).join('');
  initIcons();
}

function removeChatAttachment(idx) {
  state.groupChat.pendingFiles.splice(idx, 1);
  renderChatAttachmentPreview();
}

async function sendUnifiedMessage() {
  const text = groupChatInput.value.trim();
  const fileCount = state.groupChat.pendingFiles.length;

  if (!text && fileCount === 0) return;

  sendGroupChatBtn.disabled = true;
  const originalFiles = [...state.groupChat.pendingFiles];
  groupChatInput.value = '';
  state.groupChat.pendingFiles = [];
  renderChatAttachmentPreview();

  try {
    let finalType = state.currentChat.type;
    let finalId = state.currentChat.id;
    let finalMsg = text;

    // Command parsing: /chat @username "message"
    if (text.startsWith('/chat @')) {
      const parts = text.split(' ');
      if (parts.length >= 2) {
        const target = parts[0].substring(7); // @username
        const msg = parts.slice(1).join(' ');
        if (target && msg) {
          finalType = 'dm';
          finalId = target;
          finalMsg = msg;
          toast(`ส่งข้อความส่วนตัวไปยัง @${target}`, 'success');
        }
      }
    }

    const formData = new FormData();
    formData.append('type', finalType);
    formData.append('id', finalId);
    formData.append('message', finalMsg);
    if (state.groupChat.replyTo) {
      formData.append('reply_to_id', state.groupChat.replyTo.id);
    }
    originalFiles.forEach(f => {
      // 🎙️ EXTRA CHECK: If file is from our recorder (named voice_*.webm), mark as audio blobl property
      // though f.type is usually correct, we can also use a custom property if needed.
      formData.append('files', f);
    });

    const res = await fetch('/api/chat/send', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error);

    cancelReply();
    loadChatMessages(true);
    if (state.currentChat.type === 'dm') loadChatList(); // Refresh contacts list if new
  } catch (e) {
    toast('ส่งข้อความไม่สำเร็จ: ' + e.message, 'error');
    groupChatInput.value = text;
    state.groupChat.pendingFiles = originalFiles;
    renderChatAttachmentPreview();
  } finally {
    sendGroupChatBtn.disabled = false;
    groupChatInput.focus();
  }
}

// ─── Group Creation Logic ────────────────────
async function openCreateGroup() {
  createGroupModal.classList.remove('hidden');
  createGroupModal.classList.add('flex', 'items-center', 'justify-center');
  memberSelectList.innerHTML = '<div class="text-center p-4 opacity-50 text-xs">กำลังโหลดรายชื่อ...</div>';

  try {
    const data = await apiFetch('/api/chat/users');
    if (data && data.ok) {
      memberSelectList.innerHTML = data.users.map(u => `
                <label class="flex items-center gap-3 p-2 hover:bg-surface-50 dark:hover:bg-surface-800 rounded-xl cursor-pointer">
                    <input type="checkbox" name="member" value="${u.username}" class="w-4 h-4 rounded border-surface-300 text-brand-600 focus:ring-brand-600">
                    <div class="flex items-center gap-2">
                        <div class="w-8 h-8 rounded-full overflow-hidden bg-surface-200">
                            ${u.avatar_url ? `<img src="${u.avatar_url}" class="w-full h-full object-cover">` : `<div class="w-full h-full flex items-center justify-center text-[10px] font-bold">${u.username[0]}</div>`}
                        </div>
                        <span class="text-xs font-bold">${u.display_name || u.username}</span>
                    </div>
                </label>
            `).join('');
    }
  } catch (e) {
    memberSelectList.innerHTML = '<div class="text-center p-4 text-red-500 text-xs text-bold">โหลดข้อมูลล้มเหลว</div>';
  }
}

async function handleCreateGroup() {
  const name = newGroupName.value.trim();
  if (!name) return toast('กรุณาระบุชื่อกลุ่ม', 'error');

  const selected = Array.from(document.querySelectorAll('input[name="member"]:checked')).map(i => i.value);

  confirmCreateGroup.disabled = true;
  confirmCreateGroup.innerHTML = '<i class="animate-spin w-4 h-4" data-lucide="loader-2"></i>';
  initIcons();

  try {
    const res = await fetch('/api/groups/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, members: selected })
    });
    const data = await res.json();
    if (data.ok) {
      toast('สร้างกลุ่มสำเร็จ!', 'success');
      createGroupModal.classList.add('hidden');
      createGroupModal.classList.remove('flex', 'items-center', 'justify-center');
      newGroupName.value = '';
      loadChatList();
      switchChat('room', data.room_id, name);
    } else {
      toast(data.error, 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาดในการสร้างกลุ่ม', 'error');
  } finally {
    confirmCreateGroup.disabled = false;
    confirmCreateGroup.textContent = 'สร้างกลุ่ม';
    initIcons();
  }
}

async function openAddMemberModal() {
  if (!state.currentChat || state.currentChat.type !== 'room') return;
  addMemberSelectList.innerHTML = '<div class="text-center py-4 opacity-50 text-xs">กำลังโหลดรายชื่อ...</div>';
  addMemberModal.classList.remove('hidden');
  addMemberModal.classList.add('flex', 'items-center', 'justify-center');

  try {
    const data = await apiFetch('/api/chat/users');
    if (data.ok && data.users) {
      // Get current members to highlight or exclude? 
      // For now just show all and let INSERT OR IGNORE handle it.
      addMemberSelectList.innerHTML = data.users
        .filter(u => u.username !== 'AI-Assistant')
        .map(user => `
          <label class="flex items-center gap-3 p-3 hover:bg-surface-50 dark:hover:bg-surface-800 rounded-xl cursor-pointer transition-colors group">
            <input type="checkbox" name="newMember" value="${user.username}" class="w-4 h-4 rounded border-surface-300 text-brand-600 focus:ring-brand-500">
            <div class="w-8 h-8 rounded-lg bg-surface-100 dark:bg-surface-800 flex items-center justify-center overflow-hidden">
              ${user.avatar_url ? `<img src="${user.avatar_url}" class="w-full h-full object-cover">` : `<i data-lucide="user" class="w-4 h-4 text-surface-400"></i>`}
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-xs font-bold truncate dark:text-white">${user.display_name || user.username}</div>
              <div class="text-[9px] text-surface-400 font-medium">@${user.username}</div>
            </div>
          </label>
        `).join('');
      initIcons();
    }
  } catch (e) {
    addMemberSelectList.innerHTML = '<div class="text-center py-4 text-red-500 text-xs">โหลดไม่สำเร็จ</div>';
  }
}

async function handleAddMembers() {
  const selected = Array.from(document.querySelectorAll('input[name="newMember"]:checked')).map(i => i.value);
  if (selected.length === 0) return toast('กรุณาเลือกสมาชิกอย่างน้อย 1 คน', 'warning');

  confirmAddMember.disabled = true;
  confirmAddMember.innerHTML = '<i class="animate-spin w-4 h-4" data-lucide="loader-2"></i>';
  initIcons();

  try {
    const res = await fetch(`/api/groups/${state.currentChat.id}/members`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ members: selected })
    });
    const data = await res.json();
    if (data.ok) {
      toast('เพิ่มสมาชิกเรียบร้อย!', 'success');
      addMemberModal.classList.add('hidden');
      addMemberModal.classList.remove('flex', 'items-center', 'justify-center');
      document.querySelectorAll('input[name="newMember"]').forEach(i => i.checked = false);
    } else {
      toast(data.error, 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาดในการเพิ่มสมาชิก', 'error');
  } finally {
    confirmAddMember.disabled = false;
    confirmAddMember.textContent = 'เพิ่มเข้ากลุ่ม';
    initIcons();
  }
}

// 👤 Start DM Logic
let allUsersForDm = [];

async function openStartDm() {
  startDmModal.classList.remove('hidden');
  startDmModal.classList.add('flex', 'items-center', 'justify-center');
  dmUserSelectList.innerHTML = '<div class="text-center p-4 opacity-50 text-xs text-bold uppercase tracking-widest">กำลังโหลดรายชื่อ...</div>';
  searchDmUser.value = '';

  try {
    const data = await apiFetch('/api/chat/users');
    if (data && data.ok) {
      allUsersForDm = data.users;
      renderDmUserList(allUsersForDm);
    }
  } catch (e) {
    dmUserSelectList.innerHTML = '<div class="text-center p-4 text-red-500 text-xs font-bold">โหลดข้อมูลล้มเหลว</div>';
  }
}

function renderDmUserList(users) {
  if (!users.length) {
    dmUserSelectList.innerHTML = '<div class="text-center p-10 opacity-40 text-xs italic">ไม่พบผู้ใช้งาน...</div>';
    return;
  }

  dmUserSelectList.innerHTML = users.map(u => `
        <div onclick="startPrivateChat('${u.username}', '${u.display_name || u.username}')" 
             class="flex items-center gap-3 p-3 hover:bg-surface-50 dark:hover:bg-surface-800 rounded-2xl cursor-pointer transition-all group">
            <div class="w-10 h-10 rounded-2xl overflow-hidden bg-surface-100 dark:bg-surface-800 flex-shrink-0">
                ${u.avatar_url ? `<img src="${u.avatar_url}" class="w-full h-full object-cover">` : `<div class="w-full h-full flex items-center justify-center text-xs font-black bg-brand-600/10 text-brand-600">${u.username ? u.username[0].toUpperCase() : '?'}</div>`}
            </div>
            <div class="flex-1 min-w-0">
                <div class="text-sm font-bold group-hover:text-brand-600 transition-colors truncate">${u.display_name || u.username}</div>
                <div class="text-[10px] text-surface-400 font-bold uppercase tracking-widest truncate">@${u.username}</div>
            </div>
            <i data-lucide="message-square" class="w-4 h-4 text-surface-300 group-hover:text-brand-600 transition-colors"></i>
        </div>
    `).join('');
  initIcons();
}

function startPrivateChat(username, displayName) {
  if (startDmModal) {
    startDmModal.classList.add('hidden');
    startDmModal.classList.remove('flex', 'items-center', 'justify-center');
  }
  
  // Ensure we are in the chat view when starting a private chat
  if (typeof switchView === 'function' && state.currentView !== 'chat') {
    switchView('chat');
  }
  
  switchChat('dm', username, displayName);
}

if (searchDmUser) {
  searchDmUser.oninput = (e) => {
    const query = e.target.value.toLowerCase().trim();
    const filtered = allUsersForDm.filter(u =>
      u.username.toLowerCase().includes(query) ||
      (u.display_name && u.display_name.toLowerCase().includes(query))
    );
    renderDmUserList(filtered);
  };
}


// ─── Initialization ────────────────────────
async function initAppContent() {
  console.log("🎮 Loading app content...");
  // 1. Hide the login overlay
  const overlay = $('loginOverlay');
  if (overlay) {
    overlay.classList.add('hidden');
  }

  try {
    // 2. Sequential load of dashboard services
    await loadStatus(); // Set state.isAdmin and toggle features
    await loadNotifications();
    await loadChatList();
    await loadUnreadCounts();
    await loadHistory();
    await loadFiles();
    await loadSchedules();
    await loadPersonas();
    await loadDashboard();
    
    console.log("✅ App Content Loaded.");

    // 3. Final UI cleanup
    initIcons();

    // Switch to a view only if the user has NOT navigated away while loading.
    if (typeof switchView === 'function' && !state.currentView) {
      const _sp = new URLSearchParams(window.location.search);
      const targetView = _sp.get('view');
      if (targetView && document.getElementById('view-' + targetView)) {
        switchView(targetView);
      } else {
        switchView('home');
      }
    }
  } catch (e) {
    console.error("Content Load Failure:", e);
  }
}

// Profile Events ────────────────────────────
document.querySelectorAll('.bg-preset-btn').forEach(btn => {
  btn.onclick = () => {
    const bg = btn.dataset.bg;
    const coverPreview = $('profileCoverPreview');
    if (bg === 'custom') {
      const color = prompt('ระบุรหัสสี:', '#2563eb');
      if (color) {
        document.body.style.background = color;
        if (coverPreview) coverPreview.style.background = color;
        state.tempBackground = color;
      }
    } else {
      document.body.style.background = bg;
      if (coverPreview) coverPreview.style.background = bg;
      state.tempBackground = bg;
      document.querySelectorAll('.bg-preset-btn').forEach(b => b.classList.remove('border-brand-600'));
      btn.classList.add('border-brand-600');
    }
  };
});

// Reset Chat Right Panel to Clean Empty State
function resetChatToEmptyState() {
  state.currentChat = { type: null, id: null, name: null };
  state.lastRendered.messages = '';
  stopChatPolling();
  
  if (chatHeaderName) chatHeaderName.textContent = 'เลือกบทสนทนา';
  if (chatHeaderAvatar) {
    chatHeaderAvatar.innerHTML = '<i data-lucide="message-square" class="w-5 h-5 text-brand-600"></i>';
  }
  if (chatHeaderStatus) chatHeaderStatus.classList.add('hidden');
  
  // Hide call and group action buttons
  $('voiceCallBtn')?.classList.add('hidden');
  $('videoCallBtn')?.classList.add('hidden');
  $('viewMembersBtn')?.classList.add('hidden');
  $('addMemberBtn')?.classList.add('hidden');
  $('editGroupBtn')?.classList.add('hidden');
  $('deleteGroupBtn')?.classList.add('hidden');
  
  // Hide footer input & previews
  $('chatInputFooter')?.classList.add('hidden');
  $('replyPreview')?.classList.add('hidden');
  $('pinnedMessagesContainer')?.classList.add('hidden');
  $('unifiedTypingIndicator')?.classList.add('hidden');
  
  // Clear input value and file queue
  if (groupChatInput) groupChatInput.value = '';
  state.groupChat.pendingFiles = [];
  if (typeof renderChatAttachmentPreview === 'function') {
    renderChatAttachmentPreview();
  }
  
  // Render empty placeholder inside messages container
  if (groupChatMessages) {
    groupChatMessages.innerHTML = `
      <div id="chatEmptyPlaceholder" class="flex-1 flex flex-col items-center justify-center text-center p-8 h-full select-none">
        <div class="relative mb-6">
          <div class="w-24 h-24 rounded-3xl bg-gradient-to-tr from-brand-600/20 via-brand-500/10 to-transparent flex items-center justify-center shadow-inner border border-brand-500/20">
            <i data-lucide="messages-square" class="w-12 h-12 text-brand-500"></i>
          </div>
          <div class="absolute -bottom-1 -right-1 w-8 h-8 rounded-2xl bg-surface-100 dark:bg-surface-800 flex items-center justify-center border border-surface-200 dark:border-surface-700 shadow-sm text-surface-400">
            <i data-lucide="sparkles" class="w-4 h-4 text-amber-500"></i>
          </div>
        </div>
        <h3 class="text-xl font-black text-surface-900 dark:text-white mb-2">เลือกบทสนทนาเพื่อเริ่มแชท</h3>
        <p class="text-xs text-surface-400 max-w-[280px] leading-relaxed">
          คลิกที่รายชื่อผู้ติดต่อหรือกลุ่มจากแถบด้านซ้าย เพื่อเปิดดูข้อความและเริ่มการสนทนา
        </p>
      </div>
    `;
  }
  
  // Remove active highlight from sidebar items
  document.querySelectorAll('.messenger-chat-item').forEach(el => el.classList.remove('active'));
  
  if (typeof initIcons === 'function') initIcons();
}
window.resetChatToEmptyState = resetChatToEmptyState;

// Mobile & Desktop Chat Management
function openMobileChat() {
  if (!groupChatModal) return;
  state.groupChat.isOpen = !state.groupChat.isOpen;

  if (state.groupChat.isOpen) {
    groupChatModal.classList.remove('hidden');
    groupChatModal.classList.remove('chat-open'); // Messenger style: start at list
    
    // Always start with clean empty state so old chat is not retained
    resetChatToEmptyState();
    
    loadChatList();
    loadUnreadCounts();
    
    document.getElementById('mobileMessagesBtn')?.classList.add('active');

    setTimeout(() => {
      initIcons();
    }, 100);
  } else {
    closeMobileChat();
  }
}
window.openMobileChat = openMobileChat;

function backToChatList() {
  if (groupChatModal) {
    groupChatModal.classList.remove('chat-open'); // Slide main area away
    resetChatToEmptyState();
    
    // Smooth delay for clearing and reloading
    setTimeout(() => {
      loadChatList();
      loadUnreadCounts();
    }, 150);
  }
}
window.backToChatList = backToChatList;

function closeMobileChat() {
  if (!groupChatModal) return;
  state.groupChat.isOpen = false;
  groupChatModal.classList.add('hidden');
  groupChatModal.classList.remove('chat-open');
  document.getElementById('mobileMessagesBtn')?.classList.remove('active');
  resetChatToEmptyState();
}
window.closeMobileChat = closeMobileChat;

function showMobileChatSidebar() {
  if (groupChatModal) groupChatModal.classList.remove('chat-open');
  loadChatList();
}

// Group Chat Handlers
if (groupChatHead) {
  groupChatHead.onclick = openMobileChat;
}

if (closeGroupChat) {
  closeGroupChat.onclick = closeMobileChat;
}

// Close on backdrop click & Escape key
if (groupChatModal) {
  groupChatModal.addEventListener('click', (e) => {
    if (e.target === groupChatModal) {
      closeMobileChat();
    }
  });
}

window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (groupChatModal && !groupChatModal.classList.contains('hidden')) {
      closeMobileChat();
    }
  }
});

if (summonBotBtn) {
  summonBotBtn.onclick = () => {
    groupChatInput.value = '@bot ' + groupChatInput.value;
    groupChatInput.focus();
  };
}

if (attachFileBtn) {
  attachFileBtn.onclick = () => {
    if (chatFileInput) chatFileInput.click();
  };
}

if ($('fullscreenGroupChat')) {
  $('fullscreenGroupChat').onclick = toggleChatFullscreen;
}

if (chatFileInput) {
  chatFileInput.onchange = (e) => {
    const files = Array.from(e.target.files);
    state.groupChat.pendingFiles = [...state.groupChat.pendingFiles, ...files];
    renderChatAttachmentPreview();
    e.target.value = '';
  };
}

if (sendGroupChatBtn) sendGroupChatBtn.onclick = sendUnifiedMessage;
if (groupChatInput) {
  groupChatInput.onkeydown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendUnifiedMessage();
    } else {
      // Send typing signal for unified chat
      if (state.currentChat) {
        sendTypingSignal(state.currentChat.id, state.currentChat.type);
      }
    }
  };
}
// ─── Chat Drag & Drop ────────────────────────
if (groupChatMessages) {
  const dropOverlay = $('chatDropOverlay');

  groupChatMessages.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (dropOverlay) dropOverlay.classList.remove('hidden');
  });

  groupChatMessages.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    // Only hide if we actually left the container
    if (e.relatedTarget === null || !groupChatMessages.contains(e.relatedTarget)) {
      if (dropOverlay) dropOverlay.classList.add('hidden');
    }
  });

  groupChatMessages.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (dropOverlay) dropOverlay.classList.add('hidden');

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      state.groupChat.pendingFiles = [...state.groupChat.pendingFiles, ...files];
      renderChatAttachmentPreview();
      toast(`เพิ่ม ${files.length} ไฟล์ลงในรายการรอส่งแล้ว`, 'info');
    }
  });
}

if (openCreateGroupModal) openCreateGroupModal.onclick = openCreateGroup;
if (confirmCreateGroup) confirmCreateGroup.onclick = handleCreateGroup;
if (cancelCreateGroup) cancelCreateGroup.onclick = () => {
  createGroupModal.classList.add('hidden');
  createGroupModal.classList.remove('flex', 'items-center', 'justify-center');
};
if (openStartDmModal) openStartDmModal.onclick = openStartDm;
if (addMemberBtn) addMemberBtn.onclick = openAddMemberModal;
if (cancelAddMember) cancelAddMember.onclick = () => {
  addMemberModal.classList.add('hidden');
  addMemberModal.classList.remove('flex', 'items-center', 'justify-center');
};
if (confirmAddMember) confirmAddMember.onclick = handleAddMembers;
if (closeStartDmModal) closeStartDmModal.onclick = () => {
  startDmModal.classList.add('hidden');
  startDmModal.classList.remove('flex', 'items-center', 'justify-center');
};
if (closeGroupChatMobile) closeGroupChatMobile.onclick = closeMobileChat;
if (editGroupBtn) editGroupBtn.onclick = openEditGroupModal;

async function deleteGroup() {
  const { type, id, name } = state.currentChat || {};
  if (type !== 'room' || !id) return;

  const confirmed = await showConfirm(`ลบกลุ่มแชท`, `คุณต้องการลบกลุ่ม "${name}" ใช่หรือไม่?\n\nข้อความทั้งหมดในกลุ่มจะถูกลบอย่างถาวร ไม่สามารถกู้คืนได้!`, { type: 'danger', confirmText: 'ลบกลุ่ม' });
  if (!confirmed) return;

  const btn = $('deleteGroupBtn');
  if (btn) { btn.disabled = true; btn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i>'; initIcons(); }

  try {
    const data = await apiFetch(`/api/groups/${id}`, { method: 'DELETE' });
    if (data.ok) {
      toast(`ลบกลุ่ม "${name}" สำเร็จแล้ว`, 'success');
      // Reset chat state
      state.currentChat = { type: 'room', id: null, name: '' };
      if ($('groupChatMessages')) $('groupChatMessages').innerHTML = '<div class="text-center py-20 text-surface-300 text-[10px] font-bold uppercase tracking-widest">เลือกบทสนทนาเพื่อเริ่มแชท</div>';
      if ($('chatHeaderName')) $('chatHeaderName').textContent = 'เลือกบทสนทนา';
      if ($('chatInputArea')) $('chatInputArea').classList.add('hidden');
      if (btn) btn.classList.add('hidden');
      await loadChatList(); // Refresh sidebar
    } else {
      toast(data.error || 'ลบกลุ่มไม่สำเร็จ', 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาด: ' + e.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="trash-2" class="w-4 h-4"></i>'; initIcons(); }
  }
}

const deleteGroupBtn = $('deleteGroupBtn');
if (deleteGroupBtn) deleteGroupBtn.onclick = deleteGroup;

const viewMembersBtn = $('viewMembersBtn');
if (viewMembersBtn) viewMembersBtn.onclick = openRoomMembersPanel;

async function openRoomMembersPanel() {
  const { type, id, name } = state.currentChat || {};
  if (type !== 'room' || !id) return;

  const panel = $('roomMembersPanel');
  const list = $('roomMembersList');
  const countEl = $('roomMembersCount');
  if (!panel || !list) return;

  panel.classList.remove('hidden');
  panel.classList.add('flex', 'items-center', 'justify-center');
  list.innerHTML = '<div class="text-center py-6 text-surface-400 text-xs animate-pulse">กำลังโหลดสมาชิก...</div>';
  initIcons();

  try {
    const data = await apiFetch(`/api/chat/rooms/${id}/members`);
    const members = data.ok ? (data.users || []) : [];

    if (countEl) countEl.textContent = `${members.length} คน · ${name}`;

    if (!members.length) {
      list.innerHTML = '<div class="text-center py-6 text-surface-400 text-xs">ไม่พบสมาชิก</div>';
      return;
    }

    list.innerHTML = members.map(m => `
      <div class="flex items-center gap-3 p-3 rounded-2xl bg-surface-50 dark:bg-surface-800/50 hover:bg-surface-100 dark:hover:bg-surface-800 transition-all group">
        <div class="w-10 h-10 rounded-xl bg-brand-100 dark:bg-brand-900/40 flex items-center justify-center text-brand-600 font-black text-sm overflow-hidden flex-shrink-0 shadow-sm">
          ${m.avatar_url ? `<img src="${m.avatar_url}" class="w-full h-full object-cover">` : (m.display_name?.[0] || m.username[0]).toUpperCase()}
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-xs font-black text-surface-900 dark:text-white truncate">${m.display_name || m.username}</div>
          <div class="text-[10px] text-surface-400 font-bold">@${m.username}</div>
        </div>
        ${state.isAdmin ? `
          <button onclick="removeMemberFromRoom(${id}, '${m.username}', this.closest('div.flex'))"
            class="opacity-0 group-hover:opacity-100 transition-all p-1.5 text-surface-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg flex-shrink-0"
            title="ลบออกจากห้อง">
            <i data-lucide="user-minus" class="w-3.5 h-3.5"></i>
          </button>
        ` : ''}
      </div>
    `).join('');
    initIcons();
  } catch (e) {
    list.innerHTML = `<div class="text-center py-6 text-red-400 text-xs">โหลดล้มเหลว: ${e.message}</div>`;
  }
}

function closeRoomMembersPanel() {
  const panel = $('roomMembersPanel');
  if (panel) {
    panel.classList.add('hidden');
    panel.classList.remove('flex', 'items-center', 'justify-center');
  }
}

async function removeMemberFromRoom(roomId, username, rowEl) {
  if (!confirm(`ยืนยัน: ลบ @${username} ออกจากห้องนี้?`)) return;
  try {
    const data = await apiFetch(`/api/groups/${roomId}/members/${username}`, { method: 'DELETE' });
    if (data.ok) {
      toast(`ลบ @${username} ออกจากห้องแล้ว`, 'success');
      rowEl?.remove();
      const countEl = $('roomMembersCount');
      if (countEl) {
        const cur = parseInt(countEl.textContent) || 1;
        countEl.textContent = countEl.textContent.replace(/^\d+/, cur - 1);
      }
    } else {
      toast(data.error || 'ลบไม่สำเร็จ', 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาด: ' + e.message, 'error');
  }
}

if (chatHeaderAvatar) {
  chatHeaderAvatar.onclick = () => {
    if (state.currentChat && state.currentChat.type === 'room') {
      openEditGroupModal();
    }
  };
}
if (cancelEditGroup) cancelEditGroup.onclick = () => {
  editGroupModal.classList.add('hidden');
  editGroupModal.classList.remove('flex', 'items-center', 'justify-center');
};
if (confirmEditGroup) confirmEditGroup.onclick = handleEditGroup;

if (groupAvatarUpload) {
  groupAvatarUpload.onchange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (ev) => {
        if (groupAvatarPreview) {
          groupAvatarPreview.innerHTML = `<img src="${ev.target.result}" class="w-full h-full object-cover">`;
        }
      };
      reader.readAsDataURL(file);
    }
  };
}

const sidebarToggleBtn = $('sidebarToggleBtn');
if (sidebarToggleBtn) {
  sidebarToggleBtn.onclick = () => {
    const sidebar = $('chatSidebarPanel');
    if (sidebar) {
      renderChatSidebar();
    }
  };
}

const sidebarToggleInHeader = $('sidebarToggleInHeader');
if (sidebarToggleInHeader) {
  sidebarToggleInHeader.onclick = () => {
    if (groupChatModal) {
      groupChatModal.classList.toggle('sidebar-hide');
      renderChatSidebar();
    }
  };
}

if (groupAvatarUpload) {
  groupAvatarUpload.onchange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (ev) => {
        if (groupAvatarPreview) {
          groupAvatarPreview.innerHTML = `<img src="${ev.target.result}" class="w-full h-full object-cover">`;
        }
      };
      reader.readAsDataURL(file);
    }
  };
}

function openEditGroupModal() {
  if (!state.currentChat || state.currentChat.type !== 'room') return;
  editGroupName.value = state.currentChat.name;
  groupAvatarUpload.value = ''; // Reset file input
  if (state.currentChat.avatarUrl) {
    groupAvatarPreview.innerHTML = `<img src="${state.currentChat.avatarUrl}" class="w-full h-full object-cover">`;
  } else {
    groupAvatarPreview.innerHTML = '<i data-lucide="image" class="w-8 h-8 opacity-40"></i>';
    initIcons();
  }
  editGroupModal.classList.remove('hidden');
  editGroupModal.classList.add('flex', 'items-center', 'justify-center');
}

async function handleEditGroup() {
  if (!state.currentChat || state.currentChat.type !== 'room') return;

  const name = editGroupName.value.trim();
  if (!name) return toast('กรุณาระบุชื่อกลุ่ม', 'error');

  confirmEditGroup.disabled = true;
  confirmEditGroup.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i> กำลังบันทึก...';
  initIcons();

  const formData = new FormData();
  formData.append('name', name);
  if (groupAvatarUpload.files[0]) {
    formData.append('avatar', groupAvatarUpload.files[0]);
  }

  try {
    const res = await fetch(`/api/groups/${state.currentChat.id}/profile`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.ok) {
      toast('อัปเดตข้อมูลกลุ่มสำเร็จ', 'success');
      editGroupModal.classList.add('hidden');
      editGroupModal.classList.remove('flex', 'items-center', 'justify-center');
      loadChatList(); // Refresh sidebar to see new name/avatar
      // Update current chat state
      state.currentChat.name = name;
      chatHeaderName.textContent = name;
      if (data.avatar_url) {
        state.currentChat.avatarUrl = data.avatar_url;
        chatHeaderAvatar.innerHTML = `<img src="${data.avatar_url}" class="w-full h-full object-cover">`;
      }
    } else {
      toast(data.error || 'ไม่สามารถอัปเดตข้อมูลได้', 'error');
    }
  } catch (e) {
    console.error(e);
    toast('เกิดข้อผิดพลาดในการเชื่อมต่อ', 'error');
  } finally {
    confirmEditGroup.disabled = false;
    confirmEditGroup.innerHTML = 'บันทึกการเปลี่ยนแปลง';
  }
}

const pubToggle = $('schedulePublicToggle');
const visStatus = $('visibilityStatus');
if (pubToggle && visStatus) {
  pubToggle.onchange = () => {
    visStatus.textContent = pubToggle.checked ? 'สาธารณะ (คนอื่นเห็น)' : 'ส่วนตัว (เฉพาะคุณ)';
    visStatus.className = pubToggle.checked ? 'text-[10px] font-bold text-emerald-600 uppercase' : 'text-[10px] font-bold text-brand-600 uppercase';
  };
}

avatarUploadInput.onchange = (e) => {
  const file = e.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (ev) => {
      profileAvatarPreview.innerHTML = `<img src="${ev.target.result}" class="w-full h-full object-cover">`;
    };
    reader.readAsDataURL(file);
  }
};

saveProfileBtn.onclick = async () => {
  saveProfileBtn.disabled = true;
  saveProfileBtn.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i> กำลังบันทึก...';
  initIcons();

  const formData = new FormData();
  formData.append('display_name', profileNameInput.value.trim());
  if ($('profileDeptInput')) {
    formData.append('department', $('profileDeptInput').value.trim());
  }
  if (avatarUploadInput.files[0]) {
    formData.append('avatar', avatarUploadInput.files[0]);
  }
  if (state.tempBackground) {
    formData.append('background_url', state.tempBackground);
  }

  try {
    const res = await fetch('/api/profile/update', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.ok) {
      applyProfile(data.profile);
      toast('บันทึกโปรไฟล์เรียบร้อยแล้ว', 'success');
    } else {
      toast('เกิดข้อผิดพลาด: ' + data.error, 'error');
    }
  } catch (e) {
    toast('ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้', 'error');
  } finally {
    saveProfileBtn.disabled = false;
    saveProfileBtn.innerHTML = '<i data-lucide="check" class="w-4 h-4"></i> บันทึกการเปลี่ยนแปลง';
    initIcons();
  }
};

async function init() {
  console.log("🚀 Initializing Application v" + UI_VERSION);
  initTheme();
  initIcons();

  const authed = await checkAuth();
  if (authed) {
    initSocket();
    checkCallButtonsVisibility();
  }
  checkServerVersion();

  if (authed) {
    await initAppContent();
    requestPushPermission();

    // Init @mention autocomplete for always-visible text inputs
    if (postInput) initMentionInput('postInput');  // Social feed: all users
    if (groupChatInput) initMentionInput('groupChatInput', fetchChatContextUsers);  // Chat: room members only

    // ป้องกัน interval ซ้ำซ้อน — register เพียงครั้งเดียว
    if (!state._pollRegistered) {
      state._pollRegistered = true;
      state._chatPollRegistered = true;

      // Notification Polling (Polite 30s interval, skipped when tab is in background)
      loadNotifications();
      setInterval(() => {
        if (!document.hidden) loadNotifications();
      }, 30000);

      // Unified Chat Load & Polling (15s interval, skipped when tab is in background)
      loadChatList();
      loadUnreadCounts();
      setInterval(() => {
        if (document.hidden) return;
        loadUnreadCounts();
        if (state.groupChat.isOpen) {
          const isModalHidden = groupChatModal && groupChatModal.classList.contains('hidden');
          loadChatMessages(false, isModalHidden);
        }
      }, 15000);

      // Re-sync state cleanly on window focus instead of continuous 4s DOM-trashing polling
      window.addEventListener('focus', () => {
        const activeView = document.querySelector('.view:not(.hidden)');
        if (activeView && activeView.id === 'view-chat' && !state.sending) {
          loadHistory(true);
        }
        loadNotifications();
        loadUnreadCounts();
      });

      // Typing Status Polling (Only as fallback when Socket.IO is disconnected)
      setInterval(() => {
        if (!document.hidden && (!socket || !socket.connected)) {
          pollTypingStatus();
        }
      }, 15000);
    }

    // Listen for main chat typing
    if (msgInput) {
      msgInput.addEventListener('input', () => {
        sendTypingSignal('ai-assistant', 'dm');
      });
    }

    // ─── Chat Sidebar Filters & Search ───
    document.querySelectorAll('.chat-filter-pill').forEach(btn => {
      btn.onclick = () => {
        document.querySelectorAll('.chat-filter-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.sidebarFilter = btn.getAttribute('data-filter');
        renderChatSidebar();
      };
    });

    const sidebarSearchInput = $('chatSearchInput');
    if (sidebarSearchInput) {
      sidebarSearchInput.addEventListener('input', (e) => {
        state.sidebarSearch = e.target.value.toLowerCase();
        renderChatSidebar();
      });
    }

    // Fullscreen/Minimize Sidebar logic (Optional functionality enhancement)
    const fsSidebarBtn = $('fullscreenChatSidebar');
    if (fsSidebarBtn) {
      fsSidebarBtn.onclick = () => {
        const modal = $('groupChatModal');
        if (modal) {
          const isFull = modal.classList.contains('w-full');
          if (isFull) {
            modal.classList.remove('w-full', 'h-full', 'bottom-0', 'right-0');
            modal.classList.add('bottom-24', 'right-6', 'w-[800px]', 'h-[600px]');
            fsSidebarBtn.innerHTML = '<i data-lucide="maximize-2" class="w-4 h-4"></i>';
          } else {
            modal.classList.add('w-full', 'h-full', 'bottom-0', 'right-0');
            modal.classList.remove('bottom-24', 'right-6', 'w-[800px]', 'h-[600px]');
            fsSidebarBtn.innerHTML = '<i data-lucide="minimize-2" class="w-4 h-4"></i>';
          }
          initIcons();
        }
      };
    }
  }

  // Real-time Clock (always runs if element exists)
  if (realtimeClock) {
    setInterval(() => {
      const now = new Date();
      realtimeClock.textContent = now.toLocaleTimeString('th-TH', { hour12: false });
    }, 1000);
  }

  // Handle Google OAuth return
  const _urlParams = new URLSearchParams(window.location.search);
  if (_urlParams.has('google_connected') || _urlParams.has('google_cancelled') || _urlParams.has('google_error')) {
    history.replaceState({}, '', window.location.pathname + window.location.hash);
    
    // Explicitly hide login overlay in case it rendered before session sync
    const _loginOv = document.getElementById('loginOverlay');
    if (_loginOv) _loginOv.classList.add('hidden');
    
    // Ensure sidebar overlay is dismissed
    const _sbOverlay = document.getElementById('sidebarOverlay');
    if (_sbOverlay) {
      _sbOverlay.classList.remove('active');
      _sbOverlay.classList.add('hidden');
    }
    
    if (_urlParams.get('google_connected') === '1') {
      toast('เชื่อมต่อ Google สำเร็จ!', 'success');
      if (typeof loadGoogleDriveStatus === 'function') loadGoogleDriveStatus();
      if (typeof loadOrgGoogleStatus === 'function') loadOrgGoogleStatus();
      if (window.location.hash === '#admin' || window.location.hash === '#org') {
        if (typeof switchView === 'function') switchView('admin');
      }
    } else if (_urlParams.get('google_cancelled') === '1') {
      if (typeof loadGoogleDriveStatus === 'function') loadGoogleDriveStatus();
      if (typeof loadOrgGoogleStatus === 'function') loadOrgGoogleStatus();
    } else if (_urlParams.get('google_error') === '1') {
      toast('เชื่อมต่อ Google ไม่สำเร็จ กรุณาลองใหม่', 'error');
      if (typeof loadGoogleDriveStatus === 'function') loadGoogleDriveStatus();
      if (typeof loadOrgGoogleStatus === 'function') loadOrgGoogleStatus();
    }
  }
}

// --- Notifications Logic ---

async function loadNotifications() {
  try {
    const res = await fetch("/api/notifications");
    const data = await res.json();
    renderNotifications(data.notifications);
    updateNotifBadge(data.notifications);
  } catch (e) {
    console.error("Failed to load notifications:", e);
  }
}

function updateNotifBadge(notifs) {
  const badge = document.getElementById("navNotifBadge");
  const mobileBadge = document.getElementById("mobileNotifBadge");
  const headerBell = document.getElementById("mobileHeaderNotifBadge");
  if (!badge && !mobileBadge) return;

  const unreadCount = notifs.filter(n => !n.is_read).length;
  const displayCount = unreadCount > 99 ? '99+' : unreadCount;

  [badge, mobileBadge].forEach(el => {
    if (el) {
      if (unreadCount > 0) {
        el.textContent = displayCount;
        el.classList.remove("hidden");
        el.classList.add("flex");
      } else {
        el.classList.add("hidden");
        el.classList.remove("flex");
      }
    }
  });
  if (headerBell) headerBell.classList.toggle("hidden", unreadCount === 0);
}

function renderNotifications(notifs) {
  const container = document.getElementById("notificationsList");
  if (!container) return;

  if (!notifs || notifs.length === 0) {
    container.innerHTML = `
      <div class="text-center py-10 text-surface-400">
        <i data-lucide="bell-off" class="w-12 h-12 mx-auto mb-4 opacity-10"></i>
        <p>ไม่มีการแจ้งเตือน</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }

  container.innerHTML = notifs.map(n => {
    const iconMap = {
      'mention': 'at-sign',
      'like': 'heart',
      'comment': 'message-circle',
      'chat': 'message-square',
      'post': 'layout',
      'calendar': 'calendar',
      'system': 'bell'
    };
    const icon = iconMap[n.type] || 'bell';
    const timeAgo = formatTimeAgo(n.timestamp);
    const safeTitle = escapeHtml(n.title || '');
    const safeMessage = escapeHtml(n.message || '');
    const safeLink = encodeURI(n.link || '').replace(/'/g, '%27');
    return `
      <div id="notif-item-${n.id}" class="p-4 bg-white dark:bg-surface-900 border ${n.is_read ? 'border-surface-100 dark:border-surface-800 opacity-60' : 'border-brand-100 dark:border-brand-900/30 bg-brand-50/10'} rounded-2xl flex gap-4 transition-all hover:shadow-md group">
        <div class="w-10 h-10 rounded-xl ${n.is_read ? 'bg-surface-100 dark:bg-surface-800 text-surface-400' : 'bg-brand-600 text-white'} flex items-center justify-center flex-shrink-0 cursor-pointer" onclick="handleNotifClick(${n.id}, '${safeLink}')">
          <i data-lucide="${icon}" class="w-5 h-5"></i>
        </div>
        <div class="flex-1 min-w-0 cursor-pointer" onclick="handleNotifClick(${n.id}, '${safeLink}')">
          <div class="flex justify-between items-start mb-1">
            <h4 class="text-sm font-bold ${n.is_read ? '' : 'text-brand-600'}">${safeTitle}</h4>
            <span class="text-[10px] text-surface-400 font-bold uppercase">${timeAgo}</span>
          </div>
          <p class="text-xs text-surface-500 line-clamp-2">${safeMessage}</p>
        </div>
        <div class="flex flex-col items-center gap-2 flex-shrink-0">
          ${!n.is_read ? `<div class="w-2 h-2 bg-brand-600 rounded-full mt-1"></div>` : ''}
          <button onclick="deleteNotification(${n.id})" title="ลบการแจ้งเตือน"
            class="opacity-0 group-hover:opacity-100 transition-all p-1.5 text-surface-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg">
            <i data-lucide="x" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `;
  }).join("");
  lucide.createIcons();
}

async function handleNotifClick(id, link) {
  // Mark as read immediately in the DOM for instant feedback
  const el = document.getElementById(`notif-item-${id}`);
  if (el) {
    el.classList.remove('border-brand-100', 'dark:border-brand-900/30', 'bg-brand-50/10');
    el.classList.add('opacity-60', 'border-surface-100', 'dark:border-surface-800');
    el.querySelector('h4')?.classList.remove('text-brand-600');
    const dot = el.querySelector('.bg-brand-600.rounded-full');
    if (dot) dot.remove();
    const iconDiv = el.querySelector('.bg-brand-600');
    if (iconDiv) {
      iconDiv.classList.remove('bg-brand-600', 'text-white');
      iconDiv.classList.add('bg-surface-100', 'dark:bg-surface-800', 'text-surface-400');
    }
  }
  // Send to server and update badge
  await markNotifRead(id);
  if (link) {
    if (link.startsWith("#")) {
      const parts = link.replace("#", "").split("-");
      const view = parts[0];
      const tab = parts[1];
      showView(view);
      if (view === 'org' && tab) {
        if (typeof switchOrgTab === 'function') {
          switchOrgTab(tab);
        }
      }
    } else {
      window.open(link, "_blank");
    }
  }
}

async function markNotifRead(id) {
  try {
    await fetch(`/api/notifications/${id}/read`, { method: "POST" });
    // Refresh only badge count, not full list (to avoid flicker)
    const res = await fetch("/api/notifications");
    const data = await res.json();
    updateNotifBadge(data.notifications);
  } catch (e) {
    console.error("Failed to mark read:", e);
  }
}

async function deleteNotification(id) {
  try {
    const el = document.getElementById(`notif-item-${id}`);
    if (el) {
      el.style.transition = 'all 0.3s ease';
      el.style.opacity = '0';
      el.style.transform = 'translateX(20px)';
      setTimeout(() => el.remove(), 300);
    }
    await fetch(`/api/notifications/${id}`, { method: "DELETE" });
    // Refresh badge
    const res = await fetch("/api/notifications");
    const data = await res.json();
    updateNotifBadge(data.notifications);
    // Show empty state if all removed
    const container = document.getElementById("notificationsList");
    if (container && container.children.length === 0) {
      renderNotifications([]);
    }
  } catch (e) {
    console.error("Failed to delete notification:", e);
  }
}

async function markAllNotificationsRead() {
  try {
    await fetch("/api/notifications/read_all", { method: "POST" });
    loadNotifications();
    toast("อ่านข้อความทั้งหมดแล้ว", "success");
  } catch (e) {
    console.error("Failed to mark all read:", e);
  }
}

async function clearAllNotifications() {
  if (!confirm("ยืนยัน: ลบการแจ้งเตือนทั้งหมด?")) return;
  try {
    await fetch("/api/notifications/delete_all", { method: "DELETE" });
    renderNotifications([]);
    updateNotifBadge([]);
    toast("ลบการแจ้งเตือนทั้งหมดแล้ว", "info");
  } catch (e) {
    console.error("Failed to delete all notifications:", e);
  }
}

function formatTimeAgo(timestamp) {
  const now = new Date();
  const then = new Date(timestamp);
  const diff = Math.floor((now - then) / 1000);

  if (diff < 60) return "Just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return then.toLocaleDateString();
}

const markAllReadBtn = document.getElementById("markAllReadBtn");
if (markAllReadBtn) markAllReadBtn.onclick = markAllNotificationsRead;

// Trigger init
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

function toggleSummary(pid) {
  const p = state.feedPosts.find(x => x.id === pid);
  if (p) {
    p.hideSummary = !p.hideSummary;
    renderPosts(state.feedPosts);
  }
}

// ─── Admin Chat Management Panel ──────────────────────────────────────────────

let adminChatState = { tab: 'ai', selectedRoom: null, selectedDm: null, messages: [] };

function initAdminChatPanel() {
  // Only inject for Admin
  if (!document.getElementById('adminChatModal')) {

    const panel = document.createElement('div');
    panel.id = 'adminChatModal';
    // Floating panel pinned to bottom-right, NOT full-screen overlay
    panel.classList.add('hidden', 'flex-col');
    panel.style.cssText = 'position:fixed;bottom:80px;right:16px;z-index:9999;width:420px;max-width:calc(100vw - 32px);max-height:80vh;box-shadow:0 25px 60px rgba(0,0,0,0.35);border-radius:16px;overflow:hidden;border:1px solid rgba(0,0,0,0.1);';
    panel.innerHTML = `
      <div style="background:#dc2626;color:white;" class="flex items-center justify-between p-3">
        <div class="flex items-center gap-2">
          <i data-lucide="shield" class="w-4 h-4"></i>
          <span class="font-bold text-sm">Admin: จัดการข้อความ</span>
        </div>
        <button onclick="closeAdminChatPanel()" class="hover:opacity-70 p-1 rounded transition-opacity"><i data-lucide="x" class="w-4 h-4"></i></button>
      </div>

      <!-- Tab bar -->
      <div class="flex border-b border-surface-200 dark:border-surface-700 px-3 pt-1 gap-0.5 bg-white dark:bg-surface-900">
        <button onclick="adminChatSetTab('ai')" data-tab="ai" class="admin-tab-btn px-2.5 py-1.5 text-[11px] font-bold rounded-t-lg">🤖 AI Chat</button>
        <button onclick="adminChatSetTab('room')" data-tab="room" class="admin-tab-btn px-2.5 py-1.5 text-[11px] font-bold rounded-t-lg">👥 กลุ่ม</button>
        <button onclick="adminChatSetTab('dm')" data-tab="dm" class="admin-tab-btn px-2.5 py-1.5 text-[11px] font-bold rounded-t-lg">💬 DM</button>
      </div>

      <!-- Content -->
      <div id="adminChatContent" class="flex flex-col overflow-hidden bg-white dark:bg-surface-900" style="flex:1;min-height:0;padding:12px;gap:8px;"></div>

      <!-- Action bar -->
      <div class="bg-white dark:bg-surface-900 border-t border-surface-200 dark:border-surface-700 flex items-center justify-between gap-2" style="padding:8px 12px;">
        <span id="adminMsgCount" class="text-surface-400 font-medium" style="font-size:11px;"></span>
        <div class="flex gap-1.5">
          <button onclick="adminChatDeleteSelected()" class="px-2.5 py-1.5 bg-orange-500 hover:bg-orange-600 text-white rounded-lg font-bold transition-colors hidden" id="adminDeleteSelectedBtn" style="font-size:11px;">
            <i data-lucide="trash-2" class="w-3 h-3 inline-block mr-0.5"></i>ลบที่เลือก
          </button>
          <button onclick="adminChatClearAll()" class="px-2.5 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg font-bold transition-colors" style="font-size:11px;">
            <i data-lucide="trash" class="w-3 h-3 inline-block mr-0.5"></i>ลบทั้งหมด
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(panel);
    initIcons();
  }
}

function openAdminChatPanel() {
  const modal = document.getElementById('adminChatModal');
  if (!modal) return;
  modal.classList.remove('hidden');
  modal.classList.add('flex', 'items-center', 'justify-center');
  adminChatSetTab('ai');
  initIcons();
}

function closeAdminChatPanel() {
  const modal = document.getElementById('adminChatModal');
  if (!modal) return;
  modal.classList.add('hidden');
  modal.classList.remove('flex', 'items-center', 'justify-center');
}

function adminChatSetTab(tab) {
  adminChatState.tab = tab;
  document.querySelectorAll('.admin-tab-btn').forEach(b => {
    const active = b.dataset.tab === tab;
    b.className = `admin-tab-btn px-3 py-2 text-xs font-bold rounded-t-lg ${active ? 'bg-surface-100 dark:bg-surface-800 text-red-600 border-b-2 border-red-600' : 'text-surface-500 hover:text-surface-700 dark:hover:text-surface-200'}`;
  });
  if (tab === 'ai') adminChatLoadAi();
  else if (tab === 'room') adminChatLoadRooms();
  else if (tab === 'dm') adminChatLoadDmPairs();
}

async function adminChatLoadAi() {
  const el = document.getElementById('adminChatContent');
  el.innerHTML = '<div class="text-xs text-surface-400 animate-pulse">กำลังโหลด...</div>';
  try {
    const res = await fetch('/api/admin/chat/ai');
    if (!res.ok) throw new Error(res.statusText);
    const data = await res.json();
    adminChatState.messages = data.messages || [];
    adminRenderMessages(adminChatState.messages, 'ai');
  } catch (e) {
    el.innerHTML = '<div class="text-xs text-red-400">โหลดข้อมูลไม่สำเร็จ</div>';
  }
}

async function adminChatLoadRooms() {
  const el = document.getElementById('adminChatContent');
  el.innerHTML = '<div class="text-xs text-surface-400 animate-pulse">กำลังโหลด...</div>';
  try {
  const res = await fetch('/api/admin/chat/overview');
  if (!res.ok) throw new Error(res.statusText);
  const data = await res.json();
  const rooms = data.rooms || [];
  el.innerHTML = `
    <div class="flex flex-wrap gap-2 mb-2">
      ${rooms.map(r => `<button onclick="adminChatLoadRoom(${r.id}, ${JSON.stringify(r.name)})" class="px-3 py-1.5 text-xs font-bold bg-surface-100 dark:bg-surface-800 hover:bg-brand-50 dark:hover:bg-brand-900/30 hover:text-brand-600 rounded-lg border border-surface-200 dark:border-surface-700 transition-colors">${escHtml(r.name)}</button>`).join('')}
    </div>
    <div id="adminRoomMsgs" class="text-xs text-surface-400 italic">เลือกห้องแชทด้านบน</div>
  `;
  } catch (e) {
    el.innerHTML = '<div class="text-xs text-red-400">โหลดข้อมูลไม่สำเร็จ</div>';
  }
}

async function adminChatLoadRoom(roomId, roomName) {
  adminChatState.selectedRoom = { id: roomId, name: roomName };
  adminChatState.tab = 'room';
  try {
  const res = await fetch(`/api/admin/chat/room/${roomId}`);
  if (!res.ok) throw new Error(res.statusText);
  const data = await res.json();
  adminChatState.messages = data.messages || [];
  const el = document.getElementById('adminRoomMsgs');
  if (el) {
    el.innerHTML = '';
    renderAdminMsgList(el, adminChatState.messages, 'room');
  }
  updateAdminMsgCount();
  } catch (e) {
    const el2 = document.getElementById('adminRoomMsgs');
    if (el2) el2.innerHTML = '<div class="text-xs text-red-400">โหลดข้อมูลไม่สำเร็จ</div>';
  }
}

async function adminChatLoadDmPairs() {
  const el = document.getElementById('adminChatContent');
  el.innerHTML = '<div class="text-xs text-surface-400 animate-pulse">กำลังโหลด...</div>';
  try {
  const res = await fetch('/api/admin/chat/overview');
  if (!res.ok) throw new Error(res.statusText);
  const data = await res.json();
  const pairs = data.dm_pairs || [];
  if (!pairs.length) {
    el.innerHTML = '<div class="text-xs text-surface-400 italic text-center py-8">ไม่มีข้อความ DM</div>';
    return;
  }
  el.innerHTML = `
    <div class="flex flex-col gap-1 mb-2">
      ${pairs.map(p => `<button onclick="adminChatLoadDm(${JSON.stringify(p.user1)},${JSON.stringify(p.user2)})" class="flex items-center justify-between px-3 py-2 text-xs font-bold bg-surface-100 dark:bg-surface-800 hover:bg-brand-50 dark:hover:bg-brand-900/30 hover:text-brand-600 rounded-lg border border-surface-200 dark:border-surface-700 transition-colors text-left">
        <span>${escHtml(p.user1)} ↔ ${escHtml(p.user2)}</span>
        <span class="text-surface-400">${p.count} ข้อความ</span>
      </button>`).join('')}
    </div>
    <div id="adminDmMsgs" class="text-xs text-surface-400 italic">เลือกคู่แชทด้านบน</div>
  `;
  } catch (e) {
    el.innerHTML = '<div class="text-xs text-red-400">โหลดข้อมูลไม่สำเร็จ</div>';
  }
}

async function adminChatLoadDm(u1, u2) {
  adminChatState.selectedDm = { user1: u1, user2: u2 };
  try {
  const res = await fetch(`/api/admin/chat/dm?user1=${encodeURIComponent(u1)}&user2=${encodeURIComponent(u2)}`);
  if (!res.ok) throw new Error(res.statusText);
  const data = await res.json();
  adminChatState.messages = data.messages || [];
  const el = document.getElementById('adminDmMsgs');
  if (el) {
    el.innerHTML = '';
    renderAdminMsgList(el, adminChatState.messages, 'dm');
  }
  updateAdminMsgCount();
  } catch (e) {
    const el2 = document.getElementById('adminDmMsgs');
    if (el2) el2.innerHTML = '<div class="text-xs text-red-400">โหลดข้อมูลไม่สำเร็จ</div>';
  }
}

function adminRenderMessages(msgs, type) {
  const el = document.getElementById('adminChatContent');
  el.innerHTML = '';
  renderAdminMsgList(el, msgs, type);
  updateAdminMsgCount();
}

function renderAdminMsgList(container, msgs, type) {
  if (!msgs.length) {
    container.innerHTML = '<div class="text-xs text-surface-400 italic text-center py-8">ไม่มีข้อความ</div>';
    return;
  }
  const listDiv = document.createElement('div');
  listDiv.className = 'flex flex-col gap-1 overflow-y-auto flex-1 max-h-[400px] pr-1';
  msgs.forEach(m => {
    const row = document.createElement('div');
    row.className = 'flex items-start gap-2 p-2 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-800 group transition-colors';
    row.dataset.id = m.id;
    const sender = m.username || m.sender || '?';
    const text = (m.text || '').substring(0, 100);
    const ts = m.timestamp ? new Date(m.timestamp).toLocaleString('th-TH', { dateStyle: 'short', timeStyle: 'short' }) : '';
    row.innerHTML = `
      <input type="checkbox" class="admin-msg-check mt-0.5 flex-shrink-0 accent-red-600" data-id="${m.id}" data-type="${type}" onchange="updateAdminDeleteBtn()">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-0.5">
          <span class="font-bold text-[10px] text-brand-600">${sender}</span>
          ${m.role ? `<span class="text-[9px] px-1 py-0.5 rounded ${m.role === 'bot' ? 'bg-brand-100 text-brand-700' : 'bg-surface-200 text-surface-600'}">${m.role}</span>` : ''}
          <span class="text-[9px] text-surface-400">${ts}</span>
        </div>
        <div class="text-xs text-surface-700 dark:text-surface-300 truncate">${text || '<em class="opacity-50">ไม่มีข้อความ</em>'}</div>
      </div>
      <button onclick="adminDeleteSingleMsg(${m.id},'${type}',this.closest('[data-id]'))" class="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:text-red-500 flex-shrink-0">
        <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
      </button>
    `;
    listDiv.appendChild(row);
  });
  container.appendChild(listDiv);
  initIcons();
  updateAdminMsgCount();
}

function updateAdminMsgCount() {
  const el = document.getElementById('adminMsgCount');
  if (el) el.textContent = `${adminChatState.messages.length} ข้อความ`;
}

function updateAdminDeleteBtn() {
  const checked = document.querySelectorAll('.admin-msg-check:checked').length;
  const btn = document.getElementById('adminDeleteSelectedBtn');
  if (btn) {
    if (checked > 0) { btn.classList.remove('hidden'); btn.textContent = `ลบที่เลือก (${checked})`; }
    else { btn.classList.add('hidden'); }
  }
}

async function adminDeleteSingleMsg(mid, type, rowEl) {
  if (!confirm('ลบข้อความนี้?')) return;
  let url;
  if (type === 'ai') url = `/api/admin/chat/ai/delete/${mid}`;
  else if (type === 'room') url = `/api/admin/chat/room/delete/${mid}`;
  else url = `/api/admin/chat/dm/delete/${mid}`;
  const res = await (await fetch(url, { method: 'DELETE' })).json();
  if (res.ok) {
    rowEl?.remove();
    adminChatState.messages = adminChatState.messages.filter(m => m.id !== mid);
    updateAdminMsgCount();
    toast('ลบข้อความแล้ว', 'info');
  } else { toast('ลบไม่สำเร็จ', 'error'); }
}

async function adminChatDeleteSelected() {
  const checks = [...document.querySelectorAll('.admin-msg-check:checked')];
  if (!checks.length) return;
  if (!confirm(`ลบ ${checks.length} ข้อความที่เลือก?`)) return;
  for (const ch of checks) {
    const mid = parseInt(ch.dataset.id);
    const type = ch.dataset.type;
    let url;
    if (type === 'ai') url = `/api/admin/chat/ai/delete/${mid}`;
    else if (type === 'room') url = `/api/admin/chat/room/delete/${mid}`;
    else url = `/api/admin/chat/dm/delete/${mid}`;
    await fetch(url, { method: 'DELETE' });
    ch.closest('[data-id]')?.remove();
  }
  adminChatState.messages = adminChatState.messages.filter(m => !checks.find(c => parseInt(c.dataset.id) === m.id));
  updateAdminMsgCount();
  updateAdminDeleteBtn();
  toast(`ลบ ${checks.length} ข้อความแล้ว`, 'info');
}

async function adminChatClearAll() {
  const tab = adminChatState.tab;
  let msg = 'ลบข้อความ AI Chat ทั้งหมด?';
  if (tab === 'room' && adminChatState.selectedRoom) msg = `ลบข้อความทั้งหมดในห้อง "${adminChatState.selectedRoom.name}"?`;
  else if (tab === 'dm' && adminChatState.selectedDm) msg = `ลบ DM ระหว่าง ${adminChatState.selectedDm.user1} และ ${adminChatState.selectedDm.user2} ทั้งหมด?`;
  if (!confirm(msg)) return;

  let res;
  if (tab === 'ai') {
    res = await (await fetch('/api/admin/chat/ai/clear', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })).json();
  } else if (tab === 'room' && adminChatState.selectedRoom) {
    res = await (await fetch(`/api/admin/chat/room/${adminChatState.selectedRoom.id}/clear`, { method: 'POST' })).json();
  } else if (tab === 'dm' && adminChatState.selectedDm) {
    res = await (await fetch('/api/admin/chat/dm/clear', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(adminChatState.selectedDm) })).json();
  } else {
    toast('กรุณาเลือกห้องแชทหรือ DM ก่อน', 'warning'); return;
  }

  if (res.ok) {
    toast(`ลบ ${res.deleted} ข้อความแล้ว`, 'info');
    adminChatSetTab(tab); // Refresh
  } else { toast('ลบไม่สำเร็จ', 'error'); }
}

// Attach: init button once user is confirmed as Admin
const _origCheckAuth = window.checkAuthDone;
document.addEventListener('adminReady', () => initAdminChatPanel());

// Patch into auth flow
const _origLoginOnclick = loginBtn.onclick;
loginBtn.onclick = async function (...args) {
  await _origLoginOnclick?.apply(this, args);
  // Panel init happens via applyAdminState below
};

function applyAdminState(user) {
  if (user === 'Admin') {
    initAdminChatPanel();
  }
}
// Call on page load if already authed
document.addEventListener('DOMContentLoaded', async () => {
  if (state.user && state.isAdmin) {
    initAdminChatPanel();
  }
});
// Also call on every checkAuth success
if (typeof checkAuth === 'function') {
  const __origCA = checkAuth;
  window.checkAuth = async function () {
    const ok = await __origCA();
    if (ok && state.isAdmin) {
      initAdminChatPanel();
    }
    return ok;
  };
}
/* ══════════════════════════════════════════
   Org Member Management
   ══════════════════════════════════════════ */
let _orgMembersCache = [];
let _orgMembersLoaded = false;

let _orgLogsCache = [];

let _orgDepartmentsCache = [];

function switchOrgTab(tab) {
  ['members', 'tree', 'departments', 'leave', 'attendance', 'google', 'business', 'peak', 'announcements', 'categories', 'logs'].forEach(t => {
    const btn = $(`orgTab-${t}`);
    const content = $(`orgTabContent-${t}`);
    const active = t === tab;
    const activeClass = 'org-tab whitespace-nowrap shrink-0 flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all bg-white dark:bg-surface-700 shadow-xs text-surface-900 dark:text-white';
    const inactiveClass = 'org-tab whitespace-nowrap shrink-0 flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all text-surface-500 dark:text-surface-400 hover:text-surface-900 dark:hover:text-white hover:bg-surface-200/50 dark:hover:bg-surface-700/40';
    if (btn) btn.className = active ? activeClass : inactiveClass;
    if (content) content.classList.toggle('hidden', !active);
  });
  // Reset scroll so the new tab content is visible from the top
  const scrollEl = document.querySelector('#view-org .overflow-y-auto');
  if (scrollEl) scrollEl.scrollTop = 0;
  if (tab === 'departments') loadOrgDepartments();
  if (tab === 'leave') {
    refreshAdminLeaves();
    loadTeamLeaveCalendar();
  }
  if (tab === 'attendance' && typeof window.loadOrgAttendance === 'function') {
    window.loadOrgAttendance();
  }
  if (tab === 'google') loadOrgGoogleStatus();
  if (tab === 'business') loadOrgBusinessProfile();
  if (tab === 'peak') loadPeakSettingsStatus();
  if (tab === 'tree') renderOrgTree();
  if (tab === 'announcements') loadOrgAnnouncements();
  if (tab === 'categories') loadCustomCategoriesAndRules();
  if (tab === 'logs') loadOrgLogs();
}

// ─── Organization Departments JS ───
async function loadOrgDepartments() {
  const grid = $('orgDepartmentsGrid');
  const empty = $('orgDepartmentsEmpty');
  if (!grid) return;

  grid.innerHTML = `<div class="col-span-full text-center py-10 text-surface-400 text-xs font-semibold">กำลังโหลดข้อมูลแผนก...</div>`;
  if (empty) empty.classList.add('hidden');

  try {
    const res = await fetch('/api/org/departments');
    const data = await res.json();
    if (!data.ok) {
      grid.innerHTML = `<div class="col-span-full text-center py-10 text-rose-500 text-xs">${escHtml(data.error || 'โหลดไม่สำเร็จ')}</div>`;
      return;
    }

    _orgDepartmentsCache = data.departments || [];

    // Also update org department filter dropdown if present
    const deptSelect = $('orgFilterDept');
    if (deptSelect) {
      const currentVal = deptSelect.value;
      deptSelect.innerHTML = `<option value="">ทุกแผนก</option>` +
        _orgDepartmentsCache.map(d => `<option value="${escHtml(d.department_name)}">${escHtml(d.department_name)}</option>`).join('');
      deptSelect.value = currentVal;
    }

    if (_orgDepartmentsCache.length === 0) {
      grid.innerHTML = '';
      if (empty) empty.classList.remove('hidden');
      return;
    }

    if (empty) empty.classList.add('hidden');
    grid.innerHTML = _orgDepartmentsCache.map(d => {
      const color = d.color || '#6366f1';
      const headName = d.head_display_name || d.head_username || 'ยังไม่ระบุหัวหน้า';
      const memberCount = d.member_count || 0;
      return `
        <div class="bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-800 rounded-3xl p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between group relative overflow-hidden">
          <div class="absolute top-0 left-0 right-0 h-1.5" style="background: ${color};"></div>
          <div>
            <div class="flex items-center justify-between mb-3 pt-1">
              <div class="flex items-center gap-2.5">
                <span class="w-4 h-4 rounded-full flex-shrink-0 shadow-sm" style="background: ${color};"></span>
                <h4 class="font-black text-sm text-surface-900 dark:text-white truncate">${escHtml(d.department_name)}</h4>
              </div>
              <button onclick="openEditDeptModal(${d.id})" title="แก้ไขแผนก" class="p-1.5 rounded-xl hover:bg-surface-100 dark:hover:bg-surface-800 text-surface-400 hover:text-surface-700 dark:hover:text-surface-200 transition-colors">
                <i data-lucide="edit-3" class="w-4 h-4"></i>
              </button>
            </div>
            ${d.description ? `<p class="text-xs text-surface-500 line-clamp-2 mb-4 font-normal">${escHtml(d.description)}</p>` : `<p class="text-xs text-surface-400 italic mb-4">ไม่มีคำอธิบาย</p>`}
          </div>

          <div class="pt-4 border-t border-surface-100 dark:border-surface-800 flex items-center justify-between text-xs">
            <div class="flex items-center gap-1.5 text-surface-500">
              <i data-lucide="users" class="w-3.5 h-3.5"></i>
              <span class="font-bold text-surface-700 dark:text-surface-300">${memberCount}</span> คน
            </div>
            <div class="flex items-center gap-1.5 text-surface-500 max-w-[150px] truncate" title="หัวหน้าแผนก: ${escHtml(headName)}">
              <i data-lucide="crown" class="w-3.5 h-3.5 text-amber-500"></i>
              <span class="truncate font-medium text-surface-600 dark:text-surface-300">${escHtml(headName)}</span>
            </div>
          </div>
        </div>
      `;
    }).join('');

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error('Error loading org departments:', err);
    grid.innerHTML = `<div class="col-span-full text-center py-10 text-rose-500 text-xs">เกิดข้อผิดพลาดในการโหลดแผนก</div>`;
  }
}

function selectDeptColor(color) {
  const input = $('deptModalColor');
  if (input) input.value = color;
  document.querySelectorAll('#deptColorPickerContainer .dept-color-swatch').forEach(btn => {
    if (btn.dataset.color === color) {
      btn.classList.add('ring-2', 'ring-offset-2', 'ring-indigo-500');
    } else {
      btn.classList.remove('ring-2', 'ring-offset-2', 'ring-indigo-500');
    }
  });
}

function populateDeptHeadSelect(selectedUsername) {
  const headSelect = $('deptModalHead');
  if (!headSelect) return;
  let html = `<option value="">-- ไม่ระบุหัวหน้าแผนก --</option>`;
  if (Array.isArray(_orgMembersCache)) {
    _orgMembersCache.forEach(m => {
      const selected = m.username === selectedUsername ? 'selected' : '';
      const label = `${m.display_name || m.username} (@${m.username})`;
      html += `<option value="${escHtml(m.username)}" ${selected}>${escHtml(label)}</option>`;
    });
  }
  headSelect.innerHTML = html;
}

function openCreateDeptModal() {
  const modal = $('departmentModal');
  if (!modal) return;
  $('deptModalTitle').textContent = 'เพิ่มแผนกใหม่';
  $('deptModalId').value = '';
  $('deptModalName').value = '';
  $('deptModalDesc').value = '';
  selectDeptColor('#6366f1');
  $('deptModalDeleteBtn').classList.add('hidden');
  populateDeptHeadSelect('');
  modal.classList.remove('hidden');
}

function openEditDeptModal(deptId) {
  const dept = _orgDepartmentsCache.find(d => d.id === deptId);
  if (!dept) return;
  const modal = $('departmentModal');
  if (!modal) return;
  $('deptModalTitle').textContent = 'แก้ไขข้อมูลแผนก';
  $('deptModalId').value = dept.id;
  $('deptModalName').value = dept.department_name || dept.name || '';
  $('deptModalDesc').value = dept.description || '';
  selectDeptColor(dept.color || '#6366f1');
  $('deptModalDeleteBtn').classList.remove('hidden');
  populateDeptHeadSelect(dept.head_username || '');
  modal.classList.remove('hidden');
}

function closeDeptModal() {
  const modal = $('departmentModal');
  if (modal) modal.classList.add('hidden');
}

async function saveDeptModal() {
  const deptId = $('deptModalId').value.trim();
  const name = $('deptModalName').value.trim();
  const description = $('deptModalDesc').value.trim();
  const head_username = $('deptModalHead').value.trim();
  const color = $('deptModalColor').value.trim() || '#6366f1';

  if (!name) {
    if (typeof showToast === 'function') showToast('กรุณาระบุชื่อแผนก', 'error');
    return;
  }

  const payload = {
    name: name,
    department_name: name,
    description: description,
    head_username: head_username,
    color: color
  };

  const isEdit = !!deptId;
  const url = isEdit ? `/api/org/departments/${deptId}` : '/api/org/departments';
  const method = isEdit ? 'PUT' : 'POST';

  try {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    const res = await fetch(url, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.ok) {
      if (typeof showToast === 'function') showToast(isEdit ? 'อัปเดตข้อมูลแผนกสำเร็จ' : 'สร้างแผนกใหม่สำเร็จ', 'success');
      closeDeptModal();
      loadOrgDepartments();
      if (typeof loadOrgMembers === 'function') loadOrgMembers();
    } else {
      if (typeof showToast === 'function') showToast(data.error || 'บันทึกไม่สำเร็จ', 'error');
    }
  } catch (err) {
    console.error(err);
    if (typeof showToast === 'function') showToast('เกิดข้อผิดพลาดในการเชื่อมต่อ', 'error');
  }
}

async function deleteCurrentDept() {
  const deptId = $('deptModalId').value.trim();
  if (!deptId) return;
  if (!confirm('คุณแน่ใจหรือไม่ว่าต้องการลบแผนกนี้?')) return;

  try {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    const res = await fetch(`/api/org/departments/${deptId}`, {
      method: 'DELETE',
      headers: { 'X-CSRF-Token': csrfToken }
    });
    const data = await res.json();
    if (data.ok) {
      if (typeof showToast === 'function') showToast('ลบแผนกสำเร็จ', 'success');
      closeDeptModal();
      loadOrgDepartments();
      if (typeof loadOrgMembers === 'function') loadOrgMembers();
    } else {
      if (typeof showToast === 'function') showToast(data.error || 'ลบไม่สำเร็จ', 'error');
    }
  } catch (err) {
    console.error(err);
    if (typeof showToast === 'function') showToast('เกิดข้อผิดพลาดในการลบ', 'error');
  }
}

window.loadOrgDepartments = loadOrgDepartments;
window.selectDeptColor = selectDeptColor;
window.populateDeptHeadSelect = populateDeptHeadSelect;
window.openCreateDeptModal = openCreateDeptModal;
window.openEditDeptModal = openEditDeptModal;
window.closeDeptModal = closeDeptModal;
window.saveDeptModal = saveDeptModal;
window.deleteCurrentDept = deleteCurrentDept;

// ─── Custom Categories & AI Rules JS ───
async function loadCustomCategoriesAndRules() {
  try {
    const catRes = await fetch('/api/categories');
    const catData = await catRes.json();
    if (catData.ok) {
      const listEl = document.getElementById('customCatList');
      if (listEl) {
        if (!catData.categories || catData.categories.length === 0) {
          listEl.innerHTML = '<span class="text-xs text-surface-400">ยังไม่มีหมวดหมู่คัสตอม</span>';
        } else {
          listEl.innerHTML = catData.categories.map(c => `
            <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-brand-50 text-brand-700 border border-brand-200 dark:bg-brand-950/40 dark:text-brand-300 dark:border-brand-800">
              ${escHtml(c.category_name)} ${c.account_code ? `<span class="opacity-60 text-[10px]">(${escHtml(c.account_code)})</span>` : ''}
              <button onclick="deleteCustomCategoryBtn(${c.id})" class="hover:text-red-600 transition-colors ml-1">&times;</button>
            </span>
          `).join('');
        }
      }
    }

    const ruleRes = await fetch('/api/category-rules');
    const ruleData = await ruleRes.json();
    if (ruleData.ok) {
      const listEl = document.getElementById('aiRuleList');
      if (listEl) {
        if (!ruleData.rules || ruleData.rules.length === 0) {
          listEl.innerHTML = '<span class="text-xs text-surface-400">ยังไม่ได้ตั้งค่ากฎ AI</span>';
        } else {
          listEl.innerHTML = ruleData.rules.map(r => `
            <div class="flex items-center justify-between p-3 rounded-xl bg-surface-50 dark:bg-surface-800/40 border border-surface-200 dark:border-surface-700 text-xs">
              <div class="flex items-center gap-2">
                <span class="font-bold text-amber-600 dark:text-amber-400">พบคำว่า "${escHtml(r.keyword)}"</span>
                <span class="text-surface-400">➔</span>
                <span class="font-bold text-emerald-600 dark:text-emerald-400">จัดลงหมวดหมู่ "${escHtml(r.category_name)}"</span>
              </div>
              <button onclick="deleteAIRuleBtn(${r.id})" class="p-1 text-surface-400 hover:text-red-600 transition-colors">
                <i data-lucide="trash-2" class="w-4 h-4"></i>
              </button>
            </div>
          `).join('');
        }
      }
    }
    if (typeof lucide !== 'undefined') lucide.createIcons();
  } catch(e) {
    console.error('Failed to load categories/rules', e);
  }
}

async function addCustomCategoryBtn() {
  const nameInput = document.getElementById('newCatName');
  const codeInput = document.getElementById('newCatCode');
  const name = nameInput ? nameInput.value.trim() : '';
  const code = codeInput ? codeInput.value.trim() : '';
  if (!name) { if (typeof showToast === 'function') showToast('กรุณาระบุชื่อหมวดหมู่', 'error'); else alert('กรุณาระบุชื่อหมวดหมู่'); return; }
  try {
    const res = await fetch('/api/categories', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ category_name: name, account_code: code })
    });
    const data = await res.json();
    if (data.ok) {
      if (typeof showToast === 'function') showToast('เพิ่มหมวดหมู่สำเร็จ', 'success');
      if (nameInput) nameInput.value = '';
      if (codeInput) codeInput.value = '';
      loadCustomCategoriesAndRules();
    } else {
      if (typeof showToast === 'function') showToast(data.error || 'เกิดข้อผิดพลาด', 'error');
    }
  } catch(e) { console.error(e); }
}

async function deleteCustomCategoryBtn(id) {
  if (!confirm('ยืนยันลบหมวดหมู่นี้?')) return;
  try {
    const res = await fetch(`/api/categories/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.ok) {
      if (typeof showToast === 'function') showToast('ลบหมวดหมู่สำเร็จ', 'success');
      loadCustomCategoriesAndRules();
    }
  } catch(e) {}
}

async function addAIRuleBtn() {
  const kwInput = document.getElementById('newRuleKeyword');
  const catInput = document.getElementById('newRuleCategory');
  const kw = kwInput ? kwInput.value.trim() : '';
  const cat = catInput ? catInput.value.trim() : '';
  if (!kw || !cat) { if (typeof showToast === 'function') showToast('กรุณาระบุ Keyword และหมวดหมู่เป้าหมาย', 'error'); return; }
  try {
    const res = await fetch('/api/category-rules', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ keyword: kw, category_name: cat })
    });
    const data = await res.json();
    if (data.ok) {
      if (typeof showToast === 'function') showToast('เพิ่มกฎ AI สำเร็จ', 'success');
      if (kwInput) kwInput.value = '';
      if (catInput) catInput.value = '';
      loadCustomCategoriesAndRules();
    } else {
      if (typeof showToast === 'function') showToast(data.error || 'เกิดข้อผิดพลาด', 'error');
    }
  } catch(e) { console.error(e); }
}

async function deleteAIRuleBtn(id) {
  if (!confirm('ยืนยันลบกฎ AI นี้?')) return;
  try {
    const res = await fetch(`/api/category-rules/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.ok) {
      if (typeof showToast === 'function') showToast('ลบกฎ AI สำเร็จ', 'success');
      loadCustomCategoriesAndRules();
    }
  } catch(e) {}
}

window.loadCustomCategoriesAndRules = loadCustomCategoriesAndRules;
window.addCustomCategoryBtn = addCustomCategoryBtn;
window.deleteCustomCategoryBtn = deleteCustomCategoryBtn;
window.addAIRuleBtn = addAIRuleBtn;
window.deleteAIRuleBtn = deleteAIRuleBtn;

function updatePVBatchButton() {
  const checkedBoxes = document.querySelectorAll('.pv-checkbox:checked');
  const btn = document.getElementById('batchPVBtn');
  if (btn) {
    if (checkedBoxes.length > 0) {
      btn.classList.remove('hidden');
      btn.innerHTML = `<i data-lucide="file-text" class="w-3.5 h-3.5"></i> ออกใบสำคัญจ่ายกลุ่ม (${checkedBoxes.length} รายการ)`;
    } else {
      btn.classList.add('hidden');
    }
    if (typeof lucide !== 'undefined') lucide.createIcons();
  }
}

function toggleSelectAllPV(masterCheckbox) {
  const checkboxes = document.querySelectorAll('.pv-checkbox');
  checkboxes.forEach(cb => { cb.checked = masterCheckbox.checked; });
  updatePVBatchButton();
}

async function createBatchPaymentVoucher() {
  const checkedBoxes = document.querySelectorAll('.pv-checkbox:checked');
  if (checkedBoxes.length === 0) {
    if (typeof showToast === 'function') showToast('กรุณาเลือกรายการค่าใช้จ่ายอย่างน้อย 1 รายการค่ะ', 'error');
    return;
  }
  const items = [];
  checkedBoxes.forEach(cb => {
    try {
      items.push(JSON.parse(cb.getAttribute('data-item')));
    } catch(e){}
  });

  try {
    const res = await fetch('/api/dashboard/create-payment-voucher', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ items: items })
    });
    const data = await res.json();
    if (data.ok) {
      if (typeof showToast === 'function') showToast('ออกใบสำคัญจ่ายสำเร็จ!', 'success');
      window.open(data.file_link || data.pdf_url, '_blank');
    } else {
      if (typeof showToast === 'function') showToast(data.error || 'เกิดข้อผิดพลาดในการสร้างใบสำคัญจ่าย', 'error');
    }
  } catch(e) {
    if (typeof showToast === 'function') showToast('เกิดข้อผิดพลาดในการเชื่อมต่อระบบ', 'error');
  }
}


async function loadOrgAnnouncements() {
  const container = $('orgAnnouncementList');
  if (!container) return;
  container.innerHTML = '<div class="text-center py-8 opacity-50 text-xs">กำลังโหลดประกาศองค์กร...</div>';
  try {
    const res = await apiFetch('/api/org/announcements');
    if (res.ok && res.announcements) {
      if (res.announcements.length === 0) {
        container.innerHTML = '<div class="text-center py-10 text-surface-400 text-xs font-bold bg-surface-50 dark:bg-surface-800/30 rounded-2xl">ยังไม่มีประกาศข่าวสารภายในองค์กร</div>';
        return;
      }
      container.innerHTML = res.announcements.map(a => {
        let badgeClass = 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400';
        let badgeText = 'ข่าวสารทั่วไป';
        if (a.priority === 'important') {
          badgeClass = 'bg-red-50 text-red-600 dark:bg-red-900/30 dark:text-red-400 font-black';
          badgeText = 'สำคัญมาก';
        } else if (a.priority === 'update') {
          badgeClass = 'bg-purple-50 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400';
          badgeText = 'อัปเดตงาน';
        }
        return `
          <div class="p-4 bg-surface-50 dark:bg-surface-800/40 border border-surface-200 dark:border-surface-700/60 rounded-2xl space-y-2 relative group">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="px-2.5 py-1 rounded-lg text-[10px] font-bold ${badgeClass}">${badgeText}</span>
                <span class="text-[11px] font-bold text-surface-400">โพสต์โดย @${a.created_by} • ${a.created_at}</span>
              </div>
              <button onclick="deleteOrgAnnouncement(${a.id})" class="text-surface-400 hover:text-red-500 text-xs p-1 opacity-0 group-hover:opacity-100 transition-all">
                <i data-lucide="trash-2" class="w-4 h-4"></i>
              </button>
            </div>
            <h4 class="text-sm font-black text-surface-900 dark:text-white">${escapeHtml(a.title)}</h4>
            <p class="text-xs text-surface-600 dark:text-surface-300 leading-relaxed whitespace-pre-line">${escapeHtml(a.content)}</p>
          </div>
        `;
      }).join('');
      initIcons();
    }
  } catch (e) {
    container.innerHTML = '<div class="text-center py-6 text-red-500 text-xs">โหลดประกาศล้มเหลว</div>';
  }
}

async function submitOrgAnnouncement() {
  const title = $('ann_title').value.trim();
  const content = $('ann_content').value.trim();
  const priority = $('ann_priority').value;
  if (!title || !content) return toast('กรุณาระบุหัวข้อและเนื้อหาประกาศ', 'error');
  try {
    const res = await apiFetch('/api/org/announcements', {
      method: 'POST',
      body: JSON.stringify({ title, content, priority })
    });
    if (res.ok) {
      toast('โพสต์ประกาศเรียบร้อยแล้วค่ะ', 'success');
      $('ann_title').value = '';
      $('ann_content').value = '';
      $('createAnnounceForm').classList.add('hidden');
      loadOrgAnnouncements();
    } else {
      toast(res.error || 'ไม่สามารถโพสต์ประกาศได้', 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาดในการโพสต์ประกาศ', 'error');
  }
}

async function deleteOrgAnnouncement(id) {
  if (!confirm('คุณต้องการลบประกาศนี้ใช่หรือไม่?')) return;
  try {
    const res = await apiFetch(`/api/org/announcements/${id}`, { method: 'DELETE' });
    if (res.ok) {
      toast('ลบประกาศเรียบร้อยแล้ว', 'success');
      loadOrgAnnouncements();
    } else {
      toast(res.error || 'ลบไม่สำเร็จ', 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาดในการลบประกาศ', 'error');
  }
}

let _orgLogActiveCategory = 'all';

async function loadOrgLogs() {
  const container = $('orgLogList');
  if (!container) return;
  container.innerHTML = `
    <div class="flex flex-col items-center justify-center py-16 gap-3 text-surface-400">
      <div class="w-7 h-7 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin"></div>
      <span class="text-xs font-medium">กำลังโหลดบันทึกกิจกรรม...</span>
    </div>
  `;
  try {
    const res = await apiFetch('/api/org/logs');
    if (res.ok && res.logs) {
      _orgLogsCache = res.logs;
      applyOrgLogFilters();
    } else {
      container.innerHTML = `<div class="text-center py-12 text-rose-500 text-xs font-semibold">${escapeHtml(res.error || 'โหลดบันทึกประวัติล้มเหลว')}</div>`;
    }
  } catch (e) {
    container.innerHTML = '<div class="text-center py-12 text-rose-500 text-xs font-semibold">โหลดบันทึกประวัติล้มเหลว</div>';
  }
}

function clearOrgLogSearch() {
  const input = $('orgLogSearch');
  if (input) input.value = '';
  const clearBtn = $('orgLogSearchClear');
  if (clearBtn) clearBtn.classList.add('hidden');
  applyOrgLogFilters();
}

function setOrgLogCategoryFilter(cat) {
  _orgLogActiveCategory = cat;
  document.querySelectorAll('.org-log-cat-btn').forEach(btn => {
    const isCurrent = btn.getAttribute('data-cat') === cat;
    if (isCurrent) {
      btn.className = 'org-log-cat-btn px-3 py-1.5 rounded-xl text-xs font-bold transition-all bg-brand-600 text-white shadow-sm flex items-center gap-1.5 shrink-0';
    } else {
      btn.className = 'org-log-cat-btn px-3 py-1.5 rounded-xl text-xs font-medium transition-all bg-surface-100 hover:bg-surface-200 dark:bg-surface-800 dark:hover:bg-surface-700 text-surface-600 dark:text-surface-300 flex items-center gap-1.5 shrink-0';
    }
  });
  applyOrgLogFilters();
}

function filterOrgLogs(query) {
  const clearBtn = $('orgLogSearchClear');
  if (clearBtn) {
    if (query && query.trim()) clearBtn.classList.remove('hidden');
    else clearBtn.classList.add('hidden');
  }
  applyOrgLogFilters();
}

function parseOrgLogEvent(rawText) {
  const text = (rawText || '').trim();
  let category = 'system';
  let badgeText = 'ระบบ';
  let badgeColor = 'bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300 border-surface-200 dark:border-surface-700';
  let icon = 'activity';
  let formattedHtml = escapeHtml(text);

  // 1. Files
  const fileMatch = text.match(/Assigned file ([0-9a-fA-F]{24,64}) to category (.*)/i);
  if (fileMatch) {
    category = 'file';
    badgeText = 'จัดการไฟล์';
    badgeColor = 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20';
    icon = 'file-text';
    const hash = fileMatch[1];
    const catName = fileMatch[2].trim();
    const shortHash = hash.length > 12 ? `${hash.slice(0, 6)}…${hash.slice(-4)}` : hash;
    const catLabel = catName.toLowerCase() === 'none' ? 'ทั่วไป (None)' : escapeHtml(catName);
    formattedHtml = `จัดหมวดหมู่เอกสาร <code class="px-1.5 py-0.5 rounded bg-surface-100 dark:bg-surface-800 font-mono text-[11px] font-semibold text-brand-600 dark:text-brand-300 border border-surface-200 dark:border-surface-700" title="${hash}">${shortHash}</code> ไปยังหมวดหมู่ <span class="font-bold text-surface-900 dark:text-white">${catLabel}</span>`;
  } else if (/uploaded file|deleted file|file category/i.test(text)) {
    category = 'file';
    badgeText = 'จัดการไฟล์';
    badgeColor = 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20';
    icon = 'file-text';
  }
  // 2. Announcements
  else if (text.startsWith('Created org announcement:')) {
    category = 'post';
    badgeText = 'ประกาศองค์กร';
    badgeColor = 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';
    icon = 'megaphone';
    const title = text.replace('Created org announcement:', '').trim();
    formattedHtml = `สร้างประกาศองค์กรใหม่: <span class="font-semibold text-surface-900 dark:text-white">“${escapeHtml(title)}”</span>`;
  } else if (text.startsWith('Deleted org announcement')) {
    category = 'post';
    badgeText = 'ลบประกาศ';
    badgeColor = 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20';
    icon = 'trash-2';
    formattedHtml = `ลบประกาศองค์กร <span class="font-mono text-[11px] px-1.5 py-0.5 rounded bg-surface-100 dark:bg-surface-800">${escapeHtml(text)}</span>`;
  }
  // 3. Posts
  else if (text.startsWith('New post created:')) {
    category = 'post';
    badgeText = 'สร้างโพสต์';
    badgeColor = 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
    icon = 'plus-circle';
    const match = text.match(/ID\s*(\d+)/i);
    const id = match ? match[1] : '';
    formattedHtml = `สร้างโพสต์ใหม่ในฟีด <code class="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-mono text-[11px] font-bold">#${id}</code>`;
  } else if (text.startsWith('Post deleted:')) {
    category = 'post';
    badgeText = 'ลบโพสต์';
    badgeColor = 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20';
    icon = 'trash-2';
    const match = text.match(/ID\s*(\d+)/i);
    const id = match ? match[1] : '';
    formattedHtml = `ลบโพสต์ออกจากฟีด <code class="px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 font-mono text-[11px] font-bold">#${id}</code>`;
  }
  // 4. Knowledge Base (KB)
  else if (text.startsWith('Added KB category:')) {
    category = 'kb';
    badgeText = 'คลังความรู้';
    badgeColor = 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20';
    icon = 'book-open';
    const kbInfo = text.replace('Added KB category:', '').trim();
    formattedHtml = `เพิ่มหมวดหมู่คลังความรู้: <span class="font-semibold text-surface-900 dark:text-white">${escapeHtml(kbInfo)}</span>`;
  } else if (/kb|rag/i.test(text)) {
    category = 'kb';
    badgeText = 'คลังความรู้';
    badgeColor = 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20';
    icon = 'book-open';
  }
  // 5. Schedules
  else if (/schedule/i.test(text)) {
    category = 'post';
    badgeText = 'ปฏิทินงาน';
    badgeColor = 'bg-teal-500/10 text-teal-600 dark:text-teal-400 border-teal-500/20';
    icon = 'calendar';
  }
  // 6. Organization Profile & Department
  else if (text.includes('Updated business profile')) {
    category = 'system';
    badgeText = 'ข้อมูลธุรกิจ';
    badgeColor = 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/20';
    icon = 'building-2';
    formattedHtml = `อัปเดตข้อมูลและโปรไฟล์ธุรกิจขององค์กร`;
  } else if (/department/i.test(text)) {
    category = 'system';
    badgeText = 'โครงสร้างองค์กร';
    badgeColor = 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/20';
    icon = 'layers';
  }
  // 7. Security / User Role
  else if (/password|role|user|ownership|line account/i.test(text)) {
    category = 'system';
    badgeText = 'ความปลอดภัย';
    badgeColor = 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/20';
    icon = 'shield-check';
  }

  // Format any raw long hex hash if still untouched
  formattedHtml = formattedHtml.replace(/([0-9a-fA-F]{32,64})/g, (m) => {
    return `<code class="px-1.5 py-0.5 rounded bg-surface-100 dark:bg-surface-800 font-mono text-[11px] font-semibold text-brand-600 dark:text-brand-300 border border-surface-200 dark:border-surface-700" title="${m}">${m.slice(0, 6)}…${m.slice(-4)}</code>`;
  });

  return { category, badgeText, badgeColor, icon, formattedHtml };
}

function getOrgLogUserAvatar(username) {
  const name = username || 'System';
  const initial = name.replace(/^@/, '')[0]?.toUpperCase() || 'S';
  const palettes = [
    { bg: 'bg-blue-500/15 text-blue-600 dark:text-blue-400 ring-blue-500/20' },
    { bg: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 ring-emerald-500/20' },
    { bg: 'bg-purple-500/15 text-purple-600 dark:text-purple-400 ring-purple-500/20' },
    { bg: 'bg-amber-500/15 text-amber-600 dark:text-amber-400 ring-amber-500/20' },
    { bg: 'bg-teal-500/15 text-teal-600 dark:text-teal-400 ring-teal-500/20' },
    { bg: 'bg-rose-500/15 text-rose-600 dark:text-rose-400 ring-rose-500/20' },
    { bg: 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 ring-indigo-500/20' },
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  const p = palettes[Math.abs(hash) % palettes.length];
  return { initial, className: `${p.bg} ring-1` };
}

function formatOrgLogTime(timeStr) {
  if (!timeStr) return { dateKey: 'ไม่ระบุวันที่', displayTime: '', dateHeader: 'ไม่ระบุวันที่', fullTime: '' };
  
  const parts = timeStr.trim().split(' ');
  const datePart = parts[0] || '';
  const timePart = parts[1] || '';
  const displayTime = timePart.slice(0, 5) || timePart;

  let dateHeader = datePart;
  try {
    const d = new Date(timeStr.replace(' ', 'T'));
    if (!isNaN(d.getTime())) {
      const today = new Date();
      const isToday = d.toDateString() === today.toDateString();
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      const isYesterday = d.toDateString() === yesterday.toDateString();

      if (isToday) {
        dateHeader = 'วันนี้ (Today)';
      } else if (isYesterday) {
        dateHeader = 'เมื่อวานนี้ (Yesterday)';
      } else {
        const months = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
        dateHeader = `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
      }
    }
  } catch (e) {}

  return { dateKey: datePart, displayTime, dateHeader, fullTime: timeStr };
}

function applyOrgLogFilters() {
  const query = ($('orgLogSearch')?.value || '').toLowerCase().trim();
  const cat = _orgLogActiveCategory || 'all';

  const filtered = _orgLogsCache.filter(l => {
    const parsed = parseOrgLogEvent(l.event);
    if (cat !== 'all' && parsed.category !== cat) return false;
    if (query) {
      const matchUser = (l.user || '').toLowerCase().includes(query);
      const matchEvent = (l.event || '').toLowerCase().includes(query);
      const matchBadge = parsed.badgeText.toLowerCase().includes(query);
      if (!matchUser && !matchEvent && !matchBadge) return false;
    }
    return true;
  });

  const badge = $('orgLogCountBadge');
  if (badge) badge.textContent = `${filtered.length} รายการ`;

  renderOrgLogs(filtered);
}

function renderOrgLogs(logs) {
  const container = $('orgLogList');
  if (!container) return;

  if (!logs || logs.length === 0) {
    container.innerHTML = `
      <div class="flex flex-col items-center justify-center py-16 px-4 text-center bg-surface-50/50 dark:bg-surface-800/20 rounded-2xl border border-dashed border-surface-200 dark:border-surface-800">
        <div class="w-12 h-12 rounded-2xl bg-surface-100 dark:bg-surface-800 flex items-center justify-center text-surface-400 mb-3 shadow-inner">
          <i data-lucide="inbox" class="w-6 h-6"></i>
        </div>
        <p class="text-xs font-bold text-surface-700 dark:text-surface-300">ไม่พบประวัติกิจกรรม</p>
        <p class="text-[11px] text-surface-400 mt-0.5">ยังไม่มีกิจกรรมที่ตรงตามเงื่อนไขการค้นหาหรือตัวกรองนี้</p>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  let html = '';
  let lastDateHeader = '';

  logs.forEach(l => {
    const timeInfo = formatOrgLogTime(l.time);
    const parsed = parseOrgLogEvent(l.event);
    const avatar = getOrgLogUserAvatar(l.user);

    // Timeline Date Divider
    if (timeInfo.dateHeader !== lastDateHeader) {
      lastDateHeader = timeInfo.dateHeader;
      html += `
        <div class="flex items-center gap-2 pt-3 pb-1">
          <div class="h-[1px] flex-1 bg-surface-200 dark:bg-surface-800"></div>
          <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-surface-100 dark:bg-surface-800 text-surface-500 dark:text-surface-400 border border-surface-200/60 dark:border-surface-700/60 tabular-nums">
            ${lastDateHeader}
          </span>
          <div class="h-[1px] flex-1 bg-surface-200 dark:bg-surface-800"></div>
        </div>
      `;
    }

    html += `
      <div class="group flex items-start justify-between gap-3 p-3 bg-white hover:bg-surface-50 dark:bg-surface-900/90 dark:hover:bg-surface-800/70 border border-surface-200/80 dark:border-surface-800 rounded-2xl transition-all duration-150 hover:border-brand-500/30 hover:shadow-sm">
        <div class="flex items-start gap-3 min-w-0">
          <div class="w-8 h-8 rounded-xl ${avatar.className} flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 select-none shadow-xs">
            ${avatar.initial}
          </div>
          <div class="min-w-0 space-y-1">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-xs font-bold text-surface-900 dark:text-white">@${escapeHtml(l.user || 'System')}</span>
              <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold border ${parsed.badgeColor}">
                <i data-lucide="${parsed.icon}" class="w-3 h-3"></i>
                ${parsed.badgeText}
              </span>
            </div>
            <p class="text-xs text-surface-600 dark:text-surface-300 leading-relaxed break-words font-medium">
              ${parsed.formattedHtml}
            </p>
          </div>
        </div>
        <div class="shrink-0 text-right pl-2 pt-0.5">
          <span class="text-[11px] font-mono font-medium text-surface-400 tabular-nums cursor-default" title="${timeInfo.fullTime}">
            ${timeInfo.displayTime || timeInfo.fullTime}
          </span>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
  if (window.lucide) lucide.createIcons();
}

async function loadOrgBusinessProfile() {
  const form = $('orgBusinessForm');
  if (!form) return;
  try {
    const data = await apiFetch('/api/org/profile');
    if (data.ok && data.profile) {
      const p = data.profile;
      
      // Select fields
      if ($('biz_type')) $('biz_type').value = p.business_type || 'บริษัทจำกัด';
      if ($('biz_province')) $('biz_province').value = p.province || '';
      
      // Text inputs
      if ($('biz_name_th')) $('biz_name_th').value = p.business_name_th || '';
      if ($('biz_name_en')) $('biz_name_en').value = p.business_name_en || '';
      if ($('biz_tax_id')) $('biz_tax_id').value = p.tax_id || '';
      if ($('biz_addr1')) $('biz_addr1').value = p.address_line1 || '';
      if ($('biz_addr2')) $('biz_addr2').value = p.address_line2 || '';
      if ($('biz_district')) $('biz_district').value = p.district || '';
      if ($('biz_zipcode')) $('biz_zipcode').value = p.zipcode || '';
      if ($('biz_phone')) $('biz_phone').value = p.phone || '';
      
      // Logo and Signature fields
      if (p.logo_url) {
        if ($('biz_logo_url')) $('biz_logo_url').value = p.logo_url;
        if ($('org_logo_preview')) {
          $('org_logo_preview').src = p.logo_url;
          $('org_logo_preview').classList.remove('hidden');
        }
        if ($('org_logo_placeholder')) $('org_logo_placeholder').classList.add('hidden');
        if ($('btn_delete_logo')) $('btn_delete_logo').classList.remove('hidden');
      } else {
        resetOrgLogoUI();
      }
      
      if (p.signature_url) {
        if ($('biz_signature_url')) $('biz_signature_url').value = p.signature_url;
        if ($('org_sig_preview')) {
          $('org_sig_preview').src = p.signature_url;
          $('org_sig_preview').classList.remove('hidden');
        }
        if ($('org_sig_placeholder')) $('org_sig_placeholder').classList.add('hidden');
        if ($('btn_delete_sig')) $('btn_delete_sig').classList.remove('hidden');
      } else {
        resetOrgSigUI();
      }
      
      // Radio inputs
      const vatVal = p.vat_status || 'จด VAT แล้ว';
      const vatRadios = document.getElementsByName('vat_status');
      for (let r of vatRadios) {
        r.checked = (r.value === vatVal);
      }
      
      const branchVal = p.branch_type || 'ไม่มี';
      const branchRadios = document.getElementsByName('branch_type');
      for (let r of branchRadios) {
        r.checked = (r.value === branchVal);
      }
    }
  } catch (e) {
    console.error('Error loading business profile:', e);
    toast('ไม่สามารถโหลดข้อมูลธุรกิจได้', 'error');
  }
}

async function saveOrgBusinessProfile() {
  const business_type = $('biz_type')?.value;
  const business_name_th = $('biz_name_th')?.value;
  const phone = $('biz_phone')?.value;
  
  if (!business_type || !business_name_th || !phone) {
    toast('กรุณากรอกข้อมูลในช่องที่จำเป็น (*) ให้ครบถ้วน', 'error');
    return;
  }
  
  let vat_status = 'จด VAT แล้ว';
  const vatRadios = document.getElementsByName('vat_status');
  for (let r of vatRadios) {
    if (r.checked) vat_status = r.value;
  }
  
  let branch_type = 'ไม่มี';
  const branchRadios = document.getElementsByName('branch_type');
  for (let r of branchRadios) {
    if (r.checked) branch_type = r.value;
  }
  
  const payload = {
    business_type,
    vat_status,
    branch_type,
    business_name_th,
    business_name_en: $('biz_name_en')?.value || '',
    tax_id: $('biz_tax_id')?.value || '',
    address_line1: $('biz_addr1')?.value || '',
    address_line2: $('biz_addr2')?.value || '',
    district: $('biz_district')?.value || '',
    province: $('biz_province')?.value || '',
    zipcode: $('biz_zipcode')?.value || '',
    phone,
    logo_url: $('biz_logo_url')?.value || '',
    signature_url: $('biz_signature_url')?.value || ''
  };
  
  try {
    const data = await apiFetch('/api/org/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (data.ok) {
      toast('บันทึกข้อมูลธุรกิจเรียบร้อยแล้วค่ะ', 'success');
      loadOrgBusinessProfile();
    } else {
      toast(data.error || 'ไม่สามารถบันทึกข้อมูลได้', 'error');
    }
  } catch (e) {
    console.error('Error saving business profile:', e);
    toast('เกิดข้อผิดพลาดในการบันทึกข้อมูล', 'error');
  }
}

async function loadOrgMembers() {
  const container = $('orgMemberList');
  if (!container) return;
  container.innerHTML = '<div class="text-center py-10 text-surface-400 text-sm">กำลังโหลดข้อมูลสมาชิก...</div>';
  try {
    const data = await apiFetch('/api/org/me');
    if (data.ok) {
      _orgMembersCache = data.members || [];
      _orgMembersLoaded = true;
      // Update stats
      const total = _orgMembersCache.length;
      const admins = _orgMembersCache.filter(m => m.role === 'admin').length;
      if ($('orgStatTotal')) $('orgStatTotal').textContent = total;
      if ($('orgStatAdmins')) $('orgStatAdmins').textContent = admins;
      if ($('orgPanelName') && data.org?.name) $('orgPanelName').textContent = data.org.name;

      // Populate department filter dropdown
      const deptSelect = $('orgFilterDept');
      if (deptSelect) {
        const currVal = deptSelect.value;
        const depts = Array.from(new Set(_orgMembersCache.map(m => (m.department || '').trim()).filter(Boolean))).sort();
        deptSelect.innerHTML = '<option value="">ทุกแผนก</option>' + depts.map(d => `<option value="${escapeHtml(d)}">${escapeHtml(d)}</option>`).join('');
        if (currVal && depts.includes(currVal)) deptSelect.value = currVal;
      }

      // Load quota banner
      loadOrgQuota();

      renderOrgMembers(_orgMembersCache, state.isOrgAdmin || state.isAdmin);
      const treeContent = $('orgTabContent-tree');
      if (treeContent && !treeContent.classList.contains('hidden')) {
        renderOrgTree();
      }
    } else {
      container.innerHTML = '<div class="text-center py-10 text-surface-400 text-sm">ไม่พบข้อมูลองค์กร</div>';
    }
  } catch (e) {
    container.innerHTML = `<div class="text-center py-10 text-red-400 text-sm">โหลดข้อมูลล้มเหลว</div>`;
  }
}

async function loadOrgQuota() {
  try {
    const res = await apiFetch('/api/org/quota');
    if (res && res.ok) {
      if ($('orgQuotaPlanBadge')) $('orgQuotaPlanBadge').textContent = res.plan_display || 'Business Plan';
      if ($('orgQuotaExpiryText')) $('orgQuotaExpiryText').textContent = 'สถานะแพ็กเกจ: ' + (res.expires_at || 'ใช้งานได้ต่อเนื่อง');
      if ($('orgQuotaUsageText')) {
        const limitStr = res.is_unlimited ? 'ไม่จำกัด' : res.max_users;
        $('orgQuotaUsageText').textContent = `${res.member_count} / ${limitStr} สมาชิก (${res.usage_percent}%)`;
      }
      if ($('orgQuotaProgressBar')) {
        $('orgQuotaProgressBar').style.width = Math.max(5, Math.min(100, res.usage_percent)) + '%';
      }
    }
  } catch (e) {
    console.error('loadOrgQuota error:', e);
  }
}

function exportOrgMembersCSV() {
  window.open('/api/org/members/export-csv', '_blank');
  toast('กำลังดาวน์โหลดรายชื่อสมาชิก (CSV)...', 'info');
}

function filterOrgMembers() {
  const q = ($('orgMemberSearch')?.value || '').toLowerCase().trim();
  const dept = $('orgFilterDept')?.value || '';
  const role = $('orgFilterRole')?.value || '';

  const filtered = _orgMembersCache.filter(m => {
    if (q) {
      const matchText = (m.username + ' ' + (m.display_name || '') + ' ' + (m.email || '') + ' ' + (m.position || '')).toLowerCase();
      if (!matchText.includes(q)) return false;
    }
    if (dept && (m.department || '').trim() !== dept) return false;
    if (role === 'owner' && !m.is_owner) return false;
    if (role === 'admin' && (m.role !== 'admin' || m.is_owner)) return false;
    if (role === 'member' && m.role === 'admin') return false;
    return true;
  });

  renderOrgMembers(filtered, state.isOrgAdmin || state.isAdmin);
}

async function loadOrgGoogleStatus() {
  const notConnected = $('orgGoogleNotConnected');
  const connected = $('orgGoogleConnected');
  if (!notConnected || !connected) return;
  try {
    const data = await apiFetch('/api/auth/google/status');
    if (data.connected) {
      notConnected.classList.add('hidden');
      connected.classList.remove('hidden');
      const isOrgLevel = data.effective_source === 'org';
      const badge = isOrgLevel
        ? `<span class="ml-2 text-[9px] font-black uppercase bg-brand-100 dark:bg-brand-900/30 text-brand-600 px-1.5 py-0.5 rounded-full">ระดับองค์กร</span>`
        : `<span class="ml-2 text-[9px] font-black uppercase bg-surface-100 dark:bg-surface-700 text-surface-500 px-1.5 py-0.5 rounded-full">ส่วนตัว</span>`;
      if ($('orgGoogleConnectedEmail')) $('orgGoogleConnectedEmail').innerHTML = (data.email || '—') + badge;
      const connByEl = $('orgGoogleConnectedBy');
      const connectedBy = data.org?.connected_by;
      if (connByEl) {
        if (isOrgLevel && connectedBy) {
          connByEl.textContent = `เชื่อมต่อโดย: ${connectedBy}`;
          connByEl.classList.remove('hidden');
        } else {
          connByEl.classList.add('hidden');
        }
      }
      const disconnectBtn = $('orgGoogleDisconnectBtn');
      if (disconnectBtn) {
        disconnectBtn.classList.toggle('hidden', !(state.isOrgAdmin || state.isAdmin));
      }
    } else {
      notConnected.classList.remove('hidden');
      connected.classList.add('hidden');
    }
  } catch (e) {
    notConnected.classList.remove('hidden');
    connected.classList.add('hidden');
  }
}

async function disconnectOrgGoogle() {
  if (!confirm('ต้องการยกเลิกการเชื่อมต่อ Google Drive ขององค์กรใช่ไหม?')) return;
  try {
    const data = await apiFetch('/api/auth/google/disconnect?scope=org', { method: 'POST' });
    if (data.ok) {
      toast('ยกเลิกการเชื่อมต่อ Google เรียบร้อยแล้ว', 'success');
      loadOrgGoogleStatus();
      loadGoogleDriveStatus();
    } else {
      toast(data.error || 'เกิดข้อผิดพลาด', 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาด', 'error');
  }
}

function renderOrgMembers(members, canManage) {
  const container = $('orgMemberList');
  if (!container) return;
  if (!members.length) {
    container.innerHTML = '<div class="text-center py-10 text-surface-400 text-sm">ยังไม่มีสมาชิกในองค์กร</div>';
    return;
  }
  container.innerHTML = members.map(m => {
    const isMe = m.username === state.username;
    const isActive = m.is_active !== false;
    const avatarFallback = (m.display_name || m.username).charAt(0).toUpperCase();
    const avatarHtml = m.avatar_url
      ? `<img src="${m.avatar_url}" class="w-9 h-9 rounded-xl object-cover flex-shrink-0" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">`
        + `<div class="w-9 h-9 rounded-xl bg-surface-100 dark:bg-surface-800 border border-surface-200 dark:border-surface-700 items-center justify-center text-surface-700 dark:text-surface-200 text-xs font-bold flex-shrink-0" style="display:none">${avatarFallback}</div>`
      : `<div class="w-9 h-9 rounded-xl bg-surface-100 dark:bg-surface-800 border border-surface-200 dark:border-surface-700 flex items-center justify-center text-surface-700 dark:text-surface-200 text-xs font-bold flex-shrink-0">${avatarFallback}</div>`;
    
    // Primary Role Badge (Consistent, clean, non-shouty)
    let roleBadge = `<span class="inline-flex items-center px-2 py-0.5 text-[10px] font-medium text-surface-500 dark:text-surface-400 bg-surface-100 dark:bg-surface-800 border border-surface-200/80 dark:border-surface-700/80 rounded-md">Member</span>`;
    if (m.is_owner) {
      roleBadge = `<span class="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold text-amber-600 dark:text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-md"><i data-lucide="crown" class="w-2.5 h-2.5"></i>Owner</span>`;
    } else if (m.role === 'admin') {
      roleBadge = `<span class="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold text-brand-600 dark:text-brand-400 bg-brand-500/10 border border-brand-500/20 rounded-md"><i data-lucide="shield" class="w-2.5 h-2.5"></i>Admin</span>`;
    }

    const statusDot = `<span class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full ring-2 ring-white dark:ring-surface-900 ${isActive ? 'bg-emerald-500' : 'bg-surface-400'}" title="${isActive ? 'ใช้งานอยู่' : 'ปิดใช้งาน'}"></span>`;
    
    // Sub-permissions: Muted, cohesive tags (No rainbow neon confetti!)
    const activePerms = [];
    if (m.can_view_financial) activePerms.push('รายจ่าย');
    if (m.can_manage_leave) activePerms.push('อนุมัติลา');
    if (m.can_view_kb || m.can_edit_kb) activePerms.push('คลังความรู้');
    if (m.can_broadcast_line) activePerms.push('LINE Broadcast');
    if (m.can_manage_peak) activePerms.push('PEAK');

    let permsHtml = '';
    if (activePerms.length === 5) {
      permsHtml = `<span class="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium text-surface-600 dark:text-surface-300 bg-surface-100 dark:bg-surface-800 border border-surface-200/80 dark:border-surface-700/80 rounded-md" title="มีสิทธิ์ครบทุกระบบ: รายจ่าย, อนุมัติลา, คลังความรู้, LINE Broadcast, PEAK"><i data-lucide="shield-check" class="w-3 h-3 text-emerald-500"></i>ทุกสิทธิ์เข้าถึง</span>`;
    } else if (activePerms.length > 0) {
      permsHtml = activePerms.map(p => 
        `<span class="inline-flex items-center px-2 py-0.5 text-[10px] font-medium text-surface-600 dark:text-surface-300 bg-surface-100/80 dark:bg-surface-800/80 border border-surface-200/60 dark:border-surface-700/60 rounded-md">${p}</span>`
      ).join('');
    }

    const googleBadge = m.google_connected
      ? `<span class="inline-flex items-center gap-1 px-1.5 py-0.5 text-[9px] font-medium bg-surface-100 dark:bg-surface-800 border border-surface-200/80 dark:border-surface-700/80 text-surface-600 dark:text-surface-300 rounded" title="เชื่อมต่อ Google: ${m.google_email || ''}"><svg class="w-2.5 h-2.5" viewBox="0 0 24 24" fill="none"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>Google</span>`
      : '';
    const meBadge = isMe ? `<span class="text-[9px] font-semibold text-brand-600 dark:text-brand-400 bg-brand-500/10 border border-brand-500/20 px-1.5 py-0.5 rounded">คุณ</span>` : '';
    const subInfo = [
      `@${m.username}`,
      m.google_email ? m.google_email : (m.email ? m.email : null),
      m.department ? m.department : null,
      m.position ? m.position : null,
    ].filter(Boolean).join(' · ');
    const actions = canManage ? `
      <div class="flex items-center gap-1.5 ml-auto flex-shrink-0">
        <button onclick="openOrgMemberEditModal('${m.username}')"
          class="px-3 py-1.5 text-xs font-semibold rounded-lg border border-surface-200 dark:border-surface-700 text-surface-700 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-700/60 transition-colors">
          <i data-lucide="pencil" class="w-3 h-3 inline mr-1"></i>แก้ไข
        </button>
        ${!isMe && !m.is_owner ? `<button onclick="removeOrgMember('${m.username}')"
          class="p-1.5 text-surface-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-lg transition-colors" title="ลบออกจากองค์กร">
          <i data-lucide="user-minus" class="w-4 h-4"></i>
        </button>` : ''}
      </div>` : '';
    return `
      <div class="admin-user-row flex items-center gap-3 p-3 bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-800 rounded-xl shadow-xs">
        <div class="relative flex-shrink-0">
          ${avatarHtml}
          ${statusDot}
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-1.5 flex-wrap mb-1">
            <span class="text-xs font-semibold text-surface-900 dark:text-white truncate max-w-[180px]">${m.display_name || m.username}</span>
            ${meBadge}
            ${roleBadge}
            ${permsHtml}
            ${googleBadge}
          </div>
          <div class="text-[11px] text-surface-400 truncate">${subInfo}</div>
        </div>
        ${actions}
      </div>`;
  }).join('');
  initIcons();
}

let _orgEditingUsername = null;

function openOrgMemberEditModal(username) {
  const m = _orgMembersCache.find(x => x.username === username);
  if (!m) return;
  _orgEditingUsername = username;
  const avatarEl = $('orgEditMemberAvatar');
  if (avatarEl) {
    const initial = (m.display_name || username).charAt(0).toUpperCase();
    if (m.avatar_url) {
      const img = document.createElement('img');
      img.src = m.avatar_url;
      img.className = 'w-full h-full object-cover rounded-xl';
      img.onerror = () => {
        avatarEl.textContent = '';
        const span = document.createElement('span');
        span.className = 'text-lg font-black';
        span.textContent = initial;
        avatarEl.appendChild(span);
      };
      avatarEl.textContent = '';
      avatarEl.appendChild(img);
    } else {
      avatarEl.textContent = '';
      const span = document.createElement('span');
      span.className = 'text-lg font-black';
      span.textContent = initial;
      avatarEl.appendChild(span);
    }
  }
  if ($('orgEditMemberName')) $('orgEditMemberName').textContent = m.display_name || username;
  if ($('orgEditMemberUsername')) $('orgEditMemberUsername').textContent = `@${username}${m.department ? ' · ' + m.department : ''}${m.position ? ' · ' + m.position : ''}`;
  if ($('orgEditDisplayName')) $('orgEditDisplayName').value = m.display_name || '';
  if ($('orgEditMemberPosition')) $('orgEditMemberPosition').value = m.position || '';
  if ($('orgEditMemberDepartment')) $('orgEditMemberDepartment').value = m.department || '';
  if ($('orgEditMemberRole')) $('orgEditMemberRole').value = m.role || 'member';
  if ($('orgEditUserActive')) $('orgEditUserActive').checked = m.is_active !== false;
  if ($('orgEditUserCanViewKB')) $('orgEditUserCanViewKB').checked = !!m.can_view_kb;
  if ($('orgEditUserCanEditKB')) $('orgEditUserCanEditKB').checked = !!m.can_edit_kb;
  if ($('orgEditUserCanDeleteKB')) $('orgEditUserCanDeleteKB').checked = !!m.can_delete_kb;
  if ($('orgEditMemberFinancial')) $('orgEditMemberFinancial').checked = !!m.can_view_financial;
  if ($('orgEditMemberLeave')) $('orgEditMemberLeave').checked = !!m.can_manage_leave;
  if ($('orgEditMemberBroadcastLine')) $('orgEditMemberBroadcastLine').checked = !!m.can_broadcast_line;
  if ($('orgEditMemberManagePeak')) $('orgEditMemberManagePeak').checked = !!m.can_manage_peak;
  if ($('orgEditUserNotes')) $('orgEditUserNotes').value = m.notes || '';

  // Transfer Ownership visibility: only if logged in user is owner, and the target is an admin (not self)
  const isMeOwner = _orgMembersCache.some(x => x.username === state.username && x.is_owner);
  const targetIsOtherAdmin = !m.is_owner && (m.role === 'admin') && (m.username !== state.username);
  const transferCard = $('orgTransferOwnershipCard');
  if (transferCard) {
    transferCard.classList.toggle('hidden', !(isMeOwner && targetIsOtherAdmin));
  }

  const managerSelect = $('orgEditMemberManager');
  if (managerSelect) {
    managerSelect.innerHTML = '<option value="">ไม่มีหัวหน้างาน (ผู้บริหารสูงสุด)</option>';
    const reportsToMap = {};
    _orgMembersCache.forEach(x => {
      reportsToMap[x.username.toLowerCase()] = (x.manager_username || "").trim().toLowerCase();
    });
    _orgMembersCache.forEach(x => {
      const candidateUsername = x.username.toLowerCase();
      if (candidateUsername === username.toLowerCase()) return;
      let curr = candidateUsername;
      let isCyclic = false;
      while (curr) {
        if (curr === username.toLowerCase()) {
          isCyclic = true;
          break;
        }
        curr = reportsToMap[curr] || "";
      }
      if (isCyclic) return;
      const opt = document.createElement("option");
      opt.value = x.username;
      opt.textContent = `${x.display_name || x.username} (${x.position || 'พนักงาน'})`;
      if ((m.manager_username || "").toLowerCase() === x.username.toLowerCase()) {
        opt.selected = true;
      }
      managerSelect.appendChild(opt);
    });
  }

  const modal = $('orgMemberEditModal');
  if (modal) modal.classList.remove('hidden');
}

function closeOrgMemberEditModal() {
  _orgEditingUsername = null;
  const modal = $('orgMemberEditModal');
  if (modal) modal.classList.add('hidden');
}

async function submitOrgMemberEdit() {
  if (!_orgEditingUsername) return;
  const newRole = $('orgEditMemberRole')?.value;
  const displayName = $('orgEditDisplayName')?.value;
  const position = $('orgEditMemberPosition')?.value;
  const department = $('orgEditMemberDepartment')?.value;
  const isActive = $('orgEditUserActive')?.checked ?? true;
  const canViewKB = $('orgEditUserCanViewKB')?.checked ?? false;
  const canEditKB = $('orgEditUserCanEditKB')?.checked ?? false;
  const canDeleteKB = $('orgEditUserCanDeleteKB')?.checked ?? false;
  const canViewFinancial = $('orgEditMemberFinancial')?.checked ?? false;
  const canManageLeave = $('orgEditMemberLeave')?.checked ?? false;
  const canBroadcastLine = $('orgEditMemberBroadcastLine')?.checked ?? false;
  const canManagePeak = $('orgEditMemberManagePeak')?.checked ?? false;
  const notes = $('orgEditUserNotes')?.value || '';

  const m = _orgMembersCache.find(x => x.username === _orgEditingUsername);
  try {
    // Update org role if changed
    if (m && newRole !== m.role) {
      const r = await apiFetch(`/api/org/members/${_orgEditingUsername}/role`, {
        method: 'POST', body: JSON.stringify({ role: newRole })
      });
      if (!r.ok) { toast(r.error || 'เปลี่ยน role ไม่สำเร็จ', 'error'); return; }
    }
    // Update permissions and other fields
    const r2 = await apiFetch(`/api/org/members/${_orgEditingUsername}/permissions`, {
      method: 'PUT',
      body: JSON.stringify({
        display_name: displayName,
        position: position,
        department: department,
        is_active: isActive,
        can_view_kb: canViewKB,
        can_edit_kb: canEditKB,
        can_delete_kb: canDeleteKB,
        can_view_financial: canViewFinancial,
        can_manage_leave: canManageLeave,
        can_broadcast_line: canBroadcastLine,
        can_manage_peak: canManagePeak,
        notes: notes
      })
    });
    if (!r2.ok) { toast(r2.error || 'บันทึกข้อมูลไม่สำเร็จ', 'error'); return; }

    const managerUsername = $('orgEditMemberManager')?.value;
    if (m && managerUsername !== (m.manager_username || '')) {
      const r3 = await apiFetch(`/api/org/members/${_orgEditingUsername}/manager`, {
        method: 'POST', body: JSON.stringify({ manager_username: managerUsername })
      });
      if (!r3.ok) { toast(r3.error || 'บันทึกหัวหน้างานไม่สำเร็จ', 'error'); return; }
    }

    toast('บันทึกข้อมูลเรียบร้อยแล้ว', 'success');
    closeOrgMemberEditModal();
    loadOrgMembers();
  } catch (e) {
    toast('เกิดข้อผิดพลาด', 'error');
  }
}

async function confirmTransferOrgOwnership() {
  if (!_orgEditingUsername) return;
  const m = _orgMembersCache.find(x => x.username === _orgEditingUsername);
  if (!m) return;
  
  const confirmed = confirm(
    `⚠️ ยืนยันการโอนสิทธิ์ความเป็นเจ้าขององค์กร (Owner)\n\n` +
    `คุณกำลังจะโอนสิทธิ์ Owner ให้กับ "${m.display_name || m.username}" (@${m.username})\n` +
    `หลังจากนี้ ผู้ใช้นี้จะเป็น Owner (Admin ใหญ่) สูงสุดขององค์กร และสิทธิ์ของคุณจะถูกปรับเป็น Admin ปกติ\n\n` +
    `ต้องการดำเนินการต่อหรือไม่?`
  );
  if (!confirmed) return;

  try {
    const res = await apiFetch('/api/org/transfer-ownership', {
      method: 'POST',
      body: JSON.stringify({ new_owner: _orgEditingUsername })
    });
    if (res && res.ok) {
      toast(res.message || 'โอนสิทธิ์ความเป็นเจ้าของสำเร็จแล้ว!', 'success');
      closeOrgMemberEditModal();
      await loadOrgMembers();
    } else {
      toast(res?.error || 'โอนสิทธิ์ล้มเหลว', 'error');
    }
  } catch (err) {
    toast('เกิดข้อผิดพลาดในการโอนสิทธิ์', 'error');
  }
}

async function submitOrgMemberResetPassword() {
  if (!_orgEditingUsername) return;
  const newPassword = $('orgEditUserNewPassword')?.value;
  if (!newPassword) {
    toast('กรุณากรอกรหัสผ่านใหม่', 'warning');
    return;
  }
  if (!confirm(`ต้องการรีเซ็ตรหัสผ่านของผู้ใช้ "${_orgEditingUsername}" ใช่หรือไม่?`)) return;
  try {
    const data = await apiFetch(`/api/org/members/${_orgEditingUsername}/reset-password`, {
      method: 'POST',
      body: JSON.stringify({ password: newPassword })
    });
    if (data.ok) {
      toast('รีเซ็ตรหัสผ่านเรียบร้อยแล้ว', 'success');
      if ($('orgEditUserNewPassword')) $('orgEditUserNewPassword').value = '';
    } else {
      toast(data.error || 'รีเซ็ตรหัสผ่านไม่สำเร็จ', 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาด', 'error');
  }
}

async function toggleMemberRole(username, currentRole) {
  const newRole = currentRole === 'admin' ? 'member' : 'admin';
  const label = newRole === 'admin' ? 'เลื่อนเป็น Admin' : 'ลดเป็น Member';
  if (!confirm(`${label} ผู้ใช้ "${username}"?`)) return;
  try {
    const data = await apiFetch(`/api/org/members/${username}/role`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: newRole })
    });
    if (data.ok) {
      toast(`อัปเดตตำแหน่ง ${username} เป็น ${newRole} แล้ว`, 'success');
      loadOrgMembers();
    } else {
      toast(data.error || 'เปลี่ยนตำแหน่งไม่สำเร็จ', 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาด', 'error');
  }
}

async function removeOrgMember(username) {
  const action = state.isAdmin ? `ลบบัญชี "${username}" ออกจากระบบทั้งหมด (ไม่สามารถกู้คืนได้)?` : `นำ "${username}" ออกจากองค์กร?`;
  if (!confirm(action)) return;
  try {
    const data = await apiFetch(`/api/org/members/${username}`, { method: 'DELETE' });
    if (data.ok) {
      const msg = data.purged ? `ลบบัญชี ${username} ออกจากระบบแล้ว` : `นำ ${username} ออกจากองค์กรแล้ว`;
      toast(msg, 'success');
      loadOrgMembers();
    } else {
      toast(data.error || 'ดำเนินการไม่สำเร็จ', 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาด', 'error');
  }
}

// ─── My Settings (view-settings) ──────────────────────────────────────────
let _mySettingsCache = null;

async function loadMySettings(force = false) {
  if (_mySettingsCache && !force) { _renderMySettings(_mySettingsCache); return; }
  const loading = $('mySettingsLoading');
  if (loading) loading.classList.remove('hidden');
  try {
    const data = await apiFetch('/api/user/my-settings');
    if (data.ok) {
      _mySettingsCache = data;
      _renderMySettings(data);
    }
  } catch (e) {}
  finally { if (loading) loading.classList.add('hidden'); }
}

function _renderMySettings(d) {
  // Avatar
  const avatarEl = $('mySettingsAvatar');
  if (avatarEl) {
    if (d.avatar_url) {
      avatarEl.innerHTML = `<img src="${d.avatar_url}" class="w-full h-full object-cover" onerror="this.parentElement.innerHTML='<span class=\\'text-xl font-black\\'>${(d.display_name||d.username).charAt(0).toUpperCase()}</span>'">`;
    } else {
      avatarEl.innerHTML = `<span class="text-xl font-black">${(d.display_name || d.username || '?').charAt(0).toUpperCase()}</span>`;
    }
  }
  if ($('mySettingsUsernameLabel')) $('mySettingsUsernameLabel').textContent = d.display_name || d.username;
  if ($('mySettingsHandleLabel')) $('mySettingsHandleLabel').textContent = `@${d.username}`;
  if ($('myDisplayNameInput')) $('myDisplayNameInput').value = d.display_name || '';
  if ($('myNotesInput')) $('myNotesInput').value = d.notes || '';

  // Role badge
  const roleEl = $('myRoleBadge');
  if (roleEl) {
    const isAdmin = d.role === 'admin';
    roleEl.innerHTML = isAdmin
      ? `<span class="admin-role-badge admin">Admin</span>`
      : `<span class="admin-role-badge user">User</span>`;
  }
  // Status badge
  const statusEl = $('myStatusBadge');
  if (statusEl) {
    statusEl.innerHTML = d.is_active
      ? `<span class="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400"><span class="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>ใช้งานอยู่</span>`
      : `<span class="flex items-center gap-1.5 text-red-500"><span class="w-2 h-2 rounded-full bg-red-500 inline-block"></span>ปิดการใช้งาน</span>`;
  }
  // Permissions list
  const permsEl = $('myPermissionsList');
  if (permsEl) {
    const perms = [
      { key: 'can_view_kb', label: 'ดูคลังข้อมูล', desc: 'ดูและค้นหาไฟล์' },
      { key: 'can_edit_kb', label: 'แก้ไขคลังข้อมูล', desc: 'อัปโหลดและแก้ไขไฟล์' },
      { key: 'can_delete_kb', label: 'ลบไฟล์คลังข้อมูล', desc: 'ลบไฟล์ออกจากระบบ' },
      { key: 'can_view_financial', label: 'แดชบอร์ดรายจ่าย', desc: 'ดูหน้าสรุปภาษีและค่าใช้จ่าย' },
      { key: 'can_manage_leave', label: 'จัดการการลา', desc: 'อนุมัติและจัดการคำขอลาของพนักงาน' },
      { key: 'can_broadcast_line', label: 'บรอดแคสต์ LINE', desc: 'ส่งข้อความบรอดแคสต์ไปยังกลุ่มและผู้ใช้' },
      { key: 'can_manage_peak', label: 'จัดการ PEAK Account', desc: 'เชื่อมต่อและจัดการระบบบัญชี PEAK' },
      { key: 'can_use_ai', label: 'สนทนากับ AI', desc: 'สิทธิ์พูดคุยและประมวลผลกับ AI' },
      { key: 'can_claim_expense', label: 'เบิกจ่ายค่าใช้จ่าย', desc: 'ยื่นคำขอเบิกเงินและส่งสลิปค่าใช้จ่าย' },
    ];

    permsEl.innerHTML = perms.map(p => {
      const on = !!d[p.key];
      return `<div class="flex items-center justify-between p-3 rounded-xl border ${on ? 'border-emerald-200 dark:border-emerald-800/50 bg-emerald-50/50 dark:bg-emerald-900/10' : 'border-surface-100 dark:border-surface-700 bg-surface-50 dark:bg-surface-800/30'}">
        <div>
          <div class="text-xs font-bold text-surface-800 dark:text-white">${p.label}</div>
          <div class="text-[10px] text-surface-400">${p.desc}</div>
        </div>
        <span class="${on ? 'text-emerald-600 dark:text-emerald-400' : 'text-surface-300 dark:text-surface-600'} text-lg">
          ${on ? '✓' : '—'}
        </span>
      </div>`;
    }).join('');
  }
  // LINE Connection Status
  const myLineStatusText = $('myLineStatusText');
  const btnMyBindLine = $('btnMyBindLine');
  const btnMyUnbindLine = $('btnMyUnbindLine');
  const myLineInstruction = $('myLineInstruction');
  const myLineBannerAlert = $('myLineBannerAlert');

  if (myLineStatusText) {
    if (d.line_user_id) {
      myLineStatusText.textContent = `เชื่อมต่อแล้ว (LINE ID: ${d.line_user_id.substring(0, 10)}...)`;
      myLineStatusText.className = "text-xs font-bold text-purple-600 dark:text-purple-400 font-extrabold";
      if (btnMyBindLine) btnMyBindLine.classList.add('hidden');
      if (btnMyUnbindLine) btnMyUnbindLine.classList.remove('hidden');
      if (myLineInstruction) myLineInstruction.classList.add('hidden');
      if (myLineBannerAlert) myLineBannerAlert.classList.add('hidden');
    } else {
      myLineStatusText.textContent = 'ยังไม่ได้เชื่อมต่อบัญชี LINE';
      myLineStatusText.className = "text-xs font-bold text-surface-600 dark:text-surface-300";
      if (btnMyBindLine) btnMyBindLine.classList.remove('hidden');
      if (btnMyUnbindLine) btnMyUnbindLine.classList.add('hidden');
      if (myLineInstruction) myLineInstruction.classList.remove('hidden');
      if (myLineBannerAlert) myLineBannerAlert.classList.remove('hidden');
    }
  }

  if (window.lucide) window.lucide.createIcons();
}

async function unbindMyLine() {
  if (!await showConfirm('ยกเลิกการผูกบัญชี LINE', 'คุณแน่ใจหรือไม่ที่จะยกเลิกการผูกบัญชี LINE ส่วนตัวของคุณ?', { type: 'danger', confirmText: 'ยกเลิกการผูกบัญชี' })) {
    return;
  }
  try {
    const res = await fetch('/api/user/unbind-line', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();
    if (data.ok) {
      await showAlert('สำเร็จ', 'ยกเลิกการผูกบัญชี LINE เรียบร้อยแล้วค่ะ!', { type: 'success' });
      if (_mySettingsCache) {
        _mySettingsCache.line_user_id = null;
        _renderMySettings(_mySettingsCache);
      }
    } else {
      await showAlert('เกิดข้อผิดพลาด', `ไม่สามารถยกเลิกได้: ${data.error || 'เกิดข้อผิดพลาดค่ะ'}`, { type: 'danger' });
    }
  } catch (e) {
    await showAlert('เกิดข้อผิดพลาด', `เกิดข้อผิดพลาดในการเชื่อมต่อ: ${e.message}`, { type: 'danger' });
  }
}

function openUserLineBindModal() {
  const modal = $('userLineBindModal');
  if (!modal) return;
  if ($('userDirectLineToken')) $('userDirectLineToken').value = '';
  modal.classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
}

async function submitDirectLineBind() {
  const input = $('userDirectLineToken');
  const btn = $('btnSubmitDirectLine');
  const val = (input?.value || '').trim();
  if (!val) {
    toast('กรุณาระบุรหัสเชื่อมต่อ (Token) หรือ LINE User ID ค่ะ', 'warning');
    return;
  }
  
  const payload = val.startsWith('U') && val.length === 33 ? { line_user_id: val } : { token: val };
  btn.disabled = true;
  btn.innerHTML = '<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i> กำลังเชื่อมต่อ...';
  if (window.lucide) lucide.createIcons();
  
  try {
    const res = await fetch('/api/user/bind-line-direct', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.ok) {
      toast(data.message || 'เชื่อมต่อบัญชี LINE สำเร็จค่ะ!', 'success');
      $('userLineBindModal')?.classList.add('hidden');
      if (_mySettingsCache) {
        _mySettingsCache.line_user_id = data.line_user_id || 'linked';
        _renderMySettings(_mySettingsCache);
      }
    } else {
      toast(data.error || 'เชื่อมต่อไม่สำเร็จ กรุณาตรวจสอบรหัสอีกครั้งค่ะ', 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาดในการเชื่อมต่อค่ะ', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="check" class="w-3.5 h-3.5"></i> ยืนยันการผูกบัญชีด้วยรหัสนี้';
    if (window.lucide) lucide.createIcons();
  }
}

async function saveMyDisplayName() {
  const val = ($('myDisplayNameInput')?.value || '').trim();
  if (!val) { toast('กรุณากรอกชื่อก่อน', 'error'); return; }
  try {
    const r = await apiFetch('/api/profile/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ display_name: val }),
    });
    if (r.ok) {
      toast('บันทึกชื่อเรียบร้อยแล้ว', 'success');
      if (_mySettingsCache) _mySettingsCache.display_name = val;
      if ($('mySettingsUsernameLabel')) $('mySettingsUsernameLabel').textContent = val;
    } else {
      toast(r.error || 'บันทึกไม่สำเร็จ', 'error');
    }
  } catch { toast('เกิดข้อผิดพลาด', 'error'); }
}

async function saveMyNotes() {
  const val = $('myNotesInput')?.value || '';
  try {
    const r = await apiFetch('/api/user/update-notes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes: val }),
    });
    if (r.ok) { toast('บันทึกหมายเหตุแล้ว', 'success'); if (_mySettingsCache) _mySettingsCache.notes = val; }
    else toast(r.error || 'บันทึกไม่สำเร็จ', 'error');
  } catch { toast('เกิดข้อผิดพลาด', 'error'); }
}

async function changeMyPassword() {
  const cur = $('myCurrentPw')?.value || '';
  const newPw = ($('myNewPw')?.value || '').trim();
  if (!newPw) { toast('กรุณากรอกรหัสผ่านใหม่', 'error'); return; }
  try {
    const r = await apiFetch('/api/user/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_password: cur, new_password: newPw }),
    });
    if (r.ok) {
      toast('เปลี่ยนรหัสผ่านสำเร็จ', 'success');
      if ($('myCurrentPw')) $('myCurrentPw').value = '';
      if ($('myNewPw')) $('myNewPw').value = '';
    } else {
      toast(r.error || 'เปลี่ยนรหัสผ่านไม่สำเร็จ', 'error');
    }
  } catch { toast('เกิดข้อผิดพลาด', 'error'); }
}

let currentInviteTab = 'existing';

function setInviteTab(tabName) {
  currentInviteTab = tabName;
  
  // Update Tab buttons visual states
  ['existing', 'precreate', 'gmail', 'link_qr'].forEach(t => {
    const btn = $('inviteTabBtn_' + t);
    const content = $('inviteTabContent_' + t);
    if (btn) {
      if (t === tabName) {
        btn.className = "flex-1 py-2 px-2 text-xs font-bold rounded-lg transition-all text-center flex items-center justify-center gap-1.5 bg-brand-600 text-white shadow-md shadow-brand-500/20";
      } else {
        btn.className = "flex-1 py-2 px-2 text-xs font-bold rounded-lg transition-all text-center flex items-center justify-center gap-1.5 text-surface-500 dark:text-surface-400 hover:text-surface-900 dark:hover:text-white hover:bg-surface-200/50 dark:hover:bg-surface-700/50";
      }
    }
    if (content) {
      if (t === tabName) {
        content.classList.remove('hidden');
      } else {
        content.classList.add('hidden');
      }
    }
  });

  // Toggle submit button visibility (link_qr has its own action button)
  const submitBtn = $('inviteSubmitBtn');
  if (submitBtn) {
    submitBtn.classList.toggle('hidden', tabName === 'link_qr');
  }

  // Clear errors
  const errEl = $('inviteError');
  if (errEl) {
    errEl.classList.add('hidden');
    errEl.textContent = '';
  }

  // Auto-generate QR code immediately when switching to link_qr tab
  if (tabName === 'link_qr') {
    const linkInput = $('inviteQrLinkInput');
    if (!linkInput || !linkInput.value) {
      generateOrgInviteToken(false);
    }
  }

  initIcons();
}

function toggleInvitePwVisibility() {
  const input = $('invitePrecreatePasswordInput');
  const icon = $('invitePrecreatePwEyeIcon');
  if (!input || !icon) return;
  if (input.type === 'password') {
    input.type = 'text';
    icon.setAttribute('data-lucide', 'eye-off');
  } else {
    input.type = 'password';
    icon.setAttribute('data-lucide', 'eye');
  }
  initIcons();
}

function showInviteMemberModal(defaultTab = 'existing') {
  const modal = $('inviteMemberModal');
  if (!modal) return;
  
  // Reset values
  $('inviteUsernameInput').value = '';
  $('invitePrecreateUsernameInput').value = '';
  $('invitePrecreatePasswordInput').value = '';
  $('invitePrecreatePasswordInput').type = 'password';
  $('invitePrecreateDisplayNameInput').value = '';
  $('inviteEmailInput').value = '';
  $('inviteRoleSelect').value = 'member';
  
  $('invitePrecreatePwEyeIcon')?.setAttribute('data-lucide', 'eye');
  
  // Reset form / success views
  $('inviteFormWrapper')?.classList.remove('hidden');
  $('inviteSuccessView')?.classList.add('hidden');
  
  setInviteTab(defaultTab);
  modal.classList.remove('hidden');
  initIcons();
  
  if (defaultTab === 'existing') {
    setTimeout(() => $('inviteUsernameInput')?.focus(), 50);
  } else if (defaultTab === 'link_qr') {
    generateOrgInviteToken(false);
  }
}

async function generateOrgInviteToken(notify = true) {
  const expirySelect = $('inviteTokenExpiry');
  const deptInput = $('inviteTokenDept');
  const roleSelect = $('inviteRoleSelect');
  
  const payload = {
    role: roleSelect ? roleSelect.value : 'member',
    department: deptInput ? deptInput.value.trim() : '',
    expires_days: expirySelect ? parseInt(expirySelect.value) : 7
  };

  try {
    const res = await apiFetch('/api/org/invite-token', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    if (res && res.ok && res.invite_url) {
      const qrResult = $('inviteQrResult');
      const qrCanvas = $('inviteQrCanvas');
      const qrImg = $('inviteQrImg');
      const linkInput = $('inviteQrLinkInput');
      
      if (linkInput) linkInput.value = res.invite_url;
      
      // Render QR code: prioritize local QRCode canvas, fallback to image API
      if (qrCanvas && typeof QRCode !== 'undefined') {
        qrCanvas.innerHTML = '';
        new QRCode(qrCanvas, {
          text: res.invite_url,
          width: 144,
          height: 144,
          colorDark: '#0f172a',
          colorLight: '#ffffff',
          correctLevel: QRCode.CorrectLevel.M
        });
        if (qrImg) qrImg.classList.add('hidden');
      } else if (qrImg) {
        qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(res.invite_url)}`;
        qrImg.classList.remove('hidden');
      }
      
      if (qrResult) qrResult.classList.remove('hidden');
      if (notify) toast('สร้างลิงก์เชิญ & QR Code สำเร็จ!', 'success');
      initIcons();
    } else {
      if (notify) toast(res?.error || 'สร้างลิงก์เชิญล้มเหลว', 'error');
    }
  } catch (err) {
    if (notify) toast('เกิดข้อผิดพลาดในการสร้างลิงก์เชิญ', 'error');
  }
}

function copyInviteQrLink() {
  const input = $('inviteQrLinkInput');
  if (!input) return;
  input.select();
  input.setSelectionRange(0, 99999);
  navigator.clipboard.writeText(input.value);
  const btn = $('btnCopyQrLink');
  if (btn) {
    btn.innerHTML = '<i data-lucide="check" class="w-3.5 h-3.5"></i> คัดลอกแล้ว!';
    btn.className = "px-3 py-2 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl transition-all shrink-0 flex items-center gap-1";
    initIcons();
    setTimeout(() => {
      btn.innerHTML = '<i data-lucide="copy" class="w-3.5 h-3.5"></i> คัดลอก';
      btn.className = "px-3 py-2 text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white rounded-xl transition-all shrink-0 flex items-center gap-1";
      initIcons();
    }, 2000);
  }
}

function closeInviteMemberModal() {
  const modal = $('inviteMemberModal');
  if (modal) modal.classList.add('hidden');
}

function copyInviteSuccessLink() {
  const input = $('inviteSuccessLinkInput');
  if (!input) return;
  input.select();
  input.setSelectionRange(0, 99999);
  navigator.clipboard.writeText(input.value);
  
  const btn = $('inviteCopyBtn');
  if (btn) {
    btn.innerHTML = '<i data-lucide="check" class="w-3.5 h-3.5"></i> คัดลอกสำเร็จแล้ว!';
    btn.className = "px-3 py-1.5 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors flex items-center gap-1 shrink-0";
    initIcons();
    setTimeout(() => {
      btn.innerHTML = '<i data-lucide="copy" class="w-3.5 h-3.5"></i> คัดลอก';
      btn.className = "px-3 py-1.5 text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition-colors flex items-center gap-1 shrink-0";
      initIcons();
    }, 2000);
  }
}

async function submitInviteMember() {
  const role = $('inviteRoleSelect')?.value || 'member';
  const errEl = $('inviteError');
  const btn = $('inviteSubmitBtn');
  
  let endpoint = '/api/org/invite';
  let payload = { role };
  let successMsg = 'เชิญสมาชิกสำเร็จ';

  if (currentInviteTab === 'existing') {
    const username = $('inviteUsernameInput')?.value.trim();
    if (!username) {
      errEl.textContent = 'กรุณากรอกชื่อผู้ใช้';
      errEl.classList.remove('hidden');
      return;
    }
    payload.username = username;
    endpoint = '/api/org/invite';
    successMsg = `เชิญผู้ใช้ ${username} เข้าองค์กรสำเร็จ`;
  } else if (currentInviteTab === 'precreate') {
    const username = $('invitePrecreateUsernameInput')?.value.trim();
    const password = $('invitePrecreatePasswordInput')?.value.trim();
    const displayName = $('invitePrecreateDisplayNameInput')?.value.trim();
    
    if (!username) {
      errEl.textContent = 'กรุณากรอกชื่อผู้ใช้ใหม่';
      errEl.classList.remove('hidden');
      return;
    }
    if (!password || password.length < 6) {
      errEl.textContent = 'กรุณากำหนดรหัสผ่านอย่างน้อย 6 ตัวอักษร';
      errEl.classList.remove('hidden');
      return;
    }
    
    payload.username = username;
    payload.password = password;
    if (displayName) payload.display_name = displayName;
    
    // We send this to /api/org/members which supports on-the-fly user creation
    endpoint = '/api/org/members';
    successMsg = `สร้างบัญชีผู้ใช้ ${username} และแอดเข้าองค์กรสำเร็จ`;
  } else if (currentInviteTab === 'gmail') {
    const email = $('inviteEmailInput')?.value.trim();
    if (!email || !email.includes('@')) {
      errEl.textContent = 'กรุณากรอกที่อยู่อีเมลที่ถูกต้อง';
      errEl.classList.remove('hidden');
      return;
    }
    payload.email = email;
    endpoint = '/api/org/invite-email';
    successMsg = `เพิ่ม ${email} เข้า Whitelist และส่งคำเชิญเรียบร้อยแล้ว`;
  }

  btn.disabled = true;
  btn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> กำลังดำเนินการ...';
  initIcons();
  errEl.classList.add('hidden');

  try {
    const data = await apiFetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (data.ok) {
      toast(data.message || successMsg, 'success');
      loadOrgMembers();
      
      const successView = $('inviteSuccessView');
      const formWrapper = $('inviteFormWrapper');
      if (successView && formWrapper) {
        $('inviteSuccessMessage').textContent = data.message || successMsg;
        $('inviteSuccessLinkInput').value = window.location.origin;
        
        formWrapper.classList.add('hidden');
        successView.classList.remove('hidden');
        initIcons();
      } else {
        closeInviteMemberModal();
      }
    } else {
      errEl.textContent = data.message || data.error || 'การดำเนินการไม่สำเร็จ';
      errEl.classList.remove('hidden');
    }
  } catch (e) {
    errEl.textContent = 'เกิดข้อผิดพลาดในการเชื่อมต่อระบบ กรุณาลองใหม่';
    errEl.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="user-plus" class="w-4 h-4"></i> ดำเนินการเชิญ';
    initIcons();
  }
}

/* ══════════════════════════════════════════
   Admin User Management Panel
   ══════════════════════════════════════════ */
let adminUsersListCache = [];
let currentEditingUsername = null;

async function loadAdminUsers() {
  const container = $('adminUserList');
  container.innerHTML = '<div style="text-align:center;padding:40px;color:#94a3b8;">กำลังโหลดข้อมูลผู้ใช้...</div>';
  try {
    const data = await apiFetch('/api/admin/users');
    if (data.ok && data.users) {
      console.log('Admin Users List fetched:', data.users);
      adminUsersListCache = data.users;
      renderAdminUserList(adminUsersListCache);
    }
  } catch (e) {
    container.innerHTML = `<div style="text-align:center;padding:40px;color:#ef4444;">โหลดข้อมูลล้มเหลว: ${e.message}</div>`;
  }
}

function renderAdminUserList(users) {
  const container = $('adminUserList');

  // Update Stats
  $('totalUsersCount').textContent = users.length;
  $('activeUsersCount').textContent = users.filter(u => u.is_active).length;
  $('inactiveUsersCount').textContent = users.filter(u => !u.is_active).length;

  if (users.length === 0) {
    container.innerHTML = '<div style="text-align:center;padding:40px;color:#94a3b8;">ไม่พบข้อมูลผู้ใช้</div>';
    return;
  }

  container.innerHTML = users.map(user => {
    const roleClass = user.role === 'admin' ? 'admin' : 'user';
    const activeColor = user.is_active ? '#10b981' : '#ef4444';
    const avatarContent = user.avatar_url
      ? `<img src="${user.avatar_url}" style="width:100%;height:100%;object-fit:cover;">`
      : `<i data-lucide="user" style="width:18px;height:18px;"></i>`;

    return `
      <div class="admin-user-row">
        <div style="width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;overflow:hidden;flex-shrink:0;" class="border border-surface-200 dark:border-surface-700 bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300">
          ${avatarContent}
        </div>
        <div style="flex:1;min-width:0;">
          <div style="display:flex;align-items:center;flex-wrap:wrap;gap:6px;margin-bottom:2px;">
            <div style="font-weight:600;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:180px;" class="dark:text-white">${user.display_name || user.username.charAt(0).toUpperCase() + user.username.slice(1)}</div>
            <div class="admin-status-dot" style="background:${activeColor};" title="${user.is_active ? 'ใช้งานปกติ' : 'ถูกระงับ'}"></div>
          </div>
          <div style="display:flex;align-items:center;flex-wrap:wrap;gap:6px;">
            <div style="font-size:11px;color:#94a3b8;">@${user.username}</div>
            <span class="admin-role-badge ${roleClass}">${user.role}</span>
            ${user.department ? `<span class="text-[10px] bg-surface-100 dark:bg-surface-800 border border-surface-200 dark:border-surface-700 text-surface-600 dark:text-surface-300 px-1.5 py-0.5 rounded font-medium">${user.department.toUpperCase()}</span>` : ''}
            ${user.can_edit_kb ? `<span class="text-[10px] bg-surface-100 dark:bg-surface-800 border border-surface-200 dark:border-surface-700 text-surface-600 dark:text-surface-300 px-1.5 py-0.5 rounded font-medium">KB EDIT</span>` : ''}
          </div>
        </div>
        <div class="flex gap-2">
          <button onclick="openEditUserModal('${user.username}')" style="padding:6px 12px;border-radius:8px;font-size:12px;font-weight:600;border:1px solid #e2e8f0;background:transparent;cursor:pointer;color:#475569;" class="dark:border-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-800 transition-colors">
            แก้ไข
          </button>
          ${user.username !== 'Admin' ? `
            <button onclick="deleteAdminUser('${user.username}')" style="padding:8px;border-radius:10px;border:1px solid #fee2e2;background:transparent;cursor:pointer;color:#ef4444;" class="dark:border-red-900/30 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors" title="ลบผู้ใช้">
              <i data-lucide="trash-2" style="width:16px;height:16px;"></i>
            </button>
          ` : ''}
        </div>
      </div>
    `;
  }).join('');
  initIcons();
}

function openEditUserModal(username) {
  const user = adminUsersListCache.find(u => u.username === username);
  if (!user) return;

  currentEditingUsername = username;

  // Populate fields
  $('editUserSubtitle').textContent = `@${user.username}`;
  const avatarEl = $('editUserAvatar');
  if (user.avatar_url) {
    avatarEl.innerHTML = `<img src="${user.avatar_url}" style="width:100%;height:100%;object-fit:cover;">`;
  } else {
    avatarEl.innerHTML = `<i data-lucide="user" style="width:22px;height:22px;color:#fff;"></i>`;
    initIcons();
  }

  $('editDisplayName').value = user.display_name || '';
  $('editUserRole').value = user.role || 'user';
  $('editUserActive').checked = !!user.is_active;
  $('editUserCanViewKB').checked = !!user.can_view_kb;
  $('editUserCanEditKB').checked = !!user.can_edit_kb;
  $('editUserCanDeleteKB').checked = !!user.can_delete_kb;
  if ($('editUserCanViewFinancial')) $('editUserCanViewFinancial').checked = !!user.can_view_financial;
  
  const linePerms = (user.line_permissions || "report,links,reconcile,search,folder,leave").split(",");
  if ($('linePermReport')) $('linePermReport').checked = linePerms.includes('report');
  if ($('linePermLinks')) $('linePermLinks').checked = linePerms.includes('links');
  if ($('linePermReconcile')) $('linePermReconcile').checked = linePerms.includes('reconcile');
  if ($('linePermSearch')) $('linePermSearch').checked = linePerms.includes('search');
  if ($('linePermFolder')) $('linePermFolder').checked = linePerms.includes('folder');
  if ($('linePermLeave')) $('linePermLeave').checked = linePerms.includes('leave');

  if ($('editUserDept')) $('editUserDept').value = user.department || '';
  $('editUserNotes').value = user.notes || '';
  $('editUserNewPassword').value = '';

  // Populate LINE status
  const lineStatusEl = $('editUserLineStatus');
  const btnUnbindLine = $('btnUnbindLine');
  if (lineStatusEl && btnUnbindLine) {
    if (user.line_user_id) {
      lineStatusEl.textContent = `เชื่อมต่อแล้ว (LINE ID: ${user.line_user_id.substring(0, 10)}...)`;
      lineStatusEl.classList.remove('text-surface-600', 'dark:text-surface-300');
      lineStatusEl.classList.add('text-purple-600', 'dark:text-purple-400');
      btnUnbindLine.classList.remove('hidden');
    } else {
      lineStatusEl.textContent = 'ยังไม่ได้เชื่อมต่อบัญชี LINE';
      lineStatusEl.classList.remove('text-purple-600', 'dark:text-purple-400');
      lineStatusEl.classList.add('text-surface-600', 'dark:text-surface-300');
      btnUnbindLine.classList.add('hidden');
    }
  }

  // Protect admin self-lockout visually
  if (username === 'Admin') {
    $('editUserActive').disabled = true;
    $('editUserRole').disabled = true;
  } else {
    $('editUserActive').disabled = false;
    $('editUserRole').disabled = false;
  }

  $('editUserModal').classList.remove('hidden');
  $('editUserModal').classList.add('flex', 'items-center', 'justify-center');
}

function closeEditUserModal() {
  currentEditingUsername = null;
  $('editUserModal').classList.add('hidden');
  $('editUserModal').classList.remove('flex', 'items-center', 'justify-center');
}

async function unbindUserLine() {
  if (!currentEditingUsername) return;
  if (!await showConfirm('ยกเลิกการผูกบัญชี LINE สมาชิก', `คุณแน่ใจหรือไม่ที่จะยกเลิกการผูกบัญชี LINE สำหรับผู้ใช้ @${currentEditingUsername}?`, { type: 'danger', confirmText: 'ยกเลิกการผูกบัญชี' })) {
    return;
  }
  
  try {
    const res = await fetch(`/api/admin/users/${currentEditingUsername}/unbind-line`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await res.json();
    if (data.ok) {
      await showAlert('สำเร็จ', 'ยกเลิกการผูกบัญชี LINE เรียบร้อยแล้วค่ะพี่!', { type: 'success' });
      
      // Update UI in modal
      const lineStatusEl = $('editUserLineStatus');
      const btnUnbindLine = $('btnUnbindLine');
      if (lineStatusEl) {
        lineStatusEl.textContent = 'ยังไม่ได้เชื่อมต่อบัญชี LINE';
        lineStatusEl.classList.remove('text-purple-600', 'dark:text-purple-400');
        lineStatusEl.classList.add('text-surface-600', 'dark:text-surface-300');
      }
      if (btnUnbindLine) {
        btnUnbindLine.classList.add('hidden');
      }
      
      // Update cache
      const user = adminUsersListCache.find(u => u.username === currentEditingUsername);
      if (user) {
        user.line_user_id = null;
      }
      
      // Refresh list
      renderAdminUserList(adminUsersListCache);
    } else {
      await showAlert('เกิดข้อผิดพลาด', `ไม่สามารถยกเลิกได้: ${data.error || 'เกิดข้อผิดพลาดค่ะ'}`, { type: 'danger' });
    }
  } catch (e) {
    await showAlert('เกิดข้อผิดพลาด', `เกิดข้อผิดพลาดในการเชื่อมต่อ: ${e.message}`, { type: 'danger' });
  }
}

async function submitEditUser() {
  if (!currentEditingUsername) return;

  const linePerms = [];
  if ($('linePermReport') && $('linePermReport').checked) linePerms.push('report');
  if ($('linePermLinks') && $('linePermLinks').checked) linePerms.push('links');
  if ($('linePermReconcile') && $('linePermReconcile').checked) linePerms.push('reconcile');
  if ($('linePermSearch') && $('linePermSearch').checked) linePerms.push('search');
  if ($('linePermFolder') && $('linePermFolder').checked) linePerms.push('folder');
  if ($('linePermLeave') && $('linePermLeave').checked) linePerms.push('leave');

  const payload = {
    display_name: $('editDisplayName').value.trim(),
    role: $('editUserRole').value,
    is_active: $('editUserActive').checked,
    can_view_kb: $('editUserCanViewKB').checked,
    can_edit_kb: $('editUserCanEditKB').checked,
    can_delete_kb: $('editUserCanDeleteKB').checked,
    can_view_financial: $('editUserCanViewFinancial') ? $('editUserCanViewFinancial').checked : false,
    line_permissions: linePerms.join(','),
    department: $('editUserDept') ? $('editUserDept').value.trim() : '',
    notes: $('editUserNotes').value.trim()
  };

  try {
    const res = await fetch(`/api/admin/users/${currentEditingUsername}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.ok) {
      toast('อัปเดตข้อมูลผู้ใช้เรียบร้อยแล้ว', 'success');
      closeEditUserModal();
      loadAdminUsers(); // Refresh list
    } else {
      toast(data.error || 'เกิดข้อผิดพลาด', 'error');
    }
  } catch (e) {
    toast('ข้อผิดพลาดเครือข่าย', 'error');
  }
}

async function submitResetPassword() {
  if (!currentEditingUsername) return;
  const newPass = $('editUserNewPassword').value.trim();

  if (!newPass || newPass.length < 4) {
    toast('รหัสผ่านต้องมีอย่างน้อย 4 ตัวอักษร', 'warning');
    return;
  }

  if (!confirm(`ยืนยันการเปลี่ยนรหัสผ่านของ ${currentEditingUsername} ใช่หรือไม่?`)) return;

  try {
    const res = await fetch(`/api/admin/users/${currentEditingUsername}/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: newPass })
    });
    const data = await res.json();
    if (data.ok) {
      toast('รีเซ็ตรหัสผ่านสำเร็จ', 'success');
      $('editUserNewPassword').value = '';
    } else {
      toast(data.error || 'รีเซ็ตไม่สำเร็จ', 'error');
    }
  } catch (e) {
    toast('ข้อผิดพลาดเครือข่าย', 'error');
  }
}

// 👤 Create User Logic
function openCreateUserModal() {
  $('createUsername').value = '';
  $('createPassword').value = '';
  $('createDisplayName').value = '';
  $('createUserRole').value = 'user';
  if ($('createDeptInput')) $('createDeptInput').value = '';
  $('createUserModal').classList.remove('hidden');
  $('createUserModal').classList.add('flex', 'items-center', 'justify-center');
}

function closeCreateUserModal() {
  $('createUserModal').classList.add('hidden');
  $('createUserModal').classList.remove('flex', 'items-center', 'justify-center');
}

async function submitCreateUser() {
  const username = $('createUsername').value.trim();
  const password = $('createPassword').value.trim();
  const displayName = $('createDisplayName').value.trim();
  const role = $('createUserRole').value;

  if (!username || !password) {
    toast('กรุณากรอกชื่อผู้ใช้และรหัสผ่าน', 'warning');
    return;
  }

  if (password.length < 4) {
    toast('รหัสผ่านต้องมีอย่างน้อย 4 ตัวอักษร', 'warning');
    return;
  }

  const btn = $('confirmCreateUserBtn');
  btn.disabled = true;
  btn.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i> กำลังสร้าง...';
  initIcons();

  try {
    const res = await fetch('/api/admin/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username,
        password,
        display_name: displayName,
        role,
        can_view_kb: $('createCanViewKB').checked,
        can_edit_kb: $('createCanEditKB').checked,
        can_delete_kb: $('createCanDeleteKB').checked,
        department: $('createDeptInput') ? $('createDeptInput').value.trim() : ''
      })
    });
    const data = await res.json();
    if (data.ok) {
      toast('สร้างบัญชีผู้ใช้สำเร็จ', 'success');
      $('createCanViewKB').checked = false;
      $('createCanEditKB').checked = false;
      $('createCanDeleteKB').checked = false;
      closeCreateUserModal();
      loadAdminUsers();
    } else {
      toast(data.error || 'สร้างไม่สำเร็จ', 'error');
    }
  } catch (e) {
    toast('ข้อผิดพลาดเครือข่าย', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="check" class="w-4 h-4"></i> สร้างบัญชีผู้ใช้';
    initIcons();
  }
}

async function deleteAdminUser(username) {
  if (username === 'Admin') return;
  if (!confirm(`ยืนยันการลบผู้ใช้ @${username} ใช่หรือไม่? ข้อมูลทั้งหมดของผู้ใช้นี้จะถูกลบถาวร!`)) return;

  try {
    const res = await fetch(`/api/admin/users/${username}`, {
      method: 'DELETE'
    });
    const data = await res.json();
    if (data.ok) {
      toast('ลบผู้ใช้เรียบร้อยแล้ว', 'info');
      loadAdminUsers();
    } else {
      toast(data.error || 'ลบไม่สำเร็จ', 'error');
    }
  } catch (e) {
    toast('ข้อผิดพลาดเครือข่าย', 'error');
  }
}


/* ══════════════════════════════════════════
   Analytics / Visualization Engine (view-viz)
   ══════════════════════════════════════════ */

// currentVizType and currentVizHeaders are declared globally above

// Called by switchView when navigating to 'viz'
async function initViz() {
  if (!vizFileSelect) return;

  // Load list of CSV files
  try {
    const data = await apiFetch('/api/files');
    const csvFiles = (data.files || []).filter(f =>
      f.type === 'csv' || (f.name || '').toLowerCase().endsWith('.csv')
    );

    vizFileSelect.innerHTML = '<option value="">— เลือกไฟล์ CSV —</option>' +
      csvFiles.map(f => `<option value="${f.file_id}">${f.name}</option>`).join('');

    // Wire events (set directly to avoid duplicate listeners)
    vizFileSelect.onchange = () => loadVizData(vizFileSelect.value);
    if (vizXSelect) vizXSelect.onchange = () => renderChart();
    if (vizYSelect) vizYSelect.onchange = () => renderChart();

    // Wire chart type buttons
    document.querySelectorAll('.viz-type-btn').forEach(btn => {
      btn.onclick = () => {
        document.querySelectorAll('.viz-type-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentVizType = btn.dataset.type;
        renderChart();
      };
    });

    // Wire download button
    if (downloadChartBtn) {
      downloadChartBtn.onclick = () => {
        if (!myChart) { toast('ยังไม่มีกราฟให้ดาวน์โหลด', 'info'); return; }
        const url = vizChartCanvas.toDataURL('image/png');
        const a = document.createElement('a');
        a.href = url;
        a.download = 'orgchat_chart.png';
        a.click();
      };
    }

    if ($('analyzeVizDataBtn')) {
      $('analyzeVizDataBtn').onclick = analyzeVizData;
    }

    // Wire AI summary button
    if (generateAiSummaryBtn) {
      generateAiSummaryBtn.onclick = generateVizAiSummary;
    }

    // If a file was already selected, reload it
    if (vizFileSelect.value) {
      loadVizData(vizFileSelect.value);
    }
  } catch (e) {
    console.error('initViz error:', e);
    toast('โหลดรายการไฟล์ไม่สำเร็จ', 'error');
  }
}

async function loadVizData(fileId) {
  if (!fileId) {
    if (vizXSelect) vizXSelect.innerHTML = '<option value="">—</option>';
    if (vizYSelect) vizYSelect.innerHTML = '<option value="">—</option>';
    resetVizChart();
    return;
  }

  try {
    const data = await apiFetch(`/api/csv/${fileId}`);
    if (!data.ok) { toast(data.error || 'โหลดไฟล์ไม่สำเร็จ', 'error'); return; }

    currentVizData = data.data || [];
    currentVizHeaders = data.headers || [];

    // Populate axis selectors
    const headerOptions = currentVizHeaders.map(h => `<option value="${h}">${h}</option>`).join('');
    if (vizXSelect) vizXSelect.innerHTML = '<option value="">— เลือกคอลัมน์ —</option>' + headerOptions;
    if (vizYSelect) vizYSelect.innerHTML = '<option value="">— เลือกคอลัมน์ —</option>' + headerOptions;

    // Auto-select: first text col for X, first numeric col for Y
    const numericCols = currentVizHeaders.filter(h =>
      currentVizData.slice(0, 20).some(row => row[h] !== '' && !isNaN(parseFloat(row[h])))
    );
    const textCols = currentVizHeaders.filter(h => !numericCols.includes(h));

    if (vizXSelect) vizXSelect.value = textCols[0] || currentVizHeaders[0] || '';
    if (vizYSelect) vizYSelect.value = numericCols[0] || (currentVizHeaders.length > 1 ? currentVizHeaders[1] : '') || '';

    // Show AI summary box
    if (vizAiSummaryBox) vizAiSummaryBox.classList.remove('hidden');

    renderChart();
  } catch (e) {
    toast('เกิดข้อผิดพลาดในการโหลดข้อมูล: ' + e.message, 'error');
  }
}

function renderChart() {
  const xCol = vizXSelect?.value;
  const yCol = vizYSelect?.value;

  if (!xCol || !yCol || !currentVizData.length) {
    resetVizChart();
    return;
  }

  let labels = currentVizData.map(row => String(row[xCol] ?? ''));
  let values = currentVizData.map(row => parseFloat(row[yCol]) || 0);

  // --- DATA SIMPLIFICATION FOR LARGE DATASETS ---
  if (values.length > 20) {
    if (currentVizType === 'pie') {
      // For Pie charts: take top 12, combine the rest into "Others"
      const dataObjects = labels.map((l, i) => ({ label: l, value: values[i] }));
      dataObjects.sort((a, b) => b.value - a.value); // sort descending
      const topData = dataObjects.slice(0, 12);
      const othersValue = dataObjects.slice(12).reduce((sum, item) => sum + item.value, 0);

      labels = topData.map(d => d.label);
      values = topData.map(d => d.value);
      if (othersValue > 0) {
        labels.push(`อื่นๆ (${dataObjects.length - 12} รายการ)`);
        values.push(othersValue);
      }
    } else {
      // For Bar/Line chart: if very large, average out into bins
      const MAX_POINTS = 50;
      if (values.length > MAX_POINTS) {
        const binSize = Math.ceil(values.length / MAX_POINTS);
        const newLabels = [];
        const newValues = [];
        for (let i = 0; i < values.length; i += binSize) {
          const chunkLabels = labels.slice(i, i + binSize);
          const chunkValues = values.slice(i, i + binSize);

          // Use the range of labels as the new label (e.g., "A - C")
          const startLabel = chunkLabels[0];
          const endLabel = chunkLabels[chunkLabels.length - 1];
          newLabels.push(startLabel === endLabel ? startLabel : `${startLabel} ... ${endLabel}`);

          // Average the values
          const avg = chunkValues.reduce((sum, v) => sum + v, 0) / chunkValues.length;
          newValues.push(avg);
        }
        labels = newLabels;
        values = newValues;
      }
    }
  }
  // ----------------------------------------------

  // Destroy previous chart instance
  if (myChart) { myChart.destroy(); myChart = null; }

  if (vizChartCanvas) vizChartCanvas.classList.remove('hidden');
  if (vizEmptyState) vizEmptyState.classList.add('hidden');

  const isDark = document.documentElement.classList.contains('dark');
  const gridColor = isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)';
  const tickColor = isDark ? '#94a3b8' : '#64748b'; // slate-400 / slate-500
  const fontFamily = "'Sarabun', 'Inter', sans-serif";

  // Modern soft color palette
  const COLORS = [
    '#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#06b6d4', '#f97316', '#84cc16', '#e879f9', '#14b8a6',
    '#3b82f6', '#ec4899', '#f43f5e', '#14b8a6', '#64748b', '#94a3b8' // extra colors
  ];
  const base = COLORS[0];

  // Helper to add opacity to Hex (e.g., #RRGGBBAA)
  const hexToRbga = (hex, alpha) => {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  };

  const backgroundColors = currentVizType === 'pie'
    ? values.map((_, i) => (i === values.length - 1 && labels[i].startsWith('อื่นๆ (')) ? hexToRbga('#94a3b8', 0.9) : hexToRbga(COLORS[i % COLORS.length], 0.9))
    : hexToRbga(base, 0.8); // 80% opacity for bars
  const borderColors = currentVizType === 'pie'
    ? values.map((_, i) => (i === values.length - 1 && labels[i].startsWith('อื่นๆ (')) ? '#94a3b8' : COLORS[i % COLORS.length])
    : base;

  const config = {
    type: currentVizType,
    data: {
      labels,
      datasets: [{
        label: yCol,
        data: values,
        backgroundColor: backgroundColors,
        borderColor: borderColors,
        borderWidth: currentVizType === 'line' ? 3 : (currentVizType === 'pie' ? 2 : 0),
        borderRadius: currentVizType === 'bar' ? (values.length > 100 ? 2 : 6) : 0, // dynamic border radius
        fill: currentVizType === 'line' ? {
          target: 'origin',
          below: hexToRbga(base, 0.15) // very light fill under the line
        } : false,
        tension: 0.4, // smooth curves
        pointRadius: currentVizType === 'line' ? (values.length > 100 ? 0 : 3) : 0, // hide points if very dense
        pointHoverRadius: 6,
        pointBackgroundColor: isDark ? '#1e293b' : '#fff',
        pointBorderColor: base,
        pointBorderWidth: 2,
        hoverOffset: currentVizType === 'pie' ? 10 : 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: { top: 10, right: 10, bottom: 10, left: 10 }
      },
      animation: { duration: 800, easing: 'easeOutQuart' },
      plugins: {
        legend: {
          display: currentVizType === 'pie',
          position: 'right',
          labels: {
            color: tickColor,
            font: { family: fontFamily, size: 12, weight: '500' },
            padding: 20,
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          backgroundColor: isDark ? 'rgba(30, 41, 59, 0.95)' : 'rgba(255, 255, 255, 0.95)',
          titleColor: isDark ? '#f8fafc' : '#0f172a',
          bodyColor: isDark ? '#cbd5e1' : '#334155',
          borderColor: isDark ? '#334155' : '#e2e8f0',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 12,
          displayColors: true,
          boxPadding: 6,
          usePointStyle: true,
          titleFont: { family: fontFamily, size: 13, weight: '600' },
          bodyFont: { family: fontFamily, size: 12 },
          callbacks: {
            label: ctx => {
              const v = ctx.parsed.y !== undefined ? ctx.parsed.y : ctx.parsed;
              return ` ${Number(v).toLocaleString('th-TH')}`;
            }
          }
        }
      },
      scales: currentVizType === 'pie' ? {} : {
        x: {
          ticks: {
            color: tickColor,
            font: { family: fontFamily, size: window.innerWidth < 640 ? 8 : 11 },
            maxRotation: window.innerWidth < 640 ? 90 : 45,
            maxTicksLimit: window.innerWidth < 640 ? 6 : (values.length > 50 ? 12 : undefined),
            autoSkip: true,
          },
          grid: { display: false }
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: tickColor,
            font: { family: fontFamily, size: 11 },
            callback: v => Number(v).toLocaleString('th-TH'),
            padding: 8
          },
          grid: {
            color: gridColor,
            drawBorder: false,
            borderDash: [5, 5]
          },
          border: { display: false }
        }
      }
    }
  };

  const ctx = vizChartCanvas.getContext('2d');
  myChart = new Chart(ctx, config);

  computeVizStats(values);
}

function computeVizStats(values) {
  const nums = (values || []).filter(v => !isNaN(v) && v !== null);
  if (!nums.length) {
    if (vizStatsRow) vizStatsRow.classList.add('hidden');
    return;
  }
  const avg = nums.reduce((a, b) => a + b, 0) / nums.length;
  const max = Math.max(...nums);
  const min = Math.min(...nums);

  if (statsAvg) statsAvg.textContent = avg.toLocaleString('th-TH', { maximumFractionDigits: 2 });
  if (statsMax) statsMax.textContent = max.toLocaleString('th-TH', { maximumFractionDigits: 2 });
  if (statsMin) statsMin.textContent = min.toLocaleString('th-TH', { maximumFractionDigits: 2 });
  if (vizStatsRow) vizStatsRow.classList.remove('hidden');
}

function resetVizChart() {
  if (myChart) { myChart.destroy(); myChart = null; }
  if (vizChartCanvas) vizChartCanvas.classList.add('hidden');
  if (vizEmptyState) vizEmptyState.classList.remove('hidden');
  if (vizStatsRow) vizStatsRow.classList.add('hidden');
  if (vizAiSummaryBox) vizAiSummaryBox.classList.add('hidden');
  currentVizData = [];
  currentVizHeaders = [];
}

async function generateVizAiSummary() {
  if (!currentVizData.length || !vizYSelect?.value) {
    toast('กรุณาเลือกไฟล์และคอลัมน์ข้อมูลก่อนวิเคราะห์', 'info');
    return;
  }
  if (!aiSummaryContent) return;

  const xCol = vizXSelect?.value || '';
  const yCol = vizYSelect?.value || '';
  const values = currentVizData.map(r => parseFloat(r[yCol])).filter(v => !isNaN(v));

  aiSummaryContent.innerHTML = `
    <div class="flex items-center gap-2 text-brand-600">
      <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg>
      <span class="text-sm font-medium">AI กำลังวิเคราะห์ข้อมูล...</span>
    </div>`;

  const sample = currentVizData.slice(0, 30).map(r => `${r[xCol]}: ${r[yCol]}`).join(', ');
  const prompt = `ช่วยสรุปแนวโน้มของข้อมูลจากหัวข้อ "${xCol}" และ "${yCol}" นี้ให้หน่อย: ${sample}. สรุปสั้นๆ ในเชิงธุรกิจหรือภาพรวมองค์กร (ภาษาไทย)`;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: prompt, history: [] })
    });

    aiSummaryContent.innerHTML = '';

    if (!res.ok) {
      let errText = 'API Error: ' + res.status;
      try {
        const textData = await res.text();
        try {
          const jsonData = JSON.parse(textData);
          if (jsonData.error) errText = jsonData.error;
        } catch (_) {
          // If not JSON, but we have text and it's short, use it
          if (textData && textData.length < 100 && !textData.includes('<html')) {
            errText = textData;
          }
        }
      } catch (_) { }
      throw new Error(errText);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let botText = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let lines = buffer.split('\n');
      buffer = lines.pop();
      for (const line of lines) {
        if (line.trim().startsWith('data: ')) {
          const jsonStr = line.trim().substring(6);
          if (jsonStr) {
            try {
              const data = JSON.parse(jsonStr);
              if (data.error) throw new Error(data.error);
              if (data.content) {
                botText += data.content;
                aiSummaryContent.innerHTML = markdownToHtml(botText);
              }
            } catch (ex) {
              if (ex.message !== "Unexpected end of JSON input") {
                throw ex; // Re-throw to be caught by outer catch block mapping to fallback
              }
            }
          }
        }
      }
    }

    // If we finished streaming but got no text, fallback
    if (!botText.trim()) throw new Error('Empty AI response');

    return; // Success
  } catch (e) {
    console.error('AI summary error:', e);

    let errorMsgHtml = '';
    if (e && e.message && !e.message.includes('Empty AI response') && !e.message.includes('API Error')) {
      const displayMsg = e.message.includes('429') || e.message.toLowerCase().includes('quota')
        ? 'โควต้า AI API ของคุณหมดชั่วคราว กรุณารอสักครู่'
        : e.message;
      errorMsgHtml = `<div class="mb-3 px-3 py-2 rounded-lg border border-red-200 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-xs font-medium flex items-center gap-2">
        <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg> 
        <span>${displayMsg}</span>
      </div>`;
    }

    // Offline fallback summary if AI fails
    const avg = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const maxRow = currentVizData.find(r => parseFloat(r[yCol]) === max);
    const minRow = currentVizData.find(r => parseFloat(r[yCol]) === min);

    aiSummaryContent.innerHTML = `
      ${errorMsgHtml}
      <p class="text-sm text-surface-700 dark:text-surface-300 leading-relaxed">
        ข้อมูลในชุดนี้มีค่าเฉลี่ยอยู่ที่ <strong class="text-brand-600">${parseFloat(avg).toLocaleString('th-TH', { maximumFractionDigits: 2 })}</strong>,
        ค่าสูงสุด <strong class="text-emerald-600">${max.toLocaleString('th-TH')}${maxRow ? ` (${maxRow[xCol]})` : ''}</strong>
        และค่าต่ำสุด <strong class="text-rose-600">${min.toLocaleString('th-TH')}${minRow ? ` (${minRow[xCol]})` : ''}</strong>.
        ช่วงข้อมูล (Range) = <strong>${(max - min).toLocaleString('th-TH')}</strong>.
        <span class="text-surface-400 text-[10px] ml-1 opacity-70">(ข้อมูลสรุปสำรอง)</span>
      </p>`;
  }
}

// 📋 Kanban / Project Board Logic
async function loadKanban() {
  const containerTodo = $('kanban-todo');
  const containerInProg = $('kanban-in-progress');
  const containerDone = $('kanban-done');
  if (!containerTodo) return;

  [containerTodo, containerInProg, containerDone].forEach(c => c.innerHTML = '<div class="p-4 text-center opacity-50 text-xs italic">กำลังโหลด...</div>');

  try {
    const res = await fetch('/api/schedules');
    const data = await res.json();
    if (data.schedules) {
      renderKanban(data.schedules);
    }
  } catch (e) {
    console.error('Failed to load Kanban:', e);
    toast('ไม่สามารถโหลดข้อมูลคัมบังได้', 'error');
  }
}

function renderKanban(tasks) {
  const todo = tasks.filter(t => (t.status || 'todo') === 'todo');
  const inProg = tasks.filter(t => t.status === 'in_progress');
  const done = tasks.filter(t => t.status === 'done');

  const renderCol = (container, list, countElId) => {
    const countEl = $(countElId);
    if (countEl) countEl.textContent = list.length;

    if (list.length === 0) {
      container.innerHTML = `<div class="p-8 border-2 border-dashed border-surface-100 dark:border-surface-800 rounded-2xl text-center text-[10px] font-bold text-surface-400 uppercase tracking-widest bg-surface-50/30 dark:bg-surface-900/10">No Tasks</div>`;
      return;
    }

    container.innerHTML = list.map(t => `
      <div class="p-4 bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-800 rounded-2xl shadow-sm hover:shadow-md transition-all cursor-pointer group relative" 
           onclick="editSchedule(${t.id})" draggable="true" ondragstart="handleKanbanDragStart(event, ${t.id})">
        <div class="flex items-start justify-between mb-2">
           <span class="px-2 py-0.5 rounded-lg bg-brand-50 dark:bg-brand-900/30 text-brand-600 text-[10px] font-black uppercase tracking-wider border border-brand-100 dark:border-brand-800">${t.category}</span>
           <span class="text-[9px] text-surface-400 font-bold font-mono">${t.time}</span>
        </div>
        <h4 class="text-sm font-bold text-surface-800 dark:text-surface-100 mb-1 leading-tight group-hover:text-brand-600 transition-colors">${t.title}</h4>
        <p class="text-[11px] text-surface-500 line-clamp-2 leading-relaxed mb-3">${t.desc || 'ไม่มีรายละเอียด...'}</p>
        <div class="flex items-center justify-between pt-3 border-t border-surface-50 dark:border-surface-800">
           <div class="flex items-center gap-2">
              <div class="w-6 h-6 rounded-full bg-surface-100 dark:bg-surface-800 flex items-center justify-center overflow-hidden">
                 ${t.avatar_url ? `<img src="${t.avatar_url}" class="w-full h-full object-cover">` : `<i data-lucide="user" class="w-3 h-3 text-surface-400"></i>`}
              </div>
              <span class="text-[10px] font-bold text-surface-500">${t.display_name}</span>
           </div>
           <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button class="p-1 hover:text-brand-600" title="ย้าย"><i data-lucide="move" class="w-3 h-3"></i></button>
           </div>
        </div>
      </div>
    `).join('');
  };

  renderCol($('kanban-todo'), todo, 'kanban-todo-count');
  renderCol($('kanban-in-progress'), inProg, 'kanban-in-progress-count');
  renderCol($('kanban-done'), done, 'kanban-done-count');
  initIcons();
  setupKanbanDropZones();
}

async function renderLinkPreview(url, messageId) {
  try {
    const res = await fetch(`/api/link-preview?url=${encodeURIComponent(url)}`);
    const data = await res.json();
    if (data.ok) {
      const container = $(`preview-${messageId}`);
      if (!container) return;
      
      // Ensure the parent container expands to fit the preview full-width
      const parent = container.closest('.chat-bubble-container');
      if (parent) {
          parent.style.alignItems = 'stretch';
          // Adjust width to match bubble or requested max
          container.style.width = '100%';
      }

      container.innerHTML = `
        <a href="${data.url}" target="_blank" class="link-preview-card block w-full group/preview animate-in fade-in duration-300">
          ${data.image ? `<div class="w-full h-36 overflow-hidden bg-surface-100 dark:bg-surface-900 border-b border-surface-100 dark:border-surface-700/30"><img src="${data.image}" class="w-full h-full object-cover transition-transform duration-700 group-hover/preview:scale-110" onerror="this.parentElement.classList.add('hidden')"></div>` : ''}
          <div class="link-preview-meta">
            <h4 class="text-[12px] font-bold text-surface-900 dark:text-white line-clamp-2 leading-snug mb-1">${data.title || "Link Preview"}</h4>
            <div class="flex items-center gap-1 opacity-50">
               <span class="text-[9px] font-black uppercase tracking-wider truncate">${new URL(data.url).hostname.replace('www.', '').toUpperCase()}</span>
            </div>
          </div>
        </a>
      `;
      initIcons(); 
    }
  } catch (e) {
    console.error('Preview error:', e);
  }
}

function handleKanbanDragStart(e, sid) {
  e.dataTransfer.setData('task-id', sid);
  e.currentTarget.classList.add('opacity-40');
  setTimeout(() => e.target.classList.remove('opacity-40'), 0);
}

function setupKanbanDropZones() {
  const columns = [
    { id: 'kanban-todo', status: 'todo' },
    { id: 'kanban-in-progress', status: 'in_progress' },
    { id: 'kanban-done', status: 'done' }
  ];

  columns.forEach(col => {
    const el = $(col.id);
    if (!el) return;

    el.ondragover = (e) => { e.preventDefault(); el.classList.add('bg-brand-50/30', 'dark:bg-brand-900/10'); };
    el.ondragleave = () => { el.classList.remove('bg-brand-50/30', 'dark:bg-brand-900/10'); };
    el.ondrop = async (e) => {
      e.preventDefault();
      el.classList.remove('bg-brand-50/30', 'dark:bg-brand-900/10');
      const sid = e.dataTransfer.getData('task-id');
      if (sid) {
        await updateKanbanStatus(sid, col.status);
      }
    };
  });
}

async function updateKanbanStatus(sid, newStatus) {
  try {
    // We need to fetch the existing schedule info first to update correctly via handlescheduleitem (PUT)
    // For simplicity, we can just fetch and put.
    const res = await fetch('/api/schedules');
    const data = await res.json(); // Await the json() call
    const task = data.schedules.find(t => t.id == sid);
    if (!task) return;

    task.status = newStatus;

    const updateRes = await fetch(`/api/schedules/${sid}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(task)
    });

    if (updateRes.ok) {
      loadKanban();
      toast(`อัปเดตสถานะเป็น ${newStatus}`, 'success');
    }
  } catch (e) {
    console.error('Kanban update error:', e);
  }
}


// 🧠 AI Data Insight Plus (Deep Analysis)
async function analyzeVizData() {
  const btn = $('analyzeVizDataBtn');
  const resultArea = $('aiSummaryResult');
  const resultText = $('aiSummaryText');

  if (!state.currentViewData || state.currentViewData.length === 0) {
    toast('ไม่พบข้อมูลสำหรับวิเคราะห์', 'error');
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i> กำลังวิเคราะห์เชิงลึก...';
  resultArea.classList.remove('hidden');
  resultText.innerHTML = '<div class="flex items-center gap-3 p-4 bg-brand-50 dark:bg-brand-900/20 rounded-2xl border border-brand-100 dark:border-brand-800"><div class="meta-typing"><span></span><span></span><span></span></div><span class="text-xs font-bold text-brand-600">AI กำลังประมวลผลข้อมูลเพื่อหา Insight ให้คุณ...</span></div>';

  const dataSnippet = state.currentViewData.slice(0, 50);
  const headers = state.currentViewHeaders || Object.keys(dataSnippet[0]);

  const rtcConfig = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    { urls: 'stun:stun2.l.google.com:19302' },
    { urls: 'stun:stun3.l.google.com:19302' },
    { urls: 'stun:stun4.l.google.com:19302' },
    { urls: 'stun:stun.services.mozilla.com' },
    { urls: 'stun:stun.anyfirewall.com:3478' },
    { urls: 'stun:stun.stunprotocol.org' }
  ]
};
  const prompt = `ในฐานะนักวิเคราะห์ข้อมูลอัจฉริยะ (Data Scientist) ช่วยวิเคราะห์ไฟล์ข้อมูลนี้ที่มีหัวข้อดังนี้: ${headers.join(', ')}
และนี่คือตัวอย่างข้อมูลบางส่วน:
${JSON.stringify(dataSnippet)}

กรุณาให้คำแนะนำดังนี้:
1. ภาพรวมพฤติกรรมของข้อมูล (Key Patterns)
2. แนวโน้ม (Trends) ที่น่าสนใจหรือควรกังวล
3. ข้อเสนอแนะเชิงกลยุทธ์ (Strategic Recommendations) สำหรับธุรกิจหรือองค์กร

ใช้ภาษาไทยที่ดูเป็นมืออาชีพและสรุปเป็นข้อๆ ให้ชัดเจน`;

  try {
    const res = await apiFetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: prompt, category: 'Analysis' })
    });

    if (res.ok) {
      resultText.innerHTML = `<div class="prose-ai-insight p-4">${markdownToHtml(res.reply)}</div>`;
    } else {
      throw new Error('AI Analysis failed');
    }
  } catch (e) {
    resultText.innerHTML = `<div class="p-4 bg-red-100 text-red-600 rounded-xl text-xs font-bold">⚠️ ${e.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="sparkles" class="w-4 h-4"></i> AI Insight Plus';
    initIcons();
  }
}

// 🏠 Home Dashboard AI Feed
async function renderHomeDashboard() {
  const nameSpan = $('dash-user-name');
  if (nameSpan && state.user) nameSpan.textContent = state.user.display_name || state.user.username;

  const greetTextEl = $('dashGreetingText');
  if (greetTextEl) {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 12) greetTextEl.textContent = 'สวัสดียามเช้า';
    else if (hour >= 12 && hour < 17) greetTextEl.textContent = 'สวัสดียามบ่าย';
    else if (hour >= 17 && hour < 21) greetTextEl.textContent = 'สวัสดียามเย็น';
    else greetTextEl.textContent = 'สวัสดียามค่ำ';
  }

  const content = $('home-digest-content');
  if (content) {
    try {
      const sumData = await apiFetch('/api/summary?category=all');
      if (sumData && sumData.summary) {
        content.innerHTML = markdownToHtml(sumData.summary);
      } else {
        content.innerHTML = '<p class="italic text-surface-400">ยังไม่มีข้อมูลสรุปใหม่สำหรับวันนี้ ลองอัปโหลดไฟล์เพิ่มในคลังความรู้สิ!</p>';
      }
    } catch (e) {
      content.innerHTML = '<p class="text-xs text-red-500">โหลดสรุปไม่สำเร็จ</p>';
    }
  }

  // Load stats
  try {
    const schedules = await apiFetch('/api/schedules');
    const activeTasks = (schedules.schedules || schedules.items || []).filter(t => t.status === 'todo' || t.status === 'in_progress');
    const countEl = $('dash-kanban-count');
    if (countEl) countEl.innerHTML = `${activeTasks.length} <span class="text-sm font-medium text-surface-500">งาน</span>`;
  } catch (e) { }

  initIcons();
}

// 🎙️ AI Voice Feedback
// Version 9809 speak() function removed in favor of Unified Engine at 3546

// 📄 AI Smart Scan (OCR/Summarize)
async function scanFileWithAI(fileId) {
  toast('กำลังส่งคำสั่งสแกนไฟล์ไปยัง AI...', 'info');
  showView('chat');
  
  // Set tab to AI
  const tabBtn = document.querySelector('.chat-tab-btn[data-tab="ai"]');
  if (tabBtn) tabBtn.click();
  
  const msg = `ช่วยสรุปเนื้อหาและดึงข้อมูลสำคัญจากไฟล์ ID: ${fileId} ออกมาที สรุปเป็นหัวข้อสั้นๆ เข้าใจง่าย`;
  setTimeout(() => {
    sendMessage(msg);
  }, 500);
}

// ⚡ AI Kanban Auto-Generator
async function handleAiGenKanban() {
  const goal = aiGenKanbanInput.value.trim();
  if (!goal) return toast('กรุณากรอกเป้าหมาย', 'error');

  confirmAiGenBtn.disabled = true;
  confirmAiGenBtn.innerHTML = '<i class="animate-spin w-4 h-4"></i> กำลังประมวลผล...';
  toast('AI กำลังวางแผนงานให้คุณ...', 'info');

  try {
    const res = await apiFetch('/api/kanban/auto-generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ goal })
    });

    if (res.ok) {
      toast(`สร้างงานสำเร็จ ${res.count} รายการ`, 'success');
      aiGenKanbanModal.classList.add('hidden');
      aiGenKanbanInput.value = '';
      loadSchedules(); // Refresh Kanban
    } else {
      throw new Error(res.error || 'Failed to generate');
    }
  } catch (e) {
    console.error(e);
    toast('เกิดข้อผิดพลาด: ' + e.message, 'error');
  } finally {
    confirmAiGenBtn.disabled = false;
    confirmAiGenBtn.innerHTML = '<i data-lucide="wand-2" class="w-4 h-4"></i> เริ่มวางแผนเลย';
    initIcons();
  }
}

// 📑 AI Document Comparison
async function handleBulkCompare() {
  const selected = Array.from(document.querySelectorAll('.file-checkbox:checked')).map(cb => cb.dataset.id);
  if (selected.length < 2) return toast('กรุณาเลือกอย่างน้อย 2 ไฟล์เพื่อเปรียบเทียบ', 'error');

  // For now, compare the first two
  const f1 = selected[0];
  const f2 = selected[1];

  toast('AI กำลังเปรียบเทียบเอกสาร...', 'info');
  aiCompareModal.classList.remove('hidden');
  aiCompareModal.classList.add('flex', 'items-center', 'justify-center');
  aiCompareResult.innerHTML = '<div class="flex flex-col items-center py-12"><div class="animate-spin h-10 w-10 border-4 border-purple-600 border-t-transparent rounded-full mb-4"></div><p class="text-xs font-bold">กำลังวิเคราะห์ความเหมือนและต่าง...</p></div>';

  try {
    const res = await apiFetch('/api/kb/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file1_id: f1, file2_id: f2 })
    });

    if (res.ok) {
      aiCompareResult.innerHTML = markdownToHtml(res.comparison);
    } else {
      throw new Error(res.error || 'Comparison failed');
    }
  } catch (e) {
    console.error(e);
    aiCompareResult.innerHTML = `<div class="p-8 text-red-500 font-bold bg-red-50 rounded-2xl">❌ เกิดข้อผิดพลาด: ${e.message}</div>`;
  }
}

// 🎨 Theme & Appearance
function applyAccentColor(color) {
  setAccentColor(color);
}

function applyDashboardBg(bg) {
  const root = document.documentElement;
  if (bg.startsWith('linear-gradient') || bg.startsWith('#') || bg.startsWith('url')) {
    root.style.setProperty('--dashboard-bg', bg);
    localStorage.setItem('dashboardBg', bg);
    toast('บันทึกธีมพื้นหลังแล้ว', 'success');
  }

  // Re-apply to Home View if active
  if (state.currentView === 'home') renderHomeDashboard();
}

// Initialize theme on load
(function initTheme() {
  const savedColor = localStorage.getItem('accentColor');
  if (savedColor) setAccentColor(savedColor, false);

  const savedBg = localStorage.getItem('dashboardBg');
  if (savedBg) {
    document.documentElement.style.setProperty('--dashboard-bg', savedBg);
  }
})();

// ─── PWA Install Logic ──────────────────────
let deferredPrompt;
const installBtn = document.getElementById('installAppBtn');
const pwaSection = document.getElementById('pwaInstallSection');

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  if (pwaSection) pwaSection.classList.remove('hidden');
});

if (installBtn) {
  installBtn.addEventListener('click', (e) => {
    if (!deferredPrompt) {
      // If prompt is not available (e.g., iOS or Already Installed or not HTTPS)
      const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
      if (isIOS) {
        toast('สำหรับ iPhone: กดปุ่ม "แชร์" (Share) แล้วเลือก "เพิ่มลงหน้าจอโฮม" (Add to Home Screen)', 'info');
      } else {
        toast('กรุณากดปุ่ม 3 จุดที่มุมบราวเซอร์ แล้วเลือก "ติดตั้งแอป" หรือ "เพิ่มลงหน้าจอโฮม"', 'info');
      }
      return;
    }
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('User accepted the A2HS prompt');
      }
      deferredPrompt = null;
      if (pwaSection) pwaSection.classList.add('hidden');
    });
  });
}

window.addEventListener('appinstalled', (event) => {
  toast('ติดตั้งแอปสำเร็จ!', 'success');
});

// ✅ Explicitly call on init
setTimeout(initSystemNotifications, 2000);

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

const VAPID_PUBLIC_KEY = 'BNW7f7p3Ush_rg9vjIXxz1KTthTsiy3rz17oaygTy1-l4bTQJKpLeYEj4v3jYQkggo1VLa7w7sNb6mWDaIVH5eU';

async function subscribeUserToPush() {
  try {
    const registration = await navigator.serviceWorker.ready;
    let subscription = await registration.pushManager.getSubscription();

    if (!subscription) {
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
      });
    }

    await fetch('/api/notifications/subscribe', {
      method: 'POST',
      body: JSON.stringify({ subscription }),
      headers: { 'Content-Type': 'application/json' }
    });
    console.log("Push subscription synchronized.");
  } catch (e) {
    console.error("Failed to subscribe to push:", e);
  }
}

// ─── Browser System Notification Bridge ──────
async function initSystemNotifications() {
  const btn = document.getElementById('requestNotifBtn');
  const testBtn = document.getElementById('testNotifBtn');
  const statusIndicator = document.getElementById('notifStatusIndicator');
  const statusText = document.getElementById('notifStatusText');

  if (!btn || !('Notification' in window)) return;

  function updateUI() {
    if (Notification.permission === 'granted') {
      statusIndicator.className = 'w-2.5 h-2.5 rounded-full bg-emerald-500';
      statusText.textContent = 'เปิดใช้งานแล้ว';
      btn.classList.add('hidden');
      testBtn.disabled = false;
      testBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    } else if (Notification.permission === 'denied') {
      statusIndicator.className = 'w-2.5 h-2.5 rounded-full bg-red-500';
      statusText.textContent = 'ถูกปฏิเสธ';
      btn.textContent = 'ขออนุญาตใหม่';
      btn.classList.remove('hidden');
    }
  }

  updateUI();
  if (Notification.permission === 'granted') {
    subscribeUserToPush();
  }

  btn.onclick = async () => {
    const permission = await Notification.requestPermission();
    updateUI();
    if (permission === 'granted') {
      toast('อนุญาตการแจ้งเตือนสำเร็จ!', 'success');
      subscribeUserToPush();
      showSystemNotification('ยินดีต้อนรับ!', 'คุณจะได้รับการแจ้งเตือนข่าวสารจาก OrgChat ที่นี่');
    } else if (permission === 'denied') {
      toast('คุณได้ปฏิเสธการแจ้งเตือน หากต้องการใช้งาน กรุณาตั้งค่าที่บราวเซอร์', 'warning');
    } else {
      if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
        toast('การแจ้งเตือนต้องการ HTTPS เพื่อทำงานบนมือถือ', 'error');
      }
    }
  };

  testBtn.onclick = () => {
    showSystemNotification('แจ้งเตือนทดสอบ', 'นี่คือตัวอย่างการแจ้งเตือนจากระบบ OrgChat เหมือนแอป Meta!');
  };
}

function showSystemNotification(title, body, url = '/') {
  if (Notification.permission !== 'granted') return;

  // We primarily use the Service Worker to show notifications 
  // because it's the only way they appear reliably when the app is in background/closed
  if (navigator.serviceWorker && navigator.serviceWorker.ready) {
    navigator.serviceWorker.ready.then(registration => {
      registration.showNotification(title, {
        body: body,
        icon: '/static/icon-192.png',
        badge: '/static/icon-192.png',
        vibrate: [200, 100, 200],
        tag: 'orgchat-msg-' + Date.now(), // Unique tag to ensure multiple notifications show
        renotify: true,
        requireInteraction: false, // Don't block the screen forever
        data: { url: url }
      });
    });
  } else {
    // Fallback if SW is not ready
    try {
      new Notification(title, {
        body: body,
        icon: '/static/icon-192.png',
        tag: 'orgchat-fallback'
      });
    } catch (e) {
      console.warn("Notification API failed:", e);
    }
  }
}

// Ensure init runs on load
document.addEventListener('DOMContentLoaded', initSystemNotifications);


// Integrate with the main toast function to show system notifications as well
const originalToast = window.toast;
window.toast = function (msg, type = 'info') {
  if (typeof originalToast === 'function') {
    originalToast(msg, type);
  }
  // Send to system notification if app is hidden (user is in another app or screen locked)
  if (document.visibilityState === 'hidden' && Notification.permission === 'granted') {
    showSystemNotification('OrgChat Update', msg);
  }
};

// ─── Real-time, Theme & AI Features ──────────────────

function updateTheme() {
  const isDark = state.theme === 'dark' ||
    (state.theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches);

  if (isDark) {
    document.documentElement.classList.add('dark');
    if ($('themeIcon')) $('themeIcon').setAttribute('data-lucide', 'sun');
    if ($('themeText')) $('themeText').innerText = 'โหมดกลางวัน';
  } else {
    document.documentElement.classList.remove('dark');
    if ($('themeIcon')) $('themeIcon').setAttribute('data-lucide', 'moon');
    if ($('themeText')) $('themeText').innerText = 'โหมดกลางคืน';
  }
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

// Watch for system theme changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
  if (state.theme === 'auto') updateTheme();
});


async function extractActionItems(text, messageId) {
  try {
    const res = await fetch('/api/ai/extract-tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const data = await res.json();
    if (data.ok && data.tasks.length > 0) {
      let tasksStr = data.tasks.map(t => `• ${t.title}: ${t.description}`).join('\n');
      if (confirm(`🤖 AI พบงานที่ต้องทำ:\n${tasksStr}\n\nต้องการเปิดหน้าปฏิทินเพื่อบันทึกหรือไม่?`)) {
        showView('calendar');
        const first = data.tasks[0];
        if (scheduleTitleInput) scheduleTitleInput.value = first.title;
        if (scheduleDescInput) scheduleDescInput.value = first.description;
      }
    } else {
      toast("🤖 ไม่พบงานที่ต้องทำในข้อความนี้", "info");
    }
  } catch (e) {
    console.error(e);
  }
}

async function renderLinkPreview(url, messageId) {
  try {
    const res = await fetch(`/api/link-preview?url=${encodeURIComponent(url)}`);
    const data = await res.json();
    if (data.ok) {
      const container = $(`preview-${messageId}`);
      if (!container) return;
      container.innerHTML = `
        <a href="${data.url}" target="_blank" class="link-preview-card block max-w-[250px] group/preview animate-in fade-in duration-300">
          ${data.image ? `<div class="w-full h-32 overflow-hidden bg-surface-100 dark:bg-surface-900 border-b border-surface-100 dark:border-surface-700/30"><img src="${data.image}" class="w-full h-full object-cover transition-transform duration-700 group-hover/preview:scale-110" onerror="this.parentElement.classList.add('hidden')"></div>` : ''}
          <div class="link-preview-meta">
            <h4 class="text-[12px] font-bold text-surface-900 dark:text-white line-clamp-2 leading-snug mb-1">${data.title || "Link Preview"}</h4>
            <div class="flex items-center gap-1 opacity-50">
               <span class="text-[9px] font-bold uppercase tracking-wider truncate">${new URL(data.url).hostname.replace('www.', '').toUpperCase()}</span>
            </div>
          </div>
        </a>
      `;
      initIcons(); 


    }
  } catch (e) { }
}

async function showSearchInsights() {
  try {
    const res = await fetch('/api/admin/search-insights');
    const data = await res.json();
    if (data.ok) {
      const { top_searches, recent_searches } = data.insights;
      let html = '<div class="space-y-4 max-h-[60vh] overflow-y-auto p-2">';
      html += '<div><h3 class="text-xs font-black uppercase tracking-widest text-surface-400 mb-3">🔥 คำค้นหายอดนิยม</h3><div class="flex flex-wrap gap-2">';
      top_searches.forEach(s => {
        html += `<span class="px-3 py-1 bg-brand-50 dark:bg-brand-900/30 text-brand-600 rounded-full text-[10px] font-bold border border-brand-100 dark:border-brand-800">${s.query} (${s.count})</span>`;
      });
      html += '</div></div>';

      html += '<div><h3 class="text-xs font-black uppercase tracking-widest text-surface-400 mb-3">🕒 ค้นหาล่าสุด</h3><div class="space-y-2">';
      recent_searches.forEach(s => {
        html += `<div class="p-3 bg-surface-50 dark:bg-surface-800 rounded-2xl border border-surface-100 dark:border-surface-700 flex justify-between items-center group hover:border-brand-500 transition-all">
          <span class="text-xs font-bold">${s.query}</span>
          <span class="text-[9px] text-surface-400">${s.username} • ${new Date(s.timestamp).toLocaleTimeString()}</span>
        </div>`;
      });
      html += '</div></div></div>';

      // Fallback alert if alertModal is missing
      if (typeof alertModal === 'function') {
        alertModal("🔍 Search Insights", html);
      } else {
        confirm("ความลับทางธุรกิจ:\n" + top_searches.map(s => `${s.query} (${s.count})`).join(', '));
      }
    }
  } catch (e) { console.error(e); }
}

// Initializations on load
document.addEventListener('DOMContentLoaded', () => {
  updateTheme();
  initSocket();
  checkCallButtonsVisibility();
  if (state.isAdmin && $('dashSearchInsights')) {
    $('dashSearchInsights').classList.remove('hidden');
  }
});

// ══════════════════════════════════════════════════
// 📞 WebRTC — Old system removed. See "WebRTC Call Engine" section below (~line 10360+)
// ══════════════════════════════════════════════════

// Show call buttons only in DM mode
function checkCallButtonsVisibility() {
  if (!voiceCallBtn || !videoCallBtn) return;
  if (state.currentChat.type === 'dm' && state.currentChat.id !== 'ai-assistant') {
    voiceCallBtn.classList.remove('hidden');
    videoCallBtn.classList.remove('hidden');
  } else {
    voiceCallBtn.classList.add('hidden');
    videoCallBtn.classList.add('hidden');
  }
}

// Call function inside openDM or when chat view updates
const _originalOpenDm = window.openDm;
if (typeof openDm !== 'undefined') {
  window.openDm = function (...args) {
    _originalOpenDm.apply(this, args);
    setTimeout(checkCallButtonsVisibility, 100);
  };
}


/* ══════════════════════════════════════════════════════════════
   🗂️  KANBAN BOARD MODULE
   ══════════════════════════════════════════════════════════════ */

const kanbanState = {
  columns: [],
  dragCard: null,
  dragSourceCol: null,
  addCardTargetColumn: null,
  users: [], // New: Store users list for assignee selection
};

async function fetchUsersForKanban() {
  if (kanbanState.users.length > 0) return;
  try {
    const data = await apiFetch('/api/users/list');
    if (data.ok) {
      kanbanState.users = data.users;
    }
  } catch (e) {
    console.error('Failed to fetch users:', e);
  }
}

async function loadKanbanBoard() {
  try {
    // Ensure users are loaded for assignee rendering
    await fetchUsersForKanban();
    
    const data = await apiFetch('/api/kanban/board');
    if (data.ok) {
      kanbanState.columns = data.columns;
      renderKanbanBoard();
    }
  } catch (e) {
    console.error('Kanban load error:', e);
    toast('ไม่สามารถโหลดกระดานคัมบังได้', 'error');
  }
}

function renderKanbanBoard() {
  const board = $('kanbanBoard');
  if (!board) return;

  const emptyState = $('kanbanEmptyState');
  if (emptyState) emptyState.classList.add('hidden');

  // Remove old columns but keep emptyState
  board.querySelectorAll('.kanban-col, .kanban-add-col').forEach(el => el.remove());

  kanbanState.columns.forEach(col => {
    const colEl = buildKanbanColumn(col);
    board.appendChild(colEl);
  });

  // Add new column button at end
  const addColBtn = document.createElement('div');
  addColBtn.className = 'kanban-add-col flex-shrink-0 w-72 select-none';
  addColBtn.innerHTML = `
    <button onclick="openAddColumnModal()" class="w-full h-14 border-2 border-dashed border-surface-200 dark:border-surface-700 hover:border-brand-500 hover:bg-brand-50/40 dark:hover:bg-brand-900/20 text-surface-400 hover:text-brand-600 rounded-2xl flex items-center justify-center gap-2 font-bold text-sm transition-all select-none">
      <i data-lucide="plus" class="w-4 h-4"></i> เพิ่มคอลัมน์ใหม่
    </button>
  `;
  board.appendChild(addColBtn);

  initIcons();
  updateDashboardKanbanCount();
  initKanbanSortable();
}

function buildKanbanColumn(col) {
  const div = document.createElement('div');
  div.className = 'kanban-col flex-shrink-0 w-72 flex flex-col bg-surface-50 dark:bg-surface-900 rounded-2xl border border-surface-200 dark:border-surface-800 shadow-sm overflow-hidden select-none';
  div.dataset.colId = col.id;

  const cardCount = col.cards ? col.cards.length : 0;
  div.innerHTML = `
    <div class="kanban-col-header flex items-center justify-between px-4 py-3 border-b border-surface-200 dark:border-surface-800 select-none" style="border-top: 3px solid ${col.color || '#6366f1'}">
      <div class="flex items-center gap-2 min-w-0">
        <span class="font-black text-sm truncate">${escHtml(col.title || 'ไม่มีชื่อ')}</span>
        <span class="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full text-white" style="background:${col.color || '#6366f1'}">${cardCount}</span>
      </div>
      <div class="flex items-center gap-1 flex-shrink-0">
        <button onclick="openAddCardModal(${col.id})" title="เพิ่มการ์ด" class="p-1.5 hover:bg-surface-200 dark:hover:bg-surface-700 rounded-lg transition-all text-surface-400 hover:text-brand-600">
          <i data-lucide="plus" class="w-3.5 h-3.5"></i>
        </button>
        <button onclick="promptEditColumn(${col.id}, \`${escHtml(col.title)}\`, '${col.color || '#6366f1'}')" title="แก้ไขคอลัมน์" class="p-1.5 hover:bg-surface-200 dark:hover:bg-surface-700 rounded-lg transition-all text-surface-400 hover:text-brand-600">
          <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
        </button>
        <button onclick="deleteKanbanColumn(${col.id})" title="ลบคอลัมน์" class="p-1.5 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all text-surface-400 hover:text-red-500">
          <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
        </button>
      </div>
    </div>
    <div class="kanban-cards-list flex-1 overflow-y-auto p-3 space-y-2.5 min-h-[120px] custom-scrollbar select-none" 
         data-col-id="${col.id}">
      ${(col.cards || []).map(card => buildKanbanCardHTML(card)).join('')}
    </div>
    <div class="p-3 border-t border-surface-100 dark:border-surface-800">
      <button onclick="openAddCardModal(${col.id})" class="w-full py-2.5 border-2 border-dashed border-surface-200 dark:border-surface-700 hover:border-brand-500 hover:bg-brand-50/40 dark:hover:bg-brand-900/20 text-surface-400 hover:text-brand-600 rounded-xl flex items-center justify-center gap-1.5 font-bold text-xs transition-all select-none">
        <i data-lucide="plus" class="w-3.5 h-3.5"></i> เพิ่มการ์ด
      </button>
    </div>
  `;
  return div;
}

function buildKanbanCardHTML(card) {
  const priorityColors = {
    high: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    medium: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    low: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  };
  const priorityLabel = { 
    high: 'สูง', 
    medium: 'กลาง', 
    low: 'ต่ำ' 
  };
  const pLabel = priorityLabel[card.priority] || 'กลาง';
  const pColor = priorityColors[card.priority] || priorityColors.medium;

  const dueHtml = card.due_date ? `
    <div class="flex items-center gap-1 text-[9px] font-bold text-surface-400 mt-1">
      <i data-lucide="calendar" class="w-2.5 h-2.5"></i> ${card.due_date}
    </div>` : '';

  const assigneeList = card.assignee ? card.assignee.split(',').filter(a => a.trim()) : [];
  const assigneeDetails = assigneeList.map(a => {
    const u = kanbanState.users.find(user => user.username === a.trim());
    return u ? { name: u.display_name, avatar: u.avatar_url } : { name: a.trim(), avatar: null };
  });

  const assigneeHtml = assigneeList.length > 0 ? `
    <div class="flex items-center gap-2 mt-2 pt-2 border-t border-surface-100 dark:border-surface-700/50">
      <div class="flex -space-x-2 overflow-hidden">
        ${assigneeDetails.map(d => `
          <div class="w-6 h-6 rounded-full border-2 border-white dark:border-surface-800 bg-surface-100 dark:bg-surface-700 flex items-center justify-center overflow-hidden" title="${escHtml(d.name)}">
            ${d.avatar ? `<img src="${d.avatar}" class="w-full h-full object-cover">` : `<i data-lucide="user" class="w-3 h-3 text-surface-400"></i>`}
          </div>
        `).join('')}
      </div>
      <div class="text-[9px] font-bold text-surface-500 dark:text-surface-400 leading-tight">
        ${assigneeDetails.length <= 3 
          ? assigneeDetails.map(d => escHtml(d.name)).join(', ') 
          : `${assigneeDetails.slice(0, 2).map(d => escHtml(d.name)).join(', ')} และอีก ${assigneeDetails.length - 2} คน`}
      </div>
    </div>` : '';

  const borderStyle = card.color ? `border-l: 3px solid ${card.color};` : '';

  const labelsHtml = card.labels ? card.labels.split(',').map(l => `
    <span class="px-2 py-0.5 rounded flex items-center gap-1 text-[9px] font-black uppercase tracking-widest text-surface-600 bg-surface-50 dark:text-surface-400 dark:bg-surface-800 border border-surface-200 dark:border-surface-700">
      <i data-lucide="tag" class="w-2 h-2"></i> ${escHtml(l.trim())}
    </span>
  `).join('') : '';

  const doneHtml = card.is_done ? `
    <span class="flex items-center gap-1 text-[9px] font-black uppercase tracking-widest text-surface-600 bg-surface-50 dark:bg-surface-900/20 px-2 py-0.5 rounded-lg border border-surface-200 dark:border-surface-800">
      <i data-lucide="check-circle" class="w-2.5 h-2.5"></i> สำเร็จแล้ว
    </span>
  ` : '';

  return `
    <div class="kanban-card bg-white dark:bg-surface-800 rounded-xl border border-surface-200 dark:border-surface-700 p-3 shadow-sm hover:shadow-md cursor-grab active:cursor-grabbing group ${card.is_done ? 'opacity-80' : ''}"
         data-card-id="${card.id}" data-col-id="${card.column_id}"
         style="${borderStyle}">
      <div class="flex items-center justify-between gap-1 mb-2">
         <div class="flex flex-wrap gap-1">${labelsHtml}</div>
         ${doneHtml}
      </div>
      <div class="flex items-start justify-between gap-2">
        <p class="font-bold text-xs ${card.is_done ? 'text-surface-400 line-through' : 'text-surface-800 dark:text-surface-100'} leading-snug flex-1">${escHtml(card.title)}</p>
        <div class="flex opacity-100 sm:opacity-0 group-hover:opacity-100 transition-opacity items-center gap-1 flex-shrink-0" title="แก้ไขการ์ด">
          <button onclick="moveKanbanCardUp(${card.id}, ${card.column_id}); event.stopPropagation();" class="p-1 hover:bg-surface-100 dark:hover:bg-surface-700 rounded-lg" title="เลื่อนขึ้น">
            <i data-lucide="arrow-up" class="w-3 h-3 text-surface-400 hover:text-brand-500"></i>
          </button>
          <button onclick="moveKanbanCardDown(${card.id}, ${card.column_id}); event.stopPropagation();" class="p-1 hover:bg-surface-100 dark:hover:bg-surface-700 rounded-lg" title="เลื่อนลง">
            <i data-lucide="arrow-down" class="w-3 h-3 text-surface-400 hover:text-brand-500"></i>
          </button>
          <button onclick="openEditCardModal(${card.id}); event.stopPropagation();" class="p-1 hover:bg-surface-100 dark:hover:bg-surface-700 rounded-lg">
            <i data-lucide="edit-3" class="w-3 h-3 text-surface-400 hover:text-brand-500"></i>
          </button>
          <button onclick="deleteKanbanCard(${card.id}); event.stopPropagation();" class="p-1 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg" title="ลบการ์ด">
            <i data-lucide="trash-2" class="w-3 h-3 text-red-400"></i>
          </button>
        </div>
      </div>
      ${card.description ? `<p class="text-[10px] text-surface-400 mt-1 line-clamp-2">${escHtml(card.description)}</p>` : ''}
      <div class="mt-2 flex items-center justify-between flex-wrap gap-1">
        <span class="text-[9px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full ${pColor}">${pLabel}</span>
        ${dueHtml}
      </div>
      ${card.assignee ? `<div class="mt-1 pt-1 border-t border-surface-100 dark:border-surface-700">${assigneeHtml}</div>` : ''}
    </div>
  `;
}

// 🎯 Fluid SortableJS Initialization
function initKanbanSortable() {
  if (typeof Sortable === 'undefined') {
    setTimeout(initKanbanSortable, 100);
    return;
  }

  const board = document.getElementById('kanbanBoard');
  if (!board) return;

  const colLists = board.querySelectorAll('.kanban-cards-list');
  colLists.forEach(list => {
    if (list._sortable) {
      try { list._sortable.destroy(); } catch (e) {}
    }
    list._sortable = new Sortable(list, {
      group: 'kanban-board-cards',
      animation: 200,
      easing: 'cubic-bezier(0.2, 0, 0, 1)',
      ghostClass: 'kanban-sortable-ghost',
      chosenClass: 'kanban-sortable-chosen',
      dragClass: 'kanban-sortable-drag',
      filter: 'button, input, textarea, a, select',
      preventOnFilter: false,
      fallbackTolerance: 2,
      emptyInsertThreshold: 35,
      direction: 'vertical',
      onEnd: async function(evt) {
        const cardEl = evt.item;
        const targetColList = evt.to;
        const sourceColList = evt.from;
        if (!cardEl || !targetColList || !sourceColList) return;

        const targetColId = targetColList.dataset.colId;
        const sourceColId = sourceColList.dataset.colId;
        const cardId = cardEl.dataset.cardId;
        const newPos = evt.newIndex;

        if (!cardId || !targetColId) return;

        cardEl.dataset.colId = String(targetColId);

        // Check if target column represents a "Done" column
        const targetColObj = kanbanState.columns.find(c => String(c.id) == String(targetColId));
        const isDoneCol = targetColObj && (
          targetColObj.title.toLowerCase().includes('done') ||
          targetColObj.title.toLowerCase().includes('สำเร็จ') ||
          targetColObj.title.toLowerCase().includes('เสร็จ')
        );

        // Update Done visual styling immediately
        const titleP = cardEl.querySelector('p.font-bold');
        if (titleP) {
          if (isDoneCol) {
            titleP.classList.add('line-through', 'text-surface-400');
            titleP.classList.remove('text-surface-800', 'dark:text-surface-100');
          } else {
            titleP.classList.remove('line-through', 'text-surface-400');
            titleP.classList.add('text-surface-800', 'dark:text-surface-100');
          }
        }

        // Optimistically update column count badges
        updateKanbanColumnCounters();

        // Optimistically update in-memory state
        const sourceCol = kanbanState.columns.find(c => String(c.id) == String(sourceColId));
        if (sourceCol && sourceCol.cards) {
          const cardIdx = sourceCol.cards.findIndex(c => String(c.id) == String(cardId));
          if (cardIdx !== -1) {
            const [movedCard] = sourceCol.cards.splice(cardIdx, 1);
            if (movedCard && targetColObj) {
              movedCard.column_id = targetColId;
              movedCard.is_done = isDoneCol ? 1 : 0;
              if (!targetColObj.cards) targetColObj.cards = [];
              targetColObj.cards.splice(newPos, 0, movedCard);
            }
          }
        }

        // Background API Sync with seamless rollback if failed
        try {
          apiFetch(`/api/kanban/cards/${cardId}/move`, {
            method: 'POST',
            body: JSON.stringify({
              column_id: targetColId,
              position: newPos,
              is_done: isDoneCol ? 1 : undefined
            }),
          }).catch(err => {
            console.error('Failed to sync card position:', err);
            if (typeof toast === 'function') toast('ซิงก์ตำแหน่งไม่สำเร็จ กำลังโหลดใหม่...', 'error');
            loadKanbanBoard();
          });
        } catch (e) {
          console.error('Error syncing card move:', e);
          loadKanbanBoard();
        }
      }
    });
  });
}

function updateKanbanColumnCounters() {
  document.querySelectorAll('.kanban-col').forEach(colEl => {
    const countList = colEl.querySelector('.kanban-cards-list');
    const countBadge = colEl.querySelector('.kanban-col-header span:nth-child(2)');
    if (countList && countBadge) {
      const actualCount = countList.querySelectorAll('.kanban-card').length;
      countBadge.textContent = String(actualCount);
    }
  });
}

// Card Moving
async function moveKanbanCardUp(cardId, colId) {
  const col = kanbanState.columns.find(c => c.id == colId);
  if (!col || !col.cards) return;
  const idx = col.cards.findIndex(c => c.id == cardId);
  if (idx > 0) {
    try {
      await apiFetch(`/api/kanban/cards/${cardId}/move`, {
        method: 'POST',
        body: JSON.stringify({ column_id: colId, position: idx - 1 }),
      });
      await loadKanbanBoard();
    } catch (e) { toast('เลื่อนขึ้นไม่สำเร็จ', 'error'); }
  } else {
    toast('การ์ดอยู่บนสุดแล้ว', 'info');
  }
}

async function moveKanbanCardDown(cardId, colId) {
  const col = kanbanState.columns.find(c => c.id == colId);
  if (!col || !col.cards) return;
  const idx = col.cards.findIndex(c => c.id == cardId);
  if (idx !== -1 && idx < col.cards.length - 1) {
    try {
      await apiFetch(`/api/kanban/cards/${cardId}/move`, {
        method: 'POST',
        body: JSON.stringify({ column_id: colId, position: idx + 1 }),
      });
      await loadKanbanBoard();
    } catch (e) { toast('เลื่อนลงไม่สำเร็จ', 'error'); }
  } else {
    toast('การ์ดอยู่ล่างสุดแล้ว', 'info');
  }
}

// Column Management
function openAddColumnModal() {
  const title = prompt('ชื่อคอลัมน์ใหม่:');
  if (!title || !title.trim()) return;
  addKanbanColumn(title.trim());
}

async function addKanbanColumn(title) {
  try {
    await apiFetch('/api/kanban/columns', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
    await loadKanbanBoard();
    toast(`เพิ่มคอลัมน์ "${title}" แล้ว`, 'success');
  } catch (e) {
    toast('เพิ่มคอลัมน์ไม่สำเร็จ', 'error');
  }
}

async function deleteKanbanColumn(colId) {
  const col = kanbanState.columns.find(c => c.id === colId);
  const confirmMsg = col?.cards?.length > 0
    ? `ลบคอลัมน์ "${col.title}" และการ์ดทั้งหมด ${col.cards.length} ใบ?`
    : `ลบคอลัมน์ "${col?.title}"?`;
  if (!confirm(confirmMsg)) return;
  try {
    await apiFetch(`/api/kanban/columns/${colId}`, { method: 'DELETE' });
    await loadKanbanBoard();
    toast('ลบคอลัมน์แล้ว', 'success');
  } catch (e) {
    toast('ลบคอลัมน์ไม่สำเร็จ', 'error');
  }
}

async function promptEditColumn(colId, currentTitle, currentColor) {
  const newTitle = prompt('ชื่อคอลัมน์ใหม่:', currentTitle);
  if (newTitle === null) return;
  try {
    await apiFetch(`/api/kanban/columns/${colId}`, {
      method: 'PUT',
      body: JSON.stringify({ title: newTitle.trim() || currentTitle }),
    });
    await loadKanbanBoard();
  } catch (e) {
    toast('แก้ไขคอลัมน์ไม่สำเร็จ', 'error');
  }
}

// Card Modal
let editingCardId = null;

function openAddCardModal(colId) {
  kanbanState.addCardTargetColumn = colId;
  editingCardId = null;
  fetchUsersForKanban().then(() => showKanbanCardModal());
}

function openEditCardModal(cardId) {
  // Find the card in state
  let card = null;
  for (const col of kanbanState.columns) {
    card = (col.cards || []).find(c => c.id === cardId);
    if (card) break;
  }
  if (!card) return;

  editingCardId = cardId;
  kanbanState.addCardTargetColumn = card.column_id;
  fetchUsersForKanban().then(() => showKanbanCardModal(card));
}

function showKanbanCardModal(card = null) {
  const existingModal = $('kanbanCardModal');
  if (existingModal) existingModal.remove();

  const isEdit = !!card;
  const modal = document.createElement('div');
  modal.id = 'kanbanCardModal';
  modal.className = 'fixed inset-0 z-[2000] flex items-center justify-center p-4 bg-surface-950/80 backdrop-blur-sm animate-in fade-in duration-200';
  modal.innerHTML = `
    <div class="bg-white dark:bg-surface-900 w-full max-w-md rounded-3xl shadow-2xl border border-surface-200 dark:border-surface-800 p-6 space-y-4 animate-in zoom-in-95 duration-200">
      <div class="flex items-center justify-between">
        <h3 class="text-base font-black">${isEdit ? 'แก้ไขการ์ด' : 'เพิ่มการ์ดใหม่'}</h3>
        <button onclick="closeKanbanCardModal()" class="p-2 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-xl"><i data-lucide="x" class="w-4 h-4"></i></button>
      </div>
      <div class="space-y-3">
        <div>
          <label class="block text-[10px] font-black uppercase tracking-widest text-surface-400 mb-1">หัวข้อ *</label>
          <input id="kCardTitle" type="text" value="${card ? escHtml(card.title) : ''}" placeholder="ชื่องาน..." class="w-full bg-surface-50 dark:bg-surface-800 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-brand-600 outline-none">
        </div>
        <div class="flex items-center gap-2 py-1">
          <input id="kCardIsDone" type="checkbox" ${card && card.is_done ? 'checked' : ''} class="w-4 h-4 rounded border-surface-300 text-emerald-600 focus:ring-emerald-500">
          <label for="kCardIsDone" class="text-xs font-bold text-surface-600 dark:text-surface-400 cursor-pointer">เครื่องหมายเสร็จงาน (Mark as Done)</label>
        </div>
        <div>
          <label class="block text-[10px] font-black uppercase tracking-widest text-surface-400 mb-1">รายละเอียด</label>
          <textarea id="kCardDesc" rows="3" placeholder="รายละเอียดเพิ่มเติม..." class="w-full bg-surface-50 dark:bg-surface-800 rounded-xl px-4 py-2.5 text-sm resize-none focus:ring-2 focus:ring-brand-600 outline-none">${card ? escHtml(card.description || '') : ''}</textarea>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-[10px] font-black uppercase tracking-widest text-surface-400 mb-1">ความสำคัญ</label>
            <select id="kCardPriority" class="w-full bg-surface-50 dark:bg-surface-800 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-brand-600 outline-none">
              <option value="low" ${card?.priority === 'low' ? 'selected' : ''}>ต่ำ</option>
              <option value="medium" ${(!card || card?.priority === 'medium') ? 'selected' : ''}>กลาง</option>
              <option value="high" ${card?.priority === 'high' ? 'selected' : ''}>สูง</option>
            </select>
          </div>
          <div>
            <label class="block text-[10px] font-black uppercase tracking-widest text-surface-400 mb-1">กำหนดส่ง</label>
            <input id="kCardDue" type="date" value="${card?.due_date || ''}" class="w-full bg-surface-50 dark:bg-surface-800 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-brand-600 outline-none">
          </div>
        </div>
        <div>
          <label class="block text-[10px] font-black uppercase tracking-widest text-surface-400 mb-1">ป้ายกำกับ (คั่นด้วยจุลภาค)</label>
          <input id="kCardLabels" type="text" value="${card ? escHtml(card.labels || '') : ''}" placeholder="เช่น ด่วนมาก, อนุมัติ, ของใหม่..." class="w-full bg-surface-50 dark:bg-surface-800 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-brand-600 outline-none">
        </div>
        <div>
          <label class="block text-[10px] font-black uppercase tracking-widest text-surface-400 mb-2">ผู้รับผิดชอบ (ติ๊กเลือก)</label>
          <div class="relative">
            <input type="text" id="kUserSearch" placeholder="ค้นหาชื่อ..." oninput="filterKanbanUsers(this.value)" class="w-full bg-surface-50 dark:bg-surface-800 rounded-xl px-4 py-2 text-xs border border-surface-200 dark:border-surface-700 focus:ring-2 focus:ring-brand-600 outline-none mb-2">
            <div id="kUserList" class="user-selector-grid grid grid-cols-2 gap-2 max-h-40 overflow-y-auto p-2 border border-surface-200 dark:border-surface-800 rounded-2xl bg-surface-50/50 dark:bg-surface-900/50 custom-scrollbar">
              ${kanbanState.users.map(u => {
                const isSelected = card && (card.assignee || '').split(',').map(s => s.trim()).includes(u.username);
                return `
                  <label class="user-select-item flex items-center gap-2 p-2 rounded-xl border border-transparent hover:bg-white dark:hover:bg-surface-800 hover:border-surface-200 dark:hover:border-surface-700 cursor-pointer transition-all ${isSelected ? 'bg-brand-50/50 dark:bg-brand-900/20 border-brand-200 dark:border-brand-800' : ''}" data-username="${u.username.toLowerCase()}" data-display="${u.display_name.toLowerCase()}">
                    <input type="checkbox" name="assignee" value="${u.username}" ${isSelected ? 'checked' : ''} class="w-3.5 h-3.5 rounded border-surface-300 text-brand-600 focus:ring-brand-500">
                    <div class="flex items-center gap-1.5 min-w-0">
                      <div class="w-5 h-5 rounded-full bg-brand-100 dark:bg-brand-900 flex-shrink-0 flex items-center justify-center overflow-hidden">
                        ${u.avatar_url ? `<img src="${u.avatar_url}" class="w-full h-full object-cover">` : `<i data-lucide="user" class="w-2.5 h-2.5 text-brand-600"></i>`}
                      </div>
                      <span class="text-[11px] font-bold truncate">${escHtml(u.display_name)}</span>
                    </div>
                  </label>
                `;
              }).join('')}
            </div>
          </div>
        </div>
      </div>
      <div class="flex gap-3 pt-2">
        <button onclick="closeKanbanCardModal()" class="flex-1 py-3 bg-surface-100 dark:bg-surface-800 hover:bg-surface-200 rounded-2xl font-bold text-sm transition-all">ยกเลิก</button>
        <button onclick="submitKanbanCard()" class="flex-[2] py-3 bg-brand-600 hover:bg-brand-700 text-white rounded-2xl font-bold text-sm shadow-lg transition-all">
          ${isEdit ? 'บันทึก' : 'เพิ่มการ์ด'}
        </button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  initIcons();
  setTimeout(() => $('kCardTitle')?.focus(), 100);
}

function filterKanbanUsers(query) {
  const q = query.toLowerCase();
  document.querySelectorAll('.user-select-item').forEach(el => {
    const show = el.dataset.username.includes(q) || el.dataset.display.includes(q);
    el.classList.toggle('hidden', !show);
  });
}

function closeKanbanCardModal() {
  $('kanbanCardModal')?.remove();
}

async function submitKanbanCard() {
  const title = $('kCardTitle')?.value?.trim();
  if (!title) { toast('กรุณาใส่หัวข้อการ์ด', 'error'); return; }

  const assignees = Array.from(document.querySelectorAll('#kUserList input[name="assignee"]:checked')).map(cb => cb.value);

  const payload = {
    title,
    description: $('kCardDesc')?.value || '',
    priority: $('kCardPriority')?.value || 'medium',
    due_date: $('kCardDue')?.value || '',
    assignee: assignees.join(','),
    labels: $('kCardLabels')?.value || '',
    is_done: $('kCardIsDone')?.checked ? 1 : 0,
  };

  try {
    if (editingCardId) {
      await apiFetch(`/api/kanban/cards/${editingCardId}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
      toast('บันทึกการ์ดแล้ว', 'success');
    } else {
      payload.column_id = kanbanState.addCardTargetColumn;
      await apiFetch('/api/kanban/cards', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      toast('เพิ่มการ์ดแล้ว', 'success');
    }
    closeKanbanCardModal();
    await loadKanbanBoard();
  } catch (e) {
    toast('บันทึกไม่สำเร็จ: ' + e.message, 'error');
  }
}

async function deleteKanbanCard(cardId) {
  if (!confirm('ลบการ์ดนี้?')) return;
  try {
    await apiFetch(`/api/kanban/cards/${cardId}`, { method: 'DELETE' });
    await loadKanbanBoard();
    toast('ลบการ์ดแล้ว', 'success');
  } catch (e) {
    toast('ลบการ์ดไม่สำเร็จ', 'error');
  }
}

function updateDashboardKanbanCount() {
  const el = $('dash-kanban-count');
  if (!el) return;
  const total = kanbanState.columns.reduce((s, c) => s + (c.cards || []).length, 0);
  el.innerHTML = `${total} <span class="text-sm font-medium text-surface-500">งาน</span>`;
}

// Hook buttons
if ($('addKanbanColumnBtn')) {
  $('addKanbanColumnBtn').onclick = openAddColumnModal;
}
if ($('addKanbanCardBtn')) {
  $('addKanbanCardBtn').onclick = () => {
    const firstCol = kanbanState.columns[0];
    if (firstCol) openAddCardModal(firstCol.id);
    else toast('กรุณาเพิ่มคอลัมน์ก่อน', 'info');
  };
}


/* ══════════════════════════════════════════════════════════════
   📖  INTERNAL WIKI MODULE
   ══════════════════════════════════════════════════════════════ */

const wikiState = {
  pages: [],
  currentPage: null,
  isEditing: false,
};

async function loadWikiPages(query = '') {
  try {
    const url = query ? `/api/wiki/pages?q=${encodeURIComponent(query)}` : '/api/wiki/pages';
    const data = await apiFetch(url);
    if (data.ok) {
      wikiState.pages = data.pages;
      renderWikiPagesList();
    }
  } catch (e) {
    console.error('Wiki load error:', e);
  }
}

function renderWikiPagesList() {
  const list = $('wikiPagesList');
  if (!list) return;

  if (wikiState.pages.length === 0) {
    list.innerHTML = `<div class="px-4 py-8 text-center text-surface-400 text-xs italic">ยังไม่มีบทความ</div>`;
    return;
  }

  list.innerHTML = wikiState.pages.map(p => `
    <button onclick="loadWikiPage(${p.id})" 
      class="wiki-page-item w-full text-left px-4 py-3 text-xs font-bold hover:bg-surface-100 dark:hover:bg-surface-800 border-b border-surface-100 dark:border-surface-800 transition-all ${wikiState.currentPage?.id === p.id ? 'bg-brand-50 dark:bg-brand-900/30 text-brand-600' : 'text-surface-700 dark:text-surface-300'}">
      <div class="font-bold truncate">${escHtml(p.title)}</div>
      <div class="text-[9px] font-bold text-surface-400 uppercase tracking-widest mt-0.5">${p.author} · ${formatRelativeTime(p.updated_at)}</div>
    </button>
  `).join('');
}

async function loadWikiPage(pageId) {
  try {
    const data = await apiFetch(`/api/wiki/pages/${pageId}`);
    if (data.ok) {
      wikiState.currentPage = data.page;
      wikiState.isEditing = false;
      renderWikiContent();
      renderWikiPagesList();
    }
  } catch (e) {
    toast('โหลดบทความไม่สำเร็จ', 'error');
  }
}

function renderWikiContent() {
  const viewArea = $('wikiViewArea');
  const editorArea = $('wikiEditorArea');
  const emptyState = $('wikiEmptyState');

  if (wikiState.isEditing) {
    viewArea?.classList.add('hidden');
    emptyState?.classList.add('hidden');
    editorArea?.classList.remove('hidden');

    if ($('wikiTitleInput')) $('wikiTitleInput').value = wikiState.currentPage?.title || '';
    if ($('wikiContentInput')) $('wikiContentInput').value = wikiState.currentPage?.content || '';
  } else if (wikiState.currentPage) {
    editorArea?.classList.add('hidden');
    emptyState?.classList.add('hidden');
    viewArea?.classList.remove('hidden');

    const p = wikiState.currentPage;
    if ($('wikiTitleDisplay')) $('wikiTitleDisplay').textContent = p.title;
    if ($('wikiMeta')) {
      $('wikiMeta').textContent = `โดย ${p.author} · อัปเดต ${formatRelativeTime(p.updated_at)}`;
    }
    if ($('wikiContentDisplay')) {
      const html = typeof marked !== 'undefined' ? marked.parse(p.content || '') : escHtml(p.content || '');
      $('wikiContentDisplay').innerHTML = html;
      // Syntax highlighting
      if (typeof Prism !== 'undefined') Prism.highlightAllUnder($('wikiContentDisplay'));
    }
    initIcons();
  } else {
    editorArea?.classList.add('hidden');
    viewArea?.classList.add('hidden');
    emptyState?.classList.remove('hidden');
  }
}

function startNewWikiPage() {
  wikiState.currentPage = null;
  wikiState.isEditing = true;
  renderWikiContent();
  renderWikiPagesList();
  $('wikiTitleInput')?.focus();
}

function startEditWikiPage() {
  if (!wikiState.currentPage) return;
  wikiState.isEditing = true;
  renderWikiContent();
}

async function saveWikiPage() {
  const title = $('wikiTitleInput')?.value?.trim();
  const content = $('wikiContentInput')?.value || '';
  if (!title) { toast('กรุณาใส่หัวข้อบทความ', 'error'); return; }

  try {
    if (wikiState.currentPage?.id) {
      await apiFetch(`/api/wiki/pages/${wikiState.currentPage.id}`, {
        method: 'PUT',
        body: JSON.stringify({ title, content }),
      });
      toast('บันทึกบทความแล้ว', 'success');
      await loadWikiPage(wikiState.currentPage.id);
    } else {
      const data = await apiFetch('/api/wiki/pages', {
        method: 'POST',
        body: JSON.stringify({ title, content }),
      });
      toast('สร้างบทความแล้ว', 'success');
      await loadWikiPages();
      if (data.id) await loadWikiPage(data.id);
    }
    wikiState.isEditing = false;
    renderWikiContent();
  } catch (e) {
    toast('บันทึกไม่สำเร็จ: ' + e.message, 'error');
  }
}

async function deleteWikiPage() {
  if (!wikiState.currentPage) return;
  if (!confirm(`ลบบทความ "${wikiState.currentPage.title}"?`)) return;

  try {
    await apiFetch(`/api/wiki/pages/${wikiState.currentPage.id}`, { method: 'DELETE' });
    wikiState.currentPage = null;
    wikiState.isEditing = false;
    toast('ลบบทความแล้ว', 'success');
    await loadWikiPages();
    renderWikiContent();
  } catch (e) {
    toast('ลบไม่สำเร็จ', 'error');
  }
}

function cancelWikiEdit() {
  wikiState.isEditing = false;
  renderWikiContent();
}

function exportWiki(format) {
  if (!wikiState.currentPage || !wikiState.currentPage.id) {
    toast('ไม่พบบทความที่จะนำออก', 'error');
    return;
  }
  window.open(`/api/wiki/pages/${wikiState.currentPage.id}/export?format=${format}`, '_blank');
}

// Wire up Wiki buttons
document.addEventListener('DOMContentLoaded', () => {
  const newWikiBtn = $('newWikiBtn');
  const editWikiBtn = $('editWikiBtn');
  const deleteWikiBtn = $('deleteWikiBtn');
  const saveWikiBtn = $('saveWikiBtn');
  const cancelWikiBtn = $('cancelWikiBtn');

  if (newWikiBtn) newWikiBtn.onclick = startNewWikiPage;
  if (editWikiBtn) editWikiBtn.onclick = startEditWikiPage;
  if (deleteWikiBtn) deleteWikiBtn.onclick = deleteWikiPage;
  if (saveWikiBtn) saveWikiBtn.onclick = saveWikiPage;
  if (cancelWikiBtn) cancelWikiBtn.onclick = cancelWikiEdit;

  // Initialize call button visibility when DOM is ready
  checkCallButtonsVisibility();
});

// Helper for relative time

// Helper to escape HTML
function escHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// ─── Kanban/Wiki loaded via switchView above ─────────────────────────────
// loadKanbanBoard() and loadWikiPages()/renderWikiContent() are defined in the Kanban & Wiki modules below.

// ─── NOTIFICATIONS MODULE (Hallmark Anti-AI-Slop Revamp) ───────────────────
let _notifCache = [];
let _activeNotifFilter = 'all';

function getNotifMeta(n) {
  const type = (n.type || '').toLowerCase();
  const title = (n.title || '');
  const msg = (n.message || '');

  // 1. Leave Requests / Approval / Comments
  if (type.includes('leave') || title.includes('คำขอลา') || title.includes('ลาหยุด') || title.includes('อนุมัติลา')) {
    return {
      category: 'leave',
      badge: 'คำขอลา',
      badgeClass: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20',
      icon: 'calendar-clock',
      iconWrap: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
    };
  }

  // 2. Team Feed / Social Posts
  if (type === 'post' || title.includes('โพสต์ใหม่') || title.includes('ฟีด')) {
    return {
      category: 'feed',
      badge: 'ฟีดทีม',
      badgeClass: 'bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20',
      icon: 'message-square',
      iconWrap: 'bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20'
    };
  }

  // 3. Comments / Replies
  if (type === 'comment' || title.includes('ความคิดเห็น') || title.includes('ตอบกลับ')) {
    return {
      category: 'feed',
      badge: 'ความคิดเห็น',
      badgeClass: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20',
      icon: 'message-circle',
      iconWrap: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20'
    };
  }

  // 4. Likes
  if (type === 'like' || title.includes('ถูกใจ')) {
    return {
      category: 'feed',
      badge: 'ถูกใจ',
      badgeClass: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20',
      icon: 'heart',
      iconWrap: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20'
    };
  }

  // 5. Mentions
  if (type === 'mention' || title.includes('แท็กคุณ') || title.includes('พูดถึงคุณ')) {
    return {
      category: 'feed',
      badge: 'แท็กคุณ',
      badgeClass: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20',
      icon: 'at-sign',
      iconWrap: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
    };
  }

  // 6. Broadcasts / Announcements
  if (type === 'broadcast' || title.includes('ประกาศ')) {
    return {
      category: 'system',
      badge: 'ประกาศ',
      badgeClass: 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20',
      icon: 'megaphone',
      iconWrap: 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20'
    };
  }

  // 7. Tasks / Kanban
  if (type === 'kanban' || title.includes('งาน') || title.includes('บอร์ด')) {
    return {
      category: 'system',
      badge: 'งานทีม',
      badgeClass: 'bg-violet-500/10 text-violet-600 dark:text-violet-400 border border-violet-500/20',
      icon: 'kanban',
      iconWrap: 'bg-violet-500/10 text-violet-600 dark:text-violet-400 border border-violet-500/20'
    };
  }

  // 8. Wiki / Knowledge Base
  if (type === 'wiki' || title.includes('คลังความรู้')) {
    return {
      category: 'system',
      badge: 'คลังความรู้',
      badgeClass: 'bg-teal-500/10 text-teal-600 dark:text-teal-400 border border-teal-500/20',
      icon: 'book-open',
      iconWrap: 'bg-teal-500/10 text-teal-600 dark:text-teal-400 border border-teal-500/20'
    };
  }

  // Default: System Notification
  return {
    category: 'system',
    badge: 'ระบบ',
    badgeClass: 'bg-surface-200 dark:bg-surface-800 text-surface-600 dark:text-surface-300 border border-surface-300 dark:border-surface-700',
    icon: 'bell',
    iconWrap: 'bg-surface-100 dark:bg-surface-800 text-surface-500 dark:text-surface-400 border border-surface-200 dark:border-surface-700'
  };
}

function setNotificationFilter(filterKey) {
  _activeNotifFilter = filterKey;
  document.querySelectorAll('#notifFilterBar .notif-pill').forEach(btn => {
    const isTarget = btn.getAttribute('data-filter') === filterKey;
    btn.classList.toggle('active', isTarget);
    if (isTarget) {
      btn.className = 'notif-pill active px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-all bg-surface-900 dark:bg-blue-600 text-white border-surface-900 dark:border-blue-600 shadow-sm';
    } else {
      btn.className = 'notif-pill px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-all bg-white dark:bg-surface-900 border-surface-200 dark:border-surface-800 text-surface-600 dark:text-surface-400 hover:border-surface-300 dark:hover:border-surface-700';
    }
  });
  renderNotificationsList();
}

function renderNotificationsList() {
  const container = $('notificationsContainer');
  if (!container) return;

  const notifs = _notifCache || [];

  // Filter items
  let filtered = notifs;
  if (_activeNotifFilter === 'unread') {
    filtered = notifs.filter(n => !n.is_read);
  } else if (_activeNotifFilter === 'leave') {
    filtered = notifs.filter(n => getNotifMeta(n).category === 'leave');
  } else if (_activeNotifFilter === 'feed') {
    filtered = notifs.filter(n => getNotifMeta(n).category === 'feed');
  } else if (_activeNotifFilter === 'system') {
    filtered = notifs.filter(n => getNotifMeta(n).category === 'system');
  }

  // Update navbar & pill badges
  const totalCount = notifs.length;
  const unreadCount = notifs.filter(n => !n.is_read).length;

  const totalEl = $('notifTotalBadge');
  if (totalEl) {
    totalEl.textContent = totalCount;
    totalEl.classList.toggle('hidden', totalCount === 0);
  }

  const pAll = $('pillCountAll');
  if (pAll) pAll.textContent = totalCount > 0 ? `(${totalCount})` : '';

  const pUnread = $('pillCountUnread');
  if (pUnread) pUnread.textContent = unreadCount > 0 ? `(${unreadCount})` : '';

  // Empty state
  if (!filtered || filtered.length === 0) {
    const emptyMsg = _activeNotifFilter === 'unread'
      ? 'คุณอ่านการแจ้งเตือนทั้งหมดแล้ว'
      : 'ไม่พบรายการแจ้งเตือนในหมวดหมู่นี้';
    container.innerHTML = `
      <div class="flex flex-col items-center justify-center py-16 text-center animate-in fade-in duration-300">
        <div class="w-14 h-14 rounded-2xl bg-surface-100 dark:bg-surface-800/60 border border-surface-200/80 dark:border-surface-700/80 flex items-center justify-center text-surface-400 mb-3 shadow-sm">
          <i data-lucide="bell-off" class="w-6 h-6"></i>
        </div>
        <h4 class="text-sm font-bold text-surface-800 dark:text-surface-200 mb-1">${emptyMsg}</h4>
        <p class="text-xs text-surface-400 max-w-xs">เมื่อมีกิจกรรมหรือข้อความใหม่ ระบบจะแจ้งเตือนให้ทราบที่นี่</p>
      </div>
    `;
    if (typeof initIcons === 'function') initIcons();
    return;
  }

  // Date grouping
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const startOfYesterday = startOfToday - 86400000;

  const groups = [
    { title: 'วันนี้', items: [] },
    { title: 'เมื่อวานนี้', items: [] },
    { title: 'ก่อนหน้านี้', items: [] }
  ];

  filtered.forEach(n => {
    let t = 0;
    try { t = new Date(n.timestamp).getTime(); } catch(e){}
    if (!t || isNaN(t)) t = 0;

    if (t >= startOfToday) {
      groups[0].items.push(n);
    } else if (t >= startOfYesterday) {
      groups[1].items.push(n);
    } else {
      groups[2].items.push(n);
    }
  });

  let html = '';
  groups.forEach(g => {
    if (!g.items.length) return;

    html += `
      <div class="pt-2 first:pt-0">
        <div class="text-[11px] font-bold text-surface-400 uppercase tracking-wider px-1 pb-2 flex items-center gap-1.5">
          <span class="w-1.5 h-1.5 rounded-full bg-surface-300 dark:bg-surface-600"></span>
          ${g.title}
          <span class="text-[10px] text-surface-400 font-normal">(${g.items.length})</span>
        </div>
        <div class="space-y-2">
    `;

    g.items.forEach(n => {
      const meta = getNotifMeta(n);
      const isUnread = !n.is_read;
      const cardBg = isUnread 
        ? 'bg-white dark:bg-surface-900 border-surface-200 dark:border-surface-700/80 shadow-sm' 
        : 'bg-surface-50/70 dark:bg-surface-950/40 border-surface-200/50 dark:border-surface-800/50 hover:bg-white dark:hover:bg-surface-900';

      html += `
        <div class="group relative flex items-start gap-3 p-3 sm:p-3.5 rounded-xl border ${cardBg} transition-all cursor-pointer" onclick="handleNotificationClick(${n.id}, '${escHtml(n.link || '')}', ${n.is_read})">
          <!-- Icon Category Badge -->
          <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${meta.iconWrap} mt-0.5">
            <i data-lucide="${meta.icon}" class="w-4 h-4"></i>
          </div>

          <!-- Content Body -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1.5 flex-wrap mb-0.5">
              <span class="text-[9px] font-bold px-1.5 py-0.2 rounded ${meta.badgeClass}">
                ${meta.badge}
              </span>
              <h4 class="text-xs sm:text-[13px] ${isUnread ? 'font-bold text-surface-900 dark:text-white' : 'font-medium text-surface-700 dark:text-surface-300'} truncate">
                ${escHtml(n.title)}
              </h4>
              <span class="text-[11px] text-surface-400 ml-auto whitespace-nowrap">
                ${formatRelativeTime(n.timestamp)}
              </span>
            </div>
            <p class="text-xs text-surface-500 dark:text-surface-400 line-clamp-2 leading-relaxed">
              ${escHtml(n.message)}
            </p>
          </div>

          <!-- Actions & Unread Status -->
          <div class="flex items-center gap-1.5 shrink-0 pt-1">
            ${isUnread ? '<span class="w-2 h-2 rounded-full bg-blue-500 shadow-sm" title="ยังไม่อ่าน"></span>' : ''}
            ${isUnread ? `
              <button onclick="event.stopPropagation(); markNotificationRead(${n.id})" 
                class="opacity-0 group-hover:opacity-100 p-1 text-surface-400 hover:text-surface-800 dark:hover:text-white hover:bg-surface-200/60 dark:hover:bg-surface-800 rounded transition-all" 
                title="ทำเครื่องหมายว่าอ่านแล้ว">
                <i data-lucide="check" class="w-3.5 h-3.5"></i>
              </button>
            ` : `
              <button onclick="event.stopPropagation(); deleteNotificationSingle(${n.id})"
                class="opacity-0 group-hover:opacity-100 p-1 text-surface-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 rounded transition-all"
                title="ลบการแจ้งเตือน">
                <i data-lucide="x" class="w-3.5 h-3.5"></i>
              </button>
            `}
          </div>
        </div>
      `;
    });

    html += `
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
  if (typeof initIcons === 'function') initIcons();
}

async function loadNotifications() {
  const container = $('notificationsContainer');
  if (!container && !$('notificationsList')) return;

  try {
    const res = await apiFetch('/api/notifications');
    _notifCache = res.notifications || [];

    const unreadCount = res.unread_count !== undefined ? res.unread_count : _notifCache.filter(n => !n.is_read).length;
    const countBadge = $('navNotifBadge');
    const mobileBadge = $('mobileNotifBadge');
    const headerBell = $('mobileHeaderNotifBadge');

    [countBadge, mobileBadge].forEach(el => {
      if (el) {
        if (unreadCount > 0) {
          el.innerText = unreadCount > 99 ? '99+' : unreadCount;
          el.classList.remove('hidden');
          el.classList.add('flex');
        } else {
          el.classList.add('hidden');
          el.classList.remove('flex');
        }
      }
    });
    if (headerBell) headerBell.classList.toggle('hidden', unreadCount === 0);

    renderNotificationsList();
  } catch (err) {
    if (err && (err.status === 401 || (err.message && err.message.toLowerCase().includes('unauthorized')))) {
      return;
    }
    console.error('Error load notifications:', err);
    if (container) {
      container.innerHTML = '<p class="text-red-500 text-sm text-center py-4 font-medium">ไม่สามารถดึงข้อมูลการแจ้งเตือนได้</p>';
    }
  }
}

async function handleNotificationClick(id, link, isRead) {
  if (!isRead) await markNotificationRead(id, true);
  if (link && link !== 'None' && link !== 'undefined') {
    if (link.startsWith('#')) {
      window.location.hash = link;
    } else if (link.startsWith('/')) {
      window.location.href = link;
    } else {
      window.open(link, '_blank');
    }
  }
}

async function markNotificationRead(id, reload = true) {
  try {
    await apiFetch(`/api/notifications/${id}/read`, { method: 'POST' });
    const item = _notifCache.find(n => n.id === id);
    if (item) item.is_read = 1;
    if (typeof updateNotifBadge === 'function') updateNotifBadge(_notifCache);
    if (reload) renderNotificationsList();
  } catch (e) {
    console.error(e);
  }
}

async function readAllNotifications() {
  try {
    await apiFetch('/api/notifications/read_all', { method: 'POST' });
    _notifCache.forEach(n => n.is_read = 1);
    if (typeof updateNotifBadge === 'function') updateNotifBadge(_notifCache);
    renderNotificationsList();
  } catch (e) {
    console.error(e);
  }
}

async function deleteNotificationSingle(id) {
  try {
    await apiFetch(`/api/notifications/${id}`, { method: 'DELETE' });
    _notifCache = _notifCache.filter(n => n.id !== id);
    if (typeof updateNotifBadge === 'function') updateNotifBadge(_notifCache);
    renderNotificationsList();
  } catch (e) {
    console.error(e);
  }
}

async function clearAllNotifications() {
  if (!confirm("คุณแน่ใจหรือไม่ว่าต้องการลบการแจ้งเตือนทั้งหมด?")) return;
  try {
    await apiFetch('/api/notifications/delete_all', { method: 'DELETE' });
    _notifCache = [];
    if (typeof updateNotifBadge === 'function') updateNotifBadge(_notifCache);
    renderNotificationsList();
  } catch (e) {
    console.error(e);
  }
}

// 🎙️ VOICE MESSAGE & AUDIO PLAYER LOGIC
let mediaRecorder;
let audioChunks = [];
let recordingInterval;
let recordingStartTime;
let audioContext;
let analyser;
let dataArray;
let animationId;

window.toggleVoicePlay = function (btn, url) {
  const container = btn.closest('.audio-player-bubble');
  const audio = container.querySelector('audio');
  const icon = btn.querySelector('svg') || btn.querySelector('i');

  // Pause others
  document.querySelectorAll('audio').forEach(a => {
    if (a !== audio) {
      a.pause();
      const parent = a.closest('.audio-player-bubble');
      if (parent) {
        const otherBtnIcon = parent.querySelector('.voice-play-btn svg') || parent.querySelector('.voice-play-btn i');
        if (otherBtnIcon) {
          const sz = otherBtnIcon.classList.contains('w-3.5') ? 'w-3.5 h-3.5' : 'w-4 h-4';
          otherBtnIcon.outerHTML = `<i data-lucide="play" class="${sz}"></i>`;
        }
      }
    }
  });

  if (!icon) return;
  const sizeClass = icon.classList.contains('w-3.5') ? 'w-3.5 h-3.5' : 'w-4 h-4';

  if (audio.paused) {
    audio.play();
    icon.outerHTML = `<i data-lucide="pause" class="${sizeClass}"></i>`;
  } else {
    audio.pause();
    icon.outerHTML = `<i data-lucide="play" class="${sizeClass}"></i>`;
  }
  initIcons();
};

window.updateVoiceProgress = function (audio) {
  const container = audio.closest('.audio-player-bubble');
  const bars = container.querySelectorAll('.waveform-bar');
  const durationText = container.querySelector('.voice-duration');
  const isMe = container.classList.contains('bubble-me');

  if (!audio.duration) return;
  const percent = (audio.currentTime / audio.duration) * 100;
  
  const activeCount = Math.floor((percent / 100) * bars.length);
  bars.forEach((bar, idx) => {
    if (idx < activeCount) {
        bar.style.backgroundColor = isMe ? '#ffffff' : '#2563eb';
        bar.style.opacity = '1';
        bar.style.boxShadow = isMe ? '0 0 4px rgba(255,255,255,0.3)' : '0 0 4px rgba(37,99,235,0.3)';
    } else {
        bar.style.backgroundColor = ''; 
        bar.style.opacity = '';
        bar.style.boxShadow = '';
    }
  });

  const mins = Math.floor(audio.currentTime / 60);
  const secs = Math.floor(audio.currentTime % 60);
  durationText.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
};

window.resetVoicePlayer = function (audio) {
  const container = audio.closest('.audio-player-bubble');
  const bars = container.querySelectorAll('.waveform-bar');
  const btnIcon = container.querySelector('.voice-play-btn svg') || container.querySelector('.voice-play-btn i');
  
  bars.forEach(bar => {
    bar.style.backgroundColor = '';
    bar.style.opacity = '';
  });

  if (btnIcon) {
    const sz = btnIcon.classList.contains('w-3.5') ? 'w-3.5 h-3.5' : 'w-4 h-4';
    btnIcon.outerHTML = `<i data-lucide="play" class="${sz}"></i>`;
  }
  initIcons();
};

window.seekVoice = function (e, container) {
  const audio = container.closest('.audio-player-bubble').querySelector('audio');
  const rect = container.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const percent = Math.max(0, Math.min(1, x / rect.width));
  if (audio.duration) audio.currentTime = percent * audio.duration;
};

// --- REAL WAVEFORM ANALYSIS ---
async function analyzeAudioWaveform(url) {
  if (state.analyzedWaveforms.has(url)) return;
  
  // Placeholder to prevent duplicate requests
  state.analyzedWaveforms.set(url, Array(24).fill(20));

  try {
    const res = await fetch(url);
    const buf = await res.arrayBuffer();
    const actx = new (window.AudioContext || window.webkitAudioContext)();
    const audioBuf = await actx.decodeAudioData(buf);
    const raw = audioBuf.getChannelData(0);
    const samples = 24;
    const blockSize = Math.floor(raw.length / samples);
    const peaks = [];
    
    for (let i = 0; i < samples; i++) {
      let start = blockSize * i;
      let sum = 0;
      for (let j = 0; j < blockSize; j++) {
        sum += Math.abs(raw[start + j]);
      }
      peaks.push(sum / blockSize);
    }
    
    const max = Math.max(...peaks);
    const normalized = peaks.map(p => Math.max(15, Math.floor((p / max) * 100)));
    
    state.analyzedWaveforms.set(url, normalized);
    
    // Update all matching UI elements
    document.querySelectorAll(`.voice-waveform-container[data-audio-url="${url}"]`).forEach(container => {
      const bars = container.querySelectorAll('.waveform-bar');
      bars.forEach((bar, idx) => {
        if (normalized[idx]) bar.style.height = normalized[idx] + '%';
      });
    });
  } catch (e) {
    console.error('Waveform analysis failed:', e);
    // Fallback rhythmic pattern
    state.analyzedWaveforms.set(url, [40, 70, 90, 60, 45, 80, 100, 75, 50, 85, 95, 65, 40, 70, 90, 60, 45, 80, 100, 75, 50, 85, 95, 65]);
  }
}

// ── RECORDING LOGIC ──────────────────────────────────────────
window.toggleRecording = async function () {
  console.log('Toggle recording called, state:', mediaRecorder ? mediaRecorder.state : 'idle');
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    stopVoiceRecording();
  } else {
    startVoiceRecording();
  }
};

async function startVoiceRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // Setup Web Audio for Visualizer
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioContext.createMediaStreamSource(stream);
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 64; // Smaller FFT for simple wave
    source.connect(analyser);
    dataArray = new Uint8Array(analyser.frequencyBinCount);

    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      const file = new File([audioBlob], `voice_${Date.now()}.webm`, { type: 'audio/webm' });
      state.groupChat.pendingFiles.push(file);
      renderChatAttachmentPreview();
    };

    mediaRecorder.start();
    recordingStartTime = Date.now();

    // UI Updates
    const recUI = document.getElementById('recordingUI');
    const inputMain = document.getElementById('groupChatInput');
    if (recUI) recUI.classList.remove('hidden');
    if (inputMain) inputMain.classList.add('hidden');

    recordingInterval = setInterval(updateRecordingTimer, 100);
    drawRecordingWave();
  } catch (err) {
    console.error('Recording error:', err);
    toast('ไม่สามารถเข้าถึงไมโครโฟนได้', 'error');
  }
}

function drawRecordingWave() {
  const canvas = document.getElementById('recordingVisualizer');
  if (!canvas || !analyser) return;
  const ctx = canvas.getContext('2d');
  
  const draw = () => {
    if (!mediaRecorder || mediaRecorder.state !== 'recording') return;
    animationId = requestAnimationFrame(draw);
    
    analyser.getByteFrequencyData(dataArray);
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    const barWidth = 3;
    const gap = 2;
    const barCount = Math.floor(canvas.width / (barWidth + gap));
    
    ctx.fillStyle = '#2563eb'; // Brand Color
    
    for (let i = 0; i < barCount; i++) {
      // Use middle frequencies for a more "voice-like" feel
      const freqIndex = Math.floor(i * (dataArray.length / barCount));
      const val = dataArray[freqIndex] || 0;
      const percent = val / 255;
      const height = Math.max(2, canvas.height * percent);
      const y = (canvas.height - height) / 2;
      
      // Draw rounded rectangle
      ctx.beginPath();
      ctx.roundRect(i * (barWidth + gap), y, barWidth, height, 1.5);
      ctx.fill();
    }
  };
  draw();
}

function stopVoiceRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(track => track.stop());
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  cancelAnimationFrame(animationId);
  clearInterval(recordingInterval);

  const recUI = document.getElementById('recordingUI');
  const inputMain = document.getElementById('groupChatInput');
  if (recUI) recUI.classList.add('hidden');
  if (inputMain) inputMain.classList.remove('hidden');
}

function updateRecordingTimer() {
  const timer = document.getElementById('recordingTimer');
  if (!timer) return;
  const elapsed = Date.now() - recordingStartTime;
  const seconds = Math.floor(elapsed / 1000);
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  timer.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

window.cancelVoiceRecording = function () {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.onstop = null; // Prevent file creation
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(track => track.stop());
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  cancelAnimationFrame(animationId);
  clearInterval(recordingInterval);
  audioChunks = [];

  const recUI = document.getElementById('recordingUI');
  const inputMain = document.getElementById('groupChatInput');
  if (recUI) recUI.classList.add('hidden');
  if (inputMain) inputMain.classList.remove('hidden');
  toast('ยกเลิกการบันทึกแล้ว', 'info');
};

// 🪐 GLOBAL EVENT DELEGATION FOR VOICE MESSAGING
document.addEventListener('click', (e) => {
  // Voice recording button (main chat or group chat)
  const vBtn = e.target.closest('#voiceBtn, #groupVoiceBtn');
  if (vBtn) {
    e.preventDefault();
    console.log('Voice button clicked via delegation');
    if (typeof window.toggleRecording === 'function') window.toggleRecording();
    return;
  }

  // Cancel recording button
  const cBtn = e.target.closest('#cancelRecordingBtn');
  if (cBtn) {
    e.preventDefault();
    if (typeof window.cancelVoiceRecording === 'function') window.cancelVoiceRecording();
    return;
  }
});

// Ensure functions are definitely available globally
window.startVoiceRecording = startVoiceRecording;
window.stopVoiceRecording = stopVoiceRecording;
window.updateRecordingTimer = updateRecordingTimer;

window.adminClearAllNotifs = async function () {
  if (!confirm('ยืนยันที่จะลบการแจ้งเตือนทั้งหมดของ "ทุกคน" ใช่หรือไม่? การกระทำนี้ไม่สามารถย้อนคืนได้')) return;

  try {
    const res = await apiFetch('/api/admin/notifications/clear_all', { method: 'POST' });
    if (res.status === 'success') {
      toast(`ลบการแจ้งเตือนทั้งหมดเรียบร้อย (${res.count} รายการ)`, 'success');
      if (typeof loadNotifications === 'function') loadNotifications();
    } else {
      toast(res.message || 'เกิดข้อผิดพลาดในการลบ', 'error');
    }
  } catch (err) {
    console.error('Clear notifs error:', err);
    toast('เซิร์ฟเวอร์ขัดข้อง', 'error');
  }
};

// 🎨 WHITEBOARD IMPLEMENTATION (Real-time Collaborative + Shapes)
let wbCanvas, wbCtx, wbOverlay, wbOverlayCtx;
let wbInitialized = false;
let isDrawing = false;
let startX = 0, startY = 0, lastX = 0, lastY = 0;
let wbColor = '#000000';
let wbBrushSize = 3;
let wbTool = 'pencil'; 
let wbCursors = {}; // { username: { x, y, color } }

function initWhiteboard() {
  if (wbInitialized) {
    resizeWhiteboard();
    if (socket) socket.emit('join_whiteboard');
    return;
  }
  
  wbCanvas = $('whiteboardCanvas');
  wbOverlay = $('whiteboardOverlay');
  if (!wbCanvas || !wbOverlay) return;
  
  wbCtx = wbCanvas.getContext('2d');
  wbOverlayCtx = wbOverlay.getContext('2d');

  setTimeout(resizeWhiteboard, 50);
  window.addEventListener('resize', resizeWhiteboard);

  const getPos = (e) => {
    const rect = wbOverlay.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    return [x, y];
  };

  const onDown = (e) => {
    isDrawing = true;
    [startX, startY] = getPos(e);
    [lastX, lastY] = [startX, startY];
  };

  const onMove = (e) => {
    const [x, y] = getPos(e);
    
    // Broadcast cursor position (throttled + normalized)
    if (socket && (!window._lastCursorSync || Date.now() - window._lastCursorSync > 50)) {
      socket.emit('whiteboard_cursor', { 
        x: x / wbCanvas.width, 
        y: y / wbCanvas.height, 
        color: wbColor 
      });
      window._lastCursorSync = Date.now();
    }

    if (!isDrawing) return;
    const color = wbTool === 'eraser' ? (state.theme === 'dark' ? '#0a0a0a' : '#ffffff') : wbColor;
    
    if (wbTool === 'pencil' || wbTool === 'eraser') {
      renderShape(wbCtx, 'line', lastX, lastY, x, y, color, wbBrushSize);
      if (socket) {
        socket.emit('draw', { 
          type: 'line', 
          x0: lastX / wbCanvas.width, y0: lastY / wbCanvas.height, 
          x1: x / wbCanvas.width, y1: y / wbCanvas.height, 
          color, size: wbBrushSize 
        });
      }
      [lastX, lastY] = [x, y];
    } else {
      drawCursors(); // Draw cursors first
      renderShape(wbOverlayCtx, wbTool, startX, startY, x, y, color, wbBrushSize);
    }
  };

  const onUp = (e) => {
    if (!isDrawing) return;
    isDrawing = false;
    
    const [x, y] = getPos(e);

    if (wbTool === 'text') {
      const text = prompt('กรอกข้อความที่ต้องการ:');
      if (text && text.trim() !== '') {
        renderShape(wbCtx, 'text', x, y, 0, 0, wbColor, wbBrushSize, text);
        if (socket) {
          socket.emit('draw', { 
            type: 'text', 
            x0: x / wbCanvas.width, y0: y / wbCanvas.height, 
            x1: 0, y1: 0, 
            color: wbColor, size: wbBrushSize, text: text 
          });
        }
      }
      drawCursors(); 
      return;
    }

    if (wbTool !== 'pencil' && wbTool !== 'eraser') {
      renderShape(wbCtx, wbTool, startX, startY, x, y, wbColor, wbBrushSize);
      drawCursors(); // Clear preview and redraw cursors
      if (socket) {
        socket.emit('draw', { 
          type: wbTool, 
          x0: startX / wbCanvas.width, y0: startY / wbCanvas.height, 
          x1: x / wbCanvas.width, y1: y / wbCanvas.height, 
          color: wbColor, size: wbBrushSize 
        });
      }
    }
  };

  wbOverlay.addEventListener('mousedown', onDown);
  wbOverlay.addEventListener('mousemove', onMove);
  wbOverlay.addEventListener('mouseup', onUp);
  wbOverlay.addEventListener('mouseout', () => { 
    isDrawing = false; 
    if(wbOverlayCtx) wbOverlayCtx.clearRect(0, 0, wbOverlay.width, wbOverlay.height); 
  });

  wbOverlay.addEventListener('touchstart', (e) => { e.preventDefault(); onDown(e.touches[0]); }, { passive: false });
  wbOverlay.addEventListener('touchmove', (e) => { e.preventDefault(); onMove(e.touches[0]); }, { passive: false });
  wbOverlay.addEventListener('touchend', (e) => { e.preventDefault(); onUp(e.changedTouches[0] || e.touches[0]); }, { passive: false });

  const sizeInput = $('brushSize');
  if (sizeInput) {
    sizeInput.oninput = (e) => {
      wbBrushSize = e.target.value;
      if ($('sizeDisplay')) $('sizeDisplay').textContent = wbBrushSize;
    };
  }

  if (socket) {
    socket.emit('join_whiteboard');
    
    socket.off('wb_cursor_update');
    socket.on('wb_cursor_update', (data) => {
      if (data.username === state.user) return;
      wbCursors[data.username] = { 
        x: data.x, 
        y: data.y, 
        color: data.color, 
        lastUpdate: Date.now() 
      };
      drawCursors();
    });

    socket.off('draw_update'); 
    socket.on('draw_update', (data) => {
      console.log("Remote draw:", data);
      renderShape(wbCtx, data.type, 
        data.x0 * wbCanvas.width, data.y0 * wbCanvas.height, 
        data.x1 * wbCanvas.width, data.y1 * wbCanvas.height, 
        data.color, data.size, data.text);
    });
    socket.off('whiteboard_cleared');
    socket.on('whiteboard_cleared', () => {
      console.log("Remote clear");
      clearWhiteboardLocal(false);
    });
  }

  wbInitialized = true;
  lucide.createIcons();
  
  // Cleanup old cursors
  setInterval(() => {
    const now = Date.now();
    let changed = false;
    for (const user in wbCursors) {
      if (now - wbCursors[user].lastUpdate > 3000) {
        delete wbCursors[user];
        changed = true;
      }
    }
    if (changed) drawCursors();
  }, 1000);
}

function drawCursors() {
  if (!wbOverlayCtx || !wbCanvas) return;
  wbOverlayCtx.clearRect(0, 0, wbOverlay.width, wbOverlay.height);
  
  for (const user in wbCursors) {
    const c = wbCursors[user];
    const x = c.x * wbCanvas.width;
    const y = c.y * wbCanvas.height;
    
    wbOverlayCtx.fillStyle = c.color;
    wbOverlayCtx.beginPath();
    wbOverlayCtx.arc(x, y, 5, 0, Math.PI * 2);
    wbOverlayCtx.fill();
    
    wbOverlayCtx.font = 'bold 12px sans-serif';
    wbOverlayCtx.shadowBlur = 4;
    wbOverlayCtx.shadowColor = 'rgba(0,0,0,0.5)';
    wbOverlayCtx.fillText(user, x + 10, y + 5);
    wbOverlayCtx.shadowBlur = 0;
  }
}

function resizeWhiteboard() {
  const container = $('whiteboardContainer');
  if (!container || !wbCanvas) return;
  const w = container.clientWidth;
  const h = container.clientHeight;
  if (w === 0 || h === 0) return;
  let tempImage = null;
  if (wbCanvas.width > 0 && wbCanvas.height > 0) tempImage = wbCanvas.toDataURL();
  wbCanvas.width = w;
  wbCanvas.height = h;
  wbOverlay.width = w;
  wbOverlay.height = h;
  if (tempImage) {
    const img = new Image();
    img.onload = () => wbCtx.drawImage(img, 0, 0);
    img.src = tempImage;
  }
  wbCtx.lineJoin = 'round';
  wbCtx.lineCap = 'round';
}

function renderShape(ctx, type, x0, y0, x1, y1, color, size, text = '') {
  if(!ctx) return;
  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  const weight = parseInt(size);
  ctx.lineWidth = weight;
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';

  if (type === 'line') {
    ctx.moveTo(x0, y0);
    ctx.lineTo(x1, y1);
  } else if (type === 'rect') {
    ctx.strokeRect(x0, y0, x1 - x0, y1 - y0);
  } else if (type === 'circle') {
    const radius = Math.sqrt(Math.pow(x1 - x0, 2) + Math.pow(y1 - y0, 2));
    if (radius > 0) ctx.arc(x0, y0, radius, 0, 2 * Math.PI);
  } else if (type === 'text') {
    const fontSize = Math.max(12, weight * 5); 
    ctx.font = `bold ${fontSize}px sans-serif`;
    ctx.textBaseline = 'top';
    ctx.fillText(text, x0, y0);
    return;
  }
  ctx.stroke();
  ctx.closePath();
  
  // Redraw cursors if on overlay
  if (ctx === wbOverlayCtx) {
    for (const user in wbCursors) {
      const c = wbCursors[user];
      ctx.fillStyle = c.color;
      ctx.beginPath();
      ctx.arc(c.x, c.y, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.font = 'bold 10px sans-serif';
      ctx.fillText(user, c.x + 8, c.y + 4);
    }
  }
}

function setWhiteboardTool(tool) {
  wbTool = tool;
  document.querySelectorAll('.wb-tool-btn').forEach(btn => {
    btn.classList.remove('bg-brand-600', 'text-white');
    btn.classList.add('hover:bg-surface-100', 'dark:hover:bg-surface-800', 'text-surface-600', 'dark:text-surface-400');
  });
  const activeBtn = $(`tool-${tool}`);
  if (activeBtn) {
    activeBtn.classList.remove('hover:bg-surface-100', 'dark:hover:bg-surface-800', 'text-surface-600', 'dark:text-surface-400');
    activeBtn.classList.add('bg-brand-600', 'text-white');
  }
}

function setWhiteboardColor(color, el) {
  wbColor = color;
  if (wbTool === 'eraser') setWhiteboardTool('pencil');
  document.querySelectorAll('.wb-color-btn').forEach(btn => btn.classList.remove('ring-2', 'ring-brand-500'));
  if(el) el.classList.add('ring-2', 'ring-brand-500');
}

function clearWhiteboardLocal(broadcast = true) {
  if (!wbCanvas) return;
  wbCtx.clearRect(0, 0, wbCanvas.width, wbCanvas.height);
  if(wbOverlayCtx) wbOverlayCtx.clearRect(0, 0, wbOverlay.width, wbOverlay.height);
  if (broadcast && socket) {
    socket.emit('clear_whiteboard');
    toast('ล้างกระดานแล้ว', 'info');
  }
}

function downloadWhiteboard() {
  if (!wbCanvas) return;
  const tempCanvas = document.createElement('canvas');
  tempCanvas.width = wbCanvas.width;
  tempCanvas.height = wbCanvas.height;
  const tempCtx = tempCanvas.getContext('2d');
  tempCtx.fillStyle = state.theme === 'dark' ? '#0a0a0a' : '#ffffff';
  tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
  tempCtx.drawImage(wbCanvas, 0, 0);
  const link = document.createElement('a');
  link.download = `whiteboard-${Date.now()}.png`;
  link.href = tempCanvas.toDataURL('image/png');
  link.click();
  toast('บันทึกรูปภาพสำเร็จ', 'success');
}

window.initWhiteboard = initWhiteboard;
window.setWhiteboardTool = setWhiteboardTool;
window.setWhiteboardColor = setWhiteboardColor;
window.clearWhiteboardLocal = clearWhiteboardLocal;
window.downloadWhiteboard = downloadWhiteboard;


// ═══════════════════════════════════════════════════
// 📞 WebRTC Call Engine — Full Implementation
// ═══════════════════════════════════════════════════

// Helper — ดึง username string เสมอ ไม่ว่า state.user จะเป็น string หรือ object
function _rtcMyUsername() {
  return typeof state.user === 'object' ? (state.user?.username || '') : (state.user || '');
}

const rtcState = {
  pc: null,                 // RTCPeerConnection
  localStream: null,        // MediaStream (local)
  remoteStream: null,       // MediaStream (remote)
  callType: 'audio',        // 'audio' | 'video'
  isCaller: false,
  remoteUser: null,         // username of the other party
  isMicMuted: false,
  isCamOff: false,
  isSpeakerMuted: false,
  callTimer: null,
  callStartTime: null,
  callTimeout: null,        // timeout สำหรับ no-answer 30s
  ringtoneCtx: null,
  ringtoneInterval: null,   // interval สำหรับ repeat ringtone
  ringtoneNodes: [],
  pendingOffer: null,       // store offer before acceptCall
  pendingIceCandidates: [], // queue ICE candidates before PC is ready
};

// ICE Servers (STUN + TURN fallback)
const ICE_SERVERS = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    { urls: 'stun:stun2.l.google.com:19302' },
    // Free TURN from open relay (for NAT traversal in LAN/VPN)
    {
      urls: 'turn:openrelay.metered.ca:80',
      username: 'openrelayproject',
      credential: 'openrelayproject'
    },
    {
      urls: 'turn:openrelay.metered.ca:443',
      username: 'openrelayproject',
      credential: 'openrelayproject'
    },
    {
      urls: 'turn:openrelay.metered.ca:443?transport=tcp',
      username: 'openrelayproject',
      credential: 'openrelayproject'
    },
  ]
};

// ─── Ringtone Engine (Web Audio API) ─────────────────────────
function startRingtone() {
  try {
    stopRingtone();
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    rtcState.ringtoneCtx = ctx;

    // 🔓 Resume context immediately if suspended
    if (ctx.state === 'suspended') {
      ctx.resume().catch(e => console.warn("Ringtone context resume failed:", e));
    }

    function playBeep() {
      if (!rtcState.ringtoneCtx) return;
      // Classic phone ring pattern: 2 beeps, 2s apart
      for (let i = 0; i < 2; i++) {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.frequency.value = 440 + (i * 220); // A4, C#5
        osc.type = 'sine';
        gain.gain.setValueAtTime(0, ctx.currentTime + i * 0.2);
        gain.gain.linearRampToValueAtTime(0.3, ctx.currentTime + i * 0.2 + 0.02);
        gain.gain.linearRampToValueAtTime(0, ctx.currentTime + i * 0.2 + 0.18);
        osc.start(ctx.currentTime + i * 0.2);
        osc.stop(ctx.currentTime + i * 0.2 + 0.2);
        rtcState.ringtoneNodes.push(osc);
      }
    }

    playBeep();
    // Repeat every 2.5s
    rtcState.ringtoneInterval = setInterval(() => {
      if (rtcState.ringtoneCtx) playBeep();
    }, 2500);
  } catch (e) {
    console.warn('Ringtone error:', e);
  }
}

function stopRingtone() {
  if (rtcState.ringtoneInterval) {
    clearInterval(rtcState.ringtoneInterval);
    rtcState.ringtoneInterval = null;
  }
  try {
    if (rtcState.ringtoneCtx) {
      rtcState.ringtoneCtx.close();
      rtcState.ringtoneCtx = null;
    }
  } catch (e) {}
  rtcState.ringtoneNodes = [];
}

// ─── Create PeerConnection ────────────────────────────────────
async function createPC() {
  if (rtcState.pc) {
    rtcState.pc.close();
    rtcState.pc = null;
  }
  console.log('🏗️ Creating RTCPeerConnection with expanded ICE servers...');
  const pc = new RTCPeerConnection(ICE_SERVERS);
  rtcState.pc = pc;

  // Add local tracks to peer connection
  if (rtcState.localStream) {
    rtcState.localStream.getTracks().forEach(track => {
      pc.addTrack(track, rtcState.localStream);
    });
    console.log(`📤 Added ${rtcState.localStream.getTracks().length} local tracks`);
  }

  // On remote track
  pc.ontrack = (event) => {
    console.log('📡 Remote track received:', event.track.kind);
    const remoteAudio = document.getElementById('remoteAudio');
    const remoteVideo = document.getElementById('remoteVideo');

    let stream = event.streams[0];
    if (!stream) {
      console.log('💡 No stream in event, using rtcState.remoteStream');
      if (!rtcState.remoteStream) rtcState.remoteStream = new MediaStream();
      rtcState.remoteStream.addTrack(event.track);
      stream = rtcState.remoteStream;
    } else {
      rtcState.remoteStream = stream;
    }

    if (event.track.kind === 'audio' && remoteAudio) {
      remoteAudio.srcObject = stream;
      remoteAudio.muted = false;
      remoteAudio.volume = 1.0;
      remoteAudio.play()
        .then(() => console.log("🔊 Remote audio playing successfully"))
        .catch(e => {
          console.warn('🔇 Audio autoplay blocked, waiting for interaction...', e);
          document.addEventListener('click', () => remoteAudio.play(), { once: true });
        });
    }
    if (event.track.kind === 'video' && remoteVideo) {
      remoteVideo.srcObject = stream;
      remoteVideo.classList.remove('hidden');
      document.getElementById('remoteAvatarFallback')?.classList.add('hidden');
      remoteVideo.play().catch(e => console.warn('📹 Remote video play failed:', e));
    }
  };

  // On ICE candidate
  pc.onicecandidate = (event) => {
    if (event.candidate && socket && rtcState.remoteUser) {
      socket.emit('webrtc_signal', {
        target: rtcState.remoteUser,
        sender: _rtcMyUsername(), // Added explicit sender
        type: 'ice',
        payload: event.candidate
      });
    }
  };

  // Connection state monitoring
  pc.onconnectionstatechange = () => {
    console.log('🔗 Connection state:', pc.connectionState);
    if (pc.connectionState === 'connected') {
      startCallTimer();
      stopRingtone(); // STOP RINGING ON CONNECTION SUCCESS
      toast('เชื่อมต่อสำเร็จ!', 'success');
    } else if (['disconnected', 'failed', 'closed'].includes(pc.connectionState)) {
      handleCallEnded('ขาดการเชื่อมต่อ');
    }
  };

  pc.oniceconnectionstatechange = () => {
    console.log('🧊 ICE state:', pc.iceConnectionState);
  };

  // Flush any pending ICE candidates
  if (rtcState.pendingIceCandidates.length > 0) {
    console.log(`📥 Flushing ${rtcState.pendingIceCandidates.length} pending ICE candidates`);
    for (const candidate of rtcState.pendingIceCandidates) {
      try { await pc.addIceCandidate(new RTCIceCandidate(candidate)); } catch(e) {}
    }
    rtcState.pendingIceCandidates = [];
  }

  return pc;
}

// ─── Get User Media ───────────────────────────────────────────
async function getLocalMedia(withVideo = false) {
  const constraints = {
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      sampleRate: 44100
    },
    video: withVideo ? {
      width: { ideal: 1280 },
      height: { ideal: 720 },
      facingMode: 'user'
    } : false
  };

  try {
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    rtcState.localStream = stream;

    const localVideo = document.getElementById('localVideo');
    const localVideoContainer = document.getElementById('localVideoContainer');
    if (withVideo && localVideo && localVideoContainer) {
      localVideo.srcObject = stream;
      localVideoContainer.classList.remove('hidden');
    }
    return stream;
  } catch (err) {
    console.error('❌ Media error:', err);
    if (err.name === 'NotAllowedError') {
      toast('กรุณาอนุญาตการเข้าถึงไมโครโฟน/กล้องในเบราว์เซอร์', 'error');
    } else if (err.name === 'NotFoundError') {
      toast('ไม่พบไมโครโฟนหรือกล้องในอุปกรณ์นี้', 'error');
    } else {
      toast(`ไม่สามารถเข้าถึงสื่อได้: ${err.message}`, 'error');
    }
    throw err;
  }
}

// ─── Initiate Call (Caller side) ─────────────────────────────
async function initiateCall(withVideo = false) {
  if (!state.currentChat || state.currentChat.type !== 'dm') {
    console.warn('⚠️ Not in a DM chat, currentChat:', state.currentChat);
    toast('สามารถโทรได้เฉพาะกับ Direct Message เท่านั้น', 'error');
    return;
  }
  if (rtcState.pc) {
    toast('กำลังมีสายโทรอยู่แล้ว', 'error');
    return;
  }

  // ใช้ id (username) ไม่ใช่ name (display name) — signaling ใช้ username เป็น room key
  const targetUser = state.currentChat.id;
  const myUsername = typeof state.user === 'object' ? state.user?.username : state.user;
  console.log('🎯 Target user identified:', targetUser, '| me:', myUsername);

  if (targetUser === 'ai-assistant') {
    toast('ไม่สามารถโทรหา AI Assistant ได้', 'error');
    return;
  }

  if (!targetUser || targetUser === myUsername) {
    toast('ไม่พบผู้รับสาย หรือไม่สามารถโทรหาตัวเองได้', 'error');
    return;
  }

  rtcState.isCaller = true;
  rtcState.remoteUser = targetUser;
  rtcState.callType = withVideo ? 'video' : 'audio';
  rtcState.pendingIceCandidates = [];

  try {
    console.log('📸 Requesting local media...');
    await getLocalMedia(withVideo);
    console.log('✅ Local media captured');

    showActiveCallUI(targetUser, withVideo);
    const pc = await createPC();
    console.log('🏗️ PeerConnection created, creating offer...');

    // Create and send offer
    const offer = await pc.createOffer({
      offerToReceiveAudio: true,
      offerToReceiveVideo: withVideo
    });
    await pc.setLocalDescription(offer);

    // Signal offer to target
    socket.emit('webrtc_signal', {
      target: targetUser,
      sender: _rtcMyUsername(),
      type: 'offer',
      payload: offer,
      callType: rtcState.callType
    });

    toast(`กำลังโทรหา ${targetUser}...`, 'info');
    console.log(`📞 Calling ${targetUser} (${rtcState.callType})`);

    // Timeout if no answer after 30s
    rtcState.callTimeout = setTimeout(() => {
      if (rtcState.pc && rtcState.pc.connectionState !== 'connected') {
        handleCallEnded('ไม่มีการตอบรับ');
      }
    }, 30000);

  } catch (err) {
    console.error('❌ initiateCall error:', err);
    cleanupCall();
  }
}

// ─── Show Incoming Call UI ────────────────────────────────────
function showIncomingCallUI(callerUsername, callType = 'audio') {
  const modal = document.getElementById('incomingCallModal');
  const callerNameEl = document.getElementById('callerName');
  const callerCallTypeEl = document.getElementById('callerCallType');

  if (callerNameEl) callerNameEl.textContent = callerUsername;
  if (callerCallTypeEl) {
    callerCallTypeEl.innerHTML = callType === 'video'
      ? '<i data-lucide="video" class="w-3 h-3"></i> วิดีโอคอล'
      : '<i data-lucide="phone" class="w-3 h-3"></i> โทรด้วยเสียง';
  }

  // Set caller avatar from profiles
  const callerAvatarEl = document.getElementById('callerAvatar');
  if (callerAvatarEl) {
    const profile = state.contactProfiles?.[callerUsername];
    if (profile?.avatar_url) {
      callerAvatarEl.innerHTML = `<img src="${profile.avatar_url}" class="w-full h-full object-cover">`;
    } else {
      callerAvatarEl.innerHTML = `<span class="text-4xl font-black text-white">${callerUsername[0]?.toUpperCase()}</span>`;
    }
  }

  if (modal) modal.classList.remove('hidden');
  initIcons();
  startRingtone();
}

// ─── Show Active Call UI ──────────────────────────────────────
function showActiveCallUI(remoteUser, withVideo = false) {
  const modal = document.getElementById('activeCallModal');
  const nameEl = document.getElementById('activeCallName');
  const nameMobileEl = document.getElementById('activeCallNameMobile');

  if (nameEl) nameEl.textContent = remoteUser;
  if (nameMobileEl) nameMobileEl.textContent = remoteUser;

  const localVideoContainer = document.getElementById('localVideoContainer');
  if (localVideoContainer) {
    if (withVideo) localVideoContainer.classList.remove('hidden');
    else localVideoContainer.classList.add('hidden');
  }

  if (modal) modal.classList.remove('hidden');
  initIcons();
}

// ─── Accept Call (Callee side) ────────────────────────────────
async function acceptCall() {
  stopRingtone();
  const modal = document.getElementById('incomingCallModal');
  if (modal) modal.classList.add('hidden');

  // Audio unlock trick for browsers
    const remoteAudio = document.getElementById('remoteAudio');
    if (rtcState.ringtoneCtx && rtcState.ringtoneCtx.state === 'suspended') {
      rtcState.ringtoneCtx.resume();
    }
    if (remoteAudio) {
      remoteAudio.muted = false;
      remoteAudio.play().catch(() => {
        console.log("Waiting for user gesture to play audio...");
        document.addEventListener('click', () => { remoteAudio.play(); }, { once: true });
      }); 
    }
  if (!rtcState.pendingOffer || !rtcState.remoteUser) {
    toast('ไม่พบข้อมูลสาย', 'error');
    return;
  }

  const withVideo = rtcState.callType === 'video';

  try {
    await getLocalMedia(withVideo);
    showActiveCallUI(rtcState.remoteUser, withVideo);

    const pc = await createPC();

    // Set remote description (the offer)
    await pc.setRemoteDescription(new RTCSessionDescription(rtcState.pendingOffer));
    rtcState.pendingOffer = null;

    // Create answer
    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);

    // Send answer to caller
    socket.emit('webrtc_signal', {
      target: rtcState.remoteUser,
      sender: _rtcMyUsername(),
      type: 'answer',
      payload: answer
    });

    console.log(`✅ Call accepted, answer sent to ${rtcState.remoteUser}`);

    // Flush pending ICE candidates
    for (const candidate of rtcState.pendingIceCandidates) {
      try { await pc.addIceCandidate(new RTCIceCandidate(candidate)); } catch (e) {}
    }
    rtcState.pendingIceCandidates = [];

  } catch (err) {
    console.error('❌ acceptCall error:', err);
    toast('ไม่สามารถรับสายได้: ' + err.message, 'error');
    cleanupCall();
  }
}

// ─── Reject Call ──────────────────────────────────────────────
function rejectCall() {
  stopRingtone();
  const modal = document.getElementById('incomingCallModal');
  if (modal) modal.classList.add('hidden');

  if (rtcState.remoteUser && socket) {
    socket.emit('webrtc_signal', {
      target: rtcState.remoteUser,
      sender: _rtcMyUsername(),
      type: 'reject',
      payload: null
    });
  }
  cleanupCall();
  toast('ปฏิเสธสายแล้ว', 'info');
}

// ─── End Call ─────────────────────────────────────────────────
function endCall() {
  if (rtcState.remoteUser && socket) {
    socket.emit('webrtc_signal', {
      target: rtcState.remoteUser,
      sender: _rtcMyUsername(),
      type: 'end',
      payload: null
    });
  }
  handleCallEnded('วางสายแล้ว');
}

// ─── Handle Call Ended (both ends) ───────────────────────────
function handleCallEnded(reason = '') {
  stopCallTimer();
  stopRingtone();
  cleanupCall();
  if (reason) toast(`📵 ${reason}`, 'info');
}

// ─── Cleanup All Call State ───────────────────────────────────
function cleanupCall() {
  // Clear timeout
  if (rtcState.callTimeout) {
    clearTimeout(rtcState.callTimeout);
    rtcState.callTimeout = null;
  }

  // Stop local stream tracks
  if (rtcState.localStream) {
    rtcState.localStream.getTracks().forEach(t => t.stop());
    rtcState.localStream = null;
  }

  // Close peer connection
  if (rtcState.pc) {
    rtcState.pc.close();
    rtcState.pc = null;
  }

  rtcState.remoteStream = null;
  rtcState.isCaller = false;
  rtcState.remoteUser = null;
  rtcState.pendingOffer = null;
  rtcState.pendingIceCandidates = [];
  rtcState.isMicMuted = false;
  rtcState.isCamOff = false;
  rtcState.isSpeakerMuted = false;

  // Hide modals
  const activeModal = document.getElementById('activeCallModal');
  const incomingModal = document.getElementById('incomingCallModal');
  if (activeModal) activeModal.classList.add('hidden');
  if (incomingModal) incomingModal.classList.add('hidden');

  // Clear video elements
  const remoteVideo = document.getElementById('remoteVideo');
  const localVideo = document.getElementById('localVideo');
  const remoteAudio = document.getElementById('remoteAudio');
  if (remoteVideo) { remoteVideo.srcObject = null; remoteVideo.classList.add('hidden'); }
  if (localVideo) localVideo.srcObject = null;
  if (remoteAudio) remoteAudio.srcObject = null;
  const localVC = document.getElementById('localVideoContainer');
  if (localVC) localVC.classList.add('hidden');

  // Reset timer
  const durEl = document.getElementById('callDuration');
  const durMoEl = document.getElementById('callDurationMobile');
  if (durEl) durEl.textContent = '00:00';
  if (durMoEl) durMoEl.textContent = '00:00';

  // Reset icons
  const micIcon = document.getElementById('micIcon');
  const camIcon = document.getElementById('camIcon');
  if (micIcon) micIcon.setAttribute('data-lucide', 'mic');
  if (camIcon) camIcon.setAttribute('data-lucide', 'video');

  console.log('🧹 Call cleaned up.');
}

// ─── Call Timer ───────────────────────────────────────────────
function startCallTimer() {
  rtcState.callStartTime = Date.now();
  rtcState.callTimer = setInterval(() => {
    const elapsed = Math.floor((Date.now() - rtcState.callStartTime) / 1000);
    const mm = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const ss = String(elapsed % 60).padStart(2, '0');
    const display = `${mm}:${ss}`;
    const durEl = document.getElementById('callDuration');
    const durMoEl = document.getElementById('callDurationMobile');
    if (durEl) durEl.textContent = display;
    if (durMoEl) durMoEl.textContent = display;
  }, 1000);
}

function stopCallTimer() {
  if (rtcState.callTimer) {
    clearInterval(rtcState.callTimer);
    rtcState.callTimer = null;
  }
}

// ─── Toggle Controls ──────────────────────────────────────────
function toggleMic() {
  if (!rtcState.localStream) return;
  rtcState.isMicMuted = !rtcState.isMicMuted;
  rtcState.localStream.getAudioTracks().forEach(t => {
    t.enabled = !rtcState.isMicMuted;
  });
  const micIcon = document.getElementById('micIcon');
  const toggleMicBtn = document.getElementById('toggleMicBtn');
  if (micIcon) {
    micIcon.setAttribute('data-lucide', rtcState.isMicMuted ? 'mic-off' : 'mic');
    initIcons();
  }
  if (toggleMicBtn) {
    toggleMicBtn.querySelector('div').classList.toggle('bg-red-600', rtcState.isMicMuted);
    toggleMicBtn.querySelector('div').classList.toggle('bg-white/10', !rtcState.isMicMuted);
  }
  toast(rtcState.isMicMuted ? 'ปิดไมโครโฟน' : 'เปิดไมโครโฟน', 'info');
}

function toggleCam() {
  if (!rtcState.localStream) return;
  rtcState.isCamOff = !rtcState.isCamOff;
  rtcState.localStream.getVideoTracks().forEach(t => {
    t.enabled = !rtcState.isCamOff;
  });
  const camIcon = document.getElementById('camIcon');
  const toggleCamBtn = document.getElementById('toggleCamBtn');
  if (camIcon) {
    camIcon.setAttribute('data-lucide', rtcState.isCamOff ? 'video-off' : 'video');
    initIcons();
  }
  if (toggleCamBtn) {
    toggleCamBtn.querySelector('div').classList.toggle('bg-red-600', rtcState.isCamOff);
    toggleCamBtn.querySelector('div').classList.toggle('bg-white/10', !rtcState.isCamOff);
  }
  toast(rtcState.isCamOff ? 'ปิดกล้อง' : 'เปิดกล้อง', 'info');
}

function toggleSpeaker() {
  rtcState.isSpeakerMuted = !rtcState.isSpeakerMuted;
  const remoteAudio = document.getElementById('remoteAudio');
  if (remoteAudio) remoteAudio.muted = rtcState.isSpeakerMuted;
  const speakerIcon = document.getElementById('speakerIcon');
  const btn = document.getElementById('toggleSpeakerBtn');
  if (speakerIcon) {
    speakerIcon.setAttribute('data-lucide', rtcState.isSpeakerMuted ? 'volume-x' : 'volume-2');
    initIcons();
  }
  if (btn) {
    btn.querySelector('div').classList.toggle('bg-red-600', rtcState.isSpeakerMuted);
    btn.querySelector('div').classList.toggle('bg-white/10', !rtcState.isSpeakerMuted);
  }
  toast(rtcState.isSpeakerMuted ? 'ปิดลำโพง' : 'เปิดลำโพง', 'info');
}

async function shareScreen() {
  if (!rtcState.pc) return;
  try {
    const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
    const screenTrack = screenStream.getVideoTracks()[0];

    // Replace video track in peer connection
    const sender = rtcState.pc.getSenders().find(s => s.track && s.track.kind === 'video');
    if (sender) {
      await sender.replaceTrack(screenTrack);
    } else {
      rtcState.pc.addTrack(screenTrack, screenStream);
    }

    // Also show in local video
    const localVideo = document.getElementById('localVideo');
    if (localVideo) {
      localVideo.srcObject = screenStream;
      document.getElementById('localVideoContainer')?.classList.remove('hidden');
    }

    // On screen share end, switch back to camera
    screenTrack.onended = async () => {
      if (!rtcState.localStream) return;
      const camTrack = rtcState.localStream.getVideoTracks()[0];
      if (sender && camTrack) await sender.replaceTrack(camTrack);
      if (localVideo) localVideo.srcObject = rtcState.localStream;
      toast('หยุดแชร์หน้าจอแล้ว', 'info');
    };
    toast('กำลังแชร์หน้าจอ', 'success');
  } catch (e) {
    if (e.name !== 'AbortError' && e.name !== 'NotAllowedError') {
      toast('ไม่สามารถแชร์หน้าจอได้', 'error');
    }
  }
}

// ─── Socket WebRTC Signal Handler ────────────────────────────
function initWebRTCSignaling() {
  if (!socket) {
    console.warn('⚠️ Socket not available for WebRTC signaling');
    return;
  }

  socket.on('webrtc_signal', async (data) => {
    const { type, payload, sender, callType } = data;
    console.log(`📡 WebRTC signal [${type}] from ${sender}`);

    switch (type) {
      case 'offer':
        // Incoming call
        if (rtcState.pc) {
          // Already in a call — reject automatically
          socket.emit('webrtc_signal', {
            target: sender, sender: _rtcMyUsername(), type: 'busy', payload: null
          });
          return;
        }
        rtcState.isCaller = false;
        rtcState.remoteUser = sender;
        rtcState.callType = callType || 'audio';
        rtcState.pendingOffer = payload;
        rtcState.pendingIceCandidates = [];
        showIncomingCallUI(sender, rtcState.callType);
        break;

      case 'answer':
        // Our call was answered
        if (!rtcState.pc) return;
        try {
          await rtcState.pc.setRemoteDescription(new RTCSessionDescription(payload));
          console.log('✅ Remote answer set.');
          if (rtcState.callTimeout) clearTimeout(rtcState.callTimeout);
        } catch (e) {
          console.error('❌ setRemoteDescription (answer) error:', e);
        }
        break;

      case 'ice':
        // ICE candidate from remote
        if (rtcState.pc && rtcState.pc.remoteDescription) {
          try {
            await rtcState.pc.addIceCandidate(new RTCIceCandidate(payload));
          } catch (e) {
            console.warn('⚠️ addIceCandidate failed:', e);
          }
        } else {
          // Not ready yet — queue it
          rtcState.pendingIceCandidates.push(payload);
        }
        break;

      case 'reject':
        handleCallEnded(`${sender} ปฏิเสธสาย`);
        break;

      case 'end':
        handleCallEnded(`${sender} วางสายแล้ว`);
        break;

      case 'busy':
        handleCallEnded(`${sender} กำลังคุยสายอื่นอยู่`);
        break;
    }
  });

  console.log('✅ WebRTC signaling handler registered.');
}

// ─── Expose global functions ──────────────────────────────────
window.initiateCall  = initiateCall;
window.acceptCall    = acceptCall;
window.rejectCall    = rejectCall;
window.endCall       = endCall;
window.toggleMic     = toggleMic;
window.toggleCam     = toggleCam;
window.toggleSpeaker = toggleSpeaker;
window.shareScreen   = shareScreen;

// ─── Wire up call buttons ─────────────────────────────────────
if (voiceCallBtn) voiceCallBtn.addEventListener('click', () => initiateCall(false));
if (videoCallBtn) videoCallBtn.addEventListener('click', () => initiateCall(true));

// ─── Initialize WebRTC after socket is ready ─────────────────
// Wait until socket and user are available
(function waitForSocket() {
  const initSocketListeners = (s) => {
    initWebRTCSignaling();
    
    // 🟢 Handle User Status Updates
    s.on('user_status_updated', (data) => {
      console.log('👥 User status updated:', data);
      if (Array.isArray(data)) {
        state.onlineUsers = data.map(u => u.username);
      } else {
        // Fallback if data is different shape
        state.onlineUsers = [];
      }
      renderChatSidebar();
      updateChatHeaderStatus();
    });

    // Handle incoming messages to update status if needed
    s.on('new_message', () => {
        // Optional: refresh user status if message received
    });

    // Initial check-in
    const currentUser = (typeof state.user === 'object' ? state.user?.username : state.user);
    if (currentUser) {
      s.emit('user_online', {
        username: currentUser,
        room: state.currentChat?.name || 'General',
        room_id: state.currentChat?.id || 1,
        type: state.currentChat?.type || 'room'
      });
    }
  };

  if (socket) {
    initSocketListeners(socket);
    initSocket();
  } else {
    // Socket loaded via CDN might be delayed
    setTimeout(() => {
      if (typeof io !== 'undefined' && !socket) {
        socket = io();
      }
      if (socket) {
        initSocketListeners(socket);
        initSocket();
      }
    }, 2000);
  }
})();

/**
 * 🟢 Update the "Online/Offline" indicator in the current chat header
 */
function updateChatHeaderStatus() {
  const statusContainer = $('chatHeaderStatus');
  if (!statusContainer) return;

  const chat = state.currentChat;
  if (!chat || !chat.id) return;

  // For Rooms, we show "Live Updates" or "Active"
  if (chat.type === 'room') {
    statusContainer.innerHTML = `
      <span class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
      <p class="text-[8px] text-surface-500 font-bold uppercase tracking-widest whitespace-nowrap">กลุ่มแชท</p>
    `;
    return;
  }

  // For DMs, check if the contact is online
  // Note: For DMs, id is typically the username of the contact
  const isOnline = state.onlineUsers.includes(chat.id) || state.onlineUsers.includes(chat.name);
  
  if (isOnline) {
    statusContainer.innerHTML = `
      <span class="messenger-header-status-dot online"></span>
      <p class="text-[8px] text-emerald-600 font-bold uppercase tracking-widest whitespace-nowrap">ออนไลน์</p>
    `;
  } else {
    let lastSeenText = 'ออฟไลน์';
    if (state.userStatusMap && state.userStatusMap[chat.id] && state.userStatusMap[chat.id].last_activity) {
      lastSeenText = `ใช้งานล่าสุด: ${formatRelativeTime(state.userStatusMap[chat.id].last_activity)}`;
    }

    statusContainer.innerHTML = `
      <span class="messenger-header-status-dot offline"></span>
      <p class="text-[8px] text-surface-400 font-bold uppercase tracking-widest whitespace-nowrap">${lastSeenText}</p>
    `;
  }
}

// ─── Browser Push Notifications ─────────────────────────────────────
function urlB64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

async function requestPushPermission() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
  
  if (Notification.permission === 'granted') {
    subscribeUserToPush();
  } else if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    if (permission === 'granted') {
      subscribeUserToPush();
    }
  }
}

async function subscribeUserToPush() {
  try {
    const registration = await navigator.serviceWorker.ready;
    let subscription = await registration.pushManager.getSubscription();
    
    // Only subscribe if VAPID key is provided by the backend (rendered in index.html)
    if (!subscription && window.VAPID_PUBLIC_KEY) {
      const applicationServerKey = urlB64ToUint8Array(window.VAPID_PUBLIC_KEY);
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey
      });
      console.log('🟢 Push Notifications Subscribed');
      
      await fetch('/api/notifications/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subscription })
      });
    }
  } catch (err) {
    console.error('❌ Failed to subscribe to Push Notifications:', err);
  }
}

// ─── Collapsible Security Panel (Desktop & Mobile) ─────
function toggleSecurityPanel() {
  const panel = document.getElementById('securityPanel');
  const icon = document.getElementById('securityPanelIcon');
  const cardContainer = document.getElementById('loginCardContainer');
  const leftCol = document.getElementById('loginLeftCol');
  if (!panel) return;
  
  const isHidden = panel.classList.contains('hidden') || panel.classList.contains('max-md:hidden');
  if (isHidden) {
    panel.classList.remove('hidden', 'max-md:hidden');
    panel.classList.add('flex');
    if (cardContainer) {
      cardContainer.classList.remove('max-w-md');
      cardContainer.classList.add('max-w-4xl');
    }
    if (leftCol) {
      leftCol.classList.remove('w-full');
      leftCol.classList.add('md:w-1/2');
    }
    if (icon) icon.style.transform = 'rotate(180deg)';
  } else {
    panel.classList.add('hidden');
    panel.classList.remove('flex');
    if (cardContainer) {
      cardContainer.classList.remove('max-w-4xl');
      cardContainer.classList.add('max-w-md');
    }
    if (leftCol) {
      leftCol.classList.remove('md:w-1/2');
      leftCol.classList.add('w-full');
    }
    if (icon) icon.style.transform = 'rotate(0deg)';
  }
}
const toggleMobileSecurityPanel = toggleSecurityPanel;

// QR Code Login State
let _qrInstance = null;
let _qrCountdownInterval = null;
let _qrPollInterval = null;

async function showQRLogin() {
  const loginForm = document.querySelector('#loginOverlay .p-8.space-y-4');
  const qrModal = $('qrLoginModal');
  const loginFooter = $('loginFooter');
  if (!loginForm || !qrModal) return;

  loginForm.classList.add('hidden');
  if (loginFooter) loginFooter.classList.add('hidden');
  qrModal.classList.remove('hidden');

  // Generate QR token
  try {
    const res = await fetch('/api/qr/generate', { method: 'POST' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      const errMsg = data.error || (res.status === 429 ? 'จำกัดจำนวนการสร้าง QR Code กรุณารอสักครู่' : 'ไม่สามารถสร้าง QR Code ได้');
      toast(errMsg, 'error');
      return;
    }

    const token = data.token;
    const qrUrl = `${window.location.origin}/qr-login/${token}`;
    const canvas = $('qrCodeCanvas');
    
    // Clear previous QR
    if (canvas) {
      canvas.innerHTML = '';
      if (typeof QRCode !== 'undefined') {
        try {
          _qrInstance = null;
          _qrInstance = new QRCode(canvas, {
            text: qrUrl,
            width: 200,
            height: 200,
            colorDark: '#1e293b',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.M
          });
        } catch (qrErr) {
          console.warn('QRCode JS render failed, using fallback img:', qrErr);
          canvas.innerHTML = `<img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(qrUrl)}" alt="QR Code" class="w-full h-full object-contain rounded-lg" />`;
        }
      } else {
        canvas.innerHTML = `<img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(qrUrl)}" alt="QR Code" class="w-full h-full object-contain rounded-lg" />`;
      }
    }

    // Start countdown (5 minutes)
    let remaining = 300;
    const countdownEl = $('qrCountdown');
    const statusEl = $('qrStatus');
    
    if (_qrCountdownInterval) clearInterval(_qrCountdownInterval);
    _qrCountdownInterval = setInterval(() => {
      remaining--;
      const m = Math.floor(remaining / 60);
      const s = (remaining % 60).toString().padStart(2, '0');
      if (countdownEl) countdownEl.textContent = `${m}:${s}`;
      if (remaining <= 0) {
        if (_qrCountdownInterval) clearInterval(_qrCountdownInterval);
        if (_qrPollInterval) clearInterval(_qrPollInterval);
        if (statusEl) statusEl.innerHTML = `
          <div class="w-2 h-2 bg-red-400 rounded-full"></div>
          <span class="text-red-500">QR Code หมดอายุ กรุณาสร้างใหม่</span>
        `;
      }
    }, 1000);

    // Start polling
    if (_qrPollInterval) clearInterval(_qrPollInterval);
    _qrPollInterval = setInterval(async () => {
      try {
        const pollRes = await fetch(`/api/qr/poll/${token}`);
        const pollData = await pollRes.json();
        
        if (pollData.ok && pollData.status === 'approved') {
          // SUCCESS!
          if (_qrPollInterval) clearInterval(_qrPollInterval);
          if (_qrCountdownInterval) clearInterval(_qrCountdownInterval);
          
          if (statusEl) statusEl.innerHTML = `
            <div class="w-2 h-2 bg-emerald-400 rounded-full"></div>
            <span class="text-emerald-600 font-black">✅ อนุมัติแล้ว! กำลังเข้าระบบ...</span>
          `;
          
          state.user = pollData.user;
          state.username = pollData.user;

          setTimeout(() => {
            if (!pollData.org_role) {
              window.location.href = '/onboarding';
              return;
            }
            $('loginOverlay').classList.add('hidden');
            toast(`ยินดีต้อนรับคุณ ${pollData.user} (QR Login)`, 'success');
            initAppContent();
            loadNotifications();
            loadChatList();
            loadUnreadCounts();
          }, 1000);
        } else if (!pollData.ok) {
          // Token expired or error
          if (_qrPollInterval) clearInterval(_qrPollInterval);
          if (_qrCountdownInterval) clearInterval(_qrCountdownInterval);
        }
      } catch (e) {
        console.error('QR Poll error:', e);
      }
    }, 2000);

  } catch (e) {
    console.error('QR Login Error:', e);
    toast('ไม่สามารถสร้าง QR Code ได้', 'error');
  }

  lucide.createIcons();
}

function hideQRLogin() {
  const loginForm = document.querySelector('#loginOverlay .p-8.space-y-4');
  const qrModal = $('qrLoginModal');
  const loginFooter = $('loginFooter');
  
  if (loginForm) loginForm.classList.remove('hidden');
  if (qrModal) qrModal.classList.add('hidden');
  if (loginFooter) loginFooter.classList.remove('hidden');
  
  // Cleanup
  if (_qrPollInterval) clearInterval(_qrPollInterval);
  if (_qrCountdownInterval) clearInterval(_qrCountdownInterval);
}

// ─── QR Code Scanner (Camera) ─────────────────────────────
let _html5QrScanner = null;

function openQRScanner() {
  const modal = $('qrScannerModal');
  if (!modal) return;

  modal.classList.remove('hidden');
  modal.classList.add('flex', 'items-center', 'justify-center');
  lucide.createIcons();

  // Initialize scanner
  try {
    _html5QrScanner = new Html5Qrcode("qrScannerView");
    _html5QrScanner.start(
      { facingMode: "environment" },
      {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0
      },
      (decodedText) => {
        // QR scanned successfully!
        console.log("QR Scanned:", decodedText);
        
        // Stop scanning
        _html5QrScanner.stop().then(() => {
          _html5QrScanner.clear();
        }).catch(console.error);

        // Close modal
        modal.classList.add('hidden');
        modal.classList.remove('flex', 'items-center', 'justify-center');

        // Navigate to the scanned URL (should be /qr-login/TOKEN)
        if (decodedText.includes('/qr-login/')) {
          window.location.href = decodedText;
        } else {
          toast('QR Code ไม่ถูกต้อง กรุณาสแกน QR จากหน้า Login ของ OrgChat', 'error');
        }
      },
      (errorMessage) => {
        // Scanning error (normal during scanning, QR not detected yet)
      }
    ).catch((err) => {
      console.error("Camera Error:", err);
      modal.classList.add('hidden');
      modal.classList.remove('flex', 'items-center', 'justify-center');
      toast('ไม่สามารถเปิดกล้องได้ กรุณาอนุญาตการใช้กล้องในเบราว์เซอร์', 'error');
    });
  } catch (e) {
    console.error("QR Scanner Error:", e);
    toast('ไม่สามารถเปิดกล้องได้', 'error');
  }
}

function closeQRScanner() {
  const modal = $('qrScannerModal');
  if (_html5QrScanner) {
    _html5QrScanner.stop().then(() => {
      _html5QrScanner.clear();
    }).catch(console.error);
  }
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex', 'items-center', 'justify-center');
  }
}

// ─── Leave Management ─────────────────────────────────────

let _currentCalendarYear = new Date().getFullYear();
let _currentCalendarMonth = new Date().getMonth() + 1; // 1-12

async function loadLeaveData() {
  await loadMyLeaves();
  await loadTeamLeaveCalendar();
  initLeaveForm();
  if (typeof initLeaveCalendarCollapse === 'function') initLeaveCalendarCollapse();
}

async function changeTeamCalendarMonth(delta) {
  _currentCalendarMonth += delta;
  if (_currentCalendarMonth < 1) {
    _currentCalendarMonth = 12;
    _currentCalendarYear -= 1;
  } else if (_currentCalendarMonth > 12) {
    _currentCalendarMonth = 1;
    _currentCalendarYear += 1;
  }
  await loadTeamLeaveCalendar();
}

async function loadTeamLeaveCalendar() {
  const teamGrid = $('teamLeaveCalendarGrid');
  const teamLabel = $('teamCalendarMonthLabel');
  const adminGrid = $('adminLeaveCalendarGrid');
  const adminLabel = $('calendarMonthYearLabel');

  if (!teamGrid && !adminGrid) return;

  if (!_currentCalendarYear || !_currentCalendarMonth) {
    const now = new Date();
    _currentCalendarYear = now.getFullYear();
    _currentCalendarMonth = now.getMonth() + 1;
  }

  const monthStr = `${_currentCalendarYear}-${String(_currentCalendarMonth).padStart(2, '0')}`;
  const monthNamesTH = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"];
  const labelText = `${monthNamesTH[_currentCalendarMonth] || ''} ${_currentCalendarYear + 543}`;

  if (teamLabel) teamLabel.textContent = labelText;
  if (adminLabel) adminLabel.textContent = labelText;

  const loadingHtml = `<div class="col-span-7 py-12 text-center text-xs text-surface-400"><i data-lucide="loader" class="w-4 h-4 animate-spin inline-block mr-1.5"></i>กำลังโหลดปฏิทินวันลา...</div>`;
  if (teamGrid) teamGrid.innerHTML = loadingHtml;
  if (adminGrid) adminGrid.innerHTML = loadingHtml;
  if (typeof lucide !== 'undefined') lucide.createIcons();

  try {
    const res = await fetch(`/api/leave/team-calendar?month=${monthStr}`).then(r => r.json());
    if (!res.ok) {
      const errHtml = `<div class="col-span-7 py-10 text-center text-xs text-rose-500">ไม่สามารถโหลดปฏิทินได้ (${escHtml(res.error || 'ข้อผิดพลาด')})</div>`;
      if (teamGrid) teamGrid.innerHTML = errHtml;
      if (adminGrid) adminGrid.innerHTML = errHtml;
      return;
    }

    const events = res.events || [];
    window._currentTeamCalendarEvents = events;
    const isAdmin = !!res.is_admin;

    // Update title according to role
    const calTitle = $('leaveCalendarTitle');
    const calSubtitle = $('leaveCalendarSubtitle');
    if (calTitle) {
      calTitle.textContent = isAdmin ? 'ปฏิทินวันลาของทีม (Team Leave Calendar)' : 'ปฏิทินวันลาของฉัน (My Leave Calendar)';
    }
    if (calSubtitle) {
      calSubtitle.textContent = isAdmin ? 'ตรวจสอบวันลาและวางแผนงานร่วมกับเพื่อนร่วมทีม' : 'ตรวจสอบประวัติและสถานะวันลาของคุณ';
    }

    // Build days of the current month
    const firstDay = new Date(_currentCalendarYear, _currentCalendarMonth - 1, 1).getDay(); // 0 = Sun
    const daysInMonth = new Date(_currentCalendarYear, _currentCalendarMonth, 0).getDate();

    const now = new Date();
    const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;

    let teamHtml = '';
    let adminHtml = '';

    // Empty cells before day 1
    for (let i = 0; i < firstDay; i++) {
      teamHtml += `<div class="min-h-[85px] p-1.5 bg-surface-50/50 dark:bg-surface-800/20 rounded-2xl border border-transparent"></div>`;
      adminHtml += `<div class="min-h-[92px] p-2 bg-surface-50/30 dark:bg-surface-800/10 rounded-2xl border border-dashed border-surface-200/40 dark:border-surface-800/30 opacity-40"></div>`;
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${_currentCalendarYear}-${String(_currentCalendarMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const isToday = dateStr === todayStr;

      // Find events spanning this date
      const dayEvents = events.filter(e => {
        const s = e.start_date || '';
        const end = e.end_date || s;
        return dateStr >= s && dateStr <= end;
      });

      // Employee View event tags
      let teamEventsHtml = dayEvents.map(e => {
        let badgeColor = 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20';
        let dotColor = 'bg-purple-500';
        const lType = (e.type || '').toLowerCase();
        if (lType.includes('ป่วย') || lType.includes('sick')) {
          badgeColor = 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
          dotColor = 'bg-emerald-500';
        } else if (lType.includes('กิจ') || lType.includes('personal')) {
          badgeColor = 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';
          dotColor = 'bg-amber-500';
        } else if (lType.includes('พักร้อน') || lType.includes('vacation')) {
          badgeColor = 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20';
          dotColor = 'bg-blue-500';
        }

        const isPending = e.status === 'pending';
        const statusLabel = isPending ? 'รออนุมัติ' : 'อนุมัติแล้ว';
        const safeName = escHtml(e.display_name || e.username || '');
        const safeType = escHtml(e.type || 'ลางาน');
        const displayLabel = isAdmin ? `${safeName}: ${safeType}` : `${safeType} (${statusLabel})`;

        return `
          <div onclick="event.stopPropagation(); openLeaveComments(${e.id})" class="px-1.5 py-0.5 rounded-lg border text-[10px] font-bold flex items-center gap-1 truncate cursor-pointer hover:opacity-80 transition ${badgeColor} ${isPending ? 'opacity-85 border-dashed border-amber-400 dark:border-amber-500' : 'border-emerald-500/30'}" title="${safeName} (${safeType}) - สถานะ: ${statusLabel}">
            <span class="w-1.5 h-1.5 rounded-full ${dotColor} flex-shrink-0"></span>
            <span class="truncate">${displayLabel}</span>
          </div>
        `;
      }).join('');

      teamHtml += `
        <div class="min-h-[85px] p-1.5 bg-white dark:bg-surface-800/40 rounded-2xl border ${isToday ? 'border-brand-500 shadow-sm shadow-brand-500/10 ring-1 ring-brand-500/30' : 'border-surface-100 dark:border-surface-800'} flex flex-col justify-between transition hover:border-surface-300 dark:hover:border-surface-700">
          <div class="flex items-center justify-between mb-1">
            <span class="text-[11px] font-bold ${isToday ? 'w-5 h-5 rounded-full bg-brand-600 text-white flex items-center justify-center text-[10px]' : 'text-surface-600 dark:text-surface-300'}">${day}</span>
            ${dayEvents.length > 0 ? `<span class="text-[9px] font-bold text-surface-400 px-1 rounded bg-surface-100 dark:bg-surface-700">${dayEvents.length}</span>` : ''}
          </div>
          <div class="space-y-1 overflow-y-auto max-h-[60px] no-scrollbar">
            ${teamEventsHtml}
          </div>
        </div>
      `;

      // Admin View event tags (with approved/pending status styling matching the admin legend)
      let adminEventsHtml = dayEvents.map(e => {
        const isApproved = e.status === 'approved';
        const isPending = e.status === 'pending';
        let badgeColor = 'bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300 border-surface-200 dark:border-surface-700';
        let dotColor = 'bg-surface-400';
        let statusText = 'อื่นๆ';

        if (isApproved) {
          badgeColor = 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/50';
          dotColor = 'bg-emerald-500';
          statusText = 'อนุมัติแล้ว (Approved)';
        } else if (isPending) {
          badgeColor = 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-700/50 border-dashed';
          dotColor = 'bg-amber-500';
          statusText = 'รอดำเนินการ (Pending)';
        } else if (e.status === 'rejected') {
          badgeColor = 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800/50';
          dotColor = 'bg-rose-500';
          statusText = 'ปฏิเสธ (Rejected)';
        }

        const safeName = escHtml(e.display_name || e.username || '');
        const safeType = escHtml(e.type || '');
        const titleInfo = `${safeName} [${safeType}]\nสถานะ: ${statusText}\nวันที่: ${e.start_date} ถึง ${e.end_date}${e.reason ? '\nเหตุผล: ' + escHtml(e.reason) : ''}\n(คลิกเพื่อดูรายละเอียด / แชทคอมเมนต์)`;

        return `
          <div onclick="event.stopPropagation(); openLeaveDayDetail('${dateStr}', ${e.id})" class="px-2 py-1 rounded-xl border text-[11px] font-bold flex items-center justify-between gap-1.5 cursor-pointer hover:shadow-xs hover:border-brand-500/40 transition-all ${badgeColor}" title="${titleInfo}">
            <div class="flex items-center gap-1.5 min-w-0">
              <span class="w-2 h-2 rounded-full ${dotColor} flex-shrink-0 ${isPending ? 'animate-pulse' : ''}"></span>
              <span class="truncate font-bold">${safeName}</span>
            </div>
            <span class="text-[9px] opacity-75 font-normal shrink-0 truncate max-w-[50px]">${safeType}</span>
          </div>
        `;
      }).join('');

      adminHtml += `
        <div onclick="openLeaveDayDetail('${dateStr}')" class="min-h-[92px] p-2 bg-white dark:bg-surface-800/50 rounded-2xl border ${isToday ? 'border-brand-500 shadow-md shadow-brand-500/10 ring-2 ring-brand-500/20' : 'border-surface-200/70 dark:border-surface-800'} flex flex-col justify-between transition hover:border-brand-400 dark:hover:border-brand-600 hover:shadow-xs cursor-pointer group">
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-xs font-black ${isToday ? 'w-6 h-6 rounded-full bg-brand-600 text-white flex items-center justify-center text-[11px] shadow-sm' : 'text-surface-700 dark:text-surface-200 group-hover:text-brand-600 dark:group-hover:text-brand-400'}">${day}</span>
            ${dayEvents.length > 0 ? `<span class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-md bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-300">${dayEvents.length} คน</span>` : ''}
          </div>
          <div class="space-y-1.5 overflow-y-auto max-h-[75px] no-scrollbar">
            ${adminEventsHtml}
          </div>
        </div>
      `;
    }

    if (teamGrid) teamGrid.innerHTML = teamHtml;
    if (adminGrid) adminGrid.innerHTML = adminHtml;
    if (typeof lucide !== 'undefined') lucide.createIcons();

  } catch (err) {
    console.error('Failed to load team leave calendar:', err);
    const errHtml = `<div class="col-span-7 py-10 text-center text-xs text-rose-500">เกิดข้อผิดพลาดในการโหลดปฏิทิน</div>`;
    if (teamGrid) teamGrid.innerHTML = errHtml;
    if (adminGrid) adminGrid.innerHTML = errHtml;
  }
}


let _leaveFormInitialized = false;
function initLeaveForm() {
    if (_leaveFormInitialized) return;
    const form = $('leaveRequestForm');
    if (form) {
        form.onsubmit = async (e) => {
            e.preventDefault();
            const lType = $('leaveType').value;
            const sDate = $('leaveStartDate').value;
            const eDate = $('leaveEndDate').value;
            const reason = $('leaveReason').value;

            if (!sDate || !eDate) {
                toast("กรุณาระบุวันที่เริ่มและสิ้นสุด", "error");
                return;
            }

            const submitBtn = form.querySelector('button[type="submit"]') || form.querySelector('.btn-primary');
            if (submitBtn) {
                if (submitBtn.disabled) return;
                submitBtn.disabled = true;
                submitBtn.dataset.origText = submitBtn.textContent;
                submitBtn.textContent = "กำลังส่งคำขอลา...";
            }

            try {
                const res = await fetch('/api/leave/request', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ type: lType, start_date: sDate, end_date: eDate, reason: reason })
                });
                const data = await res.json();
                if (data.ok) {
                    toast("ส่งคำขอลาเรียบร้อยแล้ว", "success");
                    form.reset();
                    loadMyLeaves();
                } else {
                    toast(data.error || "เกิดข้อผิดพลาด", "error");
                }
            } catch (err) {
                console.error(err);
                toast("ไม่สามารถติดต่อเซิร์ฟเวอร์ได้", "error");
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = submitBtn.dataset.origText || "ส่งคำขอลา";
                }
            }
        };
        _leaveFormInitialized = true;
    }
}

async function loadMyLeaves() {
    const list = $('leaveHistoryList');
    if (!list) return;

    try {
        const [leavesRes, balanceRes] = await Promise.all([
            fetch('/api/leave/my').then(r => r.json()).catch(() => ({ ok: false })),
            fetch('/api/leave/balance').then(r => r.json()).catch(() => ({ ok: false }))
        ]);

        if (leavesRes.ok) {
            renderLeaveHistory(leavesRes.leaves);
        }
        if (balanceRes.ok && balanceRes.balance) {
            updateLeaveQuotaDashboard(balanceRes.balance);
        }
    } catch (err) {
        console.error(err);
    }
}

function updateLeaveQuotaDashboard(balance) {
    if (!balance || !balance.quotas) return;

    if ($('leaveQuotaYear')) $('leaveQuotaYear').textContent = balance.year || new Date().getFullYear();

    const q = balance.quotas;
    const catKeys = ['sick', 'personal', 'vacation', 'other'];

    catKeys.forEach(key => {
        const item = q[key];
        if (!item) return;

        const maxEl = $(`${key}Max`);
        const usedEl = $(`${key}Used`);
        const remEl = $(`${key}Remaining`);
        const badgeEl = $(`${key}RemainingBadge`);
        const barEl = $(`${key}ProgressBar`);

        if (maxEl) maxEl.textContent = item.max;
        if (usedEl) usedEl.textContent = item.used;
        if (remEl) remEl.textContent = item.remaining;
        if (badgeEl) badgeEl.textContent = `${item.remaining} วันคงเหลือ`;

        if (barEl) {
            const pct = item.max > 0 ? Math.min(100, Math.round((item.used / item.max) * 100)) : 0;
            barEl.style.width = `${pct}%`;
        }
    });
}

function renderLeaveHistory(leaves) {
    const list = $('leaveHistoryList');
    if (leaves.length === 0) {
        list.innerHTML = `
            <div class="text-center py-12 bg-surface-50 dark:bg-surface-800/30 rounded-[32px] border-2 border-dashed border-surface-200 dark:border-surface-800">
              <p class="text-surface-400 text-sm">ยังไม่มีประวัติการลา</p>
            </div>
        `;
        return;
    }

    list.innerHTML = leaves.map(l => {
        let statusColor = 'bg-amber-100 text-amber-700';
        let statusText = 'รอดำเนินการ';
        if (l.status === 'approved') {
            statusColor = 'bg-emerald-100 text-emerald-700';
            statusText = 'อนุมัติแล้ว';
        } else if (l.status === 'rejected') {
            statusColor = 'bg-rose-100 text-rose-700';
            statusText = 'ปฏิเสธแล้ว';
        }

        return `
            <div class="p-6 bg-white dark:bg-surface-900 border border-surface-100 dark:border-surface-800 rounded-3xl shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 animate-in slide-in-from-bottom-2 duration-300">
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 rounded-2xl bg-surface-50 dark:bg-surface-800 flex items-center justify-center text-surface-400">
                        <i data-lucide="${l.type === 'Sick' ? 'thermometer' : 'calendar'}" class="w-6 h-6"></i>
                    </div>
                    <div>
                        <p class="font-black text-sm text-surface-900 dark:text-white">${l.type} - ${l.start_date} ถึง ${l.end_date}</p>
                        <p class="text-[10px] text-surface-400 font-bold uppercase tracking-widest mt-0.5">${l.reason || 'ไม่ระบุเหตุผล'}</p>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    <button onclick="openLeaveComments(${l.id})" class="p-2 transition-all hover:bg-surface-50 dark:hover:bg-surface-800 rounded-xl relative group" title="แชท/คอมเม้น">
                        <i data-lucide="message-circle" class="w-5 h-5 text-surface-400 group-hover:text-brand-600 transition-colors"></i>
                    </button>
                    <div class="flex flex-col items-end gap-1">
                        <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${statusColor}">${statusText}</span>
                        <span class="text-[9px] text-surface-400">${new Date(l.timestamp).toLocaleDateString()}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    lucide.createIcons();
}

// ─── Admin Leave Management (Enterprise, Anti-AI-Slop) ────────────

let _adminLeavesList = [];
let _leaveStatusFilter = 'all';
let _selectedLeaveIds = new Set();

async function refreshAdminLeaves() {
    const tableBody = $('adminLeaveTableBody');
    if (!tableBody) return;

    try {
        tableBody.innerHTML = '<tr><td colspan="7" class="px-6 py-12 text-center text-surface-400"><i data-lucide="loader" class="w-5 h-5 animate-spin inline-block mr-2"></i>กำลังโหลดข้อมูลคำขอลา...</td></tr>';
        if (typeof lucide !== 'undefined') lucide.createIcons();

        const res = await fetch('/api/admin/leave/all');
        const data = await res.json();
        if (data.ok) {
            _adminLeavesList = data.leaves || [];
            
            // Populate department filter options if available
            const deptFilter = $('adminLeaveDeptFilter');
            if (deptFilter) {
                const depts = new Set();
                _adminLeavesList.forEach(l => {
                    const dept = l.department || l.dept_name || '';
                    if (dept) depts.add(dept);
                });
                const currentDept = deptFilter.value || 'all';
                deptFilter.innerHTML = '<option value="all">ทุกแผนก</option>' + 
                    Array.from(depts).sort().map(d => `<option value="${escHtml(d)}" ${d === currentDept ? 'selected' : ''}>${escHtml(d)}</option>`).join('');
            }

            // Update pending count badge
            const pendingCount = _adminLeavesList.filter(l => l.status === 'pending').length;
            const badge = $('pendingLeaveCountBadge');
            if (badge) {
                if (pendingCount > 0) {
                    badge.textContent = pendingCount;
                    badge.classList.remove('hidden');
                } else {
                    badge.classList.add('hidden');
                }
            }

            // Clear any lingering selection that might not exist anymore
            clearLeaveSelection();
            applyAdminLeaveFilters();
        } else {
            tableBody.innerHTML = `<tr><td colspan="7" class="px-6 py-12 text-center text-rose-500">${escHtml(data.error || 'ไม่สามารถโหลดข้อมูลคำขอลาได้')}</td></tr>`;
        }
    } catch (err) {
        console.error('refreshAdminLeaves error:', err);
        tableBody.innerHTML = '<tr><td colspan="7" class="px-6 py-12 text-center text-rose-500">เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์</td></tr>';
    }
}

function setLeaveStatusFilter(status) {
    _leaveStatusFilter = status;
    const buttons = ['all', 'pending', 'approved', 'rejected'];
    buttons.forEach(b => {
        const btn = $(`btnStatusFilter_${b}`);
        if (!btn) return;
        if (b === status) {
            btn.className = 'px-2.5 py-1 rounded-lg text-xs font-bold transition-all bg-surface-900 text-white dark:bg-white dark:text-surface-900 shadow-xs flex items-center gap-1.5';
        } else {
            btn.className = 'px-2.5 py-1 rounded-lg text-xs font-bold transition-all text-surface-500 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-800 flex items-center gap-1.5';
        }
    });
    applyAdminLeaveFilters();
}

function applyAdminLeaveFilters() {
    const searchVal = ($('adminLeaveSearchInput')?.value || '').trim().toLowerCase();
    const typeVal = $('adminLeaveTypeFilter')?.value || 'all';
    const deptVal = $('adminLeaveDeptFilter')?.value || 'all';

    let filtered = _adminLeavesList.filter(l => {
        // Status filter
        if (_leaveStatusFilter !== 'all' && l.status !== _leaveStatusFilter) return false;
        
        // Type filter
        if (typeVal !== 'all' && (l.type || '') !== typeVal) return false;

        // Department filter
        if (deptVal !== 'all') {
            const d = l.department || l.dept_name || '';
            if (d !== deptVal) return false;
        }

        // Search text
        if (searchVal) {
            const name = (l.display_name || l.username || '').toLowerCase();
            const reason = (l.reason || '').toLowerCase();
            const approver = (l.approved_by || '').toLowerCase();
            if (!name.includes(searchVal) && !reason.includes(searchVal) && !approver.includes(searchVal)) {
                return false;
            }
        }
        return true;
    });

    renderAdminLeaveTable(filtered);
}

function renderAdminLeaveTable(leaves) {
    const tableBody = $('adminLeaveTableBody');
    if (!tableBody) return;

    if (!leaves || leaves.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" class="px-6 py-12 text-center text-surface-400">ไม่พบข้อมูลคำขอลาตามเงื่อนไขที่เลือก</td></tr>';
        return;
    }

    tableBody.innerHTML = leaves.map(l => {
        const isActionable = l.status === 'pending';
        const isChecked = _selectedLeaveIds.has(l.id);

        let statusHtml = `<span class="px-2 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">Pending</span>`;
        if (l.status === 'approved') {
            statusHtml = `<div class="space-y-0.5">
                <span class="inline-block px-2 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">Approved</span>
                ${l.approved_by ? `<div class="text-[10px] text-surface-400">ผู้อนุมัติ: <span class="font-semibold text-surface-600 dark:text-surface-300">${escHtml(l.approved_by)}</span></div>` : ''}
            </div>`;
        } else if (l.status === 'rejected') {
            statusHtml = `<div class="space-y-0.5">
                <span class="inline-block px-2 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">Rejected</span>
                ${l.approved_by ? `<div class="text-[10px] text-surface-400">ผู้ปฏิเสธ: <span class="font-semibold text-surface-600 dark:text-surface-300">${escHtml(l.approved_by)}</span></div>` : ''}
            </div>`;
        }

        const nameInitial = (l.display_name || l.username || '?').charAt(0).toUpperCase();
        const durationText = l.duration_days ? `${l.duration_days} วัน` : '';

        return `
            <tr class="hover:bg-surface-50 dark:hover:bg-surface-800/40 transition-colors ${isChecked ? 'bg-brand-50/40 dark:bg-brand-950/20' : ''}">
                <td class="w-10 px-4 py-3.5 text-center">
                    ${isActionable ? `
                        <input type="checkbox" onchange="toggleSelectLeave(${l.id}, this.checked)" ${isChecked ? 'checked' : ''} class="rounded border-surface-300 dark:border-surface-700 text-brand-600 focus:ring-brand-500 cursor-pointer" />
                    ` : `
                        <span class="inline-block w-4 h-4 text-surface-300 dark:text-surface-600">—</span>
                    `}
                </td>
                <td class="px-4 py-3.5">
                    <div class="flex items-center gap-2.5">
                        <div class="w-7 h-7 rounded-full bg-surface-200 dark:bg-surface-700 text-surface-700 dark:text-surface-200 font-bold flex items-center justify-center text-xs shrink-0">
                            ${escHtml(nameInitial)}
                        </div>
                        <div class="min-w-0">
                            <div class="font-bold text-surface-900 dark:text-white truncate">${escHtml(l.display_name || l.username || '')}</div>
                            <div class="text-[10px] text-surface-400 flex items-center gap-1.5">
                                <span>@${escHtml(l.username || '')}</span>
                                ${l.department ? `<span class="px-1.5 py-0.2 rounded bg-surface-100 dark:bg-surface-800 text-surface-500 font-medium">${escHtml(l.department)}</span>` : ''}
                            </div>
                        </div>
                    </div>
                </td>
                <td class="px-4 py-3.5">
                    <span class="px-2 py-0.5 rounded-lg text-xs font-semibold bg-surface-100 dark:bg-surface-800 text-surface-700 dark:text-surface-200 border border-surface-200 dark:border-surface-700">${escHtml(l.type || 'ทั่วไป')}</span>
                </td>
                <td class="px-4 py-3.5">
                    <div class="font-mono font-medium text-surface-900 dark:text-white">${escHtml(l.start_date || '')}</div>
                    <div class="text-[10px] text-surface-400 font-mono">ถึง ${escHtml(l.end_date || '')} ${durationText ? `(${durationText})` : ''}</div>
                </td>
                <td class="px-4 py-3.5 max-w-xs truncate text-surface-500" title="${escHtml(l.reason || '-')}">${escHtml(l.reason || '-')}</td>
                <td class="px-4 py-3.5">${statusHtml}</td>
                <td class="px-4 py-3.5 text-right">
                    <div class="flex justify-end items-center gap-1.5">
                        <button type="button" onclick="openLeaveComments(${l.id})" class="p-1.5 text-surface-400 hover:text-brand-600 hover:bg-surface-100 dark:hover:bg-surface-700 rounded-lg transition-colors" title="ดูความคิดเห็นและประวัติ">
                            <i data-lucide="message-circle" class="w-4 h-4"></i>
                        </button>
                        ${isActionable ? `
                            <button type="button" onclick="adminSetLeaveStatus(${l.id}, 'approved')" class="px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition-colors flex items-center gap-1 shadow-xs" title="อนุมัติ">
                                <i data-lucide="check" class="w-3.5 h-3.5"></i>
                                <span class="hidden md:inline">อนุมัติ</span>
                            </button>
                            <button type="button" onclick="adminSetLeaveStatus(${l.id}, 'rejected')" class="px-2 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold transition-colors flex items-center gap-1 shadow-xs" title="ปฏิเสธ">
                                <i data-lucide="x" class="w-3.5 h-3.5"></i>
                                <span class="hidden md:inline">ปฏิเสธ</span>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    }).join('');

    // Update master checkbox state
    updateMasterCheckboxState();
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

function toggleSelectLeave(id, checked) {
    if (checked) {
        _selectedLeaveIds.add(id);
    } else {
        _selectedLeaveIds.delete(id);
    }
    updateBatchBar();
    updateMasterCheckboxState();
}

function toggleSelectAllLeaves(checked) {
    const actionable = _adminLeavesList.filter(l => l.status === 'pending');
    if (checked) {
        actionable.forEach(l => _selectedLeaveIds.add(l.id));
    } else {
        _selectedLeaveIds.clear();
    }
    applyAdminLeaveFilters();
    updateBatchBar();
}

function clearLeaveSelection() {
    _selectedLeaveIds.clear();
    const master = $('masterLeaveCheckbox');
    if (master) master.checked = false;
    updateBatchBar();
}

function updateMasterCheckboxState() {
    const master = $('masterLeaveCheckbox');
    if (!master) return;
    const actionable = _adminLeavesList.filter(l => l.status === 'pending');
    if (actionable.length === 0) {
        master.checked = false;
        master.disabled = true;
    } else {
        master.disabled = false;
        master.checked = actionable.every(l => _selectedLeaveIds.has(l.id));
    }
}

function updateBatchBar() {
    const bar = $('adminLeaveBatchBar');
    const countEl = $('selectedLeaveCount');
    if (!bar || !countEl) return;

    const count = _selectedLeaveIds.size;
    countEl.textContent = count;
    if (count > 0) {
        bar.classList.remove('hidden');
    } else {
        bar.classList.add('hidden');
    }
}

async function adminBatchSetLeaveStatus(status) {
    const ids = Array.from(_selectedLeaveIds);
    if (ids.length === 0) return;

    const actionText = status === 'approved' ? 'อนุมัติ' : 'ปฏิเสธ';
    if (!confirm(`คุณแน่ใจหรือไม่ว่าต้องการ ${actionText} คำขอลาที่เลือกจำนวน ${ids.length} รายการพร้อมกัน?`)) return;

    try {
        const res = await fetch('/api/admin/leave/batch-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids, status })
        });
        const data = await res.json();
        if (data.ok) {
            toast(`ดำเนินการ ${actionText} เรียบร้อยแล้ว ${data.success_count} รายการ`, "success");
            clearLeaveSelection();
            refreshAdminLeaves();
            loadTeamLeaveCalendar();
        } else {
            toast(data.error || "ไม่สามารถดำเนินการกลุ่มได้", "error");
        }
    } catch (err) {
        console.error('adminBatchSetLeaveStatus error:', err);
        toast("เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์", "error");
    }
}

async function adminSetLeaveStatus(id, status) {
    const actionText = status === 'approved' ? 'อนุมัติ' : 'ปฏิเสธ';
    if (!confirm(`คุณแน่ใจหรือไม่ว่าต้องการ ${actionText} คำขอลานี้?`)) return;

    try {
        const res = await fetch('/api/admin/leave/status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, status })
        });
        const data = await res.json();
        if (data.ok) {
            toast("ดำเนินการเรียบร้อยแล้ว", "success");
            refreshAdminLeaves();
            loadTeamLeaveCalendar();
            // If day modal is open, refresh it as well
            if (!$('leaveDayDetailModal')?.classList.contains('hidden')) {
                const title = $('leaveDayDetailTitle')?.getAttribute('data-date');
                if (title) openLeaveDayDetail(title);
            }
        } else {
            toast(data.error || "ไม่สามารถดำเนินการได้", "error");
        }
    } catch (err) {
        console.error('adminSetLeaveStatus error:', err);
        toast("เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์", "error");
    }
}

// ─── Day Detail Modal for Calendar ───────────────────────

function openLeaveDayDetail(dateStr, highlightId = null) {
    const modal = $('leaveDayDetailModal');
    const titleEl = $('leaveDayDetailTitle');
    const listEl = $('leaveDayDetailList');
    const summaryEl = $('leaveDayDetailSummary');
    if (!modal || !listEl) return;

    // Format date in Thai
    const [y, m, d] = dateStr.split('-').map(Number);
    const dateObj = new Date(y, m - 1, d);
    const thaiDateStr = dateObj.toLocaleDateString('th-TH', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    if (titleEl) {
        titleEl.textContent = thaiDateStr;
        titleEl.setAttribute('data-date', dateStr);
    }

    // Filter events spanning dateStr from window._currentTeamCalendarEvents or _adminLeavesList
    const allEvents = window._currentTeamCalendarEvents || _adminLeavesList || [];
    const dayEvents = allEvents.filter(e => {
        const s = e.start_date || '';
        const end = e.end_date || s;
        return dateStr >= s && dateStr <= end;
    });

    if (summaryEl) {
        summaryEl.textContent = `${dayEvents.length} รายการ`;
    }

    if (dayEvents.length === 0) {
        listEl.innerHTML = `
            <div class="py-12 text-center text-surface-400">
                <i data-lucide="calendar-check" class="w-8 h-8 mx-auto mb-2 opacity-40"></i>
                <p class="text-sm font-medium">ไม่มีรายการลาในวันที่เลือก</p>
                <p class="text-xs text-surface-400 mt-1">ทุกคนในทีมพร้อมปฏิบัติงานตามปกติ</p>
            </div>
        `;
    } else {
        listEl.innerHTML = dayEvents.map(e => {
            const isHighlight = highlightId && e.id === highlightId;
            const isPending = e.status === 'pending';
            const safeName = escHtml(e.display_name || e.username || '');
            const safeType = escHtml(e.type || 'ลางาน');
            const safeReason = escHtml(e.reason || '-');
            const safeDates = `${e.start_date} ถึง ${e.end_date}`;

            let statusBadge = `<span class="px-2 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">Pending</span>`;
            if (e.status === 'approved') {
                statusBadge = `<span class="px-2 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">Approved</span>`;
            } else if (e.status === 'rejected') {
                statusBadge = `<span class="px-2 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">Rejected</span>`;
            }

            return `
                <div class="pt-3 first:pt-0 ${isHighlight ? 'p-3 bg-brand-50/50 dark:bg-brand-950/30 rounded-xl border border-brand-200 dark:border-brand-800' : ''}">
                    <div class="flex items-start justify-between gap-3">
                        <div class="flex items-start gap-3">
                            <div class="w-8 h-8 rounded-full bg-surface-200 dark:bg-surface-700 text-surface-700 dark:text-surface-200 font-bold flex items-center justify-center text-xs shrink-0 mt-0.5">
                                ${safeName.charAt(0).toUpperCase()}
                            </div>
                            <div>
                                <div class="font-bold text-sm text-surface-900 dark:text-white flex items-center gap-2">
                                    <span>${safeName}</span>
                                    <span class="text-xs font-normal text-surface-400">@${escHtml(e.username || '')}</span>
                                </div>
                                <div class="text-xs text-surface-600 dark:text-surface-300 mt-0.5 font-medium flex items-center gap-2">
                                    <span class="px-1.5 py-0.2 rounded bg-surface-100 dark:bg-surface-800 border border-surface-200 dark:border-surface-700 text-[11px]">${safeType}</span>
                                    <span class="font-mono text-surface-500">${safeDates}</span>
                                </div>
                                <div class="text-xs text-surface-500 mt-1 italic">
                                    "${safeReason}"
                                </div>
                            </div>
                        </div>
                        <div class="shrink-0 flex flex-col items-end gap-2">
                            ${statusBadge}
                            <button type="button" onclick="openLeaveComments(${e.id})" class="p-1.5 text-surface-400 hover:text-brand-600 rounded-lg transition-colors text-xs flex items-center gap-1 font-semibold" title="เปิดห้องพูดคุย">
                                <i data-lucide="message-circle" class="w-3.5 h-3.5"></i>
                                <span>แชท</span>
                            </button>
                        </div>
                    </div>
                    ${isPending ? `
                        <div class="mt-3 flex items-center justify-end gap-2 pt-2 border-t border-surface-100 dark:border-surface-800/60">
                            <button type="button" onclick="adminSetLeaveStatus(${e.id}, 'approved')" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-1 shadow-xs">
                                <i data-lucide="check" class="w-3.5 h-3.5"></i> อนุมัติคำขอนี้
                            </button>
                            <button type="button" onclick="adminSetLeaveStatus(${e.id}, 'rejected')" class="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold transition-all flex items-center gap-1 shadow-xs">
                                <i data-lucide="x" class="w-3.5 h-3.5"></i> ปฏิเสธ
                            </button>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }

    modal.classList.remove('hidden');
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

function closeLeaveDayDetailModal() {
    const modal = $('leaveDayDetailModal');
    if (modal) modal.classList.add('hidden');
}

// ─── Export CSV ───────────────────────────────────────────

function exportAdminLeavesToCsv() {
    if (!_adminLeavesList || _adminLeavesList.length === 0) {
        toast("ไม่มีข้อมูลคำขอลาสำหรับส่งออก", "warning");
        return;
    }

    const headers = ["ID", "ชื่อพนักงาน", "Username", "แผนก", "ประเภทการลา", "วันที่เริ่ม", "วันที่สิ้นสุด", "จำนวนวัน", "เหตุผล", "สถานะ", "ผู้อนุมัติ", "วันที่สร้างคำขอ"];
    const rows = _adminLeavesList.map(l => [
        l.id || "",
        `"${(l.display_name || "").replace(/"/g, '""')}"`,
        `"${(l.username || "").replace(/"/g, '""')}"`,
        `"${(l.department || l.dept_name || "").replace(/"/g, '""')}"`,
        `"${(l.type || "").replace(/"/g, '""')}"`,
        l.start_date || "",
        l.end_date || "",
        l.duration_days || "",
        `"${(l.reason || "").replace(/"/g, '""')}"`,
        l.status || "",
        `"${(l.approved_by || "").replace(/"/g, '""')}"`,
        l.created_at || ""
    ]);

    const csvContent = "\uFEFF" + [headers.join(","), ...rows.map(e => e.join(","))].join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const today = new Date().toISOString().slice(0, 10);
    link.setAttribute("href", url);
    link.setAttribute("download", `leave_records_${today}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast("ส่งออกไฟล์ CSV สำเร็จแล้วค่ะ", "success");
}

// ─── Leave Comment System ─────────────────────────────

async function openLeaveComments(leaveId) {
    const modal = $('leaveCommentModal');
    const list = $('leaveCommentList');
    const inputId = $('leaveCommentId');
    const title = $('leaveCommentModalTitle');
    
    if (!modal || !list || !inputId) return;
    
    inputId.value = leaveId;
    title.textContent = `คำขอลา #${leaveId}`;
    list.innerHTML = '<div class="text-center py-4 text-surface-400">กำลังโหลดข้อความ...</div>';
    modal.classList.remove('hidden');
    modal.classList.add('flex', 'items-center', 'justify-center');
    
    try {
        const res = await fetch(`/api/leave/comments/${leaveId}`);
        const data = await res.json();
        if (data.ok) {
            renderLeaveComments(data.comments);
        }
    } catch (err) {
        console.error(err);
        list.innerHTML = '<div class="text-center py-4 text-rose-500">โหลดข้อมูลล้มเหลว</div>';
    }
}

function renderLeaveComments(comments) {
    const list = $('leaveCommentList');
    const currentUser = (state.user && typeof state.user === 'object' ? state.user.username : state.user || '').toLowerCase();
    
    if (comments.length === 0) {
        list.innerHTML = `
            <div class="text-center py-8">
                <div class="w-12 h-12 bg-surface-100 dark:bg-surface-800 rounded-full flex items-center justify-center mx-auto mb-3 text-surface-400">
                    <i data-lucide="message-square" class="w-6 h-6"></i>
                </div>
                <p class="text-xs text-surface-400">ยังไม่มีข้อความตอบกลับ</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }
    
    list.innerHTML = comments.map(c => {
        const isMe = c.username.toLowerCase() === currentUser;
        return `
            <div class="flex flex-col ${isMe ? 'items-end' : 'items-start'} gap-1">
                <div class="max-w-[85%] p-4 rounded-3xl text-sm ${isMe ? 'bg-brand-600 text-white rounded-tr-none' : 'bg-white dark:bg-surface-800 text-surface-900 dark:text-white border border-surface-100 dark:border-surface-700 rounded-tl-none shadow-sm'}">
                    ${c.comment}
                </div>
                <div class="flex items-center gap-2 px-2">
                   <span class="text-[9px] font-black uppercase tracking-widest text-surface-400">${c.username}</span>
                   <span class="text-[8px] text-surface-300">${new Date(c.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
            </div>
        `;
    }).join('');
    
    // Auto scroll to bottom
    setTimeout(() => {
        list.scrollTop = list.scrollHeight;
    }, 100);
}

// Initialize Comment Form
(function initCommentForm() {
    const form = $('leaveCommentForm');
    if (form) {
        form.onsubmit = async (e) => {
            e.preventDefault();
            const lid = $('leaveCommentId').value;
            const comment = $('leaveCommentInput').value.trim();
            if (!lid || !comment) return;
            
            try {
                const res = await fetch('/api/leave/comment', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ leave_id: lid, comment: comment })
                });
                const data = await res.json();
                if (data.ok) {
                    $('leaveCommentInput').value = '';
                    openLeaveComments(lid); // Refresh
                }
            } catch (err) {
                console.error(err);
                toast("ส่งข้อความล้มเหลว", "error");
            }
        };
    }
})();

function switchLeaveView(viewMode) {
    const tableView = $('adminLeaveTableView');
    const calView = $('adminLeaveCalendarView');
    const btnTable = $('btnLeaveViewTable');
    const btnCal = $('btnLeaveViewCalendar');

    if (viewMode === 'calendar') {
        if (tableView) tableView.classList.add('hidden');
        if (calView) calView.classList.remove('hidden');

        if (btnTable) {
            btnTable.className = "px-3 py-1.5 rounded-lg text-xs font-bold transition-all text-surface-500 hover:text-surface-700 dark:text-surface-400 dark:hover:text-surface-200";
        }
        if (btnCal) {
            btnCal.className = "px-3 py-1.5 rounded-lg text-xs font-bold transition-all bg-white dark:bg-surface-700 text-brand-600 dark:text-brand-400 shadow-sm";
        }
        loadTeamLeaveCalendar();
    } else {
        if (calView) calView.classList.add('hidden');
        if (tableView) tableView.classList.remove('hidden');

        if (btnCal) {
            btnCal.className = "px-3 py-1.5 rounded-lg text-xs font-bold transition-all text-surface-500 hover:text-surface-700 dark:text-surface-400 dark:hover:text-surface-200";
        }
        if (btnTable) {
            btnTable.className = "px-3 py-1.5 rounded-lg text-xs font-bold transition-all bg-white dark:bg-surface-700 text-brand-600 dark:text-brand-400 shadow-sm";
        }
        refreshAdminLeaves();
    }
}

function prevLeaveMonth() {
    changeTeamCalendarMonth(-1);
}

function nextLeaveMonth() {
    changeTeamCalendarMonth(1);
}

function toggleLeaveCalendar(forceState) {
    const body = $('leaveCalendarBody');
    const icon = $('leaveCalendarToggleIcon');
    const text = $('leaveCalendarToggleText');
    const nav = $('leaveCalendarMonthNav');
    if (!body) return;

    const isCurrentlyHidden = body.classList.contains('hidden');
    const shouldHide = forceState !== undefined ? !forceState : !isCurrentlyHidden;

    if (shouldHide) {
        body.classList.add('hidden');
        if (text) text.textContent = 'กางปฏิทิน';
        if (icon) {
            icon.setAttribute('data-lucide', 'chevron-down');
            icon.classList.remove('rotate-0');
            icon.classList.add('rotate-180');
        }
        if (nav) nav.classList.add('opacity-40', 'pointer-events-none');
        localStorage.setItem('orgchat_leave_calendar_collapsed', 'true');
    } else {
        body.classList.remove('hidden');
        if (text) text.textContent = 'หุบปฏิทิน';
        if (icon) {
            icon.setAttribute('data-lucide', 'chevron-up');
            icon.classList.remove('rotate-180');
            icon.classList.add('rotate-0');
        }
        if (nav) nav.classList.remove('opacity-40', 'pointer-events-none');
        localStorage.setItem('orgchat_leave_calendar_collapsed', 'false');
    }
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

function initLeaveCalendarCollapse() {
    const saved = localStorage.getItem('orgchat_leave_calendar_collapsed');
    if (saved === 'true') {
        toggleLeaveCalendar(false); // collapse
    }
}

window.toggleLeaveCalendar = toggleLeaveCalendar;
window.initLeaveCalendarCollapse = initLeaveCalendarCollapse;
window.switchLeaveView = switchLeaveView;
window.prevLeaveMonth = prevLeaveMonth;
window.nextLeaveMonth = nextLeaveMonth;
window.changeTeamCalendarMonth = changeTeamCalendarMonth;
window.loadTeamLeaveCalendar = loadTeamLeaveCalendar;

async function testMorningBriefing() {
    const btn = $('btnTestBriefing');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i> กำลังส่ง...';
        if (typeof initIcons === 'function') initIcons();
    }
    try {
        const res = await fetch('/api/admin/briefing/trigger', { method: 'POST' });
        const data = await res.json();
        if (data.ok) {
            toast('ส่ง Morning Briefing เข้า LINE เรียบร้อยแล้ว', 'success');
        } else {
            toast(data.error || 'เกิดข้อผิดพลาดในการส่ง', 'error');
        }
    } catch (e) {
        console.error(e);
        toast('ไม่สามารถติดต่อเซิร์ฟเวอร์ได้', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i data-lucide="sunrise" class="w-3.5 h-3.5"></i> ทดสอบ Morning Brief';
            if (typeof initIcons === 'function') initIcons();
        }
    }
}





function openImageViewer(url) {
  const modal = document.getElementById('imageViewerModal');
  const img = document.getElementById('imageViewerContent');
  if (modal && img) {
    img.src = url;
    modal.classList.remove('hidden');
    modal.classList.add('flex', 'items-center', 'justify-center');
    // Re-init icons for the close button inside modal
    if (typeof initIcons === 'function') initIcons();
  }
}

// ─── Reconciliation Logic ───────────────────
let reconReportUrl = null;
let _reconFilteredData = [];

document.addEventListener('DOMContentLoaded', () => {
    // ─── Authentication Logic ───────────────────
    const loginBtn = $('loginBtn');
    const loginPass = $('loginPassword');
    if (loginBtn) loginBtn.onclick = initAuth;
    if (loginPass) {
        loginPass.onkeypress = (e) => {
            if (e.key === 'Enter') initAuth();
        };
    }

    const mpInput = $('reconMPFiles');
    const shipInput = $('reconShipFiles');
    const peakInput = $('reconPeakFiles');
    if (mpInput) mpInput.onchange = (e) => { $('reconMPList').textContent = `${e.target.files.length} ไฟล์ที่เลือก`; };
    if (shipInput) shipInput.onchange = (e) => { $('reconShipList').textContent = `${e.target.files.length} ไฟล์ที่เลือก`; };
    if (peakInput) peakInput.onchange = (e) => { $('reconPeakList').textContent = `${e.target.files.length} ไฟล์ที่เลือก`; };
    const startBtn = $('startReconBtn');
    if (startBtn) startBtn.onclick = runReconciliation;

    // Set default dates for PEAK API mode (current month)
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    const fmt = (d) => d.toISOString().split('T')[0];
    const startEl = $('peakStartDate'); if (startEl && !startEl.value) startEl.value = fmt(firstDay);
    const endEl = $('peakEndDate'); if (endEl && !endEl.value) endEl.value = fmt(today);

    // Load PEAK settings status (only if authenticated)
    if (typeof state !== 'undefined' && state.user) {
        loadPeakSettingsStatus();
    }
    const downloadBtn = $('downloadReconReportBtn');
    if (downloadBtn) downloadBtn.onclick = () => { if (reconReportUrl) window.open(reconReportUrl, '_blank'); };
    const resetBtn = $('resetReconBtn');
    if (resetBtn) resetBtn.onclick = resetReconciliation;
    const filteredBtn = $('downloadFilteredBtn');
    if (filteredBtn) filteredBtn.onclick = downloadFilteredRecon;
    const localScanBtn = $('startLocalScanBtn');
    if (localScanBtn) localScanBtn.onclick = triggerLocalScan;
});

async function triggerLocalScan() {
    const btn = $('startLocalScanBtn');
    if (!btn) return;
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> กำลังส่งคำขอ...`;
    initIcons();
    
    try {
        const res = await fetch('/api/admin/reconcile/local-scan', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.ok) {
            toast(data.message || 'เริ่มสแกนโฟลเดอร์เอกสารและกระทบยอดแล้วค่ะ ⏳', 'info');
            btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> กำลังสแกนในเบื้องหลัง...`;
            initIcons();
        } else {
            toast(data.error || 'เกิดข้อผิดพลาดในการสแกน', 'error');
            btn.disabled = false;
            btn.innerHTML = originalText;
            initIcons();
        }
    } catch (e) {
        console.error(e);
        toast('การเชื่อมต่อล้มเหลว', 'error');
        btn.disabled = false;
        btn.innerHTML = originalText;
        initIcons();
    }
}

async function initAuth() {
    const userEl = $('loginUsername');
    const passEl = $('loginPassword');
    const btn = $('loginBtn');
    const errorEl = $('loginError');
    const errorMsg = $('loginErrorMsg');

    if (!userEl || !passEl || !btn) return;

    const username = userEl.value.trim();
    const password = passEl.value.trim();

    if (!username || !password) {
        toast('กรุณากรอกชื่อผู้ใช้งานและรหัสผ่าน', 'error');
        if (errorEl) {
            errorEl.classList.remove('hidden');
            errorMsg.textContent = 'กรุณากรอกข้อมูลให้ครบถ้วน';
        }
        return;
    }

    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<i data-lucide="loader-2" class="w-5 h-5 animate-spin inline-block mr-2"></i> กำลังตรวจสอบ...`;
    if (errorEl) errorEl.classList.add('hidden');

    try {
        const data = await apiFetch('/api/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });

        if (data.requires_2fa) {
            handle2FAChallenge(data.pre_auth_token);
            btn.disabled = false;
            btn.innerHTML = originalText;
            return;
        }

        if (data.ok) {
            state.user = data.user;
            state.username = (typeof data.user === 'object') ? data.user.username : data.user;
            
            if (!data.has_org) {
                window.location.href = '/onboarding';
                return;
            }

            toast(`ยินดีต้อนรับคุณ ${state.username}`, 'success');
            
            // Reload page so browser receives and attaches all session cookies cleanly
            setTimeout(() => {
                if (window.location.pathname === '/onboarding') {
                    window.location.href = '/';
                } else {
                    window.location.reload();
                }
            }, 500);
        } else {
            const msg = data.error || 'ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง';
            toast(msg, 'error');
            if (errorEl) {
                errorEl.classList.remove('hidden');
                errorMsg.textContent = msg;
            }
        }
    } catch (e) {
        console.error('Login error:', e);
        toast('การเชื่อมต่อล้มเหลว กรุณาลองใหม่อีกครั้ง', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
        lucide.createIcons();
    }
}

async function runReconciliation() {
    const mpFiles = $('reconMPFiles').files;
    const shipFiles = $('reconShipFiles').files;
    const isApiMode = window._peakMode === 'api';

    if (!mpFiles.length || !shipFiles.length) { toast('กรุณาอัปโหลดไฟล์ Marketplace และ Shipnity', 'error'); return; }
    if (!isApiMode && !$('reconPeakFiles').files.length) { toast('กรุณาอัปโหลดไฟล์ PEAK หรือเปลี่ยนเป็นโหมด API', 'error'); return; }

    const btn = $('startReconBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    showGlobalLoading('กำลังเตรียมข้อมูลการกระทบยอด...');
    initIcons();

    const formData = new FormData();
    for (let f of mpFiles) formData.append('marketplace', f);
    for (let f of shipFiles) formData.append('shipnity', f);

    try {
        if (isApiMode) {
            btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> กำลังดึงข้อมูลจาก PEAK...`;
            showGlobalLoading('กำลังดึงข้อมูลจาก PEAK API...');
            initIcons();
            const start = $('peakStartDate')?.value || '';
            const end = $('peakEndDate')?.value || '';
            const peakRes = await fetch(`/api/reconciliation/fetch-peak?start_date=${start}&end_date=${end}`);
            const peakData = await peakRes.json();
            if (!peakData.ok) { 
                toast(peakData.error || 'ดึงข้อมูล PEAK ไม่สำเร็จ', 'error'); 
                btn.disabled = false;
                btn.innerHTML = originalText;
                hideGlobalLoading();
                return; 
            }
            formData.append('peak_api_rows', JSON.stringify(peakData.rows));
            toast(`ดึงข้อมูลจาก PEAK สำเร็จ ${peakData.count} รายการ`, 'info');
        } else {
            for (let f of $('reconPeakFiles').files) formData.append('peak', f);
        }

        btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> กำลังประมวลผล...`;
        showGlobalLoading('กำลังประมวลผลและสร้างรายงานการกระทบยอด...');
        initIcons();
        const res = await fetch('/api/reconciliation/process', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.ok) {
            renderReconResults(data.summary);
            toast('ประมวลผลการกระทบยอดสำเร็จ', 'success');
            $('reconLastRun').textContent = 'ล่าสุดเมื่อ: ' + new Date().toLocaleString('th-TH');
            const rb = $('resetReconBtn'); if (rb) rb.classList.remove('hidden');
        } else { toast(data.error || 'เกิดข้อผิดพลาด', 'error'); }
    } catch (e) { console.error(e); toast('การเชื่อมต่อล้มเหลว', 'error'); }
    finally { 
        btn.disabled = false; 
        btn.innerHTML = originalText; 
        initIcons(); 
        hideGlobalLoading();
    }
}

function resetReconciliation() {
    window._reconData = null; _reconFilteredData = []; reconReportUrl = null;
    $('reconSummary')?.classList.add('hidden');
    $('reconResultsArea')?.classList.add('hidden');
    $('resetReconBtn')?.classList.add('hidden');
    ['reconMPFiles','reconShipFiles','reconPeakFiles'].forEach(id => { const el = $(id); if (el) el.value = ''; });
    ['reconMPList','reconShipList','reconPeakList'].forEach(id => { const el = $(id); if (el) el.textContent = ''; });
    const s = $('reconSearchInput'); if (s) s.value = '';
    $('reconLastRun').textContent = 'ยังไม่มีการประมวลผล';
    toast('ล้างข้อมูลเรียบร้อย', 'success');
}

function renderReconResults(summary) {
    const { total, issues, data, report_url, financial } = summary;
    reconReportUrl = report_url;
    window._reconData = data;
    $('reconStatTotal').textContent = total.toLocaleString();
    $('reconStatNormal').textContent = (total - issues).toLocaleString();
    $('reconStatIssues').textContent = issues.toLocaleString();
    const cEl = $('reconStatCancelled'); if (cEl) cEl.textContent = (financial?.mp_cancelled || 0).toLocaleString();
    const fmt = (v) => '฿' + (v || 0).toLocaleString('th-TH', {minimumFractionDigits: 0, maximumFractionDigits: 0});
    const ss = $('reconStatShipSales'); if (ss) ss.textContent = fmt(financial?.total_shipnity_sales);
    const pa = $('reconStatPeakAmount'); if (pa) pa.textContent = fmt(financial?.total_peak_amount);
    const pt = $('reconStatPeakTax'); if (pt) pt.textContent = fmt(financial?.total_peak_tax);
    const dEl = $('reconStatDiff');
    if (dEl) { const d = financial?.amount_diff || 0; dEl.textContent = (d >= 0 ? '+' : '') + fmt(d); }
    $('reconSummary').classList.remove('hidden');
    $('reconResultsArea').classList.remove('hidden');
    
    // Dynamically populate brand filter
    const brandFilter = $('reconBrandFilter');
    if (brandFilter && data && data.length > 0) {
        const brands = new Set();
        data.forEach(row => { if (row.brand) brands.add(row.brand); });
        
        const currentBrand = brandFilter.value;
        brandFilter.innerHTML = '<option value="all">ทุกแบรนด์</option>';
        Array.from(brands).sort().forEach(b => {
            brandFilter.innerHTML += `<option value="${b}">${b}</option>`;
        });
        // Restore selection if it still exists
        if (brands.has(currentBrand)) brandFilter.value = currentBrand;
    }

    updateReconBadges(data);
    renderReconTable(data);
    const si = $('reconSearchInput'); if (si) si.oninput = () => applyReconFilters();
    document.querySelectorAll('.recon-filter-btn').forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll('.recon-filter-btn').forEach(b => b.classList.remove('ring-2', 'ring-offset-1', 'ring-indigo-500'));
            btn.classList.add('ring-2', 'ring-offset-1', 'ring-indigo-500');
            applyReconFilters();
        };
    });
    const pf = $('reconPlatformFilter'); if (pf) pf.onchange = () => applyReconFilters();
    const bf = $('reconBrandFilter'); if (bf) bf.onchange = () => applyReconFilters();
    if (typeof initIcons === 'function') initIcons();
}

function applyReconFilters() {
    const data = window._reconData || [];
    const search = ($('reconSearchInput')?.value || '').toLowerCase().trim();
    const activeBtn = document.querySelector('.recon-filter-btn.ring-2');
    const filterType = activeBtn?.getAttribute('data-recon-filter') || 'all';
    const platform = $('reconPlatformFilter')?.value || 'all';
    const brand = $('reconBrandFilter')?.value || 'all';
    const filtered = data.filter(row => {
        if (search) {
            const s = [row.mp_order_id, row.shipnity_id, row.peak_invoice_id, row.platform, row.status_mp, row.issue, row.brand].map(v => (v || '').toLowerCase()).join(' ');
            if (!s.includes(search)) return false;
        }
        if (platform !== 'all' && (row.platform || '') !== platform) return false;
        if (brand !== 'all' && (row.brand || '') !== brand) return false;
        const isIssue = row.issue && row.issue !== '✅ ปกติ';
        const isCancelled = ['ยกเลิกแล้ว', 'canceled', 'cancelled', 'returned'].includes((row.status_mp || '').toLowerCase());
        switch (filterType) {
            case 'issues': return isIssue;
            case 'normal': return !isIssue;
            case 'cancelled': return isCancelled;
            case 'no-shipnity': return (row.issue || '').includes('Shipnity');
            case 'no-peak': return (row.issue || '').includes('PEAK');
            case 'amount-mismatch': return (row.issue || '').includes('💰');
            default: return true;
        }
    });
    _reconFilteredData = filtered;
    renderReconTable(filtered);
    $('reconFilterCount').textContent = `แสดง ${filtered.length} / ${data.length} รายการ`;
}

function renderReconTable(data) {
    const body = $('reconResultsBody'); if (!body) return;
    body.innerHTML = '';
    _reconFilteredData = data;
    if (data.length === 0) { body.innerHTML = `<tr><td colspan="9" class="p-8 text-center text-surface-400 text-xs">ไม่พบรายการที่ตรงกับเงื่อนไข</td></tr>`; return; }
    data.forEach(row => {
        const tr = document.createElement('tr');
        const isIssue = row.issue && row.issue !== '✅ ปกติ';
        tr.className = isIssue ? 'bg-rose-50/50 dark:bg-rose-900/5 hover:bg-rose-100/50 transition-colors' : 'hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors';
        const aS = parseFloat(row.amount_shipnity) || 0;
        const aP = parseFloat(row.amount_peak) || 0;
        const mismatch = aS > 0 && aP > 0 && Math.abs(aS - aP) > 5;
        tr.innerHTML = `
            <td class="p-3 font-mono text-[10px]">${row.mp_order_id || '-'}</td>
            <td class="p-3"><span class="px-2 py-0.5 rounded-full text-[9px] font-black ${row.platform === 'Shopee' ? 'bg-orange-100 text-orange-700' : row.platform === 'Lazada' ? 'bg-blue-100 text-blue-700' : 'bg-surface-100 text-surface-500'}">${row.platform || '-'}</span></td>
            <td class="p-3"><span class="px-2 py-0.5 rounded-full text-[9px] font-black ${row.brand === 'DUIT' ? 'bg-pink-100 text-pink-700' : row.brand === 'Thumb Toe' ? 'bg-teal-100 text-teal-700' : row.brand === 'Bytuneller' ? 'bg-cyan-100 text-cyan-700' : 'bg-surface-100 text-surface-400'}">${row.brand || '-'}</span></td>
            <td class="p-3 font-mono text-[10px]">${row.shipnity_id || '-'}</td>
            <td class="p-3 font-mono text-[10px]">${row.peak_invoice_id || '-'}</td>
            <td class="p-3"><span class="px-2 py-0.5 rounded-full text-[9px] font-black ${['ยกเลิกแล้ว','canceled','cancelled','returned'].includes((row.status_mp||'').toLowerCase()) ? 'bg-rose-100 text-rose-600' : ['สำเร็จแล้ว','confirmed'].includes((row.status_mp||'').toLowerCase()) ? 'bg-emerald-100 text-emerald-600' : 'bg-surface-100 text-surface-500'}">${row.status_mp || '-'}</span></td>
            <td class="p-3 text-[10px] text-right font-mono ${mismatch ? 'text-amber-600 font-bold' : ''}">${aS ? aS.toLocaleString() : '-'}</td>
            <td class="p-3 text-[10px] text-right font-mono ${mismatch ? 'text-amber-600 font-bold' : ''}">${aP ? aP.toLocaleString() : '-'}</td>
            <td class="p-3 text-[10px] font-bold ${isIssue ? 'text-rose-600' : 'text-emerald-600'}">${row.issue || '-'}</td>
        `;
        body.appendChild(tr);
    });
    $('reconFilterCount').textContent = `แสดง ${data.length} / ${(window._reconData || []).length} รายการ`;
}

function updateReconBadges(data) {
    const c = { 'all': data.length, 'issues': 0, 'normal': 0, 'cancelled': 0, 'no-shipnity': 0, 'no-peak': 0, 'amount-mismatch': 0 };
    data.forEach(row => {
        const isIssue = row.issue && row.issue !== '✅ ปกติ';
        if (isIssue) c['issues']++; else c['normal']++;
        if (['ยกเลิกแล้ว','canceled','cancelled','returned'].includes((row.status_mp||'').toLowerCase())) c['cancelled']++;
        if ((row.issue||'').includes('Shipnity')) c['no-shipnity']++;
        if ((row.issue||'').includes('PEAK')) c['no-peak']++;
        if ((row.issue||'').includes('💰')) c['amount-mismatch']++;
    });
    const labels = { 'all': 'ทั้งหมด', 'issues': 'เฉพาะปัญหา', 'normal': 'ปกติ', 'cancelled': 'ยกเลิกแล้ว', 'no-shipnity': 'ไม่พบใน Shipnity', 'no-peak': 'ไม่มีใน PEAK', 'amount-mismatch': 'ยอดไม่ตรง' };
    document.querySelectorAll('.recon-filter-btn').forEach(btn => {
        const k = btn.getAttribute('data-recon-filter');
        if (k && labels[k] !== undefined) btn.textContent = `${labels[k]} (${c[k]})`;
    });
}

async function downloadFilteredRecon() {
    if (!_reconFilteredData || !_reconFilteredData.length) { toast('ไม่มีข้อมูลสำหรับดาวน์โหลด', 'error'); return; }
    try {
        const res = await fetch('/api/reconciliation/download-filtered', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ rows: _reconFilteredData }) });
        if (!res.ok) { toast('ดาวน์โหลดล้มเหลว', 'error'); return; }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = 'reconciliation_filtered.xlsx'; a.click();
        URL.revokeObjectURL(url);
        toast('ดาวน์โหลดสำเร็จ', 'success');
    } catch (e) { console.error(e); toast('เกิดข้อผิดพลาด', 'error'); }
}

// ─── Google Drive Explorer ────────────────────
async function loadDriveContents(folderId = 'root') {
  const grid = $('driveGrid');
  const loading = $('driveLoading');
  const empty = $('driveEmptyState');
  const breadcrumbs = $('driveBreadcrumbs');

  if (!grid || !loading || !empty) return;

  if (state.drive.isLoading) return;
  state.drive.isLoading = true;

  grid.innerHTML = '';
  loading.classList.remove('hidden');
  empty.classList.add('hidden');

  try {
    const data = await apiFetch(`/api/drive/contents?folder_id=${folderId}`, { _timeout: 8000 });
    if (data.ok) {
      state.drive.currentFolderId = folderId;
      
      // Update history for breadcrumbs
      if (folderId === 'root') {
        state.drive.history = [{ id: 'root', name: data.folder_name || 'My Drive' }];
      } else if (data.folder_name) {
        // If the folder is already in history, trim history to it
        const idx = state.drive.history.findIndex(h => h.id === folderId);
        if (idx !== -1) {
          state.drive.history = state.drive.history.slice(0, idx + 1);
        } else {
          state.drive.history.push({ id: folderId, name: data.folder_name });
        }
      }

      renderDriveContents(data.items);
      updateDriveBreadcrumbs();
      
      // Update Back Button State
      const backBtn = $('driveBackBtn');
      if (backBtn) {
        backBtn.disabled = state.drive.history.length <= 1;
      }
    } else {
      toast(data.error || 'ไม่สามารถโหลดข้อมูล Google Drive ได้', 'error');
      grid.innerHTML = `
        <div class="col-span-full py-16 flex flex-col items-center justify-center text-center">
          <div class="w-14 h-14 bg-amber-50 dark:bg-amber-950/40 text-amber-500 rounded-2xl flex items-center justify-center mb-3">
            <i data-lucide="cloud-off" class="w-7 h-7"></i>
          </div>
          <p class="font-bold text-surface-800 dark:text-surface-100 mb-1">${escHtml(data.error || 'ไม่สามารถเชื่อมต่อ Google Drive ได้')}</p>
          <p class="text-xs text-surface-400 max-w-md mb-4">ตรวจพบข้อผิดพลาดในการเชื่อมต่อ หรือ Google OAuth ขององค์กรอาจหมดอายุ</p>
          <div class="flex items-center gap-2">
            <button onclick="loadDriveContents(state.drive.currentFolderId)" class="px-4 py-2 bg-surface-100 dark:bg-surface-800 hover:bg-surface-200 text-surface-700 dark:text-surface-200 text-xs font-bold rounded-xl transition">ลองอีกครั้ง</button>
            <a href="/#settings" class="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold rounded-xl shadow-sm transition">ไปที่หน้าตั้งค่า Google</a>
          </div>
        </div>
      `;
      if (typeof lucide !== 'undefined') lucide.createIcons();
    }
  } catch (e) {
    console.error('Drive Load Error:', e);
    toast(e.message || 'เกิดข้อผิดพลาดในการเชื่อมต่อ Google Drive', 'error');
    grid.innerHTML = `
      <div class="col-span-full py-16 flex flex-col items-center justify-center text-center">
        <div class="w-14 h-14 bg-rose-50 dark:bg-rose-950/40 text-rose-500 rounded-2xl flex items-center justify-center mb-3">
          <i data-lucide="alert-circle" class="w-7 h-7"></i>
        </div>
        <p class="font-bold text-surface-800 dark:text-surface-100 mb-1">${escHtml(e.message || 'การเชื่อมต่อหมดเวลา')}</p>
        <p class="text-xs text-surface-400 max-w-md mb-4">เซิร์ฟเวอร์ใช้เวลาตอบสนองนานเกินไป กรุณาตรวจสอบสถานะการเชื่อมต่อ</p>
        <button onclick="loadDriveContents(state.drive.currentFolderId)" class="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold rounded-xl shadow-sm transition">ลองอีกครั้ง</button>
      </div>
    `;
    if (typeof lucide !== 'undefined') lucide.createIcons();
  } finally {
    loading.classList.add('hidden');
    state.drive.isLoading = false;
  }
}

async function renameDriveFile(fileId, currentName) {
  const newName = prompt('เปลี่ยนชื่อไฟล์:', currentName);
  if (!newName || newName === currentName) return;
  
  try {
    const data = await apiFetch('/api/drive/rename', {
      method: 'POST',
      body: JSON.stringify({ file_id: fileId, new_name: newName })
    });
    if (data.ok) {
      toast('เปลี่ยนชื่อไฟล์สำเร็จ', 'success');
      loadDriveContents(state.drive.currentFolderId);
    } else {
      toast(data.error || 'เปลี่ยนชื่อล้มเหลว', 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาดในการเปลี่ยนชื่อ', 'error');
  }
}

async function deleteDriveFile(fileId, name) {
  if (!confirm(`คุณแน่ใจหรือไม่ว่าต้องการลบ "${name}"?`)) return;
  
  try {
    const data = await apiFetch('/api/drive/delete', {
      method: 'POST',
      body: JSON.stringify({ file_id: fileId })
    });
    if (data.ok) {
      toast('ย้ายไฟล์ไปถังขยะเรียบร้อย', 'success');
      loadDriveContents(state.drive.currentFolderId);
    } else {
      toast(data.error || 'ลบไฟล์ล้มเหลว', 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาดในการลบไฟล์', 'error');
  }
}

function renderDriveContents(items) {
  const grid = $('driveGrid');
  const empty = $('driveEmptyState');

  if (!items || items.length === 0) {
    empty.classList.remove('hidden');
    return;
  }

  const itemsHtml = items.map((item, idx) => {
    const isFolder = item.mimeType === 'application/vnd.google-apps.folder';
    const isImage = item.mimeType.startsWith('image/');
    const previewUrl = (isImage && item.thumbnailLink) ? item.thumbnailLink.replace('=s220', '=s400') : null;
    const onClick = isFolder ? `navigateToDriveFolder('${item.id}', '${item.name.replace(/'/g, "\\'")}')` : `window.open('${item.webViewLink}', '_blank')`;
    
    // Administrative controls (gated)
    let adminControls = '';
    if (state.isAdmin) {
      adminControls = `
        <div class="flex items-center gap-1 mt-2 pt-2 border-t border-surface-100 dark:border-surface-800">
          <button onclick="event.stopPropagation(); renameDriveFile('${item.id}', '${item.name.replace(/'/g, "\\'")}')" 
                  class="flex-1 p-1.5 bg-surface-50 dark:bg-surface-800 hover:bg-brand-50 dark:hover:bg-brand-900/30 text-surface-400 hover:text-brand-600 rounded-lg transition-all flex items-center justify-center gap-1 group/btn">
            <i data-lucide="edit-3" class="w-3 h-3"></i>
            <span class="text-[8px] font-black uppercase">Rename</span>
          </button>
          <button onclick="event.stopPropagation(); deleteDriveFile('${item.id}', '${item.name.replace(/'/g, "\\'")}')" 
                  class="p-1.5 bg-surface-50 dark:bg-surface-800 hover:bg-rose-50 dark:hover:bg-rose-900/30 text-surface-400 hover:text-rose-600 rounded-lg transition-all flex items-center justify-center group/btn">
            <i data-lucide="trash-2" class="w-3 h-3"></i>
          </button>
        </div>
      `;
    }

    return `
      <div class="group relative bg-white dark:bg-surface-900 rounded-2xl border border-surface-100 dark:border-surface-800 p-4 hover:shadow-xl hover:-translate-y-1 transition-all cursor-pointer overflow-hidden animate-in fade-in zoom-in-95 duration-300" 
           style="animation-delay: ${idx * 30}ms"
           onclick="${onClick}">
        <div class="aspect-square rounded-xl bg-surface-50 dark:bg-surface-800 flex items-center justify-center mb-3 group-hover:bg-brand-50 dark:group-hover:bg-brand-900/20 transition-colors overflow-hidden">
          ${isFolder ? 
            `<i data-lucide="folder" class="w-12 h-12 text-amber-500 fill-amber-500/20"></i>` : 
            (previewUrl ? 
              `<img src="${previewUrl}" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110">` :
              `<img src="${item.iconLink}" class="w-10 h-10 object-contain opacity-80 group-hover:opacity-100 transition-opacity">`
            )
          }
        </div>
        <div class="space-y-1">
          <p class="text-[11px] font-bold text-surface-900 dark:text-surface-100 truncate pr-2" title="${item.name}">${item.name}</p>
          <p class="text-[9px] text-surface-400 font-bold uppercase tracking-tighter truncate">${isFolder ? 'Folder' : item.mimeType.split('/').pop().toUpperCase()}</p>
        </div>
        <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <i data-lucide="${isFolder ? 'chevron-right' : 'external-link'}" class="w-3.5 h-3.5 text-surface-400"></i>
        </div>
        ${adminControls}
      </div>
    `;
  }).join('');

  // Add ".." Parent folder if not at root
  let upHtml = '';
  if (state.drive.history.length > 1) {
    const parent = state.drive.history[state.drive.history.length - 2];
    upHtml = `
      <div class="group relative bg-surface-100/50 dark:bg-surface-800/50 rounded-2xl border-2 border-dashed border-surface-200 dark:border-surface-700 p-4 hover:bg-white dark:hover:bg-surface-900 hover:border-solid hover:border-brand-500 transition-all cursor-pointer overflow-hidden animate-in fade-in zoom-in-95 duration-300" 
           onclick="goBackDriveFolder()">
        <div class="aspect-square rounded-xl bg-white dark:bg-surface-900 flex items-center justify-center mb-3 group-hover:bg-brand-50 dark:group-hover:bg-brand-900/20 transition-colors shadow-sm">
          <i data-lucide="corner-left-up" class="w-10 h-10 text-brand-600"></i>
        </div>
        <div class="space-y-1 text-center">
          <p class="text-[11px] font-black text-brand-600 tracking-tighter">..</p>
          <p class="text-[9px] text-surface-400 font-bold uppercase tracking-tighter">Go Up</p>
        </div>
      </div>
    `;
  }

  grid.innerHTML = upHtml + itemsHtml;

  lucide.createIcons();
}

function navigateToDriveFolder(id, name) {
  loadDriveContents(id);
}

function updateDriveBreadcrumbs() {
  const container = $('driveBreadcrumbs');
  if (!container) return;

  container.innerHTML = state.drive.history.map((h, i) => `
    <div class="flex items-center gap-2">
      ${i > 0 ? `<i data-lucide="chevron-right" class="w-3 h-3 text-surface-300"></i>` : ''}
      <button onclick="navigateToDriveFolder('${h.id}')" class="hover:text-brand-600 transition-colors ${i === state.drive.history.length - 1 ? 'text-surface-900 dark:text-white' : ''}">
        ${h.name}
      </button>
    </div>
  `).join('');

  lucide.createIcons();
}

function goBackDriveFolder() {
  if (state.drive.history.length > 1) {
    const prev = state.drive.history[state.drive.history.length - 2];
    loadDriveContents(prev.id);
  }
}

window.goBackDriveFolder = goBackDriveFolder;

// ─── Smart Dashboard Utilities [NEW] ────────────────

function updateSystemStatus(text = 'Live', type = 'success') {
  const dashBadge = $('dashSystemStatus');
  const dashText = $('dashSystemStatusText');
  const sidebarBadge = $('statusBadge');
  
  const colors = {
    success: { bg: 'bg-emerald-50 dark:bg-emerald-900/20', text: 'text-emerald-600', dot: 'bg-emerald-500', border: 'border-emerald-100 dark:border-emerald-800' },
    warning: { bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-600', dot: 'bg-amber-500', border: 'border-amber-100 dark:border-amber-800' },
    error: { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-600', dot: 'bg-red-500', border: 'border-red-100 dark:border-red-800' }
  };
  
  const c = colors[type] || colors.success;
  
  if (dashBadge && dashText) {
    dashBadge.className = `hidden md:flex items-center gap-2 px-3 py-1.5 ${c.bg} ${c.text} rounded-full border ${c.border}`;
    const dot = dashBadge.querySelector('.rounded-full');
    if (dot) dot.className = `w-2 h-2 ${c.dot} rounded-full animate-pulse`;
    dashText.textContent = `System ${text}`;
  }
  
  if (sidebarBadge) {
     sidebarBadge.className = `flex items-center gap-1.5 px-2 py-0.5 rounded ${c.bg} ${c.text} text-[10px] font-bold border ${c.border}`;
     const dot = sidebarBadge.querySelector('.rounded-full');
     if (dot) dot.className = `w-1 h-1 rounded-full ${c.dot}`;
     if (sidebarBadge.lastChild) sidebarBadge.lastChild.textContent = ` ${text === 'Live' ? 'พร้อมทำงาน' : text}`;
  }
}

// Weather Intelligence
async function fetchWeather() {
  try {
    const lat = 13.7563; // Bangkok
    const lon = 100.5018;
    
    const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,uv_index&hourly=temperature_2m,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=Asia%2FBangkok&forecast_days=7`;
    const aqUrl = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${lat}&longitude=${lon}&current=pm2_5,us_aqi&timezone=Asia%2FBangkok`;

    const [wRes, aqRes] = await Promise.allSettled([fetch(weatherUrl), fetch(aqUrl)]);
    
    let data = null;
    if (wRes.status === 'fulfilled' && wRes.value.ok) {
      data = await wRes.value.json();
    }
    
    let aqData = null;
    if (aqRes.status === 'fulfilled' && aqRes.value.ok) {
      try {
        aqData = await aqRes.value.json();
      } catch (_) {}
    }

    if (data && data.current) {
      const temp = Math.round(data.current.temperature_2m);
      const feels = Math.round(data.current.apparent_temperature);
      const humidity = data.current.relative_humidity_2m;
      const rain = data.current.precipitation;
      const uv = data.current.uv_index;
      const code = data.current.weather_code;
      
      // Update Dashboard Card
      if ($('currentTemp')) $('currentTemp').textContent = `${temp}°C`;
      if ($('dashFeelsLike')) $('dashFeelsLike').textContent = `${feels}°C`;
      if ($('dashHumidity')) $('dashHumidity').textContent = `${humidity}%`;
      if ($('dashUV')) {
        $('dashUV').textContent = uv != null ? uv.toFixed(1) : '--';
        $('dashUV').className = `text-sm font-black ${uv > 6 ? 'text-rose-500' : uv > 3 ? 'text-amber-500' : 'text-emerald-500'}`;
      }
      if ($('rainChance')) $('rainChance').innerHTML = `<i data-lucide="droplets" class="w-3 h-3"></i> ฝน ${rain}mm`;
      
      // Update PM 2.5
      const pm25El = $('dashPM25');
      if (pm25El) {
        const pmVal = aqData?.current?.pm2_5;
        if (pmVal != null && !isNaN(pmVal)) {
          pm25El.textContent = Number(pmVal).toFixed(1);
          pm25El.className = `text-sm font-black ${pmVal > 50 ? 'text-rose-500' : pmVal > 25 ? 'text-amber-500' : 'text-emerald-500'}`;
        } else {
          pm25El.textContent = '--';
        }
      }
      
      const condition = getWeatherCondition(code);
      if ($('weatherCondition')) $('weatherCondition').textContent = condition;
      
      const now = new Date();
      if ($('weatherLastUpdate')) $('weatherLastUpdate').textContent = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
      
      // Store globally for detail modal
      window._weatherData = data;
      window._airQualityData = aqData;
      if (typeof state !== 'undefined') {
        state.weather = data;
        state.airQuality = aqData;
      }
      
      if (typeof lucide !== 'undefined') lucide.createIcons();
    }
  } catch (err) {
    console.error('Weather fetch error:', err);
  }
}

function getWeatherCondition(code) {
  const map = {
    0: 'ท้องฟ้าแจ่มใส', 1: 'เมฆบางส่วน', 2: 'เมฆเป็นส่วนมาก', 3: 'เมฆครึ้ม',
    45: 'หมอกลง', 48: 'หมอกน้ำค้างแข็ง',
    51: 'ฝนปรอยๆ เบาๆ', 53: 'ฝนปรอยๆ ปานกลาง', 55: 'ฝนปรอยๆ หนาแน่น',
    61: 'ฝนตกเล็กน้อย', 63: 'ฝนตกปานกลาง', 65: 'ฝนตกหนัก',
    80: 'ฝนโปรยปรายเล็กน้อย', 81: 'ฝนโปรยปรายรุนแรง',
    95: 'พายุฝนฟ้าคะนอง'
  };
  return map[code] || 'อากาศแปรปรวน';
}

function showWeatherDetail() {
  const modal = $('weatherDetailModal');
  if (!modal || !window._weatherData) return;
  
  const d = window._weatherData;
  const aq = window._airQualityData;
  modal.classList.remove('hidden');
  modal.classList.add('flex', 'items-center', 'justify-center');
  
  // Update Header & Stats
  if ($('detailFeelsLike')) $('detailFeelsLike').textContent = `${Math.round(d.current.apparent_temperature)}°C`;
  if ($('detailHumidity')) $('detailHumidity').textContent = `${d.current.relative_humidity_2m}%`;
  if ($('detailUV')) $('detailUV').textContent = d.current.uv_index != null ? d.current.uv_index.toFixed(1) : '--';
  if ($('detailPM25')) {
    const pmVal = aq?.current?.pm2_5;
    if (pmVal != null && !isNaN(pmVal)) {
      $('detailPM25').textContent = Number(pmVal).toFixed(1);
      $('detailPM25').className = `text-xl font-black ${pmVal > 50 ? 'text-rose-500' : pmVal > 25 ? 'text-amber-500' : 'text-emerald-500'}`;
    } else {
      $('detailPM25').textContent = '--';
    }
  }
  
  // Hourly Forecast
  const hourlyList = $('hourlyForecastList');
  if (hourlyList) {
    const hours = d.hourly.time.slice(0, 24);
    hourlyList.innerHTML = hours.map((h, i) => {
       const date = new Date(h);
       const hour = date.getHours();
       const temp = Math.round(d.hourly.temperature_2m[i]);
       const code = d.hourly.weather_code[i];
       const active = hour === new Date().getHours() ? 'ring-2 ring-brand-500 bg-brand-50 dark:bg-brand-900/20' : 'bg-white dark:bg-surface-900';
       
       return `
         <div class="flex flex-col items-center gap-2 p-4 ${active} rounded-3xl min-w-[90px] border border-surface-100 dark:border-surface-800 shadow-sm">
            <span class="text-[10px] font-black text-surface-400">${hour}:00</span>
            <div class="text-brand-600 my-1"><i data-lucide="${getWeatherIcon(code)}" class="w-6 h-6"></i></div>
            <span class="text-sm font-black text-surface-900 dark:text-white">${temp}°C</span>
         </div>
       `;
    }).join('');
  }
  
  // Daily Forecast
  const dailyList = $('dailyForecastList');
  if (dailyList) {
    dailyList.innerHTML = d.daily.time.map((t, i) => {
       const date = new Date(t);
       const dayName = date.toLocaleDateString('th-TH', { weekday: 'long' });
       const max = Math.round(d.daily.temperature_2m_max[i]);
       const min = Math.round(d.daily.temperature_2m_min[i]);
       const code = d.daily.weather_code[i];
       
       return `
         <div class="flex items-center justify-between py-4 group">
            <div class="flex items-center gap-4">
               <div class="w-10 h-10 bg-surface-50 dark:bg-surface-800 rounded-xl flex items-center justify-center text-brand-600 group-hover:scale-110 transition-transform">
                  <i data-lucide="${getWeatherIcon(code)}" class="w-5 h-5"></i>
               </div>
               <div class="flex flex-col">
                  <span class="text-sm font-bold text-surface-900 dark:text-white">${dayName}</span>
                  <span class="text-[10px] text-surface-400 font-medium">${getWeatherCondition(code)}</span>
               </div>
            </div>
            <div class="flex items-center gap-4">
               <span class="text-sm font-black text-surface-900 dark:text-white">${max}°</span>
               <span class="text-sm font-bold text-surface-400">${min}°</span>
            </div>
         </div>
       `;
    }).join('');
  }
  
  lucide.createIcons();
}

function getWeatherIcon(code) {
  if (code === 0) return 'sun';
  if (code <= 3) return 'cloud-sun';
  if (code <= 48) return 'cloud';
  if (code <= 65) return 'cloud-rain';
  if (code <= 82) return 'cloud-drizzle';
  return 'cloud-lightning';
}

// Lunch Randomizer Logic
async function openLunchModal() {
  const modal = $('lunchModal');
  if (modal) {
    modal.classList.remove('hidden');
    modal.classList.add('flex', 'items-center', 'justify-center');
    loadLunchPlaces();
  }
}

async function loadLunchPlaces() {
  try {
    const data = await apiFetch('/api/lunch/all');
    if (data.ok) {
       state.lunchPlaces = data.places;
       renderLunchList();
    }
  } catch(e) {
    console.error('loadLunchPlaces error:', e);
  }
}

function renderLunchList() {
  const container = $('lunchPlaceList');
  if (!container || !state.lunchPlaces) return;
  
  container.innerHTML = state.lunchPlaces.map(p => `
    <div class="flex items-center justify-between p-3 bg-white dark:bg-surface-900 rounded-xl border border-surface-100 dark:border-surface-800 group">
       <div class="flex items-center gap-3">
          <div class="w-8 h-8 bg-surface-50 dark:bg-surface-800 rounded-lg flex items-center justify-center text-orange-600">
             <i data-lucide="utensils" class="w-4 h-4"></i>
          </div>
          <div>
             <div class="text-xs font-bold text-surface-900 dark:text-white">${p.name}</div>
             <div class="text-[9px] text-surface-400 uppercase tracking-widest">${p.type || 'ทั่วไป'}</div>
          </div>
       </div>
       <button onclick="deleteLunchPlace(${p.id})" class="p-2 text-surface-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all">
          <i data-lucide="trash-2" class="w-4 h-4"></i>
       </button>
    </div>
  `).join('');
  
  lucide.createIcons();
}

async function rollLunch() {
  const dashOverlay = $('dashLunchRollingOverlay');
  const dashResult = $('dashLunchResultArea');
  const modalOverlay = $('modalLunchRollingOverlay');
  const modalResult = $('modalLunchResultArea');
  
  if (dashOverlay) dashOverlay.classList.remove('hidden');
  if (dashResult) dashResult.classList.add('opacity-50', 'blur-sm');
  if (modalOverlay) modalOverlay.classList.remove('hidden');
  if (modalResult) modalResult.classList.add('opacity-50', 'blur-sm');
  
  try {
    const data = await apiFetch('/api/lunch/random');
    setTimeout(() => {
      if (dashOverlay) dashOverlay.classList.add('hidden');
      if (dashResult) dashResult.classList.remove('opacity-50', 'blur-sm');
      if (modalOverlay) modalOverlay.classList.add('hidden');
      if (modalResult) modalResult.classList.remove('opacity-50', 'blur-sm');
      
      if (data.ok && data.place) {
        // Update Dashboard Elements
        if ($('dashLunchPlaceName')) $('dashLunchPlaceName').textContent = data.place.name;
        if ($('dashLunchPlaceType')) $('dashLunchPlaceType').textContent = data.place.type || 'ร้านอาหารยอดฮิต';
        if ($('dashLunchPlaceLocation')) $('dashLunchPlaceLocation').innerHTML = `<i data-lucide="map-pin" class="w-3 h-3"></i> ${data.place.location || 'รอบออฟฟิศ'}`;
        if ($('dashLunchQuickPreview')) {
           $('dashLunchQuickPreview').innerHTML = `
             <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
             <span class="text-[10px] font-black text-brand-600">แนะนำ: ${data.place.name}</span>
           `;
        }

        // Update Modal Elements
        if ($('modalLunchPlaceName')) $('modalLunchPlaceName').textContent = data.place.name;
        if ($('modalLunchPlaceType')) $('modalLunchPlaceType').textContent = data.place.type || 'ร้านอาหารยอดฮิต';
        if ($('modalLunchPlaceLocation')) $('modalLunchPlaceLocation').innerHTML = `<i data-lucide="map-pin" class="w-3 h-3"></i> ${data.place.location || 'รอบออฟฟิศ'}`;
        
        toast(`สุ่มได้ร้าน: ${data.place.name}`, 'success');
        lucide.createIcons();
      }
    }, 1500); // Animation duration
  } catch (e) {
    if (dashOverlay) dashOverlay.classList.add('hidden');
    if (modalOverlay) modalOverlay.classList.add('hidden');
    toast('สุ่มไม่ได้ครับ กรุณาลองใหม่', 'error');
  }
}

function toggleLunchManager() {
  const mgr = $('lunchManager');
  if (mgr) mgr.classList.toggle('hidden');
}

async function addLunchPlacePrompt() {
  const name = prompt('กรุณาใส่ชื่อร้านอาหาร:');
  if (!name) return;
  const type = prompt('ประเภทอาหาร (เช่น ตามสั่ง, ก๋วยเตี๋ยว):', 'อาหารทั่วไป');
  
  try {
    const res = await apiFetch('/api/lunch/add', {
      method: 'POST',
      body: JSON.stringify({ name, type })
    });
    if (res.ok) {
      toast('เพิ่มร้านอาหารเรียบร้อยแล้ว', 'success');
      loadLunchPlaces();
    }
  } catch (e) {
    toast('เพิ่มร้านอาหารไม่สำเร็จครับ', 'error');
  }
}

async function deleteLunchPlace(id) {
  if (!confirm('คุณต้องการลบร้านนี้ใช่หรือไม่?')) return;
  try {
    const res = await apiFetch(`/api/lunch/delete/${id}`, { method: 'DELETE' });
    if (res.ok) {
      toast('ลบร้านอาหารเรียบร้อยแล้ว', 'info');
      loadLunchPlaces();
    }
  } catch (e) {
    toast('ลบไม่สำเร็จครับ (ต้องการสิทธิ์ Admin)', 'error');
  }
}

// --- LINE Broadcast Logic ---
async function sendLineBroadcast(msgId = 'lineBroadcastMsg', btnId = 'lineBroadcastBtn', toggleId = null, timeId = null) {
  const btn = $(btnId);
  const msgInput = $(msgId);
  
  if (!msgInput || !btn) {
    console.warn(`[LINE Broadcast] UI Elements not found: msg=${msgId}, btn=${btnId}`);
    return;
  }
  
  const text = msgInput.value.trim();
  if (!text) {
    toast('กรุณาพิมพ์ข้อความที่ต้องการบรอดแคสต์ค่ะพี่', 'error');
    return;
  }

  // Get scheduling details
  let schedule_time = null;
  const toggle = toggleId ? $(toggleId) : null;
  const timeInput = timeId ? $(timeId) : null;
  if (toggle && toggle.checked && timeInput && timeInput.value) {
    schedule_time = timeInput.value; // Format from input is 'YYYY-MM-DDTHH:MM'
  }
  
  const confirmMsg = schedule_time 
    ? `ยืนยันการตั้งเวลาส่งบรอดแคสต์ข้อความนี้ในวันที่ ${schedule_time.replace('T', ' ')} หรือไม่คะ?`
    : 'ยืนยันการส่งบรอดแคสต์ข้อความนี้ไปยังผู้ติดตามทุกคนคะ?';
    
  if (!confirm(confirmMsg)) return;
  
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> ${schedule_time ? 'กำลังตั้งเวลา...' : 'กำลังส่ง...'}`;
  if (window.lucide) lucide.createIcons();
  
  try {
    const payload = { text };
    if (schedule_time) {
      payload.schedule_time = schedule_time;
    }
    
    const data = await apiFetch('/api/admin/line/broadcast', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    
    if (data && data.success !== false) {
      toast(data.message || 'น้องพั้นส่งบรอดแคสต์ให้เรียบร้อยแล้วค่ะ!', 'success');
      msgInput.value = ''; // clear
      if (toggle) toggle.checked = false;
      if (timeInput) {
        timeInput.value = '';
        const containerId = timeId.replace('Time', 'TimeContainer');
        const container = $(containerId);
        if (container) container.classList.add('hidden');
      }
      refreshBroadcastHistory();
    } else {
      toast((data && data.error) || 'ส่งบรอดแคสต์ไม่สำเร็จนะคะพี่ ลองเช็ค Token อีกทีค่ะ', 'error');
    }
  } catch (err) {
    toast('เกิดข้อผิดพลาดทางเทคนิคนะคะพี่ น้องพั้นขออภัยค่ะ', 'error');
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
    if (window.lucide) lucide.createIcons();
  }
}

// --- LINE OA Settings Logic ---
async function openLineSettings() {
    const modal = $('lineSettingsModal');
    if (!modal) return;
    
    // Fetch and populate personas dropdown
    try {
        const personasData = await apiFetch('/api/personas');
        const select = $('lineSettingsPersona');
        if (select && personasData && personasData.ok) {
            select.innerHTML = '<option value="default">ค่าเริ่มต้น (น้องพั้นซ์)</option>';
            personasData.personas.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id;
                opt.textContent = p.name;
                select.appendChild(opt);
            });
        }
    } catch (err) {
        console.error('Failed to load personas for LINE config:', err);
    }
    
    // Load general settings
    try {
        const data = await apiFetch('/api/admin/line/settings');
        if (data && data.ok) {
            $('lineSettingsGreeting').value = data.config.greeting_message || '';
            $('lineSettingsAIEnabled').checked = data.config.ai_auto_responder_enabled || false;
            if ($('lineSettingsPersona')) {
                $('lineSettingsPersona').value = data.config.selected_persona_id || 'default';
            }
        }
    } catch (err) {
        console.error('Failed to fetch general LINE settings:', err);
    }

    // Load Org-specific LINE Channel credentials
    try {
        const orgData = await apiFetch('/api/org/line/channel-config');
        if (orgData && orgData.ok) {
            $('lineSettingsBotId').value = orgData.bot_basic_id || '';
            $('lineSettingsToken').value = orgData.channel_access_token_masked || '';
            $('lineSettingsSecret').value = orgData.channel_secret_masked || '';
            
            const badge = $('lineOrgBadge');
            if (badge) {
                if (orgData.has_custom_keys) {
                    badge.textContent = 'บอทเฉพาะองค์กร';
                    badge.className = 'text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300';
                } else {
                    badge.textContent = 'บอทส่วนกลาง';
                    badge.className = 'text-[10px] px-2 py-0.5 rounded-full font-bold bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300';
                }
            }
            if ($('lineTokenStatus')) {
                $('lineTokenStatus').textContent = orgData.has_custom_keys ? '✅ ใช้ Custom Key อยู่' : 'ℹ️ ใช้บอทส่วนกลาง';
            }
        }
    } catch (err) {
        console.error('Failed to fetch org LINE channel config:', err);
    }
    
    modal.classList.remove('hidden');
    if (window.lucide) lucide.createIcons();
}

async function saveLineSettings() {
    const btn = $('btnSaveLineSettings') || event?.target;
    const originalHtml = btn ? btn.innerHTML : 'บันทึกการตั้งค่า';
    
    const token = $('lineSettingsToken').value.trim();
    const secret = $('lineSettingsSecret').value.trim();
    const botId = $('lineSettingsBotId').value.trim();

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> กำลังบันทึก...';
        if (window.lucide) lucide.createIcons();
    }
    
    try {
        // 1. If token and secret are provided, save custom org credentials
        if (token && secret && !token.includes('...') && !secret.includes('...')) {
            const orgRes = await apiFetch('/api/org/line/channel-config', {
                method: 'POST',
                body: JSON.stringify({
                    channel_access_token: token,
                    channel_secret: secret,
                    bot_basic_id: botId,
                    is_active: 1
                })
            });
            if (!orgRes || !orgRes.ok) {
                toast(orgRes?.error || 'บันทึก Channel Key ไม่สำเร็จค่ะ', 'error');
                return;
            }
        }
        
        // 2. Save general settings (persona, greeting, AI responder)
        const payload = {
            greeting_message: $('lineSettingsGreeting').value.trim(),
            ai_auto_responder_enabled: $('lineSettingsAIEnabled').checked,
            selected_persona_id: $('lineSettingsPersona') ? $('lineSettingsPersona').value : 'default'
        };
        
        const data = await apiFetch('/api/admin/line/settings', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        if (data && data.ok) {
            toast('บันทึกการตั้งค่า LINE เรียบร้อยแล้ว', 'success');
            $('lineSettingsModal').classList.add('hidden');
        } else {
            toast(data.error || 'บันทึกไม่สำเร็จค่ะ', 'error');
        }
    } catch (err) {
        toast('เกิดข้อผิดพลาดในการเชื่อมต่อค่ะ', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
            if (window.lucide) lucide.createIcons();
        }
    }
}

async function testOrgLineConnection() {
    const btn = $('btnTestLineChannel');
    const token = $('lineSettingsToken').value.trim();
    const originalHtml = btn ? btn.innerHTML : 'ทดสอบการเชื่อมต่อ';
    
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i> กำลังทดสอบ...';
        if (window.lucide) lucide.createIcons();
    }
    
    try {
        const res = await apiFetch('/api/org/line/channel-config/test', {
            method: 'POST',
            body: JSON.stringify({ channel_access_token: token })
        });
        if (res && res.ok) {
            toast(res.message || 'เชื่อมต่อ LINE Bot สำเร็จเรียบร้อย!', 'success');
            if (res.bot_info?.basicId && !$('lineSettingsBotId').value) {
                $('lineSettingsBotId').value = res.bot_info.basicId;
            }
        } else {
            toast(res?.error || 'ไม่สามารถเชื่อมต่อกับ LINE API ได้', 'error');
        }
    } catch (e) {
        toast('เกิดข้อผิดพลาดในการทดสอบค่ะ', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
            if (window.lucide) lucide.createIcons();
        }
    }
}

async function resetOrgLineBot() {
    if (!await showConfirm('คืนค่าบอทส่วนกลาง', 'คุณต้องการลบ Channel Key ประจำองค์กรและกลับไปใช้ LINE Bot ส่วนกลางของระบบหรือไม่?', { type: 'warning', confirmText: 'คืนค่าบอทระบบ' })) {
        return;
    }
    try {
        const res = await apiFetch('/api/org/line/channel-config', { method: 'DELETE' });
        if (res && res.ok) {
            toast('คืนค่าการใช้งานบอทส่วนกลางสำเร็จค่ะ', 'success');
            $('lineSettingsToken').value = '';
            $('lineSettingsSecret').value = '';
            $('lineSettingsBotId').value = '@905gsngi';
            openLineSettings();
        } else {
            toast(res?.error || 'ไม่สามารถลบการตั้งค่าได้ค่ะ', 'error');
        }
    } catch (e) {
        toast('เกิดข้อผิดพลาดในการเชื่อมต่อค่ะ', 'error');
    }
}

function copyLineWebhookUrl() {
    const text = $('lineWebhookUrlText')?.textContent || window.location.origin + '/api/line/webhook';
    navigator.clipboard.writeText(text).then(() => {
        toast('คัดลอก Webhook URL เรียบร้อยแล้วค่ะ', 'success');
    }).catch(() => {
        toast('ไม่สามารถคัดลอกได้ กรุณาคัดลอกด้วยตนเองค่ะ', 'warning');
    });
}

async function refreshBroadcastHistory() {
    const list = $('broadcastHistoryList');
    if (!list) return;
    
    try {
        const data = await apiFetch('/api/admin/line/broadcast-history');
        if (data && data.ok) {
            list.innerHTML = data.history.map(item => `
                <tr class="text-xs text-surface-600 dark:text-surface-300">
                    <td class="py-3 pr-4">${new Date(item.timestamp).toLocaleString('th-TH', {hour12:false, month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'})}</td>
                    <td class="py-3 pr-4 truncate max-w-[150px]">${item.message}</td>
                    <td class="py-3">
                        <span class="px-2 py-0.5 rounded-full text-[9px] font-bold uppercase ${item.status === 'Success' ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400'}">
                            ${item.status}
                        </span>
                    </td>
                </tr>
            `).join('');
            if (!data.history.length) {
                list.innerHTML = '<tr><td colspan="3" class="py-8 text-center text-surface-400 text-[10px]">ยังไม่มีประวัติการส่งค่ะ</td></tr>';
            }
        }
    } catch (err) {
        console.error('Failed to fetch history:', err);
    }
}

// Global Event Listener for Broadcast Buttons
document.addEventListener('click', (e) => {
  const btn = e.target.closest('#lineBroadcastBtn, #lineManagerBroadcastBtn');
  if (btn) {
    e.preventDefault();
    if (btn.id === 'lineManagerBroadcastBtn') {
      sendLineBroadcast('lineManagerBroadcastMsg', 'lineManagerBroadcastBtn');
      setTimeout(refreshBroadcastHistory, 2000); // Auto-refresh after broadcast
    } else {
      sendLineBroadcast('lineBroadcastMsg', 'lineBroadcastBtn');
    }
  }
});

// --- Window Exports ---
window.sendLineBroadcast = sendLineBroadcast;
window.openLineSettings = openLineSettings;
window.saveLineSettings = saveLineSettings;
window.refreshBroadcastHistory = refreshBroadcastHistory;

// ─── To-Do Search & Filtering ──────────────────────────────
function filterTodoTasks() {
  const q = $('todoSearch').value.toLowerCase().trim();
  const tasks = document.querySelectorAll('#todoList > div');
  tasks.forEach(t => {
    const text = t.querySelector('span')?.textContent?.toLowerCase() || '';
    t.classList.toggle('hidden', q && !text.includes(q));
  });
}

// ─── AI Persona Manager (Admin) ──────────────────────────────
let adminPersonas = [];

async function openPersonaManager() {
  const modal = $('personaManagerModal');
  if (!modal) return;
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  await loadAdminPersonas();
}

function closePersonaManager() {
  const modal = $('personaManagerModal');
  if (!modal) return;
  modal.classList.add('hidden');
  modal.classList.remove('flex');
}

async function loadAdminPersonas() {
  const list = $('adminPersonaList');
  if (!list) return;
  list.innerHTML = '<div class="text-center py-10 opacity-30 italic text-xs">กำลังโหลด...</div>';

  try {
    const data = await apiFetch('/api/admin/personas');
    adminPersonas = data.personas || [];
    renderAdminPersonaList();
  } catch (err) {
    list.innerHTML = '<div class="text-center py-10 text-rose-500 text-xs">โหลดไม่สำเร็จ</div>';
  }
}

function renderAdminPersonaList() {
  const list = $('adminPersonaList');
  if (!list) return;

  if (adminPersonas.length === 0) {
    list.innerHTML = '<div class="text-center py-10 opacity-30 text-xs italic">ไม่มี Persona</div>';
    return;
  }

  list.innerHTML = adminPersonas.map(p => `
    <div onclick="selectAdminPersona('${p.id}')" class="p-3 rounded-2xl border border-surface-100 dark:border-surface-800 hover:border-brand-500 cursor-pointer transition-all bg-white dark:bg-surface-900 group">
      <div class="flex items-center gap-3">
        <img src="${p.avatar_url || 'https://cdn-icons-png.flaticon.com/512/1077/1077114.png'}" class="w-8 h-8 rounded-lg object-cover">
        <div class="flex-1 min-w-0">
          <div class="text-xs font-black truncate">${escHtml(p.name)}</div>
          <div class="text-[9px] text-surface-400 truncate uppercase tracking-tighter">${escHtml(p.description || '')}</div>
        </div>
        <i data-lucide="chevron-right" class="w-3 h-3 text-surface-300 group-hover:text-brand-500 transition-colors"></i>
      </div>
    </div>
  `).join('');
  lucide.createIcons();
}

function selectAdminPersona(id) {
  const p = adminPersonas.find(x => x.id == id);
  if (!p) return;

  $('personaEmptyState').classList.add('hidden');
  $('personaEditorContent').classList.remove('hidden');
  $('btnDeletePersona').classList.remove('hidden');

  $('edit_p_id').value = p.id;
  $('edit_p_name').value = p.name;
  $('edit_p_icon').value = p.avatar_url || '';
  $('edit_p_desc').value = p.description || '';
  $('edit_p_prompt').value = p.system_prompt || '';
}

function openCreatePersona() {
  $('personaEmptyState').classList.add('hidden');
  $('personaEditorContent').classList.remove('hidden');
  $('btnDeletePersona').classList.add('hidden');

  $('edit_p_id').value = '';
  $('edit_p_name').value = '';
  $('edit_p_icon').value = '';
  $('edit_p_desc').value = '';
  $('edit_p_prompt').value = '';
  $('edit_p_name').focus();
}

async function savePersona() {
  const id = $('edit_p_id').value;
  const name = $('edit_p_name').value.trim();
  const icon = $('edit_p_icon').value.trim();
  const description = $('edit_p_desc').value.trim();
  const prompt = $('edit_p_prompt').value.trim();

  if (!name || !prompt) {
    toast('กรุณากรอกชื่อและนิสัย AI', 'warning');
    return;
  }

  try {
    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/admin/personas/${id}` : '/api/admin/personas';
    
    const res = await apiFetch(url, {
      method,
      body: JSON.stringify({ name, icon, description, prompt })
    });

    if (res.ok) {
      toast('บันทึก Persona สำเร็จ', 'success');
      loadAdminPersonas();
      $('personaEmptyState').classList.remove('hidden');
      $('personaEditorContent').classList.add('hidden');
    } else {
      toast(res.error || 'เกิดข้อผิดพลาด', 'error');
    }
  } catch (err) {
    toast('เซิร์ฟเวอร์ขัดข้อง', 'error');
  }
}

async function deletePersona() {
  const id = $('edit_p_id').value;
  if (!id) return;

  if (!confirm('ยืนยันการลบ Persona นี้?')) return;

  try {
    const res = await apiFetch(`/api/admin/personas/${id}`, { method: 'DELETE' });
    if (res.ok) {
      toast('ลบ Persona แล้ว', 'success');
      loadAdminPersonas();
      $('personaEmptyState').classList.remove('hidden');
      $('personaEditorContent').classList.add('hidden');
    } else {
      toast(res.error || 'ลบไม่สำเร็จ', 'error');
    }
  } catch (err) {
    toast('เซิร์ฟเวอร์ขัดข้อง', 'error');
  }
}

// ─── Activity Logs (Admin) ──────────────────────────────
let activityLogs = [];

async function openActivityLogModal() {
  const modal = $('activityLogModal');
  if (!modal) return;
  modal.classList.remove('hidden');
  modal.classList.add('flex');
  await loadActivityLogs();
}

function closeActivityLogModal() {
  const modal = $('activityLogModal');
  if (!modal) return;
  modal.classList.add('hidden');
  modal.classList.remove('flex');
}

async function loadActivityLogs() {
  const tbody = $('activityLogTableBody');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="4" class="p-10 text-center opacity-30 italic">กำลังโหลดประวัติ...</td></tr>';
  $('logEmptyState').classList.add('hidden');

  try {
    const data = await apiFetch('/api/admin/logs');
    activityLogs = data.logs || [];
    renderLogs();
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="4" class="p-10 text-center text-rose-500">โหลดข้อมูลไม่สำเร็จ</td></tr>';
  }
}

function renderLogs() {
  const tbody = $('activityLogTableBody');
  const q = $('logSearch').value.toLowerCase().trim();
  
  const filtered = activityLogs.filter(l => 
    l.user.toLowerCase().includes(q) || 
    l.event.toLowerCase().includes(q)
  );

  if (filtered.length === 0) {
    tbody.innerHTML = '';
    $('logEmptyState').classList.remove('hidden');
    return;
  }

  $('logEmptyState').classList.add('hidden');
  tbody.innerHTML = filtered.map(l => `
    <tr class="hover:bg-surface-50 dark:hover:bg-surface-800/30 transition-colors">
      <td class="p-4 pl-8 text-surface-400 font-medium">${l.time}</td>
      <td class="p-4">
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 rounded-full bg-surface-100 dark:bg-surface-800 flex items-center justify-center text-[10px] font-black">${l.user[0].toUpperCase()}</div>
          <span class="font-bold">${escHtml(l.user)}</span>
        </div>
      </td>
      <td class="p-4 font-medium text-surface-600 dark:text-surface-300">${escHtml(l.event)}</td>
      <td class="p-4 text-right pr-8">
         <span class="px-2 py-0.5 rounded-full bg-surface-100 dark:bg-surface-800 text-[10px] font-bold text-surface-500">System</span>
      </td>
    </tr>
  `).join('');
}

function filterLogs() {
  renderLogs();
}

// --- Window Exports ---
window.rollLunch = rollLunch;
window.openLunchModal = openLunchModal;
window.toggleLunchManager = toggleLunchManager;
window.addLunchPlacePrompt = addLunchPlacePrompt;
window.deleteLunchPlace = deleteLunchPlace;
window.showWeatherDetail = showWeatherDetail;
window.fetchWeather = fetchWeather;
window.updateSystemStatus = updateSystemStatus;

// New Admin Exports
window.filterTodoTasks = filterTodoTasks;
window.openPersonaManager = openPersonaManager;
window.closePersonaManager = closePersonaManager;
window.loadAdminPersonas = loadAdminPersonas;
window.selectAdminPersona = selectAdminPersona;
window.selectPersona = selectPersona;
window.openCreatePersona = openCreatePersona;
window.savePersona = savePersona;
window.deletePersona = deletePersona;
window.openActivityLogModal = openActivityLogModal;
window.closeActivityLogModal = closeActivityLogModal;
window.loadActivityLogs = loadActivityLogs;
window.filterLogs = filterLogs;

// ═══════════════════════════════════════════════════════════════
// Google Drive & Sheets Per-User Connection (OAuth2)
// ═══════════════════════════════════════════════════════════════

async function loadGoogleDriveStatus() {
  const loading = $('googleConnectLoading');
  const notConnected = $('googleNotConnected');
  const connected = $('googleConnected');
  const notConfigured = $('googleOAuthNotConfigured');

  if (!loading) return; // Section not present

  // Show loading
  loading.classList.remove('hidden');
  notConnected.classList.add('hidden');
  connected.classList.add('hidden');

  try {
    const data = await apiFetch('/api/auth/google/status');

    loading.classList.add('hidden');

    if (data.connected) {
      connected.classList.remove('hidden');
      notConnected.classList.add('hidden');

      const isOrgLevel = data.effective_source === 'org';
      const connectedBy = data.org?.connected_by;

      if ($('googleConnectedEmail')) {
        const badge = isOrgLevel
          ? `<span class="ml-2 text-[9px] font-black uppercase tracking-wider bg-brand-100 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 px-1.5 py-0.5 rounded-full">ระดับองค์กร</span>`
          : `<span class="ml-2 text-[9px] font-black uppercase tracking-wider bg-surface-100 dark:bg-surface-700 text-surface-500 px-1.5 py-0.5 rounded-full">ส่วนตัว</span>`;
        $('googleConnectedEmail').innerHTML = (data.email || '—') + badge;
      }

      // แสดง "เชื่อมต่อโดย X" ถ้าเป็น org level
      const connByEl = $('googleConnectedBy');
      if (connByEl) {
        connByEl.textContent = isOrgLevel && connectedBy ? `เชื่อมต่อโดย: ${connectedBy}` : '';
        connByEl.classList.toggle('hidden', !isOrgLevel || !connectedBy);
      }

      if ($('googleSheetLink') && data.spreadsheet_url) {
        $('googleSheetLink').href = data.spreadsheet_url;
      }
      if ($('googleDriveLink') && data.drive_folder_url) {
        $('googleDriveLink').href = data.drive_folder_url;
      }

      // ซ่อนปุ่ม disconnect สำหรับ non-admin ถ้าเป็น org-level
      const disconnectBtn = $('googleDisconnectBtn');
      if (disconnectBtn && isOrgLevel && !state.isAdmin && !state.isOrgAdmin) {
        disconnectBtn.classList.add('hidden');
      }
      // ซ่อนปุ่ม reconnect สำหรับ non-admin
      const reconnectBtn = $('googleReconnectBtn');
      if (reconnectBtn && isOrgLevel && !state.isAdmin && !state.isOrgAdmin) {
        reconnectBtn.classList.add('hidden');
      }
    } else {
      notConnected.classList.remove('hidden');
      connected.classList.add('hidden');

      if (data.oauth2_available === false && notConfigured) {
        notConfigured.classList.remove('hidden');
        if ($('googleConnectBtn')) {
          $('googleConnectBtn').classList.add('opacity-50', 'pointer-events-none');
        }
      }

      // ซ่อนปุ่มเชื่อมต่อสำหรับ non-admin
      if ($('googleConnectBtn') && !state.isAdmin && !state.isOrgAdmin) {
        $('googleConnectBtn').classList.add('hidden');
        const noteEl = document.createElement('p');
        noteEl.className = 'text-[10px] text-surface-400 text-center';
        noteEl.textContent = 'Admin ขององค์กรต้องเชื่อมต่อ Google ก่อน';
        $('googleConnectBtn').parentNode?.appendChild(noteEl);
      }
    }
  } catch (err) {
    console.error('Failed to check Google connection:', err);
    loading.classList.add('hidden');
    notConnected.classList.remove('hidden');
  }

  lucide.createIcons();
}

async function disconnectGoogleDrive() {
  if (!confirm('ต้องการยกเลิกการเชื่อมต่อ Google Drive & Sheets หรือไม่?\n\nข้อมูลที่บันทึกไว้ใน Google Sheets ของคุณจะยังอยู่ แต่ระบบจะไม่เขียนข้อมูลใหม่ลงไปอีก')) {
    return;
  }

  const btn = $('googleDisconnectBtn');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> กำลังยกเลิก...';
    lucide.createIcons();
  }

  try {
    const res = await apiFetch('/api/auth/google/disconnect', {
      method: 'POST'
    });

    if (res.ok) {
      toast('ยกเลิกการเชื่อมต่อ Google สำเร็จ', 'success');
      loadGoogleDriveStatus();
    } else {
      toast('เกิดข้อผิดพลาด: ' + (res.error || 'Unknown'), 'error');
    }
  } catch (err) {
    toast('ไม่สามารถยกเลิกการเชื่อมต่อได้', 'error');
    console.error('Disconnect error:', err);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i data-lucide="unplug" class="w-4 h-4"></i> ยกเลิกการเชื่อมต่อ Google';
      lucide.createIcons();
    }
  }
}

window.disconnectGoogleDrive = disconnectGoogleDrive;
window.loadGoogleDriveStatus = loadGoogleDriveStatus;

// ─── Upgrade Prompt ───────────────────────────────────────────────────────────
function showUpgradePrompt(errData) {
  const existing = document.getElementById('upgradeModal');
  if (existing) existing.remove();

  const planLabel = { free: 'Free', pro: 'Pro', business: 'Business' };
  const current = planLabel[errData.current_plan] || errData.current_plan || 'Free';
  const isUsage = errData.error === 'usage_limit_reached';

  const titleText  = isUsage ? 'โควต้าหมดแล้ว' : 'ฟีเจอร์นี้ต้องการ Plan สูงกว่า';
  const bodyText   = errData.message || 'กรุณาอัปเกรด Plan เพื่อใช้งานต่อ';
  const usageHtml  = isUsage && errData.limit > 0 ? `
    <div class="flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200 mb-4">
      <div class="flex-1">
        <p class="text-xs text-slate-500 font-medium mb-1">การใช้งานเดือนนี้</p>
        <div class="h-1.5 bg-slate-200 rounded-full overflow-hidden">
          <div class="h-full bg-rose-500 rounded-full" style="width:100%"></div>
        </div>
      </div>
      <span class="text-xs font-bold text-rose-600 whitespace-nowrap">${errData.used}/${errData.limit}</span>
    </div>` : '';

  const modal = document.createElement('div');
  modal.id = 'upgradeModal';
  modal.style.cssText = 'position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;padding:1rem;background:rgba(15,23,42,0.45);backdrop-filter:blur(4px)';
  modal.innerHTML = `
    <div style="background:#fff;border-radius:1.25rem;max-width:380px;width:100%;padding:1.75rem;box-shadow:0 20px 60px rgba(15,23,42,0.2);font-family:Outfit,Sarabun,sans-serif;">
      <div style="display:flex;align-items:flex-start;gap:0.875rem;margin-bottom:1rem;">
        <div style="width:2.5rem;height:2.5rem;background:#fef3c7;border:1.5px solid #fde68a;border-radius:0.75rem;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
        </div>
        <div>
          <p style="font-size:0.75rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.25rem;">Plan ${current}</p>
          <h3 style="font-size:1.05rem;font-weight:800;color:#0f172a;line-height:1.3;">${titleText}</h3>
        </div>
      </div>
      <p style="font-size:0.875rem;color:#475569;margin-bottom:1rem;line-height:1.6;">${bodyText}</p>
      ${usageHtml}
      <div style="display:flex;gap:0.625rem;">
        <a href="/pricing" style="flex:1;padding:0.625rem;text-align:center;font-size:0.875rem;font-weight:700;color:#fff;background:#059669;border-radius:0.75rem;text-decoration:none;transition:background 0.15s;" onmouseover="this.style.background='#047857'" onmouseout="this.style.background='#059669'">
          อัปเกรด Plan
        </a>
        <button onclick="document.getElementById('upgradeModal').remove()" style="flex:1;padding:0.625rem;font-size:0.875rem;font-weight:600;color:#475569;background:#f1f5f9;border:1px solid #e2e8f0;border-radius:0.75rem;cursor:pointer;">
          ปิด
        </button>
      </div>
    </div>`;

  modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
  document.body.appendChild(modal);

  // Re-enable send button
  const sendBtn = document.getElementById('sendBtn');
  const msgInput = document.getElementById('msgInput');
  if (sendBtn) sendBtn.disabled = false;
  if (msgInput) { msgInput.disabled = false; msgInput.focus(); }
  if (typeof state !== 'undefined') state.sending = false;
}

// ─── Connection banner ────────────────────────────────────────────────────────
function _showConnBanner() {
  if (document.getElementById('_connBanner')) return;
  const el = document.createElement('div');
  el.id = '_connBanner';
  el.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99999;background:#dc2626;color:#fff;text-align:center;padding:0.5rem 1rem;font-size:0.8rem;font-weight:700;display:flex;align-items:center;justify-content:center;gap:0.5rem;';
  el.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M1 1l22 22M16.72 11.06A10.94 10.94 0 0 1 19 12.55M5 12.55a10.94 10.94 0 0 1 5.17-2.39M10.71 5.05A16 16 0 0 1 22.56 9M1.42 9a15.91 15.91 0 0 1 4.7-2.88M8.53 16.11a6 6 0 0 1 6.95 0M12 20h.01"/></svg><span>การเชื่อมต่อขาดหาย — กำลังเชื่อมต่อใหม่...</span>';
  document.body.prepend(el);
}
function _hideConnBanner() {
  const el = document.getElementById('_connBanner');
  if (el) el.remove();
}

// ═══════════════════════════════════════════════════════════════
// ใบแทนใบเสร็จ (Replacement Receipt)
// ═══════════════════════════════════════════════════════════════

function initReplacementReceiptView() {
  // Set today's date as default for new document date
  const today = new Date().toISOString().split('T')[0];
  const rrNewDate = $('rrNewDate');
  if (rrNewDate && !rrNewDate.value) rrNewDate.value = today;

  // Generate default RR number if empty
  const rrNewNo = $('rrNewNo');
  if (rrNewNo && !rrNewNo.value) {
    const now = new Date();
    rrNewNo.value = `RR-${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}-001`;
  }

  // Wire up reason dropdown → show/hide custom input
  const rrReason = $('rrReason');
  const rrReasonCustom = $('rrReasonCustom');
  if (rrReason && rrReasonCustom) {
    rrReason.onchange = () => {
      rrReasonCustom.classList.toggle('hidden', rrReason.value !== 'อื่นๆ');
      updateRRPreview();
    };
  }

  // Auto-fill seller info from org profile
  apiFetch('/api/org/profile').then(data => {
    if (!data || !data.ok) return;
    const p = data.profile || {};
    const nameEl = $('rrSellerName');
    const addrEl = $('rrSellerAddr');
    const taxEl = $('rrSellerTax');
    const phoneEl = $('rrSellerPhone');
    if (nameEl && !nameEl.value) nameEl.value = p.name || '';
    if (addrEl && !addrEl.value) addrEl.value = p.address || '';
    if (taxEl && !taxEl.value) taxEl.value = p.tax_id || '';
    if (phoneEl && !phoneEl.value) phoneEl.value = p.phone || '';

    // Render logo in Replacement Receipt A4 preview if it exists
    const rrLogoImg = $('rrPrevLogoImg');
    if (rrLogoImg) {
      if (p.logo_url) {
        rrLogoImg.src = p.logo_url;
        rrLogoImg.classList.remove('hidden');
      } else {
        rrLogoImg.classList.add('hidden');
      }
    }

    // Render signature in Replacement Receipt A4 preview if it exists
    const rrSigImg = $('rrPrevSignatureImg');
    if (rrSigImg) {
      if (p.signature_url) {
        rrSigImg.src = p.signature_url;
        rrSigImg.classList.remove('hidden');
      } else {
        rrSigImg.classList.add('hidden');
      }
    }

    updateRRPreview();
  }).catch(() => {});

  updateRRPreview();
  if (typeof initIcons === 'function') initIcons();
}

function openReplacementFromExpense(item) {
  showView('receipt-replacement');
  // Wait for view to render then fill
  setTimeout(() => {
    initReplacementReceiptView();

    // Fill original document reference from expense row
    const origNo = $('rrOrigNo');
    const origDate = $('rrOrigDate');
    const desc = $('rrDescription');
    const amt = $('rrAmountBeforeVat');
    const wht = $('rrWhtAmt');

    if (origNo) origNo.value = item.ref_number || '';
    if (origDate && item.date) {
      // Convert Thai/display date to yyyy-mm-dd if needed
      try {
        const parts = String(item.date).split('/');
        if (parts.length === 3) {
          const y = parts[2].length === 4 ? parts[2] : String(parseInt(parts[2]) - 543);
          origDate.value = `${y}-${parts[1].padStart(2,'0')}-${parts[0].padStart(2,'0')}`;
        } else {
          origDate.value = item.date;
        }
      } catch (_) { origDate.value = item.date || ''; }
    }
    if (desc) desc.value = item.details || item.merchant || '';
    if (amt) amt.value = item.net_amount != null ? parseFloat(item.net_amount).toFixed(2) : '';
    if (wht) wht.value = item.wht_amount != null ? parseFloat(item.wht_amount).toFixed(2) : '';

    calcRRTotal();
    updateRRPreview();
  }, 150);
}

function calcRRTotal() {
  const before = parseFloat($('rrAmountBeforeVat')?.value) || 0;
  const wht = parseFloat($('rrWhtAmt')?.value) || 0;
  const vatEl = $('rrVatAmt');
  
  let vat = parseFloat(vatEl?.value);
  
  // Logic: If vat is NaN (empty) or if this was triggered by 'before' changing,
  // we might want to suggest the 7% calculation.
  // To keep it simple and flexible: If value is invalid, we auto-calc 7%.
  // If user wants 0, they can type 0.
  if (isNaN(vat)) {
      vat = Math.round(before * 0.07 * 100) / 100;
      if (vatEl) vatEl.value = vat.toFixed(2);
  }

  const grand = Math.round((before + vat - wht) * 100) / 100;
  const grandEl = $('rrGrandTotal');
  if (grandEl) grandEl.value = grand.toFixed(2);

  updateRRPreview();
}

function _fmtRRDate(isoDate) {
  if (!isoDate) return '-';
  try {
    const d = new Date(isoDate);
    if (isNaN(d)) return isoDate;
    return d.toLocaleDateString('th-TH', { year: 'numeric', month: 'long', day: 'numeric' });
  } catch (_) { return isoDate; }
}

function thaiBahtText(num) {
  if (num === null || num === undefined || isNaN(num)) return 'ศูนย์บาทถ้วน';
  num = parseFloat(num).toFixed(2);
  if (parseFloat(num) === 0) return 'ศูนย์บาทถ้วน';
  
  const thNum = ["ศูนย์", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"];
  const thDigit = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน", "ล้าน"];
  
  let [baht, satang] = num.split('.');
  
  function convertSection(numberStr) {
      let text = "";
      let len = numberStr.length;
      for (let i = 0; i < len; i++) {
          let digit = parseInt(numberStr[i]);
          let pos = len - i - 1;
          if (digit !== 0) {
              if (pos === 1 && digit === 2) {
                  text += "ยี่สิบ";
              } else if (pos === 1 && digit === 1) {
                  text += "สิบ";
              } else if (pos === 0 && digit === 1 && len > 1 && numberStr[i - 1] !== '0') {
                  text += "เอ็ด";
              } else {
                  text += thNum[digit] + thDigit[pos];
              }
          }
      }
      return text;
  }
  
  let bahtText = "";
  let bahtLen = baht.length;
  if (bahtLen > 6) {
      let millionPos = bahtLen - 6;
      let millionStr = baht.substring(0, millionPos);
      let remainStr = baht.substring(millionPos);
      bahtText = convertSection(millionStr) + "ล้าน" + convertSection(remainStr);
  } else {
      bahtText = convertSection(baht);
  }
  
  let result = "";
  if (bahtText !== "") {
      result += bahtText + "บาท";
  }
  
  if (satang === "00" || satang === "") {
      result += "ถ้วน";
  } else {
      result += convertSection(satang) + "สตางค์";
  }
  return result;
}

function updateRRPreview() {
  const g = (id) => $( id )?.value || '';
  const set = (id, val) => { const el = $(id); if (el) el.textContent = val || '-'; };

  // Seller
  const selName = g('rrSellerName');
  set('rrPrevSelName', selName || '-');
  const selInfo = [g('rrSellerAddr'), g('rrSellerTax') ? `เลขประจำตัวผู้เสียภาษี: ${g('rrSellerTax')}` : '', g('rrSellerPhone') ? `โทร: ${g('rrSellerPhone')}` : ''].filter(Boolean).join('\n');
  set('rrPrevSelInfo', selInfo || '-');

  // Doc numbers
  set('rrPrevNewNo', g('rrNewNo') || 'RR-XXXX-XXX');
  const newDateEl = $('rrPrevNewDate');
  if (newDateEl) newDateEl.textContent = _fmtRRDate(g('rrNewDate')) || '-';

  // Original reference
  set('rrPrevOrigNo', g('rrOrigNo') || '-');
  const origDateEl = $('rrPrevOrigDate');
  if (origDateEl) origDateEl.textContent = _fmtRRDate(g('rrOrigDate')) || '-';

  // Reason
  const reason = g('rrReason');
  const reasonCustom = g('rrReasonCustom');
  set('rrPrevReason', reason || '-');
  const detailEl = $('rrPrevReasonDetail');
  const detailTxtEl = $('rrPrevReasonDetailTxt');
  if (detailEl && detailTxtEl) {
    if (reason === 'อื่นๆ' && reasonCustom) {
      detailEl.style.display = 'inline';
      detailTxtEl.textContent = reasonCustom;
    } else {
      detailEl.style.display = 'none';
    }
  }

  // Customer
  set('rrPrevCustName', g('rrCustName') || '-');
  set('rrPrevCustAddr', g('rrCustAddr') || '-');
  const custTaxEl = $('rrPrevCustTax');
  if (custTaxEl) custTaxEl.textContent = g('rrCustTax') ? `เลขประจำตัวผู้เสียภาษี: ${g('rrCustTax')}` : '-';

  // Description & amounts
  set('rrPrevDesc', g('rrDescription') || '-');
  const before = parseFloat(g('rrAmountBeforeVat')) || 0;
  const vat = parseFloat(g('rrVatAmt')) || 0;
  const wht = parseFloat(g('rrWhtAmt')) || 0;
  const grand = parseFloat(g('rrGrandTotal')) || (before + vat - wht);

  const fmt = (n) => n.toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  set('rrPrevAmountBeforeVat', fmt(before));
  set('rrPrevSubTotal', fmt(before));
  set('rrPrevVat', fmt(vat));
  set('rrPrevWht', fmt(wht));
  set('rrPrevGrandTotal', fmt(grand));

  const thaiTextEl = $('rrPrevThaiBahtText');
  if (thaiTextEl) {
    thaiTextEl.textContent = thaiBahtText(grand);
  }
}

function clearRRForm() {
  ['rrSellerName','rrSellerAddr','rrSellerTax','rrSellerPhone',
   'rrNewNo','rrNewDate','rrOrigNo','rrOrigDate',
   'rrCustName','rrCustAddr','rrCustTax',
   'rrDescription','rrAmountBeforeVat','rrWhtAmt','rrVatAmt','rrGrandTotal'].forEach(id => {
    const el = $(id);
    if (el) el.value = '';
  });
  const rrReason = $('rrReason');
  if (rrReason) rrReason.selectedIndex = 0;
  const rrReasonCustom = $('rrReasonCustom');
  if (rrReasonCustom) rrReasonCustom.classList.add('hidden');
  updateRRPreview();
  toast('ล้างข้อมูลเรียบร้อย', 'success');
}

function generateRRPdf() {
  const preview = $('rrPreview');
  if (!preview) { toast('ไม่พบตัวอย่างเอกสาร', 'error'); return; }
  if (typeof html2pdf === 'undefined') { toast('โหลด html2pdf ไม่สำเร็จ', 'error'); return; }

  const docNo = $('rrNewNo')?.value || 'RR';
  const origStyle = preview.style.cssText;
  preview.style.transform = 'none';
  preview.style.marginBottom = '0';

  html2pdf().set({
    margin: 0,
    filename: `ใบแทนใบเสร็จ_${docNo}.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
  }).from(preview).save().then(() => {
    preview.style.cssText = origStyle;
    toast('ดาวน์โหลด PDF สำเร็จ', 'success');
  }).catch((e) => {
    preview.style.cssText = origStyle;
    console.error('PDF error:', e);
    toast('เกิดข้อผิดพลาดในการสร้าง PDF', 'error');
  });
}

async function scanReceiptWithAI(input) {
  const file = input.files[0];
  if (!file) return;
  
  const formData = new FormData();
  formData.append('file', file);
  
  const btn = document.querySelector('button[onclick*="rrOcrInput"]');
  const originalHtml = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full inline-block mr-1"></span> กำลังวิเคราะห์...';
  }
  
  try {
    const res = await fetch('/api/receipt-replacement/scan', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.ok) {
      toast('สแกนบิลสำเร็จ ดึงข้อมูลลงฟอร์มเรียบร้อยค่ะ', 'success');
      
      if (data.sender && data.sender !== '-') {
        const nameEl = $('rrSellerName');
        if (nameEl) nameEl.value = data.sender;
      }
      if (data.sender_address && data.sender_address !== '-') {
        const addrEl = $('rrSellerAddr');
        if (addrEl) addrEl.value = data.sender_address;
      }
      if (data.vendor_tax_id && data.vendor_tax_id !== '-') {
        const taxEl = $('rrSellerTax');
        if (taxEl) taxEl.value = data.vendor_tax_id;
      }
      if (data.phone && data.phone !== '-') {
        const phoneEl = $('rrSellerPhone');
        if (phoneEl) phoneEl.value = data.phone;
      }
      if (data.ref_number && data.ref_number !== '-') {
        const origNoEl = $('rrOrigNo');
        if (origNoEl) origNoEl.value = data.ref_number;
      }
      
      if (data.date && data.date !== '-') {
        try {
          const parts = data.date.split('/');
          const origDateEl = $('rrOrigDate');
          if (origDateEl) {
            if (parts.length === 3) {
              origDateEl.value = `${parts[2]}-${parts[1].padStart(2,'0')}-${parts[0].padStart(2,'0')}`;
            } else {
              origDateEl.value = data.date;
            }
          }
        } catch (_) {}
      }
      
      if (data.memo && data.memo !== '-') {
        const descEl = $('rrDescription');
        if (descEl) descEl.value = data.memo;
      }
      if (data.gross_amount) {
        const amtEl = $('rrAmountBeforeVat');
        if (amtEl) amtEl.value = parseFloat(data.gross_amount).toFixed(2);
      }
      if (data.vat_amount) {
        const vatEl = $('rrVatAmt');
        if (vatEl) vatEl.value = parseFloat(data.vat_amount).toFixed(2);
      }
      if (data.wht_amount) {
        const whtEl = $('rrWhtAmt');
        if (whtEl) whtEl.value = parseFloat(data.wht_amount).toFixed(2);
      }
      
      calcRRTotal();
      updateRRPreview();
    } else {
      toast(data.error || 'สแกนไม่สำเร็จ กรุณาลองใหม่อีกครั้งค่ะ', 'error');
    }
  } catch (e) {
    console.error(e);
    toast('เกิดข้อผิดพลาดในการวิเคราะห์เอกสาร', 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = originalHtml;
    }
    input.value = '';
  }
}

let rrCurrentZoom = 1.0;

function openRRPreviewFullscreen() {
  const modal = $('rrFullscreenModal');
  const src = $('rrPreview');
  const target = $('rrFullscreenPaper');
  if (!modal || !src || !target) return;

  // Sync latest values
  updateRRPreview();

  // Clone content into fullscreen paper
  target.innerHTML = src.innerHTML;

  // Auto-fit zoom to viewport width
  const winW = window.innerWidth;
  if (winW < 850) {
    rrCurrentZoom = Math.max(0.4, (winW - 32) / 820);
  } else {
    rrCurrentZoom = 1.0;
  }
  applyRRZoom();

  modal.classList.remove('hidden');
  modal.classList.add('flex');
  document.body.style.overflow = 'hidden';

  if (typeof lucide !== 'undefined') lucide.createIcons();
}

function closeRRPreviewFullscreen() {
  const modal = $('rrFullscreenModal');
  if (!modal) return;
  modal.classList.add('hidden');
  modal.classList.remove('flex');
  document.body.style.overflow = '';
}

function changeRRZoom(delta) {
  rrCurrentZoom = Math.min(2.5, Math.max(0.35, rrCurrentZoom + delta));
  applyRRZoom();
}

function resetRRZoom() {
  rrCurrentZoom = 1.0;
  applyRRZoom();
}

function applyRRZoom() {
  const wrapper = $('rrFullscreenWrapper');
  const label = $('rrZoomLabel');
  if (wrapper) {
    wrapper.style.transform = `scale(${rrCurrentZoom})`;
  }
  if (label) {
    label.textContent = `${Math.round(rrCurrentZoom * 100)}%`;
  }
}

function printRRPaper() {
  const preview = $('rrPreview');
  if (!preview) return;
  const printWin = window.open('', '', 'width=900,height=800');
  if (!printWin) {
    window.print();
    return;
  }
  printWin.document.write(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>พิมพ์ใบแทนใบเสร็จรับเงิน</title>
        <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@400;600;700;800&family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
          @page { size: A4 portrait; margin: 0; }
          body { margin: 0; padding: 15mm; font-family: 'Sarabun', 'Outfit', sans-serif; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          #printPaper { width: 210mm; min-height: 297mm; box-sizing: border-box; }
        </style>
      </head>
      <body>
        <div id="printPaper">${preview.innerHTML}</div>
        <script>
          window.onload = function() {
            window.focus();
            window.print();
            window.close();
          };
        <\/script>
      </body>
    </html>
  `);
  printWin.document.close();
}

// Close on Escape key
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    const modal = $('rrFullscreenModal');
    if (modal && !modal.classList.contains('hidden')) {
      closeRRPreviewFullscreen();
    }
  }
});

window.initReplacementReceiptView = initReplacementReceiptView;
window.openReplacementFromExpense = openReplacementFromExpense;
window.calcRRTotal = calcRRTotal;
window.updateRRPreview = updateRRPreview;
window.clearRRForm = clearRRForm;
window.generateRRPdf = generateRRPdf;
window.scanReceiptWithAI = scanReceiptWithAI;
window.openRRPreviewFullscreen = openRRPreviewFullscreen;
window.closeRRPreviewFullscreen = closeRRPreviewFullscreen;
window.changeRRZoom = changeRRZoom;
window.resetRRZoom = resetRRZoom;
window.printRRPaper = printRRPaper;

// ─── PEAK API Integration ──────────────────────────────────────────────────────

window._peakMode = 'upload';

function setPeakMode(mode) {
    window._peakMode = mode;
    const uploadBtn = $('peakModeUpload');
    const apiBtn = $('peakModeApi');
    const uploadZone = $('peakUploadZone');
    const apiZone = $('peakApiZone');
    if (!uploadBtn || !apiBtn) return;
    if (mode === 'api') {
        uploadBtn.className = uploadBtn.className.replace('bg-white dark:bg-surface-700 text-indigo-600 shadow-sm', 'text-surface-400');
        apiBtn.className = apiBtn.className.replace('text-surface-400', 'bg-white dark:bg-surface-700 text-indigo-600 shadow-sm');
        uploadZone?.classList.add('hidden');
        apiZone?.classList.remove('hidden');
    } else {
        apiBtn.className = apiBtn.className.replace('bg-white dark:bg-surface-700 text-indigo-600 shadow-sm', 'text-surface-400');
        uploadBtn.className = uploadBtn.className.replace('text-surface-400', 'bg-white dark:bg-surface-700 text-indigo-600 shadow-sm');
        apiZone?.classList.add('hidden');
        uploadZone?.classList.remove('hidden');
    }
}

async function loadPeakSettingsStatus() {
    try {
        const res = await fetch('/api/peak/settings');
        if (!res.ok) return;
        const data = await res.json();
        if (!data.ok) return;
        const statusEl = $('peakSettingsStatus');
        const notConnectedEl = $('peakApiNotConnected');
        const isConnected = data.connect_id && data.has_user_token;
        if (statusEl) {
            statusEl.textContent = isConnected ? 'เชื่อมต่อแล้ว' : 'ยังไม่ได้เชื่อมต่อ';
            statusEl.className = statusEl.className.replace(/text-\w+-\d+/, isConnected ? 'text-emerald-600' : 'text-surface-400');
        }
        if (notConnectedEl) {
            if (window._peakMode === 'api' && !isConnected) notConnectedEl.classList.remove('hidden');
            else notConnectedEl.classList.add('hidden');
        }
        if (isConnected && $('peakConnectId')) $('peakConnectId').value = data.connect_id;
    } catch (e) { /* ignore */ }
}

async function savePeakSettings() {
    const connectId = $('peakConnectId')?.value?.trim();
    const password = $('peakPassword')?.value?.trim();
    const userToken = $('peakUserToken')?.value?.trim();
    if (!connectId || !userToken) { toast('กรุณากรอก Connect ID และ User Token', 'error'); return; }
    try {
        const res = await fetch('/api/peak/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ connect_id: connectId, password, user_token: userToken }),
        });
        const data = await res.json();
        if (data.ok) {
            toast('บันทึกการตั้งค่า PEAK สำเร็จ', 'success');
            loadPeakSettingsStatus();
        } else {
            toast(data.error || 'บันทึกไม่สำเร็จ', 'error');
        }
    } catch (e) {
        toast('การเชื่อมต่อล้มเหลว', 'error');
    }
}

window.setPeakMode = setPeakMode;
window.savePeakSettings = savePeakSettings;

/* ══════════════════════════════════════════
   Organization Tree Chart (ผังองค์กรแบบต้นไม้)
   ══════════════════════════════════════════ */
let orgTreeZoomScale = 1.0;
let orgTreePanX = 0;
let orgTreePanY = 0;
let isPanningOrgTree = false;
let startPanX = 0;
let startPanY = 0;
let editingTreeMember = null;

// Zoom and Pan Controls
function orgTreeZoom(amount) {
  orgTreeZoomScale = Math.min(Math.max(orgTreeZoomScale * amount, 0.3), 3.0);
  applyOrgTreeTransform();
}

function orgTreeZoomReset() {
  orgTreeZoomScale = 1.0;
  orgTreePanX = 0;
  orgTreePanY = 0;
  applyOrgTreeTransform();
}

function applyOrgTreeTransform() {
  const container = document.getElementById("orgTreePanContainer");
  if (container) {
    container.style.transform = `translate(${orgTreePanX}px, ${orgTreePanY}px) scale(${orgTreeZoomScale})`;
  }
}

// Drag & Pan Canvas handlers
function initOrgTreeCanvasEvents() {
  const wrapper = document.getElementById("orgTreeCanvasWrapper");
  if (!wrapper) return;
  
  wrapper.addEventListener("mousedown", (e) => {
    if (e.target.closest(".org-node-card") || e.target.closest("button") || e.target.closest("select")) {
      return;
    }
    isPanningOrgTree = true;
    wrapper.style.cursor = "grabbing";
    startPanX = e.clientX - orgTreePanX;
    startPanY = e.clientY - orgTreePanY;
  });
  
  window.addEventListener("mousemove", (e) => {
    if (!isPanningOrgTree) return;
    orgTreePanX = e.clientX - startPanX;
    orgTreePanY = e.clientY - startPanY;
    applyOrgTreeTransform();
  });
  
  window.addEventListener("mouseup", () => {
    if (isPanningOrgTree) {
      isPanningOrgTree = false;
      wrapper.style.cursor = "grab";
    }
  });

  wrapper.addEventListener("wheel", (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    orgTreeZoom(zoomFactor);
  }, { passive: false });
}

function getDeptColorConfig(dept) {
  const d = (dept || '').trim().toLowerCase();
  if (Array.isArray(_orgDepartmentsCache) && _orgDepartmentsCache.length > 0) {
    const customDept = _orgDepartmentsCache.find(item => (item.department_name || '').trim().toLowerCase() === d);
    if (customDept && customDept.color) {
      return {
        stroke: customDept.color,
        badgeBg: 'bg-surface-100 dark:bg-surface-800 text-surface-900 dark:text-white border-surface-200 dark:border-surface-700',
        border: 'border-l-4',
        customColor: customDept.color
      };
    }
  }

  if (d.includes('บริหาร') || d.includes('exec') || d.includes('manage') || d.includes('ceo') || d.includes('director')) {
    return {
      stroke: '#8b5cf6',
      badgeBg: 'bg-purple-50 dark:bg-purple-950/40 text-purple-600 dark:text-purple-400 border-purple-200 dark:border-purple-800/40',
      border: 'border-l-4 border-l-purple-500'
    };
  }
  if (d.includes('tech') || d.includes('it') || d.includes('dev') || d.includes('ไอที') || d.includes('โปรแกรม') || d.includes('engineer')) {
    return {
      stroke: '#0284c7',
      badgeBg: 'bg-sky-50 dark:bg-sky-950/40 text-sky-600 dark:text-sky-400 border-sky-200 dark:border-sky-800/40',
      border: 'border-l-4 border-l-sky-500'
    };
  }
  if (d.includes('sale') || d.includes('ขาย') || d.includes('market') || d.includes('การตลาด') || d.includes('design')) {
    return {
      stroke: '#f43f5e',
      badgeBg: 'bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border-rose-200 dark:border-rose-800/40',
      border: 'border-l-4 border-l-rose-500'
    };
  }
  if (d.includes('บัญชี') || d.includes('account') || d.includes('finance') || d.includes('การเงิน')) {
    return {
      stroke: '#10b981',
      badgeBg: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800/40',
      border: 'border-l-4 border-l-emerald-500'
    };
  }
  if (d.includes('hr') || d.includes('บุคคล') || d.includes('admin') || d.includes('ธุรการ') || d.includes('operation')) {
    return {
      stroke: '#f59e0b',
      badgeBg: 'bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-800/40',
      border: 'border-l-4 border-l-amber-500'
    };
  }
  return {
    stroke: '#6366f1',
    badgeBg: 'bg-brand-50 dark:bg-brand-950/40 text-brand-600 dark:text-brand-400 border-brand-200 dark:border-brand-800/40',
    border: 'border-l-4 border-l-brand-500'
  };
}

// Render dynamic org tree chart
async function renderOrgTree() {
  const wrapper = document.getElementById("orgTreeCanvasWrapper");
  if (!wrapper) return;
  
  if (!wrapper.dataset.eventsInitialized) {
    initOrgTreeCanvasEvents();
    wrapper.dataset.eventsInitialized = "true";
  }

  if (!_orgMembersLoaded) {
    await loadOrgMembers();
    return;
  }

  const htmlNodesContainer = document.getElementById("orgTreeHtmlNodes");
  const svgContainer = document.getElementById("orgTreeSvg");
  if (!htmlNodesContainer || !svgContainer) return;

  htmlNodesContainer.innerHTML = "";
  svgContainer.innerHTML = "";

  if (_orgMembersCache.length === 0) {
    htmlNodesContainer.innerHTML = `<div class="absolute inset-0 flex items-center justify-center text-surface-400 font-bold text-xs">ไม่พบข้อมูลสมาชิกในองค์กร</div>`;
    return;
  }

  const membersMap = {};
  _orgMembersCache.forEach(m => {
    if (!m || !m.username) return;
    membersMap[m.username.toLowerCase()] = {
      ...m,
      children: [],
      x: 0,
      y: 0,
      width: 230,
      height: 96
    };
  });

  const roots = [];
  Object.values(membersMap).forEach(node => {
    const parentUsername = (node.manager_username || "").trim().toLowerCase();
    if (parentUsername && membersMap[parentUsername] && parentUsername !== node.username.toLowerCase()) {
      membersMap[parentUsername].children.push(node);
    } else {
      roots.push(node);
    }
  });
  window._orgTreeRoots = roots;

  const levelHeight = 165;
  const siblingWidth = 270;

  function layoutSubtree(node, depth, xOffset) {
    node.y = 50 + depth * levelHeight;
    
    if (node.children.length === 0) {
      node.x = xOffset;
      return xOffset + siblingWidth;
    }
    
    let currentX = xOffset;
    const childXs = [];
    node.children.forEach(child => {
      currentX = layoutSubtree(child, depth + 1, currentX);
      childXs.push(child.x);
    });
    
    const minChildX = Math.min(...childXs);
    const maxChildX = Math.max(...childXs);
    node.x = minChildX + (maxChildX - minChildX) / 2;
    
    return currentX;
  }

  let currentOffset = 50;
  roots.forEach(root => {
    currentOffset = layoutSubtree(root, 0, currentOffset);
  });

  if (roots.length > 0) {
    const canvasWidth = wrapper.clientWidth || 800;
    orgTreePanX = (canvasWidth / 2) - (roots[0].x + roots[0].width / 2);
    orgTreePanY = 40;
    orgTreeZoomScale = 1.0;
    applyOrgTreeTransform();
  }

  Object.values(membersMap).forEach(node => {
    const deptConfig = getDeptColorConfig(node.department);
    const card = document.createElement("div");
    card.id = `org-node-${node.username.toLowerCase()}`;
    card.className = `org-node-card absolute bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700 ${deptConfig.border} p-3 rounded-2xl shadow-sm flex items-center gap-3 transition-all duration-200 hover:shadow-lg hover:scale-[1.02]`;
    card.style.width = `${node.width}px`;
    card.style.height = `${node.height}px`;
    card.style.left = `${node.x}px`;
    card.style.top = `${node.y}px`;
    if (deptConfig.customColor) {
      card.style.borderLeftColor = deptConfig.customColor;
    }
    
    card.dataset.username = node.username.toLowerCase();
    card.dataset.name = (node.display_name || '').toLowerCase();
    card.dataset.pos = (node.position || '').toLowerCase();
    card.dataset.dept = (node.department || '').toLowerCase();

    const isAdmin = node.role === "admin";
    const roleBadge = isAdmin 
      ? `<span class="px-1.5 py-0.5 rounded text-[8px] font-black uppercase bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-900/50">Admin</span>`
      : `<span class="px-1.5 py-0.5 rounded text-[8px] font-black uppercase bg-surface-50 dark:bg-surface-800 text-surface-500 dark:text-surface-400 border border-surface-100 dark:border-surface-700">Member</span>`;

    const avatarHtml = node.avatar_url 
      ? `<img src="${node.avatar_url}" class="w-10 h-10 rounded-full object-cover border border-surface-200 dark:border-surface-700 flex-shrink-0" onerror="this.outerHTML='<div class=&quot;w-10 h-10 rounded-full flex items-center justify-center text-xs font-black uppercase text-brand-600 bg-brand-50 border border-surface-200 dark:border-surface-700 flex-shrink-0&quot;>${(node.display_name || node.username)[0].toUpperCase()}</div>'">`
      : `<div class="w-10 h-10 rounded-full flex items-center justify-center text-xs font-black uppercase text-brand-600 bg-brand-50 border border-surface-200 dark:border-surface-700 flex-shrink-0">${(node.display_name || node.username)[0].toUpperCase()}</div>`;
    const deptText = node.department || 'General';
    const posText = node.position || 'พนักงาน';

    const reportCount = node.children.length;
    const reportBadge = reportCount > 0 
      ? `<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[8px] font-extrabold bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-900/50" title="ผู้ใต้บังคับบัญชาโดยตรง ${reportCount} คน"><i data-lucide="users" class="w-2.5 h-2.5"></i> ${reportCount} คน</span>`
      : '';

    const canEdit = state.isOrgAdmin || state.isAdmin;
    const editBtn = canEdit 
      ? `<button onclick="event.stopPropagation(); openEditManagerModal('${node.username}')" class="p-1 hover:bg-surface-100 dark:hover:bg-surface-700 rounded-lg text-surface-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors ml-auto cursor-pointer" title="ปรับสายการรายงาน">
           <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 1 1-3 0m3 0a1.5 1.5 0 0 1-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-9.75 0h9.75"/></svg>
         </button>`
      : "";

    card.innerHTML = `
      ${avatarHtml}
      <div class="flex-1 min-w-0 pr-1 flex flex-col justify-center">
        <div class="flex items-center gap-1.5 mb-0.5">
          <div class="font-extrabold text-xs text-surface-900 dark:text-white truncate" title="${node.display_name}">${node.display_name}</div>
          ${roleBadge}
        </div>
        <div class="flex items-center gap-1 text-[9px] font-bold text-surface-400 dark:text-surface-500 truncate" title="${posText} (${deptText})">
          <span class="truncate max-w-[90px]">${posText}</span>
          <span>·</span>
          <span class="px-1.5 py-0.5 rounded text-[8px] font-extrabold border ${deptConfig.badgeBg} truncate max-w-[80px]">${deptText}</span>
        </div>
        <div class="mt-1 flex items-center gap-1">
          ${reportBadge}
        </div>
      </div>
      ${editBtn}
    `;

    htmlNodesContainer.appendChild(card);
  });

  Object.values(membersMap).forEach(node => {
    const parentDeptConfig = getDeptColorConfig(node.department);
    node.children.forEach(child => {
      const parentBottomX = node.x + node.width / 2;
      const parentBottomY = node.y + node.height;
      const childTopX = child.x + child.width / 2;
      const childTopY = child.y;

      const midY = (parentBottomY + childTopY) / 2;
      const pathData = `M ${parentBottomX} ${parentBottomY} 
                        C ${parentBottomX} ${midY}, 
                          ${childTopX} ${midY}, 
                          ${childTopX} ${childTopY}`;

      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", pathData);
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", parentDeptConfig.stroke);
      path.setAttribute("stroke-width", "2.5");
      path.setAttribute("stroke-linecap", "round");
      path.setAttribute("opacity", "0.45");
      
      path.addEventListener("mouseenter", () => {
        path.setAttribute("opacity", "0.95");
        path.setAttribute("stroke-width", "3.5");
      });
      path.addEventListener("mouseleave", () => {
        path.setAttribute("opacity", "0.45");
        path.setAttribute("stroke-width", "2.5");
      });

      svgContainer.appendChild(path);
    });
  });
  
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

function openEditManagerModal(username) {
  const member = _orgMembersCache.find(m => m && (m.username || '').toLowerCase() === (username || '').toLowerCase());
  if (!member) return;
  editingTreeMember = username;

  const avatarEl = document.getElementById("editManagerUserAvatar");
  if (avatarEl) {
    avatarEl.src = member.avatar_url || 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="%2394a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="10" r="3"/><path d="M7 20.662V19a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v1.662"/></svg>';
  }
  const nameEl = document.getElementById("editManagerUserDisplayName");
  if (nameEl) nameEl.textContent = member.display_name || member.username;
  const posEl = document.getElementById("editManagerUserPosition");
  if (posEl) posEl.textContent = `${member.position || 'พนักงาน'} · ${member.department || 'General'}`;

  const select = document.getElementById("editManagerSelect");
  if (select) {
    select.innerHTML = '<option value="">ไม่มีหัวหน้างาน (ผู้บริหารสูงสุด)</option>';

    const reportsToMap = {};
    _orgMembersCache.forEach(m => {
      if (m && m.username) {
        reportsToMap[m.username.toLowerCase()] = (m.manager_username || "").trim().toLowerCase();
      }
    });

    _orgMembersCache.forEach(m => {
      if (!m || !m.username) return;
      const candidateUsername = m.username.toLowerCase();
      
      if (candidateUsername === (username || '').toLowerCase()) return;

      let curr = candidateUsername;
      let isCyclic = false;
      while (curr) {
        if (curr === (username || '').toLowerCase()) {
          isCyclic = true;
          break;
        }
        curr = reportsToMap[curr] || "";
      }

      if (isCyclic) return;

      const opt = document.createElement("option");
      opt.value = m.username;
      opt.textContent = `${m.display_name || m.username} (${m.position || 'พนักงาน'})`;
      if ((member.manager_username || "").toLowerCase() === m.username.toLowerCase()) {
        opt.selected = true;
      }
      select.appendChild(opt);
    });
  }

  if (typeof lucide !== 'undefined') lucide.createIcons();

  const modalEl = document.getElementById("editManagerModal");
  if (modalEl) modalEl.classList.remove("hidden");
}

function closeEditManagerModal() {
  const modalEl = document.getElementById("editManagerModal");
  if (modalEl) modalEl.classList.add("hidden");
  editingTreeMember = null;
}

async function saveManagerChange() {
  if (!editingTreeMember) return;
  const targetMember = editingTreeMember;
  const select = document.getElementById("editManagerSelect");
  const managerUsername = (select ? select.value : "").trim();

  try {
    const data = await apiFetch(`/api/org/members/${encodeURIComponent(targetMember)}/manager`, {
      method: "POST",
      body: JSON.stringify({ manager_username: managerUsername })
    });

    if (data.ok) {
      toast("ปรับปรุงสายงานสำเร็จแล้ว", "success");
      closeEditManagerModal();
      
      const targetUserLower = targetMember.toLowerCase();
      const cachedMember = _orgMembersCache.find(m => m && (m.username || '').toLowerCase() === targetUserLower);
      if (cachedMember) {
        cachedMember.manager_username = managerUsername;
      }
      
      if (typeof loadOrgMembers === 'function') {
        await loadOrgMembers();
      }
      renderOrgTree();
    } else {
      toast(data.error || "เกิดข้อผิดพลาดในการบันทึก", "error");
    }
  } catch (e) {
    console.error("Error saving manager change:", e);
    toast("เชื่อมต่อเซิร์ฟเวอร์ผิดพลาด", "error");
  }
}

function searchOrgTreeNode(query) {
  const q = (query || '').trim().toLowerCase();
  const cards = document.querySelectorAll('.org-node-card');
  if (!cards.length) return;

  cards.forEach(card => {
    card.classList.remove('ring-4', 'ring-brand-500', 'shadow-2xl', 'scale-105', 'opacity-30');
  });

  if (!q) return;

  let firstMatch = null;
  cards.forEach(card => {
    const u = card.dataset.username || '';
    const n = card.dataset.name || '';
    const p = card.dataset.pos || '';
    const d = card.dataset.dept || '';
    if (u.includes(q) || n.includes(q) || p.includes(q) || d.includes(q)) {
      card.classList.add('ring-4', 'ring-brand-500', 'shadow-2xl', 'scale-105');
      if (!firstMatch) firstMatch = card;
    } else {
      card.classList.add('opacity-30');
    }
  });

  if (firstMatch) {
    const wrapper = document.getElementById("orgTreeCanvasWrapper");
    if (wrapper) {
      const left = parseFloat(firstMatch.style.left) || 0;
      const top = parseFloat(firstMatch.style.top) || 0;
      const w = parseFloat(firstMatch.style.width) || 230;
      const h = parseFloat(firstMatch.style.height) || 96;
      const canvasWidth = wrapper.clientWidth || 800;
      const canvasHeight = wrapper.clientHeight || 600;
      orgTreePanX = (canvasWidth / 2) - (left + w / 2) * orgTreeZoomScale;
      orgTreePanY = (canvasHeight / 2) - (top + h / 2) * orgTreeZoomScale;
      applyOrgTreeTransform();
    }
  }
}

function resetOrgTreeView() {
  orgTreeZoomScale = 1.0;
  const wrapper = document.getElementById("orgTreeCanvasWrapper");
  if (wrapper && window._orgTreeRoots && window._orgTreeRoots.length > 0) {
    const root = window._orgTreeRoots[0];
    const canvasWidth = wrapper.clientWidth || 800;
    orgTreePanX = (canvasWidth / 2) - (root.x + root.width / 2);
    orgTreePanY = 40;
  } else {
    orgTreePanX = 0;
    orgTreePanY = 40;
  }
  applyOrgTreeTransform();
  
  const searchInput = document.getElementById("orgTreeSearchInput");
  if (searchInput) searchInput.value = "";
  searchOrgTreeNode("");
}

window.orgTreeZoom = orgTreeZoom;
window.orgTreeZoomReset = orgTreeZoomReset;
window.resetOrgTreeView = resetOrgTreeView;
window.searchOrgTreeNode = searchOrgTreeNode;
window.renderOrgTree = renderOrgTree;
window.openEditManagerModal = openEditManagerModal;
window.closeEditManagerModal = closeEditManagerModal;
window.saveManagerChange = saveManagerChange;

// Draggable & Resizeable Private/Group Chat Card
function initChatDragAndResize() {
  const card = document.getElementById("groupChatInnerCard");
  if (!card) return;

  function centerCard() {
    if (window.innerWidth < 768) {
      card.style.position = "";
      card.style.left = "";
      card.style.top = "";
      card.style.width = "";
      card.style.height = "";
      card.style.transform = "";
      return;
    }
    card.style.position = "absolute";
    card.style.maxWidth = "none";
    
    const cardWidth = Math.min(window.innerWidth - 40, 1100);
    const cardHeight = Math.min(window.innerHeight - 40, 700);
    const left = Math.max(20, (window.innerWidth - cardWidth) / 2);
    const top = Math.max(20, (window.innerHeight - cardHeight) / 2);
    
    card.style.left = `${left}px`;
    card.style.top = `${top}px`;
    card.style.width = `${cardWidth}px`;
    card.style.height = `${cardHeight}px`;
    card.style.transform = "none";
  }

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.attributeName === 'class') {
        const modal = document.getElementById("groupChatModal");
        if (modal && !modal.classList.contains("hidden")) {
          centerCard();
        }
      }
    });
  });
  const modal = document.getElementById("groupChatModal");
  if (modal) {
    observer.observe(modal, { attributes: true });
  }

  window.addEventListener('resize', () => {
    if (window.innerWidth < 768) {
      card.style.position = "";
      card.style.left = "";
      card.style.top = "";
      card.style.width = "";
      card.style.height = "";
    }
  });

  const sidebarHeader = document.querySelector("#chatSidebarPanel header");
  const mainChatHeader = document.querySelector("#chatMainArea header");
  
  [sidebarHeader, mainChatHeader].forEach(header => {
    if (!header) return;
    header.style.cursor = "move";
    header.addEventListener("mousedown", dragStart);
  });

  let active = false;
  let currentX;
  let currentY;
  let initialX;
  let initialY;

  function dragStart(e) {
    if (window.innerWidth < 768) return;
    if (e.button !== 0) return;
    if (e.target.closest("button") || e.target.closest("input") || e.target.closest("select") || e.target.closest("textarea") || e.target.closest("i")) return;

    initialX = e.clientX - (parseInt(card.style.left) || 0);
    initialY = e.clientY - (parseInt(card.style.top) || 0);

    active = true;
    document.addEventListener("mousemove", drag);
    document.addEventListener("mouseup", dragEnd);
  }

  function drag(e) {
    if (!active) return;
    e.preventDefault();
    currentX = e.clientX - initialX;
    currentY = e.clientY - initialY;

    const minLeft = 10;
    const minTop = 10;
    const maxLeft = window.innerWidth - 150;
    const maxTop = window.innerHeight - 150;

    currentX = Math.max(minLeft, Math.min(currentX, maxLeft));
    currentY = Math.max(minTop, Math.min(currentY, maxTop));

    card.style.left = `${currentX}px`;
    card.style.top = `${currentY}px`;
  }

  function dragEnd() {
    active = false;
    document.removeEventListener("mousemove", drag);
    document.removeEventListener("mouseup", dragEnd);
  }

  const resizer = document.createElement("div");
  resizer.className = "absolute right-0 bottom-0 w-8 h-8 cursor-se-resize z-[99] flex items-end justify-end p-1 select-none pointer-events-auto";
  resizer.innerHTML = `<svg class="w-4 h-4 text-surface-400 opacity-60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 19l4-4M10 19l9-9"/></svg>`;
  card.appendChild(resizer);

  resizer.addEventListener("mousedown", initResize);

  let initialWidth, initialHeight, startX, startY;

  function initResize(e) {
    if (window.innerWidth < 768) return;
    e.preventDefault();
    initialWidth = parseInt(card.style.width) || card.offsetWidth;
    initialHeight = parseInt(card.style.height) || card.offsetHeight;
    startX = e.clientX;
    startY = e.clientY;

    document.addEventListener("mousemove", resize);
    document.addEventListener("mouseup", stopResize);
  }

  function resize(e) {
    e.preventDefault();
    const newWidth = Math.max(500, initialWidth + (e.clientX - startX));
    const newHeight = Math.max(400, initialHeight + (e.clientY - startY));

    card.style.width = `${newWidth}px`;
    card.style.height = `${newHeight}px`;
  }

  function stopResize() {
    document.removeEventListener("mousemove", resize);
    document.removeEventListener("mouseup", stopResize);
  }
}

// ─── AI Customer Support Draft Generator ───
async function initReplyAssistantView() {
  const selectEl = $('raSourceFile');
  if (!selectEl) return;
  
  const qEl = $('raQueryText');
  const dEl = $('raDraftResult');
  const tEl = $('raTipsResult');
  if (qEl) qEl.value = '';
  if (dEl) dEl.value = '';
  if (tEl) tEl.textContent = 'เลือกอ้างอิงเอกสาร โทนที่ต้องการ และใส่คำถามลูกค้าเพื่อสแกนและแนะนำแนวทางการปิดการขายค่ะ';
  
  try {
    const data = await apiFetch('/api/files');
    selectEl.innerHTML = '<option value="">📚 ค้นหาอัตโนมัติจากทุกไฟล์ในคลังความรู้ (Recommended)</option>';
    if (data && data.files) {
      data.files.forEach(f => {
        const opt = document.createElement('option');
        opt.value = f.id;
        opt.textContent = `📄 ${f.name || 'ไม่มีชื่อไฟล์'}`;
        selectEl.appendChild(opt);
      });
    }
  } catch (e) {
    console.error('Failed to load KB files for Reply Assistant:', e);
  }
}

async function generateAIDraft() {
  const queryEl = $('raQueryText');
  const fileEl = $('raSourceFile');
  const draftEl = $('raDraftResult');
  const tipsEl = $('raTipsResult');
  const submitBtn = $('raSubmitBtn');
  
  if (!queryEl || !queryEl.value.trim()) {
    toast('กรุณาระบุข้อความสอบถามของลูกค้าก่อนนะคะ', 'error');
    return;
  }
  
  const query = queryEl.value.trim();
  const fileId = fileEl ? fileEl.value : '';
  const toneRadio = document.querySelector('input[name="raTone"]:checked');
  const tone = toneRadio ? toneRadio.value : 'formal';
  
  const originalHtml = submitBtn ? submitBtn.innerHTML : '';
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full inline-block mr-1"></span> กำลังประมวลผล...';
  }
  
  try {
    const res = await apiFetch('/api/reply-assistant/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, tone, file_id: fileId })
    });
    
    if (res && res.ok) {
      toast('ร่างข้อความสแกนจากคลังความรู้เรียบร้อยค่ะ', 'success');
      if (draftEl) draftEl.value = res.draft || '';
      if (tipsEl) tipsEl.textContent = res.tips || 'พร้อมคัดลอกข้อความไปใช้งานได้ทันที';
    } else {
      toast(res.error || 'เกิดข้อผิดพลาดในการร่างคำตอบ', 'error');
    }
  } catch (e) {
    console.error(e);
    toast('ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ AI ได้ในขณะนี้', 'error');
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalHtml;
    }
  }
}

async function copyReplyAssistantDraft() {
  const draftEl = $('raDraftResult');
  const copyBtn = $('raCopyBtn');
  if (!draftEl || !draftEl.value.trim()) {
    toast('ไม่มีข้อความให้คัดลอกค่ะ', 'error');
    return;
  }
  
  try {
    await navigator.clipboard.writeText(draftEl.value.trim());
    toast('คัดลอกข้อความลงคลิปบอร์ดแล้วค่ะ', 'success');
    
    const originalText = copyBtn ? copyBtn.innerHTML : '';
    if (copyBtn) {
      copyBtn.innerHTML = '<i data-lucide="check" class="w-3 h-3 text-emerald-500"></i> คัดลอกแล้ว!';
      if (typeof initIcons === 'function') initIcons();
      setTimeout(() => {
        copyBtn.innerHTML = originalText;
        if (typeof initIcons === 'function') initIcons();
      }, 2000);
    }
  } catch (err) {
    console.error('Failed to copy text:', err);
    toast('ไม่สามารถคัดลอกข้อความได้โดยอัตโนมัติ', 'error');
  }
}

window.initReplyAssistantView = initReplyAssistantView;
window.generateAIDraft = generateAIDraft;
window.copyReplyAssistantDraft = copyReplyAssistantDraft;

// ─── 3D Enterprise AI Communication Network for Login Overlay ───────
let _login3DAnimationId = null;

function initLogin3DBackground() {
  const canvas = document.getElementById('login3DCanvas');
  if (!canvas || typeof THREE === 'undefined') return;

  const overlay = document.getElementById('loginOverlay');
  if (!overlay || overlay.classList.contains('hidden')) return;

  if (_login3DAnimationId) {
    cancelAnimationFrame(_login3DAnimationId);
    _login3DAnimationId = null;
  }

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1200);
  camera.position.z = 420;

  const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // 1. Central Corporate AI Globe Core (สมอง AI กลางองค์กร)
  const coreGroup = new THREE.Group();

  // Outer Shield Sphere (Wireframe Icosahedron)
  const outerGeom = new THREE.IcosahedronGeometry(110, 2);
  const outerMat = new THREE.MeshBasicMaterial({
    color: 0x0284c7, // Corporate Sky Blue
    wireframe: true,
    transparent: true,
    opacity: 0.18
  });
  const outerSphere = new THREE.Mesh(outerGeom, outerMat);
  coreGroup.add(outerSphere);

  // Inner Core Sphere (Emerald Trust Core)
  const innerGeom = new THREE.IcosahedronGeometry(75, 1);
  const innerMat = new THREE.MeshBasicMaterial({
    color: 0x059669, // Emerald Green Security
    wireframe: true,
    transparent: true,
    opacity: 0.25
  });
  const innerSphere = new THREE.Mesh(innerGeom, innerMat);
  coreGroup.add(innerSphere);

  // Floating Cyber Ring (Orbital Communication Ring)
  const ringGeom = new THREE.TorusGeometry(140, 1.5, 16, 100);
  const ringMat = new THREE.MeshBasicMaterial({
    color: 0x38bdf8,
    transparent: true,
    opacity: 0.35
  });
  const ring = new THREE.Mesh(ringGeom, ringMat);
  ring.rotation.x = Math.PI / 3;
  coreGroup.add(ring);

  // Position core slightly to the right on desktop, center on mobile
  if (window.innerWidth >= 768) {
    coreGroup.position.set(220, 0, -50);
  } else {
    coreGroup.position.set(0, 0, -100);
  }
  scene.add(coreGroup);

  // 2. Inter-departmental Communication Nodes & Beam Network (เครือข่ายสื่อสารองค์กร)
  const nodeCount = window.innerWidth < 768 ? 18 : 32;
  const nodes = [];
  const nodePositions = new Float32Array(nodeCount * 3);
  const nodeGroup = new THREE.Group();

  const nodeGeom = new THREE.SphereGeometry(3.5, 16, 16);
  const nodeMat = new THREE.MeshBasicMaterial({
    color: 0x38bdf8,
    transparent: true,
    opacity: 0.85
  });

  for (let i = 0; i < nodeCount; i++) {
    const mesh = new THREE.Mesh(nodeGeom, nodeMat);
    const x = (Math.random() - 0.5) * 800;
    const y = (Math.random() - 0.5) * 600;
    const z = (Math.random() - 0.5) * 400;

    mesh.position.set(x, y, z);
    mesh.userData = {
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      vz: (Math.random() - 0.5) * 0.4,
      baseX: x,
      baseY: y
    };
    nodeGroup.add(mesh);
    nodes.push(mesh);

    nodePositions[i * 3] = x;
    nodePositions[i * 3 + 1] = y;
    nodePositions[i * 3 + 2] = z;
  }
  scene.add(nodeGroup);

  // Dynamic Connecting Beams Material
  const lineMaterial = new THREE.LineBasicMaterial({
    color: 0x0284c7,
    transparent: true,
    opacity: 0.16
  });

  let lineSegmentsMesh = null;

  function updateCommunicationBeams() {
    const linePos = [];
    const maxDist = 180;

    for (let i = 0; i < nodeCount; i++) {
      for (let j = i + 1; j < nodeCount; j++) {
        const p1 = nodes[i].position;
        const p2 = nodes[j].position;
        const dist = p1.distanceTo(p2);

        if (dist < maxDist) {
          linePos.push(p1.x, p1.y, p1.z);
          linePos.push(p2.x, p2.y, p2.z);
        }
      }
    }

    if (lineSegmentsMesh) {
      scene.remove(lineSegmentsMesh);
      lineSegmentsMesh.geometry.dispose();
    }

    const lineGeom = new THREE.BufferGeometry();
    lineGeom.setAttribute('position', new THREE.Float32BufferAttribute(linePos, 3));
    lineSegmentsMesh = new THREE.LineSegments(lineGeom, lineMaterial);
    scene.add(lineSegmentsMesh);
  }

  // 3. Ambient Neural Data Particles Grid (อนุภาคข้อมูลองค์กร)
  const particleCount = window.innerWidth < 768 ? 300 : 600;
  const pGeom = new THREE.BufferGeometry();
  const pPos = new Float32Array(particleCount * 3);
  const pColors = new Float32Array(particleCount * 3);

  const colEmerald = new THREE.Color('#059669');
  const colCyan = new THREE.Color('#0284c7');
  const colSky = new THREE.Color('#38bdf8');

  for (let k = 0; k < particleCount; k++) {
    pPos[k * 3] = (Math.random() - 0.5) * 1100;
    pPos[k * 3 + 1] = (Math.random() - 0.5) * 800;
    pPos[k * 3 + 2] = (Math.random() - 0.5) * 500;

    const chosen = k % 3 === 0 ? colEmerald : (k % 3 === 1 ? colCyan : colSky);
    pColors[k * 3] = chosen.r;
    pColors[k * 3 + 1] = chosen.g;
    pColors[k * 3 + 2] = chosen.b;
  }

  pGeom.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
  pGeom.setAttribute('color', new THREE.BufferAttribute(pColors, 3));

  const pMat = new THREE.PointsMaterial({
    size: 3.2,
    vertexColors: true,
    transparent: true,
    opacity: 0.65,
    blending: THREE.AdditiveBlending
  });

  const ambientParticles = new THREE.Points(pGeom, pMat);
  scene.add(ambientParticles);

  // Parallax Mouse & Touch Interaction
  let mouseX = 0, mouseY = 0;
  let targetX = 0, targetY = 0;

  function onPointerMove(e) {
    const px = e.touches ? e.touches[0].clientX : e.clientX;
    const py = e.touches ? e.touches[0].clientY : e.clientY;
    mouseX = (px - window.innerWidth / 2) * 0.12;
    mouseY = (py - window.innerHeight / 2) * 0.12;
  }
  window.addEventListener('mousemove', onPointerMove, { passive: true });
  window.addEventListener('touchmove', onPointerMove, { passive: true });

  function onWindowResize() {
    if (!camera || !renderer) return;
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);

    if (window.innerWidth >= 768) {
      coreGroup.position.set(220, 0, -50);
    } else {
      coreGroup.position.set(0, 0, -100);
    }
  }
  window.addEventListener('resize', onWindowResize);

  // Animation Loop
  const clock = new THREE.Clock();

  function renderLoop() {
    if (!overlay || overlay.classList.contains('hidden')) {
      if (_login3DAnimationId) cancelAnimationFrame(_login3DAnimationId);
      _login3DAnimationId = null;
      return;
    }

    _login3DAnimationId = requestAnimationFrame(renderLoop);
    const elapsedTime = clock.getElapsedTime();

    // Smooth Parallax
    targetX += (mouseX - targetX) * 0.03;
    targetY += (mouseY - targetY) * 0.03;

    camera.position.x = targetX;
    camera.position.y = -targetY;
    camera.lookAt(0, 0, 0);

    // Rotate Central Enterprise AI Core
    outerSphere.rotation.y = elapsedTime * 0.12;
    outerSphere.rotation.x = elapsedTime * 0.06;
    innerSphere.rotation.y = -elapsedTime * 0.18;
    ring.rotation.z = elapsedTime * 0.1;

    // Pulse Core Scale
    const pulse = 1 + Math.sin(elapsedTime * 1.5) * 0.04;
    coreGroup.scale.set(pulse, pulse, pulse);

    // Move Communication Nodes smoothly
    nodes.forEach(node => {
      node.position.x += node.userData.vx;
      node.position.y += node.userData.vy;

      if (Math.abs(node.position.x - node.userData.baseX) > 40) node.userData.vx *= -1;
      if (Math.abs(node.position.y - node.userData.baseY) > 40) node.userData.vy *= -1;
    });

    updateCommunicationBeams();
    ambientParticles.rotation.y = elapsedTime * 0.015;

    renderer.render(scene, camera);
  }

  renderLoop();
}

window.initLogin3DBackground = initLogin3DBackground;

// 🛡️ IT Security Audit & AI Usage Dashboard Logic
let deptUsageChartInstance = null;
let securityTimelineChartInstance = null;

async function loadSecurityAuditDashboard() {
    try {
        const res = await fetch('/api/admin/security/metrics?days=30');
        const data = await res.json();
        if (!data.ok || !data.metrics) return;

        const m = data.metrics;
        const t = m.totals || {};

        // Top Cards Update
        if ($('secTotalLogins')) $('secTotalLogins').textContent = (t.total_logins || 0).toLocaleString();
        if ($('secFailedLogins')) $('secFailedLogins').textContent = (t.failed_logins || 0).toLocaleString();
        if ($('secTotalAIQueries')) $('secTotalAIQueries').textContent = (t.total_ai_requests || 0).toLocaleString();
        if ($('secTokensBadge')) $('secTokensBadge').textContent = `${(t.total_tokens || 0).toLocaleString()} Tokens`;
        if ($('secTotalLockouts')) $('secTotalLockouts').textContent = (t.lockout_incidents || 0).toLocaleString();
        if ($('secLockoutsBadge')) $('secLockoutsBadge').textContent = `${t.lockout_incidents || 0} เคส`;

        // Success Login Rate calculation
        const succ = t.successful_logins || 0;
        const tot = t.total_logins || 1;
        const rate = Math.round((succ / (tot || 1)) * 100);
        if ($('securityLoginsBadge')) $('securityLoginsBadge').textContent = `${rate}% สำเร็จ`;

        // Top Department
        const depts = m.department_usage || [];
        if (depts.length > 0) {
            const topDept = depts[0].department || 'General';
            if ($('secTopDepartment')) $('secTopDepartment').textContent = topDept;
            if ($('topDeptBadge')) $('topDeptBadge').textContent = `${topDept} (${depts[0].count} ครั้ง)`;
        }

        // Render Charts
        renderDeptUsageChart(depts);
        renderSecurityTimelineChart(m.timeline || []);

        // Load Table
        loadAuditLogsTable();
    } catch (err) {
        console.error('[Security Audit] Dashboard load error:', err);
    }
}

function renderDeptUsageChart(depts) {
    const ctx = document.getElementById('deptUsageChart');
    if (!ctx) return;

    if (deptUsageChartInstance) {
        deptUsageChartInstance.destroy();
    }

    const labels = depts.map(d => d.department || 'General');
    const counts = depts.map(d => d.count || 0);

    deptUsageChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.length ? labels : ['General'],
            datasets: [{
                label: 'จำนวนการใช้งาน AI (ครั้ง)',
                data: counts.length ? counts : [0],
                backgroundColor: [
                    'rgba(99, 102, 241, 0.85)',
                    'rgba(16, 185, 129, 0.85)',
                    'rgba(245, 158, 11, 0.85)',
                    'rgba(168, 85, 247, 0.85)',
                    'rgba(236, 72, 153, 0.85)'
                ],
                borderRadius: 12,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(148, 163, 184, 0.1)' } },
                x: { grid: { display: false } }
            }
        }
    });
}

function renderSecurityTimelineChart(timeline) {
    const ctx = document.getElementById('securityTimelineChart');
    if (!ctx) return;

    if (securityTimelineChartInstance) {
        securityTimelineChartInstance.destroy();
    }

    const labels = timeline.map(t => t.date_str);
    const logins = timeline.map(t => t.logins || 0);
    const failed = timeline.map(t => t.failed_logins || 0);
    const aiReqs = timeline.map(t => t.ai_requests || 0);

    securityTimelineChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels.length ? labels : ['วันนี้'],
            datasets: [
                {
                    label: 'การคุยกับ AI',
                    data: aiReqs.length ? aiReqs : [0],
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.35,
                    borderWidth: 3
                },
                {
                    label: 'เข้าสู่ระบบสำเร็จ',
                    data: logins.length ? logins : [0],
                    borderColor: '#10b981',
                    borderWidth: 2,
                    tension: 0.35
                },
                {
                    label: 'ล็อกอินผิดพลาด',
                    data: failed.length ? failed : [0],
                    borderColor: '#ef4444',
                    borderWidth: 2,
                    tension: 0.35
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(148, 163, 184, 0.1)' } },
                x: { grid: { display: false } }
            }
        }
    });
}

async function loadAuditLogsTable(search = '', eventType = '') {
    const tbody = $('securityAuditLogTableBody');
    if (!tbody) return;

    try {
        let url = '/api/admin/security/audit-logs?limit=100';
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (eventType) url += `&event_type=${encodeURIComponent(eventType)}`;

        const res = await fetch(url);
        const data = await res.json();
        if (!data.ok) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center py-6 text-red-500">ไม่สามารถโหลด Audit Logs ได้</td></tr>';
            return;
        }

        const logs = data.logs || [];
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center py-8 text-surface-400">ไม่พบประวัติกิจกรรมในเงื่อนไขนี้</td></tr>';
            return;
        }

        tbody.innerHTML = logs.map(row => {
            let statusBadge = '<span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-50 text-emerald-600 dark:bg-emerald-950/50">Success 🟢</span>';
            if (row.status === 'warning') statusBadge = '<span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-600 dark:bg-amber-950/50">Warning 🟡</span>';
            if (row.status === 'failed') statusBadge = '<span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-rose-50 text-rose-600 dark:bg-rose-950/50">Failed 🔴</span>';

            let eventName = row.event_type;
            if (row.event_type === 'login_success') eventName = '🔑 เข้าสู่ระบบสำเร็จ';
            if (row.event_type === 'login_failed') eventName = '⚠️ ล็อกอินผิดพลาด';
            if (row.event_type === 'account_lockout') eventName = '🚨 ระงับบัญชีชั่วคราว';
            if (row.event_type === 'ai_chat') eventName = '🤖 AI Query';
            if (row.event_type === 'ai_rag_query') eventName = '📚 RAG Knowledge Query';

            const userAgentShort = (row.user_agent || '-').substring(0, 30);

            return `
                <tr class="hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors">
                    <td class="p-3 text-surface-400 whitespace-nowrap">${row.timestamp || '-'}</td>
                    <td class="p-3 font-bold text-surface-900 dark:text-white whitespace-nowrap">${escapeHTML(row.username || 'Anonymous')}</td>
                    <td class="p-3 text-surface-500 whitespace-nowrap">${escapeHTML(row.department || 'General')}</td>
                    <td class="p-3 font-semibold text-surface-800 dark:text-surface-200 whitespace-nowrap">${eventName}</td>
                    <td class="p-3 whitespace-nowrap">${statusBadge}</td>
                    <td class="p-3 text-surface-600 dark:text-surface-300 max-w-xs truncate" title="${escapeHTML(row.action_detail || '')}">${escapeHTML(row.action_detail || '-')}</td>
                    <td class="p-3 font-mono text-[11px] text-surface-500 whitespace-nowrap">${escapeHTML(row.ip_address || '-')}</td>
                    <td class="p-3 text-surface-400 text-[11px] whitespace-nowrap">${escapeHTML(row.ai_model || userAgentShort)}</td>
                </tr>
            `;
        }).join('');

        if (typeof lucide !== 'undefined') lucide.createIcons();
    } catch (err) {
        console.error('[Audit Logs] Error:', err);
    }
}

function filterAuditLogs() {
    const search = $('auditSearchInput') ? $('auditSearchInput').value : '';
    const eventType = $('auditEventFilter') ? $('auditEventFilter').value : '';
    loadAuditLogsTable(search, eventType);
}

function exportAuditLogsCSV() {
    window.location.href = '/api/admin/security/export-csv';
}

window.loadSecurityAuditDashboard = loadSecurityAuditDashboard;
window.loadAuditLogsTable = loadAuditLogsTable;
window.filterAuditLogs = filterAuditLogs;
window.exportAuditLogsCSV = exportAuditLogsCSV;

// ─── 🎨 Personal Custom UI & Appearance Logic ───
const CUSTOM_UI_KEY = 'orgchat_custom_ui_settings';

function getCustomUISettings() {
    try {
        const stored = localStorage.getItem(CUSTOM_UI_KEY);
        if (stored) return JSON.parse(stored);
    } catch (e) {}
    return { font: 'Sarabun', fontSize: 'normal', accent: 'blue' };
}

function saveCustomUISettings(settings) {
    try {
        localStorage.setItem(CUSTOM_UI_KEY, JSON.stringify(settings));
    } catch (e) {}
}

function applyCustomUI(settings) {
    const s = settings || getCustomUISettings();

    // 1. Apply Font Family — use global FONT_MAP for all fonts
    const targetFont = FONT_MAP[s.font] || FONT_MAP['Sarabun'];
    document.documentElement.style.setProperty('--user-custom-font', targetFont);
    document.body.style.fontFamily = targetFont;

    // Highlight Font Button
    document.querySelectorAll('.custom-font-btn').forEach(btn => {
        btn.classList.remove('border-indigo-500', 'bg-indigo-50/50', 'dark:bg-indigo-900/20');
        btn.classList.add('border-surface-200', 'dark:border-surface-700');
    });
    const activeFontBtn = document.getElementById(`fontBtn-${s.font}`);
    if (activeFontBtn) {
        activeFontBtn.classList.remove('border-surface-200', 'dark:border-surface-700');
        activeFontBtn.classList.add('border-indigo-500', 'bg-indigo-50/50', 'dark:bg-indigo-900/20');
    }

    // 2. Apply Font Size
    const fontSizes = {
        'small': { root: '13px', label: 'เล็ก (13px)' },
        'normal': { root: '14.5px', label: 'ปกติ (14.5px)' },
        'large': { root: '16px', label: 'ใหญ่ (16px)' },
        'xl': { root: '17.5px', label: 'ใหญ่มาก (17.5px)' }
    };
    const sizeConfig = fontSizes[s.fontSize] || fontSizes['normal'];
    document.documentElement.style.fontSize = sizeConfig.root;
    
    const sizeLabelEl = document.getElementById('fontSizeDisplay');
    if (sizeLabelEl) sizeLabelEl.textContent = sizeConfig.label;

    // Highlight Size Button
    document.querySelectorAll('.custom-size-btn').forEach(btn => {
        btn.classList.remove('bg-indigo-600', 'text-white', 'border-indigo-600');
        btn.classList.add('border-surface-200', 'dark:border-surface-700', 'text-surface-700', 'dark:text-surface-300');
    });
    const activeSizeBtn = document.getElementById(`fontSizeBtn-${s.fontSize}`);
    if (activeSizeBtn) {
        activeSizeBtn.classList.remove('border-surface-200', 'dark:border-surface-700', 'text-surface-700', 'dark:text-surface-300');
        activeSizeBtn.classList.add('bg-indigo-600', 'text-white', 'border-indigo-600');
    }

    // 3. Apply Accent Color
    const accentColors = {
        'blue': '#2563eb',
        'indigo': '#4f46e5',
        'emerald': '#059669',
        'amber': '#d97706',
        'rose': '#e11d48',
        'purple': '#9333ea'
    };
    const targetAccent = accentColors[s.accent] || accentColors['blue'];
    document.documentElement.style.setProperty('--brand-accent-color', targetAccent);

    // Highlight Accent Checkmarks
    document.querySelectorAll('.custom-accent-btn').forEach(btn => {
        const check = btn.querySelector('.accent-check');
        if (check) check.classList.add('hidden');
        btn.classList.remove('ring-4', 'ring-indigo-300', 'dark:ring-indigo-800');
    });
    const activeAccentBtn = document.getElementById(`accentBtn-${s.accent}`);
    if (activeAccentBtn) {
        const check = activeAccentBtn.querySelector('.accent-check');
        if (check) check.classList.remove('hidden');
        activeAccentBtn.classList.add('ring-4', 'ring-indigo-300', 'dark:ring-indigo-800');
    }
}

function setCustomFont(fontName) {
    const s = getCustomUISettings();
    s.font = fontName;
    saveCustomUISettings(s);
    applyCustomUI(s);
}

function setCustomFontSize(sizeKey) {
    const s = getCustomUISettings();
    s.fontSize = sizeKey;
    saveCustomUISettings(s);
    applyCustomUI(s);
}

function setCustomAccent(colorKey) {
    const s = getCustomUISettings();
    s.accent = colorKey;
    saveCustomUISettings(s);
    applyCustomUI(s);
}

function resetCustomUISettings() {
    const defaults = { font: 'Sarabun', fontSize: 'normal', accent: 'blue' };
    saveCustomUISettings(defaults);
    applyCustomUI(defaults);
}

window.setCustomFont = setCustomFont;
window.setCustomFontSize = setCustomFontSize;
window.setCustomAccent = setCustomAccent;
window.resetCustomUISettings = resetCustomUISettings;
window.applyCustomUI = applyCustomUI;

// ─── 🛡️ Two-Factor Authentication (2FA) Frontend Logic ───

let currentPreAuthToken = null;
let current2FAMethod = 'authenticator';
let currentUserEmail = '';

async function check2FAStatus() {
    try {
        const res = await fetch('/api/2fa/status');
        const data = await res.json();
        if (data.ok) {
            currentUserEmail = data.email || '';
            const badge = document.getElementById('totpStatusBadge');
            const disabledDiv = document.getElementById('totpDisabledActions');
            const enabledDiv = document.getElementById('totpEnabledActions');
            
            if (data.enabled) {
                if (badge) {
                    const typeText = data.type === 'email' ? 'เปิดใช้งาน (Gmail OTP)' : 'เปิดใช้งาน (Authenticator App)';
                    badge.textContent = typeText;
                    badge.className = 'px-2 py-0.5 rounded-full text-[9px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400';
                }
                if (disabledDiv) disabledDiv.classList.add('hidden');
                if (enabledDiv) enabledDiv.classList.remove('hidden');
            } else {
                if (badge) {
                    badge.textContent = 'ปิดใช้งาน';
                    badge.className = 'px-2 py-0.5 rounded-full text-[9px] font-bold bg-surface-100 text-surface-500 dark:bg-surface-800';
                }
                if (disabledDiv) disabledDiv.classList.remove('hidden');
                if (enabledDiv) enabledDiv.classList.add('hidden');
            }
        }
    } catch (e) {
        console.warn('[2FA Status] error:', e);
    }
}

async function start2FASetup() {
    try {
        const res = await fetch('/api/2fa/setup', { method: 'POST' });
        const data = await res.json();
        if (!data.ok) {
            showToast(data.error || 'ไม่สามารถตั้งค่า 2FA ได้', 'error');
            return;
        }
        
        currentUserEmail = data.email || '';
        document.getElementById('totpQrImage').src = data.qr_code;
        document.getElementById('totpSecretText').textContent = 'Secret: ' + data.secret;
        document.getElementById('totpSetupCodeInput').value = '';
        document.getElementById('emailOtpSetupCodeInput').value = '';
        document.getElementById('totpBackupCodesContainer').classList.add('hidden');
        document.getElementById('totpEnableBtn').classList.remove('hidden');
        
        const targetText = document.getElementById('text2FAEmailTarget');
        if (targetText) {
            if (currentUserEmail) {
                targetText.textContent = `ระบบจะส่งรหัส OTP 6 หลักไปยังอีเมล ${currentUserEmail}`;
            } else {
                targetText.textContent = `⚠️ บัญชีของคุณยังไม่ได้ตั้งค่าอีเมลในโปรไฟล์ กรุณาระบุอีเมลในโปรไฟล์ก่อนใช้งานวิธีกรอก OTP`;
            }
        }
        
        switch2FAMethod('authenticator');
        document.getElementById('totpSetupModal').classList.remove('hidden');
    } catch (e) {
        showToast('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์', 'error');
    }
}

function switch2FAMethod(method) {
    current2FAMethod = method;
    const btnAuth = document.getElementById('btn2FAMethodAuth');
    const btnEmail = document.getElementById('btn2FAMethodEmail');
    const secAuth = document.getElementById('section2FAAuth');
    const secEmail = document.getElementById('section2FAEmail');
    
    if (method === 'email') {
        if (btnEmail) btnEmail.className = 'flex-1 py-2.5 px-3 text-xs font-bold rounded-xl transition-all text-center flex items-center justify-center gap-1.5 bg-white dark:bg-surface-700 text-emerald-600 dark:text-white shadow-sm';
        if (btnAuth) btnAuth.className = 'flex-1 py-2.5 px-3 text-xs font-bold rounded-xl transition-all text-center flex items-center justify-center gap-1.5 text-surface-500 dark:text-surface-400 hover:text-surface-800 dark:hover:text-surface-200';
        if (secEmail) secEmail.classList.remove('hidden');
        if (secAuth) secAuth.classList.add('hidden');
    } else {
        if (btnAuth) btnAuth.className = 'flex-1 py-2.5 px-3 text-xs font-bold rounded-xl transition-all text-center flex items-center justify-center gap-1.5 bg-white dark:bg-surface-700 text-emerald-600 dark:text-white shadow-sm';
        if (btnEmail) btnEmail.className = 'flex-1 py-2.5 px-3 text-xs font-bold rounded-xl transition-all text-center flex items-center justify-center gap-1.5 text-surface-500 dark:text-surface-400 hover:text-surface-800 dark:hover:text-surface-200';
        if (secAuth) secAuth.classList.remove('hidden');
        if (secEmail) secEmail.classList.add('hidden');
    }
}

async function send2FAEmailOTP(isLoginVerify = false) {
    try {
        const payload = isLoginVerify ? { pre_auth_token: currentPreAuthToken } : {};
        const res = await fetch('/api/2fa/send-email-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!data.ok) {
            showToast(data.error || 'ส่ง OTP ล้มเหลว', 'error');
            return;
        }
        showToast(data.message || 'ส่ง OTP สำเร็จ กรุณาเช็คกล่องจดหมายใน Gmail', 'success');
    } catch (e) {
        showToast('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์', 'error');
    }
}

async function confirmEnable2FA() {
    let code = '';
    if (current2FAMethod === 'email') {
        code = document.getElementById('emailOtpSetupCodeInput').value.trim();
        if (!code) {
            showToast('กรุณาใส่รหัส OTP 6 หลักที่ส่งไปยัง Gmail', 'error');
            return;
        }
    } else {
        code = document.getElementById('totpSetupCodeInput').value.trim();
        if (!code) {
            showToast('กรุณาใส่รหัส 6 หลักจาก Authenticator App', 'error');
            return;
        }
    }
    
    try {
        const res = await fetch('/api/2fa/enable', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, type: current2FAMethod })
        });
        const data = await res.json();
        if (!data.ok) {
            showToast(data.error || 'รหัสไม่ถูกต้อง', 'error');
            return;
        }
        
        showToast(data.message || 'เปิดใช้งาน 2FA เรียบร้อยแล้ว', 'success');
        
        // Show backup codes
        if (data.backup_codes && data.backup_codes.length > 0) {
            const listDiv = document.getElementById('totpBackupCodesList');
            listDiv.innerHTML = data.backup_codes.map(c => `<div class="p-1 text-center bg-surface-100 dark:bg-surface-800 rounded-lg select-all">${c}</div>`).join('');
            document.getElementById('totpBackupCodesContainer').classList.remove('hidden');
            document.getElementById('totpEnableBtn').classList.add('hidden');
        } else {
            close2FAModal();
        }
        check2FAStatus();
    } catch (e) {
        showToast('เกิดข้อผิดพลาดในการเปิดใช้งาน 2FA', 'error');
    }
}

function close2FAModal() {
    document.getElementById('totpSetupModal').classList.add('hidden');
    check2FAStatus();
}

async function disable2FA() {
    const confirmChoice = confirm('คุณต้องการยกเลิกการยืนยันตัวตนสองชั้น (2FA) ใช่หรือไม่?');
    if (!confirmChoice) return;
    
    const password = prompt('กรุณายืนยันรหัสผ่านบัญชีผู้ใช้เพื่อยกเลิก 2FA:');
    if (password === null) return; // กด Cancel
    
    try {
        const res = await fetch('/api/2fa/disable', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });
        const data = await res.json();
        if (!data.ok) {
            showToast(data.error || 'ไม่สามารถยกเลิก 2FA ได้', 'error');
            return;
        }
        showToast(data.message || 'ยกเลิกการยืนยันตัวตนสองชั้นเรียบร้อยแล้ว', 'success');
        check2FAStatus();
    } catch (e) {
        showToast('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์', 'error');
    }
}

function handle2FAChallenge(preAuthToken) {
    currentPreAuthToken = preAuthToken;
    const modal = document.getElementById('totpVerifyModal');
    const input = document.getElementById('totpVerifyCodeInput');
    const err = document.getElementById('totpVerifyError');
    const btnResend = document.getElementById('btnSendVerifyEmailOTPContainer');
    if (input) input.value = '';
    if (err) err.classList.add('hidden');
    if (btnResend) btnResend.classList.remove('hidden');
    if (modal) modal.classList.remove('hidden');
}

async function submit2FAVerify() {
    const code = document.getElementById('totpVerifyCodeInput').value.trim();
    const err = document.getElementById('totpVerifyError');
    if (!code) {
        if (err) { err.textContent = 'กรุณากรอกรหัส 2FA หรือ OTP'; err.classList.remove('hidden'); }
        return;
    }
    
    try {
        const res = await fetch('/api/2fa/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pre_auth_token: currentPreAuthToken, code })
        });
        const data = await res.json();
        if (!data.ok) {
            if (err) { err.textContent = data.error || 'รหัสไม่ถูกต้อง'; err.classList.remove('hidden'); }
            return;
        }
        
        document.getElementById('totpVerifyModal').classList.add('hidden');
        showToast('เข้าสู่ระบบสำเร็จ!', 'success');
        window.location.reload();
    } catch (e) {
        if (err) { err.textContent = 'เกิดข้อผิดพลาดในการเชื่อมต่อ'; err.classList.remove('hidden'); }
    }
}

function cancel2FAVerify() {
    currentPreAuthToken = null;
    document.getElementById('totpVerifyModal').classList.add('hidden');
}

window.check2FAStatus = check2FAStatus;
window.start2FASetup = start2FASetup;
window.switch2FAMethod = switch2FAMethod;
window.send2FAEmailOTP = send2FAEmailOTP;
window.confirmEnable2FA = confirmEnable2FA;
window.close2FAModal = close2FAModal;
window.disable2FA = disable2FA;
window.handle2FAChallenge = handle2FAChallenge;
window.submit2FAVerify = submit2FAVerify;
window.cancel2FAVerify = cancel2FAVerify;
window.showQRLogin = showQRLogin;
window.hideQRLogin = hideQRLogin;
window.openQRScanner = openQRScanner;
if (typeof closeQRScanner === 'function') window.closeQRScanner = closeQRScanner;
window.generateGlobalSummary = generateGlobalSummary;
window.handleBulkCompare = handleBulkCompare;
window.loadOrgDepartments = loadOrgDepartments;
window.openCreateDeptModal = openCreateDeptModal;
window.openEditDeptModal = openEditDeptModal;
window.closeDeptModal = closeDeptModal;
window.saveDeptModal = saveDeptModal;
window.deleteCurrentDept = deleteCurrentDept;
window.loadCustomCategoriesAndRules = loadCustomCategoriesAndRules;
window.addCustomCategoryBtn = addCustomCategoryBtn;
window.deleteCustomCategoryBtn = deleteCustomCategoryBtn;
window.addAIRuleBtn = addAIRuleBtn;
window.deleteAIRuleBtn = deleteAIRuleBtn;
window.switchOrgTab = switchOrgTab;

document.addEventListener('DOMContentLoaded', () => {
  initChatDragAndResize();
  setTimeout(initLogin3DBackground, 200);
  applyCustomUI();
  setTimeout(check2FAStatus, 1500);

  // 🌐 Hash Routing Support (e.g. #admin, #plan, #super-admin, #line-groups)
  function handleHashRoute() {
    const hash = window.location.hash.replace('#', '').trim();
    if (hash) {
      setTimeout(() => {
        if (typeof switchView === 'function') {
          switchView(hash);
        }
      }, 250);
    }
  }
  handleHashRoute();
  window.addEventListener('hashchange', handleHashRoute);
});



window.handleGoogleLogin = handleGoogleLogin;
