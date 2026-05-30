import os
import sys
sys.path.append('.')
import database

database.init_db()
print("OS ENV LINE_CHANNEL_ACCESS_TOKEN:", os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", ""))
print("DB APP SETTING LINE_CHANNEL_ACCESS_TOKEN:", database.get_app_setting("LINE_CHANNEL_ACCESS_TOKEN", ""))
