from dataclasses import dataclass
from typing import Any
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langgraph.store.memory import InMemoryStore

model = ChatOpenAI(
    model="deepseek-chat",
    base_url= "https://api.deepseek.com",  # 自定义 API 地址
    api_key="sk-27d9b691c01e4ec4861b461c928d713c"                      # 自定义 API 密钥
)






@tool
def get_user_info(user_id: str, runtime:ToolRuntime) -> str:
    """ Look up user info"""
    store = runtime.store
    user_info = store.get(("users",), user_id)
    return str(user_info.value) if user_info else "User not found"



@tool
def save_user_info(user_id: str, user_info: dict[str, Any], runtime: ToolRuntime) -> str:
    """ Save user info"""
    store = runtime.store
    store.set(("users",), user_id, user_info)
    return "User info saved"



store = InMemoryStore()

agent = create_agent(
    model,
    tools=[get_user_info, save_user_info],
    store=store,
)