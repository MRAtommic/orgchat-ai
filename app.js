console.log("static/app.js starting...");
/* ══════════════════════════════════════════
   OrgChat — Corporate Frontend Application Logic
   ══════════════════════════════════════════ */

// ─── State ───────────────────────────────────
const state = {
  history: [],          // [{role:'user'|'bot', text}]
  sending: false,
  apiKeySet: false,
  calendar: {
    viewDate: new Date(),
    schedules: []
  },
  groupChat: {
    messages: [],
    lastId: 0,
    isOpen: false,
    pollInterval: null,
    pendingFiles: [],
    unreadCounts: { rooms: {}, dms: {} }
  },
  feedPollInterval: null,
  currentChat: { type: 'room', id: 1, name: 'General' },
  chatList: { rooms: [], contacts: [] },
  isAdmin: false,
  canEditKB: false,
  kbCategories: [],
  appSettings: {},
  personas: [],
  activePersona: null,
  postViews: {},
  lastRendered: { chatList: '', messages: '', unread: '' },
  theme: localStorage.getItem('theme') || 'auto'
};

// ─── Socket.IO Global ──────────────────────────
let socket = null;
if (typeof io !== 'undefined') {
  socket = io();
}

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

// File Preview Refs
const filePreviewModal = $('filePreviewModal');
const closePreviewBtn = $('closePreviewBtn');
const previewContent = $('previewContent');
const previewFileName = $('previewFileName');

// Helper: Scroll chat to bottom
// Helper: Scroll chat to bottom with intelligent threshold and animation awareness
function scrollToBottom(behavior = 'smooth', onlyIfAtBottom = false) {
  if (!chatArea) return;

  const threshold = 150;
  const isAtBottom = chatArea.scrollHeight - chatArea.scrollTop <= chatArea.clientHeight + threshold;

  if (!onlyIfAtBottom || isAtBottom) {
    // Use requestAnimationFrame + setTimeout to ensure height is updated after animations/DOM changes
    requestAnimationFrame(() => {
      setTimeout(() => {
        chatArea.scrollTo({ top: chatArea.scrollHeight, behavior: behavior });
      }, 10);
    });
  }
}

// Helper: Check if can edit KB
function canEditKB() {
  if (state.isAdmin) return true;
  return !!state.canEditKB;
}

// Global Error Handler for White Screen debugging
window.onerror = function (msg, url, line, col, error) {
  console.error("Critical JS Error:", msg, "at", url, ":", line);
  document.body.insertAdjacentHTML('afterbegin', `<div style="position:fixed; top:0; left:0; width:100%; min-height:50px; background:#f44336; color:white; font-family:sans-serif; font-size:12px; padding:10px; z-index:99999; overflow:auto;"><b>JS Error:</b> ${msg} (Line ${line})</div>`);
  return false;
};

const apiModal = $('apiModal');
const apiKeyInput = $('apiKeyInput');
const apiKeyToggle = $('apiKeyToggle');
const saveApiKeyBtn = $('saveApiKeyBtn');
const changeKeyBtn = $('changeKeyBtn');

const navSidebar = $('navSidebar');
const navItems = document.querySelectorAll('.nav-item');

const uploadZone = $('uploadZone');
const fileInput = $('fileInput');
const uploadProgress = $('uploadProgress');
const progressBar = $('progressBar');
const progressLabel = $('progressLabel');
const progressPercent = $('progressPercent');
const fileList = $('fileList');
const refreshFilesBtn = $('refreshFilesBtn');
const wipeDataBtn = $('wipeDataBtn');

const chatArea = $('mainChat');
const msgInput = $('msgInput');
const sendBtn = $('sendBtn');
const voiceBtn = $('voiceBtn');
const clearChatBtn = $('clearChatBtn');
const statusBadge = $('statusBadge');
const statusBadgeMobile = $('statusBadgeMobile');
const statFiles = $('statFiles');
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

// Theme Toggle listener
if (themeToggle) {
  themeToggle.onclick = () => {
    if (state.theme === 'auto') state.theme = 'dark';
    else if (state.theme === 'dark') state.theme = 'light';
    else state.theme = 'auto';
    localStorage.setItem('theme', state.theme);
    updateTheme();
    toast(`เปลี่ยนธีมเป็น: ${state.theme}`, 'info');
  };
}

const profileThemeToggle = $('profileThemeToggle');
if (profileThemeToggle) {
  profileThemeToggle.onclick = () => {
    if (state.theme === 'auto') state.theme = 'dark';
    else if (state.theme === 'dark') state.theme = 'light';
    else state.theme = 'auto';
    localStorage.setItem('theme', state.theme);
    updateTheme();
    toast(`เปลี่ยนธีมเป็น: ${state.theme}`, 'info');
  };
}
const navSettings = document.getElementById("nav-settings");
const navStats = document.getElementById("nav-stats");
const navNotifications = document.getElementById("nav-notifications");
const navNotifBadge = document.getElementById("navNotifBadge");
const csvHeaders = $('csvHeaders');
const csvBody = $('csvBody');
const saveCsvBtn = $('saveCsvBtn');
const editingFileName = $('editingFileName');
const csvStatusInfo = $('csvStatusInfo');
const addRowBtn = $('addRowBtn');
let currentEditingFileId = null;
let currentCsvHeaders = [];

// Text Editor Refs
const txtEditorModal = $('txtEditorModal');
const txtEditorContent = $('txtEditorContent');
const txtEditorTitle = $('txtEditorTitle');
const saveTxtBtn = $('saveTxtBtn');

// Unified Chat Refs
const chatRoomList = $('chatRoomList');
const chatContactList = $('chatContactList');
const chatHeaderName = $('chatHeaderName');
const chatHeaderAvatar = $('chatHeaderAvatar');
const chatHeaderStatus = $('chatHeaderStatus');
const chatInputArea = $('chatInputArea');
const createGroupModal = $('createGroupModal');
const memberSelectList = $('memberSelectList');
const confirmCreateGroup = $('confirmCreateGroup');
const cancelCreateGroup = $('cancelCreateGroup');
const newGroupName = $('newGroupName');
const openCreateGroupModal = $('openCreateGroupModal');
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
const editGroupBtn = $('editGroupBtn');
const editGroupModal = $('editGroupModal');
const editGroupName = $('editGroupName');
const groupAvatarUpload = $('groupAvatarUpload');
const groupAvatarPreview = $('groupAvatarPreview');
const confirmEditGroup = $('confirmEditGroup');
const cancelEditGroup = $('cancelEditGroup');

// WebRTC Calling Refs
const voiceCallBtn = $('voiceCallBtn');
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

// Visualization Refs
const vizFileSelect = $('vizFileSelect');
const vizXSelect = $('vizXSelect');
const vizYSelect = $('vizYSelect');
const vizTypeBtns = document.querySelectorAll('.viz-type-btn');
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
const scheduleModal = $('scheduleModal');
const closeScheduleModal = $('closeScheduleModal');
const saveScheduleBtn = $('saveScheduleBtn');
const prevMonthBtn = $('prevMonth');
const nextMonthBtn = $('nextMonth');

const scheduleTitleInput = $('scheduleTitle');
const scheduleDateInput = $('scheduleDate');
const scheduleDescInput = $('scheduleDesc');
const scheduleCatInput = $('scheduleCategory');
const scheduleTimeInput = $('scheduleTime');
const scheduleStatusInput = $('scheduleStatus');
const realtimeClock = $('realtimeClock');

// Social Feed Refs
const postInput = $('postInput');
const postCategory = $('postCategory');
const submitPostBtn = $('submitPostBtn');
const feedPosts = $('feedPosts');
const feedFilters = document.querySelectorAll('.feed-filter-chip');
const linkInputContainer = $('linkInputContainer');
const postLink = $('postLink');
const postAttachmentPreview = $('postAttachmentPreview');
const postFileInput = $('postFileInput');
let postFiles = [];

// Daily Digest Refs
const dailyDigest = $('dailyDigest');
const digestContent = $('digestContent');
const refreshDigestBtn = $('refreshDigestBtn');

// Edit Post Modal Refs
const editPostModal = $('editPostModal');
const editPostInput = $('editPostInput');
const editPostLink = $('editPostLink');
const editPostCategory = $('editPostCategory');
const saveEditPostBtn = $('saveEditPostBtn');
const closeEditPostModal = $('closeEditPostModal');
const selectAllFilesBtn = $('selectAllFiles');
const bulkDeleteBtn = $('bulkDeleteBtn');
let currentEditingPostId = null;

// Login Refs
const loginOverlay = $('loginOverlay');
const loginUsername = $('loginUsername');
const loginPassword = $('loginPassword');
const loginBtn = $('loginBtn');
const loginError = $('loginError');
const loginErrorMsg = $('loginErrorMsg');
const logoutBtn = $('logoutBtn');

// Profile Setting Refs
const profileModal = $('profileModal');
const closeProfileModal = $('closeProfileModal');
const profileTrigger = $('profileTrigger');
const saveProfileBtn = $('saveProfileBtn');
const profileNameInput = $('profileNameInput');
const avatarUploadInput = $('avatarUploadInput');
const profileAvatarPreview = $('profileAvatarPreview');
const profileCoverPreview = $('profileCoverPreview');
const bgPresetBtns = document.querySelectorAll('.bg-preset-btn');
const sidebarUserAvatar = $('sidebarUserAvatar');
const sidebarDisplayName = $('sidebarDisplayName');

// Group Chat Refs
const groupChatHead = $('groupChatHead');
const groupChatBadge = $('groupChatBadge');
const groupChatModal = $('groupChatModal');
const closeGroupChat = $('closeGroupChat');
const closeGroupChatMobile = $('closeGroupChatMobile');
const groupChatMessages = $('groupChatMessages');
const groupChatInput = $('groupChatInput');
const sendGroupChatBtn = $('sendGroupChatBtn');
const summonBotBtn = $('summonBotBtn');
const attachFileBtn = $('attachFileBtn');
const chatFileInput = $('chatFileInput');
const chatAttachmentPreview = $('chatAttachmentPreview');
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
const accentColorBtns = document.querySelectorAll('.accent-color-btn');

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
    container.className = 'toast-container fixed top-6 right-6 z-[200] flex flex-col gap-3 pointer-events-none';
    document.body.appendChild(container);
  }
  const el = document.createElement('div');
  const bgMap = {
    info: 'bg-surface-800 text-white',
    success: 'bg-emerald-600 text-white',
    error: 'bg-red-600 text-white'
  };
  el.className = `${bgMap[type] || bgMap.info} px-6 py-3 rounded-xl shadow-xl text-xs font-semibold animate-in slide-in-from-right-10 duration-300 pointer-events-auto cursor-pointer`;
  el.textContent = msg;
  el.onclick = () => el.remove();
  container.appendChild(el);
  setTimeout(() => {
    el.classList.add('animate-out', 'fade-out', 'slide-out-to-right-10');
    setTimeout(() => el.remove(), 300);
  }, 8000);
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

  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return await res.json();
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
function updateOnlineUsersList(onlineUsers) {
  /**Update UI with list of online users**/
  if (!onlineUsers || onlineUsers.length === 0) {
    console.log("No online users");
    return;
  }
  console.log("🟢 Online Users:", onlineUsers);
  // You can implement UI update here
  // For example, update chat list to show green dots next to online users
}

function showTypingIndicator(username, displayName) {
  /**Display "User is typing..." indicator**/
  const typingText = displayName || username;
  console.log(`✍️ ${typingText} is typing...`);

  // Optional: Show visual indicator in chat area
  if (chatArea) {
    // You can add a div to show "User is typing..."
    let typingDiv = chatArea.querySelector('.typing-indicator');
    if (!typingDiv) {
      typingDiv = document.createElement('div');
      typingDiv.className = 'typing-indicator text-sm text-surface-400 italic p-2';
      chatArea.appendChild(typingDiv);
    }
    typingDiv.innerHTML = `<i data-lucide="pencil" class="inline w-3 h-3 mr-1"></i>${typingText} is typing...`;
  }
}

function hideTypingIndicator(username) {
  /**Remove typing indicator**/
  console.log(`⏹️ ${username} stopped typing`);

  const typingDiv = chatArea?.querySelector('.typing-indicator');
  if (typingDiv) {
    typingDiv.remove();
  }
}

function updateMessageReadStatus(messageId, readCount, readReceipts) {
  /**Update UI with read receipts**/
  console.log(`✅ Message ${messageId} read by ${readCount} users:`, readReceipts);

  // Find the message element and add read status indicator
  const msgElement = document.querySelector(`[data-message-id="${messageId}"]`);
  if (msgElement) {
    let readBadge = msgElement.querySelector('.read-badge');
    if (!readBadge) {
      readBadge = document.createElement('span');
      readBadge.className = 'read-badge text-xs text-green-600 ml-2';
      msgElement.appendChild(readBadge);
    }
    readBadge.innerHTML = `<i data-lucide="check-check" class="inline w-3 h-3"></i> Read by ${readCount}`;
  }
}

// Status / Init
async function loadStatus() {
  try {
    const data = await apiFetch('/api/status');
    state.apiKeySet = data.api_key_set;
    if (statFiles) statFiles.textContent = data.total_files ?? 0;
    if (statChunks) statChunks.textContent = data.total_chunks ?? 0;

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
    state.canEditKB = !!data.can_edit_kb;
    state.user = data.user;
    state.username = data.user; // Ensure state.username is also set for consistency
    state.appSettings = data.app_settings || {};
    toggleAdminFeatures(state.isAdmin);

    // Join personal WebRTC room
    if (socket && state.user) {
      console.log("👤 Joining personal room via loadStatus:", state.user);
      socket.emit('join', { room: 'user_' + state.user });
    }

    // Sync UI with settings if needed
    const uploadBtn = $('uploadFilesBtn');
    if (uploadBtn) {
      if (canEditKB()) uploadBtn.classList.remove('hidden');
      else uploadBtn.classList.add('hidden');
    }
  } catch (e) {
    if (statusBadge) statusBadge.innerHTML = 'Error';
    if (statusBadgeMobile) statusBadgeMobile.innerHTML = 'Error';
  }
}

function toggleAdminFeatures(show) {
  const adminElements = [
    wipeDataBtn,
    changeKeyBtn,
    $('nav-admin'),
    $('nav-admin-mobile'),
    $('auditLogSection')
  ];

  adminElements.forEach(el => {
    if (el) el.classList.toggle('hidden', !show);
  });

  if (show) {
    initAdminChatPanel();
  }
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

function renderPersonas() {
  if (!personaList) return;
  personaList.innerHTML = `
    <div class="px-2 py-1.5 rounded-lg hover:bg-brand-50 dark:hover:bg-brand-900/30 cursor-pointer transition-all flex items-center gap-2 ${!state.activePersona ? 'bg-brand-50 dark:bg-brand-900/40 text-brand-600' : ''}" onclick="selectPersona(null)">
      <div class="w-2 h-2 rounded-full bg-brand-600"></div>
      <div class="text-[11px] font-bold">Standard Chat (Default)</div>
    </div>
  ` + state.personas.map(p => `
    <div class="px-2 py-1.5 rounded-lg hover:bg-brand-50 dark:hover:bg-brand-900/30 cursor-pointer transition-all flex items-center gap-2 ${state.activePersona?.id === p.id ? 'bg-brand-50 dark:bg-brand-900/40 text-brand-600' : ''}" onclick="selectPersona(${p.id})">
      <div class="w-1.5 h-1.5 rounded-full bg-surface-300"></div>
      <div>
        <div class="text-[11px] font-bold">${p.name}</div>
        <div class="text-[9px] text-surface-400 line-clamp-1">${p.description || ''}</div>
      </div>
    </div>
  `).join('');
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

// ─── File Preview ───────────────────────────
function openFilePreview(name, url, type) {
  if (!filePreviewModal) return;
  previewFileName.textContent = name;
  previewContent.innerHTML = '';
  filePreviewModal.classList.remove('hidden');

  const isImage = type.startsWith('image/') || url.match(/\.(jpg|jpeg|png|gif|webp)$/i);
  const isPDF = type === 'application/pdf' || url.endsWith('.pdf');

  if (isImage) {
    previewContent.innerHTML = `<img src="${url}" class="max-w-full max-h-full object-contain rounded-2xl shadow-2xl animate-in zoom-in-95 duration-300">`;
  } else if (isPDF) {
    previewContent.innerHTML = `<iframe src="${url}" class="w-full h-full border-none rounded-2xl"></iframe>`;
  } else {
    previewContent.innerHTML = `
      <div class="text-center p-12">
        <i data-lucide="file-text" class="w-20 h-20 text-surface-200 mx-auto mb-6"></i>
        <h3 class="text-xl font-bold mb-2">ไม่สามารถแสดงตัวอย่างไฟล์นี้ได้</h3>
        <p class="text-surface-400 mb-6 font-medium">กรุณาดาวน์โหลดเพื่อดูเนื้อหา</p>
        <a href="${url}" download class="btn-primary px-8 py-3 rounded-2xl">ดาวน์โหลดไฟล์</a>
      </div>
    `;
    initIcons();
  }
}

if (closePreviewBtn) {
  closePreviewBtn.onclick = () => {
    filePreviewModal.classList.add('hidden');
    previewContent.innerHTML = '';
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

function initAdminPanel() {
  loadAdminUsers();
  loadAdminDashboardStats();
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

async function loadAdminSettings() {
  try {
    const data = await apiFetch('/api/admin/settings');
    if (data && data.ok) {
      state.appSettings = data.settings;
      const chk = $('settingAllowUserEdit');
      if (chk) chk.checked = state.appSettings.allow_user_edit === '1';
    }
  } catch (e) { }
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
      // Reload files to reflect changes in UI
      loadFiles();
    }
  } catch (e) {
    toast('บันทึกการตั้งค่าล้มเหลว', 'error');
  }
}

// Global listener for settings toggle (defined in index.html)
document.addEventListener('DOMContentLoaded', () => {
  const toggle = $('settingAllowUserEdit');
  if (toggle) {
    toggle.onchange = (e) => saveAdminSetting('allow_user_edit', e.target.checked ? '1' : '0');
  }
});

// ─── View Management ────────────────────────
function switchView(viewId) {
  state.currentView = viewId;
  navItems.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === viewId);
  });

  document.querySelectorAll('.view').forEach(sec => {
    sec.classList.toggle('hidden', sec.id !== `view-${viewId}`);
  });

  // Sync mobile bottom nav active state
  document.querySelectorAll('.mobile-nav-btn[data-mobile-view]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.mobileView === viewId);
  });

  if (viewId === 'home') renderHomeDashboard();
  if (viewId === 'profile') loadProfile();
  if (viewId === 'search') {
    if (searchInput) searchInput.focus();
  }
  if (viewId === 'notifications') loadNotifications();
  if (viewId === 'stats') loadStats();
  if (viewId === 'viz') initViz();
  if (viewId === 'calendar') { loadSchedules(); loadTodoTasks(); }
  if (viewId === 'kanban') loadKanbanBoard();
  if (viewId === 'wiki') { loadWikiPages(); renderWikiContent(); }
  if (viewId === 'admin') initAdminPanel();
  if (viewId === 'kb') loadFiles();
  if (viewId === 'summary') renderSummary();
  if (viewId === 'whiteboard') initWhiteboard();

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

