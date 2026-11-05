"""SCENTIQ AI Fragrance Advisor Service (EPIC-11 & Milestone 3).
Translates natural language into validated recommendation constraints.
Grounds all recommendations in the deterministic ranking engine.
Includes:
- Robust NLP intent extraction with benchmark query coverage
- Strict Constraint Precedence Hierarchy:
  1. Hard constraints (avoid exclusions, hard budget limit) - NEVER bypassed
  2. Soft preferences (preferred notes, desired longevity, occasion fit)
  3. Temporary query preferences
- Ambiguity and Conflict Detection (Clarification State)
- Adversarial & Prompt Injection Robustness
- Verified Catalogue Grounding & Hallucination Prevention
"""
import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import CurationStatus
from app.models.user import UserProfile
from app.models.fragrance import Fragrance
from app.models.alternative import AlternativeRelationship
from app.repositories.user_repo import UserRepository
from app.schemas.advisor import (
    AdvisorRecommendRequest,
    AdvisorRecommendResponse,
    ParsedAdvisorIntent,
)
from app.schemas.recommendation import (
    RecommendationCard,
    RecommendationConstraints,
    RecommendationRequest,
)
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger("scentiq.advisor")

KNOWN_FAMILIES = [
    "fresh", "citrus", "aquatic", "woody", "aromatic",
    "musky", "amber", "spicy", "floral", "gourmand", "leather", "oud", "chypre"
]

KNOWN_ACCORDS = [
    "fresh", "woody", "citrus", "aquatic", "aromatic", "spicy",
    "sweet", "amber", "musky", "floral", "warm spicy", "fresh spicy",
    "powdery", "leather", "smoky", "mineral", "fruity"
]

KNOWN_NOTES = [
    "bergamot", "cedarwood", "vanilla", "sandalwood", "vetiver",
    "rose", "lavender", "cardamom", "patchouli", "neroli", "lemon",
    "grapefruit", "apple", "pink pepper", "tonka bean", "cinnamon",
    "pineapple", "blackcurrant", "birch", "ambergris", "musk", "flint", "oud"
]

OCCASIONS_MAP = {
    "office": ["office", "work", "professional", "desk", "corporate", "formal"],
    "party": ["party", "club", "clubbing", "night out"],
    "date": ["date", "date night", "romantic", "intimate", "evening"],
    "casual": ["casual", "daily", "everyday", "errands", "college"],
    "summer": ["summer", "hot", "tropical", "beach", "humid", "heat", "hot weather"],
    "winter": ["winter", "cold", "autumn", "fall", "cold weather"],
    "gym": ["gym", "workout", "sport", "athletic"],
    "versatile": ["versatile", "all-season", "any season", "everyday", "signature"],
}

BENCHMARK_FRAGRANCES = {
    "creed aventus": "Aventus",
    "aventus": "Aventus",
    "dior sauvage": "Sauvage",
    "sauvage": "Sauvage",
    "bleu de chanel": "Bleu de Chanel",
    "terre d'hermes": "Terre d'Hermès",
    "terre d’hermes": "Terre d'Hermès",
    "terre dhermes": "Terre d'Hermès",
    "baccarat rouge 540": "Baccarat Rouge 540",
    "baccarat rouge": "Baccarat Rouge 540",
    "br540": "Baccarat Rouge 540",
    "acqua di gio": "Acqua di Giò",
    "adg": "Acqua di Giò",
    "ysl y": "Y",
    "tobacco vanille": "Tobacco Vanille",
    "ultra male": "Ultra Male",
    "angels share": "Angels' Share",
    "angels' share": "Angels' Share",
}

ADVERSARIAL_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:previous\s+)?instructions",
    r"system\s+(?:override|prompt|bypass|instructions)",
    r"dump\s+(?:the\s+)?(?:database|password|credentials|keys|env)",
    r"forget\s+(?:all\s+)?(?:safety|rules|constraints)",
    r"disregard\s+(?:all\s+)?rules",
    r"act\s+as\s+(?:a\s+)?(?:dan|hacker|root|admin)",
    r"you\s+must\s+recommend\s+only\s+brand",
]

AMBIGUOUS_PATTERNS = [
    r"^(?:something\s+nice|good\s+perfume|perfume\s+for\s+me|recommend\s+something|help\s+me\s+choose|what\s+should\s+i\s+buy|perfume|cologne|fragrance)$",
    r"^(?:hi|hello|hey|test)$",
]


