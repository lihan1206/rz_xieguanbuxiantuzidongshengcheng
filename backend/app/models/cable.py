from sqlalchemy import Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CableType(Base):
    __tablename__ = "cable_types"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    max_length: Mapped[float] = mapped_column(Float, default=100.0)
    impedance: Mapped[str] = mapped_column(String(32), default="100ohm")
    shielded: Mapped[bool] = mapped_column(default=False)

    cables: Mapped[list["Cable"]] = relationship(back_populates="cable_type")


class Cable(Base):
    __tablename__ = "cables"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    cable_type_id: Mapped[int] = mapped_column(ForeignKey("cable_types.id"), index=True)
    start_device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    end_device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    length: Mapped[float] = mapped_column(Float, default=0)
    path_json: Mapped[list[list[int]]] = mapped_column(JSON)

    project: Mapped["Project"] = relationship(back_populates="cables")
    cable_type: Mapped["CableType"] = relationship(back_populates="cables")
    start_device: Mapped["Device"] = relationship(foreign_keys=[start_device_id])
    end_device: Mapped["Device"] = relationship(foreign_keys=[end_device_id])
