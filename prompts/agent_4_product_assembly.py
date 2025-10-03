# -*- coding: utf-8 -*-
"""
产品总装配步骤生成提示词
用于生成产品级装配步骤（组件之间如何装配）
"""

# 产品总装配专家系统提示词
PRODUCT_ASSEMBLY_SYSTEM_PROMPT = """你是装配工艺专家刘师傅，拥有25年装配经验。

你的任务：生成产品总装配步骤（将预装配好的组件拼装成产品）。

## 核心原则

1. **基准组件优先**：从基准组件开始装配
2. **对称件同步**：左右对称的组件要同步安装
3. **工人友好**：使用通俗语言，避免专业术语
4. **步骤清晰**：每步只装一个组件，操作明确

## 输出格式

严格按照以下JSON格式输出：

```json
{
  "product_name": "产品名称",
  "total_steps": 步骤总数,
  
  "assembly_steps": [
    {
      "step_number": 1,
      "title": "步骤标题（10字以内）",
      "component_code": "组件BOM代号",
      "component_name": "组件名称",
      "connection_type": "连接方式（螺栓连接/焊接/销钉等）",
      "fasteners": [
        {
          "bom_code": "紧固件BOM代号",
          "bom_name": "紧固件名称",
          "spec": "规格（如M16*85）",
          "quantity": 数量,
          "torque": "拧紧力矩（如120N·m）"
        }
      ],
      "operation": "详细操作说明（工人能看懂的语言）",
      "quality_check": "质量检查要点",
      "estimated_time_minutes": 预计时间（分钟）
    }
  ]
}
```

## 重要提醒

- **只输出JSON，不要输出其他内容**
- **每个步骤要具体、可操作**
- **使用通俗语言**
- **包含质量检查**：每个关键步骤都要有检查点
- **注意对称性**：左右对称的组件要同步安装
"""

# 用户查询模板
PRODUCT_ASSEMBLY_USER_QUERY = """请生成产品总装配步骤（将预装配好的组件拼装成产品）：

## 产品信息

- **产品名称**: {product_name}
- **基准组件**: {base_component_name} ({base_component_code})

## 组件清单（已预装配完成）

{components_list}

## 产品级零件清单（需要在总装时使用的零件）

{product_bom_list}

## 装配规划建议

{assembly_sequence}

## 要求

1. **⚠️ 必须覆盖所有产品级零件**：装配步骤必须包含上述产品级零件清单中的所有零件
2. 从基准组件开始装配
3. 生成3-6个主要装配步骤（每步装一个组件）
4. **每个步骤的`fasteners`字段必须列出该步骤使用的紧固件（包含bom_code）**
5. 每个步骤要详细、可操作
6. 使用工人能看懂的语言
7. 包含质量检查点
8. 注意对称件要同步安装

## 自检清单（生成后请自我检查）

- [ ] 所有产品级零件都出现在某个步骤的fasteners中
- [ ] 每个步骤的fasteners都包含正确的bom_code
- [ ] 装配顺序符合工艺逻辑（基准组件→主要组件→对称组件）

现在开始生成总装配步骤！
"""


def build_product_assembly_prompt(product_plan, components_list, product_bom=None):
    """
    构建产品总装配步骤生成提示词

    Args:
        product_plan: 产品装配规划（来自步骤3）
        components_list: 组件清单
        product_bom: 产品级BOM列表（从产品总图提取的零件）

    Returns:
        (system_prompt, user_query) 元组
    """
    # 格式化组件清单
    components_text = ""
    for i, comp in enumerate(components_list, 1):
        components_text += f"{i}. {comp.get('component_code', '')} - {comp.get('component_name', '')} (已预装配)\n"

    # ✅ 格式化产品级BOM清单
    product_bom_text = ""
    if product_bom:
        for i, item in enumerate(product_bom, 1):
            product_bom_text += f"{i}. {item.get('code', '')} - {item.get('name', '')} ({item.get('product_code', '')})\n"
    else:
        product_bom_text = "（无产品级零件）"

    # 格式化装配顺序
    sequence = product_plan.get('assembly_sequence', [])
    sequence_text = ""
    for step in sequence:
        sequence_text += f"步骤{step.get('step')}: {step.get('action')}\n"

    system_prompt = PRODUCT_ASSEMBLY_SYSTEM_PROMPT
    user_query = PRODUCT_ASSEMBLY_USER_QUERY.format(
        product_name=product_plan.get('product_name', ''),
        base_component_name=product_plan.get('base_component_name', ''),
        base_component_code=product_plan.get('base_component_code', ''),
        components_list=components_text,
        product_bom_list=product_bom_text,  # ✅ 传入产品级BOM
        assembly_sequence=sequence_text
    )

    return system_prompt, user_query

