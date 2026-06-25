"""
定时报表推送（每日/每周/每月）
"""
import logging
from datetime import datetime, time
from sqlalchemy.orm import Session
from app.models.report_config import ReportConfig, Frequency

logger = logging.getLogger(__name__)


def generate_and_send_reports(db: Session) -> int:
    """
    检查所有启用的推送配置，匹配当前时间的就生成并发送
    返回发送条数
    """
    now = datetime.now()
    current_time = now.time()
    current_weekday = now.isoweekday()  # 1-7
    current_day = now.day

    configs = db.query(ReportConfig).filter(ReportConfig.enabled == 1).all()
    sent_count = 0

    for cfg in configs:
        if not _should_run(cfg, current_time, current_weekday, current_day):
            continue
        try:
            _send_report(db, cfg)
            cfg.last_run_at = datetime.utcnow()
            sent_count += 1
        except Exception as e:
            logger.exception(f"推送配置 {cfg.name} 失败: {e}")

    if sent_count > 0:
        db.commit()
    return sent_count


def _should_run(cfg: ReportConfig, current_time: time, current_weekday: int, current_day: int) -> bool:
    """判断是否应该跑这个配置"""
    if cfg.run_time is None:
        return False
    # 时间窗口：分钟内匹配
    if cfg.run_time.hour != current_time.hour or cfg.run_time.minute != current_time.minute:
        return False
    freq = cfg.frequency.value if hasattr(cfg.frequency, "value") else cfg.frequency
    if freq == Frequency.DAILY.value:
        return True
    elif freq == Frequency.WEEKLY.value:
        return cfg.run_weekday == current_weekday
    elif freq == Frequency.MONTHLY.value:
        return cfg.run_day == current_day if hasattr(cfg, "run_day") else current_day == 1
    return False


def _send_report(db: Session, cfg: ReportConfig) -> None:
    """
    实际发送报表（第一期实现：站内消息）
    后期可扩展：邮件、企业微信 webhook
    """
    from app.models.message import Message, MessageType
    from app.models.user import User
    from app.services.report_data import generate_report_data

    # 生成报表数据
    data = generate_report_data(db, cfg.frequency.value if hasattr(cfg.frequency, "value") else cfg.frequency)

    # 站内消息推送
    recipients = cfg.recipients or []
    for user_id in recipients:
        msg = Message(
            recipient_id=user_id,
            sender_id=0,
            sender_name="系统",
            type=MessageType.SYSTEM,
            title=f"【{cfg.name}】{data['title']}",
            content=data["content"],
            related_record_id=None,
        )
        db.add(msg)

    # 邮件推送（预留接口）
    # send_email(cfg, data)
