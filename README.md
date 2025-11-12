# AI对话助手

一个基于FastAPI和Vue3的现代化AI对话助手系统，支持多模型聊天、会话管理和用户认证。




## 演示截屏

## 功能特性

- 🔐 用户认证系统（注册/登录）
- 💬 实时AI对话功能
- 📝 会话历史管理（最多保存5个会话）
- 🤖 支持多种AI模型（DeepSeek Chat/Coder）
- 📱 响应式设计，支持移动端
- 🗄️ MongoDB数据存储
- 🔒 JWT令牌认证

## 技术栈

### 后端
- **FastAPI** - 现代化Python Web框架
- **MongoDB** - 文档数据库
- **Motor** - 异步MongoDB驱动
- **Pydantic** - 数据验证
- **JWT** - 身份认证
- **DeepSeek API** - AI模型服务

### 前端
- **Vue 3** - 渐进式JavaScript框架
- **Composition API** - Vue3组合式API
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP客户端

## 项目结构

```
aicoro/
├── backend/                 # 后端代码
│   ├── src/
│   │   ├── routers/        # API路由
│   │   ├── models.py       # 数据模型
│   │   ├── database.py     # 数据库连接
│   │   ├── auth.py         # 认证逻辑
│   │   ├── chat_service.py # 聊天服务
│   │   ├── config.py       # 配置管理
│   │   └── main.py         # 主应用
│   ├── pyproject.toml      # 项目配置
│   └── run.py             # 启动脚本
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── stores/        # 状态管理
│   │   ├── router/        # 路由配置
│   │   ├── api/           # API接口
│   │   └── style.css      # 全局样式
│   └── package.json       # 依赖配置
└── README.md
```

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 18+
- MongoDB 4.4+

### 后端设置

1. 进入后端目录：
```bash
cd backend
```

2. 安装依赖：
```bash
pip install -e .
```

3. 配置环境变量，创建 `.env` 文件：
```env
# MongoDB配置
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=aicoro

# JWT配置
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# DeepSeek API配置
DEEPSEEK_API_KEY=your-deepseek-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

4. 启动后端服务：
```bash
python run.py
```

后端服务将在 http://localhost:8000 启动

### 前端设置

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 启动开发服务器：
```bash
npm run dev
```

前端应用将在 http://localhost:5173 启动

## 使用说明

### 1. 用户注册/登录
- 访问 http://localhost:5173
- 首次使用需要注册账号
- 注册成功后自动登录

### 2. 开始对话
- 登录后进入聊天界面
- 系统默认显示欢迎消息："Hi, 我能有什么能帮你的"
- 在输入框中输入问题，点击发送或按Enter键
- 可以选择不同的AI模型（DeepSeek Chat/Coder）

### 3. 会话管理
- 左侧边栏显示历史对话
- 点击"新对话"创建新的会话
- 点击历史会话可以查看之前的对话内容
- 支持删除不需要的会话

### 4. 用户管理
- 右上角显示用户信息
- 可以随时登出账户

## API文档

后端启动后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发说明

### 后端开发
- 遵循FastAPI最佳实践
- 使用异步编程模式
- 实现了完整的错误处理
- 支持CORS跨域请求

### 前端开发
- 使用Vue 3 Composition API
- 响应式设计，适配移动端
- 组件化开发
- 状态管理使用Pinia

## 部署

### Docker部署（推荐）
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

### 手动部署
1. 配置生产环境变量
2. 构建前端：`npm run build`
3. 启动后端：`uvicorn src.main:app --host 0.0.0.0 --port 8000`
4. 配置Nginx反向代理

## 注意事项

1. **API密钥安全**：请确保在生产环境中妥善保管DeepSeek API密钥
2. **JWT密钥**：在生产环境中使用强随机密钥
3. **数据库安全**：配置MongoDB的访问控制
4. **会话限制**：系统限制每个用户最多保存5个会话，节省存储空间

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License
