<!-- docs>requirements.md -->

# Software Requirements Specification

## 1. Purpose

This document defines the functional, non-functional and engineering requirements for AskMyData.

Its purpose is to provide a stable reference for design, implementation, testing and future evolution of the project.

This specification focuses on **what** the system must achieve rather than **how** it is implemented.

---

# 2. Product Scope

AskMyData is an AI-assisted data exploration platform that enables users to interact with structured data using natural language.

Instead of relying solely on database schemas, the platform builds a semantic Knowledge Catalog describing the data structure and business context. This catalog allows the AI engine to generate more reliable, secure and explainable answers.

The platform focuses exclusively on read-only exploration of structured databases.

---

# 3. Guiding Principle

The primary capability of AskMyData is to enable reliable AI-assisted exploration of structured data without requiring users to understand database schemas or write SQL queries.

Every requirement defined in this specification contributes directly to this objective.

---

# 4. Releases

The project is developed incrementally.

| Release | Objective |
|----------|-----------|
| Foundation | Validate the AI query engine and the application architecture. |
| MVP | Deliver a complete web application for AI-assisted PostgreSQL exploration. |
| Production-ready Portfolio | Demonstrate industrialization, observability and deployment practices. |

---

# 5. Functional Requirements

## 5.1 Authentication

### FR-AUTH-001

The system shall allow users to authenticate securely.

**Release:** MVP

---

### FR-AUTH-002

The system shall protect authenticated sessions.

**Release:** MVP

---

## 5.2 Project Management

### FR-PROJ-001

The system shall allow authenticated users to create projects.

**Release:** MVP

---

### FR-PROJ-002

The system shall allow users to update project information.

**Release:** MVP

---

### FR-PROJ-003

The system shall allow users to archive projects.

**Release:** MVP

---

## 5.3 Data Sources

### FR-DATA-001

The system shall support PostgreSQL as the initial database connector.

**Release:** Foundation

---

### FR-DATA-002

The system shall validate database connections before saving them.

**Release:** MVP

---

### FR-DATA-003

The system shall store connection credentials securely.

**Release:** MVP

---

### FR-DATA-004

The system shall access external databases using read-only permissions.

**Release:** Foundation

---

## 5.4 Knowledge Catalog

### FR-KCAT-001

The system shall discover database schemas.

**Release:** Foundation

---

### FR-KCAT-002

The system shall generate a Knowledge Catalog from discovered metadata.

**Release:** Foundation

---

### FR-KCAT-003

The system shall allow semantic descriptions to enrich the Knowledge Catalog.

**Release:** MVP

---

### FR-KCAT-004

The system shall allow the Knowledge Catalog to be regenerated after schema changes.

**Release:** MVP

---

## 5.5 AI Query Engine

### FR-AI-001

The system shall accept natural language questions.

**Release:** Foundation

---

### FR-AI-002

The system shall use the Knowledge Catalog as contextual information.

**Release:** Foundation

---

### FR-AI-003

The system shall generate SQL queries from user requests.

**Release:** Foundation

---

### FR-AI-004

The system shall validate generated SQL before execution.

**Release:** Foundation

---

### FR-AI-005

The system shall execute validated SQL queries.

**Release:** Foundation

---

### FR-AI-006

The system shall generate natural language answers from query results.

**Release:** Foundation

---

### FR-AI-007

The system shall request clarification when a question is ambiguous.

**Release:** MVP

---

## 5.6 Conversations

### FR-CONV-001

The system shall maintain conversation history for each project.

**Release:** MVP

---

### FR-CONV-002

The system shall use previous exchanges as conversational context.

**Release:** MVP

---

## 5.7 Administration

### FR-ADMIN-001

The system shall provide an administration interface for application management.

**Release:** Production-ready

---

# 6. Non-functional Requirements

## Security

### NFR-SEC-001

All database access shall be read-only.

### NFR-SEC-002

Sensitive credentials shall never be stored in plain text.

### NFR-SEC-003

Generated SQL shall be validated before execution.

---

## Reliability

### NFR-REL-001

The system shall return informative error messages without exposing sensitive information.

### NFR-REL-002

Unexpected failures shall be logged.

---

## Performance

### NFR-PERF-001

The application should return responses within an acceptable time for typical analytical queries.

---

## Maintainability

### NFR-MAIN-001

The application shall follow a modular architecture.

### NFR-MAIN-002

Business logic shall remain independent from infrastructure components.

---

# 7. Engineering Requirements

## Code Quality

### ENG-001

The project shall use automated code formatting.

### ENG-002

The project shall use static analysis tools.

### ENG-003

The project shall use type checking where applicable.

---

## Testing

### ENG-004

Critical business components shall be covered by automated tests.

### ENG-005

The AI query pipeline shall be validated through integration tests.

---

## Containerization

### ENG-006

The application shall be executable using Docker Compose.

---

## CI/CD

### ENG-007

Every pull request shall trigger automated quality checks.

### ENG-008

The default branch shall remain deployable at all times.

---

## Observability

### ENG-009

Application logs shall be structured.

### ENG-010

The application shall expose health check endpoints.

---

## Documentation

### ENG-011

Architecture decisions shall be documented through ADRs.

### ENG-012

Public documentation shall remain synchronized with the implementation.

---

# 8. Requirement Attributes

Each requirement may include the following attributes:

- Identifier
- Title
- Description
- Release
- Priority
- Dependencies
- Verification Method
- Status

These attributes will be progressively completed during the implementation phase.

---

# 9. Traceability Matrix

| Requirement | Use Case | Tests | ADR | Status |
|-------------|----------|-------|-----|--------|
| To be completed during implementation. |
