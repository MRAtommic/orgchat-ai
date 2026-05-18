# -*- coding: utf-8 -*-
"""
AI Providers — รองรับ Gemini (google-genai ใหม่), Groq, Ollama
อัปเดต: เปลี่ยนจาก google-generativeai (deprecated) → google-genai
"""
import os
import json
import logging
import requests

try:
    from google import genai
    from google.genai import types
    HAS_NEW_SDK = True
except ImportError:
    import google.generativeai as old_genai
    HAS_NEW_SDK = False

class AIProvider:
    def chat_stream(self, question: str, history: list, system_prompt: str):
        raise NotImplementedError

class GeminiProvider(AIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.backup_key = os.environ.get("GEMINI_API_KEY_BACKUP")
        if HAS_NEW_SDK:
            self.client = genai.Client(api_key=api_key)
        else:
            old_genai.configure(api_key=api_key)

    def chat_stream(self, question: str, history: list, system_prompt: str, 
                    image_data: bytes = None, mime_type: str = "image/jpeg"):
        
        # 🟢 New SDK Implementation (2026 Models)
        if HAS_NEW_SDK:
            try:
                parts = [types.Part.from_text(text=question)]
                if image_data:
                    parts.append(types.Part.from_bytes(data=image_data, mime_type=mime_type))
                
                contents = [types.Content(role="user", parts=parts)]
                config = types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.7)
                
                # 🚀 Gemini 3.x เป็นมาตรฐานความเสถียรของปี 2026
                models = [
                    "gemini-3.1-flash-lite", 
                    "gemini-3.1-pro-preview", 
                    "gemini-2.5-flash"
                ]
                for model in models:
                    try:
                        for chunk in self.client.models.generate_content_stream(model=model, contents=contents, config=config):
                            if chunk.text: yield chunk.text
                        return
                    except Exception as e:
                        print(f"⚠️ Gemini New SDK ({model}) Error: {e}")
                        continue
            except Exception as e:
                print(f"⚠️ New SDK Setup Error: {e}")

        # 🟡 Old SDK Fallback (2026 Models)
        try:
            # ลองใช้ Gemini 3.1 Flash-Lite เป็นตัวหลักสำหรับ SDK เก่า
            model_name = "gemini-3.1-flash-lite"
            model = old_genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)
            
            if image_data:
                content = [{"mime_type": mime_type, "data": image_data}, question]
            else:
                content = [question]
                
            response = model.generate_content(content, stream=True)
            for chunk in response:
                if chunk.text: yield chunk.text
        except Exception as e:
            print(f"❌ Gemini (Old SDK) Error: {e}")
            # Final fallback to Groq
            groq = GroqProvider(os.environ.get("GROQ_API_KEY", ""))
            yield from groq.chat_stream(question, history, system_prompt, image_data, mime_type)

class GroqProvider(AIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def chat_stream(self, question: str, history: list, system_prompt: str, 
                    image_data: bytes = None, mime_type: str = "image/jpeg"):
        if not self.api_key:
            yield "❌ GROQ_API_KEY is missing."
            return

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-5:]:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("text", "")})
        
        if image_data:
            import base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                ]
            })
            # 🚀 โมเดล Vision ที่ผ่านการตรวจสอบ (ปี 2026)
            models_to_try = [
                "meta-llama/llama-4-scout-17b-16e-instruct"
            ]
        else:
            messages.append({"role": "user", "content": question})
            models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        
        for model in models_to_try:
            try:
                print(f"🌀 Attempting Groq ({model})...", flush=True)
                payload = {"model": model, "messages": messages, "stream": True}
                response = requests.post(self.url, headers=headers, json=payload, stream=True, timeout=30)
                
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            line_str = line.decode('utf-8').replace('data: ', '')
                            if line_str == '[DONE]': break
                            try:
                                data = json.loads(line_str)
                                content = data['choices'][0]['delta'].get('content', '')
                                if content: yield content
                            except: continue
                    return # Success
                else:
                    print(f"❌ Groq {model} Error: {response.status_code} {response.text}", flush=True)
                    continue
            except Exception as e:
                print(f"⚠️ Groq {model} Exception: {e}", flush=True)
                continue
        yield "⚠️ ระบบ AI สำรอง (Groq) ขัดข้อง (ทุกโมเดลถูกปิดใช้งาน)"

