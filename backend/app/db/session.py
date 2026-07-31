from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.dataset import Dataset, DatasetColumn  # noqa: F401
from app.models.user import Base


settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_database_tables() -> None:
    Base.metadata.create_all(bind=engine)


def is_database_available() -> bool:
    """执行最小查询；连接失败时返回 False，交由健康接口降级。"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
