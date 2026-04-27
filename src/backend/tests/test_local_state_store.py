from pathlib import Path

from app.shared.state_store import LocalStateStore


def test_local_state_store_persists_state_and_merges_defaults(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    store = LocalStateStore(state_path)

    assert store.read()["settings"]["provider"] == "openai"

    def mutate(state: dict) -> str:
        state["settings"]["provider"] = "gemini"
        state["conversations"]["conv_test"] = {"messages": []}
        return "saved"

    assert store.update(mutate) == "saved"

    restored_store = LocalStateStore(state_path)
    restored_state = restored_store.read()

    assert restored_state["settings"]["provider"] == "gemini"
    assert restored_state["settings"]["analysis_mode"] == "quick"
    assert restored_state["conversations"]["conv_test"] == {"messages": []}
