# MVP Quality Benchmark

## 1. Objective

Evaluate the functional quality of the AskMyData MVP on a realistic PostgreSQL database.

The benchmark focuses on:

- database discovery and catalog generation;
- natural-language question understanding;
- clarification of ambiguous questions;
- SQL generation and validation;
- result accuracy;
- natural-language answer accuracy;
- Catalog Scope enforcement;
- graceful handling of unsupported questions;
- usability issues revealed by a realistic dataset.

---

## 2. Test Environment

### Application

- AskMyData MVP
- PostgreSQL connector
- Full natural-language query pipeline

### Benchmark Database

- Dataset: Pagila
- Version: `pagila-v3.1.0`
- PostgreSQL: 17
- Schema: `public`
- Tables: 22
- Access: dedicated read-only PostgreSQL account

The benchmark database is kept external to the AskMyData application database.

---

## 3. Benchmark Methodology

Each benchmark scenario records, where applicable:

- a scenario identifier;
- the natural-language question or operation being tested;
- the expected behavior;
- a reference SQL query and result obtained directly from PostgreSQL;
- the AskMyData result or answer;
- the outcome;
- observations;
- execution details when available and useful for diagnosis.

Generated SQL is not exposed by the current MVP interface and is not
persisted in execution trace metadata. It is therefore recorded only when
available through other diagnostic means.

---

## 4. Benchmark Scenarios

### 4.1 Catalog Generation

#### BENCH-CAT-001 — Catalog generation on Pagila

**Scope**

- Schema: `public`
- Selected tables: 22
- Discovered columns: 129

**Initial result (v1)**

- Catalog status: Ready
- Tables: 22
- Columns: 129
- Business synonyms: 0
- Business descriptions: not generated
- Semantic enrichment: not executed

This initial run revealed BENCH-BUG-001.

**Result after BENCH-BUG-001 resolution (v2)**

- Catalog status: Ready
- Tables: 22
- Columns: 129
- Business synonyms: 161
- Business descriptions: generated
- Semantic enrichment: executed

**Outcome:** Pass after BENCH-BUG-001 resolution

### 4.2 Natural-Language Query Quality

#### BENCH-QA-001 — Simple count

**Question**

> How many customers are there?

**Expected behavior**

AskMyData should identify the `customer` table, generate a read-only count query,
execute it successfully, and return the number of customers.

**Reference SQL**

```sql
SELECT COUNT(*) AS customer_count
FROM public.customer;
```

**Reference result**

599

**AskMyData answer**

> There are 599 customers.

**Outcome**

Pass.

**Observations**

The question completed successfully through all five query pipeline steps:

- SQL generation;
- SQL validation;
- query execution;
- result validation;
- answer generation.

The run returned one result row. Generated SQL is not exposed by the current
MVP interface or stored in the execution trace metadata.

#### BENCH-QA-002 — Simple aggregation

**Question**

> What is the total amount of all payments?

**Expected behavior**

AskMyData should identify the payment data, aggregate the payment amounts,
and return the total amount.

**Reference SQL**

```sql
SELECT SUM(amount) AS total_payment_amount
FROM public.payment;
```

**Reference result**

67416.51

**AskMyData answer**

> The total amount of all payments is 67,416.51.

**Outcome**

Pass.

**Observations**

The answer exactly matches the PostgreSQL reference result.

AskMyData correctly identified the payment amount and performed the expected
aggregation.

#### BENCH-QA-003 — Temporal filtering

**Question**

> How many rentals occurred in May 2022?

**Expected behavior**

AskMyData should identify the rental data, apply the requested May 2022 date
range, and return the number of matching rentals.

**Reference SQL**

```sql
SELECT COUNT(*) AS rental_count
FROM public.rental
WHERE rental_date >= DATE '2022-05-01'
  AND rental_date < DATE '2022-06-01';
```

**Reference result**

`1156`

**AskMyData answer**

