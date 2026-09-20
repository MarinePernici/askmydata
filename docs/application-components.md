# Application Components

## 1. Purpose

This document describes the main application components of AskMyData, their responsibilities, boundaries and dependencies.

It defines the logical organization of the application without prescribing detailed implementation classes or database models.

AskMyData initially follows a **modular monolith architecture** implemented with Django.

The AI query engine remains an internal module during the Foundation and MVP stages. Its boundaries are designed so that it may later be extracted into a dedicated FastAPI service if operational requirements justify it.

---

## 2. Architectural Style

AskMyData is organized as a modular monolith.

The application is deployed as a single Django application, but its business capabilities are separated into explicit modules.

```text
AskMyData
├── Accounts
├── Projects
├── Catalog
├── Conversations
├── Query Engine
├── Connectors
├── Observability
└── Shared Kernel
```

Each module:

* owns a defined business responsibility;
* exposes explicit application services;
* avoids direct access to another module's internal implementation;
* may depend on shared abstractions;
* remains testable independently;
* may later be extracted if necessary.

---

## 3. Architectural Principles

### Modular boundaries

Each component owns a cohesive part of the domain.

Modules should communicate through:

* application services;
* domain interfaces;
* explicit data contracts;
* domain events when justified.

Modules should not depend on another module's private models, repositories or internal utilities.

### Domain independence

Core business logic should not depend directly on:

* Django views;
* HTTP requests;
* ORM-specific behavior;
* LLM SDKs;
* PostgreSQL drivers;
* monitoring providers.

Infrastructure-specific implementations must remain behind interfaces.

### Dependency direction

Dependencies point toward the domain and application layers.

```text
Presentation
     |
     v
Application Services
     |
     v
Domain
     ^
     |
Infrastructure Implementations
```

### Incremental evolution

The initial implementation remains a single deployable application.

FastAPI, asynchronous workers or additional infrastructure services are introduced only when a concrete need appears.

---

## 4. High-Level Components

```text
User
  |
  v
Web Interface
  |
  v
Django Application
  |
  +--------------------+
  |                    |
  v                    v
Project Management   Conversation Management
  |                    |
  +---------+----------+
            |
            v
      Query Engine
            |
      +-----+------+
      |            |
      v            v
Knowledge Catalog  Connector
                       |
                       v
                  PostgreSQL
            |
            v
        LLM Provider
```

The diagram is conceptual. Internal calls occur inside the Django application during the initial architecture.

---

## 5. Presentation Layer

## Web Interface

### Definition

Provides the user-facing web interface of AskMyData.

The initial interface is rendered by Django using server-side templates and standard web technologies.

### Responsibilities

* display authentication pages;
* display project lists and project details;
* guide users through project initialization;
* display catalog information;
* provide the conversational exploration interface;
* display simplified execution states;
* display validation and business errors;
* submit user actions to application services.

### Does Not

* execute SQL;
* access external databases directly;
* build LLM prompts;
* validate generated queries;
* implement domain rules;
* call LLM providers directly.

### Dependencies

* Accounts application services;
* Project application services;
* Catalog application services;
* Conversation application services;
* Query Engine application services.

### Initial Technology

* Django views;
* Django templates;
* HTML;
* CSS;
* limited JavaScript when required.

---

## Administration Interface

### Definition

Provides restricted administrative capabilities through Django Admin.

### Responsibilities

* manage application users;
* manage invitations when enabled;
* inspect projects;
* inspect failed executions;
* support demonstration platform operations.

### Does Not

* expose source credentials;
* expose hidden prompts;
* expose hidden model reasoning;
* replace operational monitoring tools.

### Release

Production-ready Portfolio.

---

## 6. Accounts Component

### Definition

Manages user identity, authentication and access to the application.

### Responsibilities

* authenticate users;
* create and terminate sessions;
* activate and deactivate accounts;
* enforce account-level access rules;
* manage user preferences when enabled;
* support invitation-based registration when enabled.

### Domain Concepts

* User;
* UserPreferences;
* Invitation.

### Application Services

Examples:

* `AuthenticateUser`
* `LogoutUser`
* `GetCurrentUser`
* `UpdateUserPreferences`
* `CreateInvitation`
* `AcceptInvitation`
* `DeactivateUser`

### Interfaces Exposed

