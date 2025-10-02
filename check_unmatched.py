#!/usr/bin/env python3
"""
查看未匹配的BOM项目详情
"""

import json

# 加载BOM数据
with open('test_output/vision_with_bom_result.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

bom_items = data['bom_candidates']

# 未匹配的代号
unmatched_codes = ['01.09.2552', '01.09.2551', '01.09.2550', '01.09.2549']

print("="*80)
print("未匹配的4个BOM组件详情")
print("="*80)

for code in unmatched_codes:
    item = next((b for b in bom_items if b['code'] == code), None)
    if item:
        print(f"\n代号: {item['code']}")
        print(f"名称: {item['name']}")
        print(f"数量: {item['qty']}")
        print(f"重量: {item.get('weight', 'N/A')} kg")
        print(f"原始文本: {item.get('raw', 'N/A')}")

print("\n" + "="*80)
print("分析：这些都是什么？")
print("="*80)

print("""
1. T-SPV1830-EURO-04 右铲雪板组件
2. T-SPV1830-EURO-03 左铲雪板组件
3. T-SPV1830-EURO-02 后座连接架组件
4. T-SPV1830-EURO-01 连接器后座组件

这些都是【大型组件】，每个组件可能包含多个子零件。

可能的原因：
1. 这些组件在STEP文件中已经被拆解成子零件了
2. 子零件在BOM中没有单独列出，只列出了组件
3. 需要在STEP中找到属于这些组件的所有子零件

让我们看看STEP中有哪些零件可能属于这些组件...
""")

# 加载STEP未匹配零件
with open('test_output/deepseek_matching_result.json', 'r', encoding='utf-8') as f:
    ai_result = json.load(f)

unmatched_step = ai_result.get('still_unmatched_step', [])

print("\n" + "="*80)
print(f"STEP中未匹配的零件 ({len(unmatched_step)} 个)")
print("="*80)

for item in unmatched_step:
    print(f"\n零件名称: {item['geometry_name']}")
    print(f"实例数: {item['instances_count']}")
    print(f"原因: {item['reason']}")

print("\n" + "="*80)
print("推测：")
print("="*80)
print("""
STEP中的这些未匹配零件可能就是那4个组件的子零件：

- T-SWB1400-SMS-C-LK-04-02-Q235 方形板 → 可能属于某个组件
- EHYG-φ63-φ35-428-251-Ⅱ油缸盖 → 可能属于液压系统组件
- T-U2500-06-01-Q235弹簧导柱轴套 → 可能属于推雪板组件

但是BOM表中没有单独列出这些子零件，只列出了组件整体。
这是工程BOM的常见做法：组件作为一个整体采购或装配。
""")

