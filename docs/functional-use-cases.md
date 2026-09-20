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
2. The user creates and initializes a project.
3. The application discovers the available database structure.
4. The user selects the schemas and tables to expose.
5. The application builds the Knowledge Catalog.
6. The project becomes ready.
7. The user may explore the selected data schema and Knowledge Catalog.
8. The user asks questions in natural language.
9. The application generates, validates and executes a read-only query.
10. The user receives a natural language answer.
11. The user continues the current conversation, starts another conversation, or maintains the project.

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
13. The application generates the Knowledge Catalog from the discovered metadata.
14. The application automatically generates semantic descriptions and business synonyms.
15. The application records the initial schema snapshot.
16. The project status becomes **Ready**.
17. The user is redirected to the project workspace.

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

1. The system records the failure.
2. The project does not transition to Ready.
3. The user is informed that the Knowledge Catalog could not be generated.
4. The user may retry the generation after correcting the underlying issue.

### Success Result

A fully initialized project is available for AI-assisted data exploration.

The project contains:

- a validated PostgreSQL data source;
- a defined catalog scope;
- an initialized Knowledge Catalog with automatically generated semantic metadata;
- an initial schema snapshot;
- the **Ready** status.

### Related Requirements

- `FR-PROJ-001`
- `FR-DATA-001`
- `FR-DATA-002`
- `FR-DATA-003`
- `FR-DATA-004`
- `FR-DATA-005`
- `FR-KCAT-001`
- `FR-KCAT-002`
- `FR-KCAT-003`
- `NFR-SEC-001`
- `NFR-SEC-005`
- `NFR-SEC-006`

---

## UC-03 — Explore the Knowledge Catalog

### Release

MVP

### Primary Actor

User

### Goal

Inspect the technical and semantic information available in the Knowledge Catalog.

### Preconditions

- The user is authenticated.
- The user owns the project.
- The project is ready.

### Main Success Scenario

1. The user opens the Knowledge Catalog.
2. The application displays the catalog status and version.
3. The application displays the selected database objects and their technical metadata.
4. The application displays automatically generated semantic descriptions and business synonyms when available.
5. The user browses the catalog information.

### Success Result

The user can inspect the technical and semantic context used by the AI Query Engine.

### Related Requirements

- `FR-KCAT-002`
- `FR-KCAT-003`
- `FR-AI-002`

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
- In the MVP, a conversation is selected.

### Main Success Scenario

1. The user enters a natural language question.
2. In the MVP, the application records the user message in the selected conversation.
3. The application analyses the intent.
4. The application selects relevant catalog context and, in the MVP, relevant conversation context.
5. The application creates a query plan.
6. The application generates a read-only SQL query.
7. The application validates the generated SQL.
8. The application executes the validated query.
9. The application validates the returned result.
10. The application generates a natural language answer.
11. The application records execution metrics and traces and, in the MVP, records the answer in the selected conversation.
12. The answer is displayed to the user.

### Alternative Flows

#### Ambiguous question

1. The application determines that the question requires clarification.
2. The application follows UC-05 — Clarify a Question before continuing the query workflow.
3. No SQL query is generated or executed until the question is sufficiently precise.

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
- `FR-AI-007`
- `FR-AI-008`
- `FR-DATA-004`
- `NFR-SEC-001`
- `NFR-SEC-003`
- `NFR-REL-001`
- `NFR-REL-002`
- `NFR-REL-003`
- `NFR-REL-004`

---

## UC-05 — Clarify a Question

### Release

MVP

### Primary Actor

User

### Goal

Resolve ambiguity before a query is generated or executed.

### Preconditions

- The project is ready.
- The user owns the project.
- A conversation is selected.
- The user has submitted a question that requires clarification.

### Main Success Scenario

1. The application identifies the ambiguous elements.
2. The application asks a focused clarification question.
3. The user provides additional information.
4. The clarification is associated with the current question run.
5. Once the question is sufficiently precise, the application resumes the standard query workflow defined in UC-04.

### Alternative Flows

#### Clarification remains insufficient

1. The application asks another clarification question or refuses to continue.
2. No query is executed without sufficient confidence.

#### User abandons the clarification

1. The incomplete run remains traceable.
2. No query is executed.

### Success Result

The user's initial request is sufficiently precise for the standard query workflow to resume.

### Related Requirements

- `FR-AI-008`
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
- The user owns the project.
- A conversation is selected.
- At least one previous exchange exists in the selected conversation.

### Main Success Scenario

1. The application displays the messages from the selected conversation.
2. The user submits a follow-up question.
3. The application selects the relevant recent context from the selected conversation.
4. The question is processed through the standard query workflow.
5. The new answer is appended to the selected conversation.

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
- `FR-CONV-003`
- `FR-AI-008`

---

## UC-07 — Manage Conversations

### Release

MVP

### Primary Actor

User

### Goal

Create and access conversations within a project.

### Preconditions

- The user is authenticated.
- The user owns the project.
- The project is ready.

### Main Success Scenario

1. The user opens the Conversations section of a project.
2. The application displays the existing conversations for the project.
3. The user selects an existing conversation.
4. The application displays its persistent message history.

### Alternative Flows

#### Create a new conversation

1. The user requests a new conversation.
2. The application creates a conversation associated with the current project.
3. The new conversation becomes the selected conversation and is available for question answering.

#### No existing conversations

