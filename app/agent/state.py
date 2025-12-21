from typing import TypedDict, List, Optional, Dict, Annotated, Any
from langgraph.graph.message import add_messages

def merge_info(current: Any, new: Any) -> Any:
    """
    If the new node output provides a value, use it. 
    Otherwise, keep the existing value from memory.
    """
    if new is not None:
        return new
    return current

class Preferences(TypedDict, total=False):
    city: str
    budget_min: int
    budget_max: int
    bedrooms: int
    property_type: str

class LeadInfo(TypedDict, total=False):
    first_name: str
    last_name: str
    email: str

class AgentState(TypedDict):

    conversation_id: str
    messages: Annotated[list, add_messages]
    user_query : str

    preferences: Preferences
    shortlisted_projects: List[int]
    confirmed_project_id: Optional[int]
    lead: LeadInfo
    features : List
    budget: Annotated[Optional[int], merge_info]
    city: Annotated[Optional[str], merge_info]
    bhk: Annotated[Optional[int], merge_info]

    projects: List[Dict]
    response : str
    summary : str
    reply : str
    selected_project: Optional[str]
    user_contact: Optional[str]
    booking_confirmed: bool = False
    selected_project_name: Optional[str]