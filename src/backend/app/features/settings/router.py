from fastapi import APIRouter, Depends

from app.features.settings.schemas import Settings, SettingsUpdate
from app.features.settings.service import get_settings, update_settings
from app.shared.dependencies import get_local_store
from app.shared.state_store import LocalStateStore

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=Settings)
def read_settings(store: LocalStateStore = Depends(get_local_store)) -> Settings:
    return get_settings(store)


@router.patch("", response_model=Settings)
def patch_settings(
    update: SettingsUpdate,
    store: LocalStateStore = Depends(get_local_store),
) -> Settings:
    return update_settings(store, update)
