"""
文件上传 API（照片 + 自动水印）
"""
import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.models.post import Post
from app.config import settings
from app.utils.watermark import add_watermark, save_photo

router = APIRouter()


@router.post("/photo")
async def upload_photo(
    file: UploadFile = File(...),
    post_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传照片（自动加水印）"""
    # 校验类型
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail={"code": 400, "message": "只能上传图片"})

    # 读取
    content = await file.read()
    size_mb = len(content) / 1024 / 1024
    if size_mb > settings.photo_max_size_mb:
        raise HTTPException(status_code=400, detail={"code": 400, "message": f"图片不能超过 {settings.photo_max_size_mb}MB"})

    # 岗亭名
    post_name = ""
    if post_id:
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            post_name = post.name

    # 水印
    watermarked = add_watermark(
        content,
        time_str=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        post_name=post_name,
        operator_name=current_user.real_name,
    )

    # 保存
    rel_path = save_photo(watermarked)

    return {
        "code": 0,
        "message": "上传成功",
        "data": {
            "url": f"/photos/{rel_path}",
            "filename": os.path.basename(rel_path),
            "size": len(watermarked),
        },
    }
