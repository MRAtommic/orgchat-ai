import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load .env variables
with open(".env", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

smtp_server = os.environ.get("SMTP_SERVER", "").strip()
smtp_port = os.environ.get("SMTP_PORT", "").strip()
smtp_user = os.environ.get("SMTP_USER", "").strip()
smtp_password = os.environ.get("SMTP_PASSWORD", "").strip()
smtp_sender = os.environ.get("SMTP_SENDER", smtp_user).strip()

print("SMTP Server:", smtp_server)
print("SMTP Port:", smtp_port)
print("SMTP User:", smtp_user)
print("SMTP Password length:", len(smtp_password))
print("SMTP Sender:", smtp_sender)

to_email = "mxmm2547@gmail.com"
org_name = "Heartwarming Co."
invited_by = "Admin"

try:
    port = int(smtp_port) if smtp_port else 587
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Test email from OrgChat AI"
    msg["From"] = f"OrgChat AI <{smtp_sender}>"
    msg["To"] = to_email
    
    html_content = "<h1>Hello from OrgChat AI!</h1><p>This is a test email.</p>"
    msg.attach(MIMEText(html_content, "html"))
    
    print("Connecting to SMTP server...")
    if port == 465:
        server = smtplib.SMTP_SSL(smtp_server, port, timeout=10)
    else:
        server = smtplib.SMTP(smtp_server, port, timeout=10)
        server.starttls()
        
    print("Logging in...")
    server.login(smtp_user, smtp_password)
    
    print("Sending mail...")
    server.sendmail(smtp_sender, [to_email], msg.as_string())
    server.quit()
    print("SUCCESS: Email sent successfully!")
except Exception as e:
    import traceback
    print("ERROR: Failed to send email:")
    traceback.print_exc()
