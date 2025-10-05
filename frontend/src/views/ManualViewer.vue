<template>
  <div class="worker-manual-viewer">
    <!-- 顶部进度条 -->
    <div class="top-bar">
      <div class="product-info">
        <h1>{{ productName }}</h1>
        <el-tag type="info" size="large">装配说明书</el-tag>
      </div>
      
      <div class="progress-section">
        <div class="progress-info">
          <span class="current-step">步骤 {{ currentStepIndex + 1 }}</span>
          <span class="total-steps">/ {{ totalSteps }}</span>
          <span class="step-title">{{ currentStepData?.title }}</span>
        </div>
        <el-progress 
          :percentage="progressPercentage" 
          :stroke-width="10"
          :color="progressColor"
        />
      </div>

      <div class="top-actions">
        <el-button-group size="large">
          <el-button :icon="ArrowLeft" :disabled="currentStepIndex === 0" @click="previousStep">
            上一步
          </el-button>
          <el-button type="primary" :icon="ArrowRight" :disabled="currentStepIndex === totalSteps - 1" @click="nextStep">
            下一步
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 主工作区 -->
    <div class="main-workspace" v-if="manualData">
      <!-- 左侧：图纸参考（全屏显示） -->
      <div class="left-sidebar">
        <div class="drawing-section-full">
          <div class="section-title">
            📐 图纸参考
            <span v-if="drawingImages.length > 1" class="page-indicator">
              共{{ drawingImages.length }}张
            </span>
          </div>
          <el-scrollbar class="drawings-container">
            <div class="drawings-list">
              <div
                v-for="(drawingUrl, index) in drawingImages"
                :key="index"
                class="drawing-item"
                :class="{ 'zoomed': zoomedDrawingIndex === index }"
                @click="toggleDrawingZoom(index)"
              >
                <img
                  :src="drawingUrl"
                  :alt="`工程图纸 ${index + 1}`"
                  class="drawing-image"
                  @dragstart.prevent
                />
              </div>
              <div v-if="drawingImages.length === 0" class="drawing-placeholder">
                <el-icon :size="64" color="#ccc"><Picture /></el-icon>
                <p>暂无图纸</p>
              </div>
            </div>
          </el-scrollbar>
        </div>
      </div>

      <!-- 中间：3D模型 -->
      <div class="center-viewer">
        <div class="model-container" ref="modelContainer">
          <!-- Three.js 渲染区域 -->
        </div>

        <!-- 3D控制 -->
        <div class="model-controls">
          <div class="controls-row">
            <el-button-group>
              <el-button :icon="Refresh" @click="resetCamera">重置视角</el-button>
              <el-button
                :icon="View"
                :type="isExploded ? 'primary' : ''"
                @click="toggleExplode"
              >
                {{ isExploded ? '收起' : '爆炸' }}视图
              </el-button>
              <el-button
                :icon="Grid"
                :type="isWireframe ? 'primary' : ''"
                @click="toggleWireframe"
              >
                线框模式
              </el-button>
            </el-button-group>
          </div>

          <!-- 爆炸比例滑块 -->
          <div v-if="isExploded" class="explode-slider">
            <span class="slider-label">爆炸程度:</span>
            <el-slider
              v-model="explodeScale"
              :min="0"
              :max="50"
              :step="1"
              style="width: 300px; margin: 0 12px;"
            />
            <span class="slider-value">{{ explodeScale }}%</span>
          </div>
        </div>
      </div>

      <!-- 右侧：当前步骤详情 -->
      <div class="right-sidebar">
        <el-scrollbar height="100%">
          <!-- 当前步骤 -->
          <div class="step-detail-card" v-if="currentStepData">
            <div class="step-header">
              <div class="step-badge">{{ currentStepIndex + 1 }}</div>
              <h2>{{ currentStepData.title }}</h2>
            </div>

            <div class="step-content">
              <!-- 描述 -->
              <div class="description-section">
                <p class="description-text">{{ currentStepData.operation || currentStepData.description }}</p>
              </div>

              <!-- 操作步骤 -->
              <div class="operations-section" v-if="currentStepData.operation_steps">
                <h3>📝 操作步骤</h3>
                <ol class="operation-list">
                  <li v-for="(op, index) in currentStepData.operation_steps" :key="index">
                    {{ op }}
                  </li>
                </ol>
              </div>

              <!-- 所需工具 -->
              <div class="tools-section" v-if="currentStepData.tools_required && currentStepData.tools_required.length">
                <h3>🔧 所需工具</h3>
                <div class="tools-tags">
                  <el-tag 
                    v-for="tool in currentStepData.tools_required" 
                    :key="tool"
                    type="info"
                    size="large"
                    effect="plain"
                  >
                    {{ tool }}
                  </el-tag>
                </div>
              </div>

              <!-- 关键点 -->
              <div class="keypoints-section" v-if="currentStepData.key_points && currentStepData.key_points.length">
                <h3>💡 关键点</h3>
                <ul class="keypoints-list">
                  <li v-for="(point, index) in currentStepData.key_points" :key="index">
                    {{ point }}
                  </li>
                </ul>
              </div>

              <!-- ✅ 移除：安全警告已在下方"安全"标签页中统一显示 -->

              <!-- ✅ 焊接要求（如果该步骤需要焊接） -->
              <div class="welding-section" v-if="currentStepData.welding && currentStepData.welding.required">
                <h3>⚡ 焊接要求</h3>
                <div class="welding-details">
                  <p v-if="currentStepData.welding.welding_type">
                    <strong>焊接类型：</strong>{{ currentStepData.welding.welding_type }}
                  </p>
                  <p v-if="currentStepData.welding.welding_method">
                    <strong>焊接方法：</strong>{{ currentStepData.welding.welding_method }}
                  </p>
                  <p v-if="currentStepData.welding.weld_size">
                    <strong>焊缝尺寸：</strong>{{ currentStepData.welding.weld_size }}
                  </p>
                  <p v-if="currentStepData.welding.welding_position">
                    <strong>焊接位置：</strong>{{ currentStepData.welding.welding_position }}
                  </p>
                  <p v-if="currentStepData.welding.quality_requirements">
                    <strong>质量要求：</strong>{{ currentStepData.welding.quality_requirements }}
                  </p>
                  <el-alert
                    v-if="currentStepData.welding.safety_notes"
                    :title="currentStepData.welding.safety_notes"
                    type="warning"
                    :closable="false"
                    show-icon
                    style="margin-top: 8px"
                  />
                </div>
              </div>

              <!-- 质检要求 -->
              <div class="operations-section" v-if="currentStepData.quality_check">
                <h3>✅ 质检要求</h3>
                <p>{{ currentStepData.quality_check }}</p>
              </div>

              <!-- 预计时间 -->
              <div class="time-section">
                <el-icon><Clock /></el-icon>
                <span>预计时间: {{ currentStepData.estimated_time_minutes }} 分钟</span>
              </div>
            </div>
          </div>

          <!-- 快速参考标签页 -->
          <div class="quick-reference-tabs">
            <el-tabs v-model="activeTab" type="border-card">
              <el-tab-pane label="焊接" name="welding">
                <div class="tab-content-scroll">
                  <div
                    v-for="(req, index) in currentStepWeldingRequirements"
                    :key="index"
                    class="ref-item"
                  >
                    <div class="ref-header">
                      <strong>步骤{{ req.step_number }} - {{ req.component }}</strong>
                      <el-tag type="warning" size="small" v-if="req.welding_info?.required">
                        需要焊接
                      </el-tag>
                    </div>
                    <p v-if="req.welding_info?.welding_position">📍 {{ req.welding_info.welding_position }}</p>
                    <el-text type="info" size="small" v-if="req.welding_info">
                      {{ req.welding_info.welding_type || req.welding_info.welding_method }} - {{ req.welding_info.weld_size }}
                    </el-text>
                  </div>
                  <el-empty v-if="!currentStepWeldingRequirements.length" description="当前步骤无焊接要求" />
                </div>
              </el-tab-pane>

              <el-tab-pane label="质检" name="quality">
                <div class="tab-content-scroll">
                  <div
                    v-for="(checkpoint, index) in qualityCheckpoints.slice(0, 3)"
                    :key="index"
                    class="ref-item"
                  >
                    <div class="ref-header">
                      <strong>步骤{{ checkpoint.step_number }} - {{ checkpoint.component }}</strong>
                    </div>
                    <p>{{ checkpoint.quality_check }}</p>
                  </div>
                  <el-empty v-if="!qualityCheckpoints.length" description="暂无质检要求" />
                </div>
              </el-tab-pane>

              <el-tab-pane label="安全" name="safety">
                <div class="tab-content-scroll">
                  <el-alert
                    v-for="(warning, index) in (manualData.safety_and_faq?.safety_warnings || manualData.safety_warnings || []).slice(0, 3)"
                    :key="index"
                    :title="`步骤${warning.step_number} - ${warning.component}`"
                    type="warning"
                    :description="warning.warning"
                    show-icon
                    :closable="false"
                    style="margin-bottom: 8px"
                  />
                  <el-empty v-if="!(manualData.safety_and_faq?.safety_warnings || manualData.safety_warnings || []).length" description="暂无安全警告" />
                </div>
              </el-tab-pane>

              <el-tab-pane label="FAQ" name="faq">
                <div class="tab-content-scroll">
                  <div
                    v-for="(faq, index) in (manualData.safety_and_faq?.faq_items || manualData.faq_items || []).slice(0, 2)"
                    :key="index"
                    class="ref-item"
                  >
                    <div class="ref-header">
                      <strong>Q: {{ faq.question }}</strong>
                    </div>
                    <p>A: {{ faq.answer?.substring(0, 80) }}...</p>
                  </div>
                  <el-empty v-if="!(manualData.safety_and_faq?.faq_items || manualData.faq_items || []).length" description="暂无常见问题" />
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-scrollbar>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-else class="loading-screen">
      <el-icon class="is-loading" :size="64">
        <Loading />
      </el-icon>
      <p>加载装配说明书中...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Loading, ArrowLeft, ArrowRight, Picture, Box,
  Refresh, View, Grid, Clock
} from '@element-plus/icons-vue'
import axios from 'axios'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'

