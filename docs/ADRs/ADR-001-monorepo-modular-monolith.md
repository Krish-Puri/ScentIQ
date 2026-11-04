# ADR-001: Monorepo Architecture and Modular Monolith

## Context
SCENTIQ is an evidence-led fragrance discovery and recommendation platform. In its early phases (EPIC-01 through EPIC-04), it requires tight cohesion between the relational database schema, catalogue administration, evidence/provenance registries, deterministic ranking algorithms, and user-facing web clients. The team must move quickly with high fidelity to the PRD without premature microservice overhead or multiple decoupled git repositories.

## Decision
We adopt a **monorepo with a modular monolith architecture**:
- `apps/api`: Python (FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2).
- `apps/web`: Next.js App Router (TypeScript, Tailwind CSS).
- `data/`: Structured directory for raw sources, imports, processed data, and test fixtures.
- `docs/`: Centralized architecture, development runbooks, data policy, and ADRs.

Both frontend and backend are independently runnable while sharing root-level orchestration (Docker Compose, CI, and seed scripts).

## Consequences
### Positive
- Unified versioning, CI pipeline, and atomic commits across frontend contracts and backend schemas.
- Zero network latency between domain modules (e.g. Catalogue, Taxonomy, Provenance, and Ranking).
- Drastically reduced operational complexity compared to microservices.

### Negative
- Single repository size will grow over time, necessitating disciplined module boundaries and git hygiene.
