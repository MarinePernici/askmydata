# Domain Model

## 1. Purpose

This document defines the business concepts of AskMyData, their relationships and the business rules governing the application.

The domain model describes **what the application manages**, independently from any implementation technology.

It does not describe:

- the application architecture;
- the database schema;
- the API;
- the user interface;
- the infrastructure.

Those aspects are documented separately.

---

# 2. Domain Overview

AskMyData enables users to explore structured databases using natural language.

The central concept of the application is the **Project**.

A Project represents a complete data exploration workspace containing everything required to query a single structured data source.

A Project may contain:

- one external data source;
- one catalog scope;
- one Knowledge Catalog;
- project settings;
- one active conversation (MVP);
- conversation messages;
- question execution history;
- execution traces.

The external database always remains the source of truth.

The Knowledge Catalog provides semantic context but never modifies the source data.

---

# 3. Aggregate Boundaries

## Project Aggregate

`Project` is the aggregate root of the domain.

All business operations are performed inside a project.

The Project aggregate owns:

- DataSource
- CatalogScope
- ProjectSettings
- KnowledgeCatalog
- Conversation
- QuestionRun
- ExecutionTrace

The aggregate guarantees the consistency of the exploration workspace.

External systems (PostgreSQL, LLM providers, authentication providers...) are not part of the domain model.

---

# 4. Main Entities

## User

### Definition

Represents an authenticated user of AskMyData.

### Responsibilities

- authenticate;
- own projects;
- manage personal preferences;
- access owned projects.

### Main Attributes

- id
- email
- password_hash
- is_active
- created_at
- updated_at
- last_login_at

### Relationships

A User:

- owns zero or more Projects;
- has zero or one UserPreferences.

### Business Rules

- Email addresses must be unique.
- Passwords are never stored in plain text.
- Users may only access projects they own.
- Inactive users cannot authenticate.

### Release

MVP

---

## UserPreferences

### Definition

Represents optional user interface preferences.

### Main Attributes

- language
- response_language
- timezone
- theme

### Relationships

One User owns at most one UserPreferences.

### Release

Production-ready Portfolio

---

## Invitation

### Definition

Represents an invitation allowing a person to register on the platform.

Invitations are intended for the public demonstration platform.

### Main Attributes

- id
- email
- token_hash
- status
- expires_at
- created_at
- accepted_at
- revoked_at

### Status Values

- pending
- accepted
- expired
- revoked

### Business Rules

- Invitations are single-use.
- Expired invitations cannot be accepted.
- Tokens are stored as hashes.
- Public registration may be disabled.

### Release

Production-ready Portfolio

---

## Project

### Definition

Represents the central data exploration workspace.

A Project groups all resources required to explore one structured data source.

### Responsibilities

- manage one data source;
- define the catalog scope;
- own the Knowledge Catalog;
- own conversations;
- own execution history;
- store project configuration.

### Main Attributes

- id
- name
- description
- status
- created_at
- updated_at
- archived_at

### Status Values

- draft
- configuring
- building_catalog
- ready
- refreshing_catalog
- archived

Failures are recorded separately and are not lifecycle states.

### Relationships

A Project:

- belongs to one User;
- owns zero or one DataSource;
- owns zero or one CatalogScope;
- owns zero or one KnowledgeCatalog;
- owns exactly one ProjectSettings;
- owns zero or one active Conversation (MVP);
- owns zero or more QuestionRuns.

### Lifecycle

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

### Business Rules

- Projects are created in the `draft` state.
- A project becomes `ready` only after successful catalog generation.
- Only ready projects may answer questions.
- Archived projects cannot execute new questions.
- Project history is preserved after archival.
- A project is never physically deleted during the MVP.

### Release

MVP

## DataSource

### Definition

Represents the external structured data source connected to a Project.

A DataSource provides access to the database explored by AskMyData.

### Responsibilities

- store the connection configuration;
- validate connectivity;
- expose database metadata;
- execute validated read-only queries.

### Main Attributes

- id
- name
- source_type
- connection_status
- encrypted_connection_configuration
- last_connection_test_at
- last_successful_connection_at
- created_at
- updated_at

### Supported Source Types

#### MVP

- postgresql

#### Future

