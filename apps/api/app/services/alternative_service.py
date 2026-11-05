"""SCENTIQ Alternative Service.
Manages directional alternative relationships, evidence grades, and moderation gates.
Conforms to PRD Section 7 (FR-007, FR-015) and Section 11.4/11.5.
"""
from datetime import datetime, timezone
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.alternative import AlternativeRelationship
from app.models.enums import CurationStatus, EvidenceGrade, RelationshipType
from app.models.user import AuditEvent
from app.repositories.alternative_repo import AlternativeRepository
from app.repositories.fragrance_repo import FragranceRepository
from app.schemas.alternative import AlternativeCreate, AlternativeResponse


class AlternativeService:
    def __init__(self, db: Session):
        self.db = db
        self.alternative_repo = AlternativeRepository(db)
        self.fragrance_repo = FragranceRepository(db)

    def create_alternative(
        self, data: AlternativeCreate, curator_id: str = "curator"
    ) -> AlternativeRelationship:
        # 1. Self-reference check
        if data.source_fragrance_id == data.candidate_fragrance_id:
            raise ValidationError("A fragrance cannot be marked as an alternative to itself", field="candidate_fragrance_id")

        # 2. Verify both fragrances exist
        source = self.fragrance_repo.get_by_id(data.source_fragrance_id)
        if not source:
            raise NotFoundError(f"Reference fragrance {data.source_fragrance_id} not found")

        candidate = self.fragrance_repo.get_by_id(data.candidate_fragrance_id)
        if not candidate:
            raise NotFoundError(f"Candidate fragrance {data.candidate_fragrance_id} not found")

        # 3. Check for existing link
        existing = self.alternative_repo.find_existing(data.source_fragrance_id, data.candidate_fragrance_id)
        if existing:
            raise ConflictError("An alternative relationship between these two fragrances already exists")

        # 4. Construct model
        rel = AlternativeRelationship(
            source_fragrance_id=data.source_fragrance_id,
            candidate_fragrance_id=data.candidate_fragrance_id,
            relationship_type=data.relationship_type,
            evidence_grade=data.evidence_grade,
            status=CurationStatus.DRAFT,  # Requires review
            rationale=data.rationale,
            known_differences=data.known_differences,
            curator_id=curator_id,
        )

        created = self.alternative_repo.create(rel)

        # Audit
        audit = AuditEvent(
            actor_id=curator_id,
            action="CREATE_ALTERNATIVE_RELATIONSHIP",
            entity_type="alternative_relationship",
            entity_id=created.id,
            after_state={
                "source_id": str(data.source_fragrance_id),
                "candidate_id": str(data.candidate_fragrance_id),
                "type": data.relationship_type.value,
                "grade": data.evidence_grade.value,
            },
        )
        self.db.add(audit)
        self.db.commit()

        return created

    def approve_and_publish(
        self,
        relationship_id: uuid.UUID,
        reviewer_id: str,
        review_notes: Optional[str] = None,
    ) -> AlternativeRelationship:
        rel = self.alternative_repo.get_by_id(relationship_id)
        if not rel:
            raise NotFoundError(f"Alternative relationship {relationship_id} not found")

        if not reviewer_id:
            raise ValidationError("Reviewer ID is required for approving an alternative relationship")

        rel.status = CurationStatus.PUBLISHED
        rel.reviewer_id = reviewer_id
        rel.reviewed_at = datetime.now(timezone.utc)
        if review_notes:
            rel.rationale = f"{rel.rationale or ''}\n[Review Approval]: {review_notes}".strip()

        updated = self.alternative_repo.update(rel)

        # Audit
        audit = AuditEvent(
            actor_id=reviewer_id,
            action="APPROVE_ALTERNATIVE_RELATIONSHIP",
            entity_type="alternative_relationship",
            entity_id=updated.id,
            before_state={"status": CurationStatus.DRAFT.value},
            after_state={"status": CurationStatus.PUBLISHED.value, "reviewer": reviewer_id},
        )
        self.db.add(audit)
        self.db.commit()

        return updated

    def get_alternatives_for_fragrance(
        self,
        source_fragrance_id: uuid.UUID,
        relationship_type: Optional[RelationshipType] = None,
        evidence_grade: Optional[EvidenceGrade] = None,
        public_only: bool = True,
    ) -> List[AlternativeResponse]:
        rels = self.alternative_repo.list_for_fragrance(
            source_fragrance_id=source_fragrance_id,
            relationship_type=relationship_type,
            evidence_grade=evidence_grade,
            public_only=public_only,
        )

        responses = []
        for r in rels:
            cand = r.candidate_fragrance
            price = None
            if cand and cand.price_listings:
                active_prices = [p.price_inr for p in cand.price_listings if p.price_inr > 0]
                if active_prices:
                    price = min(active_prices)

            resp = AlternativeResponse(
                id=r.id,
                source_fragrance_id=r.source_fragrance_id,
                candidate_fragrance_id=r.candidate_fragrance_id,
                relationship_type=r.relationship_type,
                evidence_grade=r.evidence_grade,
                status=r.status,
                rationale=r.rationale,
                known_differences=r.known_differences,
                curator_id=r.curator_id,
                reviewer_id=r.reviewer_id,
                reviewed_at=r.reviewed_at,
                created_at=r.created_at,
                candidate_name=cand.canonical_name if cand else "Unknown",
                candidate_brand=cand.brand.canonical_name if cand and cand.brand else "Unknown",
                candidate_concentration=cand.concentration if cand else None,
                candidate_indicative_price_inr=price,
            )
            responses.append(resp)

        return responses

