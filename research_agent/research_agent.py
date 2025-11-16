from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
load_dotenv()
deepseek_api_key = os.environ["DEEPSEEK_API"]
def get_weather(city: str) -> str:
    """获取给定城市的天气。"""

    return f"It's always sunny in {city}!"
model = ChatOpenAI(
    model="deepseek-reasoner",
    temperature=0,
    openai_api_key=deepseek_api_key,
    base_url="https://api.deepseek.com/v1"
)
agent = create_agent(
    model=model,
    tools=[get_weather],
)
for chunk in agent.stream(  # [!code highlight]
    {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
    stream_mode="updates",
):
    for step, data in chunk.items():
        print(f"step: {step}")
        print(f"content: {data['messages'][-1].content_blocks}")