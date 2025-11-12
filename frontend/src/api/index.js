/**
 * API接口配置
 */
import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000',
  timeout: import.meta.env.VITE_BACKEND_EXPIRED_TIME || 60000 * 10,
  headers: {
    'Content-Type': 'application/json'
  }
})



// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // localStorage是现代浏览器都实现的一个小型数据库，全局可以访问
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 这里直接把json数据结构返回，这样前端直接分析json结构数据
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token过期或无效，清除本地存储并跳转到登录页
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_info')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 认证API
export const authAPI = {
  // 登录
  login: (credentials) => api.post('/auth/login', credentials),
  
  // 注册
  register: (userData) => api.post('/auth/register', userData),
  
  // 获取当前用户信息
  getCurrentUser: () => api.get('/auth/me')
}

// 聊天API
export const chatAPI = {
  // 发送消息
  sendMessage: (data) => api.post('/chat/send', data),
  
  // 获取会话列表
  getSessions: () => api.get('/chat/sessions'),
  
  // 获取会话消息
  getSessionMessages: (sessionId) => api.get(`/chat/sessions/${sessionId}/messages`),
  
  // 删除会话
  deleteSession: (sessionId) => api.delete(`/chat/sessions/${sessionId}`),

  deleteAllSessions: () => api.delete('/chat/sessions')
}

// 代码管理API
export const codeAPI = {
  // 获取项目列表
  getProjects: () => api.get('/code/projects'),
  
  // 获取项目文件树
  getProjectTree: (projectName) => api.get(`/code/projects/tree`,{
    params: { project_name:projectName}
  }),
  
  // 获取文件内容
  getFileContent: (projectName, filePath) => api.get(`/code/projects/files`, {
    params: { project_name: projectName,
            file_path:filePath }
  }),
  
  // 下载项目
  downloadProject: (projectName) => api.get(`/code/projects/download`, {
    params: { project_name: projectName},
    responseType: 'blob'
  })
}

export default api
