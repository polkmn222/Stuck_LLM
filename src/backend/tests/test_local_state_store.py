import time
from pathlib import Path

from app.shared.state_store import LocalStateStore


def test_local_state_store_persists_state_and_merges_defaults(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    store = LocalStateStore(state_path)

    assert store.read()["settings"]["analysis_mode"] == "quick"

    def mutate(state: dict) -> str:
        state["settings"]["analysis_mode"] = "deep"
        state["conversations"]["conv_test"] = {"messages": []}
        return "saved"

    assert store.update(mutate) == "saved"

    restored_store = LocalStateStore(state_path)
    restored_state = restored_store.read()

    assert restored_state["settings"]["analysis_mode"] == "deep"
    assert restored_state["conversations"]["conv_test"] == {"messages": []}


def test_local_state_store_splits_cache_and_artifact_domains(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    store = LocalStateStore(state_path)

    def mutate(state: dict) -> None:
        state["kv_cache"]["cache:one"] = {"payload": {"value": "cached-value"}}
        state["news_processing_runs"]["run_one"] = {"cache_hits": 1}
        state["prediction_artifacts"]["artifact_one"] = {"summary": "artifact-value"}

    store.update(mutate)

    split_dir = state_path.with_name(f"{state_path.name}.d")
    state_text = state_path.read_text()
    restored_state = LocalStateStore(state_path).read()

    assert "cached-value" not in state_text
    assert "artifact-value" not in state_text
    assert (split_dir / "kv_cache.json").exists()
    assert (split_dir / "news_processing_runs.json").exists()
    assert (split_dir / "prediction_artifacts.json").exists()
    assert restored_state["kv_cache"]["cache:one"]["payload"]["value"] == "cached-value"
    assert restored_state["news_processing_runs"]["run_one"]["cache_hits"] == 1
    assert restored_state["prediction_artifacts"]["artifact_one"]["summary"] == "artifact-value"


def test_local_state_store_skips_unchanged_split_domain_writes(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    store = LocalStateStore(state_path)

    def seed(state: dict) -> None:
        state["kv_cache"]["cache:one"] = {"payload": {"value": "cached-value"}}
        state["news_processing_runs"]["run_one"] = {"cache_hits": 1}
        state["prediction_artifacts"]["artifact_one"] = {"summary": "artifact-value"}

    store.update(seed)
    split_dir = state_path.with_name(f"{state_path.name}.d")
    kv_cache_path = split_dir / "kv_cache.json"
    news_runs_path = split_dir / "news_processing_runs.json"
    artifacts_path = split_dir / "prediction_artifacts.json"
    initial_mtimes = {
        "kv_cache": kv_cache_path.stat().st_mtime_ns,
        "news_processing_runs": news_runs_path.stat().st_mtime_ns,
        "prediction_artifacts": artifacts_path.stat().st_mtime_ns,
    }

    time.sleep(0.02)

    def update_cache_only(state: dict) -> None:
        state["kv_cache"]["cache:two"] = {"payload": {"value": "new-cache-value"}}

    store.update(update_cache_only)

    assert kv_cache_path.stat().st_mtime_ns > initial_mtimes["kv_cache"]
    assert news_runs_path.stat().st_mtime_ns == initial_mtimes["news_processing_runs"]
    assert artifacts_path.stat().st_mtime_ns == initial_mtimes["prediction_artifacts"]
