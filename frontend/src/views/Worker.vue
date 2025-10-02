<template>
  <div class="worker-page">
    <!-- 工人专用顶部导航 -->
    <div class="worker-header">
      <div class="container">
        <div class="header-content">
          <div class="logo-section">
            <h1>装配工作台</h1>
            <span class="worker-badge">工人端</span>
          </div>
          <div class="worker-info">
            <el-avatar :size="40" src="/avatars/worker.png" />
            <div class="info-text">
              <div class="name">{{ workerInfo.name }}</div>
              <div class="department">{{ workerInfo.department }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="container">
      <!-- 任务列表 -->
      <div class="task-section" v-if="!currentTask">
        <h2>我的装配任务</h2>
        
        <!-- 任务筛选 -->
        <div class="task-filters">
          <el-radio-group v-model="taskFilter" @change="filterTasks">
            <el-radio-button label="all">全部任务</el-radio-button>
            <el-radio-button label="pending">待开始</el-radio-button>
            <el-radio-button label="in_progress">进行中</el-radio-button>
            <el-radio-button label="completed">已完成</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 任务卡片 -->
        <div class="task-grid">
          <div 
            v-for="task in filteredTasks" 
            :key="task.id"
            class="task-card"
            :class="{ 'urgent': task.priority === 'high' }"
            @click="startTask(task)"
          >
            <div class="task-header">
              <h3>{{ task.name }}</h3>
              <el-tag 
                :type="getTaskStatusType(task.status)"
                size="small"
              >
                {{ getTaskStatusText(task.status) }}
              </el-tag>
            </div>
            
            <div class="task-info">
              <div class="info-item">
                <el-icon><Clock /></el-icon>
                <span>预计时间: {{ task.estimated_time }}</span>
              </div>
              <div class="info-item">
                <el-icon><User /></el-icon>
                <span>分配工程师: {{ task.engineer }}</span>
              </div>
              <div class="info-item">
                <el-icon><Calendar /></el-icon>
                <span>截止时间: {{ task.deadline }}</span>
              </div>
            </div>

            <div class="task-progress" v-if="task.status === 'in_progress'">
              <el-progress 
                :percentage="task.progress" 
                :stroke-width="8"
                :show-text="false"
              />
              <span class="progress-text">{{ task.progress }}% 完成</span>
            </div>

            <div class="task-actions">
              <el-button 
                type="primary" 
                size="large"
                :disabled="task.status === 'completed'"
                @click.stop="startTask(task)"
              >
                {{ task.status === 'pending' ? '开始装配' : 
                   task.status === 'in_progress' ? '继续装配' : '查看结果' }}
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 装配说明书界面 -->
      <div class="assembly-interface" v-else>
        <!-- 顶部工具栏 -->
        <div class="assembly-toolbar">
          <div class="left-tools">
            <el-button @click="exitTask" icon="ArrowLeft">返回任务列表</el-button>
            <h2>{{ currentTask.name }}</h2>
          </div>
          
          <div class="right-tools">
            <el-button @click="reportIssue" icon="Warning">报告问题</el-button>
            <el-button @click="requestHelp" icon="QuestionFilled">请求帮助</el-button>
            <el-button 
              type="success" 
              @click="completeTask"
              :disabled="currentStep < totalSteps"
            >
              完成装配
            </el-button>
          </div>
        </div>

        <!-- 三栏布局 -->
        <div class="assembly-layout">
          <!-- 左侧：步骤和BOM -->
          <div class="left-panel">
            <!-- 装配步骤 -->
            <div class="steps-section">
              <h3>装配步骤</h3>
              <div class="steps-list">
                <div 
                  v-for="(step, index) in assemblySteps"
                  :key="step.id"
                  class="step-item"
                  :class="{ 
                    'active': index === currentStep,
                    'completed': index < currentStep,
                    'disabled': index > currentStep
                  }"
                  @click="goToStep(index)"
                >
                  <div class="step-number">{{ index + 1 }}</div>
                  <div class="step-content">
                    <div class="step-title">{{ step.action }}</div>
                    <div class="step-time">{{ step.estimated_time }}</div>
                  </div>
                  <div class="step-status">
                    <el-icon v-if="index < currentStep" color="#67c23a">
                      <CircleCheck />
                    </el-icon>
                    <el-icon v-else-if="index === currentStep" color="#409eff">
                      <Clock />
                    </el-icon>
                  </div>
                </div>
              </div>
            </div>

            <!-- BOM清单 -->
            <div class="bom-section">
              <h3>所需零件</h3>
              <div class="bom-list">
                <div 
                  v-for="part in currentStepParts"
                  :key="part.id"
                  class="bom-item"
                >
                  <div class="part-info">
                    <div class="part-name">{{ part.name }}</div>
                    <div class="part-spec">{{ part.material }} | {{ part.spec }}</div>
                  </div>
                  <div class="part-qty">{{ part.qty }}{{ part.unit }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 中间：3D模型 -->
          <div class="center-panel">
            <WorkerThreeViewer 
              :model-url="currentTask.model_url"
              :current-step="currentStep"
              :assembly-steps="assemblySteps"
              @part-selected="handlePartSelected"
              @step-animation-complete="handleStepComplete"
            />
          </div>

          <!-- 右侧：操作指导 -->
          <div class="right-panel">
            <!-- 当前步骤详情 -->
            <div class="step-details">
              <h3>第{{ currentStep + 1 }}步：{{ currentStepData.action }}</h3>
              
              <div class="step-description">
                {{ currentStepData.description }}
              </div>

              <!-- 操作要点 -->
              <div class="operation-points" v-if="currentStepData.points">
                <h4>操作要点</h4>
                <ul>
                  <li v-for="point in currentStepData.points" :key="point">
                    {{ point }}
                  </li>
                </ul>
              </div>

              <!-- 质量检查 -->
              <div class="quality-checks" v-if="currentStepData.checks">
                <h4>质量检查</h4>
                <div class="check-list">
                  <div 
                    v-for="check in currentStepData.checks"
                    :key="check.id"
                    class="check-item"
                  >
                    <el-checkbox 
                      v-model="check.completed"
                      @change="updateCheckStatus(check)"
                    >
                      {{ check.description }}
                    </el-checkbox>
                    <div class="check-standard">{{ check.standard }}</div>
                  </div>
                </div>
              </div>

              <!-- 安全提醒 -->
              <div class="safety-notes" v-if="currentStepData.safety">
                <h4>⚠️ 安全提醒</h4>
                <div class="safety-list">
                  <div 
                    v-for="note in currentStepData.safety"
                    :key="note"
                    class="safety-item"
                  >
                    {{ note }}
                  </div>
                </div>
              </div>

              <!-- 步骤控制 -->
              <div class="step-controls">
                <el-button 
                  @click="previousStep"
                  :disabled="currentStep === 0"
                  icon="ArrowLeft"
                >
                  上一步
                </el-button>
                <el-button 
                  type="primary"
                  @click="nextStep"
                  :disabled="!canProceedToNext"
                  icon="ArrowRight"
                >
                  下一步
                </el-button>
              </div>
            </div>

            <!-- 工具和材料 -->
            <div class="tools-section">
              <h4>所需工具</h4>
              <div class="tools-list">
                <el-tag 
                  v-for="tool in currentStepData.tools"
                  :key="tool"
                  class="tool-tag"
                >
                  {{ tool }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 问题报告对话框 -->
    <IssueReportDialog 
      v-model="showIssueDialog"
      :task-id="currentTask?.id"
      @issue-submitted="handleIssueSubmitted"
    />

    <!-- 帮助请求对话框 -->
    <HelpRequestDialog 
      v-model="showHelpDialog"
      :task-id="currentTask?.id"
      @help-requested="handleHelpRequested"
    />
  </div>
</template>

<script setup lang="ts">
import WorkerThreeViewer from '@/components/worker/WorkerThreeViewer.vue'
import IssueReportDialog from '@/components/worker/IssueReportDialog.vue'
import HelpRequestDialog from '@/components/worker/HelpRequestDialog.vue'
import { apiService } from '@/api/index'

// 响应式数据
const workerInfo = ref({
  name: '张师傅',
  department: '装配车间一组'
})

const taskFilter = ref('all')
const currentTask = ref(null)
const currentStep = ref(0)
const totalSteps = ref(0)
const showIssueDialog = ref(false)
const showHelpDialog = ref(false)

const tasks = ref([
  {
    id: '1',
    name: 'V型推雪板EURO连接器装配',
    status: 'pending',
    priority: 'high',
    estimated_time: '2.5小时',
    engineer: '李工程师',
    deadline: '2024-01-16 18:00',
    progress: 0,
    model_url: '/models/euro_connector.glb'
  },
  {
    id: '2',
    name: '液压支架底座焊接',
    status: 'in_progress', 
    priority: 'normal',
    estimated_time: '4小时',
    engineer: '王工程师',
    deadline: '2024-01-17 12:00',
    progress: 35,
    model_url: '/models/hydraulic_base.glb'
  }
])

const assemblySteps = ref([])
const currentStepParts = ref([])

// 计算属性
const filteredTasks = computed(() => {
  if (taskFilter.value === 'all') return tasks.value
  return tasks.value.filter(task => task.status === taskFilter.value)
})

const currentStepData = computed(() => {
  return assemblySteps.value[currentStep.value] || {}
})

const canProceedToNext = computed(() => {
  const stepData = currentStepData.value
  if (!stepData.checks) return true
  
  return stepData.checks.every(check => check.completed)
})

// 方法
const filterTasks = () => {
  // 任务筛选逻辑
}

const startTask = (task) => {
  currentTask.value = task
  loadAssemblyData(task.id)
  
  // 更新任务状态
  if (task.status === 'pending') {
    task.status = 'in_progress'
    task.progress = 0
  }
}

const loadAssemblyData = async (taskId) => {
  try {
    // 加载装配数据
    const response = await apiService.getAssemblyData(taskId)
    assemblySteps.value = response.assembly_plan.sequence
    totalSteps.value = assemblySteps.value.length
    currentStep.value = 0
    
    updateCurrentStepParts()
    
  } catch (error) {
    ElMessage.error('加载装配数据失败')
  }
}

const updateCurrentStepParts = () => {
  const stepData = assemblySteps.value[currentStep.value]
  if (stepData && stepData.targets) {
    // 根据步骤目标更新所需零件
    currentStepParts.value = stepData.targets.map(partId => ({
      id: partId,
      name: `零件${partId}`,
      material: 'Q355B',
      spec: 't=6',
      qty: 1,
      unit: '件'
    }))
  }
}

const goToStep = (stepIndex) => {
  if (stepIndex <= currentStep.value) {
    currentStep.value = stepIndex
    updateCurrentStepParts()
  }
}

const previousStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
    updateCurrentStepParts()
  }
}

