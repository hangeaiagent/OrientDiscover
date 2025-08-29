from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import math
from geographiclib.geodesic import Geodesic
import json
import os

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
    country: Optional[str] = None
    city: Optional[str] = None

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

def find_nearest_places(points, time_mode):
    """为每个点找到最近的地点"""
    places = []
    available_places = places_data.get(time_mode, places_data["present"])
    
    for point in points:
        if point['distance'] == 0:  # 跳过起始点
            continue
            
        min_distance = float('inf')
        nearest_place = None
        
        for place_data in available_places:
            # 计算到地点的距离
            distance_result = geod.Inverse(
                point['latitude'], point['longitude'],
                place_data['latitude'], place_data['longitude']
            )
            distance_km = distance_result['s12'] / 1000  # 转换为公里
            
            if distance_km < min_distance:
                min_distance = distance_km
                nearest_place = place_data.copy()
                nearest_place['actual_lat'] = point['latitude']
                nearest_place['actual_lon'] = point['longitude']
                nearest_place['distance_to_route'] = distance_km
        
        if nearest_place and min_distance < 1000:  # 只选择1000km内的地点
            place_info = PlaceInfo(
                name=nearest_place['name'],
                latitude=point['latitude'],
                longitude=point['longitude'],
                distance=point['distance'],
                description=nearest_place['description'],
                image=nearest_place.get('image'),
                country=nearest_place.get('country'),
                city=nearest_place.get('city')
            )
            places.append(place_info)
    
    return places

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
        
        # 计算最大距离（地球周长的一半，约20000km）
        max_distance = 20000
        
        # 计算大圆航线上的点
        points = calculate_great_circle_points(
            request.latitude, 
            request.longitude, 
            request.heading, 
            max_distance, 
            request.segment_distance
        )
        
        # 找到最近的地点
        places = find_nearest_places(points, request.time_mode)
        
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

@app.get("/api/places/{time_mode}")
async def get_places(time_mode: str):
    """获取指定时间模式的所有地点"""
    if time_mode not in places_data:
        raise HTTPException(status_code=404, detail="时间模式不存在")
    
    return {"places": places_data[time_mode]}

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "方向探索派对API",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)