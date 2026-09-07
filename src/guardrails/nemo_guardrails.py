# src/guardrails/nemo_guardrails.py
from typing import Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


class Guardrails:
    """Guardrail classification for routing conversational traffic without unnecessary LLM calls."""

    TECHNICAL_KEYWORDS = {
        "sql", "python", "api", "code", "debug", "prompt", "function", "class",
        "query", "schema", "database", "json", "yaml", "regex", "algorithm",
        "vector", "retriever", "index", "langchain", "rag", "llm", "token", "model",
    }

    OFF_TOPIC_KEYWORDS = {
        "joke", "weather", "capital of france", "football", "movie", "song", "politics",
        "how are you", "what are you doing today", "what are you doing", "who are you", "tell me a joke",
        "what is the capital", "what is your name", "good morning", "hello there", "i love you",
        "can you help with math", "what's up", "how's it going"
    }

    SENSITIVE_WORDS = ["bypass", "illegal", "cash", "avoid tax", "fake invoice", "fraud"]

    @staticmethod
    def _is_low_intent_budget_message(text: str) -> bool:
        lowered = text.lower()
        if re.search(r"\b\d+\s*(rs|rupees|inr|lakh|lac|crore|cr)\b", lowered):
            if "flat" in lowered or "house" in lowered or "property" in lowered or "budget" in lowered:
                return True
        return False

    @staticmethod
    def _is_off_topic_message(text: str) -> bool:
        lowered = text.lower()
        property_keywords = {"flat", "house", "property", "apartment", "budget", "location", "area", "villa", "rent", "buy", "price", "deal"}
        if any(keyword in lowered for keyword in property_keywords):
            return False
        if any(keyword in lowered for keyword in Guardrails.OFF_TOPIC_KEYWORDS):
            return True
        return False

    @staticmethod
    def _is_simple_conversational_message(text: str) -> bool:
        lowered = (text or "").strip().lower()
        if not lowered:
            return False
        simple_greetings = {"hi", "hello", "hey", "good morning", "good evening", "namaste"}
        if lowered in simple_greetings:
            return True
        if any(keyword in lowered for keyword in ["price of land", "land price", "what is the price of land", "land in pune", "property price", "what is the price of", "flat price", "house price"]):
            return True

        property_intent = any(keyword in lowered for keyword in ["flat", "house", "apartment", "land", "villa", "property", "buy", "rent", "budget", "location", "hinjewadi", "pune"])
        if property_intent and any(action in lowered for action in ["want", "need", "looking", "want to buy", "need a", "search", "find", "interested"]):
            return True
        return False

    async def process(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Classify the message and gate whether LLM is required."""
        text = (user_message or "").strip()
        lowered = text.lower()

        violations = []
        for word in self.SENSITIVE_WORDS:
            if word in lowered:
                violations.append(f"Sensitive content detected: {word}")

        technical_score = sum(1 for token in self.TECHNICAL_KEYWORDS if token in lowered)
        contains_code_like = bool(re.search(r"`|\{|\}|\bselect\b|\bfrom\b|\bwhere\b|\bdef \w+\(|class \w+\b", lowered))
        low_intent = self._is_low_intent_budget_message(text)
        off_topic = self._is_off_topic_message(text)
        simple_conversational = self._is_simple_conversational_message(text)

        if not text:
            classification = "empty"
            requires_llm = False
        elif low_intent:
            classification = "low_intent"
            requires_llm = False
        elif off_topic:
            classification = "off_topic"
            requires_llm = False
        elif technical_score > 0 or contains_code_like:
            classification = "technical"
            requires_llm = True
        elif simple_conversational:
            classification = "conversational"
            requires_llm = False
        else:
            classification = "conversational"
            requires_llm = False

        reason = (
            "Low-intent budget mismatch; use local price guidance instead of LLM/vector retrieval."
            if classification == "low_intent"
            else (
                "Off-topic chat; no property negotiation action required."
                if classification == "off_topic"
                else (
                    "Conventional property conversation; local handling is sufficient."
                    if classification == "conversational"
                    else "Technical or high-risk request; LLM allowed for assisted response."
                )
            )
        )

        safe_response = {
            "processed": True,
            "response": text,
            "classification": classification,
            "requires_llm": requires_llm,
            "compliance_issues": violations,
            "is_compliant": len(violations) == 0,
            "reason": reason,
        }

        logger.info("Guardrail check: %s -> requires_llm=%s", classification, requires_llm)
        return safe_response


guardrails = Guardrails()