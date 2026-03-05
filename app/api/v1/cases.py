import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db
from app.core.security import require_auth
from app.models.case import CreateCaseRequest, IncidentCase, UpdateCaseRequest
from app.models.user import User
from app.services import case_service

router = APIRouter(prefix="/cases", tags=["Incidenty"])


@router.get(
    "/",
    response_model=list[IncidentCase],
    summary="Seznam incidentů",
)
async def list_cases(
    current_user: User = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[IncidentCase]:
    return await case_service.list_cases(db)


@router.post(
    "/",
    response_model=IncidentCase,
    status_code=201,
    summary="Vytvoření incidentu ze šablony",
    description="Klonuje šablonu do nového JSON dokumentu incidentu. Nevyžaduje žádné další vstupní pole.",
)
async def create_case(
    request: CreateCaseRequest,
    current_user: User = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
) -> IncidentCase:
    try:
        return await case_service.create_case(db, request, current_user.username)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{case_id}",
    response_model=IncidentCase,
    summary="Detail incidentu",
)
async def get_case(
    case_id: str,
    current_user: User = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
) -> IncidentCase:
    case = await case_service.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Incident '{case_id}' nebyl nalezen")
    return case


@router.patch(
    "/{case_id}",
    response_model=IncidentCase,
    summary="Aktualizace incidentu",
    description="Aktualizuje status workflow a/nebo kompletní JSON dokument incidentu.",
)
async def update_case(
    case_id: str,
    request: UpdateCaseRequest,
    current_user: User = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
) -> IncidentCase:
    case = await case_service.update_case(db, case_id, request)
    if not case:
        raise HTTPException(status_code=404, detail=f"Incident '{case_id}' nebyl nalezen")
    return case
