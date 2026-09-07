# src/utils/logfire_config.py
import logging
import os
from functools import wraps
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import logfire as pydantic_logfire
except Exception:  # pragma: no cover - optional dependency
    pydantic_logfire = None

try:
    from langsmith import traceable as langsmith_traceable
except Exception:  # pragma: no cover - optional dependency
    langsmith_traceable = None


def configure_observability(run_name: str, project_name: str = "actiboost", **metadata: Any) -> Dict[str, Any]:
    """Enable a minimal but useful observability metadata contract for the app."""
    project_name = project_name or "actiboost"
    os.environ.setdefault("LANGSMITH_PROJECT", project_name)
    config = {
        "run_name": run_name,
        "project_name": project_name,
        "langsmith_enabled": bool(os.getenv("LANGSMITH_API_KEY")),
        "logfire_enabled": pydantic_logfire is not None,
        "metadata": metadata,
    }
    logger.info("Observability configured for %s", run_name)
    return config


def compute_confidence_score(
    evidence_score: float,
    compliance_score: float,
    retrieval_score: float,
    uncertainty_penalty: float = 0.0,
) -> float:
    """Return a bounded confidence score using grounded evidence rather than a fake placeholder."""
    evidence = max(0.0, min(1.0, float(evidence_score)))
    compliance = max(0.0, min(1.0, float(compliance_score)))
    retrieval = max(0.0, min(1.0, float(retrieval_score)))
    penalty = max(0.0, min(0.5, float(uncertainty_penalty)))

    raw_score = (0.45 * evidence) + (0.35 * compliance) + (0.20 * retrieval)
    score = max(0.0, min(1.0, raw_score - penalty))
    return round(score, 4)


def calculate_state_confidence(state: Any) -> float:
    """Derive a score from actual state signals: requirements, research retrieval, and compliance."""
    requirements = getattr(state, "requirements", {}) or {}
    key_requirements = requirements.get("key_requirements", []) or []
    research_findings = getattr(state, "research_findings", {}) or {}
    retrieval_count = len(getattr(state, "relevant_documents", []) or [])
    findings_count = int(research_findings.get("count", 0) or 0)
    compliance_issues = getattr(state, "compliance_issues", []) or []

    requirement_score = 1.0 if key_requirements else 0.4
    retrieval_score = min(1.0, (retrieval_count + findings_count) / 3.0)
    compliance_score = 1.0 if not compliance_issues else 0.35
    evidence_score = min(1.0, (0.55 * requirement_score) + (0.45 * retrieval_score))
    uncertainty_penalty = 0.10 if compliance_issues else 0.0

    return compute_confidence_score(
        evidence_score=evidence_score,
        compliance_score=compliance_score,
        retrieval_score=retrieval_score,
        uncertainty_penalty=uncertainty_penalty,
    )


def log_query_route(user_message: str, classification: str, route: str, source: str = "unknown") -> Dict[str, Any]:
    """Emit observability metadata describing whether the request was technical or conversational and which backend executed it."""
    payload = {
        "query": (user_message or "")[:500],
        "classification": classification,
        "route": route,
        "source": source,
        "used_llm": route == "llm",
        "used_sql_cache": route == "sql_cache",
        "used_local_guardrail": route in {"local_guardrail", "off_topic"},
    }
    if pydantic_logfire is not None:
        try:
            pydantic_logfire.info("QUERY_ROUTE", extra=payload)
        except Exception:
            pass
    logger.info("Query route: classification=%s route=%s source=%s", classification, route, source)
    return payload


def logfire_trace(name: str = None):
    """Trace a function while keeping the app safe when observability packages are missing."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            trace_name = name or func.__name__
            run_meta = configure_observability(trace_name, project_name=os.getenv("LANGSMITH_PROJECT", "actiboost"))
            logger.info("🔍 %s started", trace_name)
            if pydantic_logfire is not None:
                try:
                    pydantic_logfire.info(f"TRACE start: {trace_name}", extra=run_meta)
                except Exception:
                    pass
            try:
                result = await func(*args, **kwargs)
                if pydantic_logfire is not None:
                    try:
                        pydantic_logfire.info(f"TRACE complete: {trace_name}", extra={"status": "success", **run_meta})
                    except Exception:
                        pass
                logger.info("✅ %s completed", trace_name)
                return result
            except Exception as e:
                if pydantic_logfire is not None:
                    try:
                        pydantic_logfire.exception(f"TRACE failed: {trace_name}", exc_info=True)
                    except Exception:
                        pass
                logger.exception("❌ %s failed: %s", trace_name, e)
                raise
        return wrapper
    return decorator


class LogfireClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self.logger.info(message)

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self.logger.error(message)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self.logger.warning(message)

    def exception(self, message: str, exc_info: bool = True, extra: Optional[Dict[str, Any]] = None):
        self.logger.exception(message)


logfire = LogfireClient() if pydantic_logfire is None else pydantic_logfire


__all__ = [
    "configure_observability",
    "compute_confidence_score",
    "calculate_state_confidence",
    "log_query_route",
    "logfire_trace",
    "logfire",
]