* authentication service;
* current-user access service;
* user authorization checks.

### Dependencies

* Django authentication infrastructure;
* application database;
* email delivery infrastructure when invitations are enabled.

### Does Not

* manage projects;
* access external data sources;
* execute AI queries;
* store external database credentials.

---

## 7. Projects Component

### Definition

Manages the lifecycle of data exploration projects.

`Project` is the central aggregate root of AskMyData.

### Responsibilities

* create projects;
* update project information;
* manage project lifecycle;
* coordinate project initialization;
* determine whether a project is ready;
* archive projects;
* enforce project ownership.

### Domain Concepts

* Project.

### Application Services

Examples:

* `CreateProject`
* `UpdateProject`
* `GetProject`
* `ListUserProjects`
* `StartProjectConfiguration`
* `MarkProjectReady`
* `ArchiveProject`

### Interfaces Exposed

* project retrieval;
* ownership validation;
* project lifecycle transitions;
* project readiness checks.

### Dependencies

* Accounts component;
* Data Source Management;
* Catalog component;
* Conversation component.

### Business Boundary

The Projects component coordinates the project lifecycle but does not implement:

* schema discovery;
* catalog construction;
* query generation;
* SQL execution;
* conversation processing.

---

## 8. Data Source Management

### Definition

Manages the configuration and validation of external data sources associated with projects.

This capability may initially live inside the Projects module or as a dedicated Django application depending on implementation size.

### Responsibilities

* register a data source;
* validate connection parameters;
* test connectivity;
* verify required permissions;
* encrypt connection configuration;
* update connection status;
* prevent use of source credentials while a project is archived.

### Domain Concepts

* DataSource.

### Application Services

Examples:

* `ConfigureDataSource`
* `TestDataSourceConnection`
* `ValidateReadOnlyPermissions`
* `GetDataSourceStatus`

### Interfaces Exposed

* connection configuration service;
* connection validation service;
* encrypted credential retrieval for authorized infrastructure services.

### Dependencies

* Projects component;
* Connector abstraction;
* encryption service;
* application database.

### Does Not

* discover schemas directly;
* execute user-generated queries;
* build the Knowledge Catalog;
* expose credentials to presentation components.

---

## 9. Catalog Component

### Definition

Manages the semantic representation of the connected data source.

The Catalog component provides the contextual knowledge used by the Query Engine.

### Responsibilities

* manage the catalog scope;
* discover selected database metadata;
* build the Knowledge Catalog;
* regenerate the Knowledge Catalog;
* create schema snapshots;
* generate and store semantic metadata automatically;
* provide catalog context to the Query Engine.

### Domain Concepts

* CatalogScope;
* KnowledgeCatalog;
* SchemaSnapshot;
* SemanticMetadata.

### Application Services

Examples:

* `DefineCatalogScope`
* `BuildKnowledgeCatalog`
* `RegenerateKnowledgeCatalog`
* `GetKnowledgeCatalog`
* `GetCatalogContext`

### Interfaces Exposed

* catalog construction and regeneration service;
* catalog query service;
* contextual catalog retrieval.

### Dependencies

* Projects component;
* Data Source Management;
* Connector abstraction;
* application database.

### Does Not

* execute user questions;
* generate SQL;
* call the LLM provider directly;
* modify the external database.

---

## 10. Conversation Component

### Definition

Manages conversations and user-visible messages associated with projects.

### Responsibilities

* create project conversations;
* list and retrieve project conversations;
* store ordered messages;
* retrieve conversation history;
* append user and assistant messages;
* provide limited contextual history for the selected conversation;
* archive conversations with projects.

### Domain Concepts

* Conversation;
* Message.

### Application Services

Examples:

* `ListProjectConversations`
* `GetConversation`
* `CreateProjectConversation`
* `AppendUserMessage`
* `AppendAssistantMessage`
* `GetConversationContext`
* `ArchiveConversation`

### Interfaces Exposed

* project conversation listing and retrieval;
* conversation history retrieval;
* message creation;
* contextual history selection for a specific conversation.

### Dependencies

* Projects component;
* application database.

### Does Not

* interpret user questions;
* generate SQL;
* execute queries;
* store hidden model reasoning.

---

## 11. Query Engine Component

### Definition

Coordinates the complete AI-assisted question-answering workflow.

