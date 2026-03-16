from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WiringRule(Base):
    __tablename__ = "wiring_rules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    max_length: Mapped[float] = mapped_column(Float, default=90.0)
    min_spacing: Mapped[float] = mapped_column(Float, default=0.3)
    min_bend_radius: Mapped[float] = mapped_column(Float, default=0.05)
    enabled: Mapped[bool] = mapped_column(default=True)
    description: Mapped[str] = mapped_column(String(255), default="")


class WiringVersion(Base):
    __tablename__ = "wiring_versions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    version_no: Mapped[int] = mapped_column(index=True)
    content_json: Mapped[dict] = mapped_column(JSON)
    note: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="versions")
