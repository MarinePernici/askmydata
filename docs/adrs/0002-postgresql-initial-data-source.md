<!-- docs/adr/0002-postgresql-initial-data-source.md -->

# ADR-0002 — Adopt PostgreSQL as the Initial Supported Data Source

## Status

Accepted

**Date:** 2026-07-10

---

# Context

AskMyData is designed to become a generic AI-powered data exploration platform capable of querying multiple structured data sources.

Potential future connectors include:

- MySQL;
- MariaDB;
- SQL Server;
- Oracle;
- DuckDB;
- Snowflake;
- BigQuery;
- other SQL-compatible systems.

Supporting several database engines from the beginning would require:

- multiple connector implementations;
- database-specific SQL generation;
- connector-specific testing;
- additional documentation;
- increased maintenance effort.

As a portfolio project developed by a single developer, the initial objective is to demonstrate a complete and production-oriented architecture rather than maximize connector coverage.

---

# Decision

The Foundation and MVP stages support **PostgreSQL as the only external data source**.

All interactions with external databases are performed through a **Connector** abstraction.

The PostgreSQL Connector is the only concrete implementation during the initial releases.

The rest of the application depends only on the Connector interface and remains independent from PostgreSQL-specific implementation details.

Future connectors may be introduced without requiring changes to the core domain model or major architectural redesign.

---

# Rationale

PostgreSQL was selected because it provides:

- excellent SQL standard compliance;
- mature tooling;
- strong ecosystem support;
- advanced SQL capabilities;
- compatibility with SQLAlchemy;
- widespread adoption in production environments.

Supporting a single database engine allows development effort to focus on the core challenges of AskMyData:

- Knowledge Catalog construction;
- AI-assisted query generation;
- SQL validation;
- conversational data exploration;
- software architecture;
- deployment and observability.

The Connector abstraction preserves extensibility while avoiding premature complexity.

---

# Consequences

## Positive

- Reduced implementation complexity.
- Faster development.
- Smaller testing matrix.
- Simpler CI/CD pipeline.
- Easier debugging.
- Clear connector abstraction.
- Future extensibility remains possible.

## Negative

- Only PostgreSQL databases are supported initially.
- SQL generation may initially rely on PostgreSQL-specific features.
- Connector portability will require future testing.

---

# Alternatives Considered

## Multiple SQL Connectors from the Start

### Advantages

- Broader database compatibility.
- Immediate support for more users.

### Reasons for rejection

The additional complexity would significantly slow development while providing little value for the initial portfolio objectives.

The project would need:

- connector-specific implementations;
- connector-specific integration tests;
- SQL dialect management;
- additional documentation.

These concerns are intentionally postponed.

---

## Database-Agnostic ORM Queries

Generating ORM expressions instead of SQL could reduce dialect differences.

### Advantages

- Reduced SQL dialect dependency.
- Potential portability.

### Reasons for rejection

The project is explicitly designed to generate and validate SQL queries.

The generated SQL must remain transparent, inspectable and executable against external databases.

Using ORM abstractions would make this workflow more difficult and reduce educational value.

---

# Future Evolution

Additional connectors may be introduced by implementing the Connector interface.

Examples include:

- MySQL;
- MariaDB;
- SQL Server;
- Oracle;
- DuckDB;
- Snowflake;
- BigQuery.

The introduction of a new connector should preserve:

- the core Domain Model;
- the Project aggregate boundaries;
- the Knowledge Catalog abstraction;
- the Query Engine interfaces.

Only infrastructure implementations and connector-specific behavior should evolve.

---

# Related Documents

- `docs/application-components.md`
- `docs/domain-model.md`
- `docs/requirements.md`
- `docs/diagrams/src/application-components.puml`