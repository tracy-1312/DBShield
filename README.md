# DBShield
## Authentication & Security Features

### Two-Factor Authentication (2FA)
Users can enable 2FA using any TOTP-based authenticator app (e.g. Google Authenticator, Authy).

- `POST /2fa/setup` — generates a secret and returns a QR code to scan
- `POST /2fa/verify` — verifies the 6-digit code and enables 2FA on first success

### Session Timeout
Sessions automatically expire after 15 minutes of inactivity. Any protected route requires an active, non-expired session — expired sessions are cleared and return a 401 response.

### Password Reset
Users can reset a forgotten password via a secure, time-limited token.

- `POST /reset-password/request` — takes an email, generates a reset token (expires in 30 minutes). Returns a generic success message regardless of whether the email exists, to avoid leaking registered accounts.
- `POST /reset-password/confirm` — takes the email, token, and new password. Validates the token and updates the password if valid.

### Setup Requirements
Before running the app, create a `.env` file (see `.env.example`) with the following:

```
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
DB_NAME=
DBSHIELD_KEY=       # used for encrypting sensitive fields — generate with:
                     # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FLASK_SECRET_KEY=    # any random secure string, used for session signing
```

### Dependencies
Install required packages:
```
pip install -r requirements.txt
```
New packages added for auth features: `pyotp`, `qrcode`, `bcrypt`

### Known Limitations
- Rate limiting on 2FA attempts is per-account, not per-IP
- No email-sending integration yet — reset tokens currently need to be delivered manually/logged for testing
- CSRF protection beyond `SameSite` cookie setting is not implemented