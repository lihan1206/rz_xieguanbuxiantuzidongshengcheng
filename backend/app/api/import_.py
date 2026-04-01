from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Project, User
from app.schemas.common import MessageResponse
from app.schemas.import_ import (
    ImportPreviewResponse,
    ImportResultResponse,
    ImportedDeviceInfo,
    ImportedConnectionInfo
)
from app.services.import_service import (
    parse_dxf_file,
    parse_vsdx_file,
    parse_json_file,
    import_devices_to_project,
    import_cables_to_project
)

router = APIRouter(tags=["导入"])


def _ensure_project_access(db: Session, project_id: int, current_user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    if current_user.role != "管理员" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限操作该项目")
    return project


@router.post("/projects/{project_id}/import/preview", response_model=ImportPreviewResponse)
async def preview_import(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImportPreviewResponse:
    """
    预览导入文件内容，不实际保存到数据库
    """
    _ensure_project_access(db, project_id, current_user)
    
    content = await file.read()
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.dxf'):
            result = parse_dxf_file(content)
        elif filename.endswith('.vsdx'):
            result = parse_vsdx_file(content)
        elif filename.endswith('.json'):
            result = parse_json_file(content)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的文件格式。支持格式：DXF, VSDX, JSON"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # 转换为响应格式
    devices = [
        ImportedDeviceInfo(
            name=d.get("name", "未命名设备"),
            x=d.get("x", 0),
            y=d.get("y", 0),
            device_type=d.get("device_type", "网络设备")
        )
        for d in result.get("devices", [])
    ]
    
    connections = [
        ImportedConnectionInfo(
            start_device_id=c.get("start_device_id"),
            end_device_id=c.get("end_device_id")
        )
        for c in result.get("connections", [])
    ]
    
    return ImportPreviewResponse(
        filename=file.filename,
        format=result.get("metadata", {}).get("format", "未知"),
        device_count=len(devices),
        connection_count=len(connections),
        devices=devices,
        connections=connections,
        metadata=result.get("metadata", {})
    )


@router.post("/projects/{project_id}/import", response_model=ImportResultResponse)
async def execute_import(
    project_id: int,
    file: UploadFile = File(...),
    import_devices: bool = Query(default=True, description="是否导入设备"),
    import_connections: bool = Query(default=True, description="是否导入连接"),
    clear_existing: bool = Query(default=False, description="是否清除现有设备和线缆"),
    default_device_type_id: int | None = Query(default=None, description="默认设备类型ID"),
    default_cable_type_id: int | None = Query(default=None, description="默认线缆类型ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImportResultResponse:
    """
    执行导入操作，将文件内容保存到项目中
    """
    _ensure_project_access(db, project_id, current_user)
    
    content = await file.read()
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.dxf'):
            result = parse_dxf_file(content)
        elif filename.endswith('.vsdx'):
            result = parse_vsdx_file(content)
        elif filename.endswith('.json'):
            result = parse_json_file(content)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的文件格式。支持格式：DXF, VSDX, JSON"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    imported_devices = []
    imported_cables = []
    
    try:
        # 清除现有数据（如果需要）
        if clear_existing:
            from app.models import Cable, Device
            db.query(Cable).filter(Cable.project_id == project_id).delete()
            db.query(Device).filter(Device.project_id == project_id).delete()
            db.flush()
        
        # 导入设备
        if import_devices and result.get("devices"):
            imported_devices = import_devices_to_project(
                db,
                project_id,
                result["devices"],
                default_device_type_id
            )
        
        # 导入连接（线缆）
        if import_connections and result.get("connections"):
            imported_cables = import_cables_to_project(
                db,
                project_id,
                result["connections"],
                default_cable_type_id
            )
        
        db.commit()
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return ImportResultResponse(
        success=True,
        message=f"导入成功：{len(imported_devices)} 个设备，{len(imported_cables)} 个连接",
        imported_device_count=len(imported_devices),
        imported_connection_count=len(imported_cables),
        filename=file.filename
    )