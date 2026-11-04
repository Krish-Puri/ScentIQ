"""SCENTIQ Side-by-Side Fragrance Comparison Endpoint.
Conforms to PRD Section 7 (FR-008) and Section 13.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.comparison_service import ComparisonService
from app.schemas.comparison import ComparisonRequest, ComparisonResponse
from app.schemas.envelope import ResponseEnvelope

router = APIRouter()


@router.post("", response_model=ResponseEnvelope[ComparisonResponse])
def compare_fragrances(
    request: ComparisonRequest,
    db: Session = Depends(get_db),
):
    service = ComparisonService(db)
    result = service.compare(request)
    return ResponseEnvelope.success(data=result)
