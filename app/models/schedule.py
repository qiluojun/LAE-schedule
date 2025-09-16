from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)  # 强制关联到 domain
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)  # 起始日期
    deadline = Column(DateTime(timezone=True), nullable=True)  # 截止日期
    status = Column(String, default="ongoing", index=True)  # ongoing, completed, paused
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    domain = relationship("Domain", back_populates="schedules")
    scheduled_events = relationship("ScheduledEvent", back_populates="schedule")