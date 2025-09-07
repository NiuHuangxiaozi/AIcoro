<template>
  <div class="chat-container">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h2>对话历史</h2>
        <button class="btn btn-primary new-chat-btn" @click="createNewChat">
          新对话
        </button>
      </div>
      
      <div class="sessions-list">
        <div
          v-for="session in sessions"
          :key="session.id"
          :class="['session-item', { active: currentSession?.id === session.id }]"
          @click="selectSession(session)"
        >
          <div class="session-info">
            <div class="session-title">{{ session.title }}</div>
            <div class="session-meta">
              {{ formatDate(session.updated_at) }} · {{ session.message_count }}条消息
            </div>
          </div>
          <button
            class="delete-btn"
            @click.stop="deleteSessionConfirm(session.id)"
            title="删除对话"
          >
            ×
          </button>
        </div>
        
        <div v-if="sessions.length === 0" class="empty-sessions">
          <p>暂无对话历史</p>
        </div>
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="chat-main">
      <!-- 顶部导航 -->
      <div class="chat-header">
        <div class="chat-title">
          <h1>AI对话助手</h1>
          <span v-if="currentSession" class="session-title">{{ currentSession.title }}</span>
        </div>
        
        <div class="user-info">
          <span class="username">{{ user?.username }}</span>
          <button class="btn btn-ghost logout-btn" @click="logout">
            登出
          </button>
        </div>
      </div>

      <!-- 消息区域 -->
      <div class="messages-container" ref="messagesContainer">
        <div class="messages-list">
          <div
            v-for="message in messages"
            :key="message.id"
            :class="['message', `message-${message.role}`]"
          >
            <div class="message-avatar">
              <div v-if="message.role === 'user'" class="avatar user-avatar">
                {{ user?.username?.charAt(0)?.toUpperCase() }}
              </div>
              <div v-else class="avatar ai-avatar">AI</div>
            </div>
            
            <div class="message-content">
              <div class="message-text">{{ message.content }}</div>
              <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
          </div>
          
          <!-- 加载中提示 -->
          <div v-if="sending" class="message message-assistant">
            <div class="message-avatar">
              <div class="avatar ai-avatar">AI</div>
            </div>
            <div class="message-content">
              <div class="message-text typing">
                <div class="loading"></div>
                正在思考...
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="input-container">
          <textarea
            v-model="inputMessage"
            class="message-input"
            placeholder="输入你的问题..."
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.enter.shift.exact="() => {}"
            :disabled="sending"
            rows="1"
            ref="messageInput"
          ></textarea>
          
          <div class="action-container">
            <div class="input-actions">
              <Select v-model="selectedModel" class="model-select">
                <Option value="deepseek-chat">DeepSeek Chat</Option>
                <Option value="deepseek-reasoner">DeepSeek Reasoner</Option>
              </Select>
              
              <Select v-model="selectedMode" class="mode-select">
                  <Option value="Ask">Ask</Option>
                  <Option value="Agent">Agent[⭐New⭐]</Option>
              </Select>
            </div>
            <div>
              <button
                class="btn btn-primary send-btn"
                @click="sendMessage"
                :disabled="!inputMessage.trim() || sending"
              >
                <div v-if="sending" class="loading"></div>
                {{ sending ? '发送中' : '发送' }}
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>





<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Select, Option } from 'view-ui-plus'





// @ 这里代表的就是src目录
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

// 响应式数据
const inputMessage = ref('')
const selectedModel = ref('deepseek-chat')

// 默认我们是ask模式而不是agent模式
const selectedMode = ref("Ask")

const messagesContainer = ref(null)
const messageInput = ref(null)

// 计算属性
const user = computed(() => authStore.user)
const sessions = computed(() => chatStore.sessions)
const currentSession = computed(() => chatStore.currentSession)
const messages = computed(() => chatStore.messages)
const sending = computed(() => chatStore.sending)

// 方法
const createNewChat = () => {
  chatStore.createNewSession()
  scrollToBottom()
}

const selectSession = async (session) => {
  try {
    await chatStore.selectSession(session)
    scrollToBottom()
  } catch (error) {
    console.error('选择会话失败:', error)
  }
}

