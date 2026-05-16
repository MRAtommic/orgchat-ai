import requests
import os

api_key = "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"
url = "https://api.groq.com/openai/v1/chat/completions"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
payload = {
    "model": "llama-3.2-11b-vision-preview",
    "messages": [{"role": "user", "content": "Hello, can you see me?"}],
    "max_tokens": 10
}

resp = requests.post(url, headers=headers, json=payload)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")
