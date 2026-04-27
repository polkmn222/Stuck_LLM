from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.features.credentials.schemas import (
    LlmCredentialSecret,
    LlmCredentialStatus,
    LlmCredentialUpsert,
)
from app.shared.credential_crypto import CredentialCipher
from app.shared.state_store import LocalStateStore, State

LLM_CREDENTIAL_KEY = "default"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _mask_secret(value: str) -> str:
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


def _status_from_record(record: Optional[Dict[str, Any]]) -> LlmCredentialStatus:
    if record is None:
        return LlmCredentialStatus(configured=False)
    return LlmCredentialStatus(
        configured=True,
        provider=record["provider"],
        model=record["model"],
        base_url=record["base_url"],
        api_key_mask=record["api_key_mask"],
        key_source=record["key_source"],
        created_at=record["created_at"],
        updated_at=record["updated_at"],
    )


def get_llm_credential_status(store: LocalStateStore) -> LlmCredentialStatus:
    record = store.read()["llm_credentials"].get(LLM_CREDENTIAL_KEY)
    return _status_from_record(record)


def save_llm_credential(
    store: LocalStateStore,
    cipher: CredentialCipher,
    payload: LlmCredentialUpsert,
) -> LlmCredentialStatus:
    api_key = payload.api_key.get_secret_value()
    encrypted_api_key = cipher.encrypt(api_key)
    updated_at = _now()

    def mutate(state: State) -> LlmCredentialStatus:
        existing = state["llm_credentials"].get(LLM_CREDENTIAL_KEY)
        created_at = existing["created_at"] if existing else updated_at
        record = {
            "provider": payload.provider,
            "model": payload.model,
            "base_url": payload.base_url,
            "encrypted_api_key": encrypted_api_key,
            "api_key_mask": _mask_secret(api_key),
            "key_source": cipher.key_source,
            "created_at": created_at,
            "updated_at": updated_at,
        }
        state["llm_credentials"][LLM_CREDENTIAL_KEY] = record
        return _status_from_record(record)

    return store.update(mutate)


def delete_llm_credential(store: LocalStateStore) -> LlmCredentialStatus:
    def mutate(state: State) -> LlmCredentialStatus:
        state["llm_credentials"].pop(LLM_CREDENTIAL_KEY, None)
        return LlmCredentialStatus(configured=False)

    return store.update(mutate)


def get_llm_credential_secret(
    store: LocalStateStore,
    cipher: CredentialCipher,
) -> Optional[LlmCredentialSecret]:
    record = store.read()["llm_credentials"].get(LLM_CREDENTIAL_KEY)
    if record is None:
        return None
    return LlmCredentialSecret(
        provider=record["provider"],
        model=record["model"],
        base_url=record["base_url"],
        api_key=cipher.decrypt(record["encrypted_api_key"]),
    )
