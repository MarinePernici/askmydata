# Domain Model

## 1. Purpose

This document describes the main business entities of AskMyData, their responsibilities and their relationships.

The domain model is independent from the technical implementation. It does not depend on Django, FastAPI, PostgreSQL, SQLAlchemy or any specific LLM provider.

---

## 2. Domain Overview

AskMyData allows an authenticated user to create projects connected to external data sources.

Each project contains:

* one data source;
* one knowledge catalog;
* one project configuration;
* one active conversation;
* multiple messages and question execution runs.

The application is available through invitation only.

---

## 3. Main Entities

## User

Represents an authenticated person using AskMyData.

### Responsibilities

* Own projects.
* Access only their own data.
* Manage personal preferences.
* Authenticate through a secure session.
* Use invitations to create an account.

### Main attributes

* `id`
* `email`
* `password_hash`
* `is_active`
* `is_verified`
* `created_at`
* `last_login_at`

### Relationships

* A user has one `UserPreferences`.
* A user can own several `Project` entities.
* A user can accept one `Invitation`.

---

## UserPreferences

Represents user-specific interface and localization preferences.

### Main attributes

* `language`
* `timezone`
* `theme`

### Initial supported values

#### Language

* `fr`
* `en`

#### Theme

* `light`
* `dark`
* `system`

### Relationships

* One `UserPreferences` belongs to one `User`.

---

## Invitation

Represents an invitation allowing a person to create an account.

Invitations are created only by the platform administrator.

### Main attributes

* `id`
* `email`
* `token_hash`
* `status`
* `expires_at`
* `created_at`
* `accepted_at`
* `revoked_at`
* `invited_by`

### Status values

* `pending`
* `accepted`
* `expired`
* `revoked`

### Business rules

* An invitation can only be used once.
* An invitation expires after a defined duration.
* The account email must match the invited email.
* A revoked or expired invitation cannot be accepted.
* Public self-registration is not allowed.

---

## Project

Represents a user workspace dedicated to one data source.

A project is defined by its data source and provides access to its semantic catalog and conversation.

### Main attributes

* `id`
* `name`
* `description`
* `status`
* `created_at`
* `updated_at`
* `owner_id`

### Status values

* `draft`
* `initializing`
* `ready`
* `error`
* `archived`

### Business rules

* A project belongs to exactly one user.
* A project contains exactly one data source.
* A project contains exactly one active conversation in the MVP.
* A user may own several projects.
* The number of projects per user may be limited in demonstration mode.
* Deleting a project permanently deletes its data source configuration and sensitive information.
* The conversation is archived and remains consultable after project deletion.

---

## DataSource

Represents the central business resource connected to an external data system.

A data source is not only a technical connection. It also contains status information, access restrictions and synchronization metadata.

### Main attributes

* `id`
* `name`
* `description`
* `source_type`
* `connection_status`
* `encrypted_connection_configuration`
* `last_connection_test_at`
* `last_successful_connection_at`
* `created_at`
* `updated_at`

### Initial source types

* `postgresql`

### Future source types

* `csv`
* `json`
* `bigquery`
* `mongodb`
* other SQL databases

### Connection status values

* `not_configured`
* `testing`
* `connected`
* `unreachable`
* `invalid_credentials`
* `error`

### Business rules

* A data source belongs to exactly one project.
* A data source cannot be shared between projects in the MVP.
* Connection secrets must never be stored in plain text.
* The data source must be read-only.
* A connection must be successfully tested before the project becomes ready.
* The data source is used to generate and refresh the knowledge catalog.
* The application does not read the schema before every user question.

---

## ProjectSettings

Represents configurable project-level behavior.

These settings are independent from the connection configuration.

### Main attributes

* `response_language`
* `llm_model`
* `maximum_result_rows`
* `query_timeout_seconds`
* `conversation_context_size`
* `allowed_schemas`
* `allowed_tables`
* `developer_mode_enabled`
* `created_at`
* `updated_at`

