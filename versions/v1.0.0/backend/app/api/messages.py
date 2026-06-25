"""
站内消息 API
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.models.message import Message

router = APIRouter()


@router.get("/")
async def list_messages(
    page: int = 1,
    page_size: int = 20,
    is_read: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """消息列表"""
    query = db.query(Message).filter(Message.recipient_id == current_user.id)
    if is_read is not None:
        query = query.filter(Message.is_read == (1 if is_read else 0))

    total = query.count()
    # 未读优先，按时间倒序
    items = (
        query.order_by(Message.is_read.asc(), Message.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "items": [m.to_dict() for m in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/unread-count")
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """未读数量"""
    count = (
        db.query(func.count(Message.id))
        .filter(Message.recipient_id == current_user.id, Message.is_read == 0)
        .scalar()
    )
    return {"code": 0, "message": "ok", "data": {"unread": count}}


@router.put("/{message_id}/read")
async def mark_read(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记已读"""
    msg = db.query(Message).filter(Message.id == message_id, Message.recipient_id == current_user.id).first()
    if not msg:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "消息不存在"})
    if not msg.is_read:
        msg.is_read = 1
        msg.read_at = datetime.utcnow()
        db.commit()
    return {"code": 0, "message": "ok", "data": None}


@router.put("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """全部已读"""
    db.query(Message).filter(
        Message.recipient_id == current_user.id, Message.is_read == 0
    ).update({"is_read": 1, "read_at": datetime.utcnow()})
    db.commit()
    return {"code": 0, "message": "ok", "data": None}