The Query Engine is an internal application module in the initial modular monolith.

It is designed behind explicit interfaces so it can later be extracted into a dedicated service if required.

### Responsibilities

* create and manage Question Runs;
* analyse user intent;
* determine whether clarification is required;
* build contextual input;
* create a query plan;
* generate SQL;
* validate SQL;
* execute approved queries;
* validate results;
* generate natural language answers;
* record execution traces;
* expose execution metadata for observability when required.

### Domain Concepts

* QuestionRun;
* ExecutionTrace.

### Application Services

Examples:

* `SubmitQuestion`
* `ContinueQuestionRun`
* `RejectQuestionRun`
* `GetQuestionRunStatus`
* `GetQuestionRunResult`

### Internal Services

* Question Orchestrator;
* Intent Analyzer;
* Context Builder;
* Query Planner;
* Query Generator;
* Query Validator;
* Query Executor;
* Result Validator;
* Answer Generator.

### Dependencies

* Projects component;
* Catalog component;
* Conversation component;
* Connector abstraction;
* LLM Provider abstraction;
* Observability component;
* application database.

### Does Not

* manage user authentication;
* own project lifecycle;
* expose source credentials;
* bypass query validation;
* modify external data sources.

---

## 12. Question Orchestrator

### Definition

Coordinates one Question Run from initial input to final outcome.

### Responsibilities

* initialize the run;
* call specialized services in the required order;
* manage state transitions;
* handle clarification;
* stop execution when validation fails;
* persist the final result;
* record failures and rejection reasons.

### Typical Workflow

```text
Receive Question
      |
      v
Analyse Intent
      |
      +------> Request Clarification
      |
      v
Build Context
      |
      v
Create Query Plan
      |
      v
Generate SQL
      |
      v
Validate SQL
      |
      +------> Reject
      |
      v
Execute Query
      |
      v
Validate Result
      |
      v
Generate Answer
      |
      v
Complete Run
```

### Does Not

* implement connector-specific logic;
* implement LLM-provider-specific calls;
* directly render responses to the user.

---

## 13. Intent Analyzer

### Definition

Determines whether the user request is understandable, permitted and sufficiently precise.

### Responsibilities

* identify the apparent user intent;
* detect ambiguity;
* detect requests outside the catalog scope;
* detect prohibited modification requests;
* determine whether clarification is required.

### Inputs

* user question;
* project context;
* catalog summary;
* recent context from the selected conversation, when applicable.

### Outputs

A structured result containing:

* interpreted intent;
* required clarification;
* scope assessment;
* rejection reason when applicable.

### Dependencies

* Catalog query interface;
* LLM Provider abstraction when required.

---

## 14. Context Builder

### Definition

Builds the minimal relevant context required for question processing.

### Responsibilities

* retrieve relevant technical metadata;
* retrieve semantic metadata;
* select recent messages from the selected conversation;
* exclude restricted catalog objects;
* limit context size.

### Inputs

* project;
* user question;
* current catalog;
* selected conversation, when applicable.

### Outputs

A structured context object used by downstream query services.

### Does Not

* generate SQL;
* execute queries;
* expose credentials;
* include objects outside the Catalog Scope.

---

## 15. Query Planner

### Definition

Creates a structured execution plan for answering a question.

### Responsibilities

* identify relevant tables and fields;
* identify required joins;
* determine filters and aggregations;
* define the expected result shape;
* prepare query generation.

### Outputs

A provider-independent query plan.

### Dependencies

* contextual catalog information;
* LLM Provider abstraction when required.

---

## 16. Query Generator

### Definition

Generates source-specific SQL from an approved query plan.

### Responsibilities

* generate PostgreSQL-compatible SQL;
* generate read-only statements;
* respect the Catalog Scope;
* return structured generation metadata.

### Dependencies

* Query Plan;
* Connector capabilities;
* LLM Provider abstraction.

### Does Not

* execute SQL;
* decide whether SQL is safe;
* modify the external database.

---

## 17. Query Validator

### Definition

Validates generated SQL before execution.

### Responsibilities

* parse generated SQL;
* verify that the statement is read-only;
* reject prohibited statements;
* verify referenced schemas and tables;
* enforce catalog boundaries;
* reject multiple statements when unsupported.

### Validation Layers

