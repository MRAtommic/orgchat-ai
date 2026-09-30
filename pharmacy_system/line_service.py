"""
LINE Bot Messaging Service for Pharmacy System
Handles text commands ('พารา 2'), photo OCR, and sends rich Medical Flex Messages.
"""

import re
import requests
import json
import logging
from config import Config
import database
from google_sync import google_sync
from ocr_service import parse_drug_from_image

logger = logging.getLogger("pharmacy_line")

class PharmacyLineBot:
    def __init__(self):
        self.access_token = Config.LINE_CHANNEL_ACCESS_TOKEN
        self.channel_secret = Config.LINE_CHANNEL_SECRET
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

    def reply_message(self, reply_token, messages):
        """Send reply message to LINE user."""
        if not self.access_token:
            logger.warning("LINE_CHANNEL_ACCESS_TOKEN not configured.")
            return False

        url = "https://api.line.me/v2/bot/message/reply"
        payload = {
            "replyToken": reply_token,
            "messages": messages if isinstance(messages, list) else [messages]
        }
        try:
            res = requests.post(url, headers=self.headers, json=payload, timeout=10)
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Error sending LINE reply: {e}")
            return False

    def get_message_content(self, message_id):
        """Download binary content (image/audio) from LINE."""
        url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
        try:
            res = requests.get(url, headers={"Authorization": f"Bearer {self.access_token}"}, timeout=15)
            if res.status_code == 200:
                return res.content
        except Exception as e:
            logger.error(f"Error downloading LINE content: {e}")
        return None

    def handle_webhook_event(self, event):
        """Process a single LINE event."""
        reply_token = event.get("replyToken")
        source = event.get("source", {})
        user_id = source.get("userId", "unknown")
        user_name = "LINE User"

        message = event.get("message", {})
        msg_type = message.get("type")

        if msg_type == "text":
            text = message.get("text", "").strip()
            self._handle_text_message(reply_token, text, user_name)

        elif msg_type == "image":
            msg_id = message.get("id")
            self._handle_image_message(reply_token, msg_id, user_name)

    def _handle_text_message(self, reply_token, text, user_name):
        """Parse text for deduction, stock query, or menu."""
        lower_text = text.lower()

        # 1. Menu / Help
        if lower_text in ["เมนู", "help", "คำสั่ง", "?"]:
            flex = self._create_menu_flex()
            self.reply_message(reply_token, flex)
            return

        # 2. Check stock list or low stock
        if lower_text in ["เช็คสต็อก", "สต็อก", "stock"]:
            flex = self._create_stock_summary_flex()
            self.reply_message(reply_token, flex)
            return

        if lower_text in ["ยาหมด", "เตือน", "ใกล้หมด"]:
            low_drugs = database.get_all_drugs(low_stock_only=True)
            if not low_drugs:
                self.reply_message(reply_token, {"type": "text", "text": "✅ ขณะนี้สต็อกยาทุกรายการอยู่ในเกณฑ์ปกติ ไม่มีรายการยาที่ต้องสั่งซื้อด่วนค่ะ"})
            else:
                msg = "⚠️ รายการยาที่ใกล้หมดสต็อก:\n"
                for d in low_drugs[:10]:
                    msg += f"• {d['name']}: เหลือ {d['stock_qty']} {d['unit']} (จุดเตือน {d['min_threshold']})\n"
                self.reply_message(reply_token, {"type": "text", "text": msg.strip()})
            return

        # 3. Deduction Pattern: [ชื่อยา/รหัสยา] [จำนวน] (e.g., 'พารา 2' หรือ 'Amox 1')
        match = re.match(r"^(.+?)\s*([xX*+-]?)\s*(\d+)\s*(?:เม็ด|แคปซูล|ขวด|แผง|กล่อง|ซอง)?$", text)
        if match:
            drug_query = match.group(1).strip()
            qty = int(match.group(3))

            drug = database.find_drug_by_name_or_alias(drug_query)
            if not drug:
                self.reply_message(reply_token, {
                    "type": "text",
                    "text": f"❌ ไม่พบยาชื่อ '{drug_query}' ในระบบคลังยาค่ะ\n\n💡 พิมพ์ 'เช็คสต็อก' เพื่อดูรายชื่อยาทั้งหมด หรือสแกน QR Code เพื่อตัดสต็อกได้ค่ะ"
                })
                return

            # Deduct stock
            success, result = database.deduct_stock(
                drug["id"],
                qty,
                channel="LINE_TEXT",
                dispensed_by=user_name,
                notes=f"ตัดผ่านข้อความ LINE: '{text}'"
            )

            if success:
                # Sync to Google Sheets
                google_sync.append_dispensing_log(result)
                google_sync.sync_all_drugs_to_sheet(database.get_all_drugs())

                flex = self._create_deduct_success_flex(result)
                self.reply_message(reply_token, flex)
            else:
                self.reply_message(reply_token, {"type": "text", "text": f"⚠️ ไม่สามารถตัดสต็อกได้: {result}"})
            return

        # Query single drug (e.g., 'ค้นหา พารา')
        drug = database.find_drug_by_name_or_alias(text)
        if drug:
            flex = self._create_drug_card_flex(drug)
            self.reply_message(reply_token, flex)
            return

        # Fallback helpful response
        self.reply_message(reply_token, {
            "type": "text",
            "text": f"🏥 ระบบคลังยาได้รับข้อความ: '{text}'\n\nต้องการตัดสต็อกยา กรุณาพิมพ์ [ชื่อยา] ตามด้วย [จำนวน]\nเช่น:\n👉 พารา 2\n👉 Amoxicillin 1\n\nหรือส่งรูปภาพฉลากยา/QR Code เข้ามาได้เลยค่ะ"
        })

    def _handle_image_message(self, reply_token, msg_id, user_name):
        """Process uploaded image (prescription / QR / drug bag)."""
        image_bytes = self.get_message_content(msg_id)
        if not image_bytes:
            self.reply_message(reply_token, {"type": "text", "text": "❌ ไม่สามารถดาวน์โหลดรูปภาพจาก LINE ได้ กรุณาลองใหม่อีกครั้งค่ะ"})
            return

        # Run OCR & QR analysis
        analysis = parse_drug_from_image(image_bytes)
        
        if not analysis.get("success") or not analysis.get("drug"):
            self.reply_message(reply_token, {
                "type": "text",
                "text": f"🔍 {analysis.get('message', 'ไม่สามารถระบุชื่อยาจากภาพได้')}\n\nกรุณาพิมพ์ชื่อยาและจำนวนด้วยข้อความ เช่น 'พารา 2' เพื่อตัดสต็อกแทนค่ะ"
            })
            return

        drug = analysis["drug"]
        qty = analysis.get("quantity", 1)
        method = analysis.get("method", "OCR")

        # Upload image to Google Drive dedicated folder
        drive_file_id, drive_file_link = google_sync.upload_image_to_drive(
            image_bytes,
            f"{drug['code']}_{msg_id}.jpg",
            mime_type="image/jpeg"
        )

        # Deduct stock
        success, result = database.deduct_stock(
            drug["id"],
            qty,
            channel=f"LINE_{method}",
            dispensed_by=user_name,
            drive_file_id=drive_file_id,
            drive_file_link=drive_file_link,
            notes=f"ตัดจากภาพ ({method}): {analysis.get('message')}"
        )

        if success:
            # Sync to Google Sheets
            google_sync.append_dispensing_log(result)
            google_sync.sync_all_drugs_to_sheet(database.get_all_drugs())

            flex = self._create_deduct_success_flex(result, method=method, drive_link=drive_file_link)
            self.reply_message(reply_token, flex)
        else:
            self.reply_message(reply_token, {"type": "text", "text": f"⚠️ ไม่สามารถตัดสต็อกได้: {result}"})

    # ─────────────────────────────────────────────────────────────
    # Flex Messages (Clean Medical Design)
    # ─────────────────────────────────────────────────────────────

    def _create_deduct_success_flex(self, data, method="ข้อความ", drive_link=None):
        """Card showing successful dispensing details."""
        is_low = data.get("is_low_stock", False)
        status_color = "#EF4444" if is_low else "#10B981"
        status_text = "⚠️ ยาใกล้หมดสต็อก!" if is_low else "✅ สต็อกปกติ"

        contents = {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#0F766E",
                "paddingAll": "20px",
                "contents": [
                    {
                        "type": "text",
                        "text": "🏥 ตัดสต็อกยาสำเร็จ",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "size": "lg"
                    },
                    {
                        "type": "text",
                        "text": f"ช่องทาง: {data.get('channel', method)} • {data.get('created_at')}",
                        "color": "#99F6E4",
                        "size": "xs",
                        "margin": "sm"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "20px",
                "contents": [
                    {
                        "type": "text",
                        "text": data.get("drug_name", "ยา"),
                        "weight": "bold",
                        "size": "xl",
                        "color": "#0F172A",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": f"รหัส: {data.get('drug_code', '-')}",
                        "size": "xs",
                        "color": "#64748B",
                        "margin": "xs"
                    },
                    {"type": "separator", "margin": "lg"},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {"type": "text", "text": "จำนวนที่ตัด:", "size": "sm", "color": "#64748B"},
                                    {"type": "text", "text": f"-{data.get('quantity')} {data.get('unit')}", "size": "md", "weight": "bold", "color": "#E11D48", "align": "end"}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {"type": "text", "text": "ยอดคงเหลือหลังตัด:", "size": "sm", "color": "#64748B"},
                                    {"type": "text", "text": f"{data.get('balance_after')} {data.get('unit')}", "size": "lg", "weight": "bold", "color": "#0F766E", "align": "end"}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {"type": "text", "text": "สถานะคลัง:", "size": "xs", "color": "#64748B"},
                                    {"type": "text", "text": status_text, "size": "xs", "weight": "bold", "color": status_color, "align": "end"}
                                ]
                            }
                        ]
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "🌐 เปิดดูคลังยาบนเว็บ",
                            "uri": Config.BASE_URL
                        },
                        "style": "primary",
                        "color": "#0F766E"
                    }
                ]
            }
        }

        # Add Google Drive button if image exists
        if drive_link:
            contents["footer"]["contents"].append({
                "type": "button",
                "action": {
                    "type": "uri",
                    "label": "📁 ดูรูปหลักฐานบน Google Drive",
                    "uri": drive_link
                },
                "style": "secondary",
                "margin": "sm"
            })

        return {"type": "flex", "altText": f"ตัดสต็อก {data.get('drug_name')} สำเร็จ", "contents": contents}

    def _create_menu_flex(self):
        """Clinical menu flex message."""
        return {
            "type": "flex",
            "altText": "เมนูระบบคลังยา",
            "contents": {
                "type": "bubble",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#0D9488",
                    "contents": [
                        {"type": "text", "text": "🏥 ระบบจัดการคลังยาอัตโนมัติ", "weight": "bold", "color": "#FFFFFF", "size": "md"},
                        {"type": "text", "text": "LINE Stock & Dispensing Bot", "color": "#CCFBF1", "size": "xs", "margin": "xs"}
                    ]
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "💡 วิธีการใช้งาน:", "weight": "bold", "color": "#0F172A"},
                        {"type": "text", "text": "1. พิมพ์ [ชื่อยา] [จำนวน] เพื่อตัดสต็อก\n   เช่น 'พารา 2' หรือ 'Amox 1'", "size": "xs", "color": "#475569", "margin": "md", "wrap": True},
                        {"type": "text", "text": "2. ส่งรูปภาพซองยา / ฉลากยา / QR code เพื่อให้ AI อ่านและตัดสต็อกอัตโนมัติ", "size": "xs", "color": "#475569", "margin": "sm", "wrap": True},
                        {"type": "text", "text": "3. พิมพ์ 'เช็คสต็อก' เพื่อดูรายการยาทั้งหมด", "size": "xs", "color": "#475569", "margin": "sm", "wrap": True},
                        {"type": "text", "text": "4. พิมพ์ 'ยาหมด' เพื่อดูยาที่ต้องสั่งซื้อด่วน", "size": "xs", "color": "#475569", "margin": "sm", "wrap": True}
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "button",
                            "action": {"type": "uri", "label": "💻 เข้าสู่ระบบหน้าเว็บ", "uri": Config.BASE_URL},
                            "style": "primary",
                            "color": "#0D9488"
                        }
                    ]
                }
            }
        }

    def _create_stock_summary_flex(self):
        """Returns top 5 stock summary."""
        drugs = database.get_all_drugs()[:8]
        rows = []
        for d in drugs:
            is_low = d["stock_qty"] <= d["min_threshold"]
            rows.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "text", "text": d["name"], "size": "xs", "weight": "bold", "color": "#1E293B", "flex": 3, "wrap": False},
                    {"type": "text", "text": f"{d['stock_qty']} {d['unit']}", "size": "xs", "color": "#EF4444" if is_low else "#0F766E", "weight": "bold", "align": "end", "flex": 2}
                ]
            })

        return {
            "type": "flex",
            "altText": "สรุปสต็อกยาคงเหลือ",
            "contents": {
                "type": "bubble",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#0F766E",
                    "contents": [
                        {"type": "text", "text": "📦 สรุปสต็อกยาคงเหลือ", "weight": "bold", "color": "#FFFFFF", "size": "md"}
                    ]
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "md",
                    "contents": rows if rows else [{"type": "text", "text": "ไม่มีข้อมูลยาในระบบ"}]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "button", "action": {"type": "uri", "label": "ดูคลังยาทั้งหมด", "uri": Config.BASE_URL}, "style": "primary", "color": "#0F766E"}
                    ]
                }
            }
        }

    def _create_drug_card_flex(self, d):
        """Single drug info card."""
        is_low = d["stock_qty"] <= d["min_threshold"]
        return {
            "type": "flex",
            "altText": f"ข้อมูลยา {d['name']}",
            "contents": {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": d["name"], "weight": "bold", "size": "lg", "color": "#0F172A"},
                        {"type": "text", "text": f"รหัส: {d['code']} • หมวด: {d['category']}", "size": "xs", "color": "#64748B", "margin": "xs"},
                        {"type": "separator", "margin": "md"},
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "md",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {"type": "text", "text": "คงเหลือ:", "size": "sm", "color": "#64748B"},
                                        {"type": "text", "text": f"{d['stock_qty']} {d['unit']}", "weight": "bold", "size": "md", "color": "#EF4444" if is_low else "#0F766E", "align": "end"}
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {"type": "text", "text": "รูปแบบ:", "size": "xs", "color": "#64748B"},
                                        {"type": "text", "text": d.get("dosage_form", "-"), "size": "xs", "align": "end"}
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {"type": "text", "text": "วันหมดอายุ:", "size": "xs", "color": "#64748B"},
                                        {"type": "text", "text": d.get("expiry_date", "-"), "size": "xs", "align": "end"}
                                    ]
                                }
                            ]
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "button", "action": {"type": "message", "label": f"ตัดสต็อก 1 {d['unit']}", "text": f"{d['name']} 1"}, "style": "primary", "color": "#0F766E"}
                    ]
                }
            }
        }

line_bot = PharmacyLineBot()
