from typing import Dict, Any, List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import VisitBooking, Project
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

    async def list_for_lead(self, lead_id: int) -> List[Dict[str, Any]]:
        """All bookings for a lead, with project names for display/matching."""
        result = await self.db_session.execute(
            select(VisitBooking, Project.project_name)
            .join(Project, VisitBooking.project_id == Project.id)
            .where(VisitBooking.lead_id == lead_id)
        )
        return [
            {
                "booking_id": booking.id,
                "project_id": booking.project_id,
                "project_name": project_name,
                "city": booking.city,
                "created_at": str(booking.created_at),
            }
            for booking, project_name in result.all()
        ]

    async def cancel(self, booking_id: int) -> Dict[str, Any]:
        try:
            await self.db_session.execute(
                delete(VisitBooking).where(VisitBooking.id == booking_id)
            )
            await self.db_session.commit()
            logger.info(f"🗑️ VisitBooking {booking_id} cancelled")
            return {"status": "success", "booking_id": booking_id}
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"❌ BookingTool cancel error: {e}")
            return {"status": "error", "message": str(e)}