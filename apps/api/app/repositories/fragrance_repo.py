"""SCENTIQ Fragrance Repository.
Supports structured filtering, duplicate detection, and eager association loading.
"""
import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.fragrance import Fragrance
from app.models.brand import Brand
from app.models.taxonomy import FragranceNote, FragranceAccord, Note, Accord
from app.models.price import PriceListing
from app.models.enums import CurationStatus, ListingStatus
from app.schemas.fragrance import FragranceFilterParams


class FragranceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, fragrance_id: uuid.UUID) -> Optional[Fragrance]:
        stmt = (
            select(Fragrance)
            .options(
                joinedload(Fragrance.brand),
                selectinload(Fragrance.notes).joinedload(FragranceNote.note),
                selectinload(Fragrance.accords).joinedload(FragranceAccord.accord),
                selectinload(Fragrance.price_listings),
            )
            .where(Fragrance.id == fragrance_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_slug(self, slug: str) -> Optional[Fragrance]:
        stmt = (
            select(Fragrance)
            .options(
                joinedload(Fragrance.brand),
                selectinload(Fragrance.notes).joinedload(FragranceNote.note),
                selectinload(Fragrance.accords).joinedload(FragranceAccord.accord),
                selectinload(Fragrance.price_listings),
            )
            .where(Fragrance.slug == slug.lower())
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def find_duplicate(
        self, brand_id: uuid.UUID, canonical_name: str, concentration: str
    ) -> Optional[Fragrance]:
        stmt = select(Fragrance).where(
            Fragrance.brand_id == brand_id,
            Fragrance.canonical_name.ilike(canonical_name.strip()),
            Fragrance.concentration.ilike(concentration.strip()),
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_fragrances(
        self,
        params: FragranceFilterParams,
        public_only: bool = True,
    ) -> Tuple[List[Fragrance], int]:
        stmt = (
            select(Fragrance)
            .join(Fragrance.brand)
            .options(
                joinedload(Fragrance.brand),
                selectinload(Fragrance.notes).joinedload(FragranceNote.note),
                selectinload(Fragrance.accords).joinedload(FragranceAccord.accord),
                selectinload(Fragrance.price_listings),
            )
        )

        if public_only:
            stmt = stmt.where(Fragrance.status == CurationStatus.PUBLISHED)

        if params.brand_id:
            stmt = stmt.where(Fragrance.brand_id == params.brand_id)

        if params.family:
            stmt = stmt.where(Fragrance.family.ilike(f"%{params.family}%"))

        if params.concentration:
            stmt = stmt.where(Fragrance.concentration.ilike(params.concentration))

        if params.marketed_gender:
            stmt = stmt.where(Fragrance.marketed_gender.ilike(params.marketed_gender))

        if params.q:
            q_term = f"%{params.q.strip()}%"
            stmt = stmt.where(
                or_(
                    Fragrance.canonical_name.ilike(q_term),
                    Brand.canonical_name.ilike(q_term),
                    Fragrance.description.ilike(q_term),
                )
            )

        if params.note_id:
            stmt = stmt.join(Fragrance.notes).where(FragranceNote.note_id == params.note_id)

        if params.accord_id:
            stmt = stmt.join(Fragrance.accords).where(FragranceAccord.accord_id == params.accord_id)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar() or 0

        # Order and paginate
        stmt = stmt.order_by(Fragrance.canonical_name).offset(params.offset).limit(params.limit)
        results = list(self.db.execute(stmt).scalars().unique().all())

        return results, total

    def create(self, fragrance: Fragrance) -> Fragrance:
        self.db.add(fragrance)
        self.db.commit()
        self.db.refresh(fragrance)
        return fragrance

    def update(self, fragrance: Fragrance) -> Fragrance:
        self.db.commit()
        self.db.refresh(fragrance)
        return fragrance
