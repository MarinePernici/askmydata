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

### FR-DATA-005

The system shall allow users to select the schemas and tables included in the project Catalog Scope.

**Release:** MVP

---

### FR-DATA-006

The system shall allow users to explore the selected database schema, including tables, columns and relationships.

**Release:** MVP

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

The system shall automatically generate semantic descriptions and business synonyms to enrich the Knowledge Catalog.

**Release:** MVP

---

### FR-KCAT-004

The system shall allow the Knowledge Catalog to be regenerated from the current source schema.

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

The system shall validate query results before generating a natural language answer.

**Release:** Foundation

---

### FR-AI-008

The system shall request clarification when a question is ambiguous.

**Release:** MVP

---

### FR-AI-009

The system shall generate natural language answers in the language used by the user for the current question.

**Release:** Production-ready Portfolio

---

## 5.6 Conversations

### FR-CONV-001

The system shall allow multiple conversations to be created and maintained within each project.

**Release:** MVP

---

### FR-CONV-002

The system shall use previous exchanges as conversational context.

Failed question-and-answer exchanges shall be excluded from the context provided to the AI Query Engine, while remaining accessible in the conversation history.

**Release:** MVP

---

### FR-CONV-003

The system shall allow users to access the persistent conversation history of each project.

The history shall preserve user questions and assistant messages associated with failed Question Runs, including safe explanatory error messages.

**Release:** MVP

---

## 5.7 User Preferences

### FR-USER-001

The system shall allow users to use the application interface in French or English.

**Release:** Production-ready Portfolio

---

## 5.8 Administration

### FR-ADMIN-001

The system shall provide an administration interface for application management.

**Release:** Production-ready Portfolio

---

### FR-ADMIN-002

The system shall allow administrators to create, review and revoke invitations granting access to the public demonstration platform.

**Release:** Production-ready Portfolio

---

### FR-ADMIN-003

The system shall allow a person holding a valid invitation to create an individual user account.

**Release:** Production-ready Portfolio

---

## 5.9 Public Demo

### FR-DEMO-001

The public demonstration shall allow users to select a data source from a predefined set of demonstration PostgreSQL databases.

**Release:** Production-ready Portfolio

---

### FR-DEMO-002

The public demonstration shall prevent users from configuring arbitrary external database connections.

**Release:** Production-ready Portfolio

---

### FR-DEMO-003

After selecting a demonstration data source, users shall continue through the standard project initialization workflow, including Catalog Scope selection and Knowledge Catalog generation.

**Release:** Production-ready Portfolio

---

# 6. Non-functional Requirements

## Security

### NFR-SEC-001

All database access shall be read-only.

**Release:** Foundation

### NFR-SEC-002

Sensitive application secrets and credentials shall never be stored in plain text.

**Release:** MVP

### NFR-SEC-003

Generated SQL shall be validated before execution.

**Release:** Foundation

### NFR-SEC-004

The system shall restrict access to projects and their associated data to their owner.

**Release:** MVP

### NFR-SEC-005

Data source credentials shall be encrypted at rest and shall never be exposed in application logs or user-facing responses.

**Release:** MVP

### NFR-SEC-006

External PostgreSQL connections shall use database accounts restricted to read-only permissions.

**Release:** Foundation

---

## Reliability

### NFR-REL-001

The system shall return informative error messages without exposing sensitive information.

Technical failures shall be presented through safe, user-facing messages. In the conversational interface, technical errors shall also trigger a dismissible error dialog without removing the corresponding message from the persistent history.

**Release:** MVP

### NFR-REL-002

Unexpected failures shall be logged.

**Release:** Foundation

### NFR-REL-003

The system shall handle AI query pipeline failures gracefully and shall not present failed or incomplete results as valid answers.

The system shall distinguish successful answers, clarification requests, requests that cannot be answered, and technical failures through appropriate user-facing feedback.

Failed Question Runs shall remain traceable, and their user-visible error messages shall not expose raw infrastructure exceptions or sensitive database details.

**Release:** MVP

### NFR-REL-004

The system shall maintain execution traces for each question run, including the status of the main AI query pipeline steps.

**Release:** Foundation

---

## Performance

### NFR-PERF-001

The application shall return responses within an acceptable time for typical analytical queries.

**Release:** MVP

### NFR-PERF-002

The system shall enforce configurable execution timeouts and maximum row limits for generated SQL queries.

**Release:** MVP

---

## Usability

### NFR-USA-001

The application shall adapt its layout to different desktop screen sizes while remaining usable and preserving access to all core features.

**Release:** MVP

---

## Maintainability