// Alias for index.html onclick
function showView(viewId) { switchView(viewId); }

function applyProfile(profile) {
  if (!profile) return;

  // Update Sidebar
  if (sidebarDisplayName) sidebarDisplayName.textContent = profile.display_name || profile.username;
  if (profile.avatar_url && sidebarAvatar) {
    sidebarAvatar.innerHTML = `<img src="${profile.avatar_url}" class="w-full h-full object-cover">`;
  }

  // Update Profile View Fields
  if (profileNameInput) profileNameInput.value = profile.display_name || '';
  if (profileUsernameDisplay) profileUsernameDisplay.value = profile.username || '';
  if ($('profileDeptInput')) $('profileDeptInput').value = profile.department || '';
  if (profile.avatar_url && profileAvatarPreview) {
    profileAvatarPreview.innerHTML = `<img src="${profile.avatar_url}" class="w-full h-full object-cover">`;
  }

  // Update Background
  if (profile.background_url) {
    if (profile.background_url === 'custom') {
      // Handle custom if implemented
    } else {
      document.body.style.background = profile.background_url;
      // Also update cover preview in profile view
      if (profileCoverPreview) profileCoverPreview.style.background = profile.background_url;
    }
  }

  // Update Plan Badges
  const planName = profile.plan_name || 'FREE';
  const planClass = planName.toLowerCase().includes('pro') 
    ? 'bg-gradient-to-r from-amber-200 to-yellow-400 text-amber-900 shadow-lg shadow-yellow-500/20' 
    : 'bg-surface-100 text-surface-600 dark:bg-surface-800 dark:text-surface-400';
    
  const updateBadge = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.textContent = planName;
      el.className = id === 'sidebarPlanBadge' 
        ? `px-1.5 py-0.5 rounded text-[8px] font-extrabold uppercase tracking-wider ${planClass}`
        : `px-2.5 py-1 rounded-lg text-xs font-black uppercase tracking-wider ${planClass}`;
      el.classList.remove('hidden');
    }
  };
  
  updateBadge('sidebarPlanBadge');
  updateBadge('profilePlanBadge');
}

async function loadProfile() {
  try {
    const data = await apiFetch('/api/me');
    if (data.ok && data.profile) {
      applyProfile(data.profile);
    }
  } catch (e) {
    console.error('Failed to load profile:', e);
  }
}

// ─── AI Summary Logic ────────────────────────
async function renderSummary() {
  // Just show empty state initially if no data
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
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const genBtn = $('generateGlobalSummaryBtn');
  if (genBtn) genBtn.onclick = generateGlobalSummary;

  const copyBtn = $('copySummaryBtn');
  if (copyBtn) {
    copyBtn.onclick = () => {
      const output = $('summaryOutput');
      if (!output) return;
      const text = output.innerText;
      navigator.clipboard.writeText(text).then(() => {
        toast('คัดลอกสรุปแล้ว', 'success');
      }).catch(err => {
        toast('คัดลอกไม่สำเร็จ', 'error');
      });
    };
  }
});

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

document.addEventListener('touchstart', e => {
  touchStartX = e.changedTouches[0].screenX;
}, false);

document.addEventListener('touchend', e => {
  touchEndX = e.changedTouches[0].screenX;
  handleGesture();
}, false);

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

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    document.documentElement.classList.toggle('dark');
    const isDark = document.documentElement.classList.contains('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    updateThemeIcon();
  });

  // AI Productivity Listeners
  if (aiGenKanbanBtn) aiGenKanbanBtn.onclick = () => aiGenKanbanModal.classList.remove('hidden');
  if (closeAiGenModal) closeAiGenModal.onclick = () => aiGenKanbanModal.classList.add('hidden');
  if (confirmAiGenBtn) confirmAiGenBtn.onclick = handleAiGenKanban;

  if (bulkCompareBtn) bulkCompareBtn.onclick = handleBulkCompare;
  if (closeAiCompareModal) closeAiCompareModal.onclick = () => aiCompareModal.classList.add('hidden');

  // Theme Designer Listeners
  if (customAccentInput) {
    customAccentInput.oninput = (e) => applyAccentColor(e.target.value);
  }
  accentColorBtns.forEach(btn => {
    btn.onclick = () => applyAccentColor(btn.dataset.color);
  });
  bgPresetBtns.forEach(btn => {
    btn.onclick = () => {
      const bg = btn.dataset.bg;
      if (bg === 'custom') {
        const custom = prompt('ใส่รหัสสี หรือ URL รูปภาพพื้นหลัง (e.g. #ff0000 or url(...))');
        if (custom) applyDashboardBg(custom);
      } else {
        applyDashboardBg(bg);
      }
    };
  });

  initIcons();
}

// ─── Events: Navigation ─────────────────────
if (navItems) {
  navItems.forEach(btn => {
    btn.addEventListener('click', () => {
      const view = btn.dataset.view;
      if (view) switchView(view);
    });
  });
}

// ─── Accent Color Logic ─────────────────────
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : '37, 99, 235';
}

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
accentBtns.forEach(btn => {
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
        const isAtBottom = chatArea.scrollHeight - chatArea.scrollTop <= chatArea.clientHeight + 100;

        state.history.forEach(msg => {
          appendMessage(msg.role, markdownToHtml(msg.text), msg.sources || [], false, msg.id);
        });

        // Auto-scroll if it was a manual load OR if user was already at bottom
        if (!isBackground || isAtBottom) {
          setTimeout(scrollToBottom, 50);
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

// ─── API Key Modal ────────────────────────────
function showApiModal() { apiModal.classList.remove('hidden'); }
function hideApiModal() { apiModal.classList.add('hidden'); }

apiKeyToggle.addEventListener('click', () => {
  const type = apiKeyInput.type === 'password' ? 'text' : 'password';
  apiKeyInput.type = type;
  const icon = apiKeyInput.type === 'password' ? 'eye' : 'eye-off';
  apiKeyToggle.innerHTML = `<i data-lucide="${icon}" class="w-4 h-4"></i>`;
  initIcons();
});

saveApiKeyBtn.addEventListener('click', async () => {
  const key = apiKeyInput.value.trim();
  if (!key) { toast('กรุณาใส่ API Key', 'error'); return; }
  saveApiKeyBtn.disabled = true;
  saveApiKeyBtn.textContent = 'กำลังตรวจสอบ...';
  const data = await apiFetch('/api/set_key', {
    method: 'POST',
    body: JSON.stringify({ api_key: key }),
  });
  saveApiKeyBtn.disabled = false;
  saveApiKeyBtn.textContent = 'ยืนยันและเริ่มต้น';
  if (data.ok) {
    toast('บันทึก API Key สำเร็จ', 'success');
    hideApiModal();
    await loadStatus();
    await loadFiles();
  } else {
    toast(data.error || 'เกิดข้อผิดพลาด', 'error');
  }
});

changeKeyBtn.addEventListener('click', () => {
  apiKeyInput.value = '';
  showApiModal();
});

refreshFilesBtn.onclick = async () => {
  toast('กำลังตรวจสอบไฟล์ใหม่...', 'info');
  refreshFilesBtn.classList.add('animate-spin');
  try {
    const data = await apiFetch('/api/sync', { method: 'POST' });
    if (data.results && data.results.length > 0) {
      toast(`ซิงค์ข้อมูลสำเร็จ: เพิ่ม ${data.results.length} ไฟล์ใหม่`, 'success');
    } else {
      toast('ไม่มีไฟล์ใหม่ให้อัปเดต', 'info');
    }
    await loadFiles();
    await loadStatus();
  } catch (e) {
    toast('การเปลี่ยนข้อมูลล้มเหลว', 'error');
  } finally {
    refreshFilesBtn.classList.remove('animate-spin');
  }
};

wipeDataBtn.addEventListener('click', async () => {
  if (!confirm('ยืนยันระบบ: คุณต้องการล้างฐานข้อมูลทั้งหมดใช่หรือไม่? การกระทำนี้ไม่สามารถย้อนกลับได้')) return;
  const data = await apiFetch('/api/wipe', { method: 'POST' });
  if (data.ok) {
    toast('ล้างฐานข้อมูลเรียบร้อยแล้ว', 'info');
    loadFiles();
    loadStatus();
  }
});

// ─── File Upload ──────────────────────────────
uploadZone.addEventListener('click', (e) => {
  if (e.target !== fileInput) fileInput.click();
});

uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadZone.classList.add('border-brand-600', 'bg-brand-50/50');
});
uploadZone.addEventListener('dragleave', () => {
  uploadZone.classList.remove('border-brand-600', 'bg-brand-50/50');
});
uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('border-brand-600', 'bg-brand-50/50');
  handleFiles(Array.from(e.dataTransfer.files));
});
fileInput.addEventListener('change', () => {
  handleFiles(Array.from(fileInput.files));
  fileInput.value = '';
});

// ─── Smart Search Logic ───────────────────────
let kbSearchTimeout = null;
const _kbSearchInput = $('kbSearchInput');
if (_kbSearchInput) {
  _kbSearchInput.oninput = (e) => {
    const query = e.target.value.trim();
    clearTimeout(kbSearchTimeout);
    if (!query) {
      // Reset to normal file list without re-fetching
      if (state.files && state.files.length) renderFileList(state.files);
      else loadFiles();
      return;
    }
    kbSearchTimeout = setTimeout(() => performKBSearch(query), 500);
  };
}

async function performKBSearch(query) {
  try {
    const data = await apiFetch(`/api/kb/search?q=${encodeURIComponent(query)}`);
    if (data.ok) {
      renderSearchList(data.results);
    }
  } catch (e) { console.error(e); }
}

function renderSearchList(results) {
  if (!results.length) {
    fileList.innerHTML = `
      <div class="col-span-full py-20 text-center text-surface-400">
        <i data-lucide="search-x" class="w-12 h-12 mx-auto mb-4 opacity-10"></i>
        <p>ไม่พบเนื้อหาที่เกี่ยวข้องกับ "${$('kbSearchInput').value}"</p>
      </div>`;
    initIcons();
    return;
  }

  fileList.innerHTML = results.map(r => `
    <div class="bg-white dark:bg-surface-900 border-2 border-brand-100 dark:border-brand-800 p-5 rounded-2xl flex flex-col gap-3 transition-all hover:border-brand-600 shadow-sm">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-lg bg-brand-50 dark:bg-brand-900/30 flex items-center justify-center text-brand-600">
          <i data-lucide="${FILE_LUCIDE[r.file_type] || 'file'}" class="w-4 h-4"></i>
        </div>
        <div class="flex-1 min-w-0">
          <div class="font-bold text-xs truncate uppercase tracking-tight">${r.file_name || r.source}</div>
          <div class="text-[9px] text-surface-400 font-bold uppercase">${r.location || 'Document'} • SCORE: ${(r.score * 100).toFixed(0)}%</div>
        </div>
      </div>
      <div class="text-[13px] text-surface-600 dark:text-surface-300 leading-relaxed bg-surface-50 dark:bg-surface-800/50 p-3 rounded-xl border border-surface-100 dark:border-surface-700 italic">
        "...${r.text}..."
      </div>
    </div>
  `).join('');
  initIcons();
}

async function handleFiles(files) {
  if (!files.length) return;
  const allowed = ['pdf', 'csv', 'txt', 'md', 'png', 'jpg', 'jpeg', 'bmp', 'webp', 'docx', 'xlsx'];
  const valid = files.filter(f => allowed.includes(f.name.split('.').pop().toLowerCase()));
  if (!valid.length) { toast('รูปแบบไฟล์ไม่ถูกต้อง (รองรับ PDF, Excel, Word, Text, รูปภาพ)', 'error'); return; }

  uploadProgress.classList.remove('hidden');
  updateProgress(10, 'กำลังเตรียมการ...');

  const form = new FormData();
  valid.forEach(f => form.append('files', f));
  if (deptSelect) form.append('department', deptSelect.value);

  // Auto-assign to current active category if it's not 'all' or 'unassigned'
  const activeCatBtn = document.querySelector('#kbCategorySidebar .kb-cat-item.active');
  if (activeCatBtn && activeCatBtn.dataset.id !== 'all' && activeCatBtn.dataset.id !== 'unassigned') {
    form.append('category_id', activeCatBtn.dataset.id);
  }

  try {
    updateProgress(50, 'กำลังวิเคราะห์และจัดหมวดหมู่...');
    const data = await apiFetch('/api/upload', { method: 'POST', body: form });
    updateProgress(100, 'เสร็จสมบูรณ์');

    if (data.ok) {
      const failures = data.results.filter(r => r.status === 'error');
      if (failures.length > 0) {
        toast(`ผิดพลาด ${failures.length} ไฟล์: ${failures[0].error}`, 'error');
      } else {
        toast('นำเข้าและประมวลผลข้อมูลสำเร็จ', 'success');
      }
      await loadFiles();
      await loadStatus();
    } else {
      toast(data.error || 'อัปโหลดล้มเหลว', 'error');
    }
  } catch (e) {
    toast('ข้อผิดพลาดในการเชื่อมต่อ', 'error');
  } finally {
    setTimeout(() => {
      uploadProgress.classList.add('hidden');
      updateProgress(0, '');
    }, 2000);
  }
}

function updateProgress(percent, text) {
  progressBar.style.width = `${percent}%`;
  progressPercent.textContent = `${percent}%`;
  progressLabel.textContent = text;
}

// ─── File List ────────────────────────────────
const FILE_LUCIDE = {
  pdf: 'file-text', csv: 'table-2', txt: 'file-code', md: 'file-code',
  docx: 'file-text', xlsx: 'table-2',
  png: 'image', jpg: 'image', jpeg: 'image', bmp: 'image', webp: 'image',
};

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function loadFiles() {
  try {
    const data = await apiFetch('/api/files');
    state.files = data.files || []; // Useful for filtering
    renderFileList(state.files);
    await loadCategories();
    if (typeof initDataViz === 'function') initDataViz();
  } catch (e) {
    console.error(e);
  }
}

function getKBCategoryName(id) {
  if (!id) return 'ยังไม่ได้ระบุ';
  const cat = state.kbCategories.find(c => c.id == id);
  return cat ? cat.name : 'ไม่พบหมวดหมู่';
}

// ─── Drag & Drop Handlers ──────────────────────
function handleFileDragStart(e, fileId) {
  e.dataTransfer.setData('text/plain', fileId);
  e.dataTransfer.dropEffect = 'move';
  const el = document.getElementById(`file-${fileId}`);
  if (el) el.classList.add('opacity-50');
}

function handleCategoryDragOver(e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'move';
  const btn = e.currentTarget.querySelector('.kb-cat-item');
  if (btn) btn.classList.add('bg-brand-50', 'dark:bg-brand-900/20', 'border-brand-200');
}

function handleCategoryDragLeave(e) {
  const btn = e.currentTarget.querySelector('.kb-cat-item');
  if (btn) btn.classList.remove('bg-brand-50', 'dark:bg-brand-900/20', 'border-brand-200');
}

async function handleCategoryDrop(e, catId) {
  e.preventDefault();
  const fileId = e.dataTransfer.getData('text/plain');
  const btn = e.currentTarget.querySelector('.kb-cat-item');
  if (btn) btn.classList.remove('bg-brand-50', 'dark:bg-brand-900/20', 'border-brand-200');

  if (!fileId) return;

  // If catId is 'all' or same as current, do nothing or handle accordingly
  if (catId === 'all') return;
  const targetCatId = catId === 'unassigned' ? null : catId;

  try {
    const res = await apiFetch('/api/kb/files/assign', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_id: fileId, category_id: targetCatId })
    });
    if (res.ok) {
      toast('ย้ายหมวดหมู่สำเร็จ (Drag & Drop)', 'success');
      loadFiles();
    } else {
      toast(res.error || 'ย้ายไม่สำเร็จ', 'error');
      loadFiles(); // Refresh to clear opacity
    }
  } catch (err) {
    toast('เกิดข้อผิดพลาด: ' + err.message, 'error');
    loadFiles();
  }
}

async function loadCategories() {
  try {
    const data = await apiFetch('/api/kb/categories');
    if (data.ok) {
      state.kbCategories = data.categories;
      renderCategoryUI();

      // Also populate summary dropdown
      const subCat = $('summaryCategorySelect');
      if (subCat) {
        subCat.innerHTML = '<option value="all">📚 ทุกหมวดหมู่</option>' +
          '<option value="unassigned">❔ ยังไม่ได้ระบุ</option>' +
          state.kbCategories.map(c => `<option value="${c.id}">📁 ${c.name}</option>`).join('');
      }
    }
  } catch (e) { console.error('Failed to load categories:', e); }
}

function renderCategoryUI() {
  const sidebar = $('kbCategorySidebar');
  if (!sidebar) return;

  sidebar.innerHTML = `
    <div class="drop-zone" data-id="all">
      <button class="kb-cat-item active" data-id="all">
        <i data-lucide="layers" class="w-3.5 h-3.5"></i>
        <span>ไฟล์ทั้งหมด</span>
      </button>
    </div>
    <div class="drop-zone" data-id="unassigned">
      <button class="kb-cat-item" data-id="unassigned">
        <i data-lucide="help-circle" class="w-3.5 h-3.5"></i>
        <span>ยังไม่ได้ระบุ</span>
      </button>
    </div>
    <div class="my-2 border-t border-surface-100 dark:border-surface-800"></div>
    ${state.kbCategories.map(c => `
      <div class="group flex items-center justify-between drop-zone" data-id="${c.id}">
        <button class="kb-cat-item flex-1" data-id="${c.id}">
          <i data-lucide="folder" class="w-3.5 h-3.5"></i>
          <span class="truncate">${c.name}</span>
        </button>
        ${canEditKB() ? `
          <button onclick="deleteKBCategory(${c.id})" class="p-1 px-2 opacity-0 group-hover:opacity-100 text-surface-400 hover:text-red-500 transition-all text-[10px]" title="ลบหมวดหมู่">
            <i data-lucide="x" class="w-3 h-3"></i>
          </button>
        ` : ''}
      </div>
    `).join('')}
  `;

  // Bind click & drag events
  sidebar.querySelectorAll('.kb-cat-item').forEach(btn => {
    btn.onclick = () => {
      sidebar.querySelectorAll('.kb-cat-item').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      filterFilesByCategory(btn.dataset.id);
    };
  });

  sidebar.querySelectorAll('.drop-zone').forEach(zone => {
    zone.ondragover = handleCategoryDragOver;
    zone.ondragleave = handleCategoryDragLeave;
    zone.ondrop = (e) => handleCategoryDrop(e, zone.dataset.id);
  });
  initIcons();
}

