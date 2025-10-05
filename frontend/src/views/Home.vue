<template>
  <div class="home-page">
    <!-- 粒子背景 -->
    <div class="particles-bg" ref="particlesBg"></div>

    <!-- 主要内容区域 -->
    <section class="hero-section">
      <div class="hero-content">
        <!-- 左侧：主要信息 -->
        <div class="hero-main">
          <div class="system-status">
            <div class="status-indicator" :class="{ active: systemActive }"></div>
            <span class="status-text">{{ systemActive ? 'AI系统在线' : '系统离线' }}</span>
          </div>

          <h1 class="hero-title">
            <span class="title-line">
              <span class="gradient-text creative-title">
                <span class="char-animation" style="--delay: 0s">智</span>
                <span class="char-animation" style="--delay: 0.1s">能</span>
                <span class="char-animation" style="--delay: 0.2s">装</span>
                <span class="char-animation" style="--delay: 0.3s">配</span>
                <span class="char-animation" style="--delay: 0.4s">说</span>
                <span class="char-animation" style="--delay: 0.5s">明</span>
                <span class="char-animation" style="--delay: 0.6s">书</span>
              </span>
            </span>
            <span class="title-line">
              <span class="subtitle-text glow-text">AI Assembly Manual Generator</span>
            </span>
          </h1>

          <div class="hero-description">
            <p class="description-text">
              基于多Agent协作的智能装配说明书生成系统
            </p>
            <p class="tech-specs">
              🤖 6个AI智能体协同工作 | 📊 实时处理监控 | 🔧 专业级装配指导
            </p>
          </div>

          <div class="action-panel">
            <div class="primary-actions">
              <el-button
                type="primary"
                size="large"
                @click="$router.push('/generator')"
                class="main-cta"
              >
                <el-icon><Upload /></el-icon>
                开始生成说明书
              </el-button>
              <el-button
                size="large"
                @click="$router.push('/engineer')"
                class="monitor-btn"
              >
                <el-icon><Monitor /></el-icon>
                监控台
              </el-button>
            </div>

            <div class="quick-actions">
              <el-button
                text
                @click="$router.push('/viewer')"
                class="quick-btn"
              >
                <el-icon><View /></el-icon>
                查看历史
              </el-button>
              <el-button
                text
                @click="showSystemInfo"
                class="quick-btn"
              >
                <el-icon><InfoFilled /></el-icon>
                系统信息
              </el-button>
            </div>
          </div>
        </div>

        <!-- 右侧：3D模型展示 -->
        <div class="data-panel">
          <div class="panel-header">
            <h3>🔧 3D装配预览</h3>
            <div class="model-controls">
              <el-button
                :type="autoRotate ? 'primary' : 'default'"
                @click="toggleAutoRotate"
                size="small"
                class="rotate-btn"
              >
                {{ autoRotate ? '停止旋转' : '自动旋转' }}
              </el-button>
            </div>
          </div>

          <!-- 3D模型容器 -->
          <div ref="threeContainer" class="three-container"></div>

          <!-- Agent状态面板 -->
          <div class="agents-panel">
            <h4>🤖 AI智能体状态</h4>
            <div class="agents-grid">
              <div
                v-for="agent in agentList"
                :key="agent.id"
                class="agent-card"
                :class="{ active: agent.status === 'online' }"
              >
                <div class="agent-icon">{{ agent.icon }}</div>
                <div class="agent-info">
                  <div class="agent-name">{{ agent.name }}</div>
                  <div class="agent-status">{{ agent.status === 'online' ? '在线' : '离线' }}</div>
                </div>
                <div class="agent-indicator" :class="agent.status"></div>
              </div>
            </div>
          </div>

          <!-- 实时数据统计 -->
          <div class="metrics-grid">
            <div class="metric-card">
              <div class="metric-value">{{ metrics.totalProjects }}</div>
              <div class="metric-label">总项目数</div>
              <div class="metric-trend">+{{ metrics.todayProjects }} 今日</div>
            </div>

            <div class="metric-card">
              <div class="metric-value">{{ metrics.activeAgents }}/6</div>
              <div class="metric-label">活跃Agent</div>
              <div class="metric-trend">{{ metrics.agentStatus }}</div>
            </div>

            <div class="metric-card">
              <div class="metric-value">{{ metrics.avgProcessTime }}s</div>
              <div class="metric-label">平均处理时间</div>
              <div class="metric-trend">-12% 优化</div>
            </div>

            <div class="metric-card">
              <div class="metric-value">{{ metrics.successRate }}%</div>
              <div class="metric-label">成功率</div>
              <div class="metric-trend">+5% 提升</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { Upload, Monitor, View, InfoFilled } from '@element-plus/icons-vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

