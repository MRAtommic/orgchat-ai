8798:     // Load dashboard data (including weather) on init
8799:     await loadDashboard();
8800:     console.log("✅ App Content Loaded.");
8801:     
8802:     // Switch to default home dashboard view instead of showing a blank screen
8803:     if (typeof switchView === 'function') {
8804:       switchView('home');
8805:     }
8806:   } catch (e) {
8807:     console.error("Content Load Failure:", e);
8808:   }
8809: }
8810: 
8811: // Profile Events ────────────────────────────
8812: bgPresetBtns.forEach(btn => {
8813:   btn.onclick = () => {
8814:     const bg = btn.dataset.bg;
8815:     if (bg === 'custom') {
8816:       const color = prompt('ระบุรหัสสี:', '#2563eb');
8817:       if (color) {
8818:         document.body.style.background = color;
8819:         if (profileCoverPreview) profileCoverPreview.style.background = color;
8820:         state.tempBackground = color;
8821:       }
8822:     } else {
8823:       document.body.style.background = bg;
8824:       if (profileCoverPreview) profileCoverPreview.style.background = bg;
8825:       state.tempBackground = bg;
8826:       bgPresetBtns.forEach(b => b.classList.remove('border-brand-600'));
8827:       btn.classList.add('border-brand-600');
8828:     }
8829:   };
8830: });
8831: 
8832: // Mobile Chat Management
8833: function openMobileChat() {
8834:   if (!groupChatModal) return;
8835:   state.groupChat.isOpen = !state.groupChat.isOpen;
8836: 
8837:   if (state.groupChat.isOpen) {
8838:     groupChatModal.classList.remove('hidden');
8839:     groupChatModal.classList.remove('chat-open'); // Messenger style: start at list
8840:     loadChatList();
8841:     loadUnreadCounts();
8842:     
8843:     document.getElementById('mobileMessagesBtn')?.classList.add('active');
8844: 
8845:     setTimeout(() => {
8846:       initIcons();
8847:     }, 100);
8848:   } else {
8849:     groupChatModal.classList.add('hidden');
8850:     document.getElementById('mobileMessagesBtn')?.classList.remove('active');
8851:     if (state.currentView !== 'dm' && state.currentView !== 'ai-chat') {
8852:         state.currentChat = { type: null, id: null, name: null };
8853:     }
8854:   }
8855: }
8856: 
8857: function backToChatList() {
8858:   if (groupChatModal) {
8859:     groupChatModal.classList.remove('chat-open'); // Slide main area away
8860:     state.currentChat = { type: null, id: null, name: null };
8861:     
8862:     // Smooth delay for clearing and reloading
