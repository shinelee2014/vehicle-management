"""
权限装饰器
"""
from functools import wraps
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import decode_token
from app.models.user import User

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """从 JWT 获取当前用户"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401, "message": "未登录"},
        )
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401, "message": "Token 无效或已过期"},
        )
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401, "message": "Token 异常"},
        )
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401, "message": "用户不存在或已禁用"},
        )
    return user


def require_roles(*allowed_roles: str):
    """权限装饰器工厂"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"code": 401, "message": "未登录"},
                )
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": 403, "message": f"无权限：需要 {allowed_roles}"},
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def check_permission(db: Session, user: User, module_code: str) -> bool:
    """动态检查用户是否有某个模块的权限（内置/自定义菜单）"""
    role_str = user.role.value if hasattr(user.role, "value") else user.role
    if role_str == "admin":
        return True

    from app.models.role_module import resolve_role_modules
    from app.models.module import Module

    all_codes = [m.code for m in db.query(Module).filter(Module.is_active == True).all()]
    visible = resolve_role_modules(db, role_str, all_codes)
    return module_code in visible

