from abc import ABC, abstractmethod
from typing import Optional

from app.models.case import IncidentCase
from app.models.template import SOCTemplate


class StorageBackend(ABC):
    """
    Abstraktní rozhraní pro ukládání incidentů a šablon.
    Implementace: FileStorageBackend (JSON soubory), budoucí Elasticsearch, MongoDB, …
    """

    # --- Incidenty ---

    @abstractmethod
    async def list_cases(self) -> list[IncidentCase]:
        """Vrátí všechny incidenty seřazené od nejnovějšího."""

    @abstractmethod
    async def get_case(self, case_id: str) -> Optional[IncidentCase]:
        """Vrátí incident dle case_id nebo None."""

    @abstractmethod
    async def save_case(self, case: IncidentCase) -> None:
        """Uloží incident (vytvoření i aktualizace)."""

    @abstractmethod
    async def delete_case(self, case_id: str) -> bool:
        """Smaže incident. Vrátí True pokud existoval."""

    # --- Zámky ---

    @abstractmethod
    async def acquire_lock(self, case_id: str, username: str) -> bool:
        """
        Pokusí se získat zámek pro incident.
        Vrátí True pokud byl zámek úspěšně získán nebo již patří stejnému uživateli.
        Vrátí False pokud je incident zamčen jiným uživatelem.
        """

    @abstractmethod
    async def release_lock(self, case_id: str, username: str, force: bool = False) -> bool:
        """
        Uvolní zámek incidentu.
        force=True umožní uvolnit zámek bez ohledu na vlastníka (pro admin).
        Vrátí True pokud byl zámek uvolněn nebo neexistoval.
        """

    @abstractmethod
    async def get_lock_info(self, case_id: str) -> Optional[dict]:
        """Vrátí informace o zámku {locked_by, locked_at} nebo None pokud nezamčeno."""

    # --- Šablony ---

    @abstractmethod
    async def list_templates(self) -> list[SOCTemplate]:
        """Vrátí seznam všech dostupných šablon."""

    @abstractmethod
    async def get_template(self, template_id: str) -> Optional[SOCTemplate]:
        """Vrátí šablonu dle template_id nebo None."""
