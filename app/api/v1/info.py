import aiosqlite
from fastapi import APIRouter, Depends

from app.config import settings as app_settings
from app.core.database import get_db
from app.services.settings_service import get_setting

router = APIRouter(prefix="/info", tags=["Info"])


@router.get("/", summary="Informace o aplikaci (veřejné)")
async def get_info(db: aiosqlite.Connection = Depends(get_db)) -> dict[str, str]:
    """Vrátí název, verzi a podtitulek aplikace. Nevyžaduje autentizaci."""
    return {
        "app_name":    await get_setting(db, "app_name")    or app_settings.app_name,
        "app_version": await get_setting(db, "app_version") or app_settings.app_version,
        "app_subtitle": await get_setting(db, "app_subtitle") or app_settings.app_subtitle,
    }
