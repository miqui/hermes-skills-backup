# Identifier Contract Validation for Routing Corpora

Use this when a routing corpus has visually similar identifiers across current messages, history, media, events, or relationship tables.

## Procedure

1. **Measure each identifier column from the participant-facing corpus.** Record the prefix, exact digit width, uniqueness, null count, and example-safe shape. Do not infer width from one sample.
2. **Confirm foreign-key direction with set intersections.** A current incoming ID and a historical evidence ID may look related but belong to disjoint namespaces.
3. **Encode the observed grammar as an anchored contract.** For a verified fixed width, prefer `^msg_\d{3}$` over `^msg_\d+$`.
4. **Test both positive and negative boundaries.** Cover a valid ID, wrong prefix, too few digits, too many digits, and use of one namespace where another is required.
5. **Validate references before policy or model inference.** Missing, malformed, or cross-namespace references are data-contract failures; do not send them into a classifier.

## Example test matrix

| Role | Valid | Reject |
|---|---|---|
| incoming message ID | `msg_023` | `msg_1`, `msg_0001`, `message_0107` |
| historical evidence ID | `message_0107` | `message_1`, `message_99999`, `msg_023` |

## Why this matters

Permissive `\d+` patterns silently admit malformed IDs. They can later corrupt evidence selection or cross-file joins while leaving superficially successful tests. Keep the exact-width tests near the public validation contract so a future regex refactor cannot widen the accepted language unnoticed.
