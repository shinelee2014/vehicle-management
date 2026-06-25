"""
APScheduler 定时任务
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import SessionLocal
from app.services.report import generate_and_send_reports
from app.services.archive import auto_archive_old_records
from app.services.approval_timeout import handle_pending_approvals

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler = None


def start_scheduler() -> None:
    """启动定时任务"""
    global _scheduler
    if _scheduler:
        return

    _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

    # 1. 每分钟检查超时审批
    _scheduler.add_job(
        _job_handle_timeout,
        CronTrigger.from_crontab("* * * * *"),
        id="approval_timeout",
        name="检查超时审批",
        replace_existing=True,
    )

    # 2. 每天凌晨 3 点归档旧数据
    _scheduler.add_job(
        _job_archive,
        CronTrigger.from_crontab("0 3 * * *"),
        id="archive",
        name="归档 1 年前数据",
        replace_existing=True,
    )

    # 3. 每 10 分钟检查定时报表
    _scheduler.add_job(
        _job_send_reports,
        CronTrigger.from_crontab("*/10 * * * *"),
        id="send_reports",
        name="检查并发送定时报表",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("✓ 定时任务已启动（3 个任务）")


def stop_scheduler() -> None:
    """停止定时任务"""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def _job_handle_timeout() -> None:
    db = SessionLocal()
    try:
        handle_pending_approvals(db)
    except Exception as e:
        logger.exception(f"审批超时检查失败: {e}")
    finally:
        db.close()


def _job_archive() -> None:
    db = SessionLocal()
    try:
        count = auto_archive_old_records(db)
        logger.info(f"✓ 自动归档完成：{count} 条记录")
    except Exception as e:
        logger.exception(f"自动归档失败: {e}")
    finally:
        db.close()


def _job_send_reports() -> None:
    db = SessionLocal()
    try:
        generate_and_send_reports(db)
    except Exception as e:
        logger.exception(f"定时报表发送失败: {e}")
    finally:
        db.close()