// 响应式数据
const systemActive = ref(true)
const autoRotate = ref(true)
const dataRefreshing = ref(false)
const titleText = ref(null)
const particlesBg = ref(null)
const threeContainer = ref<HTMLElement>()

// 实时数据统计
const metrics = reactive({
  totalProjects: 156,
  todayProjects: 8,
  activeAgents: 6,
  agentStatus: '全部在线',
  avgProcessTime: 45,
  successRate: 98.5
})

// 6个AI智能体信息
const agentList = reactive([
  {
    id: 1,
    name: '视觉规划智能体',
    icon: '👁️',
    status: 'online',
    description: '分析图纸，规划装配顺序'
  },
  {
    id: 2,
    name: 'BOM-3D匹配智能体',
    icon: '🔗',
    status: 'online',
    description: '匹配BOM表与3D模型'
  },
  {
    id: 3,
    name: '组件装配智能体',
    icon: '🔧',
    status: 'online',
    description: '生成组件装配步骤'
  },
  {
    id: 4,
    name: '产品总装智能体',
    icon: '🏗️',
    status: 'online',
    description: '生成产品总装步骤'
  },
  {
    id: 5,
    name: '焊接工艺智能体',
    icon: '⚡',
    status: 'online',
    description: '识别焊接符号，生成工艺要求'
  },
  {
    id: 6,
    name: '安全FAQ智能体',
    icon: '🛡️',
    status: 'online',
    description: '生成安全警告和FAQ'
  }
])

// Three.js 相关变量
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let model: THREE.Group
let animationId: number

// 初始化Three.js场景
const initThreeJS = () => {
  if (!threeContainer.value) return

  // 创建场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a2e)

  // 创建相机
  camera = new THREE.PerspectiveCamera(
    75,
    threeContainer.value.clientWidth / threeContainer.value.clientHeight,
    0.1,
    1000
  )
  camera.position.set(8, 8, 8)

  // 创建渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(threeContainer.value.clientWidth, threeContainer.value.clientHeight)
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  threeContainer.value.appendChild(renderer.domElement)

  // 创建控制器
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.autoRotate = autoRotate.value
  controls.autoRotateSpeed = 2

  // 添加更强的光源
  const ambientLight = new THREE.AmbientLight(0x404040, 0.8)
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 1.5)
  directionalLight.position.set(10, 10, 5)
  directionalLight.castShadow = true
  scene.add(directionalLight)

  // 添加额外的点光源
  const pointLight = new THREE.PointLight(0x60a5fa, 1, 100)
  pointLight.position.set(5, 5, 5)
  scene.add(pointLight)

  // 加载GLB模型
  loadModel()

  // 开始渲染循环
  animate()
}

// 加载GLB模型
const loadModel = () => {
  const loader = new GLTFLoader()

  // 尝试加载现有的GLB文件
  loader.load(
    '/产品测试.glb',
    (gltf) => {
      model = gltf.scene

      // 计算模型边界盒，自动调整大小
      const box = new THREE.Box3().setFromObject(model)
      const size = box.getSize(new THREE.Vector3())
      const maxDim = Math.max(size.x, size.y, size.z)
      const scale = 4 / maxDim // 让模型占据更大空间

      model.scale.set(scale, scale, scale)
      model.position.set(0, 0, 0)

      // 遍历模型的所有材质，设置为明亮的颜色
      model.traverse((child) => {
        if (child.isMesh) {
          child.castShadow = true
          child.receiveShadow = true
          if (child.material) {
            // 设置明亮的蓝色调
            child.material.color.setHex(0x60a5fa)
            child.material.metalness = 0.3
            child.material.roughness = 0.4
            child.material.emissive.setHex(0x001122) // 轻微发光
          }
        }
      })

      scene.add(model)
      console.log('GLB模型加载成功')
    },
    (progress) => {
      console.log('Loading progress:', progress)
    },
    (error) => {
      console.error('Error loading model:', error)
      // 如果加载失败，创建一个简单的几何体作为替代
      createFallbackModel()
    }
  )
}

