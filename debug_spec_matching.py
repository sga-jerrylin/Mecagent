"""
调试规格匹配问题
"""

import json
from core.bom_3d_matcher import BOM3DMatcher

# 读取数据
with open('test_output_three_agents/all_pdfs_bom.json', encoding='utf-8') as f:
    bom = json.load(f)

with open('test_output_three_agents/step_parts_list.json', encoding='utf-8') as f:
    parts = json.load(f)

matcher = BOM3DMatcher()

print("="*80)
print("BOM表中的规格提取")
print("="*80)

bom_specs = {}
for item in bom:
    product_code = item.get('product_code', '')
    name = item.get('name', '')
    
    spec = matcher.extract_spec_from_name(product_code) or matcher.extract_spec_from_name(name)
    
    if spec:
        bom_specs[spec] = item
        print(f"✅ {item['code']}: {spec}")
        print(f"   来自product_code: {product_code}")
        print(f"   来自name: {name}")
    else:
        print(f"❌ {item['code']}: 无规格")
        print(f"   product_code: {product_code}")
        print(f"   name: {name}")

print(f"\n总共提取到 {len(bom_specs)} 个规格")

print("\n" + "="*80)
print("3D零件中的规格提取（前30个）")
print("="*80)

part_specs = {}
for i, part in enumerate(parts[:30]):
    fixed_name = matcher.fix_encoding(part['geometry_name'])
    spec = matcher.extract_spec_from_name(fixed_name)
    
    if spec:
        if spec not in part_specs:
            part_specs[spec] = []
        part_specs[spec].append(fixed_name)
        
        # 检查是否在BOM中
        if spec in bom_specs:
            print(f"✅ {i+1}. {spec} - 在BOM中")
        else:
            print(f"❌ {i+1}. {spec} - 不在BOM中")
        print(f"   3D: {fixed_name[:80]}")
    else:
        print(f"⚠️  {i+1}. 无规格")
        print(f"   3D: {fixed_name[:80]}")

print(f"\n3D零件中提取到 {len(part_specs)} 个不同的规格")

print("\n" + "="*80)
print("规格匹配分析")
print("="*80)

print("\nBOM中的规格:")
for spec in bom_specs.keys():
    print(f"  - {spec}")

print("\n3D中的规格（前10个）:")
for spec in list(part_specs.keys())[:10]:
    print(f"  - {spec} ({len(part_specs[spec])} 个零件)")

print("\n匹配的规格:")
matched_specs = set(bom_specs.keys()) & set(part_specs.keys())
for spec in matched_specs:
    print(f"  ✅ {spec}")
    print(f"     BOM: {bom_specs[spec]['name']}")
    print(f"     3D数量: {len(part_specs[spec])}")

print("\n未匹配的BOM规格:")
unmatched_bom_specs = set(bom_specs.keys()) - set(part_specs.keys())
for spec in unmatched_bom_specs:
    print(f"  ❌ {spec} - {bom_specs[spec]['name']}")

print("\n未匹配的3D规格（前10个）:")
unmatched_part_specs = set(part_specs.keys()) - set(bom_specs.keys())
for spec in list(unmatched_part_specs)[:10]:
    print(f"  ❌ {spec}")
    print(f"     示例: {part_specs[spec][0][:80]}")