### NFR-MAIN-001

The application shall follow a modular architecture.

**Release:** MVP

### NFR-MAIN-002

Business logic shall remain independent from infrastructure components.

**Release:** MVP

---

## Resource Protection

### NFR-RES-001

The public demonstration shall enforce configurable usage limits to prevent abusive or excessive consumption of application and AI resources.

**Release:** Production-ready Portfolio

---

# 7. Engineering Requirements

## Code Quality

### ENG-001

The project shall use automated code formatting.

**Release:** MVP

### ENG-002

The project shall use static analysis tools.

**Release:** Production-ready Portfolio

### ENG-003

The project shall use type checking where applicable.

**Release:** Production-ready Portfolio

---

## Testing

### ENG-004

Critical features shall have automated tests.

**Release:** MVP

### ENG-005

The AI query pipeline shall be validated through integration tests.

**Release:** MVP

---

## Containerization

### ENG-006

The application shall be runnable locally using Docker Compose.

**Release:** MVP

---

## CI/CD

### ENG-007

Pull requests shall run automated quality checks.

**Release:** Production-ready Portfolio

### ENG-008

The default branch shall remain deployable.

**Release:** Production-ready Portfolio

---

## Observability

### ENG-009

The application shall produce structured logs and provide traceability across critical application and AI query pipeline operations.

**Release:** Production-ready Portfolio

### ENG-010

The application shall expose public health checks for deployment and operational monitoring:

- a liveness check confirming that the application process can respond without depending on external services;
- a readiness check confirming that the application can access its internal database.

Health-check responses shall not expose database credentials, connection information, or internal exception details.

**Release:** Production-ready Portfolio

---

## Documentation

### ENG-011

Major architectural decisions shall be documented using Architecture Decision Records.

**Release:** MVP

### ENG-012

Documentation shall remain synchronized with the implementation.

**Release:** MVP

---

### ENG-013

The application shall expose operational metrics for critical application and AI query pipeline operations.

**Release:** Production-ready Portfolio

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

| Requirement | Use Case | Verification | ADR | Status |
|-------------|----------|--------------|-----|--------|
| FR-AUTH-001–002 | UC-01 | Authentication tests | ADR-0001 | Implemented |
| FR-PROJ-001–003 | UC-02, UC-09, UC-10 | Project service and view tests | ADR-0001 | Implemented |
| FR-DATA-001–006 | UC-02, UC-12 | Data source, PostgreSQL connector and schema tests | ADR-0002 | Implemented |
| FR-KCAT-001–004 | UC-02, UC-03, UC-08 | Catalog service and view tests | ADR-0003 | Implemented |
| FR-AI-001–008 | UC-04, UC-05 | Query engine and pipeline integration tests | ADR-0003, ADR-0004 | Implemented |
| FR-AI-009 | UC-04 | — | — | Production-ready scope |
| FR-CONV-001–003 | UC-04, UC-06, UC-07 | Conversation and question-run tests | ADR-0001 | Implemented |
| FR-USER-001 | — | — | — | Production-ready scope |
| FR-ADMIN-001–003 | UC-11 | — | — | Production-ready scope |
| FR-DEMO-001–003 | UC-02 | — | — | Production-ready scope |
| NFR-SEC-001–006 | UC-02, UC-04, UC-10 | Security, connector, SQL validation and pipeline tests | ADR-0002, ADR-0004 | Implemented |
| NFR-REL-001–004 | UC-04, UC-05, UC-08 | Failure-handling and execution-trace tests | ADR-0001, ADR-0004 | Implemented |
| NFR-PERF-001–002 | UC-04 | Query executor and integration tests | ADR-0004 | Implemented |
| NFR-RES-001 | UC-04 | — | — | Production-ready scope |
| NFR-USA-001 | UC-01–UC-12 | Responsive UI verification | — | Implemented |
| NFR-MAIN-001–002 | UC-01–UC-12 | Architecture review and automated tests | ADR-0001 | Implemented |
| ENG-001 | — | Ruff formatting verification | — | Implemented |
| ENG-002–003 | — | — | — | Production-ready scope |
| ENG-004–005 | — | Automated and pipeline integration test suites | — | Implemented |
| ENG-006 | — | Docker Compose validation | — | Implemented |
| ENG-007–010 | — | — | — | Production-ready scope |
| ENG-011 | — | ADR review | ADR-0001–ADR-0004 | Implemented |
| ENG-012 | — | Documentation-to-implementation audit | ADR-0001–ADR-0004 | Implemented |
| ENG-013 | — | — | — | Production-ready scope |
