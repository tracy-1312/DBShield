"""Reset DBShield demo account passwords.

Run this after importing dbshield_schema.sql if the local MySQL database already
exists and you want every seeded demo user to use the same presentation password.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bcrypt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.db import get_session
from backend.models import User

DEMO_PASSWORD = "password123"
DEMO_USERNAMES = ["jsmith", "sjohnson", "mbrown", "edavis", "rwilson", "kwong"]


def main() -> None:
    password_hash = bcrypt.hashpw(DEMO_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    with get_session() as session:
        users = session.query(User).filter(User.username.in_(DEMO_USERNAMES)).all()
        for user in users:
            user.password_hash = password_hash

        print(f"Reset {len(users)} demo users to password: {DEMO_PASSWORD}")
        print("Demo logins:")
        print("  Admin: jsmith / password123")
        print("  Staff: edavis / password123")
        print("  Staff: mbrown / password123")


if __name__ == "__main__":
    main()
