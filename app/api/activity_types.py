"""
LAE v2.0 Activity Types API
支持层级化 activity type 管理的 CRUD 操作
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import ActivityType
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/activity-types", tags=["activity-types"])

# Pydantic schemas
class ActivityTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class ActivityTypeCreate(ActivityTypeBase):
    pass

class ActivityTypeUpdate(ActivityTypeBase):
    name: Optional[str] = None

class ActivityTypeResponse(ActivityTypeBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}

class ActivityTypeTreeNode(ActivityTypeResponse):
    children: List['ActivityTypeTreeNode'] = []

    model_config = {"from_attributes": True}

# Update forward references
ActivityTypeTreeNode.model_rebuild()

@router.get("/")
def list_activity_types(db: Session = Depends(get_db)):
    """获取所有 activity types"""
    activity_types = db.query(ActivityType).all()
    return [
        {
            "id": type.id,
            "name": type.name,
            "description": type.description,
            "parent_id": type.parent_id,
            "created_at": type.created_at.isoformat() if type.created_at else None
        }
        for type in activity_types
    ]

@router.get("/tree", response_model=List[ActivityTypeTreeNode])
def get_activity_types_tree(db: Session = Depends(get_db)):
    """获取 activity types 的层级树结构"""

    def build_tree(parent_id=None):
        activity_types = db.query(ActivityType).filter(ActivityType.parent_id == parent_id).all()
        tree = []
        for activity_type in activity_types:
            node = ActivityTypeTreeNode(
                id=activity_type.id,
                name=activity_type.name,
                description=activity_type.description,
                parent_id=activity_type.parent_id,
                created_at=activity_type.created_at,
                children=build_tree(activity_type.id)
            )
            tree.append(node)
        return tree

    return build_tree()

@router.get("/{type_id}", response_model=ActivityTypeResponse)
def get_activity_type(type_id: int, db: Session = Depends(get_db)):
    """获取指定 activity type"""
    activity_type = db.query(ActivityType).filter(ActivityType.id == type_id).first()
    if not activity_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity type with id {type_id} not found"
        )
    return activity_type

@router.post("/", response_model=ActivityTypeResponse, status_code=status.HTTP_201_CREATED)
def create_activity_type(activity_type: ActivityTypeCreate, db: Session = Depends(get_db)):
    """创建新 activity type"""

    # 验证 parent_id 是否存在（如果提供）
    if activity_type.parent_id:
        parent = db.query(ActivityType).filter(ActivityType.id == activity_type.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent activity type with id {activity_type.parent_id} not found"
            )

    db_activity_type = ActivityType(**activity_type.dict())
    db.add(db_activity_type)
    db.commit()
    db.refresh(db_activity_type)

    return db_activity_type

@router.put("/{type_id}", response_model=ActivityTypeResponse)
def update_activity_type(type_id: int, type_update: ActivityTypeUpdate, db: Session = Depends(get_db)):
    """更新指定 activity type"""
    activity_type = db.query(ActivityType).filter(ActivityType.id == type_id).first()
    if not activity_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity type with id {type_id} not found"
        )

    # 验证 parent_id 是否存在（如果提供）
    if type_update.parent_id:
        if type_update.parent_id == type_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activity type cannot be its own parent"
            )
        parent = db.query(ActivityType).filter(ActivityType.id == type_update.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent activity type with id {type_update.parent_id} not found"
            )

    # 更新字段
    update_data = type_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(activity_type, field, value)

    db.commit()
    db.refresh(activity_type)

    return activity_type

@router.delete("/{type_id}")
def delete_activity_type(type_id: int, db: Session = Depends(get_db)):
    """删除指定 activity type（将会级联删除所有子 types）"""
    activity_type = db.query(ActivityType).filter(ActivityType.id == type_id).first()
    if not activity_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity type with id {type_id} not found"
        )

    # 检查是否有子 types
    children_count = db.query(ActivityType).filter(ActivityType.parent_id == type_id).count()

    db.delete(activity_type)
    db.commit()

    return {
        "message": f"Activity type '{activity_type.name}' deleted successfully",
        "children_deleted": children_count
    }