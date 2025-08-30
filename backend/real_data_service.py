"""
真实地理数据服务
集成多个API获取真实的地点信息、图片和描述
"""

import requests
import asyncio
import aiohttp
from typing import List, Dict, Optional
import json
from local_attractions_db import local_attractions_db
from amap_service import amap_service
import os
from datetime import datetime

class RealDataService:
    def __init__(self):
        # API配置 - 需要申请免费API密钥
        self.apis = {
            # OpenWeatherMap Geocoding API (免费)
            'geocoding': {
                'base_url': 'http://api.openweathermap.org/geo/1.0',
                'api_key': os.getenv('OPENWEATHER_API_KEY', 'your_api_key_here')
            },
            # Nominatim OpenStreetMap API (免费，无需密钥)
            'nominatim': {
                'base_url': 'https://nominatim.openstreetmap.org'
            },
            # Unsplash API (免费)
            'unsplash': {
                'base_url': 'https://api.unsplash.com',
                'api_key': os.getenv('UNSPLASH_API_KEY', 'your_api_key_here')
            },
            # Wikipedia API (免费)
            'wikipedia': {
                'base_url': 'https://en.wikipedia.org/api/rest_v1'
            }
        }
        
        # 缓存机制
        self.cache = {}
        self.cache_file = 'data_cache.json'
        self.load_cache()
    
    def load_cache(self):
        """加载缓存数据"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
        except Exception as e:
            print(f"加载缓存失败: {e}")
            self.cache = {}
    
    def save_cache(self):
        """保存缓存数据"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    async def get_real_places_along_route(self, points: List[Dict], time_mode: str = 'present') -> List[Dict]:
        """获取目标点周围的真实地点信息"""
        places = []
        
        async with aiohttp.ClientSession() as session:
            for point in points:
                # 获取目标点周围5km内的多个景点
                nearby_places = await self.get_nearby_attractions(session, point, time_mode, radius_km=5)
                places.extend(nearby_places)
        
        self.save_cache()  # 保存缓存
        return places
    
    async def get_nearby_attractions(self, session: aiohttp.ClientSession, point: Dict, time_mode: str, radius_km: float = 5) -> List[Dict]:
        """获取目标点周围的景点"""
        attractions = []
        lat, lon = point['latitude'], point['longitude']
        target_distance = point['distance']
        
        # 使用集合跟踪已添加的景点名称，避免重复
        added_names = set()
        
        # 直接使用高德地图API搜索景点
        print(f"使用高德地图API搜索坐标 ({lat:.4f}, {lon:.4f}) 附近的景点...")
        print(f"目标点距离用户: {target_distance}km")
        
        # 搜索不同类型的景点（减少请求次数，避免超限）
        poi_types = [
            "风景名胜",  # 风景名胜（包括各类景点）
            "公园广场",  # 公园
            "文物古迹",  # 古迹
            "博物馆"     # 博物馆
        ]
        
        for poi_type in poi_types:
            try:
                amap_pois = await amap_service.search_nearby_pois(
                    lat, lon, 
                    radius=int(radius_km * 1000),  # 转换为米
                    keywords=poi_type
                )
                
                for poi in amap_pois:
                    poi_name = poi.get('name', '')
                    
                    # 过滤行政区域和重复的景点
                    if poi_name and poi_name not in added_names and len(attractions) < 5:
                        # 验证是否为有效景点（过滤行政区域）
                        if not self.is_valid_location_info({'name': poi_name, 'type': poi.get('category', '')}):
                            continue
                        
                        # POI数据已经包含解析好的坐标
                        poi_lat = poi.get('latitude')
                        poi_lon = poi.get('longitude')
                        
                        if not poi_lat or not poi_lon:
                            continue
                        
                        # 使用高德地图返回的距离（米转换为公里）
                        amap_distance = poi.get('distance', 0)
                        # 确保距离是数字
                        if isinstance(amap_distance, str):
                            try:
                                amap_distance = float(amap_distance)
                            except:
                                amap_distance = 0
                        
                        # 高德返回的距离单位是米，转换为公里
                        distance_in_km = amap_distance / 1000.0
                        
                        # 使用POI提供的详细信息
                        place_info = {
                            'name': poi_name,
                            'latitude': poi_lat,
                            'longitude': poi_lon,
                            'distance': target_distance,  # 这是用户到目标点的距离
                            'description': f"距此约{distance_in_km:.1f}公里 - {poi.get('description', poi_name)}",
                            'image': poi.get('image', 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400'),
                            'country': poi.get('country', '中国'),
                            'city': poi.get('city', poi.get('district', '当地')),
                            'opening_hours': poi.get('opening_hours', '08:00-17:30'),
                            'ticket_price': poi.get('ticket_price', '请咨询景点'),
                            'booking_method': poi.get('booking_method', '现场购票'),
                            'category': poi.get('category', '景点')
                        }
                        attractions.append(place_info)
                        added_names.add(poi_name)
                        
                        print(f"高德地图找到景点: {poi_name} ({poi_type})")
                        print(f"  距离: {amap_distance}米 -> {distance_in_km:.1f}公里")
                        print(f"  描述: {place_info['description']}")
                        
            except Exception as e:
                print(f"高德地图API搜索 {poi_type} 失败: {e}")
                continue
        
        # 如果还是没有找到足够的景点，生成一些虚拟景点
        if len(attractions) < 3:
            print(f"高德地图只找到 {len(attractions)} 个景点，生成虚拟景点补充...")
            virtual_attractions = self.generate_virtual_attractions_real(point, time_mode, radius_km)
            # 过滤掉非景点类型的虚拟内容
            filtered_virtual = [attr for attr in virtual_attractions if self.is_valid_attraction_type(attr)]
            for virtual_attr in filtered_virtual:
                if virtual_attr.get('name') not in added_names:
                    attractions.append(virtual_attr)
                    added_names.add(virtual_attr.get('name'))
                    if len(attractions) >= 5:
                        break
        
        return attractions[:5]  # 最多返回5个景点
    
    def generate_search_points(self, center_lat: float, center_lon: float, radius_km: float) -> List[Dict]:
        """在中心点周围生成搜索点"""
        from geographiclib.geodesic import Geodesic
        geod = Geodesic.WGS84
        
        search_points = []
        # 在8个方向上生成搜索点
        for bearing in [0, 45, 90, 135, 180, 225, 270, 315]:
            for distance_km in [1, 2.5, 4]:  # 不同距离
                point = geod.Direct(center_lat, center_lon, bearing, distance_km * 1000)
                search_points.append({
                    'lat': point['lat2'],
                    'lon': point['lon2']
                })
        
        return search_points
    
    def generate_virtual_attractions_real(self, point: Dict, time_mode: str, radius_km: float) -> List[Dict]:
        """生成虚拟景点（真实数据版本）"""
        lat, lon = point['latitude'], point['longitude']
        target_distance = point['distance']
        
        attractions = []
        attraction_types = ['自然风光', '历史遗迹', '文化景点']
        
        import random
        for i, attraction_type in enumerate(attraction_types):
            # 随机生成景点位置
            offset_km = random.uniform(0.5, radius_km)
            bearing = random.uniform(0, 360)
            
            from geographiclib.geodesic import Geodesic
            geod = Geodesic.WGS84
            attraction_point = geod.Direct(lat, lon, bearing, offset_km * 1000)
            
            descriptions = {
                "present": f"这里是一处美丽的{attraction_type}，展现了当地独特的自然和人文魅力。",
                "past": f"古代的{attraction_type}，承载着深厚的历史文化底蕴。"
            }
            
            # 生成详细信息
            attraction_details = self.generate_attraction_details_real(attraction_type, time_mode)
            
            # 生成具体的景点名称而不是通用名称
            specific_names = {
                '自然风光': ['山水风景区', '生态公园', '自然保护区', '森林公园'],
                '历史遗迹': ['古建筑群', '历史文化遗址', '古代遗迹', '文物保护区'],
                '文化景点': ['文化广场', '艺术中心', '文化公园', '民俗村']
            }
            
            import random
            specific_name = random.choice(specific_names.get(attraction_type, ['景点']))
            
            attraction = {
                'name': f"{specific_name}",
                'latitude': attraction_point['lat2'],
                'longitude': attraction_point['lon2'],
                'distance': target_distance,
                'description': f"距此约{offset_km:.1f}公里 - {descriptions.get(time_mode, descriptions['present'])}",
                'image': attraction_details['image'],
                'country': '中国',
                'city': '当地',
                'type': attraction_type,
                'opening_hours': attraction_details.get('opening_hours', '08:00-17:30'),
                'ticket_price': attraction_details.get('ticket_price', '成人票：50元'),
                'booking_method': attraction_details.get('booking_method', '现场购票或网上预约'),
                'category': attraction_type
            }
            attractions.append(attraction)
        
        return attractions
    
    def is_valid_attraction_type(self, attraction: Dict) -> bool:
        """验证是否为有效的景点类型"""
        name = attraction.get('name', '').lower()
        attraction_type = attraction.get('type', '').lower()
        category = attraction.get('category', '').lower()
        
        # 排除的行政区域关键词
        administrative_keywords = [
            '区', '市', '县', '省', '街道', '镇', '乡', '村',
            'district', 'city', 'county', 'province', 'street',
            '行政区', '管辖区', '辖区'
        ]
        
        # 景点关键词
        attraction_keywords = [
            '陵', '寺', '庙', '宫', '园', '山', '湖', '塔', '桥', '城', '馆', '院',
            '景区', '景点', '风景', '名胜', '古迹', '遗址', '博物', '纪念',
            'temple', 'palace', 'park', 'mountain', 'lake', 'tower', 'museum',
            'attraction', 'scenic', 'monument', 'memorial'
        ]
        
        # 检查是否为行政区域
        is_administrative = any(keyword in name for keyword in administrative_keywords)
        
        # 检查是否包含景点关键词
        has_attraction_keyword = any(keyword in name for keyword in attraction_keywords)
        
        # 检查类型和分类
        is_attraction_type = 'attraction' in attraction_type or any(
            keyword in category for keyword in ['景观', '古迹', '地标', '娱乐']
        )
        
        # 只有非行政区域且包含景点特征的才被认为是有效景点
        return not is_administrative and (has_attraction_keyword or is_attraction_type)
    
    def is_valid_location_info(self, location_info: Dict) -> bool:
        """验证位置信息是否为有效景点（非行政区域）"""
        name = location_info.get('name', '').lower()
        location_type = location_info.get('type', '').lower()
        
        # 行政区域关键词
        administrative_keywords = [
            '区', '市', '县', '省', '街道', '镇', '乡', '村', '路', '街',
            'district', 'city', 'county', 'province', 'street', 'road',
            '行政区', '管辖区', '辖区', '开发区', '新区'
        ]
        
        # 行政区域类型
        administrative_types = [
            'administrative', 'boundary', 'place'
        ]
        
        # 景点关键词
        attraction_keywords = [
            '陵', '寺', '庙', '宫', '园', '山', '湖', '塔', '桥', '城', '馆', '院',
            '景区', '景点', '风景', '名胜', '古迹', '遗址', '博物', '纪念', '公园',
            'temple', 'palace', 'park', 'mountain', 'lake', 'tower', 'museum',
            'attraction', 'scenic', 'monument', 'memorial'
        ]
        
        # 检查名称是否为行政区域
        is_administrative_name = any(keyword in name for keyword in administrative_keywords)
        
        # 检查类型是否为行政区域
        is_administrative_type = any(admin_type in location_type for admin_type in administrative_types)
        
        # 检查是否包含景点关键词
        has_attraction_keyword = any(keyword in name for keyword in attraction_keywords)
        
        # 特殊处理：如果名称明确包含景点特征，即使类型是administrative也认为是景点
        if has_attraction_keyword:
            return True
        
        # 如果是行政区域名称或类型，则过滤掉
        if is_administrative_name or is_administrative_type:
            return False
        
        return True
    
    def generate_attraction_details_from_poi(self, poi: Dict, time_mode: str) -> Dict:
        """根据高德地图POI信息生成景点详细信息"""
        import random
        
        # 根据POI类型生成相应的详细信息
        poi_type = poi.get('type', '').split(';')[0]
        
        # 默认信息
        default_details = {
            'image': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400',
            'opening_hours': '08:00-17:30',
            'ticket_price': '成人票：免费',
            'booking_method': '无需预约，直接参观'
        }
        
        # 根据类型定制信息
        if '博物馆' in poi_type or '展览馆' in poi_type:
            details = {
                'image': 'https://images.unsplash.com/photo-1554907984-15263bfd63bd?w=400',
                'opening_hours': '09:00-17:00（周一闭馆）',
                'ticket_price': '成人票：免费（需预约）',
                'booking_method': '官方网站或微信公众号预约'
            }
        elif '公园' in poi_type or '广场' in poi_type:
            details = {
                'image': 'https://images.unsplash.com/photo-1568515387631-8b650bbcdb90?w=400',
                'opening_hours': '全天开放',
                'ticket_price': '免费开放',
                'booking_method': '无需预约'
            }
        elif '寺庙' in poi_type or '道观' in poi_type:
            details = {
                'image': 'https://images.unsplash.com/photo-1548013146-72479768bada?w=400',
                'opening_hours': '08:00-17:00',
                'ticket_price': '成人票：10-30元',
                'booking_method': '现场购票'
            }
        elif '风景名胜' in poi_type or '旅游景点' in poi_type:
            ticket_prices = ['成人票：50元', '成人票：80元', '成人票：120元', '成人票：150元']
            details = {
                'image': 'https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=400',
                'opening_hours': '08:00-18:00',
                'ticket_price': random.choice(ticket_prices),
                'booking_method': '现场购票或官方网站预约'
            }
        elif '文物古迹' in poi_type:
            details = {
                'image': 'https://images.unsplash.com/photo-1569163139394-de4798aa62c6?w=400',
                'opening_hours': '08:30-17:00',
                'ticket_price': '成人票：40元',
                'booking_method': '现场购票或官方网站预约'
            }
        else:
            details = default_details
        
        # 如果是古代模式，调整信息
        if time_mode == 'past':
            details['ticket_price'] = '免费参观'
            details['booking_method'] = '自由参观'
            details['opening_hours'] = '日出而作，日落而息'
        
        return details
    
    def generate_attraction_details_real(self, attraction_type: str, time_mode: str) -> Dict:
        """为真实数据服务生成景点详细信息"""
        import random
        
        details = {
            "自然风光": {
                "present": {
                    "opening_hours": "全天开放",
                    "ticket_price": "免费",
                    "booking_method": "无需预约，直接前往",
                    "images": [
                        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
                        "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400"
                    ]
                },
                "past": {
                    "opening_hours": "日出至日落",
                    "ticket_price": "免费",
                    "booking_method": "古代无需门票，自由游览",
                    "images": [
                        "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400"
                    ]
                }
            },
            "历史遗迹": {
                "present": {
                    "opening_hours": "09:00-17:00（周一闭馆）",
                    "ticket_price": f"成人票：{random.choice(['40', '60', '80'])}元",
                    "booking_method": "现场购票或官方网站预约",
                    "images": [
                        "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=400",
                        "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400"
                    ]
                },
                "past": {
                    "opening_hours": "古代全天开放",
                    "ticket_price": "古代免费参观",
                    "booking_method": "古代无需预约",
                    "images": [
                        "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400"
                    ]
                }
            },
            "文化景点": {
                "present": {
                    "opening_hours": "10:00-18:00",
                    "ticket_price": f"成人票：{random.choice(['50', '80', '100'])}元",
                    "booking_method": "现场购票、手机APP或官方网站",
                    "images": [
                        "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=400",
                        "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400"
                    ]
                },
                "past": {
                    "opening_hours": "古代建筑全天可观赏",
                    "ticket_price": "古代免费参观",
                    "booking_method": "古代无需预约",
                    "images": [
                        "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400"
                    ]
                }
            }
        }
        
        type_details = details.get(attraction_type, details["自然风光"])
        mode_details = type_details.get(time_mode, type_details["present"])
        
        return {
            "opening_hours": mode_details["opening_hours"],
            "ticket_price": mode_details["ticket_price"],
            "booking_method": mode_details["booking_method"],
            "image": random.choice(mode_details["images"])
        }
    
    async def get_place_info(self, session: aiohttp.ClientSession, point: Dict, time_mode: str) -> Optional[Dict]:
        """获取单个地点的详细信息"""
        lat, lon = point['latitude'], point['longitude']
        cache_key = f"{lat:.4f}_{lon:.4f}_{time_mode}"
        
        # 检查缓存
        if cache_key in self.cache:
            cached_data = self.cache[cache_key].copy()
            cached_data.update({
                'latitude': lat,
                'longitude': lon,
                'distance': point['distance']
            })
            return cached_data
        
        try:
            # 1. 获取地点名称和基本信息
            location_info = await self.get_location_name(session, lat, lon)
            if not location_info:
                print(f"坐标 ({lat:.4f}, {lon:.4f}) 未找到有效景点信息")
                return None
            
            # 验证是否为有效景点（过滤行政区域）
            if not self.is_valid_location_info(location_info):
                print(f"过滤掉行政区域信息: {location_info['name']}")
                return None
            
            # 检查是否为本地数据库中的景点
            local_attraction = local_attractions_db.get_attraction_by_name(location_info['name'])
            
            # 检查是否为高德地图数据
            amap_pois = await amap_service.search_nearby_pois(lat, lon, radius=1000)
            amap_poi = None
            if amap_pois:
                # 找到名称匹配的POI
                for poi in amap_pois:
                    if poi['name'] == location_info['name']:
                        amap_poi = poi
                        break
            
            if local_attraction:
                # 使用本地数据库的详细信息
                print(f"使用本地数据库详细信息: {local_attraction['name']}")
                place_data = {
                    'name': local_attraction['name'],
                    'latitude': lat,
                    'longitude': lon,
                    'distance': point['distance'],
                    'description': local_attraction['description'],
                    'image': local_attraction['image'],
                    'country': local_attraction['country'],
                    'city': local_attraction['city'],
                    'type': 'attraction',
                    'opening_hours': local_attraction['opening_hours'],
                    'ticket_price': local_attraction['ticket_price'],
                    'booking_method': local_attraction['booking_method'],
                    'category': local_attraction['category']
                }
            elif amap_poi:
                # 使用高德地图的详细信息
                print(f"使用高德地图详细信息: {amap_poi['name']}")
                place_data = {
                    'name': amap_poi['name'],
                    'latitude': lat,
                    'longitude': lon,
                    'distance': point['distance'],
                    'description': amap_poi['description'],
                    'image': amap_poi['image'],
                    'country': amap_poi['country'],
                    'city': amap_poi['city'],
                    'type': 'attraction',
                    'opening_hours': amap_poi['opening_hours'],
                    'ticket_price': amap_poi['ticket_price'],
                    'booking_method': amap_poi['booking_method'],
                    'category': amap_poi['category']
                }
            else:
                # 2. 获取地点描述
                description = await self.get_place_description(session, location_info['name'], time_mode)
                
                # 3. 获取地点图片
                image_url = await self.get_place_image(session, location_info['name'])
                
                place_data = {
                    'name': location_info['name'],
                    'latitude': lat,
                    'longitude': lon,
                    'distance': point['distance'],
                    'description': description,
                    'image': image_url,
                    'country': location_info.get('country', ''),
                    'city': location_info.get('city', ''),
                    'type': location_info.get('type', 'place')
                }
            
            # 缓存数据
            self.cache[cache_key] = {
                'name': place_data['name'],
                'description': place_data['description'],
                'image': place_data['image'],
                'country': place_data['country'],
                'city': place_data['city'],
                'type': place_data['type'],
                'cached_at': datetime.now().isoformat()
            }
            
            return place_data
            
        except Exception as e:
            print(f"获取地点信息失败 ({lat}, {lon}): {e}")
            return None
    
    async def get_location_name(self, session: aiohttp.ClientSession, lat: float, lon: float) -> Optional[Dict]:
        """获取地点名称，直接使用高德地图API"""
        try:
            # 直接使用高德地图搜索
            print(f"使用高德地图搜索坐标 ({lat:.4f}, {lon:.4f}) 附近的景点...")
            
            # 搜索多种类型的景点
            poi_types = ["风景名胜", "公园广场", "文物古迹", "博物馆", "寺庙道观", "旅游景点"]
            
            for poi_type in poi_types:
                amap_pois = await amap_service.search_nearby_pois(lat, lon, radius=5000, keywords=poi_type)
                
                if amap_pois:
                    # 过滤行政区域
                    for poi in amap_pois:
                        if self.is_valid_location_info({'name': poi['name'], 'type': poi.get('type', '')}):
                            print(f"高德地图找到景点: {poi['name']} ({poi_type}), 距离: {poi.get('distance', 0)}米")
                            return {
                                'name': poi['name'],
                                'country': '中国',
                                'city': poi.get('cityname', '当地'),
                                'type': 'attraction',
                                'full_address': poi.get('address', '')
                            }
            
            # 如果高德地图没有找到，尝试Nominatim搜索
            print("高德地图未找到景点，尝试Nominatim搜索...")
            attractions = await self.search_nearby_attractions(session, lat, lon)
            if attractions:
                print(f"Nominatim搜索找到景点: {attractions}")
                return attractions[0]  # 返回最近的景点
            
            # 如果没有找到景点，不返回行政区域信息
            print("未找到任何景点，跳过行政区域信息")
            return None
        except Exception as e:
            print(f"Nominatim API错误: {e}")
        
        return None
    
    async def search_nearby_attractions(self, session: aiohttp.ClientSession, lat: float, lon: float, radius: float = 5000) -> List[Dict]:
        """搜索附近的景点"""
        try:
            # 使用Nominatim搜索附近的景点
            url = f"{self.apis['nominatim']['base_url']}/search"
            
            # 搜索不同类型的景点
            attraction_queries = [
                f"tourism near {lat},{lon}",
                f"attraction near {lat},{lon}",
                f"景点 near {lat},{lon}",
                f"十三陵 near {lat},{lon}",  # 专门搜索十三陵
                f"明十三陵 near {lat},{lon}"
            ]
            
            all_attractions = []
            
            for query in attraction_queries:
                params = {
                    'q': query,
                    'format': 'json',
                    'addressdetails': 1,
                    'limit': 5,
                    'bounded': 1,
                    'viewbox': f"{lon-0.05},{lat+0.05},{lon+0.05},{lat-0.05}",  # 约5km范围
                    'accept-language': 'zh-CN,zh,en'
                }
                
                headers = {
                    'User-Agent': 'OrientDiscover/1.0 (https://github.com/your-repo)'
                }
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"景点搜索查询 '{query}' 结果: {len(data)} 个")
                        
                        for item in data:
                            # 过滤出真正的景点
                            if self.is_valid_attraction(item):
                                attraction_lat = float(item['lat'])
                                attraction_lon = float(item['lon'])
                                distance = self.calculate_distance(lat, lon, attraction_lat, attraction_lon)
                                
                                if distance <= radius:  # 在指定半径内
                                    all_attractions.append({
                                        'name': item['display_name'].split(',')[0],
                                        'country': '中国',
                                        'city': item.get('address', {}).get('city', ''),
                                        'type': 'attraction',
                                        'full_address': item['display_name'],
                                        'distance': distance,
                                        'lat': attraction_lat,
                                        'lon': attraction_lon
                                    })
            
            # 按距离排序
            all_attractions.sort(key=lambda x: x['distance'])
            print(f"找到 {len(all_attractions)} 个有效景点")
            
            return all_attractions[:3]  # 返回最近的3个
            
        except Exception as e:
            print(f"景点搜索错误: {e}")
            return []
    
    def is_valid_attraction(self, item: Dict) -> bool:
        """判断是否为有效的景点"""
        display_name = item.get('display_name', '').lower()
        osm_type = item.get('type', '').lower()
        
        # 景点关键词
        attraction_keywords = [
            '陵', '寺', '庙', '宫', '园', '山', '湖', '塔', '桥', '城', '馆', '院',
            'temple', 'palace', 'park', 'mountain', 'lake', 'tower', 'museum',
            'tourism', 'attraction', 'monument', 'memorial'
        ]
        
        # 排除的行政区域关键词
        exclude_keywords = ['区', '市', '县', '省', '街道', 'district', 'city', 'county']
        
        # 检查是否包含景点关键词
        has_attraction_keyword = any(keyword in display_name for keyword in attraction_keywords)
        
        # 检查是否为行政区域
        is_administrative = any(keyword in display_name for keyword in exclude_keywords)
        
        return has_attraction_keyword and not is_administrative
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点间距离（米）"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # 地球半径（米）
        
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    async def get_place_description(self, session: aiohttp.ClientSession, place_name: str, time_mode: str) -> str:
        """获取地点描述"""
        try:
            # 尝试从Wikipedia获取描述
            description = await self.get_wikipedia_summary(session, place_name)
            
            if description:
                # 根据时间模式调整描述
                if time_mode == 'past':
                    description = f"在历史上，{description}"
                elif time_mode == 'future':
                    description = f"展望未来，{place_name}可能发展成为一个重要的地区。{description}"
                
                return description
            
        except Exception as e:
            print(f"获取描述失败: {e}")
        
        # 默认描述
        default_descriptions = {
            'present': f"这里是{place_name}，一个值得探索的地方。",
            'past': f"在过去的岁月里，{place_name}见证了历史的变迁。",
            'future': f"未来的{place_name}充满了无限可能。"
        }
        
        return default_descriptions.get(time_mode, default_descriptions['present'])
    
    async def get_wikipedia_summary(self, session: aiohttp.ClientSession, place_name: str) -> Optional[str]:
        """从Wikipedia获取地点摘要"""
        try:
            # 搜索Wikipedia页面
            search_url = f"{self.apis['wikipedia']['base_url']}/page/summary/{place_name}"
            
            async with session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()
                    extract = data.get('extract', '')
                    
                    if extract and len(extract) > 50:
                        # 限制描述长度
                        if len(extract) > 200:
                            extract = extract[:200] + "..."
                        return extract
        except Exception as e:
            print(f"Wikipedia API错误: {e}")
        
        return None
    
    async def get_place_image(self, session: aiohttp.ClientSession, place_name: str) -> str:
        """获取地点图片"""
        try:
            if self.apis['unsplash']['api_key'] != 'your_api_key_here':
                url = f"{self.apis['unsplash']['base_url']}/search/photos"
                headers = {
                    'Authorization': f"Client-ID {self.apis['unsplash']['api_key']}"
                }
                params = {
                    'query': f"{place_name} landscape city",
                    'per_page': 1,
                    'orientation': 'landscape'
                }
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results', [])
                        if results:
                            return results[0]['urls']['regular']
        except Exception as e:
            print(f"Unsplash API错误: {e}")
        
        # 默认图片
        return "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400"

# 全局实例
real_data_service = RealDataService()