const nextStep = () => {
  if (currentStep.value < totalSteps.value - 1 && canProceedToNext.value) {
    currentStep.value++
    updateCurrentStepParts()
    
    // 更新任务进度
    const progress = Math.round(((currentStep.value + 1) / totalSteps.value) * 100)
    currentTask.value.progress = progress
  }
}

const exitTask = () => {
  currentTask.value = null
  currentStep.value = 0
}

const reportIssue = () => {
  showIssueDialog.value = true
}

const requestHelp = () => {
  showHelpDialog.value = true
}

const completeTask = () => {
  ElMessageBox.confirm(
    '确认已完成所有装配步骤？',
    '完成装配',
    {
      confirmButtonText: '确认完成',
      cancelButtonText: '取消',
      type: 'success'
    }
  ).then(() => {
    currentTask.value.status = 'completed'
    currentTask.value.progress = 100
    
    ElMessage.success('装配任务已完成！')
    
    // 返回任务列表
    setTimeout(() => {
      exitTask()
    }, 2000)
  })
}

const handlePartSelected = (partId) => {
  console.log('选中零件:', partId)
}

const handleStepComplete = () => {
  console.log('步骤动画完成')
}

const updateCheckStatus = (check) => {
  console.log('更新检查状态:', check)
}

const handleIssueSubmitted = (issue) => {
  ElMessage.success('问题已提交给工程师')
  showIssueDialog.value = false
}

