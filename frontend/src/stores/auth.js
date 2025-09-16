/**
 * 认证状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token') || null)
  const loading = ref(false)

  // 计算属性
  // 只有用户信息和token信息都存在才能说登录成功
  const isAuthenticated = computed(() => !!token.value && !!user.value)

  // 初始化用户信息
  const initUser = async () => {
    if (token.value && !user.value) {
      try {
        const userData = await authAPI.getCurrentUser()
        user.value = userData
        localStorage.setItem('user_info', JSON.stringify(userData))
      } catch (error) {
        console.error('初始化用户信息失败:', error)
        logout()
      }
    }
  }

  // 登录
  const login = async (credentials) => {
    loading.value = true
    try {
      const response = await authAPI.login(credentials)
      token.value = response.access_token
      user.value = response.user
      
      // 保存到本地存储
      // assess_token指的是前端以后可以通过这个访问后端的所有接口
      // user_info就是用户名字，用户的id等等信息
      // 都保存在前端的全局变量库里面
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('user_info', JSON.stringify(response.user))
      
      return response
    } catch (error) {
        throw error
    } finally {
        loading.value = false
    }
  }

  // 注册
  const register = async (userData) => {
    loading.value = true
    try {
      const response = await authAPI.register(userData)
      token.value = response.access_token
      user.value = response.user
      
      // 保存到本地存储
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('user_info', JSON.stringify(response.user))
      
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  // 登出
  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
  }

  return {
    user,
    token,
    loading,
    isAuthenticated,
    initUser,
    login,
    register,
    logout
  }
})
