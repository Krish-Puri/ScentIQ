"""Tests for User Onboarding, Profile Persistence, Feedback and Preference Learning (EPIC-07 & EPIC-12).
Verifies:
- User registration and authentication
- Multi-step onboarding sequence completion
- User profile persistence and updates
- User data isolation (User A vs User B)
- Fragrance feedback CRUD operations
- Deterministic preference learning from explicit feedback
- Personalized recommendation scoring integration
"""
import uuid
import pytest
from app.models.enums import FeedbackType


def test_user_registration_and_authentication(client):
    email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    password = "secretPassword123"

    # 1. Register
    reg_res = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg_res.status_code == 200
    reg_data = reg_res.json()["data"]
    assert reg_data["email"] == email
    assert "access_token" in reg_data
    token = reg_data["access_token"]

    # 2. Login
    login_res = client.post("/api/v1/auth/token", json={"email": email, "password": password})
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()["data"]

    # 3. Check /me with token
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == email


def test_user_onboarding_submission_and_profile(client, seed_test_data):
    # Register a new user
    email = f"perfumelover_{uuid.uuid4().hex[:6]}@example.com"
    reg_res = client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    frag_ref_id = str(seed_test_data["frag_ref"].id)

    # 6-Step Onboarding payload
    onboarding_payload = {
        "familiarity_level": "enthusiast",
        "preferred_families": ["Fresh", "Woody"],
        "liked_notes": ["Bergamot", "Cedarwood"],
        "disliked_notes": ["Rose"],
        "liked_accords": ["Citrus", "Woody"],
        "disliked_accords": ["Powdery"],
        "known_fragrances": [
            {"fragrance_id": frag_ref_id, "preference": FeedbackType.LIKE.value}
        ],
        "occasions": ["office", "summer"],
        "budget_min": 1000.0,
        "budget_max": 5000.0,
        "preferred_concentrations": ["EDP", "Parfum"],
        "longevity_preference": "long_lasting",
        "projection_preference": "moderate",
        "avoid_terms": ["tobacco"],
    }

    # Submit onboarding
    res = client.put("/api/v1/users/me/onboarding", json=onboarding_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["onboarding_completed"] is True
    assert data["familiarity_level"] == "enthusiast"
    assert "fresh" in [f.lower() for f in data["preferred_families"]]
    assert data["budget_max"] == 5000.0

    # Avoid terms should automatically aggregate disliked notes, disliked accords and avoid terms
    avoids = [a.lower() for a in data["avoid_terms"]]
    assert "rose" in avoids
    assert "powdery" in avoids
    assert "tobacco" in avoids

    # Verify onboarding status endpoint
    status_res = client.get("/api/v1/users/me/onboarding", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["data"]["completed"] is True

    # Verify known fragrance was saved as user feedback
    fb_res = client.get("/api/v1/users/me/feedbacks", headers=headers)
    assert fb_res.status_code == 200
    feedbacks = fb_res.json()["data"]
    assert len(feedbacks) == 1
    assert feedbacks[0]["fragrance_id"] == frag_ref_id
    assert feedbacks[0]["feedback_type"] == FeedbackType.LIKE.value


def test_user_data_isolation(client):
    # Create User A
    user_a = client.post("/api/v1/auth/register", json={"email": "usera@example.com", "password": "passwordA1"}).json()["data"]
    headers_a = {"Authorization": f"Bearer {user_a['access_token']}"}

    # Create User B
    user_b = client.post("/api/v1/auth/register", json={"email": "userb@example.com", "password": "passwordB1"}).json()["data"]
    headers_b = {"Authorization": f"Bearer {user_b['access_token']}"}

    # User A updates profile
    client.put("/api/v1/users/me/profile", json={"budget_max": 2500.0, "avoid_terms": ["oud"]}, headers=headers_a)

    # User B updates profile differently
    client.put("/api/v1/users/me/profile", json={"budget_max": 15000.0, "avoid_terms": ["aquatic"]}, headers=headers_b)

    # Check User A's profile
    res_a = client.get("/api/v1/users/me/profile", headers=headers_a)
    assert res_a.json()["data"]["budget_max"] == 2500.0
    assert "oud" in res_a.json()["data"]["avoid_terms"]
    assert "aquatic" not in res_a.json()["data"]["avoid_terms"]

    # Check User B's profile
    res_b = client.get("/api/v1/users/me/profile", headers=headers_b)
    assert res_b.json()["data"]["budget_max"] == 15000.0
    assert "aquatic" in res_b.json()["data"]["avoid_terms"]
    assert "oud" not in res_b.json()["data"]["avoid_terms"]


def test_user_feedback_crud_and_preference_learning(client, seed_test_data):
    # Register user
    user = client.post("/api/v1/auth/register", json={"email": "feedbacker@example.com", "password": "password123"}).json()["data"]
    headers = {"Authorization": f"Bearer {user['access_token']}"}

    frag_ref_id = str(seed_test_data["frag_ref"].id)
    frag_cand_id = str(seed_test_data["frag_cand"].id)

    # 1. Add feedback: LIKE for Reference Fragrance
    fb_create = {
        "fragrance_id": frag_ref_id,
        "feedback_type": FeedbackType.LIKE.value,
        "rating": 4.5,
        "reason": "Outstanding citrus and cedar balance for summer mornings.",
        "observed_longevity": "8 hours",
        "observed_projection": "Moderate",
    }
    fb_res = client.post("/api/v1/users/me/feedbacks", json=fb_create, headers=headers)
    assert fb_res.status_code == 200
    fb_data = fb_res.json()["data"]
    assert fb_data["rating"] == 4.5
    assert fb_data["fragrance_name"] == "Reference Eau"

    # 2. Add feedback: DISLIKE for Candidate Fragrance
    fb_dislike = {
        "fragrance_id": frag_cand_id,
        "feedback_type": FeedbackType.DISLIKE.value,
        "rating": 2.0,
        "reason": "Drydown feels too synthetic on my skin.",
    }
    client.post("/api/v1/users/me/feedbacks", json=fb_dislike, headers=headers)

    # 3. List feedbacks
    list_res = client.get("/api/v1/users/me/feedbacks", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) == 2

    # 4. Check preference learning endpoint (EPIC-12)
    learn_res = client.get("/api/v1/users/me/preferences/learned", headers=headers)
    assert learn_res.status_code == 200
    learned = learn_res.json()["data"]
    assert learned["total_feedbacks"] == 2
    assert learned["liked_count"] == 1
    assert learned["disliked_count"] == 1
    assert "inferred_accord_weights" in learned

    # 5. Delete feedback
    del_res = client.delete(f"/api/v1/users/me/feedbacks/{frag_cand_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["data"]["deleted"] is True

    # Confirm only 1 feedback remains
    remain_res = client.get("/api/v1/users/me/feedbacks", headers=headers)
    assert len(remain_res.json()["data"]) == 1


def test_personalised_recommendations_enforce_profile_and_boost_affinity(client, seed_test_data):
    # User with budget ceiling ₹5,000 and avoid 'vanilla'
    user = client.post("/api/v1/auth/register", json={"email": "shopper@example.com", "password": "password123"}).json()["data"]
    headers = {"Authorization": f"Bearer {user['access_token']}"}

    client.put("/api/v1/users/me/profile", json={
        "budget_max": 5000.0,
        "avoid_terms": ["vanilla"],
        "preferred_families": ["Woody Citrus"],
    }, headers=headers)

    # Request recommendations without explicit budget in query
    # Candidate Eau is ₹2,200 (within budget); Reference Eau is ₹12,000 (exceeds budget)
    rec_res = client.post("/api/v1/recommendations", json={
        "session_id": "test-pers-session",
        "constraints": {
            "hard_budget_limit": True,
        },
        "limit": 10,
    }, headers=headers)

    assert rec_res.status_code == 200
    results = rec_res.json()["data"]["results"]
    result_names = [r["canonical_name"] for r in results]

    # Reference Eau (₹12,000) must be filtered out by user profile budget ceiling of ₹5,000
    assert "Reference Eau" not in result_names
    assert "Alternative Eau" in result_names