// 创建备用模型
const createFallbackModel = () => {
  const geometry = new THREE.BoxGeometry(3, 3, 3)
  const material = new THREE.MeshPhongMaterial({
    color: 0x60a5fa,
    transparent: true,
    opacity: 0.9,
    emissive: 0x001122
  })
  model = new THREE.Mesh(geometry, material)
  model.castShadow = true
  scene.add(model)
}

// 动画循环
const animate = () => {
  animationId = requestAnimationFrame(animate)

  controls.update()

  // 如果启用自动旋转且有模型（以自己为圆心旋转）
  if (autoRotate.value && model) {
    model.rotation.y += 0.008 // 稍微慢一点的旋转
  }

  renderer.render(scene, camera)
}

// 切换自动旋转
const toggleAutoRotate = () => {
  autoRotate.value = !autoRotate.value
  if (controls) {
    controls.autoRotate = autoRotate.value
  }
}

// 窗口大小调整
const handleResize = () => {
  if (!threeContainer.value || !camera || !renderer) return

  camera.aspect = threeContainer.value.clientWidth / threeContainer.value.clientHeight
  camera.updateProjectionMatrix()
  renderer.setSize(threeContainer.value.clientWidth, threeContainer.value.clientHeight)
}

// 系统信息
const showSystemInfo = () => {
  ElMessageBox.alert(
    `
    系统版本: v2.0.0
    AI引擎: Gemini 2.5 Flash
    Agent数量: 6个智能体
    支持格式: PDF, STEP, STL
    运行状态: 正常运行
    `,
    '系统信息',
    {
      confirmButtonText: '确定',
      type: 'info'
    }
  )
}

// 打字机效果
const typeWriter = (element: HTMLElement, text: string, speed: number = 100) => {
  let i = 0
  element.innerHTML = ''

  const timer = setInterval(() => {
    if (i < text.length) {
      element.innerHTML += text.charAt(i)
      i++
    } else {
      clearInterval(timer)
    }
  }, speed)
}

// 粒子背景动画
const initParticles = () => {
  if (!particlesBg.value) return

  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  particlesBg.value.appendChild(canvas)

  canvas.width = window.innerWidth
  canvas.height = window.innerHeight

  const particles = []
  const particleCount = 50

  // 创建粒子
  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      size: Math.random() * 2 + 1
    })
  }

  // 动画循环
  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    particles.forEach(particle => {
      particle.x += particle.vx
      particle.y += particle.vy

      if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1
      if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1

      ctx.beginPath()
      ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(64, 158, 255, 0.3)'
      ctx.fill()
    })

    requestAnimationFrame(animate)
  }

  animate()
}

// 数据刷新
const refreshData = () => {
  dataRefreshing.value = true

  setTimeout(() => {
    // 模拟数据更新
    metrics.totalProjects += Math.floor(Math.random() * 3)
    metrics.cpu = Math.floor(Math.random() * 40) + 20
    metrics.memory = Math.floor(Math.random() * 30) + 50
    metrics.gpu = Math.floor(Math.random() * 50) + 10

    dataRefreshing.value = false
  }, 1000)
}

// 组件挂载
onMounted(() => {
  // 打字机效果
  if (titleText.value) {
    typeWriter(titleText.value, '智能装配说明书', 150)
  }

  // 初始化粒子背景
  initParticles()

  // 初始化3D场景
  initThreeJS()
  window.addEventListener('resize', handleResize)

  // 数据刷新定时器
  const refreshInterval = setInterval(refreshData, 10000)

  // 系统状态定时器
  const statusInterval = setInterval(() => {
    systemActive.value = Math.random() > 0.1 // 90%在线率
  }, 5000)

  onUnmounted(() => {
    clearInterval(refreshInterval)
    clearInterval(statusInterval)
  })
})

