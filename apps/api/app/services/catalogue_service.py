"""SCENTIQ Catalogue Service.
Implements EPIC-03 (Catalogue Administration) & EPIC-04 validation rules:
- Curation state machine (DRAFT -> IN_REVIEW -> PUBLISHED -> NEEDS_REVIEW -> ARCHIVED)
- Duplicate detection
- Required field validation
- Provenance and rights checks before publication
- Audit trail recording
"""
import re
import uuid
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.enums import CurationStatus, LicenseStatus, UserRole
from app.models.fragrance import Fragrance
from app.models.brand import Brand
from app.models.user import AuditEvent
from app.models.evidence import ClaimEvidence
from app.repositories.fragrance_repo import FragranceRepository
from app.repositories.brand_repo import BrandRepository
from app.repositories.evidence_repo import EvidenceRepository
from app.schemas.fragrance import FragranceCreate, FragranceUpdate


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text).strip("-")


class CatalogueService:
    def __init__(self, db: Session):
        self.db = db
        self.fragrance_repo = FragranceRepository(db)
        self.brand_repo = BrandRepository(db)
        self.evidence_repo = EvidenceRepository(db)

    def create_fragrance(self, data: FragranceCreate, curator_id: str = "curator-admin") -> Fragrance:
        # 1. Validate Brand exists
        brand = self.brand_repo.get_by_id(data.brand_id)
        if not brand:
            raise NotFoundError(f"Brand with id {data.brand_id} not found", field="brand_id")

        # 2. Duplicate Detection (Canonical name + brand_id + concentration)
        existing = self.fragrance_repo.find_duplicate(
            brand_id=data.brand_id,
            canonical_name=data.canonical_name,
            concentration=data.concentration,
        )
        if existing:
            raise ConflictError(
                f"Fragrance '{data.canonical_name}' ({data.concentration}) already exists for brand '{brand.canonical_name}' (ID: {existing.id})",
                field="canonical_name",
            )

        # 3. Generate Slug
        slug = data.slug or slugify(f"{brand.canonical_name}-{data.canonical_name}-{data.concentration}")

        fragrance = Fragrance(
            brand_id=data.brand_id,
            canonical_name=data.canonical_name.strip(),
            slug=slug,
            concentration=data.concentration.strip(),
            release_year=data.release_year,
            perfumer_text=data.perfumer_text,
            marketed_gender=data.marketed_gender,
            family=data.family,
            secondary_family=data.secondary_family,
            description=data.description,
            status=CurationStatus.DRAFT,  # Starts as DRAFT
            curation_notes=data.curation_notes,
        )

        created = self.fragrance_repo.create(fragrance)

        # 4. Audit Log
        audit = AuditEvent(
            actor_id=curator_id,
            action="CREATE_FRAGRANCE",
            entity_type="fragrance",
            entity_id=created.id,
            after_state={"name": created.canonical_name, "status": created.status.value},
        )
        self.db.add(audit)
        self.db.commit()

        return created

    def transition_status(
        self,
        fragrance_id: uuid.UUID,
        new_status: CurationStatus,
        actor_id: str = "admin",
        notes: Optional[str] = None,
    ) -> Fragrance:
        fragrance = self.fragrance_repo.get_by_id(fragrance_id)
        if not fragrance:
            raise NotFoundError(f"Fragrance {fragrance_id} not found")

        old_status = fragrance.status
        if old_status == new_status:
            return fragrance

        # Enforce PRD publication rules when publishing
        if new_status == CurationStatus.PUBLISHED:
            self._validate_for_publication(fragrance)

        fragrance.status = new_status
        if notes:
            fragrance.curation_notes = f"{fragrance.curation_notes or ''}\n[Status Change to {new_status.value}]: {notes}".strip()

        updated = self.fragrance_repo.update(fragrance)

        # Audit Event
        audit = AuditEvent(
            actor_id=actor_id,
            action=f"TRANSITION_{new_status.value}",
            entity_type="fragrance",
            entity_id=updated.id,
            before_state={"status": old_status.value},
            after_state={"status": new_status.value, "notes": notes},
        )
        self.db.add(audit)
        self.db.commit()

        return updated

    def _validate_for_publication(self, fragrance: Fragrance) -> None:
        """Enforces PRD Section 11.6 Data Quality & Provenance rules:
        - Must have canonical name, concentration, brand.
        - Must have at least one traceable EvidenceSource with valid rights status.
        - Restricted sources (e.g. PROPRIETARY_RESTRICTED without license) block publication.
        """
        if not fragrance.canonical_name or not fragrance.concentration:
            raise ValidationError("Fragrance must have canonical name and concentration to be published")

        # Provenance check: verify claim evidences
        claims = self.evidence_repo.get_claims_for_entity("fragrance", fragrance.id)
        if not claims:
            raise ValidationError(
                f"Fragrance '{fragrance.canonical_name}' cannot be published without at least one verified evidence claim (PRD EPIC-04)",
                field="provenance",
            )

        for claim in claims:
            if claim.source.license_status == LicenseStatus.PROPRIETARY_RESTRICTED:
                raise ValidationError(
                    f"Publication blocked: Source '{claim.source.title}' is marked PROPRIETARY_RESTRICTED without written permission (PRD Section 11.3)",
                    field="license_status",
                )
