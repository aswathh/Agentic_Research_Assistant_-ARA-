from contextlib import asynccontextmanager
from mcp.client.stdio import stdio_client
from mcp.client import ClientSession, StdioServerParameters
from src.observability.logging_config import get_logger

logger = get_logger(__name__)

_server_params=StdioServerParameters(
    command="python",
    args=["-m", "src.mcp.server"],
)

@asynccontextmanager

async def mcp_session():
    """Open an MCP client session against our local tool server.
    Usage: async with mcp_session() as session: ...
    """
    async with stdio_client(_server_params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            yield session

async def list_of_tools():
    async with mcp_session() as session:
        tools = await session.list_tools()
        return [t.name for t in tools.tools]

async def call_tools(name:str,arguments:dict):
    async with mcp_session() as session:
        result = await session.call_tool(name,argument)
        logger.info("mcp_tool_called", tool=name, args=arguments)
        return "".join(block.text for block in result.content if hasattr(block,"text"))
