from sqlalchemy import select

from app.db.models import Lead
from app.services.lead_service import LeadService


async def test_create_lead(test_db):
    async with test_db() as session:
        service = LeadService(session)
        lead = await service.create_or_update_lead(
            email="new.user@example.com",
            preferences={"city": "Dubai", "budget": 800000},
            first_name="Test",
            last_name="User",
        )
        assert lead.id is not None
        assert lead.email == "new.user@example.com"
        assert lead.preferences == {"city": "Dubai", "budget": 800000}


async def test_update_existing_lead_by_email(test_db):
    async with test_db() as session:
        service = LeadService(session)
        first = await service.create_or_update_lead(
            email="repeat@example.com", preferences={"city": "Dubai"}
        )
        second = await service.create_or_update_lead(
            email="repeat@example.com", preferences={"city": "Phuket"}
        )
        assert second.id == first.id
        assert second.preferences == {"city": "Phuket"}

        result = await session.execute(select(Lead).where(Lead.email == "repeat@example.com"))
        assert len(result.scalars().all()) == 1
