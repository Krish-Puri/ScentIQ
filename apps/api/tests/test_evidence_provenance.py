"""Tests for Evidence & Provenance (EPIC-04).
Verifies:
- Evidence source rights and license capture
- Directional alternative relationships with A/B/C grades
- Prevention of self-referencing links
- Review approval gates before public visibility
- Unapproved links are hidden from public endpoint
"""
import uuid
import pytest
from app.models.enums import CurationStatus, EvidenceGrade, LicenseStatus, RelationshipType


def test_create_evidence_source(client):
    payload = {
        "title": "Scento CC BY 4.0 Verified Archive",
        "url": "https://huggingface.co/datasets/scento/perfume-database",
        "publisher": "Scento Open Research",
        "source_type": "OPEN_DATASET",
        "license_status": "CC_BY_4_0",
        "attribution_text": "Dataset licensed under Creative Commons Attribution 4.0 International",
    }
    response = client.post("/api/v1/admin/evidence-sources", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["license_status"] == LicenseStatus.CC_BY_4_0.value
    assert data["publisher"] == "Scento Open Research"


def test_propose_alternative_relationship(client, seed_test_data):
    source_id = str(seed_test_data["frag_ref"].id)
    cand_id = str(seed_test_data["frag_cand"].id)

    # Creating a new fragrance to link
    brand_id = str(seed_test_data["brand2"].id)
    new_frag = client.post("/api/v1/admin/fragrances", json={
        "brand_id": brand_id,
        "canonical_name": "Proposed Clone",
        "concentration": "EDP",
    }).json()["data"]

    payload = {
        "source_fragrance_id": source_id,
        "candidate_fragrance_id": new_frag["id"],
        "relationship_type": RelationshipType.COMMUNITY_REPORTED.value,
        "evidence_grade": EvidenceGrade.B_SUPPORTED.value,
        "rationale": "Community reports 85% drydown resemblance on skin.",
        "known_differences": "Proposed clone has sharper bergamot opening.",
    }
    response = client.post("/api/v1/admin/alternatives", json=payload)
    assert response.status_code == 200
    res = response.json()["data"]
    assert res["status"] == CurationStatus.DRAFT.value
    rel_id = res["id"]

    # Public endpoint should NOT include DRAFT alternative
    public_res = client.get(f"/api/v1/fragrances/{source_id}/alternatives")
    public_alt_ids = [a["id"] for a in public_res.json()["data"]]
    assert rel_id not in public_alt_ids

    # Reviewer approves alternative
    approve_res = client.patch(f"/api/v1/admin/alternatives/{rel_id}/approve", json={
        "approved": True,
        "reviewer_id": "senior-curator-reviewer",
        "review_notes": "Verified against 15 independent community reports and note pyramids.",
    })
    assert approve_res.status_code == 200
    assert approve_res.json()["data"]["status"] == CurationStatus.PUBLISHED.value

    # Public endpoint now includes the approved alternative
    public_res_after = client.get(f"/api/v1/fragrances/{source_id}/alternatives")
    public_alt_ids_after = [a["id"] for a in public_res_after.json()["data"]]
    assert rel_id in public_alt_ids_after


def test_self_referencing_alternative_rejected(client, seed_test_data):
    frag_id = str(seed_test_data["frag_ref"].id)
    payload = {
        "source_fragrance_id": frag_id,
        "candidate_fragrance_id": frag_id,  # Same fragrance
        "relationship_type": RelationshipType.SIMILAR_PROFILE.value,
        "evidence_grade": EvidenceGrade.C_PROVISIONAL.value,
    }
    response = client.post("/api/v1/admin/alternatives", json=payload)
    assert response.status_code == 400
    assert "cannot be marked as an alternative to itself" in response.json()["errors"][0]["message"]
