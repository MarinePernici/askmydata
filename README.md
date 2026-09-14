# AskMyData

AskMyData is a web application for exploring structured data using natural language.

The application aims to make data exploration accessible to users without requiring them to write SQL queries themselves. A user connects a data source, selects the data they want to make available to AskMyData, and then asks questions in natural language. AskMyData relies on a Knowledge Catalog to understand the available data, generates a SQL query, validates it before execution, executes it using read-only access, and then produces an understandable natural-language answer.

The first version focuses on PostgreSQL while maintaining an architecture that can be extended to other structured data sources.

> AskMyData is currently under development. The project is being built incrementally from documented architecture and specifications.

## How It Works

A typical AskMyData workflow is:

1. Create a project.
2. Configure a PostgreSQL data source and test the connection.
3. Select the schemas and tables that define the project's Catalog Scope.
4. Discover the source schema and build the Knowledge Catalog.
5. Ask a question in natural language.
6. Build the relevant context from the Knowledge Catalog and conversation history.
7. Generate a SQL query.
8. Validate the query before execution.
9. Execute the validated query using read-only database access.
10. Validate the result and generate a natural-language answer.

When a question is ambiguous or cannot be answered reliably, AskMyData can request clarification rather than generate an answer that is not sufficiently supported by the available data.

## Knowledge Catalog

The Knowledge Catalog acts as the semantic layer between the external data source and the AI-assisted query pipeline.

It combines:

- technical metadata discovered from the source;
- schema snapshots;
- automatically generated semantic descriptions;
- business-oriented synonyms.

Each project defines a **Catalog Scope** containing the schemas and tables available for exploration.

The Knowledge Catalog can be regenerated from the current source schema while preserving this scope.

## Conversational Data Exploration

AskMyData supports multiple conversations within the same project.

Each conversation maintains its own context, allowing users to:

- ask new questions;
- continue previous exchanges;
- respond to clarification requests;
- return to existing conversations;
- keep conversation histories isolated from one another.

## Security and Controlled SQL Execution

Generated SQL is never executed directly.

The pipeline separates query generation, validation, and execution. Before execution, generated SQL is checked against explicit security rules and the project's Catalog Scope.

The application relies on several safeguards, including:

- read-only SQL operations;
- mandatory SQL validation before execution;
- access restricted to the selected Catalog Scope;
- read-only credentials for external PostgreSQL sources;
- controlled execution limits;
- result validation before answer generation;
- execution traces for pipeline diagnostics and traceability;
- protection of application secrets and data-source credentials.

Instructions provided to the LLM are not considered a security boundary on their own.

## Architecture

AskMyData follows a **modular monolith** architecture built around Django.

The application is organized around several business capabilities:

- Accounts;
- Projects;
- Data Source Management;
- Knowledge Catalog;
- Conversation Management;
- Query Engine;
- Connectors;
- Observability.

The Query Engine is an internal application module responsible for coordinating the pipeline from a natural-language question to an answer.

External data sources are accessed through a connector abstraction. PostgreSQL is the only connector implemented in the initial scope, but the architecture is designed to allow additional connectors to be introduced later without requiring a major architectural redesign.

LLM access also relies on a provider-independent interface.

## Technology Stack

### Application

- Python
- Django
- PostgreSQL
- Django Templates
- limited client-side JavaScript

### Data Access and AI

- PostgreSQL connector
- SQLAlchemy Core or equivalent SQL tooling
- provider-independent LLM integration

### Engineering and Deployment

- pytest
- Docker / Docker Compose
- GitHub Actions
- static analysis and type checking
- structured logging
- health checks
- monitoring and error tracking

Specific infrastructure and observability tools will be selected during the Production-ready Portfolio phase.

## Local Development with Docker

### Prerequisites

- Docker
- Docker Compose

### Environment Configuration

Create the local environment file from the provided example:

```bash
cp .env.example .env
```

Then configure the required values in `.env`.

### Start the Application

Build the application image:

```bash
docker compose build
```

Start the services:

```bash
docker compose up -d
```

Apply the database migrations:

```bash
docker compose exec web python manage.py migrate
```

The application is then available at:

```text
http://localhost:8000/projects/
```
Unauthenticated users are redirected to the login page.

### Run the Test Suite

```bash
docker compose exec web python manage.py test
```

### Stop the Application

```bash
docker compose down
```

The Docker Compose development environment runs the Django application and its PostgreSQL application database in separate containers.

PostgreSQL integration tests use the external test database configured through the `TEST_SOURCE_DB_*` environment variables. When the tests are executed inside Docker Desktop, the test database running on the host is reached through `host.docker.internal`.

## Development Roadmap

Development is organized into three incremental stages.

### Foundation

The Foundation validates the core technical pipeline:

- PostgreSQL connectivity;
- schema discovery;
- minimal Knowledge Catalog;
- natural-language question processing;
- SQL generation;
- SQL validation;
- read-only execution;
- result validation;
- natural-language answer generation;
- execution traces;
- automated tests for the core system.

### MVP

The MVP adds the complete user workflow:

- authentication and session management;
- project creation, editing, and archiving;
- PostgreSQL configuration and connection testing;
- secure credential handling;
- Catalog Scope selection;
- Knowledge Catalog generation and regeneration;
- automatic semantic metadata generation;
- data schema exploration;
- multiple contextual conversations per project;
- persistent conversation history;
- clarification handling;
- responsive web interface for different desktop screen sizes;
- Docker Compose development environment.

### Production-ready Portfolio

The final phase focuses on production readiness and deployment:

- broader test coverage;
- static analysis and type checking;
- CI/CD with GitHub Actions;
- production Docker images;
- structured logging and monitoring;
- health checks;
- error tracking;
- cloud deployment;
- public demonstration environment;
- invitation-based access;
- administration tools;
- internationalization and user preferences.

## Current Scope

The current scope is intentionally limited.

PostgreSQL is the only supported external data source.

The following are notably outside the current portfolio scope:

- additional database and file connectors;
- autonomous multi-agent systems;
- long-term AI memory;
- fine-tuning;
- RAG-based document exploration;
- collaborative workspaces;
- advanced analytics features;
- enterprise-oriented features;
- manual semantic metadata editing;
- manual synonym management;
- advanced Knowledge Catalog version comparison;
- interfaces specifically designed for mobile devices.

These limitations are intentional so that the project can focus on a complete, secure, testable, and deployable data exploration workflow.

## Documentation

The project is documented before and throughout its implementation.

Detailed documentation covers:

- product vision;
- MVP scope;
- functional and non-functional requirements;
- functional use cases;
- domain model;
- application components;
- design system;
- Architecture Decision Records (ADRs);
- PlantUML architecture and domain diagrams.

This documentation serves as the reference for implementation decisions.

## Project Goals

AskMyData is also a portfolio project designed to apply and strengthen skills in:

- Python application development;
- Django architecture;
- data engineering and SQL;
- LLM integration;
- secure AI-assisted data access;
- software architecture;
- automated testing;
- Docker;
- CI/CD;
- observability;
- production deployment.

The objective is not only to build a functional AI prototype, but to develop a structured software project that explicitly incorporates architectural decisions, security constraints, testing, documentation, and deployment practices.
