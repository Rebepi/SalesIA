import base64
import hashlib
import hmac
import os
import struct
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from salesia.shared.infrastructure.config import settings

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


_argon2_hasher = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=1, hash_len=32)


def hash_password(password: str) -> str:
    return _argon2_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    if hashed_password.startswith("$argon2"):
        try:
            return _argon2_hasher.verify(hashed_password, plain_password)
        except (VerifyMismatchError, InvalidHashError):
            return False
    try:
        raw_hash = hashed_password
        if raw_hash.startswith("pbkdf2_sha256$"):
            raw_hash = raw_hash.split("$", 1)[1]
        decoded = base64.b64decode(raw_hash.encode("ascii"))
        salt = decoded[:16]
        key = decoded[16:]
        new_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(key, new_key)
    except Exception:
        return False


def needs_rehash(hashed_password: str) -> bool:
    if not hashed_password or not hashed_password.startswith("$argon2"):
        return True
    try:
        return _argon2_hasher.check_needs_rehash(hashed_password)
    except Exception:
        return True


def create_access_token(data: Optional[dict] = None, expires_delta: Optional[timedelta] = None, **kwargs) -> str:
    to_encode = (data or {}).copy()
    to_encode.update(kwargs)
    if "user_id" in to_encode:
        to_encode["sub"] = str(to_encode.pop("user_id"))
    if "company_id" in to_encode and isinstance(to_encode["company_id"], UUID):
        to_encode["company_id"] = str(to_encode["company_id"])
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now, "type": "access", "token_type": "access", "jti": uuid4().hex})
    return jwt.encode(to_encode, settings.secret_key, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: Optional[dict] = None, **kwargs) -> str:
    to_encode = (data or {}).copy()
    to_encode.update(kwargs)
    if "user_id" in to_encode:
        to_encode["sub"] = str(to_encode.pop("user_id"))
    if "company_id" in to_encode and isinstance(to_encode["company_id"], UUID):
        to_encode["company_id"] = str(to_encode["company_id"])
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": now, "type": "refresh", "token_type": "refresh", "jti": uuid4().hex})
    return jwt.encode(to_encode, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, settings.secret_key, algorithms=[JWT_ALGORITHM], options={"require": ["exp", "iat", "sub", "jti"]}
        )
    except jwt.InvalidTokenError as exc:
        raise ValueError("Token inválido") from exc


def generate_totp_secret() -> str:
    return base64.b32encode(os.urandom(20)).decode("ascii")


def generate_totp_code(secret: Union[str, bytes], intervals_no: Optional[int] = None) -> str:
    if isinstance(secret, str):
        secret_bytes = base64.b32decode(secret.upper(), casefold=True)
    else:
        secret_bytes = secret
    if intervals_no is None:
        intervals_no = int(time.time() // 30)
    msg = struct.pack(">Q", intervals_no)
    digest = hmac.new(secret_bytes, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code % 1000000).zfill(6)


def verify_totp_code(secret_b32: str, code: str) -> bool:
    if not code or len(code) != 6 or not code.isdigit():
        return False
    try:
        secret_bytes = base64.b32decode(secret_b32.upper(), casefold=True)
    except Exception:
        return False

    current_interval = int(time.time() // 30)
    for offset in (-1, 0, 1):
        if generate_totp_code(secret_bytes, current_interval + offset) == code:
            return True
    return False


def revoke_token(token: str) -> None:
    from salesia.modules.seguridad.infrastructure.models import AuthSession
    from salesia.shared.infrastructure.database import sync_session_factory

    payload = decode_token(token)
    with sync_session_factory() as session:
        active = session.get(AuthSession, UUID(payload["sid"]))
        if active:
            active.revoked_at = datetime.now(timezone.utc)
            active.sudo_until = None
            session.commit()


def is_token_revoked(token: str) -> bool:
    from salesia.modules.seguridad.infrastructure.models import AuthSession
    from salesia.shared.infrastructure.database import sync_session_factory

    try:
        payload = decode_token(token)
        with sync_session_factory() as session:
            active = session.get(AuthSession, UUID(payload["sid"]))
            return active is None or active.revoked_at is not None
    except (ValueError, KeyError):
        return True
