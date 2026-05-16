import os
import re
from dotenv import load_dotenv

ENV_PATH = ".env"

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
        # Create new if doesn't exist
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            for k, v in new_settings.items():
                f.write(f"{k}={v}\n")
        load_dotenv(ENV_PATH, override=True)
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

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    # Reload environment variables in current process
    load_dotenv(ENV_PATH, override=True)
    
    # Manually update os.environ just to be sure for immediate use
    for k, v in new_settings.items():
        os.environ[k] = str(v)
        
    return True
