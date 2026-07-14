# Functional Use Cases

## 1. Purpose

This document describes the main functional use cases of AskMyData from the perspective of its users and external systems.

It focuses on user goals and observable system behavior.

Technical implementation details, internal components and architecture decisions are documented separately.

---

# 2. Actors

## User

An authenticated person using AskMyData to explore structured data.

The MVP primarily targets data professionals, including:

- Data Analysts;
- Data Scientists;
- Analytics Engineers;
- BI Developers;
- Software Engineers.

## Administrator

A platform administrator responsible for managing users and application access.

Administration capabilities are introduced during the Production-ready Portfolio stage.

## External Data Source

A PostgreSQL database containing the structured data explored through AskMyData.

The external data source remains the source of truth.

## LLM Provider

An external AI service used to support intent analysis, query generation and natural language answer generation.

AskMyData must remain independent from any specific provider.

---

# 3. Primary User Journey

The main user journey is:

1. The user authenticates.
2. The user creates and initialize a project.
3. The application discovers the available database structure.
4. The user selects the schemas and tables to expose.
5. The application builds the Knowledge Catalog.
6. The project becomes ready.
7. The user asks questions in natural language.
8. The application generates, validates and executes a read-only query.
9. The user receives a natural language answer.
10. The user continues the conversation or maintains the project.

A project represents the central data exploration workspace. It contains the data source configuration, catalog scope, Knowledge Catalog, conversations, execution history and project settings.

---

# 4. Use Cases

## UC-01 — Authenticate

### Release

MVP

### Primary Actor

User

### Goal

Access AskMyData securely.

### Preconditions

- The user has an active account.
- The account is authorized to access the platform.

### Main Success Scenario

1. The user opens the authentication page.
2. The user enters valid credentials.
3. The application verifies the credentials.
4. The application creates a secure session.
5. The user is redirected to the project list.

### Alternative Flows

#### Invalid credentials

1. The application rejects the authentication attempt.
2. A generic error message is displayed.
3. No sensitive authentication information is exposed.

#### Inactive account

1. The application refuses access.
2. The user is informed that the account is unavailable.

### Success Result

The user can access their projects.

### Related Requirements

- `FR-AUTH-001`
- `FR-AUTH-002`
- `NFR-SEC-002`
- `NFR-REL-001`

---

## UC-02 — Create and Initialize a Project

### Release

MVP

### Primary Actor

User

### Supporting Actor

External Data Source

### Goal

Create a new data exploration project connected to a PostgreSQL database and initialize its Knowledge Catalog.

### Preconditions

- The user is authenticated.

### Main Success Scenario

1. The user requests the creation of a new project.
2. The user enters the project name and an optional description.
3. The application validates the project information.
4. The application creates the project in a draft state.
5. The user selects PostgreSQL as the data source type.
6. The user enters the database connection parameters.
7. The application validates the connection.
8. The application verifies that the configured account has the required read-only permissions.
9. The application discovers the available schemas, tables and relationships.
10. The application displays the discovered database structure.
11. The user selects the schemas and tables that will be included in the project.
12. The application stores the selected catalog scope.
13. The application generates the Knowledge Catalog.
14. The application records the initial schema snapshot.
15. The project status becomes **Ready**.
16. The user is redirected to the project workspace.

### Alternative Flows

#### Invalid project information

1. The application rejects the submitted information.
2. Validation errors are displayed.
3. No project is created.

#### Database unreachable

1. The connection test fails.
2. The application displays a connection error.
3. The user may update the connection parameters and retry.

#### Invalid credentials

1. Authentication to the database fails.
2. The application displays a generic authentication error.
3. Sensitive information is never exposed.

#### Insufficient permissions

1. The application detects that the configured account cannot safely access the database.
2. The configuration is rejected.
3. The user is informed of the required permission level.

#### Schema discovery failure

1. The application records the failure.
2. The project remains in the **Configuring** state.
3. The user may retry after resolving the issue.

#### No objects selected

1. The application prevents the initialization process from continuing.
2. The user is asked to select at least one table.

#### Knowledge Catalog generation failure

1. The application records the failure.
2. The project enters the **Catalog Building Failed** state.
3. The user may retry catalog generation.

### Success Result

A fully initialized project is available for AI-assisted data exploration.

The project contains:

- a validated PostgreSQL data source;
- a defined catalog scope;
- an initialized Knowledge Catalog;
- an initial schema snapshot;
- the **Ready** status.

### Related Requirements

- `FR-PROJ-001`
- `FR-PROJ-002`
- `FR-DATA-001`
- `FR-DATA-002`
- `FR-DATA-003`
- `FR-DATA-004`
- `FR-KCAT-001`
- `FR-KCAT-002`
- `NFR-SEC-001`
- `NFR-SEC-002`
- `NFR-REL-002`

---

## UC-03 — Enrich the Knowledge Catalog

### Release

MVP

### Primary Actor

User

### Goal

