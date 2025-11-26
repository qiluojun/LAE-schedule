from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Time, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class ScheduledEvent(Base):
    __tablename__ = "scheduled_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_date = Column(Date, nullable=False, index=True)
    time_slot = Column(String(10), nullable=True)  # 改为可选，支持V3待定任务
    name = Column(String(255), nullable=False)  # 用户自定义的行动名称
    notes = Column(Text, nullable=True)  # 备注，不参与统计
    status = Column(String(50), default="planned")  # planned, completed

    # V1.0 兼容字段 (保持向后兼容)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=True)
    goal = Column(Text, nullable=True)  # 目标描述

    # V2.0 新架构的外键关系 (全部为可选)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=True)
    activity_type_id = Column(Integer, ForeignKey("activity_types.id"), nullable=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=True)

    # V3.0 动态画布支持字段
    duration = Column(Integer, nullable=True)  # 时长(分钟)，为兼容V2数据可为空
    start_time = Column(Time, nullable=True)  # 精确开始时间(可选)
    is_precise = Column(Boolean, default=False, nullable=False)  # 是否精确任务
    canvas_position_y = Column(Integer, default=0, nullable=False)  # 画布Y坐标(并排摆放)

    # V3.0 自由画布位置字段
    x = Column(Integer, nullable=True)  # 画布X坐标(像素)
    y = Column(Integer, nullable=True)  # 画布Y坐标(像素)

    # 关联关系
    activity = relationship("Activity", back_populates="scheduled_events")  # V1.0 兼容
    domain = relationship("Domain", back_populates="scheduled_events")
    activity_type = relationship("ActivityType", back_populates="scheduled_events")
    schedule = relationship("Schedule", back_populates="scheduled_events")

    def get_effective_duration(self):
        """获取有效时长 - V3支持实际时长，V2回退到默认时长"""
        if self.duration is not None:
            return self.duration
        # V2回退逻辑：根据time_slot估算默认时长
        return 60  # 默认60分钟

    def is_parallel_task(self):
        """判断是否为并行任务（Y坐标非0）"""
        return getattr(self, 'canvas_position_y', 0) > 0

    def get_display_time(self):
        """获取显示时间 - 精确任务显示具体时间，模糊任务显示时段"""
        if self.is_precise and self.start_time:
            return self.start_time.strftime("%H:%M")
        # 模糊任务根据time_slot显示时段名称
        time_slot_names = {
            21: "上午第1时段", 22: "上午第2时段",
            51: "下午第1时段", 52: "下午第2时段",
            71: "晚上时段"
        }
        return time_slot_names.get(self.time_slot, f"时段{self.time_slot}")

    def calculate_time_from_position(self):
        """根据卡片位置计算时间属性"""
        if self.x is None or self.y is None:
            return None, None

        # 计算日期偏移（基于X坐标）
        column_width = 150  # 每列宽度
        day_offset = int(self.x / column_width)

        # 计算时间（基于Y坐标）
        header_offset = 60  # 顶部偏移
        time_start_hour = 7  # 7:00开始
        pixels_per_hour = 60  # 每小时60像素

        if self.y < header_offset:
            return None, None

        # 计算距离7:00的分钟数
        minutes_from_start = int((self.y - header_offset) / pixels_per_hour * 60)

        # 转换为具体时间
        start_hour = time_start_hour + (minutes_from_start // 60)
        start_minute = minutes_from_start % 60

        # 如果是模糊任务，对齐到10分钟
        if not self.is_precise:
            start_minute = (start_minute // 10) * 10

        from datetime import time
        calculated_time = time(hour=start_hour, minute=start_minute)

        return day_offset, calculated_time

    def calculate_position_from_time(self):
        """根据时间属性计算卡片位置"""
        if not self.start_time:
            return None, None

        # 计算X坐标（基于日期）
        column_width = 150
        x = 0  # 默认第一列，实际应该基于event_date计算

        # 计算Y坐标（基于时间）
        header_offset = 60
        time_start_hour = 7
        pixels_per_hour = 60

        # 计算距离7:00的分钟数
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        base_minutes = time_start_hour * 60
        minutes_from_start = start_minutes - base_minutes

        if minutes_from_start < 0:
            minutes_from_start = 0

        y = header_offset + int(minutes_from_start * pixels_per_hour / 60)

        return x, y

    @classmethod
    def migrate_v2_to_v3(cls, v2_data):
        """V2数据迁移到V3的辅助方法"""
        v3_data = v2_data.copy()
        # 设置V3默认值
        v3_data.setdefault('duration', 60)  # 默认60分钟
        v3_data.setdefault('is_precise', False)
        v3_data.setdefault('canvas_position_y', 0)
        v3_data.setdefault('start_time', None)
        v3_data.setdefault('x', None)
        v3_data.setdefault('y', None)
        return v3_data