- MySQL
- MariaDB
- SQL Server
- Oracle
- DuckDB
- Snowflake
- BigQuery

### Connection Status

- not_configured
- testing
- connected
- unreachable
- invalid_credentials
- insufficient_permissions
- error
- disabled

### Relationships

A DataSource:

- belongs to one Project.

### Business Rules

- A project contains at most one DataSource in the MVP.
- Connection credentials are always encrypted.
- Only read-only database accounts are supported.
- The connection must be validated before schema discovery.
- The source database remains the single source of truth.
- AskMyData never modifies the external database.

### Release

Foundation

---

## CatalogScope

### Definition

Represents the subset of database objects exposed to the AI engine.

The CatalogScope defines the exploration boundary of a Project.

### Responsibilities

- select accessible schemas;
- select accessible tables;
- limit the AI context;
- enforce the exploration perimeter.

### Main Attributes

- id
- selected_schemas
- selected_tables
- created_at
- updated_at

### Relationships

A CatalogScope:

- belongs to one Project;
- is used to build one KnowledgeCatalog.

### Business Rules

- At least one table must be selected.
- Objects outside the scope cannot be queried.
- Updating the scope requires rebuilding the Knowledge Catalog.

### Release

MVP

---

## ProjectSettings

### Definition

Represents the configurable behavior of a Project.

### Main Attributes

- response_language
- maximum_result_rows
- query_timeout_seconds
- conversation_context_size
- developer_mode_enabled

### Relationships

ProjectSettings belong to exactly one Project.

### Business Rules

- Default settings are created with the Project.
- Project settings cannot exceed platform limits.
- Developer mode never exposes secrets or hidden prompts.

### Release

MVP

---

## KnowledgeCatalog

### Definition

Represents the semantic representation of the selected database.

The Knowledge Catalog provides the business context used by the AI Query Engine.

### Responsibilities

- store discovered metadata;
- store semantic metadata;
- expose searchable business knowledge;
- provide context for question answering.

### Main Attributes

- id
- version
- status
- created_at
- updated_at
- last_refreshed_at

### Status Values

- pending
- building
- ready
- outdated
- failed

### Relationships

A KnowledgeCatalog:

- belongs to one Project;
- is built from one CatalogScope;
- contains one or more SchemaSnapshots;
- contains zero or more SemanticMetadata entries.

### Business Rules

- Technical metadata is generated automatically.
- Semantic metadata is maintained by users.
- The catalog cannot modify the source database.
- A project becomes Ready only when the catalog is Ready.
- Refreshing the catalog creates a new SchemaSnapshot.

### Release

Foundation

---

## SchemaSnapshot

### Definition

Represents an immutable snapshot of the selected database structure.

Snapshots allow AskMyData to detect schema evolution over time.

### Main Attributes

- id
- version
- schema_hash
- captured_at
- raw_metadata

### Relationships

A SchemaSnapshot:

- belongs to one KnowledgeCatalog.

### Business Rules

- Snapshots are immutable.
- Every refresh creates a new snapshot.
- Only one snapshot is considered current.
- Historical snapshots may be retained for comparison.

### Release

MVP

---

## SemanticMetadata

### Definition

Represents business knowledge associated with database objects.

Unlike technical metadata, SemanticMetadata is created and maintained by users.

### Examples

- business descriptions;
- synonyms;
- aliases;
- business definitions;
- units;
- visibility restrictions.

### Main Attributes

- id
- target_type
- target_identifier
- description
- synonyms
- is_allowed
- created_at
- updated_at

### Relationships

SemanticMetadata:

- belongs to one KnowledgeCatalog.

### Business Rules

- Semantic metadata supplements technical metadata.
- It never modifies the source schema.
- Compatible metadata should be preserved after catalog refresh.
- Metadata that cannot be mapped after a schema change must be flagged for review.
- Objects marked as unavailable cannot be exposed to the AI engine.

### Release

MVP

---

## Conversation

### Definition

Represents the history of interactions between a user and a Project.

A Conversation provides the contextual information required for follow-up questions.

### Responsibilities

- store exchanged messages;
- preserve conversational context;
- group QuestionRuns.

### Main Attributes

- id
- status
- created_at
- updated_at
- archived_at

### Status Values

- active
- archived

### Relationships

