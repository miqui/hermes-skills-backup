---
name: phase-gated-project-delivery
description: Run design → plan → build workflows with explicit human approvals, pre-write path confirmation, and per-step build checkpoints.
tags: [project-delivery, workflow, human-in-the-loop, approvals, checkpoints, design-plan-build]
---

# Phase-Gated Project Delivery

Use this when the user wants a strict human-in-the-loop workflow for software delivery: explicit approvals between design phases, no code before plan approval, controlled artifact writing, and checkpointed implementation.

This skill is especially useful when the user provides a kickoff/process document that governs execution, or when the work is time-boxed but still must follow a deliberate design/plan/build sequence.

## Core rule

When the user supplies a governing workflow, treat it as a contract. Extract the gates first, then operate inside them. Do not compress or skip approval checkpoints just because the implementation path seems obvious.

## What this skill optimizes for

- Clear checkpoint boundaries
- No accidental early coding
- Explicit approval semantics
- Traceable doc/artifact creation
- Tight build-step reporting during implementation
- Honest surfacing of new unknowns or divergences

## Approval semantics

Use **explicit approval only** for checkpoint advancement when the user has asked for strict HITL control.

- Accept: `Approve Checkpoint 2`, `Confirm Phase 2 scope`, `Approve Phase 2 plan`
- Do **not** accept ambiguous shorthand like `proceed`, `ok`, or `sounds good`
- If the user replies ambiguously, restate exactly what you believe they are approving and ask for explicit confirmation before moving on

## Phase structure

### Phase 0 — Governing constraints and discovery

1. Read the governing prompt/process doc and extract:
   - required phases/checkpoints
   - no-code / no-write gates
   - artifact location rules
   - approval semantics
   - out-of-scope items
2. Derive a working project slug.
3. Check whether prior design artifacts already exist for that slug.
4. If prior artifacts exist, summarize them and ask whether to continue from them.
5. If no prior artifacts exist, state that clearly before starting Checkpoint 1.

### Repository-contract intake gate

When a cloned or supplied repository contains `AGENTS.md`, `CONTRIBUTING.md`, a challenge brief, or other agent-facing contract, perform this intake **before** normal discovery or design work:

1. Read the closest governing instruction file in full; also check for nested instruction files before touching their directories.
2. Extract mandatory onboarding, agreement, transcript/logging, submission, data-access, secret-handling, and output-schema rules.
3. Treat an explicit agreement gate as blocking: ask for the exact required acknowledgement and do not run analysis, implementation, evaluation, or delegation until it is received.
4. If a shared append-only transcript is required, create it at the specified location only when the contract permits, record the onboarding entry after agreement, and append concise secret-redacted summaries for subsequent turns. Never commit that external log unless the contract explicitly requires it.
5. Separate **factual intake** from design: report schemas, files, media, validation requirements, and hard constraints without proposing an architecture while a user-held diagram or design review gate is pending.
6. Convert the extracted rules into visible checkpoints and verification criteria for later planning; do not silently fold them into implementation assumptions.

This gate is especially important for time-boxed challenges: compliance artifacts (transcript, output file, code-package boundaries) are first-class deliverables, not end-of-project cleanup.

### Phase 1 — Design checkpoints

#### Checkpoint 1: problem framing
Present only:
- problem restatement
- target user / primary use case
- explicit assumptions

Stop and wait for approval.

#### Checkpoint 2: options and tradeoffs
Present a bounded set of plausible directions, usually 2–3.
For each option include:
- shape
- pros
- cons
- implementation/schedule risk
- best-fit scenario

Then state the likely best option, but do not lock it in until Checkpoint 3.

Stop and wait for approval.

#### Checkpoint 3: recommended direction
Present:
- chosen direction
- component map / module boundaries
- explicit TBD decisions with proposed resolutions
- MVP scope
- not-doing list
- edge cases / risks
- exact items where user weigh-in is required

Stop and wait for approval.

## Pre-write gate for design artifacts

Before writing any design/ADR/plan files, explicitly confirm the exact target paths.

Example:
- `docs/design/<slug>-design.md`
- `docs/decisions/0001-...md`
- `docs/plans/<slug>-plan.md`

Do not create files until the user has explicitly approved the write targets.

## Phase 2 — Plan authoring gate

Before writing the implementation plan:
1. summarize the approved direction in 2–3 sentences
2. ask for explicit scope confirmation
3. confirm the exact plan file target path
4. write the plan only after both confirmations

The plan should contain resolved decisions only. Do not leave silent TBDs that were never surfaced to the user.

## Phase 3 — Build checkpoints

Implement one approved step at a time.

