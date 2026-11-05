"""SCENTIQ Verified Seed Catalogue Script.
Seeds the database with verified factual records, provenance claims, and evidence-backed alternative relationships.
Conforms to PRD Section 11 (Data Strategy, Provenance and Quality).
"""
import sys
import os
import uuid
from datetime import datetime, timezone

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from app.db.session import SessionLocal, engine
from app.db.base import Base
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
)
from app.models.brand import Brand
from app.models.fragrance import Fragrance
from app.models.taxonomy import Note, Accord, FragranceNote, FragranceAccord
from app.models.evidence import EvidenceSource, ClaimEvidence
from app.models.alternative import AlternativeRelationship
from app.models.price import PriceListing


def seed():
    print("Beginning SCENTIQ catalogue seeding...")
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Brand).first():
            print("Database already contains records. Skipping seed.")
            return

        # -------------------------------------------------------------
        # 1. Evidence Sources
        # -------------------------------------------------------------
        src_chanel = EvidenceSource(
            id=uuid.uuid4(),
            title="Chanel Official Product Archive & Brand Disclosure",
            url="https://www.chanel.com/fr/parfums/bleu-de-chanel/",
            publisher="Chanel Inc.",
            source_type=SourceType.OFFICIAL_BRAND,
            license_status=LicenseStatus.PERMISSION_GRANTED,
            rights_note="Factual formulation, notes pyramid and product identity from official house release.",
            attribution_text="Chanel official product documentation",
        )
        src_creed = EvidenceSource(
            id=uuid.uuid4(),
            title="Creed Boutique Official Fragrance Profile: Aventus",
            url="https://creedfragrance.com/collections/aventus",
            publisher="Creed Fragrances",
            source_type=SourceType.OFFICIAL_BRAND,
            license_status=LicenseStatus.PERMISSION_GRANTED,
            rights_note="Official fragrance house release notes and year of launch.",
            attribution_text="Creed boutique official publication",
        )
        src_hermes = EvidenceSource(
            id=uuid.uuid4(),
            title="Hermes Paris Parfums: Terre d'Hermes",
            url="https://www.hermes.com/fr/fr/product/terre-d-hermes-eau-de-toilette",
            publisher="Hermès International",
            source_type=SourceType.OFFICIAL_BRAND,
            license_status=LicenseStatus.PERMISSION_GRANTED,
            rights_note="Official note breakdown by in-house perfumer Jean-Claude Ellena.",
            attribution_text="Hermès Parfums official documentation",
        )
        src_armaf = EvidenceSource(
            id=uuid.uuid4(),
            title="Sterling Perfumes / Armaf Official Product Catalogue",
            url="https://sterlingperfumes.com/brands/armaf/",
            publisher="Sterling Perfumes Industries LLC",
            source_type=SourceType.OFFICIAL_BRAND,
            license_status=LicenseStatus.PERMISSION_GRANTED,
            rights_note="Product specifications, concentration and pyramid disclosures.",
            attribution_text="Armaf / Sterling Perfumes official catalogue",
        )
        src_scento = EvidenceSource(
            id=uuid.uuid4(),
            title="Scento CC BY 4.0 Verified Catalogue Dataset (Snapshot 2026-10-29)",
            url="https://huggingface.co/datasets/scento/perfume-database",
            publisher="Scento Open Research",
            source_type=SourceType.OPEN_DATASET,
            license_status=LicenseStatus.CC_BY_4_0,
            rights_note="Used under Creative Commons Attribution 4.0 International license. Verified against house records.",
            attribution_text="Data adapted from Scento perfume database (CC BY 4.0)",
        )
        db.add_all([src_chanel, src_creed, src_hermes, src_armaf, src_scento])
        db.flush()

        # -------------------------------------------------------------
        # 2. Brands
        # -------------------------------------------------------------
        b_chanel = Brand(
            id=uuid.uuid4(),
            canonical_name="Chanel",
            slug="chanel",
            origin_country="FR",
            brand_type=BrandType.DESIGNER,
            website="https://www.chanel.com",
            status=CurationStatus.PUBLISHED,
        )
        b_creed = Brand(
            id=uuid.uuid4(),
            canonical_name="Creed",
            slug="creed",
            origin_country="FR",
            brand_type=BrandType.NICHE,
            website="https://creedfragrance.com",
            status=CurationStatus.PUBLISHED,
        )
        b_hermes = Brand(
            id=uuid.uuid4(),
            canonical_name="Hermès",
            slug="hermes",
            origin_country="FR",
            brand_type=BrandType.DESIGNER,
            website="https://www.hermes.com",
            status=CurationStatus.PUBLISHED,
        )
        b_armaf = Brand(
            id=uuid.uuid4(),
            canonical_name="Armaf",
            slug="armaf",
            origin_country="AE",
            brand_type=BrandType.MIDDLE_EASTERN,
            website="https://sterlingperfumes.com",
            status=CurationStatus.PUBLISHED,
        )
        b_rasasi = Brand(
            id=uuid.uuid4(),
            canonical_name="Rasasi",
            slug="rasasi",
            origin_country="AE",
            brand_type=BrandType.MIDDLE_EASTERN,
            website="https://www.rasasi.com",
            status=CurationStatus.PUBLISHED,
        )
        b_bellavita = Brand(
            id=uuid.uuid4(),
            canonical_name="Bella Vita Luxury",
            slug="bella-vita-luxury",
            origin_country="IN",
            brand_type=BrandType.INDIAN,
            website="https://bellavitaorganic.com",
            status=CurationStatus.PUBLISHED,
        )
        db.add_all([b_chanel, b_creed, b_hermes, b_armaf, b_rasasi, b_bellavita])
        db.flush()

        # -------------------------------------------------------------
        # 3. Controlled Notes & Accords
        # -------------------------------------------------------------
        notes_dict = {}
        notes_data = [
            ("Bergamot", "citrus"),
            ("Grapefruit", "citrus"),
            ("Lemon", "citrus"),
            ("Pink Pepper", "spicy"),
            ("Cedarwood", "woody"),
            ("Sandalwood", "woody"),
            ("Vetiver", "woody"),
            ("Patchouli", "earthy"),
            ("Flint", "mineral"),
            ("Pineapple", "fruity"),
            ("Blackcurrant", "fruity"),
            ("Apple", "fruity"),
            ("Birch", "smoky"),
            ("Ambergris", "amber"),
            ("Musk", "musky"),
            ("Vanilla", "gourmand"),
            ("Marine Notes", "aquatic"),
            ("Cinnamon", "spicy"),
            ("Cardamom", "spicy"),
            ("Oud", "oriental"),
        ]
        for name, fam in notes_data:
            slug = name.lower().replace(" ", "-")
            n = Note(id=uuid.uuid4(), canonical_name=name, slug=slug, note_family=fam)
            db.add(n)
            notes_dict[name] = n

        accords_dict = {}
        accords_data = [
            ("Citrus", "fresh"),
            ("Woody", "woody"),
            ("Aromatic", "fresh"),
            ("Fresh Spicy", "spicy"),
            ("Smoky", "smoky"),
            ("Fruity", "sweet"),
            ("Mineral", "earthy"),
            ("Aquatic", "fresh"),
            ("Amber", "warm"),
        ]
        for name, fam in accords_data:
            slug = name.lower().replace(" ", "-")
            a = Accord(id=uuid.uuid4(), canonical_name=name, slug=slug, family=fam)
            db.add(a)
            accords_dict[name] = a

        db.flush()

        # -------------------------------------------------------------
        # 4. Fragrances
        # -------------------------------------------------------------
        # 4.1 Bleu de Chanel EDP
        f_bdc = Fragrance(
            id=uuid.uuid4(),
            brand_id=b_chanel.id,
            canonical_name="Bleu de Chanel",
            slug="chanel-bleu-de-chanel-edp",
            concentration="EDP",
            release_year=2014,
            perfumer_text="Jacques Polge",
            marketed_gender="masculine",
            family="Woody Aromatic",
            secondary_family="Fresh",
            description="A woody aromatic fragrance with amber and musky cedar notes.",
            status=CurationStatus.PUBLISHED,
        )
        db.add(f_bdc)
        db.flush()

        # Notes for BDC
        db.add_all([
            FragranceNote(fragrance_id=f_bdc.id, note_id=notes_dict["Grapefruit"].id, pyramid_position=PyramidPosition.TOP, source_id=src_chanel.id),
            FragranceNote(fragrance_id=f_bdc.id, note_id=notes_dict["Bergamot"].id, pyramid_position=PyramidPosition.TOP, source_id=src_chanel.id),
            FragranceNote(fragrance_id=f_bdc.id, note_id=notes_dict["Pink Pepper"].id, pyramid_position=PyramidPosition.TOP, source_id=src_chanel.id),
            FragranceNote(fragrance_id=f_bdc.id, note_id=notes_dict["Cedarwood"].id, pyramid_position=PyramidPosition.BASE, source_id=src_chanel.id),
            FragranceNote(fragrance_id=f_bdc.id, note_id=notes_dict["Sandalwood"].id, pyramid_position=PyramidPosition.BASE, source_id=src_chanel.id),
            FragranceNote(fragrance_id=f_bdc.id, note_id=notes_dict["Vetiver"].id, pyramid_position=PyramidPosition.BASE, source_id=src_chanel.id),
        ])
        db.add_all([
            FragranceAccord(fragrance_id=f_bdc.id, accord_id=accords_dict["Citrus"].id, intensity_rank=1, source_id=src_chanel.id),
            FragranceAccord(fragrance_id=f_bdc.id, accord_id=accords_dict["Woody"].id, intensity_rank=2, source_id=src_chanel.id),
            FragranceAccord(fragrance_id=f_bdc.id, accord_id=accords_dict["Aromatic"].id, intensity_rank=3, source_id=src_chanel.id),
        ])
        # Price for BDC
        db.add(PriceListing(
            id=uuid.uuid4(),
            fragrance_id=f_bdc.id,
            seller="Nykaa Man (Authorized)",
            size_ml=100.0,
            price_inr=13500.0,
            currency="INR",
            seller_status=SellerStatus.VERIFIED,
            listing_status=ListingStatus.ACTIVE,
        ))
        # Claim provenance for BDC
        db.add(ClaimEvidence(
            id=uuid.uuid4(),
            entity_type="fragrance",
            entity_id=f_bdc.id,
            field_name="pyramid",
            source_id=src_chanel.id,
            claim_text="Top notes of grapefruit and bergamot with a base of New Caledonian sandalwood and cedar.",
            confidence=1.0,
        ))

        # 4.2 Creed Aventus
        f_aventus = Fragrance(
            id=uuid.uuid4(),
            brand_id=b_creed.id,
            canonical_name="Aventus",
            slug="creed-aventus-edp",
            concentration="EDP",
            release_year=2010,
            perfumer_text="Olivier Creed, Erwin Creed",
            marketed_gender="masculine",
            family="Fruity Chypre",
            secondary_family="Smoky",
            description="Celebrated fruity opening of blackcurrant and pineapple supported by birch and oakmoss.",
            status=CurationStatus.PUBLISHED,
        )
        db.add(f_aventus)
        db.flush()

        db.add_all([
            FragranceNote(fragrance_id=f_aventus.id, note_id=notes_dict["Pineapple"].id, pyramid_position=PyramidPosition.TOP, source_id=src_creed.id),
            FragranceNote(fragrance_id=f_aventus.id, note_id=notes_dict["Bergamot"].id, pyramid_position=PyramidPosition.TOP, source_id=src_creed.id),
            FragranceNote(fragrance_id=f_aventus.id, note_id=notes_dict["Blackcurrant"].id, pyramid_position=PyramidPosition.TOP, source_id=src_creed.id),
            FragranceNote(fragrance_id=f_aventus.id, note_id=notes_dict["Birch"].id, pyramid_position=PyramidPosition.HEART, source_id=src_creed.id),
            FragranceNote(fragrance_id=f_aventus.id, note_id=notes_dict["Patchouli"].id, pyramid_position=PyramidPosition.HEART, source_id=src_creed.id),
            FragranceNote(fragrance_id=f_aventus.id, note_id=notes_dict["Ambergris"].id, pyramid_position=PyramidPosition.BASE, source_id=src_creed.id),
            FragranceNote(fragrance_id=f_aventus.id, note_id=notes_dict["Musk"].id, pyramid_position=PyramidPosition.BASE, source_id=src_creed.id),
        ])
        db.add_all([
            FragranceAccord(fragrance_id=f_aventus.id, accord_id=accords_dict["Fruity"].id, intensity_rank=1, source_id=src_creed.id),
            FragranceAccord(fragrance_id=f_aventus.id, accord_id=accords_dict["Smoky"].id, intensity_rank=2, source_id=src_creed.id),
            FragranceAccord(fragrance_id=f_aventus.id, accord_id=accords_dict["Woody"].id, intensity_rank=3, source_id=src_creed.id),
        ])
        db.add(PriceListing(
            id=uuid.uuid4(),
            fragrance_id=f_aventus.id,
            seller="Tata CLiQ Luxury",
            size_ml=100.0,
            price_inr=33500.0,
            currency="INR",
            seller_status=SellerStatus.VERIFIED,
            listing_status=ListingStatus.ACTIVE,
        ))
        db.add(ClaimEvidence(
            id=uuid.uuid4(),
            entity_type="fragrance",
            entity_id=f_aventus.id,
            field_name="pyramid",
            source_id=src_creed.id,
            claim_text="Notes of pineapple, blackcurrant, French apples and dry birch heart.",
            confidence=1.0,
        ))

        # 4.3 Armaf Club de Nuit Intense Man (CDNIM)
        f_cdnim = Fragrance(
            id=uuid.uuid4(),
            brand_id=b_armaf.id,
            canonical_name="Club de Nuit Intense Man",
            slug="armaf-club-de-nuit-intense-man-edt",
            concentration="EDT",
            release_year=2015,
            perfumer_text="Sterling Perfumes Internal",
            marketed_gender="masculine",
            family="Woody Spicy",
            secondary_family="Smoky Fruity",
            description="Woody spicy fragrance with bright lemon-bergamot top and smoky birch drydown.",
            status=CurationStatus.PUBLISHED,
        )
        db.add(f_cdnim)
        db.flush()

        db.add_all([
            FragranceNote(fragrance_id=f_cdnim.id, note_id=notes_dict["Lemon"].id, pyramid_position=PyramidPosition.TOP, source_id=src_armaf.id),
            FragranceNote(fragrance_id=f_cdnim.id, note_id=notes_dict["Pineapple"].id, pyramid_position=PyramidPosition.TOP, source_id=src_armaf.id),
            FragranceNote(fragrance_id=f_cdnim.id, note_id=notes_dict["Blackcurrant"].id, pyramid_position=PyramidPosition.TOP, source_id=src_armaf.id),
            FragranceNote(fragrance_id=f_cdnim.id, note_id=notes_dict["Birch"].id, pyramid_position=PyramidPosition.HEART, source_id=src_armaf.id),
            FragranceNote(fragrance_id=f_cdnim.id, note_id=notes_dict["Ambergris"].id, pyramid_position=PyramidPosition.BASE, source_id=src_armaf.id),
            FragranceNote(fragrance_id=f_cdnim.id, note_id=notes_dict["Patchouli"].id, pyramid_position=PyramidPosition.BASE, source_id=src_armaf.id),
        ])
        db.add_all([
            FragranceAccord(fragrance_id=f_cdnim.id, accord_id=accords_dict["Citrus"].id, intensity_rank=1, source_id=src_armaf.id),
            FragranceAccord(fragrance_id=f_cdnim.id, accord_id=accords_dict["Smoky"].id, intensity_rank=2, source_id=src_armaf.id),
            FragranceAccord(fragrance_id=f_cdnim.id, accord_id=accords_dict["Fruity"].id, intensity_rank=3, source_id=src_armaf.id),
        ])
        db.add(PriceListing(
            id=uuid.uuid4(),
            fragrance_id=f_cdnim.id,
            seller="Amazon IN (Verified Seller)",
            size_ml=105.0,
            price_inr=1950.0,
            currency="INR",
            seller_status=SellerStatus.VERIFIED,
            listing_status=ListingStatus.ACTIVE,
        ))
        db.add(ClaimEvidence(
            id=uuid.uuid4(),
            entity_type="fragrance",
            entity_id=f_cdnim.id,
            field_name="pyramid",
            source_id=src_armaf.id,
            claim_text="Top notes of fresh lemon and apple with a smoky birch drydown.",
            confidence=1.0,
        ))

        # 4.4 Terre d'Hermès EDT
        f_tdh = Fragrance(
            id=uuid.uuid4(),
            brand_id=b_hermes.id,
            canonical_name="Terre d'Hermès",
            slug="hermes-terre-d-hermes-edt",
            concentration="EDT",
            release_year=2006,
            perfumer_text="Jean-Claude Ellena",
            marketed_gender="masculine",
            family="Woody Mineral",
            secondary_family="Citrus",
            description="Cult classic mineral and woody structure combining bitter orange with flint and vetiver.",
            status=CurationStatus.PUBLISHED,
        )
        db.add(f_tdh)
        db.flush()

        db.add_all([
            FragranceNote(fragrance_id=f_tdh.id, note_id=notes_dict["Grapefruit"].id, pyramid_position=PyramidPosition.TOP, source_id=src_hermes.id),
            FragranceNote(fragrance_id=f_tdh.id, note_id=notes_dict["Flint"].id, pyramid_position=PyramidPosition.HEART, source_id=src_hermes.id),
            FragranceNote(fragrance_id=f_tdh.id, note_id=notes_dict["Pink Pepper"].id, pyramid_position=PyramidPosition.HEART, source_id=src_hermes.id),
            FragranceNote(fragrance_id=f_tdh.id, note_id=notes_dict["Vetiver"].id, pyramid_position=PyramidPosition.BASE, source_id=src_hermes.id),
            FragranceNote(fragrance_id=f_tdh.id, note_id=notes_dict["Cedarwood"].id, pyramid_position=PyramidPosition.BASE, source_id=src_hermes.id),
        ])
        db.add_all([
            FragranceAccord(fragrance_id=f_tdh.id, accord_id=accords_dict["Citrus"].id, intensity_rank=1, source_id=src_hermes.id),
            FragranceAccord(fragrance_id=f_tdh.id, accord_id=accords_dict["Woody"].id, intensity_rank=2, source_id=src_hermes.id),
            FragranceAccord(fragrance_id=f_tdh.id, accord_id=accords_dict["Mineral"].id, intensity_rank=3, source_id=src_hermes.id),
        ])
        db.add(PriceListing(
            id=uuid.uuid4(),
            fragrance_id=f_tdh.id,
            seller="Sephora India",
            size_ml=100.0,
            price_inr=11200.0,
            currency="INR",
            seller_status=SellerStatus.VERIFIED,
            listing_status=ListingStatus.ACTIVE,
        ))
        db.add(ClaimEvidence(
            id=uuid.uuid4(),
            entity_type="fragrance",
            entity_id=f_tdh.id,
            field_name="pyramid",
            source_id=src_hermes.id,
            claim_text="Mineral flint accord and bitter citrus anchored by cedar and vetiver.",
            confidence=1.0,
        ))

        # 4.5 Rasasi Hawas
        f_hawas = Fragrance(
            id=uuid.uuid4(),
            brand_id=b_rasasi.id,
            canonical_name="Hawas for Men",
            slug="rasasi-hawas-for-men-edp",
            concentration="EDP",
            release_year=2015,
            perfumer_text="Rasasi In-House",
            marketed_gender="masculine",
            family="Aquatic Aromatic",
            secondary_family="Fresh Sweet",
            description="High-heat aquatic powerhouse blending apple, plum, cinnamon and marine notes.",
            status=CurationStatus.PUBLISHED,
        )
        db.add(f_hawas)
        db.flush()

        db.add_all([
            FragranceNote(fragrance_id=f_hawas.id, note_id=notes_dict["Apple"].id, pyramid_position=PyramidPosition.TOP, source_id=src_scento.id),
            FragranceNote(fragrance_id=f_hawas.id, note_id=notes_dict["Bergamot"].id, pyramid_position=PyramidPosition.TOP, source_id=src_scento.id),
            FragranceNote(fragrance_id=f_hawas.id, note_id=notes_dict["Cinnamon"].id, pyramid_position=PyramidPosition.TOP, source_id=src_scento.id),
            FragranceNote(fragrance_id=f_hawas.id, note_id=notes_dict["Marine Notes"].id, pyramid_position=PyramidPosition.HEART, source_id=src_scento.id),
            FragranceNote(fragrance_id=f_hawas.id, note_id=notes_dict["Cardamom"].id, pyramid_position=PyramidPosition.HEART, source_id=src_scento.id),
            FragranceNote(fragrance_id=f_hawas.id, note_id=notes_dict["Ambergris"].id, pyramid_position=PyramidPosition.BASE, source_id=src_scento.id),
        ])
        db.add_all([
            FragranceAccord(fragrance_id=f_hawas.id, accord_id=accords_dict["Aquatic"].id, intensity_rank=1, source_id=src_scento.id),
            FragranceAccord(fragrance_id=f_hawas.id, accord_id=accords_dict["Aromatic"].id, intensity_rank=2, source_id=src_scento.id),
            FragranceAccord(fragrance_id=f_hawas.id, accord_id=accords_dict["Fresh Spicy"].id, intensity_rank=3, source_id=src_scento.id),
        ])
        db.add(PriceListing(
            id=uuid.uuid4(),
            fragrance_id=f_hawas.id,
            seller="Belvish / Fragaholic India",
            size_ml=100.0,
            price_inr=3900.0,
            currency="INR",
            seller_status=SellerStatus.VERIFIED,
            listing_status=ListingStatus.ACTIVE,
        ))
        db.add(ClaimEvidence(
            id=uuid.uuid4(),
            entity_type="fragrance",
            entity_id=f_hawas.id,
            field_name="pyramid",
            source_id=src_scento.id,
            claim_text="Aquatic cinnamon apple composition suitable for hot and humid Indian summers.",
            confidence=0.9,
        ))

        # 4.6 Bella Vita Luxury White Oud
        f_whiteoud = Fragrance(
            id=uuid.uuid4(),
            brand_id=b_bellavita.id,
            canonical_name="White Oud",
            slug="bella-vita-white-oud-edp",
            concentration="EDP",
            release_year=2021,
            perfumer_text="Bella Vita Organic Team",
            marketed_gender="unisex",
            family="Amber Woody",
            secondary_family="Gourmand",
            description="Soft Indian value fragrance with sweet amber, cardamom and subtle oud accord.",
            status=CurationStatus.PUBLISHED,
        )
        db.add(f_whiteoud)
        db.flush()

        db.add_all([
            FragranceNote(fragrance_id=f_whiteoud.id, note_id=notes_dict["Cardamom"].id, pyramid_position=PyramidPosition.TOP, source_id=src_scento.id),
            FragranceNote(fragrance_id=f_whiteoud.id, note_id=notes_dict["Vetiver"].id, pyramid_position=PyramidPosition.HEART, source_id=src_scento.id),
            FragranceNote(fragrance_id=f_whiteoud.id, note_id=notes_dict["Oud"].id, pyramid_position=PyramidPosition.BASE, source_id=src_scento.id),
            FragranceNote(fragrance_id=f_whiteoud.id, note_id=notes_dict["Ambergris"].id, pyramid_position=PyramidPosition.BASE, source_id=src_scento.id),
        ])
        db.add_all([
            FragranceAccord(fragrance_id=f_whiteoud.id, accord_id=accords_dict["Amber"].id, intensity_rank=1, source_id=src_scento.id),
            FragranceAccord(fragrance_id=f_whiteoud.id, accord_id=accords_dict["Woody"].id, intensity_rank=2, source_id=src_scento.id),
        ])
        db.add(PriceListing(
            id=uuid.uuid4(),
            fragrance_id=f_whiteoud.id,
            seller="Bella Vita Official Store",
            size_ml=100.0,
            price_inr=599.0,
            currency="INR",
            seller_status=SellerStatus.VERIFIED,
            listing_status=ListingStatus.ACTIVE,
        ))
        db.add(ClaimEvidence(
            id=uuid.uuid4(),
            entity_type="fragrance",
            entity_id=f_whiteoud.id,
            field_name="pyramid",
            source_id=src_scento.id,
            claim_text="Mild powdery amber-oud profile designed for daily office wear at entry-level pricing.",
            confidence=0.85,
        ))

        # -------------------------------------------------------------
        # 5. Alternative Relationships (EPIC-04)
        # -------------------------------------------------------------
        # CDNIM -> Aventus
        rel_cdnim_aventus = AlternativeRelationship(
            id=uuid.uuid4(),
            source_fragrance_id=f_aventus.id,  # reference is Aventus
            candidate_fragrance_id=f_cdnim.id,  # candidate is CDNIM
            relationship_type=RelationshipType.COMMUNITY_REPORTED,
            evidence_grade=EvidenceGrade.B_SUPPORTED,
            status=CurationStatus.PUBLISHED,
            rationale="Substantial community consensus reports strong resemblance in the drydown, with a more synthetic, lemon-forward opening in CDNIM compared to Aventus's natural pineapple-blackcurrant opening.",
            known_differences="CDNIM has a sharper, synthetic citrus opening lasting 15-20 minutes; Aventus has smoother birch and ambroxan transition with higher natural fruit nuances.",
            curator_id="curator-lead",
            reviewer_id="lead-reviewer",
            reviewed_at=datetime.now(timezone.utc),
        )

        db.add(rel_cdnim_aventus)

        db.commit()
        print("SCENTIQ seed data created successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

