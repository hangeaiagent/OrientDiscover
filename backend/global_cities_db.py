# 全球城市景点数据库
# 包含全球知名旅游城市和中国知名旅游城市的完整景点信息

import math
import random
from typing import List, Dict, Optional

class GlobalCitiesDB:
    """全球城市景点数据库"""
    
    def __init__(self):
        # 全球知名旅游城市景点数据
        self.global_cities = {
            # 法国巴黎
            "paris": {
                "name": "巴黎",
                "country": "法国",
                "coordinates": [48.8566, 2.3522],
                "attractions": [
                    {
                        "name": "埃菲尔铁塔",
                        "latitude": 48.8584,
                        "longitude": 2.2945,
                        "category": "地标建筑",
                        "description": "巴黎的象征，世界著名的铁塔建筑，高324米，是法国最受欢迎的付费参观建筑物。",
                        "opening_hours": "09:30-23:45",
                        "ticket_price": "成人票：29.4欧元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1511739001486-6bfe10ce785f?w=800",
                        "video": "https://www.youtube.com/watch?v=F7nCDrf90V8",
                        "country": "法国",
                        "city": "巴黎",
                        "address": "Champ de Mars, 5 Avenue Anatole France, 75007 Paris"
                    },
                    {
                        "name": "卢浮宫",
                        "latitude": 48.8606,
                        "longitude": 2.3376,
                        "category": "博物馆",
                        "description": "世界最大的艺术博物馆，收藏着《蒙娜丽莎》等无价艺术珍品。",
                        "opening_hours": "09:00-18:00",
                        "ticket_price": "成人票：17欧元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1566139884009-d8ff2b2be36e?w=800",
                        "video": "https://www.youtube.com/watch?v=Jo_-KUBhXds",
                        "country": "法国",
                        "city": "巴黎",
                        "address": "Rue de Rivoli, 75001 Paris"
                    },
                    {
                        "name": "凯旋门",
                        "latitude": 48.8738,
                        "longitude": 2.2950,
                        "category": "历史建筑",
                        "description": "为纪念拿破仑胜利而建的凯旋门，香榭丽舍大街的起点。",
                        "opening_hours": "10:00-23:00",
                        "ticket_price": "成人票：13欧元",
                        "booking_method": "现场购票或网上预约",
                        "image": "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?w=800",
                        "video": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                        "country": "法国",
                        "city": "巴黎",
                        "address": "Place Charles de Gaulle, 75008 Paris"
                    },
                    {
                        "name": "香榭丽舍大街",
                        "latitude": 48.8698,
                        "longitude": 2.3075,
                        "category": "购物街区",
                        "description": "世界上最美丽的大街之一，连接协和广场和凯旋门。",
                        "opening_hours": "全天开放",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1502602898536-47ad22581b52?w=800",
                        "video": "https://www.youtube.com/watch?v=AjPau5QYtYs",
                        "country": "法国",
                        "city": "巴黎",
                        "address": "Avenue des Champs-Élysées, 75008 Paris"
                    },
                    {
                        "name": "巴黎圣母院",
                        "latitude": 48.8530,
                        "longitude": 2.3499,
                        "category": "宗教建筑",
                        "description": "哥特式建筑的杰作，雨果小说《巴黎圣母院》的背景地。",
                        "opening_hours": "08:00-18:45",
                        "ticket_price": "免费参观",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1549144511-f099e773c147?w=800",
                        "video": "https://www.youtube.com/watch?v=cHcunREYzNY",
                        "country": "法国",
                        "city": "巴黎",
                        "address": "6 Parvis Notre-Dame - Pl. Jean-Paul II, 75004 Paris"
                    },
                    {
                        "name": "蒙马特高地",
                        "latitude": 48.8867,
                        "longitude": 2.3431,
                        "category": "文化区域",
                        "description": "巴黎的艺术中心，以圣心大教堂和艺术家聚集地闻名。",
                        "opening_hours": "全天开放",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?w=800",
                        "video": "https://www.youtube.com/watch?v=X4tLbzm3oAM",
                        "country": "法国",
                        "city": "巴黎",
                        "address": "Montmartre, 75018 Paris"
                    }
                ]
            },
            
            # 英国伦敦
            "london": {
                "name": "伦敦",
                "country": "英国",
                "coordinates": [51.5074, -0.1278],
                "attractions": [
                    {
                        "name": "大本钟",
                        "latitude": 51.4994,
                        "longitude": -0.1245,
                        "category": "历史建筑",
                        "description": "伦敦的象征，威斯敏斯特宫的钟楼，英国议会大厦的一部分。",
                        "opening_hours": "外观全天可观赏",
                        "ticket_price": "外观免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800",
                        "video": "https://www.youtube.com/watch?v=LtmS2ePSSdU",
                        "country": "英国",
                        "city": "伦敦",
                        "address": "Westminster, London SW1A 0AA"
                    },
                    {
                        "name": "伦敦眼",
                        "latitude": 51.5033,
                        "longitude": -0.1195,
                        "category": "观景设施",
                        "description": "世界最大的摩天轮之一，可俯瞰伦敦全景。",
                        "opening_hours": "11:00-18:00",
                        "ticket_price": "成人票：27英镑",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1520986606214-8b456906c813?w=800",
                        "video": "https://www.youtube.com/watch?v=QdK8U-VIH_o",
                        "country": "英国",
                        "city": "伦敦",
                        "address": "Riverside Building, County Hall, London SE1 7PB"
                    },
                    {
                        "name": "白金汉宫",
                        "latitude": 51.5014,
                        "longitude": -0.1419,
                        "category": "皇室建筑",
                        "description": "英国君主在伦敦的主要寝宫及办公处，著名的换岗仪式举办地。",
                        "opening_hours": "夏季开放参观",
                        "ticket_price": "成人票：30英镑",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1529655683826-3c8ca0b58b22?w=800",
                        "video": "https://www.youtube.com/watch?v=1AS-dCdYZbo",
                        "country": "英国",
                        "city": "伦敦",
                        "address": "London SW1A 1AA"
                    },
                    {
                        "name": "大英博物馆",
                        "latitude": 51.5194,
                        "longitude": -0.1270,
                        "category": "博物馆",
                        "description": "世界上历史最悠久、规模最宏伟的综合性博物馆之一。",
                        "opening_hours": "10:00-17:30",
                        "ticket_price": "免费",
                        "booking_method": "建议网上预约时间段",
                        "image": "https://images.unsplash.com/photo-1555993539-1732b0258235?w=800",
                        "video": "https://www.youtube.com/watch?v=2pYeqfBOhm8",
                        "country": "英国",
                        "city": "伦敦",
                        "address": "Great Russell St, Bloomsbury, London WC1B 3DG"
                    },
                    {
                        "name": "塔桥",
                        "latitude": 51.5055,
                        "longitude": -0.0754,
                        "category": "历史建筑",
                        "description": "伦敦泰晤士河上的一座开启桥，伦敦的象征之一。",
                        "opening_hours": "09:30-18:00",
                        "ticket_price": "成人票：11.4英镑",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800",
                        "video": "https://www.youtube.com/watch?v=hFZFjoX2cGg",
                        "country": "英国",
                        "city": "伦敦",
                        "address": "Tower Bridge Rd, London SE1 2UP"
                    },
                    {
                        "name": "西敏寺",
                        "latitude": 51.4993,
                        "longitude": -0.1273,
                        "category": "宗教建筑",
                        "description": "英国君主加冕和王室成员举行婚礼的地方，哥特式建筑杰作。",
                        "opening_hours": "09:30-15:30",
                        "ticket_price": "成人票：25英镑",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800",
                        "video": "https://www.youtube.com/watch?v=3ad_VpYhE9w",
                        "country": "英国",
                        "city": "伦敦",
                        "address": "20 Deans Yd, Westminster, London SW1P 3PA"
                    }
                ]
            },
            
            # 意大利罗马
            "rome": {
                "name": "罗马",
                "country": "意大利",
                "coordinates": [41.9028, 12.4964],
                "attractions": [
                    {
                        "name": "斗兽场",
                        "latitude": 41.8902,
                        "longitude": 12.4922,
                        "category": "历史建筑",
                        "description": "古罗马时期最大的圆形角斗场，世界新七大奇迹之一。",
                        "opening_hours": "08:30-19:15",
                        "ticket_price": "成人票：16欧元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800",
                        "video": "https://www.youtube.com/watch?v=Qhdb4fGJQkw",
                        "country": "意大利",
                        "city": "罗马",
                        "address": "Piazza del Colosseo, 1, 00184 Roma RM"
                    },
                    {
                        "name": "万神殿",
                        "latitude": 41.8986,
                        "longitude": 12.4769,
                        "category": "历史建筑",
                        "description": "古罗马时期的建筑杰作，现为天主教堂，拥有世界最大的无钢筋混凝土穹顶。",
                        "opening_hours": "09:00-19:15",
                        "ticket_price": "成人票：5欧元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?w=800",
                        "video": "https://www.youtube.com/watch?v=Qhdb4fGJQkw",
                        "country": "意大利",
                        "city": "罗马",
                        "address": "Piazza della Rotonda, 00186 Roma RM"
                    },
                    {
                        "name": "罗马广场",
                        "latitude": 41.8925,
                        "longitude": 12.4853,
                        "category": "历史遗迹",
                        "description": "古罗马帝国的政治、经济和宗教中心，现存大量古建筑遗迹。",
                        "opening_hours": "08:30-19:15",
                        "ticket_price": "成人票：16欧元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1515542622106-78bda8ba0e5b?w=800",
                        "video": "https://www.youtube.com/watch?v=Qhdb4fGJQkw",
                        "country": "意大利",
                        "city": "罗马",
                        "address": "Via della Salara Vecchia, 5/6, 00186 Roma RM"
                    },
                    {
                        "name": "特雷维喷泉",
                        "latitude": 41.9009,
                        "longitude": 12.4833,
                        "category": "地标建筑",
                        "description": "罗马最著名的喷泉，巴洛克风格杰作，许愿投币的传统地。",
                        "opening_hours": "全天开放",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800",
                        "video": "https://www.youtube.com/watch?v=Qhdb4fGJQkw",
                        "country": "意大利",
                        "city": "罗马",
                        "address": "Piazza di Trevi, 00187 Roma RM"
                    },
                    {
                        "name": "西班牙阶梯",
                        "latitude": 41.9057,
                        "longitude": 12.4823,
                        "category": "历史建筑",
                        "description": "连接西班牙广场和天主圣三教堂的巴洛克风格阶梯。",
                        "opening_hours": "全天开放",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1515542622106-78bda8ba0e5b?w=800",
                        "video": "https://www.youtube.com/watch?v=Qhdb4fGJQkw",
                        "country": "意大利",
                        "city": "罗马",
                        "address": "Piazza di Spagna, 00187 Roma RM"
                    }
                ]
            },
            
            # 美国纽约
            "new_york": {
                "name": "纽约",
                "country": "美国",
                "coordinates": [40.7128, -74.0060],
                "attractions": [
                    {
                        "name": "自由女神像",
                        "latitude": 40.6892,
                        "longitude": -74.0445,
                        "category": "地标建筑",
                        "description": "美国的象征，位于自由岛上，法国赠送给美国的友谊礼物。",
                        "opening_hours": "08:30-18:00",
                        "ticket_price": "成人票：23.5美元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1564564321837-a57b7070ac4f?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "美国",
                        "city": "纽约",
                        "address": "Liberty Island, New York, NY 10004"
                    },
                    {
                        "name": "时代广场",
                        "latitude": 40.7580,
                        "longitude": -73.9855,
                        "category": "商业区域",
                        "description": "世界的十字路口，霓虹灯闪烁的商业娱乐中心。",
                        "opening_hours": "全天开放",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "美国",
                        "city": "纽约",
                        "address": "Times Square, New York, NY 10036"
                    },
                    {
                        "name": "中央公园",
                        "latitude": 40.7829,
                        "longitude": -73.9654,
                        "category": "公园",
                        "description": "纽约曼哈顿中心的大型城市公园，都市绿洲。",
                        "opening_hours": "06:00-01:00",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1518391846015-55a9cc003b25?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "美国",
                        "city": "纽约",
                        "address": "New York, NY"
                    },
                    {
                        "name": "帝国大厦",
                        "latitude": 40.7484,
                        "longitude": -73.9857,
                        "category": "观景建筑",
                        "description": "纽约的标志性摩天大楼，Art Deco建筑风格的杰作。",
                        "opening_hours": "10:00-22:00",
                        "ticket_price": "成人票：44美元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1518391846015-55a9cc003b25?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "美国",
                        "city": "纽约",
                        "address": "20 W 34th St, New York, NY 10001"
                    },
                    {
                        "name": "大都会艺术博物馆",
                        "latitude": 40.7794,
                        "longitude": -73.9632,
                        "category": "博物馆",
                        "description": "世界四大博物馆之一，收藏涵盖各个历史时期的艺术品。",
                        "opening_hours": "10:00-17:00",
                        "ticket_price": "成人票：30美元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1564564321837-a57b7070ac4f?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "美国",
                        "city": "纽约",
                        "address": "1000 5th Ave, New York, NY 10028"
                    }
                ]
            },
            
            # 日本东京
            "tokyo": {
                "name": "东京",
                "country": "日本",
                "coordinates": [35.6762, 139.6503],
                "attractions": [
                    {
                        "name": "东京塔",
                        "latitude": 35.6586,
                        "longitude": 139.7454,
                        "category": "观景建筑",
                        "description": "东京的象征性建筑，高333米的红色铁塔，可俯瞰东京全景。",
                        "opening_hours": "09:00-23:00",
                        "ticket_price": "成人票：3000日元",
                        "booking_method": "现场购票或网上预约",
                        "image": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800",
                        "video": "https://www.youtube.com/watch?v=coYw-eVU0Ks",
                        "country": "日本",
                        "city": "东京",
                        "address": "4 Chome-2-8 Shibakoen, Minato City, Tokyo"
                    },
                    {
                        "name": "浅草寺",
                        "latitude": 35.7148,
                        "longitude": 139.7967,
                        "category": "宗教建筑",
                        "description": "东京最古老的寺庙，以雷门和仲见世商店街闻名。",
                        "opening_hours": "06:00-17:00",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1545569341-9eb8b30979d9?w=800",
                        "video": "https://www.youtube.com/watch?v=coYw-eVU0Ks",
                        "country": "日本",
                        "city": "东京",
                        "address": "2 Chome-3-1 Asakusa, Taito City, Tokyo"
                    },
                    {
                        "name": "皇居",
                        "latitude": 35.6852,
                        "longitude": 139.7528,
                        "category": "皇室建筑",
                        "description": "日本天皇的居所，拥有美丽的东御苑。",
                        "opening_hours": "东御苑09:00-17:00",
                        "ticket_price": "东御苑免费",
                        "booking_method": "东御苑无需预约",
                        "image": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800",
                        "video": "https://www.youtube.com/watch?v=coYw-eVU0Ks",
                        "country": "日本",
                        "city": "东京",
                        "address": "1-1 Chiyoda, Chiyoda City, Tokyo"
                    },
                    {
                        "name": "涩谷十字路口",
                        "latitude": 35.6598,
                        "longitude": 139.7006,
                        "category": "城市地标",
                        "description": "世界最繁忙的十字路口，东京都市生活的象征。",
                        "opening_hours": "全天开放",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1545569341-9eb8b30979d9?w=800",
                        "video": "https://www.youtube.com/watch?v=coYw-eVU0Ks",
                        "country": "日本",
                        "city": "东京",
                        "address": "Shibuya City, Tokyo"
                    },
                    {
                        "name": "银座",
                        "latitude": 35.6717,
                        "longitude": 139.7640,
                        "category": "购物区域",
                        "description": "东京最高档的购物区，世界知名品牌的聚集地。",
                        "opening_hours": "商店营业时间各异",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800",
                        "video": "https://www.youtube.com/watch?v=coYw-eVU0Ks",
                        "country": "日本",
                        "city": "东京",
                        "address": "Ginza, Chuo City, Tokyo"
                    }
                ]
            },
            
            # 西班牙巴塞罗那
            "barcelona": {
                "name": "巴塞罗那",
                "country": "西班牙",
                "coordinates": [41.3851, 2.1734],
                "attractions": [
                    {
                        "name": "圣家堂",
                        "latitude": 41.4036,
                        "longitude": 2.1744,
                        "category": "宗教建筑",
                        "description": "高迪设计的未完成杰作，巴塞罗那最著名的建筑。",
                        "opening_hours": "09:00-20:00",
                        "ticket_price": "成人票：26欧元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "西班牙",
                        "city": "巴塞罗那",
                        "address": "Carrer de Mallorca, 401, 08013 Barcelona"
                    },
                    {
                        "name": "巴特罗之家",
                        "latitude": 41.3916,
                        "longitude": 2.1649,
                        "category": "建筑艺术",
                        "description": "高迪改造的现代主义建筑杰作，色彩斑斓的外观令人惊叹。",
                        "opening_hours": "09:00-20:00",
                        "ticket_price": "成人票：35欧元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1515542622106-78bda8ba0e5b?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "西班牙",
                        "city": "巴塞罗那",
                        "address": "Passeig de Gràcia, 43, 08007 Barcelona"
                    },
                    {
                        "name": "古埃尔公园",
                        "latitude": 41.4145,
                        "longitude": 2.1527,
                        "category": "公园",
                        "description": "高迪设计的童话般公园，充满了马赛克装饰和奇特建筑。",
                        "opening_hours": "08:00-21:30",
                        "ticket_price": "成人票：10欧元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "西班牙",
                        "city": "巴塞罗那",
                        "address": "08024 Barcelona"
                    },
                    {
                        "name": "兰布拉大道",
                        "latitude": 41.3818,
                        "longitude": 2.1673,
                        "category": "步行街",
                        "description": "巴塞罗那最著名的步行街，充满活力的城市动脉。",
                        "opening_hours": "全天开放",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "西班牙",
                        "city": "巴塞罗那",
                        "address": "La Rambla, Barcelona"
                    }
                ]
            },
            
            # 泰国曼谷
            "bangkok": {
                "name": "曼谷",
                "country": "泰国",
                "coordinates": [13.7563, 100.5018],
                "attractions": [
                    {
                        "name": "大皇宫",
                        "latitude": 13.7500,
                        "longitude": 100.4915,
                        "category": "皇室建筑",
                        "description": "泰国王室的宫殿，金碧辉煌的建筑群，泰式建筑的典范。",
                        "opening_hours": "08:30-15:30",
                        "ticket_price": "成人票：500泰铢",
                        "booking_method": "现场购票",
                        "image": "https://images.unsplash.com/photo-1563492065-4c1b8b5b2a4c?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "泰国",
                        "city": "曼谷",
                        "address": "Phra Borom Maha Ratchawang, Phra Nakhon, Bangkok"
                    },
                    {
                        "name": "卧佛寺",
                        "latitude": 13.7465,
                        "longitude": 100.4927,
                        "category": "宗教建筑",
                        "description": "曼谷最古老的寺庙，以46米长的卧佛像闻名。",
                        "opening_hours": "08:00-18:30",
                        "ticket_price": "成人票：200泰铢",
                        "booking_method": "现场购票",
                        "image": "https://images.unsplash.com/photo-1563492065-4c1b8b5b2a4c?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "泰国",
                        "city": "曼谷",
                        "address": "2 Sanamchai Road, Grand Palace Subdistrict, Pranakorn District, Bangkok"
                    },
                    {
                        "name": "郑王庙",
                        "latitude": 13.7436,
                        "longitude": 100.4889,
                        "category": "宗教建筑",
                        "description": "泰国最美的寺庙之一，以其高耸的主塔闻名。",
                        "opening_hours": "08:00-18:00",
                        "ticket_price": "成人票：100泰铢",
                        "booking_method": "现场购票",
                        "image": "https://images.unsplash.com/photo-1563492065-4c1b8b5b2a4c?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "泰国",
                        "city": "曼谷",
                        "address": "158 Thanon Wang Doem, Wat Arun, Bangkok Yai, Bangkok"
                    },
                    {
                        "name": "考山路",
                        "latitude": 13.7590,
                        "longitude": 100.4977,
                        "category": "夜生活区",
                        "description": "背包客的天堂，充满活力的夜生活街区。",
                        "opening_hours": "全天开放",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1563492065-4c1b8b5b2a4c?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "泰国",
                        "city": "曼谷",
                        "address": "Khao San Road, Talat Yot, Phra Nakhon, Bangkok"
                    }
                ]
            },
            
            # 土耳其伊斯坦布尔
            "istanbul": {
                "name": "伊斯坦布尔",
                "country": "土耳其",
                "coordinates": [41.0082, 28.9784],
                "attractions": [
                    {
                        "name": "圣索菲亚大教堂",
                        "latitude": 41.0086,
                        "longitude": 28.9802,
                        "category": "宗教建筑",
                        "description": "拜占庭建筑的杰作，曾是世界上最大的教堂。",
                        "opening_hours": "09:00-19:00",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1541432901042-2d8bd64b4a9b?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "土耳其",
                        "city": "伊斯坦布尔",
                        "address": "Sultan Ahmet, Ayasofya Meydanı No:1, 34122 Fatih/İstanbul"
                    },
                    {
                        "name": "蓝色清真寺",
                        "latitude": 41.0054,
                        "longitude": 28.9768,
                        "category": "宗教建筑",
                        "description": "伊斯坦布尔的标志性建筑，以其蓝色瓷砖装饰闻名。",
                        "opening_hours": "08:30-12:00, 14:00-16:30, 17:30-18:30",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1541432901042-2d8bd64b4a9b?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "土耳其",
                        "city": "伊斯坦布尔",
                        "address": "Sultan Ahmet, At Meydanı No:7, 34122 Fatih/İstanbul"
                    },
                    {
                        "name": "托普卡帕宫",
                        "latitude": 41.0115,
                        "longitude": 28.9833,
                        "category": "皇室建筑",
                        "description": "奥斯曼帝国苏丹的宫殿，现为博物馆。",
                        "opening_hours": "09:00-18:45",
                        "ticket_price": "成人票：100土耳其里拉",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1541432901042-2d8bd64b4a9b?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "土耳其",
                        "city": "伊斯坦布尔",
                        "address": "Cankurtaran, 34122 Fatih/İstanbul"
                    },
                    {
                        "name": "大巴扎",
                        "latitude": 41.0108,
                        "longitude": 28.9680,
                        "category": "传统市场",
                        "description": "世界上最古老的有顶市场之一，购物的天堂。",
                        "opening_hours": "09:00-19:00",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1541432901042-2d8bd64b4a9b?w=800",
                        "video": "https://www.youtube.com/watch?v=YQHsXMglC9A",
                        "country": "土耳其",
                        "city": "伊斯坦布尔",
                        "address": "Beyazıt, 34126 Fatih/İstanbul"
                    }
                ]
            }
        }
        
        # 中国知名旅游城市景点数据
        self.china_cities = {
            # 北京 (集成LocalAttractionsDB数据)
            "beijing": {
                "name": "北京",
                "country": "中国", 
                "coordinates": [39.9042, 116.4074],
                "attractions": "use_local_db"  # 标记使用本地数据库
            },
            
            # 西安
            "xian": {
                "name": "西安",
                "country": "中国",
                "coordinates": [34.3416, 108.9398],
                "attractions": [
                    {
                        "name": "秦始皇兵马俑博物馆",
                        "latitude": 34.3848,
                        "longitude": 109.2734,
                        "category": "历史遗迹",
                        "description": "世界第八大奇迹，秦始皇陵的陪葬坑，展现了古代军队的壮观景象。",
                        "opening_hours": "08:30-18:00",
                        "ticket_price": "成人票：120元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1564564321837-a57b7070ac4f?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "西安市临潼区",
                        "address": "陕西省西安市临潼区秦陵北路"
                    },
                    {
                        "name": "西安古城墙",
                        "latitude": 34.2583,
                        "longitude": 108.9286,
                        "category": "历史建筑",
                        "description": "世界上保存最完整的古代城垣建筑，明代建筑的杰作。",
                        "opening_hours": "08:00-22:00",
                        "ticket_price": "成人票：54元",
                        "booking_method": "现场购票或网上预约",
                        "image": "https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "西安市",
                        "address": "陕西省西安市中心城区"
                    },
                    {
                        "name": "大雁塔",
                        "latitude": 34.2192,
                        "longitude": 108.9649,
                        "category": "宗教建筑",
                        "description": "唐代佛教文化的象征，玄奘法师译经之地。",
                        "opening_hours": "08:00-17:30",
                        "ticket_price": "成人票：50元",
                        "booking_method": "现场购票",
                        "image": "https://images.unsplash.com/photo-1564564321837-a57b7070ac4f?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "西安市雁塔区",
                        "address": "陕西省西安市雁塔区雁塔路"
                    },
                    {
                        "name": "大唐不夜城",
                        "latitude": 34.2165,
                        "longitude": 108.9673,
                        "category": "文化街区",
                        "description": "以盛唐文化为背景的大型文化主题街区，夜景璀璨。",
                        "opening_hours": "全天开放",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "西安市雁塔区",
                        "address": "陕西省西安市雁塔区慈恩寺遗址公园南侧"
                    }
                ]
            },
            
            # 杭州
            "hangzhou": {
                "name": "杭州",
                "country": "中国",
                "coordinates": [30.2741, 120.1551],
                "attractions": [
                    {
                        "name": "西湖",
                        "latitude": 30.2369,
                        "longitude": 120.1506,
                        "category": "自然景观",
                        "description": "中国最著名的湖泊之一，'上有天堂，下有苏杭'的代表。",
                        "opening_hours": "全天开放",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1518391846015-55a9cc003b25?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "杭州市西湖区",
                        "address": "浙江省杭州市西湖区"
                    },
                    {
                        "name": "灵隐寺",
                        "latitude": 30.2408,
                        "longitude": 120.1019,
                        "category": "宗教建筑",
                        "description": "中国佛教名刹，有1600多年历史，济公的传说发源地。",
                        "opening_hours": "07:00-18:15",
                        "ticket_price": "成人票：75元",
                        "booking_method": "现场购票或网上预约",
                        "image": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "杭州市西湖区",
                        "address": "浙江省杭州市西湖区灵隐路法云弄1号"
                    },
                    {
                        "name": "千岛湖",
                        "latitude": 29.6050,
                        "longitude": 119.0220,
                        "category": "自然景观",
                        "description": "人工湖泊，有1078个岛屿，是国家级风景名胜区。",
                        "opening_hours": "08:00-17:00",
                        "ticket_price": "成人票：130元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1518391846015-55a9cc003b25?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "杭州市淳安县",
                        "address": "浙江省杭州市淳安县千岛湖镇"
                    }
                ]
            },
            
            # 成都
            "chengdu": {
                "name": "成都",
                "country": "中国",
                "coordinates": [30.5728, 104.0668],
                "attractions": [
                    {
                        "name": "大熊猫繁育研究基地",
                        "latitude": 30.7327,
                        "longitude": 104.1504,
                        "category": "动物园",
                        "description": "世界著名的大熊猫科研繁育基地，观赏可爱熊猫的最佳地点。",
                        "opening_hours": "07:30-18:00",
                        "ticket_price": "成人票：58元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1564564321837-a57b7070ac4f?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "成都市成华区",
                        "address": "四川省成都市成华区熊猫大道1375号"
                    },
                    {
                        "name": "宽窄巷子",
                        "latitude": 30.6598,
                        "longitude": 104.0633,
                        "category": "历史街区",
                        "description": "成都遗留下来的清朝古街道，体现老成都的生活韵味。",
                        "opening_hours": "全天开放",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "成都市青羊区",
                        "address": "四川省成都市青羊区同仁路以东长顺街以西"
                    },
                    {
                        "name": "都江堰",
                        "latitude": 31.0074,
                        "longitude": 103.6477,
                        "category": "水利工程",
                        "description": "世界文化遗产，古代水利工程的杰作，造福川西平原2000多年。",
                        "opening_hours": "08:00-17:30",
                        "ticket_price": "成人票：80元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1518391846015-55a9cc003b25?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "都江堰市",
                        "address": "四川省都江堰市公园路"
                    }
                ]
            },
            
            # 上海
            "shanghai": {
                "name": "上海",
                "country": "中国", 
                "coordinates": [31.2304, 121.4737],
                "attractions": [
                    {
                        "name": "外滩",
                        "latitude": 31.2396,
                        "longitude": 121.4900,
                        "category": "历史建筑群",
                        "description": "上海的标志性景观，万国建筑博览群，展现了上海的历史与现代。",
                        "opening_hours": "全天开放",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "上海市黄浦区",
                        "address": "上海市黄浦区中山东一路"
                    },
                    {
                        "name": "东方明珠",
                        "latitude": 31.2397,
                        "longitude": 121.4994,
                        "category": "观景建筑",
                        "description": "上海的标志性建筑，高468米的电视塔，可俯瞰整个上海。",
                        "opening_hours": "08:00-21:30",
                        "ticket_price": "成人票：220元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "上海市浦东新区",
                        "address": "上海市浦东新区世纪大道1号"
                    },
                    {
                        "name": "上海中心大厦",
                        "latitude": 31.2335,
                        "longitude": 121.5052,
                        "category": "摩天大楼",
                        "description": "中国第二高楼，高632米，拥有世界最高的观景台。",
                        "opening_hours": "08:30-22:00",
                        "ticket_price": "成人票：199元",
                        "booking_method": "官方网站预约",
                        "image": "https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "上海市浦东新区",
                        "address": "上海市浦东新区银城中路501号"
                    },
                    {
                        "name": "南京路步行街",
                        "latitude": 31.2353,
                        "longitude": 121.4759,
                        "category": "商业街区",
                        "description": "中国最著名的商业街之一，有'中华商业第一街'之称。",
                        "opening_hours": "全天开放",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "上海市黄浦区",
                        "address": "上海市黄浦区南京东路"
                    },
                    {
                        "name": "豫园",
                        "latitude": 31.2270,
                        "longitude": 121.4904,
                        "category": "古典园林",
                        "description": "明代私人花园，江南古典园林的代表，体现了明清园林艺术。",
                        "opening_hours": "08:30-17:30",
                        "ticket_price": "成人票：40元",
                        "booking_method": "现场购票",
                        "image": "https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "上海市黄浦区",
                        "address": "上海市黄浦区福佑路168号"
                    },
                    {
                        "name": "新天地",
                        "latitude": 31.2207,
                        "longitude": 121.4759,
                        "category": "文化街区",
                        "description": "上海最具特色的都市旅游景点，融合了东西方文化。",
                        "opening_hours": "全天开放",
                        "ticket_price": "免费",
                        "booking_method": "无需预约",
                        "image": "https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=800",
                        "video": "https://www.youtube.com/watch?v=Q8TXgCzxEnw",
                        "country": "中国",
                        "city": "上海市黄浦区",
                        "address": "上海市黄浦区太仓路181弄"
                    }
                ]
            }
        }
    
    def get_all_cities(self) -> List[Dict]:
        """获取所有城市列表"""
        cities = []
        
        # 添加全球城市
        for city_key, city_data in self.global_cities.items():
            cities.append({
                "key": city_key,
                "name": city_data["name"],
                "country": city_data["country"],
                "coordinates": city_data["coordinates"],
                "type": "global",
                "attraction_count": len(city_data["attractions"])
            })
        
        # 添加中国城市
        for city_key, city_data in self.china_cities.items():
            # 特殊处理北京：计算本地数据库的景点数量
            if city_key == "beijing" and city_data["attractions"] == "use_local_db":
                from local_attractions_db import local_attractions_db
                attraction_count = len(local_attractions_db.attractions)
            else:
                attraction_count = len(city_data["attractions"]) if isinstance(city_data["attractions"], list) else 0
            
            cities.append({
                "key": city_key,
                "name": city_data["name"],
                "country": city_data["country"],
                "coordinates": city_data["coordinates"],
                "type": "china",
                "attraction_count": attraction_count
            })
        
        return cities
    
    def get_city_attractions(self, city_key: str) -> List[Dict]:
        """获取指定城市的景点列表"""
        if city_key in self.global_cities:
            return self.global_cities[city_key]["attractions"]
        elif city_key in self.china_cities:
            city_data = self.china_cities[city_key]
            # 特殊处理北京：从本地数据库获取景点
            if city_key == "beijing" and city_data["attractions"] == "use_local_db":
                from local_attractions_db import local_attractions_db
                return local_attractions_db.attractions
            else:
                return city_data["attractions"] if isinstance(city_data["attractions"], list) else []
        return []
    
    def get_random_attraction(self, city_key: str) -> Optional[Dict]:
        """随机获取城市中的一个景点"""
        attractions = self.get_city_attractions(city_key)
        if attractions:
            return random.choice(attractions)
        return None
    
    def search_cities(self, query: str) -> List[Dict]:
        """搜索城市"""
        query = query.lower()
        results = []
        
        all_cities = self.get_all_cities()
        for city in all_cities:
            if query in city["name"].lower() or query in city["country"].lower():
                results.append(city)
        
        return results
    
    def get_city_by_key(self, city_key: str) -> Optional[Dict]:
        """根据key获取城市信息"""
        if city_key in self.global_cities:
            return self.global_cities[city_key]
        elif city_key in self.china_cities:
            return self.china_cities[city_key]
        return None
    
    def find_nearby_attractions(self, latitude: float, longitude: float, radius_km: float = 50) -> List[Dict]:
        """查找指定坐标附近的景点"""
        nearby_attractions = []
        
        # 搜索全球城市景点
        for city_key, city_data in self.global_cities.items():
            for attraction in city_data["attractions"]:
                distance = self._calculate_distance(
                    latitude, longitude,
                    attraction["latitude"], attraction["longitude"]
                )
                if distance <= radius_km:
                    attraction_copy = attraction.copy()
                    attraction_copy["distance"] = distance
                    nearby_attractions.append(attraction_copy)
        
        # 搜索中国城市景点
        for city_key, city_data in self.china_cities.items():
            # 特殊处理北京：使用LocalAttractionsDB数据
            if city_key == "beijing" and city_data["attractions"] == "use_local_db":
                from local_attractions_db import local_attractions_db
                local_attractions = local_attractions_db.find_nearby_attractions(latitude, longitude, radius_km)
                for attraction in local_attractions:
                    attraction_copy = attraction.copy()
                    attraction_copy["distance"] = attraction.get("distance_to_point", 0)
                    nearby_attractions.append(attraction_copy)
            else:
                # 处理其他城市的常规景点数据
                if isinstance(city_data["attractions"], list):
                    for attraction in city_data["attractions"]:
                        distance = self._calculate_distance(
                            latitude, longitude,
                            attraction["latitude"], attraction["longitude"]
                        )
                        if distance <= radius_km:
                            attraction_copy = attraction.copy()
                            attraction_copy["distance"] = distance
                            nearby_attractions.append(attraction_copy)
        
        # 按距离排序
        nearby_attractions.sort(key=lambda x: x.get("distance", 999))
        return nearby_attractions
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点之间的距离（公里）"""
        # 使用Haversine公式计算球面距离
        R = 6371  # 地球半径（公里）
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance