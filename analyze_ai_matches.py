"""
分析AI匹配的结果
"""

import json

# 读取匹配结果
with open('test_output_three_agents/multi_pdf_matching_result.json', encoding='utf-8') as f:
    result = json.load(f)

# 获取AI匹配的零件
ai_matched = [
    p for p in result['cleaned_parts']
    if p.get('match_method') and 'AI匹配' in str(p.get('match_method'))
]

print("="*80)
print("AI匹配结果分析")
print("="*80)

print(f"\nAI匹配的零件数: {len(ai_matched)}")

# 按置信度分组
high_conf = [p for p in ai_matched if p.get('confidence', 0) >= 0.9]
medium_conf = [p for p in ai_matched if 0.7 <= p.get('confidence', 0) < 0.9]
low_conf = [p for p in ai_matched if p.get('confidence', 0) < 0.7]

print(f"\n置信度分布:")
print(f"  高置信度(≥0.9): {len(high_conf)} 个")
print(f"  中置信度(0.7-0.9): {len(medium_conf)} 个")
print(f"  低置信度(<0.7): {len(low_conf)} 个")

print(f"\n前20个AI匹配的零件:")
for i, p in enumerate(ai_matched[:20], 1):
    print(f"\n{i}. {p['fixed_name'][:70]}")
    print(f"   BOM代号: {p['bom_code']}")
    print(f"   置信度: {p.get('confidence', 0):.2f}")
    print(f"   理由: {p.get('ai_reason', '')}")

# 分析AI匹配的类型
print(f"\n{'='*80}")
print("AI匹配类型分析")
print(f"{'='*80}")

reason_keywords = {}
for p in ai_matched:
    reason = p.get('ai_reason', '')
    # 提取关键词
    if '产品代号' in reason:
        reason_keywords['产品代号匹配'] = reason_keywords.get('产品代号匹配', 0) + 1
    elif '规格' in reason:
        reason_keywords['规格匹配'] = reason_keywords.get('规格匹配', 0) + 1
    elif '推测' in reason or '推理' in reason:
        reason_keywords['推理推测'] = reason_keywords.get('推理推测', 0) + 1
    elif '部分' in reason:
        reason_keywords['部分匹配'] = reason_keywords.get('部分匹配', 0) + 1
    else:
        reason_keywords['其他'] = reason_keywords.get('其他', 0) + 1

print(f"\n匹配类型分布:")
for keyword, count in sorted(reason_keywords.items(), key=lambda x: x[1], reverse=True):
    print(f"  {keyword}: {count} 个")

