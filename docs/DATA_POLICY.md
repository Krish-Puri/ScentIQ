# SCENTIQ Data Strategy, Provenance, & Rights Policy

*Version 1.0 — Effective November 2026*

This document formalises the data governance, rights management, and provenance protocols for the SCENTIQ fragrance intelligence platform in strict adherence to the SCENTIQ Product Requirements Document (PRD).

---

## 1. Core Principles

1. **Evidence Before Confidence**: No material claim regarding notes, accords, concentration, performance, or alternative status may be published without being mapped to an authoritative `EvidenceSource`.
2. **Data Provenance Before Ingestion**: A public web page is not a reusable dataset. Every source must have an entry in `evidence_sources` with a documented `license_status`.
3. **No Synthetic Product Data in Production**: Synthetic or mock records are restricted to test suites and fixtures. Fabricated records must never be presented as verified production data.
4. **Independent Ranking**: Recommendation ranking is computed organically without commercial, sponsored, or affiliate manipulation.

---

## 2. Dataset Strategy & Restricted Sources

### 2.1 Candidate Open Source: Scento (CC BY 4.0)
- **Status**: Candidate bootstrap dataset for factual identity and note pyramids.
- **Licence**: Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Mandatory Audit Requirements Prior to Bulk Import**:
  1. Inspect the exact snapshot revision and verify attribution requirements.
  2. Verify that all extracted fields (houses, perfumes, notes, accords) are covered under CC BY 4.0.
  3. **Images & API**: Do not assume product images or the Scento live API are covered by the dataset licence. Product images from external sources must remain excluded.
  4. Ensure proper attribution notice is rendered on every public profile utilizing CC BY 4.0 data:
     > *"Data adapted from Scento perfume database (licensed under CC BY 4.0)."*

### 2.2 Restricted Source: Fragrantica
- **Policy**: **STRICT PROHIBITION ON AUTOMATED ACCESS, SCRAPING, OR DATA MINING.**
- **Reasoning**: Fragrantica's Terms of Service effective 14 January 2026 explicitly prohibit automated access, scraping, dataset compilation, vector grounding, or embedding creation without prior written permission.
- **Rule**: No engineer or curator may scrape, ingest, or store Fragrantica content in SCENTIQ databases without an executed written licence.

### 2.3 Product Imagery Policy
- Scraped product photography from retailer websites or perfume houses is **strictly prohibited**.
- Neutral, text-first bottle silhouettes and typographic placeholders are used until direct brand distributor licences are obtained.

---

## 3. Alternative Relationship & Evidence Grading

Alternative relationships are directional (`candidate` -> `reference`) and must be explicitly classified:

| Relationship Type | Definition | Permitted Public Language |
| :--- | :--- | :--- |
| **BRAND_MARKETED** | The manufacturer explicitly markets the candidate as inspired by the reference. | *"Marketed as inspired by [Reference] with brand source."* |
| **DOCUMENTED_REFERENCE** | Official interview or public design statement acknowledges inspiration. | *"Documented reference to [Reference] with citation."* |
| **COMMUNITY_REPORTED** | Multiple credible community and editorial reports observe strong resemblance. | *"Community-reported alternative" / "Reported resemblance".* |
| **SIMILAR_PROFILE** | Overlapping accords and notes indicate a shared scent family without clone claim. | *"Similar scent profile with recorded differences."* |
| **UNVERIFIED** | Provisional or single-user suggestion. | **Never published publicly.** |

### Evidence Grades
- **Grade A (Strong)**: First-party house release or controlled blind panel testing protocol.
- **Grade B (Supported)**: Multiple independent reports with documented caveats.
- **Grade C (Provisional)**: Algorithmic or single report; labelled provisional and hidden by default from primary shortlist.

---

## 4. Indian Regulatory Alignment

### 4.1 Digital Personal Data Protection Act (DPDP Act 2023)
- **Data Minimisation**: SCENTIQ collects only explicit preferences, avoid lists, and optional ratings. No continuous geolocation, gender assumptions, or sensitive personal data are required for discovery.
- **Right to Erasure & Export**: Users can export or delete their profile, feedback, and recommendation history at any time.

### 4.2 Consumer Protection (E-Commerce) Amendment Rules, 2026
- **Ranking Transparency**: Organic discovery algorithms must not favor sellers or brands on the basis of hidden fees or commissions.
- **Observed Pricing**: All price displays in INR include seller name, bottle size (ml), calculated price-per-ml, and observed date timestamp. No guaranteed live pricing claims are made.
