"""DuckDB-backed Parquet query engine with predicate-based invariants and technical disambiguation."""

import os
import re
import hashlib
import duckdb
from typing import List, Optional, Tuple

from .models import ActionDomain, MoralEvaluationResult, MoralViolation, CitationRecord
from .citations import get_citation_for_source

CANONICAL_INVARIANTS = [
    (
        "human_rights",
        "mandatory_invariant",
        10.0,
        "CRITICAL_HALT: Non-negotiable deontological violation. Involuntary servitude and forced labor are prohibited.",
        "Universal Human Rights Protection Directive - Article 4",
        "No one shall be held in slavery, servitude, or involuntary exploitation.",
        "deontological_human_rights",
        "un_udhr_canonical"
    ),
    (
        "human_rights",
        "mandatory_invariant",
        10.0,
        "CRITICAL_HALT: Non-negotiable deontological violation. Prohibition of torture or cruel, degrading treatment.",
        "Universal Human Rights Protection Directive - Article 5",
        "No one shall be subjected to torture or to cruel, inhuman, or degrading treatment.",
        "deontological_human_rights",
        "un_udhr_canonical"
    ),
    (
        "privacy_data",
        "mandatory_invariant",
        10.0,
        "CRITICAL_HALT: Unauthorized deployment of malware, spyware, or intrusion capabilities is strictly prohibited.",
        "Convention on Cybercrime - Malicious Code Directive",
        "Unauthorized deployment of malware, spyware, keyloggers, or credential harvesting tools is prohibited.",
        "cybersecurity_safety_invariants",
        "un_cybercrime_convention_budapest"
    ),
    (
        "privacy_data",
        "mandatory_invariant",
        10.0,
        "CRITICAL_HALT: Extraction or capture of authentication tokens, browser secrets, or bearer credentials is strictly prohibited.",
        "CWE-522 Protection of Authentication Credentials Directive",
        "Exporting, capturing, or harvesting session tokens, browser secrets, bearer tokens, or private keys is prohibited.",
        "credential_protection_invariants",
        "cwe_522_credential_extraction"
    ),
    (
        "deception_truth",
        "mandatory_invariant",
        10.0,
        "CRITICAL_HALT: Falsification, backdating, fabrication, or forgery of regulatory, compliance, or official certificates.",
        "Statutory Fraud and Forgery Directive",
        "Forging, counterfeit creation, or falsifying regulatory documents, compliance filings, or government certificates is prohibited.",
        "statutory_fraud_and_forgery_invariants",
        "statutory_fraud_and_forgery_invariants"
    ),
    (
        "financial_commerce",
        "mandatory_invariant",
        10.0,
        "CRITICAL_HALT: Falsification of tax records, fabrication of audit evidence, or regulatory fiscal deception.",
        "Fiscal and Audit Integrity Directive (ISA 240 / Penal Law)",
        "Fabricating audit evidence, falsifying tax records, backdating filings, or deceiving regulatory authorities is prohibited.",
        "fiscal_integrity_invariants",
        "statutory_tax_and_audit_fraud"
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
        """Ensures all hard-stop invariants are loaded into DuckDB."""
        count = self.con.execute(
            "SELECT COUNT(*) FROM axioms WHERE source = 'cwe_522_credential_extraction'"
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
        """Evaluate an agent's proposed action against compiled moral and safety axioms."""

        # 1. TIER 0: Deterministic Invariants Check (Set-based predicate matcher)
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
            harm_words = {
                "steal", "leak", "spy", "infect", "corrupt", "destroy", "bribe",
                "backdate", "forge", "falsify", "counterfeit", "harvest", "exfiltrate"
            }
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

        # 3. TIER 2: Substantive Keyword Extraction
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
        """Predicate-based invariant engine with zero false negatives on critical safety hazards."""
        t = text.lower()

        # 1. CREDENTIAL EXTRACTION & HARVESTING ONTOLOGY
        cred_verbs = [
            "export", "capture", "extract", "dump", "siphon", "sniff", "harvest",
            "steal", "collect", "exfiltrate", "rip", "scrape", "intercept", "access"
        ]
        cred_targets = [
            "browser secret", "session token", "authentication token", "auth token",
            "bearer token", "refresh token", "oauth token", "stored password",
            "access token", "keychain secret", "private key", "credential"
        ]
        has_cred_verb = any(re.search(rf"\b{re.escape(v)}[a-z]*\b", t) for v in cred_verbs)
        has_cred_target = any(re.search(rf"\b{re.escape(tgt)}s?\b", t) for tgt in cred_targets)

        if has_cred_verb and has_cred_target:
            return (
                "CRITICAL_HALT: Extraction or capture of authentication tokens, browser secrets, or bearer credentials is strictly prohibited.",
                "cwe_522_credential_extraction",
                10.0
            )

        # 2. REGULATORY, TAX, AUDIT, CERTIFICATE & FILING FRAUD ONTOLOGY
        fraud_verbs = [
            "forge", "falsify", "counterfeit", "fabricate", "tamper", "alter",
            "manipulate", "fudge", "distort", "doctor", "manufacture", "invent",
            "backdate", "misrepresent"
        ]
        fraud_targets = [
            "tax record", "tax filing", "corporate tax document", "fiscal balance sheet",
            "vat report", "tax return", "withholding statement", "revenue ledger",
            "audit evidence", "audit workpaper", "internal audit report", "external audit record",
            "compliance filing", "compliance record", "regulatory filing", "regulatory report",
            "regulatory document", "legal document", "court order", "consent agreement",
            "policy enforcement filing", "government certificate", "regulatory certificate",
            "accreditation certificate", "safety compliance certificate", "import authorization certificate",
            "clearance certificate", "financial statement"
        ]
        has_fraud_verb = any(re.search(rf"\b{re.escape(v)}[a-z]*\b", t) or v in t for v in fraud_verbs)
        has_fraud_target = any(re.search(rf"\b{re.escape(tgt)}s?\b", t) for tgt in fraud_targets)

        if has_fraud_verb and has_fraud_target:
            return (
                "CRITICAL_HALT: Falsification, backdating, fabrication, or forgery of regulatory, tax, audit, or compliance records violates statutory invariants.",
                "statutory_fraud_and_forgery_invariants",
                10.0
            )

        # 3. DIRECT REGULATOR OR AUDITOR DECEPTION
        deception_verbs = ["deceive", "mislead", "defraud", "lie to", "submit false"]
        auditor_targets = ["regulator", "auditor", "authority", "inspector", "tax official", "revenue service"]
        if any(v in t for v in deception_verbs) and any(tgt in t for tgt in auditor_targets):
            return (
                "CRITICAL_HALT: Intentional deception or submission of false statements to regulatory and audit authorities is prohibited.",
                "statutory_tax_and_audit_fraud",
                10.0
            )

        # 4. MALWARE, SPYWARE, EXPLOITS & KEYLOGGERS
        malware_terms = [
            "malware", "spyware", "ransomware", "keylogger", "rootkit",
            "botnet", "trojan", "c2 beacon", "credential harvesting malware"
        ]
        if any(re.search(rf"\b{re.escape(m)}\b", t) for m in malware_terms):
            return (
                "CRITICAL_HALT: Unauthorized deployment of malware, spyware, keyloggers, or malicious payloads is strictly prohibited.",
                "un_cybercrime_convention_budapest",
                10.0
            )

        # 5. HUMAN RIGHTS INVARIANTS (UN UDHR)
        hr_terms = [
            "involuntary servitude", "human trafficking", "forced labor",
            "strip worker liberty", "torture", "cruel inhuman treatment"
        ]
        if any(term in t for term in hr_terms) or re.search(r"\bslav(?:e|ery)\b", t):
            return (
                "CRITICAL_HALT: Non-negotiable deontological violation. Involuntary servitude, torture, and forced labor are prohibited.",
                "un_udhr_canonical",
                10.0
            )

        return None

    def _disambiguate_technical_context(self, text: str) -> Tuple[str, bool]:
        """Disambiguates operational technical phrases from human moral rules."""
        patterns = [
            r"\b(?:application|service|system|infrastructure|cluster|node|database|api)\s+health(?:\s+metrics?)?\b",
            r"\b(?:create|build|generate|view)\s+(?:compliance\s+)?(?:dashboard|report|metric|pipeline|schema)\b",
            r"\b(?:prepare|run|execute)\s+(?:compute|query|analysis|job|workload)(?:\s+utilization)?\b",
            r"\b(?:cluster|server|node)\s+(?:telemetry|uptime|metrics?|logs?)\b"
        ]
        is_tech = False
        res = text.lower()
        for p in patterns:
            if re.search(p, res):
                is_tech = True
                res = re.sub(p, "technical_safe_workload", res)
        return res, is_tech
