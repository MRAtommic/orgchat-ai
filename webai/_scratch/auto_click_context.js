8441:   }
8442: 
8443:   const dismissToast = () => {
8444:     el.style.animation = 'chatPopUpOut 0.3s ease forwards';
8445:     setTimeout(() => el.remove(), 300);
8446:   };
8447: 
8448:   // ✅ Auto-dismiss after 5s for a clean pop-up feel
8449:   const dismissTimer = setTimeout(dismissToast, 5000);
8450:   el._dismissTimer = dismissTimer;
8451: 
8452:   el.querySelector('.close-toast-btn').onclick = (e) => {
8453:     e.stopPropagation();
8454:     dismissToast();
8455:   };
8456: 
8457:   el.onclick = () => {
8458:     dismissToast();
8459:     if (type === 'room') {
8460:       switchChat('room', id, chatName);
8461:     } else {
8462:       switchChat('dm', id, chatName);
8463:     }
8464:     if (groupChatModal.classList.contains('hidden')) {
8465:       if (groupChatHead) groupChatHead.click();
8466:     }
8467:   };
8468: }
8469: 
8470: function toggleChatFullscreen() {
8471:   const modal = $('groupChatModal');
8472:   const icon = $('fullscreenIcon');
8473:   if (!modal) return;
8474:   modal.classList.toggle('fullscreen');
8475:   const isFullscreen = modal.classList.contains('fullscreen');
8476:   if (icon) {
8477:     icon.setAttribute('data-lucide', isFullscreen ? 'minimize-2' : 'maximize-2');
8478:     initIcons();
8479:   }
8480: }
