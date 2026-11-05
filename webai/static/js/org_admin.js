// ─── Organization admin: Overview / Security policy / Member lifecycle / Audit ───
// ใช้ fetch ตัวกลางใน chat.js (แนบ CSRF token ให้อัตโนมัติ)
(function () {
  const esc = (t) => (window.escapeHtml ? window.escapeHtml(t == null ? '' : String(t)) : String(t == null ? '' : t).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
  const card = 'bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-800 rounded-2xl p-5 shadow-sm';
  const btn = 'px-3.5 py-2 rounded-xl text-xs font-bold transition-all active:scale-[0.98]';
  const btnPrimary = btn + ' bg-brand-600 hover:bg-brand-700 text-white';
  const btnGhost = btn + ' border border-surface-200 dark:border-surface-700 text-surface-700 dark:text-surface-200 hover:bg-surface-100 dark:hover:bg-surface-800';
  const input = 'w-full px-3 py-2 bg-surface-50 dark:bg-surface-950 border border-surface-200 dark:border-surface-800 rounded-xl text-xs dark:text-white outline-none focus:ring-2 focus:ring-brand-500';
  const toast = (m, t) => (window.showToast ? window.showToast(m, t || 'info') : alert(m));
  const $id = (i) => document.getElementById(i);

  async function api(url, opts) {
    const res = await fetch(url, opts);
    let data = {};
    try { data = await res.json(); } catch (e) { /* not json */ }
    return { res, data };
  }
  const post = (url, body) => api(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) });

  // ───────── 1) ภาพรวม ─────────
  window.loadOrgOverview = async function () {
    const box = $id('orgTabContent-overview');
    if (!box) return;
    box.innerHTML = `<div class="text-center py-10 text-xs font-semibold text-surface-400">กำลังโหลดภาพรวม...</div>`;
    const { res, data } = await api('/api/org/overview');
    if (!res.ok || !data.ok) { box.innerHTML = `<div class="${card} text-xs text-rose-500 font-semibold">${esc(data.error || 'โหลดข้อมูลไม่สำเร็จ (ต้องเป็น Admin องค์กร)')}</div>`; return; }
    const m = data.members, f = data.two_fa, q = data.quota || {}, a = data.alerts || [];
    const stat = (label, val, sub, tone) => `
      <div class="${card}"><div class="text-[10px] font-bold uppercase tracking-widest text-surface-400">${label}</div>
      <div class="text-2xl font-black mt-1 ${tone || 'text-surface-900 dark:text-white'}">${val}</div>
      <div class="text-[11px] text-surface-500 mt-0.5">${sub || ''}</div></div>`;
    const reqTxt = { off: 'ไม่บังคับ', admins: 'บังคับเฉพาะ Admin', all: 'บังคับทุกคน' }[f.required] || f.required;
    const quotaTxt = q.max_users ? (q.is_unlimited ? `${q.member_count} คน (ไม่จำกัด)` : `${q.member_count}/${q.max_users} คน`) : `${m.total} คน`;
    box.innerHTML = `
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
        ${stat('สมาชิกที่ใช้งาน', `${m.active}<span class="text-sm font-bold text-surface-400"> / ${m.total}</span>`, `ระงับ ${m.suspended} • Admin ${m.admins}`)}
        ${stat('เปิด 2FA แล้ว', `${f.percent}%`, `${f.enabled} คน • ยังไม่เปิด ${f.missing} คน`, f.percent >= 80 ? 'text-emerald-600' : (f.percent >= 40 ? 'text-amber-600' : 'text-rose-600'))}
        ${stat('โควตาสมาชิก', esc(quotaTxt), `แพ็กเกจ ${esc(q.plan_display || '-')}`)}
        ${stat('คำเชิญที่ใช้ได้อยู่', data.invites.active, `ทั้งหมด ${data.invites.total} ลิงก์`)}
      </div>
      <div class="grid lg:grid-cols-2 gap-3">
        <div class="${card}">
          <div class="text-xs font-black text-surface-900 dark:text-white mb-2">นโยบายที่ใช้อยู่</div>
          <ul class="text-xs text-surface-600 dark:text-surface-300 space-y-1.5">
            <li>การยืนยันตัวตนสองชั้น: <b>${reqTxt}</b></li>
            <li>หมดอายุเซสชันเมื่อไม่ใช้งาน: <b>${data.policy.session_timeout_min} นาที</b></li>
            <li>รหัสผ่านอย่างน้อย: <b>${data.policy.min_password_length} ตัวอักษร</b></li>
            <li>วิธีล็อกอินที่อนุญาต: <b>${data.policy.allowed_login_methods.map(x => ({ password: 'รหัสผ่าน', google: 'Google', line: 'LINE', qr: 'QR' }[x] || x)).join(', ')}</b></li>
          </ul>
          <button class="${btnGhost} mt-3" onclick="switchOrgTab('security')">แก้ไขนโยบาย</button>
        </div>
        <div class="${card}">
          <div class="text-xs font-black text-surface-900 dark:text-white mb-2">แจ้งเตือนความผิดปกติ (24 ชม.ล่าสุด)</div>
          ${a.length ? `<ul class="text-xs space-y-1.5">${a.map(x => `<li class="flex justify-between gap-2 p-2 rounded-lg bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-300"><span><b>${esc(x.username)}</b> ล็อกอินผิด ${x.failed} ครั้ง${x.distinct_ips > 1 ? ` จาก ${x.distinct_ips} IP` : ''}</span><span class="text-[10px] opacity-70">${esc(x.last_at)}</span></li>`).join('')}</ul>`
        : `<div class="text-xs text-emerald-600 font-semibold">ไม่พบความผิดปกติ</div>`}
          ${m.without_email ? `<div class="text-[11px] text-amber-600 mt-3">มี ${m.without_email} คนที่ยังไม่มีอีเมล (ใช้รับ OTP / กู้รหัสผ่านไม่ได้)</div>` : ''}
        </div>
      </div>`;
  };

  // ───────── 2) ความปลอดภัย ─────────
  const METHODS = [['password', 'รหัสผ่าน'], ['google', 'Google'], ['line', 'LINE'], ['qr', 'QR Code']];
  window.loadOrgSecurity = async function () {
    const box = $id('orgTabContent-security');
    if (!box) return;
    box.innerHTML = `<div class="text-center py-10 text-xs font-semibold text-surface-400">กำลังโหลด...</div>`;
    const [p, mem] = await Promise.all([api('/api/org/security/policy'), api('/api/org/security/members')]);
    if (!p.res.ok || !p.data.ok) { box.innerHTML = `<div class="${card} text-xs text-rose-500 font-semibold">${esc(p.data.error || 'ต้องเป็น Admin องค์กร')}</div>`; return; }
    const pol = p.data.policy;
    const members = (mem.data && mem.data.members) || [];
    const flag = (v) => v ? '<span class="text-emerald-600 font-bold">✓</span>' : '<span class="text-surface-300">–</span>';
    box.innerHTML = `
      <div class="${card} space-y-4">
        <div><div class="text-sm font-black text-surface-900 dark:text-white">นโยบายความปลอดภัยขององค์กร</div>
        <div class="text-[11px] text-surface-500">มีผลกับสมาชิกทุกคนในองค์กรทันทีที่บันทึก (เจ้าขององค์กรไม่ถูกจำกัดวิธีล็อกอิน)</div></div>
        <div class="grid md:grid-cols-2 gap-4">
          <label class="text-xs font-bold text-surface-700 dark:text-surface-200 space-y-1.5 block">การยืนยันตัวตนสองชั้น (2FA)
            <select id="secPolReq" class="${input}">
              <option value="off" ${pol.require_2fa === 'off' ? 'selected' : ''}>ไม่บังคับ (สมาชิกเลือกเอง)</option>
              <option value="admins" ${pol.require_2fa === 'admins' ? 'selected' : ''}>บังคับเฉพาะ Admin</option>
              <option value="all" ${pol.require_2fa === 'all' ? 'selected' : ''}>บังคับทุกคน</option>
            </select></label>
          <label class="text-xs font-bold text-surface-700 dark:text-surface-200 space-y-1.5 block">หมดอายุเซสชันเมื่อไม่ใช้งาน (นาที: 15–1440)
            <input id="secPolIdle" type="number" min="15" max="1440" value="${pol.session_timeout_min}" class="${input}"></label>
          <label class="text-xs font-bold text-surface-700 dark:text-surface-200 space-y-1.5 block">ความยาวรหัสผ่านขั้นต่ำ (8–64)
            <input id="secPolPw" type="number" min="8" max="64" value="${pol.min_password_length}" class="${input}"></label>
          <div class="text-xs font-bold text-surface-700 dark:text-surface-200 space-y-1.5">วิธีล็อกอินที่อนุญาต
            <div class="flex flex-wrap gap-3 pt-1">${METHODS.map(([k, n]) => `<label class="flex items-center gap-1.5 font-semibold"><input type="checkbox" class="secPolMethod" value="${k}" ${pol.allowed_login_methods.includes(k) ? 'checked' : ''}> ${n}</label>`).join('')}</div></div>
        </div>
        <div class="flex items-center gap-3"><button class="${btnPrimary}" onclick="saveOrgSecurityPolicy()">บันทึกนโยบาย</button>
          <span class="text-[11px] text-surface-400">${pol.updated_by ? `แก้ไขล่าสุดโดย ${esc(pol.updated_by)} • ${esc(pol.updated_at || '')}` : 'ยังไม่เคยตั้งค่า (ใช้ค่าเริ่มต้น)'}</span></div>
      </div>

      <div class="${card}">
        <div class="flex items-center justify-between gap-2 mb-3"><div class="text-sm font-black text-surface-900 dark:text-white">ตารางสิทธิ์และสถานะ 2FA ของสมาชิก</div>
          <button class="${btnGhost}" onclick="loadOrgSecurity()">รีเฟรช</button></div>
        <div class="overflow-x-auto table-responsive-wrapper"><table class="w-full text-xs min-w-[700px]">
          <thead><tr class="text-left text-[10px] uppercase tracking-wider text-surface-400 border-b border-surface-100 dark:border-surface-800">
            <th class="py-2 pr-3 sticky left-0 bg-white dark:bg-surface-900 z-10 shadow-xs">สมาชิก</th><th class="pr-3">บทบาท</th><th class="pr-3">2FA</th><th class="pr-3">การเงิน</th><th class="pr-3">อนุมัติลา</th><th class="pr-3">ดูคลัง</th><th class="pr-3">แก้คลัง</th><th class="pr-3">ลบคลัง</th><th class="pr-3">บรอดแคสต์</th><th class="pr-3">LINE</th><th>สถานะ</th></tr></thead>
          <tbody>${members.map(m => `<tr class="border-b border-surface-50 dark:border-surface-800/60 text-surface-700 dark:text-surface-200">
            <td class="py-2 pr-3 sticky left-0 bg-white dark:bg-surface-900 z-10 shadow-xs"><div class="font-bold">${esc(m.display_name)}</div><div class="text-[10px] text-surface-400">${esc(m.username)}${m.email ? ' • ' + esc(m.email) : ''}</div></td>
            <td class="pr-3">${m.is_owner ? 'Owner' : (m.role === 'admin' ? 'Admin' : 'Member')}</td>
            <td class="pr-3">${m.totp_enabled ? `<span class="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 font-bold">${m.totp_type === 'email' ? 'อีเมล' : 'แอป'}</span>` : '<span class="px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-600 font-bold">ยังไม่เปิด</span>'}</td>
            <td class="pr-3">${flag(m.can_view_financial)}</td><td class="pr-3">${flag(m.can_manage_leave)}</td><td class="pr-3">${flag(m.can_view_kb)}</td><td class="pr-3">${flag(m.can_edit_kb)}</td><td class="pr-3">${flag(m.can_delete_kb)}</td><td class="pr-3">${flag(m.can_broadcast_line)}</td><td class="pr-3">${flag(m.line_linked)}</td>
            <td>${m.is_active ? '<span class="text-emerald-600 font-bold">ใช้งาน</span>' : '<span class="text-rose-500 font-bold">ระงับ</span>'}</td></tr>`).join('')}</tbody></table></div>
      </div>

      <div class="${card} space-y-3">
        <div class="text-sm font-black text-surface-900 dark:text-white">รายงานกิจกรรม (Audit Log)</div>
        <div class="grid sm:grid-cols-5 gap-2">
          <input id="auditUser" placeholder="ผู้ใช้" class="${input}"><input id="auditAction" placeholder="กิจกรรม/คำค้น" class="${input}">
          <input id="auditFrom" type="date" class="${input}"><input id="auditTo" type="date" class="${input}">
          <div class="flex gap-2"><button class="${btnPrimary} flex-1" onclick="loadOrgAudit()">ค้นหา</button><button class="${btnGhost}" onclick="exportOrgAudit()">CSV</button></div>
        </div>
        <div id="auditResult" class="overflow-x-auto text-xs"></div>
      </div>`;
    loadOrgAudit();
  };

  window.saveOrgSecurityPolicy = async function () {
    const methods = [...document.querySelectorAll('.secPolMethod:checked')].map(c => c.value);
    const body = {
      require_2fa: $id('secPolReq').value,
      session_timeout_min: parseInt($id('secPolIdle').value, 10),
      min_password_length: parseInt($id('secPolPw').value, 10),
      allowed_login_methods: methods,
    };
    if (body.require_2fa !== 'off' && !confirm('การบังคับ 2FA จะทำให้สมาชิกที่ยังไม่เปิด 2FA ต้องตั้งค่าก่อนใช้งานต่อ (รวมถึงตัวคุณเองถ้ายังไม่เปิด) ต้องการดำเนินการต่อ?')) return;
    const { res, data } = await post('/api/org/security/policy', body);
    if (!res.ok || !data.ok) { toast(data.error || 'บันทึกไม่สำเร็จ', 'error'); return; }
    toast(data.message || 'บันทึกแล้ว', 'success');
    loadOrgSecurity();
  };

  function auditQS(extra) {
    const p = new URLSearchParams();
    [['user', 'auditUser'], ['action', 'auditAction'], ['from', 'auditFrom'], ['to', 'auditTo']].forEach(([k, id]) => { const v = ($id(id) || {}).value; if (v) p.set(k, v); });
    Object.entries(extra || {}).forEach(([k, v]) => p.set(k, v));
    return p.toString();
  }
  window.loadOrgAudit = async function () {
    const out = $id('auditResult'); if (!out) return;
    out.innerHTML = '<div class="py-4 text-surface-400">กำลังค้นหา...</div>';
    const { data } = await api('/api/org/audit?' + auditQS({ limit: 50 }));
    if (!data.ok) { out.innerHTML = `<div class="py-3 text-rose-500">${esc(data.error || 'โหลดไม่สำเร็จ')}</div>`; return; }
    out.innerHTML = `<div class="text-[11px] text-surface-400 mb-1">พบ ${data.total} รายการ (แสดง 50 ล่าสุด)</div>
      <div class="overflow-x-auto table-responsive-wrapper"><table class="w-full min-w-[550px]"><thead><tr class="text-left text-[10px] uppercase tracking-wider text-surface-400 border-b border-surface-100 dark:border-surface-800"><th class="py-1.5 pr-3">เวลา</th><th class="pr-3">ผู้ใช้</th><th class="pr-3">กิจกรรม</th><th class="pr-3">รายละเอียด</th><th>IP</th></tr></thead>
      <tbody>${data.logs.map(l => `<tr class="border-b border-surface-50 dark:border-surface-800/60 text-surface-700 dark:text-surface-200"><td class="py-1.5 pr-3 whitespace-nowrap">${esc(l.time)}</td><td class="pr-3">${esc(l.username)}</td><td class="pr-3 font-bold">${esc(l.action)}</td><td class="pr-3 max-w-xs truncate" title="${esc(l.details)}">${esc(l.details)}</td><td>${esc(l.ip)}</td></tr>`).join('') || '<tr><td colspan="5" class="py-4 text-center text-surface-400">ไม่พบรายการ</td></tr>'}</tbody></table></div>`;
  };
  window.exportOrgAudit = function () { window.location.href = '/api/org/audit/export?' + auditQS(); };

  // ───────── 3) สมาชิกขั้นสูง: นำเข้า / คำเชิญ / ลาออก ─────────
  const SAMPLE_CSV = 'username,email,display_name,department,role\nsomchai,somchai@example.com,สมชาย ใจดี,ขาย,member\nsomying,somying@example.com,สมหญิง รักงาน,บัญชี,member\n';
  window.loadOrgLifecycle = async function () {
    const box = $id('orgTabContent-lifecycle');
    if (!box) return;
    box.innerHTML = `
      <div class="${card} space-y-3">
        <div><div class="text-sm font-black text-surface-900 dark:text-white">นำเข้าสมาชิกพร้อมกันหลายคน (CSV)</div>
        <div class="text-[11px] text-surface-500">คอลัมน์: username, email, display_name, department, role (member/admin) — นำเข้าได้ครั้งละไม่เกิน 200 คน ระบบสร้างรหัสผ่านชั่วคราวให้และแสดงครั้งเดียว</div></div>
        <div class="flex flex-wrap gap-2 items-center">
          <input id="importFile" type="file" accept=".csv,text/csv" class="text-xs">
          <button class="${btnGhost}" onclick="downloadImportTemplate()">ดาวน์โหลดไฟล์ตัวอย่าง</button>
        </div>
        <textarea id="importCsv" rows="4" placeholder="หรือวางข้อมูล CSV ที่นี่" class="${input} font-mono"></textarea>
        <button class="${btnPrimary}" onclick="runMemberImport()">นำเข้าสมาชิก</button>
        <div id="importReport"></div>
      </div>

      <div class="${card} space-y-3">
        <div><div class="text-sm font-black text-surface-900 dark:text-white">เชิญหลายอีเมลในครั้งเดียว</div>
        <div class="text-[11px] text-surface-500">ใส่อีเมลบรรทัดละ 1 รายการ หรือคั่นด้วยคอมมา</div></div>
        <textarea id="bulkInviteEmails" rows="3" placeholder="a@company.com&#10;b@company.com" class="${input}"></textarea>
        <div class="flex items-center gap-2"><select id="bulkInviteRole" class="${input} !w-40"><option value="member">Member</option><option value="admin">Admin</option></select>
        <button class="${btnPrimary}" onclick="runBulkInvite()">ส่งคำเชิญ</button></div>
        <div id="bulkInviteReport" class="text-xs space-y-1"></div>
      </div>

      <div class="${card}">
        <div class="flex items-center justify-between mb-3"><div class="text-sm font-black text-surface-900 dark:text-white">คำเชิญแบบลิงก์ที่สร้างไว้</div>
          <button class="${btnGhost}" onclick="loadOrgInvites()">รีเฟรช</button></div>
        <div id="orgInvitesList" class="text-xs"></div>
      </div>

      <div class="${card}">
        <div class="mb-3"><div class="text-sm font-black text-surface-900 dark:text-white">พนักงานลาออก / พ้นสภาพ</div>
        <div class="text-[11px] text-surface-500">ระงับบัญชี ตัดการผูก LINE ออกจากระบบทุกอุปกรณ์ และโอนลูกทีมให้หัวหน้าคนใหม่</div></div>
        <div id="offboardList" class="text-xs"></div>
      </div>`;
    const f = $id('importFile');
    if (f) f.onchange = () => { const file = f.files[0]; if (!file) return; const r = new FileReader(); r.onload = () => { $id('importCsv').value = r.result; }; r.readAsText(file, 'utf-8'); };
    loadOrgInvites(); loadOffboardList();
  };

  window.downloadImportTemplate = function () { downloadBlob('members_template.csv', '﻿' + SAMPLE_CSV); };
  function downloadBlob(name, text) {
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type: 'text/csv;charset=utf-8' })); a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }
  const csvCell = (v) => { v = v == null ? '' : String(v); if (/^[=+\-@]/.test(v)) v = "'" + v; return '"' + v.replace(/"/g, '""') + '"'; };

  window.runMemberImport = async function () {
    const csv = ($id('importCsv').value || '').trim();
    if (!csv) { toast('กรุณาเลือกไฟล์หรือวางข้อมูล CSV', 'error'); return; }
    const { res, data } = await post('/api/org/members/import', { csv });
    const out = $id('importReport');
    if (!res.ok || !data.ok) { out.innerHTML = `<div class="text-rose-500 text-xs font-semibold">${esc(data.error || 'นำเข้าไม่สำเร็จ')}</div>`; return; }
    out.innerHTML = `<div class="text-xs font-bold mt-2">สร้างสำเร็จ ${data.created} • ข้าม ${data.skipped}</div>
      <div class="text-[11px] text-amber-600 mb-2">${esc(data.note)}</div>
      <div class="overflow-x-auto table-responsive-wrapper"><table class="w-full text-xs min-w-[500px]"><thead><tr class="text-left text-[10px] text-surface-400 uppercase"><th>#</th><th>ชื่อผู้ใช้</th><th>อีเมล</th><th>ผล</th><th>รหัสผ่านชั่วคราว</th></tr></thead>
      <tbody>${data.report.map(r => `<tr class="border-b border-surface-50 dark:border-surface-800/60"><td class="py-1">${r.row}</td><td>${esc(r.username)}</td><td>${esc(r.email)}</td><td class="${r.temp_password ? 'text-emerald-600' : 'text-surface-500'} font-semibold">${esc(r.status)}</td><td class="font-mono select-all">${esc(r.temp_password)}</td></tr>`).join('')}</tbody></table>
      <button class="${btnGhost} mt-2" id="dlImportReport">ดาวน์โหลดผลลัพธ์ (CSV)</button>`;
    $id('dlImportReport').onclick = () => downloadBlob('import_report.csv', '﻿' + ['row,username,email,status,temp_password'].concat(data.report.map(r => [r.row, r.username, r.email, r.status, r.temp_password].map(csvCell).join(','))).join('\n'));
    if (typeof loadOrgMembers === 'function') loadOrgMembers();
  };

  window.runBulkInvite = async function () {
    const emails = ($id('bulkInviteEmails').value || '').split(/[\s,;]+/).map(s => s.trim()).filter(Boolean);
    const out = $id('bulkInviteReport');
    if (!emails.length) { toast('กรุณาใส่อีเมลอย่างน้อย 1 รายการ', 'error'); return; }
    if (emails.length > 50) { toast('เชิญได้ครั้งละไม่เกิน 50 อีเมล', 'error'); return; }
    out.innerHTML = 'กำลังส่งคำเชิญ...';
    const role = $id('bulkInviteRole').value;
    const lines = [];
    for (const email of emails) {
      try {
        const { res, data } = await post('/api/org/invite-email', { email, role });
        lines.push(`<div class="${res.ok && data.ok ? 'text-emerald-600' : 'text-rose-500'}">${esc(email)} — ${esc(data.message || data.error || (res.ok ? 'ส่งแล้ว' : 'ไม่สำเร็จ'))}</div>`);
      } catch (e) { lines.push(`<div class="text-rose-500">${esc(email)} — เชื่อมต่อไม่สำเร็จ</div>`); }
    }
    out.innerHTML = lines.join('');
  };

  window.loadOrgInvites = async function () {
    const out = $id('orgInvitesList'); if (!out) return;
    const { data } = await api('/api/org/invites');
    const list = (data && data.invites) || [];
    const st = { active: ['ใช้ได้', 'text-emerald-600'], expired: ['หมดอายุ', 'text-surface-400'], used_up: ['ใช้ครบแล้ว', 'text-surface-400'] };
    out.innerHTML = list.length ? `<div class="overflow-x-auto table-responsive-wrapper"><table class="w-full min-w-[520px]"><thead><tr class="text-left text-[10px] uppercase tracking-wider text-surface-400"><th class="py-1.5">โทเค็น</th><th>บทบาท</th><th>แผนก</th><th>ใช้แล้ว</th><th>หมดอายุ</th><th>สถานะ</th><th></th></tr></thead><tbody>
      ${list.map(i => `<tr class="border-b border-surface-50 dark:border-surface-800/60"><td class="py-1.5 font-mono">${esc(i.token_short)}</td><td>${esc(i.role)}</td><td>${esc(i.department)}</td><td>${i.used_count}${i.max_uses ? '/' + i.max_uses : ''}</td><td>${esc(i.expires_at || 'ไม่หมดอายุ')}</td><td class="font-bold ${st[i.status][1]}">${st[i.status][0]}</td><td><button class="text-rose-500 font-bold" data-revoke="${esc(i.token)}">ยกเลิก</button></td></tr>`).join('')}</tbody></table></div>` : '<div class="text-surface-400 py-2">ยังไม่มีคำเชิญแบบลิงก์</div>';
    out.querySelectorAll('[data-revoke]').forEach(el => { el.onclick = () => revokeOrgInvite(el.getAttribute('data-revoke')); });
  };
  window.revokeOrgInvite = async function (token) {
    if (!confirm('ยกเลิกคำเชิญนี้? ลิงก์จะใช้งานไม่ได้อีก')) return;
    const { res, data } = await api('/api/org/invites/' + encodeURIComponent(token), { method: 'DELETE' });
    toast(res.ok ? 'ยกเลิกคำเชิญแล้ว' : (data.error || 'ไม่สำเร็จ'), res.ok ? 'success' : 'error');
    loadOrgInvites();
  };

  window.loadOffboardList = async function () {
    const out = $id('offboardList'); if (!out) return;
    const { data } = await api('/api/org/security/members');
    const ms = (data && data.members) || [];
    window._offboardMembers = ms;
    out.innerHTML = `<table class="w-full"><tbody>${ms.filter(m => !m.is_owner).map(m => `<tr class="border-b border-surface-50 dark:border-surface-800/60"><td class="py-1.5"><b>${esc(m.display_name)}</b> <span class="text-surface-400">${esc(m.username)}</span></td><td>${m.is_active ? '' : '<span class="text-rose-500 font-bold">ระงับแล้ว</span>'}</td><td class="text-right"><button class="text-rose-600 font-bold" data-offboard="${esc(m.username)}">ดำเนินการลาออก</button></td></tr>`).join('')}</tbody></table>`;
    out.querySelectorAll('[data-offboard]').forEach(el => { el.onclick = () => startOffboard(el.getAttribute('data-offboard')); });
  };
  window.startOffboard = async function (username) {
    const others = (window._offboardMembers || []).filter(m => m.username.toLowerCase() !== username.toLowerCase() && m.is_active);
    const hint = others.slice(0, 8).map(m => m.username).join(', ');
    const reassign = prompt(`โอนลูกทีมของ ${username} ให้ใคร? (ใส่ชื่อผู้ใช้ หรือเว้นว่างถ้าไม่ต้องการ)\nตัวอย่าง: ${hint}`, '');
    if (reassign === null) return;
    const remove = confirm(`ต้องการ "ถอด ${username} ออกจากองค์กร" ด้วยหรือไม่?\nตกลง = ถอดออกจากองค์กรเลย\nยกเลิก = ระงับบัญชีอย่างเดียว (กู้คืนได้ภายหลัง)`);
    if (!confirm(`ยืนยันดำเนินการลาออกของ ${username}?`)) return;
    const { res, data } = await post(`/api/org/members/${encodeURIComponent(username)}/offboard`, { reassign_to: reassign.trim(), remove_from_org: remove });
    if (!res.ok || !data.ok) { toast(data.error || 'ดำเนินการไม่สำเร็จ', 'error'); return; }
    toast('เสร็จสิ้น: ' + data.steps.join(' • '), 'success');
    loadOffboardList(); if (typeof loadOrgMembers === 'function') loadOrgMembers();
  };

  // ───────── บังคับตั้งค่า 2FA ตามนโยบายองค์กร ─────────
  let forcing = false;
  window.force2FASetup = async function () {
    if (forcing) return; forcing = true;
    toast('องค์กรของคุณบังคับให้เปิด 2FA กรุณาตั้งค่าก่อนใช้งานต่อ', 'warning');
    try { if (typeof start2FASetup === 'function') await start2FASetup(); } finally { setTimeout(() => { forcing = false; }, 3000); }
  };
  const origClose = window.close2FAModal;
  if (typeof origClose === 'function') {
    window.close2FAModal = function () {
      origClose();
      setTimeout(async () => {
        const { data } = await api('/api/org/security/my-status');
        if (data && data.must_setup_2fa) window.force2FASetup();
      }, 600);
    };
  }
  // ถ้าถูกบล็อกวิธีล็อกอิน (LINE callback redirect มาพร้อมข้อความ)
  try {
    const qp = new URLSearchParams(location.search);
    if (qp.get('login_blocked')) { setTimeout(() => toast(qp.get('login_blocked'), 'error'), 800); history.replaceState({}, '', '/'); }
  } catch (e) { /* ignore */ }
})();
