#!/usr/bin/env python3
"""
智能装配说明书生成系统 - 一键启动脚本

使用方法：
python start.py

功能：
- 自动启动后端API服务 (端口8000)
- 自动启动前端开发服务器 (端口3000)
- 检查依赖和环境
- 提供系统状态监控
"""

import os
import sys
import time
import subprocess
import threading
import webbrowser
from pathlib import Path

def print_banner():
    """打印系统横幅"""
    print("=" * 60)
    print("🏭 智能装配说明书生成系统")
    print("📋 双通道架构版本 - 让普通工人看完说明书也能进行加工")
    print("=" * 60)

def check_dependencies():
    """检查依赖"""
    print("🔍 检查系统依赖...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False
    
    print(f"✅ Python版本: {sys.version.split()[0]}")
    
    # 检查必要的包
    required_packages = ['fastapi', 'uvicorn', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: 已安装")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}: 未安装")
    
    if missing_packages:
        print(f"⚠️ 缺少依赖包: {', '.join(missing_packages)}")
        print("💡 请运行: pip install -r requirements.txt")
        return False
    
    # 检查前端依赖
    frontend_path = Path("frontend")
    if not (frontend_path / "node_modules").exists():
        print("⚠️ 前端依赖未安装")
        print("💡 请运行: cd frontend && npm install")
        return False
    
    print("✅ 前端依赖: 已安装")
    return True

def check_environment():
    """检查环境变量"""
    print("🔧 检查环境配置...")
    
    api_keys = {
        'DEEPSEEK_API_KEY': 'sk-ea98b5da86954ddcaa2ff10e5bbba2b4',
        'DASHSCOPE_API_KEY': 'sk-a2e7b59004734cd7b06dd246bc72c30b'
    }
    
    for key, default_value in api_keys.items():
        if not os.getenv(key):
            os.environ[key] = default_value
            print(f"✅ {key}: 已设置默认值")
        else:
            print(f"✅ {key}: 已配置")
    
    return True

def start_backend():
    """启动后端服务"""
    print("🚀 启动后端API服务...")
    
    try:
        # 启动后端
        backend_process = subprocess.Popen(
            [sys.executable, "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 等待服务启动
        print("⏳ 等待后端服务启动...")
        time.sleep(5)
        
        # 检查服务状态
        import requests
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ 后端API服务启动成功")
                print("📍 后端地址: http://localhost:8000")
                print("📚 API文档: http://localhost:8000/docs")
                return backend_process
            else:
                print("❌ 后端服务启动失败")
                return None
        except requests.exceptions.RequestException:
            print("❌ 无法连接到后端服务")
            return None
            
    except Exception as e:
        print(f"❌ 启动后端服务失败: {e}")
        return None

def start_frontend():
    """启动前端服务"""
    print("🎨 启动前端开发服务器...")
    
    try:
        # 检查是否已经在运行
        import requests
        try:
            response = requests.get("http://localhost:3000", timeout=2)
            print("✅ 前端服务已在运行")
            print("📍 前端地址: http://localhost:3000")
            return None
        except requests.exceptions.RequestException:
            pass
        
        # 启动前端
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd="frontend",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 等待服务启动
        print("⏳ 等待前端服务启动...")
        time.sleep(8)
        
        # 检查服务状态
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                print("✅ 前端开发服务器启动成功")
                print("📍 前端地址: http://localhost:3000")
                return frontend_process
            else:
                print("❌ 前端服务启动失败")
                return None
        except requests.exceptions.RequestException:
            print("❌ 无法连接到前端服务")
            return None
            
    except Exception as e:
        print(f"❌ 启动前端服务失败: {e}")
        return None

def open_browser():
    """打开浏览器"""
    print("🌐 打开浏览器...")
    time.sleep(2)
    try:
        webbrowser.open("http://localhost:3000")
        print("✅ 浏览器已打开")
    except Exception as e:
        print(f"⚠️ 无法自动打开浏览器: {e}")
        print("💡 请手动访问: http://localhost:3000")

def monitor_services(backend_process, frontend_process):
    """监控服务状态"""
    print("\n" + "=" * 60)
    print("🎯 系统运行中...")
    print("📍 访问地址:")
    print("  - 前端界面: http://localhost:3000")
    print("  - 后端API: http://localhost:8000")
    print("  - API文档: http://localhost:8000/docs")
    print("\n💡 按 Ctrl+C 停止所有服务")
    print("=" * 60)
    
    try:
        while True:
            time.sleep(5)
            
            # 检查进程状态
            if backend_process and backend_process.poll() is not None:
                print("❌ 后端服务已停止")
                break
                
            if frontend_process and frontend_process.poll() is not None:
                print("❌ 前端服务已停止")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务...")
        
        if backend_process:
            backend_process.terminate()
            print("✅ 后端服务已停止")
            
        if frontend_process:
            frontend_process.terminate()
            print("✅ 前端服务已停止")
            
        print("👋 系统已关闭")

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请先安装必要的依赖")
        return
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败")
        return
    
    print("\n🚀 开始启动系统...")
    
    # 启动后端
    backend_process = start_backend()
    if not backend_process:
        print("\n❌ 后端启动失败，无法继续")
        return
    
    # 启动前端
    frontend_process = start_frontend()
    
    # 打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()
    
    # 监控服务
    monitor_services(backend_process, frontend_process)

if __name__ == "__main__":
    main()
