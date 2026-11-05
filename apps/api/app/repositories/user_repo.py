"""SCENTIQ User, Profile and Feedback Repository.
"""
from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import select, delete
from sqlalchemy.orm import Session, joinedload

from app.models.enums import FeedbackType
from app.models.user import User, UserProfile, UserFeedback
from app.models.fragrance import Fragrance
from app.models.taxonomy import FragranceNote, FragranceAccord
from sqlalchemy.orm import Session, joinedload, selectinload


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.db.execute(
            select(User).options(joinedload(User.profile)).where(User.id == user_id)
        ).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.execute(
            select(User).options(joinedload(User.profile)).where(User.email == email.lower().strip())
        ).scalar_one_or_none()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_profile(self, user_id: uuid.UUID) -> Optional[UserProfile]:
        return self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        ).scalar_one_or_none()

    def upsert_profile(self, user_id: uuid.UUID, **attrs) -> UserProfile:
        profile = self.get_profile(user_id)
        if not profile:
            profile = UserProfile(user_id=user_id, **attrs)
            self.db.add(profile)
        else:
            for k, v in attrs.items():
                if hasattr(profile, k) and v is not None:
                    setattr(profile, k, v)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_feedbacks(
        self, user_id: uuid.UUID, feedback_type: Optional[FeedbackType] = None
    ) -> List[UserFeedback]:
        stmt = (
            select(UserFeedback)
            .options(
                joinedload(UserFeedback.fragrance).joinedload(Fragrance.brand),
                joinedload(UserFeedback.fragrance).selectinload(Fragrance.notes).joinedload(FragranceNote.note),
                joinedload(UserFeedback.fragrance).selectinload(Fragrance.accords).joinedload(FragranceAccord.accord),
            )
            .where(UserFeedback.user_id == user_id)
        )
        if feedback_type:
            stmt = stmt.where(UserFeedback.feedback_type == feedback_type)
        stmt = stmt.order_by(UserFeedback.created_at.desc())
        return list(self.db.execute(stmt).scalars().unique().all())

    def get_feedback(self, user_id: uuid.UUID, fragrance_id: uuid.UUID) -> Optional[UserFeedback]:
        return self.db.execute(
            select(UserFeedback)
            .options(joinedload(UserFeedback.fragrance).joinedload(Fragrance.brand))
            .where(UserFeedback.user_id == user_id, UserFeedback.fragrance_id == fragrance_id)
        ).scalar_one_or_none()

    def upsert_feedback(
        self,
        user_id: uuid.UUID,
        fragrance_id: uuid.UUID,
        feedback_type: FeedbackType,
        rating: Optional[float] = None,
        context_json: Optional[dict] = None,
    ) -> UserFeedback:
        existing = self.get_feedback(user_id, fragrance_id)
        if existing:
            existing.feedback_type = feedback_type
            if rating is not None:
                existing.rating = rating
            if context_json is not None:
                existing.context_json = context_json
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        feedback = UserFeedback(
            user_id=user_id,
            fragrance_id=fragrance_id,
            feedback_type=feedback_type,
            rating=rating,
            context_json=context_json or {},
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def delete_feedback(self, user_id: uuid.UUID, fragrance_id: uuid.UUID) -> bool:
        stmt = delete(UserFeedback).where(
            UserFeedback.user_id == user_id, UserFeedback.fragrance_id == fragrance_id
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0

