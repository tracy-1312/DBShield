"""Encryption layer for DBShield.

Sensitive fields are encrypted with Fernet (AES-128-CBC + HMAC) before
they reach the database and decrypted when read back. EncryptedText
plugs into a SQLAlchemy column so this happens transparently.
"""

import os

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

load_dotenv()

_KEY = os.getenv("DBSHIELD_KEY")
if not _KEY:
    raise RuntimeError(
        "DBSHIELD_KEY missing from .env. Generate one with:\n"
        "  python -c \"from cryptography.fernet import Fernet; "
        "print(Fernet.generate_key().decode())\""
    )

_fernet = Fernet(_KEY.encode())


def encrypt(plaintext: str | None) -> str | None:
    """Encrypt a string. None passes through untouched."""
    if plaintext is None:
        return None
    return _fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt(token: str | None) -> str | None:
    """Decrypt a Fernet token.

    Returns a placeholder rather than raising if the value is not valid
    ciphertext, so legacy plaintext rows or a wrong key cannot crash a
    whole page of search results.
    """
    if token is None:
        return None
    try:
        return _fernet.decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError, ValueError):
        return "[unable to decrypt]"


class EncryptedText(TypeDecorator):
    """A Text column that encrypts on write and decrypts on read."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return encrypt(value)

    def process_result_value(self, value, dialect):
        return decrypt(value)