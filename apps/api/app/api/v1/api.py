"""SCENTIQ API v1 Router Aggregator.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    users,
    advisor,
    fragrances,
    alternatives,
    comparisons,
    recommendations,
    admin_catalogue,
    admin_evidence,
)

api_router = APIRouter()

# Health & Status
api_router.include_router(health.router, tags=["Health"])

# Authentication & Registration
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# User Profile, Onboarding & Feedback
api_router.include_router(users.router, prefix="/users", tags=["Users & Personalisation"])

# AI Fragrance Advisor
api_router.include_router(advisor.router, prefix="/advisor", tags=["AI Fragrance Advisor"])

# Catalogue & Search
api_router.include_router(fragrances.router, prefix="/fragrances", tags=["Fragrances"])

# Alternatives (mounted under /fragrances per PRD Section 13)
api_router.include_router(alternatives.router, prefix="/fragrances", tags=["Alternatives"])

# Comparisons
api_router.include_router(comparisons.router, prefix="/comparisons", tags=["Comparisons"])

# Recommendations
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])

# Admin & Curator operations
api_router.include_router(admin_catalogue.router, prefix="/admin", tags=["Admin Catalogue"])
api_router.include_router(admin_evidence.router, prefix="/admin", tags=["Admin Evidence"])

