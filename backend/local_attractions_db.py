# 本地景点数据库
# 解决网络API不稳定的问题

import math
from typing import List, Dict, Optional

class LocalAttractionsDB:
    """本地景点数据库"""
    
    def __init__(self):
        self.attractions = [
            # 北京昌平区景点
            {
                "name": "明十三陵",
                "latitude": 40.2917,
                "longitude": 116.2333,
                "category": "文化古迹",
                "description": "明朝十三位皇帝的陵墓群，是中国明清皇家陵寝的杰出代表。",
                "opening_hours": "08:00-17:30",
                "ticket_price": "成人票：45元",
                "booking_method": "现场购票或官方网站预约",
                "image": "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=400",
                "country": "中国",
                "city": "北京市昌平区"
            },
            {
                "name": "长陵",
                "latitude": 40.2958,
                "longitude": 116.2275,
                "category": "文化古迹", 
                "description": "明成祖朱棣的陵墓，是十三陵中规模最大、营建最早的一座。",
                "opening_hours": "08:00-17:30",
                "ticket_price": "成人票：45元",
                "booking_method": "现场购票或官方网站预约",
                "image": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400",
                "country": "中国",
                "city": "北京市昌平区"
            },
            {
                "name": "定陵",
                "latitude": 40.2889,
                "longitude": 116.2306,
                "category": "文化古迹",
                "description": "明神宗朱翊钧的陵墓，是十三陵中唯一被发掘的陵墓。",
                "opening_hours": "08:00-17:30", 
                "ticket_price": "成人票：60元",
                "booking_method": "现场购票或官方网站预约",
                "image": "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=400",
                "country": "中国",
                "city": "北京市昌平区"
            },
            {
                "name": "居庸关长城",
                "latitude": 40.2722,
                "longitude": 116.0833,
                "category": "文化古迹",
                "description": "万里长城的重要关隘，有\"天下第一雄关\"之称。",
                "opening_hours": "07:30-17:30",
                "ticket_price": "成人票：40元",
                "booking_method": "现场购票或官方网站预约",
                "image": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=400",
                "country": "中国", 
                "city": "北京市昌平区"
            },
            {
                "name": "银山塔林",
                "latitude": 40.2944,
                "longitude": 116.1667,
                "category": "文化古迹",
                "description": "辽、金、元、明、清五个朝代的古塔群，是北京地区现存古塔最多的地方。",
                "opening_hours": "08:00-17:00",
                "ticket_price": "成人票：25元",
                "booking_method": "现场购票",
                "image": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400",
                "country": "中国",
                "city": "北京市昌平区"
            },
            {
                "name": "蟒山国家森林公园",
                "latitude": 40.3167,
                "longitude": 116.1833,
                "category": "自然景观",
                "description": "北京面积最大的国家森林公园，有\"北京的绿肺\"之称。",
                "opening_hours": "07:00-18:00",
                "ticket_price": "成人票：20元",
                "booking_method": "现场购票",
                "image": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
                "country": "中国",
                "city": "北京市昌平区"
            },
            {
                "name": "小汤山温泉",
                "latitude": 40.1833,
                "longitude": 116.4167,
                "category": "休闲娱乐",
                "description": "著名的温泉度假区，有600多年的开发利用历史。",
                "opening_hours": "09:00-22:00",
                "ticket_price": "成人票：168元",
                "booking_method": "现场购票或在线预订",
                "image": "https://images.unsplash.com/photo-1571902943202-507ec2618e8f?w=400",
                "country": "中国",
                "city": "北京市昌平区"
            },
            
            # 北京其他区域景点
            {
                "name": "故宫博物院",
                "latitude": 39.9163,
                "longitude": 116.3972,
                "category": "文化古迹",
                "description": "中国明清两代的皇家宫殿，世界文化遗产。",
                "opening_hours": "08:30-17:00",
                "ticket_price": "成人票：60元",
                "booking_method": "官方网站实名预约",
                "image": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=400",
                "country": "中国",
                "city": "北京市东城区"
            },
            {
                "name": "天坛公园",
                "latitude": 39.8822,
                "longitude": 116.4066,
                "category": "文化古迹",
                "description": "明清两朝皇帝祭天的场所，世界文化遗产。",
                "opening_hours": "06:00-21:00",
                "ticket_price": "成人票：15元",
                "booking_method": "现场购票或官方网站预约",
                "image": "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=400",
                "country": "中国",
                "city": "北京市东城区"
            },
            {
                "name": "颐和园",
                "latitude": 39.9999,
                "longitude": 116.2750,
                "category": "文化古迹",
                "description": "中国现存规模最大、保存最完整的皇家园林。",
                "opening_hours": "06:30-18:00",
                "ticket_price": "成人票：30元",
                "booking_method": "现场购票或官方网站预约", 
                "image": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400",
                "country": "中国",
                "city": "北京市海淀区"
            }
        ]
    
    def find_nearby_attractions(self, lat: float, lon: float, radius_km: float = 50) -> List[Dict]:
        """查找附近的景点"""
        nearby = []
        
        for attraction in self.attractions:
            distance = self.calculate_distance(
                lat, lon, 
                attraction['latitude'], attraction['longitude']
            )
            
            if distance <= radius_km * 1000:  # 转换为米
                attraction_copy = attraction.copy()
                attraction_copy['distance_to_point'] = distance / 1000  # 转换为公里
                nearby.append(attraction_copy)
        
        # 按距离排序
        nearby.sort(key=lambda x: x['distance_to_point'])
        return nearby
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点间距离（米）"""
        R = 6371000  # 地球半径（米）
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def get_attraction_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取景点"""
        for attraction in self.attractions:
            if name in attraction['name'] or attraction['name'] in name:
                return attraction
        return None
    
    def get_attractions_by_category(self, category: str) -> List[Dict]:
        """根据类别获取景点"""
        return [attr for attr in self.attractions if attr['category'] == category]

# 全局实例
local_attractions_db = LocalAttractionsDB()
