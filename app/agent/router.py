from app.agent.state import AgentState
from app.core.logger import setup_logger
import re

logger = setup_logger(__name__)

keywords = [
    "Hello",
    "Hi",
    "Hey",
    "What can you do?",
    "hello",
    "hey",
    "hi"
]

def router(state: AgentState) -> str:
    try:
        logger.info("Router invoked")
        query = state.get("user_query", "").lower()
        shortlisted = state.get("shortlisted_projects", [])
        booking_keywords = ["book", "visit", "schedule", "interested", "buy"]
        


        if any(word in query for word in keywords):
            logger.info("Query identified as not relevant.")
            return "not_relevant"
        
        match = re.search(r"\d{6,}", query)
        if match:
            return "extract_budget"


        if any(word in query for word in booking_keywords):
            if state.get("shortlisted_projects"):
                return "book_project"
            else:
                return "not_relevant"
            
        qa_keywords = ["amenities", "completion", "finish", "facilities", "parking", "pool", "description", "details"]
        if any(word in query for word in qa_keywords):
            if len(shortlisted) > 0:
                logger.info("Routing to Project QA (Projects found in state)")
                return "project_qa"
            else:
                logger.info("User asked about amenities but no projects found. Re-routing to greet/search.")
                return "not_relevant"
            
        if not state.get("budget"):
            logger.info("Budget missing. Routing to Ask Budget.")
            return "ask_budget"
        

        logger.info("Routing to sql_search")
        return "sql_search"
    
    except Exception as e:
        logger.info(f"Router error: {e}")
        raise
