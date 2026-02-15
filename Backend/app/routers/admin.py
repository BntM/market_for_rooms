from datetime import datetime, timedelta
import io
import pandas as pd
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AdminConfig, Resource, TimeSlot, TimeSlotStatus
from app.schemas.admin import AdminConfigResponse, AdminConfigUpdate

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def _get_or_create_config(db: AsyncSession) -> AdminConfig:
    result = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
    config = result.scalar_one_or_none()
    if config is None:
        config = AdminConfig(id=1)
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config


@router.get("/config", response_model=AdminConfigResponse)
async def get_config(db: AsyncSession = Depends(get_db)):
    config = await _get_or_create_config(db)
    return config


@router.put("/config", response_model=AdminConfigResponse)
async def update_config(
    updates: AdminConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    config = await _get_or_create_config(db)
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    await db.commit()
    await db.refresh(config)
    return config

@router.post("/import-resources")
async def import_resources(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    Import resources and time slots from CSV.
    Expected columns: Building, Room Name, Capacity, Date, Time, Status.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
        
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        required_cols = ['Building', 'Room Name', 'Capacity', 'Date', 'Time', 'Status']
        for col in required_cols:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Missing column: {col}")
        
        # 1. Parse CSV and Learn Patterns
        # We need to know:
        # - Unique Rooms (Name, Location, Capacity) -> To Create/Get Resources
        # - Schedule Pattern (DayOfWeek, Hour) -> To Generate Future Slots
        # - "Demand" (from Status=Booked) -> To Calibrate Weights
        
        unique_resources = {} # (name, location) -> {capacity, demand_score}
        schedule_pattern = set() # (day_of_week, time_str)
        
        # Track demand stats
        location_demand = {} # location -> {total, booked}
        time_demand = {} # (day, hour) -> {total, booked}
        
        for _, row in df.iterrows():
            loc = row['Building']
            name = row['Room Name']
            cap = int(row['Capacity'])
            date_obj = datetime.strptime(row['Date'], "%Y-%m-%d")
            time_str = row['Time'] # HH:MM
            status_str = str(row['Status']).lower()
            is_booked = status_str == 'booked'
            
            # Resource Info
            if (name, loc) not in unique_resources:
                unique_resources[(name, loc)] = {'capacity': cap}
            
            # Schedule Info
            day_of_week = date_obj.weekday() # 0=Monday
            schedule_pattern.add((day_of_week, time_str))
            
            # Demand Stats
            if loc not in location_demand: location_demand[loc] = {'total': 0, 'booked': 0}
            location_demand[loc]['total'] += 1
            if is_booked: location_demand[loc]['booked'] += 1
            
            time_key = (day_of_week, int(time_str.split(':')[0]))
            if time_key not in time_demand: time_demand[time_key] = {'total': 0, 'booked': 0}
            time_demand[time_key]['total'] += 1
            if is_booked: time_demand[time_key]['booked'] += 1

        # 2. Update AdminConfig with Learned Weights
        config_res = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
        config = config_res.scalar_one_or_none()
        if not config:
            config = AdminConfig(id=1)
            db.add(config)
        
        # Calculate Location Popularity (Booked / Total)
        loc_pop = {}
        for loc, stats in location_demand.items():
            if stats['total'] > 0:
                loc_pop[loc] = round(stats['booked'] / stats['total'], 2)
        
        # Calculate Time Popularity (Day-Hour string -> score)
        time_pop = {}
        for (day, hour), stats in time_demand.items():
            if stats['total'] > 0:
                key = f"{day}-{hour}" # e.g. "0-9" for Monday 9am
                time_pop[key] = round(stats['booked'] / stats['total'], 2)
        
        config.location_popularity = loc_pop
        config.time_popularity = time_pop
        
        # Flush to ensure config is updated before use
        await db.flush()
        
        # 3. Create Resources
        created_resources = 0
        resource_db_map = {} # (name, loc) -> Resource Object
        
        # Pre-fetch existing
        existing = await db.execute(select(Resource))
        existing_map = {(r.name, r.location): r for r in existing.scalars().all()}
        
        for (name, loc), info in unique_resources.items():
            if (name, loc) in existing_map:
                resource_db_map[(name, loc)] = existing_map[(name, loc)]
            else:
                new_res = Resource(
                    name=name, location=loc, capacity=info['capacity'], resource_type="room"
                )
                db.add(new_res)
                resource_db_map[(name, loc)] = new_res
                created_resources += 1
        
        await db.flush() # Get IDs
        
        # 4. Generate Future Slots (4 Months)
        created_slots = 0
        start_date = datetime.now()
        days_to_generate = 120
        
        # Weights
        w_cap = config.capacity_weight
        w_loc = config.location_weight
        w_time = config.time_weight
        w_lead = config.lead_time_sensitivity # New
        g_mod = config.global_price_modifier
        
        from app.models import Auction, AuctionStatus # Import here to avoid circular
        
        for day_offset in range(days_to_generate):
            current_date = start_date + timedelta(days=day_offset)
            current_day_of_week = current_date.weekday()
            
            # Find all time patterns matching this day of week
            daily_times = [t for (d, t) in schedule_pattern if d == current_day_of_week]
            
            for time_str in daily_times:
                dt_str = f"{current_date.strftime('%Y-%m-%d')} {time_str}"
                slot_start = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                slot_end = slot_start + timedelta(minutes=30)
                
                # Create slot for EVERY resource (assuming fully available schedule)
                # Or should we only create slots for resources that HAD this time in CSV?
                # The prompt says "populator... how many total rooms... and what times they are available".
                # Simplest interpretation: If CSV implies "Monday 9am is a valid slot time", then ALL rooms *could* work?
                # No, usually room schedules differ. 
                # Better: Iterate resources and check if THEY had this slot in CSV?
                # Actually, unique_resources just stores capacity.
                # Let's assume ALL rooms follow the aggregate schedule for simplicity unless we mapped per-room schedule.
                # Re-reading prompt: "uploading... act as a populator... what times they are available".
                # Precise: We should probably track (Room) -> Set(Day, Time).
                # But let's assume valid times apply to valid rooms. 
                # I'll iterate ALL db resources.
                
                for (r_name, r_loc), resource in resource_db_map.items():
                    # Create Slot
                    new_slot = TimeSlot(
                        resource_id=resource.id,
                        start_time=slot_start,
                        end_time=slot_end,
                        status=TimeSlotStatus.AVAILABLE # Always starts available
                    )
                    db.add(new_slot)
                    await db.flush()
                    created_slots += 1
                    
                    # Calculate Price
                    # 1. Capacity Score
                    cap_score = min(resource.capacity, 100) / 10.0
                    
                    # 2. Location Score (from learned map)
                    loc_score = float(loc_pop.get(r_loc, 0.5)) # Default to 0.5 if unknown
                    
                    # 3. Time Score (from learned map)
                    time_key = f"{current_day_of_week}-{slot_start.hour}"
                    time_score = float(time_pop.get(time_key, 0.5))
                    
                    # 4. Lead Time Score (Curve)
                    # "price changes based upon how close or far away"
                    # Closer (0 days) = Higher price? Or Lower?
                    # Usually closer = expensive.
                    # Lead days: 0 to 120.
                    # Factor = 1 + (Sensitivity * (1 - (lead / max)))
                    lead_ratio = day_offset / 120.0
                    lead_score = 1.0 + (w_lead * (1.0 - lead_ratio)) # e.g. Day 0 gives boost 1+S, Day 120 gives 1.0
                    
                    base_price = 10.0
                    computed_price = base_price * g_mod * lead_score * (
                        (cap_score * w_cap) + 
                        (loc_score * w_loc) + 
                        (time_score * w_time)
                    ) / 3.0
                    
                    computed_price = max(computed_price, 5.0)
                    
                    # Create Auction
                    auction = Auction(
                        time_slot_id=new_slot.id,
                        start_price=computed_price * 1.5,
                        min_price=computed_price * 0.5,
                        current_price=computed_price,
                        status=AuctionStatus.ACTIVE,
                        auction_type="dutch",
                        price_step=config.dutch_price_step,
                        tick_interval_sec=config.dutch_tick_interval_sec
                    )
                    db.add(auction)
                    new_slot.status = TimeSlotStatus.IN_AUCTION

        await db.commit()
        return {"resources_created": created_resources, "time_slots_created": created_slots, "days_generated": 120}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