// ✅ 接收路由参数 taskId
const props = defineProps<{
  taskId: string
}>()

const manualData = ref<any>(null)
const currentStepIndex = ref(0)
const activeTab = ref('welding')
const modelContainer = ref<HTMLElement | null>(null)

// Three.js 相关
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let renderer: THREE.WebGLRenderer | null = null
let controls: OrbitControls | null = null
let model: THREE.Group | null = null
let gridHelper: THREE.GridHelper | null = null

// 保存每个mesh的原始位置、材质和爆炸方向
let meshOriginalPositions: Map<string, THREE.Vector3> = new Map()
let meshOriginalMaterials: Map<string, THREE.Material> = new Map()
let meshExplodeDirections: Map<string, THREE.Vector3> = new Map()

const isExploded = ref(false)
const isWireframe = ref(false)
const explodeScale = ref(25) // 爆炸比例（0-50，默认25）

// 图纸缩放相关
const zoomedDrawingIndex = ref<number | null>(null)

// 获取当前步骤的图纸列表
const drawingImages = computed(() => {
  if (!currentStepData.value) {
    console.log('⚠️ 当前步骤数据为空')
    return []
  }

  const stepData = currentStepData.value

  // 1. 优先从当前步骤中获取图纸
  const stepDrawings = stepData.drawings ||
                       stepData.pdf_images ||
                       stepData.technical_drawings ||
                       stepData.drawing_images ||
                       []

  if (Array.isArray(stepDrawings) && stepDrawings.length > 0) {
    console.log(`✅ 步骤${currentStepIndex.value + 1}有${stepDrawings.length}张图纸`)
    return stepDrawings
  }

  // 2. 如果步骤中没有图纸，尝试从全局获取
  if (manualData.value) {
    // 从3d_resources中获取
    const resources3d = manualData.value['3d_resources']
    if (resources3d?.pdf_images && Array.isArray(resources3d.pdf_images)) {
      console.log('✅ 从3d_resources.pdf_images找到', resources3d.pdf_images.length, '张图纸（全局）')
      return resources3d.pdf_images
    }

    // 从product_assembly中获取
    const productAssembly = manualData.value.product_assembly
    if (productAssembly?.pdf_images && Array.isArray(productAssembly.pdf_images)) {
      console.log('✅ 从product_assembly.pdf_images找到', productAssembly.pdf_images.length, '张图纸（全局）')
      return productAssembly.pdf_images
    }
  }

  // 3. ⚠️ 临时方案：如果都没有，使用默认路径
  // TODO: 等后端在每个步骤中添加图纸字段后，这段代码会自动失效
  console.warn(`⚠️ 步骤${currentStepIndex.value + 1}未找到图纸数据，使用默认路径（临时方案）`)
  const taskId = props.taskId
  return [
    `http://localhost:8000/api/manual/${taskId}/pdf_images/page_001.png`,
    `http://localhost:8000/api/manual/${taskId}/pdf_images/page_002.png`
  ]
})

