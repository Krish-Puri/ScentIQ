# ADR-006: Recommendation Quality Evaluation, Strict Precedence & Feedback Semantics

## Status
Accepted

## Context
In Milestone 3 of SCENTIQ, our focus shifted to recommendation quality, evaluation metrics, and deterministic preference learning correctness.
Earlier iterations treated feedback loosely: `OWNED` imparted positive scent affinity (+1.2 multiplier), and unrated `TRIED` imparted a positive multiplier (+0.2). This contradicted our core philosophy: ownership or testing does not equate to liking a fragrance's note profile. Additionally, user hard exclusions could theoretically be overridden by temporary session prompts or learned weights.

Furthermore, we needed a rigorous offline Information Retrieval (IR) evaluation framework with ground truth scenarios to mathematically measure recommendation quality and guarantee zero hard safety violations.

## Decision
1. **Explicit Feedback Interpretation Semantics**:
   - `LIKE`: Positive weight (+1.0).
   - `DISLIKE`: Negative weight (-1.0).
   - `NOT_FOR_ME`: Strong negative weight (-1.5).
   - `INTERESTED`: Weak positive (+0.3).
   - `OWNED`: Neutral (0.0). Ownership is recorded strictly as possession, without inflating scent profile weights.
   - `TRIED`:
     * Unrated: Neutral (0.0).
     * Rated >= 4.0: Positive (+1.0).
     * Rated <= 2.5: Negative (-1.0).
     * Neutral ratings (2.5 < rating < 4.0): Neutral (0.0).
   - Separate inferred weights from user explicit preferences; user-selected avoid terms permanently suppress positive learned weights.

2. **Strict Constraint Precedence Hierarchy**:
   - **Level 1 (Hard Constraints)**: Explicitly avoided notes, accords, brands, and hard budget ceilings. MUST NEVER be bypassed by temporary prompts or learned affinities.
   - **Level 2 (Soft Preferences)**: Preferred notes, desired longevity, occasion alignment.
   - **Level 3 (Temporary Query Preferences)**: Apply only to the current search session.

3. **Ambiguity and Conflict Resolution (Clarification State)**:
   - When a user query directly requests an ingredient on their avoid list (e.g. asking for vanilla when profile forbids vanilla), the system enters a clarification state (`conflict_detected=True`, `clarification_needed=True`) and asks the user whether to keep the exclusion, allow it temporarily, or remove it from their profile.
   - Vague queries ("something nice") trigger clarification rather than arbitrary recommendations.

4. **Offline Evaluation Framework**:
   - Standard IR metrics: Precision@5, NDCG@5, Recall@10, Intra-List Diversity, Catalogue Coverage.
   - Hard Safety Requirements: Hard Exclusion Violation Rate = 0.0%, Hard Budget Violation Rate = 0.0%.
   - Benchmarked across 10 diverse scenarios with graded ground-truth relevance judgements.

## Consequences
- Recommendations are provably safe against allergen and preference violations.
- Preference learning is deterministic, idempotent, and avoids count drift upon updates or deletions.
- Transparent explainability is maintained with match cues, caveats, and sample-first recommendations.

