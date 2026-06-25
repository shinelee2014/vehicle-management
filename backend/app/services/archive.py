"""
数据归档：1 年前的记录自动迁移到 records_archive 表
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings

logger = logging.getLogger(__name__)


def auto_archive_old_records(db: Session) -> int:
    """
    把 archive_months 月前的记录从 records 移到 records_archive
    返回归档条数
    """
    months = settings.archive_months
    cutoff = datetime.utcnow() - timedelta(days=months * 30)

    # 1. 复制到归档表
    sql_insert = text("""
        INSERT INTO records_archive
        SELECT * FROM records
        WHERE created_at < :cutoff AND archived_at IS NULL
    """)
    result = db.execute(sql_insert, {"cutoff": cutoff})
    count = result.rowcount

    # 2. 标记原表
    sql_update = text("""
        UPDATE records SET archived_at = :now
        WHERE created_at < :cutoff AND archived_at IS NULL
    """)
    db.execute(sql_update, {"cutoff": cutoff, "now": datetime.utcnow()})

    db.commit()
    return count
