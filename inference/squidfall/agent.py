"""Builds the Squidfall LangGraph agent.

Default LLM is a LOCAL Ollama model (Qwen) reached over Ollama's NATIVE API
(not the OpenAI-compatible /v1 path, which has an open bug where tool calls +
streaming break). Set USE_AZURE=true to use Azure OpenAI instead.
"""

import asyncio
from os import getenv

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

try:
    from langgraph.checkpoint.memory import InMemorySaver
except ImportError:  # older langgraph
    from langgraph.checkpoint.memory import MemorySaver as InMemorySaver

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


def _build_llm():
    if getenv("USE_AZURE", "false").lower() == "true":
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(
            azure_endpoint=getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_version=getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            azure_deployment=getenv("AZURE_OPENAI_DEPLOYMENT", "squidfall"),
            temperature=0,
        )

    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=getenv("OLLAMA_MODEL", "qwen2.5"),
        base_url=getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
        temperature=0,
        num_ctx=int(getenv("OLLAMA_NUM_CTX", "8192")),
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
    llm = _build_llm()
    tools = await _load_tools()
    # The AG-UI adapter calls graph.aget_state() each run, which needs a
    # checkpointer; without one it raises "No checkpointer set".
    return create_react_agent(
        llm, tools, prompt=SYSTEM_PROMPT, checkpointer=InMemorySaver()
    )
