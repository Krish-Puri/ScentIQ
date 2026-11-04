"""SCENTIQ Evidence and Provenance Models.
Maps directly to PRD Section 10.1 and Section 11 (Data Strategy, Provenance and Quality).
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, String, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, TimestampMixin
from app.models.enums import LicenseStatus, SourceType


class EvidenceSource(Base, TimestampMixin):
    """Source-level provenance and legal rights status."""
    __tablename__ = "evidence_sources"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    publisher: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[SourceType] = mapped_column(
        SQLEnum(SourceType, native_enum=False),
        default=SourceType.OFFICIAL_BRAND,
        nullable=False,
        index=True,
    )
    accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    license_status: Mapped[LicenseStatus] = mapped_column(
        SQLEnum(LicenseStatus, native_enum=False),
        default=LicenseStatus.PERMISSION_GRANTED,
        nullable=False,
    )
    rights_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attribution_text: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    claims: Mapped[List["ClaimEvidence"]] = relationship(
        "ClaimEvidence", back_populates="source", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<EvidenceSource '{self.title}' [{self.license_status.value}]>"


class ClaimEvidence(Base, TimestampMixin):
    """Traces an individual claim or factual field to an authoritative EvidenceSource."""
    __tablename__ = "claim_evidences"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g., 'fragrance', 'alternative'
    entity_id: Mapped[uuid.UUID] = mapped_column(GUID, nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g., 'pyramid', 'clone_link'
    source_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("evidence_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    source: Mapped["EvidenceSource"] = relationship("EvidenceSource", back_populates="claims")

    def __repr__(self) -> str:
        return f"<ClaimEvidence {self.entity_type}.{self.field_name} from source {self.source_id}>"
