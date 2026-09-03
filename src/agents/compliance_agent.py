# src/agents/compliance_agent.py
from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.models.state import NegotiationState, NegotiationStatus
from src.guardrails.nemo_guardrails import guardrails
from src.utils.logfire_config import logfire_trace

class ComplianceAgent(BaseAgent):

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("ComplianceAgent", config)

    @logfire_trace(name="ComplianceAgent - Run")
    async def run(self, state: NegotiationState) -> NegotiationState:
        self.log("Checking compliance")

        violations = []

        for msg in state.messages:
            if msg.role == "assistant":
                result = await guardrails.process(
                    user_message=msg.content,
                    context={"project_type": state.project_type}
                )

                if not result.get("is_compliant", True):
                    violations.append({
                        "message_id": msg.id,
                        "issue": result.get("compliance_issues", ["Compliance violation detected"])
                    })

        state.compliance_checks = {
            "total_checked": len(state.messages),
            "violations_found": len(violations),
            "is_clean": len(violations) == 0
        }

        if violations:
            state.compliance_issues = [v["issue"][0] if isinstance(v["issue"], list) else v["issue"] for v in violations]
            state.status = NegotiationStatus.FAILED
            self.log(f"Compliance violations found: {len(violations)}", "warning")
        else:
            self.log("All messages compliant")

        return state