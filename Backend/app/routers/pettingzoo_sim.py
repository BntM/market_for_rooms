"""Router for PettingZoo market simulation endpoints."""

import logging
import sys
import os
import traceback
import uuid
import threading
from typing import Dict

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.admin_config import AdminConfig
from app.schemas.pettingzoo_sim import (
    PZApplyRequest,
    PZGridSearchRequest,
    PZGridSearchResponse,
    PZGridSearchResult,
    PZJobStatus,
    PZMetricsResponse,
    PZSimConfig,
    PZSingleResponse,
)

# Add project root to path so we can import simulation package
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    from simulation.config import GridSearchConfig, SimulationConfig
    from simulation.runner import run_grid_search, run_single_simulation
    logger.info("simulation package imported from %s", _project_root)
except ImportError as e:
    logger.error("Failed to import simulation package from %s: %s", _project_root, e)
    raise

router = APIRouter(prefix="/api/pz-simulation", tags=["pz-simulation"])

# In-memory job store
_jobs: Dict[str, PZJobStatus] = {}


def _sim_config_from_request(req: PZSimConfig) -> SimulationConfig:
    return SimulationConfig(
        num_agents=req.num_agents,
        num_rooms=req.num_rooms,
        slots_per_room_per_day=req.slots_per_room_per_day,
        max_days=req.max_days,
        token_amount=req.token_amount,
        token_frequency=req.token_frequency,
        auction_start_price=req.auction_start_price,
        auction_min_price=req.auction_min_price,
        auction_price_step=req.auction_price_step,
        max_ticks=req.max_ticks,
        high_demand_days=[(d[0], d[1]) for d in req.high_demand_days if len(d) == 2],
    )


@router.post("/single", response_model=PZSingleResponse)
async def run_single(config: PZSimConfig):
    """Run a single simulation with the given config."""
    sim_config = _sim_config_from_request(config)
    metrics, daily_detail = run_single_simulation(sim_config)

    return PZSingleResponse(
        metrics=PZMetricsResponse(
            supply_demand_ratio=metrics.supply_demand_ratio,
            utilization_rate=metrics.utilization_rate,
            price_volatility=metrics.price_volatility,
            unmet_demand=metrics.unmet_demand,
            gini_coefficient=metrics.gini_coefficient,
            stability_score=metrics.stability_score,
        ),
        daily_detail=daily_detail,
    )


@router.post("/run")
async def start_grid_search(request: PZGridSearchRequest):
    """Start a grid search in a background thread. Returns job_id."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = PZJobStatus(job_id=job_id, status="running", progress=0.0)

    base_config = _sim_config_from_request(request.config)

    grid_config = GridSearchConfig(
        base_config=base_config,
        token_amounts=request.token_amounts,
        token_frequencies=request.token_frequencies,
        num_seeds=request.num_seeds,
    )

    def _run():
        try:
            print(f"[PZ-SIM] Grid search started: {len(request.token_amounts)} amounts x "
                  f"{len(request.token_frequencies)} freqs x {request.num_seeds} seeds",
                  flush=True)

            def on_progress(p: float):
                _jobs[job_id].progress = p

            result = run_grid_search(grid_config, progress_callback=on_progress)

            _jobs[job_id].result = PZGridSearchResponse(
                best=PZGridSearchResult(**result["best"]) if result["best"] else None,
                best_daily=result.get("best_daily", {}),
                all_results=[PZGridSearchResult(**r) for r in result["all_results"]],
                heatmap=result.get("heatmap", {}),
            )
            _jobs[job_id].status = "completed"
            _jobs[job_id].progress = 1.0
            print(f"[PZ-SIM] Grid search completed. Best: {result['best']}", flush=True)
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[PZ-SIM] Grid search FAILED: {e}\n{tb}", flush=True)
            _jobs[job_id].status = "failed"
            _jobs[job_id].error = f"{e}\n{tb}"

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return {"job_id": job_id}


@router.get("/status/{job_id}", response_model=PZJobStatus)
async def get_job_status(job_id: str):
    """Poll progress and results for a grid search job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return _jobs[job_id]


@router.post("/apply-best")
async def apply_best(req: PZApplyRequest, db: AsyncSession = Depends(get_db)):
    """Write the best token_amount + frequency to AdminConfig."""
    result = await db.execute(select(AdminConfig).where(AdminConfig.id == 1))
    config = result.scalar_one_or_none()

    if not config:
        config = AdminConfig(id=1)
        db.add(config)

    config.token_starting_amount = req.token_amount
    config.token_frequency_days = float(req.token_frequency)
    await db.commit()
    await db.refresh(config)

    return {
        "message": "Admin config updated",
        "token_starting_amount": config.token_starting_amount,
        "token_frequency_days": config.token_frequency_days,
    }
