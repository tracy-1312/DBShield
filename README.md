# DBShield

## Local demo setup

After importing `dbshield_schema.sql`, the seeded demo users use this password:

```text
password123
```

Useful demo accounts:

```text
Admin: jsmith / password123
Staff Level 1: kwong / password123
Staff Level 3: mbrown / password123
Viewer Level 3: rwilson / password123
```

The demo password is retained for the seeded presentation accounts. Any new
password created through Admin > Manage Users must meet the current password
policy: at least 12 characters, no more than 72 UTF-8 bytes, and at least one
uppercase letter, lowercase letter, number, and symbol. It must also avoid the
username, email name, and common passwords. The form can generate a secure
16-character suggestion and the backend enforces the same requirements.

If your local database already existed before this update, reset the demo passwords with:

```bash
cd DBShield-dev
backend/venv/bin/python backend/reset_demo_passwords.py
```

## How to Run the Local Page

1. Open Terminal and go to the project folder:

```bash
cd <path-to-your-project>
```

2. Start the Flask backend:

```bash
backend/venv/bin/python backend/app.py
```

If it starts successfully, you should see something like:

```text
Running on http://127.0.0.1:5000
```

3. Keep this terminal window open. Then open this URL in your browser:

```text
http://127.0.0.1:5000/
```

4. Log in with the demo account:

```text
Admin:
jsmith / password123
```

## Password policy tests

Run the standalone policy tests from the repository root:

```bash
backend/venv/bin/python -m unittest discover -s backend -p "test*.py"
```
