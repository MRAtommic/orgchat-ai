import sys
import os

# Add the directory to sys.path so we can import from webai
sys.path.append(os.path.abspath("."))

import database

try:
    events = database.get_events(limit=100)
    print(f"Success! Retrieved {len(events)} events.")
    print("First event:", events[0] if events else "None")
except Exception as e:
    import traceback
    print("Failed with exception:")
    traceback.print_exc()
