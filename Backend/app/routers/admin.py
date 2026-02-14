from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AdminConfig
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
