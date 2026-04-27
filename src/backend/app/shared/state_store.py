from __future__ import annotations

import copy
import json
import os
import threading
from pathlib import Path
from typing import Any, Callable, Dict, TypeVar

State = Dict[str, Any]
T = TypeVar("T")

DEFAULT_STATE: State = {
    "settings": {
        "provider": "openai",
        "analysis_mode": "quick",
        "default_market": "KR",
        "default_horizon": None,
    },
    "conversations": {},
    "analysis_requests": {},
    "scores": {},
    "backtests": {},
    "source_collections": {},
    "llm_credentials": {},
}


def default_state_path() -> Path:
    configured_path = os.environ.get("STUCK_LLM_STATE_PATH")
    if configured_path:
        return Path(configured_path)
    return Path(".local") / "stuck_llm_state.json"


def new_default_state() -> State:
    return copy.deepcopy(DEFAULT_STATE)


class LocalStateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.RLock()

    def read(self) -> State:
        with self._lock:
            if not self.path.exists():
                return new_default_state()

            with self.path.open("r", encoding="utf-8") as state_file:
                loaded = json.load(state_file)

            if not isinstance(loaded, dict):
                return new_default_state()

            state = new_default_state()
            state.update(loaded)
            state["settings"] = {
                **DEFAULT_STATE["settings"],
                **state.get("settings", {}),
            }
            state["conversations"] = state.get("conversations", {})
            state["analysis_requests"] = state.get("analysis_requests", {})
            state["scores"] = state.get("scores", {})
            state["backtests"] = state.get("backtests", {})
            state["source_collections"] = state.get("source_collections", {})
            state["llm_credentials"] = state.get("llm_credentials", {})
            return state

    def write(self, state: State) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.path.with_name(f"{self.path.name}.tmp")
            with temp_path.open("w", encoding="utf-8") as state_file:
                json.dump(state, state_file, indent=2, sort_keys=True)
            temp_path.replace(self.path)

    def update(self, mutator: Callable[[State], T]) -> T:
        with self._lock:
            state = self.read()
            result = mutator(state)
            self.write(state)
            return result