### Business rules

* Settings belong to exactly one project.
* Default settings are applied when the project is created.
* The response language can differ from the interface language.
* Query limits must always respect platform-level maximum values.
* Developer mode must not expose secrets, prompts or internal reasoning.

---

## KnowledgeCatalog

Represents the semantic knowledge layer generated from a data source.

It is the main abstraction used by the AI query engine to understand the connected source.

### Responsibilities

* Store discovered schema information.
* Store user-enriched business metadata.
* Store access restrictions.
* Store schema refresh history.
* Provide structured context to the AI orchestration pipeline.

### Main attributes

* `id`
* `status`
* `version`
* `created_at`
* `updated_at`
* `last_refreshed_at`

### Status values

* `pending`
* `building`
* `ready`
* `outdated`
* `failed`

### Relationships

* A knowledge catalog belongs to exactly one project.
* A knowledge catalog is generated from exactly one data source.
* A knowledge catalog contains one or more `SchemaSnapshot` entities.
* A knowledge catalog may contain semantic metadata and data profiles.

### Business rules

* The catalog is generated automatically from the data source.
* The user may enrich selected catalog elements.
* Technical schema information cannot be modified manually.
* User-defined descriptions and synonyms are stored separately from discovered schema metadata.
* Refreshing the catalog creates a new schema snapshot.
* Previous snapshots may be retained for audit and comparison.

---

## SchemaSnapshot

Represents a versioned technical snapshot of the source schema at a specific time.

### Main attributes

* `id`
* `version`
* `status`
* `captured_at`
* `schema_hash`
* `raw_metadata`
* `error_message`

### Contained information

* schemas;
* tables;
* columns;
* data types;
* primary keys;
* foreign keys;
* constraints;
* indexes, when available.

### Business rules

* A schema snapshot is immutable after creation.
* A refresh creates a new snapshot.
* Only one snapshot is considered current.
* Historical snapshots may remain available.
* Schema metadata must not contain connection secrets.

---

## SemanticMetadata

Represents user-provided business knowledge associated with catalog elements.

### Examples

* table descriptions;
* column descriptions;
* business definitions;
* synonyms;
* aliases;
* units;
* business rules;
* hidden or excluded fields.

### Main attributes

* `id`
* `target_type`
* `target_identifier`
* `description`
* `synonyms`
* `is_allowed`
* `created_at`
* `updated_at`
* `created_by`

### Business rules

* Semantic metadata supplements technical metadata.
* It does not modify the source schema.
* It must remain associated with the relevant schema element after refresh when possible.
* Restricted objects must not be sent to the LLM or queried.

---

## DataProfile

Represents optional statistical metadata calculated from source data.

### Examples

* null percentage;
* minimum value;
* maximum value;
* distinct value count;
* sample values;
* value distribution.

### Business rules

* Data profiling is optional in the MVP.
* Profiling must respect security and query limits.
* Sensitive values must not be exposed.
* Profiling results belong to a specific schema snapshot.

---

## Conversation

Represents the continuous interaction between a user and a project.

### Main attributes

* `id`
* `status`
* `created_at`
* `updated_at`
* `archived_at`

### Status values

* `active`
* `archived`

### Business rules

* A project has one active conversation in the MVP.
* A conversation contains several messages.
* Previous messages may be used as contextual input.
* Only a limited number of recent messages are sent to the AI model.
* A conversation remains consultable after project deletion.
* Archived conversations cannot execute new queries.

---

## Message

Represents one ordered conversational message.

### Main attributes

* `id`
* `role`
* `content`
* `language`
* `sequence_number`
* `created_at`

### Role values

* `user`
* `assistant`
* `system`
* `tool`
* `error`

### Business rules

* Every message belongs to one conversation.
* Messages are ordered.
* Messages are immutable after creation, except for controlled moderation or deletion requirements.
* Internal reasoning must never be stored as a user-visible message.
* Clarification requests are assistant messages.
* Clarification answers are user messages.

