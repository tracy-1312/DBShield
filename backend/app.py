from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import bcrypt
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError
from flask import Flask, jsonify, redirect, request, send_from_directory, session as flask_session

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(Path(__file__).with_name(".env"))

from backend.db import get_session
from backend.models import PatientRecord, User
from backend.search import get_record, log_action, search_records as run_search

ALLOWED_ORIGINS = {
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
}
LOCAL_FRONTEND_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0"}


def is_allowed_origin(origin: str | None) -> bool:
    if not origin:
        return False
    if origin in ALLOWED_ORIGINS:
        return True
    parsed = urlparse(origin)
    return parsed.scheme == "http" and parsed.hostname in LOCAL_FRONTEND_HOSTS

app = Flask(__name__)
secret_key = os.getenv("FLASK_SECRET_KEY")
if not secret_key:
    raise RuntimeError("FLASK_SECRET_KEY must be set in backend/.env before running DBShield.")
app.secret_key = secret_key
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def verify_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def record_to_dict(record: PatientRecord, user: User | None = None) -> dict:
    is_restricted = bool(
        user
        and user.role != "admin"
        and record.classification_level > user.clearance_level
    )
    access = "restricted" if is_restricted else "permitted"

    if is_restricted:
        return {
            "record_id": record.record_id,
            "patient_id": record.patient_id,
            "full_name": "Restricted Record",
            "date_of_birth": "Restricted",
            "category": record.category or "",
            "classification_level": record.classification_level,
            "classification": f"Level {record.classification_level}",
            "access": access,
            "contact_number": "Restricted",
            "email": "Restricted",
            "medical_notes": "Access denied. Submit an access request to view this record.",
            "assigned_doctor": "Restricted",
            "last_modified": "",
        }

    return {
        "record_id": record.record_id,
        "patient_id": record.patient_id,
        "full_name": record.full_name,
        "date_of_birth": record.date_of_birth.isoformat() if record.date_of_birth else "",
        "category": record.category or "",
        "classification_level": record.classification_level,
        "classification": f"Level {record.classification_level}",
        "access": access,
        "contact_number": record.contact_number or "",
        "email": record.email or "",
        "medical_notes": record.medical_notes or "No notes available",
        "assigned_doctor": record.assigned_doctor or "",
        "last_modified": record.last_modified.isoformat() if record.last_modified else "",
    }


def user_to_dict(user: User) -> dict:
    return {
        "user_id": user.user_id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "clearance_level": user.clearance_level,
    }


def current_user(db_session):
    user_id = flask_session.get("user_id")
    if not user_id:
        return None
    return db_session.query(User).filter_by(user_id=user_id).first()


def require_admin(db_session):
    user = current_user(db_session)
    if not user:
        return None, (jsonify({"status": "error", "message": "Please login first"}), 401)
    if user.role != "admin":
        return user, (jsonify({"status": "error", "message": "Admin access required"}), 403)
    return user, None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def role_label(role: str) -> str:
    return {
        "admin": "Admin",
        "data_manager": "Staff",
        "viewer": "Specialist",
    }.get(role, role.replace("_", " ").title())


def admin_user_to_dict(user: User) -> dict:
    payload = user_to_dict(user)
    payload["role_label"] = role_label(user.role)
    payload["classification"] = f"Level {user.clearance_level}"
    return payload


@app.route("/")
def index():
    return redirect("/frontend/auth/sign_in/index.html")


@app.route("/frontend/<path:filename>")
def frontend_file(filename):
    return send_from_directory(FRONTEND_ROOT, filename)


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if is_allowed_origin(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    if request.path == "/" or request.path.startswith("/frontend/"):
        response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@app.route("/api/<path:_path>", methods=["OPTIONS"])
def options_preflight(_path):
    return ("", 204)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "success", "message": "DBShield backend is running"})


@app.route("/api/login", methods=["POST"])
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    with get_session() as db_session:
        user = db_session.query(User).filter_by(username=username).first()
        if user and verify_password(password, user.password_hash):
            flask_session["user_id"] = user.user_id
            flask_session["role"] = user.role
            flask_session["clearance_level"] = user.clearance_level
            return jsonify({
                "status": "success",
                "message": f"Welcome {user.full_name}",
                "user": user_to_dict(user),
            }), 200

    return jsonify({"status": "error", "message": "Invalid credentials"}), 401


@app.route("/api/me", methods=["GET"])
def me():
    with get_session() as db_session:
        user = current_user(db_session)
        if not user:
            return jsonify({"status": "error", "message": "Please login first"}), 401
        return jsonify({"status": "success", "user": user_to_dict(user)})


