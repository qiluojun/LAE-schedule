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
    time_slot: Optional[str] = None  # 改为字符串且可选 (V3 待定任务支持)
    name: str
    notes: Optional[str] = None
    status: str = "planned"
    domain_id: Optional[int] = None
    activity_type_id: Optional[int] = None
    schedule_id: Optional[int] = None
    goal: Optional[str] = None  # V1.0 兼容字段

    # V3.0 动态画布支持字段
    duration: Optional[int] = None  # 时长(分钟)
    start_time: Optional[time] = None  # 精确开始时间
    is_precise: bool = False  # 是否精确任务
    canvas_position_y: int = 0  # 画布Y坐标(并排摆放)

    # V3.0 自由画布位置字段
    x: Optional[int] = None  # 画布X坐标(像素)
    y: Optional[int] = None  # 画布Y坐标(像素)

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
    time_slot: Optional[str] = None  # 改为字符串类型
    name: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    domain_id: Optional[int] = None
    activity_type_id: Optional[int] = None
    schedule_id: Optional[int] = None
    goal: Optional[str] = None  # V1.0 兼容字段

    # V3.0 动态画布支持字段
    duration: Optional[int] = None  # 时长(分钟)
    start_time: Optional[time] = None  # 精确开始时间
    is_precise: Optional[bool] = None  # 是否精确任务
    canvas_position_y: Optional[int] = None  # 画布Y坐标(并排摆放)

    # V3.0 自由画布位置字段
    x: Optional[int] = None  # 画布X坐标(像素)
    y: Optional[int] = None  # 画布Y坐标(像素)

    @validator('duration')
    def validate_duration(cls, v):
        """验证时长必须为正数，0值自动修正为默认值"""
        if v is not None and v <= 0:
            # 对于0或负值，返回默认的60分钟而不是抛出错误
            return 60
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

# Valid time slots - 改为字符串列表以匹配数据库类型
VALID_TIME_SLOTS = ["21", "22", "51", "52", "71"]

