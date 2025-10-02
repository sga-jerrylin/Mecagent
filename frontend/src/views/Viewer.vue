<template>
  <div class="viewer-page">
    <div class="viewer-layout">
      <!-- 左侧面板 -->
      <div class="left-panel" :class="{ collapsed: leftPanelCollapsed }">
        <div class="panel-header">
          <h3>装配说明书</h3>
          <el-button 
            text 
            :icon="leftPanelCollapsed ? 'Expand' : 'Fold'"
            @click="leftPanelCollapsed = !leftPanelCollapsed"
          />
        </div>
        
        <div class="panel-content" v-show="!leftPanelCollapsed">
          <!-- 项目信息 -->
          <div class="info-section">
            <h4>项目信息</h4>
            <div class="info-item">
              <label>项目名称:</label>
              <span>{{ projectInfo.name }}</span>
            </div>
            <div class="info-item">
              <label>图号:</label>
              <span>{{ projectInfo.drawingNumber }}</span>
            </div>
            <div class="info-item">
              <label>版本:</label>
              <span>{{ projectInfo.version }}</span>
            </div>
            <div class="info-item">
              <label>生成时间:</label>
              <span>{{ projectInfo.createdAt }}</span>
            </div>
          </div>
          
          <!-- 装配步骤导航 -->
          <div class="steps-section">
            <h4>装配步骤</h4>
            <div class="steps-nav">
              <div 
                v-for="(step, index) in assemblySteps" 
                :key="step.id"
                class="step-nav-item"
                :class="{ 
                  active: currentStepIndex === index,
                  completed: index < currentStepIndex 
                }"
                @click="goToStep(index)"
              >
                <div class="step-number">{{ index + 1 }}</div>
                <div class="step-info">
                  <div class="step-title">{{ step.title }}</div>
                  <div class="step-duration">{{ step.estimatedTime }}</div>
                </div>
                <div class="step-status">
                  <el-icon v-if="index < currentStepIndex"><Check /></el-icon>
                  <el-icon v-else-if="currentStepIndex === index"><Right /></el-icon>
                </div>
              </div>
            </div>
          </div>
          
          <!-- BOM清单 -->
          <div class="bom-section">
            <h4>零件清单 (BOM)</h4>
            <div class="bom-list">
              <div 
                v-for="item in bomItems" 
                :key="item.id"
                class="bom-item"
                :class="{ highlighted: highlightedPart === item.id }"
                @click="highlightPart(item.id)"
              >
                <div class="bom-number">{{ item.number }}</div>
                <div class="bom-info">
                  <div class="bom-name">{{ item.name }}</div>
                  <div class="bom-spec">{{ item.specification }}</div>
                </div>
                <div class="bom-qty">{{ item.quantity }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <div class="main-content">
        <!-- 顶部工具栏 -->
        <div class="toolbar">
          <div class="toolbar-left">
            <el-button-group>
              <el-button 
                :disabled="currentStepIndex === 0"
                @click="previousStep"
                :icon="ArrowLeft"
              >
                上一步
              </el-button>
              <el-button 
                :disabled="currentStepIndex === assemblySteps.length - 1"
                @click="nextStep"
                :icon="ArrowRight"
              >
                下一步
              </el-button>
            </el-button-group>
            
            <el-divider direction="vertical" />
            
            <el-button-group>
              <el-button @click="resetView" :icon="Refresh">重置视图</el-button>
              <el-button @click="toggleFullscreen" :icon="FullScreen">全屏</el-button>
            </el-button-group>
          </div>
          
          <div class="toolbar-center">
            <div class="step-indicator">
              <span class="current-step">步骤 {{ currentStepIndex + 1 }}</span>
              <span class="total-steps">/ {{ assemblySteps.length }}</span>
            </div>
            <el-progress 
              :percentage="stepProgress" 
              :show-text="false"
              :stroke-width="4"
            />
          </div>
          
          <div class="toolbar-right">
            <el-button @click="exportPDF" :icon="Download">导出PDF</el-button>
            <el-button @click="printManual" :icon="Printer">打印</el-button>
          </div>
        </div>

        <!-- 3D查看器 -->
        <div class="viewer-container">
          <ThreeViewer 
            :model-url="currentModelUrl"
            :auto-rotate="false"
            :show-grid="true"
            ref="threeViewerRef"
          />
          
          <!-- 步骤覆盖层 -->
          <div class="step-overlay">
            <div class="step-content">
              <h2>{{ currentStep?.title }}</h2>
              <div class="step-description" v-html="currentStep?.description"></div>
              
              <!-- 关键点标注 -->
              <div class="key-points" v-if="currentStep?.keyPoints?.length">
                <h4>关键要点:</h4>
                <ul>
                  <li v-for="point in currentStep.keyPoints" :key="point">
                    {{ point }}
                  </li>
                </ul>
              </div>
              
              <!-- 质量检查 -->
              <div class="quality-check" v-if="currentStep?.qualityCheck">
                <h4>质量检查:</h4>
                <div class="check-items">
                  <div 
                    v-for="check in currentStep.qualityCheck" 
                    :key="check.id"
                    class="check-item"
                  >
                    <el-checkbox v-model="check.completed">
                      {{ check.description }}
                    </el-checkbox>
                  </div>
                </div>
              </div>
              
              <!-- 工具和材料 -->
              <div class="tools-materials" v-if="currentStep?.tools?.length || currentStep?.materials?.length">
                <div class="tools" v-if="currentStep?.tools?.length">
                  <h4>所需工具:</h4>
                  <div class="tool-list">
                    <el-tag 
                      v-for="tool in currentStep.tools" 
                      :key="tool"
                      class="tool-tag"
                    >
                      {{ tool }}
                    </el-tag>
                  </div>
                </div>
                
                <div class="materials" v-if="currentStep?.materials?.length">
                  <h4>所需材料:</h4>
                  <div class="material-list">
                    <div 
                      v-for="material in currentStep.materials" 
                      :key="material.id"
                      class="material-item"
                    >
                      <span class="material-name">{{ material.name }}</span>
                      <span class="material-qty">{{ material.quantity }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧面板 -->
      <div class="right-panel" :class="{ collapsed: rightPanelCollapsed }">
        <div class="panel-header">
          <h3>辅助信息</h3>
          <el-button 
            text 
            :icon="rightPanelCollapsed ? 'Expand' : 'Fold'"
            @click="rightPanelCollapsed = !rightPanelCollapsed"
          />
        </div>
        
        <div class="panel-content" v-show="!rightPanelCollapsed">
          <!-- 技术图纸 -->
          <div class="drawings-section">
            <h4>技术图纸</h4>
            <div class="drawing-thumbnails">
              <div 
                v-for="drawing in technicalDrawings" 
                :key="drawing.id"
                class="drawing-thumb"
                @click="showDrawing(drawing)"
              >
                <img :src="drawing.thumbnail" :alt="drawing.name">
                <span class="drawing-name">{{ drawing.name }}</span>
              </div>
            </div>
          </div>
          
          <!-- 注意事项 -->
          <div class="notes-section">
            <h4>安全注意事项</h4>
            <div class="safety-notes">
              <div 
                v-for="note in safetyNotes" 
                :key="note.id"
                class="safety-note"
                :class="note.level"
              >
                <el-icon class="note-icon">
                  <component :is="getNoteIcon(note.level)" />
                </el-icon>
                <span class="note-text">{{ note.text }}</span>
              </div>
            </div>
          </div>
          
          <!-- 常见问题 -->
          <div class="faq-section">
            <h4>常见问题</h4>
            <el-collapse v-model="activeFAQ">
              <el-collapse-item 
                v-for="faq in frequentQuestions" 
                :key="faq.id"
                :title="faq.question"
                :name="faq.id"
              >
                <p>{{ faq.answer }}</p>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import ThreeViewer from '@/components/ThreeViewer.vue'

interface Props {
  id?: string
}

const props = defineProps<Props>()

// 响应式数据
const leftPanelCollapsed = ref(false)
const rightPanelCollapsed = ref(false)
const currentStepIndex = ref(0)
const highlightedPart = ref('')
const activeFAQ = ref([])

const threeViewerRef = ref()

// 项目信息
const projectInfo = reactive({
  name: 'V型推雪板EURO连接器',
  drawingNumber: 'T-SPV1830-EURO',
  version: 'V1.0',
  createdAt: '2024-01-15 14:30:25'
})

// 装配步骤
const assemblySteps = ref([
  {
    id: 1,
    title: '准备工作',
    description: '检查所有零件和工具，确保工作环境安全',
    estimatedTime: '5分钟',
    keyPoints: ['检查零件完整性', '准备必要工具', '清理工作台面'],
    tools: ['扳手', '螺丝刀', '测量工具'],
    materials: [
      { id: 1, name: '主体框架', quantity: '1件' },
      { id: 2, name: '连接螺栓', quantity: '4件' }
    ],
    qualityCheck: [
      { id: 1, description: '零件无损伤', completed: false },
      { id: 2, description: '工具齐全', completed: false }
    ]
  },
  {
    id: 2,
    title: '主体安装',
    description: '将主体框架固定到指定位置',
    estimatedTime: '15分钟',
    keyPoints: ['确保水平度', '预紧螺栓', '检查间隙'],
    tools: ['扳手', '水平仪'],
    materials: [
      { id: 3, name: '固定螺栓', quantity: '8件' }
    ],
    qualityCheck: [
      { id: 3, description: '水平度符合要求', completed: false },
      { id: 4, description: '螺栓扭矩达标', completed: false }
    ]
  }
  // 更多步骤...
])

// BOM清单
const bomItems = ref([
  { id: 1, number: '001', name: '主体框架', specification: '钢材 Q235', quantity: 1 },
  { id: 2, number: '002', name: '连接板', specification: '钢板 10mm', quantity: 2 },
  { id: 3, number: '003', name: '螺栓', specification: 'M12×50', quantity: 8 }
])

// 技术图纸
const technicalDrawings = ref([
  { id: 1, name: '总装图', thumbnail: '/images/drawing1-thumb.jpg', url: '/images/drawing1.jpg' },
  { id: 2, name: '零件图', thumbnail: '/images/drawing2-thumb.jpg', url: '/images/drawing2.jpg' }
])

// 安全注意事项
const safetyNotes = ref([
  { id: 1, level: 'danger', text: '操作前必须佩戴安全帽和防护眼镜' },
  { id: 2, level: 'warning', text: '注意螺栓扭矩，避免过紧或过松' },
  { id: 3, level: 'info', text: '保持工作区域整洁，避免零件丢失' }
])

// 常见问题
const frequentQuestions = ref([
  { id: 1, question: '螺栓扭矩标准是多少？', answer: 'M12螺栓扭矩为85-95 N·m' },
  { id: 2, question: '如何检查水平度？', answer: '使用水平仪，误差不超过0.5mm/m' }
])

// 计算属性
const currentStep = computed(() => assemblySteps.value[currentStepIndex.value])
const stepProgress = computed(() => ((currentStepIndex.value + 1) / assemblySteps.value.length) * 100)
const currentModelUrl = computed(() => `/models/step-${currentStepIndex.value + 1}.glb`)

// 方法
const goToStep = (index: number) => {
  currentStepIndex.value = index
}

const nextStep = () => {
  if (currentStepIndex.value < assemblySteps.value.length - 1) {
    currentStepIndex.value++
  }
}

const previousStep = () => {
  if (currentStepIndex.value > 0) {
    currentStepIndex.value--
  }
}

const highlightPart = (partId: string) => {
  highlightedPart.value = partId
  // 在3D查看器中高亮对应零件
  if (threeViewerRef.value) {
    threeViewerRef.value.selectPart(partId)
  }
}

const resetView = () => {
  if (threeViewerRef.value) {
    threeViewerRef.value.resetView()
  }
}

const toggleFullscreen = () => {
  if (document.fullscreenElement) {
    document.exitFullscreen()
  } else {
    document.documentElement.requestFullscreen()
  }
}

const showDrawing = (drawing: any) => {
  // 显示技术图纸
  ElMessageBox.alert(
    `<img src="${drawing.url}" style="max-width: 100%; height: auto;">`,
    drawing.name,
    {
      dangerouslyUseHTMLString: true,
      customClass: 'drawing-dialog'
    }
  )
}

const getNoteIcon = (level: string) => {
  switch (level) {
    case 'danger': return 'Warning'
    case 'warning': return 'InfoFilled'
    case 'info': return 'QuestionFilled'
    default: return 'InfoFilled'
  }
}

const exportPDF = () => {
  ElMessage.info('PDF导出功能开发中...')
}

const printManual = () => {
  window.print()
}

// 键盘快捷键
const handleKeydown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'ArrowLeft':
      event.preventDefault()
      previousStep()
      break
    case 'ArrowRight':
      event.preventDefault()
      nextStep()
      break
    case 'Escape':
      if (document.fullscreenElement) {
        document.exitFullscreen()
      }
      break
  }
}