1. The application displays an empty conversation state.
2. The user may create the first conversation by following the new conversation flow.

### Success Result

The user can create multiple conversations and access the persistent history of each conversation within the project.

### Related Requirements

- `FR-CONV-001`
- `FR-CONV-003`

---

## UC-08 — Regenerate the Knowledge Catalog

### Release

MVP

### Primary Actor

User

### Supporting Actor

External Data Source

### Goal

Regenerate the Knowledge Catalog from the current structure of the selected source scope.

### Preconditions

- The user is authenticated.
- The user owns the project.
- The project is ready.
- The project is connected to a valid data source.

### Main Success Scenario

1. The user requests a catalog regeneration.
2. The application rediscovers the current database structure within the selected Catalog Scope.
3. The application records a new schema snapshot.
4. The application regenerates the Knowledge Catalog from the current source schema.
5. The application automatically generates the associated semantic descriptions and business synonyms.
6. The project returns to the Ready state.

### Alternative Flows

#### Source unavailable

1. The regeneration fails.
2. The existing Knowledge Catalog remains unchanged.
3. The failure is recorded.
4. The project returns to the Ready state.
5. The user is informed that the Knowledge Catalog could not be regenerated.

### Success Result

The Knowledge Catalog reflects the current database structure within the project's selected Catalog Scope.

### Related Requirements

- `FR-KCAT-001`
- `FR-KCAT-002`
- `FR-KCAT-003`
- `FR-KCAT-004`
- `NFR-REL-002`
- `NFR-REL-003`

---

## UC-09 — Update Project Information

### Release

MVP

### Primary Actor

User

### Goal

Maintain the descriptive information of a project.

### Preconditions

- The user is authenticated.
- The user owns the project.
- The project is not archived.

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

## UC-10 — Archive a Project

### Release

MVP

### Primary Actor

User

### Goal

Remove a project from active use without immediately destroying its history.

### Preconditions

- The user is authenticated.
- The user owns the project.
- The project is not archived.

### Main Success Scenario

1. The user requests project archival.
2. The application displays the consequences.
3. The user confirms the operation.
4. The project status becomes archived.
5. New questions and external database access are disabled for the project.
6. Existing conversation and execution history remain consultable.

### Alternative Flows

#### User cancels

1. No changes are applied.
2. The project remains active.

### Success Result

The project becomes inactive and can no longer access the external data source or execute new queries, while its existing project information and history remain available for consultation.

### Related Requirements

- `FR-PROJ-003`
- `FR-CONV-003`

---

## UC-11 — Manage Platform Access

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

---

## UC-12 — Explore the Data Schema

### Release
MVP

### Primary Actor
User

### Goal
Inspect the database structure available within the project's Catalog Scope.

### Preconditions
- The user is authenticated.
- The user owns the project.
- The project is ready.

### Main Success Scenario
1. The user opens the Data section of the project.
2. The application displays the schemas and tables included in the Catalog Scope.
3. The user selects a table.
4. The application displays its columns and their structural information, including data types when available.
5. The application displays known relationships with other selected tables when available.
6. The user navigates between the available database objects.

### Alternative Flows

#### Schema information unavailable
1. The application cannot retrieve or display the schema information.
2. The user receives a safe error message.
3. The failure is recorded.

### Success Result
The user can inspect the database structure available for exploration within the project.

### Related Requirements
- `FR-DATA-006`
- `NFR-REL-001`

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
  +------> Regenerating Catalog ----+
  |                                 |
  +---------------------------------+
  |
  v
Archived
```

A project may be archived only from the Ready state. Projects that have not completed setup may be deleted, while a project undergoing catalog regeneration cannot be archived until the operation completes.

### Draft

The project exists but does not yet contain a valid data source.

### Configuring
The data source and catalog scope are being configured.

### Building Catalog
The application is generating the initial Knowledge Catalog.

### Regenerating Catalog

The application is regenerating the Knowledge Catalog from the current source schema. The project returns to Ready when the regeneration completes successfully.

### Ready
The project can process natural language questions.

### Archived
The project is no longer active and cannot execute new queries.

Failures during configuration, initial catalog generation or catalog regeneration are handled without introducing additional permanent project lifecycle states.

---

# 6. Future Use Cases

The following use cases are outside the current portfolio roadmap:

- support additional database technologies;
- manage several data sources in one project;
- share projects with other users;
- collaborate within teams;
- export query results;
- generate charts and dashboards;
- schedule catalog regenerations;
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
5. A project may contain multiple conversations, each with its own persistent message history.
6. Conversation context must be isolated between conversations within the same project.
7. Only schemas and tables included in the catalog scope may be exposed to the AI engine.
8. Regenerating the Knowledge Catalog must preserve the project's Catalog Scope unless the user explicitly changes that scope.
9. Every external query must be read-only.
10. Every generated SQL query must be validated before execution.
11. Invalid, forbidden or unvalidated SQL must never be executed.
12. The external database remains the source of truth.
13. The Knowledge Catalog provides semantic context but does not modify the source database.
14. Sensitive credentials must never be exposed in logs, application responses or data sent to AI providers.
15. Internal prompts and hidden model reasoning must never be exposed.
16. Failures and rejected executions must remain traceable.
17. A user may access only projects they own.
18. Archived projects cannot execute new questions.
19. The application must not generate an answer presented as reliable when the available data does not support it.