> 1156 rentals occurred in May 2022.

**Outcome**

Pass.

**Observations**

The answer exactly matches the PostgreSQL reference result.

AskMyData correctly interpreted the requested month and year and applied the
appropriate temporal filtering to the rental data.

#### BENCH-QA-004 — Multi-table join

**Question**

> How many customers live in Canada?

**Expected behavior**

AskMyData should identify the relationships between customers, addresses, cities,
and countries, then return the number of customers located in Canada.

**Reference SQL**

```sql
SELECT COUNT(*) AS customer_count
FROM public.customer AS customer
JOIN public.address AS address
  ON customer.address_id = address.address_id
JOIN public.city AS city
  ON address.city_id = city.city_id
JOIN public.country AS country
  ON city.country_id = country.country_id
WHERE country.country = 'Canada';
```

**Reference result**

`5`

**AskMyData answer**

> There are 5 customers who live in Canada.

**Outcome**

Pass.

**Observations**

The answer exactly matches the PostgreSQL reference result.

AskMyData successfully resolved the multi-table relationship from customers
through addresses and cities to countries.

#### BENCH-QA-005 — Top-N aggregation across multiple tables

**Question**

> Which 5 film categories generated the most revenue?

**Expected behavior**

AskMyData should associate payments with rented films and their categories,
aggregate revenue by category, rank the categories by total revenue, and return
the five highest-revenue categories.

**Reference SQL**

```sql
SELECT
    category.name AS category,
    SUM(payment.amount) AS total_revenue
FROM public.payment AS payment
JOIN public.rental AS rental
    ON payment.rental_id = rental.rental_id
JOIN public.inventory AS inventory
    ON rental.inventory_id = inventory.inventory_id
JOIN public.film_category AS film_category
    ON inventory.film_id = film_category.film_id
JOIN public.category AS category
    ON film_category.category_id = category.category_id
GROUP BY category.category_id, category.name
ORDER BY total_revenue DESC
LIMIT 5;
```

**Reference result**

| Rank | Category | Total revenue |
|---:|---|---:|
| 1 | Sports | 5314.21 |
| 2 | Sci-Fi | 4756.98 |
| 3 | Animation | 4656.30 |
| 4 | Drama | 4587.39 |
| 5 | Comedy | 4383.58 |

**AskMyData answer**

> The top 5 categories by total revenue are:
> 1. Sports — 5314.21
> 2. Sci-Fi — 4756.98
> 3. Animation — 4656.30
> 4. Drama — 4587.39
> 5. Comedy — 4383.58

**Outcome**

Pass.

**Observations**

The answer exactly matches the PostgreSQL reference result.

AskMyData correctly combined data across multiple related tables, aggregated
payment amounts by film category, ordered the aggregated results by revenue,
and returned the requested top five categories.

Both the ranking and all five revenue amounts are correct.

#### BENCH-QA-006 — Ambiguous question requiring clarification

**Question**

> Which customers are the best?

**Expected behavior**

AskMyData should recognize that "best" does not define a measurable criterion
and request clarification before generating and executing a query.

A valid clarification could ask whether "best" means, for example, customers
with the highest total spending or customers with the highest number of rentals.

**Reference SQL**

Not applicable. The question is intentionally ambiguous and should not be
executed before clarification.

**Reference result**

Not applicable.

**AskMyData answer**

