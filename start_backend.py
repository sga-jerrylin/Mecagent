#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端启动脚本
检查环境并启动FastAPI后端服务
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python版本过低: {version.major}.{version.minor}")
        print("需要Python 3.8或更高版本")
        return False
    
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """检查Python依赖"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'openai',
        'PyMuPDF',
        'Jinja2',
        'Pillow'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True


def check_api_keys():
    """检查API密钥"""
    required_keys = {
        'DASHSCOPE_API_KEY': 'DashScope API密钥 (Qwen3-VL)',
        'DEEPSEEK_API_KEY': 'DeepSeek API密钥'
    }
    
    missing_keys = []
    
    for key, description in required_keys.items():
        value = os.getenv(key)
        if value:
            print(f"✅ {description}: {value[:10]}...")
        else:
            missing_keys.append(f"{key} ({description})")
            print(f"❌ {description}")
    
    if missing_keys:
        print(f"\n缺少环境变量:")
        for key in missing_keys:
            print(f"  - {key}")
        print("\n请设置环境变量:")
        print("export DASHSCOPE_API_KEY='your_dashscope_key'")
        print("export DEEPSEEK_API_KEY='your_deepseek_key'")
        return False
    
    return True


def check_blender():
    """检查Blender"""
    blender_exe = os.getenv('BLENDER_EXE', 'blender')
    
    try:
        result = subprocess.run(
            [blender_exe, '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ Blender: {version_line}")
            return True
        else:
            print("❌ Blender 未正确安装")
            return False
            
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("❌ Blender 未找到")
        print("请安装Blender或设置BLENDER_EXE环境变量")
        return False


def create_directories():
    """创建必要的目录"""
    directories = [
        'uploads',
        'output',
        'static',
        'logs',
        '.cache'
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(exist_ok=True)
        print(f"📁 {directory}/")
    
    return True


def start_server():
    """启动FastAPI服务器"""
    print("🚀 启动后端API服务器...")
    
    # 检查backend目录
    backend_dir = Path(__file__).parent / "backend"
    if not backend_dir.exists():
        print("❌ backend 目录不存在")
        return False
    
    app_file = backend_dir / "app.py"
    if not app_file.exists():
        print("❌ backend/app.py 不存在")
        return False
    
    print("📖 API服务: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/api/docs")
    print("🔧 管理界面: http://localhost:8000/api/redoc")
    print("\n按 Ctrl+C 停止服务器\n")
    
    # 启动服务器
    try:
        os.chdir(backend_dir)
        subprocess.run([
            sys.executable, "app.py"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 后端服务器已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        return False
    
    return True


def main():
    """主函数"""
    print("🤖 智能装配说明书生成系统 - 后端启动器")
    print("=" * 60)
    
    # 检查Python版本
    if not check_python_version():
        return 1
    
    print("\n📦 检查依赖包...")
    if not check_dependencies():
        return 1
    
    print("\n🔑 检查API密钥...")
    if not check_api_keys():
        return 1
    
    print("\n🎯 检查Blender...")
    blender_ok = check_blender()
    if not blender_ok:
        print("⚠️ Blender未安装，3D模型处理功能将不可用")
        response = input("是否继续启动? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            return 1
    
    print("\n📁 创建目录...")
    create_directories()
    
    # 启动服务器
    print("\n" + "=" * 60)
    if not start_server():
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
