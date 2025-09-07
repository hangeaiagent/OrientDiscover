"""
CAMEL多智能体旅游导航系统

实现基于CAMEL框架的多智能体协作，用于一句话生成旅游导航图
包含：需求分析师、景点搜索专家、内容创作者、媒体管理员、相册组织者
"""

import os
import json
import logging
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import openai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class BaseAgent:
    """基础智能体类"""
    
    def __init__(self, role_name: str, role_description: str, system_prompt: str):
        self.role_name = role_name
        self.role_description = role_description
        self.system_prompt = system_prompt
        self.conversation_history = []
        
        # OpenAI客户端
        self.openai_client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    async def generate_response(self, user_input: str, context: Dict = None) -> str:
        """生成智能体响应"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # 添加上下文信息
            if context:
                context_msg = f"上下文信息：{json.dumps(context, ensure_ascii=False, indent=2)}"
                messages.append({"role": "system", "content": context_msg})
            
            # 添加历史对话
            messages.extend(self.conversation_history[-5:])  # 保留最近5轮对话
            
            # 添加当前用户输入
            messages.append({"role": "user", "content": user_input})
            
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4-turbo-preview",
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            assistant_message = response.choices[0].message.content
            
            # 更新对话历史
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"{self.role_name} 生成响应失败: {e}")
            return f"抱歉，{self.role_name}暂时无法处理您的请求。"
    
    def parse_json_response(self, response: str) -> Dict:
        """解析JSON响应"""
        try:
            # 尝试提取JSON部分
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # 如果没有找到JSON，返回基本结构
                return {"error": "无法解析JSON响应", "raw_response": response}
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return {"error": f"JSON解析错误: {e}", "raw_response": response}


class RequirementAnalyst(BaseAgent):
    """需求分析师智能体"""
    
    def __init__(self):
        system_prompt = """
你是一位专业的旅游需求分析师，擅长从用户的一句话描述中提取关键旅游信息。

你的任务是：
1. 分析用户输入，提取目的地、兴趣类型、时间偏好、预算等信息
2. 识别用户的潜在需求和偏好
3. 生成结构化的需求描述

请始终以JSON格式返回分析结果，包含以下字段：
- destination: 目的地/城市
- interests: 兴趣类型列表（如：历史文化、自然风光、美食购物、现代建筑等）
- time_preference: 时间安排（如：一日游、周末、假期等）
- budget_range: 预算范围（如：经济、中等、高端）
- special_requirements: 特殊需求
- travel_style: 旅行风格（如：休闲、探险、文化、购物等）
- group_type: 群体类型（如：个人、情侣、家庭、朋友等）
- season: 季节偏好
- description: 需求总结描述

分析时要考虑：
- 从关键词推断隐含需求
- 识别情感色彩和期望
- 考虑实际可行性
"""
        
        super().__init__(
            role_name="需求分析师",
            role_description="专业的旅游需求分析专家，擅长从用户描述中提取关键旅游信息",
            system_prompt=system_prompt
        )
    
    async def analyze_user_input(self, user_input: str) -> Dict:
        """分析用户输入的旅游需求"""
        prompt = f"""
请分析以下用户的旅游需求：

用户输入："{user_input}"

请提取并分析用户的旅游需求，返回详细的JSON格式分析结果。
"""
        
        response = await self.generate_response(prompt)
        return self.parse_json_response(response)


class AttractionHunter(BaseAgent):
    """景点搜索专家智能体"""
    
    def __init__(self, supabase_client, web_scraper=None):
        system_prompt = """
你是一位专业的景点搜索和信息获取专家。

你的任务是：
1. 基于用户需求在数据库中搜索匹配的景点
2. 评估现有景点信息的完整性和质量
3. 决定是否需要获取更多景点信息
4. 对景点进行相关性评分和排序

你需要考虑：
- 地理位置匹配度
- 兴趣类型匹配度
- 预算适合度
- 时间安排合理性
- 季节适宜性

