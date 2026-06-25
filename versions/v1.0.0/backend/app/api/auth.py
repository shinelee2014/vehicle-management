"""
认证 API：登录、登出、获取当前用户、修改密码
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse, PasswordChangeRequest
from app.core.security import create_access_token, verify_password, hash_password
from app.core.permissions import get_current_user
from app.models.user import User
from app.models.role_module import RoleModule, resolve_role_modules
from app.models.module import Module
from app.services.audit import log_audit


def _visible_modules(db: Session, user: User) -> list:
    """返回某用户可见的模块 code 列表（用 Module 表 + RoleModule 配置动态算出）"""
    all_codes = [m.code for m in db.query(Module).filter(Module.is_active == True).all()]
    return resolve_role_modules(db, user.role, all_codes)


def _visible_module_details(db: Session, user: User) -> list:
    """返回某用户可见模块的完整对象列表（给前端动态渲染菜单用）"""
    codes = set(_visible_modules(db, user))
    modules = db.query(Module).filter(Module.is_active == True, Module.code.in_(codes)).order_by(Module.sort_order, Module.id).all()
    return [m.to_dict() for m in modules]  # 字段顺序：id, code, name, category, path, icon, ...

router = APIRouter()


@router.post("/login", response_model=dict)
async def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """登录"""
    user = db.query(User).filter(User.username == req.username).first()

    if not user or not user.is_active:
        log_audit(db, user_id=None, username=req.username, action="login", ip_address=_ip(request), status="failed", error_message="用户不存在或已禁用")
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401, "message": "账号或密码错误"},
        )

    if not verify_password(req.password, user.password_hash):
        log_audit(db, user_id=user.id, username=req.username, action="login", ip_address=_ip(request), status="failed", error_message="密码错误")
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 401, "message": "账号或密码错误"},
        )

    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    db.commit()

    # 签发 token
    token = create_access_token(
        data={"user_id": user.id, "username": user.username, "role": user.role.value if hasattr(user.role, "value") else user.role}
    )

    # 审计日志
    log_audit(db, user_id=user.id, username=user.username, action="login", ip_address=_ip(request), status="success")
    db.commit()

    return {
        "code": 0,
        "message": "登录成功",
        "data": {
            "access_token": token,
            "token_type": "Bearer",
            "user": user.to_dict(include_post=True),
            "visible_modules": _visible_module_details(db, user),
        },
    }


@router.post("/logout")
async def logout(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """登出（前端清 token，后端记录日志）"""
    log_audit(db, user_id=current_user.id, username=current_user.username, action="logout", ip_address=_ip(request), status="success")
    db.commit()
    return {"code": 0, "message": "已登出", "data": None}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户信息"""
    return {
        "code": 0,
        "message": "ok",
        "data": {
            **current_user.to_dict(include_post=True),
            "visible_modules": _visible_module_details(db, current_user),
        },
    }


@router.put("/password")
async def change_password(req: PasswordChangeRequest, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """修改自己的密码"""
    if not verify_password(req.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 400, "message": "旧密码错误"},
        )
    current_user.password_hash = hash_password(req.new_password)
    log_audit(db, user_id=current_user.id, username=current_user.username, action="change_password", ip_address=_ip(request), status="success")
    db.commit()
    return {"code": 0, "message": "密码修改成功", "data": None}


def _ip(request: Request) -> str:
    return request.client.host if request.client else ""
