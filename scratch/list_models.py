import os
import requests
import json

api_key = "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"
url = "https://api.groq.com/openai/v1/models"
headers = {"Authorization": f"Bearer {api_key}"}

try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        models = response.json().get("data", [])
        print("--- GROQ MODELS ---")
        for m in models:
            print(m["id"])
    else:
        print(f"Error: {response.status_code} {response.text}")
except Exception as e:
    print(f"Exception: {e}")
