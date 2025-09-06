<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>AI对话助手</h1>
        <p>欢迎使用智能对话系统</p>
      </div>
      
      <div class="login-form">
        <div class="tab-buttons">
          <button 
            :class="['tab-btn', { active: isLogin }]"
            @click="isLogin = true"
          >
            登录
          </button>
          <button 
            :class="['tab-btn', { active: !isLogin }]"
            @click="isLogin = false"
          >
            注册
          </button>
        </div>

        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="username">用户名</label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              class="input"
              :class="{ error: errors.username }"
              placeholder="请输入用户名"
              required
            />
            <span v-if="errors.username" class="error-message">{{ errors.username }}</span>
          </div>

          <div class="form-group">
            <label for="password">密码</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              class="input"
              :class="{ error: errors.password }"
              placeholder="请输入密码"
              required
            />
            <span v-if="errors.password" class="error-message">{{ errors.password }}</span>
          </div>

          <div v-if="!isLogin" class="form-group">
            <label for="confirmPassword">确认密码</label>
            <input
              id="confirmPassword"
              v-model="form.confirmPassword"
              type="password"
              class="input"
              :class="{ error: errors.confirmPassword }"
              placeholder="请再次输入密码"
              required
            />
            <span v-if="errors.confirmPassword" class="error-message">{{ errors.confirmPassword }}</span>
          </div>

          <button 
            type="submit" 
            class="btn btn-primary submit-btn"
            :disabled="loading"
          >
            <div v-if="loading" class="loading"></div>
            {{ loading ? '处理中...' : (isLogin ? '登录' : '注册') }}
          </button>
        </form>

        <div v-if="errorMessage" class="alert alert-error">
          {{ errorMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 响应式数据
const isLogin = ref(true)
const loading = ref(false)
const errorMessage = ref('')

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const errors = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

// 表单验证
const validateForm = () => {
  errors.username = ''
  errors.password = ''
  errors.confirmPassword = ''

  let isValid = true

  if (!form.username.trim()) {
    errors.username = '请输入用户名'
    isValid = false
  } else if (form.username.length < 3) {
    errors.username = '用户名至少3个字符'
    isValid = false
  }

  if (!form.password) {
    errors.password = '请输入密码'
    isValid = false
  } else if (form.password.length < 6) {
    errors.password = '密码至少6个字符'
    isValid = false
  }

  if (!isLogin.value && form.password !== form.confirmPassword) {
    errors.confirmPassword = '两次输入的密码不一致'
    isValid = false
  }

  return isValid
}

// 提交表单
const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    if (isLogin.value) {
      await authStore.login({
        username: form.username,
        password: form.password
      })
    } else {
      await authStore.register({
        username: form.username,
        password: form.password
      })
    }
    
    // 登录/注册成功，跳转到聊天页面
    router.push('/chat')
  } catch (error) {
    console.error('认证失败:', error)
    if (error.response?.data?.detail) {
      errorMessage.value = error.response.data.detail
    } else {
      errorMessage.value = isLogin.value ? '登录失败，请检查用户名和密码' : '注册失败，请重试'
    }
  } finally {
    loading.value = false
  }
}

// 切换登录/注册模式时清空表单
const resetForm = () => {
  form.username = ''
  form.password = ''
  form.confirmPassword = ''
  errors.username = ''
  errors.password = ''
  errors.confirmPassword = ''
  errorMessage.value = ''
}

// 监听模式切换
const handleModeSwitch = (mode) => {
  isLogin.value = mode
  resetForm()
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.login-header {
  padding: 40px 30px 20px;
  text-align: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.login-header h1 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
}

.login-header p {
  font-size: 16px;
  opacity: 0.9;
}

.login-form {
  padding: 30px;
}

.tab-buttons {
  display: flex;
  margin-bottom: 30px;
  border-radius: 8px;
  background-color: #f8f9fa;
  padding: 4px;
}

.tab-btn {
  flex: 1;
  padding: 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.tab-btn.active {
  background: white;
  color: #007bff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.submit-btn {
  width: 100%;
  margin-top: 10px;
  padding: 14px;
  font-size: 16px;
  font-weight: 600;
}

.error-message {
  color: #dc3545;
  font-size: 12px;
  margin-top: 4px;
  display: block;
}

.alert {
  padding: 12px 16px;
  border-radius: 8px;
  margin-top: 20px;
  font-size: 14px;
}

.alert-error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

@media (max-width: 480px) {
  .login-container {
    padding: 16px;
  }
  
  .login-card {
    max-width: 100%;
  }
  
  .login-form {
    padding: 20px;
  }
  
  .login-header {
    padding: 30px 20px 15px;
  }
  
  .login-header h1 {
    font-size: 24px;
  }
}
</style>
