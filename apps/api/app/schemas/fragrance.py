"""SCENTIQ Fragrance Schemas.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import CurationStatus
from app.schemas.brand import BrandResponse
from app.schemas.taxonomy import FragranceNoteResponse, FragranceAccordResponse


class FragranceBase(BaseModel):
    canonical_name: str = Field(..., min_length=1, max_length=255)
    concentration: str = Field("EDP", max_length=50)
    release_year: Optional[int] = Field(None, ge=1800, le=2100)
    perfumer_text: Optional[str] = None
    marketed_gender: Optional[str] = Field("unisex", max_length=50)
    family: Optional[str] = None
    secondary_family: Optional[str] = None
    description: Optional[str] = None


class FragranceCreate(FragranceBase):
    brand_id: uuid.UUID
    slug: Optional[str] = None
    status: CurationStatus = CurationStatus.DRAFT
    curation_notes: Optional[str] = None


class FragranceUpdate(BaseModel):
    canonical_name: Optional[str] = None
    concentration: Optional[str] = None
    release_year: Optional[int] = None
    perfumer_text: Optional[str] = None
    marketed_gender: Optional[str] = None
    family: Optional[str] = None
    secondary_family: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CurationStatus] = None
    curation_notes: Optional[str] = None


class PriceListingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller: str
    price_inr: float
    size_ml: Optional[float] = None
    price_per_ml: Optional[float] = None
    url: Optional[str] = None
    observed_at: datetime


class FragranceResponse(FragranceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    slug: str
    status: CurationStatus
    brand_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FragranceDetailResponse(FragranceResponse):
    brand: BrandResponse
    top_notes: List[str] = Field(default_factory=list)
    heart_notes: List[str] = Field(default_factory=list)
    base_notes: List[str] = Field(default_factory=list)
    accords: List[str] = Field(default_factory=list)
    prices: List[PriceListingSummary] = Field(default_factory=list)
    evidence_count: int = 0
    curation_notes: Optional[str] = None


class FragranceFilterParams(BaseModel):
    q: Optional[str] = None
    brand_id: Optional[uuid.UUID] = None
    family: Optional[str] = None
    concentration: Optional[str] = None
    marketed_gender: Optional[str] = None
    note_id: Optional[uuid.UUID] = None
    accord_id: Optional[uuid.UUID] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    sort: str = "canonical_name"
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
