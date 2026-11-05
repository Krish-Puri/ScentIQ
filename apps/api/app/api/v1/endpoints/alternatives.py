"""SCENTIQ Alternative Endpoints.
Conforms to PRD Section 7 (FR-007) and Section 13.
"""
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import EvidenceGrade, RelationshipType
from app.services.alternative_service import AlternativeService
from app.schemas.alternative import AlternativeResponse
from app.schemas.envelope import ResponseEnvelope

router = APIRouter()


@router.get("/{id}/alternatives", response_model=ResponseEnvelope[List[AlternativeResponse]])
def get_fragrance_alternatives(
    id: uuid.UUID,
    relationship_type: Optional[RelationshipType] = None,
    evidence_grade: Optional[EvidenceGrade] = None,
    db: Session = Depends(get_db),
):
    service = AlternativeService(db)
    alternatives = service.get_alternatives_for_fragrance(
        source_fragrance_id=id,
        relationship_type=relationship_type,
        evidence_grade=evidence_grade,
        public_only=True,
    )
    return ResponseEnvelope.success(data=alternatives, total=len(alternatives))

