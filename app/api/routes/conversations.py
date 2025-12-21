from fastapi import APIRouter
import uuid

router = APIRouter(prefix="/conversations")

@router.post("")
def create_conversation():
    return {"conversation_id": str(uuid.uuid4())}
