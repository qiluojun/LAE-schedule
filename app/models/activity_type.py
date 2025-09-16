from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class ActivityType(Base):
    __tablename__ = "activity_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("activity_types.id"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 层级关系 (支持类型层级化)
    parent = relationship("ActivityType", remote_side=[id], backref="children")

    # 关联到 scheduled_events
    scheduled_events = relationship("ScheduledEvent", back_populates="activity_type")