A Conversation:

- belongs to one Project;
- contains zero or more Messages;
- contains zero or more QuestionRuns.

### Business Rules

- A Project has at most one active Conversation in the MVP.
- Previous messages may be used as conversational context.
- Only a limited amount of recent context is sent to the AI engine.
- Archived conversations cannot receive new messages.

### Release

MVP

---

## Message

### Definition

Represents one message exchanged during a Conversation.

Messages are ordered chronologically.

### Main Attributes

- id
- role
- content
- language
- sequence_number
- created_at

### Role Values

- user
- assistant
- system
- tool
- error

### Relationships

A Message:

- belongs to one Conversation;
- may initiate one QuestionRun.

### Business Rules

- Messages are immutable after creation.
- Hidden prompts are never stored as user-visible messages.
- Hidden model reasoning is never exposed.
- Clarification requests are assistant messages.

### Release

MVP

---

## QuestionRun

### Definition

Represents one execution of the AI query pipeline.

A QuestionRun begins when a user submits a question and ends when the application produces a final answer, rejects the request or encounters a failure.

Unlike a Message, a QuestionRun represents processing rather than conversation.

### Responsibilities

- coordinate one question execution;
- track execution status;
- record execution metrics;
- link user input to generated output.

### Main Attributes

- id
- status
- started_at
- completed_at
- latency_ms
- model_name
- prompt_tokens
- completion_tokens
- estimated_cost
- row_count
- error_code
- error_message

### Status Values

- pending
- running
- needs_clarification
- completed
- failed
- rejected
- abandoned

### Relationships

A QuestionRun:

- belongs to one Project;
- belongs to one Conversation;
- starts from one user Message;
- may produce one assistant Message;
- contains zero or more ExecutionTraces.

### Business Rules

- Only ready Projects may execute QuestionRuns.
- Generated SQL must always be validated before execution.
- Only read-only queries may be executed.
- Clarification exchanges remain attached to the same QuestionRun.
- Failed and rejected executions remain traceable.
- Unsupported answers must never be presented as reliable.

### Release

Foundation

---

## ExecutionTrace

### Definition

Represents one technical step executed during a QuestionRun.

Execution traces are intended for diagnostics, testing and observability.

They are not part of the user conversation.

### Responsibilities

- record pipeline execution;
- measure execution duration;
- store technical diagnostics;
- support debugging.

### Main Attributes

- id
- step
- status
- started_at
- completed_at
- duration_ms
- technical_metadata
- error_code
- error_message

### Example Steps

- intent analysis
- context selection
- query planning
- SQL generation
- SQL validation
- query execution
- result validation
- answer generation

### Relationships

An ExecutionTrace:

- belongs to one QuestionRun.

### Business Rules

- Execution traces are never exposed directly to end users.
- Sensitive information must never be stored.
- Hidden prompts are never recorded.
- Hidden model reasoning is never recorded.
- Execution traces support monitoring and debugging.

### Release

Foundation

---

# 5. Domain Services

The following concepts represent domain behavior rather than persistent entities.

They encapsulate business logic and coordinate interactions between domain entities.

Their technical implementation is described in the application architecture documentation.

---

## Connector

### Definition

Provides a common interface for interacting with external data sources.

### Responsibilities

- validate database connections;
- discover database schemas;
- execute validated read-only queries.

### Initial Implementation

- PostgreSQL Connector

---

## Knowledge Builder

### Definition

Builds and refreshes the Knowledge Catalog.

### Responsibilities

- discover technical metadata;
- generate SchemaSnapshots;
- preserve compatible SemanticMetadata;
- build the current KnowledgeCatalog.

---

## Question Orchestrator

### Definition

Coordinates the complete AI query workflow.

It orchestrates the different domain services without implementing all their logic directly.

### Responsibilities

- coordinate QuestionRuns;
- invoke specialized services;
- manage execution flow.

---

## Intent Analyzer

### Definition

Determines the user's intent before query generation.

### Responsibilities

- detect ambiguous questions;
- detect unsupported requests;
- determine whether clarification is required.

---

## Context Builder

### Definition

Builds the contextual information required by the AI engine.

### Responsibilities

- retrieve KnowledgeCatalog information;
- retrieve SemanticMetadata;
- retrieve conversation context;
- prepare the final prompt context.

