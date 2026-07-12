"""Phase 3 flows: budget correction, multi-project booking, cancellation."""
import uuid

from sqlalchemy import select

from app.db.models import VisitBooking


def new_config():
    return {"configurable": {"thread_id": str(uuid.uuid4())}}


async def send(graph, config, text):
    return await graph.ainvoke(
        {"messages": [{"role": "user", "content": text}]}, config=config
    )


async def test_budget_correction_replaces_old_value(compiled_graph):
    config = new_config()
    first = await send(compiled_graph, config, "I want a 3 bhk in Dubai under 800000")
    assert first["budget"] == 800000
    assert any(p["project_name"] == "Palm Vista" for p in first["shortlisted_projects"])

    second = await send(compiled_graph, config, "actually my budget is 600k")
    assert second["budget"] == 600000
    # Palm Vista (750k) exceeds 600k * 1.3 — must drop out after the correction
    assert all(p["price_usd"] <= 600000 * 1.3 for p in second["shortlisted_projects"])


async def test_multi_project_booking_in_one_message(compiled_graph, test_db):
    config = new_config()
    await send(compiled_graph, config, "I want a 3 bhk in Dubai under 800000")
    asked = await send(compiled_graph, config, "book Azure Bay and Palm Vista")
    assert asked["awaiting_email"] is True
    assert set(asked["pending_project_names"]) == {"Azure Bay", "Palm Vista"}

    done = await send(compiled_graph, config, "multi@example.com")
    assert "Azure Bay" in done["reply"] and "Palm Vista" in done["reply"]

    async with test_db() as session:
        bookings = (await session.execute(select(VisitBooking))).scalars().all()
        assert len(bookings) == 2


async def _book(graph, config, project="Azure Bay", email="canceller@example.com"):
    await send(graph, config, "I want a 3 bhk in Dubai under 800000")
    await send(graph, config, f"book {project}")
    return await send(graph, config, email)


async def test_cancel_booking_by_name(compiled_graph, test_db):
    config = new_config()
    booked = await _book(compiled_graph, config)
    assert "Booking Request Received" in booked["reply"]

    result = await send(compiled_graph, config, "please cancel my visit to Azure Bay")
    assert "cancelled" in result["reply"]

    async with test_db() as session:
        bookings = (await session.execute(select(VisitBooking))).scalars().all()
        assert bookings == []


async def test_cancel_single_booking_without_naming_it(compiled_graph, test_db):
    config = new_config()
    await _book(compiled_graph, config)

    result = await send(compiled_graph, config, "I need to cancel my booking")
    assert "cancelled" in result["reply"]

    async with test_db() as session:
        bookings = (await session.execute(select(VisitBooking))).scalars().all()
        assert bookings == []


async def test_cancel_without_email_asks_for_it(compiled_graph, test_db):
    # Fresh thread: agent knows nothing about this user
    config = new_config()
    asked = await send(compiled_graph, config, "cancel my site visit")
    assert asked["awaiting_email"] is True
    assert "email" in asked["reply"].lower()

    result = await send(compiled_graph, config, "unknown@example.com")
    assert "couldn't find any" in result["reply"]


async def test_cancel_with_multiple_bookings_asks_which(compiled_graph, test_db):
    config = new_config()
    await send(compiled_graph, config, "I want a 3 bhk in Dubai under 800000")
    await send(compiled_graph, config, "book Azure Bay and Palm Vista")
    await send(compiled_graph, config, "both@example.com")

    asked = await send(compiled_graph, config, "cancel one of my bookings")
    assert "Which one" in asked["reply"]

    result = await send(compiled_graph, config, "Palm Vista")
    assert "Palm Vista" in result["reply"] and "cancelled" in result["reply"]

    async with test_db() as session:
        remaining = (await session.execute(select(VisitBooking))).scalars().all()
        assert len(remaining) == 1