// ─── Document Viewer Logic ────────────────────────
function openPdfViewer(fileId, fileName) {
  const modal = $('pdfViewerModal');
  const frame = $('pdfFrame');
  const title = $('pdfViewerTitle');
  const loading = $('pdfLoading');
  const download = $('pdfDownloadLink');
  const csvContainer = $('csvViewerContainer');
  const csvTarget = $('csvTableTarget');
  const icon = $('pdfViewerIcon');

  if (!modal || !frame) return;

  title.textContent = `เปิดดู: ${fileName}`;
  loading.classList.remove('hidden');
  modal.classList.remove('hidden');
  csvContainer.classList.add('hidden');
  frame.classList.add('hidden');

  const isCsv = fileName.toLowerCase().endsWith('.csv');
  if (icon) {
    icon.setAttribute('data-lucide', isCsv ? 'table' : 'file-text');
    initIcons();
  }

  const viewUrl = `/api/kb/files/view/${fileId}`;
  download.href = viewUrl;

  if (isCsv) {
    // Parse and render CSV
    fetch(viewUrl)
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
  } else {
    // Standard PDF/Text viewer with Iframe
    frame.src = viewUrl;
    frame.classList.remove('hidden');
    frame.onload = () => {
      loading.classList.add('hidden');
    };
  }
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
  if (modal) modal.classList.add('hidden');
  if (frame) frame.src = '';
  if (csvTarget) csvTarget.innerHTML = '';
}

function filterFilesByCategory(catId) {
  state.currentKbCategory = catId; // Store for upload reference
  let filtered = state.files;
  if (catId === 'unassigned') {
    filtered = state.files.filter(f => !f.category_id);
  } else if (catId !== 'all') {
    filtered = state.files.filter(f => f.category_id == catId);
  }

  // Sync UI active states (just in case it was called programmatically)
  const sidebar = $('kbCategorySidebar');
  if (sidebar) {
    sidebar.querySelectorAll('.kb-cat-item').forEach(b => {
      b.classList.toggle('active', b.dataset.id == catId);
    });
  }

  renderFileList(filtered);
}

async function addKBCategory() {
  const name = prompt('ชื่อหมวดหมู่ใหม่:');
  if (!name) return;
  try {
    const res = await apiFetch('/api/kb/categories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    if (res.ok) {
      toast('เพิ่มหมวดหมู่แล้ว', 'success');
      loadCategories();
    } else {
      toast(res.error || 'ผิดพลาด', 'error');
    }
  } catch (e) {
    toast('ไม่สามารถเพิ่มหมวดหมู่ได้: ' + e.message, 'error');
  }
}

async function deleteKBCategory(id) {
  if (!confirm('ยืนยันลบหมวดหมู่? ไฟล์ในหมวดหมู่นี้จะถูกย้ายไปที่ "ยังไม่ได้ระบุ"')) return;
  try {
    const res = await apiFetch(`/api/kb/categories/${id}`, { method: 'DELETE' });
    if (res.ok) {
      toast('ลบหมวดหมู่แล้ว', 'info');
      await loadFiles(); // Reload files too to refresh category tags
    } else {
      toast(res.error || 'ลบไม่สำเร็จ', 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาดในการลบ: ' + e.message, 'error');
  }
}

async function moveFileToCategory(fileId) {
  if (!canEditKB()) return;

  // Custom simple prompt with categories
  let choices = state.kbCategories.map(c => `${c.id}: ${c.name}`).join('\n');
  let promptText = `เลือก ID ของหมวดหมู่ที่ต้องการย้ายไป (หรือเว้นว่างเพื่อย้ายไป "ยังไม่ได้ระบุ"):\n\n${choices}`;
  let catId = prompt(promptText);

  if (catId === null) return; // Cancelled

  if (catId && !state.kbCategories.find(c => c.id == catId)) {
    toast('ID หมวดหมู่ไม่ถูกต้อง', 'error');
    return;
  }

  try {
    const res = await apiFetch('/api/kb/files/assign', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_id: fileId, category_id: catId || null })
    });
    if (res.ok) {
      toast('ย้ายหมวดหมู่สำเร็จ', 'success');
      loadFiles();
    } else {
      toast(res.error || 'ย้ายไม่สำเร็จ', 'error');
    }
  } catch (e) {
    toast('เกิดข้อผิดพลาด: ' + e.message, 'error');
  }
}

function renderFileList(files) {
  if (!files.length) {
    fileList.innerHTML = `
      <div class="col-span-full py-20 text-center text-surface-400">
        <i data-lucide="files" class="w-12 h-12 mx-auto mb-4 opacity-10"></i>
        <p>ยังไม่มีไฟล์ถูกนำเข้ามาประมวลผล</p>
      </div>`;
    initIcons();
    return;
  }
  fileList.innerHTML = files.map(f => `
    <div class="bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-800 p-4 rounded-xl flex items-center gap-4 transition-all hover:border-brand-600/50 group relative cursor-grab active:cursor-grabbing" 
         id="file-${f.file_id}" 
         draggable="true" 
         ondragstart="handleFileDragStart(event, '${f.file_id}')">
      ${canEditKB() ? `<input type="checkbox" class="file-checkbox w-4 h-4 rounded border-surface-300 text-brand-600 focus:ring-brand-600 cursor-pointer" data-id="${f.file_id}">` : ''}
      <div class="w-10 h-10 bg-surface-50 dark:bg-surface-800 border border-surface-100 dark:border-surface-700 text-surface-500 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:text-brand-600 transition-colors">
        <i data-lucide="${FILE_LUCIDE[f.type] || 'file'}" class="w-5 h-5"></i>
      </div>
      <div class="flex-1 min-w-0">
        <div class="font-bold text-xs truncate uppercase tracking-tight" title="${f.name}">${f.name}</div>
        <div class="text-[10px] text-surface-400 mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 font-medium">
          <span class="text-brand-600 bg-brand-50/50 dark:bg-brand-900/20 px-1.5 py-0.5 rounded">${f.chunks} CHUNKS</span>
          <span class="hidden sm:inline text-surface-300">•</span>
          <span class="text-purple-600 font-bold uppercase">${f.department || 'General'}</span>
          <span class="hidden sm:inline text-surface-300">•</span>
          <span class="text-emerald-600 font-bold uppercase">${getKBCategoryName(f.category_id)}</span>
          <span class="hidden sm:inline text-surface-300">•</span>
          <span class="text-surface-500 font-mono">${formatSize(f.size)}</span>
        </div>
      </div>
      <div class="flex items-center gap-1 flex-shrink-0">
        <button class="file-view-btn p-2 text-surface-400 hover:text-brand-600 transition-colors focus:ring-2 focus:ring-brand-500/20 rounded-lg" data-id="${f.file_id}" data-name="${f.name}" title="เปิดอ่าน">
          <i data-lucide="eye" class="w-4 h-4"></i>
        </button>
        <button class="file-scan-btn p-2 text-surface-400 hover:text-purple-600 transition-colors focus:ring-2 focus:ring-purple-500/20 rounded-lg" data-id="${f.file_id}" title="สแกนด้วย AI">
          <i data-lucide="search-sparkles" class="w-4 h-4"></i>
        </button>
        ${canEditKB() ? `
          <button class="file-move-btn p-2 text-surface-400 hover:text-emerald-600 transition-colors focus:ring-2 focus:ring-emerald-500/20 rounded-lg" data-id="${f.file_id}" title="เปลี่ยนหมวดหมู่">
            <i data-lucide="folder-input" class="w-4 h-4"></i>
          </button>
        ` : ''}
        ${(String(f.type).toLowerCase() === 'csv' || String(f.type).toLowerCase() === 'txt') && canEditKB() ? `
          <button class="file-edit-btn p-2 text-surface-400 hover:text-brand-600 transition-colors focus:ring-2 focus:ring-brand-500/20 rounded-lg" data-id="${f.file_id}" data-type="${f.type}" title="แก้ไขไฟล์">
            <i data-lucide="edit-3" class="w-4 h-4"></i>
          </button>
        ` : ''}
        ${canEditKB() ? `
          <button class="file-del-btn p-2 text-surface-400 hover:text-red-500 transition-colors focus:ring-2 focus:ring-red-500/20 rounded-lg" data-id="${f.file_id}" title="ลบไฟล์">
            <i data-lucide="trash-2" class="w-4 h-4"></i>
          </button>
        ` : ''}
      </div>
    </div>
  `).join('');

  // Re-bind events
  fileList.querySelectorAll('.file-del-btn').forEach(btn => {
    btn.addEventListener('click', (e) => { e.stopPropagation(); deleteFile(btn.dataset.id); });
  });
  fileList.querySelectorAll('.file-view-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      openPdfViewer(btn.dataset.id, btn.dataset.name);
    });
  });
  fileList.querySelectorAll('.file-scan-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      scanFileWithAI(btn.dataset.id);
    });
  });
  fileList.querySelectorAll('.file-move-btn').forEach(btn => {
    btn.addEventListener('click', (e) => { e.stopPropagation(); moveFileToCategory(btn.dataset.id); });
  });
  fileList.querySelectorAll('.file-edit-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (btn.dataset.type === 'csv') openCsvEditor(btn.dataset.id);
      else openTxtEditor(btn.dataset.id);
    });
  });
  fileList.querySelectorAll('.file-checkbox').forEach(cb => {
    cb.addEventListener('change', updateBulkBar);
  });
  initIcons();
  updateBulkBar();
}

function updateBulkBar() {
  const cbs = fileList.querySelectorAll('.file-checkbox:checked');
  const bar = $('bulkActionBar');
  const count = $('selectedCount');
  if (!bar) return;
  if (cbs.length > 0) {
    bar.style.display = 'flex';
    if (count) count.textContent = `${cbs.length} รายการ`;
  } else {
    bar.style.display = 'none';
  }
}

if (selectAllFilesBtn) {
  selectAllFilesBtn.onclick = () => {
    const cbs = fileList.querySelectorAll('.file-checkbox');
    const allChecked = Array.from(cbs).every(cb => cb.checked);
    cbs.forEach(cb => cb.checked = !allChecked);
    updateBulkBar();
  };
}

if (bulkDeleteBtn) {
  bulkDeleteBtn.onclick = async () => {
    const cbs = fileList.querySelectorAll('.file-checkbox:checked');
    if (!cbs.length) return;
    if (!confirm(`Confirm: Delete ${cbs.length} files permanently?`)) return;

    bulkDeleteBtn.disabled = true;
    bulkDeleteBtn.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i> DELETING...';
    initIcons();

    for (const cb of cbs) {
      const fileId = cb.dataset.id;
      const item = $(`file-${fileId}`);
      if (item) item.classList.add('opacity-30', 'grayscale');
      await apiFetch(`/api/files/${fileId}`, { method: 'DELETE' });
    }

    toast(`Successfully deleted ${cbs.length} files`, 'success');
    await loadFiles();
    await loadStatus();
    bulkDeleteBtn.disabled = false;
    bulkDeleteBtn.innerHTML = '<i data-lucide="trash-2" class="w-3 h-3"></i> Delete Selected';
    initIcons();
  };
}

async function deleteFile(fileId) {
  if (!fileId) { console.error('Delete failed: No fileId provided'); return; }
  console.log('🗑️ Attempting to delete file:', fileId);
  const item = $(`file-${fileId}`);
  if (item) item.classList.add('opacity-30', 'grayscale');
  try {
    const data = await apiFetch(`/api/files/${fileId}`, { method: 'DELETE' });
    if (data.ok) {
      toast('ลบไฟล์สำเร็จแล้ว', 'success');
      await loadFiles();
      await loadStatus();
    } else {
      throw new Error(data.error || 'Unknown error');
    }
  } catch (e) {
    if (item) item.classList.remove('opacity-30', 'grayscale');
    console.error('Delete failed:', e);
    toast('ลบไฟล์ไม่สำเร็จ: ' + e.message, 'error');
  }
}

refreshFilesBtn.addEventListener('click', async () => {
  await loadFiles();
  await loadStatus();
});

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

function renderSearchResults(results, query = '') {
  const searchTerms = (query || (searchInput ? searchInput.value.trim() : '')).toLowerCase().split(/\s+/).filter(t => t.length > 1);
  const spinner = $('searchSpinner');
  const emptyState = $('searchEmptyState');
  if (spinner) spinner.classList.add('hidden');

  if (!results.length) {
    if (!query) {
      if (emptyState) emptyState.classList.remove('hidden');
      searchResults.innerHTML = '';
      if (emptyState) searchResults.appendChild(emptyState);
    } else {
      searchResults.innerHTML = `
        <div class="flex flex-col items-center justify-center py-20 text-center animate-in fade-in duration-500">
          <div class="w-16 h-16 bg-surface-100 dark:bg-surface-800 rounded-2xl flex items-center justify-center mb-4 text-surface-400">
            <i data-lucide="search-x" class="w-8 h-8"></i>
          </div>
          <p class="text-surface-700 dark:text-surface-300 font-semibold text-base">ไม่พบข้อมูลที่เกี่ยวข้อง</p>
          <p class="text-surface-400 text-sm mt-1 font-medium">ลองใช้คำค้นหาอื่น หรือตรวจสอบการสะกดคำ</p>
        </div>`;
    }
    initIcons();
    return;
  }

  if (emptyState) emptyState.classList.add('hidden');

  // Group by type
  const grouped = {};
  results.forEach(r => {
    if (!grouped[r.type]) grouped[r.type] = [];
    grouped[r.type].push(r);
  });

  const highlight = (text) => {
    if (!searchTerms.length) return text;
    let out = text;
    searchTerms.forEach(term => {
      const regex = new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      out = out.replace(regex, '<mark class="search-highlight">$1</mark>');
    });
    return out;
  };

  searchResults.innerHTML = `
    <div class="text-[10px] font-black uppercase tracking-[0.15em] text-surface-400 mb-4">
      พบ ${results.length} ผลลัพธ์ที่เกี่ยวข้อง
    </div>
    <div class="space-y-6">
      ${Object.entries(grouped).map(([type, items]) => `
        <div>
          <div class="flex items-center gap-2 mb-3">
            <span class="inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full border ${TYPE_COLOR[type] || 'text-surface-500 bg-surface-50 border-surface-200'}">
              <i data-lucide="${TYPE_ICON[type] || 'file'}" class="w-3 h-3"></i>
              ${TYPE_LABEL[type] || type} (${items.length})
            </span>
          </div>
          <div class="space-y-3">
            ${items.map((r, idx) => `
              <a href="${r.link || '#'}" onclick="showView('${r.link?.replace('#', '') || ''}'); return false;"
                class="block search-result-card bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-800 p-4 rounded-2xl hover:border-indigo-400/40 hover:shadow-lg hover:shadow-indigo-500/5 transition-all duration-300 animate-in slide-in-from-bottom-4 cursor-pointer"
                style="animation-delay: ${idx * 50}ms">
                <div class="flex items-start gap-3">
                  <div class="w-8 h-8 rounded-xl ${TYPE_COLOR[type] || 'bg-surface-50 border-surface-100 text-surface-500'} border flex items-center justify-center flex-shrink-0">
                    <i data-lucide="${TYPE_ICON[type] || 'file'}" class="w-4 h-4"></i>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                      <span class="text-[10px] font-bold text-surface-500 uppercase">${r.author || ''}</span>
                      <span class="text-[10px] text-surface-300">•</span>
                      <span class="text-[10px] text-surface-400">${(r.timestamp || '').substring(0, 16)}</span>
                      ${r.category ? `<span class="text-[9px] font-bold px-1.5 py-0.5 bg-surface-100 dark:bg-surface-800 rounded text-surface-500 uppercase">${r.category}</span>` : ''}
                    </div>
                    <div class="text-sm text-surface-700 dark:text-surface-300 leading-relaxed line-clamp-2">
                      ${highlight(r.text || '')}
                    </div>
                  </div>
                </div>
              </a>
            `).join('')}
          </div>
        </div>
      `).join('')}
    </div>`;
  initIcons();
}

