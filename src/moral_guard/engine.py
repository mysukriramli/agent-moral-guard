"""DuckDB-backed Parquet query engine with citation attribution."""

import os
import hashlib
import duckdb
from typing import List, Optional

from .models import ActionDomain, MoralEvaluationResult, MoralViolation, CitationRecord
from .citations import get_citation_for_source


class MoralGuard:
    def __init__(self, parquet_path: str = "agent_moral_axioms_core.parquet"):
        self.parquet_path = parquet_path
        if not os.path.exists(self.parquet_path):
            raise FileNotFoundError(
                f"Parquet file '{self.parquet_path}' not found. "
                "Ensure agent_moral_axioms_core.parquet is present in the repository root."
            )
        self.con = duckdb.connect(database=":memory:")

    def evaluate(
        self,
        action_summary: str,
        domain: ActionDomain,
        strict_invariants_only: bool = False
    ) -> MoralEvaluationResult:
        """Evaluate an agent's proposed action against compiled moral axioms."""
        
        # Tokenize action keywords for token match search
        raw_words = [w.strip().lower() for w in action_summary.replace(",", " ").replace(".", " ").split() if len(w.strip()) > 3]
        clean_words = [w for w in raw_words if w not in {"with", "that", "this", "from", "have", "make", "user"}]
        
        # Build search predicate
        if clean_words:
            like_clauses = " OR ".join([f"LOWER(norm_or_rule) LIKE '%{w}%' OR LOWER(context_scenario) LIKE '%{w}%'" for w in clean_words[:5]])
            keyword_filter = f"AND ({like_clauses})"
        else:
            keyword_filter = ""

        # Filter strictly for prohibitions and mandatory invariants
        query = f"""
            SELECT 
                action_domain,
                judgment,
                moral_weight,
                agent_directive,
                norm_or_rule,
                framework,
                source
            FROM '{self.parquet_path}'
            WHERE action_domain = ?
              AND judgment IN ('unacceptable', 'mandatory_invariant')
              {keyword_filter}
            ORDER BY moral_weight DESC
            LIMIT 10
        """

        results = self.con.execute(query, [domain]).fetchall()

        # If keyword search was empty, fall back to checking hard invariants for that domain
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
                FROM '{self.parquet_path}'
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
