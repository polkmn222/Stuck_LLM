from __future__ import annotations

import copy
import json
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Any, Callable, Dict, Iterator, Optional, TypeVar

try:
    import fcntl
except ImportError:  # pragma: no cover - POSIX file locks are available in CI/dev.
    fcntl = None  # type: ignore[assignment]

State = Dict[str, Any]
T = TypeVar("T")
SPLIT_STATE_KEYS = ("kv_cache", "news_processing_runs", "prediction_artifacts")

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
    "kv_cache": {},
    "news_processing_runs": {},
    "prediction_artifacts": {},
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
        self._file_lock_depth = 0
        self._file_lock_handle: Optional[IO[str]] = None

    @contextmanager
    def _file_lock(self) -> Iterator[None]:
        if fcntl is None:
            yield
            return

        if self._file_lock_depth == 0:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            lock_path = self.path.with_name(f"{self.path.name}.lock")
            self._file_lock_handle = lock_path.open("a+", encoding="utf-8")
            fcntl.flock(self._file_lock_handle.fileno(), fcntl.LOCK_EX)
        self._file_lock_depth += 1

        try:
            yield
        finally:
            self._file_lock_depth -= 1
            if self._file_lock_depth == 0 and self._file_lock_handle is not None:
                fcntl.flock(self._file_lock_handle.fileno(), fcntl.LOCK_UN)
                self._file_lock_handle.close()
                self._file_lock_handle = None

    def _read_unlocked(self) -> State:
        if not self.path.exists():
            state = new_default_state()
            self._merge_split_domains(state)
            return state

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
        state["kv_cache"] = state.get("kv_cache", {})
        state["news_processing_runs"] = state.get("news_processing_runs", {})
        state["prediction_artifacts"] = state.get("prediction_artifacts", {})
        state["llm_credentials"] = state.get("llm_credentials", {})
        self._merge_split_domains(state)
        return state

    def _split_state_dir(self) -> Path:
        return self.path.with_name(f"{self.path.name}.d")

    def _split_state_path(self, key: str) -> Path:
        return self._split_state_dir() / f"{key}.json"

    def _write_json_atomic(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_name(
            f"{self.path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
        )
        with temp_path.open("w", encoding="utf-8") as state_file:
            json.dump(payload, state_file, indent=2, sort_keys=True)
        temp_path.replace(path)

    def _merge_split_domains(self, state: State) -> None:
        for key in SPLIT_STATE_KEYS:
            split_path = self._split_state_path(key)
            if not split_path.exists():
                continue
            try:
                with split_path.open("r", encoding="utf-8") as split_file:
                    loaded = json.load(split_file)
            except (OSError, ValueError):
                continue
            if isinstance(loaded, dict):
                state[key] = loaded

    def _write_unlocked(self, state: State) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        main_state = copy.deepcopy(state)
        for key in SPLIT_STATE_KEYS:
            split_payload = state.get(key, {})
            self._write_json_atomic(
                self._split_state_path(key),
                split_payload if isinstance(split_payload, dict) else {},
            )
            main_state[key] = {}
        self._write_json_atomic(self.path, main_state)

    def read(self) -> State:
        with self._lock:
            return self._read_unlocked()

    def write(self, state: State) -> None:
        with self._lock:
            with self._file_lock():
                self._write_unlocked(state)

    def update(self, mutator: Callable[[State], T]) -> T:
        with self._lock:
            with self._file_lock():
                state = self._read_unlocked()
                result = mutator(state)
                self._write_unlocked(state)
                return result
