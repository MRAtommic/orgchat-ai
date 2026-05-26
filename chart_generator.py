import os
import uuid
from PIL import Image, ImageDraw, ImageFont

def generate_monthly_expense_chart(data, output_dir="uploads/social_feed"):
    """
    Generates a beautiful, modern donut chart image from the given expense data.
    Saves the image to the specified output directory and returns the filename.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"expense_chart_{uuid.uuid4().hex[:10]}.png"
    output_path = os.path.join(output_dir, filename)

    # Dimensions
    width, height = 800, 500
    bg_color = (248, 250, 252) # #f8fafc (slate-50)
    
    # Create image
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try to load Tahoma/Arial font for Thai/English support, fall back to default
    font_title = None
    font_subtitle = None
    font_bold = None
    font_total_label = None
    font_legend = None
    
    # Common system font paths
    windows_fonts = ["tahoma.ttf", "tahomabd.ttf", "arial.ttf", "arialbd.ttf", "angsana.ttf", "cordia.ttf"]
    linux_fonts = ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "FreeSans.ttf"]
    
    for fn in windows_fonts + linux_fonts:
        try:
            # Check if bold version is available
            is_bold = "bd" in fn or "Bold" in fn
            font_title = ImageFont.truetype(fn, 22)
            font_subtitle = ImageFont.truetype(fn, 14)
            font_bold = ImageFont.truetype(fn if is_bold else "tahomabd.ttf" if fn == "tahoma.ttf" else fn, 24)
            font_total_label = ImageFont.truetype(fn, 12)
            font_legend = ImageFont.truetype(fn, 15)
            break
        except IOError:
            continue
            
    if font_title is None:
        default = ImageFont.load_default()
        font_title = default
        font_subtitle = default
        font_bold = default
        font_total_label = default
        font_legend = default

    # Modern curated color palette
    colors = [
        (13, 148, 136),   # Teal
        (79, 70, 229),    # Indigo
        (124, 58, 237),   # Violet
        (225, 29, 72),    # Rose
        (217, 119, 6),    # Amber
        (5, 150, 105),    # Emerald
        (2, 132, 199),    # Sky Blue
        (190, 18, 60),    # Crimson
    ]
    
    # Filter out zero or negative values
    data = {k: v for k, v in data.items() if v > 0}
    if not data:
        # Draw fallback empty state
        draw.text((width//2, height//2), "ไม่มีข้อมูลรายจ่ายสำหรับเดือนนี้ค่ะ", fill=(100, 116, 139), font=font_title, anchor="mm")
        img.save(output_path, "PNG")
        return filename

    total = sum(data.values())
    
    # Donut Chart parameters
    cx, cy = 250, 250
    radius = 160
    inner_radius = 100
    box = [cx - radius, cy - radius, cx + radius, cy + radius]
    inner_box = [cx - inner_radius, cy - inner_radius, cx + inner_radius, cy + inner_radius]
    
    start_angle = -90
    
    # Sort data descending to make chart look clean
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    
    for i, (category, amount) in enumerate(sorted_data):
        color = colors[i % len(colors)]
        percentage = (amount / total) * 100
        angle = (percentage / 100) * 360
        
        # Draw slice
        end_angle = start_angle + angle
        draw.pieslice(box, start_angle=start_angle, end_angle=end_angle, fill=color)
        start_angle = end_angle

    # Draw center hole (Donut)
    draw.ellipse(inner_box, fill=bg_color)
    
    # Draw total text in center
    draw.text((cx, cy - 25), "ยอดรวมทั้งหมด", fill=(100, 116, 139), font=font_total_label, anchor="mm")
    total_str = f"{total:,.2f}"
    if total_str.endswith(".00"):
        total_str = total_str[:-3]
    draw.text((cx, cy + 5), total_str, fill=(15, 23, 42), font=font_bold, anchor="mm")
    draw.text((cx, cy + 30), "บาท", fill=(100, 116, 139), font=font_total_label, anchor="mm")
    
    # Draw Title on the right side
    draw.text((450, 50), "📊 รายงานสรุปรายจ่ายเดือนนี้", fill=(15, 23, 42), font=font_title)
    draw.text((450, 85), f"แยกตามหมวดหมู่ (ยอดรวม {total_str} บาท)", fill=(100, 116, 139), font=font_subtitle)
    
    # Draw Legend
    start_y = 130
    row_height = 40
    
    # Draw up to 8 categories to avoid overflow
    for i, (category, amount) in enumerate(sorted_data[:8]):
        color = colors[i % len(colors)]
        percentage = (amount / total) * 100
        y = start_y + i * row_height
        
        # Color dot/square
        draw.rounded_rectangle([450, y + 4, 466, y + 20], radius=4, fill=color)
        
        # Category label
        pct_str = f"{percentage:.1f}%"
        amt_str = f"{amount:,.2f}"
        if amt_str.endswith(".00"):
            amt_str = amt_str[:-3]
            
        draw.text((480, y), f"{category}", fill=(15, 23, 42), font=font_legend)
        draw.text((480, y + 18), f"{amt_str} บาท ({pct_str})", fill=(100, 116, 139), font=font_subtitle)
        
    # Draw brand at bottom right
    draw.text((width - 30, height - 30), "สร้างโดย น้องพั้นช์ ✨", fill=(148, 163, 184), font=font_subtitle, anchor="rb")
    
    # Save image
    img.save(output_path, "PNG")
    return filename
