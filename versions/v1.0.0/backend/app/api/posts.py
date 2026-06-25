"""
岗亭管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User, UserRole
from app.models.post import Post
from app.services.audit import log_audit

router = APIRouter()


class PostCreate(BaseModel):
    name: str
    location: Optional[str] = None
    sort_order: int = 0


class PostUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """岗亭列表（所有人可看）"""
    items = db.query(Post).order_by(Post.sort_order, Post.id).all()
    return {
        "code": 0,
        "message": "ok",
        "data": [p.to_dict() for p in items],
    }


@router.post("/")
async def create_post(
    req: PostCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建岗亭（仅管理员）"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    if db.query(Post).filter(Post.name == req.name).first():
        raise HTTPException(status_code=400, detail={"code": 400, "message": "岗亭名已存在"})

    post = Post(name=req.name, location=req.location, sort_order=req.sort_order)
    db.add(post)
    db.flush()
    log_audit(db, user_id=current_user.id, username=current_user.username, action="create_post",
              target_type="post", target_id=post.id, ip_address=request.client.host if request.client else "")
    db.commit()
    return {"code": 0, "message": "创建成功", "data": post.to_dict()}


@router.put("/{post_id}")
async def update_post(
    post_id: int,
    req: PostUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新岗亭（仅管理员）"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "岗亭不存在"})

    if req.name is not None:
        post.name = req.name
    if req.location is not None:
        post.location = req.location
    if req.sort_order is not None:
        post.sort_order = req.sort_order
    if req.is_active is not None:
        post.is_active = req.is_active

    db.commit()
    return {"code": 0, "message": "更新成功", "data": post.to_dict()}


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除岗亭（仅管理员，软删）"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "岗亭不存在"})

    post.is_active = False
    db.commit()
    return {"code": 0, "message": "已删除", "data": None}
