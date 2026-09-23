/**
 * OrgChat AI - Web Time Attendance & GPS Clock-in System
 * Handles real-time clock, GPS Geolocation, Clock-in/Clock-out, Daily Summary, and History.
 */

let attendanceOfficeConfig = null;
let currentAttendanceState = null;
let attendanceTimerInterval = null;
let userCurrentCoords = null;

// Initialize on load / view activation
document.addEventListener('DOMContentLoaded', () => {
  if (typeof window.initAttendanceSystem === 'undefined') {
    window.initAttendanceSystem = initAttendanceSystem;
  }
});

function initAttendanceSystem() {
  startAttendanceClock();
  loadAttendanceToday();
  loadAttendanceHistory();
  loadAttendanceOrgSummary();
  tryAcquireLocationSilently();
}

/**
 * Real-time digital clock with Thai formatting
 */
function startAttendanceClock() {
  if (attendanceTimerInterval) clearInterval(attendanceTimerInterval);

  function updateClock() {
    const now = new Date();
    const timeEl = document.getElementById('attLiveClock');
    const dateEl = document.getElementById('attLiveDate');
    
    if (timeEl) {
      const h = String(now.getHours()).padStart(2, '0');
      const m = String(now.getMinutes()).padStart(2, '0');
      const s = String(now.getSeconds()).padStart(2, '0');
      timeEl.textContent = `${h}:${m}:${s}`;
    }

    if (dateEl) {
      const thaiDays = ['วันอาทิตย์', 'วันจันทร์', 'วันอังคาร', 'วันพุธ', 'วันพฤหัสบดี', 'วันศุกร์', 'วันเสาร์'];
      const thaiMonths = [
        'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
        'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
      ];
      const dayName = thaiDays[now.getDay()];
      const monthName = thaiMonths[now.getMonth()];
      const year = now.getFullYear() + 543;
      dateEl.textContent = `${dayName}ที่ ${now.getDate()} ${monthName} ${year}`;
    }

    // Live work duration calculation if checked in and not checked out
    updateLiveWorkDuration();
  }

  updateClock();
  attendanceTimerInterval = setInterval(updateClock, 1000);
}

/**
 * Calculate live working duration for today
 */
function updateLiveWorkDuration() {
  const durationEl = document.getElementById('attLiveDuration');
  if (!durationEl || !currentAttendanceState || !currentAttendanceState.check_in) {
    if (durationEl && (!currentAttendanceState || !currentAttendanceState.check_in)) {
      durationEl.textContent = '0 ชม. 00 นาที';
    }
    return;
  }

  const cin = currentAttendanceState.check_in;
  const cout = currentAttendanceState.check_out;

  const now = new Date();
  const [inH, inM, inS] = cin.check_time.split(':').map(Number);
  const inDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), inH, inM, inS || 0);

  let endDate = now;
  if (cout && cout.check_time) {
    const [outH, outM, outS] = cout.check_time.split(':').map(Number);
    endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), outH, outM, outS || 0);
  }

  let diffSec = Math.max(0, Math.floor((endDate - inDate) / 1000));
  const hrs = Math.floor(diffSec / 3600);
  const mins = Math.floor((diffSec % 3600) / 60);
  const secs = diffSec % 60;

  if (cout) {
    durationEl.textContent = `${hrs} ชม. ${String(mins).padStart(2, '0')} นาที`;
  } else {
    durationEl.textContent = `${hrs} ชม. ${String(mins).padStart(2, '0')} นาที ${String(secs).padStart(2, '0')} วิ`;
  }
}

/**
 * Fetch today's attendance record and office config
 */
async function loadAttendanceToday() {
  try {
    const res = await fetch('/api/attendance/today');
    const data = await res.json();
    if (!data.ok) return;

    currentAttendanceState = data;
    attendanceOfficeConfig = data.office;

    // Render Office Information
    const officeRadiusEl = document.getElementById('attOfficeRadius');
    const officeStartTimeEl = document.getElementById('attOfficeStartTime');
    if (officeRadiusEl && data.office) {
      officeRadiusEl.textContent = `${data.office.radius_meters.toLocaleString()} เมตร`;
    }
    if (officeStartTimeEl && data.office) {
      officeStartTimeEl.textContent = `${data.office.work_start_time} น.`;
    }

    // Render Cards
    const checkInTimeEl = document.getElementById('attCheckInTime');
    const checkInBadgeEl = document.getElementById('attCheckInBadge');
    const checkOutTimeEl = document.getElementById('attCheckOutTime');
    const checkOutBadgeEl = document.getElementById('attCheckOutBadge');
    const clockBtn = document.getElementById('attClockBtn');
    const clockBtnText = document.getElementById('attClockBtnText');
    const clockBtnSub = document.getElementById('attClockBtnSub');
    const clockBtnIcon = document.getElementById('attClockBtnIcon');

    if (data.check_in) {
      const cin = data.check_in;
      if (checkInTimeEl) checkInTimeEl.textContent = cin.check_time.substring(0, 5) + ' น.';
      if (checkInBadgeEl) {
        checkInBadgeEl.classList.remove('hidden');
        if (cin.status === 'on_time') {
          checkInBadgeEl.className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800';
          checkInBadgeEl.textContent = 'ตรงเวลา ✅';
        } else if (cin.status === 'late') {
          checkInBadgeEl.className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-800';
          checkInBadgeEl.textContent = 'เข้างานสาย ⚠️';
        } else {
          checkInBadgeEl.className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-800';
          checkInBadgeEl.textContent = 'นอกพื้นที่ ⚠️';
        }
      }
    } else {
      if (checkInTimeEl) checkInTimeEl.textContent = '--:--';
      if (checkInBadgeEl) checkInBadgeEl.classList.add('hidden');
    }

    if (data.check_out) {
      const cout = data.check_out;
      if (checkOutTimeEl) checkOutTimeEl.textContent = cout.check_time.substring(0, 5) + ' น.';
      if (checkOutBadgeEl) {
        checkOutBadgeEl.classList.remove('hidden');
        if (cout.status === 'outside_geofence') {
          checkOutBadgeEl.className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-800';
          checkOutBadgeEl.textContent = 'นอกพื้นที่ ⚠️';
        } else {
          checkOutBadgeEl.className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-300 dark:border-blue-800';
          checkOutBadgeEl.textContent = 'เลิกงานเรียบร้อย ✅';
        }
      }
    } else {
      if (checkOutTimeEl) checkOutTimeEl.textContent = '--:--';
      if (checkOutBadgeEl) checkOutBadgeEl.classList.add('hidden');
    }

    // Configure Big Action Button
    if (clockBtn && clockBtnText && clockBtnIcon) {
      if (!data.check_in) {
        // Ready to Check-in
        clockBtn.className = 'w-full py-5 px-6 rounded-3xl font-bold text-white shadow-xl transition-all duration-300 flex items-center justify-center gap-4 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 hover:shadow-emerald-500/25 active:scale-[0.98] group';
        clockBtnText.textContent = '📍 บันทึกเวลาเข้างาน (Check-In)';
        if (clockBtnSub) clockBtnSub.textContent = 'แตะเพื่อแชร์พิกัด GPS และลงเวลาเข้างาน';
        clockBtnIcon.setAttribute('data-lucide', 'log-in');
      } else if (!data.check_out) {
        // Ready to Check-out
        clockBtn.className = 'w-full py-5 px-6 rounded-3xl font-bold text-white shadow-xl transition-all duration-300 flex items-center justify-center gap-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 hover:shadow-blue-500/25 active:scale-[0.98] group';
        clockBtnText.textContent = '🏃 บันทึกเวลาเลิกงาน (Check-Out)';
        if (clockBtnSub) clockBtnSub.textContent = 'แตะเพื่อแชร์พิกัด GPS และลงเวลาเลิกงาน';
        clockBtnIcon.setAttribute('data-lucide', 'log-out');
      } else {
        // Already checked out, can update
        clockBtn.className = 'w-full py-5 px-6 rounded-3xl font-bold text-white shadow-xl transition-all duration-300 flex items-center justify-center gap-4 bg-gradient-to-r from-slate-700 to-surface-800 hover:from-slate-800 hover:to-surface-900 active:scale-[0.98] group';
        clockBtnText.textContent = '✅ บันทึกเวลาครบแล้ว (อัปเดตเลิกงาน)';
        if (clockBtnSub) clockBtnSub.textContent = `เลิกงานล่าสุด: ${data.check_out.check_time.substring(0, 5)} น. (แตะเพื่ออัปเดตใหม่)`;
        clockBtnIcon.setAttribute('data-lucide', 'check-circle-2');
      }
      if (typeof lucide !== 'undefined') lucide.createIcons();
    }

  } catch (err) {
    console.error('[loadAttendanceToday] Error:', err);
  }
}