> Here are the top 10 customers by total_spent from the query:
>
> 1. customer_id 526 — KARL SEAL — total_spent 221.55 — payment_count 45 — last_payment_date 2022-07-26 03:16:46.973956 (Europe/Paris)
> 2. customer_id 148 — ELEANOR HUNT — total_spent 216.54 — payment_count 46 — last_payment_date 2022-07-27 09:38:02.694609 (Europe/Paris)
> 3. customer_id 144 — CLARA SHAW — total_spent 195.58 — payment_count 42 — last_payment_date 2022-07-26 00:37:40.765863 (Europe/Paris)
> 4. customer_id 178 — MARION SNYDER — total_spent 194.61 — payment_count 39 — last_payment_date 2022-07-20 02:50:07.758016 (Europe/Paris)
> 5. customer_id 137 — RHONDA KENNEDY — total_spent 194.61 — payment_count 39 — last_payment_date 2022-07-25 17:04:45.081153 (Europe/Paris)
> 6. customer_id 459 — TOMMY COLLAZO — total_spent 186.62 — payment_count 38 — last_payment_date 2022-07-26 20:57:33.068655 (Europe/Paris)
> 7. customer_id 469 — WESLEY BULL — total_spent 177.60 — payment_count 40 — last_payment_date 2022-07-16 11:23:21.946558 (Europe/Paris)
> 8. customer_id 468 — TIM CARY — total_spent 175.61 — payment_count 39 — last_payment_date 2022-07-18 22:18:20.404598 (Europe/Paris)
> 9. customer_id 236 — MARCIA DEAN — total_spent 175.58 — payment_count 42 — last_payment_date 2022-07-23 16:27:34.362035 (Europe/Paris)
> 10. customer_id 181 — ANA BRADLEY — total_spent 174.66 — payment_count 34 — last_payment_date 2022-07-26 21:51:28.229227 (Europe/Paris)

**Initial outcome**

Fail.

**Initial observations**

AskMyData did not request clarification for the ambiguous term "best".

Instead, it implicitly interpreted "best" as highest total spending and returned
the top 10 customers ranked by `total_spent`.

This interpretation was plausible, but it was selected without user
confirmation even though other reasonable interpretations exist, such as
highest number of rentals or another business criterion.

The expected FR-AI-008 / UC-05 behavior is to request clarification before
executing the query.

**Retest after fix**

The scenario was rerun in a new conversation.

For the original question:

> Which customers are the best?

AskMyData responded:

> By “best” do you mean customers with the highest total payments (most
> spending), the most rentals (most frequent renters), or the most recent
> activity? And how many top customers should I return?

No arbitrary business criterion was selected.

The user then answered:

> Highest total payments, top 5

AskMyData returned:

> Top 5 customers by total payments:
>
> 1. customer_id 526 — KARL SEAL — KARL.SEAL@sakilacustomer.org — total_payments: 221.55
> 2. customer_id 148 — ELEANOR HUNT — ELEANOR.HUNT@sakilacustomer.org — total_payments: 216.54
> 3. customer_id 144 — CLARA SHAW — CLARA.SHAW@sakilacustomer.org — total_payments: 195.58
> 4. customer_id 137 — RHONDA KENNEDY — RHONDA.KENNEDY@sakilacustomer.org — total_payments: 194.61
> 5. customer_id 178 — MARION SNYDER — MARION.SNYDER@sakilacustomer.org — total_payments: 194.61

The ranking and all five payment totals exactly matched the PostgreSQL reference
result.

The clarification response also preserved the plural intent of the original
question instead of silently reducing the result to a single customer.

**Outcome after fix**

Pass.

### BENCH-QA-007 — Conversation context

**Question**

Following BENCH-QA-006 in the same conversation:

> And which one of them made the most payments?

**Expected behavior**

AskMyData should resolve "them" using the customers returned in the immediately
preceding answer and determine which of those customers has the highest payment
count.

**Reference SQL**

The customer identified by AskMyData was verified directly against PostgreSQL:

```sql
SELECT
    c.customer_id,
    c.first_name,
    c.last_name,
    COUNT(p.payment_id) AS payment_count,
    SUM(p.amount) AS total_spent,
    MAX(p.payment_date) AS last_payment_date
FROM public.customer AS c
JOIN public.payment AS p
    ON p.customer_id = c.customer_id
WHERE c.customer_id = 148
GROUP BY c.customer_id, c.first_name, c.last_name;
```

**Reference result**

