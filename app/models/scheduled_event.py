from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class ScheduledEvent(Base):
    __tablename__ = "scheduled_events"
    
    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    event_date = Column(Date, nullable=False, index=True)
    time_slot = Column(Integer, nullable=False)  # 21, 22, 51, 52, 71
    goal = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)  # 备注，不参与统计
    status = Column(String, default="planned")  # planned, completed
    
    activity = relationship("Activity", back_populates="scheduled_events")