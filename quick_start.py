#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本
使用参考项目中的测试文件进行演示
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """快速启动演示"""
    print("🚀 智能装配说明书生成系统 - 快速演示")
    print("=" * 60)
    
    # 检查测试文件
    test_pdf_dir = Path("参考项目/测试-pdf")
    test_model_dir = Path("step-stl文件")
    
    if not test_pdf_dir.exists():
        print("❌ 找不到测试PDF目录: 参考项目/测试-pdf")
        return 1
    
    if not test_model_dir.exists():
        print("❌ 找不到测试模型目录: step-stl文件")
        return 1
    
    # 查找测试文件
    pdf_files = list(test_pdf_dir.glob("*.pdf"))
    model_files = list(test_model_dir.glob("*.step")) + list(test_model_dir.glob("*.stl"))
    
    if not pdf_files:
        print("❌ 测试PDF目录中没有PDF文件")
        return 1
    
    if not model_files:
        print("❌ 测试模型目录中没有STEP/STL文件")
        return 1
    
    print(f"📄 找到 {len(pdf_files)} 个PDF文件:")
    for pdf in pdf_files:
        print(f"   - {pdf.name}")
    
    print(f"🎯 找到 {len(model_files)} 个模型文件:")
    for model in model_files:
        print(f"   - {model.name}")
    
    # 检查API密钥
    dashscope_key = os.getenv('DASHSCOPE_API_KEY')
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    
    if not dashscope_key:
        print("\n❌ 请设置DASHSCOPE_API_KEY环境变量")
        print("   export DASHSCOPE_API_KEY='your_api_key'")
        return 1
    
    if not deepseek_key:
        print("\n❌ 请设置DEEPSEEK_API_KEY环境变量")
        print("   export DEEPSEEK_API_KEY='your_api_key'")
        return 1
    
    print(f"\n✅ API密钥已配置")
    
    # 选择测试文件 (使用第一个PDF和第一个模型)
    selected_pdf = pdf_files[0]
    selected_model = model_files[0]
    
    print(f"\n🎯 使用测试文件:")
    print(f"   PDF: {selected_pdf.name}")
    print(f"   模型: {selected_model.name}")
    
    # 创建输出目录
    output_dir = Path("./demo_output")
    output_dir.mkdir(exist_ok=True)
    
    print(f"   输出: {output_dir}")
    
    # 构建命令
    cmd_args = [
        sys.executable, "main.py",
        "--pdf", str(selected_pdf),
        "--models", str(selected_model),
        "--output", str(output_dir),
        "--focus", "welding",
        "--requirements", "演示用装配说明书",
        "--verbose"
    ]
    
    print(f"\n🔧 执行命令:")
    print(f"   {' '.join(cmd_args)}")
    
    # 询问用户是否继续
    try:
        response = input("\n是否继续执行演示? (y/N): ").strip().lower()
        if response not in ['y', 'yes', '是']:
            print("演示已取消")
            return 0
    except KeyboardInterrupt:
        print("\n演示已取消")
        return 0
    
    # 执行主程序
    print("\n" + "="*60)
    print("开始生成装配说明书...")
    print("="*60)
    
    try:
        import subprocess
        result = subprocess.run(cmd_args, check=False)
        
        if result.returncode == 0:
            print("\n" + "="*60)
            print("🎉 演示完成！")
            print(f"📖 请查看生成的装配说明书: {output_dir}/assembly_manual.html")
            print("💡 用浏览器打开HTML文件即可查看")
            print("="*60)
        else:
            print(f"\n❌ 演示失败，退出码: {result.returncode}")
            return result.returncode
            
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
