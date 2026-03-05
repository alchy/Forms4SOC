import json
import logging
from pathlib import Path
from typing import Optional

from app.models.template import SOCTemplate

logger = logging.getLogger(__name__)


def load_templates_from_dir(templates_dir: Path) -> list[SOCTemplate]:
    """
    Synchronní načtení šablon z adresáře – používá se při startu a v sync kontextech.
    Pro async kontext použij storage.list_templates().
    """
    templates: list[SOCTemplate] = []

    if not templates_dir.exists():
        templates_dir.mkdir(parents=True, exist_ok=True)
        return templates

    for json_file in sorted(templates_dir.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            template = SOCTemplate(**data, filename=json_file.name)
            templates.append(template)
        except Exception as exc:
            logger.warning("Cannot load template '%s': %s", json_file.name, exc)

    return templates
