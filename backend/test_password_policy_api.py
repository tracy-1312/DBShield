import os
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

import bcrypt


os.environ.setdefault(
    "DBSHIELD_KEY",
    "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=",
)
os.environ.setdefault("FLASK_SECRET_KEY", "test-only-secret")

from backend import app as app_module
from backend.models import User


class FakeQuery:
    def __init__(self, result):
        self.result = result

    def filter_by(self, **_kwargs):
        return self

    def first(self):
        return self.result


class FakeSession:
    def __init__(self, query_result=None):
        self.added = []
        self.query_result = query_result

    def add(self, value):
        self.added.append(value)

    def flush(self):
        return None

    def query(self, _model):
        return FakeQuery(self.query_result)


def session_provider(fake_session):
    @contextmanager
    def provide_session():
        yield fake_session

    return provide_session


class PasswordPolicyApiTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config.update(TESTING=True)
        self.client = app_module.app.test_client()
        self.admin = SimpleNamespace(user_id=1, role="admin")
        self.base_payload = {
            "username": "newclinician",
            "full_name": "New Clinician",
            "email": "newclinician@hospital.test",
            "role": "data_manager",
            "clearance_level": 2,
        }

    def request_with_session(self, method, path, fake_session, payload):
        with patch.object(app_module, "get_session", session_provider(fake_session)):
            with patch.object(
                app_module,
                "require_admin",
                return_value=(self.admin, None),
            ):
                return self.client.open(path, method=method, json=payload)

    def test_create_user_rejects_a_weak_password(self):
        fake_session = FakeSession()
        payload = {**self.base_payload, "password": "Password1"}

        response = self.request_with_session(
            "POST",
            "/api/admin/users",
            fake_session,
            payload,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(fake_session.added, [])
        self.assertIn("Password is not strong enough", response.get_json()["message"])

    def test_create_user_accepts_and_hashes_a_strong_password(self):
        fake_session = FakeSession()
        password = "River!Quartz7Maple"
        payload = {**self.base_payload, "password": password}

        response = self.request_with_session(
            "POST",
            "/api/admin/users",
            fake_session,
            payload,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(fake_session.added), 1)
        self.assertTrue(
            bcrypt.checkpw(
                password.encode("utf-8"),
                fake_session.added[0].password_hash.encode("utf-8"),
            )
        )

    def test_update_user_rejects_a_weak_new_password(self):
        original_hash = bcrypt.hashpw(b"Original!Pass7Word", bcrypt.gensalt()).decode("utf-8")
        target = User(
            user_id=2,
            username="existinguser",
            password_hash=original_hash,
            full_name="Existing User",
            email="existing@hospital.test",
            role="viewer",
            clearance_level=1,
        )
        fake_session = FakeSession(query_result=target)

        response = self.request_with_session(
            "PUT",
            "/api/admin/users/2",
            fake_session,
            {"password": "weak"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(target.password_hash, original_hash)


if __name__ == "__main__":
    unittest.main()
