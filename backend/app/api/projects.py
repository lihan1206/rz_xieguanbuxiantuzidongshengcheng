from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Project, User
from app.schemas.common import MessageResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["项目"])


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    status_value: str | None = Query(default=None, alias="status"),
    keyword: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Project]:
    query = db.query(Project)
    if current_user.role != "管理员":
        query = query.filter(Project.owner_id == current_user.id)
    if status_value:
        query = query.filter(Project.status == status_value)
    if keyword:
        query = query.filter(Project.name.contains(keyword))
    return query.order_by(Project.updated_at.desc()).all()


@router.post("", response_model=ProjectResponse)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = Project(
        name=payload.name,
        location=payload.location,
        purpose=payload.purpose,
        owner_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def _get_project(db: Session, project_id: int, current_user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    if current_user.role != "管理员" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问该项目")
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    return _get_project(db, project_id, current_user)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = _get_project(db, project_id, current_user)
    project.name = payload.name
    project.location = payload.location
    project.purpose = payload.purpose
    project.status = payload.status
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", response_model=MessageResponse)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    project = _get_project(db, project_id, current_user)
    db.delete(project)
    db.commit()
    return MessageResponse(message="项目删除成功")
