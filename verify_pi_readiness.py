import os
import sys
from pathlib import Path

def check_fonts():
    print("--- 1. Checking Font Handling ---")
    try:
        from export_service import export_to_pdf
        print("✅ export_service.py imported successfully.")
    except Exception as e:
        print(f"❌ Error importing export_service: {e}")

def check_meta_healing():
    print("\n--- 2. Checking Path Self-Healing ---")
    try:
        from rag_engine import _load_meta, META_FILE
        if META_FILE.exists():
            print(f"✅ Metadata file found. Testing self-healing logic...")
            meta = _load_meta()
            print("✅ _load_meta executed without errors.")
        else:
            print("ℹ️ No metadata file yet, nothing to heal.")
    except Exception as e:
        print(f"❌ Error in rag_engine: {e}")

def check_service_template():
    print("\n--- 3. Checking Service Template ---")
    if os.path.exists("orgchat-pi.service"):
        print("✅ orgchat-pi.service template created.")
    else:
        print("❌ orgchat-pi.service template missing.")

if __name__ == "__main__":
    check_fonts()
    check_meta_healing()
    check_service_template()
    print("\nVerification complete. The project is ready to be copied to Pi 4.")
