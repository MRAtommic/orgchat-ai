# -*- coding: utf-8 -*-
"""
routes/__init__.py — Blueprint Registry
All Blueprints are imported here and registered in the app factory.
"""

from routes.auth import auth_bp
from routes.chat import chat_bp
from routes.line_webhook import line_bp
from routes.file_upload import file_bp
from routes.knowledge import knowledge_bp
from routes.quotation_crm import quotation_bp
from routes.social import social_bp
from routes.admin import admin_bp
from routes.misc import misc_bp
from routes.features import features_bp
from routes.org_admin import org_admin_bp

ALL_BLUEPRINTS = [
    auth_bp,
    chat_bp,
    line_bp,
    file_bp,
    knowledge_bp,
    quotation_bp,
    social_bp,
    admin_bp,
    misc_bp,
    features_bp,
    org_admin_bp,
]

