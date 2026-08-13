# Deterministic evaluator and policy-contract checklist

Load this reference when a task turns assembled context into a classification/action assessment but must remain provider-neutral and must not write final output yet.

## Keep the decision boundary explicit

1. Return the existing typed internal assessment contract; do not create a submission row or output artifact in this phase.
2. Keep signal extraction separate from policy application: expose independent domain/topic, risk, trust, relevance, urgency, and intent signals before deriving an action.
3. An intent such as `action_required` is not an output category. Map only to the allowed submission message-type enum and assert that invariant in tests.
4. Make hard safety precedence explicit and test it: risky scam/spam handling must not be bypassed by user overrides; genuine urgency must not be blindly suppressed by mute/DND.

## Policy mappings are untrusted configuration

- Use a typed immutable default policy and typed per-user overrides.
- Reject unknown top-level/default-rule keys, malformed user mappings, non-string identifiers/topics, and actions outside the allowed action enum. Do not silently ignore a typo in a topic or policy key; either reject it or document an intentional open-topic policy and test it.
- Overrides may change actions only; never allow them to inject arbitrary message types, rationale text, evidence IDs, or bypass hard safety rules.
- State the fixed rule order in the module docstring and test the precedence points, not private helper calls.

## Rationale and media safety

- Reasons must name only material derived signals or trusted metadata. Never copy raw historical text or fabricate OCR, ASR, or image/voice content.
- If a media reference exists without an evaluator adapter, say only that content evaluation is deferred; classification must not infer what the asset depicts or says.
- Pass contextual historical evidence IDs through unchanged (`none` or bounded historical IDs). Never emit incoming IDs as evidence.

## Verification gates

1. TDD: demonstrate RED from an absent/incorrect public evaluator behavior before implementation, then GREEN.
2. Run tests with warnings-as-errors and assert every action/message type/confidence remains in contract.
3. Run a no-output actual-data smoke only after validation succeeds. Report aggregate action/type counts and error counts—never message bodies, rationales, or corpus text.
4. In strict review, ask explicitly whether policy configuration can silently accept ineffective/unrecognized overrides and whether rule precedence matches the documented order.

## Test-integrity gate

- Review the entire touched test file—not only the newly added test names—for vacuous assertions such as `... or True`, unconditional truths, or assertions that test a premise known to be false by design.
- Delete a vacuous assertion rather than neutralizing it. Replace it with a public-API behavior test that would fail if the production contract regressed.
- Do not assume an internal topic vocabulary and the output message-type enum are disjoint: legitimate strings may overlap. For internal-only topic values, drive classification and evaluation end-to-end and assert the terminal output remains in the allowed message-type enum and is not the internal-only literal.
- For rationale privacy, test absence of a synthetic raw-history sentinel phrase, not absence of evidence IDs that a concise rationale may legitimately mention.
