// --- OrgChat AI: KB Module ---

// File Preview Refs
const filePreviewModal = $('filePreviewModal');

const previewFileName = $('previewFileName');

// Helper: Check if can edit KB
function canEditKB() {
  if (state.isAdmin) return true;
  return !!state.canEditKB;
}

const navItems = document.querySelectorAll('.nav-item');

const uploadZone = $('uploadZone');

const fileInput = $('fileInput');

const uploadProgress = $('uploadProgress');

const fileList = $('fileList');

const refreshFilesBtn = $('refreshFilesBtn');

const statFiles = $('statFiles');

const navSettings = document.getElementById("nav-settings");

const navStats = document.getElementById("nav-stats");

const navNotifications = document.getElementById("nav-notifications");

const navNotifBadge = document.getElementById("navNotifBadge");

const editingFileName = $('editingFileName');

let currentEditingFileId = null;

const groupAvatarUpload = $('groupAvatarUpload');

// Visualization Refs
const vizFileSelect = $('vizFileSelect');

const vizTypeBtns = document.querySelectorAll('.viz-type-btn');

const scheduleCatInput = $('scheduleCategory');

const postCategory = $('postCategory');

const feedFilters = document.querySelectorAll('.feed-filter-chip');

const postFileInput = $('postFileInput');

let postFiles = [];

const editPostCategory = $('editPostCategory');

const selectAllFilesBtn = $('selectAllFiles');

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

const attachFileBtn = $('attachFileBtn');

const accentColorBtns = document.querySelectorAll('.accent-color-btn');

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

async function initDocumentGenerator() {
  try {
    const data = await apiFetch('/api/org/profile');
    if (data.ok && data.profile) {
      const p = data.profile;
      
      // Autofill seller info
      if (p.business_name_th) {
        if ($('sellerName')) $('sellerName').value = p.business_name_th;
      }
      
      // Combine address
      let addr = p.address_line1 || '';
      if (p.address_line2) addr += ' ' + p.address_line2;
      if (p.district) addr += ' ' + p.district;
      if (p.province) addr += ' ' + p.province;
      if (p.zipcode) addr += ' ' + p.zipcode;
      if ($('sellerAddress')) $('sellerAddress').value = addr.trim();
      
      if (p.tax_id) {
        if ($('sellerTaxId')) $('sellerTaxId').value = p.tax_id;
      }
      if (p.phone) {
        if ($('sellerPhone')) $('sellerPhone').value = p.phone;
      }
      
      // Load Logo preview
      const prevLogo = $('prevLogoImg');
      if (prevLogo) {
        if (p.logo_url) {
          prevLogo.src = p.logo_url;
          prevLogo.classList.remove('hidden');
        } else {
          prevLogo.src = '';
          prevLogo.classList.add('hidden');
        }
      }
      
      // Load Signature preview
      const prevSig = $('prevSignatureImg');
      if (prevSig) {
        if (p.signature_url) {
          prevSig.src = p.signature_url;
          prevSig.classList.remove('hidden');
        } else {
          prevSig.src = '';
          prevSig.classList.add('hidden');
        }
      }
      
      updateQuotationPreview();
    }
  } catch (err) {
    console.error('Error pre-filling quotation seller details from org profile:', err);
  }
}

function resetOrgLogoUI() {
  const placeholder = $('org_logo_placeholder');
  const preview = $('org_logo_preview');
  const deleteBtn = $('btn_delete_logo');
  const hiddenInput = $('biz_logo_url');
  
  if (hiddenInput) hiddenInput.value = '';
  if (preview) {
    preview.src = '';
    preview.classList.add('hidden');
  }
  if (placeholder) {
    placeholder.classList.remove('hidden');
    placeholder.innerHTML = `<i data-lucide="upload-cloud" class="w-5 h-5"></i><span class="text-[10px] font-bold">อัปโหลดโลโก้</span>`;
  }
  if (deleteBtn) deleteBtn.classList.add('hidden');
  if (window.lucide) window.lucide.createIcons();
}

function resetOrgSigUI() {
  const placeholder = $('org_sig_placeholder');
  const preview = $('org_sig_preview');
  const deleteBtn = $('btn_delete_sig');
  const hiddenInput = $('biz_signature_url');
  
  if (hiddenInput) hiddenInput.value = '';
  if (preview) {
    preview.src = '';
    preview.classList.add('hidden');
  }
  if (placeholder) {
    placeholder.classList.remove('hidden');
    placeholder.innerHTML = `<i data-lucide="file-signature" class="w-5 h-5"></i><span class="text-[10px] font-bold">อัปโหลดลายเซ็น</span>`;
  }
  if (deleteBtn) deleteBtn.classList.add('hidden');
  if (window.lucide) window.lucide.createIcons();
}

