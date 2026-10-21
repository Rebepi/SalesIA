import re

REDACT_KEYS = {
    "password",
    "hashed_password",
    "token",
    "refresh_token",
    "access_token",
    "secret",
    "secret_key",
    "raw_secret_key",
    "api_key",
    "private_key",
    "cvv",
    "card_number",
    "pan",
    "pin",
    "auth_token",
    "totp_secret",
    "recovery_codes",
    "card",
}


CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
