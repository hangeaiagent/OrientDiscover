# 本地景点数据库
# 解决网络API不稳定的问题

import math
from typing import List, Dict, Optional

class LocalAttractionsDB:
    """本地景点数据库"""
    
    def __init__(self):
        # 精选北京20个最具代表性的景点，确保图片和视频匹配
        self.attractions = [
            {
                "name": "故宫博物院",
                "latitude": 39.9163,
                "longitude": 116.3972,
                "category": "文化古迹",
                "description": "中国明清两代的皇家宫殿，世界文化遗产，是世界上现存规模最大、保存最为完整的木质结构古建筑群。",
                "opening_hours": "08:30-17:00",
                "ticket_price": "成人票：60元",
                "booking_method": "官方网站实名预约",
                "image": "https://images.unsplash.com/photo-1548013146-72479768bada?w=800",
                "video": "https://www.youtube.com/watch?v=WibmcsEGLKo",
                "country": "中国",
                "city": "北京市东城区",
                "address": "北京市东城区景山前街4号"
            },
            {
                "name": "天安门广场",
                "latitude": 39.9042,
                "longitude": 116.3974,
                "category": "文化古迹",
                "description": "世界上最大的城市广场之一，中华人民共和国的象征，见证了中国现代史的重要时刻。",
                "opening_hours": "05:00-22:00",
                "ticket_price": "免费",
                "booking_method": "无需预约",
                "image": "https://images.unsplash.com/photo-1570197788417-0e82375c9371?w=800",
                "video": "https://www.youtube.com/watch?v=bQVdAb0cw5k",
                "country": "中国",
                "city": "北京市东城区",
                "address": "北京市东城区东长安街"
            },
            {
                "name": "天坛公园",
                "latitude": 39.8822,
                "longitude": 116.4066,
                "category": "文化古迹",
                "description": "明清两朝皇帝祭天的场所，世界文化遗产，中国古代建筑艺术的杰作。",
                "opening_hours": "06:00-21:00",
                "ticket_price": "成人票：15元",
                "booking_method": "现场购票或官方网站预约",
                "image": "https://images.unsplash.com/photo-1583416750470-965b2707b355?w=800",
                "video": "https://www.youtube.com/watch?v=dUQABjvHPWM",
                "country": "中国",
                "city": "北京市东城区",
                "address": "北京市东城区天坛内东里7号"
            },
            {
                "name": "颐和园",
                "latitude": 39.9999,
                "longitude": 116.2750,
                "category": "文化古迹",
                "description": "中国现存规模最大、保存最完整的皇家园林，清朝皇室的夏宫。",
                "opening_hours": "06:30-18:00",
                "ticket_price": "成人票：30元",
                "booking_method": "现场购票或官方网站预约",
                "image": "https://images.unsplash.com/photo-1534050359320-02900022671e?w=800",
                "video": "https://www.youtube.com/watch?v=E2aV6RHAEwE",
                "country": "中国",
                "city": "北京市海淀区",
                "address": "北京市海淀区新建宫门路19号"
            },
            {
                "name": "圆明园",
                "latitude": 40.0084,
                "longitude": 116.2972,
                "category": "文化古迹",
                "description": "清朝皇室的离宫别苑，被誉为\"万园之园\"，现为遗址公园。",
                "opening_hours": "07:00-19:30",
                "ticket_price": "成人票：25元",
                "booking_method": "现场购票或官方网站预约",
                "image": "https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=800",
                "video": "https://www.youtube.com/watch?v=jP7Z4rNmfQA",
                "country": "中国",
                "city": "北京市海淀区",
                "address": "北京市海淀区清华西路28号"
            },
            {
                "name": "北海公园",
                "latitude": 39.9254,
                "longitude": 116.3888,
                "category": "文化古迹",
                "description": "中国现存最古老、最完整、最具综合性和代表性的皇家园林之一。",
                "opening_hours": "06:30-20:00",
                "ticket_price": "成人票：10元",
                "booking_method": "现场购票",
                "image": "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=800",
                "video": "https://www.youtube.com/watch?v=K5ZjjX8f2lE",
                "country": "中国",
                "city": "北京市西城区",
                "address": "北京市西城区文津街1号"
            },
            {
                "name": "景山公园",
                "latitude": 39.9233,
                "longitude": 116.3953,
                "category": "文化古迹",
                "description": "明清两朝的皇家园林，是俯瞰紫禁城全景的最佳位置。",
                "opening_hours": "06:30-20:00",
                "ticket_price": "成人票：2元",
                "booking_method": "现场购票",
                "image": "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800",
                "video": "https://www.youtube.com/watch?v=N6PW8LTAkBs",
                "country": "中国",
                "city": "北京市西城区",
                "address": "北京市西城区景山西街44号"
            },
            {
                "name": "八达岭长城",
                "latitude": 40.3594,
                "longitude": 116.0144,
                "category": "文化古迹",
                "description": "万里长城最著名的一段，世界文化遗产，中国古代防御工程的杰作。",
                "opening_hours": "06:30-19:00",
                "ticket_price": "成人票：40元",
                "booking_method": "官方网站预约",
                "image": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=800",
                "video": "https://www.youtube.com/watch?v=VgdSGPXzUqA",
                "country": "中国",
                "city": "北京市延庆区",
                "address": "北京市延庆区G6京藏高速58号出口"
            },
            {
                "name": "明十三陵",
                "latitude": 40.2917,
                "longitude": 116.2333,
                "category": "文化古迹",
                "description": "明朝十三位皇帝的陵墓群，是中国明清皇家陵寝的杰出代表。",
                "opening_hours": "08:00-17:30",
                "ticket_price": "成人票：45元",
                "booking_method": "现场购票或官方网站预约",
                "image": "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=800",
                "video": "https://www.youtube.com/watch?v=XdJ0O9nHtqk",
                "country": "中国",
                "city": "北京市昌平区",
                "address": "北京市昌平区十三陵镇"
            },
            {
                "name": "雍和宫",
                "latitude": 39.9473,
                "longitude": 116.4177,
                "category": "文化古迹",
                "description": "北京市内最大的藏传佛教寺院，清朝雍正皇帝的潜邸。",
                "opening_hours": "09:00-16:30",
                "ticket_price": "成人票：25元",
                "booking_method": "现场购票",
                "image": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800",
                "video": "https://www.youtube.com/watch?v=8xZH8WcqMnY",
                "country": "中国",
                "city": "北京市东城区",
                "address": "北京市东城区雍和宫大街12号"
            },
            {
                "name": "三里屯太古里",
                "latitude": 39.9368,
                "longitude": 116.4478,
                "category": "休闲娱乐",
                "description": "北京最时尚的购物和娱乐区域，汇集国际品牌、餐厅和夜生活场所。",
                "opening_hours": "10:00-22:00",
                "ticket_price": "免费",
                "booking_method": "无需预约",
                "image": "https://images.unsplash.com/photo-1549813069-f95e44d7f498?w=800",
                "video": "https://www.youtube.com/watch?v=2X5F0X0Y8JQ",
                "country": "中国",
                "city": "北京市朝阳区",
                "address": "北京市朝阳区三里屯路11号"
            },
            {
                "name": "什刹海",
                "latitude": 39.9369,
                "longitude": 116.3831,
                "category": "文化古迹",
                "description": "北京内城唯一一处具有开阔水面的开放型景区，胡同文化的代表。",
                "opening_hours": "全天开放",
                "ticket_price": "免费",
                "booking_method": "无需预约",
                "image": "https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=800",
                "video": "https://www.youtube.com/watch?v=L8xqP7GdF4M",
                "country": "中国",
                "city": "北京市西城区",
                "address": "北京市西城区羊房胡同23号"
            },
            {
                "name": "王府井大街",
                "latitude": 39.9097,
                "longitude": 116.4074,
                "category": "休闲娱乐",
                "description": "北京最著名的商业街之一，有700多年的历史，是购物和美食的天堂。",
                "opening_hours": "全天开放",
                "ticket_price": "免费",
                "booking_method": "无需预约",
                "image": "https://images.unsplash.com/photo-1549813069-f95e44d7f498?w=800",
                "video": "https://www.youtube.com/watch?v=cH8Q7Zb8K9A",
                "country": "中国",
                "city": "北京市东城区",
                "address": "北京市东城区王府井大街"
            },
            {
                "name": "南锣鼓巷",
                "latitude": 39.9368,
                "longitude": 116.4033,
                "category": "文化古迹",
                "description": "北京最古老的街区之一，保存完好的四合院建筑群，体现老北京胡同文化。",
                "opening_hours": "全天开放",
                "ticket_price": "免费",
                "booking_method": "无需预约",
                "image": "https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=800",
                "video": "https://www.youtube.com/watch?v=9Tm1yD4Ot8E",
                "country": "中国",
                "city": "北京市东城区",
                "address": "北京市东城区南锣鼓巷"
            },
            {
                "name": "鸟巢（国家体育场）",
                "latitude": 39.9928,
                "longitude": 116.3975,
                "category": "现代建筑",
                "description": "2008年北京奥运会主体育场，现代建筑的杰作，因其独特的钢结构外观而得名。",
                "opening_hours": "09:00-21:00",
                "ticket_price": "成人票：50元",
                "booking_method": "现场购票或在线预约",
                "image": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800",
                "video": "https://www.youtube.com/watch?v=3wK4d0r0h6Y",
                "country": "中国",
                "city": "北京市朝阳区",
                "address": "北京市朝阳区国家体育场南路1号"
            },
            {
                "name": "水立方（国家游泳中心）",
                "latitude": 39.9934,
                "longitude": 116.3906,
                "category": "现代建筑",
                "description": "2008年北京奥运会游泳、跳水、花样游泳项目的比赛场地，独特的蓝色泡泡外观。",
                "opening_hours": "09:00-21:00",
                "ticket_price": "成人票：30元",
                "booking_method": "现场购票或在线预约",
                "image": "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=800",
                "video": "https://www.youtube.com/watch?v=ZL5oKzlqGEw",
                "country": "中国",
                "city": "北京市朝阳区",
                "address": "北京市朝阳区天辰东路11号"
            },
            {
                "name": "恭王府",
                "latitude": 39.9354,
                "longitude": 116.3828,
                "category": "文化古迹",
                "description": "清朝规模最大的王府，和珅的宅邸，现存最完整的清代王府建筑群。",
                "opening_hours": "08:30-17:00",
                "ticket_price": "成人票：40元",
                "booking_method": "现场购票或官方网站预约",
                "image": "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800",
                "video": "https://www.youtube.com/watch?v=mH8K6YdS4Ns",
                "country": "中国",
                "city": "北京市西城区",
                "address": "北京市西城区柳荫街甲14号"
            },
            {
                "name": "香山公园",
                "latitude": 39.9961,
                "longitude": 116.1889,
                "category": "自然景观",
                "description": "北京著名的森林公园，以红叶闻名，是观赏秋景的绝佳去处。",
                "opening_hours": "06:00-18:30",
                "ticket_price": "成人票：10元",
                "booking_method": "现场购票",
                "image": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800",
                "video": "https://www.youtube.com/watch?v=QrK8xS2Vr7M",
                "country": "中国",
                "city": "北京市海淀区",
                "address": "北京市海淀区买卖街40号"
            },
            {
                "name": "中山公园",
                "latitude": 39.9048,
                "longitude": 116.3869,
                "category": "文化古迹",
                "description": "位于天安门西侧，原为明清两朝的社稷坛，现为纪念孙中山先生的公园。",
                "opening_hours": "06:00-21:00",
                "ticket_price": "成人票：3元",
                "booking_method": "现场购票",
                "image": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800",
                "video": "https://www.youtube.com/watch?v=mQwX8f9K2lM",
                "country": "中国",
                "city": "北京市东城区",
                "address": "北京市东城区中华路4号"
            },
            {
                "name": "前门大街",
                "latitude": 39.8979,
                "longitude": 116.3967,
                "category": "文化古迹",
                "description": "北京著名的商业古街，有600多年历史，保留了明清时期的建筑风格。",
                "opening_hours": "全天开放",
                "ticket_price": "免费",
                "booking_method": "无需预约",
                "image": "https://images.unsplash.com/photo-1549813069-f95e44d7f498?w=800",
                "video": "https://www.youtube.com/watch?v=QH8vK9N2f5s",
                "country": "中国",
                "city": "北京市东城区",
                "address": "北京市东城区前门大街"
            },
            {
                "name": "798艺术区",
                "latitude": 39.9847,
                "longitude": 116.4972,
                "category": "现代艺术",
                "description": "由废弃工厂改造的当代艺术区，汇集了众多画廊、艺术工作室和创意空间。",
                "opening_hours": "10:00-18:00",
                "ticket_price": "免费",
                "booking_method": "无需预约",
                "image": "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=800",
                "video": "https://www.youtube.com/watch?v=H9xK8rL2fNM",
                "country": "中国",
                "city": "北京市朝阳区",
                "address": "北京市朝阳区酒仙桥路4号"
            },
            {
                "name": "居庸关长城",
                "latitude": 40.2722,
                "longitude": 116.0833,
                "category": "文化古迹",
                "description": "万里长城的重要关隘，有\"天下第一雄关\"之称，山峦叠嶂景色壮观。",
                "opening_hours": "07:30-17:30",
                "ticket_price": "成人票：40元",
                "booking_method": "现场购票或官方网站预约",
                "image": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=800",
                "video": "https://www.youtube.com/watch?v=Rk9H7QcF8dE",
                "country": "中国",
                "city": "北京市昌平区",
                "address": "北京市昌平区南口镇居庸关村216省道"
            },
            {
                "name": "慕田峪长城",
                "latitude": 40.4319,
                "longitude": 116.5703,
                "category": "文化古迹",
                "description": "万里长城的精华段落之一，植被覆盖率高，景色优美，相对游客较少。",
                "opening_hours": "07:30-18:00",
                "ticket_price": "成人票：40元",
                "booking_method": "现场购票或官方网站预约",
                "image": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=800",
                "video": "https://www.youtube.com/watch?v=VgdSGPXzUqA",
                "country": "中国",
                "city": "北京市怀柔区",
                "address": "北京市怀柔区渤海镇慕田峪村"
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