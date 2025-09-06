# AI对话助手 - 部署指南

## 🚀 快速开始

### 前提条件
- Python 3.8+
- Node.js 18+
- MongoDB 4.4+ (可选，系统会自动使用内存数据库作为备选)

### 开发环境启动

#### 1. 启动后端服务
```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -e .

# 启动服务
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. 启动前端服务
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### 3. 访问应用
- 前端地址: http://localhost:5173
- 后端API文档: http://localhost:8000/docs

### 环境配置

#### 后端环境变量 (.env)
```env
# MongoDB配置（可选）
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=aicoro

# JWT配置
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# DeepSeek API配置（可选，用于真实AI响应）
DEEPSEEK_API_KEY=your-deepseek-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

## 🔧 配置说明

### 数据库配置
- **MongoDB**: 生产环境推荐使用MongoDB
- **内存数据库**: 开发测试时，如果MongoDB不可用会自动使用内存数据库

### AI服务配置
- **DeepSeek API**: 配置真实的API密钥以获得实际的AI响应
- **演示模式**: 未配置API密钥时，系统会返回模拟响应用于演示

## 🐳 Docker部署

### 使用Docker Compose
```bash
# 克隆项目
git clone <repository-url>
cd aicoro

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入真实的配置

# 启动所有服务
docker-compose up -d
```

### 服务访问
- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- MongoDB: localhost:27017

## 📋 功能测试

运行集成测试脚本：
```bash
python test_system.py
```

测试内容包括：
- ✅ 前端服务可访问性
- ✅ 后端健康检查
- ✅ 用户注册功能
- ✅ 聊天功能

## 🔒 生产环境部署

### 安全配置
1. **JWT密钥**: 使用强随机密钥
2. **API密钥**: 妥善保管DeepSeek API密钥
3. **数据库**: 配置MongoDB访问控制
4. **HTTPS**: 启用SSL/TLS加密

### 性能优化
1. **前端**: 使用 `npm run build` 构建生产版本
2. **后端**: 使用Gunicorn或其他WSGI服务器
3. **反向代理**: 使用Nginx进行负载均衡
4. **缓存**: 配置Redis缓存（可选）

### 监控和日志
1. **应用监控**: 集成APM工具
2. **日志收集**: 配置日志聚合
3. **健康检查**: 定期检查服务状态

## 🛠️ 故障排除

### 常见问题

#### 1. 后端无法启动
- 检查Python版本和依赖
- 确认端口8000未被占用
- 查看错误日志

#### 2. 前端无法访问
- 确认Node.js版本
- 检查端口5173是否可用
- 重新安装依赖: `npm install`

#### 3. MongoDB连接失败
- 系统会自动切换到内存数据库
- 检查MongoDB服务状态
- 验证连接字符串

#### 4. AI响应异常
- 检查DeepSeek API密钥配置
- 验证网络连接
- 查看API调用日志

### 日志查看
```bash
# 查看后端日志
tail -f backend/logs/app.log

# 查看前端构建日志
npm run build --verbose

# 查看Docker日志
docker-compose logs -f
```

## 📞 支持

如遇到问题，请检查：
1. 📖 README.md - 基本使用说明
2. 📚 API文档 - http://localhost:8000/docs
3. 🐛 日志文件 - 详细错误信息
4. 🧪 测试脚本 - 系统功能验证
