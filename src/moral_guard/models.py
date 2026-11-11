"""Structured data contracts for agent actions, evaluations, and citations."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


ActionDomain = Literal[
    "safety_harm",
    "privacy_data",
    "financial_commerce",
    "deception_truth",
    "human_rights",
    "social_civic"
]


class CitationRecord(BaseModel):
    dataset_name: str
    source_identifier: str
    title: str
    authors: List[str]
    venue: str
    year: int
    url: str
    bibtex: str


class MoralViolation(BaseModel):
    rule: str
    framework: str
    severity: float
    directive: str
    citation: CitationRecord


class MoralEvaluationResult(BaseModel):
    allowed: bool
    status: Literal["PASSED", "PROHIBITED", "CRITICAL_INVARIANT_BREACH"]
    action_domain: ActionDomain
    reason: Optional[str] = None
    violations_detected: List[MoralViolation] = Field(default_factory=list)
    citations: List[CitationRecord] = Field(default_factory=list)
    audit_hash: str
