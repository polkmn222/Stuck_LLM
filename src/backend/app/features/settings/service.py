from typing import Any, Dict

from app.features.settings.schemas import Settings, SettingsUpdate
from app.shared.state_store import LocalStateStore, State


def _model_dump(model: SettingsUpdate) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=True)
    return model.dict(exclude_unset=True)


def _settings_dump(settings: Settings) -> Dict[str, Any]:
    if hasattr(settings, "model_dump"):
        return settings.model_dump()
    return settings.dict()


def _settings_copy(settings: Settings, update_data: Dict[str, Any]) -> Settings:
    if hasattr(settings, "model_copy"):
        return settings.model_copy(update=update_data)
    return settings.copy(update=update_data)


def get_settings(store: LocalStateStore) -> Settings:
    state = store.read()
    return Settings(**state["settings"])


def update_settings(store: LocalStateStore, update: SettingsUpdate) -> Settings:
    update_data = _model_dump(update)

    def mutate(state: State) -> Settings:
        settings = Settings(**state["settings"])
        next_settings = _settings_copy(settings, update_data)
        state["settings"] = _settings_dump(next_settings)
        return next_settings

    return store.update(mutate)
