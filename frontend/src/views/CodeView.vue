<template>
  <div class="code-view-container">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <button class="btn btn-ghost back-btn" @click="goBack">
          ← 返回聊天
        </button>
        <div class="project-info">
          <span class="project-name">{{ currentProject || '代码项目' }}</span>
        </div>
      </div>
      <div class="toolbar-right">
        <button 
          class="btn btn-primary download-btn" 
          @click="downloadProject"
          :disabled="!currentProject || downloading"
        >
          <div v-if="downloading" class="loading"></div>
          {{ downloading ? '下载中...' : '下载项目' }}
        </button>
      </div>
    </div>

    <div class="main-content">
      <!-- 左侧文件树 -->
      <div class="file-explorer">
        <div class="explorer-header">
          <h3>资源管理器</h3>
        </div>
        
        <div class="project-selector" v-if="projects.length > 1">
          <select v-model="currentProject" @change="loadProjectTree" class="project-select">
            <option value="">选择项目</option>
            <option v-for="project in projects" :key="project" :value="project">
              {{ project }}
            </option>
          </select>
        </div>

        <div class="file-tree" v-if="fileTree.length > 0">
          <FileTreeNode
            v-for="node in fileTree"
            :key="node.path"
            :node="node"
            :level="0"
            @file-select="openFile"
          />
        </div>
        
        <div v-else-if="loading" class="loading-state">
          <div class="loading"></div>
          加载中...
        </div>
        
        <div v-else class="empty-state">
          <p>暂无项目文件</p>
        </div>
      </div>

      <!-- 右侧代码区域 -->
      <div class="code-area">
        <!-- 文件标签栏 -->
        <div class="tab-bar" v-if="openFiles.length > 0">
          <div
            v-for="file in openFiles"
            :key="file.path"
            :class="['tab', { active: activeFile?.path === file.path }]"
            @click="setActiveFile(file)"
          >
            <span class="tab-name">{{ file.name }}</span>
            <button class="tab-close" @click.stop="closeFile(file.path)">×</button>
          </div>
        </div>

        <!-- 代码编辑器区域 -->
        <div class="editor-container">
          <div v-if="activeFile" class="editor-wrapper">
            <div class="file-info">
              <span class="file-path">{{ activeFile.path }}</span>
              <span class="file-size">{{ formatFileSize(activeFile.size) }}</span>
            </div>
            <div ref="editorRef" class="code-editor"></div>
          </div>
          
          <div v-else class="welcome-screen">
            <div class="welcome-content">
              <h2>欢迎使用代码查看器</h2>
              <p>从左侧文件树中选择文件来查看代码</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch, onBeforeUnmount } from 'vue'
import { useRouter,useRoute } from 'vue-router'
import { EditorView, basicSetup } from 'codemirror'
import { EditorState } from '@codemirror/state'
import { python } from '@codemirror/lang-python'
import { javascript } from '@codemirror/lang-javascript'
import { json } from '@codemirror/lang-json'
import { markdown } from '@codemirror/lang-markdown'
import { oneDark } from '@codemirror/theme-one-dark'
import { codeAPI } from '@/api'
import FileTreeNode from '@/components/FileTreeNode.vue'



const router = useRouter()

const route = useRoute()

// 3. 从 route.query 中提取 rootPath 参数
// 注意：query 参数是字符串类型，如果需要其他类型（如数字），需要手动转换
const rootPath = route.query.rootPath


// 响应式数据
const projects = ref([])
const currentProject = ref('')
const fileTree = ref([])
const openFiles = ref([])
const activeFile = ref(null)
const loading = ref(false)
const downloading = ref(false)
const editorRef = ref(null)
let editorView = null

// 方法
const goBack = () => {
  router.push('/chat')
}


// 这里我们需要根据rootPath来进行项目文件夹的加载
const loadProjects = async () => {
  try {
    // const data = await codeAPI.getProjects()
    projects.value = [rootPath]
    
    // 如果只有一个项目，自动选择
    if (projects.value.length === 1) {
      currentProject.value = projects.value[0]
      await loadProjectTree()
    }
  } catch (error) {
    console.error('加载项目列表失败:', error)
    alert('加载项目列表失败')
  }
}

const loadProjectTree = async () => {
  if (!currentProject.value) return
  
  loading.value = true
  try {
    const data = await codeAPI.getProjectTree(currentProject.value)
    fileTree.value = data
  } catch (error) {
    console.error('加载文件树失败:', error)
    alert('加载文件树失败')
  } finally {
    loading.value = false
  }
}

const openFile = async (filePath) => {
  try {
    // 检查文件是否已经打开
    const existingFile = openFiles.value.find(f => f.path === filePath)
    if (existingFile) {
      setActiveFile(existingFile)
      return
    }

    // 获取文件内容
    const fileData = await codeAPI.getFileContent(currentProject.value, filePath)
    const fileName = filePath.split('/').pop()
    
    const file = {
      name: fileName,
      path: filePath,
      content: fileData.content,
      size: fileData.size
    }
    
    openFiles.value.push(file)
    setActiveFile(file)
    
  } catch (error) {
    console.error('打开文件失败:', error)
    alert('打开文件失败')
  }
}

