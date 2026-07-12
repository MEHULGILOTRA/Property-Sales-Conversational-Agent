from fastapi import APIRouter, Depends
from app.api.schemas.request import ChatRequest
from app.api.schemas.response import ChatResponse
from app.core.ratelimit import rate_limit
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/agents")

@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(rate_limit)])
async def chat(request: ChatRequest):
    service = ConversationService()
    reply, projects = await service.handle_message(request.conversation_id, request.message)
    return ChatResponse(reply=reply, shortlisted_projects=projects)
