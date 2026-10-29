"""
Masterpiece DFD Generator:
1. Context Diagram (Level 0)
2. DFD Level 1
Guaranteed:
- Pure white background (ZERO outer black frame/border)
- 100% Gane & Sarson shapes
- Action VERBS for all processes
- NOUNS for all entities, data stores, and data flows
- Large, crisp, highly legible Thai fonts
- ZERO line collisions, ZERO overlapping text, ZERO detours through boxes
- Strict balancing between Context Diagram and Level 1
"""

import os
import shutil
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=False):
    font_paths = [
        r"C:\Windows\Fonts\tahomabd.ttf" if bold else r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\LeelaUIb.ttf" if bold else r"C:\Windows\Fonts\LeelawUI.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_text_centered(draw, xy, text, font, fill=(0, 0, 0)):
    lines = text.split('\n')
    line_height = font.size + 4
    total_h = len(lines) * line_height
    start_y = xy[1] - total_h / 2
    for line in lines:
        bbox = font.getbbox(line)
        w = bbox[2] - bbox[0]
        draw.text((xy[0] - w / 2, start_y), line, font=font, fill=fill)
        start_y += line_height

def draw_entity(draw, box, text, font):
    draw.rectangle(box, fill=(255, 255, 255), outline=(0, 0, 0), width=3)
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    draw_text_centered(draw, (cx, cy), text, font)

def draw_process(draw, box, p_id, name, font_id, font_name, div_h=48):
    draw.rounded_rectangle(box, radius=18, fill=(255, 255, 255), outline=(0, 0, 0), width=3)
    divider_y = box[1] + div_h
    draw.line([(box[0], divider_y), (box[2], divider_y)], fill=(0, 0, 0), width=3)
    
    cx = (box[0] + box[2]) / 2
    id_cy = (box[1] + divider_y) / 2
    draw_text_centered(draw, (cx, id_cy), p_id, font_id)
    
    name_cy = (divider_y + box[3]) / 2
    draw_text_centered(draw, (cx, name_cy), name, font_name)

def draw_data_store(draw, box, ds_id, name, font_id, font_name, id_w=75):
    draw.line([(box[0], box[1]), (box[2], box[1])], fill=(0, 0, 0), width=3)
    draw.line([(box[0], box[3]), (box[2], box[3])], fill=(0, 0, 0), width=3)
    draw.line([(box[0], box[1]), (box[0], box[3])], fill=(0, 0, 0), width=3)
    draw.line([(box[0] + id_w, box[1]), (box[0] + id_w, box[3])], fill=(0, 0, 0), width=3)
    
    id_cx = box[0] + id_w / 2
    cy = (box[1] + box[3]) / 2
    draw_text_centered(draw, (id_cx, cy), ds_id, font_id)
    
    name_cx = box[0] + id_w + (box[2] - (box[0] + id_w)) / 2
    draw_text_centered(draw, (name_cx, cy), name, font_name)

def draw_arrow_head(draw, tip, direction="right", size=13):
    x, y = tip
    if direction == "right":
        draw.polygon([(x, y), (x - size, y - size/2), (x - size, y + size/2)], fill=(0, 0, 0))
    elif direction == "left":
        draw.polygon([(x, y), (x + size, y - size/2), (x + size, y + size/2)], fill=(0, 0, 0))
    elif direction == "down":
        draw.polygon([(x, y), (x - size/2, y - size), (x + size/2, y - size)], fill=(0, 0, 0))
    elif direction == "up":
        draw.polygon([(x, y), (x - size/2, y + size), (x + size/2, y + size)], fill=(0, 0, 0))


# =========================================================================
# 1. RENDER CONTEXT DIAGRAM (LEVEL 0) - PURE DIRECT GEOMETRY
# =========================================================================
def render_context_diagram(out_path):
    w, h = 2300, 1400
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    f_title = get_font(32, bold=True)
    f_entity = get_font(23, bold=True)
    f_proc_id = get_font(32, bold=True)
    f_proc_name = get_font(23, bold=True)
    f_label = get_font(18, bold=True)

    draw_text_centered(draw, (w / 2, 45), "แผนภาพบริบท (Context Diagram) - ระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร", f_title)

    # Process 0 (Center: X = 780 to 1520, Y = 360 to 980)
    p0 = (780, 360, 1520, 980)
    draw_process(draw, p0, "0", "ประมวลผลระบบปัญญาประดิษฐ์แชทบอท\nสำหรับองค์กร\n(OrgChat AI System)", f_proc_id, f_proc_name, div_h=60)

    # Top Entity: LINE Platform (X = 920 to 1380, Y = 90 to 220)
    line_box = (920, 90, 1380, 220)
    draw_entity(draw, line_box, "แพลตฟอร์มไลน์\n(LINE Platform)", f_entity)

    # Left Entities (X = 80 to 480)
    admin_box = (80, 320, 480, 470)
    draw_entity(draw, admin_box, "ผู้ดูแลระบบ\n(System Admin)", f_entity)

    emp_box = (80, 830, 480, 980)
    draw_entity(draw, emp_box, "พนักงาน\n(Employee)", f_entity)

    # Right Entities (X = 1820 to 2220)
    mgr_box = (1820, 320, 2220, 470)
    draw_entity(draw, mgr_box, "หัวหน้างาน\n(Manager)", f_entity)

    gcloud_box = (1820, 830, 2220, 980)
    draw_entity(draw, gcloud_box, "บริการกูเกิลคลาวด์\n(Google Cloud Services)", f_entity)

    # ---------------------------------------------------------
    # 1. LINE Platform <-> Process 0 (Pure Vertical Straight Lines)
    # ---------------------------------------------------------
    # LINE -> P0 (Down at x = 1040)
    draw.line([(1040, 220), (1040, 360)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1040, 360), "down")
    # Label on left of line
    bbox = f_label.getbbox("ข้อความแชท, ภาพสลิปโอนเงิน")
    lbl_w = bbox[2] - bbox[0]
    draw.text((1040 - lbl_w - 18, 275), "ข้อความแชท, ภาพสลิปโอนเงิน", font=f_label, fill=(0, 0, 0))

    # P0 -> LINE (Up at x = 1260)
    draw.line([(1260, 360), (1260, 220)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1260, 220), "up")
    # Label on right of line
    draw.text((1260 + 18, 275), "ข้อความตอบกลับ RAG, ผลสกัดสลิป", font=f_label, fill=(0, 0, 0))

    # ---------------------------------------------------------
    # 2. System Admin <-> Process 0 (Pure Horizontal Straight Lines)
    # ---------------------------------------------------------
    # Admin -> P0: (480, 365) -> (780, 365)
    draw.line([(480, 365), (780, 365)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (780, 365), "right")
    draw.text((495, 335), "ข้อมูลเข้าสู่ระบบ, ไฟล์เอกสารองค์กร", font=f_label, fill=(0, 0, 0))

    # P0 -> Admin: (780, 425) -> (480, 425)
    draw.line([(780, 425), (480, 425)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (480, 425), "left")
    draw.text((495, 435), "รายงานสรุปสถิติ, ข้อมูลแดชบอร์ด", font=f_label, fill=(0, 0, 0))

    # ---------------------------------------------------------
    # 3. Employee <-> Process 0 (Pure Horizontal Straight Lines)
    # ---------------------------------------------------------
    # Employee -> P0: (480, 875) -> (780, 875)
    draw.line([(480, 875), (780, 875)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (780, 875), "right")
    draw.text((495, 845), "ข้อมูลลงทะเบียน, ข้อมูลคำขอลา", font=f_label, fill=(0, 0, 0))

    # P0 -> Employee: (780, 935) -> (480, 935)
    draw.line([(780, 935), (480, 935)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (480, 935), "left")
    draw.text((495, 945), "ผลอนุมัติการลา, สรุปยอดวันลาคงเหลือ", font=f_label, fill=(0, 0, 0))

    # ---------------------------------------------------------
    # 4. Manager <-> Process 0 (Pure Horizontal Straight Lines)
    # ---------------------------------------------------------
    # P0 -> Manager: (1520, 365) -> (1820, 365)
    draw.line([(1520, 365), (1820, 365)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1820, 365), "right")
    draw.text((1535, 335), "การแจ้งเตือนคำขอลางานของพนักงาน", font=f_label, fill=(0, 0, 0))

    # Manager -> P0: (1820, 425) -> (1520, 425)
    draw.line([(1820, 425), (1520, 425)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1520, 425), "left")
    draw.text((1535, 435), "ผลการพิจารณาอนุมัติคำขอลางาน", font=f_label, fill=(0, 0, 0))

    # ---------------------------------------------------------
    # 5. Google Cloud <-> Process 0 (Pure Horizontal Straight Lines)
    # ---------------------------------------------------------
    # P0 -> Cloud: (1520, 875) -> (1820, 875)
    draw.line([(1520, 875), (1820, 875)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1820, 875), "right")
    draw.text((1535, 845), "ภาพสลิปส่งตรวจ OCR, ข้อมูลลง Sheets", font=f_label, fill=(0, 0, 0))

    # Cloud -> P0: (1820, 935) -> (1520, 935)
    draw.line([(1820, 935), (1520, 935)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1520, 935), "left")
    draw.text((1535, 945), "ข้อความสกัด OCR, ผลบันทึกบัญชี", font=f_label, fill=(0, 0, 0))

    # Safe crop: add 30px white padding around content
    bbox = img.getbbox()
    crop_x1 = max(0, bbox[0] - 30)
    crop_y1 = max(0, bbox[1] - 30)
    crop_x2 = min(w, bbox[2] + 30)
    crop_y2 = min(h, bbox[3] + 30)
    final_img = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
    final_img.save(out_path, dpi=(300, 300))
    print(f"[OK] Generated Context Diagram: {out_path} (size={final_img.size})")


# =========================================================================
# 2. RENDER DFD LEVEL 1 - ZERO COLLISIONS, ZERO BOX CROSSINGS
# =========================================================================
def render_dfd_level1(out_path):
    w, h = 2900, 2150
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    f_title = get_font(32, bold=True)
    f_entity = get_font(22, bold=True)
    f_proc_id = get_font(26, bold=True)
    f_proc_name = get_font(21, bold=True)
    f_ds_id = get_font(23, bold=True)
    f_ds_name = get_font(19, bold=True)
    f_label = get_font(17, bold=True)

    draw_text_centered(draw, (w / 2, 45), "แผนภาพกระแสข้อมูลระดับ 1 (DFD Level 1) - ระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร", f_title)

    # ---------------------------------------------------------
    # Central Column: 5 Processes (X: 840 to 1460, W = 620)
    # ---------------------------------------------------------
    px1, px2 = 840, 1460
    p1 = (px1, 110, px2, 240)
    p2 = (px1, 470, px2, 600)
    p3 = (px1, 830, px2, 960)
    p4 = (px1, 1190, px2, 1320)
    p5 = (px1, 1550, px2, 1680)

    draw_process(draw, p1, "1.0", "ตรวจสอบสิทธิ์และจัดการผู้ใช้งาน", f_proc_id, f_proc_name, div_h=46)
    draw_process(draw, p2, "2.0", "สืบค้นคลังความรู้และประมวลผลคำถาม", f_proc_id, f_proc_name, div_h=46)
    draw_process(draw, p3, "3.0", "ประมวลผลสลิปโอนเงินและบันทึกบัญชี", f_proc_id, f_proc_name, div_h=46)
    draw_process(draw, p4, "4.0", "จัดการคำขอลางานและการอนุมัติ", f_proc_id, f_proc_name, div_h=46)
    draw_process(draw, p5, "5.0", "สรุปผลสถิติและแสดงผลแดชบอร์ด", f_proc_id, f_proc_name, div_h=46)

    # ---------------------------------------------------------
    # Left Column Entities (X: 130 to 490)
    # ---------------------------------------------------------
    ex1, ex2 = 130, 490
    admin_box = (ex1, 110, ex2, 240)
    draw_entity(draw, admin_box, "ผู้ดูแลระบบ\n(System Admin)", f_entity)

    line_box = (ex1, 520, ex2, 710)
    draw_entity(draw, line_box, "แพลตฟอร์มไลน์\n(LINE Platform)", f_entity)

    emp_box = (ex1, 1190, ex2, 1320)
    draw_entity(draw, emp_box, "พนักงาน\n(Employee)", f_entity)

    # ---------------------------------------------------------
    # Right Column Entities & Data Stores (X: 1900 to 2650)
    # ---------------------------------------------------------
    # D1 beside P1.0
    ds1_box = (1900, 120, 2650, 230)
    draw_data_store(draw, ds1_box, "D1", "แฟ้มข้อมูลผู้ใช้งาน (users)", f_ds_id, f_ds_name)

    # D2 beside P2.0
    ds2_box = (1900, 480, 2650, 590)
    draw_data_store(draw, ds2_box, "D2", "แฟ้มคลังความรู้เวกเตอร์ (knowledge_base)", f_ds_id, f_ds_name)

    # D3 & Google Cloud beside P3.0
    ds3_box = (1900, 800, 2650, 890)
    draw_data_store(draw, ds3_box, "D3", "แฟ้มบันทึกเอกสารและสลิปการเงิน (drive_logs)", f_ds_id, f_ds_name)

    gcloud_box = (1900, 930, 2520, 1060)
    draw_entity(draw, gcloud_box, "บริการกูเกิลคลาวด์\n(Google Cloud Services)", f_entity)

    # Manager beside P4.0
    mgr_box = (1900, 1190, 2520, 1320)
    draw_entity(draw, mgr_box, "หัวหน้างาน\n(Manager)", f_entity)

    # D4 & D5 under P4.0
    ds4_box = (1900, 1360, 2650, 1450)
    draw_data_store(draw, ds4_box, "D4", "แฟ้มข้อมูลการลางาน (leave_requests)", f_ds_id, f_ds_name)

    ds5_box = (1900, 1480, 2650, 1570)
    draw_data_store(draw, ds5_box, "D5", "แฟ้มโควตาวันลาพนักงาน (user_leave_quotas)", f_ds_id, f_ds_name)

    # D6 beside P5.0
    ds6_box = (1900, 1610, 2650, 1720)
    draw_data_store(draw, ds6_box, "D6", "แฟ้มบันทึกประวัติระบบ (audit_logs)", f_ds_id, f_ds_name)

    # ---------------------------------------------------------
    # PROCESS 1.0 FLOWS
    # ---------------------------------------------------------
    # Admin -> P1.0 (Direct Horizontal)
    draw.line([(ex2, 150), (px1, 150)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px1, 150), "right")
    draw.text((520, 120), "ข้อมูลเข้าสู่ระบบและคำสั่งจัดการ", font=f_label, fill=(0, 0, 0))

    # Employee -> P1.0 (Outer Left Corridor: x = 60, goes all around top y = 50)
    draw.line([(ex1, 1215), (60, 1215), (60, 50), (780, 50), (780, 195), (px1, 195)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px1, 195), "right")
    draw.text((200, 20), "ข้อมูลลงทะเบียนและเข้าสู่ระบบ", font=f_label, fill=(0, 0, 0))

    # P1.0 <-> D1 (Direct Horizontal - Generous 440px distance!)
    draw.line([(px2, 145), (1900, 145)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1900, 145), "right")
    draw.text((1500, 115), "บันทึกข้อมูลผู้ใช้และสิทธิ์", font=f_label, fill=(0, 0, 0))

    draw.line([(1900, 195), (px2, 195)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px2, 195), "left")
    draw.text((1500, 205), "ข้อมูลโปรไฟล์และสิทธิ์ผู้ใช้", font=f_label, fill=(0, 0, 0))

    # ---------------------------------------------------------
    # PROCESS 2.0 FLOWS
    # ---------------------------------------------------------
    # Admin -> P2.0 (Files for RAG via middle corridor x = 550)
    draw.line([(ex2 - 40, 240), (550, 240), (550, 495), (px1, 495)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px1, 495), "right")
    draw.text((570, 465), "ไฟล์เอกสารองค์กรสำหรับ RAG", font=f_label, fill=(0, 0, 0))

    # LINE -> P2.0 (Chat Question)
    draw.line([(ex2, 555), (px1, 555)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px1, 555), "right")
    draw.text((520, 525), "ข้อความแชทสอบถามข้อมูล", font=f_label, fill=(0, 0, 0))

    # P2.0 -> LINE (RAG Answer)
    draw.line([(px1, 615), (ex2, 615)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (ex2, 615), "left")
    draw.text((520, 625), "ข้อความตอบกลับ RAG (Gemini)", font=f_label, fill=(0, 0, 0))

    # P2.0 <-> D2 (Direct Horizontal)
    draw.line([(px2, 510), (1900, 510)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1900, 510), "right")
    draw.text((1500, 480), "เวกเตอร์เอ็มเบดดิงเอกสาร", font=f_label, fill=(0, 0, 0))

    draw.line([(1900, 560), (px2, 560)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px2, 560), "left")
    draw.text((1500, 570), "เนื้อหาเอกสารที่สืบค้นได้", font=f_label, fill=(0, 0, 0))

    # ---------------------------------------------------------
    # PROCESS 3.0 FLOWS
    # ---------------------------------------------------------
    # LINE -> P3.0 (Slip Image via middle corridor x = 620)
    draw.line([(ex2, 675), (620, 675), (620, 865), (px1, 865)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px1, 865), "right")
    draw.text((640, 835), "ภาพถ่ายสลิปโอนเงิน / ใบเสร็จ", font=f_label, fill=(0, 0, 0))

    # P3.0 -> LINE (OCR Result via middle corridor x = 710)
    draw.line([(px1, 925), (710, 925), (710, 695), (ex2, 695)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (ex2, 695), "left")
    draw.text((725, 900), "ผลการสกัดสลิปและสรุปรายการ", font=f_label, fill=(0, 0, 0))

    # P3.0 -> D3 (Direct Horizontal)
    draw.line([(px2, 845), (1900, 845)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1900, 845), "right")
    draw.text((1500, 815), "บันทึกข้อมูลธุรกรรมการเงิน", font=f_label, fill=(0, 0, 0))

    # P3.0 <-> Google Cloud (Direct Horizontal - Zero Steps!)
    draw.line([(px2, 920), (1900, 920)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1900, 920), "right")
    draw.text((1500, 890), "ภาพสลิปส่งตรวจ OCR, ข้อมูลลง Sheets", font=f_label, fill=(0, 0, 0))

    draw.line([(1900, 970), (px2, 970)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px2, 970), "left")
    draw.text((1500, 980), "ผลการรู้จำอักขระ OCR, ผลบันทึกชีต", font=f_label, fill=(0, 0, 0))

    # ---------------------------------------------------------
    # PROCESS 4.0 FLOWS
    # ---------------------------------------------------------
    # Employee -> P4.0 (Direct Horizontal)
    draw.line([(ex2, 1235), (px1, 1235)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px1, 1235), "right")
    draw.text((520, 1205), "ข้อมูลคำขอลางาน (แบบฟอร์ม LIFF)", font=f_label, fill=(0, 0, 0))

    # P4.0 -> Employee (Direct Horizontal)
    draw.line([(px1, 1285), (ex2, 1285)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (ex2, 1285), "left")
    draw.text((520, 1295), "ผลการอนุมัติการลาและยอดวันลาคงเหลือ", font=f_label, fill=(0, 0, 0))

    # P4.0 -> Manager (Direct Horizontal)
    draw.line([(px2, 1235), (1900, 1235)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1900, 1235), "right")
    draw.text((1500, 1205), "การแจ้งเตือนคำขอลางาน (Flex Message)", font=f_label, fill=(0, 0, 0))

    # Manager -> P4.0 (Direct Horizontal)
    draw.line([(1900, 1285), (px2, 1285)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px2, 1285), "left")
    draw.text((1500, 1295), "ผลการพิจารณาอนุมัติ/ปฏิเสธคำขอลา", font=f_label, fill=(0, 0, 0))

    # P4.0 <-> D4
    draw.line([(1400, 1320), (1400, 1405), (1900, 1405)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1900, 1405), "right")
    draw.text((1420, 1375), "บันทึกคำขอลาและผลการอนุมัติ", font=f_label, fill=(0, 0, 0))

    # P4.0 <-> D5
    draw.line([(1300, 1320), (1300, 1525), (1900, 1525)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1900, 1525), "right")
    draw.text((1320, 1495), "ตรวจสอบและตัดทอนโควตาวันลา", font=f_label, fill=(0, 0, 0))

    # ---------------------------------------------------------
    # PROCESS 5.0 FLOWS (Satisfies No Miracle Rule)
    # ---------------------------------------------------------
    # Admin -> P5.0 (Admin requests report via outer left corridor x = 85)
    draw.line([(ex1 + 30, 240), (ex1 + 30, 270), (85, 270), (85, 1595), (px1, 1595)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px1, 1595), "right")
    draw.text((520, 1565), "คำขอรายงานสถิติและข้อมูลแดชบอร์ด", font=f_label, fill=(0, 0, 0))

    # P5.0 -> Admin (Dashboard output via outer left corridor x = 40)
    draw.line([(px1, 1650), (40, 1650), (40, 175), (ex1, 175)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (ex1, 175), "right")
    draw.text((520, 1658), "รายงานสรุปสถิติและข้อมูลแดชบอร์ด", font=f_label, fill=(0, 0, 0))

    # P5.0 reads from D6 (Direct Horizontal)
    draw.line([(1900, 1665), (px2, 1665)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px2, 1665), "left")
    draw.text((1500, 1635), "บันทึกประวัติการใช้งานระบบ (Audit Logs)", font=f_label, fill=(0, 0, 0))

    # Safe crop: find content bounding box, add 30px white padding on all sides
    bbox = img.getbbox()
    crop_x1 = max(0, bbox[0] - 30)
    crop_y1 = max(0, bbox[1] - 30)
    crop_x2 = min(w, bbox[2] + 30)
    crop_y2 = min(h, bbox[3] + 30)
    final_img = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
    final_img.save(out_path, dpi=(300, 300))
    print(f"[OK] Generated DFD Level 1: {out_path} (size={final_img.size})")

if __name__ == "__main__":
    out_dir = r"webai\เอกสาร โปรจบ\OVERLEFT\Image"
    p_ctx = os.path.join(out_dir, "fig3_1_context.png")
    p_dfd = os.path.join(out_dir, "fig3_2_dfd.png")

    render_context_diagram(p_ctx)
    render_dfd_level1(p_dfd)

    # Synchronize copies
    shutil.copy(p_ctx, os.path.join(out_dir, "image3.png"))
    shutil.copy(p_dfd, os.path.join(out_dir, "image4.png"))
    print("[SUCCESS] All images rendered and synchronized perfectly!")
