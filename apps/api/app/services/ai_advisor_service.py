"""SCENTIQ AI Fragrance Advisor Service (EPIC-11).
Translates natural language into validated recommendation constraints.
Grounds all recommendations in the deterministic ranking engine.
Includes robust rule-based intent parsing fallback when LLM is unavailable.
"""
import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import UserProfile
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
    "musky", "amber", "spicy", "floral", "gourmand", "leather", "oud"
]

KNOWN_ACCORDS = [
    "fresh", "woody", "citrus", "aquatic", "aromatic", "spicy",
    "sweet", "amber", "musky", "floral", "warm spicy", "powdery", "leather"
]

KNOWN_NOTES = [
    "bergamot", "cedarwood", "vanilla", "sandalwood", "vetiver",
    "rose", "lavender", "cardamom", "patchouli", "neroli", "lemon",
    "grapefruit", "apple", "pink pepper", "tonka bean", "cinnamon"
]

OCCASIONS_MAP = {
    "office": ["office", "work", "professional", "desk", "corporate"],
    "party": ["party", "club", "clubbing", "night out"],
    "date": ["date", "romantic", "intimate", "evening"],
    "casual": ["casual", "daily", "everyday", "errands"],
    "summer": ["summer", "hot", "tropical", "beach", "humid"],
    "winter": ["winter", "cold", "autumn", "fall"],
    "gym": ["gym", "workout", "sport", "athletic"],
}


class AIAdvisorService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.recommendation_service = RecommendationService(db)

    def parse_intent(self, message: str) -> ParsedAdvisorIntent:
        """Parses user message into structured constraints."""
        clean_msg = message.strip()
        if not clean_msg:
            return ParsedAdvisorIntent(parsed_via="empty_fallback")

        # 1. Attempt LLM extraction if API key is present
        api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        if api_key:
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
  "concentration": string[]
}}

User query: "{message}"

