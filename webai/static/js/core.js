// --- OrgChat AI: CORE Module ---

console.log("static/app.js starting...");

// ─── State ───────────────────────────────────
const state = {
  history: [],          // [{role:'user'|'bot', text}]
  sending: false,
  apiKeySet: false,
  calendar: {
    viewDate: new Date(),
    schedules: [],
    searchQuery: '',
    categoryFilter: 'all'
  },

  groupChat: {
    messages: [],
    lastId: 0,
    isOpen: false,
    pollInterval: null,
    pendingFiles: [],
    unreadCounts: { rooms: {}, dms: {} },
    replyTo: null
  },
  feedPollInterval: null,
  currentChat: { type: null, id: null, name: null },
  chatList: { rooms: [], contacts: [] },
  isAdmin: false,
  isSuperAdmin: false,
  canViewKB: false,
  canEditKB: false,
  canDeleteKB: false,
  canViewFinancial: false,
  canManageLeave: false,
  canBroadcastLine: false,
  canManagePeak: false,
  canUseAI: true,
  canClaimExpense: true,
  hasOrg: false,
  orgId: null,
  isOrgAdmin: false,

  kbCategories: [],
  allUsers: [],
  appSettings: {},
  personas: [],
  activePersona: null,
  postViews: {},
  lastRendered: { chatList: '', messages: '', unread: '', sidebar: '' },
  theme: localStorage.getItem('theme') || 'auto',
  sidebarFilter: 'all',
  sidebarSearch: '',
  analyzedWaveforms: new Map(),
  onlineUsers: [],      // List of usernames
  serverOffset: 0,      // ms offset (server - client)
  drive: {
    currentFolderId: 'root',
    history: [], // [{id, name}]
    isLoading: false
  }
};

// ─── DOM Refs ────────────────────────────────
let editingScheduleId = null;

const $ = (id) => {
  const el = document.getElementById(id);
  // if (!el) console.warn(`Element with ID "${id}" not found.`);
  return el;
};
window.$ = $;

// Persona Refs
const personaBtn = $('personaBtn');

const personaDropdown = $('personaDropdown');

const personaList = $('personaList');

const activePersonaName = $('activePersonaName');

const closePreviewBtn = $('closePreviewBtn');

const previewContent = $('previewContent');

const apiModal = $('apiModal');

const apiKeyInput = $('apiKeyInput');

const apiKeyToggle = $('apiKeyToggle');

const saveApiKeyBtn = $('saveApiKeyBtn');

const loginPasswordToggle = $('loginPasswordToggle');

const changeKeyBtn = $('changeKeyBtn');

const navSidebar = $('navSidebar');

const progressBar = $('progressBar');

const progressLabel = $('progressLabel');

const progressPercent = $('progressPercent');

const wipeDataBtn = $('wipeDataBtn');

const sendBtn = $('sendBtn');

const statusBadge = $('statusBadge');

const statusBadgeMobile = $('statusBadgeMobile');

const statChunks = $('statChunks');

const suggestions = $('suggestions');

const themeToggle = $('themeToggle');

const themeIcon = $('themeIcon');

const themeText = $('themeText');

const searchInput = $('searchInput');

const searchResults = $('searchResults');

const exportBtn = $('exportBtn');

const auditLogList = $('auditLogList');

const deptSelect = $('deptSelect');

// Theme Toggle listener (Consolidated below in Theme Management)


const csvHeaders = $('csvHeaders');

const csvBody = $('csvBody');

const saveCsvBtn = $('saveCsvBtn');

const csvStatusInfo = $('csvStatusInfo');

const addRowBtn = $('addRowBtn');

let currentCsvHeaders = [];

// Text Editor Refs
const txtEditorModal = $('txtEditorModal');

const txtEditorContent = $('txtEditorContent');

const txtEditorTitle = $('txtEditorTitle');

const saveTxtBtn = $('saveTxtBtn');

// Helper: Format relative time (Messenger-style)
function parseServerDate(isoStr) {
  if (!isoStr) return new Date();
  let dStr = isoStr.includes(' ') && !isoStr.includes('T') ? isoStr.replace(' ', 'T') : isoStr;
  if (!dStr.includes('Z') && !dStr.includes('+')) {
      dStr += 'Z';
  }
  const d = new Date(dStr);
  return isNaN(d.getTime()) ? new Date(isoStr) : d;
}

