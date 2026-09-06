# backend/auth.py
"""Authentication features: 2FA, session timeout, password reset."""
import hashlib
import secrets
import io
import base64
from datetime import datetime, timedelta
from functools import wraps

import pyotp
import qrcode
from flask import session, jsonify

from backend.db import get_session
from backend.models import User, AccessLog

import bcrypt

def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")

def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("ascii"))
    except ValueError:
        return False
    
SESSION_TIMEOUT_MINUTES = 15
RESET_TOKEN_EXPIRY_MINUTES = 30
MAX_2FA_ATTEMPTS = 5


def _log(db_sess, user_id: int | None, action: str, status: str):
    db_sess.add(AccessLog(user_id=user_id, record_id=None, action=action, status=status))


# ---------- TWO-FACTOR AUTHENTICATION ----------

def generate_2fa_secret(user_id: int):
    secret = pyotp.random_base32()
    with get_session() as db_sess:
        user = db_sess.query(User).filter_by(user_id=user_id).first()
        if not user:
            return None
        user.two_factor_secret = secret
        user.two_factor_enabled = False
        email = user.email

    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=email, issuer_name="DBShield")
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return secret, base64.b64encode(buf.getvalue()).decode()


def verify_2fa_code(user_id: int, code: str) -> dict:
    with get_session() as db_sess:
        user = db_sess.query(User).filter_by(user_id=user_id).first()
        if not user or not user.two_factor_secret:
            return {"status": "error", "message": "2FA not set up"}

        if user.failed_2fa_count >= MAX_2FA_ATTEMPTS:
            _log(db_sess, user.user_id, "2fa_verify", "locked_out")
            return {"status": "error", "message": "Too many attempts. Please log in again."}

        totp = pyotp.TOTP(user.two_factor_secret)
        valid = totp.verify(code, valid_window=1)

        if valid:
            user.failed_2fa_count = 0
            user.two_factor_enabled = True
            _log(db_sess, user.user_id, "2fa_verify", "success")
            return {"status": "success"}

        user.failed_2fa_count += 1
        _log(db_sess, user.user_id, "2fa_verify", "failed")
        return {"status": "error", "message": "Invalid code"}


# ---------- SESSION TIMEOUT ----------

def touch_session():
    session['last_activity'] = datetime.utcnow().isoformat()

def is_session_expired() -> bool:
    last = session.get('last_activity')
    if not last:
        return True
    return datetime.utcnow() - datetime.fromisoformat(last) > timedelta(minutes=SESSION_TIMEOUT_MINUTES)

def require_active_session(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "Please login first"}), 401
        if is_session_expired():
            session.clear()
            return jsonify({"status": "error", "message": "Session expired, please login again"}), 401
        touch_session()
        return f(*args, **kwargs)
    return wrapper


# ---------- PASSWORD RESET ----------

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def generate_reset_token(email: str):
    token = secrets.token_urlsafe(32)
    with get_session() as db_sess:
        user = db_sess.query(User).filter_by(email=email).first()
        if not user:
            return None
        user.reset_token_hash = _hash_token(token)
        user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRY_MINUTES)
        _log(db_sess, user.user_id, "password_reset_request", "issued")
    return token


def reset_password(email: str, token: str, new_plain_password: str, hash_password_fn) -> bool:
    """hash_password_fn: pass in Hardie's hashing function so this stays decoupled from his code."""
    with get_session() as db_sess:
        user = db_sess.query(User).filter_by(email=email).first()
        if not user or not user.reset_token_hash:
            return False
        if not secrets.compare_digest(user.reset_token_hash, _hash_token(token)):
            _log(db_sess, user.user_id, "password_reset", "failed")
            return False
        if not user.reset_token_expiry or datetime.utcnow() > user.reset_token_expiry:
            _log(db_sess, user.user_id, "password_reset", "expired")
            return False

        user.password_hash = hash_password_fn(new_plain_password)
        user.reset_token_hash = None
        user.reset_token_expiry = None
        _log(db_sess, user.user_id, "password_reset", "success")
        return True