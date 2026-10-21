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
          checkInBadgeEl.textContent = 'ตรงเวลา';
        } else if (cin.status === 'late') {
          checkInBadgeEl.className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-800';
          checkInBadgeEl.textContent = 'เข้างานสาย';
        } else {
          checkInBadgeEl.className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-800';
          checkInBadgeEl.textContent = 'นอกพื้นที่';
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
          checkOutBadgeEl.textContent = 'นอกพื้นที่';
        } else {
          checkOutBadgeEl.className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-300 dark:border-blue-800';
          checkOutBadgeEl.textContent = 'เลิกงานเรียบร้อย';
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
        clockBtnText.textContent = 'บันทึกเวลาเข้างาน (Check-In)';
        if (clockBtnSub) clockBtnSub.textContent = 'แตะเพื่อแชร์พิกัด GPS และลงเวลาเข้างาน';
        clockBtnIcon.setAttribute('data-lucide', 'log-in');
      } else if (!data.check_out) {
        // Ready to Check-out
        clockBtn.className = 'w-full py-5 px-6 rounded-3xl font-bold text-white shadow-xl transition-all duration-300 flex items-center justify-center gap-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 hover:shadow-blue-500/25 active:scale-[0.98] group';
        clockBtnText.textContent = 'บันทึกเวลาเลิกงาน (Check-Out)';
        if (clockBtnSub) clockBtnSub.textContent = 'แตะเพื่อแชร์พิกัด GPS และลงเวลาเลิกงาน';
        clockBtnIcon.setAttribute('data-lucide', 'log-out');
      } else {
        // Already checked out, can update
        clockBtn.className = 'w-full py-5 px-6 rounded-3xl font-bold text-white shadow-xl transition-all duration-300 flex items-center justify-center gap-4 bg-gradient-to-r from-slate-700 to-surface-800 hover:from-slate-800 hover:to-surface-900 active:scale-[0.98] group';
        clockBtnText.textContent = 'บันทึกเวลาครบแล้ว (อัปเดตเลิกงาน)';
        if (clockBtnSub) clockBtnSub.textContent = `เลิกงานล่าสุด: ${data.check_out.check_time.substring(0, 5)} น. (แตะเพื่ออัปเดตใหม่)`;
        clockBtnIcon.setAttribute('data-lucide', 'check-circle-2');
      }
      if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    // Synchronize Home Attendance Widget
    const homeBadge = document.getElementById('homeAttStatusBadge');
    const homeTitle = document.getElementById('homeAttStatusTitle');
    const homeSub = document.getElementById('homeAttStatusSub');
    const homeBtnText = document.getElementById('homeAttActionBtnText');

    if (homeBadge && homeTitle && homeSub) {
      if (!data.check_in) {
        homeBadge.textContent = 'ยังไม่ Check-in';
        homeBadge.className = 'inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-surface-100 dark:bg-surface-800 text-surface-600 dark:text-surface-300 border border-surface-200 dark:border-surface-700';
        homeTitle.textContent = 'ยังไม่ได้ลงเวลาเข้างานวันนี้';
        homeSub.textContent = 'บันทึกเวลาเข้า-ออกงานด้วยพิกัด GPS อัตโนมัติ';
        if (homeBtnText) homeBtnText.textContent = 'เช็คอินเข้างาน (GPS)';
      } else if (!data.check_out) {
        const inTime = data.check_in.check_time ? data.check_in.check_time.substring(0, 5) : '--:--';
        homeBadge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> เข้างานแล้ว';
        homeBadge.className = 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20';
        homeTitle.textContent = `เข้างานแล้วเวลา ${inTime} น.`;
        homeSub.textContent = data.check_in.is_late ? 'บันทึกเวลาสาย • แตะเพื่อลงเวลาเลิกงานเมื่อสิ้นสุดวัน' : 'ตรงเวลา • แตะเพื่อลงเวลาเลิกงานเมื่อสิ้นสุดวัน';
        if (homeBtnText) homeBtnText.textContent = 'ลงเวลาเลิกงาน';
      } else {
        const inTime = data.check_in.check_time ? data.check_in.check_time.substring(0, 5) : '--:--';
        const outTime = data.check_out.check_time ? data.check_out.check_time.substring(0, 5) : '--:--';
        homeBadge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-blue-500"></span> บันทึกครบถ้วน';
        homeBadge.className = 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20';
        homeTitle.textContent = `เข้า ${inTime} น. / ออก ${outTime} น.`;
        homeSub.textContent = 'บันทึกเวลาทำงานวันนี้เรียบร้อยแล้ว แตะหากต้องการอัปเดตเวลาออก';
        if (homeBtnText) homeBtnText.textContent = 'อัปเดตเวลาออก';
      }
      if (typeof lucide !== 'undefined') lucide.createIcons();
    }

  } catch (err) {
    console.error('[loadAttendanceToday] Error:', err);
  }
}

