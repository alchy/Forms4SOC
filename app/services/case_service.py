import copy
import json
from datetime import datetime, timezone
from typing import Optional

import aiosqlite

from app.models.case import CreateCaseRequest, IncidentCase, UpdateCaseRequest
from app.services.template_service import get_template


async def _generate_case_id(db: aiosqlite.Connection) -> str:
    """Generuje unikátní ID incidentu ve formátu INC-YYYY-NNNN."""
    year = datetime.now(timezone.utc).year
    async with db.execute(
        "SELECT COUNT(*) FROM cases WHERE case_id LIKE ?", (f"INC-{year}-%",)
    ) as cursor:
        row = await cursor.fetchone()
        count = row[0] + 1
    return f"INC-{year}-{count:04d}"


def _strip_examples(obj: object) -> None:
    """
    Rekurzivně projde JSON strukturu a zpracuje pole označená is_example: true.

    Design princip:
      - V šabloně jsou příkladové hodnoty (odpovídají kurzívě v markdown) označeny
        is_example: true a mají vyplněné value / analyst_note.
      - Při klonování do nového case se tato hodnota přesune do klíče 'example'
        (slouží jako placeholder v UI) a 'value' / 'analyst_note' se nastaví na null.
      - Hodnoty bez is_example (plain text v markdown) se kopírují beze změny.
    """
    if isinstance(obj, list):
        for item in obj:
            _strip_examples(item)
    elif isinstance(obj, dict):
        if obj.get("is_example", False):
            if "value" in obj:
                # Form fields: value → example
                if obj["value"] is not None:
                    obj["example"] = obj["value"]
                    obj["value"] = None
            elif "analyst_note" in obj:
                # Checklist steps: analyst_note → example
                if obj["analyst_note"] is not None:
                    obj["example"] = obj["analyst_note"]
                    obj["analyst_note"] = None
            else:
                # Table rows (contact_table apod.): každý editovatelný string klíč → {key}_example
                _SYSTEM_KEYS = {"id", "is_example", "system_role", "when_to_contact",
                                 "type", "title", "action", "done"}
                for key in list(obj.keys()):
                    if key not in _SYSTEM_KEYS and not key.endswith("_example"):
                        if obj[key] is not None:
                            obj[key + "_example"] = obj[key]
                            obj[key] = None
        for v in obj.values():
            if isinstance(v, (dict, list)):
                _strip_examples(v)


def _fill_auto_values(sections: list, case_id: str) -> None:
    """Vyplní pole označená auto_value skutečnými systémovými hodnotami."""
    for section in sections:
        for field in section.get("fields", []):
            if field.get("auto_value") == "case_id":
                field["value"] = case_id
        for subsection in section.get("subsections", []):
            for field in subsection.get("fields", []):
                if field.get("auto_value") == "case_id":
                    field["value"] = case_id


def _clone_template_sections(sections: list) -> list:
    """
    Hluboká kopie sekcí šablony pro nový incident.
    Příkladové hodnoty (is_example: true) jsou přesunuty do 'example' jako placeholder,
    skutečné hodnoty analytika začínají jako null.
    """
    cloned = copy.deepcopy(sections)
    _strip_examples(cloned)
    return cloned


def _row_to_case(row: aiosqlite.Row) -> IncidentCase:
    """Převede DB řádek na model IncidentCase."""
    return IncidentCase(
        id=row["id"],
        case_id=row["case_id"],
        template_id=row["template_id"],
        status=row["status"],
        created_by=row["created_by"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        data=json.loads(row["data"]),
    )


async def create_case(
    db: aiosqlite.Connection,
    request: CreateCaseRequest,
    username: str,
) -> IncidentCase:
    """
    Vytvoří nový incident jako klon šablony.
    Celá struktura šablony (sekce, kroky, pole) se zkopíruje do data dokumentu.
    Analytik poté vyplňuje hodnoty přímo v dokumentu.
    """
    template = get_template(request.template_id)
    if not template:
        raise ValueError(f"Šablona '{request.template_id}' nenalezena")

    case_id = await _generate_case_id(db)
    now = datetime.now(timezone.utc).isoformat()

    # JSON dokument = metadata šablony + klonované sekce připravené k vyplnění
    document = {
        "template_id": template.template_id,
        "template_version": template.version,
        "template_name": template.name,
        "category": template.category,
        "mitre_tactic": template.mitre_tactic,
        "mitre_technique": template.mitre_technique,
        "data_sources": template.data_sources,
        "sections": _clone_template_sections(template.sections),
    }
    _fill_auto_values(document["sections"], case_id)

    await db.execute(
        """
        INSERT INTO cases (case_id, template_id, status, created_by, created_at, updated_at, data)
        VALUES (?, ?, 'open', ?, ?, ?, ?)
        """,
        (case_id, request.template_id, username, now, now, json.dumps(document, ensure_ascii=False)),
    )
    await db.commit()

    return IncidentCase(
        case_id=case_id,
        template_id=request.template_id,
        status="open",
        created_by=username,
        created_at=datetime.fromisoformat(now),
        updated_at=datetime.fromisoformat(now),
        data=document,
    )


async def list_cases(db: aiosqlite.Connection) -> list[IncidentCase]:
    """Vrátí všechny incidenty seřazené od nejnovějšího."""
    async with db.execute("SELECT * FROM cases ORDER BY created_at DESC") as cursor:
        rows = await cursor.fetchall()
    return [_row_to_case(row) for row in rows]


async def get_case(db: aiosqlite.Connection, case_id: str) -> Optional[IncidentCase]:
    """Vrátí konkrétní incident dle case_id nebo None."""
    async with db.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)) as cursor:
        row = await cursor.fetchone()
    return _row_to_case(row) if row else None


async def update_case(
    db: aiosqlite.Connection,
    case_id: str,
    request: UpdateCaseRequest,
) -> Optional[IncidentCase]:
    """
    Aktualizuje incident – status workflow a/nebo celý JSON dokument.
    Dokument se nahrazuje celý (klient posílá kompletní aktualizovaný stav).
    """
    case = await get_case(db, case_id)
    if not case:
        return None

    new_status = request.status if request.status is not None else case.status
    new_data = request.data if request.data is not None else case.data
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        "UPDATE cases SET status = ?, data = ?, updated_at = ? WHERE case_id = ?",
        (new_status, json.dumps(new_data, ensure_ascii=False), now, case_id),
    )
    await db.commit()

    case.status = new_status
    case.data = new_data
    case.updated_at = datetime.fromisoformat(now)
    return case