function debounce(fn, ms) {
  let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn.apply(this, args), ms); };
}

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
  row.className = `flex gap-4 ${isUser ? 'flex-row-reverse' : 'flex-row'} animate-in fade-in group/msgrow`;
  if (msgId) row.dataset.id = msgId;

  const icon = isUser ? 'user' : 'bot';
  const avatarClass = isUser ? 'bg-surface-800' : 'bg-brand-600';
  const name = isUser ? 'USER' : 'ORG AI';
  const bubbleClass = isUser
    ? 'bg-brand-600 text-white rounded-xl rounded-tr-none text-sm p-3'
    : 'bg-surface-100 dark:bg-surface-800 text-surface-900 dark:text-surface-100 rounded-xl rounded-tl-none text-sm p-3 border border-surface-200 dark:border-surface-700';

  let feedbackPanel = !isUser ? `
    <div class="absolute -right-2 top-0 translate-x-full opacity-0 group-hover/msg:opacity-100 transition-opacity flex flex-col gap-1">
      <button class="speak-btn p-1.5 glass rounded-lg hover:text-brand-600 transition-colors" title="ฟังเสียง"><i data-lucide="volume-2" class="w-3.5 h-3.5"></i></button>
      <button class="fb-btn p-1.5 glass rounded-lg hover:text-emerald-500 transition-colors" data-val="1"><i data-lucide="thumbs-up" class="w-3.5 h-3.5"></i></button>
      <button class="fb-btn p-1.5 glass rounded-lg hover:text-red-500 transition-colors" data-val="-1"><i data-lucide="thumbs-down" class="w-3.5 h-3.5"></i></button>
      ${msgId ? `<button class="del-msg-btn p-1.5 glass rounded-lg hover:text-red-500 transition-colors" title="ลบข้อความ"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>` : ''}
    </div>` : (msgId ? `
    <div class="absolute -left-2 top-0 -translate-x-full opacity-0 group-hover/msg:opacity-100 transition-opacity flex flex-col gap-1">
      <button class="del-msg-btn p-1.5 glass rounded-lg hover:text-red-200 transition-colors" title="ลบข้อความ"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>
    </div>` : '');

  row.innerHTML = `
    <div class="w-8 h-8 flex-shrink-0 rounded-lg ${avatarClass} flex items-center justify-center text-white">
      <i data-lucide="${icon}" class="w-4 h-4"></i>
    </div>
    <div class="flex flex-col gap-1.5 max-w-[85%] min-w-0 ${isUser ? 'items-end' : 'items-start'}">
      <span class="text-[9px] font-bold text-surface-400 tracking-widest uppercase">${name}</span>
      <div class="${bubbleClass} text-[11px] max-w-none leading-relaxed relative group/msg break-words overflow-hidden w-fit min-w-0">
        ${html}
        ${feedbackPanel}
      </div>
      ${sources.length ? `
        <div class="flex flex-wrap gap-0.5 mt-1 ${isUser ? 'justify-end' : 'justify-start'}">
          ${sources.map(s => `<span style="font-size:5.5px !important; line-height:1; letter-spacing: -0.01em;" class="px-0.5 py-0.5 bg-white/40 dark:bg-surface-900/40 border border-surface-200/50 dark:border-surface-800/50 rounded-sm text-surface-400 font-medium uppercase truncate max-w-[45px] opacity-40 hover:opacity-100 transition-opacity cursor-default inline-flex items-center" title="${s}">${s}</span>`).join('')}
        </div>` : ''}
    </div>`;

  chatArea.appendChild(row);

  // Attach speak listener
  const speakBtn = row.querySelector('.speak-btn');
  if (speakBtn) {
    speakBtn.onclick = () => {
      const textToSpeak = row.querySelector('.prose').innerText;
      speak(textToSpeak);
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
  if (!confirm('ต้องการลบข้อความนี้ใช่หรือไม่?')) return;
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
      <span class="text-[9px] font-bold text-surface-400 tracking-widest uppercase">ORG AI</span>
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

function markdownToHtml(text) {
  if (typeof marked === 'undefined') return text;
  return marked.parse(text);
}

async function sendMessage(text) {
  if (state.sending || !text.trim()) return;
  if (!state.apiKeySet) { showApiModal(); return; }

  const welcome = $('welcomeScreen');
  if (welcome) welcome.remove();
  suggestions.classList.add('hidden');

  state.sending = true;
  sendBtn.disabled = true;
  msgInput.disabled = true;

  appendMessage('user', text, [], true); // This will scroll to bottom
  state.history.push({ role: 'user', text });
  saveHistory();

  showTyping(); // This will also scroll to bottom

  try {
    const payload = {
      message: text,
      history: state.history,
      persona_id: state.activePersona ? state.activePersona.id : null
    };

    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

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
            // Don't update UI during streaming - wait until stream is complete
          }
        } catch (je) {
          console.warn('Chunk parse error:', je, jsonStr);
        }
      }
    }

    // Final scroll after stream done - use auto to prevent drifting
    scrollToBottom('auto', true);

    // Display the complete bot message once streaming is done
    if (botText) {
      botMsgEl = appendMessage('bot', markdownToHtml(botText), sources, false, botId);

      // Add sources if available
      if (sources.length && botMsgEl) {
        const sContainer = document.createElement('div');
        sContainer.className = 'flex flex-wrap gap-1 mt-1';
        sContainer.innerHTML = sources.map(s => `<span class="px-1.5 py-0 bg-white dark:bg-surface-900 border border-surface-100 dark:border-surface-800 rounded text-[8px] text-surface-400 font-bold uppercase tracking-wider truncate max-w-[140px] opacity-70 hover:opacity-100 transition-opacity cursor-default" title="${s}">📎 ${s}</span>`).join('');
        const col = botMsgEl.querySelector('.flex-col') || botMsgEl.children[1];
        if (col) col.appendChild(sContainer);
      }
    }

    // Scroll to new message
    scrollToBottom('smooth', false);

    // Push bot message to local history so UI stays in sync
    if (botMsgEl) {
      state.history.push({ id: botId, role: 'bot', text: botText, sources: sources });
      saveHistory();
    }

  } catch (e) {
    removeTyping();
    let msg = e.message;
    if (msg.includes('429') || msg.toLowerCase().includes('quota')) {
      msg = "🛑 โควต้า Gemini ของคุณหมดชั่วคราว (Free Tier Limit) กรุณารอประมาณ 1 นาทีแล้วลองใหม่อีกครั้งครับ หากยังไม่ได้แนะนำให้เปลี่ยน API Key ใบใหม่ครับ";
    }
    appendMessage('bot', `<div class="p-3 rounded-lg border border-red-200 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm font-medium">⚠️ ${msg}</div>`);
  } finally {
    state.sending = false;
    sendBtn.disabled = false;
    msgInput.disabled = false;
    msgInput.focus();
  }
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

// ─── Voice Interaction (STT/TTS) ──────────────
let recognition = null;
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.lang = 'th-TH'; // Default to Thai
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = () => {
    voiceBtn.classList.add('voice-active');
    voiceBtn.innerHTML = '<i data-lucide="mic-off" class="w-4 h-4"></i>';
    initIcons();
    toast('กำลังฟัง...', 'info');
  };

  recognition.onend = () => {
    voiceBtn.classList.remove('voice-active');
    voiceBtn.innerHTML = '<i data-lucide="mic" class="w-4 h-4"></i>';
    initIcons();
  };

  recognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    msgInput.value = text;
    autoResize();
    // Auto-send after a short delay for better UX
    setTimeout(() => {
      const currentText = msgInput.value.trim();
      if (currentText) {
        msgInput.value = '';
        autoResize();
        sendMessage(currentText);
      }
    }, 1000);
  };

  recognition.onerror = (e) => {
    console.error('Speech Recognition Error:', e);
    toast('ไม่สามารถรับข้อมูลจากไมค์ได้', 'error');
  };
}

