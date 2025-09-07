# 首先加载环境变量
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import math
from geographiclib.geodesic import Geodesic
import json
import os
import asyncio
import logging
import requests
import time
from real_data_service import real_data_service
from local_attractions_db import local_attractions_db
from global_cities_db import GlobalCitiesDB
from gemini_service import gemini_service
from doro_service import doro_service
from spot_api_service import spot_api_service
from album_orchestrator import get_album_orchestrator
from vector_database import get_vector_database
from fastapi import File, UploadFile, Form
from fastapi.responses import FileResponse, Response
import tempfile
import shutil
from auth import router as auth_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backend.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="方向探索派对API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class ExploreRequest(BaseModel):
    latitude: float
    longitude: float
    heading: float
    segment_distance: int = 100  # 默认100km
    time_mode: str = "present"  # present, past, future
    speed: int = 120  # 默认120km/h

class PlaceInfo(BaseModel):
    name: str
    latitude: float
    longitude: float
    distance: float
    description: str
    image: Optional[str] = None
    video: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    opening_hours: Optional[str] = None
    ticket_price: Optional[str] = None
    booking_method: Optional[str] = None
    category: Optional[str] = None

class ExploreResponse(BaseModel):
    places: List[PlaceInfo]
    total_distance: float
    calculation_time: float

# 旅程相关数据模型
class StartJourneyRequest(BaseModel):
    start_lat: float
    start_lng: float
    start_name: str
    journey_title: str

class JourneyResponse(BaseModel):
    success: bool
    message: str
    journey_id: Optional[str] = None

# 全局变量
geod = Geodesic.WGS84
places_data = {}

# 数据库实例
global_cities_db = GlobalCitiesDB()

# 旅程管理全局变量
active_journeys = {}  # 存储活跃的旅程
journey_counter = 0   # 旅程ID计数器

# 地理编码缓存
geocode_cache = {}  # 缓存地理编码结果
cache_max_size = 1000  # 最大缓存条目数

def load_places_data():
    """加载地点数据"""
    global places_data
    
    # 创建示例数据（实际项目中应该从数据库或文件加载）
    places_data = {
        "present": [
            {
                "name": "东京",
                "latitude": 35.6762,
                "longitude": 139.6503,
                "country": "日本",
                "city": "东京",
                "description": "现代化的国际大都市，科技与传统文化的完美融合。",
                "image": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=400"
            },
            {
                "name": "纽约",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "country": "美国",
                "city": "纽约",
                "description": "世界金融中心，拥有标志性的天际线和自由女神像。",
                "image": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=400"
            },
            {
                "name": "伦敦",
                "latitude": 51.5074,
                "longitude": -0.1278,
                "country": "英国",
                "city": "伦敦",
                "description": "历史悠久的国际都市，大本钟和泰晤士河闻名世界。",
                "image": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=400"
            },
            {
                "name": "巴黎",
                "latitude": 48.8566,
                "longitude": 2.3522,
                "country": "法国",
                "city": "巴黎",
                "description": "浪漫之都，埃菲尔铁塔和卢浮宫的所在地。",
                "image": "https://images.unsplash.com/photo-1502602898536-47ad22581b52?w=400"
            },
            {
                "name": "悉尼",
                "latitude": -33.8688,
                "longitude": 151.2093,
                "country": "澳大利亚",
                "city": "悉尼",
                "description": "拥有标志性歌剧院和海港大桥的美丽海滨城市。",
                "image": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400"
            },
            {
                "name": "开普敦",
                "latitude": -33.9249,
                "longitude": 18.4241,
                "country": "南非",
                "city": "开普敦",
                "description": "非洲大陆南端的美丽城市，桌山和好望角闻名。",
                "image": "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=400"
            },
            {
                "name": "里约热内卢",
                "latitude": -22.9068,
                "longitude": -43.1729,
                "country": "巴西",
                "city": "里约热内卢",
                "description": "拥有基督像和科帕卡巴纳海滩的热情城市。",
                "image": "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=400"
            },
            {
                "name": "迪拜",
                "latitude": 25.2048,
                "longitude": 55.2708,
                "country": "阿联酋",
                "city": "迪拜",
                "description": "现代奇迹之城，拥有世界最高建筑哈利法塔。",
                "image": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=400"
            },
            {
                "name": "新加坡",
                "latitude": 1.3521,
                "longitude": 103.8198,
                "country": "新加坡",
                "city": "新加坡",
                "description": "花园城市国家，多元文化和现代建筑的完美结合。",
                "image": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=400"
            },
            {
                "name": "冰岛雷克雅未克",
                "latitude": 64.1466,
                "longitude": -21.9426,
                "country": "冰岛",
                "city": "雷克雅未克",
                "description": "世界最北的首都，极光和地热温泉的天堂。",
                "image": "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?w=400"
            },
            {
                "name": "首尔",
                "latitude": 37.5665,
                "longitude": 126.9780,
                "country": "韩国",
                "city": "首尔",
                "description": "现代科技与传统文化并存的活力都市，K-pop和韩流文化的发源地。",
                "image": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=400"
            },
            {
                "name": "上海",
                "latitude": 31.2304,
                "longitude": 121.4737,
                "country": "中国",
                "city": "上海",
                "description": "国际化大都市，东方明珠塔和外滩的璀璨夜景令人难忘。",
                "image": "https://images.unsplash.com/photo-1545893835-abaa50cbe628?w=400"
            },
            {
                "name": "香港",
                "latitude": 22.3193,
                "longitude": 114.1694,
                "country": "中国",
                "city": "香港",
                "description": "东西方文化交融的国际金融中心，维多利亚港的夜景世界闻名。",
                "image": "https://images.unsplash.com/photo-1536599018102-9f803c140fc1?w=400"
            },
            {
                "name": "曼谷",
                "latitude": 13.7563,
                "longitude": 100.5018,
                "country": "泰国",
                "city": "曼谷",
                "description": "佛教文化浓厚的热带都市，金碧辉煌的寺庙和热闹的水上市场。",
                "image": "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=400"
            },
            {
                "name": "孟买",
                "latitude": 19.0760,
                "longitude": 72.8777,
                "country": "印度",
                "city": "孟买",
                "description": "印度的商业首都，宝莱坞电影工业的中心，充满活力和色彩。",
                "image": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=400"
            },
            {
                "name": "莫斯科",
                "latitude": 55.7558,
                "longitude": 37.6176,
                "country": "俄罗斯",
                "city": "莫斯科",
                "description": "红场和克里姆林宫见证着俄罗斯的历史变迁，冬日雪景如童话世界。",
                "image": "https://images.unsplash.com/photo-1513326738677-b964603b136d?w=400"
            },
            {
                "name": "开罗",
                "latitude": 30.0444,
                "longitude": 31.2357,
                "country": "埃及",
                "city": "开罗",
                "description": "古老的金字塔和狮身人面像守护着这座千年古城。",
                "image": "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?w=400"
            }
        ],
        "past": [
            {
                "name": "古罗马",
                "latitude": 41.9028,
                "longitude": 12.4964,
                "country": "意大利",
                "city": "罗马",
                "description": "100年前的罗马，古老的斗兽场见证着历史的变迁。",
                "image": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=400"
            },
            {
                "name": "维多利亚时代伦敦",
                "latitude": 51.5074,
                "longitude": -0.1278,
                "country": "英国",
                "city": "伦敦",
                "description": "1920年代的伦敦，工业革命后的繁华与雾霾并存。",
                "image": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=400"
            },
            {
                "name": "民国上海",
                "latitude": 31.2304,
                "longitude": 121.4737,
                "country": "中国",
                "city": "上海",
                "description": "1920年代的上海，东西方文化交融的十里洋场。",
                "image": "https://images.unsplash.com/photo-1545893835-abaa50cbe628?w=400"
            },
            {
                "name": "古埃及开罗",
                "latitude": 30.0444,
                "longitude": 31.2357,
                "country": "埃及",
                "city": "开罗",
                "description": "100年前的开罗，金字塔旁的古老文明依然辉煌。",
                "image": "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?w=400"
            }
        ],
        "future": [
            {
                "name": "未来东京2124",
                "latitude": 35.6762,
                "longitude": 139.6503,
                "country": "日本",
                "city": "东京",
                "description": "2124年的东京，飞行汽车穿梭在摩天大楼间，全息投影随处可见。",
                "image": "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400"
            },
            {
                "name": "火星新城",
                "latitude": 14.5995,
                "longitude": -87.7680,
                "country": "火星殖民地",
                "city": "新奥林匹亚",
                "description": "2124年的火星殖民城市，透明穹顶下的绿色花园。",
                "image": "https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=400"
            },
            {
                "name": "海底亚特兰蒂斯",
                "latitude": 25.0000,
                "longitude": -30.0000,
                "country": "海底城市",
                "city": "新亚特兰蒂斯",
                "description": "2124年的海底城市，生物发光建筑与海洋生物和谐共存。",
                "image": "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=400"
            }
        ]
    }

