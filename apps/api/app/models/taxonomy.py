"""SCENTIQ Taxonomy Models: Notes, Accords, and Fragrance Associations.
"""
import uuid
from typing import List, Optional
from sqlalchemy import Float, ForeignKey, Integer, String, Enum as SQLEnum, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, TimestampMixin
from app.models.enums import PyramidPosition


class Note(Base, TimestampMixin):
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    canonical_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    aliases: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    note_family: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    fragrance_associations: Mapped[List["FragranceNote"]] = relationship(
        "FragranceNote", back_populates="note", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Note {self.canonical_name}>"


class Accord(Base, TimestampMixin):
    __tablename__ = "accords"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    canonical_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    family: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    fragrance_associations: Mapped[List["FragranceAccord"]] = relationship(
        "FragranceAccord", back_populates="accord", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Accord {self.canonical_name}>"


class FragranceNote(Base):
    """Junction table connecting a fragrance to its pyramid notes."""
    __tablename__ = "fragrance_notes"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    fragrance_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("fragrances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    note_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("notes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    pyramid_position: Mapped[PyramidPosition] = mapped_column(
        SQLEnum(PyramidPosition, native_enum=False),
        default=PyramidPosition.UNSPECIFIED,
        nullable=False,
    )
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("evidence_sources.id", ondelete="SET NULL"), nullable=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    fragrance: Mapped["Fragrance"] = relationship("Fragrance", back_populates="notes")
    note: Mapped["Note"] = relationship("Note", back_populates="fragrance_associations")

    __table_args__ = (
        UniqueConstraint("fragrance_id", "note_id", "pyramid_position", name="uq_fragrance_note_position"),
    )


class FragranceAccord(Base):
    """Junction table connecting a fragrance to its perceived accords."""
    __tablename__ = "fragrance_accords"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    fragrance_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("fragrances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    accord_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("accords.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    intensity_rank: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("evidence_sources.id", ondelete="SET NULL"), nullable=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    fragrance: Mapped["Fragrance"] = relationship("Fragrance", back_populates="accords")
    accord: Mapped["Accord"] = relationship("Accord", back_populates="fragrance_associations")

    __table_args__ = (
        UniqueConstraint("fragrance_id", "accord_id", name="uq_fragrance_accord"),
    )

