from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from cryptography.fernet import Fernet

CredentialKeySource = Literal["env", "generated_local"]


@dataclass(frozen=True)
class CredentialCipher:
    configured_key: Optional[str]
    local_key_path: Path

    @property
    def key_source(self) -> CredentialKeySource:
        return "env" if self.configured_key else "generated_local"

    def encrypt(self, value: str) -> str:
        return self._fernet().encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, token: str) -> str:
        return self._fernet().decrypt(token.encode("utf-8")).decode("utf-8")

    def _fernet(self) -> Fernet:
        return Fernet(self._key())

    def _key(self) -> bytes:
        if self.configured_key:
            return _derive_key(self.configured_key)
        return _load_or_create_local_key(self.local_key_path)


def _derive_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _load_or_create_local_key(path: Path) -> bytes:
    if path.exists():
        return path.read_bytes().strip()

    path.parent.mkdir(parents=True, exist_ok=True)
    key = Fernet.generate_key()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    with os.fdopen(os.open(path, flags, 0o600), "wb") as key_file:
        key_file.write(key)
    return key
