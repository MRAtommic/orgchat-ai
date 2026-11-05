// =====================================================================
// OrgChat AI — LINE Official Account & Broadcast Module
// =====================================================================

async function sendLineBroadcast(msgId = 'lineBroadcastMsg', btnId = 'lineBroadcastBtn', toggleId = null, timeId = null) {
  const btn = document.getElementById(btnId);
  const msgInput = document.getElementById(msgId);
  
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
  const toggle = toggleId ? document.getElementById(toggleId) : null;
  const timeInput = timeId ? document.getElementById(timeId) : null;
  if (toggle && toggle.checked && timeInput && timeInput.value) {
    schedule_time = timeInput.value;
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
      msgInput.value = '';
      if (toggle) toggle.checked = false;
      if (timeInput) {
        timeInput.value = '';
        const containerId = timeId.replace('Time', 'TimeContainer');
        const container = document.getElementById(containerId);
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

async function openLineSettings() {
    const modal = document.getElementById('lineSettingsModal');
    if (!modal) return;
    
    // Fetch and populate personas dropdown
    try {
        const personasData = await apiFetch('/api/personas');
        const select = document.getElementById('lineSettingsPersona');
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
            document.getElementById('lineSettingsGreeting').value = data.config.greeting_message || '';
            document.getElementById('lineSettingsAIEnabled').checked = data.config.ai_auto_responder_enabled || false;
            if (document.getElementById('lineSettingsPersona')) {
                document.getElementById('lineSettingsPersona').value = data.config.selected_persona_id || 'default';
            }
        }
    } catch (err) {
        console.error('Failed to fetch general LINE settings:', err);
    }

    // Load Org-specific LINE Channel credentials
    try {
        const orgData = await apiFetch('/api/org/line/channel-config');
        if (orgData && orgData.ok) {
            document.getElementById('lineSettingsBotId').value = orgData.bot_basic_id || '';
            document.getElementById('lineSettingsToken').value = orgData.channel_access_token_masked || '';
            document.getElementById('lineSettingsSecret').value = orgData.channel_secret_masked || '';
            
            const badge = document.getElementById('lineOrgBadge');
            if (badge) {
                if (orgData.has_custom_keys) {
                    badge.textContent = 'บอทเฉพาะองค์กร';
                    badge.className = 'text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300';
                } else {
                    badge.textContent = 'บอทส่วนกลาง';
                    badge.className = 'text-[10px] px-2 py-0.5 rounded-full font-bold bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300';
                }
            }
            if (document.getElementById('lineTokenStatus')) {
                document.getElementById('lineTokenStatus').textContent = orgData.has_custom_keys ? '✅ ใช้ Custom Key อยู่' : 'ℹ️ ใช้บอทส่วนกลาง';
            }
        }
    } catch (err) {
        console.error('Failed to fetch org LINE channel config:', err);
    }
    
    modal.classList.remove('hidden');
    if (window.lucide) lucide.createIcons();
}

async function saveLineSettings() {
    const btn = document.getElementById('btnSaveLineSettings') || event?.target;
    const originalHtml = btn ? btn.innerHTML : 'บันทึกการตั้งค่า';
    
    const token = document.getElementById('lineSettingsToken').value.trim();
    const secret = document.getElementById('lineSettingsSecret').value.trim();
    const botId = document.getElementById('lineSettingsBotId').value.trim();

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> กำลังบันทึก...';
        if (window.lucide) lucide.createIcons();
    }
    
    try {
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
        
        const payload = {
            greeting_message: document.getElementById('lineSettingsGreeting').value.trim(),
            ai_auto_responder_enabled: document.getElementById('lineSettingsAIEnabled').checked,
            selected_persona_id: document.getElementById('lineSettingsPersona') ? document.getElementById('lineSettingsPersona').value : 'default'
        };
        
        const data = await apiFetch('/api/admin/line/settings', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        if (data && data.ok) {
            toast('บันทึกการตั้งค่า LINE เรียบร้อยแล้ว', 'success');
            document.getElementById('lineSettingsModal').classList.add('hidden');
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
    const btn = document.getElementById('btnTestLineChannel');
    const token = document.getElementById('lineSettingsToken').value.trim();
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
            if (res.bot_info?.basicId && !document.getElementById('lineSettingsBotId').value) {
                document.getElementById('lineSettingsBotId').value = res.bot_info.basicId;
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
            document.getElementById('lineSettingsToken').value = '';
            document.getElementById('lineSettingsSecret').value = '';
            document.getElementById('lineSettingsBotId').value = '@905gsngi';
            openLineSettings();
        } else {
            toast(res?.error || 'ไม่สามารถลบการตั้งค่าได้ค่ะ', 'error');
        }
    } catch (e) {
        toast('เกิดข้อผิดพลาดในการเชื่อมต่อค่ะ', 'error');
    }
}

function copyLineWebhookUrl() {
    const text = document.getElementById('lineWebhookUrlText')?.textContent || window.location.origin + '/api/line/webhook';
    navigator.clipboard.writeText(text).then(() => {
        toast('คัดลอก Webhook URL เรียบร้อยแล้วค่ะ', 'success');
    }).catch(() => {
        toast('ไม่สามารถคัดลอกได้ กรุณาคัดลอกด้วยตนเองค่ะ', 'warning');
    });
}

async function refreshBroadcastHistory() {
    const list = document.getElementById('broadcastHistoryList');
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
      setTimeout(refreshBroadcastHistory, 2000);
    } else {
      sendLineBroadcast('lineBroadcastMsg', 'lineBroadcastBtn');
    }
  }
});

