from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class ScheduledEvent(Base):
    __tablename__ = "scheduled_events"

    id = Column(Integer, primary_key=True, index=True)
    event_date = Column(Date, nullable=False, index=True)
    time_slot = Column(Integer, nullable=False)  # 21, 22, 51, 52, 71
    name = Column(String, nullable=False)  # 用户自定义的行动名称
    notes = Column(Text, nullable=True)  # 备注，不参与统计
    status = Column(String, default="planned")  # planned, completed

    # V1.0 兼容字段 (保持向后兼容)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=True)
    goal = Column(Text, nullable=True)  # 目标描述

    # V2.0 新架构的外键关系 (全部为可选)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=True)
    activity_type_id = Column(Integer, ForeignKey("activity_types.id"), nullable=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=True)

    # 关联关系
    activity = relationship("Activity", back_populates="scheduled_events")  # V1.0 兼容
    domain = relationship("Domain", back_populates="scheduled_events")
    activity_type = relationship("ActivityType", back_populates="scheduled_events")
    schedule = relationship("Schedule", back_populates="scheduled_events")