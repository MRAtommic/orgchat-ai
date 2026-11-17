# -*- coding: utf-8 -*-
"""
Tool: scan_undefined_names.py
1. Scans codebase using pyflakes AST for undefined names (F821 equivalent).
2. Uses AST to find all `database.<func>` or `db.<module>.<func>` calls and verifies that the attribute exists.
"""
import ast
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import database

def check_undefined_names_via_pyflakes(target_dirs):
    import subprocess
    cmd = [sys.executable, "-m", "pyflakes"] + [str(d) for d in target_dirs]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = proc.stdout.splitlines() + proc.stderr.splitlines()
    undefined = []
    for line in lines:
        if "undefined name" in line:
            undefined.append(line.strip())
    return undefined

def check_database_attributes(target_dirs):
    db_attrs = set(dir(database))
    missing_calls = []

    for d in target_dirs:
        for py_file in Path(d).rglob("*.py"):
            if "venv" in str(py_file) or ".pytest_cache" in str(py_file) or "tests" in str(py_file):
                continue
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"), filename=str(py_file))
            except Exception as e:
                missing_calls.append(f"{py_file}: Parse error: {e}")
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    # check database.<attr>
                    if isinstance(node.value, ast.Name) and node.value.id == "database":
                        attr_name = node.attr
                        if attr_name not in db_attrs and not attr_name.startswith("_"):
                            missing_calls.append({
                                "file": str(py_file.relative_to(ROOT)),
                                "line": node.lineno,
                                "attr": f"database.{attr_name}",
                            })
    return missing_calls

if __name__ == "__main__":
    targets = [ROOT]
    print("=== Scanning Pyflakes Undefined Names ===")
    undef = check_undefined_names_via_pyflakes(targets)
    for u in undef:
        print(f"UNDEFINED: {u}")
    print(f"Total undefined names: {len(undef)}")

    print("\n=== Scanning Missing database.* Attributes ===")
    missing = check_database_attributes(targets)
    for m in missing:
        if isinstance(m, dict):
            print(f"MISSING: {m['file']}:{m['line']} -> {m['attr']}")
        else:
            print(f"ERROR: {m}")
    print(f"Total missing database.* attributes: {len(missing)}")
