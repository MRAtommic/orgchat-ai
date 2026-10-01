/**
 * 🏥 Pharmacy Stock Management System - Frontend App
 * Dynamic reactive UI with Light/Dark Mode, QR Scanner, CRUD, and Dispensing Flow.
 */

let allDrugs = [];
let currentTab = 'inventory';
let html5QrScanner = null;
let selectedDrugForDispense = null;

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    loadDashboardStats();
    loadDrugs();
    loadDispensingLogs();
    setupEventListeners();

    // Check if opened via scanned URL query param: ?scan=MED-0001 or ?dispense=MED-0001
    const urlParams = new URLSearchParams(window.location.search);
    const codeParam = urlParams.get('scan') || urlParams.get('code') || urlParams.get('dispense');
    if (codeParam) {
        setTimeout(() => handleScannedCode(codeParam), 600);
    }

    // Check Google OAuth redirect result
    const googleConnected = urlParams.get('google_connected');
    const googleEmail = urlParams.get('email');
    const googleError = urlParams.get('google_error');

    if (googleConnected) {
        setTimeout(() => {
            showToast(`🎉 เชื่อมต่อ Google สำเร็จแล้ว! สร้างชีตและโฟลเดอร์เรียบร้อย (${googleEmail || 'Google Account'})`, 'success');
            openGoogleSettingsModal();
        }, 500);
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (googleError) {
        setTimeout(() => {
            showToast(`⚠️ เกิดข้อผิดพลาดในการเชื่อมต่อ Google: ${googleError}`, 'error');
            openGoogleSettingsModal();
        }, 500);
        window.history.replaceState({}, document.title, window.location.pathname);
    }
});

// ─────────────────────────────────────────────────────────────
// Theme Switcher (Dark / Light Mode)
// ─────────────────────────────────────────────────────────────

