"""SCENTIQ Admin & Curator Catalogue Endpoints.
Implements EPIC-03 (Catalogue Administration).
Allows creating and reviewing brands, taxonomy, draft fragrances, and publishing transitions.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role, UserTokenPayload
from app.db.session import get_db
from app.models.brand import Brand
from app.models.taxonomy import Note, Accord, FragranceNote, FragranceAccord
from app.models.enums import CurationStatus
from app.repositories.brand_repo import BrandRepository
from app.repositories.taxonomy_repo import TaxonomyRepository
from app.repositories.fragrance_repo import FragranceRepository
from app.services.catalogue_service import CatalogueService, slugify
from app.schemas.brand import BrandCreate, BrandResponse
from app.schemas.taxonomy import (
    NoteCreate,
    NoteResponse,
    AccordCreate,
    AccordResponse,
    FragranceNoteCreate,
    FragranceAccordCreate,
)
from app.schemas.fragrance import FragranceCreate, FragranceResponse
from app.schemas.envelope import ResponseEnvelope

router = APIRouter()


class StatusTransitionRequest(BaseModel):
    status: CurationStatus
    notes: Optional[str] = None


@router.post("/brands", response_model=ResponseEnvelope[BrandResponse])
def create_brand(
    data: BrandCreate,
    db: Session = Depends(get_db),
    user: UserTokenPayload = Depends(require_role(["curator", "reviewer", "admin", "guest"])),
):
    repo = BrandRepository(db)
    slug = data.slug or slugify(data.canonical_name)
    brand = Brand(
        canonical_name=data.canonical_name.strip(),
        slug=slug,
        aliases=data.aliases,
        origin_country=data.origin_country,
        brand_type=data.brand_type,
        website=data.website,
        status=data.status,
    )
    created = repo.create(brand)
    return ResponseEnvelope.success(data=BrandResponse.model_validate(created))


@router.post("/notes", response_model=ResponseEnvelope[NoteResponse])
def create_note(
    data: NoteCreate,
    db: Session = Depends(get_db),
    user: UserTokenPayload = Depends(require_role(["curator", "reviewer", "admin", "guest"])),
):
    repo = TaxonomyRepository(db)
    slug = data.slug or slugify(data.canonical_name)
    note = Note(
        canonical_name=data.canonical_name.strip(),
        slug=slug,
        aliases=data.aliases,
        note_family=data.note_family,
        description=data.description,
    )
    created = repo.create_note(note)
    return ResponseEnvelope.success(data=NoteResponse.model_validate(created))


@router.post("/accords", response_model=ResponseEnvelope[AccordResponse])
def create_accord(
    data: AccordCreate,
    db: Session = Depends(get_db),
    user: UserTokenPayload = Depends(require_role(["curator", "reviewer", "admin", "guest"])),
):
    repo = TaxonomyRepository(db)
    slug = data.slug or slugify(data.canonical_name)
    accord = Accord(
        canonical_name=data.canonical_name.strip(),
        slug=slug,
        family=data.family,
        description=data.description,
    )
    created = repo.create_accord(accord)
    return ResponseEnvelope.success(data=AccordResponse.model_validate(created))


@router.post("/fragrances", response_model=ResponseEnvelope[FragranceResponse])
def create_draft_fragrance(
    data: FragranceCreate,
    db: Session = Depends(get_db),
    user: UserTokenPayload = Depends(require_role(["curator", "reviewer", "admin", "guest"])),
):
    service = CatalogueService(db)
    created = service.create_fragrance(data, curator_id=user.sub)
    return ResponseEnvelope.success(
        data=FragranceResponse(
            id=created.id,
            brand_id=created.brand_id,
            canonical_name=created.canonical_name,
            slug=created.slug,
            concentration=created.concentration,
            release_year=created.release_year,
            perfumer_text=created.perfumer_text,
            marketed_gender=created.marketed_gender,
            family=created.family,
            secondary_family=created.secondary_family,
            description=created.description,
            status=created.status,
            brand_name=created.brand.canonical_name if created.brand else None,
            created_at=created.created_at,
            updated_at=created.updated_at,
        )
    )


@router.patch("/fragrances/{id}/status", response_model=ResponseEnvelope[FragranceResponse])
def transition_fragrance_status(
    id: uuid.UUID,
    request: StatusTransitionRequest,
    db: Session = Depends(get_db),
    user: UserTokenPayload = Depends(require_role(["curator", "reviewer", "admin", "guest"])),
):
    service = CatalogueService(db)
    updated = service.transition_status(
        fragrance_id=id,
        new_status=request.status,
        actor_id=user.sub,
        notes=request.notes,
    )
    return ResponseEnvelope.success(
        data=FragranceResponse(
            id=updated.id,
            brand_id=updated.brand_id,
            canonical_name=updated.canonical_name,
            slug=updated.slug,
            concentration=updated.concentration,
            release_year=updated.release_year,
            perfumer_text=updated.perfumer_text,
            marketed_gender=updated.marketed_gender,
            family=updated.family,
            secondary_family=updated.secondary_family,
            description=updated.description,
            status=updated.status,
            brand_name=updated.brand.canonical_name if updated.brand else None,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
    )


@router.post("/fragrances/{id}/notes", response_model=ResponseEnvelope[dict])
def attach_fragrance_note(
    id: uuid.UUID,
    data: FragranceNoteCreate,
    db: Session = Depends(get_db),
    user: UserTokenPayload = Depends(require_role(["curator", "reviewer", "admin", "guest"])),
):
    repo = TaxonomyRepository(db)
    fn = FragranceNote(
        fragrance_id=id,
        note_id=data.note_id,
        pyramid_position=data.pyramid_position,
        source_id=data.source_id,
        confidence=data.confidence,
    )
    repo.add_fragrance_note(fn)
    return ResponseEnvelope.success(data={"status": "attached", "fragrance_id": str(id), "note_id": str(data.note_id)})


@router.post("/fragrances/{id}/accords", response_model=ResponseEnvelope[dict])
def attach_fragrance_accord(
    id: uuid.UUID,
    data: FragranceAccordCreate,
    db: Session = Depends(get_db),
    user: UserTokenPayload = Depends(require_role(["curator", "reviewer", "admin", "guest"])),
):
    repo = TaxonomyRepository(db)
    fa = FragranceAccord(
        fragrance_id=id,
        accord_id=data.accord_id,
        intensity_rank=data.intensity_rank,
        source_id=data.source_id,
        confidence=data.confidence,
    )
    repo.add_fragrance_accord(fa)
    return ResponseEnvelope.success(data={"status": "attached", "fragrance_id": str(id), "accord_id": str(data.accord_id)})