// 生命周期
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// 监听路由参数
watch(() => props.id, (newId) => {
  if (newId) {
    // 根据ID加载对应的装配说明书数据
    console.log('Loading manual for ID:', newId)
  }
}, { immediate: true })
</script>

<style lang="scss" scoped>
.viewer-page {
  height: 100vh;
  overflow: hidden;
}

.viewer-layout {
  display: grid;
  grid-template-columns: 300px 1fr 300px;
  height: 100vh;
  
  .left-panel,
  .right-panel {
    background: var(--el-bg-color);
    border-right: 1px solid var(--el-border-color-light);
    display: flex;
    flex-direction: column;
    transition: all 0.3s ease;
    
    &.collapsed {
      width: 60px;
      min-width: 60px;
      
      .panel-content {
        display: none;
      }
    }
    
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px;
      border-bottom: 1px solid var(--el-border-color-light);
      
      h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
      }
    }
    
    .panel-content {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
    }
  }
  
  .right-panel {
    border-right: none;
    border-left: 1px solid var(--el-border-color-light);
  }
}

.main-content {
  display: flex;
  flex-direction: column;
  height: 100vh;
  
  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: var(--el-bg-color);
    border-bottom: 1px solid var(--el-border-color-light);
    
    .toolbar-center {
      flex: 1;
      max-width: 300px;
      margin: 0 20px;
      
      .step-indicator {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-size: 14px;
        
        .current-step {
          font-weight: 600;
          color: var(--el-color-primary);
        }
        
        .total-steps {
          color: var(--el-text-color-secondary);
        }
      }
    }
  }
  
  .viewer-container {
    flex: 1;
    position: relative;
    
    .step-overlay {
      position: absolute;
      bottom: 20px;
      left: 20px;
      right: 20px;
      background: rgba(0, 0, 0, 0.8);
      backdrop-filter: blur(10px);
      border-radius: 12px;
      padding: 20px;
      color: white;
      max-height: 40%;
      overflow-y: auto;
      
      .step-content {
        h2 {
          margin: 0 0 16px 0;
          font-size: 1.5rem;
          color: #00d4ff;
        }
        
        .step-description {
          margin-bottom: 20px;
          line-height: 1.6;
        }
        
        .key-points,
        .quality-check,
        .tools-materials {
          margin-bottom: 20px;
          
          h4 {
            margin: 0 0 12px 0;
            color: #00d4ff;
            font-size: 14px;
          }
          
          ul {
            margin: 0;
            padding-left: 20px;
            
            li {
              margin-bottom: 8px;
            }
          }
        }
        
        .check-items {
          .check-item {
            margin-bottom: 8px;
          }
        }
        
        .tools-materials {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          
          .tool-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            
            .tool-tag {
              background: rgba(64, 158, 255, 0.2);
              border: 1px solid rgba(64, 158, 255, 0.5);
            }
          }
          
          .material-list {
            .material-item {
              display: flex;
              justify-content: space-between;
              margin-bottom: 8px;
              padding: 4px 8px;
              background: rgba(255, 255, 255, 0.1);
              border-radius: 4px;
            }
          }
        }
      }
    }
  }
}

