// ─── Organization admin: Department usage dashboard / Department access / Approvals / Rich menus ───
// ทุกค่าที่มาจากเซิร์ฟเวอร์ผ่าน esc() ก่อนใส่ HTML และใช้ data-attribute แทน inline handler
(function () {
  const esc = (t) => (window.escapeHtml ? window.escapeHtml(t == null ? '' : String(t)) : String(t == null ? '' : t).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
  const card = 'bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-800 rounded-2xl p-5 shadow-sm';
  const btn = 'px-3.5 py-2 rounded-xl text-xs font-bold transition-all active:scale-[0.98]';
  const btnPrimary = btn + ' bg-brand-600 hover:bg-brand-700 text-white';
  const btnGhost = btn + ' border border-surface-200 dark:border-surface-700 text-surface-700 dark:text-surface-200 hover:bg-surface-100 dark:hover:bg-surface-800';
  const inputCls = 'px-3 py-2 bg-surface-50 dark:bg-surface-950 border border-surface-200 dark:border-surface-800 rounded-xl text-xs dark:text-white outline-none focus:ring-2 focus:ring-brand-500';
  const toast = (m, t) => (window.showToast ? window.showToast(m, t || 'info') : alert(m));
  const $id = (i) => document.getElementById(i);

  async function api(url, opts) {
    const res = await fetch(url, opts);
    let data = {};
    try { data = await res.json(); } catch (e) { /* not json */ }
    return { res, data };
  }
  const post = (url, body) => api(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) });
  const fail = (box, data) => { box.innerHTML = `<div class="${card} text-xs text-rose-500 font-semibold">${esc(data.error || 'โหลดข้อมูลไม่สำเร็จ (ต้องเป็น Admin องค์กร)')}</div>`; };

  // ───────── แดชบอร์ดการใช้งานต่อแผนก ─────────
  let usageDays = 30, usageMinutes = 5;
  window.loadOrgUsage = async function () {
    const box = $id('orgTabContent-usage');
    if (!box) return;
    box.innerHTML = `<div class="text-center py-10 text-xs font-semibold text-surface-400">กำลังโหลดแดชบอร์ด...</div>`;
    const { res, data } = await api(`/api/org/usage-dashboard?days=${usageDays}&minutes=${usageMinutes}`);
    if (!res.ok || !data.ok) return fail(box, data);
    const t = data.totals, ds = data.departments;
    const maxQ = Math.max(1, ...ds.map(d => d.questions));
    const stat = (label, val, sub) => `<div class="${card}"><div class="text-[10px] font-bold uppercase tracking-widest text-surface-400">${label}</div><div class="text-2xl font-black mt-1 text-surface-900 dark:text-white">${val}</div><div class="text-[11px] text-surface-500 mt-0.5">${sub || ''}</div></div>`;
    box.innerHTML = `
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-xs font-bold text-surface-500">ช่วงเวลา</span>
        <select id="usageDays" class="${inputCls}">${[7, 30, 90, 365].map(d => `<option value="${d}" ${d === data.days ? 'selected' : ''}>${d} วันล่าสุด</option>`).join('')}</select>
        <span class="text-xs font-bold text-surface-500 ml-2">ประหยัดเวลาต่อคำตอบ</span>
        <input id="usageMinutes" type="number" min="1" max="120" value="${data.minutes_per_answer}" class="${inputCls} w-20"> <span class="text-xs text-surface-500">นาที</span>
        <button id="usageApply" class="${btnGhost}">คำนวณใหม่</button>
      </div>
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
        ${stat('คำถามทั้งหมด', t.questions, `จากผู้ใช้ ${t.active_users} คน`)}
        ${stat('คำตอบที่มีแหล่งอ้างอิง', t.answered_with_sources, t.questions ? Math.round(100 * t.answered_with_sources / t.questions) + '% ของคำถาม' : '-')}
        ${stat('เวลาที่ประหยัดได้ (ประมาณ)', `${t.hours_saved}<span class="text-sm font-bold text-surface-400"> ชม.</span>`, `คิดที่ ${data.minutes_per_answer} นาที/คำตอบ`)}
        ${stat('แผนกที่ใช้งาน', ds.length, '')}
      </div>
      <div class="${card}">
        <div class="text-sm font-black mb-3 dark:text-white">การใช้งานแยกตามแผนก</div>
        ${ds.length ? ds.map(d => `
          <div class="py-3 border-b border-surface-100 dark:border-surface-800 last:border-0">
            <div class="flex items-center justify-between gap-2 text-xs">
              <b class="dark:text-white">${esc(d.department)}</b>
              <span class="text-surface-500">${d.questions} คำถาม • ${d.active_users} คน • ประหยัด ${d.hours_saved} ชม. • 👍 ${d.thumbs_up} 👎 ${d.thumbs_down}${d.no_source_answers ? ` • <span class="text-amber-600 font-bold">ตอบโดยไม่มีที่มา ${d.no_source_answers}</span>` : ''}</span>
            </div>
            <div class="h-2 mt-1.5 bg-surface-100 dark:bg-surface-800 rounded-full overflow-hidden"><div class="h-full bg-brand-500 rounded-full" style="width:${Math.round(100 * d.questions / maxQ)}%"></div></div>
            <div class="grid md:grid-cols-2 gap-3 mt-2 text-[11px]">
              <div><div class="font-bold text-surface-400 uppercase tracking-widest text-[9px] mb-0.5">ถามบ่อย</div>${d.top_questions.length ? d.top_questions.map(q => `<div class="truncate dark:text-surface-300">• ${esc(q.text)} <b>×${q.count}</b></div>`).join('') : '<span class="text-surface-400">-</span>'}</div>
              <div><div class="font-bold text-surface-400 uppercase tracking-widest text-[9px] mb-0.5">เอกสารที่ถูกใช้ตอบบ่อย</div>${d.top_sources.length ? d.top_sources.map(s => `<div class="truncate dark:text-surface-300">• ${esc(s.name)} <b>×${s.count}</b></div>`).join('') : '<span class="text-surface-400">-</span>'}</div>
            </div>
          </div>`).join('') : '<div class="text-xs text-surface-400 py-4">ยังไม่มีข้อมูลการใช้งานในช่วงเวลานี้</div>'}
      </div>
      <div class="text-[11px] text-surface-500">ℹ️ ${esc(data.note)} • แผนกอ้างอิงจากโปรไฟล์สมาชิก (ถ้ายังไม่กรอกจะรวมเป็น "ไม่ระบุแผนก")</div>`;
    $id('usageApply').onclick = () => {
      usageDays = parseInt($id('usageDays').value, 10) || 30;
      usageMinutes = Math.max(1, Math.min(120, parseInt($id('usageMinutes').value, 10) || 5));
      window.loadOrgUsage();
    };
  };

  // ───────── สิทธิ์ตามแผนก + คำขออนุมัติ + Rich Menu ─────────
  window.loadOrgAccess = async function () {
    const box = $id('orgTabContent-access');
    if (!box) return;
    box.innerHTML = `<div class="text-center py-10 text-xs font-semibold text-surface-400">กำลังโหลด...</div>`;
    const [cats, apps, menus] = await Promise.all([
      api('/api/org/access/categories'), api('/api/org/approvals'), api('/api/org/line/richmenus')]);
    if (!cats.res.ok || !cats.data.ok) return fail(box, cats.data);
    const depts = cats.data.departments || [];
    const stLabel = { pending: ['รอพิจารณา', 'text-amber-600'], approved: ['อนุมัติ', 'text-emerald-600'], rejected: ['ปฏิเสธ', 'text-rose-600'] };
    const reqs = (apps.data && apps.data.requests) || [];
    const mids = (menus.data && menus.data.menus) || {};
    box.innerHTML = `
      <div class="${card}">
        <div class="text-sm font-black dark:text-white">สิทธิ์เอกสารตามแผนก</div>
        <div class="text-[11px] text-surface-500 mb-3">เลือกแผนกที่ <b>ได้รับอนุญาต</b> ให้ AI ค้นและตอบจากหมวดนี้ — ถ้าไม่เลือกเลย = ทุกคนที่มีสิทธิ์ตามปกติ • Admin องค์กรเห็นทุกหมวดเสมอ • มีผลทั้งเว็บและ LINE</div>
        ${depts.length ? '' : '<div class="text-xs text-amber-600 font-semibold mb-2">ยังไม่มีแผนกในองค์กร — สร้างแผนกที่แท็บ "แผนก" ก่อน</div>'}
        ${cats.data.categories.length ? cats.data.categories.map(c => `
          <div class="py-2.5 border-b border-surface-100 dark:border-surface-800 last:border-0" data-cat="${c.id}">
            <div class="text-xs font-bold dark:text-white mb-1.5">📁 ${esc(c.name)} ${c.departments.length ? '<span class="text-brand-600 font-black">🔒 จำกัดแผนก</span>' : '<span class="text-surface-400 font-semibold">เปิดตามสิทธิ์ปกติ</span>'}</div>
            <div class="flex flex-wrap gap-2 items-center">
              ${depts.map(d => `<label class="flex items-center gap-1.5 text-[11px] px-2 py-1 rounded-lg border border-surface-200 dark:border-surface-700 dark:text-surface-200 cursor-pointer"><input type="checkbox" data-dept="${esc(d)}" ${c.departments.some(x => x.toLowerCase() === String(d).toLowerCase()) ? 'checked' : ''}> ${esc(d)}</label>`).join('')}
              <button class="${btnPrimary}" data-save-cat="${c.id}">บันทึก</button>
            </div>
          </div>`).join('') : '<div class="text-xs text-surface-400">ยังไม่มีหมวดความรู้ — สร้างที่แท็บ "หมวดหมู่ & กฎ AI"</div>'}
      </div>

      <div class="${card}">
        <div class="flex items-center justify-between mb-2"><div class="text-sm font-black dark:text-white">คำขอเบิกจ่าย / อนุมัติ</div>
          <button class="${btnGhost}" data-refresh-approvals>รีเฟรช</button></div>
        <div class="text-[11px] text-surface-500 mb-3">พนักงานพิมพ์ใน LINE: <code>เบิก 500 ค่าเดินทาง</code> → ส่งการ์ดให้หัวหน้ากดอนุมัติ → ผลถูกบันทึกลงชีต "อนุมัติคำขอ (จากระบบ)"</div>
        ${reqs.length ? `<div class="overflow-x-auto"><table class="w-full text-xs"><thead><tr class="text-left text-surface-400"><th class="py-1">#</th><th>ผู้ขอ</th><th>รายการ</th><th>จำนวน</th><th>สถานะ</th><th>ผู้อนุมัติ</th><th>ชีต</th><th></th></tr></thead><tbody>
          ${reqs.map(r => `<tr class="border-t border-surface-50 dark:border-surface-800/60"><td class="py-1.5">${r.id}</td><td>${esc(r.requester)}</td><td>${esc(r.title)}</td><td>${Number(r.amount).toLocaleString()}</td>
            <td class="font-bold ${(stLabel[r.status] || ['', ''])[1]}">${esc((stLabel[r.status] || [r.status])[0])}</td><td>${esc(r.approver || '-')}</td><td>${r.sheet_logged ? '✅' : '-'}</td>
            <td class="whitespace-nowrap">${r.status === 'pending' ? `<button class="text-emerald-600 font-bold mr-2" data-decide="approve" data-id="${r.id}">อนุมัติ</button><button class="text-rose-600 font-bold" data-decide="reject" data-id="${r.id}">ปฏิเสธ</button>` : ''}</td></tr>`).join('')}
        </tbody></table></div>` : '<div class="text-xs text-surface-400">ยังไม่มีคำขอ</div>'}
      </div>

      <div class="${card}">
        <div class="text-sm font-black dark:text-white">Rich Menu ตามบทบาท (LINE)</div>
        <div class="text-[11px] text-surface-500 mb-3">สร้างเมนู 3 แบบ: พนักงาน / หัวหน้า / ผู้ดูแล — ผู้ใช้จะได้เมนูตามบทบาทเมื่อทักบอทครั้งถัดไป • การกดปุ่มด้านล่างจะแทนที่เมนูเริ่มต้นของ LINE OA นี้</div>
        <div class="flex flex-wrap items-center gap-2">
          <button class="${btnPrimary}" data-richmenu-setup>${Object.keys(mids).length ? 'สร้างเมนูใหม่' : 'สร้างเมนูครั้งแรก'}</button>
          ${['employee', 'manager', 'admin'].map(r => `<span class="text-[11px] px-2 py-1 rounded-lg ${mids[r] ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300' : 'bg-surface-100 text-surface-400 dark:bg-surface-800'}">${{ employee: 'พนักงาน', manager: 'หัวหน้า', admin: 'ผู้ดูแล' }[r]}: ${mids[r] ? 'พร้อม' : 'ยังไม่สร้าง'}</span>`).join('')}
        </div>
      </div>`;

    box.querySelectorAll('[data-save-cat]').forEach(b => b.addEventListener('click', async () => {
      const row = b.closest('[data-cat]');
      const sel = [...row.querySelectorAll('input[data-dept]:checked')].map(i => i.getAttribute('data-dept'));
      const { res, data } = await post(`/api/org/access/categories/${b.getAttribute('data-save-cat')}/departments`, { departments: sel });
      toast(res.ok && data.ok ? (sel.length ? `จำกัดเฉพาะแผนก: ${sel.join(', ')}` : 'เปิดตามสิทธิ์ปกติแล้ว') : (data.error || 'บันทึกไม่สำเร็จ'), res.ok ? 'success' : 'error');
      if (res.ok) window.loadOrgAccess();
    }));
    box.querySelectorAll('[data-decide]').forEach(b => b.addEventListener('click', async () => {
      const { res, data } = await post(`/api/org/approvals/${b.getAttribute('data-id')}/decide`, { decision: b.getAttribute('data-decide') });
      toast(res.ok ? 'บันทึกผลแล้ว' : (data.error || 'ไม่สำเร็จ'), res.ok ? 'success' : 'error');
      window.loadOrgAccess();
    }));
    const rf = box.querySelector('[data-refresh-approvals]');
    if (rf) rf.addEventListener('click', () => window.loadOrgAccess());
    const rm = box.querySelector('[data-richmenu-setup]');
    if (rm) rm.addEventListener('click', async () => {
      if (!confirm('สร้าง Rich Menu ใหม่และตั้งเป็นเมนูเริ่มต้นของ LINE OA นี้ ใช่หรือไม่?')) return;
      rm.disabled = true; rm.textContent = 'กำลังสร้าง...';
      const { res, data } = await post('/api/org/line/richmenus/setup', {});
      toast(res.ok && data.ok ? 'สร้างเมนูครบทั้ง 3 บทบาทแล้ว' : ((data.errors || []).join(' • ') || data.error || 'สร้างไม่สำเร็จ'), res.ok && data.ok ? 'success' : 'error');
      window.loadOrgAccess();
    });
  };
})();
