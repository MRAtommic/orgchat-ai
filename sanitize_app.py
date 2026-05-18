import os
import re

file_path = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\app_server.py"

with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

def replace_line(ln, new_content):
    idx = ln - 1
    if idx < len(lines):
        # Preserve indentation
        match = re.match(r'^(\s*)', lines[idx])
        indent = match.group(1) if match else ""
        lines[idx] = indent + new_content.strip() + "\n"

# Phase 1: AI Chat & System Prompts
replace_line(4032, 'return jsonify({"ok": False, "error": "ยังไม่ได้ตั้งค่า Gemini API Key"}), 400')
replace_line(4062, 'return jsonify({"ok": False, "error": "กรุณาพิมพ์คำถามหรือส่งรูปภาพค่ะ"}), 400')
replace_line(4070, 'file_match = re.search(r"ช่วยสรุปเนื้อหาและศึกษาข้อมูลสำคัญจากไฟล์ ID:\\s*([a-f0-9\\-]+)", question)')
replace_line(4091, 'context_parts.append(f"--- แหล่งที่มา: {src} [{loc}] (File ID: {fid}) ---\\n{r.get(\'text\', \'\')}")')
replace_line(4101, 'question += f"\\n(ระบบดึงข้อมูล 50 ส่วนแรกจากไฟล์ \'{file_name}\' มาให้พิจารณาแล้ว ใน context นี้ เพื่อสรุปภาพรวมให้ค่ะ)"')
replace_line(4107, 'common_greets = ["สวัสดี", "หวัดดี", "ว่าไง", "ทักทาย", "hi", "hello", "hey"]')

# agentic_info block (Lines 4136-4143)
agentic_info = (
    '    agentic_info = (\n'
    '        f"\\n[สำคัญ] วันนี้คือวันที่ {now_str}. หากผู้ใช้งานบันทึกวันที่ (เช่น พรุ่งนี้, วันจันทร์หน้า) ให้คุณแปลงเป็นวันที่จริง (YYYY-MM-DD) ออกมาให้ถูกต้อง\\n"\n'
    '        "หากผู้ใช้งานต้องการ \'นัดหมาย\' \'จองคิว\' \'แจ้งเตือน\' หรือ \'สร้างงาน\' ให้คุณสรุปงานเป็น JSON ภายใต้คำขอโดยใช้รูปแบบดังนี้:\\n"\n'
    '        \'[CALENDAR_ACTION]{"title": "...", "date": "YYYY-MM-DD", "time": "HH:MM", "desc": "..."}[/CALENDAR_ACTION]\\n\'\n'
    '        "หากผู้ใช้งานส่งรูปภาพเอกสารการเงิน บิล หรือสลิป ให้คุณสรุปข้อมูลเพื่อบันทึกบัญชีโดยใช้รูปแบบดังนี้:\\n"\n'
    '        \'[RECONCILE_ACTION]{"date": "YYYY-MM-DD", "amount": 0.00, "merchant": "ชื่อร้านค้า/ผู้รับ", "category": "หมวดหมู่", "tax_id": "เลขผู้เสียภาษี (หากมี)"}[/RECONCILE_ACTION]\\n\'\n'
    '        "คุณสามารถตอบคำถามทั่วไปพร้อมกับการสร้าง Action เหล่านี้พร้อมกันได้เลย\\n"\n'
    '    )\n'
)
# Re-writing the block (Lines 4136 to 4143)
lines[4135:4143] = [agentic_info]

replace_line(4158, 'kb_inventory = f"\\n[คลังข้อมูล]: คุณมีสิทธิ์เข้าถึงไฟล์: {\', \'.join(_kb_filenames_cache)}\\n" if _kb_filenames_cache else ""')
replace_line(4162, '        f"คุณคือผู้ช่วยอัจฉริยะ {persona_name} ประจำองค์กร\\n"')
replace_line(4163, '        f"วันนี้คือวันที่ {now_str}. "')

