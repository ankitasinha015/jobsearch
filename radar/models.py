"""Single source of truth for the Job schema (eng review D4).

Validated at every boundary: normalize output, golden_set load, score input.
"""
from __future__ import annotations

import hashlib
from typing import Literal, Optional

from pydantic import BaseModel, Field, conint

Provenance = Literal["stated", "inferred", "unknown"]
RemoteStatus = Literal["remote", "hybrid", "onsite", "unknown"]


class Job(BaseModel):
    title: str
    company: str
    normalized_title: str = ""
    normalized_company: str = ""
    location: str = "unknown"
    remote_status: RemoteStatus = "unknown"
    remote_status_provenance: Provenance = "unknown"
    employment_type: str = "unknown"
    description: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = None
    date_posted: Optional[str] = None  # ISO date, None = unknown
    source: str
    source_type: Literal["ats", "aggregator", "golden_set"]
    ats: Optional[str] = None
    source_url: str
    canonical_url: str

    def model_post_init(self, __context) -> None:
        if not self.normalized_company:
            self.normalized_company = _norm(self.company)
        if not self.normalized_title:
            self.normalized_title = _norm(self.title)

    @property
    def job_key(self) -> str:
        """Identity of the role: company + title + location."""
        raw = f"{self.normalized_company}|{self.normalized_title}|{_norm(self.location)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:20]

    @property
    def content_hash(self) -> str:
        """Identity of the content: changes when the posting meaningfully changes."""
        raw = "|".join([
            self.normalized_company, self.normalized_title, _norm(self.location),
            self.description.strip(), str(self.salary_min), str(self.salary_max),
        ])
        return hashlib.sha256(raw.encode()).hexdigest()[:20]


def _norm(s: str) -> str:
    return " ".join((s or "").lower().replace(",", " ").replace("-", " ").split())


# What the LLM returns — dimension ratings + evidence. Overall and tier are
# computed in Python (BUILDSPEC: "the LLM never assigns overall or tier").
LLM_DIMENSIONS = [
    "functional_responsibility_match",
    "seniority_scope_match",
    "product_domain_match",
    "skills_experience_match",
    "location_work_arrangement",
    "industry_mission_match",
    "compensation_match",
    "company_stage_match",
]  # posting_freshness is computed mechanically in Python


class LLMEvaluation(BaseModel):
    dimension_scores: dict[str, conint(ge=0, le=10)]
    reasons: list[str] = Field(min_length=2, max_length=4)
    concerns: list[str] = Field(max_length=3)
    confidence: Literal["high", "medium", "low"]
    recommendation: Literal["strongly_review", "review", "consider", "low_priority"]

    def model_post_init(self, __context) -> None:
        missing = [d for d in LLM_DIMENSIONS if d not in self.dimension_scores]
        if missing:
            raise ValueError(f"missing dimension scores: {missing}")
