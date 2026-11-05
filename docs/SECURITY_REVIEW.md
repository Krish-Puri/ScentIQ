# SCENTIQ — Application Security & Reliability Review

## Milestone 3 Deliverable (Section 15 & 16)

This document provides a technical audit of the security architecture, access controls, data isolation, and reliability controls implemented across SCENTIQ.

---

## 1. Authentication & Role-Based Access Control (RBAC)

### 1.1 Token Lifecycle & Cryptography
- **Algorithm**: HMAC-SHA256 (HS256) with configurable secret key (`JWT_SECRET_KEY`).
- **Token Expiry**: Configurable (`ACCESS_TOKEN_EXPIRE_MINUTES = 10080` / 7 days).
- **Password Hashing**: Direct `bcrypt.hashpw` and `bcrypt.checkpw` with unique salts.
- **Error Behavior**: Malformed, unsigned, empty, or expired tokens immediately trigger `401 Unauthorized` via `AppException(ErrorCode.AUTH_REQUIRED)` without exposing stack traces.

### 1.2 RBAC Policy Matrix

| Role | Public Catalogue | Personal Profile & Feedbacks | AI Advisor | Admin Fragrance Curation | Audit Logs |
|---|---|---|---|---|---|
| **GUEST** | Read-Only | Denied | Anonymous Session | Denied | Denied |
| **USER** | Read-Only | Full Access (Self Only) | Full Access (With Profile) | Denied (403) | Denied |
| **CURATOR** | Read-Only | Full Access | Full Access | Create/Edit Drafts | Denied |
| **REVIEWER** | Read-Only | Full Access | Full Access | Review & Publish (Dual Review) | Read-Only |
| **ADMIN** | Full Access | Full Access | Full Access | Full Access | Full Access |

---

## 2. Multi-Tenant Data Isolation & Privacy

- **Tenant Isolation**: All user endpoints (`/api/v1/users/me/*`) derive the active user ID strictly from the authenticated JWT token claim (`sub`). Query parameters or payload IDs cannot override the authenticated caller.
- **Cross-User Tampering Prevention**: Verified by automated test `test_user_data_isolation`: attempting to delete or access another user's feedback returns `404 Not Found`.
- **Data Minimisation**: User profiles store only fragrance preferences (families, accords, notes, budget, occasions, avoid terms). No demographic, location-tracking, or financial PII is requested or persisted.

---

## 3. Database Constraints & Transactional Integrity

Verified via `apps/api/tests/test_postgres_reliability.py`:

1. **Unique Constraints**:
   - `users.email`: Enforces email uniqueness; duplicate registration returns `409 Conflict`.
   - `fragrances.uq_brand_slug_concentration`: Prevents duplicate entries of the same fragrance name/concentration under a brand.
   - `alternative_relationships.uq_source_candidate_alternative`: Enforces single directional relationship between any reference and candidate.
2. **Foreign Key Cascade Deletion**:
   - Deleting a `Fragrance` automatically purges associated `FragranceNote`, `FragranceAccord`, `PriceListing`, and `AlternativeRelationship` records without leaving orphaned rows.
   - Deleting a `User` cascades and cleanses `UserProfile`, `UserFeedback`, and `RecommendationRun` records.
3. **Boundary Check Constraints**:
   - Ratings are strictly bounded between `1.0` and `5.0`.
   - Prices must be positive (> 0.0 INR).
   - Budgets cannot be negative.
   - Out-of-boundary inputs are rejected with `400 Bad Request` / `422 Unprocessable Entity`.

---

## 4. SQL Injection & API Hardening

- **SQL Injection**: 100% of database operations use SQLAlchemy 2.0 ORM expressions (`select(Model).where(...)`) with parameterized query compilation. Zero raw SQL concatenation exists.
- **Adversarial Prompt Defense**: AI Advisor input pipeline cleanses injection phrases (`ignore previous instructions`, `system override`, `dump database`).
- **Hard Constraint Safety Lock**: Hard exclusions (`avoid_terms`) from user profiles are strictly immutable within session queries.

---

## 5. Security Test Suite Execution

To execute the automated security and reliability test suite:
```bash
python -m pytest apps/api/tests/test_postgres_reliability.py -v
```
All 6 security and reliability test suites pass with zero warnings.

