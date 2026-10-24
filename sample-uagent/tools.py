"""Agent tools and business logic with planted bug for ASI:One self-healing test."""

from typing import Any, Dict


def format_agent_status(info: Dict[str, Any]) -> Dict[str, Any]:
    """Formats system health and agent metrics into a summary report (Working tool)."""
    return {
        "status": "healthy",
        "service": info.get("service", "uagent-service"),
        "version": info.get("version", "1.0.0"),
        "uptime_seconds": info.get("uptime_seconds", 3600),
    }


def compute_analytics(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Calculates LLM token usage and cost metrics.

    =============================================================================
    INTENTIONAL DEFECT FOR ASI:ONE TEST:
    Direct dictionary indexing on `payload["completion_tokens"]` raises a KeyError
    when the caller does not supply 'completion_tokens' in the request payload.

    Proposed fix via ASI:One self-healing:
        - completion_tokens = payload.get("completion_tokens", 0)
        + completion_tokens = payload.get("completion_tokens", 0)
    =============================================================================
    """
    prompt_tokens = payload.get("prompt_tokens", 0)

    # Intentional bug: Unsafe direct lookup
    completion_tokens = payload.get("completion_tokens", 0)

    total_tokens = prompt_tokens + completion_tokens
    estimated_cost = (prompt_tokens * 0.000015) + (completion_tokens * 0.00006)

    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(estimated_cost, 6),
        "status": "success",
    }