def calculate_great_circle_points(start_lat, start_lon, heading, max_distance, segment_distance):
    """计算大圆航线上的点"""
    points = []
    current_distance = 0
    
    while current_distance <= max_distance:
        # 使用大圆航线计算
        result = geod.Direct(start_lat, start_lon, heading, current_distance * 1000)  # 转换为米
        
        points.append({
            'latitude': result['lat2'],
            'longitude': result['lon2'],
            'distance': current_distance
        })
        
        current_distance += segment_distance
        
        # 最多计算20个点，避免过多数据
        if len(points) >= 20:
            break
    
    return points

def find_nearby_attractions(points, time_mode, search_radius_km=5):
    """在目标点周围搜索景点"""
    places = []
    available_places = places_data.get(time_mode, places_data["present"])
    
    for point in points:
        target_lat = point['latitude']
        target_lon = point['longitude']
        target_distance = point['distance']
        
        # 在目标点周围搜索景点
        nearby_places = []
        
        for place_data in available_places:
            # 计算到目标点的距离
            distance_result = geod.Inverse(
                target_lat, target_lon,
                place_data['latitude'], place_data['longitude']
            )
            distance_km = distance_result['s12'] / 1000  # 转换为公里
            
            # 如果在搜索半径内，添加到候选列表
            if distance_km <= search_radius_km:
                place_copy = place_data.copy()
                place_copy['distance_to_target'] = distance_km
                nearby_places.append(place_copy)
        
        # 按距离排序，选择最近的几个
        nearby_places.sort(key=lambda x: x['distance_to_target'])
        
        # 如果找到了真实景点，使用它们
        if nearby_places:
            for i, place_data in enumerate(nearby_places[:3]):  # 最多3个景点
                # 为真实景点生成详细信息
                attraction_info = generate_attraction_details_for_real_place(place_data)
                
                place_info = PlaceInfo(
                    name=place_data['name'],
                    latitude=place_data['latitude'],
                    longitude=place_data['longitude'],
                    distance=target_distance,
                    description=f"距此约{place_data['distance_to_target']:.1f}公里 - {place_data['description']}",
                    image=place_data.get('image', attraction_info['image']),
                    country=place_data.get('country'),
                    city=place_data.get('city'),
                    opening_hours=attraction_info['opening_hours'],
                    ticket_price=attraction_info['ticket_price'],
                    booking_method=attraction_info['booking_method'],
                    category=attraction_info['category']
                )
                places.append(place_info)
        else:
            # 如果没有找到真实景点，生成虚拟景点（确保是景点类型）
            virtual_places = generate_virtual_attractions(point, time_mode, search_radius_km)
            # 过滤掉可能的行政区域信息
            filtered_places = [place for place in virtual_places if is_valid_attraction_name(place.name)]
            places.extend(filtered_places)
    
    return places

def generate_virtual_attractions(point, time_mode, search_radius_km):
    """为目标点生成虚拟景点"""
    lat, lon = point['latitude'], point['longitude']
    target_distance = point['distance']
    
    # 根据经纬度判断大致区域
    region_info = get_region_info(lat, lon)
    
    # 生成3个虚拟景点
    attractions = []
    attraction_types = ['自然景观', '文化古迹', '城市地标']
    
    for i, attraction_type in enumerate(attraction_types):
        # 在目标点周围随机生成景点位置
        import random
        offset_km = random.uniform(0.5, search_radius_km)
        bearing = random.uniform(0, 360)
        
        # 计算景点坐标
        attraction_point = geod.Direct(lat, lon, bearing, offset_km * 1000)
        
        # 根据时间模式和类型生成描述
        descriptions = {
            "present": {
                '自然景观': f"这里是{region_info['name']}的一处美丽自然景观，拥有独特的地理风貌和生态环境。",
                '文化古迹': f"位于{region_info['name']}的历史文化遗址，承载着丰富的历史文化内涵。",
                '城市地标': f"{region_info['name']}的现代化地标建筑，展现了当地的发展成就。"
            },
            "past": {
                '自然景观': f"一百年前，这里是{region_info['name']}的原始自然景观，保持着最初的生态面貌。",
                '文化古迹': f"古代{region_info['name']}的重要文化遗址，见证了历史的兴衰变迁。",
                '城市地标': f"过去的{region_info['name']}重要建筑，曾是当地的政治或商业中心。"
            }
        }
        
        # 生成详细信息
        attraction_info = generate_attraction_details(attraction_type, time_mode, region_info)
        attraction_name = f"{region_info['name']}{attraction_type}{i+1}"
        description = descriptions.get(time_mode, descriptions["present"])[attraction_type]
        
        place_info = PlaceInfo(
            name=attraction_name,
            latitude=attraction_point['lat2'],
            longitude=attraction_point['lon2'],
            distance=target_distance,
            description=f"距此约{offset_km:.1f}公里 - {description}",
            image=attraction_info['image'],
            country=region_info['country'],
            city=region_info['city'],
            opening_hours=attraction_info['opening_hours'],
            ticket_price=attraction_info['ticket_price'],
            booking_method=attraction_info['booking_method'],
            category=attraction_type
        )
        attractions.append(place_info)
    
    return attractions

def is_valid_attraction_name(name: str) -> bool:
    """验证是否为有效的景点名称（非行政区域）"""
    name_lower = name.lower()
    
    # 行政区域关键词
    administrative_keywords = [
        '区', '市', '县', '省', '街道', '镇', '乡', '村', '路', '街',
        'district', 'city', 'county', 'province', 'street', 'road',
        '行政区', '管辖区', '辖区', '开发区', '新区'
    ]
    
    # 景点关键词
    attraction_keywords = [
        '陵', '寺', '庙', '宫', '园', '山', '湖', '塔', '桥', '城', '馆', '院',
        '景区', '景点', '风景', '名胜', '古迹', '遗址', '博物', '纪念', '公园',
        'temple', 'palace', 'park', 'mountain', 'lake', 'tower', 'museum',
        'attraction', 'scenic', 'monument', 'memorial'
    ]
    
    # 检查是否包含景点关键词
    has_attraction_keyword = any(keyword in name_lower for keyword in attraction_keywords)
    
    # 检查是否为行政区域
    is_administrative = any(keyword in name_lower for keyword in administrative_keywords)
    
    # 如果明确包含景点关键词，认为是有效景点
    if has_attraction_keyword:
        return True
    
    # 如果是行政区域，过滤掉
    if is_administrative:
        return False
    
    return True

def generate_attraction_details(attraction_type, time_mode, region_info):
    """生成景点的详细信息"""
    import random
    
    # 根据景点类型和时间模式生成信息
    details = {
        "自然景观": {
            "present": {
                "opening_hours": "全天开放",
                "ticket_price": "免费",
                "booking_method": "无需预约，直接前往",
                "images": [
                    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
                    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
                    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400"
                ]
            },
            "past": {
                "opening_hours": "日出至日落",
                "ticket_price": "免费",
                "booking_method": "古代无需门票，自由游览",
                "images": [
                    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400",
                    "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400"
                ]
            }
        },
        "文化古迹": {
            "present": {
                "opening_hours": "09:00-17:00（周一闭馆）",
                "ticket_price": f"成人票：{random.choice(['30', '50', '80', '120'])}元",
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
                    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400",
                    "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=400"
                ]
            }
        },
        "城市地标": {
            "present": {
                "opening_hours": "10:00-22:00",
                "ticket_price": f"观景台：{random.choice(['60', '80', '100', '150'])}元",
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
                    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400",
                    "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400"
                ]
            }
        }
    }
    
    type_details = details.get(attraction_type, details["自然景观"])
    mode_details = type_details.get(time_mode, type_details["present"])
    
    return {
        "opening_hours": mode_details["opening_hours"],
        "ticket_price": mode_details["ticket_price"],
        "booking_method": mode_details["booking_method"],
        "image": random.choice(mode_details["images"])
    }

