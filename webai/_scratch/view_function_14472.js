14467:         // 3. Final UI cleanup
14468:         initIcons();
14469:         console.log('Dashboard initialized successfully.');
14470: 
14471:         // Switch to default home dashboard view instead of showing a blank screen
14472:         if (typeof switchView === 'function') {
14473:             switchView('home');
14474:         }
14475:     } catch (e) {
14476:         console.error('Failed to initialize dashboard content:', e);
14477:     }
14478: }
14479: 
14480: async function runReconciliation() {
14481:     const mpFiles = $('reconMPFiles').files;
14482:     const shipFiles = $('reconShipFiles').files;
14483:     const peakFiles = $('reconPeakFiles').files;
14484:     if (!mpFiles.length || !shipFiles.length || !peakFiles.length) { toast('กรุณาอัปโหลดไฟล์ให้ครบทั้ง 3 หมวดหมู่', 'error'); return; }
14485:     const btn = $('startReconBtn');
14486:     const originalText = btn.innerHTML;
14487:     btn.disabled = true;
14488:     btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> กำลังประมวลผล...`;
14489:     initIcons();
14490:     const formData = new FormData();
14491:     for (let f of mpFiles) formData.append('marketplace', f);
14492:     for (let f of shipFiles) formData.append('shipnity', f);
14493:     for (let f of peakFiles) formData.append('peak', f);
14494:     try {
14495:         const res = await fetch('/api/reconciliation/process', { method: 'POST', body: formData });
14496:         const data = await res.json();
14497:         if (data.ok) {
14498:             renderReconResults(data.summary);
14499:             toast('ประมวลผลการกระทบยอดสำเร็จ', 'success');
14500:             $('reconLastRun').textContent = 'ล่าสุดเมื่อ: ' + new Date().toLocaleString('th-TH');
14501:             const rb = $('resetReconBtn'); if (rb) rb.classList.remove('hidden');
14502:         } else { toast(data.error || 'เกิดข้อผิดพลาด', 'error'); }
14503:     } catch (e) { console.error(e); toast('การเชื่อมต่อล้มเหลว', 'error'); }
14504:     finally { btn.disabled = false; btn.innerHTML = originalText; initIcons(); }
14505: }
14506: 
14507: function resetReconciliation() {
14508:     window._reconData = null; _reconFilteredData = []; reconReportUrl = null;
14509:     $('reconSummary')?.classList.add('hidden');
14510:     $('reconResultsArea')?.classList.add('hidden');
14511:     $('resetReconBtn')?.classList.add('hidden');
14512:     ['reconMPFiles','reconShipFiles','reconPeakFiles'].forEach(id => { const el = $(id); if (el) el.value = ''; });
14513:     ['reconMPList','reconShipList','reconPeakList'].forEach(id => { const el = $(id); if (el) el.textContent = ''; });
14514:     const s = $('reconSearchInput'); if (s) s.value = '';
14515:     $('reconLastRun').textContent = 'ยังไม่มีการประมวลผล';
14516:     toast('ล้างข้อมูลเรียบร้อย', 'success');
14517: }
14518: 
14519: function renderReconResults(summary) {
14520:     const { total, issues, data, report_url, financial } = summary;
14521:     reconReportUrl = report_url;
14522:     window._reconData = data;
14523:     $('reconStatTotal').textContent = total.toLocaleString();
14524:     $('reconStatNormal').textContent = (total - issues).toLocaleString();
14525:     $('reconStatIssues').textContent = issues.toLocaleString();
14526:     const cEl = $('reconStatCancelled'); if (cEl) cEl.textContent = (financial?.mp_cancelled || 0).toLocaleString();
14527:     const fmt = (v) => '฿' + (v || 0).toLocaleString('th-TH', {minimumFractionDigits: 0, maximumFractionDigits: 0});
14528:     const ss = $('reconStatShipSales'); if (ss) ss.textContent = fmt(financial?.total_shipnity_sales);
14529:     const pa = $('reconStatPeakAmount'); if (pa) pa.textContent = fmt(financial?.total_peak_amount);
14530:     const pt = $('reconStatPeakTax'); if (pt) pt.textContent = fmt(financial?.total_peak_tax);
14531:     const dEl = $('reconStatDiff');
