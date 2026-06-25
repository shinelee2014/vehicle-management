"""
审批人列表 API：返回所有可作为审批人的用户
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User, UserRole

router = APIRouter()


@router.get("/")
async def list_approvers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取所有可作为审批人的用户"""
    items = (
        db.query(User)
        .filter(User.is_approver == True, User.is_active == True)
        .order_by(User.id)
        .all()
    )
    return {
        "code": 0,
        "message": "ok",
        "data": [
            {
                "id": u.id,
                "real_name": u.real_name,
                "role": u.role.value if hasattr(u.role, "value") else u.role,
                "post_id": u.post_id,
            }
            for u in items
        ],
    }
