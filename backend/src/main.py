"""主应用程序入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import connect_to_mongo, close_mongo_connection
from .routers import auth, chat, code
from .config import settings
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时连接数据库
    await connect_to_mongo()
    yield
    # 关闭时断开数据库连接
    await close_mongo_connection()


# 创建FastAPI应用
app = FastAPI(
    title="AI对话助手",
    description="一个基于FastAPI和Vue3的AI对话助手",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(code.router)


@app.get("/")
async def root():
    """根路径"""
    return {"message": "AI对话助手API服务运行中"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}