// 组件卸载
onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  if (renderer && threeContainer.value) {
    threeContainer.value.removeChild(renderer.domElement)
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
.home-page {
  position: relative;
  min-height: 100vh;
  background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #2d3748 100%);
  overflow: hidden;
  transition: background 0.3s ease;

  // 浅色模式
  html:not(.dark) & {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%);
  }
}

// 粒子背景
.particles-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;

  canvas {
    width: 100%;
    height: 100%;
  }
}

// 主要内容
.hero-section {
  position: relative;
  z-index: 2;
  min-height: 100vh;
  display: flex;
  align-items: center;
  padding: 0 40px;

  .hero-content {
    max-width: 1400px;
    margin: 0 auto;
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 400px;
    gap: 60px;
    align-items: center;

    @media (max-width: 1200px) {
      grid-template-columns: 1fr;
      gap: 40px;
      text-align: center;
    }
  }
}

// 左侧主要内容
.hero-main {
  .system-status {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 32px;

    .status-indicator {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #ef4444;
      transition: all 0.3s ease;

      &.active {
        background: #10b981;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
        animation: pulse-green 2s infinite;
      }
    }

    .status-text {
      color: #94a3b8;
      font-size: 14px;
      font-weight: 500;
    }
  }

  .hero-title {
    margin-bottom: 32px;

    .title-line {
      display: block;

      .gradient-text {
        font-size: 4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa, #34d399, #fbbf24);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.1;

        @media (max-width: 768px) {
          font-size: 2.5rem;
        }

        &.creative-title {
          .char-animation {
            display: inline-block;
            animation: charBounce 2s ease-in-out infinite;
            animation-delay: var(--delay);
            transform-origin: center bottom;
          }
        }
      }

      .subtitle-text {
        font-size: 1.2rem;
        color: #64748b;
        font-weight: 400;
        margin-top: 8px;
        display: block;

        &.glow-text {
          text-shadow: 0 0 10px rgba(96, 165, 250, 0.5);
          animation: textGlow 3s ease-in-out infinite alternate;
        }
      }
    }
  }

  .hero-description {
    margin-bottom: 48px;

    .description-text {
      font-size: 1.3rem;
      color: #e2e8f0;
      margin-bottom: 16px;
      line-height: 1.6;
    }

    .tech-specs {
      font-size: 1rem;
      color: #94a3b8;
      line-height: 1.5;
    }
  }

  .action-panel {
    .primary-actions {
      display: flex;
      gap: 20px;
      margin-bottom: 24px;

      .main-cta {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        border: none;
        padding: 16px 32px;
        font-size: 16px;
        font-weight: 600;
        border-radius: 12px;
        transition: all 0.3s ease;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 12px 40px rgba(59, 130, 246, 0.4);
        }
      }

      .monitor-btn {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: #e2e8f0;
        padding: 16px 32px;
        font-size: 16px;
        border-radius: 12px;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;

        &:hover {
          background: rgba(255, 255, 255, 0.15);
          border-color: rgba(255, 255, 255, 0.3);
          transform: translateY(-2px);
        }
      }
    }

    .quick-actions {
      display: flex;
      gap: 24px;

      .quick-btn {
        color: #94a3b8;
        font-size: 14px;
        transition: all 0.3s ease;

        &:hover {
          color: #60a5fa;
        }
      }
    }
  }
}

