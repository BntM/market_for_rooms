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
    Accepts: {
        "agent_id": str,
        "exams": [{"name": str, "date": "YYYY-MM-DD"}],
        "max_price": float,
        "strategy": "3_days_before"
    }
    Creates limit orders for 3 days prior to each exam.
    """
    agent_id = payload.get("agent_id")
    exams = payload.get("exams", [])
    max_price = payload.get("max_price", 20.0)
    
    # Validate agent
    agent = await db.scalar(select(Agent).where(Agent.id == agent_id))
    # If no agent ID provided, maybe use the first simulated user as 'me' for demo
    if not agent:
         agent = await db.scalar(select(Agent).where(Agent.name == "User_1"))
         if not agent:
             raise HTTPException(status_code=404, detail="Agent not found")
         agent_id = agent.id

    orders_created = 0
    
    for exam in exams:
        exam_date_str = exam.get("date")
        try:
             exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d")
        except:
            continue
            
        # Strategy: 3 days before
        # T-1, T-2, T-3
        target_dates = [exam_date - timedelta(days=i) for i in range(1, 4)]
        
        for date in target_dates:
            # Find slots on this day
            # Filter by time preference? Let's say evening study (18:00 - 22:00)
            # Fetch slots
            start_of_day = date.replace(hour=0, minute=0, second=0)
            end_of_day = date.replace(hour=23, minute=59, second=59)
            
            res = await db.execute(
                select(TimeSlot)
                .where(
                    and_(
                        TimeSlot.start_time >= start_of_day,
                        TimeSlot.start_time <= end_of_day,
                        TimeSlot.status == TimeSlotStatus.AVAILABLE 
                    )
                )
            )
            slots = res.scalars().all()
            
            # Smart filter: Evening hours (18-22)
            filtered_slots = []
            for s in slots:
                if 18 <= s.start_time.hour <= 22:
                    filtered_slots.append(s)
            
            # If no evening slots, take any
            if not filtered_slots:
                filtered_slots = slots
                
            # Create Limit Order for top 2 slots per day? Or all?
            # Let's do top 3 to avoid spamming too much
            for slot in filtered_slots[:3]:
                order = LimitOrder(
                    id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    time_slot_id=slot.id,
                    max_price=max_price,
                    status=LimitOrderStatus.PENDING
                )
                db.add(order)
                orders_created += 1
                
@router.post("/chat")
async def chat_with_agent(payload: dict):
    """
    Send a text message to Patriot AI.
    Payload: {"message": "str", "history": []}
    """
    message = payload.get("message", "")
    # For now, we are stateless / simplistic 
    # Use the client to just get a response from the same endpoint? 
    # The current client `parse_syllabus` is hardcoded for syllabus prompt.
    # Let's add a generic `chat` method to client first?
    # Or just mock for now to be safe.
    
    # Real logic:
    # response = patriot_client.send_message(message)
    
    # Mock for "Help me find a room" which isn't implemented in the PDF parser
    if "help" in message.lower() or "room" in message.lower():
         return {"response": "I can help you schedule limit orders! Please upload your syllabus PDF so I can extract your exam dates."}
    
    return {"response": "I am the Market Room Agent. Upload a syllabus to get started!"}

