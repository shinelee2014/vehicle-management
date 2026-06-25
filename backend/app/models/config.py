"""
系统配置 ORM 模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from app.database import Base


class SystemConfig(Base):
    __tablename__ = "system_configs"

    config_key = Column(String(50), primary_key=True)
    config_value = Column(Text, nullable=False)
    description = Column(String(200))
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "config_key": self.config_key,
            "config_value": self.config_value,
            "description": self.description,
        }
