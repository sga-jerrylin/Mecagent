"""
分析当前数据流，明确每个智能体的输入输出
"""

import json
from pathlib import Path

# 读取现有的输出文件
output_dir = Path("test_output_three_agents")

print("=" * 80)
print("数据流分析")
print("=" * 80)

# 1. 智能体1（Qwen-VL）的输出
print("\n【智能体1：Qwen-VL视觉分析】")
print("-" * 80)

vision_file = output_dir / "agent1_vision_result.json"
if vision_file.exists():
    with open(vision_file, 'r', encoding='utf-8') as f:
        vision_data = json.load(f)
    
    print("输出字段：")
    print(f"  - bom_candidates: {len(vision_data.get('bom_candidates', []))} 项")
    
    vision_channel = vision_data.get('vision_channel', {})
    if vision_channel:
        print(f"  - vision_channel:")
        print(f"      * product_overview: {list(vision_channel.get('product_overview', {}).keys())}")
        print(f"      * drawing_number_to_bom: {len(vision_channel.get('drawing_number_to_bom', []))} 项")
        print(f"      * spatial_relationships: {len(vision_channel.get('spatial_relationships', []))} 项")
        print(f"      * assembly_connections: {len(vision_channel.get('assembly_connections', []))} 项")
        print(f"      * critical_dimensions: {len(vision_channel.get('critical_dimensions', []))} 项")
        print(f"      * assembly_sequence_hints: {len(vision_channel.get('assembly_sequence_hints', []))} 项")
        print(f"      * technical_requirements: {len(vision_channel.get('technical_requirements', []))} 项")
        print(f"      * welding_info: {len(vision_channel.get('welding_info', []))} 项")

# 2. BOM-3D匹配的输出
print("\n【步骤2：BOM-3D匹配（代码实现）】")
print("-" * 80)

matching_file = output_dir / "agent2_matching_result.json"
if matching_file.exists():
    with open(matching_file, 'r', encoding='utf-8') as f:
        matching_data = json.load(f)
    
    print("输出字段：")
    print(f"  - summary: {matching_data.get('summary', {})}")
    print(f"  - cleaned_parts: {len(matching_data.get('cleaned_parts', []))} 项")
    
    # 生成BOM到mesh_id的映射
    bom_to_mesh = {}
    for part in matching_data.get('cleaned_parts', []):
        bom_code = part.get('bom_code')
        mesh_id = part.get('mesh_id')
        if bom_code and mesh_id:
            if bom_code not in bom_to_mesh:
                bom_to_mesh[bom_code] = []
            bom_to_mesh[bom_code].append(mesh_id)
    
    print(f"  - bom_to_mesh_mapping: {len(bom_to_mesh)} 个BOM代号有对应的mesh_id")

# 3. STEP零件列表
print("\n【STEP文件解析】")
print("-" * 80)

parts_file = output_dir / "step_parts_list.json"
if parts_file.exists():
    with open(parts_file, 'r', encoding='utf-8') as f:
        parts_data = json.load(f)
    
    print(f"  - 3D零件总数: {len(parts_data)}")
    if parts_data:
        print(f"  - 示例零件: {parts_data[0]}")

# 4. 数据流总结
print("\n" + "=" * 80)
print("数据流总结")
print("=" * 80)

print("""
当前数据流：

步骤1：预处理
  输入：PDF文件 + STEP文件
  输出：
    - PDF图片列表
    - GLB文件路径
    - 3D零件列表（414个）

步骤2：智能体1（Qwen-VL）
  输入：PDF图片 + BOM表
  输出：
    - bom_candidates（53项）
    - vision_channel:
        * product_overview（产品总览）
        * drawing_number_to_bom（图号与BOM映射）
        * spatial_relationships（空间关系）
        * assembly_connections（装配连接）
        * critical_dimensions（关键尺寸）
        * assembly_sequence_hints（装配顺序线索）
        * technical_requirements（技术要求）
        * welding_info（焊接信息）

步骤3：BOM-3D匹配（代码）
  输入：BOM表 + 3D零件列表
  输出：
    - cleaned_parts（414项，每项包含bom_code和mesh_id）
    - bom_to_mesh_mapping（BOM代号 → mesh_id列表）

步骤4：智能体3（待拆分）
  输入：vision_channel + bom_to_mesh_mapping + BOM表
  输出：完整的装配说明书JSON
""")

print("\n" + "=" * 80)
print("智能体3的拆分建议")
print("=" * 80)

print("""
智能体3-1：装配步骤规划专家
  输入：
    - vision_channel.product_overview
    - vision_channel.assembly_connections
    - vision_channel.assembly_sequence_hints
    - vision_channel.spatial_relationships
    - BOM表（主要结构件）
    - bom_to_mesh_mapping
  输出：
    - assembly_steps（5-10个主要步骤）

智能体3-2：焊接工艺转化专家
  输入：
    - vision_channel.welding_info
    - vision_channel.assembly_connections（焊接连接）
  输出：
    - welding_requirements（3-5个关键焊缝）

智能体3-3：质量控制专家
  输入：
    - vision_channel.critical_dimensions
    - vision_channel.technical_requirements
    - assembly_steps（来自智能体3-1）
  输出：
    - quality_control（关键尺寸检查 + 最终检查清单）

智能体3-4：安全与FAQ生成专家
  输入：
    - assembly_steps（来自智能体3-1）
    - welding_requirements（来自智能体3-2）
  输出：
    - safety_warnings（5-10条）
    - faq（5-10个）

代码整合模块：
  输入：所有子智能体的输出 + BOM表 + bom_to_mesh_mapping
  输出：最终的完整JSON
""")

