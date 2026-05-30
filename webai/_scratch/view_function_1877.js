1872:   // Auto-hide sidebar on mobile after navigation
1873:   if (window.innerWidth < 1024) toggleSidebar(false);
1874: }
1875: 
1876: // Alias for index.html onclick
1877: function showView(viewId) { switchView(viewId); }
1878: 
1879: function applyProfile(profile) {
1880:   if (!profile) return;
1881: 
1882:   // Update Plan Badges & Org Info
1883:   const plan = profile.active_plan || 'free';
1884:   const planName = profile.plan_name || 'Free Plan';
1885:   const orgName = profile.org_name || 'Default Organization';
1886: 
1887:   // Desktop badge
1888:   const sidebarPlanBadge = $('sidebarPlanBadge');
1889:   if (sidebarPlanBadge) {
1890:     sidebarPlanBadge.textContent = planName;
1891:     sidebarPlanBadge.className = 'px-1.5 py-0.5 rounded text-[8px] font-extrabold uppercase tracking-wider block mt-1 w-max';
1892:     if (plan === 'free') {
1893:       sidebarPlanBadge.classList.add('bg-surface-100', 'text-surface-600', 'dark:bg-surface-800', 'dark:text-surface-400');
1894:     } else if (plan === 'pro') {
1895:       sidebarPlanBadge.classList.add('bg-emerald-50', 'text-emerald-600', 'dark:bg-emerald-950/40', 'dark:text-emerald-400', 'border', 'border-emerald-200/50', 'dark:border-emerald-800/30');
1896:     } else if (plan === 'business') {
1897:       sidebarPlanBadge.classList.add('bg-indigo-50', 'text-indigo-600', 'dark:bg-indigo-950/40', 'dark:text-indigo-400', 'border', 'border-indigo-200/50', 'dark:border-indigo-800/30');
1898:     }
1899:     sidebarPlanBadge.classList.remove('hidden');
1900:   }
1901: 
1902:   // Mobile badge
1903:   const mobilePlanBadge = $('mobilePlanBadge');
1904:   if (mobilePlanBadge) {
1905:     mobilePlanBadge.textContent = planName;
1906:     mobilePlanBadge.className = 'px-1.5 py-0.5 rounded text-[8px] font-extrabold uppercase tracking-wider';
1907:     if (plan === 'free') {
1908:       mobilePlanBadge.classList.add('bg-surface-100', 'text-surface-600', 'dark:bg-surface-800', 'dark:text-surface-400');
1909:     } else if (plan === 'pro') {
1910:       mobilePlanBadge.classList.add('bg-emerald-50', 'text-emerald-600', 'dark:bg-emerald-950/40', 'dark:text-emerald-400');
1911:     } else {
1912:       mobilePlanBadge.classList.add('bg-indigo-50', 'text-indigo-600', 'dark:bg-indigo-950/40', 'dark:text-indigo-400');
1913:     }
1914:     mobilePlanBadge.classList.remove('hidden');
1915:   }
1916: 
1917:   // Pro-lock indicators on nav items for free users
1918:   if (plan === 'free') {
1919:     const proNavIds = ['nav-drive', 'nav-viz'];
1920:     proNavIds.forEach(navId => {
1921:       const btn = $(navId);
1922:       if (!btn || btn.querySelector('.pro-lock-tag')) return;
1923:       const tag = document.createElement('span');
1924:       tag.className = 'pro-lock-tag ml-auto px-1 py-0.5 rounded text-[8px] font-black uppercase bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 flex-shrink-0';
1925:       tag.textContent = 'Pro';
1926:       btn.appendChild(tag);
1927:     });
1928:   } else {
1929:     document.querySelectorAll('.pro-lock-tag').forEach(el => el.remove());
1930:   }
1931: 
1932:   // Profile View Inputs
1933:   if ($('profileOrgDisplay')) $('profileOrgDisplay').value = orgName;
1934:   const profilePlanBadge = $('profilePlanBadge');
1935:   if (profilePlanBadge) {
1936:     profilePlanBadge.textContent = planName;