The initial implementation should combine:

1. structural SQL parsing;
2. explicit allowlists and denylists;
3. Catalog Scope verification;
4. read-only database permissions.

Execution limits, including query timeouts and maximum result row counts, are enforced by the Query Executor.

Prompt instructions alone are never considered a sufficient security control.

### Outputs

* approved query;
* rejected query with structured reason.

### Does Not

* rewrite unsafe queries silently;
* execute unvalidated SQL.

---

## 18. Query Executor

### Definition

Executes validated SQL against the configured external data source.

### Responsibilities

* receive an approved query;
* obtain an authorized connection;
* apply execution timeout;
* enforce result row limits;
* execute through the Connector abstraction;
* return structured results;
* record execution metadata.

### Dependencies

* Connector abstraction;
* authorized Data Source configuration;
* Observability component.

### Does Not

* accept unvalidated SQL;
* expose raw credentials;
* modify source data.

---

## 19. Result Validator

### Definition

Determines whether query results can support a reliable response.

### Responsibilities

* detect execution errors;
* detect empty results;
* detect truncated results;
* verify expected result structure;
* identify insufficient evidence;
* provide limitations to the Answer Generator.

### Outputs

* validated result;
* result limitations;
* failure or insufficiency reason.

---

## 20. Answer Generator

### Definition

Produces a natural language response grounded in validated query results.

### Responsibilities

* summarize the result;
* generate a clear natural language answer;
* report relevant limitations;
* avoid unsupported claims;
* produce a user-visible response.

### Inputs

* original question;
* validated result;
* query plan;
* relevant catalog context;
* result limitations.

### Does Not

* expose hidden prompts;
* expose hidden reasoning;
* invent information not supported by the result.

---

## 21. Connectors Component

### Definition

Provides a common abstraction for interacting with external structured data sources.

The Foundation and MVP implement only the PostgreSQL Connector.

### Responsibilities

* test connections;
* inspect source capabilities;
* retrieve schema metadata;
* execute validated read-only queries;
* normalize connector responses and errors.

### Connector Interface

The abstraction should expose capabilities equivalent to:

```text
test_connection()
validate_permissions()
discover_schema(scope=None)
execute_read_only(query, limits)
```

The exact Python interface will be defined during implementation.

### Does Not

* contain business rules;
* generate SQL;
* select catalog scope;
* call LLM providers;
* manage conversations.

---

## 22. PostgreSQL Connector

### Definition

Implements the Connector abstraction for PostgreSQL.

### Responsibilities

* establish PostgreSQL connections;
* validate connectivity;
* verify read-only permissions;
* retrieve schema metadata;
* execute approved SQL;
* map PostgreSQL errors into application errors.

### Dependencies

* PostgreSQL driver;
* SQLAlchemy Core or equivalent database toolkit;
* encrypted connection configuration.

### Security Requirements

* use a dedicated read-only database account;
* support connection timeout configuration when introduced;
* avoid exposing connection strings;
* close connections safely;
* never execute unvalidated statements.

---

## 23. LLM Provider Component

### Definition

Provides a provider-independent interface for model inference.

### Responsibilities

* send structured model requests;
* return structured responses;
* expose provider metadata when available;
* expose provider errors;
* support provider-specific reliability configuration when introduced.

Provider metadata may include token usage, model information and latency. Its persistence and monitoring are handled by the Observability component when enabled.

### Provider Interface

The abstraction may expose separate capabilities for:

* intent analysis;
* planning;
* SQL generation;
* answer generation.

### Does Not

* access source credentials;
* execute SQL;
* define business rules;
* persist user conversations directly.

### Initial Implementation

One provider and one supported model configuration are sufficient for the Foundation and MVP.

The domain and application services must not depend directly on a provider SDK.

---

## 24. Observability Component

### Definition

Provides logging, metrics and diagnostic capabilities across the application.

### Responsibilities

#### Foundation

* record execution traces;
* record execution durations;
* record normalized execution errors;
* correlate traces with Question Run identifiers.

#### Production-ready Portfolio

* produce structured application logs;
* correlate logs with Project and Question Run identifiers;
* record LLM usage metrics;
* expose health information;
* support monitoring integrations.

### Data That May Be Recorded

* Question Run identifier;
* processing step;
* duration;
* model name;
* token usage;
* estimated cost;
* result row count;
* normalized error code.

