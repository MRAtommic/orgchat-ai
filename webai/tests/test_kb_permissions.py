# -*- coding: utf-8 -*-
"""สิทธิ์คลังความรู้: superadmin ต้องมีสิทธิ์ดู/แก้/ลบเท่าแอดมิน (เดิมได้ 403 เพราะตรวจแค่ role == 'admin')"""
import pytest

import database
from routes import shared


@pytest.fixture()
def ctx():
    import app_server
    return app_server.app


def _with_role(app, monkeypatch, role, **flags):
    monkeypatch.setattr(database, "get_user_setting", lambda u: {"role": role, **flags})
    return app.test_request_context("/")


@pytest.mark.parametrize("role,expected", [("admin", True), ("superadmin", True), ("user", False)])
def test_role_grants(ctx, monkeypatch, role, expected):
    with _with_role(ctx, monkeypatch, role):
        from flask import session
        session["user"] = "someone"
        assert shared.can_view_knowledge_base() is expected
        assert shared.can_edit_knowledge_base() is expected
        assert shared.can_delete_knowledge_base() is expected


def test_user_flags_still_work(ctx, monkeypatch):
    with _with_role(ctx, monkeypatch, "user", can_view_kb=True):
        from flask import session
        session["user"] = "someone"
        assert shared.can_view_knowledge_base() is True
        assert shared.can_edit_knowledge_base() is False
        assert shared.can_delete_knowledge_base() is False


def test_anonymous_denied(ctx, monkeypatch):
    with _with_role(ctx, monkeypatch, "superadmin"):
        assert shared.can_view_knowledge_base() is False