- Customer: `148` — ELEANOR HUNT
- Payment count: `46`
- Total spent: `216.54`
- Last payment date: `2022-07-27 09:38:02.694609+02`

**AskMyData answer**

> ELEANOR HUNT (customer_id 148) made the most payments: 92 payments totaling
> 433.08; last payment on 2022-07-27 09:38:02.694609 (Europe/Paris).

**Outcome**

Fail.

**Observations**

AskMyData successfully resolved the conversational reference "them" and
identified ELEANOR HUNT (customer 148) as the correct customer.

However, the quantitative values returned for that customer are incorrect:

- payment count: `92` instead of `46`;
- total spent: `433.08` instead of `216.54`;
- last payment date: correct.

Both incorrect aggregate values are exactly twice their reference values. This
suggests that rows may have been duplicated during query generation, for
example through an unnecessary join, but the generated SQL is not currently
available to confirm the cause.

Conversation context resolution itself appears successful. The failure is
therefore related to the quantitative result of the generated query rather
than to resolving the conversational reference.

#### BENCH-QA-008 — Filtered multi-table aggregation

**Question**

> How much revenue was generated by Sports films in May 2022?

**Expected behavior**

AskMyData should identify revenue as payment amounts, restrict the data to the
Sports film category and May 2022, and return the corresponding total revenue.

**Reference SQL**

```sql
SELECT SUM(payment.amount) AS total_revenue
FROM public.payment AS payment
JOIN public.rental AS rental
    ON payment.rental_id = rental.rental_id
JOIN public.inventory AS inventory
    ON rental.inventory_id = inventory.inventory_id
JOIN public.film_category AS film_category
    ON inventory.film_id = film_category.film_id
JOIN public.category AS category
    ON film_category.category_id = category.category_id
WHERE category.name = 'Sports'
  AND payment.payment_date >= DATE '2022-05-01'
  AND payment.payment_date < DATE '2022-06-01';
```

**Reference result**

`888.04`

**AskMyData answer**

> The revenue for Sports films in May 2022 was 878.07.

**Outcome**

Fail.

**Observations**

The AskMyData result does not match the PostgreSQL reference result.

- PostgreSQL reference: `888.04`
- AskMyData result: `878.07`
- Difference: `-9.97`

A second reference query using `rental_date` instead of `payment_date` returned
`333.24`, so the discrepancy is not explained by choosing the rental date as
the temporal criterion.

Additional checks of common date-boundary variants also did not reproduce
`878.07`.

The generated SQL is not currently persisted or available through execution
trace metadata, so the exact cause cannot yet be determined.

#### BENCH-QA-009 — Average spending per customer

**Question**

> What is the average amount spent per customer?

**Expected behavior**

AskMyData should interpret "amount spent per customer" as each customer's total
spending and return the average of those customer-level totals.

**Reference SQL**

```sql
SELECT
    SUM(payment.amount) AS total_revenue,
    COUNT(DISTINCT payment.customer_id) AS paying_customers,
    SUM(payment.amount) / COUNT(DISTINCT payment.customer_id)
        AS average_spent_per_customer
FROM public.payment AS payment;
```

**Reference result**

- Total revenue: `67416.51`
- Paying customers: `599`
- Average spent per customer: `112.5484307178631052`
- Rounded to two decimal places: `112.55`

**AskMyData answer**

> The average amount spent per customer is 112.5484307178631052 (≈ 112.55).

**Outcome**

Pass.

**Observations**

The answer exactly matches the PostgreSQL reference result.

AskMyData correctly interpreted the question as average total spending per
customer and returned both the exact value and a user-friendly rounded value.

### 4.3 Conversation Context

#### BENCH-QA-010 — Simple conversational follow-up

**Questions**

> How many customers live in Canada?

Follow-up:

> And how many of them are active?

**Expected behavior**

AskMyData should preserve the conversational context and understand that
"them" refers to customers living in Canada.

**Reference SQL**

