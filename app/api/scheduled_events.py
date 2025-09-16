"""
LAE v2.0 Scheduled Events API
支持新的 v2.0 架构：name, domain_id, activity_type_id, schedule_id 字段
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel

from app.database import get_db
from app.models.models import ScheduledEvent, Domain, ActivityType, Schedule

router = APIRouter(prefix="/api/events", tags=["scheduled-events"])

# Pydantic schemas for v2.0
class ScheduledEventBase(BaseModel):
    event_date: date
    time_slot: int
    name: str
    notes: Optional[str] = None
    status: str = "planned"
    domain_id: Optional[int] = None
    activity_type_id: Optional[int] = None
    schedule_id: Optional[int] = None

class ScheduledEventCreate(ScheduledEventBase):
    pass

class ScheduledEventUpdate(BaseModel):
    event_date: Optional[date] = None
    time_slot: Optional[int] = None
    name: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    domain_id: Optional[int] = None
    activity_type_id: Optional[int] = None
    schedule_id: Optional[int] = None

class ScheduledEventResponse(ScheduledEventBase):
    id: int

    class Config:
        from_attributes = True

class ScheduledEventWithDetails(ScheduledEventResponse):
    domain_name: Optional[str] = None
    activity_type_name: Optional[str] = None
    schedule_name: Optional[str] = None

# Valid time slots remain the same
VALID_TIME_SLOTS = [21, 22, 51, 52, 71]

@router.post("/", response_model=ScheduledEventResponse, status_code=status.HTTP_201_CREATED)
def create_scheduled_event(event: ScheduledEventCreate, db: Session = Depends(get_db)):
    """创建新的 scheduled event"""

    # 验证时间槽格式
    if event.time_slot not in VALID_TIME_SLOTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time_slot. Must be one of: {VALID_TIME_SLOTS}"
        )

    # 验证外键关系（如果提供）
    if event.domain_id:
        domain = db.query(Domain).filter(Domain.id == event.domain_id).first()
        if not domain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Domain with id {event.domain_id} not found"
            )

    if event.activity_type_id:
        activity_type = db.query(ActivityType).filter(ActivityType.id == event.activity_type_id).first()
        if not activity_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Activity type with id {event.activity_type_id} not found"
            )

    if event.schedule_id:
        schedule = db.query(Schedule).filter(Schedule.id == event.schedule_id).first()
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Schedule with id {event.schedule_id} not found"
            )

    # 检查同一时间槽是否已有安排
    existing = db.query(ScheduledEvent).filter(
        ScheduledEvent.event_date == event.event_date,
        ScheduledEvent.time_slot == event.time_slot
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time slot already occupied"
        )

    db_event = ScheduledEvent(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.get("/", response_model=List[ScheduledEventResponse])
def get_scheduled_events(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    domain_id: Optional[int] = None,
    activity_type_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取 scheduled events，支持多种过滤条件"""
    query = db.query(ScheduledEvent)

    if start_date:
        query = query.filter(ScheduledEvent.event_date >= start_date)
    if end_date:
        query = query.filter(ScheduledEvent.event_date <= end_date)
    if domain_id:
        query = query.filter(ScheduledEvent.domain_id == domain_id)
    if activity_type_id:
        query = query.filter(ScheduledEvent.activity_type_id == activity_type_id)
    if status:
        query = query.filter(ScheduledEvent.status == status)

    events = query.offset(skip).limit(limit).all()
    return events

