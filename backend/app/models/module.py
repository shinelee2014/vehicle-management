"""
自定义功能模块

- 内置模块：写死在代码里（dashboard / records_in / 等），code 不能改，不能删
- 自定义模块：管理员在「角色权限」页面新增，code 唯一，可以改/删

字段：
- code: 唯一标识（如 records_in）
- name: 显示名（如 进场登记）
- description: 描述
- category: 分类（业务/管理/基础/自定义）
- path: 前端路由路径（如 /records/in）
- icon: Element Plus 图标名（如 TopRight）
- sort_order: 菜单排序（数字小靠前）
- is_builtin: 是否内置（决定能否删除/改 code/path）
- is_active: 是否启用（关闭后菜单不显示）
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from app.database import Base


# 内置模块 seed 数据（首次启动写入数据库）
# path 是前端路由路径，icon 是 Element Plus 图标组件名
BUILTIN_MODULES = [
    {"code": "dashboard", "name": "首页", "description": "数据仪表盘", "category": "业务", "path": "/dashboard", "icon": "Odometer", "sort_order": 10},
    {"code": "records_in", "name": "进场登记", "description": "录入进场车辆", "category": "业务", "path": "/records/in", "icon": "TopRight", "sort_order": 20},
    {"code": "records_out", "name": "出场登记", "description": "录入出场车辆", "category": "业务", "path": "/records/out", "icon": "BottomRight", "sort_order": 30},
    {"code": "records_query", "name": "记录查询", "description": "查询所有进出记录", "category": "业务", "path": "/records", "icon": "Document", "sort_order": 40},
    {"code": "approval", "name": "待我审批", "description": "审批进/出记录", "category": "业务", "path": "/approval", "icon": "CircleCheck", "sort_order": 50},
    {"code": "reports", "name": "报表中心", "description": "周报/月报/年报", "category": "业务", "path": "/reports", "icon": "DataAnalysis", "sort_order": 60},
    {"code": "messages", "name": "消息中心", "description": "站内信", "category": "业务", "path": "/messages", "icon": "Bell", "sort_order": 70},
    {"code": "profile", "name": "个人中心", "description": "个人信息 + 修改密码", "category": "基础", "path": "/profile", "icon": "User", "sort_order": 80},
    {"code": "admin_users", "name": "用户管理", "description": "管理用户账号", "category": "管理", "path": "/admin/users", "icon": "UserFilled", "sort_order": 100},
    {"code": "admin_posts", "name": "岗亭管理", "description": "管理岗亭", "category": "管理", "path": "/admin/posts", "icon": "OfficeBuilding", "sort_order": 110},
    {"code": "admin_configs", "name": "系统配置", "description": "系统参数配置", "category": "管理", "path": "/admin/configs", "icon": "Tools", "sort_order": 120},
    {"code": "admin_role_modules", "name": "角色权限", "description": "配置角色可见的功能模块", "category": "管理", "path": "/admin/role-modules", "icon": "Lock", "sort_order": 130},
    {"code": "admin_vehicle_types", "name": "车辆类型", "description": "配置车辆类型及是否启用", "category": "管理", "path": "/admin/vehicle-types", "icon": "List", "sort_order": 140},
]


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(String(200), default="")
    category = Column(String(20), nullable=False, default="自定义")
    path = Column(String(100), nullable=False)
    icon = Column(String(50), default="Menu")
    sort_order = Column(Integer, nullable=False, default=999)
    is_builtin = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description or "",
            "category": self.category,
            "path": self.path,
            "icon": self.icon,
            "sort_order": self.sort_order,
            "is_builtin": self.is_builtin,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
