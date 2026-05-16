import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

def test_model(model_name, version):
    print(f"\n--- Testing {model_name} with API version {version} ---")
    try:
        if version:
            client = genai.Client(api_key=api_key, http_options={"api_version": version})
        else:
            client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model=model_name,
            contents="say hi",
        )
        print("✅ SUCCESS!")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

print("\n--- Listing available models ---")
try:
    client = genai.Client(api_key=api_key)
    for m in client.models.list():
        if "flash" in m.name:
            print(m.name)
except Exception as e:
    print(f"Error listing: {e}")

test_model("gemini-2.5-flash", "v1alpha")
test_model("gemini-1.5-flash", "v1")
test_model("gemini-1.5-flash", "v1beta")
test_model("gemini-1.5-flash-8b", "v1beta")
test_model("gemini-1.5-flash-8b", "v1")
test_model("gemini-1.5-flash", None)