```sql
SELECT
    COUNT(*) AS active_customers_in_canada
FROM public.customer AS customer
JOIN public.address AS address
    ON customer.address_id = address.address_id
JOIN public.city AS city
    ON address.city_id = city.city_id
JOIN public.country AS country
    ON city.country_id = country.country_id
WHERE country.country = 'Canada'
  AND customer.active = 1;
```

**Reference result**

`5`

**AskMyData answers**

> There are 5 customers living in Canada.

> There are 5 active customers in Canada.

**Outcome**

Pass.

**Observations**

AskMyData correctly preserved the conversational context and resolved "them"
as the customers living in Canada.

The follow-up result exactly matches the PostgreSQL reference result.

This indicates that the failure observed in BENCH-QA-007 is not a general
failure of conversational context handling. The issue appears to be specific
to the query generated for that more complex follow-up.

### 4.4 Security and Scope Enforcement

#### BENCH-QA-011 — Catalog Scope enforcement

**Project scope**

A dedicated limited-scope Pagila project was created with only:

- `public.customer`
- `public.address`
- `public.city`
- `public.country`

`public.payment` was intentionally excluded from the project's Catalog Scope.

**Question**

> What is the total amount of all payments?

**Expected behavior**

AskMyData must not execute a query accessing `public.payment`, because the
table is outside the project's Catalog Scope.

If generated SQL references the excluded table, SQL validation must reject the
query before execution.

**Observed behavior**

The generated SQL was rejected during validation.

The QuestionRun failed with:

`SQLValidationError: SQL query references a table outside the catalog scope.`

Execution traces:

- `sql_generation` — completed;
- `sql_validation` — completed;
- `query_execution` — not reached.

No SQL query accessing the out-of-scope table was executed.

From the user interface, the thinking indicator stopped after processing, but
no assistant response or error message was displayed.

**Outcome**

Pass — Catalog Scope enforcement.

**Observations**

The Catalog Scope security boundary worked as expected in the real application
workflow: an out-of-scope table reference was rejected before query execution.

The scenario therefore passes for the behavior it is intended to validate:
Catalog Scope enforcement.

A user-facing error-handling defect was initially observed: the failed pipeline
did not provide persistent feedback explaining why the question could not be
answered. This defect was tracked as BENCH-BUG-005.

After the fix, the scenario was rerun against the real application. When the
generated SQL referenced `public.payment`, SQL validation again rejected the
query before execution. AskMyData then displayed the following persistent
assistant message:

> I can't answer this question with the data available in this project.

The message remained part of the conversation after a page reload, while the
QuestionRun remained failed and the technical validation error was not exposed
to the user.

BENCH-BUG-005 is therefore resolved. Catalog Scope enforcement remains
successful.

### 4.5 Unsupported and Semantically Unavailable Questions

#### BENCH-QA-012 — Question requiring unavailable business information

**Question**

> What is the profit generated by each film category?

**Expected behavior**

AskMyData should recognize that the available data does not provide the cost
information required to calculate profit.

It should explain that profit cannot be determined from the available data,
rather than substituting another metric such as revenue.

**Reference result**

No valid reference result can be calculated from the available Pagila data.

**AskMyData answer**

> Here are the profits by film category (ordered by profit descending):
>
> - Sports: 5314.21
> - Sci-Fi: 4756.98
> - Animation: 4656.30
> - Drama: 4587.39
> - Comedy: 4383.58
> - Action: 4375.85
> - New: 4361.57
> - Games: 4281.33
> - Foreign: 4270.67
> - Family: 4226.07
> - Documentary: 4217.52
> - Horror: 3722.54
> - Children: 3655.55
> - Classics: 3639.59
> - Travel: 3549.64
> - Music: 3417.72

**Outcome**

Fail.

**Observations**

AskMyData returned revenue values and labeled them as profit.