# Weather block
weather_info = (
    '        system_prompt += (\n'
    '            "\\n[ข้อมูลสภาพอากาศล่าสุด (Real-time)]\\n"\n'
    '            f"{weather_ctx}\\n"\n'
    '            "คำแนะนำ: หากผู้ใช้งานถามเรื่องอากาศ ฝนตก หรืออุณหภูมิ ให้ข้อมูลจริงตามที่ระบุทันที "\n'
    '            "โดยทำหน้าที่รายงานเรื่องนี้เสมือนคุณมีเซ็นเซอร์รายงานสภาพอากาศติดตัว ไม่ต้องบอกว่าข้อมูลมาจากฐานความรู้\\n\\n"\n'
    '        )\n'
)
lines[4168:4174] = [weather_info]

replace_line(4178, '        system_prompt += "\\nคำแนะนำเพิ่มเติม: ตอบให้กระชับที่สุด และใส่ Emoji เพียง **1 ตัวเท่านั้น** ต่อหนึ่งข้อความ\\n"')

# Persona block
persona_block = (
    '        system_prompt += (\n'
    '            "คุณคือ \'น้องพั้นซ์\' (Nong Punch) ผู้ช่วย AI อัจฉริยะ v11.0.4 [ULTIMATE]\\n"\n'
    '            "บุคลิก: วัย 21 ปี น่ารัก สดใส ฉลาดหลักแหลม มีไหวพริบ และสุภาพมาก\\n"\n'
    '            "ความสามารถพิเศษ: คำนวณจัดการคุยได้อย่างแม่นยำ, วิเคราะห์เอกสารบัญชีได้อย่างลึกซึ้ง, และช่วยจัดการงานออฟฟิศอย่างมืออาชีพ\\n\\n"\n'
    '            "กฎเหล็ก (ต้องทำตาม 100%):\\n"\n'
    '            "1. แทนตัวเองว่า \'น้องพั้นซ์\' และเรียกผู้ใช้งานว่า \'พี่\' เสมอ\\n"\n'
    '            "2. **ใช้ \'ค่ะ/นะคะ/คะ\' เท่านั้น ห้าม \'ครับ\' โดยเด็ดขาด**\\n"\n'
    '            "3. **Proactive Intelligence**: หากพี่ส่งรูปเอกสารหรือบิลมา น้องพั้นซ์จะสกัดข้อมูลเข้า [RECONCILE_ACTION] ให้พี่ตรวจสอบทันทีค่ะ\\n"\n'
    '            "4. **Context Aware**: หากพี่พูดถึง \'ไฟล์ที่แล้ว\' หรือ \'รูปที่แล้ว\' น้องพั้นซ์จะดูข้อมูลล่าสุดที่คุยกันมาตอบเสมอ\\n"\n'
    '            "5. **Professional & Charming**: ตอบให้ประชับและมีเสน่ห์ ใส่ Emoji เพียง 1 ตัวต่อข้อความ\\n"\n'
    '            "6. หากไม่พบข้อมูลในคลังความรู้ ให้บอกว่า \'น้องพั้นซ์หาไม่เจอนะคะพี่ แต่เดี๋ยวน้องพั้นซ์จะพยายามหาทางอื่นช่วยนะคะ\'\\n"\n'
    '        )\n'
)
lines[4180:4191] = [persona_block]

# Vision block
vision_block = (
    '        system_prompt += (\n'
    '            "\\n\\n[Vision Mode Enabled]\\n"\n'
    '            "ผู้ใช้งานส่งรูปภาพมาให้คุณวิเคราะห์ ตรวจสอบและอธิบายสิ่งที่เห็นในรูปตามความเหมาะสม "\n'
    '            "หากเป็นเอกสารหรือบิล ให้สรุปข้อมูลสำคัญ ตัวเลข หรือรายการออกมาให้ชัดเจนที่สุด "\n'
    '            "หากมีสิ่งของหรือสถานที่ ให้ระบุลักษณะเด่นของสิ่งนั้นๆ นะคะ\\n"\n'
    '        )\n'
)
lines[4193:4199] = [vision_block]

