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

