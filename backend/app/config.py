"""
应用配置
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用
    app_name: str = "厂区车辆进出管理系统"
    app_env: str = "development"
    log_level: str = "INFO"

    # 数据库
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "vehicle_mgmt"
    db_user: str = "vehicle"
    db_password: str = "vehicle123"

    # JWT
    jwt_secret: str = "please-change-this"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 8

    # 照片
    photo_base_dir: str = "./photos"
    photo_max_size_mb: int = 10
    photo_quality: int = 85
    watermark_format: str = "{time} | {post} | {operator}"
    watermark_position: str = "bottom_right"

    # CORS
    cors_origins: List[str] = ["*"]

    # 业务
    archive_months: int = 12
    approval_timeout_minutes: int = 30
    approval_timeout_action: str = "auto_approve"  # auto_approve / auto_reject

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


settings = Settings()
