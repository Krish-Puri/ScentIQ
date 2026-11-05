"""SCENTIQ Health and Readiness Endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.envelope import ResponseEnvelope

router = APIRouter()


@router.get("/health", response_model=ResponseEnvelope[dict])
def health_check():
    return ResponseEnvelope.success(
        data={"status": "healthy", "service": "scentiq-api", "version": "0.1.0"}
    )


@router.get("/ready", response_model=ResponseEnvelope[dict])
def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return ResponseEnvelope.success(
        data={
            "database": db_status,
            "status": "ready" if db_status == "connected" else "degraded",
        }
    )