Improve the business context used by the AI engine.

### Preconditions

- The user is authenticated.
- The user owns the project.
- The project contains a Knowledge Catalog.

### Main Success Scenario

1. The user opens the Knowledge Catalog.
2. The application displays the selected schemas, tables and columns.
3. The user adds or updates semantic descriptions.
4. The user adds business terms or synonyms.
5. The user may hide objects that should not be exposed to the AI engine.
6. The application validates and stores the semantic metadata.
7. Future questions use the updated catalog context.

### Alternative Flows

#### Invalid metadata

1. The application rejects the submitted value.
2. The existing metadata remains unchanged.

#### Restricted object

1. The user marks an object as unavailable to the AI engine.
2. The object is excluded from future context construction and query generation.

### Success Result

The Knowledge Catalog contains additional business context.

### Related Requirements

- `FR-KCAT-003`
- `FR-AI-002`
- `NFR-SEC-001`

---

## UC-04 — Ask a Question

### Release

Foundation, then MVP integration

### Primary Actor

User

### Supporting Actors

- External Data Source
- LLM Provider

### Goal

Obtain a reliable answer from structured data using natural language.

### Preconditions

- The project is ready.
- The project has a valid data source.
- The project has a usable Knowledge Catalog.
- In the MVP, the user is authenticated and owns the project.

### Main Success Scenario

1. The user enters a natural language question.
2. The application records the user message.
3. The application analyses the intent.
4. The application selects relevant catalog and conversation context.
5. The application creates a query plan.
6. The application generates a read-only SQL query.
7. The application validates the generated SQL.
8. The application executes the validated query.
9. The application validates the returned result.
10. The application generates a natural language answer.
11. The application records the answer and execution metrics.
12. The answer is displayed to the user.

### Alternative Flows

#### Question outside the catalog scope

1. The application determines that the required data is unavailable.
2. No query is executed.
3. The user receives an explanatory response.

#### Forbidden request

1. The application detects a request to modify data or execute a forbidden operation.
2. The request is rejected.
3. No query is executed.

#### Invalid generated SQL

1. SQL validation fails.
2. The application may attempt a controlled regeneration.
3. If validation still fails, the run is marked as failed.
4. No invalid query is executed.

#### Query execution failure

1. The application records the technical error.
2. The user receives a safe error message.
3. Sensitive database details are not exposed.

#### Unusable result

1. The application detects that the result does not support a reliable answer.
2. The user is informed that the question could not be answered reliably.

### Success Result

The user receives an answer supported by a validated read-only database query.

### Related Requirements

- `FR-AI-001`
- `FR-AI-002`
- `FR-AI-003`
- `FR-AI-004`
- `FR-AI-005`
- `FR-AI-006`
- `FR-DATA-004`
- `NFR-SEC-001`
- `NFR-SEC-003`
- `NFR-REL-001`
- `NFR-REL-002`

---

## UC-05 — Clarify a Question

### Release

MVP

### Primary Actor

User

### Goal

Resolve ambiguity before a query is generated or executed.

### Preconditions

- The user has submitted a question.
- The application cannot produce a sufficiently reliable interpretation.

### Main Success Scenario

1. The application identifies the ambiguous elements.
2. The application asks a focused clarification question.
3. The user provides additional information.
4. The clarification is associated with the current question run.
5. The application resumes the query workflow.
6. A validated answer is produced when possible.

### Alternative Flows

#### Clarification remains insufficient

1. The application asks another clarification question or refuses to continue.
2. No query is executed without sufficient confidence.

#### User abandons the clarification

1. The incomplete run remains traceable.
2. No query is executed.

### Success Result

The user's initial request becomes sufficiently precise for controlled execution.

### Related Requirements

- `FR-AI-007`
- `FR-CONV-001`
- `FR-CONV-002`

---

## UC-06 — Continue a Conversation

### Release

MVP

### Primary Actor

User

### Goal

Ask follow-up questions using previous exchanges as context.

### Preconditions

- The project is ready.
- The project contains an active conversation.
- At least one previous exchange exists.

### Main Success Scenario

1. The user opens the project conversation.
2. The application displays previous messages.
3. The user submits a follow-up question.
4. The application selects the relevant recent context.
5. The question is processed through the standard query workflow.
6. The new answer is appended to the conversation.

### Alternative Flows

#### Context is insufficient

1. The application asks the user to restate or clarify the reference.
2. No unsupported assumption is used.

#### Context limit reached

1. The application uses only the configured amount of recent context.
2. Older messages remain visible but are not necessarily sent to the LLM.

### Success Result

The user can explore the data through a contextual sequence of questions.

### Related Requirements

- `FR-CONV-001`
- `FR-CONV-002`
- `FR-AI-007`

---

## UC-07 — Refresh the Knowledge Catalog

### Release

MVP

### Primary Actor

User

### Supporting Actor

External Data Source

### Goal

Synchronize the project with structural changes in the source database.

### Preconditions