function initTheme() {
    const savedTheme = localStorage.getItem('pharmacy_theme') || 'light';
    setTheme(savedTheme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    setTheme(next);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('pharmacy_theme', theme);
    
    const themeIcon = document.getElementById('themeIcon');
    const themeText = document.getElementById('themeText');
    if (themeIcon) {
        themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
    if (themeText) {
        themeText.innerText = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
    }
}

// ─────────────────────────────────────────────────────────────
// Navigation & Tab Switching
// ─────────────────────────────────────────────────────────────

function switchTab(tabName) {
    currentTab = tabName;
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    document.querySelectorAll('.mobile-nav-item').forEach(item => {
        if (item.dataset.tab) {
            item.classList.toggle('active', item.dataset.tab === tabName);
        }
    });

    document.getElementById('view-inventory').style.display = tabName === 'inventory' ? 'block' : 'none';
    document.getElementById('view-logs').style.display = tabName === 'logs' ? 'block' : 'none';
    document.getElementById('view-scanner').style.display = tabName === 'scanner' ? 'block' : 'none';

    if (tabName === 'scanner') {
        startScanner();
    } else {
        stopScanner();
    }

    if (tabName === 'logs') {
        loadDispensingLogs();
    }
}

function updateMobileNav(tabName) {
    document.querySelectorAll('.mobile-nav-item').forEach(item => {
        if (item.dataset.tab) {
            item.classList.toggle('active', item.dataset.tab === tabName);
        }
    });
}

// ─────────────────────────────────────────────────────────────
// Dashboard Statistics
// ─────────────────────────────────────────────────────────────

async function loadDashboardStats() {
    try {
        const res = await fetch('/api/dashboard/stats');
        const data = await res.json();
        if (data.ok) {
            const s = data.stats;
            document.getElementById('statTotalDrugs').innerText = s.total_drugs || 0;
            document.getElementById('statTotalUnits').innerText = (s.total_units || 0).toLocaleString();
            document.getElementById('statLowStock').innerText = s.low_stock_count || 0;
            document.getElementById('statTodayDispensed').innerText = s.today_units_dispensed || 0;

            const dot = document.getElementById('sheetStatusDot');
            const text = document.getElementById('sheetStatusText');
            if (dot && text) {
                if (s.google_sheet_connected) {
                    dot.className = 'status-dot active';
                    text.innerText = 'Google Synced';
                } else {
                    dot.className = 'status-dot warning';
                    text.innerText = 'Local Cache';
                }
            }
        }
    } catch (e) {
        console.error('Error loading stats:', e);
    }
}

// ─────────────────────────────────────────────────────────────
// Drug Catalog & Inventory Management (CRUD)
// ─────────────────────────────────────────────────────────────

async function loadDrugs() {
    const search = document.getElementById('drugSearchInput')?.value || '';
    const category = document.getElementById('categoryFilter')?.value || 'all';
    const lowStockOnly = document.getElementById('lowStockCheckbox')?.checked ? '1' : '0';

    const url = `/api/drugs?q=${encodeURIComponent(search)}&category=${encodeURIComponent(category)}&low_stock=${lowStockOnly}`;
    try {
        const res = await fetch(url);
        const data = await res.json();
        if (data.ok) {
            allDrugs = data.drugs;
            renderDrugsTable(allDrugs);
        }
    } catch (e) {
        console.error('Error loading drugs:', e);
    }
}

function renderDrugsTable(drugs) {
    const tbody = document.getElementById('drugsTableBody');
    const cardsContainer = document.getElementById('drugsMobileCards');

    if (!drugs || drugs.length === 0) {
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
                        <i class="fas fa-prescription-bottle" style="font-size: 2rem; color: var(--text-subtle); margin-bottom: 0.5rem; display: block;"></i>
                        ไม่พบรายการยาตามเงื่อนไขที่ค้นหา
                    </td>
                </tr>
            `;
        }
        if (cardsContainer) {
            cardsContainer.innerHTML = `
                <div style="text-align: center; padding: 2.5rem 1rem; color: var(--text-muted); background: var(--bg-surface); border-radius: var(--radius-md); border: 1px dashed var(--border-default);">
                    <i class="fas fa-prescription-bottle" style="font-size: 2rem; color: var(--text-subtle); margin-bottom: 0.5rem; display: block;"></i>
                    ไม่พบรายการยาตามเงื่อนไข
                </div>
            `;
        }
        return;
    }

    if (tbody) {
        tbody.innerHTML = drugs.map(d => {
            const isLow = d.stock_qty <= d.min_threshold;
            const stockBadge = isLow
                ? `<span class="badge badge-danger"><i class="fas fa-circle-exclamation"></i> ใกล้หมด (${d.stock_qty} ${d.unit})</span>`
                : `<span class="badge badge-success"><i class="fas fa-check"></i> ${d.stock_qty} ${d.unit}</span>`;

            return `
                <tr>
                    <td>
                        <span class="code-pill">${escapeHtml(d.code)}</span>
                    </td>
                    <td>
                        <div style="font-weight: 700; color: var(--text-primary); font-size: 0.875rem;">${escapeHtml(d.name)}</div>
                        ${d.generic_name ? `<div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.1rem;">${escapeHtml(d.generic_name)}</div>` : ''}
                    </td>
                    <td>
                        <span class="badge badge-teal">${escapeHtml(d.category)}</span>
                    </td>
                    <td>
                        <span style="font-size: 0.8125rem; color: var(--text-secondary);">${escapeHtml(d.dosage_form || '-')}</span>
                    </td>
                    <td>
                        ${stockBadge}
                    </td>
                    <td>
                        <span style="font-size: 0.8125rem; color: var(--text-muted);">${escapeHtml(d.location || '-')}</span>
                    </td>
                    <td style="text-align: right;">
                        <div style="display: inline-flex; gap: 0.35rem; align-items: center;">
                            <button class="btn btn-outline" title="ตัดจ่ายยานี้" onclick="openDispenseModalForDrug(${d.id})" style="height: 30px; padding: 0 0.6rem; font-size: 0.75rem; color: var(--rose-600); border-color: var(--rose-100);">
                                <i class="fas fa-minus"></i> ตัดสต็อก
                            </button>
                            <button class="btn btn-outline btn-icon" title="พิมพ์ QR Code" onclick="openQrModal(${d.id})" style="height: 30px; width: 30px; font-size: 0.75rem;">
                                <i class="fas fa-qrcode"></i>
                            </button>
                            <button class="btn btn-outline btn-icon" title="แก้ไขข้อมูลยา" onclick="openEditDrugModal(${d.id})" style="height: 30px; width: 30px; font-size: 0.75rem;">
                                <i class="fas fa-pen"></i>
                            </button>
                            <button class="btn btn-outline btn-icon" title="ลบยา" onclick="confirmDeleteDrug(${d.id})" style="height: 30px; width: 30px; font-size: 0.75rem; color: var(--text-subtle);">
                                <i class="fas fa-trash-can"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    if (cardsContainer) {
        cardsContainer.innerHTML = drugs.map(d => {
            const isLow = d.stock_qty <= d.min_threshold;
            const stockBadge = isLow
                ? `<span class="badge badge-danger">ใกล้หมด (${d.stock_qty})</span>`
                : `<span class="badge badge-success">${d.stock_qty} ${d.unit}</span>`;

            return `
                <div class="drug-mobile-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.35rem;">
                        <div style="flex: 1;">
                            <span class="code-pill" style="font-size: 0.7rem;">${escapeHtml(d.code)}</span>
                            <div style="font-weight: 700; font-size: 0.95rem; color: var(--text-primary); margin-top: 0.2rem;">${escapeHtml(d.name)}</div>
                            ${d.generic_name ? `<div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(d.generic_name)}</div>` : ''}
                        </div>
                        <div style="text-align: right;">
                            ${stockBadge}
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 0.4rem; align-items: center; margin: 0.5rem 0; flex-wrap: wrap;">
                        <span class="badge badge-teal" style="font-size: 0.7rem;">${escapeHtml(d.category)}</span>
                        <span style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(d.dosage_form || 'เม็ด')}</span>
                        ${d.location ? `<span style="font-size: 0.75rem; color: var(--text-muted);"><i class="fas fa-location-dot"></i> ${escapeHtml(d.location)}</span>` : ''}
                        ${d.price ? `<span style="font-size: 0.75rem; color: var(--brand-600); font-weight: 700;">฿${d.price}</span>` : ''}
                    </div>

                    <div style="display: flex; gap: 0.35rem; margin-top: 0.65rem; padding-top: 0.65rem; border-top: 1px solid var(--border-subtle);">
                        <button class="btn btn-outline" onclick="openDispenseModalForDrug(${d.id})" style="flex: 1; height: 34px; font-size: 0.8rem; color: var(--rose-600); border-color: var(--rose-100);">
                            <i class="fas fa-minus"></i> ตัดสต็อก
                        </button>
                        <button class="btn btn-outline btn-icon" title="QR Code" onclick="openQrModal(${d.id})" style="height: 34px; width: 34px;">
                            <i class="fas fa-qrcode"></i>
                        </button>
                        <button class="btn btn-outline btn-icon" title="แก้ไข" onclick="openEditDrugModal(${d.id})" style="height: 34px; width: 34px;">
                            <i class="fas fa-pen"></i>
                        </button>
                        <button class="btn btn-outline btn-icon" title="ลบ" onclick="confirmDeleteDrug(${d.id})" style="height: 34px; width: 34px; color: var(--text-subtle);">
                            <i class="fas fa-trash-can"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }
}

// ─────────────────────────────────────────────────────────────
// Modal Operations (Add / Edit Drug)
// ─────────────────────────────────────────────────────────────

function openAddDrugModal() {
    const titleEl = document.getElementById('drugModalTitle');
    if (titleEl) titleEl.innerText = '➕ เพิ่มยาใหม่เข้าคลัง';
    const form = document.getElementById('drugForm');
    if (form) form.reset();
    const formId = document.getElementById('drugFormId');
    if (formId) formId.value = '';
    const modal = document.getElementById('drugModal');
    if (modal) modal.classList.add('active');
}

function openEditDrugModal(id) {
    const numId = Number(id);
    const drug = allDrugs.find(d => Number(d.id) === numId || d.id == id);
    if (!drug) {
        console.warn('Drug not found for id:', id, allDrugs);
        showToast('ไม่พบข้อมูลยานี้ในระบบ', 'warning');
        return;
    }

    const setVal = (elId, val) => {
        const el = document.getElementById(elId);
        if (el) el.value = val ?? '';
    };

    const titleEl = document.getElementById('drugModalTitle');
    if (titleEl) titleEl.innerText = '✏️ แก้ไขข้อมูลยา';

    setVal('drugFormId', drug.id);
    setVal('drugCodeInput', drug.code || '');
    setVal('drugNameInput', drug.name || '');
    setVal('drugGenericInput', drug.generic_name || '');
    setVal('drugCategoryInput', drug.category || 'ทั่วไป');
    setVal('drugDosageInput', drug.dosage_form || 'เม็ด (Tablet)');
    setVal('drugStrengthInput', drug.strength || '');
    setVal('drugStockInput', drug.stock_qty || 0);
    setVal('drugUnitInput', drug.unit || 'เม็ด');
    setVal('drugMinInput', drug.min_threshold || 10);
    setVal('drugPriceInput', drug.price || 0);
    setVal('drugCostInput', drug.cost || 0);
    setVal('drugExpiryInput', drug.expiry_date || '');
    setVal('drugLocationInput', drug.location || '');
    setVal('drugInstructionsInput', drug.instructions || '');

    const modal = document.getElementById('drugModal');
    if (modal) {
        modal.classList.add('active');
    }
}

function closeDrugModal() {
    const modal = document.getElementById('drugModal');
    if (modal) modal.classList.remove('active');
}

async function saveDrug(e) {
    e.preventDefault();
    const id = document.getElementById('drugFormId')?.value;
    const isEdit = Boolean(id);

    const getVal = (elId, defaultVal = '') => {
        const el = document.getElementById(elId);
        return el ? el.value.trim() : defaultVal;
    };

    const payload = {
        code: getVal('drugCodeInput'),
        name: getVal('drugNameInput'),
        generic_name: getVal('drugGenericInput'),
        category: getVal('drugCategoryInput', 'ทั่วไป'),
        dosage_form: getVal('drugDosageInput', 'เม็ด (Tablet)'),
        strength: getVal('drugStrengthInput'),
        stock_qty: parseInt(getVal('drugStockInput', '0')) || 0,
        unit: getVal('drugUnitInput', 'เม็ด'),
        min_threshold: parseInt(getVal('drugMinInput', '10')) || 10,
        price: parseFloat(getVal('drugPriceInput', '0')) || 0,
        cost: parseFloat(getVal('drugCostInput', '0')) || 0,
        expiry_date: getVal('drugExpiryInput'),
        location: getVal('drugLocationInput'),
        instructions: getVal('drugInstructionsInput')
    };

    if (!payload.name) {
        alert('กรุณากรอกชื่อยา');
        return;
    }

    try {
        const url = isEdit ? `/api/drugs/${id}` : '/api/drugs';
        const method = isEdit ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.ok) {
            closeDrugModal();
            loadDrugs();
            loadDashboardStats();
            showToast(isEdit ? 'แก้ไขข้อมูลยาและซิงก์ Sheet แล้ว' : 'เพิ่มยาใหม่และเขียนลง Google Sheet สำเร็จ!', 'success');
        } else {
            alert('เกิดข้อผิดพลาด: ' + (data.error || 'Unknown error'));
        }
    } catch (e) {
        console.error('Save drug error:', e);
        alert('ไม่สามารถบันทึกข้อมูลได้');
    }
}

async function confirmDeleteDrug(id) {
    const numId = Number(id);
    const drug = allDrugs.find(d => Number(d.id) === numId || d.id == id);
    const name = drug ? drug.name : 'ยานี้';
    if (!confirm(`คุณต้องการลบยา '${name}' ออกจากคลังยาใช่หรือไม่?\n(ระบบจะอัปเดตลง Google Sheet อัตโนมัติ)`)) {
        return;
    }
    try {
        const res = await fetch(`/api/drugs/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.ok) {
            loadDrugs();
            loadDashboardStats();
            showToast(`ลบยา '${name}' เรียบร้อยแล้ว`, 'info');
        }
    } catch (e) {
        console.error('Delete error:', e);
    }
}

// ─────────────────────────────────────────────────────────────
// Stock Dispensing Modal (Stock Deduction)
// ─────────────────────────────────────────────────────────────

function openDispenseModalForDrug(id) {
    const drug = allDrugs.find(d => d.id === id);
    if (!drug) return;

    selectedDrugForDispense = drug;
    document.getElementById('dispenseDrugName').innerText = drug.name;
    document.getElementById('dispenseDrugCode').innerText = `รหัส: ${drug.code} • คงเหลือ: ${drug.stock_qty} ${drug.unit}`;
    document.getElementById('dispenseQtyInput').value = 1;
    document.getElementById('dispenseQtyInput').max = drug.stock_qty;
    document.getElementById('dispenseUnitLabel').innerText = drug.unit;
    document.getElementById('dispensePatientInput').value = '';
    document.getElementById('dispenseNoteInput').value = '';

    document.getElementById('dispenseModal').classList.add('active');
}

function closeDispenseModal() {
    document.getElementById('dispenseModal').classList.remove('active');
    selectedDrugForDispense = null;
}

async function submitDispense(e) {
    e.preventDefault();
    if (!selectedDrugForDispense) return;

    const qty = parseInt(document.getElementById('dispenseQtyInput').value) || 1;
    const patient = document.getElementById('dispensePatientInput').value.trim();
    const notes = document.getElementById('dispenseNoteInput').value.trim();
    const dispenser = document.getElementById('dispenserNameInput')?.value || 'เภสัชกร/เจ้าหน้าที่';

    try {
        const res = await fetch('/api/dispense', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                drug_id: selectedDrugForDispense.id,
                quantity: qty,
                channel: 'WEB_MANUAL',
                dispensed_by: dispenser,
                patient_name: patient,
                notes: notes
            })
        });
        const data = await res.json();
        if (data.ok) {
            closeDispenseModal();
            loadDrugs();
            loadDashboardStats();
            loadDispensingLogs();
            showToast(`✅ ${data.message}`, 'success');
        } else {
            alert('ไม่สามารถตัดสต็อกได้: ' + (data.error || 'Unknown error'));
        }
    } catch (e) {
        console.error('Dispense error:', e);
        alert('เกิดข้อผิดพลาดในการตัดสต็อก');
    }
}

