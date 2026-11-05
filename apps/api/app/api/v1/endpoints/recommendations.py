"""SCENTIQ Recommendation Endpoints.
Conforms to PRD Section 7 (FR-009) and Section 12.3.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.recommendation_service import RecommendationService
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.schemas.envelope import ResponseEnvelope

router = APIRouter()


@router.post("", response_model=ResponseEnvelope[RecommendationResponse])
def get_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
):
    service = RecommendationService(db)
    result = service.recommend(request)
    return ResponseEnvelope.success(data=result)

