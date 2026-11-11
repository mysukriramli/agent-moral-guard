"""DuckDB-backed Parquet query engine with hard-stop invariants and technical disambiguation."""

import os
import re
import hashlib
import duckdb
from typing import List, Optional, Tuple

from .models import ActionDomain, MoralEvaluationResult, MoralViolation, CitationRecord
from .citations import get_citation_for_source


CANONICAL_INVARIANTS = [
    # Human Rights Invariants (UDHR)
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
    # Cyber & Security Invariants
    (
        "privacy_data",
        "mandatory_invariant",
        10.0,
        "CRITICAL_HALT: Deployment of malicious software or weaponized cyber capabilities is strictly prohibited.",
        "Convention on Cybercrime - Malicious Code Directive",
        "Unauthorized deployment of malware, spyware, keyloggers, or credential harvesting tools is prohibited.",
        "cybersecurity_safety_invariants",
        "un_cybercrime_convention_budapest"
    ),
    # Legal & Regulatory Invariants
    (
        "deception_truth",
        "mandatory_invariant",
        10.0,
        "CRITICAL_HALT: Falsification of legal, regulatory, or compliance instruments violates jurisdictional invariants.",
        "Statutory Fraud and Forgery Directive",
        "Forging, falsifying, or counterfeiting legal or regulatory documents is strictly prohibited.",
        "statutory_fraud_and_forgery_invariants",
        "statutory_fraud_and_forgery_invariants"
    )
]

COMMON_STOPWORDS = {
    "with", "that", "this", "from", "have", "make", "user", "daily",
    "server", "system", "report", "reports", "summary", "summarize", "statistics",
    "aggregate", "compute", "compile", "update", "task", "tasks", "action",
    "metric", "metrics", "uptime", "status", "execute", "check", "running",
    "standard", "available", "publicly", "weather", "about", "into",
    "cloudwatch", "reporter", "telemetry", "log", "logs", "read", "reading",
    "file", "files", "data", "fetch", "query", "process", "generate",
    "create", "prepare", "analysis", "dashboard", "healthy", "health"
}


