# 更新日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [v0.0.2] - 2025-10-03

### 🎉 重大改进

#### BOM-3D匹配优化
- **匹配率大幅提升**: 产品级匹配率从50.9%提升至92.7%（+41.8%）
- **放开AI输入限制**: 从只传递20个未匹配零件改为传递所有未匹配零件（219个）
  - 利用Gemini 2.5 Flash的100万token上下文能力
  - 确保AI能看到所有候选零件
- **正确计算未匹配BOM**: 修复了重复计算已匹配BOM的问题
  - 在调用AI前先排除已被代码匹配的BOM
  - 减少AI的工作量，提高匹配准确性
- **产品级BOM筛选**: 正确排除组件（从53个减少到41个）
  - 只匹配真正的零件，不匹配组件（assemblies）
  - 提高匹配率计算的准确性

**性能对比**:
| 层级 | v0.0.1 | v0.0.2 | 提升 |
|------|--------|--------|------|
| 组件1 | 33.3% | 100% | +66.7% |
| 组件2 | 70% | 100% | +30% |
| 组件3 | 80% | 93.3% | +13.3% |
| 产品级 | 50.9% | 92.7% | +41.8% |

#### Agent 5和Agent 6架构重构
- **从独立列表改为嵌入式逻辑**:
  - Agent 5（焊接工程师）: 返回`enhanced_steps`，焊接信息嵌入到每个步骤的`welding`字段
  - Agent 6（安全专家）: 返回`enhanced_steps`，安全警告嵌入到每个步骤的`safety_warnings`字段
- **修复组件图片传递问题**:
  - 在组件结果中添加`component_code`、`component_name`、`assembly_order`元数据
  - Agent 5现在可以正确获取组件图片（图片数量从0变为正确值）
- **数据流优化**:
  - Agent 5和Agent 6按顺序增强装配步骤
  - 最终的装配步骤包含完整的焊接和安全信息

**输出格式变化**:
```json
// v0.0.1 (旧格式)
{
  "assembly_steps": [...],
  "welding_requirements": [...],  // 独立列表
  "safety_warnings": [...]        // 独立列表
}

// v0.0.2 (新格式)
{
  "assembly_steps": [
    {
      "step_number": 1,
      "welding": {...},           // 嵌入到步骤中
      "safety_warnings": [...]    // 嵌入到步骤中
    }
  ]
}
```

### ✨ 新增功能

- **前端对接文档**: 新增`API_INTEGRATION_GUIDE.md`，详细说明：
  - 核心入口文件和参数
  - 输出文件位置和结构
  - 日志文件位置
  - 数据结构详解
  - 调用示例代码
- **版本说明文档**: 新增`README_v0.0.2.md`和`CHANGELOG.md`
- **COT推理**: Agent 2增加Chain of Thought推理流程（5步推理）

### 🐛 Bug修复

- **修复Agent 5图片数量为0的问题**:
  - 原因: `component_results`中缺少`assembly_order`字段
  - 解决: 在保存组件结果时添加元数据
  - 影响: Agent 5现在可以正确获取组件图片进行焊接分析
  
- **修复JSON模板花括号转义问题**:
  - 原因: Prompt模板中的JSON示例包含未转义的`{}`，导致`format()`报错
  - 解决: 将所有JSON示例中的`{}`转义为`{{}}`
  - 文件: `prompts/agent_2_bom_3d_matching.py`
  
- **修复产品级BOM筛选逻辑**:
  - 原因: 产品级BOM包含了12个组件（assemblies）
  - 解决: 过滤掉名称中包含'组件'的BOM项
  - 影响: 产品级BOM从53个减少到41个，匹配率计算更准确

### 🗑️ 代码清理

**删除的core文件**:
- `core/hierarchical_bom_matcher.py` (旧版本)
- `core/manual_integrator.py` (旧版本)
- `core/pipeline.py` (旧版本)
- `core/parallel_pipeline.py` (未使用)
- `core/quality_vision_agent.py` (未使用)
- `core/welding_vision_agent.py` (未使用)
- `core/bom_3d_matcher.py` (旧版本)

**删除的测试脚本**:
- `analyze_matching.py`
- `analyze_product_bom.py`
- `debug_check_bom.py`
- `debug_check_product_bom.py`
- `debug_product_matching.py`
- `debug_unmatched.py`
- `test_new_pipeline.py`

**删除的临时文件**:
- `test_output.txt`
- `test_run.log`
- `run_log.txt`
- `run_output.txt`
- `temp_vision_result.json`
- `system_report_20250930_002909.json`

**清理的目录**:
- `debug_output/`: 删除旧的debug文件，只保留最新的
- `uploads/`: 删除UUID命名的测试文件

### 📝 文档更新

- 新增 `API_INTEGRATION_GUIDE.md` - 前端对接完整指南
- 新增 `README_v0.0.2.md` - v0.0.2版本说明
- 新增 `CHANGELOG.md` - 版本更新日志

### 🔧 技术改进

- **Prompt优化**: Agent 2增加COT推理，提高匹配质量
- **数据流完整性**: 确保每个装配步骤都包含完整的3D高亮信息
- **错误处理**: 改进JSON解析错误提示

---

## [v0.0.1] - 2025-10-02

### 🎉 初始版本发布

#### 核心功能
- ✅ 6-Agent架构实现
- ✅ PDF图纸解析（BOM表提取）
- ✅ 3D模型处理（STEP/STL转GLB）
- ✅ BOM-3D匹配（代码匹配+AI匹配）
- ✅ 装配步骤生成（组件级+产品级）
- ✅ 焊接工艺生成
- ✅ 安全警告生成

#### 6个AI Agent
1. **Agent 1 - 视觉规划师**: 分析PDF图纸，识别组件和装配顺序
2. **Agent 2 - BOM-3D匹配**: 智能匹配BOM与3D零件
3. **Agent 3 - 组件装配工程师**: 生成组件装配步骤
4. **Agent 4 - 产品总装工程师**: 生成产品总装步骤
5. **Agent 5 - 焊接工程师**: 识别焊接需求并生成工艺要求
6. **Agent 6 - 安全专家**: 生成安全警告和FAQ

#### 技术栈
- AI模型: Gemini 2.5 Flash (via OpenRouter)
- 3D处理: CadQuery, Trimesh, pygltflib
- PDF处理: pdfplumber
- 后端: Python 3.11+
- 前端: Vue 3 + Three.js

#### 已知问题
- 产品级BOM-3D匹配率偏低（50.9%）
- Agent 5和Agent 6返回独立列表，不便于前端渲染
- 缺少前端对接文档

---

## 版本号说明

版本号格式: `MAJOR.MINOR.PATCH`

- **MAJOR**: 重大架构变更或不兼容的API修改
- **MINOR**: 新增功能，向后兼容
- **PATCH**: Bug修复和小改进，向后兼容

---

## 贡献指南

如果你想为本项目做出贡献，请：

1. Fork本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个Pull Request

---

## 联系方式

- **GitHub**: https://github.com/sga-jerrylin/Mecagent
- **Email**: jerrylin@sologenai.com

