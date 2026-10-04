-- PostgreSQL integration-test fixture for AskMyData.
--
-- This script creates the external source database used by connector,
-- catalog and query-engine integration tests.

CREATE DATABASE askmydata_test_source;

\connect askmydata_test_source

CREATE SCHEMA sales;

CREATE TABLE sales.customers (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    email VARCHAR
);

CREATE TABLE sales.orders (
    id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES sales.customers(id),
    amount NUMERIC NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

INSERT INTO sales.customers (name, email)
VALUES
    ('Alice', 'alice@example.com'),
    ('Bob', 'bob@example.com');

INSERT INTO sales.orders (customer_id, amount, created_at)
VALUES
    (1, 49.90, '2026-01-10T10:00:00Z'),
    (1, 25.00, '2026-01-11T11:00:00Z'),
    (2, 75.50, '2026-01-12T12:00:00Z');


-- Read-only role used by normal data-source integration tests.

CREATE ROLE askmydata_readonly
    LOGIN
    PASSWORD 'readonly_test_password';

GRANT CONNECT ON DATABASE askmydata_test_source TO askmydata_readonly;
GRANT USAGE ON SCHEMA sales TO askmydata_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA sales TO askmydata_readonly;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA sales TO askmydata_readonly;


-- Writable role used to verify permission detection and
-- read-only transaction enforcement.

CREATE ROLE askmydata_writable_test
    LOGIN
    PASSWORD 'writable_test_password';

GRANT CONNECT ON DATABASE askmydata_test_source TO askmydata_writable_test;
GRANT USAGE ON SCHEMA sales TO askmydata_writable_test;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA sales
    TO askmydata_writable_test;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA sales
    TO askmydata_writable_test;


-- Role intentionally lacking SELECT privileges.

CREATE ROLE askmydata_noselect_test
    LOGIN
    PASSWORD 'noselect_test_password';

GRANT CONNECT ON DATABASE askmydata_test_source TO askmydata_noselect_test;
GRANT USAGE ON SCHEMA sales TO askmydata_noselect_test;
