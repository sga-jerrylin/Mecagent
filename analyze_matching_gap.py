"""
深度分析BOM-3D匹配差距
找出为什么匹配率这么低
"""

import json
from pathlib import Path
from collections import Counter

def analyze_matching_gap():
    """分析匹配差距"""
    
    # 读取数据
    with open('test_output_three_agents/multi_pdf_matching_result.json', encoding='utf-8') as f:
        matching_result = json.load(f)
    
    with open('test_output_three_agents/all_pdfs_bom.json', encoding='utf-8') as f:
        all_bom = json.load(f)
    
    cleaned_parts = matching_result['cleaned_parts']
    
    # 分类零件
    matched_parts = [p for p in cleaned_parts if p.get('bom_code')]
    unmatched_parts = [p for p in cleaned_parts if not p.get('bom_code')]
    
    print("="*80)
    print("1. 基本统计")
    print("="*80)
    print(f"BOM总数: {len(all_bom)}")
    print(f"3D零件总数: {len(cleaned_parts)}")
    print(f"已匹配: {len(matched_parts)}")
    print(f"未匹配: {len(unmatched_parts)}")
    print(f"匹配率: {len(matched_parts)/len(cleaned_parts)*100:.1f}%")
    
    # 分析BOM代号分布
    print("\n" + "="*80)
    print("2. BOM代号分布")
    print("="*80)
    
    bom_code_prefixes = Counter()
    for item in all_bom:
        code = item['code']
        prefix = code.split('.')[0] if '.' in code else code[:2]
        bom_code_prefixes[prefix] += 1
    
    print("\nBOM代号前缀分布:")
    for prefix, count in bom_code_prefixes.most_common():
        print(f"  {prefix}.xxx: {count} 项")
    
    # 分析未匹配零件的名称特征
    print("\n" + "="*80)
    print("3. 未匹配零件名称分析")
    print("="*80)
    
    # 统计未匹配零件的名称关键词
    name_keywords = Counter()
    for part in unmatched_parts[:50]:
        name = part['fixed_name']
        # 提取关键词
        if '方形板' in name:
            name_keywords['方形板'] += 1
        elif '螺栓' in name or '螺钉' in name:
            name_keywords['螺栓/螺钉'] += 1
        elif '垫圈' in name:
            name_keywords['垫圈'] += 1
        elif '螺母' in name:
            name_keywords['螺母'] += 1
        elif '油杯' in name or '压注' in name:
            name_keywords['油杯'] += 1
        elif '安全销' in name:
            name_keywords['安全销'] += 1
        else:
            name_keywords['其他'] += 1
    
    print("\n未匹配零件类型分布（前50个）:")
    for keyword, count in name_keywords.most_common():
        print(f"  {keyword}: {count} 个")
    
    # 检查编码问题
    print("\n" + "="*80)
    print("4. 编码问题分析")
    print("="*80)
    
    encoding_issues = 0
    for part in unmatched_parts:
        name = part['fixed_name']
        # 检查是否有乱码字符
        if any(ord(c) > 127 and c not in '×°·' for c in name):
            encoding_issues += 1
    
    print(f"\n有编码问题的零件数: {encoding_issues}/{len(unmatched_parts)}")
    print(f"编码问题占比: {encoding_issues/len(unmatched_parts)*100:.1f}%")
    
    # 分析BOM表中是否有对应的零件
    print("\n" + "="*80)
    print("5. BOM表覆盖度分析")
    print("="*80)
    
    # 提取BOM表中的所有名称关键词
    bom_names = [item['name'] for item in all_bom]
    
    # 检查未匹配零件是否在BOM表中有类似名称
    potentially_matchable = 0
    for part in unmatched_parts[:20]:
        part_name = part['fixed_name']
        # 简单的关键词匹配
        for bom_name in bom_names:
            if any(keyword in part_name and keyword in bom_name 
                   for keyword in ['方形板', '螺栓', '垫圈', '螺母', '油杯', '安全销']):
                potentially_matchable += 1
                print(f"\n可能匹配:")
                print(f"  3D: {part_name}")
                print(f"  BOM: {bom_name}")
                break
    
    print(f"\n前20个未匹配零件中，可能有BOM对应的: {potentially_matchable} 个")
    
    # 分析匹配方法的有效性
    print("\n" + "="*80)
    print("6. 匹配方法分析")
    print("="*80)
    
    match_methods = Counter()
    for part in matched_parts:
        method = part.get('match_method', '未知')
        match_methods[method] += 1
    
    print("\n匹配方法分布:")
    for method, count in match_methods.most_common():
        print(f"  {method}: {count} 个零件")
    
    # 输出改进建议
    print("\n" + "="*80)
    print("7. 改进建议")
    print("="*80)
    
    print("\n基于以上分析，建议:")
    print("1. 修复编码问题 - 约{}个零件受影响".format(encoding_issues))
    print("2. 改进名称匹配算法 - 使用模糊匹配而不是精确匹配")
    print("3. 增加规格匹配的权重 - 很多标准件可以通过规格匹配")
    print("4. 检查组件图的BOM提取 - 组件图提取的BOM太少")
    print("5. 考虑使用AI辅助匹配 - 对于复杂的名称变体")


if __name__ == "__main__":
    analyze_matching_gap()

