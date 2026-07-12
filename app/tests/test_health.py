import httpx

from app.api.routes import health as health_module
from app.main import app


def make_client():
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def test_health_reports_component_status(monkeypatch):
    monkeypatch.setattr(health_module, "_probe_llm", lambda: "ok")
    async with make_client() as client:
        res = await client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["llm"] == "ok"


async def test_health_degraded_when_llm_unreachable(monkeypatch):
    monkeypatch.setattr(health_module, "_probe_llm", lambda: "unreachable")
    async with make_client() as client:
        res = await client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "degraded"
    assert body["db"] == "ok"


async def test_responses_carry_request_id_header():
    async with make_client() as client:
        res = await client.get("/health")
    assert res.headers.get("X-Request-ID")


async def test_client_supplied_request_id_is_echoed():
    async with make_client() as client:
        res = await client.get("/health", headers={"X-Request-ID": "trace-me-123"})
    assert res.headers["X-Request-ID"] == "trace-me-123"