// ─────────────────────────────────────────────────────────────
// Dispensing Logs (Audit History)
// ─────────────────────────────────────────────────────────────

async function loadDispensingLogs() {
    const date = document.getElementById('logDateFilter')?.value || '';
    const channel = document.getElementById('logChannelFilter')?.value || 'all';

    const url = `/api/dispense/logs?date=${encodeURIComponent(date)}&channel=${encodeURIComponent(channel)}`;
    try {
        const res = await fetch(url);
        const data = await res.json();
        if (data.ok) {
            renderLogsTable(data.logs);
        }
    } catch (e) {
        console.error('Error loading logs:', e);
    }
}

function renderLogsTable(logs) {
    const tbody = document.getElementById('logsTableBody');
    const cardsContainer = document.getElementById('logsMobileCards');

    if (!logs || logs.length === 0) {
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 3rem; color: var(--text-muted);">
                        <i class="fas fa-clipboard-list" style="font-size: 2.5rem; color: var(--text-subtle); margin-bottom: 0.75rem; display: block;"></i>
                        ยังไม่มีประวัติการตัดสต็อกในเงื่อนไขที่เลือก
                    </td>
                </tr>
            `;
        }
        if (cardsContainer) {
            cardsContainer.innerHTML = `
                <div style="text-align: center; padding: 2.5rem 1rem; color: var(--text-muted); background: var(--bg-surface); border-radius: 18px; border: 1px dashed var(--border-color);">
                    <i class="fas fa-clipboard-list" style="font-size: 2.5rem; color: var(--text-subtle); margin-bottom: 0.75rem; display: block;"></i>
                    ยังไม่มีประวัติการตัดสต็อก
                </div>
            `;
        }
        return;
    }

    if (tbody) {
        tbody.innerHTML = logs.map(l => {
            let channelBadge = '<span class="badge badge-teal">Web Manual</span>';
            if (l.channel.includes('LINE')) {
                channelBadge = '<span class="badge badge-success"><i class="fab fa-line"></i> LINE</span>';
            } else if (l.channel.includes('QR')) {
                channelBadge = '<span class="badge badge-warning"><i class="fas fa-qrcode"></i> QR Scan</span>';
            }

            const driveBtn = l.drive_file_link
                ? `<a href="${l.drive_file_link}" target="_blank" class="btn btn-outline" style="padding: 0.2rem 0.5rem; font-size: 0.75rem; color: var(--color-accent);"><i class="fab fa-google-drive"></i> ดูรูป</a>`
                : '-';

            return `
                <tr>
                    <td style="font-size: 0.85rem; font-weight: 600; color: var(--text-muted); font-family: monospace;">
                        ${l.created_at}
                    </td>
                    <td>
                        <div style="font-weight: 700; color: var(--text-main);">${escapeHtml(l.drug_name)}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(l.drug_code || '-')}</div>
                    </td>
                    <td>
                        <span style="font-weight: 800; color: var(--color-danger); font-size: 0.95rem;">-${l.quantity}</span>
                    </td>
                    <td>
                        <span style="font-size: 0.85rem; color: var(--text-muted);">${l.balance_before} ➔ </span>
                        <span style="font-weight: 800; color: var(--color-brand);">${l.balance_after}</span>
                    </td>
                    <td>${channelBadge}</td>
                    <td>
                        <span style="font-size: 0.85rem; color: var(--text-main); font-weight: 600;">${escapeHtml(l.dispensed_by || '-')}</span>
                    </td>
                    <td>${driveBtn}</td>
                </tr>
            `;
        }).join('');
    }

    if (cardsContainer) {
        cardsContainer.innerHTML = logs.map(l => {
            let channelBadge = '<span class="badge badge-teal">Web</span>';
            if (l.channel.includes('LINE')) {
                channelBadge = '<span class="badge badge-success"><i class="fab fa-line"></i> LINE</span>';
            } else if (l.channel.includes('QR')) {
                channelBadge = '<span class="badge badge-warning"><i class="fas fa-qrcode"></i> QR</span>';
            }

            const driveBtn = l.drive_file_link
                ? `<a href="${l.drive_file_link}" target="_blank" class="btn btn-outline" style="padding: 0.2rem 0.5rem; font-size: 0.725rem; color: var(--color-accent);"><i class="fab fa-google-drive"></i> ดูรูป</a>`
                : '';

            return `
                <div class="log-mobile-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.35rem;">
                        <div>
                            <div style="font-weight: 800; font-size: 0.95rem; color: var(--text-main);">${escapeHtml(l.drug_name)}</div>
                            <div style="font-size: 0.75rem; color: var(--text-muted); font-family: monospace;">${escapeHtml(l.drug_code || '-')} • ${l.created_at}</div>
                        </div>
                        <span style="font-weight: 800; color: var(--color-danger); font-size: 1.1rem; background: var(--color-danger-light); padding: 0.2rem 0.6rem; border-radius: 8px;">-${l.quantity}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: var(--text-muted); margin-top: 0.4rem; padding-top: 0.4rem; border-top: 1px dashed var(--border-subtle);">
                        <div>
                            <span>คงเหลือ: ${l.balance_before} ➔ </span><strong style="color: var(--color-brand);">${l.balance_after}</strong>
                        </div>
                        <div style="display: flex; gap: 0.4rem; align-items: center;">
                            ${channelBadge}
                            ${driveBtn}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }
}

