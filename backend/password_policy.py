"""Password-strength rules shared by DBShield account-management APIs."""

from __future__ import annotations

import re


MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_BYTES = 72

COMMON_PASSWORDS = frozenset(
    {
        "12345678",
        "admin123!",
        "changeme123!",
        "letmein123!",
        "password",
        "password123",
        "password123!",
        "qwerty123!",
        "welcome123!",
    }
)


def _identity_tokens(username: str = "", email: str = "") -> tuple[str, ...]:
    """Return account identifiers that should not appear in a password."""
    email_name = email.partition("@")[0]
    return tuple(
        token.casefold()
        for token in (username.strip(), email_name.strip())
        if len(token.strip()) >= 3
    )


def password_checks(password: str, username: str = "", email: str = "") -> dict[str, bool]:
    """Evaluate every password requirement without short-circuiting."""
    value = password or ""
    folded = value.casefold()
    identity_tokens = _identity_tokens(username, email)

    return {
        "minimum_length": len(value) >= MIN_PASSWORD_LENGTH,
        "maximum_length": len(value.encode("utf-8")) <= MAX_PASSWORD_BYTES,
        "uppercase": bool(re.search(r"[A-Z]", value)),
        "lowercase": bool(re.search(r"[a-z]", value)),
        "number": bool(re.search(r"[0-9]", value)),
        "symbol": bool(re.search(r"[^A-Za-z0-9\s]", value)),
        "identity_safe": not any(token in folded for token in identity_tokens),
        "not_common": folded not in COMMON_PASSWORDS,
    }


def password_validation_errors(
    password: str,
    username: str = "",
    email: str = "",
) -> list[str]:
    """Return user-facing reasons a proposed password is not acceptable."""
    checks = password_checks(password, username=username, email=email)
    rules = (
        ("minimum_length", f"use at least {MIN_PASSWORD_LENGTH} characters"),
        ("maximum_length", f"use no more than {MAX_PASSWORD_BYTES} UTF-8 bytes"),
        ("uppercase", "include an uppercase letter"),
        ("lowercase", "include a lowercase letter"),
        ("number", "include a number"),
        ("symbol", "include a symbol"),
        ("identity_safe", "not contain the username or email name"),
        ("not_common", "not be a commonly used password"),
    )
    return [message for key, message in rules if not checks[key]]
