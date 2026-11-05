"""SCENTIQ Brand Model.
"""
import uuid
from typing import List, Optional
from sqlalchemy import String, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, TimestampMixin
from app.models.enums import BrandType, CurationStatus


class Brand(Base, TimestampMixin):
    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    aliases: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    origin_country: Mapped[Optional[str]] = mapped_column(String(2), default="IN", index=True)
    brand_type: Mapped[BrandType] = mapped_column(
        SQLEnum(BrandType, native_enum=False),
        default=BrandType.DESIGNER,
        nullable=False,
    )
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[CurationStatus] = mapped_column(
        SQLEnum(CurationStatus, native_enum=False),
        default=CurationStatus.PUBLISHED,
        nullable=False,
        index=True,
    )

    fragrances: Mapped[List["Fragrance"]] = relationship(
        "Fragrance", back_populates="brand", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Brand {self.canonical_name} [{self.slug}]>"

