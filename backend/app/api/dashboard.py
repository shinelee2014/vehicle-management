"""
仪表盘 API：首页统计数据
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.models.record import Record, VehicleType, ApprovalStatus, Direction

router = APIRouter()


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """首页统计数据"""
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    # 今日进场
    today_in = (
        db.query(func.count(Record.id))
        .filter(
            Record.direction == Direction.IN,
            Record.in_time >= today_start,
            Record.in_time < today_end,
            Record.is_deleted == False,
        )
        .scalar() or 0
    )
    # 今日出场
    today_out = (
        db.query(func.count(Record.id))
        .filter(
            Record.direction == Direction.OUT,
            Record.out_time >= today_start,
            Record.out_time < today_end,
            Record.is_deleted == False,
        )
        .scalar() or 0
    )
    # 今日货车
    today_truck = (
        db.query(func.count(Record.id))
        .filter(
            Record.vehicle_type == VehicleType.TRUCK,
            Record.in_time >= today_start,
            Record.in_time < today_end,
            Record.is_deleted == False,
        )
        .scalar() or 0
    )
    # 在场车辆（已批准进场但未出场）
    in_vehicle = (
        db.query(func.count(Record.id))
        .filter(
            Record.direction == Direction.IN,
            Record.approval_status.in_([ApprovalStatus.APPROVED, ApprovalStatus.TIMEOUT]),
            Record.companion_id.is_(None),
            Record.is_deleted == False,
        )
        .scalar() or 0
    )
    # 待我审批
    pending_me = (
        db.query(func.count(Record.id))
        .filter(
            Record.approver_id == current_user.id,
            Record.approval_status == ApprovalStatus.PENDING,
            Record.is_deleted == False,
        )
        .scalar() or 0
    )

    # 最近 7 天趋势
    seven_days_ago = today_start - timedelta(days=6)
    trend_query = (
        db.query(
            func.date(Record.in_time).label("date"),
            func.count(Record.id).label("count"),
        )
        .filter(
            Record.in_time >= seven_days_ago,
            Record.direction == Direction.IN,
            Record.is_deleted == False,
        )
        .group_by(func.date(Record.in_time))
        .all()
    )
    trend_map = {str(d): c for d, c in trend_query}
    trend = []
    for i in range(7):
        d = (seven_days_ago + timedelta(days=i)).strftime("%Y-%m-%d")
        trend.append({"date": d, "count": trend_map.get(d, 0)})

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "today_in": today_in,
            "today_out": today_out,
            "today_truck": today_truck,
            "in_vehicle": in_vehicle,
            "pending_me": pending_me,
            "trend": trend,
        },
    }