Return ONLY valid JSON.
"""
            response = model.generate_content(prompt)
            text = response.text.strip()
            # Clean possible markdown wrapping
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
                confidence_score=0.95,
                parsed_via="gemini_llm",
            )
        except Exception as err:
            logger.debug(f"Gemini API parse attempt failed: {err}")
            return None

    def _parse_rule_based(self, message: str) -> ParsedAdvisorIntent:
        """Deterministic NLP intent extraction."""
        lower_msg = message.lower()

        # 1. Budget extraction (INR)
        # Matches "₹2,500", "2500 inr", "budget 3000", "under 4000", "rs 1500"
        budget_max = None
        budget_patterns = [
            r"(?:budget|under|below|max|around|within|up\s+to|price)?\s*(?:₹|rs\.?|inr)?\s*([0-9]+(?:,[0-9]{3})*|\b[0-9]{3,6}\b)\s*(?:₹|rs\.?|inr|rupees)?",
        ]
        for pat in budget_patterns:
            matches = re.finditer(pat, lower_msg)
            for m in matches:
                val_str = m.group(1).replace(",", "")
                try:
                    val = float(val_str)
                    # Plausible fragrance price between 200 and 500000 INR
                    if 200 <= val <= 500000:
                        budget_max = val
                        break
                except ValueError:
                    continue
            if budget_max:
                break

        # 2. Exclusions (avoid / dislike)
        excluded = []
        avoid_patterns = [
            r"(?:don'?t\s+like|dont\s+like|dislike|avoid|no|not\s+too|not\s+overly|hate|without)\s+([a-zA-Z\s]+?)(?=[,.]|\band\b|\bbut\b|\bfor\b|\bunder\b|\bmy\b|$)",
        ]
        for pat in avoid_patterns:
            for match in re.finditer(pat, lower_msg):
                raw = match.group(1).strip()
                # Split words like "sweet", "overly sweet", "vanilla"
                for word in raw.split():
                    clean_w = word.strip(" ,.")
                    if clean_w in KNOWN_NOTES or clean_w in KNOWN_ACCORDS or clean_w in ("sweet", "heavy", "synthetic"):
                        excluded.append(clean_w)
                if raw and raw not in excluded:
                    excluded.append(raw)

        # 3. Preferred families & accords
        preferred_families = []
        preferred_accords = []
        preferred_notes = []

        # Remove the excluded clause from consideration for preferred items
        searchable_text = lower_msg
        for exc in excluded:
            searchable_text = searchable_text.replace(exc, "")

        for fam in KNOWN_FAMILIES:
            if re.search(r"\b" + re.escape(fam) + r"\b", searchable_text):
                preferred_families.append(fam)

        for acc in KNOWN_ACCORDS:
            if re.search(r"\b" + re.escape(acc) + r"\b", searchable_text):
                preferred_accords.append(acc)

        for note in KNOWN_NOTES:
            if re.search(r"\b" + re.escape(note) + r"\b", searchable_text):
                preferred_notes.append(note)

        # 4. Occasions
        occasions = []
        for occ_key, keywords in OCCASIONS_MAP.items():
            if any(re.search(r"\b" + re.escape(kw) + r"\b", lower_msg) for kw in keywords):
                occasions.append(occ_key)

        # 5. Concentration
        concentrations = []
        if "edp" in lower_msg or "eau de parfum" in lower_msg:
            concentrations.append("EDP")
        if "edt" in lower_msg or "eau de toilette" in lower_msg:
            concentrations.append("EDT")
        if "parfum" in lower_msg or "extrait" in lower_msg:
            concentrations.append("Parfum")

        return ParsedAdvisorIntent(
            budget_max=budget_max,
            currency="INR",
            preferred_families=list(set(preferred_families)),
            preferred_accords=list(set(preferred_accords)),
            preferred_notes=list(set(preferred_notes)),
            excluded_characteristics=list(set(excluded)),
            occasions=list(set(occasions)),
            concentration=concentrations,
            confidence_score=0.90,
            parsed_via="rule_based_fallback",
        )

    def recommend_with_advisor(
        self,
        request: AdvisorRecommendRequest,
        user_id: Optional[uuid.UUID] = None,
    ) -> AdvisorRecommendResponse:
        """End-to-end bounded advisor pipeline:
        Intent Extraction -> Validation -> Profile Merge -> Deterministic Engine -> Grounded Explanation
        """
        # Step 1: Extract intent
        parsed = self.parse_intent(request.message)

        # Step 2: Merge with stored user profile (hard avoid exclusions cannot be bypassed)
        merged_avoid = set(parsed.excluded_characteristics)
        budget_limit = parsed.budget_max
        liked_families = list(parsed.preferred_families)
        liked_accords = list(parsed.preferred_accords)
        liked_notes = list(parsed.preferred_notes)

        if user_id and request.include_profile:
            profile = self.user_repo.get_profile(user_id)
            if profile:
                if profile.avoid_terms:
                    merged_avoid.update(profile.avoid_terms)
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

        # Step 3: Call deterministic recommendation engine
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

        # Step 4: Generate grounded, evidence-backed narrative explanation
        explanation = self._generate_grounded_explanation(
            parsed=parsed,
            applied_avoid=list(merged_avoid),
            budget=budget_limit,
            results=rec_response.results,
        )

        return AdvisorRecommendResponse(
            parsed_intent=parsed,
            recommendations=rec_response.results,
            explanation=explanation,
            applied_avoid_terms=list(merged_avoid),
            session_id=rec_req.session_id,
        )

    def _generate_grounded_explanation(
        self,
        parsed: ParsedAdvisorIntent,
        applied_avoid: List[str],
        budget: Optional[float],
        results: List[RecommendationCard],
    ) -> str:
        """Generates an honest, transparent rationale strictly grounded in returned catalogue results."""
        if not results:
            crit = []
            if budget:
                crit.append(f"budget ceiling of ₹{budget:,.0f}")
            if applied_avoid:
                crit.append(f"exclusions on ({', '.join(applied_avoid)})")
            crit_str = " and ".join(crit) if crit else "your specific constraints"
            return (
                f"We could not find published fragrances in our catalogue meeting {crit_str}. "
                "Try relaxing budget constraints or specific note exclusions."
            )

        top = results[0]
        price_text = f" priced at approximately ₹{top.indicative_price_inr:,.0f}" if top.indicative_price_inr else ""
        cues_text = "; ".join(top.profile_match_cues[:2])

        explanation = (
            f"Based on your request, our top recommendation is {top.canonical_name} by {top.brand_name}{price_text}. "
            f"It aligns with your criteria ({cues_text}). "
        )

        if applied_avoid:
            explanation += f"We strictly filtered out all fragrances containing {', '.join(applied_avoid[:3])}. "

        if budget:
            explanation += f"All ranked options conform to your budget constraint of ₹{budget:,.0f}. "

        if top.sample_first_recommended:
            explanation += "Because scent chemistry varies by individual skin, sampling first is recommended before a full bottle."

        return explanation
