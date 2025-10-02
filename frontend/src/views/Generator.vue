<template>
  <div class="generator-page">
    <div class="container">
      <!-- 页面标题 -->
      <div class="page-header">
        <h1>智能装配说明书生成器</h1>
        <p>上传PDF工程图纸和3D模型，AI将自动生成专业的装配说明书</p>
      </div>

      <!-- 生成步骤 -->
      <div class="generation-steps">
        <el-steps :active="currentStep" align-center>
          <el-step title="上传文件" icon="Upload" />
          <el-step title="AI解析" icon="Cpu" />
          <el-step title="工艺生成" icon="Setting" />
          <el-step title="3D处理" icon="Monitor" />
          <el-step title="完成" icon="Check" />
        </el-steps>
      </div>

      <!-- 步骤内容 -->
      <div class="step-content">
        <!-- 步骤1: 文件上传 -->
        <div v-show="currentStep === 0" class="step-panel">
          <div class="upload-section">
            <div class="upload-grid">
              <!-- PDF上传 -->
              <div class="upload-card">
                <h3>
                  <el-icon><Document /></el-icon>
                  工程图纸 (PDF)
                </h3>
                <el-upload
                  ref="pdfUploadRef"
                  class="upload-dragger"
                  drag
                  :auto-upload="false"
                  :multiple="true"
                  accept=".pdf"
                  :on-change="handlePdfChange"
                  :file-list="pdfFiles"
                >
                  <el-icon class="upload-icon"><UploadFilled /></el-icon>
                  <div class="upload-text">
                    <p>拖拽PDF文件到此处，或<em>点击上传</em></p>
                    <p class="upload-hint">支持多个PDF文件，单个文件不超过50MB</p>
                  </div>
                </el-upload>
                
                <!-- PDF文件列表 -->
                <div class="file-list" v-if="pdfFiles.length">
                  <h4>已选择的PDF文件:</h4>
                  <div class="file-item" v-for="file in pdfFiles" :key="file.uid">
                    <el-icon><Document /></el-icon>
                    <span class="file-name">{{ file.name }}</span>
                    <span class="file-size">{{ formatFileSize(file.size) }}</span>
                    <el-button 
                      type="danger" 
                      text 
                      @click="removePdfFile(file)"
                      :icon="Delete"
                    />
                  </div>
                </div>
              </div>

              <!-- 3D模型上传 -->
              <div class="upload-card">
                <h3>
                  <el-icon><Box /></el-icon>
                  3D模型 (STEP格式)
                </h3>
                <el-upload
                  ref="modelUploadRef"
                  class="upload-dragger"
                  drag
                  :auto-upload="false"
                  :multiple="true"
                  accept=".step,.stp"
                  :on-change="handleModelChange"
                  :file-list="modelFiles"
                >
                  <el-icon class="upload-icon"><Box /></el-icon>
                  <div class="upload-text">
                    <p>拖拽STEP模型文件到此处，或<em>点击上传</em></p>
                    <p class="upload-hint">仅支持STEP格式 (.step, .stp)，单个文件不超过100MB</p>
                  </div>
                </el-upload>
                
                <!-- 模型文件列表 -->
                <div class="file-list" v-if="modelFiles.length">
                  <h4>已选择的模型文件:</h4>
                  <div class="file-item" v-for="file in modelFiles" :key="file.uid">
                    <el-icon><Box /></el-icon>
                    <span class="file-name">{{ file.name }}</span>
                    <span class="file-size">{{ formatFileSize(file.size) }}</span>
                    <el-button 
                      type="danger" 
                      text 
                      @click="removeModelFile(file)"
                      :icon="Delete"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- 配置选项 -->
            <div class="config-section">
              <h3>生成配置</h3>
              <div class="config-grid">
                <div class="config-item">
                  <label>专业重点</label>
                  <el-select v-model="config.focus" placeholder="选择专业重点">
                    <el-option label="通用装配" value="general" />
                    <el-option label="焊接重点" value="welding" />
                    <el-option label="精密装配" value="precision" />
                    <el-option label="重型装配" value="heavy" />
                  </el-select>
                </div>
                
                <div class="config-item">
                  <label>质量等级</label>
                  <el-select v-model="config.quality" placeholder="选择质量等级">
                    <el-option label="基础质量" value="basic" />
                    <el-option label="标准质量" value="standard" />
                    <el-option label="高质量" value="high" />
                    <el-option label="关键质量" value="critical" />
                  </el-select>
                </div>
                
                <div class="config-item">
                  <label>输出语言</label>
                  <el-select v-model="config.language" placeholder="选择输出语言">
                    <el-option label="中文" value="zh" />
                    <el-option label="English" value="en" />
                  </el-select>
                </div>
              </div>
              
              <div class="config-item full-width">
                <label>特殊要求</label>
                <el-input
                  v-model="config.requirements"
                  type="textarea"
                  :rows="3"
                  placeholder="请描述特殊的装配要求或注意事项..."
                />
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="step-actions">
              <el-button 
                type="primary" 
                size="large"
                @click="startGeneration"
                :disabled="!canStartGeneration"
                :loading="isGenerating"
              >
                <el-icon><Right /></el-icon>
                开始生成
              </el-button>
            </div>
          </div>
        </div>

        <!-- 步骤2-4: 处理中 -->
        <div v-show="currentStep >= 1 && currentStep <= 4" class="step-panel">
          <ProcessingSteps
            :progress="processingProgress"
            :message="processingText"
            :stage="currentProcessingStage"
            ref="processingStepsRef"
          />
        </div>

        <!-- 步骤5: 完成 -->
        <div v-show="currentStep === 5" class="step-panel">
          <div class="result-section">
            <div class="result-header">
              <el-icon class="success-icon" size="64"><CircleCheck /></el-icon>
              <h2>装配说明书生成完成！</h2>
              <p>您的智能装配说明书已成功生成，可以预览和下载。</p>
            </div>
            
            <div class="result-actions">
              <el-button 
                type="primary" 
                size="large"
                @click="previewResult"
              >
                <el-icon><View /></el-icon>
                预览说明书
              </el-button>
              
              <el-button 
                size="large"
                @click="downloadResult"
              >
                <el-icon><Download /></el-icon>
                下载文件
              </el-button>
              
              <el-button 
                size="large"
                @click="shareResult"
              >
                <el-icon><Share /></el-icon>
                分享链接
              </el-button>
            </div>
            
            <!-- 结果统计 -->
            <div class="result-stats">
              <div class="stat-item">
                <div class="stat-number">{{ resultStats.pdfPages }}</div>
                <div class="stat-label">PDF页数</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ resultStats.bomItems }}</div>
                <div class="stat-label">BOM项目</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ resultStats.assemblySteps }}</div>
                <div class="stat-label">装配步骤</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ resultStats.processingTime }}</div>
                <div class="stat-label">处理时间(秒)</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadFile, UploadFiles } from 'element-plus'