function formatRelativeTime(isoStr) {
  if (!isoStr) return '';
  try {
    const date = parseServerDate(isoStr);
    const now = new Date(Date.now() + (state.serverOffset || 0));
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'เมื่อครู่';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} นาทีที่แล้ว`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} ชม.ที่แล้ว`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} วันที่แล้ว`;
    
    return date.toLocaleDateString('th-TH', { day: 'numeric', month: 'short' });
  } catch (e) {
    return isoStr;
  }
}

const createGroupModal = $('createGroupModal');

const memberSelectList = $('memberSelectList');

const confirmCreateGroup = $('confirmCreateGroup');

const cancelCreateGroup = $('cancelCreateGroup');

const newGroupName = $('newGroupName');

const openCreateGroupModal = $('openCreateGroupModal');

const editGroupBtn = $('editGroupBtn');

const editGroupModal = $('editGroupModal');

const editGroupName = $('editGroupName');

const groupAvatarPreview = $('groupAvatarPreview');

const confirmEditGroup = $('confirmEditGroup');

const cancelEditGroup = $('cancelEditGroup');

const videoCallBtn = $('videoCallBtn');

const incomingCallModal = $('incomingCallModal');

const callerName = $('callerName');

const callerAvatar = $('callerAvatar');

const acceptCallBtn = $('acceptCallBtn');

const rejectCallBtn = $('rejectCallBtn');

const activeCallModal = $('activeCallModal');

const remoteVideo = $('remoteVideo');

const remoteAudio = $('remoteAudio');

const localVideo = $('localVideo');

const localVideoContainer = $('localVideoContainer');

const remoteAvatarFallback = $('remoteAvatarFallback');

const activeCallName = $('activeCallName');

const callDuration = $('callDuration');

const toggleMicBtn = $('toggleMicBtn');

const micIcon = $('micIcon');

const toggleCamBtn = $('toggleCamBtn');

const camIcon = $('camIcon');

const shareScreenBtn = $('shareScreenBtn');

const endCallBtn = $('endCallBtn');

const vizXSelect = $('vizXSelect');

const vizYSelect = $('vizYSelect');

const vizChartCanvas = $('vizChart');

const vizEmptyState = $('vizEmptyState');

const downloadChartBtn = $('downloadChartBtn');

const vizStatsRow = $('vizStatsRow');

const statsAvg = $('statsAvg');

const statsMax = $('statsMax');

const statsMin = $('statsMin');

const vizAiSummaryBox = $('vizAiSummaryBox');

const generateAiSummaryBtn = $('generateAiSummaryBtn');

const aiSummaryContent = $('aiSummaryContent');

// Mobile Navigation Refs
const mobileMenuBtn = $('mobileMenuBtn');

const sidebarOverlay = $('sidebarOverlay');

let myChart = null;

let currentVizData = [];

let currentVizType = 'bar';

let currentVizHeaders = [];

// Calendar Refs
const calendarMonth = $('calendarMonth');

const calendarGrid = $('calendarGrid');

const upcomingSchedules = $('upcomingSchedules');

const addScheduleBtn = $('addScheduleBtn');

const archivePastSchedulesBtn = $('archivePastSchedulesBtn');

const scheduleModal = $('scheduleModal');

const closeScheduleModal = $('closeScheduleModal');

const saveScheduleBtn = $('saveScheduleBtn');

const prevMonthBtn = $('prevMonth');

const nextMonthBtn = $('nextMonth');

const scheduleTitleInput = $('scheduleTitle');

const scheduleDateInput = $('scheduleDate');

const scheduleDescInput = $('scheduleDesc');

const scheduleTimeInput = $('scheduleTime');

const scheduleStatusInput = $('scheduleStatus');

const realtimeClock = $('realtimeClock');

// Social Feed Refs
const postInput = $('postInput');

const submitPostBtn = $('submitPostBtn');

const feedPosts = $('feedPosts');

const linkInputContainer = $('linkInputContainer');

const postLink = $('postLink');

const postAttachmentPreview = $('postAttachmentPreview');

// Daily Digest Refs
const dailyDigest = $('dailyDigest');

const digestContent = $('digestContent');

const refreshDigestBtn = $('refreshDigestBtn');

// Edit Post Modal Refs
const editPostModal = $('editPostModal');

const editPostInput = $('editPostInput');

const editPostLink = $('editPostLink');

const saveEditPostBtn = $('saveEditPostBtn');

const closeEditPostModal = $('closeEditPostModal');

const bulkDeleteBtn = $('bulkDeleteBtn');

let currentEditingPostId = null;

// Login Refs
const loginOverlay = $('loginOverlay');

const loginUsername = $('loginUsername');

const loginPassword = $('loginPassword');

const loginBtn = $('loginBtn');

const loginError = $('loginError');

const logoutBtn = $('logoutBtn');

const sidebarUserAvatar = $('sidebarUserAvatar');

const sidebarDisplayName = $('sidebarDisplayName');

const summonBotBtn = $('summonBotBtn');

// AI Productivity Refs
const aiGenKanbanBtn = $('aiGenKanbanBtn');

const aiGenKanbanModal = $('aiGenKanbanModal');

const aiGenKanbanInput = $('aiGenKanbanInput');

const confirmAiGenBtn = $('confirmAiGenBtn');

const closeAiGenModal = $('closeAiGenModal');

const bulkCompareBtn = $('bulkCompareBtn');

const aiCompareModal = $('aiCompareModal');

const aiCompareResult = $('aiCompareResult');

const closeAiCompareModal = $('closeAiCompareModal');

const customAccentInput = $('customAccentInput');

// ─── Lucide Init ──────────────────────────────
function initIcons() {
  try {
    if (typeof lucide !== 'undefined') {
      lucide.createIcons();
    }
  } catch (e) {
    console.warn('Lucide icons failed to init:', e);
  }
}

// ─── Toast ───────────────────────────────────
function toast(msg, type = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    // z-[99999] ต้องสูงกว่าทุก modal (groupChatModal=1200, incoming call=9000)
    container.className = 'toast-container fixed top-6 right-6 z-[99999] flex flex-col gap-3 pointer-events-none';
    document.body.appendChild(container);
  }
  const el = document.createElement('div');
  const bgMap = {
    info: 'bg-surface-800 text-white',
    success: 'bg-emerald-600 text-white',
    error: 'bg-red-600 text-white',
    warning: 'bg-amber-500 text-white'
  };
  el.className = `${bgMap[type] || bgMap.info} px-6 py-3 rounded-xl shadow-xl text-xs font-semibold animate-in slide-in-from-right-10 duration-300 pointer-events-auto cursor-pointer`;
  el.textContent = msg;
  el.onclick = () => el.remove();
  container.appendChild(el);
  setTimeout(() => {
    el.classList.add('animate-out', 'fade-out', 'slide-out-to-right-10');
    setTimeout(() => el.remove(), 300);
  }, 4500); // 4.5 seconds for better readability
}

function hideGlobalLoading() {
  const overlay = $('globalLoadingOverlay');
  if (overlay) overlay.classList.add('hidden');
}

// ─── API Helpers ──────────────────────────────
async function apiFetch(url, options = {}) {
  // Ensure Content-Type is set for POST/PUT/PATCH if body is present, UNLESS it's FormData.
  if (options.body && !(options.body instanceof FormData)) {
    if (!options.headers) {
      options.headers = { 'Content-Type': 'application/json' };
    } else if (!options.headers['Content-Type']) {
      options.headers['Content-Type'] = 'application/json';
    }
  }

  const controller = new AbortController();
  const timeoutMs = options._timeout || 30000;
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  delete options._timeout;
  let res;
  try {
    res = await fetch(url, { ...options, signal: controller.signal });
  } catch (err) {
    clearTimeout(timer);
    if (err.name === 'AbortError') throw new Error('คำขอใช้เวลานานเกินไป กรุณาลองใหม่อีกครั้ง');
    throw err;
  }
  clearTimeout(timer);

  if (!res.ok) {
    const text = await res.text();
    let errData = null;
    try { errData = JSON.parse(text); } catch (e) {}
    if (res.status === 401) {
      if (!window._sessionExpired) {
        window._sessionExpired = true;
        if (typeof toast === 'function') {
          toast('เซสชันหมดอายุแล้ว กรุณาเข้าสู่ระบบใหม่เพื่อใช้งานต่อค่ะ', 'error');
        }
        const loginOverlay = document.getElementById('loginOverlay');
        if (loginOverlay) {
          loginOverlay.classList.remove('hidden');
        }
      }
      throw new Error('Unauthorized');
    }
    if (res.status === 403 && errData && (errData.error === 'upgrade_required' || errData.error === 'usage_limit_reached' || errData.error === 'feature_not_available')) {
      if (typeof showUpgradePrompt === 'function') showUpgradePrompt(errData);
      throw new Error('__billing_handled__');
    }
    const errorMsg = (errData && errData.error) || text || res.statusText;
    throw new Error(errorMsg);
  }
  return await res.json();
}

// ─── AI Persona Logic ──────────────────────
async function loadPersonas() {
  try {
    const data = await apiFetch('/api/personas');
    if (data.ok) {
      state.personas = data.personas;
      renderPersonas();
    }
  } catch (e) {
    console.error('Failed to load personas:', e);
  }
}

function selectPersona(id) {
  const p = (state.personas || []).find(p => p.id == id);
  state.activePersona = p || null;
  const activeName = document.getElementById('activePersonaName');
  if (activeName) activeName.textContent = p ? p.name : 'Default';
  const dd = document.getElementById('personaDropdown');
  if (dd) dd.classList.add('hidden');
  if (typeof renderPersonas === 'function') renderPersonas();
  if (typeof toast === 'function') {
    toast(p ? `สลับเป็นตัวตน: ${p.name}` : 'กลับสู่โหมดพื้นฐาน (Default)', 'info');
  }
}
window.selectPersona = selectPersona;

if (personaBtn) {
  personaBtn.onclick = (e) => {
    e.stopPropagation();
    personaDropdown?.classList.toggle('hidden');
  };
}

document.addEventListener('click', (e) => {
  const dd = document.getElementById('personaDropdown');
  const btn = document.getElementById('personaBtn');
  if (dd && !dd.classList.contains('hidden')) {
    if (!dd.contains(e.target) && !btn?.contains(e.target)) {
      dd.classList.add('hidden');
    }
  }
});

// ─── Seen Receipts ──────────────────────────
async function recordPostView(pid) {
  if (state.postViews[pid]) return; // Already recorded in this session check
  try {
    await apiFetch(`/api/posts/${pid}/view`, { method: 'POST' });
    state.postViews[pid] = true;
  } catch (e) { }
}

const postViewObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const pid = entry.target.dataset.postId;
      if (pid) recordPostView(pid);
    }
  });
}, { threshold: 0.5 });

function renderLeaderboard(topPosters) {
  const el = $('analyticsLeaderboard');
  if (!el) return;
  if (!topPosters.length) {
    el.innerHTML = '<div class="text-center py-6 text-surface-400 text-xs">ยังไม่มีข้อมูล</div>';
    return;
  }
  const medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'];
  el.innerHTML = topPosters.map((p, i) => `
    <div class="flex items-center justify-between px-4 py-3 rounded-2xl ${i === 0 ? 'bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 border border-amber-200 dark:border-amber-800' : 'bg-surface-50 dark:bg-surface-800/50'} hover:scale-[1.01] transition-transform">
      <div class="flex items-center gap-3">
        <span class="text-xl w-8 text-center">${medals[i] || (i + 1)}</span>
        <div class="w-8 h-8 rounded-full bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center text-brand-600 font-black text-xs shadow-sm">
          ${p.user ? p.user[0].toUpperCase() : '?'}
        </div>
        <span class="text-[11px] font-black text-surface-900 dark:text-white">${p.user}</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="h-2 rounded-full bg-brand-500" style="width: ${Math.max(20, (p.count / (topPosters[0]?.count || 1)) * 80)}px; opacity: ${0.4 + (0.6 * p.count / (topPosters[0]?.count || 1))}"></div>
        <span class="text-[10px] font-black text-brand-600 dark:text-brand-400 w-8 text-right">${p.count}</span>
      </div>
    </div>
  `).join('');
}

// ─── Quotation System Logic ─────────────────
let quotationItems = [];

function addQtItem() {
  quotationItems.push({ desc: '', qty: 1, price: 0 });
  renderQuotationItems();
}

function removeQtItem(index) {
  quotationItems.splice(index, 1);
  renderQuotationItems();
}

function updateQtItem(index, field, value) {
  quotationItems[index][field] = field === 'desc' ? value : parseFloat(value) || 0;
  renderQuotationItems();
}

function updateQuotationPreview() {
  const fields = [
    { id: 'qtCustomerName', prev: 'prevCustName' },
    { id: 'qtCustomerAddress', prev: 'prevCustAddress' },
    { id: 'qtCustomerTaxId', prev: 'prevCustTaxId' },
    { id: 'qtCustomerContact', prev: 'prevCustContact' },
    { id: 'qtNo', prev: 'prevQtNo' },
    { id: 'qtDate', prev: 'prevQtDate' },
    { id: 'sellerName', prev: 'prevSellerName' }
  ];
  
  fields.forEach(f => {
    const el = $(f.id);
    const prev = $(f.prev);
    if (el && prev) {
      prev.innerText = el.value || (f.id.includes('qtNo') ? 'QT-000' : '-');
    }
  });

  // Special handling for Seller Info (multiple fields to one <p>)
  const sAddr = $('sellerAddress')?.value || '';
  const sTax = $('sellerTaxId')?.value || '';
  const sPhone = $('sellerPhone')?.value || '';
  const prevSInfo = $('prevSellerInfo');
  if (prevSInfo) {
    prevSInfo.innerHTML = `${sAddr}<br>เลขประจำตัวผู้เสียภาษี: ${sTax}<br>โทร: ${sPhone}`;
  }

  // Handle replacement receipt reference elements
  const docType = $('docTypeSelect')?.value;
  const repRefBlock = $('replacementRefBlock');
  const prevRepRef = $('prevReplacementRef');
  
  if (docType === 'receipt_replacement') {
    if (repRefBlock) repRefBlock.classList.remove('hidden');
    if (prevRepRef) prevRepRef.classList.remove('hidden');
    
    if ($('prevOriginalRefNo')) $('prevOriginalRefNo').innerText = $('qtOriginalRefNo')?.value || '-';
    if ($('prevOriginalRefDate')) $('prevOriginalRefDate').innerText = $('qtOriginalRefDate')?.value || '-';
    if ($('prevReplacementReason')) $('prevReplacementReason').innerText = $('qtReplacementReason')?.value || '-';
  } else {
    if (repRefBlock) repRefBlock.classList.add('hidden');
    if (prevRepRef) prevRepRef.classList.add('hidden');
  }

  renderQuotationItems();
}

function deleteOrgLogo() {
  resetOrgLogoUI();
  toast('ลบโลโก้เรียบร้อย กดบันทึกเพื่อบันทึกการเปลี่ยนแปลง', 'info');
}

function deleteOrgSig() {
  resetOrgSigUI();
  toast('ลบลายเซ็นเรียบร้อย กดบันทึกเพื่อบันทึกการเปลี่ยนแปลง', 'info');
}

// ─── Smart Dashboard Logic ─────────────────


/** 🌦️ Weather Integration (Open-Meteo) ───────────────────────── */
async function fetchWeather() {
  const currentTempEl = $('currentTemp');
  const weatherCondEl = $('weatherCondition');
  const rainChanceEl = $('rainChance');
  const dashFeelsLike = $('dashFeelsLike');
  const dashHumidity = $('dashHumidity');
  const dashUV = $('dashUV');
  const dashPM25 = $('dashPM25');
  const mainWeatherIcon = $('mainWeatherIcon');

  if (!currentTempEl) return;

  try {
    // Bangkok: Lat 13.75, Lon 100.51
    const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=13.75&longitude=100.51&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,uv_index&hourly=temperature_2m,precipitation_probability,weather_code,uv_index&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max&timezone=Asia%2FBangkok&forecast_days=7`;
    const aqUrl = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=13.75&longitude=100.51&current=pm2_5&timezone=Asia%2FBangkok`;

    const [weatherRes, aqRes] = await Promise.all([fetch(weatherUrl), fetch(aqUrl)]);
    const weatherData = await weatherRes.json();
    const aqData = await aqRes.json();

    if (weatherData.current) {
      state.weather = weatherData; // Save to global state
      state.airQuality = aqData;
      
      const temp = Math.round(weatherData.current.temperature_2m);
      const feelsLike = Math.round(weatherData.current.apparent_temperature);
      const humidity = weatherData.current.relative_humidity_2m;
      const wCode = weatherData.current.weather_code;
      const uv = weatherData.current.uv_index;
      const pm25 = aqData.current.pm2_5;
      
      // Update UI
      currentTempEl.textContent = `${temp}°C`;
      if (dashFeelsLike) dashFeelsLike.textContent = `${feelsLike}°C`;
      if (dashHumidity) dashHumidity.textContent = `${humidity}%`;
      if (dashUV) {
        dashUV.textContent = uv.toFixed(1);
        dashUV.className = `text-sm font-black ${uv > 6 ? 'text-rose-500' : uv > 3 ? 'text-amber-500' : 'text-emerald-500'}`;
      }
      if (dashPM25) {
        dashPM25.textContent = pm25.toFixed(1);
        dashPM25.className = `text-sm font-black ${pm25 > 50 ? 'text-rose-500' : pm25 > 25 ? 'text-amber-500' : 'text-emerald-500'}`;
      }
      
      // Translate WMO Code
      const condition = translateWMO(wCode);
      let conditionText = condition.text;
      if (weatherData.current.precipitation > 0) {
        conditionText = `ขณะนี้มีฝน (${weatherData.current.precipitation} มม.)`;
      }
      weatherCondEl.textContent = conditionText;
      
      // Update Rain Chance (from first hour of forecast)
      const rainChance = weatherData.hourly.precipitation_probability[new Date().getHours()];
      rainChanceEl.innerHTML = `<i data-lucide="droplets" class="w-3 h-3"></i> โอกาสฝน ${rainChance}%`;
      
      // Update Icon
      if (mainWeatherIcon) {
        mainWeatherIcon.setAttribute('data-lucide', condition.icon);
        lucide.createIcons();
      }

      // Update Last Updated Time
      const lastUpdateEl = $('weatherLastUpdate');
      if (lastUpdateEl) {
        const now = new Date();
        lastUpdateEl.textContent = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
      }
    }
  } catch (err) {
    console.error('Weather Fetch Error:', err);
    if (weatherCondEl) weatherCondEl.textContent = 'ไม่สามารถโหลดสภาพอากาศได้';
  }
}

function translateWMO(code) {
  const mapping = {
    0: { text: 'ท้องฟ้าแจ่มใส', icon: 'sun' },
    1: { text: 'ท้องฟ้าโปร่ง', icon: 'cloud-sun' },
    2: { text: 'มีเมฆบางส่วน', icon: 'cloud-sun' },
    3: { text: 'เมฆมาก', icon: 'cloud' },
    45: { text: 'หมอกลง', icon: 'cloud-fog' },
    48: { text: 'หมอกน้ำค้างแข็ง', icon: 'cloud-fog' },
    51: { text: 'ฝนปรอยๆ', icon: 'cloud-drizzle' },
    53: { text: 'ฝนปรอยๆ', icon: 'cloud-drizzle' },
    55: { text: 'ฝนปรอยๆ หนาแน่น', icon: 'cloud-drizzle' },
    61: { text: 'ฝนตกเล็กน้อย', icon: 'cloud-rain' },
    63: { text: 'ฝนตกปานกลาง', icon: 'cloud-rain' },
    65: { text: 'ฝนตกหนัก', icon: 'cloud-rain' },
    80: { text: 'ฝนซู่เล็กน้อย', icon: 'cloud-showers' },
    81: { text: 'ฝนซู่ปานกลาง', icon: 'cloud-showers' },
    82: { text: 'ฝนซู่รุนแรง', icon: 'cloud-showers' },
    95: { text: 'พายุฝนฟ้าคะนอง', icon: 'cloud-lightning' },
  };
  return mapping[code] || { text: 'พยากรณ์อากาศ', icon: 'cloud' };
}

function showWeatherDetail() {
  const modal = $('weatherDetailModal');
  const hourlyList = $('hourlyForecastList');
  const dailyList = $('dailyForecastList');
  const detailFeelsLike = $('detailFeelsLike');
  const detailHumidity = $('detailHumidity');
  const detailUV = $('detailUV');
  const detailPM25 = $('detailPM25');

  if (!modal) return;

  // If no weather data yet, fetch it first then show
  if (!state.weather) {
    modal.classList.remove('hidden');
    modal.classList.add('flex', 'items-center', 'justify-center');
    if (hourlyList) hourlyList.innerHTML = `
      <div class="flex flex-col items-center justify-center py-10 gap-4 text-surface-400">
        <div class="w-10 h-10 border-4 border-brand-100 border-t-brand-600 rounded-full animate-spin"></div>
        <span class="text-sm font-bold">กำลังโหลดสภาพอากาศ...</span>
      </div>`;
    fetchWeather().then(() => {
      if (state.weather) showWeatherDetail();
    });
    return;
  }

  // Set Details
  if (detailFeelsLike) detailFeelsLike.textContent = `${Math.round(state.weather.current.apparent_temperature)}°C`;
  if (detailHumidity) detailHumidity.textContent = `${state.weather.current.relative_humidity_2m}%`;
  if (detailUV) detailUV.textContent = state.weather.current.uv_index.toFixed(1);
  if (detailPM25 && state.airQuality) detailPM25.textContent = state.airQuality.current.pm2_5.toFixed(1);

  // Render Hourly (Next 24h)
  if (hourlyList) {
    const hourly = state.weather.hourly;
    const nowHour = new Date().getHours();
    
    // Create horizontal scrollable hourly forecast
    hourlyList.classList.add('flex', 'overflow-x-auto', 'no-scrollbar', 'gap-4', 'pb-4');
    
    hourlyList.innerHTML = hourly.time.slice(nowHour, nowHour + 24).map((time, i) => {
      const idx = nowHour + i;
      const t = new Date(time);
      const hourStr = t.getHours().toString().padStart(2, '0') + ':00';
      const temp = Math.round(hourly.temperature_2m[idx]);
      const prob = hourly.precipitation_probability[idx];
      const cond = translateWMO(hourly.weather_code[idx]);
      
      return `
        <div class="flex flex-col items-center gap-2 p-4 bg-white dark:bg-surface-900 rounded-2xl border border-surface-100 dark:border-surface-800 min-w-[90px] shadow-sm">
          <span class="text-[10px] font-black text-surface-400">${hourStr}</span>
          <div class="w-10 h-10 bg-brand-50 dark:bg-brand-900/20 rounded-xl flex items-center justify-center text-brand-600 my-1">
             <i data-lucide="${cond.icon}" class="w-5 h-5"></i>
          </div>
          <span class="text-sm font-black text-surface-900 dark:text-white">${temp}°C</span>
          <div class="text-[9px] font-bold text-blue-500 flex items-center gap-1">
             <i data-lucide="droplets" class="w-2.5 h-2.5"></i> ${prob}%
          </div>
        </div>
      `;
    }).join('');
  }

  // Render Daily
  if (dailyList) {
    const daily = state.weather.daily;
    const days = ["อาทิตย์", "จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์"];
    
    dailyList.innerHTML = daily.time.map((time, i) => {
      const t = new Date(time);
      const dayName = i === 0 ? "วันนี้" : i === 1 ? "พรุ่งนี้" : days[t.getDay()];
      const maxTemp = Math.round(daily.temperature_2m_max[i]);
      const minTemp = Math.round(daily.temperature_2m_min[i]);
      const prob = daily.precipitation_probability_max[i];
      const cond = translateWMO(daily.weather_code[i]);
      
      return `
        <div class="flex items-center justify-between p-4 hover:bg-white dark:hover:bg-surface-900 rounded-2xl transition-all group">
          <div class="flex items-center gap-4 flex-1">
             <span class="text-xs font-bold text-surface-700 dark:text-surface-300 w-16">${dayName}</span>
             <div class="flex items-center gap-2 flex-1">
               <div class="text-brand-600"><i data-lucide="${cond.icon}" class="w-4 h-4"></i></div>
               <span class="text-[10px] font-bold text-surface-400 group-hover:text-surface-600 transition-colors">${cond.text}</span>
             </div>
          </div>
          <div class="flex items-center gap-4">
             <div class="text-[9px] font-bold text-blue-500 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <i data-lucide="droplets" class="w-2.5 h-2.5"></i> ${prob}%
             </div>
             <div class="flex items-center gap-2 text-xs font-black">
                <span class="text-surface-900 dark:text-white">${maxTemp}°</span>
                <span class="text-surface-400">${minTemp}°</span>
             </div>
          </div>
        </div>
      `;
    }).join('');
  }

  modal.classList.remove('hidden');
  modal.classList.add('flex', 'items-center', 'justify-center');
  lucide.createIcons();
}

// Alias for index.html onclick
function showView(viewId) {
  if (typeof switchView === 'function') {
    switchView(viewId);
  } else {
    console.warn(`[showView] switchView is not defined yet. Retrying in 50ms for view: ${viewId}`);
    const interval = setInterval(() => {
      if (typeof switchView === 'function') {
        clearInterval(interval);
        switchView(viewId);
      }
    }, 50);
    setTimeout(() => clearInterval(interval), 5000);
  }
}

// Placeholder/Safe wrapper for openMobileChat (defined in chat.js)
window.openMobileChat = function() {
  if (window.openMobileChat && !window.openMobileChat.isPlaceholder) {
    window.openMobileChat();
  } else {
    console.warn('openMobileChat called before initialization. Retrying in 50ms...');
    const interval = setInterval(() => {
      if (window.openMobileChat && !window.openMobileChat.isPlaceholder) {
        clearInterval(interval);
        window.openMobileChat();
      }
    }, 50);
    setTimeout(() => clearInterval(interval), 5000);
  }
};
window.openMobileChat.isPlaceholder = true;

// ─── AI Summary Logic ────────────────────────
async function renderSummary() {
  const contentArea = $('summaryContentArea');
  const emptyState = $('summaryEmpty');
  const loadingState = $('summaryLoading');
  const output = $('summaryOutput');

  // If we already have a summary in the output, show it, otherwise show empty state
  if (output && output.innerHTML.trim().length > 0) {
    contentArea.classList.remove('hidden');
    emptyState.classList.add('hidden');
    loadingState.classList.add('hidden');
  } else {
    contentArea.classList.add('hidden');
    emptyState.classList.remove('hidden');
    loadingState.classList.add('hidden');
  }
}

function toggleSidebar(force) {
  const isOpen = force !== undefined ? force : !navSidebar.classList.contains('open');
  navSidebar.classList.toggle('open', isOpen);
  if (sidebarOverlay) {
    sidebarOverlay.classList.toggle('active', isOpen);
    sidebarOverlay.classList.toggle('hidden', !isOpen);
  }
}

if (mobileMenuBtn) mobileMenuBtn.onclick = () => toggleSidebar(true);

if (sidebarOverlay) sidebarOverlay.onclick = () => toggleSidebar(false);

// Auto-close mobile sidebar when switching to desktop screen size
window.addEventListener('resize', () => {
  if (window.innerWidth >= 1024) {
    if (navSidebar && navSidebar.classList.contains('open')) {
      toggleSidebar(false);
    }
  }
});

// ─── Touch Gestures for Sidebar ────────────────
let touchStartX = 0;

let touchEndX = 0;

function handleGesture() {
  if (window.innerWidth > 1024) return;
  const swipeDistance = touchStartX - touchEndX;
  const isSidebarOpen = navSidebar.classList.contains('open');

  // Swipe Left to close sidebar
  if (isSidebarOpen && swipeDistance > 70) {
    toggleSidebar(false);
  }
  // Swipe Right from edge to open sidebar
  if (!isSidebarOpen && swipeDistance < -70 && touchStartX < 50) {
    toggleSidebar(true);
  }
}

async function loadStats() {
  try {
    const data = await apiFetch('/api/stats');
    if (statTotalQueries) statTotalQueries.textContent = data.total_queries || 0;
    if (statLikes) statLikes.textContent = data.feedback[1] || 0;
    if (statDislikes) statDislikes.textContent = data.feedback[-1] || 0;

    // Fetch and Populate Audit Log
    const logsRes = await apiFetch('/api/logs');
    if (auditLogList && logsRes.logs) {
      auditLogList.innerHTML = logsRes.logs.map(l => `
        <div class="flex items-center justify-between py-2 border-b border-surface-100 dark:border-surface-800 last:border-0 text-xs text-surface-500">
           <span class="font-bold text-brand-600 w-32">${l.time}</span>
           <span class="flex-1 px-4 text-surface-700 dark:text-surface-300">${l.event}</span>
           <span class="font-mono text-[10px] bg-surface-100 dark:bg-surface-800 px-1.5 py-0.5 rounded">${l.user}</span>
        </div>
      `).join('');
    }
  } catch (e) {
    console.error('Failed to load stats/logs:', e);
  }
}

// ─── Events: Navigation ─────────────────────
document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    const view = btn.dataset.view;
    if (view) showView(view);
  });
});

// ─── Accent Color Logic ─────────────────────
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : '37, 99, 235';
}

document.querySelectorAll('.accent-color-btn').forEach(btn => {
  btn.onclick = () => setAccentColor(btn.dataset.color);
});

// Removed redundant customAccentInput declaration as it's at the top.
if (customAccentInput) {
  customAccentInput.oninput = () => setAccentColor(customAccentInput.value);
}

// ─── History Management ─────────────────────
function saveHistory() {
  // No longer saving to localStorage as we have backend persistence
  // But we still update state.history for UI performance
}

/**
 * Helper to parse special AI actions like [CALENDAR_ACTION] from text
 */
function parseAIActions(text) {
  let displayHtml = markdownToHtml(text || '');
  let calendarData = null;
  let reconcileData = null;

  if (text && text.includes('[CALENDAR_ACTION]')) {
    const match = text.match(/\[CALENDAR_ACTION\]([\s\S]*?)\[\/CALENDAR_ACTION\]/);
    if (match) {
      try {
        calendarData = JSON.parse(match[1]);
        text = text.replace(/\[CALENDAR_ACTION\][\s\S]*?\[\/CALENDAR_ACTION\]/, '').trim();
      } catch (e) {
        console.error('Calendar parse error:', e);
      }
    }
  }

  if (text && text.includes('[RECONCILE_ACTION]')) {
    const match = text.match(/\[RECONCILE_ACTION\]([\s\S]*?)\[\/RECONCILE_ACTION\]/);
    if (match) {
      try {
        reconcileData = JSON.parse(match[1]);
        text = text.replace(/\[RECONCILE_ACTION\][\s\S]*?\[\/RECONCILE_ACTION\]/, '').trim();
      } catch (e) {
        console.error('Reconcile parse error:', e);
      }
    }
  }

  displayHtml = markdownToHtml(text || '');
  return { displayHtml, calendarData, reconcileData };
}

// ─── API Key Modal ────────────────────────────
function showApiModal() { 
  apiModal.classList.remove('hidden'); 
  apiModal.classList.add('flex', 'items-center', 'justify-center');
}

function hideApiModal() { 
  apiModal.classList.add('hidden'); 
  apiModal.classList.remove('flex', 'items-center', 'justify-center');
}

apiKeyToggle.addEventListener('click', () => {
  const type = apiKeyInput.type === 'password' ? 'text' : 'password';
  apiKeyInput.type = type;
  const icon = apiKeyInput.type === 'password' ? 'eye' : 'eye-off';
  apiKeyToggle.innerHTML = `<i data-lucide="${icon}" class="w-4 h-4"></i>`;
  initIcons();
});

if (loginPasswordToggle) {
  loginPasswordToggle.addEventListener('click', () => {
    const pwd = $('loginPassword');
    const type = pwd.type === 'password' ? 'text' : 'password';
    pwd.type = type;
    const icon = type === 'password' ? 'eye' : 'eye-off';
    loginPasswordToggle.innerHTML = `<i data-lucide="${icon}" class="w-4 h-4"></i>`;
    initIcons();
  });
}

changeKeyBtn.addEventListener('click', () => {
  apiKeyInput.value = '';
  showApiModal();
});

const _IMG_EXTS = new Set(['png','jpg','jpeg','webp','bmp']);

const _DOC_EXTS = new Set(['pdf','docx','xlsx','csv','txt','md']);

let _ghostObjectURLs = []; // track for cleanup


function _updateGhostProgress(ghosts, pct, label = '') {
  ghosts.forEach(({ el }) => {
    const bar    = el.querySelector('.ghost-bar');
    const pctEl  = el.querySelector('.ghost-pct');
    const status = el.querySelector('.ghost-status');
    if (bar) bar.style.width = pct + '%';
    if (pctEl) pctEl.textContent = pct + '%';
    if (status && label) status.textContent = label;
  });
}

function _transitionGhostsToIndexing(ghosts) {
  ghosts.forEach(({ el }) => {
    el.style.borderColor = '';
    el.classList.remove('border-brand-400/60', 'dark:border-brand-600/60', 'shadow-brand-500/10');
    el.classList.add('border-amber-400/60', 'dark:border-amber-600/60');
    const bar   = el.querySelector('.ghost-bar');
    const pctEl = el.querySelector('.ghost-pct');
    const status = el.querySelector('.ghost-status');
    if (bar) { bar.style.width = '100%'; bar.className = 'ghost-bar h-full bg-gradient-to-r from-amber-400 to-orange-500 rounded-full'; }
    if (pctEl) pctEl.textContent = 'กำลัง Index...';
    if (status) { status.textContent = 'Indexing...'; status.className = 'ghost-status text-[9px] font-black text-amber-500 uppercase tracking-tighter'; }
  });
}

function _removeGhosts(ghosts) {
  ghosts.forEach(({ el }) => {
    el.style.transition = 'opacity 0.3s, transform 0.3s';
    el.style.opacity = '0';
    el.style.transform = 'translateY(-8px)';
    setTimeout(() => el.remove(), 350);
  });
  // Revoke object URLs to free memory
  _ghostObjectURLs.forEach(u => URL.revokeObjectURL(u));
  _ghostObjectURLs = [];
}

function updateProgress(percent, text) {
  progressBar.style.width = `${percent}%`;
  progressPercent.textContent = `${percent}%`;
  progressLabel.textContent = text;
}

function renderCsvAsHtmlTable(csvText) {
  if (!csvText) return '<div class="p-8 text-center text-surface-400">ไฟล์ว่างไม่มีข้อมูล</div>';

  const rows = csvText.split(/\r?\n/).filter(line => line.trim() !== '');
  if (rows.length === 0) return '<div class="p-8 text-center text-surface-400">ไฟล์ว่างไม่มีข้อมูล</div>';

  let html = '<div class="overflow-x-auto rounded-xl border border-surface-200 dark:border-surface-800 shadow-sm"><table class="w-full text-xs text-left border-collapse">';

  rows.forEach((row, rowIndex) => {
    const cols = row.split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/); // Simple CSV parser handling quotes
    const tag = rowIndex === 0 ? 'th' : 'td';
    const rowClass = rowIndex === 0
      ? 'bg-surface-50 dark:bg-surface-800/50 sticky top-0 z-10'
      : 'hover:bg-surface-50 dark:hover:bg-surface-800/30 transition-colors border-t border-surface-100 dark:border-surface-800';

    html += `<tr class="${rowClass}">`;
    cols.forEach(col => {
      let val = col.trim();
      if (val.startsWith('"') && val.endsWith('"')) val = val.substring(1, val.length - 1);

      const colClass = rowIndex === 0
        ? 'px-4 py-3 font-black text-surface-400 uppercase tracking-widest border-b border-surface-200 dark:border-surface-700'
        : 'px-4 py-3 text-surface-600 dark:text-surface-300 font-medium whitespace-nowrap';

      html += `<${tag} class="${colClass}">${val}</${tag}>`;
    });
    html += '</tr>';
  });

  html += '</table></div>';
  return html;
}

function closePdfViewer() {
  const modal = $('pdfViewerModal');
  const frame = $('pdfFrame');
  const csvTarget = $('csvTableTarget');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex', 'items-center', 'justify-center');
  }
  if (frame) frame.src = '';
  if (csvTarget) csvTarget.innerHTML = '';
}

let currentCatVisibility = 'public';

function renderCatUserList(query = '') {
  const listArea = $('catUserListArea');
  const countSpan = $('catAuthCount');
  
  if (!state.allUsers || state.allUsers.length === 0) {
    listArea.innerHTML = '<p class="text-[10px] text-surface-400 italic text-center py-4">ไม่พบข้อมูลรายชื่อผู้ใช้</p>';
    return;
  }

  // Filter users by search query
  const filtered = state.allUsers.filter(u => 
    u.username.toLowerCase().includes(query.toLowerCase()) || 
    (u.display_name && u.display_name.toLowerCase().includes(query.toLowerCase()))
  );

  if (filtered.length === 0) {
    listArea.innerHTML = '<p class="text-[10px] text-surface-400 italic text-center py-4">ไม่พบผู้ใช้ที่ค้นหา</p>';
    return;
  }

  listArea.innerHTML = filtered.map(u => {
    const isSelected = selectedCatUsers.includes(u.username);
    return `
      <div onclick="toggleAuthUser('${u.username}')" 
           class="group flex items-center gap-3 p-2.5 rounded-xl cursor-pointer hover:bg-brand-50 dark:hover:bg-brand-900/20 transition-all border border-transparent ${isSelected ? 'bg-brand-50/50 dark:bg-brand-900/10 border-brand-200/50 dark:border-brand-800/50' : ''}">
        <div class="w-8 h-8 rounded-full bg-brand-100 dark:bg-brand-900/40 flex items-center justify-center text-[10px] font-bold text-brand-600 ${isSelected ? 'ring-2 ring-brand-500 ring-offset-2 dark:ring-offset-surface-900' : ''}">
          ${u.username.charAt(0).toUpperCase()}
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-[11px] font-bold ${isSelected ? 'text-brand-600' : ''}">${u.display_name || u.username}</div>
          <div class="text-[9px] text-surface-400 leading-none">@${u.username}</div>
        </div>
        <div class="w-5 h-5 rounded-md border-2 flex items-center justify-center transition-colors ${isSelected ? 'bg-brand-600 border-brand-600 text-white' : 'border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-800'}">
          ${isSelected ? '<i data-lucide="check" class="w-3 h-3"></i>' : ''}
        </div>
      </div>
    `;
  }).join('');

  countSpan.textContent = selectedCatUsers.length;
  initIcons();
}

function toggleAuthUser(username) {
  const index = selectedCatUsers.indexOf(username);
  if (index === -1) {
    selectedCatUsers.push(username);
  } else {
    selectedCatUsers.splice(index, 1);
  }
  // Re-render the list to show new state
  const searchQuery = $('catUserSearch').value;
  renderCatUserList(searchQuery);
}

if (searchInput) {
  searchInput.addEventListener('input', debounce(async () => {
    const q = searchInput.value.trim();
    const spinner = $('searchSpinner');
    const emptyState = $('searchEmptyState');
    if (!q || q.length < 2) {
      if (emptyState) emptyState.classList.remove('hidden');
      searchResults.innerHTML = '';
      if (emptyState) searchResults.appendChild(emptyState);
      return;
    }
    if (emptyState) emptyState.classList.add('hidden');
    if (spinner) spinner.classList.remove('hidden');
    try {
      const data = await apiFetch(`/api/search/global?q=${encodeURIComponent(q)}`);
      renderSearchResults(data.results || [], q);
    } catch (e) {
      if (spinner) spinner.classList.add('hidden');
      renderSearchResults([], q);
    }
  }, 400));
}

function debounce(fn, ms) {
  let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn.apply(this, args), ms); };
}

function markdownToHtml(text) {
  if (typeof marked === 'undefined') return text;
  return marked.parse(text);
}

// AI Vision State
state.pendingImage = null;

state.pendingMime = null;

// ─── Theme Management ───────────────────────
function initTheme() {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    document.documentElement.classList.toggle('dark', savedTheme === 'dark');
  } else {
    // Auto-detect system preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.classList.toggle('dark', prefersDark);
  }

  const savedColor = localStorage.getItem('accentColor');
  if (savedColor) setAccentColor(savedColor, false);

  updateThemeIcon();
}

function updateThemeIcon() {
  const isDark = document.documentElement.classList.contains('dark');
  if (themeIcon) {
    themeIcon.setAttribute('data-lucide', isDark ? 'sun' : 'moon');
  }
  if (themeText) {
    themeText.textContent = isDark ? 'โหมดกลางวัน' : 'โหมดกลางคืน';
  }
  
  // Update class-based theme elements (e.g. inside settings/profile modals)
  document.querySelectorAll('.themeIcon').forEach(el => {
    el.setAttribute('data-lucide', isDark ? 'sun' : 'moon');
  });
  document.querySelectorAll('.themeText').forEach(el => {
    el.textContent = isDark ? 'โหมดกลางวัน' : 'โหมดกลางคืน';
  });
  
  initIcons();
}

document.addEventListener('DOMContentLoaded', () => {
  const toggleTheme = () => {
    document.documentElement.classList.toggle('dark');
    const isDark = document.documentElement.classList.contains('dark');
    state.theme = isDark ? 'dark' : 'light';
    localStorage.setItem('theme', state.theme);
    updateThemeIcon();
    toast(`เปลี่ยนธีมเป็น: ${isDark ? 'โหมดกลางคืน' : 'โหมดกลางวัน'}`, 'info');
  };

  if (themeToggle) {
    themeToggle.onclick = toggleTheme;
  }
  const profileThemeToggle = $('profileThemeToggle');
  if (profileThemeToggle) {
    profileThemeToggle.onclick = toggleTheme;
  }
});

function setAccentColor(color, save = true) {
  if (!color) return;
  const root = document.documentElement;
  const rgb = hexToRgb(color);

  root.style.setProperty('--brand-600', color);
  root.style.setProperty('--brand-rgb', rgb);

  // Update related shades slightly (simulated)
  root.style.setProperty('--brand-700', color); // Simplified for now
  root.style.setProperty('--brand-50', `${color}10`); // Low opacity hex
  root.style.setProperty('--brand-100', `${color}20`);

  if (save) localStorage.setItem('accentColor', color);

  // Highlight active button
  document.querySelectorAll('.accent-color-btn').forEach(btn => {
    const isActive = btn.dataset.color === color;
    btn.classList.toggle('ring-2', isActive);
    btn.classList.toggle('ring-offset-2', isActive);
    btn.classList.toggle('ring-brand-600', isActive);
  });
}

const accentBtns = document.querySelectorAll('.accent-color-btn');

// ─── Premium Custom Alert/Confirm Modals ───────────────────
window.showConfirm = function(title, message, options = {}) {
  return new Promise((resolve) => {
    const container = document.getElementById('customModalContainer');
    const backdrop = document.getElementById('customModalBackdrop');
    const box = document.getElementById('customModalBox');
    const titleEl = document.getElementById('customModalTitle');
    const msgEl = document.getElementById('customModalMessage');
    const cancelBtn = document.getElementById('customModalCancelBtn');
    const confirmBtn = document.getElementById('customModalConfirmBtn');
    const iconEl = document.getElementById('customModalIcon');
    const iconBg = document.getElementById('customModalIconBg');

    if (!container || !box) {
      // Fallback if elements are missing
      resolve(window.confirm(message));
      return;
    }

    // Configure text
    titleEl.textContent = title;
    msgEl.textContent = message;
    confirmBtn.textContent = options.confirmText || 'ยืนยัน';
    cancelBtn.textContent = options.cancelText || 'ยกเลิก';
    cancelBtn.classList.remove('hidden');

    // Configure Icon & Color theme
    const type = options.type || 'warning'; // success, warning, danger, info
    let iconSvg = '';
    let colorClass = '';
    let bgClass = '';

    if (type === 'danger') {
      iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" /></svg>`;
      colorClass = 'bg-rose-600';
      bgClass = 'bg-rose-50 dark:bg-rose-950/30';
      confirmBtn.className = 'px-4 py-2 text-sm font-semibold text-white bg-rose-600 rounded-xl hover:opacity-90 transition-opacity';
    } else if (type === 'success') {
      iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>`;
      colorClass = 'bg-emerald-600';
      bgClass = 'bg-emerald-50 dark:bg-emerald-950/30';
      confirmBtn.className = 'px-4 py-2 text-sm font-semibold text-white bg-emerald-600 rounded-xl hover:opacity-90 transition-opacity';
    } else if (type === 'info') {
      iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 111.085 1.085l-.04.04m-2.137.885l.01-.01m2.122-2.122a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>`;
      colorClass = 'bg-blue-600';
      bgClass = 'bg-blue-50 dark:bg-blue-950/30';
      confirmBtn.className = 'px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-xl hover:opacity-90 transition-opacity';
    } else {
      // Default warning
      iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" /></svg>`;
      colorClass = 'bg-amber-500';
      bgClass = 'bg-amber-50 dark:bg-amber-950/30';
      confirmBtn.className = 'px-4 py-2 text-sm font-semibold text-white bg-amber-500 rounded-xl hover:opacity-90 transition-opacity';
    }

    iconEl.innerHTML = iconSvg;
    iconBg.className = `w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${bgClass} text-${type === 'warning' ? 'amber-500' : type === 'danger' ? 'rose-600' : type === 'success' ? 'emerald-600' : 'blue-600'}`;
    
    // Animate Show
    container.classList.remove('hidden');
    setTimeout(() => {
      backdrop.classList.remove('opacity-0');
      backdrop.classList.add('opacity-100');
    }, 10);

    // Event listeners
    const cleanup = () => {
      confirmBtn.onclick = null;
      cancelBtn.onclick = null;
      backdrop.classList.remove('opacity-100');
      backdrop.classList.add('opacity-0');
      setTimeout(() => {
        container.classList.add('hidden');
      }, 200);
    };

    confirmBtn.onclick = () => {
      cleanup();
      resolve(true);
    };

    cancelBtn.onclick = () => {
      cleanup();
      resolve(false);
    };
  });
};

