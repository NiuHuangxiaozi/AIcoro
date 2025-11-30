<template>
  <div class="ppt-generator">
    <div class="container">
      <!-- 左边历史记录栏 -->
      <div class="left-panel">
        <div class="history-header">
          <h3>生成历史记录</h3>
        </div>
        <div class="history-list">
          <div v-if="pptHistory.length === 0" class="no-history">
            <p>暂无生成记录</p>
          </div>
          <div v-else v-for="item in pptHistory" :key="item.id" class="history-item">
            <div class="history-title">{{ item.title }}</div>
            <div class="history-date">{{ item.createdAt }}</div>
            <div class="history-actions">
              <button class="btn-download" @click="downloadPPT(item)">下载</button>
              <button class="btn-preview" @click="previewPPT(item)">预览</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右边生成界面 -->
      <div class="right-panel">
        <div class="generator-header">
          <h2>快来生成属于自己的PPT</h2>
        </div>

        <div class="output-section">
          <label class="output-label">模型推理内容</label>
          <div class="output-box">
            <div v-if="isGenerating" class="generating-indicator">
              <div class="spinner"></div>
              <span>正在生成中...</span>
            </div>
            <div v-else-if="inferenceOutput" class="inference-content">
              {{ inferenceOutput }}
            </div>
            <div v-else class="placeholder">
              生成的内容将在这里显示
            </div>
          </div>
        </div>

        <div class="input-section">
          <label for="ppt-content" class="input-label">PPT内容主题</label>
          <textarea
            id="ppt-content"
            v-model="pptContent"
            class="content-input"
            placeholder="请输入您想要生成的PPT主题内容..."
            rows="6"
          ></textarea>
        </div>

        <div class="control-section">
          <div class="control-row">


            <button class="btn-upload-template" @click="triggerFileInput('pptx')">
              <span class="btn-icon">📄</span>
              选择PPT模板
            </button>
              <!-- 隐藏的文件输入框（关键！） -->
            <input
              ref="pptxInputRef"
              type="file"
              accept=".pptx"
              @change="handleFileUpload($event, 'pptx')"
              style="display: none"
            />
            
            <button class="btn-upload-pdf" @click="triggerFileInput('pdf')">
              <span class="btn-icon">📄</span>
              选择PDF模板
            </button>
            <input
              ref="pdfInputRef"
              type="file"
              accept=".pdf"
              @change="handleFileUpload($event, 'pdf')"
              style="display: none"
            />

            <div class="pages-selector">
              <label for="page-count" class="selector-label">生成页数：</label>
              <select id="page-count" v-model="selectedPages" class="page-select">
                <option value="5">5页</option>
                <option value="10">10页</option>
                <option value="15">15页</option>
                <option value="20">20页</option>
              </select>
            </div>
          </div>
        </div>

        <div class="generate-section">
          <button
            class="btn-generate"
            :disabled="!pptContent.trim() || isGenerating"
            @click="generatePPT"
          >
            {{ isGenerating ? '生成中...' : '开始生成' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
// 声明两个“盒子”，用来装文件
const pdfFile = ref(null)    // 相当于 Vue 2 的 this.pdfFile
const pptxFile = ref(null)   // 相当于 this.pptxFile
// 2. 获取隐藏 input 的引用
const pptxInputRef = ref(null)
const pdfInputRef = ref(null)

const pptHistory = ref([])
const pptContent = ref('')
const selectedPages = ref('10')
const isGenerating = ref(false)
const inferenceOutput = ref('')



// 3. 点击按钮时，触发隐藏 input 的 click 事件
function triggerFileInput(type) {
  if (type === 'pptx' && pptxInputRef.value) {
    pptxInputRef.value.click() // 👈 模拟点击pptx输入框！
  }
  if (type === 'pdf' && pdfInputRef.value) {
    pdfInputRef.value.click() // 👈 模拟点击pdf输入框！
  }
}


const generatePPT = async () => {
  if (!pptContent.value.trim()) return

  isGenerating.value = true
  inferenceOutput.value = ''

  try {
    // 模拟生成过程
    await new Promise(resolve => setTimeout(resolve, 2000))

    inferenceOutput.value = `正在基于主题"${pptContent.value}"生成${selectedPages.value}页的PPT...\n\n分析主题内容中...\n整理结构布局...\n生成演示文稿...`

    // 模拟完成后添加到历史记录
    const newPPT = {
      id: Date.now(),
      title: pptContent.value.substring(0, 20) + '...',
      createdAt: new Date().toLocaleString(),
    }
    pptHistory.value.unshift(newPPT)

  } catch (error) {
    console.error('生成失败:', error)
  } finally {
    isGenerating.value = false
  }
}

const downloadPPT = (item) => {
  // TODO: 实现下载逻辑
  alert(`下载PPT: ${item.title}`)
}

const previewPPT = (item) => {
  // TODO: 实现预览逻辑
  alert(`预览PPT: ${item.title}`)
}

// 模拟历史记录数据
const mockHistory = [
  {
    id: 1,
    title: '产品发布会PPT',
    createdAt: '2024-01-15 14:30',
  },
  {
    id: 2,
    title: '技术分享演示',
    createdAt: '2024-01-14 09:15',
  },
  {
    id: 3,
    title: '市场分析报告',
    createdAt: '2024-01-13 16:45',
  }
]

// 方法
const selectTemplate = () => {
  // TODO: 实现文件选择逻辑
  alert('选择PPT模板功能')
}

const selectPDF = () => {
  // TODO: 实现PDF文件选择逻辑
  alert('选择PDF文件功能')
}

// 上载pdf和ppt文件
const handleFileUpload = (event, fileType) => {
  console.log("file uploaded :", fileType)
  const file = event.target.files[0]
  if (fileType === 'pptx') {
    pptxFile.value = file
  } else if (fileType === 'pdf') {
    pdfFile.value = file
  }
}

// 组件挂载时加载历史记录
onMounted(() => {
  pptHistory.value = mockHistory
})
</script>

<style scoped>
.ppt-generator {
  display: flex;
  flex-direction: row;
  justify-content: center;
  height: 100%;
  width: 100%;
  padding: 2px 2px;
  background-color: #fff;
  color: #4a4a4a;
  box-sizing: border-box;
}

.container {
  margin: 0 2px;
  display: flex;
  gap: 10px;
  height: 100%;
  width: 100%;
}

/* 左边历史记录面板 */
.left-panel {
  flex: 1;
  background: #ffffff;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #e8e8e8;
}

.history-header h3 {
  margin: 0 0 20px 0;
  color: #2c3e50;
  font-size: 1.5rem;
  font-weight: 600;
}

.history-list {
  height: calc(100% - 80px);
  overflow-y: auto;
}

.history-item {
  padding: 15px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  margin-bottom: 12px;
  background: #fafafa;
  transition: all 0.2s ease;
}

.history-item:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
  transform: translateY(-1px);
  border-color: #d0d0d0;
}

.history-title {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 5px;
}

.history-date {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin-bottom: 10px;
}

.history-actions {
  display: flex;
  gap: 8px;
}

.btn-download, .btn-preview {
  padding: 6px 12px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #ffffff;
}

.btn-download {
  color: #27ae60;
  border-color: #27ae60;
}

.btn-download:hover {
  background: #27ae60;
  color: white;
  transform: translateY(-1px);
}

.btn-preview {
  color: #3498db;
  border-color: #3498db;
}

.btn-preview:hover {
  background: #3498db;
  color: white;
  transform: translateY(-1px);
}

.no-history {
  text-align: center;
  color: #7f8c8d;
  padding: 40px 20px;
}

/* 右边生成界面 */
.right-panel {
  flex: 2;
  background: #ffffff;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.generator-header h2 {
  margin: 0 0 30px 0;
  color: #2c3e50;
  font-size: 2rem;
  font-weight: 700;
  text-align: center;
}

.output-section {
  margin-bottom: 25px;
}

.output-label {
  display: block;
  margin-bottom: 10px;
  font-weight: 600;
  color: #2c3e50;
  font-size: 1.1rem;
}

.output-box {
  height: 150px;
  width: 100%;
  border: 2px solid #e1e8ed;
  border-radius: 10px;
  padding: 15px;
  background: #fafbfc;
  overflow-y: auto;
  transition: border-color 0.3s ease;
}

.output-box:focus-within {
  border-color: #667eea;
}

.generating-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #667eea;
  font-weight: 500;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.inference-content {
  line-height: 1.6;
  color: #2c3e50;
}

.placeholder {
  color: #95a5a6;
  font-style: italic;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.input-section {
  margin-bottom: 25px;
}

.input-label {
  display: block;
  margin-bottom: 10px;
  font-weight: 600;
  color: #2c3e50;
  font-size: 1.1rem;
}

.content-input {
  width: 100%;
  padding: 15px;
  border: 2px solid #e1e8ed;
  border-radius: 10px;
  font-size: 1rem;
  line-height: 1.5;
  resize: vertical;
  transition: border-color 0.3s ease;
  font-family: inherit;
}

.content-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.control-section {
  margin-bottom: 30px;
}

.control-row {
  display: flex;
  gap: 15px;
  align-items: center;
  flex-wrap: wrap;
}

.btn-upload-template, .btn-upload-pdf {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: 2px solid #667eea;
  background: white;
  color: #667eea;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-upload-template:hover, .btn-upload-pdf:hover {
  background: #667eea;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-icon {
  font-size: 1.2rem;
}

.pages-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selector-label {
  font-weight: 500;
  color: #2c3e50;
  white-space: nowrap;
}

.page-select {
  padding: 12px 15px;
  border: 2px solid #e1e8ed;
  border-radius: 8px;
  background: white;
  font-size: 1rem;
  cursor: pointer;
  transition: border-color 0.3s ease;
}

.page-select:focus {
  outline: none;
  border-color: #667eea;
}

.generate-section {
  display: flex;
  justify-content: center;
}

.btn-generate {
  padding: 15px 40px;
  background: linear-gradient(45deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.btn-generate:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.btn-generate:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .container {
    flex-direction: column;
    height: auto;
  }

  .left-panel, .right-panel {
    flex: none;
  }

  .control-row {
    flex-direction: column;
    align-items: stretch;
  }

  .pages-selector {
    justify-content: center;
  }

  .generator-header h2 {
    font-size: 1.5rem;
  }
}
</style>