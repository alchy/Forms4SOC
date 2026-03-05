from fastapi import APIRouter, HTTPException, Response, status, Depends

from app.auth.auth_provider import AuthProvider
from app.auth.simple_auth import SimpleAuthProvider
from app.auth.oauth_auth import OAuthProvider
from app.auth.ldap_auth import LDAPProvider
from app.config import settings
from app.core.security import COOKIE_NAME, create_access_token, require_auth
from app.models.user import LoginRequest, Token, User

router = APIRouter(prefix="/auth", tags=["Autentizace"])

_PROVIDERS: dict[str, type[AuthProvider]] = {
    "simple": SimpleAuthProvider,
    "oauth": OAuthProvider,
    "ldap": LDAPProvider,
}


def get_auth_provider() -> AuthProvider:
    """Vrátí instanci aktivního auth providera dle konfigurace AUTH_PROVIDER."""
    provider_class = _PROVIDERS.get(settings.auth_provider, SimpleAuthProvider)
    return provider_class()


@router.post(
    "/login",
    response_model=Token,
    summary="Přihlášení uživatele",
    description="Ověří přihlašovací údaje a vrátí JWT token. Token je zároveň nastaven jako httpOnly cookie.",
)
async def login(credentials: LoginRequest, response: Response) -> Token:
    provider = get_auth_provider()
    user = await provider.authenticate(credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nesprávné přihlašovací údaje",
        )

    token = create_access_token({"sub": user.username, "role": user.role})

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
    )

    return Token(access_token=token)


@router.post(
    "/logout",
    summary="Odhlášení uživatele",
    description="Smaže JWT cookie a odhlásí uživatele.",
)
async def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE_NAME)
    return {"detail": "Odhlášení proběhlo úspěšně"}


@router.get(
    "/me",
    response_model=User,
    summary="Informace o přihlášeném uživateli",
)
async def get_me(current_user: User = Depends(require_auth)) -> User:
    return current_user
