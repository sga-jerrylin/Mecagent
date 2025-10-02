# 智能装配手册生成系统 - Agent架构文档

## 系统概述

本系统采用多智能体协作架构，将复杂的装配手册生成任务分解为多个专业化的智能体，每个智能体负责特定的子任务。

---

## Agent编号体系

### **Agent 1: 视觉识别专家（Qwen-VL）**
- **编号**: Agent 1
- **名称**: Vision Recognition Expert（视觉识别专家）
- **模型**: Qwen3-VL (Alibaba)
- **提示词文件**: `prompts/agent_1_vision_prompts.py`
- **核心功能**: 
  - 从工程图纸PDF中提取视觉信息
  - 识别装配关系、连接方式、焊接符号
  - 提取关键尺寸、技术要求
  - 识别安全警告和注意事项
- **输入**: PDF工程图纸
- **输出**: `vision_channel.json`（视觉信息通道）
- **实现文件**: `processors/vision_processor.py`

---

### **Agent 2: BOM-3D匹配专家（代码+AI混合）**
- **编号**: Agent 2
- **名称**: BOM-3D Matching Expert（BOM-3D匹配专家）
- **实现方式**: 代码匹配 + AI智能匹配（DeepSeek）
- **提示词文件**: `prompts/agent_2_ai_bom_matcher_prompts.py`
- **核心功能**:
  - **代码匹配**（优先）:
    - 通过产品代号精确匹配
    - 通过规格匹配标准件
    - 编码修复（latin1→gbk）
  - **AI智能匹配**（补充）:
    - 处理代码匹配失败的零件
    - 通过推理和工程经验进行智能匹配
    - 处理乱码、部分匹配、工程推测
- **输入**: 
  - BOM表数据（从多个PDF提取）
  - 3D零件列表（STEP文件拆分）
- **输出**: 
  - `cleaned_parts`（清洗后的零件列表）
  - `bom_to_mesh_mapping`（BOM到mesh_id的映射表）
- **实现文件**: 
  - `core/bom_3d_matcher.py`（代码匹配）
  - `core/ai_matcher.py`（AI智能匹配）
- **匹配率**: 59.7%（代码47.6% + AI 12.1%）

---

### **Agent 3: 装配手册生成专家（DeepSeek）**
- **编号**: Agent 3
- **名称**: Assembly Manual Generation Expert（装配手册生成专家）
- **模型**: DeepSeek
- **架构**: 分解为4个子智能体 + 1个代码集成模块

#### **Agent 3-1: 装配步骤生成专家**
- **编号**: Agent 3-1
- **名称**: Assembly Steps Generator（装配步骤生成专家）
- **模型**: DeepSeek（文本推理）
- **提示词文件**: `prompts/agent_3_1_assembly_steps_prompts.py`
- **依赖关系**: ✅ **强依赖视觉**（必须有Qwen-VL输出）
- **核心功能**:
  - 将工程图纸转换为工人友好的装配步骤
  - 生成3-5个主要装配步骤
  - 每个步骤包含：标题、描述、零件列表、3D参数
- **输入**:
  - `vision_channel.assembly_sequence`（装配顺序）- 必需
  - `vision_channel.assembly_connections`（装配连接）- 必需
  - `bom_to_mesh_mapping`（BOM映射表）
- **输出**: `assembly_steps`（装配步骤列表）
- **状态**: ✅ 已实现并测试

#### **Agent 3-2: 焊接工艺翻译专家**
- **编号**: Agent 3-2
- **名称**: Welding Process Translator（焊接工艺翻译专家）
- **模型**: Qwen-VL（视觉识别焊接符号）⭐
- **提示词文件**: `prompts/agent_3_2_welding_prompts.py`
- **依赖关系**: ✅ **强依赖视觉**（需要图片输入）
- **核心功能**:
  - 直接从图纸识别焊接符号
  - 将焊接符号翻译为工人友好的语言
  - 生成3-5个关键焊接要求
  - 包含焊接位置、焊接方法、质量要求
