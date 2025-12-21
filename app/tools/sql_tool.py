from typing import Dict, Any, List
from app.tools.base import BaseTool
from app.db.models import Project
from app.core.logger import setup_logger
import re
from sqlalchemy import select, or_, and_
logger = setup_logger(__name__)

COUNTRY_MAPPING = {
    "US": "United States", "SG": "Singapore", "TC": "Turks and Caicos",
    "CO": "Colombia", "AE": "United Arab Emirates", "TR": "Turkey",
    "MX": "Mexico", "TH": "Thailand", "EG": "Egypt", "GR": "Greece",
    "GB": "United Kingdom", "MV": "Maldives", "CA": "Canada",
    "ES": "Spain", "VN": "Vietnam", "ID": "Indonesia", "OM": "Oman",
    "SA": "Saudi Arabia", "QA": "Qatar", "PH": "Philippines",
    "MY": "Malaysia", "AT": "Austria", "CH": "Switzerland"
}

KEY_FEATURES_LIST = [
    "pool", "gym", "parking", "garden", "balcony", "security", 
    "sea view", "beach", "terrace", "elevator", "furnished",
    "sauna", "playground", "garage", "concierge"
]

class SQLSearchTool(BaseTool):
    def __init__(self, db):
        self.db = db

    async def run(self, state):
        try:
            logger.info("SQL search tool invoked")
            #user_query = state["messages"][0]["content"].lower().strip()
            user_query = state['user_query']

            budget = state.get("budget")
            if not budget:
                logger.info("Budget missing in SQL tool")
                state["projects"] = []
                return state
            
            city_stmt = select(Project.city).distinct()
            city_result = await self.db.execute(city_stmt)
            unique_cities = [c for c in city_result.scalars().all() if c]
            #logger.info(f"Unique Cities : {unique_cities}")
            country_res = await self.db.execute(select(Project.country).distinct())
            unique_countries_in_db = [c for c in country_res.scalars().all() if c]


            bhk_stmt = select(Project.bedrooms).distinct()
            bhk_result = await self.db.execute(bhk_stmt)
            unique_bhks = [b for b in bhk_result.scalars().all() if b is not None]

            matched_cities = [city for city in unique_cities if city.lower() in user_query]
            logger.info(f"Matched: {unique_cities}")

            matched_countries = []
            for code, full_name in COUNTRY_MAPPING.items():
                # Check the 2-letter code or the full name
                if f" {code.lower()} " in f" {user_query} " or full_name.lower() in user_query:
                    if full_name in unique_countries_in_db:
                        matched_countries.append(full_name)
                    elif code in unique_countries_in_db:
                        matched_countries.append(code)

            # "3bhk", "3 bhk", "3 - bhk", "3BHK"
            bhk_pattern = r"(\d+)\s*(?:-|)\s*bhk"
            extracted_bhks = [int(d) for d in re.findall(bhk_pattern, user_query, re.IGNORECASE)]
            matched_bhks = [bhk for bhk in extracted_bhks if bhk in unique_bhks]
            requested_bhk = extracted_bhks[0] if extracted_bhks else None

            #logger.info(f"Final Matched BHKs: {matched_bhks}")         
            query = select(Project).where(Project.price_usd <= (budget * 1.3))
            query = query.order_by(Project.price_usd.desc())

            if matched_cities and matched_countries:
                logger.info(f"Extracted Country: {matched_countries}, Extracted City: {matched_cities}")
                query = query.where(
                    (Project.city.in_(matched_cities)) | (Project.country.in_(matched_countries))
                )
                state['city'] = matched_cities
                state['country'] = matched_countries

            elif matched_cities:
                logger.info(f"Extracted City: {matched_cities}")
                state['city'] = matched_cities
                query = query.where(Project.city.in_(matched_cities))

            elif matched_countries:
                logger.info(f"Extracted Country: {matched_countries}")
                query = query.where(Project.country.in_(matched_countries))
                state['country'] = matched_countries

            if matched_bhks:
                logger.info(f"Extracted BHK: {matched_bhks}")
                query = query.filter(Project.bedrooms.in_(matched_bhks))
                state['bhk'] = matched_bhks
            elif requested_bhk and requested_bhk > 0:
                logger.info(f"Requested {requested_bhk} BHK not found. Searching for lower options...")
                avail_stmt = select(Project.bedrooms).distinct().where(Project.price_usd <= (budget * 1.3))
                if matched_cities:
                    avail_stmt = avail_stmt.where(Project.city.in_(matched_cities))
                
                avail_res = await self.db.execute(avail_stmt)
                available_bhks = [b for b in avail_res.scalars().all() if b is not None]

                if requested_bhk in available_bhks:
                    query = query.where(Project.bedrooms == requested_bhk)
                    state['bhk'] = requested_bhk
                else:
                    lower_bhks = [b for b in available_bhks if b < requested_bhk]
                    if lower_bhks:
                        best_alt = max(lower_bhks)
                        logger.info(f"Best Alternative for City {matched_cities} is : {best_alt}")
                        query = query.where(Project.bedrooms == best_alt)
                        state['bhk'] = matched_bhks
                    else:
                        query = query.where(Project.bedrooms == -1)
                        
            matched_features = [f for f in KEY_FEATURES_LIST if f in user_query]
            state['features'] = matched_features
            if matched_features:
                        logger.info(f"Filtering by features: {matched_features}")
                        for feature in matched_features:
                            # We use or_ to check if the feature is in the 'features' column 
                            # OR the 'description' column. % is the wildcard for partial match.
                            query = query.where(
                                or_(
                                    Project.features.ilike(f"%{feature}%"),
                                    Project.description.ilike(f"%{feature}%"),
                                    Project.facilities.ilike(f"%{feature}%")

                                )
                            )
            query = query.order_by(Project.price_usd.desc())
            
            result = await self.db.execute(query)
            rows = result.scalars().all()

            state["projects"] = [
                {
                    "id": r.id,
                    "project_name": r.project_name,
                    "bedrooms": r.bedrooms,
                    "bathrooms": r.bathrooms,
                    "unit_type": r.unit_type,
                    "developer": r.developer,
                    "price_usd": r.price_usd,
                    "area_sqm": r.area_sqm,
                    "property_type": r.property_type,
                    "city": r.city,
                    "country": r.country,
                    "completion_status": r.completion_status,
                    "completion_date": str(r.completion_date) if r.completion_date else None,
                    "features": r.features,
                    "facilities": r.facilities,
                    "description": r.description,
                }
                for r in rows
            ]

            logger.info(f"Successfully retrieved {len(rows)} projects for budget: {budget}")
            return state

        except Exception as e:
            logger.error(f"Error in SQLTool: {str(e)}")
            state["projects"] = []
            return state
