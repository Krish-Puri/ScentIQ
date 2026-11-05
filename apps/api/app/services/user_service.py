"""SCENTIQ User Service.
Manages user authentication, profile management, onboarding workflows and feedback capture.
Strictly adheres to PRD Section 10.1, Section 10.4, Section 15.1, and EPIC-07 / EPIC-12.
"""
from typing import List, Optional
import uuid
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, AuthRequiredError, ValidationError
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.enums import FeedbackType, UserRole
from app.models.user import User, UserProfile, UserFeedback
from app.repositories.user_repo import UserRepository
from app.repositories.fragrance_repo import FragranceRepository
from app.schemas.user import (
    OnboardingRequest,
    TokenResponse,
    UserFeedbackCreate,
    UserFeedbackResponse,
    UserProfileResponse,
    UserProfileUpdate,
    UserRegisterRequest,
)


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.fragrance_repo = FragranceRepository(db)

    def register(self, data: UserRegisterRequest) -> TokenResponse:
        existing = self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictError(f"User with email '{data.email}' already exists")

        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email=data.email.lower().strip(),
            auth_subject=f"user:{user_id}",
            hashed_password=get_password_hash(data.password),
            role=data.role or UserRole.USER,
            is_active=True,
        )
        created = self.user_repo.create(user)

        # Initialize default empty profile
        self.user_repo.upsert_profile(created.id)

        token = create_access_token({
            "sub": str(created.id),
            "email": created.email,
            "role": created.role.value if hasattr(created.role, "value") else str(created.role),
        })

        return TokenResponse(
            access_token=token,
            user_id=created.id,
            email=created.email,
            role=created.role.value if hasattr(created.role, "value") else str(created.role),
        )

    def authenticate(self, email: str, password: str) -> TokenResponse:
        user = self.user_repo.get_by_email(email)
        if not user or not user.hashed_password:
            raise AuthRequiredError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise AuthRequiredError("Invalid email or password")

        if not user.is_active:
            raise AuthRequiredError("User account is inactive")

        token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        })

        return TokenResponse(
            access_token=token,
            user_id=user.id,
            email=user.email,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
        )

    def get_profile(self, user_id: uuid.UUID) -> UserProfileResponse:
        profile = self.user_repo.get_profile(user_id)
        if not profile:
            profile = self.user_repo.upsert_profile(user_id)
        return UserProfileResponse.model_validate(profile)

    def update_profile(self, user_id: uuid.UUID, update_data: UserProfileUpdate) -> UserProfileResponse:
        attrs = update_data.model_dump(exclude_unset=True)
        # If avoid_terms or disliked_notes/accords are updated, ensure consistency
        if "avoid_terms" in attrs and attrs["avoid_terms"] is not None:
            attrs["avoid_terms"] = list({term.strip().lower() for term in attrs["avoid_terms"] if term.strip()})

        updated = self.user_repo.upsert_profile(user_id, **attrs)
        return UserProfileResponse.model_validate(updated)

    def process_onboarding(self, user_id: uuid.UUID, data: OnboardingRequest) -> UserProfileResponse:
        """Processes the 6-step onboarding sequence (EPIC-07)."""
        # Combine avoid_terms with disliked notes and accords for hard exclusions
        avoid_set = set(t.strip().lower() for t in data.avoid_terms if t.strip())
        for n in data.disliked_notes:
            if n.strip():
                avoid_set.add(n.strip().lower())
        for a in data.disliked_accords:
            if a.strip():
                avoid_set.add(a.strip().lower())

        attrs = {
            "familiarity_level": data.familiarity_level,
            "preferred_families": data.preferred_families,
            "preferred_notes": data.liked_notes,
            "disliked_notes": data.disliked_notes,
            "preferred_accords": data.liked_accords,
            "disliked_accords": data.disliked_accords,
            "avoid_terms": list(avoid_set),
            "occasions": data.occasions,
            "budget_min": data.budget_min,
            "budget_max": data.budget_max,
            "preferred_concentrations": data.preferred_concentrations,
            "longevity_preference": data.longevity_preference,
            "projection_preference": data.projection_preference,
            "climate_context": data.climate_context,
            "onboarding_completed": True,
        }

        profile = self.user_repo.upsert_profile(user_id, **attrs)

        # Record known fragrances as feedback
        for item in data.known_fragrances:
            frag = self.fragrance_repo.get_by_id(item.fragrance_id)
            if frag:
                self.user_repo.upsert_feedback(
                    user_id=user_id,
                    fragrance_id=item.fragrance_id,
                    feedback_type=item.preference,
                    context_json={"source": "onboarding"},
                )

        return UserProfileResponse.model_validate(profile)

    def record_feedback(self, user_id: uuid.UUID, data: UserFeedbackCreate) -> UserFeedbackResponse:
        """Records or updates user feedback on a fragrance (EPIC-12)."""
        frag = self.fragrance_repo.get_by_id(data.fragrance_id)
        if not frag:
            raise NotFoundError(f"Fragrance {data.fragrance_id} not found")

        context = {
            "reason": data.reason,
            "wear_experience": data.wear_experience,
            "observed_longevity": data.observed_longevity,
            "observed_projection": data.observed_projection,
        }
        # Filter out None values
        clean_context = {k: v for k, v in context.items() if v is not None}

        feedback = self.user_repo.upsert_feedback(
            user_id=user_id,
            fragrance_id=data.fragrance_id,
            feedback_type=data.feedback_type,
            rating=data.rating,
            context_json=clean_context,
        )

        return UserFeedbackResponse(
            id=feedback.id,
            user_id=feedback.user_id,
            fragrance_id=feedback.fragrance_id,
            feedback_type=feedback.feedback_type,
            rating=feedback.rating,
            context_json=feedback.context_json,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at,
            fragrance_name=frag.canonical_name,
            fragrance_brand=frag.brand.canonical_name if frag.brand else None,
            fragrance_slug=frag.slug,
        )

    def list_feedbacks(
        self, user_id: uuid.UUID, feedback_type: Optional[FeedbackType] = None
    ) -> List[UserFeedbackResponse]:
        feedbacks = self.user_repo.get_feedbacks(user_id, feedback_type)
        res = []
        for fb in feedbacks:
            frag = fb.fragrance
            res.append(
                UserFeedbackResponse(
                    id=fb.id,
                    user_id=fb.user_id,
                    fragrance_id=fb.fragrance_id,
                    feedback_type=fb.feedback_type,
                    rating=fb.rating,
                    context_json=fb.context_json or {},
                    created_at=fb.created_at,
                    updated_at=fb.updated_at,
                    fragrance_name=frag.canonical_name if frag else None,
                    fragrance_brand=frag.brand.canonical_name if (frag and frag.brand) else None,
                    fragrance_slug=frag.slug if frag else None,
                )
            )
        return res

    def remove_feedback(self, user_id: uuid.UUID, fragrance_id: uuid.UUID) -> bool:
        deleted = self.user_repo.delete_feedback(user_id, fragrance_id)
        if not deleted:
            raise NotFoundError(f"Feedback for fragrance {fragrance_id} not found")
        return True
