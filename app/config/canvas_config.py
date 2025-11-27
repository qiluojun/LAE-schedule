"""
画布配置文件
用于记录PC端的标准画布尺寸，以便移动端进行等比例缩放
"""

# PC端标准画布尺寸（基准尺寸）
PC_CANVAS_CONFIG = {
    "canvas_width": 1050,      # PC端画布总宽度
    "canvas_height": 960,      # PC端画布总高度
    "time_axis_width": 80,     # 时间轴宽度
    "header_height": 60,       # 头部高度

    # 计算得出的可用区域
    "available_width": 970,    # 1050 - 80
    "available_height": 900,   # 960 - 60
}

def get_pc_canvas_config():
    """获取PC端画布配置"""
    return PC_CANVAS_CONFIG
