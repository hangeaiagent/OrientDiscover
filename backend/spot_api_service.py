# Spot地图相册API服务
# Spot Map Album API Service

import logging
from typing import List, Dict, Optional, Any
from fastapi import HTTPException
from supabase_client import supabase_client
import asyncio

logger = logging.getLogger(__name__)

class SpotAPIService:
    """Spot地图相册API服务类"""
    
    def __init__(self):
        """初始化API服务"""
        self.supabase = supabase_client
        logger.info("SpotAPIService初始化完成")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            is_connected = await self.supabase.test_connection()
            return {
                "status": "healthy" if is_connected else "unhealthy",
                "database_connected": is_connected,
                "service": "Spot地图相册API",
                "version": "1.0.0"
            }
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "error",
                "database_connected": False,
                "error": str(e)
            }
    
    # ==================== 景点相关API ====================
    
    async def get_nearby_attractions(self, latitude: float, longitude: float, 
                                   radius_km: float = 50) -> List[Dict]:
        """获取附近景点"""
        try:
            # 验证输入参数
            if not (-90 <= latitude <= 90):
                raise ValueError("纬度必须在-90到90之间")
            if not (-180 <= longitude <= 180):
                raise ValueError("经度必须在-180到180之间")
            if radius_km <= 0 or radius_km > 1000:
                raise ValueError("搜索半径必须在0-1000公里之间")
            
            logger.info(f"查询附近景点: ({latitude:.4f}, {longitude:.4f}), 半径: {radius_km}km")
            
            attractions = self.supabase.get_attractions_near_location(
                latitude, longitude, radius_km
            )
            
            logger.info(f"找到 {len(attractions)} 个附近景点")
            return attractions
            
        except ValueError as e:
            logger.warning(f"参数验证失败: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"获取附近景点失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取附近景点失败: {str(e)}")
    
    async def get_all_attractions(self) -> List[Dict]:
        """获取所有景点"""
        try:
            logger.info("获取所有景点")
            attractions = self.supabase.get_all_attractions()
            logger.info(f"获取到 {len(attractions)} 个景点")
            return attractions
            
        except Exception as e:
            logger.error(f"获取所有景点失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取所有景点失败: {str(e)}")
    
    async def get_attractions_by_category(self, category: str) -> List[Dict]:
        """根据类别获取景点"""
        try:
            if not category:
                raise ValueError("类别不能为空")
            
            logger.info(f"根据类别获取景点: {category}")
            attractions = self.supabase.get_attractions_by_category(category)
            logger.info(f"找到 {len(attractions)} 个 {category} 类景点")
            return attractions
            
        except ValueError as e:
            logger.warning(f"参数验证失败: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"根据类别获取景点失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取景点失败: {str(e)}")
    
    async def get_attractions_by_city(self, city: str) -> List[Dict]:
        """根据城市获取景点"""
        try:
            if not city:
                raise ValueError("城市不能为空")
            
            logger.info(f"根据城市获取景点: {city}")
            attractions = self.supabase.get_attractions_by_city(city)
            logger.info(f"找到 {len(attractions)} 个 {city} 的景点")
            return attractions
            
        except ValueError as e:
            logger.warning(f"参数验证失败: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"根据城市获取景点失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取景点失败: {str(e)}")
    
    async def search_attractions(self, query: str) -> List[Dict]:
        """搜索景点"""
        try:
            if not query or len(query.strip()) < 2:
                raise ValueError("搜索关键词至少需要2个字符")
            
            query = query.strip()
            logger.info(f"搜索景点: {query}")
            attractions = self.supabase.search_attractions(query)
            logger.info(f"搜索到 {len(attractions)} 个相关景点")
            return attractions
            
        except ValueError as e:
            logger.warning(f"参数验证失败: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"搜索景点失败: {e}")
            raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
    
    # ==================== 相册相关API ====================
    
    async def create_album(self, creator_id: str, title: str, 
                          description: str = None, access_level: str = 'public') -> Dict:
        """创建新相册"""
        try:
            if not creator_id:
                raise ValueError("创建者ID不能为空")
            if not title or len(title.strip()) < 1:
                raise ValueError("相册标题不能为空")
            if access_level not in ['public', 'private']:
                raise ValueError("访问级别必须是 public 或 private")
            
            logger.info(f"创建相册: {title} (创建者: {creator_id})")
            album = self.supabase.create_album(creator_id, title.strip(), description, access_level)
            
            if album:
                logger.info(f"相册创建成功: {album['id']}")
                return album
            else:
                raise HTTPException(status_code=500, detail="创建相册失败")
                
        except ValueError as e:
            logger.warning(f"参数验证失败: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"创建相册失败: {e}")
            raise HTTPException(status_code=500, detail=f"创建相册失败: {str(e)}")
    
    async def get_public_albums(self, limit: int = 20, offset: int = 0) -> List[Dict]:
        """获取公开相册"""
        try:
            if limit <= 0 or limit > 100:
                raise ValueError("限制数量必须在1-100之间")
            if offset < 0:
                raise ValueError("偏移量不能为负数")
            
            logger.info(f"获取公开相册: limit={limit}, offset={offset}")
            albums = self.supabase.get_public_albums(limit, offset)
            logger.info(f"获取到 {len(albums)} 个公开相册")
            return albums
            
        except ValueError as e:
            logger.warning(f"参数验证失败: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"获取公开相册失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取相册失败: {str(e)}")
    
    async def get_user_albums(self, user_id: str) -> List[Dict]:
        """获取用户相册"""
        try:
            if not user_id:
                raise ValueError("用户ID不能为空")
            
            logger.info(f"获取用户相册: {user_id}")
            albums = self.supabase.get_user_albums(user_id)
            logger.info(f"用户 {user_id} 有 {len(albums)} 个相册")
            return albums
            
        except ValueError as e:
            logger.warning(f"参数验证失败: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"获取用户相册失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取用户相册失败: {str(e)}")
    
    # ==================== 统计API ====================
    
    async def get_statistics(self) -> Dict:
        """获取统计信息"""
        try:
            logger.info("获取系统统计信息")
            stats = self.supabase.get_statistics()
            logger.info("统计信息获取成功")
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
    
    # ==================== 数据转换方法 ====================
    
    def _convert_attraction_for_api(self, attraction: Dict) -> Dict:
        """将数据库景点数据转换为API格式"""
        return {
            "id": attraction.get("id"),
            "name": attraction.get("name"),
            "latitude": attraction.get("latitude"),
            "longitude": attraction.get("longitude"),
            "category": attraction.get("category"),
            "country": attraction.get("country"),
            "city": attraction.get("city"),
            "address": attraction.get("address"),
            "description": attraction.get("description", ""),
            "opening_hours": attraction.get("opening_hours"),
            "ticket_price": attraction.get("ticket_price"),
            "booking_method": attraction.get("booking_method"),
            "image": attraction.get("image"),
            "video": attraction.get("video"),
            "distance": attraction.get("distance"),  # 如果有距离信息
            "media": attraction.get("media", [])  # 如果有媒体资源
        }
    
    def _convert_album_for_api(self, album: Dict) -> Dict:
        """将数据库相册数据转换为API格式"""
        return {
            "id": album.get("id"),
            "title": album.get("title"),
            "description": album.get("description"),
            "creator_id": album.get("creator_id"),
            "creator_type": album.get("creator_type"),
            "access_level": album.get("access_level"),
            "cover_image": album.get("cover_image"),
            "tags": album.get("tags", []),
            "view_count": album.get("view_count", 0),
            "like_count": album.get("like_count", 0),
            "is_recommended": album.get("is_recommended", False),
            "created_at": album.get("created_at"),
            "updated_at": album.get("updated_at")
        }

# 全局实例
spot_api_service = SpotAPIService()