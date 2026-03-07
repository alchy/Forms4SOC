from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import require_admin, require_auth
from app.models.template import SOCTemplate
from app.models.user import User
from app.services.template_service import TemplateService, get_template_service

router = APIRouter(prefix="/templates", tags=["Šablony"])


class TemplateSaveBody(BaseModel):
    content: str


class TemplateCreateBody(BaseModel):
    filename: str
    content: str


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


@router.post(
    "/",
    summary="Vytvoření nové šablony (admin)",
)
async def create_template(
    body: TemplateCreateBody,
    current_user: User = Depends(require_admin),
    svc: TemplateService = Depends(get_template_service),
):
    try:
        template_id = await svc.create(body.filename, body.content)
        return {"ok": True, "template_id": template_id, "filename": body.filename.rstrip(".yaml") + ".yaml"}
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Neplatný YAML: {exc}")


@router.get(
    "/{template_id}/source",
    summary="Zdrojový JSON šablony (admin)",
)
async def get_template_source(
    template_id: str,
    current_user: User = Depends(require_admin),
    svc: TemplateService = Depends(get_template_service),
):
    source = await svc.get_source(template_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Šablona '{template_id}' nebyla nalezena")
    return source


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


@router.put(
    "/{template_id}",
    summary="Uložení šablony (admin)",
)
async def save_template(
    template_id: str,
    body: TemplateSaveBody,
    current_user: User = Depends(require_admin),
    svc: TemplateService = Depends(get_template_service),
):
    try:
        filename = await svc.save(template_id, body.content)
        return {"ok": True, "filename": filename}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Neplatný YAML: {exc}")


@router.delete(
    "/{template_id}",
    status_code=204,
    summary="Smazání šablony (admin)",
)
async def delete_template(
    template_id: str,
    current_user: User = Depends(require_admin),
    svc: TemplateService = Depends(get_template_service),
):
    try:
        await svc.delete(template_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