### Data That Must Not Be Recorded

* database passwords;
* complete connection strings;
* secret keys;
* hidden prompts;
* hidden model reasoning;
* unrestricted query results;
* sensitive source data.

### Release

Basic traces in Foundation; enriched monitoring in Production-ready Portfolio.

---

## 25. Shared Kernel

### Definition

Contains a minimal set of abstractions and utilities shared by several modules.

### Possible Responsibilities

* common identifiers;
* shared exceptions;
* clock abstraction;
* encryption interface;
* pagination contracts;
* common result types;
* domain event base classes.

### Rules

* The Shared Kernel must remain small.
* Business logic must not be moved into generic utility modules.
* A concept belongs in the Shared Kernel only when several modules genuinely depend on it.
* Module-specific helpers remain inside their owning module.

---

## 26. Persistence Component

### Definition

Provides persistence for AskMyData application data.

This database is separate from the external source database explored by users.

### Stored Data

* users;
* projects;
* encrypted data source configurations;
* catalog scopes;
* schema snapshots;
* semantic metadata;
* conversations;
* messages;
* question runs;
* execution traces.

### Responsibilities

* persist domain entities;
* enforce data integrity;
* support transactions;
* apply schema migrations;
* provide repositories through Django ORM.

### Does Not

* store external source data as a replacement for the source database;
* store plain-text credentials;
* act as the database queried by the AI engine unless used explicitly as a demonstration source.

---

## 27. Application Database

### Initial Technology

* PostgreSQL.

### Distinction Between Databases

AskMyData uses two conceptually different database roles:

### Application Database

Stores data required to operate AskMyData.

Examples:

* accounts;
* projects;
* conversations;
* catalog metadata;
* execution history.

### External Data Source

Contains the business data explored through natural language.

The two roles must remain clearly separated even when both use PostgreSQL during local development.

---

## 28. Component Dependencies

The following dependency rules apply:

```text
Web Interface
    |
    v
Application Services
    |
    +-------------------------+
    |                         |
    v                         v
Domain Model             Domain Interfaces
                              ^
                              |
                    Infrastructure Adapters
```

### Allowed Dependencies

* Presentation may depend on application services.
* Application services may depend on domain entities and interfaces.
* Domain services may depend on domain abstractions.
* Infrastructure implementations may depend on external libraries.
* Infrastructure adapters implement interfaces defined closer to the domain.

### Forbidden Dependencies

* Domain entities must not import Django views.
* Domain services must not depend directly on provider SDKs.
* Catalog logic must not depend on HTTP.
* Query generation must not execute SQL.
* Connectors must not contain user-interface logic.
* Presentation must not access databases directly.

---

## 29. Proposed Django Module Structure

The initial codebase may follow this organization:

```text
askmydata/
├── config/
│   ├── settings/
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   ├── accounts/
│   ├── projects/
│   ├── catalog/
│   ├── conversations/
│   ├── query_engine/
│   ├── connectors/
│   └── observability/
│
├── shared/
│   ├── domain/
│   ├── application/
│   └── infrastructure/
│
├── templates/
├── static/
└── tests/
```

This structure is indicative.

The final package organization will be validated during project initialization.

---

## 30. Internal Module Structure

Each significant Django application should separate responsibilities where useful.

Example:

```text
apps/query_engine/
├── domain/
│   ├── entities.py
│   ├── services.py
│   └── interfaces.py
│
├── application/
│   ├── commands.py
│   ├── handlers.py
│   └── dto.py
│
├── infrastructure/
│   ├── llm/
│   ├── persistence/
│   └── sql/
│
├── models.py
├── admin.py
├── urls.py
├── views.py
└── tests/
```

This separation should remain pragmatic.

Small modules do not need unnecessary layers or empty packages.

---

## 31. Transaction Boundaries

### Project Configuration

Project creation and data source configuration may span several user actions.

The project remains in a non-ready state until initialization succeeds.

### Catalog Construction and Regeneration

Catalog construction and regeneration should:

* create a Schema Snapshot;
* store discovered technical metadata;
* generate and store semantic metadata;
* update catalog status;
* update project status;

External schema discovery cannot be part of one long database transaction.
During regeneration, the existing ready catalog remains available until the new catalog has been built successfully. If regeneration fails, the previous catalog is preserved and the project returns to the ready state.