For example, the values for Sports (`5314.21`), Sci-Fi (`4756.98`) and
Animation (`4656.30`) match the revenue values observed in BENCH-QA-005.

The available Pagila data does not contain the business cost information
required to calculate actual profit.

AskMyData should therefore have indicated that the requested metric could not
be calculated instead of silently substituting revenue for profit.

### 4.6 Relationship Resolution

#### BENCH-QA-013 — Many-to-many relationship and Top-N aggregation

**Question**

> Which 5 actors appeared in the most films?

**Expected behavior**

AskMyData should use the many-to-many relationship between actors and films
through `film_actor`, count the films associated with each actor, and return
the five actors with the highest film counts.

**Reference SQL**

```sql
SELECT
    actor.actor_id,
    actor.first_name,
    actor.last_name,
    COUNT(DISTINCT film_actor.film_id) AS film_count
FROM public.actor AS actor
JOIN public.film_actor AS film_actor
    ON actor.actor_id = film_actor.actor_id
GROUP BY actor.actor_id, actor.first_name, actor.last_name
ORDER BY film_count DESC, actor.actor_id
LIMIT 5;
```

**Reference result**

1. GINA DEGENERES — `42`
2. WALTER TORN — `41`
3. MARY KEITEL — `40`
4. MATTHEW CARREY — `39`
5. SANDRA KILMER — `37`

**AskMyData answer**

> The five actors with the most film appearances are:
> 1. GINA DEGENERES — 42 films (actor_id 107)
> 2. WALTER TORN — 41 films (actor_id 102)
> 3. MARY KEITEL — 40 films (actor_id 198)
> 4. MATTHEW CARREY — 39 films (actor_id 181)
> 5. SANDRA KILMER — 37 films (actor_id 23)

**Outcome**

Pass.

**Observations**

The answer exactly matches the PostgreSQL reference result.

AskMyData correctly followed the many-to-many relationship between `actor`
and films through `film_actor`, performed the aggregation, and returned the
correct Top 5 ordering and film counts.

---

## 5. Issues Discovered

### 5.1 Functional Defects

#### BENCH-BUG-001 — Semantic enrichment is bypassed by catalog views

**Area:** Knowledge Catalog generation

**Observation**

A Pagila catalog was successfully generated with 22 tables and 129 columns,
but contained no business descriptions and no business synonyms.

**Root cause**

The catalog build and regeneration views instantiate `CatalogService`
directly:

`CatalogService().build_for_project(project)`

This bypasses the application service factory `create_catalog_service()`,
which injects the configured `SemanticEnricher` and LLM provider.

As a result, structural catalog generation succeeds but semantic enrichment
is never executed through the real HTTP workflow.

**Resolution**

Catalog build and regeneration views were updated to use the application
composition factory `create_catalog_service()` instead of instantiating
`CatalogService` directly.

This ensures that the configured `SemanticEnricher` and LLM provider are used
during real HTTP catalog generation workflows.

**Validation**

The Pagila catalog was regenerated through the application UI after the fix.

- Catalog version: v2
- Status: Ready
- Tables: 22
- Columns: 129
- Business synonyms: 161
- Business descriptions: generated

Semantic metadata was successfully generated and persisted.

**Status:** Fixed and validated

#### BENCH-BUG-002 — Ambiguous business criteria do not trigger clarification

**Area:** Natural-language query pipeline / clarification

**Related requirements:** FR-AI-008, UC-05

**Initial observation**

When asked:

> Which customers are the best?

AskMyData did not request clarification. It interpreted "best" as highest total
spending and returned the top 10 customers ranked by `total_spent`.

**Expected behavior**

When a question contains an ambiguous business criterion that cannot be
resolved from the Knowledge Catalog or conversation context, AskMyData should
request clarification before generating and executing SQL.

The application should not invent a business interpretation when different
reasonable interpretations would materially change the query.

Explicit constraints from the question and conversation history, including
singular/plural intent, requested counts, filters, date ranges, and ordering,
should also be preserved.

