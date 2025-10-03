# 装配说明书自动生成系统

**版本**: v0.0.2  
**状态**: 生产就绪  
**最后更新**: 2025-10-03

基于Gemini 2.5 Flash的6-Agent智能装配说明书生成系统，支持从PDF图纸和3D模型自动生成完整的装配说明书。

---

## 🎯 核心功能

- ✅ **PDF图纸解析**: 自动提取BOM表和装配信息
- ✅ **3D模型处理**: STEP/STL转GLB，支持零件高亮
- ✅ **BOM-3D匹配**: 智能匹配BOM与3D零件（匹配率92.7%+）
- ✅ **装配步骤生成**: AI生成详细的装配步骤
- ✅ **焊接工艺**: 自动识别焊接需求并生成工艺要求
- ✅ **安全警告**: 为每个步骤生成安全注意事项
- ✅ **3D可视化**: 支持前端3D交互展示

---

## 📚 快速开始

### 前端开发人员

请查看 **[API_INTEGRATION_GUIDE.md](./API_INTEGRATION_GUIDE.md)** 了解：
- 核心入口文件和调用方法
- 输入参数说明
- 输出文件位置
- 数据结构详解
- 调用示例代码

### 后端开发人员

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置API密钥
# 编辑 config.py，设置 OPENROUTER_API_KEY

# 3. 准备输入文件
# 将PDF图纸放到 测试-pdf/ 目录
# 将STEP模型放到 step-stl文件/ 目录

# 4. 运行主程序
python core/gemini_pipeline.py

