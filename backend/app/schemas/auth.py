from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=64)
    role: str = Field(default="工程师", max_length=16)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(ORMBase):
    id: int
    username: str
    role: str
    created_at: datetime