请始终提供详细的搜索策略和结果分析。
"""
        
        super().__init__(
            role_name="景点搜索专家",
            role_description="专业的景点信息搜索和获取专家",
            system_prompt=system_prompt
        )
        
        self.supabase_client = supabase_client
        self.web_scraper = web_scraper
    
    async def search_attractions(self, requirements: Dict) -> List[Dict]:
        """基于需求搜索景点"""
        try:
            destination = requirements.get('destination', '')
            interests = requirements.get('interests', [])
            
            logger.info(f"景点搜索专家开始搜索：目的地={destination}, 兴趣={interests}")
            
            # 1. 从数据库搜索现有景点
            existing_attractions = []
            
            if destination:
                # 按城市搜索
                city_attractions = self.supabase_client.get_attractions_by_city(destination)
                existing_attractions.extend(city_attractions)
                
                # 模糊搜索
                search_attractions = self.supabase_client.search_attractions(destination)
                for attr in search_attractions:
                    if attr not in existing_attractions:
                        existing_attractions.append(attr)
            
            # 2. 按兴趣类型过滤
            if interests:
                filtered_attractions = []
                for attraction in existing_attractions:
                    attraction_category = attraction.get('category', '').lower()
                    attraction_desc = attraction.get('description', '').lower()
                    
                    # 检查是否匹配兴趣类型
                    for interest in interests:
                        interest_lower = interest.lower()
                        if (interest_lower in attraction_category or 
                            interest_lower in attraction_desc or
                            self._interest_matches_category(interest, attraction_category)):
                            
                            attraction['relevance_score'] = self._calculate_relevance_score(
                                attraction, requirements
                            )
                            filtered_attractions.append(attraction)
                            break
                
                existing_attractions = filtered_attractions
            
            # 3. 按相关性排序
            existing_attractions.sort(
                key=lambda x: x.get('relevance_score', 0), 
                reverse=True
            )
            
            # 4. 限制返回数量
            return existing_attractions[:10]
            
        except Exception as e:
            logger.error(f"景点搜索失败: {e}")
            return []
    
    def _interest_matches_category(self, interest: str, category: str) -> bool:
        """判断兴趣是否匹配景点类别"""
        interest_mapping = {
            '历史文化': ['文化古迹', '博物馆', '历史', '古建筑', '寺庙'],
            '自然风光': ['自然景观', '公园', '山水', '森林', '湖泊'],
            '现代建筑': ['城市地标', '建筑', '摩天大楼', '现代'],
            '美食购物': ['商业区', '购物', '美食', '市场'],
            '休闲娱乐': ['娱乐', '休闲', '度假', '温泉']
        }
        
        interest_lower = interest.lower()
        category_lower = category.lower()
        
        for key, values in interest_mapping.items():
            if interest_lower in key.lower():
                return any(value in category_lower for value in values)
        
        return False
    
    def _calculate_relevance_score(self, attraction: Dict, requirements: Dict) -> float:
        """计算景点与需求的相关性评分"""
        score = 0.0
        
        # 基础分数
        score += 1.0
        
        # 兴趣匹配加分
        interests = requirements.get('interests', [])
        category = attraction.get('category', '').lower()
        description = attraction.get('description', '').lower()
        
        for interest in interests:
            if interest.lower() in category or interest.lower() in description:
                score += 2.0
            elif self._interest_matches_category(interest, category):
                score += 1.5
        
        # 有图片加分
        if attraction.get('image'):
            score += 0.5
        
        # 有详细描述加分
        if len(attraction.get('description', '')) > 50:
            score += 0.3
        
        return score


class ContentCreator(BaseAgent):
    """内容创作者智能体"""
    
    def __init__(self):
        system_prompt = """
你是一位专业的旅游内容创作专家，擅长生成引人入胜的景点介绍和导游词。

你的任务是：
1. 为景点生成详细的介绍文案
2. 创作生动有趣的导游解说词
3. 提供实用的游览建议和注意事项
4. 支持多语言内容生成

