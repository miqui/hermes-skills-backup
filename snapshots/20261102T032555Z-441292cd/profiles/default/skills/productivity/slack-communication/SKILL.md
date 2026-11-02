---
name: slack-communication
description: Use when formatting messages for Slack. Use mrkdwn.
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [slack, communication, formatting, mrkdwn, delivery]
    related_skills: [humanizer]
---

# Slack communication

## Overview

Slack is a conversational delivery surface, not a GitHub README renderer. Write messages for fast scanning in the client: lead with the result, keep context proportional, and use Slack-compatible `mrkdwn` primitives. Do not assume GitHub-Flavored Markdown (GFM) headings, tables, task lists, or Markdown-link rendering will be interpreted as intended.

For this user, concise and actionable Slack `mrkdwn` is the default. Use GFM only when the user explicitly requests it. If they ask to display a Markdown artifact in Slack, render it for reading in Slack rather than wrapping the complete document in a single opaque code block, unless they explicitly request raw source.

## When to use

Use this skill when:

- Responding in a Slack thread, channel, or DM.
- Posting a status, plan, decision, review, PR summary, or technical result in Slack.
- Translating a Markdown document, report, table, checklist, or skill into Slack-readable content.
- Reporting a long technical artifact where readability and copyability must be balanced.
- The user asks for "Slack-compatible Markdown," "mrkdwn," or to display a document in Slack.

Do not use this skill to alter a file just because it will later be shared in Slack. Preserve the source document's requested format; adapt the *message that delivers it*.

## Default message shape

Use the smallest structure that makes the result actionable:

1. **Result first.** State completion, blocker, decision, or answer in the first line.
2. **Evidence next.** Give the essential IDs, files, commands, measurements, or links.
3. **Action only if needed.** State the one next decision or user action; do not add generic offers to help.

For a short update, use one or two sentences. For a technical result, use a bold label followed by short bullets. Avoid prefatory phrases such as "Here is," "Certainly," or "I hope this helps."

## Slack `mrkdwn` primitives

Use these portable constructs:

| Intent | Prefer | Example |
| --- | --- | --- |
| Emphasis | `*bold*` | `*Validation passed*` |
| Light emphasis | `_italic_` | `_Optional_` |
| Deletion | `~strike~` | `~deprecated~` |
| Inline code | backticks | `` `./gradlew test` `` |
| Code sample | fenced block | triple-backtick block |
| Quote | `>` | `> quoted decision` |
| Bullet list | `•` or `-` | `• Run targeted tests` |
| Ordered steps | `1.`, `2.` | `1. Capture baseline` |
| Link | raw URL, or Slack link syntax when supported | `Docs: https://…` or `<https://…|Docs>` |

Use a raw URL when label syntax could make the message harder to copy, audit, or render across clients.

## GFM features to avoid by default

Do not rely on these in Slack output:

- `#` / `##` Markdown headings. Use a standalone `*bold label*` instead.
- Pipe tables. Convert them into labeled bullets or compact `key: value` lines. Even if a user asks for a “Markdown table,” confirm whether they instead mean Slack-compatible formatting; use a table only after an unambiguous request for literal GFM despite Slack portability limits.
- GitHub task lists such as `- [ ]` or `- [x]`. Use `☐`, `☑`, or plain status words instead.
- Footnotes, HTML, Mermaid, collapsible sections, and embedded HTML links.
- A language tag after a code fence when portable rendering matters. Plain fenced blocks are safest.
- Markdown images. Attach media through the platform when available, then describe it with alt text in the message.

## Presenting long Markdown artifacts

When the user wants a long document, skill, plan, or report displayed in Slack:

1. Start with a one-line outcome and any verification status.
2. Render prose sections with Slack-compatible bold labels, bullets, and numbered steps.
3. Preserve commands, config, source snippets, and literal frontmatter in focused fenced code blocks.
4. Replace tables with labeled lists; retain each row's meaning.
5. Keep links copyable and visible.
6. If the full artifact is too long for one message, split on natural section boundaries and number the parts. Never silently omit a section.
7. Offer or attach the raw source only when useful or explicitly requested.

For a `SKILL.md`, show the title and explanatory sections as Slack prose. Put YAML frontmatter and executable command examples in their own fenced blocks. Do not present the whole `SKILL.md` as one fenced block unless the user asked for the literal file contents.

## Technical status format

Use this shape for engineering work:

```text
*Completed: <outcome>*

• Changed: `<path>`
• Verified: `<command or check>` → <result>
• Review/PR: <URL or status>

*Next action:* <only when a decision is needed>
```

Omit empty categories. Do not claim completion, validation, publication, or CI success without actual evidence.

## Delegated-work progress reporting

For multi-step engineering work that uses delegated workers, make progress visible in Slack without turning the channel into a stream of inconsequential updates.

1. **Present the plan before dispatching implementation workers.** State the scope, test/verification gates, and publication boundary. When the user asks to review the plan first, wait for explicit approval before dispatching.
2. **Report every material gate when it is reached:** preflight/design complete; failing test observed; implementation green; full verification complete; spec review complete; quality review complete; and publication/PR state. Do not wait until the end of a long implementation run to report all gates at once.
3. **When asked for status, report only verified state:** worker status, latest completed gate, current activity, and what has not begun. If a worker is still in preflight, say so plainly; do not imply implementation or testing has started.
4. **List sessions in Slack-native prose, not tables.** Use a bold title plus indented bullet fields (`ID`, `workspace`, `last active`). Markdown tables are not portable across Slack clients.
5. **Preserve identifiers exactly as returned by an authoritative command.** If output truncates a title or identifier, reproduce it as truncated or mark it unavailable—never reconstruct, expand, or guess missing characters.

