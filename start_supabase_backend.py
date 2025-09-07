#!/usr/bin/env python3
"""
启动支持Supabase的后端服务
Start Backend Service with Supabase Support
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

def check_environment():
    """检查环境配置"""
    print("🔧 检查环境配置...")
    
    # 检查.env文件
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️ .env文件不存在，使用.env.example创建...")
        if Path(".env.example").exists():
            subprocess.run(["cp", ".env.example", ".env"])
            print("✅ 已从.env.example复制.env文件")
            print("请编辑.env文件设置正确的Supabase配置")
        else:
            print("❌ 缺少.env.example文件")
            return False
    
    # 检查Python依赖
    try:
        import supabase
        import fastapi
        import uvicorn
        print("✅ Python依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少Python依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def start_backend():
    """启动后端服务"""
    print("\n🚀 启动后端服务...")
    
    # 切换到backend目录
    backend_dir = Path("backend")
    if backend_dir.exists():
        os.chdir(backend_dir)
    
    # 启动FastAPI服务
    try:
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8001", 
            "--reload",
            "--log-level", "info"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        print("🌐 后端服务将在 http://localhost:8001 启动")
        print("📊 API文档: http://localhost:8001/docs")
        print("🧪 Supabase测试: http://localhost:3000/test_supabase_api.html")
        print("\n按 Ctrl+C 停止服务\n")
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def show_usage():
    """显示使用说明"""
    print("""
🌟 Supabase后端服务启动器

使用方法:
  python start_supabase_backend.py

服务端点:
  - 健康检查: GET /api/spot/health
  - 附近景点: GET /api/spot/attractions/nearby
  - 所有景点: GET /api/spot/attractions  
  - 按类别查询: GET /api/spot/attractions/category/{category}
  - 按城市查询: GET /api/spot/attractions/city/{city}
  - 搜索景点: GET /api/spot/attractions/search
  - 探索接口: POST /api/explore-supabase
  - 统计信息: GET /api/spot/statistics

测试页面:
  - 打开浏览器访问: http://localhost:3000/test_supabase_api.html
  - 或直接访问: http://localhost:8001/docs (FastAPI文档)

环境配置:
  - 确保.env文件包含正确的Supabase配置
  - 数据库已按照docs/spots/db/中的文档设置
""")

def main():
    """主函数"""
    print("🗄️ Spot地图相册系统 - Supabase后端服务")
    print("="*60)
    
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        show_usage()
        return
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，请修复后重试")
        return
    
    # 显示使用说明
    show_usage()
    
    # 启动服务
    start_backend()

if __name__ == "__main__":
    main()