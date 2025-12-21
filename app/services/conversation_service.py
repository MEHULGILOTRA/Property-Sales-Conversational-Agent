from app.agent.graph import build_graph
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class ConversationService:
    def __init__(self):
        self.graph = None

    async def handle_message(self, conversation_id, message):
        if self.graph is None:
            self.graph = await build_graph()
        

        state = {
            "conversation_id": conversation_id,
            "messages": [{"role": "user", "content": message}],
            "budget": None,
            "shortlisted_projects": []
        }
        result = await self.graph.ainvoke(state)
        return result["messages"][-1]["content"], result["shortlisted_projects"]
