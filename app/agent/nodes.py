import re
from app.agent.state import AgentState
from app.core.logger import setup_logger
from app.services.ollama import local_llm_infer
from app.services.lead_service import LeadService
from app.tools.booking_tool import BookingTool

from thefuzz import fuzz
from app.db.database import AsyncSessionLocal
from app.db.models import VisitBooking, Lead
import logging

logger = setup_logger(__name__)

async def greet_node(state: AgentState) -> AgentState:
    try:

        logger.info("Node : Greet")
        logger.info(f"Messages are : {state['messages']}")
        # Save the user query
        last_message = state['messages'][-1]
        user_query = last_message.content
        state['user_query'] = user_query
        logger.info(f"Saved query: {state['user_query']}") 

        state["reply"] = "Hello! I’m the Silver Land Properties assistant. Please tell me your budget in USD."
        return state
    except Exception as e:
        logger.info(f"Greet node error: {e}")
        return state
        raise


async def extract_budget_node(state: AgentState) -> AgentState:
    try:
        logger.info("Node : Extract Budget Node")
        logger.info(f"Message is  : {state['messages']}")

        #logger.info(f"U Message is  : {type(state['messages'][0][1])}")

        user_message = state['user_query']
        logger.info(f"User Message is  : {user_message}")

        match = re.search(r"\d{6,}", user_message)
        if match:
            state["budget"] = int(match.group())
            logger.info(f"Budget extracted: {state['budget']}")
        else:
            logger.info("No budget found in message")
        return state
    except Exception as e:
        logger.info(f"Extract budget error: {e}")
        return state
        raise

async def not_relevant_node(state: AgentState) -> AgentState:
    try:
        logger.info("NODE : Not Relevant")
        state["reply"] = "Hello user, How can i help you today?"
        return state
    except Exception as e:
        logger.info(f"Relevance error: {e}")
        return state

async def ask_budget_node(state: AgentState) -> AgentState:
    try:
        logger.info("NODE : Ask Budget")
        state["reply"] = "Please enter the budget of the property you want to search in US Dollars (e.g., 500000)."
        return state
    except Exception as e:
        logger.info(f"Ask budget error: {e}")
        return state


async def select_top_projects_node(state):
    logger.info("NODE : Select Top Projects")
    projects = state.get("projects", [])
    # user_query = state["messages"][0]["content"].lower().strip()
    user_query = state['user_query']
    
    
    if not projects:
        return state
        return {"summary": "No projects found matching your criteria."}

    project_list_str = "\n".join([
        f"ID: {i} | {p['project_name']} ({p['city']}) | Price: ${p['price_usd']} | {p['bedrooms']} BHK | Features: {p.get('features', 'N/A')} | Detailed Description : {p.get('description', 'N/A')}"
        for i, p in enumerate(projects)
    ])

    prompt = f"""
    [SYSTEM]
    You are an expert real estate consultant for Silver Land Properties. Your goal is to analyze a list of properties and select the TOP 3 that best match the user's intent.
    
    [USER INTENT]
    "{user_query}"

    [DATASET]
    {project_list_str}

    [INSTRUCTIONS]
    1. Select at most 3 relevant projects from the DATASET. If only 3 or less than 3 are present in the list, provide them with all details.
    2. Start your response with a professional summary explaining why these were chosen (mentioning location, budget, or features).
    3. List the top projects clearly with their key highlights.
    Response:
    """

    # Use your local LLM function
    try:
        logger.info("--- DEBUG: Starting Shortlist Logic ---")
        summary = local_llm_infer(prompt)
        summary_lower = summary.lower()
        logger.info(f"LLM Summary Content (First 100 chars): {summary[:200]}...")
        logger.info(f"Number of projects in state: {len(state.get('projects', []))}")
        top_names = []
        for p in state.get("projects", []):
            p_name = p['project_name']
            # Check if name is in summary (Case-Insensitive)
            if p_name.lower() in summary_lower:
                top_names.append(p_name)
                logger.info(f"✅ MATCH FOUND: '{p_name}' exists in summary.")
            else:
                # Log a few failures to see why they don't match
                logger.debug(f"❌ NO MATCH: '{p_name}' not found in summary.")

        top_names = top_names[:3]
        logger.info(f"Final top_names list: {top_names}")
        shortlisted = [
            p for p in state["projects"] 
            if p['project_name'] in top_names
        ]

        state["shortlisted_projects"] = shortlisted[:3]
        state["summary"] = summary
        state["reply"] = summary

        logger.info(f"Final Count: {len(state['shortlisted_projects'])} projects shortlisted.")
        
        if len(shortlisted) == 0:
            logger.warning("CRITICAL: Shortlisted projects is 0! Check if LLM is using different names than the DB.")

        return state

    except Exception as e:
        logger.error(f"Error in summarize node: {e}")
        return state
        raise

        # --- STEP 2: Filtering the objects ---
        shortlisted = [
            p for p in state["projects"] 
            if p['project_name'] in top_names
        ]
        # logger.info(f"LLM Response for top projects : {summary}")
        # Keep only the chosen 3 in the state
        # (Simple logic: keep projects whose names are mentioned in the summary)

        top_names = [p['project_name'] for p in state["projects"] if p['project_name'] in summary][:3]

        state["shortlisted_projects"] = [
            p for p in state["projects"] 
            if p['project_name'] in top_names
        ]

        logger.info(f"Shortlisted {len(state['shortlisted_projects'])} full project records.")        
        state['reply'] = summary
        logger.info(f"Shorlisted Projects are : {state['shortlisted_projects']}")
        return state
    except Exception as e:
        logger.error(f"Selection node error: {e}")
        return state


