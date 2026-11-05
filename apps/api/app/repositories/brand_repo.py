"""SCENTIQ Brand Repository.
"""
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.brand import Brand
from app.models.enums import CurationStatus


class BrandRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, brand_id: uuid.UUID) -> Optional[Brand]:
        return self.db.execute(select(Brand).where(Brand.id == brand_id)).scalar_one_or_none()

    def get_by_slug(self, slug: str) -> Optional[Brand]:
        return self.db.execute(select(Brand).where(Brand.slug == slug.lower())).scalar_one_or_none()

    def get_by_name(self, name: str) -> Optional[Brand]:
        return self.db.execute(select(Brand).where(Brand.canonical_name.ilike(name))).scalar_one_or_none()

    def list_brands(self, status: Optional[CurationStatus] = None, limit: int = 100, offset: int = 0) -> List[Brand]:
        stmt = select(Brand)
        if status:
            stmt = stmt.where(Brand.status == status)
        stmt = stmt.order_by(Brand.canonical_name).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def create(self, brand: Brand) -> Brand:
        self.db.add(brand)
        self.db.commit()
        self.db.refresh(brand)
        return brand

    def update(self, brand: Brand) -> Brand:
        self.db.commit()
        self.db.refresh(brand)
        return brand

