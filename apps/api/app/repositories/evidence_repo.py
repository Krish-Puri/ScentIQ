"""SCENTIQ Evidence and Provenance Repository.
"""
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.evidence import EvidenceSource, ClaimEvidence


class EvidenceRepository:
    def __init__(self, db: Session):
        self.db = db

    # Sources
    def get_source_by_id(self, source_id: uuid.UUID) -> Optional[EvidenceSource]:
        return self.db.execute(select(EvidenceSource).where(EvidenceSource.id == source_id)).scalar_one_or_none()

    def list_sources(self, limit: int = 100, offset: int = 0) -> List[EvidenceSource]:
        return list(self.db.execute(select(EvidenceSource).order_by(EvidenceSource.title).limit(limit).offset(offset)).scalars().all())

    def create_source(self, source: EvidenceSource) -> EvidenceSource:
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    # Claims
    def create_claim(self, claim: ClaimEvidence) -> ClaimEvidence:
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def get_claims_for_entity(self, entity_type: str, entity_id: uuid.UUID) -> List[ClaimEvidence]:
        stmt = (
            select(ClaimEvidence)
            .where(ClaimEvidence.entity_type == entity_type, ClaimEvidence.entity_id == entity_id)
            .order_by(ClaimEvidence.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

