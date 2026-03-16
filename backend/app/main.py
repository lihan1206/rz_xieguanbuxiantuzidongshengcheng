import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, devices, projects, wiring
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.base import Base
from app.db.init_db import seed_data
from app.db.session import SessionLocal, engine

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(projects.router, prefix=settings.api_prefix)
app.include_router(devices.router, prefix=settings.api_prefix)
app.include_router(wiring.router, prefix=settings.api_prefix)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.on_event("startup")
def on_startup() -> None:
    logger.info("开始初始化数据库")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
    logger.info("应用启动完成")
