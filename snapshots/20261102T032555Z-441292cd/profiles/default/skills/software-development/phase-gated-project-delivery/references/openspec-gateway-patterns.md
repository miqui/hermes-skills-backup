# OpenSpec on Slack/Gateway: Session Lessons

Lessons from running the full OpenSpec lifecycle (explore → propose → apply → archive) via Slack gateway. The `phase-gated-project-delivery` SKILL.md already carries the critical workflow rules; this file is the detailed session-proven reference.

## Slash Commands Don't Work on Gateway

`/openspec-propose`, `/openspec-apply-change`, etc. are CLI-only in-session commands. On Slack/Telegram/Discord gateway, they do nothing.

**Trigger by natural language instead:**
- "Explore the idea of..." → loads `openspec-explore`
- "Propose a change for..." → loads `openspec-propose`
- "Apply the X change" → loads `openspec-apply-change`
- "Archive the X change" → loads `openspec-archive-change`

Hermes matches intent to the skill and loads it.

## Propose: Complete ALL 4 Artifacts Before Stopping

The propose skill creates all planning artifacts in dependency order:

```
proposal → specs + design (parallel) → tasks
```

**Failure mode observed:** Stopping after only `proposal.md` (1 of 4) and presenting it as if the workflow is complete. The user sees a proposal with no design, no specs, no tasks and asks "why are you skipping design?"

**Rule:** Loop through artifacts in dependency order. After each artifact, re-run `openspec status --change "<name>" --json` and continue until every artifact in the required set is `done`, `skipped`, or deliberately skipped. Then present all artifacts together.

## Propose ≠ Apply: Planning Stops, Implementation Waits

The propose skill explicitly says:

> "Do NOT implement the change, start the apply workflow, or edit project code during this workflow. After presenting the artifacts, stop and wait for a new user request to start the apply workflow."

**Failure mode observed:** When the user says "propose, design then implement" in one message, conflating propose + apply into a single pass. The propose skill's guardrail says stop after planning — even if the user asks for implementation in the same request.

**Rule:** Complete all 4 planning artifacts, present them for review, tell the user to trigger apply when ready, and STOP. The user must explicitly say "apply" or "implement the X change" in a new message before the apply workflow starts.

## Apply: Mark Tasks [x] as You Go

During the apply workflow, mark each task `- [ ]` → `- [x]` in `tasks.md` immediately after completing it. The apply phase parses checkbox format to track progress.

**Failure mode observed:** Implementing all code but forgetting to update `tasks.md` checkboxes, leaving the change looking incomplete even though the work is done.

## Re-reading Skills After Compression

After context compression, `skill_view` may return "unchanged" with `content_returned: false`. This does NOT mean you have the full instructions — compression may have removed the detail from your active context.

**Rule:** When executing a skill workflow, re-read the full skill content if you're unsure of any step. Don't rely on compressed memory. The skill instructions are the authoritative process — follow them literally, especially steps that feel counterintuitive (like stopping after planning even when the user asks for implementation).

## Full Lifecycle from Slack

```
1. "Explore the idea of X"
   → openspec-explore loads, thinking/discovery, no artifacts

2. "Propose a change for X"
   → openspec-propose loads
   → openspec new change "name"
   → openspec status → openspec instructions (per artifact)
   → Write all 4 artifacts: proposal, specs, design, tasks
   → STOP, present for review

3. "Apply the X change"
   → openspec-apply-change loads
   → openspec instructions apply
   → Implement tasks in order, mark [x]
   → Commit + PR

4. "Archive the X change"
   → openspec-archive-change loads
   → Sync specs, move to archive
```
