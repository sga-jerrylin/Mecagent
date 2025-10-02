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
      <!-- 左侧：图纸 + 零件 -->
      <div class="left-sidebar">
        <!-- 图纸参考 -->
        <div class="drawing-section">
          <div class="section-title">📐 图纸参考</div>
          <div
            class="drawing-viewer"
            :class="{ 'zoomed': isDrawingZoomed }"
            @click="toggleDrawingZoom"
            @mousedown="handleDrawingMouseDown"
            @mousemove="handleDrawingMouseMove"
            @mouseup="handleDrawingMouseUp"
            @mouseleave="handleDrawingMouseLeave"
          >
            <img
              v-if="currentDrawingImage"
              ref="drawingImage"
              :src="currentDrawingImage"
              alt="工程图纸"
              class="drawing-image"
              :style="drawingImageStyle"
              @wheel.prevent="handleDrawingWheel"
              @dragstart.prevent
            />
            <div v-else class="drawing-placeholder">
              <el-icon :size="64" color="#ccc"><Picture /></el-icon>
              <p>PDF图纸将在此显示</p>
            </div>
          </div>
        </div>

        <!-- 本步骤零件 -->
        <div class="parts-section">
          <div class="section-title">🔩 本步骤零件</div>
          <div class="parts-list">
            <div 
              v-for="part in currentStepParts" 
              :key="part.bom_code"
              class="part-card"
            >
              <div class="part-icon">📦</div>
              <div class="part-details">
                <div class="part-name">{{ part.bom_name }}</div>
                <div class="part-code">{{ part.bom_code }}</div>
                <el-tag size="small">x{{ part.qty }}</el-tag>
              </div>
            </div>
            <div v-if="!currentStepParts || currentStepParts.length === 0" class="empty-hint">
              <el-text type="info">本步骤无需零件</el-text>
            </div>
          </div>
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
                <p class="description-text">{{ currentStepData.description }}</p>
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

              <!-- 警告 -->
              <div class="warnings-section" v-if="currentStepData.warnings && currentStepData.warnings.length">
                <h3>⚠️ 注意事项</h3>
                <el-alert
                  v-for="(warning, index) in currentStepData.warnings"
                  :key="index"
                  :title="warning"
                  type="warning"
                  :closable="false"
                  show-icon
                  style="margin-bottom: 8px"
                />
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
                    v-for="(req, index) in manualData.welding_requirements.slice(0, 3)" 
                    :key="index"
                    class="ref-item"
                  >
                    <div class="ref-header">
                      <strong>{{ req.requirement_id }}</strong>
                      <el-tag :type="getImportanceType(req.importance)" size="small">
                        {{ req.importance }}
                      </el-tag>
                    </div>
                    <p>{{ req.welding_location }}</p>
                    <el-text type="info" size="small">{{ req.welding_type }} - {{ req.weld_size }}</el-text>
                  </div>
                </div>
              </el-tab-pane>

              <el-tab-pane label="质检" name="quality">
                <div class="tab-content-scroll">
                  <div 
                    v-for="(checkpoint, index) in manualData.quality_checkpoints.slice(0, 3)" 
                    :key="index"
                    class="ref-item"
                  >
                    <div class="ref-header">
                      <strong>{{ checkpoint.checkpoint_id }}</strong>
                    </div>
                    <p>{{ checkpoint.inspection_item }}</p>
                    <el-text type="success" size="small">✓ {{ checkpoint.acceptance_criteria }}</el-text>
                  </div>
                </div>
              </el-tab-pane>

              <el-tab-pane label="安全" name="safety">
                <div class="tab-content-scroll">
                  <el-alert
                    v-for="(warning, index) in manualData.safety_warnings.slice(0, 2)"
                    :key="index"
                    :title="warning.warning_title || '安全警告'"
                    :type="getSeverityType(warning.severity)"
                    :description="warning.description?.substring(0, 60) + '...'"
                    show-icon
                    :closable="false"
                    style="margin-bottom: 8px"
                  />
                </div>
              </el-tab-pane>

              <el-tab-pane label="FAQ" name="faq">
                <div class="tab-content-scroll">
                  <div 
                    v-for="(faq, index) in manualData.faq_items.slice(0, 2)" 
                    :key="index"
                    class="ref-item"
                  >
                    <div class="ref-header">
                      <strong>Q: {{ faq.question }}</strong>
                    </div>
                    <p>A: {{ faq.answer?.substring(0, 80) }}...</p>
                  </div>
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
let meshOriginalPositions: Map<string, THREE.Vector3> = new Map()
let meshOriginalMaterials: Map<string, THREE.Material> = new Map()

