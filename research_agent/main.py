import os
import asyncio
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore
from langgraph.config import get_stream_writer
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

# API密钥配置
tavily_api_key = os.environ["TAVILY_API"]
deepseek_api_key = os.environ["DEEPSEEK_API"]
tavily_client = TavilyClient(api_key=tavily_api_key)

# 网络搜索工具
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

# 决策agent的系统提示 - 判断是否需要网络搜索
decision_instructions = """你是一个智能决策助手。你的任务是分析用户的问题，判断是否需要使用网络搜索来回答。
请考虑以下情况需要网络搜索：
1. 问题涉及最新信息、新闻或实时数据
2. 问题需要外部事实验证或最新研究
3. 问题涉及具体的技术细节、API或工具用法
4. 问题需要查找特定网站、文档或资源

不需要网络搜索的情况：
1. 简单的事实性问题（如数学计算、基本概念解释）
2. 基于常识或通用知识的问题
3. 编程语法或基本概念
4. 用户的个人偏好或主观问题

只回答"YES"或"NO"，不要回答其他内容。
"""

# 研究agent的系统提示
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.

When writing reports, be comprehensive but concise. Include sources and citations where appropriate.
"""

# 创建长期偏好保存的backend
def make_backend(runtime):
    return CompositeBackend(
        default=StateBackend(runtime),       # 短期（瞬时）存储
        routes={
            "/memories/": StoreBackend(runtime)  # 长期存储路径
        }
    )

# DeepSeek模型配置
def get_weather(city: str) -> str:
    """获取给定城市的天气。"""
    writer = get_stream_writer()  # [!code highlight]
    # 流式传输任何任意数据
    writer(f"Looking up data for libA: {city}")
    writer(f"Acquired data for libB: {city}")
    return f"python is a good language"
    
model = ChatOpenAI(
    model="deepseek-reasoner",
    temperature=0,
    openai_api_key=deepseek_api_key,
    base_url="https://api.deepseek.com/v1"
)

# 创建决策agent - 判断是否需要网络搜索
decision_agent = create_deep_agent(
    model=model,
    tools=[],  # 决策agent有工具
    system_prompt=decision_instructions
)
easy_agent = create_deep_agent(
    model=model,
    tools=[get_weather],
    system_prompt="You are a helpful assistant that can answer easy questions and help with tasks. You can use the tools to get the weather of a city."
)


# 创建研究agent - 带长期偏好保存
research_agent = create_deep_agent(
    store=InMemoryStore(),    # 必须提供 store 给 StoreBackend
    backend=make_backend,
    model=model,
    tools=[internet_search],
    system_prompt=research_instructions + """

你是一个助手。当用户告诉你他们的偏好或长期项目内容时，
请将信息保存到 /memories/ 路径下，以便未来对话中复用。
当用户询问你是否记得某些偏好时，请从 /memories/ 路径读取相关信息。
"""
)

# 主函数 - 智能路由
async def handle_query(user_query: str, thread_id: str = None):
    """
    处理用户查询的主函数
    1. 先用决策agent判断是否需要网络搜索
    2. 根据决策结果调用相应agent
    """
    # 决策阶段
    decision_result = decision_agent.invoke({
        "messages": [{"role": "user", "content": f"用户问题：{user_query}\n\n请判断是否需要网络搜索来回答这个问题。只用回答YES或NO，不要回答其他内容。"}]
    })

    decision_response = decision_result["messages"][-1].content.strip().upper()

    print(f"决策结果: {decision_response}")

    # 配置thread_id用于长期记忆
    config = {"configurable": {"thread_id": thread_id or "default"}} if thread_id else {}

    if "YES" in decision_response:
        # 需要网络搜索，使用研究agent
        print("使用研究agent处理...")
        result = research_agent.invoke({
            "messages": [{"role": "user", "content": user_query}]
        }, config=config)
    else:
        # 不需要网络搜索，使用easy_agent直接回答（流式传输）
        print("使用easy_agent处理（流式传输）...")
        full_response = ""
        async for chunk in easy_agent.astream(
            {"messages": [{"role": "user", "content": user_query}]},
            config=config,
            stream_mode="values"
        ):
           if "messages" in chunk:
                print(f"chunk is {chunk } \n")
                s_length = len(chunk["messages"][-1].content)
                for i in range(s_length):
                  yield chunk["messages"][-1].content[i]
                  await asyncio.sleep(0.01)  # 小延迟确保流式体验
                  
# 测试代码
if __name__ == "__main__":
    import uuid

    # 检查环境变量
    if not os.environ.get("TAVILY_API") or not os.environ.get("DEEPSEEK_API"):
        print("错误：请设置环境变量 TAVILY_API 和 DEEPSEEK_API")
        print("您可以创建 .env 文件并设置这些变量：")
        print("TAVILY_API=your_tavily_api_key_here")
        print("DEEPSEEK_API=your_deepseek_api_key_here")
        exit(1)

    print("开始测试智能研究agent...")

    # 测试1: 简单问题（不需要网络搜索）
    print("=== 测试1: 简单问题（不需要网络搜索）===")
    async def test_handle_query():
        async for answer in handle_query("什么是Python编程语言？"):
            print(answer, end="", flush=True)
    asyncio.run(test_handle_query())
    print()
    print("测试完成！")