import json
import logging
from pathlib import Path
from typing import Optional

from app.config import settings
from app.models.template import SOCTemplate

logger = logging.getLogger(__name__)


def load_all_templates() -> list[SOCTemplate]:
    """
    Načte všechny JSON šablony z adresáře playbooks/.

    Adresář je zdrojem pravdy – šablony se načítají při každém requestu,
    takže přidání nebo odebrání JSON souboru se projeví okamžitě bez restartu.
    Poškozené soubory jsou přeskočeny a zalogována chyba.
    """
    playbooks_dir: Path = settings.playbooks_dir
    templates: list[SOCTemplate] = []

    if not playbooks_dir.exists():
        playbooks_dir.mkdir(parents=True, exist_ok=True)
        return templates

    for json_file in sorted(playbooks_dir.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            template = SOCTemplate(**data, filename=json_file.name)
            templates.append(template)
        except Exception as exc:
            logger.warning("Cannot load template '%s': %s", json_file.name, exc)

    return templates


def get_template(template_id: str) -> Optional[SOCTemplate]:
    """Načte konkrétní šablonu dle template_id. Vrátí None pokud nenalezena."""
    for template in load_all_templates():
        if template.template_id == template_id:
            return template
    return None