// Window Exports
window.sendLineBroadcast = sendLineBroadcast;
window.openLineSettings = openLineSettings;
window.saveLineSettings = saveLineSettings;
window.refreshBroadcastHistory = refreshBroadcastHistory;
window.testOrgLineConnection = testOrgLineConnection;
window.resetOrgLineBot = resetOrgLineBot;
window.copyLineWebhookUrl = copyLineWebhookUrl;


// ═════════════════════════════════════════════════════════════════════
// 🎨 LINE Flex Card Designer Controller
// ═════════════════════════════════════════════════════════════════════

const FLEX_PRESETS = {
  blue: {
    primary_color: '#2563EB',
    header_bg: '#1B2838',
    header_icon: '📢',
    header_title: 'ประกาศใหม่',
    header_sub: 'NEW ANNOUNCEMENT',
    badge_bg: '#EFF6FF',
    badge_color: '#2563EB',
    portal_button_text: '💬 ดูในระบบ OrgChat',
    feed_primary_color: '#7C3AED',
    feed_header_bg: '#7C3AED',
    feed_header_icon: '✨',
    feed_header_title: 'โพสต์ใหม่ใน Feed',
    feed_header_sub: 'NEW FEED POST'
  },
  purple: {
    primary_color: '#7C3AED',
    header_bg: '#2E1065',
    header_icon: '🚀',
    header_title: 'ประกาศองค์กร',
    header_sub: 'OFFICIAL NOTICE',
    badge_bg: '#F5F3FF',
    badge_color: '#7C3AED',
    portal_button_text: '💬 ดูโพสต์ใน OrgChat',
    feed_primary_color: '#8B5CF6',
    feed_header_bg: '#581C87',
    feed_header_icon: '💡',
    feed_header_title: 'สาระน่ารู้ & อัปเดต',
    feed_header_sub: 'KNOWLEDGE & FEED'
  },
  emerald: {
    primary_color: '#059669',
    header_bg: '#064E3B',
    header_icon: '🌿',
    header_title: 'ข่าวสารองค์กร',
    header_sub: 'COMPANY ANNOUNCEMENT',
    badge_bg: '#ECFDF5',
    badge_color: '#059669',
    portal_button_text: 'เข้าดูระบบ OrgChat',
    feed_primary_color: '#10B981',
    feed_header_bg: '#047857',
    feed_header_icon: '🌱',
    feed_header_title: 'เรื่องเล่าชาวองค์กร',
    feed_header_sub: 'TEAM STORIES'
  },
  amber: {
    primary_color: '#D97706',
    header_bg: '#451A03',
    header_icon: '🔥',
    header_title: 'ประกาศด่วน',
    header_sub: 'URGENT BULLETIN',
    badge_bg: '#FFFBEB',
    badge_color: '#D97706',
    portal_button_text: '💬 ตรวจสอบในระบบ',
    feed_primary_color: '#F59E0B',
    feed_header_bg: '#78350F',
    feed_header_icon: '⚡',
    feed_header_title: 'อัปเดตกิจกรรม',
    feed_header_sub: 'ACTIVITIES & FEED'
  },
  rose: {
    primary_color: '#E11D48',
    header_bg: '#4C0519',
    header_icon: '💎',
    header_title: 'ข่าวประชาสัมพันธ์',
    header_sub: 'SPECIAL NOTICE',
    badge_bg: '#FFF1F2',
    badge_color: '#E11D48',
    portal_button_text: '💬 เปิดดูใน OrgChat',
    feed_primary_color: '#F43F5E',
    feed_header_bg: '#881337',
    feed_header_icon: '💖',
    feed_header_title: 'ไฮไลท์ประจำวัน',
    feed_header_sub: 'DAILY HIGHLIGHTS'
  },
  dark: {
    primary_color: '#3B82F6',
    header_bg: '#0F172A',
    header_icon: '🏢',
    header_title: 'ประกาศสำนักงาน',
    header_sub: 'OFFICE BULLETIN',
    badge_bg: '#1E293B',
    badge_color: '#60A5FA',
    portal_button_text: '💬 เข้าสู่ระบบ OrgChat',
    feed_primary_color: '#6366F1',
    feed_header_bg: '#18181B',
    feed_header_icon: '🌐',
    feed_header_title: 'กระดานข่าวสาร',
    feed_header_sub: 'NEWSFEED'
  }
};