function toggleMoreNav() {
  const section = document.getElementById('moreNavSection');
  const icon = document.getElementById('moreNavIcon');
  if (!section) return;
  const isNowHidden = section.classList.toggle('hidden');
  if (icon) icon.style.transform = isNowHidden ? '' : 'rotate(180deg)';
  try { localStorage.setItem('moreNavOpen', isNowHidden ? '0' : '1'); } catch(e) {}
}

// Restore เพิ่มเติม state จาก localStorage
document.addEventListener('DOMContentLoaded', () => {
  try {
    if (localStorage.getItem('moreNavOpen') === '1') {
      const section = document.getElementById('moreNavSection');
      const icon = document.getElementById('moreNavIcon');
      if (section) section.classList.remove('hidden');
      if (icon) icon.style.transform = 'rotate(180deg)';
    }
  } catch(e) {}
});

function applyProfile(profile) {
  if (!profile) return;

  // Update Plan Badges & Org Info
  const plan = profile.active_plan || 'free';
  const planName = profile.plan_name || 'Free Plan';
  const orgName = profile.org_name || 'Default Organization';

  // Desktop badge
  const sidebarPlanBadge = $('sidebarPlanBadge');
  if (sidebarPlanBadge) {
    sidebarPlanBadge.textContent = planName;
    sidebarPlanBadge.className = 'px-1.5 py-0.5 rounded text-[8px] font-extrabold uppercase tracking-wider block mt-1 w-max';
    if (plan === 'free') {
      sidebarPlanBadge.classList.add('bg-surface-100', 'text-surface-600', 'dark:bg-surface-800', 'dark:text-surface-400');
    } else if (plan === 'pro') {
      sidebarPlanBadge.classList.add('bg-emerald-50', 'text-emerald-600', 'dark:bg-emerald-950/40', 'dark:text-emerald-400', 'border', 'border-emerald-200/50', 'dark:border-emerald-800/30');
    } else if (plan === 'business') {
      sidebarPlanBadge.classList.add('bg-indigo-50', 'text-indigo-600', 'dark:bg-indigo-950/40', 'dark:text-indigo-400', 'border', 'border-indigo-200/50', 'dark:border-indigo-800/30');
    }
    sidebarPlanBadge.classList.remove('hidden');
  }

  // Mobile badge
  const mobilePlanBadge = $('mobilePlanBadge');
  if (mobilePlanBadge) {
    mobilePlanBadge.textContent = planName;
    mobilePlanBadge.className = 'px-1.5 py-0.5 rounded text-[8px] font-extrabold uppercase tracking-wider';
    if (plan === 'free') {
      mobilePlanBadge.classList.add('bg-surface-100', 'text-surface-600', 'dark:bg-surface-800', 'dark:text-surface-400');
    } else if (plan === 'pro') {
      mobilePlanBadge.classList.add('bg-emerald-50', 'text-emerald-600', 'dark:bg-emerald-950/40', 'dark:text-emerald-400');
    } else {
      mobilePlanBadge.classList.add('bg-indigo-50', 'text-indigo-600', 'dark:bg-indigo-950/40', 'dark:text-indigo-400');
    }
    mobilePlanBadge.classList.remove('hidden');
  }

  // Pro-lock indicators on nav items for free users
  if (plan === 'free') {
    const proNavIds = ['nav-drive', 'nav-viz'];
    proNavIds.forEach(navId => {
      const btn = $(navId);
      if (!btn || btn.querySelector('.pro-lock-tag')) return;
      const tag = document.createElement('span');
      tag.className = 'pro-lock-tag ml-auto px-1 py-0.5 rounded text-[8px] font-black uppercase bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 flex-shrink-0';
      tag.textContent = 'Pro';
      btn.appendChild(tag);
    });
  } else {
    document.querySelectorAll('.pro-lock-tag').forEach(el => el.remove());
  }

  // Profile View Inputs
  if ($('profileOrgDisplay')) $('profileOrgDisplay').value = orgName;
  const profilePlanBadge = $('profilePlanBadge');
  if (profilePlanBadge) {
    profilePlanBadge.textContent = planName;
    profilePlanBadge.className = 'px-2.5 py-1 rounded-lg text-xs font-black uppercase tracking-wider';
    if (plan === 'free') {
      profilePlanBadge.classList.add('bg-surface-100', 'text-surface-600', 'dark:bg-surface-800', 'dark:text-surface-400');
    } else if (plan === 'pro') {
      profilePlanBadge.classList.add('bg-emerald-100', 'text-emerald-700', 'dark:bg-emerald-900/30', 'dark:text-emerald-400');
    } else {
      profilePlanBadge.classList.add('bg-indigo-100', 'text-indigo-700', 'dark:bg-indigo-900/30', 'dark:text-indigo-400');
    }
  }

  // Update Sidebar
  if (sidebarDisplayName) sidebarDisplayName.textContent = profile.display_name || profile.username;
  const sidebarUserRoleEl = $('sidebarUserRole');
  if (sidebarUserRoleEl) {
    sidebarUserRoleEl.textContent = profile.org_role === 'admin' ? 'Admin' : 'Member';
  }
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
}

