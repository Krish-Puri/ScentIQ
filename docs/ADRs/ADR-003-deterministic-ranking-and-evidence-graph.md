# ADR-003: Deterministic Evidence-Led Ranking & Guardrails for AI

## Context
A major failure mode in modern fragrance discovery is ungrounded AI chatbots that fabricate notes, invent clone percentages (e.g. "95% identical"), or recommend out-of-stock / non-existent perfumes.
Furthermore, the PRD mandates:
- "Catalogue before chatbot."
- "Evidence before confidence."
- "Deterministic recommendations before LLM-generated recommendations."

## Decision
1. **Multi-Factor Deterministic Engine**:
   Recommendations are computed using the transparent formula specified in PRD Section 12.3:
   `score = 0.30 * scent_profile_fit + 0.18 * note_accord_fit + 0.15 * occasion_fit + 0.12 * climate_context_fit + 0.10 * budget_value_fit + 0.08 * performance_fit + 0.07 * evidence_completeness - exclusion_penalties`
2. **Directional Alternative Graph**:
   Alternative relationships are directed (`candidate` -> `reference`). They cannot be symmetric or self-referential. Each link must declare:
   - Relationship type (`BRAND_MARKETED`, `DOCUMENTED_REFERENCE`, `COMMUNITY_REPORTED`, `SIMILAR_PROFILE`).
   - Evidence grade (`A_STRONG`, `B_SUPPORTED`, `C_PROVISIONAL`).
   - Curated rationale & recorded differences.
3. **Dual-Review Moderation Gate**:
   An alternative link starts in `DRAFT` and is hidden from public API endpoints until approved and published by an authenticated reviewer with an audit log.
4. **No Synthetic Percentages**:
   No universal clone percentage is generated without verified blind panel testing protocols.
5. **Sample-First Advice**:
   When profile fit is uncertain or full pyramid data is unrecorded, the platform transparently advises sampling first.

## Consequences
### Positive
- 100% factual explainability.
- Zero AI hallucinations or manufactured longevity claims.
- High consumer trust and adherence to Consumer Protection (E-Commerce) Amendment Rules, 2026.

### Negative
- Requires ongoing curator attention to review and grade incoming candidate alternatives.
