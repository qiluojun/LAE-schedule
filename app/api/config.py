"""配置 API 端点"""
from fastapi import APIRouter
from app.config.canvas_config import get_pc_canvas_config

router = APIRouter(prefix="/api/config", tags=["config"])

@router.get("/canvas")
async def get_canvas_config():
    """
    获取PC端画布配置（用于移动端缩放计算）

    Returns:
        dict: PC端画布配置信息
    """
    return get_pc_canvas_config()