const productName = computed(() => {
  if (!manualData.value) return '加载中...'
  return manualData.value?.product_overview?.product_name || '装配说明书'
})

// ✅ 构建完整的步骤列表：组件装配 + 产品装配
const allSteps = computed(() => {
  const steps = []

  // 1. 添加组件装配步骤（按assembly_order排序）
  const componentAssembly = manualData.value?.component_assembly || []
  for (const component of componentAssembly) {
    const componentSteps = component.steps || []
    for (const step of componentSteps) {
      steps.push({
        ...step,
        chapter_type: 'component_assembly',
        component_code: component.component_code,
        component_name: component.component_name,
        glb_file: component.glb_file
      })
    }
  }

  // 2. 添加产品装配步骤
  const productSteps = manualData.value?.product_assembly?.steps || []
  for (const step of productSteps) {
    steps.push({
      ...step,
      chapter_type: 'product_assembly',
      glb_file: 'product_total.glb'
    })
  }

  return steps
})

const totalSteps = computed(() => {
  return allSteps.value.length
})

const currentStepData = computed(() => {
  const stepData = allSteps.value[currentStepIndex.value]

  // 调试：查看步骤数据中是否有图纸字段
  if (stepData) {
    console.log(`📋 步骤${currentStepIndex.value + 1}的数据:`, stepData)
    console.log(`🎨 步骤${currentStepIndex.value + 1}的字段:`, Object.keys(stepData))
  }

  return stepData
})

const currentStepParts = computed(() => {
  // ✅ 兼容两种数据结构：parts_used 或 fasteners
  return currentStepData.value?.parts_used || currentStepData.value?.fasteners || []
})

// ✅ 根据当前步骤的零件自动生成3D高亮mesh列表
const currentStepHighlightMeshes = computed(() => {
  const highlightMeshes: string[] = []
  const allParts: any[] = []

  // ✅ 收集所有需要高亮的零件（主要组件 + 紧固件 + parts_used）
  // 1. 产品装配步骤：components + fasteners
  if (currentStepData.value?.components) {
    allParts.push(...currentStepData.value.components)
  }
  if (currentStepData.value?.fasteners) {
    allParts.push(...currentStepData.value.fasteners)
  }

  // 2. 组件装配步骤：parts_used
  if (currentStepData.value?.parts_used) {
    allParts.push(...currentStepData.value.parts_used)
  }

  // ✅ 优先使用零件中的mesh_id字段（直接指定）
  allParts.forEach((part: any) => {
    if (part.mesh_id) {
      // mesh_id可能是数组或单个值
      if (Array.isArray(part.mesh_id)) {
        highlightMeshes.push(...part.mesh_id)
        console.log(`  ✅ ${part.bom_code || part.code} → ${part.mesh_id.length} 个mesh (直接指定):`, part.mesh_id)
      } else {
        highlightMeshes.push(part.mesh_id)
        console.log(`  ✅ ${part.bom_code || part.code} → 1 个mesh (直接指定):`, part.mesh_id)
      }
    } else {
      // 如果没有mesh_id，尝试通过bom_to_mesh映射查找
      const bomCode = part.bom_code || part.code
      const bomToMesh = manualData.value?.['3d_resources']?.bom_to_mesh

      if (bomCode && bomToMesh && bomToMesh[bomCode]) {
        const meshes = bomToMesh[bomCode]
        highlightMeshes.push(...meshes)
        console.log(`  ✅ ${bomCode} → ${meshes.length} 个mesh (BOM映射):`, meshes)
      } else if (bomCode) {
        console.warn(`  ⚠️  ${bomCode} 没有mesh_id，也没有在bom_to_mesh中找到`)
      }
    }
  })

  console.log(`🎯 步骤${currentStepIndex.value + 1}需要高亮的零件:`, allParts.map(p => p.bom_code || p.code))
  console.log(`🎯 步骤${currentStepIndex.value + 1}需要高亮的mesh (${highlightMeshes.length}个):`, highlightMeshes)
  return highlightMeshes
})

// 图纸点击放大功能
const toggleDrawingZoom = (index: number) => {
  if (zoomedDrawingIndex.value === index) {
    zoomedDrawingIndex.value = null
  } else {
    zoomedDrawingIndex.value = index
  }
}

// ✅ 过滤当前步骤的焊接信息
const currentStepWeldingRequirements = computed(() => {
  const allWelding = manualData.value?.welding_requirements || []
  const currentStep = currentStepData.value

  if (!currentStep) return []

  // 获取当前步骤的步骤号
  const currentStepNumber = currentStep.step_number

  // 过滤出当前步骤的焊接信息
  return allWelding.filter(req => req.step_number === currentStepNumber)
})

// ✅ 从所有步骤中提取质检要求
const qualityCheckpoints = computed(() => {
  const checkpoints: any[] = []

  // 从组件装配步骤中提取
  const componentAssembly = manualData.value?.component_assembly || []
  for (const component of componentAssembly) {
    const steps = component.steps || []
    for (const step of steps) {
      if (step.quality_check) {
        checkpoints.push({
          step_number: step.step_number,
          component: component.component_name,
          quality_check: step.quality_check
        })
      }
    }
  }

  // 从产品装配步骤中提取
  const productSteps = manualData.value?.product_assembly?.steps || []
  for (const step of productSteps) {
    if (step.quality_check) {
      checkpoints.push({
        step_number: step.step_number,
        component: '产品总装',
        quality_check: step.quality_check
      })
    }
  }

  return checkpoints
})

