from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db
from app.core.permissions import get_current_user, check_permission
from app.models.user import User
from app.models.vehicle_type import VehicleType
from app.services.audit import log_audit

router = APIRouter()


class VehicleTypeCreate(BaseModel):
    code: str = Field(..., max_length=50, pattern=r"^[a-zA-Z0-9_\-]+$")
    name: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=200)


class VehicleTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


# 系统预置核心车型代码列表，不能被删除或禁用，也不能更改 code
CORE_VEHICLE_CODES = {"internal", "external", "truck"}


def _require_admin_permission(db: Session, current_user: User):
    """验证是否拥有车辆类型配置权限"""
    if not check_permission(db, current_user, "admin_vehicle_types"):
        raise HTTPException(status_code=403, detail={"code": 403, "message": "无权限"})


@router.get("/")
async def list_vehicle_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """列出所有车辆类型（管理后台用，含禁用）"""
    _require_admin_permission(db, current_user)
    items = db.query(VehicleType).order_by(VehicleType.id).all()
    return {
        "code": 0,
        "message": "ok",
        "data": [item.to_dict() for item in items]
    }


@router.get("/active")
async def list_active_vehicle_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取所有启用的车辆类型列表（所有人可用）"""
    items = db.query(VehicleType).filter(VehicleType.is_active == True).order_by(VehicleType.id).all()
    return {
        "code": 0,
        "message": "ok",
        "data": [item.to_dict() for item in items]
    }


@router.post("/")
async def create_vehicle_type(
    req: VehicleTypeCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """新建车辆类型"""
    _require_admin_permission(db, current_user)
    
    code_lower = req.code.strip().lower()
    # 限制代号防冲突
    if db.query(VehicleType).filter(VehicleType.code == code_lower).first():
        raise HTTPException(status_code=400, detail={"code": 400, "message": "车型代号已存在"})

    vt = VehicleType(
        code=code_lower,
        name=req.name.strip(),
        description=req.description.strip() if req.description else None,
        is_active=True
    )
    db.add(vt)
    db.flush()
    
    log_audit(db, user_id=current_user.id, username=current_user.username, action="create_vehicle_type",
              target_type="vehicle_type", target_id=vt.id, details={"code": code_lower, "name": req.name},
              ip_address=request.client.host if request.client else "")
    db.commit()
    return {"code": 0, "message": "创建成功", "data": vt.to_dict()}


@router.put("/{type_id}")
async def update_vehicle_type(
    type_id: int,
    req: VehicleTypeUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新车辆类型"""
    _require_admin_permission(db, current_user)
    
    vt = db.query(VehicleType).filter(VehicleType.id == type_id).first()
    if not vt:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "车型不存在"})

    # 如果是系统预置核心车型，限制其某些属性的改动
    is_core = vt.code in CORE_VEHICLE_CODES

    if req.name is not None:
        vt.name = req.name.strip()
    if req.description is not None:
        vt.description = req.description.strip()
    if req.is_active is not None:
        if is_core and not req.is_active:
            raise HTTPException(status_code=400, detail={"code": 400, "message": "系统核心车型无法被禁用"})
        vt.is_active = req.is_active

    db.commit()
    
    log_audit(db, user_id=current_user.id, username=current_user.username, action="update_vehicle_type",
              target_type="vehicle_type", target_id=vt.id, details={"code": vt.code},
              ip_address=request.client.host if request.client else "")
              
    return {"code": 0, "message": "更新成功", "data": vt.to_dict()}


@router.delete("/{type_id}")
async def delete_vehicle_type(
    type_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除车辆类型"""
    _require_admin_permission(db, current_user)
    
    vt = db.query(VehicleType).filter(VehicleType.id == type_id).first()
    if not vt:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "车型不存在"})

    if vt.code in CORE_VEHICLE_CODES:
        raise HTTPException(status_code=400, detail={"code": 400, "message": "系统核心车型不允许删除"})

    db.delete(vt)
    db.commit()
    
    log_audit(db, user_id=current_user.id, username=current_user.username, action="delete_vehicle_type",
              target_type="vehicle_type", target_id=type_id, details={"code": vt.code},
              ip_address=request.client.host if request.client else "")
              
    return {"code": 0, "message": "删除成功", "data": None}
