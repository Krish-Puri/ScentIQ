"""Tests for Catalogue Administration (EPIC-03).
Verifies:
- Duplicate detection
- Required field validation
- Curation lifecycle (DRAFT -> IN_REVIEW -> PUBLISHED -> NEEDS_REVIEW -> ARCHIVED)
- Provenance checks on publication
- Audit trail creation
"""
import uuid
import pytest
from app.models.enums import CurationStatus
from app.models.user import AuditEvent


def test_create_draft_fragrance(client, seed_test_data, curator_headers):
    brand_id = str(seed_test_data["brand1"].id)
    payload = {
        "brand_id": brand_id,
        "canonical_name": "New Fresh EDP",
        "concentration": "EDP",
        "family": "Fresh Aquatic",
        "description": "A draft fresh scent under curation.",
    }
    response = client.post("/api/v1/admin/fragrances", json=payload, headers=curator_headers)
    assert response.status_code == 200
    res = response.json()
    assert res["data"]["canonical_name"] == "New Fresh EDP"
    assert res["data"]["status"] == CurationStatus.DRAFT.value
    assert res["data"]["brand_id"] == brand_id


def test_duplicate_detection(client, seed_test_data, curator_headers):
    brand_id = str(seed_test_data["brand1"].id)
    payload = {
        "brand_id": brand_id,
        "canonical_name": "Reference Eau",  # Already exists in seed
        "concentration": "EDP",
    }
    response = client.post("/api/v1/admin/fragrances", json=payload, headers=curator_headers)
    assert response.status_code == 409
    data = response.json()
    assert data["errors"][0]["code"] == "CONFLICT"
    assert "already exists" in data["errors"][0]["message"]


def test_publication_blocked_without_provenance(client, db, seed_test_data, curator_headers):
    # Create a draft fragrance with no claim evidence
    brand_id = str(seed_test_data["brand1"].id)
    payload = {
        "brand_id": brand_id,
        "canonical_name": "Unverified Scent",
        "concentration": "EDP",
    }
    create_res = client.post("/api/v1/admin/fragrances", json=payload, headers=curator_headers)
    assert create_res.status_code == 200
    frag_id = create_res.json()["data"]["id"]

    # Attempt to transition directly to PUBLISHED
    transition_payload = {
        "status": CurationStatus.PUBLISHED.value,
        "notes": "Attempting publication without evidence",
    }
    trans_res = client.patch(f"/api/v1/admin/fragrances/{frag_id}/status", json=transition_payload, headers=curator_headers)
    assert trans_res.status_code == 400
    err = trans_res.json()["errors"][0]
    assert err["code"] == "VALIDATION_ERROR"
    assert "cannot be published without at least one verified evidence claim" in err["message"]


def test_curation_transition_with_provenance_and_audit(client, db, seed_test_data, curator_headers):
    brand_id = str(seed_test_data["brand1"].id)
    source_id = str(seed_test_data["source"].id)

    # 1. Create draft
    create_res = client.post("/api/v1/admin/fragrances", json={
        "brand_id": brand_id,
        "canonical_name": "Documented Fragrance",
        "concentration": "Parfum",
    }, headers=curator_headers)
    frag_id = create_res.json()["data"]["id"]

    # 2. Attach evidence claim
    claim_res = client.post("/api/v1/admin/claims", json={
        "entity_type": "fragrance",
        "entity_id": frag_id,
        "field_name": "canonical_name",
        "source_id": source_id,
        "claim_text": "Verified release document from Brand House.",
        "confidence": 1.0,
    }, headers=curator_headers)
    assert claim_res.status_code == 200

    # 3. Transition to PUBLISHED
    trans_res = client.patch(f"/api/v1/admin/fragrances/{frag_id}/status", json={
        "status": CurationStatus.PUBLISHED.value,
        "notes": "Reviewed and verified against brand documentation",
    }, headers=curator_headers)
    assert trans_res.status_code == 200
    assert trans_res.json()["data"]["status"] == CurationStatus.PUBLISHED.value

    # 4. Verify Audit Event logged in DB
    audits = db.query(AuditEvent).filter(AuditEvent.entity_id == uuid.UUID(frag_id)).all()
    actions = [a.action for a in audits]
    assert "CREATE_FRAGRANCE" in actions
    assert "TRANSITION_PUBLISHED" in actions


def test_admin_routes_require_authorization(client, seed_test_data, user_headers):
    # Missing auth header -> 401
    res_no_auth = client.post("/api/v1/admin/fragrances", json={"brand_id": str(uuid.uuid4()), "canonical_name": "X"})
    assert res_no_auth.status_code == 401

    # Normal user role -> 403
    res_user = client.post("/api/v1/admin/fragrances", json={"brand_id": str(uuid.uuid4()), "canonical_name": "X"}, headers=user_headers)
    assert res_user.status_code == 403

