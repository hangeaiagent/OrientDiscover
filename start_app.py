#!/usr/bin/env python3
"""
方向探索派对应用一键启动脚本
"""

import subprocess
import sys
import time
import threading
import webbrowser
from pathlib import Path

def check_requirements():
    """检查必要文件和环境"""
    print("🔍 检查环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        return False
    
    # 检查必要文件
    required_files = [
        'index.html', 'styles.css', 'app.js',
        'backend/main.py', 'requirements.txt'
    ]
    
    missing_files = [f for f in required_files if not Path(f).exists()]
    if missing_files:
        print(f"❌ 错误: 缺少必要文件: {', '.join(missing_files)}")
        return False
    
    print("✅ 环境检查通过")
    return True

def setup_environment():
    """设置虚拟环境和依赖"""
    print("🛠️  设置环境...")
    
    # 创建虚拟环境（如果不存在）
    if not Path("venv").exists():
        print("   创建虚拟环境...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    
    # 安装依赖
    print("   安装依赖包...")
    if sys.platform == "win32":
        pip_path = "venv/Scripts/pip"
        python_path = "venv/Scripts/python"
    else:
        pip_path = "venv/bin/pip"
        python_path = "venv/bin/python"
    
    subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
    subprocess.run([pip_path, "install", "requests"], check=True)
    
    print("✅ 环境设置完成")
    return python_path

def start_backend(python_path):
    """启动后端服务"""
    print("🚀 启动后端服务...")
    
    def run_backend():
        subprocess.run([
            python_path, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ], cwd="backend")
    
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # 等待后端启动
    print("   等待后端服务启动...")
    time.sleep(3)
    
    # 检查后端是否启动成功
    try:
        import requests
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务启动成功")
            return True
        else:
            print("❌ 后端服务启动失败")
            return False
    except Exception as e:
        print(f"❌ 后端服务连接失败: {e}")
        return False

def start_frontend():
    """启动前端服务"""
    print("🌐 启动前端服务...")
    
    def run_frontend():
        import http.server
        import socketserver
        
        class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def end_headers(self):
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                super().end_headers()
        
        with socketserver.TCPServer(("", 3000), CustomHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    
    frontend_thread = threading.Thread(target=run_frontend, daemon=True)
    frontend_thread.start()
    
    time.sleep(2)
    print("✅ 前端服务启动成功")

def open_browser():
    """打开浏览器"""
    print("🌍 打开浏览器...")
    time.sleep(1)
    webbrowser.open('http://localhost:3000')

def main():
    """主函数"""
    print("🧭 方向探索派对智能工具")
    print("=" * 60)
    print("一款集娱乐、教育和社交于一体的方向探索工具")
    print("=" * 60)
    
    try:
        # 检查环境
        if not check_requirements():
            sys.exit(1)
        
        # 设置环境
        python_path = setup_environment()
        
        # 启动后端
        if not start_backend(python_path):
            sys.exit(1)
        
        # 启动前端
        start_frontend()
        
        # 打开浏览器
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        print("\n" + "🎉" * 20)
        print("应用启动成功！")
        print("🌐 前端地址: http://localhost:3000")
        print("🔧 后端API: http://localhost:8000")
        print("📚 API文档: http://localhost:8000/docs")
        print("🎉" * 20)
        print("\n使用说明:")
        print("1. 在移动设备上打开前端地址")
        print("2. 授权地理位置和设备方向权限")
        print("3. 面向想要探索的方向")
        print("4. 点击'开始探索'按钮")
        print("5. 浏览生成的地点卡片")
        print("\n按 Ctrl+C 停止服务")
        print("-" * 60)
        
        # 保持主线程运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 应用已停止，感谢使用！")
            
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()