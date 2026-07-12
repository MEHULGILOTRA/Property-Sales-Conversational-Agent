from datetime import date

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.db.models import Project
from app.db.database import Base

SEED_PROJECTS = [
    dict(project_name="Azure Bay", developer="Silver Land", bedrooms=3, bathrooms=2,
         unit_type="apartment", property_type="apartment", city="Dubai",
         country="United Arab Emirates", price_usd=500000, area_sqm=120,
         completion_status="available", completion_date=date(2024, 6, 1),
         features="pool, balcony", facilities="gym, parking",
         description="Waterfront living with a large pool."),
    dict(project_name="Palm Vista", developer="Silver Land", bedrooms=3, bathrooms=3,
         unit_type="apartment", property_type="apartment", city="Dubai",
         country="United Arab Emirates", price_usd=750000, area_sqm=150,
         completion_status="available", completion_date=date(2025, 1, 1),
         features="gym, sea view", facilities="parking, concierge",
         description="Premium tower with sea view."),
    dict(project_name="Marina Heights", developer="BlueRock", bedrooms=4, bathrooms=4,
         unit_type="apartment", property_type="apartment", city="Dubai",
         country="United Arab Emirates", price_usd=900000, area_sqm=200,
         completion_status="off plan", completion_date=date(2026, 12, 1),
         features="terrace, elevator", facilities="sauna, gym",
         description="Spacious marina-front residences."),
    dict(project_name="Phuket Sands", developer="Island Homes", bedrooms=2, bathrooms=2,
         unit_type="villa", property_type="villa", city="Phuket",
         country="Thailand", price_usd=400000, area_sqm=180,
         completion_status="available", completion_date=date(2024, 3, 1),
         features="beach, garden", facilities="parking",
         description="Beachside villas steps from the sand."),
    dict(project_name="Bangkok Towers", developer="Island Homes", bedrooms=3, bathrooms=2,
         unit_type="apartment", property_type="apartment", city="Bangkok",
         country="Thailand", price_usd=650000, area_sqm=110,
         completion_status="available", completion_date=date(2024, 9, 1),
         features="pool, security", facilities="gym, playground",
         description="Central towers with rooftop pool."),
    dict(project_name="Istanbul Gardens", developer="Bosphorus Dev", bedrooms=2, bathrooms=1,
         unit_type="apartment", property_type="apartment", city="Istanbul",
         country="Turkey", price_usd=300000, area_sqm=95,
         completion_status="available", completion_date=date(2023, 11, 1),
         features="garden, balcony", facilities="parking, security",
         description="Green courtyard apartments."),
]


@pytest.fixture
async def test_db(tmp_path, monkeypatch):
    """Temp SQLite DB seeded with known projects; patches AsyncSessionLocal in
    every module that imported the symbol directly."""
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    engine = create_async_engine(db_url)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        for p in SEED_PROJECTS:
            session.add(Project(**p))
        await session.commit()

    import app.agent.graph as graph_module
    import app.agent.nodes as nodes_module
    monkeypatch.setattr(graph_module, "AsyncSessionLocal", session_factory)
    monkeypatch.setattr(nodes_module, "AsyncSessionLocal", session_factory)

    yield session_factory
    await engine.dispose()


@pytest.fixture
def mock_llm(monkeypatch):
    """Deterministic LLM stub: mentions the two cheapest project names so
    select_top's name-matching shortlist logic gets exercised."""
    def fake_infer(prompt: str, model: str = None) -> str:
        names = [p["project_name"] for p in SEED_PROJECTS]
        mentioned = [n for n in names if n.lower() in prompt.lower()]
        if mentioned:
            return "Based on your criteria I recommend: " + ", ".join(mentioned[:3])
        return "I recommend our best available options."

    import app.agent.nodes as nodes_module
    monkeypatch.setattr(nodes_module, "local_llm_infer", fake_infer)
    return fake_infer


@pytest.fixture
async def compiled_graph(test_db, mock_llm):
    from app.agent.graph import build_graph
    return await build_graph()
