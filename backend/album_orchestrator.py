"""
多智能体协作流程编排器

实现CAMEL多智能体系统的协作流程，用于一句话生成旅游导航图相册
"""

import os
import json
import logging
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

from camel_agents import (
    RequirementAnalyst, 
    AttractionHunter, 
    ContentCreator, 
    MediaManager, 
    AlbumOrganizer
)
from vector_database import get_vector_database
from supabase_client import supabase_client

logger = logging.getLogger(__name__)


class AlbumGenerationOrchestrator:
    """相册生成编排器"""
    
    def __init__(self):
        # 初始化各个智能体
        self.requirement_analyst = RequirementAnalyst()
        self.attraction_hunter = AttractionHunter(supabase_client)
        self.content_creator = ContentCreator()
        self.media_manager = MediaManager()
        self.album_organizer = AlbumOrganizer(supabase_client)
        
        # 向量数据库
        self.vector_db = get_vector_database()
        
        logger.info("多智能体协作编排器初始化完成")
    
    async def generate_album_from_prompt(self, user_prompt: str, user_id: str = None) -> Dict:
        """
        从用户一句话输入生成旅游相册
        
        Args:
            user_prompt: 用户的一句话描述
            user_id: 用户ID（可选）
            
        Returns:
            生成的相册数据
        """
        try:
            logger.info(f"开始处理用户请求：{user_prompt}")
            
            # 生成用户ID（如果未提供）
            if not user_id:
                user_id = f"user_{uuid.uuid4().hex[:8]}"
            
            # 步骤1: 需求分析
            logger.info("步骤1: 需求分析师分析用户需求")
            requirements = await self.requirement_analyst.analyze_user_input(user_prompt)
            
            if not requirements or 'error' in requirements:
                logger.error(f"需求分析失败: {requirements}")
                return {
                    'success': False,
                    'error': '需求分析失败',
                    'details': requirements
                }
            
            logger.info(f"需求分析完成: {json.dumps(requirements, ensure_ascii=False, indent=2)}")
            
            # 步骤2: 景点搜索
            logger.info("步骤2: 景点搜索专家搜索相关景点")
            attractions = await self.attraction_hunter.search_attractions(requirements)
            
            if not attractions:
                logger.warning("未找到匹配的景点，尝试向量搜索")
                # 使用向量搜索作为备选方案
                destination = requirements.get('destination', '')
                interests_text = ', '.join(requirements.get('interests', []))
                search_query = f"{destination} {interests_text} {user_prompt}"
                
                vector_results = await self.vector_db.similarity_search(
                    search_query, limit=5, threshold=0.6
                )
                
                # 转换向量搜索结果
                attractions = self._convert_vector_results_to_attractions(vector_results)
            
            if not attractions:
                logger.error("未找到任何匹配的景点")
                return {
                    'success': False,
                    'error': '未找到匹配的景点',
                    'requirements': requirements
                }
            
            logger.info(f"找到 {len(attractions)} 个景点")
            
            # 步骤3: 并行处理内容创作和媒体资源获取
            logger.info("步骤3: 并行处理内容创作和媒体资源")
            enhanced_attractions = await self._enhance_attractions_parallel(
                attractions, requirements
            )
            
            # 步骤4: 相册组织
            logger.info("步骤4: 相册组织者创建最终相册")
            album = await self.album_organizer.create_album(
                enhanced_attractions, requirements, user_id
            )
            
            if not album:
                logger.error("相册创建失败")
                return {
                    'success': False,
                    'error': '相册创建失败'
                }
            
            # 添加处理信息
            album['processing_info'] = {
                'user_prompt': user_prompt,
                'requirements': requirements,
                'processing_time': datetime.now().isoformat(),
                'agent_results': {
                    'requirement_analysis': 'completed',
                    'attraction_search': f'{len(attractions)} attractions found',
                    'content_creation': f'{len(enhanced_attractions)} attractions enhanced',
                    'album_organization': 'completed'
                }
            }
            
            logger.info(f"相册生成完成：{album.get('title', '未命名相册')}")
            
            return {
                'success': True,
                'album': album,
                'user_id': user_id
            }
            
        except Exception as e:
            logger.error(f"相册生成失败: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'error': f'相册生成失败: {str(e)}'
            }
    
    async def _enhance_attractions_parallel(self, attractions: List[Dict], requirements: Dict) -> List[Dict]:
        """并行处理景点增强（内容创作和媒体资源）"""
        try:
            enhanced_attractions = []
            
            # 创建并行任务
            tasks = []
            for attraction in attractions:
                task = self._enhance_single_attraction(attraction, requirements)
                tasks.append(task)
            
            # 执行并行任务
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"景点增强失败 {attractions[i].get('name', 'Unknown')}: {result}")
                    # 使用原始景点数据
                    enhanced_attractions.append(attractions[i])
                else:
                    enhanced_attractions.append(result)
            
            return enhanced_attractions
            
        except Exception as e:
            logger.error(f"并行处理景点增强失败: {e}")
            return attractions
    
    async def _enhance_single_attraction(self, attraction: Dict, requirements: Dict) -> Dict:
        """增强单个景点信息"""
        try:
            # 并行执行内容创作和媒体资源获取
            content_task = self.content_creator.generate_content(attraction, requirements)
            media_task = self.media_manager.fetch_media_resources(attraction)
            
            content_result, media_result = await asyncio.gather(
                content_task, media_task, return_exceptions=True
            )
            
            # 合并结果
            enhanced_attraction = attraction.copy()
            
            # 添加内容创作结果
            if not isinstance(content_result, Exception) and content_result:
                enhanced_attraction.update(content_result)
            else:
                logger.warning(f"内容创作失败 {attraction.get('name', 'Unknown')}: {content_result}")
            
            # 添加媒体资源结果
            if not isinstance(media_result, Exception) and media_result:
                enhanced_attraction.update(media_result)
                # 如果没有原始图片，使用媒体管理员提供的图片
                if not enhanced_attraction.get('image') and media_result.get('images'):
                    enhanced_attraction['image'] = media_result['images'][0]['url']
            else:
                logger.warning(f"媒体资源获取失败 {attraction.get('name', 'Unknown')}: {media_result}")
            
            return enhanced_attraction
            
        except Exception as e:
            logger.error(f"增强景点信息失败 {attraction.get('name', 'Unknown')}: {e}")
            return attraction
    
    def _convert_vector_results_to_attractions(self, vector_results: List[Dict]) -> List[Dict]:
        """将向量搜索结果转换为景点格式"""
        attractions = []
        
        for result in vector_results:
            attraction = {
                'id': result.get('attraction_id'),
                'name': result.get('name', '未知景点'),
                'latitude': result.get('latitude', 0),
                'longitude': result.get('longitude', 0),
                'category': result.get('category', '景点'),
                'country': result.get('country', ''),
                'city': result.get('city', ''),
                'address': result.get('address', ''),
                'description': result.get('content_text', ''),
                'image': result.get('main_image_url'),
                'opening_hours': '详询景点',
                'ticket_price': '详询景点',
                'booking_method': '现场购票',
                'relevance_score': result.get('similarity', 0)
            }
            
            attractions.append(attraction)
        
        return attractions
    
    async def generate_quick_recommendations(self, location: tuple, interests: List[str], limit: int = 5) -> Dict:
        """
        快速生成景点推荐（不需要完整的相册生成流程）
        
        Args:
            location: (latitude, longitude) 用户位置
            interests: 兴趣类型列表
            limit: 推荐数量限制
            
        Returns:
            推荐结果
        """
        try:
            logger.info(f"生成快速推荐：位置={location}, 兴趣={interests}")
            
            # 构建搜索查询
            interests_text = ', '.join(interests) if interests else '旅游景点'
            
            # 使用向量搜索
            vector_results = await self.vector_db.search_attractions_by_semantic(
                query=interests_text,
                location=location,
                radius_km=50,
                limit=limit
            )
            
            if not vector_results:
                # 备选：使用传统搜索
                nearby_attractions = supabase_client.get_attractions_near_location(
                    location[0], location[1], radius_km=50
                )
                vector_results = nearby_attractions[:limit]
            
            # 转换格式
            recommendations = []
            for result in vector_results:
                recommendation = {
                    'name': result.get('name', '未知景点'),
                    'category': result.get('category', '景点'),
                    'description': result.get('content_text') or result.get('description', ''),
                    'image': result.get('main_image_url') or result.get('image'),
                    'distance': result.get('distance_km') or result.get('distance', 0),
                    'similarity': result.get('similarity', 0),
                    'latitude': result.get('latitude'),
                    'longitude': result.get('longitude')
                }
                recommendations.append(recommendation)
            
            return {
                'success': True,
                'recommendations': recommendations,
                'location': location,
                'interests': interests
            }
            
        except Exception as e:
            logger.error(f"快速推荐生成失败: {e}")
            return {
                'success': False,
                'error': f'推荐生成失败: {str(e)}'
            }
    
    async def health_check(self) -> Dict:
        """健康检查"""
        try:
            health_status = {
                'orchestrator': 'healthy',
                'agents': {},
                'vector_db': 'unknown',
                'supabase': 'unknown'
            }
            
            # 检查各个智能体
            agents = [
                ('requirement_analyst', self.requirement_analyst),
                ('attraction_hunter', self.attraction_hunter),
                ('content_creator', self.content_creator),
                ('media_manager', self.media_manager),
                ('album_organizer', self.album_organizer)
            ]
            
            for agent_name, agent in agents:
                try:
                    # 简单的健康检查
                    if hasattr(agent, 'role_name'):
                        health_status['agents'][agent_name] = 'healthy'
                    else:
                        health_status['agents'][agent_name] = 'error'
                except Exception as e:
                    health_status['agents'][agent_name] = f'error: {str(e)}'
            
            # 检查向量数据库
            try:
                if self.vector_db:
                    health_status['vector_db'] = 'healthy'
                else:
                    health_status['vector_db'] = 'not_initialized'
            except Exception as e:
                health_status['vector_db'] = f'error: {str(e)}'
            
            # 检查Supabase
            try:
                test_result = await supabase_client.test_connection()
                health_status['supabase'] = 'healthy' if test_result else 'error'
            except Exception as e:
                health_status['supabase'] = f'error: {str(e)}'
            
            # 总体状态
            all_healthy = (
                health_status['orchestrator'] == 'healthy' and
                all(status == 'healthy' for status in health_status['agents'].values()) and
                health_status['vector_db'] == 'healthy' and
                health_status['supabase'] == 'healthy'
            )
            
            health_status['overall'] = 'healthy' if all_healthy else 'degraded'
            
            return health_status
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                'overall': 'error',
                'error': str(e)
            }


# 全局编排器实例
album_orchestrator = None

def get_album_orchestrator() -> AlbumGenerationOrchestrator:
    """获取相册生成编排器实例"""
    global album_orchestrator
    if album_orchestrator is None:
        album_orchestrator = AlbumGenerationOrchestrator()
    return album_orchestrator