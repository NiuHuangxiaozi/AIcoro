/**
 * 聊天状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { chatAPI } from '@/api'

export const useChatStore = defineStore('chat', () => {
  // 状态
  const sessions = ref([])
  const currentSession = ref(null)
  const messages = ref([])
  const loading = ref(false)
  const sending = ref(false)

  // 计算属性
  const currentSessionId = computed(() => currentSession.value?.id || null)

  // 获取会话列表
  const fetchSessions = async () => {
    try {
      loading.value = true
      const data = await chatAPI.getSessions()
      sessions.value = data
    } catch (error) {
      console.error('获取会话列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取会话消息
  const fetchMessages = async (sessionId) => {
    try {
      loading.value = true
      const data = await chatAPI.getSessionMessages(sessionId)
      messages.value = data
    } catch (error) {
      console.error('获取会话消息失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 发送消息
  const sendMessage = async (content,
                             model = 'deepseek-chat',
                             mode = 'Ask' ) => {
    try {
      
      sending.value = true
      
      // 添加用户消息到界面
      const userMessage = {
        id: Date.now().toString(),
        content,
        role: 'user',
        timestamp: new Date().toISOString()
      }
      messages.value.push(userMessage)
      console.log(messages)


      // 发送到后端// 被axios自动转换为JSON字符串
      const response = await chatAPI.sendMessage({
        message: content,
        session_id: currentSessionId.value,
        mode: mode,
        model,
        
      })


      // 添加AI回复到界面
      messages.value.push(response.message)

      // 更新当前会话ID
      if (!currentSession.value) {
        // 如果是新会话，重新获取会话列表
        await fetchSessions()
        // 设置当前会话为最新的会话
        const newSession = sessions.value.find(s => s.id === response.session_id)
        if (newSession) {
          currentSession.value = newSession
        }
      }

      return response
    } 
    catch (error) {
      console.error('发送消息失败:', error)
      throw error
    } finally {
      sending.value = false
    }
  }

  // 创建新会话
  const createNewSession = () => {
    currentSession.value = null
    messages.value = [
      {
        id: 'welcome',
        content: 'Hi, 我能有什么能帮你的',
        role: 'assistant',
        timestamp: new Date().toISOString()
      }
    ]
  }

  // 选择会话
  const selectSession = async (session) => {
    currentSession.value = session
    await fetchMessages(session.id)
  }

  // 删除会话
  const deleteSession = async (sessionId) => {
    try {
      await chatAPI.deleteSession(sessionId)
      
      // 从本地列表中移除，filter表示的是过滤出的意思
      sessions.value = sessions.value.filter(s => s.id !== sessionId)
      
      // 如果删除的是当前会话，创建新会话
      if (currentSession.value?.id === sessionId) {
        createNewSession()
      }
    } catch (error) {
      console.error('删除会话失败:', error)
      throw error
    }
  }

  // 初始化聊天数据
  const initChat = async () => {
    await fetchSessions()
    createNewSession()
  }

  return {
    sessions,
    currentSession,
    messages,
    loading,
    sending,
    currentSessionId,
    fetchSessions,
    fetchMessages,
    sendMessage,
    createNewSession,
    selectSession,
    deleteSession,
    initChat
  }
})
