#!/usr/bin/env python3
"""
智能装配说明书生成系统 - 系统状态检查工具

功能：
- 检查所有核心组件状态
- 验证API接口可用性
- 测试前后端连接
- 生成系统健康报告
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)

def check_files_structure():
    """检查文件结构"""
    print_header("文件结构检查")
    
    required_files = {
        "app.py": "统一后端入口",
        "start.py": "一键启动脚本",
        "frontend/package.json": "前端项目配置",
        "core/dual_channel_parser.py": "双通道解析器",
        "models/fusion_expert.py": "DeepSeek融合专家",
        "models/vision_model.py": "Qwen3-VL视觉模型",
        "processors/file_processor.py": "文件处理器",
        "generators/html_generator.py": "HTML生成器"
    }
    
    missing_files = []
    
    for file_path, description in required_files.items():
        if Path(file_path).exists():
            print(f"✅ {file_path} - {description}")
        else:
            print(f"❌ {file_path} - {description} (缺失)")
            missing_files.append(file_path)
    
    required_dirs = ["static", "output", "uploads", "temp"]
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"✅ {dir_name}/ - 目录存在")
        else:
            print(f"⚠️ {dir_name}/ - 目录不存在 (将自动创建)")
    
    return len(missing_files) == 0

def check_python_environment():
    """检查Python环境"""
    print_header("Python环境检查")
    
    print(f"✅ Python版本: {sys.version.split()[0]}")
    print(f"✅ Python路径: {sys.executable}")
    
    required_packages = [
        "fastapi", "uvicorn", "requests", "pydantic",
        "openai", "dashscope", "PyPDF2", "camelot-py",
        "Pillow", "numpy", "pandas"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}: 已安装")
        except ImportError:
            print(f"❌ {package}: 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ 缺少依赖包: {', '.join(missing_packages)}")
        print("💡 请运行: pip install -r requirements.txt")
    
    return len(missing_packages) == 0

def check_api_keys():
    """检查API密钥"""
    print_header("API密钥检查")
    
    api_keys = {
        'DEEPSEEK_API_KEY': 'DeepSeek API密钥',
        'DASHSCOPE_API_KEY': 'DashScope API密钥'
    }
    
    all_keys_present = True
    
    for key, description in api_keys.items():
        value = os.getenv(key)
        if value:
            masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"✅ {key}: {masked_value} - {description}")
        else:
            print(f"❌ {key}: 未设置 - {description}")
            all_keys_present = False
    
    return all_keys_present

def check_backend_service():
    """检查后端服务"""
    print_header("后端服务检查")
    
    backend_url = "http://localhost:8000"
    
    try:
        # 检查健康状态
        response = requests.get(f"{backend_url}/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ 后端服务: 运行正常")
            print(f"✅ 服务地址: {backend_url}")
            print(f"✅ 核心模式: {health_data.get('core_mode', 'unknown')}")
            
            components = health_data.get('components', {})
            for component, status in components.items():
                print(f"✅ {component}: {status}")
            
            return True
        else:
            print(f"❌ 后端服务: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 后端服务: 无法连接到 {backend_url}")
        print("💡 请先运行: python app.py")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ 后端服务: 连接超时")
        return False
    except Exception as e:
        print(f"❌ 后端服务: {str(e)}")
        return False

def check_frontend_service():
    """检查前端服务"""
    print_header("前端服务检查")
    
    frontend_url = "http://localhost:3000"
    
    try:
        response = requests.get(frontend_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ 前端服务: 运行正常")
            print(f"✅ 服务地址: {frontend_url}")
            
            # 检查是否包含Vue应用标识
            if "智能装配说明书生成系统" in response.text:
                print("✅ 前端内容: 正确加载")
            else:
                print("⚠️ 前端内容: 可能未正确加载")
            
            return True
        else:
            print(f"❌ 前端服务: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 前端服务: 无法连接到 {frontend_url}")
        print("💡 请先运行: cd frontend && npm run dev")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ 前端服务: 连接超时")
        return False
    except Exception as e:
        print(f"❌ 前端服务: {str(e)}")
        return False

def test_api_endpoints():
    """测试API接口"""
    print_header("API接口测试")
    
    backend_url = "http://localhost:8000"
    
    endpoints = [
        ("/", "系统首页"),
        ("/api/health", "健康检查"),
        ("/api/workers", "工人列表"),
        ("/docs", "API文档")
    ]
    
    all_passed = True
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{backend_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint} - {description}")
            else:
                print(f"❌ {endpoint} - {description} (HTTP {response.status_code})")
                all_passed = False
        except Exception as e:
            print(f"❌ {endpoint} - {description} ({str(e)})")
            all_passed = False
    
    return all_passed

def test_core_components():
    """测试核心组件"""
    print_header("核心组件测试")
    
    try:
        # 测试双通道解析器
        from core.dual_channel_parser import DualChannelParser
        parser = DualChannelParser()
        print("✅ 双通道解析器: 导入成功")
    except Exception as e:
        print(f"❌ 双通道解析器: {str(e)}")
    
    try:
        # 测试融合专家
        from models.fusion_expert import FusionExpertModel
        expert = FusionExpertModel()
        print("✅ DeepSeek融合专家: 导入成功")
    except Exception as e:
        print(f"❌ DeepSeek融合专家: {str(e)}")
    
    try:
        # 测试视觉模型
        from models.vision_model import VisionModel
        vision = VisionModel()
        print("✅ Qwen3-VL视觉模型: 导入成功")
    except Exception as e:
        print(f"❌ Qwen3-VL视觉模型: {str(e)}")

def generate_report():
    """生成系统报告"""
    print_header("系统状态报告")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "system": "智能装配说明书生成系统",
        "version": "2.0.0",
        "architecture": "双通道架构",
        "checks": {
            "files_structure": check_files_structure(),
            "python_environment": check_python_environment(),
            "api_keys": check_api_keys(),
            "backend_service": check_backend_service(),
            "frontend_service": check_frontend_service(),
            "api_endpoints": test_api_endpoints()
        }
    }
    
    # 计算总体状态
    passed_checks = sum(1 for check in report["checks"].values() if check)
    total_checks = len(report["checks"])
    success_rate = (passed_checks / total_checks) * 100
    
    print(f"\n📊 检查结果: {passed_checks}/{total_checks} 项通过 ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("✅ 系统状态: 良好")
        status = "healthy"
    elif success_rate >= 60:
        print("⚠️ 系统状态: 需要注意")
        status = "warning"
    else:
        print("❌ 系统状态: 需要修复")
        status = "error"
    
    report["overall_status"] = status
    report["success_rate"] = success_rate
    
    # 保存报告
    report_file = f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📄 详细报告已保存: {report_file}")
    
    return report

def main():
    """主函数"""
    print("🔍 智能装配说明书生成系统 - 状态检查")
    print(f"⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 执行所有检查
    test_core_components()
    report = generate_report()
    
    print("\n" + "=" * 60)
    print("🎯 检查完成!")
    
    if report["success_rate"] >= 80:
        print("💡 建议: 系统运行良好，可以正常使用")
    else:
        print("💡 建议: 请根据上述检查结果修复相关问题")
    
    print("📍 访问地址:")
    print("  - 前端界面: http://localhost:3000")
    print("  - 后端API: http://localhost:8000")
    print("  - API文档: http://localhost:8000/docs")
    print("=" * 60)

if __name__ == "__main__":
    main()
