from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class ConnectionRequest(BaseModel):
    start_device_id: int
    end_device_id: int
    cable_type_id: int | None = None


class Obstacle(BaseModel):
    x1: int = Field(ge=0, le=100)
    y1: int = Field(ge=0, le=100)
    x2: int = Field(ge=0, le=100)
    y2: int = Field(ge=0, le=100)


class AutoRouteRequest(BaseModel):
    connections: list[ConnectionRequest] = Field(default_factory=list)
    obstacles: list[Obstacle] = Field(default_factory=list)


class CableTypeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    max_length: float = Field(gt=0)
    impedance: str = Field(default="100ohm", max_length=32)
    shielded: bool = False


class CableTypeResponse(ORMBase):
    id: int
    name: str
    max_length: float
    impedance: str
    shielded: bool


class CableResponse(ORMBase):
    id: int
    project_id: int
    cable_type_id: int
    start_device_id: int
    end_device_id: int
    length: float
    path_json: list[list[int]]


class ValidationIssue(BaseModel):
    level: str
    message: str


class AutoRouteResponse(BaseModel):
    cable_count: int
    issues: list[ValidationIssue]


class WiringVersionResponse(ORMBase):
    id: int
    project_id: int
    version_no: int
    note: str
    created_at: datetime
    content_json: dict