const progressPercentage = computed(() => {
  if (totalSteps.value === 0) return 0
  return ((currentStepIndex.value + 1) / totalSteps.value) * 100
})

const progressColor = computed(() => {
  const percentage = progressPercentage.value
  if (percentage < 30) return '#409eff'
  if (percentage < 70) return '#e6a23c'
  return '#67c23a'
})

// ✅ 初始化3D查看器和模型
const init3DViewerAndModel = async () => {
  console.log('🚀 开始初始化3D查看器和模型...')
  await new Promise(resolve => setTimeout(resolve, 100)) // 等待DOM更新
  console.log('⏰ DOM更新等待完成')
  init3DViewer()
  console.log('⏰ 3D查看器初始化完成，开始加载模型...')
  await load3DModel()
  console.log('🎉 3D查看器和模型初始化全部完成')

  // ✅ 延迟后重新调整渲染器尺寸，确保容器已完全渲染
  await new Promise(resolve => setTimeout(resolve, 200))
  if (modelContainer.value && renderer && camera) {
    const width = modelContainer.value.clientWidth
    const height = modelContainer.value.clientHeight
    console.log('🔄 重新调整渲染器尺寸:', { width, height })
    camera.aspect = width / height
    camera.updateProjectionMatrix()
    renderer.setSize(width, height)
  }
}

// ✅ 优先从 localStorage 加载，如果没有再从 API 加载
const loadLocalJSON = async () => {
  if (!props.taskId) {
    ElMessage.error('任务ID不存在')
    return
  }

  try {
    // 1. 先尝试从 localStorage 加载
    const currentManual = localStorage.getItem('current_manual')
    if (currentManual) {
      manualData.value = JSON.parse(currentManual)
      console.log('✅ 从缓存加载说明书成功:', manualData.value)
      console.log('📋 manualData的所有字段:', Object.keys(manualData.value))
      ElMessage.success('装配说明书加载成功！')

      // ✅ 数据加载完成后初始化3D
      await init3DViewerAndModel()
      return
    }

    // 2. 如果缓存没有，从后端 API 获取
    const response = await axios.get(`http://localhost:8000/api/manual/${props.taskId}`)
    manualData.value = response.data

    // 保存到 localStorage
    localStorage.setItem('current_manual', JSON.stringify(manualData.value))

    console.log('✅ 从API加载说明书成功:', manualData.value)
    console.log('📋 manualData的所有字段:', Object.keys(manualData.value))
    ElMessage.success('装配说明书加载成功！')

    // ✅ 数据加载完成后初始化3D
    await init3DViewerAndModel()
  } catch (error: any) {
    console.error('❌ 加载失败:', error)
    ElMessage.error('加载失败: ' + (error.response?.data?.detail || error.message || '未知错误'))
  }
}

const previousStep = () => {
  if (currentStepIndex.value > 0) {
    currentStepIndex.value--
  }
}

const nextStep = () => {
  if (currentStepIndex.value < totalSteps.value - 1) {
    currentStepIndex.value++
  }
}

const goToStep = (index: number) => {
  currentStepIndex.value = index
}

const getImportanceType = (importance: string) => {
  const map: any = { '关键': 'danger', '重要': 'warning', '一般': 'info' }
  return map[importance] || 'info'
}

const getSeverityType = (severity: string) => {
  const map: any = { '高': 'error', '中': 'warning', '低': 'info' }
  return map[severity] || 'warning'
}

const init3DViewer = () => {
  console.log('🎬 开始初始化3D查看器...')

  if (!modelContainer.value) {
    console.error('❌ modelContainer 不存在')
    return
  }

  const container = modelContainer.value
  const width = container.clientWidth
  const height = container.clientHeight

  console.log('📐 容器尺寸:', { width, height })

  if (width === 0 || height === 0) {
    console.error('❌ 容器尺寸为0，无法初始化3D')
    return
  }

  // 创建场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xf0f2f5)
  console.log('✅ 场景创建成功')

  // 创建相机
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 10000)
  camera.position.set(500, 500, 500)

  // 创建渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  container.appendChild(renderer.domElement)
  console.log('✅ 渲染器创建成功，已添加到DOM')

  // 添加光源（增强亮度）
  const ambientLight = new THREE.AmbientLight(0xffffff, 1.2)  // 环境光增强到1.2
  scene.add(ambientLight)

  const directionalLight1 = new THREE.DirectionalLight(0xffffff, 1.0)  // 主光源
  directionalLight1.position.set(100, 100, 50)
  scene.add(directionalLight1)

  const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.6)  // 补光
  directionalLight2.position.set(-100, 50, -50)
  scene.add(directionalLight2)

  const directionalLight3 = new THREE.DirectionalLight(0xffffff, 0.4)  // 顶部补光
  directionalLight3.position.set(0, 200, 0)
  scene.add(directionalLight3)

  // 添加控制器
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05

  // 添加底部地面网格（初始位置，会在模型加载后调整）
  const gridSize = 5000  // 大网格
  gridHelper = new THREE.GridHelper(gridSize, 50, 0x888888, 0xcccccc)
  gridHelper.position.y = -1000  // 临时位置
  scene.add(gridHelper)

  // 动画循环
  const animate = () => {
    requestAnimationFrame(animate)
    if (controls) controls.update()
    if (renderer && scene && camera) {
      renderer.render(scene, camera)
    }
  }
  animate()
  console.log('🎬 动画循环已启动')

  // ✅ 调试：暴露到window对象
  ;(window as any).__three_debug__ = { scene, camera, renderer, controls }

  // 窗口大小调整
  const handleResize = () => {
    if (!container || !camera || !renderer) return
    const width = container.clientWidth
    const height = container.clientHeight
    camera.aspect = width / height
    camera.updateProjectionMatrix()
    renderer.setSize(width, height)
  }
  window.addEventListener('resize', handleResize)
}

