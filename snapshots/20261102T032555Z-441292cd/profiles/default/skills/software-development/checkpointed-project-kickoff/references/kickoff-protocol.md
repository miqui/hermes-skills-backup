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

### Conditional approvals

Approvals frequently arrive with item-level exceptions:
`Approve Checkpoint 2, but skip item 6 entirely. we will add this later.`

This IS an approval — of the modified scope. Handle it as:
1. Restate exactly what was approved and what was deferred/excluded.
2. Record the deferral in the design doc's not-doing list (with the reason).
3. Carry it into the plan as a deferred/out-of-scope item so it resurfaces later.
4. A descope the user approved deserves its own ADR (e.g. "API keys only, no OIDC").

## Presenting options (Checkpoint 2)

- Number or letter every option (1a/1b, A/B, …) so partial approval and swaps
  are unambiguous ("name the letters you'd swap").
- Anchor each option to a concrete component in the architecture. Abstract
  choices ("language", "state store") confuse users who haven't yet seen which
  box the choice governs. Show the component map first or alongside.
- If the user asks "what does X mean" twice, stop rephrasing the abstraction
  and explain via the concrete component and its data flow.
- Mark one recommendation per item; state honest tradeoffs including resource
  envelopes (e.g. "Redis is production-shaped but won't fit an 8 GB VM budget").

## Mid-checkpoint user notes

Users drop constraints between checkpoints (hardware limits, descopes,
preinstalled tooling). On each note:
1. Acknowledge and absorb immediately — do not re-ask what was already answered.
2. Restate the revised framing/constraints at the top of the NEXT checkpoint.
3. Check whether the note invalidates an earlier assumption; if yes, reopen that
   checkpoint rather than carrying a stale assumption forward.

## Minimal phase sequence

1. **Phase 0** — derive slug, check for existing design doc, inspect docs tree
2. **Phase 1 / Checkpoint 1** — problem, user, assumptions
3. **Phase 1 / Checkpoint 2** — 2–4 options with tradeoffs (numbered/lettered,
   anchored to the component map)
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
- One ADR per discrete approved decision — including approved descopes
- Number sequentially, zero-padded, never reuse a number
- ADR body quotes or paraphrases the user's exact approval wording in the
  Context/Decision sections for provenance

### Plans
- Path: `docs/plans/<slug>-plan.md` (or `docs/plans/YYYY-MM-DD-<slug>-plan.md`)
- Must link to design doc and governing ADRs
- Must not contain silent TBDs
- Deferred items from conditional approvals appear explicitly as out-of-scope/
  deferred, not omitted

## Git and publication

Local commit of approved artifacts ≠ repo publication. Commit approved docs
locally with a conventional message as you go; treat publication (GitHub repo
creation, push, PRs) as a separate, explicitly requested step. On hosts with a
sanctioned git-workflow script, publication goes through that script only at
the user's explicit ask — offer it as its own question ("init GitHub repo?")
rather than bundling it with doc commits.

## Common failure modes

- Starting file writes before the user approves paths
- Treating informal acknowledgment as approval
- Moving from design approval straight into code without the plan gate
- Leaving unresolved implementation choices hidden in file inventory or step descriptions
- Letting build deviations accumulate without opening ADR candidates
- Explaining an abstract option by rephrasing it abstractly instead of
  grounding it in the component it governs
- Losing "we'll add this later" deferrals between checkpoints
