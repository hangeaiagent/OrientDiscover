"""
向量数据库服务

集成pgvector扩展到Supabase，实现文本向量化和相似度搜索
支持景点内容的向量索引和语义搜索
"""

import os
import json
import logging
import asyncio
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import openai
from dotenv import load_dotenv
from supabase import create_client, Client
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


class EmbeddingService:
    """文本向量化服务"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = "text-embedding-3-small"  # 使用最新的嵌入模型
        self.dimension = 1536  # text-embedding-3-small的维度
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成文本向量"""
        try:
            if not texts:
                return []
            
            # 清理和预处理文本
            cleaned_texts = [self._clean_text(text) for text in texts if text and text.strip()]
            
            if not cleaned_texts:
                return []
            
            # 调用OpenAI API生成嵌入
            response = await asyncio.to_thread(
                self.openai_client.embeddings.create,
                model=self.model,
                input=cleaned_texts
            )
            
            embeddings = [data.embedding for data in response.data]
            logger.info(f"成功生成 {len(embeddings)} 个向量，维度: {len(embeddings[0]) if embeddings else 0}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"生成向量失败: {e}")
            return []
    
    async def generate_single_embedding(self, text: str) -> Optional[List[float]]:
        """生成单个文本的向量"""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else None
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # 移除多余的空白字符
        cleaned = ' '.join(text.split())
        
        # 限制长度（OpenAI有token限制）
        max_length = 8000  # 大约对应8k tokens
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length] + "..."
        
        return cleaned
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # 计算余弦相似度
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"计算相似度失败: {e}")
            return 0.0


