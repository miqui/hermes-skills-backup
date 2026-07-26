---
name: sql-fundamentals
description: "Use when writing, reviewing, debugging, teaching, or optimizing relational SQL queries and schemas across common SQL databases. Covers SELECT/WHERE/JOIN/GROUP BY, CTEs, windows, constraints, normalization, indexes, transactions, NULL semantics, safe parameterization, and dialect-aware verification."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [sql, database, relational-databases, queries, schema-design, postgres, mysql, sqlite]
    related_skills: [node-backend, spring-boot-engineer, code-performance-engineering, requesting-code-review, systematic-debugging]
---

# SQL Fundamentals

## Overview

Use this skill for practical relational SQL work: reading and writing queries, reviewing query correctness, modeling tables, debugging wrong results, making performance-sensitive changes, and explaining SQL concepts clearly. The focus is durable SQL fundamentals that transfer across PostgreSQL, MySQL, SQLite, SQL Server, and cloud query engines, while still checking the actual dialect before relying on engine-specific behavior.

This skill is intentionally framework-neutral. When the task lives inside a runtime or ORM, pair it with the appropriate implementation skill:

- `node-backend` for Prisma, TypeORM, Node.js service layers, and API persistence boundaries
- `spring-boot-engineer` for Spring Data JPA, Hibernate, repositories, transactions, and Flyway migrations
- `code-performance-engineering` for evidence-first query performance work, benchmarks, plans, and regression checks
- `requesting-code-review` for pre-commit security and quality review, especially SQL injection checks
- `systematic-debugging` when SQL behavior is failing and root cause is not yet understood

## When to Use

Use this skill when the task involves:

- Writing or reviewing SQL queries
- Explaining SQL fundamentals or teaching query construction
- Debugging wrong rows, missing rows, duplicate rows, slow queries, or unexpected `NULL` behavior
- Designing relational tables, primary keys, foreign keys, constraints, and many-to-many join tables
- Choosing between joins, subqueries, CTEs, and window functions
- Aggregating data with `GROUP BY`, `HAVING`, and aggregate functions
- Adding, reviewing, or reasoning about indexes
- Reading query plans with `EXPLAIN` or engine-specific explain tools
- Reviewing transactions, ACID guarantees, locking, isolation, idempotency, and consistency risks
- Checking that application SQL uses parameterized queries instead of string interpolation
- Translating ORM query intent into actual SQL behavior

Do not use this skill as the only guide when:

- The work is primarily framework implementation; pair with the runtime/framework skill
- The database is non-relational or document-only, unless SQL-like query semantics are the issue
- The task is exclusively AWS Athena/data lake execution; use `aws-querying-data-lake` and pair this only for SQL concepts
- The task is only performance methodology; use `code-performance-engineering` as the primary driver

## Core Workflow

### 1. Identify the engine and dialect

Before relying on syntax or behavior, determine the actual database engine and version when possible:

- PostgreSQL
- MySQL or MariaDB
- SQLite
- SQL Server
- Oracle
- DuckDB
- Presto/Trino/Athena
- BigQuery/Snowflake/Redshift

Dialect differences matter for:

- date/time functions
- string functions
- JSON operators
- upserts
- `LIMIT` / `TOP` / `FETCH`
- identifier quoting
- generated columns
- partial indexes
- window frame defaults
- transaction isolation support
- `NULL` sort ordering
- CTE optimization behavior

If the engine is unknown, write portable SQL where possible and label dialect assumptions explicitly.

### 2. Clarify the result shape

For any query, state or infer:

- the grain: one row per what?
- required columns
- filters and time ranges
- expected row count or cardinality
- whether duplicates are allowed
- sort order
- whether missing related data should be retained or excluded
- whether the query is analytical, transactional, operational, or migration-related

Many SQL bugs come from not knowing the intended grain. For example, “one row per user” and “one row per order” require different join and aggregation choices.

### 3. Build from a small correct query

Prefer an incremental construction path:

1. Start with the base table and filters.
2. Verify row count and sample rows.
3. Add one join at a time.
4. Re-check row count after each join.
5. Add grouping or windowing only after the joined row set is understood.
6. Add ordering and limit last.

When debugging, remove complexity until the incorrect behavior disappears, then add pieces back.

### 4. Verify against data, not just syntax

A query that runs can still be wrong. Verify with:

- sample rows
- row counts before and after joins
- expected edge cases
- null cases
- duplicate detection
- boundary dates
- known fixture records
- query plan for performance-sensitive paths

## Query Fundamentals

### Basic SELECT shape

