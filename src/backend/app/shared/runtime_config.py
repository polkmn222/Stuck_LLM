import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

DEFAULT_CORS_ORIGINS = [
    "http://127.0.0.1:5174",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]


@dataclass(frozen=True)
class RuntimeConfig:
    cors_origins: List[str]
    require_api_key: bool
    api_key: Optional[str]
    credential_key: Optional[str]
    credential_key_path: Optional[Path]


def _truthy(value: Optional[str]) -> bool:
    return value is not None and value.strip().lower() in {"1", "true", "yes", "on"}


def _csv_values(value: Optional[str]) -> List[str]:
    if value is None:
        return DEFAULT_CORS_ORIGINS
    values = [item.strip() for item in value.split(",") if item.strip()]
    return values or DEFAULT_CORS_ORIGINS


def _non_empty(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def load_runtime_config() -> RuntimeConfig:
    return RuntimeConfig(
        cors_origins=_csv_values(os.environ.get("STUCK_LLM_CORS_ORIGINS")),
        require_api_key=_truthy(os.environ.get("STUCK_LLM_REQUIRE_API_KEY")),
        api_key=_non_empty(os.environ.get("STUCK_LLM_API_KEY")),
        credential_key=_non_empty(os.environ.get("STUCK_LLM_CREDENTIAL_KEY")),
        credential_key_path=(
            Path(configured_path)
            if (configured_path := _non_empty(os.environ.get("STUCK_LLM_CREDENTIAL_KEY_PATH")))
            else None
        ),
    )
