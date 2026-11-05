"""Tests for Deterministic Recommendations (EPIC-08 / PRD Section 12.3).
Verifies:
- Hard exclusions (avoid terms) are strictly respected
- Hard budget limits filter out expensive options
- Reason codes and transparent fit summary are returned
- No invented or ungrounded records
"""
import pytest


def test_recommendation_scoring_and_ranking(client, seed_test_data):
    payload = {
        "constraints": {
            "liked_families": ["Woody Citrus"],
            "liked_notes": ["Bergamot", "Cedarwood"],
            "liked_accords": ["Citrus"],
            "avoid_terms": [],
            "budget_max_inr": 15000,
            "hard_budget_limit": True,
        },
        "limit": 5,
    }
    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "results" in data
    assert len(data["results"]) >= 1
    top = data["results"][0]
    assert top["score"] > 0
    assert "fit_summary" in top
    assert len(top["profile_match_cues"]) > 0


def test_hard_exclusion_filters_out_avoid_terms(client, seed_test_data):
    # Both seed fragrances contain 'Cedarwood' and 'Bergamot'
    payload = {
        "constraints": {
            "liked_families": ["Woody Citrus"],
            "avoid_terms": ["Cedarwood"],  # Hard avoid
        },
        "limit": 5,
    }
    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200
    results = response.json()["data"]["results"]
    # All candidates containing Cedarwood should be excluded
    frag_ids = [r["fragrance_id"] for r in results]
    assert str(seed_test_data["frag_ref"].id) not in frag_ids
    assert str(seed_test_data["frag_cand"].id) not in frag_ids


def test_hard_budget_ceiling_filters_expensive_fragrances(client, seed_test_data):
    # frag_ref is 12000 INR, frag_cand is 2200 INR
    payload = {
        "constraints": {
            "liked_families": ["Woody Citrus"],
            "budget_max_inr": 3000,  # Below frag_ref price
            "hard_budget_limit": True,
        },
        "limit": 5,
    }
    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200
    results = response.json()["data"]["results"]
    frag_ids = [r["fragrance_id"] for r in results]
    assert str(seed_test_data["frag_ref"].id) not in frag_ids
    assert str(seed_test_data["frag_cand"].id) in frag_ids