你的写作风格应该：
- 生动有趣，富有感染力
- 准确详实，包含文化内涵
- 实用性强，提供有价值的信息
- 语言流畅，易于理解

请始终以JSON格式返回内容，包含以下字段：
- detailed_description: 详细景点介绍（300-500字）
- guide_commentary: 导游解说词（200-300字）
- visit_tips: 游览建议
- best_time: 最佳游览时间
- duration: 建议游览时长
- highlights: 景点亮点
- cultural_background: 文化背景
- photo_spots: 最佳拍照点
"""
        
        super().__init__(
            role_name="内容创作者",
            role_description="专业的旅游内容创作专家，擅长生成引人入胜的景点介绍和导游词",
            system_prompt=system_prompt
        )
    
    async def generate_content(self, attraction: Dict, requirements: Dict = None) -> Dict:
        """为景点生成内容"""
        attraction_name = attraction.get('name', '未知景点')
        attraction_category = attraction.get('category', '景点')
        attraction_city = attraction.get('city', '')
        attraction_description = attraction.get('description', '')
        
        prompt = f"""
请为以下景点生成高质量的旅游内容：

景点名称：{attraction_name}
景点类别：{attraction_category}
所在城市：{attraction_city}
基础描述：{attraction_description}

用户需求背景：{json.dumps(requirements, ensure_ascii=False) if requirements else '无特殊要求'}

请生成包含详细介绍、导游词、游览建议等完整内容的JSON响应。
内容要求：
1. 详细介绍要有文化深度和历史背景
2. 导游词要生动有趣，有故事性
3. 游览建议要实用具体
4. 突出景点的独特魅力和价值
"""
        
        response = await self.generate_response(prompt)
        return self.parse_json_response(response)


class MediaManager(BaseAgent):
    """媒体资源管理员智能体"""
    
    def __init__(self, cloud_storage_service=None):
        system_prompt = """
你是一位专业的媒体资源获取和管理专家。

你的任务是：
1. 搜索和获取高质量的景点图片
2. 查找相关的视频资源
3. 管理媒体资源的存储和优化
4. 评估媒体资源的质量和适用性

你需要考虑：
- 图片质量和分辨率
- 版权和使用许可
- 内容的相关性和准确性
- 文件大小和加载速度
- 多样性和代表性

