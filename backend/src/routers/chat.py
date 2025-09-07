"""聊天路由"""
from datetime import datetime
from typing import List
import os
from fastapi import APIRouter, HTTPException, status, Depends
from ..database import get_database
from ..config import settings
from ..models import (
    ChatRequest, 
    ChatResponse, 
    SessionResponse, 
    Session, 
    Message, 
    User
)
from ..auth import get_current_user
from ..chat_service import chat_service

router = APIRouter(prefix="/chat", tags=["聊天"])


@router.post("/send", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    
    '''
        第一个chat_request来自于前端发来的消息，
        第二个是来源于depends函数
    '''
    """发送消息"""
    db = get_database()
    
    
    # 创建用户消息
    user_message = Message(
        content=chat_request.message,
        role="user"
    )
    
    session_id = chat_request.session_id
    session = None
    
    # 如果没有提供session_id，创建新会话
    if not session_id:
        session = Session(
            user_id=current_user.id,
            title=chat_request.message[:20] + "..." if len(chat_request.message) > 20 else chat_request.message,
            model=chat_request.model,
            messages=[user_message]
        )
        await db.sessions.insert_one(session.dict())
        session_id = session.id
    else:
        # 获取现有会话
        session_data = await db.sessions.find_one({"id": session_id, "user_id": current_user.id})
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        session = Session(**session_data)
        session.messages.append(user_message)
    
    # 生成AI响应
    # 拓展：这里可以改变模型的生成方式
    ai_response_content = await chat_service.generate_response(session.messages,
                                                               chat_request.mode,
                                                               chat_request.model,
                                                               code_generation_root_dir='_'.join([str(session.id)+'/', str(session.user_id),"dir"])
                                                               )
    # 创建AI消息
    ai_message = Message(
        content=ai_response_content or "AI暂无响应",
        role="assistant"
    )
    
    # 更新会话
    session.messages.append(ai_message)
    session.updated_at = datetime.utcnow()
    
    # 保存到数据库
    await db.sessions.replace_one(
        {"id": session_id},
        session.dict()
    )
    
    print(f"ChatResponse is {ChatResponse(
        message=ai_message,
        session_id=session_id
    )}")
    return ChatResponse(
        message=ai_message,
        session_id=session_id
    )


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(current_user: User = Depends(get_current_user)):
    """获取用户的会话列表"""
    db = get_database()
    
    # 获取最多5个会话，按更新时间倒序
    cursor = db.sessions.find(
        {"user_id": current_user.id}
    ).sort("updated_at", -1).limit(5)
    
    sessions = []
    async for session_data in cursor:
        session = Session(**session_data)
        sessions.append(SessionResponse(
            id=session.id,
            title=session.title,
            model=session.model,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=len(session.messages)
        ))
    
    return sessions


@router.get("/sessions/{session_id}/messages", response_model=List[Message])
async def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取会话的消息列表"""
    db = get_database()
    
    session_data = await db.sessions.find_one({"id": session_id, "user_id": current_user.id})
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    session = Session(**session_data)
    return session.messages


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除会话"""
    db = get_database()
    
    result = await db.sessions.delete_one({"id": session_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    return {"message": "会话删除成功"}
