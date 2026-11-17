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

  // ───────── ตั้งค่าเช็คชื่อเข้างาน (พิกัดสำนักงาน / รัศมี / เวลาเข้างาน) ─────────
  window.loadAttendanceSettingsCard = async function () {
    const host = $id('orgTabContent-attendance');
    if (!host) return;
    let card_ = $id('attSettingsCard');
    if (!card_) {
      card_ = document.createElement('div');
      card_.id = 'attSettingsCard';
      card_.className = card + ' mb-4';
      host.insertBefore(card_, host.firstChild);
    }
    const { res, data } = await api('/api/org/attendance/settings');
    if (!res.ok || !data.ok) { card_.innerHTML = ''; return; }
    const s = data.settings;
    card_.innerHTML = `
      <div class="flex flex-wrap items-center justify-between gap-2 mb-1">
        <div class="text-sm font-black dark:text-white">ตั้งค่าการเช็คชื่อขององค์กร</div>
        <span class="text-[11px] font-bold px-2 py-0.5 rounded-full ${s.configured ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300' : 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'}">${s.configured ? 'ตั้งพิกัดแล้ว' : 'ยังไม่ได้ตั้งพิกัด'}</span>
      </div>
      <div class="text-[11px] text-surface-500 mb-3">${s.configured ? 'พนักงานที่เช็คชื่อห่างจากจุดนี้เกินรัศมีจะถูกบันทึกว่า "นอกพื้นที่"' : 'ตอนนี้ระบบ <b>ไม่ตัดสินว่านอกพื้นที่</b> ทุกคนเช็คชื่อได้ตามปกติ — ตั้งพิกัดสำนักงานเพื่อเปิดการตรวจรัศมี'}</div>
      <div class="mb-3">
        <div class="flex flex-wrap gap-2 mb-2">
          <input id="attMapSearch" type="search" placeholder="ค้นหาชื่อสถานที่/บริษัท/ที่อยู่ แล้วกด Enter" class="${inputCls} flex-1 min-w-[200px]">
          <input id="attMapPaste" type="text" placeholder="หรือวางลิงก์ Google Maps / พิกัด เช่น 13.8196, 100.5143" class="${inputCls} flex-1 min-w-[200px]">
        </div>
        <div id="attCfgMap" class="w-full rounded-xl border border-surface-200 dark:border-surface-700 overflow-hidden" style="height:300px;background:#e5e7eb"></div>
        <div class="flex flex-wrap items-center justify-between gap-2 mt-1.5 text-[11px] text-surface-500">
          <span>👆 คลิกบนแผนที่เพื่อวางหมุด (ลากหมุดปรับได้) — วงกลมคือรัศมีที่ถือว่า "อยู่ในพื้นที่"</span>
          <a id="attMapGoogle" href="#" target="_blank" rel="noopener noreferrer" class="font-bold text-brand-600 hidden">ตรวจจุดนี้ใน Google Maps ↗</a>
        </div>
      </div>
      <div class="grid sm:grid-cols-2 gap-2.5">
        <label class="text-[11px] font-bold text-surface-500">ละติจูด<input id="attCfgLat" type="number" step="any" class="${inputCls} w-full mt-1" value="${s.office_lat == null ? '' : s.office_lat}" placeholder="เช่น 13.8196"></label>
        <label class="text-[11px] font-bold text-surface-500">ลองจิจูด<input id="attCfgLng" type="number" step="any" class="${inputCls} w-full mt-1" value="${s.office_lng == null ? '' : s.office_lng}" placeholder="เช่น 100.5143"></label>
        <label class="text-[11px] font-bold text-surface-500">รัศมีที่ถือว่าอยู่ในพื้นที่ (เมตร)<input id="attCfgRadius" type="number" min="20" max="20000" class="${inputCls} w-full mt-1" value="${Math.round(s.radius_m)}"></label>
        <label class="text-[11px] font-bold text-surface-500">เวลาเข้างาน (เกินจากนี้ = สาย)<input id="attCfgStart" type="time" class="${inputCls} w-full mt-1" value="${String(s.work_start_h).padStart(2, '0')}:${String(s.work_start_m).padStart(2, '0')}"></label>
      </div>
      <div class="flex flex-wrap items-center gap-2 mt-3">
        <button type="button" id="attCfgHere" class="${btnGhost}">📍 ใช้ตำแหน่งปัจจุบันของฉัน</button>
        <button type="button" id="attCfgSave" class="${btnPrimary}">บันทึก</button>
        <span class="text-[10px] text-surface-400">แนะนำรัศมี 100–300 ม. (GPS ในอาคารคลาดเคลื่อนได้หลายสิบเมตร)</span>
      </div>`;
    window._attInitMap(s);
    $id('attCfgHere').addEventListener('click', () => {
      if (!navigator.geolocation) { toast('เบราว์เซอร์ไม่รองรับ GPS', 'error'); return; }
      toast('กำลังดึงตำแหน่ง...', 'info');
      navigator.geolocation.getCurrentPosition((p) => {
        $id('attCfgLat').value = p.coords.latitude.toFixed(6);
        $id('attCfgLng').value = p.coords.longitude.toFixed(6);
        toast(`ได้ตำแหน่งแล้ว (ความแม่นยำ ±${Math.round(p.coords.accuracy)} ม.) — กดบันทึก`, 'success');
      }, () => toast('ดึงตำแหน่งไม่สำเร็จ — อนุญาตการเข้าถึงตำแหน่งในเบราว์เซอร์ก่อน', 'error'),
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 });
    });
    $id('attCfgSave').addEventListener('click', async () => {
      const body = { office_lat: $id('attCfgLat').value, office_lng: $id('attCfgLng').value, radius_m: $id('attCfgRadius').value, work_start: $id('attCfgStart').value };
      const r = await post('/api/org/attendance/settings', body);
      toast(r.res.ok && r.data.ok ? 'บันทึกการตั้งค่าเช็คชื่อแล้ว' : (r.data.error || 'บันทึกไม่สำเร็จ'), r.res.ok ? 'success' : 'error');
      if (r.res.ok) window.loadAttendanceSettingsCard();
    });
  };

  // ───────── สรุปภาพรวมการเข้างานรายเดือน (รวม / รายคน / รายวัน) ─────────
  window.loadAttendanceSummaryCard = async function (ym) {
    const host = $id('orgTabContent-attendance');
    if (!host) return;
    let c = $id('attSummaryCard');
    if (!c) {
      c = document.createElement('div');
      c.id = 'attSummaryCard';
      c.className = card + ' mb-4';
      const anchor = $id('attSettingsCard');
      if (anchor && anchor.nextSibling) host.insertBefore(c, anchor.nextSibling); else host.insertBefore(c, host.firstChild);
    }
    const month = ym || (c.dataset.month || new Date().toISOString().slice(0, 7));
    c.dataset.month = month;
    const { res, data } = await api('/api/org/attendance/summary?month=' + encodeURIComponent(month));
    if (!res.ok || !data.ok) { c.innerHTML = ''; return; }
    const t = data.totals;
    const stat = (label, val, sub, tone) => `<div class="rounded-xl border border-surface-200 dark:border-surface-800 p-3"><div class="text-[10px] font-bold uppercase tracking-widest text-surface-400">${label}</div><div class="text-xl font-black ${tone || 'dark:text-white'}">${val}</div><div class="text-[10px] text-surface-500">${sub || ''}</div></div>`;
    c.innerHTML = `
      <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div><div class="text-sm font-black dark:text-white">สรุปภาพรวมการเข้างาน</div><div class="text-[11px] text-surface-500">นับจากการเช็คชื่อทุกวันในเดือนที่เลือก (ประวัติรายวันของแต่ละคนดูได้ที่ตารางด้านล่าง)</div></div>
        <input id="attSumMonth" type="month" value="${esc(month)}" class="${inputCls}">
      </div>
      <div class="grid grid-cols-2 lg:grid-cols-5 gap-2.5 mb-4">
        ${stat('คนที่เช็คชื่อ', `${t.people}<span class="text-sm font-bold text-surface-400"> / ${t.members}</span>`, 'ของสมาชิกทั้งหมด')}
        ${stat('ครั้งที่เข้างาน', t.checkins, 'วัน-คน ในเดือนนี้')}
        ${stat('ตรงเวลา', t.on_time_pct + '%', `${t.on_time} ครั้ง`, t.on_time_pct >= 90 ? 'text-emerald-600' : 'text-amber-600')}
        ${stat('สาย / นอกพื้นที่', `${t.late} / ${t.outside}`, 'ครั้ง', t.late ? 'text-amber-600' : 'text-emerald-600')}
        ${stat('ชั่วโมงทำงานรวม', t.hours, `เฉลี่ย ${t.avg_hours_per_day} ชม./วัน`)}
      </div>
      <div class="grid lg:grid-cols-2 gap-4">
        <div>
          <div class="text-xs font-black dark:text-white mb-1.5">รายคน</div>
          ${data.employees.length ? `<div class="overflow-x-auto"><table class="w-full text-[11px]"><thead><tr class="text-left text-surface-400"><th class="py-1">ชื่อ</th><th>มา (วัน)</th><th>ตรงเวลา</th><th>สาย</th><th>นอกพื้นที่</th><th>ชม.รวม</th></tr></thead><tbody>
            ${data.employees.map(e => `<tr class="border-t border-surface-100 dark:border-surface-800"><td class="py-1.5 font-bold dark:text-white">${esc(e.username)}</td><td>${e.days}</td><td>${e.on_time}</td><td class="${e.late ? 'text-amber-600 font-bold' : ''}">${e.late}</td><td class="${e.outside ? 'text-rose-600 font-bold' : ''}">${e.outside}</td><td>${e.hours}</td></tr>`).join('')}
          </tbody></table></div>` : '<div class="text-xs text-surface-400 py-3">ยังไม่มีการเช็คชื่อในเดือนนี้</div>'}
        </div>
        <div>
          <div class="text-xs font-black dark:text-white mb-1.5">รายวัน (ประวัติทุกวันของเดือน)</div>
          ${data.days.length ? `<div class="overflow-y-auto max-h-64"><table class="w-full text-[11px]"><thead><tr class="text-left text-surface-400"><th class="py-1">วันที่</th><th>มาทำงาน</th><th>สาย</th><th>นอกพื้นที่</th></tr></thead><tbody>
            ${data.days.slice().reverse().map(d => `<tr class="border-t border-surface-100 dark:border-surface-800"><td class="py-1.5 font-bold dark:text-white">${esc(d.date)}</td><td>${d.present} คน</td><td class="${d.late ? 'text-amber-600 font-bold' : ''}">${d.late}</td><td class="${d.outside ? 'text-rose-600 font-bold' : ''}">${d.outside}</td></tr>`).join('')}
          </tbody></table></div>` : '<div class="text-xs text-surface-400 py-3">ยังไม่มีข้อมูล</div>'}
        </div>
      </div>`;
    const inp = $id('attSumMonth');
    if (inp) inp.addEventListener('change', () => { if (inp.value) window.loadAttendanceSummaryCard(inp.value); });
  };

  // ───────── แผนที่เลือกพิกัดสำนักงาน (Leaflet + OpenStreetMap — ฟรี ไม่ต้องใช้คีย์) ─────────
  let _attMap = null;
  function _ensureLeaflet() {
    return new Promise((resolve, reject) => {
      if (window.L && window.L.map) return resolve(window.L);
      if (!document.getElementById('leafletCss')) {
        const l = document.createElement('link');
        l.id = 'leafletCss'; l.rel = 'stylesheet';
        l.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css';
        document.head.appendChild(l);
      }
      let sc = document.getElementById('leafletJs');
      if (!sc) {
        sc = document.createElement('script');
        sc.id = 'leafletJs';
        sc.src = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js';
        document.head.appendChild(sc);
      }
      sc.addEventListener('load', () => resolve(window.L));
      sc.addEventListener('error', () => reject(new Error('โหลดแผนที่ไม่สำเร็จ')));
      if (window.L && window.L.map) resolve(window.L);
    });
  }
  // ดึงพิกัดจากลิงก์ Google Maps (@lat,lng / !3dlat!4dlng / ?q=lat,lng / ll=) หรือข้อความ "lat, lng"
  function _parseCoords(text) {
    const t = String(text || '').trim();
    const pats = [/@(-?\d+\.\d+),\s*(-?\d+\.\d+)/, /!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)/, /[?&](?:q|ll|query|center)=(-?\d+\.\d+)(?:,|%2C)\s*(-?\d+\.\d+)/, /^(-?\d+\.\d+)\s*[, ]\s*(-?\d+\.\d+)$/];
    for (const p of pats) { const m = t.match(p); if (m) { const a = +m[1], b = +m[2]; if (Math.abs(a) <= 90 && Math.abs(b) <= 180) return [a, b]; } }
    return null;
  }
  window._attInitMap = async function (st) {
    const el = $id('attCfgMap');
    if (!el) return;
    if (_attMap) { try { _attMap.remove(); } catch (e) { /* ignore */ } _attMap = null; }
    let L;
    try { L = await _ensureLeaflet(); } catch (e) { el.innerHTML = '<div class="p-6 text-xs text-rose-500">โหลดแผนที่ไม่สำเร็จ — กรอกพิกัดด้วยมือหรือใช้ปุ่ม "ใช้ตำแหน่งปัจจุบันของฉัน" แทนได้</div>'; return; }
    const latEl = $id('attCfgLat'), lngEl = $id('attCfgLng'), radEl = $id('attCfgRadius'), gLink = $id('attMapGoogle');
    const has = st.office_lat != null && st.office_lng != null;
    const start = has ? [st.office_lat, st.office_lng] : [13.7563, 100.5018];   // ยังไม่ตั้ง → เริ่มที่กรุงเทพ (แค่จุดเริ่มดูแผนที่ ไม่ได้บันทึก)
    _attMap = L.map(el, { scrollWheelZoom: true }).setView(start, has ? 17 : 11);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(_attMap);
    let marker = null, circle = null;
    const radius = () => Math.max(20, Math.min(20000, parseFloat(radEl.value) || 200));
    function place(lat, lng, pan) {
      latEl.value = (+lat).toFixed(6); lngEl.value = (+lng).toFixed(6);
      if (!marker) {
        marker = L.marker([lat, lng], { draggable: true }).addTo(_attMap);
        marker.on('dragend', () => { const p = marker.getLatLng(); place(p.lat, p.lng, false); });
        circle = L.circle([lat, lng], { radius: radius(), color: '#2563eb', weight: 2, fillOpacity: 0.12 }).addTo(_attMap);
      } else { marker.setLatLng([lat, lng]); circle.setLatLng([lat, lng]); }
      circle.setRadius(radius());
      if (gLink) { gLink.href = `https://www.google.com/maps?q=${(+lat).toFixed(6)},${(+lng).toFixed(6)}`; gLink.classList.remove('hidden'); }
      if (pan) _attMap.setView([lat, lng], Math.max(_attMap.getZoom(), 17));
    }
    if (has) place(start[0], start[1], false);
    _attMap.on('click', (e) => place(e.latlng.lat, e.latlng.lng, false));
    radEl.addEventListener('input', () => { if (circle) circle.setRadius(radius()); });
    const sync = () => { const a = parseFloat(latEl.value), b = parseFloat(lngEl.value); if (isFinite(a) && isFinite(b) && Math.abs(a) <= 90 && Math.abs(b) <= 180) place(a, b, true); };
    latEl.addEventListener('change', sync); lngEl.addEventListener('change', sync);
    $id('attMapPaste').addEventListener('input', (e) => { const c = _parseCoords(e.target.value); if (c) { place(c[0], c[1], true); toast('อ่านพิกัดจากลิงก์แล้ว', 'success'); } });
    $id('attMapSearch').addEventListener('keydown', async (e) => {
      if (e.key !== 'Enter') return;
      e.preventDefault();
      const q = e.target.value.trim();
      if (!q) return;
      const r = await api('/api/maps/search?q=' + encodeURIComponent(q));
      const hit = r.data && r.data.results && r.data.results[0];
      if (hit && isFinite(hit.lat) && isFinite(hit.lng)) { place(+hit.lat, +hit.lng, true); toast('พบ: ' + (hit.name || q), 'success'); }
      else toast('ไม่พบสถานที่นี้ ลองพิมพ์ให้ละเอียดขึ้น หรือคลิกบนแผนที่เอง', 'warning');
    });
    setTimeout(() => { try { _attMap.invalidateSize(); } catch (e) { /* ignore */ } }, 250);
  };
})();
