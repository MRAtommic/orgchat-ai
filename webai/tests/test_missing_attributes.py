# -*- coding: utf-8 -*-
"""
Regression test for Category 6: Undefined Names & Missing Database Attributes.
Verifies:
1. database.get_organization_by_id exists and maps to get_org
2. database.kanban_get_or_create_board exists and maps to kanban_get_board
3. database.get_attendance_records exists and returns attendance
4. database.get_organization_profile exists and maps to get_org_profile
5. AST scan across all Python files finds 0 missing database.* calls
"""
import ast
from pathlib import Path
import pytest
import database

ROOT = Path(__file__).resolve().parent.parent

def test_missing_database_attributes_regression():
    # 1. Direct function presence and aliases
    assert hasattr(database, "get_organization_by_id"), "database.get_organization_by_id must exist"
    assert database.get_organization_by_id is database.get_org

    assert hasattr(database, "kanban_get_or_create_board"), "database.kanban_get_or_create_board must exist"
    assert database.kanban_get_or_create_board is database.kanban_get_board

    assert hasattr(database, "get_attendance_records"), "database.get_attendance_records must exist"
    assert callable(database.get_attendance_records)

    assert hasattr(database, "get_organization_profile"), "database.get_organization_profile must exist"
    assert database.get_organization_profile is database.get_org_profile

def test_ast_scan_all_database_calls():
    from tools.scan_undefined_names import check_database_attributes
    targets = [ROOT / "routes", ROOT / "db", ROOT / "app_server.py", ROOT / "rag_engine.py", ROOT / "rag_query.py"]
    missing = check_database_attributes(targets)
    assert len(missing) == 0, f"Found missing database.* calls: {missing}"

