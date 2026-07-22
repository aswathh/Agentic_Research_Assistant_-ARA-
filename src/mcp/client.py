from contextlib import asynccontextmanager
from mcp.client.stdio import stdio_client
from mcp.client import ClientSession, StdioServerParameters
from src.observability.logging_config import get_logger