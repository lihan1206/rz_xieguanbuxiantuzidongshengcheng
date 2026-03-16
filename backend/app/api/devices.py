from fastapi import APIRouter, Depends, HTTPException, status
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
