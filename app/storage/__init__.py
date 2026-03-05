from pathlib import Path

import aiosqlite
from fastapi import Depends

from app.config import settings
from app.core.database import get_db
from app.services.settings_service import get_setting
from app.storage.base import StorageBackend
from app.storage.file_backend import FileStorageBackend


async def get_storage(db: aiosqlite.Connection = Depends(get_db)) -> StorageBackend:
    """
    FastAPI dependency – vrátí instanci storage backendu dle konfigurace v DB.
    Pro přepnutí na jiný backend (Elastic, Mongo) stačí upravit tuto funkci.
    """
    incidents_dir = Path(
        await get_setting(db, "incidents_dir") or settings.default_incidents_dir
    )
    return FileStorageBackend(incidents_dir)
