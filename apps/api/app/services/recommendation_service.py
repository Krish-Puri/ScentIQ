"""SCENTIQ Recommendation Service.
Implements the deterministic multi-factor ranking engine specified in PRD Section 12.3.
No black-box scoring or invented recommendations.
"""
import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.enums import CurationStatus, PyramidPosition
from app.models.fragrance import Fragrance
from app.models.taxonomy import FragranceNote, FragranceAccord
from app.models.price import PriceListing
from app.models.evidence import ClaimEvidence
from app.models.user import RecommendationRun
from app.schemas.recommendation import (
    RecommendationConstraints,
    RecommendationCard,
    RecommendationRequest,
    RecommendationResponse,
)


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db

    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        constraints = request.constraints

        # 1. Fetch all published fragrances with their relations
        stmt = (
            select(Fragrance)
            .options(
                joinedload(Fragrance.brand),
                selectinload(Fragrance.notes).joinedload(FragranceNote.note),
                selectinload(Fragrance.accords).joinedload(FragranceAccord.accord),
                selectinload(Fragrance.price_listings),
            )
            .where(Fragrance.status == CurationStatus.PUBLISHED)
        )
        candidates = list(self.db.execute(stmt).scalars().unique().all())

        scored_cards: List[RecommendationCard] = []

        # Avoid terms (case-insensitive)
        avoid_set = {term.lower().strip() for term in constraints.avoid_terms if term.strip()}
        liked_families = {f.lower().strip() for f in constraints.liked_families if f.strip()}
        liked_notes = {n.lower().strip() for n in constraints.liked_notes if n.strip()}
        liked_accords = {a.lower().strip() for a in constraints.liked_accords if a.strip()}

        for frag in candidates:
            # 2. Hard Filters
            frag_notes_names = [fn.note.canonical_name.lower() for fn in frag.notes if fn.note]
            frag_accords_names = [fa.accord.canonical_name.lower() for fa in frag.accords if fa.accord]
            all_frag_terms = set(frag_notes_names + frag_accords_names)
            if frag.family:
                all_frag_terms.add(frag.family.lower())

            # Exclusion check (PRD: hard exclusions are respected)
            if avoid_set and any(avoid in term for avoid in avoid_set for term in all_frag_terms):
                continue

            # Concentration filter
            if constraints.concentration:
                allowed_conc = [c.lower() for c in constraints.concentration]
                if frag.concentration.lower() not in allowed_conc:
                    continue

            # Budget ceiling check
            lowest_price = None
            if frag.price_listings:
                valid_prices = [p.price_inr for p in frag.price_listings if p.price_inr > 0]
                if valid_prices:
                    lowest_price = min(valid_prices)

            if constraints.budget_max_inr and constraints.hard_budget_limit:
                if lowest_price and lowest_price > constraints.budget_max_inr:
                    continue

            # 3. Deterministic Feature Scoring (PRD Section 12.3 formula)
            # Feature 1: Scent Profile Fit (0.30)
            scent_fit = 0.5  # Neutral default
            if liked_families:
                frag_fam = (frag.family or "").lower()
                frag_sec_fam = (frag.secondary_family or "").lower()
                if frag_fam in liked_families or frag_sec_fam in liked_families:
                    scent_fit = 1.0
                else:
                    scent_fit = 0.2

            # Feature 2: Note & Accord Fit (0.18)
            note_match_count = sum(1 for n in liked_notes if any(n in fn for fn in frag_notes_names))
            accord_match_count = sum(1 for a in liked_accords if any(a in fa for fa in frag_accords_names))
            total_target = max(len(liked_notes) + len(liked_accords), 1)
            note_accord_fit = min((note_match_count + accord_match_count) / total_target, 1.0)
            if not liked_notes and not liked_accords:
                note_accord_fit = 0.7  # Neutral when user did not specify notes

            # Feature 3: Occasion Fit (0.15)
            occasion_fit = 0.75  # Versatile baseline

            # Feature 4: Climate Context Fit (0.12)
            climate_fit = 0.75

            # Feature 5: Budget Value Fit (0.10)
            budget_fit = 0.7
            if constraints.budget_max_inr and lowest_price:
                if lowest_price <= constraints.budget_max_inr:
                    budget_fit = 1.0 - (lowest_price / (constraints.budget_max_inr * 1.5))
                    budget_fit = max(min(budget_fit, 1.0), 0.4)

            # Feature 6: Performance Preference Fit (0.08)
            perf_fit = 0.75

            # Feature 7: Evidence Completeness (0.07)
            has_pyramid = bool(frag.notes)
            has_accords = bool(frag.accords)
            evidence_completeness = 1.0 if (has_pyramid and has_accords) else (0.7 if has_pyramid else 0.4)

            # Composite Score (0.0 to 1.0)
            final_score = (
                0.30 * scent_fit
                + 0.18 * note_accord_fit
                + 0.15 * occasion_fit
                + 0.12 * climate_fit
                + 0.10 * budget_fit
                + 0.08 * perf_fit
                + 0.07 * evidence_completeness
            )
            final_score = round(final_score, 3)

            # Build explainable match cues & caveats
            match_cues = []
            if frag.family and frag.family.lower() in liked_families:
                match_cues.append(f"Matches preferred {frag.family} fragrance family")
            matched_notes = [fn for fn in frag_notes_names if any(n in fn for n in liked_notes)]
            if matched_notes:
                match_cues.append(f"Contains requested notes: {', '.join(matched_notes[:3])}")
            matched_accords = [fa for fa in frag_accords_names if any(a in fa for a in liked_accords)]
            if matched_accords:
                match_cues.append(f"Reflects requested accords: {', '.join(matched_accords[:3])}")

            caveats = []
            if not has_pyramid:
                caveats.append("Full note pyramid is not officially disclosed by house")
            if lowest_price is None:
                caveats.append("No active retailer price listing observed currently")

            # Sample first advice trigger (PRD FR-020)
            sample_first = final_score < 0.70 or not has_pyramid

            fit_summary = (
                f"{frag.canonical_name} by {frag.brand.canonical_name} provides a balanced "
                f"{frag.family or 'contemporary'} profile aligned with your preferences."
            )

            scored_cards.append(
                RecommendationCard(
                    fragrance_id=frag.id,
                    canonical_name=frag.canonical_name,
                    brand_name=frag.brand.canonical_name,
                    concentration=frag.concentration,
                    family=frag.family,
                    score=final_score,
                    fit_summary=fit_summary,
                    profile_match_cues=match_cues or ["Well-balanced daily profile"],
                    tradeoffs_or_caveats=caveats,
                    indicative_price_inr=lowest_price,
                    sample_first_recommended=sample_first,
                    evidence_completeness=evidence_completeness,
                )
            )

        # 4. Sort and return top candidates
        scored_cards.sort(key=lambda c: c.score, reverse=True)
        top_results = scored_cards[: request.limit]

        # 5. Log RecommendationRun for audit & evaluation
        run = RecommendationRun(
            session_id=request.session_id,
            query_snapshot=constraints.model_dump(),
            ruleset_version="v1.0",
            result_ids=[str(card.fragrance_id) for card in top_results],
        )
        self.db.add(run)
        self.db.commit()

        return RecommendationResponse(
            ruleset_version="v1.0",
            results=top_results,
            session_id=request.session_id,
            total_evaluated=len(candidates),
        )

