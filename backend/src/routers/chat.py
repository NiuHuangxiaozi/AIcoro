"""聊天路由"""
from datetime import datetime
from typing import List
import os
import time
import json
import shutil
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
    
    
    # 根据模式选择不同的流式处理方式
    if chat_request.mode == "Agent":
        print(f"Agent mode")
        # Agent模式：使用代码生成agent
        return await _handle_agent_streaming(chat_request, session, session_id, current_user, db)
    else:
        print(f"Ask mode")
        # Ask模式：使用标准聊天流式处理
        return await _handle_ask_streaming(chat_request, session, session_id, db)


async def _handle_ask_streaming(chat_request: ChatRequest, session: Session, session_id: str, db):
    """处理Ask模式的流式响应"""
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


async def _handle_agent_streaming(chat_request: ChatRequest, session: Session, session_id: str, current_user: User, db):
    """处理Agent模式的流式响应"""
    print(f"in _handle_agent_streaming")
    # 创建代码生成目录
    code_generation_root_dir = settings.base_code_dir + \
            '/' + '_'.join([str(session.id)+'/', str(session.user_id),"dir",  str(time.time())])
    
    # 准备AI消息容器
    ai_message = CodeMessage(
        content="",
        role="assistant",
        root_path=code_generation_root_dir
    )
    
    # 创建队列用于在线程间传递流式消息
    import queue
    message_queue = queue.Queue()
    
    
    # 启动代码生成任务
    import threading
    
    
    generation_complete = threading.Event()
    final_answer = None
    error_occurred = None
    def run_agent():
            nonlocal final_answer, error_occurred
            try:
                final_answer = chat_service._code_agent_llm_generate_streaming_response(
                    messages=session.messages,
                    model=chat_request.model,
                    stream_callback=stream_callback,
                    code_generation_root_dir=code_generation_root_dir
                )
            except Exception as e:
                error_occurred = str(e)
            finally:
                print(f"generation_complete.set()")
                generation_complete.set()
    # 创建流式回调函数
    def stream_callback(message: str):
            print(f"stream_callback from chat router: {message}")
            # 将消息放入队列
            message_queue.put(message)
            # 同时添加到AI回复中
            ai_message.content += message + "\n\n"
        
    print(f"before agent_thread start")
    agent_thread = threading.Thread(target=run_agent,name=f"agent_thread")
    agent_thread.daemon = True
    agent_thread.start()
    print(f'threading.enumerate() is {threading.enumerate()}')
    
    async def generate_data():
        yield f"event: message\ndata: {json.dumps({'delta': '##[BEGIN]##','session_id': session_id})}\n\n"
        
        # # 创建流式回调函数
        # def stream_callback(message: str):
        #     print(f"stream_callback from chat router: {message}")
        #     # 将消息放入队列
        #     message_queue.put(message)
        #     # 同时添加到AI回复中
        #     ai_message.content += message + "\n\n"
        
        # 启动代码生成任务
        # import threading
        # generation_complete = threading.Event()
        # final_answer = None
        # error_occurred = None
        
        # def run_agent():
        #     nonlocal final_answer, error_occurred
        #     try:
        #         final_answer = chat_service._code_agent_llm_generate_streaming_response(
        #             messages=session.messages,
        #             model=chat_request.model,
        #             stream_callback=stream_callback,
        #             code_generation_root_dir=code_generation_root_dir
        #         )
        #     except Exception as e:
        #         error_occurred = str(e)
        #     finally:
        #         generation_complete.set()
        
        # # 在后台线程中运行agent
        # agent_thread = threading.Thread(target=run_agent)
        # agent_thread.daemon = True
        # agent_thread.start()
        # print(f'threading.enumerate() is {threading.enumerate()}')
        
        # 持续读取队列中的消息并发送
        while not generation_complete.is_set() or not message_queue.empty():
            try:
                # 尝试从队列获取消息，设置超时避免阻塞
                message = message_queue.get(timeout=0.1)
                yield f"event: message\ndata: {json.dumps({'delta': message})}\n\n"
                await asyncio.sleep(0.01)  # 小延迟确保流式体验
            except queue.Empty:
                # 队列为空，继续等待
                await asyncio.sleep(0.1)

        # 处理最终结果或错误
        if error_occurred:
            error_msg = f"❌ **代码生成过程中发生错误**: {error_occurred}"
            ai_message.content += error_msg
            yield f"event: message\ndata: {json.dumps({'delta': error_msg})}\n\n"
        elif final_answer:
            final_msg = f"\n\n**最终结果**: {final_answer}"
            ai_message.content += final_msg
            yield f"event: message\ndata: {json.dumps({'delta': final_msg})}\n\n"
        
        # 保存会话
        try:
            session.messages.append(ai_message)
            session.updated_at = datetime.utcnow()
            
            await db.sessions.replace_one(
                {"id": session_id},
                session.dict()
            )
        except Exception as e:
            print(f"保存会话时出错: {e}")
        
        yield f"event: message\ndata: {json.dumps({'delta': '##[DONE]##'})}\n\n"

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
    
    # 删除对应的本地文件夹（因为可能有code相关的对话）
    for item in os.listdir(settings.base_code_dir):
        item_path = os.path.join(settings.base_code_dir, item)
        # 检查是否是目录且名称中包含 session_id
        if os.path.isdir(item_path) and f'{session_id}' in item:
            try:
                # 删除该目录及其所有内容
                shutil.rmtree(item_path)
                print(f"已删除目录：{item_path}")
            except Exception as e:
                print(f"删除目录 {item_path} 时发生错误：{e}")
                
    return {"message": "会话删除成功"}



@router.delete("/sessions")
async def delete_all_sessions(
    current_user: User = Depends(get_current_user)
):
    """删除所有会话"""
    db = get_database()
    result = await db.sessions.delete_many({"user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    try:
        shutil.rmtree(settings.base_code_dir)
        print(f"目录 '{settings.base_code_dir}' 及其所有内容已成功删除。")
    except Exception as e:
        print(f"删除目录 '{settings.base_code_dir}' 时发生错误：{e}")
    return {"message": "所有会话删除成功"}