let currentFlexTab = 'announcement';

async function loadFlexSettings() {
  // U0-2: Skip if user not authenticated
  if (typeof state === 'undefined' || !state.user) return;
  try {
    const res = await fetch('/api/org/flex-settings');
    const data = await res.json();
    if (data.ok && data.settings) {
      const s = data.settings;
      // Populate Announcement inputs
      if ($('flexPrimaryColor')) $('flexPrimaryColor').value = s.primary_color || '#2563EB';
      if ($('flexPrimaryColorHex')) $('flexPrimaryColorHex').value = s.primary_color || '#2563EB';
      if ($('flexHeaderBg')) $('flexHeaderBg').value = s.header_bg || '#1B2838';
      if ($('flexHeaderBgHex')) $('flexHeaderBgHex').value = s.header_bg || '#1B2838';
      if ($('flexHeaderIcon')) $('flexHeaderIcon').value = s.header_icon || '📢';
      if ($('flexHeaderTitle')) $('flexHeaderTitle').value = s.header_title || 'ประกาศใหม่';
      if ($('flexHeaderSub')) $('flexHeaderSub').value = s.header_sub || 'NEW ANNOUNCEMENT';
      if ($('flexBadgeBg')) $('flexBadgeBg').value = s.badge_bg || '#EFF6FF';
      if ($('flexBadgeBgHex')) $('flexBadgeBgHex').value = s.badge_bg || '#EFF6FF';
      if ($('flexBadgeColor')) $('flexBadgeColor').value = s.badge_color || s.primary_color || '#2563EB';
      if ($('flexBadgeColorHex')) $('flexBadgeColorHex').value = s.badge_color || s.primary_color || '#2563EB';
      if ($('flexPortalBtn')) $('flexPortalBtn').value = s.portal_button_text || '💬 ดูในระบบ OrgChat';

      // Populate Feed inputs
      if ($('flexFeedPrimaryColor')) $('flexFeedPrimaryColor').value = s.feed_primary_color || '#7C3AED';
      if ($('flexFeedPrimaryColorHex')) $('flexFeedPrimaryColorHex').value = s.feed_primary_color || '#7C3AED';
      if ($('flexFeedHeaderBg')) $('flexFeedHeaderBg').value = s.feed_header_bg || '#7C3AED';
      if ($('flexFeedHeaderBgHex')) $('flexFeedHeaderBgHex').value = s.feed_header_bg || '#7C3AED';
      if ($('flexFeedHeaderIcon')) $('flexFeedHeaderIcon').value = s.feed_header_icon || '✨';
      if ($('flexFeedHeaderTitle')) $('flexFeedHeaderTitle').value = s.feed_header_title || 'โพสต์ใหม่ใน Feed';
      if ($('flexFeedHeaderSub')) $('flexFeedHeaderSub').value = s.feed_header_sub || 'NEW FEED POST';

      updateLiveFlexPreview();
    }
  } catch (err) {
    console.error('Failed to load flex settings:', err);
  }
}

