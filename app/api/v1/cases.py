import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.core.security import require_admin, require_auth
from app.models.case import CreateCaseRequest, IncidentCase, UpdateCaseRequest
from app.models.user import User
from app.services import case_service
from app.storage import get_storage_backend

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
    storage = await get_storage_backend(db)
    return await case_service.list_cases(storage)


@router.post(
    "/",
    response_model=IncidentCase,
    status_code=201,
    summary="Vytvoření incidentu ze šablony",
)
async def create_case(
    request: CreateCaseRequest,
    current_user: User = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
) -> IncidentCase:
    storage = await get_storage_backend(db)
    try:
        return await case_service.create_case(storage, request, current_user.username)
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
    storage = await get_storage_backend(db)
    case = await case_service.get_case(storage, case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Incident '{case_id}' nebyl nalezen")
    return case


@router.patch(
    "/{case_id}",
    response_model=IncidentCase,
    summary="Aktualizace incidentu",
)
async def update_case(
    case_id: str,
    request: UpdateCaseRequest,
    current_user: User = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
) -> IncidentCase:
    storage = await get_storage_backend(db)
    case = await case_service.update_case(storage, case_id, request)
    if not case:
        raise HTTPException(status_code=404, detail=f"Incident '{case_id}' nebyl nalezen")
    return case


@router.delete(
    "/{case_id}",
    status_code=204,
    summary="Smazání incidentu",
)
async def delete_case(
    case_id: str,
    current_user: User = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
) -> None:
    storage = await get_storage_backend(db)
    deleted = await case_service.delete_case(storage, case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Incident '{case_id}' nebyl nalezen")


# --- Zámky ---

@router.post(
    "/{case_id}/lock",
    summary="Získání zámku incidentu",
    description="Zamkne incident pro editaci. Vrátí 200 OK pokud zámek získán, 423 pokud zamčen jiným uživatelem.",
)
async def acquire_lock(
    case_id: str,
    current_user: User = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    storage = await get_storage_backend(db)
    case = await storage.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Incident '{case_id}' nebyl nalezen")

    acquired = await storage.acquire_lock(case_id, current_user.username)
    if not acquired:
        lock_info = await storage.get_lock_info(case_id)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                "message": "Incident je zamčen jiným uživatelem",
                "locked_by": lock_info.get("locked_by") if lock_info else None,
                "locked_at": lock_info.get("locked_at") if lock_info else None,
            },
        )
    return {"locked_by": current_user.username}


@router.delete(
    "/{case_id}/lock",
    status_code=204,
    summary="Uvolnění zámku incidentu",
)
async def release_lock(
    case_id: str,
    current_user: User = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
) -> None:
    storage = await get_storage_backend(db)
    # Admin může uvolnit zámek kohokoliv
    force = current_user.role == "admin"
    await storage.release_lock(case_id, current_user.username, force=force)