- **输入**:
  - PDF图片（必需）⭐
  - `vision_channel.welding_info`（辅助信息）- 可选
- **输出**: `welding_requirements`（焊接要求列表）
- **状态**: ⏳ 需要改造为视觉模型

#### **Agent 3-3: 质量控制专家**
- **编号**: Agent 3-3
- **名称**: Quality Control Expert（质量控制专家）
- **模型**: Qwen-VL（视觉识别尺寸标注）⭐
- **提示词文件**: `prompts/agent_3_3_quality_control_prompts.py`
- **依赖关系**: ✅ **强依赖视觉**（需要图片输入）
- **核心功能**:
  - 直接从图纸识别尺寸标注和公差
  - 提取关键尺寸和公差要求
  - 生成检验清单
  - 标注质量控制点
- **输入**:
  - PDF图片（必需）⭐
  - `vision_channel.critical_dimensions`（辅助信息）- 可选
- **输出**: `quality_checkpoints`（质量检查点列表）
- **状态**: ⏳ 需要改造为视觉模型

#### **Agent 3-4: 安全与FAQ生成专家**
- **编号**: Agent 3-4
- **名称**: Safety & FAQ Generator（安全与FAQ生成专家）
- **模型**: DeepSeek（文本推理）
- **提示词文件**: `prompts/agent_3_4_safety_faq_prompts.py`
- **依赖关系**: ⚠️ **弱依赖视觉**（可选的视觉信息）
- **核心功能**:
  - 生成安全警告和注意事项
  - 生成常见问题FAQ
  - 提供故障排除建议
- **输入**:
  - `assembly_steps`（装配步骤）- 必需
  - `welding_requirements`（焊接要求）- 可选
  - `vision_channel.safety_warnings`（安全警告）- 可选
- **输出**:
  - `safety_warnings`（安全警告列表）
  - `faq_items`（FAQ列表）
- **特点**: 即使没有视觉信息，也可以基于工程常识生成安全警告和FAQ
- **状态**: ✅ 已实现

#### **代码集成模块**
- **名称**: Manual Data Integrator（手册数据集成器）
- **实现文件**: `core/manual_integrator.py`
- **核心功能**:
  - 整合所有子智能体的输出
  - 生成3D爆炸图参数（自动计算偏移量）
  - 生成最终的JSON数据结构
- **输入**: 所有子智能体的输出
- **输出**: `final_manual.json`（最终装配手册数据）
- **状态**: ✅ 已实现

---

## 数据流架构（分层依赖）

```
PDF工程图纸 + STEP 3D模型
         ↓
    ┌────────────────────────────────────┐
    │  Agent 1: 视觉识别专家 (Qwen-VL)    │
    └────────────────────────────────────┘
         ↓
    vision_channel.json
         ↓
    ┌────────────────────────────────────┐
    │  Agent 2: BOM-3D匹配专家           │
    │  - 代码匹配 (47.6%)                │
    │  - AI智能匹配 (14.2%)              │
    └────────────────────────────────────┘
         ↓
    bom_to_mesh_mapping.json
         ↓
    ┌────────────────────────────────────┐
    │  Agent 3: 装配手册生成专家          │
    │  【第一层：强依赖视觉】             │
    │  ├─ Agent 3-1: 装配步骤 ✅         │
    │  │   └─ 依赖: vision_channel      │
    │  ├─ Agent 3-2: 焊接工艺 ✅         │
    │  │   └─ 依赖: vision_channel      │
    │  ├─ Agent 3-3: 质量控制 ✅         │
    │  │   └─ 依赖: vision_channel      │
    │  │                                 │
    │  【第二层：弱依赖视觉】             │
    │  └─ Agent 3-4: 安全FAQ ✅          │
    │      └─ 主要依赖: Agent 3-1/3-2   │
    │      └─ 可选依赖: vision_channel  │
    └────────────────────────────────────┘
         ↓
    代码集成模块
         ↓
    final_manual.json
         ↓
    前端展示（Vue.js + Three.js）
```

