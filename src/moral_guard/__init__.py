"""Agent Moral Guard - Deterministic moral alignment engine with citation provenance."""

from .engine import MoralGuard
from .models import (
    ActionDomain,
    MoralEvaluationResult,
    MoralViolation,
    CitationRecord
)
from .citations import CITATION_REGISTRY, get_citation_for_source
from .server import mcp, main as run_server

__all__ = [
    "MoralGuard",
    "ActionDomain",
    "MoralEvaluationResult",
    "MoralViolation",
    "CitationRecord",
    "CITATION_REGISTRY",
    "get_citation_for_source",
    "mcp",
    "run_server"
]
