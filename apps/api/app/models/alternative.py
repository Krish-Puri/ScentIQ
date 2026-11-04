"""SCENTIQ Alternative Relationship Model.
Directed evidence-led alternative graph.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, String, Text, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, TimestampMixin
from app.models.enums import CurationStatus, EvidenceGrade, RelationshipType


class AlternativeRelationship(Base, TimestampMixin):
    """Directed graph: candidate_fragrance is an alternative to source_fragrance (the reference)."""
    __tablename__ = "alternative_relationships"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    source_fragrance_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("fragrances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_fragrance_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("fragrances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[RelationshipType] = mapped_column(
        SQLEnum(RelationshipType, native_enum=False),
        default=RelationshipType.COMMUNITY_REPORTED,
        nullable=False,
        index=True,
    )
    evidence_grade: Mapped[EvidenceGrade] = mapped_column(
        SQLEnum(EvidenceGrade, native_enum=False),
        default=EvidenceGrade.B_SUPPORTED,
        nullable=False,
        index=True,
    )
    status: Mapped[CurationStatus] = mapped_column(
        SQLEnum(CurationStatus, native_enum=False),
        default=CurationStatus.DRAFT,
        nullable=False,
        index=True,
    )
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    known_differences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    curator_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    source_fragrance: Mapped["Fragrance"] = relationship(
        "Fragrance", foreign_keys=[source_fragrance_id], back_populates="source_alternatives"
    )
    candidate_fragrance: Mapped["Fragrance"] = relationship(
        "Fragrance", foreign_keys=[candidate_fragrance_id], back_populates="target_alternatives"
    )

    __table_args__ = (
        UniqueConstraint("source_fragrance_id", "candidate_fragrance_id", name="uq_source_candidate_alternative"),
    )

    def __repr__(self) -> str:
        return (
            f"<AlternativeRelationship candidate={self.candidate_fragrance_id} "
            f"-> source={self.source_fragrance_id} [{self.relationship_type.value}, Grade {self.evidence_grade.value}]>"
        )