const load3DModel = async () => {
  console.log('🎨 开始加载3D模型...')

  if (!scene) {
    console.error('❌ scene 不存在，无法加载模型')
    return
  }

  if (!manualData.value) {
    console.error('❌ manualData 不存在，无法获取GLB路径')
    return
  }

  try {
    const loader = new GLTFLoader()

    // ✅ 获取当前步骤对应的GLB文件
    const currentStep = allSteps.value[currentStepIndex.value]
    const glbFile = currentStep?.glb_file || 'product_total.glb'

    // ✅ 构建完整的GLB文件路径
    const glbPath = `http://localhost:8000/api/manual/${props.taskId}/glb/${glbFile}`
    console.log('📦 加载3D模型:', glbPath)
    console.log('📋 当前步骤:', currentStepIndex.value + 1, '/', allSteps.value.length)
    console.log('📋 GLB文件:', glbFile)

    const gltf = await loader.loadAsync(glbPath)
    console.log('✅ GLB文件加载成功:', gltf)

    model = gltf.scene

    // 先不保存位置，等模型居中后再保存
    let meshCount = 0
    const meshNames: string[] = []
    model.traverse((child: any) => {
      if (child.isMesh) {
        meshCount++
        meshNames.push(child.name)

        // 创建新的高对比度材质（天蓝色，清晰锐利）
        const brightMaterial = new THREE.MeshStandardMaterial({
          color: 0x4A90E2,        // 天蓝色
          metalness: 0.5,
          roughness: 0.4,
          side: THREE.DoubleSide  // 双面渲染
        })

        child.material = brightMaterial
        meshOriginalMaterials.set(child.name, brightMaterial.clone())
      }
    })

    console.log('🔍 模型中的mesh数量:', meshCount)
    console.log('🔍 前20个mesh名称:', meshNames.slice(0, 20))

    // 计算模型边界并居中
    const box = new THREE.Box3().setFromObject(model)
    const center = box.getCenter(new THREE.Vector3())
    const size = box.getSize(new THREE.Vector3())

    console.log('📏 模型尺寸:', {
      size: { x: size.x, y: size.y, z: size.z },
      center: { x: center.x, y: center.y, z: center.z }
    })

    // ✅ 如果模型太小（单位可能是米，但实际是毫米建模），放大倍数
    const maxDimOriginal = Math.max(size.x, size.y, size.z)
    let scaleFactor = 1

    // 根据模型尺寸自动计算放大倍数，目标是让模型达到1500-2000单位（根据图纸1830mm）
    if (maxDimOriginal < 10) {
      scaleFactor = 1000000  // 如果小于10，放大100万倍（模型单位可能是米）
    } else if (maxDimOriginal < 100) {
      scaleFactor = 10000   // 如果小于100，放大1万倍
    } else if (maxDimOriginal < 1000) {
      scaleFactor = 1000    // 如果小于1000，放大1000倍
    }

    if (scaleFactor > 1) {
      console.warn(`⚠️ 模型太小（${maxDimOriginal.toFixed(6)}），放大${scaleFactor}倍`)
      model.scale.set(scaleFactor, scaleFactor, scaleFactor)
      // 重新计算边界
      box.setFromObject(model)
      box.getCenter(center)
      box.getSize(size)
      console.log('📏 放大后的模型尺寸:', {
        size: { x: size.x, y: size.y, z: size.z },
        center: { x: center.x, y: center.y, z: center.z },
        scaleFactor
      })
    }

    // 移动模型到中心
    model.position.sub(center)

    // ✅ 模型居中后，保存每个mesh的本地位置和爆炸方向
    const localCenter = new THREE.Vector3(0, 0, 0)
    let nearCenterCount = 0

    model.traverse((child: any) => {
      if (child.isMesh) {
        // 保存本地坐标位置（相对于父对象model）
        const localPos = child.position.clone()
        meshOriginalPositions.set(child.name, localPos)

        // 计算并保存爆炸方向（从中心指向零件，纯径向）
        const direction = new THREE.Vector3()
        direction.subVectors(localPos, localCenter)

        const distance = direction.length()

        // ✅ 优化：降低阈值，让更多零件使用实际位置计算方向
        if (distance < 0.0001) {
          // 如果零件非常接近中心点，使用随机方向避免重叠
          const theta = Math.random() * Math.PI * 2
          const phi = Math.random() * Math.PI
          direction.set(
            Math.sin(phi) * Math.cos(theta),
            Math.cos(phi),
            Math.sin(phi) * Math.sin(theta)
          )
          nearCenterCount++
        } else {
          // 归一化：严格从中心指向零件的方向
          direction.normalize()
        }

        meshExplodeDirections.set(child.name, direction)
      }
    })
    console.log('✅ 已保存', meshOriginalPositions.size, '个mesh的位置和爆炸方向')
    if (nearCenterCount > 0) {
      console.log(`⚠️ ${nearCenterCount} 个零件非常接近中心，使用随机方向`)
    }

    // 调整相机位置以适应模型
    const maxDim = Math.max(size.x, size.y, size.z)
    console.log('📏 最大尺寸:', maxDim)

    const fov = camera!.fov * (Math.PI / 180)
    let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2))
    cameraZ *= 2.5 // 增加距离，确保能看到

    console.log('📷 计算的相机距离:', cameraZ)

    // ✅ 如果计算出的距离太小（模型单位可能是毫米），使用固定距离
    if (cameraZ < 10) {
      console.warn('⚠️ 相机距离太小，使用固定距离')
      cameraZ = Math.max(maxDim * 3, 1000) // 至少1000单位
    }

    console.log('📷 最终相机距离:', cameraZ)

    camera!.position.set(cameraZ * 0.7, cameraZ * 0.5, cameraZ * 0.7)
    camera!.lookAt(0, 0, 0)

    if (controls) {
      controls.target.set(0, 0, 0)
      controls.update()
    }

    console.log('📷 相机位置:', camera!.position)
    console.log('🎯 控制器目标:', controls?.target)

    scene.add(model)
    console.log('✅ 3D模型已添加到场景')
    console.log('📊 模型信息:', {
      meshCount: meshOriginalPositions.size,
      boundingBox: size,
      center,
      cameraPosition: camera!.position,
      modelPosition: model.position
    })

    // ✅ 调整网格位置，紧贴模型底部
    if (gridHelper) {
      const modelBox = new THREE.Box3().setFromObject(model)
      const modelMin = modelBox.min
      gridHelper.position.y = modelMin.y  // 网格Y坐标 = 模型最低点Y坐标
      console.log('✅ 网格已调整到模型底部，Y =', modelMin.y)
    }

    // ✅ 调试：暴露model到window对象
    ;(window as any).__three_debug__.model = model

    ElMessage.success('3D模型加载成功！')

    // 高亮当前步骤的零件
    highlightStepParts()
  } catch (error: any) {
    console.error('❌ 3D模型加载失败:', error)
    ElMessage.error('3D模型加载失败: ' + (error.message || '未知错误'))
  }
}