async def summarize_projects_node(state):
    try:
        logger.info("NODE : Summarize all projects")
        #logger.info(f"Top Projects are : {state['shortlisted_projects']}")
        shortlisted = state.get("shortlisted_projects", [])
        if not shortlisted:
            msg = "No properties found."
            state['reply'] = msg
            return state

        # Pass ALL details for these 3
        detailed_input = ""
        for p in shortlisted:
            detailed_input += f"""
            NAME: {p['project_name']}
            PRICE: ${p['price_usd']:,}
            FEATURES: {p['features']}
            FACILITIES: {p['facilities']}
            DESCRIPTION: {p['description']}
            DEVELOPER: {p['developer']}
            -------------------
            """

        prompt = f"""
        [SYSTEM] You are a luxury real estate consultant.
        Write a detailed, 2-paragraph analysis for each of the following 3 properties. 
        Highlight how the features and facilities justify the price point.
        
        [DATA]
        {detailed_input}
        """

        #full_summary = local_llm_infer(prompt)
        full_summary = ""
        state["summary"] =  full_summary
        return state
    
    except Exception as e:
            logger.error(f"CRITICAL FAILURE in summarize_projects_node: {str(e)}")
            state["summary"] = "An internal error occurred while generating the summary."
        
            return state


async def project_qa_node(state: AgentState):
    logger.info("NODE : Project QA Node")

    projects = state.get("shortlisted_projects", [])
    query = state.get("user_query", "")

    context = "\n\n".join([
        f"Project: {p['project_name']}\nDescription: {p['description']}\nAmenities: {p.get('amenities', 'N/A')}\nCompletion: {p.get('completion_date', 'N/A')}"
        for p in projects
    ])

    prompt = f"""
    Answer the user question using ONLY the project data below. 
    If the answer isn't there, say you don't have that specific detail.
    
    Data:
    {context}
    
    Question: {query}
    """
    
    response = local_llm_infer(prompt)
    state["reply"] = response
    return state

async def present_projects_node(state: AgentState) -> AgentState:
    
    try:
        logger.info("Node : Present Projects")
        # shortlisted = state.get("shortlisted_projects", [])
        # final_summary = state.get("summary", "")
        reply = ""
        return state
    
    except Exception as e:
        logger.info(f"Present projects error: {e}")
        return state
        raise

async def book_project_node(state: AgentState):
    logger.info("NODE : Book Project Node")

    user_query = state.get("user_query")
    shortlisted = state.get("shortlisted_projects", [])

    chosen_project = None
    best_match_score = 0
    threshold = 60


    for p in shortlisted:
        name = p['project_name'].lower()
        score = fuzz.partial_ratio(user_query, name)
        
        if score > best_match_score:
            best_match_score = score
            chosen_project = p

    logger.info(f"Fuzzy match score: {best_match_score}% for project: {chosen_project['project_name'] if chosen_project else 'None'}")

    res = ""
    if not chosen_project or best_match_score < threshold:
        for p in shortlisted:
            name = p['project_name'].lower()
            res = res + "\n" + name
        res = res + "\nWhich of the top projects would you like to book? Please let me know the name."
        state["reply"] = res
        return state
    try:
        async with AsyncSessionLocal() as session:
                lead_service = LeadService(session)
                lead = await lead_service.create_or_update_lead(
                    email=state.get("user_email", "guest@example.com"),
                    preferences={"city": state.get("city"), "budget": state.get("budget")}
                )
                logger.info("Added Lead")
                booking_tool = BookingTool(session)
                booking_result = await booking_tool.run({
                    "lead_id": lead.id,
                    "project_id": chosen_project['id'],
                    "city": chosen_project.get('city', state.get('city'))
                })

                if booking_result["status"] == "success":
                    logger.info("Booking is saved!!")
                    broker_info = {
                        "name": "Mehul Gilotra",
                        "phone": "+11-111-1111",
                        "email": "mehul.gilotra@silverland.com"
                    }
                    msg = (f"✅ Booking Request Received for **{chosen_project['project_name']}**!\n\n"
                        f"👤 **Your Broker:** {broker_info['name']}\n"
                        f"📞 **Contact:** {broker_info['phone']}\n"
                        f"📧 Confirmation ID: {booking_result['booking_id']}. Site visit scheduled.")
                    state["reply"] = msg
                    state["selected_project_name"] = chosen_project['project_name']
                else:
                    state["reply"] = "I had trouble saving your booking. Please try again."

    except Exception as e:
        logger.error(f"Error in book_project_node: {e}")
        state["reply"] = "Something went wrong with the booking system."

    return state