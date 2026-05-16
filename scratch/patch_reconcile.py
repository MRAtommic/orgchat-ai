import sys

file_path = r'c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\google_drive_service.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_block = [
    '            # 3. Match Logic (Smart WHT & BE Date Handling)\n',
    '            matches = []\n',
    '            matched_inv_indices = set()\n',
    '            \n',
    '            from datetime import datetime as dt\n',
    '            def parse_date(d_str):\n',
    '                if not d_str or d_str == "-": return None\n',
    '                d_str = str(d_str).strip()\n',
    '                try: \n',
    '                    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):\n',
    '                        try: \n',
    '                            parsed = dt.strptime(d_str, fmt)\n',
    '                            if parsed.year > 2500: parsed = parsed.replace(year=parsed.year - 543)\n',
    '                            return parsed\n',
    '                        except: continue\n',
    '                    return None\n',
    '                except: return None\n',
    '            \n',
    '            for p in payments:\n',
    '                try: s_amount = float(str(p["amount"]).replace(",", ""))\n',
    '                except: s_amount = 0\n',
    '                s_receiver = str(p["receiver"]).strip()\n',
    '                s_date = parse_date(str(p["date"]).strip())\n',
    '                s_link = p["link"]\n',
    '\n',
    '                found = False\n',
    '                for inv_idx, inv in enumerate(invoices):\n',
    '                    if inv_idx in matched_inv_indices: continue\n',
    '                    if len(inv) < 15: continue\n',
    '                    \n',
    '                    try:\n',
    '                        i_amount = float(str(inv[10]).replace(",", ""))\n',
    '                        i_wht = float(str(inv[14]).replace(",", "")) if inv[14] != "-" else 0\n',
    '                    except: i_amount = i_wht = 0\n',
    '                    \n',
    '                    i_vendor = str(inv[3]).strip()\n',
    '                    i_date = parse_date(str(inv[2]).strip())\n',
    '                    i_link = str(inv[19]).strip() if len(inv) > 19 else ""\n',
    '\n',
    '                    amount_match = (abs(s_amount - i_amount) < 5.0)\n',
    '                    wht_match = (abs(s_amount - (i_amount - i_wht)) < 5.0) if i_wht > 0 else False\n',
    '                    name_match = (s_receiver in i_vendor or i_vendor in s_receiver) if s_receiver != "-" and i_vendor != "-" else False\n',
    '                    date_match = (abs((s_date - i_date).days) <= 7) if s_date and i_date else False\n',
    '\n',
    '                    if (amount_match or wht_match) and (name_match or date_match):\n',
    '                        status = "✅ จับคู่สำเร็จ"\n',
    '                        note = f"พบจาก{p[\'source\']}: " + (f"หัก WHT {i_wht} ถูกต้อง" if wht_match else "จ่ายยอดเต็ม")\n',
    '                        if i_wht > 0 and amount_match: note += " ⚠️ ลืมหัก WHT?"\n',
    '                        matches.append([dt.now().strftime("%d/%m/%Y %H:%M"), status, str(p["date"]), s_amount, i_vendor, s_link, i_link, note])\n',
    '                        matched_inv_indices.add(inv_idx)\n',
    '                        found = True\n',
    '                        break\n'
]

start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if '# 3. Match Logic' in line and 'Smart' not in line:
        start_idx = i
    if 'if not found:' in line and start_idx != -1:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    new_lines = lines[:start_idx] + new_block + lines[end_idx:]
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Successfully patched!")
else:
    print(f"Failed to find indices: {start_idx}, {end_idx}")
