"""
用户管理 API（管理员）
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.core.security import hash_password
from app.core.permissions import get_current_user
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, PasswordReset
from app.services.audit import log_audit

router = APIRouter()


@router.get("/")
async def list_users(
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    role: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用户列表（仅管理员）"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    query = db.query(User)
    if keyword:
        query = query.filter(or_(
            User.username.like(f"%{keyword}%"),
            User.real_name.like(f"%{keyword}%"),
        ))
    if role:
        query = query.filter(User.role == role)

    total = query.count()
    items = query.order_by(User.id).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "items": [u.to_dict(include_post=True) for u in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("/")
async def create_user(
    req: UserCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建用户（仅管理员）"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail={"code": 400, "message": "账号已存在"})

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        real_name=req.real_name,
        role=UserRole(req.role).value,
        post_id=req.post_id,
        is_approver=req.is_approver,
        phone=req.phone,
        email=req.email,
        is_active=True,
    )
    db.add(user)
    db.flush()
    log_audit(db, user_id=current_user.id, username=current_user.username, action="create_user",
              target_type="user", target_id=user.id, details={"username": req.username},
              ip_address=request.client.host if request.client else "")
    db.commit()
    return {"code": 0, "message": "创建成功", "data": user.to_dict()}


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    req: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新用户（仅管理员）"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "用户不存在"})

    if req.real_name is not None:
        user.real_name = req.real_name
    if req.role is not None:
        user.role = UserRole(req.role).value
    if req.post_id is not None:
        user.post_id = req.post_id
    if req.is_approver is not None:
        user.is_approver = req.is_approver
    if req.phone is not None:
        user.phone = req.phone
    if req.email is not None:
        user.email = req.email
    if req.is_active is not None:
        user.is_active = req.is_active

    log_audit(db, user_id=current_user.id, username=current_user.username, action="update_user",
              target_type="user", target_id=user.id, ip_address=request.client.host if request.client else "")
    db.commit()
    return {"code": 0, "message": "更新成功", "data": user.to_dict()}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """软删除用户（仅管理员）"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail={"code": 400, "message": "不能删除自己"})

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "用户不存在"})

    user.is_active = False
    log_audit(db, user_id=current_user.id, username=current_user.username, action="delete_user",
              target_type="user", target_id=user.id, ip_address=request.client.host if request.client else "")
    db.commit()
    return {"code": 0, "message": "已删除", "data": None}


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    req: PasswordReset,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """重置密码（仅管理员）"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "用户不存在"})

    user.password_hash = hash_password(req.new_password)
    log_audit(db, user_id=current_user.id, username=current_user.username, action="reset_password",
              target_type="user", target_id=user.id, ip_address=request.client.host if request.client else "")
    db.commit()
    return {"code": 0, "message": "密码已重置", "data": None}
