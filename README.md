# AskMyData

[Français](README.fr.md)

**Natural-language exploration of PostgreSQL data with controlled SQL generation and execution.**

AskMyData is a web application that allows users to explore structured data without writing SQL themselves. Users connect a PostgreSQL data source, select the data available to the application, and ask questions in natural language.

AskMyData builds a semantic Knowledge Catalog from the selected database schema, uses it to generate SQL queries, validates every query before execution, executes validated queries with read-only access, and returns answers in natural language.

> **Status: MVP complete — Production-readiness in progress.**
>
> The end-to-end PostgreSQL data exploration workflow is implemented and has been validated against a realistic dataset. Current work focuses on production readiness, observability, deployment, and a public demonstration environment.

## Key Features

- Natural-language exploration of PostgreSQL data
- Automatic database schema discovery
- Semantic Knowledge Catalog with generated descriptions and business-oriented synonyms
- Controlled natural-language-to-SQL pipeline
- Mandatory SQL validation before execution
- Read-only access to external data sources
- Catalog Scope enforcement to restrict accessible schemas and tables
- Clarification of ambiguous analytical questions
- Rejection of questions that cannot be answered from the project's data
- Contextual conversations with persistent history
- Persistent, user-friendly error messages for failed questions
- Failed exchanges excluded from subsequent LLM conversational context
- Execution tracing for query pipeline diagnostics
- Automated tests and documented quality benchmarking
- Docker Compose development environment

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

When a question is ambiguous or requires a missing business definition, AskMyData can request clarification before generating SQL. When the requested information cannot be derived from the project's available data, the question is rejected without SQL execution.

Technical failures are handled separately from clarification requests and questions that cannot be answered. When a question fails, AskMyData displays a dismissible error dialog and preserves a safe explanatory message in the conversation history.

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

Failed question-and-answer exchanges remain visible in the conversation history but are excluded from the context provided to the LLM for subsequent questions.

## Security and Controlled SQL Execution

Generated SQL is never executed directly.

AskMyData separates SQL generation, validation, and execution into distinct stages. Every generated query must pass application-level validation before it can reach the external database.

The current safeguards include:

- read-only SQL operations;
- mandatory SQL validation before execution;
- Catalog Scope enforcement for accessible schemas and tables;
- read-only database credentials;
- query execution limits;
- configurable account-level usage limits in Public Demo mode;
- result validation before answer generation;
- execution traces for pipeline diagnostics;
- environment-based secret management.

Queries that fail SQL validation are not executed. Questions requiring information outside the project's available data are rejected before reaching SQL execution.

LLM instructions are treated as guidance, not as a security boundary. Database permissions and application-level validation remain responsible for enforcing access restrictions.

## Public Demo

AskMyData includes a controlled Public Demo mode designed to allow
invited users to explore the complete application workflow without
connecting arbitrary external databases.

The demonstration environment provides four predefined PostgreSQL
datasets: EEG, Pagila, Olist, and Badminton.

The default usage limits are:

| Resource | Default limit |
|---|---|
| Projects | 5 per user |
| Questions | 30 per user per day |
| Catalog generations and regenerations | 10 per user per day |
| Question length | 2000 characters |

Daily usage counters are persisted in the application database.
Usage limits are enforced server-side before the corresponding
execution services are invoked.

All limits are configurable and apply exclusively in Public Demo mode.

These mechanisms reduce the risk of excessive resource consumption
but do not guarantee a global monetary spending cap.

