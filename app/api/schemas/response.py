from pydantic import BaseModel
from typing import List, Any

class ChatResponse(BaseModel):
    reply: str
    shortlisted_projects: List[Any]