**Resolution**

The SQL generation prompt now explicitly instructs the model to:

- request clarification when different reasonable interpretations would
  materially change the query;
- avoid clarification when the intended query can be determined
  unambiguously from the available context;
- preserve explicit constraints from the question and conversation history;
- return multiple ranked results when the user requests plural results without
  silently reducing the request to a single result.

The SQL generation prompt now explicitly describes the two supported response
paths: either a SQL generation result or a clarification request.

**Validation**

The SQLGenerator test suite contains dedicated coverage for the clarification
instructions and preservation of question constraints.

The real Pagila scenario was rerun in a new conversation. AskMyData requested
clarification for both the meaning of "best" and the desired number of
customers.

After the user answered:

> Highest total payments, top 5

AskMyData returned five customers ranked by total payments. The ranking and all
five totals exactly matched the PostgreSQL reference result.

**Status:** Resolved

#### BENCH-BUG-003 — Follow-up query returns duplicated aggregate values

**Area:** Natural-language query pipeline / conversation context / SQL generation

**Related requirements:** FR-CONV-002, FR-AI-003, FR-AI-005, FR-AI-007, UC-06

**Observation**

After AskMyData returned a list of customers containing ELEANOR HUNT with
46 payments and 216.54 total spent, the following contextual question was asked:

> And which one of them made the most payments?

AskMyData correctly identified ELEANOR HUNT (customer 148), but returned
92 payments and 433.08 total spent.

Direct PostgreSQL verification returned 46 payments and 216.54 total spent.

The incorrect payment count and total spent are both exactly twice the
reference values.

**Expected behavior**

AskMyData should preserve conversation context while producing aggregate values
that match the underlying PostgreSQL data.

**Suspected cause**

The exact duplication of multiple aggregate values suggests that the generated
query may duplicate payment rows, potentially through an unnecessary join.

The generated SQL is not currently persisted or exposed, so the root cause has
not yet been confirmed.

**Status:** Confirmed — root cause not yet identified

#### BENCH-BUG-004 — Complex filtered aggregation returns incorrect result

**Area:** Natural-language query pipeline / SQL generation / result accuracy

**Related requirements:** FR-AI-003, FR-AI-005, FR-AI-007

**Observation**

When asked:

> How much revenue was generated by Sports films in May 2022?

AskMyData returned `878.07`.

Direct PostgreSQL verification using payment dates returned `888.04`.

Alternative interpretations and common date-boundary variants tested during
diagnosis did not reproduce the AskMyData result.

**Expected behavior**

AskMyData should return an aggregate value consistent with the underlying
PostgreSQL data and the selected interpretation of the question.

**Root cause**

Not yet identified. The generated SQL is not currently persisted or exposed
through execution trace metadata.

**Status:** Confirmed — root cause not yet identified

#### BENCH-BUG-005 — SQL validation failure produces no user-facing feedback

**Area:** Conversation / query error handling

**Related requirements:** NFR-REL-001, NFR-REL-003

**Initial observation**

When a generated SQL query referenced a table outside the project's Catalog
Scope, the SQL validator correctly rejected the query and the QuestionRun was
marked as failed.

However, the user interface initially provided no persistent assistant response
explaining why the question could not be answered.

**Expected behavior**

A failed query pipeline should terminate gracefully and provide a safe,
informative user-facing message without exposing technical implementation
details.

The rejected SQL must remain unexecuted.

**Resolution**

SQL validation failures are now handled as controlled query failures.

When a `SQLValidationError` occurs:

- the QuestionRun remains `FAILED`;
- the technical error code and message remain recorded on the QuestionRun;
- the rejected SQL is not executed;
- the technical validation detail is not exposed to the user;
- AskMyData creates a persistent assistant message:

> I can't answer this question with the data available in this project.

Unexpected pipeline failures retain their existing behavior and are not
converted into this controlled response.

**Validation**

The fix was validated with:

- dedicated QuestionRun service coverage;
- conversation view coverage;
- the full Docker test suite (371 tests passing);
- a manual rerun of BENCH-QA-011 against the limited-scope Pagila project.

During the manual rerun, an out-of-scope generated query was rejected by SQL
validation and the safe AskMyData response was displayed in the conversation.
The response remained visible after reloading the page.

**Status:** Resolved

#### BENCH-BUG-006 — Unsupported business metric is silently substituted

**Area:** Natural-language query pipeline / semantic interpretation / result validation

**Related requirements:** FR-AI-002, FR-AI-007

**Observation**

When asked for profit by film category, AskMyData returned payment revenue
aggregates and presented them as profit.

The Knowledge Catalog does not provide a valid definition or sufficient data
for calculating profit.

**Expected behavior**

AskMyData must not silently substitute an available metric for a requested
business metric with a different meaning.

When the requested metric cannot be derived from the available catalog and
data, AskMyData should explain that the question cannot be answered with the
available information.

**Status:** Confirmed

### 5.2 Usability Issues

#### BENCH-UX-001 — Bulk table selection

**Area:** Project setup / Data Selection

**Observation**

Selecting a realistic database containing 22 tables requires selecting every table individually.

**Expected improvement**

Provide a schema-level Select all / Deselect all mechanism.

When only some tables are selected, the schema-level control should indicate a partial selection state.

**Status:** Identified

#### BENCH-UX-002 — No progress feedback during catalog generation

**Area:** Knowledge Catalog generation

**Observation**

Semantic catalog generation on a realistic database can take significantly
longer than structural catalog generation.

After submitting the catalog generation or regeneration request, the interface
provides no visual feedback indicating that processing is in progress. The page
therefore appears unresponsive while the request is being processed.

**Expected improvement**

Provide immediate visual feedback after submission, such as:

- disabling the generation/regeneration button;
- displaying a loading indicator;
- displaying a message indicating that the catalog is being generated.

The interface should also prevent accidental duplicate submissions while the
request is in progress.

**Status:** Identified

#### BENCH-UX-003 — No progress feedback during project creation

**Area:** Project creation / Confirmation

**Observation**

After clicking "Create project", the interface provides no indication that
project creation is in progress.

The button remains enabled and there is no loading indicator or processing
message. Because project initialization may include database and catalog
operations, the request can take long enough for the interface to appear
unresponsive.

This also allows the user to click "Create project" multiple times while the
first request is still being processed.

**Expected improvement**

Provide immediate visual feedback after submission:

- disable the "Create project" button;
- display a loading indicator;
- change the button label or display a message indicating that the project is
  being created;
- prevent duplicate submissions while processing is in progress.

**Status:** Identified

---

## 6. Benchmark Summary

The benchmark evaluated the AskMyData MVP against a realistic Pagila
PostgreSQL database containing 22 tables and 129 discovered columns.

Thirteen query scenarios and one catalog-generation scenario were evaluated.

The benchmark confirmed successful behavior for:

- catalog discovery and semantic enrichment after BENCH-BUG-001 resolution;
- simple counts and aggregations;
- temporal filtering;
- multi-table joins;
- Top-N aggregations;
- many-to-many relationship traversal;
- average calculations;
- simple conversational follow-ups;
- Catalog Scope enforcement.

The benchmark also identified several functional defects:

- ambiguous business criteria may be interpreted without clarification;
- a complex contextual query returned duplicated aggregate values;
- a filtered multi-table aggregation returned an incorrect result;
- SQL validation failures can terminate without user-facing feedback;
- unavailable business metrics may be silently substituted with different
  available metrics.

Three usability issues were also identified around bulk table selection and
progress feedback for long-running operations.

The benchmark therefore confirms that the core MVP query pipeline works across
a range of realistic analytical questions, while also identifying semantic
reliability and error-handling issues that should be addressed before the MVP
is considered fully validated.
