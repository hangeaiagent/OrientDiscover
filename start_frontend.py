#!/usr/bin/env python3
"""
方向探索派对前端服务启动脚本
"""

import http.server
import socketserver
import webbrowser
import threading
import time
import sys
from pathlib import Path

PORT = 3000

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器，添加CORS支持"""
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def start_server():
    """启动前端服务器"""
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"🧭 方向探索派对 - 前端服务")
            print("=" * 50)
            print(f"✓ 服务地址: http://localhost:{PORT}")
            print(f"✓ 在浏览器中打开应用...")
            print("按 Ctrl+C 停止服务")
            print("-" * 50)
            
            # 延迟打开浏览器
            def open_browser():
                time.sleep(1)
                webbrowser.open(f'http://localhost:{PORT}')
            
            threading.Thread(target=open_browser, daemon=True).start()
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n前端服务已停止")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"错误: 端口 {PORT} 已被占用，请尝试关闭其他服务或使用不同端口")
        else:
            print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 服务启动失败 - {e}")
        sys.exit(1)

def main():
    """主函数"""
    # 检查必要文件是否存在
    required_files = ['index.html', 'styles.css', 'app.js']
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print(f"错误: 缺少必要文件: {', '.join(missing_files)}")
        sys.exit(1)
    
    start_server()

if __name__ == "__main__":
    main()