def generate_attraction_details_for_real_place(place_data):
    """为真实景点生成详细信息"""
    import random
    
    # 根据景点名称推测类型
    name = place_data['name'].lower()
    if any(word in name for word in ['山', '湖', '河', '海', '森林', '公园', '自然', '风景']):
        category = '自然景观'
    elif any(word in name for word in ['寺', '庙', '宫', '城', '古', '遗址', '博物馆', '纪念']):
        category = '文化古迹'
    else:
        category = '城市地标'
    
    # 生成合理的营业信息
    if category == '自然景观':
        opening_hours = random.choice([
            "全天开放",
            "06:00-18:00",
            "日出至日落"
        ])
        ticket_price = random.choice([
            "免费",
            "成人票：20元",
            "成人票：30元"
        ])
        booking_method = "无需预约，直接前往"
        image = "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400"
        
    elif category == '文化古迹':
        opening_hours = random.choice([
            "09:00-17:00（周一闭馆）",
            "08:30-17:30",
            "09:00-16:30（冬季）"
        ])
        ticket_price = f"成人票：{random.choice(['40', '60', '80', '100'])}元"
        booking_method = random.choice([
            "现场购票或官方网站预约",
            "建议提前网上预约",
            "现场购票，旺季建议预约"
        ])
        image = "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=400"
        
    else:  # 城市地标
        opening_hours = random.choice([
            "10:00-22:00",
            "09:00-21:00",
            "全天开放（外观）"
        ])
        ticket_price = f"观景台：{random.choice(['50', '80', '120', '150'])}元"
        booking_method = random.choice([
            "现场购票、手机APP或官方网站",
            "支持现场购票和在线预订",
            "建议提前在线购票"
        ])
        image = "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=400"
    
    return {
        "opening_hours": opening_hours,
        "ticket_price": ticket_price,
        "booking_method": booking_method,
        "category": category,
        "image": image
    }

def generate_virtual_place(point, time_mode):
    """为没有匹配地点的路径点生成虚拟地点信息"""
    lat, lon = point['latitude'], point['longitude']
    
    # 根据经纬度判断大致区域
    region_info = get_region_info(lat, lon)
    
    # 根据时间模式生成不同的描述
    descriptions = {
        "present": f"这里是{region_info['name']}的一片神秘土地，等待着探索者的发现。现代文明的痕迹在这里若隐若现。",
        "past": f"一百年前，这里是{region_info['name']}的荒野之地，只有少数勇敢的探险家曾经踏足。",
        "future": f"未来的{region_info['name']}，这里可能建立起新的城市，或成为重要的科研基地。"
    }
    
    return PlaceInfo(
        name=f"{region_info['name']}神秘之地",
        latitude=lat,
        longitude=lon,
        distance=point['distance'],
        description=descriptions.get(time_mode, descriptions["present"]),
        image="https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
        country=region_info['country'],
        city=region_info['city']
    )

def get_region_info(lat, lon):
    """根据经纬度获取区域信息"""
    # 简单的区域判断逻辑
    if lat > 60:
        return {"name": "北极", "country": "极地", "city": "极地"}
    elif lat < -60:
        return {"name": "南极", "country": "极地", "city": "极地"}
    elif -30 <= lat <= 70 and -10 <= lon <= 60:
        return {"name": "欧亚大陆", "country": "欧亚", "city": "未知"}
    elif -30 <= lat <= 50 and 60 <= lon <= 150:
        return {"name": "亚洲内陆", "country": "亚洲", "city": "未知"}
    elif -50 <= lat <= 40 and -180 <= lon <= -30:
        return {"name": "美洲大陆", "country": "美洲", "city": "未知"}
    elif -40 <= lat <= 10 and 110 <= lon <= 180:
        return {"name": "大洋洲", "country": "大洋洲", "city": "未知"}
    elif -40 <= lat <= 40 and -20 <= lon <= 60:
        return {"name": "非洲大陆", "country": "非洲", "city": "未知"}
    else:
        return {"name": "海洋", "country": "海洋", "city": "海域"}

@app.on_event("startup")
async def startup_event():
    """应用启动时加载数据"""
    load_places_data()
    print("地点数据加载完成")

@app.get("/")
async def root():
    return {"message": "方向探索派对API服务正在运行"}

