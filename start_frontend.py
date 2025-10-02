#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端启动脚本
自动安装依赖并启动Vue3前端开发服务器
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(command, cwd=None, shell=True):
    """运行命令并实时输出"""
    try:
        process = subprocess.Popen(
            command,
            shell=shell,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 实时输出
        for line in process.stdout:
            print(line.rstrip())
        
        process.wait()
        return process.returncode == 0
        
    except Exception as e:
        print(f"❌ 命令执行失败: {e}")
        return False


def check_node():
    """检查Node.js是否安装"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Node.js 已安装: {version}")
            return True
        else:
            print("❌ Node.js 未安装")
            return False
    except FileNotFoundError:
        print("❌ Node.js 未安装")
        return False


def check_npm():
    """检查npm是否安装"""
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ npm 已安装: {version}")
            return True
        else:
            print("❌ npm 未安装")
            return False
    except FileNotFoundError:
        print("❌ npm 未安装")
        return False


def install_dependencies():
    """安装前端依赖"""
    print("📦 安装前端依赖...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not frontend_dir.exists():
        print("❌ frontend 目录不存在")
        return False
    
    # 检查package.json是否存在
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print("❌ package.json 不存在")
        return False
    
    # 安装依赖
    print("正在安装依赖包...")
    success = run_command("npm install", cwd=frontend_dir)
    
    if success:
        print("✅ 依赖安装完成")
        return True
    else:
        print("❌ 依赖安装失败")
        return False


def start_dev_server():
    """启动开发服务器"""
    print("🚀 启动前端开发服务器...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    # 设置环境变量
    env = os.environ.copy()
    env['VITE_API_BASE_URL'] = 'http://localhost:8000/api'
    
    print("📖 前端地址: http://localhost:3000")
    print("🔗 API地址: http://localhost:8000/api")
    print("📚 API文档: http://localhost:8000/api/docs")
    print("\n按 Ctrl+C 停止服务器\n")
    
    # 启动开发服务器
    try:
        subprocess.run(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            env=env,
            check=True
        )
    except KeyboardInterrupt:
        print("\n👋 前端服务器已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        return False
    
    return True


def main():
    """主函数"""
    print("🎨 智能装配说明书生成系统 - 前端启动器")
    print("=" * 60)
    
    # 检查Node.js环境
    if not check_node():
        print("\n请先安装Node.js:")
        print("🌐 下载地址: https://nodejs.org/")
        return 1
    
    if not check_npm():
        print("\n请先安装npm")
        return 1
    
    # 检查是否需要安装依赖
    frontend_dir = Path(__file__).parent / "frontend"
    node_modules = frontend_dir / "node_modules"
    
    if not node_modules.exists():
        print("\n📦 首次运行，需要安装依赖...")
        if not install_dependencies():
            return 1
    else:
        print("✅ 依赖已安装")
    
    # 启动开发服务器
    print("\n" + "=" * 60)
    if not start_dev_server():
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