import {
  Document, UploadFilled, Right, CircleCheck,
  Download, View, Delete, Share, Box
} from '@element-plus/icons-vue'
import ProcessingSteps from '../components/ProcessingSteps.vue'
import axios from 'axios'

// 响应式数据
const currentStep = ref(0)
const isGenerating = ref(false)
const showLogs = ref(false)

const pdfFiles = ref<UploadFiles>([])
const modelFiles = ref<UploadFiles>([])

const config = reactive({
  focus: 'welding',
  quality: 'standard',
  language: 'zh',
  requirements: ''
})

const processingProgress = ref(0)
const processingStatus = ref<'success' | 'exception' | undefined>()
const processingText = ref('')

// 新增：可视化处理相关数据
const currentProcessingStage = ref('pdf_bom') // pdf_bom, parallel, matching, generate
const processingData = ref({})
const processingStepsRef = ref()
const taskId = ref('')
const generatedManualUrl = ref('')

const processingLogs = ref<Array<{
  id: number
  time: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
}>>([])

const resultStats = reactive({
  pdfPages: 0,
  bomItems: 0,
  assemblySteps: 0,
  processingTime: 0
})

// 处理步骤配置
const processingSteps = [
  {
    title: 'AI视觉解析中...',
    description: 'Qwen3-VL模型正在分析您的工程图纸，识别BOM表格、技术要求和尺寸标注'
  },
  {
    title: '专家工艺生成中...',
    description: 'DeepSeek专家模型正在基于解析结果生成专业的装配工艺规程'
  },
  {
    title: '3D模型处理中...',
    description: 'Blender正在自动转换和优化您的3D模型，生成Web友好的格式'
  },
  {
    title: '装配说明书生成中...',
    description: '正在整合所有信息，生成最终的交互式装配说明书'
  }
]

