15101: 
15102: // ═══════════════════════════════════════════════════════════════
15103: // Google Drive & Sheets Per-User Connection (OAuth2)
15104: // ═══════════════════════════════════════════════════════════════
15105: 
15106: async function loadGoogleDriveStatus() {
15107:   const loading = $('googleConnectLoading');
15108:   const notConnected = $('googleNotConnected');
15109:   const connected = $('googleConnected');
15110:   const notConfigured = $('googleOAuthNotConfigured');
15111: 
15112:   if (!loading) return; // Section not present
15113: 
15114:   // Show loading
15115:   loading.classList.remove('hidden');
15116:   notConnected.classList.add('hidden');
15117:   connected.classList.add('hidden');
15118: 
15119:   try {
15120:     const data = await apiFetch('/api/auth/google/status');
15121: 
15122:     loading.classList.add('hidden');
15123: 
15124:     if (data.connected) {
15125:       // Show connected state
15126:       connected.classList.remove('hidden');
15127:       notConnected.classList.add('hidden');
15128: 
15129:       if ($('googleConnectedEmail')) {
15130:         $('googleConnectedEmail').textContent = data.email || '—';
15131:       }
15132:       if ($('googleSheetLink') && data.spreadsheet_url) {
15133:         $('googleSheetLink').href = data.spreadsheet_url;
15134:       }
15135:       if ($('googleDriveLink') && data.drive_folder_url) {
15136:         $('googleDriveLink').href = data.drive_folder_url;
15137:       }
15138:     } else {
15139:       // Show not connected state
15140:       notConnected.classList.remove('hidden');
15141:       connected.classList.add('hidden');
15142: 
15143:       // Check if OAuth2 is configured
15144:       if (data.oauth2_available === false && notConfigured) {
15145:         notConfigured.classList.remove('hidden');
15146:         if ($('googleConnectBtn')) {
15147:           $('googleConnectBtn').classList.add('opacity-50', 'pointer-events-none');
15148:         }
15149:       }
15150:     }
15151:   } catch (err) {
15152:     console.error('Failed to check Google connection:', err);
15153:     loading.classList.add('hidden');
15154:     notConnected.classList.remove('hidden');
15155:   }
15156: 
15157:   lucide.createIcons();
15158: }
15159: 
15160: async function disconnectGoogleDrive() {
15161:   if (!confirm('ต้องการยกเลิกการเชื่อมต่อ Google Drive & Sheets หรือไม่?\n\nข้อมูลที่บันทึกไว้ใน Google Sheets ของคุณจะยังอยู่ แต่ระบบจะไม่เขียนข้อมูลใหม่ลงไปอีก')) {
15162:     return;
15163:   }
15164: 
15165:   const btn = $('googleDisconnectBtn');
15166:   if (btn) {
15167:     btn.disabled = true;
15168:     btn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> กำลังยกเลิก...';
15169:     lucide.createIcons();
15170:   }
15171: 
15172:   try {
15173:     const res = await apiFetch('/api/auth/google/disconnect', {
15174:       method: 'POST'
15175:     });
15176: 
15177:     if (res.ok) {
15178:       toast('ยกเลิกการเชื่อมต่อ Google สำเร็จ', 'success');
15179:       loadGoogleDriveStatus();
15180:     } else {
15181:       toast('เกิดข้อผิดพลาด: ' + (res.error || 'Unknown'), 'error');
15182:     }
15183:   } catch (err) {
15184:     toast('ไม่สามารถยกเลิกการเชื่อมต่อได้', 'error');
15185:     console.error('Disconnect error:', err);
