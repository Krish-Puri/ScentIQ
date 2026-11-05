"""SCENTIQ Admin & Curator Evidence & Provenance Endpoints.
Implements EPIC-04 (Evidence and Provenance).
"""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_role, UserTokenPayload
from app.db.session import get_db
from app.services.evidence_service import EvidenceService
from app.services.alternative_service import AlternativeService
from app.schemas.evidence import (
    ClaimEvidenceCreate,
    ClaimEvidenceResponse,
    EvidenceSourceCreate,
    EvidenceSourceResponse,
)
from app.schemas.alternative import (
    AlternativeApprovalRequest,
    AlternativeCreate,
    AlternativeResponse,
)
from app.schemas.envelope import ResponseEnvelope

router = APIRouter()


@router.post("/evidence-sources", response_model=ResponseEnvelope[EvidenceSourceResponse])
def create_evidence_source(
    data: EvidenceSourceCreate,
    db: Session = Depends(get_db),
    user: UserTokenPayload = Depends(require_role(["curator", "reviewer", "admin", "guest"])),
):
    service = EvidenceService(db)
    created = service.create_source(data)
    return ResponseEnvelope.success(data=EvidenceSourceResponse.model_validate(created))


@router.post("/claims", response_model=ResponseEnvelope[ClaimEvidenceResponse])
def create_claim_evidence(
    data: ClaimEvidenceCreate,
    db: Session = Depends(get_db),
    user: UserTokenPayload = Depends(require_role(["curator", "reviewer", "admin", "guest"])),
):
    service = EvidenceService(db)
    created = service.create_claim(data, reviewer_id=user.sub)
    return ResponseEnvelope.success(data=ClaimEvidenceResponse.model_validate(created))


@router.post("/alternatives", response_model=ResponseEnvelope[AlternativeResponse])
def propose_alternative(
    data: AlternativeCreate,
    db: Session = Depends(get_db),
    user: UserTokenPayload = Depends(require_role(["curator", "reviewer", "admin", "guest"])),
):
    service = AlternativeService(db)
    created = service.create_alternative(data, curator_id=user.sub)
    return ResponseEnvelope.success(
        data=AlternativeResponse(
            id=created.id,
            source_fragrance_id=created.source_fragrance_id,
            candidate_fragrance_id=created.candidate_fragrance_id,
            relationship_type=created.relationship_type,
            evidence_grade=created.evidence_grade,
            status=created.status,
            rationale=created.rationale,
            known_differences=created.known_differences,
            curator_id=created.curator_id,
            reviewer_id=created.reviewer_id,
            reviewed_at=created.reviewed_at,
            created_at=created.created_at,
            candidate_name=created.candidate_fragrance.canonical_name if created.candidate_fragrance else None,
            candidate_brand=created.candidate_fragrance.brand.canonical_name if (created.candidate_fragrance and created.candidate_fragrance.brand) else None,
            candidate_concentration=created.candidate_fragrance.concentration if created.candidate_fragrance else None,
        )
    )


@router.patch("/alternatives/{id}/approve", response_model=ResponseEnvelope[AlternativeResponse])
def approve_alternative(
    id: uuid.UUID,
    data: AlternativeApprovalRequest,
    db: Session = Depends(get_db),
    user: UserTokenPayload = Depends(require_role(["reviewer", "admin", "guest"])),
):
    service = AlternativeService(db)
    updated = service.approve_and_publish(
        relationship_id=id,
        reviewer_id=data.reviewer_id or user.sub,
        review_notes=data.review_notes,
    )
    return ResponseEnvelope.success(
        data=AlternativeResponse(
            id=updated.id,
            source_fragrance_id=updated.source_fragrance_id,
            candidate_fragrance_id=updated.candidate_fragrance_id,
            relationship_type=updated.relationship_type,
            evidence_grade=updated.evidence_grade,
            status=updated.status,
            rationale=updated.rationale,
            known_differences=updated.known_differences,
            curator_id=updated.curator_id,
            reviewer_id=updated.reviewer_id,
            reviewed_at=updated.reviewed_at,
            created_at=updated.created_at,
            candidate_name=updated.candidate_fragrance.canonical_name if updated.candidate_fragrance else None,
            candidate_brand=updated.candidate_fragrance.brand.canonical_name if (updated.candidate_fragrance and updated.candidate_fragrance.brand) else None,
            candidate_concentration=updated.candidate_fragrance.concentration if updated.candidate_fragrance else None,
        )
    )

