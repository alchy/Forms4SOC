import json
import logging
from pathlib import Path
from typing import Optional

import aiosqlite
from fastapi import Depends

from app.config import settings
from app.core.database import get_db
from app.models.template import SOCTemplate
from app.services.settings_service import get_setting

logger = logging.getLogger(__name__)


class TemplateService:
    """
    Přístup k JSON šablonám ze souborového systému.
    Odděleno od StorageBackend – šablony mají vlastní CRUD bez zámků.
    """

    def __init__(self, templates_dir: Path) -> None:
        self.templates_dir = templates_dir
        templates_dir.mkdir(parents=True, exist_ok=True)

    async def list_templates(self) -> list[SOCTemplate]:
        result = []
        for json_file in sorted(self.templates_dir.glob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                result.append(SOCTemplate(**data, filename=json_file.name))
            except Exception as exc:
                logger.warning("Cannot load template '%s': %s", json_file.name, exc)
        return result

    async def get_template(self, template_id: str) -> Optional[SOCTemplate]:
        for template in await self.list_templates():
            if template.template_id == template_id:
                return template
        return None

    def _find_file(self, template_id: str) -> Optional[Path]:
        """Najde soubor šablony dle template_id."""
        for json_file in self.templates_dir.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if data.get("template_id") == template_id:
                    return json_file
            except Exception:
                pass
        return None

    async def get_source(self, template_id: str) -> Optional[dict]:
        """Vrátí {'content': str, 'filename': str} nebo None."""
        path = self._find_file(template_id)
        if not path:
            return None
        return {"content": path.read_text(encoding="utf-8"), "filename": path.name}

    async def save(self, template_id: str, content: str) -> str:
        """Validuje JSON a přepíše existující soubor. Vrátí filename."""
        json.loads(content)  # vyvolá ValueError pokud není validní JSON
        path = self._find_file(template_id)
        if not path:
            raise FileNotFoundError(f"Šablona '{template_id}' nebyla nalezena")
        path.write_text(content, encoding="utf-8")
        return path.name

    async def create(self, filename: str, content: str) -> str:
        """Validuje JSON a vytvoří nový soubor. Vrátí template_id z obsahu."""
        json.loads(content)  # vyvolá ValueError pokud není validní JSON
        if not filename.endswith(".json"):
            filename += ".json"
        target = self.templates_dir / filename
        if target.exists():
            raise FileExistsError(f"Soubor '{filename}' již existuje")
        target.write_text(content, encoding="utf-8")
        data = json.loads(content)
        return data.get("template_id", filename.replace(".json", ""))

    async def delete(self, template_id: str) -> None:
        """Smaže soubor šablony."""
        path = self._find_file(template_id)
        if not path:
            raise FileNotFoundError(f"Šablona '{template_id}' nebyla nalezena")
        path.unlink()


async def get_template_service(db: aiosqlite.Connection = Depends(get_db)) -> TemplateService:
    """FastAPI dependency – vrátí TemplateService nakonfigurovaný dle nastavení v DB."""
    templates_dir = Path(
        await get_setting(db, "templates_dir") or settings.default_templates_dir
    )
    return TemplateService(templates_dir)
