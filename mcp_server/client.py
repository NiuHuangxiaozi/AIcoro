from fastmcp.client.transports import FastMCPTransport


import asyncio
from fastmcp import Client, FastMCP

# HTTP 服务器
client = Client("http://localhost:8003/mcp")
async def main():
    async with client:
        # 基本服务器交互
        await client.ping()
        
        # 列出可用操作
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()
        
        for tool in tools:
            print(tool.name)
            print(tool.description)
            print(tool.inputSchema)
            print(tool.outputSchema)
asyncio.run(main())