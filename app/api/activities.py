from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.activity import Activity as ActivityModel
from app.schemas import Activity, ActivityCreate, ActivityUpdate, ActivityWithChildren

router = APIRouter()

@router.post("/", response_model=Activity)
def create_activity(activity: ActivityCreate, db: Session = Depends(get_db)):
    if activity.parent_id:
        parent = db.query(ActivityModel).filter(ActivityModel.id == activity.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent activity not found")
    
    db_activity = ActivityModel(**activity.dict())
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

@router.get("/", response_model=List[Activity])
def get_activities(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    activities = db.query(ActivityModel).offset(skip).limit(limit).all()
    return activities

@router.get("/tree", response_model=List[ActivityWithChildren])
def get_activity_tree(db: Session = Depends(get_db)):
    def build_tree(parent_id=None):
        children = db.query(ActivityModel).filter(ActivityModel.parent_id == parent_id).all()
        result = []
        for child in children:
            child_dict = {
                "id": child.id,
                "name": child.name,
                "parent_id": child.parent_id,
                "description": child.description,
                "created_at": child.created_at,
                "children": build_tree(child.id)
            }
            result.append(ActivityWithChildren(**child_dict))
        return result
    
    return build_tree()

@router.get("/{activity_id}", response_model=Activity)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = db.query(ActivityModel).filter(ActivityModel.id == activity_id).first()
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity

@router.put("/{activity_id}", response_model=Activity)
def update_activity(activity_id: int, activity: ActivityUpdate, db: Session = Depends(get_db)):
    db_activity = db.query(ActivityModel).filter(ActivityModel.id == activity_id).first()
    if db_activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    update_data = activity.dict(exclude_unset=True)
    if "parent_id" in update_data and update_data["parent_id"]:
        parent = db.query(ActivityModel).filter(ActivityModel.id == update_data["parent_id"]).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent activity not found")
    
    for key, value in update_data.items():
        setattr(db_activity, key, value)
    
    db.commit()
    db.refresh(db_activity)
    return db_activity

@router.delete("/{activity_id}")
def delete_activity(activity_id: int, db: Session = Depends(get_db)):
    db_activity = db.query(ActivityModel).filter(ActivityModel.id == activity_id).first()
    if db_activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    db.delete(db_activity)
    db.commit()
    return {"message": "Activity deleted successfully"}