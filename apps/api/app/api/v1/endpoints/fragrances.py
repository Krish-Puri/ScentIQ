"""SCENTIQ Public Fragrance Endpoints.
Conforms to PRD Section 13 API Specifications.
Only published fragrances are surfaced to public/guest consumers.
"""
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.enums import CurationStatus, PyramidPosition
from app.repositories.fragrance_repo import FragranceRepository
from app.repositories.evidence_repo import EvidenceRepository
from app.schemas.envelope import ResponseEnvelope
from app.schemas.fragrance import (
    FragranceDetailResponse,
    FragranceFilterParams,
    FragranceResponse,
    PriceListingSummary,
)
from app.schemas.brand import BrandResponse

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[List[FragranceResponse]])
def list_fragrances(
    q: Optional[str] = None,
    brand_id: Optional[uuid.UUID] = None,
    family: Optional[str] = None,
    concentration: Optional[str] = None,
    marketed_gender: Optional[str] = None,
    note_id: Optional[uuid.UUID] = None,
    accord_id: Optional[uuid.UUID] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    repo = FragranceRepository(db)
    params = FragranceFilterParams(
        q=q,
        brand_id=brand_id,
        family=family,
        concentration=concentration,
        marketed_gender=marketed_gender,
        note_id=note_id,
        accord_id=accord_id,
        limit=limit,
        offset=offset,
    )
    records, total = repo.list_fragrances(params, public_only=True)

    items = [
        FragranceResponse(
            id=f.id,
            brand_id=f.brand_id,
            canonical_name=f.canonical_name,
            slug=f.slug,
            concentration=f.concentration,
            release_year=f.release_year,
            perfumer_text=f.perfumer_text,
            marketed_gender=f.marketed_gender,
            family=f.family,
            secondary_family=f.secondary_family,
            description=f.description,
            status=f.status,
            brand_name=f.brand.canonical_name if f.brand else None,
            created_at=f.created_at,
            updated_at=f.updated_at,
        )
        for f in records
    ]

    next_cursor = str(offset + limit) if (offset + limit) < total else None
    return ResponseEnvelope.success(data=items, total=total, next_cursor=next_cursor)


@router.get("/{slug}", response_model=ResponseEnvelope[FragranceDetailResponse])
def get_fragrance_by_slug(slug: str, db: Session = Depends(get_db)):
    repo = FragranceRepository(db)
    evidence_repo = EvidenceRepository(db)

    fragrance = repo.get_by_slug(slug)
    if not fragrance or fragrance.status != CurationStatus.PUBLISHED:
        raise NotFoundError(f"Fragrance '{slug}' not found or not published", field="slug")

    top_notes = [fn.note.canonical_name for fn in fragrance.notes if fn.pyramid_position == PyramidPosition.TOP]
    heart_notes = [fn.note.canonical_name for fn in fragrance.notes if fn.pyramid_position == PyramidPosition.HEART]
    base_notes = [fn.note.canonical_name for fn in fragrance.notes if fn.pyramid_position == PyramidPosition.BASE]
    accords = [fa.accord.canonical_name for fa in sorted(fragrance.accords, key=lambda a: a.intensity_rank)]

    prices = [
        PriceListingSummary(
            id=p.id,
            seller=p.seller,
            price_inr=p.price_inr,
            size_ml=p.size_ml,
            price_per_ml=p.price_per_ml,
            url=p.url,
            observed_at=p.observed_at,
        )
        for p in fragrance.price_listings
    ]

    claims = evidence_repo.get_claims_for_entity("fragrance", fragrance.id)

    brand_resp = BrandResponse.model_validate(fragrance.brand)

    detail = FragranceDetailResponse(
        id=fragrance.id,
        brand_id=fragrance.brand_id,
        canonical_name=fragrance.canonical_name,
        slug=fragrance.slug,
        concentration=fragrance.concentration,
        release_year=fragrance.release_year,
        perfumer_text=fragrance.perfumer_text,
        marketed_gender=fragrance.marketed_gender,
        family=fragrance.family,
        secondary_family=fragrance.secondary_family,
        description=fragrance.description,
        status=fragrance.status,
        brand_name=fragrance.brand.canonical_name,
        brand=brand_resp,
        top_notes=top_notes,
        heart_notes=heart_notes,
        base_notes=base_notes,
        accords=accords,
        prices=prices,
        evidence_count=len(claims),
        curation_notes=fragrance.curation_notes,
        created_at=fragrance.created_at,
        updated_at=fragrance.updated_at,
    )

    return ResponseEnvelope.success(data=detail)

