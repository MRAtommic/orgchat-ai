# -*- coding: utf-8 -*-
"""
Payment Voucher & Receipt Substitute PDF Generation Service
Generates formal Thai accounting PDF documents:
1. Receipt Substitute (ใบแทนใบเสร็จรับเงิน / Form 50)
2. Payment Voucher (ใบสำคัญจ่าย / Batch Payment Voucher)
"""
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("OrgChatAI.PaymentVoucherService")

try:
    from fpdf import FPDF
except ImportError:
    try:
        from fpdf2 import FPDF
    except ImportError:
        class FPDF:
            def __init__(self, *args, **kwargs): pass
            def add_page(self): pass
            def add_font(self, *args, **kwargs): pass
            def set_font(self, *args, **kwargs): pass
            def cell(self, *args, **kwargs): pass
            def ln(self, *args, **kwargs): pass
            def multi_cell(self, *args, **kwargs): pass
            def line(self, *args, **kwargs): pass
            def output(self, *args): pass


def _get_thai_font_path():
    """Find available Thai TTF font on OS."""
    font_paths = []
    if os.name == 'nt':
        font_paths = [
            r"C:\Windows\Fonts\thsarabunnew.ttf",
            r"C:\Windows\Fonts\leelawad.ttf",
            r"C:\Windows\Fonts\tahoma.ttf",
            r"C:\Windows\Fonts\arial.ttf"
        ]
    else:
        font_paths = [
            "/usr/share/fonts/truetype/thai/THSarabunNew.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansThai-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
    for f in font_paths:
        if os.path.exists(f):
            return f
    return None


class ThaiPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.font_path = _get_thai_font_path()
        if self.font_path:
            try:
                self.add_font("THFont", "", self.font_path)
                self.has_thai_font = True
            except Exception as e:
                logger.warning(f"Failed to load Thai font {self.font_path}: {e}")
                self.has_thai_font = False
        else:
            self.has_thai_font = False

    def set_thai_font(self, style="", size=12):
        if self.has_thai_font:
            self.set_font("THFont", style, size)
        else:
            self.set_font("Helvetica", style, size)


def generate_receipt_substitute_pdf(item_data: dict, org_name: str = "องค์กรของคุณ") -> tuple[str, str]:
    """
    Generates a Receipt Substitute (ใบแทนใบเสร็จรับเงิน / Form 50) PDF file.
    Returns (abs_file_path, filename).
    """
    downloads_dir = Path("static/downloads")
    downloads_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ref_id = item_data.get("ref_number") or f"RS-{timestamp[-6:]}"
    safe_ref = "".join(c for c in ref_id if c.isalnum() or c in ['-', '_'])
    filename = f"Receipt_Substitute_{safe_ref}.pdf"
    file_path = downloads_dir / filename

    pdf = ThaiPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header Title
    pdf.set_thai_font(size=18)
    pdf.cell(0, 10, text="ใบรับรองแทนใบเสร็จรับเงิน (Form 50)", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_thai_font(size=12)
    pdf.cell(0, 8, text=f"ส่วนงาน / องค์กร: {org_name}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    # Info Box
    date_str = item_data.get("date") or datetime.now().strftime("%d/%m/%Y")
    requester = item_data.get("line_sender_name") or item_data.get("requester") or "ผู้ขอเบิกเงิน"
    merchant = item_data.get("merchant") or item_data.get("vendor") or "-"
    details = item_data.get("details") or item_data.get("summary") or "ค่าใช้จ่ายทั่วไป"
    net_amount = float(item_data.get("net_amount") or 0.0)

    pdf.set_thai_font(size=11)
    pdf.cell(100, 7, text=f"เลขที่เอกสาร: {ref_id}", ln=0)
    pdf.cell(90, 7, text=f"วันที่: {date_str}", ln=1)
    pdf.cell(100, 7, text=f"ผู้ขอเบิกเงิน: {requester}", ln=0)
    pdf.cell(90, 7, text=f"ผู้จ่ายเงิน / สถานที่: {merchant}", ln=1)
    pdf.ln(5)

    # Table Header
    pdf.set_fill_color(240, 240, 240)
    pdf.set_thai_font(size=10)
    pdf.cell(15, 8, text="ลำดับ", border=1, align="C", fill=True)
    pdf.cell(115, 8, text="รายการ / วัตถุประสงค์ในการจ่าย", border=1, align="C", fill=True)
    pdf.cell(60, 8, text="จำนวนเงิน (บาท)", border=1, align="C", fill=True)
    pdf.ln(8)

    # Table Content Row
    pdf.cell(15, 10, text="1", border=1, align="C")
    pdf.cell(115, 10, text=details[:60], border=1, align="L")
    pdf.cell(60, 10, text=f"{net_amount:,.2f}", border=1, align="R")
    pdf.ln(10)

    # Total Row
    pdf.cell(130, 9, text="รวมเงินทั้งสิ้น (Total Net Amount)", border=1, align="R", fill=True)
    pdf.cell(60, 9, text=f"฿{net_amount:,.2f}", border=1, align="R", fill=True)
    pdf.ln(12)

    # Declaration & Certification Statement
    pdf.set_thai_font(size=10)
    declaration_text = (
        "ข้าพเจ้าขอรับรองว่า รายจ่ายข้างต้นนี้ ได้จ่ายไปในงานขององค์กร/บริษัทโดยแท้ "
        "และไม่สามารถเรียกใบเสร็จรับเงินจากผู้รับเงินได้ จึงขอใช้ใบรับรองนี้เป็นหลักฐานในการเบิกจ่ายเงิน"
    )
    pdf.multi_cell(0, 6, text=declaration_text)
    pdf.ln(15)

    # Signatures
    pdf.cell(90, 6, text="ลงชื่อ.......................................................... (ผู้รับเงิน/ผู้เบิก)", ln=0)
    pdf.cell(100, 6, text="ลงชื่อ.......................................................... (ผู้อนุมัติ)", ln=1)
    pdf.cell(90, 6, text=f"      ({requester})", ln=0)
    pdf.cell(100, 6, text="      (..........................................................)", ln=1)
    pdf.cell(90, 6, text=f"วันที่ {date_str}", ln=0)
    pdf.cell(100, 6, text=f"วันที่ {date_str}", ln=1)

    pdf.output(str(file_path))
    return str(file_path.resolve()), filename


def generate_batch_payment_voucher_pdf(items: list[dict], org_name: str = "องค์กรของคุณ") -> tuple[str, str]:
    """
    Generates a Payment Voucher (ใบสำคัญจ่าย) PDF combining multiple expense items.
    Returns (abs_file_path, filename).
    """
    downloads_dir = Path("static/downloads")
    downloads_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pv_no = f"PV-{timestamp}"
    filename = f"Payment_Voucher_{pv_no}.pdf"
    file_path = downloads_dir / filename

    pdf = ThaiPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header Title
    pdf.set_thai_font(size=20)
    pdf.cell(0, 10, text="ใบสำคัญจ่าย (Payment Voucher)", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_thai_font(size=12)
    pdf.cell(0, 8, text=org_name, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    # Voucher Info Box
    date_str = datetime.now().strftime("%d/%m/%Y")
    pdf.set_thai_font(size=10)
    pdf.cell(100, 6, text=f"เลขที่ใบสำคัญจ่าย: {pv_no}", ln=0)
    pdf.cell(90, 6, text=f"วันที่ออกเอกสาร: {date_str}", ln=1)
    pdf.cell(100, 6, text=f"จำนวนรายการย่อย: {len(items)} รายการ", ln=0)
    pdf.cell(90, 6, text="ชำระโดย: โอนเงิน / เงินสด", ln=1)
    pdf.ln(5)

    # Table Header
    pdf.set_fill_color(230, 235, 245)
    pdf.set_thai_font(size=9)
    pdf.cell(12, 8, text="ลำดับ", border=1, align="C", fill=True)
    pdf.cell(24, 8, text="วันที่", border=1, align="C", fill=True)
    pdf.cell(50, 8, text="ผู้ส่ง/ร้านค้า", border=1, align="C", fill=True)
    pdf.cell(54, 8, text="รายละเอียด", border=1, align="C", fill=True)
    pdf.cell(25, 8, text="เลขที่อ้างอิง", border=1, align="C", fill=True)
    pdf.cell(25, 8, text="จำนวนเงิน (฿)", border=1, align="C", fill=True)
    pdf.ln(8)

    # Totals accumulators
    total_gross = 0.0
    total_vat = 0.0
    total_wht = 0.0
    total_net = 0.0

    pdf.set_thai_font(size=8)
    for idx, item in enumerate(items, 1):
        d_val = str(item.get("date") or "-")
        m_val = str(item.get("merchant") or item.get("vendor") or "-")[:24]
        det_val = str(item.get("details") or item.get("summary") or "-")[:28]
        ref_val = str(item.get("ref_number") or "-")[:12]
        
        net_amt = float(item.get("net_amount") or 0.0)
        gross_amt = float(item.get("gross_amount") or net_amt)
        vat_amt = float(item.get("vat_amount") or 0.0)
        wht_amt = float(item.get("wht_amount") or 0.0)

        total_gross += gross_amt
        total_vat += vat_amt
        total_wht += wht_amt
        total_net += net_amt

        pdf.cell(12, 7, text=str(idx), border=1, align="C")
        pdf.cell(24, 7, text=d_val, border=1, align="C")
        pdf.cell(50, 7, text=m_val, border=1, align="L")
        pdf.cell(54, 7, text=det_val, border=1, align="L")
        pdf.cell(25, 7, text=ref_val, border=1, align="C")
        pdf.cell(25, 7, text=f"{net_amt:,.2f}", border=1, align="R")
        pdf.ln(7)

    # Summary Section
    pdf.ln(3)
    pdf.set_thai_font(size=9)
    pdf.cell(140, 6, text="ยอดรวมก่อนภาษี (Gross Amount):", align="R")
    pdf.cell(50, 6, text=f"฿{total_gross:,.2f}", align="R")
    pdf.ln(6)

    pdf.cell(140, 6, text="ภาษีมูลค่าเพิ่ม (VAT 7%):", align="R")
    pdf.cell(50, 6, text=f"฿{total_vat:,.2f}", align="R")
    pdf.ln(6)

    pdf.cell(140, 6, text="ภาษีหัก ณ ที่จ่าย (WHT):", align="R")
    pdf.cell(50, 6, text=f"- ฿{total_wht:,.2f}", align="R")
    pdf.ln(6)

    pdf.set_fill_color(240, 240, 240)
    pdf.set_thai_font(size=10)
    pdf.cell(140, 8, text="ยอดชำระสุทธิทั้งสิ้น (Net Payment Total):", border=1, align="R", fill=True)
    pdf.cell(50, 8, text=f"฿{total_net:,.2f}", border=1, align="R", fill=True)
    pdf.ln(12)

    # Signatures
    pdf.set_thai_font(size=9)
    pdf.cell(63, 6, text="ผู้จัดทำเอกสาร (Prepared By)", align="C")
    pdf.cell(64, 6, text="ผู้ตรวจอนุมัติ (Approved By)", align="C")
    pdf.cell(63, 6, text="ผู้รับเงิน / ผู้เบิก (Paid To)", align="C")
    pdf.ln(12)

    pdf.cell(63, 6, text="ลงชื่อ.........................................", align="C")
    pdf.cell(64, 6, text="ลงชื่อ.........................................", align="C")
    pdf.cell(63, 6, text="ลงชื่อ.........................................", align="C")
    pdf.ln(5)
    pdf.cell(63, 6, text=f"วันที่ {date_str}", align="C")
    pdf.cell(64, 6, text=f"วันที่ {date_str}", align="C")
    pdf.cell(63, 6, text=f"วันที่ {date_str}", align="C")

    pdf.output(str(file_path))
    return str(file_path.resolve()), filename
