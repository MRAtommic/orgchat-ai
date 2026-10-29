# -*- coding: utf-8 -*-
"""
render_chapter4_figures.py
Generates flawless, publication-quality screenshots for Chapter 4:
- fig4_3_ocr.png: OCR Slip Processing & Google Sheets/Drive Integration
- fig4_4_leave.png: HR Leave Request LIFF Form & Manager 1-Click LINE Approval Flex Message
"""
import os
from PIL import Image, ImageDraw, ImageFont

def get_font(name, size):
    fonts = [
        f"C:\\Windows\\Fonts\\{name}",
        "C:\\Windows\\Fonts\\LeelawUI.ttf",
        "C:\\Windows\\Fonts\\tahoma.ttf",
        "C:\\Windows\\Fonts\\arial.ttf"
    ]
    for fp in fonts:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except:
                pass
    return ImageFont.load_default()

def draw_rounded_rect(draw, bbox, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)

def render_ocr_figure():
    width, height = 2200, 1420
    img = Image.new("RGB", (width, height), (248, 250, 252))
    draw = ImageDraw.Draw(img)

    f_title = get_font("LeelawUIb.ttf", 34)
    f_sub = get_font("LeelawUI.ttf", 21)
    f_header = get_font("LeelawUIb.ttf", 24)
    f_body = get_font("LeelawUI.ttf", 19)
    f_body_b = get_font("LeelawUIb.ttf", 19)
    f_sm = get_font("LeelawUI.ttf", 16)
    f_sm_b = get_font("LeelawUIb.ttf", 16)

    # Top banner header
    draw_rounded_rect(draw, (40, 25, width - 40, 110), radius=16, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
    draw.text((70, 36), "ระบบประมวลผลใบเสร็จและสลิปโอนเงิน (OCR) และบันทึกบัญชีอัตโนมัติ", fill=(15, 23, 42), font=f_title)
    draw.text((70, 74), "กระบวนการตรวจจับภาพสลิปผ่าน LINE OA, สกัดข้อมูลด้วย Vision API & Regex, และกระทบยอดบัญชีลง Google Sheets / Drive", fill=(100, 116, 139), font=f_sub)

    # ================= PANEL 1: LINE Mobile Chat (Left Panel) =================
    p1_x, p1_y, p1_w, p1_h = 40, 130, 920, 1260
    draw_rounded_rect(draw, (p1_x, p1_y, p1_x + p1_w, p1_y + p1_h), radius=22, fill=(241, 245, 249), outline=(203, 213, 225), width=2)

    # Phone Top Status Bar
    draw_rounded_rect(draw, (p1_x, p1_y, p1_x + p1_w, p1_y + 35), radius=22, fill=(15, 23, 42))
    draw.rectangle((p1_x, p1_y + 20, p1_x + p1_w, p1_y + 35), fill=(15, 23, 42))
    draw.text((p1_x + 35, p1_y + 8), "22:24", fill=(255, 255, 255), font=f_sm_b)
    draw.text((p1_x + p1_w - 180, p1_y + 8), "4G+  |  WiFi  |  88%", fill=(255, 255, 255), font=f_sm)

    # LINE App Header
    draw.rectangle((p1_x, p1_y + 35, p1_x + p1_w, p1_y + 105), fill=(24, 34, 53))
    draw.text((p1_x + 25, p1_y + 50), "<", fill=(255, 255, 255), font=get_font("arial.ttf", 28))
    draw.text((p1_x + 65, p1_y + 48), "OrgChat AI (บจก. ฮาร์ทวอมมิ่ง)", fill=(255, 255, 255), font=f_header)
    draw.text((p1_x + 65, p1_y + 78), "[Bot] ระบบบัญชีและการเงินอัตโนมัติ", fill=(148, 163, 184), font=f_sm)

    # --- Message 1: User Sends Bank Slip (Top Right) ---
    slip_path = r"webai\uploads\receipts_backup\2026\10\7598dbf0082c_Slip_03-10-2026__345.00.jpg"
    slip_h = 420
    if os.path.exists(slip_path):
        slip_img = Image.open(slip_path)
        slip_w = 210
        slip_h = int(slip_w * slip_img.size[1] / slip_img.size[0])
        slip_resized = slip_img.resize((slip_w, slip_h), Image.Resampling.LANCZOS)
        
        user_bx = p1_x + p1_w - slip_w - 35
        user_by = p1_y + 120
        draw.text((user_bx - 120, user_by + slip_h - 25), "22:24 น.  อ่านแล้ว", fill=(100, 116, 139), font=f_sm)
        img.paste(slip_resized, (user_bx, user_by))
        draw_rounded_rect(draw, (user_bx - 2, user_by - 2, user_bx + slip_w + 2, user_by + slip_h + 2), radius=10, fill=None, outline=(203, 213, 225), width=2)

    # --- Message 2: Bot Replies with LINE Flex Message (Below Slip) ---
    bot_y = p1_y + 120 + slip_h + 15
    # Bot Avatar
    draw.ellipse((p1_x + 25, bot_y, p1_x + 75, bot_y + 50), fill=(37, 99, 235))
    draw.text((p1_x + 36, bot_y + 12), "AI", fill=(255, 255, 255), font=f_header)
    draw.text((p1_x + 85, bot_y + 5), "น้องพั้น (OrgChat Financial Bot)", fill=(51, 65, 85), font=f_sm_b)

    # Flex Message Card
    fx_x, fx_y, fx_w, fx_h = p1_x + 85, bot_y + 35, 800, 500
    draw_rounded_rect(draw, (fx_x, fx_y, fx_x + fx_w, fx_y + fx_h), radius=18, fill=(255, 255, 255), outline=(226, 232, 240), width=2)

    # Flex Header
    draw_rounded_rect(draw, (fx_x, fx_y, fx_x + fx_w, fx_y + 75), radius=18, fill=(248, 250, 252))
    draw.rectangle((fx_x, fx_y + 40, fx_x + fx_w, fx_y + 75), fill=(248, 250, 252))
    draw.text((fx_x + 25, fx_y + 15), "TRANSFER SLIP VERIFICATION", fill=(100, 116, 139), font=f_sm_b)
    draw.text((fx_x + 25, fx_y + 40), "สลิปโอนเงิน (บันทึกบัญชีสำเร็จ)", fill=(15, 23, 42), font=f_header)

    # Flex Fields
    fields = [
        ("BOOKSHEET", "สลิปโอนเงิน / รายจ่ายบริษัท"),
        ("DATE & TIME", "03 ต.ค. 2569 | 22:24 น."),
        ("SENDER (จาก)", "นาย วีรภัทร ชื่นชอบ (ธ.กรุงเทพ 376-9-xxx765)"),
        ("RECEIVER (ไปยัง)", "SCB มณี SHOP (สุดารัตน์ เนื้อย่างเกาหลี)"),
        ("AMOUNT (จำนวนเงิน)", "345.00 THB"),
        ("REF NUMBER", "20261003222444031066039AD"),
        ("QR VERIFICATION", "ผ่านการตรวจสอบ (สลิปแท้ Mini QR ถูกต้อง)"),
        ("GOOGLE SHEETS", "เพิ่มแถวข้อมูลลงในชีตสลิปโอนเงิน แถวที่ #142 สำเร็จ"),
    ]
    cur_fy = fx_y + 90
    for label, val in fields:
        draw.text((fx_x + 25, cur_fy), label, fill=(100, 116, 139), font=f_sm)
        val_color = (13, 148, 136) if "ผ่าน" in val or "สำเร็จ" in val or "345" in val else (30, 41, 59)
        draw.text((fx_x + 220, cur_fy), val, fill=val_color, font=f_sm_b)
        draw.line((fx_x + 25, cur_fy + 26, fx_x + fx_w - 25, cur_fy + 26), fill=(241, 245, 249), width=1)
        cur_fy += 34

    # Action Button
    draw_rounded_rect(draw, (fx_x + 25, fx_y + fx_h - 60, fx_x + fx_w - 25, fx_y + fx_h - 15), radius=10, fill=(37, 99, 235))
    draw.text((fx_x + 240, fx_y + fx_h - 48), "[>] เปิดดูรายงานและชีตการเงินในระบบ", fill=(255, 255, 255), font=f_body_b)

    # Chat Bottom Bar
    draw_rounded_rect(draw, (p1_x, p1_y + p1_h - 75, p1_x + p1_w, p1_y + p1_h), radius=22, fill=(255, 255, 255))
    draw.rectangle((p1_x, p1_y + p1_h - 75, p1_x + p1_w, p1_y + p1_h - 40), fill=(255, 255, 255))
    draw_rounded_rect(draw, (p1_x + 60, p1_y + p1_h - 60, p1_x + p1_w - 90, p1_y + p1_h - 18), radius=10, fill=(241, 245, 249), outline=(203, 213, 225), width=1)
    draw.text((p1_x + 80, p1_y + p1_h - 48), "พิมพ์ข้อความ หรือส่งภาพสลิป/ใบเสร็จเพิ่มเติม...", fill=(148, 163, 184), font=f_sm)
    draw.text((p1_x + 20, p1_y + p1_h - 52), "[+]", fill=(71, 85, 105), font=f_header)
    draw.text((p1_x + p1_w - 70, p1_y + p1_h - 50), "ส่ง", fill=(37, 99, 235), font=f_header)

    # ================= PANEL 2: Google Sheets & Drive Sync (Right Panel) =================
    p2_x, p2_y, p2_w, p2_h = 990, 130, 1170, 1260
    draw_rounded_rect(draw, (p2_x, p2_y, p2_x + p2_w, p2_y + p2_h), radius=22, fill=(255, 255, 255), outline=(203, 213, 225), width=2)

    # Google Sheets Window Header
    draw_rounded_rect(draw, (p2_x, p2_y, p2_x + p2_w, p2_y + 85), radius=22, fill=(15, 123, 75))
    draw.rectangle((p2_x, p2_y + 45, p2_x + p2_w, p2_y + 85), fill=(15, 123, 75))
    draw.text((p2_x + 30, p2_y + 20), "Google Sheets — บริษัท ฮาร์ทวอมมิ่ง จำกัด (บันทึกรายรับ-รายจ่าย)", fill=(255, 255, 255), font=f_header)
    draw.text((p2_x + 30, p2_y + 52), "การเชื่อมต่ออัตโนมัติด้วย Google Workspace Service Account & Google Drive API v3", fill=(209, 250, 229), font=f_sm)

    # Spreadsheet Header Info
    tbl_y = p2_y + 110
    draw.text((p2_x + 30, tbl_y), "ชีตข้อมูล: สลิปโอนเงิน (Transfer Slips Log) — บันทึกผลกระทบยอดบัญชีอัตโนมัติ", fill=(15, 23, 42), font=f_body_b)

    # Spreadsheet Table
    th_y = tbl_y + 40
    headers = [
        ("ลำดับ", 70),
        ("วันเวลาทำรายการ", 180),
        ("ผู้ทำรายการ", 190),
        ("ยอดเงิน (บาท)", 140),
        ("หมวดหมู่บัญชี (AI)", 200),
        ("ธนาคาร/ปลายทาง", 210),
        ("สถานะสลิป", 120),
    ]
    cur_tx = p2_x + 30
    draw_rounded_rect(draw, (cur_tx, th_y, p2_x + p2_w - 30, th_y + 45), radius=6, fill=(241, 245, 249), outline=(203, 213, 225), width=1)
    for title, w in headers:
        draw.text((cur_tx + 12, th_y + 10), title, fill=(71, 85, 105), font=f_sm_b)
        cur_tx += w

    # Rows Data
    rows_data = [
        ("140", "2026-10-02 11:15", "อัครเดช (Ops)", "120.00", "ค่าพัสดุจัดส่ง", "KBank -> Flash Express", "ผ่าน"),
        ("141", "2026-10-03 16:40", "กุลธิดา (HR)", "1,250.00", "สวัสดิการอาหารพนักงาน", "SCB -> Makro สาขาปราจีน", "ผ่าน"),
        ("142", "2026-10-03 22:24", "วีรภัทร ชื่นชอบ", "345.00", "ค่าอาหาร/รับรองทีมงาน", "BBL -> SCB มณี SHOP", "ผ่าน (ใหม่)"),
    ]
    cur_ry = th_y + 50
    for r_idx, r in enumerate(rows_data):
        row_bg = (236, 253, 245) if r_idx == 2 else (255, 255, 255)
        border_col = (16, 185, 129) if r_idx == 2 else (226, 232, 240)
        draw_rounded_rect(draw, (p2_x + 30, cur_ry, p2_x + p2_w - 30, cur_ry + 46), radius=6, fill=row_bg, outline=border_col, width=2 if r_idx == 2 else 1)
        cur_cx = p2_x + 30
        for c_idx, (col_val, (_, col_w)) in enumerate(zip(r, headers)):
            c_color = (16, 185, 129) if r_idx == 2 and c_idx in [3, 6] else (15, 23, 42)
            c_font = f_sm_b if r_idx == 2 else f_sm
            draw.text((cur_cx + 12, cur_ry + 11), col_val, fill=c_color, font=c_font)
            cur_cx += col_w
        cur_ry += 52

    # Drive Cloud Storage Card
    drv_y = cur_ry + 25
    draw_rounded_rect(draw, (p2_x + 30, drv_y, p2_x + p2_w - 30, drv_y + 90), radius=12, fill=(240, 249, 255), outline=(186, 230, 253), width=2)
    draw.text((p2_x + 50, drv_y + 15), "Google Drive Cloud Backup: จัดเก็บสำเนาไฟล์ต้นฉบับแยกหมวดหมู่อัตโนมัติ", fill=(3, 105, 161), font=f_header)
    draw.text((p2_x + 50, drv_y + 48), "พาธโฟลเดอร์: /OrgChat_Drive/2569/10_ตุลาคม/สลิปโอนเงิน/7598dbf0082c_Slip_03-10-2026__345.00.jpg", fill=(7, 89, 133), font=f_body)

    # Pipeline Process Box
    box_y = drv_y + 115
    draw_rounded_rect(draw, (p2_x + 30, box_y, p2_x + p2_w - 30, p2_y + p2_h - 30), radius=16, fill=(248, 250, 252), outline=(226, 232, 240), width=2)
    draw.text((p2_x + 55, box_y + 25), "สรุปขั้นตอนสถาปัตยกรรมโมดูลประมวลผล OCR และการกระทบยอดอัตโนมัติ:", fill=(15, 23, 42), font=f_header)

    steps = [
        ("1. Image Ingestion:", "รับไฟล์ภาพสลิปผ่าน LINE Webhook คำนวณ MD5 Checksum ตรวจสอบการส่งซ้ำ"),
        ("2. Image Preprocessing:", "แปลงภาพเป็น Grayscale, ปรับ Adaptive Threshold และลด Noise ด้วย OpenCV"),
        ("3. Cloud Vision OCR:", "ส่งภาพเข้า Google Cloud Vision API สกัดข้อความภาษาไทยและถอดรหัส Mini QR"),
        ("4. Regex Parsing:", "ใช้ Regular Expression สกัด วันที่, เวลา, รหัสธุรกรรม, ชื่อธนาคาร และยอดเงินสุทธิ"),
        ("5. AI Categorization:", "Google Gemini 1.5 Flash วิเคราะห์ชื่อผู้รับโอนและจำแนกหมวดหมู่บัญชีองค์กร"),
        ("6. Sheets & Drive Sync:", "บันทึกข้อมูลเข้า Google Sheets แบบเรียลไทม์ และสำรองไฟล์ลง Google Drive"),
    ]
    sy = box_y + 75
    for st_title, st_desc in steps:
        draw.text((p2_x + 55, sy), st_title, fill=(37, 99, 235), font=f_body_b)
        draw.text((p2_x + 280, sy), st_desc, fill=(51, 65, 85), font=f_sm)
        sy += 55

    # Save
    out_dir = r"webai\เอกสาร โปรจบ\OVERLEFT\Image"
    os.makedirs(out_dir, exist_ok=True)
    out_fp = os.path.join(out_dir, "fig4_3_ocr.png")
    img.save(out_fp, "PNG", quality=95)
    print("Saved clean fig4_3_ocr.png:", out_fp, os.path.getsize(out_fp))

if __name__ == "__main__":
    render_ocr_figure()
