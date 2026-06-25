"""
定时推送配置 API（管理员）
"""
from datetime import time as dt_time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User, UserRole
from app.models.report_config import ReportConfig, Frequency

router = APIRouter()


class ReportConfigCreate(BaseModel):
    name: str
    frequency: str  # daily/weekly/monthly
    run_time: str  # HH:MM:SS
    run_weekday: Optional[int] = None  # 1-7
    recipients: List[int]
    enabled: bool = True


class ReportConfigUpdate(BaseModel):
    name: Optional[str] = None
    frequency: Optional[str] = None
    run_time: Optional[str] = None
    run_weekday: Optional[int] = None
    recipients: Optional[List[int]] = None
    enabled: Optional[bool] = None


def _parse_time(s: str) -> dt_time:
    parts = s.split(":")
    return dt_time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)


@router.get("/")
async def list_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """配置列表"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    items = db.query(ReportConfig).order_by(ReportConfig.id).all()
    return {"code": 0, "message": "ok", "data": [c.to_dict() for c in items]}


@router.post("/")
async def create_config(
    req: ReportConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """新建配置"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    config = ReportConfig(
        name=req.name,
        frequency=Frequency(req.frequency),
        run_time=_parse_time(req.run_time),
        run_weekday=req.run_weekday,
        recipients=req.recipients,
        enabled=1 if req.enabled else 0,
    )
    db.add(config)
    db.commit()
    return {"code": 0, "message": "创建成功", "data": config.to_dict()}


@router.put("/{config_id}")
async def update_config(
    config_id: int,
    req: ReportConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新配置"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    config = db.query(ReportConfig).filter(ReportConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "配置不存在"})

    if req.name is not None:
        config.name = req.name
    if req.frequency is not None:
        config.frequency = Frequency(req.frequency)
    if req.run_time is not None:
        config.run_time = _parse_time(req.run_time)
    if req.run_weekday is not None:
        config.run_weekday = req.run_weekday
    if req.recipients is not None:
        config.recipients = req.recipients
    if req.enabled is not None:
        config.enabled = 1 if req.enabled else 0

    db.commit()
    return {"code": 0, "message": "更新成功", "data": config.to_dict()}


@router.delete("/{config_id}")
async def delete_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除配置"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    config = db.query(ReportConfig).filter(ReportConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "配置不存在"})

    db.delete(config)
    db.commit()
    return {"code": 0, "message": "已删除", "data": None}
