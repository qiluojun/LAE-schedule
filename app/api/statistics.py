from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from collections import defaultdict

from app.database import get_db
from app.models.activity import Activity as ActivityModel
from app.models.scheduled_event import ScheduledEvent as ScheduledEventModel

router = APIRouter()

def get_activity_descendants(db: Session, activity_id: int):
    """递归获取活动的所有子活动ID"""
    descendants = set()
    
    def collect_children(parent_id):
        children = db.query(ActivityModel).filter(ActivityModel.parent_id == parent_id).all()
        for child in children:
            descendants.add(child.id)
            collect_children(child.id)
    
    collect_children(activity_id)
    return descendants

@router.get("/summary")
def get_summary_statistics(db: Session = Depends(get_db)):
    """获取系统总体统计信息"""
    total_activities = db.query(ActivityModel).count()
    total_events = db.query(ScheduledEventModel).count()
    completed_events = db.query(ScheduledEventModel).filter(
        ScheduledEventModel.status == "completed"
    ).count()
    
    # 按状态统计
    status_stats = db.query(
        ScheduledEventModel.status,
        func.count(ScheduledEventModel.id).label('count')
    ).group_by(ScheduledEventModel.status).all()
    
    # 按时间槽统计
    timeslot_stats = db.query(
        ScheduledEventModel.time_slot,
        func.count(ScheduledEventModel.id).label('count')
    ).group_by(ScheduledEventModel.time_slot).all()
    
    slot_names = {
        21: "上午第1时段",
        22: "上午第2时段", 
        51: "下午第1时段",
        52: "下午第2时段",
        71: "晚上时段"
    }
    
    return {
        "total_activities": total_activities,
        "total_events": total_events,
        "completed_events": completed_events,
        "completion_rate": round(completed_events / total_events * 100, 2) if total_events > 0 else 0,
        "status_distribution": [
            {"status": status, "count": count} for status, count in status_stats
        ],
        "timeslot_distribution": [
            {
                "time_slot": slot,
                "slot_name": slot_names.get(slot, f"时段{slot}"),
                "count": count
            } for slot, count in timeslot_stats
        ]
    }

@router.get("/activities/{activity_id}/statistics")
def get_activity_statistics(activity_id: int, db: Session = Depends(get_db)):
    """获取指定活动（包含子活动）的统计信息"""
    # 验证活动存在
    activity = db.query(ActivityModel).filter(ActivityModel.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # 获取该活动及其所有子活动的ID
    target_ids = {activity_id}
    target_ids.update(get_activity_descendants(db, activity_id))
    
    # 统计相关事件
    events = db.query(ScheduledEventModel).filter(
        ScheduledEventModel.activity_id.in_(target_ids)
    ).all()
    
    total_events = len(events)
    completed_events = sum(1 for event in events if event.status == "completed")
    
    # 按子活动分组统计
    activity_stats = defaultdict(lambda: {"total": 0, "completed": 0, "goals": []})
    
    for event in events:
        activity_name = db.query(ActivityModel).filter(ActivityModel.id == event.activity_id).first().name
        activity_stats[activity_name]["total"] += 1
        if event.status == "completed":
            activity_stats[activity_name]["completed"] += 1
        if event.goal:
            activity_stats[activity_name]["goals"].append({
                "goal": event.goal,
                "date": event.event_date.isoformat(),
                "status": event.status
            })
    
    return {
        "activity_id": activity_id,
        "activity_name": activity.name,
        "total_events": total_events,
        "completed_events": completed_events,
        "completion_rate": round(completed_events / total_events * 100, 2) if total_events > 0 else 0,
        "sub_activities": [
            {
                "activity_name": name,
                "total_events": stats["total"],
                "completed_events": stats["completed"],
                "completion_rate": round(stats["completed"] / stats["total"] * 100, 2) if stats["total"] > 0 else 0,
                "goals": stats["goals"]
            }
            for name, stats in activity_stats.items()
        ]
    }

@router.get("/activities/tree-statistics")
def get_activity_tree_statistics(db: Session = Depends(get_db)):
    """获取活动树形结构及其统计信息"""
    def build_tree_with_stats(parent_id=None):
        children = db.query(ActivityModel).filter(ActivityModel.parent_id == parent_id).all()
        result = []
        
        for child in children:
            # 获取该活动及其所有子活动的事件统计
            target_ids = {child.id}
            target_ids.update(get_activity_descendants(db, child.id))
            
            events = db.query(ScheduledEventModel).filter(
                ScheduledEventModel.activity_id.in_(target_ids)
            ).all()
            
            total_events = len(events)
            completed_events = sum(1 for event in events if event.status == "completed")
            
            child_data = {
                "id": child.id,
                "name": child.name,
                "parent_id": child.parent_id,
                "description": child.description,
                "created_at": child.created_at.isoformat(),
                "total_events": total_events,
                "completed_events": completed_events,
                "completion_rate": round(completed_events / total_events * 100, 2) if total_events > 0 else 0,
                "children": build_tree_with_stats(child.id)
            }
            result.append(child_data)
        
        return result
    
    return build_tree_with_stats()