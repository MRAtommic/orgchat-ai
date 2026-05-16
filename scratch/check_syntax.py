import py_compile
import traceback

try:
    py_compile.compile(r'c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\app_server.py', doraise=True)
    print("Compilation successful!")
except py_compile.PyCompileError as e:
    print(f"Compilation failed: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
    traceback.print_exc()
