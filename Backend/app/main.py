from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.config import settings
from app.database import init_db
import app.models  # noqa: F401 — register all models with SQLAlchemy
from app.routers import (
    admin,
    agents,
    auctions,
    market,
    resources,
    simulation,
    history,
    pettingzoo_sim,
    bookings,
    student,  # New
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Safe to ignore if tables exist, but ensures data integrity
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(admin.router)
app.include_router(agents.router)
app.include_router(auctions.router)
app.include_router(market.router)
app.include_router(resources.router)
app.include_router(simulation.router)
app.include_router(history.router)
app.include_router(pettingzoo_sim.router)
app.include_router(bookings.router)
app.include_router(student.router)  # New


@app.get("/health")
async def health_check():
    return {"status": "ok"}
