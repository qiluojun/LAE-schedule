# -*- coding: utf-8 -*-
"""
数据清理脚本 - 删除演示数据，保留顶级结构
"""

import sys
import os

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal
from app.models.scheduled_event import ScheduledEvent
from app.models.schedule import Schedule
from app.models.domain import Domain
from app.models.activity_type import ActivityType

def clean_all_data():
    """清理所有演示数据"""
    session = SessionLocal()

    try:
        print("开始清理数据...")

        # 1. 删除所有 scheduled_events（事件数据）
        print("删除所有事件数据...")
        events_count = session.query(ScheduledEvent).count()
        session.query(ScheduledEvent).delete()
        print(f"已删除 {events_count} 个事件")

        # 2. 删除所有 schedules（日程数据）
        print("删除所有日程数据...")
        schedules_count = session.query(Schedule).count()
        session.query(Schedule).delete()
        print(f"已删除 {schedules_count} 个日程")

        # 3. 删除二级及以下的 domains（保留顶级domains）
        print("删除二级及以下的Domain数据...")
        child_domains = session.query(Domain).filter(Domain.parent_id != None).all()
        child_domains_count = len(child_domains)
        for domain in child_domains:
            session.delete(domain)
        print(f"已删除 {child_domains_count} 个子级Domain")

        # 4. 删除二级及以下的 activity_types（保留顶级types）
        print("删除二级及以下的ActivityType数据...")
        child_types = session.query(ActivityType).filter(ActivityType.parent_id != None).all()
        child_types_count = len(child_types)
        for activity_type in child_types:
            session.delete(activity_type)
        print(f"已删除 {child_types_count} 个子级ActivityType")

        # 提交更改
        session.commit()
        print("数据清理完成！")

        # 显示剩余的顶级数据
        print("剩余的顶级数据:")
        top_domains = session.query(Domain).filter(Domain.parent_id == None).all()
        print(f"顶级Domains: {len(top_domains)} 个")
        for domain in top_domains:
            print(f"  - {domain.name}")

        top_types = session.query(ActivityType).filter(ActivityType.parent_id == None).all()
        print(f"顶级ActivityTypes: {len(top_types)} 个")
        for activity_type in top_types:
            print(f"  - {activity_type.name}")

    except Exception as e:
        session.rollback()
        print(f"清理数据时出错: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("即将清理数据库中的演示数据...")
    print("- 所有事件数据 (scheduled_events)")
    print("- 所有日程数据 (schedules)")
    print("- 二级及以下的domain数据")
    print("- 二级及以下的activity_type数据")
    print("- 保留顶级的domain和activity_type作为结构基础")
    print()

    confirm = input("确认执行清理操作？(yes/no): ")
    if confirm.lower() in ['yes', 'y']:
        clean_all_data()
    else:
        print("已取消清理操作")