# Olist Demo Dataset

## Overview

The Olist dataset contains historical Brazilian e-commerce data.

It is used to demonstrate AskMyData's ability to explore relational data, generate SQL queries from natural language, and answer business-oriented analytical questions.

## Data provenance

- **Source:** [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- **Platform:** Kaggle
- **Domain:** E-commerce
- **License:** CC BY-NC-SA 4.0

The license permits reuse under specific conditions, including attribution, noncommercial use, and share-alike requirements.

Any public demonstration using this dataset must comply with these conditions.

## Database

- **Database:** `olist`
- **Read-only role:** `olist_readonly`
- **Backup archive:** `backups/demo-db/olist.sql.gz`

## Relational model

The PostgreSQL schema contains nine tables representing:

- Customers.
- Orders.
- Order items.
- Products.
- Sellers.
- Payments.
- Reviews.
- Product category translations.
- Geolocation data.

The dataset contains approximately 1.55 million records across these tables.

The relational structure supports analysis involving multiple entities, including orders, customers, products, sellers, and payments.

## Data preparation

The dataset is prepared using:

- `scripts/demo-db/olist/schema.sql`
- `scripts/demo-db/olist/import.sh`

The SQL schema defines the relational structure, while the import script loads the source data into PostgreSQL.

## Demonstration use cases

Examples of natural-language questions include:

- What is the monthly evolution of order volumes?
- Which product categories generate the most revenue?
- What is the average order value?
- Which states have the highest number of customers?
- How do delivery times vary across orders?

These questions illustrate potential analytical use cases rather than validated benchmark results.

## Initialization

The database is restored from `olist.sql.gz` through `scripts/demo-db/init.sh`.

The initialization process creates the database and grants `olist_readonly` read-only access to tables in the `public` schema.

## Limitations

The dataset contains historical e-commerce transactions and does not represent current business activity.

The records may contain missing values, inconsistencies, or other limitations inherited from the source.

Analytical results should be interpreted within the context of the original dataset and its coverage.

The dataset is intended for demonstration and educational use, subject to its licensing conditions.