// 计算属性
const canStartGeneration = computed(() => {
  return pdfFiles.value.length > 0 && modelFiles.value.length > 0
})

// 方法
const handlePdfChange = (file: UploadFile, fileList: UploadFiles) => {
  pdfFiles.value = fileList
}

const handleModelChange = (file: UploadFile, fileList: UploadFiles) => {
  modelFiles.value = fileList
}

const removePdfFile = (file: UploadFile) => {
  const index = pdfFiles.value.indexOf(file)
  if (index > -1) {
    pdfFiles.value.splice(index, 1)
  }
}

const removeModelFile = (file: UploadFile) => {
  const index = modelFiles.value.indexOf(file)
  if (index > -1) {
    modelFiles.value.splice(index, 1)
  }
}

const formatFileSize = (size: number) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  return (size / (1024 * 1024)).toFixed(1) + ' MB'
}

const startGeneration = async () => {
  // 验证文件
  if (pdfFiles.value.length === 0 && modelFiles.value.length === 0) {
    ElMessage.warning('请至少上传一个PDF文件或3D模型文件')
    return
  }

  isGenerating.value = true
  currentStep.value = 1
  processingStatus.value = undefined
  processingProgress.value = 0
  processingText.value = '准备上传文件...'

  // 清空之前的日志
  processingLogs.value = []

  try {
    // 1. 上传文件
    currentStep.value = 2
    processingStepsRef.value?.addLog('📤 开始上传文件...', 'info')
    await uploadFiles()
    processingStepsRef.value?.addLog('✅ 文件上传完成', 'success')

    // 2. 启动并行处理（会自动建立WebSocket连接）
    currentStep.value = 3
    processingText.value = '启动并行处理流水线...'
    processingStepsRef.value?.addLog('🚀 启动生产级并行处理流水线', 'info')

    await startGenerationTask()

    // WebSocket会处理后续的进度更新和完成通知
    // 不需要在这里设置完成状态

  } catch (error: any) {
    console.error('生成失败:', error)
    ElMessage.error('生成失败: ' + (error.message || '未知错误'))
    processingStatus.value = 'exception'
    processingText.value = '生成失败'
    processingStepsRef.value?.addLog(`❌ 生成失败: ${error.message}`, 'error')
    isGenerating.value = false

    // 关闭WebSocket
    if (ws) {
      ws.close()
      ws = null
    }
  }
}

// 上传文件到后端
const uploadFiles = async () => {
  const formData = new FormData()

  // 添加PDF文件
  pdfFiles.value.forEach(file => {
    if (file.raw) {
      formData.append('pdf_files', file.raw)
    }
  })

  // 添加3D模型文件
  modelFiles.value.forEach(file => {
    if (file.raw) {
      formData.append('model_files', file.raw)
    }
  })

  const response = await axios.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })

  if (!response.data.success) {
    throw new Error('文件上传失败')
  }

  return response.data.data
}

