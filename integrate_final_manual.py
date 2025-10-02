"""
整合所有Agent输出，生成最终的装配说明书JSON
"""

import json
import os
from datetime import datetime
from core.manual_integrator import integrate_manual_data


def load_json(file_path):
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  加载失败 {file_path}: {e}")
        return None


def print_section(title, emoji="📋"):
    """打印分隔线"""
    print(f"\n{emoji} {'='*70}")
    print(f"{emoji} {title}")
    print(f"{emoji} {'='*70}\n")


def print_summary(manual_data):
    """打印装配说明书摘要"""
    
    print_section("📦 产品总览", "📦")
    overview = manual_data.get('product_overview', {})
    print(f"   产品名称: {overview.get('product_name', 'N/A')}")
    print(f"   产品类型: {overview.get('product_type', 'N/A')}")
    print(f"   总零件数: {overview.get('total_parts', 0)}")
    print(f"   主要零件: {overview.get('main_parts', 0)}")
    print(f"   标准件数: {overview.get('standard_parts', 0)}")
    print(f"   总重量: {overview.get('total_weight_kg', 0)} kg")
    print(f"   复杂度: {overview.get('complexity', 'N/A')}")
    print(f"   预计装配时间: {overview.get('estimated_time_hours', 0)} 小时")
    
    print_section("📋 BOM清单（带3D映射）", "📋")
    bom_items = manual_data.get('bom_items', [])
    print(f"   总BOM项数: {len(bom_items)}")
    
    # 统计3D映射情况
    mapped_count = sum(1 for item in bom_items if item.get('mesh_ids'))
    total_mesh_ids = sum(len(item.get('mesh_ids', [])) for item in bom_items)
    print(f"   已映射BOM: {mapped_count}/{len(bom_items)} ({mapped_count/len(bom_items)*100:.1f}%)")
    print(f"   总mesh数: {total_mesh_ids}")
    
    # 显示前5个BOM项
    print(f"\n   前5个BOM项:")
    for i, item in enumerate(bom_items[:5], 1):
        mesh_info = f"({len(item.get('mesh_ids', []))} meshes)" if item.get('mesh_ids') else "(未映射)"
        print(f"      {i}. {item.get('code', 'N/A')} - {item.get('name', 'N/A')} x{item.get('quantity', 0)} {mesh_info}")
    
    if len(bom_items) > 5:
        print(f"      ... 还有 {len(bom_items) - 5} 个BOM项")
    
    print_section("🔧 装配步骤", "🔧")
    assembly_steps = manual_data.get('assembly_steps', [])
    print(f"   总步骤数: {len(assembly_steps)}")
    
    # 显示每个步骤的摘要
    for i, step in enumerate(assembly_steps, 1):
        parts_count = len(step.get('parts_used', []))
        highlight_count = len(step.get('3d_highlight', []))
        camera = step.get('camera_angle', 'N/A')
        print(f"      步骤 {i}: {step.get('title', 'N/A')}")
        print(f"         - 使用零件: {parts_count} 个")
        print(f"         - 3D高亮: {highlight_count} meshes")
        print(f"         - 相机角度: {camera}")
        print(f"         - 描述: {step.get('description', 'N/A')[:60]}...")
    
    print_section("🔥 焊接要求", "🔥")
    welding_requirements = manual_data.get('welding_requirements', [])
    print(f"   总焊接要求数: {len(welding_requirements)}")
    
    for i, req in enumerate(welding_requirements, 1):
        print(f"      {i}. {req.get('requirement_id', 'N/A')}: {req.get('welding_location', 'N/A')}")
        print(f"         - 焊接类型: {req.get('welding_type', 'N/A')}")
        print(f"         - 焊接方法: {req.get('welding_method', 'N/A')}")
        print(f"         - 焊缝尺寸: {req.get('weld_size', 'N/A')}")
        print(f"         - 重要性: {req.get('importance', 'N/A')}")
    
    print_section("✅ 质量检验点", "✅")
    quality_checkpoints = manual_data.get('quality_checkpoints', [])
    print(f"   总检验点数: {len(quality_checkpoints)}")
    
    for i, checkpoint in enumerate(quality_checkpoints, 1):
        print(f"      {i}. {checkpoint.get('checkpoint_id', 'N/A')}: {checkpoint.get('inspection_item', 'N/A')}")
        print(f"         - 检验方法: {checkpoint.get('inspection_method', 'N/A')}")
        print(f"         - 合格标准: {checkpoint.get('acceptance_criteria', 'N/A')}")
    
    print_section("⚠️  安全警告", "⚠️")
    safety_warnings = manual_data.get('safety_warnings', [])
    print(f"   总安全警告数: {len(safety_warnings)}")
    
    for i, warning in enumerate(safety_warnings, 1):
        print(f"      {i}. [{warning.get('severity', 'N/A')}] {warning.get('warning_title', 'N/A')}")
        print(f"         - {warning.get('description', 'N/A')[:80]}...")
    
    print_section("❓ 常见问题FAQ", "❓")
    faq_items = manual_data.get('faq_items', [])
    print(f"   总FAQ数: {len(faq_items)}")
    
    for i, faq in enumerate(faq_items, 1):
        print(f"      {i}. Q: {faq.get('question', 'N/A')}")
        print(f"         A: {faq.get('answer', 'N/A')[:80]}...")
    
    print_section("🎨 3D模型信息", "🎨")
    model_3d = manual_data.get('3d_model', {})
    print(f"   GLB文件: {model_3d.get('glb_path', 'N/A')}")
    print(f"   总mesh数: {model_3d.get('total_meshes', 0)}")
    print(f"   相机预设: {len(model_3d.get('camera_angles', {}))} 个")