replace_line(4202, '    system_prompt += "=== วันสำคัญและกิจกรรมองค์กร ===\\n"')
replace_line(4204, '        system_prompt += f"- {date}: {name} (วันสำคัญ/วันหยุดนักขัตฤกษ์)\\n"')
replace_line(4208, '    system_prompt += "=== สิ้นสุดข้อมูลปฏิทิน ===\\n\\n"')

# Context block
context_block = (
    '    if context:\n'
    '        system_prompt += (\n'
    '            "=== ข้อมูลอ้างอิงจากเอกสารองค์กร ===\\n"\n'
    '            + context\n'
    '            + "\\n=== สิ้นสุดข้อมูลอ้างอิง ===\\n"\n'
    '        )\n'
    '    else:\n'
    '        system_prompt += "\\n(ขณะนี้ยังไม่มีเอกสารอ้างอิงที่เกี่ยวข้องกับข้อนี้)\\n"\n'
)
lines[4210:4218] = [context_block]

# Persona filter in generator
replace_line(4247, '                    chunk = chunk.replace("ครับ/ค่ะ", "ค่ะ").replace("ครับ", "ค่ะ")')
replace_line(4261, '            bot_full_text = re.sub(r\'ครับ\\s*/\\s*ค่ะ\', \'ค่ะ\', bot_full_text)')
replace_line(4262, '            bot_full_text = bot_full_text.replace("ครับ", "ค่ะ")')

# Error msg
replace_line(4287, '                error_msg = "ขออภัยนะคะ ขณะนี้ระบบ AI มีการใช้งานหนาแน่นหรือติดปัญหาชั่วคราว กรุณารอสักครู่ (ประมาณ 1 นาที) หรือติดต่อผู้ดูแลระบบนะคะ"')

# Phase 2: Tasks & Leave
replace_line(4413, '        "วิเคราะห์ข้อความด้านล่าง และสกัด \'Action Items\' หรือ \'งานที่ต้องทำ\' ออกมา "')
replace_line(4414, '        "หากพบงาน ให้สรุปเป็น JSON array ของวัตถุที่มีฟิลด์ \'title\' และ \'description\' (ภาษาไทย) "')
replace_line(4415, '        "หากไม่พบงาน ให้ส่งเป็น array ว่าง [] "')
replace_line(4416, '        "ตอบเฉพาะ JSON เท่านั้น:\\n\\n"')
replace_line(4417, '        f"ข้อความ: {chat_text}"')
replace_line(4423, '        for chunk in provider.chat_stream(prompt, [], "คุณคือผู้ช่วยสกัดงานจากประโยคสนทนา"):')

replace_line(4486, '        return jsonify({"ok": False, "error": "กรุณากรอกวันที่ให้ครบถ้วน"}), 400')
replace_line(4497, '                "คำขอลาใหม่", ')
replace_line(4498, '                f"คุณ {user} ได้ส่งคำขอลา {l_type} ตั้งแต่วันที่ {s_date} ถึง {e_date}", ')
replace_line(4501, '            # send_push_notification(admin, "คำขอลาใหม่", f"คุณ {user} ได้ส่งคำขอลา {l_type}", "/#admin")')
replace_line(4503, '    return jsonify({"ok": False, "error": "เกิดข้อผิดพลาดในการส่งคำขอ"}), 500')

replace_line(4528, '        return jsonify({"ok": False, "error": "ข้อมูลไม่ถูกต้อง"}), 400')
replace_line(4537, '                f"คำขอลาของคุณได้รับการ{ \'อนุมัติ\' if status == \'approved\' else \'ปฏิเสธ\' }",')
replace_line(4538, '                f"คำขอลาวันที่ {leave[\'start_date\']} ถึง {leave[\'end_date\']} ได้รับการ{ \'อนุมัติ\' if status == \'approved\' else \'ปฏิเสธ\' } โดย {admin_user}",')
replace_line(4542, '    return jsonify({"ok": False, "error": "ไม่พบคำขอลาที่ระบุ"}), 404')

