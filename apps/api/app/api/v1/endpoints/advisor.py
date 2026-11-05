"""SCENTIQ AI Fragrance Advisor Endpoints (EPIC-11).
Bounded natural-language intent parser grounded in the deterministic recommendation engine.
"""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_optional_user, UserTokenPayload
from app.db.session import get_db
from app.schemas.advisor import (
    AdvisorParseRequest,
    AdvisorRecommendRequest,
    AdvisorRecommendResponse,
    ParsedAdvisorIntent,
)
from app.schemas.envelope import ResponseEnvelope
from app.services.ai_advisor_service import AIAdvisorService

router = APIRouter()


@router.post("/parse-intent", response_model=ResponseEnvelope[ParsedAdvisorIntent])
def parse_advisor_intent(
    request: AdvisorParseRequest,
    db: Session = Depends(get_db),
):
    service = AIAdvisorService(db)
    parsed = service.parse_intent(request.message)
    return ResponseEnvelope.success(data=parsed)


@router.post("/recommend", response_model=ResponseEnvelope[AdvisorRecommendResponse])
def recommend_with_advisor(
    request: AdvisorRecommendRequest,
    db: Session = Depends(get_db),
    user: UserTokenPayload = Depends(get_optional_user),
):
    service = AIAdvisorService(db)
    user_id = None
    if user.sub and user.sub != "guest-anonymous":
        try:
            user_id = uuid.UUID(user.sub)
        except ValueError:
            user_id = None

    response = service.recommend_with_advisor(request, user_id=user_id)
    return ResponseEnvelope.success(data=response)
