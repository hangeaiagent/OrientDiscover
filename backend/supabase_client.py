# Supabase客户端配置
# Supabase Client Configuration

import os
import logging
from typing import List, Dict, Optional, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import asyncio
import json
from datetime import datetime
import uuid

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Supabase数据库客户端"""
    
    def __init__(self):
        """初始化Supabase客户端"""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("缺少必要的Supabase环境变量：SUPABASE_URL 和 SUPABASE_ANON_KEY")
        
        # 创建客户端
        self.client: Client = create_client(self.url, self.key)
        
        # 如果有service_role_key，创建管理员客户端
        if self.service_role_key:
            self.admin_client: Client = create_client(self.url, self.service_role_key)
        else:
            self.admin_client = self.client
        
        logger.info("Supabase客户端初始化成功")
    
    async def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            # 尝试查询一个简单的表来测试连接
            result = self.client.table('spot_attractions').select('count').execute()
            logger.info("Supabase连接测试成功")
            return True
        except Exception as e:
            logger.error(f"Supabase连接测试失败: {e}")
            return False
    
    # ==================== 景点相关方法 ====================
    
    def get_attractions_near_location(self, latitude: float, longitude: float, radius_km: float = 50) -> List[Dict]:
        """获取指定位置附近的景点"""
        try:
            # 使用PostGIS的ST_DWithin函数查询附近景点
            # 注意：这里使用地理坐标系，单位是米
            radius_meters = radius_km * 1000
            
            # 构建查询
            query = f"""
            SELECT 
                a.*,
                ST_X(a.location) as longitude,
                ST_Y(a.location) as latitude,
                ST_Distance(
                    a.location::geography, 
                    ST_SetSRID(ST_MakePoint({longitude}, {latitude}), 4326)::geography
                ) as distance_meters
            FROM spot_attractions a
            WHERE ST_DWithin(
                a.location::geography,
                ST_SetSRID(ST_MakePoint({longitude}, {latitude}), 4326)::geography,
                {radius_meters}
            )
            ORDER BY distance_meters
            """
            
            result = self.client.rpc('execute_sql', {'query': query}).execute()
            
            if result.data:
                attractions = []
                for row in result.data:
                    # 获取多语言内容
                    content_result = self.client.table('spot_attraction_contents')\
                        .select('*')\
                        .eq('attraction_id', row['id'])\
                        .eq('language_code', 'zh-CN')\
                        .execute()
                    
                    # 获取媒体资源
                    media_result = self.client.table('spot_attraction_media')\
                        .select('*')\
                        .eq('attraction_id', row['id'])\
                        .order('order_index')\
                        .execute()
                    
                    attraction = {
                        'id': row['id'],
                        'name': row['name'],
                        'latitude': row['latitude'],
                        'longitude': row['longitude'],
                        'category': row['category'],
                        'country': row['country'],
                        'city': row['city'],
                        'address': row['address'],
                        'opening_hours': row['opening_hours'],
                        'ticket_price': row['ticket_price'],
                        'booking_method': row['booking_method'],
                        'distance': round(row['distance_meters'] / 1000, 2),  # 转换为公里
                        'description': '',
                        'image': row['main_image_url'],
                        'video': row['video_url']
                    }
                    
                    # 添加多语言内容
                    if content_result.data:
                        content = content_result.data[0]
                        attraction['description'] = content.get('description', '')
                        attraction['attraction_introduction'] = content.get('attraction_introduction', '')
                        attraction['guide_commentary'] = content.get('guide_commentary', '')
                    
                    # 添加媒体资源
                    if media_result.data:
                        attraction['media'] = media_result.data
                        # 如果没有主图片，使用第一个图片
                        if not attraction['image'] and media_result.data:
                            for media in media_result.data:
                                if media['media_type'] == 'image':
                                    attraction['image'] = media['url']
                                    break
                    
                    attractions.append(attraction)
                
                return attractions
            
            return []
            
        except Exception as e:
            logger.error(f"查询附近景点失败: {e}")
            # 如果RPC调用失败，尝试使用基本查询
            return self._get_attractions_near_location_fallback(latitude, longitude, radius_km)
    
    def _get_attractions_near_location_fallback(self, latitude: float, longitude: float, radius_km: float) -> List[Dict]:
        """备用的附近景点查询方法"""
        try:
            # 简单的边界框查询作为备用方案
            lat_range = radius_km / 111.0  # 大约每度111公里
            lng_range = radius_km / (111.0 * abs(latitude * 3.14159 / 180))  # 考虑纬度影响
            
            result = self.client.table('spot_attractions')\
                .select('*, ST_X(location) as longitude, ST_Y(location) as latitude')\
                .execute()
            
            if result.data:
                attractions = []
                for row in result.data:
                    # 简单距离计算
                    lat_diff = abs(row['latitude'] - latitude)
                    lng_diff = abs(row['longitude'] - longitude)
                    
                    if lat_diff <= lat_range and lng_diff <= lng_range:
                        # 计算更精确的距离
                        distance = self._calculate_distance(
                            latitude, longitude, 
                            row['latitude'], row['longitude']
                        )
                        
                        if distance <= radius_km:
                            attraction = {
                                'id': row['id'],
                                'name': row['name'],
                                'latitude': row['latitude'],
                                'longitude': row['longitude'],
                                'category': row['category'],
                                'country': row['country'],
                                'city': row['city'],
                                'address': row['address'],
                                'opening_hours': row['opening_hours'],
                                'ticket_price': row['ticket_price'],
                                'booking_method': row['booking_method'],
                                'distance': distance,
                                'description': '',
                                'image': row['main_image_url'],
                                'video': row['video_url']
                            }
                            attractions.append(attraction)
                
                # 按距离排序
                attractions.sort(key=lambda x: x['distance'])
                return attractions
            
            return []
            
        except Exception as e:
            logger.error(f"备用查询附近景点也失败: {e}")
            return []
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """使用Haversine公式计算两点间距离（公里）"""
        import math
        
        R = 6371  # 地球半径（公里）
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def get_all_attractions(self) -> List[Dict]:
        """获取所有景点"""
        try:
            result = self.client.table('spot_attractions')\
                .select('*, ST_X(location) as longitude, ST_Y(location) as latitude')\
                .execute()
            
            if result.data:
                attractions = []
                for row in result.data:
                    # 获取多语言内容
                    content_result = self.client.table('spot_attraction_contents')\
                        .select('*')\
                        .eq('attraction_id', row['id'])\
                        .eq('language_code', 'zh-CN')\
                        .execute()
                    
                    attraction = {
                        'id': row['id'],
                        'name': row['name'],
                        'latitude': row['latitude'],
                        'longitude': row['longitude'],
                        'category': row['category'],
                        'country': row['country'],
                        'city': row['city'],
                        'address': row['address'],
                        'opening_hours': row['opening_hours'],
                        'ticket_price': row['ticket_price'],
                        'booking_method': row['booking_method'],
                        'description': '',
                        'image': row['main_image_url'],
                        'video': row['video_url']
                    }
                    
                    # 添加多语言内容
                    if content_result.data:
                        content = content_result.data[0]
                        attraction['description'] = content.get('description', '')
                        attraction['attraction_introduction'] = content.get('attraction_introduction', '')
                        attraction['guide_commentary'] = content.get('guide_commentary', '')
                    
                    attractions.append(attraction)
                
                return attractions
            
            return []
            
        except Exception as e:
            logger.error(f"获取所有景点失败: {e}")
            return []
    
    def get_attractions_by_category(self, category: str) -> List[Dict]:
        """根据类别获取景点"""
        try:
            result = self.client.table('spot_attractions')\
                .select('*, ST_X(location) as longitude, ST_Y(location) as latitude')\
                .eq('category', category)\
                .execute()
            
            if result.data:
                attractions = []
                for row in result.data:
                    attraction = {
                        'id': row['id'],
                        'name': row['name'],
                        'latitude': row['latitude'],
                        'longitude': row['longitude'],
                        'category': row['category'],
                        'country': row['country'],
                        'city': row['city'],
                        'address': row['address'],
                        'opening_hours': row['opening_hours'],
                        'ticket_price': row['ticket_price'],
                        'booking_method': row['booking_method'],
                        'description': '',
                        'image': row['main_image_url'],
                        'video': row['video_url']
                    }
                    attractions.append(attraction)
                
                return attractions
            
            return []
            
        except Exception as e:
            logger.error(f"根据类别获取景点失败: {e}")
            return []
    
    def get_attractions_by_city(self, city: str) -> List[Dict]:
        """根据城市获取景点"""
        try:
            result = self.client.table('spot_attractions')\
                .select('*, ST_X(location) as longitude, ST_Y(location) as latitude')\
                .eq('city', city)\
                .execute()
            
            if result.data:
                attractions = []
                for row in result.data:
                    # 获取多语言内容
                    content_result = self.client.table('spot_attraction_contents')\
                        .select('*')\
                        .eq('attraction_id', row['id'])\
                        .eq('language_code', 'zh-CN')\
                        .execute()
                    
                    attraction = {
                        'id': row['id'],
                        'name': row['name'],
                        'latitude': row['latitude'],
                        'longitude': row['longitude'],
                        'category': row['category'],
                        'country': row['country'],
                        'city': row['city'],
                        'address': row['address'],
                        'opening_hours': row['opening_hours'],
                        'ticket_price': row['ticket_price'],
                        'booking_method': row['booking_method'],
                        'description': '',
                        'image': row['main_image_url'],
                        'video': row['video_url']
                    }
                    
                    # 添加多语言内容
                    if content_result.data:
                        content = content_result.data[0]
                        attraction['description'] = content.get('description', '')
                    
                    attractions.append(attraction)
                
                return attractions
            
            return []
            
        except Exception as e:
            logger.error(f"根据城市获取景点失败: {e}")
            return []
    
    def search_attractions(self, query: str) -> List[Dict]:
        """搜索景点"""
        try:
            # 在景点名称和描述中搜索
            result = self.client.table('spot_attractions')\
                .select('*, ST_X(location) as longitude, ST_Y(location) as latitude')\
                .or_(f'name.ilike.%{query}%,address.ilike.%{query}%,city.ilike.%{query}%')\
                .execute()
            
            attractions = []
            if result.data:
                for row in result.data:
                    attraction = {
                        'id': row['id'],
                        'name': row['name'],
                        'latitude': row['latitude'],
                        'longitude': row['longitude'],
                        'category': row['category'],
                        'country': row['country'],
                        'city': row['city'],
                        'address': row['address'],
                        'opening_hours': row['opening_hours'],
                        'ticket_price': row['ticket_price'],
                        'booking_method': row['booking_method'],
                        'description': '',
                        'image': row['main_image_url'],
                        'video': row['video_url']
                    }
                    attractions.append(attraction)
            
            # 同时在多语言内容中搜索
            content_result = self.client.table('spot_attraction_contents')\
                .select('*, spot_attractions(*, ST_X(location) as longitude, ST_Y(location) as latitude)')\
                .or_(f'description.ilike.%{query}%,attraction_introduction.ilike.%{query}%')\
                .execute()
            
            if content_result.data:
                for row in content_result.data:
                    if row['spot_attractions']:
                        attraction_data = row['spot_attractions']
                        attraction = {
                            'id': attraction_data['id'],
                            'name': attraction_data['name'],
                            'latitude': attraction_data['latitude'],
                            'longitude': attraction_data['longitude'],
                            'category': attraction_data['category'],
                            'country': attraction_data['country'],
                            'city': attraction_data['city'],
                            'address': attraction_data['address'],
                            'opening_hours': attraction_data['opening_hours'],
                            'ticket_price': attraction_data['ticket_price'],
                            'booking_method': attraction_data['booking_method'],
                            'description': row.get('description', ''),
                            'image': attraction_data['main_image_url'],
                            'video': attraction_data['video_url']
                        }
                        
                        # 避免重复
                        if not any(a['id'] == attraction['id'] for a in attractions):
                            attractions.append(attraction)
            
            return attractions
            
        except Exception as e:
            logger.error(f"搜索景点失败: {e}")
            return []
    
    # ==================== 相册相关方法 ====================
    
    def create_album(self, creator_id: str, title: str, description: str = None, 
                    access_level: str = 'public') -> Optional[Dict]:
        """创建新相册"""
        try:
            result = self.client.table('spot_map_albums').insert({
                'creator_id': creator_id,
                'title': title,
                'description': description,
                'access_level': access_level
            }).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"创建相册失败: {e}")
            return None
    
    def get_public_albums(self, limit: int = 20, offset: int = 0) -> List[Dict]:
        """获取公开相册"""
        try:
            result = self.client.table('spot_map_albums')\
                .select('*')\
                .eq('access_level', 'public')\
                .order('created_at', desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"获取公开相册失败: {e}")
            return []
    
    def get_user_albums(self, user_id: str) -> List[Dict]:
        """获取用户的相册"""
        try:
            result = self.client.table('spot_map_albums')\
                .select('*')\
                .eq('creator_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"获取用户相册失败: {e}")
            return []
    
    # ==================== 统计方法 ====================
    
    def get_statistics(self) -> Dict:
        """获取数据库统计信息"""
        try:
            stats = {}
            
            # 景点总数
            attractions_result = self.client.table('spot_attractions').select('count').execute()
            stats['total_attractions'] = len(attractions_result.data) if attractions_result.data else 0
            
            # 相册总数
            albums_result = self.client.table('spot_map_albums').select('count').execute()
            stats['total_albums'] = len(albums_result.data) if albums_result.data else 0
            
            # 按类别统计景点
            categories_result = self.client.table('spot_attractions')\
                .select('category')\
                .execute()
            
            if categories_result.data:
                category_counts = {}
                for row in categories_result.data:
                    category = row['category']
                    category_counts[category] = category_counts.get(category, 0) + 1
                stats['attractions_by_category'] = category_counts
            
            # 按国家统计景点
            countries_result = self.client.table('spot_attractions')\
                .select('country')\
                .execute()
            
            if countries_result.data:
                country_counts = {}
                for row in countries_result.data:
                    country = row['country']
                    country_counts[country] = country_counts.get(country, 0) + 1
                stats['attractions_by_country'] = country_counts
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

# 全局实例
supabase_client = SupabaseClient()