<template>
  <div class="tree-node">
    <div 
      :class="['node-content', { 'is-file': !node.is_directory }]"
      :style="{ paddingLeft: `${level * 16 + 8}px` }"
      @click="handleClick"
    >
      <span v-if="node.is_directory" class="folder-icon">
        {{ expanded ? '📂' : '📁' }}
      </span>
      <span v-else class="file-icon">
        {{ getFileIcon(node.name) }}
      </span>
      <span class="node-name">{{ node.name }}</span>
      <span v-if="!node.is_directory && node.size" class="file-size">
        {{ formatFileSize(node.size) }}
      </span>
    </div>
    
    <!-- 子节点 -->
    <div v-if="node.is_directory && expanded && node.children" class="children">
      <FileTreeNode
        v-for="child in node.children"
        :key="child.path"
        :node="child"
        :level="level + 1"
        @file-select="$emit('file-select', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  level: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['file-select'])

const expanded = ref(false)

const handleClick = () => {
  if (props.node.is_directory) {
    expanded.value = !expanded.value
  } else {
    emit('file-select', props.node.path)
  }
}

const getFileIcon = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  const iconMap = {
    'py': '🐍',
    'js': '📜',
    'ts': '📘',
    'vue': '💚',
    'html': '🌐',
    'css': '🎨',
    'scss': '🎨',
    'json': '📋',
    'md': '📝',
    'txt': '📄',
    'yml': '⚙️',
    'yaml': '⚙️',
    'xml': '📰',
    'sql': '🗃️',
    'sh': '⚡',
    'bat': '⚡',
    'dockerfile': '🐳',
    'gitignore': '🙈',
    'readme': '📖'
  }
  
  return iconMap[ext] || '📄'
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}
</script>

<style scoped>
.tree-node {
  user-select: none;
}

.node-content {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 14px;
  line-height: 1.4;
}

.node-content:hover {
  background-color: #2a2d2e;
}

.node-content.is-file:hover {
  background-color: #094771;
}

.folder-icon, .file-icon {
  margin-right: 6px;
  font-size: 12px;
  width: 16px;
  display: inline-block;
  text-align: center;
}

.node-name {
  flex: 1;
  color: #cccccc;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 11px;
  color: #858585;
  margin-left: 8px;
}

.children {
  /* 子节点容器样式 */
}
</style>
