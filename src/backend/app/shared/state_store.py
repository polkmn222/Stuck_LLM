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

    def _write_unlocked(self, state: State) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_name(
            f"{self.path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
        )
        with temp_path.open("w", encoding="utf-8") as state_file:
            json.dump(state, state_file, indent=2, sort_keys=True)
        temp_path.replace(self.path)

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
