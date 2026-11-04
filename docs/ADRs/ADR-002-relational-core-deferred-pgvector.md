# ADR-002: Relational Core Schema & Deferred pgvector

## Context
Fragrance discovery relies primarily on discrete, structured dimensions:
- Canonical identity (Brand, Variant, Concentration, Year).
- Note pyramid (Top, Heart, Base).
- Scent accords (Citrus, Woody, Aromatic, Smoky, Amber, etc.).
- Provenance and Evidence claims linked to specific publications.
- Price observations, sellers, and size normalization.

The PRD explicitly states:
*"Use PostgreSQL full-text search and structured filtering initially. Defer pgvector until evaluation demonstrates a measurable benefit."*

## Decision
1. We implement the complete core domain using PostgreSQL relational tables with foreign keys, composite unique constraints, and B-tree/GIN indexing.
2. In local development and automated testing environments, SQLAlchemy's platform-independent type abstractions (`GUID` and generic `JSON`) permit instant in-memory or SQLite testing alongside full PostgreSQL support in Docker Compose.
3. High-dimensional vector embeddings and `pgvector` are deferred until offline retrieval evaluation (golden evaluation query set) establishes that vector retrieval provides a measurable NDCG@5 lift over structured multi-factor ranking.

## Consequences
### Positive
- Strict referential integrity prevents orphaned alternative links or claims without valid sources.
- Query performance is deterministic, inspectable via standard SQL query plans, and avoids black-box embedding drift.
- Faster development, lighter local dependencies, and zero cold-start vector indexing overhead.

### Negative
- Purely conversational natural language queries require structured intent parsing before SQL execution.
