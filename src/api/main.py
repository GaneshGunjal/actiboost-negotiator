# src/api/main.py
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from typing import Dict, Any
from datetime import datetime
from src.orchestrator.orchestrator import NegotiationOrchestrator
from src.models.state import NegotiationState, Message

# Request Model
class MessageRequest(BaseModel):
    message: str

# Create FastAPI app
app = FastAPI(title="Actiboost Negotiation System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = NegotiationOrchestrator()

# Store active sessions
active_sessions: Dict[str, NegotiationState] = {}

@app.get("/")
async def root():
    return {
        "message": "Actiboost Negotiation System API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/api/session/start",
            "/api/session/{session_id}/message",
            "/api/session/{session_id}/status",
            "/ws/{session_id}"
        ]
    }

@app.post("/api/session/start")
async def start_session(student_id: str = "web_user", exam_id: str = "negotiation"):
    """Start a new negotiation session"""
    state = await orchestrator.start_session(
        user_id=student_id,
        project_type="unknown"
    )
    active_sessions[state.session_id] = state
    
    welcome_message = "🏗️ Welcome to Actiboost AI Negotiator! I'm here to help you with your construction needs. What can I assist you with today?"
    
    state.messages.append(Message(
        role="assistant",
        content=welcome_message,
        language="en"
    ))
    
    return {
        "session_id": state.session_id,
        "student_id": student_id,
        "exam_id": exam_id,
        "status": "active",
        "welcome_message": welcome_message
    }

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
        "message_count": len(state.messages)
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

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)