"""Хеш пароля через pwdlib. Алгоритм — Argon2."""

from pwdlib import PasswordHash

_hasher = PasswordHash.recommended()


class PwdlibHasher:
    def hash(self, password: str) -> str:
        return _hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        return _hasher.verify(password, password_hash)
