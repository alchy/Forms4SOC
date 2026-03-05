from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1 import auth, cases, settings, templates, users
from app.config import settings as app_settings
from app.core.database import init_db
from app.web import routes as web_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    await init_db()
    yield


app = FastAPI(
    title=app_settings.app_name,
    version=app_settings.app_version,
    description="SOC Incident Management Portal – REST API",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Statické soubory (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# API – verze v1
_API_V1 = "/api/v1"
app.include_router(auth.router, prefix=_API_V1)
app.include_router(templates.router, prefix=_API_V1)
app.include_router(cases.router, prefix=_API_V1)
app.include_router(settings.router, prefix=_API_V1)
app.include_router(users.router, prefix=_API_V1)

# Web routes – Jinja2 server-side rendering
app.include_router(web_routes.router)
