// --- OrgChat AI: BILLING Module ---

(function() {
  const _billingAutoSpeakBtn = document.getElementById('autoSpeakBtn');
  let _billingAutoSpeakEnabled = false;

  if (_billingAutoSpeakBtn && !_billingAutoSpeakBtn._hasHandler) {
    _billingAutoSpeakBtn._hasHandler = true;
    _billingAutoSpeakBtn.onclick = () => {
      _billingAutoSpeakEnabled = !_billingAutoSpeakEnabled;
      _billingAutoSpeakBtn.classList.toggle('text-brand-600', _billingAutoSpeakEnabled);
      _billingAutoSpeakBtn.classList.toggle('bg-brand-50', _billingAutoSpeakEnabled);
      toast(`อ่านข้อความอัตโนมัติ: ${_billingAutoSpeakEnabled ? 'เปิด' : 'ปิด'}`, 'info');
    };
  }
})();

function speak(text) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();

  // Clean markdown for clearer speech
  const cleanText = text.replace(/[#*`_~]/g, '').slice(0, 1000); 
  const utter = new SpeechSynthesisUtterance(cleanText);
  
  // Detect Thai vs English
  const isThai = /[\u0E00-\u0E7F]/.test(text);
  
  // Try to find natural voices (Google voices are usually best)
  const voices = window.speechSynthesis.getVoices();
  const bestVoice = voices.find(v => v.name.includes('Google') && v.lang.includes(isThai ? 'th' : 'en')) || 
                    voices.find(v => v.lang.includes(isThai ? 'th' : 'en'));
  
  if (bestVoice) utter.voice = bestVoice;
  utter.lang = isThai ? 'th-TH' : 'en-US';
  utter.rate = 1.0;
  utter.pitch = 1.0;
  
  window.speechSynthesis.speak(utter);
}