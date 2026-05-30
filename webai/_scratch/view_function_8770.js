8765:     startDmModal.classList.add('hidden');
8766:     startDmModal.classList.remove('flex', 'items-center', 'justify-center');
8767:   }
8768:   
8769:   // Ensure we are in the chat view when starting a private chat
8770:   if (typeof switchView === 'function' && state.currentView !== 'chat') {
8771:     switchView('chat');
8772:   }
8773:   
8774:   switchChat('dm', username, displayName);
8775: }
8776: 
8777: if (searchDmUser) {
8778:   searchDmUser.oninput = (e) => {
8779:     const query = e.target.value.toLowerCase().trim();
8780:     const filtered = allUsersForDm.filter(u =>
8781:       u.username.toLowerCase().includes(query) ||
8782:       (u.display_name && u.display_name.toLowerCase().includes(query))
8783:     );
8784:     renderDmUserList(filtered);
8785:   };
8786: }
8787: 
8788: 
8789: // ─── Initialization ────────────────────────
8790: async function initAppContent() {
8791:   console.log("🎮 Loading app content...");
8792:   try {
8793:     await loadStatus();
8794:     await loadHistory();
8795:     await loadFiles();
8796:     await loadSchedules();
8797:     await loadPersonas();
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