/**
 * Handle Clock-in / Clock-out Action Button
 */
async function handleClockAction() {
  const clockBtn = document.getElementById('attClockBtn');
  const clockBtnText = document.getElementById('attClockBtnText');
  const clockBtnSub = document.getElementById('attClockBtnSub');

  if (!navigator.geolocation) {
    showToast('เบราว์เซอร์ของคุณไม่รองรับระบบระบุตำแหน่ง GPS', 'error');
    return;
  }

  // Set loading state
  if (clockBtn) clockBtn.disabled = true;
  if (clockBtnText) clockBtnText.textContent = '⏳ กำลังดึงพิกัดดาวเทียม GPS...';
  if (clockBtnSub) clockBtnSub.textContent = 'กรุณารอสักครู่ ระบบกำลังคำนวณตำแหน่งและระยะห่าง';

  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      const lat = pos.coords.latitude;
      const lng = pos.coords.longitude;
      userCurrentCoords = { lat, lng };

      updateGpsDisplay(lat, lng);

      try {
        if (clockBtnText) clockBtnText.textContent = '⏳ กำลังบันทึกเวลาทำงาน...';
        
        const csrfToken = window.csrf_token || (document.querySelector('meta[name="csrf-token"]') ? document.querySelector('meta[name="csrf-token"]').content : '');
        
        const res = await fetch('/api/attendance/clock', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
          },
          body: JSON.stringify({
            latitude: lat,
            longitude: lng,
            address: `Web GPS (${lat.toFixed(4)}, ${lng.toFixed(4)})`
          })
        });

        const data = await res.json();
        if (data.ok) {
          showAttendanceSuccessModal(data);
          loadAttendanceToday();
          loadAttendanceHistory();
          loadAttendanceOrgSummary();
        } else {
          showToast(data.error || 'เกิดข้อผิดพลาดในการบันทึกเวลา', 'error');
        }
      } catch (err) {
        console.error('[handleClockAction] Submit error:', err);
        showToast('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์', 'error');
      } finally {
        if (clockBtn) clockBtn.disabled = false;
        loadAttendanceToday();
      }
    },
    (err) => {
      console.warn('[handleClockAction] Geolocation error:', err);
      if (clockBtn) clockBtn.disabled = false;
      loadAttendanceToday();

      let msg = 'ไม่สามารถดึงตำแหน่ง GPS ได้';
      if (err.code === err.PERMISSION_DENIED) {
        msg = 'กรุณาอนุญาตการเข้าถึงตำแหน่ง (Location Permission) ในเบราว์เซอร์เพื่อลงเวลาทำงานค่ะ';
        showLocationPermissionGuideModal();
      } else if (err.code === err.POSITION_UNAVAILABLE) {
        msg = 'ไม่พบสัญญาณ GPS กรุณาเปิด Location Service ในอุปกรณ์ค่ะ';
      } else if (err.code === err.TIMEOUT) {
        msg = 'หมดเวลาในการค้นหาพิกัด GPS กรุณาลองใหม่อีกครั้งค่ะ';
      }
      showToast(msg, 'error');
    },
    {
      enableHighAccuracy: true,
      timeout: 12000,
      maximumAge: 0
    }
  );
}

