from pydantic import BaseModel, ConfigDict
from typing import Any, Optional


class SOCTemplate(BaseModel):
    model_config = ConfigDict(extra="allow")  # JSON šablony mohou obsahovat libovolná rozšíření

    template_id: str
    name: str
    version: str = "1.0"
    category: str
    status: str = "active"        # active | draft | deprecated
    description: Optional[str] = None
    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    mitre_subtechnique: Optional[str] = None
    data_sources: list[str] = []  # zdroje dat pro investigaci
    sections: list[Any] = []

    # Metadata ze souborového systému – není součástí JSON šablony
    filename: Optional[str] = None
