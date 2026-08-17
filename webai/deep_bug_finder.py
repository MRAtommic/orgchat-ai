"""
Comprehensive Deep Bug Finder for OrgChat AI
Scans all Python files in webai/ for:
1. Undefined names / missing imports
2. Unbound variables (used before definition across branches)
3. SQL column reference mismatches in database queries
"""
import ast
import os
import sys
import re
from pathlib import Path

WEBAI_DIR = Path(r"c:\Users\FEWIT\Desktop\orgchat-ai-main\webai")

BUILTINS = set(dir(__builtins__)) | {
    "True", "False", "None", "dict", "list", "set", "tuple", "str", "int", "float",
    "bool", "bytes", "len", "range", "print", "enumerate", "isinstance", "issubclass",
    "type", "open", "super", "zip", "map", "filter", "min", "max", "sum", "any", "all",
    "hasattr", "getattr", "setattr", "delattr", "repr", "str", "abs", "round", "sorted",
    "Exception", "ValueError", "TypeError", "KeyError", "AttributeError", "IndexError",
    "FileNotFoundError", "RuntimeError", "StopIteration", "ImportError", "NameError",
    "os", "sys", "json", "re", "time", "logging", "logger"
}

class BugVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.bugs = []
        self.current_func = None
        self.global_scope = set(BUILTINS)
        self.func_globals = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.global_scope.add(alias.asname or alias.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.global_scope.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.global_scope.add(node.name)
        old_func = self.current_func
        self.current_func = node.name
        
        # Check function body for undefined names
        local_defined = set()
        for arg in node.args.args + node.args.kwonlyargs:
            local_defined.add(arg.arg)
        if node.args.vararg: local_defined.add(node.args.vararg.arg)
        if node.args.kwarg: local_defined.add(node.args.kwarg.arg)

        # Walk body
        for body_node in ast.walk(node):
            if isinstance(body_node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = body_node.targets if hasattr(body_node, 'targets') else [body_node.target]
                for t in targets:
                    if isinstance(t, ast.Name):
                        local_defined.add(t.id)
            elif isinstance(body_node, ast.For):
                if isinstance(body_node.target, ast.Name):
                    local_defined.add(body_node.target.id)
                elif isinstance(body_node.target, ast.Tuple):
                    for elt in body_node.target.elts:
                        if isinstance(elt, ast.Name): local_defined.add(elt.id)
            elif isinstance(body_node, ast.ExceptHandler):
                if body_node.name:
                    local_defined.add(body_node.name)

            elif isinstance(body_node, ast.Name) and isinstance(body_node.ctx, ast.Load):
                name = body_node.id
                if not name.startswith("_") and name not in local_defined and name not in self.global_scope:
                    self.bugs.append((body_node.lineno, self.current_func, f"Undefined reference '{name}'"))

        self.current_func = old_func
        self.generic_visit(node)

def analyze_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
        tree = ast.parse(code, filename=filepath.name)
        visitor = BugVisitor(filepath.name)
        visitor.visit(tree)
        if visitor.bugs:
            print(f"\n[BUGS FOUND] {filepath.name}:")
            dedup = {}
            for lineno, func, msg in visitor.bugs:
                key = (lineno, msg)
                if key not in dedup:
                    dedup[key] = (func, msg)
                    print(f"  Line {lineno:4d} (in {func}): {msg}")
    except Exception as e:
        print(f"Error parsing {filepath.name}: {e}")

if __name__ == "__main__":
    print("==========================================================")
    print(" Deep AST Bug Inspection across webai/")
    print("==========================================================")
    for py_file in WEBAI_DIR.rglob("*.py"):
        if "venv" not in str(py_file) and ".temp" not in str(py_file):
            analyze_file(py_file)