// WebSocket连接
let ws: WebSocket | null = null

// 开始生成任务 - 使用WebSocket实时更新
const startGenerationTask = async () => {
  const response = await axios.post('/api/generate', {
    config: {
      focus: config.focus,
      quality: config.quality,
      language: config.language,
      requirements: config.requirements
    },
    pdf_files: pdfFiles.value.map(f => f.name),
    model_files: modelFiles.value.map(f => f.name)
  })

  if (!response.data.success) {
    throw new Error('生成失败: ' + (response.data.detail || '未知错误'))
  }

  const newTaskId = response.data.task_id
  taskId.value = newTaskId

  // 建立WebSocket连接
  connectWebSocket(newTaskId)

  return newTaskId
}

// 连接WebSocket
const connectWebSocket = (taskId: string) => {
  const wsUrl = `ws://localhost:8000/ws/task/${taskId}`
  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    console.log('WebSocket连接已建立')
    processingStepsRef.value?.addLog('✅ WebSocket连接成功', 'success')
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    handleWebSocketMessage(data)
  }

  ws.onerror = (error) => {
    console.error('WebSocket错误:', error)
    processingStepsRef.value?.addLog('❌ WebSocket连接错误', 'error')
  }

  ws.onclose = () => {
    console.log('WebSocket连接已关闭')
  }
}

// 处理WebSocket消息
const handleWebSocketMessage = (data: any) => {
  console.log('收到WebSocket消息:', data)

  switch (data.type) {
    case 'initial_state':
      // 初始状态
      if (data.data) {
        Object.keys(data.data).forEach(stage => {
          updateProcessingData(stage, data.data[stage])
        })
      }
      break

    case 'progress_update':
      // 进度更新
      currentProcessingStage.value = data.stage
      processingProgress.value = data.progress
      processingText.value = data.message

      if (data.data) {
        updateProcessingData(data.stage, data.data)
      }
      break

    case 'parallel_progress':
      // 并行处理进度
      currentProcessingStage.value = 'parallel'
      processingData.value = {
        ...processingData.value,
        parallel_progress: data.parallel_data,
        stage_data: data.parallel_data
      }

      // 计算总体进度
      const avgProgress = Object.values(data.parallel_data).reduce((sum: number, item: any) => {
        return sum + (item.progress || 0)
      }, 0) / Object.keys(data.parallel_data).length
      processingProgress.value = Math.round(avgProgress)
      break

    case 'log':
      // 日志消息
      processingStepsRef.value?.addLog(data.message, data.level)

      // 根据日志内容更新步骤状态
      updateStepByLog(data.message, data.level)
      break

    case 'completion':
      // 任务完成
      if (data.success) {
        processingProgress.value = 100
        processingStatus.value = 'success'
        processingText.value = '生成完成！'
        currentStep.value = 4

        // 更新结果统计
        if (data.result) {
          resultStats.pdfPages = data.result.statistics?.pdf_count || 0
          resultStats.bomItems = data.result.statistics?.bom_items || 0
          resultStats.assemblySteps = data.result.statistics?.assembly_steps || 0
          generatedManualUrl.value = data.result.output_file || ''
        }

        processingStepsRef.value?.addLog('✅ 装配说明书生成完成！', 'success')

        // 提示用户并跳转到查看器
        ElMessage.success({
          message: '装配说明书生成完成！即将跳转到查看器...',
          duration: 2000
        })

        setTimeout(() => {
          router.push(`/manual/${taskId.value}`)
        }, 2000)
      } else {
        processingStatus.value = 'exception'
        processingText.value = data.error || '生成失败'
        processingStepsRef.value?.addLog(`❌ ${data.error}`, 'error')
      }

      // 关闭WebSocket
      if (ws) {
        ws.close()
        ws = null
      }
      isGenerating.value = false
      break
  }
}

