# Kickoff protocol reference

Use this reference when a user wants a strictly gated design → plan → build workflow.

## Approval phrases to require

Accept only explicit approval such as:
- `Approve Checkpoint 1`
- `Approve Checkpoint 2`
- `Approve Checkpoint 3`
- `Approve Phase 1 write targets`
- `Confirm Phase 2 scope`
- `Approve Phase 2 write target`
- `Approve Phase 2 plan`

Treat these as ambiguous and non-approving until confirmed:
- `proceed`
- `ok`
- `sure`
- `looks good`
- `go ahead`

## Minimal phase sequence

1. **Phase 0** — derive slug, check for existing design doc, inspect docs tree
2. **Phase 1 / Checkpoint 1** — problem, user, assumptions
3. **Phase 1 / Checkpoint 2** — 2–4 options with tradeoffs
4. **Phase 1 / Checkpoint 3** — recommendation, component map, MVP scope, not-doing list, edge cases, explicit user decisions
5. **Phase 1 write gate** — confirm exact design/ADR target paths
6. **Phase 2 scope gate** — restate approved direction in three sentences and confirm no scope shift
7. **Phase 2 write gate** — confirm exact plan path
8. **Phase 2 plan approval** — do not code before this
9. **Phase 3** — one build step at a time, each with a build checkpoint

## Artifact conventions

### Design docs
- Path: `docs/design/<slug>-design.md`
- Contains: problem, target user, assumptions, options, recommendation, component map, MVP scope, not-doing list, edge cases, risks

### ADRs
- Path: `docs/decisions/NNNN-<short-title>.md`
- One ADR per discrete approved decision
- Number sequentially, zero-padded, never reuse a number

### Plans
- Path: `docs/plans/<slug>-plan.md`
- Must link to design doc and governing ADRs
- Must not contain silent TBDs

## Common failure modes

- Starting file writes before the user approves paths
- Treating informal acknowledgment as approval
- Moving from design approval straight into code without the plan gate
- Leaving unresolved implementation choices hidden in file inventory or step descriptions
- Letting build deviations accumulate without opening ADR candidates
