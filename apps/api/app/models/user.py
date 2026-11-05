"""SCENTIQ User, Profile, Feedback, Recommendation Audit and Governance Models.
Strictly adheres to PRD Section 10.1, Section 15.1 (Data Minimisation) and Section 16.1.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Enum as SQLEnum, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, TimestampMixin
from app.models.enums import FeedbackType, UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    auth_subject: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, native_enum=False),
        default=UserRole.USER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    feedbacks: Mapped[List["UserFeedback"]] = relationship(
        "UserFeedback", back_populates="user", cascade="all, delete-orphan"
    )
    recommendation_runs: Mapped[List["RecommendationRun"]] = relationship(
        "RecommendationRun", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email or self.auth_subject} [{self.role.value}]>"


class UserProfile(Base, TimestampMixin):
    """Explicit preference profile; fully user-editable with no sensitive inferred attributes."""
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    familiarity_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # new, casual, enthusiast, collector
    preferred_families: Mapped[List[str]] = mapped_column(JSON, default=list)
    preferred_notes: Mapped[List[str]] = mapped_column(JSON, default=list)
    disliked_notes: Mapped[List[str]] = mapped_column(JSON, default=list)
    preferred_accords: Mapped[List[str]] = mapped_column(JSON, default=list)
    disliked_accords: Mapped[List[str]] = mapped_column(JSON, default=list)
    avoid_terms: Mapped[List[str]] = mapped_column(JSON, default=list)  # Notes/accords to strictly exclude
    budget_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    budget_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    occasions: Mapped[List[str]] = mapped_column(JSON, default=list)
    preferred_concentrations: Mapped[List[str]] = mapped_column(JSON, default=list)
    longevity_preference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    projection_preference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    climate_context: Mapped[List[str]] = mapped_column(JSON, default=list)
    intensity_preference: Mapped[Optional[str]] = mapped_column(String(50), default="moderate")
    preference_vector_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="profile")


class UserFeedback(Base):
    """Explicit user feedback on fragrances (like, dislike, tried, owned)."""
    __tablename__ = "user_feedbacks"
    __table_args__ = (
        UniqueConstraint("user_id", "fragrance_id", name="uq_user_fragrance_feedback"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fragrance_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("fragrances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    feedback_type: Mapped[FeedbackType] = mapped_column(
        SQLEnum(FeedbackType, native_enum=False),
        nullable=False,
        index=True,
    )
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    context_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="feedbacks")
    fragrance: Mapped["Fragrance"] = relationship("Fragrance", lazy="joined")


class RecommendationRun(Base):
    """Audit log of recommendation runs for reproducibility, offline evaluation and latency monitoring."""
    __tablename__ = "recommendation_runs"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    query_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    ruleset_version: Mapped[str] = mapped_column(String(50), default="v1.0", nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    result_ids: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="recommendation_runs")


class AuditEvent(Base):
    """Curator and administrative traceability for catalogue and rights changes."""
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g., 'CREATE', 'PUBLISH', 'RETRACT'
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(GUID, nullable=False, index=True)
    before_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    after_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

