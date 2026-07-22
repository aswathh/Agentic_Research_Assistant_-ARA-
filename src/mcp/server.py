from datetime import datetime, timezone
from duckduckgo_search import DDGS
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ara_tools")

@mcp.tool()
def web_search(query: str, max_results: int = 3) -> str:
    """Search the web for current information not in the local knowledge base.

    Args:
        query: the search query
        max_results: how many results to return
    """
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    if not results:
        return "No results found."
    return "\n\n".join(f"{r['title']}\n{r['body']}\n{r['href']}" for r in results)

@mcp.tool()
def get_current_time() -> str:
    """Return the current UTC time. Useful for time-sensitive queries."""
    return datetime.now(timezone.utc).isoformat()

if __name__ == "__main__":
    mcp.run(transport="stdio")