@app.route("/api/search", methods=["GET"])
@app.route("/search", methods=["GET"])
def search():
    if "user_id" not in flask_session:
        return jsonify({"status": "error", "message": "Please login first"}), 401

    with get_session() as db_session:
        user = current_user(db_session)
        if not user:
            return jsonify({"status": "error", "message": "Please login first"}), 401

        max_classification = request.args.get("max_classification")
        results = run_search(
            db_session,
            user,
            keyword=request.args.get("q") or None,
            category=request.args.get("category") or None,
            max_classification=int(max_classification) if max_classification else None,
            search_notes=True,
        )

        return jsonify({
            "status": "success",
            "count": len(results),
            "user": user_to_dict(user),
            "data": [record_to_dict(record, user) for record in results],
        })


@app.route("/api/records/<patient_id>", methods=["GET", "PUT"])
def record_detail(patient_id):
    if "user_id" not in flask_session:
        return jsonify({"status": "error", "message": "Please login first"}), 401

    with get_session() as db_session:
        user = current_user(db_session)
        if not user:
            return jsonify({"status": "error", "message": "Please login first"}), 401

        record = db_session.query(PatientRecord).filter_by(patient_id=patient_id).first()
        if record is None:
            return jsonify({"status": "error", "message": "Record not found"}), 404

        permitted_record = get_record(db_session, user, record.record_id)
        if permitted_record is None:
            return jsonify({"status": "error", "message": "Access denied for this record"}), 403

        if request.method == "PUT":
            if user.role not in {"admin", "data_manager"}:
                log_action(db_session, user, "edit", record.record_id, "denied")
                return jsonify({"status": "error", "message": "You do not have permission to edit this record"}), 403

            data = request.get_json(silent=True) or {}
            if "date_of_birth" in data:
                value = str(data.get("date_of_birth") or "").strip()
                if value:
                    try:
                        record.date_of_birth = date.fromisoformat(value)
                    except ValueError:
                        return jsonify({"status": "error", "message": "Date of birth must use YYYY-MM-DD format"}), 400
                else:
                    record.date_of_birth = None

            editable_fields = {
                "full_name": "full_name",
                "contact_number": "contact_number",
                "email": "email",
                "assigned_doctor": "assigned_doctor",
                "category": "category",
                "medical_notes": "medical_notes",
            }
            for payload_key, model_field in editable_fields.items():
                if payload_key in data:
                    setattr(record, model_field, str(data.get(payload_key) or "").strip())

            log_action(db_session, user, "edit", record.record_id, "success")
            db_session.flush()

        return jsonify({
            "status": "success",
            "user": user_to_dict(user),
            "record": record_to_dict(record, user),
        })


@app.route("/api/admin/users", methods=["GET", "POST"])
def admin_users():
    with get_session() as db_session:
        admin_user, error = require_admin(db_session)
        if error:
            return error

        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            required = ["username", "full_name", "email", "role", "clearance_level", "password"]
            missing = [field for field in required if not str(data.get(field) or "").strip()]
            if missing:
                return jsonify({"status": "error", "message": f"Missing fields: {', '.join(missing)}"}), 400

            try:
                clearance_level = int(data.get("clearance_level"))
            except (TypeError, ValueError):
                return jsonify({"status": "error", "message": "Classification level must be a number"}), 400

            if clearance_level < 1 or clearance_level > 4:
                return jsonify({"status": "error", "message": "Classification level must be between 1 and 4"}), 400

            role = str(data.get("role") or "").strip()
            if role not in {"admin", "data_manager", "viewer"}:
                return jsonify({"status": "error", "message": "Invalid role"}), 400

            new_user = User(
                username=str(data.get("username") or "").strip(),
                password_hash=hash_password(str(data.get("password") or "")),
                full_name=str(data.get("full_name") or "").strip(),
                email=str(data.get("email") or "").strip(),
                role=role,
                clearance_level=clearance_level,
            )
            db_session.add(new_user)
            try:
                db_session.flush()
            except IntegrityError:
                db_session.rollback()
                return jsonify({"status": "error", "message": "Username already exists"}), 409

            return jsonify({"status": "success", "user": admin_user_to_dict(new_user)}), 201

        users = db_session.query(User).order_by(User.user_id).all()
        return jsonify({
            "status": "success",
            "user": user_to_dict(admin_user),
            "data": [admin_user_to_dict(item) for item in users],
        })


