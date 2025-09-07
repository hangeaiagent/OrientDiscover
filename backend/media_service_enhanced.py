"""
增强的媒体资源管理服务

集成多种媒体资源获取方式和云存储服务
支持图片搜索、视频获取、资源优化等功能
"""

import os
import json
import logging
import asyncio
import aiohttp
import hashlib
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import requests
from PIL import Image
import io
import base64
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


class ImageSearchService:
    """图片搜索服务"""
    
    def __init__(self):
        self.unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        self.pexels_api_key = os.getenv("PEXELS_API_KEY")
        
    async def search_images(self, query: str, count: int = 5) -> List[Dict]:
        """搜索图片"""
        try:
            images = []
            
            # 尝试Unsplash API
            if self.unsplash_access_key:
                unsplash_images = await self._search_unsplash(query, count)
                images.extend(unsplash_images)
            
            # 如果图片不够，尝试Pexels API
            if len(images) < count and self.pexels_api_key:
                remaining_count = count - len(images)
                pexels_images = await self._search_pexels(query, remaining_count)
                images.extend(pexels_images)
            
            # 如果还是不够，使用默认图片
            if len(images) < count:
                default_images = self._get_default_images(query, count - len(images))
                images.extend(default_images)
            
            return images[:count]
            
        except Exception as e:
            logger.error(f"搜索图片失败: {e}")
            return self._get_default_images(query, count)
    
    async def _search_unsplash(self, query: str, count: int) -> List[Dict]:
        """使用Unsplash API搜索图片"""
        try:
            url = "https://api.unsplash.com/search/photos"
            headers = {
                "Authorization": f"Client-ID {self.unsplash_access_key}"
            }
            params = {
                "query": query,
                "per_page": min(count, 30),
                "orientation": "landscape"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        images = []
                        
                        for photo in data.get("results", []):
                            image_info = {
                                "url": photo["urls"]["regular"],
                                "thumbnail": photo["urls"]["small"],
                                "description": photo.get("alt_description", query),
                                "photographer": photo["user"]["name"],
                                "source": "Unsplash",
                                "width": photo["width"],
                                "height": photo["height"],
                                "quality": "high"
                            }
                            images.append(image_info)
                        
                        return images
            
            return []
            
        except Exception as e:
            logger.error(f"Unsplash搜索失败: {e}")
            return []
    
    async def _search_pexels(self, query: str, count: int) -> List[Dict]:
        """使用Pexels API搜索图片"""
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {
                "Authorization": self.pexels_api_key
            }
            params = {
                "query": query,
                "per_page": min(count, 80),
                "orientation": "landscape"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        images = []
                        
                        for photo in data.get("photos", []):
                            image_info = {
                                "url": photo["src"]["large"],
                                "thumbnail": photo["src"]["medium"],
                                "description": photo.get("alt", query),
                                "photographer": photo["photographer"],
                                "source": "Pexels",
                                "width": photo["width"],
                                "height": photo["height"],
                                "quality": "high"
                            }
                            images.append(image_info)
                        
                        return images
            
            return []
            
        except Exception as e:
            logger.error(f"Pexels搜索失败: {e}")
            return []
    
    def _get_default_images(self, query: str, count: int) -> List[Dict]:
        """获取默认图片"""
        # 基于查询关键词的默认图片映射
        default_mapping = {
            "自然": "photo-1506905925346-21bda4d32df4",
            "文化": "photo-1533929736458-ca588d08c8be",
            "城市": "photo-1477959858617-67f85cf4f1df",
            "建筑": "photo-1449824913935-59a10b8d2000",
            "山水": "photo-1441974231531-c6227db76b6e",
            "古迹": "photo-1564013799919-ab600027ffc6",
            "公园": "photo-1506905925346-21bda4d32df4",
            "博物馆": "photo-1533929736458-ca588d08c8be",
            "寺庙": "photo-1564013799919-ab600027ffc6"
        }
        
        # 选择最匹配的默认图片
        selected_id = "photo-1506905925346-21bda4d32df4"  # 默认自然风光
        for keyword, image_id in default_mapping.items():
            if keyword in query:
                selected_id = image_id
                break
        
        images = []
        for i in range(count):
            image_info = {
                "url": f"https://images.unsplash.com/{selected_id}?w=800&h=600&fit=crop",
                "thumbnail": f"https://images.unsplash.com/{selected_id}?w=400&h=300&fit=crop",
                "description": f"{query}相关图片",
                "photographer": "Unsplash",
                "source": "Default",
                "width": 800,
                "height": 600,
                "quality": "medium"
            }
            images.append(image_info)
        
        return images


class VideoSearchService:
    """视频搜索服务"""
    
    def __init__(self):
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.vimeo_access_token = os.getenv("VIMEO_ACCESS_TOKEN")
    
    async def search_videos(self, query: str, count: int = 2) -> List[Dict]:
        """搜索视频"""
        try:
            videos = []
            
            # 目前返回空列表，可以后续扩展YouTube或Vimeo API
            # 这里可以添加实际的视频搜索逻辑
            
            return videos
            
        except Exception as e:
            logger.error(f"搜索视频失败: {e}")
            return []


class CloudStorageService:
    """云存储服务"""
    
    def __init__(self):
        self.storage_type = os.getenv("CLOUD_STORAGE_TYPE", "local")
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_bucket = os.getenv("AWS_S3_BUCKET")
        self.local_storage_path = os.getenv("LOCAL_STORAGE_PATH", "/workspace/media_storage")
        
        # 确保本地存储目录存在
        os.makedirs(self.local_storage_path, exist_ok=True)
    
    async def upload_media(self, media_data: bytes, filename: str, content_type: str) -> str:
        """上传媒体文件"""
        try:
            if self.storage_type == "aws_s3" and self.aws_access_key:
                return await self._upload_to_s3(media_data, filename, content_type)
            else:
                return await self._upload_to_local(media_data, filename)
                
        except Exception as e:
            logger.error(f"上传媒体文件失败: {e}")
            return None
    
    async def _upload_to_s3(self, media_data: bytes, filename: str, content_type: str) -> str:
        """上传到AWS S3"""
        try:
            import boto3
            from botocore.exceptions import NoCredentialsError
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key
            )
            
            # 生成唯一文件名
            unique_filename = f"media/{datetime.now().strftime('%Y/%m/%d')}/{filename}"
            
            # 上传文件
            s3_client.put_object(
                Bucket=self.aws_bucket,
                Key=unique_filename,
                Body=media_data,
                ContentType=content_type,
                ACL='public-read'
            )
            
            # 返回公共URL
            url = f"https://{self.aws_bucket}.s3.amazonaws.com/{unique_filename}"
            return url
            
        except NoCredentialsError:
            logger.error("AWS凭证未配置")
            return None
        except Exception as e:
            logger.error(f"S3上传失败: {e}")
            return None
    
    async def _upload_to_local(self, media_data: bytes, filename: str) -> str:
        """上传到本地存储"""
        try:
            # 创建日期目录
            date_dir = datetime.now().strftime('%Y/%m/%d')
            full_dir = os.path.join(self.local_storage_path, date_dir)
            os.makedirs(full_dir, exist_ok=True)
            
            # 生成唯一文件名
            file_hash = hashlib.md5(media_data).hexdigest()[:8]
            unique_filename = f"{file_hash}_{filename}"
            file_path = os.path.join(full_dir, unique_filename)
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(media_data)
            
            # 返回相对URL路径
            relative_path = f"media/{date_dir}/{unique_filename}"
            return f"/api/media/{relative_path}"
            
        except Exception as e:
            logger.error(f"本地存储失败: {e}")
            return None
    
    async def download_and_store_image(self, image_url: str, filename: str = None) -> Optional[str]:
        """下载并存储图片"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        # 生成文件名
                        if not filename:
                            filename = f"image_{hashlib.md5(image_url.encode()).hexdigest()[:8]}.jpg"
                        
                        # 优化图片
                        optimized_data = await self._optimize_image(image_data)
                        
                        # 上传到存储
                        stored_url = await self.upload_media(optimized_data, filename, "image/jpeg")
                        return stored_url
            
            return None
            
        except Exception as e:
            logger.error(f"下载存储图片失败: {e}")
            return None
    
    async def _optimize_image(self, image_data: bytes, max_width: int = 800, quality: int = 85) -> bytes:
        """优化图片"""
        try:
            # 打开图片
            image = Image.open(io.BytesIO(image_data))
            
            # 转换为RGB（如果需要）
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # 调整大小
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # 保存为JPEG
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"图片优化失败: {e}")
            return image_data


class EnhancedMediaManager:
    """增强的媒体资源管理器"""
    
    def __init__(self):
        self.image_search = ImageSearchService()
        self.video_search = VideoSearchService()
        self.cloud_storage = CloudStorageService()
        
    async def fetch_media_resources(self, attraction: Dict) -> Dict:
        """获取景点的媒体资源"""
        try:
            attraction_name = attraction.get('name', '')
            attraction_city = attraction.get('city', '')
            attraction_category = attraction.get('category', '')
            
            logger.info(f"获取媒体资源：{attraction_name}")
            
            # 构建搜索查询
            search_queries = [
                f"{attraction_name} {attraction_city}",
                f"{attraction_name} 景点",
                f"{attraction_category} {attraction_city}",
                attraction_name
            ]
            
            # 搜索图片
            images = []
            for query in search_queries:
                if len(images) >= 3:
                    break
                
                search_results = await self.image_search.search_images(query, 2)
                for img in search_results:
                    if img not in images:
                        images.append(img)
            
            # 搜索视频
            videos = []
            if attraction_name:
                videos = await self.video_search.search_videos(f"{attraction_name} tour", 1)
            
            # 如果有现有图片，保留它
            existing_image = attraction.get('image')
            if existing_image and not any(img['url'] == existing_image for img in images):
                images.insert(0, {
                    "url": existing_image,
                    "thumbnail": existing_image,
                    "description": f"{attraction_name}",
                    "source": "existing",
                    "quality": "unknown"
                })
            
            # 生成缩略图URLs
            thumbnails = []
            for img in images:
                thumbnail = {
                    "url": img.get('thumbnail', img['url']),
                    "description": img.get('description', ''),
                    "size": "small"
                }
                thumbnails.append(thumbnail)
            
            return {
                'images': images[:5],  # 最多5张图片
                'videos': videos,
                'thumbnails': thumbnails,
                'media_summary': {
                    'total_images': len(images),
                    'total_videos': len(videos),
                    'primary_image': images[0]['url'] if images else None,
                    'has_high_quality': any(img.get('quality') == 'high' for img in images)
                }
            }
            
        except Exception as e:
            logger.error(f"获取媒体资源失败: {e}")
            return self._get_fallback_media(attraction)
    
    def _get_fallback_media(self, attraction: Dict) -> Dict:
        """获取备用媒体资源"""
        category = attraction.get('category', '景点')
        default_images = self.image_search._get_default_images(category, 1)
        
        return {
            'images': default_images,
            'videos': [],
            'thumbnails': [
                {
                    "url": default_images[0]['thumbnail'] if default_images else '',
                    "description": f"{attraction.get('name', '景点')}",
                    "size": "small"
                }
            ],
            'media_summary': {
                'total_images': 1,
                'total_videos': 0,
                'primary_image': default_images[0]['url'] if default_images else None,
                'has_high_quality': False
            }
        }
    
    async def process_and_store_media(self, media_resources: Dict) -> Dict:
        """处理并存储媒体资源到云存储"""
        try:
            processed_resources = media_resources.copy()
            
            # 处理图片
            if 'images' in processed_resources:
                processed_images = []
                for img in processed_resources['images']:
                    # 可以选择下载并存储到自己的云存储
                    # stored_url = await self.cloud_storage.download_and_store_image(img['url'])
                    # if stored_url:
                    #     img['stored_url'] = stored_url
                    
                    processed_images.append(img)
                
                processed_resources['images'] = processed_images
            
            return processed_resources
            
        except Exception as e:
            logger.error(f"处理存储媒体资源失败: {e}")
            return media_resources
    
    async def get_media_analytics(self, media_resources: Dict) -> Dict:
        """获取媒体资源分析"""
        try:
            analytics = {
                'quality_score': 0,
                'diversity_score': 0,
                'completeness_score': 0,
                'recommendations': []
            }
            
            images = media_resources.get('images', [])
            videos = media_resources.get('videos', [])
            
            # 计算质量分数
            high_quality_count = sum(1 for img in images if img.get('quality') == 'high')
            if images:
                analytics['quality_score'] = (high_quality_count / len(images)) * 100
            
            # 计算多样性分数
            sources = set(img.get('source', 'unknown') for img in images)
            analytics['diversity_score'] = min(len(sources) * 25, 100)
            
            # 计算完整性分数
            completeness = 0
            if images:
                completeness += 60
            if videos:
                completeness += 40
            analytics['completeness_score'] = completeness
            
            # 生成建议
            if analytics['quality_score'] < 50:
                analytics['recommendations'].append('建议获取更高质量的图片')
            if analytics['diversity_score'] < 50:
                analytics['recommendations'].append('建议增加图片来源的多样性')
            if not videos:
                analytics['recommendations'].append('建议添加视频资源以提升体验')
            
            return analytics
            
        except Exception as e:
            logger.error(f"媒体分析失败: {e}")
            return {}


# 全局增强媒体管理器实例
enhanced_media_manager = None

def get_enhanced_media_manager() -> EnhancedMediaManager:
    """获取增强媒体管理器实例"""
    global enhanced_media_manager
    if enhanced_media_manager is None:
        enhanced_media_manager = EnhancedMediaManager()
    return enhanced_media_manager