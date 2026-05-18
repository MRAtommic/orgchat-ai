import sys
sys.path.insert(0, '.')
import database

webhook_url = database.get_app_setting("LINE_WEBHOOK_URL", "")
print("LINE_WEBHOOK_URL:", webhook_url)