@router.get("/with-details", response_model=List[ScheduledEventWithDetails])
def get_scheduled_events_with_details(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    domain_id: Optional[int] = None,
    activity_type_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取 scheduled events 并包含关联的详细信息"""
    query = db.query(
        ScheduledEvent,
        Domain.name.label('domain_name'),
        ActivityType.name.label('activity_type_name'),
        Schedule.name.label('schedule_name')
    ).outerjoin(Domain, ScheduledEvent.domain_id == Domain.id
    ).outerjoin(ActivityType, ScheduledEvent.activity_type_id == ActivityType.id
    ).outerjoin(Schedule, ScheduledEvent.schedule_id == Schedule.id)

    if start_date:
        query = query.filter(ScheduledEvent.event_date >= start_date)
    if end_date:
        query = query.filter(ScheduledEvent.event_date <= end_date)
    if domain_id:
        query = query.filter(ScheduledEvent.domain_id == domain_id)
    if activity_type_id:
        query = query.filter(ScheduledEvent.activity_type_id == activity_type_id)
    if status:
        query = query.filter(ScheduledEvent.status == status)

    results = query.offset(skip).limit(limit).all()

    return [
        ScheduledEventWithDetails(
            id=event.id,
            event_date=event.event_date,
            time_slot=event.time_slot,
            name=event.name,
            notes=event.notes,
            status=event.status,
            domain_id=event.domain_id,
            activity_type_id=event.activity_type_id,
            schedule_id=event.schedule_id,
            domain_name=domain_name,
            activity_type_name=activity_type_name,
            schedule_name=schedule_name
        )
        for event, domain_name, activity_type_name, schedule_name in results
    ]

@router.get("/{event_id}", response_model=ScheduledEventResponse)
def get_scheduled_event(event_id: int, db: Session = Depends(get_db)):
    """获取指定的 scheduled event"""
    event = db.query(ScheduledEvent).filter(ScheduledEvent.id == event_id).first()
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled event with id {event_id} not found"
        )
    return event

@router.put("/{event_id}", response_model=ScheduledEventResponse)
def update_scheduled_event(event_id: int, event_update: ScheduledEventUpdate, db: Session = Depends(get_db)):
    """更新指定的 scheduled event"""
    db_event = db.query(ScheduledEvent).filter(ScheduledEvent.id == event_id).first()
    if db_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled event with id {event_id} not found"
        )

    update_data = event_update.dict(exclude_unset=True)

    # 验证时间槽格式
    if "time_slot" in update_data:
        if update_data["time_slot"] not in VALID_TIME_SLOTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid time_slot. Must be one of: {VALID_TIME_SLOTS}"
            )

    # 验证外键关系
    if "domain_id" in update_data and update_data["domain_id"]:
        domain = db.query(Domain).filter(Domain.id == update_data["domain_id"]).first()
        if not domain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Domain with id {update_data['domain_id']} not found"
            )

    if "activity_type_id" in update_data and update_data["activity_type_id"]:
        activity_type = db.query(ActivityType).filter(ActivityType.id == update_data["activity_type_id"]).first()
        if not activity_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Activity type with id {update_data['activity_type_id']} not found"
            )

    if "schedule_id" in update_data and update_data["schedule_id"]:
        schedule = db.query(Schedule).filter(Schedule.id == update_data["schedule_id"]).first()
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Schedule with id {update_data['schedule_id']} not found"
            )

    # 检查时间冲突
    if "event_date" in update_data or "time_slot" in update_data:
        check_date = update_data.get("event_date", db_event.event_date)
        check_slot = update_data.get("time_slot", db_event.time_slot)

        existing = db.query(ScheduledEvent).filter(
            ScheduledEvent.id != event_id,
            ScheduledEvent.event_date == check_date,
            ScheduledEvent.time_slot == check_slot
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time slot already occupied"
            )

    for key, value in update_data.items():
        setattr(db_event, key, value)

    db.commit()
    db.refresh(db_event)
    return db_event

@router.delete("/{event_id}")
def delete_scheduled_event(event_id: int, db: Session = Depends(get_db)):
    """删除指定的 scheduled event"""
    db_event = db.query(ScheduledEvent).filter(ScheduledEvent.id == event_id).first()
    if db_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled event with id {event_id} not found"
        )

    db.delete(db_event)
    db.commit()
    return {"message": f"Scheduled event '{db_event.name}' deleted successfully"}