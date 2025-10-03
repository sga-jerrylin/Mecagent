# 📋 Agent重构任务 - 文件清单

**任务**: 调整Agent分工并重构提示词，确保装配步骤生成准确

---

## ✅ 必读文件（按优先级排序）

### 🔴 优先级1：核心问题文件

| 文件路径 | 行数范围 | 重点内容 | 为什么重要 |
|---------|---------|---------|-----------|
| `docs/HANDOVER_AGENT_REFACTORING.md` | 全部 | 交接文档，问题分析，重构方向 | **从这里开始！** 理解任务目标 |
| `prompts/agent_3_1_assembly_steps_prompts.py` | 全部 | Agent 3-1提示词（需要重构） | **核心文件！** 主要修改对象 |
| `test_output_three_agents/agent3_1_assembly_steps.json` | 1-100 | 当前输出示例 | 看到问题所在 |
| `test_output_three_agents/agent1_vision_result.json` | 961-1100 | 视觉分析结果（vision_channel） | Agent 3-1的输入数据 |

---

### 🟡 优先级2：架构理解文件

| 文件路径 | 行数范围 | 重点内容 | 为什么重要 |
|---------|---------|---------|-----------|
| `docs/AGENT_ARCHITECTURE.md` | 54-75 | Agent 3-1定义 | 理解Agent职责 |
| `docs/AGENT_ARCHITECTURE.md` | 144-197 | 数据流架构 | 理解Agent依赖关系 |
| `docs/AGENT_ARCHITECTURE.md` | 218-231 | 提示词结构标准 | 遵循设计规范 |
| `test_three_agents_pipeline.py` | 345-401 | Agent 3-1调用逻辑 | 理解执行流程 |

---

### 🟢 优先级3：参考文件

| 文件路径 | 行数范围 | 重点内容 | 为什么重要 |
|---------|---------|---------|-----------|
| `prompts/agent_1_vision_prompts.py` | 全部 | Agent 1提示词 | 可能需要优化视觉提取 |
| `prompts/agent_3_2_welding_prompts.py` | 1-100 | 焊接专家提示词 | 参考成功的提示词设计 |
| `prompts/agent_3_4_safety_faq_prompts.py` | 1-100 | 安全专家提示词 | 参考弱依赖Agent设计 |
| `core/manual_integrator.py` | 11-91 | 数据集成逻辑 | 理解最终JSON生成 |

---

## 📂 文件详细说明

### 1. `prompts/agent_3_1_assembly_steps_prompts.py` ⭐ 核心

**总行数**: 301行

**关键部分**：

| 行数 | 内容 | 问题/建议 |
|------|------|----------|
| 12-21 | 角色定义 | ✅ 基本合理 |
| 25-29 | 教育背景 | ✅ 可以保留 |
| 33-50 | 职业经验 | ✅ 可以保留 |
| 54-78 | 知识结构 | ⚠️ 需要增强装配工艺知识 |
| 82-149 | 工作SOP | ❌ **需要重构！** 过于抽象 |
| 153-215 | 输出格式 | ✅ 可以保留 |
| 220-300 | 用户输入构建 | ⚠️ 可能需要增加更多上下文 |

**重点修改区域**：
- **第82-149行**：工作SOP（Chain of Thought）
  - 当前问题：基准件识别逻辑过于简单
  - 建议：增加产品类型识别、装配策略选择
  
- **第54-78行**：知识结构
  - 当前问题：缺少具体的装配工艺知识
  - 建议：增加不同产品类型的装配模式

---

### 2. `test_output_three_agents/agent3_1_assembly_steps.json`

**总行数**: 460行

**关键内容**：
```json
{
  "assembly_steps": [
    {
      "step_number": 1,
      "title": "安装底部加强筋基准件",
      "parts_used": [{"bom_code": "01.01.017678", "bom_name": "加强筋"}]
    },
    {
      "step_number": 2,
      "title": "安装左右侧框架",
      "parts_used": [
        {"bom_code": "01.01.011660", "bom_name": "左侧框架"},
        {"bom_code": "01.01.011515", "bom_name": "右侧框架"}
      ]
    }
  ]
}
```

**问题分析**：
- ❌ 步骤1：加强筋不一定是基准件
- ❌ 步骤2：左右框架应该先于加强筋安装
- ❌ 缺少对产品整体结构的理解

---

### 3. `test_output_three_agents/agent1_vision_result.json`

**总行数**: 1100+行

**关键部分**：