// 切换GLB模型
const switchGLBModel = async (glbFile: string) => {
  console.log('🔄 开始切换GLB模型:', glbFile)

  if (!scene) {
    console.error('❌ scene 不存在，无法切换模型')
    return
  }

  try {
    // 1. 清除旧模型
    if (model) {
      console.log('🗑️ 清除旧模型')
      scene.remove(model)
      model.traverse((child: any) => {
        if (child.isMesh) {
          child.geometry?.dispose()
          child.material?.dispose()
        }
      })
    }

    // 2. 清空材质缓存
    meshOriginalMaterials.clear()
    meshOriginalPositions.clear()

    // 3. 加载新模型
    const loader = new GLTFLoader()
    const glbPath = `http://localhost:8000/api/manual/${props.taskId}/glb/${glbFile}`
    console.log('📦 加载新模型:', glbPath)

    const gltf = await loader.loadAsync(glbPath)
    console.log('✅ 新模型加载成功')

    model = gltf.scene

    // 4. 初始化材质
    let meshCount = 0
    model.traverse((child: any) => {
      if (child.isMesh) {
        meshCount++
        const brightMaterial = new THREE.MeshStandardMaterial({
          color: 0x4A90E2,
          metalness: 0.5,
          roughness: 0.4,
          side: THREE.DoubleSide
        })
        child.material = brightMaterial
        meshOriginalMaterials.set(child.name, brightMaterial.clone())
        meshOriginalPositions.set(child.name, child.position.clone())
      }
    })

    console.log('🔍 新模型mesh数量:', meshCount)

    // 5. 居中和缩放
    const box = new THREE.Box3().setFromObject(model)
    const center = box.getCenter(new THREE.Vector3())
    const size = box.getSize(new THREE.Vector3())

    const maxDimOriginal = Math.max(size.x, size.y, size.z)
    let scaleFactor = 1

    if (maxDimOriginal < 10) {
      scaleFactor = 1000000
    } else if (maxDimOriginal < 100) {
      scaleFactor = 10000
    } else if (maxDimOriginal < 1000) {
      scaleFactor = 1000
    }

    if (scaleFactor > 1) {
      console.log(`⚠️ 模型太小（${maxDimOriginal.toFixed(6)}），放大${scaleFactor}倍`)
      model.scale.set(scaleFactor, scaleFactor, scaleFactor)
      box.setFromObject(model)
      box.getCenter(center)
      box.getSize(size)
    }

    model.position.set(-center.x, -center.y, -center.z)

    // 6. 调整相机
    const maxDim = Math.max(size.x, size.y, size.z)
    let cameraZ = maxDim * 2.5

    if (cameraZ < 100) {
      cameraZ = Math.max(maxDim * 3, 1000)
    }

    camera!.position.set(cameraZ * 0.7, cameraZ * 0.5, cameraZ * 0.7)
    camera!.lookAt(0, 0, 0)

    if (controls) {
      controls.target.set(0, 0, 0)
      controls.update()
    }

    // 7. 添加到场景
    scene.add(model)
    console.log('✅ 新模型已添加到场景')

    // 8. 调整网格
    if (gridHelper) {
      const modelBox = new THREE.Box3().setFromObject(model)
      gridHelper.position.y = modelBox.min.y
    }

    // 9. 重置爆炸状态
    isExploded.value = false

    ElMessage.success(`已切换到${glbFile}`)
  } catch (error: any) {
    console.error('❌ 切换模型失败:', error)
    ElMessage.error('切换模型失败: ' + (error.message || '未知错误'))
  }
}

// 高亮当前步骤的零件
const highlightStepParts = () => {
  if (!model || !currentStepData.value) {
    console.log('⚠️ 无法高亮：model或currentStepData不存在')
    return
  }

  // ✅ 优先使用步骤中的3d_highlight，否则使用自动生成的高亮列表
  const highlightMeshes = currentStepData.value['3d_highlight'] || currentStepHighlightMeshes.value
  console.log('🎯 步骤', currentStepIndex.value + 1, '高亮mesh列表:', highlightMeshes)

  // 将JSON中的mesh ID转换为GLB中的实际mesh名称
  // JSON格式: "mesh_145" -> GLB格式: "NAUO145"
  const convertMeshId = (meshId: string): string => {
    if (meshId.startsWith('mesh_')) {
      const number = meshId.replace('mesh_', '')
      // 移除前导零：mesh_003 -> NAUO3, mesh_014 -> NAUO14
      const numericValue = parseInt(number, 10)
      return `NAUO${numericValue}`
    }
    return meshId
  }

  // 收集模型中所有mesh的名称（用于调试）
  const allMeshNames: string[] = []
  model.traverse((child: any) => {
    if (child.isMesh) {
      allMeshNames.push(child.name)
    }
  })
  console.log('📦 模型中的所有mesh (前10个):', allMeshNames.slice(0, 10))

  // 重置所有mesh的材质
  model.traverse((child: any) => {
    if (child.isMesh) {
      const originalMaterial = meshOriginalMaterials.get(child.name)
      if (originalMaterial) {
        child.material = originalMaterial.clone()
        child.material.transparent = true
        child.material.opacity = 0.3
      }
    }
  })

  // 高亮指定的mesh
  if (highlightMeshes.length > 0) {
    let highlightedCount = 0
    const convertedMeshIds = highlightMeshes.map(convertMeshId)
    console.log('🔄 转换后的mesh ID:', convertedMeshIds)

    const allMeshNames: string[] = []
    model.traverse((child: any) => {
      if (child.isMesh) {
        allMeshNames.push(child.name)
        if (convertedMeshIds.includes(child.name)) {
          console.log('✅ 找到并高亮mesh:', child.name)
          // 创建高亮材质（黄色发光）
          const highlightMaterial = new THREE.MeshStandardMaterial({
            color: 0xffff00,
            emissive: 0xffaa00,
            emissiveIntensity: 0.8,
            metalness: 0.3,
            roughness: 0.4
          })
          child.material = highlightMaterial
          highlightedCount++
        }
      }
    })

    console.log('🔍 模型中所有mesh名称（前50个）:', allMeshNames.slice(0, 50))
    console.log('🔍 需要匹配的mesh ID:', convertedMeshIds.slice(0, 10))
    console.log(`💡 成功高亮 ${highlightedCount}/${highlightMeshes.length} 个零件`)
  }
}

