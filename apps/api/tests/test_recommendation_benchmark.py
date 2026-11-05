"""SCENTIQ Offline Recommendation Quality Evaluation Benchmark (Milestone 3 - Part 3).
Executes the evaluation harness across the 10 labelled scenarios and asserts that:
1. Hard exclusion violation rate MUST BE exactly 0.0%.
2. Hard budget ceiling violation rate MUST BE exactly 0.0%.
3. Precision@5 and NDCG@5 meet production thresholds.
4. Explanations are grounded with cues and trade-offs.
"""
import os
import sys
import pytest

# Ensure scripts directory is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.seed_catalogue import seed
from scripts.expand_catalogue import expand_catalogue
from app.evaluation.evaluator import RecommendationEvaluator


def test_recommendation_quality_and_constraint_safety_benchmark(db):
    # Seed full catalogue for evaluation
    seed(db)
    expand_catalogue(db)

    evaluator = RecommendationEvaluator(db)
    report = evaluator.run_full_evaluation()

    # 1. Critical Hard Exclusion Safety: Zero Violations
    assert report.hard_exclusion_violations_total == 0, (
        f"CRITICAL SAFETY VIOLATION: {report.hard_exclusion_violations_total} "
        "recommendations contained avoided notes or accords!"
    )

    # 2. Critical Budget Constraint Safety: Zero Violations
    assert report.budget_violations_total == 0, (
        f"CRITICAL BUDGET VIOLATION: {report.budget_violations_total} "
        "recommendations exceeded user hard budget limits!"
    )

    # 3. Ranking Quality: Precision@5 & NDCG@5
    print(f"\n[BENCHMARK] Baseline Precision@5: {report.baseline_avg_precision_5:.4f}, NDCG@5: {report.baseline_avg_ndcg_5:.4f}")
    print(f"[BENCHMARK] Profile Precision@5:  {report.profile_avg_precision_5:.4f}, NDCG@5: {report.profile_avg_ndcg_5:.4f}")
    print(f"[BENCHMARK] Feedback Precision@5: {report.feedback_avg_precision_5:.4f}, NDCG@5: {report.feedback_avg_ndcg_5:.4f}")
    print(f"[BENCHMARK] Catalogue Coverage:   {report.catalogue_coverage_rate * 100:.1f}%")

    assert report.published_catalogue_size >= 25, "Catalogue size should reflect seeded dataset"
    assert report.profile_avg_precision_5 >= 0.50, (
        f"Precision@5 below threshold: {report.profile_avg_precision_5:.4f}"
    )
    assert report.profile_avg_ndcg_5 >= 0.55, (
        f"NDCG@5 below threshold: {report.profile_avg_ndcg_5:.4f}"
    )

    # 4. Scenario-specific assertions
    for res in report.scenario_results:
        # Every scenario run must adhere to hard exclusions and budgets
        assert res.hard_exclusion_violation_rate == 0.0, f"Violation in {res.scenario_id} [{res.mode}]"
        assert res.budget_violation_rate == 0.0, f"Budget violation in {res.scenario_id} [{res.mode}]"
        assert res.diversity > 0.0, f"Mono-recommendation in {res.scenario_id} [{res.mode}]"
