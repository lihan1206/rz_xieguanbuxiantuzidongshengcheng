from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Cable, CableType, Device, Project, User, WiringRule, WiringVersion
from app.schemas.common import MessageResponse
from app.schemas.wiring import (
    AutoRouteRequest,
    AutoRouteResponse,
    CableResponse,
    CableTypeCreate,
    CableTypeResponse,
    ValidationIssue,
    WiringVersionResponse,
)
from app.services.export_service import (
    build_project_payload,
    export_dxf,
    export_json,
    export_pdf,
    export_svg,
)
from app.services.wiring_engine import shortest_path

router = APIRouter(tags=["布线"])


def _ensure_project_access(db: Session, project_id: int, current_user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    if current_user.role != "管理员" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问该项目")
    return project


@router.get("/cable-types", response_model=list[CableTypeResponse])
def list_cable_types(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[CableType]:
    _ = current_user
    return db.query(CableType).order_by(CableType.id.asc()).all()


@router.post("/cable-types", response_model=CableTypeResponse)
def create_cable_type(
    payload: CableTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CableType:
    if current_user.role != "管理员":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可新增线缆类型")
    exists = db.query(CableType).filter(CableType.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="线缆类型名称已存在")
    model = CableType(**payload.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.get("/projects/{project_id}/cables", response_model=list[CableResponse])
def list_cables(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Cable]:
    _ensure_project_access(db, project_id, current_user)
    return db.query(Cable).filter(Cable.project_id == project_id).order_by(Cable.id.asc()).all()


@router.post("/projects/{project_id}/auto-route", response_model=AutoRouteResponse)
def auto_route(
    project_id: int,
    payload: AutoRouteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AutoRouteResponse:
    _ensure_project_access(db, project_id, current_user)

    devices = db.query(Device).filter(Device.project_id == project_id).order_by(Device.id.asc()).all()
    if len(devices) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="至少需要两个设备才能自动布线")

    device_map = {device.id: device for device in devices}
    cable_types = db.query(CableType).order_by(CableType.id.asc()).all()
    if not cable_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先配置线缆类型")
    default_cable_type = cable_types[0]

    for existing in db.query(Cable).filter(Cable.project_id == project_id).all():
        db.delete(existing)
    db.flush()

    connections = payload.connections
    if not connections:
        connections = [
            {"start_device_id": devices[i].id, "end_device_id": devices[i + 1].id, "cable_type_id": default_cable_type.id}
            for i in range(len(devices) - 1)
        ]

    issues: list[ValidationIssue] = []

    for conn in connections:
        start_id = conn.start_device_id if hasattr(conn, "start_device_id") else conn["start_device_id"]
        end_id = conn.end_device_id if hasattr(conn, "end_device_id") else conn["end_device_id"]
        type_id = conn.cable_type_id if hasattr(conn, "cable_type_id") else conn.get("cable_type_id")

        start = device_map.get(start_id)
        end = device_map.get(end_id)
        if not start or not end:
            issues.append(ValidationIssue(level="error", message=f"设备连接无效：{start_id} -> {end_id}"))
            continue

        cable_type = db.query(CableType).filter(CableType.id == (type_id or default_cable_type.id)).first()
        if not cable_type:
            cable_type = default_cable_type

        try:
            path = shortest_path(
                start=(start.x, start.y),
                end=(end.x, end.y),
                obstacles=[item.model_dump() for item in payload.obstacles],
            )
        except ValueError as exc:
            issues.append(ValidationIssue(level="error", message=str(exc)))
            continue

        length = float(len(path) - 1)
        cable = Cable(
            project_id=project_id,
            cable_type_id=cable_type.id,
            start_device_id=start.id,
            end_device_id=end.id,
            length=length,
            path_json=[[x, y] for x, y in path],
        )
        db.add(cable)

        if length > cable_type.max_length:
            issues.append(
                ValidationIssue(
                    level="warning",
                    message=f"线缆 {cable_type.name} 的长度 {length:.1f}m 超过类型上限 {cable_type.max_length:.1f}m",
                )
            )

    rules = db.query(WiringRule).filter(WiringRule.enabled.is_(True)).all()
    if rules:
        strict_length = min(rule.max_length for rule in rules)
        for cable in db.query(Cable).filter(Cable.project_id == project_id).all():
            if cable.length > strict_length:
                issues.append(
                    ValidationIssue(
                        level="warning",
                        message=f"线缆#{cable.id} 长度 {cable.length:.1f}m 超过规则上限 {strict_length:.1f}m",
                    )
                )

    db.flush()

    last_version = (
        db.query(WiringVersion)
        .filter(WiringVersion.project_id == project_id)
        .order_by(WiringVersion.version_no.desc())
        .first()
    )
    next_version_no = 1 if not last_version else last_version.version_no + 1

    snapshot = build_project_payload(db, project_id)
    db.add(
        WiringVersion(
            project_id=project_id,
            version_no=next_version_no,
            note="自动布线生成快照",
            content_json=snapshot,
        )
    )
    db.commit()

    cable_count = db.query(Cable).filter(Cable.project_id == project_id).count()
    return AutoRouteResponse(cable_count=cable_count, issues=issues)


@router.get("/projects/{project_id}/validate", response_model=list[ValidationIssue])
def validate_wiring(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ValidationIssue]:
    _ensure_project_access(db, project_id, current_user)

    issues: list[ValidationIssue] = []
    rules = db.query(WiringRule).filter(WiringRule.enabled.is_(True)).all()
    if not rules:
        return issues

    strict_length = min(rule.max_length for rule in rules)
    cables = db.query(Cable).filter(Cable.project_id == project_id).all()
    for cable in cables:
        if cable.length > strict_length:
            issues.append(
                ValidationIssue(
                    level="warning",
                    message=f"线缆#{cable.id} 长度 {cable.length:.1f}m 超过规则上限 {strict_length:.1f}m",
                )
            )

    if not cables:
        issues.append(ValidationIssue(level="info", message="当前项目尚未生成线缆"))

    return issues


@router.get("/projects/{project_id}/versions", response_model=list[WiringVersionResponse])
def list_versions(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WiringVersion]:
    _ensure_project_access(db, project_id, current_user)
    return (
        db.query(WiringVersion)
        .filter(WiringVersion.project_id == project_id)
        .order_by(WiringVersion.version_no.desc())
        .all()
    )


@router.post("/projects/{project_id}/versions/save", response_model=MessageResponse)
def save_version(
    project_id: int,
    note: str = Query(default="手动保存快照"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    _ensure_project_access(db, project_id, current_user)
    last_version = (
        db.query(WiringVersion)
        .filter(WiringVersion.project_id == project_id)
        .order_by(WiringVersion.version_no.desc())
        .first()
    )
    next_version_no = 1 if not last_version else last_version.version_no + 1
    payload = build_project_payload(db, project_id)
    db.add(
        WiringVersion(
            project_id=project_id,
            version_no=next_version_no,
            note=note,
            content_json=payload,
        )
    )
    db.commit()
    return MessageResponse(message="版本保存成功")


@router.get("/projects/{project_id}/export/{fmt}")
def export_project(
    project_id: int,
    fmt: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    _ensure_project_access(db, project_id, current_user)

    payload = build_project_payload(db, project_id)
    if fmt == "json":
        data = export_json(payload)
        media_type = "application/json"
        filename = f"project-{project_id}.json"
    elif fmt == "svg":
        data = export_svg(payload)
        media_type = "image/svg+xml"
        filename = f"project-{project_id}.svg"
    elif fmt == "pdf":
        data = export_pdf(payload)
        media_type = "application/pdf"
        filename = f"project-{project_id}.pdf"
    elif fmt == "dxf":
        data = export_dxf(payload)
        media_type = "application/dxf"
        filename = f"project-{project_id}.dxf"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的导出格式")

    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
