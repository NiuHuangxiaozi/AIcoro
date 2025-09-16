/**
 * 聊天状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed, nextTick } from 'vue'
import { chatAPI } from '@/api'
import { fetchEventSource } from '@microsoft/fetch-event-source'

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
  // 这列data是 session的list，在session的元信息里面是没有message，想要获得这个session的message还需要调用其他的接口
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
      // 这样只要我们在前端的组件上disable里面加上loading，就可以在加载的时候防止用户误触
      loading.value = true

      const data = await chatAPI.getSessionMessages(sessionId)
      messages.value = data
    
    } 
    catch (error) {
      console.error('获取会话消息失败:', error)
      throw error
    } 
    finally {
      loading.value = false
    }
  }


  // 创建AbortController用于取消请求
  let streamController = null;
  
  const fetchAIResponse = (content, model, mode, controller, response_session_id) => { 
    const apiUrl = 'http://localhost:8000/chat/sendstream'; // 替换为实际的 AI API 地址 
    const token = localStorage.getItem('access_token')

    fetchEventSource(apiUrl, { 
      method: 'POST', 
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }, 
      body: JSON.stringify({
        message: content,
        session_id: currentSessionId.value,
        mode: mode,
        model,
        
      }), 
      onopen: (response) => { 
        if (response.ok)  { 
          console.log('SSE  连接已建立'); 
        } else { 
          console.error('SSE  连接失败', response.status);  
        } 
      }, 
      signal: controller.signal,
      onmessage: (event) => { 
        // 先判断 event.data：如果是空字符串（'' 或 全空白），就关闭连接并返回
        const data = JSON.parse(event.data);
        console.log("receiving data is ",data.delta)

        if(data.delta === '##[BEGIN]##'){
          console.log('收到开始标记，接下来接受信息 SSE 连接,保存后端传来地session_id',data.session_id);
          response_session_id.value = data.session_id
        }
        else if(data.delta === '##[DONE]##'){
          console.log('收到结束标记，主动关闭 SSE 连接');
          controller.abort(); // 中止请求
          return;
        }
        else{
          messages.value[messages.value.length - 1].content += data.delta
        }
      }, 
      onclose: () => { 
        console.log('SSE  连接已关闭'); 
      }, 
      onerror: (error) => { 
        console.error('SSE  发生错误', error); 
      } 
    }); 
  }; 
  /**
   * 流式发送消息到后端并接收实时响应
   * 
   * 该函数实现了基于Server-Sent Events (SSE)的流式通信：
   * 1. 发送用户消息到后端流式API
   * 2. 实时接收并显示AI生成的文本块
   * 3. 处理会话管理和错误恢复
   * 4. 确保资源正确释放，避免内存泄漏
   * 
   * @param {string} content - 用户输入的消息内容
   * @param {string} model - 使用的LLM模型，默认为'deepseek-chat'
   * @param {string} mode - 对话模式，默认为'Ask'
   */
  const streamGetMessage = async (
    content,
    model = 'deepseek-chat',
    mode = 'Ask'
  ) => {

    const userMessage = {
      id: Date.now().toString(),
      content,
      role: 'user',
      timestamp: new Date().toISOString()
    }
    messages.value.push(userMessage)

    const aiMessage = {
      id: Date.now().toString(),
      content: '',
      role: 'assistant',
      timestamp: new Date().toISOString()
    }
    messages.value.push(aiMessage)



    const response_session_id = ref('')
    try{  
      // 创建一个 AbortController，可以用于在接收到空 data 时关闭连接（或外部手动关闭）
      const controller = new AbortController();
      const result = fetchAIResponse(content, model, mode, controller, response_session_id)
      // 更新当前会话ID
      if (!currentSession.value) {
        // 如果是新会话，重新获取会话列表
        await fetchSessions()
        // 设置当前会话为最新的会话
        const newSession = sessions.value.find(s => s.id === response_session_id.value)
        if (newSession) {
          currentSession.value = newSession
        }
      }
    }
    catch (error) {
      console.error('发送消息失败:', error)
      throw error
    }
    finally {
      sending.value = false
    }

  }

  /**
   * 流式传输完成后更新会话信息
   * @param {string} sessionId - 响应中的会话ID
   */
  const updateSessionAfterStreaming = async (sessionId) => {
    try {
      if (!currentSession.value && sessionId) {
        // 如果是新会话，重新获取会话列表
        await fetchSessions()
        
        // 设置当前会话为最新创建的会话
        const newSession = sessions.value.find(s => s.id === sessionId)
        if (newSession) {
          currentSession.value = newSession
          console.log('已切换到新会话:', newSession.title)
        }
      }
    } catch (error) {
      console.error('更新会话信息失败:', error)
      // 会话更新失败不应该影响用户体验，只记录错误
    }
  }

  /**
   * 取消当前的流式传输
   */
  const cancelStreaming = () => {
    if (streamController) {
      streamController.abort()
      streamController = null
      sending.value = false
      loading.value = false
      console.log('已取消流式传输')
    }
  }
  

// 非流式发送消息，响应比较慢
  const nonstreamingGetMessage = async (content,
                             model = 'deepseek-chat',
                             mode = 'Ask' ) => {
    try {
      
      // 正在发送过程
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
      // ======================================================================
      // (核心函数) 发送到后端，要求后端返回内容// 被axios自动转换为JSON字符串
      const response = await chatAPI.sendMessage({
        message: content,
        session_id: currentSessionId.value,
        mode: mode,
        model,
      })
      // ======================================================================


      console.log("response.message is ", response.message)
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



  // 选择会话，就是用户点击了左边的某一个会话，接下来的动作
  const selectSession = async (session) => {
    // 设置用户选择的session为当前的session
    currentSession.value = session
    // 从后端拉去这个session的信息
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
    // 状态
    sessions,
    currentSession,
    messages,
    loading,
    sending,
    currentSessionId,
    
    // 会话管理方法
    fetchSessions,
    fetchMessages,
    createNewSession,
    selectSession,
    deleteSession,
    initChat,
    
    // 消息发送方法
    nonstreamingGetMessage,           // 非流式发送（兼容旧版本）
    streamGetMessage,      // 流式发送（推荐使用）
    cancelStreaming,       // 取消流式传输
    
    // 辅助方法
    updateSessionAfterStreaming,
  }
})
