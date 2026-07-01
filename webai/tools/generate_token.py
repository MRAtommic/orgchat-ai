import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# สิทธิ์ที่เราต้องการ (จัดการไฟล์ใน Drive และ Sheets)
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

def main():
    creds = None
    # ไฟล์ token.json จะถูกสร้างขึ้นหลังจากการล็อกอินสำเร็จ
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # ถ้ายังไม่มีกุญแจ หรือกุญแจหมดอายุ
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"⚠️ ไม่สามารถต่ออายุโทเคนเดิมได้ ({e})")
                print("⏳ กำลังเริ่มเข้าสู่ระบบใหม่...")
                creds = None
        
        if not creds or not creds.valid:
            if not os.path.exists('credentials.json'):
                print("❌ ไม่พบไฟล์ credentials.json! กรุณาดาวน์โหลดจาก Google Cloud Console มาวางในโฟลเดอร์นี้ก่อนครับ")
                return
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # บันทึกกุญแจไว้ใช้ครั้งต่อไป
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("✅ สร้างไฟล์ token.json สำเร็จเรียบร้อยแล้ว!")

if __name__ == '__main__':
    main()
