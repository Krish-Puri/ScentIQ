"""SCENTIQ Price Listing Model.
Stores time-stamped, observed retailer prices with source context and staleness tracking.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Float, ForeignKey, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, GUID, TimestampMixin
from app.models.enums import ListingStatus, SellerStatus


class PriceListing(Base, TimestampMixin):
    __tablename__ = "price_listings"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    fragrance_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("fragrances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seller: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    size_ml: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_inr: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    seller_status: Mapped[SellerStatus] = mapped_column(
        SQLEnum(SellerStatus, native_enum=False),
        default=SellerStatus.COMMUNITY_REPORTED,
        nullable=False,
    )
    listing_status: Mapped[ListingStatus] = mapped_column(
        SQLEnum(ListingStatus, native_enum=False),
        default=ListingStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    fragrance: Mapped["Fragrance"] = relationship("Fragrance", back_populates="price_listings")

    @property
    def price_per_ml(self) -> Optional[float]:
        if self.size_ml and self.size_ml > 0:
            return round(self.price_inr / self.size_ml, 2)
        return None

    def __repr__(self) -> str:
        return f"<PriceListing {self.seller}: ₹{self.price_inr} for {self.size_ml}ml>"