// ─────────────────────────────────────────────────────────────
// QR Code Generator Modal
// ─────────────────────────────────────────────────────────────

function openQrModal(id) {
    const drug = allDrugs.find(d => d.id === id);
    if (!drug) return;

    document.getElementById('qrDrugTitle').innerText = drug.name;
    document.getElementById('qrDrugDetails').innerText = `รหัส: ${drug.code} • ${drug.category} • ${drug.dosage_form}`;
    
    const qrContainer = document.getElementById('qrcodeContainer');
    qrContainer.innerHTML = '';

    // Smart URL payload: If scanned by ANY regular phone camera, it opens the web app directly to dispense!
    const origin = window.location.origin;
    const payload = `${origin}/?scan=${encodeURIComponent(drug.code)}`;
    
    new QRCode(qrContainer, {
        text: payload,
        width: 180,
        height: 180,
        colorDark: "#0F172A",
        colorLight: "#FFFFFF",
        correctLevel: QRCode.CorrectLevel.M
    });

    document.getElementById('qrModal').classList.add('active');
}

function closeQrModal() {
    document.getElementById('qrModal').classList.remove('active');
}

function printQrLabel() {
    window.print();
}

// ─────────────────────────────────────────────────────────────
// Mobile QR & 1D Barcode Camera Scanner Engine
// ─────────────────────────────────────────────────────────────

