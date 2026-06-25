"""
审计日志 API（管理员）
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog

router = APIRouter()


@router.get("/")
async def list_logs(
    page: int = 1,
    page_size: int = 20,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """审计日志列表（仅管理员）"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if status:
        query = query.filter(AuditLog.status == status)

    total = query.count()
    items = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "items": [log.to_dict() for log in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }
