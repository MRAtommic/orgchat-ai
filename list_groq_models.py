import requests
api_key = "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"
url = "https://api.groq.com/openai/v1/models"
headers = {"Authorization": f"Bearer {api_key}"}
resp = requests.get(url, headers=headers)
if resp.status_code == 200:
    models = [m['id'] for m in resp.json()['data']]
    print("\n".join(models))
else:
    print(f"Error {resp.status_code}: {resp.text}")
