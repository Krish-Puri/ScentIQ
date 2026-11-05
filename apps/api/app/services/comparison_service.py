"""SCENTIQ Comparison Service.
Conforms to PRD Section 7 (FR-008) and Section 10.4.
Enforces side-by-side factual comparisons without unsupported percentage claims.
"""
import uuid
from typing import List, Set
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationError
from app.models.enums import CurationStatus, PyramidPosition
from app.repositories.fragrance_repo import FragranceRepository
from app.repositories.evidence_repo import EvidenceRepository
from app.schemas.comparison import ComparisonRequest, ComparisonResponse, FragranceComparisonColumn


class ComparisonService:
    def __init__(self, db: Session):
        self.db = db
        self.fragrance_repo = FragranceRepository(db)
        self.evidence_repo = EvidenceRepository(db)

    def compare(self, request: ComparisonRequest) -> ComparisonResponse:
        unique_ids = list(dict.fromkeys(request.fragrance_ids))
        if len(unique_ids) < 2 or len(unique_ids) > 3:
            raise ValidationError("Comparison requires 2 or 3 distinct fragrance IDs", field="fragrance_ids")

        columns: List[FragranceComparisonColumn] = []
        note_sets: List[Set[str]] = []
        accord_sets: List[Set[str]] = []
        missing_disclosures: List[str] = []

        for fid in unique_ids:
            frag = self.fragrance_repo.get_by_id(fid)
            if not frag:
                raise NotFoundError(f"Fragrance {fid} not found")

            top_notes = [fn.note.canonical_name for fn in frag.notes if fn.pyramid_position == PyramidPosition.TOP]
            heart_notes = [fn.note.canonical_name for fn in frag.notes if fn.pyramid_position == PyramidPosition.HEART]
            base_notes = [fn.note.canonical_name for fn in frag.notes if fn.pyramid_position == PyramidPosition.BASE]
            unspecified = [fn.note.canonical_name for fn in frag.notes if fn.pyramid_position == PyramidPosition.UNSPECIFIED]
            
            all_notes = set(top_notes + heart_notes + base_notes + unspecified)
            note_sets.append(all_notes)

            accords = [fa.accord.canonical_name for fa in sorted(frag.accords, key=lambda a: a.intensity_rank)]
            accord_sets.append(set(accords))

            # Missing data disclosures
            has_pyramid = bool(top_notes or heart_notes or base_notes)
            if not has_pyramid:
                missing_disclosures.append(f"Full pyramid data not recorded for '{frag.canonical_name}'.")

            # Prices
            indicative_price = None
            size_ml = None
            price_per_ml = None
            if frag.price_listings:
                valid_prices = [p for p in frag.price_listings if p.price_inr > 0]
                if valid_prices:
                    best = min(valid_prices, key=lambda p: p.price_inr)
                    indicative_price = best.price_inr
                    size_ml = best.size_ml
                    price_per_ml = best.price_per_ml

            claims = self.evidence_repo.get_claims_for_entity("fragrance", frag.id)

            col = FragranceComparisonColumn(
                id=frag.id,
                canonical_name=frag.canonical_name,
                brand_name=frag.brand.canonical_name if frag.brand else "Unknown",
                concentration=frag.concentration,
                family=frag.family,
                top_notes=top_notes,
                heart_notes=heart_notes,
                base_notes=base_notes,
                accords=accords,
                indicative_price_inr=indicative_price,
                size_ml=size_ml,
                price_per_ml=price_per_ml,
                has_full_pyramid_data=has_pyramid,
                evidence_count=len(claims),
            )
            columns.append(col)

        # Compute intersection
        shared_notes = sorted(list(set.intersection(*note_sets))) if note_sets else []
        shared_accords = sorted(list(set.intersection(*accord_sets))) if accord_sets else []

        # Compute distinguishing notes (notes present in some but not in all)
        all_unique_notes = set.union(*note_sets) if note_sets else set()
        distinguishing_notes = sorted(list(all_unique_notes - set(shared_notes)))

        return ComparisonResponse(
            items=columns,
            shared_notes=shared_notes,
            shared_accords=shared_accords,
            distinguishing_notes=distinguishing_notes,
            missing_data_disclosures=missing_disclosures,
        )

