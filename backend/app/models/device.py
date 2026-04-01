from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DeviceType(Base):
    __tablename__ = "device_types"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(64), default="网络设备")
    port_count: Mapped[int] = mapped_column(default=8)
    voltage: Mapped[str] = mapped_column(String(32), default="220V")
    size_desc: Mapped[str] = mapped_column(String(64), default="标准")
    icon_url: Mapped[str] = mapped_column(String(255), default="")

    devices: Mapped[list["Device"]] = relationship(back_populates="device_type")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    x: Mapped[int] = mapped_column(default=0)
    y: Mapped[int] = mapped_column(default=0)
    z: Mapped[int] = mapped_column(default=0)  # Z坐标，支持3D布线

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    device_type_id: Mapped[int] = mapped_column(ForeignKey("device_types.id"), index=True)

    project: Mapped["Project"] = relationship(back_populates="devices")
    device_type: Mapped["DeviceType"] = relationship(back_populates="devices")
