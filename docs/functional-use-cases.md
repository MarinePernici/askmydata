# Functional Use Cases

## 1. Purpose

This document describes the main functional use cases of AskMyData from the user's perspective.

It focuses on user goals rather than technical implementation.

---

# 2. Actors

## User

An authenticated person using AskMyData to explore and query structured data.

---

## Administrator

Platform administrator responsible for managing invitations and application administration.

---

## AI Agent

The intelligent assistant responsible for understanding user requests, orchestrating query execution and generating natural language responses.

---

## External Data Source

An external system containing structured data.

Examples:

* PostgreSQL
* CSV
* JSON
* BigQuery
* MongoDB

---

# UC01 — Authenticate

## Primary Actor

User

## Goal

Access the application securely.

## Main Scenario

1. The user receives an invitation.
2. The user creates an account.
3. The user signs in.
4. A secure session is created.
5. The dashboard is displayed.

## Success Result

The user can access their projects.

---

# UC02 — Create a Project

## Primary Actor

User

## Goal

Create a new project connected to a structured data source.

## Main Scenario

1. The user creates a new project.
2. The user enters general project information.
3. The project is created.
4. The project enters the configuration workflow.

## Success Result

A new project is available for configuration.

---

# UC03 — Configure a Data Source

## Primary Actor

User

## Goal

Connect a project to an external data source.

## Main Scenario

1. The user selects a data source type.
2. Connection parameters are entered.
3. The application tests the connection.
4. The connection is validated.
5. The data source is associated with the project.

## Success Result

The project is connected to an external data source.

---

# UC04 — Build the Knowledge Catalog

## Primary Actor

User

## Goal

Generate the semantic representation of the connected data source.

## Main Scenario

1. The application discovers the database structure.
2. Available schemas are displayed.
3. The user selects the schemas to expose.
4. Available tables are displayed.
5. The user selects the tables to expose.
6. The application builds the Knowledge Catalog.
7. The project becomes ready.

## Success Result

The project contains a Knowledge Catalog that can be used by the AI agent.

---

# UC05 — Enrich the Knowledge Catalog

## Primary Actor

User

## Goal

Improve the semantic quality of the project.

## Main Scenario

1. The user opens the Knowledge Catalog.
2. The user adds descriptions.
3. The user adds business definitions.
4. The user adds synonyms.
5. The user hides unnecessary objects.
6. The catalog is updated.

## Success Result

Future AI responses benefit from richer business knowledge.

---

# UC06 — Query a Project

## Primary Actor

User

## Goal

Retrieve information using natural language.

## Main Scenario

1. The user asks a question.
2. The AI agent analyses the request.
3. The Knowledge Catalog is used as context.
4. If necessary, the AI agent asks for clarification.
5. A query is generated.
6. The query is validated.
7. The query is executed in read-only mode.
8. Results are validated.
9. A natural language answer is generated.
10. The conversation is updated.

## Success Result

The user receives a reliable answer.

---

# UC07 — Continue a Conversation

## Primary Actor

User

## Goal

Continue asking contextual questions.

## Main Scenario

1. The user opens an existing conversation.
2. A follow-up question is asked.
3. Previous messages provide conversational context.
4. A new answer is generated.

## Success Result

The conversation continues naturally.

---

# UC08 — Refresh the Knowledge Catalog

## Primary Actor

User

## Goal

Synchronize the project with changes in the external data source.

## Main Scenario

1. The user requests a refresh.
2. The application rediscover the source structure.
3. A new schema snapshot is generated.
4. Existing semantic metadata is preserved whenever possible.
5. The Knowledge Catalog is updated.

## Success Result

The project reflects the current structure of the external data source.

---

# UC09 — Manage User Preferences

## Primary Actor

User

## Goal

Customize the application.

## Main Scenario

The user can modify:

* interface language;
* preferred response language;
* theme;
* timezone.

## Success Result

Preferences are applied immediately.

---

# UC10 — Delete a Project

## Primary Actor

User

## Goal

Remove a project.

## Main Scenario

1. The user requests project deletion.
2. The application asks for confirmation.
3. The data source configuration is removed.
4. Sensitive connection information is deleted.
5. The conversation is archived.
6. The project is permanently deleted.

## Success Result

The project no longer exists while archived conversations remain consultable.

---

# UC11 — Manage Invitations

## Primary Actor

Administrator

## Goal

Control access to the demonstration platform.

## Main Scenario

1. The administrator creates an invitation.
2. An invitation email is sent.
3. The invitation can be revoked before use.
4. The invitation expires automatically if unused.

## Success Result

Only invited users can create an account.

---

# 3. Future Use Cases

The following use cases are outside the MVP but are planned for future versions:

* support additional data source types;
* manage multiple conversations per project;
* share projects;
* collaborate with multiple users;
* generate charts and dashboards;
* export query results;
* semantic search within the Knowledge Catalog;
* scheduled catalog refresh;
* background processing for long-running tasks;
* external authentication providers (Google, Microsoft, GitHub).

---

# 4. Business Rules

The following rules apply to all use cases:

* every project belongs to exactly one user;
* every project contains exactly one data source in the MVP;
* every project contains one active conversation in the MVP;
* queries are always executed in read-only mode;
* only selected schemas and tables are exposed to the AI agent;
* the AI agent relies on the Knowledge Catalog rather than querying the schema for every request;
* users may enrich the semantic layer of the Knowledge Catalog;
* technical metadata and business metadata remain separated;
* project deletion removes connection information while preserving archived conversations;
* access to the platform is invitation-only.
