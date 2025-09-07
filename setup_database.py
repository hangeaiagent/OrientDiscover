#!/usr/bin/env python3
"""
Supabase数据库设置脚本
Setup script for Supabase database with map albums structure
"""

import os
import sys
from supabase import create_client, Client
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Supabase配置
SUPABASE_URL = "https://uobwbhvwrciaxloqdizc.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVvYndiaHZ3cmNpYXhsb3FkaXpjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzA3MTI2NiwiZXhwIjoyMDYyNjQ3MjY2fQ.ryRmf_i-EYRweVLL4fj4acwifoknqgTbIomL-S22Zmo"

def create_supabase_client() -> Client:
    """创建Supabase客户端"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Supabase客户端创建成功")
        return supabase
    except Exception as e:
        logger.error(f"创建Supabase客户端失败: {e}")
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

def execute_sql_statements(supabase: Client, sql_content: str) -> bool:
    """执行SQL语句"""
    try:
        # 分割SQL语句（简单的分割方式）
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        success_count = 0
        total_count = len(statements)
        
        for i, statement in enumerate(statements, 1):
            try:
                # 跳过注释和空语句
                if statement.startswith('--') or statement.startswith('/*') or not statement:
                    continue
                
                logger.info(f"执行SQL语句 {i}/{total_count}: {statement[:50]}...")
                
                # 使用rpc调用执行SQL（对于DDL语句）
                result = supabase.rpc('exec_sql', {'sql_statement': statement}).execute()
                
                success_count += 1
                logger.info(f"SQL语句执行成功 ({success_count}/{total_count})")
                
            except Exception as e:
                logger.warning(f"SQL语句执行失败: {statement[:50]}... - 错误: {e}")
                # 继续执行其他语句
                continue
        
        logger.info(f"SQL执行完成: {success_count}/{total_count} 条语句成功执行")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"执行SQL语句时发生错误: {e}")
        return False

def verify_tables_created(supabase: Client) -> bool:
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
        for table_name in expected_tables:
            try:
                # 尝试查询表结构来验证表是否存在
                result = supabase.table(table_name).select("*").limit(1).execute()
                logger.info(f"表 '{table_name}' 验证成功")
            except Exception as e:
                logger.error(f"表 '{table_name}' 验证失败: {e}")
                return False
        
        logger.info("所有表验证成功！")
        return True
        
    except Exception as e:
        logger.error(f"验证表时发生错误: {e}")
        return False

def create_users_table_if_not_exists(supabase: Client) -> bool:
    """如果users表不存在则创建（用于外键引用）"""
    try:
        # 检查users表是否存在
        result = supabase.table('users').select("*").limit(1).execute()
        logger.info("users表已存在")
        return True
    except:
        # users表不存在，创建基本的users表
        logger.info("创建users表...")
        users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
        """
        try:
            supabase.rpc('exec_sql', {'sql_statement': users_sql}).execute()
            logger.info("users表创建成功")
            return True
        except Exception as e:
            logger.error(f"创建users表失败: {e}")
            return False

def main():
    """主函数"""
    logger.info("开始设置Supabase数据库...")
    
    # 创建Supabase客户端
    supabase = create_supabase_client()
    
    # 创建users表（如果不存在）
    if not create_users_table_if_not_exists(supabase):
        logger.error("创建users表失败，终止执行")
        sys.exit(1)
    
    # 读取SQL文件
    sql_file_path = "/workspace/database_setup.sql"
    sql_content = read_sql_file(sql_file_path)
    logger.info(f"成功读取SQL文件: {sql_file_path}")
    
    # 执行SQL语句
    if execute_sql_statements(supabase, sql_content):
        logger.info("SQL语句执行完成")
    else:
        logger.error("SQL语句执行失败")
        sys.exit(1)
    
    # 验证表创建
    if verify_tables_created(supabase):
        logger.info("✅ 数据库设置完成！所有表创建成功。")
    else:
        logger.error("❌ 数据库设置失败，部分表创建不成功。")
        sys.exit(1)

if __name__ == "__main__":
    main()