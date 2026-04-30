from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.features.credentials.schemas import (
    LlmConnectionTestResult,
    LlmCredentialSecret,
    LlmCredentialStatus,
    LlmCredentialUpsert,
)
from app.features.analysis.live_provider import (
    LiveProviderError,
    LlmProviderConfig,
    OpenAiCompatibleAnalysisProvider,
    ProviderNetworkPolicy,
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


def _connection_test_provider(
    network_policy: ProviderNetworkPolicy,
) -> OpenAiCompatibleAnalysisProvider:
    return OpenAiCompatibleAnalysisProvider(network_policy=network_policy)


def _connection_error_message(code: str) -> str:
    messages = {
        "auth_error": "Authentication failed. Check the saved provider key.",
        "rate_limited": "The provider is rate limiting connection tests. Retry later.",
        "timeout": "The provider timed out during the connection test.",
        "malformed_output": "The provider responded, but the test response was malformed.",
        "unsupported_provider": "The selected provider is not connected for live analysis yet.",
        "invalid_base_url": "The saved provider base URL is not allowed.",
        "provider_error": "The provider connection test failed.",
    }
    return messages.get(code, messages["provider_error"])


def _credential_secret_and_source(
    store: LocalStateStore,
    cipher: CredentialCipher,
) -> tuple[Optional[LlmCredentialSecret], Optional[str]]:
    record = store.read()["llm_credentials"].get(LLM_CREDENTIAL_KEY)
    if record is None:
        return None, None
    return (
        LlmCredentialSecret(
            provider=record["provider"],
            model=record["model"],
            base_url=record["base_url"],
            api_key=cipher.decrypt(record["encrypted_api_key"]),
        ),
        record["key_source"],
    )


def test_llm_credential_connection(
    store: LocalStateStore,
    cipher: CredentialCipher,
    network_policy: ProviderNetworkPolicy,
) -> LlmConnectionTestResult:
    credential, key_source = _credential_secret_and_source(store, cipher)
    if credential is None:
        return LlmConnectionTestResult(
            configured=False,
            status="setup_needed",
            message="Save an LLM provider key before testing the connection.",
        )

    provider_config = LlmProviderConfig(
        provider=credential.provider,
        model=credential.model,
        base_url=credential.base_url,
        api_key=credential.api_key,
    )

    try:
        _connection_test_provider(network_policy).test_connection(provider_config)
    except LiveProviderError as error:
        return LlmConnectionTestResult(
            configured=True,
            status="provider_error",
            provider=credential.provider,
            model=credential.model,
            base_url=credential.base_url,
            key_source=key_source,
            error_code=error.code,
            message=_connection_error_message(error.code),
        )

    return LlmConnectionTestResult(
        configured=True,
        status="ok",
        provider=credential.provider,
        model=credential.model,
        base_url=credential.base_url,
        key_source=key_source,
        message="Connection test succeeded.",
    )


def get_llm_credential_secret(
    store: LocalStateStore,
    cipher: CredentialCipher,
) -> Optional[LlmCredentialSecret]:
    credential, _ = _credential_secret_and_source(store, cipher)
    return credential
