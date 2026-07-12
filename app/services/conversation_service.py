import asyncio

from app.agent.graph import build_graph
from app.core.logger import setup_logger

logger = setup_logger(__name__)

# One compiled graph (and one MemorySaver) for the whole process — per-request
# rebuilds would discard the checkpointer and with it all conversation memory.
_graph = None
_graph_lock = asyncio.Lock()


async def get_graph():
    global _graph
    if _graph is None:
        async with _graph_lock:
            if _graph is None:
                _graph = await build_graph()
    return _graph


class ConversationService:
    async def handle_message(self, conversation_id: str, message: str):
        graph = await get_graph()

        # Input carries ONLY the new message; everything else (budget, city,
        # shortlist, email flags) is restored by the checkpointer for this thread.
        config = {"configurable": {"thread_id": conversation_id}}
        result = await graph.ainvoke(
            {"messages": [{"role": "user", "content": message}]},
            config=config,
        )
        reply = result.get("reply", "Sorry, I couldn't generate a response.")
        return reply, result.get("shortlisted_projects", [])
