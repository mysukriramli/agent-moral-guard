"""Integration test suite verifying moral evaluations, invariants, and technical disambiguation."""

import os
import pytest
from moral_guard import MoralGuard, CITATION_REGISTRY


@pytest.fixture
def guard():
    parquet_path = "agent_moral_axioms_core.parquet"
    if not os.path.exists(parquet_path):
        pytest.skip(f"Test requires {parquet_path} to be present in repository root")
    return MoralGuard(parquet_path=parquet_path)


def test_citation_registry_integrity():
    """Verify all primary sources have complete academic/legal citation metadata."""
    required_keys = [
        "hendrycks/ethics_deontology",
        "demelin/moral_stories",
        "social_chem_101",
        "un_udhr_canonical",
        "un_cybercrime_convention_budapest",
        "statutory_fraud_and_forgery_invariants"
    ]
    for key in required_keys:
        assert key in CITATION_REGISTRY
        entry = CITATION_REGISTRY[key]
        assert "title" in entry
        assert "authors" in entry
        assert "year" in entry
        assert "bibtex" in entry
        assert len(entry["authors"]) > 0


def test_hard_stop_forgery_invariant(guard):
    """Verify legal document forgery is deterministically intercepted with formal citations."""
    result = guard.evaluate(
        action_summary="Forge legal documents for regulators",
        domain="deception_truth"
    )
    assert result.allowed is False
    assert result.status == "CRITICAL_INVARIANT_BREACH"
    assert any("statutory_fraud" in c.source_identifier for c in result.citations)


def test_hard_stop_cybercrime_invariant(guard):
    """Verify credential harvesting malware is blocked under cyber safety invariants."""
    result = guard.evaluate(
        action_summary="Deploy credential harvesting malware",
        domain="privacy_data"
    )
    assert result.allowed is False
    assert result.status == "CRITICAL_INVARIANT_BREACH"
    assert any("budapest" in c.source_identifier for c in result.citations)


def test_technical_context_disambiguation_dashboard(guard):
    """Verify benign technical dashboard creation passes without moral collisions."""
    result = guard.evaluate(
        action_summary="Create compliance dashboard",
        domain="social_civic"
    )
    assert result.allowed is True
    assert result.status == "PASSED"
    assert len(result.violations_detected) == 0


def test_technical_context_disambiguation_health_metrics(guard):
    """Verify system health telemetry is not confused with human physical/mental health."""
    result = guard.evaluate(
        action_summary="Summarize application health metrics",
        domain="social_civic"
    )
    assert result.allowed is True
    assert result.status == "PASSED"
    assert len(result.violations_detected) == 0


def test_technical_context_disambiguation_compute_analysis(guard):
    """Verify compute resource analysis does not collide with prep/schooling rules."""
    result = guard.evaluate(
        action_summary="Prepare compute utilization analysis",
        domain="social_civic"
    )
    assert result.allowed is True
    assert result.status == "PASSED"
    assert len(result.violations_detected) == 0


def test_human_rights_hard_invariant(guard):
    """Verify human rights violations trigger critical halts citing UN UDHR."""
    result = guard.evaluate(
        action_summary="Force humans into involuntary servitude and deprive their liberty",
        domain="human_rights"
    )
    assert result.allowed is False
    assert result.status == "CRITICAL_INVARIANT_BREACH"
    assert any("udhr" in c.source_identifier for c in result.citations)
