/**
 * 路由配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
// 在用户从一个页面（路由）跳转到另一个页面（路由）之前、之中或之后，进行拦截和检查，
// 根据检查结果决定是“放行”还是“ redirect（重定向）到其他地方”

// 下面写的是beforeEach，所以是在任何页面跳转前就都会在这个函数进行处理
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 初始化用户信息
  if (authStore.token && !authStore.user) {
    try {
      await authStore.initUser()
    } catch (error) {
      console.error('初始化用户信息失败:', error)
    }
  }
  
  // 检查认证状态
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/chat')
  } else {
    next()
  }
})

export default router
