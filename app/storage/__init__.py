from pathlib import Path

import aiosqlite

from app.services.settings_service import get_setting
from app.storage.base import StorageBackend
from app.storage.file_backend import FileStorageBackend


async def get_storage_backend(db: aiosqlite.Connection) -> StorageBackend:
    """
    Factory – vrátí instanci storage backendu dle konfigurace uložené v DB.
    Výchozí hodnoty jsou definovány v app/config.py.
    Pro přepnutí na jiný backend (Elastic, Mongo) stačí změnit tuto funkci.
    """
    from app.config import settings

    incidents_dir = Path(
        await get_setting(db, "incidents_dir") or settings.default_incidents_dir
    )
    templates_dir = Path(
        await get_setting(db, "templates_dir") or settings.default_templates_dir
    )
    return FileStorageBackend(incidents_dir, templates_dir)