const handleHelpRequested = (helpRequest) => {
  ElMessage.success('帮助请求已发送')
  showHelpDialog.value = false
}

const getTaskStatusType = (status) => {
  const statusMap = {
    'pending': 'info',
    'in_progress': 'warning',
    'completed': 'success'
  }
  return statusMap[status] || 'info'
}

const getTaskStatusText = (status) => {
  const statusMap = {
    'pending': '待开始',
    'in_progress': '进行中', 
    'completed': '已完成'
  }
  return statusMap[status] || status
}
</script>

<style lang="scss" scoped>
.worker-page {
  min-height: 100vh;
  background: var(--el-bg-color-page);
}

.worker-header {
  background: linear-gradient(135deg, #409eff, #67c23a);
  color: white;
  padding: 20px 0;
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .logo-section {
    display: flex;
    align-items: center;
    gap: 16px;
    
    h1 {
      font-size: 1.8rem;
      font-weight: 600;
      margin: 0;
    }
    
    .worker-badge {
      background: rgba(255, 255, 255, 0.2);
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 0.9rem;
    }
  }
  
  .worker-info {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .info-text {
      .name {
        font-weight: 600;
        font-size: 1.1rem;
      }
      
      .department {
        font-size: 0.9rem;
        opacity: 0.9;
      }
    }
  }
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
}

.task-section {
  padding: 40px 0;
  
  h2 {
    font-size: 2rem;
    margin-bottom: 30px;
    color: var(--el-text-color-primary);
  }
}

.task-filters {
  margin-bottom: 30px;
}

.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
}

