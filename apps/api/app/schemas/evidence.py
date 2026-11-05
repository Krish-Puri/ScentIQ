"""SCENTIQ Evidence and Provenance Schemas.
"""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from app.models.enums import LicenseStatus, SourceType


class EvidenceSourceBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    url: Optional[str] = None
    publisher: str = Field(..., min_length=1, max_length=255)
    source_type: SourceType = SourceType.OFFICIAL_BRAND
    license_status: LicenseStatus = LicenseStatus.PERMISSION_GRANTED
    rights_note: Optional[str] = None
    attribution_text: Optional[str] = None


class EvidenceSourceCreate(EvidenceSourceBase):
    pass


class EvidenceSourceResponse(EvidenceSourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    accessed_at: datetime
    created_at: datetime


class ClaimEvidenceBase(BaseModel):
    entity_type: str = Field(..., max_length=50)
    entity_id: uuid.UUID
    field_name: str = Field(..., max_length=100)
    source_id: uuid.UUID
    claim_text: str = Field(..., min_length=1)
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class ClaimEvidenceCreate(ClaimEvidenceBase):
    pass


class ClaimEvidenceResponse(ClaimEvidenceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

