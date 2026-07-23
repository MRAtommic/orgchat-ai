# -*- coding: utf-8 -*-
"""
AI Providers — รองรับ Gemini (google-genai ใหม่), Groq, Ollama
อัปเดต: เปลี่ยนจาก google-generativeai (deprecated) → google-genai
"""
import os
import json
import logging
import requests

logger = logging.getLogger(__name__)

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
    _cached_models = []
    _cache_time = 0

    def __init__(self, api_key: str):
        self.api_key = api_key
        # Collect ALL available API keys for rotation chain
        self._all_keys = [api_key]
        for env_name in ["GEMINI_API_KEY_BACKUP", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3", "GEMINI_API_KEY_4"]:
            k = (os.environ.get(env_name) or "").strip()
            if k and k not in self._all_keys:
                self._all_keys.append(k)
        self.backup_key = self._all_keys[1] if len(self._all_keys) > 1 else None
        print(f"🔑 Gemini API Key Pool: {len(self._all_keys)} key(s) available for rotation")
        if HAS_NEW_SDK:
            self.client = genai.Client(api_key=api_key)
        else:
            old_genai.configure(api_key=api_key)

    def _get_active_models(self) -> list:
        if not HAS_NEW_SDK or not self.client:
            return []
        
        import time
        now = time.time()
        # Cache for 1 hour to prevent API overhead
        if GeminiProvider._cached_models and (now - GeminiProvider._cache_time < 3600):
            return GeminiProvider._cached_models

        try:
            models_list = list(self.client.models.list())
            fetched_ids = []
            for m in models_list:
                name = getattr(m, 'name', '') or getattr(m, 'model_id', '')
                if name:
                    if name.startswith("models/"):
                        name = name[len("models/"):]
                    fetched_ids.append(name)
            
            if fetched_ids:
                GeminiProvider._cached_models = fetched_ids
                GeminiProvider._cache_time = now
                return fetched_ids
        except Exception as e:
            print(f"⚠️ Gemini failed to fetch active models: {e}", flush=True)
        return []

    def chat_stream(self, question: str, history: list, system_prompt: str, 
                    image_data: bytes = None, mime_type: str = "image/jpeg"):
        
        # 🟢 New SDK Implementation (2026 Models)
        if HAS_NEW_SDK:
            try:
                parts = [types.Part.from_text(text=question)]
                if image_data:
                    parts.append(types.Part.from_bytes(data=image_data, mime_type=mime_type))
                
                contents = []
                for msg in history[-5:]:
                    r = "user" if msg.get("role") == "user" else "model"
                    contents.append(types.Content(role=r, parts=[types.Part.from_text(text=msg.get("text", ""))]))
                contents.append(types.Content(role="user", parts=parts))
                config = types.GenerateContentConfig(
                    system_instruction=system_prompt, 
                    temperature=0.7,
                    safety_settings=[
                        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                    ]
                )
                
                active_ids = self._get_active_models()
                if active_ids:
                    dynamic_models = []
                    # Ranking of preferred Gemini models in 2026
                    patterns = [
                        "gemini-3.1-flash-lite",
                        "gemini-3.1-flash",
                        "gemini-3.1-pro",
                        "gemini-3-flash",
                        "gemini-2.5-flash-lite",
                        "gemini-2.5-flash",
                        "gemini-2.5-pro",
                        "gemini-2.0-flash-lite",
                        "gemini-2.0-flash",
                        "gemini-1.5-flash"
                    ]
                    for pattern in patterns:
                        for m in active_ids:
                            m_lower = m.lower()
                            # Filter out non-text/specialized models
                            if any(x in m_lower for x in ["embedding", "imagen", "veo", "lyria", "aqa", "audio", "tts", "image"]):
                                continue
                            if pattern in m_lower and m not in dynamic_models:
                                dynamic_models.append(m)
                    
                    for m in active_ids:
                        m_lower = m.lower()
                        if any(x in m_lower for x in ["embedding", "imagen", "veo", "lyria", "aqa", "audio", "tts", "image"]):
                            continue
                        if m not in dynamic_models:
                            dynamic_models.append(m)
                    
                    if not dynamic_models:
                        dynamic_models = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-1.5-flash"]
                    models = dynamic_models
                else:
                    models = [
                        "gemini-2.5-flash-lite",
                        "gemini-2.5-flash",
                        "gemini-1.5-flash"
                    ]
                # Limit the models we try to avoid infinite 429 rate limit retries
                models = models[:3]
                
                # Build rotation chain from all available API keys
                clients_to_try = []
                for idx, key in enumerate(self._all_keys):
                    label = "Primary" if idx == 0 else f"Key-{idx+1}"
                    clients_to_try.append((label, genai.Client(api_key=key)))

                for client_name, client_obj in clients_to_try:
                    hit_rate_limit = False
                    for model in models:
                        try:
                            for chunk in client_obj.models.generate_content_stream(model=model, contents=contents, config=config):
                                if chunk.text: yield chunk.text
                            return  # Success — exit immediately
                        except Exception as e:
                            print(f"⚠️ Gemini ({client_name}) ({model}) Error: {e}")
                            e_str = str(e).lower()
                            if "429" in e_str or "resource_exhausted" in e_str or "quota" in e_str:
                                print(f"🔄 {client_name} rate limited. Trying next key...")
                                hit_rate_limit = True
                                break  # Break model loop, try next key
                            continue
                    if not hit_rate_limit:
                        break  # Non-rate-limit error, stop trying
                # If we exhausted all keys without success, raise
                if hit_rate_limit:
                    raise Exception("🛑 All Gemini API keys exhausted (rate limited). Please wait or add more keys.")
            except Exception as e:
                print(f"⚠️ New SDK Setup Error: {e}")

        # 🟡 Old SDK Fallback — ใช้ได้เฉพาะเมื่อ New SDK ไม่ได้ติดตั้ง
        if not HAS_NEW_SDK:
            try:
                model_name = "gemini-3.1-flash-lite"
                model = old_genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)
                if image_data:
                    content = [{"mime_type": mime_type, "data": image_data}, question]
                else:
                    content = [question]
                response = model.generate_content(content, stream=True)
                for chunk in response:
                    if chunk.text: yield chunk.text
                return
            except Exception as e:
                print(f"❌ Gemini (Old SDK) Error: {e}")

        # Final fallback to Groq
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key:
            groq = GroqProvider(groq_key)
            yield from groq.chat_stream(question, history, system_prompt, image_data, mime_type)
        else:
            yield "⚠️ Gemini ไม่สามารถเชื่อมต่อได้ และไม่มี GROQ_API_KEY สำรอง"

