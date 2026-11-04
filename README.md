# SCENTIQ — Evidence-Led Fragrance Intelligence Platform

> **An evidence-led fragrance discovery and recommendation platform combining governed catalogue curation, transparent provenance, and deterministic recommendation intelligence.**

---

## 🌟 Core Product Engineering Principles

1. **Catalogue before Chatbot**: Recommendations are strictly grounded in governed, verified fragrance records. No fabricated notes or non-existent bottles.
2. **Evidence before Confidence**: All similarity and performance claims trace back to an `EvidenceSource` with explicit licensing context.
3. **Deterministic before LLM**: Mathematical multi-factor profile scoring runs first; generative AI is bounded to request parsing and explanation.
4. **No Unsupported Clone Percentages**: Qualitative evidence grades (Grade A, B, C) and side-by-side olfactory diffs replace misleading "95% clone" marketing hype.
5. **India-First, Country-Neutral**: Currency defaults to INR with observed Indian retailer listings and high-heat climate suitability, built on a country-neutral schema.

---

## 📐 Technology Architecture

- **Frontend**: Next.js 14 App Router, TypeScript, Tailwind CSS, Lucide Icons.
- **Backend**: Python 3.12, FastAPI, Pydantic v2 Settings & Schemas, SQLAlchemy 2.0.
- **Database & Migrations**: PostgreSQL 16 (production/Docker) & SQLite (isolated local/test run), Alembic migrations.
- **Testing & CI**: Pytest suite (19 unit/integration/migration tests), GitHub Actions CI.

---

## 🚀 Quickstart

### 1. Configure Environment
```bash
cp .env.example .env
```

### 2. Apply Database Migrations & Seed Verified Data
```bash
# Install backend dependencies
pip install -r apps/api/requirements.txt

# Run migrations
cd apps/api
alembic upgrade head
cd ../..

# Seed verified catalogue, provenance sources, and alternative relationships
python scripts/seed_catalogue.py
```

### 3. Launch Services

**Backend API**:
```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

**Web Application**:
```bash
cd apps/web
npm install
npm run dev
```
- Web Application: [http://localhost:3000](http://localhost:3000)

**Or Launch Everything with Docker Compose**:
```bash
docker compose up --build
```

---

## 🧪 Automated Testing

Run the full pytest suite:
```bash
pytest -v
```

The test harness exercises:
- Database schema constraints and Alembic upgrade/downgrade rollbacks.
- Correlation tracking via `X-Request-ID` and standard response envelopes.
- Duplicate detection and publication validation gates.
- Evidence source licensing and directional alternative review gates.
- Deterministic multi-factor ranking, avoid-term exclusions, and budget ceilings.
- Side-by-side comparisons with shared/distinguishing note calculations.

---

## 📦 Monorepo Directory Map

```text
scentiq/
├── apps/
│   ├── web/                    # Next.js App Router, Tailwind CSS, responsive discovery & compare UI
│   │   ├── src/app/            # App routes: /, /compare, /fragrances/[slug]
│   │   ├── src/lib/            # API client and formatting utilities
│   │   └── package.json
│   │
│   └── api/                    # FastAPI Modular Backend
│       ├── app/
│       │   ├── api/v1/         # Versioned endpoints (fragrances, alternatives, comparisons, recommendations, admin)
│       │   ├── core/           # Config, logging, error handling, security, middleware
│       │   ├── db/             # Base, session, and Alembic migrations
│       │   ├── models/         # SQLAlchemy 2.0 domain entities
│       │   ├── schemas/        # Pydantic v2 request/response schemas
│       │   ├── repositories/   # Data access layer
│       │   ├── services/       # Catalogue, evidence, alternative, comparison, recommendation services
│       │   └── main.py         # Application factory
│       ├── tests/              # 19 automated pytest tests
│       ├── alembic.ini         # Database migration configuration
│       └── requirements.txt    # Python dependencies
│
├── data/
│   ├── raw/                    # Raw external data sources
│   ├── processed/              # Normalized datasets
│   ├── imports/                # Import manifests
│   ├── fixtures/               # Seed data
│   └── scentiq_dev.db          # Local SQLite development database
│
├── docs/
│   ├── ARCHITECTURE.md         # System architecture, ERD, and sequence diagrams
│   ├── DEVELOPMENT.md          # Local developer setup and runbook
│   ├── DATA_POLICY.md          # Data acquisition rules, Scento CC BY 4.0 audit, Fragrantica restrictions
│   └── ADRs/                   # Architecture Decision Records
│       ├── ADR-001-monorepo-modular-monolith.md
│       ├── ADR-002-relational-core-deferred-pgvector.md
│       └── ADR-003-deterministic-ranking-and-evidence-graph.md
│
├── scripts/
│   └── seed_catalogue.py       # Verified catalogue seed script
├── .github/workflows/ci.yml    # Continuous Integration pipeline
├── docker-compose.yml          # Container configuration (PostgreSQL 16, API, Web)
├── .env.example                # Documented configuration template
└── README.md
```

---

## 📋 PRD Implementation Status

| PRD Epic | Workstream | Status | Implementation Details |
| :--- | :--- | :--- | :--- |
| **EPIC-01** | Product Foundation | **Completed** | Monorepo structure, Pydantic v2 typed settings, structured logging with `X-Request-ID` correlation, standard error envelopes, Docker Compose, CI workflow. |
| **EPIC-02** | Database & Migrations | **Completed** | Full relational domain schema in SQLAlchemy 2.0, Alembic migrations tested for upgrade and downgrade rollback, referential constraints, indexing. |
| **EPIC-03** | Catalogue Admin | **Completed** | Curation state machine (`DRAFT` -> `IN_REVIEW` -> `PUBLISHED` -> `NEEDS_REVIEW` -> `ARCHIVED`), duplicate detection, required-field and provenance validation, audit event logging. |
| **EPIC-04** | Evidence & Provenance | **Completed** | Source rights register, claim-to-source mapping, directional alternative relationships with types and A/B/C grades, dual-review moderation gate. |
| **EPIC-05** | Public Catalogue APIs | **Completed** | `/api/v1/fragrances`, `/api/v1/fragrances/{slug}`, filtering by family, notes, accords, prices, draft suppression. |
| **EPIC-06** | Web Client Shell | **Completed** | Responsive Next.js App Router client, live discovery shortlist, side-by-side comparison screen, fragrance dossiers, evidence badges. |
| **EPIC-08** | Recommendation Ranker | **Completed** | Deterministic multi-factor scoring formula from PRD Section 12.3, hard avoid exclusions, budget limits, sample-first advice. |
| **EPIC-10** | Comparison Service | **Completed** | Side-by-side comparison endpoint and UI, shared/distinguishing notes, missing data disclosures, price-per-ml calculation. |
