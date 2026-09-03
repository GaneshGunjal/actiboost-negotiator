# src/guardrails/nemo_guardrails.py
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Guardrails:
    """Simple guardrails stub"""
    
    async def process(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process message through guardrails"""
        # Simple check for compliance
        violations = []
        
        # Check for sensitive content
        sensitive_words = ["bypass", "illegal", "cash", "avoid tax"]
        for word in sensitive_words:
            if word in user_message.lower():
                violations.append(f"Sensitive content detected: {word}")
        
        return {
            "processed": True,
            "response": user_message,
            "compliance_issues": violations,
            "is_compliant": len(violations) == 0
        }

guardrails = Guardrails()