# Component Responsibilities

## Frontend

### Responsibilities

- Display the user interface.
- Manage user interactions.
- Display query results.
- Display application errors.

### Does NOT

- Execute SQL.
- Call databases directly.
- Build prompts.
- Validate SQL.

---

## Project Management

### Responsibilities

- Create projects.
- Update projects.
- Delete projects.
- Retrieve project information.

### Does NOT

- Execute queries.
- Manage connectors.

---

## Data Source Management

### Responsibilities

- Register data sources.
- Store connection information.
- Test connections.
- Refresh schemas.

### Does NOT

- Execute user queries.

---

## Question Engine

### Responsibilities

Coordinate the complete question-answering workflow.

### Does NOT

- Know how PostgreSQL works.
- Know how MongoDB works.

---

## Schema Retriever

### Responsibilities

Retrieve the schema through the connector interface.

---

## Prompt Builder

### Responsibilities

Prepare prompts sent to the LLM.

---

## SQL Generator

### Responsibilities

Generate SQL from the natural language question.

---

## SQL Validator

### Responsibilities

Validate generated SQL.

Reject forbidden statements.

Apply execution rules.

---

## Query Executor

### Responsibilities

Execute validated queries through the connector.

---

## Answer Generator

### Responsibilities

Transform raw results into natural language.

---

## Connector Interface

### Responsibilities

Provide a common API for every connector.

### Does NOT

Contain business logic.

---

## PostgreSQL Connector

### Responsibilities

Interact with PostgreSQL.

---

## CSV Connector

### Responsibilities

Interact with CSV files.

---

## BigQuery Connector

### Responsibilities

Interact with BigQuery.

---

## MongoDB Connector

### Responsibilities

Interact with MongoDB.