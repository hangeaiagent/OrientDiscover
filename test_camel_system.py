#!/usr/bin/env python3
"""
CAMEL多智能体旅游导航系统测试脚本

测试一句话生成旅游导航图的完整功能
"""

import asyncio
import json
import logging
import os
import sys
from dotenv import load_dotenv

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_individual_agents():
    """测试各个智能体的功能"""
    print("\n=== 测试各个智能体 ===")
    
    try:
        from camel_agents import RequirementAnalyst, AttractionHunter, ContentCreator, MediaManager, AlbumOrganizer
        from supabase_client import supabase_client
        
        # 测试需求分析师
        print("\n1. 测试需求分析师")
        analyst = RequirementAnalyst()
        test_prompt = "我想去北京体验传统文化，看故宫、长城，品尝老北京美食"
        requirements = await analyst.analyze_user_input(test_prompt)
        print(f"需求分析结果: {json.dumps(requirements, ensure_ascii=False, indent=2)}")
        
        # 测试景点搜索专家
        print("\n2. 测试景点搜索专家")
        hunter = AttractionHunter(supabase_client)
        attractions = await hunter.search_attractions(requirements)
        print(f"找到 {len(attractions)} 个景点")
        if attractions:
            print(f"第一个景点: {attractions[0].get('name', '未知')}")
        
        # 测试内容创作者
        print("\n3. 测试内容创作者")
        creator = ContentCreator()
        if attractions:
            content = await creator.generate_content(attractions[0], requirements)
            print(f"内容创作结果: {json.dumps(content, ensure_ascii=False, indent=2)}")
        
        # 测试媒体管理员
        print("\n4. 测试媒体管理员")
        media_manager = MediaManager()
        if attractions:
            media = await media_manager.fetch_media_resources(attractions[0])
            print(f"媒体资源: 图片 {len(media.get('images', []))} 张，视频 {len(media.get('videos', []))} 个")
        
        # 测试相册组织者
        print("\n5. 测试相册组织者")
        organizer = AlbumOrganizer(supabase_client)
        if attractions:
            album = await organizer.create_album(attractions[:3], requirements, "test_user")
            print(f"相册创建成功: {album.get('title', '未知标题')}")
        
        return True
        
    except Exception as e:
        logger.error(f"智能体测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_vector_database():
    """测试向量数据库功能"""
    print("\n=== 测试向量数据库 ===")
    
    try:
        from vector_database import get_vector_database
        
        vector_db = get_vector_database()
        
        # 测试向量搜索
        print("\n1. 测试向量相似度搜索")
        results = await vector_db.similarity_search("北京历史文化景点", limit=3)
        print(f"向量搜索结果: {len(results)} 个")
        
        for i, result in enumerate(results[:2]):
            print(f"  {i+1}. {result.get('name', '未知景点')} - 相似度: {result.get('similarity', 0):.3f}")
        
        # 测试语义搜索（带地理位置）
        print("\n2. 测试语义搜索（带位置）")
        semantic_results = await vector_db.search_attractions_by_semantic(
            "传统文化古建筑",
            location=(39.9042, 116.4074),  # 北京坐标
            radius_km=50,
            limit=3
        )
        print(f"语义搜索结果: {len(semantic_results)} 个")
        
        return True
        
    except Exception as e:
        logger.error(f"向量数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_orchestrator():
    """测试多智能体编排器"""
    print("\n=== 测试多智能体编排器 ===")
    
    try:
        from album_orchestrator import get_album_orchestrator
        
        orchestrator = get_album_orchestrator()
        
        # 测试健康检查
        print("\n1. 测试系统健康检查")
        health = await orchestrator.health_check()
        print(f"系统状态: {health.get('overall', 'unknown')}")
        
        # 测试完整的相册生成流程
        print("\n2. 测试完整相册生成")
        test_prompts = [
            "我想去北京看历史文化景点",
            "想去上海体验现代都市生活",
            "计划去杭州欣赏江南美景"
        ]
        
        for i, prompt in enumerate(test_prompts[:1]):  # 只测试第一个
            print(f"\n测试提示 {i+1}: {prompt}")
            
            result = await orchestrator.generate_album_from_prompt(prompt, f"test_user_{i}")
            
            if result.get('success'):
                album = result.get('album', {})
                print(f"✅ 相册生成成功:")
                print(f"   标题: {album.get('title', '未知')}")
                print(f"   景点数量: {len(album.get('attractions', []))}")
                print(f"   预估时长: {album.get('metadata', {}).get('estimated_duration', '未知')}")
            else:
                print(f"❌ 相册生成失败: {result.get('error', '未知错误')}")
        
        # 测试快速推荐
        print("\n3. 测试快速推荐")
        quick_result = await orchestrator.generate_quick_recommendations(
            location=(39.9042, 116.4074),  # 北京
            interests=["历史文化", "传统建筑"],
            limit=3
        )
        
        if quick_result.get('success'):
            recommendations = quick_result.get('recommendations', [])
            print(f"✅ 快速推荐成功: {len(recommendations)} 个景点")
            for rec in recommendations[:2]:
                print(f"   - {rec.get('name', '未知景点')}")
        else:
            print(f"❌ 快速推荐失败: {quick_result.get('error', '未知错误')}")
        
        return True
        
    except Exception as e:
        logger.error(f"编排器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_media_services():
    """测试媒体服务"""
    print("\n=== 测试媒体服务 ===")
    
    try:
        from media_service_enhanced import get_enhanced_media_manager
        
        media_manager = get_enhanced_media_manager()
        
        # 测试图片搜索
        print("\n1. 测试图片搜索")
        test_attraction = {
            'name': '故宫',
            'city': '北京',
            'category': '文化古迹'
        }
        
        media_resources = await media_manager.fetch_media_resources(test_attraction)
        
        images = media_resources.get('images', [])
        print(f"获取到 {len(images)} 张图片")
        
        if images:
            print(f"第一张图片: {images[0].get('description', '无描述')}")
            print(f"图片来源: {images[0].get('source', '未知')}")
        
        # 测试媒体分析
        analytics = media_resources.get('analytics', {})
        if analytics:
            print(f"媒体质量分析:")
            print(f"  质量分数: {analytics.get('quality_score', 0):.1f}%")
            print(f"  多样性分数: {analytics.get('diversity_score', 0):.1f}%")
            print(f"  完整性分数: {analytics.get('completeness_score', 0):.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"媒体服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_endpoints():
    """测试API端点"""
    print("\n=== 测试API端点 ===")
    
    try:
        import aiohttp
        
        # 测试基础API
        base_url = "http://localhost:8001"
        
        async with aiohttp.ClientSession() as session:
            # 测试健康检查
            print("\n1. 测试基础健康检查")
            async with session.get(f"{base_url}/api/health") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 基础API正常: {result.get('status', 'unknown')}")
                else:
                    print(f"❌ 基础API异常: HTTP {response.status}")
            
            # 测试CAMEL健康检查
            print("\n2. 测试CAMEL系统健康检查")
            async with session.get(f"{base_url}/api/camel-health") as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success'):
                        health_data = result.get('data', {})
                        print(f"✅ CAMEL系统状态: {health_data.get('overall', 'unknown')}")
                    else:
                        print(f"❌ CAMEL系统异常: {result.get('error', '未知错误')}")
                else:
                    print(f"❌ CAMEL健康检查失败: HTTP {response.status}")
            
            # 测试相册生成API
            print("\n3. 测试相册生成API")
            test_data = {
                "user_prompt": "我想去北京看故宫和长城",
                "user_id": "test_user",
                "language": "zh-CN"
            }
            
            async with session.post(f"{base_url}/api/generate-album", json=test_data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('success'):
                        album = result.get('album', {})
                        print(f"✅ 相册生成成功: {album.get('title', '未知标题')}")
                        print(f"   包含景点: {len(album.get('attractions', []))} 个")
                    else:
                        print(f"❌ 相册生成失败: {result.get('error', '未知错误')}")
                else:
                    print(f"❌ 相册生成API失败: HTTP {response.status}")
        
        return True
        
    except Exception as e:
        logger.error(f"API端点测试失败: {e}")
        print("注意: 请确保后端服务正在运行 (python backend/main.py)")
        return False


def print_test_summary(results):
    """打印测试总结"""
    print("\n" + "="*50)
    print("测试总结")
    print("="*50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n详细结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！系统运行正常。")
    else:
        print(f"\n⚠️  有 {total_tests - passed_tests} 个测试失败，请检查相关组件。")


async def main():
    """主测试函数"""
    print("开始CAMEL多智能体旅游导航系统测试...")
    print("="*60)
    
    # 检查环境变量
    required_env_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  缺少必要的环境变量: {', '.join(missing_vars)}")
        print("请检查.env文件配置")
        return
    
    # 运行测试
    test_results = {}
    
    # 测试各个组件
    test_results["智能体测试"] = await test_individual_agents()
    test_results["向量数据库测试"] = await test_vector_database()
    test_results["编排器测试"] = await test_orchestrator()
    test_results["媒体服务测试"] = await test_media_services()
    test_results["API端点测试"] = await test_api_endpoints()
    
    # 打印总结
    print_test_summary(test_results)


if __name__ == "__main__":
    asyncio.run(main())