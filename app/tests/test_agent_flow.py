"""End-to-end conversation flows through the compiled graph.

Uses the temp seeded DB and a mocked LLM (see conftest.py) — no Ollama needed.
"""
import uuid

from sqlalchemy import select

from app.db.models import Lead, VisitBooking

BOOKING_PROMPT = "Which of the top projects would you like to book"


def new_config():
    return {"configurable": {"thread_id": str(uuid.uuid4())}}


async def send(graph, config, text):
    return await graph.ainvoke(
        {"messages": [{"role": "user", "content": text}]}, config=config
    )


async def test_search_reply_lists_projects_without_booking_prompt(compiled_graph):
    result = await send(compiled_graph, new_config(), "I want a 3 bhk in Dubai under 800000")

    reply = result["reply"]
    shortlisted = result["shortlisted_projects"]
    assert shortlisted, "search should shortlist projects"
    assert any(p["project_name"] in reply for p in shortlisted)
    # Regression: search results must not be overwritten by the booking node
    assert BOOKING_PROMPT not in reply


async def test_memory_persists_across_turns_on_same_thread(compiled_graph):
    config = new_config()
    first = await send(compiled_graph, config, "I want a 3 bhk in Dubai under 800000")
    assert first["shortlisted_projects"]

    # Second turn has no budget/city — both must come from the checkpointer
    second = await send(compiled_graph, config, "what amenities does it have?")
    assert second["budget"] == 800000
    assert second["shortlisted_projects"] == first["shortlisted_projects"]


async def test_booking_asks_for_email_before_creating_rows(compiled_graph, test_db):
    config = new_config()
    await send(compiled_graph, config, "I want a 3 bhk in Dubai under 800000")
    result = await send(compiled_graph, config, "I want to book Azure Bay")

    assert result["awaiting_email"] is True
    assert "email" in result["reply"].lower()

    async with test_db() as session:
        bookings = (await session.execute(select(VisitBooking))).scalars().all()
        assert bookings == []


async def test_email_reply_completes_booking(compiled_graph, test_db):
    config = new_config()
    await send(compiled_graph, config, "I want a 3 bhk in Dubai under 800000")
    await send(compiled_graph, config, "I want to book Azure Bay")
    result = await send(compiled_graph, config, "sure, it's buyer@example.com")

    assert "Booking Request Received" in result["reply"]
    assert result["awaiting_email"] is False

    async with test_db() as session:
        lead = (await session.execute(
            select(Lead).where(Lead.email == "buyer@example.com")
        )).scalars().first()
        assert lead is not None
        bookings = (await session.execute(
            select(VisitBooking).where(VisitBooking.lead_id == lead.id)
        )).scalars().all()
        assert len(bookings) == 1


async def test_project_choice_reply_continues_booking(compiled_graph):
    config = new_config()
    await send(compiled_graph, config, "I want a 3 bhk in Dubai under 800000")
    asked = await send(compiled_graph, config, "I'd like to book a site visit")
    assert BOOKING_PROMPT in asked["reply"]

    chosen = await send(compiled_graph, config, "Palm Vista please")
    assert chosen["awaiting_email"] is True
    assert "Palm Vista" in chosen["reply"]


async def test_booking_without_shortlist_is_refused(compiled_graph, test_db):
    result = await send(compiled_graph, new_config(), "I want to book a visit")

    assert "Booking Request Received" not in result["reply"]
    async with test_db() as session:
        bookings = (await session.execute(select(VisitBooking))).scalars().all()
        assert bookings == []
