import os
from pptagent.llms import AsyncLLM
import asyncio

from pydantic import BaseModel

class Answer(BaseModel):
    city: str
    country: str
    description: str



async def main():
    vlm = AsyncLLM(
        model="qwen3-omni-flash",
        base_url=os.getenv("API_BASE"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    state= await vlm.test_connection()
    print(f"test connection state: {state}")
    answer = await vlm(
        content="where is the great wall of china?",
        response_format=Answer,
    )
    print(type(answer))
    print(answer)

    answer = await vlm(
        content="where is the great wall of china?",
        response_format=Answer,
        return_json=True,
    )

    print(type(answer))
    print(answer)




if __name__ == "__main__":
    asyncio.run(main())