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
                created_slots += 1
                
            except ValueError:
                continue 
                
        await db.commit()
        return {"resources_created": created_resources, "time_slots_created": created_slots}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
