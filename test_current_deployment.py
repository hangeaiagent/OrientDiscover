#!/usr/bin/env python3
"""
测试当前部署状态
确认行政区域过滤和高德地图API集成是否正常工作
"""

import requests
import json

def test_api_endpoint():
    """测试API端点"""
    url = "http://localhost:8000/api/explore-real"
    
    # 测试数据
    test_cases = [
        {
            "name": "昌平区坐标（应该返回景点，不返回昌平区）",
            "data": {
                "latitude": 40.2917,
                "longitude": 116.2333,
                "heading": 90,
                "segment_distance": 10,
                "time_mode": "present"
            }
        },
        {
            "name": "北京市中心（应该返回天坛、故宫等景点）",
            "data": {
                "latitude": 39.9042,
                "longitude": 116.4074,
                "heading": 90,
                "segment_distance": 15,
                "time_mode": "present"
            }
        },
        {
            "name": "小汤山附近（应该返回多样化景点）",
            "data": {
                "latitude": 40.18,
                "longitude": 116.38,
                "heading": 45,
                "segment_distance": 5,
                "time_mode": "present"
            }
        }
    ]
    
    print("🧪 测试当前部署状态")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 30)
        
        try:
            response = requests.post(url, json=test_case['data'], timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                places = data.get('places', [])
                
                print(f"✅ 状态码: {response.status_code}")
                print(f"📍 返回景点数量: {len(places)}")
                
                if places:
                    print("🏛️ 返回的景点:")
                    for j, place in enumerate(places, 1):
                        name = place.get('name', '未知')
                        # 检查是否为行政区域
                        admin_keywords = ['区', '市', '县', '省', '街道', '镇', '乡', '村']
                        is_admin = any(keyword in name for keyword in admin_keywords)
                        status = "❌ 行政区域" if is_admin else "✅ 景点"
                        
                        print(f"   {j}. {name} {status}")
                        print(f"      坐标: ({place.get('latitude', 0):.4f}, {place.get('longitude', 0):.4f})")
                        print(f"      开放时间: {place.get('opening_hours', 'null')}")
                        print(f"      票价: {place.get('ticket_price', 'null')}")
                else:
                    print("⚠️ 没有返回任何景点")
                    
            else:
                print(f"❌ 状态码: {response.status_code}")
                print(f"错误: {response.text}")
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
    
    print("\n" + "=" * 50)
    print("测试完成")

def test_health():
    """测试健康状态"""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API服务正常运行")
            return True
        else:
            print(f"❌ API服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到API服务: {e}")
        return False

if __name__ == "__main__":
    print("🔍 OrientDiscover 部署状态检查")
    print("=" * 50)
    
    # 检查API健康状态
    if test_health():
        # 测试API功能
        test_api_endpoint()
    else:
        print("请先启动API服务")
