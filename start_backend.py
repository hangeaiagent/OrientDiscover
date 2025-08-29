#!/usr/bin/env python3
"""
方向探索派对后端服务启动脚本
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        sys.exit(1)
    print(f"✓ Python版本: {sys.version}")

def install_dependencies():
    """安装依赖包"""
    print("正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ 依赖包安装完成")
    except subprocess.CalledProcessError as e:
        print(f"错误: 依赖包安装失败 - {e}")
        sys.exit(1)

def start_server():
    """启动服务器"""
    print("正在启动后端服务...")
    print("服务地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    print("按 Ctrl+C 停止服务")
    print("-" * 50)
    
    try:
        # 切换到backend目录
        os.chdir("backend")
        subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"错误: 服务启动失败 - {e}")
        sys.exit(1)

def main():
    """主函数"""
    print("🧭 方向探索派对 - 后端服务启动器")
    print("=" * 50)
    
    # 检查Python版本
    check_python_version()
    
    # 检查requirements.txt是否存在
    if not Path("requirements.txt").exists():
        print("错误: 找不到requirements.txt文件")
        sys.exit(1)
    
    # 安装依赖
    install_dependencies()
    
    # 启动服务器
    start_server()

if __name__ == "__main__":
    main()