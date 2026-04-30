from typing import cast

from fastapi import Request

from app.features.analysis.live_provider import LlmAnalysisProvider
from app.shared.credential_crypto import CredentialCipher
from app.shared.runtime_config import RuntimeConfig
from app.shared.state_store import LocalStateStore


def get_local_store(request: Request) -> LocalStateStore:
    return cast(LocalStateStore, request.app.state.local_store)


def get_credential_cipher(request: Request) -> CredentialCipher:
    return cast(CredentialCipher, request.app.state.credential_cipher)


def get_llm_analysis_provider(request: Request) -> LlmAnalysisProvider:
    return cast(LlmAnalysisProvider, request.app.state.llm_analysis_provider)


def get_runtime_config(request: Request) -> RuntimeConfig:
    return cast(RuntimeConfig, request.app.state.runtime_config)
