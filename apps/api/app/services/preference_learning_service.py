"""SCENTIQ Preference Learning Service (EPIC-12 & Milestone 3).
Transparent, deterministic preference learning from explicit feedback.
Conforms strictly to PRD Section 10.4, Section 12.3, and Milestone 3 Specifications:
- Semantics:
  * LIKE: Positive (+1.0)
  * DISLIKE: Negative (-1.0)
  * NOT_FOR_ME: Strong negative (-1.5)
  * INTERESTED: Weak positive (+0.3)
  * TRIED (unrated): Neutral (0.0)
  * OWNED: Neutral ownership information (0.0)
  * Highly rated TRIED (>=4.0): Positive (+1.0)
  * Poorly rated TRIED (<=2.5): Negative (-1.0)
  * Neutral rated TRIED (2.5 < rating < 4.0): Neutral (0.0)
- Inferred preferences kept strictly separate from explicit profile preferences.
- User-selected explicit exclusions remain permanently enforced and are never overwritten.
- Ownership alone never increases preference for notes or accords.
- Confidence score and evidence score computed deterministically.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import FeedbackType, CurationStatus
from app.models.evidence import ClaimEvidence
from app.models.user import UserProfile
from app.repositories.user_repo import UserRepository
from app.schemas.user import LearnedPreferencesSummary


@dataclass(frozen=True)
class PreferenceWeightConfig:
    """Configurable, deterministic scoring constants for preference learning."""
    # Feedback action multipliers
    MULTIPLIER_LIKE: float = 1.0
    MULTIPLIER_DISLIKE: float = -1.0
    MULTIPLIER_NOT_FOR_ME: float = -1.5
    MULTIPLIER_INTERESTED: float = 0.3
    MULTIPLIER_TRIED_UNRATED: float = 0.0
    MULTIPLIER_OWNED: float = 0.0
    MULTIPLIER_TRIED_HIGH_RATING: float = 1.0   # rating >= 4.0
    MULTIPLIER_TRIED_LOW_RATING: float = -1.0    # rating <= 2.5
    MULTIPLIER_TRIED_NEUTRAL_RATING: float = 0.0 # 2.5 < rating < 4.0

    # Note / Accord / Family weighting factors
    FAMILY_PRIMARY_WEIGHT: float = 1.5
    FAMILY_SECONDARY_WEIGHT: float = 0.8
    NOTE_WEIGHT: float = 0.7
    ACCORD_BASE_WEIGHT: float = 1.0
    ACCORD_RANK_DECAY: float = 0.15
    ACCORD_MIN_WEIGHT: float = 0.4

    # Calibration targets
    CONFIDENCE_FEEDBACK_THRESHOLD: int = 8


class PreferenceLearningService:
    def __init__(self, db: Session, config: Optional[PreferenceWeightConfig] = None):
        self.db = db
        self.user_repo = UserRepository(db)
        self.config = config or PreferenceWeightConfig()

    def compute_learned_preferences(self, user_id: uuid.UUID) -> LearnedPreferencesSummary:
        feedbacks = self.user_repo.get_feedbacks(user_id)
        profile = self.user_repo.get_profile(user_id)
        hard_avoids = [term.strip().lower() for term in (profile.avoid_terms or []) if term.strip()] if profile else []

        accord_scores: Dict[str, float] = {}
        note_scores: Dict[str, float] = {}
        family_scores: Dict[str, float] = {}

        liked_count = 0
        disliked_count = 0
        owned_count = 0
        neutral_count = 0
        total_evidence_claims = 0
        verified_fragrance_count = 0

        frag_ids = [fb.fragrance_id for fb in feedbacks if fb.fragrance_id]
        if frag_ids:
            claim_ids = list(
                self.db.execute(
                    select(ClaimEvidence.id).where(
                        ClaimEvidence.entity_id.in_(frag_ids),
                        ClaimEvidence.entity_type == "fragrance",
                    )
                ).scalars().all()
            )
            total_evidence_claims = len(claim_ids)

        for fb in feedbacks:
            frag = fb.fragrance
            if not frag:
                continue

            if frag.status == CurationStatus.PUBLISHED:
                verified_fragrance_count += 1

            # Determine action multiplier per Milestone 3 table
            multiplier = 0.0
            if fb.feedback_type == FeedbackType.LIKE:
                multiplier = self.config.MULTIPLIER_LIKE
                liked_count += 1
            elif fb.feedback_type == FeedbackType.DISLIKE:
                multiplier = self.config.MULTIPLIER_DISLIKE
                disliked_count += 1
            elif fb.feedback_type == FeedbackType.NOT_FOR_ME:
                multiplier = self.config.MULTIPLIER_NOT_FOR_ME
                disliked_count += 1
            elif fb.feedback_type == FeedbackType.INTERESTED:
                multiplier = self.config.MULTIPLIER_INTERESTED
            elif fb.feedback_type == FeedbackType.OWNED:
                # Neutral ownership information: 0.0 multiplier
                multiplier = self.config.MULTIPLIER_OWNED
                owned_count += 1
                neutral_count += 1
            elif fb.feedback_type == FeedbackType.TRIED:
                if fb.rating is not None:
                    if fb.rating >= 4.0:
                        multiplier = self.config.MULTIPLIER_TRIED_HIGH_RATING
                        liked_count += 1
                    elif fb.rating <= 2.5:
                        multiplier = self.config.MULTIPLIER_TRIED_LOW_RATING
                        disliked_count += 1
                    else:
                        multiplier = self.config.MULTIPLIER_TRIED_NEUTRAL_RATING
                        neutral_count += 1
                else:
                    # Unrated tried: Neutral 0.0 multiplier
                    multiplier = self.config.MULTIPLIER_TRIED_UNRATED
                    neutral_count += 1

            if multiplier == 0.0:
                continue

            # 1. Family weighting
            if frag.family:
                fam = frag.family.strip().lower()
                family_scores[fam] = family_scores.get(fam, 0.0) + (multiplier * self.config.FAMILY_PRIMARY_WEIGHT)
            if frag.secondary_family:
                sec_fam = frag.secondary_family.strip().lower()
                family_scores[sec_fam] = family_scores.get(sec_fam, 0.0) + (multiplier * self.config.FAMILY_SECONDARY_WEIGHT)

            # 2. Accords weighting
            if frag.accords:
                for fa in frag.accords:
                    if fa.accord:
                        acc_name = fa.accord.canonical_name.strip().lower()
                        rank = getattr(fa, "intensity_rank", 1) or 1
                        rank_weight = max(
                            self.config.ACCORD_BASE_WEIGHT - (rank - 1) * self.config.ACCORD_RANK_DECAY,
                            self.config.ACCORD_MIN_WEIGHT,
                        )
                        accord_scores[acc_name] = accord_scores.get(acc_name, 0.0) + (multiplier * rank_weight)

            # 3. Notes weighting
            if frag.notes:
                for fn in frag.notes:
                    if fn.note:
                        note_name = fn.note.canonical_name.strip().lower()
                        note_scores[note_name] = note_scores.get(note_name, 0.0) + (multiplier * self.config.NOTE_WEIGHT)

        # Enforce hard avoidance: learned positive weights can NEVER override explicit profile avoid terms
        for avoid in hard_avoids:
            if avoid in accord_scores and accord_scores[avoid] > 0:
                accord_scores[avoid] = -2.0
            if avoid in note_scores and note_scores[avoid] > 0:
                note_scores[avoid] = -2.0
            if avoid in family_scores and family_scores[avoid] > 0:
                family_scores[avoid] = -2.0

        # Normalization to [-1.0, 1.0] range
        def normalize_map(scores: Dict[str, float]) -> Dict[str, float]:
            if not scores:
                return {}
            max_abs = max(abs(v) for v in scores.values()) or 1.0
            return {k: round(v / max_abs, 3) for k, v in scores.items() if abs(v) > 0.01}

        # Calculate Confidence Score based on directional feedback volume and presence
        directional_count = liked_count + disliked_count
        if directional_count == 0:
            confidence_score = 0.1 if owned_count > 0 else 0.0
        else:
            raw_confidence = min(1.0, directional_count / float(self.config.CONFIDENCE_FEEDBACK_THRESHOLD))
            # Minor boost if user provides both positive and negative signals (demonstrates discernment)
            if liked_count > 0 and disliked_count > 0:
                raw_confidence = min(1.0, raw_confidence + 0.1)
            confidence_score = round(raw_confidence, 2)

        # Calculate Evidence Score based on verified fragrance data backing the feedback
        total_fragrances = len(feedbacks)
        if total_fragrances == 0:
            evidence_score = 0.0
        else:
            evidence_ratio = verified_fragrance_count / float(total_fragrances)
            claim_bonus = min(0.2, (total_evidence_claims / float(max(total_fragrances, 1))) * 0.1)
            evidence_score = round(min(1.0, evidence_ratio * 0.8 + claim_bonus), 2)

        return LearnedPreferencesSummary(
            total_feedbacks=len(feedbacks),
            liked_count=liked_count,
            disliked_count=disliked_count,
            owned_count=owned_count,
            neutral_count=neutral_count,
            confidence_score=confidence_score,
            evidence_score=evidence_score,
            evidence_count=total_evidence_claims,
            inferred_accord_weights=normalize_map(accord_scores),
            inferred_note_weights=normalize_map(note_scores),
            inferred_family_weights=normalize_map(family_scores),
            hard_avoid_terms=hard_avoids,
        )
