"""
报表数据生成
"""
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.record import Record, VehicleType, ApprovalStatus


def generate_report_data(db: Session, frequency: str) -> dict:
    """生成指定频率的报表数据"""
    now = datetime.now()
    if frequency == "daily":
        start = datetime(now.year, now.month, now.day)
        title = f"{start.strftime('%Y-%m-%d')} 日报"
    elif frequency == "weekly":
        start = now - timedelta(days=now.weekday())
        start = datetime(start.year, start.month, start.day)
        title = f"{start.strftime('%Y-%m-%d')} 周报"
    elif frequency == "monthly":
        start = datetime(now.year, now.month, 1)
        title = f"{start.strftime('%Y-%m')} 月报"
    else:
        start = now - timedelta(days=1)
        title = "报表"

    # 统计数据
    in_count = db.query(func.count(Record.id)).filter(
        Record.direction == "in",
        Record.in_time >= start,
    ).scalar() or 0

    out_count = db.query(func.count(Record.id)).filter(
        Record.direction == "out",
        Record.out_time >= start,
    ).scalar() or 0

    truck_count = db.query(func.count(Record.id)).filter(
        Record.vehicle_type == VehicleType.TRUCK,
        Record.in_time >= start,
    ).scalar() or 0

    pending_count = db.query(func.count(Record.id)).filter(
        Record.approval_status == ApprovalStatus.PENDING,
    ).scalar() or 0

    content = (
        f"📊 统计周期：{start.strftime('%Y-%m-%d %H:%M')} ~ {now.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"🚗 进场：{in_count} 次\n"
        f"🚙 出场：{out_count} 次\n"
        f"🚛 货车：{truck_count} 次\n"
        f"⏳ 待审批：{pending_count} 条\n"
    )
    return {
        "title": title,
        "content": content,
        "stats": {
            "in_count": in_count,
            "out_count": out_count,
            "truck_count": truck_count,
            "pending_count": pending_count,
        },
    }
