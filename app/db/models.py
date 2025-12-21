from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    JSON,
    ForeignKey,
    DateTime
)
from sqlalchemy.sql import func
from app.db.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    project_name = Column(String, index=True)
    developer = Column(String)

    bedrooms = Column(Integer)
    bathrooms = Column(Integer)

    unit_type = Column(String)
    property_type = Column(String)

    city = Column(String, index=True)
    country = Column(String)

    price_usd = Column(Integer)
    area_sqm = Column(Integer)

    completion_status = Column(String)
    completion_date = Column(Date)

    features = Column(Text)
    facilities = Column(Text)
    description = Column(Text)


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, index=True)

    preferences = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VisitBooking(Base):
    __tablename__ = "visit_bookings"

    id = Column(Integer, primary_key=True, index=True)

    lead_id = Column(Integer, ForeignKey("leads.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))

    city = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