@app.post("/api/explore", response_model=ExploreResponse)
async def explore_direction(request: ExploreRequest):
    """探索指定方向的地点"""
    import time
    start_time = time.time()
    
    try:
        # 验证输入参数
        if not (-90 <= request.latitude <= 90):
            raise HTTPException(status_code=400, detail="纬度必须在-90到90之间")
        if not (-180 <= request.longitude <= 180):
            raise HTTPException(status_code=400, detail="经度必须在-180到180之间")
        if not (0 <= request.heading < 360):
            raise HTTPException(status_code=400, detail="方向必须在0到360度之间")
        if request.segment_distance <= 0:
            raise HTTPException(status_code=400, detail="分段距离必须大于0")
        
        # 只计算到目标距离点
        target_distance = request.segment_distance
        
        # 计算目标距离点的坐标
        target_point = geod.Direct(
            request.latitude, 
            request.longitude, 
            request.heading, 
            target_distance * 1000  # 转换为米
        )
        
        # 创建目标点
        points = [{
            'latitude': target_point['lat2'],
            'longitude': target_point['lon2'],
            'distance': target_distance
        }]
        
        # 在目标点周围5km范围内搜索景点
        places = find_nearby_attractions(points, request.time_mode, search_radius_km=5)
        
        # 计算总距离
        total_distance = points[-1]['distance'] if points else 0
        
        calculation_time = time.time() - start_time
        
        return ExploreResponse(
            places=places,
            total_distance=total_distance,
            calculation_time=calculation_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算错误: {str(e)}")

@app.post("/api/explore-real", response_model=ExploreResponse)
async def explore_direction_real(request: ExploreRequest):
    """探索指定方向的地点（使用真实数据）"""
    import time
    start_time = time.time()
    
    try:
        # 验证输入参数
        if not (-90 <= request.latitude <= 90):
            raise HTTPException(status_code=400, detail="纬度必须在-90到90之间")
        if not (-180 <= request.longitude <= 180):
            raise HTTPException(status_code=400, detail="经度必须在-180到180之间")
        if not (0 <= request.heading < 360):
            raise HTTPException(status_code=400, detail="方向必须在0到360度之间")
        if request.segment_distance <= 0:
            raise HTTPException(status_code=400, detail="分段距离必须大于0")
        
        # 只计算到目标距离点
        target_distance = request.segment_distance
        
        # 计算目标距离点的坐标
        target_point = geod.Direct(
            request.latitude, 
            request.longitude, 
            request.heading, 
            target_distance * 1000  # 转换为米
        )
        
        # 创建目标点
        points = [{
            'latitude': target_point['lat2'],
            'longitude': target_point['lon2'],
            'distance': target_distance
        }]
        
        # 使用本地数据库获取附近景点信息
        target_lat = target_point['lat2']
        target_lon = target_point['lon2']
        
        # 从本地数据库中获取附近景点，搜索半径50km
        places_data_list = local_attractions_db.find_nearby_attractions(target_lat, target_lon, radius_km=50)
        
        # 🆕 如果本地数据库没有找到景点，尝试从全球城市数据库搜索
        if len(places_data_list) == 0:
            logger.info("本地数据库未找到景点，尝试从全球城市数据库搜索...")
            global_cities_db = GlobalCitiesDB()
            places_data_list = global_cities_db.find_nearby_attractions(target_lat, target_lon, radius_km=50)
            logger.info(f"从全球城市数据库中找到 {len(places_data_list)} 个景点，距离目标点 ({target_lat:.4f}, {target_lon:.4f}) 50km 以内")
        else:
            logger.info(f"从本地数据库中找到 {len(places_data_list)} 个景点，距离目标点 ({target_lat:.4f}, {target_lon:.4f}) 50km 以内")
        
        # 转换为PlaceInfo对象
        places = []
        for place_data in places_data_list:
            # 构建图片URL（取第一张图片）
            image_url = place_data.get('image', None)
            
            place_info = PlaceInfo(
                name=place_data['name'],
                latitude=place_data['latitude'],
                longitude=place_data['longitude'],
                distance=place_data.get('distance', 0),  # 使用distance字段，如果没有则默认为0
                description=place_data['description'],
                image=image_url,
                video=place_data.get('video', None),
                country=place_data.get('country', '中国'),
                city=place_data.get('city', '北京'),
                opening_hours=place_data.get('opening_hours', '详询景点'),
                ticket_price=place_data.get('ticket_price'),
                booking_method=place_data.get('booking_method'),
                category=place_data.get('category')
            )
            places.append(place_info)
        
        # 计算总距离
        total_distance = points[-1]['distance'] if points else 0
        
        calculation_time = time.time() - start_time
        
        return ExploreResponse(
            places=places,
            total_distance=total_distance,
            calculation_time=calculation_time
        )
        
    except Exception as e:
        print(f"真实数据探索错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"真实数据获取错误: {str(e)}")

@app.get("/api/places/{time_mode}")
async def get_places(time_mode: str):
    """获取指定时间模式的所有地点"""
    if time_mode not in places_data:
        raise HTTPException(status_code=404, detail="时间模式不存在")
    
    return {"places": places_data[time_mode]}

# 地理编码相关的数据模型
class GeocodeRequest(BaseModel):
    query: str

class GeocodeResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str

class PlaceDetailsRequest(BaseModel):
    place_id: str
    lat: float
    lng: float

@app.post("/api/geocode", response_model=GeocodeResponse)
async def geocode_location(request: GeocodeRequest):
    """地理编码服务 - 优先使用高德地图，备用Google Maps"""
    try:
        # 检查缓存
        cache_key = request.query.lower().strip()
        if cache_key in geocode_cache:
            logger.info(f"从缓存返回地理编码结果: {cache_key}")
            return GeocodeResponse(
                success=True,
                data=geocode_cache[cache_key],
                message=f"缓存命中: {cache_key}"
            )
        
        # 导入必要的库
        import googlemaps
        import requests
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # 首先检查本地快速匹配
        fallback_locations = {
            "北京": {"lat": 39.9042, "lng": 116.4074, "address": "北京市"},
            "上海": {"lat": 31.2304, "lng": 121.4737, "address": "上海市"},
            "广州": {"lat": 23.1291, "lng": 113.2644, "address": "广州市"},
            "深圳": {"lat": 22.5431, "lng": 114.0579, "address": "深圳市"},
            "天安门": {"lat": 39.9042, "lng": 116.4074, "address": "北京市东城区天安门"},
            "故宫": {"lat": 39.9163, "lng": 116.3972, "address": "北京市东城区故宫"},
        }
        
        # 快速匹配常用地点
        for city, info in fallback_locations.items():
            if city in request.query:
                result = {
                    "formatted_address": info["address"],
                    "geometry": {
                        "location": {"lat": info["lat"], "lng": info["lng"]},
                        "location_type": "APPROXIMATE"
                    },
                    "place_id": f"fallback_{city}",
                    "address_components": [],
                    "types": ["locality", "political"]
                }
                logger.info(f"使用本地快速匹配: {info['address']}")
                
                # 添加到缓存
                geocode_cache[cache_key] = result
                if len(geocode_cache) > cache_max_size:
                    # 删除最旧的缓存条目
                    oldest_key = next(iter(geocode_cache))
                    del geocode_cache[oldest_key]
                
                return GeocodeResponse(
                    success=True,
                    data=result,
                    message=f"快速匹配找到位置: {info['address']}"
                )
        
        # 然后尝试高德地图API
        amap_key = os.getenv("AMAP_API_KEY")
        if amap_key:
            try:
                logger.info(f"调用高德地图API查询: {request.query}")
                url = "https://restapi.amap.com/v3/geocode/geo"
                params = {
                    'key': amap_key,
                    'address': request.query,
                    'output': 'json'
                }
                
                response = requests.get(url, params=params, timeout=10)  # 增加超时时间到10秒
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"高德地图API响应: {data}")
                    if data.get('status') == '1' and data.get('geocodes'):
                        geocode = data['geocodes'][0]
                        location = geocode['location'].split(',')
                        
                        result = {
                            "formatted_address": geocode.get('formatted_address', request.query),
                            "geometry": {
                                "location": {
                                    "lat": float(location[1]),
                                    "lng": float(location[0])
                                },
                                "location_type": "APPROXIMATE"
                            },
                            "place_id": f"amap_{geocode.get('adcode', 'unknown')}",
                            "address_components": [
                                {
                                    "long_name": geocode.get('district', ''),
                                    "short_name": geocode.get('district', ''),
                                    "types": ["administrative_area_level_3", "political"]
                                },
                                {
                                    "long_name": geocode.get('city', ''),
                                    "short_name": geocode.get('city', ''),
                                    "types": ["administrative_area_level_2", "political"]
                                },
                                {
                                    "long_name": geocode.get('province', ''),
                                    "short_name": geocode.get('province', ''),
                                    "types": ["administrative_area_level_1", "political"]
                                },
                                {
                                    "long_name": "中国",
                                    "short_name": "CN",
                                    "types": ["country", "political"]
                                }
                            ],
                            "types": ["geocode"]
                        }
                        
                        logger.info(f"高德地图成功找到位置: {result['formatted_address']}")
                        
                        # 添加到缓存
                        geocode_cache[cache_key] = result
                        if len(geocode_cache) > cache_max_size:
                            # 删除最旧的缓存条目
                            oldest_key = next(iter(geocode_cache))
                            del geocode_cache[oldest_key]
                        
                        return GeocodeResponse(
                            success=True,
                            data=result,
                            message=f"高德地图找到位置: {result['formatted_address']}"
                        )
                    else:
                        logger.warning(f"高德地图API返回错误: {data.get('info', 'Unknown error')}")
                else:
                    logger.warning(f"高德地图API请求失败: HTTP {response.status_code}")
            except Exception as e:
                logger.warning(f"高德地图地理编码失败: {e}")
        
        # 备用Google Maps API
        google_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if google_key:
            try:
                gmaps = googlemaps.Client(key=google_key)
                geocode_result = gmaps.geocode(request.query)
                
                if geocode_result:
                    result = geocode_result[0]
                    return GeocodeResponse(
                        success=True,
                        data=result,
                        message=f"Google Maps找到位置: {result['formatted_address']}"
                    )
            except Exception as e:
                logger.warning(f"Google Maps地理编码失败: {e}")
        
        # 如果前面的快速匹配和高德地图都失败了，返回错误
        
        return GeocodeResponse(
            success=False,
            message=f"无法找到位置: {request.query}"
        )
        
    except Exception as e:
        logger.error(f"地理编码服务错误: {e}")
        return GeocodeResponse(
            success=False,
            message=f"地理编码服务错误: {str(e)}"
        )

@app.post("/api/place-details")
async def get_place_details(request: PlaceDetailsRequest):
    """获取地点详细信息"""
    try:
        # 从本地数据库查找匹配的景点
        for attraction in local_attractions_db.attractions:
            # 计算距离，如果很近就认为是同一个地点
            distance = local_attractions_db.calculate_distance(
                request.lat, request.lng,
                attraction['latitude'], attraction['longitude']
            )
            
            if distance < 1000:  # 1公里内认为是同一地点
                return {
                    "success": True,
                    "data": {
                        "name": attraction['name'],
                        "formatted_address": attraction.get('address', f"{attraction['city']}{attraction['name']}"),
                        "photos": [{"photo_reference": attraction.get('image', '')}] if attraction.get('image') else [],
                        "rating": 4.5,
                        "user_ratings_total": 1000,
                        "opening_hours": {"weekday_text": [attraction.get('opening_hours', '详询景点')]},
                        "geometry": {
                            "location": {
                                "lat": attraction['latitude'],
                                "lng": attraction['longitude']
                            }
                        }
                    },
                    "message": f"找到地点详情: {attraction['name']}"
                }
        
        # 如果本地没找到，返回基本信息
        return {
            "success": True,
            "data": {
                "name": "未知地点",
                "formatted_address": f"纬度: {request.lat:.4f}, 经度: {request.lng:.4f}",
                "photos": [],
                "rating": 0,
                "user_ratings_total": 0,
                "opening_hours": {"weekday_text": ["营业时间未知"]},
                "geometry": {
                    "location": {"lat": request.lat, "lng": request.lng}
                }
            },
            "message": "返回基本位置信息"
        }
        
    except Exception as e:
        logger.error(f"获取地点详情错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取地点详情错误: {str(e)}")

@app.get("/api/config/maps")
async def get_maps_config():
    """获取地图配置信息"""
    return {
        "google_maps_api_key": os.getenv("GOOGLE_MAPS_API_KEY", ""),
        "amap_api_key": os.getenv("AMAP_API_KEY", ""),
        "default_location": {"lat": 39.9042, "lng": 116.4074},
        "default_zoom": 10
    }

@app.get("/api/config/environment")
async def get_environment_config():
    """
    获取环境配置
    
    Returns:
        环境配置信息，包括API基础URL等
    """
    try:
        # 检查环境变量 isUsedomainnameaddress
        use_domain_name = os.getenv("isUsedomainnameaddress", "false").lower() == "true"
        
        # 根据环境变量决定API基础URL
        if use_domain_name:
            api_base_url = "https://spot.gitagent.io"
            environment = "production"
        else:
            api_base_url = "http://localhost:8001"
            environment = "local"
        
        # 获取服务器信息
        import socket
        hostname = socket.gethostname()
        
        config = {
            "success": True,
            "environment": environment,
            "api_base_url": api_base_url,
            "use_domain_name": use_domain_name,
            "server_info": {
                "hostname": hostname,
                "backend_port": 8001,
                "frontend_port": 3001
            },
            "timestamp": time.time()
        }
        
        logger.info(f"环境配置请求: {environment} - {api_base_url}")
        return config
        
    except Exception as e:
        logger.error(f"获取环境配置失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "environment": "local",
            "api_base_url": "http://localhost:8001",
            "use_domain_name": False
        }

# 旅程管理辅助函数
def generate_journey_id():
    """生成唯一的旅程ID"""
    global journey_counter
    journey_counter += 1
    return f"journey_{journey_counter}_{int(time.time())}"

def create_journey(start_lat: float, start_lng: float, start_name: str, title: str):
    """创建新旅程"""
    journey_id = generate_journey_id()
    journey_data = {
        "id": journey_id,
        "title": title,
        "start_time": time.time(),
        "start_location": {
            "lat": start_lat,
            "lng": start_lng,
            "name": start_name
        },
        "visited_scenes": [],
        "status": "active"
    }
    active_journeys[journey_id] = journey_data
    return journey_id

@app.post("/api/journey/start", response_model=JourneyResponse)
async def start_journey(request: StartJourneyRequest):
    """开始新旅程"""
    try:
        # 验证输入参数
        if not (-90 <= request.start_lat <= 90):
            raise HTTPException(status_code=400, detail="纬度必须在-90到90之间")
        if not (-180 <= request.start_lng <= 180):
            raise HTTPException(status_code=400, detail="经度必须在-180到180之间")
        
        # 创建新旅程
        journey_id = create_journey(
            request.start_lat,
            request.start_lng,
            request.start_name,
            request.journey_title
        )
        
        logger.info(f"创建新旅程: {journey_id}, 标题: {request.journey_title}")
        logger.info(f"起始位置: {request.start_name} ({request.start_lat:.4f}, {request.start_lng:.4f})")
        
        return JourneyResponse(
            success=True,
            message=f"旅程 '{request.journey_title}' 已开始",
            journey_id=journey_id
        )
        
    except Exception as e:
        logger.error(f"创建旅程失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建旅程失败: {str(e)}")

# 城市相关数据模型
class CityInfo(BaseModel):
    key: str
    name: str
    country: str
    coordinates: List[float]
    type: str
    attraction_count: int

class AttractionInfo(BaseModel):
    name: str
    latitude: float
    longitude: float
    category: str
    description: str
    opening_hours: str
    ticket_price: str
    booking_method: str
    image: Optional[str] = None
    video: Optional[str] = None
    country: str
    city: str
    address: str

class CityRoamingRequest(BaseModel):
    city_key: str

class CityRoamingResponse(BaseModel):
    success: bool
    message: str
    city_info: Optional[dict] = None
    attraction: Optional[AttractionInfo] = None

# 城市相关API端点
@app.get("/api/cities", response_model=List[CityInfo])
async def get_all_cities():
    """获取所有可用城市列表"""
    try:
        cities = global_cities_db.get_all_cities()
        return cities
    except Exception as e:
        logger.error(f"获取城市列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取城市列表失败: {str(e)}")

@app.get("/api/cities/search")
async def search_cities(query: str):
    """搜索城市"""
    try:
        cities = global_cities_db.search_cities(query)
        return {"cities": cities}
    except Exception as e:
        logger.error(f"搜索城市失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索城市失败: {str(e)}")

@app.get("/api/cities/{city_key}/attractions", response_model=List[AttractionInfo])
async def get_city_attractions(city_key: str):
    """获取指定城市的所有景点"""
    try:
        # 特殊处理北京，从现有数据库获取
        if city_key == "beijing":
            attractions = local_attractions_db.attractions
            return [
                AttractionInfo(
                    name=attr["name"],
                    latitude=attr["latitude"],
                    longitude=attr["longitude"],
                    category=attr["category"],
                    description=attr["description"],
                    opening_hours=attr["opening_hours"],
                    ticket_price=attr["ticket_price"],
                    booking_method=attr["booking_method"],
                    image=attr.get("image"),
                    video=attr.get("video"),
                    country=attr["country"],
                    city=attr["city"],
                    address=attr["address"]
                ) for attr in attractions
            ]
        
        attractions = global_cities_db.get_city_attractions(city_key)
        if not attractions:
            raise HTTPException(status_code=404, detail=f"未找到城市 {city_key} 的景点信息")
        
        return [
            AttractionInfo(
                name=attr["name"],
                latitude=attr["latitude"],
                longitude=attr["longitude"],
                category=attr["category"],
                description=attr["description"],
                opening_hours=attr["opening_hours"],
                ticket_price=attr["ticket_price"],
                booking_method=attr["booking_method"],
                image=attr.get("image"),
                video=attr.get("video"),
                country=attr["country"],
                city=attr["city"],
                address=attr["address"]
            ) for attr in attractions
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取城市景点失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取城市景点失败: {str(e)}")

@app.post("/api/cities/roam", response_model=CityRoamingResponse)
async def roam_to_city(request: CityRoamingRequest):
    """漫游到指定城市，随机选择一个景点"""
    try:
        city_info = global_cities_db.get_city_by_key(request.city_key)
        if not city_info:
            return CityRoamingResponse(
                success=False,
                message=f"未找到城市 {request.city_key}",
                city_info=None,
                attraction=None
            )
        
        # 特殊处理北京
        if request.city_key == "beijing":
            import random
            attraction_data = random.choice(local_attractions_db.attractions)
        else:
            attraction_data = global_cities_db.get_random_attraction(request.city_key)
        
        if not attraction_data:
            return CityRoamingResponse(
                success=False,
                message=f"城市 {city_info['name']} 暂无景点信息",
                city_info=city_info,
                attraction=None
            )
        
        attraction = AttractionInfo(
            name=attraction_data["name"],
            latitude=attraction_data["latitude"],
            longitude=attraction_data["longitude"],
            category=attraction_data["category"],
            description=attraction_data["description"],
            opening_hours=attraction_data["opening_hours"],
            ticket_price=attraction_data["ticket_price"],
            booking_method=attraction_data["booking_method"],
            image=attraction_data.get("image"),
            video=attraction_data.get("video"),
            country=attraction_data["country"],
            city=attraction_data["city"],
            address=attraction_data["address"]
        )
        
        return CityRoamingResponse(
            success=True,
            message=f"成功漫游到 {city_info['name']} - {attraction.name}",
            city_info=city_info,
            attraction=attraction
        )
        
    except Exception as e:
        logger.error(f"城市漫游失败: {str(e)}")
        return CityRoamingResponse(
            success=False,
            message=f"城市漫游失败: {str(e)}",
            city_info=None,
            attraction=None
        )

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "方向探索派对API",
        "version": "1.0.0"
    }

@app.get("/api/gemini-health")
async def gemini_health_check():
    """Gemini服务健康检查端点"""
    try:
        health_status = await gemini_service.health_check()
        return {
            "success": True,
            "data": health_status
        }
    except Exception as e:
        logger.error(f"Gemini健康检查失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "status": "error",
                "message": "健康检查失败",
                "api_accessible": False
            }
        }

