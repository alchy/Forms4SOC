import aiosqlite
import jwt
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.database import get_db
from app.core.security import COOKIE_NAME, WebAdminRequired, WebLoginRequired, decode_token
from app.models.user import TokenPayload
from app.services.settings_service import get_all_settings
from app.services.template_service import TemplateService, get_template_service

router = APIRouter(tags=["Web"])
templates = Jinja2Templates(directory="app/templates")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_user_from_cookie(request: Request) -> TokenPayload | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        return decode_token(token)
    except jwt.PyJWTError:
        return None


def _user_ctx(user: TokenPayload) -> dict:
    """Převede TokenPayload na dict pro Jinja2 kontext."""
    return {"username": user.sub, "role": user.role}


# ---------------------------------------------------------------------------
# Web auth dependencies
# ---------------------------------------------------------------------------

async def require_web_user(request: Request) -> TokenPayload:
    """Dependency – vrátí přihlášeného uživatele, jinak přesměruje na /login."""
    user = _get_user_from_cookie(request)
    if not user:
        raise WebLoginRequired()
    return user


async def require_web_admin(user: TokenPayload = Depends(require_web_user)) -> TokenPayload:
    """Dependency – vyžaduje roli admin, jinak přesměruje na /dashboard."""
    if user.role != "admin":
        raise WebAdminRequired()
    return user


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if _get_user_from_cookie(request):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: TokenPayload = Depends(require_web_user),
    svc: TemplateService = Depends(get_template_service),
):
    soc_templates = await svc.list_templates()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": _user_ctx(user),
        "templates": soc_templates,
    })


@router.get("/cases", response_class=HTMLResponse)
async def cases_list(
    request: Request,
    user: TokenPayload = Depends(require_web_user),
):
    return templates.TemplateResponse("cases.html", {
        "request": request,
        "user": _user_ctx(user),
    })


@router.get("/templates", response_class=HTMLResponse)
async def templates_list(
    request: Request,
    user: TokenPayload = Depends(require_web_user),
    svc: TemplateService = Depends(get_template_service),
):
    soc_templates = await svc.list_templates()
    return templates.TemplateResponse("templates_list.html", {
        "request": request,
        "user": _user_ctx(user),
        "templates": soc_templates,
    })


@router.get("/cases/{case_id}", response_class=HTMLResponse)
async def case_detail(
    request: Request,
    case_id: str,
    user: TokenPayload = Depends(require_web_user),
):
    return templates.TemplateResponse("case_detail.html", {
        "request": request,
        "user": _user_ctx(user),
        "case_id": case_id,
    })


@router.get("/cases/{case_id}/print", response_class=HTMLResponse)
async def case_print(
    request: Request,
    case_id: str,
    user: TokenPayload = Depends(require_web_user),
):
    return templates.TemplateResponse("print_case.html", {
        "request": request,
        "case_id": case_id,
    })


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user: TokenPayload = Depends(require_web_admin),
    db: aiosqlite.Connection = Depends(get_db),
):
    current_settings = await get_all_settings(db)
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": _user_ctx(user),
        "settings": current_settings,
    })


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    user: TokenPayload = Depends(require_web_admin),
):
    return templates.TemplateResponse("admin_users.html", {
        "request": request,
        "user": _user_ctx(user),
    })


@router.get("/templates/new", response_class=HTMLResponse)
async def template_editor_new(
    request: Request,
    user: TokenPayload = Depends(require_web_admin),
    clone: str | None = None,
):
    return templates.TemplateResponse("template_editor.html", {
        "request": request,
        "user": _user_ctx(user),
        "mode": "new",
        "template_id": None,
        "clone_from": clone,
    })


@router.get("/templates/{template_id}/edit", response_class=HTMLResponse)
async def template_editor_edit(
    request: Request,
    template_id: str,
    user: TokenPayload = Depends(require_web_admin),
):
    return templates.TemplateResponse("template_editor.html", {
        "request": request,
        "user": _user_ctx(user),
        "mode": "edit",
        "template_id": template_id,
    })
