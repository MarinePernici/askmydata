<!-- docs>adr>README.md -->

# Architecture Decision Records

This directory contains the Architecture Decision Records (ADRs) for AskMyData.

The project follows the Architecture Decision Record (ADR) approach popularized by Michael Nygard to document significant architectural decisions and their rationale.

Each ADR captures a single architectural decision, the context in which it was made, the selected solution, the alternatives considered and its consequences.

---

## ADR Index

| File | Title | Status |
|------|-------|--------|
| `0001-modular-monolith-architecture.md` | Adopt a Modular Monolith Architecture | Accepted |
| `0002-postgresql-initial-data-source.md` | Adopt PostgreSQL as the Initial Supported Data Source | Accepted |
| `0003-knowledge-catalog-semantic-layer.md` | Introduce a Knowledge Catalog as a Semantic Layer | Accepted |
| `0004-sql-query-validation.md` | Validate Every Generated SQL Query Before Execution | Accepted |

---

## Writing Guidelines

Each ADR follows the same structure:

1. Status
2. Context
3. Decision
4. Rationale
5. Consequences
6. Alternatives Considered
7. Future Evolution (when applicable)
8. Related Documents

Once an ADR is accepted, it should not be modified to reflect later decisions. Instead, a new ADR should be created to supersede or complement the previous one.

The ADRs document architectural decisions, not implementation details.