from datetime import datetime, timedelta
import io
import pandas as pd
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, insert, text
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.database import get_db
from app.models import AdminConfig, Resource, TimeSlot, TimeSlotStatus, Auction, AuctionStatus
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

async def _process_import(df: pd.DataFrame, db: AsyncSession):
    # 1. Parse CSV and Learn Patterns
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
        
        day_of_week = date_obj.weekday()
        schedule_pattern.add((day_of_week, time_str))
        
        if loc not in location_demand: location_demand[loc] = {'total': 0, 'booked': 0}
        location_demand[loc]['total'] += 1
        if is_booked: location_demand[loc]['booked'] += 1
        
        time_key = (day_of_week, int(time_str.split(':')[0]))
        if time_key not in time_demand: time_demand[time_key] = {'total': 0, 'booked': 0}
        time_demand[time_key]['total'] += 1
        if is_booked: time_demand[time_key]['booked'] += 1

    # 2. Update AdminConfig
    config_res = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
    config = config_res.scalar_one_or_none()
    if not config:
        config = AdminConfig(id=1)
        db.add(config)
    
    loc_pop = {}
    for loc, stats in location_demand.items():
        if stats['total'] > 0:
            loc_pop[loc] = round(stats['booked'] / stats['total'], 2)
    
    # Time maps for pricing
    day_pop_map = {}
    for d in range(7):
        d_total = sum(time_demand.get((d, h), {'total':0})['total'] for h in range(24))
        d_booked = sum(time_demand.get((d, h), {'booked':0})['booked'] for h in range(24))
        day_pop_map[d] = (d_booked / d_total) if d_total > 0 else 0.5
        
    hour_pop_map = {}
    for h in range(24):
        h_total = sum(time_demand.get((d, h), {'total':0})['total'] for d in range(7))
        h_booked = sum(time_demand.get((d, h), {'booked':0})['booked'] for d in range(7))
        hour_pop_map[h] = (h_booked / h_total) if h_total > 0 else 0.5
    
    # Save raw time popularity for reference just in case
    time_pop = {}
    for (day, hour), stats in time_demand.items():
        if stats['total'] > 0:
            key = f"{day}-{hour}"
            time_pop[key] = round(stats['booked'] / stats['total'], 2)
    
    config.location_popularity = loc_pop
    config.time_popularity = time_pop
    await db.flush()
    
    # 3. Create Resources
    created_resources = 0
    resource_db_map = {}
    
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
    
    await db.flush()
    
    # 4. Generate Future Slots
    created_slots = 0
    start_date = config.current_simulation_date or datetime.now()
    days_to_generate = 14 # Optimized for demo speed (was 45)
    
    w_cap = config.capacity_weight
    w_loc = config.location_weight
    w_tod = config.time_of_day_weight
    w_dow = config.day_of_week_weight
    w_lead = config.lead_time_sensitivity
    g_mod = config.global_price_modifier
    
    import random
    
    slots_to_insert = []
    auctions_to_insert = []

    # Pre-calculate factors for speed
    start_price_base = 15.0
    
    for day_offset in range(days_to_generate):
        current_date = start_date + timedelta(days=day_offset)
        current_day_of_week = current_date.weekday()
        
        daily_times = [t for (d, t) in schedule_pattern if d == current_day_of_week]
        
        for time_str in daily_times:
            dt_str = f"{current_date.strftime('%Y-%m-%d')} {time_str}"
            slot_start = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            slot_end = slot_start + timedelta(minutes=30)
            
            # Time Score
            hour = slot_start.hour
            time_key = f"{current_day_of_week}-{hour}"
            hist_time_pop = float(time_pop.get(time_key, 0.5))
            if time_key not in time_pop:
                dist_from_peak = abs(hour - 14)
                hour_score = max(0.2, 1.0 - (dist_from_peak / 10.0))
            else:
                hour_score = hist_time_pop

            for (r_name, r_loc), resource in resource_db_map.items():
                slot_id = str(uuid.uuid4())
                
                # Create Slot
                new_slot = {
                    "id": slot_id,
                    "resource_id": resource.id,
                    "start_time": slot_start,
                    "end_time": slot_end,
                    "status": "in_auction" 
                }
                slots_to_insert.append(new_slot)
                created_slots += 1
                
                # --- Calculate Initial Price Inline ---
                # Location Score
                loc_score = float(loc_pop.get(resource.location, 0.5))
                
                # Capacity Score
                cap_score = min(resource.capacity, 100) / 100.0
                
                # Lead Time (It's new, so creation time ~ now. start time - now)
                delta = slot_start - start_date # approx
                days_out = max(0, delta.total_seconds() / 86400.0)
                lead_ratio = min(1.0, days_out / 30.0)
                lead_score = 1.0 + (w_lead * (1.1 - lead_ratio))
                
                # Noise
                noise = 1.0 + (random.uniform(-0.05, 0.05))
                
                base_demand = (
                    (cap_score * w_cap * 0.5) + 
                    (loc_score * w_loc * 2.0) + 
                    (hour_score * w_tod * 2.5) + 
                    (hist_time_pop * w_dow * 1.5)
                ) / 5.0
                
                final_price = start_price_base * g_mod * lead_score * base_demand * noise
                final_price = max(5.0, min(final_price, 500.0))
                
                # Create Auction
                auc_id = str(uuid.uuid4())
                start_p = round(float(final_price * 1.6), 2)
                min_p = round(float(final_price * 0.4), 2)
                curr_p = round(float(final_price), 2)
                
                auctions_to_insert.append({
                    "id": auc_id,
                    "time_slot_id": slot_id,
                    "start_price": start_p,
                    "current_price": curr_p,
                    "min_price": min_p,
                    "status": AuctionStatus.ACTIVE,
                    "auction_type": "dutch", # Default
                    "price_step": 2.0,
                    "tick_interval_sec": 10.0,
                    "created_at": start_date
                })

    # Bulk Insert slots first so auctions can reference them
    chunk_size = 1000
    for i in range(0, len(slots_to_insert), chunk_size):
        await db.execute(insert(TimeSlot), slots_to_insert[i:i+chunk_size])
    
    # Bulk Insert auctions
    for i in range(0, len(auctions_to_insert), chunk_size):
        await db.execute(insert(Auction), auctions_to_insert[i:i+chunk_size])
    
    await db.flush()
    # Skip recalculate_prices call since we did it inline
        
    return {"resources_created": created_resources, "time_slots_created": created_slots}

@router.post("/import-resources")
async def import_resources(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        res = await _process_import(df, db)
        await db.commit()
        return res
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-and-load-defaults")
async def reset_and_load_defaults(db: AsyncSession = Depends(get_db)):
    try:
        # Load local CSV
        import os
        csv_path = "gmu_room_data_full.csv"
        if not os.path.exists(csv_path):
             csv_path = "../gmu_room_data_full.csv"
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Could not find gmu_room_data_full.csv in {os.getcwd()} or ..")

        df = pd.read_csv(csv_path)
             
        # Delete existing Logic
        # Order matters due to FKs
        await db.execute(text("DELETE FROM bookings"))
        await db.execute(text("DELETE FROM bids"))
        await db.execute(text("DELETE FROM auctions"))
        await db.execute(text("DELETE FROM time_slots"))
        # Resources kept to avoid ID key issues if referenced elsewhere? 
        # But if we delete slots, we can delete resources if we want fresh start.
        await db.execute(text("DELETE FROM resources"))
        
        # Reset sequences if using Postgres, but for SQLite it manages rowids.
        
        res = await _process_import(df, db)
        await db.commit()
        return res
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
