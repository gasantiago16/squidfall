"""FastAPI entrypoint for the inference service.

Serves the LangGraph agent over the AG-UI protocol so the frontend's
CopilotKit `LangGraphHttpAgent` (pointed at /api/v1) can talk to it.
"""

import asyncio

from fastapi import FastAPI

# Export names churn pre-1.0 — tolerate both observed spellings.
try:
    from ag_ui_langgraph import LangGraphAgent, add_langgraph_fastapi_endpoint
except ImportError:  # pragma: no cover
    from ag_ui_langgraph import add_langgraph_fastapi_endpoint
    from ag_ui_langgraph import LangGraphAGUIAgent as LangGraphAgent

from .agent import build_graph

# Build the compiled agent at import (loads MCP tools — async).
graph = asyncio.run(build_graph())
agent = LangGraphAgent(
    name="squidfall",
    description="Squidfall weather agent",
    graph=graph,
)

app = FastAPI(title="squidfall-inference")
add_langgraph_fastapi_endpoint(app, agent, "/api/v1")


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}
