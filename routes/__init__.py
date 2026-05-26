# -*- coding: utf-8 -*-
"""
routes/__init__.py — Blueprint Registry
All Blueprints are imported here and registered in the app factory.
"""

from routes.auth import auth_bp
from routes.chat import chat_bp
from routes.social import social_bp
from routes.admin import admin_bp
from routes.misc import misc_bp

ALL_BLUEPRINTS = [
    auth_bp,
    chat_bp,
    social_bp,
    admin_bp,
    misc_bp,
]
