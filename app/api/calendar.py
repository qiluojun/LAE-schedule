from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Dict
from datetime import date, datetime, timedelta
from collections import defaultdict

from app.database import get_db
from app.models.scheduled_event import ScheduledEvent as ScheduledEventModel
from app.models.activity import Activity as ActivityModel
from app.models.schedule import Schedule as ScheduleModel
from app.schemas import ScheduledEventWithActivity

router = APIRouter()

def get_week_dates(target_date: date):
    """获取指定日期所在周的7天日期"""
    days_since_monday = target_date.weekday()
    monday = target_date - timedelta(days=days_since_monday)
    return [monday + timedelta(days=i) for i in range(7)]

def get_month_dates(year: int, month: int):
    """获取指定月份的所有日期"""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Invalid month")
    
    first_day = date(year, month, 1)
    if month == 12:
        next_month_first = date(year + 1, 1, 1)
    else:
        next_month_first = date(year, month + 1, 1)
    
    dates = []
    current_date = first_day
    while current_date < next_month_first:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    return dates

@router.get("/week/{target_date}")
def get_week_schedule(target_date: date, db: Session = Depends(get_db)):
    """获取指定日期所在周的完整日程"""
    week_dates = get_week_dates(target_date)
    start_date = week_dates[0]
    end_date = week_dates[6]
    
    events = db.query(ScheduledEventModel).filter(
        ScheduledEventModel.event_date >= start_date,
        ScheduledEventModel.event_date <= end_date
    ).all()
    
    # 组织数据为周视图格式
    schedule_grid = {}
    time_slots = [21, 22, 51, 52, 71]
    
    for day in week_dates:
        schedule_grid[day.isoformat()] = {
            "date": day.isoformat(),
            "weekday": day.strftime("%A"),
            "slots": {}
        }
        for slot in time_slots:
            schedule_grid[day.isoformat()]["slots"][slot] = None
    
    # 填入实际事件
    for event in events:
        day_key = event.event_date.isoformat()
        if day_key in schedule_grid:
            schedule_grid[day_key]["slots"][event.time_slot] = {
                "id": event.id,
                "activity_id": event.activity_id,
                "activity_name": event.activity.name if event.activity else None,
                "name": getattr(event, 'name', None),  # v2.1 新字段
                "domain_id": getattr(event, 'domain_id', None),  # v2.1 新字段
                "activity_type_id": getattr(event, 'activity_type_id', None),  # v2.1 新字段
                "schedule_id": getattr(event, 'schedule_id', None),  # v2.1 新字段
                "goal": event.goal,
                "notes": event.notes,
                "status": event.status
            }
    
    return {
        "week_start": start_date.isoformat(),
        "week_end": end_date.isoformat(),
        "schedule": list(schedule_grid.values())
    }

@router.get("/month/{year}/{month}")
def get_month_schedule(year: int, month: int, db: Session = Depends(get_db)):
    """获取指定月份的日程概览"""
    month_dates = get_month_dates(year, month)
    start_date = month_dates[0]
    end_date = month_dates[-1]

    # 获取事件数据
    events = db.query(ScheduledEventModel).filter(
        ScheduledEventModel.event_date >= start_date,
        ScheduledEventModel.event_date <= end_date
    ).all()

    # 获取跨越该月的Schedule数据 (暂时注释以确保基本功能可用)
    try:
        schedules = db.query(ScheduleModel).filter(
            or_(
                and_(ScheduleModel.start_date != None, ScheduleModel.start_date <= end_date),
                and_(ScheduleModel.deadline != None, ScheduleModel.deadline >= start_date)
            )
        ).all()
    except Exception as e:
        print(f"Schedule查询出错: {e}")
        schedules = []  # 如果Schedule查询失败，继续使用空列表
    
    # 按日期聚合事件
    daily_events = defaultdict(list)
    for event in events:
        daily_events[event.event_date.isoformat()].append({
            "id": event.id,
            "activity_id": event.activity_id,
            "activity_name": event.activity.name if event.activity else "未知活动",
            "name": getattr(event, 'name', None),  # v2.1 新字段
            "domain_id": getattr(event, 'domain_id', None),  # v2.1 新字段
            "activity_type_id": getattr(event, 'activity_type_id', None),  # v2.1 新字段
            "schedule_id": getattr(event, 'schedule_id', None),  # v2.1 新字段
            "time_slot": event.time_slot,
            "goal": event.goal,
            "notes": event.notes,
            "status": event.status
        })
    
    # 构建月视图数据
    schedule_data = []
    for day in month_dates:
        day_key = day.isoformat()
        events_for_day = daily_events.get(day_key, [])
        schedule_data.append({
            "date": day_key,
            "weekday": day.strftime("%A"),
            "day": day.day,
            "event_count": len(events_for_day),
            "events": events_for_day,
            "is_today": day == date.today()
        })
    
    # 处理Schedule数据
    schedule_list = []
    for schedule in schedules:
        schedule_data_item = {
            "id": schedule.id,
            "name": schedule.name,
            "description": schedule.description,
            "start_date": schedule.start_date.isoformat() if schedule.start_date else None,
            "deadline": schedule.deadline.isoformat() if schedule.deadline else None,
            "status": schedule.status,
            "domain_id": schedule.domain_id
        }
        schedule_list.append(schedule_data_item)

    return {
        "year": year,
        "month": month,
        "month_name": datetime(year, month, 1).strftime("%B"),
        "days": schedule_data,  # 前端期望的字段名
        "schedule": schedule_data,  # 保持兼容性
        "schedules": schedule_list  # Schedule时间条数据
    }

@router.get("/day/{target_date}")
def get_day_schedule(target_date: date, db: Session = Depends(get_db)):
    """获取指定日期的详细日程"""
    events = db.query(ScheduledEventModel).filter(
        ScheduledEventModel.event_date == target_date
    ).all()
    
    # 组织为时间槽格式
    time_slots = [21, 22, 51, 52, 71]
    slot_names = {
        21: "上午第1时段",
        22: "上午第2时段", 
        51: "下午第1时段",
        52: "下午第2时段",
        71: "晚上时段"
    }
    
    day_schedule = {}
    for slot in time_slots:
        day_schedule[slot] = {
            "time_slot": slot,
            "slot_name": slot_names[slot],
            "event": None
        }
    
    for event in events:
        if event.time_slot in day_schedule:
            day_schedule[event.time_slot]["event"] = {
                "id": event.id,
                "activity_id": event.activity_id,
                "activity_name": event.activity.name,
                "goal": event.goal,
                "notes": event.notes,
                "status": event.status
            }
    
    return {
        "date": target_date.isoformat(),
        "weekday": target_date.strftime("%A"),
        "schedule": list(day_schedule.values())
    }