- The project is connected to a valid data source.
- The user owns the project.

### Main Success Scenario

1. The user requests a catalog refresh.
2. The application rediscovers the selected database scope.
3. The application creates a new schema snapshot.
4. The application compares the current and previous structures.
5. Compatible semantic metadata is preserved.
6. Removed or changed objects are flagged.
7. The Knowledge Catalog is rebuilt.
8. The project returns to the ready state.

### Alternative Flows

#### Source unavailable

1. The refresh fails.
2. The existing catalog remains available.
3. The failure is recorded.

#### Breaking schema changes

1. The application identifies semantic metadata that can no longer be mapped safely.
2. The affected metadata is flagged for user review.
3. The new catalog is not silently enriched with uncertain mappings.

### Success Result

The project reflects the current structure of the selected source scope.

### Related Requirements

- `FR-KCAT-004`
- `FR-KCAT-001`
- `FR-KCAT-002`
- `NFR-REL-002`

---

## UC-08 — Update Project Information

### Release

MVP

### Primary Actor

User

### Goal

Maintain the descriptive information of a project.

### Preconditions

- The user is authenticated.
- The user owns the project.

### Main Success Scenario

1. The user opens the project settings.
2. The user modifies the name or description.
3. The application validates the changes.
4. The project is updated.

### Alternative Flows

#### Invalid information

1. The changes are rejected.
2. Validation errors are displayed.

### Success Result

The project information reflects the user's changes.

### Related Requirements

- `FR-PROJ-002`

---

## UC-09 — Archive a Project

### Release

MVP

### Primary Actor

User

### Goal

Remove a project from active use without immediately destroying its history.

### Preconditions

- The user is authenticated.
- The user owns the project.

### Main Success Scenario

1. The user requests project archival.
2. The application displays the consequences.
3. The user confirms the operation.
4. The project status becomes archived.
5. New questions are disabled.
6. Sensitive source credentials are removed or made unusable.
7. Existing conversation and execution history remain consultable.

### Alternative Flows

#### User cancels

1. No changes are applied.
2. The project remains active.

### Success Result

The project can no longer execute queries but its historical information remains available.

### Related Requirements

- `FR-PROJ-003`
- `NFR-SEC-002`

---

## UC-10 — Manage Platform Access

### Release

Production-ready Portfolio

### Primary Actor

Administrator

### Goal

Control access to the demonstration platform.

### Preconditions

- The administrator is authenticated.
- The administrator has administrative privileges.

### Main Success Scenario

1. The administrator opens the administration interface.
2. The administrator reviews users and access status.
3. The administrator activates, disables or manages authorized accounts.
4. The application records administrative changes.

### Alternative Flows

#### Unauthorized access attempt

1. The application denies access.
2. The attempt is logged.

### Success Result

Only authorized users can access the platform.

### Related Requirements

- `FR-ADMIN-001`
- `NFR-SEC-001`
- `NFR-REL-002`

---

# 5. Project Lifecycle

A project follows this simplified lifecycle:

```text
Draft
  |
  v
Configuring
  |
  v
Building Catalog
  |
  v
Ready
  |
  +------> Refreshing Catalog ------+
  |                                 |
  +---------------------------------+
  |
  v
Archived
```
### Draft

The project exists but does not yet contain a valid data source.

### Configuring
The data source and catalog scope are being configured.

### Building Catalog
The application is generating or refreshing the Knowledge Catalog.

### Ready
The project can process natural language questions.

### Archived
The project is no longer active and cannot execute new queries.

Failures during configuration or catalog generation are recorded separately and do not constitute permanent lifecycle states.

---

# 6. Future Use Cases

The following use cases are outside the current portfolio roadmap:

- support additional database technologies;
- manage several data sources in one project;
- manage several active conversations per project;
- share projects with other users;
- collaborate within teams;
- export query results;
- generate charts and dashboards;
- schedule catalog refreshes;
- support external authentication providers;
- manage organizations and advanced permissions;
- perform autonomous data analysis;
- modify external data sources.

---

# 7. Global Business Rules

The following rules apply to all use cases:

1. Every active project belongs to exactly one user.
2. Every project contains at most one external data source in the MVP.
3. PostgreSQL is the only supported source in the initial version.
4. A project is ready only after its Knowledge Catalog has been built successfully.
5. Only schemas and tables included in the catalog scope may be exposed to the AI engine.
6. Every external query must be read-only.
7. Every generated SQL query must be validated before execution.
8. Invalid, forbidden or unvalidated SQL must never be executed.
9. The external database remains the source of truth.
10. The Knowledge Catalog provides semantic context but does not modify the source database.
11. Sensitive credentials must never be exposed to users, logs or AI providers.
12. Internal prompts and hidden model reasoning must never be exposed.
13. Failures and rejected executions must remain traceable.
14. A user may access only projects they own.
15. Archived projects cannot execute new questions.
16. The application must not generate an answer presented as reliable when the available data does not support it.
