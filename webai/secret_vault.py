# -*- coding: utf-8 -*-
"""Encrypt small secrets (e.g. TOTP seeds) at rest.

Format: "enc:v1:<fernet token>". Values without the prefix are treated as legacy plaintext, so existing
accounts keep working and are upgraded the next time they verify successfully.

Key: TOTP_ENCRYPTION_KEY if set, otherwise the app's FLASK_SECRET_KEY / SECRET_KEY. If no stable key is
configured (the app would then use a random key per restart) we DO NOT encrypt, because the data could never
be decrypted again after a restart.
"""
import base64
import hashlib
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger("OrgChatAI")
PREFIX = "enc:v1:"
_PLAIN_MARKERS = {"EMAIL_OTP"}


def _raw_key() -> str:
    return (os.environ.get("TOTP_ENCRYPTION_KEY") or os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY") or "").strip()


def _fernet():
    raw = _raw_key()
    if not raw:
        return None
    digest = hashlib.sha256(("orgchat-secret-vault|" + raw).encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def is_encrypted(value) -> bool:
    return isinstance(value, str) and value.startswith(PREFIX)


def can_encrypt() -> bool:
    return _fernet() is not None


def encrypt(value: str) -> str:
    """Return the encrypted form, or the value unchanged when it is empty / a marker / already encrypted / no stable key."""
    if not value or value in _PLAIN_MARKERS or is_encrypted(value):
        return value
    f = _fernet()
    if f is None:
        logger.warning("secret_vault: no FLASK_SECRET_KEY/TOTP_ENCRYPTION_KEY set - storing secret unencrypted")
        return value
    return PREFIX + f.encrypt(value.encode("utf-8")).decode("ascii")


def decrypt(value: str) -> str:
    """Return the plaintext. Legacy plaintext passes through. A value that cannot be decrypted returns ''."""
    if not is_encrypted(value):
        return value or ""
    f = _fernet()
    if f is None:
        return ""
    try:
        return f.decrypt(value[len(PREFIX):].encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        logger.error("secret_vault: cannot decrypt value (encryption key changed?)")
        return ""