function speak(text) {
  if (!('speechSynthesis' in window)) return;
  // Stop any current speech
  window.speechSynthesis.cancel();

  // Clean markdown for better speech
  const cleanText = text.replace(/[#*`_~]/g, '').slice(0, 300); // Limit length
  const msg = new SpeechSynthesisUtterance(cleanText);
  msg.lang = 'th-TH';
  window.speechSynthesis.speak(msg);
}

if (voiceBtn) {
  voiceBtn.onclick = () => {
    if (!recognition) {
      toast('เบราว์เซอร์ของคุณไม่รองรับการสั่งงานด้วยเสียง', 'error');
      return;
    }
    try {
      recognition.start();
    } catch (e) {
      recognition.stop();
    }
  };
}

// ─── Bootstrap ────────────────────────────────
(async () => {
  initTheme();
  initIcons();
  showWelcome();
  loadHistory();
  await loadStatus();
  await loadFiles();
  await loadPersonas();
  msgInput.focus();

  // ─── Global Background Poller ─────────────────────────────────
  // Runs every 5 seconds regardless of current view.
  // Keeps notification badges and chat unread counts synced
  // across all users on the network (Pi multi-device support).
  setInterval(async () => {
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

    // 2. Refresh chat unread counts + sidebar (only when NOT actively polling chat already)
    if (!state.groupChat.pollInterval) {
      try {
        const uData = await apiFetch('/api/chat/unread');
        if (uData && uData.ok && uData.unread) {
          const { rooms = {}, dms = {} } = uData.unread;
          // Merge into state without clearing current active chat
          Object.entries(rooms).forEach(([id, cnt]) => {
            if (cnt > 0) state.groupChat.unreadCounts.rooms[id] = cnt;
          });
          Object.entries(dms).forEach(([id, cnt]) => {
            if (cnt > 0) state.groupChat.unreadCounts.dms[id] = cnt;
          });
          updateGlobalChatBadge();
          renderChatSidebar();
        }
      } catch (e) { /* silent */ }
    }

  }, 5000);
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

      ${p.link ? `
        <div id="link-preview-${p.id}" class="post-preview-container">
          <a href="${p.link}" target="_blank" class="block p-4 bg-surface-50 dark:bg-surface-800/40 rounded-2xl border border-surface-100 dark:border-surface-700 hover:border-brand-500 transition-all group">
            <div class="flex gap-4">
              <div id="lp-img-${p.id}" class="hidden w-20 h-20 rounded-xl overflow-hidden bg-surface-200 flex-shrink-0 animate-pulse"></div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 text-brand-600 mb-1">
                  <i data-lucide="link" class="w-3 h-3"></i>
                  <span class="text-[10px] font-bold truncate uppercase tracking-widest">${p.link.split('/')[2] || 'LINK'}</span>
                </div>
                <h4 id="lp-title-${p.id}" class="text-xs font-bold text-surface-900 dark:text-white mb-1 truncate">${p.link}</h4>
                <p id="lp-desc-${p.id}" class="text-[10px] text-surface-500 line-clamp-2 leading-snug"></p>
              </div>
            </div>
          </a>
        </div>
      ` : ''}

      ${p.attachments && p.attachments.length ? `
        <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
          ${p.attachments.map(file => {
      const isImg = file.type?.startsWith('image/') || file.path.match(/\.(jpg|jpeg|png|gif|webp)$/i);
      const path = file.path;
      const name = file.name;
      const type = file.type || '';

      if (isImg) {
        return `
                <div class="relative group/att overflow-hidden rounded-xl border border-surface-100 dark:border-surface-800 aspect-video">
                  <img src="${path}" class="w-full h-full object-cover transition-transform group-hover/att:scale-110 duration-500 cursor-pointer" onclick="openLightbox('${path}')">
                  <button onclick="openFilePreview('${name}', '${path}', 'image/jpeg')" class="absolute inset-0 bg-black/40 opacity-0 group-hover/att:opacity-100 transition-opacity flex items-center justify-center text-white gap-2 text-[10px] font-bold">
                    <i data-lucide="eye" class="w-4 h-4"></i> Quick Look
                  </button>
                </div>
              `;
      }
      return `
              <div class="flex items-center gap-2 p-3 bg-surface-50 dark:bg-surface-800/40 border border-surface-100 dark:border-surface-700 rounded-xl hover:border-brand-500 transition-all truncate group/file text-[10px] font-bold relative">
                <i data-lucide="file-text" class="w-4 h-4 text-surface-400"></i>
                <span class="truncate pr-8">${name}</span>
                <button onclick="openFilePreview('${name}', '${path}', '${type}')" class="absolute right-2 p-1.5 bg-brand-500 text-white rounded-lg opacity-0 group-hover/file:opacity-100 transition-all">
                   <i data-lucide="eye" class="w-3 h-3"></i>
                </button>
              </div>
            `;
    }).join('')}
        </div>
      ` : ''}

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

submitPostBtn.onclick = async () => {
  const content = postInput.value.trim();
  const category = postCategory.value;
  const link = postLink.value.trim();

  const pollComp = $('pollComposer');
  const isPollActive = pollComp && !pollComp.classList.contains('hidden');
  const pollQuestion = isPollActive ? $('pollQuestion').value.trim() : '';

  if (!content && !link && postFiles.length === 0 && !pollQuestion) {
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
  toast('กำลังลบโพสต์...', 'info');
  if (!confirm('ยืนยัน: คุณต้องการลบโพสต์นี้ถาวรใช่หรือไม่?')) return;

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

async function submitComment(pid) {
  const input = $(`comment-input-${pid}`);
  const content = input.value.trim();
  if (!content) return;

  try {
    await apiFetch(`/api/posts/${pid}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, author: typeof state.user === 'object' ? state.user?.username : (state.user || 'Current User') })
    });
    input.value = '';
    const el = $(`comments-${pid}`);
    el.classList.add('hidden'); // Close it
    loadPosts(); // Refresh for count
    toggleComments(pid); // Re-open to show new comment
  } catch (e) { toast('คอมเมนต์ล้มเหลว', 'error'); }
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
function highlightMentions(text) {
  if (!text) return '';
  return text.replace(/@(\w+)/g, '<span class="mention-tag">@$1</span>');
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
  el.style.display = 'block';
  // Trigger animation
  requestAnimationFrame(() => { el.style.opacity = '1'; el.style.transform = 'scale(1) translateY(0)'; });
}

function hideReactionPickerDelayed(pid) {
  _pickerTimers[pid] = setTimeout(() => {
    const el = document.getElementById(`rpicker-${pid}`);
    if (el) {
      el.style.opacity = '0';
      el.style.transform = 'scale(0.85) translateY(4px)';
      setTimeout(() => { if (el) el.style.display = 'none'; }, 160);
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

feedFilters.forEach(btn => {
  btn.onclick = () => {
    feedFilters.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    showView(this.dataset.view);
  };
});

/* ─── Web Sockets & Theme Initialization ─── */
function initSocket() {
  if (!socket) return;

  socket.on('connect', () => {
    console.log("✅ Socket connected!");
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

  socket.on('new_message', (data) => {
    // Optimistic UI means we already added our own message.
    // Only append if it's from someone else and for the current chat.
    if (data.sender !== state.username && (
      (data.room_id && state.currentChat.type === 'room' && data.room_id === state.currentChat.id) ||
      (data.recipient && state.currentChat.type === 'dm' && data.sender === state.currentChat.id)
    )) {
      loadChatMessages(true); // simplest way for now, keep it synced
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
    showTypingIndicator(data.username, data.display_name || data.username);
  });

  socket.on('user_stopped_typing', (data) => {
    console.log("⏹️ User Stopped Typing:", data.username);
    hideTypingIndicator(data.username);
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

  // WebRTC Signaling — handled by initWebRTCSignaling() at bottom of file

}

function updateTheme() {
  const isDark = state.theme === 'dark' ||
    (state.theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches);

  document.documentElement.classList.toggle('dark', isDark);
  
  // Sync all theme elements (icons & text)
  document.querySelectorAll('.themeIcon').forEach(el => {
    el.setAttribute('data-lucide', isDark ? 'sun' : 'moon');
  });
  document.querySelectorAll('.themeText').forEach(el => {
    el.innerText = isDark ? 'โหมดกลางวัน' : 'โหมดกลางคืน';
  });

  // Backward compatibility for old IDs
  const oldIcon = $('themeIcon');
  const oldText = $('themeText');
  if (oldIcon) oldIcon.setAttribute('data-lucide', isDark ? 'sun' : 'moon');
  if (oldText) oldText.innerText = isDark ? 'โหมดกลางวัน' : 'โหมดกลางคืน';

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
    _todoTasks = (data.schedules || []).filter(s => s.category === 'Task');
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
        <span class="text-xs font-medium text-surface-700 dark:text-surface-300 leading-tight ${isDone ? 'line-through text-surface-400' : ''}">${t.title}</span>
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

  calendarMonth.textContent = new Intl.DateTimeFormat('th-TH', { month: 'long', year: 'numeric' }).format(date);

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

    div.className = `bg-white dark:bg-surface-900 min-h-[80px] p-2 border-t border-l border-surface-100 dark:border-surface-800 transition-all hover:bg-brand-50/30 dark:hover:bg-brand-900/10 relative ${isToday ? 'ring-1 ring-inset ring-brand-600/50' : ''} ${isSunday ? 'bg-rose-50/50 dark:bg-rose-900/10' : ''}`;

    let html = `<span class="text-[10px] font-bold ${isToday ? 'bg-brand-600 text-white w-5 h-5 flex items-center justify-center rounded-full' : (isSunday ? 'text-rose-600' : 'text-surface-400')}">${day}</span>`;

    // Check for schedules on this day
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const holidayKey = dateStr;
    const holidayName = THAI_HOLIDAYS_2026[holidayKey];

    const daySchedules = state.calendar.schedules.filter(s => s.date === dateStr);

    if (holidayName || daySchedules.length > 0) {
      html += `<div class="mt-1 space-y-1">`;

      // Render Holiday first
      if (holidayName) {
        html += `<div class="text-[8px] px-1 py-0.5 rounded truncate font-black bg-rose-100 dark:bg-rose-900/40 text-rose-600 dark:text-rose-400 border border-rose-200/50" title="${holidayName}">Holiday: ${holidayName}</div>`;
      }

      daySchedules.forEach(s => {
        const catColors = {
          Meeting: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
          Event: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
          Task: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
          Holiday: 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400'
        };
        const isDone = s.status === 'done';
        const publicBadge = s.is_public ? '<span class="text-[6px] bg-emerald-500 text-white px-0.5 rounded ml-1 uppercase">Public</span>' : '';
        const doneClass = isDone ? 'opacity-50 line-through decoration-brand-600' : '';
        const doneIcon = isDone ? '<i data-lucide="check-circle-2" class="w-2 h-2 inline-block mr-0.5 text-emerald-600 shrink-0"></i>' : '';

        html += `<div class="group/item relative flex flex-col items-start justify-between text-[8px] px-1 py-0.5 mb-1 rounded font-semibold ${catColors[s.category] || 'bg-surface-100 text-surface-600'} ${doneClass}" 
                    title="${s.title}" onclick="event.stopPropagation(); editSchedule(${s.id})">
          <div class="flex items-start w-full whitespace-normal leading-[1.2] text-left">
            <div class="flex items-center shrink-0 mt-[1px] opacity-80 font-bold">
               ${doneIcon}
               <span class="text-[7px] mr-1 uppercase">${s.time || '09:00'}</span>
            </div>
            <span class="break-words flex-1 w-full leading-[1.2] text-[8px]">${s.title}${publicBadge}</span>
          </div>
          
          <div class="hidden group-hover/item:flex items-center gap-1 absolute right-1 top-1 bg-white/90 dark:bg-surface-800/90 shadow-sm px-1 py-0.5 rounded-md backdrop-blur-sm z-10 border border-surface-200 dark:border-surface-700">
            <button class="text-emerald-500 hover:text-emerald-700 transition-colors" 
                    title="${isDone ? 'Mark as To-Do' : 'Mark as Done'}"
                    onclick="event.stopPropagation(); toggleScheduleStatus(${s.id})">
              <i data-lucide="${isDone ? 'rotate-ccw' : 'check'}" class="w-3 h-3"></i>
            </button>
            <button class="text-red-500 hover:text-red-700 transition-colors" 
                    title="Delete"
                    onclick="event.stopPropagation(); deleteSchedule(${s.id})">
              <i data-lucide="trash-2" class="w-3 h-3"></i>
            </button>
          </div>
        </div>`;
      });
      html += `</div>`;
    }

    div.innerHTML = html;

    // Aesthetic & UX: Click on day to add schedule
    div.classList.add('cursor-pointer');
    div.onclick = () => openAddModal(dateStr);

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
    <div class="flex items-start gap-2 group">
      <div class="w-8 h-8 rounded-lg ${cat.bg} flex items-center justify-center ${cat.color} flex-shrink-0 mt-0.5">
        <i data-lucide="${cat.icon}" class="w-4 h-4"></i>
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-start justify-between gap-1 leading-tight">
          <div class="text-xs font-bold leading-tight text-surface-900 dark:text-surface-100 group-hover:text-brand-600 transition-colors break-words flex-1 ${s.status === 'done' ? 'line-through opacity-50' : ''}">
            ${s.status === 'done' ? '<i data-lucide="check-circle-2" class="w-3 h-3 inline-block mr-1 text-emerald-500"></i>' : ''}
            ${s.title}${s.is_public ? ' <span class="text-[8px] bg-emerald-500 text-white px-1.5 py-0.5 rounded-full uppercase">Shared</span>' : ''}
          </div>
          <div class="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0">
            <button class="p-1 text-surface-300 hover:text-emerald-500" title="Toggle Status" onclick="toggleScheduleStatus(${s.id})">
              <i data-lucide="${s.status === 'done' ? 'rotate-ccw' : 'check'}" class="w-3 h-3"></i>
            </button>
            <button class="p-1 text-surface-300 hover:text-brand-600" title="Edit" onclick="editSchedule(${s.id})">
              <i data-lucide="edit-3" class="w-3 h-3"></i>
            </button>
            <button class="p-1 text-surface-300 hover:text-red-500" title="Delete" onclick="deleteSchedule(${s.id})">
              <i data-lucide="trash-2" class="w-3 h-3"></i>
            </button>
          </div>
        </div>
        <div class="flex items-center gap-1.5 -mt-1.5">
          <span class="text-[9px] font-black text-brand-600 bg-brand-50 dark:bg-brand-900/30 px-1.5 py-0.5 rounded">${dateStr} · ${s.time || '09:00'}</span>
        </div>
        <div class="text-[10px] text-surface-400 mt-1 leading-tight line-clamp-1">${s.desc || 'ไม่มีรายละเอียด'}</div>
        <div class="flex items-center gap-1.5 mt-1 pt-1 border-t border-surface-100 dark:border-surface-800/60">
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
  setVisibilityTab('me');

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
      visStatus.textContent = 'สาธารณะ (ทุกคนเห็น)';
      visStatus.className = 'text-[10px] font-bold text-emerald-600 uppercase';
    } else {
      visStatus.textContent = 'ส่วนตัว (กำหนดเอง)';
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
let _currentVisTab = 'me';

function onSchedulePublicToggle(isPublic) {
  const visStatus = $('visibilityStatus');
  const visSection = $('scheduleVisibilitySection');
  if (isPublic) {
    if (visStatus) {
      visStatus.textContent = 'สาธารณะ (ทุกคนเห็น)';
      visStatus.className = 'text-[10px] font-bold text-emerald-600 uppercase';
    }
    if (visSection) visSection.classList.add('hidden');
    // Clear targeted visibility when setting to public
    if ($('scheduleTargetDepts')) $('scheduleTargetDepts').value = '';
    if ($('scheduleTargetUsers')) $('scheduleTargetUsers').value = '';
    _scheduleSelectedDepts.clear();
    _scheduleSelectedUsers.clear();
  } else {
    if (visStatus) {
      visStatus.textContent = 'ส่วนตัว (กำหนดเอง)';
      visStatus.className = 'text-[10px] font-bold text-brand-600 uppercase';
    }
    if (visSection) visSection.classList.remove('hidden');
    setVisibilityTab(_currentVisTab);
  }
}

function setVisibilityTab(tab) {
  _currentVisTab = tab;
  const tabs = { me: $('visTabOnlyMe'), dept: $('visTabDept'), users: $('visTabUsers') };
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
  if (tabs[tab]) {
    tabs[tab].classList.remove('text-surface-400');
    tabs[tab].classList.add('bg-white', 'dark:bg-surface-700', 'shadow-sm', 'text-brand-600', 'dark:text-brand-400');
  }

  // Show/hide panels and clear hidden input if switching away
  if (panels.dept) panels.dept.classList.toggle('hidden', tab !== 'dept');
  if (panels.users) panels.users.classList.toggle('hidden', tab !== 'users');

  // When switching to 'me' only, clear any targeted visibility
  if (tab === 'me') {
    _scheduleSelectedDepts.clear();
    _scheduleSelectedUsers.clear();
    if ($('scheduleTargetDepts')) $('scheduleTargetDepts').value = '';
    if ($('scheduleTargetUsers')) $('scheduleTargetUsers').value = '';
  }
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
  if (deptCount) {
    const n = _scheduleSelectedDepts.size;
    deptCount.textContent = n + ' แผนก';
    deptCount.classList.toggle('hidden', n === 0);
  }
  if (userCount) {
    const n = _scheduleSelectedUsers.size;
    userCount.textContent = n + ' คน';
    userCount.classList.toggle('hidden', n === 0);
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

closeScheduleModal.onclick = () => scheduleModal.classList.add('hidden');

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

async function initViz() {
  try {
    const data = await apiFetch('/api/files');
    const csvs = (data.files || []).filter(f => f.type === 'csv');
    vizFileSelect.innerHTML = '<option value="">-- เลือกไฟล์ CSV --</option>' +
      csvs.map(f => `<option value="${f.file_id}">${f.name}</option>`).join('');
  } catch (e) {
    console.error('Failed to init Viz:', e);
  }
}

vizFileSelect.onchange = async () => {
  const fileId = vizFileSelect.value;
  if (!fileId) {
    resetViz();
    return;
  }

  try {
    const res = await apiFetch(`/api/csv/${fileId}`);
    if (!res.ok) throw new Error(res.error);

    currentVizData = res.data;
    const headers = res.headers;

    vizXSelect.innerHTML = headers.map(h => `<option value="${h}">${h}</option>`).join('');
    vizYSelect.innerHTML = headers.map(h => `<option value="${h}">${h}</option>`).join('');

    // Try to auto-select numeric Y-axis
    if (res.data.length > 0) {
      const firstRow = res.data[0];
      const numericHeader = headers.find(h => !isNaN(parseFloat(firstRow[h])));
      if (numericHeader) vizYSelect.value = numericHeader;
    }

    renderChart();
  } catch (e) {
    toast('Error loading data: ' + e.message, 'error');
  }
};

vizXSelect.onchange = renderChart;
vizYSelect.onchange = renderChart;

vizTypeBtns.forEach(btn => {
  btn.onclick = () => {
    vizTypeBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderChart();
  };
});

function resetViz() {
  if (myChart) myChart.destroy();
  vizChartCanvas.classList.add('hidden');
  vizEmptyState.classList.remove('hidden');
  vizXSelect.innerHTML = '';
  vizYSelect.innerHTML = '';
}

function renderChart() {
  const xAttr = vizXSelect.value;
  const yAttr = vizYSelect.value;
  const typeBtn = Array.from(vizTypeBtns).find(b => b.classList.contains('active'));
  const type = typeBtn ? typeBtn.dataset.type : 'bar';

  if (!xAttr || !yAttr || !currentVizData.length) return;

  vizEmptyState.classList.add('hidden');
  vizChartCanvas.classList.remove('hidden');
  vizStatsRow.classList.remove('hidden');
  vizAiSummaryBox.classList.remove('hidden');

  // Stats Calculation
  const allYValues = currentVizData.map(d => parseFloat(d[yAttr])).filter(v => !isNaN(v));
  if (allYValues.length > 0) {
    const sum = allYValues.reduce((a, b) => a + b, 0);
    const avg = sum / allYValues.length;
    const max = Math.max(...allYValues);
    const min = Math.min(...allYValues);

    statsAvg.textContent = avg.toLocaleString(undefined, { maximumFractionDigits: 2 });
    statsMax.textContent = max.toLocaleString();
    statsMin.textContent = min.toLocaleString();
  } else {
    statsAvg.textContent = '-';
    statsMax.textContent = '-';
    statsMin.textContent = '-';
  }

  // Aesthetic Upgrade: Data Sampling
  // If data is too large, sample it to keep the chart readable (max 50 points)
  let sampledData = currentVizData;
  const MAX_POINTS = 50;
  if (currentVizData.length > MAX_POINTS) {
    const step = Math.ceil(currentVizData.length / MAX_POINTS);
    sampledData = currentVizData.filter((_, i) => i % step === 0);
  }

  const labels = sampledData.map(d => d[xAttr]);
  const values = sampledData.map(d => parseFloat(d[yAttr]) || 0);

  if (myChart) myChart.destroy();

  const isDark = document.documentElement.classList.contains('dark');
  const textColor = isDark ? '#94a3b8' : '#475569';
  const gridColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';

  // Premium Palette
  const chartColors = [
    '#6366f1', '#10b981', '#f43f5e', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899'
  ];

  const ctx = vizChartCanvas.getContext('2d');

  // Create Gradient
  const gradient = ctx.createLinearGradient(0, 0, 0, 400);
  gradient.addColorStop(0, isDark ? 'rgba(99, 102, 241, 0.4)' : 'rgba(99, 102, 241, 0.2)');
  gradient.addColorStop(1, 'rgba(99, 102, 241, 0)');

  myChart = new Chart(vizChartCanvas, {
    type: type,
    data: {
      labels: labels,
      datasets: [{
        label: yAttr,
        data: values,
        backgroundColor: type === 'pie' ? chartColors : (type === 'line' ? gradient : '#6366f1'),
        borderColor: '#6366f1',
        borderWidth: 2,
        tension: 0.4, // Cubic Interpolation (Smooth Lines)
        fill: type === 'line',
        pointBackgroundColor: '#6366f1',
        pointRadius: sampledData.length > 30 ? 0 : 3,
        borderRadius: type === 'bar' ? 8 : 0,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: {
          display: type === 'pie',
          position: 'bottom',
          labels: {
            color: textColor,
            padding: 20,
            font: { family: 'Inter', size: 11, weight: '600' }
          }
        },
        tooltip: {
          backgroundColor: isDark ? '#1e293b' : '#ffffff',
          titleColor: isDark ? '#f8fafc' : '#1e293b',
          bodyColor: isDark ? '#94a3b8' : '#475569',
          borderColor: isDark ? '#334155' : '#e2e8f0',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8,
          bodyFont: { family: 'Inter' },
          titleFont: { family: 'Inter', weight: 'bold' }
        }
      },
      scales: type !== 'pie' ? {
        x: {
          grid: { display: false },
          ticks: {
            color: textColor,
            maxRotation: 45,
            minRotation: 0,
            font: { family: 'Inter', size: 10, weight: '500' }
          }
        },
        y: {
          beginAtZero: true,
          grid: { color: gridColor },
          border: { dash: [4, 4] },
          ticks: {
            color: textColor,
            font: { family: 'Inter', size: 10, weight: '500' }
          }
        }
      } : {}
    }
  });
}

downloadChartBtn.onclick = () => {
  const link = document.createElement('a');
  link.download = `chart_${vizFileSelect.value || 'export'}.png`;
  link.href = vizChartCanvas.toDataURL('image/png');
  link.click();
};

generateAiSummaryBtn.onclick = async () => {
  const fileId = vizFileSelect.value;
  const xAttr = vizXSelect.value;
  const yAttr = vizYSelect.value;
  if (!fileId || !currentVizData.length) return;

  generateAiSummaryBtn.disabled = true;
  aiSummaryContent.innerHTML = '<div class="flex items-center gap-2"><div class="meta-typing"><span></span><span></span><span></span></div> กำลังวิเคราะห์ข้อมูลพยายามสรุปแนวโน้ม...</div>';

  try {
    const total = currentVizData.length;
    const sampleSize = 25;
    let sample = [];
    if (total <= sampleSize) {
      sample = currentVizData;
    } else {
      sample = currentVizData.slice(0, sampleSize);
    }

    const dataString = sample.map(d => `${d[xAttr]}: ${d[yAttr]}`).join(', ');
    const prompt = `ช่วยสรุปแนวโน้มของข้อมูลจากหัวข้อ "${xAttr}" และ "${yAttr}" นี้ให้หน่อย: ${dataString}. สรุปสั้นๆ ในเชิงธุรกิจหรือภาพรวมองค์กร (ภาษาไทย)`;

    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: prompt })
    });

    if (!response.ok) throw new Error('Network response was not ok');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let aiSummaryText = '';
    let buffer = '';

    aiSummaryContent.innerHTML = ''; // Clear typing

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      let lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        let trimmed = line.trim();
        if (!trimmed.startsWith('data: ')) continue;
        const jsonStr = trimmed.substring(6).trim();
        if (!jsonStr) continue;

        try {
          const data = JSON.parse(jsonStr);
          if (data.content) {
            aiSummaryText += data.content;
            aiSummaryContent.innerHTML = markdownToHtml(aiSummaryText);
            // Auto scroll container if needed
            aiSummaryContent.closest('.overflow-y-auto')?.scrollTo(0, 9999);
          }
        } catch (e) { console.error("Parse error in summary stream:", e); }
      }
    }
  } catch (e) {
    aiSummaryContent.innerHTML = `<span class="text-red-500">ไม่สามารถสร้างสรุปได้ในขณะนี้: ${e.message}</span>`;
  } finally {
    generateAiSummaryBtn.disabled = false;
  }
};

async function openTxtEditor(fileId) {
  try {
    currentEditingFileId = fileId;
    const res = await apiFetch(`/api/txt/${fileId}`);
    if (!res.ok) throw new Error(res.error);

    txtEditorContent.value = res.content;
    txtEditorModal.classList.remove('hidden');
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
      state.username = data.user; // Consolidate
      state.isAdmin = data.profile?.role === 'admin' || data.user === 'Admin';
      state.canEditKB = !!data.profile?.can_edit_kb;
      applyProfile(data.profile);
      loginOverlay.classList.add('hidden');
      return true;
    }
  } catch (e) {
    console.log('User not authed');
  }
  loginOverlay.classList.remove('hidden');
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

    if (data.ok) {
      state.user = data.user;
      state.username = typeof data.user === 'object' ? data.user.username : data.user;
      loginOverlay.classList.add('hidden');
      toast(`ยินดีต้อนรับคุณ ${data.user}`, 'success');

      // Notify backend that user is online
      if (socket) {
        socket.emit('user_online', {
          room: 'General',
          username: state.username
        });
      }

      // Re-init with auth context
      initAppContent();
      // Start all polling — same as init() when auto-logged in
      loadNotifications();
      setInterval(loadNotifications, 5000); // Every 5s

      loadChatList();
      loadUnreadCounts();
      setInterval(() => {
        loadUnreadCounts();
        if (state.groupChat.isOpen) {
          loadChatMessages(false);
        }
      }, 1000); // ⚡ Faster real-time polling: 1s

      setInterval(() => {
        const activeView = document.querySelector('.view:not(.hidden)');
        if (activeView && activeView.id === 'view-chat' && !state.sending) {
          loadHistory(true);
        }
      }, 4000);

      setInterval(pollTypingStatus, 2000);
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
      loginOverlay.classList.add('hidden');
      toast(`ยินดีต้อนรับคุณ ${state.username}`, 'success');

      if (socket) {
        socket.emit('user_online', {
          room: 'General',
          username: state.username
        });
      }

      initAppContent();
      loadNotifications();
      setInterval(loadNotifications, 5000);

      loadChatList();
      loadUnreadCounts();
      setInterval(() => {
        loadUnreadCounts();
        if (state.groupChat.isOpen) {
          loadChatMessages(false);
        }
      }, 1000);

      setInterval(() => {
        const activeView = document.querySelector('.view:not(.hidden)');
        if (activeView && activeView.id === 'view-chat' && !state.sending) {
          loadHistory(true);
        }
      }, 4000);

      setInterval(pollTypingStatus, 2000);
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

window.initGoogleSignIn = function () {
  const container = document.getElementById('googleSignInBtn');
  const separator = document.getElementById('googleSignInSeparator');
  // Use a fallback dummy client_id if not provided, just so the button displays 
  // (Note: login will fail until a real GOOGLE_CLIENT_ID is set in .env)
  const clientId = window.GOOGLE_CLIENT_ID || "dummy-client-id.apps.googleusercontent.com";

  if (!container || typeof google === 'undefined') return;

  google.accounts.id.initialize({
    client_id: clientId,
    callback: handleGoogleLogin
  });

  google.accounts.id.renderButton(
    container,
    { theme: 'outline', size: 'large', width: container.parentElement.offsetWidth || 300, shape: 'pill' }
  );

  if (separator) separator.style.display = 'flex';
};

// Check if google is already loaded (in case script async loaded before app.js)
if (typeof google !== 'undefined' && google.accounts && google.accounts.id) {
  window.initGoogleSignIn();
}

function showLoginError(msg) {
  loginErrorMsg.textContent = msg;
  loginError.classList.remove('hidden');
}

logoutBtn.onclick = async () => {
  try {
    const res = await fetch('/api/logout', { method: 'POST' });
    if (res.ok) {
      window.location.reload();
    }
  } catch (e) {
    toast('ออกจากระบบไม่สำเร็จ', 'error');
  }
};

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
                    preview: msg.text || '',
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
                    preview: msg.text || '',
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
  if (!chatRoomList || !chatContactList) return;

  // Render Rooms
  chatRoomList.innerHTML = state.chatList.rooms.map(room => {
    const isActive = state.currentChat.type === 'room' && state.currentChat.id == room.id;
    // Don't show badge for active room
    const unread = isActive ? 0 : (state.groupChat.unreadCounts.rooms[room.id] || 0);
    return `
      <div onclick="switchChat('room', '${room.id}', '${room.name}', '${room.avatar_url || ''}')" 
           class="chat-sidebar-item ${isActive ? 'active' : ''}">
        <div class="chat-item-avatar shadow-sm border border-surface-100 dark:border-surface-800">
          ${room.avatar_url ? `<img src="${room.avatar_url}" class="w-full h-full object-cover">` : `<i data-lucide="users" class="w-3.5 h-3.5 text-brand-600"></i>`}
        </div>
        <div class="chat-item-info">
          <div class="chat-item-name font-black">${room.name}</div>
        </div>
        ${unread > 0 ? `<div class="chat-item-badge animate-pulse bg-red-500">${unread}</div>` : ''}
      </div>
    `;
  }).join('');

  // Render Contacts (DMs)
  chatContactList.innerHTML = state.chatList.contacts.map(contact => {
    const isActive = state.currentChat.type === 'dm' && state.currentChat.id == contact.id;
    // Don't show badge for active DM
    const unread = isActive ? 0 : (state.groupChat.unreadCounts.dms[contact.id] || 0);
    return `
      <div onclick="switchChat('dm', '${contact.id}', '${contact.name}', '${contact.avatar_url || ''}')" 
           class="chat-sidebar-item ${isActive ? 'active' : ''}">
        <div class="chat-item-avatar shadow-sm border border-surface-100 dark:border-surface-800">
          ${contact.avatar_url ? `<img src="${contact.avatar_url}" class="w-full h-full object-cover">` : `<i data-lucide="user" class="w-3.5 h-3.5 text-brand-600"></i>`}
        </div>
        <div class="chat-item-info">
          <div class="chat-item-name font-black">${contact.name}</div>
        </div>
        ${unread > 0 ? `<div class="chat-item-badge animate-pulse bg-red-500">${unread}</div>` : ''}
      </div>
    `;
  }).join('');

  initIcons();
}

async function switchChat(type, id, name, avatarUrl) {
  state.currentChat = { type, id, name, avatarUrl };

  // Socket Join
  if (socket) {
    const socketRoom = type === 'room' ? `room_${id}` : `dm_${id}`;
    socket.emit('join', { room: socketRoom });
    // Also join self room for DMs
    if (type === 'dm') socket.emit('join', { room: `dm_${state.user}` });

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

  state.lastRendered.messages = ''; // Reset to force re-render
  groupChatMessages.innerHTML = `
    <div class="flex flex-col items-center justify-center py-20 animate-pulse">
      <div class="w-12 h-12 bg-surface-100 dark:bg-surface-800 rounded-2xl flex items-center justify-center mb-4">
        <i data-lucide="loader-2" class="w-6 h-6 text-brand-600 animate-spin"></i>
      </div>
      <div class="text-[10px] font-black uppercase tracking-widest opacity-50">กำลังโหลดข้อความ...</div>
    </div>
  `;

  chatHeaderName.textContent = name;
  chatInputArea.classList.remove('hidden');

  // Reverted mobile view logic: keep both sidebar and main area visible if layout permits
  // No longer adding 'chat-open' class

  // Update Avatar & Add Member Button
  if (type === 'room') {
    if (avatarUrl) {
      chatHeaderAvatar.innerHTML = `<img src="${avatarUrl}" class="w-full h-full object-cover">`;
    } else {
      chatHeaderAvatar.innerHTML = '<i data-lucide="users" class="w-5 h-5"></i>';
    }
    chatHeaderStatus.classList.remove('hidden');

    // Show viewMembersBtn for all users in a room
    $('viewMembersBtn')?.classList.remove('hidden');
    // Only owner or admin can edit/add members
    const room = state.chatList.rooms.find(r => r.id == id);
    const deleteGroupBtn = $('deleteGroupBtn');
    if (state.isAdmin || (room && room.owner === state.user)) {
      addMemberBtn.classList.remove('hidden');
      editGroupBtn.classList.remove('hidden');
    } else {
      addMemberBtn.classList.add('hidden');
      editGroupBtn.classList.add('hidden');
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
    if (avatarUrl) {
      chatHeaderAvatar.innerHTML = `<img src="${avatarUrl}" class="w-full h-full object-cover">`;
    } else {
      chatHeaderAvatar.innerHTML = '<i data-lucide="user" class="w-5 h-5"></i>';
    }
    chatHeaderStatus.classList.add('hidden');
    addMemberBtn.classList.add('hidden');
    editGroupBtn.classList.add('hidden');
    $('deleteGroupBtn')?.classList.add('hidden');
    $('viewMembersBtn')?.classList.add('hidden');

    // Show call buttons for DM
    if (voiceCallBtn) voiceCallBtn.classList.remove('hidden');
    if (videoCallBtn) videoCallBtn.classList.remove('hidden');
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
      renderChatMessages(shouldScroll);

      // ONLY delete unread count if we are NOT peeking
      if (!isPeek) {
        if (type === 'room') delete state.groupChat.unreadCounts.rooms[id];
        else delete state.groupChat.unreadCounts.dms[id];
        updateGlobalChatBadge();
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

  const isAtBottom = groupChatMessages.scrollHeight - groupChatMessages.scrollTop <= groupChatMessages.clientHeight + 100;
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
      ? 'bg-brand-600 text-white rounded-br-none ml-auto'
      : (isBot ? 'bg-surface-100 dark:bg-surface-800 border-l-4 border-brand-500 rounded-bl-none shadow-sm' : 'bg-surface-100 dark:bg-surface-800 rounded-bl-none shadow-sm');

    if (m.is_pinned && !isMe) bubbleClass += ' ring-1 ring-brand-500/30 bg-brand-50 dark:bg-brand-900/10';

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
          <div onclick="openLightbox('${img.url}')" class="chat-img-attachment cursor-pointer hover:scale-[1.02] transition-transform w-24 h-24 rounded-lg overflow-hidden border border-surface-100 dark:border-surface-800">
            <img src="${img.url}" class="w-full h-full object-cover">
          </div>
        `).join('')}
      </div>
    ` : '';

    const audioHtml = audioAttachments.length > 0 ? `
      <div class="chat-attachment-container ${isMe ? 'justify-end' : ''} mt-2 flex flex-col gap-2">
        ${audioAttachments.map(audio => `
          <div class="audio-player-bubble ${isMe ? 'bubble-me' : 'bubble-them'} !max-w-none">
            <div class="voice-play-btn" onclick="toggleVoicePlay(this, '${audio.url}')">
              <i data-lucide="play" class="w-3.5 h-3.5"></i>
            </div>
            <div class="voice-progress-container" onclick="seekVoice(event, this)">
              <div class="voice-progress-bar"></div>
            </div>
            <span class="voice-duration">0:00</span>
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
      <div class="flex items-start gap-2 relative chat-msg-row group ${isMe ? 'flex-row-reverse' : ''} ${isLast ? 'animate-in fade-in' : ''}">
        <div class="w-8 h-8 rounded-full overflow-hidden flex-shrink-0 bg-surface-200 dark:bg-surface-700 border border-surface-100 dark:border-surface-800 shadow-sm">
          ${m.avatar_url ? `<img src="${m.avatar_url}" class="w-full h-full object-cover">` : `<div class="w-full h-full flex items-center justify-center text-[10px] font-black">${m.username ? m.username[0].toUpperCase() : '?'}</div>`}
        </div>
        <div class="max-w-[85%] min-w-0 flex flex-col ${isMe ? 'items-end' : 'items-start'}">
          <div class="flex items-center gap-2 mb-1 ${isMe ? 'flex-row-reverse text-right' : ''}">
            <span class="text-[10px] font-black text-surface-500 truncate max-w-[120px]">${m.display_name || m.username}</span>
            <span class="text-[8px] text-surface-400 opacity-60 shrink-0">${new Date(m.timestamp).toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' })}</span>
            <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
              ${( (state.isAdmin || state.currentChat.type === 'dm') && m.id) ? `<button onclick="toggleRoomMessagePin(${m.id})" class="p-1 text-slate-300 hover:text-brand-600 transition-colors" title="ปักหมุด"><i data-lucide="pin" class="w-2.5 h-2.5 ${m.is_pinned ? 'fill-current text-brand-600' : ''}"></i></button>` : ''}
              ${(isMe && m.id) ? `<button onclick="editChatMessage('${state.currentChat.type}', ${m.id}, this.closest('#msg-container-${m.id}'))" class="p-1 text-slate-300 hover:text-blue-500 transition-colors" title="แก้ไข"><i data-lucide="edit-3" class="w-2.5 h-2.5"></i></button>` : ''}
              ${(isMe && m.id) ? `<button onclick="deleteChatMessage('${state.currentChat.type}', ${m.id}, this.closest('.chat-msg-row'))" class="p-1 text-slate-300 hover:text-red-500 transition-colors" title="ลบ"><i data-lucide="trash-2" class="w-2.5 h-2.5"></i></button>` : ''}
              ${(!isMe && !isBot && m.text) ? `<button onclick="extractActionItems(${JSON.stringify(m.text).replace(/"/g, '&quot;')}, ${m.id})" class="ai-extract-btn p-1 text-slate-300 hover:text-purple-600 transition-colors" title="สกัดงานด้วย AI"><i data-lucide="wand-2" class="w-2.5 h-2.5"></i></button>` : ''}
            </div>
          </div>
          <div class="chat-bubble-container" id="msg-container-${m.id}">
            ${(m.text || m.is_pinned) ? `
            <div class="p-2.5 text-xs rounded-2xl ${bubbleClass} shadow-sm break-words overflow-hidden min-w-0 w-fit max-w-full">
              ${m.is_pinned ? `<div class="flex items-center gap-1.5 text-[9px] font-black uppercase tracking-widest mb-1.5 opacity-70"><i data-lucide="pin" class="w-2 h-2 fill-current"></i> Pinned</div>` : ''}
              <div class="whitespace-pre-wrap">${highlightMentions(m.text || '')}${m.edited_at ? ' <span class="text-[8px] opacity-50 italic">(แก้ไขแล้ว)</span>' : ''}</div>
            </div>
            ` : ''}
            <div id="preview-${m.id}" class="link-preview-slot"></div>
          </div>
          ${imagesHtml}
          ${audioHtml}
          ${filesHtml}
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
      if (urlMatch) renderLinkPreview(urlMatch[0], m.id);
    }
  });

  // Scroll to bottom if forced (manual action) OR if user was already at bottom (intelligent follow)
  if (shouldScroll || isAtBottom) {
    groupChatMessages.scrollTop = groupChatMessages.scrollHeight;
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

function renderGroupMessages(shouldScroll = false) {
  if (!groupChatMessages) return;

  const html = state.groupChat.messages.map((m, idx) => {
    const isMe = String(m.username).toLowerCase() === String(state.user || '').toLowerCase();
    const isBot = m.username === 'AI-Assistant';
    const isLast = idx === state.groupChat.messages.length - 1;

    let bubbleClass = isMe ? 'bubble-me' : (isBot ? 'bubble-them bubble-bot' : 'bubble-them');

    // Separate Images, Audio, and other Files
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
          <div onclick="openLightbox('${img.url}')" class="chat-img-attachment cursor-pointer hover:scale-[1.02] transition-transform w-32 h-32 rounded-xl overflow-hidden border border-surface-100 dark:border-surface-800 shadow-sm">
            <img src="${img.url}" class="w-full h-full object-cover">
          </div>
        `).join('')}
      </div>
    ` : '';

    const audioHtml = audioAttachments.length > 0 ? `
      <div class="chat-attachment-container ${isMe ? 'justify-end' : ''} mt-2 flex flex-col gap-2">
        ${audioAttachments.map(audio => `
          <div class="audio-player-bubble ${bubbleClass} !max-w-none">
            <div class="voice-play-btn" onclick="toggleVoicePlay(this, '${audio.url}')">
              <i data-lucide="play" class="w-4 h-4"></i>
            </div>
            <div class="voice-progress-container" onclick="seekVoice(event, this)">
              <div class="voice-progress-bar"></div>
            </div>
            <span class="voice-duration">0:00</span>
            <audio src="${audio.url}" ontimeupdate="updateVoiceProgress(this)" onended="resetVoicePlayer(this)" class="hidden"></audio>
          </div>
        `).join('')}
      </div>
    ` : '';

    const filesHtml = fileAttachments.length > 0 ? `
      <div class="chat-attachment-container ${isMe ? 'justify-end' : ''} mt-2 flex flex-col gap-1.5">
        ${fileAttachments.map(file => `
          <a href="${file.url}" target="_blank" class="chat-file-attachment flex items-center gap-2 px-3 py-2 rounded-xl text-[11px] font-bold">
            <i data-lucide="file" class="w-3.5 h-3.5 text-brand-600"></i>
            <span class="truncate max-w-[120px]">${file.name}</span>
            <i data-lucide="download" class="w-3 h-3 ml-auto opacity-50"></i>
          </a>
        `).join('')}
      </div>
    ` : '';

    // Build header (avatar + name + time)
    const headerHtml = `
      <div class="flex items-center gap-2 mb-1.5 ${isMe ? 'flex-row-reverse' : 'flex-row'}">
        <div class="w-7 h-7 rounded-lg overflow-hidden flex-shrink-0 bg-surface-100 dark:bg-surface-800 border border-surface-200/50 dark:border-surface-700/50 shadow-sm">
          ${m.avatar_url ? `<img src="${m.avatar_url}" class="w-full h-full object-cover">` : `<div class="w-full h-full flex items-center justify-center text-[10px] font-black text-brand-600 bg-brand-600/10">${m.username[0].toUpperCase()}</div>`}
        </div>
        <div class="flex flex-col ${isMe ? 'items-end' : 'items-start'}">
          <span class="text-[9px] font-black uppercase tracking-widest text-surface-500 dark:text-surface-400">${m.display_name || m.username}</span>
          <span class="text-[8px] font-bold text-surface-400 opacity-60">${new Date(m.timestamp).toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
      </div>`;

    return `
      <div class="message-bubble-row group/chatmsg ${isLast ? 'animate-message' : ''}" style="display:flex; flex-direction:column; margin-bottom:16px;">
        ${headerHtml}
        <div style="display:flex; justify-content:${isMe ? 'flex-end' : 'flex-start'}; align-items: center; gap: 8px;">
          ${(isMe && m.id) ? `<button onclick="deleteChatMessage('${state.currentChat.type}', ${m.id}, this.closest('.message-bubble-row'))" class="p-1 opacity-0 group-hover/chatmsg:opacity-100 transition-opacity text-slate-300 hover:text-red-500" title="ลบข้อความ"><i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>` : ''}
          ${m.text ? `<div class="p-3 text-[13px] leading-relaxed ${bubbleClass} whitespace-pre-wrap break-words transition-all w-fit" style="width:fit-content; max-width:75%; overflow-wrap:break-word;">${highlightMentions(m.text || '')}</div>` : ''}
        </div>
        ${imagesHtml ? `<div style="display:flex; justify-content:${isMe ? 'flex-end' : 'flex-start'}; margin-top:6px;">${imagesHtml}</div>` : ''}
        ${audioHtml ? `<div style="display:flex; justify-content:${isMe ? 'flex-end' : 'flex-start'}; margin-top:6px;">${audioHtml}</div>` : ''}
        ${filesHtml ? `<div style="display:flex; justify-content:${isMe ? 'flex-end' : 'flex-start'}; margin-top:4px;">${filesHtml}</div>` : ''}
      </div>
    `;
  }).join('');

  groupChatMessages.innerHTML = html || '<div class="text-center py-10 text-surface-400 text-xs italic">ยังไม่มีข้อความ...</div>';
  initIcons();

  if (shouldScroll) {
    groupChatMessages.scrollTop = groupChatMessages.scrollHeight;
  }
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

function openLightbox(url) {
  const lightbox = $('imageLightbox');
  const img = $('lightboxImage');
  const downloadBtn = $('lightboxDownload');
  if (!lightbox || !img) return;

  img.src = url;
  downloadBtn.href = url;
  lightbox.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
  initIcons();
}

function closeLightbox() {
  const lightbox = $('imageLightbox');
  if (!lightbox) return;
  lightbox.classList.add('hidden');
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
    btn.textContent = 'สร้างกลุ่ม';
    initIcons();
  }
}

async function openAddMemberModal() {
  if (!state.currentChat || state.currentChat.type !== 'room') return;
  addMemberSelectList.innerHTML = '<div class="text-center py-4 opacity-50 text-xs">กำลังโหลดรายชื่อ...</div>';
  addMemberModal.classList.remove('hidden');

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
  startDmModal.classList.add('hidden');
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
  try {
    await loadStatus();
    await loadHistory();
    await loadFiles();
    await loadSchedules();
    await loadPersonas();
    console.log("✅ App Content Loaded.");
  } catch (e) {
    console.error("Content Load Failure:", e);
  }
}

// Profile Events ────────────────────────────
bgPresetBtns.forEach(btn => {
  btn.onclick = () => {
    const bg = btn.dataset.bg;
    if (bg === 'custom') {
      const color = prompt('ระบุรหัสสี:', '#2563eb');
      if (color) {
        document.body.style.background = color;
        if (profileCoverPreview) profileCoverPreview.style.background = color;
        state.tempBackground = color;
      }
    } else {
      document.body.style.background = bg;
      if (profileCoverPreview) profileCoverPreview.style.background = bg;
      state.tempBackground = bg;
      bgPresetBtns.forEach(b => b.classList.remove('border-brand-600'));
      btn.classList.add('border-brand-600');
    }
  };
});

// Mobile Chat Management
function openMobileChat() {
  if (!groupChatModal) return;
  state.groupChat.isOpen = !state.groupChat.isOpen;

  if (state.groupChat.isOpen) {
    groupChatModal.classList.remove('hidden');
    groupChatModal.classList.add('sidebar-show'); // Ensure sidebar is visible by default
    loadChatList();
    loadUnreadCounts();
    loadChatMessages(true);

    document.getElementById('mobileMessagesBtn')?.classList.add('active');

    setTimeout(() => {
      if (groupChatMessages) groupChatMessages.scrollTop = groupChatMessages.scrollHeight;
      initIcons();
    }, 100);
  } else {
    groupChatModal.classList.add('hidden');
    document.getElementById('mobileMessagesBtn')?.classList.remove('active');
  }
}

function closeMobileChat() {
  if (!groupChatModal) return;
  state.groupChat.isOpen = false;
  groupChatModal.classList.add('hidden');
  groupChatModal.classList.remove('chat-open');
  document.getElementById('mobileMessagesBtn')?.classList.remove('active');
}

function showMobileChatSidebar() {
  if (groupChatModal) groupChatModal.classList.remove('chat-open');
  loadChatList();
}

// Group Chat Handlers
if (groupChatHead) {
  groupChatHead.onclick = openMobileChat;
}

if (closeGroupChat) {
  closeGroupChat.onclick = () => {
    state.groupChat.isOpen = false;
    groupChatModal.classList.add('hidden');
  };
}

if (summonBotBtn) {
  summonBotBtn.onclick = () => {
    groupChatInput.value = '@bot ' + groupChatInput.value;
    groupChatInput.focus();
  };
}

if (attachFileBtn) {
  attachFileBtn.onclick = () => chatFileInput.click();
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
if (cancelCreateGroup) cancelCreateGroup.onclick = () => createGroupModal.classList.add('hidden');
if (openStartDmModal) openStartDmModal.onclick = openStartDm;
if (addMemberBtn) addMemberBtn.onclick = openAddMemberModal;
if (cancelAddMember) cancelAddMember.onclick = () => addMemberModal.classList.add('hidden');
if (confirmAddMember) confirmAddMember.onclick = handleAddMembers;
if (closeStartDmModal) closeStartDmModal.onclick = () => startDmModal.classList.add('hidden');
if (closeGroupChatMobile) closeGroupChatMobile.onclick = closeMobileChat;
if (editGroupBtn) editGroupBtn.onclick = openEditGroupModal;

async function deleteGroup() {
  const { type, id, name } = state.currentChat || {};
  if (type !== 'room' || !id) return;

  // Custom styled confirm
  const confirmed = confirm(`⚠️ คุณต้องการลบกลุ่ม "${name}" ใช่หรือไม่?\n\nข้อความทั้งหมดในกลุ่มจะถูกลบอย่างถาวร ไม่สามารถกู้คืนได้!`);
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
  $('roomMembersPanel')?.classList.add('hidden');
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
if (cancelEditGroup) cancelEditGroup.onclick = () => editGroupModal.classList.add('hidden');
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

    // Init @mention autocomplete for always-visible text inputs
    if (postInput) initMentionInput('postInput');  // Social feed: all users
    if (groupChatInput) initMentionInput('groupChatInput', fetchChatContextUsers);  // Chat: room members only

    // Notification Polling (Increased frequency to 5s for real-time feel)
    loadNotifications();
    setInterval(loadNotifications, 5000);

    // Unified Chat Initial Load & Polling (Increased frequency to 3s)
    loadChatList();
    loadUnreadCounts();
    setInterval(() => {
      loadUnreadCounts();
      if (state.groupChat.isOpen) {
        // Poll messages only if open. 
        // Use PEEK if modal is hidden (e.g. mobile bottom nav switched away)
        const isModalHidden = groupChatModal && groupChatModal.classList.contains('hidden');
        loadChatMessages(false, isModalHidden);
      }
    }, 3000);

    // Main Chat Polling (Background update every 4s)
    setInterval(() => {
      const activeView = document.querySelector('.view:not(.hidden)');
      if (activeView && activeView.id === 'view-chat' && !state.sending) {
        loadHistory(true);
      }
    }, 4000);

    // Typing Status Polling (Every 2s)
    setInterval(pollTypingStatus, 2000);

    // Listen for main chat typing
    if (msgInput) {
      msgInput.addEventListener('input', () => {
        sendTypingSignal('ai-assistant', 'dm');
      });
    }
  }

  // Real-time Clock (always runs if element exists)
  if (realtimeClock) {
    setInterval(() => {
      const now = new Date();
      realtimeClock.textContent = now.toLocaleTimeString('th-TH', { hour12: false });
    }, 1000);
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
    return `
      <div id="notif-item-${n.id}" class="p-4 bg-white dark:bg-surface-900 border ${n.is_read ? 'border-surface-100 dark:border-surface-800 opacity-60' : 'border-brand-100 dark:border-brand-900/30 bg-brand-50/10'} rounded-2xl flex gap-4 transition-all hover:shadow-md group">
        <div class="w-10 h-10 rounded-xl ${n.is_read ? 'bg-surface-100 dark:bg-surface-800 text-surface-400' : 'bg-brand-600 text-white'} flex items-center justify-center flex-shrink-0 cursor-pointer" onclick="handleNotifClick(${n.id}, '${n.link || ''}')">
          <i data-lucide="${icon}" class="w-5 h-5"></i>
        </div>
        <div class="flex-1 min-w-0 cursor-pointer" onclick="handleNotifClick(${n.id}, '${n.link || ''}')">
          <div class="flex justify-between items-start mb-1">
            <h4 class="text-sm font-bold ${n.is_read ? '' : 'text-brand-600'}">${n.title}</h4>
            <span class="text-[10px] text-surface-400 font-bold uppercase">${timeAgo}</span>
          </div>
          <p class="text-xs text-surface-500 line-clamp-2">${n.message}</p>
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
      const view = link.replace("#", "").split("-")[0];
      showView(view);
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
    panel.style.cssText = 'position:fixed;bottom:80px;right:16px;z-index:9999;width:420px;max-width:calc(100vw - 32px);max-height:80vh;display:none;flex-direction:column;box-shadow:0 25px 60px rgba(0,0,0,0.35);border-radius:16px;overflow:hidden;border:1px solid rgba(0,0,0,0.1);';
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
  modal.style.display = 'flex';
  adminChatSetTab('ai');
  initIcons();
}

function closeAdminChatPanel() {
  const modal = document.getElementById('adminChatModal');
  if (!modal) return;
  modal.style.display = 'none';
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
  const data = await (await fetch('/api/admin/chat/ai')).json();
  adminChatState.messages = data.messages || [];
  adminRenderMessages(adminChatState.messages, 'ai');
}

async function adminChatLoadRooms() {
  const el = document.getElementById('adminChatContent');
  el.innerHTML = '<div class="text-xs text-surface-400 animate-pulse">กำลังโหลด...</div>';
  const data = await (await fetch('/api/admin/chat/overview')).json();
  const rooms = data.rooms || [];
  el.innerHTML = `
    <div class="flex flex-wrap gap-2 mb-2">
      ${rooms.map(r => `<button onclick="adminChatLoadRoom(${r.id},'${r.name.replace(/'/g, "\\\'")}')" class="px-3 py-1.5 text-xs font-bold bg-surface-100 dark:bg-surface-800 hover:bg-brand-50 dark:hover:bg-brand-900/30 hover:text-brand-600 rounded-lg border border-surface-200 dark:border-surface-700 transition-colors">${r.name}</button>`).join('')}
    </div>
    <div id="adminRoomMsgs" class="text-xs text-surface-400 italic">เลือกห้องแชทด้านบน</div>
  `;
}

async function adminChatLoadRoom(roomId, roomName) {
  adminChatState.selectedRoom = { id: roomId, name: roomName };
  adminChatState.tab = 'room';
  const data = await (await fetch(`/api/admin/chat/room/${roomId}`)).json();
  adminChatState.messages = data.messages || [];
  const el = document.getElementById('adminRoomMsgs');
  if (el) {
    el.innerHTML = '';
    renderAdminMsgList(el, adminChatState.messages, 'room');
  }
  updateAdminMsgCount();
}

async function adminChatLoadDmPairs() {
  const el = document.getElementById('adminChatContent');
  el.innerHTML = '<div class="text-xs text-surface-400 animate-pulse">กำลังโหลด...</div>';
  const data = await (await fetch('/api/admin/chat/overview')).json();
  const pairs = data.dm_pairs || [];
  if (!pairs.length) {
    el.innerHTML = '<div class="text-xs text-surface-400 italic text-center py-8">ไม่มีข้อความ DM</div>';
    return;
  }
  el.innerHTML = `
    <div class="flex flex-col gap-1 mb-2">
      ${pairs.map(p => `<button onclick="adminChatLoadDm('${p.user1}','${p.user2}')" class="flex items-center justify-between px-3 py-2 text-xs font-bold bg-surface-100 dark:bg-surface-800 hover:bg-brand-50 dark:hover:bg-brand-900/30 hover:text-brand-600 rounded-lg border border-surface-200 dark:border-surface-700 transition-colors text-left">
        <span>${p.user1} ↔ ${p.user2}</span>
        <span class="text-surface-400">${p.count} ข้อความ</span>
      </button>`).join('')}
    </div>
    <div id="adminDmMsgs" class="text-xs text-surface-400 italic">เลือกคู่แชทด้านบน</div>
  `;
}

async function adminChatLoadDm(u1, u2) {
  adminChatState.selectedDm = { user1: u1, user2: u2 };
  const data = await (await fetch(`/api/admin/chat/dm?user1=${u1}&user2=${u2}`)).json();
  adminChatState.messages = data.messages || [];
  const el = document.getElementById('adminDmMsgs');
  if (el) {
    el.innerHTML = '';
    renderAdminMsgList(el, adminChatState.messages, 'dm');
  }
  updateAdminMsgCount();
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
  try {
    const d = await (await fetch('/api/me')).json();
    if (d.ok) {
      state.isAdmin = d.profile?.role === 'admin' || d.user === 'Admin';
      state.canEditKB = !!d.profile?.can_edit_kb;
      if (state.isAdmin) initAdminChatPanel();
    }
  } catch (e) { }
});
// Also call on every checkAuth success
const _origCheckAuthFn = window.checkAuth;
if (typeof checkAuth === 'function') {
  const __origCA = checkAuth;
  window.checkAuth = async function () {
    const ok = await __origCA();
    if (ok) {
      try {
        const d = await (await fetch('/api/me')).json();
        if (d.ok) {
          state.isAdmin = d.profile?.role === 'admin' || d.user === 'Admin';
          state.canEditKB = !!d.profile?.can_edit_kb;
          if (state.isAdmin) initAdminChatPanel();
        }
      } catch { }
    }
    return ok;
  };
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
        <div style="width:40px;height:40px;border-radius:12px;background:rgba(124,58,237,.1);color:#7c3aed;display:flex;align-items:center;justify-content:center;overflow:hidden;flex-shrink:0;">
          ${avatarContent}
        </div>
        <div style="flex:1;min-width:0;">
          <div style="display:flex;align-items:center;flex-wrap:wrap;gap:6px;margin-bottom:2px;">
            <div style="font-weight:700;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:180px;" class="dark:text-white">${user.display_name || user.username.charAt(0).toUpperCase() + user.username.slice(1)}</div>
            <div class="admin-status-dot" style="background:${activeColor};" title="${user.is_active ? 'ใช้งานปกติ' : 'ถูกระงับ'}"></div>
          </div>
          <div style="display:flex;align-items:center;flex-wrap:wrap;gap:6px;">
            <div style="font-size:11px;color:#94a3b8;font-family:monospace;">@${user.username}</div>
            <span class="admin-role-badge ${roleClass}">${user.role}</span>
            ${user.department ? `<span class="text-[9px] bg-blue-100/50 text-blue-700 dark:text-blue-400 px-1 py-0.5 rounded font-bold">${user.department.toUpperCase()}</span>` : ''}
            ${user.can_edit_kb ? `<span class="text-[9px] bg-emerald-100/50 text-emerald-700 dark:text-emerald-400 px-1 py-0.5 rounded font-bold">KB EDIT</span>` : ''}
          </div>
        </div>
        <div class="flex gap-2">
          <button onclick="openEditUserModal('${user.username}')" style="padding:8px 14px;border-radius:10px;font-size:12px;font-weight:700;border:1px solid #e2e8f0;background:transparent;cursor:pointer;color:#475569;" class="dark:border-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-800 transition-colors">
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
  if ($('editUserDept')) $('editUserDept').value = user.department || '';
  $('editUserNotes').value = user.notes || '';
  $('editUserNewPassword').value = '';

  // Protect admin self-lockout visually
  if (username === 'Admin') {
    $('editUserActive').disabled = true;
    $('editUserRole').disabled = true;
  } else {
    $('editUserActive').disabled = false;
    $('editUserRole').disabled = false;
  }

  $('editUserModal').classList.remove('hidden');
  $('editUserModal').style.display = 'flex';
}

function closeEditUserModal() {
  currentEditingUsername = null;
  $('editUserModal').classList.add('hidden');
  $('editUserModal').style.display = 'none';
}

async function submitEditUser() {
  if (!currentEditingUsername) return;

  const payload = {
    display_name: $('editDisplayName').value.trim(),
    role: $('editUserRole').value,
    is_active: $('editUserActive').checked,
    can_view_kb: $('editUserCanViewKB').checked,
    can_edit_kb: $('editUserCanEditKB').checked,
    can_delete_kb: $('editUserCanDeleteKB').checked,
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
  $('createUserModal').style.display = 'flex';
}

function closeCreateUserModal() {
  $('createUserModal').classList.add('hidden');
  $('createUserModal').style.display = 'none';
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
  const fontFamily = "'Inter', 'Sarabun', sans-serif";

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
    const data = await res.json();
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
function speak(text) {
  if (!('speechSynthesis' in window)) {
    toast('เบราว์เซอร์ไม่รองรับเสียงอ่าน', 'error');
    return;
  }
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  const isThai = /[\u0E00-\u0E7F]/.test(text);
  const v = window.speechSynthesis.getVoices().find(v => v.lang.includes(isThai ? 'th' : 'en'));
  if (v) utter.voice = v;
  utter.rate = 1.0;
  window.speechSynthesis.speak(utter);
  toast('กำลังอ่านข้อความ...', 'info');
}

// 📄 AI Smart Scan (OCR/Summarize)
async function scanFileWithAI(fileId) {
  toast('กำลังสแกนไฟล์ด้วย AI...', 'info');

  try {
    const res = await apiFetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: `ช่วยสรุปเนื้อหาและดึงข้อมูลสำคัญจากไฟล์ ID: ${fileId} ออกมาที สรุปเป็นหัวข้อสั้นๆ เข้าใจง่าย`,
        history: []
      })
    });

    if (res.ok) {
      showView('chat');
      appendMessage('bot', `## 🔍 ผลการสแกนไฟล์\n\n${res.reply || 'ไม่สามารถดึงข้อมูลมาสรุปได้'}`);
    } else {
      throw new Error('Scan failed');
    }
  } catch (e) {
    console.error(e);
    toast('สแกนไฟล์ไม่สำเร็จ', 'error');
  }
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

  document.documentElement.classList.toggle('dark', isDark);
  
  // Sync all theme elements (icons & text)
  document.querySelectorAll('.themeIcon').forEach(el => {
    el.setAttribute('data-lucide', isDark ? 'sun' : 'moon');
  });
  document.querySelectorAll('.themeText').forEach(el => {
    el.innerText = isDark ? 'โหมดกลางวัน' : 'โหมดกลางคืน';
  });

  // Backward compatibility for old IDs
  const oldIcon = $('themeIcon');
  const oldText = $('themeText');
  if (oldIcon) oldIcon.setAttribute('data-lucide', isDark ? 'sun' : 'moon');
  if (oldText) oldText.innerText = isDark ? 'โหมดกลางวัน' : 'โหมดกลางคืน';

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
        <a href="${data.url}" target="_blank" class="mt-2 block bg-surface-50 dark:bg-surface-800 rounded-xl overflow-hidden border border-surface-100 dark:border-surface-700 hover:border-brand-600 transition-all max-w-sm">
          ${data.image ? `<img src="${data.image}" class="w-full h-32 object-cover" onerror="this.style.display='none'">` : ''}
          <div class="p-3">
            <h4 class="text-xs font-bold truncate">${data.title}</h4>
            <p class="text-[10px] text-surface-500 mt-1 line-clamp-2">${data.description || ""}</p>
          </div>
        </a>
      `;
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
  if (state.currentChat.type === 'dm') {
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
};

async function loadKanbanBoard() {
  try {
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
  addColBtn.className = 'kanban-add-col flex-shrink-0 w-72';
  addColBtn.innerHTML = `
    <button onclick="openAddColumnModal()" class="w-full h-14 border-2 border-dashed border-surface-200 dark:border-surface-700 hover:border-brand-500 hover:bg-brand-50/40 dark:hover:bg-brand-900/20 text-surface-400 hover:text-brand-600 rounded-2xl flex items-center justify-center gap-2 font-bold text-sm transition-all">
      <i data-lucide="plus" class="w-4 h-4"></i> เพิ่มคอลัมน์ใหม่
    </button>
  `;
  board.appendChild(addColBtn);

  initIcons();
  updateDashboardKanbanCount();
}

function buildKanbanColumn(col) {
  const div = document.createElement('div');
  div.className = 'kanban-col flex-shrink-0 w-72 flex flex-col bg-surface-50 dark:bg-surface-900 rounded-2xl border border-surface-200 dark:border-surface-800 shadow-sm overflow-hidden';
  div.dataset.colId = col.id;

  const cardCount = col.cards ? col.cards.length : 0;
  div.innerHTML = `
    <div class="kanban-col-header flex items-center justify-between px-4 py-3 border-b border-surface-200 dark:border-surface-800" style="border-top: 3px solid ${col.color || '#6366f1'}">
      <div class="flex items-center gap-2 min-w-0">
        <span class="font-black text-sm truncate">${escHtml(col.title)}</span>
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
    <div class="kanban-cards-list flex-1 overflow-y-auto p-3 space-y-2.5 min-h-[100px] custom-scrollbar" 
         data-col-id="${col.id}"
         ondragover="handleCardDragOver(event)"
         ondragleave="event.currentTarget.classList.remove('drag-over')"
         ondrop="handleCardDrop(event, ${col.id})">
      ${(col.cards || []).map(card => buildKanbanCardHTML(card)).join('')}
    </div>
    <div class="p-3 border-t border-surface-100 dark:border-surface-800">
      <button onclick="openAddCardModal(${col.id})" class="w-full py-2.5 border-2 border-dashed border-surface-200 dark:border-surface-700 hover:border-brand-500 hover:bg-brand-50/40 dark:hover:bg-brand-900/20 text-surface-400 hover:text-brand-600 rounded-xl flex items-center justify-center gap-1.5 font-bold text-xs transition-all">
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
  const priorityLabel = { high: '🔴 สูง', medium: '🟡 กลาง', low: '🟢 ต่ำ' };
  const pColor = priorityColors[card.priority] || priorityColors.medium;
  const pLabel = priorityLabel[card.priority] || '🟡 กลาง';

  const dueHtml = card.due_date ? `
    <div class="flex items-center gap-1 text-[9px] font-bold text-surface-400 mt-1">
      <i data-lucide="calendar" class="w-2.5 h-2.5"></i> ${card.due_date}
    </div>` : '';

  const assigneeHtml = card.assignee ? `
    <div class="flex items-center gap-1 text-[9px] font-bold text-surface-500 mt-1">
      <i data-lucide="user" class="w-2.5 h-2.5"></i> ${escHtml(card.assignee)}
    </div>` : '';

  const borderStyle = card.color ? `border-l: 3px solid ${card.color};` : '';

  const labelsHtml = card.labels ? card.labels.split(',').map(l => `
    <span class="px-2 py-0.5 rounded flex items-center gap-1 text-[9px] font-black uppercase tracking-widest text-indigo-700 bg-indigo-100 dark:text-indigo-300 dark:bg-indigo-900/40 border border-indigo-200 dark:border-indigo-800/50">
      <i data-lucide="tag" class="w-2 h-2"></i> ${escHtml(l.trim())}
    </span>
  `).join('') : '';

  return `
    <div class="kanban-card bg-white dark:bg-surface-800 rounded-xl border border-surface-200 dark:border-surface-700 p-3 shadow-sm hover:shadow-md cursor-grab active:cursor-grabbing transition-all hover:-translate-y-0.5 group"
         draggable="true" data-card-id="${card.id}" data-col-id="${card.column_id}"
         ondragstart="handleCardDragStart(event, ${card.id}, ${card.column_id})"
         ondragend="handleCardDragEnd(event)"
         style="${borderStyle}">
      ${labelsHtml ? `<div class="flex flex-wrap gap-1 mb-2">${labelsHtml}</div>` : ''}
      <div class="flex items-start justify-between gap-2">
        <p class="font-bold text-xs text-surface-800 dark:text-surface-100 leading-snug flex-1">${escHtml(card.title)}</p>
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

// Drag and Drop
function handleCardDragStart(event, cardId, colId) {
  kanbanState.dragCard = cardId;
  kanbanState.dragSourceCol = colId;
  event.dataTransfer.effectAllowed = 'move';
  event.target.style.opacity = '0.5';
}

function handleCardDragEnd(event) {
  event.target.style.opacity = '';
  document.querySelectorAll('.drag-over').forEach(el => {
    el.classList.remove('drag-over', 'drag-over-top', 'drag-over-bottom');
  });
}

function handleCardDragOver(event) {
  event.preventDefault();
  const target = event.target.closest('.kanban-card');
  const col = event.target.closest('.kanban-cards-list');

  // Remove previous drop indicators
  document.querySelectorAll('.drag-over-top, .drag-over-bottom').forEach(el => {
    el.classList.remove('drag-over-top', 'drag-over-bottom');
  });

  if (target && target.dataset.cardId !== kanbanState.dragCard) {
    const rect = target.getBoundingClientRect();
    const midpoint = rect.top + rect.height / 2;
    if (event.clientY < midpoint) {
      target.classList.add('drag-over-top');
    } else {
      target.classList.add('drag-over-bottom');
    }
  } else if (col) {
    col.classList.add('drag-over');
  }
}

async function handleCardDrop(event, targetColId) {
  event.preventDefault();
  document.querySelectorAll('.drag-over, .drag-over-top, .drag-over-bottom').forEach(el => {
    el.classList.remove('drag-over', 'drag-over-top', 'drag-over-bottom');
  });

  if (!kanbanState.dragCard) return;

  const cardId = kanbanState.dragCard;
  kanbanState.dragCard = null;

  const targetCard = event.target.closest('.kanban-card');
  let newPos = 0;

  if (targetCard) {
    targetColId = targetCard.dataset.colId;
    const col = kanbanState.columns.find(c => c.id == targetColId);
    if (!col || !col.cards) return;

    const targetIdx = col.cards.findIndex(c => c.id == targetCard.dataset.cardId);
    const rect = targetCard.getBoundingClientRect();
    const midpoint = rect.top + rect.height / 2;

    // If dropped on top half, place before. If bottom half, place after
    if (event.clientY < midpoint) {
      newPos = targetIdx;
    } else {
      newPos = targetIdx + 1;
    }

    // Adjust if moving within same column moving downwards
    if (kanbanState.dragSourceCol == targetColId) {
      const oldIdx = col.cards.findIndex(c => c.id == cardId);
      if (oldIdx < newPos) newPos -= 1;
    }
  } else {
    const col = kanbanState.columns.find(c => c.id == targetColId);
    newPos = col && col.cards ? col.cards.length : 0;
  }

  try {
    await apiFetch(`/api/kanban/cards/${cardId}/move`, {
      method: 'POST',
      body: JSON.stringify({ column_id: targetColId, position: newPos }),
    });
    await loadKanbanBoard();
  } catch (e) {
    toast('ย้ายการ์ดไม่สำเร็จ', 'error');
  }
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
  showKanbanCardModal();
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
  showKanbanCardModal(card);
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
        <h3 class="text-base font-black">${isEdit ? '✏️ แก้ไขการ์ด' : '➕ เพิ่มการ์ดใหม่'}</h3>
        <button onclick="closeKanbanCardModal()" class="p-2 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-xl"><i data-lucide="x" class="w-4 h-4"></i></button>
      </div>
      <div class="space-y-3">
        <div>
          <label class="block text-[10px] font-black uppercase tracking-widest text-surface-400 mb-1">หัวข้อ *</label>
          <input id="kCardTitle" type="text" value="${card ? escHtml(card.title) : ''}" placeholder="ชื่องาน..." class="w-full bg-surface-50 dark:bg-surface-800 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-brand-600 outline-none">
        </div>
        <div>
          <label class="block text-[10px] font-black uppercase tracking-widest text-surface-400 mb-1">รายละเอียด</label>
          <textarea id="kCardDesc" rows="3" placeholder="รายละเอียดเพิ่มเติม..." class="w-full bg-surface-50 dark:bg-surface-800 rounded-xl px-4 py-2.5 text-sm resize-none focus:ring-2 focus:ring-brand-600 outline-none">${card ? escHtml(card.description || '') : ''}</textarea>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-[10px] font-black uppercase tracking-widest text-surface-400 mb-1">ความสำคัญ</label>
            <select id="kCardPriority" class="w-full bg-surface-50 dark:bg-surface-800 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-brand-600 outline-none">
              <option value="low" ${card?.priority === 'low' ? 'selected' : ''}>🟢 ต่ำ</option>
              <option value="medium" ${(!card || card?.priority === 'medium') ? 'selected' : ''}>🟡 กลาง</option>
              <option value="high" ${card?.priority === 'high' ? 'selected' : ''}>🔴 สูง</option>
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
          <label class="block text-[10px] font-black uppercase tracking-widest text-surface-400 mb-1">ผู้รับผิดชอบ</label>
          <input id="kCardAssignee" type="text" value="${card ? escHtml(card.assignee || '') : ''}" placeholder="ชื่อผู้รับผิดชอบ..." class="w-full bg-surface-50 dark:bg-surface-800 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-brand-600 outline-none">
        </div>
      </div>
      <div class="flex gap-3 pt-2">
        <button onclick="closeKanbanCardModal()" class="flex-1 py-3 bg-surface-100 dark:bg-surface-800 hover:bg-surface-200 rounded-2xl font-bold text-sm transition-all">ยกเลิก</button>
        <button onclick="submitKanbanCard()" class="flex-[2] py-3 bg-brand-600 hover:bg-brand-700 text-white rounded-2xl font-bold text-sm shadow-lg transition-all">
          ${isEdit ? '💾 บันทึก' : '➕ เพิ่มการ์ด'}
        </button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  initIcons();
  setTimeout(() => $('kCardTitle')?.focus(), 100);
}

function closeKanbanCardModal() {
  $('kanbanCardModal')?.remove();
}

async function submitKanbanCard() {
  const title = $('kCardTitle')?.value?.trim();
  if (!title) { toast('กรุณาใส่หัวข้อการ์ด', 'error'); return; }

  const payload = {
    title,
    description: $('kCardDesc')?.value || '',
    priority: $('kCardPriority')?.value || 'medium',
    due_date: $('kCardDue')?.value || '',
    assignee: $('kCardAssignee')?.value || '',
    labels: $('kCardLabels')?.value || '',
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
function formatRelativeTime(isoStr) {
  if (!isoStr) return '';
  try {
    const d = new Date(isoStr);
    const diff = (Date.now() - d.getTime()) / 1000;
    if (diff < 60) return 'เมื่อกี้';
    if (diff < 3600) return `${Math.floor(diff / 60)} นาทีที่แล้ว`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} ชั่วโมงที่แล้ว`;
    if (diff < 86400 * 7) return `${Math.floor(diff / 86400)} วันที่แล้ว`;
    return d.toLocaleDateString('th-TH');
  } catch { return isoStr; }
}

// Helper to escape HTML
function escHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// ─── Kanban/Wiki loaded via switchView above ─────────────────────────────
// loadKanbanBoard() and loadWikiPages()/renderWikiContent() are defined in the Kanban & Wiki modules below.

// ─── NOTIFICATIONS MODULE ──────────────────────────────────────────────────
async function loadNotifications() {
  const container = $('notificationsContainer');
  if (!container) return;

  try {
    const res = await apiFetch('/api/notifications');

    const countBadge = $('navNotifBadge');
    if (res.unread_count > 0) {
      if (countBadge) {
        countBadge.innerText = res.unread_count > 99 ? '99+' : res.unread_count;
        countBadge.classList.remove('hidden');
      }
    } else {
      if (countBadge) countBadge.classList.add('hidden');
    }

    if (!res.notifications || res.notifications.length === 0) {
      container.innerHTML = `
        <div class="flex flex-col items-center justify-center min-h-[400px] w-full text-center animate-in fade-in zoom-in duration-500">
          <div class="relative mb-6">
            <div class="absolute inset-0 bg-brand-500/10 dark:bg-brand-500/5 blur-xl rounded-full animate-pulse"></div>
            <div class="w-24 h-24 bg-gradient-to-br from-surface-100 to-surface-50 dark:from-surface-800 dark:to-surface-900 rounded-3xl flex items-center justify-center text-surface-300 dark:text-surface-600 shadow-inner relative border border-white/50 dark:border-surface-700/50">
              <i data-lucide="bell" class="w-10 h-10"></i>
            </div>
          </div>
          <h3 class="text-lg font-black text-surface-900 dark:text-white mb-2 tracking-tight">คุณตามทันแล้ว!</h3>
          <p class="text-[13px] font-medium text-surface-500 dark:text-surface-400 max-w-xs leading-relaxed">ขณะนี้ยังไม่มีการแจ้งเตือนใหม่<br>เมื่อมีเรื่องสำคัญ ระบบจะแจ้งให้ทราบที่นี่ครับ</p>
        </div>
      `;
      initIcons();
      return;
    }

    const htmlStr = res.notifications.map(n => {
      const typeIcons = {
        'kanban': '<div class="w-10 h-10 rounded-2xl bg-gradient-to-br from-indigo-100 to-blue-50 dark:from-indigo-900/40 dark:to-blue-900/20 flex items-center justify-center flex-shrink-0 border border-indigo-200/50 dark:border-indigo-800/50 shadow-sm"><i data-lucide="layout-dashboard" class="w-5 h-5 text-indigo-600 dark:text-indigo-400"></i></div>',
        'wiki': '<div class="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-100 to-sky-50 dark:from-blue-900/40 dark:to-sky-900/20 flex items-center justify-center flex-shrink-0 border border-blue-200/50 dark:border-blue-800/50 shadow-sm"><i data-lucide="book-open" class="w-5 h-5 text-blue-600 dark:text-blue-400"></i></div>',
        'mention': '<div class="w-10 h-10 rounded-2xl bg-gradient-to-br from-orange-100 to-amber-50 dark:from-orange-900/40 dark:to-amber-900/20 flex items-center justify-center flex-shrink-0 border border-orange-200/50 dark:border-orange-800/50 shadow-sm"><i data-lucide="at-sign" class="w-5 h-5 text-orange-600 dark:text-orange-400"></i></div>',
        'system': '<div class="w-10 h-10 rounded-2xl bg-gradient-to-br from-brand-100 to-emerald-50 dark:from-brand-900/40 dark:to-emerald-900/20 flex items-center justify-center flex-shrink-0 border border-brand-200/50 dark:border-brand-800/50 shadow-sm"><i data-lucide="info" class="w-5 h-5 text-brand-600 dark:text-brand-400"></i></div>',
      };
      const iconHtml = typeIcons[n.type] || typeIcons.system;
      const readClass = n.is_read ? 'opacity-70 bg-transparent border-transparent' : 'bg-white dark:bg-surface-800/80 border-surface-200/70 dark:border-surface-700/70 shadow-lg shadow-surface-200/20 dark:shadow-none';
      const titleBold = n.is_read ? 'font-semibold text-surface-600 dark:text-surface-300' : 'font-black text-surface-900 dark:text-white';

      return `
        <div class="flex items-start gap-4 p-4 rounded-3xl border transition-all hover:bg-surface-100 dark:hover:bg-surface-800/80 ${readClass} relative overflow-hidden group cursor-pointer" onclick="handleNotificationClick(${n.id}, '${n.link || ''}', ${n.is_read})">
          ${!n.is_read ? '<div class="absolute top-0 bottom-0 left-0 w-[5px] bg-orange-500"></div>' : ''}
          ${iconHtml}
          <div class="flex-1 min-w-0 pr-4">
            <h4 class="text-sm ${titleBold} text-surface-900 dark:text-white leading-snug">${escHtml(n.title)}</h4>
            <p class="text-xs text-surface-500 mt-1.5 line-clamp-2">${escHtml(n.message)}</p>
            <span class="text-[10px] uppercase font-black tracking-widest text-surface-400 mt-2 block">${formatRelativeTime(n.timestamp)}</span>
          </div>
          ${!n.is_read ? `<button onclick="event.stopPropagation(); markNotificationRead(${n.id})" class="p-2 -mr-2 text-surface-300 hover:text-brand-600 hover:bg-brand-50 rounded-full" title="รับทราบ"><i data-lucide="check" class="w-4 h-4"></i></button>` : ''}
        </div>
      `;
    }).join('');

    container.innerHTML = htmlStr;
    initIcons();
  } catch (err) {
    console.error('Error load notifications:', err);
    container.innerHTML = '<p class="text-red-500 text-sm text-center py-4 font-bold">ไม่สามารถดึงข้อมูลการแจ้งเตือนได้</p>';
  }
}

async function handleNotificationClick(id, link, isRead) {
  if (!isRead) await markNotificationRead(id, false);
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
    if (reload) loadNotifications();
  } catch (e) {
    console.error(e);
  }
}

async function readAllNotifications() {
  try {
    await apiFetch('/api/notifications/read_all', { method: 'POST' });
    loadNotifications();
  } catch (e) {
    console.error(e);
  }
}

async function clearAllNotifications() {
  if (!confirm("คุณแน่ใจหรือไม่ว่าต้องการลบการแจ้งเตือนทั้งหมด?")) return;
  try {
    await apiFetch('/api/notifications/delete_all', { method: 'DELETE' });
    loadNotifications();
  } catch (e) {
    console.error(e);
  }
}

// 🎙️ VOICE MESSAGE & AUDIO PLAYER LOGIC
let mediaRecorder;
let audioChunks = [];
let recordingInterval;
let recordingStartTime;

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
  const bar = container.querySelector('.voice-progress-bar');
  const durationText = container.querySelector('.voice-duration');

  if (!audio.duration) return;
  const percent = (audio.currentTime / audio.duration) * 100;
  bar.style.width = `${percent}%`;

  const mins = Math.floor(audio.currentTime / 60);
  const secs = Math.floor(audio.currentTime % 60);
  durationText.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
};