function playMedicalBeep() {
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) {
            const ctx = new AudioCtx();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, ctx.currentTime);
            gain.gain.setValueAtTime(0.2, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.15);
        }
    } catch (e) {}
    if (navigator.vibrate) {
        navigator.vibrate([80, 40, 80]);
    }
}

let availableCameras = [];
let selectedCameraId = null;
let currentFacingMode = "environment"; // Always default to back camera with autofocus
let isTorchOn = false;
let pendingNewBarcode = null;

async function updateCameraList() {
    try {
        const devices = await Html5Qrcode.getCameras();
        const selectEl = document.getElementById('cameraSelectDropdown');
        if (devices && devices.length > 0) {
            availableCameras = devices;
            if (selectEl) {
                selectEl.innerHTML = devices.map((d, idx) => `
                    <option value="${d.id}" ${d.id === selectedCameraId ? 'selected' : ''}>${d.label || 'กล้องตัวที่ ' + (idx + 1)}</option>
                `).join('');
                selectEl.style.display = 'inline-block';
            }
        }
    } catch (e) {
        console.warn("Could not list cameras:", e);
    }
}

async function onCameraSelectChange(e) {
    selectedCameraId = e.target.value;
    await stopScanner();
    await startScanner();
}

async function flipCamera() {
    currentFacingMode = (currentFacingMode === "environment") ? "user" : "environment";
    selectedCameraId = null; // reset specific ID so facingMode takes effect
    showToast(`🔄 สลับไปใช้กล้อง${currentFacingMode === 'environment' ? 'หลัง' : 'หน้า'}...`, 'info');
    await stopScanner();
    await startScanner();
}

async function toggleTorch() {
    if (!html5QrScanner) {
        showToast('กรุณาเปิดกล้องก่อนใช้งานไฟฉาย', 'info');
        return;
    }
    try {
        isTorchOn = !isTorchOn;
        await html5QrScanner.applyVideoConstraints({
            advanced: [{ torch: isTorchOn }]
        });
        const btn = document.getElementById('btnToggleTorch');
        if (btn) {
            btn.classList.toggle('btn-primary', isTorchOn);
            btn.classList.toggle('btn-outline', !isTorchOn);
        }
        showToast(isTorchOn ? '💡 เปิดไฟฉายแล้ว' : 'ไฟฉายปิดแล้ว', 'info');
    } catch (e) {
        showToast('อุปกรณ์นี้ไม่รองรับการเปิดไฟฉาย', 'info');
    }
}

