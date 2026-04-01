from typing import Any, Optional
from pydantic import BaseModel, Field


class ImportedDeviceInfo(BaseModel):
    """导入的设备信息"""
    name: str = Field(description="设备名称")
    x: int = Field(description="X坐标")
    y: int = Field(description="Y坐标")
    z: int = Field(default=0, description="Z坐标（3D布线）")
    device_type: str = Field(default="网络设备", description="设备类型名称")


class ImportedConnectionInfo(BaseModel):
    """导入的连接信息"""
    start_device_id: Optional[int] = Field(description="起始设备索引")
    end_device_id: Optional[int] = Field(description="目标设备索引")


class ImportPreviewResponse(BaseModel):
    """导入预览响应"""
    filename: str = Field(description="文件名")
    format: str = Field(description="文件格式")
    device_count: int = Field(description="设备数量")
    connection_count: int = Field(description="连接数量")
    devices: list[ImportedDeviceInfo] = Field(description="设备列表预览")
    connections: list[ImportedConnectionInfo] = Field(description="连接列表预览")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")


class ImportResultResponse(BaseModel):
    """导入结果响应"""
    success: bool = Field(description="是否成功")
    message: str = Field(description="结果消息")
    imported_device_count: int = Field(default=0, description="导入的设备数量")
    imported_connection_count: int = Field(default=0, description="导入的连接数量")
    filename: str = Field(description="导入的文件名")