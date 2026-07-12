import httpx
import pytest

from app.core import ratelimit
from app.main import app
from app.services.conversation_service import ConversationService


@pytest.fixture
def small_limit(monkeypatch):
    limiter = ratelimit.RateLimiter(max_requests=3, window_seconds=60)
    monkeypatch.setattr(ratelimit, "rate_limiter", limiter)

    async def fake_handle(self, conversation_id, message):
        return "ok", []

    monkeypatch.setattr(ConversationService, "handle_message", fake_handle)
    return limiter


async def test_requests_over_limit_get_429(small_limit):
    transport = httpx.ASGITransport(app=app)
    payload = {"conversation_id": "t1", "message": "hi"}
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(3):
            res = await client.post("/agents/chat", json=payload)
            assert res.status_code == 200
        res = await client.post("/agents/chat", json=payload)
        assert res.status_code == 429
