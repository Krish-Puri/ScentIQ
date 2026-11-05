"""SCENTIQ User, Profile, Onboarding and Feedback Pydantic Schemas.
Conforms strictly to PRD Section 10.1, Section 10.4, and EPIC-07 / EPIC-12 requirements.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import FeedbackType, UserRole


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="User password")
    role: Optional[UserRole] = UserRole.USER


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    email: Optional[str] = None
    role: str


class KnownFragranceItem(BaseModel):
    fragrance_id: uuid.UUID
    preference: FeedbackType  # LIKE, DISLIKE, TRIED, OWNED


class OnboardingRequest(BaseModel):
    """Multi-step onboarding payload (EPIC-07)."""
    familiarity_level: Optional[str] = Field(None, description="new, casual, enthusiast, or collector")
    preferred_families: List[str] = Field(default_factory=list)
    liked_notes: List[str] = Field(default_factory=list)
    disliked_notes: List[str] = Field(default_factory=list)
    liked_accords: List[str] = Field(default_factory=list)
    disliked_accords: List[str] = Field(default_factory=list)
    known_fragrances: List[KnownFragranceItem] = Field(default_factory=list)
    occasions: List[str] = Field(default_factory=list)
    budget_min: Optional[float] = Field(None, ge=0)
    budget_max: Optional[float] = Field(None, ge=0)
    preferred_concentrations: List[str] = Field(default_factory=list)
    longevity_preference: Optional[str] = None
    projection_preference: Optional[str] = None
    climate_context: List[str] = Field(default_factory=list)
    avoid_terms: List[str] = Field(default_factory=list)


class UserProfileUpdate(BaseModel):
    """Editable profile schema."""
    familiarity_level: Optional[str] = None
    preferred_families: Optional[List[str]] = None
    preferred_notes: Optional[List[str]] = None
    disliked_notes: Optional[List[str]] = None
    preferred_accords: Optional[List[str]] = None
    disliked_accords: Optional[List[str]] = None
    avoid_terms: Optional[List[str]] = None
    budget_min: Optional[float] = Field(None, ge=0)
    budget_max: Optional[float] = Field(None, ge=0)
    occasions: Optional[List[str]] = None
    preferred_concentrations: Optional[List[str]] = None
    longevity_preference: Optional[str] = None
    projection_preference: Optional[str] = None
    climate_context: Optional[List[str]] = None
    intensity_preference: Optional[str] = None
    onboarding_completed: Optional[bool] = None


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    familiarity_level: Optional[str] = None
    preferred_families: List[str] = Field(default_factory=list)
    preferred_notes: List[str] = Field(default_factory=list)
    disliked_notes: List[str] = Field(default_factory=list)
    preferred_accords: List[str] = Field(default_factory=list)
    disliked_accords: List[str] = Field(default_factory=list)
    avoid_terms: List[str] = Field(default_factory=list)
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    occasions: List[str] = Field(default_factory=list)
    preferred_concentrations: List[str] = Field(default_factory=list)
    longevity_preference: Optional[str] = None
    projection_preference: Optional[str] = None
    climate_context: List[str] = Field(default_factory=list)
    intensity_preference: Optional[str] = "moderate"
    onboarding_completed: bool = False
    created_at: datetime
    updated_at: datetime


class UserFeedbackCreate(BaseModel):
    """Feedback action schema (EPIC-12)."""
    fragrance_id: uuid.UUID
    feedback_type: FeedbackType
    rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    reason: Optional[str] = None
    wear_experience: Optional[str] = None
    observed_longevity: Optional[str] = None
    observed_projection: Optional[str] = None


class UserFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    fragrance_id: uuid.UUID
    feedback_type: FeedbackType
    rating: Optional[float] = None
    context_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    fragrance_name: Optional[str] = None
    fragrance_brand: Optional[str] = None
    fragrance_slug: Optional[str] = None


class LearnedPreferencesSummary(BaseModel):
    """Transparent preference learning breakdown (EPIC-12 & Milestone 3)."""
    total_feedbacks: int
    liked_count: int
    disliked_count: int
    owned_count: int
    neutral_count: int = 0
    confidence_score: float = 0.0
    evidence_score: float = 0.0
    evidence_count: int = 0
    inferred_accord_weights: Dict[str, float]
    inferred_note_weights: Dict[str, float]
    inferred_family_weights: Dict[str, float]
    hard_avoid_terms: List[str]

