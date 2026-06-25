"""
进出记录 ORM 模型（核心）
"""
from datetime import datetime
import enum
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


class VehicleType(str, enum.Enum):
    """车辆类型枚举 - 值与数据库 ENUM 一致（小写）"""
    INTERNAL = "internal"
    EXTERNAL = "external"
    TRUCK = "truck"


class Direction(str, enum.Enum):
    """进出方向枚举"""
    IN = "in"
    OUT = "out"


class ApprovalStatus(str, enum.Enum):
    """审批状态枚举"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class RecordStatus(str, enum.Enum):
    """记录状态枚举"""
    IN_PENDING = "in_pending"
    IN_APPROVED = "in_approved"
    IN_REJECTED = "in_rejected"
    IN_TIMEOUT = "in_timeout"
    OUT_PENDING = "out_pending"
    OUT_APPROVED = "out_approved"
    OUT_REJECTED = "out_rejected"
    OUT_TIMEOUT = "out_timeout"
    COMPLETED = "completed"


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_no = Column(String(30), unique=True, nullable=False)
    plate_number = Column(String(20), nullable=False, index=True)
    # 用 String 而非 Enum，避免 MySQL ENUM 与 Python enum 映射冲突
    vehicle_type = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    operator_name = Column(String(50), nullable=False)

    # 进场
    in_time = Column(DateTime, index=True)
    in_photos = Column(JSON)
    in_remark = Column(Text)

    # 出场
    out_time = Column(DateTime, index=True)
    out_photos = Column(JSON)
    out_remark = Column(Text)

    # 货车
    cargo_info = Column(String(500))
    loading_start_at = Column(DateTime)
    loading_end_at = Column(DateTime)
    loading_duration = Column(Integer)

    # 审批
    approver_id = Column(Integer, ForeignKey("users.id"), index=True)
    approver_name = Column(String(50))
    approval_status = Column(String(20), nullable=False, default=ApprovalStatus.PENDING.value)
    approval_time = Column(DateTime)
    approval_remark = Column(Text)

    # 关联
    related_record_id = Column(Integer, ForeignKey("records.id"))
    companion_id = Column(Integer, ForeignKey("records.id"))

    # 状态
    status = Column(String(20), nullable=False, default=RecordStatus.IN_PENDING.value)

    # 通用
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    archived_at = Column(DateTime)

    # 软删除（admin 批量删除时使用，不真删数据，列表默认隐藏）
    is_deleted = Column(Integer, nullable=False, default=0, index=True)
    deleted_at = Column(DateTime)
    deleted_by = Column(Integer)
    deleted_by_name = Column(String(50))
    deleted_reason = Column(String(200))

    def to_dict(self, include_related: bool = False) -> dict:
        data = {
            "id": self.id,
            "record_no": self.record_no,
            "plate_number": self.plate_number,
            "vehicle_type": self.vehicle_type.value if isinstance(self.vehicle_type, VehicleType) else self.vehicle_type,
            "direction": self.direction.value if isinstance(self.direction, Direction) else self.direction,
            "post_id": self.post_id,
            "operator_id": self.operator_id,
            "operator_name": self.operator_name,
            "in_time": self.in_time.isoformat() if self.in_time else None,
            "in_photos": self.in_photos or [],
            "in_remark": self.in_remark,
            "out_time": self.out_time.isoformat() if self.out_time else None,
            "out_photos": self.out_photos or [],
            "out_remark": self.out_remark,
            "cargo_info": self.cargo_info,
            "loading_start_at": self.loading_start_at.isoformat() if self.loading_start_at else None,
            "loading_end_at": self.loading_end_at.isoformat() if self.loading_end_at else None,
            "loading_duration": self.loading_duration,
            "approver_id": self.approver_id,
            "approver_name": self.approver_name,
            "approval_status": self.approval_status.value if isinstance(self.approval_status, ApprovalStatus) else self.approval_status,
            "approval_time": self.approval_time.isoformat() if self.approval_time else None,
            "approval_remark": self.approval_remark,
            "related_record_id": self.related_record_id,
            "companion_id": self.companion_id,
            "status": self.status.value if isinstance(self.status, RecordStatus) else self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_deleted": bool(self.is_deleted) if self.is_deleted is not None else False,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by_name": self.deleted_by_name,
            "deleted_reason": self.deleted_reason,
        }
        return data