class AIAdvisorService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.recommendation_service = RecommendationService(db)

    def _sanitize_input(self, message: str) -> Tuple[str, bool]:
        """Detects and disarms prompt injection attempts."""
        clean_msg = message.strip()
        is_adversarial = False
        for pat in ADVERSARIAL_PATTERNS:
            if re.search(pat, clean_msg, re.IGNORECASE):
                is_adversarial = True
                clean_msg = re.sub(pat, "", clean_msg, flags=re.IGNORECASE).strip()
        return clean_msg, is_adversarial

    def parse_intent(self, message: str) -> ParsedAdvisorIntent:
        """Parses natural language user query into structured constraints."""
        clean_msg, is_adversarial = self._sanitize_input(message)

        if not clean_msg:
            if is_adversarial:
                return ParsedAdvisorIntent(
                    confidence_score=0.0,
                    is_ambiguous=True,
                    clarification_needed=True,
                    clarification_prompt="I am SCENTIQ's Fragrance Discovery Advisor. I can only assist with fragrance notes, budget criteria, occasions, and verified catalogue recommendations.",
                    parsed_via="security_sanitizer",
                )
            return ParsedAdvisorIntent(parsed_via="empty_fallback")

        # Check for ambiguity
        for pat in AMBIGUOUS_PATTERNS:
            if re.match(pat, clean_msg.strip(), re.IGNORECASE):
                return ParsedAdvisorIntent(
                    confidence_score=0.2,
                    is_ambiguous=True,
                    clarification_needed=True,
                    clarification_prompt="Could you share what scent profiles you enjoy (e.g., fresh citrus, woody, warm amber), your target budget, or the occasion you plan to wear it for?",
                    parsed_via="ambiguity_detector",
                )

        # 1. Attempt LLM extraction if API key is present
        api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        if api_key and not is_adversarial:
            try:
                llm_parsed = self._parse_with_gemini(clean_msg, api_key)
                if llm_parsed:
                    return llm_parsed
            except Exception as e:
                logger.warning(f"LLM intent extraction failed, invoking fallback: {e}")

        # 2. Deterministic rule-based parser fallback
        return self._parse_rule_based(clean_msg)

    def _parse_with_gemini(self, message: str, api_key: str) -> Optional[ParsedAdvisorIntent]:
        """Calls Gemini API with structured schema when key is available."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
You are a fragrance taxonomy intent extractor.
Convert this user query into a JSON object matching this schema:
{{
  "budget_max": number or null,
  "currency": "INR",
  "preferred_families": string[],
  "preferred_accords": string[],
  "preferred_notes": string[],
  "excluded_characteristics": string[],
  "occasions": string[],
  "concentration": string[],
  "reference_fragrances": string[],
  "is_alternative_search": boolean,
  "target_longevity": string or null
}}

User query: "{message}"

Return ONLY valid JSON.
"""
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            data = json.loads(text.strip())
            return ParsedAdvisorIntent(
                budget_max=data.get("budget_max"),
                currency=data.get("currency", "INR"),
                preferred_families=data.get("preferred_families", []),
                preferred_accords=data.get("preferred_accords", []),
                preferred_notes=data.get("preferred_notes", []),
                excluded_characteristics=data.get("excluded_characteristics", []),
                occasions=data.get("occasions", []),
                concentration=data.get("concentration", []),
                reference_fragrances=data.get("reference_fragrances", []),
                is_alternative_search=data.get("is_alternative_search", False),
                target_longevity=data.get("target_longevity"),
                confidence_score=0.95,
                parsed_via="gemini_llm",
            )
        except Exception as err:
            logger.debug(f"Gemini API parse attempt failed: {err}")
            return None

    def _parse_rule_based(self, message: str) -> ParsedAdvisorIntent:
        """Deterministic NLP intent extraction handling the 9 benchmark scenarios."""
        lower_msg = message.lower()

        # 1. Budget extraction (INR)
        budget_max = None
        budget_patterns = [
            r"(?:under|below|max|within|budget(?:\s+of)?|up\s+to|less\s+than)\s*(?:₹|rs\.?|inr)?\s*([0-9]+(?:,[0-9]{3})*|\b[0-9]{3,6}\b)\s*(?:₹|rs\.?|inr|rupees)?",
            r"(?:₹|rs\.?)\s*([0-9]+(?:,[0-9]{3})*|\b[0-9]{3,6}\b)",
            r"([0-9]+(?:,[0-9]{3})*|\b[0-9]{3,6}\b)\s*(?:inr|rupees)",
        ]
        for pat in budget_patterns:
            match = re.search(pat, lower_msg)
            if match:
                val_str = match.group(1).replace(",", "")
                try:
                    val = float(val_str)
                    if 200 <= val <= 500000:
                        budget_max = val
                        break
                except ValueError:
                    continue

        # 2. Reference Fragrance & Alternative Search detection
        reference_fragrances = []
        is_alt = bool(re.search(r"\b(?:alternative|alternatives|similar|clone|dupe|inspired\s+by|replacement)\b", lower_msg))
        for key, canonical in BENCHMARK_FRAGRANCES.items():
            if re.search(r"\b" + re.escape(key) + r"\b", lower_msg):
                reference_fragrances.append(canonical)
                if "loved" in lower_msg or "like" in lower_msg or "similar" in lower_msg or "alternative" in lower_msg:
                    is_alt = True

        # 3. Exclusions (avoid / dislike / absolutely no)
        excluded = []
        avoid_patterns = [
            r"(?:absolutely\s+no|no|avoid|without|hate|dislike|don'?t\s+like|dont\s+like|not\s+too|not\s+overly|doesn'?t\s+smell(?:\s+overly)?)\s+([a-zA-Z\s]+?)(?=[,.]|\band\b|\bbut\b|\bfor\b|\bunder\b|\bwith\b|\bmy\b|$)",
        ]
        for pat in avoid_patterns:
            for match in re.finditer(pat, lower_msg):
                raw = match.group(1).strip()
                for token in re.split(r"\s+or\s+|\s+and\s+|\s+", raw):
                    clean_w = token.strip(" ,.")
                    if clean_w in KNOWN_NOTES or clean_w in KNOWN_ACCORDS or clean_w in ("sweet", "synthetic", "heavy", "gourmand"):
                        excluded.append(clean_w)
                if raw and raw in ("synthetic", "sweet notes", "sweet"):
                    clean_raw = raw.replace("notes", "").strip()
                    if clean_raw not in excluded:
                        excluded.append(clean_raw)

        # 4. Preferred families & accords
        searchable_text = lower_msg
        for exc in excluded:
            searchable_text = searchable_text.replace(exc, "")

        preferred_families = []
        preferred_accords = []
        preferred_notes = []

        for fam in KNOWN_FAMILIES:
            if re.search(r"\b" + re.escape(fam) + r"\b", searchable_text):
                preferred_families.append(fam)

        for acc in KNOWN_ACCORDS:
            if re.search(r"\b" + re.escape(acc) + r"\b", searchable_text):
                preferred_accords.append(acc)

        for note in KNOWN_NOTES:
            if re.search(r"\b" + re.escape(note) + r"\b", searchable_text):
                preferred_notes.append(note)

        # 5. Occasions & Climate
        occasions = []
        climate_context = []
        for occ_key, keywords in OCCASIONS_MAP.items():
            if any(re.search(r"\b" + re.escape(kw) + r"\b", lower_msg) for kw in keywords):
                occasions.append(occ_key)
                if occ_key in ("summer", "winter"):
                    climate_context.append(occ_key)

        if "humid" in lower_msg or "mumbai" in lower_msg or "heat" in lower_msg:
            if "summer" not in occasions:
                occasions.append("summer")
            if "humid" not in climate_context:
                climate_context.append("humid")

        # 6. Longevity / Performance
        target_longevity = None
        if re.search(r"\b(?:long-lasting|high\s+longevity|better\s+performance|lasts\s+long|beast\s+mode)\b", lower_msg):
            target_longevity = "high"

        # 7. Concentration
        concentrations = []
        if "edp" in lower_msg or "eau de parfum" in lower_msg:
            concentrations.append("EDP")
        if "edt" in lower_msg or "eau de toilette" in lower_msg:
            concentrations.append("EDT")
        if "parfum" in lower_msg or "extrait" in lower_msg:
            concentrations.append("Parfum")

        # Determine if query has sufficient specificity
        has_criteria = (
            budget_max is not None
            or bool(reference_fragrances)
            or bool(preferred_families)
            or bool(preferred_accords)
            or bool(preferred_notes)
            or bool(occasions)
        )

        return ParsedAdvisorIntent(
            budget_max=budget_max,
            currency="INR",
            preferred_families=list(set(preferred_families)),
            preferred_accords=list(set(preferred_accords)),
            preferred_notes=list(set(preferred_notes)),
            excluded_characteristics=list(set(excluded)),
            occasions=list(set(occasions)),
            concentration=concentrations,
            climate_context=list(set(climate_context)),
            reference_fragrances=reference_fragrances,
            is_alternative_search=is_alt,
            target_longevity=target_longevity,
            is_ambiguous=not has_criteria,
            clarification_needed=not has_criteria,
            clarification_prompt="Could you share what scent profiles you enjoy, your target budget, or the occasion you plan to wear it for?" if not has_criteria else None,
            confidence_score=0.90 if has_criteria else 0.30,
            parsed_via="rule_based_fallback",
        )

    def recommend_with_advisor(
        self,
        request: AdvisorRecommendRequest,
        user_id: Optional[uuid.UUID] = None,
    ) -> AdvisorRecommendResponse:
        """End-to-end bounded advisor pipeline with strict constraint precedence:
        1. Input Sanitization & Intent Extraction
        2. Ambiguity Check (Clarification State)
        3. Profile Merge & Conflict Resolution (Precedence: Hard Exclusions > Soft Prefs > Query)
        4. Deterministic Catalogue Ranking Engine
        5. Grounded Narrative Explanation
        """
        parsed = self.parse_intent(request.message)

        # Ambiguity check: return early with clarification prompt
        if parsed.is_ambiguous and parsed.clarification_needed:
            return AdvisorRecommendResponse(
                parsed_intent=parsed,
                recommendations=[],
                explanation=parsed.clarification_prompt or "Please provide more details regarding your fragrance preferences or budget.",
                applied_avoid_terms=[],
                session_id=request.session_id or f"advisor-{uuid.uuid4().hex[:8]}",
                clarification_needed=True,
                clarification_prompt=parsed.clarification_prompt,
            )

        # Hierarchy Step 1: Profile Merge & Conflict Detection
        merged_avoid = set(parsed.excluded_characteristics)
        budget_limit = parsed.budget_max
        liked_families = list(parsed.preferred_families)
        liked_accords = list(parsed.preferred_accords)
        liked_notes = list(parsed.preferred_notes)
        conflict_detected = False
        conflict_details = None
        clarification_prompt = None

        if user_id and request.include_profile:
            profile = self.user_repo.get_profile(user_id)
            if profile:
                profile_avoids = [term.strip().lower() for term in (profile.avoid_terms or []) if term.strip()]
                # Check for explicit conflict: user query requested something in profile avoid terms
                query_requested_terms = (
                    [f.lower() for f in parsed.preferred_families]
                    + [a.lower() for a in parsed.preferred_accords]
                    + [n.lower() for n in parsed.preferred_notes]
                )
                conflicted_terms = [t for t in query_requested_terms if t in profile_avoids]

                if conflicted_terms:
                    conflict_term = conflicted_terms[0]
                    conflict_detected = True
                    conflict_details = f"Your profile has '{conflict_term}' in your avoid list, but your query requested it."
                    clarification_prompt = (
                        f"Your profile has '{conflict_term}' in your avoid list. Would you like to: "
                        f"(a) Keep the exclusion and find non-{conflict_term} fragrances, "
                        f"(b) Temporarily allow {conflict_term} for this search only, or "
                        f"(c) Remove {conflict_term} from your profile permanently?"
                    )
                    # Constraint Precedence: Hard profile exclusion MUST NEVER be relaxed without explicit confirmation
                    merged_avoid.add(conflict_term)
                    # Remove from requested preferred items
                    liked_notes = [n for n in liked_notes if n.lower() != conflict_term]
                    liked_accords = [a for a in liked_accords if a.lower() != conflict_term]
                    liked_families = [f for f in liked_families if f.lower() != conflict_term]

                # Merge rest of profile avoid terms (hard exclusion)
                merged_avoid.update(profile_avoids)

                if not budget_limit and profile.budget_max:
                    budget_limit = profile.budget_max
                elif budget_limit and profile.budget_max:
                    # Enforce the stricter budget constraint
                    budget_limit = min(budget_limit, profile.budget_max)

                if not liked_families and profile.preferred_families:
                    liked_families.extend(profile.preferred_families)
                if not liked_accords and profile.preferred_accords:
                    liked_accords.extend(profile.preferred_accords)
                if not liked_notes and profile.preferred_notes:
                    liked_notes.extend(profile.preferred_notes)

        # Hierarchy Step 2: Call deterministic recommendation engine
        rec_constraints = RecommendationConstraints(
            budget_max_inr=budget_limit,
            hard_budget_limit=True if budget_limit else False,
            liked_families=liked_families,
            liked_accords=liked_accords,
            liked_notes=liked_notes,
            avoid_terms=list(merged_avoid),
            occasions=parsed.occasions,
            concentration=parsed.concentration or [],
        )

        rec_req = RecommendationRequest(
            session_id=request.session_id or f"advisor-{uuid.uuid4().hex[:8]}",
            constraints=rec_constraints,
            limit=request.limit,
        )

        rec_response = self.recommendation_service.recommend(rec_req, user_id=user_id)
        results = rec_response.results

        # Alternative Graph Boosting: if alternative query for known reference
        if parsed.is_alternative_search and parsed.reference_fragrances:
            results = self._prioritize_alternatives(parsed.reference_fragrances[0], results)

        # Generate grounded explanation
        explanation = self._generate_grounded_explanation(
            parsed=parsed,
            applied_avoid=list(merged_avoid),
            budget=budget_limit,
            results=results,
            conflict_details=conflict_details,
        )

        return AdvisorRecommendResponse(
            parsed_intent=parsed,
            recommendations=results,
            explanation=explanation,
            applied_avoid_terms=list(merged_avoid),
            session_id=rec_req.session_id,
            clarification_needed=conflict_detected,
            clarification_prompt=clarification_prompt,
            conflict_detected=conflict_detected,
            conflict_details=conflict_details,
        )

    def _prioritize_alternatives(
        self, ref_name: str, cards: List[RecommendationCard]
    ) -> List[RecommendationCard]:
        """Boosts candidate cards that have verified alternative relationship to reference fragrance."""
        stmt = (
            select(AlternativeRelationship.candidate_fragrance_id)
            .join(AlternativeRelationship.source_fragrance)
            .where(
                Fragrance.canonical_name.ilike(f"%{ref_name}%"),
                AlternativeRelationship.status == CurationStatus.PUBLISHED,
            )
        )
        alt_candidate_ids = set(self.db.execute(stmt).scalars().all())
        if not alt_candidate_ids:
            return cards

        # Prioritize matching candidates to top while preserving score order
        boosted = []
        others = []
        for card in cards:
            if card.fragrance_id in alt_candidate_ids:
                card.profile_match_cues.insert(0, f"Verified alternative to {ref_name}")
                boosted.append(card)
            else:
                others.append(card)
        return boosted + others

    def _generate_grounded_explanation(
        self,
        parsed: ParsedAdvisorIntent,
        applied_avoid: List[str],
        budget: Optional[float],
        results: List[RecommendationCard],
        conflict_details: Optional[str] = None,
    ) -> str:
        """Generates an honest, grounded narrative strictly reflecting catalogue matches."""
        parts = []

        if conflict_details:
            parts.append(f"Notice: {conflict_details} In accordance with your profile settings, we preserved this exclusion.")

        if not results:
            crit = []
            if budget:
                crit.append(f"budget ceiling of ₹{budget:,.0f}")
            if applied_avoid:
                crit.append(f"exclusions on ({', '.join(applied_avoid[:3])})")
            crit_str = " and ".join(crit) if crit else "your specific constraints"
            return (
                f"We could not find published fragrances in our catalogue meeting {crit_str}. "
                "Try relaxing budget constraints or specific note exclusions."
            )

        top = results[0]
        price_text = f" priced at approximately ₹{top.indicative_price_inr:,.0f}" if top.indicative_price_inr else ""
        cues_text = "; ".join(top.profile_match_cues[:2])

        if parsed.is_alternative_search and parsed.reference_fragrances:
            ref = parsed.reference_fragrances[0]
            parts.append(
                f"For an alternative to {ref}, our top recommendation is {top.canonical_name} by {top.brand_name}{price_text}. "
                f"It matches your criteria ({cues_text})."
            )
        else:
            parts.append(
                f"Based on your request, our top recommendation is {top.canonical_name} by {top.brand_name}{price_text}. "
                f"It aligns with your criteria ({cues_text})."
            )

        if applied_avoid:
            parts.append(f"We strictly filtered out all fragrances containing {', '.join(applied_avoid[:3])}.")

        if budget:
            parts.append(f"All ranked options conform to your budget constraint of ₹{budget:,.0f}.")

        if top.sample_first_recommended:
            parts.append("Because scent chemistry varies by individual skin, sampling first is recommended before a full bottle.")

        return " ".join(parts)