window.showAlert = function(title, message, options = {}) {
  return new Promise((resolve) => {
    const container = document.getElementById('customModalContainer');
    const backdrop = document.getElementById('customModalBackdrop');
    const box = document.getElementById('customModalBox');
    const titleEl = document.getElementById('customModalTitle');
    const msgEl = document.getElementById('customModalMessage');
    const cancelBtn = document.getElementById('customModalCancelBtn');
    const confirmBtn = document.getElementById('customModalConfirmBtn');
    const iconEl = document.getElementById('customModalIcon');
    const iconBg = document.getElementById('customModalIconBg');

    if (!container || !box) {
      window.alert(message);
      resolve();
      return;
    }

    titleEl.textContent = title;
    msgEl.textContent = message;
    confirmBtn.textContent = options.confirmText || 'ตกลง';
    cancelBtn.classList.add('hidden'); // Hide cancel button for Alert

    const type = options.type || 'info'; // success, danger, info
    let iconSvg = '';
    let bgClass = '';

    if (type === 'danger') {
      iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" /></svg>`;
      bgClass = 'bg-rose-50 dark:bg-rose-950/30';
      confirmBtn.className = 'px-4 py-2 text-sm font-semibold text-white bg-rose-600 rounded-xl hover:opacity-90 transition-opacity';
    } else if (type === 'success') {
      iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>`;
      bgClass = 'bg-emerald-50 dark:bg-emerald-950/30';
      confirmBtn.className = 'px-4 py-2 text-sm font-semibold text-white bg-emerald-600 rounded-xl hover:opacity-90 transition-opacity';
    } else {
      iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 111.085 1.085l-.04.04m-2.137.885l.01-.01m2.122-2.122a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>`;
      bgClass = 'bg-blue-50 dark:bg-blue-950/30';
      confirmBtn.className = 'px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-xl hover:opacity-90 transition-opacity';
    }

    iconEl.innerHTML = iconSvg;
    iconBg.className = `w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${bgClass} text-${type === 'danger' ? 'rose-600' : type === 'success' ? 'emerald-600' : 'blue-600'}`;

    container.classList.remove('hidden');
    setTimeout(() => {
      backdrop.classList.remove('opacity-0');
      backdrop.classList.add('opacity-100');
    }, 10);

    const cleanup = () => {
      confirmBtn.onclick = null;
      backdrop.classList.remove('opacity-100');
      backdrop.classList.add('opacity-0');
      setTimeout(() => {
        container.classList.add('hidden');
      }, 200);
    };

    confirmBtn.onclick = () => {
      cleanup();
      resolve();
    };
  });
};

