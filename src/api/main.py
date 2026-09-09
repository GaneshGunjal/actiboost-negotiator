# src/api/main.py
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.orchestrator.orchestrator import NegotiationOrchestrator
from src.models.state import NegotiationState, Message
from src.checkpoint.checkpointer import SessionCheckpointer

# ========== CREATE APP FIRST ==========
app = FastAPI(title="Actiboost Negotiation System")

# ========== CORS ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== REQUEST MODELS ==========
class MessageRequest(BaseModel):
    message: str

class DealCreateRequest(BaseModel):
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    project_type: str
    project_size: Optional[str] = None
    location: Optional[str] = None
    initial_price: float
    final_price: Optional[float] = None
    session_id: Optional[str] = None
    negotiation_history: Optional[List[Dict]] = []

class HumanApprovalRequest(BaseModel):
    action: str  # approve, reject, hold
    approver: str
    notes: Optional[str] = None

# ========== INITIALIZE ==========
orchestrator = NegotiationOrchestrator()
checkpoint_store = SessionCheckpointer()
active_sessions: Dict[str, NegotiationState] = {}

# ========== ROOT ==========
@app.get("/")
async def root():
    return {
        "message": "Actiboost Negotiation System API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": [
            "/api/session/start",
            "/api/session/{session_id}/message",
            "/api/session/{session_id}/status",
            "/api/deals",
            "/api/deal/create",
            "/api/deal/{deal_id}/approve",
            "/api/deal/{deal_id}/human-approval",
            "/ws/{session_id}"
        ]
    }

# ========== SESSION ENDPOINTS ==========
@app.get("/api/session/start")
@app.post("/api/session/start")
async def start_session(student_id: str = "web_user", exam_id: str = "negotiation"):
    """Start a new negotiation session - supports both GET and POST"""
    try:
        state = await orchestrator.start_session(
            user_id=student_id,
            project_type="unknown"
        )
        checkpoint_store.save(state.session_id, state.model_dump())
        active_sessions[state.session_id] = state
        
        welcome_message = "🏗️ Welcome to Actiboost AI Negotiator! I'm here to help you with your construction needs. What can I assist you with today?"
        
        state.messages.append(Message(
            role="assistant",
            content=welcome_message,
            language="en",
            route="conversational",
            classification="conversational"
        ))
        
        return {
            "session_id": state.session_id,
            "student_id": student_id,
            "exam_id": exam_id,
            "status": "active",
            "welcome_message": welcome_message
        }
    except Exception as e:
        print(f"Error starting session: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "message": "Failed to start session"}
        )

@app.post("/api/session/{session_id}/message")
async def send_message(session_id: str, request: MessageRequest):
    """Send a message to the negotiation system"""
    if session_id not in active_sessions:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    
    state = active_sessions[session_id]
    user_message = request.message
    
    if not user_message:
        return JSONResponse({"error": "Message is required"}, status_code=400)
    
    state = await orchestrator.process_message(state, user_message)
    checkpoint_store.save(session_id, state.model_dump())
    active_sessions[session_id] = state
    
    assistant_message = None
    for msg in reversed(state.messages):
        if msg.role == "assistant":
            assistant_message = msg.content
            break
    
    return {
        "response": assistant_message or "I'm thinking about that...",
        "phase": state.phase.value,
        "status": state.status.value,
        "confidence": state.confidence_score,
        "violations": len(state.compliance_issues),
        "message_count": len(state.messages),
        "route": getattr(state, "route", "unknown"),
        "classification": getattr(state, "last_guardrail", "unknown")
    }