async function loadProfile() {
  try {
    const data = await apiFetch('/api/profile');
    if (data.ok && data.profile) {
      applyProfile(data.profile);
    }
  } catch (e) {
    console.error('Failed to load profile:', e);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if ($('saveProfileBtn')) {
    $('saveProfileBtn').addEventListener('click', async () => {
      try {
        $('saveProfileBtn').disabled = true;
        $('saveProfileBtn').innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> กำลังบันทึก...`;
        initIcons();

        const formData = new FormData();
        formData.append('display_name', $('profileNameInput').value || '');
        formData.append('department', $('profileDeptInput') ? $('profileDeptInput').value || '' : 'General');
        
        const fileInput = $('avatarUploadInput');
        if (fileInput && fileInput.files[0]) {
          formData.append('avatar', fileInput.files[0]);
        }

        const res = await fetch('/api/profile/update', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        if (data.ok) {
          toast('บันทึกโปรไฟล์เรียบร้อย', 'success');
          applyProfile(data.profile);
        } else {
          toast('เกิดข้อผิดพลาด: ' + (data.error || 'Unknown'), 'error');
        }
      } catch (e) {
        toast('การบันทึกล้มเหลว', 'error');
      } finally {
        $('saveProfileBtn').disabled = false;
        $('saveProfileBtn').innerHTML = `<i data-lucide="save" class="w-4 h-4"></i> บันทึกข้อมูลทั้งหมด`;
        initIcons();
      }
    });
  }

  if ($('avatarUploadInput')) {
    $('avatarUploadInput').addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
         const reader = new FileReader();
         reader.onload = (ev) => {
           if ($('profileAvatarPreview')) $('profileAvatarPreview').innerHTML = `<img src="${ev.target.result}" class="w-full h-full object-cover">`;
         };
         reader.readAsDataURL(e.target.files[0]);
      }
    });
  }
});

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

  const refreshDriveBtn = $('refreshDriveBtn');
  if (refreshDriveBtn) {
    refreshDriveBtn.onclick = () => loadDriveContents(state.drive.currentFolderId);
  }
});

document.addEventListener('touchstart', e => {
  touchStartX = e.changedTouches[0].screenX;
}, false);

document.addEventListener('touchend', e => {
  touchEndX = e.changedTouches[0].screenX;
  handleGesture();
}, false);

document.addEventListener('DOMContentLoaded', () => {
  // AI Productivity Listeners
  if (aiGenKanbanBtn) aiGenKanbanBtn.onclick = () => {
    aiGenKanbanModal.classList.remove('hidden');
    aiGenKanbanModal.classList.add('flex', 'items-center', 'justify-center');
  };
  if (closeAiGenModal) closeAiGenModal.onclick = () => {
    aiGenKanbanModal.classList.add('hidden');
    aiGenKanbanModal.classList.remove('flex', 'items-center', 'justify-center');
  };
  if (confirmAiGenBtn) confirmAiGenBtn.onclick = handleAiGenKanban;

  if (bulkCompareBtn) bulkCompareBtn.onclick = handleBulkCompare;
  if (closeAiCompareModal) closeAiCompareModal.onclick = () => {
    aiCompareModal.classList.add('hidden');
    aiCompareModal.classList.remove('flex', 'items-center', 'justify-center');
  };

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
  const query = $('kbSearchInput').value.trim();
  const searchTerms = query.toLowerCase().split(/\s+/).filter(t => t.length > 1);

  const highlightText = (text, terms) => {
    if (!terms.length) return text;
    let out = text;
    terms.forEach(term => {
      const regex = new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      out = out.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-900/50 text-surface-900 dark:text-yellow-100 rounded-sm px-0.5">$1</mark>');
    });
    return out;
  };

  if (!results.length) {
    fileList.innerHTML = `
      <div class="col-span-full py-20 text-center text-surface-400">
        <i data-lucide="search-x" class="w-12 h-12 mx-auto mb-4 opacity-10"></i>
        <p>ไม่พบเนื้อหาที่เกี่ยวข้องกับ "${query}"</p>
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
          <div class="font-bold text-xs truncate uppercase tracking-tight">${highlightText(r.file_name || r.source, searchTerms)}</div>
          <div class="text-[9px] text-surface-400 font-bold uppercase">${r.location || 'Document'} • SCORE: ${(r.score * 100).toFixed(0)}%</div>
        </div>
      </div>
      <div class="text-[13px] text-surface-600 dark:text-surface-300 leading-relaxed bg-surface-50 dark:bg-surface-800/50 p-3 rounded-xl border border-surface-100 dark:border-surface-700 italic">
        "...${highlightText(r.text, searchTerms)}..."
      </div>
    </div>
  `).join('');
  initIcons();
}

// ─── Global KB Drag & Drop ─────────────────────
// Allow dropping files anywhere in the KB view to upload
const viewKB = $('view-kb');

if (viewKB) {
  // Ensure overlay exists
  let kbDragOverlay = document.getElementById('kbDragOverlay');
  if (!kbDragOverlay) {
    kbDragOverlay = document.createElement('div');
    kbDragOverlay.id = 'kbDragOverlay';
    kbDragOverlay.className = 'hidden fixed inset-4 z-[9999] border-2 border-dashed border-brand-500/60 rounded-3xl flex items-start justify-center pt-8 pointer-events-none transition-all duration-300';
    kbDragOverlay.innerHTML = `
      <div class="bg-white/95 dark:bg-surface-900/95 backdrop-blur-md px-6 py-3.5 rounded-full shadow-2xl flex items-center gap-3 border border-brand-500/30 text-brand-600 animate-in slide-in-from-top-4 duration-200">
        <div class="w-8 h-8 rounded-full bg-brand-50 dark:bg-brand-950/50 flex items-center justify-center text-brand-600 shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" /></svg>
        </div>
        <p class="text-xs font-bold text-surface-800 dark:text-surface-100 whitespace-nowrap">วางไฟล์เพื่อเริ่มอัปโหลดเข้าคลังความรู้</p>
      </div>
    `;
    viewKB.appendChild(kbDragOverlay);
  }

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    viewKB.addEventListener(eventName, e => {
      e.preventDefault();
      e.stopPropagation();
    }, false);
  });

  let dragCounter = 0;

  viewKB.addEventListener('dragenter', () => {
    dragCounter++;
    kbDragOverlay.classList.remove('hidden');
    const uploadZone = $('uploadZone');
    if (uploadZone) uploadZone.classList.add('border-brand-600', 'bg-brand-50/50', 'scale-[1.01]');
  }, false);

  viewKB.addEventListener('dragleave', () => {
    dragCounter--;
    if (dragCounter <= 0) {
      dragCounter = 0;
      kbDragOverlay.classList.add('hidden');
      const uploadZone = $('uploadZone');
      if (uploadZone) uploadZone.classList.remove('border-brand-600', 'bg-brand-50/50', 'scale-[1.01]');
    }
  }, false);

  viewKB.addEventListener('drop', e => {
    dragCounter = 0;
    kbDragOverlay.classList.add('hidden');
    const uploadZone = $('uploadZone');
    if (uploadZone) uploadZone.classList.remove('border-brand-600', 'bg-brand-50/50', 'scale-[1.01]');
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) handleFiles(files);
  }, false);
}

function _warnWrongDocType(files, catName) {
  const name = (catName || '').toLowerCase();
  const hasImage = files.some(f => _IMG_EXTS.has(f.name.split('.').pop().toLowerCase()));
  const hasDoc   = files.some(f => _DOC_EXTS.has(f.name.split('.').pop().toLowerCase()));
  const isFinancialCat = _FINANCIAL_CAT_KEYWORDS.some(k => name.includes(k));

  // รูปภาพเข้าหมวดการเงิน → อาจเป็นสลิป ควรบันทึกรายจ่ายแทน
  if (hasImage && isFinancialCat) {
    return 'ไฟล์รูปภาพในหมวดการเงินอาจเป็นสลิปหรือใบเสร็จ — ต้องการบันทึกรายจ่ายผ่านระบบรายจ่ายแทนไหม? (กด OK เพื่อไปหน้ารายจ่าย หรือ Cancel เพื่ออัปโหลด KB ต่อ)';
  }
  // เอกสารเข้าหมวดรูปภาพ/media
  const isMediaCat = ['รูป','media','ภาพ','photo','image'].some(k => name.includes(k));
  if (hasDoc && isMediaCat) {
    return 'กำลังอัปโหลดเอกสารเข้าหมวดสื่อ/ภาพ ถูกต้องไหม?';
  }
  return null;
}

// ─── Optimistic upload ghost cards ───────────────────────────
const _IMG_PREVIEW_EXTS = new Set(['png','jpg','jpeg','webp','bmp']);

function _injectGhostCards(files) {
  // ลบ empty-state placeholder ก่อน (ถ้ามี)
  fileList.querySelector('.col-span-full')?.remove();

  const ghosts = [];
  [...files].reverse().forEach(f => {
    const ext = f.name.split('.').pop().toLowerCase();
    const icon = FILE_LUCIDE[ext] || 'file';
    const id = `ghost-${Date.now()}-${Math.random().toString(36).substr(2,6)}`;
    const isImg = _IMG_PREVIEW_EXTS.has(ext);
    const thumbUrl = isImg ? URL.createObjectURL(f) : null;
    if (thumbUrl) _ghostObjectURLs.push(thumbUrl);

    const el = document.createElement('div');
    el.id = id;
    el.className = 'group relative bg-white dark:bg-surface-900 border-2 border-brand-400/60 dark:border-brand-600/60 rounded-3xl p-5 flex flex-col gap-4 animate-in slide-in-from-top-2 duration-300 shadow-lg shadow-brand-500/10';
    el.innerHTML = `
      <div class="absolute top-4 right-4 flex items-center gap-1.5">
        <span class="flex h-2 w-2 relative">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-brand-500"></span>
        </span>
        <span class="ghost-status text-[9px] font-black text-brand-500 uppercase tracking-tighter">รอส่ง...</span>
      </div>

      <div class="flex items-start gap-4">
        <div class="w-12 h-12 rounded-2xl overflow-hidden bg-brand-50 dark:bg-brand-900/20 border border-brand-100 dark:border-brand-800 flex items-center justify-center flex-shrink-0">
          ${thumbUrl
            ? `<img src="${thumbUrl}" class="w-full h-full object-cover">`
            : `<i data-lucide="${icon}" class="w-6 h-6 text-brand-400"></i>`}
        </div>
        <div class="min-w-0 flex-1 pt-0.5">
          <h4 class="font-black text-sm text-surface-900 dark:text-white truncate tracking-tight mb-1" title="${f.name}">${f.name}</h4>
          <span class="text-[9px] font-bold text-brand-400">${formatSize(f.size)}</span>
        </div>
      </div>

      <div class="space-y-1">
        <div class="w-full bg-surface-100 dark:bg-surface-800 rounded-full h-1 overflow-hidden">
          <div class="ghost-bar h-full bg-gradient-to-r from-brand-400 to-brand-600 rounded-full transition-all duration-200" style="width:0%"></div>
        </div>
        <p class="ghost-pct text-[10px] text-center font-bold text-brand-400">0%</p>
      </div>`;

    fileList.insertBefore(el, fileList.firstChild);
    ghosts.push({ id, el });
  });

  initIcons();
  return ghosts;
}

// XHR upload ที่ได้ progress จริงเป็น bytes (ไม่ใช่ fake %)
function _xhrUpload(form, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/upload');
    xhr.upload.onprogress = e => {
      if (e.lengthComputable) onProgress(Math.round(e.loaded / e.total * 85));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try { resolve(JSON.parse(xhr.responseText)); }
        catch { reject(new Error('Invalid JSON')); }
      } else {
        reject(new Error(`HTTP ${xhr.status}`));
      }
    };
    xhr.onerror = () => reject(new Error('Network error'));
    // ส่ง CSRF/session cookie อัตโนมัติ (same-origin XHR)
    xhr.withCredentials = true;
    if (window._csrfToken) {
      xhr.setRequestHeader('X-CSRF-Token', window._csrfToken);
    }
    xhr.send(form);
  });
}

async function handleFiles(files) {
  if (!files.length) return;
  const allowed = ['pdf', 'csv', 'txt', 'md', 'png', 'jpg', 'jpeg', 'bmp', 'webp', 'docx', 'xlsx'];
  const valid = files.filter(f => allowed.includes(f.name.split('.').pop().toLowerCase()));
  if (!valid.length) { toast('รูปแบบไฟล์ไม่ถูกต้อง (รองรับ PDF, Excel, Word, Text, รูปภาพ)', 'error'); return; }

  const MAX_SIZE = 50 * 1024 * 1024;
  const oversize = valid.filter(f => f.size > MAX_SIZE);
  if (oversize.length > 0) {
    toast(`ไฟล์ขนาดใหญ่เกิน 50MB: ${oversize.map(f => f.name).join(', ')}`, 'error');
    return;
  }

  const activeCatBtn = document.querySelector('#kbCategorySidebar .kb-cat-item.active');
  const activeCatName = activeCatBtn?.textContent?.trim() || '';
  const typeWarning = _warnWrongDocType(valid, activeCatName);
  if (typeWarning) {
    const goExpense = window.confirm(typeWarning);
    if (goExpense) { showView('dashboard'); return; }
  }

  showGlobalLoading('กำลังอัปโหลดไฟล์เข้าคลังความรู้...');

  // ── Instant feedback: inject ghost cards ทันที ─────────────
  const ghosts = _injectGhostCards(valid);
  uploadProgress.classList.remove('hidden');
  updateProgress(0, 'กำลังส่งไฟล์...');

  const form = new FormData();
  valid.forEach(f => form.append('files', f));
  if (deptSelect) form.append('department', deptSelect.value);
  if (activeCatBtn && activeCatBtn.dataset.id !== 'all' && activeCatBtn.dataset.id !== 'unassigned') {
    form.append('category_id', activeCatBtn.dataset.id);
  }

  try {
    // ── Real byte-level progress via XHR ──────────────────────
    const data = await _xhrUpload(form, pct => {
      updateProgress(pct, `กำลังส่ง... ${pct}%`);
      _updateGhostProgress(ghosts, pct, pct < 85 ? 'กำลังส่ง...' : 'กำลังประมวลผล...');
    });

    updateProgress(95, 'กำลัง Index...');
    _transitionGhostsToIndexing(ghosts);

    if (data.ok) {
      const duplicates = (data.results || []).filter(r => r.status === 'duplicate');
      const failures   = (data.results || []).filter(r => r.status === 'error');
      const processing = (data.results || []).filter(r => r.status === 'processing');

      if (duplicates.length > 0) {
        toast(`⚠️ ไฟล์ซ้ำ ${duplicates.length} ไฟล์: ${duplicates.map(r => r.file).join(', ')}`, 'warning');
        // remove ghost ของไฟล์ซ้ำทันที
        duplicates.forEach((_, i) => ghosts[i] && ghosts[i].el.remove());
      }
      if (failures.length > 0) {
        toast(`❌ ผิดพลาด ${failures.length} ไฟล์: ${failures[0].error || failures[0].file}`, 'error');
      }
      if (processing.length > 0) {
        toast(`✅ นำเข้า ${processing.length} ไฟล์แล้ว กำลัง Index...`, 'success');
      }

      // โหลด file list จริงแล้วลบ ghosts (ป้องกัน duplicate card)
      await loadFiles();
      _removeGhosts(ghosts);
      await loadStatus();
    } else {
      _removeGhosts(ghosts);
      toast(data.error || 'อัปโหลดล้มเหลว', 'error');
    }
  } catch (e) {
    _removeGhosts(ghosts);
    toast('ข้อผิดพลาดในการเชื่อมต่อ', 'error');
  } finally {
    updateProgress(100, 'เสร็จสมบูรณ์');
    setTimeout(() => {
      uploadProgress.classList.add('hidden');
      updateProgress(0, '');
      hideGlobalLoading();
    }, 1500);
  }
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

      // Populate bulk move dropdown from categories
      const bulkMove = $('bulkDeptMove');
      if (bulkMove) {
        bulkMove.innerHTML = '<option value="">ย้ายหมวดหมู่...</option>' +
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
          <i data-lucide="${c.visibility === 'private' ? 'lock' : (c.visibility === 'restricted' ? 'users' : 'folder')}" class="w-3.5 h-3.5 ${c.visibility === 'private' ? 'text-amber-500' : (c.visibility === 'restricted' ? 'text-brand-500' : '')}"></i>
          <span class="truncate">${c.name}</span>
        </button>
        <div class="flex items-center opacity-0 group-hover:opacity-100 transition-all">
          ${(state.isAdmin || c.created_by === state.user) ? `
            <button onclick="openKBCategorySettings(${c.id})" class="p-1 px-1.5 text-surface-400 hover:text-brand-600 transition-all" title="ตั้งค่าความเป็นส่วนตัว">
              <i data-lucide="settings" class="w-3 h-3"></i>
            </button>
          ` : ''}
          ${canEditKB() ? `
            <button onclick="deleteKBCategory(${c.id})" class="p-1 px-1.5 text-surface-400 hover:text-red-500 transition-all" title="ลบหมวดหมู่">
              <i data-lucide="x" class="w-3 h-3"></i>
            </button>
          ` : ''}
        </div>
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

// ─── KB Category Settings ─────────────────────
let selectedCatUsers = [];

async function openKBCategorySettings(id) {
  const cat = state.kbCategories.find(c => c.id == id);
  if (!cat) return;
  
  $('catSettingsId').value = id;
  $('catSettingsTitle').textContent = `ตั้งค่าหมวดหมู่: ${cat.name}`;
  $('catUserSearch').value = '';
  setCatVisibility(cat.visibility || 'public');
  
  // 1. Pre-load all users from organization
  try {
    console.log("Fetching all users for restricted folder settings...");
    const data = await apiFetch('/api/chat/users');
    if (data && data.ok) {
      state.allUsers = data.users || [];
      console.log(`Loaded ${state.allUsers.length} users successfully.`);
    } else {
      console.warn("Failed to load users: Data not OK", data);
    }
  } catch(e) { 
    console.error("Failed to load user list error:", e); 
  }

  selectedCatUsers = [];
  $('catUserListArea').innerHTML = '<p class="text-[10px] text-surface-400 italic text-center py-4">กำลังโหลดสิทธิ์การเข้าถึง...</p>';
  
  // 2. Load existing access list
  try {
    const res = await apiFetch(`/api/kb/categories/access/${id}`);
    if (res.ok) {
      selectedCatUsers = res.users;
    }
  } catch (err) {
    console.error(err);
  }
  
  // 3. Render the selectable list
  renderCatUserList();
  
  const m = $('kbCategorySettingsModal');
  if (m) {
    m.classList.remove('hidden');
    m.classList.add('flex', 'items-center', 'justify-center');
  }
  initIcons();
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
      <div class="col-span-full py-20 text-center animate-in fade-in zoom-in duration-500">
        <div class="w-20 h-20 bg-surface-50 dark:bg-surface-900 rounded-full flex items-center justify-center mx-auto mb-6 text-surface-200">
          <i data-lucide="folder-open" class="w-10 h-10"></i>
        </div>
        <h3 class="text-lg font-black text-surface-900 dark:text-white mb-2">ยังไม่มีไฟล์ในคลังข้อมูล</h3>
        <p class="text-sm text-surface-400 max-w-xs mx-auto">เริ่มต้นโดยการอัปโหลดไฟล์เอกสารเพื่อให้ AI เรียนรู้ข้อมูลองค์กรของคุณ</p>
      </div>`;
    initIcons();
    return;
  }

  // Sort by timestamp (newest first) if available
  const sorted = [...files].sort((a, b) => {
    return new Date(b.timestamp || 0) - new Date(a.timestamp || 0);
  });

  fileList.innerHTML = sorted.map(f => {
    const isProcessing = f.status === 'processing';
    const isError = f.status === 'error';
    const catName = getKBCategoryName(f.category_id);
    const fileSize = formatSize(f.size);
    
    return `
      <div class="group relative bg-white dark:bg-surface-900 border border-surface-100 dark:border-surface-800 rounded-3xl p-5 transition-all duration-300 hover:shadow-2xl hover:shadow-brand-500/10 hover:border-brand-500/50 flex flex-col gap-4 animate-in slide-in-from-bottom-4 duration-500" 
           id="file-${f.file_id}" 
           draggable="true" 
           ondragstart="handleFileDragStart(event, '${f.file_id}')">
        
        <!-- Status Indicator -->
        <div class="absolute top-4 right-4 flex items-center gap-2">
          ${isProcessing ? `
            <span class="flex h-2 w-2 relative">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
            </span>
            <span class="text-[9px] font-black text-amber-500 uppercase tracking-tighter">Indexing...</span>
          ` : isError ? `
            <i data-lucide="alert-circle" class="w-3.5 h-3.5 text-rose-500"></i>
            <span class="text-[9px] font-black text-rose-500 uppercase tracking-tighter">Failed</span>
          ` : `
            <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"></div>
            <span class="text-[9px] font-black text-emerald-500 uppercase tracking-tighter">Ready</span>
          `}
        </div>

        <div class="flex items-start gap-4">
          <div class="w-12 h-12 rounded-2xl bg-surface-50 dark:bg-surface-800 border border-surface-100 dark:border-surface-700 flex items-center justify-center text-surface-400 group-hover:bg-brand-50 group-hover:text-brand-600 group-hover:border-brand-100 transition-all duration-300 transform group-hover:scale-110 group-hover:-rotate-3">
            <i data-lucide="${FILE_LUCIDE[f.type] || 'file'}" class="w-6 h-6"></i>
          </div>
          <div class="min-w-0 flex-1 pt-1">
            <h4 class="font-black text-sm text-surface-900 dark:text-white truncate uppercase tracking-tight mb-1" title="${f.name}">${f.name}</h4>
            <div class="flex items-center gap-2">
               <span class="text-[9px] font-black px-1.5 py-0.5 rounded-md bg-purple-50 dark:bg-purple-900/20 text-purple-600 uppercase">${f.department || 'General'}</span>
               <span class="text-[9px] font-black px-1.5 py-0.5 rounded-md bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 uppercase truncate max-w-[80px]">${catName}</span>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-2 mt-2">
          <div class="bg-surface-50/50 dark:bg-surface-800/50 p-2.5 rounded-2xl border border-surface-100/50 dark:border-surface-700/50 flex flex-col justify-center">
            <p class="text-[8px] font-black text-surface-400 uppercase tracking-widest mb-1">Knowledge Units</p>
            <p class="text-xs font-black text-brand-600">${isProcessing ? '<span class="animate-pulse">---</span>' : (f.chunks || 0) + ' CHUNKS'}</p>
          </div>
          <div class="bg-surface-50/50 dark:bg-surface-800/50 p-2.5 rounded-2xl border border-surface-100/50 dark:border-surface-700/50 flex flex-col justify-center">
            <p class="text-[8px] font-black text-surface-400 uppercase tracking-widest mb-1">File Size</p>
            <p class="text-xs font-black text-surface-600 dark:text-surface-300 uppercase">${fileSize}</p>
          </div>
        </div>

        <div class="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-surface-100/50 dark:border-surface-800/50 mt-auto">
          <div class="flex items-center gap-1 min-w-0 flex-1 pr-2">
             ${canEditKB() ? `<input type="checkbox" class="file-checkbox w-4 h-4 rounded-md border-surface-300 text-brand-600 focus:ring-brand-600 cursor-pointer flex-shrink-0" data-id="${f.file_id}">` : ''}
             <span class="text-[9px] font-black text-surface-400 ml-1 truncate opacity-60" title="ID: ${f.file_id}">ID: ${f.file_id.substring(0, 8)}...</span>
          </div>
          <div class="flex items-center gap-1 flex-shrink-0">
            <button class="file-view-btn p-1.5 text-surface-400 hover:text-brand-600 hover:bg-brand-50 dark:hover:bg-brand-900/20 transition-all rounded-xl" data-id="${f.file_id}" data-name="${f.name}" title="เปิดอ่าน">
              <i data-lucide="eye" class="w-4 h-4"></i>
            </button>
            ${!isProcessing ? `
              <button class="file-scan-btn p-1.5 text-surface-400 hover:text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-all rounded-xl" data-id="${f.file_id}" title="สแกนด้วย AI">
                <i data-lucide="scan-search" class="w-4 h-4"></i>
              </button>
              ${canEditKB() ? `
                ${['csv', 'txt', 'md'].includes((f.type || '').toLowerCase()) ? `
                <button class="file-edit-btn p-1.5 text-surface-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all rounded-xl" data-id="${f.file_id}" data-type="${(f.type || '').toLowerCase()}" title="แก้ไขไฟล์">
                  <i data-lucide="edit" class="w-4 h-4"></i>
                </button>
                ` : ''}
                <button class="file-move-btn p-1.5 text-surface-400 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-all rounded-xl" data-id="${f.file_id}" title="เปลี่ยนหมวดหมู่">
                  <i data-lucide="folder-input" class="w-4 h-4"></i>
                </button>
                <button class="file-del-btn p-1.5 text-surface-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-900/20 transition-all rounded-xl" data-id="${f.file_id}" title="ลบไฟล์">
                  <i data-lucide="trash-2" class="w-4 h-4"></i>
                </button>
              ` : ''}
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }).join('');

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
    bar.classList.remove('hidden');
    bar.classList.add('flex');
    if (count) count.textContent = `${cbs.length} รายการ`;
  } else {
    bar.classList.add('hidden');
    bar.classList.remove('flex');
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
    if (!confirm(`ยืนยัน: ลบไฟล์ ${cbs.length} รายการอย่างถาวร?`)) return;

    bulkDeleteBtn.disabled = true;
    bulkDeleteBtn.innerHTML = '<i class="animate-spin" data-lucide="loader-2"></i> กำลังลบ...';
    initIcons();

    for (const cb of cbs) {
      const fileId = cb.dataset.id;
      const item = $(`file-${fileId}`);
      if (item) item.classList.add('opacity-30', 'grayscale');
      await apiFetch(`/api/files/${fileId}`, { method: 'DELETE' });
    }

    toast(`ลบสำเร็จ ${cbs.length} ไฟล์`, 'success');
    await loadFiles();
    await loadStatus();
    bulkDeleteBtn.disabled = false;
    bulkDeleteBtn.innerHTML = '<i data-lucide="trash-2" class="w-3 h-3"></i> ลบที่เลือก';
    initIcons();
  };
}

// Bulk move to category handler
const bulkDeptMove = $('bulkDeptMove');

if (bulkDeptMove) {
  bulkDeptMove.addEventListener('change', async () => {
    const catId = bulkDeptMove.value;
    if (!catId) return;
    const cbs = fileList.querySelectorAll('.file-checkbox:checked');
    if (!cbs.length) { bulkDeptMove.value = ''; return; }
    if (!confirm(`ย้าย ${cbs.length} ไฟล์ไปยังหมวดหมู่ที่เลือก?`)) { bulkDeptMove.value = ''; return; }

    for (const cb of cbs) {
      await apiFetch(`/api/files/${cb.dataset.id}/category`, {
        method: 'PUT',
        body: JSON.stringify({ category_id: catId === 'unassigned' ? null : catId })
      });
    }
    toast(`ย้ายไฟล์เรียบร้อย ${cbs.length} รายการ`, 'success');
    bulkDeptMove.value = '';
    await loadFiles();
  });
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

if (chatAttachBtn && chatImageInput) {
  chatAttachBtn.onclick = () => chatImageInput.click();
  chatImageInput.onchange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        state.pendingImage = event.target.result;
        state.pendingMime = file.type;
        chatImageThumbnail.src = state.pendingImage;
        chatImagePreview.classList.remove('hidden');
        initIcons();
      };
      reader.readAsDataURL(file);
    }
  };
}