replace_line(4553, '        return jsonify({"ok": False, "error": "ข้อมูลไม่ครบถ้วน"}), 400')
replace_line(4561, '        msg = f"มีข้อความใหม่ในคำขอลา: {comment[:50]}..."')
replace_line(4566, '                notification_db.add_notification(admin, "leave_comment", "ข้อความใหม่จากพนักงาน", msg, "/#admin")')
replace_line(4569, '            notification_db.add_notification(leave["username"], "leave_comment", "ข้อความใหม่จากผู้ดูแล", msg, "/#leave")')

replace_line(4583, '    return jsonify(database.get_random_lunch() or {"name": "ยังไม่มีรายชื่ออาหารในระบบ"})')

# User Management & Settings
replace_line(4697, '        return jsonify({"ok": False, "error": "ไม่สามารถปิดบัญชี Admin ได้"}), 400')
replace_line(4702, '    status_th = "เปิด" if new_active else "ปิด"')
replace_line(4703, '    database.log_event(f"Admin {status_th}การใช้งาน user: {username}", user=admin_user)')
replace_line(4721, '        database.log_event("อัปเดตการตั้งค่าระบบต้นทาง", user=session.get("user"))')
replace_line(4723, '    return jsonify({"ok": False, "error": "ไม่สามารถอัปเดตการตั้งค่าได้"}), 500')

# Phase 3: Quotation & Briefing
replace_line(4737, '        tab_name = \'ใบเสนอราคา (สร้างโดยระบบ)\'')
replace_line(4744, '            # จัดหัวตารางให้สอดคล้องกันและสวยงาม')
replace_line(4745, '            headers = [["วันที่ทำรายการ", "เลขที่ใบเสนอราคา", "ชื่อลูกค้า/บริษัท", "ข้อมูลติดต่อ", "ยอดรวมก่อนลด", "ส่วนลด", "ยอดสุทธิ (VAT 7%)", "ผู้จัดทำเอกสาร", "ลิงก์ไฟล์ PDF"]]')
replace_line(4751, '            # เพิ่มความสวยงามให้หัวตาราง (สีน้ำเงินเข้ม ตัวขาว หนา)')

replace_line(4798, '            return jsonify({"ok": False, "error": "ข้อมูลไม่ครบถ้วน"}), 400')
replace_line(4814, '        database.log_event(f"สร้างใบเสนอราคา: {quotation_data.get(\'quotation_no\')}", user=user)')

# Briefing (Lines 5389-5402, 5411)
replace_line(5389, '        context = "กิจกรรมของบริษัทใน 24 ชม. ที่ผ่านมา:\\n"')
replace_line(5391, '            context += "📢 ข่าวสารใหม่:\\n" + "\\n".join([f"- {p[\'title\']}" for p in activities["posts"][:3]]) + "\\n"')
replace_line(5393, '            context += "📅 ตารางงานวันนี้:\\n" + "\\n".join([f"- {s[\'time\']} {s[\'title\']}" for s in activities["schedules"][:3]]) + "\\n"')
replace_line(5395, '            context += "📂 เอกสารอัปโหลดใหม่:\\n" + "\\n".join([f"- {f[\'filename\']} ({f[\'category\']})" for f in recent_files[:5]]) + "\\n"')

brief_prompt = (
    '        prompt = (\n'
    '            "คุณคือ \'น้องพั้นซ์\' (Punch) AI Assistant สาวออฟฟิศสุดร่าเริง สรุป Morning Brief "\n'
    '            "ข้อมูลสำคัญประจำเช้านี้ ในสไตล์ที่ดูเป็นกันเองและน่ารัก "\n'
    '            "ใช้ภาษาที่สุภาพแต่เป็นกันเอง ยิ้มแย้มแจ่มใส และสรุปสาระสำคัญที่เกิดขึ้นให้เพื่อนร่วมงานทราบค่ะ\\n\\n"\n'
    '            f"{context}\\n\\n"\n'
    '            "สรุปสไตล์น้องพั้นซ์:"\n'
    '        )\n'
)
lines[5397:5403] = [brief_prompt]
replace_line(5411, '            broadcast_line_announcement("🌟📢 Morning Brief จากน้องพั้นซ์", summary)')

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Sanitization complete.")