// 应用爆炸效果（按装配步骤层级爆炸）
const applyExplode = () => {
  if (!model) return

  // ✅ 使用allSteps（包含组件装配+产品装配）
  const steps = allSteps.value

  console.log('🔧 applyExplode 被调用', {
    hasModel: !!model,
    hasManualData: !!manualData.value,
    stepsCount: steps.length,
    isExploded: isExploded.value,
    explodeScale: explodeScale.value
  })

  let processedCount = 0
  let sampleMesh: any = null

  model.traverse((child: any) => {
    if (child.isMesh) {
      const originalLocalPos = meshOriginalPositions.get(child.name)
      const explodeDirection = meshExplodeDirections.get(child.name)

      if (originalLocalPos && explodeDirection) {
        if (isExploded.value && explodeScale.value > 0) {
          // 使用保存的爆炸方向（已经归一化）
          const direction = explodeDirection.clone()

          // 简单的径向爆炸：所有零件都从中心向外推
          // 使用统一的爆炸距离
          const explodeDistance = explodeScale.value * 0.05

          // 计算偏移量
          const offset = direction.multiplyScalar(explodeDistance)
          const newLocalPos = originalLocalPos.clone().add(offset)

          child.position.copy(newLocalPos)
          processedCount++

          // 保存第一个mesh用于调试
          if (!sampleMesh) {
            sampleMesh = {
              name: child.name,
              explodeDistance,
              originalPos: originalLocalPos.clone(),
              newPos: newLocalPos.clone(),
              direction: explodeDirection.clone(),
              offset: offset.clone()
            }
          }
        } else {
          // 恢复原始位置
          child.position.copy(originalLocalPos)
          processedCount++
        }
      }
    }
  })

  if (processedCount > 0) {
    console.log(`🔄 爆炸视图更新: ${isExploded.value ? '展开' : '收起'}, 比例=${explodeScale.value}%, 处理了${processedCount}个零件`)
    if (sampleMesh) {
      const dirLen = Math.sqrt(
        sampleMesh.direction.x ** 2 +
        sampleMesh.direction.y ** 2 +
        sampleMesh.direction.z ** 2
      )
      console.log('📍 示例零件 (径向爆炸):', {
        name: sampleMesh.name,
        原始位置: `(${sampleMesh.originalPos.x.toFixed(2)}, ${sampleMesh.originalPos.y.toFixed(2)}, ${sampleMesh.originalPos.z.toFixed(2)})`,
        新位置: `(${sampleMesh.newPos.x.toFixed(2)}, ${sampleMesh.newPos.y.toFixed(2)}, ${sampleMesh.newPos.z.toFixed(2)})`,
        方向: `(${sampleMesh.direction.x.toFixed(3)}, ${sampleMesh.direction.y.toFixed(3)}, ${sampleMesh.direction.z.toFixed(3)})`,
        方向长度: dirLen.toFixed(3),
        偏移量: `(${sampleMesh.offset.x.toFixed(2)}, ${sampleMesh.offset.y.toFixed(2)}, ${sampleMesh.offset.z.toFixed(2)})`,
        爆炸距离: sampleMesh.explodeDistance.toFixed(2)
      })
    }
  }
}

// 爆炸视图开关
const toggleExplode = () => {
  if (!model) return
  isExploded.value = !isExploded.value
  applyExplode()
}

// 监听爆炸比例变化
watch(explodeScale, () => {
  if (isExploded.value) {
    applyExplode()
  }
})

// 线框模式
const toggleWireframe = () => {
  if (!model) return

  isWireframe.value = !isWireframe.value

  model.traverse((child: any) => {
    if (child.isMesh) {
      if (child.material) {
        child.material.wireframe = isWireframe.value
      }
    }
  })
}

// 重置相机
const resetCamera = () => {
  if (!camera || !controls || !model) return

  const box = new THREE.Box3().setFromObject(model)
  const center = box.getCenter(new THREE.Vector3())
  const size = box.getSize(new THREE.Vector3())

  const maxDim = Math.max(size.x, size.y, size.z)
  const fov = camera.fov * (Math.PI / 180)
  let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2))
  cameraZ *= 1.5

  camera.position.set(cameraZ, cameraZ, cameraZ)
  camera.lookAt(0, 0, 0)
  controls.target.set(0, 0, 0)
  controls.update()
}



// 监听步骤变化，更新高亮和GLB模型
watch(currentStepIndex, async (newIndex, oldIndex) => {
  const newStep = allSteps.value[newIndex]
  const oldStep = allSteps.value[oldIndex]

  // 检查是否需要切换GLB文件
  const newGlbFile = newStep?.glb_file
  const oldGlbFile = oldStep?.glb_file

  if (newGlbFile && oldGlbFile && newGlbFile !== oldGlbFile) {
    console.log(`🔄 切换GLB模型: ${oldGlbFile} → ${newGlbFile}`)
    await switchGLBModel(newGlbFile)
  }

  highlightStepParts()

  // 如果当前是爆炸状态，重新应用爆炸
  if (isExploded.value) {
    isExploded.value = false
    toggleExplode()
  }
})

onMounted(() => {
  // ✅ 只需要加载数据，3D初始化会在数据加载完成后自动执行
  loadLocalJSON()
})

onUnmounted(() => {
  if (renderer) {
    renderer.dispose()
  }
  if (controls) {
    controls.dispose()
  }
})
</script>

