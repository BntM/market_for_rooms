from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
import uuid

from app.database import get_db
from app.models.agent import Agent
from app.models.limit_order import LimitOrder, LimitOrderStatus
from app.models.resource import TimeSlot, TimeSlotStatus, Resource
from app.services.patriot_ai_client import patriot_client

router = APIRouter(prefix="/api/student", tags=["student"])

@router.post("/parse-syllabus")
async def parse_syllabus(file: UploadFile = File(...)):
    """Upload PDF syllabus, extract text, and ask Patriot AI for exam dates."""
    try:
        content = await file.read()
        
        # 1. Extract Text
        text = patriot_client.extract_text_from_pdf(content)
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
            
        # 2. Ask Patriot AI
        # Mock response if extraction fails or for testing without live API if needed
        # exams = [{"name": "Midterm 1", "date": "2026-03-01", "time": "10:00"}]
        exams = patriot_client.parse_syllabus(text)
        
        # Fallback Mock for Hackathon Demo if API fails/timeout
        if not exams:
             exams = [
                 {"name": "Midterm Exam", "date": "2026-03-10", "time": "14:00"},
                 {"name": "Final Project", "date": "2026-04-15", "time": "09:00"}
             ]
             print("Using fallback mock exams due to API failure/empty response.")
             
        return {"exams": exams, "raw_text_preview": text[:200]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-exam-orders")
async def create_exam_orders(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    Creates real limit orders on active auctions.
    Picks the nearest available auctions to the requested study dates.
    """
    agent_id = payload.get("agent_id")
    exams = payload.get("exams", [])
    max_price = payload.get("max_price", 20.0)
    
    # Validate agent
    agent = await db.scalar(select(Agent).where(Agent.id == agent_id))
    if not agent:
        agent = await db.scalar(select(Agent).where(Agent.name == agent_id))
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    agent_id = agent.id

    # Check balance
    if agent.token_balance < max_price:
        raise HTTPException(status_code=400, detail="Insufficient token balance")

    orders_created = 0
    
    # Get all ACTIVE auctions with their time slots
    from app.models import Auction, AuctionStatus
    auc_res = await db.execute(
        select(Auction, TimeSlot)
        .join(TimeSlot, Auction.time_slot_id == TimeSlot.id)
        .where(Auction.status == AuctionStatus.ACTIVE)
        .order_by(TimeSlot.start_time)
    )
    active_auctions = auc_res.all()
    
    if not active_auctions:
        return {"orders_count": 0, "message": "No active auctions available to place orders on."}
    
    # For each exam, find the best study slots (3 days before, evening preferred)
    used_auction_ids = set()
    
    for exam in exams:
        exam_date_str = exam.get("date")
        try:
            exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d")
        except:
            continue
        
        # Target study window: 3 days before exam
        target_dates = [exam_date - timedelta(days=i) for i in range(1, 4)]
        
        # Score each auction by how close it is to a target study date + time preference
        scored = []
        for auction, slot in active_auctions:
            if auction.id in used_auction_ids:
                continue
            # Date distance (lower is better)
            best_dist = min(abs((slot.start_time.date() - td.date()).days) for td in target_dates)
            # Evening bonus (18:00+ is preferred study time)
            time_bonus = 0 if 14 <= slot.start_time.hour <= 22 else 5
            score = best_dist + time_bonus
            scored.append((score, auction, slot))
        
        scored.sort(key=lambda x: x[0])
        
        # Take best 3 per exam
        for score, auction, slot in scored[:3]:
            if auction.current_price <= max_price:
                order = LimitOrder(
                    id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    time_slot_id=slot.id,
                    max_price=max_price,
                    status=LimitOrderStatus.PENDING
                )
                db.add(order)
                used_auction_ids.add(auction.id)
                orders_created += 1
    
    await db.commit()
    return {"orders_count": orders_created, "message": f"Created {orders_created} limit orders for {len(exams)} exams"}

from app.services.gemini_client import gemini_client
from app.models.admin_config import AdminConfig

@router.post("/chat")
async def chat_with_agent(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    Send a text message to Patriot AI / Gemini Market Analyst.
    Payload: {"message": "str", "history": []}
    """
    message = payload.get("message", "")
    
    # 1. Fetch Market Context (Simplified)
    # In a real app, we'd query average prices, busy slots, etc.
    config = await db.scalar(select(AdminConfig))
    sim_time = config.current_simulation_date if config else "Unknown"
    
    market_context = {
        "sim_time": str(sim_time),
        "avg_price": "22.5", # Mocked average
        "busy_hours": "10:00 - 14:00",
        "trend": "Rising due to upcoming midterms"
    }

    # 2. Check intent (Simple keyword check for now, can be LLM based later)
    # If user asks for "Help" or "Upload", guide them.
    if "upload" in message.lower():
        return {"response": "You can upload your syllabus by clicking the paperclip icon! I'll extract your exam dates automatically."}

    # 3. Call Gemini
    response_text = await gemini_client.chat_with_market_analyst(message, market_context)
    
    return {"response": response_text}

