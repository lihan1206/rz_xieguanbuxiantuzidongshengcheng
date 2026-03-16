from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    location: str = Field(default="", max_length=128)
    purpose: str = Field(default="", max_length=255)


class ProjectUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    location: str = Field(default="", max_length=128)
    purpose: str = Field(default="", max_length=255)
    status: str = Field(default="进行中", max_length=32)


class ProjectResponse(ORMBase):
    id: int
    name: str
    location: str
    purpose: str
    status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