---

## Query Planner

### Definition

Transforms the user intent into an execution plan.

### Responsibilities

- identify required entities;
- determine the expected query strategy;
- prepare SQL generation.

---

## Query Generator

### Definition

Generates a read-only SQL query from the execution plan.

### Responsibilities

- generate SQL;
- respect catalog boundaries;
- produce source-specific queries.

---

## Query Validator

### Definition

Validates generated SQL before execution.

### Responsibilities

- verify syntax;
- reject forbidden statements;
- enforce read-only execution;
- verify catalog scope.

---

## Query Executor

### Definition

Executes validated SQL through the configured Connector.

### Responsibilities

- execute approved queries;
- retrieve results;
- capture execution metrics.

---

## Result Validator

### Definition

Determines whether the query result is sufficient to answer the user's question.

### Responsibilities

- validate returned data;
- detect empty or inconsistent results;
- prevent unsupported answers.

---

## Answer Generator

### Definition

Produces the final natural language response.

### Responsibilities

- generate the final answer;
- summarize results;
- explain limitations when necessary.

---

# 6. Main Relationships

# 6. Main Relationships

The relationships and cardinalities between the main domain entities are represented in the domain overview diagram:

- PlantUML source: [`diagrams/source/domain-overview.puml`](diagrams/source/domain-overview.puml)
- Generated diagram: [`diagrams/generated/AskMyData_Domain_Overview.svg`](diagrams/generated/AskMyData_Domain_Overview.svg)

The diagram is the reference representation of the domain relationships. Entity definitions and business rules remain documented in this file.

---

# 7. Main Business Rules

## Project

1. A Project is the central exploration workspace.
2. A Project belongs to exactly one User.
3. A Project contains at most one DataSource in the MVP.
4. A Project becomes **Ready** only after successful Knowledge Catalog generation.
5. Archived Projects cannot execute new questions.

---

## Data Exploration

6. PostgreSQL is the only supported connector in the MVP.
7. The external database always remains the source of truth.
8. AskMyData never modifies the external database.
9. Only database objects included in the CatalogScope may be queried.

---

## AI Query Engine

10. Every generated query must be validated before execution.
11. Only read-only queries may be executed.
12. Unsupported or unsafe queries must be rejected.
13. The application must never present unsupported answers as reliable.

---

## Knowledge Catalog

14. Technical metadata is generated automatically.
15. Semantic metadata is maintained by users.
16. Refreshing the catalog creates a new SchemaSnapshot.
17. Compatible semantic metadata should be preserved across refreshes.

---

## Security

18. Users may access only their own Projects.
19. Connection credentials are always encrypted.
20. Secrets must never be exposed.
21. Hidden prompts and hidden model reasoning are never exposed.

---

## Traceability

22. Every QuestionRun remains traceable.
23. Failed executions are preserved.
24. Rejected executions are preserved.
25. Execution traces are separate from user-visible conversations.

---

# 8. Explicitly Deferred Concepts

The following concepts are intentionally excluded from the current domain model.

They may be introduced in future releases without changing the core architecture.

## Collaboration

- shared projects;
- project members;
- organizations;
- advanced permissions.

---

## Data Sources

- multiple data sources per project;
- non-SQL databases;
- file connectors;
- cloud warehouses.

---

## AI Features

- autonomous agents;
- scheduled analyses;
- automatic insights;
- report generation.

---

## Analytics

- dashboards;
- charts;
- exports;
- scheduled reports.

---

## Platform

- billing;
- quotas;
- usage limits;
- API keys management.

---

# 9. Domain Model Summary

The domain revolves around a single aggregate root: **Project**.

A Project represents a complete data exploration workspace containing:

- one DataSource;
- one CatalogScope;
- one KnowledgeCatalog;
- one active Conversation;
- QuestionRuns;
- ExecutionTraces;
- ProjectSettings.

The Knowledge Catalog provides semantic understanding of the selected database.

QuestionRuns orchestrate AI-assisted exploration while ExecutionTraces ensure observability and traceability.

This model deliberately separates:

- business concepts;
- technical implementation;
- infrastructure concerns.

This separation enables the application to evolve without coupling the domain model to specific frameworks or AI providers.