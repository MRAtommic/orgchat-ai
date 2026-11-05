// หน้าจัดการองค์กร: จัดแท็บ 16 อันเป็น 6 กลุ่ม (แถวบน = กลุ่ม, แถวล่าง = แท็บในกลุ่มนั้น)
// ไม่แตะ id/ฟังก์ชันเดิมของแท็บ — แค่ซ่อน/แสดงปุ่มและครอบ switchOrgTab()
(function () {
  const GROUPS = [
    { id: 'overview', label: 'ภาพรวม', icon: 'layout-dashboard', tabs: ['overview', 'usage'] },
    { id: 'people', label: 'สมาชิก', icon: 'users', tabs: ['members', 'tree', 'departments', 'lifecycle'] },
    { id: 'hr', label: 'งานบุคคล', icon: 'calendar-check', tabs: ['leave', 'attendance', 'access'] },
    { id: 'knowledge', label: 'ความรู้ & ประกาศ', icon: 'book-open', tabs: ['categories', 'announcements'] },
    { id: 'connect', label: 'เชื่อมต่อ', icon: 'plug', tabs: ['google', 'business', 'peak'] },
    { id: 'security', label: 'ความปลอดภัย', icon: 'shield-check', tabs: ['security', 'logs'] },
  ];
  const groupOf = (tab) => GROUPS.find(g => g.tabs.includes(tab));
  let bar = null;

  function paint(tab) {
    const g = groupOf(tab) || GROUPS[0];
    GROUPS.forEach(x => x.tabs.forEach(t => {
      const b = document.getElementById('orgTab-' + t);
      if (b) b.classList.toggle('hidden', x.id !== g.id);
    }));
    if (bar) bar.querySelectorAll('[data-org-group]').forEach(b => {
      const on = b.getAttribute('data-org-group') === g.id;
      b.className = 'whitespace-nowrap shrink-0 flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-black transition-all border ' +
        (on ? 'bg-brand-600 text-white border-brand-600 shadow-sm' : 'bg-white dark:bg-surface-900 text-surface-600 dark:text-surface-300 border-surface-200 dark:border-surface-700 hover:border-brand-400');
    });
  }

  function build() {
    const first = document.getElementById('orgTab-members');
    if (!first || document.getElementById('orgGroupBar')) return !!document.getElementById('orgGroupBar');
    const row = first.parentElement;
    bar = document.createElement('div');
    bar.id = 'orgGroupBar';
    bar.className = 'flex items-center gap-2 overflow-x-auto no-scrollbar pb-2';
    GROUPS.forEach(g => {
      const b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('data-org-group', g.id);
      b.innerHTML = '<i data-lucide="' + g.icon + '" class="w-4 h-4 shrink-0"></i><span></span>';
      b.querySelector('span').textContent = g.label;
      b.addEventListener('click', () => window.switchOrgTab(g.tabs[0]));
      bar.appendChild(b);
    });
    row.parentElement.insertBefore(bar, row);
    if (window.lucide && window.lucide.createIcons) { try { window.lucide.createIcons(); } catch (e) { /* ignore */ } }
    return true;
  }

  function install() {
    if (typeof window.switchOrgTab !== 'function' || window.switchOrgTab._grouped) return;
    const orig = window.switchOrgTab;
    const wrapped = function (tab) {
      const r = orig.apply(this, arguments);
      try { build(); paint(tab); } catch (e) { /* ไม่ให้กระทบการสลับแท็บเดิม */ }
      return r;
    };
    wrapped._grouped = true;
    window.switchOrgTab = wrapped;
    try { build(); paint('members'); } catch (e) { /* ignore */ }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install); else install();
})();
