import json
from core.bom_3d_matcher import BOM3DMatcher

# 读取BOM数据
with open('test_output_three_agents/all_pdfs_bom.json', encoding='utf-8') as f:
    bom = json.load(f)

# 读取3D零件数据
with open('test_output_three_agents/step_parts_list.json', encoding='utf-8') as f:
    parts = json.load(f)

print("="*80)
print("BOM代号检查")
print("="*80)

print(f"\nBOM总数: {len(bom)}")
print("\n前10个BOM项的代号:")
for i, item in enumerate(bom[:10], 1):
    print(f"{i}. {item['code']} - {item['name'][:30]}")

print("\n" + "="*80)
print("3D零件名称检查（修复编码后）")
print("="*80)

matcher = BOM3DMatcher()

print(f"\n3D零件总数: {len(parts)}")
print("\n前10个3D零件的名称:")
for i, part in enumerate(parts[:10], 1):
    original = part['geometry_name']
    fixed = matcher.fix_encoding(original)
    print(f"{i}. 原始: {original[:60]}")
    print(f"   修复: {fixed[:60]}")
    print()

print("\n" + "="*80)
print("代号提取测试")
print("="*80)

# 测试代号提取
for i, part in enumerate(parts[:20], 1):
    fixed_name = matcher.fix_encoding(part['geometry_name'])
    code = matcher.extract_code_from_name(fixed_name)
    if code:
        print(f"{i}. 提取到代号: {code}")
        print(f"   来自: {fixed_name[:80]}")
    else:
        print(f"{i}. 未提取到代号")
        print(f"   来自: {fixed_name[:80]}")

