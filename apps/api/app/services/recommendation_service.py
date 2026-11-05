"""SCENTIQ Recommendation Service.
Implements the deterministic multi-factor ranking engine specified in PRD Section 12.3.
No black-box scoring or invented recommendations.
Personalized preference learning and profile integration per EPIC-07 and EPIC-12.
"""
from typing import List, Optional, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.enums import CurationStatus, PyramidPosition
from app.models.fragrance import Fragrance
from app.models.taxonomy import FragranceNote, FragranceAccord
from app.models.price import PriceListing
from app.models.evidence import ClaimEvidence
from app.models.user import RecommendationRun, UserProfile
from app.repositories.user_repo import UserRepository
from app.services.preference_learning_service import PreferenceLearningService
from app.schemas.recommendation import (
    RecommendationConstraints,
    RecommendationCard,
    RecommendationRequest,
    RecommendationResponse,
)


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.learning_service = PreferenceLearningService(db)

    def recommend(
        self, request: RecommendationRequest, user_id: Optional[uuid.UUID] = None
    ) -> RecommendationResponse:
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

        # Merge profile if user_id is provided
        learned_accords = {}
        learned_notes = {}
        if user_id:
            profile = self.user_repo.get_profile(user_id)
            if profile:
                if profile.avoid_terms:
                    avoid_set.update(term.lower().strip() for term in profile.avoid_terms if term.strip())
                if not liked_families and profile.preferred_families:
                    liked_families.update(f.lower().strip() for f in profile.preferred_families if f.strip())
                if not liked_notes and profile.preferred_notes:
                    liked_notes.update(n.lower().strip() for n in profile.preferred_notes if n.strip())
                if not liked_accords and profile.preferred_accords:
                    liked_accords.update(a.lower().strip() for a in profile.preferred_accords if a.strip())
                if constraints.budget_max_inr is None and profile.budget_max:
                    constraints.budget_max_inr = profile.budget_max

            # Load feedback-derived preference learning
            learned = self.learning_service.compute_learned_preferences(user_id)
            learned_accords = learned.inferred_accord_weights
            learned_notes = learned.inferred_note_weights

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
            occasion_fit = 0.7  # Standard versatile default

            # Feature 4: Climate Context Fit (0.12)
            climate_fit = 0.8  # Standard neutral

            # Feature 5: Performance Expectation (0.10)
            perf_fit = 0.75  # Standard concentration benchmark

            # Feature 6: Value / Price Competitiveness (0.10)
            value_fit = 0.8
            if lowest_price and constraints.budget_max_inr:
                if lowest_price <= constraints.budget_max_inr:
                    value_fit = 1.0
                else:
                    value_fit = max(1.0 - ((lowest_price - constraints.budget_max_inr) / constraints.budget_max_inr), 0.0)

            # Feature 7: Evidence Completeness (0.05)
            has_pyramid = len(frag.notes) >= 3
            claims_count = len(getattr(frag, "claim_evidences", []))
            evidence_completeness = min((claims_count * 0.4) + (0.8 if has_pyramid else 0.4), 1.0)

            # Combined Baseline Score
            baseline_score = (
                (scent_fit * 0.30)
                + (note_accord_fit * 0.18)
                + (occasion_fit * 0.15)
                + (climate_fit * 0.12)
                + (perf_fit * 0.10)
                + (value_fit * 0.10)
                + (evidence_completeness * 0.05)
            )

            # 4. Personalised Preference Learning Adjustment (EPIC-12)
            feedback_affinity = 0.0
            for fa in frag_accords_names:
                for k, weight in learned_accords.items():
                    if k in fa:
                        feedback_affinity += weight * 0.05
            for fn in frag_notes_names:
                for k, weight in learned_notes.items():
                    if k in fn:
                        feedback_affinity += weight * 0.03

            # Clamp final score
            final_score = round(max(min(baseline_score + feedback_affinity, 1.0), 0.05), 3)

            # Match cues & caveats
            match_cues = []
            if scent_fit >= 0.8 and frag.family:
                match_cues.append(f"Strong match for {frag.family} scent profile")
            matched_notes = [fn for fn in frag_notes_names if any(n in fn for n in liked_notes)]
            if matched_notes:
                match_cues.append(f"Includes requested notes: {', '.join(matched_notes[:3])}")
            matched_accords = [fa for fa in frag_accords_names if any(a in fa for a in liked_accords)]
            if matched_accords:
                match_cues.append(f"Reflects requested accords: {', '.join(matched_accords[:3])}")
            if feedback_affinity > 0.04:
                match_cues.append("Positively boosted based on your fragrance feedback history")

            caveats = []
            if feedback_affinity < -0.04:
                caveats.append("Contains notes/accords related to fragrances you previously rated lower")
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

        # 5. Sort and return top candidates
        scored_cards.sort(key=lambda c: c.score, reverse=True)
        top_results = scored_cards[: request.limit]

        # 6. Log RecommendationRun for audit & evaluation
        run = RecommendationRun(
            user_id=user_id,
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
