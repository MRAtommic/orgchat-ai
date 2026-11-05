// ปรับความชัดเจนของ UI ทั่วแอป (ไม่แตะตรรกะเดิม)
// 1) ช่องวันที่: เบราว์เซอร์แสดงรูปแบบ mm/dd/yyyy ตามภาษาเครื่อง → เพิ่มบรรทัดเล็กใต้ช่องแสดงวันที่แบบไทย (พ.ศ.) ให้ตรวจได้ทันที
(function () {
  const MONTHS = ['มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน', 'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'];
  const DOW = ['อาทิตย์', 'จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์'];

  function thai(v) {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v || '');
    if (!m) return '';
    const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
    if (isNaN(d)) return '';
    return 'วัน' + DOW[d.getUTCDay()] + 'ที่ ' + (+m[3]) + ' ' + MONTHS[+m[2] - 1] + ' ' + (+m[1] + 543);
  }
  function eligible(inp) {
    if (!inp || inp.type !== 'date' || inp.dataset.noThHint) return false;
    if (inp.closest('td,th,thead,tbody')) return false;      // ไม่ยัดในตาราง
    return inp.offsetWidth === 0 || inp.offsetWidth >= 140;   // ช่องเล็กในแถวตัวกรองไม่ต้องมี
  }
  function hintFor(inp) {
    let h = inp.nextElementSibling && inp.nextElementSibling.classList.contains('th-date-hint') ? inp.nextElementSibling : null;
    if (!h) {
      h = document.createElement('div');
      h.className = 'th-date-hint text-[10px] font-semibold text-brand-600 dark:text-brand-400 mt-1 ml-1 min-h-[14px]';
      inp.insertAdjacentElement('afterend', h);
    }
    return h;
  }
  function update(inp) {
    if (!eligible(inp)) return;
    hintFor(inp).textContent = thai(inp.value);
  }
  document.addEventListener('input', (e) => { if (e.target && e.target.type === 'date') update(e.target); });
  document.addEventListener('change', (e) => { if (e.target && e.target.type === 'date') update(e.target); });
  function sweep() { document.querySelectorAll('input[type="date"]').forEach(update); }
  document.addEventListener('DOMContentLoaded', () => { sweep(); setInterval(sweep, 2500); }); // ฟอร์มที่เติมค่าด้วยสคริปต์
  if (document.readyState !== 'loading') { sweep(); setInterval(sweep, 2500); }
})();
