# Checkpoint Template

Use this template when running a strict design → plan → build workflow with explicit approvals.

## Design checkpoint

### Checkpoint N — <title>

- Problem / direction / options for this checkpoint only
- Explicit assumptions or decisions visible here
- No forward progress beyond this checkpoint

Approval prompt:
- `Approve Checkpoint N`
- `Approve Checkpoint N with changes: ...`
- `Do not approve: ...`

## Pre-write gate

Before writing files, confirm exact target paths:
- `docs/design/<slug>-design.md`
- `docs/decisions/0001-...md`
- `docs/plans/<slug>-plan.md`

Approval prompt:
- `Confirm write targets`
- `Confirm write targets with changes: ...`

## Build checkpoint

### Build checkpoint N — <step name>

- Files changed
- Plan fidelity
- Newly surfaced TBDs / ADR candidates
- Tests / validation performed
- Next step

Approval prompt:
- `Confirm step N complete and continue`
- `Step N changes requested: ...`

## Ambiguous approval recovery

If the user says `proceed`, `ok`, or similar in a strict workflow:
1. restate exactly what you believe they are approving
2. ask for explicit confirmation
3. do not continue until that explicit approval arrives
