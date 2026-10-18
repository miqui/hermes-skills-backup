# Data-contract integrity review checklist

Use this reference when implementing or reviewing ingestion and validation for linked participant-facing data.

## Build a relationship inventory from actual schemas

For every input table/record type, list:

| Consumer field | Target | Chain | Severity |
|---|---|---|---|
| `message.media_type` + `message.media_id` | typed media catalog | message → typed catalog → local file | fatal |
| current record `user_id` | users | current record → user | usually fatal when required to evaluate the record |
| historical/context record IDs | lookup tables | context → lookup | commonly warning, if evaluation can continue without context |

Do not infer the inventory from code already written. Derive it from authoritative input headers and the task contract.

## Directional-chain rule

Validation must follow the direction in which the consumer needs the resource.

For a media relationship, all three conditions matter:

1. Both discriminator and ID are present together, or both are absent.
2. The discriminator selects a supported catalog and the ID exists in that catalog.
3. The selected catalog row has a safe path that resolves to an existing local file inside the dataset root.

Checking only catalog rows or only filesystem paths leaves a message-to-catalog bypass.

## Catalog identity integrity

Before building any ID-to-resource lookup, validate the catalog itself:

1. Every catalog ID is present/non-null and valid for its catalog namespace.
2. IDs are unique **within each typed catalog**. The same string may be meaningful in distinct catalogs only if the discriminator keeps those namespaces separate.
3. A duplicate or blank ID is a fatal integrity finding; do not quietly select a row by file order.
4. Build lookups only after counting IDs. Exclude ambiguous IDs (`count != 1`) from consumer resolution so a later row cannot overwrite and mask an earlier broken row.

Do not use a bare dictionary comprehension over unvalidated rows for a consumer-facing lookup: it has last-write-wins semantics. Add synthetic tests for blank IDs, duplicate IDs, and a consumer referencing a broken-then-valid duplicate pair. The result must be fatal regardless of row order.

Use distinct public diagnostics for catalog path states: blank path, path escaping the root, and missing local file. A generic "missing" check name obscures security-relevant escape failures.

## Required synthetic negative cases

Use a minimal temporary fixture. For each relationship family, include at least:

- missing target ID;
- invalid discriminator/type value;
- one half of a required field pair missing;
- traversal path outside the root;
- symlink that resolves outside the root;
- a catalog row whose path is absent/null when a consumer references it;
- at least one warning-class relationship and one fatal-class relationship.

Assert public diagnostics and fatal/warning outcome, not private helper calls.

## Acceptance evidence

Before accepting the task:

1. Require RED evidence for newly added contract edges.
2. Run focused and full tests with warnings escalated if the project supports it.
3. Run a no-output validation smoke check against permitted real input data.
4. Confirm direct smoke commands use the project's actual runtime import configuration; a test-runner-only source path can hide import failures.
5. Ask the independent reviewer: “Which consumer-to-resource links are unchecked, reverse-only, or happy-path-only?”

A zero-error smoke report demonstrates that one dataset is internally consistent. It is not proof that invalid relationships are detected; the synthetic negative suite supplies that proof.
