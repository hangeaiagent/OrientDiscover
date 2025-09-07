#!/usr/bin/env python3
"""
CAMEL多智能体旅游导航系统演示脚本

演示系统的核心功能，不需要实际的API密钥
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, List

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockRequirementAnalyst:
    """模拟需求分析师"""
    
    def __init__(self):
        self.role_name = "需求分析师"
    
    async def analyze_user_input(self, user_input: str) -> Dict:
        """分析用户输入"""
        logger.info(f"🔍 需求分析师正在分析: {user_input}")
        
        # 模拟分析结果
        if "北京" in user_input:
            return {
                "destination": "北京",
                "interests": ["历史文化", "传统建筑"],
                "time_preference": "2-3天",
                "budget_range": "中等",
                "travel_style": "文化探索",
                "group_type": "个人",
                "description": "用户希望在北京体验传统文化和历史景点"
            }
        elif "上海" in user_input:
            return {
                "destination": "上海",
                "interests": ["现代建筑", "都市体验"],
                "time_preference": "2-3天",
                "budget_range": "中等",
                "travel_style": "都市探索",
                "group_type": "个人",
                "description": "用户希望体验上海的现代都市魅力"
            }
        else:
            return {
                "destination": "未知",
                "interests": ["观光旅游"],
                "time_preference": "1-2天",
                "budget_range": "经济",
                "travel_style": "休闲",
                "group_type": "个人",
                "description": "通用旅游需求"
            }


class MockAttractionHunter:
    """模拟景点搜索专家"""
    
    def __init__(self):
        self.role_name = "景点搜索专家"
        self.mock_attractions = {
            "北京": [
                {
                    "id": "1",
                    "name": "故宫博物院",
                    "latitude": 39.9163,
                    "longitude": 116.3972,
                    "category": "文化古迹",
                    "country": "中国",
                    "city": "北京",
                    "address": "北京市东城区景山前街4号",
                    "description": "明清两朝的皇家宫殿，世界文化遗产",
                    "opening_hours": "08:30-17:00",
                    "ticket_price": "成人票60元",
                    "booking_method": "官网预约或现场购票",
                    "relevance_score": 9.5
                },
                {
                    "id": "2",
                    "name": "八达岭长城",
                    "latitude": 40.3584,
                    "longitude": 116.0135,
                    "category": "文化古迹",
                    "country": "中国",
                    "city": "北京",
                    "address": "北京市延庆区八达岭镇",
                    "description": "万里长城最著名的一段，世界文化遗产",
                    "opening_hours": "06:30-19:00",
                    "ticket_price": "成人票40元",
                    "booking_method": "现场购票或网上预订",
                    "relevance_score": 9.0
                },
                {
                    "id": "3",
                    "name": "天坛公园",
                    "latitude": 39.8816,
                    "longitude": 116.4066,
                    "category": "文化古迹",
                    "country": "中国",
                    "city": "北京",
                    "address": "北京市东城区天坛路甲1号",
                    "description": "明清皇帝祭天的场所，古建筑艺术的杰作",
                    "opening_hours": "06:00-22:00",
                    "ticket_price": "公园门票15元，联票34元",
                    "booking_method": "现场购票",
                    "relevance_score": 8.5
                }
            ],
            "上海": [
                {
                    "id": "4",
                    "name": "外滩",
                    "latitude": 31.2396,
                    "longitude": 121.4906,
                    "category": "城市地标",
                    "country": "中国",
                    "city": "上海",
                    "address": "上海市黄浦区中山东一路",
                    "description": "上海的标志性景观，万国建筑博览群",
                    "opening_hours": "全天开放",
                    "ticket_price": "免费",
                    "booking_method": "无需预约",
                    "relevance_score": 9.2
                },
                {
                    "id": "5",
                    "name": "上海中心大厦",
                    "latitude": 31.2352,
                    "longitude": 121.5055,
                    "category": "现代建筑",
                    "country": "中国",
                    "city": "上海",
                    "address": "上海市浦东新区银城中路501号",
                    "description": "上海第一高楼，现代建筑的典范",
                    "opening_hours": "09:00-22:00",
                    "ticket_price": "观光厅180元",
                    "booking_method": "现场购票或网上预订",
                    "relevance_score": 8.8
                }
            ]
        }
    
    async def search_attractions(self, requirements: Dict) -> List[Dict]:
        """搜索景点"""
        destination = requirements.get('destination', '')
        logger.info(f"🗺️ 景点搜索专家正在搜索: {destination}")
        
        attractions = self.mock_attractions.get(destination, [])
        logger.info(f"找到 {len(attractions)} 个景点")
        
        return attractions


class MockContentCreator:
    """模拟内容创作者"""
    
    def __init__(self):
        self.role_name = "内容创作者"
    
    async def generate_content(self, attraction: Dict, requirements: Dict = None) -> Dict:
        """生成内容"""
        attraction_name = attraction.get('name', '未知景点')
        logger.info(f"✍️ 内容创作者正在为 {attraction_name} 生成内容")
        
        # 模拟生成的内容
        content_templates = {
            "故宫博物院": {
                "detailed_description": "故宫博物院，又称紫禁城，是明清两朝24位皇帝的皇宫。这座宏伟的建筑群占地72万平方米，拥有9999间房屋，是世界上现存最大、最完整的古代宫殿建筑群。红墙黄瓦，雕梁画栋，每一处细节都展现着中华文明的博大精深。漫步在这座五百多年的皇宫中，仿佛能听到历史的回声，感受到帝王的威严与文化的厚重。",
                "guide_commentary": "各位游客，欢迎来到故宫博物院！这里曾是明清皇帝的家，也是中国古代建筑艺术的巅峰之作。请看这金碧辉煌的太和殿，它是皇帝举行重大典礼的地方。每当朝阳初升，阳光洒在这黄色的琉璃瓦上，整个宫殿都闪闪发光，那种庄严神圣的感觉让人震撼不已。",
                "visit_tips": "建议提前网上预约门票，避开周末和节假日高峰期。参观路线推荐：午门-太和殿-中和殿-保和殿-乾清宫-坤宁宫-御花园。",
                "best_time": "春秋两季，上午9-11点或下午2-4点",
                "duration": "3-4小时",
                "highlights": ["太和殿", "乾清宫", "御花园", "珍宝馆"],
                "cultural_background": "明朝永乐年间始建，清朝康熙年间重修，承载着500多年的皇家历史",
                "photo_spots": ["太和殿广场", "御花园", "角楼", "午门城楼"]
            }
        }
        
        # 获取模板或生成默认内容
        template = content_templates.get(attraction_name, {
            "detailed_description": f"{attraction_name}是一处值得游览的景点，具有独特的魅力和丰富的文化内涵。这里不仅风景优美，还承载着深厚的历史文化底蕴，是了解当地文化和历史的绝佳去处。",
            "guide_commentary": f"欢迎来到{attraction_name}！这里是当地最具代表性的景点之一，每年吸引着众多游客前来参观。",
            "visit_tips": "建议合理安排游览时间，注意保护环境，遵守景区规定。",
            "best_time": "建议在天气晴朗的时候前往",
            "duration": "2-3小时",
            "highlights": [attraction_name],
            "cultural_background": "具有深厚的历史文化价值",
            "photo_spots": ["主要景观点", "标志性建筑"]
        })
        
        return template


class MockMediaManager:
    """模拟媒体管理员"""
    
    def __init__(self):
        self.role_name = "媒体资源管理员"
    
    async def fetch_media_resources(self, attraction: Dict) -> Dict:
        """获取媒体资源"""
        attraction_name = attraction.get('name', '未知景点')
        logger.info(f"📸 媒体管理员正在获取 {attraction_name} 的媒体资源")
        
        # 模拟媒体资源
        default_images = [
            {
                "url": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=800",
                "thumbnail": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=400",
                "description": f"{attraction_name}全景",
                "source": "Unsplash",
                "quality": "high"
            },
            {
                "url": "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=800",
                "thumbnail": "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=400",
                "description": f"{attraction_name}细节",
                "source": "Unsplash",
                "quality": "high"
            }
        ]
        
        return {
            'images': default_images,
            'videos': [],
            'thumbnails': [img['thumbnail'] for img in default_images],
            'analytics': {
                'quality_score': 85.0,
                'diversity_score': 75.0,
                'completeness_score': 80.0,
                'recommendations': ["图片质量良好", "建议增加更多角度的照片"]
            }
        }


class MockAlbumOrganizer:
    """模拟相册组织者"""
    
    def __init__(self):
        self.role_name = "相册组织者"
    
    async def create_album(self, attractions: List[Dict], requirements: Dict, creator_id: str) -> Dict:
        """创建相册"""
        destination = requirements.get('destination', '未知目的地')
        logger.info(f"📚 相册组织者正在为 {destination} 创建相册")
        
        # 生成相册标题
        titles = {
            "北京": "北京文化探索之旅",
            "上海": "上海都市魅力体验",
        }
        
        album_title = titles.get(destination, f"{destination}精彩之旅")
        
        # 生成相册描述
        descriptions = {
            "北京": "穿越千年历史，感受帝都文化。从紫禁城的宏伟壮丽到长城的雄伟壮观，这是一场深度的文化之旅，让您领略中华文明的博大精深。",
            "上海": "体验东方巴黎的独特魅力，从外滩的万国建筑到陆家嘴的摩天大楼，感受这座国际化大都市的现代与传统的完美融合。"
        }
        
        album_description = descriptions.get(destination, f"探索{destination}的独特魅力，发现旅途中的美好时光。")
        
        return {
            'title': album_title,
            'description': album_description,
            'destination': destination,
            'creator_id': creator_id,
            'attractions': attractions,
            'metadata': {
                'total_attractions': len(attractions),
                'categories': list(set(attr.get('category', '') for attr in attractions)),
                'estimated_duration': f"{len(attractions) * 2}小时（{len(attractions)}个景点）",
                'difficulty_level': '轻松',
                'best_season': '四季皆宜',
                'budget_estimate': '中等型（200-500元）'
            }
        }


class MockOrchestrator:
    """模拟多智能体编排器"""
    
    def __init__(self):
        self.requirement_analyst = MockRequirementAnalyst()
        self.attraction_hunter = MockAttractionHunter()
        self.content_creator = MockContentCreator()
        self.media_manager = MockMediaManager()
        self.album_organizer = MockAlbumOrganizer()
    
    async def generate_album_from_prompt(self, user_prompt: str, user_id: str = None) -> Dict:
        """生成相册"""
        try:
            logger.info(f"🎯 开始处理用户请求: {user_prompt}")
            
            if not user_id:
                user_id = f"demo_user_{hash(user_prompt) % 10000}"
            
            # 步骤1: 需求分析
            logger.info("📊 步骤1: 需求分析")
            requirements = await self.requirement_analyst.analyze_user_input(user_prompt)
            await asyncio.sleep(1)  # 模拟处理时间
            
            # 步骤2: 景点搜索
            logger.info("🔍 步骤2: 景点搜索")
            attractions = await self.attraction_hunter.search_attractions(requirements)
            await asyncio.sleep(1)
            
            if not attractions:
                return {
                    'success': False,
                    'error': '未找到匹配的景点'
                }
            
            # 步骤3: 内容创作和媒体资源获取（并行处理）
            logger.info("⚡ 步骤3: 并行处理内容创作和媒体资源")
            enhanced_attractions = []
            
            for attraction in attractions:
                # 并行处理
                content_task = self.content_creator.generate_content(attraction, requirements)
                media_task = self.media_manager.fetch_media_resources(attraction)
                
                content, media = await asyncio.gather(content_task, media_task)
                
                # 合并结果
                enhanced_attraction = attraction.copy()
                enhanced_attraction.update(content)
                enhanced_attraction.update(media)
                enhanced_attractions.append(enhanced_attraction)
            
            await asyncio.sleep(1)
            
            # 步骤4: 相册组织
            logger.info("📖 步骤4: 相册组织")
            album = await self.album_organizer.create_album(
                enhanced_attractions, requirements, user_id
            )
            await asyncio.sleep(1)
            
            logger.info(f"✅ 相册生成完成: {album.get('title', '未命名相册')}")
            
            return {
                'success': True,
                'album': album,
                'user_id': user_id
            }
            
        except Exception as e:
            logger.error(f"❌ 相册生成失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def health_check(self) -> Dict:
        """健康检查"""
        return {
            'overall': 'healthy',
            'agents': {
                'requirement_analyst': 'healthy',
                'attraction_hunter': 'healthy',
                'content_creator': 'healthy',
                'media_manager': 'healthy',
                'album_organizer': 'healthy'
            },
            'vector_db': 'demo_mode',
            'supabase': 'demo_mode'
        }


async def demo_individual_agents():
    """演示各个智能体的功能"""
    print("\n" + "="*60)
    print("🤖 演示各个智能体功能")
    print("="*60)
    
    test_prompt = "我想去北京体验传统文化，看故宫、长城，品尝老北京美食"
    
    # 演示需求分析师
    print("\n1️⃣ 需求分析师")
    analyst = MockRequirementAnalyst()
    requirements = await analyst.analyze_user_input(test_prompt)
    print(f"✅ 需求分析结果:")
    for key, value in requirements.items():
        print(f"   {key}: {value}")
    
    # 演示景点搜索专家
    print("\n2️⃣ 景点搜索专家")
    hunter = MockAttractionHunter()
    attractions = await hunter.search_attractions(requirements)
    print(f"✅ 找到 {len(attractions)} 个景点:")
    for attr in attractions:
        print(f"   - {attr['name']} ({attr['category']})")
    
    # 演示内容创作者
    print("\n3️⃣ 内容创作者")
    creator = MockContentCreator()
    if attractions:
        content = await creator.generate_content(attractions[0], requirements)
        print(f"✅ 为 {attractions[0]['name']} 生成的内容:")
        print(f"   描述: {content['detailed_description'][:100]}...")
        print(f"   亮点: {', '.join(content['highlights'])}")
    
    # 演示媒体管理员
    print("\n4️⃣ 媒体资源管理员")
    media_manager = MockMediaManager()
    if attractions:
        media = await media_manager.fetch_media_resources(attractions[0])
        print(f"✅ 获取媒体资源:")
        print(f"   图片: {len(media['images'])} 张")
        print(f"   质量分数: {media['analytics']['quality_score']}%")
    
    # 演示相册组织者
    print("\n5️⃣ 相册组织者")
    organizer = MockAlbumOrganizer()
    if attractions:
        album = await organizer.create_album(attractions, requirements, "demo_user")
        print(f"✅ 相册创建成功:")
        print(f"   标题: {album['title']}")
        print(f"   景点数: {album['metadata']['total_attractions']}")
        print(f"   预估时长: {album['metadata']['estimated_duration']}")


async def demo_full_workflow():
    """演示完整的工作流程"""
    print("\n" + "="*60)
    print("🚀 演示完整相册生成流程")
    print("="*60)
    
    orchestrator = MockOrchestrator()
    
    test_cases = [
        "我想去北京看故宫和长城，体验传统文化",
        "想去上海看外滩夜景，感受现代都市魅力",
        "计划去杭州西湖游玩，体验江南风情"
    ]
    
    for i, prompt in enumerate(test_cases, 1):
        print(f"\n🎯 测试案例 {i}: {prompt}")
        print("-" * 50)
        
        result = await orchestrator.generate_album_from_prompt(prompt)
        
        if result.get('success'):
            album = result.get('album', {})
            print(f"✅ 生成成功!")
            print(f"   📚 相册标题: {album.get('title', '未知')}")
            print(f"   📍 目的地: {album.get('destination', '未知')}")
            print(f"   🗺️ 景点数量: {len(album.get('attractions', []))}")
            print(f"   ⏱️ 预估时长: {album.get('metadata', {}).get('estimated_duration', '未知')}")
            print(f"   💰 预算估算: {album.get('metadata', {}).get('budget_estimate', '未知')}")
            
            # 显示景点列表
            attractions = album.get('attractions', [])
            if attractions:
                print(f"   🏛️ 包含景点:")
                for attr in attractions[:3]:  # 只显示前3个
                    print(f"      - {attr.get('name', '未知')} ({attr.get('category', '景点')})")
        else:
            print(f"❌ 生成失败: {result.get('error', '未知错误')}")
        
        print()


async def demo_health_check():
    """演示健康检查"""
    print("\n" + "="*60)
    print("🏥 系统健康检查")
    print("="*60)
    
    orchestrator = MockOrchestrator()
    health = await orchestrator.health_check()
    
    print(f"🎯 总体状态: {health['overall']}")
    print(f"🤖 智能体状态:")
    for agent_name, status in health['agents'].items():
        status_icon = "✅" if status == "healthy" else "❌"
        print(f"   {status_icon} {agent_name}: {status}")
    
    print(f"🗄️ 向量数据库: {health['vector_db']}")
    print(f"☁️ Supabase: {health['supabase']}")


def print_demo_summary():
    """打印演示总结"""
    print("\n" + "="*60)
    print("🎉 CAMEL多智能体旅游导航系统演示完成!")
    print("="*60)
    print()
    print("📋 演示内容:")
    print("✅ 多智能体协作框架")
    print("✅ 需求分析和理解")
    print("✅ 智能景点搜索")
    print("✅ 内容自动生成")
    print("✅ 媒体资源管理")
    print("✅ 相册智能组织")
    print("✅ 系统健康监控")
    print()
    print("🔧 技术特性:")
    print("• 基于CAMEL框架的多智能体协作")
    print("• 异步并行处理提升性能")
    print("• 模块化设计便于扩展")
    print("• 智能内容生成和资源管理")
    print("• 完整的错误处理和监控")
    print()
    print("🚀 下一步:")
    print("• 配置真实的API密钥以启用完整功能")
    print("• 部署到生产环境")
    print("• 集成更多数据源和媒体服务")
    print("• 添加用户认证和个性化功能")
    print()
    print("📖 详细文档请参阅: CAMEL_SYSTEM_README.md")
    print("="*60)


async def main():
    """主演示函数"""
    print("🌟 CAMEL多智能体旅游导航系统演示")
    print("="*60)
    print("这是一个演示版本，展示系统的核心功能和架构")
    print("无需配置API密钥即可体验完整的工作流程")
    print("="*60)
    
    try:
        # 演示各个组件
        await demo_individual_agents()
        await demo_full_workflow()
        await demo_health_check()
        
        # 打印总结
        print_demo_summary()
        
    except KeyboardInterrupt:
        print("\n\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())