请提供详细的媒体资源获取策略和质量评估。
"""
        
        super().__init__(
            role_name="媒体资源管理员",
            role_description="专业的媒体资源获取和管理专家",
            system_prompt=system_prompt
        )
        
        self.cloud_storage_service = cloud_storage_service
        
        # 导入增强媒体管理器
        try:
            from media_service_enhanced import get_enhanced_media_manager
            self.enhanced_manager = get_enhanced_media_manager()
        except ImportError:
            self.enhanced_manager = None
            logger.warning("增强媒体管理器不可用，使用基础实现")
    
    async def fetch_media_resources(self, attraction: Dict) -> Dict:
        """获取景点的媒体资源"""
        try:
            attraction_name = attraction.get('name', '')
            attraction_city = attraction.get('city', '')
            
            logger.info(f"媒体管理员开始获取资源：{attraction_name}")
            
            # 使用增强媒体管理器
            if self.enhanced_manager:
                media_resources = await self.enhanced_manager.fetch_media_resources(attraction)
                
                # 处理并存储媒体资源
                processed_resources = await self.enhanced_manager.process_and_store_media(media_resources)
                
                # 获取媒体分析
                analytics = await self.enhanced_manager.get_media_analytics(processed_resources)
                processed_resources['analytics'] = analytics
                
                return processed_resources
            
            # 备用基础实现
            return await self._fetch_basic_media_resources(attraction)
            
        except Exception as e:
            logger.error(f"获取媒体资源失败: {e}")
            return await self._fetch_basic_media_resources(attraction)
    
    async def _fetch_basic_media_resources(self, attraction: Dict) -> Dict:
        """基础媒体资源获取"""
        try:
            attraction_name = attraction.get('name', '')
            
            # 基础媒体资源获取
            media_resources = {
                'images': [
                    {
                        'url': attraction.get('image') or 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800',
                        'description': f'{attraction_name}景观',
                        'quality': 'medium',
                        'size': '800x600',
                        'source': 'default'
                    }
                ],
                'videos': [],
                'thumbnails': []
            }
            
            # 如果没有现有图片，生成默认图片URL
            if not attraction.get('image'):
                category = attraction.get('category', '景点')
                default_images = self._get_default_images_by_category(category)
                media_resources['images'] = default_images
            
            # 生成缩略图
            for img in media_resources['images']:
                thumbnail = {
                    'url': img['url'].replace('w=800', 'w=400'),
                    'description': img['description'],
                    'size': 'small'
                }
                media_resources['thumbnails'].append(thumbnail)
            
            return media_resources
            
        except Exception as e:
            logger.error(f"基础媒体资源获取失败: {e}")
            return {'images': [], 'videos': [], 'thumbnails': []}
    
    def _get_default_images_by_category(self, category: str) -> List[Dict]:
        """根据景点类别获取默认图片"""
        category_images = {
            '自然景观': [
                {
                    'url': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800',
                    'description': '自然风光',
                    'quality': 'high',
                    'size': '800x600'
                }
            ],
            '文化古迹': [
                {
                    'url': 'https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=800',
                    'description': '文化古迹',
                    'quality': 'high',
                    'size': '800x600'
                }
            ],
            '城市地标': [
                {
                    'url': 'https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=800',
                    'description': '城市地标',
                    'quality': 'high',
                    'size': '800x600'
                }
            ]
        }
        
        return category_images.get(category, category_images['自然景观'])


class AlbumOrganizer(BaseAgent):
    """相册组织者智能体"""
    
    def __init__(self, supabase_client):
        system_prompt = """
你是一位专业的旅游相册组织专家。

你的任务是：
1. 整合所有景点信息生成相册
2. 优化景点排序和路线规划
3. 生成相册的元数据和描述
4. 创建吸引人的相册标题和封面

你需要考虑：
- 地理位置的合理性
- 游览路线的优化
- 时间安排的可行性
- 内容的丰富性和多样性
- 用户体验的流畅性

请提供详细的相册组织策略和最终结果。
"""
        
        super().__init__(
            role_name="相册组织者",
            role_description="专业的旅游相册组织和路线规划专家",
            system_prompt=system_prompt
        )
        
        self.supabase_client = supabase_client
    
    async def create_album(self, attractions: List[Dict], requirements: Dict, creator_id: str) -> Dict:
        """创建旅游相册"""
        try:
            destination = requirements.get('destination', '未知目的地')
            interests = requirements.get('interests', [])
            
            # 生成相册标题
            album_title = await self._generate_album_title(destination, interests, requirements)
            
            # 生成相册描述
            album_description = await self._generate_album_description(attractions, requirements)
            
            # 优化景点排序
            optimized_attractions = self._optimize_attraction_order(attractions)
            
            # 创建相册数据结构
            album_data = {
                'title': album_title,
                'description': album_description,
                'destination': destination,
                'creator_id': creator_id,
                'attractions': optimized_attractions,
                'metadata': {
                    'total_attractions': len(optimized_attractions),
                    'categories': list(set(attr.get('category', '') for attr in optimized_attractions)),
                    'estimated_duration': self._calculate_total_duration(optimized_attractions),
                    'difficulty_level': self._assess_difficulty_level(optimized_attractions),
                    'best_season': self._determine_best_season(optimized_attractions),
                    'budget_estimate': self._estimate_budget(optimized_attractions)
                },
                'created_at': datetime.now().isoformat()
            }
            
            # 保存到数据库（如果需要）
            # saved_album = self.supabase_client.create_album(
            #     creator_id, album_title, album_description
            # )
            
            logger.info(f"相册创建完成：{album_title}，包含{len(optimized_attractions)}个景点")
            
            return album_data
            
        except Exception as e:
            logger.error(f"创建相册失败: {e}")
            return {}
    
    async def _generate_album_title(self, destination: str, interests: List[str], requirements: Dict) -> str:
        """生成相册标题"""
        prompt = f"""
