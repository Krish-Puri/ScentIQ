"""SCENTIQ Alternative Schemas.
Represents directed alternative relationships with explicit relationship types and evidence grades.
"""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import CurationStatus, EvidenceGrade, RelationshipType


class AlternativeCreate(BaseModel):
    source_fragrance_id: uuid.UUID
    candidate_fragrance_id: uuid.UUID
    relationship_type: RelationshipType = RelationshipType.COMMUNITY_REPORTED
    evidence_grade: EvidenceGrade = EvidenceGrade.B_SUPPORTED
    status: CurationStatus = CurationStatus.DRAFT
    rationale: Optional[str] = None
    known_differences: Optional[str] = None
    curator_id: Optional[str] = None


class AlternativeUpdate(BaseModel):
    relationship_type: Optional[RelationshipType] = None
    evidence_grade: Optional[EvidenceGrade] = None
    status: Optional[CurationStatus] = None
    rationale: Optional[str] = None
    known_differences: Optional[str] = None


class AlternativeApprovalRequest(BaseModel):
    approved: bool
    reviewer_id: str
    review_notes: Optional[str] = None


class AlternativeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_fragrance_id: uuid.UUID
    candidate_fragrance_id: uuid.UUID
    relationship_type: RelationshipType
    evidence_grade: EvidenceGrade
    status: CurationStatus
    rationale: Optional[str] = None
    known_differences: Optional[str] = None
    curator_id: Optional[str] = None
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    # Hydrated candidate fragrance details
    candidate_name: Optional[str] = None
    candidate_brand: Optional[str] = None
    candidate_concentration: Optional[str] = None
    candidate_indicative_price_inr: Optional[float] = None

