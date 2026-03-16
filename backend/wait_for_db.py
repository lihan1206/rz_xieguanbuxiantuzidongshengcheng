import logging
import time

from sqlalchemy import create_engine, text

from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def wait_for_db(timeout: int = 60) -> None:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    start = time.time()
    while time.time() - start < timeout:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("数据库连接成功")
            return
        except Exception:
            logger.info("等待数据库启动中...")
            time.sleep(2)
    raise RuntimeError("数据库在超时时间内未就绪")


if __name__ == "__main__":
    wait_for_db()
