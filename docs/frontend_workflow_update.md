# 前端工作流更新说明

## 📋 更新概述

根据正确的工作流程，前端进度界面已更新为**顺序处理**模式，体现了PDF解析必须先完成，然后才能进行后续步骤的逻辑。

---

## 🔄 新的工作流程

### **完整流程图**

```
用户上传: PDF + STEP
    ↓
┌─────────────────────────────────────────┐
│ 阶段1: PDF解析 - 提取BOM表 ⭐ 必须先完成 │
├─────────────────────────────────────────┤
│ 1. 文本提取 (pypdf)                      │
│    - 提取BOM表格数据                     │
│    - 识别零件代号、名称、数量            │
│                                          │
│ 2. 视觉分析 (Qwen-VL)                   │
│    - 分析图纸结构                        │
│    - 识别装配关系                        │
│    - 提取技术要求                        │
│                                          │
│ 3. 生成BOM表                            │
│    - 合并文本和视觉结果                  │
│    - 生成最终BOM候选列表                 │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 阶段2: 并行处理 - 基于BOM数据           │
├─────────────────────────────────────────┤
│ 支路1: PDF深度分析                       │
│   - 装配步骤识别                         │
│   - 紧固件使用分析                       │
│   - 扭矩值提取                           │
│                                          │
│ 支路2: STEP零件提取                      │
│   - 提取几何名称                         │
│   - 统计实例数量                         │
│   - 修复编码问题                         │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 阶段3: BOM-STEP智能匹配                 │
├─────────────────────────────────────────┤
│ 1. 规则匹配                             │
│    - 基于代号匹配                        │
│    - 基于规格匹配                        │
│    - 实例数验证                          │
│                                          │
│ 2. DeepSeek推理匹配                     │
│    - 修复编码问题                        │
│    - 组件拆解                            │
│    - 语义匹配                            │
│                                          │
│ 3. 生成BOM-3D映射                       │
│    - 建立完整对应关系                    │
│    - 计算最终匹配率                      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 阶段4: 生成装配说明书                   │
├─────────────────────────────────────────┤
│ - 生成装配步骤                           │
│ - 创建3D交互界面                         │
│ - 输出HTML文档                           │
└─────────────────────────────────────────┘
```

---

## 🎯 关键改动

### **1. 阶段定义更新**

**旧版本（并行处理）：**
```javascript
const stages = {
  pdf: 'PDF解析与分析',
  model: '3D模型处理',
  ai: 'AI智能分析',
  generate: '说明书生成'
}
```

**新版本（顺序处理）：**
```javascript
const stages = {
  pdf_bom: '阶段1: PDF解析 - 提取BOM表',      // ⭐ 必须先完成
  parallel: '阶段2: 并行处理 - 基于BOM数据',  // 基于BOM
  matching: '阶段3: BOM-STEP智能匹配',       // 基于BOM
  generate: '阶段4: 生成装配说明书'           // 最终输出
}
```

### **2. 阶段1: PDF解析 - 提取BOM表**

**UI展示：**
- ✅ 文本提取 (pypdf)
  - 显示BOM候选项数量
  - 实时进度更新
  
- ✅ 视觉分析 (Qwen-VL)
  - 显示装配关系数量
  - 显示技术要求数量
  
- ✅ 生成BOM表
  - 显示最终BOM项目数

**数据结构：**
```javascript
stageData.pdf_bom = {
  current_task: 'text_extraction' | 'vision_analysis' | 'bom_generation',
  text_extraction: {
    message: '提取BOM表格数据...',
    bom_candidates: 53
  },
  vision_analysis: {
    message: '分析图纸结构和装配关系...',
    assembly_relations: 12,
    requirements: 8
  },
  bom_generation: {
    message: '合并文本和视觉结果...',
    total_items: 53
  },
  text_extraction_done: true,
  vision_analysis_done: true,
  bom_generation_done: true
}
```

### **3. 阶段2: 并行处理 - 基于BOM数据**

**UI展示：**
- 📄 PDF深度分析
  - 装配步骤数量
  - 紧固件数量
  
