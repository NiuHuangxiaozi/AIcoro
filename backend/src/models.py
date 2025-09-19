"""数据模型"""
from datetime import datetime
from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class User(BaseModel):
    """用户模型"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    username: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# 一般的文本回答
class Message(BaseModel):
    """消息模型"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    role: str  # "user" 或 "assistant"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    code_root_path :  Optional[str] = None

    

class Session(BaseModel):
    """会话模型"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    title: str = "新对话"
    messages: List[Message] = []
    model: str = "deepseek-chat"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# API请求/响应模型
class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class UserRegister(BaseModel):
    """用户注册请求"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户响应"""
    id: str
    username: str
    created_at: datetime


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    session_id: Optional[str] = None
    model: str = "deepseek-chat"
    mode: str = "Ask"


class ChatResponse(BaseModel):
    """聊天响应"""
    message: Message
    session_id: str
    


class SessionResponse(BaseModel):
    """会话响应"""
    id: str
    title: str
    model: str
    created_at: datetime
    updated_at: datetime
    message_count: int