// 右侧数据面板
.data-panel {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 32px;
  backdrop-filter: blur(20px);

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    h3 {
      margin: 0;
      color: #e2e8f0;
      font-size: 1.3rem;
      font-weight: 600;
    }

    .model-controls {
      .rotate-btn {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: #e2e8f0;

        &.el-button--primary {
          background: linear-gradient(135deg, #3b82f6, #1d4ed8);
          border: none;
          color: white;
        }

        &:hover {
          background: rgba(255, 255, 255, 0.15);
          border-color: rgba(255, 255, 255, 0.3);
        }
      }
    }
  }

  .three-container {
    height: 300px;
    margin-bottom: 24px;
    border-radius: 12px;
    overflow: hidden;
    background: rgba(0, 0, 0, 0.2);

    canvas {
      width: 100% !important;
      height: 100% !important;
      border-radius: 12px;
    }
  }

  .agents-panel {
    margin-bottom: 24px;

    h4 {
      margin: 0 0 16px 0;
      color: #e2e8f0;
      font-size: 1.1rem;
      font-weight: 600;
    }

    .agents-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;

      .agent-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 12px;
        display: flex;
        align-items: center;
        gap: 10px;
        transition: all 0.3s ease;

        &.active {
          border-color: rgba(16, 185, 129, 0.5);
          background: rgba(16, 185, 129, 0.1);
        }

        &:hover {
          background: rgba(255, 255, 255, 0.1);
          transform: translateY(-1px);
        }

        .agent-icon {
          font-size: 18px;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(96, 165, 250, 0.2);
          border-radius: 6px;
        }

        .agent-info {
          flex: 1;

          .agent-name {
            font-size: 12px;
            color: #e2e8f0;
            font-weight: 500;
            line-height: 1.2;
          }

          .agent-status {
            font-size: 10px;
            color: #94a3b8;
            margin-top: 2px;
          }
        }

        .agent-indicator {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #ef4444;

          &.online {
            background: #10b981;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
            animation: pulse-green 2s infinite;
          }
        }
      }
    }
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    margin-bottom: 32px;

    .metric-card {
      background: rgba(255, 255, 255, 0.05);
      border-radius: 12px;
      padding: 20px;
      text-align: center;
      border: 1px solid rgba(255, 255, 255, 0.1);

      .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #60a5fa;
        margin-bottom: 8px;
      }

      .metric-label {
        font-size: 12px;
        color: #94a3b8;
        margin-bottom: 4px;
      }

      .metric-trend {
        font-size: 11px;
        color: #10b981;
      }
    }
  }

  .system-health {
    h4 {
      margin: 0 0 20px 0;
      color: #e2e8f0;
      font-size: 1.1rem;
      font-weight: 600;
    }

    .health-bars {
      .health-item {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;

        span:first-child {
          width: 40px;
          font-size: 12px;
          color: #94a3b8;
        }

        .health-bar {
          flex: 1;
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          overflow: hidden;

          .health-fill {
            height: 100%;
            background: linear-gradient(90deg, #10b981, #34d399);
            border-radius: 4px;
            transition: width 0.5s ease;
          }
        }

        span:last-child {
          width: 35px;
          font-size: 12px;
          color: #e2e8f0;
          text-align: right;
        }
      }
    }
  }
}

// 动画
@keyframes pulse-green {
  0%, 100% {
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
  }
  50% {
    box-shadow: 0 0 30px rgba(16, 185, 129, 0.8);
  }
}

@keyframes charBounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0) scale(1);
  }
  40% {
    transform: translateY(-10px) scale(1.1);
  }
  60% {
    transform: translateY(-5px) scale(1.05);
  }
}

@keyframes textGlow {
  0% {
    text-shadow: 0 0 10px rgba(96, 165, 250, 0.5);
  }
  100% {
    text-shadow: 0 0 20px rgba(96, 165, 250, 0.8), 0 0 30px rgba(96, 165, 250, 0.6);
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes typing {
  from { width: 0; }
  to { width: 100%; }
}

// 响应式设计
@media (max-width: 768px) {
  .hero-section {
    padding: 0 20px;

    .hero-content {
      grid-template-columns: 1fr;
      gap: 40px;
    }
  }

  .data-panel {
    padding: 24px;

    .metrics-grid {
      grid-template-columns: 1fr;
      gap: 16px;
    }

    .three-container {
      height: 200px;
    }
  }

  .action-panel {
    .primary-actions {
      flex-direction: column;
      gap: 16px;

      .main-cta,
      .monitor-btn {
        width: 100%;
      }
    }

    .quick-actions {
      justify-content: center;
    }
  }
}
</style>