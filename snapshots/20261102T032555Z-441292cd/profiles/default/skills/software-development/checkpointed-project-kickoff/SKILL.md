---
name: checkpointed-project-kickoff
description: Human-in-the-loop project kickoff workflow for idea refinement, ADR-backed design docs, pre-build planning, and gated implementation checkpoints.
version: 1.3.0
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

7. **Presenting abstract options before the architecture is visible.**
   Options like "implementation language" or "state store" are meaningless to
   the user until they have seen the component map and know which component the
   option governs. Checkpoint 2 options must anchor each choice to a concrete
   box in the architecture ("the gateway service we write ourselves — nothing
   off the shelf does this — needs a language: Go vs Rust"). If the user asks
   "what does X mean" twice, stop rephrasing and draw the picture instead.

8. **Treating checkpoint approvals as all-or-nothing.**
   Real approvals arrive with item-level exceptions: "Approve Checkpoint 2, but
   skip item 6 entirely." Number/letter every option so partial approval is
   actionable, restate exactly what was approved vs. deferred, and carry
   deferred items into the design doc's not-doing list and the plan (never let
   a "we'll add this later" item vanish).

9. **Losing mid-checkpoint constraint notes.**
   Users often drop environment constraints between checkpoints (hardware
   limits, descoped features, tooling choices). Absorb each note immediately,
   restate the revised framing at the top of the NEXT checkpoint, and turn
   descopes into their own ADRs — a descope decision approved by the user is
   still a decision worth recording.

10. **Conflating local commits with repo publication.**
    Committing approved docs locally and publishing the repo to GitHub are
    separate gates. On hosts with a sanctioned git-workflow script, publication
    (init/push/PR) goes through that script at an explicit user request; local
    `git commit` of approved artifacts is fine and should not wait for
    publication. Offer publication as its own question, not silently bundled.

11. **Read the sanctioned git script before warning about its limits.**
    `git-workflow.sh init` tolerates a clean tree with prior local commits: it
    logs "Nothing new to commit", still creates the repo, sets the SSH remote and
    pushes. Only `update` dies on nothing-to-commit (and on never-pushed
    branches). So local per-task commits do not block publication. Grep the
    script (`grep -n "Nothing to commit\|die" git-workflow.sh`) instead of
    trusting a remembered limitation — scripts get fixed and notes go stale. If
    the script does fail at publish time, report it and offer options; do not
    improvise around it.

12. **Batching subagent work into sweeps, with parent verification.**
    For a gated build with many small plan tasks: dispatch related tasks to
    background subagents in batches (3 tasks ≈ one sweep), pass each child the
    FULL context it needs (it sees nothing of this conversation): plan paths,
    ADR numbers, existing code layout, toolchain versions, commit messages
    exactly, and explicit stop-before-task boundaries. Then ALWAYS independently
    verify child output (re-run tests/vets, spot-check the diff) before
    reporting the checkpoint — child summaries are self-reports; in one session
    a child committed identical/masked API keys into a config file because its
    own tooling display-masked `sk-…` strings and it wrote the mask back.
    Warn children explicitly: never persist display-masked credential values.