See the [Demo Datasets documentation](docs/demo-datasets/README.md)
and the [Deployment Guide](docs/deployment.md#116-resource-protection)
for further details.

The Public Demo has been validated locally. Remote deployment and
final production validation remain in progress.

## Architecture

AskMyData follows a **modular monolith** architecture built with Django.

The application is organized into modules with explicit responsibilities:

- **Accounts** — authentication, user identity, and Public Demo usage limits
- **Projects** — project lifecycle and configuration
- **Data Source** — external database configuration and connection testing
- **Knowledge Catalog** — schema discovery and semantic metadata
- **Conversation** — conversation and message history
- **Query Engine** — context building, SQL generation, validation, execution, and answer generation
- **Connectors** — database and LLM provider abstractions
- **Observability** — execution traces and diagnostics

External systems are accessed through explicit connector abstractions.

PostgreSQL is the only data source currently implemented. The architecture is designed to allow additional connectors without coupling the domain model to a specific database technology.

LLM access is also provider-independent so that providers can be changed without modifying the core query workflow.

For the detailed component model and architectural decisions, see the [architecture documentation](docs/application-components.md) and [ADRs](docs/adrs/README.md).

## Technology Stack

### Application

- Python
- Django
- PostgreSQL
- Django Templates
- HTML / CSS
- limited JavaScript

### Data and Query Processing

- psycopg
- pglast for PostgreSQL SQL parsing and validation
- provider-independent LLM integration

### Development and Quality

- Django test framework
- Ruff
- GitHub Actions
- Docker
- Docker Compose
- Git / GitHub

## Quality & Validation

The MVP has been evaluated through a documented quality benchmark using the Pagila PostgreSQL sample database.

The benchmark covered the complete application workflow, including:

- schema discovery and semantic catalog generation;
- simple and complex aggregations;
- temporal filtering;
- multi-table joins and many-to-many relationships;
- conversational context and clarification;
- SQL validation and Catalog Scope enforcement;
- unsupported business metrics;
- questions that cannot be answered from the project's data.

Fourteen query scenarios and one catalog-generation scenario were evaluated against reference PostgreSQL results.

The benchmark was also used as an iterative quality process: functional and usability issues discovered during realistic testing were investigated, fixed, and validated through automated tests and real-data retesting.

At the latest recorded benchmark validation point, the full Docker test suite contained **371 passing tests**.

See the complete [MVP Quality Benchmark](docs/benchmark/mvp-quality-benchmark.md) for the methodology, scenarios, results, discovered issues, and resolutions.

The current automated Django test suite contains **more than 580 tests**
and is executed by GitHub Actions together with Ruff linting and
formatting checks.

Public Demo usage limits are covered by automated unit and integration
tests, including quota enforcement, user isolation, daily renewal,
failed execution attempts, and standard application mode behavior.

## Local Development

### Prerequisites

- Git
- Docker
- Docker Compose v2.24.4 or later

Python 3.13 and uv are additionally required for development activities outside Docker.

### Setup

Clone the repository and create the local environment file:

```bash
git clone https://github.com/MarinePernici/AskMyData.git
cd AskMyData
cp .env.example .env
```

Review `.env` and configure the required values, including:

- Django secret key.
- Data source encryption key.
- PostgreSQL credentials and connection URLs.
- OpenAI API key.

Secret generation and detailed environment configuration are documented in the [Deployment Guide](docs/deployment.md#4-environment-configuration).

OpenTelemetry is optional and disabled by default. Configuration instructions are available in the [Observability](docs/deployment.md#9-observability) section of the Deployment Guide.

Build and start the application:

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
```

Create the initial administrator account:

```bash
docker compose exec web python manage.py createsuperuser
```

The application is then available at:

```text
http://localhost:8000/
```

The Django administration interface is available at:

```text
http://localhost:8000/admin/
```

For Local Public Demo and production deployment instructions, see the [Deployment Guide](docs/deployment.md).

### Tests

Run the complete test suite inside the application container:

```bash
docker compose exec web python manage.py test
```

The complete test suite requires a dedicated PostgreSQL integration test database configured as described below.

### Code Quality

Check Ruff:

```bash
uv run ruff check .
uv run ruff format --check .
```

Format the code when needed:

```bash
uv run ruff format .
```

### Stop the Environment

```bash
docker compose down
```

Persistent database volumes are preserved.

### Integration Test Database

Tests that exercise a real external PostgreSQL source use dedicated `TEST_SOURCE_DB_*` environment variables and additional test database credentials.

The integration test database and its dedicated roles must be initialized before running the complete test suite.

The database initialization script is available at [`scripts/setup_test_database.sql`](scripts/setup_test_database.sql).

When the test database runs on the Docker host, the application container can access it through `host.docker.internal`, provided that the host name is resolvable and PostgreSQL accepts the connection.

The integration test database must use dedicated credentials and must not point to a production or personal database.

## Roadmap

### Completed — Foundation

- Modular Django architecture
- Core domain model and persistence
- PostgreSQL connector
- Knowledge Catalog foundation
- Natural-language-to-SQL pipeline
- SQL validation and read-only execution
- Execution tracing

### Completed — MVP

- User authentication
- Project creation and management
- PostgreSQL connection configuration and testing
- Secure data-source credential handling
- Catalog Scope selection
- Schema discovery and semantic Knowledge Catalog generation
- Knowledge Catalog regeneration
- Natural-language data exploration
- Contextual conversations and persistent history
- Clarification of ambiguous questions
- Rejection of questions unsupported by project data
- SQL validation and scope enforcement
- Automated test coverage
- Docker Compose development environment
- Realistic PostgreSQL quality benchmark

### In Progress — Production Readiness

Current work focuses on turning the validated MVP into a deployable public portfolio application.

Already implemented:

- comprehensive automated test suite
- Ruff-based linting and formatting configuration
- continuous integration with GitHub Actions, including PostgreSQL integration tests
- structured JSON application logging with Project and Question Run correlation
- logging privacy protections including invitation token redaction and safe exception representation
- targeted OpenTelemetry tracing for Question Runs, Query Engine steps, and LLM calls
- telemetry privacy protections through an explicit span attribute allowlist and disabled automatic HTTP and PostgreSQL instrumentation
- OpenTelemetry metrics for Question Run throughput and duration, LLM token usage, and Query Engine step duration
- optional OTLP export to an external observability backend, with telemetry disabled by default
- application liveness and readiness health checks
- Docker health monitoring for the application and PostgreSQL services
- public landing page
- access request management and invitation-based registration
- administration tools for controlled user access
- Public Demo mode restricting data source configuration to predefined datasets
- four demonstration datasets: EEG, Pagila, Olist, and Badminton
- dedicated demonstration PostgreSQL service with dataset-specific read-only accounts
- automated demonstration database initialization
- configurable Public Demo usage limits for projects, questions, catalog operations, and question length
- persistent daily usage counters with atomic quota enforcement
- read-only usage counter inspection through Django administration
- automated unit and integration tests for Public Demo resource protection
- production-oriented Docker configuration with Gunicorn, WhiteNoise, and Caddy
- local validation of the Public Demo environment and production deployment components
- deployment and operational documentation

Remaining production-readiness work includes:

- production configuration and validation of Public Demo usage limits
- dedicated OpenAI project and API key configuration, with budget alerts
- final security and telemetry privacy validation
- review of dataset reuse and public exposure conditions
- cloud hosting selection and server sizing
- remote deployment and public HTTPS validation
- production observability validation, error tracking, and alerting
- database backup and recovery validation
- continuous deployment
- final end-to-end validation before opening the Public Demo to invited users

### Future Extensions

The architecture is designed to support future capabilities such as additional data-source connectors, but these are intentionally outside the current production-readiness scope.

## Documentation

Detailed project documentation is available in [`docs/`](docs/):

- [Product Vision](docs/product-vision.md)
- [MVP Scope](docs/mvp-scope.md)
- [Requirements](docs/requirements.md)
- [Functional Use Cases](docs/functional-use-cases.md)
- [Domain Model](docs/domain-model.md)
- [Application Components](docs/application-components.md)
- [Design System](docs/design-system.md)
- [Architecture Decision Records](docs/adrs/README.md)
- [MVP Quality Benchmark](docs/benchmark/mvp-quality-benchmark.md)
- [Demo Datasets — EEG, Pagila, Olist, Badminton](docs/demo-datasets/README.md)
- [Deployment Guide](docs/deployment.md)
- [PlantUML Diagrams](docs/diagrams/README.md)

The documentation records the main product, domain, architectural, and technical decisions made throughout the project.

## Project Context

AskMyData is a personal portfolio project designed and developed to explore the engineering challenges involved in building a controlled natural-language interface for structured data.

The project is also used to deepen practical experience in software architecture, Python and Django development, data engineering, SQL safety, LLM integration, automated testing, containerization, and production-oriented development practices.

Rather than focusing only on a working prototype, the project follows a documented software-development approach including requirements, domain modeling, architectural decisions, functional testing, realistic quality benchmarking, and progressive production readiness.