.task-card {
  background: var(--el-bg-color);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
  }
  
  &.urgent {
    border-left: 4px solid #f56c6c;
  }
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  h3 {
    font-size: 1.3rem;
    font-weight: 600;
    margin: 0;
  }
}

.task-info {
  margin-bottom: 20px;
  
  .info-item {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    color: var(--el-text-color-secondary);
    font-size: 0.9rem;
  }
}

.task-progress {
  margin-bottom: 20px;
  
  .progress-text {
    font-size: 0.9rem;
    color: var(--el-text-color-secondary);
    margin-top: 8px;
    display: block;
  }
}

.assembly-interface {
  padding: 20px 0;
}

.assembly-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 24px;
  background: var(--el-bg-color);
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  
  .left-tools {
    display: flex;
    align-items: center;
    gap: 16px;
    
    h2 {
      margin: 0;
      font-size: 1.5rem;
    }
  }
  
  .right-tools {
    display: flex;
    gap: 12px;
  }
}

.assembly-layout {
  display: grid;
  grid-template-columns: 300px 1fr 350px;
  gap: 20px;
  height: calc(100vh - 200px);
}

.left-panel, .right-panel {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 20px;
  overflow-y: auto;
}

.center-panel {
  background: var(--el-bg-color);
  border-radius: 12px;
  overflow: hidden;
}

.steps-section {
  margin-bottom: 30px;
  
  h3 {
    margin-bottom: 16px;
    font-size: 1.2rem;
    font-weight: 600;
  }
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &.active {
    background: var(--el-color-primary-light-9);
    border: 1px solid var(--el-color-primary);
  }
  
  &.completed {
    background: var(--el-color-success-light-9);
  }
  
  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .step-number {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--el-color-info-light-8);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 600;
  }
  
  .step-content {
    flex: 1;
    
    .step-title {
      font-weight: 500;
      margin-bottom: 4px;
    }
    
    .step-time {
      font-size: 0.8rem;
      color: var(--el-text-color-secondary);
    }
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .assembly-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto 1fr;
    height: auto;
  }
  
  .left-panel, .right-panel {
    height: auto;
  }
  
  .center-panel {
    height: 500px;
  }
}

@media (max-width: 768px) {
  .task-grid {
    grid-template-columns: 1fr;
  }
  
  .worker-header .header-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .assembly-toolbar {
    flex-direction: column;
    gap: 16px;
    
    .left-tools, .right-tools {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>
