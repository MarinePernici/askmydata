# MVP Scope

## 1. Purpose

The MVP (Minimum Viable Product) aims to demonstrate the feasibility of an AI-powered platform that enables users to query structured data sources using natural language.

The objective is not to build a production-ready platform, but to deliver a coherent, extensible and production-inspired application suitable for a professional portfolio.

The MVP focuses on validating the overall architecture, user workflow and AI orchestration pipeline.

---

# 2. Included Features

## User Management

* invitation-only registration;
* account activation;
* secure authentication;
* session management;
* logout;
* user profile;
* user preferences.

---

## Project Management

* create a project;
* edit project information;
* delete a project;
* archive project conversations after deletion.

---

## Data Source Management

Supported source:

* PostgreSQL.

Features:

* configure connection;
* test connection;
* validate credentials;
* read-only access only;
* encrypted connection configuration.

---

## Project Setup Wizard

The project creation workflow includes:

1. project information;
2. data source configuration;
3. connection test;
4. schema discovery;
5. schema and table selection;
6. Knowledge Catalog generation.

---

## Knowledge Catalog

* automatic schema discovery;
* schema snapshots;
* schema refresh;
* schema and table selection;
* semantic metadata;
* user-enriched descriptions;
* business synonyms;
* hidden objects.

---

## AI Query Engine

The AI agent supports:

* natural language questions;
* contextual conversations;
* clarification requests when needed;
* AI orchestration pipeline;
* read-only query generation;
* query validation;
* query execution;
* natural language answers.

---

## Conversation Management

* one active conversation per project;
* conversation history;
* contextual follow-up questions;
* archived conversations remain consultable.

---

## User Interface

* bilingual interface;
* French;
* English;
* light/dark theme;
* responsive layout.

---

## Administration

Using Django Admin:

* invitation management;
* user management;
* project overview;
* platform monitoring.

---

## Developer Features

* developer mode;
* execution pipeline status;
* execution metrics;
* diagnostic information.

Internal prompts and AI reasoning are never exposed.

---

## Infrastructure

* Docker Compose;
* automated tests;
* GitHub Actions;
* CI/CD pipeline;
* monitoring;
* cloud-ready deployment.

---

# 3. Explicitly Excluded

The following features are intentionally excluded from the MVP.

## Additional Data Sources

* CSV
* JSON
* BigQuery
* MongoDB
* MySQL
* SQL Server
* Oracle

---

## Advanced AI

* multiple AI providers;
* autonomous agents;
* long-term memory;
* fine tuning;
* Retrieval-Augmented Generation (RAG).

---

## Collaboration

* shared projects;
* multiple project members;
* comments;
* real-time collaboration.

---

## Analytics

* dashboards;
* charts;
* automatic reports;
* PDF export.

---

## Enterprise Features

* SSO;
* OAuth providers;
* advanced permissions;
* organizations;
* billing;
* quotas.

---

# 4. Platform Limits

The demonstration platform intentionally includes several limits.

Examples:

* invitation-only access;
* maximum number of projects per user;
* one data source per project;
* one active conversation per project;
* read-only queries;
* maximum execution time;
* maximum number of returned rows.

These limits may evolve in future versions.

---

# 5. MVP Success Criteria

The MVP will be considered complete when a user can:

* authenticate using an invitation;
* create a project;
* connect a PostgreSQL database;
* discover the database structure;
* choose which schemas and tables are exposed;
* automatically generate a Knowledge Catalog;
* enrich the catalog with business metadata;
* ask questions using natural language;
* receive reliable answers;
* continue contextual conversations;
* refresh the Knowledge Catalog;
* use the application in French and English.

From a technical perspective, the application must also provide:

* Docker-based deployment;
* automated testing;
* CI/CD through GitHub Actions;
* monitoring;
* production-inspired architecture;
* public online demonstration.
