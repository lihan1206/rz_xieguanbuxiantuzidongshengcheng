from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Device, DeviceType, Project, User
from app.schemas.common import MessageResponse
from app.schemas.device import (
    DeviceCreate,
    DeviceResponse,
    DeviceTypeCreate,
    DeviceTypeResponse,
    DeviceUpdate,
    DeviceBatchCreate,
    DeviceBatchUpdate,
    DeviceBatchDelete,
    BatchOperationResult,
)

router = APIRouter(tags=["设备"])


def _ensure_project_access(db: Session, project_id: int, current_user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    if current_user.role != "管理员" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限操作该项目")
    return project


@router.get("/device-types", response_model=list[DeviceTypeResponse])
def list_device_types(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[DeviceType]:
    _ = current_user
    return db.query(DeviceType).order_by(DeviceType.id.asc()).all()


@router.post("/device-types", response_model=DeviceTypeResponse)
def create_device_type(
    payload: DeviceTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceType:
    if current_user.role != "管理员":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可新增设备类型")
    existing = db.query(DeviceType).filter(DeviceType.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="设备类型名称已存在")
    model = DeviceType(**payload.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.delete("/device-types/{type_id}", response_model=MessageResponse)
def delete_device_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    if current_user.role != "管理员":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可删除设备类型")
    device_type = db.query(DeviceType).filter(DeviceType.id == type_id).first()
    if not device_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备类型不存在")
    db.delete(device_type)
    db.commit()
    return MessageResponse(message="设备类型删除成功")


@router.get("/projects/{project_id}/devices", response_model=list[DeviceResponse])
def list_devices(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Device]:
    _ensure_project_access(db, project_id, current_user)
    return db.query(Device).filter(Device.project_id == project_id).order_by(Device.id.asc()).all()


@router.post("/projects/{project_id}/devices", response_model=DeviceResponse)
def create_device(
    project_id: int,
    payload: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Device:
    _ensure_project_access(db, project_id, current_user)
    device_type = db.query(DeviceType).filter(DeviceType.id == payload.device_type_id).first()
    if not device_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备类型不存在")
    device = Device(project_id=project_id, **payload.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.put("/projects/{project_id}/devices/{device_id}", response_model=DeviceResponse)
def update_device(
    project_id: int,
    device_id: int,
    payload: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Device:
    _ensure_project_access(db, project_id, current_user)
    device = db.query(Device).filter(Device.id == device_id, Device.project_id == project_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")
    for key, value in payload.model_dump().items():
        setattr(device, key, value)
    db.commit()
    db.refresh(device)
    return device


@router.delete("/projects/{project_id}/devices/{device_id}", response_model=MessageResponse)
def delete_device(
    project_id: int,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    _ensure_project_access(db, project_id, current_user)
    device = db.query(Device).filter(Device.id == device_id, Device.project_id == project_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")
    db.delete(device)
    db.commit()
    return MessageResponse(message="设备删除成功")


@router.post("/projects/{project_id}/devices/batch", response_model=BatchOperationResult)
def batch_create_devices(
    project_id: int,
    payload: DeviceBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchOperationResult:
    """批量创建设备"""
    _ensure_project_access(db, project_id, current_user)
    
    success_count = 0
    error_count = 0
    errors = []
    created_devices = []
    
    # 验证设备类型是否存在
    device_type_ids = {d.device_type_id for d in payload.devices}
    existing_types = {t.id for t in db.query(DeviceType).filter(DeviceType.id.in_(device_type_ids)).all()}
    
    for i, device_data in enumerate(payload.devices):
        if device_data.device_type_id not in existing_types:
            error_count += 1
            errors.append(f"设备 {i+1} ({device_data.name}): 设备类型不存在")
            continue
        
        try:
            device = Device(project_id=project_id, **device_data.model_dump())
            db.add(device)
            db.flush()
            created_devices.append(device)
            success_count += 1
        except Exception as e:
            error_count += 1
            errors.append(f"设备 {i+1} ({device_data.name}): 创建失败 - {str(e)}")
    
    db.commit()
    
    return BatchOperationResult(
        success_count=success_count,
        error_count=error_count,
        errors=errors,
        message=f"批量创建设备完成，成功: {success_count}, 失败: {error_count}"
    )


@router.put("/projects/{project_id}/devices/batch", response_model=BatchOperationResult)
def batch_update_devices(
    project_id: int,
    payload: DeviceBatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchOperationResult:
    """批量更新设备"""
    _ensure_project_access(db, project_id, current_user)
    
    success_count = 0
    error_count = 0
    errors = []
    
    # 获取需要更新的设备ID列表
    device_ids = [u.device_id for u in payload.updates]
    existing_devices = {
        d.id: d for d in db.query(Device).filter(
            Device.project_id == project_id,
            Device.id.in_(device_ids)
        ).all()
    }
    
    # 验证设备类型（如果有更新）
    device_type_ids = {u.device_type_id for u in payload.updates if u.device_type_id is not None}
    existing_types = {}
    if device_type_ids:
        existing_types = {t.id for t in db.query(DeviceType).filter(DeviceType.id.in_(device_type_ids)).all()}
    
    for update_data in payload.updates:
        device = existing_devices.get(update_data.device_id)
        if not device:
            error_count += 1
            errors.append(f"设备ID {update_data.device_id}: 设备不存在")
            continue
        
        # 验证设备类型
        if update_data.device_type_id is not None and update_data.device_type_id not in existing_types:
            error_count += 1
            errors.append(f"设备ID {update_data.device_id}: 设备类型不存在")
            continue
        
        try:
            # 只更新提供的字段
            update_dict = update_data.model_dump(exclude_unset=True, exclude={"device_id"})
            for key, value in update_dict.items():
                if value is not None:
                    setattr(device, key, value)
            success_count += 1
        except Exception as e:
            error_count += 1
            errors.append(f"设备ID {update_data.device_id}: 更新失败 - {str(e)}")
    
    db.commit()
    
    return BatchOperationResult(
        success_count=success_count,
        error_count=error_count,
        errors=errors,
        message=f"批量更新设备完成，成功: {success_count}, 失败: {error_count}"
    )


@router.delete("/projects/{project_id}/devices/batch", response_model=BatchOperationResult)
def batch_delete_devices(
    project_id: int,
    payload: DeviceBatchDelete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchOperationResult:
    """批量删除设备"""
    _ensure_project_access(db, project_id, current_user)
    
    success_count = 0
    error_count = 0
    errors = []
    
    devices = db.query(Device).filter(
        Device.project_id == project_id,
        Device.id.in_(payload.device_ids)
    ).all()
    
    existing_ids = {d.id for d in devices}
    for device_id in payload.device_ids:
        if device_id not in existing_ids:
            error_count += 1
            errors.append(f"设备ID {device_id}: 设备不存在")
            continue
        
        try:
            device = db.query(Device).get(device_id)
            db.delete(device)
            success_count += 1
        except Exception as e:
            error_count += 1
            errors.append(f"设备ID {device_id}: 删除失败 - {str(e)}")
    
    db.commit()
    
    return BatchOperationResult(
        success_count=success_count,
        error_count=error_count,
        errors=errors,
        message=f"批量删除设备完成，成功: {success_count}, 失败: {error_count}"
    )