const deleteSessionConfirm = async (sessionId) => {
  if (confirm('确定要删除这个对话吗？')) {
    try {
      await chatStore.deleteSession(sessionId)
    } catch (error) {
      console.error('删除会话失败:', error)
      alert('删除失败，请重试')
    }
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || sending.value) {
    return
  }

  const message = inputMessage.value.trim()
  inputMessage.value = ''
  
  // 调整输入框高度
  if (messageInput.value) {
    messageInput.value.style.height = 'auto'
  }

  try {
    await chatStore.sendMessage(message, selectedModel.value, selectedMode.value)
    scrollToBottom()
    if(selectedMode.value == "Agent"){
      // 展示ai写的代码
      router.push("/tmpcode")
    }

  } 
  catch (error) {
    console.error('发送消息失败:', error)
    alert('发送失败，请重试')
  }
}

const logout = () => {
  authStore.logout()
  router.push('/login')
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffTime = Math.abs(now - date)
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays === 1) {
    return '今天'
  } else if (diffDays === 2) {
    return '昨天'
  } else if (diffDays <= 7) {
    return `${diffDays}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

const formatTime = (dateString) => {
  return new Date(dateString).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 这个函数就是快速的滑倒底部，就是在有新消息后调用，这样用户能看到最新的消息 
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 自动调整输入框高度
const adjustTextareaHeight = () => {
  const textarea = messageInput.value
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
  }
}

// 监听输入变化
watch(inputMessage, () => {
  nextTick(adjustTextareaHeight)
})

// 监听消息变化，自动滚动到底部
watch(messages, () => {
  scrollToBottom()
}, { deep: true })

// 组件挂载时初始化
onMounted(async () => {
  try {
    await chatStore.initChat()
    scrollToBottom()
  } catch (error) {
    console.error('初始化聊天失败:', error)
  }
})
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background-color: #f5f5f5;
}

/* 侧边栏样式 */
.sidebar {
  width: 300px;
  background: white;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.new-chat-btn {
  padding: 8px 16px;
  font-size: 14px;
}

.sessions-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.session-item:hover {
  background-color: #f8f9fa;
}

.session-item.active {
  background-color: #e3f2fd;
  border-left: 3px solid #007bff;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-meta {
  font-size: 12px;
  color: #666;
}

.delete-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  color: #999;
  cursor: pointer;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  line-height: 1;
}

.delete-btn:hover {
  background-color: #f0f0f0;
  color: #dc3545;
}

.empty-sessions {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

/* 主聊天区域样式 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e0e0e0;
  background: white;
}

.chat-title h1 {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.chat-title .session-title {
  font-size: 14px;
  color: #666;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.username {
  font-weight: 500;
  color: #333;
}

.logout-btn {
  padding: 8px 16px;
  font-size: 14px;
}

/* 消息区域样式 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #fafafa;
}

.messages-list {
  max-width: 800px;
  margin: 0 auto;
}

.message {
  display: flex;
  margin-bottom: 24px;
  align-items: flex-start;
  gap: 12px;
}

.message-avatar {
  flex-shrink: 0;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.user-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.ai-avatar {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-text {
  background: white;
  padding: 16px 20px;
  border-radius: 18px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  line-height: 1.5;
  word-wrap: break-word;
}

.message-user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  margin-left: auto;
  max-width: 80%;
}

.message-assistant .message-text {
  background: white;
  max-width: 85%;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
  text-align: right;
}

.message-user .message-time {
  text-align: right;
}

.message-assistant .message-time {
  text-align: left;
}

.typing {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 输入区域样式 */
.input-area {
  padding: 20px 24px;
  background: white;
  border-top: 1px solid #e0e0e0;
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
}

.message-input {
  width: 100%;
  min-height: 44px;
  max-height: 120px;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 22px;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  outline: none;
  font-family: inherit;
  margin-bottom: 12px;
}

.message-input:focus {
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}



/* .action-container input-actions .model-select .mode-select 与模型选择和发送按钮有关*/
.action-container {
  display: flex;
  justify-content: space-between;
}
.input-actions {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 15px;
}

.model-select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  background: wheat;
}
.mode-select {
  padding: 10px;
  border-radius: 6px;
  border: solid #ddd;
  font-size: 14px;
  background-color: wheat;
}

.send-btn {
  padding: 10px 24px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-container {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    height: 200px;
    border-right: none;
    border-bottom: 1px solid #e0e0e0;
  }
  
  .chat-header {
    padding: 12px 16px;
  }
  
  .chat-title h1 {
    font-size: 18px;
  }
  
  .messages-container {
    padding: 16px;
  }
  
  .input-area {
    padding: 16px;
  }
  
  .input-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .send-btn {
    align-self: flex-end;
  }
}
</style>