For each build step:
1. restate the step boundary
2. limit file edits to that step's inventory
3. verify with the strongest repo-context checks available
4. report a build checkpoint before continuing
5. stop for explicit confirmation before the next step

Each build checkpoint should include:
- files changed
- plan fidelity (`matches plan` / `diverges from plan`)
- newly surfaced TBDs or ADR candidates
- tests/validation performed
- next step name

## Approval provenance for auditable workflows

When the repository or challenge requires an external transcript, record each resolved gate immediately after the user's decision is clear. Capture:

- the user’s approval text (with secrets redacted);
- the precise scope/path or build step approved;
- what remains deferred or still gated.

A choice returned through an interactive confirmation control is an explicit user decision. Conversely, do not infer approval for later build steps from an approval that was scoped only to a plan artifact or current checkpoint. This makes the transcript a reliable approval record without advancing beyond the approved boundary.

## Handling new unknowns during build

If implementation surfaces a new policy or workflow question:
1. stop at the end of the current step
2. label it clearly as a new TBD / ADR candidate
3. explain why it affects execution
4. wait for explicit confirmation before proceeding

Do not silently absorb new constraints into the build.

## Handling runtime byproducts and repo-generated artifacts

If repo-local validation or harness tooling creates extra files:
- call them out explicitly in the checkpoint
- classify them as runtime/procedural byproducts vs feature files
- ask whether to keep/remove if that affects the approved file inventory
- if the workflow is document-heavy, record the decision in an ADR before continuing

## Validation guidance

Prefer repo-context validation over ad hoc standalone execution when the code is intentionally environment-bound.

Examples:
- server-only modules may fail in generic `tsx` execution but still be valid in the app/runtime
- use project TypeScript, formatter, framework-aware checks, and targeted repo-context probes
- explain any validation limitation honestly in the checkpoint

## OpenSpec as an instance of this pattern

When the user explicitly opts into spec-driven design via OpenSpec (`openspec init` in a repo), the OpenSpec CLI + skills instantiate the phase-gated pattern above. The mapping:

| This skill | OpenSpec equivalent |
|---|---|
| Phase 1 design checkpoints | `openspec-explore` (thinking/discovery) → `openspec-propose` (all planning artifacts) |
| Phase 2 plan authoring | `proposal.md` + `specs/*.md` + `design.md` + `tasks.md` (all created by propose) |
| Phase 3 build checkpoints | `openspec-apply-change` (implements tasks in order) |
| Archive / sync | `openspec-archive-change` |

**Critical rules when using OpenSpec via gateway (Slack, Telegram, etc.):**

1. **Slash commands don't work on gateway.** `/openspec-propose` and similar are CLI-only. On gateway, the user triggers by natural language ("propose a change for X", "explore the idea of Y", "apply the Z change"). Hermes matches intent to the skill and loads it.

2. **The propose skill creates ALL 4 planning artifacts in one pass.** It loops through the dependency chain: `proposal → specs + design → tasks`. Do NOT stop after writing only `proposal.md` and present it as if the workflow is complete. The skill explicitly says: "Continue until every artifact in the required set exists." If you stop early, the user sees a proposal with no design, no specs, and no tasks — and asks "why are you skipping design?"

3. **The propose skill deliberately stops before implementation.** Even if the user says "propose, design then implement" in the same request, the propose skill's guardrail says: "Do NOT implement the change, start the apply workflow, or edit project code during this workflow. After presenting the artifacts, stop and wait for a new user request." Present the complete set of planning artifacts for review, tell the user to trigger apply when ready, and stop.

4. **The apply workflow is triggered separately.** When the user says "apply" or "implement the X change," load `openspec-apply-change` and work through `tasks.md` in order, marking each `[ ]` → `[x]`.

**Common failure mode:** Running the propose workflow, stopping after only the proposal artifact (1 of 4), and presenting it as complete. This makes the user think the design phase was skipped. The fix: keep going through specs, design, and tasks in the same pass, then present all artifacts together.

## Pitfalls

- Writing docs before path confirmation
- Writing code before explicit plan approval
- Treating `proceed` as approval in a strict workflow
- Continuing past a build checkpoint without user confirmation
- Hiding runtime byproducts because they seem unimportant
- Leaving unresolved TBDs buried in a plan or implementation summary
- **Stopping the OpenSpec propose workflow after only `proposal.md`** — the propose skill requires all 4 artifacts (proposal, specs, design, tasks) to be created before stopping. Stopping early makes the user think design was skipped.

## Deliverable style

Keep the workflow legible and auditable:
- checkpoint title
- bounded content for that checkpoint only
- explicit approval request
- no accidental forward progress past the current gate

## Reference files

- `references/checkpoint-template.md` — reusable checkpoint structure and approval wording
