7901:   // Socket Join
7902:   if (socket) {
7903:     const socketRoom = type === 'room' ? `room_${id}` : `dm_${id}`;
7904:     socket.emit('join', { room: socketRoom });
7905:     
7906:     // Also join self room for DMs
7907:     const currentUser = (typeof state.user === 'object' ? state.user?.username : state.user);
7908:     if (currentUser) {
7909:         socket.emit('join', { room: `dm_${currentUser}` });
7910:     }
7911: 
7912:     // Update Call Button Visibility
7913:     if (typeof checkCallButtonsVisibility === 'function') {
7914:       checkCallButtonsVisibility();
7915:     }
7916: 
7917:     // Notify backend that user is online in this chat
7918:     socket.emit('user_online', {
7919:       room: name || 'General',
7920:       room_id: id,
7921:       type: type,
7922:       username: state.username
7923:     });
7924:   }
7925: 
7926:   // Mobile Transition & Visibility
7927:   if (groupChatModal) {
7928:     groupChatModal.classList.remove('hidden'); // Ensure it's not hidden
7929:     if (window.innerWidth < 1024) {
7930:       groupChatModal.classList.add('chat-open'); // Open the chat view on mobile
7931:     }
7932:   }
7933: 
7934:   state.lastRendered.messages = ''; // Reset to force re-render
7935:   if (groupChatMessages) {
7936:     groupChatMessages.innerHTML = `
7937:       <div class="flex flex-col items-center justify-center py-20 animate-pulse">
7938:         <div class="w-12 h-12 bg-surface-100 dark:bg-surface-800 rounded-2xl flex items-center justify-center mb-4">
7939:           <i data-lucide="loader-2" class="w-6 h-6 text-brand-600 animate-spin"></i>
7940:         </div>
7941:         <div class="text-[10px] font-black uppercase tracking-widest opacity-50">กำลังโหลดข้อความ...</div>
7942:       </div>
7943:     `;
7944:   }
7945: 
7946:   if (chatHeaderName) chatHeaderName.textContent = name;
7947:   if (chatInputArea) chatInputArea.classList.remove('hidden');
7948: 
7949:   // Reverted mobile view logic: keep both sidebar and main area visible if layout permits
7950:   // No longer adding 'chat-open' class
7951: 
7952:   // Update Avatar & Add Member Button
7953:   if (type === 'room') {
7954:     if (chatHeaderAvatar) {
7955:       if (avatarUrl) {
7956:         chatHeaderAvatar.innerHTML = `<img src="${avatarUrl}" class="w-full h-full object-cover">`;
7957:       } else {
7958:         chatHeaderAvatar.innerHTML = '<i data-lucide="users" class="w-5 h-5"></i>';
7959:       }
7960:     }
