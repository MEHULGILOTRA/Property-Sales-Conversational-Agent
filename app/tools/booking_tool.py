from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import VisitBooking
import logging

logger = logging.getLogger(__name__)

class BookingTool:
    """
    Persists confirmed visit bookings.
    """
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def run(self, booking_data: Dict[str, Any]):
        """
        Expects: {"lead_id": int, "project_id": int, "city": str}
        """
        try:
            new_booking = VisitBooking(
                lead_id=booking_data.get("lead_id"),
                project_id=booking_data.get("project_id"),
                city=booking_data.get("city")
            )
            self.db_session.add(new_booking)
            await self.db_session.commit()
            await self.db_session.refresh(new_booking)
            
            logger.info(f"✅ VisitBooking created with ID: {new_booking.id}")
            return {
                "status": "success",
                "booking_id": new_booking.id
            }
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"❌ BookingTool Error: {e}")
            return {"status": "error", "message": str(e)}