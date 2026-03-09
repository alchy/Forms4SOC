from pathlib import Path

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, status

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
    allowed_keys = {"incidents_dir", "templates_dir", "app_name", "app_version", "app_subtitle"}
    for key, value in updates.items():
        if key not in allowed_keys:
            continue
        if not value or not value.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"Hodnota pro '{key}' nesmí být prázdná.")
        try:
            p = Path(value)
        except Exception:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"Hodnota pro '{key}' není platná cesta.")
        if ".." in p.parts:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"Hodnota pro '{key}' nesmí obsahovat '..'.")
        if not p.exists():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=f"Adresář '{value}' neexistuje.")
        await set_setting(db, key, value)
    return await get_all_settings(db)
