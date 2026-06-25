# 包标记 - 显式 import 触发模型注册
from app.models.user import User, UserRole  # noqa
from app.models.post import Post  # noqa
from app.models.record import Record, VehicleType, Direction, ApprovalStatus, RecordStatus  # noqa
from app.models.message import Message, MessageType  # noqa
from app.models.config import SystemConfig  # noqa
from app.models.report_config import ReportConfig  # noqa
from app.models.audit_log import AuditLog  # noqa
from app.models.role_module import RoleModule, DEFAULT_ROLE_MODULES, resolve_role_modules  # noqa
from app.models.module import Module, BUILTIN_MODULES  # noqa