// 删除复杂的监控逻辑，现在是同步处理

// 更新处理数据用于可视化
const updateProcessingData = (stage: string, taskData: any) => {
  console.log('更新处理数据:', stage, taskData)

  const data = { ...processingData.value }

  // 处理并行进度数据
  if (taskData.parallel_progress) {
    data.parallel_progress = taskData.parallel_progress
  }

  // 处理阶段数据
  if (taskData.stage_data) {
    data.stage_data = taskData.stage_data
  }

  switch (stage) {
    case 'pdf_bom':
      // 阶段1: PDF解析 - 提取BOM表
      data.pdf_bom = {
        ...data.pdf_bom,
        ...taskData
      }
      break
    case 'parallel':
      // 阶段2: 并行处理
      data.pdf_deep = taskData.pdf_deep
      data.step_extract = taskData.step_extract
      break
    case 'matching':
      // 阶段3: BOM-STEP匹配
      data.matching = {
        ...data.matching,
        ...taskData
      }
      break
    case 'generate':
      // 阶段4: 生成说明书
      data.generate = {
        ...data.generate,
        ...taskData
      }
      break
    case 'pdf':
      data.files = taskData.pdf_analysis || []
      break
    case 'model':
      data.models = taskData.model_conversion || []
      break
    case 'ai':
      data.aiProgress = taskData.ai_progress || { vision: 0, expert: 0 }
      data.visionResults = taskData.vision_results || []
      data.expertInsights = taskData.expert_insights || []
      break
  }

  if (taskData.logs) {
    data.logs = taskData.logs
  }

  processingData.value = data
}

// 根据日志内容更新步骤状态
const updateStepByLog = (message: string, level: string) => {
  const msg = message.toLowerCase()

  // ✅ 修复: 如果是错误日志，立即停止流程并显示错误
  if (level === 'error') {
    processingStatus.value = 'exception'
    processingText.value = '处理失败'
    isGenerating.value = false

    // 显示错误对话框
    ElMessageBox.alert(message, '处理失败', {
      type: 'error',
      confirmButtonText: '确定'
    })

    return  // 不再继续更新步骤
  }

  // 步骤1: PDF文本提取
  if (msg.includes('开始pdf文本提取')) {
    processingStepsRef.value?.updateStep('pdf_text', 'active')
  } else if (msg.includes('pdf文本提取完成')) {
    const match = message.match(/(\d+)个BOM项/)
    const data = match ? {
      'BOM项数': match[1],
      '详细信息': message
    } : {}
    processingStepsRef.value?.updateStep('pdf_text', 'complete', data)
  }

  // 步骤2: STEP→GLB转换
  else if (msg.includes('开始step→glb转换')) {
    processingStepsRef.value?.updateStep('step_glb', 'active')
  } else if (msg.includes('step→glb转换完成')) {
    const fileMatch = message.match(/(\d+)个文件/)
    const partMatch = message.match(/共(\d+)个零件/)
    const data: Record<string, any> = {}
    if (fileMatch) data['文件数'] = fileMatch[1]
    if (partMatch) data['零件总数'] = partMatch[1]
    data['详细信息'] = message
    processingStepsRef.value?.updateStep('step_glb', 'complete', data)
  }

  // 步骤3: Qwen-VL视觉分析
  else if (msg.includes('qwen-vl视觉智能体启动')) {
    processingStepsRef.value?.updateStep('vision', 'active')
  } else if (msg.includes('qwen-vl视觉分析完成') || msg.includes('qwen-vl返回数据解析成功')) {
    const relationMatch = message.match(/(\d+)个装配关系/)
    const reqMatch = message.match(/(\d+)个技术要求/)
    const data: Record<string, any> = {}
    if (relationMatch) data['装配关系'] = relationMatch[1]
    if (reqMatch) data['技术要求'] = reqMatch[1]
    if (Object.keys(data).length > 0) {
      data['详细信息'] = message
      processingStepsRef.value?.updateStep('vision', 'complete', data)
    }
  }

  // 步骤4: DeepSeek智能匹配
  else if (msg.includes('deepseek开始匹配') || msg.includes('调用deepseek专家模型')) {
    processingStepsRef.value?.updateStep('matching', 'active')
  } else if (msg.includes('deepseek匹配完成')) {
    const partMatch = message.match(/(\d+)个零件/)
    const stepMatch = message.match(/(\d+)个装配步骤/)
    const rateMatch = message.match(/匹配率([\d.]+)%/)
    const matchedMatch = message.match(/\((\d+)\/(\d+)\)/)

    const data: Record<string, any> = {}
    if (partMatch) data['零件数'] = partMatch[1]
    if (stepMatch) data['装配步骤'] = stepMatch[1]
    if (rateMatch) data['匹配率'] = rateMatch[1] + '%'
    if (matchedMatch) data['匹配情况'] = `${matchedMatch[1]}/${matchedMatch[2]}`
    data['详细信息'] = message
    processingStepsRef.value?.updateStep('matching', 'complete', data)
  }

  // 步骤5: 生成爆炸动画
  else if (msg.includes('生成glb爆炸动画')) {
    processingStepsRef.value?.updateStep('explosion', 'active')
  } else if (msg.includes('成功生成') && msg.includes('爆炸动画')) {
    const match = message.match(/(\d+)个零件/)
    const data = match ? {
      '零件数': match[1],
      '详细信息': message
    } : {}
    processingStepsRef.value?.updateStep('explosion', 'complete', data)
  }

  // 步骤6: 生成HTML说明书
  else if (msg.includes('生成html装配说明书')) {
    processingStepsRef.value?.updateStep('html', 'active')
  } else if (msg.includes('处理完成')) {
    processingStepsRef.value?.updateStep('html', 'complete', {
      '详细信息': message
    })
  }
}

