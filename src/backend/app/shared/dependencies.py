from typing import cast

from fastapi import Request

from app.shared.credential_crypto import CredentialCipher
from app.shared.state_store import LocalStateStore


def get_local_store(request: Request) -> LocalStateStore:
    return cast(LocalStateStore, request.app.state.local_store)


def get_credential_cipher(request: Request) -> CredentialCipher:
    return cast(CredentialCipher, request.app.state.credential_cipher)
