"""
LAE v2.0 Schedules API
基础的 schedule 管理 CRUD 操作
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import Schedule, Domain
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/schedules", tags=["schedules"])

# Pydantic schemas
class ScheduleBase(BaseModel):
    domain_id: int
    name: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    status: str = "ongoing"

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = None

class ScheduleResponse(ScheduleBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}

class ScheduleWithDomain(ScheduleResponse):
    domain_name: str

@router.get("/", response_model=List[ScheduleResponse])
def list_schedules(
    domain_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取所有 schedules，支持按 domain、status 和日期范围过滤"""
    query = db.query(Schedule)

    if domain_id:
        query = query.filter(Schedule.domain_id == domain_id)

    if status:
        query = query.filter(Schedule.status == status)

    # 日期范围过滤：查找跨越指定时间段的Schedule
    if start_date and end_date:
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # 查找与指定时间段有重叠的Schedule
        # 条件：Schedule的start_date <= end_dt 且 Schedule的deadline >= start_dt
        from sqlalchemy import or_, and_
        query = query.filter(
            or_(
                # Schedule没有start_date但有deadline，且deadline在范围内
                and_(Schedule.start_date.is_(None), Schedule.deadline >= start_dt),
                # Schedule有start_date，检查时间重叠
                and_(
                    Schedule.start_date <= end_dt,
                    or_(
                        Schedule.deadline.is_(None),  # 没有deadline的Schedule
                        Schedule.deadline >= start_dt  # 有deadline且在范围内
                    )
                )
            )
        )

    schedules = query.all()
    return schedules

@router.get("/with-domains", response_model=List[ScheduleWithDomain])
def list_schedules_with_domains(
    domain_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取 schedules 并包含 domain 信息"""
    query = db.query(Schedule, Domain.name.label('domain_name')).join(Domain)

    if domain_id:
        query = query.filter(Schedule.domain_id == domain_id)

    if status:
        query = query.filter(Schedule.status == status)

    results = query.all()

    return [
        ScheduleWithDomain(
            id=schedule.id,
            domain_id=schedule.domain_id,
            name=schedule.name,
            description=schedule.description,
            deadline=schedule.deadline,
            status=schedule.status,
            created_at=schedule.created_at,
            domain_name=domain_name
        )
        for schedule, domain_name in results
    ]

@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """获取指定 schedule"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with id {schedule_id} not found"
        )
    return schedule

@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    """创建新 schedule"""

    # 验证 domain_id 是否存在
    domain = db.query(Domain).filter(Domain.id == schedule.domain_id).first()
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Domain with id {schedule.domain_id} not found"
        )

    db_schedule = Schedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)

    return db_schedule

@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(schedule_id: int, schedule_update: ScheduleUpdate, db: Session = Depends(get_db)):
    """更新指定 schedule"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with id {schedule_id} not found"
        )

    # 更新字段
    update_data = schedule_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)

    db.commit()
    db.refresh(schedule)

    return schedule

@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """删除指定 schedule"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with id {schedule_id} not found"
        )

    db.delete(schedule)
    db.commit()

    return {"message": f"Schedule '{schedule.name}' deleted successfully"}