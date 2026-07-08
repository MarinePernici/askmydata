# Requirements

## 1. Functional Requirements

### FR-001 - Project Management

The application shall allow a user to create a project.

### FR-002

The application shall allow a user to edit a project.

### FR-003

The application shall allow a user to delete a project.

### FR-004

The application shall allow a user to register a PostgreSQL data source.

### FR-005

The application shall validate the connection before saving it.

### FR-006

The application shall automatically discover the database schema.

### FR-007

The application shall display tables and columns.

### FR-008

The application shall allow the user to ask a question in natural language.

### FR-009

The application shall generate an SQL query.

### FR-010

The application shall validate the generated SQL before execution.

### FR-011

The application shall execute read-only SQL queries.

### FR-012

The application shall display both the generated SQL and the natural language answer.

### FR-013

The application shall keep a history of previous questions.

### FR-014

The application shall support French and English.

---

# 2. Non Functional Requirements

## NFR-001 Performance

The application should answer within a reasonable delay.

Target:
< 10 seconds for common queries.

---

## NFR-002 Security

Only read-only queries may be executed.

---

## NFR-003 Scalability

Adding a new connector should require minimal changes to the existing codebase.

---

## NFR-004 Maintainability

Business logic must be separated from presentation and infrastructure.

---

## NFR-005 Testability

Core services shall be unit tested.

---

## NFR-006 Deployment

The application shall be deployable using Docker Compose.

---

## NFR-007 Portability

The application shall run on Linux.

---

## NFR-008 Internationalization

All user-facing strings shall be translatable.

---

## NFR-009 Logging

Application events shall be logged.

---

## NFR-010 Monitoring

Health checks and metrics shall be exposed.