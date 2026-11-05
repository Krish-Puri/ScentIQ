"""SCENTIQ Information Retrieval & Recommendation Evaluation Metrics.
Part of Milestone 3 Part 3.1.
Implements:
- Precision@5
- NDCG@5 (Normalized Discounted Cumulative Gain)
- Recall@10
- Hard Exclusion Violation Rate (Target: 0.0%)
- Hard Budget Ceiling Violation Rate (Target: 0.0%)
- Intra-List Diversity (Family & Brand Diversity)
- Catalogue Coverage Rate
"""
import math
from typing import Dict, List, Optional, Set
from app.schemas.recommendation import RecommendationCard


def precision_at_k(
    recommended_slugs: List[str],
    ground_truth_relevance: Dict[str, float],
    k: int = 5,
    min_relevance: float = 1.0,
) -> float:
    """Computes Precision@K: fraction of top K recommendations that are relevant."""
    if not recommended_slugs:
        return 0.0
    top_k = recommended_slugs[:k]
    relevant_count = sum(
        1 for slug in top_k if ground_truth_relevance.get(slug, 0.0) >= min_relevance
    )
    return round(relevant_count / float(len(top_k)), 4)


def dcg_at_k(
    recommended_slugs: List[str],
    ground_truth_relevance: Dict[str, float],
    k: int = 5,
) -> float:
    """Computes Discounted Cumulative Gain at rank K using standard exponential gain."""
    top_k = recommended_slugs[:k]
    dcg = 0.0
    for idx, slug in enumerate(top_k):
        rel = ground_truth_relevance.get(slug, 0.0)
        # 1-indexed rank: rank = idx + 1
        # Discount factor: log2(rank + 1)
        dcg += (2.0 ** rel - 1.0) / math.log2(idx + 2.0)
    return dcg


def ndcg_at_k(
    recommended_slugs: List[str],
    ground_truth_relevance: Dict[str, float],
    k: int = 5,
) -> float:
    """Computes Normalized Discounted Cumulative Gain (NDCG@K)."""
    actual_dcg = dcg_at_k(recommended_slugs, ground_truth_relevance, k=k)

    # Ideal ranking of available relevance scores
    ideal_scores = sorted(ground_truth_relevance.values(), reverse=True)
    ideal_dcg = 0.0
    for idx, rel in enumerate(ideal_scores[:k]):
        ideal_dcg += (2.0 ** rel - 1.0) / math.log2(idx + 2.0)

    if ideal_dcg == 0.0:
        return 1.0 if actual_dcg == 0.0 else 0.0
    return round(actual_dcg / ideal_dcg, 4)


def recall_at_k(
    recommended_slugs: List[str],
    ground_truth_relevance: Dict[str, float],
    k: int = 10,
    min_relevance: float = 1.0,
) -> float:
    """Computes Recall@K: fraction of all relevant catalogue items retrieved in top K."""
    total_relevant = sum(1 for rel in ground_truth_relevance.values() if rel >= min_relevance)
    if total_relevant == 0:
        return 1.0
    top_k = recommended_slugs[:k]
    hits = sum(1 for slug in top_k if ground_truth_relevance.get(slug, 0.0) >= min_relevance)
    return round(hits / float(total_relevant), 4)


def hard_exclusion_violation_rate(
    recommendations: List[RecommendationCard],
    avoid_terms: List[str],
    fragrance_metadata: Dict[str, Dict],  # slug -> {notes: set, accords: set, family: str}
) -> float:
    """Computes hard exclusion violation rate: MUST BE 0.0%."""
    if not recommendations or not avoid_terms:
        return 0.0

    normalized_avoids = [term.strip().lower() for term in avoid_terms if term.strip()]
    if not normalized_avoids:
        return 0.0

    violations = 0
    for card in recommendations:
        meta = fragrance_metadata.get(card.canonical_name.lower(), {})
        notes = meta.get("notes", set())
        accords = meta.get("accords", set())
        family = meta.get("family", "").lower()

        frag_all_terms = notes | accords
        if family:
            frag_all_terms.add(family)

        has_violation = any(
            avoid in term for avoid in normalized_avoids for term in frag_all_terms
        )
        if has_violation:
            violations += 1

    return round(violations / float(len(recommendations)), 4)


def budget_violation_rate(
    recommendations: List[RecommendationCard],
    budget_ceiling: Optional[float],
    hard_budget: bool = True,
) -> float:
    """Computes budget violation rate: MUST BE 0.0% when hard_budget is True."""
    if not recommendations or not budget_ceiling or not hard_budget:
        return 0.0

    violations = 0
    for card in recommendations:
        if card.indicative_price_inr and card.indicative_price_inr > budget_ceiling:
            violations += 1

    return round(violations / float(len(recommendations)), 4)


def intra_list_diversity(recommendations: List[RecommendationCard]) -> float:
    """Computes intra-list diversity based on brand and family differentiation.
    Score in [0.0, 1.0] where 1.0 means high diversity (no repeated brands/families).
    """
    if len(recommendations) <= 1:
        return 1.0

    pairs = 0
    diff_count = 0
    for i in range(len(recommendations)):
        for j in range(i + 1, len(recommendations)):
            pairs += 1
            card_a = recommendations[i]
            card_b = recommendations[j]
            brand_diff = 1.0 if card_a.brand_name != card_b.brand_name else 0.0
            family_diff = 1.0 if (card_a.family or "").lower() != (card_b.family or "").lower() else 0.0
            diff_count += (brand_diff * 0.5) + (family_diff * 0.5)

    return round(diff_count / float(pairs), 4)


def catalogue_coverage(
    all_recommended_ids: Set[str],
    total_published_ids: Set[str],
) -> float:
    """Computes catalogue coverage: fraction of catalogue reachable across queries."""
    if not total_published_ids:
        return 0.0
    covered = all_recommended_ids & total_published_ids
    return round(len(covered) / float(len(total_published_ids)), 4)