- 📦 STEP零件提取
  - 唯一零件数量
  - 总实例数量

**数据结构：**
```javascript
parallelProgress = {
  pdf_deep: 75,      // PDF深度分析进度
  step_extract: 60   // STEP零件提取进度
}

stageData.pdf_deep = {
  message: '分析装配关系和技术要求...',
  assembly_steps: 12,
  fasteners: 45
}

stageData.step_extract = {
  message: '提取零件几何名称和实例数...',
  unique_parts: 102,
  total_instances: 414
}
```

### **4. 阶段3: BOM-STEP智能匹配**

**UI展示：**
- 🔧 规则匹配
  - 已匹配数量/总BOM数量
  - 匹配率百分比
  
- 🤖 DeepSeek推理匹配
  - 新匹配数量
  - 组件拆解数量
  
- ✅ 生成BOM-3D映射
  - 最终匹配率

**数据结构：**
```javascript
stageData.matching = {
  current_task: 'rule_matching' | 'ai_matching' | 'mapping',
  rule_matching: {
    message: '基于代号和规格进行匹配...',
    matched: 23,
    total_bom: 53,
    match_rate: 43.4
  },
  ai_matching: {
    message: '修复编码问题，组件拆解...',
    new_matches: 19,
    components: 7
  },
  mapping: {
    message: '建立完整的对应关系...',
    final_match_rate: 79.2
  },
  rule_matching_done: true,
  ai_matching_done: true,
  mapping_done: true
}
```

---

## 📝 后端需要配合的改动

### **1. WebSocket消息格式**

**阶段1: PDF解析**
```python
await websocket.send_json({
    "type": "progress_update",
    "stage": "pdf_bom",
    "progress": 30,
    "message": "正在提取BOM表...",
    "data": {
        "current_task": "text_extraction",
        "text_extraction": {
            "message": "提取BOM表格数据...",
            "bom_candidates": 53
        }
    }
})
```

**阶段2: 并行处理**
```python
await websocket.send_json({
    "type": "progress_update",
    "stage": "parallel",
    "progress": 50,
    "message": "并行处理中...",
    "data": {
        "parallel_progress": {
            "pdf_deep": 75,
            "step_extract": 60
        },
        "pdf_deep": {
            "message": "分析装配关系...",
            "assembly_steps": 12
        },
        "step_extract": {
            "message": "提取零件名称...",
            "unique_parts": 102
        }
    }
})
```

**阶段3: BOM-STEP匹配**
```python
await websocket.send_json({
    "type": "progress_update",
    "stage": "matching",
    "progress": 80,
    "message": "BOM-STEP匹配中...",
    "data": {
        "current_task": "ai_matching",
        "rule_matching": {
            "matched": 23,
            "total_bom": 53,
            "match_rate": 43.4
        },
        "ai_matching": {
            "message": "DeepSeek推理中...",
            "new_matches": 19,
            "components": 7
        },
        "rule_matching_done": true
    }
})
```

---

## ✅ 验证清单

- [x] 前端阶段定义已更新
- [x] ProcessingVisualization组件已更新
- [x] 阶段1: PDF解析UI已实现
- [x] 阶段2: 并行处理UI已实现
- [x] 阶段3: BOM-STEP匹配UI已实现
- [ ] 后端WebSocket消息格式需要更新
- [ ] 后端处理流程需要调整为顺序处理

---

## 🚀 下一步

1. **后端调整**：修改core/dual_channel_parser.py，实现顺序处理逻辑
2. **WebSocket更新**：更新消息格式，匹配新的阶段定义
3. **测试验证**：完整测试新的工作流程

---

## 📌 注意事项

1. **阶段1必须先完成**：PDF解析提取BOM是所有后续步骤的基础
2. **阶段2基于BOM**：并行处理的两个支路都依赖BOM数据
3. **阶段3基于BOM**：匹配算法需要BOM作为参考
4. **进度计算**：总进度 = (阶段1进度 × 0.3) + (阶段2进度 × 0.3) + (阶段3进度 × 0.3) + (阶段4进度 × 0.1)

