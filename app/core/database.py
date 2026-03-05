from collections.abc import AsyncGenerator

import aiosqlite

from app.config import settings


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """FastAPI dependency – poskytuje DB spojení pro jeden request."""
    async with aiosqlite.connect(settings.database_path) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db() -> None:
    """Inicializuje SQLite databázi a vytvoří tabulky (spouští se při startu)."""
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(settings.database_path) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                username         TEXT    UNIQUE NOT NULL,
                hashed_password  TEXT    NOT NULL,
                role             TEXT    NOT NULL DEFAULT 'analyst',
                is_active        INTEGER NOT NULL DEFAULT 1,
                created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS cases (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id      TEXT    UNIQUE NOT NULL,
                template_id  TEXT    NOT NULL,
                status       TEXT    NOT NULL DEFAULT 'open',
                created_by   TEXT    NOT NULL,
                created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at   TEXT    NOT NULL DEFAULT (datetime('now')),
                data         TEXT    NOT NULL DEFAULT '{}'
            );
            -- data sloupec je JSON dokument – klon šablony s hodnotami analytika.
            -- Pole jako severity, title atd. jsou součástí data dokumentu, ne schématu.
        """)
        await db.commit()
