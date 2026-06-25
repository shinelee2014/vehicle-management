"""
审计日志服务
"""
import json
from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog, AuditStatus


def log_audit(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    status: str = "success",
    error_message: Optional[str] = None,
) -> None:
    """记录审计日志（不自动 commit，由调用方统一 commit）"""
    log = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        status=AuditStatus(status),
        error_message=error_message,
    )
    db.add(log)