const isExploded = ref(false)
const isWireframe = ref(false)
const explodeScale = ref(25) // 爆炸比例（0-50，默认25）

// 图纸缩放相关
const drawingImage = ref<HTMLImageElement | null>(null)
const isDrawingZoomed = ref(false)
const drawingZoomScale = ref(1)
const drawingPanX = ref(0)
const drawingPanY = ref(0)
const isDragging = ref(false)
const hasDragged = ref(false)
const dragStartX = ref(0)
const dragStartY = ref(0)

const drawingImageStyle = computed(() => ({
  transform: `scale(${drawingZoomScale.value}) translate(${drawingPanX.value}px, ${drawingPanY.value}px)`,
  cursor: isDragging.value ? 'grabbing' : (isDrawingZoomed.value ? 'grab' : 'zoom-in')
}))

const productName = computed(() => {
  if (!manualData.value) return '加载中...'
  return manualData.value?.product_overview?.product_name || '装配说明书'
})

const totalSteps = computed(() => {
  return manualData.value?.assembly_steps?.length || 0
})

const currentStepData = computed(() => {
  if (!manualData.value?.assembly_steps) return null
  return manualData.value.assembly_steps[currentStepIndex.value]
})

const currentStepParts = computed(() => {
  return currentStepData.value?.parts_used || []
})

const currentDrawingImage = computed(() => {
  // 使用第一张PDF图片作为参考
  return '/pdf_images/page_001.png'
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

const loadLocalJSON = async () => {
  try {
    const response = await axios.get('/final_assembly_manual.json')
    manualData.value = response.data
    console.log('✅ JSON加载成功:', manualData.value)
    ElMessage.success('装配说明书加载成功！')
  } catch (error: any) {
    console.error('❌ 加载失败:', error)
    ElMessage.error('加载失败: ' + (error.message || '未知错误'))
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
  if (!modelContainer.value) return

  const container = modelContainer.value
  const width = container.clientWidth
  const height = container.clientHeight

  // 创建场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xf0f2f5)

  // 创建相机
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 10000)
  camera.position.set(500, 500, 500)

  // 创建渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  container.appendChild(renderer.domElement)

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

  // 添加网格
  const gridHelper = new THREE.GridHelper(1000, 20, 0x888888, 0xcccccc)
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
  if (!scene) return

  try {
    const loader = new GLTFLoader()
    const gltf = await loader.loadAsync('/models/model.glb')

    model = gltf.scene

    // 保存每个mesh的原始位置和材质，并改为高对比度的颜色
    model.traverse((child: any) => {
      if (child.isMesh) {
        meshOriginalPositions.set(child.name, child.position.clone())

        // 创建新的高对比度材质（天蓝色，清晰锐利）
        const brightMaterial = new THREE.MeshStandardMaterial({
          color: 0x4A90E2,        // 天蓝色（高对比度）
          metalness: 0.7,         // 较强的金属感
          roughness: 0.2,         // 非常光滑，反射清晰
          envMapIntensity: 1.5    // 强环境光反射
        })

        child.material = brightMaterial
        meshOriginalMaterials.set(child.name, brightMaterial.clone())
      }
    })

    // 计算模型边界并居中
    const box = new THREE.Box3().setFromObject(model)
    const center = box.getCenter(new THREE.Vector3())
    const size = box.getSize(new THREE.Vector3())

    // 移动模型到中心
    model.position.sub(center)

    // 调整相机位置以适应模型
    const maxDim = Math.max(size.x, size.y, size.z)
    const fov = camera!.fov * (Math.PI / 180)
    let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2))
    cameraZ *= 1.5 // 留一些边距

    camera!.position.set(cameraZ, cameraZ, cameraZ)
    camera!.lookAt(0, 0, 0)

    if (controls) {
      controls.target.set(0, 0, 0)
      controls.update()
    }

    scene.add(model)
    console.log('✅ 3D模型加载成功')
    ElMessage.success('3D模型加载成功！')

    // 高亮当前步骤的零件
    highlightStepParts()
  } catch (error: any) {
    console.error('❌ 3D模型加载失败:', error)
    ElMessage.error('3D模型加载失败: ' + (error.message || '未知错误'))
  }
}

