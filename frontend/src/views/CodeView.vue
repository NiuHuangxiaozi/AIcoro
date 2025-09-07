<template>
  <div v-if="visible" class="code-platform">
    <!-- Header with Save and Close Button -->
    <div class="header">
      <h2>代码平台</h2>
      <div class="header-actions">
        <button @click="downloadProject" class="save-btn">保存项目</button>
        <button @click="closePlatform" class="close-btn">❌</button>
      </div>
    </div>

    <div class="workspace">
      <!-- File Explorer -->
      <div class="sidebar">
        <ul>
          <FileNode
            v-for="(node, index) in projectStructure"
            :key="index"
            :node="node"
            @open-file="openFile"
          />
        </ul>
      </div>

      <!-- Editor Area -->
      <div class="editor-area">
        <!-- Open Tabs -->
        <div class="tabs">
          <div
            v-for="(file, index) in openFiles"
            :key="file.path"
            class="tab"
            :class="{ active: activeFile && activeFile.path === file.path }"
            @click="setActiveFile(file)"
          >
            {{ file.name }}
            <span class="close" @click.stop="closeFile(file)">❌</span>
          </div>
        </div>

        <!-- CodeMirror Editor -->
        <div v-if="activeFile" class="editor">
          <codemirror
            v-model="activeFile.content"
            :extensions="extensions"
            :style="{ height: '100%', width: '100%' }"
          />
        </div>
        <div v-else class="no-file">请选择文件</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { Codemirror } from 'vue-codemirror'
import { javascript } from '@codemirror/lang-javascript'
import { oneDark } from '@codemirror/theme-one-dark'
import FileNode from './FileNode.vue'
import JSZip from 'jszip'
import { saveAs } from 'file-saver'
import { useRouter } from 'vue-router'


const router = useRouter()

const visible = ref(true)

// 模拟项目结构
const projectStructure = reactive([
  {
    type: 'folder',
    name: 'src',
    children: [
      { type: 'file', name: 'main.js', path: 'src/main.js', content: 'console.log("Hello World")' },
      { type: 'file', name: 'App.vue', path: 'src/App.vue', content: '<template><h1>Hello Vue</h1></template>' },
    ],
  },
  {
    type: 'file',
    name: 'package.json',
    path: 'package.json',
    content: '{\n  "name": "demo-project"\n}',
  },
])

const openFiles = ref([])
const activeFile = ref(null)

const extensions = [javascript(), oneDark]

function openFile(file) {
  if (!openFiles.value.find(f => f.path === file.path)) {
    openFiles.value.push(file)
  }
  activeFile.value = file
}

function closeFile(file) {
  openFiles.value = openFiles.value.filter(f => f.path !== file.path)
  if (activeFile.value && activeFile.value.path === file.path) {
    activeFile.value = openFiles.value.length ? openFiles.value[0] : null
  }
}

function setActiveFile(file) {
  activeFile.value = file
}

// 保存整个项目为 zip
async function downloadProject() {
  const zip = new JSZip()

  function addToZip(node, path = '') {
    if (node.type === 'file') {
      zip.file(path + node.name, node.content)
    } else if (node.type === 'folder') {
      const folder = zip.folder(path + node.name)
      node.children.forEach(child => addToZip(child, path + node.name + '/'))
    }
  }

  projectStructure.forEach(node => addToZip(node))

  const content = await zip.generateAsync({ type: 'blob' })
  saveAs(content, 'project.zip')
}

// 关闭平台，返回 /chat
function closePlatform() {
  visible.value = false
  router.push('/chat')
}
</script>

<style scoped>
.code-platform {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: Arial, sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #282c34;
  color: #fff;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.save-btn {
  background: #61dafb;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
}

.close-btn {
  background: #e06c75;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  color: white;
  font-weight: bold;
}

.workspace {
  display: flex;
  flex: 1;
}

.sidebar {
  width: 220px;
  background: #f4f4f4;
  border-right: 1px solid #ccc;
  overflow-y: auto;
  padding: 10px;
}

.editor-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.tabs {
  display: flex;
  background: #ddd;
  border-bottom: 1px solid #bbb;
}

.tab {
  padding: 6px 12px;
  border-right: 1px solid #bbb;
  cursor: pointer;
}

.tab.active {
  background: #fff;
  font-weight: bold;
}

.tab .close {
  margin-left: 6px;
  cursor: pointer;
}

.editor {
  flex: 1;
}

.no-file {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
}
</style>
