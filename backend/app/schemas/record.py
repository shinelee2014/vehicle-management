"""
记录相关 schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class PhotoItem(BaseModel):
    kind: Literal["front", "plate", "side", "other"]  # 车前/车牌/侧面/其他
    url: str
    watermark: Optional[str] = None


class RecordCreateIn(BaseModel):
    """进场登记"""
    plate_number: str = Field(..., max_length=20)
    vehicle_type: str = Field(..., max_length=50)
    post_id: int
    approver_id: int
    in_remark: Optional[str] = None
    cargo_info: Optional[str] = None  # 货车专属
    photos: List[PhotoItem] = Field(..., min_length=1, max_length=5)


class RecordCreateOut(BaseModel):
    """出场登记"""
    related_record_id: Optional[int] = None  # 关联进记录（扫码或搜车牌时）
    plate_number: str = Field(..., max_length=20)
    post_id: int
    approver_id: int
    out_remark: Optional[str] = None
    photos: List[PhotoItem] = Field(..., min_length=1, max_length=5)


class ApprovalRequest(BaseModel):
    """审批操作"""
    action: Literal["approve", "reject"]
    remark: Optional[str] = None


class RecordQuery(BaseModel):
    """记录查询条件"""
    page: int = 1
    page_size: int = 20
    plate_number: Optional[str] = None
    post_id: Optional[int] = None
    vehicle_type: Optional[str] = None
    approval_status: Optional[Literal["pending", "approved", "rejected", "timeout"]] = None
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None