---

## QuestionRun

Represents the controlled execution of one user request through the AI orchestration pipeline.

A run may include clarification exchanges before producing a final answer.

### Main attributes

* `id`
* `status`
* `started_at`
* `completed_at`
* `input_message_id`
* `output_message_id`
* `model_name`
* `prompt_tokens`
* `completion_tokens`
* `estimated_cost`
* `latency_ms`
* `row_count`
* `error_code`
* `error_message`

### Status values

* `pending`
* `analyzing`
* `needs_clarification`
* `planning`
* `generating_query`
* `validating_query`
* `executing_query`
* `validating_result`
* `generating_answer`
* `completed`
* `failed`
* `rejected`

### Business rules

* A run starts from a user message.
* A run may request one or more clarifications.
* Clarification messages remain associated with the same run.
* A query cannot be executed before validation.
* Only read-only queries are accepted.
* The final result is stored as an assistant message.
* Failed and rejected runs remain traceable.
* Internal reasoning is never exposed.

---

## ExecutionTrace

Represents technical diagnostic information related to a question run.

### Main attributes

* `id`
* `step`
* `status`
* `started_at`
* `completed_at`
* `duration_ms`
* `technical_metadata`
* `error_code`
* `error_message`

### Example steps

* intent analysis;
* schema selection;
* context building;
* query planning;
* SQL generation;
* SQL validation;
* query execution;
* result validation;
* answer generation.

### Business rules

* Execution traces are not part of the normal user conversation.
* Normal users only see simplified processing states.
* Developer mode may expose selected metrics.
* Prompts, secrets and internal reasoning must not be exposed.
* Trace data supports testing, monitoring and debugging.

---

## 4. Domain Services

The following concepts are services rather than persistent business entities.

They will appear in the technical architecture and component diagrams.

### Connector

Provides a common interface for interacting with external data sources.

Examples:

* PostgreSQL connector;
* CSV connector;
* BigQuery connector;
* MongoDB connector.

### Knowledge Builder

Builds and refreshes the knowledge catalog from a data source.

### Question Orchestrator

Coordinates the complete question-answering workflow.

### Intent Analyzer

Determines whether the user request is understandable, allowed and sufficiently precise.

### Context Builder

Selects the relevant conversation history and catalog information.

### Query Planner

Creates a structured execution plan.

### Query Generator

Generates a source-specific query.

### Query Validator

Checks security, syntax and platform rules.

### Query Executor

Executes an approved read-only query through a connector.

### Result Validator

Checks whether the result is usable and consistent.

### Answer Generator

Produces the natural language answer.

---

## 5. Main Relationships

```text
User
├── UserPreferences
├── Invitation
└── Project*
    ├── DataSource
    ├── ProjectSettings
    ├── KnowledgeCatalog
    │   ├── SchemaSnapshot*
    │   ├── SemanticMetadata*
    │   └── DataProfile*
    └── Conversation
        ├── Message*
        └── QuestionRun*
            └── ExecutionTrace*
```

---

## 6. Main Business Rules

1. Access to the application requires a valid invitation.
2. A user can own several projects.
3. A project belongs to exactly one user.
4. A project contains exactly one data source.
5. A data source cannot be shared between projects in the MVP.
6. A project contains one active conversation in the MVP.
7. A conversation contains multiple ordered messages.
8. A question run may contain clarification exchanges.
9. Only validated read-only queries may be executed.
10. The AI engine uses the knowledge catalog instead of rediscovering the schema for every question.
11. The knowledge catalog is generated automatically and can be enriched by the user.
12. Technical schema metadata and user-defined semantic metadata remain separated.
13. Deleting a project removes the source configuration and secrets.
14. The conversation is archived and remains consultable.
15. Platform limits may restrict projects, questions, query duration and result size.
16. Internal model reasoning, secrets and complete prompts are never exposed to users.
