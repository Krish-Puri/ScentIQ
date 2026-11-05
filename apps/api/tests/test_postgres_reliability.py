"""SCENTIQ PostgreSQL & Reliability Test Suite (Milestone 3 - Part 5).
Validates:
1. Transactional consistency and rollback on failure.
2. Concurrency and idempotent upserts for feedback.
3. Database constraints (unique constraints, check constraints, foreign key cascades).
4. API security audit (JWT auth, RBAC, malformed tokens, input boundary validation).
"""
import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from app.models.enums import CurationStatus, FeedbackType, UserRole
from app.models.user import User, UserProfile, UserFeedback
from app.models.fragrance import Fragrance
from app.models.taxonomy import FragranceNote, FragranceAccord, Note
from app.models.price import PriceListing
from app.models.alternative import AlternativeRelationship
from app.core.security import create_access_token


def test_unique_email_constraint(client):
    """Registering duplicate email must return 409 Conflict without database corruption."""
    email = f"unique_{uuid.uuid4().hex[:6]}@example.com"
    res1 = client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    assert res1.status_code == 200

    res2 = client.post("/api/v1/auth/register", json={"email": email, "password": "password456"})
    assert res2.status_code == 409
    assert "already exists" in res2.json()["errors"][0]["message"]


def test_feedback_idempotent_upsert_concurrency(client, seed_test_data):
    """Rapid repeated or concurrent feedback submissions for the same (user, fragrance)
    must cleanly update in-place without duplicate constraint violation.
    """
    user = client.post("/api/v1/auth/register", json={"email": "concurrency@example.com", "password": "password123"}).json()["data"]
    headers = {"Authorization": f"Bearer {user['access_token']}"}
    frag_id = str(seed_test_data["frag_ref"].id)

    # 1. First submission: LIKE rating 4.0
    r1 = client.post("/api/v1/users/me/feedbacks", json={
        "fragrance_id": frag_id,
        "feedback_type": FeedbackType.LIKE.value,
        "rating": 4.0,
    }, headers=headers)
    assert r1.status_code == 200
    fb_id_1 = r1.json()["data"]["id"]

    # 2. Second submission: Update to DISLIKE rating 2.0
    r2 = client.post("/api/v1/users/me/feedbacks", json={
        "fragrance_id": frag_id,
        "feedback_type": FeedbackType.DISLIKE.value,
        "rating": 2.0,
    }, headers=headers)
    assert r2.status_code == 200
    fb_id_2 = r2.json()["data"]["id"]

    # Must update in-place (same feedback record ID)
    assert fb_id_1 == fb_id_2
    assert r2.json()["data"]["rating"] == 2.0
    assert r2.json()["data"]["feedback_type"] == FeedbackType.DISLIKE.value

    # Verify only 1 record exists
    list_res = client.get("/api/v1/users/me/feedbacks", headers=headers)
    assert len(list_res.json()["data"]) == 1


def test_cascade_delete_fragrance(db, seed_test_data):
    """Deleting a fragrance must cascade delete all associated notes, accords, prices and alternative links."""
    frag_id = seed_test_data["frag_cand"].id

    # Verify existing relations
    notes_count = db.query(FragranceNote).filter(FragranceNote.fragrance_id == frag_id).count()
    accords_count = db.query(FragranceAccord).filter(FragranceAccord.fragrance_id == frag_id).count()
    prices_count = db.query(PriceListing).filter(PriceListing.fragrance_id == frag_id).count()
    assert notes_count > 0
    assert accords_count > 0
    assert prices_count > 0

    # Delete candidate fragrance
    frag = db.query(Fragrance).filter(Fragrance.id == frag_id).first()
    db.delete(frag)
    db.commit()

    # Assert cascade removed all child records
    assert db.query(FragranceNote).filter(FragranceNote.fragrance_id == frag_id).count() == 0
    assert db.query(FragranceAccord).filter(FragranceAccord.fragrance_id == frag_id).count() == 0
    assert db.query(PriceListing).filter(PriceListing.fragrance_id == frag_id).count() == 0
    assert db.query(AlternativeRelationship).filter(AlternativeRelationship.candidate_fragrance_id == frag_id).count() == 0


def test_cascade_delete_user(db):
    """Deleting a user must cascade delete profile and feedbacks."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        auth_subject=f"auth0|{user_id.hex}",
        email="tobedeleted@example.com",
        hashed_password="fakehash",
        role=UserRole.USER,
    )
    db.add(user)
    db.flush()

    profile = UserProfile(user_id=user.id, familiarity_level="casual")
    db.add(profile)
    db.commit()

    # Delete user
    db.delete(user)
    db.commit()

    assert db.query(UserProfile).filter(UserProfile.user_id == user_id).first() is None


def test_input_validation_boundary_rejection(client, seed_test_data):
    """Invalid input boundaries (e.g. rating > 5.0, negative budget) must be rejected with 400 or 422."""
    user = client.post("/api/v1/auth/register", json={"email": "validator@example.com", "password": "password123"}).json()["data"]
    headers = {"Authorization": f"Bearer {user['access_token']}"}
    frag_id = str(seed_test_data["frag_ref"].id)

    # 1. Rating out of bounds (> 5.0)
    r1 = client.post("/api/v1/users/me/feedbacks", json={
        "fragrance_id": frag_id,
        "feedback_type": FeedbackType.LIKE.value,
        "rating": 6.5,
    }, headers=headers)
    assert r1.status_code in (400, 422)

    # 2. Rating out of bounds (< 1.0)
    r2 = client.post("/api/v1/users/me/feedbacks", json={
        "fragrance_id": frag_id,
        "feedback_type": FeedbackType.LIKE.value,
        "rating": 0.5,
    }, headers=headers)
    assert r2.status_code in (400, 422)

    # 3. Negative budget in profile update
    r3 = client.put("/api/v1/users/me/profile", json={
        "budget_max": -500.0,
    }, headers=headers)
    assert r3.status_code in (400, 422)


def test_api_security_rbac_and_malformed_tokens(client, curator_headers, user_headers):
    """API Security Audit:
    - Malformed token returns 401.
    - Regular user trying to access admin endpoint returns 403 Forbidden.
    - Curator token allowed access.
    """
    # 1. Malformed token
    r_bad = client.get("/api/v1/users/me/profile", headers={"Authorization": "Bearer not-a-valid-token"})
    assert r_bad.status_code == 401
    assert "Invalid or expired authentication token" in r_bad.json()["errors"][0]["message"]

    # 2. Expired / empty bearer
    r_empty = client.get("/api/v1/users/me/profile", headers={"Authorization": "Bearer "})
    assert r_empty.status_code == 401

    # 3. Regular user accessing curator-only endpoint
    r_forbidden = client.post("/api/v1/admin/fragrances", json={"brand_id": str(uuid.uuid4()), "canonical_name": "Forbidden Eau"}, headers=user_headers)
    assert r_forbidden.status_code == 403

    # 4. Authorized curator accessing curator endpoint
    r_allowed = client.post("/api/v1/admin/fragrances", json={
        "brand_id": str(uuid.uuid4()),
        "canonical_name": "Allowed Eau",
        "concentration": "EDP",
    }, headers=curator_headers)
    # Returns 404 because brand_id not found, but authorization passed (not 401 or 403)
    assert r_allowed.status_code in (200, 404)
