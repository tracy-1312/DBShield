from flask import Flask, request, jsonify, session
from backend.db import get_session
from backend.models import User
from backend.search import search_records
from backend.auth import (
    generate_2fa_secret,
    verify_2fa_code,
    require_active_session,
    touch_session,
    generate_reset_token,
    reset_password,
    hash_password,
    verify_password,
)
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")


def _record_to_dict(r):
    """Turn a SQLAlchemy row into a plain dict using only its real columns."""
    return {c.name: getattr(r, c.name) for c in r.__table__.columns}


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Use the User model from models.py
    with get_session() as db_sess:
        user = db_sess.query(User).filter_by(username=username).first()

        # Check the password against the stored bcrypt hash
        if user and verify_password(password, user.password_hash):
            session.clear()  # drop any leftover state from an earlier login
            session['user_id'] = user.user_id
            session['role'] = user.role
            session['clearance_level'] = user.clearance_level
            touch_session()  # starts the session-timeout clock
            user.failed_2fa_count = 0  # a fresh login resets the 2FA lockout

            if user.two_factor_enabled:
                session['awaiting_2fa'] = True
                return jsonify({
                    "status": "success",
                    "message": "2FA required",
                    "requires_2fa": True
                }), 200

            return jsonify({"status": "success", "message": f"Welcome {user.full_name}"}), 200

    return jsonify({"status": "error", "message": "Invalid credentials"}), 401


# ---------- TWO-FACTOR AUTHENTICATION ----------

@app.route('/2fa/setup', methods=['POST'])
@require_active_session
def setup_2fa():
    result = generate_2fa_secret(session['user_id'])
    if not result:
        return jsonify({"status": "error", "message": "User not found"}), 404
    secret, qr_code = result
    # lets the user confirm their first code on /2fa/verify
    session['setting_up_2fa'] = True
    return jsonify({"status": "success", "qr_code": qr_code})


@app.route('/2fa/verify', methods=['POST'])
def verify_2fa():
    # Deliberately not @require_active_session: at login time the user isn't
    # fully signed in yet. Either 'awaiting_2fa' (logging in with 2FA on) or
    # 'setting_up_2fa' (confirming first-time setup) must be set.
    if 'user_id' not in session or not (
        session.get('awaiting_2fa') or session.get('setting_up_2fa')
    ):
        return jsonify({"status": "error", "message": "No 2FA verification pending"}), 400

    code = request.json.get('code')
    result = verify_2fa_code(session['user_id'], code)

    if result["status"] == "success":
        session.pop('awaiting_2fa', None)
        session.pop('setting_up_2fa', None)
        touch_session()
        return jsonify(result)

    return jsonify(result), 400


# ---------- PASSWORD RESET ----------

@app.route('/reset-password/request', methods=['POST'])
def request_password_reset():
    email = request.json.get('email')
    generate_reset_token(email)
    # Same message whether or not the email exists, so we don't leak
    # which emails are registered.
    # TODO: actually send the token via email once that's set up.
    return jsonify({
        "status": "success",
        "message": "If that email exists, a reset link was sent"
    })


@app.route('/reset-password/confirm', methods=['POST'])
def confirm_password_reset():
    data = request.json
    success = reset_password(
        data['email'],
        data['token'],
        data['new_password'],
        hash_password,
    )
    if success:
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid or expired token"}), 400


# ---------- SEARCH (session-timeout protected) ----------

@app.route('/search', methods=['GET'])
@require_active_session
def search():
    with get_session() as db_sess:
        user = db_sess.query(User).filter_by(user_id=session['user_id']).first()

        results = search_records(
            db_sess,
            user,
            keyword=request.args.get('q'),
            search_notes=True
        )

        return jsonify({
            "status": "success",
            "count": len(results),
            "data": [r.to_dict() if hasattr(r, 'to_dict') else _record_to_dict(r) for r in results]
        })


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"status": "success", "message": "Logged out"})


if __name__ == '__main__':
    app.run(debug=False, port=5000)