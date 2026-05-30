import os

print("--- LINE ENV VARS ---")
for k, v in os.environ.items():
    if 'LINE' in k or 'BOT' in k or 'PUNCH' in k or 'พั้น' in k:
        print(f"{k}: {v}")