```sql
SELECT column_a, column_b
FROM table_name
WHERE status = 'active'
ORDER BY created_at DESC
LIMIT 50;
```

Reason about SQL in logical order, not text order:

1. `FROM` / joins
2. `WHERE`
3. `GROUP BY`
4. aggregates
5. `HAVING`
6. window functions
7. `SELECT`
8. `DISTINCT`
9. `ORDER BY`
10. `LIMIT` / `OFFSET`

This order explains why aliases sometimes are not available in `WHERE`, why `HAVING` filters grouped rows, and why windows operate after grouping in many engines.

### Filtering

Use `WHERE` for row-level filters before grouping:

```sql
SELECT id, email
FROM users
WHERE active = true
  AND created_at >= DATE '2026-01-01';
```

Common filter rules:

- Use parentheses when mixing `AND` and `OR`.
- Prefer half-open time intervals: `created_at >= start AND created_at < end`.
- Avoid wrapping indexed columns in functions on hot paths unless a functional index exists.
- Use `IN` for clear finite lists, but be careful with `NULL` inside `IN` / `NOT IN`.

### Sorting and pagination

Always use a deterministic order for pagination:

```sql
SELECT id, created_at, email
FROM users
WHERE created_at >= TIMESTAMP '2026-01-01 00:00:00'
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

For large or mutable datasets, prefer keyset/cursor pagination over deep `OFFSET` pagination:

```sql
SELECT id, created_at, email
FROM users
WHERE (created_at, id) < (:last_created_at, :last_id)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

Dialect note: tuple comparison is well-supported in PostgreSQL but not universal; adapt for the target engine.

## Joins and Relationships

### Join types

Use the join type that matches the relationship and missing-data behavior:

| Join | Keeps unmatched left rows? | Keeps unmatched right rows? | Typical use |
|---|---:|---:|---|
| `INNER JOIN` | No | No | Only rows with matching related data |
| `LEFT JOIN` | Yes | No | Keep base rows even if relation is missing |
| `RIGHT JOIN` | No | Yes | Rare; often rewrite as left join |
| `FULL OUTER JOIN` | Yes | Yes | Reconciliation between two datasets |
| `CROSS JOIN` | N/A | N/A | Intentional Cartesian product |
| self join | Depends | Depends | Compare rows in same table |

Example:

```sql
SELECT u.id, u.email, o.id AS order_id
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE u.active = true;
```

### Filter placement with outer joins

Be careful: filtering a right-side table in `WHERE` after a `LEFT JOIN` can accidentally turn it into an inner join.

Bad when missing orders should be retained:

```sql
SELECT u.id, o.id
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE o.status = 'paid';
```

Better:

```sql
SELECT u.id, o.id
FROM users u
LEFT JOIN orders o
  ON o.user_id = u.id
 AND o.status = 'paid';
```

### Join explosion checks

Whenever a join unexpectedly increases row count, inspect relationship cardinality:

```sql
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM users u JOIN orders o ON o.user_id = u.id;

SELECT user_id, COUNT(*) AS order_count
FROM orders
GROUP BY user_id
HAVING COUNT(*) > 1
ORDER BY order_count DESC;
```

A join explosion is not necessarily wrong, but it must match the intended grain.

## Aggregation

Use `GROUP BY` when reducing many rows into summary rows:

```sql
SELECT customer_id, COUNT(*) AS order_count, SUM(total_amount) AS revenue
FROM orders
WHERE created_at >= DATE '2026-01-01'
GROUP BY customer_id
HAVING COUNT(*) >= 3
ORDER BY revenue DESC;
```

Rules:

- `WHERE` filters rows before grouping.
- `HAVING` filters groups after aggregation.
- Every selected non-aggregated column must be grouped in standard SQL.
- `COUNT(*)` counts rows; `COUNT(column)` counts non-null values.
- Aggregates usually ignore `NULL`, except `COUNT(*)`.
- Beware one-to-many joins before aggregation; they can inflate sums and counts.

### Conditional aggregation

Portable pattern:

```sql
SELECT
  customer_id,
  COUNT(*) AS total_orders,
  SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) AS paid_orders,
  SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END) AS paid_revenue
FROM orders
GROUP BY customer_id;
```

PostgreSQL supports `FILTER` syntax:

```sql
SELECT
  customer_id,
  COUNT(*) AS total_orders,
  COUNT(*) FILTER (WHERE status = 'paid') AS paid_orders
FROM orders
GROUP BY customer_id;
```

## Subqueries, CTEs, and Set Operations

### Subqueries

Use subqueries when a query needs an intermediate result inline:

```sql
SELECT u.id, u.email
FROM users u
WHERE u.id IN (
  SELECT o.user_id
  FROM orders o
  WHERE o.created_at >= DATE '2026-01-01'
);
```

Watch out for `NOT IN` with `NULL`. Prefer `NOT EXISTS` for anti-joins:

```sql
SELECT u.id, u.email
FROM users u
WHERE NOT EXISTS (
  SELECT 1
  FROM orders o
  WHERE o.user_id = u.id
);
```

### CTEs

Use CTEs to name intermediate steps and make complex queries reviewable:

```sql
WITH paid_orders AS (
  SELECT customer_id, total_amount
  FROM orders
  WHERE status = 'paid'
),
customer_revenue AS (
  SELECT customer_id, SUM(total_amount) AS revenue
  FROM paid_orders
  GROUP BY customer_id
)
SELECT customer_id, revenue
FROM customer_revenue
WHERE revenue >= 1000
ORDER BY revenue DESC;
```

CTEs improve clarity, but engine behavior differs. In some databases, CTEs may be optimization fences or materialized unless hinted otherwise. Check the target engine for performance-sensitive queries.

### Set operations

Use set operations when combining compatible result sets:

```sql
SELECT email FROM newsletter_signups
UNION
SELECT email FROM customers;
```

Rules:

- `UNION` removes duplicates.
- `UNION ALL` keeps duplicates and is usually faster.
- `INTERSECT` returns rows present in both sets.
- `EXCEPT` / `MINUS` returns rows in one set but not the other.
- Each branch must return compatible column counts and types.

## Window Functions

Window functions compute values across related rows without collapsing the row set.

```sql
SELECT
  customer_id,
  order_id,
  created_at,
  total_amount,
  ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC, order_id DESC
  ) AS order_rank
FROM orders;
```

Common uses:

- de-duplication: `ROW_NUMBER() OVER (PARTITION BY key ORDER BY updated_at DESC)`
- running totals: `SUM(amount) OVER (ORDER BY created_at)`
- moving averages
- percent of total
- previous/next row comparisons with `LAG` / `LEAD`
- top-N per group

Example: latest order per customer:

```sql
WITH ranked_orders AS (
  SELECT
    o.*,
    ROW_NUMBER() OVER (
      PARTITION BY customer_id
      ORDER BY created_at DESC, id DESC
    ) AS rn
  FROM orders o
)
SELECT *
FROM ranked_orders
WHERE rn = 1;
```

Always specify deterministic `ORDER BY` columns inside windows when rank/order matters.

## NULL Semantics

SQL `NULL` means unknown or missing, not an empty string or zero. SQL uses three-valued logic: true, false, and unknown.

Important rules:

- `column = NULL` is not true; use `column IS NULL`.
- `column <> NULL` is not true; use `column IS NOT NULL`.
- `WHERE` only keeps rows where the predicate is true; false and unknown are filtered out.
- `COUNT(column)` ignores nulls; `COUNT(*)` does not.
- `SUM`, `AVG`, `MIN`, and `MAX` generally ignore nulls.
- `NOT IN` can behave unexpectedly if the subquery/list contains nulls.

Use `COALESCE` to provide defaults deliberately:

```sql
SELECT id, COALESCE(display_name, email, 'Unknown') AS label
FROM users;
```

Do not hide important missing data with `COALESCE` unless the default has correct business meaning.

## Schema and Relational Modeling

### Keys and constraints

Use constraints to make invalid states unrepresentable:

```sql
CREATE TABLE customers (
  id BIGINT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
  id BIGINT PRIMARY KEY,
  customer_id BIGINT NOT NULL REFERENCES customers(id),
  status VARCHAR(30) NOT NULL,
  total_amount NUMERIC(12, 2) NOT NULL CHECK (total_amount >= 0),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Modeling defaults:

- Use primary keys for stable row identity.
- Use foreign keys for referential integrity unless the system has a deliberate reason not to.
- Use `NOT NULL` when absence is invalid.
- Use `UNIQUE` constraints for business uniqueness.
- Use `CHECK` constraints for simple invariants.
- Use many-to-many join tables with a composite uniqueness rule.

Example many-to-many table:

```sql
CREATE TABLE user_roles (
  user_id BIGINT NOT NULL REFERENCES users(id),
  role_id BIGINT NOT NULL REFERENCES roles(id),
  assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, role_id)
);
```

### Normalization

Normalize by default until there is a measured reason not to:

- First normal form: values are atomic; no repeating groups in a single column.
- Second normal form: non-key columns depend on the whole key.
- Third normal form: non-key columns depend on the key, not other non-key columns.

Practical guidance:

- Avoid duplicating mutable facts across tables.
- Put relationships in join tables instead of comma-separated ID lists.
- Use lookup/reference tables when values have metadata or lifecycle.
- Consider denormalization only for read performance, reporting, caching, or immutable snapshots, and document the source of truth.

## Index Fundamentals

Indexes speed up reads by giving the database an access path, but they cost storage and slow writes. Add indexes for real query patterns, not guesses.

Good candidates:

- foreign key columns used in joins
- columns used in frequent selective filters
- columns used in common sort orders
- composite indexes matching multi-column filters and ordering
- uniqueness constraints that enforce business rules

Example:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

Index review questions:

- Which query is this index for?
- Does column order match equality filters, range filters, and sort order?
- Is the predicate selective enough to help?
- Is there an existing index that already covers this query?
- What is the write/storage cost?
- Did `EXPLAIN` show the expected plan change?

### Query plans

Use engine-specific explain tools:

- PostgreSQL: `EXPLAIN (ANALYZE, BUFFERS)` for real execution evidence
- MySQL: `EXPLAIN`, `EXPLAIN ANALYZE` where supported
- SQLite: `EXPLAIN QUERY PLAN`
- SQL Server: actual execution plan / `SET STATISTICS IO, TIME ON`

For performance-sensitive work, capture before/after evidence and pair with `code-performance-engineering`.

## Transactions and Consistency

Transactions group work so it succeeds or fails as a unit.

ACID basics:

- Atomicity: all-or-nothing
- Consistency: constraints and invariants are preserved
- Isolation: concurrent transactions do not interfere beyond the selected isolation level
- Durability: committed data survives crashes according to the database guarantees

Typical transfer pattern:

```sql
BEGIN;

UPDATE accounts
SET balance = balance - 100
WHERE id = :sender_id
  AND balance >= 100;

UPDATE accounts
SET balance = balance + 100
WHERE id = :receiver_id;

COMMIT;
```

Application code should check affected row counts and handle rollback on failure.

### Isolation and locking

Isolation levels vary by engine, but common concepts include:

- read committed
- repeatable read
- serializable
- row locks
- deadlocks
- optimistic locking with version columns
- pessimistic locking with `SELECT ... FOR UPDATE` where supported

Use transactions intentionally around multi-step invariants: balances, inventory, uniqueness races, status transitions, and idempotent event handling.

## Safe SQL and Injection Prevention

Never build SQL by concatenating or interpolating untrusted input.

Bad:

```python
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

Good:

```python
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
```

Parameter syntax varies by driver:

- SQLite/Python: `?` or named parameters depending on library
- psycopg/PostgreSQL: `%s` or driver-specific parameter APIs
- node-postgres: `$1`, `$2`
- JDBC: `?` with prepared statements
- Prisma/ORMs: use query builders or safe raw-query APIs

Rules:

- Parameterize values.
- Do not parameterize identifiers directly; validate identifiers against an allowlist.
- Avoid unsafe raw SQL escape hatches in ORMs.
- Keep secrets and PII out of logs.
- Review migration scripts and admin queries with the same care as app queries.

## Dialect Notes

### PostgreSQL

Strengths:

- strong CTE/window support
- rich indexing options
- `RETURNING`
- `ON CONFLICT` upserts
- JSONB support
- partial and expression indexes

Watch for:

- `NULLS FIRST/LAST` sort behavior
- transaction isolation details
- CTE materialization changes across versions
- case-sensitive quoted identifiers

### MySQL / MariaDB

Watch for:

- SQL mode settings changing strictness
- `LIMIT offset, count` syntax
- historical differences in window/CTE support by version
- `REPLACE` semantics deleting/reinserting rows
- collation/case-sensitivity surprises

### SQLite

Strengths:

- excellent embedded database
- simple local testing
- good modern SQL support in recent versions

Watch for:

- type affinity rather than strict column types unless using newer strict tables
- foreign keys may require enabling depending on context
- concurrency/write-lock behavior
- differences from production engines if tests use SQLite but production uses PostgreSQL/MySQL

### SQL Server

Watch for:

- `TOP` / `OFFSET FETCH` syntax
- `MERGE` caveats
- identifier quoting with brackets or quoted identifiers
- transaction and locking behavior
- date/time function differences

## Review Checklist

When reviewing a SQL change, check:

- [ ] The intended grain is clear
- [ ] The query uses the correct base table
- [ ] Filters apply before or after joins/grouping intentionally
- [ ] Join types preserve or discard unmatched rows correctly
- [ ] One-to-many joins do not accidentally inflate aggregates
- [ ] `NULL` behavior is intentional
- [ ] Time range boundaries are correct and timezone-aware where needed
- [ ] Aggregates use `COUNT(*)`, `COUNT(column)`, `SUM`, `AVG`, etc. appropriately
- [ ] CTEs/subqueries improve clarity without hiding performance problems
- [ ] Window functions have deterministic partition/order clauses
- [ ] Result ordering is deterministic when pagination or top-N is involved
- [ ] Indexes match real filters, joins, or sort patterns
- [ ] Query plan evidence exists for performance-sensitive changes
- [ ] Application SQL is parameterized and does not expose injection paths
- [ ] Schema changes use constraints to protect invariants
- [ ] Transactions wrap multi-step consistency changes

## Debugging Wrong Results

Use this sequence:

1. State the expected grain and expected row count range.
2. Run the base table query with only essential filters.
3. Count rows before joins.
4. Add joins one at a time and count after each join.
5. Check for duplicate keys on each side of the join.
6. Move right-table filters from `WHERE` into `ON` when preserving left rows matters.
7. Inspect null values explicitly.
8. Verify date/time boundaries and timezone assumptions.
9. Replace aggregation with raw rows to inspect what is being grouped.
10. Add aggregation back after the raw row set is correct.

Useful checks:

```sql
-- Duplicate key check
SELECT key_column, COUNT(*)
FROM some_table
GROUP BY key_column
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC;

-- Null check
SELECT COUNT(*) AS total_rows,
       COUNT(column_name) AS non_null_rows,
       COUNT(*) - COUNT(column_name) AS null_rows
FROM some_table;

-- Join explosion check
SELECT COUNT(*) FROM table_a;
SELECT COUNT(*) FROM table_a a JOIN table_b b ON b.a_id = a.id;
```

## Performance Triage

Do not optimize blindly. First identify whether the query is actually slow in a representative environment.

Evidence to gather:

- query text with parameters redacted where needed
- engine/version
- table row counts
- relevant indexes
- query plan
- actual runtime and rows returned
- whether slowness is CPU, I/O, lock wait, network, or result-size related

Common causes:

- missing or misordered indexes
- non-selective filters
- functions on indexed columns
- implicit type casts
- leading-wildcard `LIKE` searches
- one-to-many join explosions
- sorting large intermediate results
- deep `OFFSET` pagination
- stale statistics
- locks or long-running transactions

Pair with `code-performance-engineering` for benchmark design, before/after measurements, and regression protection.

## Common Pitfalls

1. **Not defining the grain.** If you do not know what one output row represents, joins and aggregates will drift into accidental behavior.

2. **Using `LEFT JOIN` but filtering the right table in `WHERE`.** This often discards unmatched rows and behaves like an inner join.

3. **Aggregating after a join explosion.** Sums and counts become inflated when the joined row set has a different grain than expected.

4. **Confusing `COUNT(*)` and `COUNT(column)`.** The latter ignores nulls.

5. **Using `NOT IN` with nullable subqueries.** Prefer `NOT EXISTS` unless null behavior is fully controlled.

6. **Assuming query text order is logical execution order.** `WHERE`, grouping, windows, aliases, and `ORDER BY` have specific evaluation semantics.

7. **Relying on SQLite tests to prove PostgreSQL/MySQL behavior.** SQLite is useful, but dialect and concurrency differences can hide production issues.

8. **Adding indexes without a target query.** Every index has write and storage cost; tie indexes to real filters, joins, constraints, or sort patterns.

9. **Treating ORM queries as magic.** Inspect generated SQL when correctness or performance matters.

10. **String-building SQL with user input.** Parameterize values and allowlist identifiers.

11. **Ignoring transaction boundaries.** Multi-step business invariants need explicit transaction design and failure handling.

12. **Using `SELECT *` in application paths.** It couples callers to schema shape, increases I/O, and may expose sensitive fields.

## Verification Checklist

Before calling SQL work complete:

- [ ] The target database engine/dialect is known or assumptions are stated
- [ ] The result grain and expected behavior are clear
- [ ] Query syntax was checked against the actual dialect where possible
- [ ] Sample rows and row counts were inspected for non-trivial queries
- [ ] Join cardinality and duplicate behavior were checked when joins are involved
- [ ] Aggregations were verified against raw rows or known examples
- [ ] `NULL` behavior was considered explicitly
- [ ] Time range and timezone assumptions were verified where relevant
- [ ] Query plan evidence was captured for performance-sensitive changes
- [ ] Parameterization or safe query-building was verified for application SQL
- [ ] Schema changes include constraints and indexes appropriate to the data model
- [ ] Transaction behavior is explicit for multi-step consistency changes