# 5. 查看结果
# 装配说明书: pipeline_output/assembly_manual.json
# 3D模型: pipeline_output/glb_files/*.glb
```

---

## 📁 项目结构

```
装修说明书项目/
├── core/                          # 核心代码
│   ├── gemini_pipeline.py        # ⭐ 主程序入口
│   ├── ai_matcher.py             # AI智能匹配
│   ├── hierarchical_bom_matcher_v2.py  # 分层级BOM匹配
│   ├── manual_integrator_v2.py   # 说明书整合
│   ├── dual_channel_parser.py    # PDF解析
│   └── file_classifier.py        # 文件分类
├── agents/                        # 6个AI Agent
│   ├── base_gemini_agent.py      # Agent基类
│   ├── vision_planning_agent.py  # Agent 1: 视觉规划
│   ├── component_assembly_agent.py  # Agent 3: 组件装配
│   ├── product_assembly_agent.py    # Agent 4: 产品总装
│   ├── welding_agent.py          # Agent 5: 焊接工程师
│   └── safety_faq_agent.py       # Agent 6: 安全专家
├── prompts/                       # AI提示词
│   ├── agent_1_vision_planning.py
│   ├── agent_2_bom_3d_matching.py
│   ├── agent_3_component_assembly.py
│   ├── agent_4_product_assembly.py
│   ├── agent_5_welding.py
│   └── agent_6_safety_faq.py
├── models/                        # AI模型封装
│   └── gemini_model.py
├── utils/                         # 工具函数
│   └── logger.py
├── pipeline_output/               # ⭐ 输出目录
│   ├── assembly_manual.json      # ⭐ 最终装配说明书
│   ├── glb_files/                # ⭐ 3D模型文件
│   ├── pdf_images/               # PDF转图片
│   └── step*.json                # 中间结果文件
├── debug_output/                  # Debug日志
├── 测试-pdf/                      # 输入: PDF图纸
│   ├── 产品总图.pdf
│   ├── 组件图1.pdf
│   ├── 组件图2.pdf
│   └── 组件图3.pdf
├── step-stl文件/                  # 输入: 3D模型
│   ├── 产品测试.STEP
│   ├── 组件图1.STEP
│   ├── 组件图2.STEP
│   └── 组件图3.STEP
├── frontend/                      # 前端代码
├── docs/                          # 文档
├── config.py                      # 配置文件
├── requirements.txt               # Python依赖
├── API_INTEGRATION_GUIDE.md      # ⭐ 前端对接指南
└── README.md                      # 本文件
```

---

## 🔧 技术栈

### 后端
- **AI模型**: Gemini 2.5 Flash (via OpenRouter)
- **3D处理**: CadQuery, Trimesh, pygltflib
- **PDF处理**: pdfplumber
- **语言**: Python 3.11+

### 前端
- **框架**: Vue 3 + TypeScript
- **3D渲染**: Three.js
- **UI组件**: Element Plus
- **构建工具**: Vite

---

## 📊 性能指标

| 指标 | 数值 |
|------|------|
| **BOM-3D匹配率（组件级）** | 100% |
| **BOM-3D匹配率（产品级）** | 92.7% |
| **平均处理时间** | ~5分钟 |
| **支持的零件数量** | 400+ |
| **支持的组件数量** | 无限制 |

---

## 📖 详细文档

| 文档 | 说明 | 适用对象 |
|------|------|---------|
| [API对接指南](./API_INTEGRATION_GUIDE.md) | 核心API、数据结构、调用示例 | 前端开发 |
| [系统架构](./docs/AGENT_ARCHITECTURE.md) | 6-Agent架构说明 | 后端开发 |
| [BOM匹配指南](./docs/BOM_3D_MATCHING_GUIDE.md) | 匹配算法详解 | 后端开发 |
| [前端说明](./README_FRONTEND.md) | 前端开发指南 | 前端开发 |

---

## 🚀 版本历史

### v0.0.2 (2025-10-03)

**重大改进**:
- ✅ **BOM-3D匹配优化**: 匹配率从50.9%提升至92.7%（+41.8%）
  - 放开AI输入限制（20个→全部）
  - 正确计算未匹配BOM
  - 产品级BOM排除组件（53→41个）
  
- ✅ **Agent 5和Agent 6重构**: 
  - 从独立列表改为嵌入式逻辑
  - 焊接和安全信息直接嵌入装配步骤
  - 修复组件图片传递问题

- ✅ **代码清理**:
  - 删除无用的core文件（7个）
  - 清理debug输出文件
  - 清理测试脚本

- ✅ **文档完善**:
  - 新增API对接指南
  - 更新README
  - 完善数据结构说明

**Bug修复**:
- 🐛 修复Agent 5图片数量为0的问题
- 🐛 修复JSON模板花括号转义问题
- 🐛 修复产品级BOM筛选逻辑

### v0.0.1 (2025-10-02)
- 初始版本发布
- 6-Agent架构实现
- 基础BOM-3D匹配功能

---

## 🛠️ 开发指南

### 环境要求

- Python 3.11+
- Node.js 18+ (前端开发)
- 8GB+ RAM
- 支持OpenGL的显卡（3D渲染）

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/sga-jerrylin/Mecagent.git
cd Mecagent

# 2. 安装Python依赖
pip install -r requirements.txt

# 3. 配置API密钥
# 编辑 config.py
OPENROUTER_API_KEY = "your_api_key_here"

# 4. 测试运行
python core/gemini_pipeline.py
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

---

## 📞 技术支持

### 常见问题

**Q: 如何提高BOM-3D匹配率？**  
A: 确保3D模型的零件名称包含产品代号或规格信息。

**Q: 支持哪些3D格式？**  
A: 推荐STEP格式，也支持STL格式。

**Q: 如何调试匹配失败的零件？**  
A: 查看 `debug_output/ai_matching_response_*.txt` 文件。

### 联系方式

- **GitHub Issues**: https://github.com/sga-jerrylin/Mecagent/issues
- **Email**: jerrylin@sologenai.com

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](./LICENSE) 文件。

---

## 🙏 致谢

- Gemini 2.5 Flash by Google
- OpenRouter API
- CadQuery Community
- Three.js Team

