import csv
from datetime import datetime
from app.db.database import engine, Base
from app.db.models import Project, Lead, VisitBooking
from app.core.logger import setup_logger
import asyncio
import aiofiles
from aiocsv import AsyncDictReader

from app.db.database import engine, AsyncSessionLocal, Base
from app.db.models import Project

logger = setup_logger(__name__)

CSV_PATH = "/Users/mehulgilotra/Desktop/Projects/Property Sales Agent/data/Challenge.csv"

async def main():
    try:
        await seed_projects()
    finally:
        await engine.dispose()
        print("🔌 Database connections closed.")

def parse_date(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None

def safe_int(value):
    """Converts value to int, handles empty strings, commas, and decimals."""
    if value is None or str(value).strip() == "":
        return 0
    try:
        # Remove commas and handle decimal strings like "1500.0"
        clean_val = str(value).replace(",", "").split('.')[0]
        return int(clean_val)
    except (ValueError, TypeError):
        return 0
    
async def seed_projects():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    mapping = {
        "project_name": "Project name",
        "bedrooms": "No of bedrooms",
        "bathrooms": "bathrooms",
        "unit_type": "unit type",
        "developer": "developer name",
        "price_usd": "Price (USD)",
        "area_sqm": "Area (sq mtrs)",
        "property_type": "Property type (apartment/villa)",
        "city": "city",
        "country": "country",
        "completion_status": "Completion status (off plan/available)",
        "completion_date": "completion_date",
        "features": "features",
        "facilities": "facilities",
        "description": "Project description",
    }

    async with AsyncSessionLocal() as db:
        try:
            async with aiofiles.open(CSV_PATH, mode="r", encoding="utf-8", newline="") as f:
                async for row in AsyncDictReader(f):
                    project_data = {}
                    
                    for attr, col_name in mapping.items():
                        val = row.get(col_name)
                        
                        if attr in ["bedrooms", "bathrooms", "price_usd", "area_sqm"]:
                            project_data[attr] = safe_int(val)
                        elif attr == "completion_date":
                            project_data[attr] = parse_date(val)
                        else:
                            project_data[attr] = val

                    project = Project(**project_data)
                    db.add(project)

            await db.commit()
            print("✅ Projects table seeded successfully!")

        except Exception as e:
            await db.rollback()
            print(f"❌ Error during seeding: {e}")
        finally:
            db.close()


if __name__ == "__main__":
    print("🚀 Starting database seeding...")
    asyncio.run(main())