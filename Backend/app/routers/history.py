from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import pandas as pd
import io

from app.database import get_db
from app.models import Resource
from app.services.historical_analyst import HistoricalAnalyst
from app.services.market_simulator import RoomMarketSimulator
from app.schemas.history import (
    AnalysisResponse, 
    SimulationConfig, 
    SimulationResult,
    OptimizationRequest,
    OptimizationResponse
)

router = APIRouter(prefix="/api/history", tags=["history"])

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_history(file: UploadFile = File(...)):
    """
    Upload a CSV file with columns 'location', 'time_slot', 'day'/'date'.
    Returns suggested weights and detected events.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        analyst = HistoricalAnalyst()
        demand_analysis = analyst.analyze_demand(df)
        events = analyst.detect_seasonality(df)
        
        return AnalysisResponse(
            suggested_location_weights=demand_analysis.get("suggested_location_weights", {}),
            suggested_time_weights=demand_analysis.get("suggested_time_weights", {}),
            detected_events=events
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/simulate", response_model=List[SimulationResult])
async def run_simulation(config: SimulationConfig, db: AsyncSession = Depends(get_db)):
    """
    Run an in-memory market simulation based on the provided configuration.
    Returns a list of all bookings made during the simulation.
    """
    try:
        sim = RoomMarketSimulator(base_price=config.base_price)
        
        # Setup Rooms
        if config.use_real_rooms:
            result = await db.execute(select(Resource))
            rooms = result.scalars().all()
            sim.setup_rooms(existing_rooms=rooms)
        else:
            sim.setup_rooms(num_rooms=40)
        
        # Setup Agents
        sim.setup_agents_advanced([a.model_dump() for a in config.agent_configs])
        
        # Run
        results = sim.run_simulation(
            days=config.days,
            weights=config.weights,
            token_drip=config.token_drip,
            events=config.events
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_price(config: OptimizationRequest, db: AsyncSession = Depends(get_db)):
    """
    Run multiple simulations to find the base price that maximizes revenue.
    """
    try:
        sim = RoomMarketSimulator()
        price_range = list(range(config.price_range_start, config.price_range_end + 1, config.price_step))
        
        agent_configs = [a.model_dump() for a in config.agent_configs]
        
        # Setup Rooms
        existing_rooms = None
        if config.use_real_rooms:
            result = await db.execute(select(Resource))
            existing_rooms = result.scalars().all()

        result = sim.optimize_price(
            base_price_range=price_range,
            agent_configs=agent_configs,
            weights=config.weights,
            events=config.events,
            existing_rooms=existing_rooms
        )
        
        return OptimizationResponse(
            best_base_price=result['best_base_price'],
            max_revenue=result['max_revenue'],
            all_results=result['all_results']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")