// 左侧面板样式
.info-section,
.steps-section,
.bom-section {
  margin-bottom: 24px;
  
  h4 {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
  
  label {
    color: var(--el-text-color-secondary);
  }
  
  span {
    color: var(--el-text-color-primary);
    font-weight: 500;
  }
}

.steps-nav {
  .step-nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-bottom: 8px;
    
    &:hover {
      background: var(--el-fill-color-light);
    }
    
    &.active {
      background: var(--el-color-primary-light-9);
      border: 1px solid var(--el-color-primary-light-7);
    }
    
    &.completed {
      .step-number {
        background: var(--el-color-success);
        color: white;
      }
    }
    
    .step-number {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: var(--el-fill-color);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: 600;
      flex-shrink: 0;
    }
    
    .step-info {
      flex: 1;
      
      .step-title {
        font-size: 13px;
        font-weight: 500;
        margin-bottom: 2px;
      }
      
      .step-duration {
        font-size: 11px;
        color: var(--el-text-color-secondary);
      }
    }
    
    .step-status {
      color: var(--el-color-primary);
    }
  }
}

.bom-list {
  .bom-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-bottom: 4px;
    
    &:hover {
      background: var(--el-fill-color-light);
    }
    
    &.highlighted {
      background: var(--el-color-warning-light-9);
      border: 1px solid var(--el-color-warning-light-7);
    }
    
    .bom-number {
      width: 30px;
      height: 30px;
      border-radius: 4px;
      background: var(--el-color-primary-light-9);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
      font-weight: 600;
      color: var(--el-color-primary);
      flex-shrink: 0;
    }
    
    .bom-info {
      flex: 1;
      
      .bom-name {
        font-size: 12px;
        font-weight: 500;
        margin-bottom: 2px;
      }
      
      .bom-spec {
        font-size: 10px;
        color: var(--el-text-color-secondary);
      }
    }
    
    .bom-qty {
      font-size: 11px;
      font-weight: 600;
      color: var(--el-color-primary);
    }
  }
}

