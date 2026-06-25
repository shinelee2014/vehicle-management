"""
用户 ORM 模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    """角色枚举 - 值与数据库 ENUM 一致（小写）"""
    SECURITY = "security"
    SUPERVISOR = "supervisor"
    APPROVER = "approver"  # 审批人（独立角色：只负责审批，不能登记）
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    real_name = Column(String(50), nullable=False)
    # 用 String 而非 Enum，避免 MySQL ENUM 类型与 Python enum 的成员名/值映射冲突
    role = Column(String(20), nullable=False, default=UserRole.SECURITY.value)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="SET NULL"))
    is_approver = Column(Boolean, nullable=False, default=False)
    phone = Column(String(20))
    email = Column(String(100))
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    post = relationship("Post", back_populates="users", foreign_keys=[post_id])

    def to_dict(self, include_post: bool = False) -> dict:
        data = {
            "id": self.id,
            "username": self.username,
            "real_name": self.real_name,
            "role": self.role if self.role else UserRole.SECURITY.value,
            "post_id": self.post_id,
            "is_approver": self.is_approver,
            "phone": self.phone,
            "email": self.email,
            "is_active": self.is_active,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_post and self.post:
            data["post"] = {"id": self.post.id, "name": self.post.name}
        return data
