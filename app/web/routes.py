import aiosqlite
import jwt
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.database import get_db
from app.core.security import COOKIE_NAME, decode_token
from app.models.user import TokenPayload
from app.services.settings_service import get_all_settings
from app.storage import get_storage_backend

router = APIRouter(tags=["Web"])
templates = Jinja2Templates(directory="app/templates")


def _get_user_from_cookie(request: Request) -> TokenPayload | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        return decode_token(token)
    except jwt.PyJWTError:
        return None


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = _get_user_from_cookie(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    storage = await get_storage_backend(db)
    soc_templates = await storage.list_templates()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": {"username": user.sub, "role": user.role},
        "templates": soc_templates,
    })


@router.get("/cases", response_class=HTMLResponse)
async def cases_list(request: Request):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("cases.html", {
        "request": request,
        "user": {"username": user.sub, "role": user.role},
    })


@router.get("/templates", response_class=HTMLResponse)
async def templates_list(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    storage = await get_storage_backend(db)
    soc_templates = await storage.list_templates()
    return templates.TemplateResponse("templates_list.html", {
        "request": request,
        "user": {"username": user.sub, "role": user.role},
        "templates": soc_templates,
    })


@router.get("/cases/{case_id}", response_class=HTMLResponse)
async def case_detail(request: Request, case_id: str):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse("case_detail.html", {
        "request": request,
        "user": {"username": user.sub, "role": user.role},
        "case_id": case_id,
    })


@router.get("/cases/{case_id}/print", response_class=HTMLResponse)
async def case_print(request: Request, case_id: str):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse("print_case.html", {
        "request": request,
        "case_id": case_id,
    })


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: aiosqlite.Connection = Depends(get_db)):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.role != "admin":
        return RedirectResponse(url="/dashboard", status_code=302)

    current_settings = await get_all_settings(db)
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": {"username": user.sub, "role": user.role},
        "settings": current_settings,
    })


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if user.role != "admin":
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse("admin_users.html", {
        "request": request,
        "user": {"username": user.sub, "role": user.role},
    })


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response
