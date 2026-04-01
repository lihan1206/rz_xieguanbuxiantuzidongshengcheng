from pydantic import BaseModel, Field


class DeviceBatchItem(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    device_type_id: int
    x: int = Field(ge=0, le=100)
    y: int = Field(ge=0, le=100)


class DeviceBatchCreate(BaseModel):
    devices: list[DeviceBatchItem] = Field(min_length=1, max_length=100)


class DeviceBatchUpdateItem(BaseModel):
    id: int
    name: str = Field(min_length=2, max_length=64)
    device_type_id: int
    x: int = Field(ge=0, le=100)
    y: int = Field(ge=0, le=100)


class DeviceBatchUpdate(BaseModel):
    devices: list[DeviceBatchUpdateItem] = Field(min_length=1, max_length=100)


class DeviceBatchDelete(BaseModel):
    device_ids: list[int] = Field(min_length=1, max_length=100)


class BatchOperationResult(BaseModel):
    success_count: int
    failed_count: int
    errors: list[str] = Field(default_factory=list)


class DeviceBatchCreateResult(BatchOperationResult):
    created_devices: list[int] = Field(default_factory=list)


class DeviceBatchUpdateResult(BatchOperationResult):
    updated_devices: list[int] = Field(default_factory=list)


class DeviceBatchDeleteResult(BatchOperationResult):
    deleted_devices: list[int] = Field(default_factory=list)


class ImportPreviewDevice(BaseModel):
    name: str
    x: int
    y: int
    device_type_name: str | None
    attributes: dict


class ImportPreviewResponse(BaseModel):
    success: bool
    devices: list[ImportPreviewDevice]
    errors: list[str]
    warnings: list[str]
    total_shapes: int
    imported_count: int


class ImportConfirmRequest(BaseModel):
    devices: list[DeviceBatchItem]
    default_device_type_id: int | None = None
