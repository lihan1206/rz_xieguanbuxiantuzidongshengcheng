from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class DeviceTypeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    category: str = Field(default="网络设备", max_length=64)
    port_count: int = Field(default=8, ge=1, le=256)
    voltage: str = Field(default="220V", max_length=32)
    size_desc: str = Field(default="标准", max_length=64)
    icon_url: str = Field(default="", max_length=255)


class DeviceTypeResponse(ORMBase):
    id: int
    name: str
    category: str
    port_count: int
    voltage: str
    size_desc: str
    icon_url: str


class DeviceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    device_type_id: int
    x: int = Field(ge=0, le=100)
    y: int = Field(ge=0, le=100)


class DeviceUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    device_type_id: int
    x: int = Field(ge=0, le=100)
    y: int = Field(ge=0, le=100)


class DeviceResponse(ORMBase):
    id: int
    name: str
    project_id: int
    device_type_id: int
    x: int
    y: int
