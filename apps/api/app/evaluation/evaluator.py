"""SCENTIQ Automated Recommendation Evaluation Harness.
Part of Milestone 3 Part 3.3.
Runs the 10 benchmark scenarios across:
1. Baseline (Unpersonalised, query constraints only)
2. Profile-Personalised (User profile integrated)
3. Profile + Feedback Learning (Profile + Feedback history integrated)
Computes Precision@5, NDCG@5, Recall@10, Exclusion Violation Rate, Budget Violation Rate, and Diversity.
"""
from dataclasses import dataclass, field
import uuid
from typing import Dict, List, Optional, Set
from sqlalchemy.orm import Session

from app.models.enums import CurationStatus
from app.models.fragrance import Fragrance
from app.models.taxonomy import FragranceNote, FragranceAccord
from app.models.price import PriceListing
from app.schemas.recommendation import RecommendationRequest, RecommendationCard
from app.schemas.user import OnboardingRequest, UserFeedbackCreate
from app.services.recommendation_service import RecommendationService
from app.services.user_service import UserService
from app.evaluation.dataset import EVALUATION_SCENARIOS, EvaluationScenario
from app.evaluation.metrics import (
    precision_at_k,
    ndcg_at_k,
    recall_at_k,
    hard_exclusion_violation_rate,
    budget_violation_rate,
    intra_list_diversity,
    catalogue_coverage,
)


@dataclass
class ScenarioMetrics:
    scenario_id: str
    scenario_name: str
    mode: str  # baseline, profile, profile_feedback
    precision_at_5: float
    ndcg_at_5: float
    recall_at_10: float
    hard_exclusion_violation_rate: float
    budget_violation_rate: float
    diversity: float
    top_recommendations: List[str]


@dataclass
class EvaluationReport:
    total_scenarios: int
    published_catalogue_size: int
    baseline_avg_precision_5: float
    baseline_avg_ndcg_5: float
    baseline_avg_recall_10: float
    profile_avg_precision_5: float
    profile_avg_ndcg_5: float
    profile_avg_recall_10: float
    feedback_avg_precision_5: float
    feedback_avg_ndcg_5: float
    feedback_avg_recall_10: float
    hard_exclusion_violations_total: int
    budget_violations_total: int
    catalogue_coverage_rate: float
    scenario_results: List[ScenarioMetrics] = field(default_factory=list)