let _isAttendanceClocking = false;

/**
 * Handle Clock-in / Clock-out Action Button
 */
async function handleClockAction() {
  if (_isAttendanceClocking) return;
  _isAttendanceClocking = true;

  const clockBtn = document.getElementById('attClockBtn');
  const clockBtnText = document.getElementById('attClockBtnText');
  const clockBtnSub = document.getElementById('attClockBtnSub');

  if (!navigator.geolocation) {
    _isAttendanceClocking = false;
    showToast('เบราว์เซอร์ของคุณไม่รองรับระบบระบุตำแหน่ง GPS', 'error');
    return;
  }

  // Set loading state
  if (clockBtn) clockBtn.disabled = true;
  if (clockBtnText) clockBtnText.textContent = 'กำลังดึงพิกัดดาวเทียม GPS...';
  if (clockBtnSub) clockBtnSub.textContent = 'กรุณารอสักครู่ ระบบกำลังคำนวณตำแหน่งและระยะห่าง';

  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      const lat = pos.coords.latitude;
      const lng = pos.coords.longitude;
      userCurrentCoords = { lat, lng };

      updateGpsDisplay(lat, lng);

      try {
        if (clockBtnText) clockBtnText.textContent = 'กำลังบันทึกเวลาทำงาน...';
        
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
        _isAttendanceClocking = false;
        if (clockBtn) clockBtn.disabled = false;
        loadAttendanceToday();
      }
    },
    (err) => {
      _isAttendanceClocking = false;
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
        gpsStatusEl.textContent = 'อยู่ในพื้นที่ลงเวลา';
      } else {
        gpsStatusEl.className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-800';
        gpsStatusEl.textContent = `อยู่นอกพื้นที่ (${dist.toLocaleString()} ม.)`;
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
          showToast('เบราว์เซอร์บล็อกตำแหน่งอยู่ กรุณากดปลดบล็อกที่ไอคอนตำแหน่งด้านบนแถบ URL ค่ะ', 'warning');
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
    titleEl.textContent = data.check_type === 'check_in' ? 'บันทึกเวลาเข้างานสำเร็จ!' : 'บันทึกเวลาเลิกงานสำเร็จ!';
  }
  if (timeEl && data.record) {
    timeEl.textContent = data.record.check_time ? data.record.check_time.substring(0, 5) + ' น.' : 'เรียบร้อย';
  }
  if (badgeEl) {
    if (data.status === 'on_time') {
      badgeEl.className = 'px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300';
      badgeEl.textContent = 'ตรงเวลา';
    } else if (data.status === 'late') {
      badgeEl.className = 'px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300';
      badgeEl.textContent = 'เข้างานสาย';
    } else {
      badgeEl.className = 'px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300';
      badgeEl.textContent = 'นอกพื้นที่';
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
          <td class="py-3 px-4 text-xs font-medium text-surface-900 dark:text-white whitespace-nowrap">
            <span class="inline-flex items-center gap-1.5"><i data-lucide="calendar" class="w-3.5 h-3.5 text-surface-400"></i><span>${dateFormatted}</span></span>
          </td>
          <td class="py-3 px-4">${inHtml}</td>
          <td class="py-3 px-4">${outHtml}</td>
          <td class="py-3 px-4">${hoursHtml}</td>
          <td class="py-3 px-4 text-xs text-surface-500 whitespace-nowrap">${dist}</td>
        </tr>
      `;
    });

    container.innerHTML = html;
    if (typeof lucide !== 'undefined') lucide.createIcons();
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

// ============================================================================
// Organization Attendance Management (Admin Tab & Manual Overrides)
// ============================================================================

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

let _orgAttCurrentDate = '';
let _orgAttMembersCache = [];

function getOrgAttBangkokToday() {
  const now = new Date();
  const bangkokTime = new Date(now.getTime() + (7 * 60 + now.getTimezoneOffset()) * 60000);
  const yyyy = bangkokTime.getFullYear();
  const mm = String(bangkokTime.getMonth() + 1).padStart(2, '0');
  const dd = String(bangkokTime.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

function formatOrgAttThaiDate(dateStr) {
  if (!dateStr) return '';
  const parts = dateStr.split('-');
  if (parts.length !== 3) return dateStr;
  const thaiMonths = [
    'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
    'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'
  ];
  const day = parseInt(parts[2], 10);
  const mIdx = parseInt(parts[1], 10) - 1;
  const year = parseInt(parts[0], 10) + 543;
  return `${day} ${thaiMonths[mIdx] || ''} ${year}`;
}

/**
 * Load attendance status of all org members for a specific date
 */
async function loadOrgAttendance(targetDate) {
  if (!targetDate) {
    targetDate = _orgAttCurrentDate || getOrgAttBangkokToday();
  }
  _orgAttCurrentDate = targetDate;

  const dateInput = document.getElementById('orgAttDateInput');
  if (dateInput && dateInput.value !== targetDate) {
    dateInput.value = targetDate;
  }

  const dateBadge = document.getElementById('orgAttDateBadge');
  if (dateBadge) {
    dateBadge.textContent = formatOrgAttThaiDate(targetDate);
  }

  const tbody = document.getElementById('orgAttTableBody');
  if (tbody) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="py-12 text-center text-surface-400">
          <div class="flex flex-col items-center justify-center gap-2">
            <i data-lucide="loader-2" class="w-6 h-6 animate-spin text-brand-500"></i>
            <span>กำลังโหลดข้อมูลเวลาเข้างานประจำวันที่ ${formatOrgAttThaiDate(targetDate)}...</span>
          </div>
        </td>
      </tr>
    `;
    if (typeof lucide !== 'undefined') lucide.createIcons();
  }

  try {
    const res = await fetch(`/api/admin/attendance/daily?date=${encodeURIComponent(targetDate)}`);
    const data = await res.json();

    if (!data.ok) {
      if (tbody) {
        tbody.innerHTML = `
          <tr>
            <td colspan="7" class="py-12 text-center text-rose-500 text-xs">
              ${data.error || 'ไม่สามารถโหลดข้อมูลเวลาเข้างานได้'}
            </td>
          </tr>
        `;
      }
      return;
    }

    const counts = data.counts || (data.summary ? {
      total: data.summary.total_members || 0,
      present: data.summary.present_count || 0,
      present_rate: data.summary.present_percentage || 0,
      absent: data.summary.absent_count || 0,
      late: data.summary.late_count || 0
    } : {});

    // Update KPI counts
    const totalEl = document.getElementById('orgAttStatTotal');
    const presentEl = document.getElementById('orgAttStatPresent');
    const rateEl = document.getElementById('orgAttStatRate');
    const absentEl = document.getElementById('orgAttStatAbsent');
    const lateEl = document.getElementById('orgAttStatLate');

    if (totalEl) totalEl.textContent = counts.total || 0;
    if (presentEl) presentEl.textContent = counts.present || 0;
    if (rateEl) rateEl.textContent = `(${counts.present_rate || 0}%)`;
    if (absentEl) absentEl.textContent = counts.absent || 0;
    if (lateEl) lateEl.textContent = counts.late || 0;

    const rawMembers = data.members || [];
    _orgAttMembersCache = rawMembers.map((m, idx) => {
      let st = m.status || 'absent';
      if (st === 'on_time') st = 'present';
      return {
        user_id: m.user_id || idx + 1,
        username: m.username || '',
        full_name: m.full_name || m.display_name || m.username || 'สมาชิก',
        avatar_url: m.avatar_url || '',
        role: m.role || 'member',
        department: m.department || 'ทั่วไป',
        position: m.position || '',
        email: m.email || '',
        status: st,
        check_in: m.check_in || null,
        check_out: m.check_out || null,
        total_hours: m.total_hours || m.work_duration_hours || 0,
        note: m.note || ''
      };
    });

    // Populate department filter options dynamically
    updateOrgAttDeptFilter(_orgAttMembersCache);

    // Render table
    filterOrgAttendanceTable();
  } catch (err) {
    console.error('[loadOrgAttendance] Error:', err);
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="py-12 text-center text-rose-500 text-xs">
            เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์
          </td>
        </tr>
      `;
    }
  }
}

function updateOrgAttDeptFilter(members) {
  const deptSelect = document.getElementById('orgAttDeptFilter');
  if (!deptSelect) return;

  const currentVal = deptSelect.value;
  const depts = new Set();
  members.forEach(m => {
    if (m.department && m.department.trim()) {
      depts.add(m.department.trim());
    }
  });

  let optionsHtml = '<option value="all">ทุกแผนก</option>';
  Array.from(depts).sort().forEach(d => {
    optionsHtml += `<option value="${escapeHtml(d)}">${escapeHtml(d)}</option>`;
  });
  deptSelect.innerHTML = optionsHtml;
  if (depts.has(currentVal)) {
    deptSelect.value = currentVal;
  }
}

/**
 * Filter and render attendance table
 */
function filterOrgAttendanceTable() {
  const tbody = document.getElementById('orgAttTableBody');
  const countLabel = document.getElementById('orgAttTableCount');
  if (!tbody) return;

  const searchQ = ((document.getElementById('orgAttSearchInput') || {}).value || '').toLowerCase().trim();
  const statusFilter = (document.getElementById('orgAttStatusFilter') || {}).value || 'all';
  const deptFilter = (document.getElementById('orgAttDeptFilter') || {}).value || 'all';

  const filtered = _orgAttMembersCache.filter(m => {
    // Dept filter
    if (deptFilter !== 'all' && (m.department || '').trim() !== deptFilter) {
      return false;
    }

    // Status filter
    if (statusFilter === 'present') {
      if (m.status !== 'present' && m.status !== 'late' && m.status !== 'manual_admin') return false;
    } else if (statusFilter === 'absent') {
      if (m.status !== 'absent') return false;
    } else if (statusFilter === 'late') {
      if (m.status !== 'late') return false;
    } else if (statusFilter === 'manual_admin') {
      if (m.status !== 'manual_admin') return false;
    }

    // Search query
    if (searchQ) {
      const matchName = (m.full_name || '').toLowerCase().includes(searchQ);
      const matchUser = (m.username || '').toLowerCase().includes(searchQ);
      const matchDept = (m.department || '').toLowerCase().includes(searchQ);
      const matchPos = (m.position || '').toLowerCase().includes(searchQ);
      const matchEmail = (m.email || '').toLowerCase().includes(searchQ);
      if (!matchName && !matchUser && !matchDept && !matchPos && !matchEmail) return false;
    }

    return true;
  });

  if (countLabel) {
    countLabel.textContent = `แสดง ${filtered.length} จาก ${_orgAttMembersCache.length} รายการ`;
  }

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="py-12 text-center text-surface-400 text-xs">
          <div class="flex flex-col items-center justify-center gap-1.5">
            <i data-lucide="filter-x" class="w-8 h-8 opacity-40 mb-1"></i>
            <span class="font-bold text-surface-600 dark:text-surface-300">ไม่พบข้อมูลตามเงื่อนไขที่ค้นหา</span>
            <span class="text-[11px] text-surface-400">ลองปรับการค้นหาหรือเปลี่ยนตัวกรองสถานะ</span>
          </div>
        </td>
      </tr>
    `;
    if (typeof lucide !== 'undefined') lucide.createIcons();
    return;
  }

  let html = '';
  filtered.forEach(m => {
    const displayName = m.full_name || m.username;
    const initial = (m.username || 'U').substring(0, 1).toUpperCase();
    const deptRole = [m.department, m.position || m.role].filter(Boolean).join(' • ');

    // Check-in Time & Badges
    let inHtml = '<span class="text-surface-400 font-mono text-xs">-</span>';
    if (m.check_in && m.check_in.check_time) {
      const timeStr = m.check_in.check_time.substring(0, 5);
      inHtml = `
        <div class="flex items-center gap-1.5">
          <span class="font-mono font-bold text-surface-900 dark:text-white">${timeStr} น.</span>
        </div>
      `;
    }

    // Check-out Time
    let outHtml = '<span class="text-surface-400 font-mono text-xs">-</span>';
    if (m.check_out && m.check_out.check_time) {
      const timeStr = m.check_out.check_time.substring(0, 5);
      outHtml = `
        <div class="flex items-center gap-1.5">
          <span class="font-mono font-bold text-surface-900 dark:text-white">${timeStr} น.</span>
        </div>
      `;
    }

    // Hours
    let hoursHtml = '<span class="text-surface-400 font-mono text-xs">-</span>';
    if (m.total_hours > 0) {
      hoursHtml = `<span class="font-mono font-bold text-brand-600 dark:text-brand-400 tabular-nums">${m.total_hours} ชม.</span>`;
    }

    // Status Badge
    let statusBadge = '';
    if (m.status === 'present') {
      statusBadge = '<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200/60 dark:border-emerald-800/40"><span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>มาทำงาน</span>';
    } else if (m.status === 'late') {
      statusBadge = '<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200/60 dark:border-amber-800/40"><span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span>มาสาย</span>';
    } else if (m.status === 'manual_admin') {
      statusBadge = '<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 border border-sky-200/60 dark:border-sky-800/40"><span class="w-1.5 h-1.5 rounded-full bg-sky-500"></span>แอดมินบันทึก</span>';
    } else {
      statusBadge = '<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200/60 dark:border-rose-800/40"><span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span>ยังไม่ลงเวลา</span>';
    }

    // Note / Location Details
    let noteHtml = '<span class="text-surface-400 text-xs">-</span>';
    const notes = [];
    if (m.check_in && m.check_in.distance_meters !== null && m.check_in.distance_meters !== undefined) {
      notes.push(`GPS: ${Math.round(m.check_in.distance_meters)} ม.`);
    }
    if (m.check_in && m.check_in.note) {
      notes.push(escapeHtml(m.check_in.note));
    }
    if (notes.length > 0) {
      noteHtml = `<span class="text-surface-600 dark:text-surface-300 text-[11px] truncate max-w-[200px] inline-block" title="${notes.join(' | ')}">${notes.join(' | ')}</span>`;
    }

    // Action button
    const hasRecord = !!m.check_in;
    const btnLabel = hasRecord ? 'แก้ไข' : 'บันทึกเวลาแทน';
    const btnIcon = hasRecord ? 'edit-2' : 'plus-circle';
    const btnClass = hasRecord
      ? 'text-surface-600 dark:text-surface-300 hover:text-brand-600 dark:hover:text-brand-400 hover:bg-surface-100 dark:hover:bg-surface-800'
      : 'text-brand-600 dark:text-brand-400 hover:bg-brand-50 dark:hover:bg-brand-950/40 border border-brand-200 dark:border-brand-800/50';

    html += `
      <tr class="hover:bg-surface-50/70 dark:hover:bg-surface-800/40 transition-colors">
        <td class="py-3 px-4">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-brand-500 text-white font-bold text-xs flex items-center justify-center shrink-0">
              ${initial}
            </div>
            <div class="min-w-0">
              <div class="font-bold text-surface-900 dark:text-white truncate flex items-center gap-1.5">
                <span>${escapeHtml(displayName)}</span>
                ${m.username !== displayName ? `<span class="text-[10px] text-surface-400 font-normal">(@${escapeHtml(m.username)})</span>` : ''}
              </div>
              <div class="text-[10px] text-surface-400 truncate">${escapeHtml(deptRole || 'สมาชิกทั่วไป')}</div>
            </div>
          </div>
        </td>
        <td class="py-3 px-4">${inHtml}</td>
        <td class="py-3 px-4">${outHtml}</td>
        <td class="py-3 px-4">${hoursHtml}</td>
        <td class="py-3 px-4">${statusBadge}</td>
        <td class="py-3 px-4">${noteHtml}</td>
        <td class="py-3 px-4 text-right">
          <button type="button" onclick="openOrgAttendanceModal(${m.user_id})"
            class="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-bold rounded-lg transition-colors ${btnClass}">
            <i data-lucide="${btnIcon}" class="w-3.5 h-3.5"></i>
            <span>${btnLabel}</span>
          </button>
        </td>
      </tr>
    `;
  });

  tbody.innerHTML = html;
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

/**
 * Open modal to add or edit attendance
 */
function openOrgAttendanceModal(userId) {
  const member = _orgAttMembersCache.find(m => String(m.user_id) === String(userId) || m.username === String(userId));
  if (!member) {
    if (typeof showToast === 'function') showToast('ไม่พบข้อมูลพนักงาน', 'error');
    return;
  }

  const modal = document.getElementById('orgAttendanceModal');
  if (!modal) return;

  const titleEl = document.getElementById('orgAttModalTitle');
  const userIdEl = document.getElementById('orgAttModalUserId');
  const attIdEl = document.getElementById('orgAttModalAttId');
  const dateEl = document.getElementById('orgAttModalDate');
  const nameEl = document.getElementById('orgAttModalUserName');
  const deptEl = document.getElementById('orgAttModalUserDept');
  const dateTextEl = document.getElementById('orgAttModalDateText');
  const avatarEl = document.getElementById('orgAttModalUserAvatar');
  const cinInput = document.getElementById('orgAttModalCheckInTime');
  const coutInput = document.getElementById('orgAttModalCheckOutTime');
  const statusSelect = document.getElementById('orgAttModalStatus');
  const noteInput = document.getElementById('orgAttModalNote');
  const deleteBtn = document.getElementById('orgAttModalDeleteBtn');

  userIdEl.value = member.user_id;
  dateEl.value = _orgAttCurrentDate || getOrgAttBangkokToday();
  nameEl.textContent = member.full_name || member.username;
  deptEl.textContent = [member.department, member.position || member.role].filter(Boolean).join(' • ') || 'ไม่ระบุแผนก';
  dateTextEl.textContent = formatOrgAttThaiDate(dateEl.value);
  avatarEl.textContent = (member.username || 'U').substring(0, 1).toUpperCase();

  if (member.check_in) {
    // Edit existing record
    titleEl.textContent = `แก้ไขเวลาเข้างาน: ${member.full_name || member.username}`;
    attIdEl.value = member.check_in.id || '';
    cinInput.value = (member.check_in.check_time || '08:30:00').substring(0, 8);
    coutInput.value = member.check_out ? (member.check_out.check_time || '').substring(0, 8) : '';
    statusSelect.value = member.check_in.status || 'manual_admin';
    noteInput.value = member.check_in.note || '';
    if (deleteBtn) deleteBtn.classList.remove('hidden');
  } else {
    // New manual entry
    titleEl.textContent = `บันทึกเวลาเข้างานแทน: ${member.full_name || member.username}`;
    attIdEl.value = '';
    cinInput.value = '08:30';
    coutInput.value = '';
    statusSelect.value = 'manual_admin';
    noteInput.value = '';
    if (deleteBtn) deleteBtn.classList.add('hidden');
  }

  modal.classList.remove('hidden');
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

function closeOrgAttendanceModal() {
  const modal = document.getElementById('orgAttendanceModal');
  if (modal) modal.classList.add('hidden');
}

/**
 * Save manual or edited attendance record
 */
async function saveOrgAttendanceRecord() {
  const userId = document.getElementById('orgAttModalUserId').value;
  const date = document.getElementById('orgAttModalDate').value;
  const cinTime = document.getElementById('orgAttModalCheckInTime').value;
  const coutTime = document.getElementById('orgAttModalCheckOutTime').value;
  const status = document.getElementById('orgAttModalStatus').value;
  const note = document.getElementById('orgAttModalNote').value;
  const submitBtn = document.getElementById('orgAttModalSubmitBtn');

  if (!userId || !date || !cinTime) {
    if (typeof showToast === 'function') showToast('กรุณากรอกเวลาเข้างาน', 'error');
    return;
  }

  const member = _orgAttMembersCache.find(m => String(m.user_id) === String(userId) || m.username === String(userId));
  const username = member ? member.username : '';

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.classList.add('opacity-60');
  }

  try {
    const res = await fetch('/api/admin/attendance/record', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username,
        date: date,
        check_in_time: cinTime,
        check_out_time: coutTime || null,
        status: (status === 'present' ? 'on_time' : status),
        note: note
      })
    });

    const data = await res.json();
    if (!res.ok || !data.ok) {
      if (typeof showToast === 'function') {
        showToast(data.error || 'ไม่สามารถบันทึกข้อมูลได้', 'error');
      } else {
        alert(data.error || 'ไม่สามารถบันทึกข้อมูลได้');
      }
      return;
    }

    if (typeof showToast === 'function') {
      showToast(data.message || 'บันทึกเวลาเข้างานเรียบร้อยแล้วค่ะ', 'success');
    }
    closeOrgAttendanceModal();
    loadOrgAttendance(_orgAttCurrentDate);
  } catch (err) {
    console.error('[saveOrgAttendanceRecord] Error:', err);
    if (typeof showToast === 'function') {
      showToast('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์', 'error');
    }
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.classList.remove('opacity-60');
    }
  }
}

