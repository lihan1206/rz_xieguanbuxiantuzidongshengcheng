from typing import Optional
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
    z: int = Field(default=0, ge=0, le=100, description="Z坐标，用于3D布线")


class DeviceUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    device_type_id: int
    x: int = Field(ge=0, le=100)
    y: int = Field(ge=0, le=100)
    z: int = Field(default=0, ge=0, le=100, description="Z坐标，用于3D布线")


class DeviceResponse(ORMBase):
    id: int
    name: str
    project_id: int
    device_type_id: int
    x: int
    y: int
    z: int


# 批量操作相关Schema
class DeviceBatchCreate(BaseModel):
    """批量创建设备请求"""
    devices: list[DeviceCreate] = Field(description="设备列表", min_length=1)


class DeviceBatchUpdateItem(BaseModel):
    """批量更新设备条目"""
    device_id: int = Field(description="设备ID")
    name: Optional[str] = Field(None, min_length=2, max_length=64, description="设备名称")
    device_type_id: Optional[int] = Field(None, description="设备类型ID")
    x: Optional[int] = Field(None, ge=0, le=100, description="X坐标")
    y: Optional[int] = Field(None, ge=0, le=100, description="Y坐标")
    z: Optional[int] = Field(None, ge=0, le=100, description="Z坐标，用于3D布线")


class DeviceBatchUpdate(BaseModel):
    """批量更新设备请求"""
    updates: list[DeviceBatchUpdateItem] = Field(description="更新条目列表", min_length=1)


class DeviceBatchDelete(BaseModel):
    """批量删除设备请求"""
    device_ids: list[int] = Field(description="设备ID列表", min_length=1)


class BatchOperationResult(BaseModel):
    """批量操作结果"""
    success_count: int = Field(description="成功数量")
    error_count: int = Field(description="失败数量")
    errors: list[str] = Field(default_factory=list, description="错误信息列表")
    message: str = Field(description="结果消息")
