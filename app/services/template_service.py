import logging
import re
import unicodedata
from pathlib import Path
from typing import Optional

import yaml

import aiosqlite
from fastapi import Depends

from app.config import settings
from app.core.database import get_db
from app.models.template import SOCTemplate
from app.services.settings_service import get_setting

logger = logging.getLogger(__name__)


# ── Normalizátor šablony ───────────────────────────────────────────────────
#
# Umožňuje psát šablony ve zjednodušeném formátu:
#   - pole bez `type` → výchozí "text"
#   - pole bez `editable` → výchozí true
#   - pole bez `value` → výchozí null
#   - kroky v checklist jako prostý řetězec → automaticky rozbalí na {action: ...}
#   - kroky a skupiny bez `id` → ID se vygeneruje ze `title` nebo pořadí
#   - sekce bez `id` → ID se vygeneruje z `title` nebo `type`
#
# Plný formát (stávající šablony) zůstává beze změny (zpětně kompatibilní).

def _slugify(text: str) -> str:
    """Převede text na ASCII slug s podtržítky (pro generování ID)."""
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s\-]+", "_", text)
    return text or "item"


def _norm_field(field: dict) -> dict:
    """Doplní výchozí hodnoty pro pole formuláře."""
    field.setdefault("type", "text")
    field.setdefault("editable", True)
    field.setdefault("value", None)
    return field


def _norm_step(step, idx: int, prefix: str) -> dict:
    """Rozbalí string krok nebo doplní výchozí hodnoty dict kroku."""
    if isinstance(step, str):
        step = {"action": step}
    step.setdefault("id", f"{prefix}_{idx + 1:02d}")
    step.setdefault("analyst_note", None)
    step.setdefault("done", False)
    return step


def _norm_group(group: dict, idx: int, section_id: str) -> dict:
    """Doplní ID skupiny a normalizuje její kroky."""
    group_id = group.get("id") or _slugify(group.get("title", f"group_{idx + 1}"))
    group["id"] = group_id
    prefix = f"{section_id}_{group_id}"
    group["steps"] = [
        _norm_step(s, i, prefix) for i, s in enumerate(group.get("steps", []))
    ]
    return group


def _norm_section(section: dict, idx: int) -> dict:
    """Doplní ID sekce a normalizuje pole a skupiny kroků."""
    title = section.get("title", "")
    section_id = section.get("id") or _slugify(
        title or section.get("type", f"section_{idx + 1}")
    )
    section["id"] = section_id

    if "fields" in section:
        section["fields"] = [_norm_field(f) for f in section["fields"]]

    if "step_groups" in section:
        section["step_groups"] = [
            _norm_group(g, i, section_id)
            for i, g in enumerate(section["step_groups"])
        ]
    if "subsections" in section:
        section["subsections"] = [
            _norm_section(sub, i) for i, sub in enumerate(section["subsections"])
        ]
    return section


def _normalize_template(data: dict) -> dict:
    """Normalizuje surová YAML data šablony – doplní výchozí hodnoty a rozbalí zkratky."""
    if "sections" in data and isinstance(data["sections"], list):
        data["sections"] = [
            _norm_section(s, i) for i, s in enumerate(data["sections"])
        ]
    return data


# ── TemplateService ────────────────────────────────────────────────────────

class TemplateService:
    """
    Přístup k YAML šablonám ze souborového systému.
    Odděleno od StorageBackend – šablony mají vlastní CRUD bez zámků.
    """

    def __init__(self, templates_dir: Path) -> None:
        self.templates_dir = templates_dir
        templates_dir.mkdir(parents=True, exist_ok=True)

    async def list_templates(self) -> list[SOCTemplate]:
        result = []
        for yaml_file in sorted(self.templates_dir.glob("*.yaml")):
            try:
                data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
                data = _normalize_template(data)
                result.append(SOCTemplate(**data, filename=yaml_file.name))
            except Exception as exc:
                logger.warning("Cannot load template '%s': %s", yaml_file.name, exc)
        return result

    async def get_template(self, template_id: str) -> Optional[SOCTemplate]:
        for template in await self.list_templates():
            if template.template_id == template_id:
                return template
        return None

    def _find_file(self, template_id: str) -> Optional[Path]:
        """Najde soubor šablony dle template_id."""
        for yaml_file in self.templates_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
                if data.get("template_id") == template_id:
                    return yaml_file
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
        """Validuje YAML a přepíše existující soubor. Vrátí filename."""
        yaml.safe_load(content)  # vyvolá ValueError pokud není validní YAML
        path = self._find_file(template_id)
        if not path:
            raise FileNotFoundError(f"Šablona '{template_id}' nebyla nalezena")
        path.write_text(content, encoding="utf-8")
        return path.name

    async def create(self, filename: str, content: str) -> str:
        """Validuje YAML a vytvoří nový soubor. Vrátí template_id z obsahu."""
        data = yaml.safe_load(content)  # vyvolá ValueError pokud není validní YAML
        if not filename.endswith(".yaml"):
            filename += ".yaml"
        target = self.templates_dir / filename
        if target.exists():
            raise FileExistsError(f"Soubor '{filename}' již existuje")
        target.write_text(content, encoding="utf-8")
        return data.get("template_id", filename.replace(".yaml", ""))

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
