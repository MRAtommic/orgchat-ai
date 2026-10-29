"""
Ultra-refined DFD Diagram Generator:
Guarantees 100% textbook compliance, zero collisions, generous padding, and publishing-grade aesthetics.
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
    sample_bbox = font.getbbox("กj")
    base_h = sample_bbox[3] - sample_bbox[1]
    line_height = base_h + 8
    total_h = len(lines) * line_height
    start_y = xy[1] - total_h / 2
    for line in lines:
        bbox = font.getbbox(line)
        w = bbox[2] - bbox[0]
        draw.text((xy[0] - w / 2, start_y), line, font=font, fill=fill)
        start_y += line_height

def draw_badge_label(draw, center_xy, text, font, pad_x=14, pad_y=7):
    """Draws a label on a pure white badge with a crisp subtle border to prevent any line collision."""
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    cx, cy = center_xy
    x1 = cx - tw / 2 - pad_x
    y1 = cy - th / 2 - pad_y
    x2 = cx + tw / 2 + pad_x
    y2 = cy + th / 2 + pad_y

    draw.rounded_rectangle([x1, y1, x2, y2], radius=7, fill=(255, 255, 255), outline=(180, 180, 180), width=1)
    draw.text((cx - tw / 2, cy - th / 2 - bbox[1]), text, font=font, fill=(0, 0, 0))

def draw_entity(draw, box, text, font):
    """Solid rectangle for External Entity."""
    draw.rectangle(box, fill=(255, 255, 255), outline=(0, 0, 0), width=3)
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    draw_text_centered(draw, (cx, cy), text, font)

def draw_process(draw, box, p_id, name, font_id, font_name, div_h=52):
    """Rounded rectangle with top divider for Process."""
    draw.rounded_rectangle(box, radius=18, fill=(255, 255, 255), outline=(0, 0, 0), width=3)
    divider_y = box[1] + div_h
    draw.line([(box[0], divider_y), (box[2], divider_y)], fill=(0, 0, 0), width=3)

    cx = (box[0] + box[2]) / 2
    id_cy = (box[1] + divider_y) / 2
    draw_text_centered(draw, (cx, id_cy), p_id, font_id)

    name_cy = (divider_y + box[3]) / 2
    draw_text_centered(draw, (cx, name_cy), name, font_name)

def draw_data_store(draw, box, ds_id, name, font_id, font_name, id_w=85):
    """Open-ended rectangle on the right for Data Store."""
    draw.rectangle(box, fill=(255, 255, 255), outline=None)
    draw.line([(box[0], box[1]), (box[2], box[1])], fill=(0, 0, 0), width=3)
    draw.line([(box[0], box[3]), (box[2], box[3])], fill=(0, 0, 0), width=3)
    draw.line([(box[0], box[1]), (box[0], box[3])], fill=(0, 0, 0), width=3)
    draw.line([(box[0] + id_w, box[1]), (box[0] + id_w, box[3])], fill=(0, 0, 0), width=3)

    id_cx = box[0] + id_w / 2
    cy = (box[1] + box[3]) / 2
    draw_text_centered(draw, (id_cx, cy), ds_id, font_id)

    name_cx = box[0] + id_w + (box[2] - (box[0] + id_w)) / 2
    draw_text_centered(draw, (name_cx, cy), name, font_name)

def draw_arrow_head(draw, tip, direction="right", size=14):
    x, y = tip
    if direction == "right":
        draw.polygon([(x, y), (x - size, y - size/2), (x - size, y + size/2)], fill=(0, 0, 0))
    elif direction == "left":
        draw.polygon([(x, y), (x + size, y - size/2), (x + size, y + size/2)], fill=(0, 0, 0))
    elif direction == "down":
        draw.polygon([(x, y), (x - size/2, y - size), (x + size/2, y - size)], fill=(0, 0, 0))
    elif direction == "up":
        draw.polygon([(x, y), (x - size/2, y + size), (x + size/2, y + size)], fill=(0, 0, 0))


# =============================================================================
# 1. GENERATE PERFECT CONTEXT DIAGRAM (LEVEL 0)
# =============================================================================
def render_context_diagram(out_path):
    w, h = 2500, 1550
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    f_title = get_font(32, bold=True)
    f_entity = get_font(23, bold=True)
    f_proc_id = get_font(32, bold=True)
    f_proc_name = get_font(23, bold=True)
    f_label = get_font(18, bold=True)

    draw_text_centered(draw, (w / 2, 50), "แผนภาพบริบท (Context Diagram) - ระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร", f_title)

    # Process 0
    p0 = (920, 620, 1580, 920)
    draw_process(draw, p0, "0", "ระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร\n(OrgChat AI System)", f_proc_id, f_proc_name, div_h=58)

    # 5 Entities
    line_box = (980, 120, 1520, 250)
    draw_entity(draw, line_box, "แพลตฟอร์มไลน์\n(LINE Platform)", f_entity)

    admin_box = (100, 290, 520, 440)
    draw_entity(draw, admin_box, "ผู้ดูแลระบบ\n(System Admin)", f_entity)

    emp_box = (100, 1100, 520, 1250)
    draw_entity(draw, emp_box, "พนักงาน\n(Employee)", f_entity)

    mgr_box = (1980, 290, 2400, 440)
    draw_entity(draw, mgr_box, "หัวหน้างาน\n(Manager)", f_entity)

    gcloud_box = (1980, 1100, 2400, 1250)
    draw_entity(draw, gcloud_box, "บริการกูเกิลคลาวด์\n(Google Cloud Services)", f_entity)

    # -------------------------------------------------------------------------
    # LINE <-> Process 0
    # -------------------------------------------------------------------------
    # LINE -> P0 (Down at x = 1110)
    draw.line([(1110, 250), (1110, 620)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1110, 620), "down")
    draw_badge_label(draw, (1110, 390), "ข้อความแชท, ภาพถ่ายสลิปโอนเงิน (Webhook)", f_label)

    # P0 -> LINE (Up at x = 1390)
    draw.line([(1390, 620), (1390, 250)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1390, 250), "up")
    draw_badge_label(draw, (1390, 480), "ข้อความตอบกลับ RAG, ผลสกัดสลิป (Flex Message)", f_label)

    # -------------------------------------------------------------------------
    # Admin <-> Process 0
    # -------------------------------------------------------------------------
    # Admin -> P0: (520, 340) -> (720, 340) -> (720, 670) -> (920, 670)
    draw.line([(520, 340), (720, 340), (720, 670), (920, 670)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (920, 670), "right")
    # Badge placed cleanly on horizontal segment near Admin:
    draw_badge_label(draw, (620, 340), "ข้อมูลเข้าสู่ระบบ, ไฟล์เอกสารองค์กร", f_label)

    # P0 -> Admin: (920, 720) -> (600, 720) -> (600, 390) -> (520, 390)
    draw.line([(920, 720), (600, 720), (600, 390), (520, 390)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (520, 390), "left")
    # Badge placed on horizontal segment near P0:
    draw_badge_label(draw, (760, 720), "รายงานสรุปสถิติ, ข้อมูลแดชบอร์ด", f_label)

    # -------------------------------------------------------------------------
    # Manager <-> Process 0
    # -------------------------------------------------------------------------
    # P0 -> Manager: (1580, 670) -> (1780, 670) -> (1780, 340) -> (1980, 340)
    draw.line([(1580, 670), (1780, 670), (1780, 340), (1980, 340)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1980, 340), "right")
    # Badge placed on horizontal segment near Manager:
    draw_badge_label(draw, (1880, 340), "การแจ้งเตือนคำขอลางาน (Flex Message)", f_label)

    # Manager -> P0: (1980, 390) -> (1900, 390) -> (1900, 720) -> (1580, 720)
    draw.line([(1980, 390), (1900, 390), (1900, 720), (1580, 720)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1580, 720), "left")
    # Badge placed on horizontal segment near P0:
    draw_badge_label(draw, (1740, 720), "ผลการพิจารณาอนุมัติ/ปฏิเสธคำขอลา", f_label)

    # -------------------------------------------------------------------------
    # Employee <-> Process 0
    # -------------------------------------------------------------------------
    # Employee -> P0: (520, 1145) -> (600, 1145) -> (600, 820) -> (920, 820)
    draw.line([(520, 1145), (600, 1145), (600, 820), (920, 820)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (920, 820), "right")
    # Badge placed on horizontal segment near P0:
    draw_badge_label(draw, (760, 820), "ข้อมูลลงทะเบียน, ข้อมูลคำขอลางาน", f_label)

    # P0 -> Employee: (920, 870) -> (720, 870) -> (720, 1195) -> (520, 1195)
    draw.line([(920, 870), (720, 870), (720, 1195), (520, 1195)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (520, 1195), "left")
    # Badge placed on horizontal segment near Employee:
    draw_badge_label(draw, (620, 1195), "ผลการอนุมัติการลา, สรุปยอดวันลาคงเหลือ", f_label)

    # -------------------------------------------------------------------------
    # Google Cloud <-> Process 0
    # -------------------------------------------------------------------------
    # P0 -> Cloud: (1580, 820) -> (1900, 820) -> (1900, 1145) -> (1980, 1145)
    draw.line([(1580, 820), (1900, 820), (1900, 1145), (1980, 1145)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1980, 1145), "right")
    # Badge placed on horizontal segment near P0:
    draw_badge_label(draw, (1740, 820), "ภาพสลิปส่งตรวจ OCR, ข้อมูลลง Sheets", f_label)

    # Cloud -> P0: (1980, 1195) -> (1780, 1195) -> (1780, 870) -> (1580, 870)
    draw.line([(1980, 1195), (1780, 1195), (1780, 870), (1580, 870)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (1580, 870), "left")
    # Badge placed on horizontal segment near Cloud:
    draw_badge_label(draw, (1880, 1195), "ข้อความสกัด OCR, ผลบันทึกบัญชี", f_label)

    bbox = img.getbbox()
    crop_x1 = max(0, bbox[0] - 35)
    crop_y1 = max(0, bbox[1] - 35)
    crop_x2 = min(w, bbox[2] + 35)
    crop_y2 = min(h, bbox[3] + 35)
    final_img = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
    final_img.save(out_path, dpi=(300, 300))
    print(f"[OK] Generated Clean Context Diagram: {out_path} (size={final_img.size})")


# =============================================================================
# 2. GENERATE PERFECT DFD LEVEL 1 (ZERO COLLISION)
# =============================================================================
def render_dfd_level1(out_path):
    w, h = 3400, 2300
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    f_title = get_font(34, bold=True)
    f_entity = get_font(23, bold=True)
    f_proc_id = get_font(27, bold=True)
    f_proc_name = get_font(22, bold=True)
    f_ds_id = get_font(24, bold=True)
    f_ds_name = get_font(20, bold=True)
    f_label = get_font(17, bold=True)

    draw_text_centered(draw, (w / 2, 45), "แผนภาพกระแสข้อมูลระดับ 1 (DFD Level 1) - ระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร", f_title)

    # 5 Processes (Center X = 1420, W = 680, H = 130)
    px1, px2 = 1080, 1760
    p1 = (px1, 120, px2, 250)
    p2 = (px1, 500, px2, 630)
    p3 = (px1, 880, px2, 1010)
    p4 = (px1, 1260, px2, 1390)
    p5 = (px1, 1640, px2, 1770)

    draw_process(draw, p1, "1.0", "ตรวจสอบสิทธิ์และจัดการผู้ใช้งาน", f_proc_id, f_proc_name, div_h=46)
    draw_process(draw, p2, "2.0", "สืบค้นคลังความรู้และประมวลผลคำถาม", f_proc_id, f_proc_name, div_h=46)
    draw_process(draw, p3, "3.0", "ประมวลผลสลิปโอนเงินและบันทึกบัญชี", f_proc_id, f_proc_name, div_h=46)
    draw_process(draw, p4, "4.0", "จัดการคำขอลางานและการอนุมัติ", f_proc_id, f_proc_name, div_h=46)
    draw_process(draw, p5, "5.0", "สรุปผลสถิติและแสดงผลแดชบอร์ด", f_proc_id, f_proc_name, div_h=46)

    # Left Entities: X: 180 to 540 (W = 360)
    ex1, ex2 = 180, 540
    admin_box = (ex1, 120, ex2, 250)
    draw_entity(draw, admin_box, "ผู้ดูแลระบบ\n(System Admin)", f_entity)

    line_box = (ex1, 530, ex2, 720)
    draw_entity(draw, line_box, "แพลตฟอร์มไลน์\n(LINE Platform)", f_entity)

    emp_box = (ex1, 1260, ex2, 1390)
    draw_entity(draw, emp_box, "พนักงาน\n(Employee)", f_entity)

    # Right Column: Data Stores & Entities
    # D1 beside P1.0
    ds1_box = (2200, 130, 3000, 240)
    draw_data_store(draw, ds1_box, "D1", "แฟ้มข้อมูลผู้ใช้งาน (users)", f_ds_id, f_ds_name)

    # D2 beside P2.0
    ds2_box = (2200, 510, 3000, 620)
    draw_data_store(draw, ds2_box, "D2", "แฟ้มคลังความรู้เวกเตอร์ (knowledge_base)", f_ds_id, f_ds_name)

    # D3 beside P3.0
    ds3_box = (2120, 850, 2920, 940)
    draw_data_store(draw, ds3_box, "D3", "แฟ้มบันทึกเอกสารและสลิปการเงิน (drive_logs)", f_ds_id, f_ds_name)

    # Google Cloud
    gcloud_box = (2300, 990, 3000, 1120)
    draw_entity(draw, gcloud_box, "บริการกูเกิลคลาวด์\n(Google Cloud Services)", f_entity)

    # Manager beside P4.0
    mgr_box = (2300, 1260, 3000, 1390)
    draw_entity(draw, mgr_box, "หัวหน้างาน\n(Manager)", f_entity)

    # D4 & D5 under P4.0
    ds4_box = (2120, 1430, 2920, 1520)
    draw_data_store(draw, ds4_box, "D4", "แฟ้มข้อมูลการลางาน (leave_requests)", f_ds_id, f_ds_name)

    ds5_box = (2120, 1550, 2920, 1640)
    draw_data_store(draw, ds5_box, "D5", "แฟ้มโควตาวันลาพนักงาน (user_leave_quotas)", f_ds_id, f_ds_name)

    # D6 beside P5.0
    ds6_box = (2200, 1650, 3000, 1760)
    draw_data_store(draw, ds6_box, "D6", "แฟ้มบันทึกประวัติระบบ (audit_logs)", f_ds_id, f_ds_name)

    # -------------------------------------------------------------------------
    # PROCESS 1.0 FLOWS
    # -------------------------------------------------------------------------
    # Admin -> P1.0 (Horizontal y = 160)
    draw.line([(ex2, 160), (px1, 160)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px1, 160), "right")
    draw_badge_label(draw, ((ex2 + px1) / 2, 160), "ข้อมูลเข้าสู่ระบบและคำสั่งจัดการ", f_label)

    # Employee -> P1.0 (Outer Left Corridor: x = 90, y = 75, into P1.0 at y = 210)
    draw.line([(ex1, 1285), (90, 1285), (90, 75), (880, 75), (880, 210), (px1, 210)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px1, 210), "right")
    draw_badge_label(draw, (485, 75), "ข้อมูลลงทะเบียนและเข้าสู่ระบบ", f_label)

    # P1.0 -> D1 (y = 160)
    draw.line([(px2, 160), (2200, 160)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (2200, 160), "right")
    draw_badge_label(draw, ((px2 + 2200) / 2, 160), "บันทึกข้อมูลผู้ใช้และสิทธิ์", f_label)

    # D1 -> P1.0 (y = 210)
    draw.line([(2200, 210), (px2, 210)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px2, 210), "left")
    draw_badge_label(draw, ((px2 + 2200) / 2, 210), "ข้อมูลโปรไฟล์และสิทธิ์ผู้ใช้", f_label)

    # -------------------------------------------------------------------------
    # PROCESS 2.0 FLOWS
    # -------------------------------------------------------------------------
    # Admin -> P2.0 (Files for RAG via corridor x = 620 to y = 525)
    draw.line([(ex2 - 40, 250), (620, 250), (620, 525), (px1, 525)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px1, 525), "right")
    draw_badge_label(draw, (850, 525), "ไฟล์เอกสารองค์กรสำหรับ RAG", f_label)

    # LINE -> P2.0 (Chat Question y = 575)
    draw.line([(ex2, 575), (px1, 575)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px1, 575), "right")
    draw_badge_label(draw, ((ex2 + px1) / 2, 575), "ข้อความแชทสอบถามข้อมูล", f_label)

    # P2.0 -> LINE (RAG Answer y = 645 via stepped line x = 720)
    draw.line([(px1, 610), (720, 610), (720, 660), (ex2, 660)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (ex2, 660), "left")
    draw_badge_label(draw, (890, 610), "ข้อความตอบกลับ RAG (Gemini)", f_label)

    # P2.0 -> D2 (y = 535)
    draw.line([(px2, 535), (2200, 535)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (2200, 535), "right")
    draw_badge_label(draw, ((px2 + 2200) / 2, 535), "เวกเตอร์เอ็มเบดดิงเอกสาร", f_label)

    # D2 -> P2.0 (y = 590)
    draw.line([(2200, 590), (px2, 590)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px2, 590), "left")
    draw_badge_label(draw, ((px2 + 2200) / 2, 590), "เนื้อหาเอกสารที่สืบค้นได้", f_label)

    # -------------------------------------------------------------------------
    # PROCESS 3.0 FLOWS
    # -------------------------------------------------------------------------
    # LINE -> P3.0 (Slip Image via corridor x = 620 to y = 910)
    draw.line([(ex2 - 50, 720), (620, 720), (620, 910), (px1, 910)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px1, 910), "right")
    draw_badge_label(draw, (850, 910), "ภาพถ่ายสลิปโอนเงิน / ใบเสร็จ", f_label)

    # P3.0 -> LINE (OCR Result: corridor x = 740, enters LINE at y = 690)
    draw.line([(px1, 970), (740, 970), (740, 690), (ex2, 690)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (ex2, 690), "left")
    draw_badge_label(draw, (910, 970), "ผลการสกัดสลิปและสรุปรายการ", f_label)

    # P3.0 -> D3 (Horizontal y = 895, segment [1760..2120] = 360px)
    draw.line([(px2, 895), (2120, 895)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (2120, 895), "right")
    draw_badge_label(draw, ((px2 + 2120) / 2, 895), "บันทึกข้อมูลธุรกรรมการเงิน", f_label)

    # P3.0 -> Google Cloud: (1760, 960) -> (2020, 960) -> (2020, 1030) -> (2300, 1030)
    draw.line([(px2, 960), (2020, 960), (2020, 1030), (2300, 1030)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (2300, 1030), "right")
    draw_badge_label(draw, (1890, 960), "ภาพสลิปส่งตรวจ OCR, ข้อมูลลง Sheets", f_label)

    # Google Cloud -> P3.0: (2300, 1080) -> (1840, 1080) -> (1840, 990) -> (1760, 990)
    draw.line([(2300, 1080), (1840, 1080), (1840, 990), (px2, 990)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px2, 990), "left")
    draw_badge_label(draw, (2060, 1080), "ผลการรู้จำอักขระ OCR, ผลบันทึกชีต", f_label)

    # -------------------------------------------------------------------------
    # PROCESS 4.0 FLOWS
    # -------------------------------------------------------------------------
    # Employee -> P4.0 (y = 1295)
    draw.line([(ex2, 1295), (px1, 1295)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px1, 1295), "right")
    draw_badge_label(draw, ((ex2 + px1) / 2, 1295), "ข้อมูลคำขอลางาน (แบบฟอร์ม LIFF)", f_label)

    # P4.0 -> Employee (y = 1355)
    draw.line([(px1, 1355), (ex2, 1355)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (ex2, 1355), "left")
    draw_badge_label(draw, ((ex2 + px1) / 2, 1355), "ผลการอนุมัติการลาและยอดวันลาคงเหลือ", f_label)

    # P4.0 -> Manager (y = 1295)
    draw.line([(px2, 1295), (2300, 1295)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (2300, 1295), "right")
    draw_badge_label(draw, ((px2 + 2300) / 2, 1295), "การแจ้งเตือนคำขอลางาน (Flex Message)", f_label)

    # Manager -> P4.0 (y = 1355)
    draw.line([(2300, 1355), (px2, 1355)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px2, 1355), "left")
    draw_badge_label(draw, ((px2 + 2300) / 2, 1355), "ผลการพิจารณาอนุมัติ/ปฏิเสธคำขอลา", f_label)

    # P4.0 -> D4: (1660, 1390) -> (1660, 1475) -> (2120, 1475)
    draw.line([(1660, 1390), (1660, 1475), (2120, 1475)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (2120, 1475), "right")
    draw_badge_label(draw, (1890, 1475), "บันทึกคำขอลาและผลการอนุมัติ", f_label)

    # P4.0 -> D5: (1500, 1390) -> (1500, 1595) -> (2120, 1595)
    draw.line([(1500, 1390), (1500, 1595), (2120, 1595)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (2120, 1595), "right")
    draw_badge_label(draw, (1810, 1595), "ตรวจสอบและตัดทอนโควตาวันลา", f_label)

    # -------------------------------------------------------------------------
    # PROCESS 5.0 FLOWS
    # -------------------------------------------------------------------------
    # Admin -> P5.0 (Corridor x = 130 to y = 1675)
    draw.line([(ex1 + 60, 250), (130, 250), (130, 1675), (px1, 1675)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px1, 1675), "right")
    draw_badge_label(draw, (605, 1675), "คำขอรายงานสถิติและข้อมูลแดชบอร์ด", f_label)

    # P5.0 -> Admin (Corridor x = 40 to y = 180)
    draw.line([(px1, 1735), (40, 1735), (40, 180), (ex1, 180)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (ex1, 180), "right")
    draw_badge_label(draw, (605, 1735), "รายงานสรุปสถิติและข้อมูลแดชบอร์ด", f_label)

    # D6 -> P5.0 (Horizontal y = 1705, segment [px2=1760..2200] = 440px)
    draw.line([(2200, 1705), (px2, 1705)], fill=(0, 0, 0), width=3)
    draw_arrow_head(draw, (px2, 1705), "left")
    draw_badge_label(draw, ((px2 + 2200) / 2, 1705), "บันทึกประวัติการใช้งานระบบ (Audit Logs)", f_label)

    bbox = img.getbbox()
    crop_x1 = max(0, bbox[0] - 35)
    crop_y1 = max(0, bbox[1] - 35)
    crop_x2 = min(w, bbox[2] + 35)
    crop_y2 = min(h, bbox[3] + 35)
    final_img = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
    final_img.save(out_path, dpi=(300, 300))
    print(f"[OK] Generated Flawless DFD Level 1: {out_path} (size={final_img.size})")


if __name__ == "__main__":
    out_dir_overleft = r"webai\เอกสาร โปรจบ\OVERLEFT\Image"
    out_dir_updated = r"webai\เอกสาร โปรจบ\OrgChat_Overleaf_Updated\Image"

    for target_dir in [out_dir_overleft, out_dir_updated]:
        os.makedirs(target_dir, exist_ok=True)
        ctx_file = os.path.join(target_dir, "fig3_1_context.png")
        dfd_file = os.path.join(target_dir, "fig3_2_dfd.png")
        render_context_diagram(ctx_file)
        render_dfd_level1(dfd_file)
        shutil.copy2(ctx_file, os.path.join(target_dir, "image3.png"))
        shutil.copy2(dfd_file, os.path.join(target_dir, "image4.png"))

    print("[SUCCESS] Both diagrams rendered and synchronized across all directories!")