请为以下旅游相册生成一个吸引人的标题：

目的地：{destination}
兴趣类型：{', '.join(interests)}
旅行风格：{requirements.get('travel_style', '休闲')}

要求：
1. 标题要简洁有力，不超过20个字
2. 体现目的地特色和旅行主题
3. 具有吸引力和记忆点
4. 适合作为相册封面标题

请只返回标题文本，不需要其他内容。
"""
        
        response = await self.generate_response(prompt)
        # 提取标题（去除多余的引号和格式）
        title = response.strip().strip('"').strip("'")
        return title[:20]  # 确保不超过20个字符
    
    async def _generate_album_description(self, attractions: List[Dict], requirements: Dict) -> str:
        """生成相册描述"""
        attraction_names = [attr.get('name', '') for attr in attractions[:5]]  # 取前5个
        
        prompt = f"""
请为包含以下景点的旅游相册生成一段描述：

主要景点：{', '.join(attraction_names)}
总景点数：{len(attractions)}
用户需求：{requirements.get('description', '探索之旅')}

要求：
1. 描述要生动有趣，激发旅游欲望
2. 突出行程的特色和亮点
3. 长度控制在100-150字
4. 语言要优美流畅

请只返回描述文本。
"""
        
        response = await self.generate_response(prompt)
        return response.strip()
    
    def _optimize_attraction_order(self, attractions: List[Dict]) -> List[Dict]:
        """优化景点排序"""
        # 简单的排序策略：按相关性评分排序
        return sorted(
            attractions, 
            key=lambda x: x.get('relevance_score', 0), 
            reverse=True
        )
    
    def _calculate_total_duration(self, attractions: List[Dict]) -> str:
        """计算总游览时长"""
        # 简单估算：每个景点2小时
        total_hours = len(attractions) * 2
        
        if total_hours <= 8:
            return f"{total_hours}小时（一日游）"
        elif total_hours <= 16:
            return f"{total_hours}小时（两日游）"
        else:
            days = (total_hours + 7) // 8  # 向上取整
            return f"{days}天"
    
    def _assess_difficulty_level(self, attractions: List[Dict]) -> str:
        """评估难度等级"""
        # 简单评估：根据景点类型判断
        categories = [attr.get('category', '') for attr in attractions]
        
        if any('山' in cat or '徒步' in cat for cat in categories):
            return "中等"
        else:
            return "轻松"
    
    def _determine_best_season(self, attractions: List[Dict]) -> str:
        """确定最佳季节"""
        # 简单判断：根据景点类型
        categories = [attr.get('category', '') for attr in attractions]
        
        if any('自然' in cat for cat in categories):
            return "春秋两季"
        else:
            return "四季皆宜"
    
    def _estimate_budget(self, attractions: List[Dict]) -> str:
        """估算预算"""
        # 简单估算：根据门票价格
        total_tickets = 0
        for attr in attractions:
            ticket_price = attr.get('ticket_price', '')
            if '免费' in ticket_price:
                continue
            elif '元' in ticket_price:
                try:
                    # 提取数字
                    price = ''.join(filter(str.isdigit, ticket_price))
                    if price:
                        total_tickets += int(price)
                except:
                    total_tickets += 50  # 默认50元
            else:
                total_tickets += 50
        
        if total_tickets < 200:
            return "经济型（200元以下）"
        elif total_tickets < 500:
            return "中等型（200-500元）"
        else:
            return "高端型（500元以上）"


# 多智能体协作编排器将在下一个文件中实现