class GroqProvider(AIProvider):
    _cached_models = []
    _cache_time = 0

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def _get_active_models(self, api_key: str) -> list:
        import time
        now = time.time()
        # Cache for 1 hour to prevent API overhead
        if GroqProvider._cached_models and (now - GroqProvider._cache_time < 3600):
            return GroqProvider._cached_models

        models_url = "https://api.groq.com/openai/v1/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            response = requests.get(models_url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json().get("data", [])
                fetched_ids = [m["id"] for m in data if "id" in m]
                if fetched_ids:
                    GroqProvider._cached_models = fetched_ids
                    GroqProvider._cache_time = now
                    return fetched_ids
        except Exception as e:
            print(f"⚠️ Groq failed to fetch active models: {e}", flush=True)
        return []

    def chat_stream(self, question: str, history: list, system_prompt: str, 
                    image_data: bytes = None, mime_type: str = "image/jpeg"):
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

        else:
            messages.append({"role": "user", "content": question})

        # Determine keys to try (support dynamic key fallback)
        keys_to_try = []
        if self.api_key:
            keys_to_try.append(self.api_key)
        backup_key = os.environ.get("GROQ_API_KEY_BACKUP")
        if backup_key and backup_key not in keys_to_try:
            keys_to_try.append(backup_key)

        if not keys_to_try:
            yield "❌ GROQ_API_KEY is missing."
            return

        for active_key in keys_to_try:
            # Try to get active models dynamically from the Groq API for this key
            active_ids = self._get_active_models(active_key)
            
            if active_ids:
                if image_data:
                    dynamic_models = []
                    for pattern in ["llama-4-scout", "llama-3.2", "vision"]:
                        for m in active_ids:
                            if pattern in m.lower() and m not in dynamic_models:
                                dynamic_models.append(m)
                    for m in active_ids:
                        if "vision" in m.lower() and m not in dynamic_models:
                            dynamic_models.append(m)
                    if not dynamic_models:
                        dynamic_models = ["meta-llama/llama-4-scout-17b-16e-instruct"]
                else:
                    dynamic_models = []
                    patterns = [
                        "llama-3.3-70b", 
                        "llama-4-70b", 
                        "gpt-oss-120b", 
                        "llama-3.1-70b",
                        "llama-3.1-8b", 
                        "llama-3.3", 
                        "gpt-oss",
                        "qwen3", 
                        "qwen", 
                        "llama", 
                        "mixtral"
                    ]
                    for pattern in patterns:
                        for m in active_ids:
                            m_lower = m.lower()
                            if any(x in m_lower for x in ["whisper", "guard", "saudi", "arabic", "compound"]):
                                continue
                            if pattern in m_lower and m not in dynamic_models:
                                dynamic_models.append(m)
                    for m in active_ids:
                        m_lower = m.lower()
                        if any(x in m_lower for x in ["whisper", "guard", "saudi", "arabic", "compound"]):
                            continue
                        if m not in dynamic_models:
                            dynamic_models.append(m)
                    if not dynamic_models:
                        dynamic_models = ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "llama-3.1-8b-instant"]
                
                models_to_try = dynamic_models
            else:
                if image_data:
                    models_to_try = ["meta-llama/llama-4-scout-17b-16e-instruct"]
                else:
                    models_to_try = ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "llama-3.1-8b-instant"]

            headers = {"Authorization": f"Bearer {active_key}", "Content-Type": "application/json"}
            key_worked = False
            
            for model in models_to_try:
                try:
                    print(f"🌀 Attempting Groq ({model}) with key {active_key[:10]}...", flush=True)
                    payload = {"model": model, "messages": messages, "stream": True}
                    response = requests.post(self.url, headers=headers, json=payload, stream=True, timeout=30)
                    
                    if response.status_code == 200:
                        key_worked = True
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
                    elif response.status_code == 401:
                        print(f"❌ Groq key {active_key[:10]} is invalid (401). Trying next key...", flush=True)
                        break # Break inner model loop to try the next key immediately!
                    else:
                        print(f"❌ Groq {model} Error: {response.status_code} {response.text}", flush=True)
                        continue
                except Exception as e:
                    print(f"⚠️ Groq {model} Exception: {e}", flush=True)
                    continue
            
            if key_worked:
                return

        yield "⚠️ ระบบ AI สำรอง (Groq) ขัดข้อง (ทุกโมเดลถูกปิดใช้งาน)"


