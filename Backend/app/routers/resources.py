from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Resource, TimeSlot
from app.schemas.resource import (
    ResourceCreate,
    ResourceResponse,
    ResourceUpdate,
    TimeSlotGenerateRequest,
    TimeSlotResponse,
)

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.post("/", response_model=ResourceResponse, status_code=201)
async def create_resource(data: ResourceCreate, db: AsyncSession = Depends(get_db)):
    resource = Resource(**data.model_dump())
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource


@router.get("/", response_model=list[ResourceResponse])
async def list_resources(
    resource_type: str | None = None,
    location: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Resource).where(Resource.is_active == True)
    if resource_type:
        query = query.where(Resource.resource_type == resource_type)
    if location:
        query = query.where(Resource.location == location)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(resource_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


@router.put("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: str,
    updates: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(resource, field, value)
    await db.commit()
    await db.refresh(resource)
    return resource


@router.delete("/{resource_id}", status_code=204)
async def delete_resource(resource_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    await db.delete(resource)
    await db.commit()


@router.post(
    "/{resource_id}/timeslots/generate",
    response_model=list[TimeSlotResponse],
    status_code=201,
)
async def generate_time_slots(
    resource_id: str,
    data: TimeSlotGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Resource not found")

    start_date = datetime.fromisoformat(data.start_date)
    end_date = datetime.fromisoformat(data.end_date)
    slots = []

    current_date = start_date
    while current_date <= end_date:
        current_time = current_date.replace(hour=data.daily_start_hour, minute=0, second=0)
        day_end = current_date.replace(hour=data.daily_end_hour, minute=0, second=0)
        while current_time < day_end:
            slot = TimeSlot(
                resource_id=resource_id,
                start_time=current_time,
                end_time=current_time + timedelta(minutes=30),
            )
            db.add(slot)
            slots.append(slot)
            current_time += timedelta(minutes=30)
        current_date += timedelta(days=1)

    await db.commit()
    for slot in slots:
        await db.refresh(slot)
    return slots


@router.get("/{resource_id}/timeslots", response_model=list[TimeSlotResponse])
async def list_time_slots(
    resource_id: str,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(TimeSlot).where(TimeSlot.resource_id == resource_id)
    if status:
        query = query.where(TimeSlot.status == status)
    query = query.order_by(TimeSlot.start_time)
    result = await db.execute(query)
    return result.scalars().all()
