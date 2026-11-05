# ADR-004: User Personalisation, Preference Isolation and Deterministic Learning

## Context
SCENTIQ evolves from a static fragrance catalogue into a personal decision-support application (EPIC-07, EPIC-12). Users need a tailored experience that respects their experience level, preferred olfactory families, loved and avoided notes, budget constraints, and active wear feedback.

Key PRD principles dictate:
- No sensitive demographic tracking or ungrounded profiling.
- Explicit preferences (user profile) must remain distinct from inferred preferences (learned from feedback).
- Automatic preference learning must never overwrite user-defined preferences or bypass explicit exclusions.
- Recommendations must remain explainable and transparent.

## Decision
1. **User Profile Architecture**:
   - `UserProfile` model stores user-defined preferences (familiarity level, preferred families, notes, accords, budget ceiling, preferred concentrations, occasions, and avoid terms).
   - Strict data isolation: authenticated endpoints (`/api/v1/users/me/*`) ensure User A cannot view or manipulate User B's profile.
2. **Deterministic Preference Learning**:
   - `PreferenceLearningService` analyzes explicit user feedback (LIKE, DISLIKE, OWNED, TRIED).
   - Derives normalized affinity weights for accords and notes.
   - Generates transparent breakdown (`/api/v1/users/me/preferences/learned`) showing exact affinity adjustments.
3. **Recommendation Integration**:
   - `RecommendationService` applies learned affinity adjustments as explainable score bonuses/penalties (+/- 0.05).
   - Hard exclusions (avoid terms) are merged with query constraints and remain strictly non-negotiable.

## Status
Accepted and Implemented.

## Consequences
- Guaranteed reproducibility of recommendations.
- Zero black-box drift or invasive tracking.
- Complete user control over personal data and explicit exclusions.
