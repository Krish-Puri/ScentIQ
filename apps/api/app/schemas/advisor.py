"""SCENTIQ AI Fragrance Advisor Pydantic Schemas.
Conforms strictly to PRD Section 12.3 and EPIC-11.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.recommendation import RecommendationCard


class AdvisorParseRequest(BaseModel):
    message: str = Field(..., min_length=2, description="Natural language query from user")
    session_id: Optional[str] = "advisor-session"


class ParsedAdvisorIntent(BaseModel):
    budget_max: Optional[float] = None
    currency: str = "INR"
    preferred_families: List[str] = Field(default_factory=list)
    preferred_accords: List[str] = Field(default_factory=list)
    preferred_notes: List[str] = Field(default_factory=list)
    excluded_characteristics: List[str] = Field(default_factory=list)
    occasions: List[str] = Field(default_factory=list)
    concentration: List[str] = Field(default_factory=list)
    climate_context: List[str] = Field(default_factory=list)
    reference_fragrances: List[str] = Field(default_factory=list)
    is_alternative_search: bool = False
    target_longevity: Optional[str] = None
    is_ambiguous: bool = False
    clarification_needed: bool = False
    clarification_prompt: Optional[str] = None
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    parsed_via: str = "deterministic_rule_parser"


class AdvisorRecommendRequest(BaseModel):
    message: str = Field(..., min_length=2, description="Natural language query from user")
    session_id: Optional[str] = "advisor-session"
    include_profile: bool = True
    limit: int = Field(5, ge=1, le=20)


class AdvisorRecommendResponse(BaseModel):
    parsed_intent: ParsedAdvisorIntent
    recommendations: List[RecommendationCard]
    explanation: str
    applied_avoid_terms: List[str]
    session_id: str
    clarification_needed: bool = False
    clarification_prompt: Optional[str] = None
    conflict_detected: bool = False
    conflict_details: Optional[str] = None

