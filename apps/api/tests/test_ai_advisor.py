"""Tests for AI Fragrance Advisor (EPIC-11).
Verifies:
- Intent parsing from natural language queries
- Deterministic fallback when LLM is unavailable
- Schema validation
- Integration with user profile and hard exclusions
- Evidence-grounded explanations
"""
import uuid
import pytest


def test_ai_advisor_intent_parsing(client):
    query = "I want a fresh, slightly woody perfume for office use. My budget is ₹2,500. I don't like overly sweet fragrances."
    res = client.post("/api/v1/advisor/parse-intent", json={"message": query})
    assert res.status_code == 200
    data = res.json()["data"]

    # Budget extracted
    assert data["budget_max"] == 2500.0
    assert data["currency"] == "INR"

    # Accords and families
    accords = [a.lower() for a in data["preferred_accords"]]
    assert "fresh" in accords
    assert "woody" in accords

    # Exclusions
    assert any("sweet" in exc.lower() for exc in data["excluded_characteristics"])

    # Occasions
    assert "office" in data["occasions"]
    assert data["parsed_via"] in ("rule_based_fallback", "gemini_llm")


def test_ai_advisor_recommend_pipeline(client, seed_test_data):
    # Query within Alternative Eau's budget (₹2,200)
    query = "Looking for a citrus woody fragrance for work under ₹3,000"
    res = client.post("/api/v1/advisor/recommend", json={
        "message": query,
        "limit": 5,
    })
    assert res.status_code == 200
    data = res.json()["data"]

    parsed = data["parsed_intent"]
    assert parsed["budget_max"] == 3000.0

    # Recommendations should contain Alternative Eau (₹2,200) and exclude Reference Eau (₹12,000)
    recs = data["recommendations"]
    rec_names = [r["canonical_name"] for r in recs]
    assert "Alternative Eau" in rec_names
    assert "Reference Eau" not in rec_names

    # Grounded explanation
    assert "Alternative Eau" in data["explanation"]
    assert "3,000" in data["explanation"]


def test_ai_advisor_profile_integration_and_hard_exclusions(client, seed_test_data):
    # Register user with avoid term 'citrus'
    user = client.post("/api/v1/auth/register", json={"email": "advisortest@example.com", "password": "password123"}).json()["data"]
    headers = {"Authorization": f"Bearer {user['access_token']}"}

    client.put("/api/v1/users/me/profile", json={
        "avoid_terms": ["citrus"],
    }, headers=headers)

    # Both Reference Eau and Alternative Eau have Citrus accords in seed data
    query = "Find me a great woody perfume under ₹15,000"
    res = client.post("/api/v1/advisor/recommend", json={
        "message": query,
        "include_profile": True,
    }, headers=headers)

    assert res.status_code == 200
    data = res.json()["data"]
    # Profile avoid term 'citrus' was merged
    assert "citrus" in [a.lower() for a in data["applied_avoid_terms"]]
    # Since both seed fragrances have citrus, both should be filtered out by hard exclusion
    assert len(data["recommendations"]) == 0
    assert "could not find published fragrances" in data["explanation"]


def test_ai_advisor_fallback_on_empty_or_vague_message(client):
    res = client.post("/api/v1/advisor/parse-intent", json={"message": "recommend something"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert isinstance(data["preferred_accords"], list)