@router.post("/", response_model=ScheduledEventResponse, status_code=status.HTTP_201_CREATED)
def create_scheduled_event(event: ScheduledEventCreate, db: Session = Depends(get_db)):
    """创建新的 scheduled event"""

    # 验证时间槽格式 (允许 null 用于待定任务)
    if event.time_slot is not None and event.time_slot not in VALID_TIME_SLOTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time_slot. Must be one of: {VALID_TIME_SLOTS} or null for pending tasks"
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
    # 待定任务 (time_slot 为 null) 不检查冲突
    if event.time_slot is not None and event.canvas_position_y == 0:
        # 只有在主位置(Y=0)时才检查冲突
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
    # Debug logging (Unicode safe)
    print(f"DEBUG: Updating event {event_id}")
    try:
        update_dict = event_update.dict(exclude_unset=True)
        # 安全的Unicode处理
        safe_dict = {}
        for k, v in update_dict.items():
            if isinstance(v, str):
                safe_dict[k] = repr(v)  # 使用repr避免Unicode问题
            else:
                safe_dict[k] = v
        print(f"DEBUG: Update data received: {safe_dict}")
    except UnicodeEncodeError as e:
        print(f"DEBUG: Unicode encoding error in data display: {e}")
        print("DEBUG: Update data received (raw keys):", list(event_update.dict(exclude_unset=True).keys()))

    db_event = db.query(ScheduledEvent).filter(ScheduledEvent.id == event_id).first()
    if db_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled event with id {event_id} not found"
        )

    # 安全的Unicode处理
    try:
        safe_name = repr(db_event.name) if db_event.name else 'None'
        print(f"DEBUG: Original event: name={safe_name}, domain_id={db_event.domain_id}")
    except UnicodeEncodeError:
        print(f"DEBUG: Original event: name=[Unicode], domain_id={db_event.domain_id}")

    try:
        # 先安全获取update_data
        update_data = {}
        raw_data = event_update.dict(exclude_unset=True)

        # 处理每个字段，确保Unicode安全
        for k, v in raw_data.items():
            update_data[k] = v

        print(f"DEBUG: Successfully processed {len(update_data)} fields")

        # 安全显示update_data（用于调试）
        safe_update = {}
        for k, v in update_data.items():
            if isinstance(v, str):
                safe_update[k] = f"[String:{len(v)}chars]"  # 避免显示实际Unicode内容
            else:
                safe_update[k] = v
        print(f"DEBUG: Processed update data types: {safe_update}")

    except UnicodeEncodeError as ue:
        print(f"DEBUG: Unicode encoding error, but processing continues: {ue}")
        # 即使有Unicode编码错误，我们仍然可以继续处理数据
        try:
            update_data = event_update.dict(exclude_unset=True)
            print(f"DEBUG: Data processed despite encoding error, {len(update_data)} fields")
        except Exception as fallback_e:
            print(f"ERROR: Complete failure processing update data: {fallback_e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to process update data due to encoding issues"
            )
    except Exception as e:
        print(f"ERROR: Error processing update data: [Exception details suppressed to avoid encoding issues]")
        print(f"ERROR: Exception type: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid update data: encoding error"
        )

    # 验证时间槽格式 (允许 null 用于待定任务)
    try:
        if "time_slot" in update_data:
            print(f"DEBUG: Validating time_slot: {update_data['time_slot']}")
            if update_data["time_slot"] is not None and update_data["time_slot"] not in VALID_TIME_SLOTS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid time_slot. Must be one of: {VALID_TIME_SLOTS} or null for pending tasks"
                )
        print("DEBUG: Time slot validation passed")
    except Exception as e:
        print(f"ERROR: Time slot validation error: {e}")
        raise

    # 验证外键关系 - 宽松模式，不存在的引用会被置空而不是报错
    if "domain_id" in update_data and update_data["domain_id"]:
        domain = db.query(Domain).filter(Domain.id == update_data["domain_id"]).first()
        if not domain:
            # 对于旧卡片兼容性，将不存在的引用置空而不是抛出错误
            print(f"WARNING: Domain with id {update_data['domain_id']} not found, setting to null")
            update_data["domain_id"] = None

    if "activity_type_id" in update_data and update_data["activity_type_id"]:
        activity_type = db.query(ActivityType).filter(ActivityType.id == update_data["activity_type_id"]).first()
        if not activity_type:
            # 对于旧卡片兼容性，将不存在的引用置空而不是抛出错误
            print(f"WARNING: Activity type with id {update_data['activity_type_id']} not found, setting to null")
            update_data["activity_type_id"] = None

    if "schedule_id" in update_data and update_data["schedule_id"]:
        schedule = db.query(Schedule).filter(Schedule.id == update_data["schedule_id"]).first()
        if not schedule:
            # 对于旧卡片兼容性，将不存在的引用置空而不是抛出错误
            print(f"WARNING: Schedule with id {update_data['schedule_id']} not found, setting to null")
            update_data["schedule_id"] = None

    # V3.0: 检查时间冲突 - 考虑并排摆放逻辑
    try:
        if "event_date" in update_data or "time_slot" in update_data or "canvas_position_y" in update_data:
            print("DEBUG: Checking time conflict...")
            check_date = update_data.get("event_date", db_event.event_date)
            check_slot = update_data.get("time_slot", db_event.time_slot)

            # 安全获取canvas_position_y，对旧记录兼容处理
            try:
                old_canvas_y = getattr(db_event, 'canvas_position_y', 0)
            except AttributeError:
                old_canvas_y = 0
            check_y = update_data.get("canvas_position_y", old_canvas_y)

            print(f"DEBUG: Conflict check params: date={check_date}, slot={check_slot}, y={check_y}")

            # 待定任务 (time_slot 为 null) 不检查冲突
            # 只有在主位置(Y=0)且有时间槽时才检查冲突
            if check_slot is not None and check_y == 0:
                existing = db.query(ScheduledEvent).filter(
                    ScheduledEvent.id != event_id,
                    ScheduledEvent.event_date == check_date,
                    ScheduledEvent.time_slot == check_slot,
                    ScheduledEvent.canvas_position_y == 0
                ).first()
                if existing:
                    print(f"DEBUG: Found conflict with event {existing.id}")
                    # V3自由画布：自动分配新的Y位置以支持并排摆放
                    # 检查当前请求是否要求Y=0位置
                    if update_data.get("canvas_position_y", 0) == 0:
                        # 查找该时间槽的最大Y位置并分配下一个
                        max_y_result = db.query(ScheduledEvent.canvas_position_y).filter(
                            ScheduledEvent.id != event_id,
                            ScheduledEvent.event_date == check_date,
                            ScheduledEvent.time_slot == check_slot
                        ).all()

                        existing_y_positions = [row[0] for row in max_y_result if row[0] is not None]
                        next_y = max(existing_y_positions, default=-1) + 1

                        update_data["canvas_position_y"] = next_y
                        print(f"DEBUG: Auto-assigned canvas_position_y = {next_y} (existing positions: {existing_y_positions})")
                    else:
                        print(f"DEBUG: Requested specific Y position: {update_data['canvas_position_y']}")
                        # 检查具体Y位置是否被占用
                        y_conflict = db.query(ScheduledEvent).filter(
                            ScheduledEvent.id != event_id,
                            ScheduledEvent.event_date == check_date,
                            ScheduledEvent.time_slot == check_slot,
                            ScheduledEvent.canvas_position_y == update_data["canvas_position_y"]
                        ).first()
                        if y_conflict:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Position already occupied by event {y_conflict.id}"
                            )
                else:
                    print("DEBUG: No time conflict found")
            else:
                print("DEBUG: Non-zero canvas_position_y, skipping conflict check")
        print("DEBUG: Time conflict check completed")
    except Exception as e:
        print(f"ERROR: Time conflict check error: [Exception suppressed to avoid encoding issues]")
        print(f"ERROR: Exception type: {type(e).__name__}")
        raise

    try:
        print(f"DEBUG: Applying updates to {len(update_data)} fields")
        for key, value in update_data.items():
            setattr(db_event, key, value)

        print("DEBUG: Committing to database...")
        db.commit()
        db.refresh(db_event)
        print(f"DEBUG: Event {event_id} updated successfully")
        return db_event
    except Exception as e:
        print(f"ERROR: Database update error: [Exception suppressed to avoid encoding issues]")
        print(f"ERROR: Exception type: {type(e).__name__}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database update failed: encoding error"
        )

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