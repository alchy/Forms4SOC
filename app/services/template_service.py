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
    Přístup k read-only JSON šablonám ze souborového systému.
    Odděleno od StorageBackend – šablony nemají CRUD ani zámky.
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


async def get_template_service(db: aiosqlite.Connection = Depends(get_db)) -> TemplateService:
    """FastAPI dependency – vrátí TemplateService nakonfigurovaný dle nastavení v DB."""
    templates_dir = Path(
        await get_setting(db, "templates_dir") or settings.default_templates_dir
    )
    return TemplateService(templates_dir)