// 处理阶段完成回调
const handleStageComplete = (stage: string) => {
  processingStepsRef.value?.addLog(`${stage}阶段处理完成`, 'success')
}

const previewResult = () => {
  if (generatedManualUrl.value) {
    window.open(generatedManualUrl.value, '_blank')
  } else {
    ElMessage.warning('说明书还未生成完成')
  }
  router.push('/viewer/demo')
}

const downloadResult = () => {
  ElMessage.info('下载功能开发中...')
}

const shareResult = () => {
  ElMessage.info('分享功能开发中...')
}

// 路由
const router = useRouter()

// 组件卸载时清理WebSocket
onUnmounted(() => {
  if (ws) {
    ws.close()
    ws = null
  }
})
</script>

<style lang="scss" scoped>
.generator-page {
  min-height: 100vh;
  padding: 40px 0;
  
  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px;
  }
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
  
  h1 {
    font-size: 2.5rem;
    font-weight: 600;
    margin-bottom: 16px;
    background: linear-gradient(135deg, #409eff, #67c23a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  p {
    font-size: 1.1rem;
    color: var(--el-text-color-secondary);
  }
}

.generation-steps {
  margin-bottom: 60px;
}

.step-content {
  .step-panel {
    min-height: 500px;
  }
}

.upload-section {
  .upload-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 32px;
    margin-bottom: 40px;
    
    .upload-card {
      background: var(--el-bg-color);
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
      
      h3 {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 20px;
        color: var(--el-text-color-primary);
      }
      
      .upload-dragger {
        width: 100%;
        
        :deep(.el-upload-dragger) {
          width: 100%;
          height: 200px;
          border: 2px dashed var(--el-border-color);
          border-radius: 12px;
          background: var(--el-fill-color-lighter);
          transition: all 0.3s ease;
          
          &:hover {
            border-color: var(--el-color-primary);
            background: var(--el-color-primary-light-9);
          }
        }
        
        .upload-icon {
          font-size: 48px;
          color: var(--el-color-primary);
          margin-bottom: 16px;
        }
        
        .upload-text {
          p {
            margin: 8px 0;
            
            &.upload-hint {
              font-size: 12px;
              color: var(--el-text-color-secondary);
            }
          }
          
          em {
            color: var(--el-color-primary);
            font-style: normal;
          }
        }
      }
      
      .file-list {
        margin-top: 20px;
        
        h4 {
          margin-bottom: 12px;
          color: var(--el-text-color-primary);
        }
        
        .file-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: var(--el-fill-color-light);
          border-radius: 8px;
          margin-bottom: 8px;
          
          .file-name {
            flex: 1;
            font-size: 14px;
          }
          
          .file-size {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
      }
    }
  }
  
  .config-section {
    background: var(--el-bg-color);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 40px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    
    h3 {
      margin-bottom: 20px;
      color: var(--el-text-color-primary);
    }
    
    .config-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
      margin-bottom: 20px;
    }
    
    .config-item {
      &.full-width {
        grid-column: 1 / -1;
      }
      
      label {
        display: block;
        margin-bottom: 8px;
        font-weight: 500;
        color: var(--el-text-color-primary);
      }
    }
  }
  
  .step-actions {
    text-align: center;
  }
}

