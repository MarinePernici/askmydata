# Architecture Decision Matrix

## Objective

Select the initial backend architecture for AskMyData.

The selected architecture must support the MVP while helping demonstrate skills in:

- software architecture;
- Python backend development;
- API design;
- Docker;
- automated testing;
- CI/CD;
- deployment;
- monitoring;
- maintainability.

---

## Options

### Option 1 — Django only

The application is built entirely with Django.

Django handles:

- web application;
- authentication;
- administration;
- business logic;
- API;
- AI workflow;
- database connectors.

### Option 2 — FastAPI only

The application is built entirely with FastAPI.

FastAPI handles:

- API;
- business logic;
- AI workflow;
- database connectors;
- authentication;
- administration through custom code.

### Option 3 — Django + FastAPI

The application is split into two services.

Django handles:

- users;
- projects;
- data source metadata;
- history;
- administration;
- web/API application layer.

FastAPI handles:

- schema retrieval;
- prompt building;
- SQL generation;
- SQL validation;
- query execution;
- answer generation.

### Option 4 — Django + FastAPI + Worker

The application uses Django, FastAPI and an asynchronous worker.

The worker handles:

- long-running queries;
- schema refresh;
- evaluation runs;
- background tasks.

### Option 5 — Full microservices

The application is split into several independent services:

- authentication service;
- project service;
- connector service;
- AI service;
- query execution service;
- monitoring service.

---

## Evaluation Criteria

| Criterion | Description |
|---|---|
| Simplicity | Is the architecture easy to implement for the MVP? |
| Maintainability | Does it keep responsibilities separated? |
| Scalability | Can it evolve toward more connectors and workloads? |
| Deployment cost | Can it be deployed cheaply? |
| CV value | Does it demonstrate useful backend and DevOps skills? |
| Learning value | Does it help develop missing skills? |
| Risk | Is the architecture likely to slow down delivery? |

---

## Comparison

Scores:

- 1 = weak
- 2 = acceptable
- 3 = good
- 4 = very good
- 5 = excellent

| Option | Simplicity | Maintainability | Scalability | Deployment cost | CV value | Learning value | Risk |
|---|---:|---:|---:|---:|---:|---:|---:|
| Django only | 5 | 3 | 2 | 5 | 3 | 3 | 2 |
| FastAPI only | 4 | 3 | 3 | 5 | 3 | 4 | 2 |
| Django + FastAPI | 3 | 5 | 4 | 4 | 5 | 5 | 3 |
| Django + FastAPI + Worker | 2 | 5 | 5 | 3 | 5 | 5 | 4 |
| Full microservices | 1 | 4 | 5 | 1 | 4 | 4 | 5 |

---

## Preliminary Analysis

### Django only

Strong for productivity and administration.

Weak for demonstrating service separation and AI-specific API design.

### FastAPI only

Strong for API and AI workflows.

Weak for administration, authentication and full web application structure.

### Django + FastAPI

Best balance for the portfolio objective.

It demonstrates architecture, API design, service separation and industrialisation without creating excessive complexity.

### Django + FastAPI + Worker

Technically strong, but too much for the first MVP.

Can be introduced later when background processing becomes necessary.

### Full microservices

Over-engineered for the project.

Too costly and too complex for a portfolio MVP.

---

## Preliminary Decision

The recommended architecture is:

**Option 3 — Django + FastAPI**

The worker architecture may be added later as an evolution.