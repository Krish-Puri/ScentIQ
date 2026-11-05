"""SCENTIQ Recommendation Schemas.
Conforms to PRD Section 12.3 and Section 13.
"""
import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RecommendationConstraints(BaseModel):
    liked_families: List[str] = Field(default_factory=list)
    liked_notes: List[str] = Field(default_factory=list)
    liked_accords: List[str] = Field(default_factory=list)
    avoid_terms: List[str] = Field(default_factory=list)  # Hard exclusions
    occasions: List[str] = Field(default_factory=list)
    climate: List[str] = Field(default_factory=list)
    budget_max_inr: Optional[float] = None
    hard_budget_limit: bool = True
    desired_intensity: Optional[str] = "moderate"
    concentration: List[str] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    constraints: RecommendationConstraints
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    limit: int = Field(5, ge=1, le=10)


class RecommendationCard(BaseModel):
    fragrance_id: uuid.UUID
    canonical_name: str
    brand_name: str
    concentration: str
    family: Optional[str] = None
    score: float
    fit_summary: str
    profile_match_cues: List[str] = Field(default_factory=list)
    tradeoffs_or_caveats: List[str] = Field(default_factory=list)
    indicative_price_inr: Optional[float] = None
    sample_first_recommended: bool = False
    evidence_completeness: float = 1.0


class RecommendationResponse(BaseModel):
    ruleset_version: str = "v1.0"
    results: List[RecommendationCard]
    session_id: str
    total_evaluated: int

