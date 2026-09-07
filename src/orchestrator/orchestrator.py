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
from src.checkpoint.checkpointer import SessionCheckpointer
from src.rag.indexer import SimpleIndexer
from src.rag.reranker import FlashReranker
from src.utils.rate_limiter import SlidingRateLimiter
import logging

logger = logging.getLogger(__name__)


def parse_budget_in_rupees(text: str) -> float | None:
    """Extract a budget amount from text such as '30 lakh' or '5000 rs'."""
    if not text:
        return None

    lowered = text.lower().strip()
    match = re.search(r"(\d+(?:\.\d+)?)\s*(rs|rupees|inr|lakh|lac|crore|cr|k|thousand|m|million)?", lowered)
    if not match:
        return None

    amount = float(match.group(1))
    unit = (match.group(2) or "").lower()

    conversion = {
        "": 1.0,
        "rs": 1.0,
        "rupees": 1.0,
        "inr": 1.0,
        "k": 1000.0,
        "thousand": 1000.0,
        "lakh": 100000.0,
        "lac": 100000.0,
        "crore": 10000000.0,
        "cr": 10000000.0,
        "m": 1000000.0,
        "million": 1000000.0,
    }
    return amount * conversion.get(unit, 1.0)


def format_indian_rupees(value: float) -> str:
    if value is None:
        return "₹0"

    if value >= 10000000:
        crore_value = value / 10000000
        return f"₹{crore_value:,.2f} crore" if crore_value % 1 else f"₹{crore_value:,.0f} crore"

    if value >= 100000:
        lakh_value = value / 100000
        return f"₹{lakh_value:,.2f} lakh" if lakh_value % 1 else f"₹{lakh_value:,.0f} lakh"

    return f"₹{value:,.0f}"


class NegotiationOrchestrator:

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.max_local_guardrail_turns = int(self.config.get("max_local_guardrail_turns", 5))
        self.agents = self._initialize_agents()
        self.logger = logging.getLogger(__name__)
        self.checkpointer = SessionCheckpointer()
        self.indexer = SimpleIndexer()
        self.reranker = FlashReranker()
        self.rate_limiter = SlidingRateLimiter(max_requests=60, window_seconds=60)
        self._seed_index()

    def _seed_index(self):
        base_dir = "data/knowledge_base"
        from pathlib import Path
        path = Path(base_dir)
        if not path.exists():
            return
        for file in sorted(path.glob("*.txt")):
            text = file.read_text(encoding="utf-8", errors="ignore")
            self.indexer.add_document(file.stem, text, {"source": str(file)})

    def _checkpoint_state(self, state: NegotiationState):
        try:
            state.checkpoint_id = state.session_id
            self.checkpointer.save(state.session_id, state.model_dump())
        except Exception as exc:
            self.logger.warning("Checkpoint save failed: %s", exc)

    def _initialize_agents(self):
        return {
            "requirement": RequirementAgent(self.config),
            "research": ResearchAgent(self.config),
            "negotiation": NegotiationAgent(self.config),
            "compliance": ComplianceAgent(self.config)
        }

    def _build_conversational_response(self, user_message: str, session_id: str = None) -> str:
        lower = user_message.lower()
        budget_value = parse_budget_in_rupees(user_message)

        if "hinjewadi" in lower or "hijewadi" in lower:
            location = "Hinjewadi"
        else:
            location = "the location you mentioned"

        if budget_value is not None:
            budget_label = format_indian_rupees(budget_value)
            approx_1bhk = price_db.calculate_price("flat", "2BHK", "Hinjawadi", 800)[0] if hasattr(price_db, "calculate_price") else 4200000
            approx_2bhk = price_db.calculate_price("flat", "2BHK", "Hinjawadi", 1200)[0] if hasattr(price_db, "calculate_price") else 7200000
            if budget_value < 1000000:
                response = (
                    f"🏗️ Thanks for your message. For {location}, the realistic market ranges are usually around:\n"
                    f"• 1 BHK: ₹{approx_1bhk:,.0f} onwards\n"
                    f"• 2 BHK: ₹{approx_2bhk:,.0f} onwards\n\n"
                    f"This means a budget of {budget_label} is below the typical property range in {location}. If you want, I can still help with nearby alternatives such as rental units, studio options, or a more realistic budget range."
                )
            else:
                response = (
                    f"🏗️ Thanks for your requirement in {location}. Using your budget of {budget_label}, a realistic shortlist would usually be around:\n"
                    f"• 1 BHK: ₹{approx_1bhk:,.0f} onwards\n"
                    f"• 2 BHK: ₹{approx_2bhk:,.0f} onwards\n\n"
                    "I can help narrow it to ready-to-move options, builder offers, and a better deal structure within your budget."
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

        if not self.rate_limiter.allow(f"session:{state.session_id}"):
            fallback = "The system is temporarily rate-limited. Please wait a moment and try again."
            state.messages.append(Message(role="assistant", content=fallback, language="en", route="rate_limited", classification="system"))
            self._checkpoint_state(state)
            return state

        state.messages.append(Message(
            role="user",
            content=user_message
        ))

        guardrail_result = await guardrails.process(user_message, context={"project_type": state.project_type})
        classification = guardrail_result.get("classification", "conversational")
        state.last_guardrail = classification

        local_guardrail_turns = sum(1 for msg in state.messages if getattr(msg, "route", None) == "local_guardrail")
        if classification == "low_intent" and local_guardrail_turns < self.max_local_guardrail_turns:
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
            self._checkpoint_state(state)
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
                self._checkpoint_state(state)
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
            self._checkpoint_state(state)
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

        state.relevant_documents = self.reranker.rerank(
            self.indexer.search(user_message, top_k=5),
            user_message,
        )
        self._checkpoint_state(state)
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