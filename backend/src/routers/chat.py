"""聊天路由"""
from datetime import datetime
from typing import List
import os
import time
import json
from openai import OpenAI
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
import asyncio
from ..database import get_database
from ..config import settings
from ..models import (
    ChatRequest, 
    ChatResponse, 
    SessionResponse, 
    Session, 
    Message, 
    CodeMessage,
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
        非流式调用
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
    code_generation_root_dir = settings.base_code_dir+\
            '/' + '_'.join([str(session.id)+'/', str(session.user_id),"dir",  str(time.time())])
    ai_response_content = await chat_service.generate_response(session.messages,
                                                               chat_request.mode,
                                                               chat_request.model,
                                                               code_generation_root_dir=code_generation_root_dir
                                                               )
    # 创建AI消息
    if chat_request.mode == "Agent":
        ai_message = CodeMessage(
            content=ai_response_content or "AI暂无响应",
            role="assistant",
            root_path=code_generation_root_dir
        )
    else:
        ai_message = Message(
            content=ai_response_content or "AI暂无响应",
            role="assistant",
        )
    
    # 更新会话
    session.messages.append(ai_message)
    session.updated_at = datetime.utcnow()
    
    # 保存到数据库
    await db.sessions.replace_one(
        {"id": session_id},
        session.dict()
    )
    
    print(f"[非流式调用方法]:ChatResponse is {ChatResponse(
        message=ai_message,
        session_id=session_id
    )}")
    
    return ChatResponse(
        message=ai_message,
        session_id=session_id
    )


@router.post("/sendstream")
async def send_stream(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    
    # 获取数据库连接
    db = get_database()
    # 构造用户消息结构
    user_message = Message(
        content=chat_request.message,
        role="user"
    )
    # 会话管理：创建新会话或获取现有会话
    session_id = chat_request.session_id
    session = None
    try:
        if not session_id:
            # 创建新会话
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
    except Exception as e:
        # 数据库操作异常处理
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"会话处理失败: {str(e)}"
        )
    
    
    #  会话里面添加message，然后不断地往里面填充
    ai_message = Message(
            content="",
            role="assistant",
        )
    
    
    # 将后端message格式转化为模型需要的格式
    formatted_messages = []
    for message in session.messages:
        formatted_messages.append({
            "role": message.role,
            "content": message.content
        })
    client = OpenAI(api_key=settings.deepseek_api_key,
                             base_url=settings.deepseek_base_url
                             )
    response_stream = client.chat.completions.create(
                    model=settings.deepseek_chat_model,
                    messages=formatted_messages,
                    stream=True
                )
    async def generate_data():
        streaming_is_begin = False
        yield f"event: message\ndata: {json.dumps({'delta': '##[BEGIN]##','session_id': session_id})}\n\n"
        for chunk in response_stream:
            if chunk.choices[0].delta.content == '' and streaming_is_begin == True:
                print("is over")
                streaming_is_begin = False
                
                session.messages.append(ai_message)
                session.updated_at = datetime.utcnow()
                
                # 异步保存到数据库（避免阻塞）
                await db.sessions.replace_one(
                    {"id": session_id},
                    session.dict()
                )
                yield f"event: message\ndata: {json.dumps({'delta': '##[DONE]##'})}\n\n"
            else:
                if not streaming_is_begin:
                    streaming_is_begin = True
                str_tokens= chunk.choices[0].delta.content
                ai_message.content += str_tokens
                yield f"event: message\ndata: {json.dumps({'delta': str_tokens})}\n\n"
            await asyncio.sleep(0.01)  # 模拟延迟

    return StreamingResponse(generate_data(), media_type="text/event-stream",headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
        })


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(current_user: User = Depends(get_current_user)):
    """获取用户的会话列表"""
    db = get_database()
    
    # 获取最多5个会话，按更新时间倒序
    # mongodb是一个集合数据库，非关系型数据库
    cursor = db.sessions.find(
        {"user_id": current_user.id}
    ).sort("updated_at", -1)
    
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
