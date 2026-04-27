import secrets
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.features.analysis.router import router as analysis_router
from app.features.backtest.router import router as backtest_router
from app.features.conversations.router import router as conversations_router
from app.features.credentials.router import router as credentials_router
from app.features.health.router import router as health_router
from app.features.ingestion.router import router as ingestion_router
from app.features.market_data.router import router as market_data_router
from app.features.scoring.router import router as scoring_router
from app.features.settings.router import router as settings_router
from app.shared.runtime_config import RuntimeConfig, load_runtime_config
from app.shared.credential_crypto import CredentialCipher
from app.shared.state_store import LocalStateStore, default_state_path


def _bearer_token(request: Request) -> Optional[str]:
    authorization = request.headers.get("authorization")
    if authorization is None:
        return None
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        return None
    return authorization[len(prefix) :]


def _request_api_key(request: Request) -> Optional[str]:
    return request.headers.get("x-stuck-llm-api-key") or _bearer_token(request)


def create_app(
    state_path: Optional[Path] = None,
    runtime_config: Optional[RuntimeConfig] = None,
) -> FastAPI:
    config = runtime_config or load_runtime_config()
    app = FastAPI(
        title="Stock Analysis Agent API",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Stuck-LLM-API-Key"],
    )
    resolved_state_path = state_path or default_state_path()
    app.state.runtime_config = config
    app.state.local_store = LocalStateStore(resolved_state_path)
    app.state.credential_cipher = CredentialCipher(
        configured_key=config.credential_key,
        local_key_path=config.credential_key_path
        or resolved_state_path.parent / "stuck_llm_credential.key",
    )

    @app.middleware("http")
    async def require_api_key(request: Request, call_next):
        if (
            config.require_api_key
            and request.method != "OPTIONS"
            and request.url.path != "/health"
        ):
            expected_key = config.api_key
            supplied_key = _request_api_key(request)
            if not expected_key or not supplied_key:
                return JSONResponse(status_code=401, content={"detail": "API key required"})
            if not secrets.compare_digest(supplied_key, expected_key):
                return JSONResponse(status_code=401, content={"detail": "API key required"})
        return await call_next(request)

    app.include_router(health_router)
    app.include_router(settings_router)
    app.include_router(credentials_router)
    app.include_router(conversations_router)
    app.include_router(market_data_router)
    app.include_router(analysis_router)
    app.include_router(scoring_router)
    app.include_router(backtest_router)
    app.include_router(ingestion_router)
    return app


app = create_app()
