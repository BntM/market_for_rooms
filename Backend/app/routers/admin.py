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
        
        created_resources = 0
        created_slots = 0
        
        # Cache resources to minimize DB hits
        existing_res = await db.execute(select(Resource))
        resource_map = {(r.name, r.location): r for r in existing_res.scalars().all()}
        
        for _, row in df.iterrows():
            loc = row['Building']
            name = row['Room Name']
            cap = int(row['Capacity'])
            
            # 1. Get or Create Resource
            if (name, loc) not in resource_map:
                new_res = Resource(
                    name=name,
                    location=loc,
                    capacity=cap,
                    resource_type="room"
                )
                db.add(new_res)
                await db.flush() # Get ID
                resource_map[(name, loc)] = new_res
                created_resources += 1
            
            resource = resource_map[(name, loc)]
            
            # 2. Create Time Slot
            try:
                # Parse Date and Time
                dt_str = f"{row['Date']} {row['Time']}"
                start_time = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                end_time = start_time + timedelta(minutes=30)
                
                status_str = str(row['Status']).lower()
                status = TimeSlotStatus.AVAILABLE if status_str == 'available' else TimeSlotStatus.BOOKED
                
                new_slot = TimeSlot(
                    resource_id=resource.id,
                    start_time=start_time,
                    end_time=end_time,
                    status=status
                )
                db.add(new_slot)
                await db.flush() # Need ID for Auction
                created_slots += 1
                
                # 3. Create Auction/Price Logic Immediately
                # "initial pricing well just be based on the .csv... studying how the capacity, location, and time"
                
                # Get Config for weights (or defaults if new)
                # We haven't fetched config inside the loop to avoid DB spam, 
                # but we should fetch it once at start.
                if created_slots == 1:
                     config_res = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
                     config = config_res.scalar_one_or_none()
                     if not config:
                        config = AdminConfig(id=1) 
                        db.add(config)
                        await db.flush()

                # Basic Heuristics
                # Capacity: Standardize around 10-50?
                # Time: Peak 10am-2pm? (Hour 10-14)
                
                cap_score = min(resource.capacity, 100) / 10.0 # 10 cap -> 1.0, 50 cap -> 5.0
                
                hour = start_time.hour
                time_score = 1.0
                if 9 <= hour <= 17: time_score = 1.5 # Work day
                if 11 <= hour <= 14: time_score = 2.0 # Prime time
                
                # Location score: simple hash or random if unknown? 
                # Or just basic density? Let's use 1.0 default and let Admin tune via "Location Popularity" JSON later.
                # The user said "studying... location". 
                # If we have location_popularity map in config, use it.
                loc_weights = config.location_popularity or {}
                loc_score = float(loc_weights.get(resource.location, 1.0))
                
                # Configurable Weights
                w_cap = config.capacity_weight
                w_loc = config.location_weight
                w_time = config.time_weight
                g_mod = config.global_price_modifier
                
                # Pricing Formula
                # Base is ~10 tokens.
                base_val = 10.0
                computed_price = base_val * g_mod * (
                    (cap_score * w_cap) + 
                    (loc_score * w_loc) + 
                    (time_score * w_time)
                ) / 3.0 # Average out
                
                # Ensure min price
                computed_price = max(computed_price, 5.0)

                # Create Auction (if available)
                if status == TimeSlotStatus.AVAILABLE:
                    from app.models import Auction, AuctionStatus
                    auction = Auction(
                        time_slot_id=new_slot.id,
                        start_price=computed_price * 1.2, # Start a bit higher
                        min_price=computed_price * 0.5,
                        current_price=computed_price,
                        status=AuctionStatus.ACTIVE,
                        auction_type="dutch",
                        price_step=config.dutch_price_step,
                        tick_interval_sec=config.dutch_tick_interval_sec
                    )
                    db.add(auction)
                    # Mark slot as in auction
                    new_slot.status = TimeSlotStatus.IN_AUCTION
                
            except ValueError:
                continue 
                
        await db.commit()
        return {"resources_created": created_resources, "time_slots_created": created_slots}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
