#!/usr/bin/env python3
"""
Supabase REST API数据库设置脚本
Setup script for Supabase database using REST API
"""

import requests
import json
import logging
import sys

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Supabase配置
SUPABASE_URL = "https://uobwbhvwrciaxloqdizc.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVvYndiaHZ3cmNpYXhsb3FkaXpjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzA3MTI2NiwiZXhwIjoyMDYyNjQ3MjY2fQ.ryRmf_i-EYRweVLL4fj4acwifoknqgTbIomL-S22Zmo"

def execute_sql_via_api(sql_statement: str) -> bool:
    """通过Supabase REST API执行SQL语句"""
    try:
        headers = {
            'apikey': SUPABASE_SERVICE_ROLE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # 使用rpc端点执行SQL
        url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
        payload = {
            "sql_statement": sql_statement
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            logger.info(f"✅ SQL执行成功")
            return True
        else:
            logger.error(f"❌ SQL执行失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"API调用失败: {e}")
        return False

def create_tables_step_by_step():
    """逐步创建表结构"""
    
    # 1. 创建users表（如果不存在）
    logger.info("1. 创建users表...")
    users_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMPTZ DEFAULT now(),
        updated_at TIMESTAMPTZ DEFAULT now()
    );
    """
    
    # 2. 创建map_albums表
    logger.info("2. 创建map_albums表...")
    map_albums_sql = """
    CREATE TABLE IF NOT EXISTS map_albums (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        creator_id UUID REFERENCES users(id) ON DELETE CASCADE,
        creator_type TEXT CHECK (creator_type IN ('system_admin', 'user_self')) DEFAULT 'user_self',
        title TEXT NOT NULL,
        description TEXT,
        cover_image TEXT,
        access_level TEXT CHECK (access_level IN ('private', 'public')) DEFAULT 'public',
        tags TEXT[] DEFAULT '{}',
        view_count INTEGER DEFAULT 0,
        like_count INTEGER DEFAULT 0,
        is_recommended BOOLEAN DEFAULT false,
        created_at TIMESTAMPTZ DEFAULT now(),
        updated_at TIMESTAMPTZ DEFAULT now()
    );
    """
    
    # 3. 创建attractions表
    logger.info("3. 创建attractions表...")
    attractions_sql = """
    CREATE TABLE IF NOT EXISTS attractions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL,
        location GEOMETRY(Point, 4326),
        category TEXT NOT NULL,
        country TEXT NOT NULL,
        city TEXT NOT NULL,
        address TEXT,
        opening_hours TEXT,
        ticket_price TEXT,
        booking_method TEXT,
        main_image_url TEXT,
        video_url TEXT,
        created_at TIMESTAMPTZ DEFAULT now(),
        updated_at TIMESTAMPTZ DEFAULT now()
    );
    """
    
    # 4. 创建attraction_contents表
    logger.info("4. 创建attraction_contents表...")
    attraction_contents_sql = """
    CREATE TABLE IF NOT EXISTS attraction_contents (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        attraction_id UUID REFERENCES attractions(id) ON DELETE CASCADE,
        language_code TEXT NOT NULL,
        name_translated TEXT,
        description TEXT,
        attraction_introduction TEXT,
        guide_commentary TEXT,
        created_at TIMESTAMPTZ DEFAULT now(),
        UNIQUE(attraction_id, language_code)
    );
    """
    
    # 5. 创建attraction_media表
    logger.info("5. 创建attraction_media表...")
    attraction_media_sql = """
    CREATE TABLE IF NOT EXISTS attraction_media (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        attraction_id UUID REFERENCES attractions(id) ON DELETE CASCADE,
        media_type TEXT CHECK (media_type IN ('image', 'video', 'audio')) NOT NULL,
        url TEXT NOT NULL,
        caption TEXT,
        is_primary BOOLEAN DEFAULT false,
        order_index INTEGER DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT now()
    );
    """
    
    # 6. 创建album_attractions表
    logger.info("6. 创建album_attractions表...")
    album_attractions_sql = """
    CREATE TABLE IF NOT EXISTS album_attractions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        album_id UUID REFERENCES map_albums(id) ON DELETE CASCADE,
        attraction_id UUID REFERENCES attractions(id) ON DELETE CASCADE,
        order_index INTEGER DEFAULT 0,
        custom_note TEXT,
        visit_duration INTEGER,
        created_at TIMESTAMPTZ DEFAULT now(),
        UNIQUE(album_id, attraction_id)
    );
    """
    
    # 7. 创建user_behaviors表
    logger.info("7. 创建user_behaviors表...")
    user_behaviors_sql = """
    CREATE TABLE IF NOT EXISTS user_behaviors (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        album_id UUID REFERENCES map_albums(id) ON DELETE CASCADE,
        action_type TEXT CHECK (action_type IN ('view', 'like', 'share', 'bookmark')) NOT NULL,
        created_at TIMESTAMPTZ DEFAULT now()
    );
    """
    
    # 执行所有SQL语句
    sql_statements = [
        ("users", users_sql),
        ("map_albums", map_albums_sql),
        ("attractions", attractions_sql),
        ("attraction_contents", attraction_contents_sql),
        ("attraction_media", attraction_media_sql),
        ("album_attractions", album_attractions_sql),
        ("user_behaviors", user_behaviors_sql)
    ]
    
    success_count = 0
    for table_name, sql in sql_statements:
        logger.info(f"创建表 {table_name}...")
        if execute_sql_via_api(sql):
            success_count += 1
            logger.info(f"✅ 表 {table_name} 创建成功")
        else:
            logger.error(f"❌ 表 {table_name} 创建失败")
    
    return success_count == len(sql_statements)

def create_indexes():
    """创建索引"""
    logger.info("创建数据库索引...")
    
    indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_map_albums_creator ON map_albums(creator_id);",
        "CREATE INDEX IF NOT EXISTS idx_map_albums_access_level ON map_albums(access_level);",
        "CREATE INDEX IF NOT EXISTS idx_attractions_category ON attractions(category);",
        "CREATE INDEX IF NOT EXISTS idx_attraction_contents_attraction ON attraction_contents(attraction_id);",
        "CREATE INDEX IF NOT EXISTS idx_album_attractions_album ON album_attractions(album_id);",
        "CREATE INDEX IF NOT EXISTS idx_user_behaviors_user ON user_behaviors(user_id);"
    ]
    
    success_count = 0
    for sql in indexes_sql:
        if execute_sql_via_api(sql):
            success_count += 1
    
    logger.info(f"索引创建完成: {success_count}/{len(indexes_sql)} 个索引创建成功")

def verify_tables():
    """验证表是否创建成功"""
    logger.info("验证表创建...")
    
    expected_tables = [
        'users', 'map_albums', 'attractions', 
        'attraction_contents', 'attraction_media',
        'album_attractions', 'user_behaviors'
    ]
    
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}'
    }
    
    success_count = 0
    for table_name in expected_tables:
        try:
            url = f"{SUPABASE_URL}/rest/v1/{table_name}?select=id&limit=1"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"✅ 表 '{table_name}' 验证成功")
                success_count += 1
            else:
                logger.error(f"❌ 表 '{table_name}' 验证失败: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ 表 '{table_name}' 验证失败: {e}")
    
    return success_count == len(expected_tables)

def main():
    """主函数"""
    logger.info("🚀 开始通过REST API设置Supabase数据库...")
    
    # 创建表
    if create_tables_step_by_step():
        logger.info("✅ 所有表创建成功")
    else:
        logger.error("❌ 部分表创建失败")
        sys.exit(1)
    
    # 创建索引
    create_indexes()
    
    # 验证表
    if verify_tables():
        logger.info("🎉 数据库设置完成！所有表验证成功。")
    else:
        logger.error("❌ 数据库验证失败。")
        sys.exit(1)

if __name__ == "__main__":
    main()