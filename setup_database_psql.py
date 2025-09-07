#!/usr/bin/env python3
"""
PostgreSQL数据库设置脚本 - 直连版本
Direct PostgreSQL database setup script for map albums structure
"""

import psycopg2
import logging
import sys
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Supabase数据库连接信息
SUPABASE_URL = "https://uobwbhvwrciaxloqdizc.supabase.co"
DATABASE_URL = "postgresql://postgres:JjcUcOgvzPb7cHMH@db.uobwbhvwrciaxloqdizc.supabase.co:5432/postgres"

def create_connection():
    """创建数据库连接"""
    try:
        # 解析数据库URL
        parsed = urlparse(DATABASE_URL)
        
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # 去掉开头的'/'
            user=parsed.username,
            password=parsed.password
        )
        logger.info("数据库连接成功")
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        sys.exit(1)

def read_sql_file(file_path: str) -> str:
    """读取SQL文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"SQL文件未找到: {file_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"读取SQL文件失败: {e}")
        sys.exit(1)

def execute_sql_statements(conn, sql_content: str) -> bool:
    """执行SQL语句"""
    try:
        cursor = conn.cursor()
        
        # 分割SQL语句，更智能的分割方式
        statements = []
        current_statement = ""
        in_function = False
        
        lines = sql_content.split('\n')
        for line in lines:
            stripped_line = line.strip()
            
            # 跳过注释和空行
            if not stripped_line or stripped_line.startswith('--'):
                continue
            
            current_statement += line + '\n'
            
            # 检查是否在函数定义中
            if 'CREATE OR REPLACE FUNCTION' in line.upper() or 'CREATE FUNCTION' in line.upper():
                in_function = True
            elif in_function and line.strip().endswith("$$ language 'plpgsql';"):
                in_function = False
                statements.append(current_statement.strip())
                current_statement = ""
            elif not in_function and line.strip().endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
        
        # 添加最后一个语句（如果有的话）
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        success_count = 0
        total_count = len(statements)
        
        for i, statement in enumerate(statements, 1):
            if not statement.strip():
                continue
                
            try:
                logger.info(f"执行SQL语句 {i}/{total_count}: {statement[:100].replace(chr(10), ' ')}...")
                cursor.execute(statement)
                conn.commit()
                success_count += 1
                logger.info(f"✅ SQL语句执行成功 ({success_count}/{total_count})")
                
            except Exception as e:
                logger.warning(f"⚠️ SQL语句执行失败: {str(e)[:200]}")
                conn.rollback()
                # 继续执行其他语句
                continue
        
        cursor.close()
        logger.info(f"SQL执行完成: {success_count}/{total_count} 条语句成功执行")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"执行SQL语句时发生错误: {e}")
        return False

def verify_tables_created(conn) -> bool:
    """验证表是否创建成功"""
    expected_tables = [
        'map_albums',
        'attractions', 
        'attraction_contents',
        'attraction_media',
        'album_attractions',
        'attraction_embeddings',
        'user_behaviors'
    ]
    
    try:
        cursor = conn.cursor()
        
        for table_name in expected_tables:
            try:
                cursor.execute(f"SELECT 1 FROM {table_name} LIMIT 1;")
                logger.info(f"✅ 表 '{table_name}' 验证成功")
            except Exception as e:
                logger.error(f"❌ 表 '{table_name}' 验证失败: {e}")
                conn.rollback()
                return False
        
        cursor.close()
        logger.info("🎉 所有表验证成功！")
        return True
        
    except Exception as e:
        logger.error(f"验证表时发生错误: {e}")
        return False

def create_users_table_if_not_exists(conn) -> bool:
    """如果users表不存在则创建（用于外键引用）"""
    try:
        cursor = conn.cursor()
        
        # 检查users表是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        
        exists = cursor.fetchone()[0]
        
        if exists:
            logger.info("users表已存在")
            cursor.close()
            return True
        else:
            # users表不存在，创建基本的users表
            logger.info("创建users表...")
            users_sql = """
            CREATE TABLE users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now()
            );
            """
            cursor.execute(users_sql)
            conn.commit()
            cursor.close()
            logger.info("✅ users表创建成功")
            return True
            
    except Exception as e:
        logger.error(f"创建users表失败: {e}")
        conn.rollback()
        return False

def main():
    """主函数"""
    logger.info("🚀 开始设置PostgreSQL数据库...")
    
    # 创建数据库连接
    conn = create_connection()
    
    try:
        # 创建users表（如果不存在）
        if not create_users_table_if_not_exists(conn):
            logger.error("创建users表失败，终止执行")
            sys.exit(1)
        
        # 读取SQL文件
        sql_file_path = "/workspace/database_setup.sql"
        sql_content = read_sql_file(sql_file_path)
        logger.info(f"✅ 成功读取SQL文件: {sql_file_path}")
        
        # 执行SQL语句
        if execute_sql_statements(conn, sql_content):
            logger.info("✅ SQL语句执行完成")
        else:
            logger.error("❌ SQL语句执行失败")
            sys.exit(1)
        
        # 验证表创建
        if verify_tables_created(conn):
            logger.info("🎉 数据库设置完成！所有表创建成功。")
        else:
            logger.error("❌ 数据库设置失败，部分表创建不成功。")
            sys.exit(1)
            
    finally:
        conn.close()
        logger.info("数据库连接已关闭")

if __name__ == "__main__":
    main()