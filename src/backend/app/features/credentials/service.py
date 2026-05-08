from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.features.credentials.schemas import (
    ExternalCredentialListResponse,
    ExternalCredentialProvider,
    ExternalCredentialSecret,
    ExternalCredentialStatus,
    ExternalCredentialUpsert,
    LlmConnectionTestResult,
    LlmCredentialListResponse,
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
EXTERNAL_CREDENTIAL_KEY = "default"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _mask_secret(value: str) -> str:
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


def _active_credential_id(state: State) -> Optional[str]:
    credentials = state.get("llm_credentials", {})
    active_id = state.get("active_llm_credential_id")
    if isinstance(active_id, str) and active_id in credentials:
        return active_id
    if LLM_CREDENTIAL_KEY in credentials:
        return LLM_CREDENTIAL_KEY
    for credential_id in credentials:
        return str(credential_id)
    return None


def _status_from_record(
    credential_id: Optional[str],
    record: Optional[Dict[str, Any]],
    active_id: Optional[str] = None,
) -> LlmCredentialStatus:
    if record is None:
        return LlmCredentialStatus(configured=False)
    return LlmCredentialStatus(
        configured=True,
        credential_id=credential_id,
        label=record.get("label"),
        provider=record["provider"],
        model=record["model"],
        base_url=record["base_url"],
        api_key_mask=record["api_key_mask"],
        key_source=record["key_source"],
        is_active=credential_id is not None and credential_id == active_id,
        created_at=record["created_at"],
        updated_at=record["updated_at"],
    )


def _external_status_from_record(
    credential_id: Optional[str],
    record: Optional[Dict[str, Any]],
    active_ids: Optional[Dict[str, str]] = None,
) -> ExternalCredentialStatus:
    if record is None:
        return ExternalCredentialStatus(configured=False)
    provider = record["provider"]
    return ExternalCredentialStatus(
        configured=True,
        credential_id=credential_id,
        label=record.get("label"),
        provider=provider,
        api_key_mask=record["api_key_mask"],
        key_source=record["key_source"],
        is_active=(
            credential_id is not None
            and active_ids is not None
            and active_ids.get(provider) == credential_id
        ),
        created_at=record["created_at"],
        updated_at=record["updated_at"],
    )


def _active_external_credential_id(
    state: State,
    provider: ExternalCredentialProvider,
) -> Optional[str]:
    credentials = state.get("external_credentials", {})
    active_ids = state.get("active_external_credential_ids", {})
    active_id = active_ids.get(provider) if isinstance(active_ids, dict) else None
    if isinstance(active_id, str):
        record = credentials.get(active_id)
        if isinstance(record, dict) and record.get("provider") == provider:
            return active_id
    default_id = f"{provider}_{EXTERNAL_CREDENTIAL_KEY}"
    record = credentials.get(default_id)
    if isinstance(record, dict) and record.get("provider") == provider:
        return default_id
    for credential_id, record in credentials.items():
        if isinstance(record, dict) and record.get("provider") == provider:
            return str(credential_id)
    return None


def get_llm_credential_status(store: LocalStateStore) -> LlmCredentialStatus:
    state = store.read()
    active_id = _active_credential_id(state)
    record = state["llm_credentials"].get(active_id) if active_id else None
    return _status_from_record(active_id, record, active_id)


def list_llm_credentials(store: LocalStateStore) -> LlmCredentialListResponse:
    state = store.read()
    active_id = _active_credential_id(state)
    credentials = [
        _status_from_record(credential_id, record, active_id)
        for credential_id, record in state["llm_credentials"].items()
        if isinstance(record, dict)
    ]
    return LlmCredentialListResponse(
        active_credential_id=active_id,
        credentials=credentials,
    )


def list_external_credentials(store: LocalStateStore) -> ExternalCredentialListResponse:
    state = store.read()
    active_ids = {
        provider: credential_id
        for provider in ("tavily", "gnews", "serpapi", "eventregistry")
        if (credential_id := _active_external_credential_id(state, provider)) is not None
    }
    credentials = [
        _external_status_from_record(credential_id, record, active_ids)
        for credential_id, record in state["external_credentials"].items()
        if isinstance(record, dict)
    ]
    return ExternalCredentialListResponse(
        active_credential_ids=active_ids,
        credentials=credentials,
    )


def save_llm_credential(
    store: LocalStateStore,
    cipher: CredentialCipher,
    payload: LlmCredentialUpsert,
) -> LlmCredentialStatus:
    api_key = payload.api_key.get_secret_value()
    encrypted_api_key = cipher.encrypt(api_key)
    updated_at = _now()
    credential_id = payload.credential_id or LLM_CREDENTIAL_KEY

    def mutate(state: State) -> LlmCredentialStatus:
        existing = state["llm_credentials"].get(credential_id)
        created_at = existing["created_at"] if existing else updated_at
        record = {
            "label": payload.label,
            "provider": payload.provider,
            "model": payload.model,
            "base_url": payload.base_url,
            "encrypted_api_key": encrypted_api_key,
            "api_key_mask": _mask_secret(api_key),
            "key_source": cipher.key_source,
            "created_at": created_at,
            "updated_at": updated_at,
        }
        state["llm_credentials"][credential_id] = record
        if payload.make_active or _active_credential_id(state) is None:
            state["active_llm_credential_id"] = credential_id
        return _status_from_record(
            credential_id,
            record,
            _active_credential_id(state),
        )

    return store.update(mutate)


def save_external_credential(
    store: LocalStateStore,
    cipher: CredentialCipher,
    payload: ExternalCredentialUpsert,
) -> ExternalCredentialStatus:
    api_key = payload.api_key.get_secret_value()
    encrypted_api_key = cipher.encrypt(api_key)
    updated_at = _now()
    credential_id = payload.credential_id or f"{payload.provider}_{EXTERNAL_CREDENTIAL_KEY}"

    def mutate(state: State) -> ExternalCredentialStatus:
        existing = state["external_credentials"].get(credential_id)
        created_at = existing["created_at"] if existing else updated_at
        record = {
            "label": payload.label,
            "provider": payload.provider,
            "encrypted_api_key": encrypted_api_key,
            "api_key_mask": _mask_secret(api_key),
            "key_source": cipher.key_source,
            "created_at": created_at,
            "updated_at": updated_at,
        }
        state["external_credentials"][credential_id] = record
        if payload.make_active or _active_external_credential_id(state, payload.provider) is None:
            state["active_external_credential_ids"][payload.provider] = credential_id
        return _external_status_from_record(
            credential_id,
            record,
            state["active_external_credential_ids"],
        )

    return store.update(mutate)


def set_active_external_credential(
    store: LocalStateStore,
    credential_id: str,
) -> ExternalCredentialStatus:
    def mutate(state: State) -> ExternalCredentialStatus:
        record = state["external_credentials"].get(credential_id)
        if record is None:
            return ExternalCredentialStatus(configured=False)
        provider = record["provider"]
        state["active_external_credential_ids"][provider] = credential_id
        return _external_status_from_record(
            credential_id,
            record,
            state["active_external_credential_ids"],
        )

    return store.update(mutate)


def delete_external_credential(
    store: LocalStateStore,
    credential_id: str,
) -> ExternalCredentialStatus:
    def mutate(state: State) -> ExternalCredentialStatus:
        record = state["external_credentials"].pop(credential_id, None)
        if record is None:
            return ExternalCredentialStatus(configured=False)
        provider = record["provider"]
        if state["active_external_credential_ids"].get(provider) == credential_id:
            state["active_external_credential_ids"].pop(provider, None)
            next_id = _active_external_credential_id(state, provider)
            if next_id is not None:
                state["active_external_credential_ids"][provider] = next_id
        return ExternalCredentialStatus(configured=False)

    return store.update(mutate)


def set_active_llm_credential(
    store: LocalStateStore,
    credential_id: str,
) -> LlmCredentialStatus:
    def mutate(state: State) -> LlmCredentialStatus:
        record = state["llm_credentials"].get(credential_id)
        if record is None:
            return LlmCredentialStatus(configured=False)
        state["active_llm_credential_id"] = credential_id
        return _status_from_record(credential_id, record, credential_id)

    return store.update(mutate)


def delete_llm_credential(
    store: LocalStateStore,
    credential_id: Optional[str] = None,
) -> LlmCredentialStatus:
    def mutate(state: State) -> LlmCredentialStatus:
        target_id = credential_id or _active_credential_id(state) or LLM_CREDENTIAL_KEY
        state["llm_credentials"].pop(target_id, None)
        if state.get("active_llm_credential_id") == target_id:
            state["active_llm_credential_id"] = None
        next_active_id = _active_credential_id(state)
        if next_active_id is not None:
            state["active_llm_credential_id"] = next_active_id
            return _status_from_record(
                next_active_id,
                state["llm_credentials"].get(next_active_id),
                next_active_id,
            )
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
    return _credential_secret_and_source_for_id(store, cipher, None)


def _credential_secret_and_source_for_id(
    store: LocalStateStore,
    cipher: CredentialCipher,
    credential_id: Optional[str],
) -> tuple[Optional[LlmCredentialSecret], Optional[str]]:
    state = store.read()
    resolved_id = credential_id or _active_credential_id(state)
    record = state["llm_credentials"].get(resolved_id) if resolved_id else None
    if record is None:
        return None, None
    return (
        LlmCredentialSecret(
            credential_id=resolved_id or LLM_CREDENTIAL_KEY,
            label=record.get("label"),
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
    credential_id: Optional[str] = None,
) -> Optional[LlmCredentialSecret]:
    credential, _ = _credential_secret_and_source_for_id(store, cipher, credential_id)
    return credential


def get_active_external_credential_secrets(
    store: LocalStateStore,
    cipher: CredentialCipher,
) -> Dict[ExternalCredentialProvider, ExternalCredentialSecret]:
    state = store.read()
    secrets: Dict[ExternalCredentialProvider, ExternalCredentialSecret] = {}
    for provider in ("tavily", "gnews", "serpapi", "eventregistry"):
        credential_id = _active_external_credential_id(state, provider)
        record = state["external_credentials"].get(credential_id) if credential_id else None
        if not isinstance(record, dict):
            continue
        secrets[provider] = ExternalCredentialSecret(
            credential_id=credential_id,
            label=record.get("label"),
            provider=provider,
            api_key=cipher.decrypt(record["encrypted_api_key"]),
        )
    return secrets