const closeFile = (filePath) => {
  const index = openFiles.value.findIndex(f => f.path === filePath)
  if (index === -1) return
  
  const closingFile = openFiles.value[index]
  openFiles.value.splice(index, 1)
  
  // 如果关闭的是当前活动文件，切换到其他文件
  if (activeFile.value?.path === filePath) {
    if (openFiles.value.length > 0) {
      // 优先选择右边的文件，如果没有则选择左边的
      const newActiveIndex = index < openFiles.value.length ? index : index - 1
      setActiveFile(openFiles.value[newActiveIndex])
    } else {
      activeFile.value = null
      destroyEditor()
    }
  }
}

const setActiveFile = (file) => {
  activeFile.value = file
  nextTick(() => {
    createEditor(file.content, file.name)
  })
}

const getLanguageExtension = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'py':
      return python()
    case 'js':
    case 'ts':
      return javascript()
    case 'json':
      return json()
    case 'md':
      return markdown()
    default:
      return []
  }
}

const createEditor = (content, filename) => {
  if (!editorRef.value) return
  
  destroyEditor()
  
  const extensions = [
    basicSetup,
    oneDark,
    getLanguageExtension(filename),
    EditorView.editable.of(false), // 只读模式
    EditorView.theme({
      '&': {
        height: '100%',
        fontSize: '14px'
      },
      '.cm-content': {
        padding: '16px'
      },
      '.cm-focused': {
        outline: 'none'
      }
    })
  ]
  
  const state = EditorState.create({
    doc: content,
    extensions
  })
  
  editorView = new EditorView({
    state,
    parent: editorRef.value
  })
}

const destroyEditor = () => {
  if (editorView) {
    editorView.destroy()
    editorView = null
  }
}

const downloadProject = async () => {
  if (!currentProject.value) return
  
  downloading.value = true
  try {
    const blob = await codeAPI.downloadProject(currentProject.value)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${currentProject.value}.tar.gz`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
  } catch (error) {
    console.error('下载项目失败:', error)
    alert('下载项目失败')
  } finally {
    downloading.value = false
  }
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 监听项目变化
watch(currentProject, (newProject) => {
  if (newProject) {
    loadProjectTree()
    // 清空已打开的文件
    openFiles.value = []
    activeFile.value = null
    destroyEditor()
  }
})

// 组件挂载时初始化
onMounted(() => {
  loadProjects()
})

// 组件卸载时清理编辑器，关闭代码这个页面组件应该就卸载了
onBeforeUnmount(() => {
  destroyEditor()
})
</script>

<style scoped>
.code-view-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #1e1e1e;
  color: #d4d4d4;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background-color: #2d2d30;
  border-bottom: 1px solid #3e3e42;
  height: 48px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  padding: 6px 12px;
  font-size: 14px;
  color: #cccccc;
  background: none;
  border: 1px solid #464647;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  background-color: #404040;
  border-color: #6c6c6c;
}

.project-info {
  display: flex;
  align-items: center;
}

.project-name {
  font-weight: 500;
  color: #ffffff;
}

.download-btn {
  padding: 6px 16px;
  font-size: 14px;
  background-color: #0e639c;
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.download-btn:hover:not(:disabled) {
  background-color: #1177bb;
}

.download-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.file-explorer {
  width: 300px;
  background-color: #252526;
  border-right: 1px solid #3e3e42;
  display: flex;
  flex-direction: column;
}

.explorer-header {
  padding: 12px 16px;
  border-bottom: 1px solid #3e3e42;
  background-color: #2d2d30;
}

.explorer-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #cccccc;
  text-transform: uppercase;
}

.project-selector {
  padding: 12px 16px;
  border-bottom: 1px solid #3e3e42;
}

.project-select {
  width: 100%;
  padding: 8px 12px;
  background-color: #3c3c3c;
  border: 1px solid #464647;
  border-radius: 4px;
  color: #d4d4d4;
  font-size: 14px;
}

.file-tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.loading-state, .empty-state {
  padding: 40px 16px;
  text-align: center;
  color: #858585;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.code-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #1e1e1e;
}

.tab-bar {
  display: flex;
  background-color: #2d2d30;
  border-bottom: 1px solid #3e3e42;
  overflow-x: auto;
}

.tab {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background-color: #2d2d30;
  border-right: 1px solid #3e3e42;
  cursor: pointer;
  transition: background-color 0.2s;
  min-width: 0;
  white-space: nowrap;
}

.tab:hover {
  background-color: #37373d;
}

.tab.active {
  background-color: #1e1e1e;
  border-bottom: 2px solid #007acc;
}

.tab-name {
  font-size: 14px;
  color: #cccccc;
  margin-right: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tab-close {
  background: none;
  border: none;
  color: #858585;
  cursor: pointer;
  font-size: 16px;
  padding: 0;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 3px;
}

.tab-close:hover {
  background-color: #464647;
  color: #cccccc;
}

.editor-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.editor-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.file-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background-color: #2d2d30;
  border-bottom: 1px solid #3e3e42;
  font-size: 12px;
}

.file-path {
  color: #cccccc;
}

.file-size {
  color: #858585;
}

.code-editor {
  flex: 1;
  overflow: hidden;
}

.welcome-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.welcome-content {
  text-align: center;
  color: #858585;
}

.welcome-content h2 {
  margin-bottom: 16px;
  color: #cccccc;
}

.loading {
  width: 16px;
  height: 16px;
  border: 2px solid #3e3e42;
  border-top: 2px solid #007acc;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .file-explorer {
    width: 250px;
  }
  
  .toolbar {
    padding: 8px 12px;
  }
  
  .toolbar-left {
    gap: 12px;
  }
}
</style>
