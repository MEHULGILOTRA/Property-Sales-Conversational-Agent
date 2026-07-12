import time
import uuid

from fastapi import FastAPI, Request

from app.api.routes.conversations import router as conversation_router
from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.core.logger import setup_logger, request_id_var

logger = setup_logger(__name__)

app = FastAPI(title="Property Sales Conversational Agent")


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
    token = request_id_var.set(request_id)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(f"{request.method} {request.url.path} took {duration_ms:.0f}ms")
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(conversation_router)
app.include_router(chat_router)
app.include_router(health_router)

# RUN LIKE THIS -
# uvicorn app.main:app --reload
