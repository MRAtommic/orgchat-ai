// --- OrgChat AI: ADMIN Module ---

// ─── Email Whitelist Logic ───────────────────
async function loadWhitelist() {
  try {
    const res = await apiFetch('/api/admin/whitelist');
    if (res && res.ok) {
      const chk = $('settingEmailWhitelist');
      const container = $('whitelistContainer');
      if (chk) chk.checked = res.enabled;
      if (container) container.classList.toggle('hidden', !res.enabled);
      renderWhitelist(res.emails || []);
    }
  } catch (e) {
    console.error('Failed to load whitelist:', e);
  }
}

function renderWhitelist(emails) {
  const list = $('whitelistEmailList');
  if (!list) return;
  if (emails.length === 0) {
    list.innerHTML = '<li class="py-3 text-sm text-surface-500 text-center">ยังไม่มีอีเมลในระบบ</li>';
    return;
  }
  list.innerHTML = emails.map(item => `
    <li class="py-2 flex items-center justify-between group">
      <div>
        <div class="text-sm font-bold text-surface-900 dark:text-white">${item.email}</div>
        <div class="text-xs text-surface-500">เพิ่มโดย: ${item.added_by} • ${new Date(item.created_at).toLocaleDateString('th-TH')}</div>
      </div>
      <button type="button" onclick="removeWhitelistEmail('${item.email}')" class="text-red-500 hover:text-red-700 p-2 rounded opacity-0 group-hover:opacity-100 transition-opacity">
        <i data-lucide="trash-2" class="w-4 h-4"></i>
      </button>
    </li>
  `).join('');
  initIcons();
}

async function toggleEmailWhitelist(enabled) {
  const container = $('whitelistContainer');
  const chk = $('settingEmailWhitelist');
  if (container) container.classList.toggle('hidden', !enabled);
  try {
    const res = await apiFetch('/api/admin/whitelist/toggle', {
      method: 'POST',
      body: JSON.stringify({ enabled })
    });
    if (res.ok) {
      toast(enabled ? 'เปิด Whitelist แล้ว — ใช้ได้กับ Login ผ่าน Google' : 'ปิด Whitelist แล้ว', 'success');
    } else {
      // Revert UI on failure
      if (chk) chk.checked = !enabled;
      if (container) container.classList.toggle('hidden', enabled);
      toast(res.error || 'เกิดข้อผิดพลาด', 'error');
    }
  } catch (e) {
    // Revert UI on error
    if (chk) chk.checked = !enabled;
    if (container) container.classList.toggle('hidden', enabled);
    toast('ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้', 'error');
  }
}

async function addWhitelistEmail() {
  const input = $('whitelistEmailInput');
  const email = input.value.trim();
  if (!email || !email.includes('@')) {
    toast('กรุณากรอกอีเมลให้ถูกต้อง', 'warning');
    return;
  }
  try {
    const res = await apiFetch('/api/admin/whitelist', {
      method: 'POST',
      body: JSON.stringify({ email })
    });
    if (res.ok) {
      toast('เพิ่มอีเมลสำเร็จ', 'success');
      input.value = '';
      loadWhitelist(); // Refresh
    } else {
      toast(res.error || 'เกิดข้อผิดพลาด', 'error');
    }
  } catch (e) {
    toast(e.message || 'ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้', 'error');
  }
}

async function removeWhitelistEmail(email) {
  if (!confirm(`คุณต้องการลบ ${email} ออกจาก Whitelist ใช่หรือไม่?`)) return;
  try {
    const res = await apiFetch(`/api/admin/whitelist/${encodeURIComponent(email)}`, {
      method: 'DELETE'
    });
    if (res.ok) {
      toast('ลบอีเมลสำเร็จ', 'success');
      loadWhitelist(); // Refresh
    } else {
      toast(res.error || 'เกิดข้อผิดพลาด', 'error');
    }
  } catch (e) {
    toast(e.message || 'ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้', 'error');
  }
}

/**
 * Parses structured AI actions from text response.
 */
function parseAIActions(text) {
  let displayHtml = markdownToHtml(text);
  let calendarData = null;
  let reconcileData = null;

  // 1. Calendar Action Detection
  const calMatch = text.match(/\[CALENDAR_ACTION\]([\s\S]*?)\[\/CALENDAR_ACTION\]/);
  if (calMatch) {
    try {
      calendarData = JSON.parse(calMatch[1]);
      // Clean up the text for display (remove the raw JSON tag)
      displayHtml = displayHtml.replace(/\[CALENDAR_ACTION\][\s\S]*?\[\/CALENDAR_ACTION\]/g, '');
    } catch (e) { console.error('Calendar JSON parse error:', e); }
  }

  // 2. Reconciliation (Accounting) Action Detection
  const reconMatch = text.match(/\[RECONCILE_ACTION\]([\s\S]*?)\[\/RECONCILE_ACTION\]/);
  if (reconMatch) {
    try {
      reconcileData = JSON.parse(reconMatch[1]);
      // Clean up the text for display (remove the raw JSON tag)
      displayHtml = displayHtml.replace(/\[RECONCILE_ACTION\][\s\S]*?\[\/RECONCILE_ACTION\]/g, '');
    } catch (e) { console.error('Reconcile JSON parse error:', e); }
  }

  return { displayHtml, calendarData, reconcileData };
}

