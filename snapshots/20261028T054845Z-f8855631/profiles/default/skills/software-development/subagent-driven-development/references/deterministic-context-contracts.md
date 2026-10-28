# Deterministic context-contract checklist

Use this reference when a task assembles context from validated records for a later evaluator, but must not make a decision yet.

## Preserve a typed boundary under constrained scope

If the approved task cannot modify an existing shared model but needs additional signals:

1. Stop before quietly widening the model or hiding fields in an untyped dictionary.
2. Ask for a contract decision: explicitly amend the shared model, or introduce a dedicated immutable wrapper/result type in the new module.
3. When a wrapper is chosen, retain the original model as a named typed field and expose each additional decision-relevant signal as a typed field or small typed nested dataclass.
4. Keep source IDs, derived booleans, and bounded summaries; do not retain raw history bodies, media bytes, or opaque metadata blobs.

## Specify deterministic semantics, not just field presence

Every derived semantic field needs an explicit, testable rule. In particular:

- A field named `is_recent` must compare stable dataset timestamps against a documented reference timestamp and duration/window; it must not mean merely "has a timestamp" or conflate an independent state such as consent/opt-out with recency.
- Treat a stated duration as an exact elapsed-time bound: compare a full `timedelta` (or equivalent), not truncated integer units such as `timedelta.days`. Test both the inclusive exact boundary (for example, exactly 180d) and an immediately-over-bound value with a fractional remainder (for example, 180d23h) so truncation bugs cannot pass.
- Define invalid/missing timestamp behavior explicitly (`False`, `None`, or a validation error), specify future-relative-to-anchor behavior, and cover each with tests. Anchor time comparisons to a stable record timestamp when the task is deterministic; never use wall-clock time unless the task explicitly requires it.
- For "latest" values, define the source ordering, tie behavior, and aggregation (for example: maximum ISO date; sum all rows on that date). Never use wall-clock time unless the task explicitly requires it.
- For boolean CSV flags, enumerate accepted spellings or validate them. Do not let arbitrary nonempty strings silently mean `True` unless the data contract explicitly says so.

## Historical evidence selection

Write the selection rule before implementation and test it through the public result:

1. Filter to the same principal/user.
2. Choose one best relevance tier rather than mixing weak matches to fill a cap (for example: matching group for group messages, matching business for business messages, then matching sender).
3. Sort selected rows with explicit stable tie-breakers, such as timestamp descending then ID ascending.
4. Enforce a small documented maximum.
5. Surface evidence IDs and bounded event summaries only; return `none` when no eligible history exists.

## Review prompts

Ask the spec reviewer:

- Which public context fields lack a deterministic source/selection rule?
- Does any field name overstate what is actually measured (especially recency, trust, or relevance)?
- Can duplicate source records or ties change output based on input row order?
- Is raw corpus content retained where identifiers or derived summaries would suffice?

Require synthetic tests for missing data, old-vs-recent timestamps, ties, duplicate source records, and no-evidence behavior before accepting the task.
