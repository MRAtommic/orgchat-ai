import requests

token = "ZfvRksmDJ4dEknlUGdhU+NkmnCH3wlHNDLyN6/7YwasAV/FAIQ7sTjwRkQGRoSxWpBlp2vArvluZAkgwjvVe5fPW/8VTnBqwt/C+eqWyCW5zSbf18+g2yZwIjBJDSY7YGWfEuMSZZTNd9mvBsDrvWgdB04t89/1O/w1cDnyilFU="
gid = "C4e1e6ebb9d4c0c9e87e2bf6bf97c0d93"

url = f"https://api.line.me/v2/bot/group/{gid}/summary"
headers = {"Authorization": f"Bearer {token}"}

print(f"Requesting {url}")
r = requests.get(url, headers=headers)
print("Status code:", r.status_code)
print("Response JSON:", r.text)
