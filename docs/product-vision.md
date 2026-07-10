# Product Vision

## 1. Vision

AskMyData is a web platform that enables users to explore and query structured data sources using natural language through an AI-powered assistant.

Instead of directly interacting with databases, AskMyData builds a semantic knowledge catalog from connected data sources. This catalog provides the AI agent with structured knowledge about the data, enabling more reliable, secure and explainable answers.

The platform is designed to be extensible and source-agnostic, allowing new data source types to be added without modifying the application's core architecture.

---

# 2. Problem Statement

Organizations store valuable information in databases, data warehouses and structured files.

Although these data sources contain valuable business knowledge, accessing them usually requires technical skills such as:

* SQL;
* understanding database schemas;
* knowledge of relationships between tables;
* assistance from developers or data analysts.

As a result, business users often depend on technical teams to answer relatively simple questions.

AskMyData aims to reduce this dependency by providing a secure natural language interface over structured data.

---

# 3. Objectives

## Functional Objectives

Allow users to:

* create projects;
* connect external data sources;
* automatically discover their structure;
* select which schemas and tables should be exposed to the AI;
* automatically build a knowledge catalog;
* enrich the catalog with business metadata;
* ask questions in natural language;
* receive reliable and understandable answers;
* keep a searchable conversation history.

---

## Technical Objectives

Design a modern backend platform featuring:

* modular architecture;
* clear separation of responsibilities;
* REST APIs;
* AI orchestration;
* connector-based architecture;
* secure execution pipeline;
* observability;
* automated testing;
* CI/CD;
* cloud deployment;
* containerized infrastructure.

---

## Educational Objectives

The project serves as a portfolio demonstrating practical experience with:

* software architecture;
* Python development;
* Django;
* FastAPI;
* Docker;
* automated testing;
* GitHub Actions;
* CI/CD;
* cloud deployment;
* monitoring;
* LLM integration;
* AI application development.

---

# 4. Target Audience

AskMyData is primarily intended for:

* business users;
* analysts;
* developers;
* data professionals;
* anyone who needs to explore structured data without writing SQL.

The current version is developed as a portfolio project and technical demonstration.

---

# 5. Main User Journey

1. Create a project.
2. Configure a data source.
3. Test the connection.
4. Discover the database structure.
5. Select the schemas and tables to expose.
6. Build the knowledge catalog.
7. Ask questions in natural language.
8. Review the generated answer.
9. Continue the conversation using contextual follow-up questions.

---

# 6. Core Features

## MVP

* user authentication;
* invitation-only access;
* project management;
* PostgreSQL connector;
* automatic schema discovery;
* schema and table selection;
* automatic knowledge catalog generation;
* knowledge catalog enrichment;
* AI-powered natural language querying;
* secure read-only query execution;
* conversation history;
* bilingual interface (French and English).

---

## Future Versions

* CSV support;
* JSON support;
* BigQuery connector;
* MongoDB connector;
* additional SQL databases;
* semantic search;
* dashboards and charts;
* project sharing;
* team collaboration;
* external authentication providers;
* additional languages.

---

# 7. Design Principles

The platform is built around the following principles:

* modular architecture;
* separation of concerns;
* extensibility;
* security by default;
* explainability;
* observability;
* internationalization;
* maintainability;
* documentation-first development.

---

# 8. Internationalization

Internationalization is considered from the beginning of the project.

The first supported languages are:

* French
* English

Additional languages should be added without significant architectural changes.

---

# 9. Constraints

The project must:

* remain inexpensive to deploy;
* be publicly accessible as a demonstration platform;
* provide invitation-only access;
* operate in read-only mode against connected data sources;
* never modify external data;
* support multiple data source technologies through a common architecture;
* rely on open-source technologies whenever possible.

---

# 10. Success Criteria

The project will be considered successful if it demonstrates:

* secure user authentication;
* successful PostgreSQL integration;
* automatic knowledge catalog generation;
* reliable natural language querying;
* extensible connector architecture;
* containerized deployment;
* automated testing;
* CI/CD pipeline;
* production-like architecture;
* public online demonstration;
* straightforward integration of additional data source connectors.

---

# 11. Non-Goals

The first version is **not** intended to:

* replace a Business Intelligence platform;
* replace an ETL or ELT solution;
* become a SQL editor;
* modify connected data sources;
* train custom AI models;
* expose prompts or internal AI reasoning;
* support every existing database technology;
* optimize for large-scale production workloads.
