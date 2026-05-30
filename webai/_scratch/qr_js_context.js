13821: }
13822: 
13823: // ─── QR Code Login ─────────────────────────────────────
13824: let _qrPollInterval = null;
13825: let _qrCountdownInterval = null;
13826: let _qrInstance = null;
13827: 
13828: async function showQRLogin() {
13829:   const loginForm = document.querySelector('#loginOverlay .p-8.space-y-4');
13830:   const qrModal = $('qrLoginModal');
13831:   const loginFooter = $('loginFooter');
13832:   if (!loginForm || !qrModal) return;
13833: 
13834:   loginForm.classList.add('hidden');
13835:   if (loginFooter) loginFooter.classList.add('hidden');
13836:   qrModal.classList.remove('hidden');
13837: 
13838:   // Generate QR token
13839:   try {
13840:     const res = await fetch('/api/qr/generate', { method: 'POST' });
13841:     const data = await res.json();
13842:     if (!data.ok) {
13843:       toast('ไม่สามารถสร้าง QR Code ได้', 'error');
13844:       return;
13845:     }
13846: 
13847:     const token = data.token;
13848:     const qrUrl = `${window.location.origin}/qr-login/${token}`;
13849:     const canvas = $('qrCodeCanvas');
13850:     
13851:     // Clear previous QR
13852:     canvas.innerHTML = '';
13853:     if (_qrInstance) _qrInstance = null;
13854: 
13855:     _qrInstance = new QRCode(canvas, {
13856:       text: qrUrl,
13857:       width: 200,
13858:       height: 200,
13859:       colorDark: '#1e293b',
13860:       colorLight: '#ffffff',
13861:       correctLevel: QRCode.CorrectLevel.M
13862:     });
13863: 
13864:     // Start countdown (5 minutes)
13865:     let remaining = 300;
13866:     const countdownEl = $('qrCountdown');
13867:     const statusEl = $('qrStatus');
13868:     
13869:     if (_qrCountdownInterval) clearInterval(_qrCountdownInterval);
13870:     _qrCountdownInterval = setInterval(() => {
13871:       remaining--;
13872:       const m = Math.floor(remaining / 60);
13873:       const s = (remaining % 60).toString().padStart(2, '0');
13874:       if (countdownEl) countdownEl.textContent = `${m}:${s}`;
13875:       if (remaining <= 0) {
13876:         clearInterval(_qrCountdownInterval);
13877:         clearInterval(_qrPollInterval);
13878:         if (statusEl) statusEl.innerHTML = `
13879:           <div class="w-2 h-2 bg-red-400 rounded-full"></div>
13880:           <span class="text-red-500">QR Code หมดอายุ กรุณาสร้างใหม่</span>
13881:         `;
13882:       }
13883:     }, 1000);
13884: 
13885:     // Start polling
13886:     if (_qrPollInterval) clearInterval(_qrPollInterval);
13887:     _qrPollInterval = setInterval(async () => {
13888:       try {
13889:         const pollRes = await fetch(`/api/qr/poll/${token}`);
13890:         const pollData = await pollRes.json();
13891:         
13892:         if (pollData.ok && pollData.status === 'approved') {
13893:           // SUCCESS!
13894:           clearInterval(_qrPollInterval);
13895:           clearInterval(_qrCountdownInterval);
13896:           
13897:           if (statusEl) statusEl.innerHTML = `
13898:             <div class="w-2 h-2 bg-emerald-400 rounded-full"></div>
13899:             <span class="text-emerald-600 font-black">✅ อนุมัติแล้ว! กำลังเข้าระบบ...</span>
13900:           `;
13901:           
13902:           state.user = pollData.user;
13903:           state.username = pollData.user;
13904:           
13905:           setTimeout(() => {
13906:             $('loginOverlay').classList.add('hidden');
13907:             toast(`ยินดีต้อนรับคุณ ${pollData.user} (QR Login)`, 'success');
13908:             initAppContent();
13909:             loadNotifications();
13910:             loadChatList();
13911:             loadUnreadCounts();
13912:           }, 1000);
13913:         } else if (!pollData.ok) {
13914:           // Token expired or error
13915:           clearInterval(_qrPollInterval);
13916:           clearInterval(_qrCountdownInterval);
13917:         }
13918:       } catch (e) {
13919:         console.error('QR Poll error:', e);
13920:       }
13921:     }, 2000);
13922: 
13923:   } catch (e) {
13924:     console.error('QR Login Error:', e);
13925:     toast('ไม่สามารถสร้าง QR Code ได้', 'error');
13926:   }
13927: 
13928:   lucide.createIcons();
13929: }
13930: 
13931: function hideQRLogin() {
13932:   const loginForm = document.querySelector('#loginOverlay .p-8.space-y-4');
13933:   const qrModal = $('qrLoginModal');
13934:   const loginFooter = $('loginFooter');
13935:   
13936:   if (loginForm) loginForm.classList.remove('hidden');
13937:   if (qrModal) qrModal.classList.add('hidden');
13938:   if (loginFooter) loginFooter.classList.remove('hidden');
13939:   
13940:   // Cleanup
13941:   if (_qrPollInterval) clearInterval(_qrPollInterval);
13942:   if (_qrCountdownInterval) clearInterval(_qrCountdownInterval);
13943: }
13944: 
13945: // ─── QR Code Scanner (Camera) ─────────────────────────────
13946: let _html5QrScanner = null;
13947: 
13948: function openQRScanner() {
13949:   const modal = $('qrScannerModal');
13950:   if (!modal) return;
