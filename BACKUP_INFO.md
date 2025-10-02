# 🔄 项目备份信息

## 📦 备份仓库
- **GitHub仓库**: https://github.com/sga-jerrylin/Mecagent.git
- **备份时间**: 2025-10-02
- **备份分支**: main
- **提交哈希**: 5e285d6

---

## 📊 备份统计
- **总文件数**: 1524个文件
- **总大小**: 116.91 MB
- **代码行数**: ~50,000+ 行

---

## ⚠️ 注意事项

### 大文件警告
GitHub检测到以下大文件（超过50MB）：
- `step-stl文件/产品测试.STL` - 69.73 MB

**建议**：
- 如果需要频繁更新，考虑使用 [Git LFS](https://git-lfs.github.com/)
- 或者将大文件移到云存储（如阿里云OSS、AWS S3）

---

## 📁 项目结构

```
装修说明书项目/
├── backend/                 # FastAPI后端
│   ├── app.py              # 主应用
│   └── websocket_manager.py # WebSocket管理
├── frontend/               # Vue3前端
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 通用组件
│   │   └── main.ts        # 入口文件
│   └── public/            # 静态资源
├── core/                   # 核心业务逻辑
│   ├── dual_channel_parser.py  # 双通道解析器
│   ├── bom_3d_matcher.py       # BOM-3D匹配
│   └── manual_integrator.py    # 手册集成器
├── models/                 # AI模型封装
│   ├── vision_model.py    # Qwen-VL模型
│   └── assembly_expert.py # DeepSeek模型
├── prompts/               # Agent提示词
│   ├── agent_1_vision_prompts.py
│   ├── agent_2_ai_bom_matcher_prompts.py
│   └── agent_3_*.py
├── processors/            # 文件处理器
│   └── file_processor.py
├── docs/                  # 文档
│   ├── AGENT_ARCHITECTURE.md
│   └── HANDOVER.md
└── 参考项目/              # 参考代码和备份
    └── frontend-old-views/
```

---

## 🚀 核心功能

### 多Agent协作架构
1. **Agent 1**: Qwen-VL视觉识别专家
   - 分析工程图纸
   - 识别BOM表、装配关系、焊接符号

2. **Agent 2**: BOM-3D智能匹配专家
   - 代码匹配（47.6%）
   - AI智能匹配（14.2%）
   - 总匹配率：61.8%

3. **Agent 3**: 装配手册生成专家
   - Agent 3-1: 装配步骤生成
   - Agent 3-2: 焊接工艺翻译
   - Agent 3-3: 质量控制
   - Agent 3-4: 安全FAQ

### 前端特性
- ✅ Vue3 + TypeScript + Three.js
- ✅ 3D模型交互（旋转、缩放、爆炸视图）
- ✅ 图纸查看（点击放大、拖拽移动、滚轮缩放）
- ✅ 实时进度显示（WebSocket）
- ✅ 响应式设计

### 后端特性
- ✅ FastAPI异步框架
- ✅ WebSocket实时通信
- ✅ 并行处理流水线
- ✅ 多PDF支持

---

## 🔧 技术栈

### 前端
- Vue 3.4
- TypeScript
- Element Plus
- Three.js
- GSAP
- Vite

### 后端
- Python 3.13
- FastAPI
- Qwen-VL (Alibaba)
- DeepSeek
- PyMuPDF
- trimesh

---

## 📝 最新更新

### 2025-10-02
1. ✅ **ManualViewer.vue转正处理**
   - 将TestManualViewer.vue替换为正式的ManualViewer.vue
   - 旧版本备份到`参考项目/frontend-old-views/`

2. ✅ **3D模型优化**
   - 天蓝色高对比度显示（#4A90E2）
   - 金属材质优化（metalness: 0.7, roughness: 0.2）
   - 三光源照明系统

3. ✅ **图纸交互功能**
   - 点击放大（2倍）
   - 拖拽移动
   - 滚轮缩放（1-5倍）

4. ✅ **产品信息优化**
   - 从视觉大模型获取产品名称
   - 显示产品类型和工作原理

---

## 🔄 如何恢复备份

```bash
# 克隆仓库
git clone https://github.com/sga-jerrylin/Mecagent.git

# 进入目录
cd Mecagent

# 安装后端依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install

# 启动后端
cd ..
python backend/app.py

# 启动前端（新终端）
cd frontend
npm run dev
```

---

## 📞 联系方式

- **GitHub**: https://github.com/sga-jerrylin
- **项目**: Mecagent - 智能装配说明书生成系统

---

**备份状态**: ✅ 成功  
**最后更新**: 2025-10-02 23:10

