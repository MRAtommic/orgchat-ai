import os
import requests
import json
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from dotenv import load_dotenv

# Load env variables
load_dotenv()
LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

if not LINE_ACCESS_TOKEN:
    print("❌ Error: LINE_CHANNEL_ACCESS_TOKEN not found in .env")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def create_rich_menu_image():
    """Generate a premium rich menu image (2500x843) using Pillow."""
    print("🎨 Generating Rich Menu Image...")
    width, height = 2500, 843
    # Create base image with gradient-like dark background
    img = Image.new("RGB", (width, height), color="#0f172a")
    draw = ImageDraw.Draw(img)
    
    # Draw button dividers
    draw.line([(833, 0), (833, height)], fill="#1e293b", width=5)
    draw.line([(1666, 0), (1666, height)], fill="#1e293b", width=5)
    
    # Try to load a font, fallback to default if not available
    try:
        # For Windows, Tahoma or Segoe UI usually support Thai
        font_path = "C:\\Windows\\Fonts\\tahoma.ttf"
        font_large = ImageFont.truetype(font_path, 80)
        font_emoji = ImageFont.truetype("C:\\Windows\\Fonts\\seguiemj.ttf", 100) # Emoji font
    except Exception:
        font_large = ImageFont.load_default()
        font_emoji = font_large

    # Helper to draw centered text
    def draw_button(x_center, text, icon, color):
        try:
            draw.text((x_center - 100, 300), icon, font=font_emoji, fill=color, anchor="mm")
            draw.text((x_center, 500), text, font=font_large, fill="#f8fafc", anchor="mm")
        except:
            draw.text((x_center, 421), f"{icon} {text}", fill="#ffffff", anchor="mm")

    draw_button(416, "ดูแดชบอร์ดยอดวิว", "📊", "#6366f1")
    draw_button(1250, "สถานะโฟลเดอร์", "📁", "#10b981")
    draw_button(2083, "วิธีใช้งานระบบ", "❓", "#ec4899")
    
    # Add a premium top border
    draw.rectangle([(0, 0), (width, 15)], fill="#6366f1")
    
    img_path = "rich_menu_bg.png"
    img.save(img_path)
    print(f"✅ Image saved to {img_path}")
    return img_path

def setup_rich_menu():
    print("🚀 Starting Rich Menu Setup...")
    
    # 1. Define Rich Menu Object
    rich_menu_obj = {
        "size": {"width": 2500, "height": 843},
        "selected": True,
        "name": "WebAI Premium Menu",
        "chatBarText": "เมนูคำสั่ง",
        "areas": [
            {
                "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
                "action": {
                    "type": "uri",
                    "uri": "https://openchat.sbs/dashboard"
                }
            },
            {
                "bounds": {"x": 834, "y": 0, "width": 833, "height": 843},
                "action": {
                    "type": "message",
                    "text": "สถานะโฟลเดอร์"
                }
            },
            {
                "bounds": {"x": 1667, "y": 0, "width": 833, "height": 843},
                "action": {
                    "type": "message",
                    "text": "วิธีใช้งาน"
                }
            }
        ]
    }

    # 2. Create Rich Menu
    print("📝 Creating Rich Menu object on LINE...")
    res = requests.post("https://api.line.me/v2/bot/richmenu", headers=HEADERS, json=rich_menu_obj)
    if res.status_code != 200:
        print(f"❌ Failed to create menu: {res.text}")
        return
    rich_menu_id = res.json().get("richMenuId")
    print(f"✅ Rich Menu Created! ID: {rich_menu_id}")

    # 3. Generate and Upload Image
    img_path = create_rich_menu_image()
    print("📤 Uploading image to LINE...")
    with open(img_path, "rb") as f:
        img_headers = {
            "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
            "Content-Type": "image/png"
        }
        res_img = requests.post(
            f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content",
            headers=img_headers,
            data=f
        )
        if res_img.status_code != 200:
            print(f"❌ Failed to upload image: {res_img.text}")
            return
    print("✅ Image uploaded successfully!")

    # 4. Set as Default Rich Menu
    print("⭐ Setting as default menu for all users...")
    res_def = requests.post(f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}", headers=HEADERS)
    if res_def.status_code == 200:
        print("🎉 SUCCESS! Rich menu is now live on your LINE Official Account.")
    else:
        print(f"❌ Failed to set default: {res_def.text}")

if __name__ == "__main__":
    setup_rich_menu()
