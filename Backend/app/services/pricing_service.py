from datetime import datetime, timedelta
import uuid
from sqlalchemy import select, insert, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AdminConfig, Resource, TimeSlot, Auction, TimeSlotStatus, AuctionStatus

async def recalculate_prices(db: AsyncSession, start_date: datetime, days: int = 120):
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
    # time_pop = config.time_popularity or {} # Raw time pop
    
    # 2. Get Resources
    res_result = await db.execute(select(Resource))
    resources = res_result.scalars().all()
    resource_map = {r.id: r for r in resources}

    # 3. Define Time Patterns (Simplified for now - strictly 9am-5pm or from existing slots?)
    # For "Progress a Day", we might want to GENERATE new slots if they don't exist, 
    # OR just update existing auctions.
    # The request says "changes all prices... dynamic pricing". 
    # Let's focus on updating EXISTING active auctions and creating new ones if needed.
    
    # Let's fetch all future slots from start_date
    end_date = start_date + timedelta(days=days)
    
    # Check for slots in this range
    # Ideally, we should be generating slots if they don't exist.
    # For this implementation, let's assume we are updating PRICES of existing unbooked slots.
    
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
        # Time components
        dow = slot.start_time.weekday()
        hour = slot.start_time.hour
        
        # Demand scores (mock logic here if maps are empty, or use learned data)
        # Using simple heuristics if config maps are missing
        
        # Loc Score
        loc_score = float(loc_pop.get(resource.location, 0.5))
        
        # Time Score (simple peak curve centered at 14:00)
        dist_from_peak = abs(hour - 14)
        hour_score = max(0.2, 1.0 - (dist_from_peak / 10.0))
        
        # Day Score (Tu/We/Th busy)
        if dow in [1, 2, 3]: day_score = 0.8
        elif dow in [0, 4]: day_score = 0.6
        else: day_score = 0.3
        
        # Capacity Score
        cap_score = min(resource.capacity, 100) / 100.0
        
        # Lead Time Score (closer = more expensive)
        delta = slot.start_time - config.current_simulation_date
        days_out = max(0, delta.days)
        lead_ratio = min(1.0, days_out / 30.0) # 0 = now, 1 = 30+ days away
        lead_score = 1.0 + (w_lead * (1.0 - lead_ratio)) # High lead weight -> expensive now
        
        # Combine
        combined_score = (
            (cap_score * w_cap) + 
            (loc_score * w_loc) + 
            (day_score * w_dow * 2.0) + 
            (hour_score * w_tod * 2.0)
        ) / 4.0
        
        base_price = 10.0
        final_price = max(base_price * g_mod * lead_score * combined_score, 5.0)
        return final_price

    # Update Loop
    for slot, auction in rows:
        resource = resource_map.get(slot.resource_id)
        if not resource: continue
        
        new_price = calculate_price(slot, resource)
        
        if auction:
             # Update existing auction
             auction.current_price = new_price
             auction.start_price = new_price * 1.5
             auction.min_price = new_price * 0.5
        else:
            # Create new auction if missing
            new_auction = Auction(
                id=str(uuid.uuid4()),
                time_slot_id=slot.id,
                start_price=new_price * 1.5,
                min_price=new_price * 0.5,
                current_price=new_price,
                status=AuctionStatus.ACTIVE,
                auction_type=config.default_auction_type,
                price_step=config.dutch_price_step,
                tick_interval_sec=config.dutch_tick_interval_sec,
                created_at=datetime.utcnow()
            )
            db.add(new_auction)
            
    await db.flush()
