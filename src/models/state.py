# src/models/state.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import uuid

class NegotiationPhase(str, Enum):
    REQUIREMENTS = "requirements"
    RESEARCH = "research"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    COMPLIANCE = "compliance"
    FINALIZATION = "finalization"

class NegotiationStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str
    content: str
    language: str = "en"
    timestamp: datetime = Field(default_factory=datetime.now)

class NegotiationState(BaseModel):
    """Complete state for the autonomous negotiator"""
    
    # Session Info
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # User Info
    user_id: str
    project_type: str = "unknown"
    budget_range: Dict[str, float] = Field(default_factory=lambda: {"min": 0.0, "max": 0.0})
    requirements: Dict[str, Any] = Field(default_factory=dict)
    
    # Negotiation Data
    phase: NegotiationPhase = NegotiationPhase.REQUIREMENTS
    status: NegotiationStatus = NegotiationStatus.ACTIVE
    messages: List[Message] = Field(default_factory=list)
    
    # Proposals
    current_proposal: Optional[Dict[str, Any]] = None
    proposal_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Research Data
    research_findings: Dict[str, Any] = Field(default_factory=dict)
    relevant_documents: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Compliance
    compliance_checks: Dict[str, Any] = Field(default_factory=dict)
    compliance_issues: List[str] = Field(default_factory=list)
    
    # Agent States
    agent_states: Dict[str, Any] = Field(default_factory=dict)
    
    # Metrics
    tokens_used: int = 0
    negotiation_rounds: int = 0
    confidence_score: float = 0.0
    
    # Checkpoint (for long-term memory)
    checkpoint_id: Optional[str] = None
    previous_states: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Golden Dataset Metadata (for evaluation)
    expected_outcome: Optional[str] = None
    ground_truth: Optional[Dict[str, Any]] = None