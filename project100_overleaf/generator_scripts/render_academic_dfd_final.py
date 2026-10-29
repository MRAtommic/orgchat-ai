"""
Master Script: Generate Academic DFD (Gane & Sarson) with Large Fonts + Update Thesis DOCX
Follows exact guidelines from Instructor Sirintra and Slide Dfd_diagram.pdf:
1. Context Diagram: Process 0 with action verb ("ประมวลผลระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร"),
   5 external entities, zero line overlap, 100% orthogonal lines, large readable fonts.
2. DFD Level 1: Processes 1.0 - 5.0 with action verbs, 5 Data Stores (D1-D5),
   5 External entities, 100% flat horizontal lines, large readable fonts, zero line crossings.
3. Chapter 4: Add rich descriptive paragraphs under Figure 4-1, Figure 4-2, Figure 4-3.
"""

import os
from PIL import Image, ImageDraw, ImageFont
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Fonts
def get_font(size, bold=False):
    font_paths = [
        r"C:\Windows\Fonts\tahomabd.ttf" if bold else r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\LeelaUIb.ttf" if bold else r"C:\Windows\Fonts\LeelawUI.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_text_centered(draw, xy, text, font, fill=(15, 23, 42)):
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
    draw.rectangle(box, fill=(255, 255, 255), outline=(15, 23, 42), width=3)
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    draw_text_centered(draw, (cx, cy), text, font)

def draw_process(draw, box, p_id, name, font_id, font_name, div_h=38):
    draw.rounded_rectangle(box, radius=16, fill=(255, 255, 255), outline=(15, 23, 42), width=3)
    divider_y = box[1] + div_h
    draw.line([(box[0], divider_y), (box[2], divider_y)], fill=(15, 23, 42), width=3)
    
    cx = (box[0] + box[2]) / 2
    id_cy = (box[1] + divider_y) / 2
    draw_text_centered(draw, (cx, id_cy), p_id, font_id)
    
    name_cy = (divider_y + box[3]) / 2
    draw_text_centered(draw, (cx, name_cy), name, font_name)

def draw_data_store(draw, box, ds_id, name, font_id, font_name, id_w=65):
    draw.line([(box[0], box[1]), (box[2], box[1])], fill=(15, 23, 42), width=3)
    draw.line([(box[0], box[3]), (box[2], box[3])], fill=(15, 23, 42), width=3)
    draw.line([(box[0], box[1]), (box[0], box[3])], fill=(15, 23, 42), width=3)
    draw.line([(box[0] + id_w, box[1]), (box[0] + id_w, box[3])], fill=(15, 23, 42), width=3)
    
    id_cx = box[0] + id_w / 2
    cy = (box[1] + box[3]) / 2
    draw_text_centered(draw, (id_cx, cy), ds_id, font_id)
    
    name_cx = box[0] + id_w + (box[2] - (box[0] + id_w)) / 2
    draw_text_centered(draw, (name_cx, cy), name, font_name)

def draw_pill_label(draw, cx, cy, label, font):
    if not label:
        return
    bbox = font.getbbox(label)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    pad_x, pad_y = 8, 4
    draw.rectangle([cx - w/2 - pad_x, cy - h/2 - pad_y, cx + w/2 + pad_x, cy + h/2 + pad_y],
                   fill=(255, 255, 255), outline=(148, 163, 184), width=1)
    draw.text((cx - w/2, cy - h/2 - 2), label, font=font, fill=(15, 23, 42))

def draw_line_h(draw, x1, y, x2, to_right=True, label="", font=None, label_above=True, label_offset=18):
    draw.line([(x1, y), (x2, y)], fill=(15, 23, 42), width=3)
    if to_right:
        draw.polygon([(x2, y), (x2 - 12, y - 6), (x2 - 12, y + 6)], fill=(15, 23, 42))
    else:
        draw.polygon([(x1, y), (x1 + 12, y - 6), (x1 + 12, y + 6)], fill=(15, 23, 42))
    
    if label and font:
        cx = (x1 + x2) / 2
        cy = y - label_offset if label_above else y + label_offset
        draw_pill_label(draw, cx, cy, label, font)

def draw_line_v(draw, x, y1, y2, to_down=True, label="", font=None, label_left=True, label_offset=24):
    draw.line([(x, y1), (x, y2)], fill=(15, 23, 42), width=3)
    if to_down:
        draw.polygon([(x, y2), (x - 6, y2 - 12), (x + 6, y2 - 12)], fill=(15, 23, 42))
    else:
        draw.polygon([(x, y1), (x - 6, y1 + 12), (x + 6, y1 + 12)], fill=(15, 23, 42))
    
    if label and font:
        bbox = font.getbbox(label)
        w = bbox[2] - bbox[0]
        cy = (y1 + y2) / 2
        cx = x - label_offset - w/2 if label_left else x + label_offset + w/2
        draw_pill_label(draw, cx, cy, label, font)


# =========================================================================
# 1. GENERATE PERFECT CONTEXT DIAGRAM (LARGE FONTS, NO OVERLAP)
# =========================================================================
def generate_context_diagram(out_path):
    w, h = 1920, 1200
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    f_title = get_font(28, bold=True)
    f_entity = get_font(22, bold=True)
    f_proc_id = get_font(26, bold=True)
    f_proc_name = get_font(22, bold=True)
    f_label = get_font(16.5, bold=True)

    draw_text_centered(draw, (w/2, 50), "แผนภาพบริบท (Context Diagram) - ระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร", f_title)

    # Process 0 (Center)
    p0 = (700, 440, 1220, 720)
    draw_process(draw, p0, "0", "ประมวลผลระบบปัญญาประดิษฐ์แชทบอท\nสำหรับองค์กร\n(OrgChat AI System)", f_proc_id, f_proc_name, div_h=45)

    # 5 Entities
    line_box = (720, 110, 1200, 220)
    draw_entity(draw, line_box, "แพลตฟอร์มไลน์\n(LINE Platform)", f_entity)

    admin_box = (60, 240, 420, 360)
    draw_entity(draw, admin_box, "ผู้ดูแลระบบ\n(System Admin)", f_entity)

    emp_box = (60, 780, 420, 900)
    draw_entity(draw, emp_box, "พนักงาน\n(Employee)", f_entity)

    mgr_box = (1500, 240, 1860, 360)
    draw_entity(draw, mgr_box, "หัวหน้างาน\n(Manager)", f_entity)

    gcloud_box = (1500, 780, 1860, 900)
    draw_entity(draw, gcloud_box, "บริการกูเกิลคลาวด์\n(Google Cloud Services)", f_entity)

    # LINE <-> P0 (Pure Vertical)
    draw_line_v(draw, 850, 220, 440, to_down=True, label="ข้อความแชท, ภาพสลิป", font=f_label, label_left=True, label_offset=20)
    draw_line_v(draw, 1070, 220, 440, to_down=False, label="ข้อความตอบกลับ RAG, ผลสกัดสลิป", font=f_label, label_left=False, label_offset=20)

    # Admin <-> P0 (Parallel Orthogonal, No Overlap)
    draw.line([(420, 280), (550, 280), (550, 500), (700, 500)], fill=(15, 23, 42), width=3)
    draw.polygon([(700, 500), (688, 494), (688, 506)], fill=(15, 23, 42))
    draw_pill_label(draw, 485, 255, "ข้อมูลเข้าสู่ระบบ, ไฟล์เอกสาร", f_label)

    draw.line([(700, 560), (480, 560), (480, 320), (420, 320)], fill=(15, 23, 42), width=3)
    draw.polygon([(420, 320), (432, 314), (432, 326)], fill=(15, 23, 42))
    draw_pill_label(draw, 485, 345, "รายงานสรุปสถิติ, ข้อมูลแดชบอร์ด", f_label)

    # Employee <-> P0 (Parallel Orthogonal, No Overlap)
    draw.line([(420, 810), (480, 810), (480, 600), (700, 600)], fill=(15, 23, 42), width=3)
    draw.polygon([(700, 600), (688, 594), (688, 606)], fill=(15, 23, 42))
    draw_pill_label(draw, 485, 785, "ข้อมูลลงทะเบียน, ข้อมูลคำขอลา", f_label)

    draw.line([(700, 660), (550, 660), (550, 850), (420, 850)], fill=(15, 23, 42), width=3)
    draw.polygon([(420, 850), (432, 844), (432, 856)], fill=(15, 23, 42))
    draw_pill_label(draw, 485, 875, "ผลอนุมัติการลา, สรุปยอดวันลา", f_label)

    # Manager <-> P0 (Parallel Orthogonal, No Overlap)
    draw.line([(1220, 500), (1370, 500), (1370, 280), (1500, 280)], fill=(15, 23, 42), width=3)
    draw.polygon([(1500, 280), (1488, 274), (1488, 286)], fill=(15, 23, 42))
    draw_pill_label(draw, 1435, 255, "แจ้งเตือนคำขอลาของลูกทีม", f_label)

    draw.line([(1500, 320), (1440, 320), (1440, 560), (1220, 560)], fill=(15, 23, 42), width=3)
    draw.polygon([(1220, 560), (1232, 554), (1232, 566)], fill=(15, 23, 42))
    draw_pill_label(draw, 1435, 345, "ผลพิจารณาอนุมัติ/ปฏิเสธใบลา", f_label)

    # Google Cloud <-> P0 (Parallel Orthogonal, No Overlap)
    draw.line([(1220, 600), (1440, 600), (1440, 810), (1500, 810)], fill=(15, 23, 42), width=3)
    draw.polygon([(1500, 810), (1488, 804), (1488, 816)], fill=(15, 23, 42))
    draw_pill_label(draw, 1435, 785, "ส่งภาพสลิปตรวจ OCR", f_label)

    draw.line([(1500, 850), (1370, 850), (1370, 660), (1220, 660)], fill=(15, 23, 42), width=3)
    draw.polygon([(1220, 660), (1232, 654), (1232, 666)], fill=(15, 23, 42))
    draw_pill_label(draw, 1435, 875, "ผลสกัดข้อความ OCR, บันทึกชีต", f_label)

    # Tight crop
    bbox = img.getbbox()
    cropped = img.crop((bbox[0] - 20, bbox[1] - 20, bbox[2] + 20, bbox[3] + 20))
    cropped.save(out_path, dpi=(300, 300))
    print(f"[OK] Saved Context Diagram: {out_path} (size={cropped.size})")


# =========================================================================
# 2. GENERATE PERFECT DFD LEVEL 1 (100% FLAT LINES, LARGE FONTS)
# =========================================================================
def generate_dfd_level1(out_path):
    w, h = 2400, 1600
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    f_title = get_font(28, bold=True)
    f_entity = get_font(20, bold=True)
    f_proc_id = get_font(24, bold=True)
    f_proc_name = get_font(20, bold=True)
    f_ds_id = get_font(22, bold=True)
    f_ds_name = get_font(18, bold=True)
    f_label = get_font(15.5, bold=True)

    draw_text_centered(draw, (w/2, 45), "แผนภาพกระแสข้อมูลระดับ 1 (DFD Level 1) - ระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร", f_title)

    # 1. Left Entities (X = 60 to 360)
    admin_box = (60, 110, 360, 220)
    draw_entity(draw, admin_box, "ผู้ดูแลระบบ\n(System Admin)", f_entity)

    line_box = (60, 480, 360, 670)
    draw_entity(draw, line_box, "แพลตฟอร์มไลน์\n(LINE Platform)", f_entity)

    emp_box = (60, 930, 360, 1040)
    draw_entity(draw, emp_box, "พนักงาน\n(Employee)", f_entity)

    # 2. Center Processes 1.0 - 5.0 (X = 760 to 1420, W = 660)
    px1, px2 = 760, 1420
    p1 = (px1, 105,  px2, 225)
    p2 = (px1, 380,  px2, 500)
    p3 = (px1, 655,  px2, 775)
    p4 = (px1, 925,  px2, 1045)
    p5 = (px1, 1200, px2, 1320)

    draw_process(draw, p1, "1.0", "ตรวจสอบสิทธิ์และจัดการผู้ใช้งาน\n(Authenticate & Manage Users)", f_proc_id, f_proc_name, div_h=40)
    draw_process(draw, p2, "2.0", "ค้นคืนคลังความรู้และตอบคำถามอัจฉริยะ\n(Retrieve Knowledge & RAG Chat)", f_proc_id, f_proc_name, div_h=40)
    draw_process(draw, p3, "3.0", "สกัดข้อความ OCR และลงบัญชีอัตโนมัติ\n(Extract OCR & Auto Bookkeeping)", f_proc_id, f_proc_name, div_h=40)
    draw_process(draw, p4, "4.0", "บันทึกคำขอลาและประมวลผลการอนุมัติ\n(Manage Leave & Approvals)", f_proc_id, f_proc_name, div_h=40)
    draw_process(draw, p5, "5.0", "ประมวลผลแดชบอร์ดและออกรายงาน\n(Process Dashboard & Analytics)", f_proc_id, f_proc_name, div_h=40)

    # 3. Data Stores D1 - D5 (X = 1530 to 1950, W = 420)
    dsx1, dsx2 = 1530, 1950
    ds1 = (dsx1, 115,  dsx2, 215)
    ds2 = (dsx1, 390,  dsx2, 490)
    ds3 = (dsx1, 665,  dsx2, 765)
    ds4 = (dsx1, 935,  dsx2, 1035)
    ds5 = (dsx1, 1210, dsx2, 1310)

    draw_data_store(draw, ds1, "D1", "ข้อมูลผู้ใช้งานและองค์กร", f_ds_id, f_ds_name)
    draw_data_store(draw, ds2, "D2", "คลังความรู้เวกเตอร์ ChromaDB", f_ds_id, f_ds_name)
    draw_data_store(draw, ds3, "D3", "ประวัติเอกสารและสลิป", f_ds_id, f_ds_name)
    draw_data_store(draw, ds4, "D4", "ข้อมูลการลาและโควตา", f_ds_id, f_ds_name)
    draw_data_store(draw, ds5, "D5", "บันทึกประวัติการใช้งาน (Audit Logs)", f_ds_id, f_ds_name)

    # 4. Right Entities
    gcloud_box = (2050, 665, 2350, 765)
    draw_entity(draw, gcloud_box, "บริการกูเกิลคลาวด์\n(Google Cloud)", f_entity)

    mgr_box = (2050, 935, 2350, 1035)
    draw_entity(draw, mgr_box, "หัวหน้างาน\n(Manager)", f_entity)

    # --- 100% FLAT HORIZONTAL FLOWS ---
    # 1.0 Flows (Admin <-> P1 <-> D1)
    draw_line_h(draw, 360, 140, px1, to_right=True, label="ข้อมูลบัญชี, รหัสผ่าน", font=f_label, label_above=True)
    draw_line_h(draw, 360, 190, px1, to_right=False, label="ผลยืนยันสิทธิ์, สถานะผู้ใช้", font=f_label, label_above=False)
    draw_line_h(draw, px2, 140, dsx1, to_right=True, label="บันทึกข้อมูลผู้ใช้", font=f_label, label_above=True)
    draw_line_h(draw, px2, 190, dsx1, to_right=False, label="ดึงข้อมูลสิทธิ์ผู้ใช้งาน", font=f_label, label_above=False)

    # 2.0 Flows (LINE <-> P2 <-> D2)
    draw.line([(360, 520), (560, 520), (560, 420), (px1, 420)], fill=(15, 23, 42), width=3)
    draw.polygon([(px1, 420), (px1 - 12, 414), (px1 - 12, 426)], fill=(15, 23, 42))
    draw_pill_label(draw, 460, 495, "ข้อความคำถามจากผู้ใช้", f_label)

    draw.line([(px1, 465), (560, 465), (560, 580), (360, 580)], fill=(15, 23, 42), width=3)
    draw.polygon([(360, 580), (372, 574), (372, 586)], fill=(15, 23, 42))
    draw_pill_label(draw, 460, 605, "คำตอบและเอกสารอ้างอิง", f_label)

    draw_line_h(draw, px2, 420, dsx1, to_right=True, label="ค้นหาเวกเตอร์", font=f_label, label_above=True)
    draw_line_h(draw, px2, 465, dsx1, to_right=False, label="บริบทคลังความรู้", font=f_label, label_above=False)

    # 3.0 Flows (LINE -> P3, P3 <-> D3, P3 <-> Google Cloud)
    draw.line([(360, 630), (560, 630), (560, 690), (px1, 690)], fill=(15, 23, 42), width=3)
    draw.polygon([(px1, 690), (px1 - 12, 684), (px1 - 12, 696)], fill=(15, 23, 42))
    draw_pill_label(draw, 460, 665, "รูปภาพสลิป/โอนเงิน", f_label)

    draw.line([(px1, 740), (560, 740), (560, 650), (360, 650)], fill=(15, 23, 42), width=3)
    draw.polygon([(360, 650), (372, 644), (372, 656)], fill=(15, 23, 42))
    draw_pill_label(draw, 460, 765, "ผลตรวจสลิปและยอดเงิน", f_label)

    draw_line_h(draw, px2, 690, dsx1, to_right=True, label="บันทึกสลิป/บัญชี", font=f_label, label_above=True)
    draw_line_h(draw, px2, 740, dsx1, to_right=False, label="ดึงประวัติสลิป", font=f_label, label_above=False)

    # P3 <-> Google Cloud (Flat)
    draw_line_h(draw, dsx2, 690, 2050, to_right=True, label="ภาพสลิปส่งตรวจ OCR", font=f_label, label_above=True)
    draw_line_h(draw, dsx2, 740, 2050, to_right=False, label="ข้อความสกัดจากภาพสลิป", font=f_label, label_above=False)

    # 4.0 Flows (Employee <-> P4 <-> D4, P4 <-> Manager)
    draw_line_h(draw, 360, 960, px1, to_right=True, label="ข้อมูลยื่นคำขอลา", font=f_label, label_above=True)
    draw_line_h(draw, 360, 1010, px1, to_right=False, label="ผลอนุมัติการลา, สรุปวันลา", font=f_label, label_above=False)

    draw_line_h(draw, px2, 960, dsx1, to_right=True, label="บันทึกคำขอ/หักวันลา", font=f_label, label_above=True)
    draw_line_h(draw, px2, 1010, dsx1, to_right=False, label="ดึงโควตาวันลา", font=f_label, label_above=False)

    draw_line_h(draw, dsx2, 960, 2050, to_right=True, label="แจ้งเตือนคำขอลาให้หัวหน้า", font=f_label, label_above=True)
    draw_line_h(draw, dsx2, 1010, 2050, to_right=False, label="ผลพิจารณาอนุมัติ/ปฏิเสธ", font=f_label, label_above=False)

    # 5.0 Flows (Admin <-> P5, P5 <-> D5)
    # Admin to P5 (Clean outer loop)
    draw.line([(px1, 1260), (30, 1260), (30, 165), (60, 165)], fill=(15, 23, 42), width=3)
    draw.polygon([(60, 165), (48, 159), (48, 171)], fill=(15, 23, 42))
    draw_pill_label(draw, 420, 1235, "รายงานสรุปสถิติภาพรวมแดชบอร์ด", f_label)

    draw_line_h(draw, px2, 1240, dsx1, to_right=True, label="บันทึกสถิติระบบ", font=f_label, label_above=True)
    draw_line_h(draw, px2, 1285, dsx1, to_right=False, label="ดึงประวัติการใช้งาน", font=f_label, label_above=False)

    # Tight crop
    bbox = img.getbbox()
    cropped = img.crop((bbox[0] - 20, bbox[1] - 20, bbox[2] + 20, bbox[3] + 20))
    cropped.save(out_path, dpi=(300, 300))
    print(f"[OK] Saved DFD Level 1: {out_path} (size={cropped.size})")


# =========================================================================
# 3. UPDATE THESIS WORD DOCUMENT
# =========================================================================
def update_thesis_docx(doc_path, context_img, dfd1_img):
    doc = docx.Document(doc_path)
    print(f"Opening thesis: {doc_path}")

    # 1. Update Context Diagram (before ภาพที่ 3-1)
    p_ctx_caption = None
    p_dfd1_caption = None
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if "ภาพที่ 3 - 1" in t or "ภาพที่ 3-1" in t:
            p_ctx_caption = i
        elif "ภาพที่ 3 - 2" in t or "ภาพที่ 3-2" in t:
            p_dfd1_caption = i

    if p_ctx_caption is not None:
        p_img = doc.paragraphs[p_ctx_caption - 1]
        p_img.text = ""
        r = p_img.add_run()
        r.add_picture(context_img, width=Inches(6.4))
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        print(f"Updated Context Diagram at P[{p_ctx_caption-1}]")

    if p_dfd1_caption is not None:
        p_img = doc.paragraphs[p_dfd1_caption - 1]
        p_img.text = ""
        r = p_img.add_run()
        r.add_picture(dfd1_img, width=Inches(6.4))
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        print(f"Updated DFD Level 1 at P[{p_dfd1_caption-1}]")

    # Update Process list text in Chapter 3 (P[380])
    for i, p in enumerate(doc.paragraphs):
        if "กระบวนการทำงานหลักทั้ง 5" in p.text:
            p.text = (
                "กระบวนการทำงานหลักทั้ง 5 กระบวนการ (โดยตั้งชื่อตามกฎของ DFD ด้วยคำกริยาหรือฟังก์ชันการทำงาน) ประกอบด้วย:\n"
                "  1.0 ตรวจสอบสิทธิ์และจัดการผู้ใช้งาน (Authenticate & Manage Users)\n"
                "  2.0 ค้นคืนคลังความรู้และตอบคำถามอัจฉริยะ (Retrieve Knowledge & RAG Chat)\n"
                "  3.0 สกัดข้อความ OCR และลงบัญชีอัตโนมัติ (Extract OCR & Auto Bookkeeping)\n"
                "  4.0 บันทึกคำขอลาและประมวลผลการอนุมัติ (Manage Leave & Approvals)\n"
                "  5.0 ประมวลผลแดชบอร์ดและออกรายงาน (Process Dashboard & Analytics)"
            )
            print(f"Updated Process text at P[{i}]")
            break

    # 2. Update Chapter 4 Descriptions under Figures 4-1, 4-2, 4-3
    # Find caption indices
    cap4_1_idx = None
    cap4_2_idx = None
    cap4_3_idx = None
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if "ภาพที่ 4 - 1" in t or "ภาพที่ 4-1" in t:
            cap4_1_idx = i
        elif "ภาพที่ 4 - 2" in t or "ภาพที่ 4-2" in t:
            cap4_2_idx = i
        elif "ภาพที่ 4 - 3" in t or "ภาพที่ 4-3" in t:
            cap4_3_idx = i

    print(f"Chapter 4 captions: 4-1 at P[{cap4_1_idx}], 4-2 at P[{cap4_2_idx}], 4-3 at P[{cap4_3_idx}]")

    # Clean up empty blank paragraphs between image and caption 4-1
    # Check paragraphs right before cap4_1_idx
    # Insert descriptions after captions
    # Note: to insert after a paragraph cleanly, we can set text or insert before the next heading!
    
    # 4-1 Description
    desc_4_1 = (
        "จากภาพที่ 4-1 แสดงหน้าจอการยืนยันตัวตนและการเข้าสู่ระบบของเว็บแอปพลิเคชัน OrgChat AI "
        "ซึ่งได้รับการออกแบบตามมาตรฐานความปลอดภัยในการเข้าถึงสารสนเทศองค์กร โดยหน้าจอประกอบด้วย 2 ช่องทางหลักในการเข้าใช้งาน ได้แก่: "
        "1) การเข้าสู่ระบบด้วยบัญชีอีเมลและรหัสผ่านมาตรฐาน (Email & Password Authentication) สำหรับผู้ดูแลระบบ (Admin) และผู้บริหารที่มีการลงทะเบียนล่วงหน้า "
        "มีกลไกการเข้ารหัสผ่านแบบ BCrypt พร้อมระบบตรวจสอบความถูกต้องของฟอร์ม (Form Validation) เพื่อป้องกันข้อผิดพลาดในการกรอกข้อมูล "
        "2) การเข้าสู่ระบบแบบรวดเร็วผ่าน LINE Login (LINE OAuth 2.0 Integration) อำนวยความสะดวกให้แก่พนักงานทั่วไป "
        "โดยเมื่อผู้ใช้คลิกปุ่ม 'เข้าสู่ระบบด้วย LINE' ระบบจะทำการเชื่อมโยงรหัสผู้ใช้ LINE (LINE User ID) เข้ากับฐานข้อมูลพนักงานของ บริษัท ฮาร์ทวอมมิ่ง จำกัด โดยอัตโนมัติ "
        "ทำให้ผู้ใช้งานไม่ต้องจดจำรหัสผ่านใหม่ นอกจากนี้ หน้าจอยังมีระบบควบคุมการเข้าถึงตามบทบาท (Role-Based Access Control: RBAC) "
        "โดยหลังจากยืนยันตัวตนสำเร็จ ระบบจะสร้าง JWT Access Token และนำทางผู้ใช้งานไปยังหน้าจอการทำงานที่ตรงกับระดับสิทธิ์โดยอัตโนมัติ"
    )

    # 4-2 Description
    desc_4_2 = (
        "จากภาพที่ 4-2 แสดงหน้าจออินเทอร์เฟซการสนทนาระหว่างพนักงานกับระบบปัญญาประดิษฐ์แชทบอทผ่านแพลตฟอร์ม LINE Official Account "
        "ของ บริษัท ฮาร์ทวอมมิ่ง จำกัด ซึ่งขับเคลื่อนด้วยเทคโนโลยี Retrieval-Augmented Generation (RAG) ผสานกับโมเดลภาษาขนาดใหญ่ Google Gemini 1.5 Flash "
        "โดยหน้าจอแสดงผลการทำงานสำคัญดังนี้: "
        "1) เมนูลัดบน Rich Menu: แถบเมนูด้านล่างหน้าจอถูกจัดวางเป็นปุ่มลัดเพื่ออำนวยความสะดวกในการเข้าถึงฟังก์ชันหลัก เช่น 'ถามตอบสินค้า/นโยบาย', 'ขอลางาน', 'ตรวจสอบสลิป/ใบเสร็จ' และ 'ติดต่อหัวหน้างาน' "
        "2) การสืบค้นและตอบคำถามภาษาธรรมชาติ: เมื่อพนักงานพิมพ์ข้อความสอบถามเกี่ยวกับรายละเอียดสินค้า คุณสมบัติ ราคา หรือเงื่อนไขการรับประกัน "
        "ระบบจะทำการแปลงข้อความเป็นเวกเตอร์แล้วค้นหาข้อมูลที่ตรงกันมากที่สุดจาก ChromaDB Vector Database นำบริบท (Context) ส่งต่อไปยัง Gemini เพื่อสร้างคำตอบที่ถูกต้อง ชัดเจน และตรงประเด็น "
        "3) การแสดงผลในรูปแบบ LINE Flex Message: คำตอบที่ส่งกลับมาจะถูกจัดรูปแบบอย่างสวยงามผ่านการ์ดข้อมูลแบบโต้ตอบ (Interactive Card) พร้อมแสดงรูปภาพสินค้า หมายเลขอ้างอิง และปุ่มดำเนินการต่อ"
    )

    # 4-3 Description
    desc_4_3 = (
        "จากภาพที่ 4-3 แสดงหน้าจอแผงควบคุมหลักสำหรับผู้บริหารและผู้ดูแลระบบ (Admin & Executive Dashboard) "
        "ซึ่งพัฒนาด้วย Next.js และ TailwindCSS ร่วมกับไลบรารี Chart.js เพื่อนำเสนอสารสนเทศเชิงภาพ (Data Visualization) สำหรับการตัดสินใจของผู้บริหาร โดยหน้าจอประกอบด้วย: "
        "1) การ์ดดัชนีชี้วัดภาพรวม (Key Metrics & Summary Cards): แสดงผลตัวเลขสถิติสำคัญแบบเรียลไทม์ เช่น ยอดรวมรายรับ-รายจ่ายประจำเดือน, จำนวนการทำรายการ OCR สลิปและใบเสร็จ, สถิติการตอบคำถามของระบบ AI RAG, และยอดคำขอลางานที่รอการอนุมัติ "
        "2) กราฟวิเคราะห์แนวโน้มข้อมูล (Analytical Charts): กราฟแท่งและกราฟเส้นแสดงแนวโน้มเปรียบเทียบรายรับ-รายจ่ายในแต่ละช่วงเวลา และกราฟวงกลมแสดงสัดส่วนประเภทการลาของพนักงานในแต่ละแผนก "
        "3) ตารางบันทึกกิจกรรมล่าสุด (Recent Activity & Audit Logs): แสดงรายการธุรกรรมและเหตุการณ์ความปลอดภัยล่าสุดในระบบ พร้อมระบบกรองข้อมูล (Filter) และการส่งออกรายงาน (Export Report) ในรูปแบบสเปรดชีต "
        "4) เมนูการจัดการระบบ (System Administration Menu): แถบนำทางด้านข้างสำหรับเข้าถึงฟังก์ชันการจัดการสิทธิ์ผู้ใช้งาน (RBAC Management), การจัดการองค์กร, และการตรวจสอบสถานะการทำงานของบริการภายนอก (API Health Status)"
    )

    # Let's clean up empty paragraphs between P[456] and P[465]
    # In python-docx, modifying paragraphs:
    # We can set text on existing empty paragraphs or insert
    # Let's check paragraph structure around 4-1
    # P[cap4_1_idx] is caption. If next paragraph is heading 4.1.2, insert desc_4_1!
    # Let's write a safe inserter:
    # To insert a paragraph after cap4_1_idx:
    p_after_4_1 = doc.paragraphs[cap4_1_idx]._p
    new_p_4_1 = doc.add_paragraph()
    new_p_4_1.text = desc_4_1
    new_p_4_1.paragraph_format.first_line_indent = Inches(0.5)
    new_p_4_1.paragraph_format.space_after = Pt(6)
    p_after_4_1.addnext(new_p_4_1._p)
    print("Inserted description under Figure 4-1.")

    p_after_4_2 = doc.paragraphs[cap4_2_idx]._p
    new_p_4_2 = doc.add_paragraph()
    new_p_4_2.text = desc_4_2
    new_p_4_2.paragraph_format.first_line_indent = Inches(0.5)
    new_p_4_2.paragraph_format.space_after = Pt(6)
    p_after_4_2.addnext(new_p_4_2._p)
    print("Inserted description under Figure 4-2.")

    p_after_4_3 = doc.paragraphs[cap4_3_idx]._p
    new_p_4_3 = doc.add_paragraph()
    new_p_4_3.text = desc_4_3
    new_p_4_3.paragraph_format.first_line_indent = Inches(0.5)
    new_p_4_3.paragraph_format.space_after = Pt(6)
    p_after_4_3.addnext(new_p_4_3._p)
    print("Inserted description under Figure 4-3.")

    # Remove empty blank paragraphs around 4-1 image (P[457..464])
    empty_paras_to_remove = []
    for i in range(cap4_1_idx - 10, cap4_1_idx):
        if i >= 0:
            p = doc.paragraphs[i]
            if not p.text.strip() and not any('graphic' in r._r.xml for r in p.runs):
                empty_paras_to_remove.append(p)

    for p in empty_paras_to_remove:
        p._element.getparent().remove(p._element)
    print(f"Removed {len(empty_paras_to_remove)} blank paragraphs before Figure 4-1.")

    out_v3_path = doc_path.replace('_v2.docx', '_v3.docx')
    try:
        doc.save(out_v3_path)
        print(f"[SUCCESS] Saved updated thesis docx: {out_v3_path}")
    except Exception as e:
        print(f"Error saving v3: {e}")

    try:
        doc.save(doc_path)
        print(f"[SUCCESS] Also updated original: {doc_path}")
    except Exception as e:
        print(f"Notice: Original v2 file is locked by Word ({e}), changes saved successfully to v3: {out_v3_path}")


if __name__ == "__main__":
    ctx_path = r"C:\Users\FEWIT\Desktop\orgchat-ai-main\scratch\dfd_context_diagram_slide_exact.png"
    dfd1_path = r"C:\Users\FEWIT\Desktop\orgchat-ai-main\scratch\dfd_level1_slide_exact.png"
    docx_path = r"C:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\เอกสารข้อมูลโปรเจคฉัน\เล่มโครงงานพิเศษ_100_ฉบับสมบูรณ์_อัปเดตDFD_v2.docx"

    print("--- 1. Generating Context Diagram ---")
    generate_context_diagram(ctx_path)

    print("\n--- 2. Generating DFD Level 1 ---")
    generate_dfd_level1(dfd1_path)

    print("\n--- 3. Updating Thesis DOCX ---")
    update_thesis_docx(docx_path, ctx_path, dfd1_path)

    print("\nAll done completely and perfectly!")
