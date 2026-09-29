"""
AST Undefined Name & Missing Import Linter for OrgChat AI
Scans Python route files to catch NameError bugs (unimported modules/undefined variables).
"""
import ast
import sys
import os
from pathlib import Path

ROUTES_DIR = Path(r"c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\routes")

BUILTINS = set(dir(__builtins__)) | {
    "True", "False", "None", "dict", "list", "set", "tuple", "str", "int", "float",
    "bool", "bytes", "len", "range", "print", "enumerate", "isinstance", "issubclass",
    "type", "open", "super", "zip", "map", "filter", "min", "max", "sum", "any", "all",
    "hasattr", "getattr", "setattr", "delattr", "repr", "str", "abs", "round", "sorted",
    "Exception", "ValueError", "TypeError", "KeyError", "AttributeError", "IndexError",
    "FileNotFoundError", "RuntimeError", "StopIteration", "ImportError", "NameError",
    "os", "sys", "json", "re", "time", "logging", "logger"
}

def analyze_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    try:
        tree = ast.parse(code, filename=filepath.name)
    except SyntaxError as e:
        print(f"❌ Syntax Error in {filepath.name}: {e}")
        return

    imported_names = set(BUILTINS)
    
    # Collect imports and global definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            imported_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            imported_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    imported_names.add(target.id)

    undefined = []
    
    # Check variable/module usage inside function bodies
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id not in imported_names and not node.id.startswith("_"):
                undefined.append((node.lineno, node.id))

    if undefined:
        print(f"\n[WARNING] Potential Undefined Names / Missing Imports in {filepath.name}:")
        seen = set()
        for lineno, name in undefined:
            if name not in seen:
                print(f"   Line {lineno}: '{name}' is used but might not be imported or defined!")
                seen.add(name)
    else:
        print(f"[OK] {filepath.name}: Clean")


if __name__ == "__main__":
    print("==========================================================")
    print(" AST Code Audit: Scanning for Undefined References")
    print("==========================================================")
    for py_file in ROUTES_DIR.glob("*.py"):
        analyze_file(py_file)
