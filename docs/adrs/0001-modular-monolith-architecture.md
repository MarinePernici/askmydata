<!-- docs>adr>0001-modular-monolith-architecture.md -->

# ADR-0001 — Adopt a Modular Monolith Architecture

## Status

Accepted

**Date:** 2026-07-09

---

# Context

AskMyData is a portfolio project whose primary objective is to demonstrate software engineering practices applied to an AI-powered application.

The project is developed by a single developer and aims to showcase competencies in:

- Python development;
- Django;
- software architecture;
- AI integration;
- Docker;
- CI/CD;
- testing;
- observability;
- deployment.

Although the application integrates Large Language Models (LLMs), its expected workload is limited and does not initially justify a distributed architecture.

At the same time, the architecture should remain flexible enough to support future evolution without requiring major redesign.

---

# Decision

AskMyData will be implemented as a **Modular Monolith**.

The application will initially be deployed as a single Django application while separating business capabilities into independent modules.

The initial architecture separates the following business capabilities:

- Accounts;
- Projects;
- Data Source Management;
- Catalog;
- Conversations;
- Query Engine;
- Connectors;
- Observability;
- Shared Kernel.

Each module owns its business responsibilities and communicates with other modules through explicit application services and well-defined interfaces.

External systems such as PostgreSQL and LLM providers are accessed through infrastructure abstractions.

The AI Query Engine remains an internal module during the Foundation and MVP stages.

Its public interfaces are intentionally designed to allow future extraction into a dedicated service if operational requirements justify it.

---

# Rationale

A modular monolith provides the best balance between simplicity and maintainability for the current project.

It enables:

- rapid feature development;
- reduced operational complexity;
- straightforward local development;
- simpler testing;
- easier debugging;
- a single deployment unit.

At the same time, clear module boundaries reduce coupling and encourage good architectural practices.

This approach also aligns with the project's educational objective by demonstrating domain-driven modularization without introducing unnecessary infrastructure.

---

# Consequences

## Positive

- Simple deployment architecture.
- Single application to maintain.
- Lower infrastructure costs.
- Easier local development.
- Easier debugging.
- Faster development cycle.
- Explicit module boundaries.
- Improved testability.
- Straightforward Docker deployment.
- Simple CI/CD pipeline.
- Future service extraction remains possible.

## Negative

- All modules share the same deployment lifecycle.
- Independent scaling of individual modules is not possible.
- Strong discipline is required to preserve module boundaries.
- Internal dependencies must be carefully managed to avoid becoming a "big ball of mud."

---

# Alternatives Considered

## Django + FastAPI Microservices

Each major capability would be deployed as an independent service.

### Advantages

- Independent deployment.
- Independent scaling.
- Clear runtime isolation.

### Reasons for rejection

The additional operational complexity is not justified for the expected workload or team size.

It would introduce:

- service-to-service communication;
- multiple deployment pipelines;
- distributed debugging;
- duplicated infrastructure;
- increased maintenance effort.

The benefits do not outweigh the costs for the current scope.

---

## FastAPI as the Main Application

FastAPI could have been selected as the primary application framework.

### Advantages

- Lightweight.
- Excellent API performance.
- Strong asynchronous capabilities.

### Reasons for rejection

AskMyData requires more than an API.

The project includes:

- authentication;
- administration;
- server-rendered pages;
- user management;
- project management;
- administration tools.

Django provides these capabilities out of the box while remaining fully compatible with modern architectural practices.

FastAPI remains a viable candidate for future extraction of the Query Engine if independent deployment becomes desirable.

---

# Future Evolution

The current architecture intentionally preserves clear extraction boundaries.

If future requirements justify it, the following component may become an independent service:

- Query Engine.

Such an evolution should not require changes to the domain model or business rules, only to the deployment architecture.

---

# Related Documents

- `docs/application-components.md`
- `docs/domain-model.md`
- `docs/requirements.md`
- `docs/diagrams/src/application-components.puml`