from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Cookie, Depends, HTTPException, status

from app.config import settings
from app.models.user import TokenPayload, User

COOKIE_NAME = "forms4soc_token"


# ---------------------------------------------------------------------------
# Hesla
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> TokenPayload:
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    return TokenPayload(**payload)


# ---------------------------------------------------------------------------
# FastAPI dependency – ochrana API endpointů
# ---------------------------------------------------------------------------

async def require_auth(
    forms4soc_token: Optional[str] = Cookie(default=None),
) -> User:
    """
    Dependency pro ochranu API endpointů.
    Použití: current_user: User = Depends(require_auth)
    """
    if not forms4soc_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nepřihlášen – chybí autentizační token",
        )
    try:
        payload = decode_token(forms4soc_token)
        return User(username=payload.sub, role=payload.role)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Platnost tokenu vypršela – přihlaste se znovu",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neplatný autentizační token",
        )
