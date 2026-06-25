"""
审计日志 ORM 模型
"""
from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON
from app.database import Base


class AuditStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    username = Column(String(50))
    action = Column(String(50), nullable=False, index=True)
    target_type = Column(String(20))
    target_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    status = Column(Enum(AuditStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=AuditStatus.SUCCESS)
    error_message = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "status": self.status.value if isinstance(self.status, AuditStatus) else self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
