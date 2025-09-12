from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.database import get_db
from app.models.scheduled_event import ScheduledEvent as ScheduledEventModel
from app.models.activity import Activity as ActivityModel
from app.schemas import ScheduledEvent, ScheduledEventCreate, ScheduledEventUpdate, ScheduledEventWithActivity

router = APIRouter()

@router.post("/", response_model=ScheduledEvent)
def create_scheduled_event(event: ScheduledEventCreate, db: Session = Depends(get_db)):
    # 验证activity存在
    activity = db.query(ActivityModel).filter(ActivityModel.id == event.activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # 验证时间槽格式 (21, 22, 51, 52, 71)
    valid_slots = [21, 22, 51, 52, 71]
    if event.time_slot not in valid_slots:
        raise HTTPException(status_code=400, detail=f"Invalid time_slot. Must be one of: {valid_slots}")
    
    # 检查同一时间槽是否已有安排
    existing = db.query(ScheduledEventModel).filter(
        ScheduledEventModel.event_date == event.event_date,
        ScheduledEventModel.time_slot == event.time_slot
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Time slot already occupied")
    
    db_event = ScheduledEventModel(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.get("/", response_model=List[ScheduledEventWithActivity])
def get_scheduled_events(
    skip: int = 0, 
    limit: int = 100, 
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db)
):
    query = db.query(ScheduledEventModel)
    
    if start_date:
        query = query.filter(ScheduledEventModel.event_date >= start_date)
    if end_date:
        query = query.filter(ScheduledEventModel.event_date <= end_date)
    
    events = query.offset(skip).limit(limit).all()
    return events

@router.get("/{event_id}", response_model=ScheduledEventWithActivity)
def get_scheduled_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(ScheduledEventModel).filter(ScheduledEventModel.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Scheduled event not found")
    return event

@router.put("/{event_id}", response_model=ScheduledEvent)
def update_scheduled_event(event_id: int, event: ScheduledEventUpdate, db: Session = Depends(get_db)):
    db_event = db.query(ScheduledEventModel).filter(ScheduledEventModel.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Scheduled event not found")
    
    update_data = event.dict(exclude_unset=True)
    
    # 验证activity存在
    if "activity_id" in update_data:
        activity = db.query(ActivityModel).filter(ActivityModel.id == update_data["activity_id"]).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
    
    # 验证时间槽格式
    if "time_slot" in update_data:
        valid_slots = [21, 22, 51, 52, 71]
        if update_data["time_slot"] not in valid_slots:
            raise HTTPException(status_code=400, detail=f"Invalid time_slot. Must be one of: {valid_slots}")
    
    # 检查时间冲突
    if "event_date" in update_data or "time_slot" in update_data:
        check_date = update_data.get("event_date", db_event.event_date)
        check_slot = update_data.get("time_slot", db_event.time_slot)
        
        existing = db.query(ScheduledEventModel).filter(
            ScheduledEventModel.id != event_id,
            ScheduledEventModel.event_date == check_date,
            ScheduledEventModel.time_slot == check_slot
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Time slot already occupied")
    
    for key, value in update_data.items():
        setattr(db_event, key, value)
    
    db.commit()
    db.refresh(db_event)
    return db_event

@router.delete("/{event_id}")
def delete_scheduled_event(event_id: int, db: Session = Depends(get_db)):
    db_event = db.query(ScheduledEventModel).filter(ScheduledEventModel.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Scheduled event not found")
    
    db.delete(db_event)
    db.commit()
    return {"message": "Scheduled event deleted successfully"}