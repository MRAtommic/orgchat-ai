// ─── Google Sheets Expense Reconciliation UI ───
    // ─── State ───────────────────────────────────────────
        let globalSheetsList = [];
        let unclearRows = [];
        let allExpenses = [];   // Standardized full expenses from Sheets
        let currentTab = 'all'; // 'all', 'vat', 'unclear'
        let currentEmbedZoom = 1.0;

        // Currently edited row info
        let currentEditItem = null;

        // ─── Init ────────────────────────────────────────────
        window.addEventListener('load', function () {
            lucide.createIcons();
            const hash = window.location.hash || '';
            if (hash.includes('tax') || hash.includes('expense') || hash.includes('finance')) {
                loadDashboardData();
            }
        });

        // ─── DATA LOADING ────────────────────────────────────
        function loadDashboardData() {
            // Check if user has permission to view financial dashboard
            if (typeof state !== 'undefined' && state.userRole && state.userRole !== 'admin' && !state.canViewFinancial) {
                return;
            }
            // ── Feature gate: skip API calls if plan doesn't include financial_dashboard ──
            if (typeof state !== 'undefined' && state.orgFeatures && !state.orgFeatures.financial_dashboard) {
                const catList = document.getElementById('catList');
                if (catList) {
                    catList.innerHTML = '<div class="text-center py-12 text-slate-400 dark:text-slate-500">' +
                        '<i data-lucide="lock" class="w-10 h-10 mx-auto mb-3 opacity-50"></i>' +
                        '<p class="text-sm font-semibold mb-1">ฟีเจอร์แดชบอร์ดการเงิน</p>' +
                        '<p class="text-xs">ฟีเจอร์นี้ต้องใช้ Plan Pro ขึ้นไป</p>' +
                        '<a href="/pricing?upgrade=financial_dashboard" class="inline-block mt-3 px-4 py-2 text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 rounded-lg transition">อัปเกรด Plan</a>' +
                        '</div>';
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                }
                console.log('📊 Financial dashboard feature not available on current plan — skipping API calls.');
                return;
            }

            const icon = document.getElementById('refreshIcon');
            if (icon) icon.classList.add('spinning');

            document.getElementById('catList').innerHTML =
                '<div class="text-center py-8 text-slate-400 text-sm">กำลังดึงข้อมูล...</div>';

            // 1. Fetch dashboard summaries, unclear scans, and categories
            apiFetch('/api/dashboard/tax-expense-data')
                .then(data => {
                    if (!data.ok) { showError(data.error); return; }
                    
                    // Render Summaries
                    animateValue('valExpense', data.total_expense);
                    animateValue('valVat',     data.total_vat);
                    animateValue('valWht3',    data.total_wht_3);
                    animateValue('valWht53',   data.total_wht_53);
                    document.getElementById('chartTotalLabel').textContent = formatNum(data.total_expense);

                    // Dynamic Business Profile Updates
                    if (data.biz_profile || data.org_info) {
                        const p = data.biz_profile || {};
                        const o = data.org_info || {};
                        const nameTh = p.business_name_th || o.name || 'ชื่อบริษัทของคุณ';
                        const nameEn = p.business_name_en || 'Your Company English Name';
                        const phone = p.phone || '-';
                        
                        const lblTh = document.getElementById('companyNameLabel');
                        if (lblTh) lblTh.textContent = nameTh;
                        
                        const lblEn = document.getElementById('companyNameEnLabel');
                        if (lblEn) lblEn.textContent = nameEn;
                        
                        const lblPhone = document.getElementById('companyPhoneLabel');
                        if (lblPhone) {
                            lblPhone.innerHTML = `<i data-lucide="phone" class="w-3.5 h-3.5 text-slate-400"></i> ${phone}`;
                            if (typeof initIcons === 'function') initIcons();
                        }
                        
                        const expenseLblTh = document.getElementById('expenseFormCompanyNameLabel');
                        if (expenseLblTh) expenseLblTh.textContent = nameTh;
                        const expenseLblEn = document.getElementById('expenseFormCompanyNameEnLabel');
                        if (expenseLblEn) expenseLblEn.textContent = nameEn;
                    }

                    globalSheetsList = data.sheets_list || [];
                    unclearRows = data.unclear_scans || [];

                    if (data.spreadsheet_url) {
                        const sheetsLink = document.getElementById('dashboardSheetsLink');
                        if (sheetsLink) sheetsLink.href = data.spreadsheet_url;
                    }
                    if (data.drive_folder_url) {
                        const driveLink = document.getElementById('dashboardDriveLink');
                        if (driveLink) driveLink.href = data.drive_folder_url;
                    }

                    renderCategories(data.categories, data.total_expense);
                    renderExpenseDoughnutChart(data.categories);
                    renderUnclearTable(unclearRows);
                })
                .catch(err => {
                    console.error(err);
                });

            // 2. Fetch full list of standardized expenses
            apiFetch('/api/dashboard/all-expenses')
                .then(data => {
                    if (icon) icon.classList.remove('spinning');
                    if (data.ok) {
                        allExpenses = data.expenses || [];
                        const totalCount = allExpenses.length;
                        const paidCount = allExpenses.filter(e => e.status === 'จ่ายแล้ว').length;
                        const countEl = document.getElementById('valExpenseCount');
                        if (countEl) countEl.textContent = `${totalCount} รายการ`;
                        const paidEl = document.getElementById('valPaidCount');
                        if (paidEl) paidEl.textContent = `${paidCount}`;
                        populateFilters(allExpenses);
                        applyAllFilters();
                    }
                })
                .catch(err => {
                    if (icon) icon.classList.remove('spinning');
                    console.error(err);
                });
        }

        let expenseChartInstance = null;

        function renderExpenseDoughnutChart(categories) {
            const canvas = document.getElementById('mainChart');
            if (!canvas) return;

            if (expenseChartInstance) {
                expenseChartInstance.destroy();
                expenseChartInstance = null;
            }

            if (!categories || categories.length === 0) {
                return;
            }

            const labels = categories.map(c => c.name || c.category || 'อื่นๆ');
            const data = categories.map(c => Number(c.value || c.amount || 0));

            const colorPalette = [
                '#3b82f6', // blue
                '#6366f1', // indigo
                '#10b981', // emerald
                '#f59e0b', // amber
                '#ec4899', // pink
                '#8b5cf6', // purple
                '#14b8a6', // teal
                '#f97316'  // orange
            ];

            const isDark = document.documentElement.classList.contains('dark');
            const borderCol = isDark ? '#0f172a' : '#ffffff';

            const ctx = canvas.getContext('2d');
            expenseChartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: colorPalette.slice(0, data.length),
                        borderWidth: 3,
                        borderColor: borderCol,
                        hoverOffset: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '72%',
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const val = context.parsed || 0;
                                    return ' ' + context.label + ': ฿' + formatNum(val);
                                }
                            }
                        }
                    }
                }
            });
        }

        function renderCategories(categories, totalExpense) {
            const list = document.getElementById('catList');
            if (!list) return;
            
            if (!categories || categories.length === 0) {
                list.innerHTML = '<div class="text-center py-8 text-surface-400 text-xs">ไม่มีข้อมูลหมวดหมู่</div>';
                return;
            }

            const colorPalette = ['#3b82f6', '#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#14b8a6', '#f97316'];
            
            list.innerHTML = categories.map((cat, idx) => {
                const name = cat.name || cat.category || 'อื่นๆ';
                const amount = cat.value || cat.amount || 0;
                const pct = totalExpense > 0 ? ((amount / totalExpense) * 100).toFixed(1) : '0.0';
                const barColor = colorPalette[idx % colorPalette.length];
                
                return `
                    <div class="space-y-2 p-3.5 rounded-xl bg-surface-50/70 dark:bg-surface-800/40 border border-surface-200/70 dark:border-surface-700/60 hover:border-brand-500/40 transition-all">
                        <div class="flex items-center justify-between text-xs">
                            <div class="flex items-center gap-2">
                                <span class="w-2.5 h-2.5 rounded-full shrink-0" style="background-color: ${barColor}"></span>
                                <span class="font-semibold text-surface-900 dark:text-white">${escHtml(name)}</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="font-bold text-surface-900 dark:text-white tabular-nums">฿${formatNum(amount)}</span>
                                <span class="text-[10px] text-surface-600 dark:text-surface-300 font-bold bg-surface-200/60 dark:bg-surface-700 px-2 py-0.5 rounded-md">${pct}%</span>
                            </div>
                        </div>
                        <div class="w-full h-1.5 bg-surface-200/80 dark:bg-surface-700/80 rounded-full overflow-hidden">
                            <div class="h-full rounded-full transition-all duration-500" style="width: ${pct}%; background-color: ${barColor}"></div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function renderMonthlySummary(groups) {
            const list = document.getElementById('monthlySummaryList');
            if (!list) return;

            const groupKeys = Object.keys(groups).sort((a, b) => {
                if (a === 'unknown') return 1;
                if (b === 'unknown') return -1;
                return b.localeCompare(a);
            });

            if (groupKeys.length === 0) {
                list.innerHTML = '<div class="text-center py-8 text-surface-400 text-xs">ไม่มีข้อมูลสรุปรายเดือน</div>';
                return;
            }

            list.innerHTML = groupKeys.map(k => {
                const title = formatGroupNameTH(k);
                const items = groups[k] || [];
                const total = items.reduce((sum, item) => sum + (item.net_amount || 0), 0);
                const isUnknown = k === 'unknown';

                return `
                    <div class="flex items-center justify-between p-3 rounded-xl bg-surface-50/70 dark:bg-surface-800/40 border border-surface-200/70 dark:border-surface-700/60 hover:bg-surface-100/60 dark:hover:bg-surface-700/40 transition-all text-xs">
                        <div class="flex items-center gap-2.5">
                            <span class="w-2 h-2 rounded-full ${isUnknown ? 'bg-amber-400' : 'bg-brand-500'}"></span>
                            <div>
                                <span class="font-semibold text-surface-900 dark:text-white">${escHtml(title)}</span>
                                <span class="text-[10px] text-surface-400 dark:text-surface-500 ml-1.5">(${items.length} รายการ)</span>
                            </div>
                        </div>
                        <span class="font-bold text-surface-900 dark:text-white tabular-nums">฿${formatNum(total)}</span>
                    </div>
                `;
            }).join('');
        }

        // ─── POPULATE FILTERS ────────────────────────────────
        function populateFilters(expenses) {
            // Populate requesters
            const reqSelect = document.getElementById('filterRequester');
            const requesters = new Set();
            expenses.forEach(e => {
                if (e.line_sender_name && e.line_sender_name !== '-') {
                    requesters.add(e.line_sender_name);
                }
            });
            
            reqSelect.innerHTML = '<option value="">ทั้งหมด</option>';
            requesters.forEach(r => {
                reqSelect.innerHTML += `<option value="${escHtml(r)}">${escHtml(r)}</option>`;
            });
        }

        // ─── TAB SWITCHING ───────────────────────────────────
        function switchTab(tab) {
            currentTab = tab;

            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.toggle('active', btn.id === `tabBtn-${tab}`);
            });
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.toggle('hidden', pane.id !== `tabContent-${tab}`);
            });

            if (tab === 'pnd') {
                loadPndReport();
            } else {
                applyAllFilters();
            }
        }

        // ─── ภ.ง.ด. MONTHLY REPORT ──────────────────────────
        let pndData = null;

        function loadPndReport() {
            const year = document.getElementById('pndYearFilter').value;
            const btn = document.getElementById('pndRefreshBtn');
            btn.textContent = 'กำลังโหลด...';
            btn.disabled = true;

            fetch(`/api/dashboard/wht-monthly-report?year=${year}`)
                .then(r => r.json())
                .then(data => {
                    btn.textContent = 'โหลดข้อมูล';
                    btn.disabled = false;
                    if (!data.ok) {
                        document.getElementById('pndSummaryCards').innerHTML =
                            `<div class="text-center py-8 text-red-400 text-sm col-span-3">${data.error || 'เกิดข้อผิดพลาด'}</div>`;
                        return;
                    }
                    pndData = data;
                    renderPndSummaryCards(data);
                    renderPndMonthlyTable(data);
                })
                .catch(() => { btn.textContent = 'โหลดข้อมูล'; btn.disabled = false; });
        }

        function renderPndSummaryCards(data) {
            document.getElementById('pndSummaryCards').innerHTML = `
                <div class="bg-white border border-slate-200 rounded-2xl p-5 flex gap-4 items-start shadow-sm">
                    <div class="w-1 h-12 bg-amber-500 rounded-full flex-shrink-0"></div>
                    <div><p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">ภ.ง.ด.3 (บุคคลธรรมดา)</p>
                    <p class="text-2xl font-extrabold text-amber-600">฿${formatNum(data.total_pnd3_wht)}</p>
                    <p class="text-[10px] text-slate-400 mt-1">ภาษีหัก ณ ที่จ่าย ปี ${data.year}</p></div>
                </div>
                <div class="bg-white border border-slate-200 rounded-2xl p-5 flex gap-4 items-start shadow-sm">
                    <div class="w-1 h-12 bg-rose-500 rounded-full flex-shrink-0"></div>
                    <div><p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">ภ.ง.ด.53 (นิติบุคคล)</p>
                    <p class="text-2xl font-extrabold text-rose-600">฿${formatNum(data.total_pnd53_wht)}</p>
                    <p class="text-[10px] text-slate-400 mt-1">ภาษีหัก ณ ที่จ่าย ปี ${data.year}</p></div>
                </div>
                <div class="bg-white border border-slate-200 rounded-2xl p-5 flex gap-4 items-start shadow-sm">
                    <div class="w-1 h-12 bg-blue-600 rounded-full flex-shrink-0"></div>
                    <div><p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">รวมทั้งหมด</p>
                    <p class="text-2xl font-extrabold text-blue-600">฿${formatNum(data.total_wht_all)}</p>
                    <p class="text-[10px] text-slate-400 mt-1">${data.entries.length} รายการที่มีการหัก WHT</p></div>
                </div>`;
        }

        function renderPndMonthlyTable(data) {
            const container = document.getElementById('pndMonthlyTable');
            if (!data.monthly_summary || data.monthly_summary.length === 0) {
                container.innerHTML = '<div class="text-center py-12 text-slate-400 text-sm">ไม่พบรายการ ภ.ง.ด. ในปีที่เลือก</div>';
                return;
            }
            const MONTH_TH = {'01':'มกราคม','02':'กุมภาพันธ์','03':'มีนาคม','04':'เมษายน','05':'พฤษภาคม','06':'มิถุนายน','07':'กรกฎาคม','08':'สิงหาคม','09':'กันยายน','10':'ตุลาคม','11':'พฤศจิกายน','12':'ธันวาคม'};
            const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

            const tableHead = `<tr class="bg-slate-50 border-b border-slate-100">
                <th class="px-4 py-2.5 text-[9px] font-bold text-slate-400 uppercase">วันที่</th>
                <th class="px-4 py-2.5 text-[9px] font-bold text-slate-400 uppercase">ผู้รับเงิน</th>
                <th class="px-4 py-2.5 text-[9px] font-bold text-slate-400 uppercase">เลขผู้เสียภาษี</th>
                <th class="px-4 py-2.5 text-[9px] font-bold text-slate-400 uppercase">รายละเอียด</th>
                <th class="px-4 py-2.5 text-[9px] font-bold text-slate-400 uppercase text-right">ยอดฐาน</th>
                <th class="px-4 py-2.5 text-[9px] font-bold text-slate-400 uppercase text-center">อัตรา</th>
                <th class="px-4 py-2.5 text-[9px] font-bold text-slate-400 uppercase text-right">ภาษีที่หัก</th>
            </tr>`;

            container.innerHTML = data.monthly_summary.map(m => {
                const mEntries = data.entries.filter(e => e.month === m.month_num);
                const pnd3 = mEntries.filter(e => e.pnd_type === 'ภ.ง.ด.3');
                const pnd53 = mEntries.filter(e => e.pnd_type !== 'ภ.ง.ด.3');

                const makeRows = (items, cls) => items.map(e => `
                    <tr class="border-b border-slate-50 hover:bg-slate-50/50 transition">
                        <td class="px-4 py-2.5 text-xs text-slate-500 whitespace-nowrap">${esc(e.date)}</td>
                        <td class="px-4 py-2.5 text-xs font-semibold text-slate-800 max-w-[160px] truncate">${esc(e.vendor)}</td>
                        <td class="px-4 py-2.5 text-xs text-slate-500">${esc(e.tax_id)}</td>
                        <td class="px-4 py-2.5 text-xs text-slate-600 max-w-[180px] truncate">${esc(e.description)}</td>
                        <td class="px-4 py-2.5 text-xs text-right tabular-nums font-semibold text-slate-700">฿${formatNum(e.base_amount)}</td>
                        <td class="px-4 py-2.5 text-xs text-center text-slate-500">${e.wht_rate > 0 ? e.wht_rate + '%' : '-'}</td>
                        <td class="px-4 py-2.5 text-xs text-right tabular-nums font-bold ${cls}">฿${formatNum(e.wht_amount)}</td>
                    </tr>`).join('');

                return `<div class="border border-slate-200 rounded-2xl overflow-hidden bg-white shadow-sm">
                    <div class="px-5 py-3 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2">
                        <h4 class="text-sm font-extrabold text-slate-900">${esc(m.month_th)} ${data.year}</h4>
                        <div class="flex items-center gap-3 text-xs">
                            ${m.pnd3_count > 0 ? `<span class="bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full font-bold text-[10px]">ภ.ง.ด.3: ฿${formatNum(m.pnd3_wht)} (${m.pnd3_count} ราย)</span>` : ''}
                            ${m.pnd53_count > 0 ? `<span class="bg-rose-50 text-rose-700 border border-rose-200 px-2 py-0.5 rounded-full font-bold text-[10px]">ภ.ง.ด.53: ฿${formatNum(m.pnd53_wht)} (${m.pnd53_count} ราย)</span>` : ''}
                            <span class="font-bold text-slate-700">รวม ฿${formatNum(m.total_wht)}</span>
                        </div>
                    </div>
                    ${pnd3.length > 0 ? `<div class="border-b border-slate-100">
                        <div class="px-5 py-1.5 bg-amber-50"><span class="text-[10px] font-bold text-amber-700 uppercase tracking-widest">ภ.ง.ด.3 — บุคคลธรรมดา</span></div>
                        <div class="overflow-x-auto"><table class="w-full text-left"><thead>${tableHead}</thead>
                        <tbody>${makeRows(pnd3,'text-amber-600')}</tbody>
                        <tfoot><tr class="bg-amber-50"><td colspan="6" class="px-4 py-2 text-xs font-bold text-amber-800 text-right">รวม ภ.ง.ด.3</td>
                        <td class="px-4 py-2 text-xs font-extrabold text-amber-700 text-right tabular-nums">฿${formatNum(m.pnd3_wht)}</td></tr></tfoot>
                        </table></div></div>` : ''}
                    ${pnd53.length > 0 ? `<div>
                        <div class="px-5 py-1.5 bg-rose-50"><span class="text-[10px] font-bold text-rose-700 uppercase tracking-widest">ภ.ง.ด.53 — นิติบุคคล</span></div>
                        <div class="overflow-x-auto"><table class="w-full text-left"><thead>${tableHead}</thead>
                        <tbody>${makeRows(pnd53,'text-rose-600')}</tbody>
                        <tfoot><tr class="bg-rose-50"><td colspan="6" class="px-4 py-2 text-xs font-bold text-rose-800 text-right">รวม ภ.ง.ด.53</td>
                        <td class="px-4 py-2 text-xs font-extrabold text-rose-700 text-right tabular-nums">฿${formatNum(m.pnd53_wht)}</td></tr></tfoot>
                        </table></div></div>` : ''}
                </div>`;
            }).join('');
        }

        function exportPndExcel() {
            if (!pndData || !pndData.entries) { alert('กรุณาโหลดข้อมูลก่อน'); return; }
            fetch('/api/dashboard/wht-export', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({entries: pndData.entries, year: pndData.year})
            }).then(r => {
                if (!r.ok) throw new Error('failed');
                return r.blob();
            }).then(blob => {
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = `WHT_Report_${pndData.year}.xlsx`;
                a.click();
            }).catch(() => alert('เกิดข้อผิดพลาดในการ Export'));
        }

        // ─── FILTER / SORTING LOGIC ─────────────────────────
        function applyAllFilters() {
            const dateVal = document.getElementById('filterDate').value;
            const searchVal = document.getElementById('filterSearch').value.trim().toLowerCase();
            const requesterVal = document.getElementById('filterRequester').value;
            const docTypeVal = document.getElementById('filterDocType').value;
            const statusVal = document.getElementById('filterStatus').value;
            const dateToggle = document.getElementById('dateToggle').checked; // true = upload date, false = doc date

            // Filter standardized expenses
            let filtered = allExpenses.filter(e => {
                // 1. Date filter
                if (dateVal) {
                    const cleanDateVal = dateVal.replace(/-/g, '');
                    const rowDate = cleanDate(e.date);
                    if (rowDate !== cleanDateVal) return false;
                }
                
                // 2. Text Search
                if (searchVal) {
                    const searchStr = `${e.merchant} ${e.details} ${e.ref_number} ${e.sheet_name}`.toLowerCase();
                    if (!searchStr.includes(searchVal)) return false;
                }

                // 3. Requester
                if (requesterVal && e.line_sender_name !== requesterVal) return false;

                // 4. Doc Type
                if (docTypeVal && e.sheet_name !== docTypeVal) return false;

                // 5. Status
                if (statusVal && e.status !== statusVal) return false;

                return true;
            });

            // Handle Active Tab Views
            if (currentTab === 'all') {
                renderGroupedExpenses(filtered);
            } else if (currentTab === 'vat') {
                // Only show invoices with VAT or WHT > 0
                const vatItems = filtered.filter(e => e.vat_amount > 0 || e.wht_amount > 0);
                renderTaxTable(vatItems);
            } else if (currentTab === 'unclear') {
                // Client-side search on unclear rows
                let filteredUnclear = unclearRows.filter(e => {
                    if (searchVal) {
                        return `${e.vendor} ${e.issues} ${e.sheet}`.toLowerCase().includes(searchVal);
                    }
                    return true;
                });
                renderUnclearTable(filteredUnclear);
            }
        }

        function cleanDate(dStr) {
            if (!dStr) return '';
            return dStr.replace(/\//g, '').replace(/-/g, '').trim();
        }

        // ─── RENDERING ALL EXPENSES (GROUPED BY MONTH) ────────
        function renderGroupedExpenses(expenses) {
            const container = document.getElementById('expenseListGrouped');
            const empty = document.getElementById('filterEmpty');

            if (!expenses || expenses.length === 0) {
                container.innerHTML = '';
                empty.classList.remove('hidden');
                return;
            }
            empty.classList.add('hidden');

            // Group by Month (e.g. "พฤษภาคม 2026", "เมษายน 2026")
            const groups = {};
            expenses.forEach(e => {
                const groupName = getMonthGroupName(e.date);
                if (!groups[groupName]) {
                    groups[groupName] = [];
                }
                groups[groupName].push(e);
            });

            // Get month groups sorted chronologically, with 'unknown' always last
            const groupKeys = Object.keys(groups).sort((a, b) => {
                if (a === 'unknown') return 1;
                if (b === 'unknown') return -1;
                return b.localeCompare(a);
            });

            // Render monthly summary card at top
            renderMonthlySummary(groups);

            container.innerHTML = groupKeys.map(k => {
                const monthNameTH = formatGroupNameTH(k);
                const items = groups[k];
                const monthTotal = items.reduce((acc, cur) => acc + (cur.net_amount || 0), 0);

                const rowsHtml = items.map(item => {
                    const statusBadgeClass = item.status === 'จ่ายแล้ว' 
                        ? 'text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200/60 dark:border-emerald-800/60' 
                        : 'text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/50 border border-amber-200/60 dark:border-amber-800/60';
                    const docTypeClass = item.sheet_name === 'สลิปโอนเงิน' 
                        ? 'text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-200/60 dark:border-indigo-800/60' 
                        : 'text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-950/50 border border-brand-200/60 dark:border-brand-800/60';
                    
                    const merchantDisplay = item.merchant && item.merchant !== '-' ? escHtml(item.merchant) : '<span class="text-surface-400">—</span>';
                    const detailsDisplay = item.details && item.details !== '-' ? escHtml(item.details) : '<span class="text-surface-400">—</span>';
                    const dateDisplay = item.date && item.date !== '-' ? escHtml(item.date) : '<span class="text-surface-400">—</span>';

                    return `
                    <tr class="hover:bg-surface-50/70 dark:hover:bg-surface-800/40 transition-colors cursor-pointer border-b border-surface-100 dark:border-surface-800/60" onclick="openEditModalFromRow(${JSON.stringify(item).replace(/"/g, '&quot;')})">
                        <td class="w-10 px-3 py-3.5 text-center" onclick="event.stopPropagation()">
                            <input type="checkbox" class="pv-checkbox w-4 h-4 rounded text-brand-600 border-surface-300 dark:border-surface-600 dark:bg-surface-800 focus:ring-brand-500 cursor-pointer" data-item="${escAttr(JSON.stringify(item))}" onchange="updatePVBatchButton()">
                        </td>
                        <td class="px-5 py-3.5 text-xs text-surface-500 dark:text-surface-400 whitespace-nowrap font-medium">${dateDisplay}</td>
                        <td class="px-5 py-3.5 whitespace-nowrap">
                            <span class="px-2.5 py-0.5 rounded-md text-[10px] font-semibold ${docTypeClass}">${escHtml(item.sheet_name)}</span>
                        </td>
                        <td class="px-5 py-3.5 whitespace-nowrap">
                            <p class="text-xs font-semibold text-surface-900 dark:text-white truncate max-w-[180px]">${merchantDisplay}</p>
                        </td>
                        <td class="px-5 py-3.5">
                            <p class="text-xs text-surface-600 dark:text-surface-300 truncate max-w-[260px]">${detailsDisplay}</p>
                        </td>
                        <td class="px-5 py-3.5 whitespace-nowrap">
                            <span class="text-xs text-surface-700 dark:text-surface-300 font-medium">${escHtml(item.line_sender_name || 'ไม่ระบุ')}</span>
                        </td>
                        <td class="px-5 py-3.5 whitespace-nowrap">
                            <span class="px-2 py-0.5 rounded-md text-[10px] font-semibold ${statusBadgeClass}">${escHtml(item.status)}</span>
                        </td>
                        <td class="px-5 py-3.5 text-xs font-bold text-surface-900 dark:text-white whitespace-nowrap tabular-nums">฿${formatNum(item.net_amount)}</td>
                        <td class="px-5 py-3.5 text-right whitespace-nowrap" onclick="event.stopPropagation()">
                            <div class="flex items-center justify-end gap-1">
                                <button onclick="openEditModalFromRow(${JSON.stringify(item).replace(/"/g, '&quot;')})" class="p-1.5 text-surface-400 hover:text-surface-900 dark:hover:text-white hover:bg-surface-100 dark:hover:bg-surface-800 rounded-lg transition" title="ดูรายละเอียด/แก้ไข">
                                    <i data-lucide="edit-3" class="w-4 h-4"></i>
                                </button>
                                <button onclick="deleteRowDirect('${escAttr(item.sheet_name)}', ${item.row_index})" class="p-1.5 text-surface-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg transition" title="ลบรายการ">
                                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                                </button>
                                <button onclick="openReplacementFromExpense(${JSON.stringify(item).replace(/"/g, '&quot;')})" class="p-1.5 text-surface-400 hover:text-amber-600 dark:hover:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-950/40 rounded-lg transition" title="สร้างใบแทนใบเสร็จ">
                                    <i data-lucide="receipt" class="w-4 h-4"></i>
                                </button>
                            </div>
                        </td>
                    </tr>`;
                }).join('');

                return `
                <div class="pt-6 first:pt-0">
                    <div class="flex items-center justify-between mb-3 px-1">
                        <div class="flex items-center gap-2.5">
                            <h4 class="text-xs font-bold text-surface-900 dark:text-white uppercase tracking-wider">${monthNameTH}</h4>
                            <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-400">${items.length} รายการ</span>
                            <button id="batchPVBtn" onclick="createBatchPaymentVoucher()" class="hidden ml-2 px-3 py-1 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-lg transition flex items-center gap-1.5 shadow-xs">
                                <i data-lucide="file-text" class="w-3.5 h-3.5"></i> ออกใบสำคัญจ่ายกลุ่ม (Payment Voucher)
                            </button>
                        </div>
                        <span class="text-xs font-semibold text-surface-700 dark:text-surface-300">ยอดรวม <span class="font-bold text-surface-900 dark:text-white tabular-nums">฿${formatNum(monthTotal)}</span></span>
                    </div>
                    <div class="overflow-x-auto border border-surface-200/80 dark:border-surface-800 rounded-xl bg-white dark:bg-surface-900 shadow-xs">
                        <table class="w-full text-left">
                            <thead>
                                <tr class="bg-surface-50 dark:bg-surface-800/60 border-b border-surface-200/80 dark:border-surface-800">
                                    <th class="w-10 px-3 py-3 text-center"><input type="checkbox" class="w-4 h-4 rounded text-brand-600 border-surface-300 dark:border-surface-600 dark:bg-surface-800 focus:ring-brand-500 cursor-pointer" onchange="toggleSelectAllPV(this)"></th>
                                    <th class="px-5 py-3 text-[10px] font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wider">วันที่</th>
                                    <th class="px-5 py-3 text-[10px] font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wider">ประเภทเอกสาร</th>
                                    <th class="px-5 py-3 text-[10px] font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wider">ร้านค้า</th>
                                    <th class="px-5 py-3 text-[10px] font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wider">รายละเอียด</th>
                                    <th class="px-5 py-3 text-[10px] font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wider">ผู้ขอเบิกจ่าย</th>
                                    <th class="px-5 py-3 text-[10px] font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wider">สถานะการจ่าย</th>
                                    <th class="px-5 py-3 text-[10px] font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wider">ยอดชำระ</th>
                                    <th class="px-5 py-3 text-[10px] font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wider text-right">จัดการ</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-surface-100 dark:divide-surface-800/60 bg-white dark:bg-surface-900">
                                ${rowsHtml}
                            </tbody>
                        </table>
                    </div>
                </div>`;
            }).join('');

            lucide.createIcons();
        }

        // Helper to extract sorting group key "YYYY-MM" (normalized to Gregorian for sorting)
        function getMonthGroupName(dateStr) {
            if (!dateStr || dateStr === '-') return 'unknown';
            const clean = dateStr.replace(/\//g, '-').trim();
            const parts = clean.split('-');
            if (parts.length === 3) {
                let y = 0;
                let m = '01';
                if (parts[2].length === 4) {
                    y = parseInt(parts[2], 10);
                    m = parts[1].padStart(2, '0');
                } else if (parts[0].length === 4) {
                    y = parseInt(parts[0], 10);
                    m = parts[1].padStart(2, '0');
                }
                if (y > 0) {
                    const gregorianYear = y > 2400 ? y - 543 : y;
                    return `${gregorianYear}-${m}`;
                }
            }
            return 'unknown';
        }

        const MONTH_TH = {
            '01': 'มกราคม', '02': 'กุมภาพันธ์', '03': 'มีนาคม', '04': 'เมษายน',
            '05': 'พฤษภาคม', '06': 'มิถุนายน', '07': 'กรกฎาคม', '08': 'สิงหาคม',
            '09': 'กันยายน', '10': 'ตุลาคม', '11': 'พฤศจิกายน', '12': 'ธันวาคม'
        };
        function formatGroupNameTH(key) {
            if (key === 'unknown') return 'ไม่ระบุเดือน / ไม่มีวันที่ในเอกสาร';
            const parts = key.split('-');
            let y = parseInt(parts[0], 10) || 0;
            const yearTH = y > 2400 ? y : y + 543;
            const monthName = MONTH_TH[parts[1]] || 'ไม่ระบุ';
            return `${monthName} ${yearTH}`;
        }

        // ─── RENDERING TAX INVOICES TABLE ───────────────────
        function renderTaxTable(items) {
            const tbody = document.getElementById('taxInvoicesTable');
            const empty = document.getElementById('filterEmpty');

            if (!items || items.length === 0) {
                tbody.innerHTML = '';
                empty.classList.remove('hidden');
                return;
            }
            empty.classList.add('hidden');

            tbody.innerHTML = items.map(item => {
                return `
                <tr class="table-row-hover transition cursor-pointer" onclick="openEditModalFromRow(${JSON.stringify(item).replace(/"/g, '&quot;')})">
                    <td class="px-6 py-4 text-xs text-slate-500 whitespace-nowrap">${escHtml(item.date)}</td>
                    <td class="px-6 py-4 whitespace-nowrap font-bold text-slate-800">${escHtml(item.merchant)}</td>
                    <td class="px-6 py-4 text-xs text-slate-600">${escHtml(item.details)}</td>
                    <td class="px-6 py-4 text-xs font-bold text-slate-800 tabular-nums">฿${formatNum(item.gross_amount)}</td>
                    <td class="px-6 py-4 text-xs font-bold text-emerald-600 tabular-nums">฿${formatNum(item.vat_amount)}</td>
                    <td class="px-6 py-4 text-xs font-bold text-amber-600 tabular-nums">฿${formatNum(item.wht_amount)}</td>
                    <td class="px-6 py-4 text-xs font-extrabold text-slate-900 tabular-nums">฿${formatNum(item.net_amount)}</td>
                    <td class="px-6 py-4 text-right whitespace-nowrap" onclick="event.stopPropagation()">
                        <button onclick="openEditModalFromRow(${JSON.stringify(item).replace(/"/g, '&quot;')})" class="p-1.5 text-slate-400 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition mr-1.5" title="ดูรายละเอียด/แก้ไข">
                            <i data-lucide="edit-3" class="w-4.5 h-4.5"></i>
                        </button>
                        <button onclick="deleteRowDirect('${escAttr(item.sheet_name)}', ${item.row_index})" class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition">
                            <i data-lucide="trash-2" class="w-4.5 h-4.5"></i>
                        </button>
                    </td>
                </tr>`;
            }).join('');

            lucide.createIcons();
        }

        // ─── RENDERING UNCLEAR SCANS TABLE ──────────────────
        function renderUnclearTable(rows) {
            const tbody  = document.getElementById('unclearScansTable');
            const empty  = document.getElementById('filterEmpty');

            if (rows.length === 0) {
                tbody.innerHTML = '';
                empty.classList.remove('hidden');
                return;
            }
            empty.classList.add('hidden');

            tbody.innerHTML = rows.map(item => {
                const fileHtml = buildFileButton(item);
                // Standardize item object for edit modal compatibility
                const standardizedItem = {
                    date: item.date,
                    merchant: item.vendor,
                    details: item.issues || 'ตรวจสอบข้อมูล',
                    net_amount: item.amount,
                    gross_amount: item.amount, // Default to same if unclear
                    vat_amount: 0,
                    wht_amount: 0,
                    status: 'ยังไม่จ่าย',
                    sheet_name: item.sheet,
                    row_index: item.row,
                    original_filename: '-',
                    link: item.link
                };
                const itemJson = JSON.stringify(standardizedItem).replace(/"/g, '&quot;');

                return `
                <tr class="table-row-hover transition cursor-pointer" onclick="openEditModalFromRow(${itemJson})">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="text-xs font-semibold text-slate-700">${escHtml(item.date)}</span>
                        ${item.upload_time ? `<div class="text-[10px] text-slate-400 mt-0.5"><i data-lucide="clock" class="w-2.5 h-2.5 inline mr-1"></i>${escHtml(item.upload_time)}</div>` : ''}
                    </td>
                    <td class="px-6 py-4">
                        <p class="text-xs font-bold text-slate-800">${escHtml(item.vendor)}</p>
                        <p class="text-[9px] text-slate-400 font-medium uppercase mt-0.5">${escHtml(item.sheet)} &middot; แถว ${item.row}</p>
                    </td>
                    <td class="px-6 py-4 text-xs font-bold text-slate-800 tabular-nums">฿${formatNum(item.amount)}</td>
                    <td class="px-6 py-4">
                        <span class="badge-amber px-2 py-0.5 rounded-md text-[9px] font-bold">${escHtml(item.issues)}</span>
                    </td>
                    <td class="px-6 py-4">${fileHtml}</td>
                    <td class="px-6 py-4 text-right">
                        <div class="flex items-center justify-end gap-2" onclick="event.stopPropagation()">
                            <button onclick="openEditModalFromRow(${itemJson})"
                                class="inline-flex items-center gap-1.5 px-2 py-1.5 text-[10px] font-semibold text-slate-700 bg-slate-50 border border-slate-200 hover:bg-slate-100 rounded-lg transition">
                                <i data-lucide="edit-3" class="w-3 h-3"></i> แก้ไข
                            </button>
                            <button onclick="openMoveModal('${escAttr(item.sheet)}', ${item.row})"
                                class="inline-flex items-center gap-1.5 px-2 py-1.5 text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 hover:bg-emerald-100 rounded-lg transition">
                                <i data-lucide="folder-symlink" class="w-3 h-3"></i> ย้าย
                            </button>
                        </div>
                    </td>
                </tr>`;
            }).join('');

            lucide.createIcons();
        }

        function buildFileButton(item) {
            if (!item.link) return `<span class="text-[10px] text-slate-400 italic">ไม่มีไฟล์</span>`;
            return `
                <button onclick="openMediaSidebar('${escAttr(item.link)}', '${escAttr(item.vendor)}', false)"
                    class="inline-flex items-center gap-1.5 px-2 py-1 text-[10px] font-semibold text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg transition">
                    <i data-lucide="file-text" class="w-3 h-3"></i> ดูไฟล์
                </button>`;
        }

        // ─── PREMIUM EDIT MODAL LOGIC ───────────────────────
        function openEditModalFromRow(item) {
            currentEditItem = item;
            
            // Set Left Pane Preview
            const frame = document.getElementById('editMediaFrame');
            const loading = document.getElementById('editMediaLoading');
            const typeBadge = document.getElementById('modalDocTypeBadge');
            const filenameLabel = document.getElementById('modalOriginalFilename');

            typeBadge.textContent = item.sheet_name;
            filenameLabel.textContent = item.original_filename && item.original_filename !== '-' ? item.original_filename : 'หลักฐานการชำระเงิน';
            
            loading.style.display = 'flex';
            frame.src = 'about:blank';
            currentEmbedZoom = 1.0;
            document.getElementById('zoomPercent').textContent = '100%';

            if (item.link && item.link.startsWith('http')) {
                const embedUrl = driveEmbedUrl(item.link);
                frame.onload = () => { loading.style.display = 'none'; };
                frame.src = embedUrl;
            } else {
                loading.style.display = 'none';
                frame.srcdoc = `
                    <div style="font-family:sans-serif; text-align:center; padding:50px; color:#64748b;">
                        <svg width="48" height="48" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" style="margin:0 auto 10px;"><path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                        <p style="font-size:13px; font-weight:600; margin:0;">ไม่มีลิงก์ไฟล์หรือเอกสารแนบ</p>
                    </div>`;
            }

            // Fill Form values
            document.getElementById('modalField-date').value = parseDateToInput(item.date);
            document.getElementById('modalField-requester').value = item.line_sender_name !== '-' ? item.line_sender_name : '';
            document.getElementById('modalField-details').value = item.details !== '-' ? item.details : '';
            document.getElementById('modalField-merchant').value = item.merchant !== '-' ? item.merchant : '';
            document.getElementById('modalField-taxId').value = item.tax_id !== '-' ? item.tax_id : '';
            document.getElementById('modalField-address').value = item.address !== '-' ? item.address : '';
            
            // Category-specific fields populate
            const ext = item.extracted_data || {};
            document.getElementById('modalField-receiver').value = item.receiver || ext.receiver || ext.payee_name || (item.merchant !== '-' ? item.merchant : '');
            document.getElementById('modalField-time').value = item.time || ext.time || '';
            document.getElementById('modalField-bankFrom').value = item.bank_from || ext.sender_bank || ext.bank_from || '';
            document.getElementById('modalField-bankTo').value = item.bank_to || ext.receiver_bank || ext.bank_to || '';
            document.getElementById('modalField-memo').value = item.memo || ext.memo || '';

            document.getElementById('modalField-whtType').value = item.wht_type || ext.wht_type || '-';
            document.getElementById('modalField-whtRate').value = item.wht_rate || ext.wht_rate || ext.wht_percent || '';
            document.getElementById('modalField-payerName').value = item.payer_name || ext.payer_name || '';
            document.getElementById('modalField-payeeName').value = item.payee_name || ext.payee_name || item.receiver || '';

            document.getElementById('modalField-expenseType').value = item.expense_type || ext.income_type || item.category || '';

            // Toggle category sections based on sheet_name
            const sName = (item.sheet_name || '').trim();
            const isSlip = sName === 'สลิปโอนเงิน';
            const isWht = sName === 'ใบหัก ณ ที่จ่าย';
            const isReceipt = sName === 'ใบเสร็จ/ใบกำกับภาษี';
            const isGenExp = sName === 'บันทึกค่าใช้จ่าย';

            const slipSec = document.getElementById('modalSection-slip');
            const whtSec = document.getElementById('modalSection-wht');
            const expSec = document.getElementById('modalSection-expense');

            if (slipSec) slipSec.classList.toggle('hidden', !isSlip);
            if (whtSec) whtSec.classList.toggle('hidden', !isWht && !isReceipt);
            if (expSec) expSec.classList.toggle('hidden', !isGenExp && !isReceipt);

            // Set branch radio
            const branchType = item.branch && item.branch.includes('00000') ? 'สำนักงานใหญ่' : (item.branch !== '-' ? 'สาขา' : 'ไม่มีสาขา');
            document.querySelectorAll('input[name="branch_type"]').forEach(r => {
                r.checked = r.value === branchType;
            });

            // Set payment status radio
            const pStatus = item.status === 'จ่ายแล้ว' ? 'จ่ายแล้ว' : 'ยังไม่จ่าย';
            document.querySelectorAll('input[name="payment_status"]').forEach(r => {
                r.checked = r.value === pStatus;
            });

            // Set Tax checkbox and section visibility
            const hasTax = item.vat_amount > 0 || (item.ref_number && item.ref_number !== '-');
            document.getElementById('modalField-hasTaxInvoice').checked = hasTax;
            document.getElementById('modalField-refNumber').value = item.ref_number !== '-' ? item.ref_number : '';
            toggleTaxInvoiceInput();

            // Itemize Summaries fields
            document.getElementById('modalItemTitle').textContent = item.details !== '-' ? item.details : 'ค่าใช้จ่าย';
            document.getElementById('modalItemAmount').textContent = `฿${formatNum(item.net_amount)}`;
            
            document.getElementById('modalField-grossAmount').value = item.gross_amount;
            document.getElementById('modalField-vatAmount').value = item.vat_amount;
            document.getElementById('modalField-whtAmount').value = item.wht_amount;
            document.getElementById('modalField-netAmount').value = item.net_amount;

            // Reset tabs
            switchFormTab('info');

            // Open Modal
            document.getElementById('editExpenseModal').classList.remove('hidden');
        }

        function closeEditModal() {
            document.getElementById('editExpenseModal').classList.add('hidden');
            document.getElementById('editMediaFrame').src = 'about:blank';
        }

        function switchFormTab(tab) {
            document.querySelectorAll('#formTab-info, #formTab-summary').forEach(btn => {
                btn.classList.toggle('active', btn.id === `formTab-${tab}`);
            });
            document.getElementById('formContent-info').classList.toggle('hidden', tab !== 'info');
            document.getElementById('formContent-summary').classList.toggle('hidden', tab !== 'summary');
        }

        function toggleTaxInvoiceInput() {
            const hasTax = document.getElementById('modalField-hasTaxInvoice').checked;
            document.getElementById('taxInvoiceSection').classList.toggle('hidden', !hasTax);
        }

        function toggleManualTotals() {
            const manual = document.getElementById('modalField-manualEdit').checked;
            document.getElementById('modalField-grossAmount').readOnly = !manual;
            document.getElementById('modalField-vatAmount').readOnly = !manual;
            document.getElementById('modalField-whtAmount').readOnly = !manual;
        }

        // Automatic Math Recalculation
        function recalculateTotals() {
            const manual = document.getElementById('modalField-manualEdit').checked;
            if (manual) return;

            const gross = parseFloat(document.getElementById('modalField-grossAmount').value) || 0.0;
            const discount = parseFloat(document.getElementById('modalField-discount').value) || 0.0;
            const vat = parseFloat(document.getElementById('modalField-vatAmount').value) || 0.0;
            const wht = parseFloat(document.getElementById('modalField-whtAmount').value) || 0.0;

            const net = (gross - discount + vat - wht).toFixed(2);
            document.getElementById('modalField-netAmount').value = net;
            document.getElementById('modalItemAmount').textContent = `฿${formatNum(parseFloat(net))}`;
        }

        // Date conversions helper
        function parseDateToInput(dStr) {
            if (!dStr || dStr === '-') return '';
            // Assume format DD/MM/YYYY
            const parts = dStr.split('/');
            if (parts.length === 3) {
                return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
            }
            return dStr;
        }

        function parseInputToDate(inputVal) {
            if (!inputVal) return '-';
            const parts = inputVal.split('-');
            if (parts.length === 3) {
                return `${parts[2]}/${parts[1]}/${parts[0]}`;
            }
            return inputVal;
        }

        function adjustEmbedZoom(multiplier) {
            currentEmbedZoom = Math.min(Math.max(currentEmbedZoom * multiplier, 0.5), 3.0);
            const frame = document.getElementById('editMediaFrame');
            frame.style.transform = `scale(${currentEmbedZoom})`;
            frame.style.transformOrigin = 'top left';
            frame.style.width = `${100 / currentEmbedZoom}%`;
            frame.style.height = `${100 / currentEmbedZoom}%`;
            document.getElementById('zoomPercent').textContent = `${Math.round(currentEmbedZoom * 100)}%`;
        }

        // ─── CORE UPDATE & DELETE SYNC VIA BACKEND APIs ───────
        function saveExpenseRow() {
            const btn = document.getElementById('btnSaveExpense');
            btn.disabled = true;
            btn.innerHTML = '<div class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full spinning"></div> กำลังบันทึก...';

            const status = document.querySelector('input[name="payment_status"]:checked').value;
            const branch = document.querySelector('input[name="branch_type"]:checked').value;
            const dateInput = document.getElementById('modalField-date').value;

            const fields = {
                "date": parseInputToDate(dateInput),
                "line_sender_name": document.getElementById('modalField-requester').value,
                "details": document.getElementById('modalField-details').value,
                "merchant": document.getElementById('modalField-merchant').value,
                "tax_id": document.getElementById('modalField-taxId').value,
                "address": document.getElementById('modalField-address').value,
                "branch": branch === 'สำนักงานใหญ่' ? "'00000" : (branch === 'สาขา' ? "'00001" : '-'),
                "status": status,
                "net_amount": document.getElementById('modalField-netAmount').value,
                "gross_amount": document.getElementById('modalField-grossAmount').value,
                "vat_amount": document.getElementById('modalField-vatAmount').value,
                "wht_amount": document.getElementById('modalField-whtAmount').value,
                "ref_number": document.getElementById('modalField-hasTaxInvoice').checked ? document.getElementById('modalField-refNumber').value : '-',
                "receiver": document.getElementById('modalField-receiver')?.value || '-',
                "payer_name": document.getElementById('modalField-payerName')?.value || '-',
                "payee_name": document.getElementById('modalField-payeeName')?.value || '-',
                "time": document.getElementById('modalField-time')?.value || '-',
                "bank_from": document.getElementById('modalField-bankFrom')?.value || '-',
                "bank_to": document.getElementById('modalField-bankTo')?.value || '-',
                "memo": document.getElementById('modalField-memo')?.value || '-',
                "wht_type": document.getElementById('modalField-whtType')?.value || '-',
                "wht_rate": document.getElementById('modalField-whtRate')?.value || '-',
                "expense_type": document.getElementById('modalField-expenseType')?.value || '-'
            };

            fetch('/api/dashboard/update-expense', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sheet_name: currentEditItem.sheet_name,
                    row_index: currentEditItem.row_index,
                    fields: fields
                })
            })
            .then(r => r.json())
            .then(data => {
                btn.disabled = false;
                btn.innerHTML = '<i data-lucide="save" class="w-4 h-4"></i> บันทึกข้อมูล';
                lucide.createIcons();

                if (data.ok) {
                    closeEditModal();
                    loadDashboardData();
                } else {
                    alert('ไม่สามารถบันทึกได้: ' + (data.error || 'ข้อผิดพลาดหลังบ้าน'));
                }
            })
            .catch(err => {
                btn.disabled = false;
                btn.innerHTML = '<i data-lucide="save" class="w-4 h-4"></i> บันทึกข้อมูล';
                lucide.createIcons();
                alert('เกิดข้อผิดพลาดในการเชื่อมต่อเครือข่าย');
            });
        }

        function deleteExpenseRow() {
            if (!confirm(`คุณแน่ใจว่าต้องการลบรายการของ "${currentEditItem.merchant}" แถว ${currentEditItem.row_index} ออกอย่างถาวรใช่หรือไม่?`)) return;

            fetch('/api/dashboard/delete-expense', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sheet_name: currentEditItem.sheet_name,
                    row_index: currentEditItem.row_index
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.ok) {
                    closeEditModal();
                    loadDashboardData();
                } else {
                    alert('ไม่สามารถลบรายการได้: ' + (data.error || 'ข้อผิดพลาดหลังบ้าน'));
                }
            })
            .catch(err => {
                alert('เกิดข้อผิดพลาดในการเชื่อมต่อเครือข่าย');
            });
        }

        function deleteRowDirect(sheetName, rowIndex) {
            if (!confirm(`คุณแน่ใจว่าต้องการลบรายการนี้ แถว ${rowIndex} ออกอย่างถาวรใช่หรือไม่?`)) return;

            fetch('/api/dashboard/delete-expense', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sheet_name: sheetName,
                    row_index: rowIndex
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.ok) {
                    loadDashboardData();
                } else {
                    alert('ล้มเหลว: ' + (data.error || 'ไม่พบแถว'));
                }
            });
        }

        function downloadFullExcel() {
            // Generates an Excel report of the current sheet view
            const base = window.location.origin;
            window.open(`${base}/api/reconciliation/download-filtered`, '_blank');
        }

        // ─── MEDIA SIDEBAR ───────────────────────────────────
        function openMediaSidebar(rawUrl, name) {
            const sidebar  = document.getElementById('mediaSidebar');
            const overlay  = document.getElementById('mediaSidebarOverlay');
            const frame    = document.getElementById('mediaFrame');
            const loading  = document.getElementById('sidebarLoading');
            const openLink = document.getElementById('sidebarOpenLink');
            const fileName = document.getElementById('sidebarFileName');

            fileName.textContent = name || 'ไฟล์แนบ';
            openLink.href = rawUrl;
            loading.style.display = 'flex';

            frame.src = 'about:blank';
            const embedUrl = driveEmbedUrl(rawUrl);
            frame.onload = () => { loading.style.display = 'none'; };
            frame.src = embedUrl;

            sidebar.classList.add('open');
            overlay.classList.add('active');
            lucide.createIcons();
        }

        function closeMediaSidebar() {
            const sidebar = document.getElementById('mediaSidebar');
            const overlay = document.getElementById('mediaSidebarOverlay');
            const frame   = document.getElementById('mediaFrame');

            sidebar.classList.remove('open');
            overlay.classList.remove('active');

            setTimeout(() => {
                frame.src = 'about:blank';
            }, 350);
        }

        function driveEmbedUrl(url) {
            if (url.includes('/preview')) return url;
            const patterns = [
                /drive\.google\.com\/file\/d\/([a-zA-Z0-9_-]+)/,
                /drive\.google\.com\/open\?id=([a-zA-Z0-9_-]+)/,
                /id=([a-zA-Z0-9_-]+)/
            ];
            for (const re of patterns) {
                const m = url.match(re);
                if (m) return `https://drive.google.com/file/d/${m[1]}/preview`;
            }
            return `https://docs.google.com/viewer?url=${encodeURIComponent(url)}&embedded=true`;
        }

        // ─── MOVE MODAL ──────────────────────────────────────
        function openMoveModal(sheet, row) {
            document.getElementById('moveFromSheet').value = sheet;
            document.getElementById('moveRow').value = row;

            const sel = document.getElementById('moveToSheet');
            sel.innerHTML = '<option value="">-- เลือกชีตปลายทาง --</option>';
            globalSheetsList.forEach(s => {
                if (s !== sheet && !['Dashboard','แดชบอร์ด','Sheet1'].includes(s)) {
                    sel.innerHTML += `<option value="${escHtml(s)}">${escHtml(s)}</option>`;
                }
            });

            document.getElementById('moveModal').classList.remove('hidden');
            lucide.createIcons();
        }

        function closeMoveModal() {
            document.getElementById('moveModal').classList.add('hidden');
        }

        function submitMoveExpense(e) {
            e.preventDefault();
            const from = document.getElementById('moveFromSheet').value;
            const row  = parseInt(document.getElementById('moveRow').value);
            const to   = document.getElementById('moveToSheet').value;
            const btn  = document.getElementById('moveSubmitBtn');

            if (!to) return;

            btn.disabled = true;
            btn.innerHTML = '<div class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full spinning"></div> กำลังย้าย...';

            fetch('/api/reconciliation/move-row', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ from_sheet: from, row_index: row, to_sheet: to })
            })
            .then(r => r.json())
            .then(data => {
                btn.disabled = false;
                btn.innerHTML = '<i data-lucide="check" class="w-3.5 h-3.5"></i> ย้ายรายการ';
                lucide.createIcons();
                if (data.ok) {
                    closeMoveModal();
                    loadDashboardData();
                } else {
                    alert('ล้มเหลว: ' + (data.error || 'ไม่ทราบสาเหตุ'));
                }
            })
            .catch(() => {
                btn.disabled = false;
                btn.innerHTML = '<i data-lucide="check" class="w-3.5 h-3.5"></i> ย้ายรายการ';
                lucide.createIcons();
            });
        }

        // ─── UTILS ───────────────────────────────────────────
        function formatNum(n) {
            return (n || 0).toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }

        function animateValue(id, end) {
            const el = document.getElementById(id);
            if (!el) return;
            const duration = 1000;
            let start = null;
            const step = ts => {
                if (!start) start = ts;
                const p = Math.min((ts - start) / duration, 1);
                el.textContent = formatNum(p * end);
                if (p < 1) requestAnimationFrame(step);
            };
            requestAnimationFrame(step);
        }

        function escHtml(s) {
            return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
        }
        function escAttr(s) {
            return String(s || '').replace(/'/g,"\\'").replace(/"/g,'&quot;');
        }

        function showError(msg) {
            document.getElementById('catList').innerHTML =
                `<div class="text-center py-8 text-rose-400 text-sm">เกิดข้อผิดพลาด: ${escHtml(msg)}</div>`;
        }
