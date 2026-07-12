import time

from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import (
    greet_node,
    extract_budget_node,
    ask_budget_node,
    not_relevant_node,
    present_projects_node,
    select_top_projects_node,
    summarize_projects_node,
    project_qa_node,
    book_project_node
)
from app.agent.router import router
from app.tools.sql_tool import SQLSearchTool
from app.db.database import AsyncSessionLocal
from app.core.logger import setup_logger
from langgraph.checkpoint.memory import MemorySaver

logger = setup_logger(__name__)

async def sql_search_node(state: AgentState):
    """Proper async node that manages its own DB session lifecycle"""
    async with AsyncSessionLocal() as db:
        sql_tool = SQLSearchTool(db)
        return await sql_tool.run(state)


def timed(name, node_fn):
    """Wrap a node so its execution time lands in the logs as a metric."""
    async def wrapper(state):
        start = time.perf_counter()
        try:
            return await node_fn(state)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(f"metric node={name} duration_ms={duration_ms:.0f}")
    return wrapper

async def build_graph():
    try:
        memory = MemorySaver()
        logger.info("Building LangGraph")

        graph = StateGraph(AgentState)

        nodes = {
            "greet": greet_node,
            "extract_budget": extract_budget_node,
            "ask_budget": ask_budget_node,
            "not_relevant": not_relevant_node,
            "project_qa": project_qa_node,
            "sql_search": sql_search_node,
            "select_top": select_top_projects_node,
            "summarize_projects": summarize_projects_node,
            "present": present_projects_node,
            "book_project": book_project_node,
        }
        for name, fn in nodes.items():
            graph.add_node(name, timed(name, fn))

        graph.set_entry_point("greet")

        graph.add_conditional_edges(
            "greet",
            router,
            {
                "ask_budget": "ask_budget",
                "extract_budget": "extract_budget",
                "not_relevant": "not_relevant",
                "project_qa": "project_qa",
                "book_project": "book_project",
                "sql_search": "sql_search",
            }
        )
        graph.add_edge("extract_budget", "sql_search")

        graph.add_edge("ask_budget", END)
        graph.add_edge("not_relevant", END)
        graph.add_edge("project_qa", END)

        # Search results end at "present" — booking is only reached through
        # the router when the user actually expresses booking intent.
        graph.add_edge("sql_search", "select_top")
        graph.add_edge("select_top", "summarize_projects")
        graph.add_edge("summarize_projects", "present")
        graph.add_edge("present", END)
        graph.add_edge("book_project", END)

        app = graph.compile(checkpointer=memory)
        logger.info("LangGraph compiled successfully")
        return app
    except Exception as e:
        logger.error(f"Graph build error: {e}")
        raise
