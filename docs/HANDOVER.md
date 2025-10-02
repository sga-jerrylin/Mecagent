# 项目交接文档

**交接时间**: 2025-10-01  
**项目名称**: 智能装配说明书生成系统  
**当前状态**: 开发中，前4个步骤基本完成，存在若干待修复问题

---

## 📋 目录

1. [项目概述](#项目概述)
2. [系统架构](#系统架构)
3. [核心流程](#核心流程)
4. [已完成的工作](#已完成的工作)
5. [当前遗留问题](#当前遗留问题)
6. [关键文件说明](#关键文件说明)
7. [下一步工作建议](#下一步工作建议)

---

## 项目概述

### 项目目标
将PDF工程图纸 + STEP 3D模型 → 自动生成交互式HTML装配说明书

### 技术栈
- **后端**: Python + FastAPI + WebSocket
- **前端**: Vue 3 + TypeScript + Element Plus
- **AI模型**: 
  - Qwen-VL (视觉分析)
  - DeepSeek (智能匹配和推理)
- **3D处理**: trimesh (STEP→GLB转换)

### 核心价值
- 自动化：减少人工编写装配说明书的时间
- 智能化：AI理解图纸和3D模型，自动匹配零件
- 可视化：生成带爆炸动画的交互式说明书

---

## 系统架构

### 后端架构
```
backend/
├── app.py                    # FastAPI主应用，WebSocket服务
├── websocket_manager.py      # WebSocket连接管理
├── core/
│   ├── parallel_pipeline.py  # 并行处理流水线（核心）
│   └── dual_channel_parser.py # 双通道PDF解析（文本+视觉）
├── models/
│   ├── vision_model.py       # Qwen-VL视觉模型封装
│   └── assembly_expert.py    # DeepSeek专家模型封装
├── processors/
│   └── file_processor.py     # PDF和3D模型处理
└── generators/
    └── html_generator.py     # HTML说明书生成
```

### 前端架构
```
frontend/src/
├── views/
│   ├── Generator.vue         # 主生成界面
│   └── Settings.vue          # API密钥配置
└── components/
    └── ProcessingSteps.vue   # 步骤进度展示组件（新）
```

### 数据流
```
用户上传文件
    ↓
FastAPI接收 → 创建任务 → 建立WebSocket
    ↓
ParallelAssemblyPipeline.process()
    ↓
┌─────────────┬─────────────┬─────────────┐
│  通道1      │  通道2      │  通道3      │
│  PDF解析    │  STEP→GLB   │  视觉分析   │
│  (pypdf)    │  (trimesh)  │  (Qwen-VL)  │
└─────────────┴─────────────┴─────────────┘
    ↓
DeepSeek智能匹配 (BOM ↔ GLB零件)
    ↓
生成爆炸动画 + HTML说明书
    ↓
WebSocket推送结果 → 前端展示
```

---

## 核心流程

### 完整的5个步骤

#### **步骤1: pypdf解析BOM**
- **文件**: `processors/file_processor.py` - `PDFProcessor.extract_text()`
- **功能**: 从PDF中提取文本，识别BOM表
- **输出**: 53个BOM项（示例数据）
- **日志**: 
  - `📄 开始PDF文本提取`
  - `✅ PDF文本提取完成: 53个BOM项`

#### **步骤2: STEP→GLB转换 + 解析零件**
- **文件**: `processors/file_processor.py` - `ModelProcessor.step_to_glb()`
- **功能**: 
  1. 使用trimesh将STEP文件转换为GLB格式
  2. 提取零件信息（节点名称、几何体）
- **输出**: GLB文件 + 零件列表
- **日志**:
  - `🔄 开始STEP→GLB转换，共X个文件`
  - `✅ STEP→GLB转换完成: X个文件, 共Y个零件`
- **⚠️ 已修复问题**: 字段名不匹配（`parts_count` vs `part_count`）

#### **步骤3: Qwen-VL视觉分析**
- **文件**: `core/dual_channel_parser.py` - `_vision_channel_parse()`
- **功能**: 
  1. 将PDF每一页转为图片
  2. 结合BOM上下文，调用Qwen-VL分析装配关系
- **输出**: 装配关系、技术要求
- **日志**:
  - `🤖 Qwen-VL视觉智能体启动，分析X页图纸...`
  - `✅ Qwen-VL视觉分析完成: X个装配关系, Y个技术要求`
- **⚠️ 当前问题**: JSON解析失败（见下文）

#### **步骤4: DeepSeek智能匹配**
- **文件**: `core/parallel_pipeline.py` - `_generate_assembly_specification()`
- **功能**: 
  1. 接收BOM数据 + GLB零件数据 + 视觉分析结果
  2. 调用DeepSeek进行智能匹配
  3. 生成装配规范（零件对应关系 + 装配步骤）
- **输出**: 装配规范JSON
- **日志**:
  - `🤖 DeepSeek开始匹配BOM和GLB零件...`
  - `✅ DeepSeek匹配完成: X个零件, Y个装配步骤, 匹配率Z%`
- **⚠️ 当前问题**: 匹配结果显示0（见下文）

#### **步骤5: 生成说明书**
- **文件**: `generators/html_generator.py`
- **功能**: 
  1. 生成爆炸动画数据
  2. 生成HTML交互式说明书
- **输出**: `index.html` + 相关资源
- **状态**: ⏳ 待优化（用户要求最后讨论）

---

## 已完成的工作

### 1. 前端UI重构 ✅
- **新组件**: `frontend/src/components/ProcessingSteps.vue`
- **功能**:
  - 使用Element Plus时间线展示6个步骤
  - 实时显示关键数据（BOM项数、零件数、匹配率等）
  - 实时日志滚动显示
  - 根据日志内容自动更新步骤状态
- **文件修改**:
  - `frontend/src/views/Generator.vue` - 集成新组件，添加`updateStepByLog()`函数

### 2. API密钥配置界面 ✅
- **新页面**: `frontend/src/views/Settings.vue`
- **功能**:
  - 前端输入DashScope和DeepSeek API Key
  - 保存到localStorage
  - 后端API接收并更新环境变量
- **后端API**:
  - `POST /api/settings` - 更新API密钥
  - `GET /api/settings` - 查看当前配置（脱敏）

### 3. WebSocket进度报告 ✅
- **文件**: `backend/websocket_manager.py`
- **修复**: 事件循环错误
  - 使用`asyncio.run_coroutine_threadsafe()`
  - 保存主事件循环引用
- **功能**: 实时推送日志和进度到前端

### 4. 详细日志输出 ✅
- **修改文件**:
  - `core/parallel_pipeline.py` - 添加STEP→GLB转换日志
  - `core/dual_channel_parser.py` - 添加视觉分析日志
- **日志级别**: info, success, warning, error

### 5. 错误处理增强 ⚠️ 部分完成
- **已添加**: 
  - 并行任务异常捕获
  - GLB转换失败检测
  - PDF解析失败检测
- **待完成**: 
  - 视觉分析失败的重试机制
  - 错误时立即停止流程

---

## 当前遗留问题

### 🔴 问题1: Qwen-VL返回JSON解析失败

**错误信息**:
```
[WARNING] ⚠️ Qwen-VL返回的JSON不完整，尝试修复...
[ERROR] ❌ JSON解析失败: Expecting ',' delimiter: line 1024 column 8 (char 19518)
```

**原因分析**:
1. Qwen-VL返回的JSON太长（超过1024行）
2. JSON格式不正确，可能有语法错误
3. 可能被截断

**当前处理**:
- 文件: `core/dual_channel_parser.py` 第381-464行
- 策略: 尝试智能修复，失败后返回空数据
- **问题**: 返回空数据后，没有触发重试机制

**需要修复**:
1. ✅ 添加重试机制（最多3次）
2. ✅ 优化Qwen-VL的prompt，减少返回数据量
3. ✅ 增加max_tokens限制
4. ✅ 如果3次都失败，应该停止流程并报错

**相关代码位置**:
- `core/dual_channel_parser.py` - `_call_assembly_expert_model()` 方法

---

### 🔴 问题2: DeepSeek匹配结果显示0

**错误信息**:
```
✅ DeepSeek匹配完成: 0个零件, 0个装配步骤, 匹配率0.0% (0/53)
```

**原因分析**:
1. DeepSeek返回的JSON结构与代码期望的不一致
2. 字段名可能是 `result.result.parts` 而不是 `result.parts`
3. 或者DeepSeek返回的是其他字段名

**当前代码**:
- 文件: `core/parallel_pipeline.py` 第437-475行
- 尝试读取: `assembly_steps`, `steps`, `parts`, `components`, `bom_mapping`, `mapping`

**需要修复**:
1. ✅ 查看实际的DeepSeek返回数据结构
2. ✅ 检查 `debug_output/assembly_expert_output_*.json` 文件
3. ✅ 根据实际结构调整字段提取逻辑
4. ✅ 添加调试日志，打印完整的返回结构

**调试方法**:
```python
# 在 parallel_pipeline.py 第437行后添加
print(f"[DEBUG] DeepSeek完整返回: {json.dumps(result, indent=2, ensure_ascii=False)}")
```

---

### 🔴 问题3: 步骤报错后继续执行

**用户需求**:
> "我觉得 步骤中有一个环节报错就应该停下来 显示报错信息 而不是一直往下运行"

**当前问题**:
- 视觉分析失败后，返回空数据继续执行
- 应该立即停止并在前端显示错误

**需要修复**:
1. ✅ 修改 `core/parallel_pipeline.py` 第162-169行
2. ✅ 视觉分析失败应该 `raise Exception` 而不是返回空数据
3. ✅ 前端接收到error级别的日志后，停止进度条并显示错误

**相关代码**:
```python
# 当前代码（第162-169行）
try:
    parallel_results["vision"] = future_vision.result()
    if not parallel_results["vision"]:
        # ❌ 不应该继续，应该抛出异常
        self._log("⚠️ 视觉分析未返回结果，将使用空数据继续", "warning")
        parallel_results["vision"] = []
except Exception as e:
    # ❌ 不应该继续，应该抛出异常
    self._log(f"⚠️ 视觉分析失败: {str(e)}，将使用空数据继续", "warning")
    parallel_results["vision"] = []
```

**应该改为**:
```python
try:
    parallel_results["vision"] = future_vision.result()
    if not parallel_results["vision"]:
        raise Exception("视觉分析未返回结果")
except Exception as e:
    error_msg = f"视觉分析失败: {str(e)}"
    self._log(f"❌ {error_msg}", "error")
    raise Exception(error_msg)  # 立即停止
```

---

### 🟡 问题4: 关键信息不够详细

**用户需求**:
> "关键信息我觉得 不够详细 可以把日志中的详细信息 放在每个阶段完成后的关键信息上"

**当前状态**:
- 前端已经添加了 `详细信息` 字段
- 但显示效果可能不够明显

**需要优化**:
1. ✅ 在 `ProcessingSteps.vue` 中，将 `详细信息` 单独显示
2. ✅ 使用更大的字体或不同的颜色
3. ✅ 可以考虑使用折叠面板展示详细信息

---

## 关键文件说明

### 后端核心文件

#### 1. `backend/app.py`
- **作用**: FastAPI主应用
- **关键功能**:
  - `/api/generate` - 启动生成任务
  - `/ws/{task_id}` - WebSocket连接
  - `/api/settings` - API密钥配置
- **关键变量**:
  - `api_keys` - 全局API密钥字典
  - `ws_manager` - WebSocket管理器实例

#### 2. `core/parallel_pipeline.py`
- **作用**: 并行处理流水线（最核心）
- **关键方法**:
  - `process()` - 主流程入口
  - `_process_models_with_progress()` - STEP→GLB转换
  - `_generate_assembly_specification()` - DeepSeek匹配
- **关键变量**:
  - `progress_reporter` - 进度报告器
  - `parallel_results` - 并行任务结果

#### 3. `core/dual_channel_parser.py`
- **作用**: 双通道PDF解析
- **关键方法**:
  - `parse()` - 主入口
  - `_text_channel_parse()` - 文本通道（pypdf）
  - `_vision_channel_parse()` - 视觉通道（Qwen-VL）
  - `_call_assembly_expert_model()` - 调用Qwen-VL
- **⚠️ 问题区域**: 第381-464行（JSON解析）

#### 4. `processors/file_processor.py`
- **作用**: 文件处理
- **关键类**:
  - `PDFProcessor` - PDF处理
  - `ModelProcessor` - 3D模型处理
- **关键方法**:
  - `step_to_glb()` - STEP转GLB
  - **⚠️ 注意**: 返回字段是 `parts_count` 不是 `part_count`

#### 5. `models/assembly_expert.py`
- **作用**: DeepSeek专家模型封装
- **关键方法**:
  - `generate_assembly_specification()` - 生成装配规范
- **返回结构**:
```python
{
    "success": True,
    "result": {
        "assembly_steps": [...],
        "parts": [...],
        "bom_mapping": [...]
    },
    "raw_response": "...",
    "token_usage": {...}
}
```

### 前端核心文件

#### 1. `frontend/src/views/Generator.vue`
- **作用**: 主生成界面
- **关键方法**:
  - `startGeneration()` - 启动生成
  - `connectWebSocket()` - 建立WebSocket
  - `handleWebSocketMessage()` - 处理WebSocket消息
  - `updateStepByLog()` - 根据日志更新步骤状态
- **关键变量**:
  - `processingStepsRef` - 步骤组件引用
  - `processingProgress` - 总进度

#### 2. `frontend/src/components/ProcessingSteps.vue`
- **作用**: 步骤进度展示
- **关键方法**:
  - `addLog()` - 添加日志
  - `updateStep()` - 更新步骤状态
- **步骤ID**:
  - `pdf_text` - PDF文本提取
  - `step_glb` - STEP→GLB转换
  - `vision` - Qwen-VL视觉分析
  - `matching` - DeepSeek智能匹配
  - `explosion` - 生成爆炸动画
  - `html` - 生成HTML说明书

---

## 下一步工作建议

### 优先级1: 修复Qwen-VL JSON解析失败 🔴

**任务清单**:
1. [ ] 添加重试机制（最多3次）
2. [ ] 优化Qwen-VL的prompt，减少返回数据量
3. [ ] 增加`max_tokens`限制（建议4000-6000）
4. [ ] 如果3次都失败，停止流程并报错

**代码位置**: `core/dual_channel_parser.py` - `_call_assembly_expert_model()`

**参考代码**:
```python
def _call_assembly_expert_model(self, ...):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 调用Qwen-VL
            response = self.vision_model.analyze_with_context(...)
            # 解析JSON
            parsed_result = json.loads(json_str)
            return parsed_result  # 成功
        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                self._log(f"⚠️ JSON解析失败，重试 {attempt+1}/{max_retries}...", "warning")
                continue
            else:
                # 最后一次失败，抛出异常
                raise Exception(f"Qwen-VL调用失败（已重试{max_retries}次）: {str(e)}")
```

---

### 优先级2: 修复DeepSeek匹配结果显示0 🔴

**任务清单**:
1. [ ] 查看 `debug_output/assembly_expert_output_*.json` 文件
2. [ ] 打印DeepSeek完整返回结构
3. [ ] 根据实际结构调整字段提取逻辑
4. [ ] 测试并验证匹配率正确显示

**调试代码**:
```python
# 在 core/parallel_pipeline.py 第437行后添加
print(f"[DEBUG] DeepSeek完整返回:")
print(json.dumps(result, indent=2, ensure_ascii=False))

# 在第456行后添加
print(f"[DEBUG] parsed_result类型: {type(parsed_result)}")
print(f"[DEBUG] parsed_result内容: {parsed_result}")
```

---

### 优先级3: 错误时立即停止流程 🔴

**任务清单**:
1. [ ] 修改 `core/parallel_pipeline.py` 第162-169行
2. [ ] 视觉分析失败应该抛出异常
3. [ ] 前端接收error日志后停止进度条
4. [ ] 显示明显的错误提示

**前端修改**:
```typescript
// 在 Generator.vue 的 updateStepByLog() 中
if (level === 'error') {
  // 停止进度
  processingStatus.value = 'exception'
  processingText.value = '处理失败'
  // 显示错误对话框
  ElMessageBox.alert(message, '错误', {
    type: 'error',
    confirmButtonText: '确定'
  })
}
```

---

### 优先级4: 优化关键信息显示 🟡

**任务清单**:
1. [ ] 修改 `ProcessingSteps.vue`
2. [ ] 将 `详细信息` 单独显示
3. [ ] 使用折叠面板或弹出框
4. [ ] 测试显示效果

---

## 测试建议

### 测试步骤
1. 启动后端: `python backend/app.py`
2. 访问前端: `http://localhost:3000`
3. 配置API密钥（Settings页面）
4. 上传测试文件:
   - PDF: 工程图纸
   - STEP: 3D模型
5. 观察日志和步骤进度
6. 检查是否有错误

### 测试重点
- [ ] Qwen-VL是否成功返回数据
- [ ] DeepSeek匹配率是否正确显示
- [ ] 错误时是否立即停止
- [ ] 前端步骤状态是否正确更新

---

## 联系信息

如有问题，请查看以下文档：
- `docs/workflow_summary.md` - 完整流程梳理
- `docs/api_key_setup.md` - API密钥配置指南
- `docs/websocket_fix.md` - WebSocket修复说明

**祝下一位Agent工作顺利！** 🚀

