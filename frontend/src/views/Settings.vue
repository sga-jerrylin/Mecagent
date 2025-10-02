<template>
  <div class="settings-container">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </div>
      </template>

      <el-form :model="settings" label-width="150px" label-position="left">
        <!-- API密钥配置 -->
        <el-divider content-position="left">
          <el-icon><Key /></el-icon>
          <span style="margin-left: 8px;">API密钥配置</span>
        </el-divider>

        <el-form-item label="DashScope API Key">
          <el-input
            v-model="settings.dashscopeApiKey"
            type="password"
            show-password
            placeholder="请输入阿里云DashScope API Key"
            clearable
          >
            <template #prepend>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
          <div class="form-item-tip">
            用于Qwen-VL视觉模型，
            <el-link type="primary" href="https://dashscope.console.aliyun.com/" target="_blank">
              获取API Key
            </el-link>
          </div>
        </el-form-item>

        <el-form-item label="DeepSeek API Key">
          <el-input
            v-model="settings.deepseekApiKey"
            type="password"
            show-password
            placeholder="请输入DeepSeek API Key"
            clearable
          >
            <template #prepend>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
          <div class="form-item-tip">
            用于装配专家推理模型，
            <el-link type="primary" href="https://platform.deepseek.com/" target="_blank">
              获取API Key
            </el-link>
          </div>
        </el-form-item>

        <!-- 系统配置 -->
        <el-divider content-position="left">
          <el-icon><Tools /></el-icon>
          <span style="margin-left: 8px;">系统配置</span>
        </el-divider>

        <el-form-item label="WebSocket地址">
          <el-input
            v-model="settings.websocketUrl"
            placeholder="ws://localhost:8000"
            clearable
          >
            <template #prepend>
              <el-icon><Connection /></el-icon>
            </template>
          </el-input>
          <div class="form-item-tip">
            WebSocket服务器地址，用于实时进度推送
          </div>
        </el-form-item>

        <el-form-item label="API基础地址">
          <el-input
            v-model="settings.apiBaseUrl"
            placeholder="http://localhost:8000/api"
            clearable
          >
            <template #prepend>
              <el-icon><Link /></el-icon>
            </template>
          </el-input>
          <div class="form-item-tip">
            后端API服务器地址
          </div>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving">
            <el-icon><Select /></el-icon>
            <span>保存设置</span>
          </el-button>
          <el-button @click="resetSettings">
            <el-icon><RefreshLeft /></el-icon>
            <span>重置为默认</span>
          </el-button>
          <el-button @click="testConnection" :loading="testing">
            <el-icon><Connection /></el-icon>
            <span>测试连接</span>
          </el-button>
        </el-form-item>

        <!-- 状态信息 -->
        <el-alert
          v-if="statusMessage"
          :title="statusMessage"
          :type="statusType"
          :closable="false"
          show-icon
          style="margin-top: 20px;"
        />
      </el-form>
    </el-card>

    <!-- 使用说明 -->
    <el-card class="help-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <el-icon><QuestionFilled /></el-icon>
          <span>使用说明</span>
        </div>
      </template>

      <el-steps direction="vertical" :active="3">
        <el-step title="获取DashScope API Key">
          <template #description>
            <div>
              1. 访问 <el-link type="primary" href="https://dashscope.console.aliyun.com/" target="_blank">阿里云DashScope控制台</el-link><br>
              2. 登录/注册账号<br>
              3. 创建API Key并复制
            </div>
          </template>
        </el-step>
        <el-step title="获取DeepSeek API Key">
          <template #description>
            <div>
              1. 访问 <el-link type="primary" href="https://platform.deepseek.com/" target="_blank">DeepSeek开放平台</el-link><br>
              2. 登录/注册账号<br>
              3. 创建API Key并复制
            </div>
          </template>
        </el-step>
        <el-step title="配置并保存">
          <template #description>
            <div>
              1. 将API Key粘贴到上方输入框<br>
              2. 点击"保存设置"按钮<br>
              3. 点击"测试连接"验证配置是否正确
            </div>
          </template>
        </el-step>
      </el-steps>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, Key, Lock, Tools, Connection, Link, Select, RefreshLeft, QuestionFilled } from '@element-plus/icons-vue'
import axios from 'axios'

interface Settings {
  dashscopeApiKey: string
  deepseekApiKey: string
  websocketUrl: string
  apiBaseUrl: string
}

const settings = ref<Settings>({
  dashscopeApiKey: '',
  deepseekApiKey: '',
  websocketUrl: 'ws://localhost:8000',
  apiBaseUrl: 'http://localhost:8000/api'
})

const saving = ref(false)
const testing = ref(false)
const statusMessage = ref('')
const statusType = ref<'success' | 'warning' | 'error' | 'info'>('info')

// 加载设置
onMounted(() => {
  loadSettings()
})

const loadSettings = () => {
  const saved = localStorage.getItem('app_settings')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      settings.value = { ...settings.value, ...parsed }
    } catch (e) {
      console.error('加载设置失败:', e)
    }
  }
}

const saveSettings = async () => {
  saving.value = true
  statusMessage.value = ''
  
  try {
    // 保存到localStorage
    localStorage.setItem('app_settings', JSON.stringify(settings.value))
    
    // 发送到后端
    await axios.post(`${settings.value.apiBaseUrl}/settings`, {
      dashscope_api_key: settings.value.dashscopeApiKey,
      deepseek_api_key: settings.value.deepseekApiKey
    })
    
    statusMessage.value = '设置保存成功！'
    statusType.value = 'success'
    ElMessage.success('设置已保存')
  } catch (error: any) {
    statusMessage.value = `保存失败: ${error.message}`
    statusType.value = 'error'
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

const resetSettings = () => {
  settings.value = {
    dashscopeApiKey: '',
    deepseekApiKey: '',
    websocketUrl: 'ws://localhost:8000',
    apiBaseUrl: 'http://localhost:8000/api'
  }
  localStorage.removeItem('app_settings')
  statusMessage.value = '已重置为默认设置'
  statusType.value = 'info'
  ElMessage.info('已重置为默认设置')
}

const testConnection = async () => {
  testing.value = true
  statusMessage.value = ''
  
  try {
    const response = await axios.get(`${settings.value.apiBaseUrl}/health`)
    
    if (response.data.status === 'healthy') {
      statusMessage.value = '✅ 连接成功！后端服务运行正常'
      statusType.value = 'success'
      ElMessage.success('连接测试成功')
    } else {
      statusMessage.value = '⚠️ 后端服务状态异常'
      statusType.value = 'warning'
    }
  } catch (error: any) {
    statusMessage.value = `❌ 连接失败: ${error.message}`
    statusType.value = 'error'
    ElMessage.error('连接测试失败')
  } finally {
    testing.value = false
  }
}
</script>

<style scoped>
.settings-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.settings-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.form-item-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.help-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

:deep(.el-step__description) {
  padding-right: 20px;
  line-height: 1.8;
}
</style>