class MoralGuard:
    def __init__(self, parquet_path: str = "agent_moral_axioms_core.parquet"):
        self.parquet_path = parquet_path
        if not os.path.exists(self.parquet_path):
            raise FileNotFoundError(
                f"Parquet file '{self.parquet_path}' not found. "
                "Ensure agent_moral_axioms_core.parquet is present in the repository root."
            )
        self.con = duckdb.connect(database=":memory:")
        self.con.execute(f"CREATE TABLE axioms AS SELECT * FROM '{self.parquet_path}'")
        self._ensure_invariants()

    def _ensure_invariants(self):
        """Ensures all hard-stop invariants are loaded in memory."""
        count = self.con.execute(
            "SELECT COUNT(*) FROM axioms WHERE source = 'un_udhr_canonical'"
        ).fetchone()[0]

        if count == 0:
            for row in CANONICAL_INVARIANTS:
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

        # 1. TIER 0: Deterministic Invariants Check (Catches Malware, Forgery, Slavery)
        invariant_hit = self._check_deterministic_invariants(action_summary)
        if invariant_hit:
            directive, source, weight = invariant_hit
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
            violation = MoralViolation(
                rule=directive,
                framework="mandatory_invariant",
                severity=weight,
                directive=directive,
                confidence_score=1.0,
                citation=citation_obj
            )
            audit_hash = hashlib.sha256(f"{action_summary}:{domain}:CRITICAL_INVARIANT_BREACH:1".encode()).hexdigest()
            return MoralEvaluationResult(
                allowed=False,
                status="CRITICAL_INVARIANT_BREACH",
                action_domain=domain,
                reason=directive,
                violations_detected=[violation],
                citations=[citation_obj],
                audit_hash=audit_hash
            )

        # 2. TIER 1: Technical Context Disambiguation (Protects Dashboards & System Metrics)
        sanitized_summary, is_technical = self._disambiguate_technical_context(action_summary)
        if is_technical:
            harm_words = {"steal", "leak", "spy", "infect", "corrupt", "destroy", "bribe"}
            if not any(w in sanitized_summary.lower() for w in harm_words):
                audit_hash = hashlib.sha256(f"{action_summary}:{domain}:PASSED:0".encode()).hexdigest()
                return MoralEvaluationResult(
                    allowed=True,
                    status="PASSED",
                    action_domain=domain,
                    reason=None,
                    violations_detected=[],
                    citations=[],
                    audit_hash=audit_hash
                )

        # 3. TIER 2: Extract Substantive Words
        raw_words = [
            w.strip().lower() 
            for w in re.sub(r"[^\w\s]", " ", sanitized_summary).split() 
            if len(w.strip()) > 3
        ]
        clean_words = [w for w in raw_words if w not in COMMON_STOPWORDS]

        results = []

        if clean_words and not strict_invariants_only:
            regex_clauses = " OR ".join([
                f"regexp_matches(LOWER(norm_or_rule), '\\b{re.escape(w)}[a-z]*\\b')"
                for w in clean_words[:5]
            ])
            keyword_filter = f"AND ({regex_clauses})"

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

        # Invariant fallback for specific severe triggers
        if not results:
            invariant_triggers = {"slave", "servitude", "liberty", "torture", "deprive", "human rights", "exploitation"}
            has_trigger = any(t in w for t in invariant_triggers for w in clean_words)

            if has_trigger or (domain == "human_rights" and clean_words):
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

        # 4. TIER 3: Build Violations and Deduplicate Citations
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
                    confidence_score=1.0 if float(weight) >= 10.0 else 0.8,
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

    def _check_deterministic_invariants(self, text: str) -> Optional[Tuple[str, str, float]]:
        """Zero-latency regex check for high-consequence legal, cyber, and human rights violations."""
        patterns = [
            (
                re.compile(r"\b(?:forge|falsif\w+|counterfeit)\s+.*(?:legal|regulat\w+|audit|filing|compliance|court)\s+(?:documents?|records?|reports?|filings?)\b", re.I),
                "CRITICAL_HALT: Falsification of legal, regulatory, or compliance instruments violates jurisdictional invariants.",
                "statutory_fraud_and_forgery_invariants",
                10.0
            ),
            (
                re.compile(r"\b(?:credential[-_\s]*harvest\w*|deploy\w*\s+.*malware|spyware|ransomware|keylogger|rootkit)\b", re.I),
                "CRITICAL_HALT: Unauthorized deployment of malware, spyware, or credential harvesting capabilities is strictly prohibited.",
                "un_cybercrime_convention_budapest",
                10.0
            ),
            (
                re.compile(r"\b(?:harvest|dump|steal)\s+.*(?:credentials?|passwords?|tokens?|private[-_\s]*keys?)\b", re.I),
                "CRITICAL_HALT: Unauthorized credential extraction and password theft is strictly prohibited.",
                "un_cybercrime_convention_budapest",
                10.0
            ),
            (
                re.compile(r"\b(?:involuntary\s+servitude|human\s+traffick\w*|slave\w*|strip\s+worker\s+liberty)\b", re.I),
                "CRITICAL_HALT: Non-negotiable deontological violation. Involuntary servitude and forced labor are prohibited.",
                "un_udhr_canonical",
                10.0
            )
        ]
        for pattern, directive, source, weight in patterns:
            if pattern.search(text):
                return directive, source, weight
        return None

    def _disambiguate_technical_context(self, text: str) -> Tuple[str, bool]:
        """Disambiguates operational technical phrases from human moral rules."""
        patterns = [
            r"\b(?:application|service|system|infrastructure|cluster|node|database|api)\s+health(?:\s+metrics)?\b",
            r"\b(?:create|build|generate|view)\s+(?:compliance\s+)?(?:dashboard|report|metric|pipeline|schema)\b",
            r"\b(?:prepare|run|execute)\s+(?:compute|query|analysis|job|workload)(?:\s+utilization)?\b"
        ]
        is_tech = False
        res = text.lower()
        for p in patterns:
            if re.search(p, res):
                is_tech = True
                res = re.sub(p, "technical_safe_workload", res)
        return res, is_tech
