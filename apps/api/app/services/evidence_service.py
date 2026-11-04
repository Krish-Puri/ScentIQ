"""SCENTIQ Evidence and Provenance Service.
Manages source documentation, rights register, and claim-to-source mapping.
"""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationError
from app.models.evidence import EvidenceSource, ClaimEvidence
from app.models.enums import LicenseStatus, SourceType
from app.repositories.evidence_repo import EvidenceRepository
from app.schemas.evidence import EvidenceSourceCreate, ClaimEvidenceCreate


class EvidenceService:
    def __init__(self, db: Session):
        self.db = db
        self.evidence_repo = EvidenceRepository(db)

    def create_source(self, data: EvidenceSourceCreate) -> EvidenceSource:
        source = EvidenceSource(
            title=data.title.strip(),
            url=str(data.url) if data.url else None,
            publisher=data.publisher.strip(),
            source_type=data.source_type,
            license_status=data.license_status,
            rights_note=data.rights_note,
            attribution_text=data.attribution_text,
        )
        return self.evidence_repo.create_source(source)

    def create_claim(self, data: ClaimEvidenceCreate, reviewer_id: Optional[str] = None) -> ClaimEvidence:
        source = self.evidence_repo.get_source_by_id(data.source_id)
        if not source:
            raise NotFoundError(f"EvidenceSource {data.source_id} not found", field="source_id")

        claim = ClaimEvidence(
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            field_name=data.field_name,
            source_id=data.source_id,
            claim_text=data.claim_text.strip(),
            confidence=data.confidence,
            reviewer_id=reviewer_id,
        )
        return self.evidence_repo.create_claim(claim)

    def get_claims_for_entity(self, entity_type: str, entity_id: uuid.UUID) -> List[ClaimEvidence]:
        return self.evidence_repo.get_claims_for_entity(entity_type, entity_id)