/**
 * Update the GPS Status Banner
 */
function updateGpsDisplay(lat, lng) {
  const gpsCoordEl = document.getElementById('attGpsCoords');
  const gpsDistEl = document.getElementById('attGpsDistance');
  const gpsStatusEl = document.getElementById('attGpsStatusBadge');

  if (gpsCoordEl) {
    gpsCoordEl.textContent = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
  }

  if (attendanceOfficeConfig) {
    const dist = calculateDistance(lat, lng, attendanceOfficeConfig.latitude, attendanceOfficeConfig.longitude);
    if (gpsDistEl) {
      gpsDistEl.textContent = `${dist.toLocaleString()} ม.`;
    }
    if (gpsStatusEl) {
      if (dist <= attendanceOfficeConfig.radius_meters) {
        gpsStatusEl.className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800';
        gpsStatusEl.textContent = 'อยู่ในพื้นที่ลงเวลา ✅';
      } else {
        gpsStatusEl.className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-800';
        gpsStatusEl.textContent = `อยู่นอกพื้นที่ (${dist.toLocaleString()} ม.) ⚠️`;
      }
    }
  }
}

/**
 * Try to read GPS silently on page load to preview distance (only if permission is already granted)
 */
async function tryAcquireLocationSilently() {
  if (!navigator.geolocation) return;
  try {
    if (navigator.permissions && navigator.permissions.query) {
      const p = await navigator.permissions.query({ name: 'geolocation' });
      if (p.state !== 'granted') {
        // Do NOT call getCurrentPosition if not granted yet,
        // to prevent browsers from automatically suppressing or auto-blocking without a user gesture!
        return;
      }
    }
  } catch (e) {
    // Fallback for browsers that don't support permissions.query
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      userCurrentCoords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
      updateGpsDisplay(pos.coords.latitude, pos.coords.longitude);
    },
    () => {},
    { enableHighAccuracy: false, timeout: 5000, maximumAge: 60000 }
  );
}

/**
 * Explicitly trigger the browser's native location permission prompt on user click
 */
function requestLocationPermissionPrompt() {
  if (!navigator.geolocation) {
    if (typeof showToast === 'function') showToast('เบราว์เซอร์ของคุณไม่รองรับ GPS', 'error');
    return;
  }
  
  if (typeof showToast === 'function') showToast('กำลังส่งคำขอสิทธิ์ตำแหน่งไปยังเบราว์เซอร์...', 'info');

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude;
      const lng = pos.coords.longitude;
      userCurrentCoords = { lat, lng };
      updateGpsDisplay(lat, lng);
      closeLocationPermissionGuideModal();
      if (typeof showToast === 'function') showToast('เชื่อมต่อพิกัด GPS สำเร็จแล้วค่ะ!', 'success');
    },
    (err) => {
      console.warn('[requestLocationPermissionPrompt] Geolocation error:', err);
      if (err.code === err.PERMISSION_DENIED) {
        if (typeof showToast === 'function') {
          showToast('เบราว์เซอร์บล็อกตำแหน่งอยู่ กรุณากดปลดบล็อกที่รูปแม่กุญแจ 🔒 ด้านบนแถบ URL ค่ะ', 'warning');
        }
        showLocationPermissionGuideModal();
      } else if (err.code === err.POSITION_UNAVAILABLE) {
        if (typeof showToast === 'function') showToast('ไม่พบสัญญาณ GPS กรุณาเปิด Location ในอุปกรณ์ค่ะ', 'error');
      } else if (err.code === err.TIMEOUT) {
        if (typeof showToast === 'function') showToast('หมดเวลาค้นหาพิกัด GPS กรุณาลองใหม่ค่ะ', 'error');
      }
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
  );
}
window.requestLocationPermissionPrompt = requestLocationPermissionPrompt;

/**
 * Haversine formula on client
 */
function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371000;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c);
}

/**
 * Show Success Confirmation Dialog
 */
