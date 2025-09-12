import requests
import json
from datetime import date, timedelta

BASE_URL = "http://127.0.0.1:8000/api"

def create_test_data():
    print("Starting to create test data...")
    
    # 1. 创建主活动
    main_activities = [
        {"name": "zeroPPD", "description": "Zero-Point Product Development 项目"},
        {"name": "学习", "description": "个人技能提升"},
        {"name": "生活", "description": "日常生活安排"},
    ]
    
    activity_ids = {}
    
    # 创建主活动
    for activity in main_activities:
        response = requests.post(f"{BASE_URL}/activities/", 
                               json=activity,
                               headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            result = response.json()
            activity_ids[activity["name"]] = result["id"]
            print(f"Created main activity: {activity['name']} (ID: {result['id']})")
        else:
            print(f"Failed to create activity: {activity['name']} - {response.text}")
    
    # 2. 创建子活动
    sub_activities = [
        # zeroPPD 子活动
        {"name": "zeroPPD-文献阅读", "parent_id": activity_ids.get("zeroPPD"), 
         "description": "阅读相关学术论文和技术文档"},
        {"name": "zeroPPD-数据分析", "parent_id": activity_ids.get("zeroPPD"), 
         "description": "处理和分析项目数据"},
        {"name": "zeroPPD-代码开发", "parent_id": activity_ids.get("zeroPPD"), 
         "description": "编写项目相关代码"},
        {"name": "zeroPPD-实验设计", "parent_id": activity_ids.get("zeroPPD"), 
         "description": "设计和执行实验"},
        
        # 学习子活动
        {"name": "技术学习", "parent_id": activity_ids.get("学习"), 
         "description": "学习新技术和工具"},
        {"name": "论文写作", "parent_id": activity_ids.get("学习"), 
         "description": "学术论文写作技巧"},
        
        # 生活子活动
        {"name": "运动健身", "parent_id": activity_ids.get("生活"), 
         "description": "保持身体健康"},
        {"name": "休息娱乐", "parent_id": activity_ids.get("生活"), 
         "description": "放松和娱乐活动"},
    ]
    
    for activity in sub_activities:
        response = requests.post(f"{BASE_URL}/activities/", 
                               json=activity,
                               headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            result = response.json()
            activity_ids[activity["name"]] = result["id"]
            print(f"Created sub activity: {activity['name']} (ID: {result['id']})")
        else:
            print(f"Failed to create sub activity: {activity['name']} - {response.text}")
    
    # 3. 创建一些示例日程
    today = date.today()
    
    # 本周的一些示例日程
    sample_events = [
        {
            "activity_id": activity_ids.get("zeroPPD-文献阅读"),
            "event_date": today.isoformat(),
            "time_slot": 21,  # 上午第1时段
            "goal": "阅读3篇关于产品开发的论文",
            "notes": "重点关注方法论部分",
            "status": "planned"
        },
        {
            "activity_id": activity_ids.get("zeroPPD-数据分析"),
            "event_date": today.isoformat(),
            "time_slot": 51,  # 下午第1时段
            "goal": "完成初步数据清洗",
            "notes": "使用Python pandas处理",
            "status": "planned"
        },
        {
            "activity_id": activity_ids.get("技术学习"),
            "event_date": (today + timedelta(days=1)).isoformat(),
            "time_slot": 22,  # 上午第2时段
            "goal": "学习FastAPI高级特性",
            "notes": "重点学习中间件和依赖注入",
            "status": "planned"
        },
        {
            "activity_id": activity_ids.get("运动健身"),
            "event_date": (today + timedelta(days=1)).isoformat(),
            "time_slot": 71,  # 晚上时段
            "goal": "跑步30分钟",
            "notes": "在公园慢跑",
            "status": "planned"
        },
        {
            "activity_id": activity_ids.get("zeroPPD-实验设计"),
            "event_date": (today + timedelta(days=2)).isoformat(),
            "time_slot": 21,  # 上午第1时段
            "goal": "设计A/B测试方案",
            "notes": "确定控制变量和测试指标",
            "status": "planned"
        }
    ]
    
    for event in sample_events:
        if event["activity_id"]:  # 只有活动ID存在时才创建
            response = requests.post(f"{BASE_URL}/events/", 
                                   json=event,
                                   headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                result = response.json()
                print(f"Created event: {event['goal']} (ID: {result['id']})")
            else:
                print(f"Failed to create event: {event['goal']} - {response.text}")
    
    print("\nTest data creation completed!")
    print("Now you can visit http://127.0.0.1:8000 to view the system")
    print("Test features:")
    print("1. Summary view - Activity tree structure and management")
    print("2. Week view - Schedule view and drag-drop functionality")  
    print("3. Month view - Monthly overview")

if __name__ == "__main__":
    create_test_data()