"""
自定义模块管理 API（仅管理员）

- GET    /modules/                列出所有模块
- GET    /modules/{id}            详情
- POST   /modules/                新建自定义模块
- PUT    /modules/{id}            更新（内置模块不能改 code/path）
- DELETE /modules/{id}            删除（只能删自定义模块）
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User, UserRole
from app.models.module import Module, BUILTIN_MODULES
from app.services.audit import log_audit

router = APIRouter()


def _require_admin(current_user: User):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail={"code": 403, "message": "仅管理员可访问"})


@router.get("/")
async def list_modules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """列出所有模块（已登录用户都能看，自定义模块用于动态菜单渲染）"""
    items = db.query(Module).order_by(Module.sort_order, Module.id).all()
    return {"code": 0, "message": "ok", "data": {"items": [m.to_dict() for m in items]}}


@router.get("/{module_id}")
async def get_module(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    m = db.query(Module).filter(Module.id == module_id).first()
    if not m:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "模块不存在"})
    return {"code": 0, "message": "ok", "data": m.to_dict()}


@router.post("/")
async def create_module(
    payload: dict,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """新建自定义模块（仅管理员）"""
    _require_admin(current_user)

    code = (payload.get("code") or "").strip()
    name = (payload.get("name") or "").strip()
    path = (payload.get("path") or "").strip()
    if not code or not name or not path:
        raise HTTPException(status_code=400, detail={"code": 400, "message": "code / name / path 必填"})

    if db.query(Module).filter(Module.code == code).first():
        raise HTTPException(status_code=400, detail={"code": 400, "message": f"模块 code 已存在: {code}"})

    m = Module(
        code=code,
        name=name,
        description=payload.get("description", ""),
        category=payload.get("category", "自定义"),
        path=path if path.startswith("/") else f"/{path}",
        icon=payload.get("icon", "Menu"),
        sort_order=int(payload.get("sort_order", 999)),
        is_builtin=False,
        is_active=bool(payload.get("is_active", True)),
    )
    db.add(m)
    db.flush()
    log_audit(
        db, user_id=current_user.id, username=current_user.username,
        action="create_module", target_type="module", target_id=m.id,
        details=m.to_dict(),
        ip_address=request.client.host if request.client else "",
    )
    db.commit()
    return {"code": 0, "message": "创建成功", "data": m.to_dict()}


@router.put("/{module_id}")
async def update_module(
    module_id: int,
    payload: dict,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新模块（仅管理员；内置模块不能改 code）"""
    _require_admin(current_user)
    m = db.query(Module).filter(Module.id == module_id).first()
    if not m:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "模块不存在"})

    # 内置模块：code 不能改（会破坏前端组件逻辑），path 可以改
    if m.is_builtin:
        if "code" in payload and payload["code"] != m.code:
            raise HTTPException(status_code=400, detail={"code": 400, "message": "内置模块 code 不能修改"})
        if "is_builtin" in payload and payload["is_builtin"] != m.is_builtin:
            raise HTTPException(status_code=400, detail={"code": 400, "message": "不能修改内置标识"})

    if "name" in payload:
        m.name = payload["name"].strip() or m.name
    if "description" in payload:
        m.description = payload["description"]
    if "category" in payload:
        m.category = payload["category"]
    if "path" in payload:
        new_path = (payload["path"] or "").strip()
        m.path = new_path if new_path.startswith("/") else f"/{new_path}"
    if "icon" in payload:
        m.icon = payload["icon"] or "Menu"
    if "sort_order" in payload:
        m.sort_order = int(payload["sort_order"])
    if "is_active" in payload:
        m.is_active = bool(payload["is_active"])
    if not m.is_builtin and "code" in payload:
        new_code = (payload["code"] or "").strip()
        if new_code != m.code:
            if db.query(Module).filter(Module.code == new_code).first():
                raise HTTPException(status_code=400, detail={"code": 400, "message": f"模块 code 已存在: {new_code}"})
            m.code = new_code

    db.flush()
    log_audit(
        db, user_id=current_user.id, username=current_user.username,
        action="update_module", target_type="module", target_id=m.id,
        details=m.to_dict(),
        ip_address=request.client.host if request.client else "",
    )
    db.commit()
    return {"code": 0, "message": "已保存", "data": m.to_dict()}


@router.delete("/{module_id}")
async def delete_module(
    module_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除模块（仅管理员；只能删自定义模块）"""
    _require_admin(current_user)
    m = db.query(Module).filter(Module.id == module_id).first()
    if not m:
        raise HTTPException(status_code=404, detail={"code": 404, "message": "模块不存在"})
    if m.is_builtin:
        raise HTTPException(status_code=400, detail={"code": 400, "message": "内置模块不能删除"})

    # 同时从所有角色的 modules 数组里移除这个 code
    from app.models.role_module import RoleModule
    role_modules = db.query(RoleModule).all()
    for rm in role_modules:
        if rm.modules and m.code in rm.modules:
            rm.modules = [c for c in rm.modules if c != m.code]

    db.delete(m)
    db.flush()
    log_audit(
        db, user_id=current_user.id, username=current_user.username,
        action="delete_module", target_type="module", target_id=module_id,
        details={"code": m.code},
        ip_address=request.client.host if request.client else "",
    )
    db.commit()
    return {"code": 0, "message": "已删除", "data": None}
