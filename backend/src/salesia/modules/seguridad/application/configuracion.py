import secrets

from salesia.modules.seguridad.infrastructure.security import hash_password

_DUMMY_HASH = hash_password(secrets.token_urlsafe(32))


COMMON_PASSWORDS = {"123456789012", "password12345", "password123456", "administrator123", "qwertyuiop123"}