class VectorDatabase:
    """向量数据库服务"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        self.db_url = os.getenv("SUPABASE_DB_URL")  # 直接数据库连接URL
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("缺少Supabase配置")
        
        # 创建Supabase客户端
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # 嵌入服务
        self.embedding_service = EmbeddingService()
        
        # 数据库连接（用于pgvector操作）
        self.db_connection = None
        if self.db_url:
            try:
                self.db_connection = psycopg2.connect(self.db_url)
                logger.info("PostgreSQL数据库连接成功")
            except Exception as e:
                logger.warning(f"无法连接PostgreSQL数据库: {e}")
    
    async def initialize_vector_tables(self):
        """初始化向量表结构"""
        try:
            if not self.db_connection:
                logger.warning("没有数据库连接，跳过向量表初始化")
                return
            
            with self.db_connection.cursor() as cursor:
                # 启用pgvector扩展
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # 创建景点向量表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS spot_attraction_embeddings (
                        id SERIAL PRIMARY KEY,
                        attraction_id UUID REFERENCES spot_attractions(id) ON DELETE CASCADE,
                        content_type VARCHAR(50) NOT NULL,
                        language_code VARCHAR(10) DEFAULT 'zh-CN',
                        content_text TEXT NOT NULL,
                        embedding VECTOR(1536) NOT NULL,
                        content_hash VARCHAR(64) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(attraction_id, content_type, language_code, content_hash)
                    );
                """)
                
                # 创建向量索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS spot_attraction_embeddings_vector_idx 
                    ON spot_attraction_embeddings 
                    USING ivfflat (embedding vector_cosine_ops) 
                    WITH (lists = 100);
                """)
                
                # 创建其他索引
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS spot_attraction_embeddings_attraction_id_idx 
                    ON spot_attraction_embeddings (attraction_id);
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS spot_attraction_embeddings_content_type_idx 
                    ON spot_attraction_embeddings (content_type);
                """)
                
                self.db_connection.commit()
                logger.info("向量表结构初始化完成")
                
        except Exception as e:
            logger.error(f"初始化向量表失败: {e}")
            if self.db_connection:
                self.db_connection.rollback()
    
    async def store_attraction_embeddings(self, attraction_id: str, contents: Dict[str, str], language_code: str = 'zh-CN'):
        """存储景点向量"""
        try:
            stored_count = 0
            
            for content_type, text in contents.items():
                if not text or not text.strip():
                    continue
                
                # 生成内容哈希
                content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
                
                # 检查是否已存在
                if await self._embedding_exists(attraction_id, content_type, language_code, content_hash):
                    logger.info(f"向量已存在，跳过: {attraction_id} - {content_type}")
                    continue
                
                # 生成向量
                embedding = await self.embedding_service.generate_single_embedding(text)
                if not embedding:
                    logger.warning(f"无法生成向量: {attraction_id} - {content_type}")
                    continue
                
                # 存储到数据库
                if self.db_connection:
                    await self._store_embedding_to_postgres(
                        attraction_id, content_type, language_code, text, embedding, content_hash
                    )
                else:
                    await self._store_embedding_to_supabase(
                        attraction_id, content_type, language_code, text, embedding, content_hash
                    )
                
                stored_count += 1
                logger.info(f"已存储向量: {attraction_id} - {content_type}")
            
            logger.info(f"景点 {attraction_id} 总共存储了 {stored_count} 个向量")
            return stored_count
            
        except Exception as e:
            logger.error(f"存储景点向量失败: {e}")
            return 0
    
    async def _embedding_exists(self, attraction_id: str, content_type: str, language_code: str, content_hash: str) -> bool:
        """检查向量是否已存在"""
        try:
            if self.db_connection:
                with self.db_connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT id FROM spot_attraction_embeddings 
                        WHERE attraction_id = %s AND content_type = %s 
                        AND language_code = %s AND content_hash = %s
                    """, (attraction_id, content_type, language_code, content_hash))
                    return cursor.fetchone() is not None
            else:
                result = self.supabase.table('spot_attraction_embeddings')\
                    .select('id')\
                    .eq('attraction_id', attraction_id)\
                    .eq('content_type', content_type)\
                    .eq('language_code', language_code)\
                    .eq('content_hash', content_hash)\
                    .execute()
                return len(result.data) > 0
                
        except Exception as e:
            logger.error(f"检查向量存在性失败: {e}")
            return False
    
    async def _store_embedding_to_postgres(self, attraction_id: str, content_type: str, 
                                         language_code: str, text: str, embedding: List[float], content_hash: str):
        """存储向量到PostgreSQL"""
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO spot_attraction_embeddings 
                    (attraction_id, content_type, language_code, content_text, embedding, content_hash)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (attraction_id, content_type, language_code, content_hash) 
                    DO UPDATE SET 
                        content_text = EXCLUDED.content_text,
                        embedding = EXCLUDED.embedding,
                        updated_at = CURRENT_TIMESTAMP
                """, (attraction_id, content_type, language_code, text, embedding, content_hash))
                
                self.db_connection.commit()
                
        except Exception as e:
            logger.error(f"存储向量到PostgreSQL失败: {e}")
            if self.db_connection:
                self.db_connection.rollback()
            raise
    
    async def _store_embedding_to_supabase(self, attraction_id: str, content_type: str,
                                         language_code: str, text: str, embedding: List[float], content_hash: str):
        """存储向量到Supabase"""
        try:
            # 注意：Supabase的Python客户端可能不直接支持向量类型
            # 这里假设表结构支持JSON存储向量
            result = self.supabase.table('spot_attraction_embeddings')\
                .upsert({
                    'attraction_id': attraction_id,
                    'content_type': content_type,
                    'language_code': language_code,
                    'content_text': text,
                    'embedding': embedding,  # 可能需要转换格式
                    'content_hash': content_hash
                })\
                .execute()
                
        except Exception as e:
            logger.error(f"存储向量到Supabase失败: {e}")
            raise
    
    async def similarity_search(self, query: str, language_code: str = 'zh-CN', 
                              limit: int = 10, threshold: float = 0.7) -> List[Dict]:
        """基于向量相似度搜索景点"""
        try:
            # 生成查询向量
            query_embedding = await self.embedding_service.generate_single_embedding(query)
            if not query_embedding:
                logger.error("无法生成查询向量")
                return []
            
            # 执行相似度搜索
            if self.db_connection:
                results = await self._similarity_search_postgres(
                    query_embedding, language_code, limit, threshold
                )
            else:
                results = await self._similarity_search_supabase(
                    query_embedding, language_code, limit, threshold
                )
            
            logger.info(f"相似度搜索返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"相似度搜索失败: {e}")
            return []
    
    async def _similarity_search_postgres(self, query_embedding: List[float], 
                                        language_code: str, limit: int, threshold: float) -> List[Dict]:
        """使用PostgreSQL进行相似度搜索"""
        try:
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        e.attraction_id,
                        e.content_type,
                        e.content_text,
                        e.embedding <-> %s::vector as distance,
                        1 - (e.embedding <-> %s::vector) as similarity,
                        a.name,
                        a.category,
                        a.city,
                        a.country,
                        a.address,
                        a.main_image_url,
                        ST_X(a.location) as longitude,
                        ST_Y(a.location) as latitude
                    FROM spot_attraction_embeddings e
                    JOIN spot_attractions a ON e.attraction_id = a.id
                    WHERE e.language_code = %s
                    AND 1 - (e.embedding <-> %s::vector) >= %s
                    ORDER BY e.embedding <-> %s::vector
                    LIMIT %s
                """, (query_embedding, query_embedding, language_code, query_embedding, threshold, query_embedding, limit))
                
                rows = cursor.fetchall()
                
                # 转换为字典列表
                results = []
                for row in rows:
                    result = dict(row)
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"PostgreSQL相似度搜索失败: {e}")
            return []
    
    async def _similarity_search_supabase(self, query_embedding: List[float],
                                        language_code: str, limit: int, threshold: float) -> List[Dict]:
        """使用Supabase进行相似度搜索（备用方案）"""
        try:
            # 注意：这是一个简化的实现，实际可能需要使用RPC函数
            # 获取所有嵌入向量进行客户端计算（不推荐用于生产环境）
            result = self.supabase.table('spot_attraction_embeddings')\
                .select('*, spot_attractions(*)')\
                .eq('language_code', language_code)\
                .limit(100)\
                .execute()  # 限制数量以避免性能问题
            
            if not result.data:
                return []
            
            # 计算相似度
            similarities = []
            for row in result.data:
                if 'embedding' in row and row['embedding']:
                    similarity = self.embedding_service.calculate_similarity(
                        query_embedding, row['embedding']
                    )
                    
                    if similarity >= threshold:
                        row['similarity'] = similarity
                        similarities.append(row)
            
            # 按相似度排序
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Supabase相似度搜索失败: {e}")
            return []
    
    async def batch_process_attractions(self, batch_size: int = 10):
        """批量处理景点，生成向量"""
        try:
            # 获取所有景点
            attractions_result = self.supabase.table('spot_attractions')\
                .select('id, name, category, address, opening_hours, ticket_price, booking_method')\
                .execute()
            
            if not attractions_result.data:
                logger.info("没有找到景点数据")
                return
            
            attractions = attractions_result.data
            logger.info(f"开始批量处理 {len(attractions)} 个景点")
            
            processed_count = 0
            for i in range(0, len(attractions), batch_size):
                batch = attractions[i:i + batch_size]
                
                for attraction in batch:
                    attraction_id = attraction['id']
                    
                    # 获取多语言内容
                    content_result = self.supabase.table('spot_attraction_contents')\
                        .select('*')\
                        .eq('attraction_id', attraction_id)\
                        .execute()
                    
                    # 准备内容字典
                    contents = {
                        'name': attraction.get('name', ''),
                        'category': attraction.get('category', ''),
                        'address': attraction.get('address', ''),
                        'opening_hours': attraction.get('opening_hours', ''),
                        'ticket_price': attraction.get('ticket_price', ''),
                        'booking_method': attraction.get('booking_method', '')
                    }
                    
                    # 添加多语言内容
                    if content_result.data:
                        for content in content_result.data:
                            lang = content.get('language_code', 'zh-CN')
                            contents[f'description_{lang}'] = content.get('description', '')
                            contents[f'introduction_{lang}'] = content.get('attraction_introduction', '')
                            contents[f'commentary_{lang}'] = content.get('guide_commentary', '')
                    
                    # 存储向量
                    stored_count = await self.store_attraction_embeddings(attraction_id, contents)
                    processed_count += stored_count
                
                logger.info(f"已处理 {min(i + batch_size, len(attractions))} / {len(attractions)} 个景点")
                
                # 添加延迟以避免API限制
                await asyncio.sleep(1)
            
            logger.info(f"批量处理完成，总共生成 {processed_count} 个向量")
            
        except Exception as e:
            logger.error(f"批量处理景点失败: {e}")
    
    async def search_attractions_by_semantic(self, query: str, location: Optional[Tuple[float, float]] = None,
                                           radius_km: float = 50, limit: int = 10) -> List[Dict]:
        """语义搜索景点（结合地理位置）"""
        try:
            # 先进行语义搜索
            semantic_results = await self.similarity_search(query, limit=limit * 2)
            
            if not location:
                return semantic_results[:limit]
            
            # 结合地理位置过滤
            lat, lon = location
            filtered_results = []
            
            for result in semantic_results:
                if 'latitude' in result and 'longitude' in result:
                    attr_lat = result['latitude']
                    attr_lon = result['longitude']
                    
                    # 计算距离
                    distance = self._calculate_distance(lat, lon, attr_lat, attr_lon)
                    
                    if distance <= radius_km:
                        result['distance_km'] = distance
                        filtered_results.append(result)
            
            # 按相似度和距离综合排序
            filtered_results.sort(key=lambda x: (
                -x.get('similarity', 0) * 0.7 +  # 相似度权重70%
                x.get('distance_km', 0) / radius_km * 0.3  # 距离权重30%
            ))
            
            return filtered_results[:limit]
            
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点间距离（公里）"""
        import math
        
        R = 6371  # 地球半径（公里）
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def close(self):
        """关闭数据库连接"""
        if self.db_connection:
            self.db_connection.close()
            logger.info("数据库连接已关闭")


# 全局向量数据库实例
vector_db = None

def get_vector_database() -> VectorDatabase:
    """获取向量数据库实例"""
    global vector_db
    if vector_db is None:
        vector_db = VectorDatabase()
    return vector_db