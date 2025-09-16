"""
LAE v2.0 Domains API
支持层级化 domain 管理的 CRUD 操作
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import Domain
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/domains", tags=["domains"])

# Pydantic schemas
class DomainBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class DomainCreate(DomainBase):
    pass

class DomainUpdate(DomainBase):
    name: Optional[str] = None

class DomainResponse(DomainBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}

class DomainTreeNode(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    created_at: datetime
    children: List['DomainTreeNode'] = []

    model_config = {"from_attributes": True}

# Update forward references
DomainTreeNode.model_rebuild()

@router.get("/")
def list_domains(db: Session = Depends(get_db)):
    """获取所有 domains"""
    domains = db.query(Domain).all()
    return [
        {
            "id": domain.id,
            "name": domain.name,
            "description": domain.description,
            "parent_id": domain.parent_id,
            "created_at": domain.created_at.isoformat() if domain.created_at else None
        }
        for domain in domains
    ]

@router.get("/tree", response_model=List[DomainTreeNode])
def get_domains_tree(db: Session = Depends(get_db)):
    """获取 domains 的层级树结构"""

    def build_tree(parent_id=None):
        domains = db.query(Domain).filter(Domain.parent_id == parent_id).all()
        tree = []
        for domain in domains:
            node = DomainTreeNode(
                id=domain.id,
                name=domain.name,
                description=domain.description,
                parent_id=domain.parent_id,
                created_at=domain.created_at,
                children=build_tree(domain.id)
            )
            tree.append(node)
        return tree

    return build_tree()

@router.get("/{domain_id}", response_model=DomainResponse)
def get_domain(domain_id: int, db: Session = Depends(get_db)):
    """获取指定 domain"""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain with id {domain_id} not found"
        )
    return domain

@router.post("/", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
def create_domain(domain: DomainCreate, db: Session = Depends(get_db)):
    """创建新 domain"""

    # 验证 parent_id 是否存在（如果提供）
    if domain.parent_id:
        parent = db.query(Domain).filter(Domain.id == domain.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent domain with id {domain.parent_id} not found"
            )

    db_domain = Domain(**domain.dict())
    db.add(db_domain)
    db.commit()
    db.refresh(db_domain)

    return db_domain

@router.put("/{domain_id}", response_model=DomainResponse)
def update_domain(domain_id: int, domain_update: DomainUpdate, db: Session = Depends(get_db)):
    """更新指定 domain"""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain with id {domain_id} not found"
        )

    # 验证 parent_id 是否存在（如果提供）
    if domain_update.parent_id:
        if domain_update.parent_id == domain_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Domain cannot be its own parent"
            )
        parent = db.query(Domain).filter(Domain.id == domain_update.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent domain with id {domain_update.parent_id} not found"
            )

    # 更新字段
    update_data = domain_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(domain, field, value)

    db.commit()
    db.refresh(domain)

    return domain

@router.delete("/{domain_id}")
def delete_domain(domain_id: int, db: Session = Depends(get_db)):
    """删除指定 domain（将会级联删除所有子 domains）"""
    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain with id {domain_id} not found"
        )

    # 检查是否有子 domains
    children_count = db.query(Domain).filter(Domain.parent_id == domain_id).count()

    db.delete(domain)
    db.commit()

    return {
        "message": f"Domain '{domain.name}' deleted successfully",
        "children_deleted": children_count
    }