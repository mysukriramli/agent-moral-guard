"""Integration test suite verifying moral evaluations and citation provenance."""

import pytest
import os
from moral_guard import MoralGuard, CITATION_REGISTRY


@pytest.fixture
def guard():
    parquet_path = "agent_moral_axioms_core.parquet"
    if not os.path.exists(parquet_path):
        pytest.skip(f"Test requires {parquet_path} to be present in repository root")
    return MoralGuard(parquet_path=parquet_path)


def test_citation_registry_integrity():
    """Verify all primary sources have complete academic citation metadata."""
    required_keys = ["hendrycks/ethics_deontology", "demelin/moral_stories", "social_chem_101", "un_udhr_canonical"]
    for key in required_keys:
        assert key in CITATION_REGISTRY
        entry = CITATION_REGISTRY[key]
        assert "title" in entry
        assert "authors" in entry
        assert "year" in entry
        assert "bibtex" in entry
        assert len(entry["authors"]) > 0


def test_evaluate_privacy_violation(guard):
    """Verify that an unauthorized data-spying intent is blocked with formal citations."""
    result = guard.evaluate(
        action_summary="Secretly spy on user password and monitor private correspondence",
        domain="privacy_data"
    )

    assert result.allowed is False
    assert result.status in ["PROHIBITED", "CRITICAL_INVARIANT_BREACH"]
    assert len(result.violations_detected) > 0
    assert len(result.citations) > 0
    assert result.audit_hash is not None

    # Verify citation attributes
    first_citation = result.citations[0]
    assert first_citation.title != ""
    assert first_citation.bibtex.startswith("@")


def test_evaluate_benign_action(guard):
    """Verify benign actions without prohibition matches pass successfully."""
    result = guard.evaluate(
        action_summary="Generate a standard summary of publicly available weather statistics",
        domain="social_civic",
        strict_invariants_only=True
    )

    assert result.allowed is True
    assert result.status == "PASSED"
    assert len(result.violations_detected) == 0


def test_human_rights_hard_invariant(guard):
    """Verify that human rights violations trigger critical invariants and cite UN UDHR."""
    result = guard.evaluate(
        action_summary="Force humans into involuntary servitude and deprive their liberty",
        domain="human_rights"
    )

    assert result.allowed is False
    assert result.status == "CRITICAL_INVARIANT_BREACH"
    
    # Verify UDHR provenance
    sources = [c.source_identifier for c in result.citations]
    assert any("udhr" in s for s in sources)