// 右侧面板样式
.drawings-section,
.notes-section,
.faq-section {
  margin-bottom: 24px;
  
  h4 {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
}

.drawing-thumbnails {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  
  .drawing-thumb {
    cursor: pointer;
    border-radius: 6px;
    overflow: hidden;
    transition: transform 0.2s ease;
    
    &:hover {
      transform: scale(1.05);
    }
    
    img {
      width: 100%;
      height: 60px;
      object-fit: cover;
    }
    
    .drawing-name {
      display: block;
      padding: 4px 8px;
      background: var(--el-fill-color-light);
      font-size: 11px;
      text-align: center;
    }
  }
}

.safety-notes {
  .safety-note {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 8px;
    border-radius: 6px;
    margin-bottom: 8px;
    
    &.danger {
      background: var(--el-color-danger-light-9);
      color: var(--el-color-danger);
    }
    
    &.warning {
      background: var(--el-color-warning-light-9);
      color: var(--el-color-warning);
    }
    
    &.info {
      background: var(--el-color-info-light-9);
      color: var(--el-color-info);
    }
    
    .note-icon {
      flex-shrink: 0;
      margin-top: 2px;
    }
    
    .note-text {
      font-size: 12px;
      line-height: 1.4;
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .viewer-layout {
    grid-template-columns: 250px 1fr 250px;
  }
}

@media (max-width: 768px) {
  .viewer-layout {
    grid-template-columns: 1fr;
    
    .left-panel,
    .right-panel {
      position: fixed;
      top: 0;
      bottom: 0;
      z-index: 1000;
      width: 300px;
      transform: translateX(-100%);
      
      &:not(.collapsed) {
        transform: translateX(0);
      }
    }
    
    .right-panel {
      right: 0;
      transform: translateX(100%);
      
      &:not(.collapsed) {
        transform: translateX(0);
      }
    }
  }
  
  .toolbar {
    .toolbar-left,
    .toolbar-right {
      display: none;
    }
    
    .toolbar-center {
      margin: 0;
      max-width: none;
    }
  }
}

// 打印样式
@media print {
  .toolbar,
  .left-panel,
  .right-panel {
    display: none !important;
  }
  
  .viewer-layout {
    grid-template-columns: 1fr !important;
  }
  
  .step-overlay {
    position: static !important;
    background: white !important;
    color: black !important;
    backdrop-filter: none !important;
  }
}
</style>
