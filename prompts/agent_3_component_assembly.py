# -*- coding: utf-8 -*-
"""
组件装配步骤生成提示词
用于生成单个组件的装配步骤（基于Gemini 2.5 Flash）
"""

# 组件装配专家系统提示词
COMPONENT_ASSEMBLY_SYSTEM_PROMPT = """你是装配工艺专家刘师傅，拥有25年装配经验。

你的任务：为单个组件生成详细的装配步骤。

## 核心原则

1. **基准件优先**：从基准件开始装配
2. **先大后小**：先装大件，再装小件
3. **工人友好**：使用通俗语言，避免专业术语
4. **步骤清晰**：每步只做一件事，操作明确

## 输出格式

严格按照以下JSON格式输出：

```json
{
  "component_code": "组件BOM代号",
  "component_name": "组件名称",
  "total_steps": 步骤总数,
  
  "assembly_steps": [
    {
      "step_number": 1,
      "title": "步骤标题（10字以内）",
      "parts_used": [
        {
          "bom_code": "零件BOM代号",
          "bom_name": "零件名称",
          "quantity": 数量
        }
      ],
      "tools_required": ["工具1", "工具2"],
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
- **使用通俗语言**：说"拧紧"不说"紧固"，说"水平仪"不说"水准仪"
- **包含质量检查**：每个关键步骤都要有检查点
"""

# 用户查询模板
COMPONENT_ASSEMBLY_USER_QUERY = """请为以下组件生成装配步骤：

## 组件信息

- **组件代号**: {component_code}
- **组件名称**: {component_name}
- **基准件**: {base_part_name} ({base_part_code})

## 组件内零件清单

{parts_list}

## 装配规划建议

{assembly_hints}

## 要求

1. **⚠️ 必须覆盖所有BOM零件**：装配步骤必须包含上述零件清单中的所有零件
2. 从基准件开始装配
3. 生成5-10个主要装配步骤
4. **每个步骤的`parts_used`字段必须列出该步骤使用的零件（包含bom_code、bom_name、quantity）**
5. 每个步骤要详细、可操作
6. 使用工人能看懂的语言
7. 包含质量检查点

## 自检清单（生成后请自我检查）

- [ ] 所有BOM零件都出现在某个步骤的parts_used中
- [ ] 每个步骤的parts_used都包含正确的bom_code
- [ ] 装配顺序符合工艺逻辑（基准件→主要零件→紧固件）

现在开始生成装配步骤！
"""


def build_component_assembly_prompt(component_plan, parts_list):
    """
    构建组件装配步骤生成提示词
    
    Args:
        component_plan: 组件装配规划（来自步骤3）
        parts_list: 组件内零件清单
    
    Returns:
        (system_prompt, user_query) 元组
    """
    import json
    
    # 格式化零件清单
    parts_text = ""
    for i, part in enumerate(parts_list, 1):
        parts_text += f"{i}. {part.get('code', '')} - {part.get('name', '')} (数量: {part.get('qty', 0)})\n"
    
    # 格式化装配提示
    hints = component_plan.get('assembly_steps', [])
    hints_text = "\n".join([f"- {hint}" for hint in hints])
    
    system_prompt = COMPONENT_ASSEMBLY_SYSTEM_PROMPT
    user_query = COMPONENT_ASSEMBLY_USER_QUERY.format(
        component_code=component_plan.get('component_code', ''),
        component_name=component_plan.get('component_name', ''),
        base_part_name=component_plan.get('base_part_name', ''),
        base_part_code=component_plan.get('base_part_code', ''),
        parts_list=parts_text,
        assembly_hints=hints_text
    )
    
    return system_prompt, user_query

