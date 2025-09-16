from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("domains.id"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 层级关系
    parent = relationship("Domain", remote_side=[id], backref="children")

    # 关联到 schedules 和 scheduled_events
    schedules = relationship("Schedule", back_populates="domain", cascade="all, delete-orphan")
    scheduled_events = relationship("ScheduledEvent", back_populates="domain")