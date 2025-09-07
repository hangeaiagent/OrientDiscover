#!/usr/bin/env python3
"""
历史数据迁移脚本 - Python版本
Historical Data Migration Script for Spot Map Albums System
"""

import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from urllib.parse import urlparse

# 添加backend目录到Python路径
sys.path.append('/workspace/backend')

from local_attractions_db import local_attractions_db
from global_cities_db import GlobalCitiesDB

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Supabase数据库连接信息
DATABASE_URL = "postgresql://postgres:JjcUcOgvzPb7cHMH@db.uobwbhvwrciaxloqdizc.supabase.co:5432/postgres"

class HistoricalDataMigrator:
    """历史数据迁移器"""
    
    def __init__(self):
        self.conn = None
        self.global_db = GlobalCitiesDB()
        self.migration_stats = {
            'attractions_migrated': 0,
            'contents_migrated': 0,
            'media_migrated': 0,
            'errors': []
        }
    
    def connect_database(self):
        """连接数据库"""
        try:
            parsed = urlparse(DATABASE_URL)
            self.conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port,
                database=parsed.path[1:],
                user=parsed.username,
                password=parsed.password
            )
            logger.info("数据库连接成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def migrate_attraction(self, attraction_data: Dict, source: str) -> Optional[str]:
        """迁移单个景点数据"""
        try:
            cursor = self.conn.cursor()
            
            # 插入景点主表数据
            insert_attraction_sql = """
            INSERT INTO spot_attractions (
                name, location, category, country, city, address,
                opening_hours, ticket_price, booking_method, 
                main_image_url, video_url, created_at, updated_at
            ) VALUES (
                %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, %s, %s,
                %s, %s, %s, %s, %s, now(), now()
            ) RETURNING id;
            """
            
            cursor.execute(insert_attraction_sql, (
                attraction_data['name'],
                attraction_data['longitude'], 
                attraction_data['latitude'],
                attraction_data['category'],
                attraction_data['country'],
                attraction_data['city'],
                attraction_data.get('address', ''),
                attraction_data.get('opening_hours', ''),
                attraction_data.get('ticket_price', ''),
                attraction_data.get('booking_method', ''),
                attraction_data.get('image', attraction_data.get('main_image_url', '')),
                attraction_data.get('video', attraction_data.get('video_url', ''))
            ))
            
            attraction_id = cursor.fetchone()[0]
            
            # 插入中文描述到多语言内容表
            description = attraction_data.get('description', '')
            if description and description.strip():
                insert_content_sql = """
                INSERT INTO spot_attraction_contents (
                    attraction_id, language_code, name_translated, 
                    description, attraction_introduction, created_at
                ) VALUES (%s, %s, %s, %s, %s, now());
                """
                
                cursor.execute(insert_content_sql, (
                    attraction_id,
                    'zh-CN',
                    attraction_data['name'],
                    description,
                    description  # 将description同时作为introduction
                ))
                self.migration_stats['contents_migrated'] += 1
            
            # 插入媒体资源
            media_count = 0
            
            # 插入主图片
            image_url = attraction_data.get('image', attraction_data.get('main_image_url', ''))
            if image_url and image_url.strip():
                insert_media_sql = """
                INSERT INTO spot_attraction_media (
                    attraction_id, media_type, url, caption, 
                    is_primary, order_index, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, now());
                """
                
                cursor.execute(insert_media_sql, (
                    attraction_id,
                    'image',
                    image_url,
                    '景点主图片',
                    True,
                    0
                ))
                media_count += 1
            
            # 插入视频
            video_url = attraction_data.get('video', attraction_data.get('video_url', ''))
            if video_url and video_url.strip():
                cursor.execute(insert_media_sql, (
                    attraction_id,
                    'video', 
                    video_url,
                    '景点介绍视频',
                    False,
                    1
                ))
                media_count += 1
            
            self.migration_stats['media_migrated'] += media_count
            self.conn.commit()
            cursor.close()
            
            self.migration_stats['attractions_migrated'] += 1
            logger.info(f"✅ 迁移景点成功: {attraction_data['name']} (来源: {source})")
            
            return attraction_id
            
        except Exception as e:
            error_msg = f"迁移景点失败: {attraction_data.get('name', 'Unknown')} - {str(e)}"
            logger.error(error_msg)
            self.migration_stats['errors'].append(error_msg)
            self.conn.rollback()
            return None
    
    def migrate_local_attractions(self):
        """迁移本地北京景点数据"""
        logger.info("开始迁移本地北京景点数据...")
        
        local_attractions = local_attractions_db.attractions
        for attraction in local_attractions:
            self.migrate_attraction(attraction, "LocalAttractionsDB")
        
        logger.info(f"本地景点迁移完成: {len(local_attractions)} 个景点")
    
    def migrate_global_attractions(self):
        """迁移全球城市景点数据"""
        logger.info("开始迁移全球城市景点数据...")
        
        total_migrated = 0
        
        # 迁移全球城市景点
        for city_key, city_data in self.global_db.global_cities.items():
            logger.info(f"迁移城市: {city_data['name']} ({city_data['country']})")
            
            for attraction in city_data['attractions']:
                self.migrate_attraction(attraction, f"GlobalCitiesDB-{city_key}")
                total_migrated += 1
        
        # 迁移中国其他城市景点
        for city_key, city_data in self.global_db.china_cities.items():
            # 跳过北京（已在本地数据中处理）
            if city_key == "beijing":
                continue
                
            if isinstance(city_data['attractions'], list):
                logger.info(f"迁移城市: {city_data['name']} ({city_data['country']})")
                
                for attraction in city_data['attractions']:
                    self.migrate_attraction(attraction, f"ChinaCitiesDB-{city_key}")
                    total_migrated += 1
        
        logger.info(f"全球景点迁移完成: {total_migrated} 个景点")
    
    def validate_migration(self):
        """验证迁移结果"""
        logger.info("开始验证迁移结果...")
        
        try:
            cursor = self.conn.cursor()
            
            # 统计各表记录数
            validation_queries = {
                '景点总数': 'SELECT COUNT(*) FROM spot_attractions',
                '多语言内容总数': 'SELECT COUNT(*) FROM spot_attraction_contents',
                '媒体资源总数': 'SELECT COUNT(*) FROM spot_attraction_media',
                '国家数量': 'SELECT COUNT(DISTINCT country) FROM spot_attractions',
                '城市数量': 'SELECT COUNT(DISTINCT city) FROM spot_attractions',
                '类别数量': 'SELECT COUNT(DISTINCT category) FROM spot_attractions'
            }
            
            validation_results = {}
            for metric, query in validation_queries.items():
                cursor.execute(query)
                count = cursor.fetchone()[0]
                validation_results[metric] = count
                logger.info(f"✅ {metric}: {count}")
            
            # 按国家统计
            cursor.execute("""
                SELECT country, COUNT(*) 
                FROM spot_attractions 
                GROUP BY country 
                ORDER BY COUNT(*) DESC
            """)
            
            country_stats = cursor.fetchall()
            logger.info("按国家统计:")
            for country, count in country_stats:
                logger.info(f"  - {country}: {count} 个景点")
            
            # 按类别统计
            cursor.execute("""
                SELECT category, COUNT(*) 
                FROM spot_attractions 
                GROUP BY category 
                ORDER BY COUNT(*) DESC
            """)
            
            category_stats = cursor.fetchall()
            logger.info("按类别统计:")
            for category, count in category_stats:
                logger.info(f"  - {category}: {count} 个景点")
            
            cursor.close()
            
            # 保存验证结果
            self.migration_stats['validation_results'] = validation_results
            self.migration_stats['country_stats'] = dict(country_stats)
            self.migration_stats['category_stats'] = dict(category_stats)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"验证迁移结果失败: {e}")
            return None
    
    def generate_migration_report(self):
        """生成迁移报告"""
        report = {
            'migration_timestamp': datetime.now().isoformat(),
            'migration_summary': {
                'attractions_migrated': self.migration_stats['attractions_migrated'],
                'contents_migrated': self.migration_stats['contents_migrated'],
                'media_migrated': self.migration_stats['media_migrated'],
                'errors_count': len(self.migration_stats['errors'])
            },
            'validation_results': self.migration_stats.get('validation_results', {}),
            'country_statistics': self.migration_stats.get('country_stats', {}),
            'category_statistics': self.migration_stats.get('category_stats', {}),
            'errors': self.migration_stats['errors']
        }
        
        # 保存报告到文件
        report_file = f"/workspace/migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"迁移报告已保存到: {report_file}")
        return report
    
    def run_migration(self):
        """执行完整的数据迁移流程"""
        logger.info("🚀 开始历史数据迁移...")
        
        # 连接数据库
        if not self.connect_database():
            logger.error("数据库连接失败，终止迁移")
            return False
        
        try:
            # 迁移本地景点数据
            self.migrate_local_attractions()
            
            # 迁移全球景点数据
            self.migrate_global_attractions()
            
            # 验证迁移结果
            self.validate_migration()
            
            # 生成迁移报告
            report = self.generate_migration_report()
            
            logger.info("🎉 数据迁移完成！")
            logger.info(f"总计迁移景点: {self.migration_stats['attractions_migrated']} 个")
            logger.info(f"总计迁移内容: {self.migration_stats['contents_migrated']} 条")
            logger.info(f"总计迁移媒体: {self.migration_stats['media_migrated']} 个")
            
            if self.migration_stats['errors']:
                logger.warning(f"迁移过程中发生 {len(self.migration_stats['errors'])} 个错误")
                for error in self.migration_stats['errors']:
                    logger.warning(f"  - {error}")
            
            return True
            
        except Exception as e:
            logger.error(f"迁移过程中发生严重错误: {e}")
            return False
        
        finally:
            if self.conn:
                self.conn.close()
                logger.info("数据库连接已关闭")

def main():
    """主函数"""
    migrator = HistoricalDataMigrator()
    success = migrator.run_migration()
    
    if success:
        logger.info("✅ 迁移任务成功完成")
        sys.exit(0)
    else:
        logger.error("❌ 迁移任务失败")
        sys.exit(1)

if __name__ == "__main__":
    main()