.processing-section {
  display: flex;
  align-items: center;
  gap: 60px;
  
  .processing-visual {
    flex-shrink: 0;
    
    .processing-animation {
      width: 300px;
      height: 300px;
      background: radial-gradient(circle, rgba(64, 158, 255, 0.1), transparent);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
  
  .processing-info {
    flex: 1;
    
    h3 {
      font-size: 1.8rem;
      margin-bottom: 16px;
      color: var(--el-text-color-primary);
    }
    
    p {
      font-size: 1.1rem;
      color: var(--el-text-color-secondary);
      line-height: 1.6;
      margin-bottom: 32px;
    }
    
    .progress-section {
      margin-bottom: 32px;
      
      .progress-text {
        margin-top: 12px;
        text-align: center;
        color: var(--el-text-color-secondary);
      }
    }
    
    .log-section {
      h4 {
        margin-bottom: 12px;
        color: var(--el-text-color-primary);
      }
      
      .log-container {
        max-height: 200px;
        overflow-y: auto;
        background: var(--el-fill-color-darker);
        border-radius: 8px;
        padding: 12px;
        
        .log-item {
          display: flex;
          gap: 12px;
          margin-bottom: 8px;
          font-family: monospace;
          font-size: 12px;
          
          .log-time {
            color: var(--el-text-color-secondary);
            flex-shrink: 0;
          }
          
          .log-message {
            flex: 1;
          }
          
          &.info { color: var(--el-color-info); }
          &.success { color: var(--el-color-success); }
          &.warning { color: var(--el-color-warning); }
          &.error { color: var(--el-color-danger); }
        }
      }
    }
  }
}

.result-section {
  text-align: center;
  
  .result-header {
    margin-bottom: 40px;
    
    .success-icon {
      color: var(--el-color-success);
      margin-bottom: 20px;
    }
    
    h2 {
      font-size: 2rem;
      margin-bottom: 16px;
      color: var(--el-text-color-primary);
    }
    
    p {
      font-size: 1.1rem;
      color: var(--el-text-color-secondary);
    }
  }
  
  .result-actions {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-bottom: 60px;
  }
  
  .result-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 32px;
    
    .stat-item {
      .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--el-color-primary);
        margin-bottom: 8px;
      }
      
      .stat-label {
        color: var(--el-text-color-secondary);
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .upload-grid {
    grid-template-columns: 1fr !important;
  }
  
  .processing-section {
    flex-direction: column;
    gap: 40px;
    text-align: center;
  }
  
  .result-actions {
    flex-direction: column;
    align-items: center;
  }
}
</style>
