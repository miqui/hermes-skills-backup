---
name: checkpointed-project-kickoff
description: Human-in-the-loop project kickoff workflow for idea refinement, ADR-backed design docs, pre-build planning, and gated implementation checkpoints.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [planning, design, docs, adr, human-in-the-loop, workflow]
    related_skills: [idea-refine, writing-plans, test-driven-development]
---

# Checkpointed Project Kickoff

## Overview

Use this skill when the user wants a **docs-first, human-in-the-loop** workflow that moves through:
1. problem framing,
2. option comparison,
3. direction selection,
4. design doc + ADR capture,
5. pre-build implementation planning,
6. build execution with explicit checkpoints.

This skill is for users who do **not** want a one-shot brainstorm or an immediate code sprint. They want explicit approvals, traceable artifacts under `docs/`, and a predictable phase gate before any writing or coding.

See `references/kickoff-protocol.md` for a condensed protocol template and approval language patterns.

## When to Use

Use this skill when:
- the user asks for a project kickoff with design, ADRs, and plans before coding
- the user wants idea-refine → writing-plans → build as separate gated phases
- the work should persist to repo docs under `docs/design/`, `docs/decisions/`, and `docs/plans/`
- the user wants to be treated as an experienced collaborator with explicit review checkpoints
- the user insists on approval semantics such as “do not proceed until explicitly confirmed”

Do not use this skill when:
- the user wants immediate implementation with no design phase
- the work is a tiny one-off bug fix with no meaningful design surface
- the repo already has a stable approved plan and the only remaining work is execution

## Core Rules

### 1) Explicit approval means explicit approval
Treat only clear approval as a green light.

Accepted examples:
- `Approve Checkpoint 1`
- `Approve Phase 2 scope`
- `Approve write target`

Non-approval examples:
- `proceed`
- `ok`
- `sure`
- `looks good`

If the reply is ambiguous, restate exactly what you think was approved and ask for explicit confirmation before advancing.

### 2) No silent artifact writes
Before the **first write of each phase**, confirm the exact target paths with the user.

Examples:
- design doc + ADR paths before Phase 1 artifact creation
- plan path before Phase 2 artifact creation

Do not create files, directories, or append revisions until the write targets are explicitly approved.

### 3) No code until plan approval
Do not begin implementation until:
- the design direction is approved
- the plan is approved
- all plan `TBD`s are resolved and replaced with ADR references or explicit accepted decisions

### 4) Treat silent scope drift as a stop condition
If scope changes after a design checkpoint or during build, stop and either:
- open an ADR candidate for the change, or
- return to the prior planning phase if the change invalidates the current plan

## Phase 0 — Setup & discovery

1. Derive a slug from the project or idea name.
2. Check whether `docs/design/<slug>-design.md` already exists.
3. If it exists:
   - read it
   - summarize current status
   - ask whether to continue the existing project or start fresh under a new slug
   - do not proceed until the user chooses
4. Identify or prepare the target docs tree:
   - `docs/design/`
   - `docs/decisions/`
   - `docs/plans/`
5. Do not write anything yet.

## Phase 1 — Idea refinement with checkpoints

### Checkpoint 1: problem framing
Present:
- restated problem
- target user/use case
- explicit assumptions

Stop and wait for explicit approval.

### Checkpoint 2: options & tradeoffs
Present 2–4 plausible directions with honest tradeoffs.

Stop and wait for explicit approval.

### Checkpoint 3: recommended direction
Present together:
- recommended direction
- component map
- MVP scope
- not-doing list
- edge cases / failure modes / risks
- all `TBD — decision needed` items with a concrete proposed resolution for each

Stop and wait for explicit approval.

### Phase 1 artifact rules
After Checkpoint 3 approval:
- confirm exact write targets before writing
- write `docs/design/<slug>-design.md`
- write one ADR per discrete user-approved decision under `docs/decisions/NNNN-<short-title>.md`
- set frontmatter and traceability links on every file

## Phase 2 — Plan authoring

Before writing the plan:
1. summarize the approved direction and component map in three sentences
2. ask the user to confirm scope has not shifted
3. if scope changed, stop and return to the design gate that needs to be reopened

When writing the plan:
- use the approved design and ADRs as inputs
- enumerate every remaining `TBD`
- do not present a plan with silent or unresolved `TBD`s
- each open `TBD` must include a concrete proposed resolution or be flagged as a hard blocker

Before the first plan write:
- confirm the exact plan path with the user

## Phase 3 — Build with per-step checkpoints

Only begin after the plan is approved and all `TBD`s are resolved.

For each implementation step:
1. implement only that step
2. stop and present a build checkpoint including:
   - files changed
   - plan fidelity
   - newly surfaced TBDs
   - tests/validation status
   - next step
3. do not begin the next step until the user explicitly confirms

## ADR handling

Use ADRs for:
- direction choices approved during design
- deviations discovered during build
- scope changes that materially alter module boundaries, interfaces, or implementation approach

ADR shape:
- Context
- Decision
- Status
- Consequences
- Alternatives considered

Never silently overwrite an older ADR. Supersede it and link the replacement.

## Documentation rules

Every artifact should include frontmatter:
- `title`
- `status`
- `date`
- `owner`
- `slug`
- `related`

Idempotency rules:
- if a target file already exists, do not overwrite silently
- append a dated revision/changelog section
- summarize what changed and why
- preserve history

Traceability rules:
- design doc links ADRs
- plan links design doc and ADRs
- ADRs back-link to the plan step or design surface they govern

## Git rules

Before staging docs, verify the repo is a git worktree.
If true:
- stage the changed docs
- propose a conventional commit message
- do not commit or push unless the user explicitly asks

If false:
- skip git operations
- tell the user staging was skipped
- remind them to initialize a repo

## Pitfalls

1. **Treating “proceed” as approval.**
   In this workflow, it is not enough.

2. **Writing directories/files before path confirmation.**
   Pre-write gates are part of the contract.

3. **Leaving silent TBDs in the plan.**
   An unmentioned TBD becomes a hidden implementation decision.

4. **Jumping into code after design approval but before plan approval.**
   The plan gate is mandatory.

5. **Batching multiple review checkpoints together.**
   Present one gate at a time and wait.

6. **Letting build drift accumulate.**
   If multiple steps diverge from plan, stop and revise the plan.

## Verification Checklist

- [ ] Slug chosen and prior design doc checked
- [ ] No artifacts written before phase-specific path approval
- [ ] Problem framing approved explicitly
- [ ] Options/tradeoffs approved explicitly
- [ ] Direction/component map/MVP scope approved explicitly
- [ ] Design doc and ADRs written with traceability
- [ ] Phase 2 scope re-confirmed before plan writing
- [ ] Plan written with no silent TBDs
- [ ] Plan approved before coding starts
- [ ] Each build step stops for user confirmation before continuing

## Relationship to other skills

- Use `idea-refine` for the thinking patterns inside Phase 1.
- Use `writing-plans` for the implementation-plan structure inside Phase 2.
- Use `test-driven-development` during Phase 3 execution when code changes begin.

This skill does not replace those skills; it coordinates them under a stricter human-in-the-loop approval contract.
