<!-- docs>product-vision.md -->

# Product Vision

## Vision

Organizations increasingly rely on structured data to support operational and strategic decisions. However, accessing this information often requires technical expertise, knowledge of database schemas, and SQL skills that many users do not possess.

AskMyData aims to bridge this gap by providing an AI-assisted data exploration platform built on a semantic understanding of enterprise data.

Rather than interacting directly with a database, users interact with a knowledge layer generated from its structure and enriched with business context. This approach enables more reliable, secure and explainable interactions while reducing the need for technical expertise.

---

# Problem Statement

Although organizations store large amounts of valuable data, extracting meaningful information remains difficult.

Several challenges limit access to this information:

- database schemas are often large and difficult to understand;
- business terminology rarely matches table or column names;
- writing SQL queries requires technical expertise;
- traditional AI-to-SQL approaches often lack business context;
- generated SQL may be incorrect, unsafe or difficult to validate;
- users need confidence in the answers produced by AI systems.

Existing solutions frequently focus on translating natural language into SQL, but provide little understanding of the underlying data model or the reasoning behind the generated answers.

---

# Proposed Solution

AskMyData introduces a semantic knowledge layer between the database and the AI engine.

Before answering questions, the application builds a Knowledge Catalog describing the structure of the database, its relationships and business meaning.

This catalog allows the AI engine to:

- understand the user's intent;
- interpret business vocabulary;
- generate more relevant SQL queries;
- validate generated queries before execution;
- execute queries in a controlled read-only environment;
- generate clear natural language answers supported by reliable database queries.

The database remains the source of truth, while the Knowledge Catalog provides the contextual understanding required for accurate AI-assisted exploration.

---

# Target Users

## Long-term Vision

AskMyData is designed to make structured data accessible to every business user, regardless of their technical background.

Typical users include:

- business analysts;
- product managers;
- finance teams;
- marketing teams;
- sales teams;
- human resources;
- operations teams;
- decision makers.

The long-term objective is to reduce technical barriers and democratize access to organizational knowledge.

## MVP Focus

The first version focuses on technical users who regularly work with data, including:

- Data Analysts;
- Data Scientists;
- Analytics Engineers;
- BI Developers;
- Software Engineers.

This narrower scope allows the project to validate the core concepts before extending the platform to a broader audience.

---

# Core Principles

The following principles guide every architectural and functional decision.

## Reliability over novelty

The objective is not simply to generate SQL with a Large Language Model, but to produce reliable and trustworthy answers.

## Semantic understanding before SQL generation

The AI should reason from business knowledge rather than directly from raw database structures.

## Security by design

Database access must remain controlled, auditable and read-only by default.

## Explainability

Users should understand how answers are produced and be able to trust the underlying execution process.

## Modular architecture

Business logic, AI orchestration, infrastructure and user interface must remain loosely coupled to facilitate maintenance and future evolution.

## Incremental development

The platform is built iteratively, validating the AI engine first before expanding towards a complete production-ready application.

---

# Product Goals

The project aims to demonstrate that AI-assisted data exploration can be both accessible and reliable.

The primary objectives are:

- simplify access to structured data;
- reduce dependency on SQL expertise;
- improve understanding of complex databases;
- provide trustworthy AI-assisted answers;
- demonstrate modern software engineering practices for AI applications.

---

# Out of Scope

AskMyData is not intended to become:

- a Business Intelligence platform;
- a dashboard builder;
- a reporting tool;
- a database administration tool;
- an autonomous AI agent capable of modifying databases;
- a replacement for existing database management systems.

The platform focuses exclusively on secure, explainable and AI-assisted exploration of structured data.

---

# Success Vision

A successful version of AskMyData enables users to explore complex databases naturally, without requiring detailed knowledge of their internal structure.

The platform combines semantic understanding, controlled SQL generation and modern software engineering practices to deliver a reliable AI-assisted experience.

Beyond solving a practical problem, the project also demonstrates the design, development and industrialization of a modern AI application through clean architecture, automated testing, containerization, CI/CD, observability and production-oriented engineering practices.