window.resetVoicePlayer = function (audio) {
  const container = audio.closest('.audio-player-bubble');
  const bar = container.querySelector('.voice-progress-bar');
  const btnIcon = container.querySelector('.voice-play-btn svg') || container.querySelector('.voice-play-btn i');
  bar.style.width = '0%';
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

// RECORDING LOGIC
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
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      const file = new File([audioBlob], `voice_${Date.now()}.webm`, { type: 'audio/webm' });

      // Add to pending files
      state.groupChat.pendingFiles.push(file);
      renderChatAttachmentPreview();

      // Check if we should auto-send (UX choice)
      // toast('อัดเสียงเสร็จแล้ว กดส่งได้ทันที!', 'info');
    };

    mediaRecorder.start();
    recordingStartTime = Date.now();

    // UI Updates
    const recUI = document.getElementById('recordingUI');
    const inputMain = document.getElementById('groupChatInput');
    if (recUI) recUI.classList.remove('hidden');
    if (inputMain) inputMain.classList.add('hidden');

    recordingInterval = setInterval(updateRecordingTimer, 100);
    // toast('กำลังบันทึกเสียง...', 'info');
  } catch (err) {
    console.error('Recording error:', err);
    toast('ไม่สามารถเข้าถึงไมโครโฟนได้', 'error');
  }
}

