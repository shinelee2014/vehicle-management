"""
站内消息 ORM 模型
"""
from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from app.database import Base


class MessageType(str, enum.Enum):
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_RESULT = "approval_result"
    SYSTEM = "system"
    ANNOUNCEMENT = "announcement"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sender_id = Column(Integer, default=0)
    sender_name = Column(String(50), default="系统")
    type = Column(Enum(MessageType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    related_record_id = Column(Integer, ForeignKey("records.id"))
    is_read = Column(Integer, nullable=False, default=0)
    read_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "recipient_id": self.recipient_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "type": self.type.value if isinstance(self.type, MessageType) else self.type,
            "title": self.title,
            "content": self.content,
            "related_record_id": self.related_record_id,
            "is_read": bool(self.is_read),
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
