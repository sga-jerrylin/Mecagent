# -*- coding: utf-8 -*-
"""
系统配置文件
集中管理所有配置参数
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# API配置
API_CONFIG = {
    # 阿里云DashScope配置 (Qwen3-VL)
    "dashscope": {
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen3-vl-plus",
        "timeout": 300,  # 5分钟超时
    },
    
    # DeepSeek配置 (装配专家)
    "deepseek": {
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "timeout": 180,  # 3分钟超时
        "temperature": 0.1,  # 降低随机性
        "max_tokens": 8000,
    }
}

# 文件处理配置
FILE_CONFIG = {
    # PDF处理配置
    "pdf": {
        "dpi": 300,  # 图片渲染DPI
        "max_pages": 50,  # 最大页数限制
        "supported_formats": [".pdf"],
    },
    
    # 3D模型配置
    "model": {
        "supported_formats": [".stl", ".step", ".stp"],
        "max_file_size": 100 * 1024 * 1024,  # 100MB
        "scale_factor": 1.0,  # 默认缩放因子
        "blender_timeout": 300,  # Blender处理超时(秒)
    }
}

# Blender配置
BLENDER_CONFIG = {
    "executable": os.getenv("BLENDER_EXE", "blender"),
    "timeout": 300,  # 5分钟超时
    "memory_limit": "4G",  # 内存限制
    "enable_gpu": False,  # 是否启用GPU渲染
}

# 输出配置
OUTPUT_CONFIG = {
    # HTML生成配置
    "html": {
        "template_name": "assembly_manual.html",
        "include_3d_viewer": True,
        "enable_offline": True,  # 启用离线支持
        "responsive_design": True,  # 响应式设计
    },
    
    # 3D查看器配置
    "viewer": {
        "threejs_version": "0.160.0",
        "enable_controls": True,
        "enable_explode": True,
        "default_camera_position": [5, 5, 5],
        "background_color": 0xf0f0f0,
    }
}

# 专业重点配置
FOCUS_TYPES = {
    "general": {
        "name": "通用装配",
        "description": "适用于一般机械装配",
        "focus_areas": ["assembly", "quality"],
    },
    "welding": {
        "name": "焊接重点",
        "description": "重点关注焊接工艺和质量",
        "focus_areas": ["welding", "assembly", "quality"],
    },
    "precision": {
        "name": "精密装配",
        "description": "高精度装配要求",
        "focus_areas": ["assembly", "quality"],
    },
    "heavy": {
        "name": "重型装配",
        "description": "重型设备装配",
        "focus_areas": ["assembly", "quality"],
    }
}

# 质量等级配置
QUALITY_LEVELS = {
    "basic": "基础质量要求",
    "standard": "标准质量要求",
    "high": "高质量要求",
    "critical": "关键质量要求"
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "assembly_system.log",
    "max_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
}

# 缓存配置
CACHE_CONFIG = {
    "enable": True,
    "directory": PROJECT_ROOT / ".cache",
    "max_size": 1024 * 1024 * 1024,  # 1GB
    "ttl": 24 * 3600,  # 24小时
}

# 安全配置
SECURITY_CONFIG = {
    "max_file_size": 500 * 1024 * 1024,  # 500MB
    "allowed_file_types": [".pdf", ".stl", ".step", ".stp"],
    "scan_uploads": False,  # 是否扫描上传文件
}

# 性能配置
PERFORMANCE_CONFIG = {
    "max_concurrent_jobs": 2,  # 最大并发任务数
    "memory_limit": "8G",  # 内存限制
    "temp_cleanup": True,  # 自动清理临时文件
}

# 开发配置
DEV_CONFIG = {
    "debug": os.getenv("DEBUG", "false").lower() == "true",
    "verbose": os.getenv("VERBOSE", "false").lower() == "true",
    "profile": False,  # 性能分析
    "mock_api": False,  # 模拟API调用
}


def get_config(section: str = None):
    """
    获取配置信息
    
    Args:
        section: 配置节名称，如果为None则返回所有配置
        
    Returns:
        配置字典
    """
    all_config = {
        "api": API_CONFIG,
        "file": FILE_CONFIG,
        "blender": BLENDER_CONFIG,
        "output": OUTPUT_CONFIG,
        "focus_types": FOCUS_TYPES,
        "quality_levels": QUALITY_LEVELS,
        "logging": LOGGING_CONFIG,
        "cache": CACHE_CONFIG,
        "security": SECURITY_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "dev": DEV_CONFIG,
    }
    
    if section:
        return all_config.get(section, {})
    return all_config


def validate_config():
    """验证配置的有效性"""
    errors = []
    
    # 检查API密钥
    if not API_CONFIG["dashscope"]["api_key"]:
        errors.append("DASHSCOPE_API_KEY 未设置")
    
    if not API_CONFIG["deepseek"]["api_key"]:
        errors.append("DEEPSEEK_API_KEY 未设置")
    
    # 检查Blender路径
    blender_path = BLENDER_CONFIG["executable"]
    if blender_path != "blender":  # 如果不是默认路径
        if not Path(blender_path).exists():
            errors.append(f"Blender可执行文件不存在: {blender_path}")
    
    # 检查缓存目录
    cache_dir = CACHE_CONFIG["directory"]
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        errors.append(f"无法创建缓存目录: {e}")
    
    return errors


def setup_environment():
    """设置运行环境"""
    # 创建必要的目录
    directories = [
        CACHE_CONFIG["directory"],
        PROJECT_ROOT / "logs",
        PROJECT_ROOT / "temp",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    # 设置环境变量
    if DEV_CONFIG["debug"]:
        os.environ["DEBUG"] = "true"
    
    if DEV_CONFIG["verbose"]:
        os.environ["VERBOSE"] = "true"


if __name__ == "__main__":
    # 配置验证脚本
    print("🔧 配置验证")
    print("=" * 40)
    
    errors = validate_config()
    
    if errors:
        print("❌ 配置错误:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("✅ 配置验证通过")
    
    print("\n📋 当前配置:")
    config = get_config()
    for section, values in config.items():
        print(f"  {section}: {len(values)} 项配置")
    
    # 设置环境
    setup_environment()
    print("\n✅ 环境设置完成")
