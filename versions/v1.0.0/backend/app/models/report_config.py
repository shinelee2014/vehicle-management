"""
定时推送配置 ORM 模型
"""
from datetime import datetime
from datetime import time as dt_time
import enum
from sqlalchemy import Column, Integer, String, DateTime, Time, JSON, Enum, SmallInteger
from app.database import Base


class Frequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ReportConfig(Base):
    __tablename__ = "report_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    frequency = Column(Enum(Frequency, values_callable=lambda x: [e.value for e in x]), nullable=False)
    run_time = Column(Time, nullable=False)
    run_weekday = Column(SmallInteger)
    recipients = Column(JSON, nullable=False)
    enabled = Column(Integer, nullable=False, default=1)
    last_run_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "frequency": self.frequency.value if isinstance(self.frequency, Frequency) else self.frequency,
            "run_time": self.run_time.strftime("%H:%M:%S") if self.run_time else None,
            "run_weekday": self.run_weekday,
            "recipients": self.recipients or [],
            "enabled": bool(self.enabled),
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
        }
