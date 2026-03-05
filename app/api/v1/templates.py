from fastapi import APIRouter, Depends, HTTPException

from app.core.security import require_auth
from app.models.template import SOCTemplate
from app.models.user import User
from app.services.template_service import TemplateService, get_template_service

router = APIRouter(prefix="/templates", tags=["Šablony"])


@router.get(
    "/",
    response_model=list[SOCTemplate],
    summary="Seznam SOC šablon",
)
async def list_templates(
    current_user: User = Depends(require_auth),
    svc: TemplateService = Depends(get_template_service),
) -> list[SOCTemplate]:
    return await svc.list_templates()


@router.get(
    "/{template_id}",
    response_model=SOCTemplate,
    summary="Detail šablony",
)
async def get_template_by_id(
    template_id: str,
    current_user: User = Depends(require_auth),
    svc: TemplateService = Depends(get_template_service),
) -> SOCTemplate:
    template = await svc.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Šablona '{template_id}' nebyla nalezena")
    return template
