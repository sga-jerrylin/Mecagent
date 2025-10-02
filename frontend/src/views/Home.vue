<template>
  <div class="home-page">
    <!-- 英雄区域 -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-text">
          <h1 class="hero-title">
            <span class="gradient-text">智能装配说明书</span>
            <br>
            生成系统
          </h1>
          <p class="hero-subtitle">
            基于AI视觉识别和专家模型，自动将工程图纸和3D模型转换为工人友好的装配说明书
          </p>
          <div class="hero-features">
            <div class="feature-item">
              <el-icon><View /></el-icon>
              <span>AI视觉解析</span>
            </div>
            <div class="feature-item">
              <el-icon><Setting /></el-icon>
              <span>专家工艺</span>
            </div>
            <div class="feature-item">
              <el-icon><Monitor /></el-icon>
              <span>3D交互</span>
            </div>
          </div>
          <div class="hero-actions">
            <el-button
              type="primary"
              size="large"
              @click="$router.push('/generator')"
              class="cta-button"
            >
              <el-icon><DocumentAdd /></el-icon>
              开始生成
            </el-button>
            <el-button
              size="large"
              @click="$router.push('/settings')"
              class="settings-button"
            >
              <el-icon><Setting /></el-icon>
              API设置
            </el-button>
            <el-button
              size="large"
              @click="showDemo"
              class="demo-button"
            >
              <el-icon><VideoPlay /></el-icon>
              查看演示
            </el-button>
          </div>
        </div>
        
        <div class="hero-visual">
          <div class="visual-container">
            <!-- 3D预览 -->
            <div class="preview-3d">
              <ThreeViewer 
                :model-url="demoModelUrl"
                :auto-rotate="true"
                :show-grid="false"
              />
            </div>
            
            <!-- 浮动卡片 -->
            <div class="floating-cards">
              <div class="card card-1" :class="{ active: activeCard === 1 }">
                <el-icon><Document /></el-icon>
                <span>PDF解析</span>
              </div>
              <div class="card card-2" :class="{ active: activeCard === 2 }">
                <el-icon><Cpu /></el-icon>
                <span>AI分析</span>
              </div>
              <div class="card card-3" :class="{ active: activeCard === 3 }">
                <el-icon><Monitor /></el-icon>
                <span>3D渲染</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 功能特性 -->
    <section class="features-section">
      <div class="container">
        <h2 class="section-title">核心功能</h2>
        <div class="features-grid">
          <div class="feature-card" v-for="feature in features" :key="feature.id">
            <div class="feature-icon">
              <el-icon :size="32"><component :is="feature.icon" /></el-icon>
            </div>
            <h3>{{ feature.title }}</h3>
            <p>{{ feature.description }}</p>
            <div class="feature-tags">
              <el-tag 
                v-for="tag in feature.tags" 
                :key="tag" 
                size="small"
                effect="plain"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 工作流程 -->
    <section class="workflow-section">
      <div class="container">
        <h2 class="section-title">工作流程</h2>
        <div class="workflow-steps">
          <div 
            class="step" 
            v-for="(step, index) in workflowSteps" 
            :key="step.id"
            :class="{ active: currentStep === index }"
            @click="currentStep = index"
          >
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-content">
              <h4>{{ step.title }}</h4>
              <p>{{ step.description }}</p>
            </div>
            <div class="step-arrow" v-if="index < workflowSteps.length - 1">
              <el-icon><ArrowRight /></el-icon>
            </div>
          </div>
        </div>
        
        <!-- 步骤详情 -->
        <div class="step-detail" v-if="workflowSteps[currentStep]">
          <div class="detail-content">
            <h3>{{ workflowSteps[currentStep].title }}</h3>
            <p>{{ workflowSteps[currentStep].detail }}</p>
            <div class="detail-image">
              <img :src="workflowSteps[currentStep].image" :alt="workflowSteps[currentStep].title">
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 统计数据 -->
    <section class="stats-section">
      <div class="container">
        <div class="stats-grid">
          <div class="stat-item" v-for="stat in stats" :key="stat.label">
            <div class="stat-number">{{ animatedStats[stat.label] }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import ThreeViewer from '@/components/ThreeViewer.vue'
import { gsap } from 'gsap'

// 响应式数据
const activeCard = ref(1)
const currentStep = ref(0)
// ✅ 暂时禁用demo模型，避免加载不存在的文件导致错误
const demoModelUrl = ref('')  // 原值: '/models/demo.glb'

const animatedStats = reactive({
  '处理图纸': 0,
  '生成说明书': 0,
  '节省时间': 0,
  '准确率': 0
})

// 功能特性
const features = [
  {
    id: 1,
    icon: 'View',
    title: 'AI视觉识别',
    description: '基于Qwen3-VL模型，自动识别工程图纸中的BOM表格、技术要求、尺寸标注等信息',
    tags: ['OCR', '表格识别', '符号识别']
  },
  {
    id: 2,
    icon: 'Setting',
    title: '专家工艺生成',
    description: '20年经验的装配焊接专家模型，生成符合工业标准的装配工艺规程',
    tags: ['装配顺序', '焊接工艺', '质量控制']
  },
  {
    id: 3,
    icon: 'Monitor',
    title: '3D交互展示',
    description: '支持STL/STEP模型自动转换，提供爆炸视图、零件高亮等交互功能',
    tags: ['Three.js', '爆炸视图', '实时渲染']
  },
  {
    id: 4,
    icon: 'DocumentAdd',
    title: '智能说明书',
    description: '生成工人友好的HTML装配说明书，支持离线使用和移动设备',
    tags: ['响应式', 'PWA', '离线可用']
  }
]

// 工作流程
const workflowSteps = [
  {
    id: 1,
    title: '上传文件',
    description: '上传PDF工程图纸和3D模型文件',
    detail: '支持PDF格式的工程图纸和STL/STEP格式的3D模型文件。系统会自动验证文件格式和完整性。',
    image: '/images/step1.png'
  },
  {
    id: 2,
    title: 'AI解析',
    description: '视觉模型自动解析图纸内容',
    detail: 'Qwen3-VL视觉模型会自动识别BOM表格、技术要求、尺寸标注、焊接符号等关键信息，准确率超过95%。',
    image: '/images/step2.png'
  },
  {
    id: 3,
    title: '工艺生成',
    description: '专家模型生成装配工艺规程',
    detail: 'DeepSeek专家模型基于解析结果，结合20年工程经验，生成详细的装配步骤、质量要求和安全注意事项。',
    image: '/images/step3.png'
  },
  {
    id: 4,
    title: '3D处理',
    description: '自动转换和优化3D模型',
    detail: '使用Blender自动将STEP/STL模型转换为Web友好的GLB格式，并进行模型优化和材质处理。',
    image: '/images/step4.png'
  },
  {
    id: 5,
    title: '生成说明书',
    description: '输出交互式装配说明书',
    detail: '生成包含3D交互、步骤导航、质量检查的完整HTML装配说明书，工人可直接使用。',
    image: '/images/step5.png'
  }
]

// 统计数据
const stats = [
  { label: '处理图纸', value: 1250 },
  { label: '生成说明书', value: 890 },
  { label: '节省时间', value: 75 },
  { label: '准确率', value: 96 }
]

// 方法
const showDemo = () => {
  ElMessageBox.alert(
    '演示功能正在开发中，敬请期待！',
    '演示',
    {
      confirmButtonText: '了解',
      type: 'info'
    }
  )
}

// 动画效果
const animateCards = () => {
  const interval = setInterval(() => {
    activeCard.value = activeCard.value === 3 ? 1 : activeCard.value + 1
  }, 2000)
  
  onUnmounted(() => {
    clearInterval(interval)
  })
}

const animateStats = () => {
  stats.forEach(stat => {
    gsap.to(animatedStats, {
      [stat.label]: stat.value,
      duration: 2,
      ease: 'power2.out'
    })
  })
}

// 生命周期
onMounted(() => {
  animateCards()
  
  // 延迟启动统计动画
  setTimeout(() => {
    animateStats()
  }, 1000)
})
</script>

<style lang="scss" scoped>
.home-page {
  min-height: 100vh;
}

.hero-section {
  min-height: 100vh;
  display: flex;
  align-items: center;
  padding: 0 24px;
  
  .hero-content {
    max-width: 1400px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 60px;
    align-items: center;
  }
  
  .hero-text {
    .hero-title {
      font-size: 3.5rem;
      font-weight: 700;
      line-height: 1.2;
      margin-bottom: 24px;
      
      .gradient-text {
        background: linear-gradient(135deg, #409eff, #67c23a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
    }
    
    .hero-subtitle {
      font-size: 1.25rem;
      color: var(--el-text-color-secondary);
      line-height: 1.6;
      margin-bottom: 32px;
    }
    
    .hero-features {
      display: flex;
      gap: 24px;
      margin-bottom: 40px;
      
      .feature-item {
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--el-color-primary);
        font-weight: 500;
      }
    }
    
    .hero-actions {
      display: flex;
      gap: 16px;
      
      .cta-button {
        padding: 16px 32px;
        font-size: 16px;
        border-radius: 12px;
        background: linear-gradient(135deg, #409eff, #67c23a);
        border: none;
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(64, 158, 255, 0.3);
        }
      }
      
      .demo-button {
        padding: 16px 32px;
        font-size: 16px;
        border-radius: 12px;
        
        &:hover {
          transform: translateY(-2px);
        }
      }
    }
  }
  
  .hero-visual {
    .visual-container {
      position: relative;
      height: 500px;
      
      .preview-3d {
        width: 100%;
        height: 100%;
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      }
      
      .floating-cards {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        pointer-events: none;
        
        .card {
          position: absolute;
          background: rgba(255, 255, 255, 0.9);
          backdrop-filter: blur(10px);
          border-radius: 12px;
          padding: 16px 20px;
          display: flex;
          align-items: center;
          gap: 8px;
          box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
          transition: all 0.3s ease;
          opacity: 0.7;
          
          &.active {
            opacity: 1;
            transform: scale(1.05);
          }
          
          &.card-1 {
            top: 20px;
            left: 20px;
          }
          
          &.card-2 {
            top: 50%;
            right: 20px;
            transform: translateY(-50%);
          }
          
          &.card-3 {
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
          }
        }
      }
    }
  }
}

.features-section {
  padding: 100px 0;
  background: var(--el-fill-color-lighter);
  
  .container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
  }
  
  .section-title {
    text-align: center;
    font-size: 2.5rem;
    font-weight: 600;
    margin-bottom: 60px;
    color: var(--el-text-color-primary);
  }
  
  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 32px;
    
    .feature-card {
      background: var(--el-bg-color);
      border-radius: 16px;
      padding: 32px;
      text-align: center;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
      transition: all 0.3s ease;
      
      &:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
      }
      
      .feature-icon {
        width: 80px;
        height: 80px;
        background: linear-gradient(135deg, #409eff, #67c23a);
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 24px;
        color: white;
      }
      
      h3 {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 16px;
        color: var(--el-text-color-primary);
      }
      
      p {
        color: var(--el-text-color-secondary);
        line-height: 1.6;
        margin-bottom: 20px;
      }
      
      .feature-tags {
        display: flex;
        justify-content: center;
        gap: 8px;
        flex-wrap: wrap;
      }
    }
  }
}

