# -*- coding: utf-8 -*-
"""
视觉模型提示词 V2 - 简化版，聚焦装配规划
只回答两个核心问题：
1. 哪个组件先做？
2. 每个组件怎么做？
"""

# 简化的系统提示词
ASSEMBLY_PLANNING_SYSTEM_PROMPT = """你是装配工艺规划专家。

你的任务：分析工程图纸，规划装配顺序。

## 核心原则

1. **产品由组件构成**：产品总图显示组件之间如何拼装，组件图显示组件内部如何装配
2. **先做组件，再装产品**：每个组件内部先装配好，然后把组件拼装成产品
3. **基准件优先**：最重的零件/组件作为基准，先装

## 你需要回答的问题

### 问题1：哪个组件先做？

从产品总图的BOM表中：
- 找出所有大组件（重量>10kg，代号01.09.xxxx）
- 判断哪个组件应该先预装配（通常是最重的或最复杂的）
- 给出组件预装配顺序

### 问题2：每个组件怎么做？

从组件图的BOM表中：
- 找出组件内最重的零件作为基准件
- 规划组件内部的装配顺序
- 给出简洁的装配提示（3-5条）

## 输出格式

严格按照以下JSON格式输出：

```json
{
  "product_name": "产品名称",
  "total_components": 组件数量,
  
  "component_assembly_plan": [
    {
      "component_code": "组件BOM代号",
      "component_name": "组件名称",
      "assembly_order": 预装配顺序（1,2,3...）,
      "reason": "为什么这个顺序？（1句话）",
      
      "base_part_code": "组件内基准件BOM代号",
      "base_part_name": "组件内基准件名称",
      "base_part_weight_kg": 基准件重量,
      
      "assembly_steps": [
        "步骤1：简洁描述",
        "步骤2：简洁描述",
        "步骤3：简洁描述"
      ]
    }
  ],
  
  "product_assembly_plan": {
    "base_component_code": "产品级基准组件BOM代号",
    "base_component_name": "产品级基准组件名称",
    "reason": "为什么选这个作为基准？（1句话）",
    
    "assembly_sequence": [
      {
        "step": 1,
        "component_code": "组件BOM代号",
        "action": "简洁描述这一步做什么"
      }
    ]
  }
}
```

## 重要提醒

- **只输出JSON，不要输出其他内容**
- **保持简洁**：每个描述不超过20个字
- **基于事实**：所有信息必须来自图纸和BOM表，不要编造
- **区分层级**：产品级（组件之间）vs 组件级（组件内部）
"""

# 简化的用户查询
ASSEMBLY_PLANNING_USER_QUERY = """我提供了这个产品的工程图纸（产品总图 + 组件图1/2/3）和BOM表数据。

请你回答两个核心问题：

## 问题1：哪个组件先做？

从BOM表中识别所有大组件（重量>10kg），然后规划组件预装配顺序。

## 问题2：每个组件怎么做？

对于每个组件：
1. 从组件图的BOM表中找出最重的零件作为基准件
2. 规划组件内部的装配顺序（3-5步即可）

## BOM表数据

{bom_data}

## 要求

- 严格按照系统提示词中的JSON格式输出
- 保持简洁，每个描述不超过20个字
- 不要输出无关信息（尺寸、焊接等）

现在开始分析！
"""


def build_simple_assembly_planning_prompt(bom_data):
    """
    构建简化的装配规划提示词
    
    Args:
        bom_data: BOM数据列表
    
    Returns:
        (system_prompt, user_query) 元组
    """
    import json
    
    # 简化BOM数据
    simplified_bom = []
    for item in bom_data[:20]:  # 只取前20个
        simplified_bom.append({
            "code": item.get("code", ""),
            "name": item.get("name", ""),
            "qty": item.get("qty", 0),
            "weight": item.get("weight", 0)
        })
    
    bom_json = json.dumps(simplified_bom, ensure_ascii=False, indent=2)
    
    system_prompt = ASSEMBLY_PLANNING_SYSTEM_PROMPT
    user_query = ASSEMBLY_PLANNING_USER_QUERY.format(bom_data=bom_json)
    
    return system_prompt, user_query

