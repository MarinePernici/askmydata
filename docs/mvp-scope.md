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
- archive a project

### Data Source Management

- PostgreSQL connector
- connection configuration
- connection testing
- encrypted credentials
- read-only access

### Project Setup

- schema discovery
- schema and table selection
- Catalog Scope definition
- Knowledge Catalog generation

### Data Exploration

- data source overview
- schema exploration
- table and column metadata
- database relationships

### Knowledge Catalog

- automatic generation
- technical metadata
- automatically generated semantic descriptions
- business synonyms
- catalog regeneration from the current source schema

### AI Query Engine

- natural language questions
- contextual conversations
- clarification requests
- SQL generation
- SQL validation
- read-only execution
- result validation
- natural language answers

### Conversations

- multiple conversations per project
- persistent conversation history
- contextual follow-up questions

### User Interface

- responsive desktop web interface
- project dashboard
- guided project creation workflow
- data source overview
- schema exploration
- Knowledge Catalog exploration
- conversational interface
- project settings

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

## Advanced Catalog Management

- manual semantic metadata editing
- manual synonym management
- schema change conflict resolution
- advanced catalog version comparison

## User Interface

- mobile-specific layouts
- mobile-optimized navigation
- tablet-specific layouts

---

# 6. Success Criteria

## Foundation

The project successfully answers natural language questions over a PostgreSQL database through a secure AI pipeline.

## MVP

A user can:

- authenticate securely
- create and configure a project
- connect and validate a PostgreSQL data source
- select the schemas and tables available for exploration
- build and inspect a Knowledge Catalog
- inspect the selected database schema
- create and revisit conversations
- ask contextual questions in natural language
- receive answers supported by validated read-only SQL queries
- update and archive a project

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