async function startScanner() {
    if (html5QrScanner) {
        return;
    }
    const scannerEl = document.getElementById('qr-reader');
    if (!scannerEl) return;

    try {
        // Safe list of formats for both 1D and 2D barcodes
        const formats = (typeof Html5QrcodeSupportedFormats !== 'undefined') ? [
            Html5QrcodeSupportedFormats.QR_CODE,
            Html5QrcodeSupportedFormats.EAN_13,
            Html5QrcodeSupportedFormats.EAN_8,
            Html5QrcodeSupportedFormats.CODE_128,
            Html5QrcodeSupportedFormats.CODE_39,
            Html5QrcodeSupportedFormats.UPC_A,
            Html5QrcodeSupportedFormats.UPC_E,
            Html5QrcodeSupportedFormats.DATA_MATRIX,
            Html5QrcodeSupportedFormats.CODABAR
        ] : [0, 9, 10, 5, 3, 14, 15, 6, 2];

        html5QrScanner = new Html5Qrcode("qr-reader", {
            formatsToSupport: formats,
            verbose: false,
            experimentalFeatures: {
                useBarCodeDetectorIfSupported: true
            }
        });

        const config = {
            fps: 15,
            qrbox: (viewfinderWidth, viewfinderHeight) => {
                // Wide rectangular box ideal for both barcodes & QR
                const w = Math.min(Math.floor(viewfinderWidth * 0.9), 360);
                const h = Math.min(Math.floor(viewfinderHeight * 0.65), 240);
                return { width: Math.max(w, 200), height: Math.max(h, 150) };
            }
        };

        const cameraMode = selectedCameraId ? selectedCameraId : { facingMode: currentFacingMode };

        await html5QrScanner.start(
            cameraMode,
            config,
            onScanSuccess,
            (errorMessage) => {
                // scanning frame
            }
        );

        const errorNotice = document.getElementById('scannerErrorNotice');
        if (errorNotice) errorNotice.style.display = 'none';
        const activeNotice = document.getElementById('scannerActiveIndicator');
        if (activeNotice) activeNotice.style.display = 'block';

        // After camera starts and permission granted, populate camera dropdown
        updateCameraList();

    } catch (err) {
        console.warn("Unable to start camera scanner:", err);
        const errorNotice = document.getElementById('scannerErrorNotice');
        if (errorNotice) {
            errorNotice.style.display = 'block';
            errorNotice.innerHTML = `
                <i class="fas fa-exclamation-circle"></i> ไม่สามารถเปิดกล้องได้: ${escapeHtml(err?.message || err || 'กรุณาอนุญาตการเข้าถึงกล้อง')}<br>
                <small>หากใช้ Safari/Chrome กรุณากดอนุญาตให้เข้าถึงกล้อง หรือใช้วิธีพิมพ์รหัส/ถ่ายภาพด้านล่างแทนค่ะ</small>
            `;
        }
        const activeNotice = document.getElementById('scannerActiveIndicator');
        if (activeNotice) activeNotice.style.display = 'none';
    }
}

async function stopScanner() {
    if (html5QrScanner) {
        try {
            await html5QrScanner.stop();
            html5QrScanner.clear();
        } catch (err) {}
        html5QrScanner = null;
        isTorchOn = false;
        const ind = document.getElementById('scannerActiveIndicator');
        if (ind) ind.style.display = 'none';
    }
}

async function onScanSuccess(decodedText, decodedResult) {
    await stopScanner();
    await handleScannedCode(decodedText);
}

async function handleScannedCode(rawCode) {
    if (!rawCode) return;
    
    // Parse URL if the code was a URL (e.g. scanned from regular phone camera or LINE QR)
    let cleanCode = rawCode.trim();
    if (cleanCode.startsWith('http://') || cleanCode.startsWith('https://')) {
        try {
            const url = new URL(cleanCode);
            cleanCode = url.searchParams.get('scan') || url.searchParams.get('code') || url.searchParams.get('dispense') || cleanCode;
            if (cleanCode.includes('/')) {
                const parts = cleanCode.split('/');
                cleanCode = parts[parts.length - 1];
            }
        } catch (e) {}
    }
    cleanCode = cleanCode.replace(/^PHARM:/i, '').trim();

    playMedicalBeep();
    showToast(`🔍 กำลังตรวจสอบรหัส: ${cleanCode}...`, 'info');

    try {
        const res = await fetch(`/api/drugs/scan-lookup?code=${encodeURIComponent(cleanCode)}`);
        const data = await res.json();

        if (data.ok && data.found && data.drug) {
            const drug = data.drug;
            switchTab('inventory');
            openDispenseModalForDrug(drug.id);
            showToast(`✅ พบยาในคลัง: ${drug.name}`, 'success');
        } else {
            // Open nice modal prompt instead of window.confirm!
            openNewBarcodeModal(cleanCode);
        }
    } catch (e) {
        console.error('Scan lookup error:', e);
        showToast('เกิดข้อผิดพลาดในการค้นหาข้อมูลยา', 'error');
    }
}

// Modal for Unregistered Barcode Prompt
function openNewBarcodeModal(code) {
    pendingNewBarcode = code;
    const disp = document.getElementById('newBarcodeDisplay');
    if (disp) disp.innerText = code;
    const modal = document.getElementById('newBarcodeModal');
    if (modal) modal.classList.add('active');
}

function closeNewBarcodeModal() {
    const modal = document.getElementById('newBarcodeModal');
    if (modal) modal.classList.remove('active');
}

function proceedAddNewDrugWithBarcode() {
    const code = pendingNewBarcode;
    closeNewBarcodeModal();
    switchTab('inventory');
    openAddDrugModal();
    const codeInput = document.getElementById('drugCodeInput');
    if (codeInput && code) {
        codeInput.value = code;
    }
}

// Manual Barcode Input & Quick Test
function submitManualBarcode() {
    const input = document.getElementById('manualBarcodeInput');
    if (!input) return;
    const val = input.value.trim();
    if (!val) {
        showToast('กรุณากรอกรหัสยาหรือบาร์โค้ด', 'warning');
        return;
    }
    handleScannedCode(val);
}

function quickTestScan(code) {
    const input = document.getElementById('manualBarcodeInput');
    if (input) input.value = code;
    handleScannedCode(code);
}

