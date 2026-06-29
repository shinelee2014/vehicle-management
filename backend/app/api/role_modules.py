"""
角色权限管理 API（仅管理员）
- GET /role-modules/      列出全部角色的可见模块
- GET /role-modules/catalog  获取模块清单（含 code/name/description）
- PUT /role-modules/{role}   更新某角色的可见模块列表
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.permissions import get_current_user, check_permission
from app.models.user import User, UserRole
from app.models.role_module import RoleModule, DEFAULT_ROLE_MODULES
from app.models.module import Module
from app.services.audit import log_audit

router = APIRouter()


def _require_admin(current_user: User, db: Session):
    if not check_permission(db, current_user, "admin_role_modules"):
        raise HTTPException(status_code=403, detail={"code": 403, "message": "仅管理员可访问"})


@router.get("/catalog")
async def get_module_catalog(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取模块清单（从 modules 表读取，方便前端渲染菜单）"""
    items = db.query(Module).order_by(Module.sort_order, Module.id).all()
    return {"code": 0, "message": "ok", "data": {"modules": [m.to_dict() for m in items]}}


@router.get("/")
async def list_role_modules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """列出全部角色的可见模块（仅管理员）"""
    _require_admin(current_user, db)
    items = db.query(RoleModule).order_by(RoleModule.role).all()
    # 没配置的角色也返回默认值（方便前端展示）
    rows = {r.role: r.to_dict() for r in items}
    for role in DEFAULT_ROLE_MODULES:
        if role not in rows:
            rows[role] = {"role": role, "modules": DEFAULT_ROLE_MODULES[role], "updated_at": None}
    return {"code": 0, "message": "ok", "data": {"items": list(rows.values())}}


@router.put("/{role}")
async def update_role_modules(
    role: str,
    payload: dict,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新某角色的可见模块（仅管理员）"""
    _require_admin(current_user, db)
    if role not in DEFAULT_ROLE_MODULES:
        raise HTTPException(status_code=400, detail={"code": 400, "message": f"未知角色: {role}"})

    modules = payload.get("modules")
    if not isinstance(modules, list):
        raise HTTPException(status_code=400, detail={"code": 400, "message": "modules 必须是数组"})

    # 校验 module code 都在合法清单内
    valid_codes = {m.code for m in db.query(Module).all()}
    invalid = [m for m in modules if m not in valid_codes]
    if invalid:
        raise HTTPException(status_code=400, detail={"code": 400, "message": f"非法模块: {invalid}"})

    # upsert
    rm = db.query(RoleModule).filter(RoleModule.role == role).first()
    if rm:
        rm.modules = modules
    else:
        rm = RoleModule(role=role, modules=modules)
        db.add(rm)
    db.flush()

    log_audit(
        db, user_id=current_user.id, username=current_user.username,
        action="update_role_modules", target_type="role_module", target_id=None,
        details={"role": role, "modules": modules},
        ip_address=request.client.host if request.client else "",
    )
    db.commit()
    return {"code": 0, "message": "已保存", "data": rm.to_dict()}
