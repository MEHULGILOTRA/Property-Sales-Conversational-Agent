import asyncio

import requests
from fastapi import APIRouter, Response
from sqlalchemy import text

from app.config import LLM_PROVIDER, LLM_BASE_URL
from app.db.database import AsyncSessionLocal

router = APIRouter()


async def check_db() -> str:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return "ok"
    except Exception as e:
        return f"error: {e}"


def _probe_llm() -> str:
    try:
        if LLM_PROVIDER == "openai":
            url = f"{LLM_BASE_URL.rstrip('/')}/v1/models"
        else:
            url = LLM_BASE_URL  # Ollama root answers "Ollama is running"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        return "ok"
    except Exception:
        return "unreachable"


async def check_llm() -> str:
    return await asyncio.to_thread(_probe_llm)


@router.get("/health")
async def health(response: Response):
    db_status, llm_status = await asyncio.gather(check_db(), check_llm())

    healthy = db_status == "ok"
    # LLM being down is "degraded", not fatal — the agent has deterministic fallbacks
    status = "ok" if healthy and llm_status == "ok" else ("degraded" if healthy else "error")
    if not healthy:
        response.status_code = 503

    return {"status": status, "db": db_status, "llm": llm_status, "llm_provider": LLM_PROVIDER}