def analyze_media_contents(content_data: bytes, mime_type: str = "image/jpeg"):
    """ใช้ AI วิเคราะห์เนื้อหา (OCR สำหรับรูปภาพ หรือ STT สำหรับเสียง)"""
    
    is_audio = mime_type.startswith("audio/")
    
    # Load organization custom category rules if available
    custom_rules_str = ""
    try:
        import database
        from routes.shared import get_current_org_id
        org_id = get_current_org_id() or 1
        custom_rules = database.get_ai_category_rules(org_id)
        if custom_rules:
            rule_texts = "\n".join([f"- If text/merchant contains '{r['keyword']}', categorize as '{r['category_name']}'" for r in custom_rules])
            custom_rules_str = f"\n\nORGANIZATION CUSTOM CATEGORY RULES:\n{rule_texts}\n"
    except Exception as e_rule:
        logger.warning(f"Could not load custom AI rules: {e_rule}")

    if is_audio:
        prompt = """คุณคือ 'พั้น' ผู้ช่วยอัจฉริยะ สกัดข้อมูลจากข้อความเสียงบันทึกค่าใช้จ่าย
ฟังเสียงและ EXTRACT JSON ONLY.
{
  "category": "Receipt | Slip | Statement | ID_Card | Invoice | Quotation | General_Expense",
  "smart_name": "ประเภท_วันที่_คำอธิบาย_ยอดเงิน.mp3",
  "extracted_data": {
    "date": "DD/MM/YYYY", "time": "HH:MM",
    "net_amount": 0.00,
    "memo": "สรุปสิ่งที่พูดในเสียง",
    "receiver": "ชื่อทางการเต็มของร้านค้า/ผู้รับเงิน รวม บริษัท/จำกัด ครบถ้วน (ถ้ามี)",
    "income_type": "ประเภทค่าใช้จ่าย"
  },
  "summary": "Thai summary of the voice message"
}
RULES:
1. If the user says "บันทึกค่า...", set category to "General_Expense" or the most relevant one.
2. Extract exact amount mentioned.
3. Use "-" for missing string, 0 for missing numbers. No conversational text.""" + custom_rules_str
    else:
        prompt = """คุณคือ 'พั้น' ผู้ช่วยอัจฉริยะ สกัดข้อมูลจากเอกสารด้วยความแม่นยำ
EXTRACT JSON ONLY.
{
  "category": "Receipt | Slip | Statement | ID_Card | Invoice | Quotation | PaymentVoucher | Other",
  "smart_name": "ประเภท_วันที่_ผู้ส่ง_ยอดเงิน.jpg",
  "extracted_data": {
  "date": "DD/MM/YYYY", "time": "HH:MM",
  "sender": "FULL OFFICIAL VENDOR NAME exactly as printed (e.g. บริษัท บอกบุญ 888 จำกัด / ห้างหุ้นส่วนจำกัด ... / นาย/นาง/นางสาว ... — รวม คำนำหน้า+ชื่อกลาง+คำลงท้าย ครบถ้วน ห้ามตัดทอน)", "receiver": "FULL OFFICIAL BUYER NAME exactly as printed (รวม บริษัท/จำกัด ครบถ้วน)",
  "sender_bank": "Full English Bank Name (e.g. Kasikornbank, SCB)",
  "receiver_bank": "Full English Bank Name",
  "gross_amount": 0.00, "discount_amount": 0.00, "vat_amount": 0.00, "wht_amount": 0.00,
  "net_amount": 0.00,
  "total_amount": 0.00,
  "wht_rate": 0.00,
  "vendor_tax_id": "13_DIGIT_OF_VENDOR/SELLER (เลขที่ภาษีของผู้ขาย/ร้านค้า ไม่ใช่ผู้ซื้อ)",
  "tax_id": "13_DIGIT_OF_VENDOR/SELLER (same as vendor_tax_id)",
  "memo": "MEMO", "ref_number": "REF_NO", "appr_code": "APPROVAL_CODE",
  "qr_payload": "000201...",
  "branch": "BRANCH",
  "sender_address": "VENDOR PHYSICAL ADDRESS ONLY (ที่อยู่จดทะเบียนของผู้ขาย — ถนน/ตำบล/จังหวัด/รหัสไปรษณีย์ เท่านั้น ห้ามใส่ชื่อคน/เบอร์โทร/อีเมล)",
  "receiver_address": "BUYER PHYSICAL ADDRESS ONLY (ที่อยู่ผู้ซื้อ — ถนน/ตำบล/จังหวัด เท่านั้น)",
  "contact": "ชื่อผู้ติดต่อ (บุคคล ไม่ใช่ที่อยู่)", "phone": "Phone No", "email": "Email",
  "first_name_th": "ชื่อ", "last_name_th": "นามสกุล",
  "first_name_en": "First Name", "last_name_en": "Last Name",
  "birth_date": "DD/MM/YYYY", "gender": "Male/Female", "expiry_date": "DD/MM/YYYY",
  "address": "Full Address", "laser_id": "Laser Code",
  "income_type": "Income Type", "wht_type": "WHT Type", "is_etax": false,
  "transactions": [{"date": "DD/MM/YYYY", "time": "HH:MM", "description": "...", "details": "...", "withdrawal": 0.00, "deposit": 0.00, "balance": 0.00, "channel": "...", "ref_number": "...", "counterparty": "..."}]
  },  "summary": "Thai summary"
}""" + custom_rules_str
RULES:
0. COMPANY NAME RULE (CRITICAL — applies to ALL document types):
   - `sender` and `receiver` MUST be the FULL OFFICIAL registered name exactly as it appears on the document.
   - Thai company: MUST include prefix "บริษัท" / "ห้างหุ้นส่วนจำกัด" / "ห้างหุ้นส่วนสามัญ" AND suffix "จำกัด" / "จำกัด (มหาชน)" as printed.
   - Individual: MUST include title prefix (นาย / นาง / นางสาว / ดร. / etc.) + full name.
   - NEVER abbreviate, shorten, or omit any part of the company name.
   - Example WRONG: "บอกบุญ 888" → CORRECT: "บริษัท บอกบุญ 888 จำกัด"
   - Example WRONG: "อิมแพ็ค" → CORRECT: "บริษัท อิมแพ็ค เอ็กซิบิชั่น แมเนจเม้นท์ จำกัด"