/**
 * Delete attendance record
 */
async function deleteOrgAttendanceCurrentRecord() {
  const attId = document.getElementById('orgAttModalAttId').value;
  const userId = document.getElementById('orgAttModalUserId').value;
  const member = _orgAttMembersCache.find(m => (m.check_in && String(m.check_in.id) === String(attId)) || String(m.user_id) === String(userId));
  const username = member ? member.username : '';
  const date = document.getElementById('orgAttModalDate').value || _orgAttCurrentDate || getOrgAttBangkokToday();

  if (!username) {
    if (typeof showToast === 'function') showToast('ไม่พบชื่อผู้ใช้สำหรับลบ', 'error');
    return;
  }

  if (!confirm(`คุณแน่ใจหรือไม่ว่าต้องการลบบันทึกการลงเวลาของ ${username} ประจำวันที่ ${date}? สถานะจะกลับเป็น "ยังไม่ลงเวลา"`)) {
    return;
  }

  try {
    const res = await fetch('/api/admin/attendance/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username,
        date: date
      })
    });
    const data = await res.json();

    if (!res.ok || !data.ok) {
      if (typeof showToast === 'function') {
        showToast(data.error || 'ไม่สามารถลบบันทึกได้', 'error');
      } else {
        alert(data.error || 'ไม่สามารถลบบันทึกได้');
      }
      return;
    }

    if (typeof showToast === 'function') {
      showToast(data.message || 'ลบบันทึกเวลาเรียบร้อยแล้ว', 'success');
    }
    closeOrgAttendanceModal();
    loadOrgAttendance(_orgAttCurrentDate);
  } catch (err) {
    console.error('[deleteOrgAttendanceCurrentRecord] Error:', err);
    if (typeof showToast === 'function') {
      showToast('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์', 'error');
    }
  }
}

