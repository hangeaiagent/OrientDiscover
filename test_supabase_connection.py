#!/usr/bin/env python3
"""
测试Supabase数据库连接
Test Supabase Database Connection
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# 添加后端目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_environment_variables():
    """测试环境变量"""
    print("🔧 检查环境变量...")
    load_dotenv()
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:20]}...")
        else:
            missing_vars.append(var)
            print(f"❌ {var}: 未设置")
    
    if missing_vars:
        print(f"\n⚠️ 缺少环境变量: {', '.join(missing_vars)}")
        print("请创建 .env 文件并设置这些变量")
        return False
    
    print("✅ 环境变量检查通过")
    return True

def test_supabase_import():
    """测试Supabase模块导入"""
    print("\n📦 测试模块导入...")
    
    try:
        from supabase import create_client, Client
        print("✅ Supabase Python客户端导入成功")
        return True
    except ImportError as e:
        print(f"❌ Supabase Python客户端导入失败: {e}")
        print("请运行: pip install supabase")
        return False

async def test_supabase_connection():
    """测试Supabase数据库连接"""
    print("\n🔗 测试Supabase连接...")
    
    try:
        from supabase_client import supabase_client
        
        # 测试连接
        is_connected = await supabase_client.test_connection()
        
        if is_connected:
            print("✅ Supabase数据库连接成功")
            return True
        else:
            print("❌ Supabase数据库连接失败")
            return False
            
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False

async def test_api_service():
    """测试API服务"""
    print("\n🚀 测试API服务...")
    
    try:
        from spot_api_service import spot_api_service
        
        # 健康检查
        health_status = await spot_api_service.health_check()
        print(f"✅ API服务状态: {health_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ API服务测试失败: {e}")
        return False

async def test_data_queries():
    """测试数据查询"""
    print("\n📊 测试数据查询...")
    
    try:
        from spot_api_service import spot_api_service
        
        # 测试获取所有景点
        print("  测试获取所有景点...")
        attractions = await spot_api_service.get_all_attractions()
        print(f"  ✅ 获取到 {len(attractions)} 个景点")
        
        # 测试附近景点查询（北京天安门附近）
        print("  测试附近景点查询...")
        nearby = await spot_api_service.get_nearby_attractions(39.9042, 116.4074, 50)
        print(f"  ✅ 找到 {len(nearby)} 个附近景点")
        
        # 测试搜索功能
        print("  测试搜索功能...")
        search_results = await spot_api_service.search_attractions("故宫")
        print(f"  ✅ 搜索到 {len(search_results)} 个相关景点")
        
        # 测试统计信息
        print("  测试统计信息...")
        stats = await spot_api_service.get_statistics()
        print(f"  ✅ 统计信息: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据查询测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🧪 开始Supabase集成测试\n")
    
    tests = [
        ("环境变量检查", test_environment_variables),
        ("模块导入测试", test_supabase_import),
        ("数据库连接测试", test_supabase_connection),
        ("API服务测试", test_api_service),
        ("数据查询测试", test_data_queries)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 {test_name}")
        print(f"{'='*50}")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
                
            if result:
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
                
        except Exception as e:
            print(f"💥 {test_name} - 异常: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*50}")
    print(f"📊 测试结果: {passed}/{total} 通过")
    print(f"{'='*50}")
    
    if passed == total:
        print("🎉 所有测试通过！Supabase集成准备就绪")
        return True
    else:
        print("⚠️ 部分测试失败，请检查配置")
        return False

if __name__ == "__main__":
    asyncio.run(main())