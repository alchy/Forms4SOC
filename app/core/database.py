from collections.abc import AsyncGenerator
from pathlib import Path

import aiosqlite

from app.config import settings
from app.core.security import hash_password


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """FastAPI dependency – poskytuje DB spojení pro jeden request."""
    async with aiosqlite.connect(settings.database_path) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db() -> None:
    """Inicializuje SQLite databázi, vytvoří tabulky a seed admin uživatele."""
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(settings.database_path) as db:
        db.row_factory = aiosqlite.Row

        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                username         TEXT    UNIQUE NOT NULL,
                hashed_password  TEXT    NOT NULL,
                role             TEXT    NOT NULL DEFAULT 'analyst',
                is_active        INTEGER NOT NULL DEFAULT 1,
                created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)

        # Výchozí nastavení (přepsatelná adminem v GUI)
        await db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('incidents_dir', ?)",
            (settings.default_incidents_dir,),
        )
        await db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('templates_dir', ?)",
            (settings.default_templates_dir,),
        )
        await db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('app_name', ?)",
            (settings.app_name,),
        )
        await db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('app_version', ?)",
            (settings.app_version,),
        )
        await db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('app_subtitle', ?)",
            (settings.app_subtitle,),
        )

        # Seed admin uživatele pokud žádný neexistuje
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            user_count = row[0]

        if user_count == 0:
            await db.execute(
                "INSERT INTO users (username, hashed_password, role, is_active) VALUES (?, ?, 'admin', 1)",
                (settings.admin_username, hash_password(settings.admin_password)),
            )

        await db.commit()
