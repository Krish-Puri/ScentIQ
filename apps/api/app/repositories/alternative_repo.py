"""SCENTIQ Alternative Repository.
"""
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.alternative import AlternativeRelationship
from app.models.fragrance import Fragrance
from app.models.price import PriceListing
from app.models.enums import CurationStatus, EvidenceGrade, RelationshipType


class AlternativeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, relationship_id: uuid.UUID) -> Optional[AlternativeRelationship]:
        stmt = (
            select(AlternativeRelationship)
            .options(
                joinedload(AlternativeRelationship.source_fragrance).joinedload(Fragrance.brand),
                joinedload(AlternativeRelationship.candidate_fragrance).joinedload(Fragrance.brand),
                joinedload(AlternativeRelationship.candidate_fragrance).selectinload(Fragrance.price_listings),
            )
            .where(AlternativeRelationship.id == relationship_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def find_existing(
        self, source_fragrance_id: uuid.UUID, candidate_fragrance_id: uuid.UUID
    ) -> Optional[AlternativeRelationship]:
        stmt = select(AlternativeRelationship).where(
            AlternativeRelationship.source_fragrance_id == source_fragrance_id,
            AlternativeRelationship.candidate_fragrance_id == candidate_fragrance_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_fragrance(
        self,
        source_fragrance_id: uuid.UUID,
        relationship_type: Optional[RelationshipType] = None,
        evidence_grade: Optional[EvidenceGrade] = None,
        public_only: bool = True,
    ) -> List[AlternativeRelationship]:
        stmt = (
            select(AlternativeRelationship)
            .options(
                joinedload(AlternativeRelationship.candidate_fragrance).joinedload(Fragrance.brand),
                joinedload(AlternativeRelationship.candidate_fragrance).selectinload(Fragrance.price_listings),
            )
            .where(AlternativeRelationship.source_fragrance_id == source_fragrance_id)
        )

        if public_only:
            stmt = stmt.where(AlternativeRelationship.status == CurationStatus.PUBLISHED)

        if relationship_type:
            stmt = stmt.where(AlternativeRelationship.relationship_type == relationship_type)

        if evidence_grade:
            stmt = stmt.where(AlternativeRelationship.evidence_grade == evidence_grade)

        stmt = stmt.order_by(AlternativeRelationship.evidence_grade.asc(), AlternativeRelationship.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def create(self, rel: AlternativeRelationship) -> AlternativeRelationship:
        self.db.add(rel)
        self.db.commit()
        self.db.refresh(rel)
        return rel

    def update(self, rel: AlternativeRelationship) -> AlternativeRelationship:
        self.db.commit()
        self.db.refresh(rel)
        return rel