function stopVoiceRecording() {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(track => track.stop());
  }
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
  // Voice recording button
  const vBtn = e.target.closest('#voiceBtn');
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

const rtcState = {
  pc: null,                // RTCPeerConnection
  localStream: null,       // MediaStream (local)
  remoteStream: null,      // MediaStream (remote)
  callType: 'audio',       // 'audio' | 'video'
  isCaller: false,
  remoteUser: null,        // username of the other party
  isMicMuted: false,
  isCamOff: false,
  isSpeakerMuted: false,
  callTimer: null,
  callStartTime: null,
  ringtoneCtx: null,
  ringtoneNodes: [],
  pendingOffer: null,      // store offer before acceptCall
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
        sender: state.user, // Added explicit sender
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
      toast('✅ เชื่อมต่อสำเร็จ!', 'success');
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
      toast('❌ กรุณาอนุญาตการเข้าถึงไมโครโฟน/กล้องในเบราว์เซอร์', 'error');
    } else if (err.name === 'NotFoundError') {
      toast('❌ ไม่พบไมโครโฟนหรือกล้องในอุปกรณ์นี้', 'error');
    } else {
      toast(`❌ ไม่สามารถเข้าถึงสื่อได้: ${err.message}`, 'error');
    }
    throw err;
  }
}

