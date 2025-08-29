#!/usr/bin/env python3
"""
API测试脚本
"""

import requests
import json

def test_health():
    """测试健康检查端点"""
    print("🔍 测试健康检查...")
    try:
        response = requests.get("http://localhost:8000/api/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")

def test_explore():
    """测试探索API"""
    print("\n🧭 测试探索API...")
    
    # 测试数据：北京的坐标，朝向东方
    test_data = {
        "latitude": 39.9042,
        "longitude": 116.4074,
        "heading": 90,  # 东方
        "segment_distance": 100,
        "time_mode": "present",
        "speed": 120
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/explore",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 探索API测试通过")
            print(f"   找到 {len(data['places'])} 个地点")
            print(f"   总距离: {data['total_distance']} km")
            print(f"   计算时间: {data['calculation_time']:.3f} 秒")
            
            # 显示前3个地点
            for i, place in enumerate(data['places'][:3]):
                print(f"   地点 {i+1}: {place['name']} ({place['distance']} km)")
        else:
            print(f"❌ 探索API失败: {response.status_code}")
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def test_places():
    """测试地点数据API"""
    print("\n📍 测试地点数据API...")
    
    for mode in ["present", "past", "future"]:
        try:
            response = requests.get(f"http://localhost:8000/api/places/{mode}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {mode} 模式: {len(data['places'])} 个地点")
            else:
                print(f"❌ {mode} 模式失败: {response.status_code}")
        except Exception as e:
            print(f"❌ {mode} 模式请求失败: {e}")

def main():
    """主测试函数"""
    print("🧭 方向探索派对 - API测试")
    print("=" * 50)
    
    test_health()
    test_explore()
    test_places()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("\n📱 前端访问地址: http://localhost:3000")
    print("📚 API文档地址: http://localhost:8000/docs")

if __name__ == "__main__":
    main()