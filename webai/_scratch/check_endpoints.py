import urllib.request
import urllib.error
import json

endpoints = [
    "http://127.0.0.1:5005/api/superadmin/overview",
    "http://127.0.0.1:5005/api/superadmin/users",
    "http://127.0.0.1:5005/api/superadmin/system",
    "http://127.0.0.1:5005/api/personas"
]

print(">>> Starting Endpoint Validation...")
for url in endpoints:
    print(f"\nChecking URL: {url}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as res:
            status = res.status
            body = res.read().decode('utf-8')
            print(f"Status Code: {status}")
            try:
                data = json.loads(body)
                print(f"JSON Output is valid! Response: {data}")
            except Exception as je:
                print(f"Non-JSON body returned: {body[:300]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        print(f"HTTP Status Code: {e.code}")
        try:
            data = json.loads(body)
            print(f"JSON Output is valid (Error response)!: {data}")
        except Exception as je:
            print(f"Non-JSON error body: {body[:500]}")
    except Exception as e:
        print(f"Request failed: {e}")