// ─── Initiate Call (Caller side) ─────────────────────────────
async function initiateCall(withVideo = false) {
  if (!state.currentChat || state.currentChat.type !== 'dm') {
    console.warn('⚠️ Not in a DM chat, currentChat:', state.currentChat);
    toast('📞 สามารถโทรได้เฉพาะกับ Direct Message เท่านั้น', 'error');
    return;
  }
  if (rtcState.pc) {
    toast('⚠️ กำลังมีสายโทรอยู่แล้ว', 'error');
    return;
  }

  const targetUser = state.currentChat.name;
  console.log('🎯 Target user identified:', targetUser);
  
  if (!targetUser || targetUser === state.user) {
    toast('❌ ไม่พบผู้รับสาย หรือไม่สามารถโทรหาตัวเองได้', 'error');
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
      sender: state.user,
      type: 'offer',
      payload: offer,
      callType: rtcState.callType
    });

    toast(`📞 กำลังโทรหา ${targetUser}...`, 'info');
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
    toast('❌ ไม่พบข้อมูลสาย', 'error');
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
      sender: state.user,
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
    toast('❌ ไม่สามารถรับสายได้: ' + err.message, 'error');
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
      sender: state.user,
      type: 'reject',
      payload: null
    });
  }
  cleanupCall();
  toast('📵 ปฏิเสธสายแล้ว', 'info');
}

// ─── End Call ─────────────────────────────────────────────────
function endCall() {
  if (rtcState.remoteUser && socket) {
    socket.emit('webrtc_signal', {
      target: rtcState.remoteUser,
      sender: state.user,
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
  toast(rtcState.isMicMuted ? '🔇 ปิดไมโครโฟน' : '🎙️ เปิดไมโครโฟน', 'info');
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
  toast(rtcState.isCamOff ? '📵 ปิดกล้อง' : '📷 เปิดกล้อง', 'info');
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
  toast(rtcState.isSpeakerMuted ? '🔇 ปิดลำโพง' : '🔊 เปิดลำโพง', 'info');
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
      toast('🖥️ หยุดแชร์หน้าจอแล้ว', 'info');
    };
    toast('🖥️ กำลังแชร์หน้าจอ', 'success');
  } catch (e) {
    if (e.name !== 'AbortError' && e.name !== 'NotAllowedError') {
      toast('❌ ไม่สามารถแชร์หน้าจอได้', 'error');
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
            target: sender, sender: state.user, type: 'busy', payload: null
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
window.initiateCall = initiateCall;
window.acceptCall   = acceptCall;
window.rejectCall   = rejectCall;
window.endCall      = endCall;
window.toggleMic    = toggleMic;
window.toggleCam    = toggleCam;
window.toggleSpeaker = toggleSpeaker;
window.shareScreen  = shareScreen;

// ─── Initialize WebRTC after socket is ready ─────────────────
// Wait until socket and user are available
(function waitForSocket() {
  if (socket) {
    initWebRTCSignaling();
  } else {
    // Socket loaded via CDN might be delayed
    setTimeout(() => {
      if (typeof io !== 'undefined' && !socket) {
        socket = io();
      }
      initWebRTCSignaling();
    }, 2000);
  }
})();

