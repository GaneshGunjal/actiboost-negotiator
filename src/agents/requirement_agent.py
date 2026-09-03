# src/agents/requirement_agent.py
from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.models.state import NegotiationState, Message, NegotiationPhase
from src.utils.groq_client import groq
from src.utils.logfire_config import logfire_trace

class RequirementAgent(BaseAgent):

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("RequirementAgent", config)

    @logfire_trace(name="RequirementAgent - Run")
    async def run(self, state: NegotiationState) -> NegotiationState:
        self.log("Analyzing user requirements")

        user_message = None
        for msg in reversed(state.messages):
            if msg.role == "user":
                user_message = msg
                break

        if not user_message:
            self.log("No user message found", "warning")
            return state

        prompt = f"""
        Analyze this user message and extract project requirements.

        Message: {user_message.content}

        Return JSON with:
        - project_type: string (residential/commercial/industrial/renovation)
        - budget_range: {{"min": number, "max": number}} (in INR)
        - timeline: string (urgent/standard/flexible)
        - key_requirements: list of strings
        - questions_for_user: list of follow-up questions

        If information is missing, note it as "unknown".
        """

        try:
            result = await groq.ask_json(prompt)

            # Extract project type
            state.project_type = result.get("project_type", "unknown")
            
            # Extract budget - ensure numbers
            budget = result.get("budget_range", {"min": 0, "max": 0})
            try:
                state.budget_range = {
                    "min": float(budget.get("min", 0)) if budget.get("min") else 0,
                    "max": float(budget.get("max", 0)) if budget.get("max") else 0
                }
            except (ValueError, TypeError):
                state.budget_range = {"min": 0, "max": 0}
            
            # Extract requirements
            state.requirements = {
                "timeline": result.get("timeline", "unknown"),
                "key_requirements": result.get("key_requirements", []),
                "questions_for_user": result.get("questions_for_user", [])
            }

            # Move to research phase if we have requirements
            if len(state.requirements.get("key_requirements", [])) > 0:
                state.phase = NegotiationPhase.RESEARCH

            self.log(f"Extracted requirements: {state.project_type}")

        except Exception as e:
            self.log(f"Error extracting requirements: {e}", "error")

        return state