function updateLiveFlexPreview() {
  const isAnnounce = currentFlexTab === 'announcement';

  const primary = isAnnounce
    ? ($('flexPrimaryColorHex')?.value || '#2563EB')
    : ($('flexFeedPrimaryColorHex')?.value || '#7C3AED');
  
  const headerBg = isAnnounce
    ? ($('flexHeaderBgHex')?.value || '#1B2838')
    : ($('flexFeedHeaderBgHex')?.value || '#7C3AED');

  const headerIcon = isAnnounce
    ? ($('flexHeaderIcon')?.value || '📢')
    : ($('flexFeedHeaderIcon')?.value || '✨');

  const headerTitle = isAnnounce
    ? ($('flexHeaderTitle')?.value || 'ประกาศใหม่')
    : ($('flexFeedHeaderTitle')?.value || 'โพสต์ใหม่ใน Feed');

  const headerSub = isAnnounce
    ? ($('flexHeaderSub')?.value || 'NEW ANNOUNCEMENT')
    : ($('flexFeedHeaderSub')?.value || 'NEW FEED POST');

  const badgeBg = isAnnounce
    ? ($('flexBadgeBgHex')?.value || '#EFF6FF')
    : '#F5F3FF';

  const badgeColor = isAnnounce
    ? ($('flexBadgeColorHex')?.value || primary)
    : primary;

  const badgeText = isAnnounce ? 'GENERAL' : 'FEED';
  const portalBtn = $('flexPortalBtn')?.value || '💬 ดูในระบบ OrgChat';

  // Update Preview Elements
  const prevHeader = $('flexPrevHeader');
  if (prevHeader) prevHeader.style.backgroundColor = headerBg;

  const prevIcon = $('flexPrevHeaderIcon');
  if (prevIcon) prevIcon.textContent = headerIcon;

  const prevTitle = $('flexPrevHeaderTitle');
  if (prevTitle) prevTitle.textContent = headerTitle;

  const prevSub = $('flexPrevHeaderSub');
  if (prevSub) prevSub.textContent = headerSub;

  const prevBadge = $('flexPrevBadge');
  if (prevBadge) {
    prevBadge.textContent = badgeText;
    prevBadge.style.backgroundColor = badgeBg;
    prevBadge.style.color = badgeColor;
  }

  const prevAvatar = $('flexPrevAvatar');
  if (prevAvatar) prevAvatar.style.backgroundColor = primary;

  const prevBtnPrimary = $('flexPrevBtnPrimary');
  if (prevBtnPrimary) prevBtnPrimary.style.backgroundColor = primary;

  const prevBtnSecondary = $('flexPrevBtnSecondary');
  if (prevBtnSecondary) prevBtnSecondary.textContent = portalBtn;
}

function applyFlexPreset(key) {
  const p = FLEX_PRESETS[key];
  if (!p) return;

  if ($('flexPrimaryColor')) $('flexPrimaryColor').value = p.primary_color;
  if ($('flexPrimaryColorHex')) $('flexPrimaryColorHex').value = p.primary_color;
  if ($('flexHeaderBg')) $('flexHeaderBg').value = p.header_bg;
  if ($('flexHeaderBgHex')) $('flexHeaderBgHex').value = p.header_bg;
  if ($('flexHeaderIcon')) $('flexHeaderIcon').value = p.header_icon;
  if ($('flexHeaderTitle')) $('flexHeaderTitle').value = p.header_title;
  if ($('flexHeaderSub')) $('flexHeaderSub').value = p.header_sub;
  if ($('flexBadgeBg')) $('flexBadgeBg').value = p.badge_bg;
  if ($('flexBadgeBgHex')) $('flexBadgeBgHex').value = p.badge_bg;
  if ($('flexBadgeColor')) $('flexBadgeColor').value = p.badge_color;
  if ($('flexBadgeColorHex')) $('flexBadgeColorHex').value = p.badge_color;
  if ($('flexPortalBtn')) $('flexPortalBtn').value = p.portal_button_text;

  if ($('flexFeedPrimaryColor')) $('flexFeedPrimaryColor').value = p.feed_primary_color;
  if ($('flexFeedPrimaryColorHex')) $('flexFeedPrimaryColorHex').value = p.feed_primary_color;
  if ($('flexFeedHeaderBg')) $('flexFeedHeaderBg').value = p.feed_header_bg;
  if ($('flexFeedHeaderBgHex')) $('flexFeedHeaderBgHex').value = p.feed_header_bg;
  if ($('flexFeedHeaderIcon')) $('flexFeedHeaderIcon').value = p.feed_header_icon;
  if ($('flexFeedHeaderTitle')) $('flexFeedHeaderTitle').value = p.feed_header_title;
  if ($('flexFeedHeaderSub')) $('flexFeedHeaderSub').value = p.feed_header_sub;

  updateLiveFlexPreview();
  if (typeof toast === 'function') toast(`เลือกชุดสี: ${key.toUpperCase()}`, 'info');
}

