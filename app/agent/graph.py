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

async def build_graph():
    try:
        memory = MemorySaver()
        logger.info("Building LangGraph")

        async with AsyncSessionLocal() as db:
            sql_tool = SQLSearchTool(db)

            graph = StateGraph(AgentState)

            graph.add_node("greet", greet_node)
            graph.add_node("extract_budget", extract_budget_node)
            graph.add_node("ask_budget", ask_budget_node)
            graph.add_node("not_relevant", not_relevant_node)
            graph.add_node("project_qa", project_qa_node)
            graph.add_node("sql_search", sql_search_node)
            graph.add_node("select_top", select_top_projects_node)
            graph.add_node("summarize_projects", summarize_projects_node)
            graph.add_node("present", present_projects_node)
            graph.add_node("book_project", book_project_node)

            graph.set_entry_point("greet")

            #graph.add_edge("greet", "extract_budget")
            graph.add_conditional_edges("greet", 
                router, 
                {
                "ask_budget": "ask_budget",
                "extract_budget" : "extract_budget",
                "not_relevant": "not_relevant",
                "project_qa" : "project_qa",
                "book_project" : "book_project"
            }
            )
            graph.add_edge("extract_budget", "sql_search")

            graph.add_edge("ask_budget", END)
            graph.add_edge("not_relevant", END)
            graph.add_edge("project_qa", END)

            graph.add_edge("sql_search", "select_top")
            graph.add_edge("select_top", "summarize_projects")
            graph.add_edge("summarize_projects", "present")
            graph.add_edge("present", "book_project")
            graph.add_edge("book_project", END)


            logger.info("LangGraph compiled successfully")
            app = graph.compile(checkpointer=memory)
            return app
    except Exception as e:
        logger.error(f"Graph build error: {e}")
        raise