<style scoped lang="scss">
.worker-manual-viewer {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
  overflow: hidden;
}

.top-bar {
  height: 100px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  gap: 24px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);

  .product-info {
    min-width: 250px;

    h1 {
      margin: 0 0 8px 0;
      font-size: 24px;
      font-weight: 700;
    }
  }

  .progress-section {
    flex: 1;

    .progress-info {
      display: flex;
      align-items: baseline;
      gap: 8px;
      margin-bottom: 8px;

      .current-step {
        font-size: 32px;
        font-weight: 700;
      }

      .total-steps {
        font-size: 20px;
        opacity: 0.8;
      }

      .step-title {
        font-size: 16px;
        margin-left: 16px;
        opacity: 0.9;
      }
    }
  }

  .top-actions {
    display: flex;
    gap: 12px;
  }
}

.main-workspace {
  flex: 1;
  display: grid;
  grid-template-columns: 300px 1fr 400px;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

.left-sidebar, .right-sidebar {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.left-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;

  .section-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 12px;
    color: #333;
    display: flex;
    align-items: center;
    justify-content: space-between;

    .page-indicator {
      font-size: 14px;
      color: #666;
      font-weight: normal;
    }
  }

  .drawing-section-full {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .drawings-container {
      flex: 1;
      height: 100%;
    }

    .drawings-list {
      display: flex;
      flex-direction: column;
      gap: 16px;
      padding: 8px;
    }

    .drawing-item {
      background: #fafafa;
      border: 2px solid #e5e7eb;
      border-radius: 8px;
      overflow: hidden;
      cursor: pointer;
      transition: all 0.3s ease;

      &:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
      }

      &.zoomed {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: 9999;
        border-radius: 0;
        border: none;
        background: rgba(0, 0, 0, 0.95);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;

        .drawing-image {
          max-width: 95vw;
          max-height: 95vh;
          width: auto;
          height: auto;
        }
      }

      .drawing-image {
        width: 100%;
        height: auto;
        display: block;
        background: white;
        user-select: none;
        -webkit-user-drag: none;
      }
    }

    .drawing-placeholder {
      width: 100%;
      height: 300px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 12px;
      background: #fafafa;
      border: 2px dashed #e5e7eb;
      border-radius: 8px;

      p {
        margin: 0;
        color: #999;
      }
    }
  }

  .drawing-section-old {
    flex: 1;

    .drawing-viewer {
      height: 100%;
      background: #fafafa;
      border: 2px solid #e5e7eb;
      border-radius: 8px;
      overflow: hidden;
      position: relative;
      transition: all 0.3s ease;
      user-select: none;

      &.zoomed {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: 9999;
        border-radius: 0;
        background: rgba(0, 0, 0, 0.95);
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .drawing-image {
        width: 100%;
        height: 100%;
        object-fit: contain;
        background: white;
        transition: transform 0.2s ease;
        transform-origin: center center;
        user-select: none;
        -webkit-user-drag: none;
      }

      .drawing-placeholder {
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 12px;

        p {
          margin: 0;
          color: #999;
        }
      }

      .drawing-nav-buttons {
        position: absolute;
        bottom: 16px;
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        gap: 12px;
        z-index: 10;

        :deep(.el-button) {
          background: rgba(255, 255, 255, 0.9);
          backdrop-filter: blur(4px);

          &:hover:not(:disabled) {
            background: white;
          }
        }
      }
    }
  }

  .parts-section {
    .parts-list {
      display: flex;
      flex-direction: column;
      gap: 8px;

      .part-card {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        background: #f9fafb;
        border-radius: 8px;
        border: 1px solid #e5e7eb;

        .part-icon {
          font-size: 32px;
        }

        .part-details {
          flex: 1;

          .part-name {
            font-weight: 600;
            margin-bottom: 4px;
          }

          .part-code {
            font-size: 12px;
            color: #666;
            margin-bottom: 4px;
          }
        }
      }

      .empty-hint {
        text-align: center;
        padding: 24px;
        color: #999;
      }
    }
  }
}

.center-viewer {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;

  .model-container {
    flex: 1;
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);

    canvas {
      display: block;
      width: 100%;
      height: 100%;
    }
  }

  .model-controls {
    padding: 16px;
    border-top: 1px solid #e5e7eb;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;

    .controls-row {
      display: flex;
      justify-content: center;
    }

    .explode-slider {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background: #f5f7fa;
      border-radius: 8px;

      .slider-label {
        font-size: 14px;
        color: #666;
        white-space: nowrap;
      }

      .slider-value {
        font-size: 14px;
        font-weight: 600;
        color: #7c3aed;
        min-width: 45px;
        text-align: right;
      }
    }
  }
}

.right-sidebar {
  padding: 16px;

  .step-detail-card {
    margin-bottom: 16px;

    .step-header {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 20px;

      .step-badge {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        font-weight: 700;
        flex-shrink: 0;
      }

      h2 {
        margin: 0;
        font-size: 20px;
        color: #333;
      }
    }

    .step-content {
      h3 {
        font-size: 16px;
        margin: 16px 0 12px 0;
        color: #333;
      }

      .description-text {
        font-size: 15px;
        line-height: 1.8;
        color: #555;
        margin-bottom: 16px;
      }

      .operation-list {
        padding-left: 20px;
        margin: 0;

        li {
          margin-bottom: 8px;
          line-height: 1.6;
        }
      }

      .tools-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }

      .keypoints-list {
        padding-left: 20px;
        margin: 0;

        li {
          margin-bottom: 8px;
          line-height: 1.6;
          color: #555;
        }
      }

      .time-section {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid #e5e7eb;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        color: #666;
      }
    }
  }

  .quick-reference-tabs {
    .tab-content-scroll {
      max-height: 300px;
      overflow-y: auto;

      .ref-item {
        padding: 12px;
        margin-bottom: 12px;
        background: #f9fafb;
        border-radius: 8px;

        .ref-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        p {
          margin: 4px 0;
          font-size: 14px;
          color: #555;
        }
      }
    }
  }
}

.loading-screen {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;

  p {
    font-size: 18px;
    color: #666;
  }
}
</style>