// Global Toast Notification Helper
window.showToast = function (message, type = 'info') {
  let container = document.getElementById('globalToastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'globalToastContainer';
    container.className = 'fixed bottom-5 right-5 z-[10000] flex flex-col gap-2 pointer-events-none';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  const bgClass = type === 'error' || type === 'danger' ? 'bg-rose-600 text-white' : type === 'success' ? 'bg-emerald-600 text-white' : 'bg-slate-900 text-white dark:bg-surface-800';
  const icon = type === 'error' || type === 'danger' ? '❌' : type === 'success' ? '✅' : 'ℹ️';

  toast.className = `pointer-events-auto flex items-center gap-2 px-4 py-3 rounded-2xl shadow-xl text-xs font-bold transition-all duration-300 transform translate-y-4 opacity-0 ${bgClass}`;
  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;

  container.appendChild(toast);

  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-4', 'opacity-0');
  });

  setTimeout(() => {
    toast.classList.add('translate-y-4', 'opacity-0');
    setTimeout(() => {
      toast.remove();
    }, 300);
  }, 3500);
};

// ═══════════════════════════════════════════════════════════════
// 🍪 PDPA & Cookie Consent Manager (Chapter 3: Ethics & PDPA)
// ═══════════════════════════════════════════════════════════════
class PDPAConsentManager {
  constructor() {
    this.storageKey = 'orgchat_pdpa_consent_v1';
    this.consent = this.loadConsent();
  }

