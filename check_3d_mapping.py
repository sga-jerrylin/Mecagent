import json

# 读取匹配结果
with open('test_output_three_agents/agent2_matching_result.json', encoding='utf-8') as f:
    matching_data = json.load(f)

# 读取装配步骤
with open('test_output_three_agents/agent3_1_assembly_steps.json', encoding='utf-8') as f:
    steps_data = json.load(f)

# 读取最终说明书
with open('test_output_three_agents/final_assembly_manual.json', encoding='utf-8') as f:
    final_data = json.load(f)

print("="*80)
print("BOM-3D映射检查")
print("="*80)

mapping = matching_data.get('bom_to_mesh_mapping', {})
print(f"\nBOM映射数量: {len(mapping)}")
print(f"\n前10个映射:")
for i, (k, v) in enumerate(list(mapping.items())[:10]):
    print(f"  {k}: {v}")

print("\n" + "="*80)
print("装配步骤1的零件")
print("="*80)

step1 = steps_data['assembly_steps'][0]
print(f"\n步骤1: {step1['title']}")
print(f"使用的零件:")
for part in step1['parts_used']:
    bom_code = part['bom_code']
    print(f"  - {bom_code}: {part['bom_name']}")
    if bom_code in mapping:
        print(f"    ✅ 有映射: {mapping[bom_code]}")
    else:
        print(f"    ❌ 无映射")

print("\n" + "="*80)
print("最终说明书中的步骤1")
print("="*80)

final_step1 = final_data['assembly_steps'][0]
print(f"\n步骤1: {final_step1['title']}")
print(f"3D高亮: {final_step1['3d_highlight']}")
print(f"相机角度: {final_step1['camera_angle']}")
print(f"爆炸偏移: {final_step1['explosion_offset']}")

