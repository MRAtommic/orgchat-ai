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
8863:     setTimeout(() => {
8864:         loadChatList();
8865:         loadUnreadCounts();
8866:     }, 150);
8867:   }
8868: }
8869: 
8870: function closeMobileChat() {
8871:   if (!groupChatModal) return;
8872:   state.groupChat.isOpen = false;
8873:   groupChatModal.classList.add('hidden');
8874:   groupChatModal.classList.remove('chat-open');
8875:   document.getElementById('mobileMessagesBtn')?.classList.remove('active');
8876:   if (state.currentView !== 'dm' && state.currentView !== 'ai-chat') {
8877:     state.currentChat = { type: null, id: null, name: null };
8878:   }
8879: }
8880: 
8881: function showMobileChatSidebar() {
8882:   if (groupChatModal) groupChatModal.classList.remove('chat-open');
8883:   loadChatList();
8884: }
8885: 
8886: // Group Chat Handlers
8887: if (groupChatHead) {
8888:   groupChatHead.onclick = openMobileChat;
8889: }
8890: 
8891: if (closeGroupChat) {
8892:   closeGroupChat.onclick = () => {
8893:     state.groupChat.isOpen = false;
8894:     groupChatModal.classList.add('hidden');
8895:     groupChatModal.classList.remove('flex', 'items-center', 'justify-center');
8896:     // Also clear currentChat to allow notifications if we are not in that route
8897:     if (state.currentView !== 'dm' && state.currentView !== 'ai-chat') {
8898:       state.currentChat = { type: null, id: null, name: null };
8899:     }
8900:   };
8901: }
8902: 
8903: if (summonBotBtn) {
8904:   summonBotBtn.onclick = () => {
8905:     groupChatInput.value = '@bot ' + groupChatInput.value;
8906:     groupChatInput.focus();
8907:   };
8908: }
8909: 
8910: if (attachFileBtn) {
