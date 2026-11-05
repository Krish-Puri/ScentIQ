"""SCENTIQ Preference Learning Service (EPIC-12).
Transparent, deterministic preference learning from explicit feedback.
Conforms strictly to PRD Section 10.4 and Section 12.3:
- Inferred preferences kept separate from explicit profile preferences.
- User-selected explicit exclusions remain permanently enforced.
- No black-box ML or unexplainable weights.
"""
from typing import Dict, List, Optional
import uuid
from sqlalchemy.orm import Session

from app.models.enums import FeedbackType
from app.models.user import UserProfile
from app.repositories.user_repo import UserRepository
from app.schemas.user import LearnedPreferencesSummary


class PreferenceLearningService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def compute_learned_preferences(self, user_id: uuid.UUID) -> LearnedPreferencesSummary:
        feedbacks = self.user_repo.get_feedbacks(user_id)
        profile = self.user_repo.get_profile(user_id)
        hard_avoids = profile.avoid_terms if (profile and profile.avoid_terms) else []

        accord_scores: Dict[str, float] = {}
        note_scores: Dict[str, float] = {}
        family_scores: Dict[str, float] = {}

        liked_count = 0
        disliked_count = 0
        owned_count = 0

        for fb in feedbacks:
            frag = fb.fragrance
            if not frag:
                continue

            # Determine multiplier
            multiplier = 0.0
            if fb.feedback_type == FeedbackType.LIKE:
                multiplier = 1.0
                liked_count += 1
            elif fb.feedback_type == FeedbackType.OWNED:
                multiplier = 1.2
                owned_count += 1
            elif fb.feedback_type == FeedbackType.INTERESTED:
                multiplier = 0.5
            elif fb.feedback_type == FeedbackType.TRIED:
                if fb.rating and fb.rating >= 4.0:
                    multiplier = 1.0
                    liked_count += 1
                elif fb.rating and fb.rating <= 2.5:
                    multiplier = -1.0
                    disliked_count += 1
                else:
                    multiplier = 0.2
            elif fb.feedback_type in (FeedbackType.DISLIKE, FeedbackType.NOT_FOR_ME):
                multiplier = -1.2
                disliked_count += 1

            if multiplier == 0.0:
                continue

            # 1. Family weighting
            if frag.family:
                fam = frag.family.strip().lower()
                family_scores[fam] = family_scores.get(fam, 0.0) + multiplier * 1.5
            if frag.secondary_family:
                sec_fam = frag.secondary_family.strip().lower()
                family_scores[sec_fam] = family_scores.get(sec_fam, 0.0) + multiplier * 0.8

            # 2. Accords weighting
            if frag.accords:
                for fa in frag.accords:
                    if fa.accord:
                        acc_name = fa.accord.canonical_name.strip().lower()
                        # Rank 1 has higher impact than Rank 5
                        rank_weight = max(1.0 - (fa.intensity_rank - 1) * 0.15, 0.4)
                        accord_scores[acc_name] = accord_scores.get(acc_name, 0.0) + (multiplier * rank_weight)

            # 3. Notes weighting
            if frag.notes:
                for fn in frag.notes:
                    if fn.note:
                        note_name = fn.note.canonical_name.strip().lower()
                        note_scores[note_name] = note_scores.get(note_name, 0.0) + (multiplier * 0.7)

        # Normalize scores to [-1.0, 1.0] range
        def normalize_map(scores: Dict[str, float]) -> Dict[str, float]:
            if not scores:
                return {}
            max_abs = max(abs(v) for v in scores.values()) or 1.0
            return {k: round(v / max_abs, 3) for k, v in scores.items() if abs(v) > 0.01}

        return LearnedPreferencesSummary(
            total_feedbacks=len(feedbacks),
            liked_count=liked_count,
            disliked_count=disliked_count,
            owned_count=owned_count,
            inferred_accord_weights=normalize_map(accord_scores),
            inferred_note_weights=normalize_map(note_scores),
            inferred_family_weights=normalize_map(family_scores),
            hard_avoid_terms=hard_avoids,
        )