  loadConsent() {
    try {
      const val = localStorage.getItem(this.storageKey);
      return val ? JSON.parse(val) : null;
    } catch (e) {
      return null;
    }
  }

  saveConsent(necessary = true, preferences = true, analytics = true) {
    const data = {
      necessary: true,
      preferences: Boolean(preferences),
      analytics: Boolean(analytics),
      timestamp: new Date().toISOString()
    };
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(data));
      this.consent = data;
    } catch (e) {}
    this.hideBanner();
  }

  init() {
    if (!this.consent) {
      const banner = document.getElementById('pdpaConsentBanner');
      if (banner) banner.classList.remove('hidden');
    }
  }

  hideBanner() {
    const banner = document.getElementById('pdpaConsentBanner');
    if (banner) banner.classList.add('hidden');
    const modal = document.getElementById('pdpaPreferencesModal');
    if (modal) modal.classList.add('hidden');
  }

  openSettings() {
    const modal = document.getElementById('pdpaPreferencesModal');
    if (modal) {
      const prefCheck = document.getElementById('pdpaPrefCookies');
      const analCheck = document.getElementById('pdpaAnalCookies');
      if (prefCheck) prefCheck.checked = this.consent ? this.consent.preferences : true;
      if (analCheck) analCheck.checked = this.consent ? this.consent.analytics : true;
      modal.classList.remove('hidden');
    }
  }
}

