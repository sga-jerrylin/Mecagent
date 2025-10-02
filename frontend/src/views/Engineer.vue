<template>
  <div class="engineer-page">
    <div class="container">
      <!-- 页面标题 -->
      <div class="page-header">
        <h1>工程师工作台</h1>
        <p>上传图纸和3D模型，AI解析后进行人工复核，最终分发给工人</p>
      </div>

      <!-- 工作流程指示器 -->
      <div class="workflow-steps">
        <el-steps :active="currentStep" align-center>
          <el-step title="上传文件" icon="Upload" />
          <el-step title="AI解析" icon="Cpu" />
          <el-step title="人工复核" icon="User" />
          <el-step title="质量检查" icon="CircleCheck" />
          <el-step title="分发工人" icon="Share" />
        </el-steps>
      </div>

      <!-- 步骤内容 -->
      <div class="step-content">
        <!-- 步骤1: 文件上传 -->
        <div v-show="currentStep === 0" class="step-panel">
          <FileUploadSection 
            @files-uploaded="handleFilesUploaded"
            @upload-progress="handleUploadProgress"
          />
        </div>

        <!-- 步骤2: AI解析中 -->
        <div v-show="currentStep === 1" class="step-panel">
          <AIProcessingSection 
            :task-id="currentTaskId"
            @processing-complete="handleProcessingComplete"
            @processing-error="handleProcessingError"
          />
        </div>

        <!-- 步骤3: 人工复核 -->
        <div v-show="currentStep === 2" class="step-panel">
          <HumanReviewSection 
            :candidate-facts="candidateFacts"
            :assembly-spec="assemblySpec"
            @review-complete="handleReviewComplete"
            @request-revision="handleRequestRevision"
          />
        </div>

        <!-- 步骤4: 质量检查 -->
        <div v-show="currentStep === 3" class="step-panel">
          <QualityCheckSection 
            :assembly-spec="reviewedAssemblySpec"
            @quality-approved="handleQualityApproved"
            @quality-rejected="handleQualityRejected"
          />
        </div>

        <!-- 步骤5: 分发工人 -->
        <div v-show="currentStep === 4" class="step-panel">
          <WorkerDistributionSection 
            :manual-id="finalManualId"
            @distribution-complete="handleDistributionComplete"
          />
        </div>
      </div>

      <!-- 项目历史 -->
      <div class="project-history" v-if="projectHistory.length > 0">
        <h3>项目历史</h3>
        <el-table :data="projectHistory" style="width: 100%">
          <el-table-column prop="name" label="项目名称" />
          <el-table-column prop="status" label="状态">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row.status)">
                {{ getStatusText(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" />
          <el-table-column prop="assigned_workers" label="分配工人数" />
          <el-table-column label="操作">
            <template #default="scope">
              <el-button size="small" @click="viewProject(scope.row)">查看</el-button>
              <el-button size="small" @click="editProject(scope.row)">编辑</el-button>
              <el-button 
                size="small" 
                type="primary" 
                @click="redistributeProject(scope.row)"
                v-if="scope.row.status === 'approved'"
              >
                重新分发
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import FileUploadSection from '@/components/engineer/FileUploadSection.vue'
import AIProcessingSection from '@/components/engineer/AIProcessingSection.vue'
import HumanReviewSection from '@/components/engineer/HumanReviewSection.vue'
import QualityCheckSection from '@/components/engineer/QualityCheckSection.vue'
import WorkerDistributionSection from '@/components/engineer/WorkerDistributionSection.vue'

// 响应式数据
const currentStep = ref(0)
const currentTaskId = ref('')
const candidateFacts = ref({})
const assemblySpec = ref({})
const reviewedAssemblySpec = ref({})
const finalManualId = ref('')

const projectHistory = ref([
  {
    id: '1',
    name: 'V型推雪板EURO连接器',
    status: 'approved',
    created_at: '2024-01-15 14:30',
    assigned_workers: 3
  },
  {
    id: '2', 
    name: '液压支架底座',
    status: 'in_review',
    created_at: '2024-01-14 09:15',
    assigned_workers: 0
  }
])

// 方法
const handleFilesUploaded = (uploadResult: any) => {
  console.log('文件上传完成:', uploadResult)
  currentStep.value = 1
  // 启动AI解析
  startAIProcessing(uploadResult)
}

const handleUploadProgress = (progress: number) => {
  console.log('上传进度:', progress)
}

const startAIProcessing = async (uploadResult: any) => {
  try {
    // 调用双通道解析API
    const response = await apiService.startDualChannelParsing({
      pdf_files: uploadResult.pdf_files,
      model_files: uploadResult.model_files
    })
    
    currentTaskId.value = response.task_id
    
  } catch (error) {
    ElMessage.error('启动AI解析失败')
    currentStep.value = 0
  }
}

const handleProcessingComplete = (result: any) => {
  console.log('AI解析完成:', result)
  candidateFacts.value = result.candidate_facts
  assemblySpec.value = result.assembly_spec
  currentStep.value = 2
}

const handleProcessingError = (error: any) => {
  console.error('AI解析失败:', error)
  ElMessage.error('AI解析失败，请重试')
  currentStep.value = 0
}

const handleReviewComplete = (reviewedData: any) => {
  console.log('人工复核完成:', reviewedData)
  reviewedAssemblySpec.value = reviewedData
  currentStep.value = 3
}

const handleRequestRevision = (revisionRequest: any) => {
  console.log('请求修订:', revisionRequest)
  // 返回AI解析步骤
  currentStep.value = 1
  // 重新处理
}

const handleQualityApproved = (approvedData: any) => {
  console.log('质量检查通过:', approvedData)
  currentStep.value = 4
}

const handleQualityRejected = (rejectionReason: any) => {
  console.log('质量检查不通过:', rejectionReason)
  // 返回人工复核步骤
  currentStep.value = 2
}

const handleDistributionComplete = (distributionResult: any) => {
  console.log('分发完成:', distributionResult)
  finalManualId.value = distributionResult.manual_id
  
  // 添加到项目历史
  projectHistory.value.unshift({
    id: distributionResult.manual_id,
    name: distributionResult.project_name,
    status: 'distributed',
    created_at: new Date().toLocaleString(),
    assigned_workers: distributionResult.worker_count
  })
  
  ElMessage.success('装配说明书已成功分发给工人！')
  
  // 重置流程
  setTimeout(() => {
    resetWorkflow()
  }, 3000)
}

const resetWorkflow = () => {
  currentStep.value = 0
  currentTaskId.value = ''
  candidateFacts.value = {}
  assemblySpec.value = {}
  reviewedAssemblySpec.value = {}
  finalManualId.value = ''
}

const getStatusType = (status: string) => {
  const statusMap = {
    'draft': 'info',
    'in_review': 'warning', 
    'approved': 'success',
    'distributed': 'primary',
    'completed': 'success',
    'rejected': 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap = {
    'draft': '草稿',
    'in_review': '复核中',
    'approved': '已批准',
    'distributed': '已分发',
    'completed': '已完成',
    'rejected': '已拒绝'
  }
  return statusMap[status] || status
}

const viewProject = (project: any) => {
  // 跳转到项目详情页
  router.push(`/engineer/project/${project.id}`)
}

const editProject = (project: any) => {
  // 编辑项目
  ElMessage.info('编辑功能开发中...')
}

const redistributeProject = (project: any) => {
  // 重新分发项目
  ElMessage.info('重新分发功能开发中...')
}

// 路由
const router = useRouter()
</script>

<style lang="scss" scoped>
.engineer-page {
  min-height: 100vh;
  padding: 40px 0;
  background: var(--el-bg-color-page);
  
  .container {
    max-width: 1400px;
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

.workflow-steps {
  margin-bottom: 60px;
  
  :deep(.el-steps) {
    .el-step__title {
      font-weight: 500;
    }
    
    .el-step__icon {
      border-radius: 50%;
    }
    
    .el-step.is-process .el-step__icon {
      background: var(--el-color-primary);
      border-color: var(--el-color-primary);
    }
  }
}

.step-content {
  .step-panel {
    min-height: 500px;
    background: var(--el-bg-color);
    border-radius: 16px;
    padding: 32px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    margin-bottom: 40px;
  }
}

.project-history {
  margin-top: 60px;
  
  h3 {
    margin-bottom: 20px;
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  
  .el-table {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .page-header h1 {
    font-size: 2rem;
  }
  
  .step-content .step-panel {
    padding: 20px;
  }
  
  .workflow-steps {
    :deep(.el-steps) {
      .el-step__title {
        font-size: 12px;
      }
    }
  }
}
</style>