// 高亮当前步骤的零件
const highlightStepParts = () => {
  if (!model || !currentStepData.value) return

  const highlightMeshes = currentStepData.value['3d_highlight'] || []
  console.log('🎯 高亮mesh列表:', highlightMeshes)

  // 将JSON中的mesh ID转换为GLB中的实际mesh名称
  // JSON格式: "mesh_145" -> GLB格式: "NAUO145"
  const convertMeshId = (meshId: string): string => {
    if (meshId.startsWith('mesh_')) {
      const number = meshId.replace('mesh_', '')
      return `NAUO${number}`
    }
    return meshId
  }

  // 重置所有mesh的材质
  model.traverse((child: any) => {
    if (child.isMesh) {
      const originalMaterial = meshOriginalMaterials.get(child.name)
      if (originalMaterial) {
        child.material = originalMaterial.clone()
      }
    }
  })

  // 高亮指定的mesh
  if (highlightMeshes.length > 0) {
    let highlightedCount = 0
    const convertedMeshIds = highlightMeshes.map(convertMeshId)
    console.log('🔄 转换后的mesh ID:', convertedMeshIds)

    model.traverse((child: any) => {
      if (child.isMesh) {
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
    console.log(`💡 成功高亮 ${highlightedCount}/${highlightMeshes.length} 个零件`)
  }
}

// 应用爆炸效果
const applyExplode = () => {
  if (!model) return

  // 计算模型中心
  const box = new THREE.Box3().setFromObject(model)
  const center = box.getCenter(new THREE.Vector3())
  const size = box.getSize(new THREE.Vector3())
  const maxDimension = Math.max(size.x, size.y, size.z)

  model.traverse((child: any) => {
    if (child.isMesh) {
      const originalPos = meshOriginalPositions.get(child.name)
      if (originalPos) {
        if (isExploded.value && explodeScale.value > 0) {
          // 计算从中心到mesh的方向向量
          const direction = new THREE.Vector3()
          direction.subVectors(originalPos, center)

          // 如果距离太小，给一个默认方向
          if (direction.length() < 0.1) {
            direction.set(
              Math.random() - 0.5,
              Math.random() - 0.5,
              Math.random() - 0.5
            )
          }

          direction.normalize()

          // 应用径向爆炸偏移，基于模型尺寸的百分比
          const offset = direction.multiplyScalar(maxDimension * explodeScale.value / 100)
          child.position.copy(originalPos).add(offset)
        } else {
          // 恢复原始位置
          child.position.copy(originalPos)
        }
      }
    }
  })
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

// 图纸缩放功能
const toggleDrawingZoom = (event: MouseEvent) => {
  // 如果发生了拖拽，不触发缩放
  if (hasDragged.value) {
    hasDragged.value = false
    return
  }

  isDrawingZoomed.value = !isDrawingZoomed.value
  if (!isDrawingZoomed.value) {
    // 恢复原始大小和位置
    drawingZoomScale.value = 1
    drawingPanX.value = 0
    drawingPanY.value = 0
  } else {
    // 放大到2倍
    drawingZoomScale.value = 2
  }
}

const handleDrawingWheel = (event: WheelEvent) => {
  if (!isDrawingZoomed.value) return

  // 滚轮缩放
  const delta = event.deltaY > 0 ? -0.1 : 0.1
  const newScale = drawingZoomScale.value + delta

  // 限制缩放范围：1倍到5倍
  drawingZoomScale.value = Math.max(1, Math.min(5, newScale))
}

// 图纸拖拽功能
const handleDrawingMouseDown = (event: MouseEvent) => {
  if (!isDrawingZoomed.value) return

  isDragging.value = true
  hasDragged.value = false
  dragStartX.value = event.clientX - drawingPanX.value
  dragStartY.value = event.clientY - drawingPanY.value

  event.preventDefault()
  event.stopPropagation()
}

const handleDrawingMouseMove = (event: MouseEvent) => {
  if (!isDragging.value || !isDrawingZoomed.value) return

  // 标记已经发生拖拽
  hasDragged.value = true

  drawingPanX.value = event.clientX - dragStartX.value
  drawingPanY.value = event.clientY - dragStartY.value

  event.preventDefault()
}

const handleDrawingMouseUp = () => {
  isDragging.value = false
}

const handleDrawingMouseLeave = () => {
  isDragging.value = false
}

// 监听步骤变化，更新高亮
watch(currentStepIndex, () => {
  highlightStepParts()
  // 如果当前是爆炸状态，重新应用爆炸
  if (isExploded.value) {
    isExploded.value = false
    toggleExplode()
  }
})

onMounted(() => {
  loadLocalJSON()
  setTimeout(() => {
    init3DViewer()
    load3DModel()
  }, 500)
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
  }

  .drawing-section {
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

