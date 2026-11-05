// แปลรหัสกิจกรรม (Audit action) เป็นภาษาไทยที่คนอ่านเข้าใจ — ใช้ร่วมกันหลายหน้า
(function () {
  const MAP = {
    USER_LOGIN: ['🔑', 'เข้าสู่ระบบ', 'ok'],
    USER_LOGOUT: ['🚪', 'ออกจากระบบ', 'info'],
    CHAT_QUERY: ['💬', 'ถาม AI', 'brand'],
    FILE_UPLOAD: ['📤', 'อัปโหลดไฟล์เข้าคลังความรู้', 'info'],
    FILE_DELETE: ['🗑️', 'ลบไฟล์', 'danger'],
    UPDATE_CLEARANCE: ['🔐', 'ปรับระดับสิทธิ์เอกสาร', 'purple'],
    CATEGORY_DEPT_ACCESS: ['🏷️', 'กำหนดแผนกที่เข้าถึงหมวดเอกสาร', 'purple'],
    APPROVAL_DECIDED: ['✅', 'พิจารณาคำขออนุมัติ', 'info'],
    LINE_RICHMENU_SETUP: ['📱', 'สร้างเมนู LINE ตามบทบาท', 'info'],
    ORG_SECURITY_POLICY_UPDATED: ['🛡️', 'แก้นโยบายความปลอดภัยองค์กร', 'purple'],
    ORG_AUDIT_EXPORTED: ['📥', 'ส่งออกบันทึกกิจกรรม', 'info'],
    ORG_INVITE_REVOKED: ['✉️', 'ยกเลิกคำเชิญ', 'warn'],
    ORG_MEMBERS_IMPORTED: ['👥', 'นำเข้าสมาชิกหลายคน', 'info'],
    ORG_MEMBER_OFFBOARDED: ['👋', 'ดำเนินการพนักงานลาออก', 'danger'],
    ORG_MEMBER_JOINED_VIA_TOKEN: ['🤝', 'สมาชิกเข้าร่วมผ่านลิงก์เชิญ', 'ok'],
    SECURITY_IP_UNBLOCKED: ['🔓', 'ปลดบล็อก IP', 'warn'],
    SECURITY_ALERT_PROMPT_INJECTION: ['🚨', 'ตรวจพบความพยายามสั่ง AI ให้ทำผิดกติกา', 'danger'],
    WAF_ATTACK_BLOCKED: ['🛑', 'ระบบป้องกันบล็อกการโจมตี', 'danger'],
  };
  const TONE = {
    ok: 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20',
    info: 'bg-sky-500/10 text-sky-600 border border-sky-500/20',
    brand: 'bg-brand-500/10 text-brand-600 border border-brand-500/20',
    purple: 'bg-purple-500/10 text-purple-600 border border-purple-500/20',
    warn: 'bg-amber-500/10 text-amber-600 border border-amber-500/20',
    danger: 'bg-rose-500/10 text-rose-600 border border-rose-500/20',
    none: 'bg-surface-100 text-surface-700 dark:bg-surface-800 dark:text-surface-300',
  };
  // คืน {text, cls}  (text ปลอดภัยสำหรับ textContent; ถ้าใส่ innerHTML ต้อง esc เอง)
  window.auditActionInfo = function (code) {
    const c = String(code || '');
    const m = MAP[c];
    if (m) return { text: m[0] + ' ' + m[1], cls: TONE[m[2]] };
    let tone = 'none';
    if (/DELETE|OFFBOARD|BLOCK|ATTACK|INJECTION/.test(c)) tone = 'danger';
    else if (/CLEARANCE|ACCESS|POLICY/.test(c)) tone = 'purple';
    return { text: c.replace(/_/g, ' ').toLowerCase(), cls: TONE[tone] };
  };
})();