function showAttendanceSuccessModal(data) {
  const modal = document.getElementById('attSuccessModal');
  const titleEl = document.getElementById('attModalTitle');
  const timeEl = document.getElementById('attModalTime');
  const badgeEl = document.getElementById('attModalBadge');
  const distEl = document.getElementById('attModalDist');

  if (titleEl) {
    titleEl.textContent = data.check_type === 'check_in' ? '✅ บันทึกเวลาเข้างานสำเร็จ!' : '🏃 บันทึกเวลาเลิกงานสำเร็จ!';
  }
  if (timeEl && data.record) {
    timeEl.textContent = data.record.check_time ? data.record.check_time.substring(0, 5) + ' น.' : 'เรียบร้อย';
  }
  if (badgeEl) {
    if (data.status === 'on_time') {
      badgeEl.className = 'px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300';
      badgeEl.textContent = 'ตรงเวลา ✅';
    } else if (data.status === 'late') {
      badgeEl.className = 'px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300';
      badgeEl.textContent = 'เข้างานสาย ⚠️';
    } else {
      badgeEl.className = 'px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300';
      badgeEl.textContent = 'นอกพื้นที่ ⚠️';
    }
  }
  if (distEl) {
    distEl.textContent = `ระยะห่างจากออฟฟิศ: ${data.distance_meters.toLocaleString()} เมตร`;
  }

  if (modal) {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }

  showToast(data.message, 'success');
}