@app.get("/api/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get the current status of a session"""
    if session_id not in active_sessions:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    
    state = active_sessions[session_id]
    return {
        "session_id": session_id,
        "phase": state.phase.value,
        "status": state.status.value,
        "messages": len(state.messages),
        "violations": len(state.compliance_issues),
        "confidence": state.confidence_score,
        "project_type": state.project_type,
        "budget_range": state.budget_range
    }

# ========== DEAL ENDPOINTS ==========
@app.post("/api/deal/create")
async def create_deal(deal_data: DealCreateRequest):
    """Create a new deal in the database"""
    from src.models.database import SessionLocal, Deal
    
    db = SessionLocal()
    try:
        deal = Deal(
            customer_name=deal_data.customer_name,
            customer_email=deal_data.customer_email,
            customer_phone=deal_data.customer_phone,
            project_type=deal_data.project_type,
            project_size=deal_data.project_size,
            location=deal_data.location,
            initial_price=deal_data.initial_price,
            final_price=deal_data.final_price or deal_data.initial_price,
            status="pending",
            session_id=deal_data.session_id,
            negotiation_history=deal_data.negotiation_history or []
        )
        db.add(deal)
        db.commit()
        db.refresh(deal)
        return {"success": True, "deal_id": deal.id}
    except Exception as e:
        db.rollback()
        print(f"Error creating deal: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@app.get("/api/deals")
async def get_deals():
    """Get all deals"""
    from src.models.database import SessionLocal, Deal
    
    db = SessionLocal()
    try:
        deals = db.query(Deal).order_by(Deal.created_at.desc()).all()
        return [{
            "id": d.id,
            "customer_name": d.customer_name,
            "customer_email": d.customer_email,
            "project_type": d.project_type,
            "project_size": d.project_size,
            "location": d.location,
            "initial_price": d.initial_price,
            "final_price": d.final_price,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "approved_by": d.approved_by
        } for d in deals]
    finally:
        db.close()

@app.post("/api/deal/{deal_id}/approve")
async def approve_deal(deal_id: int, approver: str):
    """Approve a deal (Human-in-the-loop)"""
    from src.models.database import SessionLocal, Deal
    from datetime import datetime
    
    db = SessionLocal()
    try:
        deal = db.query(Deal).filter(Deal.id == deal_id).first()
        if not deal:
            return {"success": False, "error": "Deal not found"}
        
        deal.status = "approved"
        deal.approved_by = approver
        deal.approved_at = datetime.now()
        db.commit()
        return {"success": True, "deal_id": deal_id, "status": "approved"}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

# ========== HUMAN-IN-THE-LOOP ENDPOINT ==========
@app.post("/api/deal/{deal_id}/human-approval")
async def human_approval(deal_id: int, request: HumanApprovalRequest):
    """Human-in-the-loop approval system"""
    from src.models.database import SessionLocal, Deal
    from datetime import datetime
    
    db = SessionLocal()
    try:
        deal = db.query(Deal).filter(Deal.id == deal_id).first()
        if not deal:
            return {"success": False, "error": "Deal not found"}
        
        if request.action == "approve":
            deal.status = "approved"
            deal.approved_by = request.approver
            deal.approved_at = datetime.now()
            message = "✅ Deal approved by manager!"
        elif request.action == "reject":
            deal.status = "rejected"
            deal.approved_by = request.approver
            deal.approved_at = datetime.now()
            message = "❌ Deal rejected by manager."
        elif request.action == "hold":
            deal.status = "pending"
            message = "⏳ Deal placed on hold for review."
        else:
            return {"success": False, "error": "Invalid action"}
        
        if request.notes:
            deal.notes = request.notes
        
        db.commit()
        return {
            "success": True, 
            "deal_id": deal_id, 
            "status": deal.status,
            "message": message,
            "approved_by": request.approver,
            "approved_at": deal.approved_at.isoformat()
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

# ========== WEBSOCKET ==========
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    
    if session_id not in active_sessions:
        await websocket.send_json({"error": "Session not found"})
        await websocket.close()
        return
    
    state = active_sessions[session_id]
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                json_data = json.loads(data)
                user_message = json_data.get("message", "")
                
                if user_message:
                    state = await orchestrator.process_message(state, user_message)
                    active_sessions[session_id] = state
                    
                    assistant_message = None
                    for msg in reversed(state.messages):
                        if msg.role == "assistant":
                            assistant_message = msg.content
                            break
                    
                    await websocket.send_json({
                        "response": assistant_message or "Processing...",
                        "phase": state.phase.value,
                        "status": state.status.value,
                        "confidence": state.confidence_score
                    })
                
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
            except Exception as e:
                await websocket.send_json({"error": str(e)})
    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# ========== HEALTH CHECK ==========
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "timestamp": datetime.now().isoformat()
    }

# ========== RUN ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)