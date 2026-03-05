import jwt
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.security import COOKIE_NAME, decode_token
from app.models.user import TokenPayload
from app.services.template_service import load_all_templates

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
async def dashboard(request: Request):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    soc_templates = load_all_templates()

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
async def templates_list(request: Request):
    user = _get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    soc_templates = load_all_templates()
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


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response