### 依赖关系说明

**强依赖视觉（必须有Qwen-VL输出）：**
- Agent 3-1：装配顺序、装配连接只能从图纸识别
- Agent 3-2：焊接符号、焊接位置只能从图纸识别
- Agent 3-3：尺寸公差、技术要求只能从图纸识别

**弱依赖视觉（可选的视觉信息）：**
- Agent 3-4：主要基于前3个Agent的输出进行推理
  - 即使没有视觉信息，也能基于工程常识生成安全警告和FAQ
  - 图纸上的安全警告是加分项，不是必需项

---

## 提示词文件命名规范

所有提示词文件统一存放在 `prompts/` 目录下，命名规范：

```
agent_{编号}_{功能名称}_prompts.py
```

**示例**:
- `agent_1_vision_prompts.py` - Agent 1视觉识别专家
- `agent_2_ai_bom_matcher_prompts.py` - Agent 2 AI智能匹配
- `agent_3_1_assembly_steps_prompts.py` - Agent 3-1装配步骤生成
- `agent_3_2_welding_prompts.py` - Agent 3-2焊接工艺翻译
- `agent_3_3_quality_control_prompts.py` - Agent 3-3质量控制
- `agent_3_4_safety_faq_prompts.py` - Agent 3-4安全FAQ

---

## 提示词文件结构（5模块标准）

每个提示词文件都遵循统一的5模块结构：

1. **模块1：角色定义** - `{AGENT_NAME}_ROLE`
2. **模块2：教育背景** - `{AGENT_NAME}_EDUCATION`
3. **模块3：职业背景** - `{AGENT_NAME}_EXPERIENCE`
4. **模块4：知识结构** - `{AGENT_NAME}_KNOWLEDGE`
5. **模块5：工作SOP** - `{AGENT_NAME}_SOP`（Chain of Thought形式）

**完整身份组合**: `{AGENT_NAME}_IDENTITY`

**辅助函数**: `build_{function_name}_prompt()` - 构建用户输入

---

## 当前实现状态

| Agent | 状态 | 依赖关系 | 匹配率/完成度 | 备注 |
|-------|------|----------|--------------|------|
| Agent 1 | ✅ 完成 | - | - | 视觉识别专家 |
| Agent 2 | ✅ 完成 | - | 61.8% | 代码+AI混合匹配 |
| Agent 3-1 | ✅ 完成 | ✅ 强依赖视觉 | - | 装配步骤生成 |
| Agent 3-2 | ✅ 完成 | ✅ 强依赖视觉 | - | 焊接工艺翻译 |
| Agent 3-3 | ✅ 完成 | ✅ 强依赖视觉 | - | 质量控制 |
| Agent 3-4 | ✅ 完成 | ⚠️ 弱依赖视觉 | - | 安全FAQ |
| 集成模块 | ✅ 完成 | - | - | 数据集成 |

---

## 下一步工作

1. ✅ 统一提示词管理（已完成）
2. ✅ Agent编号和命名规范（已完成）
3. ✅ 实现Agent 3-2（焊接工艺翻译专家）
4. ✅ 实现Agent 3-3（质量控制专家）
5. ✅ 实现Agent 3-4（安全FAQ生成专家）
6. ✅ 分层依赖架构（已完成）
7. ⏳ 端到端测试
8. ⏳ 前端集成

---

## 技术栈

- **AI模型**: 
  - Qwen3-VL (Alibaba) - 视觉识别
  - DeepSeek - 推理和文本生成
- **后端**: Python, FastAPI
- **前端**: Vue.js 3, TypeScript, Three.js, GSAP
- **3D处理**: trimesh (STEP → GLB)
- **PDF处理**: PyMuPDF, pypdf

