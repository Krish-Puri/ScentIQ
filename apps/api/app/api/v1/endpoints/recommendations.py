"""SCENTIQ Recommendation Endpoints.
Conforms to PRD Section 7 (FR-009) and Section 12.3.
Supports anonymous discovery as well as user-personalized ranking.
"""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_optional_user, UserTokenPayload
from app.db.session import get_db
from app.services.recommendation_service import RecommendationService
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.schemas.envelope import ResponseEnvelope

router = APIRouter()


@router.post("", response_model=ResponseEnvelope[RecommendationResponse])
def get_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
    user: UserTokenPayload = Depends(get_optional_user),
):
    service = RecommendationService(db)
    user_id = None
    if user.sub and user.sub != "guest-anonymous":
        try:
            user_id = uuid.UUID(user.sub)
        except ValueError:
            user_id = None

    result = service.recommend(request, user_id=user_id)
    return ResponseEnvelope.success(data=result)
