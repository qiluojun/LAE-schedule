from app.database import engine, Base
from app.models.models import Activity, ScheduledEvent
import os

def create_tables():
    # 确保data目录存在
    os.makedirs("data", exist_ok=True)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()