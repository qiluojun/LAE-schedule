from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from collections import defaultdict

from app.database import get_db
from app.models.activity import Activity as ActivityModel
from app.models.scheduled_event import ScheduledEvent as ScheduledEventModel
from app.models.models import Domain, ActivityType, Schedule

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
    try:
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
    except Exception as e:
        # 空数据库或其他错误时返回默认值
        print(f"Summary statistics error: {e}")
        return {
            "total_activities": 0,
            "total_events": 0,
            "completed_events": 0,
            "completion_rate": 0,
            "status_distribution": [],
            "timeslot_distribution": []
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


@router.get("/domains/statistics")
def get_domain_statistics(db: Session = Depends(get_db)):
    """获取所有Domain的统计信息，包括日程数量和卡片数量"""
    try:
        domains = db.query(Domain).all()
        result = {}

        for domain in domains:
            # 统计该domain的所有scheduled_events（包括子domain）
            child_domains = get_domain_descendants(db, domain.id)
            all_domain_ids = {domain.id}.union(child_domains)

            # 统计日程数量（V2架构）
            schedule_count = db.query(Schedule).filter(
                Schedule.domain_id.in_(all_domain_ids)
            ).count()

            # 统计卡片数量（V3架构）- 基于scheduled_events表中的domain_id
            card_count = db.query(ScheduledEventModel).filter(
                ScheduledEventModel.domain_id.in_(all_domain_ids)
            ).count()

            result[domain.id] = {
                "domain_id": domain.id,
                "domain_name": domain.name,
                "schedule_count": schedule_count,
                "card_count": card_count,
                "total_items": schedule_count + card_count
            }

        return result
    except Exception as e:
        # 空数据库或其他错误时返回空字典
        print(f"Domain statistics error: {e}")
        return {}


@router.get("/activity-types/statistics")
def get_activity_type_statistics(db: Session = Depends(get_db)):
    """获取所有ActivityType的统计信息，包括卡片数量"""
    try:
        activity_types = db.query(ActivityType).all()
        result = {}

        for activity_type in activity_types:
            # 统计该activity_type的所有scheduled_events（包括子type）
            child_types = get_activity_type_descendants(db, activity_type.id)
            all_type_ids = {activity_type.id}.union(child_types)

            # 统计卡片数量（V3架构）- 基于scheduled_events表中的activity_type_id
            card_count = db.query(ScheduledEventModel).filter(
                ScheduledEventModel.activity_type_id.in_(all_type_ids)
            ).count()

            result[activity_type.id] = {
                "activity_type_id": activity_type.id,
                "activity_type_name": activity_type.name,
                "card_count": card_count
            }

        return result
    except Exception as e:
        # 空数据库或其他错误时返回空字典
        print(f"ActivityType statistics error: {e}")
        return {}


def get_domain_descendants(db: Session, domain_id: int):
    """递归获取domain的所有子domain ID"""
    descendants = set()

    def collect_children(parent_id):
        children = db.query(Domain).filter(Domain.parent_id == parent_id).all()
        for child in children:
            descendants.add(child.id)
            collect_children(child.id)

    collect_children(domain_id)
    return descendants


def get_activity_type_descendants(db: Session, activity_type_id: int):
    """递归获取activity_type的所有子type ID"""
    descendants = set()

    def collect_children(parent_id):
        children = db.query(ActivityType).filter(ActivityType.parent_id == parent_id).all()
        for child in children:
            descendants.add(child.id)
            collect_children(child.id)

    collect_children(activity_type_id)
    return descendants