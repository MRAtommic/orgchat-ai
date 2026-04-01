import os
import json
import requests
import google.generativeai as genai
from google.generativeai import types

class AIProvider:
    def chat_stream(self, question: str, history: list, system_prompt: str):
        raise NotImplementedError

class GeminiProvider(AIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)

    def chat_stream(self, question: str, history: list, system_prompt: str, image_data: bytes = None, mime_type: str = "image/jpeg"):
        # Configure tools (Web Search)
        tools = []
        if os.environ.get("ENABLE_WEB_SEARCH", "true").lower() == "true":
            # Direct tool name for grounding
            tools = [{'google_search_retrieval': {}}]

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_prompt,
            tools=tools
        )
        
        # Build contents for a single turn if image is present
        # Or start a chat session if it's a long conversation
        if image_data:
            # For simplicity, multimodal messages are usually single-turn or requires special handling in chat sessions
            # Here we'll combine history and image in the final prompt if possible, or use a simple generate_content
            contents = []
            # Add limited history as text context
            for msg in history[-5:]:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg.get("text", "")}]})
            
            # Add final user message with image
            contents.append({
                "role": "user",
                "parts": [
                    {"text": question},
                    {"inline_data": {"mime_type": mime_type, "data": image_data}}
                ]
            })
            
            response = model.generate_content(contents, stream=True)
        else:
            # Standard text-only chat session
            gemini_history = []
            for msg in history[-12:]:
                role = "user" if msg.get("role") == "user" else "model"
                gemini_history.append({"role": role, "parts": [{"text": msg.get("text", "")}]})
            
            chat_session = model.start_chat(history=gemini_history)
            response = chat_session.send_message(question, stream=True)

        for chunk in response:
            try:
                if chunk.text:
                    yield chunk.text
            except Exception as e:
                print(f"⚠️ Chunk error (possibly safety filter): {e}")
                continue

class GroqProvider(AIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def chat_stream(self, question: str, history: list, system_prompt: str, image_data: bytes = None, mime_type: str = None):
        # Groq Free Tier has very low TPM (6000), so we must be aggressive in saving tokens
        # Truncate system prompt
        if len(system_prompt) > 4000:
            system_prompt = system_prompt[:4000] + "... [Truncated for Token Limits]"
            
        messages = [{"role": "system", "content": system_prompt}]
        
        # Reduce history window for Groq
        for msg in history[-4:]:
            raw_role = msg.get("role", "user").lower()
            role = "assistant" if raw_role in ["bot", "model", "assistant"] else "user"
            text = msg.get("text", "")
            # Truncate long history messages
            if len(text) > 500: text = text[:500] + "..."
            messages.append({"role": role, "content": text})
            
        # Determine model based on whether image is present
        model_name = "llama-3.1-8b-instant"
        final_question_content = question
        
        if image_data:
            model_name = "meta-llama/llama-4-scout-17b-16e-instruct"
            # Format for multimodal
            import base64
            b64_img = base64.b64encode(image_data).decode('utf-8')
            final_question_content = [
                {"type": "text", "text": question},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{b64_img}"
                    }
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
            yield f"Error from Groq: {response.text}"
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
                            yield f"⚠️ Groq Error: {content['error'].get('message', 'Unknown error')}"
                            return
                        chunk = content['choices'][0]['delta'].get('content', '')
                        if chunk:
                            yield chunk
                    except Exception as e:
                        print(f"Error parsing Groq chunk: {e}")
                        continue

class OllamaProvider(AIProvider):
    def __init__(self, model_name: str = "llama3.1"):
        self.model_name = model_name
        self.url = "http://localhost:11434/api/chat"

    def chat_stream(self, question: str, history: list, system_prompt: str, image_data: bytes = None, mime_type: str = None):
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-10:]:
            raw_role = msg.get("role", "user").lower()
            role = "assistant" if raw_role in ["bot", "model", "assistant"] else "user"
            messages.append({"role": role, "content": msg.get("text")})
        messages.append({"role": "user", "content": question})

        data = {
            "model": self.model_name,
            "messages": messages,
            "stream": True
        }
        
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
            yield f"Error connecting to Ollama: {str(e)}. Make sure Ollama is running."

def get_provider():
    provider_type = os.environ.get("AI_PROVIDER", "gemini").lower()
    
    if provider_type == "groq":
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        return GroqProvider(api_key)
    
    elif provider_type == "ollama":
        model = os.environ.get("OLLAMA_MODEL", "llama3.1")
        return OllamaProvider(model)
    
    else: # Default gemini
        api_key = os.environ.get("GEMINI_API_KEY")
        return GeminiProvider(api_key)
