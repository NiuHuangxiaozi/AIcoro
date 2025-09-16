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
        print(f"创建了独立代码目录！！！")
        
        messages[-1].content += f"你是一个经验丰富的程序员，请在指定的文件路径：{tar_dir} 进行代码编写 要求：\
            1.所有的操作都在上面的路径下进行，不能修改路径外的任何东西 2.代码简介规范有注释"
        
        model_answer : str = get_code_agent_response(messages, tar_dir, model)
        
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
    
    
    # 生成假的数据
    def _generate_mock_response(self, user_message: str, model: str) -> str:
        """生成模拟AI响应用于演示"""
        import random
        
        # 根据用户消息内容生成不同类型的响应
        user_message_lower = user_message.lower()
        
        if any(word in user_message_lower for word in ['你好', 'hello', 'hi', '您好']):
            responses = [
                "你好！我是AI助手，很高兴为您服务。有什么我可以帮助您的吗？",
                "您好！我是基于DeepSeek的AI对话助手，请告诉我您需要什么帮助。",
                "Hi！欢迎使用AI对话助手，我可以回答问题、提供建议或进行对话。"
            ]
        elif any(word in user_message_lower for word in ['谢谢', 'thank', '感谢']):
            responses = [
                "不客气！很高兴能帮助到您。还有其他问题吗？",
                "您太客气了！如果还有其他需要帮助的地方，随时告诉我。",
                "不用谢！这是我应该做的。有什么其他问题吗？"
            ]
        elif any(word in user_message_lower for word in ['编程', 'code', '代码', 'python', 'javascript']):
            responses = [
                f"关于编程问题，我很乐意帮助您！您提到的'{user_message}'是一个很好的话题。作为AI助手，我可以为您提供编程建议、代码示例和最佳实践。",
                f"编程是一个非常有趣的领域！针对您的问题'{user_message}'，我建议先明确需求，然后选择合适的技术栈。需要我详细解释某个特定的编程概念吗？",
                f"看起来您对编程很感兴趣！关于'{user_message}'，我可以提供相关的代码示例和解决方案。请告诉我您具体需要什么帮助？"
            ]
        elif '?' in user_message or '？' in user_message:
            responses = [
                f"这是一个很好的问题！关于'{user_message.replace('?', '').replace('？', '')}'，让我来为您详细解答...",
                f"您的问题很有价值。针对'{user_message}'，我的理解是这样的...",
                f"感谢您的提问！关于这个问题，我认为可以从几个角度来分析..."
            ]
        else:
            responses = [
                f"我理解您说的是'{user_message}'。这确实是一个值得深入讨论的话题。您希望我从哪个角度来分析呢？",
                f"关于'{user_message}'，我有一些想法可以分享。这个话题涉及多个方面，您最关心哪一点？",
                f"您提到的'{user_message}'很有意思。作为AI助手，我可以为您提供相关信息和建议。需要我详细说明吗？",
                f"基于您的输入'{user_message}'，我认为我们可以进一步探讨这个主题。您希望了解更多细节吗？"
            ]
        
        # 根据模型类型调整响应风格
        response = random.choice(responses)
        if model == "deepseek-coder":
            response += "\n\n💡 提示：我是DeepSeek Coder模型，特别擅长编程相关的问题！"
        else:
            response += "\n\n✨ 这是一个演示响应，实际使用时请配置真实的DeepSeek API密钥。"
        
        return response


# 全局聊天服务实例
chat_service = ChatService()