class RecommendationEvaluator:
    def __init__(self, db: Session):
        self.db = db
        self.rec_service = RecommendationService(db)
        self.user_service = UserService(db)
        self._build_catalogue_index()

    def _build_catalogue_index(self):
        """Indexes catalogue fragrances for fast metadata lookup."""
        self.fragrance_by_slug: Dict[str, Fragrance] = {}
        self.fragrance_by_id: Dict[uuid.UUID, Fragrance] = {}
        self.fragrance_metadata: Dict[str, Dict] = {}
        self.published_ids: Set[str] = set()

        frags = self.db.query(Fragrance).filter(Fragrance.status == CurationStatus.PUBLISHED).all()
        for f in frags:
            self.fragrance_by_slug[f.slug] = f
            self.fragrance_by_id[f.id] = f
            self.published_ids.add(str(f.id))

            notes = set()
            for fn in f.notes:
                if fn.note:
                    notes.add(fn.note.canonical_name.lower())

            accords = set()
            for fa in f.accords:
                if fa.accord:
                    accords.add(fa.accord.canonical_name.lower())

            self.fragrance_metadata[f.canonical_name.lower()] = {
                "slug": f.slug,
                "notes": notes,
                "accords": accords,
                "family": f.family or "",
            }

    def evaluate_scenario(
        self, scenario: EvaluationScenario, mode: str
    ) -> ScenarioMetrics:
        user_id = None
        if mode in ("profile", "profile_feedback"):
            user_id = uuid.uuid4()
            p = scenario.persona
            onboarding = OnboardingRequest(
                familiarity_level=p.familiarity_level,
                preferred_families=p.preferred_families,
                liked_notes=p.liked_notes,
                liked_accords=p.liked_accords,
                avoid_terms=p.avoid_terms,
                budget_max=p.budget_max,
                occasions=p.occasions,
            )
            self.user_service.process_onboarding(user_id, onboarding)

            if mode == "profile_feedback" and scenario.feedback_history:
                for fb in scenario.feedback_history:
                    frag = self.fragrance_by_slug.get(fb.fragrance_slug)
                    if frag:
                        self.user_service.record_feedback(
                            user_id=user_id,
                            data=UserFeedbackCreate(
                                fragrance_id=frag.id,
                                feedback_type=fb.feedback_type,
                                rating=fb.rating,
                            ),
                        )

        req = RecommendationRequest(
            session_id=f"eval-{scenario.id}-{mode}",
            constraints=scenario.query_constraints,
            limit=10,
        )
        resp = self.rec_service.recommend(req, user_id=user_id)
        cards = resp.results

        # Map fragrance cards to slugs
        card_slugs = []
        for c in cards:
            frag = self.fragrance_by_id.get(c.fragrance_id)
            if frag:
                card_slugs.append(frag.slug)
            else:
                card_slugs.append(c.canonical_name.lower().replace(" ", "-"))

        p5 = precision_at_k(card_slugs, scenario.ground_truth_relevance, k=5)
        ndcg5 = ndcg_at_k(card_slugs, scenario.ground_truth_relevance, k=5)
        r10 = recall_at_k(card_slugs, scenario.ground_truth_relevance, k=10)

        # Hard exclusions & budget checks
        all_avoids = list(scenario.query_constraints.avoid_terms)
        if mode != "baseline" and scenario.persona.avoid_terms:
            all_avoids.extend(scenario.persona.avoid_terms)

        excl_viol = hard_exclusion_violation_rate(cards, all_avoids, self.fragrance_metadata)

        budget_limit = scenario.query_constraints.budget_max_inr
        if mode != "baseline" and scenario.persona.budget_max:
            budget_limit = min(budget_limit or float("inf"), scenario.persona.budget_max)

        budg_viol = budget_violation_rate(
            cards,
            budget_limit,
            hard_budget=scenario.query_constraints.hard_budget_limit,
        )

        div = intra_list_diversity(cards)

        return ScenarioMetrics(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            mode=mode,
            precision_at_5=p5,
            ndcg_at_5=ndcg5,
            recall_at_10=r10,
            hard_exclusion_violation_rate=excl_viol,
            budget_violation_rate=budg_viol,
            diversity=div,
            top_recommendations=card_slugs[:5],
        )

    def run_full_evaluation(self) -> EvaluationReport:
        all_results: List[ScenarioMetrics] = []
        all_recommended_ids: Set[str] = set()

        baseline_p5, baseline_ndcg5, baseline_r10 = [], [], []
        profile_p5, profile_ndcg5, profile_r10 = [], [], []
        feedback_p5, feedback_ndcg5, feedback_r10 = [], [], []

        total_excl_violations = 0
        total_budget_violations = 0

        for sc in EVALUATION_SCENARIOS:
            # Baseline
            m_base = self.evaluate_scenario(sc, "baseline")
            all_results.append(m_base)
            baseline_p5.append(m_base.precision_at_5)
            baseline_ndcg5.append(m_base.ndcg_at_5)
            baseline_r10.append(m_base.recall_at_10)
            if m_base.hard_exclusion_violation_rate > 0.0:
                total_excl_violations += 1
            if m_base.budget_violation_rate > 0.0:
                total_budget_violations += 1

            # Profile
            m_prof = self.evaluate_scenario(sc, "profile")
            all_results.append(m_prof)
            profile_p5.append(m_prof.precision_at_5)
            profile_ndcg5.append(m_prof.ndcg_at_5)
            profile_r10.append(m_prof.recall_at_10)
            if m_prof.hard_exclusion_violation_rate > 0.0:
                total_excl_violations += 1
            if m_prof.budget_violation_rate > 0.0:
                total_budget_violations += 1

            # Profile + Feedback
            m_feed = self.evaluate_scenario(sc, "profile_feedback")
            all_results.append(m_feed)
            feedback_p5.append(m_feed.precision_at_5)
            feedback_ndcg5.append(m_feed.ndcg_at_5)
            feedback_r10.append(m_feed.recall_at_10)
            if m_feed.hard_exclusion_violation_rate > 0.0:
                total_excl_violations += 1
            if m_feed.budget_violation_rate > 0.0:
                total_budget_violations += 1

            for slug in m_prof.top_recommendations:
                frag = self.fragrance_by_slug.get(slug)
                if frag:
                    all_recommended_ids.add(str(frag.id))

        coverage = catalogue_coverage(all_recommended_ids, self.published_ids)

        def avg(lst: List[float]) -> float:
            return round(sum(lst) / float(len(lst)), 4) if lst else 0.0

        return EvaluationReport(
            total_scenarios=len(EVALUATION_SCENARIOS),
            published_catalogue_size=len(self.published_ids),
            baseline_avg_precision_5=avg(baseline_p5),
            baseline_avg_ndcg_5=avg(baseline_ndcg5),
            baseline_avg_recall_10=avg(baseline_r10),
            profile_avg_precision_5=avg(profile_p5),
            profile_avg_ndcg_5=avg(profile_ndcg5),
            profile_avg_recall_10=avg(profile_r10),
            feedback_avg_precision_5=avg(feedback_p5),
            feedback_avg_ndcg_5=avg(feedback_ndcg5),
            feedback_avg_recall_10=avg(feedback_r10),
            hard_exclusion_violations_total=total_excl_violations,
            budget_violations_total=total_budget_violations,
            catalogue_coverage_rate=coverage,
            scenario_results=all_results,
        )

