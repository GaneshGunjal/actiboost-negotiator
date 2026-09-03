# src/orchestrator/orchestrator.py
from typing import Dict, Any
from src.agents.requirement_agent import RequirementAgent
from src.agents.research_agent import ResearchAgent
from src.agents.negotiation_agent import NegotiationAgent
from src.agents.compliance_agent import ComplianceAgent
from src.models.state import NegotiationState, NegotiationPhase, Message
import logging

logger = logging.getLogger(__name__)

class NegotiationOrchestrator:

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.agents = self._initialize_agents()
        self.logger = logging.getLogger(__name__)

    def _initialize_agents(self):
        return {
            "requirement": RequirementAgent(self.config),
            "research": ResearchAgent(self.config),
            "negotiation": NegotiationAgent(self.config),
            "compliance": ComplianceAgent(self.config)
        }

    async def process_message(self, state: NegotiationState, user_message: str) -> NegotiationState:
        self.logger.info(f"Processing message: {user_message[:50]}...")
        state.messages.append(Message(
            role="user",
            content=user_message
        ))
        state = await self.agents["requirement"].run(state)
        if state.phase in [NegotiationPhase.RESEARCH, NegotiationPhase.PROPOSAL]:
            state = await self.agents["research"].run(state)
        state = await self.agents["negotiation"].run(state)
        state = await self.agents["compliance"].run(state)
        return state

    async def start_session(self, user_id: str, project_type: str = "unknown") -> NegotiationState:
        state = NegotiationState(
            user_id=user_id,
            project_type=project_type,
            budget_range={"min": 0.0, "max": 0.0},
            requirements={}
        )
        self.logger.info(f"Started session for user {user_id}")
        return state

    def get_status(self, state: NegotiationState) -> Dict[str, Any]:
        return {
            "session_id": state.session_id,
            "phase": state.phase.value,
            "status": state.status.value,
            "messages": len(state.messages),
            "violations": len(state.compliance_issues),
            "confidence": state.confidence_score
        }