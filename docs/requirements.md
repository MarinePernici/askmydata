# Requirements Specification

## 1. Functional Requirements

### FR-001 — User Authentication

The application shall provide invitation-only user registration.

---

### FR-002 — User Authentication

The application shall provide secure user authentication using server-side sessions.

---

### FR-003 — User Preferences

The application shall allow users to manage their personal preferences.

Supported preferences include:

* interface language;
* preferred response language;
* theme;
* timezone.

---

### FR-004 — Project Management

The application shall allow users to create projects.

---

### FR-005 — Project Management

The application shall allow users to update project information.

---

### FR-006 — Project Management

The application shall allow users to permanently delete projects.

Project conversations shall remain archived and consultable.

---

### FR-007 — Data Source Management

The application shall allow users to configure a PostgreSQL data source.

---

### FR-008 — Data Source Management

The application shall validate the connection before saving the data source.

---

### FR-009 — Data Source Management

The application shall store connection credentials securely.

Credentials shall never be stored in plain text.

---

### FR-010 — Schema Discovery

The application shall automatically discover the connected database structure.

---

### FR-011 — Schema Discovery

The application shall allow users to select the schemas and tables exposed to the AI agent.

---

### FR-012 — Knowledge Catalog

The application shall generate a Knowledge Catalog from the selected database objects.

---

### FR-013 — Knowledge Catalog

The application shall allow users to enrich the Knowledge Catalog with semantic metadata.

Examples include:

* business descriptions;
* synonyms;
* hidden objects.

---

### FR-014 — Knowledge Catalog

The application shall support refreshing the Knowledge Catalog.

A new schema snapshot shall be generated during each refresh.

---

### FR-015 — Natural Language Querying

The application shall allow users to ask questions using natural language.

---

### FR-016 — AI Orchestration

The AI agent shall analyse user intent before generating a query.

---

### FR-017 — AI Orchestration

The AI agent shall request clarification when a question is ambiguous.

---

### FR-018 — Query Generation

The application shall generate source-specific read-only queries.

---

### FR-019 — Query Validation

Generated queries shall be validated before execution.

---

### FR-020 — Query Execution

Only validated read-only queries shall be executed.

---

### FR-021 — Natural Language Response

The application shall generate understandable natural language answers.

---

### FR-022 — Conversation Management

The application shall preserve conversation history.

---

### FR-023 — Contextual Conversations

The AI agent shall use previous conversation messages as contextual information.

---

### FR-024 — Knowledge Catalog Refresh

Users shall be able to refresh a project's Knowledge Catalog at any time.

---

### FR-025 — Internationalization

The application shall support both French and English.

---

### FR-026 — Developer Mode

The application shall provide an optional developer mode exposing execution metrics.

The application shall never expose prompts, secrets or internal AI reasoning.

---

### FR-027 — Administration

The administrator shall manage invitations through the administration interface.

---

### FR-028 — Administration

The administrator shall manage users through the administration interface.

---

# 2. Non-Functional Requirements

## Performance

### NFR-001

Typical requests should complete within 10 seconds under normal conditions.

---

### NFR-002

Knowledge Catalog generation shall execute asynchronously whenever possible.

---

## Security

### NFR-003

Only authenticated users may access projects.

---

### NFR-004

The platform shall use invitation-only registration.

---

### NFR-005

Connected data sources shall always be accessed in read-only mode.

---

### NFR-006

Sensitive credentials shall be encrypted.

---

### NFR-007

The application shall never expose prompts, secrets or internal reasoning.

---

## Architecture

### NFR-008

The application shall follow a modular architecture.

---

### NFR-009

Business logic shall remain independent from infrastructure.

---

### NFR-010

The architecture shall support additional data source connectors with minimal changes.

---

### NFR-011

The AI orchestration pipeline shall remain independent from any specific LLM provider.

---

## Maintainability

### NFR-012

Core business services shall be unit tested.

---

### NFR-013

Architecture decisions shall be documented.

---

### NFR-014

The application shall follow a documentation-first approach.

---

## Deployment

### NFR-015

The application shall be deployable using Docker Compose.

---

### NFR-016

The application shall be cloud-ready.

---

### NFR-017

The application shall support automated deployment through CI/CD.

---

## Observability

### NFR-018

Application logs shall be centralized.

---

### NFR-019

Health checks shall be available.

---

### NFR-020

Execution metrics shall be collected.

---

### NFR-021

Errors shall be traceable through structured logging.

---

## Internationalization

### NFR-022

All user-facing text shall be translatable.

---

## Portability

### NFR-023

The application shall run on Linux.

Development under WSL shall be fully supported.
