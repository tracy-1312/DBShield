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

If your local database already existed before this update, reset the demo passwords with:

```bash
cd DBShield-dev
backend/venv/bin/python backend/reset_demo_passwords.py
```

## How to Run the Local Page

1. Open Terminal and go to the project folder:

```bash
cd /Users/kunlangli/Documents/Codex/DBShield-dev
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