@app.post("/api/generate-attraction-photo")
async def generate_attraction_photo(
    user_photo: UploadFile = File(...),
    attraction_name: str = Form(...),
    style_photo: Optional[UploadFile] = File(None),
    location: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    opening_hours: Optional[str] = Form(None),
    ticket_price: Optional[str] = Form(None),
    latitude: Optional[str] = Form(None),
    longitude: Optional[str] = Form(None),
    custom_prompt: Optional[str] = Form(None)
):
    """
    生成景点合影照片
    
    Args:
        user_photo: 用户上传的照片
        attraction_name: 景点名称
        style_photo: 范例照片（可选）- 用于风格迁移
        location: 景点位置（可选）
        category: 景点类别（可选）
        description: 景点描述（可选）
        opening_hours: 开放时间（可选）
        ticket_price: 门票价格（可选）
        latitude: 纬度（可选）
        longitude: 经度（可选）
        custom_prompt: 自定义提示词（可选）
        
    Returns:
        生成的合影照片信息
    """
    try:
        logger.info(f"收到景点合影生成请求: {attraction_name}")
        
        # 验证文件类型
        if not user_photo.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="请上传有效的图片文件")
        
        # 转换坐标参数
        lat_float = None
        lng_float = None
        if latitude:
            try:
                lat_float = float(latitude)
            except ValueError:
                pass
        if longitude:
            try:
                lng_float = float(longitude)
            except ValueError:
                pass
        
        # 调用Gemini服务生成合影
        success, message, result = await gemini_service.generate_attraction_photo(
            user_photo=user_photo,
            attraction_name=attraction_name,
            style_photo=style_photo,
            location=location,
            category=category,
            description=description,
            opening_hours=opening_hours,
            ticket_price=ticket_price,
            latitude=lat_float,
            longitude=lng_float,
            custom_prompt=custom_prompt
        )
        
        if success and result:
            return {
                "success": True,
                "message": message,
                "data": {
                    "image_url": result["base64"],  # 返回base64编码的图片
                    "filename": result["filename"],
                    "attraction": result["attraction"],
                    "prompt": result["prompt"]
                }
            }
        else:
            # 如果result包含错误详情，返回详细信息而不是抛出异常
            if result and isinstance(result, dict) and result.get("type") == "ai_feedback":
                return {
                    "success": False,
                    "message": message,
                    "error_details": result
                }
            else:
                raise HTTPException(status_code=500, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成景点合影时出错: {e}")
        raise HTTPException(status_code=500, detail=f"生成景点合影失败: {str(e)}")

@app.get("/api/generated-images")
async def get_generated_images(limit: int = 10):
    """
    获取最近生成的合影照片列表
    
    Args:
        limit: 返回的图片数量限制
        
    Returns:
        生成的图片列表
    """
    try:
        images = gemini_service.get_generated_images(limit=limit)
        return {
            "success": True,
            "data": images
        }
    except Exception as e:
        logger.error(f"获取生成的图片列表时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取图片列表失败: {str(e)}")

# ================== Doro合影相关端点 ==================

@app.get("/api/doro/list")
async def get_doro_list():
    """
    获取所有Doro形象列表
    
    Returns:
        包含预设和自定义Doro的列表
    """
    try:
        doro_list = doro_service.get_all_doros()
        return {
            "success": True,
            "data": doro_list
        }
    except Exception as e:
        logger.error(f"获取Doro列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取Doro列表失败: {str(e)}")

@app.get("/api/doro/random")
async def get_random_doro():
    """
    获取随机Doro形象
    
    Returns:
        随机选择的Doro信息
    """
    try:
        random_doro = doro_service.get_random_doro()
        if not random_doro:
            raise HTTPException(status_code=404, detail="没有可用的Doro形象")
        
        return {
            "success": True,
            "data": random_doro
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取随机Doro失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取随机Doro失败: {str(e)}")

@app.post("/api/doro/upload")
async def upload_custom_doro(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """
    上传自定义Doro形象
    
    Args:
        file: 图片文件
        name: 自定义名称
        description: 自定义描述
        
    Returns:
        保存的Doro信息
    """
    try:
        doro_info = await doro_service.save_custom_doro(file, name, description)
        return {
            "success": True,
            "data": doro_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传自定义Doro失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@app.get("/api/doro/image/{doro_id}")
async def get_doro_image(doro_id: str):
    """
    获取Doro图片文件
    
    Args:
        doro_id: Doro的ID
        
    Returns:
        图片文件
    """
    try:
        image_path = doro_service.get_doro_by_id(doro_id)
        if not image_path:
            raise HTTPException(status_code=404, detail="Doro图片不存在")
        
        return FileResponse(
            path=str(image_path),
            media_type="image/png"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Doro图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")

@app.get("/api/doro/thumbnail/{doro_id}")
async def get_doro_thumbnail(doro_id: str):
    """
    获取Doro缩略图
    
    Args:
        doro_id: Doro的ID
        
    Returns:
        缩略图文件
    """
    try:
        # 暂时返回原图，后续可以实现真正的缩略图生成
        image_path = doro_service.get_doro_by_id(doro_id)
        if not image_path:
            raise HTTPException(status_code=404, detail="Doro图片不存在")
        
        return FileResponse(
            path=str(image_path),
            media_type="image/png"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Doro缩略图失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缩略图失败: {str(e)}")

@app.post("/api/doro/generate")
async def generate_doro_selfie(
    user_photo: UploadFile = File(...),
    doro_image: Optional[UploadFile] = File(None),
    doro_id: Optional[str] = Form(None),
    style_photo: Optional[UploadFile] = File(None),
    attraction_name: str = Form(...),
    attraction_type: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    doro_style: Optional[str] = Form("default"),
    user_description: Optional[str] = Form(None),
    time_of_day: Optional[str] = Form(None),
    weather: Optional[str] = Form(None),
    season: Optional[str] = Form(None),
    mood: Optional[str] = Form(None)
):
    """
    生成Doro合影
    
    Args:
        user_photo: 用户照片
        doro_image: Doro图片文件（与doro_id二选一）
        doro_id: Doro ID（与doro_image二选一）
        style_photo: 服装风格参考（可选）
        attraction_name: 景点名称
        attraction_type: 景点类型
        location: 地理位置
        doro_style: Doro风格
        user_description: 用户额外描述
        time_of_day: 时间段
        weather: 天气
        season: 季节
        mood: 情绪氛围
        
    Returns:
        生成的合影信息
    """
    try:
        # 获取Doro图片
        if doro_image:
            # 使用上传的Doro图片
            doro_photo = doro_image
        elif doro_id:
            # 使用预设或已保存的Doro
            doro_path = doro_service.get_doro_by_id(doro_id)
            if not doro_path:
                raise HTTPException(status_code=404, detail="指定的Doro不存在")
            
            # 创建临时文件对象
            with open(doro_path, 'rb') as f:
                doro_content = f.read()
            
            # 创建UploadFile对象 - 修复BytesIO指针问题
            import io
            doro_file = io.BytesIO(doro_content)
            doro_file.seek(0)  # 确保指针在开始位置
            doro_photo = UploadFile(
                filename=doro_path.name,
                file=doro_file
            )
        else:
            raise HTTPException(status_code=400, detail="必须提供Doro图片或Doro ID")
        
        # 准备景点信息
        attraction_info = {
            "name": attraction_name,
            "category": attraction_type,
            "location": location,
            "doro_style": doro_style,
            "user_description": user_description,
            "time_of_day": time_of_day,
            "weather": weather,
            "season": season,
            "mood": mood
        }
        
        # 调用Gemini服务生成合影
        success, message, result = await gemini_service.generate_doro_selfie_with_attraction(
            user_photo=user_photo,
            doro_photo=doro_photo,
            style_photo=style_photo,
            attraction_info=attraction_info
        )
        
        if success:
            return {
                "success": True,
                "message": message,
                "data": result
            }
        else:
            raise HTTPException(status_code=500, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成Doro合影失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@app.post("/api/doro/generate-video")
async def generate_doro_video(
    user_photo: UploadFile = File(...),
    doro_image: Optional[UploadFile] = File(None),
    doro_id: Optional[str] = Form(None),
    style_photo: Optional[UploadFile] = File(None),
    attraction_name: str = Form(...),
    attraction_type: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    doro_style: Optional[str] = Form("default"),
    user_description: Optional[str] = Form(None),
    time_of_day: Optional[str] = Form(None),
    weather: Optional[str] = Form(None),
    season: Optional[str] = Form(None),
    mood: Optional[str] = Form(None)
):
    """
    生成Doro合影视频
    
    使用Imagen生成静态合影图片，然后用Veo 3生成动态视频
    """
    try:
        # 获取Doro图片
        if doro_image:
            doro_photo = doro_image
        elif doro_id:
            doro_path = doro_service.get_doro_by_id(doro_id)
            if not doro_path:
                raise HTTPException(status_code=404, detail="指定的Doro不存在")
            
            # 创建UploadFile对象
            with open(doro_path, 'rb') as f:
                doro_content = f.read()
            
            import io
            doro_file = io.BytesIO(doro_content)
            doro_file.seek(0)
            doro_photo = UploadFile(
                filename=doro_path.name,
                file=doro_file
            )
        else:
            raise HTTPException(status_code=400, detail="必须提供Doro图片或Doro ID")
        
        # 准备景点信息
        attraction_info = {
            "name": attraction_name,
            "category": attraction_type,
            "location": location,
            "doro_style": doro_style,
            "user_description": user_description,
            "time_of_day": time_of_day,
            "weather": weather,
            "season": season,
            "mood": mood
        }
        
        # 调用Gemini服务生成视频
        success, message, result = await gemini_service.generate_doro_video_with_attraction(
            user_photo=user_photo,
            doro_photo=doro_photo,
            style_photo=style_photo,
            attraction_info=attraction_info
        )
        
        if success:
            return {
                "success": True,
                "message": message,
                "data": result
            }
        else:
            raise HTTPException(status_code=500, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成Doro合影视频失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成Doro合影视频失败: {str(e)}")


@app.delete("/api/doro/{doro_id}")
async def delete_custom_doro(doro_id: str):
    """
    删除自定义Doro
    
    Args:
        doro_id: 要删除的Doro ID
        
    Returns:
        删除结果
    """
    try:
        if not doro_id.startswith("custom_"):
            raise HTTPException(status_code=400, detail="只能删除自定义Doro")
        
        success = doro_service.delete_custom_doro(doro_id)
        if success:
            return {
                "success": True,
                "message": "Doro删除成功"
            }
        else:
            raise HTTPException(status_code=404, detail="Doro不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除Doro失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

# ================== 原有的下载端点 ==================

@app.get("/api/download-image/{filename}")
async def download_generated_image(filename: str):
    """
    下载生成的合影照片
    
    Args:
        filename: 图片文件名
        
    Returns:
        图片文件
    """
    try:
        filepath = os.path.join("backend/generated_images", filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="图片文件不存在")
        
        # 确保文件名安全
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="无效的文件名")
        
        return FileResponse(
            path=filepath,
            media_type="image/png",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载图片时出错: {e}")
        raise HTTPException(status_code=500, detail=f"下载图片失败: {str(e)}")

# ================== Supabase数据库API端点 ==================

@app.get("/api/spot/health")
async def spot_health_check():
    """Spot数据库服务健康检查"""
    try:
        health_status = await spot_api_service.health_check()
        return {
            "success": True,
            "data": health_status
        }
    except Exception as e:
        logger.error(f"Spot服务健康检查失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "status": "error",
                "database_connected": False
            }
        }

@app.get("/api/spot/attractions/nearby")
async def get_nearby_attractions_from_db(
    latitude: float,
    longitude: float,
    radius: float = 50
):
    """从Supabase数据库获取附近景点"""
    try:
        attractions = await spot_api_service.get_nearby_attractions(latitude, longitude, radius)
        return {
            "success": True,
            "data": attractions,
            "count": len(attractions),
            "message": f"找到 {len(attractions)} 个附近景点"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取附近景点失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取附近景点失败: {str(e)}")

@app.get("/api/spot/attractions")
async def get_all_attractions_from_db():
    """从Supabase数据库获取所有景点"""
    try:
        attractions = await spot_api_service.get_all_attractions()
        return {
            "success": True,
            "data": attractions,
            "count": len(attractions),
            "message": f"获取到 {len(attractions)} 个景点"
        }
    except Exception as e:
        logger.error(f"获取所有景点失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取所有景点失败: {str(e)}")

@app.get("/api/spot/attractions/category/{category}")
async def get_attractions_by_category_from_db(category: str):
    """从Supabase数据库根据类别获取景点"""
    try:
        attractions = await spot_api_service.get_attractions_by_category(category)
        return {
            "success": True,
            "data": attractions,
            "count": len(attractions),
            "message": f"找到 {len(attractions)} 个 {category} 类景点"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"根据类别获取景点失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取景点失败: {str(e)}")

@app.get("/api/spot/attractions/city/{city}")
async def get_attractions_by_city_from_db(city: str):
    """从Supabase数据库根据城市获取景点"""
    try:
        attractions = await spot_api_service.get_attractions_by_city(city)
        return {
            "success": True,
            "data": attractions,
            "count": len(attractions),
            "message": f"找到 {len(attractions)} 个 {city} 的景点"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"根据城市获取景点失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取景点失败: {str(e)}")

@app.get("/api/spot/attractions/search")
async def search_attractions_from_db(query: str):
    """从Supabase数据库搜索景点"""
    try:
        attractions = await spot_api_service.search_attractions(query)
        return {
            "success": True,
            "data": attractions,
            "count": len(attractions),
            "message": f"搜索到 {len(attractions)} 个相关景点"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索景点失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.post("/api/spot/albums")
async def create_album_in_db(
    creator_id: str,
    title: str,
    description: str = None,
    access_level: str = "public"
):
    """在Supabase数据库中创建新相册"""
    try:
        album = await spot_api_service.create_album(creator_id, title, description, access_level)
        return {
            "success": True,
            "data": album,
            "message": f"相册 '{title}' 创建成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建相册失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建相册失败: {str(e)}")

@app.get("/api/spot/albums/public")
async def get_public_albums_from_db(limit: int = 20, offset: int = 0):
    """从Supabase数据库获取公开相册"""
    try:
        albums = await spot_api_service.get_public_albums(limit, offset)
        return {
            "success": True,
            "data": albums,
            "count": len(albums),
            "message": f"获取到 {len(albums)} 个公开相册"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取公开相册失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取相册失败: {str(e)}")

@app.get("/api/spot/albums/user/{user_id}")
async def get_user_albums_from_db(user_id: str):
    """从Supabase数据库获取用户相册"""
    try:
        albums = await spot_api_service.get_user_albums(user_id)
        return {
            "success": True,
            "data": albums,
            "count": len(albums),
            "message": f"用户有 {len(albums)} 个相册"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户相册失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户相册失败: {str(e)}")

@app.get("/api/spot/statistics")
async def get_spot_statistics():
    """从Supabase数据库获取统计信息"""
    try:
        stats = await spot_api_service.get_statistics()
        return {
            "success": True,
            "data": stats,
            "message": "统计信息获取成功"
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

# 修改现有的explore-real端点以使用新的数据库API
@app.post("/api/explore-supabase", response_model=ExploreResponse)
async def explore_direction_supabase(request: ExploreRequest):
    """使用Supabase数据库探索指定方向的地点"""
    import time
    start_time = time.time()
    
    try:
        # 验证输入参数
        if not (-90 <= request.latitude <= 90):
            raise HTTPException(status_code=400, detail="纬度必须在-90到90之间")
        if not (-180 <= request.longitude <= 180):
            raise HTTPException(status_code=400, detail="经度必须在-180到180之间")
        if not (0 <= request.heading < 360):
            raise HTTPException(status_code=400, detail="方向必须在0到360度之间")
        if request.segment_distance <= 0:
            raise HTTPException(status_code=400, detail="分段距离必须大于0")
        
        # 计算目标距离点的坐标
        target_distance = request.segment_distance
        target_point = geod.Direct(
            request.latitude, 
            request.longitude, 
            request.heading, 
            target_distance * 1000  # 转换为米
        )
        
        target_lat = target_point['lat2']
        target_lon = target_point['lon2']
        
        # 使用新的Supabase API获取附近景点
        attractions_data = await spot_api_service.get_nearby_attractions(
            target_lat, target_lon, radius_km=50
        )
        
        # 转换为PlaceInfo对象
        places = []
        for attraction in attractions_data:
            place_info = PlaceInfo(
                name=attraction['name'],
                latitude=attraction['latitude'],
                longitude=attraction['longitude'],
                distance=attraction.get('distance', target_distance),
                description=attraction.get('description', ''),
                image=attraction.get('image'),
                video=attraction.get('video'),
                country=attraction.get('country'),
                city=attraction.get('city'),
                opening_hours=attraction.get('opening_hours'),
                ticket_price=attraction.get('ticket_price'),
                booking_method=attraction.get('booking_method'),
                category=attraction.get('category')
            )
            places.append(place_info)
        
        calculation_time = time.time() - start_time
        
        logger.info(f"使用Supabase数据库找到 {len(places)} 个景点，耗时 {calculation_time:.2f}秒")
        
        return ExploreResponse(
            places=places,
            total_distance=target_distance,
            calculation_time=calculation_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Supabase数据探索错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Supabase数据获取错误: {str(e)}")

# ================== CAMEL多智能体相册生成端点 ==================

class OneClickAlbumRequest(BaseModel):
    user_prompt: str
    user_id: Optional[str] = None
    language: Optional[str] = "zh-CN"

class OneClickAlbumResponse(BaseModel):
    success: bool
    message: str
    album: Optional[Dict] = None
    user_id: Optional[str] = None
    error: Optional[str] = None

@app.post("/api/generate-album", response_model=OneClickAlbumResponse)
async def generate_album_from_prompt(request: OneClickAlbumRequest):
    """
    一句话生成旅游导航图相册
    
    使用CAMEL多智能体系统和向量数据库实现智能旅游规划
    """
    try:
        logger.info(f"收到一句话生成相册请求: {request.user_prompt}")
        
        # 获取多智能体编排器
        orchestrator = get_album_orchestrator()
        
        # 生成相册
        result = await orchestrator.generate_album_from_prompt(
            user_prompt=request.user_prompt,
            user_id=request.user_id
        )
        
        if result.get('success'):
            return OneClickAlbumResponse(
                success=True,
                message=f"成功生成旅游相册：{result['album'].get('title', '未命名相册')}",
                album=result['album'],
                user_id=result.get('user_id')
            )
        else:
            return OneClickAlbumResponse(
                success=False,
                message="相册生成失败",
                error=result.get('error', '未知错误')
            )
            
    except Exception as e:
        logger.error(f"一句话生成相册失败: {e}")
        import traceback
        traceback.print_exc()
        
        return OneClickAlbumResponse(
            success=False,
            message="系统错误",
            error=f"相册生成失败: {str(e)}"
        )

@app.get("/api/quick-recommendations")
async def get_quick_recommendations(
    latitude: float,
    longitude: float,
    interests: str = "",
    limit: int = 5
):
    """
    快速景点推荐
    
    基于位置和兴趣快速推荐景点，不需要完整的相册生成流程
    """
    try:
        logger.info(f"快速推荐请求: 位置=({latitude}, {longitude}), 兴趣={interests}")
        
        # 解析兴趣列表
        interests_list = [interest.strip() for interest in interests.split(',') if interest.strip()]
        
        # 获取多智能体编排器
        orchestrator = get_album_orchestrator()
        
        # 生成快速推荐
        result = await orchestrator.generate_quick_recommendations(
            location=(latitude, longitude),
            interests=interests_list,
            limit=limit
        )
        
        return {
            "success": result.get('success', False),
            "data": result.get('recommendations', []),
            "message": f"找到 {len(result.get('recommendations', []))} 个推荐景点"
        }
        
    except Exception as e:
        logger.error(f"快速推荐失败: {e}")
        return {
            "success": False,
            "error": f"推荐生成失败: {str(e)}"
        }

@app.get("/api/camel-health")
async def camel_health_check():
    """CAMEL多智能体系统健康检查"""
    try:
        orchestrator = get_album_orchestrator()
        health_status = await orchestrator.health_check()
        
        return {
            "success": True,
            "data": health_status
        }
        
    except Exception as e:
        logger.error(f"CAMEL健康检查失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "overall": "error",
                "message": "健康检查失败"
            }
        }

@app.post("/api/vector-search")
async def vector_similarity_search(
    query: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: float = 50,
    limit: int = 10,
    threshold: float = 0.7
):
    """
    向量相似度搜索景点
    
    使用语义搜索找到与查询最相关的景点
    """
    try:
        logger.info(f"向量搜索请求: {query}")
        
        # 获取向量数据库
        vector_db = get_vector_database()
        
        # 执行搜索
        if latitude is not None and longitude is not None:
            results = await vector_db.search_attractions_by_semantic(
                query=query,
                location=(latitude, longitude),
                radius_km=radius_km,
                limit=limit
            )
        else:
            results = await vector_db.similarity_search(
                query=query,
                limit=limit,
                threshold=threshold
            )
        
        return {
            "success": True,
            "data": results,
            "count": len(results),
            "message": f"找到 {len(results)} 个相关景点"
        }
        
    except Exception as e:
        logger.error(f"向量搜索失败: {e}")
        return {
            "success": False,
            "error": f"搜索失败: {str(e)}"
        }

@app.post("/api/batch-process-vectors")
async def batch_process_attraction_vectors(batch_size: int = 10):
    """
    批量处理景点向量
    
    为数据库中的景点生成向量索引（管理员功能）
    """
    try:
        logger.info(f"开始批量处理景点向量，批次大小: {batch_size}")
        
        # 获取向量数据库
        vector_db = get_vector_database()
        
        # 初始化向量表
        await vector_db.initialize_vector_tables()
        
        # 批量处理
        await vector_db.batch_process_attractions(batch_size=batch_size)
        
        return {
            "success": True,
            "message": "批量向量处理完成"
        }
        
    except Exception as e:
        logger.error(f"批量处理向量失败: {e}")
        return {
            "success": False,
            "error": f"批量处理失败: {str(e)}"
        }

# ================== 相册管理端点 ==================

class SaveAlbumRequest(BaseModel):
    album_data: Dict
    user_id: str
    access_level: str = "public"

@app.post("/api/save-album")
async def save_generated_album(request: SaveAlbumRequest):
    """保存生成的相册到数据库"""
    try:
        album_data = request.album_data
        
        # 保存到Supabase
        saved_album = await spot_api_service.create_album(
            creator_id=request.user_id,
            title=album_data.get('title', '未命名相册'),
            description=album_data.get('description', ''),
            access_level=request.access_level
        )
        
        return {
            "success": True,
            "data": saved_album,
            "message": "相册保存成功"
        }
        
    except Exception as e:
        logger.error(f"保存相册失败: {e}")
        return {
            "success": False,
            "error": f"保存失败: {str(e)}"
        }

@app.get("/api/my-albums/{user_id}")
async def get_user_generated_albums(user_id: str):
    """获取用户生成的相册列表"""
    try:
        albums = await spot_api_service.get_user_albums(user_id)
        
        return {
            "success": True,
            "data": albums,
            "count": len(albums),
            "message": f"找到 {len(albums)} 个相册"
        }
        
    except Exception as e:
        logger.error(f"获取用户相册失败: {e}")
        return {
            "success": False,
            "error": f"获取相册失败: {str(e)}"
        }

# 包含认证路由
app.include_router(auth_router, prefix="/api/auth", tags=["用户认证"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)