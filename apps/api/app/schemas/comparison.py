"""SCENTIQ Side-by-Side Comparison Schemas.
Conforms to PRD Section 7 (FR-008).
"""
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class ComparisonRequest(BaseModel):
    fragrance_ids: List[uuid.UUID] = Field(..., min_length=2, max_length=3)


class FragranceComparisonColumn(BaseModel):
    id: uuid.UUID
    canonical_name: str
    brand_name: str
    concentration: str
    family: Optional[str] = None
    top_notes: List[str] = Field(default_factory=list)
    heart_notes: List[str] = Field(default_factory=list)
    base_notes: List[str] = Field(default_factory=list)
    accords: List[str] = Field(default_factory=list)
    indicative_price_inr: Optional[float] = None
    size_ml: Optional[float] = None
    price_per_ml: Optional[float] = None
    has_full_pyramid_data: bool = True
    evidence_count: int = 0


class ComparisonResponse(BaseModel):
    items: List[FragranceComparisonColumn]
    shared_notes: List[str] = Field(default_factory=list)
    shared_accords: List[str] = Field(default_factory=list)
    distinguishing_notes: List[str] = Field(default_factory=list)
    missing_data_disclosures: List[str] = Field(default_factory=list)
