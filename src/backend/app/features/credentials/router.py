from fastapi import APIRouter, Depends

from app.features.analysis.live_provider import ProviderNetworkPolicy
from app.features.credentials.schemas import (
    ExternalCredentialListResponse,
    ExternalCredentialStatus,
    ExternalCredentialUpsert,
    LlmConnectionTestResult,
    LlmCredentialListResponse,
    LlmCredentialStatus,
    LlmCredentialUpsert,
)
from app.features.credentials.service import (
    delete_external_credential,
    delete_llm_credential,
    get_llm_credential_status,
    list_llm_credentials,
    list_external_credentials,
    save_llm_credential,
    save_external_credential,
    set_active_external_credential,
    set_active_llm_credential,
    test_llm_credential_connection,
)
from app.shared.credential_crypto import CredentialCipher
from app.shared.dependencies import get_credential_cipher, get_local_store, get_runtime_config
from app.shared.runtime_config import RuntimeConfig
from app.shared.state_store import LocalStateStore

router = APIRouter(prefix="/credentials", tags=["credentials"])


@router.get("/llm", response_model=LlmCredentialStatus)
def read_llm_credential_status(
    store: LocalStateStore = Depends(get_local_store),
) -> LlmCredentialStatus:
    return get_llm_credential_status(store)


@router.get("/llm/profiles", response_model=LlmCredentialListResponse)
def read_llm_credential_profiles(
    store: LocalStateStore = Depends(get_local_store),
) -> LlmCredentialListResponse:
    return list_llm_credentials(store)


@router.get("/external/profiles", response_model=ExternalCredentialListResponse)
def read_external_credential_profiles(
    store: LocalStateStore = Depends(get_local_store),
) -> ExternalCredentialListResponse:
    return list_external_credentials(store)


@router.put("/llm", response_model=LlmCredentialStatus)
def write_llm_credential(
    payload: LlmCredentialUpsert,
    store: LocalStateStore = Depends(get_local_store),
    cipher: CredentialCipher = Depends(get_credential_cipher),
) -> LlmCredentialStatus:
    return save_llm_credential(store, cipher, payload)


@router.post("/llm/profiles", response_model=LlmCredentialStatus)
def create_llm_credential_profile(
    payload: LlmCredentialUpsert,
    store: LocalStateStore = Depends(get_local_store),
    cipher: CredentialCipher = Depends(get_credential_cipher),
) -> LlmCredentialStatus:
    return save_llm_credential(store, cipher, payload)


@router.post("/external/profiles", response_model=ExternalCredentialStatus)
def create_external_credential_profile(
    payload: ExternalCredentialUpsert,
    store: LocalStateStore = Depends(get_local_store),
    cipher: CredentialCipher = Depends(get_credential_cipher),
) -> ExternalCredentialStatus:
    return save_external_credential(store, cipher, payload)


@router.patch("/llm/profiles/{credential_id}/active", response_model=LlmCredentialStatus)
def select_llm_credential_profile(
    credential_id: str,
    store: LocalStateStore = Depends(get_local_store),
) -> LlmCredentialStatus:
    return set_active_llm_credential(store, credential_id)


@router.patch("/external/profiles/{credential_id}/active", response_model=ExternalCredentialStatus)
def select_external_credential_profile(
    credential_id: str,
    store: LocalStateStore = Depends(get_local_store),
) -> ExternalCredentialStatus:
    return set_active_external_credential(store, credential_id)


@router.delete("/llm", response_model=LlmCredentialStatus)
def remove_llm_credential(
    store: LocalStateStore = Depends(get_local_store),
) -> LlmCredentialStatus:
    return delete_llm_credential(store)


@router.delete("/llm/profiles/{credential_id}", response_model=LlmCredentialStatus)
def remove_llm_credential_profile(
    credential_id: str,
    store: LocalStateStore = Depends(get_local_store),
) -> LlmCredentialStatus:
    return delete_llm_credential(store, credential_id)


@router.delete("/external/profiles/{credential_id}", response_model=ExternalCredentialStatus)
def remove_external_credential_profile(
    credential_id: str,
    store: LocalStateStore = Depends(get_local_store),
) -> ExternalCredentialStatus:
    return delete_external_credential(store, credential_id)


@router.post("/llm/test", response_model=LlmConnectionTestResult)
def test_llm_credential(
    store: LocalStateStore = Depends(get_local_store),
    cipher: CredentialCipher = Depends(get_credential_cipher),
    runtime_config: RuntimeConfig = Depends(get_runtime_config),
) -> LlmConnectionTestResult:
    return test_llm_credential_connection(
        store,
        cipher,
        ProviderNetworkPolicy.from_runtime_config(runtime_config),
    )
