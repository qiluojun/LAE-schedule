from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List

class ActivityBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None

class Activity(ActivityBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ActivityWithChildren(Activity):
    children: List['Activity'] = []

class ScheduledEventBase(BaseModel):
    activity_id: int
    event_date: date
    time_slot: int
    goal: Optional[str] = None
    notes: Optional[str] = None
    status: str = "planned"

class ScheduledEventCreate(ScheduledEventBase):
    pass

class ScheduledEventUpdate(BaseModel):
    activity_id: Optional[int] = None
    event_date: Optional[date] = None
    time_slot: Optional[int] = None
    goal: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class ScheduledEvent(ScheduledEventBase):
    id: int
    
    class Config:
        from_attributes = True

class ScheduledEventWithActivity(ScheduledEvent):
    activity: Activity

ActivityWithChildren.model_rebuild()