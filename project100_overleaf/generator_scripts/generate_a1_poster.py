import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image

def generate_a1_poster():
    output_jpeg = r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\การบ้าน4\AUCC2027_OrgChat_AI_Poster_A1.jpeg'
    
    # A1 Portrait dimensions in inches at 200 DPI (approx 4678 x 6622 px, crisp & high resolution)
    fig_w = 23.39
    fig_h = 33.11
    dpi = 200
    
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    font_name = 'Leelawadee UI'
    plt.rcParams['font.sans-serif'] = [font_name, 'Tahoma', 'Arial']
    
    # Colors
    c_primary = '#0F172A'    # Deep Navy Slate
    c_brand = '#1E40AF'      # Vibrant Royal Blue
    c_accent = '#0EA5E9'     # Cyan Accent
    c_card_bg = '#FFFFFF'
    c_card_border = '#CBD5E1'
    c_text_dark = '#1E293B'
    c_text_muted = '#475569'
    
    # --- 1. HEADER BANNER ---
    header_rect = patches.FancyBboxPatch((2, 85.5), 96, 13.0, boxstyle="round,pad=0.5", 
                                        facecolor=c_primary, edgecolor=c_brand, lw=2.5)
    ax.add_patch(header_rect)
    
    # Conference Tag
    ax.text(50, 96.8, "The 15th Asia Undergraduate Conference on Computing (AUCC 2027)", 
            color='#38BDF8', fontsize=16, weight='bold', ha='center', va='center', fontname=font_name)
    
    # Thai Title
    ax.text(50, 93.8, "การพัฒนาระบบปัญญาประดิษฐ์แชทบอทสำหรับองค์กร กรณีศึกษา บริษัท ฮาร์ทวอมมิ่ง จำกัด", 
            color='#FFFFFF', fontsize=22, weight='bold', ha='center', va='center', fontname=font_name)
    
    # English Title
    ax.text(50, 91.0, "Development of an Artificial Intelligence Chatbot for Organization: A Case Study of Heartwarming Co., Ltd.", 
            color='#E2E8F0', fontsize=14, weight='bold', ha='center', va='center', fontname=font_name)
    
    # Authors & Advisor
    ax.text(50, 88.0, "คณะผู้วิจัย: นายธนากร ธนบวรพล  |  นายวีรภัทร ชื่นชอบ   •   อาจารย์ที่ปรึกษา: อาจารย์ ดร.ศิรินทรา แว่วศรี", 
            color='#FDE047', fontsize=13, weight='bold', ha='center', va='center', fontname=font_name)
    ax.text(50, 86.4, "สาขาวิชาเทคโนโลยีสารสนเทศ คณะเทคโนโลยีและการจัดการอุตสาหกรรม มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ", 
            color='#94A3B8', fontsize=11, ha='center', va='center', fontname=font_name)

    def draw_section_card(x, y, w, h, title):
        card = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4", 
                                      facecolor=c_card_bg, edgecolor=c_card_border, lw=1.5)
        ax.add_patch(card)
        # Header strip
        strip = patches.FancyBboxPatch((x, y + h - 2.6), w, 2.6, boxstyle="round,pad=0.2", 
                                       facecolor='#F1F5F9', edgecolor='none')
        ax.add_patch(strip)
        # Accent bar
        bar = patches.Rectangle((x, y + h - 2.6), 1.2, 2.6, facecolor=c_brand, edgecolor='none')
        ax.add_patch(bar)
        # Title text
        ax.text(x + 2.2, y + h - 1.3, title, color=c_primary, fontsize=14.5, weight='bold', 
                va='center', ha='left', fontname=font_name)

    # --- LEFT COLUMN (x: 2 to 49, width: 47) ---
    # 2. บทนำและที่มา (Background & Problem)
    draw_section_card(2, 69.5, 47, 15.0, "1. บทนำและที่มาของปัญหา (Background & Problem)")
    intro_txt = (
        "- ปัญหาเดิมขององค์กร (Pain Points):\n"
        "   1) ข้อมูลคู่มือสินค้ากระจัดกระจาย ทำให้ค้นหาข้อมูลตอบลูกค้าล่าช้าเฉลี่ย 3-5 นาที/คำถาม\n"
        "   2) การบันทึกบัญชีรายรับจากสลิปโอนเงินใช้คนกรอกมือ เสี่ยงต่อข้อผิดพลาดและใช้เวลานาน\n"
        "   3) การยื่นและอนุมัติวันลายังใช้แบบฟอร์มเอกสาร ขาดระบบตรวจสอบโควตาแบบเรียลไทม์\n"
        "- แนวทางแก้ไข (Solution):\n"
        "   พัฒนา 'OrgChat AI' ผสาน LINE OA + Web Management + AI RAG (Gemini) + OCR อัตโนมัติ"
    )
    ax.text(3.5, 80.2, intro_txt, color=c_text_dark, fontsize=10.8, linespacing=1.6, va='top', ha='left', fontname=font_name)

    # 3. วัตถุประสงค์ (Objectives)
    draw_section_card(2, 53.5, 47, 14.8, "2. วัตถุประสงค์ของโครงการ (Objectives)")
    obj_txt = (
        "1. วิเคราะห์และพัฒนาระบบ AI Chatbot องค์กรผ่าน LINE OA และเว็บแอปพลิเคชัน\n"
        "2. พัฒนาระบบคลังความรู้อัจฉริยะ (RAG) สืบค้นคู่มือสินค้าด้วย Gemini + ChromaDB\n"
        "3. พัฒนาระบบสแกนสลิป OCR และบันทึกลง Google Sheets / Drive อัตโนมัติ\n"
        "4. พัฒนาระบบบริหารงานบุคคลและแจ้งเตือนอนุมัติวันลาผ่าน LINE Flex Message\n"
        "5. ประเมินประสิทธิภาพระบบและความพึงพอใจของผู้ใช้งานจริง (บริษัท ฮาร์ทวอมมิ่ง จำกัด)"
    )
    ax.text(3.5, 64.2, obj_txt, color=c_text_dark, fontsize=10.8, linespacing=1.6, va='top', ha='left', fontname=font_name)

    # 4. สถาปัตยกรรมระบบ (System Architecture)
    draw_section_card(2, 23.5, 47, 28.8, "3. สถาปัตยกรรมระบบ (System Architecture)")
    arch_img_path = r'scratch\thesis_exact_figs\p_331_image2.png'
    if os.path.exists(arch_img_path):
        img_arch = Image.open(arch_img_path)
        ax.imshow(img_arch, extent=[3.5, 47.5, 24.5, 48.5], aspect='auto', zorder=5)

    # 5. ฟังก์ชันการทำงาน 5 โมดูลหลัก (5 Core Modules)
    draw_section_card(2, 2, 47, 20.2, "4. โมดูลการทำงานหลัก (Core System Modules)")
    mod_txt = (
        "- M1 (Auth & RBAC): ยืนยันตัวตน, จัดการสิทธิ์ 3 ระดับ (Admin, Manager, Employee), LINE Login\n"
        "- M2 (AI RAG Chatbot): ค้นคืนเอกสารคู่มือสินค้าและนโยบายใน ChromaDB ตอบผ่าน LINE\n"
        "- M3 (OCR Bookkeeping): ตรวจจับสลิปโอนเงิน 5 ธนาคาร สกัดยอด วันที่ บันทึก Sheets/Drive\n"
        "- M4 (HR Leave Management): ยื่นคำขอลาผ่าน LINE Rich Menu และส่งแจ้งเตือนอนุมัติผ่าน Flex Msg\n"
        "- M5 (Admin Dashboard & Logs): กราฟสรุปสถิติ รายรับ-รายจ่าย รายการลา และ Audit Trail"
    )
    ax.text(3.5, 18.5, mod_txt, color=c_text_dark, fontsize=10.8, linespacing=1.6, va='top', ha='left', fontname=font_name)

    # --- RIGHT COLUMN (x: 51 to 98, width: 47) ---
    # 6. หน้าจอส่วนติดต่อผู้ใช้จริง (User Interface Highlights)
    draw_section_card(51, 48.5, 47, 36.0, "5. หน้าจอส่วนติดต่อผู้ใช้จริง (System Interfaces)")
    
    # 3 Screenshots side by side or stacked
    # UI 1: LINE RAG
    rag_img_path = r'scratch\thesis_exact_figs\p_469_image13.png'
    if os.path.exists(rag_img_path):
        img_rag = Image.open(rag_img_path)
        ax.imshow(img_rag, extent=[52.5, 73.5, 60.5, 80.5], aspect='auto', zorder=5)
        ax.text(63.0, 59.2, "(ก) ถามตอบคู่มือสินค้า AI RAG ผ่าน LINE", fontsize=9.5, weight='bold', ha='center', color=c_primary, fontname=font_name)

    # UI 2: Login Web
    login_img_path = r'scratch\thesis_exact_figs\p_456_image12.png'
    if os.path.exists(login_img_path):
        img_login = Image.open(login_img_path)
        ax.imshow(img_login, extent=[75.5, 96.5, 60.5, 80.5], aspect='auto', zorder=5)
        ax.text(86.0, 59.2, "(ข) หน้าเข้าสู่ระบบและ LINE OAuth", fontsize=9.5, weight='bold', ha='center', color=c_primary, fontname=font_name)

    # UI 3: Admin Dashboard
    dash_img_path = r'scratch\thesis_exact_figs\p_478_image14.png'
    if os.path.exists(dash_img_path):
        img_dash = Image.open(dash_img_path)
        ax.imshow(img_dash, extent=[53.0, 96.0, 50.2, 58.0], aspect='auto', zorder=5)
        ax.text(74.5, 49.2, "(ค) แผงควบคุมผู้บริหาร สรุปสถิติและการเงินภาพรวม", fontsize=9.5, weight='bold', ha='center', color=c_primary, fontname=font_name)

    # 7. ผลการทดสอบและประเมินผล (Testing & Evaluation Results)
    draw_section_card(51, 16.5, 47, 30.8, "6. ผลการทดสอบและประเมินผล (Results & Evaluation)")
    
    # Metric Badges
    b1 = patches.FancyBboxPatch((53, 38.5), 13.5, 5.5, boxstyle="round,pad=0.3", facecolor='#EFF6FF', edgecolor='#3B82F6', lw=1.5)
    ax.add_patch(b1)
    ax.text(59.75, 42.2, "100%", color='#1D4ED8', fontsize=18, weight='bold', ha='center', fontname=font_name)
    ax.text(59.75, 39.5, "Functional Testing\n(15 Test Cases)", color=c_text_muted, fontsize=9, weight='bold', ha='center', fontname=font_name)

    b2 = patches.FancyBboxPatch((67.75, 38.5), 13.5, 5.5, boxstyle="round,pad=0.3", facecolor='#F0FDF4', edgecolor='#22C55E', lw=1.5)
    ax.add_patch(b2)
    ax.text(74.5, 42.2, "96.4%", color='#15803D', fontsize=18, weight='bold', ha='center', fontname=font_name)
    ax.text(74.5, 39.5, "OCR Slip Accuracy\n(50 Slips จาก 5 ธนาคาร)", color=c_text_muted, fontsize=9, weight='bold', ha='center', fontname=font_name)

    b3 = patches.FancyBboxPatch((82.5, 38.5), 13.5, 5.5, boxstyle="round,pad=0.3", facecolor='#FAF5FF', edgecolor='#A855F7', lw=1.5)
    ax.add_patch(b3)
    ax.text(89.25, 42.2, "94.8%", color='#7E22CE', fontsize=18, weight='bold', ha='center', fontname=font_name)
    ax.text(89.25, 39.5, "RAG Fact Accuracy\n(50 Queries, 1.84s Avg)", color=c_text_muted, fontsize=9, weight='bold', ha='center', fontname=font_name)

    # UAT Table summary
    uat_txt = (
        "- ผลการประเมินความพึงพอใจจากผู้ใช้งานจริง (N = 20 คน, มาตราส่วน 5 ระดับ):\n"
        "   1. ด้านความถูกต้องแม่นยำของ AI RAG:  Mean = 4.70 (S.D. = 0.46) [มากที่สุด]\n"
        "   2. ด้านความสะดวกรวดเร็วผ่าน LINE:       Mean = 4.75 (S.D. = 0.44) [มากที่สุด]\n"
        "   3. ด้านระบบจัดการงานบุคคลและวันลา:      Mean = 4.60 (S.D. = 0.50) [มากที่สุด]\n"
        "   4. ด้านความง่ายของแผงควบคุมผู้บริหาร:      Mean = 4.55 (S.D. = 0.51) [มากที่สุด]\n"
        "   สรุปภาพรวมความพึงพอใจทุกด้าน:          Mean = 4.65 (S.D. = 0.48) [ระดับมากที่สุด]"
    )
    ax.text(53, 36.5, uat_txt, color=c_text_dark, fontsize=10.2, linespacing=1.5, va='top', ha='left', fontname=font_name)

    # 8. สรุปผลและประโยชน์ที่ได้รับ (Conclusion & Benefits)
    draw_section_card(51, 2, 47, 13.5, "7. สรุปผลและประโยชน์ที่ได้รับ (Conclusion & Impact)")
    conc_txt = (
        "- ลดเวลาการค้นหาข้อมูลคู่มือสินค้าจาก 3-5 นาที เหลือเพียง 1-2 วินาที\n"
        "- บันทึกบัญชีสลิปโอนเงินอัตโนมัติ ลดความผิดพลาดของมนุษย์ได้ 100%\n"
        "- บริหารจัดการวันลาแบบ Real-time โปร่งใส แจ้งเตือนตรงผ่าน LINE OA\n"
        "- เพิ่มผลิตภาพและความคล่องตัวในการดำเนินงานขององค์กรได้อย่างมีประสิทธิภาพ"
    )
    ax.text(53, 12.0, conc_txt, color='#065F46', fontsize=10.8, weight='bold', linespacing=1.6, va='top', ha='left', fontname=font_name)

    # Footer note
    ax.text(50, 0.8, "ภาควิชาเทคโนโลยีสารสนเทศ คณะเทคโนโลยีและการจัดการอุตสาหกรรม มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ (KMUTNB)", 
            color='#94A3B8', fontsize=10, ha='center', va='center', fontname=font_name)

    plt.tight_layout()
    plt.savefig(output_jpeg, format='jpeg', dpi=dpi, bbox_inches='tight')
    plt.close()
    print(f"Successfully generated clean A1 Poster: {output_jpeg}")

if __name__ == "__main__":
    generate_a1_poster()
