"""
报表 API
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User, UserRole
from app.models.post import Post
from app.models.record import Record, VehicleType, ApprovalStatus, Direction

router = APIRouter()


def _date_range(frequency: str, start_date: str = None, end_date: str = None):
    """计算日期范围"""
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    if frequency == "today":
        return today_start, now
    if frequency == "week":
        return today_start - timedelta(days=now.weekday()), now
    if frequency == "month":
        return datetime(now.year, now.month, 1), now
    if frequency == "custom" and start_date and end_date:
        try:
            s = datetime.strptime(start_date, "%Y-%m-%d")
            e = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            return s, e
        except ValueError:
            pass
    return today_start, now


@router.get("/daily")
async def daily_report(
    date: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """日报数据"""
    if current_user.role == UserRole.SECURITY.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    if date:
        try:
            start = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail={"code": 400, "message": "日期格式错误"})
    else:
        now = datetime.now()
        start = datetime(now.year, now.month, now.day)
    end = start + timedelta(days=1)

    return _build_report(db, start, end, "日报")


@router.get("/weekly")
async def weekly_report(
    start_date: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """周报数据"""
    if current_user.role == UserRole.SECURITY.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    start, end = _date_range("week", start_date)
    return _build_report(db, start, end, "周报")


@router.get("/monthly")
async def monthly_report(
    year: int = None,
    month: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """月报数据"""
    if current_user.role == UserRole.SECURITY.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return _build_report(db, start, end, f"{year}-{month:02d} 月报")


@router.get("/summary")
async def summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """汇总统计（用于报表页头部）"""
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    month_start = datetime(now.year, now.month, 1)
    week_start = today_start - timedelta(days=now.weekday())

    def count_in(start):
        return db.query(func.count(Record.id)).filter(
            Record.direction == Direction.IN, Record.in_time >= start
        ).scalar() or 0

    def count_out(start):
        return db.query(func.count(Record.id)).filter(
            Record.direction == Direction.OUT, Record.out_time >= start
        ).scalar() or 0

    def count_truck(start):
        return db.query(func.count(Record.id)).filter(
            Record.vehicle_type == VehicleType.TRUCK, Record.in_time >= start
        ).scalar() or 0

    # 平均停留（只算已完成的）
    avg_duration = db.query(func.avg(Record.loading_duration)).filter(
        Record.loading_duration.isnot(None),
        Record.in_time >= month_start,
    ).scalar() or 0

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "today_in": count_in(today_start),
            "today_out": count_out(today_start),
            "week_in": count_in(week_start),
            "week_out": count_out(week_start),
            "month_in": count_in(month_start),
            "month_out": count_out(month_start),
            "month_truck": count_truck(month_start),
            "avg_duration": round(float(avg_duration), 1),
        },
    }


def _build_report(db: Session, start: datetime, end: datetime, title: str) -> dict:
    """构造完整报表数据"""
    # 总数
    in_count = db.query(func.count(Record.id)).filter(
        Record.direction == Direction.IN, Record.in_time >= start, Record.in_time < end
    ).scalar() or 0

    out_count = db.query(func.count(Record.id)).filter(
        Record.direction == Direction.OUT, Record.out_time >= start, Record.out_time < end
    ).scalar() or 0

    # 按类型
    by_type = db.query(Record.vehicle_type, func.count(Record.id)).filter(
        Record.direction == Direction.IN, Record.in_time >= start, Record.in_time < end
    ).group_by(Record.vehicle_type).all()
    type_stats = {t.value if hasattr(t, "value") else t: c for t, c in by_type}

    # 按岗亭
    by_post = db.query(Record.post_id, func.count(Record.id)).filter(
        Record.direction == Direction.IN, Record.in_time >= start, Record.in_time < end
    ).group_by(Record.post_id).all()
    posts = {p.id: p.name for p in db.query(Post).all()}
    post_stats = [{"post_id": pid, "post_name": posts.get(pid, f"#{pid}"), "count": c} for pid, c in by_post]

    # 按审批人
    by_approver = db.query(Record.approver_id, Record.approver_name, func.count(Record.id)).filter(
        Record.in_time >= start, Record.in_time < end
    ).group_by(Record.approver_id, Record.approver_name).all()
    approver_stats = [
        {"approver_id": aid, "approver_name": aname, "count": c}
        for aid, aname, c in by_approver if aid is not None
    ]

    # 按日期趋势（每日）
    days = (end - start).days
    if days > 60:
        days = 60  # 防止太多
    trend = []
    for i in range(min(days, 31)):
        d = start + timedelta(days=i)
        d_end = d + timedelta(days=1)
        c = db.query(func.count(Record.id)).filter(
            Record.direction == Direction.IN, Record.in_time >= d, Record.in_time < d_end
        ).scalar() or 0
        trend.append({"date": d.strftime("%Y-%m-%d"), "count": c})

    # 平均停留
    avg_duration = db.query(func.avg(Record.loading_duration)).filter(
        Record.loading_duration.isnot(None),
        Record.in_time >= start, Record.in_time < end,
    ).scalar() or 0

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "title": title,
            "period": {
                "start": start.strftime("%Y-%m-%d"),
                "end": (end - timedelta(days=1)).strftime("%Y-%m-%d"),
            },
            "totals": {
                "in_count": in_count,
                "out_count": out_count,
                "truck_count": type_stats.get("truck", 0),
                "internal_count": type_stats.get("internal", 0),
                "external_count": type_stats.get("external", 0),
                "avg_duration": round(float(avg_duration), 1),
            },
            "by_type": [
                {"type": "internal", "name": "内部车", "count": type_stats.get("internal", 0)},
                {"type": "external", "name": "外部车", "count": type_stats.get("external", 0)},
                {"type": "truck", "name": "货车", "count": type_stats.get("truck", 0)},
            ],
            "by_post": post_stats,
            "by_approver": approver_stats,
            "trend": trend,
        },
    }