window.pdpaConsent = new PDPAConsentManager();

// ═══════════════════════════════════════════════════════════════
// ⏱️ Auto-Session Lock & Inactivity Guard (Chapter 1 & 2)
// ═══════════════════════════════════════════════════════════════
class AutoSessionLockManager {
  constructor(timeoutMs = 15 * 60 * 1000) { // 15 minutes default
    this.timeoutMs = timeoutMs;
    this.timer = null;
    this.isLocked = false;
    this.enabled = localStorage.getItem('orgchat_autolock_enabled') !== 'false';
  }

  init() {
    if (!this.enabled) return;
    const events = ['mousedown', 'mousemove', 'keydown', 'touchstart', 'scroll'];
    events.forEach(e => window.addEventListener(e, () => this.resetTimer(), { passive: true }));
    this.resetTimer();
  }

  resetTimer() {
    if (this.isLocked) return;
    if (this.timer) clearTimeout(this.timer);
    if (!this.enabled) return;
    
    // Only lock if user is authenticated (not on login screen)
    if (document.body.classList.contains('authenticated') || document.getElementById('chatArea')) {
      this.timer = setTimeout(() => this.lockScreen(), this.timeoutMs);
    }
  }

  lockScreen() {
    this.isLocked = true;
    const lockEl = document.getElementById('screenLockOverlay');
    if (lockEl) {
      lockEl.classList.remove('hidden');
      const input = document.getElementById('lockScreenPassword');
      if (input) {
        input.value = '';
        setTimeout(() => input.focus(), 100);
      }
    }
  }

  unlock(password) {
    if (!password) {
      if (window.showToast) window.showToast('กรุณากรอกรหัสผ่านเพื่อปลดล็อก', 'error');
      return;
    }
    // Verify password against API
    fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: state.username || localStorage.getItem('orgchat_username') || 'Admin',
        password: password
      })
    })
    .then(r => r.json())
    .then(d => {
      if (d.ok) {
        this.isLocked = false;
        const lockEl = document.getElementById('screenLockOverlay');
        if (lockEl) lockEl.classList.add('hidden');
        if (window.showToast) window.showToast('ปลดล็อกหน้าจอเรียบร้อยแล้วค่ะ', 'success');
        this.resetTimer();
      } else {
        if (window.showToast) window.showToast('รหัสผ่านไม่ถูกต้อง: ' + (d.error || ''), 'error');
      }
    })
    .catch(() => {
      if (window.showToast) window.showToast('ไม่สามารถตรวจสอบรหัสผ่านได้', 'error');
    });
  }
}

window.sessionLock = new AutoSessionLockManager();