| 行数 | 字段 | 内容 |
|------|------|------|
| 961-967 | `product_overview` | 产品名称、类型、主要结构 |
| 968-1000 | `assembly_sequence_hints` | 装配顺序线索 |
| 1001-1050 | `assembly_connections` | 装配连接关系 |
| 1051-1100 | `spatial_relationships` | 空间关系 |

**示例数据**：
```json
{
  "vision_channel": {
    "product_overview": {
      "product_name": "T-SPV1830-EURO",
      "product_type": "推雪板",
      "main_structure": "框架+铲板+液压系统+连接组件"
    },
    "assembly_sequence_hints": [
      "建议先安装连接器后座作为基准件",
      "然后安装左右侧框架",
      "最后安装铲板和液压系统"
    ]
  }
}
```

**评估**：
- ✅ 产品信息完整
- ✅ 装配顺序线索清晰
- ⚠️ 可能需要更详细的工艺分析

---

### 4. `docs/AGENT_ARCHITECTURE.md`

**总行数**: 271行

**关键章节**：

| 行数 | 章节 | 内容 |
|------|------|------|
| 1-8 | 系统概述 | 多Agent协作架构 |
| 9-51 | Agent 1-2定义 | 视觉识别、BOM匹配 |
| 54-141 | Agent 3定义 | 装配手册生成（4个子Agent） |
| 144-197 | 数据流架构 | Agent依赖关系图 |
| 200-231 | 提示词规范 | 5模块标准、命名规范 |

**重点阅读**：
- **第60-75行**：Agent 3-1的详细定义
- **第186-197行**：依赖关系说明

---

### 5. `test_three_agents_pipeline.py`

**总行数**: 680+行

**关键函数**：

| 行数 | 函数 | 功能 |
|------|------|------|
| 345-401 | `step4_1_assembly_steps_generation` | Agent 3-1调用 |
| 575-680 | `run_complete_pipeline` | 完整流水线 |

**调用流程**：
```python
# 第345-401行
def step4_1_assembly_steps_generation(self, vision_result, bom_data):
    # 1. 构建用户输入
    user_input = build_assembly_steps_user_input(vision_result, bom_data)
    
    # 2. 组合system prompt
    system_prompt = f"{ASSEMBLY_STEPS_EXPERT_IDENTITY}\n\n{ASSEMBLY_STEPS_OUTPUT_FORMAT}"
    
    # 3. 调用DeepSeek
    response = self.deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.1,
        max_tokens=8000
    )
```

---

## 🎯 快速开始指南

### Step 1: 阅读交接文档（15分钟）
```bash
# 打开交接文档
docs/HANDOVER_AGENT_REFACTORING.md
```

### Step 2: 查看当前问题（10分钟）
```bash
# 查看当前输出
test_output_three_agents/agent3_1_assembly_steps.json

# 查看视觉输入
test_output_three_agents/agent1_vision_result.json
```

### Step 3: 理解提示词结构（20分钟）
```bash
# 查看Agent 3-1提示词
prompts/agent_3_1_assembly_steps_prompts.py

# 参考其他Agent提示词
prompts/agent_3_2_welding_prompts.py
prompts/agent_3_4_safety_faq_prompts.py
```

### Step 4: 理解架构（15分钟）
```bash
# 查看架构文档
docs/AGENT_ARCHITECTURE.md

# 查看测试流水线
test_three_agents_pipeline.py (第345-401行)
```

### Step 5: 开始重构（3-4小时）
1. 选择重构方向（见交接文档）
2. 修改提示词文件
3. 运行测试验证
4. 迭代优化

---

## 📝 修改文件清单

### 必须修改
- [ ] `prompts/agent_3_1_assembly_steps_prompts.py`

### 可能修改
- [ ] `prompts/agent_1_vision_prompts.py`（如果需要优化视觉提取）
- [ ] `docs/AGENT_ARCHITECTURE.md`（更新架构说明）

### 可能新增
- [ ] `prompts/agent_3_0_assembly_planning_prompts.py`（如果采用方向4）

---

## 🧪 测试验证

### 运行测试
```bash
# 运行完整流水线
python test_three_agents_pipeline.py

# 查看输出
test_output_three_agents/agent3_1_assembly_steps.json
test_output_three_agents/final_assembly_manual.json
```

### 验证指标
- ✅ 基准件选择正确
- ✅ 装配顺序符合工艺
- ✅ 零件分组合理
- ✅ 步骤数量合理（5-10个）
- ✅ 语言通俗易懂

---

**文件清单完成**  
**开始重构吧！** 🚀

