import re
import os

index_path = "../templates/index.html"
view_profile_path = "view_profile_extracted.html"
view_settings_path = "view_settings_extracted.html"

# Load current index.html
with open(index_path, "r", encoding="utf-8") as f:
    index_content = f.read()

# Load extracted profile
with open(view_profile_path, "r", encoding="utf-8") as f:
    profile_html = f.read()

# Load extracted settings (original)
with open(view_settings_path, "r", encoding="utf-8") as f:
    settings_html = f.read()

# Build the replacement setting block with the QR Login Scanner included beautifully
settings_with_qr_html = """<!-- Settings View (Original System Settings) -->
        <section id="view-settings"
          class="view hidden flex-1 flex flex-col items-center overflow-hidden animate-in fade-in duration-300">
          <header
            class="h-14 border-b border-surface-100 dark:border-surface-800 flex items-center justify-between px-6 bg-white dark:bg-surface-900 w-full">
            <h2 class="font-semibold text-sm">การตั้งค่าระบบ</h2>
          </header>
          <div class="p-8 flex-1 min-h-0 overflow-y-auto w-full max-w-2xl space-y-4">
            <div class="p-6 bg-white dark:bg-surface-900 border border-surface-200 rounded-xl">
              <h3 class="font-bold text-sm mb-1 uppercase text-surface-500">Google Gemini Connectivity</h3>
              <p class="text-xl font-bold mb-4">Gemini 2.0 Flash AI</p>
              <button id="changeKeyBtn" class="btn-secondary w-full uppercase">RESET API KEY</button>
            </div>

            <!-- PWA & OS Notification Settings -->
            <div class="p-6 bg-white dark:bg-surface-900 border border-surface-200 rounded-xl space-y-4">
              <h3 class="font-bold text-sm mb-1 uppercase text-surface-500 flex items-center gap-2">
                <i data-lucide="bell" class="w-4 h-4 text-brand-600"></i> Push Notifications
              </h3>
              <p class="text-xs text-surface-400">อนุญาตให้ระบบส่งการแจ้งเตือนไปยังมือถือหรือคอมพิวเตอร์ของคุณ
                แม้ในขณะที่ไม่ได้เปิดหน้าเว็บอยู่</p>

              <div id="notifStatusBox"
                class="p-4 bg-surface-50 dark:bg-surface-800/50 rounded-2xl border border-surface-100 dark:border-surface-700 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div class="flex items-center gap-3">
                  <div id="notifStatusIndicator" class="w-2.5 h-2.5 rounded-full bg-surface-300"></div>
                  <span id="notifStatusText"
                    class="text-xs font-bold uppercase tracking-wider text-surface-400">ยังไม่ได้เปิดใช้งาน</span>
                </div>
                <button id="requestNotifBtn"
                  class="btn-primary py-2 px-6 text-[11px] font-black uppercase tracking-widest shadow-lg shadow-brand-500/20">
                  เปิดใช้งานการแจ้งเตือน
                </button>
              </div>

              <div class="pt-2">
                <button id="testNotifBtn"
                  class="text-[10px] font-bold text-brand-600 hover:underline uppercase tracking-widest flex items-center gap-1.5 opacity-50 cursor-not-allowed disabled:opacity-50"
                  disabled>
                  <i data-lucide="send" class="w-3 h-3"></i> ส่งข้อความทดสอบ
                </button>
              </div>
            </div>

            <!-- QR Login Scanner (New) -->
            <div class="p-6 bg-white dark:bg-surface-900 border border-surface-200 dark:border-surface-800 rounded-xl space-y-4">
              <h3 class="font-bold text-sm mb-1 uppercase text-surface-500 flex items-center gap-2">
                <i data-lucide="qr-code" class="w-4 h-4 text-emerald-600"></i> QR Login Scanner
              </h3>
              <p class="text-xs text-surface-400">ใช้มือถือเครื่องนี้สแกน QR Code บนหน้าจอคอมพิวเตอร์เพื่อเข้าสู่ระบบทันที</p>
              
              <button onclick="openQRScanner()" 
                class="btn-primary w-full py-4 bg-emerald-600 hover:bg-emerald-700 text-xs font-black uppercase tracking-widest shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2 border-none">
                <i data-lucide="camera" class="w-5 h-5"></i> เปิดกล้องสแกน QR Code เพื่อ Login
              </button>
            </div>

            <!-- App Installation Section -->
            <div id="pwaInstallSection"
              class="p-6 bg-white dark:bg-surface-900 border border-surface-200 rounded-xl space-y-4">
              <h3 class="font-bold text-sm mb-1 uppercase text-surface-500 flex items-center gap-2">
                <i data-lucide="smartphone" class="w-4 h-4 text-brand-600"></i> ดาวน์โหลด/ติดตั้ง APK (ผ่าน PWA)
              </h3>
              <p class="text-xs text-surface-400">ติดตั้งแอป OrgChat ลงในหน้าจอโฮมเพื่อการใช้งานที่สะดวกเหมือนแอปมือถือ
                (ทดแทน APK แบบเดิม)</p>

              <button id="installAppBtn"
                class="btn-primary w-full py-3 text-[11px] font-black uppercase tracking-widest shadow-lg shadow-brand-500/20 flex items-center justify-center gap-2">
                <i data-lucide="download-cloud" class="w-4 h-4"></i> ติดตั้งคัดลอกลงมือถือ (APK Style)
              </button>
            </div>
          </div>
        </section>"""

# Find the start tag of view-profile in templates/index.html
start_match = re.search(r'<!-- Profile Settings View -->', index_content)
if not start_match:
    print("Could not find start marker in templates/index.html")
    exit(1)

# Find the start tag of view-leave in templates/index.html (which comes right after view-profile)
end_match = re.search(r'<!-- Leave Management View -->', index_content)
if not end_match:
    print("Could not find end marker in templates/index.html")
    exit(1)

start_pos = start_match.start()
end_pos = end_match.start()

# Let's see the text we are replacing
target_to_replace = index_content[start_pos:end_pos]
print(f"Target size to replace: {len(target_to_replace)} bytes")

# Ensure it contains the corrupted elements
if "class=\"bg-" in target_to_replace:
    print("Detected corruption class=\"bg- inside target to replace.")
else:
    print("Warning: class=\"bg-\" not found in replacement target. Double checking...")

# Combine clean profile and clean settings (with QR)
new_block = "<!-- Profile Settings View -->\n        " + profile_html + "\n\n        " + settings_with_qr_html + "\n\n        "

# Perform replacement
new_index_content = index_content[:start_pos] + new_block + index_content[end_pos:]

# Save a backup of the broken index.html before editing
with open("../templates/index.html.bak", "w", encoding="utf-8") as bak:
    bak.write(index_content)
print("Saved backup to templates/index.html.bak")

# Write the patched index.html
with open(index_path, "w", encoding="utf-8") as f:
    f.write(new_index_content)
print("Patched index.html successfully!")

# Run validations
# 1. Count occurrences of googleDriveSection
count = new_index_content.count('id="googleDriveSection"')
print(f"Occurrences of googleDriveSection in new file: {count}")
if count == 1:
    print("Perfect! Only one googleDriveSection exists (in view-admin).")
else:
    print(f"Warning! Found {count} occurrences. Expected exactly 1.")
