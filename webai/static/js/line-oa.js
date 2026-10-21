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
