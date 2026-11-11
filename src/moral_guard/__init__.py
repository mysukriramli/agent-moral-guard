"""Agent Moral Guard - Deterministic moral alignment engine with citation provenance."""

from .engine import MoralGuard
from .models import (
    ActionDomain,
    MoralEvaluationResult,
    MoralViolation,
    CitationRecord
)
from .citations import CITATION_REGISTRY, get_citation_for_source


def run_server():
    """Lazy launcher for MCP server."""
    from .server import main
    main()


__all__ = [
    "MoralGuard",
    "ActionDomain",
    "MoralEvaluationResult",
    "MoralViolation",
    "CitationRecord",
    "CITATION_REGISTRY",
    "get_citation_for_source",
    "run_server"
]