// ─── Audit Trail & Security Compliance UI ──────────
async function loadAuditLogsUI() {
  const tbody = $('auditLogTableBody');
  if (!tbody) return;

  const username = ($('auditSearchInput') ? $('auditSearchInput').value.trim() : '');
  const action = ($('auditActionFilter') ? $('auditActionFilter').value : '');

  try {
    let url = `/api/admin/audit-logs?limit=50`;
    if (username) url += `&username=${encodeURIComponent(username)}`;
    if (action) url += `&action=${encodeURIComponent(action)}`;

    const res = await apiFetch(url);
    if (res && res.ok) {
      if (!res.logs || res.logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="px-4 py-4 text-center text-surface-400">ยังไม่มีประวัติการใช้งานในระบบ</td></tr>`;
        return;
      }
      tbody.innerHTML = res.logs.map(log => {
        let actionBadgeClass = 'bg-surface-100 text-surface-700 dark:bg-surface-800 dark:text-surface-300';
        if (log.action === 'CHAT_QUERY') actionBadgeClass = 'bg-brand-500/10 text-brand-600 border border-brand-500/20';
        else if (log.action === 'USER_LOGIN') actionBadgeClass = 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20';
        else if (log.action.includes('CLEARANCE') || log.action.includes('ACCESS')) actionBadgeClass = 'bg-purple-500/10 text-purple-600 border border-purple-500/20';
        else if (log.action.includes('DELETE')) actionBadgeClass = 'bg-rose-500/10 text-rose-600 border border-rose-500/20';

        return `
          <tr class="hover:bg-surface-50 dark:hover:bg-surface-800/40 transition-colors">
            <td class="px-3 py-2 text-[11px] text-surface-500 whitespace-nowrap">${log.timestamp ? new Date(log.timestamp).toLocaleString('th-TH') : '-'}</td>
            <td class="px-3 py-2 font-bold text-surface-900 dark:text-white">${log.username}</td>
            <td class="px-3 py-2"><span class="px-2 py-0.5 rounded text-[10px] font-black uppercase ${actionBadgeClass}">${log.action}</span></td>
            <td class="px-3 py-2 max-w-xs truncate" title="${log.details || ''}">${log.details || '-'}</td>
            <td class="px-3 py-2 text-[11px] text-surface-400 font-mono">${log.ip_address || '-'}</td>
          </tr>
        `;
      }).join('');
    } else {
      tbody.innerHTML = `<tr><td colspan="5" class="px-4 py-4 text-center text-red-500">เกิดข้อผิดพลาดในการโหลดข้อมูล</td></tr>`;
    }
  } catch (e) {
    console.error('Failed to load audit logs:', e);
    tbody.innerHTML = `<tr><td colspan="5" class="px-4 py-4 text-center text-red-500">ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้</td></tr>`;
  }
}

function exportAuditLogsCSV() {
  window.open('/api/admin/audit-logs/export', '_blank');
}

// ─── System Health Alerts Banner (Google Key, API warnings) ───
async function checkSystemAlerts() {
  try {
    const res = await apiFetch('/api/admin/system-alerts');
    if (res && res.ok && res.alerts && res.alerts.length > 0) {
      renderSystemAlertsBanner(res.alerts);
    } else {
      const banner = $('systemAlertBanner');
      if (banner) banner.classList.add('hidden');
    }
  } catch (e) {
    console.debug('System alerts check skipped:', e);
  }
}

function renderSystemAlertsBanner(alerts) {
  if (!alerts || !alerts.length) return;
  const alert = alerts[0];
  const dismissedKey = 'dismissed_alert_' + (alert.id || 'general') + '_' + (alert.timestamp || '');
  if (localStorage.getItem(dismissedKey) || sessionStorage.getItem('dismissed_google_alert')) {
    return;
  }
  let banner = $('systemAlertBanner');
  if (!banner) {
    banner = document.createElement('div');
    banner.id = 'systemAlertBanner';
    banner.className = 'w-full bg-amber-500/10 border-b border-amber-500/20 text-amber-900 dark:text-amber-200 px-4 py-2 text-xs flex items-center justify-between z-50 backdrop-blur-xs transition-all';
    document.body.prepend(banner);
  }
  banner.classList.remove('hidden');
  banner.innerHTML = `
    <div class="flex items-center gap-2.5 max-w-4xl mx-auto flex-1">
      <span class="inline-flex items-center justify-center w-5 h-5 bg-amber-500/20 text-amber-600 dark:text-amber-400 rounded-md font-bold text-xs shrink-0">⚠️</span>
      <div class="flex flex-wrap items-center gap-x-2 text-xs">
        <span class="font-bold text-surface-900 dark:text-white">${alert.title}:</span>
        <span class="text-surface-700 dark:text-surface-300 font-medium">${alert.message}</span>
        ${alert.hint ? `<span class="text-surface-500 dark:text-surface-400 text-[11px]">(${alert.hint})</span>` : ''}
      </div>
    </div>
    <button onclick="localStorage.setItem('${dismissedKey}', '1'); sessionStorage.setItem('dismissed_google_alert', '1'); document.getElementById('systemAlertBanner')?.remove()" class="text-surface-400 hover:text-surface-700 dark:hover:text-surface-200 p-1 font-bold text-xs rounded transition" title="ปิดการแจ้งเตือนนี้">✕</button>
  `;
}

// Auto-check on load if user is logged in
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', checkSystemAlerts);
} else {
  setTimeout(checkSystemAlerts, 1000);
}