def analyze_image_contents(image_data: bytes, mime_type: str = "image/jpeg"):
    """ใช้ AI วิเคราะห์รูปภาพ (OCR + Smart Audit)"""
    prompt = """
    คุณคือ 'พั้น' ผู้ช่วยอัจฉริยะ (Professional Auditor v11.0.4)
    ภารกิจ: สกัดข้อมูลจากเอกสารบัญชี/ภาษี ด้วยความแม่นยำสูงสุด
    
    **Auditor Intelligence (ระดับความฉลาดสูงสุด)**:
    - หากยอดเงินไม่ชัดเจน ให้ใช้หลักการทางบัญชี: gross_amount - discount_amount + vat_amount - wht_amount = net_amount
    - สังเกตโลโก้ธนาคารเพื่อระบุ sender_bank/receiver_bank แม้ตัวหนังสือจะไม่ชัด
    - ตรวจสอบ QR Code ในสลิป (ถ้ามี) เพื่อยืนยันความถูกต้องของข้อมูล
    - หากข้อมูลบางอย่างหายไป (เช่น สาขา) ให้พยายามคาดการณ์จากที่อยู่ในเอกสารอย่างสมเหตุสมผล
    
    **กฎการสกัดข้อมูล**:
    1. **Bank Slip (สลิปโอนเงิน)**:
       - เน้น: วันที่, เวลา, ผู้โอน, ผู้รับ, ยอดเงิน (net_amount), บันทึก (memo)
       - สำคัญ: ระบุธนาคารต้นทาง (sender_bank) และธนาคารปลายทาง (receiver_bank) เช่น กสิกรไทย, ไทยพาณิชย์, SCB, KBANK เป็นต้น
       - ห้ามสกัด: income_type, wht_rate, tax_id (ถ้าไม่ใช่สลิปนิติบุคคล)
    2. **Receipt/Invoice (ใบเสร็จ/ใบกำกับภาษี)**:
       - เน้น: เลขประจำตัวผู้เสียภาษี (tax_id), ยอดก่อนภาษี (gross_amount), ส่วนลด (discount_amount), ภาษี (vat_amount), ยอดสุทธิ (net_amount)
       - **หัก ณ ที่จ่าย (wht_amount)**: สำคัญมาก! ต้องสกัดจากคำว่า "หัก ณ ที่จ่าย", "WHT", "ภาษีหัก ณ ที่จ่าย" หรือยอดที่ติดลบก่อนรวมเป็นยอดสุทธิ
       - **อัตราภาษี (wht_rate)**: เช่น 1%, 3%, 5%
    3. **Statement**: สกัดรายการ transactions ในรูปแบบ List
    
    EXTRACT DATA INTO JSON:
    {
      "category": "Receipt | Slip | Statement | ID_Card",
      "smart_name": "ประเภท_วันที่_ผู้ส่ง_ยอดเงิน.jpg",
      "extracted_data": {
        "date": "DD/MM/YYYY",
        "time": "HH:MM",
        "sender": "SENDER_NAME",
        "sender_bank": "BANK_NAME (เช่น กสิกรไทย, ไทยพาณิชย์, SCB, KBANK)",
        "receiver": "RECEIVER_NAME",
        "receiver_bank": "BANK_NAME (เช่น กสิกรไทย, ไทยพาณิชย์, SCB, KBANK)",
        "gross_amount": 0.00,
        "discount_amount": 0.00,
        "vat_amount": 0.00,
        "wht_amount": 0.00,
        "net_amount": 0.00,
        "tax_id": "13_DIGIT_ID",
        "memo": "MEMO_TEXT",
        "ref_number": "REF_NO",
        "branch": "BRANCH_NAME",
        "sender_address": "ADDRESS_OF_SENDER",
        "receiver_address": "ADDRESS_OF_RECEIVER",
        "income_type": "ประเภทเงินได้ (เช่น ค่าบริการ, ค่าขนส่ง)",
        "wht_type": "ประเภทภาษีหัก ณ ที่จ่าย (เช่น ค่าบริการ 3%)",
        "contact": "ช่องทางการติดต่อ (เบอร์โทร/อีเมล)",
        "transactions": [
          {
            "date": "DD/MM/YYYY",
            "time": "HH:MM",
            "description": "รายการ",
            "details": "รายละเอียด",
            "withdrawal": 0.00,
            "deposit": 0.00,
            "fee": 0.00,
            "balance": 0.00,
            "channel": "ช่องทาง",
            "ref": "เลขที่อ้างอิง",
            "counterparty": "คู่ค้า/ผู้โอน"
          }
        ]
      },
      "summary": "สรุปสั้นๆ (ภาษาไทย)"
    }
    
    RULES:
    - **สแกนบันทึกช่วยจำ (Memo)**: หากเห็นคำว่า "ExWHT" หรือ "หัก ณ ที่จ่าย" ในบันทึกช่วยจำ ต้องตีความว่ามีการหักภาษีแล้ว และสกัดยอดออกมาให้ได้
    - **ระบุธนาคารให้แม่นยำ**: ต้องระบุธนาคารต้นทาง (sender_bank) และปลายทาง (receiver_bank) ให้ได้ โดยดูจากชื่อธนาคาร หรือ "โลโก้" ที่อยู่ใกล้ชื่อนั้นๆ
    - **กรณี Bill Payment (ชำระบิล)**: หากเห็นคำว่า "Bill Payment", "Comp Code", หรือ "Biller ID" และไม่มีโลโก้ธนาคารที่ชัดเจนของฝั่งผู้รับ **ให้ใส่ receiver_bank เป็น "-"** ห้ามเดาเอาจากโลโก้ธนาคารที่ใช้โอน (เช่น K-BIZ, K Plus)
    - **สกัดวันและเวลาให้แม่นยำ**: มักจะอยู่คู่กัน (เช่น 10/03/2026 15:12 หรือ 10-03-26 15:12) ต้องสกัดทั้งคู่ หากเจอเวลาต้องใส่ในช่อง `time` ห้ามทิ้งเป็น "-" หากมีข้อมูล
    - **หัก ณ ที่จ่าย (WHT) และ ที่อยู่ (Address)**: สำคัญมาก! ต้องสกัดที่อยู่ (`sender_address`) และเลขประจำตัวผู้เสียภาษี (`tax_id`) จากใบกำกับภาษีให้ได้ครบถ้วนที่สุด หากเจอหลายที่อยู่ ให้เลือกที่อยู่ของผู้ที่ออกเอกสาร (Seller/Vendor) เป็นหลัก
    - **หัก ณ ที่จ่าย (WHT) ต้องสกัดให้ได้**: มักจะเป็นยอดเล็กๆ ที่อยู่ท้ายบิล หรือระบุเป็น % (1%, 3%, 5%) หากเห็นคำว่า "หัก ณ ที่จ่าย", "WHT", "ภาษีหัก ณ ที่จ่าย" ต้องเอาตัวเลขนั้นมาใส่ใน `wht_amount` และระบุประเภทใน `wht_type` (เช่น ค่าบริการ 3%, ค่าขนส่ง 1%) ห้ามข้ามเด็ดขาด
    - **หมวดหมู่ (Category)**: 
        - "Slip": สลิปโอนเงินธนาคาร
        - "Receipt": ใบเสร็จรับเงิน/ใบกำกับภาษีที่มีการชำระเงินแล้ว
        - "Invoice": ใบแจ้งหนี้ที่ยังไม่ได้ชำระ
        - "Statement": รายการเดินบัญชีธนาคาร (ต้องสกัดรายการเดินบัญชี "ทุกบรรทัด" ที่ปรากฏในภาพ ใส่ลงใน transactions ให้ครบถ้วนที่สุด ทั้งวันที่, เวลา, รายการ, ยอดเงิน และคู่ค้า)
        - "ID_Card": บัตรประชาชน (ต้องสกัดให้ครบ: id_number, first_name_th, last_name_th, first_name_en, last_name_en, birth_date, gender, address, expiry_date, laser_id)
    - ตัวอย่างโครงสร้าง ID_Card: {"id_number": "...", "first_name_th": "วีรภัทร", "last_name_th": "ชื่นชอบ", "first_name_en": "Weeraphat", "last_name_en": "Chuenchob", ...}
        - "Quotation": ใบเสนอราคา
    - ใช้ "-" หากไม่มีข้อมูล (ตัวเลขใช้ 0)
    - ยอดหัก ณ ที่จ่าย (WHT) สำคัญมากสำหรับงานบัญชี
    - ONLY JSON. NO CONVERSATIONAL TEXT.
    """
    
    # 🚀 Prioritize Gemini for Vision/OCR (Better at Thai & Complex Layouts)
    full_response = ""
    try:
        gemini = GeminiProvider(os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY_BACKUP"))
        for chunk in gemini.chat_stream(prompt, [], "You are a professional accounting AI.", image_data=image_data, mime_type=mime_type):
            full_response += chunk
    except Exception as e:
        print(f"⚠️ Primary Gemini failed: {e}. Trying fallback...", flush=True)

    # Robust Fallback: If Gemini failed or response doesn't look like JSON
    is_valid_json = "{" in full_response and "}" in full_response
    if len(full_response) < 50 or not is_valid_json or "⚠️" in full_response:
        try:
            # ใช้ Groq เป็นสำรอง
            provider = get_provider() 
            if isinstance(provider, GeminiProvider): # If already tried above, try Groq directly
                groq_key = os.environ.get("GROQ_API_KEY")
                if groq_key:
                    provider = GroqProvider(groq_key)
            
            full_response = ""
            for chunk in provider.chat_stream(prompt, [], "You are a professional accounting AI.", image_data=image_data, mime_type=mime_type):
                full_response += chunk
        except Exception as e:
            import traceback
            print(f"❌ Fallback also failed: {e}\n{traceback.format_exc()}", flush=True)

    print(f"DEBUG: AI Raw Response ({len(full_response)} chars): {full_response[:500]}...", flush=True)
    
    try:
        # Clean response to get JSON (หาปีกกาคู่แรกและคู่สุดท้าย)
        full_response = full_response.strip()
        start_idx = full_response.find('{')
        end_idx = full_response.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_str = full_response[start_idx:end_idx+1]
            return json.loads(json_str)
        return {"category": "Unknown", "extracted_data": {}, "summary": full_response or "❌ No response from AI providers"}
    except Exception as e:
        return {"category": "Unknown", "extracted_data": {}, "summary": f"❌ JSON Parse Error: {str(e)} | Raw: {full_response[:100]}"}

def get_provider():
    """Returns the configured AI provider based on environment variables."""
    provider_type = os.environ.get("AI_PROVIDER", "gemini").lower()
    api_key = os.environ.get("GEMINI_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")

    if provider_type == "gemini" and api_key:
        return GeminiProvider(api_key)
    elif provider_type == "groq" and groq_key:
        return GroqProvider(groq_key)
    return GeminiProvider(api_key or "dummy")

def generate_response(question: str, history: list = None, system_prompt: str = "") -> str:
    """Helper to get a full response (non-streaming) from the configured provider."""
    provider = get_provider()
    history = history or []
    full_response = ""
    for chunk in provider.chat_stream(question, history, system_prompt):
        full_response += chunk
    return full_response
