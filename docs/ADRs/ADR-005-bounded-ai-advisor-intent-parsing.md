# ADR-005: Bounded AI Fragrance Advisor Intent Parsing and Grounded Engine Integration

## Context
Users frequently articulate fragrance requirements in natural conversational language (e.g., "I want a fresh, slightly woody perfume for office use under ₹2,500 without overly sweet notes").

Core PRD principles require:
- The LLM must never invent recommendations, clone relationships, prices, performance claims, or similarity percentages.
- The deterministic recommendation engine remains the sole source of recommendation ranking and scoring.
- Bounded intent-parsing service with strict Pydantic validation.
- Zero downtime: robust fallback when external LLM APIs are unconfigured or unavailable.

## Decision
1. **Pipeline Architecture**:
   `User Message` → `Intent Extraction` → `Schema Validation (ParsedAdvisorIntent)` → `Profile Merge (Strict Avoid Enforcement)` → `Deterministic Recommendation Engine` → `Grounded Narrative Explanation`.
2. **Dual-Mode Intent Parser**:
   - LLM mode (via Gemini API structured JSON schema) when API key is provided.
   - Deterministic rule-based NLP fallback (regex-based budget, avoid-term parsing, keyword family and accord mapping) when LLM is unconfigured, unreachable, or fails schema validation.
3. **Evidence-Grounded Explanations**:
   - The advisor narrative is generated strictly from the returned fragrance attributes, matched cues, budget ceiling compliance, and verified claim evidences.

## Status
Accepted and Implemented.

## Consequences
- Total protection against AI hallucinations and fake fragrance claims.
- High resilience and offline testability via deterministic fallback parser.
- Transparent constraint extraction surfaced directly in the UI.
