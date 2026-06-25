"""
启动时初始化：重置默认账号密码 + 默认角色权限 + 内置模块
"""
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.models.user import User
from app.models.role_module import RoleModule, DEFAULT_ROLE_MODULES
from app.models.module import Module, BUILTIN_MODULES

logger = logging.getLogger(__name__)

# 占位符 → 默认密码映射
DEFAULT_PASSWORD_MAP = {
    "admin": "admin123",
    "security1": "123456",
    "security2": "123456",
    "supervisor1": "123456",
    "supervisor2": "123456",
}


def ensure_default_passwords(db: Session) -> None:
    """首次启动时，把 __DEFAULT__ 占位符的密码重置为默认密码"""
    users = db.query(User).filter(User.password_hash == "__DEFAULT__").all()
    if not users:
        return
    for user in users:
        default_pwd = DEFAULT_PASSWORD_MAP.get(user.username, "123456")
        user.password_hash = hash_password(default_pwd)
        logger.warning(
            f"⚠️  重置默认账号 {user.username} 的密码为 {default_pwd}，"
            f"⚠️  请在首次登录后立即修改！"
        )
    db.commit()


def ensure_builtin_modules(db: Session) -> None:
    """首次启动时写入内置模块（已存在的不会覆盖，多 worker 启动也不会冲突）"""
    added = 0
    for m in BUILTIN_MODULES:
        existing = db.query(Module).filter(Module.code == m["code"]).first()
        if existing:
            continue
        try:
            db.add(Module(**m, is_builtin=True, is_active=True))
            db.flush()  # 立刻 flush，能立刻看到 unique 冲突
            added += 1
        except IntegrityError:
            db.rollback()  # 别的 worker 已经插入了，跳过
            continue
    if added:
        logger.info(f"✓ 写入 {added} 个内置模块")
        db.commit()


def ensure_default_role_modules(db: Session) -> None:
    """首次启动时，给所有内置角色写入默认可见模块；
    已有配置的角色不会被覆盖（admin 可以到「角色权限」页调整）"""
    added = 0
    for role, modules in DEFAULT_ROLE_MODULES.items():
        if db.query(RoleModule).filter(RoleModule.role == role).first():
            continue
        if modules == "ALL":
            # 管理员：默认全部已存在模块的 code
            modules = [m.code for m in db.query(Module).all()]
        try:
            db.add(RoleModule(role=role, modules=modules))
            db.flush()
            added += 1
        except IntegrityError:
            db.rollback()
            continue
    if added:
        logger.info(f"✓ 初始化 {added} 个角色的默认模块权限")
        db.commit()




