<!-- docs>mvp-scope.md -->

# MVP Scope

## 1. Purpose

AskMyData is developed incrementally to ensure that each stage delivers measurable value while keeping the architecture extensible.

Rather than attempting to build the complete platform from the beginning, the project is divided into three successive milestones:

1. Foundation
2. MVP
3. Production-ready Portfolio

Each stage builds upon the previous one without requiring major architectural redesign.

---

# 2. Foundation

## Objective

Validate the core AI-powered query engine independently from the complete web application.

The goal is to ensure that the end-to-end workflow is reliable before introducing user management, project management and deployment concerns.

## Included

- PostgreSQL connector
- Schema discovery
- Minimal Knowledge Catalog generation
- Natural language question processing
- AI orchestration pipeline
- SQL generation
- SQL validation
- Read-only query execution
- Natural language answer generation
- Execution traces
- Unit tests for the core services

## Excluded

- Authentication
- User accounts
- Project management
- Administration
- Conversation history
- Developer dashboard
- CI/CD
- Monitoring
- Cloud deployment

---

# 3. MVP

## Objective

Deliver a complete web application allowing a user to securely explore a PostgreSQL database using natural language.

The MVP focuses on functional completeness rather than production-level operations.

## Included Features

### User Management

- secure authentication
- session management

### Project Management

- create a project
- edit project information
- delete a project

### Data Source Management

- PostgreSQL connector
- connection configuration
- connection testing
- encrypted credentials
- read-only access

### Project Setup

- schema discovery
- schema selection
- table selection
- Knowledge Catalog generation

### Knowledge Catalog

- automatic generation
- schema refresh
- semantic descriptions
- business synonyms

### AI Query Engine

- natural language questions
- contextual conversations
- clarification requests
- SQL generation
- SQL validation
- read-only execution
- natural language answers

### Conversation

- one active conversation per project
- conversation history

### User Interface

- responsive web interface

### Technical Foundation

- modular architecture
- automated tests
- Docker Compose for local development

---

# 4. Production-ready Portfolio

## Objective

Demonstrate software engineering and MLOps practices expected in a modern AI application.

This stage focuses on maintainability, deployment and operational excellence.

## Included Features

### Software Quality

- comprehensive automated tests
- code quality checks
- static analysis
- architecture validation

### DevOps

- Docker images
- GitHub Actions
- CI pipeline
- CD pipeline

### Observability

- structured logging
- health checks
- execution metrics
- monitoring dashboards
- error tracking

### Deployment

- cloud deployment
- public demonstration instance
- production configuration
- secret management

### Advanced Platform Features

- invitation-only registration
- Django administration
- developer mode
- internationalization
- user preferences
- theme support

---

# 5. Explicitly Excluded

The following features are intentionally excluded from the current portfolio roadmap.

## Additional Data Sources

- CSV
- JSON
- MySQL
- SQL Server
- Oracle
- BigQuery
- MongoDB

## Advanced AI

- multiple AI providers
- autonomous agents
- long-term memory
- fine tuning
- Retrieval-Augmented Generation (RAG)

## Collaboration

- shared projects
- multiple project members
- comments
- real-time collaboration

## Analytics

- dashboards
- charts
- PDF export
- scheduled reports

## Enterprise Features

- organizations
- advanced permissions
- SSO
- OAuth providers
- billing
- quotas

---

# 6. Success Criteria

## Foundation

The project successfully answers natural language questions over a PostgreSQL database through a secure AI pipeline.

## MVP

A user can:

- authenticate
- create a project
- connect a PostgreSQL database
- build a Knowledge Catalog
- ask contextual questions
- receive reliable natural language answers

## Production-ready Portfolio

The application demonstrates:

- clean architecture
- automated testing
- Docker-based deployment
- CI/CD
- monitoring
- structured logging
- cloud deployment
- production-inspired engineering practices
