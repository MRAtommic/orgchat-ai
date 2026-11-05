// ─── LINE Groups Management UI ───
                // LINE Group mapping handlers
                async function refreshGroupMappings() {
                    const listBody = document.getElementById('lineGroupMappingsList');
                    if (!listBody) return;
                    
                    listBody.innerHTML = `
                      <tr>
                        <td colspan="4" class="p-8 text-center text-surface-450 italic">
                          <i data-lucide="loader-2" class="w-5 h-5 animate-spin mx-auto mb-2 opacity-50 text-[#00B900]"></i>
                          กำลังดึงข้อมูลแชทกลุ่ม...
                        </td>
                      </tr>
                    `;
                    
                    try {
                        const res = await fetch('/api/line/groups');
                        const data = await res.json();
                        
                        if (!data.ok) {
                            listBody.innerHTML = `
                              <tr>
                                <td colspan="4" class="p-8 text-center text-red-500 font-bold">
                                  ❌ ดึงข้อมูลล้มเหลว: ${data.error || 'Unknown error'}
                                </td>
                              </tr>
                            `;
                            return;
                        }
                        
                        const mappings = data.mappings || [];
                        if (mappings.length === 0) {
                            listBody.innerHTML = `
                              <tr>
                                <td colspan="4" class="p-12 text-center text-surface-400 font-medium">
                                  <i data-lucide="users" class="w-12 h-12 mx-auto mb-3 opacity-20 text-[#00B900]"></i>
                                  ยังไม่มีการเชื่อมต่อแชทกลุ่ม LINE เลยค่ะพี่ 
                                  <p class="text-[10px] text-surface-400 mt-1 uppercase font-black">พิมพ์ "รหัสกลุ่ม" ในกลุ่มแล้วนำมาผูกเพื่อเริ่มใช้งานได้เลยค่ะ!</p>
                                </td>
                              </tr>
                            `;
                            if (window.lucide) window.lucide.createIcons();
                            return;
                        }
                        
                        listBody.innerHTML = mappings.map(m => `
                          <tr class="hover:bg-surface-50/50 dark:hover:bg-surface-800/30 transition-all border-b border-surface-100/50 dark:border-surface-800/50">
                            <td class="p-3 pl-4 font-bold text-surface-900 dark:text-white">${escapeHtml(m.group_name || 'แชทกลุ่ม LINE')}</td>
                            <td class="p-3 font-mono text-[10px] select-all">${escapeHtml(m.group_id)}</td>
                            <td class="p-3">
                              ${m.default_folder_id ? `
                                <span class="px-2.5 py-1 bg-[#00B900]/10 text-[#00B900] text-[10px] font-bold rounded-lg border border-[#00B900]/20 flex items-center gap-1.5 w-max">
                                  <i data-lucide="folder" class="w-3.5 h-3.5"></i>
                                  ${escapeHtml(m.default_folder_name || 'โฟลเดอร์เริ่มต้น')}
                                </span>
                              ` : `
                                <span class="px-2.5 py-1 bg-surface-100 dark:bg-surface-800 text-surface-450 text-[10px] font-bold rounded-lg border border-surface-200 dark:border-surface-700 flex items-center gap-1.5 w-max">
                                  <i data-lucide="help-circle" class="w-3.5 h-3.5"></i>
                                  ถามผ่าน LINE ทุกครั้ง
                                </span>
                              `}
                            </td>
                            <td class="p-3 text-center">
                              <button onclick="unbindGroup('${m.group_id}')" class="p-2 bg-rose-50 hover:bg-rose-100 text-rose-600 dark:bg-rose-900/10 dark:hover:bg-rose-900/20 rounded-lg border border-rose-100 dark:border-rose-900/30 transition-all hover:scale-105 active:scale-95" title="ยกเลิกเชื่อมต่อ">
                                <i data-lucide="trash-2" class="w-4 h-4"></i>
                              </button>
                            </td>
                          </tr>
                        `).join('');
                        
                        if (window.lucide) window.lucide.createIcons();
                    } catch (err) {
                        listBody.innerHTML = `
                          <tr>
                            <td colspan="4" class="p-8 text-center text-red-500 font-bold">
                              ❌ เกิดข้อผิดพลาดในการดึงข้อมูล: ${err.message}
                            </td>
                          </tr>
                        `;
                    }
                }

                async function loadGoogleFoldersForGroup() {
                    const select = document.getElementById('lineGroupBindFolder');
                    if (!select) return;
                    
                    try {
                        const res = await fetch('/api/google/folders');
                        const data = await res.json();
                        
                        if (data.ok) {
                            const folders = data.folders || [];
                            select.innerHTML = '<option value="">-- แสดงปุ่มเลือกโฟลเดอร์บน LINE --</option>' + 
                              folders.map(f => `<option value="${f.id}">${escapeHtml(f.name)}</option>`).join('');
                        } else {
                            select.innerHTML = '<option value="" class="text-rose-500" style="color: #ef4444;">❌ Google Drive ยังไม่ได้เชื่อมต่อ (กรุณาเชื่อมต่อก่อน)</option>';
                        }
                    } catch (err) {
                        console.error("Failed to load Google Drive folders for group mapping dropdown:", err);
                        select.innerHTML = '<option value="" class="text-rose-500" style="color: #ef4444;">❌ Google Drive ยังไม่ได้เชื่อมต่อ (กรุณาเชื่อมต่อก่อน)</option>';
                    }
                }

                async function submitGroupBinding() {
                    const groupIdInput = document.getElementById('lineGroupBindId');
                    const groupNameInput = document.getElementById('lineGroupBindName');
                    const folderSelect = document.getElementById('lineGroupBindFolder');
                    const btn = document.getElementById('lineGroupBindBtn');
                    
                    if (!groupIdInput || !groupNameInput || !folderSelect || !btn) return;
                    
                    const group_id = groupIdInput.value.trim();
                    const group_name = groupNameInput.value.trim();
                    
                    if (!group_id) {
                        toast('กรุณากรอก Group ID ของ LINE แชทกลุ่มด้วยนะคะพี่ 😊', 'warning');
                        return;
                    }
                    
                    const lineIdPattern = /^[CRU][a-fA-F0-9]{32}$/;
                    if (!lineIdPattern.test(group_id)) {
                        toast('รูปแบบ Group ID ไม่ถูกต้อง (ต้องขึ้นต้นด้วย C, R หรือ U และมีความยาว 33 ตัวอักษรค่ะ)', 'warning');
                        return;
                    }
                    
                    const default_folder_id = folderSelect.value;
                    const default_folder_name = default_folder_id ? folderSelect.options[folderSelect.selectedIndex].text : '';
                    
                    btn.disabled = true;
                    const originalText = btn.innerHTML;
                    btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> กำลังบันทึกข้อมูล...`;
                    if (window.lucide) window.lucide.createIcons();
                    
                    try {
                        const res = await fetch('/api/line/groups/bind', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                group_id,
                                group_name,
                                default_folder_id,
                                default_folder_name
                            })
                        });
                        
                        const data = await res.json();
                        if (data.ok) {
                            toast('เชื่อมโยงแชทกลุ่ม LINE สำเร็จเรียบร้อยค่ะ ✨💖', 'success');
                            groupIdInput.value = '';
                            groupNameInput.value = '';
                            folderSelect.value = '';
                            refreshGroupMappings();
                        } else {
                            toast('ผูกบัญชีแชทกลุ่มไม่สำเร็จค่ะ: ' + (data.error || 'Unknown error'), 'error');
                        }
                    } catch (err) {
                        toast('เกิดข้อผิดพลาดในการบันทึกข้อมูล: ' + err.message, 'error');
                    } finally {
                        btn.disabled = false;
                        btn.innerHTML = originalText;
                        if (window.lucide) window.lucide.createIcons();
                    }
                }

                async function unbindGroup(groupId) {
                    if (!confirm('พี่แน่ใจนะคะว่าต้องการยกเลิกการผูกแชทกลุ่ม LINE นี้?')) return;
                    
                    try {
                        const res = await fetch(`/api/line/groups/unbind/${groupId}`, {
                            method: 'DELETE'
                        });
                        const data = await res.json();
                        
                        if (data.ok) {
                            toast('ยกเลิกการผูกแชทกลุ่มเรียบร้อยแล้วค่ะ ✨', 'success');
                            refreshGroupMappings();
                        } else {
                            toast('ยกเลิกไม่สำเร็จค่ะ: ' + (data.error || 'Unknown error'), 'error');
                        }
                    } catch (err) {
                        toast('เกิดข้อผิดพลาดในการทำงาน: ' + err.message, 'error');
                    }
                }

                async function toggleGroupBot(groupId, currentBotOn) {
                    try {
                        const newStatus = currentBotOn ? 0 : 1;
                        const res = await fetch(`/api/org/line/groups/${groupId}/toggle-bot`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ bot_enabled: newStatus })
                        });
                        const data = await res.json();
                        if (data.ok) {
                            toast(newStatus ? 'เปิดการทำงานของ AI ในกลุ่มนี้แล้วค่ะ 🤖✨' : 'ปิดการทำงานของ AI ในกลุ่มนี้ชั่วคราวแล้วค่ะ ⏸️', 'success');
                            refreshGroupMappings();
                        } else {
                            toast('สลับสถานะไม่สำเร็จ: ' + (data.error || 'Unknown error'), 'error');
                        }
                    } catch (err) {
                        toast('เกิดข้อผิดพลาด: ' + err.message, 'error');
                    }
                }

                async function openEditLineGroupModal(groupId) {
                    const m = _cachedGroupMappings.find(g => g.group_id === groupId);
                    if (!m) {
                        toast('ไม่พบข้อมูลกลุ่มค่ะ', 'error');
                        return;
                    }
                    
                    document.getElementById('editGroupModalId').value = m.group_id;
                    document.getElementById('editGroupModalIdDisplay').textContent = m.group_id;
                    document.getElementById('editGroupModalName').value = m.group_name || m.line_real_name || '';
                    document.getElementById('editGroupModalBotEnabled').checked = m.bot_enabled !== 0;

                    // Load folders into modal dropdown
                    const folderSelect = document.getElementById('editGroupModalFolder');
                    folderSelect.innerHTML = '<option value="">-- แสดงปุ่มเลือกโฟลเดอร์บน LINE --</option>';
                    try {
                        const res = await fetch('/api/google/folders');
                        const data = await res.json();
                        if (data.ok && data.folders) {
                            folderSelect.innerHTML += data.folders.map(f => 
                                `<option value="${f.id}" ${f.id === m.default_folder_id ? 'selected' : ''}>${escapeHtml(f.name)}</option>`
                            ).join('');
                        }
                    } catch (err) {
                        console.error(err);
                    }

                    document.getElementById('editLineGroupModal').classList.remove('hidden');
                }

                function closeEditLineGroupModal() {
                    document.getElementById('editLineGroupModal').classList.add('hidden');
                }

                async function saveLineGroupSettings() {
                    const groupId = document.getElementById('editGroupModalId').value;
                    const groupName = document.getElementById('editGroupModalName').value.trim();
                    const folderSelect = document.getElementById('editGroupModalFolder');
                    const default_folder_id = folderSelect.value;
                    const default_folder_name = default_folder_id ? folderSelect.options[folderSelect.selectedIndex].text : '';
                    const bot_enabled = document.getElementById('editGroupModalBotEnabled').checked ? 1 : 0;

                    const btn = document.getElementById('saveEditGroupBtn');
                    btn.disabled = true;
                    btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> กำลังบันทึก...`;
                    if (window.lucide) window.lucide.createIcons();

                    try {
                        const res = await fetch(`/api/line/groups/${groupId}/settings`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                group_name: groupName,
                                default_folder_id: default_folder_id,
                                default_folder_name: default_folder_name,
                                bot_enabled: bot_enabled
                            })
                        });
                        const data = await res.json();
                        if (data.ok) {
                            toast('ปรับปรุงตั้งค่ากลุ่ม LINE เรียบร้อยแล้วค่ะ ✨💖', 'success');
                            closeEditLineGroupModal();
                            refreshGroupMappings();
                        } else {
                            toast('บันทึกไม่สำเร็จ: ' + (data.error || 'Unknown error'), 'error');
                        }
                    } catch (err) {
                        toast('เกิดข้อผิดพลาด: ' + err.message, 'error');
                    } finally {
                        btn.disabled = false;
                        btn.innerHTML = `บันทึกการตั้งค่า`;
                    }
                }

                // Escape HTML utility
                function escapeHtml(text) {
                    if (!text) return '';
                    return text
                        .replace(/&/g, "&amp;")
                        .replace(/</g, "&lt;")
                        .replace(/>/g, "&gt;")
                        .replace(/"/g, "&quot;")
                        .replace(/'/g, "&#039;");
                }

                // Intercept showView once line-manager or line-groups is loaded
                if (typeof window.originalShowView === 'undefined') {
                    window.originalShowView = window.showView;
                    window.showView = function(viewId) {
                        if (window.originalShowView) window.originalShowView(viewId);
                        if (viewId === 'line-manager' || viewId === 'line-groups') {
                            if (typeof refreshGroupMappings === 'function') refreshGroupMappings();
                            if (typeof loadGoogleFoldersForGroupRegister === 'function') loadGoogleFoldersForGroupRegister();
                            if (typeof loadFlexSettings === 'function') loadFlexSettings();
                        }
                    };
                }

// ─── LINE Group Folder Selection ───
// ── LINE Groups ──────────────────────────────────────
let _lgLoaded = false;
let _orgDriveFoldersCache = [];

async function loadGoogleFoldersForGroupRegister() {
  const select = document.getElementById('lg-group-folder');
  if (!select) return;
  try {
    const res = await fetch('/api/google/folders');
    const data = await res.json();
    if (data.ok && Array.isArray(data.folders)) {
      _orgDriveFoldersCache = data.folders;
      select.innerHTML = '<option value="">-- ถามเลือกโฟลเดอร์บน LINE ทุกครั้ง --</option>';
      data.folders.forEach(f => {
        const opt = document.createElement('option');
        opt.value = f.id;
        opt.textContent = `📁 ${f.name}`;
        select.appendChild(opt);
      });
    }
  } catch (e) {
    console.warn('Cannot load Google Drive folders for group select:', e);
  }
}

async function loadLineGroups(force = false) {
  if (_lgLoaded && !force) return;
  document.getElementById('lg-loading').classList.remove('hidden');
  document.getElementById('lg-empty').classList.add('hidden');
  document.getElementById('lg-list').classList.add('hidden');
  try {
    const res = await fetch('/api/org/line/groups');
    const data = await res.json();
    document.getElementById('lg-loading').classList.add('hidden');
    const list = document.getElementById('lg-list');
    if (!data.ok || !data.groups || !data.groups.length) {
      document.getElementById('lg-empty').classList.remove('hidden');
    } else {
      list.classList.remove('hidden');
      list.innerHTML = '';
      data.groups.forEach(g => {
        const li = document.createElement('li');
        li.className = 'flex items-center gap-3 px-6 py-4 hover:bg-surface-50 dark:hover:bg-surface-800/50';
        
        // รูปกลุ่ม LINE จริง หรือ placeholder สีเขียว
        const picHtml = g.line_picture_url
          ? `<img src="${g.line_picture_url}" class="w-11 h-11 rounded-xl object-cover flex-shrink-0 border border-surface-200 dark:border-surface-700">`
          : `<div class="w-11 h-11 rounded-xl bg-[#00B900] flex items-center justify-center flex-shrink-0"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="w-6 h-6 fill-white"><path d="M19.365 9.863c.349 0 .63.285.63.631 0 .345-.281.63-.63.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.281.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.281.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/></svg></div>`;
        
        const displayName = g.line_real_name || g.group_name || '(ไม่มีชื่อ)';
        const nameSource = g.line_real_name
          ? `<span class="ml-1 px-1.5 py-0.5 text-[8px] font-black uppercase tracking-wider bg-[#00B900]/15 text-[#00B900] rounded-full">LINE</span>`
          : (g.group_name ? `<span class="ml-1 px-1.5 py-0.5 text-[8px] font-black uppercase tracking-wider bg-surface-100 dark:bg-surface-700 text-surface-400 rounded-full">ตั้งเอง</span>` : '');
        
        const folderTag = g.default_folder_name
          ? `<span class="inline-flex items-center gap-1 text-[10px] text-indigo-600 dark:text-indigo-400 font-semibold bg-indigo-50 dark:bg-indigo-950/40 px-2 py-0.5 rounded-md border border-indigo-200 dark:border-indigo-800/50 mt-1"><i data-lucide="folder" class="w-3 h-3"></i> ${g.default_folder_name}</span>`
          : `<span class="text-[10px] text-surface-400 mt-1 block">ถามโฟลเดอร์บน LINE ทุกครั้ง</span>`;

        const botEnabled = g.bot_enabled !== undefined ? g.bot_enabled : 1;
        const toggleHtml = `
          <div class="flex items-center gap-2 mr-2">
            <span class="text-[10px] font-bold text-surface-500 uppercase tracking-widest hidden sm:inline">บอท AI</span>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" value="" class="sr-only peer" ${botEnabled ? 'checked' : ''} onchange="toggleLineGroupBot('${g.group_id}', this.checked)">
              <div class="w-9 h-5 bg-surface-200 peer-focus:outline-none rounded-full peer dark:bg-surface-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-surface-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all dark:border-surface-600 peer-checked:bg-emerald-500"></div>
            </label>
          </div>
        `;
        
        li.innerHTML = `
          ${picHtml}
          <div class="flex-1 min-w-0">
            <p class="font-bold text-surface-800 dark:text-surface-100 text-sm flex items-center gap-1 flex-wrap">
              ${displayName}${nameSource}
            </p>
            ${g.line_real_name && g.group_name && g.line_real_name !== g.group_name
              ? `<p class="text-[10px] text-surface-400 mt-0.5">ชื่อที่ตั้งเอง: ${g.group_name}</p>`
              : ''}
            <p class="text-[10px] font-mono text-surface-400 mt-0.5 truncate">${g.group_id}</p>
            ${folderTag}
          </div>
          ${toggleHtml}
          <button onclick="openEditLineGroupModal('${g.group_id}', '${(g.group_name || '').replace(/'/g, "\\'")}', '${g.default_folder_id || ''}', ${botEnabled})" class="text-xs text-surface-500 hover:text-brand-600 font-semibold px-2.5 py-1.5 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors flex items-center gap-1">
            <i data-lucide="settings" class="w-3.5 h-3.5"></i> ตั้งค่า
          </button>
          <button onclick="deleteLineGroup('${g.group_id}')" class="flex-shrink-0 text-xs text-red-400 hover:text-red-600 font-semibold px-2.5 py-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">ลบ</button>
        `;
        list.appendChild(li);
      });
      if (window.lucide) window.lucide.createIcons();
    }
    _lgLoaded = true;
  } catch (e) {
    document.getElementById('lg-loading').classList.add('hidden');
    document.getElementById('lg-empty').classList.remove('hidden');
  }
}

async function registerLineGroup() {
  const groupId = document.getElementById('lg-group-id').value.trim();
  const groupName = document.getElementById('lg-group-name').value.trim();
  const defaultFolderId = document.getElementById('lg-group-folder').value;
  if (!groupId) { showLineGroupToast('กรุณาใส่ Group ID', true); return; }
  
  const lineIdPattern = /^[CRU][a-fA-F0-9]{32}$/;
  if (!lineIdPattern.test(groupId)) {
    showLineGroupToast('รูปแบบ Group ID ไม่ถูกต้อง (ต้องขึ้นต้นด้วย C, R หรือ U และมีความยาว 33 ตัวอักษรค่ะ)', true);
    return;
  }
  const res = await fetch('/api/org/line/register-group', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ group_id: groupId, group_name: groupName, default_folder_id: defaultFolderId }),
  });
  const data = await res.json();
  if (data.ok) {
    showLineGroupToast('เพิ่มกลุ่มสำเร็จ ✅');
    document.getElementById('lg-group-id').value = '';
    document.getElementById('lg-group-name').value = '';
    loadLineGroups(true);
  } else {
    showLineGroupToast(data.error || 'เกิดข้อผิดพลาด', true);
  }
}

