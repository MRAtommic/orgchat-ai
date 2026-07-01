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