from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    location: Mapped[str] = mapped_column(String(128), default="")
    purpose: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(32), default="进行中")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    owner: Mapped["User"] = relationship(back_populates="projects")

    devices: Mapped[list["Device"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    cables: Mapped[list["Cable"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    versions: Mapped[list["WiringVersion"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
