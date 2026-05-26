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
    _cached_models = []
    _cache_time = 0

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.backup_key = os.environ.get("GEMINI_API_KEY_BACKUP")
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
                
                contents = [types.Content(role="user", parts=parts)]
                config = types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.7)
                
                active_ids = self._get_active_models()
                if active_ids:
                    dynamic_models = []
                    # Ranking of preferred Gemini models in 2026
                    patterns = [
                        "gemini-3.5-flash",
                        "gemini-3.1-flash-lite",
                        "gemini-3.1-pro",
                        "gemini-3-flash",
                        "gemini-3-pro",
                        "gemini-2.5-flash",
                        "gemini-2.5-pro",
                        "gemini-2.0-flash-lite",
                        "gemini-2.0-flash",
                        "gemini-flash-lite",
                        "gemini-flash"
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
                        dynamic_models = ["gemini-3.1-flash-lite", "gemini-3.1-pro-preview", "gemini-2.5-flash"]
                    models = dynamic_models
                else:
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
    "receiver": "ชื่อร้านค้าหรือผู้รับเงิน (ถ้ามี)",
    "income_type": "ประเภทค่าใช้จ่าย"
  },
  "summary": "Thai summary of the voice message"
}
RULES:
1. If the user says "บันทึกค่า...", set category to "General_Expense" or the most relevant one.
2. Extract exact amount mentioned.
3. Use "-" for missing string, 0 for missing numbers. No conversational text."""
    else:
        prompt = """คุณคือ 'พั้น' ผู้ช่วยอัจฉริยะ สกัดข้อมูลจากเอกสารด้วยความแม่นยำ
EXTRACT JSON ONLY.
{
  "category": "Receipt | Slip | Statement | ID_Card | Invoice | Quotation",
  "smart_name": "ประเภท_วันที่_ผู้ส่ง_ยอดเงิน.jpg",
  "extracted_data": {
    "date": "DD/MM/YYYY", "time": "HH:MM",
    "sender": "SENDER_NAME", "receiver": "RECEIVER_NAME",
    "sender_bank": "Full English Bank Name (e.g. Kasikornbank, SCB)", 
    "receiver_bank": "Full English Bank Name",
    "gross_amount": 0.00, "discount_amount": 0.00, "vat_amount": 0.00, "wht_amount": 0.00, "net_amount": 0.00,
    "tax_id": "13_DIGIT", "memo": "MEMO", "ref_number": "REF_NO", "appr_code": "APPROVAL_CODE",
    "branch": "BRANCH", "sender_address": "ADDRESS", "receiver_address": "ADDRESS",
    "income_type": "Income Type", "wht_type": "WHT Type", "is_etax": false,
    "transactions": [{"date": "DD/MM/YYYY", "time": "HH:MM", "description": "...", "withdrawal": 0.00, "deposit": 0.00, "balance": 0.00}]
  },
  "summary": "Thai summary"
}
RULES:
1. Bank Slip: Extract exact sender_bank/receiver_bank in English. Check logos. For Bill Payment without receiver logo, receiver_bank="-".
2. Receipt/Invoice: `tax_id`, `gross_amount`, `vat_amount`, `wht_amount` are critical! WHT=หัก ณ ที่จ่าย/WHT/ติดลบ.
3. Statement: Extract ALL rows into `transactions`.
4. ID Card: Extract `id_number`, names (TH/EN), `birth_date`, `gender`, `address`, `laser_id`.
5. ALWAYS extract `appr_code` (Auth Code/Approval Code) to prevent duplicates.
6. Use "-" for missing string, 0 for missing numbers. No conversational text."""
    
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
            print(f"❌ Fallback also failed: {e}\n{traceback.format_exc()}", flush=True)

    print(f"DEBUG: AI Raw Response ({len(full_response)} chars): {full_response[:500]}...", flush=True)
    
    try:
        # Clean response to get JSON
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