1. Bank Slip: Extract exact sender_bank/receiver_bank in English. Check logos. For Bill Payment without receiver logo, receiver_bank="-".
2. Receipt/Invoice/PaymentVoucher:
   - `vendor_tax_id` and `tax_id` = เลขที่ภาษี 13 หลักของ **ผู้รับเงิน/ผู้ขาย** เท่านั้น (ห้ามใส่เลขของผู้จ่ายเงิน/บริษัทที่ออกเอกสาร).
   - PaymentVoucher (ใบสำคัญจ่าย): ผู้รับเงิน = บุคคลหรือบริษัทที่อยู่ใต้หัวข้อ "ผู้ขาย" หรือ "ผู้รับเงิน" → ใช้เลขภาษีของคนนั้น ไม่ใช่บริษัทที่ออกเอกสาร.
   - บุคคลธรรมดา → ใช้เลขบัตรประชาชน 13 หลัก.
   - `gross_amount` = ยอดก่อน VAT (pre-VAT subtotal).
   - `total_amount` = ยอดรวม VAT (gross_amount + vat_amount = จำนวนเงินทั้งสิ้น).
   - `net_amount` = ยอดที่จ่ายจริง หลังหัก WHT (total_amount - wht_amount).
   - `wht_amount`, `vat_amount` are critical! WHT=หัก ณ ที่จ่าย.
   - `sender_address` = ที่อยู่จริงของผู้ขาย (ถนน/ตำบล/จังหวัด) ONLY — ห้ามใส่ชื่อบุคคล/เบอร์/อีเมล.
   - ชื่อผู้ติดต่อ → `contact`. เบอร์โทร → `phone`. อีเมล → `email`. ห้ามปนกับ address.
   - Quotation (ใบเสนอราคา): ยังไม่มีการจ่ายเงิน ตั้ง category="Quotation" เสมอ.
   - PaymentVoucher (ใบสำคัญจ่าย): ตั้ง category="PaymentVoucher".
