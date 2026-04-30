from fastapi import APIRouter, Depends

from app.features.analysis.live_provider import ProviderNetworkPolicy
from app.features.credentials.schemas import (
    LlmConnectionTestResult,
    LlmCredentialStatus,
    LlmCredentialUpsert,
)
from app.features.credentials.service import (
    delete_llm_credential,
    get_llm_credential_status,
    save_llm_credential,
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


@router.put("/llm", response_model=LlmCredentialStatus)
def write_llm_credential(
    payload: LlmCredentialUpsert,
    store: LocalStateStore = Depends(get_local_store),
    cipher: CredentialCipher = Depends(get_credential_cipher),
) -> LlmCredentialStatus:
    return save_llm_credential(store, cipher, payload)


@router.delete("/llm", response_model=LlmCredentialStatus)
def remove_llm_credential(
    store: LocalStateStore = Depends(get_local_store),
) -> LlmCredentialStatus:
    return delete_llm_credential(store)


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
