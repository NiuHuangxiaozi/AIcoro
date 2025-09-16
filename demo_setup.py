#!/usr/bin/env python3
"""
演示设置脚本
创建更多测试项目来展示代码查看器功能
"""

import os
import json
from pathlib import Path

# 代码生成根目录
CODE_ROOT = Path(__file__).parent / "tmp_code_generation"

def create_vue_project():
    """创建一个Vue项目示例"""
    project_path = CODE_ROOT / "vue_todo_app"
    project_path.mkdir(exist_ok=True)
    
    # 创建package.json
    package_json = {
        "name": "vue-todo-app",
        "version": "1.0.0",
        "description": "一个简单的Vue Todo应用",
        "main": "src/main.js",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview"
        },
        "dependencies": {
            "vue": "^3.3.0",
            "vue-router": "^4.2.0"
        },
        "devDependencies": {
            "@vitejs/plugin-vue": "^4.2.0",
            "vite": "^4.3.0"
        }
    }
    
    with open(project_path / "package.json", "w", encoding="utf-8") as f:
        json.dump(package_json, f, indent=2, ensure_ascii=False)
    
    # 创建src目录
    src_path = project_path / "src"
    src_path.mkdir(exist_ok=True)
    
    # 创建main.js
    main_js = '''import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import TodoList from './components/TodoList.vue'
import About from './components/About.vue'

const routes = [
  { path: '/', component: TodoList },
  { path: '/about', component: About }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)
app.use(router)
app.mount('#app')
'''
    
    with open(src_path / "main.js", "w", encoding="utf-8") as f:
        f.write(main_js)
    
    # 创建App.vue
    app_vue = '''<template>
  <div id="app">
    <nav class="navbar">
      <h1>Vue Todo App</h1>
      <div class="nav-links">
        <router-link to="/">首页</router-link>
        <router-link to="/about">关于</router-link>
      </div>
    </nav>
    
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
// Vue 3 Composition API
</script>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background-color: #2c3e50;
  color: white;
}

.nav-links {
  display: flex;
  gap: 1rem;
}

.nav-links a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  background-color: #34495e;
}

.main-content {
  padding: 2rem;
  max-width: 800px;
  margin: 0 auto;
}
</style>
'''
    
    with open(src_path / "App.vue", "w", encoding="utf-8") as f:
        f.write(app_vue)
    
    # 创建components目录
    components_path = src_path / "components"
    components_path.mkdir(exist_ok=True)
    
    # 创建TodoList.vue
    todo_list_vue = '''<template>
  <div class="todo-container">
    <h2>我的待办事项</h2>
    
    <div class="add-todo">
      <input 
        v-model="newTodo" 
        @keyup.enter="addTodo"
        placeholder="添加新的待办事项..."
        class="todo-input"
      />
      <button @click="addTodo" class="add-btn">添加</button>
    </div>
    
    <div class="todo-list">
      <div 
        v-for="todo in todos" 
        :key="todo.id"
        :class="['todo-item', { completed: todo.completed }]"
      >
        <input 
          type="checkbox" 
          v-model="todo.completed"
          class="todo-checkbox"
        />
        <span class="todo-text">{{ todo.text }}</span>
        <button @click="deleteTodo(todo.id)" class="delete-btn">删除</button>
      </div>
    </div>
    
    <div class="todo-stats">
      <p>总计: {{ todos.length }} | 已完成: {{ completedCount }} | 待完成: {{ remainingCount }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const newTodo = ref('')
const todos = ref([
  { id: 1, text: '学习Vue 3', completed: false },
  { id: 2, text: '完成项目', completed: true },
  { id: 3, text: '写文档', completed: false }
])

const completedCount = computed(() => 
  todos.value.filter(todo => todo.completed).length
)

const remainingCount = computed(() => 
  todos.value.filter(todo => !todo.completed).length
)

const addTodo = () => {
  if (newTodo.value.trim()) {
    todos.value.push({
      id: Date.now(),
      text: newTodo.value.trim(),
      completed: false
    })
    newTodo.value = ''
  }
}

const deleteTodo = (id) => {
  const index = todos.value.findIndex(todo => todo.id === id)
  if (index > -1) {
    todos.value.splice(index, 1)
  }
}
</script>

<style scoped>
.todo-container {
  max-width: 600px;
  margin: 0 auto;
}

.add-todo {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.todo-input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.add-btn {
  padding: 0.5rem 1rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border-bottom: 1px solid #eee;
}

.todo-item.completed .todo-text {
  text-decoration: line-through;
  color: #999;
}

.todo-text {
  flex: 1;
}

.delete-btn {
  padding: 0.25rem 0.5rem;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.todo-stats {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
  text-align: center;
}
</style>
'''
    
    with open(components_path / "TodoList.vue", "w", encoding="utf-8") as f:
        f.write(todo_list_vue)
    
    # 创建About.vue
    about_vue = '''<template>
  <div class="about-container">
    <h2>关于我们</h2>
    <div class="content">
      <p>这是一个使用Vue 3开发的简单待办事项应用。</p>
      
      <h3>技术栈</h3>
      <ul>
        <li>Vue 3 - 前端框架</li>
        <li>Vue Router - 路由管理</li>
        <li>Composition API - 组合式API</li>
        <li>Vite - 构建工具</li>
      </ul>
      
      <h3>功能特性</h3>
      <ul>
        <li>添加待办事项</li>
        <li>标记完成状态</li>
        <li>删除待办事项</li>
        <li>统计功能</li>
      </ul>
      
      <div class="footer">
        <p>由AI助手生成 © 2024</p>
      </div>
    </div>
  </div>
</template>

<script setup>
// 静态页面，无需响应式数据
</script>

<style scoped>
.about-container {
  max-width: 600px;
  margin: 0 auto;
}

.content {
  line-height: 1.6;
}

.content h3 {
  color: #2c3e50;
  margin-top: 2rem;
}

.content ul {
  padding-left: 2rem;
}

.content li {
  margin-bottom: 0.5rem;
}

.footer {
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 1px solid #eee;
  text-align: center;
  color: #666;
}
</style>
'''
    
    with open(components_path / "About.vue", "w", encoding="utf-8") as f:
        f.write(about_vue)
    
    # 创建README.md
    readme = '''# Vue Todo App

一个使用Vue 3构建的简单待办事项应用。

## 功能特性

- ✅ 添加新的待办事项
- ✅ 标记任务完成状态
- ✅ 删除不需要的任务
- ✅ 实时统计任务数量
- ✅ 响应式设计
- ✅ 路由导航

## 技术栈

- **Vue 3** - 渐进式JavaScript框架
- **Vue Router** - 官方路由管理器
- **Composition API** - Vue 3的新特性
- **Vite** - 下一代前端构建工具

## 项目结构

```
vue_todo_app/
├── src/
│   ├── components/
│   │   ├── TodoList.vue    # 待办事项列表组件
│   │   └── About.vue       # 关于页面组件
│   ├── App.vue             # 根组件
│   └── main.js             # 应用入口
├── package.json            # 项目配置
└── README.md              # 项目说明
```

## 开发指南

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

### 构建生产版本

```bash
npm run build
```

## 组件说明

### TodoList.vue
主要的待办事项管理组件，包含：
- 新增任务输入框
- 任务列表显示
- 完成状态切换
- 任务删除功能
- 统计信息显示

### About.vue
静态的关于页面，介绍应用的技术栈和功能特性。

## 特色功能

1. **响应式数据管理** - 使用Vue 3的Composition API
2. **实时统计** - 自动计算完成和未完成任务数量
3. **键盘支持** - 支持回车键快速添加任务
4. **状态持久化** - 可扩展支持本地存储
5. **组件化设计** - 清晰的组件结构便于维护

## 扩展建议

- 添加本地存储功能
- 实现任务分类
- 添加截止日期
- 支持任务排序
- 添加搜索过滤功能
'''
    
    with open(project_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    
    print(f"✅ 创建Vue项目: {project_path}")

def create_python_api_project():
    """创建一个Python API项目示例"""
    project_path = CODE_ROOT / "python_api_server"
    project_path.mkdir(exist_ok=True)
    
    # 创建requirements.txt
    requirements = '''fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-decouple==3.8
'''
    
    with open(project_path / "requirements.txt", "w") as f:
        f.write(requirements)
    
    # 创建main.py
    main_py = '''"""
FastAPI 示例应用
一个简单的用户管理和任务管理API
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

app = FastAPI(
    title="任务管理API",
    description="一个简单的任务管理系统API",
    version="1.0.0"
)

security = HTTPBearer()

# 数据模型
class User(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime

class Task(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    completed: bool = False
    user_id: str
    created_at: datetime
    updated_at: datetime

class CreateTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None

class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

# 内存数据存储（生产环境应使用数据库）
users_db = {}
tasks_db = {}

@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "欢迎使用任务管理API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/users", response_model=List[User])
async def get_users():
    """获取所有用户"""
    return list(users_db.values())

@app.post("/users", response_model=User)
async def create_user(username: str, email: str):
    """创建新用户"""
    # 检查用户名是否已存在
    for user in users_db.values():
        if user.username == username:
            raise HTTPException(status_code=400, detail="用户名已存在")
    
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username=username,
        email=email,
        created_at=datetime.now()
    )
    users_db[user_id] = user
    return user

@app.get("/users/{user_id}/tasks", response_model=List[Task])
async def get_user_tasks(user_id: str):
    """获取用户的所有任务"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user_tasks = [task for task in tasks_db.values() if task.user_id == user_id]
    return user_tasks

@app.post("/users/{user_id}/tasks", response_model=Task)
async def create_task(user_id: str, task_data: CreateTaskRequest):
    """为用户创建新任务"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    task_id = str(uuid.uuid4())
    task = Task(
        id=task_id,
        title=task_data.title,
        description=task_data.description,
        completed=False,
        user_id=user_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    tasks_db[task_id] = task
    return task

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_data: UpdateTaskRequest):
    """更新任务"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks_db[task_id]
    
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.completed is not None:
        task.completed = task_data.completed
    
    task.updated_at = datetime.now()
    return task

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    del tasks_db[task_id]
    return {"message": "任务已删除"}

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "users_count": len(users_db),
        "tasks_count": len(tasks_db)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    with open(project_path / "main.py", "w", encoding="utf-8") as f:
        f.write(main_py)
    
    # 创建config.py
    config_py = '''"""
应用配置模块
"""
from decouple import config
from typing import List

class Settings:
    """应用设置"""
    
    # 应用基本信息
    APP_NAME: str = "任务管理API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = config("DEBUG", default=True, cast=bool)
    
    # 服务器配置
    HOST: str = config("HOST", default="0.0.0.0")
    PORT: int = config("PORT", default=8000, cast=int)
    
    # 安全配置
    SECRET_KEY: str = config("SECRET_KEY", default="your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 数据库配置
    DATABASE_URL: str = config("DATABASE_URL", default="sqlite:///./tasks.db")
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # 日志配置
    LOG_LEVEL: str = config("LOG_LEVEL", default="INFO")
    LOG_FILE: str = config("LOG_FILE", default="app.log")

# 创建设置实例
settings = Settings()
'''
    
    with open(project_path / "config.py", "w", encoding="utf-8") as f:
        f.write(config_py)
    
    # 创建utils.py
    utils_py = '''"""
工具函数模块
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """验证令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None

def generate_id() -> str:
    """生成唯一ID"""
    return secrets.token_urlsafe(16)

def hash_string(text: str) -> str:
    """计算字符串的MD5哈希值"""
    return hashlib.md5(text.encode()).hexdigest()

def format_datetime(dt: datetime) -> str:
    """格式化日期时间"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def validate_email(email: str) -> bool:
    """简单的邮箱格式验证"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

class ResponseFormatter:
    """响应格式化工具"""
    
    @staticmethod
    def success(data=None, message="操作成功"):
        """成功响应"""
        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def error(message="操作失败", code=None):
        """错误响应"""
        return {
            "success": False,
            "message": message,
            "code": code,
            "timestamp": datetime.now().isoformat()
        }
'''
    
    with open(project_path / "utils.py", "w", encoding="utf-8") as f:
        f.write(utils_py)
    
    print(f"✅ 创建Python API项目: {project_path}")

def main():
    """主函数"""
    print("🚀 开始创建演示项目...")
    
    # 确保目录存在
    CODE_ROOT.mkdir(exist_ok=True)
    
    # 创建项目
    create_vue_project()
    create_python_api_project()
    
    print("\n✨ 演示项目创建完成!")
    print(f"📁 项目位置: {CODE_ROOT}")
    print("\n已创建的项目:")
    print("1. test_project - Python基础项目")
    print("2. vue_todo_app - Vue 3待办事项应用")
    print("3. python_api_server - FastAPI服务器")
    
    print("\n💡 现在可以:")
    print("1. 启动后端服务器: cd backend && python -m uvicorn src.main:app --reload")
    print("2. 启动前端服务器: cd frontend && npm run dev")
    print("3. 访问 http://localhost:5173/tmpcode 查看代码")

if __name__ == "__main__":
    main()
