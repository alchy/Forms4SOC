import aiosqlite
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.core.security import require_admin
from app.models.user import User
from app.services.settings_service import get_all_settings, set_setting

router = APIRouter(prefix="/settings", tags=["Nastavení"])


@router.get(
    "/",
    summary="Aktuální nastavení (admin)",
)
async def get_settings(
    current_user: User = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, str]:
    return await get_all_settings(db)


@router.patch(
    "/",
    summary="Aktualizace nastavení (admin)",
)
async def update_settings(
    updates: dict[str, str],
    current_user: User = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, str]:
    allowed_keys = {"incidents_dir", "templates_dir"}
    for key, value in updates.items():
        if key in allowed_keys:
            await set_setting(db, key, value)
    return await get_all_settings(db)
