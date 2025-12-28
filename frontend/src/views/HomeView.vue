<template>

    <div class="app-container">
      <!-- 功能选择栏 -->
      <div class="feature-sidebar">
        <div class="feature-header">
          <h3>Feature Selection</h3>
          <button class="btn btn-ghost logout-btn" @click="handleLogout">
            Logout
          </button>
        </div>
        <div class="feature-options">
          <button
            :class="['feature-btn', { active: selectedFeature === 'chat' }]"
            @click="selectFeature('chat')"
          >
            <RouterLink to="/home/chat" >
              💬 Chat
            </RouterLink>
          </button>
          <button
            :class="['feature-btn', { active: selectedFeature === 'ppt' }]"
            @click="selectFeature('ppt')"
          >
            <RouterLink to="/home/ppt" >
              📊 PPT Generator
            </RouterLink>
          </button>
        </div>
      </div>

      <Layout :style="{padding: '1px', overflowY: 'auto', width: '100%'}">
            <RouterView></RouterView>
      </Layout>
    </div>
</template>

<script setup>
// 当前选中的功能
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const selectedFeature = ref('chat')

// 切换功能方法
const selectFeature = (feature) => {
  selectedFeature.value = feature
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

</script>

<style scoped>

.app-container {
  display: flex;
  width: 100%;        /* 占满视口宽度 */
  height: 100vh;       /* 占满视口高度 */
  background-color: #f5f5f5;
  overflow: hidden;    /* 防止子元素溢出导致滚动 */
}

/* 功能选择栏样式 */
.feature-sidebar {
  width: 40vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.feature-header {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(0, 0, 0, 0.05); /* 可选：轻微背景提升层次 */
  backdrop-filter: blur(4px); /* 可选：毛玻璃效果（如果背景是半透明）*/
}

.feature-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #ffffff;
  letter-spacing: 0.5px;
}

.feature-header .logout-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: #ffffff;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.feature-header .logout-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.4);
}

.feature-options {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}


.feature-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  padding: 12px 8px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 25px;
  font-weight: 500;
  transition: all 0.3s ease;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feature-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.feature-btn.active {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
}

/* 右侧内容区域 */
.content-wrapper {
  background: #fff;
  border-radius: 1px;
  /* 如果内容超出，wrapper 内部滚动 */
  overflow-y: auto;
}

</style>
