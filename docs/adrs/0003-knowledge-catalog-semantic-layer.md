<!-- docs/adr/0003-knowledge-catalog-semantic-layer.md -->

# ADR-0003 — Introduce a Knowledge Catalog as a Semantic Layer

## Status

Accepted

**Date:** 2026-07-13

---

# Context

Large Language Models can generate SQL directly from database schemas.

However, relying solely on raw database metadata presents several limitations:

- technical table and column names may not reflect business concepts;
- schemas may contain hundreds of tables, exceeding model context limits;
- irrelevant objects increase prompt size and reduce answer quality;
- users often describe business concepts rather than physical database structures;
- the application requires a mechanism to preserve business knowledge independently from the database schema.

The project also aims to provide a safer and more maintainable AI-assisted exploration experience.

---

# Decision

AskMyData introduces a **Knowledge Catalog** as an intermediate semantic layer between the external database and the AI Query Engine.

The Knowledge Catalog is built from the selected Catalog Scope and contains:

- discovered technical metadata;
- schema snapshots;
- user-defined semantic metadata;
- business descriptions;
- synonyms;
- visibility rules.

The Query Engine never reasons directly over the complete database schema.

Instead, it consumes the contextual information provided by the Knowledge Catalog.

The external database remains the single source of truth.

The Knowledge Catalog does not replicate or modify business data.

---

# Rationale

Separating technical metadata from semantic knowledge provides several benefits.

The Knowledge Catalog:

- reduces the amount of information sent to the LLM;
- improves prompt quality;
- preserves business terminology;
- enables user customization;
- supports schema evolution;
- isolates AI-specific concerns from database structures.

This approach also creates a clear architectural boundary between:

- data storage;
- metadata;
- semantic enrichment;
- AI reasoning.

The semantic layer becomes an application asset rather than a property of the database itself.

---

# Consequences

## Positive

- Better prompt quality.
- Smaller LLM context.
- Improved response relevance.
- User-defined business vocabulary.
- Better resilience to schema evolution.
- Clear separation between technical and semantic metadata.
- Easier future support for additional connectors.

## Negative

- Additional metadata must be stored.
- Catalog generation introduces an initialization step.
- Catalog refreshes must be managed when schemas evolve.
- Additional synchronization logic is required.

---

# Alternatives Considered

## Direct Database Schema Access

The AI engine could directly inspect the database schema for every question.

### Advantages

- Simpler implementation.
- No intermediate catalog.

### Reasons for rejection

This approach would:

- increase prompt size;
- repeatedly retrieve identical metadata;
- expose irrelevant database objects;
- prevent semantic enrichment;
- provide poorer support for business terminology.

---

## Manual Business Dictionary

A manually maintained business dictionary could replace automatic catalog generation.

### Advantages

- Complete control over descriptions.
- No schema discovery process.

### Reasons for rejection

Manual maintenance would quickly become inconsistent with the actual database schema.

Automatic discovery significantly reduces maintenance effort while preserving synchronization with the source database.

---

# Future Evolution

The Knowledge Catalog may evolve to support:

- richer semantic annotations;
- glossary management;
- business metrics;
- calculated concepts;
- embeddings;
- semantic search;
- automated catalog quality checks;
- AI-assisted metadata suggestions.

These enhancements should extend the semantic layer without changing its primary role as the contextual interface between the database and the AI Query Engine.

---

# Related Documents

- `docs/domain-model.md`
- `docs/application-components.md`
- `docs/requirements.md`
- `docs/diagrams/src/domain-model.puml`