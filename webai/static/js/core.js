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
  currentChat: { type: 'room', id: 1, name: 'General' },
  chatList: { rooms: [], contacts: [] },
  isAdmin: false,
  canEditKB: false,
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
      if (typeof toast === 'function') {
        toast('เซสชันหมดอายุแล้ว กรุณาเข้าสู่ระบบใหม่เพื่อใช้งานต่อค่ะ', 'error');
      }
      const loginOverlay = document.getElementById('loginOverlay');
      if (loginOverlay) {
        loginOverlay.classList.remove('hidden');
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
  const p = state.personas.find(p => p.id === id);
  state.activePersona = p || null;
  if (activePersonaName) activePersonaName.textContent = p ? p.name : 'Default';
  if (personaDropdown) personaDropdown.classList.add('hidden');
  renderPersonas();
  toast(p ? `สลับเป็นตัวตน: ${p.name}` : 'กลับสู่โหมดพื้นฐาน', 'info');
}

if (personaBtn) {
  personaBtn.onclick = () => {
    personaDropdown?.classList.toggle('hidden');
  };
}

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
function showView(viewId) { switchView(viewId); }

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
  if (sidebarOverlay) sidebarOverlay.classList.toggle('active', isOpen);
}

if (mobileMenuBtn) mobileMenuBtn.onclick = () => toggleSidebar(true);

if (sidebarOverlay) sidebarOverlay.onclick = () => toggleSidebar(false);

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
    if (view) switchView(view);
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
    themeText.textContent = isDark ? 'โหมดกลางวัน' : 'โหมดกลางคืน';
    initIcons();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (themeToggle) {
    themeToggle.onclick = () => {
      document.documentElement.classList.toggle('dark');
      const isDark = document.documentElement.classList.contains('dark');
      state.theme = isDark ? 'dark' : 'light';
      localStorage.setItem('theme', state.theme);
      updateThemeIcon();
      toast(`เปลี่ยนธีมเป็น: ${isDark ? 'โหมดกลางคืน' : 'โหมดกลางวัน'}`, 'info');
    };
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