# -*- coding: utf-8 -*-
"""
AI Providers — รองรับ Gemini (google-genai ใหม่), Groq, Ollama
อัปเดต: เปลี่ยนจาก google-generativeai (deprecated) → google-genai
"""
import os
import json
import requests

# ✅ ใช้ google-genai (SDK ใหม่) แทน google-generativeai ที่ deprecated แล้ว
from google import genai
from google.genai import types


class AIProvider:
    def chat_stream(self, question: str, history: list, system_prompt: str):
        raise NotImplementedError


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        # google-genai ใหม่: สร้าง client ต่อ instance (ไม่ใช่ global configure)
        self.client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})

    def chat_stream(self, question: str, history: list, system_prompt: str,
                    image_data: bytes = None, mime_type: str = "image/jpeg"):

        # สร้าง history ในรูปแบบ google-genai
        gemini_history = []
        for msg in history[-12:]:
            role = "user" if msg.get("role") == "user" else "model"
            gemini_history.append(
                types.Content(role=role, parts=[types.Part(text=msg.get("text", ""))])
            )

        # สร้าง contents สำหรับการโทรครั้งนี้
        if image_data:
            # โหมดรูปภาพ: รวม history + คำถาม + รูป
            parts = [
                types.Part(text=question),
                types.Part(inline_data=types.Blob(mime_type=mime_type, data=image_data))
            ]
            contents = gemini_history + [types.Content(role="user", parts=parts)]
        else:
            # โหมดข้อความ: history + คำถามล่าสุด
            contents = gemini_history + [
                types.Content(role="user", parts=[types.Part(text=question)])
            ]

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
            max_output_tokens=2048,
        )

        print(f"DEBUG: เรียก Gemini API (google-genai SDK ใหม่, Real-time Streaming)...", flush=True)

        try:
            # ✅ ใช้ generate_content_stream เพื่อให้ AI ทยอยตอบออกมาทีละนิด (Real-time)
            response_stream = self.client.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=contents,
                config=config,
            )
            
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            err_msg = str(e)
            print(f"❌ Gemini API Error: {err_msg}", flush=True)
            if "429" in err_msg or "quota" in err_msg.lower():
                yield "⚠️ ขณะนี้มีการใช้งาน AI มากเกินไป โปรดรอสักครู่แล้วลองใหม่"
            elif "api_key" in err_msg.lower() or "invalid" in err_msg.lower():
                yield "❌ API Key ไม่ถูกต้อง กรุณาตรวจสอบการตั้งค่าในระบบ"
            else:
                yield f"❌ เกิดข้อผิดพลาดจาก AI: {err_msg[:200]}"


class GroqProvider(AIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def chat_stream(self, question: str, history: list, system_prompt: str,
                    image_data: bytes = None, mime_type: str = None):
        # Groq Free Tier มี TPM ต่ำ ต้องประหยัด token
        if len(system_prompt) > 4000:
            system_prompt = system_prompt[:4000] + "... [ตัดออกเพื่อประหยัด Token]"

        messages = [{"role": "system", "content": system_prompt}]

        for msg in history[-4:]:
            raw_role = msg.get("role", "user").lower()
            role = "assistant" if raw_role in ["bot", "model", "assistant"] else "user"
            text = msg.get("text", "")
            if len(text) > 500:
                text = text[:500] + "..."
            messages.append({"role": role, "content": text})

        # ใช้โมเดลตัวแรงล่าสุดของ Groq (70B) เพื่อความฉลาดสูงสุด
        model_name = "llama-3.3-70b-versatile"
        final_question_content = question

        if image_data:
            model_name = "meta-llama/llama-4-scout-17b-16e-instruct"
            import base64
            b64_img = base64.b64encode(image_data).decode('utf-8')
            final_question_content = [
                {"type": "text", "text": question},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{b64_img}"}
                }
            ]

        messages.append({"role": "user", "content": final_question_content})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model_name,
            "messages": messages,
            "stream": True
        }

        response = requests.post(self.url, headers=headers, json=data, stream=True)
        if response.status_code != 200:
            yield f"❌ ข้อผิดพลาดจาก Groq: {response.text}"
            return

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith("data: "):
                    if line == "data: [DONE]":
                        break
                    try:
                        content = json.loads(line[6:])
                        if 'error' in content:
                            yield f"⚠️ Groq Error: {content['error'].get('message', 'ไม่ทราบสาเหตุ')}"
                            return
                        chunk = content['choices'][0]['delta'].get('content', '')
                        if chunk:
                            yield chunk
                    except Exception as e:
                        print(f"❌ Error parsing Groq chunk: {e}")
                        continue


class OllamaProvider(AIProvider):
    def __init__(self, model_name: str = "llama3.1"):
        self.model_name = model_name
        self.url = "http://localhost:11434/api/chat"

    def chat_stream(self, question: str, history: list, system_prompt: str,
                    image_data: bytes = None, mime_type: str = None):
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-10:]:
            raw_role = msg.get("role", "user").lower()
            role = "assistant" if raw_role in ["bot", "model", "assistant"] else "user"
            messages.append({"role": role, "content": msg.get("text")})
        messages.append({"role": "user", "content": question})

        data = {"model": self.model_name, "messages": messages, "stream": True}

        try:
            response = requests.post(self.url, json=data, stream=True)
            for line in response.iter_lines():
                if line:
                    content = json.loads(line.decode('utf-8'))
                    chunk = content.get('message', {}).get('content', '')
                    if chunk:
                        yield chunk
                    if content.get('done'):
                        break
        except Exception as e:
            yield f"❌ ไม่สามารถเชื่อมต่อ Ollama ได้: {str(e)} — กรุณาตรวจสอบว่า Ollama กำลังทำงานอยู่"


def get_provider():
    provider_type = os.environ.get("AI_PROVIDER", "gemini").lower()

    if provider_type == "groq":
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("ไม่พบ GROQ_API_KEY ในตัวแปรสภาพแวดล้อม")
        return GroqProvider(api_key)

    elif provider_type == "ollama":
        model = os.environ.get("OLLAMA_MODEL", "llama3.1")
        return OllamaProvider(model)

    else:  # Default: gemini
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("ไม่พบ GEMINI_API_KEY ในตัวแปรสภาพแวดล้อม")
        return GeminiProvider(api_key)
