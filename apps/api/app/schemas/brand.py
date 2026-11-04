"""SCENTIQ Brand Schemas.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import BrandType, CurationStatus


class BrandBase(BaseModel):
    canonical_name: str = Field(..., min_length=1, max_length=255)
    aliases: List[str] = Field(default_factory=list)
    origin_country: Optional[str] = Field("IN", min_length=2, max_length=2)
    brand_type: BrandType = BrandType.DESIGNER
    website: Optional[str] = None
    status: CurationStatus = CurationStatus.PUBLISHED


class BrandCreate(BrandBase):
    slug: Optional[str] = None  # Auto-generated from canonical_name if omitted


class BrandUpdate(BaseModel):
    canonical_name: Optional[str] = None
    aliases: Optional[List[str]] = None
    origin_country: Optional[str] = None
    brand_type: Optional[BrandType] = None
    website: Optional[str] = None
    status: Optional[CurationStatus] = None


class BrandResponse(BrandBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    created_at: datetime
    updated_at: datetime