@app.route("/api/admin/users/<int:user_id>", methods=["PUT", "DELETE"])
def admin_user_detail(user_id):
    with get_session() as db_session:
        admin_user, error = require_admin(db_session)
        if error:
            return error

        target = db_session.query(User).filter_by(user_id=user_id).first()
        if not target:
            return jsonify({"status": "error", "message": "User not found"}), 404

        if request.method == "DELETE":
            if target.user_id == admin_user.user_id:
                return jsonify({"status": "error", "message": "You cannot delete the currently signed-in admin"}), 400
            db_session.delete(target)
            return jsonify({"status": "success", "message": "User deleted"})

        data = request.get_json(silent=True) or {}
        if "username" in data:
            target.username = str(data.get("username") or "").strip()
        if "full_name" in data:
            target.full_name = str(data.get("full_name") or "").strip()
        if "email" in data:
            target.email = str(data.get("email") or "").strip()
        if "role" in data:
            role = str(data.get("role") or "").strip()
            if role not in {"admin", "data_manager", "viewer"}:
                return jsonify({"status": "error", "message": "Invalid role"}), 400
            target.role = role
        if "clearance_level" in data:
            try:
                clearance_level = int(data.get("clearance_level"))
            except (TypeError, ValueError):
                return jsonify({"status": "error", "message": "Classification level must be a number"}), 400
            if clearance_level < 1 or clearance_level > 4:
                return jsonify({"status": "error", "message": "Classification level must be between 1 and 4"}), 400
            target.clearance_level = clearance_level
        if str(data.get("password") or "").strip():
            target.password_hash = hash_password(str(data.get("password") or ""))

        try:
            db_session.flush()
        except IntegrityError:
            db_session.rollback()
            return jsonify({"status": "error", "message": "Username already exists"}), 409

        return jsonify({"status": "success", "user": admin_user_to_dict(target)})


@app.route("/api/admin/records", methods=["GET", "POST"])
def admin_records():
    with get_session() as db_session:
        admin_user, error = require_admin(db_session)
        if error:
            return error

        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            required = ["patient_id", "full_name", "category", "classification_level"]
            missing = [field for field in required if not str(data.get(field) or "").strip()]
            if missing:
                return jsonify({"status": "error", "message": f"Missing fields: {', '.join(missing)}"}), 400

            try:
                classification_level = int(data.get("classification_level"))
            except (TypeError, ValueError):
                return jsonify({"status": "error", "message": "Classification level must be a number"}), 400

            if classification_level < 1 or classification_level > 4:
                return jsonify({"status": "error", "message": "Classification level must be between 1 and 4"}), 400

            dob = None
            dob_value = str(data.get("date_of_birth") or "").strip()
            if dob_value:
                try:
                    dob = date.fromisoformat(dob_value)
                except ValueError:
                    return jsonify({"status": "error", "message": "Date of birth must use YYYY-MM-DD format"}), 400

            record = PatientRecord(
                patient_id=str(data.get("patient_id") or "").strip(),
                full_name=str(data.get("full_name") or "").strip(),
                date_of_birth=dob,
                category=str(data.get("category") or "").strip(),
                classification_level=classification_level,
                contact_number=str(data.get("contact_number") or "").strip(),
                email=str(data.get("email") or "").strip(),
                medical_notes=str(data.get("medical_notes") or "").strip(),
                assigned_doctor=str(data.get("assigned_doctor") or "").strip(),
            )
            db_session.add(record)
            try:
                db_session.flush()
            except IntegrityError:
                db_session.rollback()
                return jsonify({"status": "error", "message": "Patient ID already exists"}), 409
            log_action(db_session, admin_user, "edit", record.record_id, "success")
            return jsonify({"status": "success", "record": record_to_dict(record, admin_user)}), 201

        records = db_session.query(PatientRecord).order_by(PatientRecord.patient_id).all()
        return jsonify({
            "status": "success",
            "user": user_to_dict(admin_user),
            "data": [record_to_dict(record, admin_user) for record in records],
        })


@app.route("/api/admin/records/<patient_id>", methods=["DELETE"])
def admin_record_delete(patient_id):
    with get_session() as db_session:
        admin_user, error = require_admin(db_session)
        if error:
            return error

        record = db_session.query(PatientRecord).filter_by(patient_id=patient_id).first()
        if not record:
            return jsonify({"status": "error", "message": "Record not found"}), 404
        log_action(db_session, admin_user, "edit", record.record_id, "success")
        db_session.delete(record)
        return jsonify({"status": "success", "message": "Record deleted"})


@app.route("/api/logout", methods=["POST"])
@app.route("/logout", methods=["POST"])
def logout():
    flask_session.clear()
    return jsonify({"status": "success", "message": "Logged out"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
