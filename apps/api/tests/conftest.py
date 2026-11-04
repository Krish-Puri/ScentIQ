"""SCENTIQ Test Fixtures and Harness.
Uses an isolated in-memory SQLite database for fast, reliable, reproducible testing.
"""
import uuid
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import (
    BrandType,
    CurationStatus,
    EvidenceGrade,
    LicenseStatus,
    ListingStatus,
    PyramidPosition,
    RelationshipType,
    SellerStatus,
    SourceType,
    UserRole,
)
from app.models.brand import Brand
from app.models.fragrance import Fragrance
from app.models.taxonomy import Note, Accord, FragranceNote, FragranceAccord
from app.models.evidence import EvidenceSource, ClaimEvidence
from app.models.alternative import AlternativeRelationship
from app.models.price import PriceListing

TEST_DB_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Provides a fresh, isolated database per test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """TestClient with get_db dependency overridden to use the test session."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_test_data(db: Session):
    """Seeds a minimal verified dataset for tests."""
    source = EvidenceSource(
        id=uuid.uuid4(),
        title="Official Brand Release",
        url="https://example.com/brand",
        publisher="Brand House",
        source_type=SourceType.OFFICIAL_BRAND,
        license_status=LicenseStatus.PERMISSION_GRANTED,
    )
    db.add(source)

    brand1 = Brand(
        id=uuid.uuid4(),
        canonical_name="Luxury House",
        slug="luxury-house",
        brand_type=BrandType.DESIGNER,
        origin_country="FR",
        status=CurationStatus.PUBLISHED,
    )
    brand2 = Brand(
        id=uuid.uuid4(),
        canonical_name="Value House",
        slug="value-house",
        brand_type=BrandType.MIDDLE_EASTERN,
        origin_country="AE",
        status=CurationStatus.PUBLISHED,
    )
    db.add_all([brand1, brand2])
    db.flush()

    note1 = Note(id=uuid.uuid4(), canonical_name="Bergamot", slug="bergamot", note_family="citrus")
    note2 = Note(id=uuid.uuid4(), canonical_name="Cedarwood", slug="cedarwood", note_family="woody")
    note3 = Note(id=uuid.uuid4(), canonical_name="Vanilla", slug="vanilla", note_family="gourmand")
    db.add_all([note1, note2, note3])

    accord1 = Accord(id=uuid.uuid4(), canonical_name="Citrus", slug="citrus", family="fresh")
    accord2 = Accord(id=uuid.uuid4(), canonical_name="Woody", slug="woody", family="woody")
    db.add_all([accord1, accord2])
    db.flush()

    # Reference Fragrance
    frag_ref = Fragrance(
        id=uuid.uuid4(),
        brand_id=brand1.id,
        canonical_name="Reference Eau",
        slug="luxury-house-reference-eau-edp",
        concentration="EDP",
        family="Woody Citrus",
        status=CurationStatus.PUBLISHED,
    )
    # Candidate Fragrance
    frag_cand = Fragrance(
        id=uuid.uuid4(),
        brand_id=brand2.id,
        canonical_name="Alternative Eau",
        slug="value-house-alternative-eau-edp",
        concentration="EDP",
        family="Woody Citrus",
        status=CurationStatus.PUBLISHED,
    )
    db.add_all([frag_ref, frag_cand])
    db.flush()

    # Notes & Accords
    db.add(FragranceNote(fragrance_id=frag_ref.id, note_id=note1.id, pyramid_position=PyramidPosition.TOP))
    db.add(FragranceNote(fragrance_id=frag_ref.id, note_id=note2.id, pyramid_position=PyramidPosition.BASE))
    db.add(FragranceNote(fragrance_id=frag_cand.id, note_id=note1.id, pyramid_position=PyramidPosition.TOP))
    db.add(FragranceNote(fragrance_id=frag_cand.id, note_id=note2.id, pyramid_position=PyramidPosition.BASE))
    db.add(FragranceAccord(fragrance_id=frag_ref.id, accord_id=accord1.id, intensity_rank=1))
    db.add(FragranceAccord(fragrance_id=frag_cand.id, accord_id=accord1.id, intensity_rank=1))

    # Prices
    db.add(PriceListing(fragrance_id=frag_ref.id, seller="Store A", price_inr=12000.0, size_ml=100.0))
    db.add(PriceListing(fragrance_id=frag_cand.id, seller="Store B", price_inr=2200.0, size_ml=100.0))

    # Provenance Claim
    db.add(ClaimEvidence(
        entity_type="fragrance",
        entity_id=frag_ref.id,
        field_name="pyramid",
        source_id=source.id,
        claim_text="Verified pyramid top bergamot, base cedarwood.",
    ))
    db.add(ClaimEvidence(
        entity_type="fragrance",
        entity_id=frag_cand.id,
        field_name="pyramid",
        source_id=source.id,
        claim_text="Verified candidate pyramid.",
    ))

    # Published alternative relationship
    rel = AlternativeRelationship(
        source_fragrance_id=frag_ref.id,
        candidate_fragrance_id=frag_cand.id,
        relationship_type=RelationshipType.COMMUNITY_REPORTED,
        evidence_grade=EvidenceGrade.B_SUPPORTED,
        status=CurationStatus.PUBLISHED,
        rationale="Strong drydown resemblance with minor opening variance.",
        reviewer_id="reviewer-1",
    )
    db.add(rel)

    db.commit()

    return {
        "source": source,
        "brand1": brand1,
        "brand2": brand2,
        "note1": note1,
        "note2": note2,
        "note3": note3,
        "frag_ref": frag_ref,
        "frag_cand": frag_cand,
        "relationship": rel,
    }
