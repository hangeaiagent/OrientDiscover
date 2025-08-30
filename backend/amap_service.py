"""
高德地图API服务
提供现代化的地理信息搜索功能
"""

import aiohttp
import asyncio
import json
import os
from typing import List, Dict, Optional
from urllib.parse import quote

class AmapService:
    """高德地图API服务"""
    
    def __init__(self):
        self.api_key = os.getenv("AMAP_API_KEY", "72a87689c90310d3a119865c755a5681")
        self.base_url = "https://restapi.amap.com/v3"
        
    async def search_nearby_pois(self, lat: float, lon: float, radius: int = 5000, keywords: str = "", types: str = "风景名胜") -> List[Dict]:
        """搜索附近的POI点"""
        try:
            url = f"{self.base_url}/place/around"
            params = {
                'key': self.api_key,
                'location': f"{lon},{lat}",  # 高德API使用经度,纬度格式
                'radius': radius,
                'types': types if not keywords else '',  # 如果有keywords，不使用types
                'keywords': keywords if keywords else '',  # 关键词搜索
                'sortrule': 'distance',  # 按距离排序
                'offset': 20,  # 返回数量
                'page': 1,
                'extensions': 'all'  # 返回详细信息
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"高德地图POI搜索结果: {data.get('count', 0)} 个")
                        
                        if data.get('status') == '1' and data.get('pois'):
                            return self._parse_pois(data['pois'])
                        else:
                            print(f"高德地图API错误: {data.get('info', 'Unknown error')}")
                            return []
                    else:
                        print(f"高德地图API请求失败: HTTP {response.status}")
                        return []
                        
        except Exception as e:
            print(f"高德地图API异常: {e}")
            return []
    
    def _parse_pois(self, pois: List[Dict]) -> List[Dict]:
        """解析POI数据"""
        attractions = []
        
        for poi in pois:
            try:
                # 解析坐标
                location = poi.get('location', '').split(',')
                if len(location) != 2:
                    continue
                    
                lon, lat = float(location[0]), float(location[1])
                
                # 解析地址信息
                address = poi.get('address', '')
                pname = poi.get('pname', '')  # 省份
                cityname = poi.get('cityname', '')  # 城市
                adname = poi.get('adname', '')  # 区域
                
                # 生成景点信息
                attraction = {
                    'name': poi.get('name', '未知景点'),
                    'latitude': lat,
                    'longitude': lon,
                    'category': self._map_category(poi.get('type', '')),
                    'description': self._generate_description(poi),
                    'address': address,
                    'province': pname,
                    'city': cityname,
                    'district': adname,
                    'tel': poi.get('tel', ''),
                    'website': poi.get('website', ''),
                    'rating': poi.get('biz_ext', {}).get('rating', ''),
                    'cost': poi.get('biz_ext', {}).get('cost', ''),
                    'opening_hours': self._parse_opening_hours(poi),
                    'ticket_price': self._estimate_ticket_price(poi),
                    'booking_method': self._get_booking_method(poi),
                    'image': self._get_poi_image(poi),
                    'photos': poi.get('photos', []),  # 保留原始图片数组
                    'distance': float(poi.get('distance', 0)),  # 确保是数字类型
                    'country': '中国'
                }
                
                attractions.append(attraction)
                
            except Exception as e:
                print(f"解析POI数据错误: {e}")
                continue
        
        return attractions
    
    def _map_category(self, amap_type: str) -> str:
        """映射高德地图类型到我们的分类"""
        type_mapping = {
            '风景名胜': '自然景观',
            '公园广场': '自然景观',
            '文物古迹': '文化古迹',
            '教堂': '文化古迹',
            '博物馆': '文化古迹',
            '展览馆': '文化古迹',
            '纪念馆': '文化古迹',
            '游乐园': '休闲娱乐',
            '度假村': '休闲娱乐',
            '温泉': '休闲娱乐',
            '购物': '城市地标',
            '商务住宅': '城市地标'
        }
        
        for key, value in type_mapping.items():
            if key in amap_type:
                return value
        
        return '城市地标'
    
    def _generate_description(self, poi: Dict) -> str:
        """生成景点描述"""
        name = poi.get('name', '')
        type_desc = poi.get('type', '')
        address = poi.get('address', '')
        
        # 基础描述
        description = f"{name}位于{address}，"
        
        # 根据类型添加描述
        if '风景名胜' in type_desc:
            description += "是一处著名的自然风景区，拥有优美的自然风光。"
        elif '文物古迹' in type_desc:
            description += "是具有重要历史文化价值的古迹，承载着深厚的历史底蕴。"
        elif '博物馆' in type_desc:
            description += "是展示历史文化和艺术珍品的重要场所。"
        elif '公园' in type_desc:
            description += "是市民休闲娱乐的好去处，环境优美。"
        else:
            description += "是当地的重要地标建筑。"
        
        return description
    
    def _parse_opening_hours(self, poi: Dict) -> str:
        """解析营业时间"""
        # 高德地图的营业时间在biz_ext中
        biz_ext = poi.get('biz_ext', {})
        opening_hours = biz_ext.get('opening_hours', '')
        
        if opening_hours:
            return opening_hours
        
        # 根据类型推测营业时间
        poi_type = poi.get('type', '')
        if '风景名胜' in poi_type or '公园' in poi_type:
            return "06:00-18:00"
        elif '博物馆' in poi_type or '文物古迹' in poi_type:
            return "09:00-17:00"
        elif '游乐园' in poi_type:
            return "09:00-21:00"
        else:
            return "营业时间请咨询商家"
    
    def _estimate_ticket_price(self, poi: Dict) -> str:
        """估算门票价格"""
        # 高德地图的价格信息在biz_ext中
        biz_ext = poi.get('biz_ext', {})
        cost = biz_ext.get('cost', '')
        
        if cost:
            return f"参考价格：{cost}元"
        
        # 根据类型估算价格
        poi_type = poi.get('type', '')
        name = poi.get('name', '')
        
        if '公园' in poi_type and '免费' not in name:
            return "成人票：10-30元"
        elif '风景名胜' in poi_type:
            return "成人票：30-80元"
        elif '博物馆' in poi_type:
            return "成人票：20-60元"
        elif '文物古迹' in poi_type:
            return "成人票：40-100元"
        elif '游乐园' in poi_type:
            return "成人票：100-300元"
        else:
            return "价格请咨询商家"
    
    def _get_booking_method(self, poi: Dict) -> str:
        """获取购票方式"""
        tel = poi.get('tel', '')
        website = poi.get('website', '')
        
        methods = []
        if tel:
            methods.append("电话预订")
        if website:
            methods.append("官方网站")
        
        methods.append("现场购票")
        
        return "、".join(methods)
    
    def _get_poi_image(self, poi: Dict) -> str:
        """获取POI图片"""
        # 首先尝试从高德地图API获取真实图片
        photos = poi.get('photos', [])
        if photos and len(photos) > 0:
            # 选择第一张图片
            photo = photos[0]
            if isinstance(photo, dict) and 'url' in photo:
                return photo['url']
            elif isinstance(photo, str):
                # 有时候photos可能直接是URL字符串数组
                return photo
        
        # 其次尝试从biz_ext中获取图片
        biz_ext = poi.get('biz_ext', {})
        if 'pic_info' in biz_ext:
            return biz_ext['pic_info']
        
        # 如果没有图片，根据POI类型提供默认图片
        poi_type = poi.get('type', '')
        
        if '风景名胜' in poi_type or '公园' in poi_type:
            return "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400"
        elif '文物古迹' in poi_type or '博物馆' in poi_type:
            return "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=400"
        elif '游乐园' in poi_type:
            return "https://images.unsplash.com/photo-1594736797933-d0401ba2fe65?w=400"
        else:
            return "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=400"
    
    async def geocode_reverse(self, lat: float, lon: float) -> Optional[Dict]:
        """逆地理编码 - 根据坐标获取地址信息"""
        try:
            url = f"{self.base_url}/geocode/regeo"
            params = {
                'key': self.api_key,
                'location': f"{lon},{lat}",
                'poitype': '',
                'radius': 1000,
                'extensions': 'all',
                'batch': 'false',
                'roadlevel': 0
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('status') == '1' and data.get('regeocode'):
                            regeocode = data['regeocode']
                            addressComponent = regeocode.get('addressComponent', {})
                            
                            return {
                                'formatted_address': regeocode.get('formatted_address', ''),
                                'country': addressComponent.get('country', '中国'),
                                'province': addressComponent.get('province', ''),
                                'city': addressComponent.get('city', ''),
                                'district': addressComponent.get('district', ''),
                                'township': addressComponent.get('township', ''),
                                'neighborhood': addressComponent.get('neighborhood', {}),
                                'building': addressComponent.get('building', {}),
                                'pois': regeocode.get('pois', [])
                            }
                        else:
                            print(f"高德逆地理编码错误: {data.get('info', 'Unknown error')}")
                            return None
                    else:
                        print(f"高德逆地理编码请求失败: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            print(f"高德逆地理编码异常: {e}")
            return None

# 全局实例
amap_service = AmapService()