function closeAttendanceSuccessModal() {
  const modal = document.getElementById('attSuccessModal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

function showLocationPermissionGuideModal() {
  const modal = document.getElementById('attPermissionGuideModal');
  if (modal) {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    if (typeof lucide !== 'undefined') lucide.createIcons();
  }
}

function closeLocationPermissionGuideModal() {
  const modal = document.getElementById('attPermissionGuideModal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

window.closeAttendanceSuccessModal = closeAttendanceSuccessModal;
window.showLocationPermissionGuideModal = showLocationPermissionGuideModal;
window.closeLocationPermissionGuideModal = closeLocationPermissionGuideModal;

/**
 * Load User's Attendance History
 */
async function loadAttendanceHistory() {
  const container = document.getElementById('attHistoryTableBody');
  const countBadge = document.getElementById('attHistoryCount');
  if (!container) return;

  try {
    const res = await fetch('/api/attendance/my-history?limit=30');
    const data = await res.json();
    if (!data.ok || !data.daily_summary) {
      container.innerHTML = '<tr><td colspan="5" class="py-8 text-center text-surface-400 text-xs">ไม่พบข้อมูลประวัติการลงเวลา</td></tr>';
      return;
    }

    if (countBadge) countBadge.textContent = `${data.count} วัน`;

    if (data.daily_summary.length === 0) {
      container.innerHTML = '<tr><td colspan="5" class="py-8 text-center text-surface-400 text-xs">ยังไม่มีประวัติการลงเวลาในระบบ</td></tr>';
      return;
    }

    let html = '';
    data.daily_summary.forEach(item => {
      const dParts = item.date.split('-');
      const dateFormatted = `${dParts[2]}/${dParts[1]}/${parseInt(dParts[0]) + 543}`;
      
      // In time & badge
      let inHtml = '<span class="text-surface-400 text-xs">-</span>';
      if (item.check_in) {
        const cin = item.check_in;
        let badgeColor = 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300';
        let badgeText = 'ตรงเวลา';
        if (cin.status === 'late') {
          badgeColor = 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300';
          badgeText = 'สาย';
        } else if (cin.status === 'outside_geofence') {
          badgeColor = 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300';
          badgeText = 'นอกเขต';
        }
        inHtml = `
          <div class="flex items-center gap-2">
            <span class="font-bold text-xs">${cin.check_time.substring(0, 5)} น.</span>
            <span class="text-[10px] font-semibold px-1.5 py-0.5 rounded ${badgeColor}">${badgeText}</span>
          </div>
        `;
      }

      // Out time
      let outHtml = '<span class="text-surface-400 text-xs">-</span>';
      if (item.check_out) {
        outHtml = `<span class="font-bold text-xs">${item.check_out.check_time.substring(0, 5)} น.</span>`;
      }

      // Total hours
      const hoursHtml = item.total_hours > 0 
        ? `<span class="font-bold text-xs text-brand-600 dark:text-brand-400">${item.total_hours} ชม.</span>`
        : '<span class="text-surface-400 text-xs">-</span>';

      // Distance
      const dist = (item.check_in && item.check_in.distance_meters) ? `${Math.round(item.check_in.distance_meters)} ม.` : '-';

      html += `
        <tr class="border-b border-surface-100 dark:border-surface-800/60 hover:bg-surface-50 dark:hover:bg-surface-800/40 transition-colors">
          <td class="py-3 px-4 text-xs font-medium text-surface-900 dark:text-white whitespace-nowrap">📅 ${dateFormatted}</td>
          <td class="py-3 px-4">${inHtml}</td>
          <td class="py-3 px-4">${outHtml}</td>
          <td class="py-3 px-4">${hoursHtml}</td>
          <td class="py-3 px-4 text-xs text-surface-500 whitespace-nowrap">${dist}</td>
        </tr>
      `;
    });

    container.innerHTML = html;
  } catch (err) {
    console.error('[loadAttendanceHistory] Error:', err);
    container.innerHTML = '<tr><td colspan="5" class="py-8 text-center text-rose-500 text-xs">เกิดข้อผิดพลาดในการโหลดประวัติ</td></tr>';
  }
}

/**
 * Load Organization Summary (For Admins)
 */
async function loadAttendanceOrgSummary() {
  const container = document.getElementById('attOrgSummaryCard');
  if (!container) return;

  try {
    const res = await fetch('/api/attendance/org-summary');
    const data = await res.json();
    if (!data.ok) return;

    container.classList.remove('hidden');

    const totalEl = document.getElementById('attOrgTotalMembers');
    const clockedInEl = document.getElementById('attOrgClockedIn');
    const notClockedInEl = document.getElementById('attOrgNotClockedIn');
    const lateEl = document.getElementById('attOrgLate');

    if (totalEl) totalEl.textContent = data.total_members;
    if (clockedInEl) clockedInEl.textContent = data.clocked_in_count;
    if (notClockedInEl) notClockedInEl.textContent = data.not_clocked_in_count;
    if (lateEl) lateEl.textContent = data.late_count;

    // Render org member attendance list
    const memberList = document.getElementById('attOrgMembersList');
    if (memberList && data.records) {
      if (data.records.length === 0) {
        memberList.innerHTML = '<div class="py-4 text-center text-surface-400 text-xs">ยังไม่มีสมาชิกในองค์กรลงเวลาในวันนี้</div>';
      } else {
        let mHtml = '';
        data.records.forEach(r => {
          const typeTh = r.check_type === 'check_in' ? 'เข้างาน' : 'เลิกงาน';
          const typeBadge = r.check_type === 'check_in' ? 'bg-emerald-50 text-emerald-700' : 'bg-blue-50 text-blue-700';
          mHtml += `
            <div class="flex items-center justify-between p-3 rounded-2xl bg-surface-50 dark:bg-surface-800/50 border border-surface-100 dark:border-surface-700/60">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-brand-100 dark:bg-brand-900/40 text-brand-600 flex items-center justify-center font-bold text-xs">
                  ${(r.username || 'U').substring(0, 1).toUpperCase()}
                </div>
                <div>
                  <p class="text-xs font-bold text-surface-900 dark:text-white">${r.username}</p>
                  <p class="text-[11px] text-surface-400">${r.check_time.substring(0, 5)} น. (${Math.round(r.distance_meters || 0)} ม.)</p>
                </div>
              </div>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded ${typeBadge}">${typeTh}</span>
            </div>
          `;
        });
        memberList.innerHTML = mHtml;
      }
    }
  } catch (err) {
    console.error('[loadAttendanceOrgSummary] Error:', err);
  }
}
