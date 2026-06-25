"""
系统配置 API（管理员）
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User, UserRole
from app.models.config import SystemConfig

router = APIRouter()


class ConfigItem(BaseModel):
    config_key: str
    config_value: str
    description: Optional[str] = None


class ConfigUpdate(BaseModel):
    config_value: str


@router.get("/configs")
async def list_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取所有配置（仅管理员）"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    items = db.query(SystemConfig).order_by(SystemConfig.config_key).all()
    return {
        "code": 0,
        "message": "ok",
        "data": [c.to_dict() for c in items],
    }


@router.put("/configs/{key}")
async def update_config(
    key: str,
    req: ConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新配置（仅管理员）"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})

    config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    if not config:
        config = SystemConfig(config_key=key, config_value=req.config_value)
        db.add(config)
    else:
        config.config_value = req.config_value
    db.commit()
    return {"code": 0, "message": "更新成功", "data": config.to_dict()}
