from typing import Optional

from app.auth.auth_provider import AuthProvider
from app.config import settings
from app.core.security import hash_password, verify_password
from app.models.user import User


def _build_users() -> dict[str, dict]:
    """
    Sestaví in-memory slovník uživatelů z konfigurace.
    V produkci nahradit dotazem do databáze.
    """
    return {
        settings.admin_username: {
            "username": settings.admin_username,
            "hashed_password": hash_password(settings.admin_password),
            "role": "admin",
            "is_active": True,
        }
    }


# Inicializace při načtení modulu
_USERS: dict[str, dict] = _build_users()


class SimpleAuthProvider(AuthProvider):
    """
    Jednoduchý autentizační provider – username/password.

    Uživatelé jsou definováni v .env (ADMIN_USERNAME, ADMIN_PASSWORD).
    Vhodné pro vývoj a první nasazení.

    Nahrazení: implementuj OAuthProvider nebo LDAPProvider se stejným rozhraním
    a nastav AUTH_PROVIDER v .env.
    """

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        user_data = _USERS.get(username)
        if not user_data:
            return None
        if not user_data.get("is_active"):
            return None
        if not verify_password(password, user_data["hashed_password"]):
            return None
        return User(username=user_data["username"], role=user_data["role"])

    async def get_user(self, username: str) -> Optional[User]:
        user_data = _USERS.get(username)
        if not user_data or not user_data.get("is_active"):
            return None
        return User(username=user_data["username"], role=user_data["role"])
