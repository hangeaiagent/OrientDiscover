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
from dotenv import load_dotenv
from real_data_service import real_data_service
from local_attractions_db import local_attractions_db
from gemini_service import gemini_service
from fastapi import File, UploadFile, Form
from fastapi.responses import FileResponse
import tempfile
import shutil

# 加载环境变量
load_dotenv()

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

# 全局变量
geod = Geodesic.WGS84
places_data = {}

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
                distance=place_data['distance_to_point'],
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
        # 导入必要的库
        import googlemaps
        import requests
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # 首先尝试高德地图API
        amap_key = os.getenv("AMAP_API_KEY")
        if amap_key:
            try:
                url = "https://restapi.amap.com/v3/geocode/geo"
                params = {
                    'key': amap_key,
                    'address': request.query,
                    'output': 'json'
                }
                
                response = requests.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
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
                        
                        return GeocodeResponse(
                            success=True,
                            data=result,
                            message=f"高德地图找到位置: {result['formatted_address']}"
                        )
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
        
        # 本地备用数据
        fallback_locations = {
            "北京": {"lat": 39.9042, "lng": 116.4074, "address": "北京市"},
            "上海": {"lat": 31.2304, "lng": 121.4737, "address": "上海市"},
            "广州": {"lat": 23.1291, "lng": 113.2644, "address": "广州市"},
            "深圳": {"lat": 22.5431, "lng": 114.0579, "address": "深圳市"},
            "天安门": {"lat": 39.9042, "lng": 116.4074, "address": "北京市东城区天安门"},
            "故宫": {"lat": 39.9163, "lng": 116.3972, "address": "北京市东城区故宫"},
        }
        
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
                return GeocodeResponse(
                    success=True,
                    data=result,
                    message=f"使用本地数据找到位置: {info['address']}"
                )
        
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

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "方向探索派对API",
        "version": "1.0.0"
    }

@app.post("/api/generate-attraction-photo")
async def generate_attraction_photo(
    user_photo: UploadFile = File(...),
    attraction_name: str = Form(...),
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
        lat_float = float(latitude) if latitude else None
        lng_float = float(longitude) if longitude else None
        
        # 调用Gemini服务生成合影
        success, message, result = await gemini_service.generate_attraction_photo(
            user_photo=user_photo,
            attraction_name=attraction_name,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)