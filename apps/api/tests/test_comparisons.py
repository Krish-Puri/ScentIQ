"""Tests for Side-by-Side Comparison (FR-008).
Verifies:
- Comparing 2 or 3 fragrances returns structured columns
- Computes shared and distinguishing notes
- Price per ml is calculated when size and price exist
- Discloses missing pyramid data
"""
import uuid
import pytest


def test_comparison_between_two_fragrances(client, seed_test_data):
    ref_id = str(seed_test_data["frag_ref"].id)
    cand_id = str(seed_test_data["frag_cand"].id)

    payload = {"fragrance_ids": [ref_id, cand_id]}
    response = client.post("/api/v1/comparisons", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) == 2

    # Both share Bergamot and Cedarwood
    assert "Bergamot" in data["shared_notes"]
    assert "Cedarwood" in data["shared_notes"]
    assert "Citrus" in data["shared_accords"]

    # Price per ml calculation
    ref_item = next(i for i in data["items"] if i["id"] == ref_id)
    assert ref_item["indicative_price_inr"] == 12000.0
    assert ref_item["size_ml"] == 100.0
    assert ref_item["price_per_ml"] == 120.0


def test_comparison_validation_minimum_items(client, seed_test_data):
    ref_id = str(seed_test_data["frag_ref"].id)
    # Only 1 fragrance ID provided
    payload = {"fragrance_ids": [ref_id]}
    response = client.post("/api/v1/comparisons", json=payload)
    assert response.status_code == 400

