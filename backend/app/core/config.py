from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从环境变量和 backend/.env 加载的应用配置。"""

    app_name: str = "AI智能数据分析助手"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    cors_allowed_origins: str = "http://127.0.0.1:5500,http://localhost:5500"

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_database: str = "ai_data_analysis"
    mysql_user: str = "root"
    mysql_password: str = ""

    storage_root: str = "../storage"
    frontend_index_path: str = "../../frontend/index.html"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def resolved_frontend_index_path(self) -> Path:
        return (Path(__file__).resolve().parents[2] / self.frontend_index_path).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
