1797:   lucide.createIcons();
1798: }
1799: 
1800: 
1801: // ─── View Management ────────────────────────
1802: function switchView(viewId) {
1803:   console.log("🚀 Switching view to:", viewId);
1804:   state.currentView = viewId;
1805:   
1806:   // Highlight active menu item
1807:   if (navItems) {
1808:     navItems.forEach(btn => {
1809:       btn.classList.toggle('active', btn.dataset.view === viewId);
1810:     });
1811:   }
1812: 
1813:   document.querySelectorAll('.view').forEach(sec => {
1814:     sec.classList.toggle('hidden', sec.id !== `view-${viewId}`);
1815:   });
1816: 
1817:   // Sync mobile bottom nav active state
1818:   document.querySelectorAll('.mobile-nav-btn[data-mobile-view]').forEach(btn => {
1819:     btn.classList.toggle('active', btn.dataset.mobileView === viewId);
1820:   });
1821: 
1822:   // 🔔 FIX: Reset currentChat if we left the chat area to allow notifications
1823:   // This tells the system we are no longer viewing the chat window
1824:   if (viewId !== 'dm' && viewId !== 'ai-chat') {
1825:     if (state.currentChat && state.currentChat.id) {
1826:         console.log("👋 Leaving chat room:", state.currentChat.id);
1827:         stopChatPolling();
1828:         state.currentChat = { type: null, id: null, name: null };
1829:     }
1830:   }
1831: 
1832:   if (viewId === 'home') loadDashboard();
1833:   if (viewId === 'profile') loadProfile();
1834:   if (viewId === 'search') {
1835:     if (searchInput) searchInput.focus();
1836:   }
1837:   if (viewId === 'notifications') loadNotifications();
1838:   if (viewId === 'stats') loadStats();
1839:   if (viewId === 'viz') initViz();
1840:   if (viewId === 'csv-explorer') initCSVExplorer();
1841:   if (viewId === 'calendar') { loadSchedules(); loadTodoTasks(); }
1842:   if (viewId === 'kanban') loadKanbanBoard();
1843:   if (viewId === 'wiki') { loadWikiPages(); renderWikiContent(); }
1844:   if (viewId === 'admin') { initAdminPanel(); loadGoogleDriveStatus(); }
1845:   if (viewId === 'kb') loadFiles();
1846:   if (viewId === 'drive') loadDriveContents(state.drive.currentFolderId);
1847:   if (viewId === 'summary') renderSummary();
1848:   if (viewId === 'whiteboard') initWhiteboard();
1849:   if (viewId === 'leave') loadLeaveData();
1850: 
1851:   // ─── Feed Auto-Refresh ───────────────────────
1852:   // Clear any existing feed poll interval when changing views
1853:   if (state.feedPollInterval) {
1854:     clearInterval(state.feedPollInterval);
1855:     state.feedPollInterval = null;
1856:   }
1857:   if (viewId === 'feed') {
1858:     loadPosts();
1859:     loadDailyDigest();
1860:     // Auto-refresh feed every 15 seconds so poll votes & new posts update live
1861:     state.feedPollInterval = setInterval(() => {