6. **Always include an explicit agent roster in any status report.** One line per agent, Slack-readable: `<emoji> <agent id> — <task summary> — <state> — <model used>` (e.g. `🔄 sa-0-054ce098 — CI workflow — running — claude-sonnet-5`). The model used by each worker is MANDATORY in every roster line — Miguel corrected this explicitly after it was omitted twice. Include a `Parent (me)` line for the orchestrator (with the orchestrating model). This user cannot read GFM tables in Slack and explicitly requires the roster on every status ask — never summarize worker state without listing each agent.

Suggested active-work update:

```text
*Status: <current gate>*

• sa-0-… — <task> — running
• Parent (me) — orchestration/verification — waiting on children
• Completed: <verified gate>
• Not started: <remaining gates>
• Safety: no commit, push, or PR
```

## Liveness acks before long operations (standing rule)

The user perceives a silent tool-running turn as a hang. Before starting any long or multi-step sequence (delegations, builds, verification passes, bulk edits), post a one-line ack in the thread first — what is being worked on and what comes next — instead of producing only the final answer after the fact. Post a short milestone line between phases of a long turn (e.g. "plan folded, dispatching workers"). Keep acks to one line; the final result still leads with the outcome.

## PR merging is user-owned

Opening a PR via the git workflow wrapper is agent-owned; **merging an open PR is not**. This user merges PRs personally — never run `gh pr merge` unless the user explicitly names that PR for merging. "Work on the next item" does not authorize merging pending PRs, even green ones the new work depends on. When a follow-up task needs an unmerged PR's content, report the dependency and ask the user to merge (then `git fetch && git merge --ff-only origin/main` before continuing — a stale local `main` without the merged files produces confusing file-not-found states). If a merge slipped through before correction, disclose exactly which PRs were merged and by what command. This rule is mirrored in `local-git-workflow` (which is user-owned and could not be patched — recommend `hermes curator adopt local-git-workflow` so the lesson lives there too).

## Status reports must list the agent roster

Already covered in "Delegated-work progress reporting" item 6 above: every status ask gets an explicit per-agent roster line (`<emoji> <id> — <task> — <state>` plus a `Parent (me)` line). Reinforced from this session: the user first hit an unreadable GFM table roster, then said "better. remember" for the one-line-per-agent prose format — rosters must be prose bullets, never tables.

## Decision and blocker format

When reporting review or verification results with mixed severities, report BLOCKERS FIRST as their own section — only then should-fixes and nits. The user asked for exactly this ordering after receiving a findings dump that buried the blockers.

Ask decision questions as plain numbered bullet text in the chat message — NOT as an interactive multi-question form/prompt. Interactive question forms truncate in this user's Slack client (the form comes back empty); numbered bullets get answered directly in reply (e.g. "1: yes, 2: yes ..."). Enumerate options with a recommendation per item. This rule covers EVERY question mechanism, including the structured clarify/question tool: never render questions as clickable choice buttons in Slack — the user rejects button-formatted questions outright. If the tool must be used, omit all choices so it presents as a plain free-text prompt, or put the numbered questions in the chat message instead. Load this skill before asking the user anything in a Slack session, not only before formatting a result.

```text
*Decision needed: <subject>*

• Option A: <impact>
• Option B: <impact>

*Recommendation:* <one clear choice and reason>
```

```text
*Blocked: <specific blocker>*

• Observed: <actual error or missing prerequisite>
• Impact: <what cannot proceed>
• Needed: <smallest user action or decision>
```

## Common pitfalls

1. **Using GFM headings and tables.** Slack can show them as raw punctuation or hard-to-scan text. Use bold labels and lists.
2. **Posting raw source when the user asked to see the artifact.** Source-only delivery is difficult to read. Render prose and isolate only literal code/configuration.
3. **Putting every detail in a code block.** Code blocks prevent emphasis and reduce scanability. Reserve them for text that must be copied exactly.
4. **Treating a PR link as the result.** State what changed and what verification actually ran.
5. **Adding generic conversational filler.** Begin with the outcome and stop when the user has what they need.
6. **Using GFM by habit.** The user interacts primarily through Slack; use `mrkdwn` unless they request another format.
7. **Sending decision questions through interactive forms/prompts.** Multi-question interactive forms truncate for this user and come back empty; ask decision points as numbered plain-text bullets with a recommendation per item.
8. **Turning a soft quality target into a delivery blocker.** Keep safety, authorization, and correctness gates. But if the user relaxes a non-essential preference (such as an ideal document length), update the plan immediately and deliver once essential verification is satisfied. Do not repeatedly post progress-only updates while the user is waiting for a usable result.

9. **Never wrap URLs in bold/asterisks.** Stray `*` around links triggers Slack 404 unfurls; post URLs as plain text or `<url|label>`.

## Verification checklist

- [ ] The first line communicates the outcome, blocker, or decision.
- [ ] Formatting uses Slack-compatible `mrkdwn` primitives.
- [ ] No GFM-only headings, tables, or task lists remain unless explicitly requested.
- [ ] Commands, paths, IDs, and URLs are copyable.
- [ ] Long artifacts are sectioned without omitted content.
- [ ] Claims of validation, publication, or completion have evidence.
- [ ] The message contains no generic filler or unnecessary invitation to continue.

## Reference

See `references/slack-mrkdwn.md` for a compact conversion guide and example delivery patterns.
