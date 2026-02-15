from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import random

from app.database import get_db
from app.models import Resource, TimeSlot, PriceHistory, TimeSlotStatus, AdminConfig
from app.services.historical_analyst import HistoricalAnalyst
from pydantic import BaseModel
from typing import Dict, Optional

router = APIRouter(prefix="/api/god", tags=["god"])

class ForecastRequest(BaseModel):
    end_date: str  # YYYY-MM-DD
    analysis_results: Optional[Dict] = None # Optional if using saved model
    use_saved_model: bool = False

@router.post("/auto-populate")
async def auto_populate_market(req: ForecastRequest, db: AsyncSession = Depends(get_db)):
    """
    Synthetic ML Model: Takes analysis results and populates the market with 
    predicted price trends and time slots up to the end_date.
    If use_saved_model is True, it fetches the last training results from AdminConfig.
    """
    try:
        end_dt = datetime.strptime(req.end_date, "%Y-%m-%d")
        now = datetime.now()
        
        # Determine Weights source
        weights = {}
        time_weights = {}
        
        if req.use_saved_model:
            # Fetch from AdminConfig
            res = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
            config = res.scalar_one_or_none()
            if config:
                weights = config.location_popularity or {}
                time_weights = config.time_popularity or {}
            else:
                 # Default fallback if no model trained yet
                 weights = {"Library": 1.2, "Fenwick Library": 1.2, "Student Center": 1.1}
                 time_weights = {"10:00": 1.3}
        elif req.analysis_results:
             weights = req.analysis_results.get("suggested_location_weights", {})
             time_weights = req.analysis_results.get("suggested_time_weights", {})
             
             # Also SAVE these to AdminConfig as the "latest model"
             res = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
             config = res.scalar_one_or_none()
             if not config:
                 config = AdminConfig(id=1)
                 db.add(config)
             
             config.location_popularity = weights
             config.time_popularity = time_weights
             await db.flush() # Persist immediate training
        
        # 1. Get all resources
        res_result = await db.execute(select(Resource))
        resources = res_result.scalars().all()
        
        created_slots = 0
        created_prices = 0
        
        current_date = now
        while current_date <= end_dt:
            # For each resource
            for res in resources:
                # Generate slots for 9 AM to 5 PM
                for hour in range(9, 18):
                    for minute in [0, 30]:
                        start_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        end_time = start_time + timedelta(minutes=30)
                        
                        # Check if slot exists to avoid duplicates
                        # (Simplification: Checking start_time & resource_id)
                        existing = await db.execute(
                            select(TimeSlot).where(
                                TimeSlot.resource_id == res.id, 
                                TimeSlot.start_time == start_time
                            )
                        )
                        if existing.scalar_one_or_none():
                            continue 

                        new_slot = TimeSlot(
                            resource_id=res.id,
                            start_time=start_time,
                            end_time=end_time,
                            status=TimeSlotStatus.AVAILABLE
                        )
                        db.add(new_slot)
                        await db.flush()
                        created_slots += 1
                        
                        # Generate Synthetic Price Data based on ML Weights
                        loc_w = weights.get(res.location, 1.0) or 1.0
                        time_str = f"{hour:02d}:{minute:02d}"
                        t_w = time_weights.get(time_str, 1.0) or 1.0
                        
                        # Base price formula + some "ML randomness"
                        base_price = 10.0 * float(loc_w) * float(t_w)
                        
                        # Create a series of price history points for this slot
                        for i in range(5):
                            ph = PriceHistory(
                                auction_id=None, # It's a forecasted price
                                time_slot_id=new_slot.id,
                                price=base_price + random.uniform(-2, 2),
                                created_at=start_time - timedelta(hours=random.randint(1, 24))
                            )
                            db.add(ph)
                            created_prices += 1
            
            # Move to next day
            current_date += timedelta(days=1)
            
        await db.commit()
        return {
            "status": "success",
            "message": f"ML Model generated {created_slots} slots and {created_prices} price data points.",
            "details": {
                "resources_processed": len(resources),
                "end_date": req.end_date
            }
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
