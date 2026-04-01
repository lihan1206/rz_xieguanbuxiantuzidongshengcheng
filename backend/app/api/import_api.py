import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Device, DeviceType, Project, User
from app.schemas.common import MessageResponse
from app.schemas.device import DeviceResponse
from app.schemas.import_schemas import (
    DeviceBatchCreate,
    DeviceBatchCreateResult,
    DeviceBatchDelete,
    DeviceBatchDeleteResult,
    DeviceBatchUpdate,
    DeviceBatchUpdateResult,
    ImportConfirmRequest,
    ImportPreviewDevice,
    ImportPreviewResponse,
)
from app.services.import_service import ImportService

router = APIRouter(tags=["导入与批量操作"])
logger = logging.getLogger(__name__)
import_service = ImportService()


def _ensure_project_access(db: Session, project_id: int, current_user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    if current_user.role != "管理员" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限操作该项目")
    return project


@router.post("/projects/{project_id}/devices/batch-create", response_model=DeviceBatchCreateResult)
def batch_create_devices(
    project_id: int,
    payload: DeviceBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceBatchCreateResult:
    _ensure_project_access(db, project_id, current_user)

    created_ids: list[int] = []
    errors: list[str] = []

    device_type_ids = {d.device_type_id for d in payload.devices}
    existing_types = (
        db.query(DeviceType).filter(DeviceType.id.in_(device_type_ids)).all()
    )
    type_map = {t.id: t for t in existing_types}

    for idx, item in enumerate(payload.devices):
        try:
            if item.device_type_id not in type_map:
                errors.append(f"第{idx + 1}个设备: 设备类型ID {item.device_type_id} 不存在")
                continue

            device = Device(
                project_id=project_id,
                name=item.name,
                device_type_id=item.device_type_id,
                x=item.x,
                y=item.y,
            )
            db.add(device)
            db.flush()
            created_ids.append(device.id)

        except Exception as e:
            errors.append(f"第{idx + 1}个设备创建失败: {str(e)}")

    db.commit()

    return DeviceBatchCreateResult(
        success_count=len(created_ids),
        failed_count=len(errors),
        errors=errors,
        created_devices=created_ids,
    )


@router.put("/projects/{project_id}/devices/batch-update", response_model=DeviceBatchUpdateResult)
def batch_update_devices(
    project_id: int,
    payload: DeviceBatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceBatchUpdateResult:
    _ensure_project_access(db, project_id, current_user)

    updated_ids: list[int] = []
    errors: list[str] = []

    device_ids = [d.id for d in payload.devices]
    existing_devices = (
        db.query(Device)
        .filter(Device.id.in_(device_ids), Device.project_id == project_id)
        .all()
    )
    device_map = {d.id: d for d in existing_devices}

    device_type_ids = {d.device_type_id for d in payload.devices}
    existing_types = (
        db.query(DeviceType).filter(DeviceType.id.in_(device_type_ids)).all()
    )
    type_map = {t.id: t for t in existing_types}

    for idx, item in enumerate(payload.devices):
        try:
            if item.id not in device_map:
                errors.append(f"第{idx + 1}个设备: 设备ID {item.id} 不存在或不属于该项目")
                continue

            if item.device_type_id not in type_map:
                errors.append(f"第{idx + 1}个设备: 设备类型ID {item.device_type_id} 不存在")
                continue

            device = device_map[item.id]
            device.name = item.name
            device.device_type_id = item.device_type_id
            device.x = item.x
            device.y = item.y
            updated_ids.append(device.id)

        except Exception as e:
            errors.append(f"第{idx + 1}个设备更新失败: {str(e)}")

    db.commit()

    return DeviceBatchUpdateResult(
        success_count=len(updated_ids),
        failed_count=len(errors),
        errors=errors,
        updated_devices=updated_ids,
    )


@router.delete("/projects/{project_id}/devices/batch-delete", response_model=DeviceBatchDeleteResult)
def batch_delete_devices(
    project_id: int,
    payload: DeviceBatchDelete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceBatchDeleteResult:
    _ensure_project_access(db, project_id, current_user)

    deleted_ids: list[int] = []
    errors: list[str] = []

    existing_devices = (
        db.query(Device)
        .filter(Device.id.in_(payload.device_ids), Device.project_id == project_id)
        .all()
    )
    device_map = {d.id: d for d in existing_devices}

    for device_id in payload.device_ids:
        try:
            if device_id not in device_map:
                errors.append(f"设备ID {device_id} 不存在或不属于该项目")
                continue

            db.delete(device_map[device_id])
            deleted_ids.append(device_id)

        except Exception as e:
            errors.append(f"设备ID {device_id} 删除失败: {str(e)}")

    db.commit()

    return DeviceBatchDeleteResult(
        success_count=len(deleted_ids),
        failed_count=len(errors),
        errors=errors,
        deleted_devices=deleted_ids,
    )


@router.get("/import/supported-formats")
def get_supported_formats(
    current_user: User = Depends(get_current_user),
) -> dict:
    _ = current_user
    return {
        "formats": import_service.get_supported_formats(),
        "max_file_size_mb": 50,
    }


@router.post("/projects/{project_id}/import/preview", response_model=ImportPreviewResponse)
async def preview_import(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImportPreviewResponse:
    _ensure_project_access(db, project_id, current_user)

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        is_valid, msg = import_service.validate_file(tmp_path)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

        result = import_service.parse_file(tmp_path)

        devices = [
            ImportPreviewDevice(
                name=d.name,
                x=d.x,
                y=d.y,
                device_type_name=d.device_type_name,
                attributes=d.attributes,
            )
            for d in result.devices
        ]

        return ImportPreviewResponse(
            success=result.success,
            devices=devices,
            errors=result.errors,
            warnings=result.warnings,
            total_shapes=result.total_shapes,
            imported_count=result.imported_count,
        )

    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/projects/{project_id}/import/confirm", response_model=DeviceBatchCreateResult)
def confirm_import(
    project_id: int,
    payload: ImportConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceBatchCreateResult:
    _ensure_project_access(db, project_id, current_user)

    created_ids: list[int] = []
    errors: list[str] = []

    device_type_ids = {d.device_type_id for d in payload.devices}
    if payload.default_device_type_id:
        device_type_ids.add(payload.default_device_type_id)

    existing_types = (
        db.query(DeviceType).filter(DeviceType.id.in_(device_type_ids)).all()
    )
    type_map = {t.id: t for t in existing_types}

    default_type_id = payload.default_device_type_id
    if default_type_id and default_type_id not in type_map:
        default_type_id = None

    for idx, item in enumerate(payload.devices):
        try:
            type_id = item.device_type_id
            if type_id not in type_map:
                if default_type_id:
                    type_id = default_type_id
                else:
                    errors.append(f"第{idx + 1}个设备: 设备类型ID {item.device_type_id} 不存在")
                    continue

            device = Device(
                project_id=project_id,
                name=item.name,
                device_type_id=type_id,
                x=item.x,
                y=item.y,
            )
            db.add(device)
            db.flush()
            created_ids.append(device.id)

        except Exception as e:
            errors.append(f"第{idx + 1}个设备创建失败: {str(e)}")

    db.commit()

    return DeviceBatchCreateResult(
        success_count=len(created_ids),
        failed_count=len(errors),
        errors=errors,
        created_devices=created_ids,
    )