// Client-Side Instant File / Photo Scanning
async function scanLocalImageFile(input) {
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];
    showToast('🔍 กำลังวิเคราะห์รูปภาพ...', 'info');

    await stopScanner();

    try {
        // Try decoding directly in browser first
        const scanner = new Html5Qrcode("qr-reader-file-temp");
        const result = await scanner.scanFile(file, true);
        if (result) {
            handleScannedCode(result);
            input.value = '';
            return;
        }
    } catch (clientErr) {
        console.log("Client file scan failed, falling back to server OCR:", clientErr);
    }

    // Fallback: Upload to server OCR
    uploadPrescriptionForScan(input);
}

// Image upload OCR scan
async function uploadPrescriptionForScan(input) {
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    const btn = document.getElementById('btnUploadOcr');
    if (btn) btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> กำลังวิเคราะห์ภาพ...';

    try {
        const res = await fetch('/api/scan-image', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.ok && data.analysis) {
            const an = data.analysis;
            if (an.success && an.drug) {
                switchTab('inventory');
                openDispenseModalForDrug(an.drug.id);
                document.getElementById('dispenseQtyInput').value = an.quantity || 1;
                showToast(`AI OCR ตรวจพบ: ${an.drug.name} (จำนวน ${an.quantity})`, 'success');
            } else {
                alert(an.message || 'ไม่สามารถตรวจพบชื่อยาจากภาพนี้ได้');
            }
        }
    } catch (e) {
        console.error('Scan error:', e);
        alert('เกิดข้อผิดพลาดในการประมวลผลรูปภาพ');
    } finally {
        if (btn) btn.innerHTML = '<i class="fas fa-camera"></i> อัปโหลดรูปใบสั่งยา / ซองยา';
        input.value = '';
    }
}

// ─────────────────────────────────────────────────────────────
// Manual Force Sync to Google Sheet
// ─────────────────────────────────────────────────────────────

async function syncWithGoogleSheet() {
    const btn = document.getElementById('btnSyncSheet');
    if (btn) btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> กำลังซิงก์...';

    try {
        const res = await fetch('/api/sync-sheet', { method: 'POST' });
        const data = await res.json();
        if (data.ok) {
            showToast('✅ ซิงก์ข้อมูลคลังยาลง Google Sheet สำเร็จแล้ว', 'success');
            loadDashboardStats();
        } else {
            alert('การซิงก์ Sheet: ' + (data.message || 'Error'));
        }
    } catch (e) {
        console.error('Sync error:', e);
    } finally {
        if (btn) btn.innerHTML = '<i class="fas fa-sync-alt"></i> ซิงก์กับ Google Sheet';
    }
}

// ─────────────────────────────────────────────────────────────
// Utilities & Toast Notifications
// ─────────────────────────────────────────────────────────────

