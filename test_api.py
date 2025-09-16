#!/usr/bin/env python3
"""
测试API功能的独立脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from fastapi.testclient import TestClient

def test_statistics_api():
    """测试statistics API"""
    client = TestClient(app)

    print("Testing statistics/summary endpoint...")
    try:
        response = client.get("/api/statistics/summary")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ API成功响应:")
            print(f"  总活动数: {data['total_activities']}")
            print(f"  总事件数: {data['total_events']}")
            print(f"  完成率: {data['completion_rate']}%")
        else:
            print(f"❌ API返回错误状态码: {response.status_code}")
            print(f"响应内容: {response.text}")

    except Exception as e:
        print(f"❌ API测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_statistics_api()