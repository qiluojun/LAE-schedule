"""
LAE v2.0 数据库初始化脚本
创建新的 v2.0 数据模型表结构
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.models.models import Domain, ActivityType, Schedule, ScheduledEvent

def create_v2_database():
    """Create LAE v2.0 database schema"""
    print("Creating LAE v2.0 database schema...")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("LAE v2.0 database tables created successfully!")
    print("New tables:")
    print("  - domains")
    print("  - activity_types")
    print("  - schedules")
    print("  - scheduled_events (updated to v2.0 architecture)")

if __name__ == "__main__":
    create_v2_database()