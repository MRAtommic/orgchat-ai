import os
import re
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Absolute path เทียบกับ directory ของไฟล์นี้ ป้องกันการ resolve ผิดที่เมื่อ cwd ต่างกัน
ENV_PATH = str(Path(__file__).parent / ".env")

def get_settings():
    """Read .env file and return a dictionary of settings."""
    settings = {}
    if not os.path.exists(ENV_PATH):
        return settings
    
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                settings[key.strip()] = value.strip()
    return settings

def update_settings(new_settings):
    """
    Update .env file with new settings.
    Preserves comments and existing order where possible.
    """
    if not os.path.exists(ENV_PATH):
        # Create new if doesn't exist — write atomically via temp file
        env_dir = os.path.dirname(ENV_PATH)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=env_dir, delete=False) as tmp:
            for k, v in new_settings.items():
                tmp.write(f"{k}={v}\n")
            tmp_path = tmp.name
        os.replace(tmp_path, ENV_PATH)
        _orig_db_set = os.environ.get("DB_PATH")
        load_dotenv(ENV_PATH, override=True, encoding="utf-8")
        if _orig_db_set:
            os.environ["DB_PATH"] = _orig_db_set
        return True

    with open(ENV_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated_keys = set()
    new_lines = []

    for line in lines:
        match = re.match(r"^(\s*([A-Za-z0-9_]+)\s*=)(.*)$", line)
        if match:
            prefix = match.group(1)
            key = match.group(2)
            if key in new_settings:
                new_lines.append(f"{key}={new_settings[key]}\n")
                updated_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Add new keys that weren't in the file
    for k, v in new_settings.items():
        if k not in updated_keys:
            new_lines.append(f"{k}={v}\n")

    # Atomic write: ป้องกัน .env เสียหายถ้า process crash ระหว่างเขียน
    env_dir = os.path.dirname(ENV_PATH) or "."
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=env_dir, delete=False) as tmp:
        tmp.writelines(new_lines)
        tmp_path = tmp.name
    os.replace(tmp_path, ENV_PATH)

    # Reload environment variables in current process
    _orig_db_set = os.environ.get("DB_PATH")
    load_dotenv(ENV_PATH, override=True, encoding="utf-8")
    if _orig_db_set:
        os.environ["DB_PATH"] = _orig_db_set
    
    # Manually update os.environ just to be sure for immediate use
    for k, v in new_settings.items():
        os.environ[k] = str(v)
        
    return True
