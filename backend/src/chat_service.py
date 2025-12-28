"""聊天服务"""
from operator import call
import httpx
import os
import json
import yaml
import re
import asyncio
from typing import List, Dict, Any
from .config import settings
from .models import Message
from openai import OpenAI
from  fastapi.responses import StreamingResponse
from jinja2 import Template
from typing import Tuple
import logging
from fastmcp import Client
from pydantic import BaseModel
from fastmcp.client import Client
import ast

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
     
    
    
    
    
    # reAct 对话的接口
    # FastApiMCP 会自动在 mcp_app 上注册两个标准 JSON-RPC 方法
    # 查看所有的接口列表
    async def get_available_tools(self):
        """获取工具列表"""
        async with Client(settings.MCP_URL) as mcp_client:
            tools = await mcp_client.list_tools()
            return tools


    # 调用具体的工具
    async def call_mcp_tool(self, tool_name: str, arguments: dict) -> str:
        """调用 MCP 工具"""
        async with Client(settings.MCP_URL) as mcp_client:
            response = await mcp_client.call_tool(tool_name, arguments, timeout=60.0)
            # 注意：response 可能是 list 或单个 result，根据 FastMCP 实际返回调整
            if response.content and len(response.content) > 0:
                return response.content[0].text
            else:
                return "工具执行错误：没有返回结果"
    
    
    import re
    import ast
    from typing import Dict, Any

    def parse_action(self, code_str: str) -> Tuple[str, Dict[str, Any]]:
        # 匹配函数名和括号内的内容
        match = re.match(r'(\w+)\((.*)\)', code_str, re.DOTALL)
        if not match:
            raise ValueError("Invalid function call syntax")

        func_name = match.group(1)
        args_str = match.group(2).strip()

        # 如果参数为空，返回空字典
        if not args_str:
            return {}

        # 使用与原逻辑相同的参数分割方式（处理字符串、嵌套括号等）
        args_parts = []
        current_arg = ""
        in_string = False
        string_char = None
        paren_depth = 0
        i = 0

        while i < len(args_str):
            char = args_str[i]

            if not in_string:
                if char in ['"', "'"]:
                    in_string = True
                    string_char = char
                    current_arg += char
                elif char == '(':
                    paren_depth += 1
                    current_arg += char
                elif char == ')':
                    paren_depth -= 1
                    current_arg += char
                elif char == ',' and paren_depth == 0:
                    args_parts.append(current_arg.strip())
                    current_arg = ""
                else:
                    current_arg += char
            else:
                current_arg += char
                # 判断是否是未转义的引号结束
                if char == string_char and (i == 0 or args_str[i - 1] != '\\'):
                    in_string = False
                    string_char = None
            i += 1

        if current_arg.strip():
            args_parts.append(current_arg.strip())

        # 现在解析每个 part 为 key=value
        result = {}
        for part in args_parts:
            if '=' not in part:
                raise ValueError(f"Only keyword arguments are supported, got: {part}")
            
            # 从右边第一个 = 分割（防止值中包含 =，如 url="http://a=b"）
            eq_index = part.find('=')
            key = part[:eq_index].strip()
            value_str = part[eq_index + 1:].strip()

            if not key.isidentifier():
                raise ValueError(f"Invalid parameter name: {key}")

            try:
                # 安全解析值：支持字符串、数字、列表、字典等
                value = ast.literal_eval(value_str)
            except (ValueError, SyntaxError):
                # 如果 literal_eval 失败（如纯标识符），保留为字符串？
                # 但通常我们希望值是字面量。这里严格要求必须可解析。
                raise ValueError(f"Invalid value format: {value_str}")

            result[key] = value

        return func_name, result

    def load_react_prompt(self, tools, user_query, scratchpad):
        # 1. 从 YAML 读取模板字符串
        with open("./src/prompts/react_prompt.yaml", "r", encoding="utf-8") as f:
            prompts = yaml.safe_load(f)
        
        # 2. 用 Jinja2 渲染
        template_str = prompts["react_prompt"]
        template = Template(template_str)
        
        return template.render(
            tools=tools,
            user_query=user_query,
            scratchpad=scratchpad
        )
    
    # reAct 对话的实现
    async def reAct_chat_stream(self,
                    messages: List[Message],
                    model: str = "deepseek-chat"):
        '''
            采用reAct的方式进行对话操作
        '''
        # 1. 获取工具描述，Tool是一个Basemodel对象
        tools = await self.get_available_tools()
        
        step = 0
        scratchpad = ""
        while step < settings.MAX_STEPS:
            prompt = self.load_react_prompt(tools, messages[-1].content, scratchpad)
            response_stream = self.client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": prompt}],
                            stream=True)
            
            cur_step_answer = ""
            for chunk in response_stream:
                cur_step_answer += chunk.choices[0].delta.content
                yield chunk.choices[0].delta.content

            # cur_step_answer 是当前模型的输出
            thought_match = re.search(r"<thought>(.*?)</thought>", cur_step_answer, re.DOTALL)
            if thought_match:
                # group 是一个捕获组，group就是获取第一个左括号对应的内容
                thought = thought_match.group(1)
                # 将模型的思考加入上下文
                # 流式发送思考过程
                yield f"💭[思考中]: {thought.strip()}\n"
            
            # 检测模型是否输出 Final Answer，如果是的话，直接返回
            if "<final_answer>" in cur_step_answer:
                final_answer = re.search(r"<final_answer>(.*?)</final_answer>", cur_step_answer, re.DOTALL)
                yield "✅ 问题回答完毕"
                yield final_answer.group(1)
                return
            
            # 检测模型是否输出 Action，如果是的话，直接返回
            action_match = re.search(r"<action>(.*?)</action>", cur_step_answer, re.DOTALL)
            if not action_match:
                raise RuntimeError("模型未输出 <action>")
            action = action_match.group(1)
            
            # 解释我们的行为
            tool_name, args = self.parse_action(action)

            print(f"\n\n🔧 Action: {tool_name}({', '.join(args)})")
            
            yield f"🔧 Action: {tool_name}({', '.join(args)})\n"

            try:
                observation = await self.call_mcp_tool(tool_name, args)
                yield f"🔧 MCP ToolResult: {observation}\n"
            except Exception as e:
                observation = f"工具执行错误：{str(e)}"
                yield f"❌ **工具执行错误**: {observation}\n"

            # 将用户的观察继续加入到消息队列里面
            logging.info(f"\n\n🔍 Observation：{observation}")
            obs_msg = f"<observation>{observation}</observation>"
            messages.append(Message(role="user", content=obs_msg))

# 全局聊天服务实例
chat_service = ChatService()