3. Statement: Extract ALL rows into `transactions`. For each transaction row, extract date, time, description/รายการ, details/รายละเอียด (CRITICAL: You MUST extract any visible names, account numbers, ATM/branch locations, or bank initials next to or underneath the transaction description. Do NOT lazily use "-"), withdrawal/ถอน, deposit/ฝาก, balance/ยอดคงเหลือ, channel/ช่องทาง, ref_number/เลขที่อ้างอิง, and counterparty/คู่ค้า/ผู้โอน (CRITICAL: Extract the name of the person, company, or merchant who sent or received the money from the transaction text. Do NOT leave as "-" if any name is visible).
4. ID Card: Extract `id_number`, names (TH/EN), `birth_date`, `gender`, `address`, `laser_id`.
5. ALWAYS extract `appr_code` (Auth Code/Approval Code) to prevent duplicates.
6. QR Code Slip Verification: Look for the Thai QR Code payload on the transfer slip (usually begins with '000201' and is a long alphanumeric string) and extract the raw EMVCo string payload into 'qr_payload'. If not found or not visible, use "-".
7. Use "-" for missing string, 0 for missing numbers. No conversational text.
8. If the document/image is NOT a financial transaction document (e.g. general photo, screenshot of software/web page, profile picture, non-invoice document), set category to "Other"."""
    
    # 🚀 Prioritize Gemini for Media Analysis
    full_response = ""
    try:
        gemini = GeminiProvider(os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY_BACKUP"))
        # Using chat_stream which supports image/audio via Part.from_bytes
        for chunk in gemini.chat_stream(prompt, [], "You are a professional accounting AI.", image_data=content_data, mime_type=mime_type):
            full_response += chunk
    except Exception as e:
        print(f"⚠️ Primary Gemini failed: {e}. Trying fallback...", flush=True)

    # Robust Fallback
    is_valid_json = "{" in full_response and "}" in full_response
    if len(full_response) < 50 or not is_valid_json or "⚠️" in full_response:
        try:
            # Note: Groq might not support audio via this specific call, 
            # so we focus on Gemini for audio.
            if not is_audio:
                provider = get_provider() 
                if isinstance(provider, GeminiProvider):
                    groq_key = os.environ.get("GROQ_API_KEY")
                    if groq_key:
                        provider = GroqProvider(groq_key)
                
                full_response = ""
                for chunk in provider.chat_stream(prompt, [], "You are a professional accounting AI.", image_data=content_data, mime_type=mime_type):
                    full_response += chunk
        except Exception as e:
            import traceback
            logger.error(f"Fallback also failed: {e}\n{traceback.format_exc()}")

    logger.debug(f"AI Raw Response ({len(full_response)} chars): {full_response[:500]}...")
    
    import re
    try:
        # Clean response to get JSON
        full_response = full_response.strip()
        
        # Strip outer markdown blocks if present
        if full_response.startswith("```json"):
            full_response = full_response[7:].strip()
        if full_response.endswith("```"):
            full_response = full_response[:-3].strip()
            
        start_idx = full_response.find('{')
        end_idx = full_response.rfind('}')
        
        json_str = ""
        if start_idx != -1:
            if end_idx != -1:
                json_str = full_response[start_idx:end_idx+1]
            else:
                json_str = full_response[start_idx:]
                
        if json_str:
            try:
                # Use strict=False to allow control characters (tabs, newlines) inside strings
                return json.loads(json_str, strict=False)
            except Exception as e:
                # Clean nested markdown blocks if any
                cleaned = json_str
                cleaned = re.sub(r'```json\s*', '', cleaned)
                cleaned = re.sub(r'```\s*', '', cleaned)
                try:
                    return json.loads(cleaned, strict=False)
                except Exception:
                    pass
        
        # If we reach here, it failed to parse as JSON. Let's do a regex fallback on full_response!
        result = {
            "category": "Unknown",
            "extracted_data": {},
            "summary": "สแกนเอกสารสำเร็จ (ข้อมูลบางส่วนอาจคลาดเคลื่อน)"
        }
        
        # Use full_response or json_str as search target
        search_target = json_str or full_response
        
        # Extract category
        cat_match = re.search(r'"category"\s*:\s*"([^"]+)"', search_target)
        if cat_match:
            result["category"] = cat_match.group(1)
        else:
            # Try parsing from smart_name prefix
            name_match = re.search(r'"smart_name"\s*:\s*"([^"]+)"', search_target)
            if name_match:
                name_val = name_match.group(1)
                if "_" in name_val:
                    result["category"] = name_val.split("_")[0]
            
        # Extract net_amount
        amt_match = re.search(r'"net_amount"\s*:\s*([\d.]+)', search_target)
        if amt_match:
            try:
                result["extracted_data"]["net_amount"] = float(amt_match.group(1))
            except:
                pass
                
        # Extract sender
        sender_match = re.search(r'"sender"\s*:\s*"([^"]+)"', search_target)
        if sender_match:
            result["extracted_data"]["sender"] = sender_match.group(1)
            
        # Extract receiver
        receiver_match = re.search(r'"receiver"\s*:\s*"([^"]+)"', search_target)
        if receiver_match:
            result["extracted_data"]["receiver"] = receiver_match.group(1)

        # Extract date
        date_match = re.search(r'"date"\s*:\s*"([^"]+)"', search_target)
        if date_match:
            result["extracted_data"]["date"] = date_match.group(1)
            
        # Extract ref_number
        ref_match = re.search(r'"ref_number"\s*:\s*"([^"]+)"', search_target)
        if ref_match:
            result["extracted_data"]["ref_number"] = ref_match.group(1)

        # Extract summary
        sum_match = re.search(r'"summary"\s*:\s*"([^"]+)"', search_target)
        if sum_match:
            result["summary"] = sum_match.group(1)
            
        # If the category is STILL Unknown, but we see "Slip" or "Receipt" in the text, let's auto-detect it
        if result["category"] == "Unknown":
            lower_text = search_target.lower()
            if "slip" in lower_text or "สลิป" in lower_text:
                result["category"] = "Slip"
            elif "receipt" in lower_text or "ใบเสร็จ" in lower_text:
                result["category"] = "Receipt"
            elif "invoice" in lower_text or "ใบกำกับ" in lower_text:
                result["category"] = "Invoice"
                
        return result

    except Exception as e:
        return {"category": "Unknown", "extracted_data": {}, "summary": f"❌ JSON Parse Error: {str(e)} | Raw: {full_response[:100]}"}


def get_provider():
    """Returns the configured AI provider based on environment variables."""
    provider_type = os.environ.get("AI_PROVIDER", "groq").lower()
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
