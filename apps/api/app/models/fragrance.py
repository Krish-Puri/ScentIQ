"""SCENTIQ Fragrance Model.
Central entity in the fragrance catalogue.
"""
import uuid
from typing import List, Optional
from sqlalchemy import ForeignKey, Integer, String, Text, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, TimestampMixin
from app.models.enums import CurationStatus


class Fragrance(Base, TimestampMixin):
    __tablename__ = "fragrances"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    concentration: Mapped[str] = mapped_column(String(50), default="EDP", nullable=False, index=True)
    release_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    perfumer_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    marketed_gender: Mapped[Optional[str]] = mapped_column(String(50), default="unisex", index=True)
    family: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    secondary_family: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Curation lifecycle: DRAFT -> IN_REVIEW -> PUBLISHED -> NEEDS_REVIEW -> ARCHIVED
    status: Mapped[CurationStatus] = mapped_column(
        SQLEnum(CurationStatus, native_enum=False),
        default=CurationStatus.DRAFT,
        nullable=False,
        index=True,
    )
    curation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", back_populates="fragrances")
    notes: Mapped[List["FragranceNote"]] = relationship(
        "FragranceNote", back_populates="fragrance", cascade="all, delete-orphan"
    )
    accords: Mapped[List["FragranceAccord"]] = relationship(
        "FragranceAccord", back_populates="fragrance", cascade="all, delete-orphan"
    )
    price_listings: Mapped[List["PriceListing"]] = relationship(
        "PriceListing", back_populates="fragrance", cascade="all, delete-orphan"
    )

    # Alternative relationships (directed graph: candidate is alternative to reference)
    source_alternatives: Mapped[List["AlternativeRelationship"]] = relationship(
        "AlternativeRelationship",
        foreign_keys="AlternativeRelationship.source_fragrance_id",
        back_populates="source_fragrance",
        cascade="all, delete-orphan",
    )
    target_alternatives: Mapped[List["AlternativeRelationship"]] = relationship(
        "AlternativeRelationship",
        foreign_keys="AlternativeRelationship.candidate_fragrance_id",
        back_populates="candidate_fragrance",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("brand_id", "slug", "concentration", name="uq_brand_slug_concentration"),
    )

    def __repr__(self) -> str:
        return f"<Fragrance {self.canonical_name} ({self.concentration}) [{self.status.value}]>"
