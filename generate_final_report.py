#!/usr/bin/env python3
"""
生成最终匹配报告
合并规则匹配和DeepSeek推理的结果
"""

import json

# 加载规则匹配结果
with open('test_output/step_bom_matching_v2_result.json', 'r', encoding='utf-8') as f:
    rule_result = json.load(f)

# 加载DeepSeek推理结果
with open('test_output/deepseek_matching_result.json', 'r', encoding='utf-8') as f:
    ai_result = json.load(f)

# 合并结果
all_matches = []

# 添加规则匹配的结果
for match in rule_result['matched']:
    all_matches.append({
        'bom_code': match['bom_item']['code'],
        'bom_name': match['bom_item']['name'],
        'bom_qty': match['bom_item']['qty'],
        'step_geometry_name': match['step_part']['geometry_name'],
        'step_instances': len(match['step_part']['instances']),
        'confidence': match['confidence'],
        'match_method': 'rule_based',
        'match_strategy': match.get('match_reason', match.get('match_strategy', 'unknown'))
    })

# 添加DeepSeek新匹配的结果
for match in ai_result.get('new_matches', []):
    all_matches.append({
        'bom_code': match['bom_code'],
        'bom_name': match['bom_name'],
        'bom_qty': match['bom_qty'],
        'step_geometry_name': match['step_geometry_name'],
        'step_instances': match['step_instances'],
        'confidence': match['confidence'],
        'match_method': 'ai_reasoning',
        'match_type': match['match_type'],
        'reasoning': match['reasoning']
    })

# 添加组件拆解结果
component_matches = []
for comp in ai_result.get('component_decomposition', []):
    component_matches.append({
        'bom_code': comp['bom_code'],
        'bom_name': comp['bom_name'],
        'bom_qty': comp['bom_qty'],
        'sub_parts': comp['sub_parts'],
        'confidence': comp['confidence'],
        'reasoning': comp['reasoning']
    })

# 生成报告
print("="*80)
print("BOM-STEP 最终匹配报告")
print("="*80)
print()

print("📊 匹配统计")
print("-"*80)
print(f"总BOM项目数: 53")
print(f"规则匹配: {len(rule_result['matched'])} 个 (43.4%)")
print(f"AI推理匹配: {len(ai_result.get('new_matches', []))} 个")
print(f"组件拆解: {len(component_matches)} 个")
print(f"总匹配数: {len(all_matches)} 个")
print(f"最终匹配率: {len(all_matches) / 53 * 100:.1f}%")
print()

print("✅ 规则匹配成功 ({} 个)".format(len(rule_result['matched'])))
print("-"*80)
for i, match in enumerate(rule_result['matched'][:10], 1):
    print(f"{i:2d}. {match['bom_item']['code']:20s} → {match['step_part']['geometry_name'][:50]}")
    print(f"    实例数: {len(match['step_part']['instances'])} = BOM数量: {match['bom_item']['qty']}")
if len(rule_result['matched']) > 10:
    print(f"    ... 还有 {len(rule_result['matched']) - 10} 个")
print()

print("🤖 AI推理匹配成功 ({} 个)".format(len(ai_result.get('new_matches', []))))
print("-"*80)
for i, match in enumerate(ai_result.get('new_matches', [])[:10], 1):
    print(f"{i:2d}. {match['bom_code']:20s} → {match['step_geometry_name'][:50]}")
    print(f"    实例数: {match['step_instances']} = BOM数量: {match['bom_qty']}")
    print(f"    类型: {match['match_type']}, 置信度: {match['confidence']}")
    print(f"    推理: {match['reasoning'][:80]}...")
    print()
if len(ai_result.get('new_matches', [])) > 10:
    print(f"    ... 还有 {len(ai_result.get('new_matches', [])) - 10} 个")
print()

print("📦 组件拆解成功 ({} 个)".format(len(component_matches)))
print("-"*80)
for i, comp in enumerate(component_matches, 1):
    print(f"{i:2d}. {comp['bom_code']:20s} {comp['bom_name']}")
    print(f"    子零件数: {len(comp['sub_parts'])}")
    for sub in comp['sub_parts']:
        print(f"      - {sub['step_geometry_name']} ({sub['step_instances']}个) - {sub['role']}")
    print(f"    置信度: {comp['confidence']}")
    print()

print("⚠️  仍未匹配的BOM项目 ({} 个)".format(len(ai_result.get('still_unmatched_bom', []))))
print("-"*80)
for i, item in enumerate(ai_result.get('still_unmatched_bom', []), 1):
    print(f"{i:2d}. {item['code']:20s} {item['name']}")
    print(f"    原因: {item['reason']}")
print()

print("="*80)
print("💡 关键洞察")
print("="*80)
print(ai_result.get('summary', {}).get('key_insights', 'N/A'))
print()

# 保存最终报告
final_report = {
    'summary': {
        'total_bom_items': 53,
        'rule_matched': len(rule_result['matched']),
        'ai_matched': len(ai_result.get('new_matches', [])),
        'component_decomposed': len(component_matches),
        'total_matched': len(all_matches),
        'match_rate': len(all_matches) / 53,
    },
    'all_matches': all_matches,
    'component_matches': component_matches,
    'unmatched_bom': ai_result.get('still_unmatched_bom', []),
    'unmatched_step': ai_result.get('still_unmatched_step', []),
    'insights': ai_result.get('summary', {}).get('key_insights', '')
}

with open('test_output/final_matching_report.json', 'w', encoding='utf-8') as f:
    json.dump(final_report, f, ensure_ascii=False, indent=2)

print("✅ 最终报告已保存到: test_output/final_matching_report.json")

