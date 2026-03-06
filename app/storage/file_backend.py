import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.models.case import IncidentCase
from app.storage.base import StorageBackend

logger = logging.getLogger(__name__)


class FileStorageBackend(StorageBackend):
    """
    Implementace StorageBackend ukládající incidenty jako JSON soubory.

    Incidenty: {incidents_dir}/{case_id}.json
    Zámky:     {incidents_dir}/{case_id}.lock
    """

    def __init__(self, incidents_dir: Path) -> None:
        self.incidents_dir = incidents_dir
        incidents_dir.mkdir(parents=True, exist_ok=True)

    def _case_path(self, case_id: str) -> Path:
        return self.incidents_dir / f"{case_id}.json"

    def _lock_path(self, case_id: str) -> Path:
        return self.incidents_dir / f"{case_id}.lock"

    def _load_case_from_path(self, path: Path) -> Optional[IncidentCase]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            case = IncidentCase(**data)
            # Přidej informaci o zámku z .lock souboru
            lock_path = self._lock_path(case.case_id)
            if lock_path.exists():
                try:
                    lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
                    case.locked_by = lock_data.get("locked_by")
                except Exception:
                    pass
            return case
        except Exception as exc:
            logger.warning("Cannot load case '%s': %s", path.name, exc)
            return None

    async def list_cases(self) -> list[IncidentCase]:
        cases = []
        json_files = sorted(
            self.incidents_dir.glob("UIB-*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for json_file in json_files:
            case = self._load_case_from_path(json_file)
            if case:
                cases.append(case)
        return cases

    async def get_case(self, case_id: str) -> Optional[IncidentCase]:
        path = self._case_path(case_id)
        if not path.exists():
            return None
        return self._load_case_from_path(path)

    async def save_case(self, case: IncidentCase) -> None:
        path = self._case_path(case.case_id)
        data = case.model_dump(mode="json", exclude={"locked_by"})
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def delete_case(self, case_id: str) -> bool:
        path = self._case_path(case_id)
        if not path.exists():
            return False
        path.unlink()
        lock_path = self._lock_path(case_id)
        if lock_path.exists():
            lock_path.unlink()
        return True

    async def acquire_lock(self, case_id: str, username: str) -> bool:
        lock_path = self._lock_path(case_id)
        if lock_path.exists():
            try:
                existing = json.loads(lock_path.read_text(encoding="utf-8"))
                if existing.get("locked_by") == username:
                    # Obnov timestamp zámku
                    lock_data = {
                        "locked_by": username,
                        "locked_at": datetime.now(timezone.utc).isoformat(),
                    }
                    lock_path.write_text(
                        json.dumps(lock_data, ensure_ascii=False), encoding="utf-8"
                    )
                    return True
                else:
                    return False  # Zamčeno jiným uživatelem
            except Exception:
                return False  # Poškozený lock soubor – považuj za zamčeno

        lock_data = {
            "locked_by": username,
            "locked_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            lock_path.write_text(json.dumps(lock_data, ensure_ascii=False), encoding="utf-8")
            return True
        except Exception as exc:
            logger.warning("Cannot acquire lock for '%s': %s", case_id, exc)
            return False

    async def release_lock(self, case_id: str, username: str, force: bool = False) -> bool:
        lock_path = self._lock_path(case_id)
        if not lock_path.exists():
            return True
        try:
            existing = json.loads(lock_path.read_text(encoding="utf-8"))
            if not force and existing.get("locked_by") != username:
                return False
            lock_path.unlink()
            return True
        except Exception as exc:
            logger.warning("Cannot release lock for '%s': %s", case_id, exc)
            return False

    async def get_lock_info(self, case_id: str) -> Optional[dict]:
        lock_path = self._lock_path(case_id)
        if not lock_path.exists():
            return None
        try:
            return json.loads(lock_path.read_text(encoding="utf-8"))
        except Exception:
            return None