// ═══════════════════════════════════════════════════════════════
// 📊 Security Health Dashboard Controller (Chapter 1, 2, 4)
// ═══════════════════════════════════════════════════════════════

window.openSecurityDashboard = function() {
  const modal = document.getElementById('securityHealthModal');
  if (!modal) return;
  modal.classList.remove('hidden');
  window.loadSecurityDashboard();
};

window.loadSecurityDashboard = async function() {
  try {
    const res = await fetch('/api/security/health-status');
    const data = await res.json();
    if (data.ok && data.health) {
      const h = data.health;
      const scoreEl = document.getElementById('secScoreVal');
      const logIntEl = document.getElementById('secLogIntegrityVal');
      const mfaEl = document.getElementById('secMfaAdoptionVal');
      const failEl = document.getElementById('secFailedLoginsVal');
      if (scoreEl) scoreEl.innerText = `${h.overall_health_score}%`;
      if (logIntEl) logIntEl.innerText = `${h.log_integrity_percent}%`;
      if (mfaEl) mfaEl.innerText = `${h.mfa_adoption_percent || 0}%`;
      if (failEl) failEl.innerText = `${h.failed_logins_24h}`;
    }
  } catch (e) {
    console.warn('Failed to load health metrics:', e);
  }

  // Load audit logs
  try {
    const res = await fetch('/api/security/audit-logs');
    const data = await res.json();
    const listEl = document.getElementById('secAuditLogList');
    if (listEl && data.ok && Array.isArray(data.logs)) {
      if (data.logs.length === 0) {
        listEl.innerHTML = '<div class="text-center py-4 text-surface-400">ยังไม่มีบันทึกเหตุการณ์</div>';
      } else {
        listEl.innerHTML = data.logs.slice(0, 15).map(l => {
          const verifiedBadge = l.is_verified 
            ? '<span class="text-[9px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-full">✓ Verified HMAC</span>'
            : '<span class="text-[9px] font-bold text-rose-600 bg-rose-50 dark:bg-rose-950/40 px-2 py-0.5 rounded-full">⚠️ TAMPERED</span>';
          return `
            <div class="p-2.5 rounded-xl bg-surface-50 dark:bg-surface-800/40 border border-surface-200 dark:border-surface-700/60 flex items-center justify-between gap-2">
              <div class="min-w-0">
                <div class="font-bold text-surface-900 dark:text-white truncate">${l.action} <span class="text-[10px] text-surface-400 font-normal">(${l.username})</span></div>
                <div class="text-[10px] text-surface-500 truncate">${l.details || '-'} · IP: ${l.ip_address || '-'}</div>
              </div>
              <div class="flex items-center gap-2 flex-shrink-0">
                ${verifiedBadge}
                <span class="text-[9px] text-surface-400">${(l.timestamp || '').split(' ')[1] || ''}</span>
              </div>
            </div>
          `;
        }).join('');
      }
    }
  } catch (e) {
    console.warn('Failed to load audit logs:', e);
  }

  // Load Blacklisted IPs
  window.loadSecurityBlacklist();

  // Load SOC Threat Intelligence Telemetry
  window.loadSecurityThreatIntel();
};

window.loadSecurityBlacklist = async function() {
  const container = document.getElementById('secBlacklistContainer');
  if (!container) return;

  try {
    const res = await fetch('/api/security/blacklist');
    const data = await res.json();
    if (data.ok && Array.isArray(data.blacklist)) {
      if (data.blacklist.length === 0) {
        container.innerHTML = '<div class="text-center py-2 text-surface-400 text-[11px]">ไม่มี IP ที่ถูกระงับในขณะนี้</div>';
      } else {
        container.innerHTML = data.blacklist.map(b => `
          <div class="p-2.5 rounded-xl bg-white dark:bg-surface-900 border border-rose-100 dark:border-rose-900/30 flex items-center justify-between">
            <div>
              <div class="font-bold text-rose-600 font-mono text-[11px]">${b.ip_address}</div>
              <div class="text-[10px] text-surface-500">${b.reason} (พบการโจมตี ${b.violation_count} ครั้ง)</div>
            </div>
            <button type="button" onclick="unblockSecurityIp('${b.ip_address}')" class="px-2.5 py-1 bg-rose-100 hover:bg-rose-200 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300 rounded-lg text-[10px] font-bold transition">
              ปลดบล็อค
            </button>
          </div>
        `).join('');
      }
    }
  } catch (e) {
    console.warn('Failed to load blacklist:', e);
  }
};

window.unblockSecurityIp = async function(ip) {
  if (!confirm(`ยืนยันการปลดล็อค IP ${ip}?`)) return;
  try {
    const res = await fetch('/api/security/unblock-ip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip_address: ip })
    });
    const data = await res.json();
    if (data.ok) {
      window.loadSecurityBlacklist();
      window.loadSecurityDashboard();
    } else {
      alert(data.message || 'เกิดข้อผิดพลาด');
    }
  } catch (e) {
    alert('เกิดข้อผิดพลาดในการปลดล็อค IP');
  }
};

window.testPiiMasking = async function() {
  const input = document.getElementById('testPiiInput');
  const box = document.getElementById('testPiiResultBox');
  if (!input || !box) return;

  const text = input.value.trim();
  if (!text) {
    box.classList.remove('hidden');
    box.innerHTML = '<span class="text-amber-600">กรุณากรอกข้อความเพื่อทดสอบ</span>';
    return;
  }

  try {
    const res = await fetch('/api/security/mask-pii', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    });
    const data = await res.json();
    if (data.ok) {
      box.classList.remove('hidden');
      if (data.count === 0) {
        box.innerHTML = `<span class="text-emerald-600 font-bold">✅ ปลอดภัย:</span> ไม่พบข้อมูลส่วนบุคคลอ่อนไหว (PII)<div class="text-surface-400 mt-1">${data.masked_text}</div>`;
      } else {
        box.innerHTML = `
          <div class="text-rose-600 font-bold mb-1">🛡️ เซ็นเซอร์ข้อมูลอ่อนไหวแล้ว (${data.count} รายการ):</div>
          <div class="p-2 rounded bg-surface-100 dark:bg-surface-800 text-teal-600 dark:text-teal-400 font-bold">${data.masked_text}</div>
          <div class="text-[10px] text-surface-400 mt-1">ตรวจพบ: ${data.detected_items.map(i => i.type).join(', ')}</div>
        `;
      }
    }
  } catch (e) {
    box.classList.remove('hidden');
    box.innerText = '❌ เกิดข้อผิดพลาดในการทดสอบ Mask';
  }
};

window.loadSecurityThreatIntel = async function() {
  const box = document.getElementById('secThreatIntelBox');
  if (!box) return;

  try {
    const res = await fetch('/api/security/threat-intel');
    const data = await res.json();
    if (data.ok) {
      const threatIps = (data.active_threat_ips || []).map(t => `<span class="px-2 py-0.5 rounded bg-rose-100 dark:bg-rose-900/30 text-rose-600 font-bold">${t.ip} (${t.incidents} ครั้ง)</span>`).join(' ') || '<span class="text-emerald-600">ไม่มี IP ผิดปกติใน 24h</span>';
      const actions = (data.top_flagged_actions || []).map(a => `<span class="px-2 py-0.5 rounded bg-surface-100 dark:bg-surface-800 text-surface-700 dark:text-surface-300">${a.action}: ${a.count}</span>`).join(' ') || '<span class="text-surface-400">ไม่มี Alert</span>';
      
      box.innerHTML = `
        <div class="flex items-center justify-between mb-2 pb-1.5 border-b border-indigo-100 dark:border-indigo-900/30">
          <span class="font-bold text-indigo-600 dark:text-indigo-400">🛡️ SOC Threat Telemetry</span>
          <span class="text-[9px] text-emerald-600 font-bold">● ${data.intel_engine_status}</span>
        </div>
        <div class="space-y-1.5 text-[10px]">
          <div><strong class="text-surface-600 dark:text-surface-300">🚨 Top Flagged Threat IPs (24h):</strong> <div class="mt-0.5 flex flex-wrap gap-1">${threatIps}</div></div>
          <div><strong class="text-surface-600 dark:text-surface-300">📊 Security Alert Actions (24h):</strong> <div class="mt-0.5 flex flex-wrap gap-1">${actions}</div></div>
        </div>
      `;
    }
  } catch (e) {
    console.warn('Failed to load threat intel:', e);
  }
};

