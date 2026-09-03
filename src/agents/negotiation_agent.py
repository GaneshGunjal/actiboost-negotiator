# src/agents/negotiation_agent.py
from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.models.state import NegotiationState, Message
from src.utils.groq_client import groq
from src.utils.logfire_config import logfire_trace

class NegotiationAgent(BaseAgent):

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("NegotiationAgent", config)

    @logfire_trace(name="NegotiationAgent - Run")
    async def run(self, state: NegotiationState) -> NegotiationState:
        self.log("Generating negotiation response")

        user_message = None
        for msg in reversed(state.messages):
            if msg.role == "user":
                user_message = msg
                break

        if not user_message:
            self.log("No user message found", "warning")
            return state

        context_parts = []
        
        # Project Type
        if state.project_type and state.project_type != "unknown":
            context_parts.append(f"Project Type: {state.project_type}")
        
        # Budget Range - Safe handling
        if state.budget_range:
            min_budget = state.budget_range.get("min", 0)
            max_budget = state.budget_range.get("max", 0)
            
            try:
                min_budget = float(min_budget) if min_budget else 0
                max_budget = float(max_budget) if max_budget else 0
            except (ValueError, TypeError):
                min_budget = 0
                max_budget = 0
            
            if min_budget > 0:
                max_str = f" - {max_budget}" if max_budget > 0 else ""
                context_parts.append(f"Budget Range: {min_budget}{max_str}")
        
        # Key Requirements
        if state.requirements.get("key_requirements"):
            context_parts.append(f"Key Requirements: {', '.join(state.requirements['key_requirements'][:3])}")
        
        context = "\n".join(context_parts) if context_parts else "No additional context yet"

        prompt = f"""
        You are Actiboost's AI negotiation agent for construction projects.

        Context:
        {context}

        User: {user_message.content}

        Return JSON with:
        - response: your response text
        - follow_up: list of follow-up questions
        - confidence: number from 0-1
        """

        try:
            result = await groq.ask_json(prompt)

            state.messages.append(Message(
                role="assistant",
                content=result.get("response", "How can I help you with your construction project?"),
                language="en"
            ))

            try:
                state.confidence_score = float(result.get("confidence", state.confidence_score))
            except (ValueError, TypeError):
                state.confidence_score = 0.5

            self.log(f"Generated response with confidence {state.confidence_score:.2f}")

        except Exception as e:
            self.log(f"Error generating response: {e}", "error")
            state.messages.append(Message(
                role="assistant",
                content="I understand you're interested in our construction services. Could you please tell me more about your project?",
                language="en"
            ))

        return state