function switchFlexTab(tab) {
  currentFlexTab = tab;
  const isAnnounce = tab === 'announcement';

  const tabAnnounce = $('flex-tab-announcement');
  const tabFeed = $('flex-tab-feed');
  const secAnnounce = $('flexControlsAnnouncement');
  const secFeed = $('flexControlsFeed');

  if (tabAnnounce && tabFeed) {
    if (isAnnounce) {
      tabAnnounce.className = 'px-4 py-2 rounded-xl text-xs font-bold bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300';
      tabFeed.className = 'px-4 py-2 rounded-xl text-xs font-bold text-surface-500 hover:text-surface-900 dark:hover:text-white';
    } else {
      tabFeed.className = 'px-4 py-2 rounded-xl text-xs font-bold bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300';
      tabAnnounce.className = 'px-4 py-2 rounded-xl text-xs font-bold text-surface-500 hover:text-surface-900 dark:hover:text-white';
    }
  }

  if (secAnnounce) secAnnounce.classList.toggle('hidden', !isAnnounce);
  if (secFeed) secFeed.classList.toggle('hidden', isAnnounce);

  updateLiveFlexPreview();
}

async function saveFlexSettings() {
  const btn = $('btnSaveFlexSettings');
  const oldText = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i> กำลังบันทึก...';
  }

  const payload = {
    primary_color: $('flexPrimaryColorHex')?.value || '#2563EB',
    header_bg: $('flexHeaderBgHex')?.value || '#1B2838',
    header_icon: $('flexHeaderIcon')?.value || '📢',
    header_title: $('flexHeaderTitle')?.value || 'ประกาศใหม่',
    header_sub: $('flexHeaderSub')?.value || 'NEW ANNOUNCEMENT',
    badge_bg: $('flexBadgeBgHex')?.value || '#EFF6FF',
    badge_color: $('flexBadgeColorHex')?.value || '#2563EB',
    portal_button_text: $('flexPortalBtn')?.value || '💬 ดูในระบบ OrgChat',
    feed_primary_color: $('flexFeedPrimaryColorHex')?.value || '#7C3AED',
    feed_header_bg: $('flexFeedHeaderBgHex')?.value || '#7C3AED',
    feed_header_icon: $('flexFeedHeaderIcon')?.value || '✨',
    feed_header_title: $('flexFeedHeaderTitle')?.value || 'โพสต์ใหม่ใน Feed',
    feed_header_sub: $('flexFeedHeaderSub')?.value || 'NEW FEED POST',
    card_style: 'modern'
  };

  try {
    const res = await fetch('/api/org/flex-settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.ok) {
      if (typeof toast === 'function') toast('บันทึกการออกแบบ LINE Flex Card ขององค์กรสำเร็จแล้ว 🎉', 'success');
    } else {
      if (typeof toast === 'function') toast(data.error || 'บันทึกไม่สำเร็จ', 'error');
    }
  } catch (err) {
    console.error('Error saving flex settings:', err);
    if (typeof toast === 'function') toast('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์', 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = oldText;
      if (window.lucide && typeof window.lucide.createIcons === 'function') window.lucide.createIcons();
    }
  }
}