window.runUebaBehaviorScan = async function() {
  const box = document.getElementById('secThreatIntelBox');
  if (!box) return;
  box.innerHTML = '<span class="text-indigo-600 font-bold animate-pulse">🔍 กำลังรวบรวมและวิเคราะห์พฤติกรรม UEBA Telemetry...</span>';

  try {
    const res = await fetch('/api/security/analyze-behavior', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    const data = await res.json();
    if (data.ok && data.analysis) {
      const a = data.analysis;
      const badgeColor = a.threat_level === 'CRITICAL' ? 'bg-rose-600 text-white' : a.threat_level === 'HIGH' ? 'bg-amber-600 text-white' : 'bg-emerald-600 text-white';
      const anomaliesList = a.anomalies.length > 0 ? a.anomalies.map(an => `<li class="text-rose-500">• ${an}</li>`).join('') : '<li class="text-emerald-600">• พฤติกรรมการใช้งานปกติ ไม่พบความเสี่ยง Data Exfiltration</li>';

      box.innerHTML = `
        <div class="space-y-2">
          <div class="flex items-center justify-between pb-1.5 border-b border-indigo-100 dark:border-indigo-900/30">
            <span class="font-bold text-surface-900 dark:text-white">👤 ผลการวิเคราะห์พฤติกรรมผู้ใช้: <code>${a.username}</code></span>
            <span class="px-2.5 py-0.5 rounded-full font-bold text-[10px] ${badgeColor}">Threat Level: ${a.threat_level} (${a.risk_score}/100)</span>
          </div>
          <div class="text-[10px] space-y-1">
            <div><strong>IP:</strong> <code>${a.ip_address}</code> | <strong>5-min Request Burst:</strong> ${a.burst_count_5m} | <strong>24h Alerts:</strong> ${a.security_alerts_24h}</div>
            <ul class="mt-1 space-y-0.5">${anomaliesList}</ul>
            <div class="mt-1 text-[9px] text-surface-400">SOC Recommendation: <strong class="text-indigo-600 dark:text-indigo-400">${a.recommended_action}</strong></div>
          </div>
        </div>
      `;
    }
  } catch (e) {
    box.innerHTML = '<span class="text-rose-600">❌ เกิดข้อผิดพลาดในการวิเคราะห์ UEBA</span>';
  }
};

window.runFimScan = async function() {
  const btn = document.getElementById('btnScanFim');
  const box = document.getElementById('fimScanStatusBox');
  if (btn) btn.disabled = true;
  if (box) {
    box.classList.remove('hidden');
    box.innerText = '🔍 กำลังคำนวณและตรวจสอบ SHA-256 Hash ของไฟล์ทั้งหมดในระบบ...';
  }

  try {
    const res = await fetch('/api/security/verify-integrity', { method: 'POST' });
    const data = await res.json();
    if (data.ok && box) {
      const total = data.total_scanned || 0;
      const tampered = (data.files || []).filter(f => !f.valid);
      if (tampered.length === 0) {
        box.innerHTML = `<span class="text-emerald-600 font-bold">✅ การตรวจสอบเสร็จสิ้น:</span> สแกนไฟล์ทั้งหมด ${total} รายการ ทุกไฟล์มีความสมบูรณ์ตรงตาม Baseline 100%`;
      } else {
        box.innerHTML = `<span class="text-rose-600 font-bold">🚨 ตรวจพบไฟล์ถูกดัดแปลง (${tampered.length} ไฟล์):</span> ${tampered.map(t => t.file).join(', ')}`;
      }
    }
  } catch (e) {
    if (box) box.innerText = '❌ เกิดข้อผิดพลาดในการสแกนไฟล์';
  } finally {
    if (btn) btn.disabled = false;
  }
};

window.runKbAnomalyScan = async function() {
  const btn = document.getElementById('btnScanKbAnomalies');
  const box = document.getElementById('kbAnomalyStatusBox');
  if (btn) btn.disabled = true;
  if (box) {
    box.classList.remove('hidden');
    box.innerText = '🔍 กำลังวิเคราะห์โครงสร้างคลังความรู้ ตรวจหา Binary Duplicates (SHA-256) และ Anomaly Files...';
  }

  try {
    const res = await fetch('/api/kb/anomalies');
    const data = await res.json();
    if (data.ok && box) {
      const dupCount = data.duplicate_groups_count || 0;
      const anoCount = data.anomalies_count || 0;
      const total = data.total_scanned || 0;

      if (dupCount === 0 && anoCount === 0) {
        box.innerHTML = `<span class="text-emerald-600 font-bold">✅ คลังข้อมูลสมบูรณ์ 100%:</span> สแกนไฟล์ทั้งหมด ${total} รายการ ไม่พบไฟล์ซ้ำซ้อนหรือไฟล์ผิดปกติ`;
      } else {
        let detailsHtml = '';
        if (dupCount > 0) {
          detailsHtml += `<div class="mt-1 text-amber-600 font-bold">⚠️ พบกลุ่มไฟล์ซ้ำซ้อน ${dupCount} กลุ่ม:</div>`;
          data.duplicates.forEach(d => {
            detailsHtml += `<div class="text-[10px] text-surface-500">• ${d.suggestion}</div>`;
          });
        }
        if (anoCount > 0) {
          detailsHtml += `<div class="mt-1 text-rose-600 font-bold">🚨 พบความผิดปกติ ${anoCount} รายการ:</div>`;
          data.anomalies.forEach(a => {
            detailsHtml += `<div class="text-[10px] text-surface-500">• [${a.type}] ${a.description}</div>`;
          });
        }
        box.innerHTML = detailsHtml;
      }
    }
  } catch (e) {
    if (box) box.innerText = '❌ เกิดข้อผิดพลาดในการตรวจสอบคลังข้อมูล';
  } finally {
    if (btn) btn.disabled = false;
  }
};

// ═══════════════════════════════════════════════════════════════
// 🖨️ Dynamic Digital Watermarking & Screen Capture Guard
// ═══════════════════════════════════════════════════════════════

class DigitalWatermarkManager {
  constructor() {
    this.overlayId = 'enterpriseWatermarkOverlay';
    this.interval = null;
  }

  init() {
    // Only show watermark when user is logged in
    const username = state.username || localStorage.getItem('orgchat_username') || sessionStorage.getItem('username');
    if (!username) return;

    this.renderWatermark(username);
    
    // Periodically update timestamp every 60 seconds
    if (this.interval) clearInterval(this.interval);
    this.interval = setInterval(() => {
      this.renderWatermark(username);
    }, 60000);
  }

  renderWatermark(username) {
    let overlay = document.getElementById(this.overlayId);
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = this.overlayId;
      document.body.appendChild(overlay);
    }

    const now = new Date();
    const dateStr = now.toLocaleDateString('th-TH', { year: 'numeric', month: 'short', day: 'numeric' });
    const timeStr = now.toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' });
    const orgName = (state.currentOrg && state.currentOrg.name) || 'OrgChat Enterprise';

    // Build repeating pattern
    const itemsCount = 36;
    let itemsHtml = '';
    for (let i = 0; i < itemsCount; i++) {
      itemsHtml += `
        <div class="watermark-item">
          <span>🔒 ${username} • ${orgName}</span>
          <span style="font-size: 9px; opacity: 0.85;">${dateStr} ${timeStr} • CONFIDENTIAL</span>
        </div>
      `;
    }

    overlay.innerHTML = `<div class="watermark-pattern">${itemsHtml}</div>`;
  }
}

// ═══════════════════════════════════════════════════════════════
// 🧠 Multi-Agent AI Debate Room Controller
// ═══════════════════════════════════════════════════════════════

window.openAiDebateRoom = function() {
  const modal = document.getElementById('aiDebateModal');
  if (!modal) return;
  modal.classList.remove('hidden');
  const input = document.getElementById('debateTopicInput');
  if (input) input.focus();
};

window.startAiDebate = async function() {
  const input = document.getElementById('debateTopicInput');
  const btn = document.getElementById('btnStartDebate');
  const loadingBox = document.getElementById('debateLoadingBox');
  const container = document.getElementById('debateTranscriptsContainer');
  const listEl = document.getElementById('debateTranscriptsList');
  const consensusEl = document.getElementById('debateConsensusContent');

  if (!input) return;
  const topic = input.value.trim();
  if (!topic) {
    alert('กรุณาระบุหัวข้อที่ต้องการให้บอร์ด AI ประชุมวิเคราะห์ค่ะ');
    input.focus();
    return;
  }

  if (btn) btn.disabled = true;
  if (loadingBox) loadingBox.classList.remove('hidden');
  if (container) container.classList.add('hidden');

  try {
    const res = await fetch('/api/ai/debate/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic: topic })
    });
    const data = await res.json();

    if (data.ok && Array.isArray(data.transcripts)) {
      if (listEl) {
        listEl.innerHTML = data.transcripts.map(t => {
          const colorStyles = {
            emerald: 'bg-emerald-50/70 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900/40 text-emerald-900 dark:text-emerald-300',
            amber: 'bg-amber-50/70 dark:bg-amber-950/20 border-amber-200 dark:border-amber-900/40 text-amber-900 dark:text-amber-300',
            cyan: 'bg-cyan-50/70 dark:bg-cyan-950/20 border-cyan-200 dark:border-cyan-900/40 text-cyan-900 dark:text-cyan-300',
            rose: 'bg-rose-50/70 dark:bg-rose-950/20 border-rose-200 dark:border-rose-900/40 text-rose-900 dark:text-rose-300'
          }[t.color] || 'bg-surface-50 dark:bg-surface-800 border-surface-200';

          return `
            <div class="p-4 rounded-2xl border ${colorStyles} space-y-2">
              <div class="flex items-center gap-2 pb-1.5 border-b border-black/5 dark:border-white/5">
                <span class="text-xl">${t.avatar}</span>
                <div>
                  <div class="font-black text-xs">${t.name}</div>
                  <div class="text-[10px] opacity-75">${t.role_title}</div>
                </div>
              </div>
              <div class="text-xs leading-relaxed whitespace-pre-line text-surface-800 dark:text-surface-200">
                ${t.opinion}
              </div>
            </div>
          `;
        }).join('');
      }

      if (consensusEl) {
        // Simple markdown formatted render
        const rawConsensus = data.executive_consensus || 'ไม่มีข้อสรุป';
        consensusEl.innerHTML = rawConsensus
          .replace(/### (.*?)\n/g, '<h5 class="font-bold text-xs text-indigo-700 dark:text-indigo-300 mt-2 mb-1">$1</h5>')
          .replace(/## (.*?)\n/g, '<h4 class="font-black text-sm text-indigo-800 dark:text-indigo-200 mt-3 mb-1.5">$1</h4>')
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\n/g, '<br/>');
      }

      if (container) container.classList.remove('hidden');
    } else {
      alert(data.error || data.message || 'เกิดข้อผิดพลาดในการประชุมบอร์ด');
    }
  } catch (e) {
    alert('เกิดข้อผิดพลาดในการเชื่อมต่อระบบ AI Debate');
  } finally {
    if (btn) btn.disabled = false;
    if (loadingBox) loadingBox.classList.add('hidden');
  }
};

window.digitalWatermark = new DigitalWatermarkManager();

document.addEventListener('DOMContentLoaded', () => {
  window.pdpaConsent.init();
  window.sessionLock.init();
  window.digitalWatermark.init();
});