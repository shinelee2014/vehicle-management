"""
角色-功能模块权限模型

设计：用单表存储（role, modules JSON），避免多对多关联表
- role: 角色名（security/supervisor/approver/admin）
- modules: 该角色可见的功能模块 code 列表

模块定义本身（name / path / icon / category）由 Module 表存（可自定义）
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import Session
from app.database import Base


# 默认角色权限（首次启动时写入数据库；模块 code 必须先存在于 modules 表）
DEFAULT_ROLE_MODULES = {
    "security": [
        "dashboard", "records_in", "records_out", "records_query",
        "messages", "profile",
    ],
    "approver": [
        "dashboard", "approval", "records_query",
        "messages", "profile",
    ],
    "supervisor": [
        "dashboard", "records_in", "records_out", "records_query",
        "approval", "reports", "messages", "profile",
        "admin_posts",
    ],
    "admin": "ALL",  # 标记：管理员默认全部模块（动态算出）
}


class RoleModule(Base):
    __tablename__ = "role_modules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String(20), unique=True, nullable=False)
    modules = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "modules": self.modules or [],
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def resolve_role_modules(db: Session, role: str, all_module_codes: list) -> list:
    """读取某角色的可见模块列表，没有配置时用默认；admin 默认全部"""
    if role == "admin":
        return list(all_module_codes)
    rm = db.query(RoleModule).filter(RoleModule.role == role).first()
    if rm and rm.modules:
        return list(rm.modules)
    defaults = DEFAULT_ROLE_MODULES.get(role, [])
    if defaults == "ALL":
        return list(all_module_codes)
    return list(defaults)

