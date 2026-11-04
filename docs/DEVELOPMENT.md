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

## 3. Running with Docker Compose

To start the full PostgreSQL 16 database, FastAPI backend, and Next.js frontend in containers:
```bash
docker compose up --build
```

---

## 4. Running Automated Tests

Run the full pytest suite across all units, repositories, validation rules, migrations, and endpoints:
```bash
pytest -v
```

To run a specific test module:
```bash
pytest apps/api/tests/test_catalogue_admin.py -v
pytest apps/api/tests/test_evidence_provenance.py -v
pytest apps/api/tests/test_recommendations.py -v
pytest apps/api/tests/test_comparisons.py -v
pytest apps/api/tests/test_migrations.py -v
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
alembic revision -m "add_new_feature_table"
```

---

## 6. Architecture & Code Conventions

- **Models (`apps/api/app/models/`)**: Pure SQLAlchemy 2.0 mapped models.
- **Schemas (`apps/api/app/schemas/`)**: Pydantic v2 schemas. Every public response wraps data inside `ResponseEnvelope`.
- **Repositories (`apps/api/app/repositories/`)**: Encapsulates DB queries and transactions.
- **Services (`apps/api/app/services/`)**: Business logic, curation state machines, evidence validation, and deterministic ranking.
- **Endpoints (`apps/api/app/api/v1/endpoints/`)**: Fast, typed route handlers with dependency injection.