.workflow-section {
  padding: 100px 0;
  
  .container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
  }
  
  .workflow-steps {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 60px;
    
    .step {
      display: flex;
      align-items: center;
      cursor: pointer;
      transition: all 0.3s ease;
      
      &.active {
        .step-number {
          background: var(--el-color-primary);
          color: white;
        }
        
        .step-content h4 {
          color: var(--el-color-primary);
        }
      }
      
      .step-number {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: var(--el-fill-color);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        margin-right: 16px;
        transition: all 0.3s ease;
      }
      
      .step-content {
        h4 {
          margin: 0 0 8px 0;
          font-weight: 600;
          transition: color 0.3s ease;
        }
        
        p {
          margin: 0;
          color: var(--el-text-color-secondary);
          font-size: 14px;
        }
      }
      
      .step-arrow {
        margin: 0 20px;
        color: var(--el-text-color-placeholder);
      }
    }
  }
  
  .step-detail {
    background: var(--el-bg-color);
    border-radius: 16px;
    padding: 40px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    
    .detail-content {
      text-align: center;
      
      h3 {
        font-size: 1.8rem;
        margin-bottom: 16px;
        color: var(--el-text-color-primary);
      }
      
      p {
        color: var(--el-text-color-secondary);
        line-height: 1.6;
        margin-bottom: 32px;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
      }
      
      .detail-image {
        img {
          max-width: 100%;
          height: auto;
          border-radius: 12px;
          box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
      }
    }
  }
}

.stats-section {
  padding: 80px 0;
  background: linear-gradient(135deg, #409eff, #67c23a);
  
  .container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px;
  }
  
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 40px;
    
    .stat-item {
      text-align: center;
      color: white;
      
      .stat-number {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 8px;
      }
      
      .stat-label {
        font-size: 1.1rem;
        opacity: 0.9;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .hero-section .hero-content {
    grid-template-columns: 1fr;
    gap: 40px;
    text-align: center;
  }
  
  .hero-text .hero-title {
    font-size: 2.5rem;
  }
  
  .workflow-steps {
    flex-direction: column;
    gap: 20px;
    
    .step-arrow {
      transform: rotate(90deg);
      margin: 10px 0;
    }
  }
}
</style>
