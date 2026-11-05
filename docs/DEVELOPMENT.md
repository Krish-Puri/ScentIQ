# SCENTIQ Local Development Guide

Welcome to the **SCENTIQ** engineering workspace. This guide explains how to configure, run, test, and maintain the application.

---

## 1. Prerequisites

- **Python**: 3.12+
- **Node.js**: 20+ (Node 22 LTS recommended)
- **PostgreSQL**: 16 (or use built-in SQLite fallback for instant local testing)
- **Docker & Docker Compose** (optional for containerized run)

---

## 2. Quickstart (Standalone Local Mode)

### Step 1: Environment Variables
Create your local `.env` from `.env.example`:
```bash
cp .env.example .env
```

### Step 2: Backend Dependencies & Database
From the root of the repository:
```bash
# Install Python packages
pip install -r apps/api/requirements.txt

# Apply database migrations
cd apps/api
alembic upgrade head
cd ../..

# Seed verified catalogue and evidence sources
python scripts/seed_catalogue.py

# Expand catalogue with 50+ curated verified records
python scripts/expand_catalogue.py
```

### Step 3: Frontend Dependencies
```bash
cd apps/web
npm install
cd ../..
```

### Step 4: Run Application
Start the backend (Terminal 1):
```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```
- API Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- API Health: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

Start the web client (Terminal 2):
```bash
npm run dev:web
```
- Web Application: [http://localhost:3000](http://localhost:3000)

---

## 3. Running Automated Tests & Evaluation Harness

### Run the full pytest suite (44 tests):
```bash
python -m pytest apps/api/tests -v
```

### Run Specific Test Suites:
```bash
# Recommendation IR Quality & Safety Benchmark (Precision@5, NDCG@5, Recall@10, Exclusion Rate)
python -m pytest apps/api/tests/test_recommendation_benchmark.py -v

# AI Fragrance Advisor NLP Robustness & Adversarial Testing
python -m pytest apps/api/tests/test_ai_advisor_benchmark.py -v

# PostgreSQL Constraints, Cascades, Concurrency & Security Audit
python -m pytest apps/api/tests/test_postgres_reliability.py -v

# Complete 14-Step Full User Journey Integration Test
python -m pytest apps/api/tests/test_full_journey_e2e.py -v

# Deterministic User Personalisation & Neutral Action Semantics
python -m pytest apps/api/tests/test_user_personalisation.py -v
```

### Run Frontend Production Build & Playwright E2E:
```bash
# Production build check (compiles all routes)
npm --prefix apps/web run build

# Playwright E2E test
npx --prefix apps/web playwright test
```

---

## 4. Catalogue Governance & Quality Validation

Validate database consistency, complete note pyramids, positive INR pricing, and evidence provenance:
```bash
python scripts/validate_catalogue_data.py
```

---

## 5. Database Migrations Workflow

SCENTIQ uses Alembic for database version control.

### Apply migrations:
```bash
cd apps/api
alembic upgrade head
```

### Rollback last migration:
```bash
cd apps/api
alembic downgrade -1
```

### Create a new revision:
```bash
cd apps/api
alembic revision -m "description_of_change"
```

---

## 6. Architecture & Code Conventions

- **Models (`apps/api/app/models/`)**: Pure SQLAlchemy 2.0 mapped models.
- **Schemas (`apps/api/app/schemas/`)**: Pydantic v2 schemas. Every public response wraps data inside `ResponseEnvelope`.
- **Evaluation (`apps/api/app/evaluation/`)**: IR metrics (Precision@5, NDCG@5, Diversity, Coverage), scenario datasets, and benchmark runner.
- **Repositories (`apps/api/app/repositories/`)**: Encapsulates DB queries and transactions.
- **Services (`apps/api/app/services/`)**: Business logic, preference learning, AI intent parsing, and deterministic ranking engine.
- **Endpoints (`apps/api/app/api/v1/endpoints/`)**: Fast, typed route handlers with dependency injection.
