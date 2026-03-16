import logging

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import CableType, DeviceType, User, WiringRule

logger = logging.getLogger(__name__)


def seed_data(db: Session) -> None:
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        db.add(User(username="admin", password_hash=get_password_hash("123456"), role="管理员"))

    if db.query(DeviceType).count() == 0:
        db.add_all(
            [
                DeviceType(name="核心交换机", category="网络设备", port_count=24, voltage="220V", size_desc="1U机架"),
                DeviceType(name="摄像头", category="安防设备", port_count=1, voltage="12V", size_desc="壁装"),
                DeviceType(name="配电箱", category="电力设备", port_count=12, voltage="380V", size_desc="落地式"),
            ]
        )

    if db.query(CableType).count() == 0:
        db.add_all(
            [
                CableType(name="Cat6网线", max_length=90, impedance="100ohm", shielded=False),
                CableType(name="单模光纤", max_length=5000, impedance="N/A", shielded=True),
                CableType(name="RVV电源线", max_length=200, impedance="N/A", shielded=False),
            ]
        )

    if db.query(WiringRule).count() == 0:
        db.add(
            WiringRule(
                name="默认综合布线规范",
                max_length=90,
                min_spacing=0.3,
                min_bend_radius=0.05,
                enabled=True,
                description="参考综合布线工程设计规范，限制单段长度并保留安全间距",
            )
        )

    db.commit()
    logger.info("初始化种子数据完成")
