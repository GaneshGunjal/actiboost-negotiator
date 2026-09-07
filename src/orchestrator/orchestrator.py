# src/orchestrator/orchestrator.py
from typing import Dict, Any
import re
from src.agents.requirement_agent import RequirementAgent
from src.agents.research_agent import ResearchAgent
from src.agents.negotiation_agent import NegotiationAgent
from src.agents.compliance_agent import ComplianceAgent
from src.models.database import log_low_intent_lead, get_cached_response, save_cached_response
from src.models.state import NegotiationState, NegotiationPhase, Message
from src.guardrails.nemo_guardrails import guardrails
from src.utils.logfire_config import calculate_state_confidence, configure_observability, log_query_route
from src.utils.price_loader import price_db
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

    def _build_conversational_response(self, user_message: str, session_id: str = None) -> str:
        lower = user_message.lower()
        budget_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:rs|rupees|inr|lakh|lac|crore|cr)", lower)
        budget_value = None
        if budget_matches:
            try:
                budget_value = float(budget_matches[0])
            except ValueError:
                budget_value = None

        if "hinjewadi" in lower or "hijewadi" in lower:
            location = "Hinjewadi"
        else:
            location = "the location you mentioned"

        if budget_value is not None and budget_value < 100000:
            approx_1bhk = price_db.calculate_price("flat", "2BHK", "Hinjawadi", 800)[0] if hasattr(price_db, "calculate_price") else 4200000
            approx_2bhk = price_db.calculate_price("flat", "2BHK", "Hinjawadi", 1200)[0] if hasattr(price_db, "calculate_price") else 7200000
            response = (
                f"🏗️ Thanks for your message. For {location}, the realistic market ranges are usually around:\n"
                f"• 1 BHK: ₹{approx_1bhk:,.0f} onwards\n"
                f"• 2 BHK: ₹{approx_2bhk:,.0f} onwards\n\n"
                "This means a budget of ₹100 is well below the likely property range. If you want, I can still help with nearby alternatives such as rental units, studio options, or a more realistic budget range."
            )
        else:
            response = (
                f"🏗️ Thanks for sharing your requirement for {location}. I can help with available property types, realistic budget ranges, and nearby options. "
                "Please share the preferred size, possession timeline, and your target budget range so I can narrow it down quickly."
            )

        log_low_intent_lead(session_id, user_message, "low_intent", "Low-intent property budget message; avoid LLM/vector retrieval")
        return response

    async def process_message(self, state: NegotiationState, user_message: str) -> NegotiationState:
        self.logger.info(f"Processing message: {user_message[:50]}...")
        configure_observability("process_message", project_name="actiboost", session_id=state.session_id)
        state.messages.append(Message(
            role="user",
            content=user_message
        ))

        guardrail_result = await guardrails.process(user_message, context={"project_type": state.project_type})
        classification = guardrail_result.get("classification", "conversational")
        state.last_guardrail = classification

        if classification == "low_intent":
            state.route = "local_guardrail"
            response = self._build_conversational_response(user_message, state.session_id)
            state.messages.append(Message(
                role="assistant",
                content=response,
                language="en",
                route=state.route,
                classification=classification,
            ))
            state.confidence_score = 0.92
            log_query_route(user_message, classification, state.route, source="local_guardrail")
            self.logger.info("Guardrail short-circuited %s request without LLM call.", classification)
            return state

        if classification == "off_topic":
            state.route = "off_topic"
            response = "I’m here to help with construction, pricing, land, and negotiation queries. Please ask about a property, budget, or project requirement and I’ll assist you directly."
            state.messages.append(Message(
                role="assistant",
                content=response,
                language="en",
                route=state.route,
                classification=classification,
            ))
            state.confidence_score = 0.9
            log_query_route(user_message, classification, state.route, source="local_guardrail")
            self.logger.info("Off-topic request handled locally without LLM call.")
            return state

        if classification == "technical":
            cached_response = get_cached_response(user_message, "technical")
            if cached_response:
                state.route = "sql_cache"
                state.messages.append(Message(
                    role="assistant",
                    content=cached_response,
                    language="en",
                    route=state.route,
                    classification=classification,
                ))
                state.confidence_score = 0.94
                log_query_route(user_message, classification, state.route, source="sqlite")
                self.logger.info("Technical request served from SQL cache.")
                return state

        if classification == "conversational" and guardrails._is_simple_conversational_message(user_message):
            state.route = "local_guardrail"
            response = "Hello! Welcome back to Actiboost AI Negotiator. Tell me your budget, preferred location, and property type and I’ll guide you quickly."
            if any(keyword in user_message.lower() for keyword in ["price", "land", "flat", "house", "property"]):
                response = self._build_conversational_response(user_message, state.session_id)
            state.messages.append(Message(
                role="assistant",
                content=response,
                language="en",
                route=state.route,
                classification=classification,
            ))
            state.confidence_score = 0.88
            log_query_route(user_message, classification, state.route, source="local_guardrail")
            self.logger.info("Simple conversational property inquiry handled locally without LLM call.")
            return state

        state.route = "llm"
        log_query_route(user_message, classification, state.route, source="groq")
        state = await self.agents["requirement"].run(state)
        if state.phase in [NegotiationPhase.RESEARCH, NegotiationPhase.PROPOSAL]:
            state = await self.agents["research"].run(state)
        state = await self.agents["negotiation"].run(state)
        state = await self.agents["compliance"].run(state)
        state.confidence_score = calculate_state_confidence(state)
        self.logger.info("Computed confidence score: %.4f", state.confidence_score)

        if classification == "technical":
            latest_response = None
            for msg in reversed(state.messages):
                if msg.role == "assistant":
                    latest_response = msg.content
                    break
            if latest_response:
                save_cached_response(user_message, "technical", latest_response, "llm")

        return state

    async def start_session(self, user_id: str, project_type: str = "unknown") -> NegotiationState:
        state = NegotiationState(
            user_id=user_id,
            project_type=project_type,
            budget_range={"min": 0.0, "max": 0.0},
            requirements={}
        )
        state.confidence_score = calculate_state_confidence(state)
        configure_observability("start_session", project_name="actiboost", user_id=user_id, session_id=state.session_id)
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