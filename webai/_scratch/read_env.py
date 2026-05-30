import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

paths = ['.env', '../.env', 'line_config.json']
for p in paths:
    if os.path.exists(p):
        print(f"--- File: {p} ---")
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if 'LINE' in line or 'BOT' in line or 'PUNCH' in line or 'SECRET' in line:
                    print(line.strip())
