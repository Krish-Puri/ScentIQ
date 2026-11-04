"""SCENTIQ Domain Enumerations.
Strictly mapped to PRD Sections 8.5, 10.1, 10.4, 11.4, and 11.5.
"""
from enum import Enum


class CurationStatus(str, Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    PUBLISHED = "PUBLISHED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    ARCHIVED = "ARCHIVED"


class RelationshipType(str, Enum):
    BRAND_MARKETED = "BRAND_MARKETED"  # Brand explicitly markets inspiration
    DOCUMENTED_REFERENCE = "DOCUMENTED_REFERENCE"  # Verified interview / official reference
    COMMUNITY_REPORTED = "COMMUNITY_REPORTED"  # Community consensus resemblance
    SIMILAR_PROFILE = "SIMILAR_PROFILE"  # Overlapping notes/accords, no clone claim
    UNVERIFIED = "UNVERIFIED"  # Provisional / unverified


class EvidenceGrade(str, Enum):
    A_STRONG = "A_STRONG"  # Grade A: First-party brand claim or controlled independent test
    B_SUPPORTED = "B_SUPPORTED"  # Grade B: Multiple independent credible reports with caveats
    C_PROVISIONAL = "C_PROVISIONAL"  # Grade C: Single report / algorithmic / provisional


class PyramidPosition(str, Enum):
    TOP = "TOP"
    HEART = "HEART"
    BASE = "BASE"
    UNSPECIFIED = "UNSPECIFIED"


class BrandType(str, Enum):
    DESIGNER = "DESIGNER"
    NICHE = "NICHE"
    MIDDLE_EASTERN = "MIDDLE_EASTERN"
    INDIAN = "INDIAN"
    INDIE = "INDIE"
    MASS_MARKET = "MASS_MARKET"


class UserRole(str, Enum):
    GUEST = "GUEST"
    USER = "USER"
    CURATOR = "CURATOR"
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"


class FeedbackType(str, Enum):
    LIKE = "LIKE"
    DISLIKE = "DISLIKE"
    NOT_FOR_ME = "NOT_FOR_ME"
    INTERESTED = "INTERESTED"
    TRIED = "TRIED"
    OWNED = "OWNED"


class SourceType(str, Enum):
    OFFICIAL_BRAND = "OFFICIAL_BRAND"
    AUTHORIZED_RETAILER = "AUTHORIZED_RETAILER"
    INDEPENDENT_TEST = "INDEPENDENT_TEST"
    COMMUNITY = "COMMUNITY"
    EDITORIAL = "EDITORIAL"
    OPEN_DATASET = "OPEN_DATASET"


class LicenseStatus(str, Enum):
    PUBLIC_DOMAIN = "PUBLIC_DOMAIN"
    CC_BY_4_0 = "CC_BY_4_0"
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    PROPRIETARY_RESTRICTED = "PROPRIETARY_RESTRICTED"
    UNKNOWN = "UNKNOWN"


class SellerStatus(str, Enum):
    VERIFIED = "VERIFIED"
    COMMUNITY_REPORTED = "COMMUNITY_REPORTED"
    UNVERIFIED = "UNVERIFIED"


class ListingStatus(str, Enum):
    ACTIVE = "ACTIVE"
    STALE = "STALE"
    SUPPRESSED = "SUPPRESSED"