function setupEventListeners() {
    const searchInput = document.getElementById('drugSearchInput');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(loadDrugs, 300);
        });
    }

    const catFilter = document.getElementById('categoryFilter');
    if (catFilter) catFilter.addEventListener('change', loadDrugs);

    const lowStockCheck = document.getElementById('lowStockCheckbox');
    if (lowStockCheck) lowStockCheck.addEventListener('change', loadDrugs);

    const logDate = document.getElementById('logDateFilter');
    if (logDate) logDate.addEventListener('change', loadDispensingLogs);

    const logChannel = document.getElementById('logChannelFilter');
    if (logChannel) logChannel.addEventListener('change', loadDispensingLogs);
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast-alert';
    toast.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        z-index: 100;
        background-color: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-left: 4px solid ${type === 'success' ? 'var(--color-success)' : 'var(--color-brand)'};
        color: var(--text-main);
        padding: 0.875rem 1.25rem;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        font-weight: 700;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        animation: slideUp 0.3s ease;
    `;
    toast.innerHTML = `<i class="fas ${type === 'success' ? 'fa-check-circle text-success' : 'fa-info-circle'}"></i> ${message}`;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.4s ease';
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ─────────────────────────────────────────────────────────────
// Google Drive & Sheets Connection Settings
// ─────────────────────────────────────────────────────────────

async function openGoogleSettingsModal() {
    document.getElementById('googleSettingsModal').classList.add('active');
    loadGoogleConfig();
}

function closeGoogleSettingsModal() {
    document.getElementById('googleSettingsModal').classList.remove('active');
}

async function loadGoogleConfig() {
    const banner = document.getElementById('googleStatusBanner');
    const statusText = document.getElementById('googleStatusText');
    const emailEl = document.getElementById('googleServiceEmail');
    const linkSheet = document.getElementById('linkOpenSheet');
    const linkDrive = document.getElementById('linkOpenDrive');
    const sheetInput = document.getElementById('inputSpreadsheetId');
    const driveInput = document.getElementById('inputDriveFolderId');
    const oauthCard = document.getElementById('googleOAuthCard');
    const connectedArea = document.getElementById('googleConnectedArea');
    const connectedEmailText = document.getElementById('googleConnectedEmailText');
    const btnGoToSheet = document.getElementById('btnGoToSheet');
    const btnGoToDrive = document.getElementById('btnGoToDrive');

    try {
        const res = await fetch('/api/google/config');
        const data = await res.json();
        if (data.ok && data.config) {
            const c = data.config;
            sheetInput.value = c.spreadsheet_id || '';
            driveInput.value = c.drive_folder_id || '';

            if (c.auth_type === 'oauth' && c.is_connected) {
                // OAuth Connected
                if (oauthCard) oauthCard.style.display = 'none';
                if (connectedArea) {
                    connectedArea.style.display = 'block';
                    if (connectedEmailText) {
                        connectedEmailText.innerHTML = `บัญชี Google: <strong>${escapeHtml(c.connected_email || '-')}</strong><br><span style="font-size: 0.775rem; color: var(--text-muted);">ชีต: ${escapeHtml(c.sheet_title || 'ระบบคลังยา')}</span>`;
                    }
                    if (btnGoToSheet && c.spreadsheet_url) btnGoToSheet.href = c.spreadsheet_url;
                    if (btnGoToDrive && c.drive_folder_url) btnGoToDrive.href = c.drive_folder_url;
                }
                if (emailEl) {
                    emailEl.innerHTML = `<strong>ประเภทการเชื่อมต่อ:</strong> บัญชีส่วนตัว (OAuth 2.0: ${escapeHtml(c.connected_email || '')})`;
                }
            } else {
                // Service Account or Not Connected
                if (oauthCard) oauthCard.style.display = 'block';
                if (connectedArea) connectedArea.style.display = 'none';
                if (c.service_account_email) {
                    if (emailEl) emailEl.innerHTML = `<strong>Service Account:</strong> <code style="color: var(--color-brand); font-size: 0.775rem;">${escapeHtml(c.service_account_email)}</code>`;
                } else {
                    if (emailEl) emailEl.innerText = 'ยังไม่ได้เชื่อมต่อบัญชี Google';
                }
            }

            if (c.is_connected && c.spreadsheet_id) {
                banner.style.background = 'var(--color-success-light)';
                banner.style.border = '1px solid var(--color-success)';
                statusText.innerHTML = `<span style="color: var(--color-success);"><i class="fas fa-check-circle"></i> เชื่อมต่อ Google Drive & Sheets สำเร็จ</span> (${escapeHtml(c.sheet_title || 'พร้อมใช้งาน')})`;

                if (linkSheet && c.spreadsheet_url) {
                    linkSheet.href = c.spreadsheet_url;
                    linkSheet.style.display = 'inline-flex';
                }
                if (linkDrive && c.drive_folder_url) {
                    linkDrive.href = c.drive_folder_url;
                    linkDrive.style.display = 'inline-flex';
                }
            } else {
                banner.style.background = 'var(--color-warning-light)';
                banner.style.border = '1px solid var(--color-warning)';
                statusText.innerHTML = `<span style="color: var(--color-warning);"><i class="fas fa-exclamation-triangle"></i> กำลังใช้งานในโหมด Local Cache (ยังไม่ได้เชื่อมต่อ Google Sheet)</span>`;
                if (c.connection_error) {
                    statusText.innerHTML += `<div style="font-size: 0.75rem; color: var(--color-danger); margin-top: 0.25rem;">ข้อผิดพลาด: ${escapeHtml(c.connection_error)}</div>`;
                }
                if (linkSheet) linkSheet.style.display = 'none';
                if (linkDrive) linkDrive.style.display = 'none';
            }
        }
    } catch (e) {
        console.error('Error loading google config:', e);
    }
}

async function disconnectGoogleAccount() {
    if (!confirm('คุณต้องการยกเลิกการเชื่อมต่อกับบัญชี Google นี้ใช่หรือไม่?\n(ข้อมูลในคลังยายังคงอยู่ในเครื่องตามปกติ)')) {
        return;
    }
    try {
        const res = await fetch('/api/google/disconnect', { method: 'POST' });
        const data = await res.json();
        if (data.ok) {
            showToast('ตัดการเชื่อมต่อ Google เรียบร้อยแล้ว', 'info');
            loadGoogleConfig();
            loadDashboardStats();
        } else {
            alert('ไม่สามารถตัดการเชื่อมต่อได้: ' + (data.error || 'Error'));
        }
    } catch (e) {
        console.error('Disconnect error:', e);
        alert('เกิดข้อผิดพลาดในการตัดการเชื่อมต่อ');
    }
}

async function saveGoogleConfig(e) {
    e.preventDefault();
    const btn = document.getElementById('btnSaveGoogleConfig');
    if (btn) btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> กำลังทดสอบและบันทึก...';

    const sheetInput = document.getElementById('inputSpreadsheetId').value.trim();
    const driveInput = document.getElementById('inputDriveFolderId').value.trim();

    try {
        const res = await fetch('/api/google/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                spreadsheet_id: sheetInput,
                drive_folder_id: driveInput
            })
        });
        const data = await res.json();
        if (data.ok) {
            showToast('✅ บันทึกและเชื่อมต่อ Google Drive & Sheets เรียบร้อยแล้ว', 'success');
            loadGoogleConfig();
            loadDashboardStats();
        } else {
            alert('ไม่สามารถบันทึกได้: ' + (data.error || 'Error'));
        }
    } catch (e) {
        console.error('Save google config error:', e);
        alert('เกิดข้อผิดพลาดในการบันทึก');
    } finally {
        if (btn) btn.innerHTML = '<i class="fas fa-save"></i> บันทึกและทดสอบเชื่อมต่อ';
    }
}

async function autoCreateSheet() {
    const btn = document.getElementById('btnAutoCreateSheet');
    if (btn) btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> กำลังสร้าง...';

    try {
        const res = await fetch('/api/google/auto-create-sheet', { method: 'POST' });
        const data = await res.json();
        if (data.ok) {
            showToast('🎉 สร้าง Google Sheet คลังยาสำเร็จแล้ว!', 'success');
            loadGoogleConfig();
            loadDashboardStats();
        } else {
            alert('ไม่สามารถสร้าง Sheet อัตโนมัติได้: ' + (data.error || 'กรุณาตรวจสอบสิทธิ์ของ Service Account'));
        }
    } catch (e) {
        console.error('Auto create sheet error:', e);
        alert('เกิดข้อผิดพลาดในการสร้าง Sheet');
    } finally {
        if (btn) btn.innerHTML = '✨ สร้าง Sheet ใหม่อัตโนมัติ';
    }
}