13. **Verifying behavior with live systems beats diagnosing from code.**
    When a subagent reports a blocker (e.g. "model name mismatch between
    ConfigMap and router"), reproduce the behavior at the real boundary before
    accepting the diagnosis — a direct curl to the upstream showed BOTH model
    names worked, revealing the real bug (an unpopulated registry map in
    main.go). Ask which specific experiment supports the claimed root cause.

14. **Prompted answers that partially time out are still answers.** When a multi-question
    gate (clarify form, checkpoint batch) returns some answers plus "user did not
    respond" for the rest, the answered items are recorded decisions — do not re-ask
    them. State exactly which answers landed and re-prompt ONLY the unanswered ones
    (user, 2026-09: "i already provided answers, if not prompt me again"). Re-asking
    everything wastes a review cycle; treating a timed-out form as wholly unanswered
    discards real decisions.

15. **Prefer numbered plain-text questions over structured prompt forms for decision gates.**
    Structured question forms on chat platforms can render truncated or return empty
    (an EMPTY form response means NO answers landed — re-present them as plain text,
    don't treat the gate as passed). Post the decisions as short numbered lines with
    the recommended pick marked first; plain text survives rendering and gets
    answered inline.

16. **Go straight from gate approval to artifact — no intermediate round-trips.** Once a
    checkpoint is approved and write paths are confirmed, produce the artifact in the same
    flow; do NOT insert a skill load, re-read, or "here's my approach" hop before writing it —
    the user experiences every gate→artifact hop as delay. Load any prerequisite skills
    BEFORE the gate whose approval produces the artifact, not after.

17. **Never end a turn on a promise of future work.** A closing line like "I'll run the next passes now" ends the turn with nothing running; the user then asks for status and finds zero progress. Either execute the next step in the same turn (research, repo scaffold, review pass) or end the turn with an explicit question that needs his answer. When a status ask reveals this, say plainly that nothing ran since the last report, then do the work.

18. **Re-verify against a user-supplied source before overriding an earlier assumption.** When the user hands over a URL/doc as the authority (e.g. a model page, API route), read it fully and re-check any "correction" you made from a different source. A second doc site may describe a different access path (direct vendor API vs. the aggregator he specified); the user's stated route wins, and the contract (endpoint, model ID, request/response shape) is taken from his source's live page, not memory.

19. **Probe feature support before committing a design to a new cloud feature.** For newly launched services, check the IaC provider (release notes, open issues/PRs for the resource type) before planning Terraform around it. If unsupported, present the split (IaC for everything else + standalone deploy script, swap in when the provider ships) as a labeled option for the user's decision, and note the sequencing dependency it creates (e.g. an origin hostname only known after the script runs).

20. **Separate live risks from misconfiguration risks when explaining security design.** If asked "is this true now?" about a threat you described (e.g. a fork PR obtaining cloud OIDC credentials on a public repo), say plainly whether the current design already blocks it, then list the guards (trigger choice, trust-policy conditions, job guards, repo settings to verify). Presenting a hypothetical as a present hole erodes trust and bloats the plan.

22. **Take the delegated model name from `delegate_task(action='list')` or config `delegation.model`, never from memory.** The user can change it in config.yaml between sessions; a stale label in a status roster reads as a wrong-model dispatch and costs a correction round.

21. **Offer complementary scanners, but keep the user's stated policy engine as the gate.** When he names a policy tool (OPA/Rego), do not swap it for another (Checkov); propose the other as an additional non-blocking layer and let him decide, then record both in the CI design (blocking vs non-blocking, promotion criteria).

23. **Budget/repeat TBDs: offer a 'defer and calibrate' option.** When a checkpoint proposes unmeasured spend caps or repeat counts, the user may not follow the jargon ("don't understand, 3.3"). Re-explain in plain words (what it is, why it exists, rough arithmetic) and offer a/b/c with c = make them config values and calibrate after the first smoke run. Record the deferral as its own ADR. If asked for run cost before any run exists, say plainly that no run has happened ($0 spent) rather than quoting earlier guesses.

24. **Judge approval by intent, not spelling — but a correction is not an approval.** A typo'd or shorthand reply ("approve all recommended", "apprivoved targets") that clearly names the gate is explicit approval; accept it and restate what landed in one line. A reply that only supplies corrections or notes ("note: use X") is NOT approval: restate the revised framing and ask for the explicit approve, as the same step as the next gate's prep.

25. **Spike feasibility from primary docs before the direction checkpoint.** When the design hinges on a third-party SDK capability (live model switch, native tracing, token/cache accounting), search/read its docs and examples before Checkpoint 3, then report findings labeled "from docs, not yet run" and carry unverified items as risks with a first-smoke-run validation. This turns an assumption into a resolved TBD without overclaiming.

26. **Docs-only artifact writes still go to a subagent, and the parent verifies structure with a script.** Brief the child with every approved decision and exact paths, forbid commits/remotes/code, and require staging only. Then verify in one script: frontmatter keys present on every file, all relative `.md` links resolve, required ADR sections exist, and no credential-looking strings. Report what was and was not checked (structure vs prose).

27. **Re-run each build step's verification yourself before the checkpoint.** After a child reports a build task done, re-run lint/format/tests, read the generated config (e.g. CI job names, permissions, action SHA pins), run the secret scan, and check `git status` is clean and the commit message is exact. Present the checkpoint with: files changed, plan fidelity, deviations/additions beyond the plan, validation, what is NOT yet verified (e.g. CI never ran because nothing is pushed), new TBDs, next step.

28. **A blocked verification is reported, not rerouted.** If your own check script is held for approval and times out, say plainly that the artifact is unverified, list what was and wasn't checked, and offer options (approve the read-only script, user reads it, accept the self-report with its risk). Do not retry through another tool. When the user says to try again, re-run the same read-only check.

29. **Probe the environment before dispatching a spike.** Check what the spike depends on (e.g. whether Jaeger answers on its OTLP port) with a cheap curl and put the result in the child's brief with the fallback (throwaway local listener). Give live-spend spikes a hard dollar cap enforced in the script, an `op run` env-file containing only an `op://` reference, and a STOP-and-report instruction if the secret manager needs approval.

30. **Publication bundle: README + repo description + protection + CI check.** Every new repo gets a `README.md` and a GitHub description (`gh repo edit --description`). Order: verify the last checkpoint, `betterleaks dir .`, `git-workflow.sh init`, then protect `main` (`gh api -X PUT repos/<o>/<r>/branches/main/protection` with required checks = workflow job names + 1 approving review), then confirm the first CI run is green. A user's "push all work when done" pre-authorizes the push, not skipping verification, and the next build step still waits for its own approval.

31. **After protection, all changes go through a PR.** For a README or later docs: leave the change uncommitted on `main` (if you already made a branch, check out `main`, delete the stale local branch, which needs approval) and run `git-workflow.sh change "<msg>" --branch <name>`; then report checks and stop — the user merges. The README's "Run manually" section documents only commands actually run now (paste real output); money-spending commands are shown in `op run --env-file` form and marked not re-run. State status honestly (built vs planned checklist). Reviewers/bots may push follow-up commits, so re-pull `main` and say so when the user reports a merge.

32. **Mid-build model/provider changes are superseding ADRs, not edits.** When the user changes an approved choice (e.g. model pair) during build: write a new ADR superseding the old one (set the old status to `superseded` with a link), append a dated Correction note rather than rewriting an ADR whose assumption proved wrong, renumber later planned ADRs in the plan, re-run a small capped spike to confirm IDs/endpoints/cache behaviour on the new choice, and fold it into the next build step's brief. Unanswered side-decisions: state the recommendation you are taking so the user can veto, instead of re-asking.

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
