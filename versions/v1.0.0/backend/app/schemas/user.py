"""
用户管理 schemas
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=50)
    real_name: str = Field(..., max_length=50)
    role: Literal["security", "supervisor", "approver", "admin"]
    post_id: Optional[int] = None
    is_approver: bool = False
    phone: Optional[str] = None
    email: Optional[str] = None


class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    role: Optional[Literal["security", "supervisor", "approver", "admin"]] = None
    post_id: Optional[int] = None
    is_approver: Optional[bool] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordReset(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=50)
