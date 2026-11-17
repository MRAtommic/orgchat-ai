# -*- coding: utf-8 -*-
"""Finds names that are used but never defined anywhere visible (runtime NameError candidates),
resolving `from x import *` by inspecting the imported modules' real namespaces (pyflakes cannot do that).

Usage (isolated, never touches real data):
    DB_PATH=<tmp>/x.db DATA_DIR=<tmp>/d VECTOR_BACKEND=python python tools/find_undefined_names.py
"""
import ast
import builtins
import os
import pathlib
import sys

assert os.environ.get("DB_PATH") and os.environ.get("DATA_DIR"), "set DB_PATH and DATA_DIR to temp locations first"
os.environ.setdefault("FLASK_SECRET_KEY", "x_test_secret_0123456789abcdef")
os.environ.setdefault("BASE_URL", "http://localhost:5999")
sys.path.insert(0, os.getcwd())
import app_server  # noqa: E402,F401  (imports routes/db/everything)

BUILT = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__class__"}
mods = []
for p in list(pathlib.Path(".").glob("*.py")) + list(pathlib.Path("routes").glob("*.py")) + list(pathlib.Path("db").glob("*.py")) + list(pathlib.Path("tasks").glob("*.py")):
    if p.name.startswith(("test", "_", "run_", "scratch")):
        continue
    name = p.with_suffix("").as_posix().replace("/", ".")
    if name in sys.modules:
        mods.append((name, p))


def local_names(fn):
    sc = set()
    a = fn.args
    for x in a.args + a.kwonlyargs + a.posonlyargs:
        sc.add(x.arg)
    if a.vararg:
        sc.add(a.vararg.arg)
    if a.kwarg:
        sc.add(a.kwarg.arg)
    for sub in ast.walk(fn):
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, (ast.Store, ast.Del)):
            sc.add(sub.id)
        elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and sub is not fn:
            sc.add(sub.name)
        elif isinstance(sub, ast.ExceptHandler) and sub.name:
            sc.add(sub.name)
        elif isinstance(sub, (ast.Import, ast.ImportFrom)):
            for al in sub.names:
                sc.add((al.asname or al.name).split(".")[0])
        elif isinstance(sub, ast.arg):
            sc.add(sub.arg)
        elif isinstance(sub, (ast.Global, ast.Nonlocal)):
            sc.update(sub.names)
    return sc


bad = set()
for name, p in mods:
    g = sys.modules[name].__dict__
    tree = ast.parse(p.read_text(encoding="utf-8"))

    class V(ast.NodeVisitor):
        def __init__(self):
            self.scopes = [set()]

        def visit_FunctionDef(self, n):
            for d in n.decorator_list:
                self.visit(d)
            self.scopes.append(local_names(n))
            for b in n.body:
                self.visit(b)
            self.scopes.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Lambda(self, n):
            self.scopes.append({x.arg for x in n.args.args} | {x.arg for x in n.args.kwonlyargs})
            self.visit(n.body)
            self.scopes.pop()

        def _comp(self, n):
            sc = set()
            for gen in n.generators:
                for sub in ast.walk(gen.target):
                    if isinstance(sub, ast.Name):
                        sc.add(sub.id)
            self.scopes.append(sc)
            self.generic_visit(n)
            self.scopes.pop()

        visit_ListComp = visit_SetComp = visit_DictComp = visit_GeneratorExp = _comp

        def visit_Name(self, n):
            if isinstance(n.ctx, ast.Load) and n.id not in g and n.id not in BUILT and not any(n.id in s for s in self.scopes):
                bad.add((name, n.lineno, n.id))

    V().visit(tree)

print(f"{len(bad)} possible NameErrors")
for b in sorted(bad):
    print(*b)
