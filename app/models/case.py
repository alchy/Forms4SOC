from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime


class IncidentCase(BaseModel):
    id: Optional[int] = None
    case_id: str
    template_id: str
    status: str = "open"          # open | in_progress | closed | false_positive
    created_by: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    data: dict[str, Any] = {}     # kompletní JSON dokument (klon šablony + hodnoty analytika)


class CreateCaseRequest(BaseModel):
    template_id: str              # vše ostatní pochází ze šablony nebo se generuje


class UpdateCaseRequest(BaseModel):
    status: Optional[str] = None         # volitelná změna stavu workflow
    data: Optional[dict[str, Any]] = None  # volitelná aktualizace dokumentu
