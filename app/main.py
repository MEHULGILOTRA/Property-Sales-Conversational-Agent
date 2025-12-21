from fastapi import FastAPI
from app.api.routes.conversations import router as conversation_router
from app.api.routes.chat import router as chat_router
from app.core.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI()

app.include_router(conversation_router)
app.include_router(chat_router)

# RUN LIKE THIS - 
# uvicorn app.main:app --reload
