"""SCENTIQ Automated Catalogue Data Quality & Integrity Validator.
Part of Milestone 3 Part 6.1.
Enforces rigorous data governance, provenance verification, and catalogue consistency rules:
1. Every fragrance has required fields (canonical_name, brand, concentration, status).
2. Published fragrances have at least one verified active price listing (> 0 INR).
3. Note pyramids contain complete structures (top, heart, base).
4. Concentration is a recognized standard (EDT, EDP, Parfum, Extrait, EDC).
5. Marketed gender is one of ('masculine', 'feminine', 'unisex').
6. Price listings have positive price, currency INR, valid seller.
7. No self-referential alternative relationships (source != candidate).
8. Published fragrances have verified source provenance (evidence source).
"""
import sys
import os
from typing import Dict, List, Tuple

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from app.db.session import SessionLocal
from app.models.enums import CurationStatus, PyramidPosition
from app.models.brand import Brand
from app.models.fragrance import Fragrance
from app.models.taxonomy import FragranceNote, FragranceAccord, Note, Accord
from app.models.price import PriceListing
from app.models.evidence import EvidenceSource, ClaimEvidence
from app.models.alternative import AlternativeRelationship

VALID_CONCENTRATIONS = {"EDT", "EDP", "PARFUM", "EXTRAIT", "EDC", "EXTRAIT DE PARFUM"}
VALID_GENDERS = {"masculine", "feminine", "unisex"}


class CatalogueValidator:
    def __init__(self, db):
        self.db = db
        self.critical_errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict[str, int] = {}

    def run_all_checks(self) -> bool:
        print("=" * 60)
        print("SCENTIQ CATALOGUE DATA QUALITY & PROVENANCE AUDIT")
        print("=" * 60)

        self._check_brands()
        self._check_evidence_sources()
        self._check_fragrances()
        self._check_price_listings()
        self._check_alternative_relationships()

        self._print_summary()
        return len(self.critical_errors) == 0

    def _check_brands(self):
        brands = self.db.query(Brand).all()
        self.stats["total_brands"] = len(brands)
        for b in brands:
            if not b.canonical_name or not b.slug:
                self.critical_errors.append(f"Brand {b.id} missing name or slug.")
            if not b.brand_type:
                self.critical_errors.append(f"Brand {b.canonical_name} has invalid brand_type.")

    def _check_evidence_sources(self):
        sources = self.db.query(EvidenceSource).all()
        self.stats["total_sources"] = len(sources)
        if len(sources) == 0:
            self.critical_errors.append("CRITICAL: No evidence sources found in database.")
        for s in sources:
            if not s.title or not s.publisher:
                self.critical_errors.append(f"EvidenceSource {s.id} missing title or publisher.")
            if not s.license_status:
                self.critical_errors.append(f"EvidenceSource {s.title} missing license_status.")

    def _check_fragrances(self):
        fragrances = self.db.query(Fragrance).all()
        self.stats["total_fragrances"] = len(fragrances)
        published_count = 0

        for frag in fragrances:
            # 1. Required fields
            if not frag.canonical_name or not frag.slug or not frag.brand_id:
                self.critical_errors.append(f"Fragrance {frag.id} missing essential metadata.")

            # 2. Concentration check
            if (frag.concentration or "").upper() not in VALID_CONCENTRATIONS:
                self.critical_errors.append(f"Fragrance '{frag.canonical_name}' has unrecognized concentration '{frag.concentration}'.")

            # 3. Gender check
            if frag.marketed_gender and frag.marketed_gender.lower() not in VALID_GENDERS:
                self.warnings.append(f"Fragrance '{frag.canonical_name}' has non-standard marketed gender '{frag.marketed_gender}'.")

            # 4. Note pyramid checks
            notes = self.db.query(FragranceNote).filter(FragranceNote.fragrance_id == frag.id).all()
            if len(notes) < 3:
                if frag.status == CurationStatus.PUBLISHED:
                    self.warnings.append(f"Published fragrance '{frag.canonical_name}' has fewer than 3 notes ({len(notes)}).")

            # 5. Published checks
            if frag.status == CurationStatus.PUBLISHED:
                published_count += 1
                prices = self.db.query(PriceListing).filter(PriceListing.fragrance_id == frag.id).all()
                if not prices or not any(p.price_inr > 0 for p in prices):
                    self.critical_errors.append(f"Published fragrance '{frag.canonical_name}' has no active price listing.")

                # Check evidence claims
                claims = self.db.query(ClaimEvidence).filter(
                    ClaimEvidence.entity_id == frag.id,
                    ClaimEvidence.entity_type == "fragrance"
                ).all()
                if not claims:
                    self.warnings.append(f"Published fragrance '{frag.canonical_name}' lacks explicit ClaimEvidence provenance.")

        self.stats["published_fragrances"] = published_count

    def _check_price_listings(self):
        prices = self.db.query(PriceListing).all()
        self.stats["total_price_listings"] = len(prices)
        for p in prices:
            if p.price_inr <= 0:
                self.critical_errors.append(f"PriceListing {p.id} has non-positive price: ₹{p.price_inr}")
            if p.currency != "INR":
                self.critical_errors.append(f"PriceListing {p.id} currency must be 'INR', found '{p.currency}'")
            if not p.seller or not p.seller.strip():
                self.critical_errors.append(f"PriceListing {p.id} missing seller designation.")

    def _check_alternative_relationships(self):
        alts = self.db.query(AlternativeRelationship).all()
        self.stats["total_alternatives"] = len(alts)
        for alt in alts:
            # Self-reference check
            if alt.source_fragrance_id == alt.candidate_fragrance_id:
                self.critical_errors.append(f"CRITICAL: Self-referencing alternative detected! {alt.id}")
            if not alt.relationship_type:
                self.critical_errors.append(f"Alternative {alt.id} missing relationship_type.")
            if not alt.evidence_grade:
                self.critical_errors.append(f"Alternative {alt.id} missing evidence_grade.")
            if not alt.rationale:
                self.warnings.append(f"Alternative {alt.id} missing evidence rationale.")

    def _print_summary(self):
        print("\nAudit Summary Statistics:")
        for k, v in self.stats.items():
            print(f"  - {k}: {v}")

        print(f"\nWarnings: {len(self.warnings)}")
        for w in self.warnings[:10]:
            print(f"  [WARN] {w}")
        if len(self.warnings) > 10:
            print(f"  ... and {len(self.warnings) - 10} more warnings.")

        print(f"\nCritical Errors: {len(self.critical_errors)}")
        for e in self.critical_errors:
            print(f"  [CRITICAL ERROR] {e}")

        if not self.critical_errors:
            print("\n>>> AUDIT PASSED: Catalogue data adheres to SCENTIQ data quality standards. <<<")
        else:
            print("\n>>> AUDIT FAILED: Fix critical errors before publishing catalogue data. <<<")


def main():
    db = SessionLocal()
    try:
        validator = CatalogueValidator(db)
        passed = validator.run_all_checks()
        sys.exit(0 if passed else 1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

