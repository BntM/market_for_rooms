import random
from datetime import datetime, timedelta
import uuid
from sqlalchemy import select, insert, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AdminConfig, Resource, TimeSlot, Auction, TimeSlotStatus, AuctionStatus

async def recalculate_prices(db: AsyncSession, start_date: datetime, days: int = 7):
    # 1. Get Config & Weightings
    config_res = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
    config = config_res.scalar_one_or_none()
    if not config:
        return

    # Weights
    w_cap = config.capacity_weight
    w_loc = config.location_weight
    w_tod = config.time_of_day_weight
    w_dow = config.day_of_week_weight
    w_lead = config.lead_time_sensitivity
    g_mod = config.global_price_modifier
    
    loc_pop = config.location_popularity or {}
    time_pop = config.time_popularity or {} # Keyed by "day-hour"
    
    # 2. Get Resources
    res_result = await db.execute(select(Resource))
    resources = res_result.scalars().all()
    resource_map = {r.id: r for r in resources}

    # 3. Fetch future slots
    end_date = start_date + timedelta(days=days)
    
    slots_res = await db.execute(
        select(TimeSlot, Auction)
        .outerjoin(Auction, Auction.time_slot_id == TimeSlot.id)
        .where(
            TimeSlot.start_time >= start_date,
            TimeSlot.start_time <= end_date,
            TimeSlot.status != TimeSlotStatus.BOOKED
        )
    )
    rows = slots_res.all()
    
    # Helper to calculate price
    def calculate_price(slot, resource):
        dow = slot.start_time.weekday()
        hour = slot.start_time.hour
        
        # 1. Learned Popularity (ML aspect)
        # Location
        loc_score = float(loc_pop.get(resource.location, 0.5))
        
        # Time (Day + Hour)
        time_key = f"{dow}-{hour}"
        hist_time_pop = float(time_pop.get(time_key, 0.5))
        
        # Fallback to general hour peak if specific day-hour is missing
        if time_key not in time_pop:
            dist_from_peak = abs(hour - 14)
            hour_score = max(0.2, 1.0 - (dist_from_peak / 10.0))
        else:
            hour_score = hist_time_pop

        # 2. Capacity Score
        cap_score = min(resource.capacity, 100) / 100.0
        
        # 3. Lead Time Score (Urgency Modifier)
        delta = slot.start_time - config.current_simulation_date
        days_out = max(0, delta.total_seconds() / 86400.0)
        lead_ratio = min(1.0, days_out / 30.0) # 0 = today, 1 = 30+ days away
        # Price increases exponentially as we get closer
        lead_score = 1.0 + (w_lead * (1.1 - lead_ratio))
        
        # 4. Market Noise (The "Vegas" factor)
        noise = 1.0 + (random.uniform(-0.05, 0.05)) # Small random fluctuations
        
        # Combine
        # Using a weighted average of scores
        base_demand = (
            (cap_score * w_cap * 0.5) + # Small rooms are base
            (loc_score * w_loc * 2.0) + # Location is big
            (hour_score * w_tod * 2.5) + # Time is biggest
            (hist_time_pop * w_dow * 1.5) # Day of week influence
        ) / 5.0
        
        base_price = 15.0
        final_price = base_price * g_mod * lead_score * base_demand * noise
        
        # Hard limits
        return max(5.0, min(final_price, 500.0))

    # Update Loop
    for slot, auction in rows:
        resource = resource_map.get(slot.resource_id)
        if not resource: continue
        
        new_price = calculate_price(slot, resource)
        
        if auction:
             # Update existing auction
             auction.current_price = round(float(new_price), 2)
             auction.start_price = round(float(new_price * 1.6), 2)
             auction.min_price = round(float(new_price * 0.4), 2)
        else:
            # Create new auction if missing
            new_auc_id = str(uuid.uuid4())
            new_auction = Auction(
                id=new_auc_id,
                time_slot_id=slot.id,
                start_price=round(float(new_price * 1.6), 2),
                min_price=round(float(new_price * 0.4), 2),
                current_price=round(float(new_price), 2),
                status=AuctionStatus.ACTIVE,
                auction_type=config.default_auction_type,
                price_step=config.dutch_price_step,
                tick_interval_sec=config.dutch_tick_interval_sec,
                created_at=config.current_simulation_date or datetime.utcnow()
            )
            db.add(new_auction)
            
    # Increment model version
    config.pricing_model_version += 1
    await db.flush()
