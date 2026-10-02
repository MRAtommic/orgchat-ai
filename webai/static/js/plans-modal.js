// ─── Subscription Plans & Billing Modal ───
              // ─── Plan Configuration ────────────────────────────
              const PLAN_CFG = {
                  free:     { label:'Free',  labelTh:'ฟรี',     price:0,   color:'#64748b', icon:'star',       badge:'plan-badge-free' },
                  pro:      { label:'Pro',   labelTh:'โปร',     price:299, color:'#059669', icon:'zap',        badge:'plan-badge-pro' },
                  business: { label:'Ultra', labelTh:'อัลตร้า', price:599, color:'#6366f1', icon:'building-2', badge:'plan-badge-business' },
              };
              const PLAN_RANK = { free:0, pro:1, business:2 };

              let plan_current = 'free';
              let plan_pendingPlan = null;

              // ─── Initializer called by app.js ──────────────────
              function initPlanView() {
                  console.log("💳 Initializing Plan View...");
                  try {
                      if (typeof lucide !== 'undefined') lucide.createIcons();
                      planCheckPayReturn();
                      planLoad();
                  } catch (e) {
                      console.error("Plan Init Error:", e);
                      planShowErr("เกิดข้อผิดพลาดในการเริ่มต้นหน้าแพลน: " + e.message);
                  }
              }

              // ─── Check payment return ───────────────────────────
              function planCheckPayReturn() {
                  const p = new URLSearchParams(location.search);
                  const r = p.get('payment'), pl = p.get('plan');
                  const el = document.getElementById('planPayBanner');
                  if (!el) return;
                  if (r === 'success') {
                      el.className = 'w-full pb-4 block';
                      el.innerHTML = `<div class="flex items-center gap-3 p-4 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/30 rounded-2xl text-sm">
                          <div class="w-9 h-9 bg-emerald-100 dark:bg-emerald-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
                              <i data-lucide="check-circle" class="w-5 h-5 text-emerald-600"></i>
                          </div>
                          <div>
                              <p class="font-extrabold text-emerald-800 dark:text-emerald-300">ชำระเงินสำเร็จ!</p>
                              <p class="text-emerald-600 dark:text-emerald-400 text-xs mt-0.5">แพลนถูกอัปเกรดเป็น <strong>${PLAN_CFG[pl]?.label || pl}</strong> แล้วค่ะ ระบบจะอัปเดตภายใน 1–2 นาที</p>
                          </div></div>`;
                      lucide.createIcons();
                      history.replaceState({}, '', '/');
                  } else if (r === 'cancel') {
                      el.className = 'w-full pb-4 block';
                      el.innerHTML = `<div id="planCancelBanner" class="flex items-center justify-between gap-3 p-4 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/30 rounded-2xl text-sm">
                          <div class="flex items-center gap-3">
                              <i data-lucide="info" class="w-4 h-4 text-amber-500 flex-shrink-0"></i>
                              <span class="text-amber-700 dark:text-amber-300">ยกเลิกการชำระเงินแล้วค่ะ ยังสามารถอัปเกรดได้ทุกเมื่อ</span>
                          </div>
                          <button onclick="document.getElementById('planCancelBanner').remove()" class="text-amber-400 hover:text-amber-600 p-1 flex-shrink-0">
                              <i data-lucide="x" class="w-4 h-4"></i>
                          </button></div>`;
                      lucide.createIcons();
                      history.replaceState({}, '', '/');
                      setTimeout(() => { const b = document.getElementById('planCancelBanner'); if (b) b.remove(); }, 7000);
                  } else {
                      el.className = 'hidden';
                  }
              }

              // ─── Fetch data from server ─────────────────────────
              async function planLoad() {
                  console.log("🔄 Loading plan status...");
                  const skel = document.getElementById('planSkeleton');
                  const cont = document.getElementById('planContent');
                  
                  try {
                      if (skel) skel.classList.remove('hidden');
                      if (cont) cont.classList.add('hidden');

                      // Use apiFetch (from app.js) which has better error handling and timeout
                      let d;
                      if (typeof apiFetch === 'function') {
                          d = await apiFetch('/api/billing/status');
                      } else {
                          const r = await fetch('/api/billing/status');
                          if (r.status === 401) { planShowAuth(); return; }
                          d = await r.json();
                      }

                      if (!d || !d.ok) throw new Error((d && d.error) || 'ไม่สามารถดึงข้อมูลแพลนได้');
                      
                      plan_current = d.plan || 'free';
                      planRender(d);
                  } catch(e) {
                      console.error("Plan Load Error:", e);
                      planShowErr(e.message || "ไม่สามารถโหลดข้อมูลได้ในขณะนี้");
                  }
              }

              // ─── Render View content ────────────────────────────
              function planRender(d) {
                  document.getElementById('planSkeleton').classList.add('hidden');
                  const c = document.getElementById('planContent');
                  c.classList.remove('hidden');
                  const sections = [
                      planRenderHeader(d),
                      planRenderUsageSection(d),
                      planRenderPlanSection(d)
                  ];
                  if (d.is_org_admin) {
                      sections.push(planRenderActionsSection(d));
                  }
                  c.innerHTML = sections.join('');
                  lucide.createIcons();
                  // Animate progress bars
                  requestAnimationFrame(() => {
                      document.querySelectorAll('[data-plan-w]').forEach(el => {
                          el.style.width = el.dataset.planW + '%';
                      });
                  });
              }

              // ─── Header segment ─────────────────────────────────
              function planRenderHeader(d) {
                  const cfg = PLAN_CFG[d.plan] || PLAN_CFG.free;
                  const expHtml = d.plan_expires_at
                      ? (d.cancel_at_period_end
                          ? '<span class="flex items-center gap-1 text-xs text-rose-500 dark:text-rose-400 font-semibold"><i data-lucide="calendar-x" class="w-3.5 h-3.5"></i>หมดอายุ ' + planFmtDate(d.plan_expires_at) + ' (ยกเลิกแล้ว)</span>'
                          : '<span class="flex items-center gap-1 text-xs text-slate-400 dark:text-surface-400"><i data-lucide="calendar" class="w-3.5 h-3.5"></i>ต่ออายุ ' + planFmtDate(d.plan_expires_at) + '</span>')
                      : (d.plan !== 'free'
                          ? '<span class="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400 font-semibold"><i data-lucide="infinity" class="w-3.5 h-3.5"></i>ไม่มีกำหนดหมดอายุ</span>'
                          : '');
                  const expiredBadge = d.is_expired
                      ? '<span class="plan-badge bg-rose-100 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400 border border-rose-200 dark:border-rose-800/30 ml-1">หมดอายุ</span>' : '';
                  const priceStr = cfg.price === 0 ? 'ฟรี' : ('฿' + cfg.price.toLocaleString() + '/เดือน');
                  const actionBtns = d.plan !== 'free'
                      ? (d.is_org_admin
                          ? '<div class="flex gap-2 flex-wrap">'
                            + (d.has_stripe_subscription
                                ? '<button class="plan-btn plan-btn-gray text-xs" onclick="planOpenPortal()"><i data-lucide="settings" class="w-3.5 h-3.5"></i>จัดการ Subscription</button>'
                                  + (!d.cancel_at_period_end
                                      ? '<button class="plan-btn plan-btn-red text-xs" onclick="planOpenModal(\'planCancelModal\')"><i data-lucide="x-circle" class="w-3.5 h-3.5"></i>ยกเลิกแผน</button>'
                                      : '')
                                : '')
                            + '</div>'
                          : '<span class="text-xs font-semibold text-slate-400 dark:text-surface-400 mt-2 block sm:mt-0 flex items-center gap-1"><i data-lucide="shield-alert" class="w-3.5 h-3.5"></i>เฉพาะ Admin องค์กรเท่านั้นที่จัดการได้</span>')
                      : '';

                  return `
                  <div class="bg-white dark:bg-surface-900 border border-slate-200 dark:border-surface-800 rounded-3xl p-6">
                      <div class="flex flex-col sm:flex-row sm:items-center gap-4">
                          <div class="w-16 h-16 rounded-2xl flex items-center justify-center flex-shrink-0"
                               style="background:${cfg.color}15;border:2.5px solid ${cfg.color}30">
                              <i data-lucide="${cfg.icon}" class="w-7 h-7" style="color:${cfg.color}"></i>
                          </div>
                          <div class="flex-1">
                              <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">แพลนปัจจุบัน</p>
                              <div class="flex items-center gap-2 flex-wrap">
                                  <span class="text-3xl font-black text-slate-900 dark:text-white">${cfg.label}</span>
                                  <span class="plan-badge ${cfg.badge}">${cfg.labelTh}</span>
                                  ${expiredBadge}
                              </div>
                              <div class="flex items-center gap-4 mt-1.5 flex-wrap">
                                  <span class="text-sm font-bold text-slate-500 dark:text-surface-300">${priceStr}</span>
                                  ${expHtml}
                              </div>
                          </div>
                          ${actionBtns}
                      </div>
                  </div>`;
      }

      // ─── Usage Segment ──────────────────────────────────
      function planRenderUsageSection(d) {
          const u = d.usage;
          return `
          <div>
              <h2 class="text-xs font-bold text-slate-400 dark:text-surface-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                  <i data-lucide="bar-chart-2" class="w-3.5 h-3.5"></i>การใช้งานเดือนนี้
              </h2>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  ${planUsageCard('ไฟล์เอกสาร (KB)', u.kb_files,   'files',          'ไฟล์')}
                  ${planUsageCard('บันทึกค่าใช้จ่าย', u.expenses,   'receipt',        'รายการ')}
                  ${planUsageCard('AI ถามตอบ',         u.ai_queries, 'message-circle', 'ครั้ง')}
                  ${planUsageCard('สมาชิกในทีม',       u.max_users,  'users',          'คน')}
              </div>
          </div>`;
      }

      function planUsageCard(label, stat, icon, unit) {
          const unlimited = stat.limit === -1;
          const used  = stat.used ?? 0;
          const limit = stat.limit ?? 0;
          const pct   = unlimited ? 100 : (limit > 0 ? Math.min(Math.round((used / limit) * 100), 100) : 0);
          const barColor = unlimited ? '#10b981'
                         : pct >= 90 ? '#ef4444'
                         : pct >= 70 ? '#f59e0b' : '#059669';
          const textColor = unlimited ? 'text-emerald-500'
                          : pct >= 90 ? 'text-rose-500'
                          : pct >= 70 ? 'text-amber-500' : 'text-emerald-600';
          const limitStr = unlimited
              ? '<span class="text-emerald-500 font-bold">/ ∞</span>'
              : '<span class="font-semibold text-slate-600 dark:text-surface-300">/ ' + limit.toLocaleString() + '</span> ' + unit;
          const alertHtml = (!unlimited && pct >= 90)
              ? '<p class="text-[10px] mt-1.5 text-rose-400 font-semibold"><i data-lucide="alert-circle" class="w-3 h-3 inline"></i> ใกล้ถึง limit — พิจารณาอัปเกรด</p>'
              : '';

          return `
          <div class="bg-white dark:bg-surface-900 border border-slate-200 dark:border-surface-800 rounded-3xl p-5">
              <div class="flex items-center gap-2 mb-3">
                  <i data-lucide="${icon}" class="w-4 h-4 text-slate-400 dark:text-surface-500"></i>
                  <p class="text-[10px] font-bold text-slate-400 dark:text-surface-500 uppercase tracking-widest leading-tight">${label}</p>
              </div>
              <div class="flex items-end justify-between mb-3">
                  <div class="flex items-baseline gap-1">
                      <span class="text-3xl font-black text-slate-900 dark:text-white">${used.toLocaleString()}</span>
                      <span class="text-xs text-slate-400 dark:text-surface-400 font-medium ml-0.5">${limitStr}</span>
                  </div>
                  <span class="text-xs font-bold ${textColor}">
                      ${unlimited ? 'ไม่จำกัด' : pct + '%'}
                  </span>
              </div>
              <div class="bar-track bg-slate-100 dark:bg-surface-950">
                  <div class="bar-fill" data-plan-w="${unlimited ? 100 : pct}"
                       style="width:0%;background:${barColor}"></div>
              </div>
              ${alertHtml}
          </div>`;
      }

      // ─── Plan Section ───────────────────────────────────
      function planRenderPlanSection(d) {
          const cur = d.plan;
          const cards = Object.entries(PLAN_CFG).map(([key, cfg]) => {
              const isCur  = key === cur;
              const isLow  = PLAN_RANK[key] < PLAN_RANK[cur];
              const isHigh = PLAN_RANK[key] > PLAN_RANK[cur];

              const borderStyle = isCur
                  ? `style="--plan-color:${cfg.color};border-color:${cfg.color};box-shadow:0 0 0 4px ${cfg.color}18"`
                  : '';

              const LIMITS = {
                  free:     ['10 รายการ/เดือน','35 ครั้ง/เดือน','5 ไฟล์ KB','1 คน'],
                  pro:      ['ไม่จำกัด','ไม่จำกัด','100 ไฟล์ KB','3 คน'],
                  business: ['ไม่จำกัด','ไม่จำกัด','ไม่จำกัด','10 คน'],
              }[key];
              const FEATS = {
                  free:     [false,false,false,false,false],
                  pro:      [true,true,true,false,false],
                  business: [true,true,true,true,true],
              }[key];
              const FEAT_LABELS = ['Google Sheets','Dashboard','LINE Bot','Export','Priority Support'];

              const limitHtml = ['ค่าใช้จ่าย','AI ถามตอบ','Knowledge Base','สมาชิก']
                  .map((l,i) => `<div class="flex items-start gap-2 text-sm">
                      <i data-lucide="check" class="w-3.5 h-3.5 mt-0.5 flex-shrink-0" style="color:${cfg.color}"></i>
                      <span class="text-slate-600 dark:text-surface-300"><span class="font-semibold text-slate-800 dark:text-white">${LIMITS[i]}</span> ${l}</span>
                  </div>`).join('');

              const featHtml = FEAT_LABELS.map((l,i) => FEATS[i]
                  ? `<span class="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/30 rounded-full px-2.5 py-0.5">
                         <i data-lucide="check" class="w-2.5 h-2.5"></i>${l}
                     </span>`
                  : `<span class="inline-flex items-center gap-1 text-[10px] font-bold text-slate-400 dark:text-surface-500 bg-slate-50 dark:bg-surface-900 border border-slate-200 dark:border-surface-800 rounded-full px-2.5 py-0.5">
                         <i data-lucide="minus" class="w-2.5 h-2.5"></i>${l}
                     </span>`
              ).join('');

              let btnHtml;
              if (isCur) {
                  btnHtml = `<div class="plan-btn justify-center w-full pointer-events-none"
                                  style="background:${cfg.color}15;color:${cfg.color};border:1.5px solid ${cfg.color}50">
                      <i data-lucide="check-circle" class="w-4 h-4"></i> แพลนของคุณ
                  </div>`;
              } else if (isLow) {
                  btnHtml = `<div class="plan-btn plan-btn-gray justify-center w-full pointer-events-none opacity-50 text-xs">
                      ไม่สามารถ Downgrade ได้
                  </div>`;
              } else {
                  if (d.is_org_admin) {
                      const btnClass = key === 'business' ? 'plan-btn-indigo' : 'plan-btn-green';
                      btnHtml = `<button class="plan-btn ${btnClass} justify-center w-full" onclick="planOpenPayModal('${key}')">
                          <i data-lucide="zap" class="w-4 h-4"></i> อัปเกรดเป็น ${cfg.label}
                      </button>`;
                  } else {
                      btnHtml = `<div class="plan-btn plan-btn-gray justify-center w-full pointer-events-none opacity-50 text-xs">
                          เฉพาะ Admin องค์กรเท่านั้นที่อัปเกรดได้
                      </div>`;
                  }
              }

              const popularTag = key === 'pro'
                  ? '<span class="plan-badge bg-emerald-500 text-white ml-1">แนะนำ</span>' : '';
              const priceHtml = cfg.price === 0
                  ? '<span class="text-2xl font-black text-slate-900 dark:text-white">ฟรี</span>'
                  : '<span class="text-2xl font-black text-slate-900 dark:text-white">฿' + cfg.price.toLocaleString() + '</span><span class="text-slate-400 dark:text-surface-400 text-xs font-semibold">/เดือน</span>';
              const curBadge = isCur ? '<span class="plan-badge ' + cfg.badge + '">ปัจจุบัน</span>' : '';

              return `
              <div class="plan-card ${isCur ? 'current' : ''} bg-white dark:bg-surface-900 border border-slate-200 dark:border-surface-800 p-5 flex flex-col gap-4" ${borderStyle}>
                  <div>
                      <div class="flex items-center gap-2 mb-1 flex-wrap">
                          <i data-lucide="${cfg.icon}" class="w-5 h-5" style="color:${cfg.color}"></i>
                          <span class="font-extrabold text-slate-900 dark:text-white text-lg">${cfg.label}</span>
                          ${curBadge}
                          ${popularTag}
                      </div>
                      <div class="flex items-baseline gap-1.5">${priceHtml}</div>
                  </div>
                  <div class="space-y-2">${limitHtml}</div>
                  <div class="flex flex-wrap gap-1.5">${featHtml}</div>
                  ${btnHtml}
              </div>`;
          }).join('');

          return `
          <div>
              <h2 class="text-xs font-bold text-slate-400 dark:text-surface-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                  <i data-lucide="layers" class="w-3.5 h-3.5"></i>เปรียบเทียบและเปลี่ยนแพลน
              </h2>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">${cards}</div>
          </div>`;
      }

      // ─── Actions Section ────────────────────────────────
      function planRenderActionsSection(d) {
          if (d.plan === 'free') {
              return `
              <div class="bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950/20 dark:to-teal-950/20 border border-emerald-200 dark:border-emerald-800/30 rounded-3xl p-6 flex flex-col sm:flex-row items-center gap-5">
                  <div class="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 rounded-2xl flex items-center justify-center flex-shrink-0">
                      <i data-lucide="sparkles" class="w-6 h-6 text-emerald-600"></i>
                  </div>
                  <div class="flex-1 text-center sm:text-left">
                      <p class="font-extrabold text-emerald-900 dark:text-emerald-300 mb-0.5">อัปเกรดเพื่อปลดล็อคทุกฟีเจอร์</p>
                      <p class="text-sm text-emerald-700 dark:text-emerald-400">Google Sheets, LINE Bot, Dashboard การเงิน และอีกมากมาย</p>
                  </div>
                  <div class="flex gap-3 flex-wrap justify-center">
                      <button class="plan-btn plan-btn-green whitespace-nowrap" onclick="planOpenPayModal('pro')">
                          <i data-lucide="zap" class="w-4 h-4"></i> Pro — ฿299/เดือน
                      </button>
                      <button class="plan-btn plan-btn-indigo whitespace-nowrap" onclick="planOpenPayModal('business')">
                          <i data-lucide="building-2" class="w-4 h-4"></i> Ultra — ฿599/เดือน
                      </button>
                  </div>
              </div>`;
          }

          return `
          <div class="bg-white dark:bg-surface-900 border border-slate-200 dark:border-surface-800 rounded-3xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div class="text-center sm:text-left">
                  <p class="font-bold text-slate-700 dark:text-surface-200">ต้องการจัดการ Subscription?</p>
                  <p class="text-sm text-slate-400 dark:text-surface-450 mt-0.5">ดูประวัติการชำระ, เปลี่ยนบัตร, หรือยกเลิก Subscription ใน Stripe Portal</p>
              </div>
              <div class="flex gap-3 flex-wrap justify-center">
                  <button class="plan-btn plan-btn-gray" onclick="planOpenPortal()">
                      <i data-lucide="external-link" class="w-4 h-4"></i>Stripe Portal
                  </button>
                  <button class="plan-btn plan-btn-red" onclick="planOpenModal('planCancelModal')">
                      <i data-lucide="x-circle" class="w-4 h-4"></i>ยกเลิกแผน
                  </button>
              </div>
          </div>`;
      }

      // ─── Payment Modal ─────────────────────────────────
      function planOpenPayModal(plan) {
          plan_pendingPlan = plan;
          const cfg = PLAN_CFG[plan];
          const el = document.getElementById('planPayModalBody');
          if (!el) return;
          el.innerHTML = `
              <div class="bg-slate-50 dark:bg-surface-950 border border-slate-100 dark:border-surface-800/80 rounded-2xl p-4 mb-2">
                  <div class="flex items-center gap-3 mb-1">
                      <i data-lucide="${cfg.icon}" class="w-5 h-5" style="color:${cfg.color}"></i>
                      <span class="font-extrabold text-slate-900 dark:text-white text-lg">อัปเกรดเป็น ${cfg.label}</span>
                  </div>
                  <p class="text-2xl font-black text-slate-900 dark:text-white">
                      ฿${cfg.price.toLocaleString()}
                      <span class="text-sm font-semibold text-slate-400">/เดือน</span>
                  </p>
              </div>
              <p class="text-sm text-slate-500 dark:text-slate-400 px-0.5 mb-3">เลือกช่องทางชำระเงิน</p>
              <button id="planBtnCard" class="plan-btn plan-btn-green w-full justify-center text-base py-3.5 mb-2" onclick="planDoCheckout('card')">
                  <i data-lucide="credit-card" class="w-5 h-5"></i> บัตรเครดิต / Visa / Mastercard
              </button>
              <button id="planBtnPP" class="plan-btn plan-btn-outline-green w-full justify-center text-base py-3.5" onclick="planDoCheckout('promptpay')">
                  <span class="w-5 h-5 rounded-full bg-green-700 flex items-center justify-center text-white text-[9px] font-black flex-shrink-0">PP</span>
                  PromptPay — ชำระครั้งเดียว 30 วัน
              </button>
              <p class="text-[11px] text-slate-400 text-center mt-3 px-2">
                  PromptPay ต้องต่ออายุเองทุก 30 วัน • ชำระผ่าน Stripe (ปลอดภัย 100%)
              </p>`;
          lucide.createIcons();
          planOpenModal('planPayModal');
      }

      async function planDoCheckout(method) {
          const plan = plan_pendingPlan;
          const isCard = method === 'card';
          const btn = document.getElementById(isCard ? 'planBtnCard' : 'planBtnPP');
          if (!btn) return;
          const cardLabel = '<i data-lucide="credit-card" class="w-5 h-5"></i> บัตรเครดิต / Visa / Mastercard';
          const ppLabel   = '<span class="w-5 h-5 rounded-full bg-green-700 flex items-center justify-center text-white text-[9px] font-black flex-shrink-0">PP</span> PromptPay — ชำระครั้งเดียว 30 วัน';
          function resetBtn() {
              btn.disabled = false;
              btn.innerHTML = isCard ? cardLabel : ppLabel;
              if (typeof lucide !== 'undefined') lucide.createIcons();
          }
          btn.disabled = true;
          btn.innerHTML = '<span class="w-4 h-4 border-2 border-white border-t-transparent rounded-full spin"></span> กำลังโหลด...';
          try {
              const r = await fetch(isCard ? '/api/b/c' : '/api/b/cp', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ plan })
              });
              if (r.status === 401) { window.location.href = `/signup?plan=${plan}`; return; }
              const data = await r.json();
              if (data.ok && data.url) {
                  window.location.href = data.url;
              } else if (data.needs_org) {
                  planCloseModal('planPayModal');
                  if (typeof toast === 'function') toast('กรุณาสร้างองค์กรก่อน', 'info');
                  setTimeout(() => window.location.href = '/onboarding', 1500);
              } else {
                  if (typeof toast === 'function') toast(data.error || 'เกิดข้อผิดพลาด กรุณาลองใหม่', 'error');
                  resetBtn();
              }
          } catch(e) {
              if (typeof toast === 'function') toast('เชื่อมต่อไม่ได้', 'error');
              resetBtn();
          }
      }

      // ─── Stripe Portal ─────────────────────────────────
      async function planOpenPortal() {
          if (typeof toast === 'function') toast('กำลังเปิด Subscription Portal...', 'info');
          try {
              const r = await fetch('/api/b/p', { method: 'POST' });
              const d = await r.json();
              if (d.ok && d.url) window.location.href = d.url;
              else if (typeof toast === 'function') toast(d.error || 'ไม่สามารถเปิด Portal ได้', 'error');
          } catch(e) { if (typeof toast === 'function') toast('เกิดข้อผิดพลาด', 'error'); }
      }

      // ─── Cancel Plan ───────────────────────────────────
      async function planDoCancelPlan() {
          const btn = document.getElementById('planCancelConfirmBtn');
          if (!btn) return;
          const originalHtml = '<i data-lucide="x-circle" class="w-4 h-4"></i> ยืนยันยกเลิก';
          function resetBtn() {
              btn.disabled = false;
              btn.innerHTML = originalHtml;
              if (typeof lucide !== 'undefined') lucide.createIcons();
          }
          btn.disabled = true;
          btn.innerHTML = '<span class="w-4 h-4 border-2 border-current border-t-transparent rounded-full spin"></span> กำลังยกเลิก...';
          try {
              const r = await fetch('/api/billing/cancel-plan', { method: 'POST' });
              const d = await r.json();
              if (d.ok) {
                  resetBtn();
                  planCloseModal('planCancelModal');
                  if (typeof toast === 'function') toast('ยกเลิกแผนสำเร็จ — แผนจะถูกยกเลิกเมื่อสิ้นสุดรอบการใช้งานนี้ค่ะ', 'success');
                  setTimeout(planLoad, 1200);
              } else {
                  if (typeof toast === 'function') toast(d.error || 'ยกเลิกไม่สำเร็จ', 'error');
                  resetBtn();
              }
          } catch(e) {
              if (typeof toast === 'function') toast('เกิดข้อผิดพลาด', 'error');
              resetBtn();
          }
      }

      // ─── Modal Helpers ─────────────────────────────────
      function planOpenModal(id)  { const el = document.getElementById(id); if (el) { el.classList.add('open'); document.body.style.overflow='hidden'; } }
      function planCloseModal(id) { const el = document.getElementById(id); if (el) { el.classList.remove('open'); document.body.style.overflow=''; } }
      document.querySelectorAll('.plan-overlay').forEach(el => {
          el.addEventListener('click', e => { if (e.target === el) planCloseModal(el.id); });
      });

      // ─── Error States ──────────────────────────────────
      function planShowErr(msg) {
          document.getElementById('planSkeleton').classList.add('hidden');
          const c = document.getElementById('planContent');
          c.classList.remove('hidden');
          c.innerHTML = `
          <div class="py-24 flex flex-col items-center gap-4 text-center">
              <div class="w-16 h-16 bg-rose-50 dark:bg-rose-950/20 rounded-2xl flex items-center justify-center">
                  <i data-lucide="alert-triangle" class="w-8 h-8 text-rose-400"></i>
              </div>
              <p class="text-slate-500 dark:text-surface-400 text-sm max-w-xs">${msg}</p>
              <div class="flex gap-3 mt-1">
                  <button onclick="planLoad()" class="plan-btn plan-btn-green">ลองใหม่</button>
                  <button onclick="showView('home')" class="plan-btn plan-btn-gray">กลับหน้าหลัก</button>
              </div>
          </div>`;
          lucide.createIcons();
      }

      function planShowAuth() {
          planShowErr('กรุณาเข้าสู่ระบบก่อนดูข้อมูลแพลน');
      }

      // ─── Date Formatter ────────────────────────────────
      function planFmtDate(iso) {
          try { return new Date(iso).toLocaleDateString('th-TH', { year:'numeric', month:'long', day:'numeric' }); }
          catch { return iso; }
      }

      // ─── Auto-trigger on page load if query param matches ────
      (function() {
          const params = new URLSearchParams(window.location.search);
          if (params.get('view') === 'plan') {
              // Defer execution slightly to let index.html and app.js scripts initialize
              setTimeout(() => {
                  if (typeof showView === 'function') {
                      showView('plan');
                  }
              }, 150);
          }
      })();
