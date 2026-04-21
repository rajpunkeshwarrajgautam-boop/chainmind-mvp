from __future__ import annotations

from passlib.context import CryptContext

# PBKDF2 avoids bcrypt backend issues on some Python / bcrypt combinations (e.g. 3.14).
_pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)
