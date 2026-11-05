// หน้าตั้งค่า: เมนูลัดภายในหน้า (กดเลื่อนไปหมวด + ไฮไลต์หมวดที่กำลังดูอยู่)
(function () {
  function init() {
    const nav = document.getElementById('settingsNav');
    const scroller = document.getElementById('settingsScroll');
    if (!nav || !scroller || nav.dataset.ready) return;
    nav.dataset.ready = '1';
    const buttons = [...nav.querySelectorAll('[data-settings-target]')];
    const targets = buttons.map(b => document.getElementById(b.getAttribute('data-settings-target'))).filter(Boolean);

    function setActive(id) {
      buttons.forEach(b => b.classList.toggle('active', b.getAttribute('data-settings-target') === id));
    }
    buttons.forEach(b => b.addEventListener('click', () => {
      const el = document.getElementById(b.getAttribute('data-settings-target'));
      if (!el) return;
      const top = el.getBoundingClientRect().top - scroller.getBoundingClientRect().top + scroller.scrollTop - (window.innerWidth < 1024 ? 56 : 8);
      scroller.scrollTo({ top, behavior: 'smooth' });
      setActive(el.id);
    }));

    if ('IntersectionObserver' in window) {
      const io = new IntersectionObserver((entries) => {
        const vis = entries.filter(e => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
        if (vis) setActive(vis.target.id);
      }, { root: scroller, rootMargin: '-10% 0px -70% 0px', threshold: 0 });
      targets.forEach(t => io.observe(t));
    }
    setActive('myAccountCard');
    if (window.lucide && window.lucide.createIcons) { try { window.lucide.createIcons(); } catch (e) { /* ignore */ } }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
