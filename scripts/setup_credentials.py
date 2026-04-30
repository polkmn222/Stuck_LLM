#!/usr/bin/env python3
from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path
from typing import Optional, cast

from pydantic import SecretStr

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "src" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.features.credentials.schemas import (  # noqa: E402
    CEREBRAS_DEFAULT_MODEL,
    CredentialProvider,
    LlmCredentialUpsert,
)
from app.features.credentials.service import save_llm_credential  # noqa: E402
from app.shared.credential_crypto import CredentialCipher  # noqa: E402
from app.shared.state_store import LocalStateStore, default_state_path  # noqa: E402


def _prompt(label: str, default: Optional[str] = None, secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    prompt = f"{label}{suffix}: "
    value = getpass.getpass(prompt) if secret else input(prompt)
    if not value.strip() and default is not None:
        return default
    return value.strip()


def _default_base_url(provider: str) -> Optional[str]:
    if provider == "openai":
        return "https://api.openai.com/v1"
    if provider == "anthropic":
        return "https://api.anthropic.com/v1"
    if provider == "cerebras":
        return "https://api.cerebras.ai/v1"
    return None


def _default_model(provider: str) -> str:
    if provider == "openai":
        return "gpt-4o-mini"
    if provider == "anthropic":
        return "claude-3-5-sonnet-latest"
    if provider == "cerebras":
        return CEREBRAS_DEFAULT_MODEL
    return "openai-compatible-model"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Configure encrypted local BYOK LLM credentials."
    )
    parser.add_argument("--provider", choices=["cerebras", "openai", "anthropic", "custom"])
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--api-key")
    parser.add_argument("--state-path", type=Path, default=default_state_path())
    parser.add_argument("--credential-key")
    parser.add_argument("--credential-key-path", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    provider = cast(
        CredentialProvider,
        args.provider or _prompt("Provider (cerebras, openai, anthropic, custom)", "cerebras"),
    )
    model = args.model or _prompt("Model", _default_model(provider))
    base_url = args.base_url
    if base_url is None:
        base_url = _prompt("Base URL", _default_base_url(provider))
    api_key = args.api_key or _prompt("API key", secret=True)

    state_path = args.state_path
    cipher = CredentialCipher(
        configured_key=args.credential_key,
        local_key_path=args.credential_key_path
        or state_path.parent / "stuck_llm_credential.key",
    )
    status = save_llm_credential(
        LocalStateStore(state_path),
        cipher,
        LlmCredentialUpsert(
            provider=provider,
            model=model,
            base_url=base_url,
            api_key=SecretStr(api_key),
        ),
    )
    print(
        "Saved LLM credential: "
        f"provider={status.provider} model={status.model} "
        f"base_url={status.base_url} key={status.api_key_mask} "
        f"source={status.key_source}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