async function resetFlexSettings() {
  if (!confirm('ต้องการคืนค่าเริ่มต้นมาตรฐานของ LINE Flex Card สำหรับองค์กรนี้ใช่หรือไม่?')) return;
  try {
    const res = await fetch('/api/org/flex-settings/reset', { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      if (typeof toast === 'function') toast('คืนค่าเริ่มต้นมาตรฐานเรียบร้อยแล้ว ✅', 'success');
      loadFlexSettings();
    } else {
      if (typeof toast === 'function') toast(data.error || 'รีเซ็ตไม่สำเร็จ', 'error');
    }
  } catch (err) {
    console.error('Error resetting flex settings:', err);
  }
}

// Helper to sync color input with hex text input
function syncFlexColor(pickerId, hexId) {
  const picker = $(pickerId);
  const hex = $(hexId);
  if (picker && hex) {
    picker.addEventListener('input', () => {
      hex.value = picker.value.toUpperCase();
      updateLiveFlexPreview();
    });
    hex.addEventListener('input', () => {
      if (/^#[0-9A-Fa-f]{6}$/.test(hex.value)) {
        picker.value = hex.value;
        updateLiveFlexPreview();
      }
    });
  }
}

// Initialize listeners on DOM load
document.addEventListener('DOMContentLoaded', () => {
  syncFlexColor('flexPrimaryColor', 'flexPrimaryColorHex');
  syncFlexColor('flexHeaderBg', 'flexHeaderBgHex');
  syncFlexColor('flexBadgeBg', 'flexBadgeBgHex');
  syncFlexColor('flexBadgeColor', 'flexBadgeColorHex');
  syncFlexColor('flexFeedPrimaryColor', 'flexFeedPrimaryColorHex');
  syncFlexColor('flexFeedHeaderBg', 'flexFeedHeaderBgHex');

  // Load flex settings if already on line-manager view
  setTimeout(loadFlexSettings, 1000);
});

// Window Exports
window.loadFlexSettings = loadFlexSettings;
window.updateLiveFlexPreview = updateLiveFlexPreview;
window.applyFlexPreset = applyFlexPreset;
window.switchFlexTab = switchFlexTab;
window.saveFlexSettings = saveFlexSettings;
window.resetFlexSettings = resetFlexSettings;
window.switchLineSubTab = switchLineSubTab;

// ─── Segmented Sub-Tab Switcher for LINE Management ──────────────
function switchLineSubTab(tab = 'groups') {
  const tabs = {
    groups: { btn: document.getElementById('line-tab-groups'), sec: document.getElementById('lineTabGroupsPanel') },
    flex: { btn: document.getElementById('line-tab-flex'), sec: document.getElementById('lineTabFlexPanel') },
    broadcast: { btn: document.getElementById('line-tab-broadcast'), sec: document.getElementById('lineTabBroadcastPanel') },
    settings: { btn: document.getElementById('line-tab-settings'), sec: document.getElementById('lineTabSettingsPanel') }
  };

  const activeClasses = ['bg-white', 'dark:bg-surface-700', 'shadow-sm', 'text-brand-600'];
  const inactiveClasses = ['text-surface-400'];

  Object.keys(tabs).forEach(k => {
    const item = tabs[k];
    const isActive = (k === tab);
    if (item.btn) {
      if (isActive) {
        item.btn.classList.add(...activeClasses);
        item.btn.classList.remove(...inactiveClasses);
      } else {
        item.btn.classList.remove(...activeClasses);
        item.btn.classList.add(...inactiveClasses);
      }
    }
    if (item.sec) {
      item.sec.classList.toggle('hidden', !isActive);
      if (isActive) {
        item.sec.classList.remove('animate-in', 'fade-in', 'duration-200');
        void item.sec.offsetWidth;
        item.sec.classList.add('animate-in', 'fade-in', 'duration-200');
      }
    }
  });

  if (tab === 'groups') {
    if (typeof loadLineGroups === 'function') loadLineGroups(true);
    if (typeof loadGoogleFoldersForGroupRegister === 'function') loadGoogleFoldersForGroupRegister();
  } else if (tab === 'flex') {
    if (typeof loadFlexSettings === 'function') loadFlexSettings();
    if (typeof updateLiveFlexPreview === 'function') updateLiveFlexPreview();
  } else if (tab === 'broadcast') {
    if (typeof refreshBroadcastHistory === 'function') refreshBroadcastHistory();
  }
  if (typeof initIcons === 'function') {
    initIcons();
  } else if (window.lucide && typeof window.lucide.createIcons === 'function') {
    window.lucide.createIcons();
  }
}
window.switchLineSubTab = switchLineSubTab;
