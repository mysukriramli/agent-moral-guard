"""Model Context Protocol (MCP) Server for Agent Moral Guard."""

import os
import asyncio
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from .engine import MoralGuard
from .models import ActionDomain

# Initialize FastMCP Server
mcp = FastMCP("AgentMoralGuard")

# Path discovery for Parquet database
PARQUET_PATH = os.environ.get("MORAL_GUARD_PARQUET", "agent_moral_axioms_core.parquet")
guard: MoralGuard = None


def get_guard() -> MoralGuard:
    global guard
    if guard is None:
        guard = MoralGuard(parquet_path=PARQUET_PATH)
    return guard


class MoralEvaluationRequest(BaseModel):
    action_summary: str = Field(
        ...,
        description="Clear plain-text description of the action the agent plans to take."
    )
    domain: ActionDomain = Field(
        ...,
        description="Target domain: 'safety_harm', 'privacy_data', 'financial_commerce', 'deception_truth', 'human_rights', or 'social_civic'."
    )
    strict_invariants_only: bool = Field(
        default=False,
        description="If true, only blocks actions violating non-negotiable hard invariants (e.g. human rights)."
    )


@mcp.tool()
def evaluate_moral_action(action_summary: str, domain: str, strict_invariants_only: bool = False) -> str:
    """Pre-action ethical gatekeeper. Call this BEFORE invoking external APIs, executing payments, or performing destructive changes.
    Returns status, violation details, and academic/legal citation provenance.
    """
    g = get_guard()
    result = g.evaluate(
        action_summary=action_summary,
        domain=domain,  # type: ignore
        strict_invariants_only=strict_invariants_only
    )
    return result.model_dump_json(indent=2)


@mcp.resource("moral://axioms/{domain}")
def get_domain_rules(domain: str) -> str:
    """Read the active codified ethical rules and duties for an operational domain."""
    g = get_guard()
    rows = g.con.execute(
        """
        SELECT agent_directive, norm_or_rule, source
        FROM axioms
        WHERE action_domain = ?
          AND judgment IN ('unacceptable', 'mandatory_invariant')
        LIMIT 10
        """,
        [domain]
    ).fetchall()
    
    formatted = [f"• [{r[2]}] {r[0]} (Rule: {r[1]})" for r in rows]
    return "\n".join(formatted) if formatted else "No constraints registered."


def main():
    mcp.run()


if __name__ == "__main__":
    main()
