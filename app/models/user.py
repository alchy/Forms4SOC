from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    username: str
    role: str = "analyst"
    is_active: bool = True


class TokenPayload(BaseModel):
    sub: str       # username
    role: str = "analyst"
    exp: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str
