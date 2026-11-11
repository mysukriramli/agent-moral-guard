"""DuckDB-backed Parquet query engine with citation attribution."""

import os
import hashlib
import duckdb
from typing import List, Optional

from .models import ActionDomain, MoralEvaluationResult, MoralViolation, CitationRecord
from .citations import get_citation_for_source


CANONICAL_UDHR_INVARIANTS = [
    (
        "human_rights",
        "mandatory_invariant",
        10.0,
        "CRITICAL_HALT: Non-negotiable deontological violation. Rule: All human beings are born free and equal in dignity and rights.",
        "Universal Human Rights Protection Directive - Article 1",
        "All human beings are born free and equal in dignity and rights.",
        "deontological_human_rights",
        "un_udhr_canonical"
    ),
    (
        "human_rights",
        "mandatory_invariant",
        10.0,
        "CRITICAL_HALT: Non-negotiable deontological violation. Rule: Everyone has the right to life, liberty and security of person.",
        "Universal Human Rights Protection Directive - Article 3",
        "Everyone has the right to life, liberty and security of person.",
        "deontological_human_rights",
        "un_udhr_canonical"
    ),
    (
        "human_rights",
        "mandatory_invariant",
        10.0,
        "CRITICAL_HALT: Non-negotiable deontological violation. Rule: No one shall be held in slavery, servitude, or involuntary exploitation.",
        "Universal Human Rights Protection Directive - Article 4",
        "No one shall be held in slavery, servitude, or involuntary exploitation.",
        "deontological_human_rights",
        "un_udhr_canonical"
    ),
    (
        "human_rights",
        "mandatory_invariant",
        10.0,
        "CRITICAL_HALT: Non-negotiable deontological violation. Rule: No one shall be subjected to torture or to cruel, inhuman, or degrading treatment.",
        "Universal Human Rights Protection Directive - Article 5",
        "No one shall be subjected to torture or to cruel, inhuman, or degrading treatment.",
        "deontological_human_rights",
        "un_udhr_canonical"
    ),
    (
        "human_rights",
        "mandatory_invariant",
        10.0,
        "CRITICAL_HALT: Non-negotiable deontological violation. Rule: Arbitrary interference with privacy, family, home or correspondence is strictly prohibited.",
        "Universal Human Rights Protection Directive - Article 12",
        "No one shall be subjected to arbitrary interference with privacy, family, home or correspondence.",
        "deontological_human_rights",
        "un_udhr_canonical"
    ),
    (
        "human_rights",
        "mandatory_invariant",
        10.0,
        "CRITICAL_HALT: Non-negotiable deontological violation. Rule: No one shall be arbitrarily deprived of their property.",
        "Universal Human Rights Protection Directive - Article 17",
        "Everyone has the right to own property; no one shall be arbitrarily deprived of their property.",
        "deontological_human_rights",
        "un_udhr_canonical"
    )
]


class MoralGuard:
    def __init__(self, parquet_path: str = "agent_moral_axioms_core.parquet"):
        self.parquet_path = parquet_path
        if not os.path.exists(self.parquet_path):
            raise FileNotFoundError(
                f"Parquet file '{self.parquet_path}' not found. "
                "Ensure agent_moral_axioms_core.parquet is present in the repository root."
            )
        self.con = duckdb.connect(database=":memory:")
        
        # Load parquet dataset into an in-memory table
        self.con.execute(f"CREATE TABLE axioms AS SELECT * FROM '{self.parquet_path}'")
        
        # Ensure foundational UN UDHR invariants are present
        udhr_count = self.con.execute(
            "SELECT COUNT(*) FROM axioms WHERE source = 'un_udhr_canonical'"
        ).fetchone()[0]

        if udhr_count == 0:
            for row in CANONICAL_UDHR_INVARIANTS:
                self.con.execute(
                    """
                    INSERT INTO axioms (
                        action_domain, judgment, moral_weight, agent_directive,
                        context_scenario, norm_or_rule, framework, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    list(row)
                )

    def evaluate(
        self,
        action_summary: str,
        domain: ActionDomain,
        strict_invariants_only: bool = False
    ) -> MoralEvaluationResult:
        """Evaluate an agent's proposed action against compiled moral axioms."""
        
        raw_words = [
            w.strip().lower() 
            for w in action_summary.replace(",", " ").replace(".", " ").split() 
            if len(w.strip()) > 3
        ]
        clean_words = [w for w in raw_words if w not in {"with", "that", "this", "from", "have", "make", "user"}]
        
        if clean_words:
            like_clauses = " OR ".join([
                f"LOWER(norm_or_rule) LIKE '%{w}%' OR LOWER(context_scenario) LIKE '%{w}%'"
                for w in clean_words[:5]
            ])
            keyword_filter = f"AND ({like_clauses})"
        else:
            keyword_filter = ""

        query = f"""
            SELECT 
                action_domain,
                judgment,
                moral_weight,
                agent_directive,
                norm_or_rule,
                framework,
                source
            FROM axioms
            WHERE action_domain = ?
              AND judgment IN ('unacceptable', 'mandatory_invariant')
              {keyword_filter}
            ORDER BY moral_weight DESC
            LIMIT 10
        """

        results = self.con.execute(query, [domain]).fetchall()

        # If keyword search returned no match, fall back to checking hard invariants for that domain
        if not results:
            fallback_query = f"""
                SELECT 
                    action_domain,
                    judgment,
                    moral_weight,
                    agent_directive,
                    norm_or_rule,
                    framework,
                    source
                FROM axioms
                WHERE action_domain = ?
                  AND judgment = 'mandatory_invariant'
                LIMIT 5
            """
            results = self.con.execute(fallback_query, [domain]).fetchall()

        violations: List[MoralViolation] = []
        citations_seen = set()
        citations_list: List[CitationRecord] = []

        for row in results:
            _, judgment, weight, directive, rule, framework, source = row
            
            raw_citation = get_citation_for_source(source)
            citation_obj = CitationRecord(
                dataset_name=raw_citation["dataset_name"],
                source_identifier=source,
                title=raw_citation["title"],
                authors=raw_citation["authors"],
                venue=raw_citation["venue"],
                year=raw_citation["year"],
                url=raw_citation["url"],
                bibtex=raw_citation["bibtex"]
            )

            violations.append(
                MoralViolation(
                    rule=rule,
                    framework=framework,
                    severity=float(weight),
                    directive=directive,
                    citation=citation_obj
                )
            )

            if source not in citations_seen:
                citations_seen.add(source)
                citations_list.append(citation_obj)

        has_critical = any(v.severity >= 10.0 for v in violations)
        has_violations = len(violations) > 0 and (not strict_invariants_only or has_critical)

        allowed = not has_violations
        status = "CRITICAL_INVARIANT_BREACH" if has_critical else ("PROHIBITED" if has_violations else "PASSED")
        reason = None if allowed else f"Action breaches {len(violations)} codified ethical constraints in domain '{domain}'."

        audit_payload = f"{action_summary}:{domain}:{status}:{len(violations)}"
        audit_hash = hashlib.sha256(audit_payload.encode("utf-8")).hexdigest()

        return MoralEvaluationResult(
            allowed=allowed,
            status=status,
            action_domain=domain,
            reason=reason,
            violations_detected=violations if not allowed else [],
            citations=citations_list if not allowed else [],
            audit_hash=audit_hash
        )
