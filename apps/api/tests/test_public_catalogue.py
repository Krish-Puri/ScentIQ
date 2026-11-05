"""Tests for Public Catalogue Endpoints (EPIC-05 / FR-004, FR-006).
"""
import pytest
from app.models.enums import CurationStatus
from app.models.fragrance import Fragrance


def test_list_published_fragrances(client, seed_test_data):
    response = client.get("/api/v1/fragrances")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 2
    assert data["meta"]["total"] >= 2
    slugs = [f["slug"] for f in data["data"]]
    assert seed_test_data["frag_ref"].slug in slugs


def test_draft_fragrance_hidden_from_public_list(client, db, seed_test_data):
    brand_id = seed_test_data["brand1"].id
    draft = Fragrance(
        brand_id=brand_id,
        canonical_name="Secret Unreleased",
        slug="secret-unreleased-edp",
        concentration="EDP",
        status=CurationStatus.DRAFT,
    )
    db.add(draft)
    db.commit()

    # Public list should NOT include draft
    response = client.get("/api/v1/fragrances")
    slugs = [f["slug"] for f in response.json()["data"]]
    assert "secret-unreleased-edp" not in slugs

    # Direct slug detail request should return 404
    detail_res = client.get("/api/v1/fragrances/secret-unreleased-edp")
    assert detail_res.status_code == 404


def test_fragrance_detail_by_slug(client, seed_test_data):
    ref_slug = seed_test_data["frag_ref"].slug
    response = client.get(f"/api/v1/fragrances/{ref_slug}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["canonical_name"] == "Reference Eau"
    assert data["brand"]["canonical_name"] == "Luxury House"
    assert "Bergamot" in data["top_notes"]
    assert "Cedarwood" in data["base_notes"]
    assert "Citrus" in data["accords"]
    assert len(data["prices"]) == 1
    assert data["prices"][0]["price_inr"] == 12000.0
    assert data["evidence_count"] >= 1

