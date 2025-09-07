#!/usr/bin/env python3
"""
CAMEL多智能体旅游导航系统启动脚本

启动完整的系统，包括后端API服务和前端界面
"""

import os
import sys
import subprocess
import time
import requests
import webbrowser
from pathlib import Path

def check_dependencies():
    """检查依赖项"""
    print("检查依赖项...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'openai', 'supabase', 
        'python-dotenv', 'aiohttp', 'pillow'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 依赖项检查通过")
    return True


def check_environment():
    """检查环境变量"""
    print("检查环境变量...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'OPENAI_API_KEY',
        'SUPABASE_URL', 
        'SUPABASE_ANON_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 缺少环境变量: {', '.join(missing_vars)}")
        print("请检查.env文件配置")
        return False
    
    print("✅ 环境变量检查通过")
    return True


def start_backend():
    """启动后端服务"""
    print("启动后端服务...")
    
    backend_script = Path(__file__).parent / "backend" / "main.py"
    
    if not backend_script.exists():
        print(f"❌ 后端脚本不存在: {backend_script}")
        return None
    
    try:
        # 启动后端进程
        process = subprocess.Popen([
            sys.executable, str(backend_script)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服务启动
        print("等待后端服务启动...")
        for i in range(30):  # 最多等待30秒
            try:
                response = requests.get("http://localhost:8001/api/health", timeout=2)
                if response.status_code == 200:
                    print("✅ 后端服务启动成功")
                    return process
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
            print(f"等待中... ({i+1}/30)")
        
        print("❌ 后端服务启动超时")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ 启动后端服务失败: {e}")
        return None


def check_backend_health():
    """检查后端服务健康状态"""
    print("检查后端服务健康状态...")
    
    try:
        # 检查基础API
        response = requests.get("http://localhost:8001/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ 基础API不健康")
            return False
        
        # 检查CAMEL系统
        response = requests.get("http://localhost:8001/api/camel-health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                health_data = result.get('data', {})
                overall_status = health_data.get('overall', 'unknown')
                print(f"✅ CAMEL系统状态: {overall_status}")
                
                # 显示各组件状态
                agents = health_data.get('agents', {})
                print("智能体状态:")
                for agent_name, status in agents.items():
                    print(f"  - {agent_name}: {status}")
                
                return overall_status in ['healthy', 'degraded']
            else:
                print(f"❌ CAMEL系统异常: {result.get('error', '未知错误')}")
                return False
        else:
            print("❌ CAMEL健康检查失败")
            return False
        
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False


def open_web_interface():
    """打开Web界面"""
    print("打开Web界面...")
    
    # 检查HTML文件是否存在
    html_files = [
        Path(__file__).parent / "album_generator.html",
        Path(__file__).parent / "index.html"
    ]
    
    for html_file in html_files:
        if html_file.exists():
            try:
                # 在浏览器中打开
                webbrowser.open(f"file://{html_file.absolute()}")
                print(f"✅ 已在浏览器中打开: {html_file.name}")
                return True
            except Exception as e:
                print(f"❌ 打开浏览器失败: {e}")
    
    print("❌ 找不到Web界面文件")
    return False


def run_quick_test():
    """运行快速测试"""
    print("运行快速功能测试...")
    
    try:
        # 测试相册生成API
        test_data = {
            "user_prompt": "我想去北京看故宫",
            "user_id": "test_user",
            "language": "zh-CN"
        }
        
        response = requests.post(
            "http://localhost:8001/api/generate-album", 
            json=test_data, 
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                album = result.get('album', {})
                print(f"✅ 相册生成测试成功")
                print(f"   标题: {album.get('title', '未知')}")
                print(f"   景点数: {len(album.get('attractions', []))}")
                return True
            else:
                print(f"❌ 相册生成失败: {result.get('error', '未知错误')}")
                return False
        else:
            print(f"❌ API调用失败: HTTP {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ 快速测试失败: {e}")
        return False


def print_usage_info():
    """打印使用说明"""
    print("\n" + "="*60)
    print("🎉 CAMEL多智能体旅游导航系统已启动！")
    print("="*60)
    print()
    print("📋 使用说明:")
    print("1. Web界面已在浏览器中打开")
    print("2. 在输入框中描述你的旅行想法")
    print("3. 点击'生成旅游相册'按钮")
    print("4. AI将为你规划完美的旅行行程")
    print()
    print("🔗 可用端点:")
    print("- 后端API: http://localhost:8001")
    print("- 健康检查: http://localhost:8001/api/health")
    print("- CAMEL健康: http://localhost:8001/api/camel-health")
    print("- 相册生成: http://localhost:8001/api/generate-album")
    print()
    print("📖 API文档: http://localhost:8001/docs")
    print()
    print("⚠️  注意: 按Ctrl+C停止服务")
    print("="*60)


def main():
    """主函数"""
    print("CAMEL多智能体旅游导航系统启动器")
    print("="*60)
    
    # 检查依赖项
    if not check_dependencies():
        return 1
    
    # 检查环境变量
    if not check_environment():
        return 1
    
    # 启动后端服务
    backend_process = start_backend()
    if not backend_process:
        return 1
    
    try:
        # 检查健康状态
        if not check_backend_health():
            print("⚠️  系统健康检查失败，但继续运行...")
        
        # 运行快速测试
        if run_quick_test():
            print("✅ 系统功能测试通过")
        else:
            print("⚠️  功能测试失败，但系统仍可使用")
        
        # 打开Web界面
        open_web_interface()
        
        # 打印使用说明
        print_usage_info()
        
        # 保持运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在停止服务...")
            backend_process.terminate()
            backend_process.wait()
            print("✅ 服务已停止")
            return 0
    
    except Exception as e:
        print(f"❌ 系统运行异常: {e}")
        if backend_process:
            backend_process.terminate()
        return 1


if __name__ == "__main__":
    sys.exit(main())