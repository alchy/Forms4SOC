from fastapi import APIRouter, Depends, HTTPException

from app.core.security import require_auth
from app.models.template import SOCTemplate
from app.models.user import User
from app.services.template_service import get_template, load_all_templates

router = APIRouter(prefix="/templates", tags=["Šablony"])


@router.get(
    "/",
    response_model=list[SOCTemplate],
    summary="Seznam SOC šablon",
    description="Vrátí seznam všech dostupných šablon načtených z adresáře playbooks/.",
)
async def list_templates(current_user: User = Depends(require_auth)) -> list[SOCTemplate]:
    return load_all_templates()


@router.get(
    "/{template_id}",
    response_model=SOCTemplate,
    summary="Detail šablony",
    description="Vrátí kompletní detail šablony včetně sekcí.",
)
async def get_template_by_id(
    template_id: str,
    current_user: User = Depends(require_auth),
) -> SOCTemplate:
    template = get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Šablona '{template_id}' nebyla nalezena",
        )
    return template
