"""SCENTIQ User Profile, Onboarding and Feedback Endpoints.
Implements EPIC-07 and EPIC-12.
Ensures strict user data isolation: users only access their own profiles and feedback.
"""
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user, UserTokenPayload
from app.db.session import get_db
from app.models.enums import FeedbackType
from app.schemas.envelope import ResponseEnvelope
from app.schemas.user import (
    LearnedPreferencesSummary,
    OnboardingRequest,
    UserFeedbackCreate,
    UserFeedbackResponse,
    UserProfileResponse,
    UserProfileUpdate,
)
from app.services.preference_learning_service import PreferenceLearningService
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me/profile", response_model=ResponseEnvelope[UserProfileResponse])
def get_my_profile(
    user: UserTokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    profile = service.get_profile(uuid.UUID(user.sub))
    return ResponseEnvelope.success(data=profile)


@router.put("/me/profile", response_model=ResponseEnvelope[UserProfileResponse])
def update_my_profile(
    data: UserProfileUpdate,
    user: UserTokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    updated = service.update_profile(uuid.UUID(user.sub), data)
    return ResponseEnvelope.success(data=updated)


@router.get("/me/onboarding", response_model=ResponseEnvelope[dict])
def get_onboarding_status(
    user: UserTokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    profile = service.get_profile(uuid.UUID(user.sub))
    return ResponseEnvelope.success(
        data={
            "completed": profile.onboarding_completed,
            "familiarity_level": profile.familiarity_level,
            "profile": profile.model_dump(),
        }
    )


@router.put("/me/onboarding", response_model=ResponseEnvelope[UserProfileResponse])
def submit_onboarding(
    data: OnboardingRequest,
    user: UserTokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    profile = service.process_onboarding(uuid.UUID(user.sub), data)
    return ResponseEnvelope.success(data=profile)


@router.post("/me/feedbacks", response_model=ResponseEnvelope[UserFeedbackResponse])
def record_user_feedback(
    data: UserFeedbackCreate,
    user: UserTokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    fb = service.record_feedback(uuid.UUID(user.sub), data)
    return ResponseEnvelope.success(data=fb)


@router.get("/me/feedbacks", response_model=ResponseEnvelope[List[UserFeedbackResponse]])
def list_user_feedbacks(
    feedback_type: Optional[FeedbackType] = Query(None, description="Optional feedback type filter"),
    user: UserTokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    fbs = service.list_feedbacks(uuid.UUID(user.sub), feedback_type)
    return ResponseEnvelope.success(data=fbs)


@router.delete("/me/feedbacks/{fragrance_id}", response_model=ResponseEnvelope[dict])
def remove_user_feedback(
    fragrance_id: uuid.UUID,
    user: UserTokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    service.remove_feedback(uuid.UUID(user.sub), fragrance_id)
    return ResponseEnvelope.success(data={"deleted": True, "fragrance_id": str(fragrance_id)})


@router.get("/me/preferences/learned", response_model=ResponseEnvelope[LearnedPreferencesSummary])
def get_learned_preferences(
    user: UserTokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    learning_service = PreferenceLearningService(db)
    summary = learning_service.compute_learned_preferences(uuid.UUID(user.sub))
    return ResponseEnvelope.success(data=summary)