/**
 * Export current table view as CSV
 */
function exportOrgAttendanceCSV() {
  if (!_orgAttMembersCache || _orgAttMembersCache.length === 0) {
    if (typeof showToast === 'function') showToast('ไม่มีข้อมูลสำหรับส่งออก', 'info');
    return;
  }

  const dateStr = _orgAttCurrentDate || getOrgAttBangkokToday();
  const headers = ['ลำดับ', 'ชื่อ-นามสกุล', 'Username', 'อีเมล', 'แผนก', 'ตำแหน่ง', 'วันที่', 'เวลาเข้า', 'เวลาออก', 'ชั่วโมงทำงาน', 'สถานะ', 'ระยะทาง GPS (ม.)', 'หมายเหตุ'];

  const rows = _orgAttMembersCache.map((m, idx) => {
    let statusText = 'ยังไม่ลงเวลา';
    if (m.status === 'present') statusText = 'มาทำงาน (ตรงเวลา)';
    else if (m.status === 'late') statusText = 'มาสาย';
    else if (m.status === 'manual_admin') statusText = 'บันทึกโดยแอดมิน';

    const cinTime = m.check_in ? (m.check_in.check_time || '') : '';
    const coutTime = m.check_out ? (m.check_out.check_time || '') : '';
    const hours = m.total_hours || 0;
    const dist = (m.check_in && m.check_in.distance_meters !== null) ? Math.round(m.check_in.distance_meters) : '';
    const note = (m.check_in && m.check_in.note) ? m.check_in.note : '';

    return [
      idx + 1,
      `"${(m.full_name || '').replace(/"/g, '""')}"`,
      `"${(m.username || '').replace(/"/g, '""')}"`,
      `"${(m.email || '').replace(/"/g, '""')}"`,
      `"${(m.department || '').replace(/"/g, '""')}"`,
      `"${(m.position || m.role || '').replace(/"/g, '""')}"`,
      dateStr,
      cinTime,
      coutTime,
      hours,
      `"${statusText}"`,
      dist,
      `"${note.replace(/"/g, '""')}"`
    ].join(',');
  });

  const csvContent = '\uFEFF' + [headers.join(','), ...rows].join('\r\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `attendance_${dateStr}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  if (typeof showToast === 'function') {
    showToast(`ส่งออกไฟล์ attendance_${dateStr}.csv เรียบร้อยแล้ว`, 'success');
  }
}

function setOrgAttDateOffset(offsetDays) {
  const current = _orgAttCurrentDate || getOrgAttBangkokToday();
  const parts = current.split('-');
  const d = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
  d.setDate(d.getDate() + offsetDays);

  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  loadOrgAttendance(`${yyyy}-${mm}-${dd}`);
}

function setOrgAttDateToday() {
  loadOrgAttendance(getOrgAttBangkokToday());
}

// Global Exports
window.loadOrgAttendance = loadOrgAttendance;
window.filterOrgAttendanceTable = filterOrgAttendanceTable;
window.openOrgAttendanceModal = openOrgAttendanceModal;
window.closeOrgAttendanceModal = closeOrgAttendanceModal;
window.saveOrgAttendanceRecord = saveOrgAttendanceRecord;
window.deleteOrgAttendanceCurrentRecord = deleteOrgAttendanceCurrentRecord;
window.exportOrgAttendanceCSV = exportOrgAttendanceCSV;
window.setOrgAttDateOffset = setOrgAttDateOffset;
window.setOrgAttDateToday = setOrgAttDateToday;
