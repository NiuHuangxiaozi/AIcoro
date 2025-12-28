<template>
  <div class="ppt-generator">
    <div class="container">
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
        
        <progress :value="progress" max="100" class="progress-bar"></progress>

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
              <span v-if="pptxFile" class="uploaded-symbol">✔️</span>
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
              <span v-if="pdfFile" class="uploaded-symbol">✔️</span>
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
                <option value="3">3页</option>
                <option value="6">6页</option>
                <option value="9">9页</option>
                <option value="12">12页</option>
              </select>
            </div>


            <button
              v-if="downloadLink"
              class="btn-download-pptx"
              @click="downloadPPTX"
            >
              <span class="btn-icon">📥</span>
              下载PPTX
            </button>

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
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { usePptStore } from '@/stores/ppt'
const pptStore = usePptStore()
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

// 每一次生成ppt都是一次任务
const taskId = ref('')
const downloadLink = ref(null)
const filename = ref('')


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

  if (!pdfFile.value) {
    alert('请选择PPT模板和PDF模板')
    return
  }
  if (!pptContent.value.trim()) return

  isGenerating.value = true
  inferenceOutput.value = ''

  try {

      taskId.value = await pptStore.PPTGen(pptxFile.value, pdfFile.value, pptContent.value, selectedPages.value)
      startGeneration(taskId.value)
      console.log("ppt is ok", taskId)
  } catch (error) {
    console.error('生成失败:', error)
  } finally {
    isGenerating.value = false
  }
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




// 在ppt生成的过程中显示进度并最终显示能够下载。
const progress = ref(0)
const statusMessage = ref('')
// 这个是一个全双工的链接，然后在这个链接上进行通信
const socket = ref(null)

const startGeneration = async (taskId) => {
      console.log("Connecting to websocket", `/pptgen/wsapi/${taskId}`)
      const socket = new WebSocket(`ws://localhost:8001/pptgen/wsapi/${taskId}`)
      console.log("socket", socket)
      socket.onmessage = (event) => {
        console.log("Socket Received message:", event.data)
        const data = JSON.parse(event.data)
        progress.value = data.progress
        statusMessage.value = data.status

        inferenceOutput.value = data.status
        if (data.progress >= 100) {
          console.log("progress is 100, close socket")
          socket.close()
          fetchDownloadLink()
        }
    }
    socket.onerror = (error) => {
      console.error("WebSocket error:", error)
      socket.close()
    }
  }

const downloadPPTX = () => {
  if (!downloadLink.value) 
  {
    alert('pptx还未生成完毕，请稍后再试')
    return
  }
  const link = document.createElement('a');
  link.href = downloadLink.value;
  link.download = filename.value;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const fetchDownloadLink = async () => {
  try {
        const downloadResponse = await pptStore.getDownloadLink(taskId.value)
        console.log("downloadResponse", downloadResponse)
        downloadLink.value = URL.createObjectURL(downloadResponse) // 将blob转换为url
        filename.value = "ppagent_" + taskId.value.replace('/', '_') + '.pptx'
  } catch (error) {
    console.error("Download error:", error)
    statusMessage.value += '\nFailed to continue the task.'
  }
}

// 组件挂载时加载历史记录
onMounted(() => {
  // pptHistory.value = mockHistory
  
})
onBeforeUnmount(() => {
    socket.close()
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
  justify-content: center;
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

.uploaded-symbol {
  position: absolute;
  right: 5px;
  top: 50%;
  transform: translateY(-50%);
  color: green;
  font-size: 12px;
}

.progress-bar {
  width: 100%;
  height: 20px;
  margin-bottom: 10px;
  appearance: none;
  background-color: #f3f3f3;
}


/* 下载按钮的样式 */
.btn-download-pptx {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background-color: #4CAF50; /* 绿色，表示成功/完成 */
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
}

.btn-download-pptx:hover {
  background-color: #45a049;
}

.btn-download-pptx:active {
  transform: scale(0.98);
}

.btn-icon {
  font-size: 18px;
}

</style>