### Question Processing

A Question Run should be persisted before external processing begins.

Each significant step updates the run and trace state independently.

A failed external call must not erase the existing Question Run history.

---

## 32. Error Handling

Components should return structured application errors rather than leaking raw infrastructure exceptions.

### Error Categories

* validation error;
* authorization error;
* project state error;
* connection error;
* catalog error;
* query validation error;
* query execution error;
* LLM provider error;
* timeout;
* unexpected internal error.

### Rules

* User-facing messages remain generic and understandable.
* Technical details are logged safely.
* Sensitive information is removed from errors.
* External provider errors are translated into application-level errors.
* Failed Question Runs remain traceable.

---

## 33. Asynchronous Processing

The initial implementation may execute short operations synchronously.

Operations likely to justify asynchronous execution later include:

* schema discovery;
* Knowledge Catalog construction;
* Knowledge Catalog regeneration;
* long-running queries;
* evaluation workflows.

No task queue is required for the initial Foundation unless actual execution times make it necessary.

The application layer should avoid coupling business logic to a specific task queue.

---

## 34. Future FastAPI Extraction

FastAPI is not part of the initial deployment architecture.

The Query Engine may later be extracted when one or more of the following conditions appear:

* independent scaling is required;
* asynchronous API workloads become significant;
* model inference deployment differs from the Django application;
* multiple clients need direct access to the Query Engine;
* separate deployment cycles become valuable;
* operational isolation becomes necessary.

### Candidate Extraction Boundary

```text
Django Application
    |
    | Internal API
    v
FastAPI Query Engine
    |
    +--> LLM Provider
    |
    +--> External Data Source
```

The following interfaces must remain stable to support extraction:

* submit question;
* continue clarification;
* retrieve run status;
* retrieve final result;
* retrieve safe execution traces.

Extraction is an architectural option, not an MVP requirement.

---

## 35. Explicitly Deferred Components

The following components are intentionally excluded from the initial implementation:

* dedicated FastAPI service;
* task queue;
* Redis;
* dedicated vector database;
* Kubernetes;
* event broker;
* service mesh;
* multiple LLM providers;
* additional database connectors;
* real-time collaborative services;
* separate frontend SPA.

They may be introduced only when supported by a concrete functional or operational need.

---

## 36. Component Summary

| Component                | Primary Responsibility                | Initial Release               |
| ------------------------ | ------------------------------------- | ----------------------------- |
| Web Interface            | User interaction                      | MVP                           |
| Administration Interface | Platform administration               | Production-ready Portfolio    |
| Accounts                 | Authentication and users              | MVP                           |
| Projects                 | Project lifecycle and ownership       | MVP                           |
| Data Source Management   | External connection configuration     | Foundation / MVP              |
| Catalog                  | Semantic catalog and schema snapshots | Foundation / MVP              |
| Conversations            | Messages and contextual history       | MVP                           |
| Query Engine             | AI-assisted question workflow         | Foundation                    |
| Connectors               | External source abstraction           | Foundation                    |
| PostgreSQL Connector     | PostgreSQL integration                | Foundation                    |
| LLM Provider             | Provider-independent model access     | Foundation                    |
| Observability            | Logs, traces and metrics              | Foundation / Production-ready |
| Shared Kernel            | Minimal shared abstractions           | Foundation                    |
| Persistence              | Application data storage              | Foundation                    |

---

## 37. Main Architectural Rules

1. AskMyData starts as a modular monolith.
2. Django is the initial application framework.
3. Project is the central domain aggregate.
4. Modules expose explicit application services.
5. Module internals are not accessed directly by other modules.
6. Domain logic remains independent from external providers.
7. LLM provider access is hidden behind an interface.
8. External database access is hidden behind the Connector interface.
9. Only the PostgreSQL Connector is implemented initially.
10. Generated SQL is never executed before validation.
11. Presentation components never access databases directly.
12. Application data and external source data remain separate.
13. Question Runs and Execution Traces provide operational traceability.
14. Conversation context is isolated between Conversations within the same Project.
15. Sensitive information is excluded from logs and traces.
16. FastAPI extraction remains possible but is not implemented prematurely.
17. Infrastructure components are introduced only when a demonstrated need exists.