"""
LAE v3.0 Scheduled Events API
支持完整的 v2.0 架构：name, domain_id, activity_type_id, schedule_id 字段
新增 v3.0 动态画布支持：duration, start_time, is_precise, canvas_position_y 字段
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, time
from pydantic import BaseModel, validator

from app.database import get_db
from app.models.models import ScheduledEvent, Domain, ActivityType, Schedule

router = APIRouter(prefix="/api/events", tags=["scheduled-events"])

# Pydantic schemas for v2.0 with v3.0 extensions
class ScheduledEventBase(BaseModel):
    event_date: date
    time_slot: int
    name: str
    notes: Optional[str] = None
    status: str = "planned"
    domain_id: Optional[int] = None
    activity_type_id: Optional[int] = None
    schedule_id: Optional[int] = None

    # V3.0 动态画布支持字段
    duration: Optional[int] = None  # 时长(分钟)
    start_time: Optional[time] = None  # 精确开始时间
    is_precise: bool = False  # 是否精确任务
    canvas_position_y: int = 0  # 画布Y坐标(并排摆放)

    @validator('duration')
    def validate_duration(cls, v):
        """验证时长必须为正数"""
        if v is not None and v <= 0:
            raise ValueError('Duration must be positive')
        return v

    # 暂时注释掉这个validator，稍后修复
    # @validator('start_time')
    # def validate_precise_time(cls, v, values):
    #     """验证精确任务必须有start_time"""
    #     if values.get('is_precise') and v is None:
    #         raise ValueError('Precise tasks must have start_time')
    #     return v

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

    # V3.0 动态画布支持字段
    duration: Optional[int] = None  # 时长(分钟)
    start_time: Optional[time] = None  # 精确开始时间
    is_precise: Optional[bool] = None  # 是否精确任务
    canvas_position_y: Optional[int] = None  # 画布Y坐标(并排摆放)

    @validator('duration')
    def validate_duration(cls, v):
        """验证时长必须为正数"""
        if v is not None and v <= 0:
            raise ValueError('Duration must be positive')
        return v

    # 暂时注释掉这个validator，稍后修复
    # @validator('start_time')
    # def validate_precise_time(cls, v, values):
    #     """验证精确任务必须有start_time"""
    #     if values.get('is_precise') and v is None:
    #         raise ValueError('Precise tasks must have start_time')
    #     return v

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

    # V3.0: 检查时间冲突 - 考虑并排摆放逻辑
    # 如果指定了canvas_position_y，允许并排摆放，不检查冲突
    if event.canvas_position_y == 0:  # 只有在主位置(Y=0)时才检查冲突
        existing = db.query(ScheduledEvent).filter(
            ScheduledEvent.event_date == event.event_date,
            ScheduledEvent.time_slot == event.time_slot,
            ScheduledEvent.canvas_position_y == 0  # 只检查主位置的冲突
        ).first()
        if existing:
            # 如果V3字段存在且支持并排，自动分配新的Y位置
            if hasattr(event, 'canvas_position_y'):
                # 找到下一个可用的Y位置
                max_y = db.query(ScheduledEvent).filter(
                    ScheduledEvent.event_date == event.event_date,
                    ScheduledEvent.time_slot == event.time_slot
                ).count()
                event.canvas_position_y = max_y
            else:
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

    # V3.0: 检查时间冲突 - 考虑并排摆放逻辑
    if "event_date" in update_data or "time_slot" in update_data or "canvas_position_y" in update_data:
        check_date = update_data.get("event_date", db_event.event_date)
        check_slot = update_data.get("time_slot", db_event.time_slot)
        check_y = update_data.get("canvas_position_y", getattr(db_event, 'canvas_position_y', 0))

        # 只有在主位置(Y=0)时才检查冲突
        if check_y == 0:
            existing = db.query(ScheduledEvent).filter(
                ScheduledEvent.id != event_id,
                ScheduledEvent.event_date == check_date,
                ScheduledEvent.time_slot == check_slot,
                ScheduledEvent.canvas_position_y == 0
            ).first()
            if existing:
                # 如果有冲突且支持V3并排摆放，自动分配新Y位置
                if "canvas_position_y" not in update_data:
                    max_y = db.query(ScheduledEvent).filter(
                        ScheduledEvent.id != event_id,
                        ScheduledEvent.event_date == check_date,
                        ScheduledEvent.time_slot == check_slot
                    ).count()
                    update_data["canvas_position_y"] = max_y
                else:
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