"""Builds the Squidfall LangGraph agent.

The LLM is provider-agnostic: the agent calls build_llm() (see llm.py), which
selects Ollama / OpenAI-compatible / Azure OpenAI from LLM_PROVIDER. MCP tools
are loaded from TOOLS_ENDPOINT and wired into a ReAct agent.
"""

import asyncio
from os import getenv

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

try:
    from langgraph.checkpoint.memory import InMemorySaver
except ImportError:  # older langgraph
    from langgraph.checkpoint.memory import MemorySaver as InMemorySaver

from .llm import build_llm

TOOLS_ENDPOINT = getenv("TOOLS_ENDPOINT", "http://squidfall-tools:8002/mcp")

mcp_client = MultiServerMCPClient(
    {
        "tools": {
            "transport": "streamable_http",
            "url": TOOLS_ENDPOINT,
        }
    }
)

SYSTEM_PROMPT = (
    "You are Squidfall, a helpful weather assistant. To answer weather "
    "questions, first call get_coordinates to turn a place name into latitude "
    "and longitude, then call get_forecast with those coordinates. Always use "
    "the tools instead of guessing the weather."
)


async def _load_tools(retries: int = 15, delay: float = 2.0):
    """Load MCP tools, retrying while the tools container finishes starting."""
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return await mcp_client.get_tools()
        except Exception as error:  # tools server may not be ready yet
            last_error = error
            print(f"[squidfall] MCP not ready ({attempt}/{retries}): {error}", flush=True)
            await asyncio.sleep(delay)
    raise RuntimeError(f"Could not load MCP tools from {TOOLS_ENDPOINT}: {last_error}")


async def build_graph():
    """Build and return a compiled LangGraph ReAct agent."""
    llm = build_llm()
    tools = await _load_tools()
    # The AG-UI adapter calls graph.aget_state() each run, which needs a
    # checkpointer; without one it raises "No checkpointer set".
    return create_react_agent(
        llm, tools, prompt=SYSTEM_PROMPT, checkpointer=InMemorySaver()
    )
