"""聊天服务"""
import httpx
import os
import json
from typing import List, Dict, Any
from .config import settings
from .models import Message
from openai import OpenAI
from  fastapi.responses import StreamingResponse

class ChatService:
    """聊天服务类"""
    
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url
        
        self.client = OpenAI(api_key=settings.deepseek_api_key,
                             base_url=settings.deepseek_base_url
                             )

    
    async def generate_response(
        self,
        messages: List[Message],
        mode: str = "Ask",
        model: str = "deepseek-chat",
        **kwargs
    ) -> str:
        """
        生成AI响应的主入口方法
        
        根据不同的模式和配置，选择合适的响应生成策略：
        - Ask模式: 普通对话响应
        - Agent模式: 代码生成agent响应
        
        Args:
            messages: 对话消息历史列表
            mode: 对话模式（Ask/Agent）
            model: 使用的LLM模型名称
            **kwargs: 其他配置参数
            
        Returns:
            str: 生成的AI响应内容
        """
        # 检查API密钥配置
        if not self.api_key or self.api_key == "test-api-key":
            # 返回模拟响应用于演示和测试
            user_message = messages[-1].content if messages else ""
            return self._generate_mock_response(user_message, model)
        
        try:
            # 根据不同模式选择响应策略
            if mode == "Ask":
                # 普通对话模式
                model_answer = self._get_nonstreaming_response(messages, mode, model)
            elif mode == "Agent":
                # 代码生成agent模式
                model_answer = self._code_agent_llm_generate_response(
                    messages=messages, 
                    model=model, 
                    **kwargs
                )
            else:
                # 未知模式，默认使用Ask模式
                model_answer = self._get_nonstreaming_response(messages, "Ask", model)
            
            return model_answer
            
        except Exception as e:
            # 生成响应时的异常处理
            error_message = f"生成AI响应时出错: {str(e)}"
            print(error_message)
            return error_message
    
    
    def _code_agent_llm_generate_response(self,
                                          messages: List[Message],
                                          model: str = "deepseek-reasoner",
                                          stream_callback = None,
                                          **kwargs):
        '''
            自己写代码的ai agent, 算法： ReAct
        '''
        from .ai_code_agent.agent import get_code_agent_response
        
        # 检查模型
        if model not in settings.supported_LLM:
            return f"Current system can not support model {model}!"
        
        # 检查文件路径
        if "code_generation_root_dir" in kwargs:
            tar_dir = kwargs["code_generation_root_dir"]
        else:
            return ("in Function _code_agent_llm_generate_response: \
                kwargs has no code_generation_root_dir variable, the backend can not refer to correct code generation base_dir!!!!")
        
        os.makedirs(tar_dir, exist_ok=True)
        print(f"创建了独立代码目录！！！\n")
        
        messages[-1].content += f"你是一个经验丰富的程序员，请在指定的文件路径：{tar_dir} 进行代码编写\n 要求：\
            1.所有的操作都在上面的路径下进行，不能修改路径外的任何东西 2.代码简介规范有注释"
        
        # 提取用户的最后一条消息作为任务
        task = messages[-1].content
        model_answer : str = get_code_agent_response(task, tar_dir, model, stream_callback)
        
        return model_answer

    def _code_agent_llm_generate_streaming_response(self,
                                                   messages: List[Message],
                                                   model: str = "deepseek-reasoner",
                                                   stream_callback = None,
                                                   **kwargs):
        '''
            流式生成代码的ai agent, 算法： ReAct
        '''
        from .ai_code_agent.agent import get_code_agent_response
        
        # 检查模型
        if model not in settings.supported_LLM:
            if stream_callback:
                stream_callback(f"❌ **错误**: 当前系统不支持模型 {model}!")
            return f"Current system can not support model {model}!"
        
        # 检查文件路径
        if "code_generation_root_dir" in kwargs:
            tar_dir = kwargs["code_generation_root_dir"]
        else:
            error_msg = "代码生成路径未指定，无法继续执行"
            if stream_callback:
                stream_callback(f"❌ **错误**: {error_msg}")
            return error_msg
        
        os.makedirs(tar_dir, exist_ok=True)
        print(f"创建了独立代码目录！！！")
        if stream_callback:
            stream_callback(f"📁 创建临时代码目录！！！！\n")
        
        # 提取用户的最后一条消息作为任务
        task = ""
        for message in messages:
            task += f"{message.role}: {message.content}\n\n"
        task += f"**你是一个经验丰富的程序员，请在指定的文件路径：{tar_dir} 进行代码编写 要求：\
            1.所有的操作都在上面的路径下进行，不能修改路径外的任何东西 2.代码简介规范有注释**"
        model_answer : str = get_code_agent_response(task, tar_dir, model, stream_callback)
        
        return model_answer

    # 非流式传输数据
    def _get_nonstreaming_response(
        self, 
        messages: List[Message], 
        mode: str = "Ask", 
        model: str = "deepseek-chat"
    ) -> str:
        """
        生成完整的AI响应，通过调用DeepSeek的非流式接口        
        Args:
            messages: 对话消息历史列表
            mode: 对话模式（Ask/Agent等）
            model: 使用的LLM模型名称
            
        Returns:
            str: 完整的AI响应内容
        """
        #  会话里面添加message，然后不断地往里面填充
    
    
        # 将后端message格式转化为模型需要的格式
        formatted_messages = []
        for message in messages:
            formatted_messages.append({
                "role": message.role,
                "content": message.content
            })
        try:
            if model == "deepseek-chat":
                response = self.client.chat.completions.create(
                            model=settings.deepseek_chat_model,
                            messages=formatted_messages,
                            stream=False
                    )
            else:
                raise ValueError(f"Unsupported model: {model}")

            return response.choices[0].message.content
    
        except httpx.HTTPError as e:
            # 处理HTTP请求异常
            error_message = f"HTTP请求错误: {str(e)}"
            print(error_message)
            return error_message
        except Exception as e:
            # 处理其他异常
            error_message = f"生成AI响应时出错: {str(e)}"
            print(error_message)
            return error_message
    

# 全局聊天服务实例
chat_service = ChatService()