async function toggleLineGroupBot(groupId, isEnabled) {
  try {
    const res = await fetch(`/api/org/line/groups/${groupId}/toggle-bot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bot_enabled: isEnabled ? 1 : 0 })
    });
    const data = await res.json();
    if (data.ok) {
      showLineGroupToast(isEnabled ? 'เปิดใช้งานบอทแล้ว ✅' : 'ปิดการใช้งานบอทแล้ว ❌');
    } else {
      showLineGroupToast(data.error || 'เกิดข้อผิดพลาด', true);
      loadLineGroups(true); // Revert UI
    }
  } catch (e) {
    showLineGroupToast('เกิดข้อผิดพลาดในการเชื่อมต่อ', true);
    loadLineGroups(true); // Revert UI
  }
}

async function syncLineGroupNames() {
  const btn = document.getElementById('lg-sync-btn');
  if (btn) { btn.disabled = true; btn.innerHTML = '<i data-lucide="loader-2" class="w-3 h-3 animate-spin inline mr-1"></i>กำลังดึง...'; }
  try {
    const res = await fetch('/api/org/line/sync-group-names', { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      const ok = data.results.filter(r => r.ok).length;
      const fail = data.results.filter(r => !r.ok);
      showLineGroupToast(`ดึงชื่อสำเร็จ ${ok} กลุ่ม` + (fail.length ? ` · ${fail.length} กลุ่มไม่พบ` : ''));
      _lgLoaded = false;
      await loadLineGroups(true);
    } else {
      showLineGroupToast(data.error || 'เกิดข้อผิดพลาด', true);
    }
  } catch (e) {
    showLineGroupToast('เชื่อมต่อไม่ได้', true);
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="refresh-cw" class="w-3 h-3 inline mr-1"></i>ดึงชื่อจาก LINE'; if(window.lucide) window.lucide.createIcons(); }
  }
}

async function deleteLineGroup(groupId) {
  if (!confirm('ลบกลุ่ม ' + groupId + ' ออกจากระบบ?')) return;
  const res = await fetch('/api/org/line/groups/' + groupId, { method: 'DELETE' });
  const data = await res.json();
  if (data.ok) { showLineGroupToast('ลบกลุ่มแล้ว'); loadLineGroups(true); }
  else showLineGroupToast('เกิดข้อผิดพลาด', true);
}

function openEditLineGroupModal(groupId, groupName, defaultFolderId, botEnabled) {
  document.getElementById('edit-lg-group-id').value = groupId;
  document.getElementById('edit-lg-group-name').value = groupName || '';
  
  const select = document.getElementById('edit-lg-group-folder');
  select.innerHTML = '<option value="">-- ถามเลือกโฟลเดอร์บน LINE ทุกครั้ง --</option>';
  _orgDriveFoldersCache.forEach(f => {
    const opt = document.createElement('option');
    opt.value = f.id;
    opt.textContent = `📁 ${f.name}`;
    if (f.id === defaultFolderId) opt.selected = true;
    select.appendChild(opt);
  });
  
  document.getElementById('edit-lg-bot-enabled').checked = !!botEnabled;
  document.getElementById('modal-edit-line-group').classList.remove('hidden');
}

function closeEditLineGroupModal() {
  document.getElementById('modal-edit-line-group').classList.add('hidden');
}

async function saveEditLineGroupSettings() {
  const groupId = document.getElementById('edit-lg-group-id').value;
  const groupName = document.getElementById('edit-lg-group-name').value.trim();
  const defaultFolderId = document.getElementById('edit-lg-group-folder').value;
  const botEnabled = document.getElementById('edit-lg-bot-enabled').checked ? 1 : 0;
  
  try {
    const res = await fetch('/api/org/line/groups/' + groupId, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        group_name: groupName,
        default_folder_id: defaultFolderId,
        bot_enabled: botEnabled
      })
    });
    const data = await res.json();
    if (data.ok) {
      showLineGroupToast('บันทึกการตั้งค่ากลุ่มเรียบร้อย ✅');
      closeEditLineGroupModal();
      loadLineGroups(true);
    } else {
      showLineGroupToast(data.error || 'เกิดข้อผิดพลาดในการบันทึก', true);
    }
  } catch (e) {
    showLineGroupToast('เกิดข้อผิดพลาดในการเชื่อมต่อ', true);
  }
}

function showLineGroupToast(msg, isError = false) {
  if (typeof toast === 'function') {
    toast(msg, isError ? 'error' : 'success');
  } else {
    alert(msg); // Fallback
  }
}

// ─── Sidebar Collapse Toggler ───────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const navSidebar = document.getElementById('navSidebar');
  const collapseBtn = document.getElementById('sidebarCollapseBtn');
  const collapseIcon = document.getElementById('collapseBtnIcon');

  if (navSidebar && collapseBtn && collapseIcon) {
    // 1. Load saved state
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isCollapsed) {
      navSidebar.classList.add('collapsed');
      collapseIcon.setAttribute('data-lucide', 'chevron-right');
      if (typeof initIcons === 'function') {
        setTimeout(initIcons, 100);
      }
    }

    // 2. Toggle on click
    collapseBtn.addEventListener('click', () => {
      const willCollapse = !navSidebar.classList.contains('collapsed');
      navSidebar.classList.toggle('collapsed', willCollapse);
      collapseIcon.setAttribute('data-lucide', willCollapse ? 'chevron-right' : 'chevron-left');
      localStorage.setItem('sidebarCollapsed', willCollapse);
      if (typeof initIcons === 'function') {
        initIcons();
      }
    });
  }
});