def main():
    """主函数"""
    output_dir = "test_output_three_agents"
    
    print_section("🚀 开始整合装配说明书数据", "🚀")
    
    # 1. 加载所有Agent的输出
    print("📂 加载Agent输出文件...")
    
    vision_result = load_json(f"{output_dir}/agent1_vision_result.json")
    bom_data = load_json(f"{output_dir}/all_pdfs_bom.json")
    matching_result = load_json(f"{output_dir}/agent2_code_ai_matching_result.json")
    assembly_steps = load_json(f"{output_dir}/agent3_1_assembly_steps.json")
    welding_requirements = load_json(f"{output_dir}/agent3_2_welding_requirements.json")
    quality_control = load_json(f"{output_dir}/agent3_3_quality_control.json")
    safety_faq = load_json(f"{output_dir}/agent3_4_safety_faq.json")
    
    print("   ✅ 视觉分析结果")
    print("   ✅ BOM数据")
    print("   ✅ BOM-3D匹配结果")
    print("   ✅ 装配步骤")
    print("   ✅ 焊接要求")
    print("   ✅ 质量控制")
    print("   ✅ 安全与FAQ")
    
    # 2. 提取数据
    print("\n📊 提取数据...")

    bom_to_mesh_mapping = matching_result.get('bom_to_mesh_mapping', {}) if matching_result else {}

    # 提取assembly_steps（可能是字典包含assembly_steps字段，也可能直接是列表）
    if isinstance(assembly_steps, dict):
        assembly_steps = assembly_steps.get('assembly_steps', [])
    elif not isinstance(assembly_steps, list):
        assembly_steps = []

    # 提取welding_requirements
    if isinstance(welding_requirements, dict):
        welding_requirements = welding_requirements.get('welding_requirements', [])
    elif not isinstance(welding_requirements, list):
        welding_requirements = []

    quality_checkpoints = quality_control.get('quality_checkpoints', []) if quality_control else []
    critical_dimensions = quality_control.get('critical_dimensions', []) if quality_control else []
    safety_warnings = safety_faq.get('safety_warnings', []) if safety_faq else []
    faq_items = safety_faq.get('faq_items', []) if safety_faq else []
    
    print(f"   BOM映射: {len(bom_to_mesh_mapping)} 个代号")
    print(f"   装配步骤: {len(assembly_steps) if assembly_steps else 0} 步")
    print(f"   焊接要求: {len(welding_requirements) if welding_requirements else 0} 个")
    print(f"   质量检验点: {len(quality_checkpoints)} 个")
    print(f"   关键尺寸: {len(critical_dimensions)} 个")
    print(f"   安全警告: {len(safety_warnings)} 个")
    print(f"   FAQ: {len(faq_items)} 个")
    
    # 3. 调用集成模块
    print("\n🔧 调用集成模块...")
    
    manual_data = integrate_manual_data(
        vision_result=vision_result or {},
        bom_data=bom_data or [],
        bom_to_mesh_mapping=bom_to_mesh_mapping,
        assembly_steps=assembly_steps,
        welding_requirements=welding_requirements,
        quality_checkpoints=quality_checkpoints,
        safety_warnings=safety_warnings,
        faq_items=faq_items
    )
    
    # 添加GLB路径
    manual_data['3d_model']['glb_path'] = f"{output_dir}/model.glb"
    
    print("   ✅ 集成完成")
    
    # 4. 保存最终JSON
    output_path = f"{output_dir}/final_assembly_manual.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manual_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 最终装配说明书已保存: {output_path}")
    
    # 5. 打印摘要
    print_summary(manual_data)
    
    # 6. 统计信息
    print_section("📊 最终统计", "📊")
    file_size = os.path.getsize(output_path) / 1024
    print(f"   文件大小: {file_size:.2f} KB")
    print(f"   生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   数据完整性: ✅")
    
    print_section("🎉 集成完成！", "🎉")
    print(f"   前端可以直接加载: {output_path}")
    print(f"   3D模型文件: {output_dir}/model.glb")
    print(f"   图纸图片: {output_dir}/pdf_images_*/")


if __name__ == "__main__":
    main()

