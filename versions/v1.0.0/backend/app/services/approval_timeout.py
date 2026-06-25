"""
审批超时处理
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.config import settings
from app.models.record import Record, RecordStatus, ApprovalStatus

logger = logging.getLogger(__name__)


def handle_pending_approvals(db: Session) -> int:
    """
    处理超时未审批的记录
    返回处理的条数
    """
    timeout_minutes = settings.approval_timeout_minutes
    cutoff = datetime.utcnow() - timedelta(minutes=timeout_minutes)

    # 找出所有超时的待审记录
    records = (
        db.query(Record)
        .filter(Record.approval_status == ApprovalStatus.PENDING)
        .filter(Record.created_at < cutoff)
        .all()
    )

    if not records:
        return 0

    action = settings.approval_timeout_action
    for r in records:
        if action == "auto_approve":
            r.approval_status = ApprovalStatus.TIMEOUT
            r.approval_time = datetime.utcnow()
            r.approval_remark = f"系统：{timeout_minutes} 分钟未审批，自动通过"
            # 更新 status
            if r.direction.value == "in":
                r.status = RecordStatus.IN_TIMEOUT
            else:
                r.status = RecordStatus.OUT_TIMEOUT
        elif action == "auto_reject":
            r.approval_status = ApprovalStatus.TIMEOUT
            r.approval_time = datetime.utcnow()
            r.approval_remark = f"系统：{timeout_minutes} 分钟未审批，自动驳回"
            if r.direction.value == "in":
                r.status = RecordStatus.IN_TIMEOUT
            else:
                r.status = RecordStatus.OUT_TIMEOUT

    db.commit()
    logger.info(f"审批超时处理：{len(records)} 条")
    return len(records)
