from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from app.db.models import Lead

import logging

logger = logging.getLogger(__name__)

class LeadService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_lead_by_email(self, email: str):
        """Fetch a lead record by email address."""
        result = await self.db.execute(select(Lead).where(Lead.email == email))
        return result.scalars().first()

    async def create_or_update_lead(self, email: str, preferences: dict, first_name: str = None, last_name: str = None):
        """
        Saves user info. If email exists, update the preferences JSON.
        If not, create a new Lead entry.
        """
        try:
            existing_lead = await self.get_lead_by_email(email)

            if existing_lead:
                logger.info(f"Existing lead found for {email}. Updating preferences.")
                existing_lead.preferences = preferences
                # Optionally update names if provided
                if first_name: existing_lead.first_name = first_name
                if last_name: existing_lead.last_name = last_name
                
                await self.db.commit()
                await self.db.refresh(existing_lead)
                return existing_lead
            else:
                logger.info(f"Creating new lead for {email}.")
                new_lead = Lead(
                    first_name=first_name or "Guest",
                    last_name=last_name or "User",
                    email=email,
                    preferences=preferences
                )
                self.db.add(new_lead)
                await self.db.commit()
                await self.db.refresh(new_lead)
                return new_lead
                
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in LeadService: {e}")
            raise