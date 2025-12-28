from fastmcp import FastMCP
from ddgs import DDGS  
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP(name="MCP tools")

@mcp.tool()
def web_search(query: str) -> List[Dict]:
    '''
    Search the web for the query
    '''
    logging.info(f"Searching the web for the query: {query}")
    ddgs = DDGS()
    results = ddgs.text(query, max_results=3)
    result_list = []
    for result in results:
        result_list.append({
            "title": result["title"][:100],
            "url": result["href"],
            "snippet": result["body"][:400]
        })
    return result_list


@mcp.tool()
def health_check() -> str:
    '''
    Check the health of the server
    '''
    return "Server is healthy"

if __name__ == "__main__":
    mcp.run(transport='http', host="127.0.0.1", port=8003)