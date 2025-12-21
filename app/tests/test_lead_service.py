import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.models import Lead, Base 
from app.services.lead_service import LeadService

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'property_sales.db')}"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def test_run():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        service = LeadService(session)
        
        test_email = "test_user@example.com"
        test_prefs = {"city": "Dubai", "bhk": 3}
        
        print(f"\n--- Testing Create Lead ---")
        lead = await service.create_or_update_lead(
            email=test_email, 
            preferences=test_prefs,
            first_name="Test",
            last_name="Subject"
        )

        print(f"Result: Created/Retrieved Lead ID {lead.id} for {lead.email}")

        print(f"\n--- Testing Update Lead ---")
        updated_prefs = {"city": "Phuket", "bhk": 5}
        updated_lead = await service.create_or_update_lead(
            email=test_email,
            preferences=updated_prefs
        )
        print(f"Result: Updated Preferences to {updated_lead.preferences}")
    
    await engine.dispose()

if __name__ == "__main__":
    try:
        asyncio.run(test_run())
    except Exception as e:
        print(f"❌ Test Failed: {e}")