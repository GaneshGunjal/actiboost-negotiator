# src/agents/research_agent.py
from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.models.state import NegotiationState
from src.utils.logfire_config import logfire_trace

class ResearchAgent(BaseAgent):

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("ResearchAgent", config)

    @logfire_trace(name="ResearchAgent - Run")
    async def run(self, state: NegotiationState) -> NegotiationState:
        self.log("Researching relevant information (RAG disabled)")
        
        # Skip RAG for now - just pass through
        state.research_findings = {
            "query": "RAG disabled",
            "results": [],
            "count": 0
        }
        state.relevant_documents = []
        
        self.log("Research complete (RAG disabled)")
        return state