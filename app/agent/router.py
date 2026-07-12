from app.agent.state import AgentState
from app.core.logger import setup_logger
import re

logger = setup_logger(__name__)

greeting_keywords = ["hello", "hi", "hey"]

def router(state: AgentState) -> str:
    try:
        logger.info("Router invoked")
        query = state.get("user_query", "").lower()
        shortlisted = state.get("shortlisted_projects", [])
        booking_keywords = ["book", "visit", "schedule", "interested", "buy"]

        # Mid-booking: the user was asked for their email — route the reply back.
        if state.get("awaiting_email"):
            logger.info("Awaiting email — routing back to booking.")
            return "book_project"

        query_words = re.findall(r"[a-z]+", query)
        if any(word in query_words for word in greeting_keywords) or "what can you do" in query:
            logger.info("Query identified as greeting / not relevant.")
            return "not_relevant"

        match = re.search(r"\d{6,}", query)
        if match:
            return "extract_budget"

        # Mid-booking: the user was asked which project to book — a plain
        # project-name reply (no new budget/greeting) continues the booking.
        if state.get("awaiting_project_choice") and shortlisted:
            logger.info("Awaiting project choice — routing back to booking.")
            return "book_project"


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
